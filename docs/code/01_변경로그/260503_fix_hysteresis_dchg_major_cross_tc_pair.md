# 히스테리시스 Dchg major 페어링 + Phase canonical anchor + Dchg endpoint scaling + CV 마스킹

날짜: 2026-05-03
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수:
- `_plot_one()` cycle_soc legacy_mode (L27664 부근) — Fix 1
- `_apply_hysteresis_phase_canonical_anchor()` (L26552 부근, 신규) — Fix 2 + Fix 3
- `_compute_hysteresis_phase_canonical_delta()` staticmethod (신규) — Fix 2
- `_scale_hysteresis_dchg_phase_to_canonical_end()` staticmethod (신규) — Fix 3
- `unified_profile_confirm_button()` (L27365~) — canonical anchor 호출 + `origin_compat=False`
- `_profile_render_loop()` (L21164~) — pair fallback 동기화 (anchor + scaling)

## 변경 요약

본 PR 은 사용자 보고 6건을 단일 변경 세트로 처리:

1. **Fix 1** — Cy0003 / Cy0012 페어링 우회 버그
   → `_render_major` 변수: Dchg + 페어링 활성 시 minor 처리, cross-TC 페어링 적용
2. **Fix 2** — Phase 시작점 SOC 정렬 (Dchg→1.0, Chg→0.0)
   → `_apply_hysteresis_phase_canonical_anchor`: 첫 row shift 로 CC-CV 잉여 + cumul drift 흡수
3. **Fix 3** — Dchg endpoint 정렬 (Cy0012 dchg start, TC 14-23 dchg end)
   → `_scale_hysteresis_dchg_phase_to_canonical_end`: dchg phase 의 마지막 row 를 canonical end (`1 - depth%/100` Dchg 또는 `0.0` Chg) 로 linear scaling
4. **Fix 4** — dQdV 의 CV 영역 노이즈 제거
   → `origin_compat=False`: hysteresis preset 의 dQdV 도 CV (|ΔV|<2mV) 마스킹 적용
5. **Fix 5** — 사이클 분류 boundary 누락 (TC 12, TC 23) + 라벨 명칭 변경
   → `_merge_hysteresis_envelopes`: hyst 그룹 직후의 단일 TC RPT envelope 흡수 (depth 100% 인식)
   → 라벨: '히스테리시스(방전/충전)' → '히스테리시스(방충전/충방전)' 으로 페어링 의미 명확화
6. **Fix 6** — 단일방향 분석 (preset 4/5) 의 axis_mode (SOC/DOD) 일관성
   → `_calc_soc`: charge/discharge scope 에서 axis_mode 반영 — `SOC = 1 − DOD` 관계 보장
   → `_plot_one` (chg/dchg legacy): X축 라벨 + Excel 헤더 동적 결정

## 배경 — 사용자 보고

**Bug 1 (페어링 우회)**:

> "TC 3-12 > hysteresis 분석 시 작업물이 Cy0004~Cy0011은 의도대로 잘 출력된다.
> Cy0003과 Cy0012가 충방전 profile이 섞여서 출력되는 문제다."
> "cyc0004~0011은 충전+방전이 같은 DOD, SOC 간격이지만, cyc0003, 0012는 충방전 간격이 다르다."

**Bug 2 (SOC 시작점 정렬)**:

> "TC3-12: 일부 close loop가 SOC1.0 시작점이 아님"
> "TC14-23: SOC 0.0 시작점이 아님"

랩장님 원본 (`pne_chg_Profile_data` / `pne_dchg_Profile_data`) 의 phase-relative anchor 와
Manual Excel ([3~12_충전], [3~12_방전], 등) 의 시작점 정렬을 hysteresis preset 의 closed-loop
fan 시각에서도 보장 필요.

**Bug 3 (SOC 끝점 정렬 + dQdV CV 노이즈)**:

> "1. Cy0012 방전 프로파일의 시작(역순) SOC 1.0이 아님"
> "2. TC 13-24: 방전의 끝점이 정확히 SOC 0.0이 아님"
> "3. dQdV 산정 시, 충전의 CV 구간은 제외하자"

Fix 2 의 단순 shift 만으로는 dchg phase 의 endpoint 가 canonical end 에 도달하지 않음
(per-TC chg/dchg amount 불일치, CC-CV 잉여 잔존). dchg phase 의 linear scaling 으로
endpoint 를 강제 정렬 + CV 영역 dQdV 노이즈 제거.

**Bug 4 (사이클 분류 boundary 누락 + 라벨 변경)**:

> "현재: hysteresis(TC3-11, TC14-22)로 분류됨"
> "변경: 방충전hysteresis(TC3-12), 충방전hysteresis(TC14-23)"
> "예외 케이스로 수정하기 보다는 충방전 .sch 패턴 파일에서 의도를 파악 후 분류"

`_classify_loop_group` 의 HYSTERESIS_DCHG/CHG 판정 룰 (L8013-8026) 은 EC type=2048
(DOD%) / type=18432 (SOC%) 조건. 그러나 사용자 protocol 의 마지막 cycle (depth 100%
envelope) 은 voltage cutoff 로 정의되어 RPT 로 fall-through → 사이클 바에서 hyst
그룹에서 누락. `.sch` 의 인접 패턴 (단일 TC RPT 가 hyst 그룹 직후 + chg+dchg 구조)
을 인식하여 hyst envelope 으로 흡수.

**Bug 5 (X축 SOC/DOD 옵션의 SOC=1−DOD 일관성)**:

> "X축 SOC, DOD 옵션 검토"
> "* SOC = 1−DOD"
> "* 프로파일 분석 시(히스테리시스 분석 포함), SOC와 DOD의 시작점은 0.0"

랩장님 원본 (`oper1.py`) 은 충전 분석 데이터를 항상 ChgCap (0→1, 라벨 "SOC") 로,
방전 분석을 항상 DchgCap (0→1, 라벨 "DOD") 로 출력. 자연 anchor (Chg+SOC, Dchg+DOD)
는 X 시작점 = 0 ✓. 그러나 사용자가 axis_mode 를 토글 (예: 충전 분석 + DOD axis,
방전 분석 + SOC axis) 시 X 데이터가 axis_mode 에 무관하여 SOC=1−DOD 깨뜨림.

Hysteresis 분석 (preset 3) 은 별도 로직 (Layer 2 + 2-α + 2-β) 으로 절대 cell SOC
좌표를 사용하므로 본 fix 영향 없음 — 사용자 명시 ("Fix B/C 는 기존 hysteresis 분석
구조 유지").

사용자 protocol (Voltage hysteresis test, TC 3-12 방전 hyst):

| TC | CHG step | DCHG step | depth (라벨) |
|---:|---|---|---|
| 3 | **0→100%** (full, RPT 후 만충) | 100→90% | 10% |
| 4 | 90→100% (recovery) | 100→80% | 20% |
| 5~10 | 부분 chg (recovery) | 100→{70..30}% | 30%~70% |
| 11 | 20→100% | 100→10% | 90% |
| 12 | 10→100% | **100→0%** (full envelope) | 100% |
| 13 | 0→100% (full) | 100→0% (full) | RPT (post) |

페어링 모델 — `TC N dchg + TC (N+1) chg = closed loop`:
- Cy0003 = TC3 dchg (100→90%) + TC4 chg (90→100%) = ΔDOD 10% mini-loop (좁음)
- Cy0004~Cy0011 = 같은 패턴, depth 20%~90%
- Cy0012 = TC12 dchg (100→0%) + TC13 chg (0→100%) = ΔDOD 100% envelope

## 진단

`_apply_hysteresis_soc_offsets()` (L26545) 의 major 판정:

```python
soc_range = df['SOC'].max() - df['SOC'].min() if len(df) > 0 else 0
result_obj._hyst_type = 'major' if soc_range >= 0.98 else 'minor'
```

사용자 protocol 의 raw SOC range 계산:

| TC | df 의 SOC 범위 | `_is_major` |
|---:|---|---|
| 3 | [0, 1.0] (chg 0→100% + dchg 100→90%) → 1.0 | **True** |
| 4-11 | 부분 범위 (예: TC 4 = [0.8, 1.0]) → 0.2~0.9 | False |
| 12 | [0, 1.0] (chg 10→100% + dchg 100→0%) → 1.0 | **True** |
| 14-22 | 작은 범위 → 0.1~0.9 | False |
| 23 | [0, 1.0] (chg 0→100% + dchg 100→0%) → 1.0 | **True** |

→ TC 3, TC 12 (Dchg) 와 TC 23 (Chg) 가 모두 major.

L27665 의 페어링 가드 (Bug 발생 지점):

```python
if 'Condition' in p.columns and not _is_major:
    # segment 분할 + cross-TC 페어링 (Dchg/Chg 분기)
else:
    # major fallthrough — p.SOC, p.Vol 통째 plot
```

→ **TC 3, TC 12 가 major 분기로 떨어져 segment 분할이 우회**되어, 페어링 없이 chg + dchg 가 한 번에 plot:

- Cy0003 plotted: TC 3 의 chg arc (0→100%) **+** dchg arc (100→90%) — chg 폭 100% vs dchg 폭 10% **비대칭**
- Cy0012 plotted: TC 12 의 chg arc (10→100%) **+** dchg arc (100→0%) — chg 폭 90% vs dchg 폭 100% **비대칭**

사용자가 보고한 "충방전 간격이 다르다" 의 정확한 메커니즘.

TC 23 (Chg major) 도 동일하게 fallthrough 하지만, 사용자 protocol 에서 TC 23 = chg 0→100% + dchg 100→0% **자체완결 within-TC envelope** 이라 fallthrough 결과가 의도와 일치 (사용자: "TC 14-23 으로 HYSTERESIS 분석하면 ok").

## 수정 1 — Render 분기 surgical fix

L27664 부근에 `_render_major` 변수 도입:

```python
# Before
if 'Condition' in p.columns and not _is_major:
    ...
```

```python
# After
# Dchg 페어링 + raw SOC range ≥ 0.98 의 cycle 은 의미상 minor.
# 사용자 protocol 예: TC 3 = chg 0→100% + dchg 100→90% (depth 10%
# mini-loop), TC 12 = chg 10→100% + dchg 100→0% (depth 100%
# envelope). raw SOC range 가 둘 다 1.0 이라 _is_major=True 로
# over-classify 되어 segment 분할이 우회 → chg + dchg 가 한 곡선
# 으로 그려져 비대칭 loop 발생. cross-TC 페어링 (Cy0003 = TC3 dchg
# + TC4 chg, Cy0012 = TC12 dchg + TC13 chg) 정상화 위해 rendering
# 차원에서 minor 로 처리. Chg major (예: Cy0023 = chg 0→100% + dchg
# 100→0% within-TC envelope) 는 fallthrough 보존.
_render_major = _is_major
if _is_major and _pair_enabled and _direction == 'Dchg':
    _render_major = False
if 'Condition' in p.columns and not _render_major:
    ...
```

추가로 sub_color (dQdV/Crate/Temp axes) 도 `_render_major` 사용으로 일관성 보장 (L27758-27759).

## 수정 2 — Phase canonical anchor (SOC 시작점 정렬)

**진단**: `_apply_hysteresis_soc_offsets` 의 cumul anchor 가 절대 cell SOC 좌표 산출 시,
CC-CV 잉여 (CC 후 CV 단계에서 ChgCap 추가 누적, +0.05~0.10) 가 anchor cumul 에 흡수되어
다음 TC 의 절대 SOC 가 약간 drift. 결과적으로:
- TC 3-12 dchg 의 첫 row SOC 가 정확히 1.0 이 아니라 1.05 또는 0.97 등으로 어긋남
- TC 14-23 chg 의 첫 row SOC 가 정확히 0.0 이 아니라 0.03 등으로 어긋남

**Fix**: 신규 메서드 `_apply_hysteresis_phase_canonical_anchor` 가
`_apply_hysteresis_soc_offsets` 직후 호출되어 hyst label 별 추가 shift 적용:

```python
# Dchg 그룹: dchg phase 첫 row → SOC 1.0
if direction == 'Dchg':
    dchg_first = df[df['Condition'] == 2]['SOC'].iloc[0]
    delta = 1.0 - dchg_first
# Chg 그룹: chg phase 첫 row → SOC 0.0
elif direction == 'Chg':
    chg_first = df[df['Condition'] == 1]['SOC'].iloc[0]
    delta = 0.0 - chg_first
df['SOC'] = df['SOC'] + delta  # 전체 df shift
```

**효과**:
- 모든 Dchg TC 의 dchg arc 가 정확히 SOC 1.0 line 에서 출발 (closed loop top 정렬)
- 모든 Chg TC 의 chg arc 가 정확히 SOC 0.0 line 에서 출발
- CC-CV 잉여 와 cumul drift 가 per-TC 보정되어 누적 안 됨
- Hyst label 미식별 TC (RPT, GITT 등) 는 변경 없음 (기존 absolute SOC 유지)

**Closure 보존**:
- TC N 의 chg phase 도 함께 shift → chg end (= dchg start) 도 SOC 1.0 정렬
- TC (N+1) 도 자체적으로 normalize → cross-TC pair 의 chg arc end 가 1.0
- TC N dchg end (= 1.0 - depth%) ≈ TC (N+1) chg start (= 1.0 - chg_amount) → closure
- 단, raw 데이터의 chg amount 가 정확하지 않으면 약간의 gap 발생 가능 (CC-CV 변동성)

**Pair fallback 동기화** (L21164):

`_profile_render_loop` 에서 TC N+1 fallback fetch 시, 기존 `_hyst_soc_offset_maps` 의 absolute
shift 적용 후 추가로 `_compute_hysteresis_phase_canonical_delta` 호출하여 main path 와
일관성 보장. `self._hyst_phase_label_maps` 가 main path 산출 시 캐시됨.

## 수정 3 — Dchg endpoint scaling

**진단**: Fix 2 의 단순 shift 는 phase **첫 row** 만 canonical anchor 에 정렬. **마지막 row** 가 canonical end 와 일치하는지는 raw 데이터의 chg/dchg amount 에 의존:
- Dchg group: dchg 마지막 row = `chg_end_canonical - dchg_amount`. dchg amount 가 깊이 (depth%) 와 일치하면 자동 정렬, 불일치 시 drift.
- Chg group: dchg 마지막 row = `chg_amount - dchg_amount`. 일반 protocol 에서 chg amount > dchg amount (CC-CV 잉여) → dchg 끝점 > 0.

**Fix**: 신규 staticmethod `_scale_hysteresis_dchg_phase_to_canonical_end` — dchg phase 의 **마지막 row** 만 linear scaling 으로 canonical end 에 끌어당김:

```python
# dchg target_last 산출
if direction == 'Dchg':
    target_last = 1.0 - depth_pct / 100.0  # 예: depth 20% → 0.8
elif direction == 'Chg':
    target_last = 0.0  # within-TC return-to-start

# dchg phase 만 linear scale (첫 row 보존, 마지막 row 만 이동)
scale = (target_last - s_first) / (s_last - s_first)
df.loc[dchg_idx, 'SOC'] = s_first + (df['SOC'] - s_first) * scale
```

**안전 한도**: scaling 비율 (`target_range / raw_range`) 이 ±20% 초과 시 skip — 데이터 이상 신호로 간주, 무리한 변형 회피. scale ≈ 1.0 (변화 없음) 시도 skip.

**Side effect**: chg phase 는 보존하므로 cross-TC 페어링의 closure 가 약간 어긋날 수 있음 (보통 < 1% SOC, 시각적 무시 가능).

## 수정 4 — dQdV CV 마스킹 활성화

**진단**: 사용자 보고 "dQdV 산정 시, 충전의 CV 구간은 제외하자". Hysteresis preset 의 `origin_compat=True` 가 `_unified_calculate_dqdv` 의 CV 마스킹 (|ΔV|<2mV 영역의 dQdV NaN 처리) 을 OFF 시킴 — CV plateau 의 분모 0 으로 인해 inf/NaN spike 가 dQdV 플롯에 노이즈로 출력.

**Fix**: hysteresis preset 의 `origin_compat = False` 로 변경 (L27401).

```python
# Before
origin_compat = is_hysteresis_mode  # 히스테리시스 모드 시 True (CV 마스킹 OFF)
# After
origin_compat = False  # 사용자 요청: CV 마스킹 ON (CV 영역 dQdV NaN 처리)
```

**영향**: Excel 골든 reference (origin Excel 에서 CV 영역 dQdV 가 inf/NaN) 와의 numerical 일치성은 일부 손상. 사용자 분석 의도 (clean dQdV 시각) 우선.

## 수정 5 — 사이클 분류 envelope merge + 라벨 변경

**진단**:
- `_classify_loop_group` 의 HYSTERESIS_DCHG 룰 (L8017): `N==1 and end_condition.type==2048 (DOD%)` 만 인식
- 사용자 protocol 의 TC 12 (depth 100% Dchg envelope) 는 voltage cutoff (V_min) 으로 정의 → RPT 분기로 fall-through
- 사이클 바 popover: "사이클 3~11 (9cy)" 으로 표시 — 사용자 인지의 "10cy hyst 그룹" 과 불일치

**Fix**: `_build_loop_group_info` (L8169) 에 신규 post-pass `_merge_hysteresis_envelopes` 추가:

```python
# 각 hyst 그룹의 i+1 (next) 위치가 RPT/CHG_DCHG + loop_count==1 + body 호환
# (chg+dchg, no short pulse) 이면 envelope 후보 → hyst category 로 reclassify.
# ORIGINAL result 기준으로만 후보 수집 → chain merge 방지 (mid-RPT 보호).
for i, g in enumerate(result):
    if g['category'] not in ('HYSTERESIS_DCHG', 'HYSTERESIS_CHG'):
        continue
    if i + 1 < len(result):
        next_g = result[i + 1]
        if (next_g['category'] in ('RPT', 'CHG_DCHG')
                and next_g.get('loop_count') == 1
                and _is_compatible_with_hyst_envelope(next_g)):
            merges.append((i + 1, g['category']))

for idx, cat in merges:
    result[idx]['category'] = cat
```

**중간 RPT 보호**: original result 기준으로만 후보 수집하므로, TC 13 (mid-RPT, 흡수 후 TC 12 가 HYSTERESIS_DCHG 가 되더라도) 은 흡수되지 않음 — 원본 분류상 TC 13 의 next 가 HYSTERESIS_CHG 이고 prev 가 RPT 이므로 hyst 그룹 next 위치 조건 불만족.

**라벨 명칭 변경**:

| 구 | 신 (260503) | 의미 |
|---|---|---|
| `히스테리시스(방전)` | `히스테리시스(방충전)` | TC N dchg + TC N+1 chg = 방→충 cross-TC 페어링 |
| `히스테리시스(충전)` | `히스테리시스(충방전)` | TC N chg + TC N dchg = 충→방 within-TC 페어링 |
| `히스테리시스 (방전 경로)` | `방충전 히스테리시스` | popover 표시명 |
| `히스테리시스 (충전 경로)` | `충방전 히스테리시스` | popover 표시명 |

`_compute_tc_hysteresis_labels` 의 keyword 매칭 (L1006-1019) 도 신 명칭 우선 + 구 alias 호환 처리:

```python
if '히스테리시스' in cat:
    if '방충전' in cat:    tc_to_hyst_dir[tc_int] = 'Dchg'  # 신
    elif '충방전' in cat:  tc_to_hyst_dir[tc_int] = 'Chg'   # 신
    elif '방전' in cat:    tc_to_hyst_dir[tc_int] = 'Dchg'  # 구 alias
    elif '충전' in cat:    tc_to_hyst_dir[tc_int] = 'Chg'   # 구 alias
```

## 수정 6 — `_calc_soc` 의 SOC = 1 − DOD 일관성 (Fix A)

**진단**: `_calc_soc` (L2428~) 가 charge/discharge scope 에서 axis_mode 무시:
```python
if data_scope == "charge":
    return df["ChgCap"]   # axis_mode 무관, 항상 0→1
if data_scope == "discharge":
    return df["DchgCap"]  # axis_mode 무관, 항상 0→1
```

→ 충전 분석 + DOD axis 시: X = ChgCap (0→1) 인데 라벨 "DOD" → 의미 충돌
→ 방전 분석 + SOC axis 시: X = DchgCap (0→1) 인데 라벨 "SOC" → 의미 충돌
→ SOC = 1 − DOD 깨뜨림.

**Fix**: `_calc_soc` 의 charge/discharge 분기에 axis_mode 추가:

```python
if data_scope == "charge":
    if axis_mode == "dod":
        return 1.0 - df["ChgCap"]  # DOD 1 → 0
    return df["ChgCap"]            # SOC 0 → 1 (자연 anchor)
if data_scope == "discharge":
    if axis_mode == "soc":
        return 1.0 - df["DchgCap"] # SOC 1 → 0
    return df["DchgCap"]           # DOD 0 → 1 (자연 anchor)
```

**자연 anchor 의 X 시작점 = 0 보존**:
- 충전 분석 + SOC: X 시작 = 0 ✓ (oper1.py 동일)
- 방전 분석 + DOD: X 시작 = 0 ✓ (oper1.py 동일)
- 충전 분석 + DOD: X 시작 = 1 (= 1 − 0)
- 방전 분석 + SOC: X 시작 = 1 (= 1 − 0)

**렌더 + Excel 출력 동기화**: `_plot_one` (legacy_mode "chg" / "dchg") 의 X축 라벨
및 Excel 헤더가 axis_mode 에 따라 동적 결정:

```python
_chg_axis_label  = "DOD" if options['axis_mode'] == 'dod' else "SOC"
_dchg_axis_label = "SOC" if options['axis_mode'] == 'soc' else "DOD"
```

`_fallback` 함수도 `axis_mode=options.get("axis_mode", ...)` 전달.

**Hysteresis 분석 (preset 3) 영향 없음**: `_calc_soc` 의 cycle scope 분기 (L2447~)
및 `_apply_hysteresis_soc_offsets` (Layer 2+2-α+2-β) 는 변경 없음. 사용자 명시
("Fix B, C 는 기존 hysteresis 분석 구조 유지").

## 호출 순서

```
unified_profile_confirm_button():
  1. _apply_hysteresis_soc_offsets(...)              # Layer 2: absolute cell SOC anchor
  2. _apply_hysteresis_phase_canonical_anchor(...)   # Layer 2-α: 첫 row shift (Fix 2)
                                                     # Layer 2-β: dchg endpoint scaling (Fix 3)
  3. _build_hysteresis_long_dataframe(...)           # long-format 시트
  4. _hyst_labels = _compute_tc_hysteresis_labels(...)
  5. _profile_render_loop(...)                       # render
       - L21164: pair fallback fetch 시 동일 anchor + scaling 동기 (Fix 2 + Fix 3)
       - L27659: Fix 1 (_render_major) 가드 → segment 분할 + 페어링
       - dQdV: origin_compat=False 로 CV 영역 마스킹 (Fix 4)
       - legacy_mode "chg"/"dchg": axis_mode 에 따라 X 데이터/라벨/헤더 (Fix 6)

_extract_pne_sch_pattern_summary():
  → _build_loop_group_info(): post-pass _merge_hysteresis_envelopes (Fix 5)
  → 사이클 바 popover 가 "방충전 히스테리시스 (TC3-12)" 로 표시 (Fix 5 라벨)
```

## 영향 범위 (Trace)

| TC | direction | `_is_major` | `_render_major` | 분기 | 결과 |
|---:|---|---|---|---|---|
| 3 | Dchg | True | **False** | segment 분할 + cross-TC | TC3 dchg + TC4 chg = **ΔDOD 10% mini-loop** ✓ |
| 4-11 | Dchg | False | False | (변경 없음) | 기존 cross-TC 페어링 ✓ |
| 12 | Dchg | True | **False** | segment 분할 + cross-TC | TC12 dchg + TC13 chg = **ΔDOD 100% envelope** ✓ |
| 14-22 | Chg | False | False | (변경 없음) | 기존 cross-TC 페어링 ✓ |
| 23 | Chg | True | True | major fallthrough | TC23 chg + TC23 dchg = ΔSOC 100% within-TC envelope ✓ |

**핵심**: Dchg + 페어링 활성 인 cycle 만 영향. Chg major (TC 23) 는 fallthrough 그대로 보존.

## 색상 일관성

L27709 의 segment 색상 결정:
```python
_color, _lw, _alpha = _get_profile_color('chg_dchg', _cyc_idx, _n_cyc,
    condition=_cond, is_major=False)
```

`is_major=False` 강제 → rainbow stop 매핑 (`_HYST_RAINBOW_STOPS`, cyc_idx 기반).

| Cycle | rank | color |
|---|---|---|
| Cy0012 (depth 100%, rank 0) | 0 | `#000000` (black) |
| Cy0011 (depth 90%, rank 1) | 1 | `#4D4DB2` (보라) |
| ... | ... | rainbow |
| Cy0003 (depth 10%, rank 9) | 9 | `#FF3333` (red) |

Fix 이전: TC 3, TC 12 가 major 분기로 떨어져 색상이 `#333333` (다크 그레이) 일관성 없음.
Fix 이후: TC 12 = `#000000` (black, rank 0), TC 3 = `#FF3333` (red, rank 9) — `260420_hysteresis_preset_cv_and_rainbow_colors.md` 의 의도와 일치.

## 회귀 검증

검증 스크립트: `tools/test_code/hysteresis_render_decision_validator.py`

8-step 검증 (49개 케이스 PASS):

1. **Truth table** — `_render_major` 결정의 8가지 입력 조합. **8/8 PASS**.
2. **실제 hyst 경로 분석** — `data/exp_data/성능_hysteresis/` boundary cycle 식별 (worktree 환경에서 SKIP).
3. **Simulation** — 사용자 protocol (TC 3-12 + TC 14-23) 12개 cycle. **12/12 PASS**.
4. **Phase canonical delta** — `_compute_hysteresis_phase_canonical_delta` 8가지 입력. **8/8 PASS**.
5. **Dchg endpoint scaling** — `_scale_hysteresis_dchg_phase_to_canonical_end` 7가지 케이스. **7/7 PASS**.
6. **dQdV CV 마스킹** — `_unified_calculate_dqdv` 의 origin_compat=False 시 CV 영역 NaN 처리 검증. **2/2 PASS**.
7. **Envelope merge** — `_merge_hysteresis_envelopes` 6가지 시나리오. **6/6 PASS**.
8. **`_calc_soc` axis_mode (Fix A)** — charge×SOC, charge×DOD, discharge×SOC, discharge×DOD 4가지 + SOC=1−DOD 관계 검증 2가지. **6/6 PASS**.

```bash
python tools/test_code/hysteresis_render_decision_validator.py
```

## 사용자 검증 가이드 (사내 PC)

**Fix 1 (Cy0003/Cy0012 페어링)**:
1. proto 실행 → TC 3-12 hyst 데이터 로드
2. 프리셋 콤보 → **히스테리시스** 선택 (TC 페어링 자동 ON)
3. 사이클 범위 = `3-12`, **Profile 분석** 실행
4. 결과 그래프에서 **Cy0003** 과 **Cy0012** 단독 선택 확인:
   - Cy0003: SOC 90~100% 의 작은 closed loop (depth 10%, red 색상)
   - Cy0012: SOC 0~100% 의 큰 closed loop (depth 100% envelope, black 색상)
5. Cy0004~Cy0011 의 모양 변동 없음 확인 (rainbow 색상, 점진적 폭)

**Fix 2 (SOC 시작점 정렬)**:
6. TC 3-12 통합 fan 그래프에서 모든 dchg arc 가 **SOC = 1.0 line 에 정확히 정렬** 확인
7. TC 14-23 통합 fan 그래프에서 모든 chg arc 가 **SOC = 0.0 line 에 정확히 정렬** 확인
8. CC-CV 잉여 가 큰 protocol (예: Si25P) 에서도 dchg start 가 SOC 1.0 으로 정렬되는지 확인
9. `_perf_logger` 출력 확인 — `[hysteresis] phase canonical anchor 적용: shift=N개, dchg-scale=M개 cycle`

**Fix 3 (Dchg endpoint scaling)**:
10. **Cy0012**: dchg arc 의 시작점 (SOC 1.0) AND 끝점 (SOC 0.0) 모두 정확히 정렬 확인
11. **TC 14-23**: 각 cycle 의 dchg arc 끝점이 정확히 SOC 0.0 line 에 도달 확인
12. 큰 drift (>20%) 시 scaling skip + warning 로그 출력 확인 — 데이터 이상 신호 시 보호

**Fix 4 (dQdV CV 마스킹)**:
13. dQdV 플롯에서 충전 CV plateau 영역 (V ≈ 4.5V 근처) 의 noise spike 가 사라졌는지 확인
14. CC 영역의 정상 dQdV 곡선은 보존 확인
15. 엑셀 골든 reference 와 numerical 차이 발생 가능 — CV 영역만 NaN 처리, CC 영역 일치

**Fix 5 (사이클 분류 + 라벨)**:
16. 사이클 바 popover hover — TC 3-12 hyst 그룹이 **"방충전 히스테리시스 (TC 3~12, 10cy)"** 로 표시 (이전 "히스테리시스 (방전 경로) 9cy" 에서 변경)
17. TC 14-23 hyst 그룹이 **"충방전 히스테리시스 (TC 14~23, 10cy)"** 로 표시
18. mid-RPT (TC 13) 는 RPT 로 별도 분류되어 hyst 그룹 사이에 분리되는지 확인
19. SOC 별 DCIR / GITT 등 다른 protocol 에서 envelope merge 가 잘못 작동하지 않는지 회귀 검증 (`tools/test_code/hysteresis_render_decision_validator.py` Step 7)

**Fix 6 (preset 4/5 axis_mode)**:
20. **충전 분석** + SOC axis: chg curve 가 X 0 → 1 (왼쪽→오른쪽), 라벨 "SOC", Excel 컬럼 "SOC" — oper1.py 동일 ✓
21. **충전 분석** + DOD axis: chg curve 가 X 1 → 0 (오른쪽→왼쪽 mirror), 라벨 "DOD", Excel 컬럼 "DOD" (Fix 6 신규)
22. **방전 분석** + SOC axis: dchg curve 가 X 1 → 0 (오른쪽→왼쪽), 라벨 "SOC", Excel 컬럼 "SOC" (Fix 6 신규) — 사용자 image 2 와 일치
23. **방전 분석** + DOD axis: dchg curve 가 X 0 → 1 (왼쪽→오른쪽), 라벨 "DOD", Excel 컬럼 "DOD" — oper1.py 동일, 사용자 image 1 과 일치 ✓
24. **Hyst 분석 (preset 3)**: 변동 없음 — 기존 절대 cell SOC 좌표 보존 (Fix B/C 미적용)

**Regression 점검**:
10. 사이클 범위 = `14-23` → preset 3 + TC 페어링: closed loop fan 동작 (chg arc anchored at 0.0)
11. TC 23 단독 → ΔSOC 100% within-TC envelope 동작 보존
12. preset 4 (충전 분석) / preset 5 (방전 분석) — 변동 없음 (랩장님 원본 등가, phase-relative anchor 그대로)
13. preset 1/2 (전체/dQdV) — hysteresis 모드 아니므로 변동 없음

## 관련 변경로그 / wiki

- `260428_hysteresis_tc_pairing.md` — TC 페어링 도입 changelog (본 fix 의 baseline)
- `260428_hysteresis_depth_labels_and_color_rank.md` — depth_pct 라벨링 + rainbow rank
- `260429_fix_hysteresis_soc_offset_anchor_shift_and_dqdv_keyerror.md` — SOC offset anchor 수정
- `wiki/40_work_log/260429_hysteresis_unified_flow.md` — 통합 flow + long-format 시트
- `wiki/11_profile_analysis/260420_hysteresis_major_threshold.md` — major 임계값 0.5→0.98 상향
- `wiki/11_profile_analysis/260420_hysteresis_preset_cv_and_rainbow_colors.md` — rainbow 색상 정의
- `wiki/11_profile_analysis/260503_anchor_layer_separation.md` — anchor layer 분리 정의 (신규)

## 사용자 protocol 의 anchor 정의 정리

랩장님 원본 (`BAK/260204_sy_origin/BatteryDataTool 260204.py` L1366-1477) 의 `pne_chg_Profile_data` / `pne_dchg_Profile_data` 는 **phase-relative anchor**:
- 충전 분석: SOC 컬럼 = Chgcap 정규화 누적값 (chg phase 시작점 = SOC 0)
- 방전 분석: SOC 컬럼 = Dchgcap 정규화 누적값 (dchg phase 시작점 = SOC 0 = DOD 0 = cell SOC 100%)

현재 BDT 의 preset 4 (충전 분석) / preset 5 (방전 분석) 는 이 정의와 등가.

Hysteresis preset 3 은 **절대 cell SOC anchor** 로 cross-TC 페어링 적합한 별도 layer.

자세한 내용은 `wiki/11_profile_analysis/260503_anchor_layer_separation.md` 참고.
