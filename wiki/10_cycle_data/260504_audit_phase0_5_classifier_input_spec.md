---
title: "Phase 0-5: 분류기 v2 input spec — Phase 0 audit 종합"
date: 2026-05-04
tags: [audit, classifier-spec, sch-parser, phase0-5, summary, classifier-v2]
related:
  - "[[260504_plan_22cat_audit_and_eval_overlay]]"
  - "[[260504_audit_phase0_2_187_validation]]"
  - "[[260504_audit_phase0_3_pne_ui_review]]"
  - "[[260504_audit_phase0_4_dcir_pattern_review]]"
status: phase-0-audit-final
---

# Phase 0-5: 분류기 v2 input spec — Phase 0 audit 종합

> Phase 0-1 ~ 0-4 의 모든 finding 을 종합. **사용자 통찰 (260504): "결국 .sch 파일 분석을 통한 사이클 분류 — 분류 input = mincapacity / 인가 전류 / 전압 / EndCondition / sampling 주기"** 를 분류기 v2 spec 으로 정식화.
> 추가 4 PNE UI 캡처 (hysteresis / RSS / 일반수명 / 복합floating) review 포함.

---

## TL;DR

- ⭐ **사용자 핵심 통찰** — 분류기 input 5 base + CC vs CCCV 의 voltage 컬럼 의미 분리:
  - **CC mode**: `Charge(V)/Discharge(V)` 컬럼 = display only (또는 default), **실제 V cutoff = EndCondition** (`+28 end_voltage_mV`)
  - **CCCV mode**: `Charge(V)` 컬럼 = **CC target = CV target** (`+12 voltage_mV`), EndCondition = **I cutoff** (`+32 end_current_mA`) + 시간/SOC/DOD 등
- ⭐ Phase 0-1d 의 +12 해석 ("CHG VRef") 정정: type_code 별 의미 다름.
- 4 추가 sample 의 binary 매칭 확인:
  - RSS 수명 (Q8 Sub): n=215, `+336=60s`, `has_+36=True`
  - 일반 수명 (Gen5+B 2335 Si Hybrid): n=178, `+336=60s`
  - 복합 floating (Q8 SUB): n=57, `+336=60s`, `+656=50` (n_steps 와 가까움)
- ⭐⭐ **22 카테고리 분류 룰 v2** 정리 — Phase 0 audit 의 모든 신규 field 활용.
- Phase c (코드 fix) 의 implementation spec 확보.

---

## 1. 사용자 핵심 통찰 (260504)

> "결국 하고 싶은 건 .sch 파일 분석을 통한 사이클 분류이다.
> mincapacity, 인가 전류, 전압, EndCondition + sampling 주기이다.
> - CC 전류 인가의 cutoff 전압은 EndCondition을 따름
> - CCCV는 Charge(V), Discharge(V) 열 정보가 CC cutoff voltage + EndCondition에 전류 cutoff 외 조건들이 있음"

### CC mode (type_code `0x0201` CHG_CC, `0x0202` DCHG_CC)

| binary | UI field | 의미 |
|---|---|---|
| `+12` (CHG) / `+16` (DCHG) | `Charge(V)` / `Discharge(V)` 컬럼 | **Display only (또는 사용자 default)** — 실제 cutoff 가 아님 |
| `+20` | `Current(A)` | **인가 전류 (실제 적용)** |
| `+24` | EndCondition `t > HH:MM:SS` | **시간 cutoff** |
| **`+28`** | EndCondition `V < x` 또는 `V > x` | ⭐ **실제 V cutoff** |
| `+36/+40` | EndCondition `C > x` | Capacity cutoff |
| `+372/+500/+504` | EndCondition `Step N SOC/DOD X%` | ref-step jump |

### CCCV mode (type_code `0x0101` CHG_CCCV, `0x0102` DCHG_CCCV)

| binary | UI field | 의미 |
|---|---|---|
| **`+12`** | `Charge(V)` 컬럼 | ⭐ **CC target voltage = CV target voltage** (둘 다 같은 값) |
| `+20` | `Current(A)` | 인가 전류 (CC 단계) |
| `+24` | EndCondition `t > HH:MM:SS` | 시간 cutoff |
| `+28` | (CCCV 에서는 0) | 미사용 |
| **`+32`** | EndCondition `I < x` | ⭐ **실제 I cutoff (CV 단계)** |
| `+36/+40` | EndCondition `C > x` | Capacity cutoff |

### 검증 (4 캡처)

| Sample | step type / mode | UI Voltage 컬럼 | UI EndCondition | 의미 |
|---|---|---|---|---|
| Hysteresis (Si25P) | step 8 DisCharge CC | 2.500 | **V < 2.750** Move NEXT | 2.500 = default, 2.750 = 실제 cutoff |
| RSS (Q8 Sub) | step 30 Charge CC | 4.300 | **V > 4.140** or C > 3.042 | 4.300 = default, 4.140 = 실제 cutoff |
| 일반 수명 (Gen5+B) | step 12 Charge CC | 4.300 | **V > 4.140** Move NEXT | 동상 |
| 복합 floating | step 47 Charge CCCV | 4.550 | **t > 1D 0:00:00** Move NEXT | 4.550 = CC target = CV target ✓ |

→ ⭐ **Phase 0-1d 의 +12 해석 정정** 필요:
- 기존: "+12 = CHG VRef = CC target V or CV target V"
- 정정: "**+12 = CHG voltage (CC mode 에서는 display, CCCV mode 에서는 CV target)**"
- CC step 의 실제 V cutoff = `+28` (EndCondition)

---

## 2. 4 추가 PNE UI 캡처 review

### 2.1 Hysteresis (Si25P 6330mAh 0.2C-10min Voltage hysteresis test)

| 항목 | 값 |
|---|---|
| 시험 안전 | V 4.6/2.5, I 20/0, **셀 온도 60.0/0.0**, Cap 6.963, **저장 주기 137** |
| Step 패턴 | step 8 = full discharge → step 14/20/26/.../50 = **DOD 10/20/30/40/50/60/70 % 부분 방전** |
| Loop | 각 DOD level 1회 → 다음 cycle |
| End 조건 | DCHG step 의 "**Step 8 DOD X%(AH) Move NEXT**" — ref-step jump |

→ 22 카테고리의 **HYSTERESIS_DCHG** 패턴 정확히 일치. 분류 룰: `+500 = 2048 (DOD%)` + ref_step_number 비0 → HYSTERESIS_DCHG.

### 2.2 RSS 포함 수명 (Q8 Sub_2485mAh 2C Rss 2step 방전)

| 항목 | 값 |
|---|---|
| binary | n=215, `+656=14`, `+336=60s`, `has_+36=True` |
| Step 패턴 | step 14 (DCHG, **Step 8 DOD 30%**) → step 15 (DCHG 2.485A, **t > 0:00:01**) → step 16 (Rest 31min) |
| Multi-step charge | step 30-33: V > 4.140 → V > 4.160 → V > 4.300 (CCCV) → V > 4.550 (CCCV 2hr) — **4-step charge** |
| 2-step discharge | step 35 V<3.65 → step 36 V<3.0 — Hysteresis 종료 V 3.65V |
| Loop | 반복 97회 (step 38) |

→ ACCEL + Hysteresis hybrid + RSS pulse. 22 카테고리 **ACCEL** + **RSS_DCIR** mix.

### 2.3 일반 수명 (Gen5+B 2335mAh 2C Si Hybrid 상온)

| 항목 | 값 |
|---|---|
| binary | n=178, `+656=5`, `+336=60s` |
| Multi-step charge | step 12-15: 4.300 (V>4.140) → 4.300 (V>4.160) → 4.300 (CCCV I<2.320) → 4.550 (CCCV I<0.234 or t>2hr) |
| 2-step discharge | step 17 V<3.65 → step 18 V<3.0 (둘 다 t>5hr cap) |
| Loop | 반복 98회 (step 20) |

→ 22 카테고리 **ACCEL** 표준 패턴. multi-step charge 4 단계 + 2-step discharge.

### 2.4 복합 floating (Q8 SUB GEN5+B 2C 고온복합 Floating Max V)

| 항목 | 값 |
|---|---|
| binary | n=57, `+656=50`, `+336=60s` |
| 시험 안전 | V 4.6/2.5, **셀 온도 60.0/0.0** (HT) |
| Step 패턴 | step 18-19/21-22/24-25: SOC 30%/20%/20% incremental charge — **Step 12 SOC X%(AH) Move NEXT** |
| step 31-39 | Discharge Step 14 DOD 30%/20%/20% — DOD ref-step jump |
| step 47 | CCCV `t > 1D 0:00:00` — **1일 floating** |
| step 51 | 반복 6회 후 **Step 11로 이동** (20회 반복) — outer goto |

→ 22 카테고리 **FLOATING + ACCEL + Hysteresis** hybrid. Multi-pattern.

→ ⭐ **+656 = 50** (n_steps 57 와 가까움) — 저장 주기 의미 검증 후보. 본 sample 의 +656 ~ n_steps 패턴 일치.

---

## 3. 분류기 v2 input spec — 5 base + 신규 field

### 3.1 Base inputs (사용자 통찰)

| Input | binary 위치 | 의미 |
|---|---|---|
| **mincapacity** | `+104 capacity_limit_mAh` (또는 사용자 입력 경로 테이블 "용량") | 셀 nominal 용량 (mAh) |
| **인가 전류** | step `+20 current_mA` | C-rate 산출 (current / capacity) |
| **전압 (CC)** | step `+28 end_voltage_mV` | 실제 V cutoff |
| **전압 (CCCV)** | step `+12 voltage_mV` | CC target = CV target |
| **EndCondition** | step `+24/+28/+32/+36/+40/+372/+500/+504` + ref-step jump | 종료 조건 multi-OR |
| **Sampling 주기** | step `+336 record_interval_s` | 1/60/0.1/300 등 |

### 3.2 Phase 0 신규 발견 inputs (Phase 0-2/0-3/0-4)

| Input | binary | 활용 |
|---|---|---|
| `chamber_temp_c` | `+396` | 23/45/-10/15/-5 cluster — 시험 환경 group |
| `v_safety_upper_mV` | `+88` | 시험 V upper |
| `v_safety_lower_mV` | `+92` | 시험 V lower (DCHG 에서는 step-specific 가능) |
| `i_safety_upper/lower_mA` | `+96/+100` | I buffer |
| `chg/dchg_end_capacity_cutoff_mAh` | `+36/+40` | C cutoff |
| `mode_flag` | `+84` | multi-purpose (1/0/257) |
| `record_interval_secondary` | `+388` | 보조 sampling rate |

### 3.3 신규 미식별 inputs (Phase 0-3/0-4 후보)

| Input | UI field | 우선순위 |
|---|---|---|
| ⭐⭐⭐ **`ref_step_number`** | "Step N" jump | DCIR/Hysteresis 분류 핵심 |
| ⭐⭐⭐ **`ref_step_kind`** | "Char./Dis." | 동상 |
| ⭐⭐ **`ref_capacity_basis`** | "AH or V" | 동상 |
| (✓) `pct_threshold` | SOC/DOD % | `+372` 이미 식별 |
| ⭐⭐ **`jump_target_step`** | "NEXT or Step N" | multi-step charge 분류 |
| ⭐⭐ **`end_delta_vp_V`** | Delta Vp (Pick V Drop) | DCIR pulse 측정 식별 |
| ⭐ `end_power_W`, `end_watt_hour_Wh` | Power, WattHour | 추가 EC type |
| ⭐ multi-condition OR array | end condition slots | 4-5 condition 동시 |

---

## 4. 22 카테고리 분류 룰 v2

### 4.1 단순 type-based (현재 룰 유지 + 보강)

| 카테고리 | 룰 | 보강 (Phase 0 발견) |
|---|---|---|
| **INIT** | position=0, N=1, all DCHG (+REST) | (현재 유지) |
| **TERMINATION** | position=last, N=1, DCHG only | (현재 유지) |
| **REST_LONG** | REST only, t≥3600 | `+336` 활용 가능 |
| **REST_SHORT** | REST only, t<3600 | (유지) |
| **POWER_CHG** | type_code `CHG_CP` | (유지) |

### 4.2 Multi-step charge 기반 (사용자 통찰: CC vs CCCV)

| 카테고리 | 룰 v2 |
|---|---|
| **ACCEL** | N≥20 + `len(chg_steps) ≥ 2` (multi-step CC charge) + DCHG. **각 CC step 의 `+28` 가 4.140/4.160/... 처럼 점진적 증가** + 마지막 CCCV step (`+32` I cutoff) + 2-step DCHG (`+28 = 3650 → 3000`) |
| **FORMATION** | 2≤N≤10 + CHG + DCHG (`+12` ≈ 0.1C, 모든 전류 ≈ 0.1C * capacity) |
| **CHG_DCHG** | N=1 + CHG + DCHG (위 룰 안 걸림) |

### 4.3 RPT (사용자 통찰: 0.2C base)

| 카테고리 | 룰 v2 |
|---|---|
| **RPT** | N=1 + CHG + DCHG + 모든 `+20 ≈ capacity * 0.2` (±30%) |

→ **mincapacity** 와 step 의 `+20` 비교 핵심.

### 4.4 Hysteresis (Phase 0-4 발견: ref-step jump)

| 카테고리 | 룰 v2 |
|---|---|
| **HYSTERESIS_DCHG** | N=1 + DCHG + `+500 = 2048` (DOD%) + ⭐ ref_step_number 비0 (예: "Step 8 DOD X%") + no short pulse (DCHG `+24 > 30`) |
| **HYSTERESIS_CHG** | N=1 + CHG + `+500 = 18432` (SOC%) + ref_step_number 비0 + no short CHG pulse |

### 4.5 DCIR family (Phase 0-4 발견)

| 카테고리 | 룰 v2 |
|---|---|
| **SOC_DCIR** | EC≥4 + body≥8 + N=5~19 + EC type 다양성 ≥3 + ⭐ **ref-step jump (+500 ∈ {2048, 18432}, 다수 step)** |
| **PULSE_DCIR** | EC + 짧은 DCHG (`+24 ≤ 30`) + DCHG≥2 + body≥5 + ⭐ **`+336 ≤ 1s` (펄스 sampling)** |
| **RSS_DCIR** | N=1 + EC + DCHG≥4 + body≥10 + ref-step jump (DOD%) |

### 4.6 GITT (Phase 0-2 발견: +336 = 1s)

| 카테고리 | 룰 v2 |
|---|---|
| **GITT_PULSE** | (type_code `GITT_*` 사용) OR (REST `+24 ≥ 600` + 짧은 CHG/DCHG, N≥10) + ⭐ **`+336 = 1s`** + `+396` 비0 (chamber 온도 기록) |
| **SWEEP_PULSE** | N≥10, body≤3 (GITT 안 걸린 경우) + `+336 ≠ 1s` |

### 4.7 Floating (Phase 0-1a fix 후)

| 카테고리 | 룰 v2 |
|---|---|
| **FLOATING** | CHG + no DCHG + `+24 ≥ 43200` (12hr+) + ⭐ ((`+12 > 0` (CCCV)) OR (`+28 > 0` (CC)))   ← phase 0-1a 의 v_chg fix |

→ ⚠️ Phase 0-1a 의 fix 핵심: `s.get('voltage_mV', 0) > 0` 으로 변경 (현재 코드는 `v_chg_mV` 또는 `v_chg` 검색 → parser output 에 없음 → False).

### 4.8 SET (단순 single step)

| 카테고리 | 룰 v2 |
|---|---|
| **CHARGE_SET** | N=1, CHG only (no DCHG), CCCV 단일 |
| **DISCHARGE_SET** | N=1, DCHG_CCCV only, body≤2 |
| **DCHG_SET** | N=1, DCHG only (no CHG) — TERMINATION 외 |

### 4.9 카테고리 신규 후보 (Phase 0-1b 발견)

| 카테고리 | 식별 |
|---|---|
| **ECT** | `+664 schedule_description.contains("ECT")` + `+336 = 1s` + `+396 ∈ {23, 45, -10, 15, -5}` cluster |

→ ECT 시험은 step pattern 으로는 GITT_PULSE 또는 ACCEL 변형. **schedule_desc keyword + 환경 메타** 로 식별 가능. 신규 카테고리 추가 vs `ACCEL/GITT_PULSE` sub-tag 둘 중 결정 필요.

---

## 5. Schedule keyword 분류 layer (Phase 0-1b 의 +664)

`+664 schedule_description` 의 keyword 추출 → 22 카테고리 prior:

```python
def _classify_by_keyword(desc: str) -> str | None:
    d = desc.lower()
    if 'hysteresis' in d:
        return 'HYSTERESIS_DCHG'  # 또는 step pattern 으로 CHG 구분
    if 'floating' in d:
        return 'FLOATING'
    if 'gitt' in d:
        return 'GITT_PULSE'
    if 'ect' in d:
        return 'ECT'  # 또는 GITT_PULSE
    if 'soc별dcir' in d.replace(' ', '') or 'dcir' in d:
        return 'SOC_DCIR'
    if 'rss' in d:
        return 'RSS_DCIR'  # RSS 포함 수명 의 경우 ACCEL + RSS_DCIR mix
    if 'rpt' in d:
        return 'RPT'
    if 'si hybrid' in d or 'seu' in d or 'accel' in d:
        return 'ACCEL'
    if 'formation' in d or '화성' in d:
        return 'FORMATION'
    return None
```

→ **2-layer 분류**: keyword prior → step pattern 검증 (mismatch 시 step pattern 우선).

---

## 6. Phase c 의 implementation spec

### 6.1 Parser `_parse_pne_sch` 보강 — 9 confirmed + 5 미식별

```python
# step block 신규 추가 (Phase 0-2 confirmed)
'v_safety_upper_mV': struct.unpack_from('<f', blk, 88)[0],
'v_safety_lower_mV': struct.unpack_from('<f', blk, 92)[0],
'i_safety_upper_mA': struct.unpack_from('<f', blk, 96)[0],
'i_safety_lower_mA': struct.unpack_from('<f', blk, 100)[0],
'chg_end_capacity_cutoff_mAh': struct.unpack_from('<f', blk, 36)[0],
'dchg_end_capacity_cutoff_mAh': struct.unpack_from('<f', blk, 40)[0],
'record_interval_s': struct.unpack_from('<f', blk, 336)[0],
'chamber_temp_c': struct.unpack_from('<f', blk, 396)[0],
'mode_flag': struct.unpack_from('<I', blk, 84)[0],

# header 신규 (Phase 0-2 confirmed)
'format_version': struct.unpack_from('<I', data, 4)[0],   # 131077
'header_record_count': struct.unpack_from('<I', data, 8)[0],   # 50
'block_count_meta': struct.unpack_from('<I', data, 656)[0],
'schedule_description': decode_ascii(data[664:664+64]),
'user_category': decode_cp949(data[336:336+32]),
'created_at': decode_cp949(data[587:587+24]),
'modified_at': decode_cp949(data[910:910+24]),

# Phase 0-3/0-4 미식별 후보 (binary 위치 추가 검증 필요)
# 'ref_step_number', 'ref_step_kind', 'ref_capacity_basis',
# 'jump_target_step', 'end_delta_vp_V', 'end_power_W', 'end_watt_hour_Wh'
```

### 6.2 분류기 `_classify_loop_group` 보강

1. ⚠️ **`v_chg` 키 mismatch fix** (Phase 0-1a 발견, 1줄):
   ```python
   # L8053 변경
   has_v_cut = any(s.get('voltage_mV', 0) > 0 for s in chg_steps)  # 'v_chg_mV' / 'v_chg' → 'voltage_mV'
   ```

2. **`+336 < 5` hint** 추가 (Phase 0-2):
   ```python
   short_sampling = any(s.get('record_interval_s', 60) < 5 for s in body)
   ```

3. **CC vs CCCV V cutoff 분리** (사용자 통찰):
   ```python
   def _step_v_cutoff(s):
       """Get actual V cutoff (mV) — CC vs CCCV 별 의미 다름."""
       if s['type'] in ('CHG_CCCV', 'DCHG_CCCV'):
           return s.get('voltage_mV', 0)  # CV target
       elif s['type'] in ('CHG_CC', 'DCHG_CC'):
           return s.get('end_voltage_mV', 0)  # EndCondition
       return 0
   ```

4. **Schedule keyword classifier** (Phase 0-1b):
   ```python
   def _classify_by_schedule_desc(desc: str) -> str | None: ...
   ```

5. **ref-step jump 활용** (Phase 0-3/0-4):
   ```python
   # Phase 0-5 binary search 후 식별
   ref_step = step.get('ref_step_number', 0)
   if ref_step > 0:
       # SOC/DOD ref-step 사용 시험 — DCIR/Hysteresis 강한 hint
       ...
   ```

### 6.3 분류기 v2 output 추가

기존 22 카테고리 외에 **sub-tag** 추가 가능:
- `ACCEL` + sub-tag `Si_Hybrid` / `RSS` / `2step_discharge`
- `HYSTERESIS_DCHG` + sub-tag `Si25P_0.2C` / `0.5C_60min`
- `FLOATING` + sub-tag `120D` / `MaxV` / `4C_HT`
- `ECT` + sub-tag `parameter1` / `GITT`

→ Phase b (22 카테고리 spec audit) 와 함께 결정.

---

## 7. Phase 0 audit 종합 요약

### Phase 0 sub-step 별 산출

| Phase | 산출 | 핵심 |
|---|---|---|
| 0-1a | [[260504_audit_phase0_sch_parsing_gap]] | parser 코드 review + ⚠️ `v_chg` bug |
| 0-1b | [[260504_audit_phase0_extractable_fields]] | 4 sample header dump + 식별 가능 field list |
| 0-1c | [`tools/sch_csv_crosscheck.md`](../../tools/sch_csv_crosscheck.md) | 10 CSV ↔ 9 sch capacity 100% 일치 |
| 0-1d | [[260504_audit_phase0_csv_sch_step_alignment]] | 3 sample step alignment + 5 신규 field |
| 0-2 | [[260504_audit_phase0_2_187_validation]] | 187 전수 28,779 step 가설 검증 |
| 0-3 | [[260504_audit_phase0_3_pne_ui_review]] | PNE UI ECT GITT review + 15+ 신규 field |
| 0-4 | [[260504_audit_phase0_4_dcir_pattern_review]] | DCIR UI review + ⭐⭐⭐ SOC/DOD ref-step jump |
| **0-5** | **본 노트** | **분류기 v2 input spec 정식화** |

### Phase 0 의 가장 큰 가치

1. ⭐⭐⭐ **사용자 통찰** — CC vs CCCV 의 voltage 컬럼 의미 분리. 분류 룰의 base.
2. ⭐⭐⭐ **SOC/DOD ref-step jump mechanism** — DCIR/Hysteresis 분류의 핵심.
3. ⭐⭐⭐ **`+336` × keyword 의 강한 상관** — GITT/ECT=1s, hysteresis=60s, DCIR=0.1s.
4. ⭐⭐ **9 신규 field confirmed** + **5 신규 field 후보** + **header schema 명시**.
5. ⚠️ **`v_chg` 키 mismatch bug** — 1줄 fix 로 FLOATING 분류 활성화.

---

## 8. 다음 단계 — Phase c 권장 순서

| 순서 | 작업 | 예상 cost |
|---|---|---|
| 1 | `v_chg` 키 fix (1줄) + 187 분류 변화 측정 | 즉시 |
| 2 | parser 9 confirmed field 추가 | 1시간 |
| 3 | CC vs CCCV V cutoff 분리 함수 추가 | 30분 |
| 4 | schedule keyword classifier 추가 | 1시간 |
| 5 | `+336 < 5` hint + GITT/PULSE 분류 보강 | 30분 |
| 6 | Phase 0-3/0-4 미식별 5 field binary search (Phase 0-5-α) | 2-3시간 |
| 7 | ref-step jump 활용 분류 룰 (DCIR/Hysteresis 보강) | 2시간 |
| 8 | 187 분류 정확도 metric (Phase d) | 1시간 |
| 9 | 22 카테고리 spec audit (Phase b) — 평가자 review | TBD |

본 grilling session 의 audit phase 종료. **Phase c 는 별도 session** 에서 본 spec 따라 진행 권장.

---

## Related

- [[260504_plan_22cat_audit_and_eval_overlay]] — 5단계 plan
- [[260504_audit_phase0_sch_parsing_gap]] — Phase 0-1a
- [[260504_audit_phase0_extractable_fields]] — Phase 0-1b
- [[260504_audit_phase0_csv_sch_step_alignment]] — Phase 0-1d
- [[260504_audit_phase0_2_187_validation]] — Phase 0-2
- [[260504_audit_phase0_3_pne_ui_review]] — Phase 0-3
- [[260504_audit_phase0_4_dcir_pattern_review]] — Phase 0-4
- [[hub_logical_cycle]] — 논리 사이클 hub
