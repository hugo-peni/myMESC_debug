#!/usr/bin/env python3
"""
MESC Motor Controller GUI
A PyQt6 application for controlling MESC motor controllers via serial connection.
"""

import sys
import serial
import serial.tools.list_ports
import struct
import csv
import json
import re
from collections import deque
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QPushButton, QSlider, QLabel,
                              QComboBox, QPlainTextEdit, QGroupBox, QSpinBox,
                              QLineEdit, QFileDialog, QTabWidget, QCheckBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QPalette, QColor, QTextCharFormat

try:
    import matplotlib
    matplotlib.use('QtAgg')
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available. Plotting features will be disabled.")


class DataBuffer:
    """Buffer for storing collected motor data"""
    def __init__(self, max_samples=1000):
        self.max_samples = max_samples
        self.clear()

    def clear(self):
        """Clear all data"""
        self.timestamp = []
        self.vbus = []
        self.iu = []
        self.iv = []
        self.iw = []
        self.vd = []
        self.vq = []
        self.angle = []
        self.sample_count = 0

    def add_sample(self, time, vbus_val, iu_val, iv_val, iw_val, vd_val, vq_val, angle_val):
        """Add a single sample to the buffer"""
        if len(self.timestamp) >= self.max_samples:
            # Remove oldest sample
            self.timestamp.pop(0)
            self.vbus.pop(0)
            self.iu.pop(0)
            self.iv.pop(0)
            self.iw.pop(0)
            self.vd.pop(0)
            self.vq.pop(0)
            self.angle.pop(0)

        self.timestamp.append(time)
        self.vbus.append(vbus_val)
        self.iu.append(iu_val)
        self.iv.append(iv_val)
        self.iw.append(iw_val)
        self.vd.append(vd_val)
        self.vq.append(vq_val)
        self.angle.append(angle_val)
        self.sample_count += 1

    def get_size(self):
        """Get current number of samples"""
        return len(self.timestamp)


class SerialReaderThread(QThread):
    """Thread for reading serial data without blocking the GUI"""
    data_received = pyqtSignal(str)
    csv_data_received = pyqtSignal(list)  # For CSV snapshot data

    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.running = True
        self.buffer = ""
        self.capturing_csv = False
        self.csv_buffer = []

    def run(self):
        """Continuously read from serial port"""
        while self.running and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    try:
                        decoded = data.decode('utf-8', errors='replace')
                        self.data_received.emit(decoded)

                        # Try to parse CSV snapshot data
                        self.buffer += decoded
                        self.parse_csv_data()

                    except Exception as e:
                        self.data_received.emit(f"[Decode Error: {e}]\n")
                self.msleep(10)  # Small delay to prevent CPU hogging
            except Exception as e:
                self.data_received.emit(f"[Read Error: {e}]\n")
                break

    def parse_csv_data(self):
        """Parse incoming CSV snapshot data"""
        try:
            lines = self.buffer.split('\n')

            for line in lines[:-1]:
                line_clean = line.strip()

                # Detect start of CSV data
                if "Ia, Ib, Ic, Va, Vb, Vc" in line_clean:
                    self.capturing_csv = True
                    self.csv_buffer = []
                    continue

                # Detect end of CSV data
                if "Snapshot output complete" in line_clean and self.capturing_csv:
                    self.capturing_csv = False
                    if self.csv_buffer:
                        self.csv_data_received.emit(self.csv_buffer)
                    self.csv_buffer = []
                    continue

                # Capture CSV lines
                if self.capturing_csv and line_clean:
                    # Parse CSV line: "0.076, 0.174, -0.074, 0.588, 0.634, 0.785"
                    # Remove ANSI escape codes
                    clean_line = re.sub(r'\x1b\[[0-9;]*m', '', line_clean)
                    clean_line = re.sub(r'\[[0-9]+`', '', clean_line)

                    if ',' in clean_line and not clean_line.startswith('['):
                        try:
                            values = [float(x.strip()) for x in clean_line.split(',')]
                            if len(values) == 6:  # Ia, Ib, Ic, Va, Vb, Vc
                                self.csv_buffer.append(values)
                        except ValueError:
                            pass  # Skip malformed lines

            # Keep last incomplete line
            self.buffer = lines[-1]

        except Exception as e:
            pass  # Silently ignore parse errors

    def stop(self):
        """Stop the reading thread"""
        self.running = False


class MESCControllerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.reader_thread = None
        self.data_buffer = DataBuffer(max_samples=1000)
        self.collecting_data = False
        self.collection_start_time = None
        self.init_ui()
        self.scan_ports()

        # Setup data collection timer
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.update_plot)
        self.plot_update_interval = 100  # ms

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("MESC Motor Controller")
        self.setGeometry(100, 100, 900, 700)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Serial Port Selection Group
        port_group = QGroupBox("Serial Port Connection")
        port_layout = QHBoxLayout()

        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(200)
        port_layout.addWidget(QLabel("Port:"))
        port_layout.addWidget(self.port_combo)

        self.baud_combo = QComboBox()
        self.baud_combo.addItems(['9600', '19200', '38400', '57600', '115200', '230400', '460800', '921600'])
        self.baud_combo.setCurrentText('115200')
        port_layout.addWidget(QLabel("Baud Rate:"))
        port_layout.addWidget(self.baud_combo)

        self.scan_button = QPushButton("Scan Ports")
        self.scan_button.clicked.connect(self.scan_ports)
        port_layout.addWidget(self.scan_button)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_connection)
        self.connect_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        port_layout.addWidget(self.connect_button)

        port_layout.addStretch()
        port_group.setLayout(port_layout)
        main_layout.addWidget(port_group)

        # Motor Control Group
        control_group = QGroupBox("Motor Control")
        control_layout = QVBoxLayout()

        # Current/Torque Request Slider
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("Current Request (A):"))

        self.current_label = QLabel("0.0")
        self.current_label.setStyleSheet("font-weight: bold; font-size: 14pt;")
        self.current_label.setMinimumWidth(60)
        slider_layout.addWidget(self.current_label)

        self.current_slider = QSlider(Qt.Orientation.Horizontal)
        self.current_slider.setMinimum(-30)  # -3.0 A
        self.current_slider.setMaximum(30)   # +3.0 A
        self.current_slider.setValue(0)
        self.current_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.current_slider.setTickInterval(5)
        self.current_slider.valueChanged.connect(self.slider_changed)
        self.current_slider.sliderReleased.connect(self.send_current_command)
        slider_layout.addWidget(self.current_slider)

        control_layout.addLayout(slider_layout)

        # Max current setting
        max_current_layout = QHBoxLayout()
        max_current_layout.addWidget(QLabel("Max Current (A):"))
        self.max_current_spin = QSpinBox()
        self.max_current_spin.setMinimum(1)
        self.max_current_spin.setMaximum(500)
        self.max_current_spin.setValue(3)
        self.max_current_spin.valueChanged.connect(self.update_slider_range)
        max_current_layout.addWidget(self.max_current_spin)
        max_current_layout.addStretch()
        control_layout.addLayout(max_current_layout)

        # Emergency Stop Button
        self.estop_button = QPushButton("EMERGENCY STOP")
        self.estop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                font-size: 16pt;
                padding: 20px;
                border: 3px solid #c62828;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        self.estop_button.clicked.connect(self.emergency_stop)
        control_layout.addWidget(self.estop_button)

        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)

        # Quick Commands Group
        quick_cmd_group = QGroupBox("Quick Commands")
        quick_cmd_layout = QHBoxLayout()

        status_btn = QPushButton("Status")
        status_btn.clicked.connect(lambda: self.send_command("status start"))
        quick_cmd_layout.addWidget(status_btn)

        stop_status_btn = QPushButton("Stop Status")
        stop_status_btn.clicked.connect(lambda: self.send_command("status stop"))
        quick_cmd_layout.addWidget(stop_status_btn)

        error_btn = QPushButton("Show Errors")
        error_btn.clicked.connect(lambda: self.send_command("error"))
        quick_cmd_layout.addWidget(error_btn)

        powerdata_btn = QPushButton("Power Data")
        powerdata_btn.clicked.connect(lambda: self.send_command("powerdata"))
        quick_cmd_layout.addWidget(powerdata_btn)

        quick_cmd_layout.addStretch()
        quick_cmd_group.setLayout(quick_cmd_layout)
        main_layout.addWidget(quick_cmd_group)

        # Data Collection Group
        data_group = QGroupBox("Data Collection")
        data_layout = QHBoxLayout()

        self.collect_btn = QPushButton("Start Collection")
        self.collect_btn.clicked.connect(self.toggle_data_collection)
        self.collect_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        data_layout.addWidget(self.collect_btn)

        self.clear_data_btn = QPushButton("Clear Data")
        self.clear_data_btn.clicked.connect(self.clear_collected_data)
        data_layout.addWidget(self.clear_data_btn)

        self.export_btn = QPushButton("Export CSV")
        self.export_btn.clicked.connect(self.export_data)
        data_layout.addWidget(self.export_btn)

        self.samples_label = QLabel("Samples: 0")
        data_layout.addWidget(self.samples_label)

        data_layout.addStretch()
        data_group.setLayout(data_layout)
        main_layout.addWidget(data_group)

        # Plotting Area (if matplotlib available)
        if MATPLOTLIB_AVAILABLE:
            self.setup_plots(main_layout)

        # Terminal Group
        terminal_group = QGroupBox("Serial Terminal")
        terminal_layout = QVBoxLayout()

        # Terminal display
        self.terminal = QPlainTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setFont(QFont("Courier", 9))
        self.terminal.setMaximumBlockCount(1000)  # Limit to 1000 lines
        terminal_layout.addWidget(self.terminal)

        # Command input
        cmd_layout = QHBoxLayout()
        cmd_layout.addWidget(QLabel("Command:"))
        self.cmd_input = QLineEdit()
        self.cmd_input.returnPressed.connect(self.send_manual_command)
        cmd_layout.addWidget(self.cmd_input)

        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_manual_command)
        cmd_layout.addWidget(send_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.terminal.clear)
        cmd_layout.addWidget(clear_btn)

        terminal_layout.addLayout(cmd_layout)
        terminal_group.setLayout(terminal_layout)
        main_layout.addWidget(terminal_group)

        # Status bar
        self.statusBar().showMessage("Not connected")

    def scan_ports(self):
        """Scan and populate available serial ports"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()

        for port in ports:
            # Display port with description
            display_name = f"{port.device} - {port.description}"
            self.port_combo.addItem(display_name, port.device)

        if self.port_combo.count() == 0:
            self.port_combo.addItem("No ports found", None)
            self.append_terminal("[INFO] No serial ports found\n")
        else:
            self.append_terminal(f"[INFO] Found {self.port_combo.count()} serial port(s)\n")

    def toggle_connection(self):
        """Connect or disconnect from serial port"""
        if self.serial_port and self.serial_port.is_open:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        """Connect to the selected serial port"""
        port_data = self.port_combo.currentData()
        if not port_data:
            self.append_terminal("[ERROR] No valid port selected\n")
            return

        try:
            baud_rate = int(self.baud_combo.currentText())
            self.serial_port = serial.Serial(
                port=port_data,
                baudrate=baud_rate,
                timeout=0.1,
                write_timeout=1.0
            )

            # Start reader thread
            self.reader_thread = SerialReaderThread(self.serial_port)
            self.reader_thread.data_received.connect(self.append_terminal)
            self.reader_thread.start()

            self.connect_button.setText("Disconnect")
            self.connect_button.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
            self.statusBar().showMessage(f"Connected to {port_data} at {baud_rate} baud")
            self.append_terminal(f"[INFO] Connected to {port_data} at {baud_rate} baud\n")

            # Disable port selection while connected
            self.port_combo.setEnabled(False)
            self.baud_combo.setEnabled(False)
            self.scan_button.setEnabled(False)

        except Exception as e:
            self.append_terminal(f"[ERROR] Connection failed: {e}\n")
            self.statusBar().showMessage("Connection failed")

    def disconnect_serial(self):
        """Disconnect from serial port"""
        try:
            # Stop reader thread
            if self.reader_thread:
                self.reader_thread.stop()
                self.reader_thread.wait(1000)  # Wait up to 1 second
                self.reader_thread = None

            if self.serial_port:
                self.serial_port.close()
                self.serial_port = None

            self.connect_button.setText("Connect")
            self.connect_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
            self.statusBar().showMessage("Disconnected")
            self.append_terminal("[INFO] Disconnected\n")

            # Re-enable port selection
            self.port_combo.setEnabled(True)
            self.baud_combo.setEnabled(True)
            self.scan_button.setEnabled(True)

        except Exception as e:
            self.append_terminal(f"[ERROR] Disconnect error: {e}\n")

    def slider_changed(self):
        """Update current label when slider moves"""
        value = self.current_slider.value() / 10.0
        self.current_label.setText(f"{value:.1f}")

    def send_current_command(self):
        """Send current request command when slider is released"""
        value = self.current_slider.value() / 10.0
        self.send_command(f"set uart_req {value:.2f}")

    def update_slider_range(self):
        """Update slider range based on max current setting"""
        max_val = self.max_current_spin.value() * 10
        self.current_slider.setMinimum(-max_val)
        self.current_slider.setMaximum(max_val)
        self.current_slider.setTickInterval(max_val // 10)

    def emergency_stop(self):
        """Send emergency stop command"""
        self.current_slider.setValue(0)
        self.send_command("set uart_req 0")
        self.send_command("set uart_dreq 0")
        self.append_terminal("[EMERGENCY STOP] All motor commands set to 0\n", color="red")

    def send_command(self, command):
        """Send a command to the motor controller"""
        if not self.serial_port or not self.serial_port.is_open:
            self.append_terminal("[ERROR] Not connected to serial port\n")
            return

        try:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            full_command = command + "\r\n"
            self.serial_port.write(full_command.encode('utf-8'))
            self.append_terminal(f"[{timestamp} TX] {command}\n", color="blue")
        except Exception as e:
            self.append_terminal(f"[ERROR] Failed to send command: {e}\n")

    def send_manual_command(self):
        """Send command from manual input field"""
        command = self.cmd_input.text().strip()
        if command:
            self.send_command(command)
            self.cmd_input.clear()

    def append_terminal(self, text, color=None):
        """Append text to terminal with optional color"""
        cursor = self.terminal.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)

        # Create text format with color
        text_format = QTextCharFormat()

        if color:
            if color == "blue":
                text_format.setForeground(QColor(0, 0, 200))
            elif color == "red":
                text_format.setForeground(QColor(200, 0, 0))
            elif color == "green":
                text_format.setForeground(QColor(0, 150, 0))
        else:
            # Default color for received data
            if text.startswith("["):
                if "ERROR" in text:
                    text_format.setForeground(QColor(200, 0, 0))
                elif "INFO" in text:
                    text_format.setForeground(QColor(0, 100, 200))
                elif "TX" in text:
                    text_format.setForeground(QColor(0, 0, 200))
                else:
                    text_format.setForeground(QColor(0, 150, 0))
            else:
                text_format.setForeground(QColor(50, 50, 50))

        cursor.setCharFormat(text_format)
        cursor.insertText(text)
        self.terminal.setTextCursor(cursor)

        # Auto-scroll to bottom
        self.terminal.ensureCursorVisible()

    def setup_plots(self, layout):
        """Setup matplotlib plotting area"""
        plot_group = QGroupBox("Current Waveforms")
        plot_layout = QVBoxLayout()

        # Create matplotlib figure
        self.figure = Figure(figsize=(10, 4))
        self.canvas = FigureCanvas(self.figure)

        # Create subplots
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel('Time (ms)')
        self.ax.set_ylabel('Current (A)')
        self.ax.set_title('Phase Currents (Ia, Ib, Ic)')
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(['Ia', 'Ib', 'Ic'])

        plot_layout.addWidget(self.canvas)
        plot_group.setLayout(plot_layout)
        layout.addWidget(plot_group)

    def toggle_data_collection(self):
        """Start or stop data collection"""
        if not self.collecting_data:
            self.start_data_collection()
        else:
            self.stop_data_collection()

    def start_data_collection(self):
        """Start collecting data"""
        if not self.serial_port or not self.serial_port.is_open:
            self.append_terminal("[ERROR] Cannot collect data - not connected\n")
            return

        # Clear existing data
        self.data_buffer.clear()
        self.samples_label.setText("Samples: 0")

        self.collecting_data = True
        self.collection_start_time = datetime.now()
        self.collect_btn.setText("Collecting...")
        self.collect_btn.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold;")
        self.collect_btn.setEnabled(False)

        # Connect CSV data signal
        if self.reader_thread:
            self.reader_thread.csv_data_received.connect(self.process_snapshot_data)

        # Send phasesnap command
        self.append_terminal("[INFO] Starting phase snapshot capture...\n", color="green")
        self.send_command("phasesnap")

    def stop_data_collection(self):
        """Stop collecting data (automatic after snapshot completes)"""
        self.collecting_data = False
        self.collect_btn.setText("Start Collection")
        self.collect_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.collect_btn.setEnabled(True)

        # Disconnect CSV data signal
        if self.reader_thread:
            try:
                self.reader_thread.csv_data_received.disconnect(self.process_snapshot_data)
            except:
                pass

        self.append_terminal(f"[INFO] Data collection complete ({self.data_buffer.get_size()} samples)\n", color="green")

    def process_snapshot_data(self, csv_data):
        """Process incoming snapshot CSV data"""
        if not self.collecting_data:
            return

        try:
            # csv_data is a list of lists: [[Ia, Ib, Ic, Va, Vb, Vc], ...]
            # Assuming 20kHz PWM, each sample is 50us apart
            sample_period = 50e-6  # 50 microseconds

            for idx, row in enumerate(csv_data):
                if len(row) == 6:
                    ia, ib, ic, va, vb, vc = row
                    timestamp = idx * sample_period

                    # Add to buffer
                    # Using phase currents (Ia, Ib, Ic) as (Iu, Iv, Iw)
                    # Using phase voltages (Va, Vb, Vc) for Vbus (average), Vd, Vq (placeholder)
                    vbus_approx = (va + vb + vc) / 3.0  # Rough approximation

                    self.data_buffer.add_sample(
                        timestamp,
                        vbus_approx,  # Approximated bus voltage
                        ia,  # Iu
                        ib,  # Iv
                        ic,  # Iw
                        0.0,  # Vd (not available in snapshot)
                        0.0,  # Vq (not available in snapshot)
                        0     # angle (not available in snapshot)
                    )

            # Update sample count label
            self.samples_label.setText(f"Samples: {self.data_buffer.get_size()}")

            # Update plot
            if MATPLOTLIB_AVAILABLE:
                self.update_plot()

            # Automatically stop collection after processing
            self.stop_data_collection()

        except Exception as e:
            self.append_terminal(f"[ERROR] Failed to process snapshot data: {e}\n")
            self.stop_data_collection()

    def update_plot(self):
        """Update the current waveform plot"""
        if not MATPLOTLIB_AVAILABLE or self.data_buffer.get_size() < 2:
            return

        try:
            self.ax.clear()
            # Convert timestamp from seconds to milliseconds for better readability
            time_ms = [t * 1000 for t in self.data_buffer.timestamp]

            self.ax.plot(time_ms, self.data_buffer.iu, 'b-', label='Ia', linewidth=0.8)
            self.ax.plot(time_ms, self.data_buffer.iv, 'r-', label='Ib', linewidth=0.8)
            self.ax.plot(time_ms, self.data_buffer.iw, 'g-', label='Ic', linewidth=0.8)
            self.ax.set_xlabel('Time (ms)')
            self.ax.set_ylabel('Current (A)')
            self.ax.set_title(f'Phase Currents - {self.data_buffer.get_size()} samples')
            self.ax.grid(True, alpha=0.3)
            self.ax.legend(loc='upper right')
            self.canvas.draw()
        except Exception as e:
            print(f"Plot update error: {e}")

    def clear_collected_data(self):
        """Clear all collected data"""
        self.data_buffer.clear()
        self.samples_label.setText("Samples: 0")
        if MATPLOTLIB_AVAILABLE:
            self.ax.clear()
            self.ax.set_xlabel('Time (ms)')
            self.ax.set_ylabel('Current (A)')
            self.ax.set_title('Phase Currents (Ia, Ib, Ic)')
            self.ax.grid(True, alpha=0.3)
            self.canvas.draw()
        self.append_terminal("[INFO] Data buffer cleared\n", color="green")

    def export_data(self):
        """Export collected data to CSV file"""
        if self.data_buffer.get_size() == 0:
            self.append_terminal("[ERROR] No data to export\n")
            return

        # Open file dialog
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Data to CSV",
            f"mesc_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv);;All Files (*)"
        )

        if not filename:
            return

        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp_s', 'Vbus_approx', 'Ia', 'Ib', 'Ic', 'Vd', 'Vq', 'angle'])

                for i in range(self.data_buffer.get_size()):
                    writer.writerow([
                        f"{self.data_buffer.timestamp[i]:.6f}",
                        f"{self.data_buffer.vbus[i]:.3f}",
                        f"{self.data_buffer.iu[i]:.3f}",
                        f"{self.data_buffer.iv[i]:.3f}",
                        f"{self.data_buffer.iw[i]:.3f}",
                        f"{self.data_buffer.vd[i]:.3f}",
                        f"{self.data_buffer.vq[i]:.3f}",
                        self.data_buffer.angle[i]
                    ])

            self.append_terminal(f"[INFO] Data exported to {filename}\n", color="green")
            self.statusBar().showMessage(f"Exported {self.data_buffer.get_size()} samples to {filename}")

        except Exception as e:
            self.append_terminal(f"[ERROR] Failed to export data: {e}\n")

    def closeEvent(self, event):
        """Clean up when closing the application"""
        if self.serial_port and self.serial_port.is_open:
            self.emergency_stop()  # Safety: stop motor before closing
            self.disconnect_serial()
        event.accept()


def main():
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    window = MESCControllerGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
