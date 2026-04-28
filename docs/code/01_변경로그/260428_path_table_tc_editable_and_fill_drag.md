# 경로 테이블 — TC 항상 편집 가능 + Excel-style 드래그 채우기

날짜: 2026-04-28
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수:
- `_update_ect_columns_state()` (~L24625)
- `eventFilter()` (~L24783) — viewport 마우스 이벤트 분기 추가
- `_is_fill_handle_click()`, `_start_fill_drag()`, `_update_fill_drag()`, `_finish_fill_drag()` (신규, ~L24866+)
- `_cycle_table_paste()` (~L23866) — broadcast paste 분기 추가
- `_bdt_setup_signals()` (~L17621) — viewport eventFilter 설치 + 상태 초기화

## 배경

사용자 보고 2건:

1. **TC 입력 가능하도록 변경**: 기존 `_update_ect_columns_state` 가 ECT path 체크 OFF 시 col 4 (TC) 를 read-only 처리. 사용자는 stepnum 또는 사이클 바를 통해서만 TC 입력 가능 — 직접 입력 불가능.
2. **드래그 후 붙여넣기 기능 추가**: Excel 의 fill-handle drag 처럼 한 셀의 값을 드래그로 인접 셀에 복사하는 기능 부재.

## 변경 1 — TC 컬럼 항상 편집 가능

`_update_ect_columns_state` 의 col 토글 로직 분리:
- **col 4 (TC)**: ECT 무관하게 **항상 편집 가능 + 기본 배경**
- **col 5 (모드)**: 기존대로 ECT 체크 시에만 편집 가능 (모드는 ECT 모드에서만 의미 있음)

```python
# col 4 (TC) — 항상 편집 가능 보장
item4.setFlags(item4.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
item4.setBackground(clear_bg)
# col 5 (모드) — ECT 체크 시에만 편집 가능
if ect_on:
    item5.setFlags(item5.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
else:
    item5.setFlags(item5.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
```

stepnum / 사이클 바와 양방향 동기화는 기존 `_on_cycle_cell_changed` 로직이 그대로 동작.

## 변경 2 — Excel-style fill-drag 핸들

선택 셀 우하단 6×6 픽셀 hot zone 에서 마우스 드래그 → 인접 셀에 소스 값 복사.

### 동작 흐름
1. 셀 선택 (currentItem) 후 우하단 핸들 영역 호버 → cursor 가 cross-cursor (✚) 로 변경 (UX 힌트).
2. 핸들에서 left mouse press → `_start_fill_drag` 가 source `(row, col, value)` 캡처.
3. 마우스 드래그 → `_update_fill_drag` 가 target 셀까지 직사각형 영역을 selection 으로 시각화.
4. 마우스 release → `_finish_fill_drag` 가 영역 내 모든 셀 (소스 제외) 에 value 복사. `_push_table_undo` 호출 — Ctrl+Z 로 되돌리기 가능.

### 핵심 구현

```python
# viewport 에 eventFilter 설치
self.cycle_path_table.viewport().installEventFilter(self)
self._fill_drag_active = False
self._fill_drag_source: tuple[int, int, str] | None = None
self._fill_drag_last_target: tuple[int, int] | None = None
```

`eventFilter` 의 viewport 분기:
- `MouseButtonPress` + 핸들 영역 → `_start_fill_drag`
- `MouseMove` + active → `_update_fill_drag` (selection 갱신)
- `MouseMove` + idle + 핸들 호버 → cursor 변경
- `MouseButtonRelease` + active → `_finish_fill_drag`

`_is_fill_handle_click` — `tbl.visualItemRect(currentItem)` 로 셀 사각형 획득 후 우하단 6×6 `QRect` 가 마우스 좌표를 포함하는지 검사.

`_finish_fill_drag` 는 read-only flag 가 없는 셀만 채우므로 col 5 (모드, ECT off 시 read-only) 등은 자동 보호. cellChanged 시그널을 수동 emit 하여 col 4 → 사이클 바 동기화도 정상 트리거.

## 변경 3 — Broadcast paste

`_cycle_table_paste` 에 분기 추가: 클립보드가 1×1 (단일 값) 이고 선택 영역이 N×M (N+M > 2) 이면 영역 전체에 broadcast 복사.

```python
is_single_value = (len(rows) == 1 and len(rows[0]) == 1)
if is_single_value and sel:
    n_target = (r_hi - r_lo + 1) * (c_hi - c_lo + 1)
    if n_target > 1:
        # 모든 선택 셀에 single_val 복사 (read-only 셀은 skip)
        ...
        return
```

이는 fill-drag 와 보완적 — 키보드 기반 fill (Ctrl+C → 영역 선택 → Ctrl+V) 을 가능하게 함.

## 변경 위치 요약

| 라인 | 함수 | 변경 |
|---|---|---|
| ~L17621 | `_bdt_setup_signals` | `viewport().installEventFilter(self)` + fill-drag 상태 초기화 |
| ~L23866 | `_cycle_table_paste` | broadcast paste 분기 추가 (1×1 → N×M) |
| ~L24625 | `_update_ect_columns_state` | col 4 ↔ col 5 토글 분리, col 4 항상 편집 가능 |
| ~L24783 | `eventFilter` | viewport 마우스 이벤트 분기 (fill-drag, hover cursor) |
| ~L24866 | `_is_fill_handle_click` (신규) | currentItem 우하단 6×6 hot zone 판정 |
| ~L24881 | `_start_fill_drag` (신규) | 소스 셀 정보 캡처 |
| ~L24891 | `_update_fill_drag` (신규) | 드래그 중 selection 시각화 |
| ~L24909 | `_finish_fill_drag` (신규) | 영역에 값 복사 + cellChanged emit |

기존 동작 (드래그앤드롭 파일/폴더, Ctrl+C/V/Z, Delete, Enter 행 확장) 은 모두 유지.

## 검증 (사용자 측)

1. BDT 재시작 → 사이클데이터 탭.
2. **TC 편집 검증**: ECT path 체크 OFF 상태에서 TC 셀 더블클릭 → 텍스트 편집 가능 확인. "1-50" 등 직접 입력 → 검정 폰트 + 사이클 바 동기화 + stepnum 동기화 확인.
3. **Fill-drag 검증**:
   a. TC 셀에 "3-12" 입력.
   b. 셀 선택된 상태에서 마우스를 우하단 모서리(6×6px)로 이동 → cursor 가 ✚ 로 변경 확인.
   c. 핸들에서 좌클릭 후 아래로 드래그 → 드래그 영역이 selection 으로 표시.
   d. 마우스 release → 모든 영역의 TC 셀에 "3-12" 복사 확인.
   e. Ctrl+Z 로 되돌리기 동작 확인.
4. **Broadcast paste 검증**:
   a. 한 셀 (예: "3-12") 복사 (Ctrl+C).
   b. col 4 의 다른 행 5개 선택 (drag 또는 shift+click).
   c. Ctrl+V → 5개 셀 모두 "3-12" 채워짐 확인.

## 회귀 / 영향 범위

- ECT 모드 토글 동작 (col 5, stepnum 활성/비활성): 기존과 동일.
- 파일/폴더 드래그앤드롭 (col 1 경로 입력): 변경 없음 — viewport eventFilter 가 추가되었지만 drag/drop 이벤트는 table 자체에서 처리.
- Ctrl+C / Ctrl+V (다중 셀 paste): 기존 동작 유지 (1×1 broadcast 만 신규 분기).
- 우클릭 컨텍스트 메뉴, Enter 행 확장 등: 변경 없음.

## 한계 / 후속 작업

1. **편집 중 fill-drag 비활성화**: 셀 편집 모드 (persistent editor 열림) 에서는 마우스 이벤트가 editor 로 전달되어 fill-drag 가 트리거되지 않음 — 의도된 동작이지만 사용자 혼동 가능. 필요 시 명시적 안내 추가.
2. **연속 dragging UX**: 현재 release 시점에만 채우기. Excel 처럼 drag 중 실시간 미리보기 (회색 outline) 를 추가하려면 `paintEvent` 오버라이드 필요 — 현재 구현은 selection rect 만으로 시각 피드백.
3. **Fill direction**: 좌상→우하 / 우하→좌상 모두 동작 (`sorted` 사용). 대각선 영역 채우기도 지원.
