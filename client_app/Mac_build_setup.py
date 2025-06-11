
from setuptools import setup
import os
import sys
import site
import shutil 

APP_NAME = "ColonyDynamicsSimulator"
MAIN_SCRIPT = 'Mac_main.py'
VERSION = '1.0.0'
ICON_MAC = 'img/icon.icns'

OPTIONS = {
    'argv_emulation': True,
    'packages': [
        'pandas',
        'matplotlib',
        'customtkinter',
        'psutil',
        'dotenv',
        'aiohttp',
        'frozenlist',
        'requests',
        'chardet',
        'PIL'
    ],
    'includes': [
        'scipy.optimize',
        'scipy.linalg',
        'sklearn.metrics',
        'sklearn.utils._typedefs',
        'sklearn.utils._heap',
        'sklearn.utils._sorting',
        'sklearn.utils._vector_sentinel',
        'numpy',
        'matplotlib.backends.backend_tkagg',
    ],
    'iconfile': ICON_MAC if os.path.exists(ICON_MAC) else None,
    'plist': {
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': APP_NAME,
        'CFBundleGetInfoString': f"{APP_NAME} {VERSION}, (c) Your Name/Company",
        'CFBundleIdentifier': f"com.yourcompany.{APP_NAME.lower().replace(' ', '')}",
        'CFBundleVersion': VERSION,
        'CFBundleShortVersionString': VERSION,
        'NSHumanReadableCopyright': '(c) Your Name/Company. All rights reserved.'
    }
}

setup(
    app=[MAIN_SCRIPT],
    name=APP_NAME,
    version=VERSION,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

if not os.path.exists(ICON_MAC) and OPTIONS.get('iconfile'):
    print(f"WARNING: Icon file '{ICON_MAC}' specified but not found. Build will lack an icon.")
elif not OPTIONS.get('iconfile'):
     print(f"INFO: No icon file specified or found at '{ICON_MAC}'.")

print("-" * 40)
print("Setup configuration complete.")
print("-" * 40)