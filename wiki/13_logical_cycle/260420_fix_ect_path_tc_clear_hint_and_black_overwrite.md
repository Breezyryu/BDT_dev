# ECT path TC 값 삭제 시 힌트 값·색 복원 이중 버그 수정

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수: `_restore_cycle_hint()` (L22607), `_on_cycle_cell_changed()` (L22627)

## 배경 / 문제

사용자 보고:
> "ECT path 사용 활성화 후 TC 값 입력 → TC 값 삭제 시, 회색폰트로 기존 TC 전체 구간이 아닌 검은색 폰트로 논리사이클 구간이 출력된다."

기대 동작: TC 값 삭제 시 `1-{max_TC}` 가 **회색** 폰트로 복원
실제 동작: `1-{max_논리사이클}` 이 **검정** 폰트로 남음

두 가지 버그가 동시에 발생한다.

## 원인

### 버그 1 — 값: `_restore_cycle_hint` 가 논리사이클 사용 [L22607-22625]

`_get_row_max_cycle_info()` 는 `max_cycle` (논리사이클 최대) 과 `max_raw` (TotlCycle 최대) 두 값을 모두 반환하지만, `_restore_cycle_hint` 가 TC 컬럼(col 4) 힌트를 찍을 때 `max_cycle` 을 사용.

```python
# Before
item4.setText(f"1-{info['max_cycle']}")
item4.setToolTip(f"최대 TC: {info['max_cycle']}")  # 라벨은 TC, 값은 논리
```

General 모드(`1 논리 = 1 TC`)에서는 두 값이 일치해 증상이 가려지지만, **Sweep 모드(GITT/DCIR, 1 논리 = 수십~수백 TC)** 에서는 `max_cycle << max_raw` 이므로 TC 힌트 자리에 훨씬 작은 논리사이클 값이 나타난다. col 4 의 설계 의도(TC 단위)와 불일치.

### 버그 2 — 색: stepnum·바 선택이 남아 검정색 덮어쓰기 유발 [L22627-22643]

`_on_cycle_cell_changed` 가 col 4 변경을 감지하면 동기화 블록에서 stepnum·사이클 바와 값을 맞추는데, **삭제(`text == ''`) 시에는 `if text:` 가드에 막혀 stepnum·바에 이전 "50" 등이 그대로 잔존**.

```python
if text:
    self._timeline_syncing = True
    self._set_bar_selection_for_row(bar_row, text)
    self.stepnum.setPlainText(text)
    self._timeline_syncing = False
# else 없음 → stepnum·바에 이전 선택 유지
```

이후 stepnum / 바 관련 이벤트가 `_write_cycle_to_table()` (L23713) 을 호출하면 **항상 검정색**:

```python
# _write_cycle_to_table 내부
item.setText(text)
item.setForeground(QtGui.QColor(0, 0, 0))  # 무조건 검정
```

결과적으로 `_restore_cycle_hint` 가 회색으로 그려놓은 "1-50" 이 다시 검정으로 덮여 씌워진다.

## 수정

### 1. `_restore_cycle_hint` — `max_raw` 사용 (L22607-22625)

```python
# After
max_tc = info['max_raw']  # col 4 = TC 컬럼 → TC 최대값
...
item4.setText(f"1-{max_tc}")
item4.setToolTip(f"최대 TC: {max_tc}")
```

`max_raw` 가 없으면 `_get_row_max_cycle_info` 가 내부에서 `str(max_cyc)` 로 폴백하므로 None 위험 없음.

### 2. `_on_cycle_cell_changed` — 삭제 시 stepnum·바 선택 해제 (L22627-22650)

```python
# After
if text:
    # 기존 동기화
    ...
else:
    # 셀 비움 → stepnum·바 선택도 함께 해제
    self._timeline_syncing = True
    self._set_bar_selection_for_row(bar_row, '')
    self.stepnum.setPlainText('')
    self._timeline_syncing = False
```

`_set_bar_selection_for_row('')` 는 빈 문자열을 파싱해 `sels = []` 를 만들고 `_row_selections[bar_row] = []` 로 선택을 완전히 비운다. 후속 이벤트에서 `_write_cycle_to_table` 가 덮어쓸 텍스트 자체가 사라져 검정 회귀를 차단.

## 동작 변화

### General 모드 (수명시험 등)

| 단계 | Before | After |
|---|---|---|
| TC 삭제 후 힌트 값 | `1-{max_cycle}` (== `max_raw`, 동일) | `1-{max_raw}` (동일) |
| TC 삭제 후 힌트 색 | 회색 유지되지만 stepnum/바에 잔존값이 있으면 검정 회귀 가능 | **회색 안정** |

### Sweep 모드 (GITT / DCIR 등)

| 단계 | Before | After |
|---|---|---|
| TC 삭제 후 힌트 값 | `1-{max_cycle}` (논리, 값이 너무 작음) | `1-{max_raw}` (TC, 정확) |
| TC 삭제 후 힌트 색 | 검정으로 덮임 | 회색 유지 |

## 영향 범위

- `_restore_cycle_hint()` — max TC 출처 변경 (1 토큰)
- `_on_cycle_cell_changed()` — else 분기 추가 (7줄)
- 기타 로직 미변경
- 회귀 위험:
  - General 모드에서 `max_cycle == max_raw` 이므로 시각 차이 없음
  - TC 삭제 후 stepnum/바가 선택 해제되는 것은 기대 동작과 일치 (TC 값이 비었으니 바/입력창도 비어야 정합)

## 검증 포인트

- [ ] (General) 수명시험 경로 + ECT path 체크, col 4 에 `50` 입력 후 삭제 → 회색 `1-{max_TC}` 로 복원, stepnum 비워짐, 바 선택 해제
- [ ] (Sweep) GITT/DCIR 경로 + ECT path 체크, col 4 에 `50` 입력 후 삭제 → 회색 `1-{max_raw_TC}` 로 복원 (값이 논리사이클이 아닌 실제 TC)
- [ ] col 4 툴팁이 "최대 TC: {max_raw}" 로 라벨·값 일치
- [ ] col 4 삭제 후 프로파일 분석 실행 시 `chg_dchg_dcir_no` 가 비어 ECT 루프 자연 스킵 (기존과 동일)
- [ ] 사용자 입력 (검정) → 삭제 → 재입력 왕복에서 색상 혼동 없음

## 관련 변경로그

- `260420_fix_ect_path_tc_autofill_roundtrip.md` — ECT path 저장·로드 시 회색 힌트 보존 (이번 수정과 별개의 왕복 이슈)
- `260420_fix_ect_path_profile_always_override.md` — ECT 체크 시 프로파일 분석 항상 ECT 위임
