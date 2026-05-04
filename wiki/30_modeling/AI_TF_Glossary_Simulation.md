---
title: "AI TF 배터리 용어집 — 시뮬레이션 카테고리 (v2)"
tags: [AI_TF, glossary, terminology, simulation, modeling, P2D, SPM, PINN, MSMD, structural, safety, ECT]
type: reference
status: active
aliases:
  - AI TF 시뮬레이션 용어
  - 배터리 용어 정리 — 시뮬 파트
  - SBP 알고리즘 비교 부속 용어집 — 시뮬
related:
  - "[[AI_TF_Glossary_SBP]]"
  - "[[시뮬레이션_용어사전]]"
  - "[[!용어]]"
  - "[[MSMD]]"
  - "[[PINNSTRIPES_NREL]]"
  - "[[NREL_PINN]]"
  - "[[phygnn_NREL]]"
  - "[[NREL_SSC_수명모델_참고]]"
  - "[[PyBaMM_정리]]"
  - "[[MOC_Modeling_AI]]"
  - "[[배터리_모델링_리뷰]]"
scope: "AI TF 배터리 용어 정리 활동의 시뮬레이션 카테고리 — 박사급 peer 관점, 13개 그룹 151개 항목."
source_tsv: "Downloads/SBP알고/용어_시뮬레이션_v2.txt"
source_origin: "다른 그룹원이 작성한 초안(Downloads/SBP알고/용어.txt)의 시뮬레이션 카테고리 21개 + 본 정비로 추가된 130개"
created: 2026-05-04
updated: 2026-05-04
---

# AI TF 배터리 용어집 — 시뮬레이션

> AI TF 활동의 일환으로 작성된 배터리 용어집의 **시뮬레이션 카테고리**. 다른 그룹원이 작성한 초안의 시뮬레이션 카테고리(원본 21개)를 박사급 peer 관점에서 BDT 실무·NREL House Code·PyBaMM 계열까지 보강해 13개 그룹 151개 항목으로 정비.
>
> 일반 배터리 용어는 [[!용어]], 시뮬레이션 코어 개념의 16-개념 분류 정리는 [[시뮬레이션_용어사전]] 참조. SBP/BMS 카테고리는 [[AI_TF_Glossary_SBP]].

## 📑 13개 그룹 빠른 이동

| # | 그룹 | 항목 |
|---|---|---|
| 1 | 기본 방정식·법칙 | 13 |
| 2 | 원자/분자 스케일 | 7 |
| 3 | 전극·셀 스케일 물리 기반 모델 | 13 |
| 4 | 모듈/팩 스케일 — 열·전기 | 6 |
| 5 | **구조해석·안전성 시뮬레이션** | 28 |
| 6 | 멀티스케일 | 4 |
| 7 | 데이터 기반·하이브리드 모델 | 14 |
| 8 | 상태/파라미터 추정 | 12 |
| 9 | 수명/노화 모델 | 8 |
| 10 | 수치 해석 기법 | 13 |
| 11 | 워크플로우 | 12 |
| 12 | 도구·소프트웨어 | 14 |
| 13 | 응용·실시간 | 7 |
| | **합계** | **151** |

## 🔗 다른 카테고리와의 분리

다른 카테고리에 의미 인접 항목이 있는 경우 정의에 명시적으로 차별화 처리:

- **L6 Tafel 식**: 분석/측정의 Tafel Plot(측정 그래프)과 식(시뮬레이션) 구분
- **L34 응력-확산 결합 모델**: 열화 메커니즘의 '기계적 응력' 현상을 시뮬레이션
- **L39 열폭주 모델**: 안전성/열화의 '열 폭주' 현상을 시뮬레이션
- **L101 SEI 성장 모델**: 열화 메커니즘의 'SEI 성장/분해' 현상을 시뮬레이션
- **L102 Li 도금 모델**: 안전성/열화의 '리튬 플레이팅' 현상을 시뮬레이션

---


## 1. 기본 방정식·법칙

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| 옴의 법칙 | Ohm's Law |  | 전압·전류·저항의 선형 관계 V = IR. ECM과 모든 전기 회로 시뮬레이션의 기본 구성 식. |  |  |
| 네른스트 식 | Nernst Equation |  | 온도와 활동도(농도)에 따른 전극 평형 전위(OCV)를 기술하는 열역학 식. |  |  |
| 패러데이의 법칙 | Faraday's Law |  | 통과한 전하량과 반응한 물질량(Q = n·F·ΔN)의 비례 관계. 용량·쿨롱 효율 계산의 기반. |  |  |
| 버틀러-볼머 식 | Butler-Volmer Equation |  | 전극 표면에서의 전극 전위와 전류 밀도 사이의 관계를 나타내는 식. 전하 전달 저항(Rct) 모델링에 사용됨. |  |  |
| Tafel 식 | Tafel Equation |  | 과전압이 큰 영역에서 Butler-Volmer 식의 근사형. 교환전류 밀도와 전이 계수를 추출하는 데 사용 (분석/측정 카테고리의 'Tafel Plot'은 측정 그래프이며 별개). |  |  |
| 픽의 확산 법칙 | Fick's Laws of Diffusion |  | 농도 구배에 따른 물질의 확산 속도를 설명하는 법칙. 리튬 이온의 확산 현상 모델링에 사용됨. |  |  |
| 아레니우스 식 | Arrhenius Equation |  | 온도에 따른 반응 속도 상수 k = A·exp(-Ea/RT)의 의존성. 캘린더 수명·확산 계수의 활성화 에너지 추출에 사용. |  |  |
| Maxwell-Stefan 방정식 | Maxwell-Stefan Equation |  | 다성분 농축 전해액에서 종(species) 간 상호 확산을 기술하는 식. Fick보다 일반화된 표현. |  |  |
| Poisson-Nernst-Planck | Poisson-Nernst-Planck Equation | PNP | 전기장과 이온 농도 분포의 결합을 풀어 전하 운반을 기술. 묽은 용액 영역에서 사용. |  |  |
| 농축 용액 이론 | Concentrated Solution Theory |  | 묽은 용액 가정을 벗어나는 농축 전해액(>1 M)의 이온 수송 이론. P2D의 기본 가정. | 전해액 농도 분극을 정량화 가능. | 이송 파라미터(t+, D, κ)의 농도 의존성 측정이 까다로움. |
| 푸리에 열전도 법칙 | Fourier's Law of Heat Conduction |  | 온도 구배에 따른 열 유속 q = -k ∇T를 정의. 셀·팩 열 시뮬레이션의 기반. |  |  |
| 나비에-스토크스 방정식 | Navier-Stokes Equations |  | 유체 운동량 보존 식. 팩 냉각수·공기 유동을 기술하며 CFD의 핵심. |  |  |
| 에너지 보존 식 | Energy Conservation Equation |  | 셀 내부 열원(저항 발열·반응열·엔트로피 변화)과 열 전달을 결합한 보존 식. |  |  |

## 2. 원자/분자 스케일

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| 제1원리 계산 | First-principles Calculation | DFT (Density Functional Theory) | 실험 데이터 없이 양자역학의 기본 원리만을 이용하여 물질의 구조, 에너지, 전자 상태 등을 계산하는 기법. 신소재 물성 예측에 사용. |  |  |
| 분자 동역학 | Molecular Dynamics (MD) |  | 원자 또는 분자 간의 상호작용을 기반으로 뉴턴의 운동 방정식을 풀어 시간에 따른 움직임을 모사하는 시뮬레이션 기법. 전해액, 계면 현상 연구에 활용. |  |  |
| 제1원리 분자 동역학 | Ab Initio Molecular Dynamics (AIMD) |  | DFT로 매 시간 스텝의 힘을 계산하면서 MD를 수행하는 기법. 결합 형성·파괴를 다룰 수 있음. |  | 계산 비용이 매우 커 수백 원자·수십 ps 수준의 한계. |
| 반응성 힘장 | Reactive Force Field | ReaxFF | 전하 평형과 결합 차수를 동적으로 갱신하여 화학 반응을 다루는 경험 기반 힘장. SEI/CEI 형성 연구에 사용. |  | AIMD보다 빠르지만 파라미터 보정·전이성 확보가 어려움. |
| 동역학적 몬테카를로 | Kinetic Monte Carlo (KMC) |  | 활성화 에너지가 부여된 이산 사건의 확률적 샘플링으로 시간 진화를 추적. SEI 성장·결정 성장 연구. |  |  |
| 위상장 모델 | Phase Field Model |  | 계면을 연속적인 order parameter로 표현해 미세조직 진화·덴드라이트 성장을 모사. | 계면 추적 없이 형상 진화 가능. | 계면 두께 파라미터 의존, 계산 비용 큼. |
| Marcus 이론 | Marcus Theory of Electron Transfer |  | 재배치 에너지(λ)와 자유에너지로 전자 전달 속도를 기술. Butler-Volmer의 미시적 기반. |  |  |

## 3. 전극·셀 스케일 물리 기반 모델

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| 등가회로 모델 | Equivalent Circuit Model | ECM, Thevenin Model | 배터리의 전기적 거동을 저항(R), 커패시터(C) 등의 조합으로 단순화한 모델. BMS의 SOC, SOH, SOP 추정에 주로 사용됨. | 계산이 빠르고 임베디드 적용이 용이. | 물리적 의미가 약하고, 학습 영역(SOC·온도·C-rate) 외 외삽이 어려움. |
| 1차 RC 모델 | 1RC Model | First-order Thevenin | 저항 1개 + RC 1쌍으로 분극을 표현하는 가장 단순한 ECM. | 실시간성이 매우 높음. | 저주파(확산) 거동을 표현하기 어려움. |
| 2차 RC 모델 | 2RC Model | Second-order Thevenin | 저항 1개 + RC 2쌍으로 빠른(전하전달)·느린(확산) 분극을 분리하는 ECM. 양산 BMS의 표준. | 정확도와 계산량의 균형이 좋음. | 파라미터(6개 이상) 보정 부담 증가. |
| 뉴만 모델 | Newman Model (Pseudo-2D Model) | P2D, DFN (Doyle-Fuller-Newman) | 전극은 다공성 매질로, 활물질은 1D 구형 입자로 가정하여 농축 용액 이론으로 푸는 가장 대표적인 물리 기반 배터리 모델. | 내부 농도·전위 분포까지 정확도가 높음. | 비선형 PDE 시스템으로 계산 비용이 매우 큼. |
| 단일 입자 모델 | Single Particle Model (SPM) |  | 전극을 하나의 평균적인 구형 입자로 가정하여 전해액 분극을 무시한 단순화 모델. | 계산 속도가 매우 빠르고 분석적 해석이 가능. | 전해액 농도 분극·고 C-rate에서 정확도 저하. |
| 전해액 포함 SPM | Single Particle Model with Electrolyte | SPMe | SPM에 전해액 농도/전위 분극을 추가하여 중·고 C-rate까지 적용 가능하게 확장한 모델. | SPM 대비 정확도가 큰 폭으로 향상. | 여전히 평균 입자 가정이 한계. |
| 확장 SPM | Enhanced Single Particle Model | ESPM | SPMe에 부반응(SEI 성장 등)·열 결합을 추가한 확장 모델. | 수명 시뮬레이션과 결합 가능. | 파라미터 수 증가로 동정 부담. |
| 재정식화 SPM | Reformulated SPM | RSPM | 입자 내 확산 PDE를 직교 다항식·라플라스 변환으로 축약하여 ODE로 푸는 기법. | 실시간 BMS 탑재 가능한 속도. | 축약 차수가 부족하면 고주파 응답 손실. |
| Pseudo-3D 모델 | Pseudo-3D Model | P3D | P2D를 셀의 두께 방향(through-plane)에 더해 면 방향(in-plane)까지 확장한 모델. 대형 셀의 전류 불균일 해석. |  | 면 방향 격자에 비례해 비용 급증. |
| 다중 물리 모델링 | Multi-physics Modeling |  | 배터리 내에서 동시에 발생하는 전기화학·열·기계 현상을 연계하여 해석하는 시뮬레이션 기법. |  |  |
| 거시적 모델 | Macroscopic Model |  | 전극을 하나의 균일한 개체로 간주하여 평균적인 거동을 모델링하는 방식. (e.g., ECM, P2D) |  |  |
| 미시적 모델 | Microscopic Model |  | 전극 내부의 활물질 입자, 기공 구조 등을 직접 모델링하여 국소적인 현상을 해석하는 방식. |  |  |
| 응력-확산 결합 모델 | Diffusion-Induced Stress Model |  | '열화 메커니즘' 카테고리의 '기계적 응력' 현상을 시뮬레이션하는 모델. 리튬 삽입에 따른 부피 변화로 발생하는 응력을 확산과 결합해 풀이. | 입자 균열 예측 등 수명·안전성 해석에 필수. | 활물질 기계 물성 측정이 어려움. |

## 4. 모듈/팩 스케일 — 열·전기

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| 럼프드 열 모델 | Lumped Thermal Model |  | 셀을 1점(혹은 코어/표면 2점)으로 가정해 열용량·대류·전도를 1차 ODE로 표현. | 실시간 BTMS 제어용으로 적합. | 내부 온도 구배를 표현 못 함. |
| 1D/2D/3D 열 모델 | 1D/2D/3D Thermal Model |  | 셀·팩 형상에 따라 차원을 늘려 푸리에 식을 풀어내는 열 시뮬레이션. | 내부 핫스팟·열폭주 전이 분석 가능. | 차원이 올라갈수록 계산 비용 급증. |
| 전기-열 연성 모델 | Electro-thermal Coupled Model |  | 전기화학 모델의 발열항을 열 모델로 보내고, 온도를 다시 파라미터(D, k0, κ)에 피드백하는 연성 시뮬레이션. | 온도 의존 거동(저온 출력·고온 열화)을 일관되게 표현. | 연성 알고리즘에 따라 안정성·수렴성 이슈. |
| 전기-열-기계 연성 모델 | Electro-thermal-mechanical Coupled Model |  | 전기화학·열·기계(스웰링·응력)를 모두 결합한 통합 모델. 안전성·수명 해석에 사용. | 열폭주 사전 신호 모사 가능. | 파라미터·계산 비용·검증 난이도 모두 큼. |
| 열폭주 모델 | Thermal Runaway Model |  | '안전성/열화' 카테고리의 '열 폭주' 현상을 시뮬레이션하는 모델. Arrhenius 형식의 부반응(SEI 분해·전해액 분해·양극 산소 방출 등)을 합산해 자기 가속 발열을 풀이. | 셀·팩의 트리거 임계값 예측. | 반응 파라미터(A, Ea)의 불확실성이 큼. |
| 전산 유체 역학 | Computational Fluid Dynamics (CFD) |  | 유체(공기, 냉각수 등)의 움직임과 열 전달을 수치적으로 해석하는 기법. 배터리 팩의 열 관리 시스템 설계에 활용. |  |  |

## 5. 구조해석·안전성 시뮬레이션

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| 구조 해석 | Structural Analysis |  | 외력·내력에 대한 구조물의 변형·응력·변위를 수치 해석으로 평가하는 기법. 셀 외장재·모듈 프레임·팩 트레이의 강성·강도 검증에 사용. |  |  |
| 명시적 동해석 | Explicit Dynamics |  | 시간 적분에 양해법(central difference)을 사용하는 비선형 동해석 기법. 충돌·충격·낙하 등 짧은 시간 대변형 문제의 표준. | 대변형·접촉·파괴를 안정적으로 표현. | CFL 조건이 시간 스텝을 강하게 제한. |
| 암시적 정해석 | Implicit Static Analysis |  | 음해법으로 평형 방정식을 풀어 정적·준정적 하중을 평가하는 해석. 매끄러운 하중-변위 관계에 효율적. | 큰 시간 스텝 가능. | 강한 비선형·접촉 문제에서 수렴성 저하. |
| 준정적 해석 | Quasi-static Analysis |  | 관성 효과가 무시될 만큼 느린 하중 변화를 정적 평형으로 근사하는 해석. 셀 압착·굽힘 시험 모사. |  | 관성·동적 효과를 잃음. |
| 비선형 해석 | Nonlinear Analysis |  | 기하·재료·접촉 비선형성을 포함하는 해석. 셀 변형 한계·금속 캔 좌굴 등에 필수. | 실 거동에 가까운 결과. | 수렴성·계산 비용 부담. |
| 접촉 해석 | Contact Analysis |  | 두 물체 간 접촉·마찰·분리를 모사하는 해석. 젤리롤-캔 접촉, 분리막 파열 모사에 사용. |  | 접촉 알고리즘(penalty/Lagrange) 선택이 결과를 좌우. |
| 모드 해석 | Modal Analysis |  | 구조물의 고유 진동수와 모드 형상을 추출하는 선형 해석. 차량 운행 시 공진 회피 설계의 기반. |  |  |
| 랜덤 진동 해석 | Random Vibration Analysis | PSD Analysis | 입력 PSD(Power Spectral Density)로 통계적 응답(RMS 응력·변위)을 평가하는 진동 해석. 차량용 셀·팩 내구 설계의 표준 (e.g., ISO 16750, GB/T 31467). |  | 선형 가정 한계. |
| 피로 해석 | Fatigue Analysis |  | 반복 하중에 의한 손상을 누적해 수명을 예측하는 해석. S-N 곡선·Miner의 법칙·Rainflow 카운팅과 결합. |  | 재료 피로 곡선 부족 시 신뢰도 저하. |
| 좌굴 해석 | Buckling Analysis |  | 압축 하중 하에서 구조물이 형상을 유지하지 못하고 갑자기 변형되는 좌굴 거동을 평가. 캔·셀 케이스 설계에 사용. |  |  |
| 충돌 해석 | Crash Analysis | Crashworthiness Analysis | 차량 충돌 시 팩의 변형·관통·내부 단락 위험을 평가하는 명시적 동해석. 자동차 EV 안전 인증의 핵심 (e.g., ISO 26262, GB 38031, ECE R100). | 셀 내부 단락 사전 평가 가능. | 셀 내부 균질화 모델 정확도가 결과를 지배. |
| 낙하 해석 | Drop Test Simulation |  | 휴대 기기·제품 낙하 시 셀·모듈 손상을 평가하는 명시적 동해석. UN 38.3·IEC 62133·KC·CTIA 시험을 사전 모사. |  |  |
| 볼 드랍 해석 | Ball Drop Simulation |  | 규정된 무게의 강구를 일정 높이에서 셀 표면에 낙하시켜 충격 손상을 평가하는 시뮬레이션. UL 1642 등 셀 안전성 검증에 사용. |  |  |
| 관통 해석 | Nail Penetration Simulation |  | 못 또는 강체 인덴터로 셀을 관통시켜 발생하는 변형·내부 단락·발열을 모사. '안전성 평가'의 관통 시험을 사전에 수치적으로 평가. | 위험 시험 횟수 절감. | 분리막 파열 임계값 보정이 필수. |
| 압착 해석 | Crush Simulation |  | 셀·모듈을 외부 압축 하중으로 변형시켜 안전 한계를 평가하는 시뮬레이션. SAE J2464·UN 38.3·GB 38031 시험 모사. |  |  |
| 덴트 해석 | Dent Analysis | Indentation Simulation | 외부 충격으로 셀 외장재(캔·파우치)에 발생하는 국부 변형을 평가. 표면 손상이 수명·내부 단락에 미치는 영향 평가. |  |  |
| 임팩트 해석 | Impact Analysis |  | 단발성 고속 하중에 대한 동해석. 펜듈럼 충격·발사체 충돌·물체 충격 모사를 포괄. |  |  |
| CFL 조건 | Courant-Friedrichs-Lewy Condition |  | 명시적 동해석의 시간 스텝을 음파 속도와 격자 크기로 제한하는 안정 조건 (Δt ≤ Δx / c). 위반 시 발산. |  | 너무 작은 격자는 시간 스텝을 강하게 깎음. |
| 존슨-쿡 모델 | Johnson-Cook Plasticity Model |  | 변형률·변형률 속도·온도 의존성을 가진 금속 소성 모델. 충돌·관통 해석에서 캔·전극의 표준 재료 모델. |  | 파라미터 5개 + 파괴 모델 5개로 동정 부담. |
| 초탄성 모델 | Hyperelastic Model | Mooney-Rivlin, Ogden | 큰 변형 영역의 탄성 거동을 변형 에너지 함수로 표현하는 재료 모델. 분리막·바인더 모사에 사용. |  |  |
| 점탄성 모델 | Viscoelastic Model | Prony Series | 시간 의존 탄성 거동을 표현하는 재료 모델. 분리막·고분자 전해질·압축 거동 모사. |  |  |
| 등가 응력 | von Mises Stress | Equivalent Stress | 다축 응력 상태에서 항복 판정의 기준이 되는 등가 스칼라 응력. 구조 해석 결과 후처리의 표준. |  |  |
| 균질화 셀 구조 모델 | Homogenized Cell Structural Model |  | 젤리롤·스택의 미세구조를 평균화해 등가 이방성 재료로 표현하는 모델. 팩 충돌 해석의 셀 표현에 사용. | 대규모 팩 해석 가능. | 내부 단락 위치 특정은 어려움. |
| 표현 부피 요소 | Representative Volume Element (RVE) |  | 미세구조의 거시적 거동을 대표하는 최소 단위 부피. 균질화 파라미터 추출에 사용. |  |  |
| SPH | Smoothed Particle Hydrodynamics |  | 격자 없이 입자로 매질을 표현하는 무격자(meshfree) 기법. 매우 큰 변형·파편 비산·관통 시뮬레이션에 적합. |  | 입자 수가 많아 계산 비용 큼. |
| ALE | Arbitrary Lagrangian-Eulerian |  | 격자가 물질이나 공간에 고정되지 않고 임의로 움직이도록 허용하는 기법. 큰 변형 시 격자 왜곡(distortion) 회피. |  |  |
| 단락 발생 기준 | Short-Circuit Criterion |  | 변형·응력·관통 깊이가 임계값을 초과할 때 셀 내부 단락이 발생한다고 판단하는 시뮬레이션 후처리 기준. |  | 임계값 동정에 별도 셀 시험 필요. |
| 분리막 파열 모델 | Separator Failure Model |  | 변형률·온도·관통 압력에 의해 분리막이 파열되어 단락이 발생하는 거동을 모사. 충돌·관통 해석의 핵심. |  | 파열 임계값의 시험 산포가 큼. |

## 6. 멀티스케일

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| 다중 스케일 다중 영역 모델 | Multi-Scale Multi-Domain | MSMD | NREL Kim et al. (2011)이 제안한 프레임워크. 입자(particle)/전극(electrode)/셀(cell) 도메인을 분리해 다른 모델·격자로 풀고 결합. | 도메인별로 적절한 모델·해법을 선택할 수 있어 대규모 셀 해석에 유리. | 도메인 간 정보 교환 정확도가 결과를 좌우. |
| GH-MSMD | Gauss-Hermite Quadrature MSMD |  | MSMD에서 입자 도메인을 가우스-에르미트 적분점으로 축약(NREL JES 2017). 입자 PDE 풀이 비용을 큰 폭으로 절감. | 대형 셀 P2D 해석을 실시간에 근접한 속도로 수행. | 적분점 수 부족 시 고 C-rate 정확도 손실. |
| 균질화 | Homogenization |  | 미시 구조(입자·기공 분포)의 평균적 거동을 거시 파라미터(유효 전도도·유효 확산계수)로 대체하는 수학적 절차. | 멀티스케일 모델의 핵심 도구. | 이방성·국소 변동성 정보가 손실. |
| Bruggeman 보정 | Bruggeman Relation / Effective Tortuosity |  | 다공성 전극의 유효 이온 확산을 ε^β / τ 형태로 보정하는 경험식. | P2D/SPMe의 표준 보정. | 실측 굴곡률과 큰 차이가 날 수 있음. |

## 7. 데이터 기반·하이브리드 모델

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| 대리 모델 | Surrogate Model | Meta-model | 고비용 물리 모델의 입출력 관계를 학습해 빠르게 평가할 수 있도록 만든 근사 모델. | 최적화·UQ 반복 계산 시간을 수 자릿수 단축. | 외삽 영역에서 신뢰도 급락. |
| 가우시안 프로세스 회귀 | Gaussian Process Regression (GPR) |  | 함수 자체에 가우시안 사전(prior)을 두어 평균과 불확실성을 동시에 출력하는 비모수 회귀. | 소량 데이터로도 UQ가 가능. | 데이터 점 수 N에 대해 O(N³) 비용. |
| 인공 신경망 | Artificial Neural Network (ANN) |  | 다층 비선형 함수 근사기. SOC/SOH 회귀·노화 예측 등에 사용. |  | 과적합 위험과 외삽 한계. |
| 순환 신경망 | Recurrent Neural Network | RNN/LSTM/GRU | 이전 시점 상태를 다음 시점에 전달해 시계열 의존성을 학습. SOC 추정·드라이빙 사이클 예측에 활용. |  | 긴 시퀀스에서 그래디언트 소실/폭주 문제. |
| 합성곱 신경망 | Convolutional Neural Network (CNN) |  | 지역 패턴(EIS Nyquist, dQ/dV 곡선, 셀 이미지)을 추출해 분류·회귀에 사용. | 특징 자동 추출. | 회전·노이즈에 민감할 수 있음. |
| 트랜스포머 | Transformer |  | 어텐션 메커니즘 기반 시계열·시퀀스 모델. 대용량 사이클 데이터에서 RNN을 대체. | 긴 의존성 학습. | 데이터·계산 자원 요구가 큼. |
| 물리 정보 신경망 | Physics-Informed Neural Network (PINN) |  | 지배 방정식의 잔차를 손실 함수에 포함시켜 학습하는 신경망. SPM/P2D surrogate 구축에 사용. | 데이터가 부족해도 물리적 일관성 유지. | 손실 항의 가중치 튜닝이 어려움. |
| 물리 가이드 신경망 | Physics-Guided Neural Network | phygnn | NREL이 제안한 PINN 변형. 물리 사전을 손실·아키텍처에 결합한 프레임워크. | BDT 잔존 수명 예측 surrogate 후보. | 도메인별 손실 설계 필요. |
| PINNSTRIPES | PINNSTRIPES |  | Hassanaly et al. (2024) NREL이 공개한 P2D/SPM PINN surrogate 코드베이스. PyBaMM 검증 데이터와 연계. | 실시간 P2D 평가를 가능하게 함. | 특정 화학·운전 조건에 학습 의존. |
| 연산자 학습 | Operator Learning | DeepONet, FNO | 함수→함수 매핑 자체를 학습하여 PDE 해를 즉시 추론. 다양한 입력 프로파일에 일반화. | 메시 의존성에서 자유로움. | 이론적 보장은 아직 제한적. |
| 하이브리드 모델 | Hybrid Physics-ML Model |  | 물리 모델의 잔차나 미지 항을 ML로 보정하는 결합 구조. 화이트박스의 해석성과 블랙박스의 정확도 결합. | BDT empirical/EC 트랙 결합 후보. | 검증·인증 절차가 복잡. |
| 강화학습 | Reinforcement Learning (RL) |  | 보상 함수를 통해 의사결정 정책을 학습. 급속 충전 프로파일·BTMS 제어 최적화에 응용. | 비선형 제약을 갖는 제어 정책 자동화. | 안전 제약 보장이 까다로움. |
| 능동 학습 | Active Learning |  | 다음에 측정/시뮬레이션할 입력을 정보 획득량 기준으로 선택하는 학습 전략. 실험 캠페인 설계에 사용. | 실험 횟수 대폭 절감. | 획득 함수 설계가 결과를 좌우. |
| 디지털 트윈 | Digital Twin |  | 실제 셀/팩의 측정 데이터를 실시간으로 받아 동기화되는 가상 모델. 잔존 수명·고장 사전 진단에 사용. | 필드 데이터 기반 의사결정 지원. | 모델·센서·통신 인프라가 모두 갖춰져야 함. |

## 8. 상태/파라미터 추정

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| 칼만 필터 | Kalman Filter (KF) |  | 측정값의 노이즈를 고려하여 시스템의 상태를 재귀적으로 추정하는 알고리즘. 선형 가우시안 시스템의 최적 추정. | SOC 추정에 가장 널리 사용됨. | 비선형 시스템에 직접 적용 불가. |
| 확장 칼만 필터 | Extended Kalman Filter (EKF) |  | 비선형 모델을 작동점에서 1차 선형화하여 KF 형식을 적용하는 추정기. | 계산이 가벼워 양산 BMS의 표준. | 강한 비선형에서 발산 위험. |
| 무향 칼만 필터 | Unscented Kalman Filter (UKF) |  | Sigma point를 비선형 함수에 통과시켜 평균·공분산을 보존하는 추정기. | EKF 대비 비선형성 강한 영역에서 정확. | 계산량이 EKF 대비 큼. |
| 적응형 UKF | Adaptive UKF (AUKF) |  | 잡음 공분산을 측정 잔차로부터 온라인으로 갱신하는 UKF. 저항 변화 등 시변 시스템에 적합. | SOH 추적과 결합 시 유리. | 조정 파라미터가 많아 튜닝 부담. |
| 파티클 필터 | Particle Filter |  | 상태 사후 분포를 가중치를 갖는 입자 집합으로 근사하는 비선형·비가우시안 추정기. | 강한 비선형·다봉 분포에서도 동작. | 입자 수에 따라 계산 비용 큼. |
| 루엔버거 옵저버 | Luenberger Observer |  | 측정 잔차에 이득(L)을 곱해 상태를 추정하는 결정론적 옵저버. | 구조가 단순해 임베디드 친화적. | 확률적 잡음 모델은 표현 못 함. |
| 슬라이딩 모드 옵저버 | Sliding Mode Observer (SMO) |  | 비선형 강건 옵저버. 모델 불확실성에 강함. SOC 추정에 사용. |  | 채터링(chattering) 현상. |
| 재귀 최소 자승법 | Recursive Least Squares (RLS) |  | ECM 파라미터를 측정 데이터가 들어올 때마다 갱신하는 온라인 추정기. | 실시간 R/C 추정에 표준. | 망각 인자 튜닝 필요. |
| 베이지안 추정 | Bayesian Estimation |  | 사전 분포와 가능도를 결합해 사후 분포를 갱신하는 추정 프레임워크. | 불확실성 정량화와 자연스럽게 결합. | 사후 계산이 일반적으로 비쌈. |
| 최대 사후 / 최우 추정 | Maximum A Posteriori / Maximum Likelihood | MAP / MLE | 파라미터의 사후 최빈값(MAP) 또는 가능도 최대화(MLE)로 점 추정을 구하는 기법. |  |  |
| 파라미터 추정 (온라인) | Online Parameter Estimation |  | BMS 운전 중 측정 데이터로부터 ECM의 R/C 등 모델 파라미터를 재귀적으로 갱신하는 온라인 동정 기술. RLS·KF 계열과 결합. | 실시간 SOH 추적 가능. | 초기값·여기 신호(excitation) 부족 시 발산. |
| 파라미터화 (오프라인) | Offline Parameterization |  | 시뮬레이션 모델(P2D, ECM 등)에 사용되는 저항·확산계수 등 파라미터 값을 GITT, EIS, OCV, pulse-test 등 실험 데이터로부터 사전에 추출하는 오프라인 절차. | 정확한 파라미터로 모델 신뢰도 확보. | 대량의 셀 시험·해석 시간 필요. |

## 9. 수명/노화 모델

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| 경험적 수명 모델 | Empirical Lifetime Model |  | 온도·DOD·C-rate 등 운전 변수의 경험적 함수로 용량 손실을 적합 (e.g., Wang 2011, Bloom 2001). | 실험 기반으로 BMS 탑재 용이. | 외삽·다른 화학 적용 시 신뢰도 저하. |
| 반경험적 수명 모델 | Semi-Empirical Lifetime Model |  | Eyring/Arrhenius 가속 인자와 메커니즘 모티프(√t SEI 형성 등)를 결합. 캘린더와 사이클 항을 분리. | 물리적 해석과 적합성의 균형. | 메커니즘 분리에 가정이 필요. |
| 메커니즘 기반 수명 모델 | Mechanistic Lifetime Model |  | '열화 메커니즘' 카테고리의 LLI/LAM, SEI 성장, Li plating, 입자 균열 등 개별 현상을 ODE로 풀어 P2D/SPMe와 결합한 수명 시뮬레이션 모델. | 열화 원인 진단에 강력. | 파라미터 다수, 검증 데이터 요구량 큼. |
| 캘린더-사이클 분리 모델 | Calendar-Cycle Separation Model |  | 총 용량 손실을 캘린더(보관)와 사이클(운전) 항의 합으로 분리해 적합. NREL SSC Lifetime의 기본 형식. | 필드 운전 시나리오에 따라 합산 가능. | 두 항의 상호작용을 무시하면 오차. |
| SEI 성장 모델 | SEI Growth Model |  | '열화 메커니즘' 카테고리의 'SEI 성장/분해' 현상을 시뮬레이션하는 모델. Tafel(전위 의존) 또는 parabolic(√t) 형식으로 SEI 두께·LLI를 시간에 대해 적분. | 캘린더 열화의 표준. | 초기 막 형성 단계 표현이 어려움. |
| Li 도금 모델 | Lithium Plating Model |  | '안전성/열화' 카테고리의 '리튬 플레이팅' 현상을 시뮬레이션하는 모델. 음극 표면 과전위가 0 V vs Li/Li+ 이하로 떨어질 때 plating 전류를 추가 반응으로 분기. | 저온·고속 충전 안전 한계 예측. | plating 일부의 가역(intercalation 복귀) 모델링이 까다로움. |
| 등가 사이클 누적 | Equivalent Full Cycle Accumulation | EFC | 임의 충방전 프로파일을 1C 등가 풀 사이클 수로 환산해 누적 노화를 계산. | 필드 데이터 압축에 유리. | 경로 의존성을 잃음. |
| Rainflow 카운팅 | Rainflow Counting |  | 임의 SOC 시계열을 (DOD, mean-SOC) 사이클로 분해하는 피로 해석 기법. 사이클 노화 모델 입력으로 사용. |  | 잔여 반사이클 처리에 약속이 필요. |

## 10. 수치 해석 기법

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| 유한 요소법 | Finite Element Method (FEM) |  | 해석 대상을 유한한 개수의 작은 요소(Element)로 나누어 근사해를 구하는 수치 해석 기법. 구조, 열, 전자기장 해석 등에 널리 사용됨. |  |  |
| 유한 체적법 | Finite Volume Method (FVM) |  | 보존량(질량·운동량·에너지)을 셀 체적 단위로 적분해 푸는 기법. CFD·열 해석의 표준. | 보존성이 자연스럽게 만족. | 비구조 격자에서 정확도 저하 가능. |
| 유한 차분법 | Finite Difference Method (FDM) |  | 미분을 격자점 간 차분으로 근사해 PDE를 푸는 가장 단순한 수치 기법. | 구현이 쉬움. | 복잡한 형상 처리가 어려움. |
| 스펙트럴 방법 | Spectral Method |  | 해를 직교 기저(체비셰프·푸리에·Legendre 등)의 합으로 전개해 푸는 기법. 매끄러운 해에서 지수적 수렴. |  | 비매끄러운 해(충격파)에서 Gibbs 현상. |
| 이산 요소법 | Discrete Element Method (DEM) |  | 입자 집합 간 접촉·마찰을 풀어 분체·전극 압연 등을 모사. | 전극 미세구조 시뮬레이션에 활용. | 입자 수에 비례한 큰 비용. |
| 격자 볼츠만 방법 | Lattice Boltzmann Method (LBM) |  | Boltzmann 방정식을 이산화해 메소스케일 유체·다공성 매질 흐름을 풀이. | 복잡 다공성 전극의 유효 물성 추출에 적합. | 압축성·고 마하 영역에 약함. |
| 모델 차수 축소 | Model Order Reduction (MOR) | ROM | 고차원 모델의 주요 모드를 추출해 저차원 시스템으로 축약. P2D→ROM으로 BMS 탑재. | 실시간 평가 가능. | 비선형성·외삽 영역에서 정확도 저하. |
| 적합 직교 분해 | Proper Orthogonal Decomposition (POD) |  | 스냅샷 행렬의 SVD로 에너지 우위 모드를 추출하는 차원 축소 기법. ROM 구축에 사용. |  |  |
| 메싱 | Meshing |  | FEM, CFD 등 수치 해석을 위해 해석 대상을 작은 격자(Mesh) 또는 요소(Element)로 분할하는 작업. | 격자의 품질과 조밀도가 해석의 정확도와 계산 시간에 큰 영향을 줌. |  |
| 경계 조건 | Boundary Condition |  | 시뮬레이션 모델의 경계에서 정의되는 물리적 조건(온도, 전압, 열 유속 등). |  |  |
| 초기 조건 | Initial Condition |  | 시뮬레이션 시작 시점의 상태 변수(SOC·온도·농도 분포) 값. 결과 수렴까지의 transient를 결정. |  |  |
| 양해법/음해법 | Explicit / Implicit Solver |  | 시간 적분 시 다음 스텝이 현재 변수만으로 결정되면 explicit, 미지수와 결합된 방정식을 풀면 implicit. | implicit는 큰 Δt 가능, explicit는 단순. | implicit는 행렬 풀이 비용, explicit는 안정 조건 제한(CFL). |
| 시간 적분 기법 | Time Integration Scheme |  | Backward Euler, Crank-Nicolson, BDF, RK45 등 ODE/DAE 시간 진행 알고리즘. |  |  |

## 11. 워크플로우

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| 모델 검증 | Model Validation |  | 시뮬레이션 결과가 실제 실험 결과와 얼마나 잘 일치하는지를 비교하여 모델의 신뢰도를 검증하는 과정. |  |  |
| 모델 보정 | Model Calibration |  | 측정 오차·모델 단순화의 영향을 보정하기 위해 일부 파라미터를 데이터에 맞춰 미세 조정하는 절차. | 검증 전 단계로 잔차를 최소화. | 과적합으로 일반화 능력 손실 위험. |
| 민감도 분석 | Sensitivity Analysis |  | 특정 입력 파라미터의 변화가 결과에 얼마나 큰 영향을 미치는지 분석하는 기법. |  |  |
| 글로벌 민감도 분석 | Global Sensitivity Analysis | Sobol, Morris | 전 파라미터 공간을 샘플링해 주효과(Si)·총효과(STi) 지수를 계산하는 정량 기법. | Local SA보다 신뢰성이 높음. | 샘플 수에 비례한 큰 비용. |
| 불확실성 정량화 | Uncertainty Quantification (UQ) |  | 입력·모델 불확실성이 출력에 어떻게 전파되는지 정량화. Monte Carlo, PCE, GPR surrogate 등 사용. | 신뢰 구간을 동반한 의사결정 가능. | 계산 비용·통계적 가정 부담. |
| 역문제 | Inverse Problem |  | 관측 데이터로부터 모델 파라미터·내부 상태를 역으로 추정하는 문제. EIS fitting·SOH 추정의 본질. | 실험 정보를 모델로 환원. | 비유일 해(non-unique) 위험. |
| 데이터 동화 | Data Assimilation |  | 관측을 반복적으로 모델에 주입해 상태·파라미터 추정치를 갱신하는 기법. KF/EnKF/4D-Var 계열. | 필드 운영 모델의 표준. | 선형/비선형·계산 자원 균형 필요. |
| 실험 계획법 | Design of Experiments (DOE) |  | 최소 실험으로 최대 정보를 얻도록 인자·수준을 설계하는 통계 기법. (e.g., Full factorial, Latin Hypercube, D-optimal) | 노화 실험 캠페인의 표준. | 선형성 가정의 한계. |
| 베이지안 최적화 | Bayesian Optimization |  | GPR surrogate와 획득 함수(EI, UCB)로 비싼 목적함수의 최적점을 찾는 기법. 충전 프로토콜·셀 설계 최적화. | 소수 실험으로 수렴. | 고차원에서 효율 저하. |
| 유전 알고리즘 | Genetic Algorithm (GA) |  | 자연 선택을 모사한 메타휴리스틱 최적화. 비미분·다봉 함수에 적합. |  | 수렴 보장 없음. |
| 회귀 검증 | Regression Validation |  | 코드/모델 수정 후 baseline 케이스 결과를 자동 비교해 회귀(regression)를 잡아내는 검증 프로세스. BDT 표준 4-케이스 회귀 검증기가 대표적 운영 사례. | 리팩터링·라이브러리 업데이트의 안전망. | baseline 갱신 정책이 명확해야 함. |
| 도메인 적응 | Domain Adaptation / Transfer Learning |  | 셀 A에서 학습한 모델을 셀 B에 빠르게 이식하는 기법. 사전 학습 + 소량 fine-tuning. | 신규 셀 학습 비용 절감. | 도메인 시프트가 크면 부정적 전이. |

## 12. 도구·소프트웨어

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| COMSOL Multiphysics | COMSOL Multiphysics |  | 유한 요소 기반 다중 물리 상용 SW. 배터리 모듈로 P2D/3D 열·기계 연성 해석을 지원. |  | 라이선스 비용이 높음. |
| Ansys Fluent | Ansys Fluent |  | FVM 기반 CFD 상용 SW. 팩 BTMS 유동·열 해석에 표준. |  |  |
| GT-AutoLion | GT-AutoLion |  | Gamma Technologies의 P2D 기반 배터리 셀·시스템 시뮬레이션 SW. GT-SUITE와 연계되어 차량급 통합 해석에 사용. |  |  |
| Simulink/Simscape Battery | Simulink / Simscape Battery |  | MathWorks의 시스템·제어 시뮬레이션 환경. ECM·열 모델로 BMS·HIL 검증. |  |  |
| PyBaMM | Python Battery Mathematical Modelling | PyBaMM | Oxford-Imperial 컨소시엄이 주도하는 오픈소스 P2D/SPM(e) 솔버. BDT House Code의 검증 베이스. | 자유로운 모델 확장·자동 미분 지원. | 상용 SW 대비 GUI·고객지원 부재. |
| MPET | Multiphase Porous Electrode Theory | MPET | MIT Bazant 그룹의 오픈소스 다상 다공성 전극 솔버. LFP 등 상분리 활물질 해석에 강함. |  |  |
| BatPaC | Battery Performance and Cost | BatPaC | Argonne 국립연구소의 셀·팩 설계·코스트 계산 도구. 양산 셀 BoM·비용 산정. |  | 전기화학 디테일은 부족. |
| Cantera | Cantera |  | 전기화학·화학반응 동역학 오픈소스 라이브러리. 부반응·열폭주 분해 반응 모델링. |  |  |
| Dakota | Dakota |  | Sandia 국립연구소의 UQ·민감도·최적화 툴킷. 외부 시뮬레이터와 결합해 사용. |  |  |
| LS-DYNA | LS-DYNA |  | Ansys 자회사 LSTC의 명시적 동해석 상용 SW. 충돌·낙하·관통·볼 드랍 등 안전성 시뮬레이션의 산업 표준. |  |  |
| Abaqus | Abaqus |  | Dassault Systèmes의 Implicit/Explicit 통합 FEM SW. 셀·팩 비선형 구조·열·전기 연성 해석에 광범위 사용. |  |  |
| Altair Radioss | Altair Radioss |  | Altair의 명시적 동해석 SW. 자동차 충돌·드롭 모사에 자주 사용. |  |  |
| MSC Nastran | MSC Nastran |  | 항공우주·자동차의 모드·정적·랜덤 진동 해석 표준 상용 SW. |  |  |
| Pam-Crash | ESI Pam-Crash |  | ESI Group의 충돌 해석 SW. 차량 안전·배터리 팩 충돌 시뮬레이션에 사용. |  |  |

## 13. 응용·실시간

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| 모델-인-더-루프 | Model-in-the-Loop | MIL | 제어 알고리즘과 플랜트 모델을 같은 시뮬레이션 환경에서 결합해 검증하는 단계. 개발 초기. |  |  |
| 소프트웨어-인-더-루프 | Software-in-the-Loop | SIL | 컴파일된 제어 코드와 플랜트 모델을 결합해 검증. |  |  |
| 프로세서-인-더-루프 | Processor-in-the-Loop | PIL | 타겟 마이크로컨트롤러에 코드를 적재하고 플랜트 모델과 결합해 실시간 거동을 검증. |  |  |
| 하드웨어-인-더-루프 | Hardware-in-the-Loop | HIL | BMS·인버터 등 실제 ECU와 셀/팩 모델을 실시간 시뮬레이터로 결합해 검증하는 인증 전 단계. | 양산 BMS 검증의 표준. | 실시간 솔버 성능이 모델 충실도를 제한. |
| 실시간 시뮬레이션 | Real-time Simulation |  | 솔버가 실세계 시간보다 빠르거나 같은 속도로 실행되어야 하는 시뮬레이션. HIL의 전제 조건. |  |  |
| 임베디드 모델 | Embedded Battery Model |  | BMS MCU에 탑재되어 SOC/SOH/SOP를 실시간 추정하는 경량 배터리 모델 (보통 ECM, RSPM, GH-MSMD 등). | 실차/실제품 동작. | 메모리·연산 성능 제약. |
| ECT 통합 시뮬레이션 | Electro-Chemo-Thermal Coupled Simulation | ECT | 전기·화학·열을 일관되게 풀어 빅데이터 기반 운전 시나리오를 평가. BDT 트랙 7의 핵심 골격. | 필드 데이터 reproducibility 확보. | 데이터 양·검증 인프라 부담. |
