# 연결처리 모드 — 사이클 바 행 선택이 잘못된 테이블 행에 기록되는 버그 수정

날짜: 2026-05-10
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
요청: 류성택 (260510 BDT 사용 중 발견)

대상 식별자:
- `_write_cycle_to_table` (L28543 부근) — link_mode 분기 추가
- `_on_stepnum_text_changed` (L28021 부근) — `bar_row=cycle_timeline._active_row` 명시 전달

## 사용자 보고 — 그대로

> 2번째 연결 그룹 사이클 선택 시, 경로 테이블 사이클에 `103-601`로
> 처리되는 문제.
>
> (캡처: 1번 박스 — 첫 시험명 그룹 [801-900 / 901-1000 / 1-1000_32, 8 폴더],
> 두 번째 시험명 그룹 [Ah_T23_1 / _T23_2 / _T23_3]. 사이클 바 2 행. 두 번째
> 그룹 첫 행 col4 에 `103-601` 이 들어가 있고, 첫 그룹 col4 는 비어 있음.)

## 근본 원인 — bar_row 의 의미가 두 함수에서 어긋남

### `_update_cycle_timeline` (L28572 ~)

연결처리 모드일 때 그룹 단위로 블록을 합산해 사이클 바 1 행씩 구성.
**사이클 바의 row 인덱스 = 그룹 인덱스.**

```python
# L28630 부근
if link_mode and len(rows) > 1:
    row_groups = self._get_table_row_groups()
    merged_rows = []
    for grp in row_groups:
        ...
        merged_rows.append((grp_label, grp_blocks))
    rows = merged_rows
self.cycle_timeline.set_multi_blocks(rows)   # row idx = group idx
```

### `_handle_link_cycle_table` (L27380 ~)

연결처리 모드일 때 col4 의 `1-cumul_tc` 힌트를 **그룹 첫 행에만** 기록.

```python
# L27431
if link_mode and len(grp_rows) > 1:
    cumul_tc = sum(row_info[r]['cycle'] for r in grp_rows ...)
    for idx, r in enumerate(grp_rows):
        if idx == 0:
            txt4 = f"1-{cumul_tc}"   # 그룹 첫 행에만
        else:
            item4.setText('')         # 나머지는 빈칸
```

### `_write_cycle_to_table` (구) — link_mode 무시

```python
data_row_idx = 0
for r in range(tbl.rowCount()):
    if not self._get_table_cell(r, 1):
        continue
    if data_row_idx == bar_row:
        item.setText(text)
        return
    data_row_idx += 1
```

→ 사이클 바의 row 인덱스(= 그룹 인덱스)를 **빈 행 제외 데이터 행 카운터**로
재해석. 그룹당 path 가 N 개면 그룹 인덱스 g 의 사이클 텍스트가 정작 데이터
행 인덱스 g 의 행에 떨어지므로:

| 사이클 바 행 (= 그룹 idx) | 의도 (그룹 첫 행) | 실제 (데이터 행 idx) |
|---|---|---|
| 0 (첫 그룹) | row 0 (= 801-900) | row 0 (= 801-900) ✓ 우연 일치 |
| 1 (둘째 그룹) | row 4 (= T23_1) | row 1 (= 901-1000) ✗ |
| ... | ... | ... |

캡처에서 `103-601` 이 두 번째 그룹 첫 행(T23_1)에 있고 첫 그룹 col4 가
비어 있는 것은, 사용자가 두 번째 그룹 사이클 바 클릭 → 두 번째 그룹의
의도 행(T23_1) 에 다행히 기록되어야 했지만, 추가로 첫 그룹의 데이터 행에도
이전 잘못된 매핑이 누적되며 link 토글 후 `1-cumul_tc` 힌트 갱신으로 첫
그룹 col4 가 다시 빈칸이 된 상태로 보임. 어느 경로든 **두 함수의 행 의미
불일치**가 근본 원인.

## 변경 내용

### 1. `_write_cycle_to_table` — link_mode 분기 추가

```python
def _write_cycle_to_table(self, text, col=4, bar_row=0):
    link_mode = self.chk_link_cycle.isChecked()

    # 그룹별 데이터 행 인덱스 (빈 행 = 구분자)
    groups: list[list[int]] = []
    current = []
    for r in range(tbl.rowCount()):
        if self._get_table_cell(r, 1):
            current.append(r)
        else:
            if current:
                groups.append(current); current = []
    if current:
        groups.append(current)

    if link_mode:
        # bar_row = 그룹 인덱스 → 그룹 첫 행에만 기록, 나머지는 빈칸
        if not (0 <= bar_row < len(groups)): return
        grp = groups[bar_row]
        if not grp: return
        _set_text(grp[0])
        for r in grp[1:]:
            item = tbl.item(r, col)
            if item is not None:
                item.setText(''); item.setToolTip('')
    else:
        # bar_row = 데이터 행 인덱스 (기존 동작 호환)
        data_row_idx = 0
        for grp in groups:
            for r in grp:
                if data_row_idx == bar_row:
                    _set_text(r); return
                data_row_idx += 1
```

→ `_handle_link_cycle_table` 의 "그룹 첫 행에만 힌트, 나머지 빈칸" 정책과
정확히 일치.

### 2. `_on_stepnum_text_changed` — 활성 행 전달

stepnum 텍스트 편집은 **사이클 바 활성 행**의 선택을 표현하므로, 이를
`bar_row` 로 명시 전달. (이전엔 default `bar_row=0` 으로 무조건 첫 그룹/첫
데이터 행에 기록되던 잠복 버그.)

```python
self._write_cycle_to_table(
    text, col=4, bar_row=self.cycle_timeline._active_row)
```

## 회귀 영향

- **비연결 모드** (link unchecked): 기존 데이터 행 카운터 매핑 그대로 — 회귀 없음.
- **단일 path 그룹**: link 모드라도 그룹 행이 1개라 `_set_text(grp[0])` 가 그 행에 그대로 기록 — 동일 결과.
- **bar_row 범위 초과**: `if not (0 <= bar_row < len(groups)): return` 로 silent skip (예외 X, 사용자 경험 안전).
- `_handle_link_cycle_table` 의 toggle 시 그룹 첫 행 `1-cumul_tc` 힌트는 `_write_cycle_to_table` 와 같은 행을 갱신하므로 시각적 충돌 없음.

## 검증

- `python -m py_compile DataTool_dev_code/DataTool_optRCD_proto_.py` → OK
- 수동 시각 확인 항목:
  - [ ] 연결처리 ON, 그룹 2개 이상 — 두 번째 그룹 사이클 바 클릭 시 두
        번째 그룹 **첫 행** col4 에만 텍스트 기록, 나머지 빈칸
  - [ ] 첫 번째 그룹은 여전히 첫 그룹 첫 행에 기록
  - [ ] 비연결 모드 — 기존처럼 path 가 있는 N 번째 데이터 행에 기록
  - [ ] stepnum 직접 편집 → 활성 그룹의 첫 행에 반영 (이전엔 항상 첫 그룹 첫 행)
  - [ ] 토글 (연결 ON ↔ OFF) 시 col4 표시 일관성

## 관련

- 260509 [link_toyo_tc_fallback](260509_link_toyo_tc_fallback.md) — 연결 모드 max_tc 산출 정정
- 260510 [cycle_timeline_per_row_ticks_and_stretch](260510_cycle_timeline_per_row_ticks_and_stretch.md) — 행별 눈금 분리 + 박스 stretch
