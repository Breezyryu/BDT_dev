# 경로 교체 시 채널/용량/사이클 셀 자동 갱신

## 배경

`cycle_path_table`에서 기존 경로값을 다른 경로로 교체했을 때 채널(col2) · 용량(col3) · 사이클(col4) 셀과 사이클 바가 이전 경로 기준으로 남아있던 문제.

### 원인

1. `_update_cell_tooltip`의 col=1 분기는 경로 존재 색상과 그룹 구분선만 갱신. 자동 메타 수집은 의도적으로 제거되어 `btn_autofill_path`(🔍 채우기) 버튼으로만 복구 가능했음.
2. `_autofill_row`는 **빈 셀만** 채움 (`if not existing:`). 경로 교체 후 기존 셀 값이 남아있으면 🔍 버튼을 눌러도 갱신되지 않음.
3. `_init_confirm_button`이 stale col3 용량을 `per_path_capacities`로 Phase 0에 주입 → 새 경로가 잘못된 용량으로 cycle_map 빌드.
4. 프로필 분석 버튼은 Phase 0 + 타임라인 갱신을 수행하지만, 사이클 분석 버튼과 달리 `_autofill_table_empty_cells()`를 호출하지 않았음.

## 변경 내용

### 1. 프로필 분석 버튼 진입부 autofill
`unified_profile_confirm_button` 시작부, `_init_confirm_button` 호출 직전에 `_autofill_table_empty_cells()`를 호출. 사이클 분석 버튼과 동일 처리로 stale col3가 Phase 0에 주입되는 것을 방지.

### 2. col=1 경로 변경 감지 훅
`WindowClass._row_last_path: dict[int, str]` 속성 추가 — 행별 마지막 경로 추적.

신규 메서드 `_on_path_cell_changed(row)`:
- 이전 경로와 새 경로 비교, 동일하면 즉시 리턴.
- 교체/삭제 시: 이전 경로 메타(`_path_meta_cache`)를 기준으로 col 0/2/3 중 auto 값과 일치하는 셀을 클리어. col 4는 회색 힌트(auto)만 클리어, 사용자 입력(검정)은 보존.
- 새 경로가 유효하면 `_autofill_row(row)` 호출로 재채우기.
- `_row_last_path[row]` 갱신.

`_update_cell_tooltip` col=1 분기에서 새 훅 호출.

### 3. 내부 bulk 연산 내 signal 차단 + 매핑 동기화
- `_set_table_rows` — 로드 중 cellChanged 중복 I/O 방지 (로드 후 `_autofill_table_empty_cells`가 처리).
- `_swap_table_rows` — 부분 swap 상태에서 훅이 오작동하지 않도록 signal 차단, 수동으로 highlight/separator 수행, `_row_last_path` 두 행 교환.
- `_clear_table` — `_row_last_path.clear()` 추가.
- `_cycle_table_context_menu` 행 삭제 후 — `_row_last_path`를 현재 테이블 상태로 재동기화 (행 번호 밀림 대응).
- `_autofill_table_empty_cells` 종료부 — `_row_last_path`를 현재 테이블 상태로 재동기화 (paste/load 후 기준선 확립).

## 동작 시나리오

| 시나리오 | 기존 | 변경 후 |
|---------|------|--------|
| 빈 행에 새 경로 입력 | 🔍 버튼 수동 | cellChanged 훅에서 자동 채우기 |
| 기존 경로 → 다른 경로 교체 | 이전 채널/용량/사이클 잔존 | auto 값 셀 클리어 + 새 경로로 재채우기 |
| 경로 삭제 (빈칸화) | 이전 auto 값 잔존 | auto 값 셀 클리어 |
| 사용자가 bold/검정으로 수정한 값 | — | 보존 |
| 프로필 분석 버튼 클릭 | Phase 0 + 바 갱신만 | 빈 셀 autofill → Phase 0 → 바 갱신 |

## 범위 밖 (향후 개선 후보)

- 단일 행 `_autofill_row(row)` 호출은 link 모드 그룹 합산 힌트를 반영하지 못함. 연결 모드에서 정확한 누적 TC 힌트가 필요하면 🔍 채우기 버튼 사용 권장.
- `_channel_meta_store` 전체 fingerprint 무효화만 존재. 경로 1개 교체 시 해당 엔트리만 선별 무효화하는 기능은 향후 개선 대상.
- 사이클 바 실시간 갱신은 포함하지 않음 — 프로필 버튼 클릭 시점에만 `_update_cycle_timeline()` 수행.
