# 경로 테이블 메타 수집: 자동 → 버튼 트리거로 변경

> **작성일**: 2026-04-16
> **대상 파일**: `DataTool_dev_code/DataTool_optRCD_proto_.py`
> **변경 위치**: `_update_cell_tooltip`, UI 버튼 영역, 시그널 연결

---

## 배경

사이클 데이터 탭의 경로 테이블(`cycle_path_table`)에 경로를 입력(타이핑/붙여넣기)하면 300ms 디바운스 타이머 후 자동으로 메타데이터(시험명/채널/용량/TC)를 수집했다. 경로를 여러 행 빠르게 입력·수정할 때 매번 I/O가 발생하는 문제가 있어 **버튼 클릭으로 명시적 트리거**하도록 변경.

## 변경 내용

### 1. 자동 autofill 디바운스 제거

`_update_cell_tooltip()` 에서 col==1 변경 시:
- ✅ 유지: `_highlight_path_cell(row)`, `_update_group_separators()`
- ❌ 제거: `_autofill_pending_row` 설정 + `_autofill_timer` 300ms 시작 블록

### 2. "🔍 채우기" 버튼 추가

`btn_clear_path`(🗑) 오른쪽에 `btn_autofill_path` 버튼을 `horizontalLayout_108`에 추가.
- 라벨: `🔍 채우기`
- 툴팁: "경로 기반 메타 자동 채우기 (시험명/채널/용량/TC)"
- 스타일: 기존 경로 버튼과 동일 (`_path_btn_qss`)

### 3. `_autofill_all_rows()` 함수

기존 `_autofill_pending_row_handler()` (단일 행 디바운스 핸들러)를 대체.
- 전체 행 순회 → 유효 경로가 있는 행에만 `_autofill_row()` 호출
- 버튼 클릭 시 슬롯으로 연결

### 4. 시그널 연결

`btn_autofill_path.clicked.connect(self._autofill_all_rows)`

## 유지되는 자동 채우기 경로

| 경로 | 동작 | 변경 |
|---|---|---|
| 📂 불러오기 (파일 로드) | `_load_path_file_to_table` 끝에서 `_autofill_table_empty_cells()` 호출 | **유지** |
| 확인 버튼 (실행 시점) | `unified_cyc_confirm_button` 에서 `_autofill_table_empty_cells()` 호출 | **유지** |
| 셀 직접 편집 (경로 타이핑) | 이전: cellChanged → 디바운스 → autofill | **제거** → 버튼으로 대체 |

## 회귀 영향

- 경로 하이라이트(존재/부재 색상 표시)는 그대로 동작 (cellChanged → _highlight_path_cell)
- 구분선 갱신도 그대로 동작 (cellChanged → _update_group_separators)
- `_autofill_row`, `_resolve_path_meta` 함수는 변경 없음
- `_autofill_timer`, `_autofill_pending_row` 는 dead code (호출 안 됨, 향후 정리 가능)

## 검증

1. 경로 직접 입력 → 메타 자동 채워지지 않음 (하이라이트만 표시)
2. "🔍 채우기" 클릭 → 유효 경로 행에 시험명/채널/용량/TC 채워짐
3. 📂 불러오기 → 파일 로드 후 자동 채우기 그대로 동작
4. 빈 행은 건너뜀
5. 2회 연속 클릭 → 동일 결과 (멱등성)
