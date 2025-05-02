#!/bin/bash

# Mac_build.sh
# Builds the macOS application using py2app and copies necessary data files alongside.

# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error when substituting.
# set -u # Uncomment if you want stricter variable checks
# Prevent errors in pipelines from being masked.
set -o pipefail

# --- Configuration ---
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
echo "Script directory: $SCRIPT_DIR"

REQUIRED_PYTHON_VERSION='3.9.11'
VENV_DIR_NAME=".venv"
REQUIREMENTS_FILE="Mac_requirements.txt" # Using Mac specific requirements
SETUP_FILE="Mac_build_setup.py"                   # py2app setup file
APP_NAME="SimulationManager"            # Match the name in setup.py if needed for paths
DIST_DIR_NAME="Mac_dist"                # Final output directory name
ITEMS_TO_COPY_REL=(".env" "img" "Template") # Items relative to $SCRIPT_DIR to copy alongside .app

# --- Calculated Paths ---
VENV_DIR="$SCRIPT_DIR/$VENV_DIR_NAME"
REQUIREMENTS_PATH="$SCRIPT_DIR/$REQUIREMENTS_FILE"
SETUP_PATH="$SCRIPT_DIR/$SETUP_FILE"
PARENT_DIR=$(dirname "$SCRIPT_DIR")
FINAL_DIST_PATH="$PARENT_DIR/$DIST_DIR_NAME" # Final location for the built app bundle structure

# Define ANSI colors for output messages (Optional)
COLOR_RESET='\033[0m'
COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[0;33m'
COLOR_BLUE='\033[0;34m'
COLOR_MAGENTA='\033[0;35m'
COLOR_CYAN='\033[0;36m'

# Helper function for logging steps
log_step() {
    echo -e "\n${COLOR_MAGENTA}--- $1 ---${COLOR_RESET}"
}

# Helper function for logging success
log_success() {
    echo -e "${COLOR_GREEN}\t -> Success.${COLOR_RESET}"
}

# Helper function for logging warnings
log_warning() {
    echo -e "${COLOR_YELLOW}WARNING: $1${COLOR_RESET}"
}

# Helper function for logging errors and exiting
log_error_exit() {
    echo -e "${COLOR_RED}*** ERROR: $1 ***${COLOR_RESET}" >&2
    # Deactivate venv if active before exiting
    [[ "$VIRTUAL_ENV" != "" ]] && deactivate
    exit 1
}

echo -e "\n${COLOR_YELLOW}=== macOS Build Script (Bash) ===${COLOR_RESET}"

#region 0.5 Clean Previous Build Output (in parent directory)
log_step "0.5 Cleaning up previous build output ('$DIST_DIR_NAME' in parent dir)"
echo "Checking for existing build output at: $FINAL_DIST_PATH"
if [ -e "$FINAL_DIST_PATH" ]; then
    log_warning "Found previous build output at '$FINAL_DIST_PATH'. Attempting to remove it."
    rm -rf "$FINAL_DIST_PATH" || log_error_exit "Failed to remove previous build output at '$FINAL_DIST_PATH'. Check permissions."
    echo -e "${COLOR_GREEN}\t -> Previous build output removed successfully.${COLOR_RESET}"
else
    echo "No previous build output found at '$FINAL_DIST_PATH'."
fi
#endregion

#region 1 Clean existing virtual environment (in app directory)
log_step "1 Cleaning up existing environment (in '$SCRIPT_DIR')"
if [ -d "$VENV_DIR" ]; then
    echo "Removing existing virtual environment: $VENV_DIR"
    rm -rf "$VENV_DIR" || log_error_exit "Failed to remove existing virtual environment '$VENV_DIR'. Check permissions."
    log_success
else
    echo "No existing virtual environment found at '$VENV_DIR'."
fi
#endregion

#region 2 Verify Python Installation and Version
log_step "2 Verifying Python 3 installation and version"
if ! command -v python3 &> /dev/null; then
    log_error_exit "Python 3 is not installed or not found in PATH. Please install Python $REQUIRED_PYTHON_VERSION."
fi
PYTHON_PATH=$(command -v python3)
echo "Python 3 executable found: $PYTHON_PATH"

echo "Checking Python version..."
PYTHON_VERSION_OUTPUT=$($PYTHON_PATH --version 2>&1) || true
echo "Output from '$PYTHON_PATH --version': $PYTHON_VERSION_OUTPUT"
DETECTED_PYTHON_VERSION=$(echo "$PYTHON_VERSION_OUTPUT" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -n 1)

if [ -z "$DETECTED_PYTHON_VERSION" ]; then
    log_error_exit "Could not parse Python version number from output: '$PYTHON_VERSION_OUTPUT'. Ensure '$PYTHON_PATH --version' works correctly."
fi

echo "Detected Python version: $DETECTED_PYTHON_VERSION"
if [ "$DETECTED_PYTHON_VERSION" == "$REQUIRED_PYTHON_VERSION" ]; then
    echo -e "${COLOR_GREEN}Python version $DETECTED_PYTHON_VERSION matches required version $REQUIRED_PYTHON_VERSION.${COLOR_RESET}"
else
    log_error_exit "Incorrect Python version detected. Found '$DETECTED_PYTHON_VERSION', but require '$REQUIRED_PYTHON_VERSION'. Please install or configure PATH to use the correct version."
fi
#endregion

#region 3 Create new virtual environment
log_step "3 Creating new virtual environment"
"$PYTHON_PATH" -m venv "$VENV_DIR" || log_error_exit "Virtual environment creation in '$VENV_DIR' failed."
log_success
#endregion

#region 4 Activate virtual environment and Upgrade Pip
log_step "4 Activating virtual environment and Upgrading Pip"
source "$VENV_DIR/bin/activate" || log_error_exit "Failed to activate virtual environment."
echo "Virtual environment activated."
python -m pip install --upgrade pip || log_error_exit "Upgrade of pip failed."
log_success
#endregion

#region 5 Install Dependencies from Mac_requirements.txt
log_step "5 Installing dependencies from '$REQUIREMENTS_FILE'"
if [ -f "$REQUIREMENTS_PATH" ]; then
    pip install --no-cache-dir -r "$REQUIREMENTS_PATH" || log_error_exit "Installation of dependencies from '$REQUIREMENTS_FILE' failed."
    log_success
else
    log_warning "File '$REQUIREMENTS_FILE' not found. Skipping dependency installation."
fi
#endregion

#region 6 Verify setup.py for Build
log_step "6 Verifying setup file for build"
if [ ! -f "$SETUP_PATH" ]; then
    log_error_exit "Setup file '$SETUP_FILE' not found in '$SCRIPT_DIR'. Cannot proceed with build."
fi
 echo "Setup file found: $SETUP_PATH"
#endregion

#region 7 Build with py2app
log_step "7 Building application with py2app"
cd "$SCRIPT_DIR" || log_error_exit "Failed to change directory to $SCRIPT_DIR"
python "$SETUP_FILE" py2app || log_error_exit "py2app build failed."
PY2APP_OUTPUT_DIR="$SCRIPT_DIR/dist"
if [ ! -d "$PY2APP_OUTPUT_DIR" ]; then
    log_error_exit "py2app output directory '$PY2APP_OUTPUT_DIR' not found after build attempt."
fi
if [ ! -d "$PY2APP_OUTPUT_DIR/$APP_NAME.app" ]; then
     log_error_exit "Application bundle '$APP_NAME.app' not found inside '$PY2APP_OUTPUT_DIR'."
fi
log_success
cd - > /dev/null # Go back to previous directory (optional)
#endregion

#region 8 Cleanup Intermediate Files (build folder)
log_step "8 Cleaning up intermediate files (build folder)"
BUILD_DIR="$SCRIPT_DIR/build"
if [ -d "$BUILD_DIR" ]; then
    echo "Removing intermediate build directory: $BUILD_DIR"
    rm -rf "$BUILD_DIR" || log_warning "Could not remove intermediate build directory $BUILD_DIR."
    echo -e "${COLOR_GREEN}\t -> Intermediate build directory removed.${COLOR_RESET}"
else
     echo "Intermediate build directory '$BUILD_DIR' not found, skipping cleanup."
fi
#endregion

#region 9 Move Application Bundle to Final Destination
log_step "9 Moving '$APP_NAME.app' to final destination"
echo "Final destination directory: $FINAL_DIST_PATH"

# Create the final destination directory (e.g., Mac_dist in parent)
mkdir -p "$FINAL_DIST_PATH" || log_error_exit "Failed to create final destination directory '$FINAL_DIST_PATH'."

# Define source path for the .app bundle
APP_BUNDLE_SOURCE="$PY2APP_OUTPUT_DIR/$APP_NAME.app"

# Move the .app bundle
echo "Moving '$APP_BUNDLE_SOURCE' to '$FINAL_DIST_PATH'..."
mv "$APP_BUNDLE_SOURCE" "$FINAL_DIST_PATH/" || log_error_exit "Failed to move application bundle to '$FINAL_DIST_PATH'."
log_success

# Clean up the now empty py2app 'dist' directory inside 'app'
echo "Removing temporary py2app output directory: $PY2APP_OUTPUT_DIR"
rm -rf "$PY2APP_OUTPUT_DIR" || log_warning "Could not remove temporary py2app output directory '$PY2APP_OUTPUT_DIR'."
#endregion

#region 9.5 Copy Additional Items Alongside .app Bundle <<< ADDED REGION
log_step "9.5 Copying additional items to '$FINAL_DIST_PATH'"

for ITEM_NAME in "${ITEMS_TO_COPY_REL[@]}"; do
    SOURCE_ITEM_PATH="$SCRIPT_DIR/$ITEM_NAME"
    DESTINATION_DIR="$FINAL_DIST_PATH" # Copy directly into Mac_dist

    if [ -e "$SOURCE_ITEM_PATH" ]; then
        echo "Copying '$ITEM_NAME' to '$DESTINATION_DIR'..."
        # Use -R for directories, works for files too. Use trailing slash on destination
        # to ensure it copies *into* the directory if it exists.
        cp -R "$SOURCE_ITEM_PATH" "$DESTINATION_DIR/" || log_warning "Failed to copy '$ITEM_NAME' to '$DESTINATION_DIR'. Continuing..."
        # Check exit status of cp explicitly
        if [ $? -eq 0 ]; then
            echo -e "${COLOR_GREEN}\t -> Successfully copied '$ITEM_NAME'.${COLOR_RESET}"
        fi
    else
        log_warning "Source item '$SOURCE_ITEM_PATH' not found. Skipping copy."
    fi
done
#endregion

#region 10 Final Virtual Environment Cleanup
log_step "10 Final Virtual Environment Cleanup"
if [ -d "$VENV_DIR" ]; then
    echo "Removing virtual environment: $VENV_DIR"
    # Deactivate before removing
    [[ "$VIRTUAL_ENV" != "" ]] && deactivate
    rm -rf "$VENV_DIR" || log_warning "Could not completely remove virtual environment '$VENV_DIR'. You may need to remove it manually."
    echo -e "${COLOR_GREEN}\t -> Virtual environment removed.${COLOR_RESET}"
else
    echo "Virtual environment '$VENV_DIR' not found, skipping final cleanup."
fi
#endregion

# --- Final Success Message ---
echo -e "\n${COLOR_YELLOW}=== Script finished successfully! ===${COLOR_RESET}"
echo -e "${COLOR_GREEN}The final '$DIST_DIR_NAME' folder containing '$APP_NAME.app' and data files is located at: $FINAL_DIST_PATH${COLOR_RESET}"

exit 0