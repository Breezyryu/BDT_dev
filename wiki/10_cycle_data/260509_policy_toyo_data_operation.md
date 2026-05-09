---
title: "TOYO 데이터 운영 정책 — PNE 차이 측 결정 박제"
date: 2026-05-09
tags: [policy, toyo, raw-data, operation, pne-comparison, capacity-log, ptn]
related:
  - "[[260508_raw_data_schema_unified_reference]]"
  - "[[260409_study_02_toyo_cycle_data]]"
  - "[[260409_study_03_pne_cycle_data]]"
  - "[[260410_study_pne_cyc_vs_csv_structure]]"
  - "[[260411_analysis_cycle_concepts_unification]]"
  - "[[31_software_dev/adr/0008-bdt-test-and-study-automation|ADR-0008]]"
status: policy
---

# TOYO 데이터 운영 정책

> **위치 부여**: schema 정리 = `260508_raw_data_schema_unified_reference` (사실).
> 본 문서 = 그 위의 **운영 결정** 박제. PNE 와의 차이가 운영 차이를 만드는 지점만 정책화.
> SSOT — 향후 Toyo 데이터 operation 변경 시 본 문서를 갱신.

---

## TL;DR

- **PNE 와 운영 차이 4 핵심**: (1) text PTN vs binary `.sch` (2) 1 step = 1 NNNNNN 파일 vs batch SaveData (3) chamber 온도 부재 (4) Cycle 컬럼 신뢰 X
- **자원 정책**: P0 = `PTN` + `_Option.PTN` + `CAPACITY.LOG`. P1 = `NNNNNN` 1개 (D6 sampling). 나머지 **P2 lazy**
- **인코딩**: cp949 강제 (auto-detect 금지)
- **Logical Cycle**: `TotlCycle` 만 신뢰 — `Cycle` 컬럼은 사용 금지
- **Chamber 온도 보강**: 1순위 = 경로명 정규식, 2순위 = 외부 yaml (현재 미구현 — Decision 8)
- **DCIR 식별**: `Finish ∈ {Tim, Time}` ∧ `Cap < mincapacity/60` ∧ `Condition=2` 3 조건 AND
- **검증 게이트**: pytest fixture α/β/γ/δ ([[31_software_dev/adr/0008-bdt-test-and-study-automation|ADR-0008]]) — Toyo subset 필수

---

## 1. PNE 차이 — 운영 차이 매트릭스

| 영역 | Toyo | PNE | 운영 영향 |
|---|---|---|---|
| schedule 형식 | text `.PTN` (cp949 고정폭) | binary `.sch` (offset+TypeCode) | Toyo = 정규식 / 고정폭 슬라이스. PNE = struct unpack |
| 시계열 분할 | **1 step = 1 NNNNNN 파일** | batch (1~10 cycle/파일) | Toyo = filesystem I/O 지배. PNE = csv 파싱 + stitching |
| 메타 요약 | `CAPACITY.LOG` (헤더 있음, 17/19 col) | `SaveEndData.csv` (헤더 없음, 48+ col) | Toyo = pandas read_csv. PNE = positional 매핑 |
| chamber 온도 | ❌ 없음 | ✅ `.sch +396` | Toyo = **외부 보강 필수** (Decision 8) |
| Rest step row | ❌ CAPACITY.LOG에 없음 | ✅ SaveEndData에 있음 | Toyo = PTN `*_rest_min` 또는 NNNNNN 시계열로 우회 |
| Cycle 컬럼 | 1 고정 — **신뢰 X** | TotlCycle 정상 | Toyo = `TotlCycle` 만, `Cycle` 무시 |
| 모델 변종 | BLK3600 / BLK5200 컬럼명 다름 | PNE 단일 | Toyo = 컬럼 정규화 layer 필수 |
| 인코딩 | **cp949** (한국어 Windows) | binary | Toyo = `encoding='cp949'` 강제 |
| 채널 폴더명 | 숫자만 (`30`, `11`, ...) | `M01Ch008[008]` 패턴 | 판별 함수 분기 — `is_pne_folder()` L555 |
| 미활용 자산 | `_Option2.PTN`, `.CMT` | `.db`, `.log` | 양쪽 모두 P3 (보강 후보) |

---

## 2. 데이터 수집 정책

### 2.1 채널 폴더 발견

- **Toyo 채널 = 폴더명이 숫자만** 인 폴더 (예: `Z:/Toyo1/30`)
- 발견 함수 = `is_pne_folder()` 의 음의 분기
- **결정**: 새 cycler (Arbin 등) 추가 시에는 별도 판별 함수 분기 — Toyo digit-only 규칙은 손대지 않음

### 2.2 raw 파일 인벤토리 (채널당)

- `<name>.PTN` — 메인 schedule (P0 항상)
- `<name>_Option.PTN` — 셀 capacity (P0 항상)
- `<name>_Option2.PTN` — step별 cutoff (현재 **미활용**, P3 보강 후보)
- `CAPACITY.LOG` — step row 메타 (P0 항상)
- `NNNNNN` 6자리 0-패딩 — 시계열 per step (P1 sampling 1개 + P2 lazy 나머지)
- `<name>.CMT` — 보통 빈 파일 (P3 무시)

### 2.3 경로 입력 convention

- **결정**: 사용자가 **채널 폴더 경로** 입력 (예: `Z:/Toyo1/30`)
  - 부모 폴더 (`Z:/Toyo1`) 입력 시 = 자동 채널 발견 모드 (현황 탭 측)
  - 사이클 탭 / 프로파일 탭 = 채널 직접 입력
- 멀티 경로 지원 — `260310_link_cycle_multi_path_analysis` 참조

---

## 3. 인코딩 · 파일 형식 정책

### 3.1 cp949 강제

- **결정**: 모든 Toyo text 파일 (`PTN`, `_Option.PTN`, `CAPACITY.LOG`, `NNNNNN`, `.CMT`) 은 **cp949 고정**
- **Why**: Toyo 충방전기는 한국어 Windows (cp949) 환경에서 동작. utf-8 / chardet auto-detect = 한국어 셀명 / 메모 깨짐
- **How to apply**:
  - `pd.read_csv(..., encoding='cp949', on_bad_lines='skip')`
  - bytes 처리 시 `.decode('cp949', errors='replace')`
  - 신규 파일 형식 (BLK 새 모델) 진입 시 cp949 가정 우선, 실패 시에만 fallback 검토

### 3.2 BLK3600 vs BLK5200 컬럼명 정규화

- **결정**: `toyo_cycle_import()` (L3084 부근) 의 컬럼 alias map 단일 진입점에서 정규화
- 대상 alias:
  - `Capacity[mAh]` → `Cap[mAh]`
  - `OCV[V]` → `Ocv`
  - `Passed Time[Sec]` → `PassTime[Sec]`
  - `Temp1[deg]` → `Temp1[Deg]`
- **결정**: 새 BLK 모델 진입 시 alias 만 추가, 본 코드 로직 분기 추가 금지 (정규화 layer 단일화)

---

## 4. 자원 (Compute) 정책 — P0 / P1 / P2 / P3

> 제 1원칙 — 컴퓨팅 부담 최소화. 채널당 P0 + P1 합계 ≤ 100 ms 목표 ([[260508_raw_data_schema_unified_reference|260508 §7]] 검증).

| Tier | 파일 | 비용 | 발동 시점 |
|---|---|---|---|
| **P0 항상** | `PTN`, `_Option.PTN`, `CAPACITY.LOG` | < 25 ms 합 | 채널 메타 1회 로드 시 |
| **P1 sampling** | `NNNNNN` 1개 (첫 사이클 또는 대표) | 1~10 ms | 카테고리 결정용 D6 sampling 측정 시 |
| **P2 lazy** | `NNNNNN` 나머지, DCIR 펄스 파일 | 1~10 ms × N | 사용자 요청 (프로파일 / DCIR / dQdV) 시만 |
| **P3 보강 후보** | `_Option2.PTN`, `.CMT` | n/a | 현재 미활용. 향후 안전 cutoff 추출 시 P0 격상 검토 |

- **결정**: `NNNNNN` 의 P1 sampling 대상 = `OriCycle == 1` 첫 파일 1개. 첫 사이클이 비정상 시 다음 정상 사이클로 fallback.
- **결정**: P2 lazy 의 캐시 hit 미스 시 disk read — 현재 정책 유지 (메모리 폭발 방지). 채널당 1000+ NNNNNN preload 금지.

---

## 5. 캐싱 정책

### 5.1 lru_cache scope

- **결정**: `toyo_read_csv` 류 함수에 `functools.lru_cache(maxsize=...)` 유지 (현행)
- **결정**: 캐시 invalidation 은 사용자 명시 trigger (UI "새 경로 감지" 또는 재시작) — 자동 무효화 X
- **Why**: 시험 실행 중 동일 파일 (CAPACITY.LOG) 이 disk 측에서 갱신될 수 있으나, BDT 운영 모드 = "완료 시험 분석" 위주. 진행 중 시험은 현황 탭만 — 별도 cache 정책

### 5.2 channel-level meta cache

- `ChannelMeta` (proto_:332) 단위 — 채널 진입 시 P0 4종 결과를 dataclass 한 번에 묶음
- **결정**: 멀티 경로 파이프라인에서는 채널별 ChannelMeta 를 dict 로 묶어 처리 (per-process 메모리 비제한)

---

## 6. Logical Cycle 매핑 정책

### 6.1 Cycle 컬럼 절대 사용 금지

- **결정**: `CAPACITY.LOG.Cycle` 컬럼은 대부분 1 고정 — **사용 금지** (안전장치 코드 추가 금지)
- **사용**: `TotlCycle` (= NNNNNN 파일명) 만 신뢰

### 6.2 매핑 진입점

- 단일 진입점: `toyo_build_cycle_map()` (proto_:3428 부근)
- 우선순위:
  1. `extract_toyo_ptn_structure()` 로 PTN 구조 힌트 추출 (RPT 주기, 가속수명 loop_count 등)
  2. PTN 구조 + capacity.log Condition 시퀀스 결합
  3. 이상 감지 시 1:1 fallback (TC 1개 = 논리사이클 1개)

### 6.3 PTN 한 줄 = chg + dchg 동시 인코딩

- **운영 영향**: 한 step 정의에 충/방전 slot 둘 다 들어감. 사용 안 한 slot 은 0 / dash
- **결정**: `_parse_ptn_step` (L7251) 의 슬롯 분리 로직 단일 진입 — 다른 곳에서 PTN 직접 슬라이싱 금지

---

## 7. DCIR 식별 정책

### 7.1 식별 조건 (AND)

- `Finish ∈ {"Tim", "Time", "                 Tim"}` (BLK 변종 포함)
- `Condition == 2` (방전)
- `Cap[mAh] < mincapacity / 60`

### 7.2 mincapacity / 60 임계값

- **Why**: 셀 용량의 약 1.7% — 이보다 작은 방전은 의미 있는 충방전이 아닌 **펄스**
- **결정**: 임계 분모 60 은 hard-coded 유지 (BDT 표준). 변경 시 회귀 fixture (γ 그래프 골든) 측 영향 점검 필수

### 7.3 chkir 모드

- `chkir=True` (일반 DCIR) — 매 DCIR 행에 연속 번호
- `chkir=False` (쌍 DCIR) — 짝수 인덱스에서 큰 점프 (다음 DCIR 세트까지)
- **결정**: UI 라디오 버튼 default = `True` (일반 DCIR), 사용자 명시 변경 시만 `False`

---

## 8. Chamber 온도 보강 정책 (Toyo-only gap)

- **Gap**: PTN / Option 어디에도 시험 환경 (chamber) 온도 정보 없음. PNE 는 `.sch +396` 에 있음.
- **결정 1순위**: 경로명 정규식 추출
  - 패턴: `(상온|RT|23도|23C|45도|45C|고온|저온|HT|LT)`
  - 매핑: `상온|RT|23` → 23 °C, `45|HT` → 45 °C, `저온|LT` → -10 또는 0 °C (Decision 8)
- **결정 2순위**: 외부 yaml (현재 **미구현** — Decision 8)
  - 위치 후보: `wiki/10_cycle_data/chamber_temp_overrides.yaml` 또는 `tools/manifests/`
  - 형식: `<채널 경로 prefix>: chamber_C`
- **결정 3순위**: 사용자 UI 입력 (Decision 8 — 현재 BDT 미구현)

> ⚠️ **Decision 8 — 미해결 결정**: 1·2·3 순위 모두 도입할지 / 1순위만 둘지 / yaml 도입 시점은 언제인지. **Q-별 sprint 측 검토 항목**.

---

## 9. Rest step 행 부재 — 보강 정책

- **Gap**: `CAPACITY.LOG` 에는 Rest 행이 없음. PNE `SaveEndData` 는 `Condition=3` 행 있음.
- **결정**: Rest 시간 = `PTN.chg_rest_min` 및 `PTN.dchg_rest_min` 에서 추출 (P0 자원 내)
- **결정**: Rest 중 시계열 (전압 회복 곡선) 필요 시 → 인접 NNNNNN 파일에서 `Condition==3` 슬라이스 (P2 lazy)
- **결정**: GITT/HPPC 분류에서 Rest 시간이 결정 신호일 때 — PTN-only 로 판별 (NNNNNN 의존 X)

---

## 10. 충방전 인덱스 정렬 정책

### 10.1 위치 기반 매칭 (인덱스 매칭 X)

- **Why**: 다단 충전 병합 + DCIR 스텝 끼어듦 → `Chg.index` (TotlCycle) 와 `Dchg.index` (TotlCycle) 가 시스템적으로 어긋남
- **결정**: `toyo_cycle_data` (L3236~3254) 의 `.values[:_nmin]` 강제 재할당 정책 유지 — 첫 충전 ↔ 첫 방전, n번째 충전 ↔ n번째 방전
- **금지**: pandas `reindex` / `align` 으로 인덱스 매칭 시도 (DCIR 펄스 stay 가 인덱스 불일치를 만들어 NaN 폭발)

### 10.2 고아 첫 행 처리

- **결정**: 첫 행이 `Condition=2` 이고 `Cycleraw[1, "TotlCycle"]==1` 이면 **드롭** (시험 시작 잔류 방전)
- **금지**: 과거 버그 형태 = `Condition=2` 모든 행의 `TotlCycle -= 1` (DCIR 파일 번호 어긋남)

---

## 11. mincapacity 산정 정책

| 입력 | 동작 |
|---|---|
| `mincapacity > 0` | 사용자 입력 그대로 |
| `mincapacity == 0` ∧ 경로에 `mAh` 포함 | `name_capacity()` 정규식 추출 |
| `mincapacity == 0` ∧ 경로에 `mAh` 없음 | 첫 사이클 NNNNNN 의 max 전류 / `inirate` (C-rate) |

- **결정**: 자동 산정 실패 시 fallback = 사용자에게 명시 입력 요청 (silent default 금지)
- **결정**: 자동 산정 결과는 UI 에 노출 — 사용자가 1차 검증

---

## 12. 검증 게이트 — pytest fixture (ADR-0008 정합)

| Fixture | Toyo subset 정의 |
|---|---|
| **(α) 표준 데이터 경로** | `tests/data_toyo_sample/<channel>` (BLK3600 1개 + BLK5200 1개) |
| **(β) 전처리 골든 레퍼런스** | `df.NewData` 의 (Cycle, Dchg, Chg, Eff, Eff2, RndV, Temp, AvgV, OriCyc) 9 컬럼 baseline parquet |
| **(γ) 그래프 골든 image** | 사이클 탭 표준 그래프 PNG (DPI 100, 색상 대비 검증) |
| **(δ) 저장 데이터 schema** | Excel 출력 시트명 / 헤더 / dtype 자동 점검 |

- **결정**: BLK 신규 모델 추가 시 fixture α 에 1개 sample 추가 + β/γ/δ 자동 갱신
- **결정**: 사외 PC 측 = subset (in-repo 작은 샘플), 사내 PC 측 = full (실시험 데이터). ENV var `BDT_TEST_ENV=local|office` 분기

---

## 13. 알려진 한계 — Toyo 측 박제

- **chamber 온도 부재** → Decision 8 보강 필요
- **Rest 행 부재** → PTN/NNNNNN 우회
- **Cycle 컬럼 1 고정** → TotlCycle 만 사용
- **per-step 파일 폭증** → 채널당 1000+ NNNNNN, P2 lazy 정책 강제
- **`_Option2.PTN` 미활용** → 안전 cutoff 추출 시 P0 격상 검토 (P3 → P0)
- **신뢰성 시험 일부 `.xls` Fasoo DRM** → 사외 환경 decrypt 불가 ([Fasoo DRM 메모리](.claude/projects/c--Users-Ryu-battery-python-BDT-dev/memory/project_fasoo_drm_xls.md))
- **PTN 한 줄 = chg + dchg 동시 인코딩** → 슬롯 분리 단일 진입점 강제

---

## 14. 미해결 결정 (Open Decisions)

| # | 항목 | 1순위 안 | 결정자 | trigger |
|---|---|---|---|---|
| D8 | chamber 온도 보강 1·2·3 순위 도입 | 1순위만 (경로 정규식) | 본인 | yaml 운영 시점 도래 시 재검토 |
| D9 | `_Option2.PTN` 안전 cutoff 추출 P0 격상 시점 | 보류 | 본인 | empirical 4번 트랙에서 cutoff 정확도 필요 시 |
| D10 | BLK 신규 모델 alias 자동 검출 | 수동 갱신 | 본인 | 신모델 진입 시 |
| D11 | Toyo→Arbin 추가 cycler 도입 시 본 정책 분리 | 별도 정책 문서 | 본인 | Arbin 데이터 진입 시 |

---

## 15. 핵심 코드 위치 (260508 reference 시점)

> 라인 번호는 [[260508_raw_data_schema_unified_reference|260508 reference §9]] 와 동일. 본 정책 적용 시 verify against current code 필수.

### 진입점

- `toyo_cycle_data()` proto_:3116 — 사이클 데이터 메인 파이프라인
- `toyo_Profile_import()` proto_:5115 — 프로파일 시계열 import
- `toyo_build_cycle_map()` proto_:3428 부근 — 논리사이클 매핑

### 파싱 layer

- `_parse_ptn_step()` proto_:7251 — PTN 한 줄 슬롯 분리
- `_find_ptn_file()` proto_:7221 — 메인 PTN 파일 탐색
- `_read_ptn_option_capacity()` proto_:7235 — `_Option.PTN` capacity
- `extract_toyo_ptn_structure()` proto_:7427 — 시험유형 판별
- `toyo_read_csv()` proto_:5095 — CAPACITY.LOG + NNNNNN (lru_cache)
- `toyo_cycle_import()` proto_:3084 부근 — capacity.log 정규화
- `toyo_min_cap()` proto_:3099 — 기준 용량 산정
- `name_capacity()` proto_:364 — 경로 mAh 정규식

### 보조

- `LogicalCycleGroup` proto_:315 — 논리사이클 그룹 dataclass
- `ChannelMeta` proto_:332 — Phase 0 캐시 객체
- `is_pne_folder()` proto_:555 — 채널 폴더 판별 (Toyo = 음의 분기)
- `get_cycle_map()` proto_:9271 — 통합 진입점

---

## 16. Related

- [[260508_raw_data_schema_unified_reference]] — schema fact (sibling SSOT)
- [[260409_study_02_toyo_cycle_data]] — Toyo 코드 라인별 학습
- [[260411_analysis_cycle_concepts_unification]] — TC / 논리 / UI 사이클 통일
- [[260321_review_cycle_classification_logic]] — RPT/Rss/GITT 분류 로직
- [[31_software_dev/adr/0008-bdt-test-and-study-automation|ADR-0008]] — 검증 fixture 4종
- [[31_software_dev/adr/0007-workflow-efficiency-pipeline|ADR-0007]] — 워크플로우 효율 파이프라인

---

## 17. 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-09 | 최초 작성 — Toyo 운영 정책 17 영역 박제 + PNE 차이 매트릭스 + Open Decision 4건 |
