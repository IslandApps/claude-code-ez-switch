#!/bin/bash

# EZ-Switch Run Script for Linux (Standalone Source)

# --- Configuration ---
APP_SCRIPT="ezswitch.py"
# ---------------------

# Get the directory where this script is located
# This ensures the script can be run from any directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting EZ-Switch application..."

# 1. Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH."
    echo "This application requires Python 3 to run."
    exit 1
fi

# 2. Check if the application file exists
if [ ! -f "$SCRIPT_DIR/$APP_SCRIPT" ]; then
    echo "Error: $APP_SCRIPT not found in the application directory."
    echo "Please ensure $APP_SCRIPT is in the same folder as this run.sh script."
    exit 1
fi

# 3. Change to the script directory to ensure relative paths work correctly inside the app
cd "$SCRIPT_DIR"

# 4. Run the application
# We use the "$@" to pass any command line arguments the user might provide
python3 "$APP_SCRIPT" "$@"

APP_EXIT_CODE=$?

# 5. Check if the application ran successfully
if [ $APP_EXIT_CODE -ne 0 ]; then
    echo ""
    echo "Error: EZ-Switch encountered an error while running (Code: $APP_EXIT_CODE)."
    echo "Please review the output above for details."
fi

exit $APP_EXIT_CODE