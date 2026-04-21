---
tags: [AI, deep_learning, PINN, battery/simulation, review]
up: [[Simulation & Modeling]]
status: stable
created: 2025-01-02
updated: 2026-01-27
aliase: [PINN Review, DeepONet Battery]
---

# Physics-Informed Deep Learning for Battery (PINN & DeepONet)

## 📌 요약 (Summary)
배터리 수명(SOH)과 잔존 수명(RUL) 예측을 위해 물리학 지식(Physics)과 데이터(Data)를 결합하는 **하이브리드 모델링** 기법에 대한 리뷰입니다. 특히 **PINN**(Physics-Informed Neural Network)과 **DeepONet**(Deep Operator Machine)을 결합하여 데이터 부족 문제와 일반화 성능 한계를 극복하는 방법을 다룹니다.

## 1. 배경 및 필요성

### 기존 방식의 한계
- **물리 기반 모델 (Physics-based)**: 전기화학 모델(DFN 등)은 정확하지만 연산 비용이 높고 파라미터 튜닝이 어려움.
- **데이터 기반 모델 (Data-driven)**: RNN/LSTM 등은 빠르지만 대량의 데이터가 필요하고 물리적 해석이 불가능(Black-box).

### PINN의 접근법
- 신경망 학습 손실 함수(Loss Function)에 **물리 방정식(PDE/ODE)의 잔차(Residual)**를 포함시킴.
- $$ Loss = Loss_{data} + \lambda \cdot Loss_{physics} $$
- **장점**: 적은 데이터로 학습 가능, 물리 법칙 준수(Mass Consevation 등), 외삽(Extrapolation) 성능 향상.

## 2. 핵심 아키텍처

### 2.1 PINN (Physics-Informed Neural Networks)
- **입력**: 시간($t$), 공간($x$), 변수($V, I, T$)
- **출력**: SOH, RUL, 내부 상태($c_s, \phi_s$)
- **학습 전략**:
    - **Data Loss**: 계측된 전압/전류 데이터와의 오차 최소화.
    - **Physics Loss**: 배터리 지배 방정식(Fick's Law, Butler-Volmer) 위배 정도 최소화.

### 2.2 DeepONet (Deep Operator Network)
함수 자체를 입력으로 받아 함수를 출력하는 모델. 가변적인 운전 조건(충방전 프로파일)에 대응하기 유리함.
- **Branch Net**: 센서 데이터(전압, 전류 곡선의 특징) 인코딩.
- **Trunk Net**: 조건 변수(온도, 시간 등) 인코딩.
- **결합**: 두 네트워크의 내적(Dot product)으로 결과 추정.

## 3. 방법론 (Methodology)

### 3.1 특징 추출 (Feature Extraction)
효율적인 학습을 위해 원본 데이터 대신 물리적 의미가 담긴 특징을 추출하여 입력.
- **DTDF (Distinct Time-Dependent Features)**:
    - 전압/전류 곡선의 평균, 분산, 기울기.
    - 증분 용량(IC, Incremental Capacity) 곡선의 Peak 위치 및 크기.

### 3.2 학습 전략 (Training Strategy)
1. **Surrogate Modeling**: 복잡한 물리 모델을 근사하는 가벼운 신경망(Surrogate)을 먼저 학습.
2. **Transfer Learning**: 다양한 온도/조건 데이터로 사전 학습 후, 타겟 데이터를 이용해 Fine-tuning.
3. **Loss Balancing**: 학습 초기에는 Data Loss에 집중하고, 점진적으로 Physics Loss 가중치($\lambda$)를 높여 물리적 정합성 확보.

## 4. 결론 및 시사점
- PINN은 배터리 내부 상태(리튬 농도 등)를 비파괴적으로 추정하는 가상 센서 역할을 할 수 있음.
- DeepONet 도입으로 다양한 운전 패턴에 대한 일반화 성능 확보 가능.
- **도전 과제**: 물리 제약이 걸린 비볼록(Non-convex) 최적화 문제의 수렴성 확보가 어려움.

---
## 📚 참고 문헌 (References)
1. **Nature Communications (2024)**: [Physics-informed neural network for lithium-ion battery degradation stable modeling](https://www.nature.com/articles/s41467-024-48779-z)
2. **Scientific Reports**: A framework for Li-ion battery prognosis based on hybrid Bayesian PINN.
3. **Review**: Hybrid Modeling of Lithium-Ion Battery (MDPI).
