@echo off
REM ===============================================================
REM  doc_converter 초기 셋업 (1회 실행)
REM  - Python 3.12 venv 생성
REM  - 의존성 설치 (pip)
REM  - 모델 사전 다운로드 (HF 캐시 채움)
REM ===============================================================
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] python 을 찾을 수 없습니다. Python 3.12+ 설치 필요.
    exit /b 1
)

if not exist ".venv" (
    echo [setup] Python venv 생성
    python -m venv .venv
    if errorlevel 1 exit /b 1
)

call .venv\Scripts\activate.bat

echo [setup] pip 업그레이드
python -m pip install --upgrade pip

echo [setup] 의존성 설치 (requirements.txt)
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] pip install 실패. 사내 PyPI 미러 설정 확인.
    exit /b 1
)

echo [setup] 모델 사전 다운로드
set PYTHONIOENCODING=utf-8
python prefetch_models.py

echo.
echo [setup] 완료. 이제 convert.bat 로 변환 실행 가능.
echo   사용법: convert.bat ^<소스폴더^> [출력폴더]
endlocal
