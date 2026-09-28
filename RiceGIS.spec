# -*- mode: python ; coding: utf-8 -*-
# RiceGIS.spec
import sys
from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs, collect_data_files

block_cipher = None

# Collect rasterio assets and binaries (replaces --collect-all rasterio)
rasterio_datas, rasterio_binaries, rasterio_hiddenimports = collect_all('rasterio')

# Collect ONNX Runtime dependencies selectively
onnx_binaries = collect_dynamic_libs('onnxruntime')
onnx_datas = collect_data_files('onnxruntime')

# Combine all datas and binaries
datas = [('assets', 'assets'), ('ui', 'ui')] + rasterio_datas + onnx_datas
binaries = rasterio_binaries + onnx_binaries

# FILTER OUT PyQt5's isolated C++ runtime binaries (safely handles 2-element tuples)
filtered_binaries = []
for item in binaries:
    # Safely extract source path regardless of tuple length
    src = item[0] if isinstance(item[0], str) else item[1]
    
    # Check if the binary is PyQt5's bundled MSVCP140 or VCRUNTIME140
    src_upper = src.upper()
    if 'PYQT5' in src_upper and ('MSVCP140' in src_upper or 'VCRUNTIME140' in src_upper):
        continue  # Skip bundled PyQt5 C++ runtimes
    
    filtered_binaries.append(item)

hiddenimports = [
    'sklearn',
    'sklearn.ensemble._forest',
    'onnxruntime',
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtWidgets',
] + rasterio_hiddenimports

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=filtered_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    icon=['app_icon.ico'],
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