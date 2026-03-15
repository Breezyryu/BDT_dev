---
tags: [model, degradation, simulation, LCO, SiC, pouch]
up: [[Simulation & Modeling]]
status: review
created: 2026-01-27
---

# Empirical Degradation Models (LCO/SiC Pouch Cell)

## 1. 개요 (Overview)

본 문서는 [[LCO]]/[[Graphite]] 기반 3전극 파우치 셀(Pouch Cell)에서 관찰된 열화 거동을 설명하는 경험적(Empirical) 모델을 정리합니다.
PyBaMM 시뮬레이션 파라미터로 활용하기 위해 $E_a$(활성화 에너지)와 $k$(반응 속도 상수)를 도출하는 것이 목표입니다.

## 2. 주요 수식 (Key Equations)

### 2.1 아레니우스 관계식 (Temperature Dependence)

$$k(T) = A \cdot \exp\left(-\frac{E_a}{R T}\right)$$

- **$k(T)$**: 반응 속도 상수 (Reaction rate constant)
- **$E_a$**: 활성화 에너지 (Activation Energy)
- **$A$**: 빈도 인자 (Frequency Factor)

### 2.2 용량 감소 모델 (Calendar Aging)

$$Q_{loss} = B \cdot \exp\left(-\frac{E_a}{R T}\right) \cdot t^z$$

- **$Q_{loss}$**: 용량 감소율 (%)
- **$t$**: 시간 (days)
- **$z$**: 시간 지수 (주로 0.5 for SEI growth)

## 3. 실험 데이터 요약 (Experimental Data)

### 3.1 3전극 셀 데이터 (Reference Electrode)

- **음극 전위 상승**: 초기 0.05V $\to$ 열화 후 0.12V (Li plating risk 증가)
- **양극 임피던스**: Rct(Charge Transfer Resistance) 20% 증가

## 4. SiC 특화 보정 모델 (Proposed Model)

![[경험적모델.excalidraw|700]]
> *그림 1: 경험적 모델의 개념도 및 파라미터 상관관계*

실리콘 함량($w_{Si}$)과 방전 심도($DOD$), 그리고 파우치 셀의 압력($P$)을 고려한 통합 모델입니다.

### 4.1 용량 감소 (Total Capacity Loss)
2. **사이클**: 2 C-rate (0.5C, 1C) × 2 DOD (50, 100%)
3. **압력**: 지그(Jig) 가압력 가변 테스트 (옵션)

## 6. 결론
이 모델은 기존 Wang 모델에 **SiC 기계적 열화 항**을 추가하여, 고용량 파우치 셀의 비선형적 수명 거동을 예측할 수 있도록 설계되었습니다.

---
**References**
1. Wang et al. (2011), Cycle-life model for graphite-LiFePO4 cells.
2. NREL, Lithium-Ion Battery Life Model with Electrode Cracking.

## 📚 관련 노트 (Related Notes)
- **데이터 출처 (Data Source)**: [[SOP_Pouch_3Electrode_Cell]] (실험 데이터 생성 절차)
- **구현 (Implementation)**: [[Analysis_PyBaMM_ExpressionTree]] (PyBaMM 모델링 코드 분석)
- **상위 개념**: [[모델링 및 AI (Modeling & AI)]]

