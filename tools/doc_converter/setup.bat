@echo off
REM ===============================================================
REM  doc_converter 초기 셋업 (1회 실행) — uv 기반
REM
REM  venv 탐지 순서:
REM   1. <repo_root>/../.venv   (BDT_code 형제, 사내 표준)
REM   2. <repo_root>/.venv       (저장소 루트)
REM   3. tools/doc_converter/.venv  (로컬 폴백, 신규 생성)
REM
REM  탐지된 venv 는 tools/doc_converter/.venv 로 **junction** 연결해
REM  이후 모든 .bat 와 VS Code 설정이 .venv/Scripts/python.exe 로 일관 접근.
REM ===============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

where uv >nul 2>nul
if errorlevel 1 (
    echo [ERROR] uv 를 찾을 수 없습니다.
    echo   PowerShell: irm https://astral.sh/uv/install.ps1 ^| iex
    exit /b 1
)

REM 기존 junction/.venv 제거 (오래된 링크 정리)
if exist ".venv" (
    REM 디렉토리 심볼릭 링크/junction 인지 확인
    dir .venv 2>nul | findstr "<JUNCTION>" >nul
    if not errorlevel 1 (
        echo [setup] 기존 junction 제거 재연결
        rmdir .venv
    )
)

REM 1. 공유 venv 탐지 (BDT_code 부모)
set "SHARED_VENV="
for %%P in ("..\..\..\.venv" "..\..\.venv") do (
    if exist "%%~P\Scripts\python.exe" (
        set "SHARED_VENV=%%~fP"
        goto :found_shared
    )
)

:found_shared
if defined SHARED_VENV (
    echo [setup] 공유 venv 발견: !SHARED_VENV!
    echo [setup] junction 생성: .venv ^-^> !SHARED_VENV!
    mklink /J .venv "!SHARED_VENV!" >nul
    if errorlevel 1 (
        echo [WARN] junction 실패 — 로컬 venv 로 진행
        goto :make_local
    )
    goto :install_deps
)

:make_local
if not exist ".venv\Scripts\python.exe" (
    echo [setup] 공유 venv 없음 ^-^> 로컬 uv venv 생성 (tools/doc_converter/.venv)
    uv venv --python 3.12
    if errorlevel 1 exit /b 1
) else (
    echo [setup] 기존 로컬 .venv 재사용
)

:install_deps
echo [setup] 의존성 설치 (uv pip install)
uv pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] uv pip install 실패.
    exit /b 1
)

echo.
echo [setup] 모델 사전 다운로드 여부
echo   Y : 지금 HF 모델 받기 (~3GB, 10-20분 소요)
echo   N : 나중에 첫 변환 때 자동 다운로드
set /p PREFETCH="> 선택 (Y/N, 기본 N): "
if /i "%PREFETCH%"=="Y" (
    set PYTHONIOENCODING=utf-8
    uv run python prefetch_models.py
)

echo.
echo [setup] 완료!
echo   - 로컬 OSS 변환 : convert.bat ^<소스폴더^>  또는 VS Code F5
echo   - DoXA API 변환 : doxa_convert.bat ^<소스^>  (사내 + DOXA_TOKEN 설정)
echo   - VS Code        : tools/doc_converter 를 폴더로 열고 F5 / Ctrl+Shift+B
endlocal
