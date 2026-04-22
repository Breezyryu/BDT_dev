@echo off
REM ===============================================================
REM  문서 → Markdown 일괄 변환 실행기
REM  사용: convert.bat <소스폴더> [출력폴더] [--force]
REM ===============================================================
setlocal
cd /d "%~dp0"

if "%~1"=="" (
    echo 사용법: convert.bat ^<소스폴더^> [출력폴더] [--force]
    echo 예시 : convert.bat "C:\Users\me\Documents\raw\g5p_at"
    exit /b 1
)

if not exist ".venv" (
    echo [ERROR] .venv 없음. 먼저 setup.bat 실행 필요.
    exit /b 1
)

call .venv\Scripts\activate.bat
set PYTHONIOENCODING=utf-8
REM HF 오프라인 강제 (모델 재다운로드 차단)
set HF_HUB_OFFLINE=1
set TRANSFORMERS_OFFLINE=1

python convert.py %*
endlocal
