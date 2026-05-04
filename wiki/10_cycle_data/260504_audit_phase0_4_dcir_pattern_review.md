---
title: "Phase 0-4: DCIR 패턴 PNE UI cross-check — SOC/DOD 이동 조건 mechanism"
date: 2026-05-04
tags: [audit, pne-ui, dcir, soc-jump, dod-jump, phase0-4, multi-condition-end]
related:
  - "[[260504_audit_phase0_3_pne_ui_review]]"
  - "[[260504_audit_phase0_2_187_validation]]"
status: phase-0-4-complete
---

# Phase 0-4: DCIR 패턴 (`SOC별 DCIR 충방전_2610mAh`) UI review

> Phase 0-3 (ECT GITT) 에 이은 두 번째 PNE UI 캡처 분석.
> ⭐⭐⭐ **SOC/DOD 이동 조건의 reference-step mechanism** 발견 — DCIR 분류기 정확도의 핵심.

---

## TL;DR

- **SOC별 DCIR** 시험의 핵심 mechanism = **"Step N (Char./Dis.) 의 AH/V 의 SOC X% → 이동스텝 NEXT/M"** 형식의 conditional jump.
- 우리가 식별한 `+372 (value_pct) + +500 (EC type) + +504 (enabled)` 외에 **reference step number + AH/V 종류 + jump target step** 가 binary 의 unknown 영역에 저장됨.
- ⭐ **End condition 이 multi-condition OR 형식**: 한 step 에 4-5 condition 동시 가능 (V, I, t, C, **SOC ref step**, **DOD ref step**), 각각 별도 jump target.
- ⚠️ **H9 가설 reject**: header `+656` ≠ 저장 주기. 본 sample binary `+656 = 2`, UI `저장 주기 = 106`.
- DCIR 시험은 **chamber 온도 미사용** (`+396` 비어있음) — Phase 0-2 일관.
- 셀 온도 safety **= 60°C (high temp protection)** — ECT GITT (0/0 default) 와 다름.
- 저장 주기 = step 수 추정 (106 = 105+1, 29 = 28+1).

---

## 1. UI 캡처 요약

캡처 대상: `Ref_SOC별 DCIR 충방전_2610mAh.csv` ↔ `성능/250513...SBR 0.9 DCIR.sch`

| 항목 | 값 |
|---|---|
| n_steps (binary) | 105 |
| n_steps (CSV) | 106 (= 105 + 완료 1) |
| UI 저장 주기 | **106 회** |
| binary `+656` | **2** ← UI 와 mismatch |
| `+336` first | 1.0s (sampling 1s) |
| `+396` first | (없음) — chamber 온도 미사용 |

### 시험 안전 조건 (DCIR vs ECT GITT 비교)

| Field | DCIR (본 sample) | ECT GITT (Phase 0-3) |
|---|---|---|
| 최대 전압 | 4.750 V | 4.700 V |
| 최소 전압 | 1.900 V | 1.800 V |
| 최대 전류 | 10.000 A | 20.000 A |
| **최대 셀 온도** | **60.0 °C** | 0.0 °C (default) |
| **최소 셀 온도** | 0.0 °C | 0.0 °C |
| 최대 용량 | 2.871 Ah | 6.195 Ah |
| 충/방전 용량 변화량 | 0% | 0% |
| **저장 주기** | **106 회** | 29 회 |

→ ⭐ **셀 온도 limit 이 시험별로 다름** 검증. DCIR 은 60°C high temp protection (cell 보호용 사용), ECT GITT 는 default 0/0.

---

## 2. ⭐⭐⭐ 핵심 발견: SOC/DOD 이동 조건 mechanism

### Step 28 (DOD 100% jump) — 캡처 4

```
Step 28: Discharge CC, 2.500V, 1.307A
End: "Step 27 DOD 100.0%(AH) Move NEXT"
```

UI panel detail:
- 종료전압/전류/시간/용량 모두 0
- ⭐ **이동 조건**: `Step 27(Char.) AH 의 DOD 100 % → 이동스텝 NEXT`
- 의미: **step 27 에서 charge 한 양 (AH 누적) 의 100%** 만큼 방전하면 NEXT step 으로 이동
- = **CHG-DCHG 1:1 capacity matching pattern** (DCIR pulse 측정의 표준)

### Step 29 (SOC 1% jump + multi-condition) — 캡처 3

```
Step 29: Charge CC/CV, 4.550V, 0.522A
End: "I < 0.055 Move NEXT or Step 11 SOC 1.0%(AH) Move N(EXT)"
```

UI panel detail:
- 종료전류 = **0.055 A** → +32 ✓
- 종료시간/용량/Power/WattHour/DeltaVp = 0
- ⭐ **이동 조건**: `Step 11(Char.) AH 의 SOC 1 % → 이동스텝 NEXT`
- 의미: 두 condition OR — **CV cutoff 도달** 또는 **step 11 에서 charge 한 양의 1% 추가 도달** → NEXT
- = **SOC 1% incremental charge** (다음 SOC level 로 진행)

### DCIR 패턴의 step 구조 (step 18~30 = 1 cycle = 1 SOC level)

```
step 18: Charge CC/CV (0.05C, 20s)         ┐ rate별 pulse charge
step 19: Discharge CC (0.05C, DOD 100%)    │   (charge 양만큼 방전)
step 20: Rest 30min                         │
step 21: Charge CC/CV (0.1C, 20s)          │
step 22: Discharge CC (0.1C, DOD 100%)     │
step 23: Rest 30min                         │
step 24: Charge CC/CV (0.2C, 20s)          │  (SOC 측정용 pulse)
step 25: Discharge CC (0.2C, DOD 100%)     │
step 26: Rest 30min                         │
step 27: Charge CC/CV (0.5C, 20s)          │
step 28: Discharge CC (0.5C, DOD 100%)     ┘
step 29: Charge CC/CV (0.2C) → Step 11 SOC 1%   ← SOC level up
step 30: Loop 20회 → 다음 Cycle             ← SOC 1%, 2%, ..., 20%
```

→ **SOC 별 DCIR**: SOC 1%~20% 각 level 에서 4 rate (0.05/0.1/0.2/0.5C) pulse 측정 후 DOD 100% recharge → SOC 다음 level 로.

22 카테고리 의 `SOC_DCIR` 와 정확히 일치하는 패턴. 분류기에서 본 mechanism 이해 시 정확한 식별 가능.

---

## 3. End Condition 구조 — Multi-condition OR

DCIR 캡처에서 명확:

| Step | End condition 1 | OR | End condition 2 | OR | End condition 3 |
|---|---|---|---|---|---|
| 18 | I < 0.055 → NEXT | OR | t > 0:00:20 → NEXT | — | — |
| 19 | Step 18 DOD 100%(AH) → NEXT | — | — | — | — |
| 27 | I < 0.055 → NEXT | OR | t > 0:00:20 → NEXT | — | — |
| 28 | Step 27 DOD 100%(AH) → NEXT | — | — | — | — |
| 29 | I < 0.055 → NEXT | OR | **Step 11 SOC 1.0%(AH) → NEXT** | — | — |

**Condition type list (UI 에서 추론)**:
- `종료전압` (V threshold)
- `종료전류` (I threshold)
- `종료시간` (t threshold) — D + HH:MM:SS + ms
- `종료용량` (Capacity threshold, Ah)
- `Power` (W) — phase 0-3 에서 발견, 본 sample 에서 0
- `End WattHour` (Wh)
- `Delta Vp` (V Pick Drop)
- `종료온도` (°C)
- ⭐ **SOC ref-step (`Step N (kind) AH/V 의 SOC X%`)** — DCIR 핵심
- ⭐ **DOD ref-step (`Step N (kind) AH/V 의 DOD X%`)** — DCIR 핵심

각 condition 별로 **Move NEXT** / **Move Step N** / **Move (other)** 의 jump target 별도 저장.

---

## 4. SOC/DOD 이동 조건의 binary field 후보

UI 의 SOC/DOD jump 입력 폼:

```
[Step 11(Char.) ▾] [AH ▾] 의 SOC [1] % → 이동스텝 [NEXT ▾]
[Step 27(Char.) ▾] [AH ▾] 의 DOD [100] % → 이동스텝 [NEXT ▾]
```

→ **5 sub-field**:
1. `ref_step_number` (uint32) — 기준 step 번호 (11, 27 등)
2. `ref_step_kind` (uint32 enum) — Char./Dis./Rest/...
3. `ref_capacity_basis` (uint32 enum) — AH or V (V = voltage 기반?)
4. `pct_threshold` (float32) — 1.0%, 100.0%, 5.0% 등
5. `jump_target_step` (uint32) — NEXT (= 0 or step+1?) or specific step number

→ binary 는 +500 (`end_condition_type` = 2048 DOD% / 18432 SOC%) + +372 (`value_pct`) + +504 (`enabled`) 외에 **5 field** 추가 필요. unknown +108~+335 영역 또는 +376~+495 영역.

**검증 가설 H15**: SOC/DOD jump 의 binary 위치 = +108~+335 또는 +376~+495 의 unknown 영역.

검증 방법: SOC% jump 사용 step (예: step 29 = +500=18432) 의 binary 에서 11 (ref step), 1.0 (% — 이미 +372 일 가능성), 0/NEXT 값 search.

---

## 5. 가설 검증 결과 (Phase 0-3 의 H9 ~ H13)

본 DCIR sample 로 추가 검증:

### H9: header `+656` = 저장 주기 ❌ REJECT
- DCIR sample: UI 저장 주기 = 106, binary `+656 = 2`
- ECT GITT: UI 저장 주기 = 29, binary `+656 = 5` 또는 13
- → **저장 주기 ≠ +656**. `+656` 의 의미 여전히 미해결
- 새 가설: 저장 주기 = step 수 + 1 (= n_csv_rows). 매 schedule 마다 자동 계산 값.

### H10: Power/WattHour/Delta Vp binary 위치
- 본 DCIR sample 도 모두 0 → unknown 영역도 0. 사용 시험 미발견.
- DCIR pulse 측정에서 Delta Vp 사용 안 함? 또는 다른 sample 에서 사용?
- → **추가 sample 조사 필요**.

### H11: End condition jump target field
- DCIR 패턴 다수 step 이 "Move NEXT" 단순. step 13 의 "V > 4,590 Move Step 16" 같은 case 본 sample 에 미발견.
- ⭐ **신규 발견**: DCIR 의 SOC/DOD jump 가 다른 형태의 jump target — `Step N(kind) AH/V 의 SOC/DOD %`. binary 매핑 필요.

### H12: CR mode — 미발견 (DCIR 도 CC/CC/CV 만 사용)

### H13: 임피던스/셀 온도/용량 step limit binary 위치
- DCIR step 73: 전압 4.6/2.4, 전류 0/0, 임피던스 0/0, 셀온도 0/0
- 셀 온도 safety = 시험 안전 (header) 에서 60°C (high) — step level 은 0
- → **header level 만 셀 온도 safety 활성. step level 은 미사용 패턴.**

---

## 6. DCIR 분류기 정확도 향상 plan

### 22 카테고리의 DCIR 관련 카테고리

| 카테고리 | 패턴 | DCIR sample 매핑 |
|---|---|---|
| `PULSE_DCIR` | EC + 짧은 DCHG (≤30s) + DCHG≥2 | step 18-28 (0.05-0.5C pulse) |
| `RSS_DCIR` | N=1 + EC + DCHG≥4 + body≥10 | (전체 schedule scope) |
| `SOC_DCIR` | EC≥4 + body≥8 + N=5~19 + EC type 다양성 ≥3 | (전체 schedule scope) |

본 sample 의 DCIR schedule 은 **전체로는 SOC_DCIR 또는 RSS_DCIR**, **개별 cycle 내부는 PULSE_DCIR** 의 hybrid.

### 향상 방법

⭐⭐⭐ **SOC/DOD ref-step jump 식별 시 SOC_DCIR 분류 명확**:
- `+500 = 18432 (SOC%)` + ref_step_number 비0 → SOC 별 DCIR 시험
- `+500 = 2048 (DOD%)` + ref_step_number 비0 → DOD 기반 DCIR 또는 hysteresis 변형

⭐⭐ **+336 sampling rate**:
- 1s = SOC_DCIR / 일반 DCIR
- 0.1s = pulse measurement (RSS_DCIR 의 short pulse)
- 60s = 일반 cycling

→ Phase c (분류기 fix) 의 SOC_DCIR / RSS_DCIR / PULSE_DCIR disambiguate 룰 보강:
1. `+500 == 18432` (SOC%) 검출 → SOC_DCIR
2. `+336 < 1` 검출 + DCHG 짧은 step → RSS_DCIR / PULSE_DCIR
3. ref-step jump 사용 → 명확한 SOC/DOD 시험

---

## 7. 신규 field summary (Phase 0-3 + 0-4 통합)

본 phase 0-4 추가 신규 field:

| 후보 | UI field | binary 위치 (추정) | 우선순위 |
|---|---|---|---|
| ⭐⭐⭐ `ref_step_number` | "Step N(...)" jump | unknown +108~+335 | DCIR 분류 핵심 |
| ⭐⭐⭐ `ref_step_kind` | "Char./Dis." enum | 동상 | 동상 |
| ⭐⭐ `ref_capacity_basis` | "AH or V" enum | 동상 | 동상 |
| (✓) `pct_threshold` | SOC/DOD % | `+372` (value_pct) ✓ | 이미 식별 |
| ⭐⭐ `jump_target_step` | "NEXT" or step N | 동상 | 동상 |
| ⭐ `end_condition_array_size` | multi-condition 갯수 | 동상 | OR 구조 표현 |

→ DCIR 분류 핵심 = ref-step jump field 5건 식별.

---

## 8. 본 review 의 결론

### Phase 0-4 의 가장 큰 가치

1. ⭐⭐⭐ **SOC/DOD 이동 조건 mechanism** 발견 — DCIR 분류기 정확도의 핵심 mechanism. 22 카테고리 중 3개 (`SOC_DCIR`, `RSS_DCIR`, `PULSE_DCIR`) disambiguate 의 prior 가 됨.

2. ⭐⭐ **End condition 이 multi-condition OR 구조** 확인 — 한 step 에 4-5 condition 동시. 우리 binary 식별 (+500/+504) 으로는 single condition 만 표현. binary 의 array 구조 추가 식별 필요.

3. ⚠️ **H9 reject** — `+656` 저장 주기 가설 reject. 더 좋은 해석: 저장 주기 = `n_steps + 1` (자동 계산).

4. **셀 온도 safety 가 시험별로 다름** — DCIR=60°C, ECT GITT=0°C. 시험 안전 group 식별 후보.

### Phase c 의 PR 후보 갱신 (Phase 0-4 추가)

| Sub-step | 작업 | 우선순위 |
|---|---|---|
| (c-α) `v_chg` 키 mismatch fix | Phase 0-1a | ⭐⭐⭐ |
| (c-β1) parser 9 confirmed field 추가 | Phase 0-2 | ⭐⭐⭐ |
| (c-β2) parser header 5 field | Phase 0-3 | ⭐⭐ |
| (c-β3) Delta Vp / Power / WattHour | Phase 0-3 H10 | ⭐⭐ |
| **(c-β4) SOC/DOD ref-step jump field 5건 식별** | Phase 0-4 H15 | **⭐⭐⭐ DCIR 분류 핵심** |
| (c-γ) keyword + `+336 < 5` hint | Phase 0-2 | ⭐⭐⭐ |
| (c-δ) End condition jump target | Phase 0-3 H11 | ⭐⭐ |
| **(c-ε) Multi-condition OR end array** | Phase 0-4 | ⭐⭐ |

---

## 9. 다음 단계 권장

본 phase 0-4 의 **SOC/DOD jump field** 식별이 **Phase c 작업 전에 필수**:

### 옵션 A: Phase 0-5 (SOC/DOD jump binary search)
- DCIR sample 의 step 28, 29 binary dump → 11, 27 (ref_step), 100, 1.0 (pct), NEXT (target) 값 search
- unknown +108~+335 의 어느 offset 인지 식별
- 187 전수 적용 → ref-step jump 사용 시험 분포

### 옵션 B: 본 grilling session wrap → Phase c 별도 session
- 모든 finding 정리 완료
- Phase c 의 implementation 은 별도 session 에서 진행
- 본 session 은 audit phase 종료

추천: **옵션 A**. SOC/DOD jump binary 매핑 식별이 분류기 fix 전 필수 정보. 본 worktree 안에서 binary search 빠르게 가능.

---

## Related

- [[260504_audit_phase0_3_pne_ui_review]] — ECT GITT UI review
- [[260504_audit_phase0_2_187_validation]] — 187 전수 검증
- [[260504_audit_phase0_csv_sch_step_alignment]] — step alignment
- [[260504_plan_22cat_audit_and_eval_overlay]] — 5단계 plan
