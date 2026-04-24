# 사이클 요약/상세 탭 레이아웃·스타일 통일

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`

## 배경

사용자 요청:
> 상세 탭의 plot 처럼 요약 탭의 plot 구성으로 바꾸자 → 레이아웃·스타일만 통일

두 탭의 **지표 6개는 각각 다르게 유지** (탭1: Dchg/Eff/Temp/DCIR/Eff2/RndV, 탭2: Dchg/Chg/AvgV/DchgEng/RndV_chg_rest/RndV), 시각적 스타일·축 범위 처리만 탭1 ↔ 탭2 일관되게.

## 변경 내용

### 1. 신규 헬퍼 `_auto_adjust_axes_y_from_data(axes)` (L3330 근처)

탭2 의 다양한 지표별 축에 데이터 기반 **ylim 확장**을 독립 적용:

```python
def _auto_adjust_axes_y_from_data(axes):
    """각 ax 의 scatter 데이터 기반 ylim 확장 (각 축 독립).

    graph_cycle 에서 설정된 초기 ylim 을 존중하되,
    데이터가 범위 밖이면 확장.
    """
    for ax in axes:
        ys = []
        for coll in ax.collections:
            offs = coll.get_offsets()
            if len(offs) > 0:
                y = np.array(offs[:, 1], dtype=float)
                valid = y[~np.isnan(y)]
                if len(valid) > 0:
                    ys.extend(valid.tolist())
        if not ys:
            continue
        y_min, y_max = min(ys), max(ys)
        cur_low, cur_high = ax.get_ylim()
        _pad = (y_max - y_min) * 0.05 if y_max > y_min else 0.01
        new_low = min(cur_low, y_min - _pad)
        new_high = max(cur_high, y_max + _pad)
        if new_low < new_high:
            ax.set_ylim(new_low, new_high)
```

기존 `_auto_adjust_cycle_axes` 는 탭1 의 특정 축 매핑(ax1=Dchg, ax4=DCIR) 을 가정해서 그대로 재사용 불가 → **범용 버전** 신규.

### 2. 탭2 스타일 통일 호출 (L21340 근처)

`_auto_adjust_cycle_axes` 호출 직후 탭2 axes 에 동일 스타일 적용:

```python
if has_valid_data:
    _auto_adjust_cycle_axes(axes_list, ylimitlow, ylimithigh, xscale)
    # 탭2(상세) 스타일 통일: xlim/xticks 동기화 + ylim 데이터 기반 확장
    _x1_lim = ax1.get_xlim()
    _x1_ticks = ax1.get_xticks()
    for _ax_b in axes_list_b:
        _ax_b.set_xlim(_x1_lim)
        _ax_b.set_xticks(_x1_ticks)
    _auto_adjust_axes_y_from_data(axes_list_b)
```

| 항목 | Before | After |
|---|---|---|
| 탭2 xlim | 탭1 ax1 만 동기화 | **xlim + xticks** 모두 동기화 |
| 탭2 ylim | `graph_output_cycle_tab2` 하드코딩 | 데이터 기반 **자동 확장** |
| 탭1 ylim | `_auto_adjust_cycle_axes` (기존) | 불변 |

## 통일 효과

- **xlim 범위**: 탭1 ax1 자동 조정 결과가 탭2 6개 ax 에 복사 → 두 탭의 x축 완전 일치
- **xticks 간격**: 같은 눈금 (예: 0/500/1000/1500/2000) → 좌·우 비교 용이
- **ylim 상하한**: 탭2 의 각 지표가 범위 밖이어도 **데이터에 맞춰 자동 확장** → 점이 잘리지 않음
- **스타일 공통 (figsize / tight_layout / scatter 마커 / legend 등)**: `graph_cycle` / `graph_cycle_empty` 공용 함수 사용으로 이미 통일

## 영향 범위

- `_auto_adjust_axes_y_from_data()` 신규 유틸 (탭2 전용이지만 향후 탭3/4 도 재사용 가능)
- 탭2 에만 효과 (탭1 은 기존 `_auto_adjust_cycle_axes` 그대로)
- 지표 구성은 **변경 없음** (사용자 확답에 따라)
- 회귀 위험: 탭2 의 ylim 이 기본값 대비 더 넓어질 뿐, scatter 점은 그대로 유지

## 검증 포인트

- [ ] 사이클 분석 실행 후 "요약" / "상세" 탭 전환 시 **x축 범위·눈금 동일**
- [ ] 탭2 의 각 플롯에서 **점이 잘리지 않고 전체 표시**
- [ ] 탭2 의 ax5 (RndV_chg_rest) 가 데이터 있으면 ylim 이 적절히 자동 확장
- [ ] 탭1 의 ax1 (Dchg) ylim 동작 불변 (ylimitlow/ylimithigh 기반)
- [ ] 탭1 의 ax4 (DCIR) 상한 제한 동작 불변

## 후속 옵션 (선택)

- 탭2 에도 n_legend>8 시 외부 legend 배치 (탭1과 동일) — 필요 시 별도 PR
- 축별 ylim 하드코딩 제거하고 완전 데이터 기반으로 전환 — `graph_output_cycle_tab2` 리팩터 필요 시
