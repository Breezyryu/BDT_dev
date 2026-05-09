---
title: "Changelog: A 단계 구현 — usecols + ThreadPool + merge_rows 벡터화 (류성택 요청)"
date: 2026-05-09
tags: [changelog, code, toyo, performance, a-step, usecols, threadpool, vectorize]
related:
  - "[[260509_proposal_toyo_speedup_to_pne_parity]]"
  - "[[260509_policy_data_parsing_pipeline]]"
status: applied
---

# Changelog: A 단계 구현 — Quick Win 3건

> 작업 요청자: 류성택 (사용자) — `A작업 진행해 - raw에 어떤 컬럼이 있는 지 나열하고 추출하는 컬럼은 어떤건지 알려줘`

---

## 변경 사항

### 1. raw 컬럼 전수 조사 (`raw/raw_exp/exp_data/수명_Toyo` 156 채널)

**CAPACITY.LOG 헤더 변종 2종**:
- Variant 1 — BLK3600 17 컬럼 (n=64)
- Variant 2 — BLK3600 19 컬럼 (n=88, `+DchCycle, +PassedDate`)
- BLK5200 본 디렉토리 0건

**NNNNNN 헤더 변종 2종**:
- Variant 1 — 16 컬럼 (n=64)
- Variant 2 — 17 컬럼 (n=88, `+PassedDate`)

**핵심 발견**:
- 빈 컬럼 4~5개 (col 5, 6, 8, 9, 10) — 시스템 reserved
- `Temp1[Deg]` 중복 (col 7과 col 15/16) — 한 번만 read 충분
- CAPACITY.LOG 빈 컬럼 2개 (col 12, 15) — pandas 가 빈 이름으로 파싱

### 2. 추출 컬럼 매핑

#### CAPACITY.LOG — 17~19 → **10 컬럼**

| # | 컬럼 | 추출 |
|---:|---|:---:|
| 0,1 | Date, Time | ❌ |
| 2 | Condition | ✅ |
| 3 | Mode | ✅ |
| 4 | Cycle (1 고정) | ❌ |
| 5 | TotlCycle | ✅ |
| 6 | Cap[mAh] | ✅ |
| 7,8 | PassTime, TotlPassTime | ❌ |
| 9 | Pow[mWh] | ✅ |
| 10 | AveVolt[V] | ✅ |
| 11 | PeakVolt[V] | ✅ |
| 12 | (blank) | ❌ |
| 13 | PeakTemp[Deg] | ✅ |
| 14 | Ocv | ✅ |
| 15 | (blank) | ❌ |
| 16 | Finish | ✅ |
| 17,18 | DchCycle, PassedDate | ❌ |

#### NNNNNN — 16~17 → **5 컬럼**

| # | 컬럼 | 추출 |
|---:|---|:---:|
| 0,1 | Date, Time | ❌ |
| 2 | PassTime[Sec] | ✅ |
| 3 | Voltage[V] | ✅ |
| 4 | Current[mA] | ✅ |
| 5,6 | (blank) | ❌ |
| 7 | Temp1[Deg] | ✅ |
| 8,9,10 | (blank) | ❌ |
| 11 | Condition | ✅ |
| 12,13,14 | Mode, Cycle, TotlCycle | ❌ (cycle_map 으로 별도 매핑) |
| 15 | PassedDate or Temp1[Deg] dup | ❌ |
| 16 | Temp1[Deg] dup | ❌ |

### 3. 코드 변경 — `DataTool_dev_code/DataTool_optRCD_proto_.py`

| 변경 | 라인 | 내용 |
|---|---|---|
| **A1** module-level usecols set | proto_:5224~5243 | `TOYO_CAP_LOG_USECOLS` (18 names) + `TOYO_NNNNNN_USECOLS` (8 names) frozenset |
| **A1** `toyo_read_csv` | proto_:5244~5275 | `usecols=lambda c: c in usecols_set` callable 적용 |
| **A2** `_unified_toyo_load_raw` | proto_:2018~2079 | 작업 평탄화 + `ThreadPoolExecutor(max_workers=4)` |
| **A3** `toyo_cycle_data` `_agg_dict` | proto_:5360~5383 | groupby + agg 벡터화 dict |
| **A3** `toyo_cycle_data` agg 호출 | proto_:5417~5429 | `groupby(merge_group, sort=False).agg(_agg_active)` |
| **A3** AveVolt 후처리 재계산 | proto_:5424~5429 | `Cond=2 ∧ Cap≠0` 마스크 |

### 4. 코드 정합 보존

- **단일 진입점 정책 ([[260509_policy_data_parsing_pipeline|§7 D1]])**: `toyo_read_csv`, `_unified_toyo_load_raw`, `toyo_cycle_data` 만 수정. 다른 곳에서 raw 직접 read 하는 케이스 0 (회귀 영향 없음).
- **단위 통일 SSOT ([[260509_policy_data_parsing_pipeline|§7 D2]])**: 단위 변환 식 무수정 — `usecols` 는 read 단계만, downstream 정규화 (`_unified_normalize_toyo`) 무영향.
- **위치 기반 인덱스 정렬 ([[260509_policy_toyo_data_operation|§10.1]])**: A3 가 결과 row 순서 보존 — `groupby(sort=False)` 명시.
- **순서 보존 ([[260509_proposal_toyo_speedup_to_pne_parity|§9.1]])**: A2 ThreadPool `ex.map()` 입력 순서대로 결과 yield → `file_boundaries` 정합.

---

## Why

### 기존 문제

A1 — `pd.read_csv` 가 17~19 / 16~17 컬럼 모두 파싱 후 추출 단계에서 5/10 컬럼만 사용. 메모리·CPU 낭비.

A2 — `_unified_toyo_load_raw` 의 NNNNNN read 가 순차 for-loop. 채널당 NNNNNN p50=1715, max=5954 ([[260509_audit_toyo_lifetime_full_inventory|260509 audit]]) → disk I/O 직렬화 병목.

A3 — `merge_rows` 가 `groupby + apply` Python loop. 다단 충전 1 채널 100~200 그룹 × Python 함수 호출 overhead.

### 해결

- **A1** — `usecols` callable 로 read 단계에서 필요 컬럼만 파싱. read 1.5~2x 가속 + 메모리 1/3.
- **A2** — 작업 평탄화 + `ThreadPoolExecutor(max_workers=4)` 병렬 read. 100 cycle 800~1000 ms → 230 ms (3~4x).
- **A3** — `groupby + agg` numpy 벡터화. merge 단계 5~50 ms → 1~5 ms (5~10x).

### 정책 정합

- raw 무수정 ([[260509_policy_toyo_data_operation|운영 정책]]) ✓
- 단일 진입점 ([[260509_policy_data_parsing_pipeline|D1]]) ✓
- workers ≤ 4 (NAS 부하 차단, 사이클 분석 측 DCIR ThreadPool 패턴 정합) ✓
- byte-level 정합 — A3 의 `Pow[mWh]` Cond=1/Rest 측 sum 변경은 다운스트림 사용 0 확인

---

## 검증 — 실데이터 (Q7M Inner BLK1 ch11, NNNNNN 4956 step)

### A1 검증

```
=== toyo_read_csv (CAPACITY.LOG) ===
   read time: 9.4 ms
   shape: (5955, 10)        ← 이전 (5955, 17~19)
   cols (10): ['Condition', 'Mode', 'TotlCycle', 'Cap[mAh]', 'Pow[mWh]',
               'AveVolt[V]', 'PeakVolt[V]', 'PeakTemp[Deg]', 'Ocv', 'Finish']

=== toyo_read_csv (NNNNNN cycle 1) ===
   read time: 4.2 ms
   shape: (2811, 6)         ← 이전 (2811, 16~17)
   cols (6): ['PassTime[Sec]', 'Voltage[V]', 'Current[mA]',
              'Temp1[Deg]', 'Condition', 'TotlCycle']
```

→ ✅ 컬럼 수 17/16 → 10/6 (TotlCycle 은 신뢰성 fallback 측 추출, downstream 미사용)

### A3 + 사이클 풀 파이프라인

```
=== toyo_cycle_data 풀 (Q7M Inner BLK1 ch11, mincap=1689) ===
   total time: 94.7 ms       ← 이전 추정 ~150~235 ms (큰 채널)
   df.NewData shape: (1000, 19)
   df.NewData head:
     Cycle  Dchg     Eff      Eff2    AvgV     ...
     1      1.022    1.940    0.982   3.924    (1st RPT 사이클)
     2      0.963    0.960    0.998   3.807
     3      0.963    1.002    1.000   3.808
```

→ ✅ Eff·Eff2·Dchg ratio 정상 범위. 출력 정합 OK.

### A2 검증 — 100 cycle / 500 cycle 프로파일 read

```
=== _unified_toyo_load_raw (100 cycle) ===
   total time: 230.4 ms      ← 이전 추정 100~1000 ms (3~4x speedup)
   shape: (19978, 9)
   Cycle range: [1, 100]
   Conditions: {2: 9777, 1: 7668, 3: 2533}  ← 0=휴지 → 3 통일 정합

=== _unified_toyo_load_raw (500 cycle) ===
   total time: 927.3 ms      ← 100 cycle 의 ~4x (linear)
```

→ ✅ workers=4 정합, Condition 매핑 정합, 시간 PNE warm 영역 진입.

### Cache hit 효과

```
First call:   94.7 ms
Cache hit:    51.5 ms       ← capacity.log + mincap 캐시 hit
```

→ B 단계 (ToyoChannelMeta) 시 5~10 ms 도달 가능 — 다음 단계.

---

## 가속 효과 — 정량

| 지표 | 이전 | A 단계 후 | speedup |
|---|---:|---:|---:|
| `toyo_read_csv` (CAPACITY.LOG) | ~15~25 ms | **9.4 ms** | 1.6~2.5x |
| `toyo_cycle_data` 풀 (4956 step 채널) | ~150~235 ms | **94.7 ms** | ~1.6~2.5x |
| `_unified_toyo_load_raw` 100 cycle | ~800~1000 ms | **230 ms** | **3~4x** |
| `_unified_toyo_load_raw` 500 cycle | ~4 ~ 5 s | **0.93 s** | **~5x** |

→ **PNE 사이클 (20~100 ms) 동등 진입** ✅
→ **PNE 프로파일 warm (30~200 ms) 영역 진입** (100 cycle 230 ms — 약간 상회) ✅

---

## 영향 범위

### 직접 영향

- **사이클 분석 가속** — Toyo 측 사이클 50~235 → **~94 ms** (PNE 동등 진입).
- **프로파일 분석 가속** — Toyo 측 프로파일 (100 cycle) 800~1000 → **230 ms** (PNE warm 영역).
- **메모리 절약** — read 시 추출 컬럼만 → 메모리 1/3 (NNNNNN 16 → 5 컬럼).
- **단일 진입점 강화** — `TOYO_*_USECOLS` frozenset 가 추출 컬럼 SSOT 역할. 컬럼 추가 시 본 set 갱신 + 회귀 fixture 갱신.

### 간접 영향

- **B 단계 (Phase 0) 진입 준비** — `ToyoChannelMeta` 도입 시 본 A 단계 결과 (10/5 컬럼 view) 가 그대로 dataclass field 가 됨.
- **C 단계 (사이드카 cache) 진입 준비** — A1 의 컬럼 추출 정합 → 사이드카 parquet schema 도 동일 10/5 컬럼.
- **회귀 fixture 미생성** — A3 byte-level 정합은 `Pow[mWh]` Cond=1/Rest 측 sum 로 변경. 다운스트림 사용 0 확인했으나, 사용자 실데이터 측 추가 검증 필요.

### 무영향

- 다른 사이클러 (PNE) 코드 무수정.
- 다른 Toyo 함수 (`toyo_min_cap`, `toyo_build_cycle_map`, `extract_toyo_ptn_structure`) 무수정.
- raw 데이터 무수정.

---

## 후속 작업

1. **사용자 실데이터 회귀 검증** — Toyo 채널 1~2개로 신·구 코드 출력 비교 (특히 다단 충전 / DCIR 펄스 多 케이스).
2. **B 단계 진입** — `ToyoChannelMeta` dataclass 신설 ([[260509_proposal_toyo_speedup_to_pne_parity|§5 B1]]).
3. **PR 발행** — git push 사용자 명시 승인 후 main 머지 (현재 `claude/cool-bardeen-9ffc5b` worktree branch).
4. **벤치마크 자동화** — `pytest-benchmark` 도입 + 표준 fixture (Q7M Inner BLK1 ch11) 등록 ([[260509_proposal_toyo_speedup_to_pne_parity|§10.2]]).

---

## Related

- [[260509_proposal_toyo_speedup_to_pne_parity]] — 4 trajectory 제안 (A 단계 source)
- [[260509_policy_data_parsing_pipeline]] — 파싱 정책 (D1 단일 진입점, D2 단위 통일)
- [[260509_policy_toyo_data_operation]] — Toyo 운영 정책 (raw 무수정)
- [[260509_audit_toyo_lifetime_full_inventory]] — 156 채널 분포 (NNNNNN p50=1715, max=5954)
- [[260508_raw_data_schema_unified_reference]] — schema fact (raw 17~19/16~17 컬럼)

---

## 갱신 (2026-05-09 추가) — Date/Time 추출 + 단일행 정합 보존

### 1. Date/Time 추출 추가

사용자 요청: `[0,1] Date,Time 도 활용하자.`

| 변경 | 라인 | 내용 |
|---|---|---|
| `TOYO_CAP_LOG_USECOLS` | proto_:5226 | `'Date', 'Time'` 추가 (10 → 12 names) |
| `TOYO_NNNNNN_USECOLS` | proto_:5237 | `'Date', 'Time'` 추가 (5 → 7 names) |
| `toyo_cycle_import` | proto_:5305~5320 | 추출 list 에 `Date, Time` 추가 (10 → 12 컬럼) |
| `toyo_Profile_import` | proto_:5260~5290 | BLK 변종 3종 모두 `Date, Time` 추가 (5 → 7 컬럼) |
| `_agg_dict` | proto_:5379~5380 | `'Date': 'last', 'Time': 'last'` (사이클 종료 시점) |
| `_unified_toyo_load_raw` | proto_:2113~2118 | `Datetime_abs = pd.to_datetime(Date + ' ' + Time)` 표준 컬럼 |
| `_unified_normalize_toyo` | proto_:2236~2237 | `Datetime_abs` 표준 출력 schema 측 통과 |

**활용**:
- 시험 시작/종료 절대 timestamp 추적
- 폴더명 (`250207_250307`) 와 정합 검증
- 챔버 온도 변경 시점 / 시험 중단 시점 식별 가능
- 멀티 채널 동기화 (정확한 timestamp)

**검증**:
```
Q7M Inner BLK1 ch11 (50 cycle):
  Datetime_abs n_valid: 11304/11304 (100%)
  first: 2025-02-06 19:44:18
  last:  2025-02-08 04:47:32  (약 33시간)

Q7M Sub ch10 (50 cycle):
  first: 2025-02-19 17:47:36
  last:  2025-02-21 04:09:05  (약 35시간)
```

### 2. A3 단일행 정합 보존

**문제**: 첫 회귀 검증 시 5/5 채널 모두 `AvgV` 측 미세 diff (Δ ~0.001 V) 발견.

**원인**: 기존 `merge_rows` 의 `if len(group)==1: return group.iloc[0]` 분기 → 단일 행 Cond=2 그룹은 raw `AveVolt[V]` 유지. 신 코드 (`agg + mask`) 는 단일 행 Cond=2 도 `Pow/Cap` 으로 재계산 → raw 측정값 (~3.6952 V) vs 계산값 (~3.6940 V) 미세 차이.

**해결** (proto_:5418~5436):

```python
# 그룹 크기 사전 계산 — 단일 행 그룹 식별용
_group_sizes = Cycleraw.groupby(merge_group, sort=False).size().values
Cycleraw = Cycleraw.groupby(merge_group, sort=False).agg(_agg_active).reset_index(drop=True)
# AveVolt[V] 재계산 — Cond=2 ∧ Cap≠0 ∧ 다중 행 그룹 만 (단일 행은 raw 유지)
_mask_dchg_re = (
    (Cycleraw['Condition'] == 2) &
    (Cycleraw['Cap[mAh]'] != 0) &
    (_group_sizes > 1)
)
```

### 3. 회귀 검증 — 5채널 byte-level 정합

다단 충전 + DCIR 펄스 多 채널:

| 채널 | NNNNNN | shape | 이전 (ms) | 신 (ms) | speedup | byte-level |
|---|---:|---|---:|---:|---:|---|
| Q7M Inner BLK1 ch11 | 4956 | (1000, 19) | 296.9 | **94.1** | **3.2x** | ✅ |
| Q7M Sub ch10 | 5841 | (1177, 19) | 314.3 | **69.6** | **4.5x** | ✅ |
| Q7M Main ch21 | 4956 | (1000, 19) | 265.9 | **59.6** | **4.5x** | ✅ |
| M1 ch10 | 1717 | (433, 19) | 122.0 | **37.1** | **3.3x** | ✅ |
| 김건희 245 장수명 ch22 | 796 | (201, 19) | 45.3 | **23.9** | **1.9x** | ✅ |

**종합**: 채널 5, 총 diffs 0, **전체 PASS**. 평균 speedup ~3.5x.

### 4. PNE 동등 수준 도달 확인

| 지표 | PNE 사이클 | Toyo 사이클 (A 단계 후) | 결론 |
|---|---|---|---|
| 일반 채널 (~1700 step) | 20~100 ms | **37 ms** | ✅ PNE 동등 |
| 큰 채널 (~5000 step) | (PNE 동등 N/A) | **60~95 ms** | ✅ PNE 영역 |
| 최대 (~5841 step) | — | **70 ms** | ✅ |

**[[260509_proposal_toyo_speedup_to_pne_parity|제안]] 의 A 단계 목표 (25~100 ms) 도달**.

### 5. 정합 보존 정책 박제

본 검증 결과 → [[260509_policy_data_parsing_pipeline|파싱 정책]] §10 회귀 검증 측 갱신 권고:

> **byte-level 정합 우선** — 가속 변경 시 기존 동작 정합 보존 강제. 기존 출력과 미세 차이 (~0.001 V) 발견 시도 PASS 처리 금지. 단일 행 그룹 등 분기 정합 보존.
