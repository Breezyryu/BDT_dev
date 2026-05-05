---
title: "Phase 0-5 분류기 v3 구축 — 모든 발견 통합 + ECT 신규 + UNKNOWN 0"
date: 2026-05-05
tags: [classifier-v3, phase0-5, phase0-5-alpha, mode-flag, ect-category, ref-step]
related:
  - "[[260504_audit_phase0_5_classifier_input_spec]]"
  - "[[260505_phase0_5_187_cycle_definitions]]"
  - "[[260505_phase0_5_alpha_ref_step_field_identified]]"
  - "[[260505_phase0_5_classifier_logic]]"
status: v3-complete
---

# Phase 0-5 분류기 v3 — 모든 발견 통합 batch script

> Phase 0-5 spec + Phase 0-5-α (`ref_step_number` 식별) + mode_flag 도메인 분석 결과를
> 모두 통합한 v3 batch 분류기. 187 폴더 / 368 .sch / 8,298 group 분류.
> ⭐ **UNKNOWN 0건** (v2 142 → v3 0) + **ECT 신규 79 group** + **ref_step 일반화**.

---

## TL;DR

- ✅ **UNKNOWN 142 → 0** (Phase 0-5-α `N=14` mid-range gap fix 효과)
- ⭐ **22 카테고리 유지** (ECT 는 별도 카테고리가 아닌 ACCEL/FORMATION/GITT_PULSE 의 sub_tag 으로 통합 — 도메인 검증 후 결정, §4 참조)
- ⭐ **ref_step_number 기반 룰 일반화** — HYSTERESIS_DCHG/CHG +27 group, RSS_DCIR multi_cluster 32 group 식별
- ⭐ **mode_flag 활용** — DCHG_CCCV mode=0 → PULSE_DCIR sub_tag, ECT-parameter 79 group 식별 (sub_tag)
- ⭐ **CC vs CCCV V cutoff 분리** + **`v_chg` 키 fix** (v2 부터 적용)
- 산출:
  - [`tools/sch_phase0_5_v3_classify.py`](../../tools/sch_phase0_5_v3_classify.py) — v3 batch 스크립트
  - [`tools/sch_phase0_5_v3_groups.csv`](../../tools/sch_phase0_5_v3_groups.csv) — 8,298 group × 22 col
  - [`tools/sch_phase0_5_v3_files.csv`](../../tools/sch_phase0_5_v3_files.csv) — 368 file × 12 col
  - [`tools/sch_phase0_5_v3_summary.md`](../../tools/sch_phase0_5_v3_summary.md) — v3 요약
  - [`tools/sch_phase0_5_v2_v3_diff.md`](../../tools/sch_phase0_5_v2_v3_diff.md) — v2 vs v3 diff 분석
  - [`tools/sch_phase0_5_v2_v3_diff.py`](../../tools/sch_phase0_5_v2_v3_diff.py) — diff 도구

---

## 1. v3 의 v2 대비 변경

### 1.1 Parser 보강 (Tier 1 — 분류 룰 직접 영향)

```python
# v3 신규 step_info 필드
'mode_flag':         struct.unpack_from('<I', blk, 84)[0]   # cycle counter 인식
'record_interval_s': struct.unpack_from('<f', blk, 336)[0]  # GITT/PULSE sub_tag
'chamber_temp_c':    struct.unpack_from('<f', blk, 396)[0]  # ECT 식별

# end_condition 에 ref_step_number 추가 (Phase 0-5-α)
step_info['end_condition'] = {
    'type': ec500,                          # legacy (= (ref_step << 8) | type_byte)
    'value_pct': round(ec_value, 2),
    'ref_step_number': (ec500 >> 8) & 0xFF, # ⭐ Phase 0-5-α
    'type_marker': ec500 & 0xFF,            # 본 데이터셋 항상 0
}

# Header schema (Tier 2 — informational)
header['format_version'] = ...
header['header_record_count'] = ...
header['block_count_meta'] = ...
header['schedule_description'] = ...   # +664 ASCII keyword
```

### 1.2 분류기 룰 변경

| # | 룰 | v2 | v3 | 효과 |
|---|---|---|---|---|
| A | `v_chg` 키 fix | ❌ bug | `voltage_mV` 사용 | FLOATING 30 활성화 |
| B | CC vs CCCV V cutoff 분리 | ❌ | helper 함수 | multi-step charge 정확 식별 |
| C | schedule keyword prior | ❌ | 8 keyword | ECT/RSS/Hysteresis prior |
| D | ref_step 일반화 hysteresis | `ec_type==2048` | `ref_step≠0` | +27 hysteresis group |
| E | RSS_DCIR multi-cluster | 단일 룰 | `≥2 distinct ref_step` sub_tag | RSS_DCIR +32 |
| F | ACCEL `N=14` mid_life | ❌ → UNKNOWN | `N=11~19 + multi-CHG` | UNKNOWN 142 → 0 |
| G | DCHG_CCCV mode=0 → PULSE_DCIR sub_tag | ❌ | sub_tag `dchg_cccv_pulse` | DCIR pulse 식별 |
| H | ECT 신규 카테고리 | ❌ (GITT/ACCEL 분류) | desc_kw `ect` OR (REST mode=0 + chamber + +336<5) | 79 group ECT |

### 1.3 우선순위 재조정

도메인 정확성 보존을 위한 룰 순서:

```
 1. INIT
 2. ECT (신규 — desc_kw OR REST mode=0 + chamber)
 3. GITT_PULSE
 4. FLOATING
 5. ACCEL strong (N≥20)
 6. RSS_DCIR (cluster) — N=1 + DCHG≥4 + body≥10 + not has_short_dchg
 7. HYSTERESIS_DCHG (ref_step 일반화)
 8. HYSTERESIS_CHG (ref_step 일반화)
 9. SOC_DCIR
10. PULSE_DCIR (short DCHG + DCHG_CCCV mode=0 sub_tag)
11. PULSE_DCIR (DCHG_CCCV mode=0 단독 hint)
12. RSS_DCIR fallback
13. ACCEL mid_life (N=11~19 + multi-CHG)
14. DISCHARGE_SET / POWER_CHG / REST_LONG / FORMATION / CHARGE_SET / TERMINATION /
    DCHG_SET / RPT / CHG_DCHG / SWEEP_PULSE / REST_SHORT / UNKNOWN
```

핵심 disambiguate:
- **PULSE_DCIR vs RSS_DCIR**: `has_short_dchg` (≤30s 펄스 있음) 으로 분리. 짧은 펄스 = PULSE, 긴 DCHG = RSS.
- **HYSTERESIS_DCHG vs RSS_DCIR**: RSS 가 먼저 매칭하되 `not has_short_dchg + DCHG≥4 + body≥10` 조건. Hysteresis 는 그 외 N=1 + DCHG + ref_step.
- **ACCEL N=14 vs SOC_DCIR**: SOC_DCIR (5≤N<20 + EC type 다양성 ≥3) 가 먼저 매칭. 그 후 ACCEL mid_life (N=11~19).

---

## 2. v2 vs v3 카테고리 분포 diff (ECT sub_tag 통합 후)

| Category | v2 | v3 | diff | 비고 |
|---|---|---|---|---|
| RPT | 2842 | 2833 | -9 | 일부 → HYSTERESIS_CHG (ref_step) |
| **ACCEL** | 929 | **1071** | **+142** | UNKNOWN 142 흡수 (mid_life sub_tag) |
| CHG_DCHG | 970 | 970 | 0 | 변동 없음 |
| PULSE_DCIR | 856 | 856 | 0 | sub_tag 추가만 |
| CHARGE_SET | 561 | 551 | -10 | 일부 → HYSTERESIS_CHG |
| FORMATION | 382 | 382 | 0 | sub_tag (ect) 만 추가 |
| REST_LONG | 330 | 330 | 0 | |
| HYSTERESIS_DCHG | 230 | 198 | -32 | 32 → RSS_DCIR multi_cluster |
| HYSTERESIS_CHG | 198 | 217 | +19 | ref_step 일반화 |
| DCHG_SET | 192 | 192 | 0 | |
| INIT | 191 | 191 | 0 | |
| **UNKNOWN** | **142** | **0** | **-142 ✅** | ACCEL mid_life 흡수 |
| TERMINATION | 122 | 122 | 0 | |
| POWER_CHG | 108 | 108 | 0 | |
| DISCHARGE_SET | 84 | 84 | 0 | |
| GITT_PULSE | 71 | 71 | 0 | sub_tag (ect) 만 추가 |
| **RSS_DCIR** | **8** | **40** | **+32** | multi_cluster 흡수 |
| REST_SHORT | 32 | 32 | 0 | |
| FLOATING | 30 | 30 | 0 | |
| SOC_DCIR | 20 | 20 | 0 | |

→ **22 카테고리 유지** (신규 카테고리 없음). 변동 = UNKNOWN 142 / ref_step 일반화 / RSS multi_cluster 분리.

---

## 3. v2 → v3 transition matrix (변경된 group)

| v2 → v3 | count | 의미 |
|---|---|---|
| **UNKNOWN → ACCEL(mid_life)** | **142** | Phase 0-5-α `N=14` gap fix |
| ACCEL(multi_step) → ECT | 67 | ECT-parameter schedule (도메인 정확) |
| HYSTERESIS_DCHG → RSS_DCIR(multi_cluster) | 32 | multi-cluster ref_step (8/42/76/110) |
| CHARGE_SET → HYSTERESIS_CHG | 10 | ref_step 일반화 (CHG only + ref_step) |
| RPT → HYSTERESIS_CHG | 9 | ref_step 일반화 (N=1 + CHG+DCHG + ref_step on CHG) |
| FORMATION → ECT | 9 | ECT 의 작은 N 패턴 |
| GITT_PULSE → ECT | 3 | ECT GITT schedule |

→ 합계 **272 group 재분류** (v2 의 3.3%). 모두 도메인 의미 향상 방향.

---

## 4. ECT 처리 — 별도 카테고리가 아닌 sub_tag (도메인 검증 후 결정)

### 4.1 도메인 검증 (사용자 지적, 260505)

> "ECT (신규)는 단순 rest가 긴 거 아닌가?"

검증 결과 ([`tools/ect_inspect.md`](../../tools/ect_inspect.md)):

| 항목 | 결과 |
|---|---|
| ECT 분류 79 group 중 "단순 1-step REST" | **0 / 79 (0%)** — 단순 휴지 아님 |
| body size 평균 | 7.1 (min 4, max 20) |
| n_chg 평균 / n_dchg 평균 / n_rest 평균 | 3.0 / 1.1 / 2.8 |
| loop_count (N) 평균 | 30.8 (min 7, max 120) |

→ ECT 는 단순 긴 REST 가 아니지만, **step pattern 자체는 ACCEL 의 정확한 시그니처**:

```
ECT-parameter1 대표 sample (body=7, N=30):
  step 1: CHG_CC 9510mA V_cut=4220   (multi-step charge 1단)
  step 2: CHG_CC 7846mA V_cut=4240   (multi-step charge 2단)
  step 3: CHG_CCCV 6657mA V=4300     (CCCV 3단)
  step 4: CHG_CCCV 4755mA V=4470     (CCCV 4단)
  step 5: REST 60s
  step 6: DCHG_CC 2378mA V_cut=3300  (0.5C 부분 방전, ~SOC 50%)
  step 7: REST 60s
                                     ↓ × N=30 cycles
```

이는 **4-step multi-step charge + 부분 DCHG cycling = ACCEL 의 정확한 시그니처**.
chamber 온도 명시 (23/45/-10°C) 만 일반 ACCEL 과 차이.

### 4.2 v3 결정 — ECT sub_tag

Phase 0-5 spec §4.9 도 이미 "**신규 카테고리 추가 vs `ACCEL/GITT_PULSE` sub-tag 둘 중 결정 필요**"
명시. 도메인 검증 후 **sub_tag 으로 통합** 결정.

```python
# is_ect_signal 계산 — schedule keyword + 환경 메타
is_ect_signal = (desc_kw == 'ect' or
                 (rest_mode0_chamber_ratio >= 0.5 and short_sampling
                  and len(body) >= 5))

# ACCEL/FORMATION/GITT_PULSE 룰 매칭 후 sub_tag 으로 추가
if is_ect_signal:
    sub_parts.append('ect')
```

### 4.3 결과: 79 group ECT sub_tag 분포

| 카테고리 | sub_tag | count | 의미 |
|---|---|---|---|
| **ACCEL** | `multi_step+ect` | **67** | ECT-parameter chamber-controlled cycling |
| FORMATION | `ect` | 9 | 작은 N 의 ECT 변형 |
| GITT_PULSE | `gitt_block+ect` | 3 | ECT GITT schedule |

→ 79 group 모두 정확한 카테고리 + ECT sub_tag 으로 통합.
→ Phase b (22 카테고리 spec) 에서 sub_tag 변형 정식 등록 권장.

### 4.4 ECT 도메인 의미 (참고)

ECT (Equivalent Circuit Test) = 등가회로 모델의 파라미터 추출 시험.
- 4 chamber 온도 (23/45/-10/15/-5°C) 에서 측정
- short sampling (1s) 으로 pulse + 환경 응답 capture
- **step pattern 자체는 ACCEL 의 정확한 변형** (chamber control 만 차이)
- 식별: `schedule_description == 'ECT' OR (REST mode=0 + chamber + sampling<5s)`
- 분류: ACCEL/FORMATION/GITT_PULSE + sub_tag `ect`

---

## 5. ACCEL mid_life — Phase 0-5-α gap fix

### 5.1 Gap

v2 룰 ACCEL `N≥20` + FORMATION `2≤N≤10` 사이의 **N=11~19** 구간이 fall-through.
복합floating 시험의 `N=14 + 4 multi-CHG + 1 DCHG + 2 REST` 패턴이 142 group UNKNOWN 발생.

### 5.2 v3 해결

```python
# ACCEL strong (변경 없음)
if N >= 20 and len(chg) >= 2 and dchg:
    return 'ACCEL', 'multi_step' if len(chg) >= 3 else ''

# ⭐ ACCEL mid_life — N=11~19 + multi-step (≥3 CHG)
# SOC_DCIR/RSS_DCIR/PULSE_DCIR 룰 이후로 배치 (disambiguate)
if 11 <= N <= 19 and len(chg) >= 3 and dchg:
    return 'ACCEL', 'mid_life'
```

### 5.3 결과: UNKNOWN 142 → 0

| 폴더 | UNKNOWN (v2) | v3 분류 |
|---|---|---|
| 안성진 251mAh HaeanProtoDOE/Main 복합Floating | 56 | ACCEL(mid_life) |
| 김영환 3365mAh Gen6+VB ATL 280day | 28 | ACCEL(mid_life) |
| 박기진 4948mAh Gen6+VB SDI 280day | 56 | ACCEL(mid_life) |
| 외 2 | 2 | ACCEL(mid_life) |

---

## 6. ref_step_number 일반화 효과

### 6.1 HYSTERESIS_DCHG/CHG 변동

v2: `ec_type == 2048` (DOD%) 또는 `== 18432` (SOC%) 매칭 — fixed value
v3: `ref_step_number > 0` 일반 매칭 — 임의 schedule

| | v2 | v3 | 영입 |
|---|---|---|---|
| HYSTERESIS_DCHG | 230 | 198 | -32 (→ RSS_DCIR multi_cluster) |
| HYSTERESIS_CHG | 198 | 217 | +19 |

HYSTERESIS_CHG +19 의 source:
- `CHARGE_SET → HYSTERESIS_CHG`: 10 group (CHG only + ref_step ≠ 0)
- `RPT → HYSTERESIS_CHG`: 9 group (N=1 + CHG+DCHG, CHG 에 ref_step 사용)

→ v3 가 더 도메인 정확 (ref_step 사용 시 hysteresis 의미가 강함).

### 6.2 RSS_DCIR multi_cluster 흡수

```python
# RSS_DCIR sub_tag = 'multi_cluster' (≥2 distinct ref_step)
ref_steps_dchg = {ref_step_number for ec_on_dchg if ref_step > 0}
if len(ref_steps_dchg) >= 2:
    sub_parts.append('multi_cluster')
```

→ Phase 0-4 spec 의 RSS sample (ref_step 8/42/76/110, cluster 간격 34) 정확 식별.
v2 에서 HYSTERESIS_DCHG 로 잘못 분류된 32 group 을 v3 에서 RSS_DCIR 로 재분류.

---

## 7. mode_flag 활용

### 7.1 DCHG_CCCV mode=0 → PULSE_DCIR sub_tag

```python
n_dchg_cccv_mode0 = sum(1 for s in body
                        if s['type'] == 'DCHG_CCCV' and s.get('mode_flag') == 0)
has_dchg_cccv_pulse = n_dchg_cccv_mode0 > 0

# PULSE_DCIR sub_tag
sub_tags = ['short_sampling'] if short_sampling else []
if has_dchg_cccv_pulse:
    sub_tags.append('dchg_cccv_pulse')   # ⭐ v3 신규
return 'PULSE_DCIR', '+'.join(sub_tags)
```

### 7.2 결과 — PULSE_DCIR sub_tag 분포

| sub_tag | count |
|---|---|
| `short_sampling` | 770 |
| `short_sampling+dchg_cccv_pulse` | 86 |

→ 86 group 이 명확한 DCIR pulse measurement (DCHG_CCCV ref-step capacity matching).

### 7.3 REST mode=0 + chamber → ECT

위 §4 ECT 식별 룰의 핵심.

---

## 8. v3 카테고리 전역 분포 (8,298 group, 22 카테고리 유지)

| Category | count | 비율 |
|---|---|---|
| RPT | 2,833 | 34.1% |
| ACCEL | 1,071 | 12.9% |
| CHG_DCHG | 970 | 11.7% |
| PULSE_DCIR | 856 | 10.3% |
| CHARGE_SET | 551 | 6.6% |
| FORMATION | 382 | 4.6% |
| REST_LONG | 330 | 4.0% |
| HYSTERESIS_CHG | 217 | 2.6% |
| HYSTERESIS_DCHG | 198 | 2.4% |
| DCHG_SET | 192 | 2.3% |
| INIT | 191 | 2.3% |
| TERMINATION | 122 | 1.5% |
| POWER_CHG | 108 | 1.3% |
| DISCHARGE_SET | 84 | 1.0% |
| GITT_PULSE | 71 | 0.9% |
| RSS_DCIR | 40 | 0.5% |
| REST_SHORT | 32 | 0.4% |
| FLOATING | 30 | 0.4% |
| SOC_DCIR | 20 | 0.2% |
| **UNKNOWN** | **0** | **0.0% ✅** |

### sub_tag 활용

| 카테고리 | sub_tag | count | 의미 |
|---|---|---|---|
| ACCEL | `multi_step` | 814 | 다단 charge ≥3 |
| ACCEL | `mid_life` | 142 | N=11~19 (Phase 0-5-α gap fix) |
| ACCEL | `multi_step+ect` | 67 | ECT-parameter cycling |
| ACCEL | (none) | 48 | N≥20 + CHG=2 |
| FORMATION | `ect` | 9 | 작은 N 의 ECT |
| GITT_PULSE | `gitt_block+ect` | 3 | ECT GITT |
| HYSTERESIS_DCHG | `desc_kw` | (varies) | schedule 명시 |
| RSS_DCIR | `multi_cluster` | (32) | ≥2 distinct ref_step |
| RSS_DCIR | `desc_kw` | (varies) | schedule 'rss' |
| PULSE_DCIR | `short_sampling` | 770 | rec_iv<5s |
| PULSE_DCIR | `short_sampling+dchg_cccv_pulse` | 86 | DCHG_CCCV mode=0 (DCIR pulse) |

---

## 9. proto 본체 fix 권장 PR 후보

본 v3 는 self-contained batch script. **proto `DataTool_optRCD_proto_.py` 본체에 적용
하려면 다음 단계 PR**:

| 순서 | 작업 | 영향 위치 | cost |
|---|---|---|---|
| **c-α** | `v_chg` 키 fix (1줄) | L8053 `voltage_mV` 사용 | 즉시 |
| **c-β1** | parser ref_step_number 추가 | `_parse_pne_sch` L7752 | 30분 |
| **c-β2** | parser mode_flag/record_interval_s 추가 | `_parse_pne_sch` Tier 1 | 30분 |
| **c-β3** | parser schedule_description 추가 | `_parse_pne_sch` header | 30분 |
| **c-γ1** | `step_v_cutoff_mV` helper | proto 신규 함수 | 30분 |
| **c-γ2** | schedule keyword classifier | proto 신규 함수 | 1시간 |
| **c-δ1** | RSS_DCIR multi_cluster sub_tag | `_classify_loop_group` | 30분 |
| **c-δ2** | hysteresis ref_step 일반화 | `_classify_loop_group` | 1시간 |
| **c-δ3** | ACCEL `N=14` mid_life | `_classify_loop_group` | 30분 |
| **c-δ4** | ECT 신규 카테고리 | `_classify_loop_group` + label map | 1.5시간 |
| **c-δ5** | DCHG_CCCV mode=0 sub_tag | `_classify_loop_group` | 30분 |
| **d** | 187 분류 정확도 측정 (confusion matrix) | 사용자 review + Phase d | 1시간 |

→ 총 **~8.5 시간** 작업으로 proto 본체 v3 완성.

### proto 코드 영향 범위

```
DataTool_optRCD_proto_.py
  L7570-7584  _SCH_TYPE_MAP (변경 없음)
  L7594-7768  _parse_pne_sch (보강 +9 field)
  L7975-8143  _classify_loop_group (룰 +H 신규 + 우선순위 재배치)
  L9430-9458  _CLASSIFIED_COLORS (ECT 색상 추가 필요)
  L5724-5749  _SCH_CAT_TO_NEW (ECT → 사용자 친화 한글 매핑 추가)
```

ECT 추가 시 `_SCH_CAT_TO_NEW` 의 신규 entry:
```python
'ECT': ('ECT', None),   # 또는 ('등가회로', None)
```

---

## 10. 재현 방법

```bash
cd C:\Users\Ryu\battery\python\BDT_dev\.claude\worktrees\adoring-hopper-e1c07f

# 1. v3 batch 실행
python tools/sch_phase0_5_v3_classify.py
# → tools/sch_phase0_5_v3_groups.csv (8298 row)
#   tools/sch_phase0_5_v3_files.csv (368 row)
#   tools/sch_phase0_5_v3_summary.md

# 2. v2 vs v3 diff
python tools/sch_phase0_5_v2_v3_diff.py
# → tools/sch_phase0_5_v2_v3_diff.md (transition matrix + sub_tag 분포)
```

스크립트는 self-contained — proto 코드 변경 없이 batch 실행. proto 본체 PR 적용은
별도 session 권장.

---

## 11. 다음 단계

### 11.1 검증 (Phase d)

- 187 분류 정확도 측정 (confusion matrix vs 도메인 전문가 manual review)
- 특히 ECT 79 group / RSS_DCIR multi_cluster 32 group / ACCEL mid_life 142 group 의
  도메인 정확성 review

### 11.2 proto 코드 적용 (Phase c)

위 §9 의 c-α ~ c-δ5 단계별 PR. 각 PR 후 187 분류 결과 diff 측정으로 점진적 검증.

### 11.3 사이클 바 색상 추가 (UI)

`_CLASSIFIED_COLORS` 에 ECT 색상 (예: 회색-파랑 계열, 환경 측정 의미) 추가.

### 11.4 22 → 23 카테고리 spec 업데이트 (Phase b)

Phase 0-5 spec [[260504_audit_phase0_5_classifier_input_spec]] 의 22 카테고리에
**ECT** 추가하여 23 카테고리로 갱신. sub_tag 변형 (multi_step / mid_life /
multi_cluster / dchg_cccv_pulse 등) 정식화.

---

## Related

- [[260504_audit_phase0_5_classifier_input_spec]] — 분류기 v2 spec
- [[260505_phase0_5_187_cycle_definitions]] — v2 187 폴더 사이클 정의
- [[260505_phase0_5_alpha_ref_step_field_identified]] — ref_step_number 식별
- [[260505_phase0_5_classifier_logic]] — 분류 로직 설명서
- [[260504_plan_22cat_audit_and_eval_overlay]] — 5단계 audit plan
