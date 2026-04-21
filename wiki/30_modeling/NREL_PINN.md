---
title: "NREL_PINN"
tags: [Modeling_AI, PINN, NREL, 문헌]
type: reference
status: active
related:
  - "[[PINN_기초]]"
  - "[[PINN_문헌정리]]"
  - "[[Knowledge_PINN_DeepONet]]"
created: 2025-12-15
updated: 2026-03-15
source: "origin/NREL - PINN.md"
---

https://arxiv.org/pdf/2312.17329
https://arxiv.org/pdf/2312.17336
https://arxiv.org/pdf/1505.07776
https://onlinelibrary.wiley.com/doi/full/10.1002/sam.11347

양음극 프로파일 분석
[https://doi.org/10.1016/j.jpowsour.2022.231296](https://doi.org/10.1016/j.jpowsour.2022.231296 "Persistent link using digital object identifier")


- Voltage responses > internal parameters
- governing equations that describe the internal kinetic/transport physics
- **Prameter**: reaction kinetics, transport, initial battery state
- PINN 학습도 많은 computation 리소스가 필요 > Bayesican calibration, Markov-Chain Monte-Carlo(MCMC),

## Internal parameter
- Effective solid-phase diffusivity
- Eletrolyte transport property
- Surface kinetic rates

Particle suface/diffusion length: 측정 어려움 (destructive test 필요)

Non-destructive test: RPTs, EIS
> battery dynamic에 영향을 미침
> cycle-by-cycle polarization

approximate the physics-based models

Fidelity 확보 모델 데이터 기반 학습

## 관련 문서

- [[PINN_문헌정리]] — 논문 리뷰
- [[PINN_기초]] — PINN 기본 개념
- [[Knowledge_PINN_DeepONet]] — DeepONet 심화
