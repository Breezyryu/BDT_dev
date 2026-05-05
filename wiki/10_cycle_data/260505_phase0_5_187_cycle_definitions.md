---
title: "Phase 0-5 분류기 v2 — 187 폴더 / 368 .sch 사이클별 정의 전수"
date: 2026-05-05
tags: [phase0-5, classifier-v2, 187-folders, cycle-definitions, sch-parsing]
related:
  - "[[260504_audit_phase0_5_classifier_input_spec]]"
  - "[[260504_plan_22cat_audit_and_eval_overlay]]"
  - "[[260504_audit_phase0_2_187_validation]]"
  - "[[260419_사이클분류_전면재검토]]"
  - "[[hub_logical_cycle]]"
status: phase-0-5-applied
---

# Phase 0-5 분류기 v2 — 187 폴더 / 368 .sch 사이클별 정의 전수

> [[260504_audit_phase0_5_classifier_input_spec]] 의 분류기 v2 spec 을 `raw/raw_exp/exp_data/` 187 폴더 / 368 `.sch` 전수에 적용. **8,298 loop group (사이클 그룹) 단위로 카테고리·TC 범위·V cutoff·C-rate·EC types·sampling 주기·chamber 온도** 모두 정의.

---

## TL;DR

- ✅ **368 .sch** 전수 파싱 (실패 0건). **8,298 사이클 그룹** 분류.
- ✅ 187 폴더 = `.sch` 보유 173 + 미보유 14 (= Toyo `.ptn` 시험: 수명 12 + 성능 1 + 복합floating 1).
- ✅ Phase 0-5 spec 의 5 핵심 변경 모두 적용:
  1. ⚠️ `v_chg` 키 mismatch fix → **FLOATING 30 group 활성화**
  2. CC vs CCCV V cutoff 분리 (사용자 통찰)
  3. 9 신규 parser field 추가
  4. Schedule keyword classifier (header `+664`)
  5. `+336 < 5` short_sampling hint
- ⭐ **카테고리 분포**: RPT 34.2 % > CHG_DCHG 11.7 % > ACCEL 11.2 % > PULSE_DCIR 10.3 %.
- ⚠️ **UNKNOWN 1.7 %** (142 group, body-signature dedup 시 14 종) — 모두 `복합floating` 의 `N=14` mid-range 패턴 (Phase 0-5-α 후속 검증 필요).
- 산출:
  - [`tools/sch_phase0_5_groups.csv`](../../tools/sch_phase0_5_groups.csv) — 사이클(loop group) 단위 정의 한 row (8,298 row × 24 col)
  - [`tools/sch_phase0_5_files.csv`](../../tools/sch_phase0_5_files.csv) — 파일 단위 메타 (368 row × 13 col)
  - [`tools/sch_phase0_5_summary.md`](../../tools/sch_phase0_5_summary.md) — 자동 생성 요약 (cross-table + UNKNOWN list + 폴더별 분포)
  - [`tools/sch_phase0_5_classify_all.py`](../../tools/sch_phase0_5_classify_all.py) — 본 분석 재현 스크립트

---

## 1. 입력·산출 개요

### 1.1 입력

| 항목 | 값 |
|---|---|
| Root | `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data` |
| 시험종류 | 5 (성능 / 성능_hysteresis / 성능_시험직후 / 수명 / 수명_복합floating) |
| 실험 폴더 | **187** (`.sch` 보유 173 + 미보유 14) |
| `.sch` 파일 | **368** (parsed 368, failed 0) |

미보유 14 폴더 breakdown:
- 수명: 12 폴더 (Toyo `.ptn` 시험으로 추정)
- 성능: 1 폴더
- 복합floating: 1 폴더

### 1.2 산출

| 산출 | 행 | 비고 |
|---|---|---|
| `groups.csv` | 8,298 | 사이클(loop group) 단위 한 row — 24 컬럼: TC 범위, 카테고리, sub_tag, V cutoff, C-rate, EC types, sampling, chamber, … |
| `files.csv` | 368 | 파일 단위 — schedule_description, n_steps, n_groups, total_tc, 카테고리 summary |
| `summary.md` | — | 시험종류 × 카테고리 cross-table, UNKNOWN list, 폴더별 분포 |

---

## 2. Phase 0-5 spec 적용 사항

### 2.1 Parser 보강 (9 신규 field)

```python
# Step block (Phase 0-2 confirmed)
'v_safety_upper_mV':           +88   # CHG/DCHG/REST 모두 적용
'v_safety_lower_mV':           +92   # type 별 의미 다름 (Phase 0-2 H2 partial)
'i_safety_upper_mA':           +96
'i_safety_lower_mA':          +100
'chg_end_capacity_cutoff_mAh': +36   # 127 file
'dchg_end_capacity_cutoff_mAh':+40   #  43 file
'record_interval_s':          +336   # ECT/GITT=1s, hyst=60s, DCIR=0.1s
'chamber_temp_c':             +396   # 124 file (23/45/-10/15/-5)
'mode_flag':                   +84   # multi-purpose

# Header (Phase 0-2 confirmed schema)
'format_version':                +4   # always 131077
'header_record_count':           +8   # always 50
'block_count_meta':            +656
'schedule_description':        +664   # ASCII 64 byte
```

### 2.2 분류기 v2 룰 변경

| 변경 | 영향 |
|---|---|
| ⚠️ **`v_chg` 키 mismatch fix** — `s.get('v_chg_mV', s.get('v_chg', 0))` → `s.get('voltage_mV', 0)` | **FLOATING 30 group** 활성화 (이전엔 has_v_cut=False 로 차단) |
| **CC vs CCCV V cutoff 분리**: CC = `+28 end_voltage_mV`, CCCV = `+12 voltage_mV` | `chg_v_cutoff_mV` / `dchg_v_cutoff_mV` 컬럼 의미 정확화 |
| **schedule keyword prior** (`+664` description) | hysteresis/gitt/ect/floating/rss/dcir/rpt/formation 8 keyword 인식 (현재는 sub_tag 만 영향, 카테고리 결정은 step pattern 우선) |
| **`+336 < 5` short_sampling hint** | GITT_PULSE / PULSE_DCIR 의 sub_tag 로 표시 |

### 2.3 ⚠️ 본 분석은 batch script 만 적용 — proto 코드 fix 권장

본 분석은 `tools/sch_phase0_5_classify_all.py` 의 **자체 구현 v2 분류기** 로 실행. `DataTool_optRCD_proto_.py` 의 `_classify_loop_group` (L7975) **자체에는 아직 fix 미반영**. Phase c (코드 fix) 단계에서 proto 본체에 PR 필요.

---

## 3. 시험종류 × 카테고리 cross-table

| 시험종류 | 폴더(.sch/전체) | 파일 | TC총수 | RPT | CHG_DCHG | ACCEL | PULSE_DCIR | CHARGE_SET | FORMATION | REST_LONG | HYSTERESIS_DCHG | HYSTERESIS_CHG | DCHG_SET | INIT | UNKNOWN | TERMINATION | POWER_CHG | DISCHARGE_SET | GITT_PULSE | REST_SHORT | FLOATING | SOC_DCIR | RSS_DCIR |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 성능 | 102/103 | 197 | 12,469 | 1180 | 862 | 80 | 176 | 198 | 48 | 321 | 27 | 27 | 173 | 50 | 0 | 119 | 108 | 84 | 71 | 32 | 6 | 20 | 0 |
| 성능_hysteresis | 16/16 | 20 | 450 | 64 | 24 | 0 | 0 | 0 | 0 | 0 | **171** | **171** | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 성능_시험직후 | 10/10 | 10 | 41 | 16 | 10 | 0 | 0 | 0 | 0 | 9 | 0 | 0 | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 수명 | 24/36 | 85 | **80,631** | 1076 | 0 | **849** | 230 | 45 | 0 | 0 | 32 | 0 | 0 | 81 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 8 |
| 수명_복합floating | 21/22 | 56 | 21,462 | 506 | 74 | 0 | 450 | 318 | 334 | 0 | 0 | 0 | 16 | 40 | **142** | 0 | 0 | 0 | 0 | 0 | **24** | 0 | 0 |

→ **시험종류별 dominant 카테고리**:
- 성능: RPT(1180) + CHG_DCHG(862) — RPT/일반 충방전 중심
- 성능_hysteresis: HYSTERESIS_DCHG(171) + HYSTERESIS_CHG(171) — **완벽히 페어링** ✓
- 성능_시험직후: RPT(16) + CHG_DCHG(10) — 시험직후 RPT
- 수명: ACCEL(849) + RPT(1076) — 가속수명 + 중간 RPT
- 수명_복합floating: ACCEL(450) + FORMATION(334) + PULSE_DCIR(318) + RPT(506) + FLOATING(24) — multi-pattern hybrid

---

## 4. 카테고리 전역 분포

| Category | count | 비율 | 의미 |
|---|---|---|---|
| **RPT** | 2,842 | **34.2 %** | N=1, CHG+DCHG, 모든 전류 ≈ 0.2C ±30% |
| CHG_DCHG | 970 | 11.7 % | N=1, CHG+DCHG (RPT 룰 안 걸림) |
| **ACCEL** | 929 | 11.2 % | N≥20, multi-step CHG + DCHG (가속수명) |
| **PULSE_DCIR** | 856 | 10.3 % | EC + 짧은 DCHG (≤30s) + DCHG≥2 + body≥5 |
| CHARGE_SET | 561 | 6.8 % | N=1, CHG only (no DCHG) — SOC 세팅 |
| FORMATION | 382 | 4.6 % | 2≤N≤10, CHG+DCHG (화성 사이클) |
| REST_LONG | 330 | 4.0 % | REST only, t≥3600s |
| HYSTERESIS_DCHG | 230 | 2.8 % | N=1, DCHG, EC=2048 (DOD%) |
| HYSTERESIS_CHG | 198 | 2.4 % | N=1, CHG, EC=18432 (SOC%) |
| DCHG_SET | 192 | 2.3 % | N=1, DCHG only |
| INIT | 191 | 2.3 % | position=0, N=1, DCHG (+REST) — 초기 방전 |
| **UNKNOWN** | 142 | **1.7 %** | (Phase 0-5-α 후속 — §6 참조) |
| TERMINATION | 122 | 1.5 % | position=last, N=1, DCHG only |
| POWER_CHG | 108 | 1.3 % | CHG_CP 포함 |
| DISCHARGE_SET | 84 | 1.0 % | DCHG_CCCV only, body≤2 |
| GITT_PULSE | 71 | 0.9 % | GITT 블록 또는 REST(≥600s)+CHG/DCHG 1~2 step, N≥10 |
| REST_SHORT | 32 | 0.4 % | REST only, t<3600s |
| **FLOATING** | 30 | 0.4 % | CHG only + ≥12hr + V_cut (⭐ v_chg fix 후 활성화) |
| SOC_DCIR | 20 | 0.2 % | EC≥4 + body≥8 + N=5~19 + EC type≥3종 |
| RSS_DCIR | 8 | 0.1 % | N=1, EC, DCHG≥4, body≥10 |

총 **8,298 group** = 173 .sch-보유 폴더 × 평균 47.97 group/folder.

---

## 5. 카테고리별 대표 사이클 정의 sample

각 카테고리에서 대표 1-2건의 사이클 정의 (TC 범위, body 구성, V cutoff, C-rate, EC types, sampling).

### INIT (초기 방전)

| 폴더 | sch | TC | N | body | chg/dchg/rest | C-rate | rec_iv |
|---|---|---|---|---|---|---|---|
| 240821 ATL-Mini-422mAh-GITT-15도 | … | 1-1 | 1 | 1 | 0/1/0 | dchg=1.0 | 60s |
| 240919 SOC별DCIR-15도 | … | 1-1 | 1 | 1 | 0/1/0 | dchg=1.0 | 1s |

### FORMATION (화성)

| 폴더 | TC | N | body | chg/dchg/rest | V_chg / V_dchg | C-rate | rec_iv |
|---|---|---|---|---|---|---|---|
| 240821 GITT-15도 | 2-4 | 3 | 4 | 1/1/2 | 4500 / 3000 | 0.8/0.5 | 60s |
| 240919 SOC별DCIR-15도 | 2-4 | 3 | 4 | 1/1/2 | 4500 / 3000 | 0.8/0.5 | 60s |

### RPT (Reference Performance Test, N=1, 0.2C base)

| 폴더 | TC | N | body | chg/dchg/rest | V_chg / V_dchg | C-rate | rec_iv |
|---|---|---|---|---|---|---|---|
| 240919 SOC별DCIR | 5-5 | 1 | 4 | 1/1/2 | 4500 / 2000 | 0.2/0.2 | 60s |
| 250314 Floating+9D | 2-2 | 1 | 4 | 1/1/2 | 4530 / 3000 | 0.2/0.2 | 60s |

### ACCEL (가속수명, N≥20 multi-step)

| 폴더 | TC | N | body | chg/dchg/rest | V_chg cuts | C-rate | EC types |
|---|---|---|---|---|---|---|---|
| 240919 SOC별DCIR | 27-51 | 25 | 13 | 4/5/4 | 4500 | 0.5/0.2 | 3328;13056;13824;14592;15360 |
| 250513 SBR 0.7 DCIR | 6-25 | 20 | 13 | 5/4/4 | 4550 | 0.5/0.5 | 2816;4608;5376;6144;6912 |

### HYSTERESIS_DCHG (depth 기반 부분방전)

| 폴더 | TC | N | body | chg/dchg/rest | V_chg | C-rate | EC type |
|---|---|---|---|---|---|---|---|
| 260316 LWN 25P 0.5C-10min | 3-3 | 1 | 4 | 1/1/2 | 4550 | 0.5/0.5 | **2048 (DOD%)** |
| 260317 SDI Gen5+ MP1 0.2C-10min | 3-3 | 1 | 4 | 1/1/2 | 4530 | 0.2/0.2 | **2048 (DOD%)** |

### HYSTERESIS_CHG (SOC% 기반 부분충전)

| 폴더 | TC | N | body | chg/dchg/rest | V_dchg | C-rate | EC type |
|---|---|---|---|---|---|---|---|
| 260316 LWN 25P 0.5C-10min | 14-14 | 1 | 4 | 1/1/2 | 2750 | 0.5/0.5 | **18432 (SOC%)** |
| 260317 SDI Gen5+ MP1 | 14-14 | 1 | 4 | 1/1/2 | 2900 | 0.2/0.2 | **18432 (SOC%)** |

### GITT_PULSE (REST≥600s + 짧은 펄스, N≥10)

| 폴더 | TC | N | body | chg/dchg/rest | V_chg | C-rate | rec_iv |
|---|---|---|---|---|---|---|---|
| 240821 GITT-15도 | 5-109 | 105 | 2 | 1/0/1 | 4500 | chg=0.1 | 60s |
| 250827 ECT-parameter | 31-150 | 120 | 20 | 2/3/7 | 4470;4540 | 0.2/0.2 | **1s** ⭐ |

### PULSE_DCIR (짧은 DCHG 펄스 ≤30s)

| 폴더 | TC | N | body | chg/dchg/rest | V_chg | C-rate | EC type | rec_iv |
|---|---|---|---|---|---|---|---|---|
| 260211 POR 40C pulse PA1 ATL | 5-13 | 9 | 7 | 1/5/1 | 4500 | 0.2/0.2 | 3840 | **0.1s** ⭐ |
| 260211 POR 40C pulse PA1 SDI | 5-13 | 9 | 7 | 1/5/1 | 4500 | 0.2/0.2 | 3840 | **0.1s** ⭐ |

### SOC_DCIR (SOC별 DCIR)

| 폴더 | TC | N | body | chg/dchg/rest | V_chg | C-rate | EC types | rec_iv |
|---|---|---|---|---|---|---|---|---|
| 240919 SOC별DCIR | 7-11 | 5 | 13 | 4/5/4 | 4500 | 0.5/0.5 | 3328;5376;6144;6912;7680 | **0.1s** ⭐ |
| 250513 SBR 0.7 DCIR | 26-40 | 15 | 13 | 5/4/4 | 4550 | 0.5/0.5 | 2816;8448;9216;9984;10752 | **0.1s** ⭐ |

### RSS_DCIR (확산 포함 정상상태 저항)

| 폴더 | TC | N | body | chg/dchg/rest | V_chg / V_dchg | C-rate | EC types |
|---|---|---|---|---|---|---|---|
| A1_MP1_4500mAh_T23_1 (Gen4 ATL MP1) | 203-203 | 1 | 10 | 4/4/2 | 4500 / 3000 | 0.2/0.2 | 14592;15104 |

→ 단 8 group 만 RSS_DCIR 분류. Phase 0-4 의 "RSS 포함 수명" 패턴은 ACCEL+RSS_DCIR mix 로 분류되어 ACCEL 우선.

### FLOATING (장시간 충전 ≥12hr) — ⭐ v_chg fix 후 활성화

| 폴더 | TC | N | body | chg/dchg/rest | V_chg | C-rate | rec_iv |
|---|---|---|---|---|---|---|---|
| 250314 Gen5 SDI Pre-MP Si5% Floating+9D | 3-3 | 1 | 2 | 1/0/1 | 4530 | chg=0.8 | 60s |
| 260112 Gen5+B SDI MP2 2.0C EPF HT Floating | 1-1 | 1 | 2 | 1/0/1 | 4550 | chg=0.8 | 60s |

→ 30 group / 6 (성능) + 24 (복합floating). Phase 0-1a 의 `v_chg` mismatch fix 효과 확인.

### CHARGE_SET / DCHG_SET (단일 step 세팅)

| 카테고리 | 폴더 | TC | N | body | chg/dchg/rest | C-rate |
|---|---|---|---|---|---|---|
| CHARGE_SET | 240919 SOC별DCIR | 6-6 | 1 | 1 | 1/0/0 | chg=0.2 |
| DCHG_SET | 250827 ECT-parameter | 46-46 | 1 | 2 | 0/1/1 | dchg=0.2 |
| DISCHARGE_SET | 260211 POR 40C pulse PA1 | 3-3 | 1 | 1 | 0/1/0 | dchg=0.2 |

### REST_LONG / REST_SHORT (단순 휴지)

| 카테고리 | 폴더 | TC | rec_iv | 의미 |
|---|---|---|---|---|
| REST_LONG | 250827 ECT-parameter | 36-36 | 1s | t≥3600s |
| REST_SHORT | 251002 RatedCh half | 1-1 | 300s | t<3600s |

### TERMINATION (마지막 방전 종료)

| 폴더 | TC | N | body | chg/dchg/rest | C-rate |
|---|---|---|---|---|---|
| 260211 POR 40C pulse PA1 ATL | 266-266 | 1 | 5 | 0/4/1 | dchg=0.2 |
| 260211 POR 40C pulse PA1 SDI | 266-266 | 1 | 5 | 0/4/1 | dchg=0.2 |

### POWER_CHG (전력 충전 CHG_CP)

| 폴더 | TC | N | body | chg/dchg/rest | V_chg | rec_iv |
|---|---|---|---|---|---|---|
| 250827 ECT-parameter | 33-33 | 1 | 4 | 2/0/2 | 4470 | 1s |

→ 108 group / 모두 ECT-parameter 폴더 (PA2-SDI).

---

## 6. UNKNOWN 14종 — Phase 0-5-α 후속 검증 필요

`UNKNOWN 142 group` 모두 `수명_복합floating/` 의 동일 패턴이 outer-goto 로 확장된 것. body-signature 기준으로 dedup 시 **14 종** (= 14 .sch 파일):

| 폴더 (앞 40자) | N | body | chg/dchg/rest | 패턴 |
|---|---|---|---|---|
| 260320_안성진_251mAh_HaeanProtoDOE복합Floating (4 sch) | 14 | 7 | 4/1/2 | 다단CHG(4) → DCHG → REST × 2 |
| 260320_안성진_251mAh_HaeanProtoMain복합Floating (4 sch) | 14 | 7 | 4/1/2 | 동상 |
| 260413_김영환_3365mAh_Gen6+VB ATL Proto1 고온복합Floating 280day (2 sch) | 14 | 8 | 4/2/2 | 다단CHG(4) → DCHG×2 → REST×2 |
| 260413_박기진_4948mAh_Gen6+VB SDI Proto1 고온복합Floating 280day (4 sch) | 14 | 8 | 4/2/2 | 동상 |

→ 분류 룰의 **N=14 mid-range gap**:
- ACCEL 룰: `N≥20 + len(chg)≥2 + dchg` — `N=14<20` 으로 fall-through
- FORMATION 룰: `2≤N≤10 + chg + dchg` — `N=14>10` 으로 fall-through
- 결과: 어느 쪽도 안 걸려 UNKNOWN

→ **Phase 0-5-α 후속 권장 fix**:
1. ACCEL 임계값 완화: `N≥20` → `N≥10` + `multi-step (len(chg)≥3)` 조건 강화
2. 또는 신규 카테고리 `MID_LIFE_FLOATING` 추가 (복합floating 의 N=14 short-cycle 패턴)
3. schedule keyword `"복합floating"` prior 활용 → ACCEL 또는 FLOATING 강제 매핑

---

## 7. 폴더명 ↔ 카테고리 정합성 의심 list (sample)

폴더명에 키워드는 있는데 해당 카테고리가 0인 케이스 — `tools/sch_phase0_5_summary.md` §5 참조.

주요 패턴:
- "복합floating" 폴더 22 중 FLOATING 분류 없는 폴더 다수 → **§6 의 N=14 UNKNOWN 케이스** + ACCEL/PULSE_DCIR 으로 분류된 케이스
- "RSS" 키워드 폴더에서 RSS_DCIR 미발견 → ACCEL+RSS_DCIR mix 로 ACCEL 우선 (Phase 0-4 finding)

---

## 8. 폴더 × 카테고리 분포 (sample)

전체 173 폴더 × 카테고리 분포는 `tools/sch_phase0_5_summary.md` §4 참조. 대표 sample:

| 시험종류 | 폴더 | n_sch | TC총수 | 카테고리 분포 |
|---|---|---|---|---|
| 성능 | 240821 Gen4pGr ATL-Mini-422mAh-GITT-15도 | 2 | 428 | GITT_PULSE(4), INIT(2), FORMATION(2) |
| 성능 | 240919 Gen4pGr SOC별DCIR-15도 | 2 | 192 | SOC_DCIR(8), ACCEL(4), INIT(2), FORMATION(2), RPT(2), CHARGE_SET(2) |
| 성능 | 250314 Gen5 SDI Pre-MP Si5% Floating+9D | 4 | 12 | INIT(4), RPT(4), **FLOATING(4)** |
| 성능 | 250513 Gen5+B SDI MP1 DoE SBR 0.7 DCIR | 1 | 95 | SOC_DCIR(4), ACCEL(2), INIT(1), FORMATION(1), RPT(1) |
| 성능 | 250827 PA2-SDI 447V-275V-ECT-parameter (1~8) | 1 ea | 5~150 | RPT, CHG_DCHG, ACCEL, REST_LONG, POWER_CHG, GITT_PULSE 다양 |
| 성능_hysteresis | 260316 LWN 25P 0.5C-10min volt hysteresis | 1 | 25~30 | HYSTERESIS_DCHG + HYSTERESIS_CHG **페어** + RPT |
| 수명 | 250207 ATL Q7M Inner 2C 상온수명 1-100cyc | 5+ | ~1000 | RPT + ACCEL multi-step |
| 수명_복합floating | 260413 박기진 Gen6+VB SDI Proto1 280day | 4 | 462 | UNKNOWN(40), FORMATION(8), … |

---

## 9. 다음 단계

### 9.1 Phase a (187 분류 통계 baseline)

본 노트가 Phase a 의 **baseline metric** 역할:
- UNKNOWN 1.7 % (142/8298) — Phase 0-5 spec 적용 후 baseline
- FLOATING 30 group — `v_chg` fix 효과 측정 baseline

→ proto 코드 fix 후 재실행 시 본 결과와 diff 비교.

### 9.2 Phase c (코드 fix PR)

권장 우선순위:

| 순서 | 작업 | 예상 효과 | 대상 |
|---|---|---|---|
| 1 | `v_chg` 키 mismatch fix (1줄) | FLOATING 30+ 활성화 | proto L8053 |
| 2 | parser 9 신규 field 추가 | 분류기 보강 base | proto L7594-7768 |
| 3 | CC vs CCCV V cutoff 분리 함수 | 룰 정확도 | proto 신규 helper |
| 4 | schedule keyword classifier | ambiguous case prior | proto 신규 helper |
| 5 | `+336 < 5` short_sampling hint | GITT_PULSE/PULSE_DCIR sub-tag | proto L7975 (룰 보강) |
| 6 | **ACCEL N=14 mid-range gap fix** ⭐ | UNKNOWN 142 → 0 (target) | proto L8058 |

### 9.3 Phase 0-5-α (미식별 5 field binary search)

[[260504_audit_phase0_5_classifier_input_spec]] §3.3 의 5 후보:
- `ref_step_number`, `ref_step_kind`, `ref_capacity_basis` (DCIR/Hysteresis ref-step jump)
- `jump_target_step` (multi-step charge)
- `end_delta_vp_V` (DCIR pulse Vp Drop)

→ ⭐⭐⭐ **`ref_step_number = +501 (uint8)` 식별 완료** (368 .sch 전수 1,169 step 검증).
  세부: [[260505_phase0_5_alpha_ref_step_field_identified]]

→ 나머지 4 field (`ref_step_kind` / `ref_basis` / `jump_target_step` / `end_delta_vp_V`)
  는 본 데이터셋의 모든 ref-using step 이 default 케이스 (Char. + AH + NEXT, Vp 미사용)
  라 별도 byte 식별 보류. PNE vendor spec 확보 또는 non-default sample 신규 측정 필요.

→ ref_step_number 발견의 가치: Phase 0-5 spec 의 hysteresis 분류 룰 (`ec_type == 2048`,
  `== 18432`) 의 정체 = `(ref_step << 8)` 인코딩. 분류기 v3 에서
  HYSTERESIS / RSS_DCIR / SOC_DCIR / PULSE_DCIR disambiguate 룰 일반화 가능.

### 9.4 Phase b / d

- (b) 22 카테고리 spec audit — 도메인 명문화. 본 결과의 sub_tag 변형 (예: ACCEL_Si_Hybrid, HYSTERESIS_0.5C_60min) 기반 정식화 가능.
- (d) 정확도 측정 — confusion matrix, ground truth = (b) spec + 평가자 manual review.

---

## 10. 재현 방법

```bash
cd C:\Users\Ryu\battery\python\BDT_dev\.claude\worktrees\adoring-hopper-e1c07f
python tools/sch_phase0_5_classify_all.py
```

→ `tools/sch_phase0_5_groups.csv`, `sch_phase0_5_files.csv`, `sch_phase0_5_summary.md` 갱신.

스크립트는 self-contained — `_parse_pne_sch` / `_classify_loop_group` 의 v2 버전을 자체 구현하여 proto 코드 변경 없이 batch 실행.

---

## Related

- [[260504_audit_phase0_5_classifier_input_spec]] — 본 분석의 spec 출처
- [[260504_plan_22cat_audit_and_eval_overlay]] — 5단계 audit plan
- [[260504_audit_phase0_2_187_validation]] — 28,779 step 가설 검증 (Phase 0-2)
- [[260419_사이클분류_전면재검토]] — 분류기 전면 재검토
- [[hub_logical_cycle]] — 논리 사이클 hub
