@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
cd /d "%~dp0"

REM ===============================================================
REM  doc_converter setup (run once) - uv based
REM
REM  Default: create LOCAL venv at tools/doc_converter/.venv
REM   - Isolates doc_converter deps (~5GB) from BDT venv
REM   - Guarantees PyInstaller never bundles these libs into DataTool.exe
REM
REM  Options:
REM    setup.bat            : default, local venv
REM    setup.bat --shared   : junction to BDT parent .venv (shared)
REM ===============================================================

REM 1. Check uv
where uv >nul 2>nul
if errorlevel 1 (
    echo [ERROR] uv not found.
    echo   Install with PowerShell:
    echo     irm https://astral.sh/uv/install.ps1 ^| iex
    exit /b 1
)

REM 2. Parse flags
set "USE_SHARED=0"
if /i "%~1"=="--shared" set "USE_SHARED=1"

REM 3. Clean stale junction (if exists)
if exist ".venv" (
    dir .venv 2>nul | findstr /C:"<JUNCTION>" >nul 2>&1
    if not errorlevel 1 (
        echo [setup] Remove stale junction
        rmdir .venv
    )
)

REM 4. Prepare venv
if "%USE_SHARED%"=="1" (
    call :setup_shared
    if errorlevel 1 exit /b 1
) else (
    call :setup_local
    if errorlevel 1 exit /b 1
)

REM 5. Install dependencies (with sequential fallback on conflict)
echo [setup] Install dependencies via uv pip (combined resolution)
uv pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [WARN] Combined install failed. Trying sequential install
    echo        (works around resolver conflicts with older PyPI mirrors).
    echo.
    uv pip install "mineru[core]>=3.1,<4" || exit /b 1
    uv pip install "docling>=2.90,<3" || exit /b 1
    uv pip install "markitdown[pdf,pptx,docx]>=0.1,<1" || exit /b 1
    uv pip install "easyocr>=1.7" "pymupdf>=1.27" || exit /b 1
    uv pip install "pandas>=2.2" "openpyxl>=3.1" "tabulate>=0.10" ^
                   "requests>=2.32" "urllib3>=2.0" || exit /b 1
    echo [setup] Sequential install succeeded.
)

REM 6. Optional model prefetch
echo.
echo [?] Prefetch HF models now? (~3GB, 10-20min)
echo     Y : download now
echo     N : lazy-load on first conversion (default)
set "PREFETCH=N"
set /p "PREFETCH=> "
if /i "%PREFETCH%"=="Y" (
    set PYTHONIOENCODING=utf-8
    uv run python prefetch_models.py
)

echo.
echo [setup] Done!
echo   Local OSS : convert.bat ^<source_folder^>   or VS Code F5
echo   DoXA API  : doxa_convert.bat ^<source^>     (requires DOXA_TOKEN)
echo   VS Code   : open tools/doc_converter folder, press F5 / Ctrl+Shift+B
echo.
echo [Note] DataTool.exe (PyInstaller) does NOT bundle these libs
echo        unless BDT main code imports them (verified: no imports).
exit /b 0


REM ===============================================================
REM  Subroutines
REM ===============================================================

:setup_shared
set "SHARED_VENV="
if exist "..\..\..\.venv\Scripts\python.exe" set "SHARED_VENV=%CD%\..\..\..\.venv"
if exist "..\..\.venv\Scripts\python.exe" if not defined SHARED_VENV set "SHARED_VENV=%CD%\..\..\.venv"

if not defined SHARED_VENV (
    echo [ERROR] --shared requested but no parent .venv found.
    echo         Checked: ..\..\..\.venv  and  ..\..\.venv
    exit /b 1
)

echo [setup] Shared venv: !SHARED_VENV!
echo [WARN]  BDT venv will grow by ~5GB. DataTool.exe bundle unaffected.

mklink /J .venv "!SHARED_VENV!" >nul
if errorlevel 1 (
    echo [ERROR] junction creation failed
    exit /b 1
)
exit /b 0


:setup_local
if not exist ".venv\Scripts\python.exe" (
    echo [setup] Create local uv venv at tools/doc_converter/.venv (Python 3.12)
    uv venv --python 3.12
    if errorlevel 1 exit /b 1
) else (
    echo [setup] Reuse existing local .venv
)
exit /b 0
