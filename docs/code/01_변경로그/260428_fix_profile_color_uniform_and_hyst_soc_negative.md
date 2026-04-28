# 프로파일 분석 — 사이클 라인 단색 + 히스테리시스 SOC 음수 동시 수정

날짜: 2026-04-28
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수:
- `_compute_tc_soc_offsets()` (L861)
- `_plot_one` (legacy_mode == "chg") (L25847+)
- `_plot_one` (legacy_mode == "dchg") (L25906+)
- `_plot_one` (legacy_mode == "cycle_soc") `_is_hysteresis` 분기 (L25977+)

## 배경

사용자 보고 1 — 프로파일 라인 색상이 동일:
> 사이클데이터 - 프로파일 분석 진행 시 plot 된 라인 색상 문제
> * 전체 통합 시, 프로파일 라인 색상이 동일한 문제 (CH 채널 제어에서는 색상 구분 되어있음)
> * 프리셋: 히스테리시스 설정 시, plot 라인 색상 동일 (CH 채널 제어에서 사이클 색상은 구분되어있음)

스크린샷: 9개 사이클 (Cy0014~Cy0022) 이 모두 검정색 단일 라인으로 표시. 다이얼로그의 사이클 리스트는 색상이 정상 구분.

사용자 보고 2 — 히스테리시스 분석 SOC 음수:
> 히스테리시스 분석 시, 전압 프로파일에서 SOC가 음수로 출력되는 문제
> 비정상 경로: `260317_260325_05_현혜정_4986mAh_SDI Gen5+ MP1 0.2C-10min volt hysteresis`
> 정상 경로: `260319_260326_05_현혜정_6330mAh_LWN 25P(after LT50cy) 0.2C-10min volt hysteresis`

스크린샷: SDI 케이스 SOC 범위 -0.1~0.4, Voltage 3.9~4.5V (고전압 영역인데 SOC 가 음수에서 시작).

## 결함 1 — 색상 후처리가 사이클 인덱스를 0으로 고정

### 원인

`_profile_render_loop` 의 색상 후처리 루프 (L20395-20442) 는 artist 의 `_cond_tag` 속성으로 사이클 경계를 검출:

```python
_cyc_idx = 0
_prev_cond = None
for line in _non_rest:
    _cond = getattr(line, '_cond_tag', None)
    if _prev_cond is not None:                   # ← 첫 루프 skip
        if _cond == _prev_cond or (_prev_cond == 2 and _cond == 1):
            _cyc_idx += 1
    _line_cyc_map[id(line)] = _cyc_idx
    _prev_cond = _cond
```

**결정적 흐름**:
1. 히스테리시스 플롯 함수는 `_cyc_idx = CycleNo.index(CycNo)` 로 올바른 사이클 색상 적용 — but `_cond_tag` **미설정**.
2. 후처리 루프는 `color_mode == 'chg_dchg' != 'distinct'` 조건 만족 → 진입.
3. 모든 라인 `_cond_tag = None` → `_prev_cond is not None` 조건 항상 False → `_cyc_idx` 0 고정.
4. `_n_cycles_detected = 1`, 모든 라인 `ci = 0`.
5. `_get_profile_color('chg_dchg', 0, 1, condition=None)` → `_HYST_RAINBOW_STOPS[0] = (0,0,0)` = `#000000` (검정).
6. `line.set_color('#000000')` 가 플롯 함수의 색상을 덮어씀.

"전체 통합" + chg/dchg legacy mode 도 동일: `graph_profile()` 은 color/`_cond_tag` 둘 다 미설정 → 후처리에서 `_cyc_idx=0` 고정 → 모두 동일 색상.

### CH 채널 제어 다이얼로그가 정상이었던 이유

`sub2_channel_map[label]['color']` 는 후처리 *직전* 의 `_artists[0].get_color()` 를 저장 (L20196). 다이얼로그는 올바른 색을 받지만 그래프는 그 직후 후처리에서 단색으로 덮어쓰여짐.

### 수정

플롯 함수가 artist 에 `_cond_tag` 를 설정하면 후처리 루프가 사이클 경계를 정상 검출하고 동일 색상을 재계산. 후처리 로직은 idempotent 하게 동작하도록 이미 설계되어 있었음.

**1. cycle_soc 의 `_is_hysteresis` 분기** (L25977+):
- Condition 1/2 분기: `_a1._cond_tag = _cond`, `_a3._cond_tag = _cond`
- Major Loop fallback: `_a1._cond_tag = 1`, `_a3._cond_tag = 1`
- sub-axes (ax2 dQdV / ax5 Crate / ax4 dVdQ / ax6 Temp): 일괄 `._cond_tag = 1`

**2. chg legacy mode** (L25847+):
- 6개 axes 의 `graph_profile()` 결과 모두 `._cond_tag = 1`

**3. dchg legacy mode** (L25906+):
- 6개 axes 의 `graph_profile()` 결과 모두 `._cond_tag = 2`

후처리 루프 (L20395-20442) 와 `_get_profile_color` (L3732) 는 변경 없음 — 인터페이스를 유지했기 때문에 기존 검출 로직이 그대로 동작.

### 영향 범위

- 히스테리시스 cycle 오버레이: 사이클 N개가 chg_dchg 레인보우 색상으로 분리 표시.
- "전체 통합" 의 충전 / 방전 / cycle 모드: warm / cool / dual gradient 가 사이클별로 분리 적용.
- "사이클 통합" 도 동일 fix 의 혜택 (cycle 오버레이가 dual gradient 로 정상 분리).
- 5사이클 이하: `color_mode == 'distinct'` 로 후처리 루프 미진입이므로 영향 없음.

---

## 결함 2 — `_compute_tc_soc_offsets` 의 SOC 음수

### 원인 (가설 + 부분 검증)

`_compute_tc_soc_offsets` (L861-893) 는 `cumul_net = 0` 에서 시작하여 TC별로 `Σ(ChgCap - DchgCap)` 누적:

```python
cumul_net = 0.0
for tc in sorted(cr['TC'].unique()):
    result[int(tc)] = cumul_net / cap_uah   # ← 누적 = 0 에서 시작
    chg = ...; dchg = ...
    cumul_net += (chg - dchg)
```

즉 셀이 TC 1 시작 시 SOC=0 (empty) 라고 가정. 충전 위주 프로토콜에서는 누적이 양수로 진행되어 정상 SOC 산출.

**비정상 케이스 (SDI Gen5+ MP1 4986mAh)**: 0.2C-10min volt hysteresis 프로토콜은 만충 → 지정 SOC 까지 방전 후 hysteresis loop 측정. TC 1 부터 방전이 시작되면 누적이 첫 사이클부터 음수 → offset 음수 → SOC 플롯이 -0.1 부근에서 시작.

**정상 케이스 (LWN 25P after LT50cy)**: "after LT50cy" — 50 사이클 수명시험 이후 OCV/RPT 등 충전 step 추가로 chg-dchg 누적이 균형 또는 양 → offset ≥ 0.

### 수정

**anchor 자동 보정**: 누적 결과에 음수가 감지되면 (`min(offset) < -0.05`) 모든 offset 에 `-min` 만큼 더해 [0, max_excursion] 범위로 평행이동. 정상 케이스 (`min ≥ 0`) 는 변경 없음.

```python
if result:
    _min = min(result.values())
    if _min < -0.05:
        shift = -_min
        result = {tc: v + shift for tc, v in result.items()}
        _perf_logger.info(f'[soc_offset] anchor shift +{shift:.3f} ...')
```

마진 0.05 는 측정 노이즈 / 부동소수점 오차 허용.

### 검증 권장

1. SDI Gen5+ MP1 비정상 경로 → 히스테리시스 분석 → SOC 가 [0, 1.05] 이내에 표시.
2. LWN 25P 정상 경로 두 개 (0.2C, 0.5C) → 변경 전과 동일 (anchor shift 미발동).
3. logger 로그 `[soc_offset] anchor shift +X.XXX` 출력 — SDI 만 발동, LWN 미발동 시 의도대로 동작.

### 한계 / 후속 작업

- 만충 시작 가정이 틀린 (방전부터 의도적으로 시작하는) 프로토콜이 있을 수 있음. 그 경우 본 수정은 잘못된 anchor 를 적용. 회귀 발견 시 voltage 기반 fallback (Step 2.4) 또는 사용자가 anchor 를 명시적으로 지정하는 옵션 추가 필요.
- 셀의 TC 1 직전 상태를 정확히 알 수 있는 메타데이터가 도입되면 본 휴리스틱은 제거 가능.

---

## 변경 요약

| 위치 | 변경 |
|------|------|
| L861-908 `_compute_tc_soc_offsets` | 음수 offset 자동 anchor shift, docstring 업데이트, perf logger info |
| L25847+ `chg` legacy `_plot_one` | 6개 artist 에 `._cond_tag = 1` |
| L25906+ `dchg` legacy `_plot_one` | 6개 artist 에 `._cond_tag = 2` |
| L25977+ `cycle_soc` 의 `_is_hysteresis` 분기 | 모든 artist 에 `._cond_tag` 설정 (chg/dchg seg = _cond, 그 외 = 1) |

후처리 루프 (L20395-20442), `_get_profile_color` (L3732), `_apply_legend_strategy` (L3889), `_resolve_profile_color_mode` (L3599) 는 **변경 없음**.

## 회귀 검증

- `cycle_regression_validator` 4 케이스 baseline 통과 확인 필요.
- 5사이클 이하 (`color_mode='distinct'`) 는 영향 없음.
- 히스테리시스 ON / OFF, 전체통합 / 셀별통합 / 사이클통합, chg / dchg / cycle 의 조합에서 사이클별 색상 구분 확인.
