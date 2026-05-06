# onepath 빌드 — 출력 폴더 자동 버전 suffix

- 작성일: 2026-05-07
- 대상: `build_exe_onepath.bat`

## 변경

기존 — 빌드 시 `BatteryDataTool_YYMMDD` 폴더로 출력. 같은 날 두 번째
빌드 시 PyInstaller `--noconfirm` 가 기존 폴더를 **덮어쓰기** → 이전
빌드 결과 손실.

신규 — 폴더 존재 체크 + 자동 `_v1`, `_v2` ... suffix 추가.

```bat
set "BUILD_BASE=BatteryDataTool_%YYMMDD%"
set "BUILD_NAME=%BUILD_BASE%"
set "VERSION=1"

:check_folder
if exist "%~dp0..\build\%BUILD_NAME%" (
    set "BUILD_NAME=%BUILD_BASE%_v%VERSION%"
    set /a VERSION+=1
    goto check_folder
)
echo Output folder: %BUILD_NAME%
```

## 동작 시나리오

| 빌드 회차 | 기존 폴더 | 결과 BUILD_NAME |
|---|---|---|
| 1회차 | (없음) | `BatteryDataTool_260506` |
| 2회차 | `BatteryDataTool_260506` | `BatteryDataTool_260506_v1` |
| 3회차 | `BatteryDataTool_260506`, `_v1` | `BatteryDataTool_260506_v2` |
| 4회차 | `..._v2` 까지 | `BatteryDataTool_260506_v3` |

## 영향
- PyInstaller `--name "%BUILD_NAME%"` + `--distpath ../build` 그대로
  사용 → 새 폴더에 빌드, 기존 폴더 보존
- 빌드 후 `.py` 원본 복사 로직 ([:70-75](../../build_exe_onepath.bat:70))
  도 동일 BUILD_NAME 사용 → 새 폴더에 정확히 복사
- echo 로 빌드 시작 시 출력 폴더명 노출 (체크용)

## 주의
- cmd `set /a` + 변수 expansion 패턴 사용 — `setlocal enabledelayedexpansion`
  불필요 (블록 진입마다 `%VAR%` 재expand)
- 폴더 명만 검사 — 파일/하위 폴더 충돌 시도는 하지 않음 (PyInstaller 가
  처리)
