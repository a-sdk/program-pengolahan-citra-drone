@echo off

rmdir /s dist\
rmdir /s build\

call .venv\Scripts\activate.bat
pause
pyinstaller ^
--noconfirm ^
RiceGIS.spec

:: Force remove PyQt5's conflicting C++ runtime DLLs
if exist "dist\RiceGIS\_internal\PyQt5\Qt5\bin\MSVCP140.dll" (
    del /f /q "dist\RiceGIS\_internal\PyQt5\Qt5\bin\MSVCP140.dll"
    echo [FIX] Removed conflicting PyQt5 MSVCP140.dll
)
if exist "dist\RiceGIS\_internal\PyQt5\Qt5\bin\VCRUNTIME140.dll" (
    del /f /q "dist\RiceGIS\_internal\PyQt5\Qt5\bin\VCRUNTIME140.dll"
    echo [FIX] Removed conflicting PyQt5 VCRUNTIME140.dll
)

pause