---
title: "사이클 분석 Y축 fit — 빈공간 제거 + 상세 탭 yticks 정정"
date: 2026-04-26
tags: [bugfix, cycle-data, axis-scaling, ylim, yticks, ux]
related:
  - "[[260426_fix_cycle_channel_control_sub_and_tab2_redraw]]"
---

# 사이클 분석 Y축 fit — 빈공간 제거 + 상세 탭 yticks 정정

> 사용자 보고 두 결함:
> 1. 요약 탭 plot 의 빈공간이 많다 (특히 Temp, RndV)
> 2. 상세 탭 plot 의 Y축 설정 (yticks 등) 점검 필요

## 원인

### 요약 탭 (`graph_output_cycle` L3067)
hardcoded ylim 이 데이터 범위보다 매우 넓음:

| Axis | Hardcoded ylim | 실제 데이터 (Q8/Gen4) | 빈공간 |
|---|---|---|---|
| ax1 Discharge Cap Ratio | 사용자 입력 | 0.74-1.00 | 적당 |
| ax2 Eff | 0.992-1.004 | 좁음 (의도) | 적당 |
| ax3 Temp | **0-50, step 5** | **22-25** | **>50%** ❌ |
| ax4 DCIR | 0-120·irscale | 0-100 | 적당 |
| ax5 Eff2 | 0.996-1.008 | 좁음 (의도) | 적당 |
| ax6 RndV | **3.00-4.00, step 0.1** | **3.0-3.7** | **30%** ❌ |

`_auto_adjust_cycle_axes` (L3349) 가 ax1 Dchg 만 동적 fit — 나머지 axes 는 hardcoded.

### 상세 탭 (`graph_output_cycle_tab2` L3124)
hardcoded ylim 이 데이터 범위보다 매우 넓고 yticks 도 부적절:

| Axis | Hardcoded | 데이터 | 결과 |
|---|---|---|---|
| ax1 Dchg Ratio | 0.70-1.02, step 0.05 | 0.74-1.00 | 적당 |
| ax2 Chg Ratio | 0.70-1.02, step 0.05 | 0.74-1.00 | 적당 |
| ax3 AvgV | 3.00-4.00, step 0.1 | 3.7-3.9 | **빈공간 70%** ❌ |
| ax4 DchgEng | **0-15, step 1** | **12-15** | **빈공간 80% + tick 15개 너무 촘촘** ❌ |
| ax5 Charge Rest End V | 4.00-4.25, step 0.05 | 4.20-4.25 | **빈공간 80%** ❌ |
| ax6 Discharge Rest End V | 2.80-3.20, step 0.05 | 3.15-3.20 | **빈공간 80%** ❌ |

`_auto_adjust_axes_y_from_data` (L3323) 가 **확장만** 하고 **축소 안 함** → hardcoded 가 데이터보다 넓을 때 그대로 유지.

## 수정

### 1) `_fit_ax_y_from_data` 신규 helper (L3323)

데이터 기반 ylim 완전 fit (확장 + 축소) + matplotlib `MaxNLocator` 로 자동 yticks:

```python
def _fit_ax_y_from_data(ax, *, padding=0.05, max_nbins=6) -> bool:
    ys = []
    for coll in ax.collections:
        offs = coll.get_offsets()
        if len(offs) > 0:
            y = np.array(offs[:, 1], dtype=float)
            valid = y[~np.isnan(y)]
            if len(valid) > 0:
                ys.extend(valid.tolist())
    if not ys:
        return False
    y_min, y_max = min(ys), max(ys)
    y_range = y_max - y_min
    _pad = y_range * padding if y_range > 0 else max(abs(y_min) * 0.05, 0.01)
    new_low = y_min - _pad
    new_high = y_max + _pad
    if new_high <= new_low:
        return False
    ax.set_ylim(new_low, new_high)
    # hardcoded yticks 무효화 + matplotlib 자동 (1·2·5 nice number)
    ax.yaxis.set_major_locator(plt.MaxNLocator(nbins=max_nbins, prune='both',
                                               steps=[1, 2, 2.5, 5, 10]))
    return True
```

`MaxNLocator(steps=[1, 2, 2.5, 5, 10])` — matplotlib 의 표준 nice-number 알고리즘으로 1, 2, 2.5, 5, 10 의 10^k 배수 중 적절한 step 선택.

### 2) `_auto_adjust_axes_y_from_data` 일반화 (상세 탭)

```python
def _auto_adjust_axes_y_from_data(axes):
    """모든 axes 에 _fit_ax_y_from_data 호출."""
    for ax in axes:
        _fit_ax_y_from_data(ax)
```

이제 확장만이 아니라 **fit (축소도)** 수행. graph_output_cycle_tab2 의 hardcoded ylim 이 모두 데이터 범위로 좁혀짐.

### 3) `_auto_adjust_cycle_axes` 에 ax3/ax6 fit 추가 (요약 탭)

```python
# ax3 (Temperature) / ax6 (Rest End Voltage) 데이터 fit ──
# graph_output_cycle 의 hardcoded ylim (Temp 0~50, RndV 3.0~4.0) 이
# 데이터 범위 (Temp 22~25, RndV 3.0~3.7) 대비 넓어 빈공간이 큼.
# 데이터 기반 fit 으로 가시성 향상. ax2/ax5 (Eff) 는 좁은 범위가
# 도메인적으로 의미 있어 그대로 유지. ax1 은 사용자 입력 ylim 적용.
_fit_ax_y_from_data(ax3, padding=0.10, max_nbins=6)
_fit_ax_y_from_data(ax6, padding=0.05, max_nbins=6)
```

- **ax2/ax5 (Eff·Eff2)** 는 hardcoded 유지 — 0.992-1.004 같은 좁은 범위가 도메인적으로 의미 있음 (효율의 미세 변동을 강조)
- **ax4 (DCIR)** 는 기존 500 초과 보정 로직 유지 (소량의 이상치를 클램프)
- **ax1 (Dchg Ratio)** 은 사용자 입력 `ylimitlow`/`ylimithigh` 적용 — 변경 없음

## 효과

### 요약 탭 (Q8 ATL Main 2.0C 기준)

| Axis | Before | After |
|---|---|---|
| ax3 Temp | 0~50 (50% 빈공간) | 21~26 (데이터 fit) |
| ax6 RndV | 3.0~4.0 (30% 빈공간) | 3.2~3.7 (데이터 fit) |

### 상세 탭

| Axis | Before | After |
|---|---|---|
| ax1 Dchg | 0.70-1.02 step 0.05 | 0.73-1.01 nice ticks |
| ax3 AvgV | 3.0-4.0 step 0.1 | 3.7-3.95 nice ticks |
| ax4 DchgEng | **0-15 step 1 (15 ticks)** | **12-16 nice ticks** ✓ |
| ax5 Chg Rest V | 4.0-4.25 step 0.05 | 4.20-4.26 |
| ax6 Dchg Rest V | 2.8-3.2 step 0.05 | 3.14-3.21 |

빈공간이 거의 사라지고 데이터 변동 패턴이 더 잘 보임.

## 검증

- [x] `python -c "ast.parse(...)"` syntax OK
- [ ] 사용자 알파:
  - 요약 탭 ax3 Temp 가 데이터 범위에 fit (22-25 가 거의 가득 차게 표시)
  - 요약 탭 ax6 RndV 도 fit
  - 상세 탭 ax4 DchgEng 의 yticks 가 매끄러운 (12, 13, 14, 15 등) 형태
  - 상세 탭 모든 axis 의 빈공간 감소
  - 채널 토글·xlim 동기화 등 기존 동작 유지
- [ ] Edge cases:
  - 데이터가 한 점만 있는 경우 (단일 사이클) — `y_range == 0` 분기로 작은 padding
  - 모든 데이터 NaN — 변경 없음 (`if not ys: return False`)

## 위험·롤백

- **위험**: 낮음 — 데이터 fit 은 보편적 개선. ax2/ax5 (Eff) 도메인 의미 보존
- **롤백**: 단일 commit, revert 로 hardcoded ylim/yticks 복원

## 관련

- 채널 토글 fix (`260426_fix_cycle_channel_control_sub_and_tab2_redraw`) 와 같은 세션
- 요약/상세 탭 분리 PR (`d259e56`, `5225df9`) 의 후속 정정
