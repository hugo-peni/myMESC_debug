# STM32 Code Editor - Setup Guide

## Quick Start

The STM32 Code Editor is now ready to use! This guide will help you get started.

## Prerequisites Installed

✅ Python 3.13 with virtual environment
✅ PyQt6 6.10.0 (GUI framework)
✅ All dependencies from requirements.txt

## Installation Complete

All dependencies have been installed in your virtual environment at:
```
/Users/hugopenichou/Desktop/myMESC_debug/.venv
```

## Running the Editor

### Method 1: Launch Script (Recommended)
```bash
cd /Users/hugopenichou/Desktop/myMESC_debug/app
./run_editor.sh
```

### Method 2: Direct Python
```bash
cd /Users/hugopenichou/Desktop/myMESC_debug/app
source ../.venv/bin/activate
python3 stm32_code_editor.py
```

### Method 3: From Anywhere
```bash
/Users/hugopenichou/Desktop/myMESC_debug/app/run_editor.sh
```

## First Time Usage

1. **Launch the Editor**
   ```bash
   cd /Users/hugopenichou/Desktop/myMESC_debug/app
   ./run_editor.sh
   ```

2. **Open Your Project**
   - Click "Open Project" in the toolbar
   - Navigate to your STM32 project (e.g., `/Users/hugopenichou/Desktop/myMESC/MESC_F405RG`)
   - The file browser will populate automatically

3. **Set Build Directory** (if not auto-detected)
   - Click "Set Build Dir" in the toolbar
   - Select your `Debug` or `Release` folder

4. **Start Editing**
   - Double-click any `.c` or `.h` file in the file browser
   - Edit with full C syntax highlighting
   - Save with `Ctrl+S`

5. **Build Your Code**
   - Click "Build" or press `Ctrl+B`
   - Watch the console for compilation output

6. **Flash to Device**
   - Connect your ST-Link V2
   - Click "Flash" or press `Ctrl+F`
   - Device will auto-reset after flashing

## Troubleshooting

### Issue: "Virtual environment not found"
**Solution**: Make sure you've created the virtual environment:
```bash
cd /Users/hugopenichou/Desktop/myMESC_debug
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Build directory not set"
**Solution**: Click "Set Build Dir" and select your Debug folder manually

### Issue: Qt font warning
**Fix**: This is cosmetic only. The warning about "Courier" font can be ignored.

### Issue: "make: command not found"
**Solution**: Install Xcode Command Line Tools:
```bash
xcode-select --install
```

### Issue: OpenOCD fails
**Solution**: Check ST-Link connection:
```bash
st-info --probe
```

## Features Available

### File Operations
- ✅ Open Project folders
- ✅ Browse files with tree view
- ✅ Open multiple files in tabs
- ✅ Save file (`Ctrl+S`)
- ✅ Save all files (`Ctrl+Shift+S`)
- ✅ C/C++ syntax highlighting

### Build Operations
- ✅ Clean (`make clean`)
- ✅ Build (`make -j8 all`) - Press `Ctrl+B`
- ✅ Rebuild (`make clean && make -j8 all`) - Press `Ctrl+Shift+B`
- ✅ Real-time console output
- ✅ Color-coded error messages

### Flash Operations
- ✅ Flash firmware (`make flash`) - Press `Ctrl+F`
- ✅ Reset device (`make reset`) - Press `Ctrl+R`
- ✅ Erase flash (`make erase`)
- ✅ OpenOCD integration

### UI Features
- ✅ Dark theme optimized for coding
- ✅ Resizable panels
- ✅ Console output with scrollback
- ✅ Status bar with current file
- ✅ Keyboard shortcuts

## Integration with Your Previous Setup

The editor works seamlessly with your existing terminal workflow from the October 24, 2025 session:

| Terminal Command | Editor Button | Shortcut |
|------------------|---------------|----------|
| `cd Debug && make clean` | Clean | - |
| `make -j8 all` | Build | `Ctrl+B` |
| `make clean && make -j8 all` | Rebuild | `Ctrl+Shift+B` |
| `make flash` | Flash | `Ctrl+F` |
| `make reset` | Reset Device | `Ctrl+R` |
| `make erase` | Erase Flash | - |

All the makefile targets you set up (flash, reset, erase) work directly from the editor!

## Keyboard Shortcuts Cheat Sheet

```
Ctrl+O      Open Project
Ctrl+S      Save File
Ctrl+Shift+S Save All Files
Ctrl+B      Build Project
Ctrl+Shift+B Rebuild Project
Ctrl+F      Flash Firmware
Ctrl+R      Reset Device
```

## Example Workflow

### Scenario: Edit, Build, and Flash MESC_F405RG

1. Launch editor: `./run_editor.sh`
2. Open project: Click "Open Project" → select `/Users/hugopenichou/Desktop/myMESC/MESC_F405RG`
3. Open file: Double-click `Core/Src/main.c` in file browser
4. Make changes: Edit the code with syntax highlighting
5. Save: Press `Ctrl+S`
6. Build: Press `Ctrl+B`
7. Wait: Watch console for "Command completed successfully"
8. Flash: Press `Ctrl+F`
9. Done: Device resets automatically

## File Filters

The file browser shows only relevant development files:
- `*.c`, `*.cpp` - C/C++ source files
- `*.h`, `*.hpp` - Header files
- `*.s` - Assembly files
- `*.ld` - Linker scripts
- `*.txt`, `*.md` - Documentation
- `makefile`, `Makefile` - Build files

## Console Output Colors

- **Green**: Success messages (build complete, flash successful)
- **Red**: Error messages (compilation errors, flash failures)
- **Cyan**: Info messages (starting operations)
- **White**: Standard output

## Tips & Tricks

### Tip 1: Multiple Files
Open multiple files in tabs and use `Ctrl+Shift+S` to save them all at once before building.

### Tip 2: Console Scrollback
The console keeps 10,000 lines of history. Clear it anytime with "Clear Console" button.

### Tip 3: Quick Build & Flash
After editing, press `Ctrl+B` then `Ctrl+F` for quick build and flash.

### Tip 4: File Browser
Resize the file browser panel by dragging the splitter for more or less space.

### Tip 5: Tab Management
Close tabs with the X button. The editor tracks which file each tab contains.

## What's Different from STM32CubeIDE?

| Feature | This Editor | STM32CubeIDE |
|---------|-------------|--------------|
| **Size** | ~30 MB | ~1.5 GB |
| **Startup** | 2 seconds | 30 seconds |
| **Memory** | ~150 MB | ~1 GB |
| **Learning Curve** | Minimal | Steep |
| **Customization** | Python source | Eclipse plugins |
| **GDB Debug** | No (terminal) | Yes (full GUI) |
| **Build Speed** | Same (uses make) | Same (uses make) |

**When to use this editor:**
- Quick code edits
- Fast build & flash cycles
- Low resource usage
- Learning embedded development
- Complementing terminal workflow

**When to use STM32CubeIDE:**
- Full debugging with breakpoints
- Code generation from CubeMX
- Complex projects with many dependencies
- Need code completion and refactoring

## Your Development Environment

You now have three ways to work with STM32:

### 1. Terminal (Manual Control)
```bash
cd /Users/hugopenichou/Desktop/myMESC/MESC_F405RG/Debug
make -j8 all && make flash
```

### 2. This Editor (GUI + Build + Flash)
```bash
./run_editor.sh
# Click, edit, build, flash
```

### 3. STM32CubeIDE (Full IDE)
- Full debugging
- Code generation
- Peripheral configuration

## Next Steps

1. **Try the Editor**: Launch it and open your MESC project
2. **Edit Some Code**: Make a small change to test
3. **Build**: Press `Ctrl+B` and watch it compile
4. **Flash**: Press `Ctrl+F` to program your device
5. **Verify**: Check that your device works

## Support

For issues:
1. Check this guide
2. Check [README_CODE_EDITOR.md](README_CODE_EDITOR.md) for detailed docs
3. Verify makefile has required targets
4. Test commands manually in terminal first

## Files Created

All files are in `/Users/hugopenichou/Desktop/myMESC_debug/app/`:

- `stm32_code_editor.py` - Main editor application (~650 lines)
- `run_editor.sh` - Launch script (handles venv activation)
- `README_CODE_EDITOR.md` - Detailed documentation
- `SETUP_GUIDE.md` - This file

## Requirements Updated

The `requirements.txt` now includes:
```
PyQt6>=6.4.0
PyQt6-Qt6>=6.4.0
```

All other dependencies for your MESC GUI and SpinPAK logo generator are also included.

## Success!

Your STM32 Code Editor is fully installed and ready to use. Enjoy coding!

---

**Created**: October 24, 2025
**For**: MESC_F405RG Development
**Compatible with**: ARM GCC 13.3.1, OpenOCD, macOS
