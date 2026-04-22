@echo off
REM ===============================================================
REM  DoXA API 기반 문서 변환기 (사내 네트워크 전용)
REM  사용: doxa_convert.bat <소스> [출력폴더] [--format standard]
REM ===============================================================
setlocal
cd /d "%~dp0"

if "%DOXA_TOKEN%"=="" (
    echo [ERROR] DOXA_TOKEN 환경변수가 설정되지 않았습니다.
    echo   https://aia.sec.samsung.net 에서 토큰 발급 후:
    echo     set DOXA_TOKEN=^<토큰^>
    exit /b 2
)

if "%~1"=="" (
    echo 사용법: doxa_convert.bat ^<소스파일 또는 폴더^> [출력폴더] [--format ^<포맷^>]
    echo 예시 : doxa_convert.bat "C:\path\raw\g5p_at"
    exit /b 1
)

if not exist ".venv" (
    echo [ERROR] .venv 없음. 먼저 setup.bat 실행 필요.
    exit /b 1
)

call .venv\Scripts\activate.bat
set PYTHONIOENCODING=utf-8

python doxa_convert.py %*
endlocal
