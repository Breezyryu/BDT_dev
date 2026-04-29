---
title: "개발 설계변수 × 모델링 파라미터 정리 보고서"
date: 2026-04-22
tags: [report, cell-design, pybamm, parameters, mapping, modeling]
type: report
status: active
aliases:
  - 설계변수 모델링 파라미터 보고서
  - Cell Design × PyBaMM 매핑 보고서
related:
  - "[[Cell_Design_Specification_필드]]"
  - "[[260422_analysis_pybamm_key_parameters]]"
  - "[[PyBaMM_Variables_PPT]]"
  - "[[합제밀도와_전류밀도]]"
  - "[[충방전_매커니즘]]"
  - "[[MX배터리그룹_평가항목]]"
  - "[[전해액]]"
  - "[[Silicon]]"
author: 선행BatteryLab
scope: BDT + PyBaMM 시뮬레이션 연동
created: 2026-04-22
slide: true
marp: true
---

# 개발 설계변수 × 모델링 파라미터 정리 보고서

> **개발부서의 실무 설계 knob 과 PyBaMM 모델링 파라미터를 단일 프레임으로 매핑하고, 변환에 내재한 단순화 가정과 유효 범위를 명시하는 보고서**
>
> 작성: 선행BatteryLab · 2026-04-22

---

## 📋 목차

1. **Executive Summary** — 한 페이지 요약
2. **배경 및 문제 정의** — 왜 이 정리가 필요한가
3. **개발 설계변수 전체 스캔** — Cell Design Spec 7대 분류 × 63 필드
4. **모델링 파라미터 전체 스캔** — PyBaMM 8대 카테고리 × ~70 파라미터
5. **양방향 매핑** — 설계변수 ↔ PyBaMM (Category A/B/C/D)
6. **PyBaMM 커버리지 분석** — 직접 27% / 간접 32% / 범위 밖 41%
7. **변환 가정 A1~A8** — 왜 가정이 보고의 중심이어야 하는가
8. **Key Parameter 14** — Rate-determining × 개발 설계의 공통 집합
9. **개발 프로세스 단계별 활용** — EA / PA / Proto / MP / CA 별 시뮬 역할
10. **한계와 향후 확장** — 현재 PyBaMM 1D 가 못 다루는 영역
11. **결론 및 권고**
12. **부록** — 상세 매핑표, 관련 문서 링크

---

# 1. Executive Summary

## 1.1 한 페이지로 보는 결론

> **시뮬은 실제 셀의 모든 물리를 담지 못한다. 설계변수를 모델 파라미터로 변환하는 모든 식은 단순화 가정의 집합이며, 그 가정의 유효 범위 안에서만 의사결정에 쓸 수 있다.**

### 핵심 수치

| 지표 | 값 |
|------|:--:|
| Cell Design Spec 필드 수 | **63** (7대 분류) |
| PyBaMM 입력 파라미터 | **~70** (8대 카테고리) |
| **직접 변환 가능 (Category A)** | **27 %** (17/63) |
| **가정 거친 간접 변환 (Category B)** | **32 %** (20/63) |
| **PyBaMM 범위 밖 (Category D)** | **41 %** (26/63) |
| 이중 관점 핵심 파라미터 (Tier S + A) | **14 개** |
| 핵심 변환 가정 (A1 ~ A8) | **8 개** |

### 핵심 메시지 5

1. **설계 = 시뮬 + α** — Design Spec 의 41% 는 시뮬 범위 밖 (파우치·기구·공정·업체·코팅 구조). 시뮬은 전체의 일부 관점일 뿐이다.
2. **이중 관점 일치하는 knob 14개** — Rate-determining 이론과 셀 개발 실무가 **동시에 중요**하다고 지목한 파라미터. 여기에 리소스 집중.
3. **변환은 가정의 집합** — 합제밀도 → 체적분율, D50 → 입자반경 등 모든 변환에 A1~A8 가정이 내재. 보고서에 **변환식 + 가정 + 유효범위 + 파탄지표 + 대안** 5요소를 명시해야 한다.
4. **첨가제·bi-modal 입자는 현재 gap** — FEC, LiDFOB 등 전해액 첨가제와 대/소립자 혼합은 PyBaMM 1D 직접 키 없음. SEI/plating kinetic 역피팅 + MPM 확장으로 보완.
5. **개발 단계마다 시뮬 역할이 다르다** — EA 에서는 목표 설정, PA 에서는 Design Spec 검증, Proto 에서는 파라미터 교정, MP 에서는 공정 편차 영향, CA 에서는 수명 예측.

---

# 2. 배경 및 문제 정의

## 2.1 왜 이 정리가 필요한가

BDT 프로젝트에 PyBaMM 시뮬레이션이 연동되면서, **개발부서 사양서와 시뮬 입력 사이의 변환 경로** 가 반복적으로 작업되고 있다. 그 과정에서:

- 동일한 개발 변수를 서로 다른 변환 공식으로 넣는 경우
- 변환에 쓴 가정이 문서화되지 않아 Δ 가 났을 때 원인 역추적 불가
- Cell Design Spec 의 어떤 필드는 시뮬로 확인 가능하고 어떤 필드는 불가한지 모호
- 첨가제·bi-modal 입자처럼 실무 중요도는 높으나 시뮬 직접 입력 불가한 변수 구분 부족

이 보고서는 이를 **단일 프레임**으로 정리한다.

## 2.2 프레임워크

```
┌────────────────────────────────────────────────────────┐
│           개발 설계변수 (Cell Design Spec)               │
│              7대 분류 × 63 필드                          │
└────────────────────┬───────────────────────────────────┘
                     │
                     ▼  Category A/B/C/D 분류
             ┌───────────────────┐
             │  Category A  27%  │ 직접 변환 (단위만)
             │  Category B  32%  │ 가정 A1~A8 통한 변환
             │  Category C      │ 검증용 (시뮬 결과 vs 실측)
             │  Category D  41%  │ PyBaMM 범위 밖
             └───────┬───────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│              모델링 파라미터 (PyBaMM)                    │
│                8대 카테고리 × ~70                        │
└────────────────────┬───────────────────────────────────┘
                     │
                     ▼  Rate-determining × 개발 설계 이중 관점
               Tier S(8) + A(6) = Key 14
```

---

# 3. 개발 설계변수 전체 스캔

출처: ATL Gen5+ Cell Design Specification (CA03, 250526) 의 표준 필드 스키마.
상세는 [[Cell_Design_Specification_필드]] 참조.

## 3.1 7대 분류 요약

| # | 분류 | 필드 수 | 핵심 knob |
|---|------|:------:|---------|
| 1 | **Cell dimension** | 5 | X/Y max, t at shipping, t at 1st full charge |
| 2 | **Cathode** | 15 | 소재 type/grade, specific capacity, LL, thickness, density(calendering/stack), formulation, tab |
| 3 | **Anode** | 14 | 소재 type (AG/NG/Si mixture), specific capacity, LL, thickness, density, formulation, tab |
| 4 | **Separator** | 13 | base 재료·두께 + 1st/2nd side × 1st/2nd layer 코팅 구조 |
| 5 | **Electrolyte** | 6 | 용매·첨가제·조성비·주액량 (g/Ah)·Molarity |
| 6 | **Pouch or CAN** | 5 | 두께, 업체, Side folding, Forming type/R |
| 7 | **Others** | 5 | Energy density (Fresh/EOL/SEU), Current density, J/R, N/P ratio, Weight |
|   | **메타** | 8 | Vendor, Project, Model, Type (Winding/Stack), Avg. Voltage, Capacity 3종 |
|   | **합계** | **63** | |

## 3.2 Spec 2.1 (Cathode Type) 화학계별 물성 테이블

> Spec 2.1 `Type of active material` 은 "NCM or else" 같은 범주형 필드이지만, 화학계에 따라 **PyBaMM 파라미터 값이 크게 다르다** (c_max, OCP 함수, voltage cut-off, D_s 범위). 따라서 본 필드의 선택은 5장 매핑 테이블 전체의 **프리셋 교체** 를 의미한다.
> 출처: [[양극별_특성]].

| Formula | 이론 용량 (mAh/g) | Half cell (mAh/g) | 충전 V | 작동 V | Press density (g/cc) | 부피 용량 (mAh/cc) | PyBaMM 시사 |
|---------|:------------:|:-----------:|:----:|:----:|:---------------:|:--------------:|----------|
| **LiCoO₂** (LCO) | 274 | 160 | 4.2 | 3.8 | **3.7** | 590 | 고밀도, 저 D_s, Cobalt cost ↑ |
| **LiNi₀.₉Co₀.₁O₂** (Ni-rich) | 274 | 202 | 4.2 | 3.5 | 3.2 | 646 | 고용량, 양극 표면 안정성 issue |
| **LiNi₀.₈Co₀.₁Mn₀.₁O₂** (NMC811) | 274 | 185 | 4.2 | 3.5 | 3.2 | 592 | 고에너지밀도, Ni-rich 계열 |
| **LiNi₀.₅Co₀.₂Mn₀.₃O₂** (NMC523) | 274 | 170 | 4.2 | 3.5 | 3.2 | 557 | 균형형, Chen2020 대표 |
| **LiNi₀.₈Co₀.₁₅Al₀.₀₅O₂** (NCA) | 274 | 183 | 4.2 | 3.5 | 3.2 | 586 | Al doping, Tesla 계열 |
| **LiNi₁/₃Co₁/₃Mn₁/₃O₂** (NMC111) | 274 | 156 | 4.2 | 3.7 | 3.1 | 487 | 고전압 안정, 저용량 |
| **LiNi½Mn½O₂** | 280 | 195 | **4.6** | 3.7 | 3.1 | 605 | 고전압 NMC 계열 (Co-free) |
| **LiMnO₂** | 285 | 230 | 4.2 | 3.2 | 2.8 | 644 | Co-free, 구조 불안정 |
| **LiMn₂O₄** (LMO) | 148 | 100 | 4.2 | 4.0 | 2.8 | 280 | 저용량, 안전성 ↑ |
| **LiNi₀.₅Mn₁.₅O₄** (LNMO) | 147 | 120 | **5.0** | 4.7 | 2.8 | 336 | 차세대 고전압 |
| **LiCoPO₄** (LCP) | 167 | 70 | 5.0 | 4.6 | 2.7 | 189 | 연구용, 전해액 한계 |
| **LiFePO₄** (LFP) | 170 | 140 | 3.8 | 3.4 | **2.0** | 280 | **2상 공존 → Fickian 부적합 (가정 A2)** |

### 3.2.1 PyBaMM 파라미터 변환에의 함의

| 화학계 | `Maximum concentration` (c_max, mol/m³) | `Upper voltage cut-off` [V] | D_s 범위 (m²/s) | 주의 가정 |
|-------|:--------------------------------:|:---------------------:|:---------------:|---------|
| **LCO (표준)** | ~51,500 | 4.2 | 10⁻⁹ ~ 10⁻¹¹ | A3 표준 |
| **🎯 Gen5+ 고전압 LCO** | ~51,500 | **4.53 (Gen5+ 타겟)** | 10⁻⁹ ~ 10⁻¹¹ (고전압에서 급락) | **A3+A4 재튜닝, LAM_pe 가속, CEI/O₂ evolution** |
| NMC622 | ~63,000 | 4.2 | 10⁻¹⁰ ~ 10⁻¹² | A3 표준 (Chen2020 프리셋 해당) |
| NMC811 | ~65,000 | 4.2 | 10⁻¹⁰ ~ 10⁻¹² | A3 표준 (OKane2022 해당) |
| NCA | ~63,000 | 4.2 | 10⁻¹⁰ ~ 10⁻¹² | Al doping 반영 함수형 |
| LNMO | ~28,000 | **4.95** | 10⁻¹¹ ~ 10⁻¹³ | 전해액 산화 안정성 별도 |
| **LFP** | ~22,000 | 3.8 | 10⁻¹⁷ ~ 10⁻¹⁸ | **A2 파탄 — MPM 또는 2상 모델 필수** |

### 3.2.2 Gen5+ ATL 실제 화학 조성 (개발 방향)

**선행BatteryLab 확인 조성 (2026-04-22)**:
- **양극**: **고전압 LCO** (LiCoO₂, Spec 상 `Gen5 4.53V 2.0C PF-PTO` · `PF-MP1`)
  - 표준 LCO 는 4.2V cut-off 이지만 **4.53V 까지 고전압 운용** 으로 용량 밀도 ↑
  - 표 상 LCO 이론 274 mAh/g / half-cell 160 @4.2V → 고전압 영역 추가 활용 시 ~190 mAh/g 접근
- **음극**: Graphite 또는 **Graphite + SiC (Silicon-Carbon 복합)**
  - Spec 상 `APG-031 + 5% Si (EPF)` — **Si/Gr blend, Si 5%**
  - 개발 방향: **Si (SiC) 함량 점진적 증가** → 체적 에너지밀도 목표 ↑
- **개발 방향 요약**: 양극 고전압화 (↑ voltage window) + 음극 Si 함량 증가 (↑ specific capacity)

### 3.2.3 고전압 LCO 의 PyBaMM 특화 주의사항

| 물성 | 표준 LCO (4.2V) | Gen5+ 고전압 LCO (4.53V) |
|------|:------------:|:----------------:|
| 작동 x 범위 | 0.5 ~ 1.0 | **0.3 ~ 1.0** (deep delithiation) |
| c_max | ~51,500 mol/m³ | 동일 |
| 고전압 영역 OCP 함수 형상 | 기존 프리셋 커버 | **커버 안 됨 — 재측정 필요** |
| D_s (SOC 의존) | 10⁻⁹ ~ 10⁻¹¹ m²/s | 고전압 영역에서 급락 가능 — GITT 필수 |
| 구조 열화 (layered → spinel-like) | 극소 | **가속 — LAM_pe 지배** |
| 산소 방출 (O₂ evolution) | 없음 | **고전압 부반응 — 전해액 분해 가속** |
| SEI (cathode CEI 포함) | 일반 | **CEI 강화 필요 — FEC/LiDFOB 등 첨가제** |

### 3.2.4 SiC (Silicon-Carbon 복합) 음극 주의사항

**반응식** ([[Silicon]] 참조):
$$\text{SiC} + 4\text{Li}^+ + 4e^- \rightleftharpoons \text{Li}_4\text{C} + \text{Si}$$

순수 Si 대비:
| 물성 | 순수 Si | SiC 복합 |
|------|:----:|:---:|
| 이론 용량 (mAh/g) | 3579 (Li₁₅Si₄) | ~1000~2500 (Si 함량 의존) |
| 체적 팽창 | ~300% | ~100~200% (Carbon matrix 완충) |
| 사이클 수명 | ~50~100cy | 300~800cy (구조에 따라) |
| SEI 안정성 | 취약 | Carbon 계면 → 상대적 안정 |

**PyBaMM 1D 에서의 상태**:
- SiC 복합도 기본적으로 **blend 음극** — 가정 A9 (blend → 단일 유효 음극) 적용
- Si 비율 < 5% 면 Gr 단독 프리셋 + 초기 capacity 보정으로 근사
- Si 비율 > 5% 에서는 **MPM + Si 독립 LAM 축** 필요
- 개발 방향이 "Si 함량 증가" 이므로 **현재는 Gr 근사 OK, 향후 MPM 전환 필수**

### 3.2.5 주의 — 프리셋 재사용의 한계

- PyBaMM 내장 프리셋 중 **LCO 전용은 사실상 없음** (Marquis2019 가 graphite/LiCoO2 지만 오래되고 4.2V 기준)
- Chen2020·OKane2022 등은 **NMC 기반 4.2V 표준** — **고전압 LCO 시뮬에 그대로 쓰면 틀림**
- 필요한 재튜닝:
  - **OCP 함수** — LCO 고전압 영역 (0.3 < x_p < 0.5) 측정 기반 재구성 (반셀 GITT 필수)
  - **c_max, 초기 stoichiometry** — LCO 고전압 운용 window 반영
  - **SEI/CEI kinetic** — 4.53V 특유 산화 분해 반영
  - **LAM_pe factor** — 표준 대비 가속
- **프리셋 선택 자체가 가정** — 화학계 같아도 입자 형상 (potato vs flaky), surface coating (PF-PTO = Phosphate-based), single crystal 여부에 따라 D_s 가 1 order 차이

---

## 3.4 개발 우선순위 Top 10 (MX배터리그룹 평가항목 기준)

[[MX배터리그룹_평가항목]] 과 [[합제밀도와_전류밀도]] 참조.

| 순위 | 변수 | Spec 필드 |
|:---:|-----|---------|
| 1 | 전극 두께 (양/음극) | 2.8 / 3.7 Coating thickness |
| 2 | 합제밀도 (calendering → stack) | 2.9~2.10 / 3.8~3.9 Density |
| 3 | 입자 D50 | 2.3 / 3.3 Characteristics (활물질 특성) |
| 4 | 활물질 비용량 | 2.4~2.6 / 3.4~3.5 Reversible capacity |
| 5 | N/P ratio | 7.4 N/P ratio |
| 6 | 전류밀도 | 7.2 Current Density |
| 7 | 전해액 염 농도 | 5.6 Molarity |
| 8 | 전해액 첨가제 조성 | 5.3~5.4 Additives + formulation |
| 9 | 분리막 두께·기공률 | 4.2 Base thickness + 4.4~4.11 코팅 |
| 10 | 상/하한 전압 | 메타: Avg. Voltage + 전압 범위 |

---

# 4. 모델링 파라미터 전체 스캔

출처: PyBaMM v25.12 기준. 상세 전체 리스트는 [[PyBaMM_Variables_PPT]] 참조.

## 4.1 8대 카테고리 요약

| # | 카테고리 | 대표 파라미터 수 | 예시 |
|---|---------|:--------------:|------|
| A | **Geometry** | 14 | Positive/Negative electrode thickness, Particle radius, Cell dimension |
| B | **Material Properties** | 18 | Conductivity, Porosity, Active material volume fraction, Bruggeman, Density, Specific heat |
| C | **Electrochemistry Kinetics** | 6 | Exchange-current density, Charge transfer coefficient, Double-layer capacity |
| D | **Transport** | 10 | Particle diffusivity, Electrolyte diffusivity/conductivity, Max concentration, Transference number |
| E | **Thermodynamics / OCP** | 8 | Electrode OCP (함수형), OCP entropic change, Voltage cut-off |
| F | **Thermal** | 12 | Ambient temp, Heat transfer coeff, Thermal conductivity, Specific heat |
| G | **Degradation** | 15 | SEI kinetic rate, Plating rate, LAM factor (OKane2022 등 활성화 시) |
| H | **Initial / Boundary** | 6 | Initial conc in electrode, Nominal cell capacity, Current function |
|   | **합계** | **~89 (중복 제외 ~70)** | |

---

# 5. 양방향 매핑 — 설계변수 ↔ PyBaMM

## 5.1 4-Category 분류 체계

| Category | 정의 | 예시 필드 수 |
|----------|------|:----------:|
| **A (Direct)** | Spec 값을 단위만 바꿔 PyBaMM 에 넣음 | 17 |
| **B (Calculated)** | 2개 이상 Spec 필드를 조합하고 **가정 A1~A8** 적용 | 20 |
| **C (Validation)** | PyBaMM 에 직접 입력은 아니지만 시뮬 결과와 비교하는 **검증용 실측** | (Proto OQA 등) |
| **D (Out of Scope)** | PyBaMM 1D 전기화학 모델로는 다룰 수 없는 변수 | 26 |

## 5.2 핵심 매핑 테이블 (Category A+B)

### Geometry·Transport·Kinetics (직접+간접)

| Spec 필드 | PyBaMM 파라미터 | 변환 | Cat | 가정 |
|---------|----------------|------|:---:|:----:|
| 2.8 Coating thickness (pos) | `Positive electrode thickness [m]` | ×1e-6 | A | — |
| 3.7 Coating thickness (neg) | `Negative electrode thickness [m]` | ×1e-6 | A | — |
| 4.2 Base separator thickness | `Separator thickness [m]` | ×1e-6 | A | — |
| 2.15 / 3.14 Width | `Electrode width [m]` | ×1e-3 | A | — |
| 2.9~2.10 Density (calendering→stack) | `Positive electrode active material volume fraction` + `porosity` | ρ·w/ρ_true, 1-ρ/ρ_true | B | **A1** |
| 3.8~3.9 Density (음극) | `Negative ... volume fraction` / `porosity` | 위 동일 | B | **A1** |
| 2.3 / 3.3 D50 (Characteristics) | `Positive/Negative particle radius [m]` | D50/2 × 1e-6 | B | **A2** |
| 2.4~2.5 Specific capacity (양극) + density | `Maximum concentration in positive electrode [mol.m-3]` | Q·3.6·ρ·1e6/F | B | **A3** |
| 3.4~3.5 Specific capacity (음극) | `Maximum concentration in negative electrode [mol.m-3]` | 위 동일 | B | A3 |
| 7.4 N/P ratio | `Initial concentration in positive/negative electrode` 조합 | stoichiometry window | B | **A4** |
| 5.6 Molarity | `Initial concentration in electrolyte [mol.m-3]` | ×1000 | A | — |
| 5.1~5.2 Base solvents + formulation | `Electrolyte diffusivity/conductivity [S.m-1]` 함수형 교체 | Nyman2008, Landesfeind2019 등 | B | **A5** |
| 5.3~5.4 Additives + formulation | `SEI kinetic rate constant` + `Lithium plating kinetic rate constant` | 역피팅 | B | **A6** |
| 5.5 Amount of electrolyte | (직접 키 없음; 고갈 모델 확장 시) | — | D | — |

### System·Environment

| Spec 필드 | PyBaMM 파라미터 | 변환 | Cat | 가정 |
|---------|----------------|------|:---:|:----:|
| Min./Target/OQC Capacity | `Nominal cell capacity [A.h]` | ÷1000 | A | — |
| 7.2 Current density + 면적 | `Current function [A]` | j × W × H × N_layers | B | **A7** |
| Avg. Cell Voltage (화학계 추정) | `Upper/Lower voltage cut-off [V]` | 화학계 매핑 | B | — |
| Ambient 환경 | `Ambient temperature [K]` | °C + 273.15 | A/B | **A8** |
| 7.3 J/R Layer | `Number of electrodes connected in parallel to make a cell` | 적층수 | A | — |
| 4.4~4.11 코팅 구조 | (평균 물성만: `Separator porosity`, `Bruggeman`) | 상세 구조 무시 | B | — |
| 2.11 / 3.10 Substrate thickness | (집전체 저항 부분만, 보통 무시) | 무시 | D | — |

## 5.3 Category C (검증용)

### 5.3.1 기본 Category C (풀셀·사이클 레벨)

| Spec 측정치 | PyBaMM 출력 | 허용 Δ |
|----------|-----------|:-----:|
| OQC Cell Capacity | `Discharge capacity [A.h]` | ±2 % |
| Avg. Cell Voltage (적분) | `Terminal voltage [V]` 적분 평균 | ±10 mV |
| RPT 용량 추이 (Proto04/MP107) | 열화 시뮬 용량 커브 | Trend 일치 |
| DCIR from HPPC (Proto03) | `Resistance [Ohm]` / GITT 기반 | ±15 % |
| 1.5 t max at 1st full charge (스웰링) | **PyBaMM 범위 밖 (Category D)** | — |

### 5.3.2 GITT 기반 **직접 측정** Category C (가정 A2/A3 역검증)

> 위의 기본 검증은 풀셀 스케일 결과 비교. 이것만으로는 **가정 A2/A3 (입자 반경·c_max) 가 맞는지 모른다** — 풀셀이 맞아도 내부 파라미터가 틀렸을 수 있음.
>
> **GITT 반셀 측정**은 Weppner-Huggins 공식으로 **D_s 를 SOC 별로 직접 추출** → PyBaMM 입력과 직접 비교 가능.
>
> 상세 원리: [[260419_GITT_확산계수_추출]], [[GITT]] 참조.

| 실측 항목 | 측정 방법 | PyBaMM 대응 | 허용 Δ | 참고 데이터셋 |
|---------|---------|-----------|:-----:|------------|
| 양극 D_s(SOC) | GITT 반셀 | `Positive particle diffusivity [m²/s]` 함수형 | ±1 order | 251224 M1 ATL Cathode Half |
| 음극 D_s(SOC) — Gr 영역 | GITT 반셀 | `Negative particle diffusivity [m²/s]` | ±1 order | 251224 M1 ATL Anode Half |
| 음극 D_s(SOC) — Si 영역 | GITT 반셀 (저율 C/20) | (MPM 확장 시 독립 축) | 범위 확인 | Si 전용 실측 필요 |
| 양극 dV/dQ 피크 위치 | 반셀 완전 충/방전 | PyBaMM OCP 함수 피크 | SOC ±2 % | 반셀 데이터 |
| 음극 dV/dQ 피크 (Gr stage) | 반셀 완전 방전 | PyBaMM OCP 함수 | SOC ±2 % | 반셀 데이터 |
| c_max 실측 (Q·ρ·3.6/F) | 반셀 이론 capacity + 진밀도 | `Maximum concentration in electrode [mol.m-3]` | Δx < 0.03 | — |
| OCV 히스테리시스 (Si) | 충/방전 양방향 OCV | (히스테리시스 서브모델 필요) | ΔV < 20 mV for Gr; > 100 mV for Si | — |

### 5.3.3 BDT GITT 데이터셋 활용성 (이미 확보)

[[260419_GITT_확산계수_추출]] §5.2:

```
240821 선행랩 Gen4pGr 422mAh GITT          (풀셀 NMC + Gr, 기준 데이터)
250905 M2-SDI open-ca-half 14pi             (양극 반셀)
250905 M2-SDI open-an-half 14pi             (음극 반셀)
251224 박민희 M1 ATL Cathode Half GITT 0.1C  (Gen5+ 인접)
251224 박민희 M1 ATL Anode Half GITT 0.05C   (Gen5+ 인접)
```

Gen5+ ATL 프로젝트는 **M1 ATL Cathode/Anode Half GITT** 가 바로 사용 가능 → **PyBaMM 파라미터의 즉시 검증 루트 확보**.

### 5.3.4 GITT 검증 실패 시 역추적

| 증상 | 파탄 가정 | 대응 |
|------|---------|------|
| D_s > 10⁻⁸ m²/s | 측정 iR 미제거 | 회귀 구간 조정 |
| D_s < 10⁻¹⁸ m²/s | **A2 — Fickian 부적합** (LFP·Si 3상) | MPM 전환, Si 독립 처리 |
| SOC 곡선이 랜덤 | pulse 경계 검출 오류 | BDT 전처리 수정 |
| 양/음극 D_s 반대 크기 | r 입력 오류 | 입자 반경 재확인 |
| Si 영역 비현실적 값 | **A2 + A9 파탄** | Si 전용 MPM + 히스테리시스 |

---

# 6. PyBaMM 커버리지 분석

## 6.1 Spec 분류별 커버리지

| Spec 대분류 | 직접 (A) | 간접 (B) | 범위 밖 (D) | 범위밖 비율 |
|-----------|:------:|:------:|:----------:|:---------:|
| 1. Cell dimension (5) | 0 | 1 | 4 | **80 %** |
| 2. Cathode (15) | 5 | 7 | 3 | 20 % |
| 3. Anode (14) | 5 | 6 | 3 | 21 % |
| 4. Separator (13) | 2 | 2 | 9 | **69 %** |
| 5. Electrolyte (6) | 2 | 3 | 1 | 17 % |
| 6. Pouch or CAN (5) | 0 | 0 | 5 | **100 %** |
| 7. Others (5) | 3 | 1 | 1 | 20 % |
| **합계 (63)** | **17 (27 %)** | **20 (32 %)** | **26 (41 %)** | — |

## 6.2 해석

- **양극·음극 (Cathode/Anode)** 이 시뮬 커버리지 가장 좋음 (직접+간접 80%). 전기화학 모델의 중심.
- **분리막 (Separator)** 은 코팅 구조 세부가 많아 69% 범위 밖. 평균 물성(porosity, Bruggeman)만 반영.
- **Pouch/CAN** 은 100% 범위 밖. 기구·패키지·공정은 PyBaMM 1D 전기화학 모델의 대상이 아님.
- **Cell dimension** 도 80% 범위 밖 — 1D 모델은 단면만 보며 면내 치수 세부 무시.

---

# 7. 변환 가정 A1~A8 — 보고의 중심

> **시뮬은 실제 셀의 모든 물리를 반영할 수 없다. 단순화 가정에 기반해 셀 설계변수와 모델링 파라미터의 관계를 정의하는 것이 핵심이다.**

[[260422_analysis_pybamm_key_parameters]] 섹션 6 참조. 8개 가정의 요약:

| # | 가정 | Spec → PyBaMM 변환 | 유효 범위 | 파탄 지표 |
|---|------|------------------|---------|----------|
| **A1** | 합제밀도 → ε_AM | ρ_press·w_AM/ρ_true | 표준 슬러리·프레스 | 실측 용량 < 97% 이론, 두께 편차 >4μm |
| **A2** | D50 → 단일 r | 단봉 PSD 가정 | 좁은 unimodal | rate curve 이탈 → bi-modal 의심 |
| **A3** | 비용량 → c_max | Q_theor·ρ·3.6/F | 표준 화학계 | stoichiometry Δx > 0.03 |
| **A4** | N/P → 초기 stoichiometry | Formation 후 static | 초기 ~수십 사이클 | dV/dQ 비대칭 이동 |
| **A5** | 전해액 농도·용매 → D_e, κ_e | 함수형 교체 | 1.0~1.35 M | Concentration polarization 급상승 |
| **A6** | 첨가제 → SEI/plating rate | 역피팅 집약 | 단일 첨가제 주효 | 첨가제 조합 간 DCIR 불일치 |
| **A7** | 전류밀도 → Current function | 면내 균일 | 단일 셀, 표준 tab | 면적별 IR 편차 |
| **A8** | 온도 → Ambient (lumped) | 전 셀 단일 | 저·중율, 챔버 | 온도 스프레드 >5℃, 국부 plating |
| **A9** | Blend 음극 (Si+Gr) → 단일 유효 음극 | Si 비율 ≤ 5%, 초기 10 사이클 | **체적팽창 300%, 히스테리시스 150~300 mV, crosstalk, 3상 공존** | dV/dQ 에 Si·Gr 피크 독립 이동, knee < 300cy |

> **A9 는 Gen5+ ATL (APG-031+5%Si EPF) 에서 A1 (ε_AM)·A2 (단일 r)·A3 (c_max) 를 동시에 흔드는** 특이 가정이다. Si 체적팽창, 전압 히스테리시스, Li⁺ crosstalk 는 PyBaMM 기본 DFN 이 담지 않는 물리이므로 **MPM + 히스테리시스 서브모델 + stress coupling** 확장 필요. 상세: [[260422_analysis_pybamm_key_parameters]] §6.6 (Si 음극 특화 가정 파탄 시나리오) + [[Silicon]] 문헌 12편.

### 변환 5요소 문서화 원칙 (권장)

**모든 Spec → PyBaMM 변환에 다음을 명시**:

1. **변환식** — 수식
2. **내재 가정** — 어떤 물리를 버리는지
3. **유효 범위** — 화학계·C-rate·온도·사이클 수
4. **파탄 지표** — 실측 신호로 가정이 깨졌음을 알 수 있는 것
5. **대안 경로** — 깨질 때 어떤 서브모델·실측으로 보강

이 원칙을 지키면 시뮬은 **실측과 함께 진화**한다. 안 지키면 "잘 맞을 때만 쓰는 장난감"이 된다.

---

# 8. Key Parameter 14 — 이중 관점 공통 집합

## 8.1 선별 논리

두 관점 Top 10 을 교차 집계:

- **관점 A (Rate-determining)**: 전체 시스템 속도를 지배하는 가장 느린 단계
- **관점 B (Cell Design)**: R&D 현장이 실제로 돌릴 수 있는 knob

## 8.2 Tier S — 두 관점 모두 Top 10 (8개)

| 파라미터 | Rate 순위 | 개발 순위 |
|--------|:--------:|:-------:|
| `Negative particle radius` (r_n) | 1 | 3 |
| `Negative particle diffusivity` (D_s,n) | 2 | (소재) |
| `Positive particle radius` (r_p) | 4 | 3 |
| `Positive particle diffusivity` (D_s,p) | 5 | (소재) |
| `Electrolyte diffusivity` (D_e) | 6 | 7 |
| `Electrolyte conductivity` (κ_e) | 7 | 7 |
| `Ambient temperature` | 10 | 환경 |
| `Negative electrode OCP` (U_n) | 3 | (소재) |

## 8.3 Tier A — 한 관점 Top 10 + 다른 관점 강영향 (6개)

| 파라미터 | 대표 관점 | 다른 관점 연결 |
|--------|---------|-------------|
| `Electrode thickness (pos/neg)` | 개발 1위 | 전해질 수송 강영향 |
| `Active material volume fraction` | 개발 2위 (합제밀도) | 고상전도 ↔ 전해질 경쟁 |
| `Maximum concentration in electrode` | 개발 4위 (비용량) | 양극 Ds 구배·OCV 기울기 |
| `Initial electrolyte concentration` | 개발 7위 | 전해질 ④ 비선형 최적점 |
| `Current function` | 개발 6위 | 모든 단계 과전압 스케일 |
| `Voltage cut-off` | 개발 10위 | 양극/음극 damage 한계 |

## 8.4 핵심 관찰

- **음극 입자 반경**이 두 관점 모두 최상위 — **시뮬 ↔ 개발 피드백의 중심 knob**
- **합제밀도는 trade-off** — 고상전도 ↑ vs 전해질 수송 ↓, 최적점 존재
- **N/P ratio는 열역학적 방어** — Rate 자체는 아니지만 Li plating 안전 마진
- **첨가제·bi-modal 입자는 gap** — 별도 보완 경로 필수

---

# 9. 개발 프로세스 단계별 시뮬 활용

Gen5+ ATL 프로젝트 단계 (raw/g5p_at/) 기준.

| 단계 | 문서 대표 | 시뮬 역할 | 주 활용 파라미터 | 시뮬 한계 |
|------|---------|---------|--------------|---------|
| **EA** Evaluation Approval | EA03 과제계획서, EA01 Cell Pack Proposal | 목표 capacity·energy·수명 feasibility 탐색 | 개발 목표 sweep (전극 두께, 입자 크기, 전해액 농도) | 소재 불확정 → 프리셋 기반 |
| **PA** Plan Approval | PA01 Cell Design Spec 초안, PA02 DFMEA 초안, PA05 신규 소재검토서 | Design Spec 초안 값으로 율특성·온도 영향 **사전 검증** | Category A+B 전체 | 첨가제·신규 소재 파라미터 미지 |
| **Proto** | Proto02 OQA, Proto04 Cycle, Proto08 신규소재평가 | 실측 vs 시뮬 **교차검증 + 파라미터 피팅** | Category C 전부 | 1~10 사이클 초기 열화만 |
| **MP1** | MP101 공정결과서, MP103 Test Report, MP104~114 Cycle data, MP106 분해분석 | 공정 편차가 Design Spec 내 드리프트 시 시뮬 예측 | 양산 분포 입력 (두께, 합제 ±), 온도 sweep | 면내 불균일 1D 불가 |
| **MP2** | MP201~215 동일 계열 + ER2 | 1차 검증 기반 재시뮬·안전성 시나리오 | 동일 + 급속충전 safety | 내부 단락·기계적 |
| **CA** Close | CA01 과제완료, CA03 Cell Design Spec **최종**, CA04 DFMEA 최종 | **최종 수명 예측**, DFMEA 위험 모드별 시뮬 대응 | Category C 전체 + Tier S/A | 장기 수명 가정 다수 붕괴 |

## 9.1 단계별 Δ 관리

| 단계 | 실측 vs 시뮬 Δ 관리 기준 | 초과 시 |
|------|--------------------|--------|
| EA | — (시뮬은 탐색용) | — |
| PA | 용량 ±5%, DCIR ±20% | Spec 값 재조정 |
| Proto | 용량 ±2%, DCIR ±15%, OCV ±10mV | **가정 A1~A8 중 파탄 원인 역추적** |
| MP1/MP2 | Proto 기준 유지 | 공정 편차 원인 분석 |
| CA | 수명 trend 일치 | 열화 서브모델 파라미터 재피팅 |

---

# 10. 한계와 향후 확장

## 10.1 현재 PyBaMM 1D 가 못 다루는 영역 (Category D 전체 재정리)

| 분류 | 항목 | 대안 |
|------|------|------|
| **기구** | Pouch 두께·folding·forming, Tab 위치·welding, Sealant | 구조 해석, FEA |
| **공정** | Mixing RPM, Coating speed, Pressing tension, Slitting burr | 공정 DOE |
| **품질** | Overhang, Peel strength, Hi-pot, Edge sliding | CTQ 검사 |
| **첨가제 시너지** | 다층 SEI, 첨가제 상충·소모 | **실측 + kinetic 역피팅 라이브러리** |
| **bi-modal 입자** | 대·소립자 혼합 | **PyBaMM MPM** (Multi-Particle Model) |
| **수백 사이클 수명** | dynamic N/P, 전해액 고갈, LAM 진전 | 열화 서브모델 확장 + 장기 실측 |
| **가스·스웰링** | CO₂, CO, H₂ 발생 → 두께 증가 | 가스 모델 확장 (PyBaMM 범위 밖) |
| **안전 시험** | Nail penetration, Dent, Thermal abuse | Multi-physics (열-전기-기계 결합) |
| **면내 불균일** | Tab 근접 전류집중, 권심/edge 편차, 함침 편차 | 3D 모델, Multi-cell 패키지 모델 |

## 10.2 BDT 확장 로드맵

[[PyBaMM_Variables_PPT]] 5.2 참조 + 본 보고서 요약:

1. **Rate-determining Step Visualizer** — 시뮬 결과에서 ②~⑥ 단계별 τ 계산·막대그래프
2. **합제밀도 Trade-off 탐색 UI** — ρ_press 슬라이더로 (ε_AM, porosity) 동시 업데이트 + 용량·율특성 Pareto
3. **N/P ratio 슬라이더** — Li plating 안전 마진 시뮬
4. **bi-modal 입자 MPM 확장** — PyBaMM MPM 연동, 대·소립자 비중 입력
5. **첨가제 프리셋 라이브러리** — 첨가제 조합별 SEI/plating kinetic 측정값 수집 → 프리셋
6. **전해액 함수형 교체 UI** — 용매 조성별 D_e(c,T), κ_e(c,T) 함수 선택
7. **단계별 Δ 자동 계산 탭** — Category C 실측 입력 → 시뮬 결과와 Δ 표시 + 가정 A1~A8 역추적 힌트

---

# 11. 결론 및 권고

## 11.1 결론

1. Cell Design Spec 63 필드 중 **27%** 는 PyBaMM 에 직접 넣고, **32%** 는 가정 A1~A8 을 거쳐 넣고, **41%** 는 시뮬 범위 밖이다.
2. 두 관점 (Rate-determining × 개발 설계) 공통 핵심 파라미터는 **14 개** 로 좁혀진다. 이 중 **음극 입자 반경** 이 가장 높은 우선순위.
3. 변환은 **가정의 집합**이며, 실측과 Δ 가 크면 모델보다 **가정의 파탄**을 먼저 의심해야 한다.
4. PyBaMM 1D 는 **전체 개발의 일부 관점** 이다. Pouch·공정·수율·안전·수명 장기 영역은 다른 도구가 필요하다.

## 11.2 권고

### 단기 (1~3개월)

- **Proto 단계에서 Category C 검증 워크플로우 구축** — Proto02 OQA 데이터로 Δ 자동 계산
- **변환 5요소 문서화 템플릿** 배포 — 모든 Spec → PyBaMM 입력 시 변환식+가정+범위+파탄지표+대안 명시
- **Tier S 14 파라미터 BDT UI 우선 노출** — 기타 파라미터는 접기/고급 메뉴

### 중기 (3~6개월)

- **첨가제 프리셋 라이브러리** 시드 데이터 수집 — FEC, VEC, LiDFOB, LiPO₂F₂ 별 SEI/plating kinetic
- **bi-modal 입자 MPM 모듈** — PyBaMM MPM 연동 프로토타입
- **단계별 Δ 자동 추적 대시보드** — EA → PA → Proto → MP → CA 단계별 Δ 히스토리

### 장기 (6개월+)

- **면내 불균일 3D 모델** 검토 — tab 근접 / 권심 영향 급속충전 안전성
- **가스·스웰링 모델 확장** — Category D 일부 편입
- **AI 기반 파라미터 identifiability 분석** — 어떤 Spec 조합이 시뮬 결과에 민감한지 Sobol 지수

## 11.3 핵심 액션 아이템

1. ✅ 본 보고서를 개발·모델링팀 **단일 참조 문서**로 활용
2. 🔲 [[Cell_Design_Specification_필드]] 를 Spec 작성 시 체크리스트로 사용
3. 🔲 [[260422_analysis_pybamm_key_parameters]] 의 가정 A1~A8 을 모든 변환에 인용
4. 🔲 Proto 평가 시 Category C 필드 자동 비교
5. 🔲 DFMEA 위험 모드별 PyBaMM 서브모델 매핑 노트 추가 생성 (별도 작업)

---

# 12. 부록

## 12.1 관련 문서 참조

| 유형 | 문서 | 역할 |
|------|------|------|
| **정본 (이 보고서가 요약하는 원천)** | [[PyBaMM_Variables_PPT]] | PyBaMM ~70 파라미터 + 510~517 변수 전수 리스트 |
| 정본 | [[Cell_Design_Specification_필드]] | Cell Design Spec 7대 분류 × 63 필드 스키마 |
| 정본 | [[260422_analysis_pybamm_key_parameters]] | Rate × 개발 이중 관점 분석, 가정 A1~A8 상세 |
| 지식 | [[합제밀도와_전류밀도]] | 전극 설계 공식 (LL, ρ_press, current density) |
| 지식 | [[충방전_매커니즘]] | Rate-determining 이론, 주차타워 비유 |
| 지식 | [[전해액]] | 첨가제 DOE 조성 |
| 지식 | [[Silicon]] | Si 음극 특성 (Gen5+ 기반) |
| 지식 | [[분리막_기능층]] | 분리막 코팅 구조 |
| 평가 | [[MX배터리그룹_평가항목]] | 개발 평가 전체 항목 |
| 원본 (기밀) | `raw/g5p_at/*` (46 파일) | EA/PA/Proto/MP/CA 전 단계 문서 |

## 12.2 약어

| 약어 | 의미 |
|------|------|
| LL | Loading Level (mg/cm²) |
| NP ratio | Negative/Positive 용량비 |
| SEI | Solid Electrolyte Interphase |
| LAM | Loss of Active Material |
| LLI | Loss of Lithium Inventory |
| DFMEA | Design Failure Mode and Effects Analysis |
| OQA / OQC | Outgoing Quality Assurance / Control |
| CTQ | Critical To Quality |
| MPM | Multi-Particle Model |
| DFN | Doyle-Fuller-Newman (P2D) |
| SPM | Single Particle Model |
| RPT | Reference Performance Test |
| EA / PA / CA | Evaluation / Plan / Close Approval (개발 단계) |
| MP1 / MP2 | Mass Production 1차 / 2차 |

## 12.3 개발 단계 흐름 (Gen5+ ATL 기준)

```
EA (Evaluation)
  EA01 Cell Pack Proposal
  EA02 Spec Meeting 회의록
  EA03 과제계획서
  EA04 EA 회의록
    │
    ▼
PA (Plan Approval)
  PA01 Cell Design Spec 초안
  PA02 DFMEA 초안
  PA04 Risk Assessment
  PA05 신규 소재검토서
  PA06 선행개발제안서
  PA07 제안승인회의록
    │
    ▼
Proto (프로토타입 1차)
  Proto02 OQA data
  Proto03 Test report
  Proto04 Cycle data
  Proto05 Test report ver2
  Proto08 신규소재평가
    │
    ▼
MP1 (Mass Production 1차)
  MP101 공정결과서
  MP102 Cell Approve Sheet
  MP103/108 Test Report (ver1~2)
  MP104/107/114 Cycle data (ver1~3)
  MP106 분해분석
    │
    ▼
MP2 (Mass Production 2차)
  MP201 공정결과서
  MP202 수율결과서
  MP203 Pack Approval Sheet
  MP204/209 Test report (ver1~2)
  MP205/208 Cycle data (ver1~2)
  MP207 분해분석
  MP215 ER2 보고서
  MP216 부품승인 검토 결과
    │
    ▼
CA (Close)
  CA01 과제완료 보고서
  CA02 과제완료 회의록
  CA03 Cell Design Spec 최종   ◀── 본 보고서 스키마 출처
  CA04 DFMEA 최종
```

---

> *본 보고서는 개발-시뮬 브릿지 단일 참조 문서로 유지되며, 가정 A1~A8 및 변환 테이블은 신규 소재·새 화학계 도입 시 재검토한다.*
>
> *Next review: Proto 실측 확보 후 Category C 자동 검증 워크플로우 구축 시점*
