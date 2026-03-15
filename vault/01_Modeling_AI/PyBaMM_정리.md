---
title: "PyBaMM 정리"
tags: [Modeling_AI, PyBaMM, 시뮬레이션]
type: model
status: active
related:
  - "[[PyBaMM_Solve]]"
  - "[[Analysis_PyBaMM_ExpressionTree]]"
  - "[[Phase1_패키지_구조_분석]]"
  - "[[Empirical_Degradation_Models]]"
  - "[[03_Battery_Knowledge/Electrochemical_parameter]]"
created: 2025-12-15
updated: 2026-03-15
source: "origin/Pybamm 정리.md"
---

# 개요
## 1.구성
1. 미분 방정식 시스템을 작성하고 풀기 위한 프레임워크
2. 배터리 모델 및 매개변수 라이브러리
3. 배터리 실험 시뮬레이션 및 결과 시각화를 위한 전문 도구

## 2. 시스템 아키텍처
- 모델 정의, 매개변수 관리, 이산화, 수치해석 솔버 등 기능별로 시스템 분리
![[Pasted image 20251218133334.png]]

### **2.1 Expression Tree System**
표현 트리 시스템은 수학적 표현을 기호로 표현하여 자동적인 미분, 기호 조작, 코드 생성을 가능하게 합니다.
![[Pasted image 20251014071725.png]]
### **2.2 Battery Model System**
- 리튬이온배터리 모델은 Doyle-Fuller-Newman(DFN), 단일 입자 모델(SPM_Single Particle Model) 등과 같은 물리 기반 배터리 모델을 제공
![[Pasted image 20251014070913.png]]
	- *DFN(Doyle-Fuller-Newman): 전극, 전해질, 고체 및 액체 상의 반응과 물질 전달을 포함하는 모델링*
	- *SPM(Single Particle Model): DFN 모델보다 단순화된 모델로, 각 전극 입자를 단일한 대표 입자로 가정하여 모델링
	- 모델별 컨셉![[Pasted image 20251014073259.png]]
		https://doi.org/10.1149/1945-7111/ad8548
### **2.3 Parameter System**
매개변수 시스템은 배터리별 매개변수를 관리하고 `ParameterValues`클래스를 통해 다양한 화학 물질에 대한 표준 매개변수 집합을 제공합니다. 표준화된 매개변수 공유를 위해 Battery Parameter eXchange(BPX) 형식을 지원.

### **2.4 Discretization system**
이산화 시스템은 유한 체적, 스펙트럼 체적 또는 유한 요소법을 사용하여 연속 모델 방정식을 이산 수치 문제로 변환합니다.
![[Pasted image 20251014072153.png]]



![[Pasted image 20251014072229.png]]

# DFN 모델
[[DFN ]]

## 관련 문서

- [[모델 Figure 참고]] (Project/Modeling)


