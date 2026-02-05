@echo off
setlocal
echo Converting UI file...

cd /d "%~dp0"

set "VENV_EXE=%~dp0.venv\Scripts\pyuic6.exe"
set "UI_FILE=%~dp0BatteryDataTool_UI.ui"
set "OUTPUT_FILE=%~dp0BatteryDataTool_UI.py"

"%VENV_EXE%" -x "%UI_FILE%" -o "%OUTPUT_FILE%"

echo UI conversion complete.
pause

