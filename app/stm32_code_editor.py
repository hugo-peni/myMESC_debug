#!/usr/bin/env python3
"""
STM32 Code Editor with Build & Flash Support
A PyQt6-based code editor for STM32 development with integrated build tools.
"""

import sys
import os
import subprocess
import re
from pathlib import Path

# Fix Qt plugin path for PyQt6 on macOS
# This allows the script to run directly without setting environment variables
if sys.platform == 'darwin':  # macOS
    # Try to find PyQt6 installation
    try:
        import PyQt6
        pyqt6_path = Path(PyQt6.__file__).parent
        qt_plugins = pyqt6_path / "Qt6" / "plugins"
        if qt_plugins.exists():
            os.environ['QT_PLUGIN_PATH'] = str(qt_plugins)
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(qt_plugins / "platforms")
    except ImportError:
        pass
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QWidget, QVBoxLayout,
    QHBoxLayout, QSplitter, QTreeView, QToolBar,
    QStatusBar, QTabWidget, QPlainTextEdit, QMessageBox, QFileDialog,
    QInputDialog, QMenu
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QProcess, QDir, QModelIndex, QTimer
)
from PyQt6.QtGui import (
    QAction, QIcon, QFont, QColor, QPalette, QSyntaxHighlighter,
    QTextCharFormat, QKeySequence, QFileSystemModel
)


class CSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for C/C++ code."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Define formatting styles
        self.formats = {}

        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(86, 156, 214))  # Blue
        keyword_format.setFontWeight(QFont.Weight.Bold)
        self.formats['keyword'] = keyword_format

        # Types
        type_format = QTextCharFormat()
        type_format.setForeground(QColor(78, 201, 176))  # Cyan
        self.formats['type'] = type_format

        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(106, 153, 85))  # Green
        self.formats['comment'] = comment_format

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(206, 145, 120))  # Orange
        self.formats['string'] = string_format

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(181, 206, 168))  # Light green
        self.formats['number'] = number_format

        # Preprocessor
        preprocessor_format = QTextCharFormat()
        preprocessor_format.setForeground(QColor(197, 134, 192))  # Purple
        self.formats['preprocessor'] = preprocessor_format

        # Define patterns
        self.rules = []

        # C/C++ keywords
        keywords = [
            'auto', 'break', 'case', 'char', 'const', 'continue', 'default',
            'do', 'double', 'else', 'enum', 'extern', 'float', 'for', 'goto',
            'if', 'int', 'long', 'register', 'return', 'short', 'signed',
            'sizeof', 'static', 'struct', 'switch', 'typedef', 'union',
            'unsigned', 'void', 'volatile', 'while', 'bool', 'true', 'false',
            'class', 'namespace', 'public', 'private', 'protected', 'virtual'
        ]
        self.rules.extend([
            (r'\b' + keyword + r'\b', self.formats['keyword'])
            for keyword in keywords
        ])

        # Types
        types = [
            'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t',
            'int8_t', 'int16_t', 'int32_t', 'int64_t',
            'size_t', 'bool', 'GPIO_TypeDef', 'TIM_TypeDef'
        ]
        self.rules.extend([
            (r'\b' + t + r'\b', self.formats['type'])
            for t in types
        ])

        # Numbers
        self.rules.append((r'\b[0-9]+[ulUL]*\b', self.formats['number']))
        self.rules.append((r'\b0x[0-9a-fA-F]+[ulUL]*\b', self.formats['number']))

        # Preprocessor directives
        self.rules.append((r'^\s*#\s*\w+.*$', self.formats['preprocessor']))

        # Single-line comments
        self.rules.append((r'//[^\n]*', self.formats['comment']))

        # Strings
        self.rules.append((r'"(?:[^"\\]|\\.)*"', self.formats['string']))
        self.rules.append((r"'(?:[^'\\]|\\.)*'", self.formats['string']))

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given text block."""
        # Apply all rules
        for pattern, fmt in self.rules:
            for match in re.finditer(pattern, text, re.MULTILINE):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, fmt)

        # Multi-line comments
        self.setCurrentBlockState(0)
        start_index = 0

        if self.previousBlockState() != 1:
            start_index = text.find('/*')

        while start_index >= 0:
            end_index = text.find('*/', start_index)

            if end_index == -1:
                self.setCurrentBlockState(1)
                comment_length = len(text) - start_index
            else:
                comment_length = end_index - start_index + 2

            self.setFormat(start_index, comment_length, self.formats['comment'])
            start_index = text.find('/*', start_index + comment_length)


class CodeEditor(QTextEdit):
    """Enhanced text editor with line numbers and C syntax highlighting."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Set font
        font = QFont("Menlo", 11)  # Monospace font for macOS
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        # Set tab width to 4 spaces
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(' '))

        # Enable syntax highlighting
        self.highlighter = CSyntaxHighlighter(self.document())

        # Set dark theme colors
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
        self.setPalette(palette)

        self.file_path = None

    def set_file_path(self, path):
        """Set the file path for this editor."""
        self.file_path = path

    def get_file_path(self):
        """Get the file path for this editor."""
        return self.file_path


class ConsoleOutput(QPlainTextEdit):
    """Console output widget for displaying build/flash output."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)

        # Set font
        font = QFont("Menlo", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        # Set dark theme
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(20, 20, 20))
        palette.setColor(QPalette.ColorRole.Text, QColor(200, 200, 200))
        self.setPalette(palette)

        self.setMaximumBlockCount(10000)  # Limit scrollback

    def append_text(self, text, color=None):
        """Append text with optional color."""
        if color:
            self.appendHtml(f'<span style="color: {color};">{text}</span>')
        else:
            self.appendPlainText(text)

        # Auto-scroll to bottom
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def append_error(self, text):
        """Append error text in red."""
        self.append_text(text, "#ff5555")

    def append_success(self, text):
        """Append success text in green."""
        self.append_text(text, "#50fa7b")

    def append_info(self, text):
        """Append info text in cyan."""
        self.append_text(text, "#8be9fd")


class BuildThread(QThread):
    """Thread for running build/flash commands."""

    output_ready = pyqtSignal(str, str)  # text, type (normal/error/success)
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, command, working_dir):
        super().__init__()
        self.command = command
        self.working_dir = working_dir
        self.process = None

    def run(self):
        """Run the build command."""
        try:
            self.output_ready.emit(f"\n$ {self.command}\n", "info")

            # Run command
            self.process = subprocess.Popen(
                self.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.working_dir,
                text=True,
                bufsize=1
            )

            # Read output in real-time
            while True:
                output = self.process.stdout.readline()
                if output:
                    self.output_ready.emit(output, "normal")

                error = self.process.stderr.readline()
                if error:
                    self.output_ready.emit(error, "error")

                # Check if process finished
                if output == '' and error == '' and self.process.poll() is not None:
                    break

            # Get return code
            return_code = self.process.wait()

            if return_code == 0:
                self.finished.emit(True, "Command completed successfully")
            else:
                self.finished.emit(False, f"Command failed with exit code {return_code}")

        except Exception as e:
            self.output_ready.emit(f"Error: {str(e)}\n", "error")
            self.finished.emit(False, str(e))

    def stop(self):
        """Stop the running process."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=5)


class STM32CodeEditor(QMainWindow):
    """Main STM32 Code Editor application."""

    def __init__(self):
        super().__init__()

        # Configuration
        self.project_path = None
        self.build_dir = None
        self.current_editor = None
        self.build_thread = None

        # Initialize UI
        self.init_ui()

        # Load settings
        self.load_settings()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("STM32 Code Editor")
        self.setGeometry(100, 100, 1400, 900)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create main splitter (vertical)
        main_splitter = QSplitter(Qt.Orientation.Vertical)

        # Top splitter (horizontal) - file browser and editor
        top_splitter = QSplitter(Qt.Orientation.Horizontal)

        # File browser
        self.file_browser = self.create_file_browser()
        top_splitter.addWidget(self.file_browser)

        # Editor tabs
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.tabCloseRequested.connect(self.close_tab)
        self.editor_tabs.currentChanged.connect(self.on_tab_changed)
        top_splitter.addWidget(self.editor_tabs)

        # Set sizes for top splitter
        top_splitter.setSizes([250, 1150])

        main_splitter.addWidget(top_splitter)

        # Console output
        self.console = ConsoleOutput()
        main_splitter.addWidget(self.console)

        # Set sizes for main splitter
        main_splitter.setSizes([600, 300])

        main_layout.addWidget(main_splitter)

        # Create toolbar (after console is created)
        self.create_toolbar()

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Apply dark theme
        self.apply_dark_theme()

        self.console.append_success("STM32 Code Editor initialized")
        self.console.append_info("Open a project folder to start editing")

    def create_toolbar(self):
        """Create the application toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # File actions
        open_folder_action = QAction("Open Project", self)
        open_folder_action.setShortcut(QKeySequence("Ctrl+O"))
        open_folder_action.triggered.connect(self.open_project)
        toolbar.addAction(open_folder_action)

        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save_current_file)
        toolbar.addAction(save_action)

        save_all_action = QAction("Save All", self)
        save_all_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_all_action.triggered.connect(self.save_all_files)
        toolbar.addAction(save_all_action)

        toolbar.addSeparator()

        # Build actions
        clean_action = QAction("Clean", self)
        clean_action.triggered.connect(self.clean_build)
        toolbar.addAction(clean_action)

        build_action = QAction("Build", self)
        build_action.setShortcut(QKeySequence("Ctrl+B"))
        build_action.triggered.connect(self.build_project)
        toolbar.addAction(build_action)

        rebuild_action = QAction("Rebuild", self)
        rebuild_action.setShortcut(QKeySequence("Ctrl+Shift+B"))
        rebuild_action.triggered.connect(self.rebuild_project)
        toolbar.addAction(rebuild_action)

        toolbar.addSeparator()

        # Flash actions
        flash_action = QAction("Flash", self)
        flash_action.setShortcut(QKeySequence("Ctrl+F"))
        flash_action.triggered.connect(self.flash_firmware)
        toolbar.addAction(flash_action)

        reset_action = QAction("Reset Device", self)
        reset_action.setShortcut(QKeySequence("Ctrl+R"))
        reset_action.triggered.connect(self.reset_device)
        toolbar.addAction(reset_action)

        erase_action = QAction("Erase Flash", self)
        erase_action.triggered.connect(self.erase_flash)
        toolbar.addAction(erase_action)

        toolbar.addSeparator()

        # Utility actions
        clear_console_action = QAction("Clear Console", self)
        clear_console_action.triggered.connect(self.console.clear)
        toolbar.addAction(clear_console_action)

        set_build_dir_action = QAction("Set Build Dir", self)
        set_build_dir_action.triggered.connect(self.set_build_directory)
        toolbar.addAction(set_build_dir_action)

    def create_file_browser(self):
        """Create the file browser widget."""
        file_browser = QTreeView()
        file_browser.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        file_browser.customContextMenuRequested.connect(self.show_file_context_menu)

        # Create file system model
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(QDir.rootPath())

        # Set filters to show only relevant files
        self.file_model.setNameFilters([
            "*.c", "*.cpp", "*.h", "*.hpp", "*.s", "*.ld",
            "*.txt", "*.md", "makefile", "Makefile"
        ])
        self.file_model.setNameFilterDisables(False)

        file_browser.setModel(self.file_model)
        file_browser.setAnimated(True)
        file_browser.setIndentation(20)
        file_browser.setSortingEnabled(True)

        # Hide unnecessary columns
        file_browser.setColumnHidden(1, True)  # Size
        file_browser.setColumnHidden(2, True)  # Type
        file_browser.setColumnHidden(3, True)  # Modified

        # Connect double-click to open file
        file_browser.doubleClicked.connect(self.open_file_from_browser)

        return file_browser

    def show_file_context_menu(self, position):
        """Show context menu for file browser."""
        menu = QMenu()

        index = self.file_browser.indexAt(position)
        if index.isValid():
            file_path = self.file_model.filePath(index)

            if os.path.isfile(file_path):
                open_action = menu.addAction("Open")
                open_action.triggered.connect(lambda: self.open_file(file_path))

        menu.exec(self.file_browser.viewport().mapToGlobal(position))

    def apply_dark_theme(self):
        """Apply dark theme to the application."""
        dark_stylesheet = """
        QMainWindow, QWidget {
            background-color: #1e1e1e;
            color: #d4d4d4;
        }
        QToolBar {
            background-color: #2d2d30;
            border: none;
            padding: 5px;
        }
        QToolBar QToolButton {
            background-color: #2d2d30;
            color: #d4d4d4;
            border: none;
            padding: 5px 10px;
            margin: 2px;
        }
        QToolBar QToolButton:hover {
            background-color: #3e3e42;
        }
        QToolBar QToolButton:pressed {
            background-color: #007acc;
        }
        QTreeView {
            background-color: #252526;
            color: #d4d4d4;
            border: none;
        }
        QTreeView::item:selected {
            background-color: #094771;
        }
        QTreeView::item:hover {
            background-color: #2a2d2e;
        }
        QTabWidget::pane {
            border: 1px solid #3e3e42;
            background-color: #1e1e1e;
        }
        QTabBar::tab {
            background-color: #2d2d30;
            color: #d4d4d4;
            padding: 8px 15px;
            border: none;
        }
        QTabBar::tab:selected {
            background-color: #1e1e1e;
            border-bottom: 2px solid #007acc;
        }
        QTabBar::tab:hover {
            background-color: #3e3e42;
        }
        QStatusBar {
            background-color: #007acc;
            color: white;
        }
        """
        self.setStyleSheet(dark_stylesheet)

    def open_project(self):
        """Open a project folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Project Folder",
            str(Path.home())
        )

        if folder:
            self.project_path = folder
            self.file_browser.setRootIndex(self.file_model.index(folder))
            self.console.append_success(f"Opened project: {folder}")
            self.status_bar.showMessage(f"Project: {folder}")

            # Try to auto-detect build directory
            debug_dir = os.path.join(folder, "Debug")
            release_dir = os.path.join(folder, "Release")

            if os.path.exists(debug_dir):
                self.build_dir = debug_dir
                self.console.append_info(f"Auto-detected build directory: {debug_dir}")
            elif os.path.exists(release_dir):
                self.build_dir = release_dir
                self.console.append_info(f"Auto-detected build directory: {release_dir}")

    def set_build_directory(self):
        """Set the build directory manually."""
        if not self.project_path:
            QMessageBox.warning(self, "Warning", "Please open a project first")
            return

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Build Directory",
            self.project_path
        )

        if folder:
            self.build_dir = folder
            self.console.append_success(f"Build directory set to: {folder}")

    def open_file_from_browser(self, index: QModelIndex):
        """Open file from file browser double-click."""
        file_path = self.file_model.filePath(index)
        if os.path.isfile(file_path):
            self.open_file(file_path)

    def open_file(self, file_path):
        """Open a file in a new tab."""
        # Check if file is already open
        for i in range(self.editor_tabs.count()):
            editor = self.editor_tabs.widget(i)
            if editor.get_file_path() == file_path:
                self.editor_tabs.setCurrentIndex(i)
                return

        # Create new editor
        editor = CodeEditor()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                editor.setPlainText(content)

            editor.set_file_path(file_path)

            # Add tab
            file_name = os.path.basename(file_path)
            index = self.editor_tabs.addTab(editor, file_name)
            self.editor_tabs.setCurrentIndex(index)

            self.console.append_info(f"Opened: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file: {str(e)}")

    def close_tab(self, index):
        """Close a tab."""
        editor = self.editor_tabs.widget(index)

        # TODO: Check if file has unsaved changes

        self.editor_tabs.removeTab(index)

    def on_tab_changed(self, index):
        """Handle tab change."""
        if index >= 0:
            self.current_editor = self.editor_tabs.widget(index)
            file_path = self.current_editor.get_file_path()
            self.status_bar.showMessage(f"Editing: {file_path}")
        else:
            self.current_editor = None

    def save_current_file(self):
        """Save the current file."""
        if not self.current_editor:
            return

        file_path = self.current_editor.get_file_path()
        if not file_path:
            return

        try:
            content = self.current_editor.toPlainText()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.console.append_success(f"Saved: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")

    def save_all_files(self):
        """Save all open files."""
        for i in range(self.editor_tabs.count()):
            editor = self.editor_tabs.widget(i)
            file_path = editor.get_file_path()

            if file_path:
                try:
                    content = editor.toPlainText()
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)

                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save {file_path}: {str(e)}")
                    return

        self.console.append_success("All files saved")

    def run_build_command(self, command, description):
        """Run a build command in a thread."""
        if not self.build_dir:
            QMessageBox.warning(self, "Warning", "Please set the build directory first")
            return

        if self.build_thread and self.build_thread.isRunning():
            QMessageBox.warning(self, "Warning", "A build process is already running")
            return

        self.console.append_info(f"\n{'='*60}")
        self.console.append_info(f"{description}")
        self.console.append_info(f"{'='*60}")

        self.build_thread = BuildThread(command, self.build_dir)
        self.build_thread.output_ready.connect(self.on_build_output)
        self.build_thread.finished.connect(self.on_build_finished)
        self.build_thread.start()

        self.status_bar.showMessage(f"{description}...")

    def on_build_output(self, text, output_type):
        """Handle build output."""
        if output_type == "error":
            self.console.append_error(text.rstrip())
        elif output_type == "info":
            self.console.append_info(text.rstrip())
        else:
            self.console.appendPlainText(text.rstrip())

    def on_build_finished(self, success, message):
        """Handle build completion."""
        if success:
            self.console.append_success(f"\n{message}")
            self.status_bar.showMessage("Ready")
        else:
            self.console.append_error(f"\n{message}")
            self.status_bar.showMessage("Build failed")

    def clean_build(self):
        """Clean the build directory."""
        self.run_build_command("make clean", "Cleaning build artifacts")

    def build_project(self):
        """Build the project."""
        self.run_build_command("make -j8 all", "Building project")

    def rebuild_project(self):
        """Rebuild the project (clean + build)."""
        self.run_build_command("make clean && make -j8 all", "Rebuilding project")

    def flash_firmware(self):
        """Flash firmware to device."""
        self.run_build_command("make flash", "Flashing firmware")

    def reset_device(self):
        """Reset the device."""
        self.run_build_command("make reset", "Resetting device")

    def erase_flash(self):
        """Erase the device flash."""
        reply = QMessageBox.question(
            self,
            "Confirm Erase",
            "Are you sure you want to erase the entire flash memory?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.run_build_command("make erase", "Erasing flash memory")

    def load_settings(self):
        """Load application settings."""
        # TODO: Implement settings persistence
        pass

    def closeEvent(self, event):
        """Handle application close."""
        # TODO: Check for unsaved changes
        event.accept()


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("STM32 Code Editor")

    editor = STM32CodeEditor()
    editor.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
