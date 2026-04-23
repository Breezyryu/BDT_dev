@echo off
REM ===============================================================
REM  doc_converter 초기 셋업 (1회 실행) — uv 기반
REM
REM  [중요] 기본값: tools/doc_converter/.venv 에 **별도 venv** 생성.
REM  이유:
REM    1. BDT .venv 오염 방지 (doc_converter 의존성 ~5GB 분리)
REM    2. PyInstaller 로 DataTool.exe 패키징 시 doc_converter 라이브러리
REM       번들 가능성 완전 차단
REM    3. 문서 변환 파이프라인을 선택적으로 설치/제거 가능
REM
REM  공유 venv 가 꼭 필요하면 --shared 플래그로 강제 (BDT_code 부모 .venv 사용).
REM ===============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

where uv >nul 2>nul
if errorlevel 1 (
    echo [ERROR] uv 를 찾을 수 없습니다.
    echo   PowerShell: irm https://astral.sh/uv/install.ps1 ^| iex
    exit /b 1
)

REM --shared 플래그 처리
set "USE_SHARED=0"
if /i "%~1"=="--shared" set "USE_SHARED=1"

if "!USE_SHARED!"=="1" (
    REM 공유 venv 탐지 (BDT_code 부모)
    set "SHARED_VENV="
    for %%P in ("..\..\..\.venv" "..\..\.venv") do (
        if exist "%%~P\Scripts\python.exe" (
            set "SHARED_VENV=%%~fP"
            goto :found_shared
        )
    )
    echo [ERROR] --shared 지정했으나 부모 .venv 없음
    exit /b 1

    :found_shared
    echo [setup] 공유 venv 사용: !SHARED_VENV!
    echo [WARN]  BDT .venv 에 ~5GB 의존성 추가됩니다. DataTool.exe 패키징에는 영향 없음 (PyInstaller 는 import 된 것만 번들).

    if exist ".venv" rmdir /s /q .venv >nul 2>&1
    mklink /J .venv "!SHARED_VENV!" >nul
    if errorlevel 1 (
        echo [ERROR] junction 실패
        exit /b 1
    )
    goto :install_deps
)

REM 기본: 로컬 별도 venv
REM 기존 junction 이면 제거 후 재생성
if exist ".venv" (
    dir .venv 2>nul | findstr "<JUNCTION>" >nul
    if not errorlevel 1 (
        echo [setup] 기존 junction 제거
        rmdir .venv
    )
)

if not exist ".venv\Scripts\python.exe" (
    echo [setup] 로컬 uv venv 생성 (tools/doc_converter/.venv, Python 3.12)
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
echo.
echo [참고] PyInstaller 로 DataTool.exe 패키징 시 이 venv 의 라이브러리는
echo        포함되지 않습니다 (BDT 가 import 하지 않는 패키지는 번들 제외).
endlocal
