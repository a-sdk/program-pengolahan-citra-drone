# -*- mode: python ; coding: utf-8 -*-
# RiceGIS.spec
import sys
import os
from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs, collect_data_files

block_cipher = None

# Collect rasterio, pyproj, and geopandas assets
rasterio_datas, rasterio_binaries, rasterio_hiddenimports = collect_all('rasterio')
pyproj_datas, pyproj_binaries, pyproj_hiddenimports = collect_all('pyproj')

# Collect ONNX Runtime dependencies
onnx_binaries = collect_dynamic_libs('onnxruntime')
onnx_datas = collect_data_files('onnxruntime')

# Combine datas and binaries
datas = [('assets', 'assets'), ('ui', 'ui')] + rasterio_datas + pyproj_datas + onnx_datas
binaries = rasterio_binaries + pyproj_binaries + onnx_binaries

# Filter binaries selectively based on OS
filtered_binaries = []
for item in binaries:
    src = item[0] if isinstance(item[0], str) else item[1]
    src_upper = src.upper()
    
    # Windows-specific DLL filter
    if sys.platform.startswith('win'):
        if 'PYQT5' in src_upper and ('MSVCP140' in src_upper or 'VCRUNTIME140' in src_upper):
            continue  # Skip bundled PyQt5 C++ runtimes on Windows
            
    filtered_binaries.append(item)

hiddenimports = [
    'sklearn',
    'sklearn.ensemble._forest',
    'onnxruntime',
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtWidgets',
    'PyQt5.sip',
    'shapely',
    'geopandas',
] + rasterio_hiddenimports + pyproj_hiddenimports

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=filtered_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib.tests', 'scipy.spatial.tests'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Cross-platform Icon handling
icon_file = 'app_icon.ico' if sys.platform.startswith('win') else None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RiceGIS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='RiceGIS',
)