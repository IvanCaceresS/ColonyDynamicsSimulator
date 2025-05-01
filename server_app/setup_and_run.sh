#!/bin/bash

# --- Script Configuration ---
VENV_DIR=".venv"
REQUIREMENTS_FILE="./requirements.txt"
API_SCRIPT="./api.py"

# --- Function to handle errors and exit ---
handle_error() {
    echo "Error on line $1: $2"
    exit 1
}

# Trap errors and call the handler
trap 'handle_error ${LINENO} "${BASH_COMMAND}"' ERR

echo "Starting setup and execution script..."

# --- 1. Check for Python3 ---
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed or not found in PATH."
    echo "Please install Python3 and ensure it's accessible from your terminal."
    exit 1
fi
echo "Python3 found."

# --- 2. Create Virtual Environment ---
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment '$VENV_DIR' already exists. Skipping creation."
else
    echo "Creating virtual environment '$VENV_DIR'..."
    python3 -m venv "$VENV_DIR"
    echo "Virtual environment created."
fi

# --- 3. Determine Activation Script Path based on OS ---
VENV_ACTIVATE=""
case "$OSTYPE" in
    linux*)
        # Linux (Ubuntu, WSL)
        VENV_ACTIVATE="$VENV_DIR/bin/activate"
        ;;
    msys*|mingw*)
        # Windows (Git Bash)
        VENV_ACTIVATE="$VENV_DIR/Scripts/activate"
        ;;
    *)
        echo "Warning: Unknown OS type '$OSTYPE'. Assuming Linux-like activation path."
        VENV_ACTIVATE="$VENV_DIR/bin/activate"
        ;;
esac

# Check if the determined activation script exists
if [ ! -f "$VENV_ACTIVATE" ]; then
    echo "Error: Could not find virtual environment activation script at '$VENV_ACTIVATE'."
    echo "Please check the '$VENV_DIR' directory structure."
    exit 1
fi
echo "Activation script found at '$VENV_ACTIVATE'."


# --- 4. Activate Virtual Environment ---
echo "Activating virtual environment..."
source "$VENV_ACTIVATE"
echo "Virtual environment activated."
echo "Using Python3 from: $(command -v python3)"

# --- 5. Install Requirements ---
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing dependencies from '$REQUIREMENTS_FILE'..."
    pip install -r "$REQUIREMENTS_FILE"
    echo "Dependencies installed."
else
    echo "Warning: '$REQUIREMENTS_FILE' not found. Skipping dependency installation."
fi

# --- 6. Execute API Script ---
if [ -f "$API_SCRIPT" ]; then
    echo "Executing script '$API_SCRIPT'..."
    python3 "$API_SCRIPT"
    echo "Script execution finished."
else
    echo "Error: API script '$API_SCRIPT' not found."
    exit 1
fi

echo "Script finished successfully."