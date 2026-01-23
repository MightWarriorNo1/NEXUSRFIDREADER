# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(SPEC))

# Define data files to include
datas = [
    # Include font files
    (os.path.join(current_dir, 'font', '*'), 'font'),
    # Include UI images
    (os.path.join(current_dir, 'ui', 'img', '*'), 'ui/img'),
    # Include compiled UI files
    (os.path.join(current_dir, 'ui', 'pl_rc.py'), '.'),
    # Include screens UI files
    (os.path.join(current_dir, 'ui', 'screens', '*.py'), 'ui/screens'),
]

# Define hidden imports for PySide6 and other modules
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui', 
    'PySide6.QtWidgets',
    'PySide6.QtNetwork',
    'PySide6.QtSerialPort',
    'sllurp',
    'pynmea2',
    'geopy',
    'geographiclib',
    'schedule',
    'ping3',
    'numpy',
    'serial',
    'requests',
    'urllib3',
    'sqlite3',
    'threading',
    'time',
    'json',
    'platform',
    'subprocess',
    'glob',
    'signal',
    'traceback',
    'functools',
    'os',
    'sys',
    'pathlib',
]

a = Analysis(
    ['main.py'],
    pathex=[current_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='NexusRFIDReader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(current_dir, 'ui', 'img', 'icon.ico'),
)