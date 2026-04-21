---
date: 2026-04-09
tags: [python, BDT, 코드학습, 사이클데이터, DataFrame, 배터리물리, 열화]
aliases: [df_newdata, NewData컬럼분석]
---

# df.NewData 컬럼별 물리적 의미 심화

> **학습 목표**: `df.NewData`의 각 컬럼이 **전기화학적으로 무엇을 의미**하는지,
> **정상 범위와 이상 패턴**을 어떻게 판별하는지, 그리고 **열화 메커니즘과의 연결**을 체화한다.

**대상**: `df.NewData` DataFrame (Toyo/PNE 공통 + MK DCIR 확장)  
**선행 학습**: [[260409_study_01_cycle_data_pipeline_overview|Study 01]]–[[260409_study_04_graph_output_cycle|Study 04]] 전체

---

## 1. df.NewData 전체 구조

```python
# 공통 컬럼 (Toyo + PNE 모두)
df.NewData.columns = [
    "Cycle",    # 사이클 순번 (1, 2, 3, ...)
    "Dchg",     # 방전 용량 ratio
    "Chg",      # 충전 용량 ratio
    "Eff",      # 쿨롱 효율
    "Eff2",     # 교차 효율
    "RndV",     # Rest End Voltage (V)
    "Temp",     # 온도 (°C)
    "AvgV",     # 평균 방전 전압 (V)
    "DchgEng",  # 방전 에너지 (mWh)
    "OriCyc",   # 원본 사이클 번호
    "dcir",     # DCIR (mΩ)
    "ChgVolt",  # 충전 상한 전압 (V)
    "ChgSteps", # 충전 스텝 수
]

# PNE MK DCIR 확장 컬럼
+ "dcir2"          # 1s Pulse DCIR (mΩ)
+ "soc70_dcir"     # SOC70% 1s Pulse DCIR (mΩ)
+ "soc70_rss_dcir" # SOC70% RSS DCIR (mΩ)
+ "rssocv"         # RSS 후 Rest OCV (V)
+ "rssccv"         # RSS CC 종료 전압 (V)

# PNE 추가 컬럼
+ "DchgVolt"       # 방전 하한 전압 (V)
+ "DchgCurr"       # 방전 전류 (A)
```

---

## 2. 컬럼별 심화 분석

### 2.1 Cycle — 사이클 순번

| 항목 | 내용 |
|------|------|
| **계산 방법** | `range(1, len(df.NewData) + 1)` (순번) 또는 `cycle_map` 기반 논리번호 |
| **물리적 의미** | 충방전 반복 횟수. 수명시험의 X축 기본 단위 |
| **정상 범위** | 1 ~ 수천 (일반 수명시험), 1 ~ 수만 (저율 사이클) |
| **주의점** | `Cycle` ≠ `OriCyc`. DCIR/RPT 스텝이 끼면 OriCyc가 더 크다 |

> 🔋 **Cycle vs OriCyc**:
> ```
> Cycle:  1, 2, 3, 4, 5, ... (df.NewData 순번, 연속)
> OriCyc: 3, 8, 13, 18, 23, ... (실제 Toyo TotlCycle, 비연속)
>                                 → DCIR/Rest 스텝이 사이에 있음
> ```

---

### 2.2 Dchg — 방전 용량 비 (Discharge Capacity Ratio)

| 항목 | 내용 |
|------|------|
| **계산** | Toyo: `Cap[mAh] / mincapacity`, PNE: `DchgCap(μAh) / mincapacity / 1000` |
| **단위** | 무차원 (0~1.0+). 그래프에서는 ×100 = % |
| **물리적 의미** | 기준 용량 대비 현재 방전 가능 용량의 비율 |
| **정상 범위** | 초기 0.98~1.02, 점진적 감소 |
| **이상 패턴** | |

```
정상 열화:    ●●●●●●●●●●●●●●●
              1.00 → 0.98 → 0.96 → ... (서서히 감소)

무릎점(knee): ●●●●●●●●●●
                            ●●
                              ●●
                                ●● (갑자기 가속)

회복(RPT후):  ●●●●●
                    ●  ← RPT 후 일시적 상승
                    ●●●●● (다시 감소 추세)

초기 활성화:  ●
              ●●
                ●●●●●●●● (초기 2~3사이클 약간 증가 → 정상)
```

> 🔋 **Dchg > 1.0이 가능한 이유**:
> 기준 용량은 첫 사이클 또는 경로명에서 추출한 공칭 용량이다.
> 실제 용량이 공칭보다 높으면(설계 여유 등) 초기 Dchg > 1.0이 된다.

---

### 2.3 Chg — 충전 용량 비

| 항목 | 내용 |
|------|------|
| **계산** | Dchg와 동일 방식이나 충전 방향 |
| **물리적 의미** | 셀에 주입된 전하량의 비율 |
| **Dchg와의 관계** | 항상 `Chg ≥ Dchg` (정상 셀) |
| **차이(Chg - Dchg)의 의미** | = 비가역 용량 손실 (SEI 형성, 부반응) |

> Chg만 단독으로 보는 경우는 드물고, Eff = Dchg/Chg로 간접 분석.

---

### 2.4 Eff — 쿨롱 효율 (Coulombic Efficiency)

| 항목 | 내용 |
|------|------|
| **계산** | `Dchg / Chg` (같은 사이클) |
| **단위** | 무차원 (0.99~1.00) |
| **물리적 의미** | 충전한 리튬 중 방전으로 회수된 비율 |
| **정상 범위** | 0.995~0.9999 (건강한 셀) |

#### 이상 값 해석

| Eff 값 | 의미 | 가능한 원인 |
|--------|------|------------|
| 0.999~1.000 | 매우 건강 | SEI 안정화 완료 |
| 0.995~0.999 | 정상 | 통상적 SEI 성장 |
| 0.990~0.995 | 주의 | 가속 열화 초기, 부반응 증가 |
| < 0.990 | 이상 | 리튬 석출, 내부 단락, 전해액 분해 |
| > 1.000 | 측정 이상 | 불완전 CV, 자가방전 영향, 접촉 불량 |

> 🔋 **Eff의 물리학**:
> $$CE = \frac{Q_{discharge}}{Q_{charge}} = 1 - \frac{Q_{lost}}{Q_{charge}}$$
> $Q_{lost}$ = SEI 성장 + 리튬 석출 + 전해액 분해로 소모된 리튬

---

### 2.5 Eff2 — 교차 효율

| 항목 | 내용 |
|------|------|
| **계산** | `Chg(n+1) / Dchg(n)` (사이클 간) |
| **물리적 의미** | 방전 후 다음 충전에서 얼마나 복구되는지 |
| **Eff와의 차이** | Eff는 사이클 내, Eff2는 사이클 간. Rest 효과 포함 |
| **정상 범위** | 0.998~1.005 |

> 🔋 **Eff2 > 1.0의 물리적 해석**:
> 방전 후 Rest 시간 동안 전극 내 농도 구배가 완화되면,
> 다음 충전에서 이전 방전보다 더 많은 리튬을 넣을 수 있다.
> 이는 "회복 효과"이며 정상적인 현상이다.

---

### 2.6 RndV — Rest End Voltage (= 근사 OCV)

| 항목 | 내용 |
|------|------|
| **계산** | Toyo: `chgdata["Ocv"]` (충전 직전 Rest 전압), PNE: `pivot_data["Ocv"][3] / 1e6` (휴지 최소) |
| **단위** | V |
| **물리적 의미** | 충전 완료 후 안정화된 전압 ≈ 만충 OCV |
| **정상 범위** | NMC: 4.15~4.20V, LFP: 3.35~3.45V |

> 🔋 **RndV ≠ 정확한 OCV**:
> 진정한 OCV는 무한 시간 Rest 후의 전압이지만, 실제 시험에서는 10분~1시간 Rest만 부여.
> 따라서 RndV는 OCV의 **근사값**이며, Rest 시간이 짧을수록 OCV보다 높게 측정된다.
> 
> **RndV 감소 = 열화 신호**:
> 동일 SOC에서 OCV가 낮아진다 = 활물질의 열역학적 특성 변화 (LAM) 또는 LLI

---

### 2.7 Temp — 방전 최고 온도

| 항목 | 내용 |
|------|------|
| **계산** | Toyo: `PeakTemp[Deg]`, PNE: `Temp(m°C) / 1000` |
| **단위** | °C |
| **물리적 의미** | 방전 중 셀 표면/내부 최고 온도 |
| **기대값** | 항온 챔버 설정온도 ± 2°C |

> 🔋 **온도가 중요한 이유**:
> - 모든 전기화학 반응은 온도에 지수적으로 의존 (Arrhenius)
> - 10°C 상승 → 열화 속도 ~2배
> - BDT 현황 탭의 색상 코드: 15°C(파랑), 23°C(검정), 35°C(보라), 45°C(빨강)

---

### 2.8 AvgV — 평균 방전 전압

| 항목 | 내용 |
|------|------|
| **계산** | Toyo: `Pow[mWh] / Cap[mAh]`, PNE: `DchgEng / Dchg / mincapacity * 1000` |
| **단위** | V |
| **물리적 의미** | 방전 전체 구간의 가중 평균 전압 |
| **물리 공식** | $V_{avg} = \frac{E_{discharge}}{Q_{discharge}} = \frac{\int V \cdot I \, dt}{\int I \, dt}$ |

> 🔋 **AvgV 감소의 의미**:
> $$V_{avg} = OCV_{avg} - \overline{\eta} - \overline{I \cdot R}$$
> AvgV 감소 = 과전압(η) 증가 + 옴 손실(IR) 증가 = **내부 저항 증가**
> 
> AvgV는 DCIR보다 **매 사이클 측정 가능**하므로 (DCIR은 주기적 측정),
> 저항 변화의 **연속적 추세**를 파악하는 데 유용하다.

---

### 2.9 DchgEng — 방전 에너지

| 항목 | 내용 |
|------|------|
| **계산** | Toyo: `Pow[mWh]`, PNE: `DchgEngD(μWh) / 1000` |
| **단위** | mWh |
| **물리적 의미** | 방전 시 실제 사용 가능한 에너지 |
| **Dchg와의 관계** | `DchgEng = Dchg × AvgV × mincapacity` (근사) |

> 🔋 **에너지 vs 용량**:
> 에너지 열화가 용량 열화보다 빠른 이유:
> - 용량 감소 + 전압 감소가 곱해지기 때문
> - $E = Q \times V_{avg}$: Q가 5% 감소하고 V가 3% 감소하면 E는 ~8% 감소

---

### 2.10 dcir / dcir2 / soc70_dcir / soc70_rss_dcir — DCIR 계열

| 컬럼 | 측정 방법 | 포함 저항 | 사용 모드 |
|------|----------|----------|----------|
| `dcir` | Toyo: 프로필 파일 ΔV/ΔI, PNE: imp/1000 또는 RSS | 전체 또는 RSS | 모든 모드 |
| `dcir2` | PNE: 1s Pulse ΔV/ΔI | 옴 + 빠른 CT | MK DCIR만 |
| `soc70_dcir` | dcir2에서 SOC70% 추출 | 옴 + 빠른 CT @SOC70% | MK DCIR만 |
| `soc70_rss_dcir` | dcir에서 SOC70% 추출 | 전체 @SOC70% | MK DCIR만 |

#### DCIR 계층 구조

```
전체 DCIR (RSS, soc70_rss_dcir)
├── 옴 저항 (R₀)          ─┐
├── 전하이동 저항 (R_ct)    ├── 1s Pulse DCIR (soc70_dcir)
└── 확산 저항 (R_diff)     ─┘  ← 이 부분만 차이

따라서: RSS - Pulse = 확산 저항 성분
```

> 🔋 **DCIR 증가 메커니즘별 해석**:
> | 증가 패턴 | 주요 원인 |
> |----------|----------|
> | R₀ 증가 (Pulse ↑) | SEI 두께 증가, 접촉 저항 증가, 전해액 열화 |
> | R_diff 증가 (RSS-Pulse 차이 ↑) | 입자 균열, 기공 폐쇄, 전해액 건조 |
> | 전체 급등 | 내부 단락 직전, 심각한 LAM |

---

### 2.11 ChgVolt / ChgSteps — 충전 패턴 추적

| 항목 | 내용 |
|------|------|
| **ChgVolt** | 해당 사이클의 충전 상한 전압 (V) |
| **ChgSteps** | 해당 사이클의 충전 스텝 수 |
| **용도** | RPT 사이클 vs 수명시험 사이클 구분 |

> 🔋 **RPT 구분 활용**:
> ```
> 수명시험 사이클: ChgVolt=4.20V, ChgSteps=2 (CC+CV)
> RPT 사이클:     ChgVolt=4.20V, ChgSteps=4 (저율 CC+CV+방전+CC+CV)
> ```
> ChgSteps가 갑자기 바뀌면 → 패턴이 전환된 지점 (수명→RPT 또는 그 반대)

---

## 3. 열화 시나리오별 df.NewData 패턴

### 시나리오 A: 정상 열화 (SEI 지배)

```
Dchg:  1.00 → 0.99 → 0.98 → 0.97 (√n 형태의 완만한 감소)
Eff:   0.998 → 0.999 → 0.9995 (초기 감소 후 안정화)
DCIR:  30 → 32 → 35 → 38 mΩ (완만한 증가)
AvgV:  3.72 → 3.71 → 3.70 V (미세 감소)
```

### 시나리오 B: 무릎점(Knee) 발생

```
Dchg:  1.00 → 0.95 → 0.92 → 0.85 → 0.70 → 0.50 (갑작스러운 가속)
Eff:   0.999 → 0.998 → 0.995 → 0.990 → 0.980 (효율 급락)
DCIR:  30 → 35 → 50 → 80 → 150 mΩ (저항 폭증)
RndV:  4.18 → 4.17 → 4.15 → 4.10 V (OCV 급락)
```

> 원인: LLI 누적 → 음극 stoichiometry가 위험 영역 진입 → 리튬 석출 캐스케이드

### 시나리오 C: 온도 이상

```
Temp:  23 → 23 → 25 → 30 → 35 (점진적 상승)
Dchg:  1.00 → 0.99 → 0.96 → 0.90 (가속 열화)
Eff:   0.999 → 0.998 → 0.995 (동반 감소)
```

> 원인: 챔버 온도 제어 이상 또는 셀 내부 발열 증가 (내부 단락 초기 징후 가능)

---

## 4. df.NewData → DB (cycle_summary) 매핑

| df.NewData | DB 컬럼 | 변환 |
|:-----------|:--------|:-----|
| Dchg | dchg_ratio | 그대로 |
| Chg | chg_ratio | 그대로 |
| Eff | eff | 그대로 |
| Eff2 | eff2 | 그대로 |
| RndV | rest_voltage | 그대로 |
| AvgV | avg_voltage | 그대로 |
| Temp | temperature | 그대로 |
| DchgEng | dchg_energy | 그대로 |
| dcir | dcir | 그대로 |
| dcir2 | dcir2 | 그대로 |
| soc70_dcir | soc70_dcir | 그대로 |
| OriCyc | ori_cycle | 그대로 |

> 참고: DB 스키마는 `database.instructions.md`에 정의. Phase 1에서 구현 예정.

---

## 5. 물리적 검증 규칙 요약

BDT에서 데이터 품질을 자동 검증할 때 적용해야 하는 규칙:

| 검증 항목 | 조건 | 위반 시 의미 |
|----------|------|-------------|
| Dchg > 0 | 항상 | 계산 오류 |
| Dchg ≤ 1.1 | 통상 | 기준 용량 설정 오류 가능 |
| 0 < Eff < 1.01 | 통상 | Eff > 1.01 = 불완전 CV 또는 접촉 불량 |
| dcir > 0 | DCIR 존재 시 | 음수 DCIR = 측정 오류 |
| dcir < 500 | 통상 | 500mΩ 초과 = 내부 단락 또는 접촉 불량 |
| 2.0 ≤ RndV ≤ 4.5 | NMC | 범위 초과 = 전압 측정 이상 |
| 0 ≤ Temp ≤ 80 | 정상 시험 | 범위 초과 = 열폭주 또는 센서 이상 |
| Dchg[n] ≤ Dchg[n-1] × 1.05 | 연속 사이클 | 급격한 증가 = RPT 효과 또는 이상 |

---

## 6. 학습 체크리스트

- [ ] df.NewData의 15+ 컬럼 각각의 물리적 의미를 1문장으로 설명할 수 있는가?
- [ ] Eff = 0.993인 셀의 1000사이클 후 예상 용량 손실을 추정할 수 있는가?
- [ ] RSS DCIR과 1s Pulse DCIR의 차이가 확산 저항임을 전기화학적으로 설명할 수 있는가?
- [ ] RndV가 감소하는 두 가지 원인(LLI, LAM)을 구분할 수 있는가?
- [ ] "무릎점" 패턴을 df.NewData의 Dchg + Eff + DCIR 트렌드로 식별할 수 있는가?
- [ ] Toyo와 PNE의 단위 변환 체인을 각각 정확히 기술할 수 있는가?

---

## 연결 노트

- [[260409_study_01_cycle_data_pipeline_overview|Study 01: 파이프라인 개요]]
- [[260409_study_02_toyo_cycle_data|Study 02: Toyo 라인별 분석]]
- [[260409_study_03_pne_cycle_data|Study 03: PNE 라인별 분석]]
- [[260409_study_04_graph_output_cycle|Study 04: 그래프 플로팅]]
- [[Electrochemical_parameter|전기화학 기본 성질]] (vault)
- [[충방전_매커니즘|충방전 메커니즘]] (vault)
- [[DCIR_측정_업체별|DCIR 측정 방법]] (vault)
