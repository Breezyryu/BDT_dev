---
title: "Phase 0-5-α — ref_step_number binary offset 식별 (+501 uint8)"
date: 2026-05-05
tags: [phase0-5-alpha, sch-parser, ref-step, binary-search, dcir, hysteresis]
related:
  - "[[260504_audit_phase0_5_classifier_input_spec]]"
  - "[[260504_audit_phase0_4_dcir_pattern_review]]"
  - "[[260505_phase0_5_187_cycle_definitions]]"
status: phase-0-5-alpha-partial
---

# Phase 0-5-α — ref_step_number binary offset 식별

> [[260504_audit_phase0_5_classifier_input_spec]] §3.3 의 미식별 5 field 후보에 대한 binary search.
> ⭐⭐⭐ **`ref_step_number = +501 (uint8)` 식별 완료** — 368 .sch 전수 1,169 step 검증.
> 나머지 4 field (kind/basis/jump_target/delta_vp) 는 본 데이터셋에 default 케이스만 등장하여 식별 보류.

---

## TL;DR

- ⭐⭐⭐ **`ref_step_number = +501 (uint8)`** — 1,169 ref-using step 전수 검증.
  - 동등하게: `+500 uint32 = (ref_step_number << 8) | type_marker_low_byte`
  - 모든 ref-using sample 에서 type_marker_low_byte (= +500 byte 0) = `0` 으로 일정.
- 본 발견으로 [[260504_audit_phase0_5_classifier_input_spec]] §4.4 의 hysteresis 분류 룰 (`ec_type == 2048` for DCHG, `== 18432` for CHG) 의 의미가 명확해짐:
  - **2048 = `8 << 8`** → ref_step=8 (hysteresis 표준 cluster 첫 CHG step)
  - **18432 = `72 << 8`** → ref_step=72 (hysteresis CHG SOC% 의 표준 ref)
- ⚠️ `ref_step_kind` (Char./Dis.) / `ref_basis` (AH/V) / `jump_target_step` (NEXT/Step N) 는 **본 데이터셋의 모든 1,169 ref-using step 이 default 값** (Char. + AH + NEXT) 이라 별도 byte 식별 불가.
- ⚠️ `end_delta_vp_V` (DCIR pulse Vp Drop) 는 본 데이터셋에 사용 sample 없음 (Phase 0-3 H10 결론 일치).
- 산출:
  - [`tools/sch_phase0_5_alpha_dump.py`](../../tools/sch_phase0_5_alpha_dump.py) — DCIR sample step 구조 dump
  - [`tools/sch_phase0_5_alpha_binary_search.py`](../../tools/sch_phase0_5_alpha_binary_search.py) — DCIR sample binary search v2
  - [`tools/sch_phase0_5_alpha_validate.py`](../../tools/sch_phase0_5_alpha_validate.py) — 368 .sch 전수 cross-validate
  - [`tools/sch_phase0_5_alpha_other_fields.py`](../../tools/sch_phase0_5_alpha_other_fields.py) — kind/basis/jump_target enum search

---

## 1. 식별 방법

### 1.1 Known values (Phase 0-4 §2)

DCIR sample (`성능/250513_…/SBR 0.9 DCIR.sch`) 의 step 구조 (UI 캡처 ↔ binary):

| UI step (spec) | binary idx | binary step_num | type | EC | spec ref step | spec pct |
|---|---|---|---|---|---|---|
| Step 28 (DCHG 1.307A) | 26 | 27 | DCHG_CC | DOD% | **27** (preceding 0.5C CHG) | 100.0 |
| Step 29 (CHG 0.522A) | 27 | 28 | CHG_CCCV | SOC% | **11** (cluster start CHG) | 1.0 |

binary 의 `+500 uint32` 값:
- idx 26: `6912 = 0x1B00` → byte[1] = `0x1B = 27` ✓
- idx 27: `2816 = 0x0B00` → byte[1] = `0x0B = 11` ✓

→ ⭐⭐⭐ **+501 byte = ref_step_number** 가설.

### 1.2 Cross-validate (다른 sample)

#### Hysteresis sample 1 (`260316_LWN 25P 0.5C-10min volt hysteresis`)

| idx | step# | type | +500 | +501 byte | pct (+372) | 의미 |
|---|---|---|---|---|---|---|
| 12 | 13 | DCHG_CC | **2048** | **8** | 10.0 | DOD 10% ref step 8 ✓ |
| 18 | 19 | DCHG_CC | 2048 | 8 | 20.0 | DOD 20% ref step 8 ✓ |
| … | … | … | … | … | 30~90 | … (총 9 step) |
| 76 | 77 | CHG_CC | **18432** | **72** | 10.0 | SOC 10% ref step 72 ✓ |
| 82 | 83 | CHG_CC | 18432 | 72 | 20.0 | SOC 20% ref step 72 ✓ |
| … | … | … | … | … | 30~90 | … (총 9 step) |

→ Phase 0-5 spec §4.4 의 `2048 = DOD%`, `18432 = SOC%` 정체:
- **2048 = `8 << 8`** = ref_step 8 (hysteresis 표준 cluster 첫 CHG step)
- **18432 = `72 << 8`** = ref_step 72 (hysteresis CHG SOC%의 표준 ref step)

#### Hysteresis sample 2 (`260327_SDI Gen5+ MP1 0.2C-10min volt hysteresis`)

| step# | type | +500 | +501 byte | pct |
|---|---|---|---|---|
| 17~65 | CHG_CC | **3072** | **12** | 10/20/…/90 |

→ 3072 = `12 << 8` → ref_step 12 (이 schedule 의 cluster 첫 CHG step)

#### RSS DCIR sample (`260119_Q8 ATL Main 2.0C Rss RT`)

| idx | step# | type | +500 | +501 byte | pct |
|---|---|---|---|---|---|
| 12 | 13 | DCHG_CC | **2048** | **8** | 30 |
| 15 | 16 | DCHG_CC | 2048 | 8 | 20 |
| 18 | 19 | DCHG_CC | 2048 | 8 | 20 |
| 21 | 22 | DCHG_CC | 2048 | 8 | 15 |
| 46 | 47 | DCHG_CC | **10752** | **42** | 30 |
| 49 | 50 | DCHG_CC | 10752 | 42 | 20 |
| … | … | … | … | … | … |
| 80 | 81 | DCHG_CC | **19456** | **76** | 30 |
| 114 | 115 | DCHG_CC | **28160** | **110** | 30 |

→ 4 cluster (각 cluster 의 첫 CHG step ref): 8 / 42 / 76 / 110 ✓ (cluster 간격 34 step).

---

## 2. 368 .sch 전수 통계

### 2.1 사용 빈도

| 항목 | 값 |
|---|---|
| Files parsed | 368 |
| Total steps | 28,779 |
| Ref-step using steps (`ec504_enabled = 1` 그리고 `+501 byte ≠ 0`) | **1,169 (4.1 %)** |
| Files with ≥1 ref-step | **106 (28.8 %)** |

### 2.2 ref_step_number (+501 byte) 분포

| ref_step | count | 의미 (sample 기반 추정) |
|---|---|---|
| **8** | 334 | hysteresis 표준 cluster 첫 CHG step |
| **72** | 204 | hysteresis CHG SOC% 의 표준 ref |
| 15 | 62 | hysteresis sample 변형 |
| 76 | 60 | RSS_DCIR cluster 2 |
| 12 | 57 | hysteresis sample 변형 |
| 14 | 48 | RSS_DCIR cluster 1 |
| 42 | 42 | RSS_DCIR cluster 2 |
| 110 | 36 | RSS_DCIR cluster 3 |
| 145, 181, 6 | 36 ea | 기타 |
| 57, 13, 59, 117, 119, 17, 87, 96, 27 | 6~18 ea | DCIR/SOC_DCIR |

총 **47 종** unique ref_step 값. 범위: **6 ~ 181** (uint8 max 255 미만).

### 2.3 step type 별 ref_step 분포

| step type | total ref-using | top values |
|---|---|---|
| DCHG_CC | 715 | 8(318), 76(60), 14(48), 42(38), 110(36) |
| CHG_CC | 213 | 72(194), 8(10), 12(9) |
| CHG_CCCV | 206 | 12(48), 6(36), 57(16), 117(12), 17(10) |
| DCHG_CCCV | 35 | 15(31), 19(4) |

→ DCHG steps 가 압도적 다수 (61%) — DOD% 기반 jump (DCIR/Hysteresis 의 DCHG cluster).

### 2.4 pct (+372) at ref-step 분포

| pct | count | 의미 |
|---|---|---|
| 1.0 % | 20 | SOC 1% incremental (DCIR SOC level up) |
| 2.5 % | 31 | — |
| 5.0 % | 12 | — |
| **10.0 %** | 76 | hysteresis level 1 |
| 15.0 % | 72 | RSS_DCIR (15% step) |
| **20.0 %** | 341 | hysteresis + RSS_DCIR |
| **30.0 %** | 203 | hysteresis + RSS_DCIR (30% step) |
| 40~90 % | 45 ea | hysteresis level 4~9 |
| **100.0 %** | 144 | DOD 100% (DCIR full pulse) |

→ 분포가 매우 선명한 cluster 구조 — Phase 0-4 의 hysteresis (10/20/.../90) + RSS (15/20/30) + DCIR (100) 패턴 정확히 반영.

### 2.5 +500 byte 0 (type_marker_low_byte) 분포

| value | count |
|---|---|
| **0** | **1,169 (100 %)** |

→ ⚠️ 본 데이터셋의 **모든** ref-using step 에서 byte 0 = 0. 즉, **기본 type marker** (= "DOD%/SOC% with ref step" 만 사용). 다른 type marker 사용 sample 없음.

### 2.6 +500 byte 2/3 (high bytes) 분포

| value | count |
|---|---|
| **(0, 0)** | **1,169 (100 %)** |

→ ⚠️ 본 데이터셋의 모든 ref-using step 에서 high bytes = 0. 즉, ref_step_number 가 uint8 (0~255) 범위 내에서 충분 — uint16/uint32 변환 불필요.

---

## 3. 미식별 4 field 분석

### 3.1 ref_step_kind (Char./Dis. enum)

본 데이터셋 1,169 ref-using step 의 모든 ref step (8, 72, 12, 76 등) 이 **CHG step** (Char.) 을 가리킴 — Phase 0-4 spec §2 에서 "Step N(Char.) AH" 패턴 일관.

본 데이터셋에 "Step N(Dis.)" 케이스 없음 → **enum 값 식별 불가** (default = 0 으로 추정).

→ binary search 에서도 ref-using step 전수에서 동일 byte/uint16/uint32 값을 갖는 offset = `+504 (= ec_enabled = 1)` 만 발견. 즉, kind enum 은 **+500 byte 0 = 0 (default Char.)** 안에 인코딩되어 있을 가능성 가장 높음.

### 3.2 ref_basis (AH/V enum)

본 데이터셋의 모든 ref step jump 가 **AH 기반** ("Step N(Char.) AH 의 SOC/DOD X%"). V 기반 케이스 없음 → 식별 불가.

→ +500 byte 0 의 다른 bit 또는 별도 default field 안에 인코딩 추정.

### 3.3 jump_target_step (NEXT or Step N)

본 데이터셋의 모든 ref step jump 가 **NEXT** ("Move NEXT") — DCIR / hysteresis / RSS 모두 NEXT 만 사용.

→ NEXT 는 default (= 0 또는 step+1) 일 가능성. "Move Step N" 케이스가 본 데이터셋에 없으므로 **별도 byte 식별 불가**.

→ binary search 에서 monotone increasing offsets (per-step varying) 에 step_num 패턴 (`+0` 외) 미발견.

### 3.4 end_delta_vp_V (DCIR pulse Vp Drop)

[[260504_audit_phase0_3_pne_ui_review]] H10 에서 "Delta Vp 사용 시험 미발견" 이미 결론.
본 phase 0-5-α 도 동일 — 사용 sample 없음.

→ **PNE pattern editor 의 Pick V Drop 옵션을 활용한 시험이 본 데이터셋에 부재**. 식별 보류.

---

## 4. 결론 — 분류기 v2 정확도 영향

### 4.1 즉시 활용 가능 (proto 코드 fix 후보)

⭐⭐⭐ **`+501 = ref_step_number` 인코딩 인식** 으로 분류기 룰 보강:

```python
# Phase 0-5-α 검증 후 추가
def parse_end_condition(blk: bytes) -> dict:
    ec500 = struct.unpack_from('<I', blk, 500)[0]
    ec504 = struct.unpack_from('<I', blk, 504)[0]
    if ec500 == 0 or ec504 != 1:
        return {}
    type_marker = ec500 & 0xFF              # always 0 in observed data
    ref_step_number = (ec500 >> 8) & 0xFF   # ⭐⭐⭐ 이번에 식별
    pct = struct.unpack_from('<f', blk, 372)[0]
    return {
        'ref_step_number': ref_step_number,
        'pct_threshold': round(pct, 2),
        # type_marker, ref_kind, ref_basis, jump_target — default 가정
    }
```

→ Phase 0-5 spec 의 hysteresis 분류 룰을 **fixed value (`2048` / `18432`) 매칭에서
ref_step 사용 일반 룰** 로 일반화 가능:

```python
# Before (Phase 0-5 spec §4.4):
if any(s.get('end_condition', {}).get('type') == 2048 for s in ec_on_dchg):
    return 'HYSTERESIS_DCHG'
# = 특정 schedule (ref_step=8 인 표준 hysteresis) 만 매칭

# After (Phase 0-5-α):
if any(s.get('end_condition', {}).get('ref_step_number', 0) > 0
       for s in ec_on_dchg):
    # DCHG step 에 ref-step jump → DOD% 기반 부분 방전 시험
    if N == 1 and not has_short_dchg:
        return 'HYSTERESIS_DCHG'
    elif N == 1 and has_ec and len(dchg) >= 4:
        return 'RSS_DCIR'
    elif 5 <= N < 20 and len(ec_steps) >= 4:
        return 'SOC_DCIR'
    # ...
```

→ **HYSTERESIS_DCHG / RSS_DCIR / SOC_DCIR / PULSE_DCIR disambiguate 정확도 향상**.

### 4.2 보류 항목

| Field | 이유 | 후속 |
|---|---|---|
| `ref_step_kind` | 모든 sample 이 Char. | non-default sample 확보 또는 vendor spec |
| `ref_basis` | 모든 sample 이 AH | 동상 |
| `jump_target_step` | 모든 sample 이 NEXT | "Move Step N" 사용 sample 확보 |
| `end_delta_vp_V` | 사용 sample 없음 | DCIR pulse 측정 추가 sample 또는 vendor spec |

→ 이 4 field 는 **PNE vendor spec 문서 확보 또는 non-default 시험 sample 신규 측정** 후 식별 가능.

### 4.3 187 폴더 cycle definitions 영향

[[260505_phase0_5_187_cycle_definitions]] 의 분류 결과에 본 발견 적용 시:

- HYSTERESIS_DCHG 230 group / HYSTERESIS_CHG 198 group 분류는 정확 (ref_step=8/72 fix)
- SOC_DCIR 20 group + RSS_DCIR 8 group + PULSE_DCIR 856 group 의 ref_step 기반 disambiguate 가능 → 향후 분류기 v3 에서 조정

→ **본 phase 0-5-α 발견은 분류기 v3 의 base** 로 활용.

---

## 5. 다음 단계

| 순서 | 작업 | 예상 cost |
|---|---|---|
| 1 | proto `_parse_pne_sch` (L7594) 의 `step_info['end_condition']` 에 `ref_step_number` 추가 | 30분 |
| 2 | 분류기 v3: HYSTERESIS / RSS_DCIR / SOC_DCIR / PULSE_DCIR ref_step 기반 룰 일반화 | 2시간 |
| 3 | 187 분류 결과 diff (v2 vs v3) — 정확도 향상 측정 | 1시간 |
| 4 | non-default ref_kind / jump_target sample 발굴 (다른 부서 / 협력업체 schedule) | TBD |
| 5 | PNE vendor spec 확보 시도 — 분류기 v3 후속 | TBD |

---

## 6. 재현 방법

```bash
cd C:\Users\Ryu\battery\python\BDT_dev\.claude\worktrees\adoring-hopper-e1c07f

# 1. DCIR sample 의 step 구조 dump (개별 sample 검증)
python tools/sch_phase0_5_alpha_dump.py

# 2. DCIR sample 에서 binary search (ref_step_number = +501 식별)
python tools/sch_phase0_5_alpha_binary_search.py

# 3. 368 .sch 전수 cross-validate (1,169 step 검증)
python tools/sch_phase0_5_alpha_validate.py

# 4. ref_kind / ref_basis / jump_target enum search
python tools/sch_phase0_5_alpha_other_fields.py
```

---

## Related

- [[260504_audit_phase0_5_classifier_input_spec]] §3.3 — 미식별 5 field 후보 list
- [[260504_audit_phase0_4_dcir_pattern_review]] §2 — SOC/DOD ref-step jump mechanism 발견
- [[260504_audit_phase0_3_pne_ui_review]] H10 — Delta Vp 사용 sample 미발견 결론
- [[260505_phase0_5_187_cycle_definitions]] — 187 폴더 사이클별 정의 (본 발견 활용 후속)
