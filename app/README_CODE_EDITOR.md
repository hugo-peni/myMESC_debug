# STM32 Code Editor

A PyQt6-based integrated development environment (IDE) for STM32 firmware development with built-in support for building, flashing, and debugging STM32 projects directly from the editor.

## Features

### Code Editor
- **Syntax Highlighting**: Full C/C++ syntax highlighting with color-coded keywords, types, comments, strings, and preprocessor directives
- **Multiple Tabs**: Open and edit multiple files simultaneously with tab management
- **Dark Theme**: Professional dark theme optimized for long coding sessions
- **Monospace Font**: Uses Menlo font (macOS) for clear code readability
- **Auto-save**: Save individual files or all open files at once

### Project Management
- **File Browser**: Integrated file tree view for easy navigation
- **Project Folders**: Open entire project folders and browse the file structure
- **File Filters**: Automatically filters to show only relevant files (*.c, *.h, *.cpp, etc.)
- **Context Menu**: Right-click files for quick actions

### Build System Integration
- **Clean**: Remove all build artifacts (`make clean`)
- **Build**: Compile the project with parallel jobs (`make -j8 all`)
- **Rebuild**: Clean and build in one command (`make clean && make -j8 all`)
- **Real-time Output**: View compilation progress and errors in the integrated console
- **Error Detection**: Compilation errors are highlighted in red

### Flash & Debug Tools
- **Flash Firmware**: Program your STM32 device via OpenOCD (`make flash`)
- **Reset Device**: Perform a hardware reset (`make reset`)
- **Erase Flash**: Completely erase the device memory (`make erase`)
- **Build Directory Detection**: Automatically finds Debug/Release folders

### Console Output
- **Real-time Feedback**: See command output as it happens
- **Color-coded Messages**:
  - Green for success messages
  - Red for errors
  - Cyan for informational messages
- **Scrollback Buffer**: Up to 10,000 lines of output history
- **Clear Console**: One-click console clearing

## Installation

### Prerequisites

1. **Python 3.8+** with PyQt6
2. **ARM GNU Toolchain 13.3.1** (as installed in your previous session)
3. **OpenOCD** for flashing
4. **Make** build tool

### Setup Virtual Environment

```bash
# Navigate to project root
cd /Users/hugopenichou/Desktop/myMESC_debug

# Create virtual environment (if not already created)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Verify Dependencies

```bash
# Check PyQt6
python3 -c "import PyQt6; print('PyQt6 installed')"

# Check ARM toolchain
arm-none-eabi-gcc --version

# Check OpenOCD
openocd --version
```

## Usage

### Starting the Editor

#### Option 1: Using the launch script (Recommended)
```bash
cd /Users/hugopenichou/Desktop/myMESC_debug/app
./run_editor.sh
```

#### Option 2: Direct Python execution
```bash
cd /Users/hugopenichou/Desktop/myMESC_debug/app
source ../venv/bin/activate
python3 stm32_code_editor.py
```

### Opening a Project

1. Click **"Open Project"** in the toolbar (or press `Ctrl+O`)
2. Navigate to your STM32 project folder (e.g., `/Users/hugopenichou/Desktop/myMESC/MESC_F405RG`)
3. The file browser will populate with your project files
4. The editor will auto-detect the `Debug` or `Release` folder as the build directory

### Editing Files

1. **Open File**: Double-click any file in the file browser
2. **Edit**: Type your code with full syntax highlighting
3. **Save**: Press `Ctrl+S` or click "Save"
4. **Save All**: Press `Ctrl+Shift+S` or click "Save All"
5. **Close Tab**: Click the X on the tab or use the close button

### Building Your Project

1. **Set Build Directory** (if not auto-detected): Click "Set Build Dir" and select your `Debug` or `Release` folder
2. **Build**: Click "Build" or press `Ctrl+B`
3. **Watch Output**: Monitor the console for compilation progress
4. **Check Results**: Green "Command completed successfully" means success

### Flashing to Device

1. **Connect ST-Link**: Plug in your ST-Link V2 debugger
2. **Build First**: Make sure your project is compiled
3. **Flash**: Click "Flash" or press `Ctrl+F`
4. **Monitor Progress**: Watch the console for OpenOCD output
5. **Success**: Device will automatically reset after flashing

### Additional Operations

#### Reset Device
- Click "Reset Device" or press `Ctrl+R`
- Performs a hardware reset without reflashing

#### Erase Flash
- Click "Erase Flash"
- Confirm the warning dialog
- Completely erases the device memory

#### Clean Build
- Click "Clean" to remove build artifacts
- Useful before a fresh rebuild

#### Rebuild
- Click "Rebuild" or press `Ctrl+Shift+B`
- Performs clean + build in one operation

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open Project |
| `Ctrl+S` | Save File |
| `Ctrl+Shift+S` | Save All Files |
| `Ctrl+B` | Build Project |
| `Ctrl+Shift+B` | Rebuild Project |
| `Ctrl+F` | Flash Firmware |
| `Ctrl+R` | Reset Device |

## File Filters

The file browser shows only relevant files for STM32 development:
- `*.c`, `*.cpp` - C/C++ source files
- `*.h`, `*.hpp` - Header files
- `*.s` - Assembly files
- `*.ld` - Linker scripts
- `*.txt`, `*.md` - Documentation
- `makefile`, `Makefile` - Build files

## Integration with Your Makefile

The editor expects your `makefile` to have these targets:

```makefile
# Standard targets
all: $(BUILD_ARTIFACT)
clean: # Remove build artifacts

# Flash targets (as you set up in your previous session)
flash: all
	openocd -f interface/stlink-v2.cfg -f target/stm32f4x.cfg \
	  -c "program $(BUILD_ARTIFACT_NAME).elf verify reset exit"

reset:
	openocd -f interface/stlink-v2.cfg -f target/stm32f4x.cfg \
	  -c "init; reset; exit"

erase:
	openocd -f interface/stlink-v2.cfg -f target/stm32f4x.cfg \
	  -c "init; reset halt; stm32f4x mass_erase 0; exit"
```

Your MESC_F405RG project already has these targets configured!

## Console Output Examples

### Successful Build
```
============================================================
Building project
============================================================

$ make -j8 all
arm-none-eabi-gcc -c "main.c" -o "main.o"
arm-none-eabi-gcc -c "stm32f4xx_it.c" -o "stm32f4xx_it.o"
...
Finished building target: MESC_F405RG.elf

Command completed successfully
```

### Successful Flash
```
============================================================
Flashing firmware
============================================================

$ make flash
Open On-Chip Debugger 0.12.0
...
** Programming Started **
** Programming Finished **
** Verified OK **
** Resetting Target **

Command completed successfully
```

### Compilation Error
```
============================================================
Building project
============================================================

$ make -j8 all
arm-none-eabi-gcc -c "main.c" -o "main.o"
main.c:42:5: error: 'GPIO_PIN_13' undeclared
   42 |     GPIO_PIN_13;
      |     ^~~~~~~~~~~

Command failed with exit code 2
```

## Architecture

### Components

```
STM32CodeEditor (QMainWindow)
├── Toolbar (QToolBar)
│   ├── File Actions (Open, Save, Save All)
│   ├── Build Actions (Clean, Build, Rebuild)
│   ├── Flash Actions (Flash, Reset, Erase)
│   └── Utility Actions (Clear Console, Set Build Dir)
│
├── Main Splitter (Vertical)
│   ├── Top Splitter (Horizontal)
│   │   ├── File Browser (QTreeView)
│   │   │   └── File System Model (QFileSystemModel)
│   │   └── Editor Tabs (QTabWidget)
│   │       └── Code Editors (CodeEditor)
│   │           └── Syntax Highlighter (CSyntaxHighlighter)
│   └── Console Output (ConsoleOutput)
│
└── Status Bar (QStatusBar)
```

### Threading

The editor uses `BuildThread (QThread)` for running build/flash commands:
- **Non-blocking UI**: Editor remains responsive during compilation
- **Real-time Output**: Console updates as compilation progresses
- **Process Control**: Can monitor and control running processes

### Syntax Highlighting

C/C++ syntax highlighting with:
- **Keywords**: if, else, for, while, return, etc. (Blue, Bold)
- **Types**: uint32_t, int16_t, GPIO_TypeDef, etc. (Cyan)
- **Comments**: // and /* */ style (Green)
- **Strings**: "..." and '...' (Orange)
- **Numbers**: Decimal and hexadecimal (Light green)
- **Preprocessor**: #include, #define, etc. (Purple)

## Customization

### Changing the Font

Edit [stm32_code_editor.py](stm32_code_editor.py) around line 157:

```python
font = QFont("Menlo", 11)  # Change font family and size
```

### Changing Colors

Edit the syntax highlighter around line 37-58:

```python
keyword_format.setForeground(QColor(86, 156, 214))  # Change keyword color
```

### Adding File Types

Edit the file filter around line 463:

```python
self.file_model.setNameFilters([
    "*.c", "*.cpp", "*.h", "*.hpp", "*.s", "*.ld",
    "*.txt", "*.md", "makefile", "Makefile",
    "*.py"  # Add Python files
])
```

### Changing Theme

The editor uses a dark theme defined in `apply_dark_theme()` around line 506. You can customize colors by editing the stylesheet.

## Troubleshooting

### "Build directory not set"
- **Solution**: Click "Set Build Dir" and select your `Debug` or `Release` folder
- Or open a project that contains a `Debug` folder for auto-detection

### "A build process is already running"
- **Solution**: Wait for the current build/flash operation to complete
- Check the console for progress

### "Failed to open file"
- **Solution**: Check file permissions
- Ensure the file is a text file (not binary)

### OpenOCD connection issues
- **Solution**: Check ST-Link is connected
- Run `st-info --probe` to verify connection
- Kill any competing processes: `sudo killall openocd`

### Makefile targets not working
- **Solution**: Verify your makefile has the required targets
- Check that you're in the correct build directory
- Test manually: `cd Debug && make flash`

## Comparison to STM32CubeIDE

| Feature | STM32 Code Editor | STM32CubeIDE |
|---------|-------------------|--------------|
| **Size** | ~30 MB (Python + PyQt6) | ~1.5 GB |
| **Startup Time** | ~2 seconds | ~30 seconds |
| **Syntax Highlighting** | ✅ C/C++ | ✅ C/C++ |
| **Build System** | ✅ Make | ✅ Make + Eclipse |
| **Flash Support** | ✅ OpenOCD | ✅ OpenOCD |
| **GDB Debugging** | ❌ (Terminal only) | ✅ Full GUI |
| **Code Completion** | ❌ | ✅ |
| **Refactoring** | ❌ | ✅ |
| **Resource Usage** | Low | High |
| **Customization** | ✅ Python source | ⚠️ Eclipse plugins |

**Best Use Cases**:
- **This Editor**: Quick edits, building, flashing, lightweight development
- **STM32CubeIDE**: Full debugging, code generation, complex projects

## Advanced Usage

### Custom Build Commands

You can modify the build commands by editing these methods:

```python
def build_project(self):
    self.run_build_command("make -j8 all", "Building project")
```

Change `"make -j8 all"` to any custom command.

### Adding New Toolbar Actions

Add custom actions in `create_toolbar()`:

```python
custom_action = QAction("My Action", self)
custom_action.triggered.connect(self.my_custom_function)
toolbar.addAction(custom_action)
```

### Extending File Types

To add syntax highlighting for other languages, create a new highlighter class similar to `CSyntaxHighlighter`.

## Known Limitations

1. **No Code Completion**: For full IntelliSense, use STM32CubeIDE or VSCode with C/C++ extensions
2. **No Integrated Debugging**: Use `arm-none-eabi-gdb` with OpenOCD in terminal
3. **No Git Integration**: Use terminal or Git GUI tools
4. **No Multi-project Support**: One project at a time

## Future Enhancements

Potential improvements:
- [ ] Unsaved changes detection
- [ ] Find/Replace functionality
- [ ] Code folding
- [ ] Line numbers in editor
- [ ] Terminal integration
- [ ] Serial monitor for USB CDC
- [ ] Settings persistence
- [ ] Custom build configurations
- [ ] Git integration
- [ ] Multiple project support

## Technical Details

**Language**: Python 3.8+
**GUI Framework**: PyQt6
**Build System**: GNU Make
**Toolchain**: ARM GCC 13.3.1
**Flash Tool**: OpenOCD
**Lines of Code**: ~650

## Support

For issues or questions:
1. Check this README
2. Check console output for error messages
3. Verify your makefile has required targets
4. Test commands manually in terminal

## License

This editor is part of your MESC development environment.

## Credits

Created to complement your STM32 command-line development workflow established in the October 24, 2025 session.

**Author**: Hugo
**Date**: October 2025
**Project**: MESC_F405RG Development Environment
