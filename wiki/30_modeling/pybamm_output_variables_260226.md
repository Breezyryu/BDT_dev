# PyBaMM 전기화학 시뮬레이션 출력 변수 전체 목록 (2026-02-26)

> **PyBaMM v25.12.2** 기준, `model.variables.keys()`로 추출한 전체 출력 변수 목록  
> 모델: **SPM** (514개) / **SPMe** (517개) / **DFN** (515개)

---

## 목차

1. [변수 수 요약](#1-변수-수-요약)
2. [모델 가용성 매트릭스](#2-모델-가용성-매트릭스)
3. [3모델 공통 변수 (510개) — 카테고리별](#3-3모델-공통-변수-510개--카테고리별)
   - [3.1 시간 / 기본 전기 출력](#31-시간--기본-전기-출력)
   - [3.2 전압 분해 (Overpotential / OCV)](#32-전압-분해-overpotential--ocv)
   - [3.3 양극 — 전극 물성 & 전기화학](#33-양극--전극-물성--전기화학)
   - [3.4 음극 — 전극 물성 & 전기화학](#34-음극--전극-물성--전기화학)
   - [3.5 입자 농도 & 화학양론비 (Particle)](#35-입자-농도--화학양론비-particle)
   - [3.6 전해질 (Electrolyte)](#36-전해질-electrolyte)
   - [3.7 분리막 (Separator)](#37-분리막-separator)
   - [3.8 열 (Thermal)](#38-열-thermal)
   - [3.9 열화 / 부반응 (Degradation)](#39-열화--부반응-degradation)
   - [3.10 리튬 인벤토리 / 총량](#310-리튬-인벤토리--총량)
   - [3.11 구조 / 좌표 / 기타](#311-구조--좌표--기타)
   - [3.12 X-averaged 음극 관련](#312-x-averaged-음극-관련)
   - [3.13 X-averaged 양극 관련](#313-x-averaged-양극-관련)
   - [3.14 X-averaged 전해질 / 분리막 / 발열 / 기타](#314-x-averaged-전해질--분리막--발열--기타)
   - [3.15 Volume-averaged 변수](#315-volume-averaged-변수)
4. [SPM 전용 변수 (SPMe/DFN에 없음)](#4-spm-전용-변수-spmedfn에-없음)
5. [SPMe 추가 변수 (SPM 대비 +3)](#5-spme-추가-변수-spm-대비-3)
6. [DFN 추가 변수 (SPM 대비 +5)](#6-dfn-추가-변수-spm-대비-5)
7. [모델별 누락 변수](#7-모델별-누락-변수)
8. [현재 코드에서 사용 중인 변수](#8-현재-코드에서-사용-중인-변수)

---

## 1. 변수 수 요약

| 모델 | 변수 수 | 설명 |
|------|---------|------|
| **SPM** (Single Particle Model) | **514** | 각 전극을 단일 입자로 근사, 전해질 농도 균일 가정 |
| **SPMe** (SPM with electrolyte) | **517** | SPM + 전해질 확산 방정식 (농도 구배 해석) |
| **DFN** (Doyle-Fuller-Newman) | **515** | Full pseudo-2D, 전극 내 전자 전도 명시적 해석 |

---

## 2. 모델 가용성 매트릭스

| 변수 그룹 | SPM | SPMe | DFN | 비고 |
|-----------|:---:|:----:|:---:|------|
| 공통 (510개) | ✅ | ✅ | ✅ | 3모델 동일 |
| `Electrolyte convection/diffusion/migration flux` | ❌ | ✅ | ✅ | SPMe/DFN 전해질 플럭스 분리 |
| `Negative/Positive electrolyte current density` | ✅ | ✅ | ❌ | DFN 미포함 |
| `X-averaged negative/positive particle flux` | ✅ | ✅ | ❌ | DFN 미포함 |
| `Negative/Positive electrode effective conductivity` | ❌ | ❌ | ✅ | DFN 전용 |

---

## 3. 3모델 공통 변수 (510개) — 카테고리별

### 3.1 시간 / 기본 전기 출력

| # | 변수 키 | 단위 | 설명 |
|---|---------|------|------|
| 1 | `Time [s]` | s | 시간 (초) |
| 2 | `Time [min]` | min | 시간 (분) |
| 3 | `Time [h]` | h | 시간 (시) |
| 4 | `Terminal voltage [V]` | V | 단자 전압 |
| 5 | `Voltage [V]` | V | 전압 |
| 6 | `Voltage expression [V]` | V | 전압 수식 표현 |
| 7 | `Battery voltage [V]` | V | 배터리 전압 |
| 8 | `Local voltage [V]` | V | 국소 전압 |
| 9 | `Current [A]` | A | 전류 |
| 10 | `Current variable [A]` | A | 전류 변수 |
| 11 | `C-rate` | - | C-rate |
| 12 | `Discharge capacity [A.h]` | Ah | 방전 용량 |
| 13 | `Discharge energy [W.h]` | Wh | 방전 에너지 |
| 14 | `Throughput capacity [A.h]` | Ah | 누적 처리 용량 |
| 15 | `Throughput energy [W.h]` | Wh | 누적 처리 에너지 |
| 16 | `Power [W]` | W | 출력 |
| 17 | `Terminal power [W]` | W | 단자 출력 |
| 18 | `Resistance [Ohm]` | Ω | 내부 저항 |
| 19 | `Local ECM resistance [Ohm]` | Ω | 국소 등가회로 저항 |
| 20 | `Current collector current density [A.m-2]` | A/m² | 집전체 전류밀도 |
| 21 | `Electrode current density [A.m-2]` | A/m² | 전극 전류밀도 |
| 22 | `Total current density [A.m-2]` | A/m² | 총 전류밀도 |

### 3.2 전압 분해 (Overpotential / OCV)

| # | 변수 키 | 단위 | 설명 |
|---|---------|------|------|
| 1 | `Battery open-circuit voltage [V]` | V | 배터리 개방회로 전압 |
| 2 | `Bulk open-circuit voltage [V]` | V | 벌크 OCV |
| 3 | `Surface open-circuit voltage [V]` | V | 표면 OCV |
| 4 | `Contact overpotential [V]` | V | 접촉 과전압 |
| 5 | `Particle concentration overpotential [V]` | V | 입자 농도 과전압 |
| 6 | `Battery particle concentration overpotential [V]` | V | 배터리 입자 농도 과전압 |
| 7 | `Battery negative particle concentration overpotential [V]` | V | 음극 입자 농도 과전압 |
| 8 | `Battery positive particle concentration overpotential [V]` | V | 양극 입자 농도 과전압 |
| 9 | `Battery negative electrode bulk open-circuit potential [V]` | V | 음극 벌크 OCP |
| 10 | `Battery positive electrode bulk open-circuit potential [V]` | V | 양극 벌크 OCP |
| 11 | `X-averaged concentration overpotential [V]` | V | X평균 농도 과전압 |
| 12 | `X-averaged electrolyte ohmic losses [V]` | V | X평균 전해질 옴 손실 |
| 13 | `X-averaged electrolyte overpotential [V]` | V | X평균 전해질 과전압 |
| 14 | `X-averaged reaction overpotential [V]` | V | X평균 반응 과전압 |
| 15 | `X-averaged solid phase ohmic losses [V]` | V | X평균 고체상 옴 손실 |
| 16 | `X-averaged SEI film overpotential [V]` | V | X평균 SEI 필름 과전압 |
| 17 | `X-averaged battery concentration overpotential [V]` | V | X평균 배터리 농도 과전압 |
| 18 | `X-averaged battery electrolyte ohmic losses [V]` | V | X평균 배터리 전해질 옴 손실 |
| 19 | `X-averaged battery reaction overpotential [V]` | V | X평균 배터리 반응 과전압 |
| 20 | `X-averaged battery solid phase ohmic losses [V]` | V | X평균 배터리 고체상 옴 손실 |
| 21 | `X-averaged battery negative reaction overpotential [V]` | V | X평균 배터리 음극 반응 과전압 |
| 22 | `X-averaged battery negative solid phase ohmic losses [V]` | V | X평균 배터리 음극 고체상 옴 손실 |
| 23 | `X-averaged battery positive reaction overpotential [V]` | V | X평균 배터리 양극 반응 과전압 |
| 24 | `X-averaged battery positive solid phase ohmic losses [V]` | V | X평균 배터리 양극 고체상 옴 손실 |

### 3.3 양극 — 전극 물성 & 전기화학

| # | 변수 키 | 단위 | 설명 |
|---|---------|------|------|
| 1 | `Positive electrode open-circuit potential [V]` | V | 양극 OCP |
| 2 | `Positive electrode equilibrium open-circuit potential [V]` | V | 양극 평형 OCP |
| 3 | `Positive electrode bulk open-circuit potential [V]` | V | 양극 벌크 OCP |
| 4 | `Positive electrode potential [V]` | V | 양극 전위 (φ_s) |
| 5 | `Positive electrode reaction overpotential [V]` | V | 양극 반응 과전압 |
| 6 | `Positive electrode ohmic losses [V]` | V | 양극 옴 손실 |
| 7 | `Positive electrode SEI film overpotential [V]` | V | 양극 SEI 필름 과전압 |
| 8 | `Positive electrode surface potential difference [V]` | V | 양극 표면 전위차 |
| 9 | `Positive electrode surface potential difference at separator interface [V]` | V | 양극-분리막 계면 전위차 |
| 10 | `Positive electrode exchange current density [A.m-2]` | A/m² | 양극 교환 전류밀도 |
| 11 | `Positive electrode interfacial current density [A.m-2]` | A/m² | 양극 계면 전류밀도 |
| 12 | `Positive electrode volumetric interfacial current density [A.m-3]` | A/m³ | 양극 체적 계면 전류밀도 |
| 13 | `Positive electrode current density [A.m-2]` | A/m² | 양극 전류밀도 |
| 14 | `Positive electrode SEI interfacial current density [A.m-2]` | A/m² | 양극 SEI 계면 전류밀도 |
| 15 | `Positive electrode SEI volumetric interfacial current density [A.m-3]` | A/m³ | 양극 SEI 체적 전류밀도 |
| 16 | `Positive electrode SEI on cracks interfacial current density [A.m-2]` | A/m² | 양극 SEI(크랙) 계면 전류밀도 |
| 17 | `Positive electrode SEI on cracks volumetric interfacial current density [A.m-3]` | A/m³ | 양극 SEI(크랙) 체적 전류밀도 |
| 18 | `Positive electrode lithium plating interfacial current density [A.m-2]` | A/m² | 양극 리튬 석출 계면 전류밀도 |
| 19 | `Positive electrode lithium plating volumetric interfacial current density [A.m-3]` | A/m³ | 양극 리튬 석출 체적 전류밀도 |
| 20 | `Positive electrode lithium plating reaction overpotential [V]` | V | 양극 리튬 석출 과전압 |
| 21 | `Positive electrode entropic change [V.K-1]` | V/K | 양극 엔트로피 변화 |
| 22 | `Positive electrode stoichiometry` | - | 양극 화학양론비 |
| 23 | `Positive electrode extent of lithiation` | - | 양극 리튬화 정도 |
| 24 | `Positive electrode capacity [A.h]` | Ah | 양극 용량 |
| 25 | `Positive electrode active material volume fraction` | - | 양극 활물질 체적분율 |
| 26 | `Positive electrode active material volume fraction change [s-1]` | 1/s | 양극 활물질 변화율 |
| 27 | `Positive electrode porosity` | - | 양극 공극률 |
| 28 | `Positive electrode porosity change [s-1]` | 1/s | 양극 공극률 변화율 |
| 29 | `Positive electrode porosity times concentration [mol.m-3]` | mol/m³ | 양극 (공극률 × 농도) |
| 30 | `Positive electrode surface area to volume ratio [m-1]` | 1/m | 양극 비표면적 |
| 31 | `Positive electrode interface utilisation` | - | 양극 계면 활용율 |
| 32 | `Positive electrode interface utilisation variable` | - | 양극 계면 활용율 변수 |
| 33 | `Positive electrode roughness ratio` | - | 양극 거칠기 비 |
| 34 | `Positive electrode transport efficiency` | - | 양극 수송 효율 |
| 35 | `Positive electrode temperature [K]` | K | 양극 온도 |
| 36 | `Positive electrode temperature [C]` | °C | 양극 온도 |
| 37 | `Positive electrode pressure [Pa]` | Pa | 양극 압력 |
| 38 | `Positive electrode volume-averaged concentration` | - | 양극 체적평균 농도 (무차원) |
| 39 | `Positive electrode volume-averaged concentration [mol.m-3]` | mol/m³ | 양극 체적평균 농도 |
| 40 | `Positive electrode volume-averaged acceleration [m.s-2]` | m/s² | 양극 체적평균 가속도 |
| 41 | `Positive electrode volume-averaged velocity [m.s-1]` | m/s | 양극 체적평균 속도 |
| 42 | `Positive electrolyte concentration [Molar]` | M | 양극 영역 전해질 농도 (몰) |
| 43 | `Positive electrolyte concentration [mol.m-3]` | mol/m³ | 양극 영역 전해질 농도 |
| 44 | `Positive electrolyte potential [V]` | V | 양극 영역 전해질 전위 |
| 45 | `Positive electrolyte transport efficiency` | - | 양극 전해질 수송 효율 |
| 46 | `Positive current collector potential [V]` | V | 양극 집전체 전위 |
| 47 | `Positive current collector temperature [K]` | K | 양극 집전체 온도 |
| 48 | `Positive current collector temperature [C]` | °C | 양극 집전체 온도 |
| 49 | `Positive current collector Ohmic heating [W.m-3]` | W/m³ | 양극 집전체 옴 발열 |

### 3.4 음극 — 전극 물성 & 전기화학

> 양극(3.3절)과 동일 구조. `"Positive"` → `"Negative"` 치환.

| # | 변수 키 | 단위 | 설명 |
|---|---------|------|------|
| 1 | `Negative electrode open-circuit potential [V]` | V | 음극 OCP |
| 2 | `Negative electrode equilibrium open-circuit potential [V]` | V | 음극 평형 OCP |
| 3 | `Negative electrode bulk open-circuit potential [V]` | V | 음극 벌크 OCP |
| 4 | `Negative electrode potential [V]` | V | 음극 전위 (φ_s) |
| 5 | `Negative electrode reaction overpotential [V]` | V | 음극 반응 과전압 |
| 6 | `Negative electrode ohmic losses [V]` | V | 음극 옴 손실 |
| 7 | `Negative electrode SEI film overpotential [V]` | V | 음극 SEI 필름 과전압 |
| 8 | `Negative electrode surface potential difference [V]` | V | 음극 표면 전위차 |
| 9 | `Negative electrode surface potential difference at separator interface [V]` | V | 음극-분리막 계면 전위차 |
| 10 | `Negative electrode exchange current density [A.m-2]` | A/m² | 음극 교환 전류밀도 |
| 11 | `Negative electrode interfacial current density [A.m-2]` | A/m² | 음극 계면 전류밀도 |
| 12 | `Negative electrode volumetric interfacial current density [A.m-3]` | A/m³ | 음극 체적 계면 전류밀도 |
| 13 | `Negative electrode current density [A.m-2]` | A/m² | 음극 전류밀도 |
| 14 | `Negative electrode SEI interfacial current density [A.m-2]` | A/m² | 음극 SEI 계면 전류밀도 |
| 15 | `Negative electrode SEI volumetric interfacial current density [A.m-3]` | A/m³ | 음극 SEI 체적 전류밀도 |
| 16 | `Negative electrode SEI on cracks interfacial current density [A.m-2]` | A/m² | 음극 SEI(크랙) 계면 전류밀도 |
| 17 | `Negative electrode SEI on cracks volumetric interfacial current density [A.m-3]` | A/m³ | 음극 SEI(크랙) 체적 전류밀도 |
| 18 | `Negative electrode lithium plating interfacial current density [A.m-2]` | A/m² | 음극 리튬 석출 계면 전류밀도 |
| 19 | `Negative electrode lithium plating volumetric interfacial current density [A.m-3]` | A/m³ | 음극 리튬 석출 체적 전류밀도 |
| 20 | `Negative electrode lithium plating reaction overpotential [V]` | V | 음극 리튬 석출 과전압 |
| 21 | `Negative electrode entropic change [V.K-1]` | V/K | 음극 엔트로피 변화 |
| 22 | `Negative electrode stoichiometry` | - | 음극 화학양론비 |
| 23 | `Negative electrode extent of lithiation` | - | 음극 리튬화 정도 |
| 24 | `Negative electrode capacity [A.h]` | Ah | 음극 용량 |
| 25 | `Negative electrode active material volume fraction` | - | 음극 활물질 체적분율 |
| 26 | `Negative electrode active material volume fraction change [s-1]` | 1/s | 음극 활물질 변화율 |
| 27 | `Negative electrode porosity` | - | 음극 공극률 |
| 28 | `Negative electrode porosity change [s-1]` | 1/s | 음극 공극률 변화율 |
| 29 | `Negative electrode porosity times concentration [mol.m-3]` | mol/m³ | 음극 (공극률 × 농도) |
| 30 | `Negative electrode surface area to volume ratio [m-1]` | 1/m | 음극 비표면적 |
| 31 | `Negative electrode interface utilisation` | - | 음극 계면 활용율 |
| 32 | `Negative electrode interface utilisation variable` | - | 음극 계면 활용율 변수 |
| 33 | `Negative electrode roughness ratio` | - | 음극 거칠기 비 |
| 34 | `Negative electrode transport efficiency` | - | 음극 수송 효율 |
| 35 | `Negative electrode temperature [K]` | K | 음극 온도 |
| 36 | `Negative electrode temperature [C]` | °C | 음극 온도 |
| 37 | `Negative electrode pressure [Pa]` | Pa | 음극 압력 |
| 38 | `Negative electrode volume-averaged concentration` | - | 음극 체적평균 농도 (무차원) |
| 39 | `Negative electrode volume-averaged concentration [mol.m-3]` | mol/m³ | 음극 체적평균 농도 |
| 40 | `Negative electrode volume-averaged acceleration [m.s-2]` | m/s² | 음극 체적평균 가속도 |
| 41 | `Negative electrode volume-averaged velocity [m.s-1]` | m/s | 음극 체적평균 속도 |
| 42 | `Negative electrolyte concentration [Molar]` | M | 음극 영역 전해질 농도 (몰) |
| 43 | `Negative electrolyte concentration [mol.m-3]` | mol/m³ | 음극 영역 전해질 농도 |
| 44 | `Negative electrolyte potential [V]` | V | 음극 영역 전해질 전위 |
| 45 | `Negative electrolyte transport efficiency` | - | 음극 전해질 수송 효율 |
| 46 | `Negative current collector potential [V]` | V | 음극 집전체 전위 |
| 47 | `Negative current collector temperature [K]` | K | 음극 집전체 온도 |
| 48 | `Negative current collector temperature [C]` | °C | 음극 집전체 온도 |
| 49 | `Negative current collector Ohmic heating [W.m-3]` | W/m³ | 음극 집전체 옴 발열 |

### 3.5 입자 농도 & 화학양론비 (Particle)

| # | 변수 키 | 단위 | 설명 |
|---|---------|------|------|
| 1 | `Positive particle concentration` | - | 양극 입자 내 Li 농도 (무차원) |
| 2 | `Positive particle concentration [mol.m-3]` | mol/m³ | 양극 입자 내 Li 농도 |
| 3 | `Positive particle surface concentration` | - | 양극 입자 표면 농도 (무차원) |
| 4 | `Positive particle surface concentration [mol.m-3]` | mol/m³ | 양극 입자 표면 농도 |
| 5 | `Positive particle stoichiometry` | - | 양극 입자 화학양론비 |
| 6 | `Positive particle surface stoichiometry` | - | 양극 입자 표면 화학양론비 |
| 7 | `Positive particle flux [mol.m-2.s-1]` | mol/m²·s | 양극 입자 Li 플럭스 |
| 8 | `Positive particle bc [mol.m-4]` | mol/m⁴ | 양극 입자 경계조건 |
| 9 | `Positive particle rhs [mol.m-3.s-1]` | mol/m³·s | 양극 입자 RHS |
| 10 | `Positive particle effective diffusivity [m2.s-1]` | m²/s | 양극 입자 유효 확산계수 |
| 11 | `Positive particle radius` | - | 양극 입자 반경 (무차원) |
| 12 | `Positive particle radius [m]` | m | 양극 입자 반경 |
| 13 | `Positive particle crack length [m]` | m | 양극 입자 크랙 길이 |
| 14 | `Positive particle cracking rate [m.s-1]` | m/s | 양극 입자 크랙 성장 속도 |
| 15 | `Positive particle concentration overpotential [V]` | V | 양극 입자 농도 과전압 |
| 16 | `Negative particle concentration` | - | 음극 입자 내 Li 농도 (무차원) |
| 17 | `Negative particle concentration [mol.m-3]` | mol/m³ | 음극 입자 내 Li 농도 |
| 18 | `Negative particle surface concentration` | - | 음극 입자 표면 농도 (무차원) |
| 19 | `Negative particle surface concentration [mol.m-3]` | mol/m³ | 음극 입자 표면 농도 |
| 20 | `Negative particle stoichiometry` | - | 음극 입자 화학양론비 |
| 21 | `Negative particle surface stoichiometry` | - | 음극 입자 표면 화학양론비 |
| 22 | `Negative particle flux [mol.m-2.s-1]` | mol/m²·s | 음극 입자 Li 플럭스 |
| 23 | `Negative particle bc [mol.m-4]` | mol/m⁴ | 음극 입자 경계조건 |
| 24 | `Negative particle rhs [mol.m-3.s-1]` | mol/m³·s | 음극 입자 RHS |
| 25 | `Negative particle effective diffusivity [m2.s-1]` | m²/s | 음극 입자 유효 확산계수 |
| 26 | `Negative particle radius` | - | 음극 입자 반경 (무차원) |
| 27 | `Negative particle radius [m]` | m | 음극 입자 반경 |
| 28 | `Negative particle crack length [m]` | m | 음극 입자 크랙 길이 |
| 29 | `Negative particle cracking rate [m.s-1]` | m/s | 음극 입자 크랙 성장 속도 |
| 30 | `Negative particle concentration overpotential [V]` | V | 음극 입자 농도 과전압 |

#### 평균 / 최대 / 최소 입자 농도

| # | 변수 키 | 단위 | 설명 |
|---|---------|------|------|
| 1 | `Average positive particle concentration` | - | 평균 양극 입자 농도 (무차원) |
| 2 | `Average positive particle concentration [mol.m-3]` | mol/m³ | 평균 양극 입자 농도 |
| 3 | `Average positive particle stoichiometry` | - | 평균 양극 화학양론비 |
| 4 | `Average negative particle concentration` | - | 평균 음극 입자 농도 (무차원) |
| 5 | `Average negative particle concentration [mol.m-3]` | mol/m³ | 평균 음극 입자 농도 |
| 6 | `Average negative particle stoichiometry` | - | 평균 음극 화학양론비 |
| 7 | `Maximum positive particle concentration` | - | 최대 양극 입자 농도 |
| 8 | `Maximum positive particle concentration [mol.m-3]` | mol/m³ | 최대 양극 입자 농도 |
| 9 | `Maximum positive particle stoichiometry` | - | 최대 양극 화학양론비 |
| 10 | `Maximum positive particle surface concentration` | - | 최대 양극 표면 농도 |
| 11 | `Maximum positive particle surface concentration [mol.m-3]` | mol/m³ | 최대 양극 표면 농도 |
| 12 | `Maximum positive particle surface stoichiometry` | - | 최대 양극 표면 화학양론비 |
| 13 | `Maximum negative particle concentration` | - | 최대 음극 입자 농도 |
| 14 | `Maximum negative particle concentration [mol.m-3]` | mol/m³ | 최대 음극 입자 농도 |
| 15 | `Maximum negative particle stoichiometry` | - | 최대 음극 화학양론비 |
| 16 | `Maximum negative particle surface concentration` | - | 최대 음극 표면 농도 |
| 17 | `Maximum negative particle surface concentration [mol.m-3]` | mol/m³ | 최대 음극 표면 농도 |
| 18 | `Maximum negative particle surface stoichiometry` | - | 최대 음극 표면 화학양론비 |
| 19 | `Minimum positive particle concentration` | - | 최소 양극 입자 농도 |
| 20 | `Minimum positive particle concentration [mol.m-3]` | mol/m³ | 최소 양극 입자 농도 |
| 21 | `Minimum positive particle stoichiometry` | - | 최소 양극 화학양론비 |
| 22 | `Minimum positive particle surface concentration` | - | 최소 양극 표면 농도 |
| 23 | `Minimum positive particle surface stoichiometry` | - | 최소 양극 표면 화학양론비 |
| 24 | `Minimum negative particle concentration` | - | 최소 음극 입자 농도 |
| 25 | `Minimum negative particle concentration [mol.m-3]` | mol/m³ | 최소 음극 입자 농도 |
| 26 | `Minimum negative particle stoichiometry` | - | 최소 음극 화학양론비 |
| 27 | `Minimum negative particle surface concentration` | - | 최소 음극 표면 농도 |
| 28 | `Minimum negative particle surface stoichiometry` | - | 최소 음극 표면 화학양론비 |

#### R-averaged 입자 농도

| # | 변수 키 | 단위 | 설명 |
|---|---------|------|------|
| 1 | `R-averaged positive particle concentration` | - | R평균 양극 입자 농도 |
| 2 | `R-averaged positive particle concentration [mol.m-3]` | mol/m³ | R평균 양극 입자 농도 |
| 3 | `R-averaged positive particle stoichiometry` | - | R평균 양극 화학양론비 |
| 4 | `R-averaged negative particle concentration` | - | R평균 음극 입자 농도 |
| 5 | `R-averaged negative particle concentration [mol.m-3]` | mol/m³ | R평균 음극 입자 농도 |
| 6 | `R-averaged negative particle stoichiometry` | - | R평균 음극 화학양론비 |

### 3.6 전해질 (Electrolyte)

| # | 변수 키 | 단위 | 설명 |
|---|---------|------|------|
| 1 | `Electrolyte concentration [mol.m-3]` | mol/m³ | 전해질 Li 이온 농도 |
| 2 | `Electrolyte concentration [Molar]` | M | 전해질 Li 이온 농도 (몰농도) |
| 3 | `Electrolyte concentration concatenation [mol.m-3]` | mol/m³ | 전해질 농도 연결 (전체 도메인) |
| 4 | `Electrolyte potential [V]` | V | 전해질 전위 (φ_e) |
| 5 | `Electrolyte current density [A.m-2]` | A/m² | 전해질 전류밀도 |
| 6 | `Electrolyte flux [mol.m-2.s-1]` | mol/m²·s | 전해질 플럭스 |
| 7 | `Electrolyte transport efficiency` | - | 전해질 수송 효율 |
| 8 | `Electrode transport efficiency` | - | 전극 수송 효율 |
| 9 | `Exchange current density [A.m-2]` | A/m² | 교환 전류밀도 (전체) |
| 10 | `Interfacial current density [A.m-2]` | A/m² | 계면 전류밀도 (전체) |
| 11 | `Gradient of electrolyte potential [V.m-1]` | V/m | 전해질 전위 구배 |
| 12 | `Gradient of negative electrode potential [V.m-1]` | V/m | 음극 전위 구배 |
| 13 | `Gradient of negative electrolyte potential [V.m-1]` | V/m | 음극 전해질 전위 구배 |
| 14 | `Gradient of positive electrode potential [V.m-1]` | V/m | 양극 전위 구배 |
| 15 | `Gradient of positive electrolyte potential [V.m-1]` | V/m | 양극 전해질 전위 구배 |
| 16 | `Gradient of separator electrolyte potential [V.m-1]` | V/m | 분리막 전해질 전위 구배 |

#### 체적 계면 전류밀도 합산

| # | 변수 키 | 단위 | 설명 |
|---|---------|------|------|
| 1 | `Sum of volumetric interfacial current densities [A.m-3]` | A/m³ | 체적 계면 전류밀도 합 (전체) |
| 2 | `Sum of electrolyte reaction source terms [A.m-3]` | A/m³ | 전해질 반응 소스항 합 |
| 3 | `Sum of negative electrode volumetric interfacial current densities [A.m-3]` | A/m³ | 음극 체적 계면 전류밀도 합 |
| 4 | `Sum of negative electrode electrolyte reaction source terms [A.m-3]` | A/m³ | 음극 전해질 반응 소스항 합 |
| 5 | `Sum of positive electrode volumetric interfacial current densities [A.m-3]` | A/m³ | 양극 체적 계면 전류밀도 합 |
| 6 | `Sum of positive electrode electrolyte reaction source terms [A.m-3]` | A/m³ | 양극 전해질 반응 소스항 합 |
| 7 | `Sum of x-averaged negative electrode volumetric interfacial current densities [A.m-3]` | A/m³ | X평균 음극 체적 전류밀도 합 |
| 8 | `Sum of x-averaged negative electrode electrolyte reaction source terms [A.m-3]` | A/m³ | X평균 음극 반응 소스항 합 |
| 9 | `Sum of x-averaged positive electrode volumetric interfacial current densities [A.m-3]` | A/m³ | X평균 양극 체적 전류밀도 합 |
| 10 | `Sum of x-averaged positive electrode electrolyte reaction source terms [A.m-3]` | A/m³ | X평균 양극 반응 소스항 합 |

### 3.7 분리막 (Separator)

| # | 변수 키 | 단위 | 설명 |
|---|---------|------|------|
| 1 | `Separator porosity` | - | 분리막 공극률 |
| 2 | `Separator porosity change [s-1]` | 1/s | 분리막 공극률 변화율 |
| 3 | `Separator porosity times concentration [mol.m-3]` | mol/m³ | 분리막 (공극률 × 농도) |
| 4 | `Separator electrolyte concentration [mol.m-3]` | mol/m³ | 분리막 전해질 농도 |
| 5 | `Separator electrolyte concentration [Molar]` | M | 분리막 전해질 농도 (몰) |
| 6 | `Separator electrolyte potential [V]` | V | 분리막 전해질 전위 |
| 7 | `Separator electrolyte transport efficiency` | - | 분리막 전해질 수송 효율 |
| 8 | `Separator electrode transport efficiency` | - | 분리막 전극 수송 효율 |
| 9 | `Separator temperature [K]` | K | 분리막 온도 |
| 10 | `Separator temperature [C]` | °C | 분리막 온도 |
| 11 | `Separator pressure [Pa]` | Pa | 분리막 압력 |
| 12 | `Separator volume-averaged acceleration [m.s-2]` | m/s² | 분리막 체적평균 가속도 |
| 13 | `Separator volume-averaged velocity [m.s-1]` | m/s | 분리막 체적평균 속도 |

### 3.8 열 (Thermal)

| # | 변수 키 | 단위 | 설명 |
|---|---------|------|------|
| 1 | `Ambient temperature [K]` | K | 환경 온도 |
| 2 | `Ambient temperature [C]` | °C | 환경 온도 |
| 3 | `Cell temperature [K]` | K | 셀 온도 |
| 4 | `Cell temperature [C]` | °C | 셀 온도 |
| 5 | `Surface temperature [K]` | K | 표면 온도 |
| 6 | `Total heating [W.m-3]` | W/m³ | 총 발열 (체적밀도) |
| 7 | `Total heating [W]` | W | 총 발열 |
| 8 | `Total heating per unit electrode-pair area [W.m-2]` | W/m² | 총 발열 (전극면적당) |
| 9 | `Ohmic heating [W.m-3]` | W/m³ | 옴 발열 (체적밀도) |
| 10 | `Ohmic heating [W]` | W | 옴 발열 |
| 11 | `Ohmic heating per unit electrode-pair area [W.m-2]` | W/m² | 옴 발열 (전극면적당) |
| 12 | `Irreversible electrochemical heating [W.m-3]` | W/m³ | 비가역 전기화학 발열 |
| 13 | `Irreversible electrochemical heating [W]` | W | 비가역 전기화학 발열 |
| 14 | `Irreversible electrochemical heating per unit electrode-pair area [W.m-2]` | W/m² | 비가역 발열 (면적당) |
| 15 | `Reversible heating [W.m-3]` | W/m³ | 가역 발열 (엔트로피) |
| 16 | `Reversible heating [W]` | W | 가역 발열 |
| 17 | `Reversible heating per unit electrode-pair area [W.m-2]` | W/m² | 가역 발열 (면적당) |
| 18 | `Environment total cooling [W]` | W | 환경 냉각량 |
| 19 | `Surface total cooling [W.m-3]` | W/m³ | 표면 냉각 (체적밀도) |
| 20 | `Surface total cooling [W]` | W | 표면 냉각 |

### 3.9 열화 / 부반응 (Degradation)

#### SEI 관련

| # | 변수 키 | 단위 | 설명 |
|---|---------|------|------|
| 1 | `Positive SEI thickness [m]` | m | 양극 SEI 두께 |
| 2 | `Positive SEI concentration [mol.m-3]` | mol/m³ | 양극 SEI 농도 |
| 3 | `Positive SEI on cracks thickness [m]` | m | 양극 크랙 SEI 두께 |
| 4 | `Positive SEI on cracks concentration [mol.m-3]` | mol/m³ | 양극 크랙 SEI 농도 |
| 5 | `Negative SEI thickness [m]` | m | 음극 SEI 두께 |
| 6 | `Negative SEI concentration [mol.m-3]` | mol/m³ | 음극 SEI 농도 |
| 7 | `Negative SEI on cracks thickness [m]` | m | 음극 크랙 SEI 두께 |
| 8 | `Negative SEI on cracks concentration [mol.m-3]` | mol/m³ | 음극 크랙 SEI 농도 |

#### 리튬 석출 (Lithium Plating)

| # | 변수 키 | 단위 | 설명 |
|---|---------|------|------|
| 1 | `Positive lithium plating thickness [m]` | m | 양극 리튬 석출 두께 |
| 2 | `Positive lithium plating concentration [mol.m-3]` | mol/m³ | 양극 리튬 석출 농도 |
| 3 | `Negative lithium plating thickness [m]` | m | 음극 리튬 석출 두께 |
| 4 | `Negative lithium plating concentration [mol.m-3]` | mol/m³ | 음극 리튬 석출 농도 |
| 5 | `Positive dead lithium thickness [m]` | m | 양극 데드 리튬 두께 |
| 6 | `Positive dead lithium concentration [mol.m-3]` | mol/m³ | 양극 데드 리튬 농도 |
| 7 | `Negative dead lithium thickness [m]` | m | 음극 데드 리튬 두께 |
| 8 | `Negative dead lithium concentration [mol.m-3]` | mol/m³ | 음극 데드 리튬 농도 |
| 9 | `Positive crack surface to volume ratio [m-1]` | 1/m | 양극 크랙 비표면적 |
| 10 | `Negative crack surface to volume ratio [m-1]` | 1/m | 음극 크랙 비표면적 |

#### 열화 지표 (%)

| # | 변수 키 | 단위 | 설명 |
|---|---------|------|------|
| 1 | `LLI [%]` | % | 리튬 인벤토리 손실 |
| 2 | `LAM_pe [%]` | % | 양극 활물질 손실 |
| 3 | `LAM_ne [%]` | % | 음극 활물질 손실 |
| 4 | `Loss of lithium inventory [%]` | % | 리튬 인벤토리 손실 (상세) |
| 5 | `Loss of lithium inventory, including electrolyte [%]` | % | 전해질 포함 LLI |
| 6 | `Loss of active material in positive electrode [%]` | % | 양극 활물질 손실 (상세) |
| 7 | `Loss of active material in negative electrode [%]` | % | 음극 활물질 손실 (상세) |

#### 부반응 용량 / 리튬 손실

| # | 변수 키 | 단위 | 설명 |
|---|---------|------|------|
| 1 | `Total capacity lost to side reactions [A.h]` | Ah | 부반응 전체 용량 손실 |
| 2 | `Loss of capacity to negative SEI [A.h]` | Ah | 음극 SEI 용량 손실 |
| 3 | `Loss of capacity to negative SEI on cracks [A.h]` | Ah | 음극 크랙 SEI 용량 손실 |
| 4 | `Loss of capacity to negative lithium plating [A.h]` | Ah | 음극 석출 용량 손실 |
| 5 | `Loss of capacity to positive SEI [A.h]` | Ah | 양극 SEI 용량 손실 |
| 6 | `Loss of capacity to positive SEI on cracks [A.h]` | Ah | 양극 크랙 SEI 용량 손실 |
| 7 | `Loss of capacity to positive lithium plating [A.h]` | Ah | 양극 석출 용량 손실 |
| 8 | `Loss of lithium to negative SEI [mol]` | mol | 음극 SEI 리튬 손실 |
| 9 | `Loss of lithium to negative SEI on cracks [mol]` | mol | 음극 크랙 SEI 리튬 손실 |
| 10 | `Loss of lithium to negative lithium plating [mol]` | mol | 음극 석출 리튬 손실 |
| 11 | `Loss of lithium to positive SEI [mol]` | mol | 양극 SEI 리튬 손실 |
| 12 | `Loss of lithium to positive SEI on cracks [mol]` | mol | 양극 크랙 SEI 리튬 손실 |
| 13 | `Loss of lithium to positive lithium plating [mol]` | mol | 양극 석출 리튬 손실 |
| 14 | `Loss of lithium due to loss of active material in negative electrode [mol]` | mol | 음극 활물질 손실에 의한 리튬 손실 |
| 15 | `Loss of lithium due to loss of active material in positive electrode [mol]` | mol | 양극 활물질 손실에 의한 리튬 손실 |

### 3.10 리튬 인벤토리 / 총량

| # | 변수 키 | 단위 | 설명 |
|---|---------|------|------|
| 1 | `Total lithium [mol]` | mol | 총 리튬량 |
| 2 | `Total lithium capacity [A.h]` | Ah | 총 리튬 용량 |
| 3 | `Total lithium capacity in particles [A.h]` | Ah | 입자 내 리튬 용량 |
| 4 | `Total lithium in particles [mol]` | mol | 입자 내 총 리튬 |
| 5 | `Total lithium in electrolyte [mol]` | mol | 전해질 내 리튬 |
| 6 | `Total lithium in positive electrode [mol]` | mol | 양극 내 리튬 |
| 7 | `Total lithium in negative electrode [mol]` | mol | 음극 내 리튬 |
| 8 | `Total lithium in primary phase in positive electrode [mol]` | mol | 양극 1차상 리튬 |
| 9 | `Total lithium in primary phase in negative electrode [mol]` | mol | 음극 1차상 리튬 |
| 10 | `Total lithium lost [mol]` | mol | 총 손실 리튬 |
| 11 | `Total lithium lost from particles [mol]` | mol | 입자 유래 리튬 손실 |
| 12 | `Total lithium lost from electrolyte [mol]` | mol | 전해질 유래 리튬 손실 |
| 13 | `Total lithium lost to side reactions [mol]` | mol | 부반응 리튬 손실 |

### 3.11 구조 / 좌표 / 기타

| # | 변수 키 | 단위 | 설명 |
|---|---------|------|------|
| 1 | `x [m]` | m | 셀 두께 방향 좌표 (전체) |
| 2 | `x_n [m]` | m | 음극 영역 좌표 |
| 3 | `x_p [m]` | m | 양극 영역 좌표 |
| 4 | `x_s [m]` | m | 분리막 영역 좌표 |
| 5 | `r_n [m]` | m | 음극 입자 반경 좌표 |
| 6 | `r_p [m]` | m | 양극 입자 반경 좌표 |
| 7 | `Porosity` | - | 전체 공극률 분포 |
| 8 | `Porosity change` | - | 공극률 변화 |
| 9 | `Porosity times concentration [mol.m-3]` | mol/m³ | 공극률 × 농도 |
| 10 | `Pressure [Pa]` | Pa | 압력 분포 |
| 11 | `Transverse volume-averaged acceleration [m.s-2]` | m/s² | 횡방향 체적평균 가속도 |
| 12 | `Transverse volume-averaged velocity [m.s-1]` | m/s | 횡방향 체적평균 속도 |
| 13 | `negative electrode transverse volume-averaged acceleration [m.s-2]` | m/s² | 음극 횡방향 가속도 |
| 14 | `negative electrode transverse volume-averaged velocity [m.s-1]` | m/s | 음극 횡방향 속도 |
| 15 | `positive electrode transverse volume-averaged acceleration [m.s-2]` | m/s² | 양극 횡방향 가속도 |
| 16 | `positive electrode transverse volume-averaged velocity [m.s-1]` | m/s | 양극 횡방향 속도 |
| 17 | `separator transverse volume-averaged acceleration [m.s-2]` | m/s² | 분리막 횡방향 가속도 |
| 18 | `separator transverse volume-averaged velocity [m.s-1]` | m/s | 분리막 횡방향 속도 |

### 3.12 X-averaged 음극 관련

| # | 변수 키 | 단위 | 설명 |
|---|---------|------|------|
| 1 | `X-averaged negative electrode open-circuit potential [V]` | V | X평균 음극 OCP |
| 2 | `X-averaged negative electrode equilibrium open-circuit potential [V]` | V | X평균 음극 평형 OCP |
| 3 | `X-averaged negative electrode potential [V]` | V | X평균 음극 전위 |
| 4 | `X-averaged negative electrode reaction overpotential [V]` | V | X평균 음극 반응 과전압 |
| 5 | `X-averaged negative electrode ohmic losses [V]` | V | X평균 음극 옴 손실 |
| 6 | `X-averaged negative electrode surface potential difference [V]` | V | X평균 음극 표면 전위차 |
| 7 | `X-averaged negative electrode resistance [Ohm.m2]` | Ω·m² | X평균 음극 저항 |
| 8 | `X-averaged negative electrode SEI film overpotential [V]` | V | X평균 음극 SEI 과전압 |
| 9 | `X-averaged negative electrode exchange current density [A.m-2]` | A/m² | X평균 음극 교환 전류밀도 |
| 10 | `X-averaged negative electrode interfacial current density [A.m-2]` | A/m² | X평균 음극 계면 전류밀도 |
| 11 | `X-averaged negative electrode volumetric interfacial current density [A.m-3]` | A/m³ | X평균 음극 체적 전류밀도 |
| 12 | `X-averaged negative electrode total interfacial current density [A.m-2]` | A/m² | X평균 음극 총 계면 전류밀도 |
| 13 | `X-averaged negative electrode total volumetric interfacial current density [A.m-3]` | A/m³ | X평균 음극 총 체적 전류밀도 |
| 14 | `X-averaged negative electrode SEI interfacial current density [A.m-2]` | A/m² | X평균 음극 SEI 전류밀도 |
| 15 | `X-averaged negative electrode SEI volumetric interfacial current density [A.m-3]` | A/m³ | X평균 음극 SEI 체적 전류밀도 |
| 16 | `X-averaged negative electrode SEI on cracks interfacial current density [A.m-2]` | A/m² | X평균 음극 크랙 SEI 전류밀도 |
| 17 | `X-averaged negative electrode SEI on cracks volumetric interfacial current density [A.m-3]` | A/m³ | X평균 음극 크랙 SEI 체적 전류밀도 |
| 18 | `X-averaged negative electrode lithium plating interfacial current density [A.m-2]` | A/m² | X평균 음극 석출 전류밀도 |
| 19 | `X-averaged negative electrode lithium plating volumetric interfacial current density [A.m-3]` | A/m³ | X평균 음극 석출 체적 전류밀도 |
| 20 | `X-averaged negative electrode lithium plating reaction overpotential [V]` | V | X평균 음극 석출 과전압 |
| 21 | `X-averaged negative electrode entropic change [V.K-1]` | V/K | X평균 음극 엔트로피 변화 |
| 22 | `X-averaged negative electrode extent of lithiation` | - | X평균 음극 리튬화 정도 |
| 23 | `X-averaged negative electrode active material volume fraction` | - | X평균 음극 활물질 분율 |
| 24 | `X-averaged negative electrode active material volume fraction change [s-1]` | 1/s | X평균 음극 활물질 변화율 |
| 25 | `X-averaged negative electrode porosity` | - | X평균 음극 공극률 |
| 26 | `X-averaged negative electrode porosity change [s-1]` | 1/s | X평균 음극 공극률 변화율 |
| 27 | `X-averaged negative electrode surface area to volume ratio [m-1]` | 1/m | X평균 음극 비표면적 |
| 28 | `X-averaged negative electrode interface utilisation` | - | X평균 음극 계면 활용율 |
| 29 | `X-averaged negative electrode interface utilisation variable` | - | X평균 음극 계면 활용율 변수 |
| 30 | `X-averaged negative electrode roughness ratio` | - | X평균 음극 거칠기 비 |
| 31 | `X-averaged negative electrode transport efficiency` | - | X평균 음극 수송 효율 |
| 32 | `X-averaged negative electrode temperature [K]` | K | X평균 음극 온도 |
| 33 | `X-averaged negative electrode temperature [C]` | °C | X평균 음극 온도 |
| 34 | `X-averaged negative electrode pressure [Pa]` | Pa | X평균 음극 압력 |
| 35 | `X-averaged negative electrode volume-averaged acceleration [m.s-2]` | m/s² | X평균 음극 가속도 |
| 36 | `X-averaged negative electrode transverse volume-averaged acceleration [m.s-2]` | m/s² | X평균 음극 횡방향 가속도 |
| 37 | `X-averaged negative electrode transverse volume-averaged velocity [m.s-1]` | m/s | X평균 음극 횡방향 속도 |
| 38 | `X-averaged negative particle concentration` | - | X평균 음극 입자 농도 (무차원) |
| 39 | `X-averaged negative particle concentration [mol.m-3]` | mol/m³ | X평균 음극 입자 농도 |
| 40 | `X-averaged negative particle surface concentration` | - | X평균 음극 표면 농도 (무차원) |
| 41 | `X-averaged negative particle surface concentration [mol.m-3]` | mol/m³ | X평균 음극 표면 농도 |
| 42 | `X-averaged negative particle stoichiometry` | - | X평균 음극 화학양론비 |
| 43 | `X-averaged negative particle surface stoichiometry` | - | X평균 음극 표면 화학양론비 |
| 44 | `X-averaged negative particle effective diffusivity [m2.s-1]` | m²/s | X평균 음극 유효 확산계수 |
| 45 | `X-averaged negative particle radius [m]` | m | X평균 음극 입자 반경 |
| 46 | `X-averaged negative particle crack length [m]` | m | X평균 음극 크랙 길이 |
| 47 | `X-averaged negative particle cracking rate [m.s-1]` | m/s | X평균 음극 크랙 성장 속도 |
| 48 | `X-averaged negative SEI thickness [m]` | m | X평균 음극 SEI 두께 |
| 49 | `X-averaged negative SEI concentration [mol.m-3]` | mol/m³ | X평균 음극 SEI 농도 |
| 50 | `X-averaged negative SEI on cracks thickness [m]` | m | X평균 음극 크랙 SEI 두께 |
| 51 | `X-averaged negative SEI on cracks concentration [mol.m-3]` | mol/m³ | X평균 음극 크랙 SEI 농도 |
| 52 | `X-averaged negative lithium plating thickness [m]` | m | X평균 음극 석출 두께 |
| 53 | `X-averaged negative lithium plating concentration [mol.m-3]` | mol/m³ | X평균 음극 석출 농도 |
| 54 | `X-averaged negative dead lithium thickness [m]` | m | X평균 음극 데드 리튬 두께 |
| 55 | `X-averaged negative dead lithium concentration [mol.m-3]` | mol/m³ | X평균 음극 데드 리튬 농도 |
| 56 | `X-averaged negative electrolyte concentration [mol.m-3]` | mol/m³ | X평균 음극 전해질 농도 |
| 57 | `X-averaged negative electrolyte concentration [Molar]` | M | X평균 음극 전해질 농도 (몰) |
| 58 | `X-averaged negative electrolyte potential [V]` | V | X평균 음극 전해질 전위 |
| 59 | `X-averaged negative electrolyte transport efficiency` | - | X평균 음극 전해질 수송 효율 |

### 3.13 X-averaged 양극 관련

> 3.12절과 동일 구조. `"negative"` → `"positive"` 치환. (총 59개)

| # | 변수 키 | 단위 | 설명 |
|---|---------|------|------|
| 1 | `X-averaged positive electrode open-circuit potential [V]` | V | X평균 양극 OCP |
| 2 | `X-averaged positive electrode equilibrium open-circuit potential [V]` | V | X평균 양극 평형 OCP |
| 3 | `X-averaged positive electrode potential [V]` | V | X평균 양극 전위 |
| 4 | `X-averaged positive electrode reaction overpotential [V]` | V | X평균 양극 반응 과전압 |
| 5 | `X-averaged positive electrode ohmic losses [V]` | V | X평균 양극 옴 손실 |
| 6 | `X-averaged positive electrode surface potential difference [V]` | V | X평균 양극 표면 전위차 |
| 7 | `X-averaged positive electrode resistance [Ohm.m2]` | Ω·m² | X평균 양극 저항 |
| 8 | `X-averaged positive electrode SEI film overpotential [V]` | V | X평균 양극 SEI 과전압 |
| 9 | `X-averaged positive electrode exchange current density [A.m-2]` | A/m² | X평균 양극 교환 전류밀도 |
| 10 | `X-averaged positive electrode interfacial current density [A.m-2]` | A/m² | X평균 양극 계면 전류밀도 |
| 11 | `X-averaged positive electrode volumetric interfacial current density [A.m-3]` | A/m³ | X평균 양극 체적 전류밀도 |
| 12 | `X-averaged positive electrode total interfacial current density [A.m-2]` | A/m² | X평균 양극 총 계면 전류밀도 |
| 13 | `X-averaged positive electrode total volumetric interfacial current density [A.m-3]` | A/m³ | X평균 양극 총 체적 전류밀도 |
| 14 | `X-averaged positive electrode SEI interfacial current density [A.m-2]` | A/m² | X평균 양극 SEI 전류밀도 |
| 15 | `X-averaged positive electrode SEI volumetric interfacial current density [A.m-3]` | A/m³ | X평균 양극 SEI 체적 전류밀도 |
| 16 | `X-averaged positive electrode SEI on cracks interfacial current density [A.m-2]` | A/m² | X평균 양극 크랙 SEI 전류밀도 |
| 17 | `X-averaged positive electrode SEI on cracks volumetric interfacial current density [A.m-3]` | A/m³ | X평균 양극 크랙 SEI 체적 전류밀도 |
| 18 | `X-averaged positive electrode lithium plating interfacial current density [A.m-2]` | A/m² | X평균 양극 석출 전류밀도 |
| 19 | `X-averaged positive electrode lithium plating volumetric interfacial current density [A.m-3]` | A/m³ | X평균 양극 석출 체적 전류밀도 |
| 20 | `X-averaged positive electrode lithium plating reaction overpotential [V]` | V | X평균 양극 석출 과전압 |
| 21 | `X-averaged positive electrode entropic change [V.K-1]` | V/K | X평균 양극 엔트로피 변화 |
| 22 | `X-averaged positive electrode extent of lithiation` | - | X평균 양극 리튬화 정도 |
| 23 | `X-averaged positive electrode active material volume fraction` | - | X평균 양극 활물질 분율 |
| 24 | `X-averaged positive electrode active material volume fraction change [s-1]` | 1/s | X평균 양극 활물질 변화율 |
| 25 | `X-averaged positive electrode porosity` | - | X평균 양극 공극률 |
| 26 | `X-averaged positive electrode porosity change [s-1]` | 1/s | X평균 양극 공극률 변화율 |
| 27 | `X-averaged positive electrode surface area to volume ratio [m-1]` | 1/m | X평균 양극 비표면적 |
| 28 | `X-averaged positive electrode interface utilisation` | - | X평균 양극 계면 활용율 |
| 29 | `X-averaged positive electrode interface utilisation variable` | - | X평균 양극 계면 활용율 변수 |
| 30 | `X-averaged positive electrode roughness ratio` | - | X평균 양극 거칠기 비 |
| 31 | `X-averaged positive electrode transport efficiency` | - | X평균 양극 수송 효율 |
| 32 | `X-averaged positive electrode temperature [K]` | K | X평균 양극 온도 |
| 33 | `X-averaged positive electrode temperature [C]` | °C | X평균 양극 온도 |
| 34 | `X-averaged positive electrode pressure [Pa]` | Pa | X평균 양극 압력 |
| 35 | `X-averaged positive electrode volume-averaged acceleration [m.s-2]` | m/s² | X평균 양극 가속도 |
| 36 | `X-averaged positive electrode transverse volume-averaged acceleration [m.s-2]` | m/s² | X평균 양극 횡방향 가속도 |
| 37 | `X-averaged positive electrode transverse volume-averaged velocity [m.s-1]` | m/s | X평균 양극 횡방향 속도 |
| 38 | `X-averaged positive particle concentration` | - | X평균 양극 입자 농도 (무차원) |
| 39 | `X-averaged positive particle concentration [mol.m-3]` | mol/m³ | X평균 양극 입자 농도 |
| 40 | `X-averaged positive particle surface concentration` | - | X평균 양극 표면 농도 (무차원) |
| 41 | `X-averaged positive particle surface concentration [mol.m-3]` | mol/m³ | X평균 양극 표면 농도 |
| 42 | `X-averaged positive particle stoichiometry` | - | X평균 양극 화학양론비 |
| 43 | `X-averaged positive particle surface stoichiometry` | - | X평균 양극 표면 화학양론비 |
| 44 | `X-averaged positive particle effective diffusivity [m2.s-1]` | m²/s | X평균 양극 유효 확산계수 |
| 45 | `X-averaged positive particle radius [m]` | m | X평균 양극 입자 반경 |
| 46 | `X-averaged positive particle crack length [m]` | m | X평균 양극 크랙 길이 |
| 47 | `X-averaged positive particle cracking rate [m.s-1]` | m/s | X평균 양극 크랙 성장 속도 |
| 48 | `X-averaged positive SEI thickness [m]` | m | X평균 양극 SEI 두께 |
| 49 | `X-averaged positive SEI concentration [mol.m-3]` | mol/m³ | X평균 양극 SEI 농도 |
| 50 | `X-averaged positive SEI on cracks thickness [m]` | m | X평균 양극 크랙 SEI 두께 |
| 51 | `X-averaged positive SEI on cracks concentration [mol.m-3]` | mol/m³ | X평균 양극 크랙 SEI 농도 |
| 52 | `X-averaged positive lithium plating thickness [m]` | m | X평균 양극 석출 두께 |
| 53 | `X-averaged positive lithium plating concentration [mol.m-3]` | mol/m³ | X평균 양극 석출 농도 |
| 54 | `X-averaged positive dead lithium thickness [m]` | m | X평균 양극 데드 리튬 두께 |
| 55 | `X-averaged positive dead lithium concentration [mol.m-3]` | mol/m³ | X평균 양극 데드 리튬 농도 |
| 56 | `X-averaged positive electrolyte concentration [mol.m-3]` | mol/m³ | X평균 양극 전해질 농도 |
| 57 | `X-averaged positive electrolyte concentration [Molar]` | M | X평균 양극 전해질 농도 (몰) |
| 58 | `X-averaged positive electrolyte potential [V]` | V | X평균 양극 전해질 전위 |
| 59 | `X-averaged positive electrolyte transport efficiency` | - | X평균 양극 전해질 수송 효율 |

### 3.14 X-averaged 전해질 / 분리막 / 발열 / 기타

| # | 변수 키 | 단위 | 설명 |
|---|---------|------|------|
| 1 | `X-averaged electrolyte concentration [mol.m-3]` | mol/m³ | X평균 전해질 농도 |
| 2 | `X-averaged electrolyte concentration [Molar]` | M | X평균 전해질 농도 (몰) |
| 3 | `X-averaged electrolyte potential [V]` | V | X평균 전해질 전위 |
| 4 | `X-averaged cell temperature [K]` | K | X평균 셀 온도 |
| 5 | `X-averaged cell temperature [C]` | °C | X평균 셀 온도 |
| 6 | `X-averaged total heating [W.m-3]` | W/m³ | X평균 총 발열 |
| 7 | `X-averaged Ohmic heating [W.m-3]` | W/m³ | X평균 옴 발열 |
| 8 | `X-averaged irreversible electrochemical heating [W.m-3]` | W/m³ | X평균 비가역 발열 |
| 9 | `X-averaged reversible heating [W.m-3]` | W/m³ | X평균 가역 발열 |
| 10 | `X-averaged separator electrolyte concentration [mol.m-3]` | mol/m³ | X평균 분리막 전해질 농도 |
| 11 | `X-averaged separator electrolyte concentration [Molar]` | M | X평균 분리막 전해질 농도 (몰) |
| 12 | `X-averaged separator electrolyte potential [V]` | V | X평균 분리막 전해질 전위 |
| 13 | `X-averaged separator electrolyte transport efficiency` | - | X평균 분리막 전해질 수송 효율 |
| 14 | `X-averaged separator electrode transport efficiency` | - | X평균 분리막 전극 수송 효율 |
| 15 | `X-averaged separator porosity` | - | X평균 분리막 공극률 |
| 16 | `X-averaged separator porosity change [s-1]` | 1/s | X평균 분리막 공극률 변화율 |
| 17 | `X-averaged separator temperature [K]` | K | X평균 분리막 온도 |
| 18 | `X-averaged separator temperature [C]` | °C | X평균 분리막 온도 |
| 19 | `X-averaged separator pressure [Pa]` | Pa | X평균 분리막 압력 |
| 20 | `X-averaged separator volume-averaged acceleration [m.s-2]` | m/s² | X평균 분리막 가속도 |
| 21 | `X-averaged separator transverse volume-averaged acceleration [m.s-2]` | m/s² | X평균 분리막 횡방향 가속도 |
| 22 | `X-averaged separator transverse volume-averaged velocity [m.s-1]` | m/s | X평균 분리막 횡방향 속도 |
| 23 | `X-averaged volume-averaged acceleration [m.s-1]` | m/s | X평균 체적평균 가속도 |

### 3.15 Volume-averaged 변수

| # | 변수 키 | 단위 | 설명 |
|---|---------|------|------|
| 1 | `Volume-averaged cell temperature [K]` | K | 체적평균 셀 온도 |
| 2 | `Volume-averaged cell temperature [C]` | °C | 체적평균 셀 온도 |
| 3 | `Volume-averaged ambient temperature [K]` | K | 체적평균 환경 온도 |
| 4 | `Volume-averaged ambient temperature [C]` | °C | 체적평균 환경 온도 |
| 5 | `Volume-averaged surface temperature [K]` | K | 체적평균 표면 온도 |
| 6 | `Volume-averaged total heating [W.m-3]` | W/m³ | 체적평균 총 발열 |
| 7 | `Volume-averaged Ohmic heating [W.m-3]` | W/m³ | 체적평균 옴 발열 |
| 8 | `Volume-averaged irreversible electrochemical heating [W.m-3]` | W/m³ | 체적평균 비가역 발열 |
| 9 | `Volume-averaged reversible heating [W.m-3]` | W/m³ | 체적평균 가역 발열 |
| 10 | `Volume-averaged velocity [m.s-1]` | m/s | 체적평균 속도 |
| 11 | `Volume-averaged acceleration [m.s-1]` | m/s | 체적평균 가속도 |
| 12 | `Volume-averaged negative SEI thickness [m]` | m | 체적평균 음극 SEI 두께 |
| 13 | `Volume-averaged negative SEI concentration [mol.m-3]` | mol/m³ | 체적평균 음극 SEI 농도 |
| 14 | `Volume-averaged negative SEI on cracks thickness [m]` | m | 체적평균 음극 크랙 SEI 두께 |
| 15 | `Volume-averaged negative SEI on cracks concentration [mol.m-3]` | mol/m³ | 체적평균 음극 크랙 SEI 농도 |
| 16 | `Volume-averaged negative lithium plating thickness [m]` | m | 체적평균 음극 석출 두께 |
| 17 | `Volume-averaged negative lithium plating concentration [mol.m-3]` | mol/m³ | 체적평균 음극 석출 농도 |
| 18 | `Volume-averaged negative dead lithium thickness [m]` | m | 체적평균 음극 데드 리튬 두께 |
| 19 | `Volume-averaged negative dead lithium concentration [mol.m-3]` | mol/m³ | 체적평균 음극 데드 리튬 농도 |
| 20 | `Volume-averaged negative particle effective diffusivity [m2.s-1]` | m²/s | 체적평균 음극 유효 확산계수 |
| 21 | `Volume-averaged positive SEI thickness [m]` | m | 체적평균 양극 SEI 두께 |
| 22 | `Volume-averaged positive SEI concentration [mol.m-3]` | mol/m³ | 체적평균 양극 SEI 농도 |
| 23 | `Volume-averaged positive SEI on cracks thickness [m]` | m | 체적평균 양극 크랙 SEI 두께 |
| 24 | `Volume-averaged positive SEI on cracks concentration [mol.m-3]` | mol/m³ | 체적평균 양극 크랙 SEI 농도 |
| 25 | `Volume-averaged positive lithium plating thickness [m]` | m | 체적평균 양극 석출 두께 |
| 26 | `Volume-averaged positive lithium plating concentration [mol.m-3]` | mol/m³ | 체적평균 양극 석출 농도 |
| 27 | `Volume-averaged positive dead lithium thickness [m]` | m | 체적평균 양극 데드 리튬 두께 |
| 28 | `Volume-averaged positive dead lithium concentration [mol.m-3]` | mol/m³ | 체적평균 양극 데드 리튬 농도 |
| 29 | `Volume-averaged positive particle effective diffusivity [m2.s-1]` | m²/s | 체적평균 양극 유효 확산계수 |

---

## 4. SPM 전용 변수 (SPMe/DFN에 없음)

SPM에만 있고 SPMe/DFN에 없는 변수는 **4개**입니다.

| # | 변수 키 | 단위 | 설명 |
|---|---------|------|------|
| 1 | `Negative electrolyte current density [A.m-2]` | A/m² | 음극 전해질 전류밀도 |
| 2 | `Positive electrolyte current density [A.m-2]` | A/m² | 양극 전해질 전류밀도 |
| 3 | `X-averaged negative particle flux [mol.m-2.s-1]` | mol/m²·s | X평균 음극 입자 플럭스 |
| 4 | `X-averaged positive particle flux [mol.m-2.s-1]` | mol/m²·s | X평균 양극 입자 플럭스 |

> 참고: 이 4개는 SPMe에도 포함되어 있으나 **DFN에는 없음**.

---

## 5. SPMe 추가 변수 (SPM 대비 +3)

| # | 변수 키 | 단위 | 설명 | SPM | SPMe | DFN |
|---|---------|------|------|:---:|:----:|:---:|
| 1 | `Electrolyte convection flux [mol.m-2.s-1]` | mol/m²·s | 전해질 대류 플럭스 | ❌ | ✅ | ✅ |
| 2 | `Electrolyte diffusion flux [mol.m-2.s-1]` | mol/m²·s | 전해질 확산 플럭스 | ❌ | ✅ | ✅ |
| 3 | `Electrolyte migration flux [mol.m-2.s-1]` | mol/m²·s | 전해질 이동 플럭스 | ❌ | ✅ | ✅ |

> SPMe는 SPM에 **전해질 확산 방정식**을 추가하므로, 전해질 내 물질 수송을 **대류/확산/이동** 3가지로 분리하여 출력합니다.

---

## 6. DFN 추가 변수 (SPM 대비 +5)

| # | 변수 키 | 단위 | 설명 | SPM | SPMe | DFN |
|---|---------|------|------|:---:|:----:|:---:|
| 1 | `Electrolyte convection flux [mol.m-2.s-1]` | mol/m²·s | 전해질 대류 플럭스 | ❌ | ✅ | ✅ |
| 2 | `Electrolyte diffusion flux [mol.m-2.s-1]` | mol/m²·s | 전해질 확산 플럭스 | ❌ | ✅ | ✅ |
| 3 | `Electrolyte migration flux [mol.m-2.s-1]` | mol/m²·s | 전해질 이동 플럭스 | ❌ | ✅ | ✅ |
| 4 | `Negative electrode effective conductivity` | S/m | 음극 유효 전도도 | ❌ | ❌ | ✅ |
| 5 | `Positive electrode effective conductivity` | S/m | 양극 유효 전도도 | ❌ | ❌ | ✅ |

> DFN은 Full pseudo-2D 모델로 **전극 내 전자 전도**를 명시적으로 해석하므로 유효 전도도가 추가됩니다.

---

## 7. 모델별 누락 변수

### DFN에 없는 변수 (SPM/SPMe에는 있음)

| # | 변수 키 | 단위 | 설명 |
|---|---------|------|------|
| 1 | `Negative electrolyte current density [A.m-2]` | A/m² | 음극 전해질 전류밀도 |
| 2 | `Positive electrolyte current density [A.m-2]` | A/m² | 양극 전해질 전류밀도 |
| 3 | `X-averaged negative particle flux [mol.m-2.s-1]` | mol/m²·s | X평균 음극 입자 플럭스 |
| 4 | `X-averaged positive particle flux [mol.m-2.s-1]` | mol/m²·s | X평균 양극 입자 플럭스 |

> DFN은 전극 내 공간 분포를 명시적으로 해석하므로, 단일 입자 기반의 "X-averaged particle flux"를 별도로 계산하지 않음.

---

## 8. 현재 코드에서 사용 중인 변수

> `BatteryDataTool_optRCD_proto_.py` (`run_pybamm_simulation` 결과 추출부)

| # | 추출 변수 | PyBaMM 키 | 용도 |
|---|----------|----------|------|
| 1 | 시간 | `Time [s]` | 시간축 (÷60 → 분) |
| 2 | 전압 | `Terminal voltage [V]` | 전압 커브, 종합 모니터링 |
| 3 | 전류 | `Current [A]` | 종합 모니터링, dV/dQ 부호 판별 |
| 4 | 용량 | `Discharge capacity [A.h]` | 전압-용량 플롯, dV/dQ |
| 5 | 양극 OCP | `X-averaged positive electrode open-circuit potential [V]` | 전극 분포 플롯 |
| 6 | 음극 OCP | `X-averaged negative electrode open-circuit potential [V]` | 전극 분포 플롯 |
| 7 | 양극 Li 농도 | `X-averaged positive particle surface concentration [mol.m-3]` | 전극 분포 플롯 |
| 8 | 음극 Li 농도 | `X-averaged negative particle surface concentration [mol.m-3]` | SOC 정규화, 전극 분포 플롯 |

### 활용 가능한 추가 변수 (미사용)

전체 510~517개 중 **8개만 사용** 중이며, 다음 변수들을 추가 시각화에 활용할 수 있음:

| 카테고리 | 추천 변수 | 활용처 |
|---------|----------|--------|
| **열 분석** | `Cell temperature [K]`, `Total heating [W]` | 온도 모니터링 탭 |
| **열화 추적** | `LLI [%]`, `LAM_pe [%]`, `LAM_ne [%]` | 수명 예측 탭 |
| **SEI 성장** | `X-averaged negative SEI thickness [m]` | 열화 메커니즘 탭 |
| **리튬 석출** | `Negative lithium plating thickness [m]` | 급속충전 안전성 탭 |
| **전해질 분포** | `Electrolyte concentration [mol.m-3]` | 농도 구배 시각화 |
| **전압 분해** | `X-averaged reaction overpotential [V]`, `X-averaged electrolyte ohmic losses [V]` | 과전압 분석 탭 |
| **SOC** | `Positive/Negative electrode stoichiometry` | 정밀 SOC 추정 |

---

*생성일: 2026-02-26 | PyBaMM v25.12.2 | `model.variables.keys()` 기준*
