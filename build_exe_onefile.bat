@echo off
setlocal
echo Building DataTool.exe with Icon...

cd /d "%~dp0"

set "VENV_EXE=%~dp0.venv\Scripts\pyinstaller.exe"
set "SCRIPT_PATH=%~dp0DataTool.py"
set "ICON_PATH=%~dp0DataTool.ico"

"%VENV_EXE%" ^
    --onefile ^
    --noconsole ^
    --noconfirm ^
    --uac-admin ^
    --hidden-import fsspec ^
    --hidden-import pybamm ^
    --hidden-import casadi ^
    --collect-all pybamm ^
    --collect-all casadi ^
    --icon="%ICON_PATH%" ^
    "%SCRIPT_PATH%" ^
    --distpath "."

pause