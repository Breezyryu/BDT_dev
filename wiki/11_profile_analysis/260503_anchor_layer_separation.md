---
tags: [bdt, hysteresis, profile-analysis, anchor, soc, dod, design-decision]
date: 2026-05-03
status: implemented
---

# 히스테리시스 분석의 SOC anchor 2-layer 정의

## 배경

BDT 의 프로파일 분석은 cycle 별 SOC 좌표를 어떻게 anchor 할지에 대해 **두 가지 의미상 다른 layer** 가 공존한다. 이 노트는 두 layer 의 정의와 적용 범위를 명문화하여 사용자/개발자 간 혼동을 방지한다.

랩장님 원본 (`DataTool_dev_code/BAK/260204_sy_origin/BatteryDataTool 260204.py` L1366-1477) 의 `pne_chg_Profile_data` / `pne_dchg_Profile_data` 는 **phase-relative anchor** 만 제공. Proto 의 unified profile pipeline 은 이를 **preset 4 (충전 분석) / preset 5 (방전 분석)** 에 보존하면서, 별개로 **preset 3 (히스테리시스)** 를 위한 **absolute cell SOC anchor** 를 추가 도입.

## Layer 1 — Phase-relative anchor (preset 4 / 5)

### 정의

각 cycle 의 chg phase 또는 dchg phase 데이터를 추출해, **해당 phase 의 첫 row 가 SOC = 0** 이 되도록 정규화. SOC 컬럼은 cell 의 절대 charge state 가 아니라 **phase 시작 시점부터의 누적 chg/dchg 량**.

| Phase | SOC 컬럼 의미 | 시작점 | 종료점 (예시) |
|---|---|---|---|
| 충전 | Chgcap / mincapacity 의 누적 (0 부터) | SOC = 0 | SOC = chg_amount (≤ 1.0+잉여) |
| 방전 | Dchgcap / mincapacity 의 누적 (0 부터) | SOC = 0 (= DOD 0) | SOC = dchg_amount |

방전 분석에서 SOC 라는 컬럼명은 **misleading** — 실제 의미는 DOD (Depth of Discharge). 그래프 X축으로 그리면:
- DOD 0% = cell SOC 100% (시작점, 만충 상태)
- DOD 100% = cell SOC 0% (만방 상태)

### 적용 범위

- **Preset 4 (충전 분석)**: scope=charge, overlap=split, axis=SOC. 충전 phase 만 추출 → 모든 cycle 의 chg curve 를 SOC = 0 anchor 에서 출발하는 fan 으로 표시.
- **Preset 5 (방전 분석)**: scope=discharge, overlap=split, axis=SOC. 방전 phase 만 추출 → 모든 cycle 의 dchg curve 를 DOD = 0 anchor 에서 출발하는 fan 으로 표시.

### 사용자 워크플로우 매핑

엑셀 골든 reference (`raw/사내문서/Voltage hysteresis test_Graph format_v1.3_bundle.txt`) 의 raw paste 시트와 numerically 등가:

| 엑셀 시트 | BDT 등가 |
|---|---|
| `[3~12_충전]` | preset 4 + cycle range = `3~12` |
| `[3~12_방전]` | preset 5 + cycle range = `3~12` |
| `[14~23_충전]` | preset 4 + cycle range = `14~23` |
| `[14~23_방전]` | preset 5 + cycle range = `14~23` |

각 시트의 첫 row SOC = 0 정규화는 랩장님 원본 코드의 step 누적 alignment 와 동일.

### 구현 위치

- 충전: `pne_chg_Profile_data` (origin) → `unified_profile_core(scope="charge", ...)` (proto)
- 방전: `pne_dchg_Profile_data` (origin) → `unified_profile_core(scope="discharge", ...)` (proto)

Proto 의 `unified_profile_core` 는 origin 의 step 누적 + 단위 변환 로직을 그대로 보존. SOC offset 적용 없음 (raw phase-relative 좌표 그대로).

## Layer 2 — Absolute cell SOC anchor (preset 3)

### 정의

각 TC 의 SOC 컬럼을 **cell 의 실제 절대 SOC (state of charge)** 좌표로 변환. SaveEndData 의 ChgCap/DchgCap 누적을 통해 각 TC 시작 시점의 절대 SOC 를 산출한 뒤, df 의 raw SOC 를 shift.

```python
# _apply_hysteresis_soc_offsets() L26534-26537
assumed_start = df['SOC'].iloc[0]
df['SOC'] = df['SOC'] - assumed_start + offset  # offset = TC start 의 absolute SOC
```

`offset` 은 `_compute_tc_soc_offsets()` (L871) 가 산출:
- 1차 패스: 무클립 누적의 최저점으로 `initial_full` 추정 (cell 이 cycle 1 시작 시 만충 상태인지 0 상태인지)
- 2차 패스: `[_HYST_SOC_HARD_MIN=-0.2, _HYST_SOC_HARD_MAX=1.2]` 클립 누적으로 각 TC 시작 SOC 산출

### 적용 범위

- **Preset 3 (히스테리시스)**: scope=cycle, overlap=connected, axis=SOC, **TC 페어링 자동 ON**. 각 TC 의 chg + dchg phase 양쪽이 추출되며, SOC 좌표가 절대 cell SOC. Cross-TC 페어링 (TC N 의 dchg + TC N+1 의 chg) 으로 closed loop fan 형성.

### 사용자 protocol 의 absolute anchor 산출 예 (TC 3-12 방전 hyst)

| TC | 시작 SOC (offset) | df 내 phase | 종료 SOC |
|---:|---|---|---|
| 3 | 0.0 | chg 0→1.0, dchg 1.0→0.9 | 0.9 |
| 4 | 0.9 | chg 0.9→1.0, dchg 1.0→0.8 | 0.8 |
| 5 | 0.8 | chg 0.8→1.0, dchg 1.0→0.7 | 0.7 |
| ... | ... | ... | ... |
| 11 | 0.2 | chg 0.2→1.0, dchg 1.0→0.1 | 0.1 |
| 12 | 0.1 | chg 0.1→1.0, dchg 1.0→0.0 | 0.0 |
| 13 | 0.0 | chg 0→1.0, dchg 1.0→0.0 (RPT) | 0.0 |

Cross-TC 페어링 결과:
- Cy0003 = TC 3 dchg (SOC 1.0→0.9) + TC 4 chg (SOC 0.9→1.0) = **ΔDOD 10% closed loop at SOC 90~100%**
- Cy0012 = TC 12 dchg (SOC 1.0→0.0) + TC 13 chg (SOC 0.0→1.0) = **ΔDOD 100% envelope spanning SOC 0~100%**

### 구현 위치

- Anchor 산출: `_compute_tc_soc_offsets` (L871)
- Anchor 적용: `_apply_hysteresis_soc_offsets` (L26467) — preset 3 (cycle scope + connected) 진입 시 자동 호출
- 페어링 plot: `_plot_one()` cycle_soc legacy_mode (L27619~) — `_segments` 결정 + `graph_profile` 호출

## Layer 2-α — Phase canonical anchor (preset 3 보정 단계)

### 정의

Layer 2 의 absolute cell SOC anchor 적용 후, **각 hyst TC 의 primary phase 첫 row 를 canonical SOC 로 추가 shift**:
- **Dchg 그룹** (방전 hyst): 각 TC 의 dchg phase 첫 row → SOC **1.0**
- **Chg 그룹** (충전 hyst): 각 TC 의 chg phase 첫 row → SOC **0.0**

### 동기

Layer 2 의 cumul anchor 는 raw 데이터의 누적 chg/dchg balance 에 의존. 실 protocol 에서 **CC-CV 잉여** (CC 단계 이후 CV 단계 동안 ChgCap 이 nominal 정격용량을 초과하여 누적, 보통 +0.05~0.10) 가 발생하면 anchor cumul 에 흡수되어:

- TC 3-12 에서 dchg phase 첫 row SOC ≠ 1.0 (예: 1.05 또는 0.97 로 어긋남)
- TC 14-23 에서 chg phase 첫 row SOC ≠ 0.0 (예: 0.03 으로 어긋남)

사용자가 직접 보고한 시각 어긋남:
> "TC3-12: 일부 close loop가 SOC 1.0 시작점이 아님"
> "TC14-23: SOC 0.0 시작점이 아님"

### 알고리즘

```python
# _apply_hysteresis_phase_canonical_anchor (L26552 부근, 신규)
if direction == 'Dchg':
    dchg_first = df[df['Condition'] == 2]['SOC'].iloc[0]
    delta = 1.0 - dchg_first
elif direction == 'Chg':
    chg_first = df[df['Condition'] == 1]['SOC'].iloc[0]
    delta = 0.0 - chg_first
df['SOC'] = df['SOC'] + delta  # 전체 df shift (chg/dchg phase 모두)
```

전체 df 를 같은 값으로 shift 하므로 chg phase 와 dchg phase 의 상대 거리 (=cell 의 실제 ΔSOC trajectory) 보존. 다만 cumul anchor 의 절대 좌표는 약간 어긋남 (e.g., raw 1.05 였던 chg end 가 1.0 으로 보정되어 -0.05 shift 적용).

### 사용자 protocol 의 canonical anchor 산출 (CC-CV 잉여 +0.05 가정)

| TC | absolute (Layer 2) start | dchg first | canonical delta | canonical (Layer 2-α) start |
|---:|---|---|---|---|
| 3 | 0.0 | 1.05 | -0.05 | -0.05 |
| 4 | 0.9 | 1.05 | -0.05 | 0.85 |
| 5 | 0.8 | 1.05 | -0.05 | 0.75 |
| ... | ... | ... | ... | ... |
| 12 | 0.1 | 1.05 | -0.05 | 0.05 |
| 14 | 0.05 (drift) | - | -0.05 | 0.0 |
| 15 | 0.05 | - | -0.05 | 0.0 |
| ... | ... | ... | ... | ... |

→ 모든 dchg arc 가 SOC 1.0 에서 정확히 출발, 모든 chg arc (chg 그룹) 가 SOC 0.0 에서 정확히 출발.

### Closure 영향

Cross-TC 페어링의 closure 는 chg amount 가 일관될 때 보존:
- TC 3 dchg end (canonical) = 1.0 - 10% = 0.9
- TC 4 chg start (canonical) = 1.0 - chg_amount = 1.0 - 10% = 0.9 ✓
- 두 endpoint 일치 → closure 보존

CC-CV 잉여가 TC 마다 다르거나 chg amount 가 변동하면 약간의 gap 발생 (보통 < 1%, 시각적 무시 가능).

### 구현 위치

- 신규 메서드: `_apply_hysteresis_phase_canonical_anchor` (L26552~)
- 보조 staticmethod: `_compute_hysteresis_phase_canonical_delta` (df, info → delta)
- 호출 위치: `unified_profile_confirm_button` L27365 (Layer 2 직후)
- 라벨 캐시: `self._hyst_phase_label_maps` (folder_idx → tc → hyst_label_info)
- Pair fallback 동기화: `_profile_render_loop` L21164 — 캐시된 label maps 로 fallback 시 동일 정규화

## Layer 2-β — Dchg endpoint scaling (preset 3 보정 단계)

### 정의

Layer 2-α 후에도 잔존하는 dchg phase 의 **마지막 row (endpoint)** drift 를 linear scaling 으로 canonical end 에 강제 정렬:
- **Dchg 그룹**: dchg phase 마지막 row → SOC `1 - depth_pct/100` (예: TC 12 depth 100% → 0.0, TC 4 depth 20% → 0.8)
- **Chg 그룹**: dchg phase 마지막 row → SOC **0.0** (within-TC return-to-start)

### 동기

Layer 2-α 의 단순 shift 는 phase **첫 row** 만 anchor — 마지막 row 는 raw 데이터의 chg/dchg amount 에 의존:
- Chg 그룹: chg amount > dchg amount (CC-CV 잉여) 시 dchg 마지막 row > 0 → 사용자 보고 "TC 14-23 dchg 끝점 ≠ 0.0"
- Dchg 그룹: 일반적으로 amount 일치 (자동 정렬), 단 cumul drift 잔존 시 보정 필요

### 알고리즘

```python
# Step B: dchg phase 의 endpoint scaling (Layer 2-α 직후)
s_first = dchg_first_row_SOC  # Layer 2-α 가 이미 canonical 로 anchor 함
s_last = dchg_last_row_SOC

if direction == 'Dchg':
    target_last = 1.0 - depth_pct / 100.0
elif direction == 'Chg':
    target_last = 0.0

scale = (target_last - s_first) / (s_last - s_first)

# 안전 한도: ±20% 이내 보정만 허용 (이상 데이터 보호)
if abs(scale - 1.0) <= 0.20:
    df.loc[dchg_idx, 'SOC'] = s_first + (df['SOC'] - s_first) * scale
```

### Side effect

- chg phase 는 보존 (scaling 미적용) → cross-TC 페어링의 closure 가 약간 어긋날 수 있음 (보통 < 1% SOC, 시각적 무시 가능)
- dQdV 값은 1/scale 만큼 영향 받음 (보통 < 5% 변화)
- scale = 1.0 (변화 없음) 또는 |scale - 1.0| > 0.20 (큰 보정) 시 skip

### 구현 위치

- 신규 staticmethod: `_scale_hysteresis_dchg_phase_to_canonical_end` (L26625~)
- 호출 위치: `_apply_hysteresis_phase_canonical_anchor` Step B (Layer 2-α 직후)
- Pair fallback 동기화: `_profile_render_loop` L21164 — fallback fetch 시 동일 적용

## Layer 1 vs Layer 2 vs Layer 2-α/β — 사용 가이드

| 분석 의도 | 추천 layer / preset |
|---|---|
| 단일 방향 chg curve 비교 (방전 hyst 의 충전 데이터 sheet 등가) | **Phase-relative (Layer 1) — preset 4** |
| 단일 방향 dchg curve 비교 (방전 hyst 의 방전 데이터 sheet 등가) | **Phase-relative (Layer 1) — preset 5** |
| Closed-loop fan 시각화 (히스테리시스 envelope + mini-loops) | **Absolute + canonical (Layer 2 + 2-α + 2-β) — preset 3** |
| Cross-TC 페어링 데이터 추출 (long-format 통합 시트) | **Layer 2 + 2-α + 2-β — preset 3** + `Hysteresis_Analysis` 시트 활용 |
| CC-CV 잉여 / cumul drift 가 큰 protocol | **Layer 2-α (시작점) + 2-β (끝점) 자동 적용** — phase endpoint 강제 정렬 |
| dQdV CV 영역 노이즈 제외 | **preset 3 의 origin_compat=False** (자동, 260503 기본 ON) |

## Layer 간 변환 (참고)

Phase-relative SOC ↔ Absolute SOC:

```
# 충전 phase
absolute_SOC[i] = anchor[TC] + chgcap_cumul[i]
phase_relative_SOC[i] = chgcap_cumul[i] = absolute_SOC[i] - anchor[TC]

# 방전 phase
absolute_SOC[i] = (anchor[TC] + chg_total) - dchgcap_cumul[i]
phase_relative_SOC[i] = dchgcap_cumul[i] = (anchor[TC] + chg_total) - absolute_SOC[i]
```

여기서 `anchor[TC]` 는 `_compute_tc_soc_offsets` 의 출력. `chg_total` 은 해당 TC 의 chg phase 종료 시점의 chgcap 누적.

## Layer 별 envelope 의미

| Layer | envelope 정의 | 색상 | 예 (TC 3-12 dchg hyst) |
|---|---|---|---|
| Layer 1 (preset 4) | 가장 큰 chg span 의 cycle | rainbow rank | TC 3 (chg 0→100% full) |
| Layer 1 (preset 5) | 가장 큰 dchg span 의 cycle | rainbow rank | TC 12 (dchg 100→0% full) |
| Layer 2 (preset 3) | depth=100% 의 closed loop | rainbow rank 0 (black) | Cy0012 (TC 12 dchg + TC 13 chg) |

## 관련 변경로그 / 코드 참조

- 원본 anchor 정의: `DataTool_dev_code/BAK/260204_sy_origin/BatteryDataTool 260204.py` L1366-1477
- Anchor 산출: `DataTool_dev_code/DataTool_optRCD_proto_.py` L871 `_compute_tc_soc_offsets`
- Anchor 적용 (preset 3): L26467 `_apply_hysteresis_soc_offsets`
- 페어링 결정 (preset 3): L27664~ `_render_major` + `_segments`
- Bug fix changelog: `docs/code/01_변경로그/260503_fix_hysteresis_dchg_major_cross_tc_pair.md`
- 회귀 검증: `tools/test_code/hysteresis_render_decision_validator.py`
- 사전 작업: `wiki/40_work_log/260429_hysteresis_unified_flow.md`

## 디버깅 팁

만약 사용자가 보고하는 시각이 **위 정의와 어긋나면**, 다음 순서로 확인:

1. **Preset 확인**: 어느 preset 인가? (3 / 4 / 5)
   - Preset 3: closed loop 이 안 닫히면 → `_render_major` + cross-TC 페어링 + offset map 검증
   - Preset 4/5: phase-relative 가 어긋나면 → unified_profile_core 의 step 누적 검증
2. **Hyst label 확인**: `_compute_tc_hysteresis_labels` 가 cycle 별 (direction, depth_pct) 를 정확히 산출했는지 — `tools/test_code/hysteresis_label_validator.py`
3. **Render 결정 확인**: `_render_major` truth table 검증 — `tools/test_code/hysteresis_render_decision_validator.py`
4. **Anchor 산출 확인**: `_compute_tc_soc_offsets` 의 `_perf_logger.info('[soc_offset] ...')` 로그
5. **Pair fetch 확인**: TC N+1 이 selection 밖이면 fallback fetch 경로 (`_profile_render_loop` L21157~) 가 정상 동작했는지 + offset 수동 적용됐는지
