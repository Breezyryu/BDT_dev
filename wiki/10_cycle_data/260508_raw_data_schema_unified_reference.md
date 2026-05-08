---
title: "Raw Data Schema 통합 Reference — Toyo · PNE 추출 가능 정보 전체"
date: 2026-05-08
tags: [reference, raw-data, toyo, pne, schema, ptn, sch, capacity-log, save-end-data]
related:
  - "[[260504_audit_phase0_extractable_fields]]"
  - "[[260409_study_02_toyo_cycle_data]]"
  - "[[260409_study_03_pne_cycle_data]]"
  - "[[260410_study_pne_cyc_vs_csv_structure]]"
status: reference
---

# Raw Data Schema 통합 Reference

> Toyo · PNE 양 시스템의 **모든 raw 파일에서 추출 가능한 정보** 전체 정리.
> 사이클 정의 6 차원 (D1~D6) + 6 카테고리 (initial/RPT/Rss/GITT/HPPC/가속수명) 결정에 사용.
> 검증: BDT 본 코드 + 실제 raw sample (Q7M Inner 1-100cyc / channel 30, M01Ch008).

---

## TL;DR

- **Toyo 5종 + PNE 6종** raw 파일 schema 전부 매핑
- **6 차원** (phase·mode·단계수·C-rate·cutoff·sampling) 모두 P0+P1 자원으로 추출 가능
- **6 카테고리** 결정 — HPPC만 D6 sampling 측정 1회 추가 필요
- **Toyo·PNE 동등성 검증**: 11/12 항목 동등, **시험 환경 온도(chamber)만 Toyo 누락**
- 자원 정책: P0(< 100ms 항상) / P1(그룹별 1회) / P2(요청 시 lazy)

---

## 1. 파일 인벤토리 (채널당)

### Toyo

| 파일 | 형식 | 크기 (대표) | 역할 |
|---|---|---|---|
| `<name>.PTN` | text 고정폭 | 1~5 KB | 메인 schedule (chg+dchg+loop) |
| `<name>_Option.PTN` | key=value | ~50 byte | 셀 capacity |
| `<name>_Option2.PTN` | CSV | 5~50 KB | step별 안전 cutoff (현재 미활용) |
| `CAPACITY.LOG` | CSV (17/19 col) | 50~750 KB | step row 메타 |
| `NNNNNN` (6자리 0-패딩) | CSV | 1~250 KB · N | 시계열 per step (N=TotlCycle 최대) |
| `<name>.CMT` | text | ~2 byte | 보통 빈 파일 |

**채널 폴더명**: 숫자만 (`30`, `31`, `11`, ...)

### PNE

| 파일 | 형식 | 크기 (대표) | 역할 |
|---|---|---|---|
| `<name>.sch` | binary | 10~50 KB | 메인 schedule (1920 + 652·N bytes) |
| `<name>.cyc` | binary | ~1 MB | sweep 시계열 (gap-fill용) |
| `<name>.db` | binary | 작음 | 메타 (현재 미사용) |
| `<name>.log` | text | 작음 | 운용 로그 (현재 미사용) |
| `Restore/<ch>_SaveEndData.csv` | CSV (헤더 X, 48+ col) | 10~500 KB | step row 메타 |
| `Restore/<ch>_SaveData<NNNN>.csv` | CSV (동일 schema) | 0.5~5 MB · N | 시계열 batch |

**채널 폴더명**: `M01Ch008[008]` 형태 (`is_pne_folder()` L555)

---

## 2. Toyo 파일별 상세

### 2.1 `<name>.PTN` — 메인 schedule

**형식**: 1줄 헤더 + 1줄/step. **한 줄에 chg slot (앞 ~256 char) + dchg slot (뒷 ~280 char) 동시 인코딩**.

**Mode 코드** (BDT `_parse_ptn_step` L7251 검증):

| 코드 | 의미 |
|---|---|
| `00` | CC |
| `10` | CCCV |
| `30` | Rest |

**고정폭 위치**:

| 필드 | 위치 | 단위 | 의미 |
|---|---|---|---|
| chg_mode | `[1:4]` | code | 00/10/30 |
| chg_current_mA | `[5:15]` | mA | CC 전류 |
| chg_cv_voltage | `[17:23]` | V | CCCV 목표 전압 |
| chg_cc_endvolt | `[32:39]` | V | CC 종료 전압 |
| **chg_cutoff_mA** | `[55:63]` | mA | **CV 종료 전류 (i_cutoff)** |
| chg_rest_min | `[106:111]` | min | 충전 후 휴지 |
| dchg_mode | `[262:266]` | code | 00/10/30 |
| dchg_current_mA | `[268:276]` | mA | 방전 CC 전류 |
| dchg_endvolt | `[311:318]` | V | 방전 종료 전압 |
| dchg_rest_min | `[361:366]` | min | 방전 후 휴지 |
| **loop_to** | `[535:539]` | step# | "이 step에서 step N으로 loop" |
| **loop_count** | `[539:543]` | int | 반복 횟수 |

### 2.2 `<name>_Option.PTN` — 셀 옵션

```
[BaseCellCapacity]
Pattern_BaseCellCapacity=1689
```

**추출**: 공칭 용량 (mAh) — C-rate 계산 기준

### 2.3 `<name>_Option2.PTN` — step별 옵션

- CSV, 1줄/step, 350+ 컬럼
- 안전 cutoff 임계값 (T_max, T_min, V_max, V_min 등 추정)
- **현재 BDT 미활용** — 보강 대상

### 2.4 `CAPACITY.LOG` — 사이클 메타

**컬럼 (헤더 가변, 17 또는 19)**:

| # | 이름 | 의미 |
|---|---|---|
| 0 | Date | step 종료 일자 |
| 1 | Time | step 종료 시각 |
| 2 | **Condition** | 1=충전, 2=방전 (rest는 row 없음) |
| 3 | **Mode** | PTN step 번호 (capacity.log↔PTN 매핑 키) |
| 4 | Cycle | (대부분 1로 고정 — 신뢰 X) |
| 5 | **TotlCycle** | 누적 step 카운터 (NNNNNN 파일명 ↔ 1:1) |
| 6 | **Cap[mAh]** | step 측정 용량 |
| 7 | PassTime | step 지속 시간 (HHH:MM:SS) |
| 8 | TotlPassTime | 누적 시간 |
| 9 | Pow[mWh] | 에너지 |
| 10 | AveVolt[V] | 평균 전압 |
| 11 | PeakVolt[V] | 최대/최종 전압 |
| 13 | PeakTemp[Deg] | 최대 온도 |
| 14 | Ocv | step 직전 OCV |
| 16 | **Finish** | `Vol`(V cutoff) / `Cur`(I cutoff = CV 종료) |
| 17, 18 | DchCycle, PassedDate | (19 컬럼 버전만) |

### 2.5 `NNNNNN` — 시계열 per step

**파일 구조**:
- Line 1: 메타 (`0,0,1,0,0,0,0` 7 정수, step 시작 마커 추정)
- Line 2~3: 빈
- Line 4: 컬럼 헤더
- Line 5~: 시계열 데이터

**컬럼 (16개)**:

| # | 이름 | 의미 |
|---|---|---|
| 0, 1 | Date, Time | 측정 시각 |
| 2 | **PassTime[Sec]** | step 시작부터 누적 초 |
| 3 | **Voltage[V]** | 단자 전압 |
| 4 | **Current[mA]** | 전류 (부호 없음 — Condition으로 방향) |
| 7 | Temp1[Deg] | 셀 온도 |
| 11 | **Condition** | 1=charge, 2=discharge, 3=rest |
| 12 | Mode | PTN step 번호 |
| 13 | Cycle | 사이클 카운터 |
| 14 | TotlCycle | 누적 step 카운터 |
| 15 | Temp1[Deg] | (중복) |

### 2.6 `<name>.CMT`

- 텍스트, 보통 빈 파일 (운용자 메모)
- **추출 없음**

---

## 3. PNE 파일별 상세

> PNE `.sch` binary 정밀 분석은 [[260504_audit_phase0_extractable_fields]] 참조.
> 본 절은 통합 reference용 요약.

### 3.1 `<name>.sch` — schedule binary

**구조**: 1920 byte 헤더 + 652 byte/step 고정.

**헤더 핵심** (offset):

| Offset | 의미 |
|---|---|
| `+0` | magic = 740721 |
| `+336` | user_category (cp949) |
| `+664` | **schedule description (시험명, ASCII)** ⭐⭐⭐ |
| `+728` | comment (ASCII) |

**Step block 핵심** (offset):

| Offset | 의미 |
|---|---|
| `+0` | StepNumber |
| **`+8`** | **TypeCode** (`0x0101`=CC, `0x0201`=CV, `0x0401`=REST, `0x0501`=LOOP, ...) |
| `+12` | 충전 V cutoff (mV) |
| `+16` | 방전 V cutoff (mV) |
| `+20` | I cutoff (mA) |
| `+24` | Time limit (sec) |
| **`+56`** | LOOP count |
| **`+396`** | chamber_temp_C (float32) — **시험 환경 온도, Toyo엔 없음** |
| `+500` | end_condition_type |

### 3.2 `<name>.cyc` — sweep binary

- float32 records 시계열
- SaveData 누락 구간 gap-fill에 사용
- BDT `_cached_pne_restore_files` (L1482) 의존

### 3.3 `<name>.db` / `<name>.log`

- 현재 미사용

### 3.4 `Restore/<ch>_SaveEndData.csv` — step 메타

**형식**: 헤더 없음, 정수 인코딩, 48+ 컬럼.

**핵심 컬럼**:

| # | 이름 | 인코딩 |
|---|---|---|
| 0 | Index | int |
| 1 | **Stepmode** | 2=CC, 3=CV |
| 2 | **Condition** | 1=충전, 2=방전, 3=휴지 |
| 7 | StepNo | step 번호 |
| 8 | Voltage | μV (/1e6 = V) |
| 9 | Current | μA signed (/1e6 = A) |
| 10 | ChgCap | μAh |
| 11 | DchgCap | μAh |
| 14 | ChgWh | μWh |
| 15 | DchgWh | μWh |
| 17 | StepTime | ×0.01 s |
| 19 | TotTime_Sec | ×0.01 s |
| 21 | Temp1 | m°C (/1e3) |
| 27 | **TotlCycle** | 누적 사이클 (Toyo TotlCycle 대응) |

### 3.5 `Restore/<ch>_SaveData<NNNN>.csv` — 시계열

- SaveEndData와 **동일한 schema**
- 차이: 시계열 (1 step = 다수 row)
- PNE 자동 분할 (1~10 cycle/file 비고정)

---

## 4. 6 차원 추출 매트릭스

| 차원 | Toyo Primary | PNE Primary |
|---|---|---|
| **D1 phase 구조** | `CAPACITY.LOG.Condition` | `SaveEndData.Condition` |
| **D2 전류 인가 방식** | `PTN.chg_mode` (00/10/30) | `.sch.TypeCode` (0x0101/0x0201/0x0401) |
| **D3 단계 수** | LC 내 row 수 | LC 내 StepNo 수 |
| **D4 C-rate** | `PTN.chg_current_mA` / nominal_cap | `.sch` current / nominal_cap |
| **D5 V cutoff** | `PTN.chg_cv_voltage` 등 | `.sch +12/+16` |
| **D5 I cutoff** | **`PTN.chg_cutoff_mA`** ← capacity.log엔 없음 | `.sch +20` |
| **D5 time cutoff** | (PTN 일부 step) | `.sch +24` |
| **D6 sampling 주기** | NNNNNN PassTime diff (1회) | SaveData TotTime_Sec diff (1회) |
| **휴지 시간** | `PTN.chg_rest_min` / `dchg_rest_min` | `.sch` REST step time limit |
| **셀 온도** | `CAPACITY.LOG.PeakTemp` + NNNNNN | `SaveEndData.Temp1` + SaveData |
| **시험 환경 온도** | ❌ (PTN/Option에 없음) | ✅ `.sch +396 chamber_temp_C` |
| **OCV** | `CAPACITY.LOG.Ocv` | SaveEndData (rest 종료 V) |
| **공칭 용량** | `_Option.PTN BaseCellCapacity` | dataset 경로명 또는 `.sch` |

---

## 5. Toyo ↔ PNE 동등성

| 개념 | Toyo | PNE | 동등성 |
|---|---|---|---|
| Schedule 정의 | `.PTN` (text) | `.sch` (binary) | ✅ |
| 셀 capacity | `_Option.PTN` | `.sch` 또는 경로 | ✅ |
| Step 메타 요약 | `CAPACITY.LOG` | `SaveEndData.csv` | ✅ |
| Step 시계열 | `NNNNNN` (1 file/step) | `SaveData<NNNN>.csv` (batch) | ⚠️ 분할 단위 다름 |
| CC vs CV 식별 | PTN `chg_mode` 명시 | `TypeCode` + Stepmode 명시 | ✅ |
| **CV 종료 전류** | PTN `chg_cutoff_mA` 명시 | `.sch +20` 명시 | ✅ |
| 휴지 시간 | PTN `*_rest_min` 명시 | `.sch` REST step | ✅ |
| 명시적 loop | PTN `loop_to` + `loop_count` | LOOP step + `+56` | ✅ |
| 누적 step 카운터 | `TotlCycle` | `TotlCycle` (col 27) | ✅ |
| **시험 환경 온도** | ❌ | ✅ `.sch +396` | ❌ Toyo 누락 |
| 사이클 카운터 (논리) | (Cycle col 신뢰 X) → LC 매핑 | `_build_pne_cycle_map` (L5903) | ⚠️ 양쪽 매핑 필요 |
| Step 종료 사유 | `Finish` (Vol/Cur/Tim) | EndState 코드 | ✅ |

**Toyo 누락 보강 방안**:
- 시험 환경 온도 → dataset 경로명 ("상온수명", "고온") 추출 또는 외부 yaml

---

## 6. 카테고리 결정 신호 (P0+P1 자원만 사용)

| 카테고리 | Toyo 결정 신호 | PNE 결정 신호 |
|---|---|---|
| **initial** | LC 첫 step + Cond=2 only | LC 첫 step + 첫 row Cond=2 |
| **RPT** | PTN: chg=0.2C±0.05 + CCCV / cap.log: chg_c_max ∈ [0.15, 0.25] + Finish=Cur | `.sch`: TypeCode CC, current=0.2C + CV step / SaveEndData stepmode=2/3 |
| **Rss** | PTN: 짧은 chg/dchg (time<5min) | `.sch`: time limit < 300s + 단일 step |
| **GITT** | PTN: 다단 chg + 긴 rest (>=60min) + loop_count high | `.sch`: 다단 CC + REST > 1h |
| **HPPC** | NNNNNN sampling 0.1s + 짧은 chg+dchg pulse pair | `.sch`: 짧은 chg+dchg + sampling 0.1s |
| **가속수명** | PTN: 다단 chg (n≥2) + loop_count high (≥20) | `.sch`: 다단 CC/CV + LOOP step count ≥20 |

**결정 가능성 매트릭스**:

| 카테고리 | D1 | D2 | D3 | D4 | D5 V | D5 I | D6 | 결정 가능? |
|---|---|---|---|---|---|---|---|---|
| initial | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | (P2) | ✅ |
| RPT | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | (P2) | ✅ |
| Rss | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | (P2) | ✅ |
| 가속수명 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | (P2) | ✅ |
| GITT | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | 부분 (rest 시간으로 추정) |
| HPPC | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | **D6 필요 → P2 sampling 1회 측정으로 대체** |

→ **결론**: P0+P1 자원만으로 6 카테고리 모두 결정 가능. 단 dataset당 NNNNNN 1개 sampling 측정 필요 (HPPC의 D6 변별).

---

## 7. 자원 정책 (제 1원칙: 컴퓨팅 부담 최소화)

| 파일 | 비용 | 권장 |
|---|---|---|
| Toyo `.PTN` | < 1ms | **P0 항상** |
| Toyo `_Option.PTN` | < 1ms | **P0 항상** |
| Toyo `_Option2.PTN` | 5ms | **현재 미사용** |
| Toyo `CAPACITY.LOG` | 5~25ms | **P0 항상** |
| Toyo `NNNNNN` (1개) | 1~10ms | **P1 sampling 1회**, 나머지 **P2 lazy** |
| PNE `.sch` | 5~10ms | **P0 항상** |
| PNE `SaveEndData.csv` | 10~50ms | **P0 항상** |
| PNE `SaveData<NNNN>` | **무거움** | **P2 lazy** (사용자 요청 시) |
| PNE `.cyc` | 50ms+ | gap-fill 시만 |

**P0 + P1 합계 (채널당)**: ~100ms 이하 (검증: Q7M Inner BLK1 1003 LCs = 210ms with 캐시)

**캐싱**: `functools.lru_cache` 활용 (BDT 본 코드 패턴, 예: `toyo_read_csv` L5095, `_cached_pne_restore_files` L1482)

---

## 8. 알려진 한계

### 8.1 Toyo

- 시험 환경 온도(D7) 누락 → 경로명/yaml로 보강
- `Cycle` 컬럼 신뢰도 X (대부분 1 고정) → LC 매핑 v2로 도출
- Rest step row 부재 → PTN `*_rest_min` 또는 NNNNNN 시계열로만
- PTN 한 줄에 chg+dchg 모두 인코딩 → 사용 안 한 slot은 0/dash
- `_Option2.PTN` 미해석
- 신뢰성 시험 일부 `.xls` Fasoo DRM (사외 환경 불가)

### 8.2 PNE

- SaveData 분할 기준 비고정 (1~10 cycle/file) → stitching 로직 필요
- 20+ 컬럼 sparse — EndState 코드 사전 외부 미공개
- `.cyc` gap-fill 로직 복잡
- 채널 폴더명 변형 (`M01Ch008[008]` 외 변종)

### 8.3 공통

- SOC 직접 측정 X (cap 누적/명목 추정)
- DCIR 별도 알고리즘 필요 (`toyo_cycle_data` L5167~)
- EIS 데이터 없음 (별도 측정)

---

## 9. 핵심 코드 위치

### Toyo
- `_parse_ptn_step` (L7251) — PTN 한 줄 파싱
- `_find_ptn_file` (L7221) — 메인 PTN 파일 탐색
- `_read_ptn_option_capacity` (L7235) — `_Option.PTN` capacity 읽기
- `extract_toyo_ptn_structure` (L7427) — 시험유형 판별
- `toyo_read_csv` (L5095) — capacity.log + NNNNNN 파일 읽기 (lru_cache)
- `toyo_Profile_import` (L5115) — 시계열 임포트
- `toyo_build_cycle_map` (L5519) — 논리사이클 매핑

### PNE
- `_unified_pne_load_raw` (L1695) — 시계열 통합 로더
- `_cached_pne_restore_files` (L1482) — SaveEndData + .cyc gap-fill
- `_parse_pne_sch` (L8027) — schedule binary 파싱
- `_parse_cyc_header` (L9532) — .cyc binary 헤더
- `_cyc_to_cycle_df` (L9696) — .cyc → DataFrame
- `_build_pne_cycle_map` (L5903) — 논리사이클 매핑
- `is_pne_folder` (L555) — 채널 폴더 판별

### 공통
- `LogicalCycleGroup` (L315) — 논리사이클 그룹 dataclass
- `ChannelMeta` (L332) — Phase 0 캐시 객체
- `get_cycle_map` (L9271) — 통합 진입점

---

## 10. Related

- [[260504_audit_phase0_extractable_fields]] — PNE `.sch` binary 정밀 분석 (4 sample, header/step 모든 byte)
- [[260504_audit_phase0_sch_parsing_gap]] — PNE parser gap audit
- [[260409_study_02_toyo_cycle_data]] — Toyo 사이클 데이터 학습
- [[260409_study_03_pne_cycle_data]] — PNE 사이클 데이터 학습
- [[260410_study_pne_cyc_vs_csv_structure]] — PNE `.cyc` vs CSV 구조
- [[260411_analysis_cycle_pipeline_complete]] — 전체 사이클 파이프라인
- [[260321_review_cycle_classification_logic]] — 분류 로직 (RPT/Rss/GITT)
- 허브 → [[hub_cycle_pipeline]] · [[hub_logical_cycle]]

---

## 11. 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-08 | 최초 작성 — Toyo + PNE 통합 reference, 6 차원 매트릭스, 동등성 표 |
