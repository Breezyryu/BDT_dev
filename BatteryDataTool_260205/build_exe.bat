@echo off
echo Building BatteryDataTool.exe...

REM ============================================
REM 환경에 맞게 아래 경로를 수정하세요
REM ============================================
REM 현재 PC:  set VENV_PATH=%~dp0..\.venv
REM 다른 PC:  set VENV_PATH=%~dp0..\..\..\.venv
set VENV_PATH=%~dp0..\.venv
REM ============================================

REM 현재 배치 파일 위치로 이동
cd /d "%~dp0"

"%VENV_PATH%\Scripts\pyinstaller.exe" ^
    --onefile ^
    --noconsole ^
    --noconfirm ^
    --uac-admin ^
    --hidden-import fsspec ^
    "%~dp0BatteryDataTool.py" ^
    --distpath "."

echo Build complete.
pause

