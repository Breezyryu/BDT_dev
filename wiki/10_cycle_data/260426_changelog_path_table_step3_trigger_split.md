---
title: "경로 테이블 Step 3 — 자동 채우기 트리거 light/full 분리"
date: 2026-04-26
tags: [changelog, cycle-data, performance, ux, path-table]
related:
  - "[[260426_changelog_path_table_step1_cache_patch|Step 1 캐시 패치]]"
  - "[[260426_changelog_path_table_step2_light_meta|Step 2 light meta 분리]]"
  - "[[../31_software_dev/260426_study_lru_cache_principles|lru_cache 원리]]"
---

# 경로 테이블 Step 3 — 자동 채우기 트리거 light/full 분리

> **PR #3 / 6** — 사용자 요청 3·4번을 충족하는 핵심 UX 변경.
> paste/drop/load/cellChanged 직후에는 IO 없는 light 만, confirm 시점에는 full 자동.

## 배경

Step 1 (캐시 패치) 와 Step 2 (`_resolve_path_meta_light` 함수 추가) 위에서, 이번 PR 은 **호출자에게 mode 선택권** 을 부여한다.

사용자 요청:
- 3번: "경로 입력 시, **경로명과 용량값만 읽어오도록** 변경"
- 4번: "**채우기 기능 사용 시**, 채널 및 TC 정보 로드"

→ "경로 입력" 액션과 "분석 시작" 액션을 명확히 분리. 입력 시점엔 IO 0, 분석 시점에 한 번에 IO.

## 변경 사항

### 1) `_autofill_row(row, *, link_info=None, mode='full')` (L22329)

```python
def _autofill_row(self, row: int, *, link_info: dict | None = None,
                  mode: str = 'full') -> None:
    """단일 행의 빈 셀을 경로 기반 메타데이터로 자동 채우기.
    ...
    mode : str
        'light': IO 없는 경량 채우기 (col0 시험명·col3 용량만, IO 0).
                 col2 채널·col4 TC 은 비워둠 (confirm 시점에 full 채워짐).
        'full' (기본): 기존 동작. scandir + cycle_map 으로 모든 컬럼 채움.
    """
    ...
    if mode == 'light':
        meta = self._resolve_path_meta_light(path)
    else:
        meta = self._resolve_path_meta(path)
    ...
```

light 모드에서는 `_resolve_path_meta_light` 가 `meta['ch']=''`, `meta['cycle']=''` 를 반환 → 기존 cols 처리 로직이 빈 값을 자동으로 skip → col 2/4 변경 없음 (추가 분기 코드 불필요).

### 2) `_autofill_table_empty_cells(*, mode='full')` (L22453)

```python
def _autofill_table_empty_cells(self, *, mode: str = 'full'):
    """전체 테이블 자동 채우기 — _autofill_row 기반.
    ...
    mode : str
        'full' (기본): 기존 동작 — 모든 호출자 (confirm 등) 그대로.
        'light': paste·드롭·로드 직후 IO 없는 경량 채우기.
    """
    ...
    for r in range(tbl.rowCount()):
        ...
        if mode == 'light':
            meta = self._resolve_path_meta_light(path)
        else:
            meta = self._resolve_path_meta(path)
        ...
        self._autofill_row(r, mode=mode, ...)

    # 연결 모드 누적 hint 는 cycle 정보 필요 → light 에서는 skip
    if link_mode and mode == 'full':
        self._autofill_link_cumulative_hints()
```

**default = 'full'** 이 핵심. 모든 기존 호출자가 명시 mode 없이 호출하면 default 'full' → 기존 동작 그대로 → **회귀 0**.

### 3) "경로 입력" 호출자만 명시 `mode='light'`

| 호출자 | 위치 | 사용자 액션 | 이번 PR 동작 |
|---|---|---|---|
| `_on_path_cell_changed` | L22013 | 셀 직접 입력·교체 | `_autofill_row(row, mode='light')` |
| `_cycle_table_paste` | L23038 | Ctrl+V 붙여넣기 | `_autofill_table_empty_cells(mode='light')` |
| `_drop_paths_to_table` | L23981 | 파일·폴더 drag-drop | `_autofill_table_empty_cells(mode='light')` |
| `_open_table_from_path_file` | L22852 | txt/csv 경로 파일 import | `_autofill_table_empty_cells(mode='light')` |

### 4) "분석 시작" 호출자는 default 'full' (기존 동작 유지)

| 호출자 | 위치 | 사용자 액션 | 동작 |
|---|---|---|---|
| `unified_cyc_confirm_button` 진입 | L20917 | "사이클 분석" 버튼 | default='full' → 기존 동작 |
| Phase 0 직전 (사이클 분석 직전) | L24970 | (내부 호출) | default='full' → 기존 동작 |

## UX 변화 (사용자 멘탈 모델)

**Before**:
```
[paste] → 5-30초 freeze → col0~5 모두 채워짐 → confirm → 분석
```

**After**:
```
[paste] → 즉시 응답 (col0·col3 만 채워짐, col2·col4 비어있음)
       → 사용자가 col2·col4 수동 입력 가능 (또는 비워둔 채)
       → [confirm] → 비어있던 col2·col4 자동 채움 (full IO) → 분석
```

→ 사용자가 입력 단계에서 freeze 없이 자유롭게 편집. 분석 시작 시점에만 IO 비용 한 번 지불.

## 회귀 방지 — default 'full' 의 의미

이 PR 의 가장 중요한 안전장치는 **`_autofill_table_empty_cells` 와 `_autofill_row` 의 default mode 가 'full'** 이라는 점:

- Step 3 에서 명시 변경된 4개 호출자만 light
- 그 외 호출자 (confirm + 내부 호출 등) 모두 default 'full' → 기존 동작
- → **Step 3 단독 머지 시 회귀 0**
- → Step 4 에서 confirm 호출 시 statusBar 진행률만 추가하면 됨 (default 'full' 그대로)

## 검증

- [x] `python -c "ast.parse(...)"` syntax OK
- [x] `_autofill_table_empty_cells` 호출 위치 5곳 모두 점검 (4곳 default full 유지, 4곳 명시 light)
- [ ] 사용자 알파:
  - 네트워크 드라이브 경로 paste → 즉시 col0·col3 채워짐, col2·col4 비어있음 (freeze 0 확인)
  - drag-and-drop 도 동일 동작
  - 사용자가 col2·col4 수동 입력 가능
  - confirm 클릭 → 비어있던 col2·col4 자동 채워짐 (기존 IO 비용 그대로)
  - 분석 결과 정상 (회귀 0)
- [ ] perf log: `_resolve_path_meta_light` 호출 시 `os.scandir`·`pd.read_csv` 미호출 확인

## 위험·롤백

- **위험**: 중간 — UX 멘탈 모델 변화. col2/col4 가 입력 직후 비어보이는 게 사용자에게 익숙치 않을 수 있음
- **완화**:
  - confirm 시 자동 채워지므로 사용자 추가 액션 불필요
  - 변경로그를 사용자에게 사전 공유
  - 향후 placeholder 텍스트 추가 옵션 (별도 PR — Step 6 후보)
- **롤백**: 4개 명시 'light' 호출을 mode 인자 제거하면 default 'full' 로 회복 → 5분 작업

## 다음 단계

- **Step 4** (PR #4): `unified_cyc_confirm_button` 진입부에 statusBar 진행률 표시 + `QApplication.processEvents()`. **default 'full' 그대로 유지** — Step 3 와 자연스럽게 결합
- **Step 5** (PR #5): 행 삭제·col1 변경 시 `_path_meta_cache_light` 도 함께 무효화
- **Step 6** (PR #6): paste 헤더 자동 검출 + 연결처리 토글 즉시 hint
