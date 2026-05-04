---
title: "Phase 0-1d: CSV ↔ .sch step-level alignment — unknown bytes 해석"
date: 2026-05-04
tags: [audit, sch-parser, csv-crosscheck, step-alignment, unknown-bytes, phase0]
related:
  - "[[260504_plan_22cat_audit_and_eval_overlay]]"
  - "[[260504_audit_phase0_extractable_fields]]"
  - "[[260504_audit_phase0_sch_parsing_gap]]"
status: phase-0-1d-complete
---

# Phase 0-1d: CSV ↔ .sch step-level alignment

> 사용자 제공 PNE 패턴 CSV 와 매칭되는 .sch 의 **step-by-step 정밀 비교**.
> Cross-check 로 unknown bytes (+108~+335 등) 의 의미 식별. 5건 신규 field 확정 + 1건 기존 추정 오류 정정.

---

## TL;DR

- 3 sample (Floating / 4cycle SOC30 / ECT GITT) step-by-step 매칭으로 **6건 신규 field 확정** + **1건 기존 추정 오류 정정**.
- ⭐ **+88 = V Limit upper, +92 = V Limit lower** 확정 — phase 0-1 추정 (+92=upper) 잘못. 실제는 +88 (CHG safety upper), +92 (DCHG safety lower).
- ⭐ **+12, +16, +20, +24, +28, +32 = step parameter** (VRef, IRef, time, end V/I) — phase 0-1 일치.
- ⭐ **신규 +36 = End Capacity cutoff (CHG)**, **+40 = End Capacity cutoff (DCHG)** (mAh).
- ⭐ **신규 +396 = 시험 온도 reference (°C, ECT only)** — 23°C 발견.
- ⭐ **+336 의미 정밀화**: record interval (s). ECT 시험 = 1s, 일반 시험 = 60s.
- CSV `Cycle` 행 = .sch 미저장 (가상 marker). CSV step 수 = (`.sch + Cycle 수 + 완료 1`).
- 도구: [`tools/sch_csv_step_align.py`](../../tools/sch_csv_step_align.py).

---

## 1. CSV ↔ .sch step type 매핑

| CSV `Type` | .sch type_name | 비고 |
|---|---|---|
| `Cycle` | (없음, skip) | CSV-only marker. .sch 미저장. |
| `Charge` | `CHG_CC` (Mode=CC) / `CHG_CCCV` (Mode=CC/CV) / `CHG_CP` (Mode=CP) | Mode 별 분리 저장 |
| `DisCharge` | `DCHG_CC` (Mode=CC) / `DCHG_CCCV` (Mode=CC/CV) | Mode 별 분리 |
| `Rest` | `REST` (0xFF03) 또는 `REST_SAFE` (0xFF07) | LOOP 후 REST 가 REST_SAFE 로 저장되는 경향 (검증 추가 필요) |
| `Loop` | `LOOP` (0xFF08) — 첫 N-1번 / `GOTO` (0xFF06) — 마지막 1번 | 마지막 Loop = GOTO |
| `완료` | `END` (0x0006) 또는 미저장 | sample 미발견 |

**계산식**: `len(CSV) = len(.sch) + len(CSV[Cycle]) + 1` (`완료` step 1건).

검증 (3 sample):
| Sample | CSV raw | CSV Cycle 수 | CSV-skip | .sch | 검증 |
|---|---|---|---|---|---|
| Floating | 5 | 1 | 3 | 4 | CSV-skip (3) + Loop split (+1) = 4 ✓ |
| 4cycle SOC30 | 15 | 3 | 11 | 14 | 11 + Loop split (+3) = 14 ✓ |
| ECT GITT | 29 | 7 | 21 | 28 | 21 + Loop split (+7) = 28 ✓ |

→ Loop split 패턴: 매 Loop 마다 .sch 에 LOOP + GOTO 또는 LOOP + REST_SAFE 추가. 정확한 split 룰은 phase 0-2 에서 확정.

---

## 2. Step block byte offset 의미 (확정)

CSV step 컬럼과 일치 검증된 byte offset:

| Offset | Type | 의미 | CSV 컬럼 | Sample 값 검증 |
|---|---|---|---|---|
| +0 | uint32 | step_number | StepNo | ✓ |
| +8 | uint32 | type_code | Type+Mode | ✓ |
| **+12** | float32 | **CHG VRef (mV)** = CC target V 또는 CV target V | VRef(V) × 1000 (CHG only) | Floating: 4550 = 4.55V CC/CV target ✓ <br> ECT: 4530 ✓ |
| **+16** | float32 | **DCHG VRef (mV)** | VRef(V) × 1000 (DCHG only) | 4cycle: 2500 = 2.5V ✓ <br> ECT: 2500 ✓ |
| **+20** | float32 | **IRef (mA)** | IRef(A) × 1000 | Floating: 2150 ✓ <br> 4cycle: 1000 ✓ <br> ECT: 1177 ✓ |
| **+24** | float32 | **End time (s)** | End "t > HH:MM:SS" | REST 600 ✓ <br> Floating: 1.037e7 ≈ 120일 ✓ <br> ECT: 25200 = 7시간, 21600 = 6시간 ✓ |
| **+28** | float32 | **DCHG End V cutoff (mV)** | End "V < x" | 4cycle: 3000 = 3.0V ✓ <br> ECT: 2750 = 2.75V ✓ |
| **+32** | float32 | **CHG End I cutoff (CV mA)** | End "I < x" | Floating: (없음) <br> 4cycle: (CCCV 없음 in step1) <br> ECT: 118 = 0.118A ✓ |
| **+36** ⭐ | float32 | **CHG End Capacity cutoff (mAh)** ⭐ NEW | End "C > x" | ECT: 6000 = 6.0Ah ✓ |
| **+40** ⭐ | float32 | **DCHG End Capacity cutoff (mAh)** ⭐ NEW | End "C > x" | ECT: 6000 = 6.0Ah ✓ |
| +52 | uint32 | goto_target_step (LOOP only) | (LOOP) | ✓ |
| +56 | uint32 | loop_count / goto_target | "Repeat N" | ECT Loop step: 4 ✓ |
| **+84** | uint32 | **mode flag** = 1 (active step) / 0 (LOOP/GOTO/END) | (CSV 미표시) | 모든 active step = 1 ✓ |
| **+88** ⭐ | float32 | **V Limit upper (mV)** ⭐ CONFIRMED | "V≤V_hi" | Floating: 4600 ✓ <br> ECT REST: 4650 ✓ <br> ECT CHG: 4580 ✓ |
| **+92** ⭐ | float32 | **V Limit lower (mV)** ⭐ CORRECTED (phase 0-1 오류 정정) | "V_lo≤V" | 4cycle DCHG: 2950 (CSV "2.45≤V" 직접 매칭 X — system default 의심) <br> ECT REST: 1500 <br> ECT DCHG: 2700 (CSV "1.8≤V" 와 mismatch — 매 step default 일 수도) |
| **+96** ⭐ | float32 | **I Limit upper (mA)** ⭐ CONFIRMED | "I≤I_hi" | Floating: 2200 (CSV 2.2 A) ✓ <br> ECT: 1227 (CSV 1.227A) ✓ |
| **+100** ⭐ | float32 | **I Limit lower (mA)** ⭐ CONFIRMED | "I_lo≤I" | Floating: 2100 ✓ <br> ECT: 1127 ✓ |
| +104 | float32 | capacity_limit_mAh | Safety Capacity upper × 1000 | ✓ |
| **+336** ⭐ | float32 | **record_interval_s (primary)** ⭐ CONFIRMED | (CSV 미표시) | ECT: **1s**, 일반: 60s — ECT 시험은 sampling 더 빠름! |
| +372 | float32 | end_condition_value_pct | (DOD/SOC %) | 4cycle Loop step: 30 (SOC30) ✓ |
| +388 | float32 | record_interval_s (secondary) | (CSV 미표시) | 60s 일정 (의미 정밀화 필요) |
| **+396** ⭐ | float32 | **시험 온도 reference (°C) ?** ⭐ NEW | (CSV 미표시) | ECT: **23°C** (모든 step 동일), 다른 sample: 미발견 |
| +500 | uint32 | end_condition_type | (DOD%/SOC% type code) | ✓ |
| +504 | uint32 | end_condition_enabled | | ✓ |
| +580 | uint32 | goto_repeat_count (LOOP) | "Goto repeat" | ✓ |

---

## 3. Phase 0-1 의 추정 정정

### `+92` 의 의미 — Upper → Lower 정정

**Phase 0-1 추정**: `+92 = safety upper voltage (DCHG sample 모두 2950)`.

**Phase 0-1d 정정**: 실제로는 `+88 = V Limit upper`, `+92 = V Limit lower`.

근거:
1. **Floating CHG_CCCV step 1**: +88 = 4600 mV. CSV `V Limit = V≤4.6` (V upper limit). **+88 이 upper** 확정.
2. **ECT REST step 1**: +88 = 4650 mV (전체 시험의 V upper). +92 = 1500 mV (전체 시험의 V lower). **REST 도 system 의 V upper/lower 보유**.
3. **DCHG step**: +88 미사용 (CHG 만 존재), +92 = 2700~2950 (V lower). CSV `V Limit = 2.45≤V` 의 lower 와 일치하지 않는 sample 있어 **system default 가 적용되는 case 일 수도**.

→ Phase 0-1 의 `260504_audit_phase0_sch_parsing_gap.md` §4 #1 의 "+92 = safety upper voltage" 해석을 `+88 upper / +92 lower` 로 정정 필요.

---

## 4. ECT 시험의 특수성

ECT GITT sample (260316 M47 ATL ECT GITT) 에서 발견:

1. **`+336 = 1s`** (다른 sample 60s). ECT 는 데이터 sampling 1초로 빠름 → 정밀 측정.
2. **`+396 = 23.0`** (모든 step 동일). 23°C — chamber 온도 reference 의심.
3. **GITT_START / GITT_END type 사용**. 22 카테고리의 GITT_PULSE 와 일치.
4. **End condition multi-OR**: `End = "I < 0.118 or t > 07:00:00.0 or C > 6.0"`. 3 condition 중 가장 먼저 만족하는 조건 적용. **+24 (t)**, **+32 (I)**, **+36 (C)** 모두 사용.

→ ECT 시험은 22 카테고리 외 신규 카테고리가 아니라 **GITT_PULSE 의 변형**. 단 sub-pattern (ACT 가변 vs GITT) 별 분류 필요.

---

## 5. 분류기 룰 보강 후보 (Phase c)

본 alignment 결과로 `_classify_loop_group` 의 의미 명확화 + 정확도 보강 가능:

### 즉시 fix 가능 (Phase c α)

1. ⚠️ **`v_chg` 키 mismatch** — Phase 0-1a 발견 (1줄 fix). FLOATING 분류 무력 해결.
2. **+92 의미 정정** — 분류기 코드에서 +92 를 V upper 로 사용하는 부분이 있다면 +88 로 교체.

### 신규 분류 룰 (Phase c β)

3. **+396 (시험 온도)** 활용 — temperature-based 분류 가능. 예: ECT (>=20°C, sampling=1s) 식별.
4. **+336 (record interval)** 활용 — 1s = ECT 또는 GITT, 60s = 일반 시험 식별.
5. **+36/+40 (End C cutoff)** 활용 — capacity 기반 cycling 식별.
6. **+88/+92 V limits** 활용 — 시험의 V range 식별 (RPT vs ACCEL vs Hybrid).

### Header keyword classifier (Phase c γ — 가장 큰 영향)

`+664 schedule_description` keyword 추출 (Phase 0-1b §1):
- "hysteresis" → HYSTERESIS_DCHG/CHG
- "Floating" → FLOATING
- "GITT" → GITT_PULSE
- "ECT" → GITT_PULSE 변형 (또는 신규)
- "DCIR" → SOC_DCIR / PULSE_DCIR
- "RPT" → RPT
- "ACCEL"/"Si Hybrid"/"SEU" → ACCEL

---

## 6. Phase 0-2 추가 검증 후보

본 3 sample 검증으로 발견된 가설 — 187 전수에서 일관성 확인 필요:

| 가설 | 검증 방법 |
|---|---|
| `+88 = V upper, +92 = V lower` 모든 시험에 일관 | 187 전수 dump → V limit pattern 분포 |
| `+336 = 1s` ECT/GITT only, `+336 = 60s` 일반 | 187 전수 → +336 분포 |
| `+396 = 23°C` ECT only, 다른 시험 = 0 또는 미사용 | 187 전수 → +396 분포 |
| Loop split (`LOOP` + `GOTO` 또는 `LOOP` + `REST_SAFE`) 의 정확한 룰 | 187 전수 → step type 시퀀스 패턴 |
| `+92` system default (DCHG=2.95V) 인지, step-별 가변인지 | 다양한 V cutoff 의 DCHG 시험 검증 |

---

## 7. 산출물

- 신규: [`tools/sch_csv_step_align.py`](../../tools/sch_csv_step_align.py) — step-by-step alignment 도구
- 신규: [`tools/sch_csv_step_align.md`](../../tools/sch_csv_step_align.md) — 3 sample × 단계별 dump (628 줄)
- 갱신 후보: [`260504_audit_phase0_extractable_fields.md`](260504_audit_phase0_extractable_fields.md) — `+92` 의미 정정 + 신규 field +36/+40/+396 추가
- 갱신 후보: [`260504_audit_phase0_sch_parsing_gap.md`](260504_audit_phase0_sch_parsing_gap.md) — §4 의 `+92` 해석 정정

---

## 8. Related

- [[260504_plan_22cat_audit_and_eval_overlay]] — 5단계 plan
- [[260504_audit_phase0_extractable_fields]] — Phase 0-1b (4 sample header dump)
- [[260504_audit_phase0_sch_parsing_gap]] — Phase 0-1a (코드 review)
- 도구: [`tools/sch_csv_step_align.py`](../../tools/sch_csv_step_align.py)

---

## 9. 참고 코드 위치

- `DataTool_dev_code/DataTool_optRCD_proto_.py:7594` — `_parse_pne_sch` 본체
- L7689, L7711 — Parser 가 emit 하는 `voltage_mV`, `current_mA`, `time_limit_s`, `end_voltage_mV`, `end_current_mA`, `capacity_limit_mAh` (이미 추출)
- **신규 추가 후보**: `+12 chg_target_v_mV`, `+16 dchg_target_v_mV`, `+36/+40 end_capacity_cutoff_mAh`, `+88 v_limit_upper_mV`, `+92 v_limit_lower_mV`, `+96 i_limit_upper_mA`, `+100 i_limit_lower_mA`, `+336 record_interval_s`, `+396 chamber_temp_c`
