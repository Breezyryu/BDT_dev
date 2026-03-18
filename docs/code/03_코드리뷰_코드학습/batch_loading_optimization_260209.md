# 배치 로딩 최적화 — Step Profile 데이터 처리 (2026.02.09)

## 1. 배경 및 문제 정의

### 1.1 데이터 규모

| 항목 | 범위 | 설명 |
|------|------|------|
| `all_data_folder` | ≤ 10 | 최상위 폴더 (온도 등 조건별) |
| `subfolder` (채널) | ≤ 20 | 각 폴더 내 충방전기 채널 |
| `CycleNo` | 1 ~ 2,000 | 스텝 충전 사이클 수 |

최악의 경우 처리 대상: **10 × 20 × 2,000 = 400,000 사이클**

### 1.2 기존 구조의 병목

기존 `step_confirm_button`은 **사이클마다** 개별 함수(`toyo_step_Profile_data` / `pne_step_Profile_data`)를 호출했다.

```
for folder in all_data_folder:          # ≤10
  for channel in subfolder:             # ≤20
    for cycle in CycleNo:               # ≤2000
      toyo_step_Profile_data(...)       # ← 매번 독립 호출
```

이 구조에서 사이클당 반복되는 디스크 I/O가 핵심 병목이었다.

---

## 2. I/O 분석: 얼마나 중복 읽기가 발생하는가

### 2.1 Toyo 사이클러

| 함수 | 호출 위치 | 중복 읽기 내용 |
|------|-----------|---------------|
| `toyo_min_cap()` | `toyo_step_Profile_data` 진입 시 | `mincapacity == 0`이면 **매 사이클마다** cycle-1 파일(`000001`) 읽기 |
| `toyo_Profile_import()` | 사이클 데이터 읽기 | 사이클별 개별 파일 → 중복 없음 (파일이 모두 다름) |

**핵심 문제**: `toyo_min_cap`이 **2,000번** 동일한 cycle-1 파일을 읽음

```python
# 기존: 사이클마다 호출
def toyo_step_Profile_data(raw_file_path, inicycle, mincapacity, cutoff, inirate):
    tempmincap = toyo_min_cap(raw_file_path, mincapacity, inirate)  # ← 매번 실행
    mincapacity = tempmincap
    ...
```

### 2.2 PNE 사이클러

| 함수 | 호출 위치 | 중복 읽기 내용 |
|------|-----------|---------------|
| `pne_min_cap()` | 진입 시 | `SaveData0001.csv` (대형 파일) **매 사이클마다** 읽기 |
| `pne_search_cycle()` → `pne_data()` | 사이클 데이터 위치 탐색 | `SaveEndData.csv` + `savingFileIndex_start.csv` **매 사이클마다** 읽기 |
| `pne_data()` | 실제 데이터 읽기 | 해당 범위의 `SaveData*.csv` 파일 읽기 (인접 사이클은 같은 파일 재읽기) |

**핵심 문제**: 1 채널 × 2,000 사이클 기준
- `SaveEndData.csv` → **2,000번** 읽기
- `savingFileIndex_start.csv` → **2,000번** 읽기
- `SaveData0001.csv` (min_cap) → **2,000번** 읽기
- 인접 사이클의 `SaveData` 파일 → **다수 중복 읽기**

20채널이면 총 **120,000회 이상** 대형 CSV 반복 읽기 발생.

```python
# 기존: pne_step_Profile_data 내부 호출 체인
def pne_step_Profile_data(raw_file_path, inicycle, mincapacity, cutoff, inirate):
    tempcap = pne_min_cap(raw_file_path, ...)    # SaveData0001.csv 읽기
    profile_raw = pne_data(raw_file_path, inicycle)  # ← 내부에서:
    # └→ pne_search_cycle()  → SaveEndData.csv + savingFileIndex_start.csv 읽기
    # └→ 해당 범위 SaveData*.csv 읽기
```

---

## 3. 최적화 전략: 채널 단위 배치 로딩

### 3.1 핵심 원리

> **"사이클별 호출"을 "채널별 1회 호출"로 변환**

```
[기존] 사이클 단위                    [배치] 채널 단위
┌──────────────────────┐            ┌──────────────────────┐
│ cycle 1 → 파일읽기    │            │ 채널 1번 진입         │
│ cycle 2 → 파일읽기    │            │  ├ min_cap 1회 계산   │
│ cycle 3 → 파일읽기    │     →      │  ├ 인덱스 1회 읽기    │
│ ...                   │            │  ├ SaveData 범위 로딩 │
│ cycle 2000 → 파일읽기 │            │  └ 메모리에서 분배     │
└──────────────────────┘            └──────────────────────┘
```

| 항목 | 기존 (사이클당) | 배치 (채널당) | 절감률 |
|------|-----------------|--------------|--------|
| `toyo_min_cap` 호출 | N회 (N=사이클수) | **1회** | 99.95% |
| `SaveEndData.csv` 읽기 | N회 | **1회** | 99.95% |
| `savingFileIndex_start.csv` 읽기 | N회 | **1회** | 99.95% |
| `SaveData` 파일 읽기 | N회 (중복 포함) | **1회** (범위 일괄) | ~90%+ |
| ThreadPool 태스크 수 | 폴더×채널×사이클 (~400K) | 폴더×채널 (~200) | 99.95% |

### 3.2 병렬화 세분도 변경

```
[기존]  ThreadPoolExecutor 태스크 = 폴더 × 채널 × 사이클
        → 최대 10 × 20 × 2000 = 400,000 태스크
        → 스레드 스케줄링 오버헤드 극심

[변경]  ThreadPoolExecutor 태스크 = 폴더 × 채널
        → 최대 10 × 20 = 200 태스크
        → 각 태스크 내부에서 2,000 사이클을 순차 처리 (I/O는 1회)
```

---

## 4. 구현 상세

### 4.1 새로 추가된 함수

#### `toyo_step_Profile_batch()` (글로벌 함수, ~L634)

```python
def toyo_step_Profile_batch(raw_file_path, cycle_list, mincapacity, cutoff, inirate):
    """
    Toyo 스텝 프로파일 배치 로딩: 채널당 1회 min_cap 산정 후, 모든 사이클을 순회.
    Returns: {cycle_no: [mincapacity, df], ...}
    """
    # ★ min_cap은 채널 진입 시 1회만 계산
    mincapacity = toyo_min_cap(raw_file_path, mincapacity, inirate)
    
    results = {}
    for inicycle in cycle_list:
        # 기존 toyo_step_Profile_data와 동일한 로직
        # Condition < 2 인 경우 다음 사이클 연결 처리 포함
        # 벡터화 용량 계산 (delta_time, next_current, contribution)
        # 단위 변환 (시간→분, 전류→C-rate, 용량→SOC)
        results[inicycle] = [mincapacity, df]
    return results
```

**변경 포인트**:
- `toyo_min_cap()` 호출이 루프 **바깥**에 위치 → 채널당 1회
- 반환값이 `dict` — `{사이클번호: [용량, DataFrame]}`

#### `pne_step_Profile_batch()` (글로벌 함수, ~L690)

```python
def pne_step_Profile_batch(raw_file_path, cycle_list, mincapacity, cutoff, inirate):
    """
    PNE 스텝 프로파일 배치 로딩
    """
    # ★ "Pattern" 폴더 조기 반환
    if (raw_file_path[-4:-1]) == "ter":
        return {cyc: [mincapacity, pd.DataFrame()] for cyc in cycle_list}
    
    # ★ min_cap 1회 계산
    mincapacity = pne_min_cap(raw_file_path, mincapacity, inirate)
    
    # ★ 인덱스 파일 1회 읽기 (SaveEndData, savingFileIndex_start)
    save_end_data = pd.read_csv(...)      # 1회
    file_index_list = pd.read_csv(...)    # 1회
    
    # ★ 전체 사이클 범위의 SaveData 파일을 1회 일괄 로딩
    min_cyc, max_cyc = min(cycle_list), max(cycle_list) + 1
    file_start = binary_search(file_index_list, ...)
    file_end = binary_search(file_index_list, ...)
    
    all_raw = pd.concat([
        pd.read_csv(rawdir + f) for f in subfile[file_start:file_end+1] if "SaveData" in f
    ])
    
    # ★ PNE21/22 단위 변환 계수 사전 결정
    is_pne21_22 = ('PNE21' in raw_file_path) or ('PNE22' in raw_file_path)
    current_divisor = mincapacity * (1000000 if is_pne21_22 else 1000)
    
    # ★ 메모리에서 사이클별 분배
    for inicycle in cycle_list:
        cycle_raw = all_raw[(all_raw[27] == inicycle) & (all_raw[2].isin([9, 1]))]
        # 컬럼 선택, 단위 변환, 스텝 연결, cut-off 처리
        results[inicycle] = [mincapacity, df]
    return results
```

**변경 포인트**:
1. `pne_min_cap()` → 1회 (기존: N회)
2. `SaveEndData.csv` → 1회 직접 읽기 (`pne_search_cycle` 우회)
3. `savingFileIndex_start.csv` → 1회 직접 읽기
4. `SaveData*.csv` → 범위 계산 후 필요한 파일만 1회 일괄 `pd.concat`
5. 사이클 분배는 `all_raw[27] == inicycle` 필터링으로 메모리에서 수행

### 4.2 변경된 클래스 메서드

#### `_load_step_batch_task()` (~L8513)

```python
def _load_step_batch_task(self, task_info):
    """채널 단위 배치 스텝 프로파일 로딩 (ThreadPoolExecutor용)"""
    folder_path, cycle_list, mincapacity, mincrate, firstCrate, is_pne, folder_idx, subfolder_idx = task_info
    try:
        if is_pne:
            batch_results = pne_step_Profile_batch(folder_path, cycle_list, ...)
        else:
            batch_results = toyo_step_Profile_batch(folder_path, cycle_list, ...)
        return (folder_idx, subfolder_idx, batch_results)
    except Exception as e:
        print(f"[배치 로딩 오류] {folder_path}: {e}")
        return (folder_idx, subfolder_idx, None)
```

- 기존 `_load_step_data_task`(사이클 1개 로딩)를 대체
- `cycle_list` 전체를 배치 함수에 위임

#### `_load_all_step_data_parallel()` (~L8530)

```python
def _load_all_step_data_parallel(self, all_data_folder, CycleNo, mincapacity, mincrate, firstCrate, max_workers=4):
    """모든 폴더의 스텝 프로파일 데이터를 병렬로 로딩 (채널 단위 배치)"""
    tasks = []
    for i, cyclefolder in enumerate(all_data_folder):       # ≤10 폴더
        subfolder = [f.path for f in os.scandir(cyclefolder) if f.is_dir()]
        is_pne = check_cycler(cyclefolder)
        for j, folder_path in enumerate(subfolder):          # ≤20 채널
            if "Pattern" not in folder_path:
                # ★ CycleNo 전체를 채널에 위임
                task_info = (folder_path, CycleNo, mincapacity, mincrate, firstCrate, is_pne, i, j)
                tasks.append(task_info)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(self._load_step_batch_task, task): task for task in tasks}
        for future in as_completed(futures):
            folder_idx, subfolder_idx, batch_results = future.result()
            if batch_results:
                for cyc_no, temp in batch_results.items():
                    results[(folder_idx, subfolder_idx, cyc_no)] = temp
            # 진행률: 채널 완료 기준 (50%까지)
            completed += 1
            self.progressBar.setValue(int(completed / total_tasks * 50))
    return results
```

**변경 전후 비교**:

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| 태스크 단위 | `(folder, channel, cycle)` | `(folder, channel)` |
| 태스크 수 (최악) | 400,000 | 200 |
| 태스크 인자 | `inicycle` (정수 1개) | `CycleNo` (리스트 전체) |
| 반환 형식 | `(i, j, cyc, [cap, df])` | `(i, j, {cyc: [cap, df], ...})` |
| 진행률 기준 | 사이클 완료 | 채널 완료 |

---

## 5. 데이터 흐름 다이어그램

```
step_confirm_button()
  │
  ├── _load_all_step_data_parallel(all_data_folder, CycleNo, ...)
  │     │
  │     ├── [Thread 1] _load_step_batch_task(채널A, CycleNo=[1..2000])
  │     │     └── toyo_step_Profile_batch() or pne_step_Profile_batch()
  │     │           ├── min_cap 1회 계산
  │     │           ├── 인덱스/원시데이터 1회 로딩
  │     │           └── 메모리에서 2000 사이클 분배 → {1: [...], 2: [...], ...}
  │     │
  │     ├── [Thread 2] _load_step_batch_task(채널B, CycleNo=[1..2000])
  │     │     └── (동일 구조)
  │     │
  │     ├── [Thread 3] ...
  │     └── [Thread 4] ...
  │
  │     → results = {(folder_idx, subfolder_idx, cyc_no): [mincapacity, df], ...}
  │
  ├── 결과 순회 및 플롯
  │     for cyc in CycleNo:
  │       for folder in all_data_folder:
  │         for channel in subfolder:
  │           data = results[(folder_idx, subfolder_idx, cyc)]
  │           _plot_and_save_step_data(axes, data, ...)
  │
  └── 타이틀/레전드 설정 + UI 업데이트
```

---

## 6. 기존 함수 보존

| 함수 | 위치 | 상태 |
|------|------|------|
| `toyo_step_Profile_data()` | ~L799 | **보존** — 단일 사이클 호출 시 사용 가능 |
| `pne_step_Profile_data()` | ~L1469 | **보존** — 단일 사이클 호출 시 사용 가능 |
| `toyo_step_Profile_batch()` | ~L634 | **신규** — 배치 로딩용 |
| `pne_step_Profile_batch()` | ~L690 | **신규** — 배치 로딩용 |

기존 함수는 삭제하지 않았으며, 다른 호출처(예: 단일 사이클 프리뷰 등)에서 계속 사용 가능하다.

---

## 7. 예상 성능 비교

### 케이스: 10폴더 × 20채널 × 2,000사이클 (PNE 기준)

| 작업 | 기존 | 배치 | 비고 |
|------|------|------|------|
| `SaveEndData.csv` 읽기 | 400,000회 | 200회 | 채널당 1회 |
| `savingFileIndex_start.csv` 읽기 | 400,000회 | 200회 | 채널당 1회 |
| `SaveData0001.csv` (min_cap) 읽기 | 400,000회 | 200회 | 채널당 1회 |
| `SaveData*.csv` (원시) 읽기 | ~800,000회+ | ~200회 | 범위 일괄 로딩 |
| ThreadPool 태스크 생성 | 400,000개 | 200개 | 오버헤드 대폭 감소 |
| 메모리 피크 | 사이클별 1개 DF | 채널별 전체 DF | 약간 증가 가능 |

**디스크 I/O 총 횟수**: 약 **160만 → 800회** (99.95% 감소)

---

## 8. 주의사항 및 한계

1. **메모리 사용량**: PNE 배치 로딩 시 `all_raw`에 전체 사이클 범위의 원시 데이터가 적재됨. 극단적으로 큰 데이터셋에서는 메모리 모니터링 필요.

2. **Toyo `Condition < 2` 처리**: 배치 함수 내에서도 다음 사이클 파일을 순차 읽어 연결하는 while 루프가 존재. 이 부분은 본질적으로 순차적이므로 추가 최적화가 어려움.

3. **에러 격리**: `_load_step_batch_task`에서 한 채널이 실패해도 다른 채널에 영향 없음 (`try/except`로 보호, `None` 반환).

4. **진행률 표시**: 기존 사이클 단위 → 채널 단위로 변경되어, 채널 수가 적은 경우 진행바 업데이트 간격이 넓어질 수 있음.

5. **기존 함수 호환**: `toyo_step_Profile_data`, `pne_step_Profile_data`는 그대로 유지되므로, 다른 기능에서 단일 사이클 로딩이 필요한 경우 기존 함수 사용 가능.

---

## 9. 파일 변경 요약

**대상 파일**: `BatteryDataTool_260206_edit/BatteryDataTool.py`

| 변경 유형 | 위치 (대략) | 내용 |
|-----------|------------|------|
| 추가 | L628~L795 | `toyo_step_Profile_batch()`, `pne_step_Profile_batch()` |
| 교체 | L8513~L8530 | `_load_step_data_task` → `_load_step_batch_task` |
| 교체 | L8530~L8568 | `_load_all_step_data_parallel` 채널 단위 배치 버전 |
| 보존 | L799, L1469 | 기존 `toyo_step_Profile_data`, `pne_step_Profile_data` 유지 |
