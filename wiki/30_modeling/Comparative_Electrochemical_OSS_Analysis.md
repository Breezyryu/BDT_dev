---
relocated: 2026-04-22
source_vault: "docs/vault/01_Modeling_AI/Comparative_Electrochemical_OSS_Analysis.md"
title: "전기화학 시뮬레이션 오픈소스 비교 딥서치 (P2D / PINN / MD)"
aliases:
  - Comparative Electrochemical OSS Analysis
  - 전기화학 OSS 비교
tags:
  - Modeling_AI
  - P2D
  - DFN
  - SPM
  - PINN
  - MD
  - reference
  - comparison
type: reference
status: active
related:
  - "[[PyBaMM_정리]]"
  - "[[PyBaMM_Solve]]"
  - "[[Analysis_PyBaMM_ExpressionTree]]"
  - "[[SUNDIALS]]"
  - "[[PINNSTRIPES_NREL]]"
  - "[[phygnn_NREL]]"
  - "[[PINN_기초]]"
  - "[[PINN_문헌정리]]"
  - "[[NREL_PINN]]"
  - "[[Knowledge_PINN_DeepONet]]"
  - "[[Empirical_Degradation_Models]]"
  - "[[NREL_SSC_수명모델_참고]]"
created: 2026-04-19
updated: 2026-04-19
source: "멀티-에이전트 딥서치 (GitHub / ReadTheDocs / arXiv / JES / JOSS)"
---

# 전기화학 시뮬레이션 오픈소스 비교 딥서치 (P2D · PINN · MD)

> [!abstract] 요약
> 배터리 전기화학 시뮬레이션 오픈소스를 **코딩 · 수치해석 · 전기화학** 3관점에서 심층 비교.
> - **P2D 계열 9종**: PyBaMM · MPET · COBRAPRO · cideMOD · PETLION.jl · BattMo.jl · PyBOP · SLIDE · formation-modeling
> - **PINN 계열 3종**: PINN-Battery-Prognostics · PINN-SPM-fast-prototyping · PINNSTRIPES
> - **MD 계열 2종**: moleculer-db (⚠️ 오인 URL) · openmmtools
> 축: **지배 방정식 / 이산화 / 솔버 / 자동미분 / 파라미터 추정 / 라이선스 / 성능 / BDT 연계**

---

## 0. 분석 축

본 문서는 다음 7축으로 각 프로젝트를 정량 비교한다.

| 축           | 내용                                    | 이유                  |
| ----------- | ------------------------------------- | ------------------- |
| **지배 방정식**  | SPM / SPMe / DFN / 열 / 열화 확장          | 모델 scope 및 물리 표현력   |
| **이산화**     | FVM / FEM / FDM / Spectral / 0-D      | 수렴성·정확도·mesh 적응성    |
| **솔버**      | DAE/ODE integrator · 선형대수             | 안정성·속도·stiffness 대응 |
| **AD**      | Symbolic / CasADi / JAX / ForwardDiff | 감도·경사기반 역문제         |
| **파라미터 추정** | MCMC · PSO · CMA-ES · adjoint         | 역문제 생태계 통합도         |
| **라이선스**    | BSD/MIT/AGPL/NOASSERTION              | 사내 배포 가능성           |
| **BDT 연계**  | Python/PyBaMM 중심 BDT와의 통합 비용          | 실제 적용 우선순위          |

---

## 1. P2D 계열

### 1.1 PyBaMM — Python/BSD-3 ([GitHub](https://github.com/pybamm-team/PyBaMM))

- **언어/라이선스**: Python 3, **BSD-3**, NumFOCUS 거버넌스.
- **Model scope**: `SPM`, `SPMe`, `MPM`, `DFN`, `NewmanTobias`, `MSMR`(다반응 다사이트), `Yang2017`(SEI+plating), 열 모델(lumped/x-full/3D), 열화 서브모델(SEI 4종 kinetics / Li plating / crack / LAM).
- **지배 방정식**: Newman 정식 DFN — Fick particle, 농축용액 전해질 ($\varepsilon \partial c_e/\partial t = \partial_x(D_e^{eff}\partial_x c_e) + (1-t^+)/F \cdot j$), Butler-Volmer ($j = j_0[\exp(\alpha_a F\eta/RT)-\exp(-\alpha_c F\eta/RT)]$), 수정 Ohm ($\partial_x(\kappa^{eff}\partial_x\phi_e) + \partial_x(\kappa_D^{eff}\partial_x\ln c_e) + j = 0$). 확장: Verbrugge/Baker MSMR, Reniers/O'Kane LAM, 복합 전극.
- **이산화**: **FVM (기본)** + Chebyshev 스펙트럴 옵션. `Discretisation` 클래스가 Expression Tree를 상태벡터로 변환 (→ [[Analysis_PyBaMM_ExpressionTree]]).
- **솔버**: 1순위 **IDAKLUSolver** (SUNDIALS IDAS BDF + KLU sparse LU, C++, OpenMP 배치). 대안: `CasadiSolver`(CasADi+SUNDIALS, safe/fast/fast-with-events), `ScipySolver`, `AlgebraicSolver`(KINSOL), `JaxSolver`/`JaxBDFSolver`(미분가능).
- **AD**: 두 경로 — (1) **CasADi 심볼릭** 희소 해석 Jacobian + `InputParameter` 감도, (2) **JAX** 완전 미분가능 전진 해 (`idaklu_jax`).
- **파라미터 추정**: 내장 MCMC 없음. `InputParameter` 감도 출력 + [[PyBOP|PyBOP]] 연동 (CMA-ES/PINTS). EIS 피팅 `pybamm-eis`.
- **성능**: IDAKLU 기준 상용 솔버급. DFN 1-C 방전 ~1초 미만 (laptop). OpenMP 배치 병렬. GPU는 JAX 경로.
- **I/O**: `ParameterValues("Chen2020")`, BPX JSON, 자연어 DSL (`"Discharge at C/10 for 10 hours"`), Solution 객체 (NumPy/CSV/JSON/pickle 저장).
- **문서**: docs.pybamm.org Sphinx, 수십 개 Colab 노트북.
- **커뮤니티**: ★1,539, 760 forks, 2026-04-17 커밋, Oxford/Imperial/Birmingham/NREL 공동.
- **차별점**: **심볼릭 Expression Tree 추상화** — 수식 그대로 PDE 작성, 자동 CasADi/JAX 전송. 서브모델 플러그인 아키텍처. MSMR / JAX 미분가능 경로. NumFOCUS.
- **BDT 연계**: **BDT 공식 백엔드**. 별도 조치 불필요.

### 1.2 MPET — Python/MIT-ish ([GitHub](https://github.com/TRI-AMDD/mpet))

- **언어/라이선스**: Python + daetools (MIT-family, 인용 요청). Toyota Research Institute.
- **Model scope**: 포러스 전극 이론 + **다입자(multi-particle-per-volume)** 앙상블. **Cahn-Hilliard/Allen-Cahn 상분리 phase-field** (LFP / graphite staging의 비평형 열역학 특화). 열 모델 미지원.
- **지배 방정식**: 입자 `∂c_i/∂t = -∇·F_i`, 흐름 `F_i = -(D_i c_i/k_B T)∇μ_i`. 상분리 BC는 surface energy Neumann `n·κ∇c_i = ∂γ_s/∂c_i`. 반응: **BV + Marcus + Marcus-Hush-Chidsey + CIET**(Coupled-Ion-Electron-Transfer, Bazant). 전해질: Stefan-Maxwell 농축용액 또는 희석.
- **이산화**: 1D 매크로 FV + 입자 앙상블 (구형 or 1D slab). 4차 Cahn-Hilliard 연산자는 2차 FV 분할.
- **솔버**: **daetools → SUNDIALS IDAS** (variable-order BDF DAE). SuperLU. GPU 없음.
- **AD**: daetools 심볼릭 (operator overloading). 외부 감도 노출 없음.
- **파라미터 추정**: 내장 없음. 앙상블 sweep은 외부 fitter 연동.
- **성능**: 클러스터 지향. 상분리 많은 입자에서 비용 큼. 내부 병렬 없음.
- **I/O**: INI `params_system.cfg`, HDF5/MAT 출력, Dash 대시보드.
- **커뮤니티**: ★39, 2024-12 마지막 커밋. 원저: Smith & Bazant, JES 164, E3291 (2017).
- **차별점**: **유일한 phase-field P2D OSS**. CIET/Marcus-Hush-Chidsey 반응 메뉴. 입자간 접촉저항 네트워크.
- **BDT 연계**: 직접 결합 없음. LFP/graphite staging 해석 요구 시 별도 실행 → 파라미터(상분리 계수) 추출 후 PyBaMM 측면 확장.

### 1.3 COBRAPRO — MATLAB/MIT ([GitHub](https://github.com/COBRAPROsimulator/COBRAPRO))

- **언어/라이선스**: MATLAB ≥2016a, **MIT**. Onori group (Stanford).
- **Model scope**: **DFN(P2D) 단일**, isothermal, 열화 없음. 핵심 가치는 **파라미터 식별**.
- **지배 방정식**: 표준 DFN. 논문 JES 2024 (Ha & Onori, doi:10.1149/1945-7111/ad7292)에 수치기법 + **consistent initial-condition 알고리즘** (index-1 DAE) 명시. 
- **이산화**: **FVM + Hermite 보간** — 입자 표면 농도 / `De_eff` / `κ_eff` / `c_e` / 전극 BC 전부 Hermite (`DFN_model/FVM_interpolation/`). 단순 선형 대비 정확도·성능 이득.
- **솔버**: **SUNDIALS IDAS** via sundialsTB mex. CasADi로 해석적 Jacobian.
- **AD**: CasADi 심볼릭. Local Sensitivity Analysis 내장.
- **파라미터 추정**: ⭐ **내장 PSO** (`particleswarm` + `parpool`) + `ga`/`fmincon`/`patternsearch`. **LSA+상관분석 기반 식별성 분석** (`DFN_LSA_Corr_CC.m`, `DFN_LSA_Corr_HPPC.m`) — 비식별 파라미터 제거 후 calibration.
- **성능**: DEARLIBS 대비 **~1000× 가속** (JOSS arXiv 2404.10022).
- **I/O**: MATLAB .mat/.csv.
- **커뮤니티**: ★27, 2025-09-15 커밋.
- **차별점**: **DFN + 식별성 분석 + PSO가 통합된 유일 OSS**. README가 PyBaMM/LIONSIMBA/PETLION/MPET에는 identification 내장이 없다고 명시. COMSOL 교차검증.
- **BDT 연계**: MATLAB 스택이라 직결 불가. 아이디어 이식: **Hermite 보간 · consistent IC · LSA 상관분석** 3개를 PyBaMM+PyBOP 파이프라인에 도입 가치.

### 1.4 cideMOD — Python/AGPL-3.0 ([GitHub](https://github.com/cidetec-energy-storage/cideMOD))

- **언어/라이선스**: Python + **FEniCSx (dolfinx 0.7)** + multiphenicsx + Gmsh + PETSc. **AGPL-3.0** (강한 copyleft — 상용 주의).
- **Model scope**: ⭐ **Pseudo X-Dimensional (PXD)** — DFN P2D를 **P3D/P4D**로 확장(실제 3D 셀 지오메트리, 탭 위치 자유). 열 + SEI 성장 + LAM. 복수 활물질.
- **지배 방정식**: 표준 DFN + 에너지 방정식(ohmic/반응/reversible heat) + SEI: EC-solvent SEI 두께 ODE 형태.
- **이산화**: **FEM (Lagrange)** 매크로 + **Legendre 스펙트럴(3-4 모드)** pseudo-r. Backward Euler 시간적분, adaptive Δt.
- **솔버**: **PETSc SNES** 묵시적 Newton + Krylov (preconditioned). FEniCS UFL form 컴파일러로 어셈블리.
- **AD**: **UFL symbolic** — `ufl.derivative`로 Jacobian 자동 유도.
- **파라미터 추정**: 없음. adjoint 프레임워크 미제공.
- **성능**: P2D 싱글코어 ~10초; **P4D 50k 셀 ~1시간**.
- **I/O**: JSON dict + Gmsh .msh, XDMF/HDF5 출력 (ParaView).
- **커뮤니티**: ★38, v2.0.0 (2023-08). Cidetec 소규모 팀.
- **차별점**: ⭐ **유일한 실 3D/4D 셀 지오메트리 OSS**. 탭 위치 / 불규칙 mesh / 진짜 FEM.
- **BDT 연계**: AGPL + FEniCS 스택 부담 큼. 차용 대상: (a) P4D 기하 지오메트리 효과 검증용 외부 실행, (b) FEM+Spectral 혼합 이산화 아이디어.

### 1.5 PETLION.jl — Julia/MIT ([GitHub](https://github.com/MarcBerliner/PETLION.jl), [JES 2021](https://iopscience.iop.org/article/10.1149/1945-7111/ac201c))

- **언어/라이선스**: Julia, **MIT**. Berliner(MIT)/CMU.
- **Model scope**: 표준 P2D (1D macro + pseudo-r) + 선택적 **lumped/1D thermal** + SEI aging. 3D/plating/cracking/mechanics 없음.
- **지배 방정식**: 표준 Newman DFN. **Marcus-Hush-Chidsey** 옵션. semi-explicit DAE.
- **이산화**: **FVM (x)** + **8차 FDM 또는 스펙트럴 collocation (r)**. N=10 × section → 341 DAE (301 diff + 40 algebraic).
- **솔버**: ⭐ **Sundials IDA + KLU sparse LU** (Julia Sundials.jl 경유). 4개 Julia stiff DAE 솔버 벤치마크에서 Rodas5/Rosenbrock23/Radau5 대비 **>10× 승리**.
- **AD**: ⭐ **심볼릭 Jacobian via ModelingToolkit.jl / Symbolics.jl** (5-10 μs/eval, zero-alloc) + ForwardDiff.jl (25-150 μs, greedy sparsity coloring).
- **파라미터 추정**: 내장 없음. ms 단위 forward 해가 외부 MCMC/최적화 loop에 trivial.
- **성능**: ⭐⭐⭐ **전체 1-C 방전 2.96 ms** (심볼릭). LIONSIMBA 191 ms 대비 **206×**, PyBaMM "fast" 113 ms 대비 **35×**. 총 메모리 ~1 MB. Thermal 1.1-1.3× 감속. GPU 없음.
- **I/O**: Julia struct / kwargs, 내장 chemistry(LCO/NMC/NCA), Solution 배열.
- **커뮤니티**: ★79, v1.0.6 (2025-03), 주로 단독 메인테이너. D3BATT 등 컨트롤 문헌에서 인용.
- **차별점**: ⭐⭐⭐ **P2D 속도의 끝판왕**. 심볼릭 희소 Jacobian + IDA-KLU + 타이트한 Julia. **MPC/실시간 컨트롤/외부-루프 피팅 최적**.
- **BDT 연계**: Julia 스택 장벽 있지만 PyJulia/juliacall로 Python 호출 가능. **MCMC 수천-만회 forward 필요 시 surrogate 대신 PETLION 직접 호출** 시나리오가 매력적.

### 1.6 BattMo.jl — Julia/MIT ([GitHub](https://github.com/BattMoTeam/BattMo.jl), [arXiv](https://arxiv.org/html/2512.17933))

- **언어/라이선스**: Julia + **[Jutul.jl](https://github.com/sintefmath/Jutul.jl)** (SINTEF multiphysics FV 프레임워크). **MIT**. EU Horizon 2020 다기관.
- **Model scope**: ⭐ **가장 광범위** — PXD (P2D/P3D pouch/P4D), **Li-ion + Na-ion**, 전기화학 + 열 + **SEI + Li plating + cracking + mechanics + hysteresis + multiphase**.
- **지배 방정식**: 전체 DFN + 열(Arrhenius) + SEI ODE + plating/cracking 부반응. **계산 그래프(computational graph)** — 노드=변수, 엣지=함수관계. Jutul이 그래프 순회로 residual/Jacobian 조립.
- **이산화**: **FVM on unstructured grids** (Jutul). **1D/2D/3D 통합 코드 경로** (coin-cell/jellyroll/pouch). Backward Euler.
- **솔버**: Jutul **fully-implicit Newton** + AD 잔차, 희소 선형해 (direct / Krylov+preconditioner, MRST-style stack).
- **AD**: ⭐⭐ **네이티브 forward-mode AD on sparse residual graph** + ⭐ **adjoint sensitivity** — gradient-based calibration 공식 지원.
- **파라미터 추정**: ⭐ **내장 adjoint-based parameter calibration** (arXiv 2512.17933).
- **성능**: 3D 확장 가능. PyBaMM 직접 비교 수치는 미공개.
- **I/O**: **JSON** 셀 파라미터(chen_2020, xu_2015 등), JSON 프로토콜/시뮬 설정, SimulationOutput dict, GLMakie 3D 뷰어.
- **문서**: Documenter.jl (battmo.org) — 3개 중 **최고 완성도**.
- **커뮤니티**: ★35, **1,587 커밋**, 다기관 팀 (SINTEF + BattMo consortium), Zenodo 10.5281/zenodo.17313586.
- **차별점**: ⭐ **미분가능 멀티피직스 + 1D↔3D 통합 + Na-ion + MATLAB/Julia/Python(PyBattMo)/웹 GUI 생태계**.
- **BDT 연계**: [PyBattMo](https://github.com/BattMoTeam/PyBattMo) Python 래퍼 존재 → BDT에서 subprocess로 호출 가능. Chen-2020 계열 JSON 파라미터가 PyBaMM과 관례 유사 → **파라미터 교차사용** 가능.

### 1.7 PyBOP — Python/BSD-3 ([GitHub](https://github.com/pybop-team/PyBOP), [JOSS](https://doi.org/10.21105/joss.07874))

- **언어/라이선스**: Python ≥3.10, **BSD-3**. JOSS 2025 (Planden et al.).
- **Model scope**: ⭐ PyBaMM/`scikit-fem`/ECM을 **감싸는 estimation + design optimisation** 프레임워크. 자체 물리 정의 없음.
- **지배 방정식**: PyBaMM 상속. PyBOP는 cost function 표현: RMSE, SSE, Gaussian/Student-t log-likelihood, MAP+prior, design cost (에너지/파워 gravimetric/volumetric), weighted/feature distance.
- **이산화**: PyBaMM 상속.
- **솔버 (forward)**: PyBaMM (CasADi / IDAKLU / JAX / scikits.odes).
- **파라미터 추정** ⭐⭐⭐: 두 계열.
  - **결정론적/최적화**: AdamW, gradient descent, iRProp+, Cuckoo, Random Search, Simulated Annealing + **PINTS 래퍼** (CMA-ES, XNES, SNES, PSO) + **SciPy** (minimize/differential_evolution/nonlinear constraints).
  - **베이지안 MCMC** (PINTS): **NUTS / HMC / DREAM / MALA / Emcee Hammer / Metropolis / Haario adaptive / Slice (doubling/stepout/rank-shrinking) / Population / Relativistic / DE-MCMC / Rao-Blackwell / Monomial-Gamma Hamiltonian**. 옵션 `ep-bolfi`로 likelihood-free.
  - **관측치**: time-domain V/I/T, GITT pulse, HPPC, **frequency-domain EIS** (`simple_eis.py`).
  - **감도 분석**: SALib (Sobol/Morris).
- **성능**: 공식 airspeed-velocity 대시보드 (pybop-bench).
- **I/O**: `pybop.Dataset`, BPX JSON, **PyProBE** (Neware/Basytec/Biologic/Maccor) 통합.
- **문서**: Sphinx + Colab + 다수 노트북 (ECM multi-pulse, pouch spatial ID, energy-based electrode design, MAP, MCMC, EIS, GITT).
- **커뮤니티**: ★193, 활발 (2026-04-13 커밋), JOSS 2025.
- **차별점**: **PyBaMM 생태계에서 유일한 본격적 estimation+design 프레임워크**. 25+ optimiser × 17+ sampler uniform API.
- **BDT 연계**: ⭐ **최우선 통합 후보**. 현재 BDT는 측정 V(t)/I(t)/Q만 제공 — PyBaMM forward + PyBOP estimation으로 셀별 파라미터 역추정 즉시 가능. PyProBE와의 파서 중복을 BDT가 흡수.

### 1.8 SLIDE — C++/BSD-3 ([GitHub](https://github.com/Battery-Intelligence-Lab/SLIDE))

- **언어/라이선스**: C++17, CMake. **BSD-3**. Oxford Battery Intelligence Lab (Howey/Reniers/Kumtepeli).
- **Model scope**: ⭐ **SPM + lumped thermal + 물리기반 열화 메뉴**. 대규모 사이클 시뮬레이션 특화.
- **지배 방정식**:
  - **Spectral SPM + eigenvalue transform**: `∂z_{2:N}/∂t = D_s(T) V^{-1} Λ V z + B̃ j(t)` — 상태행렬 대각화로 속도 ↑.
  - Butler-Volmer + Arrhenius.
  - 열화 메뉴 (ID 플래그로 토글):
    - **SEI**: Pinson&Bazant 2013 / Ning&Popov 2004 / Christensen&Newman 2005 / fitted variant.
    - **Surface cracking (CS)**: fatigue → 추가 SEI + 표면적 증가 + 확산계수 감소 (Dai stress model).
    - **LAM**: stress/cycle-driven 활물질 분율 감소.
    - **Li plating**: 가역/비가역 Tafel.
    - **SEI-porosity coupling**: Ashwin/Chung/Wang 2016.
- **이산화**: **Chebyshev 스펙트럴 collocation** (r방향, N≈5).
- **솔버**: 커스텀 explicit time-stepper (adaptive forward-Euler/RK-style). Tester-like CC/CV 제어 루프. **stiffness 일반성 포기 → 처리량 최적화**.
- **AD**: 없음.
- **파라미터 추정**: `Cell_SPM_fitting.cpp` + `src/optimisation/` — 열화 파라미터 피팅 harness (일반 inverse 아님).
- **성능**: ⭐⭐ **5000 1C-CC 사이클 < 1분**, +CV < 2분 (싱글 스레드). 100 1C 사이클 0.9초.
- **I/O**: CSV 출력, MATLAB .m 리더.
- **문서**: Jekyll/Doxygen site (완성도 높음) + PDF manual.
- **커뮤니티**: ★136, 2026-02-10 커밋, 주로 단독 메인테이너.
- **차별점**: **SPM+다양한 열화를 수천 사이클 스케일로 실행하는 유일 OSS**.
- **BDT 연계**: C++ 독립 바이너리로 실행 → CSV 출력 파싱. **장기 열화 시뮬레이션 보조 툴**로 외부 호출 후 BDT UI에 측정 vs 모델 오버레이 가능. 관련: [[NREL_SSC_수명모델_참고]].

### 1.9 formation-modeling — Python/MIT-ish ([GitHub](https://github.com/wengandrew/formation-modeling), [JES 2023](https://iopscience.iop.org/article/10.1149/1945-7111/aceffe))

- **언어/라이선스**: Python 3.8, NumPy/SciPy/Pandas, YAML. LICENSE 확인 필요.
- **Model scope**: ⭐ **포메이션 사이클 전용 0-D OCV-R + 2-species SEI**. Weng+Kim+Barai+Lee+Stefanopoulou (UMich).
- **지배 방정식**:
  - 열역학: 전극 SOH θ_n/θ_p 밸런스, `dQ_int`/`dQ_app` (Ah) 스텝, `OCV = U_p(θ_p) - U_n(θ_n)`.
  - 동역학: R0 + 병렬 R1C1 per electrode; CV 모드는 ZOH RC의 해석적 지수 해.
  - **Yang 2017 SEI**: reaction-limited + diffusion-limited, 2 species (inner dense / outer porous), 직렬 저항 형태 `D_SEI = (1/D_SEI1 + 1/D_SEI2)^{-1}`, 농도/두께 추적.
  - 팽창: 흑연(Kupper2018/Mohtat2020) + NMC(Mohtat2020), 가역/비가역 분리, SEI-성장-결합 boost.
  - 프로토콜: CHARGE_CC/CV, DISCHARGE_CC/CV, REST.
- **이산화**: **0-D ODE (lumped)**. dt=5s 균일.
- **솔버**: 커스텀 explicit 스테퍼 + ZOH RC 해석해. SciPy `optimize`는 피팅 전용.
- **AD**: 없음.
- **파라미터 추정**: 동봉 실험 데이터 (`diagnostic_test_cell_umbl2022feb_cell152064.csv`)로 k_SEI/D_SEI/ECM 피팅. **dV/dQ 툴 내장** (`src/dvdq.py`).
- **성능**: 0-D라 사실상 즉시.
- **I/O**: YAML config, CSV cycler.
- **커뮤니티**: ★16, 2025-11-10.
- **차별점**: ⭐ **포메이션 동역학에 특화된 유일한 OSS**. Li-inventory 장부, 2-species SEI, dV/dQ 호환 전극 밸런스.
- **BDT 연계**: **매우 가까운 matching** — BDT 사이클 데이터 중 **포메이션 구간 해석** 확장 시 차용 1순위. dV/dQ 로직(`src/dvdq.py`)과 전극 밸런스 수식을 BDT 사이클 탭에 이식 가능.

---

## 2. PINN 계열

### 2.1 PINN-Battery-Prognostics (Wen 2024) — PyTorch/License 미명시 ([GitHub](https://github.com/WenPengfei0823/PINN-Battery-Prognostics))

- **언어**: PyTorch + MATLAB 전처리. ⚠️ **LICENSE 파일 없음** — 법적 재배포 모호.
- **문제**: **Prognostics (SOH/RUL)** — 사이클 단위, 전기화학 없음.
- **네트워크**: 평이한 MLP (layers ∈ {2,4,6,8,10} × neurons ∈ {8..128}).
- **물리**: **Verhulst 로지스틱 fade ODE** `dU/dt = r·U·(1 − U/K) + C` (learnable r,K,C) + **DeepHPM 브랜치** (2nd MLP가 fade dynamics 자체를 학습).
- **손실**: 3 모드
  - Baseline: MSE only
  - Sum: `L_U + L_F + L_Ft` (F = ODE residual)
  - **AdpBal**: Kendall-Gal 2018 uncertainty weighting `exp(-σ)L + σ` (learnable log-σ)
- **학습**: Adam + StepLR, L-BFGS **없음**.
- **Hard IC/BC**: 해당 없음 (0-D).
- **AD**: PyTorch `torch.autograd.grad(create_graph=True, retain_graph=True)` 2차 도함수.
- **Dataset**: Severson 2019 LFP/graphite (`SeversonBattery.mat`, 124 cells).
- **파라미터 추론**: Point estimate only (gradient descent on log-params).
- **성능**: RMSE 개선 (IEEE TIV 2024). 솔버 속도 X — 대체할 PDE 솔버 없음.
- **문서/커뮤니티**: ★277, 2024-09, 단일 저자.
- **차별점**: **유일하게 prognostics/RUL 목표 + DeepHPM**(ODE discovery).
- **BDT 연계**: ⭐⭐ **BDT 현재 범위(사이클 fade)와 직접 매치**. PyTorch 네이티브 → 포팅 쉬움. 단, **라이선스 부재**로 복사 재사용 블로커. 아이디어만 이식.

### 2.2 PINN-SPM-fast-prototyping (CIDETEC 2023) — TF/**AGPL-3.0** ([GitHub](https://github.com/cidetec-energy-storage/PINN-SPM-fast-prototyping))

- **언어/라이선스**: TensorFlow 2.x + Keras, **AGPL-3.0** (강한 copyleft).
- **문제**: SPM **forward surrogate**, 설계변수 sweep (thickness, porosity, C-rate).
- **네트워크**: 전극별 Keras SavedModel (`SPM NE/`, `SPM PE/`). 입력 `(t_norm, r_norm, bc_norm, t_max_norm)`.
- **물리**: 구형 Fick + r=Rs Neumann (`-D_s ∂c/∂r = j/(a_s F)`) + r=0 symmetry. **BV와 OCV는 NN 밖에서 후처리** (OCV 테이블 `scipy.interp1d` + `η = (2RT/F)arcsinh(...)`).
- **손실**: 공개 코드에 명시 없음 (pretrained 가중치만 배포).
- **학습**: 미공개.
- **Hard IC**: **Output surgery** — NN이 `x̄ = x - x_0` 예측 → `x = x̄ + x_0`로 IC 자동.
- **AD**: TF GradientTape.
- **Dataset**: 전부 합성 (NMC811 | Gr-Si, L∈[50,200]μm, ε∈[0.2,0.6], C∈[1,3]).
- **파라미터 추론**: 없음. surrogate sweep을 외부 최적화에 제공.
- **커뮤니티**: ★22, 2024-04-30.
- **차별점**: **설계변수 parametric NN** (구조가 IP 전략 반영). BV+OCV가 NN 외부 → PyBaMM SPM과 호환성 높음.
- **BDT 연계**: ⚠️ **AGPL + TF 스택 + 문서 부재**로 실사용 제약. 아키텍처 아이디어 (NN은 확산만, BV/OCV는 analytical)만 차용.

### 2.3 PINNSTRIPES (NREL Hassanaly 2024) — TF/**BSD-3** ([GitHub](https://github.com/NatLabRockies/PINNSTRIPES), vault [[PINNSTRIPES_NREL]])

> 기존 vault 분석 존재 — 여기서는 다른 2개와 비교 축에서만 재기술.

- **언어/라이선스**: Python 3.11 + TF 2.16 + `tf2jax` + **NumPyro**. **BSD-3**. NREL 공식.
- **문제**: **SPM (Part I) + P2D (Part II) forward surrogate + Bayesian calibration**.
- **네트워크**: 설정 가능 — split/merged, FC/residual/**gradient-pathology block** (Wang 2020), activations: tanh/swish/sigmoid/elu/selu/gelu. **Hierarchical multi-fidelity (HNN/HNNTIME)**.
- **물리**: 전 SPM + P2D — Fick particle, Butler-Volmer (`LINEARIZE_J`, `EXP_LIMITER` 안정화), electrolyte potential, solid potential, reference (anode), OCP 단조 다항식.
- **손실**: 4항 `L = α₀L_int + α₁L_bound + α₂L_data + α₃L_reg`, 3가지 가중치 전략:
  - **Static** (`loss_fn_lbfgs`)
  - ⭐ **Self-adaptive per-collocation weights** (`loss_fn_dynamicAttention_tensor`) — minimax 게임 (weights maximize loss, net minimizes).
  - ⭐ **Annealing (gradient-norm rebalancing)** (`loss_fn_annealing`, Wang 2021).
- **학습**: ⭐⭐ **2-stage Adam → L-BFGS** (3000→10000 epochs, threshold gating) + **GRADUAL_TIME curriculum**.
- **Hard IC**: ⭐ `y(t) = y₀ + (1 − exp(−t/τ))·NN(t,...)` (τ=HARD_IC_TIMESCALE).
- **AD**: **persistent GradientTape** 2차 r도함수 + nested tapes for 가중치.
- **Dataset**: self-generated FD SPM 적분기. Data-free 학습 가능.
- **파라미터 추론**: ⭐⭐⭐ **NumPyro NUTS/HMC Bayesian calibration**. `i0_a ∈ [0.5,4]`, `ds_c ∈ [1,10]`. Bisectional σ 탐색.
- **성능**: forward ~ms (FD 대비 수천 배), forward error <1%.
- **문서/커뮤니티**: ★62, 2025-12-10 활발, CI/test suite, 2편 JES 논문.
- **차별점**: **이 3개 중 가장 완성도 높음**. SPM+P2D 모두 + Bayesian 폐루프 + self-adaptive/annealing/curriculum/hard-IC 전체 패키지.
- **BDT 연계** (기존 [[PINNSTRIPES_NREL]]에 상세): PyBaMM 데이터 생성기 + PINNSTRIPES surrogate 템플릿 + BDT 실측 data-loss + NumPyro MCMC → **셀별 파라미터 역추정 폐루프**.

---

## 3. MD 계열

### 3.1 moleculer-db — ⚠️ **오인 링크**

`https://github.com/moleculerjs/moleculer-db` 는 **Node.js Moleculer microservice 프레임워크의 DB addon**이다. MongoDB/Mongoose/Sequelize 어댑터. 배터리 MD와 **무관**. "moleculer"는 JavaScript 말장난.

**실제 배터리 MD 표준 후보** (필요 시 대체):
- **LAMMPS** — 고전 MD 표준, 전해질/폴리머/고체전해질. ReaxFF로 SEI 반응.
- **OpenMM** — Python/GPU, 3.2로 연결.
- **GROMACS** — 액체 전해질/폴리머.
- **ASE** — DFT/MD glue.
- **i-PI** — 경로적분 MD (Li 고체 내 확산 양자효과).
- **pymatgen** — 전극 재료 구조/물성.
- **RDKit + CP2K/VASP** — cheminformatics + AIMD (SEI 분해 경로).

### 3.2 openmmtools — Python/MIT ([GitHub](https://github.com/choderalab/openmmtools))

- **언어/라이선스**: Python (C++/CUDA OpenMM 래핑). **MIT**. Chodera lab (MSKCC).
- **Scope**: OpenMM 확장 toolkit — **alchemy** (FEP/TI), **integrators** (Langevin 패밀리), **MCMC** 이동, **REMD/SAMS**, **testsystems**, NCMC, NetCDF storage.
- **지배 물리**: Newton EOM + Langevin 열역학 (symplectic Verlet/leapfrog + Trotter 분할). 힘장은 OpenMM 상속: AMBER/CHARMM/CGenFF/GAFF/OPLS-AA/Amoeba.
- **Integrators**: `LangevinIntegrator`, `VVVRIntegrator`, **`GeodesicBAOABIntegrator` (g-BAOAB, 평형 추천)**, `GHMCIntegrator`, `NonequilibriumLangevinIntegrator`, `AlchemicalNonequilibriumLangevinIntegrator`, `MTSIntegrator`, `VelocityVerletIntegrator`, `NoseHooverChainVelocityVerletIntegrator`, `MetropolisMonteCarloIntegrator`, `HMCIntegrator`.
- **Discretization**: Δt 1-4 fs, SHAKE/RATTLE/SETTLE 제약.
- **Solver**: PME (long-range electrostatics), LJ cutoff, 주기 BC, MC barostat (NPT).
- **AD/자동미분**: 해당 없음 (MD는 forward only).
- **성능**: ⭐⭐ GPU (CUDA/OpenCL) — 소형 단백질 수화 시스템 100-500 ns/day.
- **배터리 적용성**: ⚠️ Chodera lab은 biomolecular FEP 중심. 배터리 전해질(LiPF6/LiTFSI/LiFSI in EC/EMC/DMC/DME)은 **가능하지만** 표준 문헌은 LAMMPS/GROMACS 위주. openmmtools 알케미로 **Li+ 용매화 자유에너지** 계산 가능 → 전해질 설계.
- **문서/커뮤니티**: ReadTheDocs, Zenodo DOI, v0.26.0 (2026-01-07), ~14명 core contributors.
- **BDT 연계**: **scale 부정합** (Å-nm/fs-ns vs μm-mm/ms-hours). 올바른 다리는 **파라미터 공급**:
  - MD Green-Kubo/Einstein → `D_Li`, `D_solvent`, **`κ(c,T)`**, **`t+`** 추출 → BDT 연속체 파라미터 테이블 주입.
  - Alchemy → 전극 계면 exchange-current 보정.
  - 런타임 의존성 불필요 — **offline CSV 파이프라인**.

---

## 4. 축별 비교 매트릭스

### 4.1 지배 방정식 / Scope

| 프로젝트 | SPM | SPMe | DFN/P2D | 3D/P4D | 열 | SEI | Plating | Cracking | LAM | Phase-field | Na-ion |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **PyBaMM** | ✅ | ✅ | ✅ | 부분(3D 열) | ✅ | ✅(4종) | ✅ | ✅ | ✅ | ❌ | 부분 |
| **MPET** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⭐ Cahn-Hilliard | ❌ |
| **COBRAPRO** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **cideMOD** | ❌ | ❌ | ✅ | ⭐ P3D/P4D | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **PETLION.jl** | ❌ | ❌ | ✅ | ❌ | ✅ lumped/1D | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **BattMo.jl** | ❌ | ❌ | ✅ | ⭐ P4D | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ⭐ |
| **PyBOP** | (PyBaMM) | (PyBaMM) | (PyBaMM) | (scikit-fem) | (PyBaMM) | (PyBaMM) | (PyBaMM) | (PyBaMM) | (PyBaMM) | ❌ | (PyBaMM) |
| **SLIDE** | ✅ | ❌ | ❌ | ❌ | ✅ lumped | ⭐ 4종 | ✅ | ⭐ | ✅ | ❌ | ❌ |
| **formation** | ❌ (0-D) | ❌ | ❌ | ❌ | ❌ | ⭐ 2-species Yang | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Wen PINN** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ (fade ODE) | ❌ | ❌ | ❌ | ❌ | ❌ |
| **CIDETEC PINN** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **PINNSTRIPES** | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **openmmtools** | MD only | — | — | — | — | 원소 단위 | — | — | — | — | — |

### 4.2 이산화

| 프로젝트 | x/macro | r/particle | 시간 |
|---|---|---|---|
| PyBaMM | FVM (기본) / Chebyshev | FVM / spectral | implicit (IDAKLU BDF) |
| MPET | FV 1D | FV (Cahn-Hilliard 2nd order) | IDAS BDF |
| COBRAPRO | **FVM + Hermite 보간** | **Hermite** | IDAS BDF |
| cideMOD | **FEM (Lagrange)** | **Legendre spectral (3-4 모드)** | Backward Euler adaptive |
| PETLION.jl | **FVM** | **8차 FDM 또는 spectral collocation** | IDA BDF |
| BattMo.jl | **FVM on unstructured (1D/2D/3D 통합)** | FV | Backward Euler + Newton |
| SLIDE | — (SPM, 1-particle) | **Chebyshev spectral + eigenvalue transform** | explicit adaptive |
| formation | — (0-D) | — | explicit dt=5s + 해석 ZOH RC |
| PINNSTRIPES | mesh-free (collocation) | mesh-free | 정적 + GRADUAL_TIME curriculum |
| CIDETEC PINN | mesh-free | mesh-free | 정적 |
| Wen PINN | — (0-D) | — | — (cycle index) |

### 4.3 솔버 / 선형대수

| 프로젝트 | 시간적분기 | 선형솔버 | stiffness | 언어 바인딩 |
|---|---|---|---|---|
| PyBaMM | **IDAKLU (SUNDIALS BDF)** / CasADi / JAX / SciPy | KLU sparse LU | implicit | C++ pybind |
| MPET | IDAS (daetools) | SuperLU | implicit | Python |
| COBRAPRO | IDAS | KLU via mex | implicit | MATLAB mex |
| cideMOD | PETSc SNES Newton | Krylov + precond | implicit | Python/C++ |
| PETLION.jl | **IDA + KLU** (Sundials.jl) | KLU sparse | implicit | Julia native |
| BattMo.jl | Jutul Newton | sparse direct / Krylov | implicit | Julia native |
| SLIDE | **explicit adaptive FE/RK** | — | ❌ (특화 설계) | C++ native |
| formation | explicit + ZOH RC | — | — | Python |
| PINNSTRIPES | 해결 없음 (NN) | — | — | TF |

### 4.4 자동미분 (AD)

| 프로젝트 | 백엔드 | 용도 |
|---|---|---|
| PyBaMM | **CasADi 심볼릭** + **JAX** | Jacobian 희소, 파라미터 감도, 경사기반 최적화 |
| MPET | daetools 심볼릭 | Jacobian (내부만) |
| COBRAPRO | **CasADi 심볼릭** | Jacobian + LSA |
| cideMOD | **UFL 심볼릭** (FEniCS) | Jacobian |
| PETLION.jl | **Symbolics.jl/ModelingToolkit.jl** + **ForwardDiff.jl** | Jacobian, 감도 |
| BattMo.jl | ⭐ **Jutul 네이티브 forward AD + adjoint** | Jacobian + **gradient-based calibration** |
| SLIDE | — | — |
| formation | — | — |
| Wen PINN | **PyTorch autograd** | 2차 도함수 (F_t) |
| CIDETEC PINN | TF GradientTape | 물리 잔차 |
| PINNSTRIPES | **persistent GradientTape + nested** | 2차 r도함수 + minimax self-adaptive 가중치 |

### 4.5 파라미터 추정 생태계

| 프로젝트 | 내장 옵티마이저 | 내장 MCMC | 감도 분석 | 식별성 |
|---|---|---|---|---|
| PyBaMM | ❌ (PyBOP) | ❌ (PyBOP) | InputParameter | ❌ |
| MPET | ❌ | ❌ | ❌ | ❌ |
| COBRAPRO | ⭐ **PSO/GA/fmincon** | ❌ | ⭐ LSA | ⭐ **LSA+상관분석** |
| cideMOD | ❌ | ❌ | ❌ | ❌ |
| PETLION.jl | ❌ | ❌ | ❌ (ms solve로 외부 루프) | ❌ |
| BattMo.jl | ⭐ **adjoint-based calibration** | ❌ | adjoint | ❌ |
| PyBOP | ⭐⭐⭐ **25+ (AdamW/CMA-ES/PSO/XNES/SNES/SciPy...)** | ⭐⭐⭐ **17 PINTS (NUTS/HMC/DREAM/MALA/Emcee...)** | ⭐ SALib (Sobol/Morris) | prior-based |
| SLIDE | 열화 fitting harness | ❌ | ❌ | ❌ |
| formation | SciPy `optimize` (연구 companion) | ❌ | ❌ | ❌ |
| Wen PINN | Adam (point est.) | ❌ (uncertainty weight 근사) | ❌ | ❌ |
| CIDETEC PINN | ❌ | ❌ | ❌ | ❌ |
| PINNSTRIPES | ⭐ **NumPyro NUTS/HMC** | ⭐⭐ | ❌ | bisectional σ |

### 4.6 라이선스 · 언어 · 성능 · 활동도

| 프로젝트 | 라이선스 | 언어 | 속도 헤드라인 | ★ | 최근 커밋 |
|---|---|---|---|---|---|
| PyBaMM | **BSD-3** | Python | DFN 1C ~<1s | 1,539 | 2026-04-17 |
| MPET | MIT-ish | Python | 클러스터용 | 39 | 2024-12-17 |
| COBRAPRO | **MIT** | MATLAB | ~1000× DEARLIBS | 27 | 2025-09-15 |
| cideMOD | **AGPL-3.0** ⚠️ | Python+FEniCSx | P2D 10s / P4D 1h | 38 | 2023-08 |
| PETLION.jl | **MIT** | Julia | ⭐ **2.96 ms / discharge (206× LIONSIMBA)** | 79 | 2025-03 |
| BattMo.jl | **MIT** | Julia | (수치 미공개) | 35 | 활발 (1587 커밋) |
| PyBOP | **BSD-3** | Python | airspeed-velocity 대시보드 | 193 | 2026-04-13 |
| SLIDE | **BSD-3** | C++ | ⭐ **5000 cycles < 1분** | 136 | 2026-02-10 |
| formation | (확인 필요) | Python | 0-D 즉시 | 16 | 2025-11-10 |
| Wen PINN | ⚠️ **LICENSE 없음** | PyTorch | forward ms | 277 | 2024-09-05 |
| CIDETEC PINN | ⚠️ **AGPL-3.0** | TF/Keras | (미공개) | 22 | 2024-04-30 |
| PINNSTRIPES | **BSD-3** | TF 2.16 | forward ~ms, err<1% | 62 | 2025-12-10 |
| openmmtools | **MIT** | Python/OpenMM | 100-500 ns/day GPU | — | 2026-01-07 |

---

## 5. 세 관점에서의 심층 논의

### 5.1 전기화학 관점

- **Newman DFN 정식이 표준**: PyBaMM/MPET/COBRAPRO/cideMOD/PETLION/BattMo 전부 $\varepsilon\partial c_e/\partial t + (1-t^+)/F\cdot j = \partial_x(D_e^{eff}\partial_x c_e)$, BV kinetics, concentrated-solution 전해질을 공유.
- **경계 확장 3방향**:
  1. **반응 동역학**: MPET만이 **CIET**(Bazant coupled ion-electron transfer) + Marcus/MHC 내장. PETLION은 MHC만. 나머지는 BV 기본.
  2. **상분리 열역학**: MPET 유일의 **Cahn-Hilliard** (LFP/graphite staging 필수).
  3. **다차원 셀 기하**: cideMOD(P3D/P4D FEM) + BattMo(Jutul FVM 1D/2D/3D). 탭 배치·냉각 효과 해석 가능.
- **열화 물리의 성숙도**: BattMo > PyBaMM ≈ SLIDE > cideMOD > 나머지. SLIDE는 열화 메뉴(SEI 4종·CS·LAM·plating)가 특히 풍부하지만 SPM 한정.
- **포메이션 전용**: formation-modeling만 2-species Yang 2017 SEI + 전극 밸런스 + 팽창 결합을 포메이션 프로토콜 수준으로 모델링.

### 5.2 수치해석 관점

- **DAE vs ODE**: P2D는 전형적 **index-1 DAE**. 초기조건 consistency가 critical — COBRAPRO의 공헌이 여기에 집중.
- **시간적분기**:
  - **SUNDIALS IDA(S) + KLU**가 오픈소스 표준 (PyBaMM/MPET/COBRAPRO/PETLION). BDF variable-order.
  - cideMOD는 Newton + Backward Euler (FEM 관례).
  - BattMo는 Jutul의 MRST-style fully implicit.
  - **SLIDE는 예외** — explicit 적응형 시간 스텝 + tester-like CC/CV 제어 루프. stiffness 일반성을 버린 대가로 throughput.
- **이산화 공간**:
  - **FVM이 지배적** (PyBaMM/MPET/COBRAPRO/PETLION/BattMo). 보존 특성.
  - **FEM**은 cideMOD 유일 — 3D geometry 이득.
  - **Spectral**: PyBaMM(Chebyshev 옵션) / PETLION(r 8차 FDM 또는 spectral) / SLIDE(Chebyshev + eigenvalue transform) / cideMOD(Legendre r). r 방향에서 stiff 구배를 적은 점수로 처리.
- **희소 Jacobian + AD**: PETLION.jl의 **ModelingToolkit 심볼릭 + greedy sparsity coloring**가 속도 기록(2.96 ms)의 핵심. BattMo.jl의 **Jutul adjoint**는 gradient-based calibration의 구조적 기반.
- **PINN 수치해석**:
  - **Hard-IC ansatz** `y(t) = y₀ + (1 − exp(−t/τ))·NN` (PINNSTRIPES) vs **output surgery** `x = x̄ + x_0` (CIDETEC) — 동등 효과.
  - **Self-adaptive collocation weights** (PINNSTRIPES minimax)와 **annealing** (grad-norm rebalancing)이 stiff PDE의 loss balancing 최첨단.
  - **GRADUAL_TIME curriculum** — 시간 도메인 점진 확대로 long-horizon 학습 안정화.
  - 2차 도함수(구형 Fick)는 **persistent GradientTape**로 메모리 최적.

### 5.3 코딩 관점

- **API 설계 비교**:
  - PyBaMM: **Expression Tree 심볼릭** — 수식 그대로 작성, Discretisation이 변환. 모델-이산화-솔버 관심사 분리의 정석.
  - BattMo: **computational graph (노드=변수, 엣지=함수)** — Jutul의 엔진이 순회하며 residual/Jacobian 조립.
  - MPET: **daetools 모델그래프** — 오퍼레이터 오버로드.
  - COBRAPRO: **MATLAB 절차적** — 직접 residual/Jacobian 작성.
  - PETLION.jl: **ModelingToolkit 심볼릭** — 선언적 + 심볼 희소 Jacobian.
  - cideMOD: **FEniCS UFL** — `ufl.derivative`로 대수적 Jacobian.
- **확장성**: PyBaMM 서브모델 플러그인 > BattMo(그래프 노드) > MPET(반응 메뉴) > PETLION(정형 P2D) > COBRAPRO/cideMOD(수정 코스트 큼).
- **생태계**: PyBaMM이 독보적 (**PyBOP / liionpack / pybamm-eis / pybamm-cookiecutter / BPX**). BattMo도 가족 (**MATLAB core / PyBattMo / 웹 GUI `app.batterymodel.com`**).
- **배포/라이선스 주의**: **cideMOD와 CIDETEC PINN은 AGPL** — 사내/상용 상품에 직접 포함 시 copyleft 리스크. BDT가 서비스로 노출되는 경우 특히 주의.

---

## 6. BDT 관점 통합 전략

> BDT = **PyQt6 + PyBaMM + NumPy/SciPy + Pandas** 중심의 사이클 분석/시뮬 도구.
> 프로젝트별 "차용 vs 래퍼 vs 아이디어" 판단.

| 프로젝트 | 통합 난이도 | 권고 |
|---|---|---|
| **PyBaMM** | N/A | 이미 백엔드 |
| **PyBOP** | ⭐⭐⭐ 낮음 | **즉시 도입**. BSD-3 Python 네이티브. BDT 측정 데이터 → PyBaMM forward + PyBOP CMA-ES/MCMC로 셀별 파라미터 역추정 탭 추가. |
| **PETLION.jl** | ⭐⭐ 중 | ★ **MCMC 수천 회 forward 필요 시 subprocess**. juliacall/PyJulia. surrogate 대안 고려. |
| **BattMo.jl / PyBattMo** | ⭐⭐ 중 | **P3D/P4D 지오메트리 분석 필요 시** subprocess. JSON 파라미터 PyBaMM과 교차. adjoint calibration 참고. |
| **COBRAPRO** | ⭐ 낮음 (아이디어) | MATLAB 의존 → 직결 X. **Hermite 보간 / consistent IC / LSA+상관 식별성 분석** 3개 아이디어 이식. |
| **cideMOD** | ⚠️ AGPL 장벽 | 상용 BDT에 직접 포함 X. 3D geometry 요구 시 독립 실행 + 결과 import. |
| **MPET** | ⭐ 낮음 (특수 용도) | LFP/graphite staging 해석 요구 시만. phase-field 파라미터 추출 후 PyBaMM 확장. |
| **SLIDE** | ⭐⭐ 중 (C++ 바이너리) | **장기 열화 시뮬** 요구 시 subprocess → CSV → BDT UI 오버레이. NREL SSC와 함께 관련: [[NREL_SSC_수명모델_참고]]. |
| **formation-modeling** | ⭐⭐⭐ 낮음 (아이디어) | ★ **포메이션 사이클 분석 확장 시 차용 1순위**. 0-D OCV-R + 2-species SEI + dV/dQ 로직을 BDT 사이클 탭에 이식. |
| **PINNSTRIPES** | ⭐⭐ 중 (TF 스택) | ★ **Bayesian 파라미터 역추정 파이프라인**의 참조 구현. (a) TF subprocess or (b) tf2jax+NumPyro or (c) PyTorch 재구현 중 택1. 기존 vault [[PINNSTRIPES_NREL]] 전략 준수. |
| **Wen PINN** | ⚠️ LICENSE 없음 | 아이디어만 (Verhulst fade ODE + Kendall uncertainty weighting + DeepHPM). 복사 재사용은 블로커. |
| **CIDETEC PINN** | ⚠️ AGPL + TF + 미문서화 | 실사용 X. BV/OCV를 NN 밖으로 빼는 아키텍처만 참고. |
| **openmmtools** | ⭐⭐ 중 (scale 다리) | 직접 BDT에 포함 불필요. **MD → D_Li/κ/t+ 오프라인 CSV**로 PyBaMM 파라미터 파일에 주입하는 파이프라인. |

### 6.1 권고 실행 순서 (BDT 확장)

1. **PyBOP 통합 (Phase 1)**: 셀별 파라미터 역추정 탭 (CMA-ES + NUTS). BDT 측정 CSV → `pybop.Dataset` → `pybop.FittingProblem` → `Result`. 
2. **PETLION.jl subprocess 옵션 (Phase 2)**: MCMC 반복 성능 벤치마크. 충분히 빠르면 JL 직접, 아니면 surrogate.
3. **PINNSTRIPES 포팅 (Phase 3)**: PyBaMM 데이터 생성 → PyTorch PINN(PINNSTRIPES 손실 구조 이식) → Pyro MCMC. [[PINNSTRIPES_NREL]] 전략 그대로.
4. **Formation 탭 확장 (옵션)**: wengandrew/formation-modeling 수식을 BDT 포메이션 분석에 이식.
5. **열화 오버레이 (옵션)**: SLIDE subprocess 또는 NREL SSC 수명 모델 직접 구현으로 측정 vs 모델 fade overlay.
6. **3D geometry (장래)**: 필요 시 BattMo.jl subprocess 또는 cideMOD 독립 실행.
7. **MD 파라미터 공급 (장래)**: openmmtools/LAMMPS 외부 실험 결과 → BDT 전해질 파라미터 파일.

---

## 7. 결론

- **종합 플랫폼**: **PyBaMM**이 OSS P2D의 사실상 표준(물리 breadth + 생태계 + BSD-3 + NumFOCUS).
- **속도 특화**: **PETLION.jl** (2.96 ms/discharge, 206× LIONSIMBA). MCMC/MPC 등 수만 회 forward 시나리오 최강.
- **Multiphysics/미분가능**: **BattMo.jl** (adjoint, 1D/2D/3D 통합, Na-ion, 풍부한 물리).
- **파라미터 식별성**: **PyBOP**(estimation 생태계 폭) + **COBRAPRO**(DFN+식별성 통합).
- **특수 물리**: **MPET**(phase-field/CIET) · **cideMOD**(3D 지오메트리) · **SLIDE**(장기 열화) · **formation-modeling**(포메이션).
- **PINN 참조 구현**: **PINNSTRIPES** (BSD-3, SPM+P2D, Bayesian 폐루프, self-adaptive/annealing/curriculum/hard-IC 풀 패키지).
- **MD 다리**: **openmmtools**는 battery-specific은 아니지만 MIT/GPU/alchemy로 전해질 설계 후보. 실제로는 LAMMPS/GROMACS가 배터리 MD 문헌 표준.

BDT 중심으로 보면 **PyBaMM(현) → PyBOP(즉시) → PETLION(MCMC 가속 필요시) → PINNSTRIPES 구조 이식(역추정)** 이 가장 자연스러운 로드맵이다. AGPL(cideMOD, CIDETEC PINN)과 라이선스 미명시(Wen PINN) 프로젝트는 **아이디어 참고**에 한정.

---

## 8. 참고 링크

### P2D
- PyBaMM: https://github.com/pybamm-team/PyBaMM · https://pybamm.org
- MPET: https://github.com/TRI-AMDD/mpet · [Smith & Bazant JES 164 E3291 (2017)](https://iopscience.iop.org/article/10.1149/2.0171711jes)
- COBRAPRO: https://github.com/COBRAPROsimulator/COBRAPRO · [Ha & Onori JES 2024](https://iopscience.iop.org/article/10.1149/1945-7111/ad7292) · [JOSS arXiv 2404.10022](https://arxiv.org/abs/2404.10022)
- cideMOD: https://github.com/cidetec-energy-storage/cideMOD · https://cidemod.readthedocs.io · [JES 2022 doi:10.1149/1945-7111/ac91fb](https://iopscience.iop.org/article/10.1149/1945-7111/ac91fb)
- PETLION.jl: https://github.com/MarcBerliner/PETLION.jl · [Berliner et al. JES 2021](https://iopscience.iop.org/article/10.1149/1945-7111/ac201c)
- BattMo.jl: https://github.com/BattMoTeam/BattMo.jl · http://battmo.org/BattMo.jl/dev/ · [arXiv 2512.17933](https://arxiv.org/html/2512.17933) · https://app.batterymodel.com
- PyBOP: https://github.com/pybop-team/PyBOP · [JOSS 2025 doi:10.21105/joss.07874](https://doi.org/10.21105/joss.07874)
- SLIDE: https://github.com/Battery-Intelligence-Lab/SLIDE · https://Battery-Intelligence-Lab.github.io/SLIDE/ · [Reniers et al. JES 166 A3189 (2019)](https://doi.org/10.1149/2.0281914jes)
- formation-modeling: https://github.com/wengandrew/formation-modeling · [Weng et al. JES 170 090523 (2023)](https://iopscience.iop.org/article/10.1149/1945-7111/aceffe)

### PINN
- PINN-Battery-Prognostics: https://github.com/WenPengfei0823/PINN-Battery-Prognostics · [IEEE TIV 2024 doi:10.1109/TIV.2023.3315548](https://doi.org/10.1109/TIV.2023.3315548)
- PINN-SPM-fast-prototyping: https://github.com/cidetec-energy-storage/PINN-SPM-fast-prototyping
- PINNSTRIPES: https://github.com/NatLabRockies/PINNSTRIPES · [Hassanaly et al. JES 98 113103 (2024)](https://doi.org/10.1016/j.est.2024.113103) · [Part II 113104](https://doi.org/10.1016/j.est.2024.113104) · [arXiv 2312.17329](https://arxiv.org/abs/2312.17329)

### MD
- moleculer-db: https://github.com/moleculerjs/moleculer-db (⚠️ Node.js, 오인 링크)
- openmmtools: https://github.com/choderalab/openmmtools · https://openmmtools.readthedocs.io · https://openmm.org
- (대체) LAMMPS https://www.lammps.org · GROMACS https://www.gromacs.org · ASE https://wiki.fysik.dtu.dk/ase · pymatgen https://pymatgen.org

---

## 9. 관련 vault 노트

- [[PyBaMM_정리]] — PyBaMM 백엔드 기본
- [[Analysis_PyBaMM_ExpressionTree]] — Expression Tree 심볼릭 분석
- [[PyBaMM_Solve]] — IDAKLU/CasADi 솔버 (스텁, 보완 필요)
- [[SUNDIALS]] — IDAS/KLU (스텁, 보완 필요)
- [[PINNSTRIPES_NREL]] — PINNSTRIPES 상세
- [[phygnn_NREL]] — NREL Physics-Guided NN (이중 손실 구조 참고)
- [[PINN_기초]] · [[PINN_문헌정리]] · [[NREL_PINN]] · [[Knowledge_PINN_DeepONet]]
- [[NREL_SSC_수명모델_참고]] — NREL SSC NMC 열화 모델 참조 (SLIDE와 함께)
- [[Empirical_Degradation_Models]] — 경험 열화 모델
