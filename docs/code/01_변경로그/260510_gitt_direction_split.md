# GITT 방향 분기 — sequential 단방향 GITT 별도 카테고리 분기

날짜: 2026-05-10
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수/필드:
- `_merge_pulse_groups` (proto_:6732) — direction-aware merge + `_GITT_PAIR_THRESHOLD`
- `_apply_sch_categories_to_classified` (proto_:6604) — sch 덮어쓰기 시 방향 보존
- `_CLASSIFIED_COLORS` (proto_:10778) — `GITT(charge)`/`GITT(discharge)` 추가
- `CATEGORY_LABELS` (proto_:6440) — 방향별 라벨 추가
- `_HEURISTIC_CAT_NORMALIZE` (proto_:6525) — passthrough 추가
- `tools/export_all_cycle_timelines.py:_block_color` — 방향별 색조 변형

요청: 류성택 (260510, exp_data 전수 사이클 타임라인 검토 중 240821 GITT 단일 블록 식별)

## 사용자 보고

> 240821 선행랩 류성택 Gen4pGr mini-ATL-WD-Proto-422mAh-20C-450V-GITT-15도
> : GITT 방전방향, 충전방향 구분

대상 dataset의 GITT 시험은 충전방향 105 cycle + 방전방향 105 cycle (sequential 2-phase) 구조이지만 단일 `GITT(full)` 블록(TC 5-214, 210cy)으로 표시되어 phase test 성격이 시각화에 묻힘.

## 근본 원인

`_merge_pulse_groups`(proto_:6732)이 **인접 단방향 pulse 그룹**을 size 무관하게 page-merge:

```python
# Before
if (next_seg is pulse and next_seg.action != action):
    si += 1
    paired_items.extend(next_seg.items)   # 105 + 105 → 210
    # category = 'GITT' (방향 정보 소실)
```

추가로 `_apply_sch_categories_to_classified`가 schedule loop_groups의 `GITT_PULSE` 매핑(`GITT(full)`)을 **무조건 덮어씀** → `_merge_pulse_groups`에서 분기해도 무효.

## 변경 — 3개 함수 + 3개 매핑

### 1. `_merge_pulse_groups` direction-aware merge (proto_:6732)

```python
_GITT_PAIR_THRESHOLD = 3  # 인접 그룹이 둘 다 < 3 일 때만 alternating pair

can_pair = (
    next_seg is not None
    and next_seg[0] == 'pulse'
    and next_seg[2] != action
    and len(items) < _GITT_PAIR_THRESHOLD
    and len(next_seg[1]) < _GITT_PAIR_THRESHOLD
)
if can_pair:
    paired_items = items + next_seg[1]
    actions = {action, next_seg[2]}
    si += 2
else:
    paired_items = list(items)
    actions = {action}
    si += 1

# 방향 → 카테고리
if actions == {'CHG_ONLY'}:
    cat = 'GITT(charge)'
elif actions == {'DCHG_ONLY'}:
    cat = 'GITT(discharge)'
else:
    cat = 'GITT(full)'
```

**의미**:
- **alternating GITT** (각 그룹 1-2 cycle, 충/방전 교차) → `GITT(full)` (기존 동작 유지)
- **sequential phase test** (각 그룹 ≥ 3, 단방향 시퀀스) → `GITT(charge)` / `GITT(discharge)` 분기

threshold=3 의 근거: 정상 alternating GITT는 각 그룹이 1 (단일 충 + 단일 방 페어) 또는 길어도 2 (다중 시도). 3 이상이면 sequential 시험.

### 2. `_apply_sch_categories_to_classified` 방향 보존 (proto_:6604)

```python
new_cat = tc_to_new_cat.get(int(tc_target))
if new_cat:
    # 260510: GITT 방향 분기 보존
    cur_cat = entry.get('category', '')
    if (new_cat in ('GITT(full)', 'GITT')
            and cur_cat in ('GITT(charge)', 'GITT(discharge)')):
        out.append(entry)  # sch 덮어쓰기 skip, 방향 유지
        continue
    e2 = dict(entry)
    e2['category'] = new_cat
    out.append(e2)
```

`_merge_pulse_groups`가 부여한 방향 정보가 schedule loop_groups의 GITT 매핑으로 인해 유실되는 것을 방지.

### 3. 매핑 3종 추가

**`CATEGORY_LABELS`** (proto_:6440):
```python
'GITT(charge)': 'GITT 충전방향 (sequential)',
'GITT(discharge)': 'GITT 방전방향 (sequential)',
```

**`_CLASSIFIED_COLORS`** (proto_:10778):
```python
'GITT(charge)':    {'color_idx': 3, 'desc': 'GITT 충전방향 (sequential)'},
'GITT(discharge)': {'color_idx': 3, 'desc': 'GITT 방전방향 (sequential)'},
```

**`_HEURISTIC_CAT_NORMALIZE`** (proto_:6525):
```python
'GITT(charge)':    'fwd',
'GITT(discharge)': 'fwd',
```

세 매핑이 함께 정합되어야 cycle bar / pill / tooltip / 컬럼 표기 모두 일관.

### 4. export 스크립트 색조 변형 (`tools/export_all_cycle_timelines.py`)

```python
# GITT 방향별 색조 변형 (PALETTE[3] = #F39B7F 베이스)
if pattern == "GITT(charge)":
    return "#F8B89D", desc      # 더 밝은 살구
if pattern == "GITT(discharge)":
    return "#D67555", desc      # 더 어둡고 붉은 살구
```

같은 idx=3 orange 계열 내에서 명도 변형으로 시각 구분. proto_의 _CLASSIFIED_COLORS는 idx=3 단일 유지하되 export 렌더 단계에서만 분기 — 사이클 탭 본 화면에 영향 0.

## 240821 GITT 검증

```
Before:
  blocks: 1
       5- 214  GITT(full)            count=210

After:
  blocks: 2
       5- 109  GITT(charge)          count=105
     110- 214  GITT(discharge)       count=105
```

## exp_data 전수 영향 (204 datasets)

분류 결과 카운트:
- `GITT(charge)`: 19 건 (신규)
- `GITT(discharge)`: 15 건 (신규)
- `GITT(full)`: 17 건 (alternating GITT 유지)
- `GITT(simplified)`: 0
- `GITT` (legacy alias): 1

비-GITT dataset (170건+) 분류 결과 불변 — `_pulse` 마커가 없어 본 변경 코드 경로 미진입.

## 호환성

- **non-GITT**: 영향 없음 (`_pulse` 항목 없으면 새 분기 미진입)
- **alternating GITT** (각 그룹 < 3): 기존 `GITT` → `GITT(full)` (기존 alias 동등 의미, 색상 동일)
- **sequential GITT** (단방향 ≥ 3 cycle 시퀀스): `GITT` 단일 → `GITT(charge)`/`GITT(discharge)` 분기 (시각 차별)
- **schedule classifier**: GITT 방향 entry 만 sch 덮어쓰기 우회 (다른 카테고리는 종전 동작)

## 회귀

- `tools/test_code/regression_classify_pne_cycles.py --verify`:
  `[PASS] 760 entries 완전 일치` (baseline = `251028_..._Q8 ATL` 일반 수명 — GITT 없음)
- 신규 v3 HTML export: `204 datasets 처리 26.7s` (회귀 0)
- `tests/regression/test_full_sweep.py`: 904 skipped (baseline 미생성 상태 유지)

## 적용 파일

- `DataTool_dev_code/DataTool_optRCD_proto_.py` (worktree zen-volhard-e787a1)
- `tools/export_all_cycle_timelines.py` (worktree)
- 산출물: `docs/code/02_레퍼런스/260510_exp_data_cycle_timelines_v3.html`
- main 머지 후: `C:/Users/Ryu/battery/python/BDT_dev/DataTool_dev_code/DataTool_optRCD_proto_.py`

## 검증 절차 (사용자)

1. 앱 재시작 (또는 `_reset_all_caches()` 호출)
2. **240821 GITT** 폴더 입력 → 사이클 분석
3. 사이클 바: TC 5-109 충전방향 (밝은 살구) + TC 110-214 방전방향 (어두운 살구) 두 블록 확인
4. 마우스오버: `GITT 충전방향 (sequential)` / `GITT 방전방향 (sequential)` 툴팁
5. **다른 GITT dataset** (alternating, 짧은 alternating GITT pulse 시험): 단일 `GITT(full)` 블록 유지 확인 (회귀 없음)
6. **non-GITT** (수명/RPT/DCIR): 분류 변화 없음

## 향후 확장 후보

- `GITT_PAIR_THRESHOLD`를 schedule struct의 그룹 길이 통계 기반 동적 결정 (현재 fixed=3)
- `gitt_direction` 필드를 `meta.cycle_groups`까지 전파 (LogicalCycleGroup 통합)
- 색상 변형을 proto_ `_CLASSIFIED_COLORS`로 승격 (현재는 export 렌더 단계만)
