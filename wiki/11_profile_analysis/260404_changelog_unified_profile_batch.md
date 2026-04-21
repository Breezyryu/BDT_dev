# 260404 — Phase 3: 통합 프로필 배치 로더 추가

> 📎 2026-04-21: `260404_review_unified_batch_loader_architecture` 병합 (아키텍처 상세 섹션 흡수)

## 배경 / 목적

Phase 2에서 `unified_profile_core()`가 기존 5개 파싱 함수와 동일한 결과를 산출함을 검증했다.
Phase 3에서는 **배치 로딩 계층**을 통합한다.

기존 구조: 10개 배치 함수(toyo/pne × step/rate/chg/dchg/continue) + 2개 병렬 로더(`_load_step_batch_task`, `_load_profile_batch_task`)가 개별적으로 작동.

통합 목표: 1개 배치 함수 + 1개 병렬 로더로 교체하되, **PNE SaveData 1회 I/O 최적화**를 유지.

## 변경 내용

### 신규 함수 (proto_.py)

| 함수명 | 위치 | 역할 |
|--------|------|------|
| `_unified_process_single_cycle_from_raw()` | 라인 1331~ | 이미 로드된 원시 데이터에서 단일 사이클 Stage 2~6 실행 |
| `unified_profile_batch()` | 라인 1452~ | **메인 배치 함수** — PNE/Toyo 분기, cycle_list 전체 처리 |
| `unified_profile_batch_continue()` | 라인 1579~ | Continue 전용 배치 — step_ranges 단위 처리 |
| `_load_unified_batch_task()` | 라인 14101~ | ThreadPoolExecutor용 채널 단위 태스크 (WindowClass 메서드) |
| `_load_all_unified_parallel()` | 라인 14138~ | **통합 병렬 로더** — 모든 폴더 병렬 처리 (WindowClass 메서드) |

### 기존 10개 배치 함수 → 통합 매핑

| 기존 함수 | 통합 호출 |
|-----------|----------|
| `toyo_step_Profile_batch` | `unified_profile_batch(data_scope="charge", axis_mode="time", continuity="overlay")` |
| `pne_step_Profile_batch` | 동일 (PNE 자동 감지) |
| `toyo_rate_Profile_batch` | `unified_profile_batch(data_scope="charge", axis_mode="time", continuity="overlay")` ※ 스텝 병합 없음 |
| `pne_rate_Profile_batch` | 동일 |
| `toyo_chg_Profile_batch` | `unified_profile_batch(data_scope="charge", axis_mode="soc", calc_dqdv=True)` |
| `pne_chg_Profile_batch` | 동일 |
| `toyo_dchg_Profile_batch` | `unified_profile_batch(data_scope="discharge", axis_mode="soc", calc_dqdv=True)` |
| `pne_dchg_Profile_batch` | 동일 |
| `toyo_continue_Profile_batch` | `unified_profile_batch_continue(step_ranges=[...])` |
| `pne_continue_Profile_batch` | 동일 |

### 기존 2개 병렬 로더 → 통합 매핑

| 기존 | 통합 |
|------|------|
| `_load_step_batch_task` + `_load_all_step_data_parallel` | `_load_unified_batch_task` + `_load_all_unified_parallel` |
| `_load_profile_batch_task` + `_load_all_profile_data_parallel` | 동일 |

## 핵심 설계 결정

### 1. PNE 1회 I/O 최적화 유지

```
기존: _pne_load_profile_raw() → all_raw 1회 로드 → 사이클별 분배
통합: _unified_pne_load_raw(min, max) → all_raw 1회 로드
      → Cycle 컬럼으로 슬라이싱
      → _unified_process_single_cycle_from_raw() 사이클별 Stage 2~6
```

PNE SaveData는 수백 MB 단위의 바이너리 CSV이므로 **사이클별 개별 로드**는 I/O 병목.
기존 최적화를 그대로 유지하면서 통합 파이프라인의 Stage 2~6을 적용한다.

### 2. Toyo는 사이클별 unified_profile_core() 직접 호출

Toyo는 사이클별 개별 파일(`000001`, `000002`, ...)이므로 일괄 로드의 이점이 없다.
`unified_profile_core()`를 루프 호출하되, `min_cap` 산정은 1회만 수행.

### 3. Continue 모드 분리

Continue 모드는 다른 모드와 인터페이스가 다르다:
- 입력: `step_ranges = [(start, end), ...]` (사이클 범위 쌍)
- 옵션: `continuity="continuous"` 고정, `data_scope="cycle"` 고정

`unified_profile_batch_continue()`로 분리하여 명확성 확보.

### 4. 반환 형식 호환

```python
# 기존 배치 함수
{cycle_no: [mincapacity, df]}

# 통합 배치 함수
{cycle_no: [mincapacity, UnifiedProfileResult]}
# UnifiedProfileResult.df → 기존 df와 동일 컬럼 구조
```

Phase 4 UI 통합 시, `result.df`로 접근하면 기존 렌더러와 호환.

## Before / After 비교

### Before
```
10개 배치 함수 × (PNE/Toyo 분기 내장)
2개 병렬 로더 × (profile_type 분기)
= 12개 함수, ~500줄 코드
```

### After
```
1개 배치 함수 (unified_profile_batch)
1개 Continue 전용 (unified_profile_batch_continue)
1개 내부 헬퍼 (_unified_process_single_cycle_from_raw)
1개 병렬 로더 (_load_all_unified_parallel)
1개 태스크 함수 (_load_unified_batch_task)
= 5개 함수, ~300줄 코드
```

## 영향 범위

- **변경된 파일**: `DataTool_dev/DataTool_optRCD_proto_.py`
- **추가된 코드**: ~300줄
  - `_unified_process_single_cycle_from_raw()`: 라인 1331~
  - `unified_profile_batch()`: 라인 1452~
  - `unified_profile_batch_continue()`: 라인 1579~
  - `_load_unified_batch_task()`: 라인 14101~ (WindowClass 메서드)
  - `_load_all_unified_parallel()`: 라인 14138~ (WindowClass 메서드)
- **기존 함수**: 변경 없음 (유지, Phase 5에서 제거 예정)
- **UI**: 변경 없음 (Phase 4에서 통합 UI 구현 예정)

## 다음 단계

- ~~Phase 3: 배치 로더 통합~~ ✅ 완료
- Phase 4: UI 통합 (5개 버튼 → 1개 통합 버튼 + 4개 옵션 위젯)
- Phase 5: 기존 10개 배치 함수 + 2개 병렬 로더 deprecated → 제거

---

## 아키텍처 (ThreadPoolExecutor)

> 이하 내용은 `260404_review_unified_batch_loader_architecture` (2026-04-04) 에서 병합됨.
> 통합 배치 로더의 전체 호출 구조, I/O 분기 원리, ThreadPoolExecutor 패턴 등 상세.

### 전체 호출 구조

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

### 왜 이렇게 분기하는가? — PNE vs Toyo I/O 패턴

| | PNE | Toyo |
|--|-----|------|
| 파일 구조 | SaveData 파일 수개에 모든 사이클 압축 | 사이클별 개별 파일 (000001, 000002...) |
| 최적 로딩 | 파일 1회 읽고 메모리에서 사이클 분배 | 사이클별 파일 읽기 (일괄 불가) |
| I/O 병목 | 대용량 CSV 파싱 | 파일 열기/닫기 반복 |

PNE에서 `_unified_pne_load_raw(min_cycle, max_cycle)`을 1회 호출하면, SaveData 파일을 한 번만 파싱하고 전체 원시 데이터를 메모리에 올린다. 이후 `all_raw[all_raw["Cycle"] == cyc]`로 사이클별 슬라이싱하면 디스크 I/O 없이 처리 가능하다.

Toyo는 사이클별 파일이므로 일괄 로드 이점이 없어 `unified_profile_core()`를 직접 루프 호출한다.

### `_unified_process_single_cycle_from_raw()` 상세

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

**왜 Stage 1만 분리했는가?**

Stage 1(원시 로딩)이 I/O 바운드이고, Stage 2~6은 CPU 바운드(DataFrame 조작)이기 때문이다.
PNE 배치에서는 Stage 1을 1회만 실행하고, 나머지는 사이클별로 반복 실행하는 것이 최적.

### `unified_profile_batch()` 옵션 라우팅

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

#### 옵션 → 기존 함수 매핑표

| data_scope | axis_mode | calc_dqdv | 기존 함수 |
|-----------|-----------|-----------|----------|
| charge | time | False | step/rate |
| charge | soc | True | chg |
| discharge | soc | True | dchg |
| cycle | time | False | continue (overlay) |

### 병렬 로더 `_load_all_unified_parallel()` 구조

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

#### 기존 대비 차이점

| | 기존 | 통합 |
|--|------|------|
| 태스크 함수 | `_load_step_batch_task` + `_load_profile_batch_task` | `_load_unified_batch_task` 1개 |
| 분기 기준 | `profile_type` 문자열 + `is_pne` bool | `options` dict (4개 옵션) |
| `is_pne` 판별 | 태스크 생성 시 전달 | 배치 함수 내부에서 자동 판별 |
| 결과 형식 | `[mincapacity, df]` | `[mincapacity, UnifiedProfileResult]` |

기존에는 `is_pne`를 상위 로더에서 판별해서 태스크에 전달했지만, 통합 버전에서는 `unified_profile_batch()` 내부에서 `check_cycler()`를 호출한다. 이는 채널별로 사이클러 타입이 다를 수 있는 경우에도 정확히 작동한다.

### Continue 모드가 분리된 이유

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

### 핵심 Python 문법 설명

#### 1. `@dataclass` 반환 vs 기존 `[mincapacity, df]` 반환

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

#### 2. `**options` dict 패턴

```python
# 옵션을 dict로 전달 → 확장 용이
options = {
    "data_scope": "charge",
    "axis_mode": "soc",
    "calc_dqdv": True,
}
# 꺼낼 때: options.get("key", default) — 키 없으면 기본값
```

#### 3. `ThreadPoolExecutor` + `as_completed` 패턴

```python
with ThreadPoolExecutor(max_workers=N) as executor:
    futures = {executor.submit(func, arg): arg for arg in tasks}
    for future in as_completed(futures):
        result = future.result()  # 완료된 순서대로 결과 수신
```

- `submit()`: 태스크를 스레드풀에 제출 (비동기)
- `as_completed()`: 완료된 순서대로 Future 반환 (FIFO 아님)
- 프로그레스바 업데이트는 `completed / total` 비율로 계산
