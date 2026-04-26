---
title: "버그 수정 — '🔍 채우기' 버튼이 연결처리 그룹 동작을 무시"
date: 2026-04-26
tags: [bugfix, cycle-data, link-mode, autofill]
related:
  - "[[260426_changelog_path_table_step3_trigger_split|Step 3 트리거 분리]]"
  - "[[260426_changelog_path_table_step6_paste_header_link_hint|Step 6 paste 헤더·링크 토글]]"
---

# 버그 수정 — '🔍 채우기' 버튼이 연결처리 그룹 동작을 무시

## 증상

연결처리 (`chk_link_cycle`) 체크 상태에서 **'🔍 채우기'** 버튼 (`btn_autofill_path`) 을 누르면, 그룹 첫 행뿐 아니라 **그룹 내 모든 행의 col0(시험명)** 이 채워졌다. 정상은 그룹별 한 줄만 시험명·채널·용량 표시되어야 한다 (사용자 ECT 비교 시나리오).

## 원인 — `_autofill_all_rows` 가 link_info 미전달

`_autofill_all_rows` (L22057, `btn_autofill_path` 클릭 시그널 슬롯):

```python
def _autofill_all_rows(self):
    for row in range(self.cycle_path_table.rowCount()):
        path = self._get_table_cell(row, 1)
        if path:
            self._autofill_row(row)              # ❌ link_info=None
            self._highlight_path_cell(row)
```

`_autofill_row(row)` 는 default 인자 `link_info=None` 으로 호출됨 → 함수 내부에서:

```python
link_mode = link_info is not None       # False
is_grp_first = link_info['is_first'] if link_mode else True   # True
first_meta = link_info.get('first_meta') if link_mode else None
```

→ **모든 행이 "첫 번째 행" 으로 처리** 되어 col0(시험명) 이 무조건 채워졌음.

반면 confirm 진입부의 `_autofill_table_empty_cells(mode='full')` 는 그룹 분리·link_info 빌드를 정확히 처리:

```python
first_meta = None
for r in range(...):
    path = ...
    if not path:
        first_meta = None     # 빈 행 = 그룹 구분자
        continue
    is_grp_first = (first_meta is None)
    if is_grp_first:
        first_meta = meta
    if link_mode:
        self._autofill_row(r, link_info={
            'is_first': is_grp_first, 'first_meta': first_meta},
            mode=mode)
```

→ confirm 시점에는 정상 동작했으나, **'🔍 채우기' 버튼은 별도 함수** 라 같은 로직을 거치지 않았음.

## 수정 — `_autofill_all_rows` 를 `_autofill_table_empty_cells(mode='full')` 의 thin wrapper 로

```python
def _autofill_all_rows(self):
    """버튼 트리거: 유효 경로가 있는 모든 행에 메타 자동 채우기 (full).

    `_autofill_table_empty_cells(mode='full')` 의 thin wrapper.
    - 연결처리 체크 시 그룹별 link_info 빌드 → **그룹 첫 행만** col0/col2/col3 채움
      (이전 동작은 link_info=None 호출로 모든 행 col0 채워지던 버그였음)
    - 후처리 (강조, mismatch 검사, _row_last_path 동기화) 모두 포함
    - statusBar 진행률 + processEvents 로 UI 응답 확보 (네트워크 드라이브 대응)
    """
    if not self._has_table_data():
        return
    try:
        _status = self.statusBar()
    except Exception:
        _status = None

    def _autofill_progress(done: int, total: int) -> None:
        if _status is not None and total > 0:
            _status.showMessage(f"채우기 중... ({done}/{total})")
        QtWidgets.QApplication.processEvents()

    self._autofill_table_empty_cells(
        mode='full', progress_cb=_autofill_progress)
    if _status is not None:
        _status.showMessage("완료", 2000)
```

## 효과

**Before** (연결처리 ON, 3행 동일 그룹):
```
시험명          | 경로            | 채널 | 용량  | TC      | 모드
─────────────────────────────────────────────────────────────
Q8 Main 2.0C   | C:\path\1       |  1   | 2335 | 1-300   | CYC
Q8 Main 2.0C   | C:\path\2       |  2   | 2335 | 301-600 | CYC   ← col0 중복!
Q8 Main 2.0C   | C:\path\3       |  3   | 2335 | 601-900 | CYC   ← col0 중복!
```

**After** (수정):
```
시험명          | 경로            | 채널 | 용량  | TC          | 모드
──────────────────────────────────────────────────────────────────
Q8 Main 2.0C   | C:\path\1       |  1   | 2335 | 1-900       | CYC
               | C:\path\2       |      |      |             |       ← 빈 칸
               | C:\path\3       |      |      |             |       ← 빈 칸
```

(누적 hint "1-900" 도 `_autofill_link_cumulative_hints` 가 자동 적용)

## 부수 효과 — 코드 중복 제거 + UX 통일

- **DRY**: `_autofill_all_rows` 의 단순 루프가 사라지고 `_autofill_table_empty_cells` 단일 진입점으로 통합. 두 함수가 같은 로직을 두 번 구현하던 문제 해소.
- **UX 통일**: confirm 진입부 (Step 4) 와 동일하게 statusBar 진행률 표시 + `processEvents()` 호출. "🔍 채우기" 버튼도 freeze 없이 응답.
- **후처리 보장**: `_highlight_all_paths`, `_highlight_channel_mismatch`, `_highlight_capacity_mismatch`, `_row_last_path` 동기화 모두 포함됨 (이전엔 `_highlight_path_cell` 만 호출).

## 검증

- [x] `python -c "ast.parse(...)"` syntax OK
- [ ] 연결처리 OFF + '🔍 채우기' → 모든 행 채워짐 (기존 동작)
- [ ] 연결처리 ON + '🔍 채우기' → 그룹 첫 행만 col0/col2/col3 채워짐, 후속 행 빈 칸
- [ ] 연결처리 ON + '🔍 채우기' → col4 에 누적 TC ("1-900") 가 회색 hint 로 표시
- [ ] statusBar "채우기 중... (3/5)" 진행률 표시 → "완료" 메시지

## 위험·롤백

- **위험**: 매우 낮음. wrapper 패턴으로 기능 통합 + 동작 정정
- **롤백**: 신규 본문을 이전 5줄 루프로 되돌리면 됨 (단 버그 복귀)
