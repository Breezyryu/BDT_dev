---
title: "TOYO 수명 데이터 전수조사 — raw/raw_exp/exp_data/수명_Toyo"
date: 2026-05-09
tags: [audit, toyo, raw-data, inventory, anomaly, lifetime]
related:
  - "[[260508_raw_data_schema_unified_reference]]"
  - "[[260509_policy_toyo_data_operation]]"
  - "[[260409_study_02_toyo_cycle_data]]"
status: audit
---

# TOYO 수명 데이터 전수조사

> **대상**: `raw/raw_exp/exp_data/수명_Toyo/` 전수 (26 datasets, 156 channels, 358,847 NNNNNN files).
> **시점**: 2026-05-09.
> **목적**: schema reference (`260508`) 와 운영 정책 (`260509_policy`) 의 실제 데이터 정합 검증 + 신규 발견 file types 박제 + 운영 anomaly 식별.

---

## TL;DR

- **26 datasets / 156 channels / 358,847 NNNNNN files** — 모두 **BLK3600** (BLK5200 0건)
- **신규 file types 5종** 260508 reference 미등록 — `CHCMT.TXT` / `COMMON_ENV.CFG` / `LCOUNT.TMP` / `LCOUNT2.TMP` / `TEMP.LOG`
- **운영 anomaly 7건** — 빈 채널 4건 / capacity 불일치 1건 / multi-PTN 36 채널 / 폴더명 double-space 변형 / 1 채널 sub-dataset / LCOUNT 누락 9건 / TEMP.LOG 2건
- **CAPACITY.LOG 헤더 변종 2종**: 17 컬럼 (legacy) / 19 컬럼 (`DchCycle`+`PassedDate` 추가)
- **운영 정책 갱신 필요 4건** — 빈 채널 skip 강제 / multi-PTN 우선순위 정의 / 폴더명 capacity fallback 룰 / 신규 file types 무시 정책

---

## 1. 디렉토리 구조 모델

```
수명_Toyo/
├── <dataset_folder>/                      # 26개
│   ├── <name>.CMT                         # 보통 빈 파일 (운용 메모)
│   └── <channel_id>/                      # 채널 폴더 (digit-only) — 156개 합
│       ├── 000001 ~ NNNNNN                # step별 시계열 (358,847 합)
│       ├── <name>.PTN                     # 메인 schedule
│       ├── <name>_Option.PTN              # 셀 capacity
│       ├── <name>_Option2.PTN             # step별 안전 cutoff (BDT 미활용)
│       ├── CAPACITY.LOG                   # step row 메타
│       ├── CHCMT.TXT                      # ★ 신규 발견 (2 byte)
│       ├── COMMON_ENV.CFG                 # ★ 신규 발견 (~150 byte)
│       ├── LCOUNT.TMP                     # ★ 신규 발견 (~21 KB)
│       ├── LCOUNT2.TMP                    # ★ 신규 발견 (62 byte, BLK 변종)
│       └── TEMP.LOG                       # ★ 2 채널만 (특수 로깅)
```

---

## 2. 가족 분류 — 9 family

| family | datasets | channels | NNNNNN | 셀 | 시험 type | nominal mAh |
|---|---:|---:|---:|---|---|---:|
| **Q7M Inner 1689 김동진 RT2C 수명** | 4 | 8 | 3,976 | Q7M Inner ATL | 1-100·101-200·201-300·301-400 cyc 분할 | 1,689 |
| **Q7M Inner 1689 BLK1 가속수명** | 1 | 18 | 81,284 | Q7M Inner ATL | 가속 (BLK1 20EA) | 1,689 |
| **Q7M Main 1680 blk7 가속수명** | 1 | 20 | 82,253 | Q7M Main ATL | 가속 (blk7 20ea) | 1,680 |
| **Q7M Sub 2068 가속수명** | 1 | 18 | 84,796 | Q7M Sub ATL | 가속 (`-r` 변종) | 2,068 |
| **Gen4 4470 blk2** | 1 | 2 | 1,986 | Gen4 ATL MP2 | 23 °C | 4,470 |
| **Gen4 4470 blk7** | 1 | 6 | 32,751 | Gen4 ATL MP2 | 23 °C (240131) | 4,470 |
| **M1 4175** | 1 | 24 | 38,430 | M1 ATL | 23 °C | 4,175 |
| **김건희 SUS 245 수명** (1 space) | 7 | 28 | 17,435 | ATL JINJU SUS | 1-100…1000-1200 cyc 분할 | 245 |
| **김건희 SUS 245 장수명** (2 spaces) | 8 | 28 | 15,936 | ATL JINJU SUS | 1-100…901-1000 + `_32` sub | 245 |
| **김건희 SUS 222** (빈 채널) | 1 | 4 | **0** | ATL JINJU SUS | (시험 abort 추정) | 222→245 (mismatch) |
| **합계** | **26** | **156** | **358,847** | | | |

> **분류 키**:
> - `JINJU SUS` (single space) ↔ `JINJU  SUS` (double space) = 김건희 운영자가 수명 vs 장수명 구분에 폴더명 변형 사용 (의도적 — anomaly 아님).
> - `Q7M Inner` 두 family — 김동진 RT2C 100cyc 분할 (4 small datasets) vs BLK1 가속 (1 large 18ch).

---

## 3. 채널당 NNNNNN 분포

| 통계 | 값 |
|---|---:|
| 채널 수 | 156 |
| min | 0 (빈 채널 4) |
| p25 | 496 |
| p50 | 1,715 |
| p75 | 4,956 |
| max | 5,954 |
| 합계 | 358,847 |

> **운영 함의**: P2 lazy 정책 ([[260509_policy_toyo_data_operation|§4]]) 의 정당성 — max 5,954 step / channel preload 시 메모리 폭발. 첫 sampling 1개 (P1) + 요청 시 lazy load 정책 유지 정합.

---

## 4. File Type 인구센서스 (channel-level)

| Type | Count | size_min | size_med | size_max | Notes |
|---|---:|---:|---:|---:|---|
| `NNNNNN` (시계열) | **358,847** | — | — | — | step별 시계열 |
| `main.PTN` | 192 | 4,152 | 17,232 | 19,957 | 일부 채널 다중 PTN (anomaly A5) |
| `_Option.PTN` | 192 | 50 | 51 | 51 | 1줄 capacity |
| `_Option2.PTN` | 192 | 6,628 | 16,234 | 18,794 | BDT 미활용 (P3) |
| `CAPACITY.LOG` | 152 | 52,769 | 271,599 | 906,652 | 4 빈 채널 누락 |
| **★ `CHCMT.TXT`** | 156 | 2 | 2 | 2 | 채널 코멘트 (보통 빈 2 byte) |
| **★ `COMMON_ENV.CFG`** | 156 | 150 | 150 | 173 | 환경 설정 |
| **★ `LCOUNT.TMP`** | 147 | 10,793 | 10,793 | 21,431 | Loop 카운트 (9 채널 누락) |
| **★ `LCOUNT2.TMP`** | 64 | 62 | 62 | 62 | BLK 변종 의존 |
| **★ `TEMP.LOG`** | 2 | 276 | 276 | 276 | 특수 로깅 (M1/8, Q7M Sub/10) |

> **★ = 260508 reference 미등록**. 본 audit으로 확인된 신규 file types.

---

## 5. CAPACITY.LOG 헤더 변종

### 변종 A — 17 컬럼 (legacy)

```
Date,Time,Condition,Mode,Cycle,TotlCycle,Cap[mAh],PassTime,TotlPassTime,Pow[mWh],AveVolt[V],PeakVolt[V],,PeakTemp[Deg],Ocv,,Finish
```

발생: Q7M Inner 김동진 RT2C, 김건희 245mAh (수명·장수명 모두)

### 변종 B — 19 컬럼 (확장)

```
Date,Time,Condition,Mode,Cycle,TotlCycle,Cap[mAh],PassTime,TotlPassTime,Pow[mWh],AveVolt[V],PeakVolt[V],,PeakTemp[Deg],Ocv,,Finish,DchCycle,PassedDate
```

발생: Q7M Inner BLK1, Q7M Main blk7, Q7M Sub, Gen4, M1

> **운영 함의**: 둘 다 **BLK3600** 계열 (`Cap[mAh]` 짧은 이름). 19 컬럼 확장은 BLK 변종이 아닌 **펌웨어 버전 차이**로 추정. `toyo_cycle_import` 의 alias map 은 두 변종 모두 처리해야 함 — 17 컬럼에서 `DchCycle`/`PassedDate` 누락은 정상.

---

## 6. ★ Anomaly 7건 박제

### A1 — 빈 채널 4건 (NNNNNN=0, CAPACITY.LOG 부재)

```
260115_260130_3_김건희_222mAh_ATL JINJU SUS 상온수명 1-100/{18, 19, 20, 21}
```

**가설**: 시험 시작 직후 abort 또는 data wipe.
**운영 결정**: `NNNNNN==0 ∧ CAPACITY.LOG 부재` → **자동 skip + 경고 로그**.

### A2 — 폴더명 vs `_Option.PTN` capacity 불일치 1건

| 폴더명 mAh | Option.PTN mAh | 위치 |
|---:|---:|---|
| **222** | **245** | `260115_260130_3_김건희_222mAh_ATL JINJU SUS 상온수명 1-100` |

**가설**: 폴더명 typo (222 → 245) — 빈 채널이라 데이터 영향 없으나 metadata 정합 깨짐.
**운영 결정**: capacity 산정 우선순위 = `_Option.PTN` > 폴더명. 폴더명은 fallback 만 — 본 anomaly 가 정책 정당성 입증.
→ [[260509_policy_toyo_data_operation|§11]] mincapacity 산정 정책 측 신호.

### A3 — 김건희 245mAh 폴더명 double-space 변형 (의도적)

```
JINJU SUS  (1 space) → 수명     (1-100, 101-200, ..., 1000-1200)  7 datasets
JINJU  SUS (2 spaces) → 장수명  (1-100, 101-200, ..., 901-1000)   8 datasets
```

**판정**: anomaly 아님 — 김건희 운영자가 수명/장수명 구분에 의도적 변형 사용.
**운영 결정**: 폴더명 trim/whitespace-normalize 시 두 시험을 하나로 collapse 하지 말 것 — `os.path.basename` 그대로 사용.

### A4 — 1 채널 sub-dataset 1건

```
260420_260430_3_김건희_245mAh_ATL JINJU  SUS 상온장수명 901-1000_32  (1 channel: 32)
```

**가설**: 본 dataset (`901-1000`, 3 ch) 에서 ch=32 만 별도로 분리 보관. 시험 종료 시점이 다르거나 추가 검증용.
**운영 결정**: 본 dataset 의 ch=32 와 sub-dataset 의 ch=32 가 **동일 채널 다른 시점인지 / 다른 채널인지** 김건희 확인 필요. 자동 dedup 금지 — 사용자 확인 전까지 별도 dataset 처리.

### A5 — multi-PTN 36 채널

| 가족 | 채널 수 | 두 PTN |
|---|---:|---|
| Q7M Inner BLK1 | 18 | `... 250206.PTN` + `... 250304.PTN` |
| Q7M Sub | 18 | `... 250219.PTN` + `... 250219r.PTN` |

**가설**: 시험 schedule 재정의 (250206 → 250304 1개월 후 갱신, 250219 → 250219r reverse?). 두 PTN 중 어느 것이 실제 적용됐는지 코드가 결정해야 함.
**운영 결정 (제안)**:
- 1순위 = 폴더명과 매칭되는 PTN (`Q7M Inner ATL_45V 1689mAh BLK1 20EA [23] - 250304` → `... 250304.PTN`)
- 2순위 = `mtime` 최신
- 3순위 = ASCII 사전순 마지막
- → [[260509_policy_toyo_data_operation|§6.3]] PTN 슬롯 분리 단일 진입점 정책에 multi-PTN 우선순위 추가 필요.

### A6 — LCOUNT.TMP 누락 9 채널

```
김건희 222mAh 1-100/{18, 19, 20, 21}              (빈 채널 — A1 정합)
Gen4 blk7 - 240131/{11, 12, 13, 14, 15}          (5 채널 — 펌웨어 변종?)
```

**판정**: 빈 채널 4 + Gen4 blk7 5 채널. 후자 5 채널은 데이터 정상 (NNNNNN 多) 이지만 LCOUNT.TMP 만 부재 → 펌웨어 차이 또는 운영 시점 차이.
**운영 결정**: `LCOUNT.TMP` 는 BDT 운영 측 미사용 (P3) — 부재해도 무영향.

### A7 — TEMP.LOG 2 채널

```
M1 ATL [45V 4175mAh]/8
Q7M Sub ATL [45v 2068mAh] [23] - 250219r/10
```

**판정**: 2 channel만 존재. 특수 온도 로깅 추정 — 별도 챔버 sensor 또는 진단 데이터.
**운영 결정**: BDT 운영 측 미사용 (P3) — parser 추가 시 family 식별자로 활용 검토.

---

## 7. 운영 정책 갱신 권고 (260509_policy → 갱신)

### G1 — 빈 채널 자동 skip 룰 추가

`§ 신설 9.1` 또는 `§4.5` 측에 박제:

```
빈 채널 정의: NNNNNN 파일 0개 ∧ CAPACITY.LOG 부재
→ BDT 자동 skip + 경고 로그 (silent skip 금지)
→ 가족 분류 시 카운트 제외
```

### G2 — multi-PTN 우선순위 (§6.3 확장)

기존:
> `_parse_ptn_step` 의 슬롯 분리 로직 단일 진입 — 다른 곳에서 PTN 직접 슬라이싱 금지

**추가**:
> `_find_ptn_file()` (proto_:7221) 다중 매치 시 우선순위:
> 1. 폴더명과 base name 매칭되는 PTN
> 2. `os.path.getmtime()` 최신
> 3. ASCII 사전순 마지막

### G3 — capacity 산정 우선순위 명시 (§11 보강)

기존:
> `mincapacity == 0` ∧ 경로에 `mAh` 포함 → `name_capacity()` 정규식 추출

**보강**:
> 1순위 = `_Option.PTN` `Pattern_BaseCellCapacity` (실제 시험 적용 값)
> 2순위 = 경로 `mAh` 정규식 (운영자 폴더명 — typo 가능)
> 3순위 = 첫 사이클 max 전류 / `inirate`
>
> A2 anomaly (222 폴더 vs 245 PTN) 가 본 우선순위 정당성 입증.

### G4 — 신규 file types 무시 명시

`§13` 알려진 한계 측에 추가:
> `CHCMT.TXT` / `COMMON_ENV.CFG` / `LCOUNT.TMP` / `LCOUNT2.TMP` / `TEMP.LOG` — Toyo 충방전기 운영 측 보조 파일. **BDT 미사용 (P3)** — parser 추가 금지, 향후 family 식별자 활용 검토 시 재평가.

---

## 8. 260508 schema reference 갱신 권고

`260508_raw_data_schema_unified_reference.md §2.1` 측 Toyo 파일 인벤토리 표 보강:

| 파일 | 형식 | 크기 (대표) | 역할 |
|---|---|---|---|
| (기존 6 항목 유지) | | | |
| `CHCMT.TXT` | text | 2 byte | 채널 코멘트 (보통 빈 파일) |
| `COMMON_ENV.CFG` | key=value | ~150 byte | 운영 환경 설정 |
| `LCOUNT.TMP` | binary | ~10~20 KB | Toyo loop 카운트 (BDT 미사용) |
| `LCOUNT2.TMP` | binary | 62 byte | BLK 변종 측 (BDT 미사용) |
| `TEMP.LOG` | CSV | ~280 byte | 특수 온도 로깅 (2 채널만) |

---

## 9. 데이터 무결성 결론

### 양호

- **BLK 균질** — 156/156 BLK3600 (변종 분기 부담 없음)
- **TotlCycle ↔ NNNNNN 정합** — sample 검증 (`first_tc=1`, `last_tc=NNNNNN.count`)
- **capacity 일관** — 1 mismatch 외 25/26 dataset 폴더명 ↔ Option.PTN 일치
- **cp949 인코딩** — 모든 텍스트 파일 cp949 정상 디코딩 (sanity 통과)
- **multi-PTN 운영 의도 명확** — 같은 시험 schedule 갱신 흔적 (250206→250304 / 250219→250219r)

### 주의

- 222mAh dataset = 빈 채널 4건 + capacity mismatch — **시험 미시작 abort 폴더**. 사용자 (김건희) 측 처분 결정 필요 (보존? 정리?).
- 245mAh `_32` sub-dataset — 본 dataset (`901-1000`) 과 dedup 가능 여부 사용자 확인 필요.
- `장수명` 폴더 7건 / `수명` 폴더 7건 — 동일 cyc range 의 sister datasets. **시험 protocol 다른지 / 같은지** 확인 필요 (PTN content 비교 측 후속 audit 가능).

---

## 10. 후속 작업 (옵션)

- **F1 — multi-PTN content diff**: A5 의 36 채널 multi-PTN 두 파일을 byte-level diff → schedule 갱신 내역 박제.
- **F2 — 김건희 수명 vs 장수명 PTN diff**: family 별 PTN content 비교 → 운영 protocol 차이 정리.
- **F3 — pytest fixture α 등록**: 본 26 dataset 中 sample 1~2개를 `tests/data_toyo_sample/` 에 in-repo 추가 (사외 PC subset, [[31_software_dev/adr/0008-bdt-test-and-study-automation|ADR-0008]] 정합).
- **F4 — 빈 채널 skip 코드 구현**: `is_pne_folder()` 의 음의 분기 측 + `NNNNNN==0` 자동 skip layer.
- **F5 — 김건희 ch=32 dedup 결정**: 사용자 확인 후 정책 박제.

---

## 11. Related

- [[260508_raw_data_schema_unified_reference]] — schema fact (갱신 권고 §8)
- [[260509_policy_toyo_data_operation]] — 운영 정책 (갱신 권고 §7)
- [[260409_study_02_toyo_cycle_data]] — Toyo 코드 라인별 분석
- [[260411_analysis_cycle_concepts_unification]] — TC / 논리 / UI 사이클 통일

---

## 12. 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-09 | 최초 작성 — 26 datasets 156 channels 358K NNNNNN 전수조사 + anomaly 7 + 정책 갱신 권고 4 |
