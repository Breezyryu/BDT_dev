# 260404 논리사이클 Phase B — 경로 테이블 아래 논리사이클 정보 라벨

## 배경 / 목적

Phase A에서 논리사이클 매핑(cycle_map) 생성 로직을 구현했으나,
사용자가 **현재 경로에 몇 개의 논리사이클이 있는지**, **어떤 시험 유형인지** 알 방법이 없었다.

사이클 번호를 `stepnum`에 입력할 때 유효 범위를 모르면 잘못된 번호를 입력하거나,
존재하지 않는 사이클을 요청하여 에러가 발생할 수 있다.

Phase B는 경로 입력 후 자동으로 cycle_map을 빌드하여
**"ℹ 논리사이클 1~25 (PNE, 스윕 시험, 물리TC 180개)"** 형태의
정보를 경로 테이블 바로 아래에 표시한다.

---

## 변경 내용

### 1. `cycle_map_info_label` 위젯 추가 (setupUi)

`_path_groupbox` 레이아웃에서 `cycle_path_table` + 버튼 레이아웃(`horizontalLayout_119`) 바로 아래에 QLabel 추가.

```python
self.cycle_map_info_label = QtWidgets.QLabel(parent=self._path_groupbox)
self.cycle_map_info_label.setStyleSheet(
    "QLabel { color: #666666; font-size: 11px; padding: 1px 4px; }")
self.cycle_map_info_label.setWordWrap(True)
self.cycle_map_info_label.setText("")
self.cycle_map_info_label.setVisible(False)
self._path_groupbox_vlayout.addWidget(self.cycle_map_info_label)
```

- 초기 상태: 숨김 (`setVisible(False)`)
- 경로가 유효할 때만 표시
- 회색 소형 폰트로 테이블을 압도하지 않는 정보 라벨 역할

### 2. `_update_cycle_map_info()` 신규 메서드

경로 테이블의 첫 유효 경로에서 cycle_map을 빌드하여 라벨 텍스트를 갱신.

```python
def _update_cycle_map_info(self) -> None:
    # 1. 첫 유효 경로 + 용량 추출
    # 2. 첫 채널 폴더에서 cycle_map 빌드
    #    - PNE: pne_build_cycle_map()
    #    - Toyo: toyo_build_cycle_map()
    # 3. 시험 유형 판별 (tuple 값 존재 → 스윕 시험)
    # 4. 라벨 텍스트 구성:
    #    "ℹ 논리사이클 1~N  (PNE, 스윕 시험, 물리TC M개)"
    #    "ℹ 논리사이클 1~N  (Toyo, 일반 시험)"
```

**표시 정보:**

| 항목 | 예시 |
|------|------|
| 논리사이클 범위 | `1~25` |
| 사이클러 종류 | `PNE` / `Toyo` |
| 시험 유형 | `일반 시험` / `스윕 시험, 물리TC 180개` |

**툴팁 상세:**
- cycle_map 개수
- 사이클러 종류
- 시험 유형
- 경로

### 3. 트리거 연결

`_autofill_table_empty_cells()` 마지막에 `_update_cycle_map_info()` 호출 추가.

```python
# _autofill_table_empty_cells 끝부분:
self._highlight_all_paths()
self._highlight_channel_mismatch()
self._highlight_capacity_mismatch()
self._update_cycle_map_info()      # ← Phase B 추가
```

**호출 시점:**
- 경로 파일 로드 (`_load_path_file_to_table` → `_autofill_table_empty_cells`)
- 테이블 셀 직접 편집 (300ms 디바운스 타이머 → `_autofill_table_empty_cells`)
- 사이클 분석 실행 (`unified_cyc_confirm_button` → `_autofill_table_empty_cells`)

### 4. 초기화 시 라벨 숨김

`_clear_table()` 함수에 `self.cycle_map_info_label.setVisible(False)` 추가.

---

## Before / After

**Before:**
```
┌─ 1. 경로 입력 ──────────────────────────┐
│ [시험명] [경로]       [채널] [용량] [사이클] │
│ ...                                       │
└───────────────────────────────────────────┘
    (사용자는 유효 사이클 범위를 모름)
```

**After:**
```
┌─ 1. 경로 입력 ──────────────────────────┐
│ [시험명] [경로]       [채널] [용량] [사이클] │
│ ...                                       │
│ ℹ 논리사이클 1~25  (PNE, 스윕 시험, TC 180)│
└───────────────────────────────────────────┘
    (사용자가 stepnum에 1~25 범위 내에서 입력)
```

---

## 영향 범위

| 함수/위젯 | 변경 유형 |
|-----------|----------|
| `setupUi()` | `cycle_map_info_label` QLabel 추가 |
| `_update_cycle_map_info()` | **신규** — cycle_map 빌드 + 라벨 갱신 |
| `_autofill_table_empty_cells()` | 끝에 `_update_cycle_map_info()` 호출 추가 |
| `_clear_table()` | 라벨 숨김 처리 추가 |
| `ui-component-map.instructions.md` | Tab 1 위젯 트리에 라벨 추가 |

## 하위 호환성

- 라벨은 정보 표시 전용 (입력 로직에 영향 없음)
- cycle_map 빌드 실패 시 라벨이 숨겨짐 (에러 전파 없음)
- 기존 `_autofill_table_empty_cells` 동작에 추가 호출만 붙음

## Phase A 변경로그 참조

- Phase A-1: `260404_impl_logical_cycle_phase_a.md`
- Phase A-2: `260404_impl_logical_cycle_phase_a.md` (§Phase A-2, 병합됨)
