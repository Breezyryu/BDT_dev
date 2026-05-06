---
title: 스웰링 + 전기화학 모델링 연구 정리 (Literature)
aliases: [Swelling EC Modeling, Electrochemo-Mechanical Coupling, ECM]
tags: [modeling, swelling, mechanical, P2D, MSMD, literature, stub]
type: literature
status: stub
created: 2026-05-02
updated: 2026-05-02
related:
  - "[[../CONTEXT|CONTEXT]]"
  - "[[시뮬레이션_용어사전]]"
  - "[[MSMD]]"
  - "[[PyBaMM_정리]]"
  - "[[배터리_모델링_리뷰]]"
---

# 스웰링 + 전기화학 모델링 연구 정리

> **상태**: stub. 본인 정독 + 본 wiki 의 deep-dive 노트로 분리·확장 예정.
>
> **배경 (2026-05-02)**: BDT 사이클 탭 스웰링 데이터 입력 grill 중, "P2D 모델도 스웰링 어려움" 답이 부분적으로만 정확하다는 발견. 활물질·cell-level mechanical coupling 은 표준 영역이고, hard/gas 분리만 한계. 그리고 **House Code (MSMD/GH-MSMD) 자체에 mechanical domain 이 이미 포함되어 있을 가능성** 큼 — raw 분석 시 cross-check 우선.

---

## 1. 활물질 단위 (P2D + Stress) — 표준 영역

| Paper | 기여 |
|-------|------|
| **Christensen & Newman 2006** (J. Solid State Electrochem.) | P2D + stress 의 origin paper. Diffusion-induced stress 표준 form |
| **Mukhopadhyay & Sheldon 2014** (Progress in Materials Science) | Stress in Li-ion SOA 리뷰. 박사급 peer 가독성 최상 |
| Sethuraman et al. 2010 (J. Power Sources) | Si thin film in-situ stress 측정 |
| Bower et al. 2011 (JMPS) | Si 음극 소성-탄성 응력 모델 |
| Schweidler et al. 2018 (JES) | Graphite stage 별 lattice expansion 정량 |
| Reimers & Dahn 1992 | Graphite stage 의 origin |

→ 활물질 단위에서는 **Si expansion (300% 이론치)**, **Graphite 약 10% c-axis expansion** 모두 정량화·시뮬화 standard.

## 2. Cell-level Pouch Swelling — 활발한 최신 영역

| Paper | 기여 |
|-------|------|
| ★ **Mohtat et al. 2021** (Nature Communications) | Pouch cell swelling **시계열 측정 + 모델 결합**. 본인 4·5번 양 측 직접 영향 |
| ★ **Louli, Genovese, Dahn group** (2018~2023, JES 시리즈) | **Differential thickness analysis** — Q vs thickness 의 dQ/dT analog. dV/dQ 와 결합 가능 |
| Cannarella & Arnold 2014 (J. Power Sources) | Pouch internal pressure 측정 |
| Berg, Schiele et al. 2023 | Fast-charge 중 in-situ thickness time-resolved |

→ 본인의 **100사이클 만충 두께 측정** 과 **Mohtat·Louli 측 differential thickness analysis** 가 결합 가능. 4번 empirical 의 secondary feature 로 두께 신호 활용 시 강한 backbone.

## 3. Hard / Gas Swelling 분리 — 여전히 한계

| Paper | 기여 |
|-------|------|
| Spotnitz & Franklin 2003 | Gas evolution thermodynamics |
| Onuki et al. 2008 | Gas mass spectrometry 측정 |
| Bernhard et al. 2015 | DEMS (Differential Electrochem. Mass Spec.) — gas component 분리 |

→ DEMS 로 gas 항 분리 측정 가능, 단 **cell-level swelling 과 결합한 정량 분리는 여전히 한계** (사용자 답 = 학계 합의).

## 4. PyBaMM 호환 Swelling Model

| Paper | 기여 |
|-------|------|
| **Ai et al. 2020** (J. Power Sources) | PyBaMM 통합 가능한 **cell expansion model** (활물질 + 전극 mechanical coupling). 본인 PyBaMM main 정책에 직접 활용 가능 |

## 5. ★ House Code (MSMD/GH-MSMD) 의 Mechanical Domain — 미발견 자산 가능성

**Kim, Pesaran, Smith 2011** (JES, [`raw/House Code/kim2011.pdf`](../../raw/House%20Code/kim2011.pdf)) 의 MSMD 4-domain 정의:

1. **Particle-domain** — 활물질 입자 (화학·확산·**stress**)
2. **Electrode-domain** — porous-electrode 평형 (전극 단위)
3. **Cell-domain** — thermal · **mechanical homogenization**
4. **Capacity-fade-domain** — 열화 · degradation

**Lee 2017 GH-MSMD generalization** ([JES 2017](https://iopscience.iop.org/article/10.1149/2.0571706jes/pdf)) 도 mechanical homogenization 포함.

→ **본인 raw/House Code/MSMD/, GH-MSMD/ 디렉토리 안에 mechanical 모듈이 명시적으로 들어있을 가능성 높음**. D1 (House Code 분석) 작업 시 우선 cross-check.

→ 만약 mechanical 모듈 확인되면, ADR-0001 의 EC model capability 가 expand 되어 **5번 트랙 substance 의 잠재 확장점**:
  - Gen6+ (SiC 15%) / Gen6++ (SiC 25%) 의 활물질 expansion + cell-level swelling 추정
  - 4번 empirical 의 두께 secondary feature 와 cross-validate
  - 박사급 peer 보고 시 "House Code 자체에 mechanical 있어 활용" frame 가능

## 6. 학계 합의 한계 (주의)

- **Hard / Gas 분리 in-situ** — DEMS 외 cell-level 결합 측정 한계.
- **Long-term cycle 의 swelling 정확 fit** — 활물질 expansion + SEI growth + plating + gas 의 다항 결합으로 fit 불안정.
- **Form factor 별 기구 stress 환경 영향** — pouch vs prismatic vs cylindrical 별 stress 분포 다름. 모델링 측 generalization 어려움.

→ **현재 BDT 측 frame ("정상 hard swelling 직접 측정 + empirical 추정 — 신뢰도 한계 인정")** 은 학계 한계와 정합.

## Follow-up

- [ ] Mohtat 2021 정독 + 본 wiki 에 deep-dive 노트 분리
- [ ] Louli·Dahn series 정독 + differential thickness 노트 분리
- [ ] Christensen-Newman 2006 정독 + P2D+stress 표준 form 노트 (← 박사급 peer 보고 backbone)
- [ ] **D1 작업 시 raw/House Code/MSMD/ 의 mechanical 모듈 cross-check** ← 우선
- [ ] House Code mechanical 확인 시 → 별도 deep-dive 노트 + ADR-0002 후보 ("House Code mechanical capability 활용 정책")
- [ ] Ai et al. 2020 의 PyBaMM 통합 swelling model PoC 검토 (본인 PyBaMM main 정책에 자연 통합)
