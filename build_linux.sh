#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "=== Cleaning previous build artifacts ==="
rm -rf dist/ build/

echo "=== Activating Virtual Environment ==="
if [ -d ".venv-linux" ]; then
    source .venv-linux/bin/activate
elif [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "[ERROR] Linux virtual environment (.venv-linux) not found!"
    exit 1
fi

read -p "Press [Enter] to start PyInstaller build..."

echo "=== Building RiceGIS with PyInstaller ==="
pyinstaller --noconfirm RiceGIS.spec

echo "=== Post-build cleanup ==="
# Linux equivalents for Qt/C++ runtime conflicts (stdc++/gcc cleanup if Qt bundles duplicate system libs)
QT_LIB_DIR="dist/RiceGIS/_internal/PyQt5/Qt5/lib"

if [ -f "$QT_LIB_DIR/libstdc++.so.6" ]; then
    rm -f "$QT_LIB_DIR/libstdc++.so.6"
    echo "[FIX] Removed bundled Qt libstdc++.so.6 to prevent system driver conflicts"
fi

if [ -f "$QT_LIB_DIR/libgcc_s.so.1" ]; then
    rm -f "$QT_LIB_DIR/libgcc_s.so.1"
    echo "[FIX] Removed bundled Qt libgcc_s.so.1 to prevent system driver conflicts"
fi

echo "=== Build Completed Successfully ==="
read -p "Press [Enter] to exit..."