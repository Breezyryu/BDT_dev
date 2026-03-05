@echo off
setlocal
echo Building BatteryDataTool (onedir)...

cd /d "%~dp0"

set "VENV_EXE=%~dp0.venv\Scripts\pyinstaller.exe"
set "SCRIPT_PATH=%~dp0BatteryDataTool.py"
set "ICON_PATH=%~dp0BatteryDataTool.ico"
"%VENV_EXE%" ^
    --onedir ^
    --noconsole ^
    --noconfirm ^
    --collect-all pybamm ^
    --collect-all casadi ^
    --collect-all pybammsolvers ^
    --hidden-import fsspec ^
    --hidden-import anytree ^
    --hidden-import pooch ^
    --hidden-import posthog ^
    --hidden-import xarray ^
    --hidden-import platformdirs ^
    --icon="%ICON_PATH%" ^
    "%SCRIPT_PATH%" ^
    --distpath "."

pause