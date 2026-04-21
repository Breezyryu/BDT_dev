---
relocated: 2026-04-22
source_vault: "docs/vault/01_Modeling_AI/PINNSTRIPES_NREL.md"
title: "PINNSTRIPES (NREL Li-ion PINN Surrogate)"
aliases:
  - PINNSTRIPES
  - NREL SPM PINN
  - Hassanaly PINN
tags:
  - Modeling_AI
  - PINN
  - NREL
  - SPM
  - P2D
  - reference
  - battery
type: reference
status: active
related:
  - "[[phygnn_NREL]]"
  - "[[NREL_PINN]]"
  - "[[PINN_기초]]"
  - "[[PINN_문헌정리]]"
  - "[[Knowledge_PINN_DeepONet]]"
  - "[[PyBaMM_정리]]"
  - "[[PyBaMM_Solve]]"
  - "[[Analysis_PyBaMM_ExpressionTree]]"
created: 2026-04-19
updated: 2026-04-19
source: "https://github.com/NatLabRockies/PINNSTRIPES"
---

# PINNSTRIPES — Li-ion SPM/P2D PINN Surrogate (NREL)

> [!abstract] 요약
> **"Physics-Informed Neural Network SurrogaTe for Rapidly Identifying Parameters in Energy Systems"**
> Hassanaly et al.(2024, *Journal of Energy Storage*) 논문의 공식 구현체로,
> Li-ion 배터리의 **SPM / Pseudo-2D (P2D)** 모델을 PINN으로 대체하여
> **매개변수 추정(parameter inference)** 속도를 극적으로 향상시키는 프레임워크.

- 저장소: https://github.com/NatLabRockies/PINNSTRIPES
- DOI (SW): 10.11578/dc.20231106.1
- 개발: NREL + DOE 자금 지원
- 분석일: 2026-04-19

---

## 1. 인용 논문

| Part | 제목 | 요지 |
|---|---|---|
| **Part I** | PINN surrogate of Li-ion battery models for parameter inference, Part I: Implementation and multi-fidelity hierarchies for the single-particle model (JES vol.98, 113103, 2024) | SPM PINN 구현 + multi-fidelity 계층 |
| **Part II** | 〃 Part II: Regularization and application of the pseudo-2D model (JES vol.98, 113104, 2024) | P2D 확장 + 정규화 전략 |

---

## 2. 전체 아키텍처

```
PINNSTRIPES/
├── pinn_spm_param/            # SPM PINN 코어
│   ├── main.py                # 학습 진입점
│   ├── repeat_sim.py          # 반복 시뮬레이션
│   ├── util/                  # 핵심 모듈 (아래 상세)
│   ├── integration_spm/       # implicit/explicit SPM 적분기 (데이터 생성)
│   ├── preProcess/            # makeDataset_spm.py 등 전처리
│   ├── postProcess/           # 결과 검증/시각화
│   └── tests/
└── BayesianCalibration_spm/   # MCMC/Bayesian 매개변수 추정
    ├── makeData.py
    └── cal_nosigma.py
```

### 3단계 워크플로우
1. **Pre-processing**: `integration_spm`의 implicit/explicit 적분기로 유한차분 SPM 해 생성 → 지도학습용 데이터
2. **PINN Training**: `main.py` (SGD → L-BFGS 2단계)
3. **Post-processing / Bayesian calibration**: 학습된 PINN을 **매개변수 추정 surrogate**로 활용

---

## 3. `util/` 핵심 모듈

### 물리 모델 (SPM 방정식)
| 파일 | 역할 |
|---|---|
| `spm.py` | SPM 전체 모델 (확산 계수 `D_s_a/D_s_c`, 교환전류, 초기조건 IC 클래스) |
| `spm_simpler.py` | 단순화 SPM (학습 초기/디버깅용) |
| `generateOCP.py` | Open Circuit Potential 곡선 생성 |
| `generateOCP_poly_mon.py` | 다항식 기반 단조 OCP |
| `uocp_cs.py` | 전극 전위 함수 |
| `thermo.py` | 열역학 상수 |

### 신경망 + 손실
| 파일 | 역할 |
|---|---|
| `myNN.py` | PINN 네트워크 정의 |
| `custom_activations.py` | 커스텀 활성함수 |
| `init_pinn.py` / `load_pinn.py` | 초기화 / 재로드 |
| `_losses.py` | **핵심**: 물리 잔차 + 경계/초기 + 데이터 + 정규화 손실 |
| `eager_lbfgs.py` | Eager 모드 L-BFGS (2단계 정제) |
| `forwardPass.py` | 순전파 |

### 유틸
| 파일 | 역할 |
|---|---|
| `dataTools.py`, `_rescale.py` | 데이터 처리 + 스케일링 |
| `tf_lineInterp.py` | TF용 선형 보간 (OCP 테이블 보간) |
| `scitools.py`, `argument.py`, `conditionalDecorator.py` | 과학/CLI/데코레이터 |
| `plotsUtil_batt.py` | 배터리 결과 시각화 |

---

## 4. PINN 학습 전략 (핵심 특징)

### 4.1 4-항 손실 구조
$$
\mathcal{L} = \alpha_0 \mathcal{L}_{\text{int}} + \alpha_1 \mathcal{L}_{\text{bnd}} + \alpha_2 \mathcal{L}_{\text{data}} + \alpha_3 \mathcal{L}_{\text{reg}}
$$

| 항 | 내용 | 배치 |
|---|---|---|
| **Interior** | PDE 잔차: 전류밀도(j_a, j_c) + 구면좌표 확산 PDE (∂c_s/∂t = (1/r²) ∂/∂r(r² D_s ∂c_s/∂r)) | `BATCH_SIZE_INT` |
| **Boundary** | `r=0` zero-flux + `r=r_max` flux-matching | `BATCH_SIZE_BOUND` |
| **Data** | 실측/수치해 대비 fidelity (potentials + concentrations) | `MAX_BATCH_SIZE_DATA` |
| **Regularization** | 정규화 (현재 플레이스홀더) | `BATCH_SIZE_REG` |

### 4.2 경계/초기조건 처리 — **Hybrid**
- **Hard IC**: 지수 시간 게이트 `(1 - exp(-t/τ))` 로 초기값 강제 주입
  → `HARD_IC_TIMESCALE` 옵션
- **Soft BC**: 경계 잔차를 손실로 가중 부과

### 4.3 `tf.GradientTape` 활용
```python
with tf.GradientTape(watch_accessed_variables=False,
                     persistent=True) as tape:
    tape.watch(r); tape.watch(t)
    # 1차 도함수
    # 2차 도함수 (구면 확산)
```
- **Persistent tape**로 ∂²/∂r² 등 고차 도함수 재사용
- **Selective watch**로 메모리 최적화

### 4.4 동적 가중치 조정
1. **Per-term weights**: `int_col_weights` 등 개별 스케일
2. **Annealing scheduler**: `loss_fn_lbfgs_annealing()` — 시간 의존 가중치
3. **Attention-based**: `loss_fn_dynamicAttention_tensor()` — 배치 크기 반영
4. **Global α**: `alpha[0..3]` 전역 균형

### 4.5 Collocation points
- `fixed`: 학습 전반 고정
- `random`: 에포크마다 재샘플
- `GRADUAL_TIME`: 시간 도메인을 점진적으로 확대하여 "시간 순방향" 학습

### 4.6 2-Stage 최적화
1. **SGD (Adam 등)** → 광범위 탐색
2. **L-BFGS (eager mode)** → 정밀 정제

---

## 5. Bayesian Calibration 모듈

- **용도**: 학습된 PINN을 MCMC 우도 계산의 빠른 surrogate로 활용
- **플로우**:
  1. `makeData.py`: 관측 데이터 생성
  2. `cal_nosigma.py`: bisectional hyperparameter search로 likelihood uncertainty 결정
  3. PINN 호출 → 매개변수 사후분포 추정

> SPM/P2D 풀 시뮬레이션을 MCMC 단계마다 돌리지 않고 **PINN으로 수천 배 가속**하는 것이 핵심 가치.

---

## 6. BDT / PyBaMM 관점 — 참고 포인트

> [!tip] PyBaMM 전기화학 시뮬레이션과의 접점
> PINNSTRIPES는 **PyBaMM을 직접 사용하지 않고 자체 적분기**를 쓰지만,
> 구조·손실·데이터 파이프라인이 **PyBaMM 대체/가속**에 그대로 적용 가능.

### (a) PyBaMM → PINN 데이터 파이프라인 교체
- `integration_spm/`의 자체 implicit/explicit 적분기를
  → **PyBaMM SPM/DFN 솔버 출력**으로 교체 가능
- `preProcess/makeDataset_spm.py`의 포맷만 맞추면 PyBaMM 결과를 지도학습 데이터로 사용 가능
- 관련: [[PyBaMM_Solve]], [[SUNDIALS]]

### (b) BDT 측정 데이터 직접 활용
- `_losses.py`의 **Data loss**에 실측 V(t), I(t) 넣으면
  → PyBaMM 파라미터(D_s, i_0, ε 등) 역추정 surrogate 구축 가능
- BDT의 사이클 데이터 (`df.NewData`의 Voltage/Current/Capacity)가 직접 입력원

### (c) Multi-fidelity 계층 (Part I 핵심 아이디어)
- 저해상도 PyBaMM 해 → **선학습** → 고해상도/실측 데이터로 fine-tune
- BDT의 다양한 C-rate 데이터 세트에 적합

### (d) `_losses.py` 패턴 차용
- 구면좌표 확산 PDE를 TF로 표현하는 코드는 **PyBaMM ExpressionTree를 PINN으로 포팅**할 때 직접 참고
- 관련: [[Analysis_PyBaMM_ExpressionTree]]

### (e) Hard IC 게이팅 `(1 - exp(-t/τ))`
- PINN이 초기조건에서 벗어나는 일반적 문제 해결
- 배터리 초기 SOC/OCV 제약이 강한 우리 도메인에 매우 유용

### (f) Bayesian Calibration 워크플로우 이식
- BDT + PyBaMM 조합으로 **셀별 파라미터 추정** 수행 시
  - PyBaMM으로 수치해 생성 → PINNSTRIPES 구조로 PINN 학습 → MCMC에서 surrogate 호출
  - 관련: [[PINN_기초]]의 inverse problem 섹션

---

## 7. 한계 및 도입 시 고려사항

| 항목 | 이슈 | 대응 |
|---|---|---|
| **프레임워크** | TensorFlow 2.x + eager L-BFGS | PyTorch 이식 시 `torch.autograd.functional` + SciPy `minimize` 조합 필요 |
| **SPM 한정** | DFN/P2D는 Part II에서 확장, 코드도 존재하나 복잡도 ↑ | 먼저 SPM으로 파일럿 |
| **PyBaMM 직결 부재** | 자체 적분기 사용 | `solution.y_sol`을 PINN 학습 데이터 포맷으로 변환 레이어 필요 |
| **OCP 테이블** | `tf_lineInterp.py`로 TF 보간 | PyBaMM의 `Interpolant`와 매핑 |
| **학습 비용** | SGD + L-BFGS 이중 학습 + 4-항 손실 | GPU 필수, 셀 형식별로 학습 필요 |
| **매개변수 수** | 추정할 파라미터 증가 시 네트워크 입력 차원 급증 | sensitivity로 주요 파라미터만 선별 |

---

## 8. 결론

- **가장 참고 가치 큰 요소**:
  1. ✅ **4-항 손실 설계** (interior / boundary / data / reg)
  2. ✅ **Hard IC 지수 게이트** `(1 - exp(-t/τ))`
  3. ✅ **Persistent `GradientTape`** 로 구면확산 2차 도함수
  4. ✅ **Dynamic attention + annealing** 가중치
  5. ✅ **2-stage (SGD → L-BFGS)** 최적화
  6. ✅ **PINN → Bayesian inference surrogate** 파이프라인

- **PyBaMM과의 결합 전략 (BDT 맥락)**:
  - PyBaMM = **데이터 생성기**
  - PINNSTRIPES 구조 = **surrogate 템플릿**
  - BDT 실측 데이터 = **fine-tune / data-loss source**
  - → 3자 결합으로 셀별 파라미터 추정 + 열화 파라미터 트래킹 가능

- **프레임워크 제약** (TF) 상 직접 포크보다 **아이디어 + 손실 구조 이식**이 현실적

---

## 9. 참고 링크

- GitHub: https://github.com/NatLabRockies/PINNSTRIPES
- Part I (JES 2024): Hassanaly et al., JES vol.98, 113103
- Part II (JES 2024): Hassanaly et al., JES vol.98, 113104
- 관련 vault 노트: [[phygnn_NREL]], [[NREL_PINN]], [[PINN_기초]], [[PyBaMM_정리]]

## 관련 노트

- [[phygnn_NREL]] — 같은 NREL 그룹의 일반 PGNN 프레임워크
- [[NREL_PINN]] — NREL PINN 연구 동향
- [[PINN_기초]] — PINN 기본 개념
- [[Knowledge_PINN_DeepONet]] — PINN/DeepONet 심화
- [[PyBaMM_정리]] — 데이터 생성 소스로 결합
- [[PyBaMM_Solve]] — 솔버 결과 포맷
- [[Analysis_PyBaMM_ExpressionTree]] — PDE 표현 비교 포인트
- [[수명_해석_방향]] — Bayesian calibration으로 열화 파라미터 추정 연결
