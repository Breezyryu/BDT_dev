# 파일명에서 "Battery" 제거

## 날짜
2026-03-10

## 변경 내용
모든 파일/폴더명에서 `Battery` 접두어를 제거하여 `BatteryDataTool` → `DataTool`로 변경함.

### 이름 변경된 파일/폴더 (BAK/ 제외)

| 변경 전 | 변경 후 |
|---------|---------|
| `BatteryDataTool.py` | `DataTool.py` |
| `BatteryDataTool.ico` | `DataTool.ico` |
| `BatteryDataTool.spec` | `DataTool.spec` |
| `BatteryDataTool_260306.py` | `DataTool_260306.py` |
| `BatteryDataTool_260306.spec` | `DataTool_260306.spec` |
| `BatteryDataTool_dev/` | `DataTool_dev/` |
| `BatteryDataTool_dev/BatteryDataTool.py` | `DataTool_dev/DataTool.py` |
| `BatteryDataTool_dev/BatteryDataTool_optRCD_proto_.py` | `DataTool_dev/DataTool_optRCD_proto_.py` |
| `BatteryDataTool_dev/BatteryDataTool_UI.py` | `DataTool_dev/DataTool_UI.py` |
| `BatteryDataTool_dev/BatteryDataTool_UI.ui` | `DataTool_dev/DataTool_UI.ui` |
| `BatteryDataTool_dev/BatteryDataTool_UI_260209.ui` | `DataTool_dev/DataTool_UI_260209.ui` |
| `build/BatteryDataTool/` | `build/DataTool/` |
| `build/BatteryDataTool_260306/` | `build/DataTool_260306/` |

### 내부 참조 업데이트

- `build_exe_onefile.bat` — 스크립트/아이콘 경로 업데이트
- `build_exe_onepath.bat` — 스크립트/아이콘 경로 업데이트
- `build_ui.bat` — UI 파일 경로 업데이트
- `DataTool.spec` — Analysis, EXE, COLLECT 이름/경로 업데이트
- `DataTool_260306.spec` — Analysis, EXE, COLLECT 이름/경로 업데이트
- `.gitignore` — `BatteryDataTool/` → `DataTool/`

### 미변경 대상
- `BAK/` 폴더 내 파일 (읽기 전용 정책에 따라 미변경)
- `.py` 파일 내부의 윈도우 타이틀 문자열 (`"BatteryDataTool v260224"` 등) — UI 표시 이름이므로 유지
