@echo off
setlocal
chcp 65001 >nul
echo Starting DataTool with BDT_TRACE enabled (dev mode)...
echo.

cd /d "%~dp0"

REM Default: <BDT_dev parent>\bdt_trace (same level as build folder)
if "%~1"=="" (
    set "TRACE_DIR=%~dp0..\bdt_trace"
) else (
    set "TRACE_DIR=%~1"
)

if "%~2"=="" (
    set "TRACE_LEVEL=substep"
) else (
    set "TRACE_LEVEL=%~2"
)

set "BDT_TRACE=1"
set "BDT_TRACE_DIR=%TRACE_DIR%"
set "BDT_TRACE_LEVEL=%TRACE_LEVEL%"

echo BDT_TRACE       = %BDT_TRACE%
echo BDT_TRACE_DIR   = %BDT_TRACE_DIR%
echo BDT_TRACE_LEVEL = %BDT_TRACE_LEVEL%
echo.
echo Output: %TRACE_DIR%\session_^<TS^>\step.csv  step_summary.md  step_hotspot.png
echo.

if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYEXE=%~dp0.venv\Scripts\python.exe"
) else if exist "%~dp0..\.venv\Scripts\python.exe" (
    set "PYEXE=%~dp0..\.venv\Scripts\python.exe"
) else (
    echo [ERROR] .venv not found.
    pause
    exit /b 1
)

"%PYEXE%" "%~dp0DataTool_dev_code\DataTool_optRCD_proto_.py"

echo.
echo [done] Trace artifacts: %TRACE_DIR%
pause
