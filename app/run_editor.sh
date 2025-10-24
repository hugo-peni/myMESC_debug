#!/bin/bash
# Launch script for STM32 Code Editor

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if virtual environment exists
VENV_DIR="$SCRIPT_DIR/../.venv"

if [ ! -d "$VENV_DIR" ]; then
    # Try alternate venv name
    VENV_DIR="$SCRIPT_DIR/../venv"
    if [ ! -d "$VENV_DIR" ]; then
        echo "Virtual environment not found at $VENV_DIR"
        echo "Please create a virtual environment first:"
        echo "  cd $SCRIPT_DIR/.."
        echo "  python3 -m venv .venv"
        echo "  source .venv/bin/activate"
        echo "  pip install -r requirements.txt"
        exit 1
    fi
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Set Qt plugin path
export QT_PLUGIN_PATH="$VENV_DIR/lib/python3.13/site-packages/PyQt6/Qt6/plugins"
export QT_QPA_PLATFORM_PLUGIN_PATH="$QT_PLUGIN_PATH/platforms"

# Run the editor
echo "Starting STM32 Code Editor..."
python3 "$SCRIPT_DIR/stm32_code_editor.py"
