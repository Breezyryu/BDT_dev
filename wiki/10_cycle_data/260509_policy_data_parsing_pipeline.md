---
title: "데이터 파싱 정책 — 사이클 분석 / 프로파일 분석 (Toyo · PNE 비교)"
date: 2026-05-09
tags: [policy, parsing, cycle-analysis, profile-analysis, toyo, pne, performance]
related:
  - "[[260508_raw_data_schema_unified_reference]]"
  - "[[260509_policy_toyo_data_operation]]"
  - "[[260509_audit_toyo_lifetime_full_inventory]]"
  - "[[260409_study_02_toyo_cycle_data]]"
  - "[[260409_study_03_pne_cycle_data]]"
  - "[[260411_analysis_cycle_pipeline_complete]]"
status: policy
---

# 데이터 파싱 정책 — 사이클 분석 · 프로파일 분석

> **위치 부여**: schema fact (`260508`) + Toyo 운영 정책 (`260509_policy_toyo_data_operation`) 위에서, **분석 종류별 (사이클 vs 프로파일) × 사이클러별 (Toyo vs PNE) 4 매트릭스의 파싱 파이프라인** 박제.
> 코드 실측 (proto_:5211~12000) 기준 — 각 함수 line 번호 명시.

---

## TL;DR

- **사이클 분석** — 1 파일 (CAPACITY.LOG / SaveEndData) → 10/13 컬럼 추출 → 병합·DCIR·효율 → `df.NewData`
- **프로파일 분석** — N 파일 (NNNNNN / SaveData) → 5/14 컬럼 → 단위 정규화·시간보정 → 표준 컬럼 12종
- **컬럼 폭증 차단**: Toyo 17~19→10 (사이클) / 16→5 (프로파일) ▪ PNE 47+→13 (사이클) / 47+→14 (프로파일)
- **컴퓨팅**: Toyo 사이클 ~25 ms (cap.log 1 file) ▪ PNE 사이클 ~10 ms (Phase 0 캐시) ▪ Toyo 프로파일 N × 5 ms ▪ PNE 프로파일 무거움 (`.cyc warm` 1.6 ms / cold 50 ms)
- **DCIR 분기**: Toyo = 1 모드 (`Finish=Tim` AND) + ThreadPool ≤4 ▪ PNE = 3 모드 (chkir / mkdcir RSS+1s / 10s pulse) + vectorized numpy
- **단위 통일**: 표준 컬럼 = V·mA·sec·°C·mAh ratio. Toyo는 raw V/mA/°C 직접 + 용량 시간적분. PNE는 μV/μA/m°C 정수 → 1e6·1e3 분모 분리.

---

## 1. 4 매트릭스 — 분석 × 사이클러

| | **Toyo** | **PNE** |
|---|---|---|
| **사이클** | `toyo_cycle_data` proto_:5289 | `pne_cycle_data` proto_:11689 |
| **프로파일** | `_unified_toyo_load_raw` proto_:1988 + `_unified_normalize_toyo` proto_:2192 | `_unified_pne_load_raw` proto_:1729 + `_unified_normalize_pne` proto_:2111 |

> **사이클 = step 메타 요약** (1 step = 1 row, 사이클 트렌드 추출). **프로파일 = 시계열 raw** (1 step = N rows, V/I/T 곡선).

---

## 2. 사이클 분석 — Raw 컬럼 vs 추출 컬럼

### 2.1 Toyo `CAPACITY.LOG` — 17/19 → 10 컬럼

**Raw (BLK3600 17 컬럼)**:

```
Date, Time, Condition, Mode, Cycle, TotlCycle, Cap[mAh], PassTime, TotlPassTime,
Pow[mWh], AveVolt[V], PeakVolt[V], (blank), PeakTemp[Deg], Ocv, (blank), Finish
```

**Raw (BLK3600 19 컬럼 확장)**: 위 + `DchCycle, PassedDate`

**Raw (BLK5200 변종)**: `Total Cycle, Capacity[mAh], OCV[V], End Factor, Peak Volt.[V], Power[mWh], Peak Temp.[deg], Ave. Volt.[V]` — 긴 이름

**추출 — `toyo_cycle_import` proto_:5257**:

```
TotlCycle, Condition, Cap[mAh], Ocv, Finish, Mode, PeakVolt[V],
Pow[mWh], PeakTemp[Deg], AveVolt[V]
```

→ **10 컬럼 / 17 ~ 19 컬럼** (사용률 53~59%)

### 2.2 PNE `SaveEndData.csv` — 47+ → 13 컬럼

**Raw (47+ 컬럼, 헤더 X, 정수 인코딩)**: [[260508_raw_data_schema_unified_reference|260508 §3.4]] 참조.

**추출 — `pne_cycle_data` proto_:11705**:

```python
Cycleraw = save_end_cached[[27, 2, 10, 11, 8, 20, 45, 15, 17, 9, 24, 29, 6]]
Cycleraw.columns = ["TotlCycle", "Condition", "chgCap", "DchgCap", "Ocv", "imp",
                     "volmax", "DchgEngD", "steptime", "Curr", "Temp", "AvgV", "EndState"]
```

→ **13 컬럼 / 47+ 컬럼** (사용률 ~28%) — sparse 무시

### 2.3 무시 컬럼

| Toyo 무시 | PNE 무시 |
|---|---|
| `Date, Time` (PassTime 누적으로 충분) | col 0 Index, col 1 Stepmode (CV 분기 시만 보강) |
| `PassTime, TotlPassTime` (사이클 분석 측 불필요) | col 7 StepNo (사이클 분석 측 불필요) |
| `Cycle` (1 고정 — [[260509_policy_toyo_data_operation|§6.1]] 사용 금지) | col 14 ChgWh (DchgEngD 만 사용) |
| `DchCycle, PassedDate` (19 컬럼만, 미활용) | col 18 TotTime_Day (사이클 측 불필요) |
| | col 28 CurrCycle, col 30 AvgCurr, col 33 day, col 34 time |

---

## 3. 사이클 분석 — 전처리 파이프라인

### 3.1 Toyo `toyo_cycle_data` 13 단계

| # | 단계 | 라인 | 동작 |
|---:|---|---|---|
| 1 | mincap 산정 | proto_:5294 | `toyo_min_cap` — 캐시 → mAh 정규식 → I_max/inirate |
| 2 | CAPACITY.LOG 로드 | proto_:5297 | `toyo_cycle_import` → 10 컬럼 추출 (lru cache) |
| 3 | OriCycle 보존 | proto_:5301 | `Cycleraw["OriCycle"] = TotlCycle` |
| 4 | 고아 첫 행 드롭 | proto_:5305 | `Cond=2 AND TC=1` → drop |
| 5 | merge_group 생성 | proto_:5313 | `(cond ≠ shift) | (~cond.isin([1,2]))).cumsum()` |
| 6 | PeakVolt 사전 저장 | proto_:5337 | 병합 전 max + step 수 (`_chg_volt_map`, `_chg_steps_map`) |
| 7 | merge_rows 실행 | proto_:5348 | 다단 충전 → 1행. Cap 합산, AveVolt 재계산 |
| 8 | mask 1-pass | proto_:5351 | numpy mask: `_m_chg`, `_m_dchg`, `_m_dcir` 한 번에 |
| 9 | DCIR 병렬 읽기 | proto_:5388 | ThreadPoolExecutor (workers ≤ 4) NNNNNN 1개씩 |
| 10 | DCIR 사이클 매핑 | proto_:5415 | `cyccal` 일반/쌍 모드 (chkir) |
| 11 | 인덱스 정렬 | proto_:5447 | 위치 기반 `.values[:_nmin]` (인덱스 매칭 X) |
| 12 | Eff·Eff2·ratio | proto_:5459 | `Eff = Dchg/Chg`, `Eff2 = Chg2/Dchg`, `Dchg /= mincap` |
| 13 | df.NewData 조립 | proto_:5467 | 10 컬럼 + dcir + RndV split + cycle_map |

**핵심 정책 결정**:

- **고아 첫 행만 drop** (과거 버그: `Cond=2 전체 TotlCycle -=1` → DCIR 파일 번호 불일치 — proto_:5303 주석)
- **위치 기반 인덱스 매칭** — DCIR 펄스 끼어듦 → `Chg.index` ≠ `Dchg.index` 시스템적 → `.values[:_nmin]` 강제 ([[260509_policy_toyo_data_operation|§10.1]])
- **Pow mWh → Wh 변환** (`/1000`, proto_:5380) — PNE와 단위 통일

### 3.2 PNE `pne_cycle_data` 9 단계

| # | 단계 | 라인 | 동작 |
|---:|---|---|---|
| 1 | mincap 산정 | proto_:11700 | `pne_min_cap` (Toyo 와 동일 패턴) |
| 2 | SaveEndData 로드 | proto_:11703 | `get_channel_save_end_data` (Phase 0 캐시) |
| 3 | 13 컬럼 추출 | proto_:11705 | `[[27,2,10,11,8,20,45,15,17,9,24,29,6]]` |
| 4 | cycle_map 생성 | proto_:11711 | `_get_pne_cycle_map` (.sch 힌트 우선) |
| 5 | coincell 단위 변환 | proto_:11254 | `is_micro_unit` → DchgCap/chgCap/Curr `/1000` |
| 6 | DCIR 분기 | proto_:11258 | **3 모드** (chkir / mkdcir / 10s pulse) |
| 7 | pivot_table | proto_:11309 | index=TotlCycle, columns=Condition, sum/min/max aggfunc |
| 8 | 단위 정규화 | proto_:11322 | μV → V (/1e6), m°C → °C (/1000), mWh → Wh |
| 9 | df.NewData 조립 | proto_:11337 | 10 컬럼 + dcir 분기별 |

**핵심 정책 결정**:

- **Phase 0 캐시 표준** — `ChannelMeta` (proto_:380) → `get_channel_save_end_data` 거의 항상 hit
- **pivot_table 1-pass** — for-loop 대신 `pd.pivot_table` 로 13 컬럼 한 번에 집계
- **DCIR 3 모드 분기**:
  - `chkir=True` (일반): Cond=2 ∧ volmax>4.1V → `imp/1000`
  - `mkdcir=True` (RSS + 1s pulse): EndState 78/64 분기 + 벡터화 (`(_v3-_v1)/_c1`)
  - 기타 (10s pulse): Cond=2 ∧ steptime≤6000 → `imp/1000`

### 3.3 Toyo vs PNE — 핵심 단계 비교

| 항목 | Toyo | PNE | Why |
|---|---|---|---|
| 1차 데이터 | text CSV (lru_cache) | binary 정수 (Phase 0 ChannelMeta) | 형식 다름 |
| 다단 충전 처리 | `merge_rows` 명시 | `pivot_table sum` 묵시 | PNE는 step 단위 분리 안 됨 |
| DCIR 모드 | 1 (Finish=Tim AND) | 3 (chkir / mkdcir / 10s) | PNE EndState/steptime 풍부 |
| DCIR 계산 | ThreadPool 병렬 NNNNNN 읽기 | 단일 `imp/1000` (이미 측정됨) | Toyo는 V/I 직접, PNE는 imp 컬럼 |
| 인덱스 정렬 | 위치 기반 강제 | TotlCycle pivot 자연 정합 | Toyo merge 부작용 |
| Eff 계산 | 동일 | 동일 | — |
| 효율 | 양방향 호환 | 양방향 호환 | — |

---

## 4. 프로파일 분석 — Raw 컬럼 vs 추출 컬럼

### 4.1 Toyo `NNNNNN` — 16 → 5 컬럼

**Raw (BLK3600 16 컬럼)**:

```
Date, Time, PassTime[Sec], Voltage[V], Current[mA], (blank), (blank),
Temp1[Deg], (blank), (blank), (blank), Condition, Mode, Cycle, TotlCycle, Temp1[Deg]_dup
```

**추출 — `toyo_Profile_import` proto_:5237**:

```python
df.dataraw = df.dataraw[["PassTime[Sec]", "Voltage[V]", "Current[mA]", "Condition", "Temp1[Deg]"]]
```

→ **5 컬럼 / 16 컬럼** (사용률 31%)

**BLK 변종 처리** (proto_:5241~5252):

| 분기 | 컬럼 정규화 |
|---|---|
| `PassTime[Sec]` ∈ cols ∧ `Temp1[Deg]` ∈ cols | BLK3600 — 그대로 |
| `PassTime[Sec]` ∈ cols ∧ `Temp1[Deg]` ∉ cols | 신뢰성 (Temp 부재) — `TotlCycle` → `Temp1[Deg]` rename (안전 fallback) |
| `Passed Time[Sec]` ∈ cols | BLK5200 — `Passed Time[Sec] → PassTime[Sec]`, `Temp1[deg] → Temp1[Deg]` |

### 4.2 PNE `SaveData<NNNN>.csv` — 47+ → 14 컬럼

**Raw (47+ 컬럼, SaveEndData 동일 schema)**: [[260508_raw_data_schema_unified_reference|260508 §3.5]] 참조.

**추출 — `_unified_pne_load_raw` proto_:1729 docstring 명시**:

```
[0]Index, [2]StepType, [7]StepNo,
[8]Voltage(μV), [9]Current(μA),
[10]ChgCap(μAh), [11]DchgCap(μAh),
[14]ChgWh, [15]DchgWh,
[17]StepTime(/100s), [18]TotTime(day), [19]TotTime(/100s),
[21]Temp1, [27]TotalCycle
```

→ **14 컬럼 / 47+ 컬럼** (사용률 ~30%)

### 4.3 무시 컬럼

| Toyo 무시 | PNE 무시 |
|---|---|
| `Date, Time` (PassTime 으로 충분) | col 1 Stepmode, col 3 ChgDchg, col 4-5 |
| col 5,6,8,9,10 (blank) | col 12,13 ChgPower/DchgPower (raw W) |
| col 13 Cycle (Toyo 신뢰 X) | col 16,18 (sparse) |
| col 14 TotlCycle (별도 cycle_map 사용) | col 22-26 Temp2/3, col 28-32, col 35-44 |
| col 15 Temp1 dup | col 45 voltage_max (사이클 측만), col 46+ |

---

## 5. 프로파일 분석 — 정규화 파이프라인

### 5.1 Toyo `_unified_normalize_toyo` 7 단계 (proto_:2192)

| # | 변환 | 라인 | 식 |
|---:|---|---|---|
| 1 | Condition 통일 | proto_:2084 (load) | Toyo `0=휴지` → PNE `3=휴지` (`replace({0:3})`) |
| 2 | 시간 누적 보정 | proto_:2216 | `time_diffs = np.diff(time_raw)`; 음수 → 0 → cumsum |
| 3 | Voltage | proto_:2223 | 그대로 (이미 V) |
| 4 | Current 부호 | proto_:2226 | `Cond=2 → -1`, else `+1` (Toyo 크기값만 기록) |
| 5 | Crate | proto_:2229 | `signed_curr_mA / mincapacity` |
| 6 | 용량 적분 | proto_:2261 | `Σ(dt × abs(next_I) / 3600) / mincap` (Toyo 누적 cap 미제공 — 시간적분) |
| 7 | 에너지 적분 | proto_:2268 | `Σ(dt × abs(next_I) × next_V / 3600) / mincap` |

**핵심 정책 결정**:

- **시간 리셋 보정** — daily timer reset (PassTime 1440 기준 0 reset) → 음수 diff → 0 클립 → cumsum
- **shift(-1) 패턴** — `dt × next_I` (다음 행 전류 × 다음 행까지 시간차) — 기존 BDT 누적 정합
- **부호 부여** — Toyo는 Condition 으로만 부호 결정 (raw current는 모두 양수)

### 5.2 PNE `_unified_normalize_pne` 9 변환 (proto_:2111)

| # | 변환 | 라인 | 식 |
|---:|---|---|---|
| 1 | Condition 그대로 | proto_:2137 | 1=충전, 2=방전, 3=휴지 (이미 통일) |
| 2 | 시간 (TotTime) | proto_:2144 | `(TotTime_Day × 8640000 + TotTime_Sec_raw) / 100` → sec |
| 3 | Voltage | proto_:2152 | μV → V (`/1_000_000`) |
| 4 | Current (μA) | proto_:2160 | μA → A (`/1_000_000`) — **일반 PNE** |
| 5 | Current (nA) | proto_:2158 | nA → A (`/1_000_000_000`) — **PNE21/22 코인셀** |
| 6 | Crate | proto_:2163 | `Current_raw / cap_divisor` (cap_divisor = mincap × 1e6 if micro else × 1e3) |
| 7 | 용량 정규화 | proto_:2166 | `ChgCap_raw / cap_divisor` (이미 누적 제공!) |
| 8 | 에너지 | proto_:2170 | `ChgWh_raw / cap_divisor` |
| 9 | Temp | proto_:2174 | m°C → °C (`/1_000`) |

**핵심 정책 결정**:

- **`is_micro_unit` 분기** — PNE21/22 (코인셀) → 1e9 분모. 일반 PNE → 1e6 분모. 분기 단일 진입점 (`is_micro_unit` proto_:741) 강제.
- **TotTime > StepTime** — 멀티 사이클 시 누적 시간 (TotTime_Day × 8640000) 우선, 단일 사이클은 StepTime fallback
- **누적 용량 직접 사용** — PNE는 ChgCap/DchgCap 누적값 제공 → 시간적분 불필요 (Toyo와 결정적 차이)

### 5.3 Toyo vs PNE — 정규화 비교

| 변환 | Toyo | PNE | 운영 함의 |
|---|---|---|---|
| Voltage | 그대로 (V) | μV → V (/1e6) | Toyo 정밀도 낮음 (소수점 4자리), PNE 6자리 |
| Current 부호 | Cond 기반 부여 | raw signed | Toyo는 Condition 정확해야 부호 정합 |
| 용량 | 시간적분 (`Σ dt·I`) | raw 누적 직접 | Toyo는 dt·I 정밀도 의존 |
| Temp | 그대로 (°C) | m°C → °C (/1e3) | PNE 3자리 정밀도 |
| 시간 base | PassTime cumsum (리셋 보정) | TotTime_Day × 8640000 + TotTime_Sec | PNE는 day overflow 보정 |
| 코인셀 분기 | 없음 | `is_micro_unit` → 1e9 분모 | PNE21/22 만 |

**표준 출력 컬럼 (12 / 14 — 양 사이클러 통일)**:

```
Time_s, Voltage, Current_mA, Crate, Temp,
ChgCap, DchgCap, ChgWh, DchgWh,
Step, Condition, Cycle [, PhysicalCycle, OCV, CCV, Stepmode]
```

---

## 6. 컴퓨팅 비용 — 측정 + 캐시 정책

### 6.1 사이클 분석 비용 (채널당)

| 사이클러 | 단계 | 비용 | 캐시 |
|---|---|---:|---|
| Toyo | CAPACITY.LOG 로드 | 5 ~ 25 ms | `_get_channel_cache(path)['capacity_log']` (lru) |
| Toyo | 10 컬럼 추출 + merge_group cumsum | 10 ~ 30 ms | — |
| Toyo | merge_rows (groupby apply) | 5 ~ 50 ms | — |
| Toyo | DCIR (NNNNNN 5~10 file 병렬 읽기) | 20 ~ 100 ms | ThreadPool ≤ 4 workers |
| Toyo | df.NewData 조립 + ptn 구조 | 10 ~ 30 ms | `extract_toyo_ptn_structure` 내부 캐시 |
| **Toyo 합계** | | **~50 ~ 235 ms** | |
| PNE | SaveEndData 로드 | 10 ~ 50 ms | **Phase 0 ChannelMeta** (거의 hit) |
| PNE | 13 컬럼 view | < 1 ms | view (no copy) |
| PNE | pivot_table | 5 ~ 30 ms | — |
| PNE | DCIR (벡터화) | 1 ~ 5 ms | — |
| PNE | df.NewData 조립 | 5 ~ 15 ms | — |
| **PNE 합계** | | **~20 ~ 100 ms** | |

> **PNE 가 ~2~3x 빠름** — Phase 0 캐시 + 벡터화 DCIR + view-based 컬럼 추출. Toyo는 NNNNNN DCIR 파일 5~10개 병렬 읽기가 지배적.

### 6.2 프로파일 분석 비용 (채널당, N 사이클)

| 사이클러 | 단계 | 비용 | 캐시 |
|---|---|---:|---|
| Toyo | NNNNNN N개 순차 read | N × 1 ~ 10 ms | 없음 (per-file disk read) |
| Toyo | 5 컬럼 추출 × N | < 1 ms × N | — |
| Toyo | concat + Condition 통일 | ~10 ms | — |
| Toyo | 시간 cumsum + 부호 + 용량 적분 | ~20 ms (벡터화) | — |
| **Toyo 합계 (N=100)** | | **~120 ~ 1020 ms** | |
| PNE | SaveData<NNNN> batch 로드 | 무거움 (0.5 ~ 5 MB × M) | `_cached_pne_restore_files` (lru) |
| PNE | `.cyc` warm gap-fill | **1.6 ~ 6.6 ms** (warm) / 49 ~ 55 ms (cold) | binary cache 강력 |
| PNE | 14 컬럼 추출 + 단위 정규화 | ~30 ~ 100 ms | — |
| **PNE 합계 (warm 캐시)** | | **~30 ~ 200 ms** | |
| **PNE 합계 (cold 캐시)** | | **~500 ms ~ 5 s** | 첫 호출 |

> **PNE warm 캐시는 압도적 빠름** (5~200x, [[260410_study_pne_cyc_vs_csv_structure|260410]] 벤치). **cold 호출은 무거움** — `.cyc` 캐시 정책이 핵심.

### 6.3 캐시 계층

| 캐시 | 적용 | 진입점 | 무효화 |
|---|---|---|---|
| **L1 — `_get_channel_cache(path)`** | Toyo CAPACITY.LOG, mincap | proto_:863 | `clear_channel_cache()` proto_:858 또는 자동 (path stale) |
| **L2 — `ChannelMeta`** | PNE SaveEndData 13 컬럼 view + cycle_map | proto_:380, 775 | `clear_channel_meta_store()` proto_:830 |
| **L3 — `_cached_pne_restore_files`** | PNE Restore 폴더 (.cyc gap-fill 포함) | proto_:1528 | lru maxsize 도달 시 LRU eviction |
| **L4 — lru_cache (functools)** | `extract_toyo_ptn_structure`, `_parse_pne_sch` | 함수 데코레이터 | 프로세스 재시작 |

**무효화 정책 ([[260509_policy_toyo_data_operation|§5.2]])**: 사용자 명시 trigger (UI "새 경로 감지" 또는 재시작) — 자동 invalidation X. 시험 중 분석 모드 = "완료 시험 분석" 위주.

---

## 7. 정책 결정 박스

### D1 — 컬럼 사용률 강제

- **Toyo 사이클**: 17~19 → **10 컬럼만** (`toyo_cycle_import` 단일 진입점, 추가 컬럼 ad-hoc 사용 금지)
- **Toyo 프로파일**: 16 → **5 컬럼만** (`toyo_Profile_import` 단일 진입점)
- **PNE 사이클**: 47+ → **13 컬럼만** (`pne_cycle_data` proto_:11705 positional indexing)
- **PNE 프로파일**: 47+ → **14 컬럼만** (`_unified_pne_load_raw` docstring)
- **Why**: sparse 컬럼 (PNE col 22-44) 의미 미공개 + 메모리 폭증 차단
- **신규 분석 시**: 컬럼 추가 필요 시 **단일 진입점** 갱신 + 회귀 fixture (β/δ) 동시 갱신

### D2 — 단위 통일 SSOT

- **사이클러 무관 표준 단위**: V, mA, sec, °C, mAh ratio (0~1)
- Toyo raw → 표준: V, mA, sec, °C, Wh `/1000` 만 변환
- PNE raw → 표준: μV `/1e6`, μA `/1e6` (또는 nA `/1e9`), m°C `/1e3`, /100s `/100`
- **금지**: 표준 단위 (V) 외 변형 컬럼 (mV, kΩ 등) 을 `df.NewData` / 표준 프로파일에 박아 넣지 말 것 — 그래프 layer 에서만 변환

### D3 — DCIR 모드 사이클러별 정합

| 사이클러 | 모드 | 식별 신호 | UI flag |
|---|---|---|---|
| Toyo | 단일 | `Finish=Tim ∧ Cap<min/60 ∧ Cond=2` | `chkir` (일반/쌍 분기) |
| PNE | 일반 | `Cond=2 ∧ volmax>4.1V` | `chkir=True` |
| PNE | RSS + 1s pulse | `EndState=78/64 ∧ steptime/curr 조건` | `mkdcir=True` |
| PNE | 10s pulse | `Cond=2 ∧ steptime≤6000` | (default) |

- **신규 DCIR 패턴** 추가 시 코드 수정 측 영향 = mode flag 추가 + 회귀 fixture 갱신.

### D4 — Toyo 용량 시간적분 정합

- Toyo 는 누적 cap 컬럼 **부재** — 시간적분 (`Σ dt·next_I/3600 / mincap`) 으로 도출
- **shift(-1) 패턴** (`next_I`) — proto_:2249 — 변경 시 기존 BDT 출력 정합 깨짐. 절대 변경 금지.
- PNE는 raw 누적값 직접 사용 → Toyo만 시간적분.

### D5 — 캐시 무효화 = 사용자 명시

- 자동 invalidation 금지 — 시험 진행 중 file 갱신 케이스는 BDT 분석 모드 (완료 시험) 와 무관.
- 새 경로 감지 시 = UI 측 trigger ("새 경로 감지" 다이얼로그) 또는 재시작.

### D6 — 표준 출력 컬럼 schema 동결

`df.NewData` 사이클 출력 (10 + dcir + RndV split):

```
Cycle, Dchg, RndV, RndV_chg_rest, Eff, Chg, DchgEng, Eff2, Temp, AvgV, OriCyc, dcir
```

표준 프로파일 출력 (12 + 옵션):

```
Time_s, Voltage, Current_mA, Crate, Temp,
ChgCap, DchgCap, ChgWh, DchgWh,
Step, Condition, Cycle, [PhysicalCycle, OCV, CCV, Stepmode]
```

- 컬럼 추가 시 = ADR 박제 + 회귀 fixture 갱신. 컬럼 rename 시 = 절대 금지 (downstream 의존성 깨짐).

---

## 8. 알려진 한계

### 8.1 Toyo

- **신뢰성 충방전기 변종** — Temp 컬럼 부재. 현재 `TotlCycle` 을 `Temp1[Deg]` 로 alias (proto_:5246~5248) — **부정확하지만 NaN 폭발 차단용 fallback**. 분석 시 Temp 무시 정책.
- **NNNNNN 파일 5,954개/채널 max** ([[260509_audit_toyo_lifetime_full_inventory|260509 audit]]) — 풀 프로파일 로드 시 disk I/O 폭증. P2 lazy 정책 강제.
- **DCIR ThreadPool ≤ 4 workers** — NAS 환경 부하 방지. 채널 레벨 ThreadPool과 이중 부하 회피.

### 8.2 PNE

- **`.cyc` cold 캐시** — 첫 호출 50 ms (대형 채널). lru cache 보존 권장 (max 5~10 채널).
- **EndState 코드 사전 미공개** — DCIR `mkdcir` 분기의 78/64/66 magic number는 사외 공식 X (사내 검증 측만).
- **PNE21/22 코인셀** — `is_micro_unit` 분기 단일 진입점. 새 코인셀 환경 추가 시 분기 추가 필요.

### 8.3 공통

- **SOC 직접 측정 X** — 누적 cap / 명목 추정.
- **DCIR 정밀도** — 펄스 길이 / 측정 빈도 / sensor 노이즈 영향. 절대값 보다 **트렌드** 측 신뢰도 높음.

---

## 9. 회귀 검증 게이트

### 9.1 fixture (ADR-0008 정합)

| Fixture | 사이클 분석 측 | 프로파일 분석 측 |
|---|---|---|
| **(α) 표준 데이터 경로** | Toyo BLK3600 1ch + PNE 1ch | 동일 (sample 공유) |
| **(β) 전처리 골든** | `df.NewData` 12 컬럼 baseline parquet | 표준 프로파일 12+ 컬럼 baseline |
| **(γ) 그래프 골든** | 사이클 탭 PNG (DPI 100) | 프로파일 탭 PNG |
| **(δ) 저장 schema** | Excel 시트 cycle_data 컬럼·dtype 자동 점검 | profile_data 시트 검증 |

### 9.2 회귀 trigger

- 컬럼 추출 단일 진입점 변경 (`toyo_cycle_import`, `_unified_pne_load_raw` 등) → α + β + δ 갱신 필수
- 단위 정규화 식 변경 (`/1e6`, `/1000`, `Σ dt·I`) → β 즉시 깨짐 → 의도된 변경인지 확인
- DCIR 모드 분기 변경 → γ DCIR 그래프 깨짐 → 의도 확인

---

## 10. 핵심 코드 위치

### 사이클 분석

- `toyo_cycle_data` proto_:5289 — Toyo 메인
- `toyo_cycle_import` proto_:5257 — 10 컬럼 추출
- `toyo_read_csv` proto_:5211 — CAPACITY.LOG / NNNNNN read (lru cache)
- `toyo_min_cap` proto_:5272 — 기준 용량 산정
- `pne_cycle_data` proto_:11689 — PNE 메인
- `_process_pne_cycleraw` proto_:11221 — DCIR + pivot + df.NewData
- `get_channel_save_end_data` proto_:780 — Phase 0 캐시 진입

### 프로파일 분석

- `toyo_Profile_import` proto_:5237 — Toyo 단일 사이클 (5 컬럼)
- `_unified_toyo_load_raw` proto_:1988 — Toyo 멀티 사이클 통합 로더
- `_unified_normalize_toyo` proto_:2192 — Toyo 정규화 (시간적분)
- `_unified_pne_load_raw` proto_:1729 — PNE 통합 로더 (Layer A 단일화)
- `_unified_normalize_pne` proto_:2111 — PNE 정규화 (μV/μA/m°C → V/mA/°C)
- `_cached_pne_restore_files` proto_:1528 — Restore 캐시
- `unified_profile_core` proto_:3177 — 통합 프로파일 진입점

### 보조

- `is_micro_unit` proto_:741 — 코인셀 판별 (PNE 분기)
- `_get_channel_cache` proto_:863 — L1 캐시
- `ChannelMeta` proto_:380 — Phase 0 dataclass
- `_ensure_dcir_columns` proto_:1182 — 표준 DCIR 컬럼 보장
- `_ensure_rndv_split_columns` proto_:1201 — RndV / RndV_chg_rest 분리

---

## 11. Related

- [[260508_raw_data_schema_unified_reference]] — schema fact (raw 컬럼 inventory)
- [[260509_policy_toyo_data_operation]] — Toyo 운영 정책 (cp949, BLK 정규화, mincap 우선순위)
- [[260509_audit_toyo_lifetime_full_inventory]] — 실제 데이터 전수조사 (NNNNNN 분포)
- [[260409_study_02_toyo_cycle_data]] — Toyo 코드 라인별 분석
- [[260409_study_03_pne_cycle_data]] — PNE 코드 라인별 분석
- [[260410_study_pne_cyc_vs_csv_structure]] — `.cyc` warm/cold 벤치마크
- [[260411_analysis_cycle_pipeline_complete]] — 전체 사이클 파이프라인
- [[31_software_dev/adr/0008-bdt-test-and-study-automation|ADR-0008]] — 검증 fixture 4종

---

## 12. 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-09 | 최초 작성 — 사이클·프로파일 × Toyo·PNE 4 매트릭스 + 컬럼 추출 + 전처리 13/9/7/9 단계 + 컴퓨팅 벤치 + 정책 결정 D1~D6 + 회귀 게이트 |
