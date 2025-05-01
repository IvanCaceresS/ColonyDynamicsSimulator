#!/bin/bash
set -e

# --- Configuration ---
VENV_DIR=".venv"
REQUIREMENTS_FILE="./requirements.txt"
MAIN_SCRIPT="./main.py"
BUILD_NAME="SimulationManager"
ICON_WIN="img/icono.ico"
ICON_MAC="img/icono.icns"
ITEMS_TO_COPY=("./.env" "./img" "./Template")
BUILD_DIST_DIR="./dist"
BUILD_DIR="./build"
SPEC_FILE="./${BUILD_NAME}.spec"

echo "Starting configuration, build, and copy script..."

# --- 1. Remove existing virtual environment if it exists ---
if [ -d "$VENV_DIR" ]; then
    echo "Removing existing virtual environment '$VENV_DIR'..."
    rm -rf "$VENV_DIR"
    echo "Virtual environment removed."
fi

# --- 2. Check if Python is available ---
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not found in PATH."
    echo "Please install Python (ideally 3.x) and ensure it's accessible from your terminal."
    exit 1
fi
echo "Python found."

# --- 3. Create new virtual environment ---
echo "Creating new virtual environment '$VENV_DIR'..."
python -m venv "$VENV_DIR"
echo "Virtual environment created."

# --- 4. Determine and Activate Virtual Environment ---
VENV_ACTIVATE=""
case "$OSTYPE" in
    linux*|darwin*)
        VENV_ACTIVATE="$VENV_DIR/bin/activate"
        ;;
    msys*|mingw*)
        VENV_ACTIVATE="$VENV_DIR/Scripts/activate"
        ;;
    *)
        echo "Warning: Unknown OS type '$OSTYPE'. Assuming Linux/macOS activation path."
        VENV_ACTIVATE="$VENV_DIR/bin/activate"
        ;;
esac

if [ ! -f "$VENV_ACTIVATE" ]; then
    echo "Error: Virtual environment activation script not found at '$VENV_ACTIVATE'."
    echo "Please check the directory structure of '$VENV_DIR'."
    exit 1
fi

echo "Activating virtual environment..."
source "$VENV_ACTIVATE"
echo "Virtual environment activated. Using Python from: $(command -v python)"


# --- 5. Upgrade pip and install PyInstaller and dependencies ---
echo "Upgrading pip, setuptools, wheel and installing PyInstaller..."
python -m pip install --upgrade pip setuptools wheel
pip install pyinstaller

if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing additional dependencies from '$REQUIREMENTS_FILE'..."
    pip install --no-cache-dir -r "$REQUIREMENTS_FILE"
    echo "Dependencies installed."
else
    echo "Warning: '$REQUIREMENTS_FILE' not found, skipping additional dependency installation."
fi

# --- 6. Check if the main script for the build exists ---
if [ ! -f "$MAIN_SCRIPT" ]; then
    echo "Error: The main script '$MAIN_SCRIPT' for PyInstaller was not found."
    echo "Ensure your main file is named '$MAIN_SCRIPT' and is in the project root."
    exit 1
fi
echo "Main script '$MAIN_SCRIPT' found."

# --- 7. Determine icon and build with PyInstaller ---
echo "Preparing and running PyInstaller build..."

ICON_TO_USE=""
PYINSTALLER_CMD="pyinstaller --onefile --windowed --name \"$BUILD_NAME\""

case "$OSTYPE" in
    darwin*)
        if [ -f "$ICON_MAC" ]; then
            ICON_TO_USE="$ICON_MAC"
            PYINSTALLER_CMD="$PYINSTALLER_CMD --icon=\"$ICON_TO_USE\""
            echo "Using macOS icon: '$ICON_TO_USE'"
        else
            echo "Warning: macOS icon '$ICON_MAC' not found. Build will continue without an icon."
        fi
        ;;
    linux*|msys*|mingw*)
        if [ -f "$ICON_WIN" ]; then
            ICON_TO_USE="$ICON_WIN"
            PYINSTALLER_CMD="$PYINSTALLER_CMD --icon=\"$ICON_TO_USE\""
            echo "Using Windows/Linux icon: '$ICON_TO_USE'"
        else
            echo "Warning: Windows/Linux icon '$ICON_WIN' not found. Build will continue without an icon."
        fi
        ;;
    *)
        echo "Warning: Unknown OS type '$OSTYPE'. No icon will be used."
        ;;
esac

PYINSTALLER_CMD="$PYINSTALLER_CMD \"$MAIN_SCRIPT\""

echo "Executing PyInstaller command: $PYINSTALLER_CMD"
eval $PYINSTALLER_CMD

echo "PyInstaller build finished."

# --- 8. Copy additional items (files/directories) to the dist folder ---
echo "Copying necessary items to '$BUILD_DIST_DIR'..."

if [ ! -d "$BUILD_DIST_DIR" ]; then
    echo "Error: PyInstaller output directory '$BUILD_DIST_DIR' was not found after the build."
    echo "The PyInstaller build might have failed. Review the previous messages."
    exit 1
fi

# Iterate over the list of items to copy
for item in "${ITEMS_TO_COPY[@]}"; do
    # Check if the source item (file or directory) exists
    if [ -e "$item" ]; then
        echo "Copying '$item' to '$BUILD_DIST_DIR/'..."
        # 'cp -r' works for files and directories.
        # The trailing '/' in the destination ensures the source item is copied INSIDE dist.
        cp -r "$item" "$BUILD_DIST_DIR/"
        echo "Copy successful."
    else
        echo "Warning: Source item '$item' not found. Skipping copy."
    fi
done

echo "Item copying finished."

# --- 9. Clean up temporary PyInstaller files and directories ---
echo "Starting cleanup of temporary PyInstaller files and directories..."

if [ -d "$BUILD_DIR" ]; then
    echo "Removing directory '$BUILD_DIR'..."
    rm -rf "$BUILD_DIR"
    echo "'$BUILD_DIR' removed."
else
    echo "Directory '$BUILD_DIR' not found, skipping removal."
fi

if [ -f "$SPEC_FILE" ]; then
    echo "Removing file '$SPEC_FILE'..."
    rm "$SPEC_FILE"
    echo "'$SPEC_FILE' removed."
else
    echo "File '$SPEC_FILE' not found, skipping removal."
fi

echo "Cleanup finished."

# --- Finalization ---
echo ""
echo "------------------------------------------------------------------"
echo "Script completed successfully."
echo "The executable '$BUILD_NAME' and copied items are located in the '$BUILD_DIST_DIR' folder."
echo "Temporary build files ('$BUILD_DIR' and '$SPEC_FILE') have been removed."
echo "------------------------------------------------------------------"