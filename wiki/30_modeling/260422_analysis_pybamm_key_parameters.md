---
title: "PyBaMM Key 파라미터 — Rate-determining × 셀 개발 설계 이중 관점"
date: 2026-04-22
tags: [pybamm, parameters, rate-determining, cell-design, analysis]
type: analysis
status: active
aliases:
  - PyBaMM 핵심 파라미터
  - Key parameter 도출
  - 시뮬 vs 개발 관점
related:
  - "[[PyBaMM_Variables_PPT]]"
  - "[[합제밀도와_전류밀도]]"
  - "[[충방전_매커니즘]]"
  - "[[전해액]]"
  - "[[MX배터리그룹_평가항목]]"
  - "[[PyBaMM_정리]]"
  - "[[Silicon]]"
created: 2026-04-22
---

# PyBaMM Key 파라미터 도출 — Rate-determining × 셀 개발 설계 이중 관점

> 전체 파라미터 리스트는 [[PyBaMM_Variables_PPT]] 참조 (Input ~70 + Output 510~517).
> 본 문서는 그 중 **"실제로 중요한"** 파라미터를 두 축으로 선별하고 교차 분석한다.

---

## 🎯 목적

PyBaMM 입력 파라미터 ~70개 중 의미 있는 소수를 뽑으려면 **일관된 선별 기준**이 필요하다. 두 가지 상보적 관점을 사용한다:

| 관점 | 기준 | 질문 |
|------|------|------|
| **A. Rate-determining step** | 전기화학·물리 이론 | 전체 시스템 속도를 지배하는 가장 느린 단계는 무엇인가? |
| **B. 셀 개발 설계** | R&D 실무 제어 변수 | 개발부서가 실제로 돌릴 수 있는 knob 은 무엇인가? |

두 관점에서 공통으로 핵심인 파라미터가 **진짜 key parameter**다.

---

# 1. 관점 A — Rate-determining Step 기반

## 1.1 Li⁺ 이동 경로와 단계별 시간상수

충방전 중 Li⁺ 이온은 양극 ↔ 음극 간 7단계 경로를 거친다 ([[충방전_매커니즘]]의 주차타워 비유 참조).

```
 ┌─ ① 전자 전도 (고상) ─────────── 양극 집전체 → 활물질
 │  τ ~ (thickness) × ρ_e / κ_s    μs ~ ms (보통 빠름)
 │
 ├─ ② 고상 확산 (양극 입자) ───── Li 이탈
 │  τ_p = r_p² / D_s,p             수 초 ~ 분 (입자 크기 지배)
 │
 ├─ ③ 계면 반응 (양극) ─────────── Butler-Volmer η
 │  ∝ 1 / j₀,p                     ms ~ 초
 │
 ├─ ④ 전해질 수송 ────────────── 양극→분리막→음극
 │  τ_e = L_tot² / D_e_eff         수 초 (농도·전도도 지배)
 │
 ├─ ⑤ 계면 반응 (음극) ─────────── Butler-Volmer η  ← 리튬 석출 여기서
 │  ∝ 1 / j₀,n                     ms ~ 초 (급충 시 핵심)
 │
 ├─ ⑥ 고상 확산 (음극 입자) ───── Li 삽입
 │  τ_n = r_n² / D_s,n             수 초 ~ 분 (Gr D~1e-14 m²/s)
 │
 └─ ⑦ 전자 전도 (음극) ─────────── 활물질 → 집전체
    보통 가장 빠름
```

**직렬 결합 특성**: 총 시간 τ_total ≈ max(τᵢ) (가장 느린 단계가 지배). 이것이 "Rate-determining step" 개념. 동시에 해당 단계에 **damage 집중** — Li plating, 구조 파괴 등.

## 1.2 단계별 PyBaMM 파라미터 매핑

| 경로 | 속도 결정 주요 파라미터 (PyBaMM key) | 보조 파라미터 |
|------|------------------------------------|--------------|
| ① 양극 고상 전도 | `Positive electrode conductivity [S.m-1]` | `Positive electrode thickness [m]` |
| **② 양극 고상 확산** | `Positive particle diffusivity [m2.s-1]` (D_s,p, 함수형), `Positive particle radius [m]` (r_p) | `Maximum concentration in positive electrode [mol.m-3]` |
| **③ 양극 계면 반응** | `Positive electrode exchange-current density [A.m-2]` (j₀,p, 함수형) | `Positive electrode charge transfer coefficient` (α) |
| **④ 전해질 수송** | `Electrolyte diffusivity [m2.s-1]` (D_e), `Electrolyte conductivity [S.m-1]` (κ_e), `Initial concentration in electrolyte [mol.m-3]` (c_e,0) | `Cation transference number` (t₊), `Thermodynamic factor`, `Bruggeman coefficients`, `Separator porosity`, `electrode porosity` |
| **⑤ 음극 계면 반응** | `Negative electrode exchange-current density [A.m-2]` (j₀,n) — **Li plating 여기서 경쟁** | `Negative electrode charge transfer coefficient`, `Lithium plating kinetic rate constant [m.s-1]` |
| **⑥ 음극 고상 확산** | `Negative particle diffusivity [m2.s-1]` (D_s,n), `Negative particle radius [m]` (r_n) | `Maximum concentration in negative electrode` |
| ⑦ 음극 고상 전도 | `Negative electrode conductivity [S.m-1]` | `Negative current collector conductivity` |
| 전체 온도 의존 | `Ambient temperature [K]` (Arrhenius로 ②③⑤⑥ 모두 가속) | `Reference temperature [K]` |

## 1.3 OCV / Diffusivity 관점의 추가 인사이트

- **OCV 자체는 thermodynamic** (속도 ≠). 그러나 **dU/dx 기울기**는 농도 과전압에 직접 영향:
  - Plateau(상변화) 구간: dU/dx ≈ 0 → 과전압 적음 → fast charge 유리
  - Steep slope 구간 (Gr 0.2~0.5 x): dU/dx 큼 → 확산 과전압 증폭
- **음극 OCP**: 0V vs Li/Li⁺ 근접 시 **리튬 석출** 리스크 급증. `Negative electrode OCP [V]` 함수 형상이 안전 마진을 결정.
- **양극 OCP**: 고전압 영역에서 구조 변화 (층상 → spinel-like) → Capacity fade 기원.

### Rate-determining 관점 Top 10

| 순위 | PyBaMM 파라미터 | 왜 핵심인가 |
|:---:|----------------|-----------|
| 1 | `Negative particle radius [m]` | τ_n = r_n²/D — 제곱 효과. 급속 충전 한계의 최대 요인 |
| 2 | `Negative particle diffusivity [m2.s-1]` | Gr D_s ~ 1e-14 m²/s로 시스템 최저. 직접 rate-limiting |
| 3 | `Negative electrode OCP [V]` | 0V 근접도가 Li plating 안전 마진 결정 |
| 4 | `Positive particle radius [m]` | τ_p. NMC는 D가 음극보다 느릴 때도 있음 (1e-15) |
| 5 | `Positive particle diffusivity [m2.s-1]` | r_p 와 조합으로 양극 측 율특성 |
| 6 | `Electrolyte diffusivity [m2.s-1]` | 전해질 수송 — 고율·저온에서 병목 |
| 7 | `Electrolyte conductivity [S.m-1]` | 전해질 Ohmic + 농도분극 |
| 8 | `Negative electrode exchange-current density [A.m-2]` | 음극 계면 반응. Li plating과 SEI intercalation 경쟁 지배 |
| 9 | `Positive electrode OCP [V]` | 충전 말기 고전압 damage 기준 |
| 10 | `Ambient temperature [K]` | 모든 Arrhenius 과정 공통 스케일링 |

---

# 2. 관점 B — 셀 개발 설계 실무 변수

[[MX배터리그룹_평가항목]], [[합제밀도와_전류밀도]], [[전해액]], [[충방전_매커니즘]] 에서 R&D 현장이 실제로 "설계 knob" 으로 돌리는 변수를 추린다.

## 2.1 전극 설계 (Geometry × Material)

| 개발 제어 변수 | 실무 의미 | PyBaMM 연결 |
|--------------|----------|-----------|
| **전극 두께** (μm) | 에너지 vs 파워 균형. 두꺼우면 용량↑ 저항↑ | `Positive/Negative electrode thickness [m]` |
| **합제밀도** (g/cc) | ρ_press = LL / thickness. 누를수록 활물질 밀집 | `Electrode active material volume fraction` (+ `porosity`, Bruggeman 간접) |
| **L/L (Loading, mg/cm²)** | 단위 면적 활물질량 | 두께 × 합제밀도 (derived) |
| **활물질 비용량** (mAh/g) | 소재 고유 — NMC622 ~175, Gr ~355 | `Maximum concentration in electrode [mol.m-3]` (c_max = Q·ρ·3.6/F) |
| **전류밀도** (mA/cm²) | = 용량 / 반응면적 · 1h (양극 기준) | `Current function [A]` / (`Electrode width` × `height` × 적층수) |
| **N/P ratio** | 음극 용량 / 양극 용량 (보통 1.08~1.15) | `Initial concentration in [pos/neg] electrode` + 두께·체적분율로 계산됨 (직접 키 없음) |
| **입자 크기 D50** (μm) | 소립자↑ → 표면적↑ 파워↑, but 에너지↓ 부반응↑ | `Positive/Negative particle radius [m]` = D50/2 |
| **대립자/소립자 비중 (bi-modal)** | 대립자로 탭밀도↑ + 소립자로 반응성↑ | **기본 DFN 미지원**; MPM (`Multi-Particle Model`) 또는 particle size distribution 옵션 필요 |

### 합제밀도 ↔ PyBaMM 정량 변환 ([[합제밀도와_전류밀도]] 기반)

$$\varepsilon_{AM} = \frac{\rho_{press} \cdot w_{AM}}{\rho_{true,AM}}, \quad \varepsilon_{pore} = 1 - \frac{\rho_{press}}{\rho_{true,composite}}$$

- ρ_press ↑ → ε_AM ↑ (활물질 체적분율 ↑, 용량 ↑), 동시에 ε_pore ↓ (공극 ↓, 전해질 수송 ↓)
- 이 trade-off가 rate-determining 관점 ④ (전해질 수송) 와 ①⑦ (고상 전도) 의 경쟁을 만든다.

## 2.2 전해액 설계

[[전해액]] DOE 기반:

| 개발 변수 | 실무 의미 | PyBaMM 매핑 | 비고 |
|----------|---------|-----------|------|
| **염 농도** (M, 보통 1.0~1.35) | 너무 묽음 → 전도도↓, 너무 진함 → 점도↑ | `Initial concentration in electrolyte [mol.m-3]` | 최적점 존재 (보통 1.0~1.2M) |
| **용매 조성** (EC/DMC/EMC/PC 비율) | 점도·저온·SEI 형성 특성 | `Electrolyte diffusivity`, `Electrolyte conductivity` 함수형 (Nyman2008 등) | 조성별 물성 함수 교체 필요 |
| **첨가제 FEC** | 음극 SEI 안정화 (Si, Li plating 방어) | `SEI kinetic rate constant`, `Negative exchange current` 간접 | 직접 입력 키 없음 — SEI/plating 모델 파라미터로 |
| **첨가제 PS / LiDFOB** | 고온 안정, 양극 표면 보호 | SEI 성장 속도, cathode interfacial kinetics | 마찬가지 간접 |
| **주액량 (g/Ah)** | 실제 전해질 총량. 1.25~1.35 typical | PyBaMM 1D 모델 직접 없음 — `Electrolyte concentration` 유지 가정 | 장기 수명에서 고갈 고려 시 확장 필요 |

> **첨가제는 PyBaMM 1D 기본 모델에 직접 입력 키가 없다.** SEI/plating 서브모델의 kinetic constant 를 간접 튜닝해야 하며, 이는 측정 기반 파라미터 피팅 영역.

## 2.3 셀 시스템 설계

| 개발 변수 | PyBaMM 매핑 |
|----------|-----------|
| **적층수 / 병렬 셀** | `Number of electrodes connected in parallel to make a cell` |
| **분리막 두께** (μm) | `Separator thickness [m]` |
| **분리막 기공률** | `Separator porosity`, `Separator Bruggeman` |
| **상/하한 전압** | `Upper / Lower voltage cut-off [V]` |
| **충전 알고리즘** (다단 CC-CV) | `Experiment` string — `Current function [A]` 과 결합 |
| **작동 온도** | `Ambient temperature [K]`, `Initial temperature [K]` |
| **열전달 계수** | `Total heat transfer coefficient [W.m-2.K-1]` |

### 개발 관점 Top 10

| 순위 | 개발 변수 | PyBaMM 대응 |
|:---:|---------|-----------|
| 1 | 전극 두께 (양/음극) | `Positive/Negative electrode thickness [m]` |
| 2 | 합제밀도 → 활물질 체적분율 | `Positive/Negative electrode active material volume fraction` + `porosity` |
| 3 | 입자 D50 → 반경 | `Positive/Negative particle radius [m]` |
| 4 | 활물질 비용량 → c_max | `Maximum concentration in positive/negative electrode [mol.m-3]` |
| 5 | N/P ratio | 초기 농도 + 두께·체적분율 조합 (계산) |
| 6 | 전류밀도 | `Current function [A]` + 전극 면적 |
| 7 | 전해액 염 농도 | `Initial concentration in electrolyte [mol.m-3]` |
| 8 | 전해액 첨가제 (FEC 등) | SEI / Li plating kinetic rate (간접) |
| 9 | 분리막 두께·기공률 | `Separator thickness / porosity` |
| 10 | 상/하한 전압 | `Upper / Lower voltage cut-off [V]` |

---

# 3. 두 관점 연관성 매트릭스

각 개발 변수가 어떤 Rate-determining 단계를 어떻게 움직이는지. **↑↑** = 강한 양의 효과, **↓↓** = 강한 감속, **↔** = 영향 미미.

| 개발 변수 (B) \ Rate 단계 (A) | ① 고상 전도 | ② 양극 Ds | ③ 양극 반응 | ④ 전해질 수송 | ⑤ 음극 반응 (Li plating) | ⑥ 음극 Ds | 온도 (공통) |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| 양극 두께 ↑ | ↓ | ↔ | ↔ | ↓↓ (경로 길이↑) | ↔ | ↔ | ↔ |
| 음극 두께 ↑ | ↓ | ↔ | ↔ | ↓↓ | ↓ (과전압↑) | ↔ | ↔ |
| 양극 합제밀도 ↑ | ↑↑ (밀집·전도도) | ↔ | ↔ | ↓↓ (공극↓) | ↔ | ↔ | ↔ |
| 음극 합제밀도 ↑ | ↑↑ | ↔ | ↔ | ↓↓ | ↓ (Li plating 위험↑) | ↔ | ↔ |
| 양극 입자 반경 r_p ↓ | ↔ | **↑↑** (τ=r²/D 제곱) | ↑ (표면적↑, j 실효↑) | ↔ | ↔ | ↔ | ↔ |
| 음극 입자 반경 r_n ↓ | ↔ | ↔ | ↔ | ↔ | ↑ (면적↑ → j plating 여유) | **↑↑** (제곱) | ↔ |
| 대립자/소립자 bi-modal | ↔ | ↑ (소립자 dominant) | ↑ | ↔ | ↑ | ↑ | ↔ |
| N/P ratio 1.1→1.15 | ↔ | ↔ | ↔ | ↔ | **↑↑ (Li plating 방어)** | ↔ | ↔ |
| 전류밀도 ↑ | ↓ (IR↑) | ↓ (구배↑) | ↓↓ (η↑) | ↓↓ (구배↑) | ↓↓ (Li plating 가속) | ↓ | 발열↑ |
| 전해액 농도 ↑ | ↔ | ↔ | ↑ (공급↑) | 비선형 (~1.2M 최적) | ↑ | ↔ | ↔ |
| 첨가제 FEC | ↔ | ↔ | ↔ | ↔ (일부 점도) | ↑↑ (SEI 안정·plating 방어) | ↔ | ↔ |
| 첨가제 LiDFOB | ↔ | ↔ | ↑ (양극 SEI 안정) | ↔ | ↔ | ↔ | ↔ |
| 분리막 기공률 ↑ | ↔ | ↔ | ↔ | ↑↑ | ↔ | ↔ | ↔ |
| 분리막 두께 ↓ | ↔ | ↔ | ↔ | ↑↑ (경로 단축) | ↔ | ↔ | ↔ |
| 온도 ↑ (상온 내) | ↑ | ↑ (Arrhenius) | ↑ | ↑ | ↑ (두 측면: 반응 촉진 / 전해질 분해↑) | ↑ | — |

### 핵심 관찰

1. **음극 입자 반경**이 두 관점 모두의 최상위 공통 knob. 줄이면 ⑥τ_n 제곱으로 감소 + ⑤ Li plating 여유 확보. 단, 부반응 표면적 증가로 수명 측면 trade-off.
2. **합제밀도**는 ①⑦(고상 전도)에는 양, ④(전해질 수송)에는 음. **최적점 존재**. [[합제밀도와_전류밀도]] 의 실무 관측과 정합.
3. **N/P ratio**는 열역학적 방어 (Li plating margin) — rate-determining 단계를 바꾸지는 않지만 ⑤의 damage 한계를 넓힘.
4. **전해액 첨가제**는 PyBaMM 1D 직접 키가 없고 SEI/plating kinetic 파라미터로 **간접 반영**. 이 영역이 simulation과 실측의 gap.
5. **전류밀도**는 모든 단계 과전압을 동시에 키운다. 개발에서 "낮출 수 있으면 낮추되" 에너지밀도 타협 필요.

---

# 4. 이중 관점 결합 Tier

두 관점 Top 10을 교차 집계해 **진짜 key parameter**를 뽑는다.

## 4.1 Tier S — 두 관점 모두 Top 10 (이중 핵심, 8개)

| 파라미터 | Rate 순위 | 개발 순위 | 비고 |
|---------|:--------:|:--------:|------|
| `Negative particle radius [m]` | **1** | **3** | 급속 충전 한계의 1순위 knob |
| `Positive particle radius [m]` | 4 | 3 | 양극 율특성, bi-modal |
| `Negative particle diffusivity [m2.s-1]` | **2** | (간접, 소재로 결정) | Gr/Si 소재 선택의 본질 |
| `Positive particle diffusivity [m2.s-1]` | 5 | (간접) | NMC vs LFP 차이 |
| `Electrolyte diffusivity [m2.s-1]` | 6 | 7 (농도·조성) | 용매·염으로 튜닝 |
| `Electrolyte conductivity [S.m-1]` | 7 | 7 | 염 농도·용매 조성 |
| `Ambient temperature [K]` | **10** | 경계 조건 | 전 반응 Arrhenius |
| `Negative electrode OCP [V]` | **3** | (소재) | Gr vs Si vs LTO |

## 4.2 Tier A — 한 관점 Top 10 + 다른 관점 강한 영향 (6개)

| 파라미터 | 대표 관점 | 다른 관점 연결 |
|---------|---------|--------------|
| `Positive/Negative electrode thickness [m]` | 개발 #1 | 전해질 수송 ④ 강하게 영향 |
| `Positive/Negative electrode active material volume fraction` | 개발 #2 (합제밀도) | 고상 전도 ①⑦ ↔ 전해질 ④ 경쟁 |
| `Maximum concentration in positive/negative electrode [mol.m-3]` | 개발 #4 (비용량) | 양극 Ds 구배·OCV 기울기 조정 |
| `Initial concentration in electrolyte [mol.m-3]` | 개발 #7 | 전해질 수송 ④ 비선형 최적점 |
| `Current function [A]` | 개발 #6 | 모든 단계 과전압 스케일링 |
| `Upper / Lower voltage cut-off [V]` | 개발 #10 | 양극 OCP damage 한계, 음극 석출 한계 |

## 4.3 Tier B — 주로 한 관점 (5개)

| 파라미터 | 주 관점 | 비고 |
|---------|--------|------|
| `Negative electrode exchange-current density [A.m-2]` | Rate #8 | 측정 어려움 (GITT로 간접) |
| `Positive electrode exchange-current density [A.m-2]` | Rate | 측정 어려움 |
| `Separator thickness / porosity / Bruggeman` | 개발 #9 | 사급자재 스펙 |
| `Number of electrodes in parallel` | 개발 | 셀 구조 설계 |
| `Total heat transfer coefficient` | 개발 (열) | 패키지 설계 |

## 4.4 Tier C — 간접/소재 선택으로 결정 (이 리스트 밖)

- Charge transfer coefficient (α) — 보통 0.5 고정
- Cation transference number (t₊) — 전해액 고유 물성
- Thermodynamic factor — 전해액 고유
- Bruggeman (전극) — 합제밀도와 연계
- OCP entropic change — 측정 가능하나 2차적

## 4.5 Tier D — 첨가제/특수 모델 (PyBaMM 기본 DFN 범위 밖)

- FEC, VEC, PS, LiDFOB 등 첨가제 → SEI kinetic rate / Li plating kinetic rate 간접
- 대립자/소립자 bi-modal → **MPM (Multi-Particle Model)** 또는 `particle-size distribution` 옵션 필요
- 주액량 (g/Ah) → 전해질 고갈 모델 확장 시

---

# 5. BDT 프로젝트 적용 권장

## 5.1 BDT 현재 커버리지 (from [[PyBaMM_Variables_PPT]])

BDT `_key_map` / `_key_map_extended` 는 **34개 입력 파라미터** 지원. Tier S/A 대부분 포함하지만 누락·미흡:

| Tier | 항목 | BDT 지원 | 비고 |
|------|------|:--------:|------|
| S | `Negative/Positive particle radius` | ✅ | — |
| S | `Negative/Positive particle diffusivity` | ✅ (값 입력) | 함수형(T·c 의존) 지원은 미흡 |
| S | `Electrolyte diffusivity/conductivity` | ✅ (값 입력) | 함수형 미흡 |
| S | `Ambient temperature` | ✅ | — |
| S | `Negative electrode OCP [V]` | ✅ (함수형) | 프리셋 함수 사용, 커스텀 곡선 입력 UX 없음 |
| A | 전극 두께 | ✅ | — |
| A | 활물질 체적분율 | ✅ | — |
| A | 최대 농도 (c_max) | ✅ | — |
| A | 전해액 초기 농도 | ✅ | — |
| A | Current function | (간접, Experiment 문자열) | 직접 키 아님 |
| A | 상/하한 전압 | ✅ | — |

## 5.2 도입 권장 기능 (BDT 확장 아이디어)

1. **Rate-determining Step Visualizer** — 한 시뮬 결과에서 각 단계 τ 를 자동 계산·막대그래프. 음극 Ds, r_n 우세성 즉시 확인.
2. **합제밀도 Trade-off 탐색** — ρ_press 슬라이더로 (ε_AM, porosity) 동시 업데이트 → 용량 vs 율특성 Pareto 커브.
3. **N/P ratio 슬라이더** — 초기 stoichiometry 조정으로 Li plating 안전 마진 시뮬레이션.
4. **입자 bi-modal 확장** — PyBaMM MPM 모델 지원, 대/소립자 비중 입력.
5. **첨가제 효과 매핑 테이블** — 첨가제별 SEI kinetic rate 튜닝 값 프리셋 (FEC, LiDFOB 등).
6. **전해액 함수형 교체 UI** — 조성별 D_e(c,T), κ_e(c,T) 함수 선택 (Nyman2008, Landesfeind2019 등).

## 5.3 개발부서 실측값 → 시뮬 파라미터 변환 우선순위

1. **Design Sheet 필수** (즉시 시뮬 가능): 전극 두께, 전극 폭·높이, 적층수, 공칭 용량, 상/하한 전압, 온도
2. **IQC 물성** (변환 필요): D50 → r, 1st discharge capacity → c_max, 1st efficiency → LLI_init
3. **합제밀도 + 배합비** → 활물질 체적분율, 공극률
4. **전해액 조성** → 염 농도 직접; 확산·전도도는 함수형 프리셋 교체
5. **첨가제** → **직접 변환 불가**. 가속수명 실측 → SEI/plating kinetic 피팅 → 역대입

---

# 6. 단순화 가정 맵 — 변환의 본질

> **핵심 원리**: PyBaMM (또는 어떤 1D 전기화학 모델이든) 은 실제 셀의 물리 전부를 담지 못한다. 시뮬을 쓴다는 것은 **"어떤 물리를 버리고 어떤 물리를 살릴지"** 를 선언하는 것이고, 셀 설계변수를 모델 파라미터로 변환하는 모든 식은 **단순화 가정의 집합**이다.

앞서 도출한 Tier S/A 14개 파라미터도, 실무 knob 에서 PyBaMM 숫자로 넘어가는 순간 가정이 개입한다. 실측과 Δ 가 나왔을 때, 모델이 틀렸다기보다 **가정이 적용 범위를 벗어난 것**이다. 이 섹션은 그 가정들을 명시적으로 펼쳐 놓는다.

## 6.1 PyBaMM 1D 모델이 기본적으로 버리는 물리

| 가정 범주 | 단순화 내용 | 실제 셀은 어떻게 다른가 |
|----------|------------|-----------------|
| **공간 차원** | 두께 방향 (x) 1D + 입자 반경 (r) | 면내(y,z) 불균일, tab 근처 과전압, 권심 vs edge 전류밀도 차이 |
| **입자 형상** | 완전 구형 (sphere), 단일 반경 r | 실제 다분산 D50, 판상/비구형, 표면 crack, 대·소립자 혼합 |
| **입자 분포** | 활물질 균일하게 두께 방향 분포 | 바인더·도전재 표면 집중 (binder migration), slurry drying 편차 |
| **전해질 이론** | Dilute solution Nernst-Planck | 고농도에서 thermodynamic factor 비선형, solvent drag |
| **계면 반응** | Butler-Volmer, α=0.5 대칭 | 실제 α 비대칭, 다단 반응, adsorption 단계 |
| **전극 구조** | Bruggeman τ = ε^(1-β) | 실제 τ는 구조 의존, binder/도전재 네트워크에 민감 |
| **기계적 변형** | 없거나 단순 porosity change | Si 음극 체적 팽창 300%, 국부 압력 변화, 입자 crack 진전 |
| **열 모델** | Lumped 또는 x 방향 1D | 국부 hot-spot, tab 발열 집중, 권심 열축적 |
| **SEI / Li plating** | 면적 평균 성장률, 단일 화학종 | 실제 다층 SEI · 불균일 · dead lithium 회복 가역성 |
| **가스 발생** | 없음 | CO₂, CO, H₂ 발생 → 스웰링 (PyBaMM 범위 밖) |
| **파우치/기구** | 무시 (cell-level만) | Sealant, terrace, tab welding 저항 |

## 6.2 설계변수 → 모델 파라미터 변환에 내재된 가정 8가지

개발부서가 쓰는 실무 변수를 PyBaMM 숫자로 넘길 때마다 아래 가정들이 붙는다. **변환식 + 가정 + 유효 범위 + 파탄 지표** 네 가지를 세트로 기록해야 실무에 쓸 수 있다.

### 가정 A1: 합제밀도 → 활물질 체적분율
$$\varepsilon_{AM} = \rho_{press} \cdot w_{AM} / \rho_{true,AM}$$
- **가정**: 바인더·도전재 진밀도와 배합비가 이론값과 정확히 일치. 활물질/공극 모두 균일 분포.
- **유효 범위**: 표준 NMP 슬러리 + 양호한 슬릿팅/프레스 공정.
- **파탄 조건**: binder migration (건조 중 표면 집중), 도전재 네트워크 불균일, 프레스 불균일 (edge/center Δ).
- **파탄 지표**: 실측 용량 < 이론 용량의 97% 이하, 면적별 두께 편차 > 4 μm.

### 가정 A2: D50 → 단일 particle radius
$$r = D_{50} / 2$$
- **가정**: 단일 대표 입자. 입자 분포의 고차 모멘트(분산, 왜도) 무시.
- **유효 범위**: 단봉(unimodal) 좁은 PSD.
- **파탄 조건**: Bi-modal (의도 or 자연), agglomerate, 큰 span (D90/D10).
- **파탄 지표**: 실측 rate capability 곡선이 단일 r 시뮬과 특정 C-rate 구간에서 크게 이탈.
- **대안**: PyBaMM **MPM** (Multi-Particle Model) 또는 particle-size distribution 옵션.

### 가정 A3: 1st discharge capacity (IQC) → c_max
$$c_{max} = Q_{theor}\,[\text{mAh/g}] \cdot 3.6 \cdot \rho_{AM}\,[\text{g/cm³}] / F \times 10^6$$
- **가정**: 측정 비용량 = 이론 최대. 1st efficiency 손실은 초기 LLI 로만 반영.
- **유효 범위**: Gr/NMC 표준 화학계.
- **파탄 조건**: 전극 kinetics 한계로 실제 full lithiation 도달 불가, Si의 계단식 상변화.
- **파탄 지표**: stoichiometry window 실측 vs 시뮬 Δx > 0.03.

### 가정 A4: N/P ratio → 초기 stoichiometry 조합
- **가정**: Formation 이후 stable. 수명 중 Li 분포 static.
- **유효 범위**: 초기 ~수십 사이클.
- **파탄 조건**: LAM_ne vs LAM_pe 비대칭 진행 → 동적 NP drift.
- **파탄 지표**: 수명 중 dV/dQ 피크 비대칭 이동.
- **대안**: 장기 수명 시뮬에서는 NP ratio 를 시간 함수로 업데이트.

### 가정 A5: 전해액 농도 → Initial electrolyte concentration
- **가정**: 주액 후 균일 확산, 시뮬 중 평균 1M 수준 유지.
- **유효 범위**: 함침 완료 ~ 초기 수백 사이클.
- **파탄 조건**: 주액 불균일 (wettability), 장기 분해·고갈, 가스 발생으로 부분 공극.
- **파탄 지표**: 고율 구간 전압 sagging 가속, 용량 knee point.
- **대안**: 전해액 총량을 상한 제약으로 넣는 확장 모델.

### 가정 A6: 전해액 첨가제 → SEI/plating kinetic rate
- **가정**: FEC, VEC, LiDFOB 등 복수 첨가제 효과를 SEI 성장 상수 1~2개 + plating rate constant 로 집약 가능.
- **유효 범위**: 단일 첨가제 주효일 때.
- **파탄 조건**: 첨가제 간 시너지·상충, 다층 SEI 형성, 첨가제 소모 동역학 (shelf-life).
- **파탄 지표**: 같은 셀 설계 + 다른 첨가제 조합 간 DCIR 트렌드 불일치.
- **대안**: **시뮬만으로 첨가제 설계 불가**. 첨가제별 가속수명 실측 → kinetic rate 역피팅 → 프리셋 구축.

### 가정 A7: 전류밀도 → Current function [A] × 면적
$$I [A] = j [A/m²] \times (W \times H \times N_{layers})$$
- **가정**: 면내 균일 전류 분포.
- **유효 범위**: 단일 셀, 표준 tab 위치.
- **파탄 조건**: Tab 근접 과전류, 권심 vs edge, 불균일 함침.
- **파탄 지표**: IR 드롭 면적별 편차, 실측 온도 맵 불균일.

### 가정 A8: 온도 → Ambient temperature (lumped)
- **가정**: 전 셀 단일 온도.
- **유효 범위**: 저율·중율, 환경 챔버 조건.
- **파탄 조건**: 고율 충전 국부 hot-spot, 권심 열축적.
- **파탄 지표**: 실측 온도 스프레드 > 5℃, 국부 Li plating (평균 온도로는 설명 불가).
- **대안**: PyBaMM `thermal=x-full` 옵션 (두께 방향 분포).

## 6.3 가정 조합이 시뮬 유효 범위를 결정한다

| 시뮬 시나리오 | 기본 DFN + 기본 가정 | 보완 필요 항목 |
|------------|----------------|--------------|
| **초기 율특성 (RPT 1회)** | ✅ 잘 맞음 | — |
| **CC-CV 풀사이클** | ✅ 대부분 OK | OCV hysteresis (Si 큰 경우) |
| **GITT / HPPC (DCIR)** | ✅ OK | 계면 동역학 파라미터 GITT 교정 |
| **1~10 사이클 열화** | 🟡 조심 | SEI + plating 서브모델, 파라미터 피팅 |
| **수백 사이클 수명** | ❌ 가정 다수 붕괴 | Dynamic N/P, 전해액 고갈, LAM, 크랙 모두 |
| **급속 충전 안전성** | 🟡 평균만 | 면내 불균일, 국부 온도 맵 |
| **첨가제 DOE** | ❌ 직접 불가 | kinetic rate 역피팅 경로 |
| **가스 스웰링** | ❌ 범위 밖 | PyBaMM 구조 확장 필요 |
| **기계적 / 관통 안전** | ❌ 범위 밖 | FEA·CFD 결합 |

## 6.4 실무 체크리스트 — 시뮬 적용 전 검증

```
□ 목적이 tier S/A 파라미터로 커버되는 물리인가? (rate·OCV·수명·열 중 무엇인가)
□ 각 입력값이 어떤 변환 가정을 거쳤는가? (A1~A8 중 해당 항목 리스트업)
□ 가정의 유효 범위 내에서 운용하는가? (C-rate, 온도, 사이클 수, 화학계)
□ 실측 vs 시뮬 Δ 허용 기준은? (전압 < 10 mV, 용량 < 2%, DCIR < 15%)
□ Δ 초과 시 파탄 지표로 어떤 가정이 깨졌는지 역추적 가능한가?
□ 없다면 어떤 서브모델·실측으로 보강할 것인가?
```

## 6.6 Gen5+ 실제 화학 조성 기반 가정 파탄 시나리오

> **Gen5+ ATL 실제 조성 (2026-04-22 사용자 확인)**:
> - 양극: **고전압 LCO** (LiCoO₂, 4.53V cut-off, Spec `Gen5 4.53V 2.0C PF-PTO`)
> - 음극: **Graphite** 또는 **Graphite + SiC** (Silicon-Carbon 복합, Si 5%~, EPF 공정)
> - 개발 방향: 양극 고전압화 ↑ + 음극 Si 함량 증가 ↑
>
> 이 조성은 가정 A1~A3 + 추가 A9·A10 을 **동시에** 흔든다.
> 상세 도메인 지식: [[Silicon]] (12편 문헌), [[양극별_특성]] (LCO 물성).

### 6.6.0 고전압 LCO 특화 — 가정 A3/A4 파탄

**표준 LCO (4.2V) 대비 고전압 LCO (4.53V)** 가 기본 DFN 에서 깨는 것:

| 물리 | 표준 LCO | Gen5+ LCO 4.53V | 가정 파탄 |
|------|:-----:|:-------------:|---------|
| 작동 x_p 범위 | 0.5 ~ 1.0 | **0.3 ~ 1.0** (deep delithiation) | A3 (c_max 기반 stoichiometry window) |
| OCP 함수 | 프리셋 커버 | **고전압 영역 미측정** | A3, 히스테리시스 |
| 구조 열화 | 극소 | **layered → spinel-like 가속** | LAM_pe 기본 무시 안 됨 |
| O₂ evolution | 없음 | **전해액 산화 가속** | SEI 서브모델 부족 |
| D_s SOC 의존 | 10⁻⁹~10⁻¹¹ | **고전압에서 급락 가능** | A2 (단일 D_s) |

**대안**:
- 반셀 GITT 로 4.53V 까지 D_s(SOC) 직접 측정 — [[260419_GITT_확산계수_추출]] 방식
- OCP 함수 재측정 (4.2V 가 아닌 4.53V 까지 확장)
- PyBaMM degradation 서브모델: LAM_pe rate constant 재튜닝
- CEI (Cathode Electrolyte Interphase) 성장 kinetic 별도 관리 (FEC, LiDFOB 등 첨가제 역할)

---

### 6.6.1 Si / SiC 복합 음극 물리 (PyBaMM 기본 DFN 이 안 담는 것)

> Gen5+ 개발 방향이 **Si 함량 증가**이므로, 현재 5% blend → 장기 ≥10% 예상. 가정 관리가 점점 중요해진다.
> 상세 문헌: [[Silicon]] — Jiang 2020, Shin 2021, Choi 2025, Wetjen 2025 등.

### 6.6.1 Si 가 유발하는 물리 (PyBaMM 기본 DFN 이 안 담는 것)

| Si 물리 | 수치 스케일 | PyBaMM 1D 에서 상태 |
|--------|----------|-----------------|
| 체적 팽창 | **최대 300%** (Li₁₅Si₄) | ❌ 기본 DFN 은 고정 porosity |
| 전압 히스테리시스 | **150~300 mV** (충/방전 비대칭) | ❌ OCP 를 soc 단조함수로 가정 |
| 전압 이완 | 수시간 ~ 수십시간 지속 | ❌ 화학-기계 응력 이완 모델 없음 |
| Li⁺ crosstalk (Si↔Gr) | 사이클마다 Li 재분배 | ❌ 단일 입자 가정 (Si+Gr blend 아님) |
| 상전이 (c-Si → a-LixSi → c-Li15Si4) | multi-step | ❌ Fickian diffusion 단순화 |
| Si 확산계수 | **10⁻¹⁴ ~ 10⁻¹⁶ m²/s** (Gr 보다 2~3 자리 낮음) | ⚠️ 단일 D_s 로 뭉뚱그림 |
| 급속 Si 손실 | 0-30% SOC / 40℃ 에서 **Si 80% 손실 vs Gr 10%** | ❌ LAM 단일 축으로 간주 |
| SiO-SEI crust (knee 현상) | RT 1C 장기에서 sudden decay | ❌ 일반 SEI 성장 모델과 다른 메커니즘 |

### 6.6.2 가정별 Si 특화 파탄 조건

#### 🔴 가정 A1 (합제밀도 → ε_AM) — Si 에서 치명적

**기본 A1 의 한계**:
$$\varepsilon_{AM} = \rho_{press} \cdot w_{AM} / \rho_{true,AM}$$

**Si 에서 깨지는 이유**:
1. **충전 상태별 부피 변화** — Fresh 와 1st full charge 의 ε_AM 이 300% 까지 차이. 고정값 입력 불가.
2. **Si 비율 vs Gr 비율** — Blend 음극은 ρ_true 가 단일값 아님 (Si 2.33 g/cc + Gr 2.26 g/cc)
3. **응력 기인 porosity 감소** — 팽창한 Si 가 공극을 메워 전해질 수송 차단

**파탄 지표**:
- Spec 1.5 `t max at 1st full charge` ÷ 1.4 `t max at shipping` > 1.08 (8% 이상 두께 증가 → Si 팽창 영향 크다는 신호)
- 초기 10 사이클 activation 구간이 Graphite 셀 대비 5cy→**5~10cy** 로 길어짐

**대안**:
- PyBaMM `particle mechanics` 옵션 (stress 모델) 활성화
- ε_AM 을 Fresh 값과 EOL 값 이원으로 입력 + 시점별 업데이트

#### 🔴 가정 A2 (D50 → 단일 r) — Si 에서 3중 파탄

**Si 에서 깨지는 이유**:
1. **Si + Gr bi-modal** — APG-031 (Gr) + EPF (Si) 는 구조적으로 완전히 다른 분포
2. **Si 입자 내 상전이** — c-Si(외곽) → a-LixSi(중간) → c-Li15Si4(코어) 로 **3개 상이 공존**. 단일 구형 확산 부적합
3. **Si 입자 표면 crack** — 사이클링 중 입자 파쇄 → 반경 분포 동적 변화

**파탄 지표**:
- rate capability 곡선이 단봉 모델로 피팅 안 됨
- dV/dQ 에서 Si 피크 (~0.45V) 와 Gr stage 피크가 독립적으로 이동

**대안**:
- **PyBaMM MPM** (Multi-Particle Model) — Si 와 Gr 을 각기 다른 입자 군으로
- 또는 blend OCP 모델 — Si 분율 자체를 피팅 파라미터로 (Schmitt 2022 접근)

#### 🔴 가정 A3 (비용량 → c_max) + 히스테리시스 추가 파탄

**Si 에서 깨지는 이유**:
1. **이론 용량 vs 실측 용량 격차 큼** — Si 이론 3579 mAh/g, 실측 1500~2500 mAh/g (crack, SEI 로 손실)
2. **전압 히스테리시스 150~300 mV** — OCP 함수가 **단조함수 가정**을 직접 깸. 충/방전에서 다른 OCP.
3. **전압 이완 수시간 지속** — 평형 c_eq 도달 자체가 느림 → "2nd reversible capacity" 측정값이 pulse 조건에 민감

**파탄 지표**:
- RPT OCV 시 충/방전 ΔV > 100 mV (Gr 단독은 ~10 mV)
- Rest 1h 후에도 voltage 가 계속 drift (평형 미도달)

**대안**:
- PyBaMM `open-circuit potential = "current sigmoid"` 또는 히스테리시스 서브모델
- OCV 측정 시 rest ≥ 4h + 충/방전 양방향 측정 → blended OCP 함수 구성

### 6.6.3 Si 5% blend 의 추가 가정 A9 (제안)

기존 A1~A8 에 Si 특화 가정을 추가할 것을 제안한다:

**가정 A9: Blend 음극 → 단일 유효 음극**
- **가정**: Si + Gr 을 단일 OCP + 단일 D_s + 단일 r 로 대표
- **유효 범위**: Si 비율 ≤ 5% + 초기 10 사이클 이내
- **파탄 조건**: Si 비율 >5%, 또는 사이클 >50, 또는 SOC 편중 운용 (0~30% 또는 70~100%)
- **파탄 지표**: dV/dQ 에 두 피크 (Gr stage + Si) 독립 이동, knee 조기 발현 (<300cy)
- **대안**: MPM + Si 독립 LAM 축 + 히스테리시스 서브모델 (Jiang 2020)

### 6.6.4 Gen5+ 실무 체크리스트 (Si 5% 한정)

```
□ Spec 1.5 (t at 1st full charge) 대비 1.4 (t at shipping) 비율 기록했는가?
□ Proto OQA 에서 초기 10 사이클 activation 구간 용량 변화 > Gr 셀 수준인가?
□ dV/dQ 에 Si 특성 피크 (~0.4V, ~0.2V) 분리 확인했는가?
□ 저온 (15℃ 이하) + 고율 (>1C) 충전 시 Li plating η 모니터링 중인가?
□ 전해액에 FEC 또는 VC 가 Si 에 맞는 농도 (보통 5~10%) 로 들어갔는가?
□ 시뮬 결과 수명 곡선이 knee 이전에 끝나는가? (Si knee ~200~400cy)
□ LLI, LAM_pe, LAM_ne 분리 추적 + LAM_ne 를 Si/Gr 로 또 분리했는가?
```

---

## 6.7 GITT 기반 diffusivity 직접 검증 — 가정 A2/A3 역검증 경로

> 가정 A2 (D50 → r) + A3 (비용량 → c_max) 는 **간접 변환**이다. 이를 **직접 측정**으로 검증하는 방법이 GITT.
> 상세 원리 · 수식 · 실무: [[260419_GITT_확산계수_추출]], [[GITT]].

### 6.7.1 Weppner-Huggins 공식 — A2/A3 의 실측 anchor

$$D_s = \frac{4}{9\pi}\left(r\cdot \frac{dE/dt}{dU/d\sqrt{t}}\right)^2$$

- **r**: 가정 A2 에서 D50/2 로 가정했던 입자 반경 — GITT D_s 계산에 직접 들어감
- **dE/dt**: 연속 pulse 간 OCV 변화율 — OCV 곡선 기울기
- **dU/d√t**: pulse 중 전압 sag 의 Sand 기울기 — 확산 동역학 실측
- **출력 D_s**: PyBaMM `Positive/Negative particle diffusivity [m²/s]` 입력

### 6.7.2 검증 체크

| 검증 항목 | 실측 (GITT) | PyBaMM 입력 | Δ 허용 |
|---------|-----------|-----------|-------|
| D_s (양극, 50% SOC) | 10⁻¹⁰ ~ 10⁻¹² (NMC 범위) | `Positive particle diffusivity` | ±1 order |
| D_s (음극 Gr, 50% SOC) | 10⁻¹¹ ~ 10⁻¹³ | `Negative particle diffusivity` | ±1 order |
| D_s (Si, 50% SOC) | 10⁻¹⁴ ~ 10⁻¹⁶ | (MPM 확장 시 별도 축) | 범위 확인 |
| D_s SOC-curve 형상 | 양끝 급락, 중간 flat | 함수형 D(c) | 곡선 형상 일치 |
| dV/dQ peak 위치 | Proto 측정 | PyBaMM OCP 함수 기반 | 피크 SOC ±2% |
| c_max (Q·ρ·3.6/F 추정) | OQA capacity + Half cell | `Maximum concentration` | stoichiometry window Δx < 0.03 |

### 6.7.3 BDT 데이터셋 활용 (이미 존재)

[[260419_GITT_확산계수_추출]] §5.2 기준 BDT 내 GITT 데이터셋 5종:

1. 240821 선행랩 Gen4pGr 422mAh GITT (풀셀 NMC + Gr, r_pos=5μm, r_neg=12μm)
2. 250905 M2-SDI open-ca-half (양극 반셀)
3. 250905 M2-SDI open-an-half (음극 반셀)
4. 251224 박민희 M1 ATL Cathode Half GITT 0.1C
5. 251224 박민희 M1 ATL Anode Half GITT 0.05C

→ **Gen5+ 와 동일/인접 프로젝트 GITT 가 이미 확보**. Category C 검증에 바로 활용 가능.

### 6.7.4 실패 모드 진단 (측정값이 이상할 때)

| 증상 | 원인 | 가정 |
|------|------|------|
| D_s > 10⁻⁸ m²/s | iR drop 미제거 또는 회귀 구간 오류 | 측정 데이터 처리 문제 |
| D_s < 10⁻¹⁸ m²/s | LFP 같은 2상 물질 or 측정 노이즈 | **A2 파탄** — Fickian 가정 부적합 |
| SOC 맵 랜덤 spike | pulse 경계 검출 오류 | 데이터 처리 |
| 양극/음극 D_s 반대 크기 | r 입력 오류 (5μm ↔ 12μm 혼동) | 단위/식별 오류 |
| Si 영역에서 비현실적 값 | Si 3상 공존, Fickian 무효 | **A2 + A9 파탄** — Si 전용 모델 필요 |

---

## 6.8 변환 문서화 원칙 (권장)

BDT 또는 개발 보고서에 설계변수 → PyBaMM 값을 싣는 모든 경우, **5요소 세트**를 명시:

1. **변환식** — 수식 자체
2. **내재 가정** — 어떤 물리를 버리는지 한 줄
3. **유효 범위** — 가정이 성립하는 C-rate·온도·화학계
4. **파탄 지표** — 가정이 깨졌음을 알 수 있는 실측 신호
5. **대안 경로** — 깨질 때 어떤 모델 확장·실측으로 보강할지

> 이 원칙이 지켜지면, 시뮬은 실측과 **함께 진화하는 도구** 가 된다. 지켜지지 않으면 시뮬은 "잘 맞을 때만 쓰는 장난감" 이 되어 의사결정에 위험하다.

---

# 7. 결론

## 7.1 Key Parameter 최종 도출 (Tier S + A, 14개)

```
[Tier S] 두 관점 공통 핵심 (8)
  1. Negative particle radius      r_n
  2. Negative particle diffusivity D_s,n
  3. Positive particle radius      r_p
  4. Positive particle diffusivity D_s,p
  5. Electrolyte diffusivity       D_e
  6. Electrolyte conductivity      κ_e
  7. Ambient temperature           T
  8. Negative electrode OCP        U_n(x,T)

[Tier A] 개발 주도 + Rate 강영향 (6)
  9.  Electrode thickness (pos/neg)
  10. Active material volume fraction (pos/neg)
  11. Max concentration in electrode (pos/neg)
  12. Initial electrolyte concentration
  13. Current function [A]
  14. Voltage cut-off (upper/lower)
```

## 7.2 두 관점의 연관성 요약

| 관찰 | 함의 |
|------|------|
| **음극 입자 반경**이 양 관점 모두 최상위 | R&D → 시뮬 → R&D 피드백 루프의 중심 knob. 한 번의 튜닝이 이론·실무 모두에 영향 |
| **합제밀도는 trade-off** (고상 전도↑ vs 전해질 수송↓) | 최적점 탐색이 시뮬 활용의 가장 직관적 성공 사례 |
| **첨가제는 gap** (실무는 중요, PyBaMM 직접 키 없음) | SEI/plating 파라미터 역피팅이 필수 보완 경로 (가정 A6) |
| **bi-modal 입자 분포**도 gap | MPM 확장으로 해결 (가정 A2) |
| **N/P ratio는 열역학적 방어**, rate 자체는 아님 | 안전 마진 계산용. rate 튜닝과 독립 (가정 A4) |
| **변환은 가정의 집합** | Tier S 파라미터도 A1~A8 가정 통과 후 숫자가 됨. 실측과 Δ 크면 가정부터 의심 |

## 7.3 다음 단계

1. Tier S/A 14개 파라미터로 **Design of Experiments (DOE) 시뮬레이션**
   - 목적: 셀 설계 변수 민감도 분석
   - 방법: Latin Hypercube sampling or Sobol indices
2. BDT 에 **Rate-step τ visualization** 탭 추가
3. **첨가제 프리셋 라이브러리** 구축 (SEI kinetic rate 측정값 기반)
4. **bi-modal 입자 확장** — PyBaMM MPM 연동 검토

---

## 🔗 관련 문서

- [[PyBaMM_Variables_PPT]] — 전체 파라미터 리스트
- **[[Cell_Design_Specification_필드]]** — 실제 Cell Design Spec 7대 분류 × 필드 스키마 + PyBaMM 커버리지 매트릭스 (Direct 27% / Indirect 32% / Out-of-scope 41%)
- [[합제밀도와_전류밀도]] — 전극 설계 공식
- [[충방전_매커니즘]] — Rate-determining 이론 + 주차타워 비유
- [[전해액]] — 첨가제 조합 DOE
- [[MX배터리그룹_평가항목]] — 개발 항목 전체
- [[Silicon]] — Si 음극 (체적 팽창, 입도 변화)
- [[PyBaMM_정리]] — PyBaMM 모델 개요
- [[GITT]] — diffusivity 측정 방법
