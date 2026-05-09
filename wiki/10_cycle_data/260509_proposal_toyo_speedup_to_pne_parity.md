---
title: "Toyo 사이클·프로파일 가속 제안 — PNE 동등 수준 도달"
date: 2026-05-09
tags: [proposal, toyo, performance, optimization, speedup, cache, phase0, sidecar]
related:
  - "[[260509_policy_data_parsing_pipeline]]"
  - "[[260509_policy_toyo_data_operation]]"
  - "[[260509_audit_toyo_lifetime_full_inventory]]"
  - "[[260410_study_pne_cyc_vs_csv_structure]]"
status: proposal
---

# Toyo 가속 제안 — PNE 동등 수준 도달

> **목표**: Toyo 사이클 50~235 ms → 20~100 ms / Toyo 프로파일 N×1~10 ms → 30~200 ms warm.
> **방법**: PNE 우위 4 원인 분해 → 4 trajectory 가속 (Quick win · Phase 0 · 사이드카 cache · binary 변환).
> **제 1원칙**: raw 데이터 무수정. 캐시는 사이드카 (`<channel>/.bdt_cache/`) 또는 메모리만.

---

## TL;DR

- **PNE 우위 4 원인**: (1) Phase 0 캐시 ChannelMeta (2) `imp` 컬럼 직접 사용 (DCIR I/O 0) (3) pivot_table 1-pass (4) `.cyc` binary warm cache
- **Toyo 가속 4 trajectory** — A·B·C·D 단계 누적
  - **A: Quick win** (1~2 일) — usecols + 프로파일 ThreadPool + merge_rows 벡터화 → **2~5x speedup**
  - **B: Toyo Phase 0** (1주) — `ToyoChannelMeta` dataclass → **PNE Phase 0 동등 패러다임**
  - **C: 사이드카 cache** (1~2주) — `<channel>/.bdt_cache/timeseries.parquet` → **PNE warm 동등**
  - **D: binary 변환** (장기) — Toyo NNNNNN → BDT 자체 binary → **PNE 우위**
- **Decision Required**: 사이드카 cache 위치 정책 + 사용자 trigger UX (Decision 12)
- **회귀 위험**: byte-level 정합 검증 fixture (β/γ/δ) 갱신 필수

---

## 1. 현황 vs 목표 비용

| 분석 | 현재 Toyo | 현재 PNE | 목표 (A 후) | 목표 (C 후) |
|---|---|---|---|---|
| 사이클 | 50 ~ 235 ms | 20 ~ 100 ms | 25 ~ 100 ms | **5 ~ 30 ms** |
| 프로파일 (N=100) | 100 ~ 1000 ms | 30 ~ 200 ms (warm) | 30 ~ 250 ms (병렬) | **1 ~ 30 ms (warm)** |
| 프로파일 (N=1000) | 1 ~ 10 s | 100 ~ 500 ms (warm) | 250 ms ~ 2 s (병렬) | **5 ~ 50 ms (warm)** |

> **C 단계 도달 시 Toyo warm = PNE warm 동등** (사이드카 cache).

---

## 2. PNE 우위 4 원인 — 분해

| 원인 | PNE 측 동작 | Toyo 측 부재 | 효과 |
|---|---|---|---|
| **C1** Phase 0 캐시 | `ChannelMeta` (proto_:380) — SaveEndData 13 컬럼 view 사전 추출 + cycle_map 캐시 | Toyo 측 등가 부재 — `_get_channel_cache` 는 raw csv 만 캐시 | 첫 호출 후 재호출 즉시 |
| **C2** DCIR I/O 0 | SaveEndData `imp` 컬럼 (col 20) 직접 사용 — disk read 추가 0 | Toyo NNNNNN 5~10개 추가 read 필요 (DCIR 펄스 파일) | 20~100 ms 추가 부담 |
| **C3** 벡터화 집계 | `pivot_table` 1-pass — 13 컬럼 한 번에 집계 | `groupby + apply (merge_rows)` Python loop | 5~50 ms |
| **C4** `.cyc` binary warm cache | float32 records — warm 1.6~6.6 ms (5~200x csv) | 16 컬럼 cp949 csv per-step | 100~1000x speedup 가능 |

---

## 3. 가속 방안 매트릭스

| ID | 방안 | 영역 | 효과 (예상) | 구현 비용 | 우선순위 |
|---|---|---|---|---|---|
| **A1** | `pd.read_csv(usecols=[...])` 모든 Toyo read 적용 | I/O | **1.5~2x** | < 1 일 | ★★★ |
| **A2** | 프로파일 측 ThreadPool 도입 (`_unified_toyo_load_raw`) | I/O | **3~4x** (NAS 부하 한계) | 1 일 | ★★★ |
| **A3** | `merge_rows` Python loop → numpy mask 벡터화 | CPU | **5~10x** (5~50 ms → 1~5 ms) | 1~2 일 | ★★ |
| **B1** | `ToyoChannelMeta` dataclass — Phase 0 동등 패러다임 | 인프라 | **5~25x** 재호출 | 3~5 일 | ★★★ |
| **B2** | DCIR 사이클 list 사전 추출 → meta 보관 | I/O | DCIR 5~10 file → 1 file (메타) | B1 통합 | ★★ |
| **C1** | 사이드카 `timeseries.parquet` (NNNNNN bundle) | 인프라 | **100~500x** 재호출 | 1~2주 | ★★★ |
| **C2** | 사이드카 `cycle.parquet` (capacity.log + derived) | 인프라 | **10~25x** | C1 통합 | ★★ |
| **C3** | mtime 검증 + 자동 재변환 | 인프라 | 정합 보장 | C1 통합 | ★★★ |
| **D1** | Toyo NNNNNN → BDT 자체 binary 변환 (PNE-equivalent) | 장기 | **200~1000x** | 1~2개월 | ★ |

> **★★★ = 즉시 추진 권장** / **★★ = B 단계 묶음** / **★ = D 장기**

---

## 4. A 단계 — Quick Win (1~2 일)

### A1. `usecols` 모든 Toyo read 적용

**현재** (proto_:5230 — `toyo_read_csv`):

```python
dataraw = pd.read_csv(filepath, sep=",", skiprows=skiprows, engine="c",
                      encoding="cp949", on_bad_lines='skip')
# → 17/19/16 컬럼 모두 파싱 후 5/10 컬럼만 추출
```

**제안**:

```python
# capacity.log (1 인자) — 사이클 분석 측 10 컬럼
CAP_LOG_USECOLS = ['TotlCycle', 'Condition', 'Cap[mAh]', 'Ocv', 'Finish',
                   'Mode', 'PeakVolt[V]', 'Pow[mWh]', 'PeakTemp[Deg]', 'AveVolt[V]']
# NNNNNN (2 인자) — 프로파일 분석 측 5 컬럼
NNNNNN_USECOLS = ['PassTime[Sec]', 'Voltage[V]', 'Current[mA]', 'Condition', 'Temp1[Deg]']
```

**효과**: read 시간 1.5~2x 감소 + 메모리 1/3.
**위험**: BLK5200 컬럼명 다름 (`Capacity[mAh]`, `Passed Time[Sec]`) → callable usecols 또는 fallback 분기.
**구현 거점**: `toyo_read_csv` proto_:5211, `toyo_Profile_import` proto_:5237 read 측 함수.

### A2. 프로파일 ThreadPool 도입

**현재** (proto_:2026~2065 — `_unified_toyo_load_raw`):

```python
for logical_cyc in range(cycle_start, cycle_end + 1):
    for phys_cyc in range(first_file, last_file + 1):
        tempdata = toyo_Profile_import(raw_file_path, phys_cyc)  # 순차
```

**제안**: 사이클 분석 측 DCIR 패턴 (proto_:5411) 그대로 — `ThreadPoolExecutor(max_workers=4)`.

```python
def _read_one(phys_cyc):
    return phys_cyc, toyo_Profile_import(raw_file_path, phys_cyc)

with ThreadPoolExecutor(max_workers=min(4, calc_optimal_workers(N))) as ex:
    for phys_cyc, tempdata in ex.map(_read_one, all_phys_cycles):
        ...
```

**효과**: 100 cycle = 100~1000 ms → 30~250 ms (3~4x).
**위험**: NAS 환경 채널 레벨 ThreadPool과 이중 부하 — workers ≤ 4 강제 (사이클 분석 측 정책 정합).

### A3. `merge_rows` 벡터화

**현재** (proto_:5315 — `merge_rows` groupby+apply):

```python
def merge_rows(group):
    if len(group) == 1: return group.iloc[0]
    cond = group["Condition"].iloc[0]
    result = group.iloc[-1].copy()  # 마지막 행 기준
    if cond == 1:
        result["Cap[mAh]"] = group["Cap[mAh]"].sum()
        ...
    return result
Cycleraw = Cycleraw.groupby(merge_group, group_keys=False).apply(merge_rows, ...)
```

**제안**: groupby + agg (numpy 벡터화):

```python
agg_dict = {
    'Cap[mAh]': 'sum',     # Cond=1, 2 모두
    'Pow[mWh]': 'sum',     # Cond=2 만 (마스크 후 적용)
    'Ocv': 'first',        # 첫 행
    'PeakVolt[V]': 'last', # 마지막 행
    'PeakTemp[Deg]': 'last',
    'TotlCycle': 'last',
    'Condition': 'first',
    'Finish': 'last',
    'Mode': 'last',
    'AveVolt[V]': 'last',  # 후처리 재계산
}
Cycleraw = Cycleraw.groupby(merge_group).agg(agg_dict).reset_index(drop=True)
# AveVolt 재계산 (Cond=2 만): Pow / Cap
mask_dchg = (Cycleraw['Condition'] == 2) & (Cycleraw['Cap[mAh]'] != 0)
Cycleraw.loc[mask_dchg, 'AveVolt[V]'] = Cycleraw.loc[mask_dchg, 'Pow[mWh]'] / Cycleraw.loc[mask_dchg, 'Cap[mAh]']
```

**효과**: 5~50 ms → 1~5 ms (5~10x).
**위험**: 기존 출력과 byte-level 정합 검증 필수 (`first` vs `iloc[0]` 등). 회귀 fixture β 측 검증.

---

## 5. B 단계 — Toyo Phase 0 (1주)

### B1. `ToyoChannelMeta` dataclass 신설

**모델**: PNE의 `ChannelMeta` (proto_:380) 패턴 그대로:

```python
@dataclass
class ToyoChannelMeta:
    channel_path: str
    capacity_log_view: pd.DataFrame  # 10 컬럼 추출 + OriCycle 보존
    mincapacity: float
    ptn_struct: dict  # extract_toyo_ptn_structure 결과
    cycle_map: dict   # toyo_build_cycle_map 결과
    chgvolt_map: pd.Series   # 충전 PeakVolt max
    chgsteps_map: pd.Series  # 충전 step 수
    dcir_cycles: list[int]   # DCIR 펄스 사이클 list (B2)
    fingerprint: str  # raw mtime/size hash (캐시 검증)
```

**진입점**: `get_toyo_channel_meta(path)` (PNE의 `get_channel_meta` mirror).

**저장**: 메모리 `_toyo_meta_store: dict[str, ToyoChannelMeta]`.

**효과**:
- 첫 호출: 50~235 ms 그대로
- 재호출 (UI 토글, 그래프 재그리기): **5~10 ms** (메모리 hit)
- 사이클 + 프로파일 두 분석 모두 같은 meta 공유

### B2. DCIR 사이클 list 사전 추출

**현재**: 사이클 분석 매 호출마다 NNNNNN 5~10개 read.
**제안**: meta 생성 시 1회 sweep — DCIR 사이클 식별 (`Finish=Tim ∧ Cap<min/60 ∧ Cond=2`) → list 보관. 분석 시 list 그대로 사용.

**효과**: DCIR 측 disk read 횟수가 N (전체 사이클) 에서 K (DCIR 펄스 수, 5~10개) 로 감소 — 이미 현재 동작과 같음. 신규 효과 = **meta cache hit 시 0**.

### B3. 무효화 정책

`fingerprint = hash(capacity_log mtime + size)` — raw 변경 시만 재생성.
[[260509_policy_toyo_data_operation|§5.2]] 의 "사용자 명시 trigger" 정책 정합. 새 경로 감지 UI 진입 시 자동 재계산.

---

## 6. C 단계 — 사이드카 Cache (1~2주)

### C1. `timeseries.parquet` (NNNNNN bundle)

**구조**:

```
<channel>/
├── 000001 ~ NNNNNN          # raw — 무수정
├── CAPACITY.LOG             # raw — 무수정
└── .bdt_cache/              # ★ 신규 사이드카
    ├── meta.json            # schema_version, raw_fingerprint
    ├── timeseries.parquet   # NNNNNN N개 → 단일 parquet (5 컬럼 + Cycle 컬럼)
    └── cycle.parquet        # capacity.log + derived (10 컬럼 + OriCycle + ChgVolt)
```

**timeseries.parquet schema**:

```
Cycle (int32)            # TotlCycle
PassTime[Sec] (float32)
Voltage[V] (float32)
Current[mA] (float32)
Condition (int8)
Temp1[Deg] (float32)
```

**변환 로직**: 첫 trigger 시 (사용자 또는 자동) 모든 NNNNNN sweep → concat → parquet 저장.

**효과**:
- 첫 변환: 1~5 s (채널당, NNNNNN 1000~6000 file)
- 재호출: **1~10 ms** (parquet read, snappy 압축)
- 채널당 cache 크기: 30~50 MB (NNNNNN 합 100~250 MB 의 약 30%)

### C2. `cycle.parquet`

CAPACITY.LOG 10 컬럼 + Phase 0 derived (OriCycle, ChgVolt, ChgSteps) 사전 박제.

**효과**: 사이클 분석 첫 호출 5~25 ms → **1~3 ms**.

### C3. mtime 검증 + 자동 재변환

```python
def is_cache_valid(channel_path: str) -> bool:
    cache_meta = load_cache_meta(channel_path)
    if cache_meta is None: return False
    if cache_meta['schema_version'] != SCHEMA_VERSION: return False
    raw_fp = compute_raw_fingerprint(channel_path)  # mtime + size hash
    return raw_fp == cache_meta['raw_fingerprint']
```

**무효화 trigger**: raw 파일 추가/변경/schema 버전 갱신.

### C4. 사용자 UX (Decision 12)

| 옵션 | UX | 첫 호출 부담 | 정책 정합 |
|---|---|---|---|
| **(a) 자동 변환** | 첫 호출 시 5~15 s 진행바 → 이후 즉시 | 첫 호출만 부담 | ★★★ 권장 |
| **(b) 수동 trigger** | 사용자 우클릭 "캐시 생성" 메뉴 | 0 (사용자 의도) | ★★ 분석 빈도 낮은 채널 |
| **(c) 백그라운드 사전 변환** | 채널 발견 시 백그라운드 worker | 0 (UI 무영향) | ★★★ 멀티 채널 분석 |

> **Decision 12**: 본 3 옵션 중 default 선택 + 수동 무효화 / 강제 재생성 UI 추가 결정 필요.

---

## 7. D 단계 — Binary 변환 (장기)

### D1. Toyo → BDT 자체 binary

**모델**: PNE의 `.cyc` (float32 records) 같은 방식 — Toyo NNNNNN 16 컬럼을 5 컬럼 binary 로 변환.

**구조** (`<channel>/.bdt_cache/timeseries.bdtbin`):

```
[header 64 bytes]
- magic = b'BDTTYBIN'
- schema_version (u32)
- channel_id (u32)
- record_count (u32)
- ...
[records — 20 byte each]
- cycle (u32)
- passtime (f32)
- voltage (f32)
- current (f32)
- temp (f32)
- condition (u8 + padding)
```

**효과**:
- read: parquet 1~10 ms 와 유사 또는 약간 빠름
- 압축률: parquet snappy 와 비슷 (binary float32 압축률 한계)
- 의존성: BDT 자체 — pyarrow 의존 제거 가능

**Trade-off**:
- 구현 비용 1~2개월 (binary parser + 검증 fixture + UI 통합)
- parquet 대비 효과 marginal — pyarrow 의존이 부담스러울 때만 정당화
- **기각 가능성 高** — C 단계 (parquet) 로 충분.

---

## 8. 단계별 로드맵

```
Week 1-2:  A 단계 — Quick win
  ├── A1 usecols (1 일)
  ├── A2 프로파일 ThreadPool (1 일)
  └── A3 merge_rows 벡터화 (1~2 일)
  → Toyo 사이클 25~100 ms · 프로파일 30~250 ms (PNE 동등 진입)

Week 3:    B 단계 — Toyo Phase 0
  ├── B1 ToyoChannelMeta dataclass + 진입점
  ├── B2 DCIR 사이클 list 사전 추출
  └── B3 fingerprint 무효화
  → 재호출 5~10 ms · 멀티 분석 공유 meta

Week 4-5:  C 단계 — 사이드카 cache
  ├── C1 timeseries.parquet
  ├── C2 cycle.parquet
  ├── C3 mtime 검증
  └── C4 UX (Decision 12)
  → Toyo warm 1~30 ms (PNE warm 동등)

(장기):    D 단계 — Binary 변환 (선택)
  └── D1 .bdtbin (parquet 의존 제거 시만)
```

**MBO 정합** ([[26_W19]] / [[mbo_2026]]): A·B 는 **1.2 혁신 (개발자용 SW + AI 협업 도구)** 측 직접 기여. C 는 **1.2.2 도전** 측 사이클 데이터 이상 감지 / 빅데이터 분석 인프라 측 anchor.

---

## 9. 위험·Trade-off

### 9.1 정합 위험

| 위험 | 영역 | 완화 |
|---|---|---|
| `merge_rows` 벡터화 결과가 기존과 미세 차이 | A3 | byte-level diff fixture β |
| `usecols` BLK5200 컬럼명 다름 → 누락 | A1 | callable usecols 또는 try/except fallback |
| 사이드카 cache 가 stale → 잘못된 분석 | C3 | fingerprint 검증 + schema_version |
| 사이드카 변환 중 process kill → 부분 cache | C1 | atomic write (`.tmp` → rename) |

### 9.2 disk · 메모리 trade-off

- 사이드카 cache disk 사용량: 채널당 30~50 MB → 156 채널 ([[260509_audit_toyo_lifetime_full_inventory|260509 audit]]) = **5 ~ 8 GB 추가**
- 메모리 (B 단계 Phase 0): 채널당 1~5 MB × 동시 분석 채널 수 — UI 멀티 채널 시 폭증 차단 정책 필요 (LRU max 50 채널 제안)

### 9.3 정책 정합

- **raw 무수정** ([[260509_policy_toyo_data_operation|운영 정책]]) — 사이드카는 `<channel>/.bdt_cache/` 별도 폴더, raw 무영향 ✓
- **사외/사내 dual-env** ([[31_software_dev/adr/0008-bdt-test-and-study-automation|ADR-0008]]) — 사외 PC subset / 사내 PC full 모두 동작 ✓
- **AI 도구 외부 의존 X** — pyarrow / pandas / numpy 만 사용 ✓
- **Fasoo DRM 대응** — 사이드카는 사외 환경에서도 변환 가능 (raw csv 만 cp949) ✓

---

## 10. 회귀 검증

### 10.1 fixture 갱신

각 단계마다 [[31_software_dev/adr/0008-bdt-test-and-study-automation|ADR-0008]] 의 fixture α/β/γ/δ 4종 갱신:

| 단계 | α (경로) | β (전처리) | γ (그래프) | δ (저장) |
|---|---|---|---|---|
| A1 usecols | — | byte-level diff | — | — |
| A2 ThreadPool | — | order-invariant 검증 | — | — |
| A3 merge_rows | — | **byte-level diff** ★ | trend 일치 | — |
| B1 Phase 0 | meta hit/miss 시나리오 | 동일 결과 보장 | — | — |
| C1 사이드카 | + .bdt_cache fixture | parquet vs raw byte-level | — | — |

### 10.2 성능 회귀 검증

- benchmark fixture: 표준 채널 1개 (Q7M Inner BLK1 ch11, 4956 NNNNNN) — `pytest-benchmark`
- 기준: A 단계 후 사이클 ≤ 100 ms · 프로파일 ≤ 250 ms (100 cycle)
- 기준: C 단계 후 사이클 warm ≤ 30 ms · 프로파일 warm ≤ 50 ms (100 cycle)

---

## 11. 핵심 코드 위치 (수정 거점)

### A 단계

- `toyo_read_csv` proto_:5211 — A1 usecols 추가
- `toyo_Profile_import` proto_:5237 — A1 + BLK 변종 분기 정합
- `_unified_toyo_load_raw` proto_:1988 — A2 ThreadPool 도입
- `merge_rows` proto_:5315 — A3 벡터화 (groupby+agg)

### B 단계

- 신규 `ToyoChannelMeta` dataclass — proto_:380 (PNE ChannelMeta 인접)
- 신규 `get_toyo_channel_meta()` — proto_:775 (PNE `get_channel_meta` 인접)
- 신규 `_toyo_meta_store` — proto_:830 (PNE `_clear_channel_meta_store` 인접)
- `toyo_cycle_data` proto_:5289 / `toyo_Profile_import` proto_:5237 — meta 진입점 통합

### C 단계

- 신규 모듈 `bdt_cache.py` — atomic write, fingerprint, schema_version
- `_unified_toyo_load_raw` proto_:1988 — parquet 진입점 우선
- `toyo_cycle_data` proto_:5289 — cycle.parquet 진입점 우선
- UI — 캐시 trigger 메뉴 (Decision 12)

---

## 12. Open Decision

| # | 항목 | 1순위 안 | trigger |
|---|---|---|---|
| **D12** | C 단계 cache 변환 trigger UX | (a) 자동 변환 + (b) 수동 무효화 | C 단계 진입 시 사용자 결정 |
| **D13** | 사이드카 cache LRU max 채널 수 | 50 채널 (~250 MB 메모리) | B 단계 진입 시 |
| **D14** | D 단계 binary 변환 채택 여부 | 기각 (parquet 충분) | C 단계 후 효과 측정 |
| **D15** | benchmark fixture 채널 선정 | Q7M Inner BLK1 ch11 (4956 step) | A 단계 진입 전 |

---

## 13. Related

- [[260509_policy_data_parsing_pipeline]] — 본 가속의 baseline 비용
- [[260509_policy_toyo_data_operation]] — 운영 정책 (raw 무수정·캐시 무효화 정합)
- [[260509_audit_toyo_lifetime_full_inventory]] — 156 채널 NNNNNN 분포 (cache 크기 산정 근거)
- [[260410_study_pne_cyc_vs_csv_structure]] — `.cyc` warm/cold 벤치마크 (목표 기준)
- [[260411_analysis_cycle_pipeline_complete]] — 전체 사이클 파이프라인
- [[31_software_dev/adr/0008-bdt-test-and-study-automation|ADR-0008]] — fixture α/β/γ/δ

---

## 14. 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-09 | 최초 제안 — PNE 우위 4 원인 분해 + Toyo 가속 4 trajectory (A 9·B 3·C 4·D 1) + Decision D12~D15 |
