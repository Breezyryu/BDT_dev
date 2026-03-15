---
title: "Prep_Electrochemical_Modeling_Interview"
tags: [Modeling_AI, 전기화학, 면접준비]
type: reference
status: active
related:
  - "[[03_Battery_Knowledge/Battery_Electrochemical_properties]]"
  - "[[03_Battery_Knowledge/Electrochemical_parameter]]"
  - "[[PyBaMM_정리]]"
created: 2026-01-27
updated: 2026-03-15
source: "origin/Prep_Electrochemical_Modeling_Interview.md"
---

# 전기화학 모델링 (P2D/ROM) 면접 대비

## 1. P2D 모델 핵심 (Deep Dive)

### 1.1 물리적 가정과 한계
- **Pseudo-2D의 의미**: 전극 두께($x$)와 입자 반경($r$) 두 차원만 고려.
    - $y, z$축 방향은 균일하다고 가정 (Homogenization).
    - **한계**: 코팅 불균일성, 입자 분포(PSD), 공극률 편차 무시 $\to$ 국부 열화 예측 불가.

### 1.2 Boundary Conditions (경계조건)
- **입자 중심 ($r=0$)**: $\frac{\partial c_s}{\partial r} = 0$ (대칭성).
- **입자 표면 ($r=R$)**: $-D_s \frac{\partial c_s}{\partial r} = \frac{j}{F}$ (플럭스 연속성).
- **Current Collector 접점**: $\nabla \phi_s = -I_{app}/\sigma_{eff}$ (전류 인가).

### 1.3 Convergence Issue 해결
- **고전류/저온 수렴성 악화 원인**:
    1. 전해질 고갈 ($c_e \to 0$ singularity).
    2. Butler-Volmer 식의 지수항 폭주 ($\exp(\eta)$).
- **해결책**:
    - Adaptive Time-stepping (급격한 변화 시 $\Delta t$ 축소).
    - Log-transfomation 변수 사용.
    - Damping Factor 적용.

## 2. Reduced Order Model (ROM)

### 2.1 필요성 (Why ROM?)
- **속도**: P2D (수 초~분) vs ROM (ms). BMS 실시간 탑재 필수.
- **활용**: MPC(모델 예측 제어), SOH 실시간 추정.

### 2.2 축소 기법 (Techniques)
- **SPM (Single Particle Model)**:
    - 전극 전체를 하나의 입자로 단순화. 전해질 저항 무시.
    - *보정*: SPMe (전해질 확산 항 추가).
- **ECM (Equivalent Circuit Model)**:
    - 전기적 등가회로 (R, C)로 근사. 빠르지만 물리적 의미 부족.
- **수학적 축소 (POD / Pade)**:
    - **POD**: 주요 모드(Eigenvalue)만 남기고 차원 축소 ($10^4 \to 10^1$).
    - **Pade Approximation**: 전달함수 $G(s)$의 분수 근사.

## 3. 실무 대응 답변 (Practical Q&A)

### Q. 파라미터 피팅은 어떻게?
- **Identifiability Analysis**: 민감도(Sensitivity)가 높은 파라미터 선별 (예: $D_s$, $k$).
- **Multi-step Fitting**:
    1. OCV (저율 방전) $\to$ 열역학 파라미터.
    2. GITT $\to$ 확산 계수.
    3. Pulse/EIS $\to$ 반응 속도 및 저항.

### Q. 모델 오차 발생 시 접근법?
1. **데이터 검증**: 온도/전류 센서 오차 확인.
2. **초기 조건**: SOC 불균형 확인.
3. **물리 현상 누락**: 부반응(Side reaction), 발열(Thermal) 고려 여부 체크.
