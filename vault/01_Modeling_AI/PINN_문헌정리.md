---
title: "PINN 문헌 정리"
tags: [Modeling_AI, PINN, 문헌정리]
type: reference
status: active
related:
  - "[[PINN_기초]]"
  - "[[Knowledge_PINN_DeepONet]]"
  - "[[NREL_PINN]]"
  - "[[NN_문헌정리]]"
  - "[[NN_DataSet]]"
created: 2025-12-15
updated: 2026-03-15
source: "origin/PINN 문헌 정리.md"
---

# [Physics-informed neural network for lithium-ion battery degradation stable modeling and prognosis](https://www.nature.com/articles/s41467-024-48779-z)
	- 387 battery / 310,705 samples

![[Pasted image 20250819092237.png]]
![[Pasted image 20250819092403.png]]
- SOH에 따른 feature
- Correlation heatmap
-
# [Perspective—Combining Physics and Machine Learning to Predict Battery Lifetime](10.1149/1945-7111/abec55)
![[Pasted image 20250819085201.png]]
- Sequential Integration
	- A1: PB 예측값 ~ 실험값
	- A2: 실험값과 유사한 PB synthetic data
	- A3: 매개변수(확산계수, exchange current density etc.) 학습
- Hybrid
	- 물리적 제약을 두는 컨셉
	- 연구 결과는 없음

#

## 관련 문서

- [[NREL - PINN]] (Resource/PINN)
