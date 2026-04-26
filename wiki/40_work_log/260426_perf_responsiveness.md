---
title: "260426_perf_responsiveness"
tags: [Work_Log, BDT, Performance, UX, PyInstaller, PyBaMM]
type: changelog
status: active
related:
  - "[[bdt-internals]]"
created: 2026-04-26
updated: 2026-04-26
---

# BDT EXE 반응성·사용성 개선 (묶음 A+B+D)

## 배경

`build_exe_onepath.bat` 로 빌드해 사내 배포하는 BDT EXE 의 콜드 스타트, GUI 반응성, 일상 사용성 결함을 한 번에 보강. 빌드 타깃을 `DataTool_dev_code/DataTool_optRCD_proto_.py` 로 통일하고, 이전 진입점 `DataTool_260306.py` 는 더 이상 빌드 대상이 아님.

도메인 회귀 위험이 큰 matplotlib figure 재구조화·xlwings 워커화(이전 묶음 C)는 본 작업에서 제외, 추후 별도 PR 로 다룰 예정.

## 변경 요약

### 묶음 A — 콜드 스타트 단축 + 스플래시 + 빌드 정합

- `build_exe_onepath.bat`
  - `SCRIPT_PATH` 를 `DataTool_dev_code\DataTool_optRCD_proto_.py` 로 갱신.
  - `--splash="splash.png"`, `--clean` 추가.
  - `--exclude-module IPython/jupyter/pytest/sphinx/notebook` 로 dist 슬리밍 (tkinter 는 25곳 사용 중이라 보존).
  - 중복인 `--collect-binaries casadi` 제거 (`--collect-all casadi` 로 충분).
  - splash.png 부재 시 `gen_splash.py` 자동 호출.
- `gen_splash.py` (신규) — Pillow 로 580×120 단색 placeholder PNG 1회 생성. 텍스트는 런타임에 `pyi_splash.update_text` 로 단계 표시.
- `splash.png` (신규) — 위 스크립트 결과물.
- `DataTool_optRCD_proto_.py` 모듈 최상위 import 정리:
  - `pyodbc`, `xlwings as xw`, `from scipy.optimize import curve_fit, root_scalar`, `from scipy.stats import linregress` 4종을 모듈 `__getattr__` 기반 lazy 로 변환.
  - `pybamm` 직접 import + frozen-mode `ctypes.CDLL` 8개 강제 선로드 블록 제거 → `bdt_pybamm._ensure_pybamm_runtime()` 으로 게이팅.
- `bdt_pybamm.py` (신규) — PyBaMM 시뮬레이션 코어 + lazy 게이트:
  - `is_installed()` (find_spec 만, 콜드 스타트 영향 없음)
  - `is_available()` / `_lazy_pybamm()` (실제 import 시도)
  - `is_empty_solution()`, `okane2022_param_values()`, `run_simulation()` 래퍼
  - `_ensure_pybamm_runtime()` 안에서 frozen 빌드일 때만 casadi DLL 8개 + PATH 등록 (1회 NOOP 게이팅).
- `proto_.py` 의 `run_pybamm_simulation` 195줄 본문 → `bdt_pybamm.run_simulation` 한 줄 위임으로 교체. dead code 0줄.
- `HAS_PYBAMM` 변수 + `pybamm.*` 직접 호출 5곳 모두 `bdt_pybamm.*` 로 위임:
  - setupUi 의 탭 비활성화 게이트 → `bdt_pybamm.is_installed()` (find_spec 만)
  - 시뮬 실행 버튼 / param 평가 → `bdt_pybamm.is_available()`
  - `pybamm.EmptySolution` 검사 → `bdt_pybamm.is_empty_solution(sol)`
  - `pybamm.ParameterValues("OKane2022")` → `bdt_pybamm.okane2022_param_values()`
- 진입점([proto:32748+] 영역):
  - `pyi_splash.update_text("UI 초기화…")` / `…("메인 윈도우 구성…")` 단계 표시 (frozen 빌드 한정).
  - `_bdt_log_path()` 헬퍼 — `%LOCALAPPDATA%/BDT/logs/BDT_YYYYMMDD.log` 회전 로그.
  - `sys.excepthook` 강화: `--noconsole` 빌드에서도 `QMessageBox.critical` 모달 + 로그 파일 기록.
  - `myWindow.show()` 직전 `pyi_splash.close()`.

### 묶음 B — 크로스스레드 안전 채널 + statusBar + 워커 에러 가시화

- `_WorkerSignals(QtCore.QObject)` (신규 모듈 본문 클래스):
  - `progress: pyqtSignal(int)` / `message: pyqtSignal(str)` / `error: pyqtSignal(str, str)` 3채널.
- `WindowClass.__init__` 끝부분에 `_bdt_setup_signals()` 호출 추가:
  - `self._sig.progress.connect(self.progressBar.setValue)`
  - `self._sig.message.connect(lambda s: self.statusBar().showMessage(s, 5000))`
  - `self._sig.error.connect(self._bdt_show_error)` — `QMessageBox.warning` + `logging.warning`.
- 워커 함수 `_load_cycle_data_task` 의 `print(f"[병렬 로딩 오류]...")` 를 `self._sig.error.emit("배터리 데이터 로딩 실패", ...)` 로 교체 (시그널 미연결 시 logging 폴백).

### 묶음 D — QSettings 영속화 · 드래그앤드롭 · 메뉴바 · About

- 기존 `_CYCLE_SETTINGS_ORG="BDT"` / `_CYCLE_SETTINGS_APP="DataTool"` org/app 재사용, 키 네임스페이스 분리:
  - `window/geometry`, `window/state`, `window/recent_folders` (최대 5개).
- `closeEvent` 오버라이드로 종료 시 `saveGeometry`/`saveState`/recent 저장.
- 시작 시 `_bdt_restore_window_state()` 로 복원 + 최근 폴더 메뉴 재구성.
- `setAcceptDrops(True)` + `dragEnterEvent`/`dropEvent` 오버라이드 — 메인 윈도우에 폴더 드롭 시 `cycle_path_table` 첫 빈 행에 자동 입력 + 최근 폴더 추가 + statusBar 안내.
- 메뉴바 신설 (이전엔 메뉴바 자체가 없었음):
  - **File**: 폴더 열기… (Ctrl+O), 최근 폴더(서브메뉴 5개), 종료 (Ctrl+Q)
  - **View**: 새로고침 (F5) — `check_cycler.cache_clear()` + `is_pne_folder.cache_clear()` + Phase 0 메타 무효화
  - **Help**: 로그 폴더 열기, BDT 정보…
- About 다이얼로그 — 버전 `v260426 (proto)`, 빌드 일자, 로그 폴더 경로 안내.

## 검증

```text
$ python -c "import sys; sys.path.insert(0,'DataTool_dev_code'); import DataTool_optRCD_proto_ as m"
proto OK

$ (WindowClass 생성 직후)
pybamm in modules: False
scipy in modules: False
xlwings in modules: False
pyodbc in modules: False
menus: ['&File', '&View', '&Help']
acceptDrops: True
recent_menu: QMenu
```

- 콜드 스타트(파이썬 직접 실행) 기준 무거운 의존성 4종 모두 미로드 — 사용자가 PyBaMM/엑셀/MDB/피팅 탭을 직접 켜기 전까지는 영원히 import 되지 않음.
- WindowClass 인스턴스 생성 정상 (offscreen Qt).
- `_WorkerSignals` 시그널 채널 연결 확인.

## 측정 (TODO — 사내 PC 에서 빌드 후)

| 항목 | Before | After (예상) |
|---|---|---|
| EXE 콜드 스타트 (메인 윈도우 가시) | 측정 필요 | -50% 이상 목표 |
| dist 폴더 부피 | 측정 필요 | -10% 이상 목표 |
| PyBaMM 미사용자 첫 클릭까지 | DLL 8개 + pybamm import 동기 부담 | 게이팅으로 0 |
| 워커 에러 가시화 | 콘솔로만 (`--noconsole`이라 사라짐) | `QMessageBox` + 로컬 로그 |
| 창 크기/스플리터 영속 | 매번 리셋 | QSettings 복원 |
| 폴더 드롭 → 자동 마운트 | 없음 | 메인 윈도우 어디서나 드롭 |

빌드는 `build_exe_onepath.bat` 한 번 실행으로 완료. 사외 환경에선 PyBaMM 시뮬·xlwings DRM 검증 불가 — 사내 PC 회귀 테스트 필요.

## 영향 범위 정리

- **변경된 파일**
  - [`build_exe_onepath.bat`](../../build_exe_onepath.bat)
  - [`gen_splash.py`](../../gen_splash.py) (신규)
  - [`splash.png`](../../splash.png) (신규 바이너리)
  - [`DataTool_dev_code/bdt_pybamm.py`](../../DataTool_dev_code/bdt_pybamm.py) (신규)
  - [`DataTool_dev_code/DataTool_optRCD_proto_.py`](../../DataTool_dev_code/DataTool_optRCD_proto_.py)
- **건드리지 않은 부분 (의도적)**
  - matplotlib figure 재사용 / `draw_idle` 통일 — 회귀 위험으로 별도 PR.
  - xlwings COM 워커화 — 동일.
  - tkinter `filedialog` 25곳 사용처 → `QFileDialog` 단일화 — 변경 분량 큼, 별도 PR.
  - HiDPI 활성화 — 사용자가 의도적으로 주석 처리한 흔적이 있어 보존.
  - 기존 `progressBar.setValue` 113곳 — 워커 안에서 직접 호출하던 부분이 이미 컨슈머 루프(메인 스레드)로 모여 있어 추가 시그널 교체 불필요로 판단. `_load_cycle_data_task` 의 워커 측 `print` 만 시그널로 교체.

## 후속 일감 (분리 PR 권장)

1. matplotlib figure 재사용 패턴 (`set_data` + `draw_idle`) — 사이클 100+ 데이터셋 탭 전환 단축.
2. xlwings 동기 오픈 → `QThreadPool` 비동기화 — 잠긴 .xlsx 에서 GUI 멈춤 방지.
3. tkinter `filedialog` → `QFileDialog` 단일화 + `tkinter` exclude — 추가 dist 슬리밍.
4. `QProgressDialog` 취소 버튼 — 배치 로드 진입점에 적용 (현재 ThreadPoolExecutor 컨슈머 루프에 cancel 분기 추가).
