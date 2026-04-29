---
title: "프로파일 분석 — 현재 vs Target 격차"
aliases:
  - Profile Gap Analysis
  - Current vs Target Gap
tags:
  - profile-analysis
  - spec
  - gap-analysis
  - phase-plan
type: spec
status: draft
related:
  - "[[260428_profile_4modes_spec]]"
  - "[[260428_profile_view_color_spec]]"
  - "[[hub_unified_profile]]"
  - "[[260420_profile_axis_dod_option]]"
  - "[[260418_profile_options_redesign]]"
created: 2026-04-28
updated: 2026-04-28
---

# 프로파일 분석 — 현재 vs Target 격차

> [!abstract] 요약
> [[260428_profile_4modes_spec]]의 4종 분석 모델과 현재 코드의 옵션 조합 모델 사이 격차를 5개 결함(G1~G5)으로 정리. 각 결함의 위치·target·우선순위·구현 phase 제안.

> 상위 → [[hub_unified_profile]] · 4종 분석 → [[260428_profile_4modes_spec]] · 색상 → [[260428_profile_view_color_spec]]

---

## 1. 매핑 표 — 사용자 의도 → 현재 코드 경로

| 사용자 의도 (4종 분석) | 현재 옵션 조합 | legacy_mode | 실행 함수 |
|---|---|---|---|
| 방전 분석 (시간) | scope=discharge, axis=time, overlap=split | `dchg` | `_profile_render_loop` (L26497+) |
| 방전 분석 (DOD) | scope=discharge, axis=dod, overlap=split | `dchg` | 동상 |
| 충전 분석 (시간) | scope=charge, axis=time, overlap=split | `chg` | `_profile_render_loop` (L26424+) |
| 충전 분석 (SOC) | scope=charge, axis=soc, overlap=split | `chg` | 동상 |
| 전체 프로파일 (시간) | scope=cycle, axis=time, overlap=continuous | `continue` | `_profile_render_loop` (L26311+) |
| 히스테리시스 (SOC) | scope=cycle, axis=soc, overlap=connected, hyst_pair=ON | `cycle_soc` (히스) | L26582+ |
| 히스테리시스 (DOD) | scope=cycle, axis=dod, overlap=connected, hyst_pair=ON | `cycle_soc` (히스) | L26582+ |
| (기타) 사이클+SOC+분리 | scope=cycle, axis=soc, overlap=split | `cycle_soc` (비히스) | L26725+ |
| (기타) 사이클+DOD+분리 | scope=cycle, axis=dod, overlap=split | `cycle_soc` (비히스) | L26725+ ⚠ |

---

## 2. 결함 / 격차 (G1~G5)

### G1 — 사이클+DOD plot 좌우 분리 좌표계 🔴

| 항목 | 값 |
|---|---|
| **현상** | DOD 모드에서 충전을 X=-1~0 (음수), 방전을 X=0~1 (양수)로 좌우 분리 plot. 사용자 보고 "이상함" — 시각 결함 (X 라벨 가독성, dVdQ 끝점 ±5 스파이크) 동반. |
| **위치** | `_calc_soc()` L2388-2402 (connected) + L2423-2440 (split) |
| **현재 코드** | `dod[chg_mask] = -df.loc[chg_mask, "ChgCap"]` — 충전을 음수 영역으로 mirror |
| **Target** | DOD/SOC 모두 0~1 양수 — 데이터 동일, X축 라벨만 "DOD"/"SOC" 차이 |
| **사유** | 좌우 분리 좌표계는 이전 [[260420_profile_axis_dod_option]] 시점 설계였으나, (a) 사용자 mental model 불일치, (b) dVdQ 스파이크, (c) 라벨 가독성, (d) 히스테리시스 닫힌 루프 부자연스러움 — 4개 사유로 재검토 후 폐기 결정 |
| **우선순위** | 🔴 즉시 (사용자 보고 버그) |
| **Phase** | Phase 2 |

#### 수정 가이드

```python
# _calc_soc() L2388-2402 (현재 — connected 분기)
if axis_mode == "dod" and overlap == "connected":
    if "Condition" in df.columns:
        dod = pd.Series(np.nan, index=df.index)
        chg_mask = df["Condition"] == 1
        dchg_mask = df["Condition"] == 2
        if chg_mask.any():
            dod[chg_mask] = -df.loc[chg_mask, "ChgCap"]   # ← 음수 (제거)
        if dchg_mask.any():
            dod[dchg_mask] = df.loc[dchg_mask, "DchgCap"]
        return dod.ffill()
    return df["DchgCap"] - df["ChgCap"]

# Target — SOC connected 분기와 통합
if overlap == "connected" and axis_mode in ("soc", "dod"):
    # 닫힌 루프: 충전 0→peak, 방전 peak→0 (둘 다 0~1 양수). 라벨만 SOC/DOD 차이.
    if "Condition" in df.columns:
        soc = pd.Series(np.nan, index=df.index)
        for cyc in df["Cycle"].unique():
            cyc_mask = df["Cycle"] == cyc
            if not cyc_mask.any():
                continue
            chg_mask = cyc_mask & (df["Condition"] == 1)
            dchg_mask = cyc_mask & (df["Condition"] == 2)
            if chg_mask.any():
                soc[chg_mask] = df.loc[chg_mask, "ChgCap"]
            peak = (df.loc[chg_mask, "ChgCap"].max()
                    if chg_mask.any() else 1.0)
            if dchg_mask.any():
                soc[dchg_mask] = peak - df.loc[dchg_mask, "DchgCap"]
        return soc.ffill()
    return df["ChgCap"] - df["DchgCap"]

# split 분기 (L2423-2440) — axis_mode 분기 제거
if axis_mode in ("soc", "dod"):
    if "Condition" in df.columns:
        soc = pd.Series(np.nan, index=df.index)
        chg_mask = df["Condition"] == 1
        dchg_mask = df["Condition"] == 2
        rest_mask = df["Condition"] == 3
        soc[chg_mask] = df.loc[chg_mask, "ChgCap"]    # 항상 양수
        soc[dchg_mask] = df.loc[dchg_mask, "DchgCap"]
        if rest_mask.any():
            soc[rest_mask] = np.nan
            soc = soc.ffill()
        return soc
    return df["ChgCap"] - df["DchgCap"]
```

---

### G2 — 비히스테리시스(split) 분기 DOD 미지원 🔴

| 항목 | 값 |
|---|---|
| **현상** | `cycle_soc` legacy_mode의 비히스테리시스(else) 분기에서 X축 라벨 `"SOC"`, X 범위 `-0.1, 1.2` 하드코딩. DOD 모드 선택해도 라벨이 SOC로 표시됨. |
| **위치** | `cycle_soc` plot 분기 L26725-26794 (else 블록, 10개 `graph_profile()` 호출) |
| **현재 코드** | `graph_profile(_seg.SOC, _seg.Vol, ax1, -0.1, 1.2, 0.1, ..., "SOC", "Voltage(V)", _seg_lbl)` |
| **Target** | `_axis_label`, `_x_lo`, `_x_hi` 변수 사용 (히스테리시스 분기와 동일 패턴) |
| **사유** | 히스테리시스 분기(L26582+)는 동적 라벨/범위 사용. 비히스테리시스도 동일하게 통일. |
| **우선순위** | 🔴 즉시 (DOD 옵션의 의미 일관성) |
| **Phase** | Phase 2 |

#### 수정 가이드

L26725-26794 의 모든 `graph_profile()` 호출에서:
```python
# Before
_a1 = graph_profile(_seg.SOC, _seg.Vol, ax1,
    -0.1, 1.2, 0.1, ..., "SOC", "Voltage(V)", _seg_lbl)

# After
_a1 = graph_profile(_seg.SOC, _seg.Vol, ax1,
    _x_lo, _x_hi, 0.1, ..., _axis_label, "Voltage(V)", _seg_lbl)
```

`_x_lo`, `_x_hi`, `_axis_label`은 히스테리시스 분기에서 정의된 변수 (L26570-26573) — 비히스테리시스 분기에 진입하기 전에 이미 정의되어 있어 그대로 사용 가능. 단 G1 적용 후에는 `_x_lo, _x_hi = (-0.1, 1.2)` 통일.

---

### G3 — TC 페어링 수동 체크박스 🟡

| 항목 | 값 |
|---|---|
| **현상** | 히스테리시스 페어 루프를 보려면 `profile_hyst_pair_chk` 체크박스 수동 ON 필요. 사용자가 매번 토글. |
| **위치** | `profile_hyst_pair_chk` UI 위젯 L11945, `_hyst_pair_state` 처리 L26601+ |
| **현재 코드** | 사용자 명시 ON에만 `_pair_enabled = True` |
| **Target** | 사이클+연결+(SOC|DOD) 조합 시 자동 ON. 체크박스 UI 제거. |
| **사유** | 히스테리시스 분석의 본질이 페어 루프 — 별도 옵션이 아닌 분석의 기본 동작 ([[260428_profile_4modes_spec]] §2.4) |
| **우선순위** | 🟡 중간 (UX 개선) |
| **Phase** | Phase 3 |

#### 수정 가이드

```python
# _read_profile_options() 또는 페어링 활성 결정 위치
hyst_pair = (
    options.get('data_scope') == 'cycle' and
    options.get('overlap') == 'connected' and
    options.get('axis_mode') in ('soc', 'dod')
)
# UI 체크박스 제거 (혹은 'override' 옵션으로 강제 OFF 가능)
```

UI 위젯 `profile_hyst_pair_chk` 제거 + 관련 시그널 정리.

---

### G4 — UI에 "분석 종류" 1차 분류 부재 🟢

| 항목 | 값 |
|---|---|
| **현상** | 옵션 조합형 UI — 사용자가 데이터 범위 + X축 + overlap을 각각 선택. 4종 분석 종류라는 1차 분류가 UI에 노출되지 않음. |
| **위치** | UI: `_data_scope_groupbox` L11825+, profile_axis_* L11891+, profile_ovlp_* L11859+ |
| **현재 코드** | 옵션 dict `{data_scope, axis_mode, overlap, ...}` |
| **Target** | 분석 종류 라디오 그룹 추가 (방전/충전/전체/히스테리시스 4개), 분석 종류 선택 시 X축·overlap 자동 활성/비활성 |
| **사유** | 사용자 mental model 일치 + 잘못된 옵션 조합 차단 |
| **우선순위** | 🟢 낮음 (호환성 영향 큼, 후속 phase) |
| **Phase** | Phase 4 |

#### 수정 가이드

```python
# 새 위젯 (가이드)
_analysis_seg, _analysis_btns = self._make_seg_group(
    ["방전", "충전", "전체 프로파일", "히스테리시스"], ..., checked_idx=2)
self.profile_analysis_dchg = _analysis_btns[0]
self.profile_analysis_chg = _analysis_btns[1]
self.profile_analysis_full = _analysis_btns[2]
self.profile_analysis_hyst = _analysis_btns[3]

# _read_profile_options()에 analysis_mode 추가
analysis_map = {0: "discharge", 1: "charge", 2: "full", 3: "hysteresis"}
analysis_mode = analysis_map.get(self.profile_analysis_group.checkedId(), "full")

# 분석 종류 → 옵션 자동 매핑 (인덱스: spec §3 매트릭스)
if analysis_mode == "discharge":
    data_scope, overlap = "discharge", "split"
    axis_options = {"time", "dod"}
elif analysis_mode == "charge":
    data_scope, overlap = "charge", "split"
    axis_options = {"time", "soc"}
elif analysis_mode == "full":
    data_scope, overlap = "cycle", "continuous"
    axis_options = {"time"}
elif analysis_mode == "hysteresis":
    data_scope, overlap = "cycle", "connected"
    axis_options = {"soc", "dod"}
    hyst_pair = True  # G3 자동 활성

# 활성/비활성 X축 라디오 자동 제어
self.profile_axis_time.setEnabled("time" in axis_options)
self.profile_axis_soc.setEnabled("soc" in axis_options)
self.profile_axis_dod.setEnabled("dod" in axis_options)
```

기존 `data_scope` / `overlap` 라디오는 디버그 모드에서만 노출하거나 완전 제거.

---

### G5 — dQdV 전환 충전 모드만 지원 🟢

| 항목 | 값 |
|---|---|
| **현상** | `chk_dqdv` 체크박스가 충전(`chg`) 모드에서만 X/Y axis swap. 방전·히스테리시스에서는 동작 없음. |
| **위치** | `chk_dqdv` UI L12065, 처리 분기 L26442-26450 (충전 분기 내부) |
| **현재 코드** | `if self.chk_dqdv.isChecked(): graph_profile(p.Vol, p.dQdV, ...) else: graph_profile(p.dQdV, p.Vol, ...)` — `chg` legacy_mode 한정 |
| **Target** | 방전/히스테리시스 분석에도 동일 swap 적용 |
| **사유** | dV/dQ feature 분석은 방전 데이터에서도 유용. 히스테리시스에서 voltage 축 vs SOC 축 toggle 분석 가능. |
| **우선순위** | 🟢 낮음 (기능 확장) |
| **Phase** | Phase 5 |

---

### G6 — 전체통합 + 다중 경로 시 plot line 색상 단색화 🔴

| 항목 | 값 |
|---|---|
| **현상** | 전체통합(`AllProfile`) + 다중 경로(N>1) 분석 시 모든 plot line이 동일 색상(남색 #3C5488 베이스 가변 농도)으로 표시. 우측 path colorbar는 정상 다단계로 보이지만 line과 매칭 안 됨. |
| **위치** | (A) 후처리 색상 루프 `_get_profile_color()` 호출 L20744-20749, (B) 모든 `_plot_one()` 콜백 — `_path_idx_tag` 부재 (chg L26424+, dchg L26497+, cycle_soc L26567+, step L26399+, continue L26820+), (C) 후처리 루프 path 매핑 부재 L20693-20728 |
| **현재 코드** | `_resolve_profile_color_mode()`가 'group' 반환 ✓. 그러나 `_get_profile_color('group', ci, n_total, ...)` 호출 시 **`group_idx` 인자 누락** → default `0` → `group_bases[0]=(60,84,136)` 남색 베이스만 사용. cycle_idx 농도 차이만 있어 사실상 단색. |
| **Target** | 5개 `_plot_one()` 모두 `_path_idx_tag = path_idx` 부착 + 후처리 루프에서 `_line_path_map` 구성 + `_get_profile_color()`에 `group_idx=path_idx` 전달 |
| **사유** | (1) 사용자가 다중 경로 분석을 일상적으로 사용 (스크린샷 21경로), (2) "Path (N)" colorbar는 컬러맵을 별도 생성하지만 line은 무관, (3) architecture-level 결함이라 다음 phase에서 통합 정리 필요 |
| **우선순위** | 🔴 즉시 (다중 경로 분석 결과 시각 무의미) |
| **Phase** | Phase 2.5 |

#### 흐름 (확정)

```
1. _resolve_profile_color_mode(view_mode='all', n_folders=N>1, ...)
   → 'group' 반환  ✓ 정상 [proto_.py:3832-3833]

2. legacy_mode 분기 _plot_one() (5종 공통)
   → _artists 에 _cycle_id_tag 만 부착  ✗ _path_idx_tag 부재

3. 후처리 색상 루프 [proto_.py:20693-20728]
   → _line_cyc_map만 구성  ✗ _line_path_map 부재

4. _get_profile_color('group', ci, n_total, condition=..., is_first=..., is_last=...)
   → group_idx 인자 누락 → default 0  [proto_.py:20744-20749]

5. _get_profile_color() group 분기 [proto_.py:3990-4004]
   → group_bases[0 % 4] = 남색 (60, 84, 136)
   → scale = 0.4 + 0.6 × (cycle_idx / max(n−1, 1))
   → 모든 line이 남색 베이스, cycle_idx 농도만 차이
```

#### 수정 가이드 (요약, Phase 2.5에서 구체화)

```python
# A) 후처리 색상 루프에 path 매핑 추가 [L20693-20728 부근]
_explicit_path_ids = [getattr(L, '_path_idx_tag', None) for L in _non_rest]
_line_path_map = {}
if any(x is not None for x in _explicit_path_ids):
    for line, pid in zip(_non_rest, _explicit_path_ids):
        _line_path_map[id(line)] = int(pid) if pid is not None else 0

# B) _get_profile_color() 호출에 group_idx 전달 [L20744]
_pi = _line_path_map.get(id(line), 0)
_c, _lw, _a = _get_profile_color(
    color_mode, ci, _n_cycles_detected,
    condition=_cond,
    group_idx=_pi,         # ← 추가
    is_first=_is_first,
    is_last=_is_last,
)

# C) 5개 _plot_one() 콜백에 _path_idx_tag 부착
# 옵션 1: render_loop 시그니처 확장 — _plot_one 호출 시 path_idx 전달
# 옵션 2: _profile_render_loop 후처리에서 일괄 부착 (FolderBase → path_idx 매핑)
```

옵션 2가 변경 범위 작아 권장 — `_profile_render_loop()` 내부에서 `all_data_folder` 인덱스로 자동 매핑.

---

### 추가 — GITT/OCV/CCV 도출 (전체 프로파일 advanced)

[[260428_profile_4modes_spec]] §2.3 명시. 별도 결함이 아닌 신규 기능이지만, 4종 분석 모델 완성도를 위해 Phase 5에 함께 검토.

| 항목 | 값 |
|---|---|
| **GITT** | 펄스+휴지 시퀀스에서 `R_total = ΔV_total / I`, `R_ohm = ΔV_immediate / I`, `R_diff = R_total − R_ohm` |
| **OCV** | 긴 휴지 (예 ≥ 1h) 종료 시점 voltage — 평형 근사 |
| **CCV** | 펄스 직후 voltage — 반응 전위 |
| **출력 형태** | 각 사이클 별 scatter / line, 별도 plot 또는 기존 6 subplot에 overlay |
| **현재 코드** | 부분적 — DCIR 분석에서 R_ohm/R_diff 일부 도출 ([[hub_dcir]] 참조). OCV/CCV 별도 미구현. |

---

## 3. Phase 제안 (구현 로드맵)

| Phase | Scope | 결함 | 추정 변경 라인 | 위험도 |
|---|---|---|---|---|
| **Phase 2** | DOD 좌표계 단순화 | G1, G2 | proto_.py ~50 라인 | 🟢 낮음 — 내부 데이터 변환만, UI 무변경 |
| **Phase 3** | 페어링 자동화 | G3 | proto_.py ~30 라인 + UI 위젯 제거 | 🟡 중간 — UI 변경 + 옵션 의미 변경 |
| **Phase 4** | UI 재설계 — 분석 종류 라디오 | G4 | proto_.py ~200 라인 (UI 추가 + 옵션 매핑) | 🔴 높음 — UI 대규모 변경, 사용자 학습 비용 |
| **Phase 5** | dQdV 확대 + GITT/OCV/CCV | G5 + advanced | 신규 함수 + 약 100~300 라인 | 🟡 중간 — 기능 확장 |

각 Phase는 별도 plan 모드로 세부 정의. Phase 2부터 순차 진행 권장.

---

## 4. 검증 매트릭스

각 Phase 완료 후 검증할 시나리오:

| Phase | 시나리오 | 기대 결과 |
|---|---|---|
| Phase 2 | 사이클 + DOD + 연결 | 닫힌 루프, X 0~1 양수, dVdQ 스파이크 사라짐 |
| Phase 2 | 사이클 + DOD + 분리 | 충/방 NaN 경계, X 0~1 양수, 라벨 "DOD" |
| Phase 2 | 사이클 + SOC + 연결/분리 | 회귀 없음 (변경 없음) |
| Phase 3 | 사이클 + SOC + 연결 | 자동으로 페어 루프 표시 (체크박스 없음) |
| Phase 3 | 사이클 + SOC + 분리 | 페어링 비활성 (overlap=split이므로) |
| Phase 4 | "히스테리시스" 라디오 선택 | overlap=연결, 페어링 자동, X축 SOC/DOD 활성 |
| Phase 4 | "방전 분석" 라디오 선택 | overlap=분리, X축 시간/DOD 활성, SOC 비활성 |
| Phase 5 | 방전 분석 + dQdV 전환 | X/Y swap 정상 |

---

## 5. 관련 노트

- [[260428_profile_4modes_spec]] — 4종 분석 모델 spec (target 정의)
- [[260428_profile_view_color_spec]] — 그래프 구성·색상 체계 (직교 차원)
- [[hub_unified_profile]] — 코드 아키텍처 hub
- [[260420_profile_axis_dod_option]] — DOD 옵션 추가 시점 (이전 좌우 분리 의도, 본 문서에서 G1으로 재검토)
- [[260418_profile_options_redesign]] — 옵션 재설계 분석
- [[260410_analysis_profile_option_redesign]] — 옵션 캐싱 분석
- [[hub_dcir]] — DCIR 분석 (GITT R 도출과 연관)
