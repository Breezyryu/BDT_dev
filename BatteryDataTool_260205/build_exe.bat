@echo off
setlocal
echo Building BatteryDataTool.exe with Icon...

cd /d "%~dp0"

set "VENV_EXE=%~dp0.venv\Scripts\pyinstaller.exe"
set "SCRIPT_PATH=%~dp0BatteryDataTool.py"
set "ICON_PATH=%~dp0BatteryDataTool.ico"

"%VENV_EXE%" ^
    --onefile ^
    --noconsole ^
    --noconfirm ^
    --uac-admin ^
    --hidden-import fsspec ^
    %ICON_CMD% ^
    "%SCRIPT_PATH%" ^
    --distpath "."

pause