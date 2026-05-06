@echo off
setlocal
echo Building DataTool (onedir)...

cd /d "%~dp0"

:: .venv 탐색: 현재 디렉토리 → 상위 디렉토리
if exist "%~dp0.venv\Scripts\pyinstaller.exe" (
    set "VENV_DIR=%~dp0.venv"
) else if exist "%~dp0..\.venv\Scripts\pyinstaller.exe" (
    set "VENV_DIR=%~dp0..\.venv"
) else (
    echo [ERROR] .venv not found. Checked:
    echo   %~dp0.venv
    echo   %~dp0..\.venv
    pause
    exit /b 1
)

set "VENV_EXE=%VENV_DIR%\Scripts\pyinstaller.exe"
set "SCRIPT_PATH=%~dp0DataTool_dev_code\DataTool_optRCD_proto_.py"
set "BDT_PYBAMM=%~dp0DataTool_dev_code\bdt_pybamm.py"
set "ICON_PATH=%~dp0DataTool.ico"
set "RUNTIME_HOOK=%~dp0hook-runtime-casadi.py"
set "SPLASH_PATH=%~dp0splash.png"

:: 출력명: BatteryDataTool_YYMMDD (로케일 무관)
:: Win11 24H2 이후 wmic 제거 → powershell Get-Date 로 대체 (Win7+ 호환)
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyMMdd"') do set "YYMMDD=%%I"
set "BUILD_NAME=BatteryDataTool_%YYMMDD%"

if not exist "%SPLASH_PATH%" (
    echo [ERROR] splash.png not found: %SPLASH_PATH%
    pause
    exit /b 1
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
    --hidden-import xlwings ^
    --hidden-import pyodbc ^
    --exclude-module IPython ^
    --exclude-module jupyter ^
    --exclude-module pytest ^
    --exclude-module sphinx ^
    --exclude-module notebook ^
    --runtime-hook="%RUNTIME_HOOK%" ^
    --add-data "%BDT_PYBAMM%;." ^
    --splash="%SPLASH_PATH%" ^
    --icon="%ICON_PATH%" ^
    --name "%BUILD_NAME%" ^
    "%SCRIPT_PATH%" ^
    --distpath "%~dp0..\build"

:: 빌드 성공 시 .py 원본을 출력 폴더에 복사
if exist "%~dp0..\build\%BUILD_NAME%" (
    echo Copying source files...
    copy "%~dp0DataTool_dev_code\DataTool_optRCD_proto_.py" "%~dp0..\build\%BUILD_NAME%\" >nul
    copy "%~dp0DataTool_dev_code\bdt_pybamm.py" "%~dp0..\build\%BUILD_NAME%\" >nul
    echo Done: ..\build\%BUILD_NAME%\
)

pause
