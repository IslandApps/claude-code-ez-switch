#!/bin/bash

# EZ-Switch Run Script - Cross-Platform (Linux & Windows Bash)

# --- Configuration ---
APP_SCRIPT="ezswitch.py"
# ---------------------

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "------------------------------------------"
echo "   Claude Code EZ-Switch - Starter"
echo "------------------------------------------"

# 1. Detect OS
OS_TYPE="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="linux"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS_TYPE="windows"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
fi

echo "[*] Detected OS: $OS_TYPE"

# 2. Identify Python Command
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    # Check if 'python' is actually Python 3
    if [[ "$(python --version 2>&1)" == *"Python 3"* ]]; then
        PYTHON_CMD="python"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "[!] Error: Python 3 is not installed or not in PATH."
    exit 1
fi

# 3. Check and Install Dependencies
echo "[*] Checking dependencies..."

if [[ "$OS_TYPE" == "linux" ]]; then
    # Check for Tkinter (common missing dependency on Linux)
    if ! $PYTHON_CMD -c "import tkinter" &> /dev/null; then
        echo "[!] Tkinter is missing. Attempting to install 'python3-tk'..."
        if command -v apt-get &> /dev/null; then
            echo "[*] Running: sudo apt-get update && sudo apt-get install -y python3-tk"
            sudo apt-get update && sudo apt-get install -y python3-tk
        else
            echo "[!] Error: Could not install python3-tk automatically. Please install it manually."
            exit 1
        fi
    fi
elif [[ "$OS_TYPE" == "windows" ]]; then
    # Check for pywin32 (Windows-specific dependency)
    if ! $PYTHON_CMD -c "import win32gui" &> /dev/null; then
        echo "[!] pywin32 is missing. Attempting to install..."
        $PYTHON_CMD -m pip install pywin32
    fi
fi

# 4. Check if the application file exists
if [ ! -f "$APP_SCRIPT" ]; then
    echo "[!] Error: $APP_SCRIPT not found in $SCRIPT_DIR"
    exit 1
fi

# 5. Run the application
echo "[*] Launching application..."
$PYTHON_CMD "$APP_SCRIPT" "$@"

APP_EXIT_CODE=$?

# 6. Check if the application ran successfully
if [ $APP_EXIT_CODE -ne 0 ]; then
    echo ""
    echo "[!] Error: EZ-Switch exited with code $APP_EXIT_CODE."
fi

exit $APP_EXIT_CODE