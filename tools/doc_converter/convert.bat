@echo off
chcp 65001 >nul 2>&1
REM ===============================================================
REM  Document - Markdown batch converter (local OSS)
REM  Usage: convert.bat <source> [output] [--force]
REM  Or   : convert.bat     (no args -> interactive GUI dialog)
REM ===============================================================
setlocal
cd /d "%~dp0"

if not exist ".venv" (
    echo [ERROR] .venv not found. Run setup.bat first.
    exit /b 1
)

set PYTHONIOENCODING=utf-8
REM Force HF offline after first model download (blocks re-download)
set HF_HUB_OFFLINE=1
set TRANSFORMERS_OFFLINE=1

uv run python convert.py %*
endlocal
