---
relocated: 2026-04-22
source_vault: "docs/vault/03_Battery_Knowledge/PyBaMM_Variables_PPT.md"
name: PyBaMM 변수 전체 리스트 & 중요도 조사 (PPT용)
description: PyBaMM v25.12 기준 입력 파라미터(~70) + 출력 변수(510~517) 전수조사. Tier 1/2/3 중요도 분류. BDT 프로젝트 적용 매핑 포함.
type: reference
tags:
  - pybamm
  - battery-model
  - parameters
  - variables
  - reference
  - ppt
created: 2026-04-21
source:
  - "[[Electrochemical_parameter]]"
  - "[[Battery_Science_MOC]]"
  - docs/code/02_변경검토/pybamm_output_variables_260226.md
  - DataTool_optRCD_proto_.py
related:
  - "[[NREL_SSC_수명모델_참고]]"
  - "[[Battery_Electrochemical_properties]]"
slide: true
marp: true
---

# PyBaMM 변수 전수 조사 자료

> **PyBaMM v25.12.2** 기준 — 입력 파라미터 약 70개 + 출력 변수 510~517개
>
> BDT 프로젝트 적용 현황 + 중요도 Tier 분류
>
> 작성일: 2026-04-21

---

## 목차

1. **PyBaMM 개요** — 모델 계층과 변수 규모
2. **변수 분류 체계** — Input Parameters vs Output Variables
3. **Input Parameters 전수 리스트** — 7대 카테고리 (~70개)
4. **Output Variables 전수 리스트** — 15대 카테고리 (510~517개)
5. **모델별 차이** — SPM / SPMe / DFN
6. **중요도 Tier 분류** — Tier 1 / Tier 2 / Tier 3
7. **BDT 프로젝트 적용 매핑**
8. **실측 파라미터 연계 (Category A/B/C/D)**
9. **권장 조사 우선순위** — 중요도 top 20
10. **부록** — 프리셋 목록, 참고 자료

---

# 1. PyBaMM 개요

---

## 1.1 PyBaMM이란?

| 항목 | 설명 |
|------|------|
| **정의** | Python-based Battery Mathematical Modelling — 오픈소스 배터리 물리 모델링 프레임워크 |
| **개발자** | 옥스퍼드 대학교 (Chayambuka, Sulzer, Marquis 등) |
| **최신 버전** | v25.12.2 (기준 시점 2026-02-26) |
| **기반 물리** | 전기화학 (Butler-Volmer), 확산 (Fick), 전위 (Nernst-Planck), 열전달 (Fourier) |
| **지원 모델** | SPM, SPMe, DFN, MPM, MSMR, Half-Cell, PoT 등 |
| **파라미터 세트** | Chen2020, Marquis2019, Ecker2015, OKane2022, ORegan2022, Ai2020 등 20+ |

### 3대 리튬이온 기본 모델

| 모델 | Full Name | 핵심 가정 | 속도 | 사용처 |
|------|-----------|----------|------|--------|
| **SPM** | Single Particle Model | 대표 입자 1개, 전해질 균일 | ⚡ 가장 빠름 | BMS 실시간, 대량 스윕 |
| **SPMe** | SPM + electrolyte | SPM + 전해질 확산 방정식 | ⚡ 빠름 | 속도-정확도 절충 |
| **DFN** | Doyle-Fuller-Newman (P2D) | 전극 내 공간 분포 명시적 해석 | 🐢 느림 | 고정밀 연구, 열화 분석 |

---

## 1.2 변수 규모 한눈에

```
┌──────────────────────────────────────────────────────────────┐
│  PyBaMM 변수 = Input Parameters (~70) + Output Variables     │
│                                                               │
│  ▪ Input Parameters (Chen2020 기준)                           │
│     ├─ Geometry     14개  ████                                │
│     ├─ Material     18개  █████                               │
│     ├─ Kinetics      6개  ██                                  │
│     ├─ Transport    10개  ███                                 │
│     ├─ Thermal      12개  ████                                │
│     ├─ Degradation  15개  ████                                │
│     └─ Boundary      6개  ██                                  │
│                     ═════                                      │
│                  총 ~70개                                      │
│                                                               │
│  ▪ Output Variables (v25.12 기준)                             │
│     ├─ SPM           514개                                    │
│     ├─ SPMe          517개  (+3 전해질 플럭스)                │
│     ├─ DFN           515개  (+5, -4 교체)                    │
│     └─ 공통          510개                                    │
└──────────────────────────────────────────────────────────────┘
```

---

# 2. 변수 분류 체계

---

## 2.1 Input vs Output

| 구분 | Input Parameters | Output Variables |
|------|-----------------|------------------|
| **정의** | 모델에 **입력**하는 물성/조건값 | 시뮬레이션이 **계산하는** 결과값 |
| **개수** | ~70개 (프리셋별) | 510~517개 (모델별) |
| **접근** | `param["Positive electrode thickness [m]"]` | `sol["Terminal voltage [V]"].entries` |
| **타입** | 스칼라, 함수(callable), 배열 | 시간축 1D 또는 (공간×시간) 2D |
| **변경 가능** | ✅ 사용자 조정 | ❌ 모델 결과물 (parameter로 제어) |
| **예시** | `Positive electrode thickness [m]` | `Terminal voltage [V]` |

### 핵심 메서드

```python
# Input Parameter 탐색
param = pybamm.ParameterValues("Chen2020")
param.search("thickness")             # 관련 파라미터 검색
param["Positive electrode thickness [m]"] = 75e-6  # 수정

# Output Variable 추출
sol = sim.solve([0, 3600])
list(sol.model.variables.keys())      # 전체 출력 변수
sol["Terminal voltage [V]"].entries   # 시간축 배열
```

---

## 2.2 변수 명명 규칙 (네이밍 컨벤션)

| 패턴 | 의미 | 예시 |
|------|------|------|
| `[unit]` | SI 단위 (공식) | `[m]`, `[V]`, `[mol.m-3]` |
| `[Molar]` | 몰농도 (몰/L) | `Electrolyte concentration [Molar]` |
| `[C]` / `[K]` | 섭씨/켈빈 | `Cell temperature [C]` |
| `Positive / Negative` | 양극 / 음극 | `Positive electrode thickness [m]` |
| `X-averaged` | x축(두께 방향) 공간 평균 | `X-averaged cell temperature [K]` |
| `Volume-averaged` | 전체 체적 평균 | `Volume-averaged cell temperature [K]` |
| `R-averaged` | 입자 반경 방향 평균 | `R-averaged positive particle concentration` |
| `Average` | 단순 평균 (맥락 의존) | `Average positive particle concentration` |
| `Total` | 누적/합 | `Total lithium [mol]` |
| `Loss of` | 손실량 | `Loss of lithium inventory [%]` |
| `Sum of` | 구성요소 합 | `Sum of volumetric interfacial current densities [A.m-3]` |
| `Gradient of` | 공간 미분 | `Gradient of electrolyte potential [V.m-1]` |

---

# 3. Input Parameters 전수 리스트

---

## 3.1 카테고리 A: Geometry (기하학) — 14개

> **설계 설계부서 Cell Design Sheet에서 직접 추출 가능** — 가장 우선순위 높음

| # | 파라미터 키 | 단위 | BDT 한글 | 사용 |
|---|-----------|------|---------|:----:|
| 1 | `Negative electrode thickness [m]` | m | 음극 두께 | ✅ |
| 2 | `Positive electrode thickness [m]` | m | 양극 두께 | ✅ |
| 3 | `Separator thickness [m]` | m | 분리막 두께 | ✅ |
| 4 | `Negative current collector thickness [m]` | m | 음극 집전체 두께 | ❌ |
| 5 | `Positive current collector thickness [m]` | m | 양극 집전체 두께 | ❌ |
| 6 | `Negative particle radius [m]` | m | 음극 입자 반경 | ✅ |
| 7 | `Positive particle radius [m]` | m | 양극 입자 반경 | ✅ |
| 8 | `Electrode height [m]` | m | 전극 높이 | ✅ |
| 9 | `Electrode width [m]` | m | 전극 폭(면적) | ✅ |
| 10 | `Cell cooling surface area [m2]` | m² | 셀 냉각 표면적 | ❌ |
| 11 | `Cell volume [m3]` | m³ | 셀 부피 | ❌ |
| 12 | `Number of electrodes connected in parallel to make a cell` | - | 적층 수 (병렬) | ✅ |
| 13 | `Number of cells connected in series to make a battery` | - | 직렬 셀 수 | ❌ |
| 14 | `Cell thermal expansion coefficient [m.K-1]` | m/K | 셀 열팽창 계수 | ❌ |

---

## 3.2 카테고리 B: Material Properties — 18개

### B.1 전기 물성 (Electronic)

| 파라미터 키 | 단위 | BDT | 사용 |
|-----------|------|-----|:----:|
| `Negative electrode conductivity [S.m-1]` | S/m | 음극 전자전도도 | ✅ |
| `Positive electrode conductivity [S.m-1]` | S/m | 양극 전자전도도 | ✅ |
| `Negative current collector conductivity [S.m-1]` | S/m | 음극 집전체 전도도 | ❌ |
| `Positive current collector conductivity [S.m-1]` | S/m | 양극 집전체 전도도 | ❌ |

### B.2 다공성 / 체적분율 (Porosity / Volume fraction)

| 파라미터 키 | 단위 | BDT | 사용 |
|-----------|------|-----|:----:|
| `Negative electrode porosity` | - | 음극 공극률 | ✅ |
| `Positive electrode porosity` | - | 양극 공극률 | ✅ |
| `Separator porosity` | - | 분리막 공극률 | ✅ |
| `Negative electrode active material volume fraction` | - | 음극 활물질 체적분율 | ✅ |
| `Positive electrode active material volume fraction` | - | 양극 활물질 체적분율 | ✅ |

### B.3 Bruggeman 계수 (유효 수송 보정)

| 파라미터 키 | 단위 | BDT | 사용 |
|-----------|------|-----|:----:|
| `Negative electrode Bruggeman coefficient (electrolyte)` | - | 음극 Bruggeman | ✅ |
| `Negative electrode Bruggeman coefficient (electrode)` | - | 음극 고상 Bruggeman | ❌ |
| `Positive electrode Bruggeman coefficient (electrolyte)` | - | 양극 Bruggeman | ✅ |
| `Positive electrode Bruggeman coefficient (electrode)` | - | 양극 고상 Bruggeman | ❌ |
| `Separator Bruggeman coefficient (electrolyte)` | - | 분리막 Bruggeman | ✅ |

### B.4 밀도 / 비열

| 파라미터 키 | 단위 | BDT | 사용 |
|-----------|------|-----|:----:|
| `Negative electrode density [kg.m-3]` | kg/m³ | 음극 밀도 | ❌ |
| `Positive electrode density [kg.m-3]` | kg/m³ | 양극 밀도 | ❌ |
| `Separator density [kg.m-3]` | kg/m³ | 분리막 밀도 | ❌ |
| `Negative current collector density [kg.m-3]` | kg/m³ | 음극 집전체 밀도 | ❌ |

---

## 3.3 카테고리 C: Electrochemistry Kinetics — 6개

| # | 파라미터 키 | 단위 | 설명 | BDT |
|---|-----------|------|-----|:----:|
| 1 | `Negative electrode exchange-current density [A.m-2]` | A/m² | 음극 교환 전류밀도 (함수형) | ✅ |
| 2 | `Positive electrode exchange-current density [A.m-2]` | A/m² | 양극 교환 전류밀도 (함수형) | ✅ |
| 3 | `Negative electrode charge transfer coefficient` | - | 음극 전하이동계수 (α, 기본=0.5) | ❌ |
| 4 | `Positive electrode charge transfer coefficient` | - | 양극 전하이동계수 | ❌ |
| 5 | `Negative electrode double-layer capacity [F.m-2]` | F/m² | 음극 이중층 용량 | ❌ |
| 6 | `Positive electrode double-layer capacity [F.m-2]` | F/m² | 양극 이중층 용량 | ❌ |

### 핵심 수식 (Butler-Volmer)

$$j = j_0 \left[ \exp\left(\frac{\alpha F \eta}{RT}\right) - \exp\left(-\frac{(1-\alpha) F \eta}{RT}\right) \right]$$

- $j_0$ : Exchange current density (교환 전류밀도)
- $\alpha$ : Charge transfer coefficient (전하이동계수)
- $\eta$ : Overpotential (과전압) — **Output variable**

---

## 3.4 카테고리 D: Transport (수송) — 10개

### D.1 고체상 (활물질 내부 Li 확산)

| # | 파라미터 키 | 단위 | 형태 |
|---|-----------|------|-----|
| 1 | `Negative particle diffusivity [m2.s-1]` | m²/s | 상수 또는 f(c,T) |
| 2 | `Positive particle diffusivity [m2.s-1]` | m²/s | 상수 또는 f(c,T) |
| 3 | `Maximum concentration in negative electrode [mol.m-3]` | mol/m³ | 상수 |
| 4 | `Maximum concentration in positive electrode [mol.m-3]` | mol/m³ | 상수 |

### D.2 전해질상 (이온 확산 / 전도)

| # | 파라미터 키 | 단위 | 형태 |
|---|-----------|------|-----|
| 5 | `Electrolyte diffusivity [m2.s-1]` | m²/s | 보통 f(c,T) |
| 6 | `Electrolyte conductivity [S.m-1]` | S/m | 보통 f(c,T) |
| 7 | `Cation transference number` | - | 상수 (t₊, 0.2~0.4 typical) |
| 8 | `Thermodynamic factor` | - | 상수 또는 f(c) |
| 9 | `Initial concentration in electrolyte [mol.m-3]` | mol/m³ | 상수 (보통 1000 mol/m³ = 1M) |
| 10 | `EC diffusivity [m2.s-1]` | m²/s | SEI 성장 모델용 |

---

## 3.5 카테고리 E: Thermodynamics (OCP / 전압) — 8개

| # | 파라미터 키 | 단위 | 형태 |
|---|-----------|------|-----|
| 1 | `Negative electrode OCP [V]` | V | **함수형** U(sto, T) |
| 2 | `Positive electrode OCP [V]` | V | **함수형** U(sto, T) |
| 3 | `Negative electrode OCP entropic change [V.K-1]` | V/K | ∂U/∂T, 가역발열 |
| 4 | `Positive electrode OCP entropic change [V.K-1]` | V/K | ∂U/∂T |
| 5 | `Upper voltage cut-off [V]` | V | 충전 종료 전압 |
| 6 | `Lower voltage cut-off [V]` | V | 방전 종료 전압 |
| 7 | `Open-circuit voltage at 0% SOC [V]` | V | SOC 정규화 기준 |
| 8 | `Open-circuit voltage at 100% SOC [V]` | V | SOC 정규화 기준 |

### 전체 OCV 수식 (셀 단자 전압의 이상적 값)

$$U_{cell}(SOC) = U_{pos}(x_{pos}(SOC)) - U_{neg}(x_{neg}(SOC))$$

- $x_{pos}$ : 양극 화학양론비 (stoichiometry)
- $x_{neg}$ : 음극 화학양론비
- OCP 함수 $U_{pos}, U_{neg}$ — chemistry 별 특성 곡선

---

## 3.6 카테고리 F: Thermal (열) — 12개

### F.1 경계 조건 / 환경

| # | 파라미터 키 | 단위 | 설명 |
|---|-----------|------|-----|
| 1 | `Ambient temperature [K]` | K | 환경 온도 |
| 2 | `Initial temperature [K]` | K | 초기 셀 온도 |
| 3 | `Reference temperature [K]` | K | Arrhenius 기준 |
| 4 | `Total heat transfer coefficient [W.m-2.K-1]` | W/m²·K | 대류 냉각 계수 |

### F.2 소재 열물성

| # | 파라미터 키 | 단위 |
|---|-----------|------|
| 5 | `Negative electrode specific heat capacity [J.kg-1.K-1]` | J/kg·K |
| 6 | `Positive electrode specific heat capacity [J.kg-1.K-1]` | J/kg·K |
| 7 | `Separator specific heat capacity [J.kg-1.K-1]` | J/kg·K |
| 8 | `Negative current collector specific heat capacity [J.kg-1.K-1]` | J/kg·K |
| 9 | `Negative electrode thermal conductivity [W.m-1.K-1]` | W/m·K |
| 10 | `Positive electrode thermal conductivity [W.m-1.K-1]` | W/m·K |
| 11 | `Separator thermal conductivity [W.m-1.K-1]` | W/m·K |
| 12 | `Negative current collector thermal conductivity [W.m-1.K-1]` | W/m·K |

---

## 3.7 카테고리 G: Degradation (열화) — 15개

> **OKane2022 등 열화 모델 활성화 시** 사용. 기본 SPM/DFN 시뮬에는 0으로 세팅되어 있을 수 있음.

### G.1 SEI 관련 (8개)

| # | 파라미터 키 | 단위 |
|---|-----------|------|
| 1 | `SEI partial molar volume [m3.mol-1]` | m³/mol |
| 2 | `SEI reaction exchange current density [A.m-2]` | A/m² |
| 3 | `SEI resistivity [Ohm.m]` | Ω·m |
| 4 | `SEI solvent diffusivity [m2.s-1]` | m²/s |
| 5 | `Bulk solvent concentration [mol.m-3]` | mol/m³ |
| 6 | `SEI open-circuit potential [V]` | V |
| 7 | `Initial SEI thickness [m]` | m |
| 8 | `SEI kinetic rate constant [m.s-1]` | m/s |

### G.2 Lithium Plating (4개)

| # | 파라미터 키 | 단위 |
|---|-----------|------|
| 9 | `Lithium plating kinetic rate constant [m.s-1]` | m/s |
| 10 | `Lithium plating transfer coefficient` | - |
| 11 | `Exchange-current density for plating [A.m-2]` | A/m² |
| 12 | `Dead lithium decay constant [s-1]` | 1/s |

### G.3 LAM / 기계적 열화 (3개)

| # | 파라미터 키 | 단위 |
|---|-----------|------|
| 13 | `Negative electrode reaction-driven LAM factor [m3.mol-1]` | m³/mol |
| 14 | `Positive electrode reaction-driven LAM factor [m3.mol-1]` | m³/mol |
| 15 | `Ratio of lithium moles to SEI moles` | - |

---

## 3.8 카테고리 H: Initial & Boundary (초기/경계) — 6개

| # | 파라미터 키 | 단위 | 역할 |
|---|-----------|------|------|
| 1 | `Initial concentration in negative electrode [mol.m-3]` | mol/m³ | 음극 초기 Li 농도 → init_soc |
| 2 | `Initial concentration in positive electrode [mol.m-3]` | mol/m³ | 양극 초기 Li 농도 → init_soc |
| 3 | `Nominal cell capacity [A.h]` | A·h | 공칭 용량 (C-rate 기준) |
| 4 | `Current function [A]` | A | 충방전 전류 (상수 또는 함수) |
| 5 | `Contact resistance [Ohm]` | Ω | 접촉 저항 |
| 6 | `Negative electrode surface potential difference at separator interface [V]` | V | half-cell boundary |

---

# 4. Output Variables 전수 리스트

---

## 4.1 Output 변수 15대 카테고리 (510개 공통)

| # | 카테고리 | 변수 수 | 핵심 주제 |
|---|---------|:------:|----------|
| 1 | 시간 / 기본 전기 출력 | 22 | Time, Voltage, Current, Capacity, Power, Resistance |
| 2 | 전압 분해 (Overpotential / OCV) | 24 | OCV, η_reaction, ohmic, SEI film |
| 3 | 양극 전극 물성 & 전기화학 | 49 | OCP, 전위, 반응, 계면 전류, 리튬화 |
| 4 | 음극 전극 물성 & 전기화학 | 49 | (양극과 동일 구조) |
| 5 | 입자 농도 & 화학양론비 | 30+28+6 | particle conc., surface conc., stoichiometry |
| 6 | 전해질 | 16 | concentration, potential, current density, flux |
| 7 | 분리막 | 13 | porosity, concentration, potential, temp, pressure |
| 8 | 열 (Thermal) | 20 | Total/Ohmic/Irreversible/Reversible heating, cooling |
| 9 | 열화 / 부반응 | 42 | SEI thickness, plating thickness, LLI, LAM, side reactions |
| 10 | 리튬 인벤토리 / 총량 | 13 | Total lithium, losses, lost to side reactions |
| 11 | 구조 / 좌표 / 기타 | 18 | x, r_n, r_p, porosity, pressure distribution |
| 12 | X-averaged 음극 관련 | 59 | 음극 x축 평균 — 모든 주요 변수의 평균 |
| 13 | X-averaged 양극 관련 | 59 | 양극 x축 평균 |
| 14 | X-averaged 전해질/분리막/발열 | 23 | 전해질·발열의 x축 평균 |
| 15 | Volume-averaged 변수 | 29 | 전체 체적 평균 (온도, 발열, SEI, 플레이팅) |

**합계 ≈ 510개 (모델별 ±5)**

---

## 4.2 카테고리 ① 시간 / 기본 전기 출력 (22개)

> **거의 모든 시뮬에서 추출하는 핵심 변수**

| 키 | 단위 | 빈도 | BDT |
|----|------|:---:|:---:|
| `Time [s]` / `[min]` / `[h]` | s/min/h | 🔴 | ✅ |
| `Terminal voltage [V]` | V | 🔴 | ✅ |
| `Voltage [V]` / `Battery voltage [V]` | V | 🔴 | — |
| `Current [A]` | A | 🔴 | ✅ |
| `C-rate` | - | 🟡 | — |
| `Discharge capacity [A.h]` | A·h | 🔴 | ✅ |
| `Discharge energy [W.h]` | W·h | 🟡 | — |
| `Throughput capacity [A.h]` | A·h | 🟡 | — |
| `Throughput energy [W.h]` | W·h | 🟢 | — |
| `Power [W]` / `Terminal power [W]` | W | 🟡 | — |
| `Resistance [Ohm]` | Ω | 🟡 | — |
| `Local ECM resistance [Ohm]` | Ω | 🟢 | — |
| `Current collector current density [A.m-2]` | A/m² | 🟢 | — |
| `Electrode current density [A.m-2]` | A/m² | 🟢 | — |
| `Total current density [A.m-2]` | A/m² | 🟢 | — |

🔴=필수 / 🟡=중요 / 🟢=세부

---

## 4.3 카테고리 ② 전압 분해 (24개)

> **셀 전압 $V = U_p - U_n - \sum\eta - IR$ 분해에 필요**

```
V_cell = U_pos (양극 OCP)
       - U_neg (음극 OCP)
       - η_pos (양극 반응 과전압)
       - η_neg (음극 반응 과전압)
       - η_conc (농도 과전압)
       - ΔV_ohm (전해질+고상 옴손실)
       - η_SEI (SEI film 과전압)
```

### 핵심 변수 (BDT 일반 Plot [1,0] Voltage Components에 사용)

| 변수 키 | 용도 |
|--------|------|
| `Battery negative electrode bulk open-circuit potential [V]` | ① Neg OCP (음극 기여) |
| `Battery positive electrode bulk open-circuit potential [V]` | ② Pos OCP (양극 기여) |
| `Battery negative particle concentration overpotential [V]` | ③-1 음극 농도 η |
| `X-averaged battery negative reaction overpotential [V]` | ③-2 음극 반응 η |
| `Battery positive particle concentration overpotential [V]` | ④-1 양극 농도 η |
| `X-averaged battery positive reaction overpotential [V]` | ④-2 양극 반응 η |
| `X-averaged battery concentration overpotential [V]` | ⑤-1 전해질 농도 η |
| `X-averaged battery electrolyte ohmic losses [V]` | ⑤-2 전해질 옴 |
| `X-averaged battery negative/positive solid phase ohmic losses [V]` | ⑤-3 고상 옴 |

---

## 4.4 카테고리 ③ 양극 전극 변수 (49개)

> 음극(카테고리 ④)과 완전히 대칭적 구조. `Positive` → `Negative` 치환.

### 전극 전위 / 과전압 (8개)
- `Positive electrode open-circuit potential [V]`
- `Positive electrode equilibrium open-circuit potential [V]`
- `Positive electrode bulk open-circuit potential [V]`
- `Positive electrode potential [V]`
- `Positive electrode reaction overpotential [V]`
- `Positive electrode ohmic losses [V]`
- `Positive electrode SEI film overpotential [V]`
- `Positive electrode surface potential difference [V]`

### 전류 / 반응 (9개)
- `Positive electrode exchange current density [A.m-2]`
- `Positive electrode interfacial current density [A.m-2]`
- `Positive electrode volumetric interfacial current density [A.m-3]`
- `Positive electrode current density [A.m-2]`
- (+ SEI/plating 세부 5개)

### 화학양론 / 리튬화 (3개)
- `Positive electrode stoichiometry`
- `Positive electrode extent of lithiation`
- `Positive electrode capacity [A.h]`

### 미세구조 (9개)
- `Positive electrode active material volume fraction` (+ change rate)
- `Positive electrode porosity` (+ change rate, × concentration)
- `Positive electrode surface area to volume ratio [m-1]`
- `Positive electrode interface utilisation` (+ variable)
- `Positive electrode roughness ratio`
- `Positive electrode transport efficiency`

### 온도 / 압력 / 속도 (5개)
- `Positive electrode temperature [K]` / `[C]`
- `Positive electrode pressure [Pa]`
- `Positive electrode volume-averaged concentration [mol.m-3]`
- `Positive electrode volume-averaged velocity/acceleration`

### 전해질 (양극 영역) (4개)
- `Positive electrolyte concentration [mol.m-3]` / `[Molar]`
- `Positive electrolyte potential [V]`
- `Positive electrolyte transport efficiency`

### 집전체 (4개)
- `Positive current collector potential [V]` / `temperature [K]` / `[C]` / `Ohmic heating [W.m-3]`

---

## 4.5 카테고리 ⑤ 입자 농도 (64개)

### 양극/음극 입자 (30개)
- `Positive particle concentration` (+ `[mol.m-3]`, surface, stoichiometry, surface stoichiometry)
- `Positive particle flux [mol.m-2.s-1]` / `bc [mol.m-4]` / `rhs`
- `Positive particle effective diffusivity [m2.s-1]` / `radius [m]`
- `Positive particle crack length [m]` / `cracking rate [m.s-1]`
- `Positive particle concentration overpotential [V]`
- (음극 동일 구조 — 총 30개)

### 평균/최대/최소 (28개)
- `Average [neg/pos] particle concentration` (+ `[mol.m-3]`, stoichiometry)
- `Maximum [neg/pos] particle concentration` (+ surface, stoichiometry × 2)
- `Minimum [neg/pos] particle concentration` (surface × 2)
- **활용**: 입자 내 Li 균일도 체크, solidification 위험 탐지

### R-averaged (6개)
- `R-averaged [neg/pos] particle concentration` (+ `[mol.m-3]`, stoichiometry)

---

## 4.6 카테고리 ⑥ 전해질 (16개)

### 상태 변수
| 변수 키 | 설명 |
|--------|------|
| `Electrolyte concentration [mol.m-3]` / `[Molar]` | Li⁺ 이온 농도 |
| `Electrolyte potential [V]` | φ_e |
| `Electrolyte current density [A.m-2]` | 이온 전류 밀도 |
| `Electrolyte flux [mol.m-2.s-1]` | Li⁺ 플럭스 |
| `Electrolyte transport efficiency` | 유효 수송 계수 |

### 구배 / 분리막 (gradient)
- `Gradient of electrolyte potential [V.m-1]`
- `Gradient of negative/positive/separator electrolyte potential [V.m-1]`

### 계면 전류 합산 (Sum of...)
- `Sum of volumetric interfacial current densities [A.m-3]`
- `Sum of negative/positive electrode volumetric interfacial current densities [A.m-3]`
- `Sum of negative/positive electrode electrolyte reaction source terms [A.m-3]`

---

## 4.7 카테고리 ⑧ 열 (Thermal) — 20개

| 분류 | 변수 키 |
|------|--------|
| **온도** | `Ambient temperature [K]`/`[C]`, `Cell temperature [K]`/`[C]`, `Surface temperature [K]` |
| **총 발열** | `Total heating [W.m-3]` / `[W]` / `per unit electrode-pair area [W.m-2]` |
| **옴 발열** | `Ohmic heating [W.m-3]` / `[W]` / `per unit area [W.m-2]` |
| **비가역 발열** | `Irreversible electrochemical heating [W.m-3]` / `[W]` / `per unit area [W.m-2]` |
| **가역 발열** | `Reversible heating [W.m-3]` / `[W]` / `per unit area [W.m-2]` |
| **냉각** | `Environment total cooling [W]`, `Surface total cooling [W.m-3]` / `[W]` |

### 열 모델 옵션 (Input)
```python
model = pybamm.lithium_ion.DFN(options={"thermal": "lumped"})
# options: "isothermal", "lumped", "x-lumped", "x-full"
```

---

## 4.8 카테고리 ⑨ 열화 (Degradation) — 42개

### SEI (8개)
`Positive/Negative SEI thickness [m]`, `SEI concentration [mol.m-3]`, `SEI on cracks thickness/concentration`

### 리튬 석출 (10개)
- `Positive/Negative lithium plating thickness [m]` / `concentration [mol.m-3]`
- `Positive/Negative dead lithium thickness [m]` / `concentration [mol.m-3]`
- `Positive/Negative crack surface to volume ratio [m-1]`

### 열화 지표 % (7개) — **수명 분석 핵심**
| 키 | 단위 | 의미 |
|----|------|------|
| `LLI [%]` | % | Loss of Lithium Inventory |
| `LAM_pe [%]` | % | Loss of Active Material (positive) |
| `LAM_ne [%]` | % | Loss of Active Material (negative) |
| `Loss of lithium inventory [%]` | % | LLI 상세 |
| `Loss of lithium inventory, including electrolyte [%]` | % | LLI + 전해질 포함 |
| `Loss of active material in positive electrode [%]` | % | LAM_pe 상세 |
| `Loss of active material in negative electrode [%]` | % | LAM_ne 상세 |

### 부반응 용량 손실 (15개)
- `Total capacity lost to side reactions [A.h]`
- `Loss of capacity to [pos/neg] SEI [A.h]` × 4
- `Loss of capacity to [pos/neg] SEI on cracks [A.h]` × 2
- `Loss of capacity to [pos/neg] lithium plating [A.h]` × 2
- `Loss of lithium to [SEI/plating/LAM] [mol]` × 8

---

## 4.9 카테고리 ⑩ 리튬 인벤토리 — 13개

> **전체 셀 내 Li의 위치와 손실 추적** — 열화 분석 필수

| 키 | 단위 | 설명 |
|----|------|------|
| `Total lithium [mol]` | mol | 총 리튬량 |
| `Total lithium capacity [A.h]` | A·h | 총 리튬 용량 |
| `Total lithium in particles [mol]` | mol | 입자 내 (Li_intercalated) |
| `Total lithium in electrolyte [mol]` | mol | 전해질 내 |
| `Total lithium in positive/negative electrode [mol]` | mol | 전극별 |
| `Total lithium in primary phase in pos/neg electrode [mol]` | mol | 1차상 (MSMR 모델용) |
| `Total lithium lost [mol]` | mol | 총 손실 |
| `Total lithium lost from particles [mol]` | mol | 입자 유래 손실 |
| `Total lithium lost from electrolyte [mol]` | mol | 전해질 유래 손실 |
| `Total lithium lost to side reactions [mol]` | mol | 부반응 손실 |

---

# 5. 모델별 차이 (SPM / SPMe / DFN)

---

## 5.1 변수 수 비교

| 모델 | 변수 수 | 공통 | 특화 |
|------|:------:|:----:|------|
| **SPM** | 514 | 510 | + 전해질 전류밀도 (pos/neg), X-averaged particle flux (pos/neg) |
| **SPMe** | 517 | 510 | + 전해질 convection/diffusion/migration flux (3개) + SPM 특화 4개 |
| **DFN** | 515 | 510 | + Electrode effective conductivity (pos/neg) + 전해질 플럭스 3개 |

---

## 5.2 모델별 가용성 매트릭스

| 변수 그룹 | SPM | SPMe | DFN | 설명 |
|----------|:---:|:----:|:---:|-----|
| 기본 510개 | ✅ | ✅ | ✅ | 3모델 동일 |
| `Negative/Positive electrolyte current density [A.m-2]` | ✅ | ✅ | ❌ | DFN은 공간분포 해석하므로 별도 계산 안 함 |
| `X-averaged negative/positive particle flux [mol.m-2.s-1]` | ✅ | ✅ | ❌ | 위와 동일 |
| `Electrolyte convection/diffusion/migration flux [mol.m-2.s-1]` | ❌ | ✅ | ✅ | 전해질 확산 방정식 있을 때만 |
| `Negative/Positive electrode effective conductivity` | ❌ | ❌ | ✅ | DFN 전용 — 고상 전자 전도 명시적 해석 |

### 실무 가이드
- **BMS, 빠른 스윕** → SPM
- **DCIR, GITT, 농도 구배 분석** → SPMe
- **고정밀 수명 분석, 상세 열화** → DFN

---

# 6. 중요도 Tier 분류

---

## 6.1 분류 기준

| Tier | 정의 | 대상 변수 수 |
|------|------|:----------:|
| **Tier 1** 🔴 | **필수** — 모든 시뮬에서 확인 / 셀 설계 필수 파라미터 | ~15 |
| **Tier 2** 🟡 | **중요** — 수명/안전성 분석, 고급 사용 | ~35 |
| **Tier 3** 🟢 | **세부** — 연구/특수 목적, 선택적 | 나머지 500+ |

### 판단 기준 3가지
1. **물리적 필수성**: 모델이 해결할 수 없으면 의미 없는 변수
2. **설계 영향도**: 셀 개발 현장에서 직접 제어 가능한 파라미터
3. **분석 활용도**: 성능/수명/안전성 평가에 자주 쓰이는 변수

---

## 6.2 Tier 1 — 필수 🔴 (Input 9개 + Output 6개)

### Input (9개)
| # | 파라미터 | 이유 |
|---|---------|------|
| 1 | `Positive electrode thickness [m]` | 용량·저항 지배 |
| 2 | `Negative electrode thickness [m]` | 용량·저항 지배 |
| 3 | `Separator thickness [m]` | 저항 지배 |
| 4 | `Positive particle radius [m]` | 율특성 지배 (τ = r²/D) |
| 5 | `Negative particle radius [m]` | 율특성 지배 |
| 6 | `Nominal cell capacity [A.h]` | C-rate 정의의 기준 |
| 7 | `Upper / Lower voltage cut-off [V]` | 사이클 종료 조건 |
| 8 | `Ambient temperature [K]` | Arrhenius 전 과정 영향 |
| 9 | `Current function [A]` | 충방전 프로파일 자체 |

### Output (6개)
| # | 변수 | 용도 |
|---|-----|------|
| 1 | `Time [s]` | 시간 축 |
| 2 | `Terminal voltage [V]` | 셀 전압 커브 |
| 3 | `Current [A]` | 전류 프로파일 |
| 4 | `Discharge capacity [A.h]` | 용량 추이 |
| 5 | `X-averaged positive electrode extent of lithiation` | SOC_pos |
| 6 | `X-averaged negative electrode extent of lithiation` | SOC_neg |

---

## 6.3 Tier 2 — 중요 🟡 (Input 20개 + Output 15개)

### Input (20개) — 셀 설계 + 소재 물성

**설계 파라미터 (10개)**
- `Positive/Negative electrode active material volume fraction` (2)
- `Positive/Negative electrode porosity` (2)
- `Separator porosity` (1)
- `Positive/Negative/Separator Bruggeman coefficient (electrolyte)` (3)
- `Electrode width [m]` / `Electrode height [m]` (2)

**소재 물성 (10개)**
- `Maximum concentration in positive/negative electrode [mol.m-3]` (2)
- `Positive/Negative particle diffusivity [m2.s-1]` (2)
- `Positive/Negative electrode conductivity [S.m-1]` (2)
- `Electrolyte diffusivity/conductivity [m2.s-1]/[S.m-1]` (2)
- `Positive/Negative electrode exchange-current density [A.m-2]` (2)

### Output (15개) — 분해 분석 / 열 / 수명

- `X-averaged positive/negative electrode open-circuit potential [V]` (2)
- `X-averaged positive/negative electrode reaction overpotential [V]` (2)
- `X-averaged battery [concentration/electrolyte ohmic losses/reaction/solid phase ohmic losses] [V]` (4)
- `Volume-averaged cell temperature [C]` (1)
- `Volume-averaged [Ohmic/Irreversible/Reversible/Total] heating [W.m-3]` (4)
- `X-averaged positive/negative particle surface concentration [mol.m-3]` (2)

---

## 6.4 Tier 3 — 세부 🟢 (500+개)

### 사용 시나리오별 추가 추천

| 시나리오 | 추가로 볼 변수 |
|---------|--------------|
| **급속충전 안전성** | `X-averaged negative electrode lithium plating reaction overpotential [V]`, `Negative lithium plating thickness [m]`, `Negative electrode potential [V]` (0V 근접 감시) |
| **수명 열화 분석** | `LLI [%]`, `LAM_pe [%]`, `LAM_ne [%]`, `X-averaged negative SEI thickness [m]`, `Total capacity lost to side reactions [A.h]` |
| **DCIR / HPPC** | `Resistance [Ohm]`, `Local ECM resistance [Ohm]`, `Power [W]` |
| **전해질 구배 분석** | `Electrolyte concentration [mol.m-3]` (공간 분포), `Electrolyte potential [V]`, `Electrolyte convection/diffusion/migration flux` (SPMe/DFN) |
| **입자 내부 균일도** | `Positive/Negative particle concentration [mol.m-3]` (반경 방향), `Maximum/Minimum particle surface concentration`, `Particle concentration overpotential [V]` |
| **기계적 응력** | `Pressure [Pa]` (분포), `Positive/Negative particle crack length [m]`, `crack surface to volume ratio [m-1]` |

---

# 7. BDT 프로젝트 적용 매핑

---

## 7.1 BDT에서 제어하는 Input Parameters (34개)

BDT UI → PyBaMM 매핑 (`_key_map` + `_key_map_extended`)

| 카테고리 | BDT 한글 | PyBaMM 영어 키 | 단위 변환 |
|---------|---------|---------------|----------|
| **Geometry** | 양극/음극 두께 | `Positive/Negative electrode thickness [m]` | μm → m (×1e-6) |
|  | 양극/음극 입자 반경 | `Positive/Negative particle radius [m]` | μm → m |
|  | 분리막 두께 | `Separator thickness [m]` | μm → m |
|  | 전극 폭/높이 | `Electrode width/height [m]` | mm → m |
|  | 양극/음극 활물질 비율 | `Positive/Negative electrode active material volume fraction` | 1 |
|  | 양극/음극/분리막 기공률 | `Positive/Negative/Separator porosity` | 1 |
|  | 적층 수 | `Number of electrodes connected in parallel...` | 1 |
|  | 셀 용량 | `Nominal cell capacity [A.h]` | 1 |
| **Transport** | 양극/음극 고상확산계수 | `Positive/Negative electrode diffusivity [m2.s-1]` | 1 |
|  | 전해질 확산계수/전도도 | `Electrolyte diffusivity/conductivity` | 1 |
|  | 양극/음극 전자전도도 | `Positive/Negative electrode conductivity [S.m-1]` | 1 |
|  | 전해질 농도 | `Initial concentration in electrolyte [mol.m-3]` | 1 |
|  | 양극/음극/분리막 Bruggeman | `... Bruggeman coefficient (electrolyte)` | 1 |
| **Kinetics** | 양극/음극 교환전류밀도 | `Positive/Negative electrode exchange-current density [A.m-2]` | 1 |
|  | 양극/음극 최대농도 | `Maximum concentration in positive/negative electrode [mol.m-3]` | 1 |
|  | Plating 속도/전달 | `Lithium plating kinetic rate constant / transfer coefficient` | 1 |
| **Thermodynamics** | 양극/음극 OCP | `Positive/Negative electrode OCP [V]` | 함수형 |
|  | 온도 | `Ambient temperature [K]` | °C → K (+273.15) |
|  | 열전달 계수 | `Total heat transfer coefficient [W.m-2.K-1]` | 1 |
|  | 상/하한 전압 | `Upper/Lower voltage cut-off [V]` | 1 |

---

## 7.2 BDT에서 시각화하는 Output Variables

### 일반 Plot (2×3) — 사용 변수 ~15개

| 위치 | 차트 | 사용 변수 |
|------|------|----------|
| [0,0] Voltage & Current | `Terminal voltage [V]`, `Current [A]` |
| [0,1] Electrode Balance (SoC) | `X-averaged positive/negative extent of lithiation`, `X-averaged positive/negative OCP` |
| [0,2] Temperature & Heat | `Volume-averaged cell temperature [C]`, `Volume-averaged Ohmic/Irreversible/Reversible heating [W.m-3]` |
| [1,0] Voltage Components | 10개 분해 변수 (전체 섹션 4.3 참조) |
| [1,1] Electrode Balance (Stoichiometry) | `X-averaged pos/neg extent of lithiation`, 각 OCP |
| [1,2] Lithium Plating Risk | `X-averaged negative electrode potential [V]`, `X-averaged negative electrode lithium plating reaction overpotential [V]` |

### 상세 Plot (2×3) — 구현 계획 중

| 위치 | 차트 | 필요 변수 (예상) |
|------|------|----------------|
| [0,0] Overpotential Breakdown | Reaction/Ohmic/Concentration η |
| [0,1] Solid-Phase Diffusion | `X-averaged [pos/neg] particle surface/bulk concentration [mol.m-3]` |
| [0,2] Electrolyte Li⁺ Concentration | `Electrolyte concentration [mol.m-3]` (SPMe/DFN) |
| [1,0] Electrolyte Potential Gradient | `Electrolyte potential [V]`, `Gradient of electrolyte potential [V.m-1]` |
| [1,1] Interfacial Current Density | `Positive/Negative electrode interfacial current density [A.m-2]` |
| [1,2] Lithium Plating Risk | (일반 Plot과 동일) |

---

## 7.3 현재 미사용 → 도입 권장 변수

BDT가 아직 시각화하지 않는, 활용도 높은 변수 Top 10

| # | 변수 | 활용처 |
|---|-----|--------|
| 1 | `LLI [%]` | 수명 분석 탭 — 리튬 손실 정량 |
| 2 | `LAM_pe [%]` / `LAM_ne [%]` | 수명 분석 탭 — 활물질 손실 정량 |
| 3 | `X-averaged negative SEI thickness [m]` | SEI 성장 추이 |
| 4 | `Negative lithium plating thickness [m]` | 급속충전 안전 마진 |
| 5 | `Total capacity lost to side reactions [A.h]` | 열화 종합 지표 |
| 6 | `Electrolyte concentration [mol.m-3]` (공간) | 농도 구배 히트맵 |
| 7 | `Resistance [Ohm]` / `Local ECM resistance [Ohm]` | DCIR 시뮬 |
| 8 | `Positive/Negative particle concentration [mol.m-3]` (반경) | 입자 내 Li 분포 애니메이션 |
| 9 | `Throughput capacity [A.h]` / `Throughput energy [W.h]` | 누적 부하 (수명 x축) |
| 10 | `X-averaged [pos/neg] electrode resistance [Ohm.m2]` | 전극별 저항 분해 |

---

# 8. 실측 파라미터 연계 (Category A/B/C/D)

---

## 8.1 개발부서 실측값 ↔ PyBaMM 매핑

> BDT pybamm.instructions.md에 이미 정의된 4-Category 시스템

| Category | 정의 | 개수 | PyBaMM 매핑 |
|----------|------|:---:|-------------|
| **A — Direct Input** | Cell Design Sheet에서 직접 변환 | 7 | 두께 × 1e-6, 온도 +273.15 |
| **B — Calculated** | 2+ 실측값 조합해 변환 | 9 | 합제밀도 → 체적분율, D50 → 반경 |
| **C — Validation** | 시뮬 결과와 비교 검증 | 6 | OCV/IMP/RPT 교차검증 |
| **D — Out of Scope** | PyBaMM 1D 모델링 불가 | ~30+ | 기구·공정·품질·수율·스웰링 |

---

## 8.2 Category A (직접 입력, 7개)

| 개발부서 항목 | PyBaMM 키 | 변환 |
|-------------|----------|------|
| Cathode coating thickness (μm) | `Positive electrode thickness [m]` | ×1e-6 |
| Anode coating thickness (μm) | `Negative electrode thickness [m]` | ×1e-6 |
| Separator base thickness (μm) | `Separator thickness [m]` | ×1e-6 |
| Electrolyte Molarity (M) | `Initial concentration in electrolyte [mol.m-3]` | ×1000 |
| Min. Capacity (mAh) | `Nominal cell capacity [A.h]` | ÷1000 |
| Electrode Width (mm) | `Electrode width [m]` | ÷1000 |
| Temperature (℃) | `Ambient temperature [K]` | +273.15 |

---

## 8.3 Category B (변환 계산, 9개)

| 개발 항목(들) | PyBaMM 파라미터 | 변환식 |
|-------------|----------------|--------|
| Press density + Formulation | Active material volume fraction | $\varepsilon_{AM} = \dfrac{\rho_{press} \cdot w_{AM}}{\rho_{AM}}$ |
| D50 particle size (IQC) | Particle radius [m] | $r = \dfrac{D_{50}}{2} \times 10^{-6}$ |
| 1st discharge capacity (IQC) | Maximum solid concentration | $c_{max} = \dfrac{Q \cdot 3.6 \cdot \rho_{AM}}{F} \times 10^6$ |
| Loading + Density | Thickness 교차검증 | $t = \dfrac{\text{loading}}{\rho_{press}} \times 10$ |
| Formulation + Density | Porosity | $\varepsilon = 1 - \dfrac{\rho_{press}}{\rho_{true}}$ |
| W × L × Layers × 2 | Electrode area (m²) | 기하학 계산 |
| Current density (mA/cm²) | C-rate | $C = \dfrac{j \cdot A}{Q_{cell}}$ |
| 1st Efficiency (IQC, %) | Initial LLI 추정 | $LLI_{init} = 1 - \eta_{1st}$ |
| Separator coating layers | 총 분리막 두께 | base + Σ(coating layers) |

---

## 8.4 Category C (검증, 6개)

| 실측 | PyBaMM 시뮬 | 허용 기준 |
|------|-----------|----------|
| OCV at 62% SOC | `sol["Terminal voltage [V]"]` at SOC=0.62 | Δ < 10 mV |
| OCV at 30% SOC | at SOC=0.30 | Δ < 10 mV |
| IMP (mΩ) | DCIR from HPPC simulation | Δ < 15 % |
| ACT Capacity (mAh) | Simulated capacity | Trend alignment |
| K-value (mV/h) | Self-discharge (calendar aging) | Order-of-magnitude |
| Thickness at full charge | **NOT AVAILABLE** | — (Category D) |

---

## 8.5 Category D (범위 외, PyBaMM 불가)

| 분류 | 예시 |
|------|------|
| **기구 치수** | X/Y 크기, terrace, tab distance, sealant width |
| **공정 조건** | Mixing RPM, coating speed, pressing tension, welding |
| **품질 검사** | Overhang, burr, peel strength, Hi-pot |
| **수율 관리** | Defect rate, failure mode tracking |
| **소재 IQC (물리)** | BET, pH, residual Li, magnetic impurity, moisture |
| **기계적 안전성** | Dent, nail penetration (internal short) |
| **가스 스웰링** | Thickness at full charge — gas generation |

---

# 9. 권장 조사 우선순위

---

## 9.1 최종 TOP 20 (PPT 집중 조사 대상)

### Input Parameters Top 10

| 순위 | 파라미터 | 카테고리 | 중요도 근거 |
|:---:|---------|---------|-----------|
| 1 | `Positive electrode thickness [m]` | Geometry | 용량·저항 지배 |
| 2 | `Negative electrode thickness [m]` | Geometry | 용량·저항 지배 |
| 3 | `Positive particle radius [m]` | Geometry | 율특성 τ = r²/D |
| 4 | `Negative particle radius [m]` | Geometry | 율특성 |
| 5 | `Positive electrode active material volume fraction` | Material | 용량 직접 결정 |
| 6 | `Negative electrode active material volume fraction` | Material | 용량 직접 결정 |
| 7 | `Maximum concentration in positive electrode [mol.m-3]` | Material | c_max — 이론 용량 |
| 8 | `Maximum concentration in negative electrode [mol.m-3]` | Material | c_max |
| 9 | `Positive / Negative electrode OCP [V]` | Thermodynamics | V-SOC 곡선 결정 |
| 10 | `Ambient temperature [K]` | Boundary | 전 반응 Arrhenius 영향 |

### Output Variables Top 10

| 순위 | 변수 | 카테고리 | 중요도 근거 |
|:---:|-----|---------|-----------|
| 1 | `Terminal voltage [V]` | 기본 전기 | 가장 기본 출력 |
| 2 | `Current [A]` | 기본 전기 | 충방전 프로파일 |
| 3 | `Discharge capacity [A.h]` | 기본 전기 | 용량-전압 분석 |
| 4 | `X-averaged positive/negative electrode extent of lithiation` | 양극/음극 | SOC 정규화 |
| 5 | `X-averaged positive/negative electrode OCP [V]` | 전압 분해 | Electrode Balance 플롯 |
| 6 | `Volume-averaged cell temperature [C]` | 열 | 발열 모니터링 |
| 7 | `Volume-averaged Ohmic/Irreversible/Reversible heating [W.m-3]` | 열 | 발열 분해 |
| 8 | `X-averaged negative electrode potential [V]` | 음극 | 리튬 석출 감시 (0V 근접) |
| 9 | `X-averaged negative electrode lithium plating reaction overpotential [V]` | 음극 | 안전성 |
| 10 | `LLI [%]` / `LAM_pe [%]` / `LAM_ne [%]` | 열화 | 수명 정량 지표 |

---

## 9.2 조사 로드맵 (PPT 발표 흐름 제안)

```
[Slide 1]  PyBaMM이란? (1 슬라이드)
[Slide 2]  변수 규모 개요 — 70 input + 510 output
[Slide 3]  모델 계층 SPM/SPMe/DFN (1 슬라이드)
─────────────────────────────────────────────────
[Slide 4-6]   Tier 1 Input 9개 (각 변수 도해)
[Slide 7-9]   Tier 1 Output 6개
─────────────────────────────────────────────────
[Slide 10-12] Tier 2 주요 변수 (소재 물성, 수송)
[Slide 13]    Tier 2 열/수명 변수
─────────────────────────────────────────────────
[Slide 14]    모델별 변수 차이 매트릭스
[Slide 15]    BDT 현재 커버리지 (34 input + 15 output)
[Slide 16]    실측 매칭 4-Category 시스템
─────────────────────────────────────────────────
[Slide 17]    TOP 20 조사 우선순위
[Slide 18]    확장 로드맵 — 미사용 변수 도입 제안
[Slide 19]    참고자료 / Q&A
```

---

# 10. 부록

---

## 10.1 PyBaMM 내장 Parameter Set 목록

| Set | Chemistry | 저자 | 주요 용도 |
|-----|-----------|------|----------|
| `Marquis2019` | Graphite / LiCoO2 | Marquis 2019 | PyBaMM 초기 기본값, SPM/DFN 튜토리얼 |
| `Chen2020` | Graphite / NMC622 | Chen 2020 | LG M50 21700, 가장 일반적 |
| `Ecker2015` | Graphite / NMC111 | Ecker 2015 | EV 어플리케이션 |
| `OKane2022` | Gr(Si) / NMC811 | O'Kane 2022 | **열화 + 리튬석출 모델** (BDT 기본값) |
| `ORegan2022` | Graphite / NMC | O'Regan 2022 | 비등방성 물성 상세 |
| `Ai2020` | Graphite / NMC | Ai 2020 | 기계적 응력 / 팽창 |
| `Mohtat2020` | NMC / Graphite | Mohtat 2020 | GM 파우치 |
| `Ramadass2004` | Graphite / LCO | Ramadass 2004 | SEI 열화 고전 논문 |
| `NCA_Kim2011` | NCA / Graphite | Kim 2011 | NCA 화학 |
| `Prada2013` | LFP / Graphite | Prada 2013 | LFP 셀 |
| `Chen2020_composite` | Gr+Si / NMC622 | Chen 2020 | Silicon composite |
| `Xu2019` | NMC622 / Graphite | Xu 2019 | Half-cell |
| `MSMR_example` | - | - | Multi-species Multi-reaction 데모 |

---

## 10.2 변수 탐색 코드 스니펫

```python
import pybamm

# 1. 전체 output variables 리스트
model = pybamm.lithium_ion.DFN()
all_vars = list(model.variables.keys())
print(f"총 {len(all_vars)}개 출력 변수")

# 2. 키워드 검색
matches = [v for v in all_vars if "overpotential" in v.lower()]
for v in matches:
    print(v)

# 3. Parameter set 전체 확인
param = pybamm.ParameterValues("OKane2022")
for k, v in param.items():
    print(f"{k}: {v}")

# 4. 특정 파라미터 검색
param.search("conductivity")
# → Electrolyte conductivity [S.m-1]: ...
#    Positive electrode conductivity [S.m-1]: 0.18
#    ...

# 5. Solution 추출
sim = pybamm.Simulation(model, parameter_values=param)
sol = sim.solve([0, 3600])
V = sol["Terminal voltage [V]"].entries   # 시간축 1D
c = sol["Positive particle concentration [mol.m-3]"].entries  # (R, X, T) 3D
```

---

## 10.3 단위 변환 치트시트

| 개발부서 단위 | PyBaMM 단위 | 스케일 |
|-------------|------------|-------|
| μm (두께/입자) | m | ×1e-6 |
| mm (전극 폭/높이) | m | ×1e-3 |
| °C (온도) | K | +273.15 |
| mAh (용량) | A·h | ÷1000 |
| mΩ (저항) | Ω | ÷1000 |
| M (전해질 농도) | mol.m-3 | ×1000 |
| g/cc (밀도) | kg.m-3 | ×1000 |
| mA/cm² (전류밀도) | A/m² | ×10 |
| Wh/kg (비에너지) | J/kg | ×3600 |

---

## 10.4 참고 자료

### 공식
- [PyBaMM GitHub](https://github.com/pybamm-team/PyBaMM)
- [PyBaMM Docs](https://docs.pybamm.org/)
- [DFN Notebook](https://github.com/pybamm-team/PyBaMM/blob/develop/docs/source/examples/notebooks/models/DFN.ipynb)

### BDT 프로젝트 내부
- [[Electrochemical_parameter]] — 전기화학 파라미터 정의
- [[Battery_Electrochemical_properties]] — 셀 물성 목록
- [[Battery_Science_MOC]] — 배터리 과학 MOC
- `.github/instructions/pybamm.instructions.md` — BDT PyBaMM 코딩 가이드
- `docs/code/02_변경검토/pybamm_output_variables_260226.md` — 출력 변수 전수 리스트
- `DataTool_optRCD_proto_.py` (라인 10523-10717, 31413-31910, 32432-32510)

### 대표 논문 (Chemistry별)
- Marquis 2019 — *J. Electrochem. Soc.* 166(15):A3693 (Marquis set)
- Chen 2020 — *J. Electrochem. Soc.* 167(8):080534 (LG M50 파라미터)
- O'Kane 2022 — *PCCP* 24:7909 (리튬 석출 + SEI 크랙)
- O'Regan 2022 — *Electrochim. Acta* 425:140700 (비등방성 물성)

---

## 10.5 용어 요약 (Glossary)

| 용어 | 설명 |
|------|------|
| **SPM** | Single Particle Model — 대표 입자 1개 |
| **SPMe** | SPM with electrolyte — SPM + 전해질 확산 |
| **DFN** | Doyle-Fuller-Newman — Full P2D 모델 |
| **OCP** | Open-Circuit Potential — 단일 전극 개방 전위 |
| **OCV** | Open-Circuit Voltage — 셀 단자 개방 전압 (= U_pos - U_neg) |
| **Stoichiometry** | 화학양론비 = c/c_max (0~1) |
| **Extent of lithiation** | 리튬화 정도 — stoichiometry와 동일 or 변환 관계 |
| **η (eta)** | Overpotential — 평형 전위에서 벗어난 정도 |
| **LLI** | Loss of Lithium Inventory — 리튬 인벤토리 손실 |
| **LAM** | Loss of Active Material — 활물질 손실 (pe/ne) |
| **SEI** | Solid-Electrolyte Interphase — 전극 표면 피막 |
| **X-averaged** | x(두께) 방향 공간 평균 |
| **R-averaged** | r(입자 반경) 방향 공간 평균 |
| **Bruggeman coefficient** | 다공성 매체 유효 수송 보정 계수 (보통 1.5) |

---

*문서 생성: 2026-04-21 / PyBaMM v25.12.2 기준*
*작성자 기여: 조사 결과를 PPT로 변환 시 섹션별 슬라이드 분리 (`---` 구분선 기준) 권장*
