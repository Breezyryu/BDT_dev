@echo off
chcp 65001 >nul 2>&1
REM ===============================================================
REM  DoXA API document converter (Samsung internal)
REM  Usage: doxa_convert.bat <source> [output] [--format <fmt>]
REM  Or   : doxa_convert.bat   (no args -> interactive dialog)
REM ===============================================================
setlocal
cd /d "%~dp0"

if "%DOXA_TOKEN%"=="" (
    echo [ERROR] DOXA_TOKEN not set.
    echo   Get token from https://aia.sec.samsung.net, then:
    echo     set DOXA_TOKEN=^<your_token^>
    exit /b 2
)

if not exist ".venv" (
    echo [ERROR] .venv not found. Run setup.bat first.
    exit /b 1
)

set PYTHONIOENCODING=utf-8

uv run python doxa_convert.py %*
endlocal
