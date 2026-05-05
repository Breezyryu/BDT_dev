---
title: "상세 결과 탭 — 비율 그래프 3개 ylim/ytick 통일 (Dchg/Chg/Eng)"
date: 2026-05-05
tags: [enhancement, cycle-data, axis-scaling, ylim, yticks, ux, detail-tab]
related:
  - "[[260426_fix_cycle_axes_y_fit]]"
---

# 상세 결과 탭 — 비율 그래프 3개 ylim/ytick 통일

> 사용자 요청: Cycle 분석의 **상세 결과 탭**에서 비율(unitless) 단위 3개
> 그래프 — Discharge Capacity Ratio / Charge Capacity Ratio / Discharge
> Energy Ratio — 의 y축 ylim·ytick 을 동일하게 구성하여 채널/사이클 간
> 비교를 용이하게 하자.

## Before

`_finalize_cycle_tab` 호출 직전 축 자동 조정 단계 (`L23665` 인근):

```python
_ax1b.set_ylim(*ax1.get_ylim())          # 2-1 ↔ 1-1 동일 (이전 요청)
_ax1b.set_yticks(ax1.get_yticks())
_fit_ax_y_from_data(_ax2b, ymin_floor=0.6, outlier_filter='iqr')  # 2-2 독립
_fit_ax_y_from_data(_ax3b, ymax_cap=4.0)
_fit_ax_y_from_data(_ax4b)               # 2-4 독립
_fit_ax_y_from_data(_ax5b)
_fit_ax_y_from_data(_ax6b, ymax_cap=4.0)
```

| Axis | ylim | yticks |
|---|---|---|
| 2-1 Dchg Cap Ratio | ax1 자동 조정 결과 (예: 0.65-1.05) | step 0.05 |
| 2-2 Chg Cap Ratio | 데이터 fit (예: 0.70-1.0) | MaxNLocator 자동 (4 tick) |
| 2-4 Dchg Eng Ratio | 데이터 fit (예: 0.65-1.0) | MaxNLocator 자동 |

→ 같은 0~1 비율 단위인데 y 스케일이 제각각이라 시각적 비교가 어려움.

## After

신규 헬퍼 `_sync_ratio_axes_y` 로 4 개 축 (탭1 1-1 + 탭2 2-1·2-2·2-4)
의 ylim·yticks 동기화:

```python
_sync_ratio_axes_y(
    (ax1, _ax1b, _ax2b, _ax4b),
    step=0.05,
    ymin_floor=0.0,
    base_ylim=ax1.get_ylim(),     # ax1 자동 조정 결과를 anchor
)
_fit_ax_y_from_data(_ax3b, ymax_cap=4.0)
_fit_ax_y_from_data(_ax5b)
_fit_ax_y_from_data(_ax6b, ymax_cap=4.0)
```

### 동기화 알고리즘 (`_sync_ratio_axes_y`, L4005)

1. 4 개 축의 모든 scatter offsets 에서 y 데이터 합산
2. Tukey 1.5×IQR outlier 제거 (단일 점 이상치로 ylim 과확장 방지)
3. step (0.05) 단위로 floor/ceil 라운딩 + 1 step 여유
4. `base_ylim` (= `ax1.get_ylim()`) 과 union — **확장만, 절대 축소 금지**
5. tick 개수 ≤ 10 보장 (초과 시 step 자동 확대)
6. 4 개 축에 동일 `set_ylim` + `set_yticks` 적용

### 인변량 (invariants)

- **1-1 = 2-1 = 2-2 = 2-4** — 비율 4 개 축 ylim·ytick 완전 일치
- 사용자 입력 ylim (`ylimitlow`/`ylimithigh`) **절대 축소 금지**
  → `_auto_adjust_cycle_axes` 가 이미 user-input 기반 자동 확장 적용,
  새 헬퍼는 그 결과를 base 로 union 만 수행
- Charge Cap Ratio min 이 Discharge Cap Ratio min 보다 낮은 드문 케이스에서만
  탭1 ax1 도 함께 확장 (두 비율은 도메인적으로 매우 가까워 ≤2% 차이)

## 효과 (예상 — Q8 ATL 2335mAh 기준)

| Axis | Before | After |
|---|---|---|
| 1-1 Dchg Cap Ratio | 0.65-1.05 step 0.05 | (변경 없음 또는 데이터 따라 ±0.05) |
| 2-1 Dchg Cap Ratio | 1-1 동일 | 1-1 동일 (변경 없음) |
| 2-2 Chg Cap Ratio | 0.70-1.00 (4 tick) | **0.65-1.05 step 0.05** |
| 2-4 Dchg Eng Ratio | 데이터 fit | **0.65-1.05 step 0.05** |

→ 3 개 비율 그래프가 동일 y 격자에 정렬되어 충방전 효율·에너지 fade 의
상대적 차이를 한눈에 비교 가능.

## 영향 없음 (변경하지 않은 축)

| Axis | 처리 | 이유 |
|---|---|---|
| 2-3 AvgV | `_fit_ax_y_from_data(ymax_cap=4.0)` | 단위 다름 (Voltage) |
| 2-5 Charge Rest End V | `_fit_ax_y_from_data` | 단위 다름 |
| 2-6 Discharge Rest End V | `_fit_ax_y_from_data(ymax_cap=4.0)` | 단위 다름 |

요약 탭의 ax2/ax3/ax4/ax5/ax6 (Eff/Temp/DCIR/Eff2/RndV) 도 영향 없음.

## 검증

- [x] `python -m py_compile` syntax OK
- [ ] 사용자 알파:
  - 상세 결과 탭의 Discharge Cap / Charge Cap / Discharge Eng Ratio
    3 개 그래프 y축 격자(ylim·ytick)가 완전 일치
  - 요약 탭 1-1 Discharge Cap Ratio 와도 일치 (이전 요청 유지)
  - 사용자가 ylimitlow/ylimithigh 입력 시 그 범위가 축소되지 않음
  - 채널 토글, xlim 동기화 등 기존 동작 유지

## 위험·롤백

- **위험**: 낮음 — 시각 표현만 변경. 데이터·범례·툴팁 영향 없음
- **롤백**: 단일 함수 추가 + 단일 호출부 변경. revert 로 즉시 복원

## 관련

- `_fit_ax_y_from_data` / `_auto_adjust_cycle_axes` 도입 (`260426_fix_cycle_axes_y_fit`)
- 2-1 ↔ 1-1 동기화 도입 (이전 사용자 요청 — `_ax1b.set_ylim(*ax1.get_ylim())`)
