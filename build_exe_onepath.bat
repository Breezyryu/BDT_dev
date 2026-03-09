@echo off
setlocal
echo Building DataTool (onedir)...

cd /d "%~dp0"

set "VENV_EXE=%~dp0.venv\Scripts\pyinstaller.exe"
set "SCRIPT_PATH=%~dp0DataTool_260306.py"
set "ICON_PATH=%~dp0DataTool.ico"
set "RUNTIME_HOOK=%~dp0hook-runtime-casadi.py"
"%VENV_EXE%" ^
    --onedir ^
    --noconsole ^
    --noconfirm ^
    --collect-all pybamm ^
    --collect-all casadi ^
    --collect-all pybammsolvers ^
    --collect-binaries casadi ^
    --hidden-import fsspec ^
    --hidden-import anytree ^
    --hidden-import pooch ^
    --hidden-import posthog ^
    --hidden-import xarray ^
    --hidden-import platformdirs ^
    --hidden-import casadi ^
    --hidden-import casadi._casadi ^
    --runtime-hook="%RUNTIME_HOOK%" ^
    --icon="%ICON_PATH%" ^
    "%SCRIPT_PATH%" ^
    --distpath "."

pause