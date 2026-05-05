---
title: "Phase 0-5 분류기 v2 — 사이클 분류 로직 설명서"
date: 2026-05-05
tags: [classifier, sch-parser, cycle-classification, logic-doc, 22-categories, decision-tree]
related:
  - "[[260504_audit_phase0_5_classifier_input_spec]]"
  - "[[260505_phase0_5_187_cycle_definitions]]"
  - "[[260505_phase0_5_alpha_ref_step_field_identified]]"
  - "[[260419_사이클분류_전면재검토]]"
  - "[[hub_logical_cycle]]"
status: stable
---

# Phase 0-5 분류기 v2 — 사이클 분류 로직 설명서

> PNE `.sch` 바이너리에서 추출한 step 구조 기반으로 한 사이클 그룹 (loop group)
> 의 시험 카테고리 (22 종) 를 결정하는 분류 로직의 도메인 의미·판별 룰·우선순위를
> 박사급 peer 가 검토 가능한 수준으로 정리한 reference 문서.
>
> 본 노트는 [[260504_audit_phase0_5_classifier_input_spec]] (분류기 v2 spec) +
> [[260505_phase0_5_alpha_ref_step_field_identified]] (Phase 0-5-α 발견) 의
> 실행 결과 [[260505_phase0_5_187_cycle_definitions]] 에 적용된 룰 entire 를 재구성.

---

## 0. TL;DR — 한 페이지 요약

### 0.1 분류 단위

**사이클 그룹 (loop group)** — `.sch` 의 LOOP step 으로 구분되는 step block 묶음.
한 LOOP 의 `loop_count` (= N) 만큼 반복 실행되며, 결과 데이터에서 해당 N 개의 사이클이
하나의 카테고리 값을 공유한다.

```
.sch 파일 예시:
  step 1  DCHG (INIT)        ──┐
  step 2  LOOP loop_count=1     ─→ Group 0 (INIT)
  step 3  REST_SAFE          ──┘
  step 4~7  CHG/DCHG          ──┐
  step 8  LOOP loop_count=3     ─→ Group 1 (FORMATION, N=3)
  step 9  REST_SAFE          ──┘
  step 10~22 CHG/DCHG (multi)──┐
  step 23 LOOP loop_count=100   ─→ Group 2 (ACCEL, N=100)
  ...
```

### 0.2 분류 입력 (사용자 통찰 5 base + 1)

| Input | binary 위치 | 의미 |
|---|---|---|
| `mincapacity` | `+104` (또는 사용자 입력 path) | 셀 nominal 용량 (mAh) — C-rate 산출의 분모 |
| 인가 전류 | step `+20` | C-rate = current / mincapacity |
| 전압 (CC) | step `+28 end_voltage_mV` | CC 단계의 실제 V cutoff |
| 전압 (CCCV) | step `+12 voltage_mV` | CC target = CV target |
| EndCondition | `+24/+28/+32/+36/+40/+372/+500/+504` | 종료 조건 multi-OR |
| Sampling 주기 | step `+336 record_interval_s` | ECT/GITT=1s, hyst=60s, DCIR=0.1s |

### 0.3 분류 출력 (22 카테고리)

| 그룹 | 카테고리 | 의미 |
|---|---|---|
| **사이클 (반복)** | ACCEL, FORMATION | 가속수명 / 화성 |
| **RPT 그룹** | RPT, CHG_DCHG | 0.2C 기준 / 일반 충방전 |
| **DCIR 그룹** | SOC_DCIR, PULSE_DCIR, RSS_DCIR | SOC별 / 펄스 / 정상상태 |
| **GITT 그룹** | GITT_PULSE, SWEEP_PULSE | full / simplified |
| **Hysteresis 그룹** | HYSTERESIS_DCHG, HYSTERESIS_CHG | DOD% / SOC% 부분 |
| **저장 그룹** | FLOATING, REST_LONG, REST_SHORT, POWER_CHG | floating / 휴지 / K-value |
| **세팅 그룹** | INIT, TERMINATION, CHARGE_SET, DCHG_SET, DISCHARGE_SET | 초기·종료·SOC 세팅 |
| **fallback** | UNKNOWN, EMPTY | 미분류 |

---

## 1. 입력 정의 — 사용자 통찰 (CC vs CCCV)

### 1.1 사용자 핵심 통찰 (260504)

> "결국 하고 싶은 건 .sch 파일 분석을 통한 사이클 분류이다.
>  mincapacity, 인가 전류, 전압, EndCondition + sampling 주기이다.
>
> - **CC 전류 인가의 cutoff 전압은 EndCondition을 따름**
> - **CCCV는 Charge(V), Discharge(V) 열 정보가 CC cutoff voltage + EndCondition 에
>   전류 cutoff 외 조건들이 있음**"

### 1.2 CC mode (`type_code = 0x0201 CHG_CC`, `0x0202 DCHG_CC`)

| binary | UI field | 의미 |
|---|---|---|
| `+12 (CHG)` / `+16 (DCHG)` | `Charge(V)` / `Discharge(V)` | **Display only (또는 사용자 default)** — 실제 cutoff 가 아님 |
| `+20` | `Current(A)` | **인가 전류 (실제 적용)** |
| `+24` | EndCondition `t > HH:MM:SS` | **시간 cutoff** |
| **`+28`** | EndCondition `V < x` 또는 `V > x` | ⭐ **실제 V cutoff** |
| `+36/+40` | EndCondition `C > x` | Capacity cutoff |
| `+500` | EndCondition `Step N SOC/DOD X%` | ref-step jump (Phase 0-5-α) |

### 1.3 CCCV mode (`type_code = 0x0101 CHG_CCCV`, `0x0102 DCHG_CCCV`)

| binary | UI field | 의미 |
|---|---|---|
| **`+12`** | `Charge(V)` | ⭐ **CC target voltage = CV target voltage** (둘 다 같은 값) |
| `+20` | `Current(A)` | 인가 전류 (CC 단계) |
| `+24` | EndCondition `t > HH:MM:SS` | 시간 cutoff |
| `+28` | (CCCV 에서는 0) | 미사용 |
| **`+32`** | EndCondition `I < x` | ⭐ **실제 I cutoff (CV 단계)** |
| `+36/+40` | EndCondition `C > x` | Capacity cutoff |

### 1.4 분류기 함수 — V cutoff 추출

```python
def step_v_cutoff_mV(s: dict) -> float:
    """CC vs CCCV 의 V cutoff 의미 분리 (Phase 0-5 사용자 통찰)."""
    t = s.get('type', '')
    if t in ('CHG_CCCV', 'DCHG_CCCV'):
        return s.get('voltage_mV', 0)        # CV target
    if t in ('CHG_CC', 'DCHG_CC'):
        return s.get('end_voltage_mV', 0)    # EndCondition
    return 0
```

→ 분류 룰에서 V cutoff 비교 시 step_v_cutoff_mV 사용 필수. 그렇지 않으면 CC step
의 `+12` (display) 를 cutoff 로 오해 → multi-step charge 의 4.140/4.160/... 점진적
증가 패턴 탐지 실패.

---

## 2. End Condition 인코딩 — Multi-condition OR

### 2.1 `+500/+504` ref-step jump 인코딩 (Phase 0-5-α 발견)

PNE 의 EndCondition 중 **"Step N (Char./Dis.) AH/V 의 SOC/DOD X% Move NEXT/Step M"**
형식의 ref-step jump 은 다음 인코딩으로 저장된다:

```
+500 (uint32) = (ref_step_number << 8) | type_marker_low_byte
                                                    ↑
                                           본 데이터셋에서 항상 0
+501 byte                  = ref_step_number  (uint8, 0~255)
+504 (uint32)              = ec_enabled       (1 = 활성, 0 = 비활성)
+372 (float32)             = pct_threshold    (1.0% / 10.0% / 100.0% 등)
```

### 2.2 ref-step jump 사용 패턴 (368 .sch 전수, 1,169 step)

| pattern | step type | +500 값 | ref_step | pct | 의미 |
|---|---|---|---|---|---|
| Hysteresis DCHG (DOD%) | DCHG_CC | **2048 = 8<<8** | 8 | 10/20/.../90 | cluster 첫 CHG step (#8) 까지 충전한 양의 X% 만큼 부분 방전 |
| Hysteresis CHG (SOC%) | CHG_CC | **18432 = 72<<8** | 72 | 10/20/.../90 | 별도 cluster (#72) 까지 방전한 양의 X% 만큼 부분 충전 |
| RSS_DCIR (4 cluster) | DCHG_CC | 2048/10752/19456/28160 | 8/42/76/110 | 15/20/30 | 각 cluster 의 다른 ref step (간격 34) |
| SOC_DCIR (DOD 100%) | DCHG_CC | (own_step<<8) | 17/20/23/26... | 100.0 | 직전 CHG step 의 charge 양 100% 만큼 방전 |
| SOC_DCIR (SOC 1%) | CHG_CCCV | 2816 = 11<<8 | 11 | 1.0/5.0 | 초기 charge step (#11) 양의 1% 추가 → SOC level up |

### 2.3 일반 EndCondition 종류 (UI 추론)

한 step 에 4-5 condition 이 OR 로 동시 적용 가능:

| Condition | 위치 | 예 |
|---|---|---|
| 종료 전압 | `+28` | "V > 4.140" or "V < 2.750" |
| 종료 전류 | `+32` | "I < 0.055" |
| 종료 시간 | `+24` | "t > 0:00:20" or "t > 1D 0:00:00" |
| 종료 용량 | `+36/+40` | "C > 3.042" |
| ref-step SOC% | `+500/+504` | "Step 11 SOC 1%(AH) Move NEXT" |
| ref-step DOD% | `+500/+504` | "Step 27 DOD 100%(AH) Move NEXT" |

→ 본 분류기 v2 는 multi-condition OR 의 **각 slot 개수 + ref-step 사용 여부** 만
인지. 각 condition 의 "Move NEXT vs Move Step N" 차이는 미인지 (jump_target_step
미식별 — Phase 0-5-α 보류 항목).

---

## 3. 22 카테고리 정의 — 도메인 의미와 판별 룰

각 카테고리는 **(도메인 의미) + (.sch 패턴 시그니처) + (판별 룰)** 3-tuple 로 정의.
판별 룰은 우선순위 순서로 평가되며 첫 매칭이 결과.

### 3.1 시험 진행 단계 (position-based)

#### `INIT` — 초기 방전

- **의미**: 셀 시험 시작 시 SOC 초기화 (full discharge 또는 SOC 0% 세팅).
- **시그니처**: 첫 LOOP, N=1, DCHG (또는 DCHG+REST) only, CHG 없음.
- **룰**:
  ```
  position == 0 AND N == 1 AND
  all(s.type in (DCHG_TYPES | {'REST'})) AND
  any(s.type in DCHG_TYPES)
  ```

#### `TERMINATION` — 시험 종료 방전

- **의미**: 시험 마지막 step — full discharge 후 보관 SOC 세팅.
- **시그니처**: 마지막 LOOP, N=1, DCHG only.
- **룰**:
  ```
  position == total_loops - 1 AND N == 1 AND dchg AND not chg
  ```

### 3.2 사이클 시험 (반복 횟수 기반)

#### `ACCEL` — 가속수명 사이클

- **의미**: 셀의 calendar/cycle 노화 가속 평가. multi-step charge protocol
  (점진적 V 상승) + 0.5C~1C 방전을 N≥20회 반복.
- **시그니처**: N≥20, multi-step CHG (≥2), DCHG, sampling 60s.
- **룰**:
  ```
  N >= 20 AND len(chg_steps) >= 2 AND dchg
  ```
- **sub_tag**: `multi_step` (CHG≥3) — Si Hybrid 4-step charge 등.

#### `FORMATION` — 화성 사이클

- **의미**: 신규 셀의 SEI 형성. 0.1C~0.2C 저속 충방전 N=2~10회.
- **시그니처**: 2≤N≤10, CHG+DCHG.
- **룰**:
  ```
  2 <= N <= 10 AND chg AND dchg
  ```

#### `RPT` — Reference Performance Test

- **의미**: 사이클 진행 중간 체크 — 0.2C 기준 capacity 측정. 같은 조건
  반복으로 capacity fade 추적.
- **시그니처**: N=1, CHG+DCHG, 모든 인가 전류 ≈ 0.2C ±30%.
- **룰**:
  ```
  N == 1 AND chg AND dchg AND
  rate_02C = capacity_mAh * 0.2 AND
  all(abs(I - rate_02C) / rate_02C < 0.3 for I in currents)
  ```
- ⚠️ `mincapacity` (path table 입력) 0 일 때 RPT 판정 불가 → CHG_DCHG 로 fall-through.

#### `CHG_DCHG` — 일반 1회 충방전

- **의미**: RPT 룰 안 걸린 N=1 충방전 (rate 가 0.2C 가 아닌 케이스 또는 capacity 미입력).
- **시그니처**: N=1, CHG+DCHG.
- **룰**: 위 RPT 룰 fall-through.

### 3.3 GITT 시험

#### `GITT_PULSE` — GITT (Galvanostatic Intermittent Titration Technique)

- **의미**: 작은 전류 (0.05C 등) 펄스 → 장시간 REST (≥10분) 반복. OCV-SOC 관계 측정.
- **시그니처**: GITT 블록 코드 (0x0003/0x0007/0x0008) 또는 REST≥600s + 짧은 CHG/DCHG, N≥10.
- **룰**:
  ```
  (has_gitt_block AND N >= 10) OR
  (N >= 10 AND len(body) <= 3 AND max_rest_s >= 600 AND
   any non-rest CHG or DCHG)
  ```
- **sub_tag**: `short_sampling` (`+336 < 5`) — ECT GITT (1s sampling).

#### `SWEEP_PULSE` — Simplified GITT / sweep

- **의미**: GITT 룰 안 걸린 N≥10 short-body 패턴.
- **시그니처**: N≥10, body≤3, REST<600s.
- **룰**: 위 GITT 룰 fall-through 후 `N >= 10 AND len(body) <= 3`.

### 3.4 DCIR 시험 (Direct Current Internal Resistance)

> [[260504_audit_phase0_4_dcir_pattern_review]] 참고. 3 카테고리 모두 짧은 펄스 +
> ref-step jump 의 변형이지만 N / step 구성으로 disambiguate.

#### `SOC_DCIR` — SOC 별 DCIR

- **의미**: SOC 1%~20% 각 level 에서 4 rate (0.05/0.1/0.2/0.5C) pulse 측정.
  ref-step SOC% 로 SOC level up.
- **시그니처**: EC≥4, body≥8, N=5~19, EC type 다양성 ≥3 (서로 다른 SOC level).
- **룰**:
  ```
  5 <= N < 20 AND len(ec_steps) >= 4 AND len(body) >= 8 AND
  len(set(ec_types)) >= 3
  ```

#### `PULSE_DCIR` — 펄스 DCIR

- **의미**: 짧은 (≤30s) DCHG 펄스 다수회 — 정상상태 도달 전 펄스 저항 측정.
- **시그니처**: EC + 짧은 DCHG (`+24 ≤ 30`) + DCHG≥2, body≥5.
- **룰**:
  ```
  has_ec AND has_short_dchg AND len(dchg) >= 2 AND len(body) >= 5
  ```
- **sub_tag**: `short_sampling` (`+336 < 5`, e.g. 0.1s) — pulse measurement.

#### `RSS_DCIR` — RSS (Reduced Step Size, 또는 정상상태 저항)

- **의미**: DCHG 4회 이상 + 긴 REST → 확산 포함 정상상태 저항.
- **시그니처**: N=1, EC, DCHG≥4, body≥10.
- **룰**:
  ```
  N == 1 AND has_ec AND len(dchg) >= 4 AND len(body) >= 10
  ```

### 3.5 Hysteresis 시험

#### `HYSTERESIS_DCHG` — DOD% 부분 방전

- **의미**: 같은 SOC 에서 점진적으로 깊어지는 부분 방전 (DOD 10/20/.../90 %).
  V hysteresis 측정. ref-step = cluster 의 첫 CHG step (전형적으로 step 8).
- **시그니처**: N=1, DCHG, EC type=2048 (= ref_step 8), no short pulse.
- **룰** (분류기 v2):
  ```
  N == 1 AND not has_short_dchg AND
  any(ec_type == 2048 for s in ec_on_dchg)
  ```
- **룰** (분류기 v3 후보, Phase 0-5-α 일반화):
  ```
  N == 1 AND not has_short_dchg AND
  any(ref_step_number > 0 for s in ec_on_dchg)
  ```

#### `HYSTERESIS_CHG` — SOC% 부분 충전

- **의미**: 같은 SOC 에서 점진적으로 깊어지는 부분 충전 (SOC 10/20/.../90 %).
- **시그니처**: N=1, CHG, EC type=18432 (= ref_step 72), no short pulse.
- **룰** (분류기 v2):
  ```
  N == 1 AND not has_short_chg AND
  any(ec_type == 18432 for s in ec_on_chg)
  ```

### 3.6 저장 / 휴지 시험

#### `FLOATING` — 장시간 floating (calendar aging)

- **의미**: CV 상태로 일~수개월 방치 — SEI growth, calendar aging 측정.
- **시그니처**: CHG only (no DCHG), 최소 1 step 의 `time_limit_s ≥ 43200` (12hr+).
- **룰** (Phase 0-5-α fix 후):
  ```
  chg AND not dchg AND
  max_chg_time >= 43200 AND
  any(s.voltage_mV > 0 for s in chg_steps)   # ⚠️ 'voltage_mV' (proto fix 필요)
  ```
- ⚠️ proto 코드 L8053 의 `v_chg_mV/v_chg` 키 mismatch bug → 본 룰 무력화.
  Phase c-α 에서 proto 본체 fix 필요.

#### `REST_LONG` — 장시간 휴지

- **의미**: 단순 REST step ≥3600s (1시간+).
- **시그니처**: body=1, type=REST, time_limit_s≥3600.
- **룰**:
  ```
  len(body) == 1 AND types[0] == 'REST' AND
  body[0].time_limit_s >= 3600
  ```

#### `REST_SHORT` — 단시간 휴지

- **의미**: 단순 REST step <3600s.
- **룰**: 위 룰 fall-through 후 `len(body) == 1 AND type == REST`.

#### `POWER_CHG` — 전력 충전 (K-value 측정)

- **의미**: CHG_CP (Constant Power) 사용 — K-value (power-cap 비례 상수) 측정.
- **시그니처**: type 에 `CHG_CP` 포함.
- **룰**: `'CHG_CP' in type_set`.

### 3.7 단일 step 세팅

#### `CHARGE_SET` — 충전 세팅

- **의미**: SOC X% 까지 충전 (방전 없음). N=1.
- **시그니처**: N=1, CHG only (DCHG 없음), CHG/REST/REST_SAFE 만.
- **룰**:
  ```
  N == 1 AND chg AND not dchg AND
  type_set <= (CHG_TYPES | {'REST', 'REST_SAFE'})
  ```

#### `DISCHARGE_SET` — DCHG_CCCV 세팅

- **의미**: CCCV 방전 (정전압 방전) 단독 — SOC 세밀 조정.
- **시그니처**: N=1, has DCHG_CCCV, body≤2.
- **룰**:
  ```
  N == 1 AND has_dchg_cccv AND len(body) <= 2
  ```

#### `DCHG_SET` — 일반 방전 세팅

- **의미**: N=1, DCHG only (CHG 없음). TERMINATION fall-through.
- **룰**:
  ```
  N == 1 AND dchg AND not chg
  ```

### 3.8 Fallback

#### `UNKNOWN` — 미분류

- **의미**: 위 17 룰 모두 안 걸린 그룹.
- **현 데이터셋 발생 케이스**: `복합floating` 의 **N=14 mid-range** 패턴
  (4chg/1dchg/2rest body) — ACCEL (N≥20) 과 FORMATION (N≤10) 사이에서 fall-through.

#### `EMPTY` — 빈 body

- **의미**: body 가 없는 LOOP (이론상 불가, 안전 fallback).

---

## 4. 분류 우선순위 (Decision Order)

22 카테고리는 **순서대로 평가** 되며 첫 매칭이 결과. 우선순위는 도메인 specificity
순 — 특이 패턴 먼저, 일반 패턴 나중.

```
 1. INIT              (position == 0, N=1, DCHG only)
 2. GITT_PULSE        (GITT 블록 또는 N≥10 + REST≥600s)
 2b. FLOATING         (CHG only + ≥12hr + V_cut)
 3. ACCEL             (N≥20, multi-CHG + DCHG)
 4. HYSTERESIS_DCHG   (N=1, DCHG, ec_type=2048)
 5. HYSTERESIS_CHG    (N=1, CHG, ec_type=18432)
 6. SOC_DCIR          (5≤N<20, EC≥4, body≥8, EC type 다양성)
 7. PULSE_DCIR        (EC, 짧은 DCHG, DCHG≥2, body≥5)
 8. RSS_DCIR          (N=1, EC, DCHG≥4, body≥10)
 9. DISCHARGE_SET     (N=1, DCHG_CCCV, body≤2)
10. POWER_CHG         (CHG_CP 포함)
11. REST_LONG         (REST only, t≥3600)
12. FORMATION         (2≤N≤10, CHG+DCHG)
13. CHARGE_SET        (N=1, CHG only)
14. TERMINATION       (position == last, N=1, DCHG only)
14b. DCHG_SET         (N=1, DCHG only)
15. RPT               (N=1, CHG+DCHG, 모든 I ≈ 0.2C ±30%)
16. CHG_DCHG          (N=1, CHG+DCHG, RPT fall-through)
17. SWEEP_PULSE       (N≥10, body≤3)
18. REST_SHORT        (REST only, t<3600)
99. UNKNOWN           (모두 fall-through)
```

### 4.1 우선순위 핵심 결정

| 결정 | 이유 |
|---|---|
| INIT 가 1순위 | 첫 step (position=0) DCHG 는 거의 항상 SOC 초기화 |
| GITT 가 ACCEL 보다 먼저 | GITT 의 N≥10 이 ACCEL 의 N≥20 룰 안 걸림 |
| FLOATING 이 ACCEL 보다 먼저 | DCHG 없는 케이스를 ACCEL 이전에 분리 |
| HYSTERESIS 가 SOC_DCIR 보다 먼저 | N=1 인 hysteresis 가 SOC_DCIR (5≤N<20) 룰 자체에 안 걸리지만, 명확성 위해 |
| RPT 가 CHG_DCHG 보다 먼저 | RPT 가 CHG_DCHG 의 specialization (0.2C 조건) |
| RPT 가 FORMATION 보다 나중 | FORMATION (2≤N≤10) 이 RPT (N=1) 와 겹치지 않으므로 순서 무관 |
| DCHG_SET 이 TERMINATION 직후 | TERMINATION 은 specialized DCHG_SET (마지막 위치) |

### 4.2 ACCEL N=14 mid-range gap

- ACCEL 룰: `N≥20 + 다단CHG + DCHG`
- FORMATION 룰: `2≤N≤10 + CHG + DCHG`
- 사이 gap: **11≤N≤19** + 다단CHG + DCHG

→ 본 데이터셋의 `복합floating/HaeanProto N=14` 패턴이 이 gap 에 빠져 UNKNOWN 142건 발생.
**Phase 0-5-α 후속 fix 후보**:
1. ACCEL 임계값 완화: `N≥10` + `len(chg)≥3` (더 엄격한 multi-step) — risk: FORMATION 와 겹침
2. 신규 카테고리 `MID_LIFE_CYCLE` 추가
3. schedule_description keyword `"복합floating"` prior

---

## 5. 분류 결정 흐름도

```
┌─────────────────────────────────────────────────────────────────┐
│ INPUT: body (loop 내부 step list), N, position, total_loops,    │
│        capacity_mAh, schedule_description                        │
└─────────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │   position == 0, N=1, DCHG?   │
            │   YES → INIT                  │
            └───────────────┬───────────────┘
                            │ NO
            ┌───────────────┴───────────────┐
            │   GITT 블록 OR (N≥10+REST≥10m)?│
            │   YES → GITT_PULSE            │
            └───────────────┬───────────────┘
                            │ NO
            ┌───────────────┴───────────────┐
            │  CHG only + 12hr+ + V_cut?    │
            │  YES → FLOATING               │
            └───────────────┬───────────────┘
                            │ NO
            ┌───────────────┴───────────────┐
            │  N≥20 + multi-CHG + DCHG?     │
            │  YES → ACCEL                  │
            └───────────────┬───────────────┘
                            │ NO
            ┌───────────────┴───────────────┐
            │  N=1 + DCHG + ec_type=2048?   │
            │  YES → HYSTERESIS_DCHG        │
            └───────────────┬───────────────┘
                            │ NO
            ┌───────────────┴───────────────┐
            │  N=1 + CHG + ec_type=18432?   │
            │  YES → HYSTERESIS_CHG         │
            └───────────────┬───────────────┘
                            │ NO
            ┌───────────────┴───────────────┐
            │  5≤N<20 + EC≥4 + body≥8 +     │
            │  EC type 다양성 ≥3?            │
            │  YES → SOC_DCIR               │
            └───────────────┬───────────────┘
                            │ NO
            ┌───────────────┴───────────────┐
            │  EC + 짧은 DCHG + DCHG≥2 +    │
            │  body≥5?                       │
            │  YES → PULSE_DCIR             │
            └───────────────┬───────────────┘
                            │ NO
            ┌───────────────┴───────────────┐
            │  N=1 + EC + DCHG≥4 + body≥10?│
            │  YES → RSS_DCIR               │
            └───────────────┬───────────────┘
                            │ NO
            ┌───────────────┴───────────────┐
            │  N=1 + DCHG_CCCV + body≤2?    │
            │  YES → DISCHARGE_SET          │
            └───────────────┬───────────────┘
                            │ NO
            ┌───────────────┴───────────────┐
            │  CHG_CP 포함?                  │
            │  YES → POWER_CHG              │
            └───────────────┬───────────────┘
                            │ NO
            ┌───────────────┴───────────────┐
            │  body=1 + REST + t≥3600?      │
            │  YES → REST_LONG              │
            └───────────────┬───────────────┘
                            │ NO
            ┌───────────────┴───────────────┐
            │  2≤N≤10 + CHG + DCHG?         │
            │  YES → FORMATION              │
            └───────────────┬───────────────┘
                            │ NO
            ┌───────────────┴───────────────┐
            │  N=1 + CHG only?              │
            │  YES → CHARGE_SET             │
            └───────────────┬───────────────┘
                            │ NO
            ┌───────────────┴───────────────┐
            │  position=last + N=1 + DCHG   │
            │  only?                         │
            │  YES → TERMINATION            │
            └───────────────┬───────────────┘
                            │ NO
            ┌───────────────┴───────────────┐
            │  N=1 + DCHG only?             │
            │  YES → DCHG_SET               │
            └───────────────┬───────────────┘
                            │ NO
            ┌───────────────┴───────────────┐
            │  N=1 + CHG + DCHG +           │
            │  모든 I ≈ 0.2C±30%?            │
            │  YES → RPT                    │
            └───────────────┬───────────────┘
                            │ NO
            ┌───────────────┴───────────────┐
            │  N=1 + CHG + DCHG?            │
            │  YES → CHG_DCHG               │
            └───────────────┬───────────────┘
                            │ NO
            ┌───────────────┴───────────────┐
            │  N≥10 + body≤3?               │
            │  YES → SWEEP_PULSE            │
            └───────────────┬───────────────┘
                            │ NO
            ┌───────────────┴───────────────┐
            │  body=1 + REST?               │
            │  YES → REST_SHORT             │
            └───────────────┬───────────────┘
                            │ NO
                            ▼
                        UNKNOWN
```

---

## 6. v2 (현재) vs v3 (Phase 0-5-α 후) 분류기 비교

### 6.1 현재 v2 분류기 (proto L7975 + batch script)

| 항목 | 상태 |
|---|---|
| `v_chg` 키 mismatch bug | ⚠️ proto 미수정 (batch script 만 fix) |
| 9 신규 parser field | ⚠️ proto 미반영 |
| CC vs CCCV V cutoff 분리 | ⚠️ proto 미반영 |
| schedule keyword prior | ⚠️ proto 미반영 |
| `+336 < 5` short_sampling hint | ⚠️ proto 미반영 |
| ref_step_number 인코딩 | ⚠️ proto 미반영 (Phase 0-5-α) |

### 6.2 v3 분류기 후보 (Phase c 후)

```python
# proto _parse_pne_sch 보강 (Phase 0-2/0-5-α confirmed)
step_info['v_safety_upper_mV']   = struct.unpack_from('<f', blk, 88)[0]
step_info['v_safety_lower_mV']   = struct.unpack_from('<f', blk, 92)[0]
step_info['i_safety_upper_mA']   = struct.unpack_from('<f', blk, 96)[0]
step_info['i_safety_lower_mA']   = struct.unpack_from('<f', blk, 100)[0]
step_info['record_interval_s']   = struct.unpack_from('<f', blk, 336)[0]
step_info['chamber_temp_c']      = struct.unpack_from('<f', blk, 396)[0]
step_info['mode_flag']           = struct.unpack_from('<I', blk, 84)[0]

# end_condition 에 ref_step_number 추가 (Phase 0-5-α)
ec_type_full = struct.unpack_from('<I', blk, 500)[0]
ec_enabled = struct.unpack_from('<I', blk, 504)[0]
if ec_type_full != 0 and ec_enabled == 1:
    step_info['end_condition'] = {
        'type': ec_type_full,
        'value_pct': round(struct.unpack_from('<f', blk, 372)[0], 2),
        'ref_step_number': (ec_type_full >> 8) & 0xFF,  # ⭐ Phase 0-5-α
        'type_marker': ec_type_full & 0xFF,             # 본 데이터셋 항상 0
    }

# 분류기 _classify_loop_group 의 hysteresis 룰 일반화
# Before:
if any(s.get('end_condition', {}).get('type') == 2048 for s in ec_on_dchg):
    return 'HYSTERESIS_DCHG'
# After (Phase 0-5-α 일반화):
if any(s.get('end_condition', {}).get('ref_step_number', 0) > 0
       for s in ec_on_dchg):
    return 'HYSTERESIS_DCHG'  # 또는 RSS_DCIR / SOC_DCIR — N/body 로 disambiguate
```

→ v3 의 핵심 차이:
- HYSTERESIS_DCHG / RSS_DCIR / SOC_DCIR 의 disambiguate 가 **fixed value 매칭이
  아닌 일반 ref_step 사용 + N/body 룰** 로 정확화.
- Schedule 의 step 번호 변경에 robust (현 v2 는 ref_step=8 또는 72 인 hysteresis
  schedule 만 매칭).

### 6.3 187 폴더 분류 결과 영향 예측

| Category (v2) | count | v3 예상 변화 |
|---|---|---|
| HYSTERESIS_DCHG | 230 | 유지 ± 약간 (ref_step 변형 케이스 흡수) |
| HYSTERESIS_CHG | 198 | 동상 |
| SOC_DCIR | 20 | ↑ (v2 의 PULSE_DCIR 일부가 SOC_DCIR 로 이동 가능) |
| PULSE_DCIR | 856 | ↓ |
| RSS_DCIR | 8 | ↑ (v2 의 PULSE_DCIR 일부 흡수) |
| FLOATING | 30 | ↑ (proto v_chg fix 후 잠재 +α) |
| UNKNOWN | 142 | ↓ (ACCEL N=14 gap fix 시 → 0 target) |

→ **v3 적용 후 정확도 향상 측정 (Phase d) 가 필요**.

---

## 7. UNKNOWN 케이스 분석 — Phase 0-5-α 후속

### 7.1 본 데이터셋 UNKNOWN 14 종 (body-signature dedup)

| 폴더 | sch 수 | N | body | chg/dchg/rest | 패턴 |
|---|---|---|---|---|---|
| 안성진 251mAh HaeanProtoDOE 복합Floating | 4 | 14 | 7 | 4/1/2 | 다단CHG(4) → DCHG → REST×2 |
| 안성진 251mAh HaeanProtoMain 복합Floating | 4 | 14 | 7 | 4/1/2 | 동상 |
| 김영환 3365mAh Gen6+VB ATL Proto1 280day | 2 | 14 | 8 | 4/2/2 | 다단CHG → DCHG×2 → REST×2 |
| 박기진 4948mAh Gen6+VB SDI Proto1 280day | 4 | 14 | 8 | 4/2/2 | 동상 |

→ 모두 `복합floating/` 시험. **N=14 mid-life cycle** 패턴이 ACCEL/FORMATION gap 에 위치.

### 7.2 후속 fix 후보

#### 옵션 A: ACCEL 임계값 완화

```python
# Before
if N >= 20 and len(chg_steps) >= 2 and dchg_steps:
    return 'ACCEL'
# After
if N >= 10 and len(chg_steps) >= 3 and dchg_steps:
    return 'ACCEL'
```

→ Risk: FORMATION (2≤N≤10) 와 겹침. mitigation 필요 (FORMATION 룰 강화 또는 우선순위 조정).

#### 옵션 B: 신규 카테고리

`MID_LIFE_FLOATING` (또는 `복합사이클`) 추가 — N=11~19 + multi-CHG + 작은 DCHG.

#### 옵션 C: schedule_description keyword 활용

```python
desc = parsed['header']['schedule_description'].lower()
if '복합floating' in desc or 'haean' in desc or '280day' in desc:
    if N == 14 and len(chg_steps) >= 3:
        return 'ACCEL'  # sub_tag = 'floating_hybrid'
```

→ 가장 안전 (schedule 명시적 신호 활용). 단 schedule 작성 컨벤션 의존.

---

## 8. Sub-tag 활용 (분류기 v2 신규)

22 카테고리 외 sub_tag 으로 추가 정보:

| Category | Sub-tag | 의미 |
|---|---|---|
| ACCEL | `multi_step` | CHG≥3 (Si Hybrid 4-step charge 등) |
| GITT_PULSE | `gitt_block` / `short_sampling` | GITT 블록 사용 / `+336 < 5` |
| PULSE_DCIR | `short_sampling` | `+336 < 5` (0.1s 펄스 측정) |
| FLOATING | `cccv` / `cc` | CV target 사용 / CC end_voltage 사용 |
| CHARGE_SET | `cccv` | CCCV charge |
| HYSTERESIS_DCHG | `hysteresis` | schedule_description keyword 매칭 |
| HYSTERESIS_CHG | `hysteresis` | 동상 |

→ Phase b (22 카테고리 spec audit) 에서 sub_tag 정식 분류 변형 등록 가능.

---

## 9. Limitations & Caveats

### 9.1 mincapacity 의존성

RPT 룰 (`모든 I ≈ 0.2C ±30%`) 은 `mincapacity` (셀 nominal 용량) 입력 필요.
path table 사용자 입력 + `+104 capacity_limit_mAh` (per-step) + 폴더명 regex 의 3-tier
fallback 사용. 모두 0 시 RPT 판정 불가 → CHG_DCHG fall-through.

### 9.2 outer-goto loop expansion

LOOP step 의 `+52 goto_target_step` + `+580 goto_repeat_count` 가 비0이면
schedule 본체를 `goto_repeat_count` 회 추가 반복하여 expanded group 생성. expanded
group 의 카테고리는 본체와 동일 → 8,298 group 중 outer-goto 확장분이 다수 포함
(특히 `복합floating` 의 N=14 UNKNOWN 142 건 = 14 unique × outer-goto 반복).

### 9.3 일반 헤지 룰

- Phase 0-5 spec 의 `ec_type == 2048` / `== 18432` 매칭은 **특정 schedule template
  (ref_step=8 hysteresis, ref_step=72 SOC%)** 만 매칭. 다른 schedule 의 hysteresis 는
  Phase 0-5-α v3 룰 (ref_step_number > 0) 로 일반화 필요.
- ACCEL `N≥20` 임계값은 hard threshold — 100세포 ATL Q7M (N=100~400) 에는 robust 하지만
  HaeanProto N=14 같은 short-life test 에는 fragile.

### 9.4 Toyo `.ptn` 미지원

본 분류기는 PNE `.sch` 만 지원. Toyo `.ptn` (수명 36 폴더 중 12 폴더) 은 별도
parser/classifier 필요. Phase 3 (Toyo 확장) 에서 동일 결정 트리 적용 가능.

### 9.5 Phase 0-5-α 보류 4 field

- `ref_step_kind` (Char./Dis.): 본 데이터셋 모두 Char.
- `ref_basis` (AH/V): 본 데이터셋 모두 AH
- `jump_target_step` (NEXT/Step N): 본 데이터셋 모두 NEXT
- `end_delta_vp_V` (DCIR Vp Drop): 사용 sample 부재

→ 위 4 field 가 필요한 시험 (예: V-based ref-step jump, Move Step N) 이 발생하면
binary search 재시도 필요.

---

## 10. 참고 코드 위치

| 위치 | 내용 |
|---|---|
| `DataTool_optRCD_proto_.py:7560` | `# PNE .sch 바이너리 파서 (내장)` 주석 |
| `:7570-7584` | `_SCH_TYPE_MAP` (14 type codes) |
| `:7594-7768` | `_parse_pne_sch` 본체 |
| `:7936-7972` | `_decompose_loop_groups` (LOOP 기준 그룹 분할) |
| `:7975-8143` | `_classify_loop_group` (22 카테고리 판정) |
| `:8053` | ⚠️ `v_chg` 키 mismatch bug |
| `:8146-8228` | `_build_loop_group_info` (TC 범위 + C-rate 산출) |
| `:8231-8276` | `_merge_hysteresis_envelopes` (hyst envelope 흡수) |
| `:8300-8351` | `_expand_groups_with_outer_goto` (outer-goto 확장) |
| `:9430-9458` | `_CLASSIFIED_COLORS` (22 → 10 색상 팔레트) |

신규 도구 (Phase 0-5 / 0-5-α):
- [`tools/sch_phase0_5_classify_all.py`](../../tools/sch_phase0_5_classify_all.py) — 187 폴더 batch
- [`tools/sch_phase0_5_alpha_validate.py`](../../tools/sch_phase0_5_alpha_validate.py) — ref_step_number cross-validate

---

## 11. 분류 결과 활용

본 분류 로직은 다음 BDT 기능의 base layer:

1. **사이클 바 색상 (Cycle Timeline Bar)** — 22 카테고리 → 10 색상 팔레트 (`_CLASSIFIED_COLORS`)
2. **TC 자동 분류** — 사용자 입력 TC 범위 검증 / 자동 표시
3. **6 평가 항목 매핑 layer** ([[260504_plan_22cat_audit_and_eval_overlay]] §4)
   — 22 자동 분류 + 6 평가자 매핑이 직교 layer
4. **사이클 데이터 그래프 분류** — RPT 만 / ACCEL 만 등 카테고리 필터

분류 정확도 (UNKNOWN 비율, 오분류율) 는 위 4 기능의 신뢰도 base.

---

## Related

- [[260504_audit_phase0_5_classifier_input_spec]] — 분류기 v2 spec 정의
- [[260505_phase0_5_187_cycle_definitions]] — 187 폴더 사이클별 정의 결과
- [[260505_phase0_5_alpha_ref_step_field_identified]] — Phase 0-5-α ref_step 식별
- [[260504_plan_22cat_audit_and_eval_overlay]] — 5단계 audit plan
- [[260419_사이클분류_전면재검토]] — 분류기 전면 재검토 (Phase 1)
- [[260504_audit_phase0_4_dcir_pattern_review]] — DCIR pattern UI review
- [[260504_audit_phase0_3_pne_ui_review]] — ECT GITT pattern UI review
- [[hub_logical_cycle]] — 논리 사이클 hub
