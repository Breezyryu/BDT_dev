# 260404 — 통합 배치 로더 아키텍처 리뷰

## 대상 함수 / 위치

| 함수 | 파일 | 라인 |
|------|------|------|
| `_unified_process_single_cycle_from_raw()` | `proto_.py` | 1331~ |
| `unified_profile_batch()` | `proto_.py` | 1452~ |
| `unified_profile_batch_continue()` | `proto_.py` | 1579~ |
| `_load_unified_batch_task()` | `proto_.py` | 14101~ |
| `_load_all_unified_parallel()` | `proto_.py` | 14138~ |

---

## 1. 전체 호출 구조

```
UI 버튼 (Phase 4)
  │
  ▼
_load_all_unified_parallel()          ← 최상위 병렬 오케스트레이터
  │  ThreadPoolExecutor
  ├──→ _load_unified_batch_task()     ← 채널 1개 담당 워커
  │      │
  │      ├── continuity=="continuous"?
  │      │   YES → unified_profile_batch_continue()
  │      │           └── unified_profile_core() × step_ranges
  │      │
  │      └── NO (overlay)
  │          └── unified_profile_batch()
  │                │
  │                ├── is_pne?
  │                │   YES → _unified_pne_load_raw() 1회
  │                │         └── _unified_process_single_cycle_from_raw() × cycle_list
  │                │              └── Stage 2~6 파이프라인
  │                │
  │                └── NO (Toyo)
  │                    └── unified_profile_core() × cycle_list
  │                         └── Stage 1~6 파이프라인 (개별 I/O)
  │
  ▼
results dict → 렌더러 (_profile_render_loop)
```

### 왜 이렇게 분기하는가?

**PNE vs Toyo의 I/O 패턴 차이** 때문이다.

| | PNE | Toyo |
|--|-----|------|
| 파일 구조 | SaveData 파일 수개에 모든 사이클 압축 | 사이클별 개별 파일 (000001, 000002...) |
| 최적 로딩 | 파일 1회 읽고 메모리에서 사이클 분배 | 사이클별 파일 읽기 (일괄 불가) |
| I/O 병목 | 대용량 CSV 파싱 | 파일 열기/닫기 반복 |

PNE에서 `_unified_pne_load_raw(min_cycle, max_cycle)`을 1회 호출하면, SaveData 파일을 한 번만 파싱하고 전체 원시 데이터를 메모리에 올린다. 이후 `all_raw[all_raw["Cycle"] == cyc]`로 사이클별 슬라이싱하면 디스크 I/O 없이 처리 가능하다.

Toyo는 사이클별 파일이므로 일괄 로드 이점이 없어 `unified_profile_core()`를 직접 루프 호출한다.

---

## 2. `_unified_process_single_cycle_from_raw()` 상세

```python
# 입력: 이미 로드된 원시 데이터의 특정 사이클 슬라이스
raw_cycle = all_raw[all_raw["Cycle"] == cyc].copy()

# Stage 1: 생략 (이미 로드됨)
# Stage 2: Condition 필터링
filtered = _unified_filter_condition(raw_cycle, data_scope, include_rest)
# Stage 3: 정규화 (PNE: μV→V, μA→mA / Toyo: 시간적분 용량 계산)
normalized = _unified_normalize_pne(filtered, mincapacity, raw_file_path)
# Stage 4: 스텝 병합 (멀티스텝 CC→CV 시간·용량 연속)
merged = _unified_merge_steps(normalized, data_scope)
# Stage 5: X축(Time/SOC) 및 overlay/continuous 처리
with_axis = _unified_calculate_axis(merged, axis_mode, data_scope, continuity)
# Stage 6: dQ/dV 계산 (선택)
if calc_dqdv:
    with_axis = _unified_calculate_dqdv(with_axis, smooth_degree)
```

### 왜 Stage 1만 분리했는가?

Stage 1(원시 로딩)이 I/O 바운드이고, Stage 2~6은 CPU 바운드(DataFrame 조작)이기 때문이다.
PNE 배치에서는 Stage 1을 1회만 실행하고, 나머지는 사이클별로 반복 실행하는 것이 최적.

---

## 3. `unified_profile_batch()` 옵션 라우팅

```python
# 기존: profile_type + is_pne로 10개 함수 중 1개 선택
if profile_type == 'chg':
    if is_pne:
        pne_chg_Profile_batch(...)
    else:
        toyo_chg_Profile_batch(...)

# 통합: options dict 하나로 모든 모드 커버
unified_profile_batch(
    ...,
    data_scope="charge",    # step/rate/chg → charge
    axis_mode="soc",        # chg/dchg → soc, step/rate → time
    calc_dqdv=True,         # chg/dchg → True
    cutoff=0.05,            # 전류/전압 컷오프
)
```

### 옵션 → 기존 함수 매핑표

| data_scope | axis_mode | calc_dqdv | 기존 함수 |
|-----------|-----------|-----------|----------|
| charge | time | False | step/rate |
| charge | soc | True | chg |
| discharge | soc | True | dchg |
| cycle | time | False | continue (overlay) |

---

## 4. 병렬 로더 `_load_all_unified_parallel()` 구조

```python
# 1단계: 태스크 수집
for cyclefolder in all_data_folder:          # 폴더 순회
    for folder_path in subfolder:             # 채널 순회
        tasks.append((folder_path, cycle_list, mincapacity, inirate, options, i, j))

# 2단계: ThreadPoolExecutor로 병렬 실행
with ThreadPoolExecutor(max_workers=N) as executor:
    futures = {executor.submit(_load_unified_batch_task, task): task ...}
    for future in as_completed(futures):
        # 결과 수집 + 프로그레스바 업데이트

# 3단계: 결과 dict 반환
# {(folder_idx, subfolder_idx, cycle_key): [mincapacity, UnifiedProfileResult]}
```

### 기존 대비 차이점

| | 기존 | 통합 |
|--|------|------|
| 태스크 함수 | `_load_step_batch_task` + `_load_profile_batch_task` | `_load_unified_batch_task` 1개 |
| 분기 기준 | `profile_type` 문자열 + `is_pne` bool | `options` dict (4개 옵션) |
| `is_pne` 판별 | 태스크 생성 시 전달 | 배치 함수 내부에서 자동 판별 |
| 결과 형식 | `[mincapacity, df]` | `[mincapacity, UnifiedProfileResult]` |

기존에는 `is_pne`를 상위 로더에서 판별해서 태스크에 전달했지만, 통합 버전에서는 `unified_profile_batch()` 내부에서 `check_cycler()`를 호출한다. 이는 채널별로 사이클러 타입이 다를 수 있는 경우에도 정확히 작동한다.

---

## 5. Continue 모드가 분리된 이유

Continue 모드는 **인터페이스가 근본적으로 다르다**:

```python
# Overlay 모드: cycle_list → 사이클별 독립 결과
unified_profile_batch(cycle_list=[1, 5, 10, ...])
# → {1: result, 5: result, 10: result, ...}

# Continue 모드: step_ranges → 범위별 연속 결과
unified_profile_batch_continue(step_ranges=[(1, 3), (5, 7)])
# → {(1, 3): result, (5, 7): result}
```

Continue에서는 사이클 간 시간/용량이 연속이어야 하므로, 사이클 단위 독립 처리가 불가능하다.
`(start, end)` 범위를 통째로 `unified_profile_core()`에 전달해야 한다.

---

## 핵심 Python 문법 설명

### 1. `@dataclass` 반환 vs 기존 `[mincapacity, df]` 반환

```python
# 기존: 리스트로 반환 → 위치 기반 접근 (가독성 낮음)
result = batch_results[cyc]
mincapacity = result[0]
df = result[1]

# 통합: dataclass로 반환 → 이름 기반 접근
result = batch_results[cyc]
mincapacity = result[0]           # 호환성 유지
profile = result[1]               # UnifiedProfileResult
df = profile.df                   # 명시적
```

### 2. `**options` dict 패턴

```python
# 옵션을 dict로 전달 → 확장 용이
options = {
    "data_scope": "charge",
    "axis_mode": "soc",
    "calc_dqdv": True,
}
# 꺼낼 때: options.get("key", default) — 키 없으면 기본값
```

### 3. `ThreadPoolExecutor` + `as_completed` 패턴

```python
with ThreadPoolExecutor(max_workers=N) as executor:
    futures = {executor.submit(func, arg): arg for arg in tasks}
    for future in as_completed(futures):
        result = future.result()  # 완료된 순서대로 결과 수신
```

- `submit()`: 태스크를 스레드풀에 제출 (비동기)
- `as_completed()`: 완료된 순서대로 Future 반환 (FIFO 아님)
- 프로그레스바 업데이트는 `completed / total` 비율로 계산
