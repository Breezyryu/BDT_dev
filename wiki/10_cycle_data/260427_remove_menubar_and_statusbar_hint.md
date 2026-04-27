# 260427 메뉴바(File/View/Help) + 상태바 안내 메시지 제거

## 배경

사용자 요청: 화면 상단 `File / View / Help` 메뉴바와 화면 하단의
"준비됨 — 폴더를 드래그하거나 Ctrl+O 로 열기" 안내 텍스트가 운영상 불필요
하다. 깔끔한 UI 를 위해 두 요소를 제거.

## 변경 내용

### 1. `_bdt_setup_signals` — 메뉴 셋업 호출 + 안내 메시지 제거
**Before**
```python
self.statusBar().showMessage("준비됨 — 폴더를 드래그하거나 Ctrl+O 로 열기")

self._bdt_setup_dnd()
self._bdt_setup_menu()
self._bdt_restore_window_state()
```

**After**
```python
self._bdt_setup_dnd()
self._bdt_restore_window_state()
```

statusBar 자체는 유지 — 워커 진행률·에러 메시지가 transient 로 표시됨.
영구적으로 노출되는 안내 텍스트만 삭제.

### 2. 메뉴바 + 메뉴 액션 함수 제거
**제거 대상** (proto_.py:17684~17753 일대):
- `_bdt_setup_menu(self)` — File/View/Help 메뉴바 구성
- `_bdt_action_open_folder(self)` — 폴더 열기
- `_bdt_action_refresh(self)` — 캐시 비움 (F5)
- `_bdt_action_open_log_dir(self)` — 로그 폴더 열기
- `_bdt_action_about(self)` — BDT 정보 모달

`_bdt_recent_folders` / `_bdt_add_recent` / `_bdt_refresh_recent_menu` 는
**유지** — drag-drop 으로 폴더 추가 시 QSettings 에 최근 경로를 기록
하는 데 여전히 사용됨. `_bdt_refresh_recent_menu` 는 `_bdt_recent_menu`
속성이 없으므로 no-op 으로 안전 동작.

## 동작 변화

| 항목 | Before | After |
|---|---|---|
| 상단 메뉴바 | `File / View / Help` 표시 | **없음** |
| 하단 상태바 (초기) | `"준비됨 — 폴더를 드래그하거나 Ctrl+O 로 열기"` 영구 표시 | **빈 상태** |
| Ctrl+O 단축키 | 메뉴 액션으로 매핑됨 | 동작 안 함 (필요 시 재추가) |
| F5 단축키 | 캐시 비움 | 동작 안 함 (필요 시 재추가) |
| Drag-drop 폴더 추가 | 정상 + 6초 알림 | 정상 + 6초 알림 (변경 없음) |
| 워커 진행/에러 메시지 | 상태바 표시 | 상태바 표시 (변경 없음) |
| 창 위치/크기 복원 | QSettings 기반 | 변경 없음 |

## 영향 범위

### 사라지는 기능
- 메뉴를 통한 **폴더 열기** UI — Drag-drop 또는 사이클 탭 내부 버튼으로 대체 가능
- **F5 새로고침** 단축키
- **로그 폴더 열기** (메뉴 → Help)
- **BDT 정보** 모달

### 유지되는 기능
- Drag-drop 폴더 추가 (기존 `_bdt_setup_dnd` 그대로)
- 워커 progress/error 상태바 알림 (5초 transient)
- QSettings 창 상태 영속화
- 최근 폴더 기록 (메뉴는 없지만 데이터는 보존, 향후 재활용 가능)

### 향후 (필요 시)
단축키만 다시 살리고 싶다면 `_bdt_setup_signals` 에 다음 한 줄로 충분:
```python
QtGui.QShortcut(QtGui.QKeySequence("F5"), self).activated.connect(...)
```

## 파일 변경 요약

| 파일 | 변경 |
|---|---|
| `DataTool_dev_code/DataTool_optRCD_proto_.py` | -73 / +5 (메뉴 셋업 + 액션 4개 + 상태바 초기 메시지 제거) |
| `wiki/10_cycle_data/260427_remove_menubar_and_statusbar_hint.md` | 신규 (본 문서) |
