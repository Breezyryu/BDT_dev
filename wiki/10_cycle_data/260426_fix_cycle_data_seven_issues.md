---
title: "사이클 분석 7개 결함 일괄 수정"
date: 2026-04-26
tags: [bugfix, cycle-data, ylim, units, ux, multi-fix]
related:
  - "[[260426_fix_cycle_axes_y_fit]]"
  - "[[260426_fix_cycle_channel_control_sub_and_tab2_redraw]]"
  - "[[260426_fix_pne_sch_typecode_swap_offset_correct]]"
---

# 사이클 분석 7개 결함 일괄 수정

> 사용자 보고 7개 항목 + 캡처 검증. 같은 세션에서 진행된 axis fit / 채널 컨트롤 / PNE swap 수정의 후속.

## 항목별 수정

### 1. Toyo Discharge Energy 단위 (mWh → Wh)

**증상**: 1번(ATL Q7M Toyo)·3번(Q8 Sub Toyo) 그룹 DchgEng 가 6000·9000 으로 표시 (정상 6·9 Wh 의 1000배). PNE 그룹 (2·4번) 은 0.

**원인**: `toyo_cycle_data` 의 `DchgEng = Dchgdata["Pow[mWh]"]` (L4256) — mWh 단위 그대로 반환. PNE 의 `pivot_data["DchgEngD"][2] / 1000` 와 단위 불일치.

**수정**:
```python
DchgEng = Dchgdata["Pow[mWh]"] / 1000  # mWh → Wh
```

⚠️ **PNE DchgEng = 0 결함은 별개 이슈** — column 15 raw 단위 검증 필요. 향후 SaveEndData CSV column 15 raw value 직접 확인하여 fix.

### 2. 요약·상세 탭 grid 정렬 통일

**증상**: 두 탭의 그리드 위치가 약간 어긋남.

**원인**: `plt.suptitle` 은 **현재 활성 figure** 에만 적용. fig (요약) 와 fig2 (상세) 중 호출 시점에 활성인 한쪽만 suptitle 표시 → 다른 쪽은 suptitle 영역만큼 plot 위로 올라감.

**수정**:
```python
fig.suptitle(suptitle_name, ...)
if fig2 is not None:
    fig2.suptitle(suptitle_name, ...)
```

두 figure 모두 동일 suptitle 적용 → grid 정렬 일치.

### 3. 방전·충전 용량 ylim outlier 제외 + 최소 0.6 선호

**증상**: 한 점만 매우 낮은 값 (0.4 등) 이 있을 때 ylim 이 그 outlier 까지 늘어나서 정상 데이터 가시성 ↓.

**수정**:
1. `_fit_ax_y_from_data(ax, ymin_floor, outlier_filter='iqr')` 매개변수 추가
2. `_auto_adjust_cycle_axes` 의 ax1 (요약 탭 Dchg ratio) 에 IQR 1.5 outlier 필터 추가
3. 상세 탭 ax1/ax2 (용량 ratio) 호출에 `ymin_floor=0.6, outlier_filter='iqr'` 적용

```python
# 상세 탭
_fit_ax_y_from_data(_ax1b, ymin_floor=0.6, outlier_filter='iqr')  # Dchg
_fit_ax_y_from_data(_ax2b, ymin_floor=0.6, outlier_filter='iqr')  # Chg
```

`ymin_floor=0.6` 동작:
- 데이터 min 이 0.7 → ylim_low = 0.6 (강제 0.6 까지 보여줌)
- 데이터 min 이 0.5 → ylim_low = 0.5 (데이터 우선)

### 4. Rest End Voltage ylim max = 4.0

**증상**: 방전 후 Rest 의 max 가 4.0 위로 늘어나면 가시성 ↓.

**수정**:
```python
# 요약 탭 ax6 (RndV = 방전 후 OCV)
_fit_ax_y_from_data(ax6, padding=0.05, max_nbins=6, ymax_cap=4.0)
# 상세 탭 ax6 (Discharge Rest End V = RndV)
_fit_ax_y_from_data(_ax6b, ymax_cap=4.0)
```

`ymax_cap=4.0`: 데이터+padding 이 4.0 을 넘으면 4.0 으로 cap.

### 5. Toyo Charge Rest End V 잘못된 매핑 (방전 rest 값 출력)

**증상**: 1번·3번 (Toyo) 그룹의 Charge Rest End V (2-5) 가 실제로는 방전 rest 값 (≈3.0V) 표시. 정상은 ≈4.2V.

**원인** (`toyo_cycle_data` L4350-4354):
```python
# 잘못된 단순 복사:
df.NewData['RndV_chg_rest'] = df.NewData['RndV']  # ❌ RndV = 방전 후 OCV
```

`RndV` (= chgdata["Ocv"]) 는 충전 step 시작 직전 OCV = **방전 후 OCV** (≈3.0V). 따라서 `RndV_chg_rest` 도 같은 방전 후 OCV 가 되어 의미 무효.

**수정**:
```python
# 방전 step 의 Ocv = 방전 직전 V = 충전 후 OCV (Charge Rest End V)
DchgOcv = Dchgdata["Ocv"]
# (인덱스 정렬 적용)
DchgOcv = DchgOcv.iloc[1:]
DchgOcv = DchgOcv.iloc[:_nmin]
# DataFrame 생성 시 정확한 값으로 채움
df.NewData = pd.DataFrame({
    "Dchg": Dchg, "RndV": Ocv, "RndV_chg_rest": DchgOcv,
    ...
})
```

추가 안전장치: `_ensure_rndv_split_columns` 가 호출자 미리 채운 값을 보존하도록 변경:
```python
if not _chg_volt.empty:
    _new = nd['OriCyc'].map(_chg_volt)
    _na_mask = nd['RndV_chg_rest'].isna()
    nd.loc[_na_mask, 'RndV_chg_rest'] = _new.loc[_na_mask]  # NaN 만 채움
```

### 6. 평균 방전 전압 ylim max = 4.0

**수정**:
```python
# 상세 탭 ax3 (Average Discharge Voltage)
_fit_ax_y_from_data(_ax3b, ymax_cap=4.0)
```

데이터 3.7~3.95 + padding 시 4.0 cap.

### 7. 충방전 패턴 상세 버튼·popup 스타일 → CH 토글 통일

**원인**: 패턴 상세 버튼은 hardcoded 라이트 색상 (`#F0F4F8`/`#3C5488`), CH 토글은 dark/light 자동 감지. 다른 위치에서 일관성 부족.

**수정** (L19264-19271):
```python
# CH 토글과 동일한 dark/light 동적 색상
from PyQt6.QtWidgets import QApplication
_palette = QApplication.instance().palette()
_bg = _palette.color(_palette.ColorRole.Window)
_is_dark = _bg.lightness() < 128
_btn_bg = "#3c3c3c" if _is_dark else "#f5f5f5"
_btn_hover = "#505050" if _is_dark else "#e0e0e0"
_btn_border = "#666" if _is_dark else "#ccc"

toggle_btn = QPushButton("▶ 상세")
toggle_btn.setFixedSize(50, 22)   # CH 토글과 동일 size
toggle_btn.setStyleSheet(...)      # CH 토글과 동일 stylesheet
```

popup 도 동일 dark/light 색상:
```python
popup.setStyleSheet(
    f'QFrame {{ background: {_btn_bg}; '
    f'border: 1px solid {_btn_border}; border-radius: 5px; }}')
```

## 검증

- [x] `python -c "ast.parse(...)"` syntax OK
- [ ] 사용자 알파:
  - 1번: Toyo DchgEng 가 정상 Wh 단위 (6 Wh, 9 Wh 등)
  - 2번: 요약/상세 탭 grid 정렬 일치
  - 3번: 용량 ratio outlier 무시 + 최소 0.6
  - 4번: Rest End V max 4.0 cap (3.0~4.0 범위 표시)
  - 5번: Charge Rest End V 가 실제 충전 후 OCV (≈4.2V) 표시
  - 6번: AvgV max 4.0 cap
  - 7번: 패턴 상세 버튼·popup 이 CH 토글과 동일 스타일 (다크/라이트)
- ⚠️ **PNE DchgEng = 0 별도 이슈** — column 15 raw 값 검증 필요

## 위험·롤백

- **위험**: 중간 — Toyo 데이터 경로 변경 (DchgOcv 추출, RndV_chg_rest 매핑) 가 핵심
- **롤백**: 단일 commit, revert 1회

## 향후

- PNE DchgEng = 0 결함 — Q8 Main SaveEndData CSV 의 column 15 raw value 직접 확인 필요. 단위 (mWh? Wh? µWh?) 확정 후 fix
- `_ensure_rndv_split_columns` 의 NaN 기반 보존 로직은 PNE / Toyo 양쪽 동일 동작
