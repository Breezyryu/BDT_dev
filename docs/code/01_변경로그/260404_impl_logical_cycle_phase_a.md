# 260404 논리사이클 Phase A 구현 — 매핑 테이블 생성 및 프로필 통합

## 배경 / 목적

사이클 데이터 탭과 프로필 분석 탭의 사이클 번호 체계가 불일치하는 문제를 해결한다.

- **사이클 데이터 탭**: 이미 논리사이클 사용 (유효 방전 1회 = 1 사이클)
- **프로필 분석 탭**: 물리 파일 번호 직접 사용 → 논리사이클과 불일치

사용자가 "3번째 사이클 프로필"을 요청했을 때, 사이클 데이터 탭의 3번째 사이클과 동일한 데이터를 프로필 탭에서도 볼 수 있도록 한다.

---

## 변경 내용

### 1. `pne_build_cycle_map()` 신규 함수

PNE SaveEndData로부터 논리사이클 → TotlCycle 매핑을 생성하는 함수.

```python
def pne_build_cycle_map(raw_file_path, mincapacity, ini_crate) -> tuple[dict, float]:
    # SaveEndData의 TotlCycle별 pivot → 충방전 쌍이 모두 있는 사이클만 유효
    # 결과: {1: TotlCycle_A, 2: TotlCycle_B, ...}
```

- `_process_pne_cycleraw()`의 사이클 재정의 로직을 재현
- TotlCycle별로 `pivot_table(index="TotlCycle", columns="Condition")` 수행
- 충방전 쌍이 모두 존재하는 TotlCycle만 유효 사이클로 판정
- 논리사이클 번호(1,2,3…) → TotlCycle 값의 매핑 반환

**위치**: `toyo_build_cycle_map()` 바로 뒤 (기존 함수와 동일 섹션)

### 2. `_unified_toyo_load_raw()` — cycle_map 파라미터 추가

**Before:**
```python
def _unified_toyo_load_raw(raw_file_path, cycle_start, cycle_end):
    for cyc in range(cycle_start, cycle_end + 1):
        fpath = os.path.join(raw_file_path, "%06d" % cyc)  # 물리파일 직접 접근
```

**After:**
```python
def _unified_toyo_load_raw(raw_file_path, cycle_start, cycle_end, cycle_map=None):
    if cycle_map:
        # 논리사이클 → 물리파일 변환
        for logical_cyc in range(cycle_start, cycle_end + 1):
            first_file, last_file = cycle_map[logical_cyc]
            for phys_cyc in range(first_file, last_file + 1):
                # 물리파일 로드, Cycle=논리사이클 번호, PhysicalCycle=물리번호 보존
    else:
        # 기존 동작 (하위 호환성)
```

- cycle_map 사용 시 동일 논리사이클에 속하는 여러 물리파일을 같은 Cycle 번호로 태깅
- `PhysicalCycle` 컬럼으로 원본 파일 번호 보존
- cycle_map이 None이면 기존 동작과 완전 동일 (하위 호환)

### 3. `_unified_pne_load_raw()` — cycle_map 파라미터 추가

**Before:**
```python
def _unified_pne_load_raw(raw_file_path, cycle_start, cycle_end):
    # TotlCycle 값으로 직접 필터
    raw = raw.loc[(raw[27] >= cycle_start) & (raw[27] <= cycle_end)]
```

**After:**
```python
def _unified_pne_load_raw(raw_file_path, cycle_start, cycle_end, cycle_map=None):
    if cycle_map:
        # 논리사이클 → TotlCycle 변환
        totl_cycles = [cycle_map[lc] for lc in range(cycle_start, cycle_end+1) if lc in cycle_map]
        raw = raw.loc[raw[27].isin(totl_cycles)]
        # Cycle 컬럼을 논리사이클 번호로 교체, PhysicalCycle로 원본 보존
```

- cycle_map의 TotlCycle 값으로 정확히 필터링 (범위 대신 isin)
- `PhysicalCycle` 컬럼으로 원본 TotlCycle 보존
- 매핑에 없는 행 자동 제거

### 4. `unified_profile_core()` — cycle_map 자동 생성

```python
def unified_profile_core(..., cycle_map=None):
    # cycle_map이 None이면 자동 생성
    if cycle_map is None:
        if is_pne:
            cycle_map, _ = pne_build_cycle_map(...)
        else:
            cycle_map, _ = toyo_build_cycle_map(...)
    # 로딩 함수에 cycle_map 전달
    raw = _unified_toyo_load_raw(..., cycle_map=cycle_map)
```

- `cycle_map=None` → 자동으로 `toyo_build_cycle_map()` 또는 `pne_build_cycle_map()` 호출
- metadata에 `cycle_map` 포함하여 반환 (UI에서 매핑 확인 가능)

### 5. `unified_profile_batch()` — cycle_map 1회 생성 후 재사용

```python
def unified_profile_batch(..., cycle_map=None):
    # cycle_map 1회 생성
    if cycle_map is None:
        cycle_map = build_map(...)
    # 각 사이클 처리 시 cycle_map 전달
    for cyc in cycle_list:
        result = unified_profile_core(..., cycle_map=cycle_map)
```

- 배치 로딩에서 cycle_map을 1회만 생성 (성능 최적화)
- PNE 1회 I/O 최적화 유지: `_unified_pne_load_raw()`에도 cycle_map 전달

### 6. `unified_profile_batch_continue()` — cycle_map 전달

Continue 모드에도 동일하게 cycle_map 자동 생성 및 전달 적용.

---

## 영향 범위

| 함수 | 변경 유형 |
|------|----------|
| `pne_build_cycle_map()` | 신규 추가 |
| `_unified_pne_load_raw()` | 시그니처 + 내부 로직 변경 |
| `_unified_toyo_load_raw()` | 시그니처 + 내부 로직 변경 |
| `unified_profile_core()` | 시그니처 + Stage 1 로직 변경 |
| `unified_profile_batch()` | 시그니처 + cycle_map 생성 로직 추가 |
| `unified_profile_batch_continue()` | 시그니처 + cycle_map 생성 로직 추가 |
| `toyo_build_cycle_map()` | 변경 없음 (기존 함수 그대로 활용) |
| `toyo_cycle_data()` | 변경 없음 |
| `pne_cycle_data()` | 변경 없음 |
| `graph_output_cycle()` | 변경 없음 |

## 하위 호환성

- 모든 변경은 `cycle_map=None` 기본값으로 기존 동작과 완전 호환
- cycle_map이 없거나 빈 dict이면 물리 번호 직접 사용 (기존 동작)
- 일반 수명 시험(1물리=1논리)에서는 매핑이 항등이므로 성능 영향 없음
