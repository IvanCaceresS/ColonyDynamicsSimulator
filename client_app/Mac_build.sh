#!/bin/bash
# Script to build macOS application bundle
# --- Ensure script is run as root ---
if [ "$(id -u)" -ne 0 ]; then
  echo -e "\033[0;31m*** ERROR: This script must be run as root. Please use sudo. ***\033[0m" >&2
  exit 1
fi
set -e
set -o pipefail
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
echo "Script directory: $SCRIPT_DIR"
REQUIRED_PYTHON_VERSION='3.9.11'
VENV_DIR_NAME=".venv"
REQUIREMENTS_FILE="Mac_requirements.txt" # Using Mac specific requirements
SETUP_FILE="Mac_build_setup.py"          # py2app setup file
APP_NAME="SimulationManager"             # Match the name in setup.py if needed for paths
DIST_DIR_NAME="Mac_dist"                 # Final output directory name
ITEMS_TO_COPY_REL=(".env" "img" "Template") # Items relative to $SCRIPT_DIR to copy alongside .app
# --- Calculated Paths ---
VENV_DIR="$SCRIPT_DIR/$VENV_DIR_NAME"
REQUIREMENTS_PATH="$SCRIPT_DIR/$REQUIREMENTS_FILE"
SETUP_PATH="$SCRIPT_DIR/$SETUP_FILE"
PARENT_DIR=$(dirname "$SCRIPT_DIR")
FINAL_DIST_PATH="$PARENT_DIR/$DIST_DIR_NAME" # Final location for the built app bundle structure
# Define ANSI colors for output messages
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
echo -e "\n${COLOR_YELLOW}=== macOS Build Script (Bash) - Running as root ===${COLOR_RESET}"
#region 0.5 Clean Previous Build Output (in parent directory)
log_step "0.5 Cleaning up previous build output ('$DIST_DIR_NAME' in parent dir)"
echo "Checking for existing build output at: $FINAL_DIST_PATH"
if [ -e "$FINAL_DIST_PATH" ]; then
    log_warning "Found previous build output at '$FINAL_DIST_PATH'. Attempting to remove it."
    # Since we are root, rm -rf should have fewer permission issues
    rm -rf "$FINAL_DIST_PATH" || log_error_exit "Failed to remove previous build output at '$FINAL_DIST_PATH'."
    echo -e "${COLOR_GREEN}\t -> Previous build output removed successfully.${COLOR_RESET}"
else
    echo "No previous build output found at '$FINAL_DIST_PATH'."
fi
#endregion
#region 1 Clean existing virtual environment (in app directory)
log_step "1 Cleaning up existing environment (in '$SCRIPT_DIR')"
if [ -d "$VENV_DIR" ]; then
    echo "Removing existing virtual environment: $VENV_DIR"
    rm -rf "$VENV_DIR" || log_error_exit "Failed to remove existing virtual environment '$VENV_DIR'."
    log_success
else
    echo "No existing virtual environment found at '$VENV_DIR'."
fi
#endregion
#region 2 Verify Python Installation and Version
log_step "2 Verifying Python 3 installation and version (Target: $REQUIRED_PYTHON_VERSION)"
PYTHON_PATH="" # Will store the path to the validated Python executable
# Function to check a Python executable and its version
# Sets PYTHON_PATH (globally in this script context) if a valid executable is found and version matches
# Returns 0 on success, 1 on failure (not found or version mismatch)
find_and_validate_python() {
    local executable_name="$1"
    local found_exe_path
    
    if ! command -v "$executable_name" &> /dev/null; then
        echo "Executable '$executable_name' not found in PATH."
        return 1
    fi
    
    found_exe_path=$(command -v "$executable_name")
    echo "Found '$executable_name' at: $found_exe_path"
    
    echo "Checking version of '$found_exe_path'..."
    # Capture stderr to stdout for version check, handle potential errors
    local version_output
    version_output=$("$found_exe_path" --version 2>&1)
    local version_check_status=$?
    if [ $version_check_status -ne 0 ]; then
        log_warning "Command '$found_exe_path --version' failed or produced an error. Output: $version_output"
        return 1
    fi
    echo "Output from '$found_exe_path --version': $version_output"
    local detected_version
    # Regex to find version like X.Y.Z. Handles "Python 3.9.11" or just "3.9.11"
    detected_version=$(echo "$version_output" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -n 1)
    
    if [ -z "$detected_version" ]; then
        log_warning "Could not parse Python version from output: '$version_output' for '$found_exe_path'."
        return 1
    fi
    
    echo "Detected Python version for '$found_exe_path': $detected_version"
    if [ "$detected_version" == "$REQUIRED_PYTHON_VERSION" ]; then
        echo -e "${COLOR_GREEN}Python version $detected_version matches required $REQUIRED_PYTHON_VERSION.${COLOR_RESET}"
        PYTHON_PATH="$found_exe_path" # Set the global PYTHON_PATH for the script
        return 0 # Success
    else
        log_warning "Incorrect Python version for '$found_exe_path'. Found '$detected_version', but require '$REQUIRED_PYTHON_VERSION'."
        return 1 # Version mismatch
    fi
}
# Attempt to find a suitable Python version from common names
# Prioritize more specific names (e.g., python3.9) if they exist and match
echo "Searching for a suitable Python installation..."
# Construct specific pythonX.Y name, e.g., python3.9 from 3.9.11
SPECIFIC_PYTHON_CMD="python${REQUIRED_PYTHON_VERSION%.*}" 
if find_and_validate_python "$SPECIFIC_PYTHON_CMD"; then
    log_success "Using '$SPECIFIC_PYTHON_CMD' found in PATH."
elif find_and_validate_python "python3"; then # Fallback to generic python3
    log_success "Using 'python3' found in PATH."
else
    log_warning "No suitable Python version ($REQUIRED_PYTHON_VERSION) found in PATH."
    
    # Attempt to install Python if not found or version is incorrect
    echo "Attempting to download and install Python $REQUIRED_PYTHON_VERSION..."
    
    # Construct download URL and filename based on REQUIRED_PYTHON_VERSION
    # This example targets a specific macOS installer (macos11 for Intel/Universal2)
    # Adjust if a different package is needed (e.g., for older macOS or specific architecture)
    PYTHON_INSTALL_PKG_URL="https://www.python.org/ftp/python/$REQUIRED_PYTHON_VERSION/python-$REQUIRED_PYTHON_VERSION-macos11.pkg"
    PYTHON_PKG_FILENAME="python-$REQUIRED_PYTHON_VERSION-macos11.pkg"
    TEMP_INSTALL_PKG_PATH="/tmp/$PYTHON_PKG_FILENAME"
    echo "Downloading Python $REQUIRED_PYTHON_VERSION installer from $PYTHON_INSTALL_PKG_URL..."
    if curl -# -L "$PYTHON_INSTALL_PKG_URL" -o "$TEMP_INSTALL_PKG_PATH"; then
        echo "Download successful: $TEMP_INSTALL_PKG_PATH"
        echo -e "${COLOR_YELLOW}Python installation requires administrator privileges. Already running as root.${COLOR_RESET}"
        
        # No need for sudo here as script is already root
        if installer -pkg "$TEMP_INSTALL_PKG_PATH" -target /; then
            echo -e "${COLOR_GREEN}Python $REQUIRED_PYTHON_VERSION installation command executed successfully.${COLOR_RESET}"
            rm "$TEMP_INSTALL_PKG_PATH" # Clean up downloaded package
            # After installation, try to find the installed Python.
            # Common paths for python.org installers:
            # /Library/Frameworks/Python.framework/Versions/X.Y/bin/pythonX.Y
            # /usr/local/bin/pythonX.Y (symlink)
            # We will re-run find_and_validate_python with the specific version name.
            echo "Verifying Python installation..."
            if find_and_validate_python "$SPECIFIC_PYTHON_CMD"; then
                 log_success "Successfully verified installed Python (as '$SPECIFIC_PYTHON_CMD')."
            elif find_and_validate_python "python3"; then # Fallback to generic python3
                 log_success "Successfully verified installed Python (as 'python3')."
            else
                 # Provide more specific paths to check if auto-detection fails
                 FRAMEWORK_PYTHON_PATH="/Library/Frameworks/Python.framework/Versions/${REQUIRED_PYTHON_VERSION%.*}/bin/$SPECIFIC_PYTHON_CMD"
                 USR_LOCAL_BIN_PYTHON_PATH="/usr/local/bin/$SPECIFIC_PYTHON_CMD"
                 log_error_exit "Python $REQUIRED_PYTHON_VERSION installation seemed to succeed, but could not find or validate the correct version afterwards.
Please check your installation or install manually.
Expected paths might include:
$FRAMEWORK_PYTHON_PATH
$USR_LOCAL_BIN_PYTHON_PATH
Ensure the correct Python is in your PATH."
            fi
        else
            rm -f "$TEMP_INSTALL_PKG_PATH" # Clean up even on failure
            log_error_exit "Python $REQUIRED_PYTHON_VERSION installation failed (installer command). Please install manually from python.org."
        fi
    else
        log_error_exit "Failed to download Python $REQUIRED_PYTHON_VERSION installer from $PYTHON_INSTALL_PKG_URL. Check network or URL."
    fi
fi
# Final check: If PYTHON_PATH is still not set, something went wrong.
if [ -z "$PYTHON_PATH" ]; then
    log_error_exit "Failed to find or install a working Python $REQUIRED_PYTHON_VERSION. Aborting."
fi
echo "Using Python executable: $PYTHON_PATH"
#endregion
#region 3 Create new virtual environment
log_step "3 Creating new virtual environment"
"$PYTHON_PATH" -m venv "$VENV_DIR" || log_error_exit "Virtual environment creation in '$VENV_DIR' failed using '$PYTHON_PATH'."
log_success
#endregion
#region 4 Activate virtual environment and Upgrade Pip
log_step "4 Activating virtual environment and Upgrading Pip"
source "$VENV_DIR/bin/activate" || log_error_exit "Failed to activate virtual environment."
echo "Virtual environment activated."
# Use python from venv to ensure pip is upgraded for the correct environment
python -m pip install --upgrade pip || log_error_exit "Upgrade of pip failed."
log_success
#endregion
#region 5 Install Dependencies from Mac_requirements.txt
log_step "5 Installing dependencies from '$REQUIREMENTS_FILE'"
if [ -f "$REQUIREMENTS_PATH" ]; then
    # Use python from venv (which implies pip from venv)
    python -m pip install --no-cache-dir -r "$REQUIREMENTS_PATH" || log_error_exit "Installation of dependencies from '$REQUIREMENTS_FILE' failed."
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
# Use python from venv
python "$SETUP_FILE" py2app || log_error_exit "py2app build failed."
PY2APP_OUTPUT_DIR="$SCRIPT_DIR/dist" # Default py2app output
if [ ! -d "$PY2APP_OUTPUT_DIR" ]; then
    log_error_exit "py2app output directory '$PY2APP_OUTPUT_DIR' not found after build attempt."
fi
if [ ! -d "$PY2APP_OUTPUT_DIR/$APP_NAME.app" ]; then
     log_error_exit "Application bundle '$APP_NAME.app' not found inside '$PY2APP_OUTPUT_DIR'."
fi
log_success
cd - > /dev/null # Return to previous directory
#endregion
#region 8 Cleanup Intermediate Files (build folder)
log_step "8 Cleaning up intermediate files (build folder)"
BUILD_DIR="$SCRIPT_DIR/build" # Default py2app intermediate build folder
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
# Clean up the now empty py2app 'dist' directory inside SCRIPT_DIR
echo "Removing temporary py2app output directory: $PY2APP_OUTPUT_DIR"
rm -rf "$PY2APP_OUTPUT_DIR" || log_warning "Could not remove temporary py2app output directory '$PY2APP_OUTPUT_DIR'."
#endregion
#region 9.5 Copy Additional Items Alongside .app Bundle
log_step "9.5 Copying additional items to '$FINAL_DIST_PATH'"
for ITEM_NAME in "${ITEMS_TO_COPY_REL[@]}"; do
    SOURCE_ITEM_PATH="$SCRIPT_DIR/$ITEM_NAME"
    DESTINATION_DIR="$FINAL_DIST_PATH" # Copy directly into Mac_dist
    if [ -e "$SOURCE_ITEM_PATH" ]; then
        echo "Copying '$ITEM_NAME' to '$DESTINATION_DIR'..."
        # Use -R for directories, works for files too. Use trailing slash on destination
        # to ensure it copies *into* the directory if it exists.
        cp -R "$SOURCE_ITEM_PATH" "$DESTINATION_DIR/"
        # Check exit status of cp explicitly
        if [ $? -eq 0 ]; then
            echo -e "${COLOR_GREEN}\t -> Successfully copied '$ITEM_NAME'.${COLOR_RESET}"
        else
            # Changed to log_error_exit as these items might be critical
            log_error_exit "Failed to copy '$ITEM_NAME' from '$SOURCE_ITEM_PATH' to '$DESTINATION_DIR'."
        fi
    else
        log_warning "Source item '$SOURCE_ITEM_PATH' not found. Skipping copy."
    fi
done
#endregion
#region 9.6 Create and Setup Relative Alias Launcher
log_step "9.6 Creating and setting up relative Alias launcher"
ALIAS_NAME="${APP_NAME}Launcher" # Launcher name based on APP_NAME
# Path to the actual executable inside the .app bundle
TARGET_BINARY_PATH="$FINAL_DIST_PATH/$APP_NAME.app/Contents/MacOS/$APP_NAME"
ALIAS_DEST_PATH="$FINAL_DIST_PATH" # Create alias in the same directory as .app
if [ -f "$TARGET_BINARY_PATH" ]; then
    echo "Target binary found: $TARGET_BINARY_PATH"
    echo "Creating Alias named '$ALIAS_NAME' in '$ALIAS_DEST_PATH'..."
    # AppleScript to create the alias
    # Using POSIX file for paths is generally more robust
    osascript_command="tell application \"Finder\"
        set targetFile to POSIX file \"$TARGET_BINARY_PATH\"
        set destinationFolder to POSIX file \"$ALIAS_DEST_PATH\"
        set newAlias to make new alias file to targetFile at destinationFolder with properties {name:\"$ALIAS_NAME\"}
    end tell"
    
    # Execute AppleScript
    if osascript -e "$osascript_command"; then
        # Verify alias creation. Note: osascript might return success even if Finder has an issue.
        if [ -e "$ALIAS_DEST_PATH/$ALIAS_NAME" ]; then
            log_success "Alias '$ALIAS_NAME' created successfully in '$ALIAS_DEST_PATH'."
        else
            # Finder might take a moment, or use a slightly different name if there's a conflict.
            # This check is a best effort.
            log_warning "osascript command succeeded, but direct verification of Alias '$ALIAS_DEST_PATH/$ALIAS_NAME' failed. Please check '$ALIAS_DEST_PATH'."
        fi
    else
        log_warning "osascript command to create Alias failed. The Alias might not have been created. Target: '$TARGET_BINARY_PATH'"
    fi
else
    log_warning "Target binary '$TARGET_BINARY_PATH' not found. Skipping Alias creation."
fi
#endregion
#region 10 Final Virtual Environment Cleanup
log_step "10 Final Virtual Environment Cleanup"
if [ -d "$VENV_DIR" ]; then
    echo "Removing virtual environment: $VENV_DIR"
    # Deactivate if script is sourced and venv is active in current shell
    # For script execution, VIRTUAL_ENV might not be set if subshell for activate failed.
    if [[ -n "$VIRTUAL_ENV" && "$VIRTUAL_ENV" == "$VENV_DIR" ]]; then
        type deactivate &>/dev/null && deactivate
        echo "Virtual environment deactivated."
    fi
    rm -rf "$VENV_DIR" || log_warning "Could not completely remove virtual environment '$VENV_DIR'. You may need to remove it manually."
    echo -e "${COLOR_GREEN}\t -> Virtual environment removed.${COLOR_RESET}"
else
    echo "Virtual environment '$VENV_DIR' not found, skipping final cleanup."
fi
#endregion
#region 11 Set Final Permissions for Distribution Directory
log_step "11 Setting Final Permissions for '$DIST_DIR_NAME'"
if [ -d "$FINAL_DIST_PATH" ]; then
    echo "Setting permissions to 777 recursively for: $FINAL_DIST_PATH"
    chmod -R 777 "$FINAL_DIST_PATH" || log_warning "Failed to set permissions for '$FINAL_DIST_PATH'. Please check manually."
    log_success "Permissions for '$FINAL_DIST_PATH' set to 777."
else
    log_warning "Final distribution directory '$FINAL_DIST_PATH' not found. Skipping permission setting."
fi
#endregion
# --- Final Success Message ---
echo -e "\n${COLOR_YELLOW}=== Script finished successfully! ===${COLOR_RESET}"
echo -e "${COLOR_GREEN}The final '$DIST_DIR_NAME' folder containing '$APP_NAME.app', data files, and launcher is located at: $FINAL_DIST_PATH${COLOR_RESET}"
echo -e "${COLOR_GREEN}Permissions for '$FINAL_DIST_PATH' have been set to 777 recursively.${COLOR_RESET}"
exit 0