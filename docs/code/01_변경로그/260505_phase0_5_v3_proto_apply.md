# 260505 — Phase 0-5 v3 proto 본체 적용 (분류기 v3)

## 배경

[[wiki/10_cycle_data/260505_phase0_5_v3_implementation]] 의 v3 batch script 를 proto 본체
`DataTool_optRCD_proto_.py` 에 직접 적용. sub_tag 제외, 카테고리 단위 분류 룰만 변경.

## 변경 사항

### `_parse_pne_sch` (L7594~)

#### 1. Header schedule_description 추가

```python
# +664 ASCII 64 byte → schedule keyword prior 활용
desc_b = data[664:664 + 64]
null_idx = desc_b.find(b'\x00')
if null_idx >= 0:
    desc_b = desc_b[:null_idx]
schedule_description = desc_b.decode('ascii', errors='replace').strip()
```

return dict 에 `'schedule_description': schedule_description` 추가.

#### 2. Step common metadata 추가 (모든 type)

```python
step_info['record_interval_s'] = struct.unpack_from('<f', blk, 336)[0]
step_info['mode_flag'] = struct.unpack_from('<I', blk, 84)[0]
step_info['chamber_temp_c'] = struct.unpack_from('<f', blk, 396)[0]
```

#### 3. End condition 에 ref_step_number 추가 (Phase 0-5-α)

```python
ec_type = struct.unpack_from('<I', blk, 500)[0]
ec_enabled = struct.unpack_from('<I', blk, 504)[0]
if ec_type != 0 and ec_enabled == 1:
    step_info['end_condition'] = {
        'type': ec_type,
        'value_pct': round(ec_value, 2),
        'ref_step_number': (ec_type >> 8) & 0xFF,  # ⭐ Phase 0-5-α
        'type_marker': ec_type & 0xFF,             # 본 데이터셋 항상 0
    }
```

`+500 uint32 = (ref_step_number << 8) | type_marker` 인코딩 (Phase 0-5-α 발견).

### 신규 Helper 함수 (L8009~)

```python
def _step_v_cutoff_mV(s: dict) -> float:
    """CC vs CCCV 의 실제 V cutoff 추출 (사용자 통찰)."""
    if s['type'] in ('CHG_CCCV', 'DCHG_CCCV'):
        return s.get('voltage_mV', 0)        # CV target
    if s['type'] in ('CHG_CC', 'DCHG_CC'):
        return s.get('end_voltage_mV', 0)    # EndCondition
    return 0


def _schedule_desc_keyword(desc: str) -> str:
    """schedule_description 에서 시험 keyword 추출 (rss/hysteresis/gitt/ect/...)."""
    ...
```

### `_classify_loop_group` (L8051~)

#### 1. ⚠️ `v_chg` 키 mismatch fix (Phase 0-1a)

```python
# Before (bug):
has_v_cut = any(s.get('v_chg_mV', s.get('v_chg', 0)) > 0 for s in chg_steps)
# parser output 에 'v_chg_mV' 또는 'v_chg' 키 없음 → 항상 False

# After:
has_v_cut = any(s.get('voltage_mV', 0) > 0 for s in chg_steps)
```

→ FLOATING 30 group 활성화.

#### 2. ref_step_number 일반화 (Phase 0-5-α)

```python
has_ref_step_dchg = any(
    s.get('end_condition', {}).get('ref_step_number', 0) > 0
    for s in ec_on_dchg)
has_ref_step_chg = any(
    s.get('end_condition', {}).get('ref_step_number', 0) > 0
    for s in ec_on_chg)

# HYSTERESIS_DCHG (변경)
# Before: ec_type == 2048 fixed value
if N == 1 and not has_short_dchg and has_ref_step_dchg:
    return 'HYSTERESIS_DCHG'

# HYSTERESIS_CHG (변경)
# Before: ec_type == 18432 fixed value
if N == 1 and not has_short_chg and has_ref_step_chg:
    return 'HYSTERESIS_CHG'
```

→ 임의 ref_step 의 hysteresis schedule 식별 가능.

#### 3. RSS_DCIR 우선순위 변경 + has_short_dchg 가드 추가

```python
# RSS_DCIR (HYSTERESIS_DCHG 보다 먼저 — 도메인 정확성)
# 기존: has_ec + N=1 + DCHG≥4 + body≥10 (HYSTERESIS_DCHG 뒤)
# v3:  + not has_short_dchg (긴 DCHG = 정상상태) — PULSE_DCIR (짧은 펄스) 와 분리
if (N == 1 and has_ec and len(dchg_steps) >= 4 and len(body) >= 10
        and not has_short_dchg):
    return 'RSS_DCIR'
```

→ Q8 ATL Main 2.0C Rss RT (v2 RSS 8 group) + multi-cluster RSS pattern 모두 흡수.

#### 4. ACCEL N=11~19 mid-range gap fix (Phase 0-5-α)

```python
# ACCEL strong (변경 없음)
if N >= 20 and len(chg_steps) >= 2 and dchg_steps:
    return 'ACCEL'

# ⭐ ACCEL mid-range (신규) — N=11~19 + multi-step (≥3 CHG)
# SOC_DCIR / PULSE_DCIR 룰 이후 처리하여 disambiguate
if 11 <= N <= 19 and len(chg_steps) >= 3 and dchg_steps:
    return 'ACCEL'
```

→ 복합floating HaeanProto N=14, 김영환/박기진 280day N=14 등 v2 UNKNOWN 142 group 흡수.

#### 5. PULSE_DCIR — DCHG_CCCV mode=0 단독 hint (신규)

```python
has_dchg_cccv_pulse = any(
    s['type'] == 'DCHG_CCCV' and s.get('mode_flag', 0) == 0
    for s in body)

# PULSE_DCIR 기존 룰 (변경 없음)
if has_ec and has_short_dchg and len(dchg_steps) >= 2 and len(body) >= 5:
    return 'PULSE_DCIR'

# ⭐ PULSE_DCIR (강한 hint, 신규) — DCHG_CCCV mode=0 = DCIR pulse
# 도메인 검증: 100% EC enabled, capacity reference matching
if has_dchg_cccv_pulse and len(dchg_steps) >= 2:
    return 'PULSE_DCIR'
```

## 추가 변경 (260505) — STORAGE_CYCLE 신규 카테고리

### 사용자 도메인 지적

> "복합사이클 분류에서 중간중간 formation으로 분류되는 것들의 사이클 목적은
>  '만충저장' 이다."

대상 schedule: `수명_복합floating/260203_260531_01_최웅철_4268mAh_SDI GB6 PRO14 GEN4 1.3C 고온복합/`

검증 결과 (전체 FORMATION 382 group 의 chg_crate 분포):

| chg_crate | count | 도메인 |
|---|---|---|
| 0.0~0.2C | 46 | ⭐ 진짜 FORMATION (저속 SEI 형성) |
| 0.5~2.0C | 336 | ⚠️ 만충저장 (4.5V + 24h CV + 주기 capacity check) |

→ 88% (336/382) 가 도메인적으로 FORMATION 아님. 신규 카테고리 STORAGE_CYCLE 분리.

### 변경 사항

#### 1. `_SCH_CAT_TO_NEW` (L5730)

```python
# UI 표기는 기존 FLOATING 과 동일 '저장(floating)' 으로 통일 (사용자 요청, 260505).
# internal category 는 STORAGE_CYCLE / FLOATING 으로 분리 보존 (분석/통계용).
'STORAGE_CYCLE': ('저장', 'floating'),
```

#### 2. `_CLASSIFIED_COLORS` (L9553)

```python
# '저장(floating)' 라벨로 FLOATING + STORAGE_CYCLE 통합 표시 (color_idx=7).
'저장(floating)': {'color_idx': 7, 'desc': '저장 (Floating + 만충 cycling, 복합floating 시험)'},
```

#### 3. `_build_loop_group_info` post-pass (L8344)

```python
# Post-pass — STORAGE_CYCLE 변환 (Phase 0-5 v3, 260505):
schedule_desc = parsed.get('schedule_description', '') or ''
desc_kw = _schedule_desc_keyword(schedule_desc)
has_long_cv_step = any(
    s['type'] == 'CHG_CCCV' and s.get('time_limit_s', 0) >= 43200
    for s in parsed.get('steps', []))
if desc_kw == 'floating' or has_long_cv_step:
    for g in result:
        if g['category'] == 'FORMATION':
            g['category'] = 'STORAGE_CYCLE'
```

→ schedule level 단서 (`floating` keyword OR ≥12hr CV step) 로 복합floating
schedule 의 FORMATION → STORAGE_CYCLE 변환. GITT/DCIR/일반 시험의 FORMATION 은 보존.

### 변환 결과

| Category | v3 (initial) | v3.1 (STORAGE) | 변동 |
|---|---|---|---|
| FORMATION | 382 | **48** | **-334** (진짜 화성만) |
| **STORAGE_CYCLE** (신규) | 0 | **334** | +334 (만충저장 분리) |

총 카테고리 22 → **23** (STORAGE_CYCLE 추가).

## 결과 (368 .sch / 8,298 group)

| Category | v2 | proto v3 | 변동 |
|---|---|---|---|
| RPT | 2842 | 2802 | -40 (envelope merge) |
| **ACCEL** | 929 | **1071** | **+142** (UNKNOWN gap fix) |
| CHG_DCHG | 970 | 956 | -14 (envelope merge) |
| PULSE_DCIR | 856 | 856 | 0 |
| CHARGE_SET | 561 | 551 | -10 |
| FORMATION | 382 | 382 | 0 |
| REST_LONG | 330 | 330 | 0 |
| HYSTERESIS_CHG | 198 | 240 | +42 (ref_step + envelope) |
| HYSTERESIS_DCHG | 230 | 220 | -10 (RSS 흡수) |
| DCHG_SET | 192 | 192 | 0 |
| INIT | 191 | 191 | 0 |
| TERMINATION | 122 | 122 | 0 |
| POWER_CHG | 108 | 108 | 0 |
| DISCHARGE_SET | 84 | 84 | 0 |
| GITT_PULSE | 71 | 71 | 0 |
| **RSS_DCIR** | **8** | **40** | **+32** (multi-cluster 흡수) |
| REST_SHORT | 32 | 32 | 0 |
| FLOATING | 30 | 30 | 0 |
| SOC_DCIR | 20 | 20 | 0 |
| **UNKNOWN** | **142** | **0** | **-142 ✅** |

총 **22 카테고리 유지** (신규 카테고리 없음, sub_tag 미사용 — 사용자 요청).

## 검증

| 항목 | 결과 |
|---|---|
| Python syntax | ✓ OK |
| 368 .sch parse | ✓ 0 failed |
| 8,298 group classify | ✓ 동일 |
| UNKNOWN | ✓ 0 |
| batch v3 vs proto v3 | hysteresis envelope merge 효과 (의도된 차이) 외 카테고리 단위 일치 |

`_merge_hysteresis_envelopes` 후처리 (사용자 요청 260503) 가 proto 에만 있어 RPT/CHG_DCHG -45,
HYSTERESIS +45 의 차이가 batch 와 발생하지만, 이는 의도된 동작.

## 영향 범위

### 분류 출력 (사용자 측 변동)

- `사이클(ACCEL)` 카테고리 + 142 group (복합floating UNKNOWN 흡수)
- `히스테리시스(방충전)/(충방전)` 카테고리 + 42 group (ref_step 일반화로 임의 schedule 식별)
- `DCIR` 카테고리 + 32 group (RSS multi-cluster 흡수)
- `저장(floating)` 카테고리 + 30 group 활성화 (`v_chg` 키 fix)
- `unknown` 카테고리 → 0 group

### parser output schema 확장

기존 키:
- `step`, `idx`, `type`, `type_code`
- `voltage_mV`, `current_mA`, `time_limit_s`
- `end_voltage_mV`, `end_current_mA`, `capacity_limit_mAh`
- `cv_voltage_mV`, `cv_cutoff_mA` (CCCV 만)
- `loop_count`, `goto_target_step`, `goto_repeat_count` (LOOP 만)
- `goto_target` (GOTO 만)
- `end_condition` (EC enabled 만)

신규 키:
- step common: `record_interval_s`, `mode_flag`, `chamber_temp_c`
- `end_condition.ref_step_number`, `end_condition.type_marker`
- top-level: `schedule_description`

### 호환성

- 기존 분류 결과를 보존하면서 v3 변경만 추가 (예: HYSTERESIS_DCHG 230 → 220 은 8 group RSS_DCIR 흡수 효과; v2 의 RSS 정확성은 유지).
- UI / 사이클 바 색상 (`_CLASSIFIED_COLORS`) 변경 없음 (22 카테고리 유지).
- `_SCH_CAT_TO_NEW` 변경 없음.
- 사용자 친화 한글 라벨 (`사이클(ACCEL)`, `히스테리시스(방충전)` 등) 그대로.

## 재현

```bash
cd C:\Users\Ryu\battery\python\BDT_dev\.claude\worktrees\adoring-hopper-e1c07f
python tools/sch_phase0_5_v3_proto_verify.py
# → tools/proto_v3_groups.csv (8298 group, 22 카테고리)
```

## 다음 단계

1. **Phase d (정확도 측정)** — 187 폴더 분류 결과의 도메인 review (ACCEL +142, RSS +32, HYS +42)
2. **proto 본체 unit test** — `_classify_loop_group` 의 22 카테고리 fixture 추가
3. **사이클 바 UI 검증** — 변경된 분류 결과가 BDT UI 에서 정상 표시되는지 확인
4. **사용자 acceptance** — 도메인 expert manual review 후 main merge

## Related

- [[wiki/10_cycle_data/260505_phase0_5_v3_implementation]] — v3 batch 구현 노트
- [[wiki/10_cycle_data/260505_phase0_5_alpha_ref_step_field_identified]] — Phase 0-5-α
- [[wiki/10_cycle_data/260505_phase0_5_classifier_logic]] — 분류 로직 설명서
- [[wiki/10_cycle_data/260504_audit_phase0_5_classifier_input_spec]] — v2 spec
- [[docs/code/01_변경로그/260505_phase0_5_v3_classifier]] — batch v3 변경로그
