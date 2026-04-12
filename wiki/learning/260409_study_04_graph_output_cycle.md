---
date: 2026-04-09
tags: [python, BDT, 코드학습, matplotlib, 그래프, 사이클데이터, PyQt6]
aliases: [graph_output_cycle, 사이클그래프]
---

# graph_output_cycle() 플로팅 라인별 분석

> **학습 목표**: `df.NewData`가 6개 서브플롯으로 시각화되는 과정을 이해한다.
> 각 서브플롯이 **어떤 물리량**을, **어떤 스타일**로, **왜** 그렇게 그리는지 체화한다.

**대상 함수**:
- `graph_output_cycle()` — L2573–2613 (6개 서브플롯 조합)
- `graph_cycle()` — L2545–2557 (filled scatter)
- `graph_cycle_empty()` — L2560–2571 (empty scatter)
- `graph_cycle_base()` — L2528–2542 (축 설정 공통)

**선행 학습**: [[260409_study_03_pne_cycle_data|Study 03: PNE 사이클 데이터]]

---

## 1. 6개 서브플롯 레이아웃

```
┌─────────────────┬─────────────────┬─────────────────┐
│   ax1           │   ax2           │   ax3           │
│   방전 용량 비   │   쿨롱 효율     │   온도           │
│   (Dchg ratio)  │   (Eff)         │   (Temp, °C)    │
├─────────────────┼─────────────────┼─────────────────┤
│   ax4           │   ax5           │   ax6           │
│   DCIR          │   교차 효율     │   AvgV + RndV   │
│   (dcir, mΩ)    │   (Eff2)        │   (V)           │
└─────────────────┴─────────────────┴─────────────────┘
```

---

## 2. 함수 시그니처 (L2573–2574)

```python
def graph_output_cycle(
    df,           # df.NewData를 가진 DataFrame 컨테이너
    xscale,       # X축 범위 (0=자동, 양수=고정)
    ylimitlow,    # Dchg Y축 하한 (ratio, 예: 0.8)
    ylimithigh,   # Dchg Y축 상한 (ratio, 예: 1.05)
    irscale,      # DCIR Y축 스케일 배수 (기본 1.0)
    temp_lgnd,    # 범례 라벨 (온도/셀명 등)
    colorno,      # 색상 인덱스 (0~9, THEME['PALETTE'])
    graphcolor,   # 색상 팔레트 리스트
    dcir,         # DCIR 체크박스 위젯 (QCheckBox)
    ax1, ax2, ax3, ax4, ax5, ax6  # matplotlib Axes 6개
):
```

> ⚠ `dcir`은 **데이터가 아니라 QCheckBox 위젯**이다. `dcir.isChecked()`로 MK DCIR 모드를 판별.
> 이는 UI 로직과 그래프 로직이 결합된 레거시 패턴이다.

---

## 3. 색상 선택 (L2576)

```python
color = graphcolor[colorno % len(THEME['PALETTE'])]
# THEME['PALETTE']: 10색 순환 팔레트
# '#3C5488'(남색), '#E64B35'(빨강), '#00A087'(청록), '#4DBBD5'(하늘),
# '#F39B7F'(살구), '#8491B4'(회보라), '#91D1C2'(민트), '#DC0000'(진빨),
# '#7E6148'(갈색), '#B09C85'(베이지)
#
# colorno % 10: 셀이 10개를 넘으면 색상 순환
# 🔋 여러 셀을 한 그래프에 오버레이할 때 색상으로 구분
```

---

## 4. 서브플롯별 상세 분석

### 4.1 ax1 — 방전 용량 비 (Dchg Ratio)

```python
artists.append(graph_cycle(
    df.NewData.index,     # X: 행 인덱스 (0, 1, 2, ...)
    df.NewData.Dchg,      # Y: 방전 용량 ratio (0~1.0)
    ax1,
    ylimitlow,            # Y 하한 (사용자 설정, 예: 0.80)
    ylimithigh,           # Y 상한 (사용자 설정, 예: 1.05)
    0.05,                 # Y 눈금 간격
    "Cycle",              # X 라벨
    "Discharge Capacity Ratio",  # Y 라벨
    temp_lgnd,            # 범례: 온도 표시 (예: "23°C")
    xscale,               # X 범위
    color                 # 점 색상
))
```

> 🔋 **가장 중요한 플롯**: 수명시험의 핵심 지표.
> - Y=1.0에서 시작 → 점진적 감소 = 용량 열화
> - 갑작스러운 감소 = 무릎점(knee point) 발생
> - Y=0.8 (80%) = 일반적 EOL(수명종료) 기준

### 4.2 ax2 — 쿨롱 효율 (Eff)

```python
artists.append(graph_cycle(
    df.NewData.index,
    df.NewData.Eff,       # Y: Dchg/Chg (0.99~1.00 범위)
    ax2,
    0.992,                # Y 하한 (99.2%)
    1.004,                # Y 상한 (100.4%)
    0.002,                # Y 눈금 간격 (0.2%)
    "Cycle",
    "Discharge/Charge Efficiency",
    temp_lgnd, xscale, color
))
```

> 🔋 **쿨롱 효율 해석**:
> - 99.9% = 0.1% 리튬이 매 사이클 소모 → 1000사이클에 10% 손실
> - 갑자기 효율 하락 → 부반응 증가 (리튬 석출, 전해액 분해)
> - Y축 범위가 0.992~1.004로 매우 좁음 → 미세한 변화도 시각적으로 감지

### 4.3 ax3 — 온도 (Temperature)

```python
artists.append(graph_cycle(
    df.NewData.index,
    df.NewData.Temp,      # Y: 방전 중 최고 온도 (°C)
    ax3,
    0,                    # Y 하한: 0°C
    50,                   # Y 상한: 50°C
    5,                    # Y 눈금 간격: 5°C
    "Cycle",
    "Temperature (℃)",
    temp_lgnd, xscale, color
))
```

> 🔋 **온도 모니터링**:
> - 일정한 온도 = 항온 챔버 정상 동작
> - 점진적 온도 상승 = 내부 저항 증가 (발열 증가)
> - 급격한 온도 변화 = 챔버 이상 또는 셀 이상

### 4.4 ax4 — DCIR (MK 모드 vs 일반 모드 분기)

```python
if dcir.isChecked() and hasattr(df.NewData, "dcir2"):           # L2591
    # ── MK DCIR 모드: SOC70% 1s Pulse + RSS ──
    
    # Empty scatter: SOC70% 1s Pulse DCIR (속이 빈 원)
    artists.append(graph_cycle_empty(
        df.NewData.index, df.NewData.soc70_dcir,
        ax4, 0, 120.0 * irscale, 20 * irscale,
        "Cycle", "DC-IR @Discharge (mΩ)",
        "_nolegend_", xscale, color, _size=_dcir_es
    ))                                                          # L2592-2593
    
    # Filled scatter: SOC70% RSS DCIR (속이 찬 원)
    artists.append(graph_cycle(
        df.NewData.index, df.NewData.soc70_rss_dcir,
        ax4, 0, 120.0 * irscale, 20 * irscale,
        "Cycle", "DC-IR @Discharge (mΩ)",
        temp_lgnd, xscale, color, _size=_dcir_s
    ))                                                          # L2594-2595
    
    # 점선 연결 (추세 시각화)
    _dcir_valid = df.NewData.soc70_dcir.dropna()                # L2597
    if len(_dcir_valid) > 1:
        ax4.plot(_dcir_valid.index, _dcir_valid.values,
                 linewidth=0.8, alpha=0.5, color=color,
                 linestyle='--', zorder=2)                      # L2599
    # RSS도 동일하게 실선 연결
    _rss_valid = df.NewData.soc70_rss_dcir.dropna()
    if len(_rss_valid) > 1:
        ax4.plot(...)                                           # L2603

else:                                                           # L2605
    # ── 일반 DCIR 모드 ──
    artists.append(graph_cycle(
        df.NewData.index, df.NewData.dcir,
        ax4, 0, 120.0 * irscale, 20 * irscale,
        "Cycle", "DC-IR @Discharge(mΩ)",
        temp_lgnd, xscale, color, _size=_dcir_s
    ))                                                          # L2606-2607
```

> 🔋 **DCIR 플롯 해석**:
> - **RSS (●, 실선)**: 정상상태 DCIR — 모든 저항 성분 포함 → 값이 더 큼
> - **1s Pulse (○, 점선)**: 1초 응답 — 옴 저항 + 빠른 전하이동만 → 값이 더 작음
> - 두 값의 차이 = 확산 저항 성분
> - DCIR 증가 추세 = SEI 성장 + 접촉 저항 증가 = 열화 진행

### 4.5 ax5 — 교차 효율 (Eff2)

```python
artists.append(graph_cycle(
    df.NewData.index,
    df.NewData.Eff2,      # Y: Chg(n+1) / Dchg(n)
    ax5,
    0.996, 1.008, 0.002,  # Y 범위: 99.6~100.8%
    "Cycle",
    "Charge/Discharge Efficiency",
    temp_lgnd, xscale, color
))
```

> 🔋 **Eff2 vs Eff 차이**:
> - Eff = Dchg(n) / Chg(n) — 같은 사이클 내 비교
> - Eff2 = Chg(n+1) / Dchg(n) — 사이클 간 비교
> - Eff2가 더 민감: Rest 중 자가방전/회복 효과가 반영됨

### 4.6 ax6 — 평균 전압 + Rest 전압 (복합 플롯)

```python
# Rest End Voltage — filled scatter (●)
artists.append(graph_cycle(
    df.NewData.index, df.NewData.RndV,
    ax6, 3.00, 4.00, 0.1,
    "Cycle", "Rest End Voltage (V)",
    "_nolegend_", xscale, color           # ← 범례 제외
))                                                              # L2583-2584

# Average Discharge Voltage — empty scatter (○)
artists.append(graph_cycle_empty(
    df.NewData.index, df.NewData.AvgV,
    ax6, 3.00, 4.00, 0.1,
    "Cycle", "Average/Discharge Rest Voltage (V)",
    temp_lgnd, xscale, color
))                                                              # L2587-2588
```

> 🔋 **ax6 복합 플롯 해석**:
> - **RndV (●, 위쪽)**: 충전 후 Rest 전압 ≈ 만충 OCV. 일정해야 정상.
> - **AvgV (○, 아래쪽)**: 평균 방전 전압. 내부 저항 증가 시 하락.
> - 두 값의 차이(RndV - AvgV) 증가 = 내부 저항 증가의 직관적 지표.
> - `place_avgrest_labels(ax6)`가 나중에 호출되어 중앙에 "Avg V" / "Rest V" 라벨 배치.

---

## 5. 헬퍼 함수 상세

### 5.1 graph_cycle() — Filled Scatter (L2545–2557)

```python
def graph_cycle(x, y, ax, lowlimt, highlimit, ygap, xlabel, ylabel,
                tlabel, xscale, cyc_color, overall_xlimit=0, _size=None):
    _s = _size if _size is not None else THEME['SCATTER_SIZE']
    if cyc_color != 0:
        sc = ax.scatter(x, y, label=tlabel, s=_s, color=cyc_color,
                   alpha=THEME['SCATTER_ALPHA'],          # 반투명
                   edgecolors=THEME['EDGE_COLOR'],        # 테두리 색
                   linewidths=THEME['EDGE_WIDTH'],        # 테두리 두께
                   zorder=3)                              # 그리드 위에 표시
    # ...
    graph_cycle_base(x, ax, lowlimt, highlimit, ygap, xlabel, ylabel, xscale, overall_xlimit)
    return sc
```

> - `SCATTER_ALPHA`: 여러 셀 오버레이 시 겹침 시각화
> - `zorder=3`: 그리드(zorder=1) 위에 점을 그림
> - 반환값 `sc`: 나중에 artist 목록에 추가 → 범례 관리/삭제에 사용

### 5.2 graph_cycle_empty() — Empty Scatter (L2560–2571)

```python
def graph_cycle_empty(x, y, ax, ...):
    sc = ax.scatter(x, y, label=tlabel, s=_s,
               edgecolors=cyc_color,
               facecolors='none',           # ← 속이 빈 원!
               alpha=THEME['SCATTER_ALPHA'],
               linewidths=0.6, zorder=3)
```

> - `facecolors='none'` = 속이 빈 원(○)으로 표시
> - 같은 축에 filled(●)와 empty(○)를 겹쳐 2종류 데이터 구분
> - 사용처: ax6(AvgV), ax4(MK DCIR의 1s Pulse)

### 5.3 graph_cycle_base() — 축 설정 (L2528–2542)

```python
def graph_cycle_base(x_data, ax, lowlimit, highlimit, y_gap, xlabel, ylabel, xscale, overall_xlimit):
    if xscale != 0:
        xrangemax = xscale
        # X축 눈금 간격 자동 계산 (50 단위)
        xrangegap = ((xlimit >= 400) + (xlimit >= 800) + ... + 1) * 50
        # 눈금이 7개 이하가 되도록 조정
        while xrangemax / xrangegap > 7:
            xrangegap += 50
        ax.set_xticks(np.arange(0, xrangemax + xrangegap, xrangegap))
        ax.set_xlim(-xrangemax * 0.02, xrangemax * 1.02)
        # xlim: 좌우에 2% 여백
    if highlimit != 0:
        ax.set_yticks(np.arange(lowlimit, highlimit, y_gap))
        ax.set_ylim(lowlimit, highlimit)
```

> **X축 눈금 알고리즘**:
> ```
> xscale=1200일 때:
>   xlimit >= 400 → +50, >= 800 → +50, >= 1500 → 안됨
>   xrangegap = (1+1+0+0+0+1) × 50 = 150
>   xticks: 0, 150, 300, 450, 600, 750, 900, 1050, 1200
>   (9개 > 7개이므로)
>   while: xrangegap → 200
>   xticks: 0, 200, 400, 600, 800, 1000, 1200 (7개, OK)
> ```

---

## 6. 데이터 → 그래프 매핑 요약

| 서브플롯 | X | Y (df.NewData) | 스타일 | Y 기본 범위 | 🔋 열화 해석 |
|---------|---|----------------|--------|------------|-------------|
| ax1 | index | Dchg | ● filled | 사용자 설정 | ↓ = 용량 열화 |
| ax2 | index | Eff | ● filled | 0.992–1.004 | ↓ = 부반응 증가 |
| ax3 | index | Temp | ● filled | 0–50°C | ↑ = 발열 증가 |
| ax4 | index | dcir / soc70_* | ● + ○ + 선 | 0–120mΩ | ↑ = 저항 증가 |
| ax5 | index | Eff2 | ● filled | 0.996–1.008 | ↓ = 가역 손실 |
| ax6 | index | RndV(●) + AvgV(○) | ● + ○ | 3.0–4.0V | RndV↓ 또는 AvgV↓ = 열화 |

---

## 7. 보조 함수: 라벨 배치

### place_avgrest_labels(ax6) — L2624–2663

ax6에 그려진 RndV(●)와 AvgV(○) 클러스터의 **중앙값 사이**에 구분선을 그리고
"Avg V" / "Rest V" 텍스트를 배치한다.

```
  4.18 ── RndV ●●●●●●●●●●●●●●●●●
                                         Rest V  ← 텍스트
  4.08 ── ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   ← 구분선 (midline)
                                         Avg V   ← 텍스트
  3.72 ── AvgV ○○○○○○○○○○○○○○○○○
```

### place_dcir_labels(ax4) — L2665+

MK DCIR 모드에서 RSS(●)와 1s Pulse(○) 클러스터에 각각
"Rss@SOC70%" / "DCIR1s@SOC70%" 라벨을 배치한다.

---

## 8. 학습 체크리스트

- [ ] 6개 서브플롯 각각이 어떤 물리량을 보여주는지 설명할 수 있는가?
- [ ] filled(●) vs empty(○) scatter의 사용 구분을 말할 수 있는가?
- [ ] MK DCIR 모드에서 ax4에 4개 요소(RSS●, 1s○, RSS선, 1s점선)가 그려지는 이유를 설명할 수 있는가?
- [ ] ax6에서 RndV와 AvgV의 차이가 물리적으로 무엇을 의미하는지 설명할 수 있는가?
- [ ] 색상 순환(`colorno % 10`)이 왜 필요한지 (다중 셀 오버레이) 설명할 수 있는가?
- [ ] `graph_cycle_base()`의 X축 눈금 알고리즘을 xscale=2000으로 직접 계산해볼 수 있는가?

---

## 다음 학습

- [[260409_study_05_df_newdata_deep_dive|Study 05: df.NewData 컬럼별 물리적 의미 심화]]
