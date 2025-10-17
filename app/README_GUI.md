# MESC Motor Controller GUI

A PyQt6-based graphical user interface for controlling MESC motor controllers via serial connection.

## Features

- **Serial Port Scanning**: Automatically detects and lists all available serial ports
- **Real-time Terminal**: Monitor all data going in and out of the serial connection
- **Current Control Slider**: Adjustable slider for setting motor current (-3.0A to +3.0A by default)
- **Emergency Stop Button**: Large, prominent emergency stop button that immediately sets all motor commands to 0
- **Quick Commands**: One-click buttons for common MESC commands (status, errors, power data)
- **Manual Command Entry**: Send any MESC command directly via the command line interface
- **Color-coded Output**: Easy-to-read terminal with color-coded messages (TX, RX, errors, info)
- **Data Collection**: Start/stop data logging with real-time current monitoring
- **Live Plotting**: Real-time visualization of phase currents (Iu, Iv, Iw)
- **CSV Export**: Export collected data to CSV file for analysis in Excel, MATLAB, Python, etc.

## Installation

1. Install Python 3.8 or higher

2. Install required dependencies:
```bash
pip install -r requirements_gui.txt
```

Or install manually:
```bash
pip install PyQt6 pyserial matplotlib
```

## Usage

1. Run the application:
```bash
python mesc_controller_gui.py
```

2. Select your serial port from the dropdown (or click "Scan Ports" to refresh)

3. Choose the correct baud rate (default: 115200)

4. Click "Connect"

5. Use the slider to control motor current, or use quick commands

6. Monitor all communication in the terminal window

## Data Collection and Analysis

The GUI includes a powerful data collection system for capturing and visualizing motor current data.

### Collecting Data

1. **Connect** to your motor controller

2. **Start Collection**: Click the "Start Collection" button
   - The GUI sends the `phasesnap` command to MESC
   - MESC captures 600 samples at PWM frequency (~20kHz, or ~50μs per sample)
   - Total capture time: ~30ms
   - The button shows "Collecting..." while capturing

3. **Automatic Processing**: Data is automatically processed when capture completes
   - Phase currents (Ia, Ib, Ic) are parsed from the terminal output
   - Phase voltages (Va, Vb, Vc) are also captured
   - Live plot updates automatically
   - Button returns to "Start Collection" when done

4. **View Results**: The plot shows all three phase currents
   - Blue line: Phase A current (Ia)
   - Red line: Phase B current (Ib)
   - Green line: Phase C current (Ic)
   - Time axis in milliseconds
   - Zoomed view of the 30ms capture window

5. **Export Data**: Click "Export CSV" to save data
   - Choose filename and location
   - Data saved with columns: timestamp_s, Vbus_approx, Ia, Ib, Ic, Vd, Vq, angle
   - Compatible with Excel, MATLAB, Python, etc.
   - High resolution: 600 samples in ~30ms

6. **Clear Data**: Click "Clear Data" to reset buffer and start fresh

### Captured Variables

The `phasesnap` command captures:
- **Ia, Ib, Ic**: Phase currents A, B, C (A) - instantaneous values
- **Va, Vb, Vc**: Phase voltages A, B, C (V) - instantaneous values
- **Sample rate**: ~20kHz (50μs period)
- **Total samples**: 600
- **Capture duration**: ~30ms

### Analysis Tips

After exporting data to CSV, you can analyze it with:

**Python/Matplotlib:**
```python
import pandas as pd
import matplotlib.pyplot as plt

data = pd.read_csv('mesc_data.csv')
plt.plot(data['timestamp'], data['Iu'], label='Iu')
plt.plot(data['timestamp'], data['Iv'], label='Iv')
plt.plot(data['timestamp'], data['Iw'], label='Iw')
plt.xlabel('Time (s)')
plt.ylabel('Current (A)')
plt.legend()
plt.grid(True)
plt.show()
```

**MATLAB:**
```matlab
data = readtable('mesc_data.csv');
plot(data.timestamp, data.Iu, 'b-', ...
     data.timestamp, data.Iv, 'r-', ...
     data.timestamp, data.Iw, 'g-')
xlabel('Time (s)')
ylabel('Current (A)')
legend('Iu', 'Iv', 'Iw')
grid on
```

## Safety Features

- Emergency stop button always visible and accessible
- Motor commands automatically set to 0 when closing the application
- Connection status always displayed
- All commands are logged with timestamps

## MESC Commands

The GUI supports all MESC serial commands including:

- `set uart_req <value>` - Set motor current/torque
- `status start/stop` - Real-time status monitoring
- `error` - Display error flags
- `powerdata` - Show power data
- `measure` - Run motor measurements
- `get <variable>` - Read configuration
- `set <variable> <value>` - Write configuration
- `save` / `load` - Save/load settings to flash

For a complete command reference, see the MESC documentation.

## Troubleshooting

**Port not found:**
- Check USB cable connection
- Check device drivers are installed
- Click "Scan Ports" to refresh the list

**Connection fails:**
- Verify correct baud rate (usually 115200)
- Check if port is already open in another application
- Try unplugging and reconnecting the device

**No response from controller:**
- Verify correct port is selected
- Check terminal for error messages
- Try sending simple commands like "help" or "error"

## Keyboard Shortcuts

- **Enter** in command field: Send command
- **Escape**: Emergency stop (when slider is focused)

## License

This GUI application is provided as-is for use with MESC motor controllers.
