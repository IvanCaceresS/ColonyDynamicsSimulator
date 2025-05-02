# setup.py (Revised - DATA_FILES removed)
from setuptools import setup
import os

# --- Basic App Configuration ---
APP_NAME = "SimulationManager"
MAIN_SCRIPT = 'main.py'
VERSION = '1.0.0' # Or dynamically load from your app/version file

# --- Icon File ---
# IMPORTANT: macOS uses .icns files, not .ico.
# You MUST convert your img/icono.ico to img/icono.icns.
ICON_MAC = 'img/icono.icns'

# --- Files and Folders to Include ---
# <<< REMOVED >>> DATA_FILES variable is no longer needed here.
# These will be copied manually by the build script alongside the .app bundle.

# --- py2app Options ---
OPTIONS = {
    'argv_emulation': True, # Helps with command-line arguments for GUI apps
    'packages': [
        'pandas',
        'matplotlib',
        'customtkinter',
        'psutil',
        'dotenv',
        'openai',
        'tiktoken'
        # Add other packages py2app might miss during analysis
    ],
    'iconfile': ICON_MAC if os.path.exists(ICON_MAC) else None,
    'plist': {
        # --- Basic Info.plist settings ---
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': APP_NAME,
        'CFBundleGetInfoString': f"{APP_NAME} {VERSION}, (c) Your Name/Company",
        'CFBundleIdentifier': f"com.yourcompany.{APP_NAME.lower().replace(' ', '')}", # CHANGE THIS
        'CFBundleVersion': VERSION,
        'CFBundleShortVersionString': VERSION,
        'NSHumanReadableCopyright': '(c) Your Name/Company. All rights reserved.' # CHANGE THIS
    },
}

# --- Setup Configuration ---
setup(
    app=[MAIN_SCRIPT],          # Your main application script
    name=APP_NAME,              # App name
    version=VERSION,            # App version
    # <<< REMOVED >>> 'data_files=DATA_FILES,' argument is removed.
    options={'py2app': OPTIONS},# Pass py2app specific options
    setup_requires=['py2app'],  # Ensure py2app is available for the setup process
)

# --- Post-setup Check (Optional) ---
if not os.path.exists(ICON_MAC) and OPTIONS.get('iconfile'):
    print(f"WARNING: Icon file '{ICON_MAC}' specified but not found. Build will lack an icon.")
elif not OPTIONS.get('iconfile'):
     print(f"INFO: No icon file specified or found at '{ICON_MAC}'.")

print("-" * 40)
print("Setup configuration complete.")
print("Remember to change 'CFBundleIdentifier' and Copyright info in the plist options!")
print("-" * 40)