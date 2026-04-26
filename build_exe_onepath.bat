@echo off
setlocal
echo Building DataTool (onedir)...

cd /d "%~dp0"

set "VENV_EXE=%~dp0.venv\Scripts\pyinstaller.exe"
set "SCRIPT_PATH=%~dp0DataTool_dev_code\DataTool_optRCD_proto_.py"
set "ICON_PATH=%~dp0DataTool.ico"
set "RUNTIME_HOOK=%~dp0hook-runtime-casadi.py"
set "SPLASH_PATH=%~dp0splash.png"

if not exist "%SPLASH_PATH%" (
    echo splash.png not found, generating placeholder...
    "%~dp0.venv\Scripts\python.exe" "%~dp0gen_splash.py"
)

"%VENV_EXE%" ^
    --onedir ^
    --noconsole ^
    --noconfirm ^
    --clean ^
    --collect-all pybamm ^
    --collect-all casadi ^
    --collect-all pybammsolvers ^
    --hidden-import fsspec ^
    --hidden-import anytree ^
    --hidden-import pooch ^
    --hidden-import posthog ^
    --hidden-import xarray ^
    --hidden-import platformdirs ^
    --hidden-import casadi ^
    --hidden-import casadi._casadi ^
    --exclude-module IPython ^
    --exclude-module jupyter ^
    --exclude-module pytest ^
    --exclude-module sphinx ^
    --exclude-module notebook ^
    --runtime-hook="%RUNTIME_HOOK%" ^
    --splash="%SPLASH_PATH%" ^
    --icon="%ICON_PATH%" ^
    "%SCRIPT_PATH%" ^
    --distpath "."

pause
