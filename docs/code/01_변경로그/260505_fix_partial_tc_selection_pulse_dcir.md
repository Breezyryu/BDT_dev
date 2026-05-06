# 부분 TC 선택 시 sweep 그룹 내부 TC 데이터 로딩 (physical-TC 폴백)

날짜: 2026-05-05
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수:
- `_unified_pne_load_raw` (L1535 근처) — physical-TC 폴백 추가
- `_unified_filter_condition` (L2236 직후) — scope 미스매치 시 raw 보존
- `_diagnose_empty_filter` (신규) — 진단 메시지 헬퍼
- `unified_profile_core` / `_unified_process_single_cycle_from_raw` — 진단 메시지 활용

## 사용자 보고 — 그대로

```
경로: 260226_260228_05_문현규_3876mAh_PS 연속저장 DCIR
TC 입력: 5-19
프로파일 분석 → 다이얼로그:
  M01Ch024[024] — 데이터 없음
  M01Ch025[025] — 데이터 없음
[19:42:57]   [unified] folders=1, tasks=2, cycles=15, workers=2
[19:42:57] ◀ WindowClass._load_all_unified_parallel 완료  [0.005s]
```

5ms 만에 완료된 로드 + "데이터 없음" → raw 자체가 안 들어옴.

## 근본 원인 — sweep cycle_map 의 'all' 그룹과 사용자 TC 입력의 의미 불일치

### 문제 시험 (PULSE_DCIR) 의 cycle_map 구조

`260226_..._PS 연속저장 DCIR` 은 sch 파싱으로 PULSE_DCIR 확정 (sweep_mode=True). `_pne_build_sweep_cycle_map` 가 다음과 같이 cycle_map 을 만든다:

| ln | 'all' | 분류 |
|----|-------|------|
| 1 | (1, 1) | 방전(초기) |
| 2 | (2, 2) | RPT |
| 3 | (3, 19) | 방전(SOC세팅) + 충전(세팅) + DCIR×15 모두 묶음 |

→ `cycle_map.keys() = {1, 2, 3}`. TC4-19 는 **모두 cycle_map[3]['all']=(3,19) 의 내부 TC**.

### `_unified_pne_load_raw` 의 기존 로직

```python
for logical_cyc in range(cycle_start, cycle_end + 1):
    if logical_cyc not in cycle_map:
        continue       # ← key 가 없으면 무조건 skip
    entry = cycle_map[logical_cyc]
    ...
```

사용자가 `TC=5-19` 입력 → `cycle_start=5, cycle_end=19` → `range(5, 20)` 모두 cycle_map keys 에 없음 → 전부 skip → `totl_cycles_set` 빈 집합 → `return None`.

`unified_profile_core` 가 `raw is None` 을 받고 `error="데이터 없음"` 반환. 사용자 다이얼로그에 그대로 표시.

전체 구간 (1-19) 으로 돌리면 logical_cyc=3 가 매칭되어 `cycle_map[3]['all']=(3,19)` 이 펼쳐지고 TC3-19 로드되어 "잘 출력" 으로 보였던 것.

## 변경 — physical-TC 폴백

`_unified_pne_load_raw` 에 cycle_map['all'] 의 모든 TC 를 펼친 역인덱스 (`physical_TC → logical_cyc`) 를 두고, key 매칭 실패 시 폴백 동작:

```python
# 부분 TC 선택 지원 (260505 fix): sweep 시험 (PULSE_DCIR 등) 의 cycle_map 은
# 다수 TC 를 하나의 논리사이클로 묶음 (cycle_map[ln]['all']=(start,end)).
# 사용자가 그 그룹 안의 개별 TC (예: TC=5-19) 를 입력하면 logical_cyc 5..19
# 가 cycle_map keys 에 없어서 모두 skip → totl_cycles 빈 집합 → "데이터 없음".
# 이를 막기 위해 cycle_map 의 'all' 범위들을 펼쳐 physical-TC → logical-cyc
# 역인덱스를 만들어 두고, key 가 없는 input 은 physical TC 로 해석한다.
_tc_to_logical: dict[int, int] = {}
for _lc, _entry in cycle_map.items():
    if isinstance(_entry, dict) and 'all' in _entry:
        _s, _e = _entry['all']
        for _tc in range(int(_s), int(_e) + 1):
            if _tc not in _tc_to_logical:
                _tc_to_logical[_tc] = _lc

for logical_cyc in range(cycle_start, cycle_end + 1):
    if logical_cyc in cycle_map:
        # 표준 경로: logical_cyc 를 그대로 사용
        entry = cycle_map[logical_cyc]
        tc_list = _cm_tc_list(entry, 'cycle')
        if not tc_list:
            tc_list = _cm_tc_list(entry, 'all')
        for tc in tc_list:
            totl_cycles_set.add(tc)
            logical_to_totl[tc] = logical_cyc
    elif logical_cyc in _tc_to_logical:
        # 폴백: 사용자가 sweep 그룹 내부의 physical TC 를 직접 선택한 경우.
        # 해당 TC 만 단독으로 로드 (identity 매핑) → 사용자가 입력한 TC 가
        # 별도 탭으로 그려진다. 기존 sweep 키 입력 (예: TC=3) 은 영향 없음.
        totl_cycles_set.add(logical_cyc)
        logical_to_totl[logical_cyc] = logical_cyc  # identity
    # else: cycle_map 어디에도 없는 TC → skip (예: max_tc 초과)
```

## 검증 시뮬레이션

`cycle_map = {1: {'all':(1,1)}, 2: {'all':(2,2)}, 3: {'all':(3,19)}}` 기준:

| 사용자 입력 | Before fix | After fix |
|-------------|------------|-----------|
| TC=5-19 | `totl_cycles=[]` → "데이터 없음" | `totl_cycles=[5..19]`, identity 매핑 → 15 TCs 정상 로드 |
| TC=3 (sweep key) | `totl_cycles=[3..19]`, all → logical 3 | 동일 (sweep semantics 보존) |
| TC=3, 7 (혼합) | TC=7 skip | TC=3 → sweep 그룹 (cycle=3), TC=4-7 identity, TC=8-19 cycle=3 |

## 다른 시험에서도 동작

- General mode (each TC = own logical): cycle_map keys = {1, 2, ...n}, each `'all':(t,t)` 단일. 폴백 분기 진입하지 않음 → 영향 없음.
- Sweep mode 의 일반 cycle (chg/dchg pair): cycle_map[ln]['all']=(s,s) 또는 (s,e) 형태. 사용자가 ln key 입력 시 표준 경로, 그룹 내부 TC 입력 시 폴백.
- max_tc 초과 입력: `_tc_to_logical` 에도 없으므로 skip (기존 동작 유지).

## 함께 들어간 보강 (별 챕터에서 이미 적용)

### `_unified_filter_condition` raw fallback (L2236 직후)

scope 필터로 모두 drop 되더라도 raw 에 활성/휴지 데이터가 있으면 보존:

```python
if filtered.empty and len(df) > 0:
    if df["Condition"].isin([1, 2, 3]).any():
        filtered = df[df["Condition"].isin([1, 2, 3])].copy()
        _perf_logger.info(...)
```

→ 사용자가 명시한 TC 가 휴지/단방향 only 여도 raw 가 있는 한 그래프가 그려진다.

### `_diagnose_empty_filter` 헬퍼 (신규)

raw 자체가 없는 edge case 에서 한 줄 "필터 후 데이터 없음" 대신:

| raw 내용 | scope | 메시지 |
|----------|-------|--------|
| 충전+휴지 | discharge | `방전 스텝 없음 (충전 + 휴지만 존재) — '사이클' 스코프 권장` |
| 휴지만 | cycle, rest off | `휴지 스텝만 존재 — '휴지 포함' 옵션 ON 필요` |

## 검증 절차 (사용자)

1. 앱 재시작
2. `260226_260228_05_문현규_3876mAh_PS 연속저장 DCIR` 경로 입력
3. TC=`5-19`, 사이클 스코프 + 시간 축 + 이어서 (continuous)
4. 프로파일 분석 → **15개 TC 모두 정상 로드 + 한 탭에 연속 timeseries 그려짐**
5. (옵션) "분리" 모드로 바꾸면 TC 별 별도 탭

## 호환성

- 정상 케이스 (cycle_map key 매칭): 폴백 분기 진입 안 함 → 영향 없음.
- General mode 시험: 모든 TC 가 cycle_map key → 영향 없음.
- max_tc 초과 입력: `_tc_to_logical` 에도 없음 → skip (기존과 동일).
- 동일 TC 가 동시에 cycle_map key + 다른 cycle_map['all'] 내부에 들어 있는 경우: 직접 매칭이 우선 (반복 처음에 처리), 폴백은 미진입.

## 적용 파일

- `C:\Users\Ryu\battery\python\BDT_dev\DataTool_dev_code\DataTool_optRCD_proto_.py` (main, 사용자 테스트 환경)
- `C:\Users\Ryu\battery\python\BDT_dev\.claude\worktrees\stoic-agnesi-bd7997\DataTool_dev_code\DataTool_optRCD_proto_.py` (worktree)
