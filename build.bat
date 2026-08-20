@echo off

rmdir /s dist\
rmdir /s build\

call .venv_ricegis\Scripts\activate.bat
pause
pyinstaller ^
--noconfirm ^
--console ^
--hidden-import="sklearn" ^
--hidden-import="sklearn.ensemble._forest" ^
--hidden-import="onnxruntime" ^
--icon=app_icon.ico ^
--name RiceGIS ^
--add-data "assets;assets" ^
--add-data "ui;ui" ^
--collect-all rasterio ^
--collect-all onnxruntime ^
main.py

pause