---
title: "Electrochemical Parameter"
tags: [Battery_Knowledge, 전기화학, 파라미터]
type: knowledge
status: active
related:
  - "[[GITT]]"
  - "[[Battery_Electrochemical_properties]]"
  - "[[01_Modeling_AI/PyBaMM_정리]]"
created: 2025-12-15
updated: 2026-03-15
source: "origin/Electrochemical parameter.md"
---

# 1. Pore size
- Braunauer-Emmett-Teller (BET) theory
	- fitting gas surface absorption measurements
	- 3~300nm
- Mercury porosimetry
	- pore neck rather than full pore size
# 2. Porosity
- X-ray tomography
- Electron microscopy
	- tortuosity, bruggeman coefficient, pore shape도 estimate 하는 연구도 다수
- Ion beam milling with scanning electron microscopy (SEM-FIB)
# 3. Chemical and material properties
- Plasma optical emission spectroscopy (ICP-OES)
	- ICP is used for NMC elemental analysis because it can be dissolved in acid
- Energy-dispersive X-ray spectroscopy (EDS)
	- negative electrode components SiOx and graphite cannot, therefore the composition is analyzed with EDS only.
	- EDS cannot detect low atomic number elements such as lithium
	- 산란효과를 피하기 위해 이온밀링 처리된 시료 표면에서 수행
# 4. Electrochemical
- full cell, half cell, three-electrode cell : 각각 한계를 지님
- Two-electrode half cells (lithium metal counter)
	- 높은 내부 저항 (ohmic drop)
	- 리튬메탈로 인한 polarization
	- 쿨롱 효율이 낮아 수명이 안좋다
	- 리튬이 충분한 상황으로 full capacity를 알 수 있다.
- Three-electrode cell
	- 반전지와 전체 전지의 3전극 시험을 결합함으로써 각 전극 내부의 전지 화학량론 및 리튬 함량을 분석
	- 기본적인 열역학적 및 동역학적 매개변수를 제공할 수 있다.
-  GITT (Galvanostatic intermittent titration technique)
	- OCV, Diffusivity
- EIS
	- 온도별 Exchange current density
	- Activation energy: arrhenius equation
	- Reaction rate
- 4point probe
	- electronic conductivity
	-

## 관련 문서

- [[ECT]] (Project/Battery_Research)
- [[배터리 QPA(Quality Process Audit)]] (Project/Battery_Research)
- [[코인셀 SOP]] (Project/Battery_Research)
