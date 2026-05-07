# onepath 빌드 — 출력 레이아웃 src/ 분리

- 작성일: 2026-05-07
- 대상: [build_exe_onepath.bat](../../build_exe_onepath.bat)
- 관련: [260507_build_onepath_auto_versioning.md](260507_build_onepath_auto_versioning.md)

## 변경 요약

빌드 결과를 `BUILD_NAME/` 한 폴더 안에 평탄하게 풀던 방식 →
exe·`_internal` 묶음과 `.py` 원본을 **두 서브폴더로 분리**.

## 디렉토리 구조

### 기존 (Before)

```
build/
└── BatteryDataTool_260507/
    ├── _internal/
    ├── BatteryDataTool_260507.exe
    ├── DataTool_optRCD_proto_.py
    └── bdt_pybamm.py
```

### 신규 (After)

```
build/
└── BatteryDataTool_260507/                  ← 외부 폴더 (배포 단위)
    ├── BatteryDataTool_260507/              ← 실행 묶음
    │   ├── _internal/
    │   └── BatteryDataTool_260507.exe
    └── src/                                 ← 원본 .py (exe 활용분만)
        ├── DataTool_optRCD_proto_.py
        └── bdt_pybamm.py
```

## 변경 포인트

| 항목 | 기존 | 신규 |
|---|---|---|
| `--distpath` | `..\build` | `..\build\%BUILD_NAME%` |
| .py 복사 위치 | `%BUILD_NAME%\` | `%BUILD_NAME%\src\` |
| 빌드 성공 체크 | `..\build\%BUILD_NAME%` | `..\build\%BUILD_NAME%\%BUILD_NAME%` |
| `src/` 자동 생성 | 없음 | `mkdir` 추가 |

## 코드 diff

```bat
:: --- PyInstaller 호출
-    --distpath "%~dp0..\build"
+    --distpath "%~dp0..\build\%BUILD_NAME%"

:: --- 후처리 .py 복사
-if exist "%~dp0..\build\%BUILD_NAME%" (
-    echo Copying source files...
-    copy "...DataTool_optRCD_proto_.py" "%~dp0..\build\%BUILD_NAME%\" >nul
-    copy "...bdt_pybamm.py"             "%~dp0..\build\%BUILD_NAME%\" >nul
+if exist "%~dp0..\build\%BUILD_NAME%\%BUILD_NAME%" (
+    echo Copying source files to src/...
+    if not exist "%~dp0..\build\%BUILD_NAME%\src" mkdir "%~dp0..\build\%BUILD_NAME%\src"
+    copy "...DataTool_optRCD_proto_.py" "%~dp0..\build\%BUILD_NAME%\src\" >nul
+    copy "...bdt_pybamm.py"             "%~dp0..\build\%BUILD_NAME%\src\" >nul
)
```

## src/ 포함 범위 — exe 활용 .py 만

| 파일 | exe 사용? | src/ 포함? |
|---|---|---|
| `DataTool_optRCD_proto_.py` | entry point | O |
| `bdt_pybamm.py` | `import bdt_pybamm` + `--add-data` | O |
| `DataTool_UI.py` | 별개 UI 실험 | X |
| `DataTool_UI_test.py` | 테스트 | X |

상대 import (`from .`) 나 동적 로드 없음 → 두 파일이 exe 가 의존하는 .py 전부.

## 의도

- 배포 산출물(exe·`_internal`)과 **참조용 원본 코드**를 시각적으로 분리
- `_internal/` 안에 `.py` 가 섞여 있으면 그룹원이 "이 파일 수정해도 되나?"
  로 혼동 → `src/` 폴더로 격리하면 의도가 명확
- 외부 폴더명과 내부 실행 폴더명이 동일(`BUILD_NAME`)하므로 zip 으로 압축
  해서 보내도 압축 해제 시 폴더 1단계 감싸짐이 자연스러움

## 호환성

- `_v1`/`_v2` 자동 suffix 로직 그대로 작동 (외부 폴더 단위로 충돌 검사)
- onefile 빌드(`build_exe_onefile.bat`) 는 단일 exe 출력이므로 **변경
  대상 아님** — 그대로 둠
