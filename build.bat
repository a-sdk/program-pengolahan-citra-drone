@echo off

rmdir /s dist\
rmdir /s build\

call .venv_stable\Scripts\activate.bat
pause
pyinstaller ^
--noconfirm ^
--console ^
--hidden-import="sklearn" ^
--hidden-import="sklearn.ensemble._forest" ^
--icon=app_icon.ico ^
--name mYApp ^
--add-data "assets;assets" ^
--add-data "ui;ui" ^
--collect-all tensorflow ^
--collect-all rasterio ^
main.py

pause