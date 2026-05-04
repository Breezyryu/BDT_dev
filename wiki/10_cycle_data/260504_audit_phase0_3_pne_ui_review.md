---
title: "Phase 0-3: PNE 패턴 편집기 UI ↔ .sch binary cross-check"
date: 2026-05-04
tags: [audit, pne-ui, cross-check, phase0-3, unknown-bytes, sch-parser]
related:
  - "[[260504_audit_phase0_2_187_validation]]"
  - "[[260504_audit_phase0_csv_sch_step_alignment]]"
  - "[[260504_audit_phase0_extractable_fields]]"
status: phase-0-3-complete
---

# Phase 0-3: PNE 패턴 편집기 UI ↔ .sch binary cross-check

> 사용자 제공 PNE 패턴 편집기 UI 캡처 (5882mAh_ECT 패턴11 GITT) 검토.
> Phase 0-2 까지 식별 못한 **신규 field 약 15+ 건 발견**. 대부분 step block 의 unknown +108~+335 / +376~+495 에 저장 추정.

---

## TL;DR

- PNE UI 가 step 별 **약 25개 field** 보유. 우리가 binary 분석에서 식별한 ~10 field + **신규 15+ field**.
- ✅ 우리 식별한 매핑은 **모두 UI 와 일치 검증**: VRef/IRef/End/V·I limits/Chamber temp/record interval.
- ⭐ **Mode CR (Constant Resistance)** dropdown 옵션 — 우리 `_SCH_TYPE_MAP` 에 없음.
- ⭐ **End Condition 추가 7건**: Power, End WattHour, **Delta Vp (Pick 전압 Drop)** ⭐⭐⭐ DCIR 핵심, 종료온도, CP-mode 연동, Cycle Pause, SOC 이동.
- ⭐ **Step 안전 조건 추가 3건**: 임피던스 limit, 셀 온도 limit, 용량 step limit.
- ⭐ **Step 기록 조건 추가 4건**: V/I/T 변화량 기반 sampling threshold, msec sampling.
- ⭐ **End condition jump target**: "Move NEXT" vs "Move Step N" — 우리 식별 못함.
- ⭐ **시험 안전 조건 (header) 추가 5건**: 셀 온도 max/min, capacity drift %, 저장 주기.
- 본 review 가 unknown 228 bytes (+108~+335) 영역의 reverse-engineering 가이드.

---

## 1. UI 캡처 요약

캡처 대상: `260316_270318_00_이성일_5882mAh_M47 ATL ECT GITT.sch` (Phase 0-1d sample, 28 step in binary / 29 row in UI).

### 시험 안전 조건 (header)

| UI Field | 값 | Binary 매핑 / 의미 |
|---|---|---|
| 최대 전압 | 4.700 V | (header — 검증 필요) |
| 최소 전압 | 1.800 V | (header) |
| 최대 전류 | 20.000 A | (header) |
| 최소 전류 | 0.000 A | (header) |
| **최대 셀 온도** | 0.0 °C | ⭐ NEW (header) |
| **최소 셀 온도** | 0.0 °C | ⭐ NEW |
| **최대 용량** | **6.195 Ah** | step block `+104` (CSV `Capacity upper`) ✓ |
| **최소 용량** | 0.000 Ah | ⭐ NEW |
| **충전용량 변화량** | **0%** | ⭐ NEW (capacity drift safety) |
| **방전용량 변화량** | **0%** | ⭐ NEW |
| **저장 주기** | **29 회** | header `+656` 후보 (검증 필요 — 본 sample binary `+656`=5 mismatch) |

→ "최대 용량 = 6.195 Ah" 가 step block `+104` 와 일치 → **header 와 step block 모두 capacity_limit 보유**. binary 에서 우리는 step block 의 `+104` 만 식별. header 에 같은 값이 또 있는지 검증 필요.

### Step 2 (Charge CC/CV) — 모든 field

**기본** (UI 좌측):

| UI Field | 값 | Binary | 검증 |
|---|---|---|---|
| Type | Charge | type_code → MAP | ✓ |
| Mode | **CC/CV** (CCCV) | type_code 0x0101 (CHG_CCCV) | ✓ |
| Charge(V) | **4.530** | `+12` | ✓ |
| Discharge(V) | 0.000 | `+16` (DCHG only, CHG=0) | ✓ |
| Current(A) | **1.177** | `+20` | ✓ |
| Chamber(°C) | **23.0** | `+396` | ✓ |

→ ⭐ Mode dropdown 옵션 = **CC, CV, CC/CV, CP, CR**. 우리 type_map 에 **CR (Constant Resistance) 없음**.

**End Condition (Other Condition)** — UI 우측 details:

| UI Field | 값 | Binary | 검증 |
|---|---|---|---|
| 측정횟수 | 0 | unknown | ⭐ NEW |
| 기준 Cycle | 0 | unknown | ⭐ NEW |
| 기준용량 | .000 Ah | unknown | ⭐ NEW |
| 기준Type | (없음) | unknown | ⭐ NEW |
| 용량효율 | 0% | unknown | ⭐ NEW |
| 감소포인트 | 0% | unknown | ⭐ NEW |
| 종료전압 | .000 V | `+28` (DCHG only) | CHG=0 ✓ |
| **종료전류** | **.118 A** | `+32` | ✓ |
| **종료시간** | **0 D 07:00:00 0 ms** | `+24` = 25200s | ✓ |
| **종료용량** | **6.000 Ah** | `+36` | ✓ |
| ⭐ Power | .000 W | unknown | NEW |
| ⭐ **End WattHour** | .000 Wh | unknown | NEW (Energy cutoff) |
| ⭐ **Delta Vp** | .000 V (Pick 전압 Drop) | unknown | ⭐⭐⭐ **NEW — DCIR 측정 핵심** |
| ⭐ 종료온도 | .0 °C | unknown | NEW |
| ⭐ 전 STEP (CP모드)와 연동 | 미사용 | unknown | NEW (CP chaining flag) |
| ⭐ Cycle 반복 후 Pause | 미사용 | unknown | NEW |
| ⭐ Goto 스텝 / Cycle 반복횟수 / Goto 반복횟수 | 0 / 0 / 0 | `+52, +56, +580` (LOOP only) | partial ✓ |
| ⭐ SOC 이동 조건 | 미사용 / SOC 0% / NEXT | unknown | NEW |

**Step 안전 조건 (Step 2)**:

| UI Field | 상한값 | 하한값 | Binary | 검증 |
|---|---|---|---|---|
| 전압(V) | **4.580** | 0.000 | `+88` (upper) ✓ / `+92` (lower) | ✓ partial |
| 전류(A) | **1.227** | **1.127** | `+96` / `+100` | ✓ |
| 용량(Ah) | 0.000 | 0.000 | unknown (step 안전 → step end `+36/+40` 와 다른 의미) | ⭐ NEW |
| ⭐ **임피던스(mΩ)** | 0.0 | 0.0 | unknown | ⭐ NEW |
| ⭐ **셀 온도(°C)** | 0.0 | 0.0 | unknown | ⭐ NEW |

**Step 기록 조건 (Step 2)**:

| UI Field | 값 | Binary | 검증 |
|---|---|---|---|
| **시간 변화** | **00:00:01 / 000 msec** | `+336` = **1.0s** | ✓ |
| ⭐ **전압 변화** | 0.000 V | unknown | NEW |
| ⭐ **전류 변화** | 0.000 A | unknown | NEW |
| ⭐ **온도 변화** | 0.0 °C | unknown | NEW |
| ⭐ **msec sampling** | 000 msec | unknown (또는 `+388`?) | NEW |

**Add Test Time**: 0 시간 0 분 → ⭐ NEW (test time extension)

---

## 2. End Condition Jump Target — "Move NEXT" vs "Move Step N"

UI 의 step list 에서:

| Step | End Condition | Jump |
|---|---|---|
| 2 | "I < 0.118" | **Move NEXT** |
| 2 | "t > 7:00:00" | **Move NEXT** |
| 4 | "V < 2,750" | **Move NEXT** |
| 4 | "t > 6:00:00" | **Move NEXT** |
| 4 | "C > ..." | **Move NEXT or C** (?) |
| 13 | "V > 4,590" | ⭐ **Move Step 16** |
| 13 | "t > 0:06:00" | Move NEXT |
| 27 | "V < 2,750" | Move NEXT |
| 27 | "t > 0:00:01" | Move NEXT |

⭐ **End condition 별 jump target 별도 저장**. step 13 의 "V > 4,590 Move Step 16" 처럼 multi-step charge 의 conditional jump-out.

→ **binary 의 unknown 영역에 jump target step number 저장 추정**. step 13 의 binary dump 에서 `16` (또는 step 16 의 ofs 정보) 검색 → 매핑 후보 식별 가능.

---

## 3. Mode CR (Constant Resistance) — 22 type 외

UI dropdown:

```
CC/CV
CC
CV
CP
CR    ← 우리 _SCH_TYPE_MAP 에 없음
```

`_SCH_TYPE_MAP`:
- `0x0101 CHG_CCCV` / `0x0102 DCHG_CCCV` (CCCV)
- `0x0201 CHG_CC` / `0x0202 DCHG_CC` (CC)
- `0x0209 CHG_CP` (CP)
- (CV / CR 없음)

→ **CR mode 의 type_code 미식별**. 187 sample 의 unknown type code (Phase 0-2 의 `UNK_0x...`) 0 건 → 본 데이터셋에 CR 시험 없음. 다른 lab/시험에서 등장 시 unknown 으로 catch 후 mapping 추가.

→ DCHG_CV (`0x???`) 도 동상 — DCHG_CCCV 외에 DCHG_CV 단독 type_code 가능성.

---

## 4. 신규 field summary — Parser 보강 후보

### Header 영역 (+940~+1919 의 unknown ~979 bytes 후보)

| 후보 | UI 필드 | 우선순위 |
|---|---|---|
| `chamber_temp_safety_max/min` | 최대/최소 셀 온도 | ⭐⭐ |
| `capacity_safety_min` | 최소 용량 | ⭐ |
| `chg_capacity_drift_pct` | 충전용량 변화량 | ⭐ |
| `dchg_capacity_drift_pct` | 방전용량 변화량 | ⭐ |
| `save_alarm_interval` | 저장 주기 (29) | ⭐⭐ — `+656` 일관성 검증 후 |

### Step block 영역 (+108~+335 + +376~+495 의 unknown 가운데)

| 후보 | UI 필드 | 우선순위 |
|---|---|---|
| `end_power_W` | Power | ⭐ |
| `end_watt_hour_Wh` | End WattHour | ⭐⭐ (수명 시험에 사용 가능) |
| ⭐⭐⭐ `end_delta_vp_V` | **Delta Vp (Pick 전압 Drop)** | **⭐⭐⭐ DCIR 측정의 핵심** |
| `end_temperature_C` | 종료온도 | ⭐⭐ (열폭주 안전) |
| `cp_mode_chained_flag` | 전 STEP CP 연동 | ⭐ |
| `cycle_pause_flag` | Cycle 반복 후 Pause | ⭐ |
| `soc_move_threshold_pct` + `soc_move_target_step` | SOC 이동 조건 | ⭐ |
| `impedance_safety_max_mOhm` | 임피던스 상한 | ⭐ |
| `cell_temp_safety_max/min_step_C` | step 별 셀 온도 limit | ⭐⭐ |
| `v_recording_threshold_V` | V 변화 sampling | ⭐⭐ (변화 기반 sampling) |
| `i_recording_threshold_A` | I 변화 sampling | ⭐⭐ |
| `t_recording_threshold_C` | T 변화 sampling | ⭐⭐ |
| `record_interval_msec` | msec sampling | ⭐ (`+388` 후보) |
| `end_condition_jump_target_1/2/3` | Move NEXT / Move Step N | ⭐⭐⭐ (multi-step charge 분류 핵심) |
| `add_test_time_h/min` | Add Test Time | ⭐ |

### Type 코드 추가

| 후보 | UI 옵션 | 우선순위 |
|---|---|---|
| **CR (Constant Resistance)** type_code | Mode dropdown | ⭐ (현재 데이터셋 미사용) |
| **DCHG_CV / DCHG_CR** type_code | Mode dropdown | ⭐ |

---

## 5. 검증 가설 (Phase 0-4 후보)

### H9: Header `+656` = "저장 주기" 회수 ?
- UI: 29
- Binary phase 0-2: 본 sample `+656` = 5 또는 13 (값 다름)
- → ⚠️ **불일치** — 다른 의미 또는 binary 의 다른 위치
- 검증: header dump 에서 29 (또는 그 변형) 값 search

### H10: Power/WattHour/DeltaVp 가 +108~+335 unknown 영역에 저장
- 본 sample 에서는 모두 0 → unknown 영역도 0 (Phase 0-2 일관)
- 검증: 187 중 **DCIR pulse 시험 (Delta Vp 사용 추정)** 또는 **Power 시험 (CHG_CP)** sample 의 binary dump 비교

### H11: End condition jump target field (Move Step N)
- step 13 의 "V > 4,590 Move Step 16"
- 검증: 해당 step 의 binary 에서 16 또는 step 16 ofs 값 search

### H12: CR (Constant Resistance) type_code
- Phase 0-2 type_count 에 unknown 0건 → 본 데이터셋에 CR 시험 없음
- 검증: 다른 lab 의 .sch sample 추가 확보

### H13: Step 안전 조건 (임피던스/셀 온도/용량 step) 의 binary 위치
- 본 sample 에서는 모두 0 → Phase 0-2 unknown 영역과 일관
- 검증: 임피던스 또는 셀 온도 step limit 사용한 시험 binary 비교

---

## 6. 본 review 가 분류기 정확도에 미치는 영향

### ⭐⭐⭐ 가장 큰 영향: Delta Vp 식별

**DCIR 측정 시험의 핵심 metric** = pulse 인가 후 voltage drop (ΔV) 측정 → 임피던스 계산.

현재 22 카테고리:
- `PULSE_DCIR` — short DCHG pulse 기반
- `RSS_DCIR` — 짧은 DCHG 다회
- `SOC_DCIR` — SOC 별 DCIR

세 카테고리 disambiguate 의 어려움 = step pattern 만 보면 비슷. **Delta Vp 사용 step 식별 시 명확한 DCIR 시험으로 분류 가능**.

→ Phase 0-3-α (Delta Vp 사용 시험 binary 비교) 우선 진행 가치 큼.

### ⭐⭐ 두 번째 영향: Multi-step charge 의 jump target

ACCEL / Hybrid / SOC setting 등 **multi-step charge** 시험에서 step jump 룰:
- 단순 sequential (Move NEXT) — 일반 cycling
- Conditional jump (Move Step N) — V cutoff 별 다른 step

Jump target field 식별 시 **multi-step charge pattern 의 정확한 reconstruction** 가능 → ACCEL / Hybrid / RPT 등 disambiguate.

### ⭐ 추가 metadata

- `chg/dchg_capacity_drift_pct` — 비0 시 capacity-aware cycling (수명 시험 식별)
- `cell_temp_safety_max/min` — 시험 환경 temperature group (저온/고온 시험 식별)
- `cycle_pause_flag` — 사용자 intervention 시험

---

## 7. Phase c (parser/분류기 fix) 의 우선순위 갱신

본 phase 0-3 review 로 우선순위 변경:

| Sub-step | 작업 | 우선순위 |
|---|---|---|
| (c-α) `v_chg` 키 mismatch fix (1줄) | Phase 0-1a | ⭐⭐⭐ 즉시 |
| (c-β1) parser 9 field 추가 (Phase 0-2 confirmed) | +88, +92, +96, +100, +36, +40, +336, +396, +84 | ⭐⭐⭐ |
| (c-β2) parser 5+ field 추가 (Phase 0-3 후보) | +664 schedule_desc, header chamber, header capacity_drift, save_alarm | ⭐⭐ |
| (c-β3) Delta Vp / Power / WattHour 식별 → parser 보강 | Phase 0-3 H10 검증 후 | ⭐⭐⭐ DCIR 분류 핵심 |
| (c-γ) keyword classifier (`+664`) + `+336 < 5s` hint | Phase 0-2 confirmed | ⭐⭐⭐ |
| (c-δ) End condition jump target 식별 | Phase 0-3 H11 검증 후 | ⭐⭐ multi-step charge |

---

## 8. 산출물

UI 캡처 source:
- 캡처 1: 전체 화면 (시험 안전 조건 + 29 step list + Step 2 detail)
- 캡처 2: Step 2 의 End Condition (Other Condition) 패널
- 캡처 3: Mode dropdown (CC/CV/CCCV/CP/CR)

Wiki 정리:
- 본 노트: 신규 field 15+ 건 식별 + 가설 4건 (H9-H13)
- 갱신 후보: [[260504_audit_phase0_2_187_validation]] 의 Parser 보강 후보 list 에 본 review 의 UI field 추가

---

## 9. 다음 단계 추천

본 phase 0-3 의 신규 field 식별로 **Phase c (parser/분류기 fix) 의 scope 확장 가능**.

권장 순서:
1. **즉시**: (c-α) `v_chg` fix (1줄)
2. **본 worktree 안**: (c-β1) confirmed 9 field parser 추가 → 187 분류 테스트
3. **별도 session**: (c-β3) Delta Vp / Power 식별 — DCIR 분류 정확도 핵심
4. **별도 session**: (c-δ) End condition jump target — multi-step charge

또는 (c) 전체를 별도 session 에서 통합 진행. 본 grilling session 의 audit phase (0-1, 0-2, 0-3) 는 충분히 깊어졌으므로 wrap 권장.

---

## Related

- [[260504_audit_phase0_2_187_validation]] — 187 전수 가설 검증
- [[260504_audit_phase0_csv_sch_step_alignment]] — 3 sample step alignment
- [[260504_audit_phase0_extractable_fields]] — 4 sample header dump
- [[260504_audit_phase0_sch_parsing_gap]] — parser 코드 review
- [[260504_plan_22cat_audit_and_eval_overlay]] — 5단계 plan
