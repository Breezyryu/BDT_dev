# ADR-0004 — Cell design-to-P2D parameter mapping: 4 categories + physics-based transfer

- Status: accepted
- Date: 2026-05-02
- Deciders: 본인 (선행배터리랩 「성능·수명 해석」 파트)
- Anchors: [[0001-lifetime-prediction-tool-split]], [[0002-measurement-envelope-operational-definition]], [[0003-functional-form-mediated-extrapolation]]

## Context

BDT #9 '전기화학Sims' 탭 (PyBaMM main + House Code 발굴) 의 핵심 frame. Gen6 계열 (Gen6 Gr only / Gen6+ SiC 15% / Gen6++ SiC 25%) P2D 시뮬레이션 진입 단계. 사용자 명시: "셀 개발 설계 값과 모델의 파라미터를 관계 정의 필요" — frame 미정.

박사급 peer 청중 (CL3·CL4 과반) 이 첫 보고에서 즉 challenge 들어올 영역:
- ε_act, R_s 등 P2D 파라미터를 어디서 가져왔나?
- 셀 별로 다른 파라미터 — 셀 간 transfer 는 어떻게?
- D, k_0 같은 fit-driven 은 모든 셀에 half-coin GITT 측정 가능한가?

본인 frame 의 데이터 한계 ([ADR-0002](0002-measurement-envelope-operational-definition.md) 의 유사 셀 transfer 정책):
- 모든 Gen6 계열 셀에 half-coin GITT 측정 불가 (자원 한계)
- full cell GITT 만 있는 셀의 D, k_0 추정 = inverse problem
- **1:1 매핑 파라미터 변동에 따른 fit-driven 파라미터의 셀 간 transfer = physics 기반 정합 필수**

## Decision

P2D 파라미터의 셀 별 매핑을 **4 카테고리** 로 분류하고, fit-driven 파라미터의 셀 간 transfer 는 **physics-based form** 위에서 수행한다.

### 4 카테고리

**(A) Direct 1:1 매핑** — 셀 spec 에서 직접 추출:
| 파라미터 | 매핑 source |
|---------|------------|
| ε_act (활물질 부피분율) | 합제밀도 × 활물질 비율 / 활물질 진밀도 |
| R_s (입자 반경) | 활물질 D50 (PSD 측정) |
| L (전극 두께) | 직접 측정 |
| c_max (이론 농도) | 활물질 화학량 (LCO / Graphite / Si 별) |

**(B) Indirect / Derived** — (A) 위에서 학계 표준 form 으로 유도:
| 파라미터 | Form |
|---------|------|
| a_s (비표면적) | 3·ε_act / R_s (구형 입자 가정) |
| τ (tortuosity) | ε^-0.5 (Bruggeman, ★ Gen6 측 검증 필요) |
| ε_elyt | 1 − ε_act − ε_binder − ε_carbon |

**(C) Fit-driven** — 측정 데이터로 fit 추출:
| 파라미터 | Source |
|---------|--------|
| D (확산계수) | GITT (full cell + half-coin 일부 셀) |
| k_0 (Butler-Volmer) | EIS fit |
| OCV(SOC) | half-coin GITT (Gen6 일부 셀만) |

**(D) 문헌 default** — 활물질 / 전해액 spec 으로 reference:
| 파라미터 | Source |
|---------|--------|
| σ (electronic conductivity) | 활물질 종 별 학계 값 |
| κ (electrolyte conductivity) | 전해액 vendor spec |
| Si volume expansion factor | Si 함량 별 (Schweidler 2018) |

### Physics-based parameter transfer

(A) Direct 매핑이 셀 별로 다를 때, (C) Fit-driven 파라미터의 셀 간 transfer 는 **physics-based form 위에서**:

- **D_eff transfer**: D_eff = D_0 · ε^a / τ. 셀 A 의 D_eff 측정 → 셀 B 의 D_eff = D_eff(A) · (ε_B/ε_A)^a · (τ_A/τ_B)
- **k_0 transfer**: k_0 ∝ a_s ∝ ε_act / R_s. R_s 변동 → k_0 자연 scaling.
- **OCV 활물질 의존**: 활물질 종 동일 시 OCV 동일. **Si-Graphite blend 의 가중 평균** 은 학계 form (Lain-Brandon 2019, Schweidler 2018) 위에서.

**Raw transfer (form 없이 단순 scaling)** 는 금지 — ADR-0003 의 raw extrapolation 금지와 일관.

학계 anchor:
- Newman 1993 / Doyle-Newman 1993 — porous-electrode theory (P2D 표준 form)
- Bruggeman 1935 — tortuosity-porosity relation (검증 필요)
- Kim, Pesaran, Smith 2011 (MSMD) — multi-scale 매핑
- Schweidler 2018 — Si-Graphite blend stage expansion
- Lain-Brandon 2019 — Si-Graphite blend OCV 가중 평균

### 운영 정합 (4 ADR layer)

- **ADR-0001** 의 EC model extrapolation 영역 → ADR-0004 의 (C) Fit-driven + physics-based transfer 가 backbone
- **ADR-0002** 의 유사 셀 transfer → ADR-0004 의 physics-based transfer 가 학계 form specialization
- **ADR-0003** 의 form-mediated extrapolation → ADR-0004 의 transfer form 도 학계 표준 위에서

## Consequences

**Positive**:
- 박사급 peer 가독성 ↑ — 4 카테고리 frame + physics-based transfer 명시 = 학계 표준 정합.
- 셀 매트릭스 (제조사 4 × Gen3~Gen6++) 모두에 동일 매핑 frame 재사용.
- ADR-0001~0003 의 자연 후속 — modeling frame **4 ADR layer 완성** (도구 분할 + envelope + form-mediated + 파라미터 매핑).
- BDT '전기화학Sims' 탭 결과의 epistemic 정직성 ↑ — 어느 파라미터가 직접 / fit / transfer 인지 표시.

**Negative**:
- 4 카테고리 분류 표 작성 부담 — `wiki/30_modeling/` 에 Gen6 계열 매핑 표 노트 신규.
- **(B) Bruggeman 가정의 Gen6 측 검증 부재** → 셀 별 τ 측정 가능 시 검증, 아니면 가정 유지 + UQ 표시.
- (C) Fit-driven UQ 정량 부담 (ADR-0003 의 UQ 와 정합).
- Physics-based transfer 의 form 별 학계 reference 정리 부담.

**Neutral / follow-up**:
- **Gen6 계열 매핑 표 작성** — 셀 별 ε_act, R_s, L, c_max 표. `wiki/30_modeling/` 에 신규 노트 ("Gen6 셀 P2D 파라미터 매핑").
- **Bruggeman 검증** — Gen6 측 셀 측정 데이터 충분 시.
- **Si-Graphite blend OCV 가중 평균 form** (Lain-Brandon 2019) — 별도 deep-dive.
- **House Code (MSMD) 의 multi-scale 매핑이 ADR-0004 frame 과 어떻게 정합** — D1 작업 시 cross-check.
- BDT '전기화학Sims' 탭 UI 에 4 카테고리 표시 (어느 파라미터가 직접 / fit / transfer 인지 사용자 가독성).

## Alternatives considered

- **단일 카테고리 (모두 fit-driven)** — 모든 파라미터를 측정 fit 으로. 측정 부담 + (A) Direct 측 spec 정보 무시. **Rejected**.
- **단일 카테고리 (모두 문헌 default)** — 모든 파라미터를 활물질 종 별 reference. 셀 별 microstructure 차이 무시. **Rejected**.
- **3 카테고리 (Physics-based transfer 미포함)** — fit-driven 파라미터의 셀 간 transfer 정책 부재 → ADR-0002 의 유사 셀 transfer 가 ad-hoc 운영. 박사급 peer challenge 영역. **Rejected**.
- **CONTEXT.md entry 만 — ADR 미작성** — frame 결정의 hard-to-reverse + surprising + real trade-off 모두 충족 → ADR 가치 큼. **Rejected**.
