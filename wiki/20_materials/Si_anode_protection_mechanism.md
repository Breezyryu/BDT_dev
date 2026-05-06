---
title: Si 음극 보호 메커니즘 (만방 voltage 상향)
aliases: [Si Anode Protection, Si Protection Mechanism, 만방 V 상향]
tags: [materials, silicon, anode, swelling, SEI, LAM, lifetime, stub]
type: reference
status: stub
created: 2026-05-02
updated: 2026-05-02
related:
  - "[[../CONTEXT|CONTEXT]]"
  - "[[Silicon]]"
  - "[[../30_modeling/swelling_ec_modeling_literature]]"
  - "[[../30_modeling/Empirical_Degradation_Models]]"
  - "[[../31_software_dev/adr/0001-lifetime-prediction-tool-split|ADR-0001]]"
  - "[[../31_software_dev/adr/0002-measurement-envelope-operational-definition|ADR-0002]]"
---

# Si 음극 보호 메커니즘 — 만방 voltage 상향

> **상태**: stub. 본인 정독 + 본 wiki 의 deep-dive 노트로 분리·확장 예정.
>
> **배경 (2026-05-02)**: BDT '실수명 예측' 탭에 Si 보호 만방 voltage 상향 기능을 본인이 추가해야 함 (1주 작업). 메커니즘 frame 은 선행Lab 「배터리 소재 전공자」 파트가 결정. 본인은 그 위에 모델링 layer 추가. 박사급 peer 보고 시 메커니즘 정합성 + 학계 reference 필수.

---

## 1. 메커니즘 — (a) + (b) 결합

### (a) Cyclic stress range ↓ → SEI fracture ↓ → swelling ↓

Si 음극은 lithiation/delithiation 시 **부피 ~300% expansion / contraction** (이론치). full delithiation 끝점 (low SOC) 에서 부피 contraction 이 최대 → SEI 가 부착된 표면이 mechanical strain 받음 → **SEI fracture → 새 SEI 형성 (electrolyte 소모) → 수명 ↓ + swelling 누적**.

만방 voltage ↑ → SOC 하한 ↑ → cyclic SOC range 좁힘 → Si 의 cyclic strain amplitude ↓ → SEI fracture rate ∝ (Δstrain)^n (n = 1.5~2 추정).

**학계 reference**:
- Wood et al. 2015 (Adv. Energy Mater.) — Si 음극 SEI cyclic fracture
- Berla et al. 2014 (J. Power Sources) — Si SEI mechanical reformation
- Schweidler et al. 2018 (JES) — Si-Graphite blend stage expansion

### (b) Si full delithiation 회피 → LAM 보호

Full delithiation (SOC 0%) 시 Si 입자 표면에서 active material loss (LAM) 가속:
- Si 입자 cracking → 활물질 isolation
- 음극 conductive network 단절
- Capacity loss + 저항 증가 동시

만방 voltage ↑ → 음극 측 평형 voltage 가 Si full delithiation 영역 도달 안 함 → LAM 보호.

**학계 reference**:
- Sethuraman et al. 2010 (J. Power Sources) — Si 박막 in-situ stress
- Bower et al. 2011 (JMPS) — Si 소성-탄성 응력
- Liu et al. 2014 (Nature Nanotech.) — Si 입자 cracking in-situ TEM

## 2. Trade-off — 수명 ↑ vs 사용 capacity ↓

만방 V 3.0 → 3.3V 상향 시:
- Cyclic SOC range = 0~100% → ~10~100% (SOC 하한 ~10% 가정)
- 사용 가능 capacity = -8~10% (cell 별 OCV slope 의존)
- 수명 (사이클 80% retention) = +20~40% (Si 함량 의존, Gen6+ 15% < Gen6++ 25% 기대)

**Pareto front 표준 보고 frame** (CONTEXT.md):
- X축 = 만방 V 또는 사용 capacity
- Y축 = 80% retention cycle (form-mediated extrapolation, ADR-0003)
- 다층 곡선 = Gen6 (Gr only, 효과 ≈ 0) · Gen6+ (15%) · Gen6++ (25%)

## 3. 모델링 input ('실수명 예측' 탭)

본인 1주 작업의 추가 기능:

| Input parameter | Type | 정의 | 비고 |
|----------------|------|------|------|
| 만방 V (V_low) | continuous | 방전 cutoff voltage | ADR-0002 envelope 의 V상하한 차원 흡수 |
| 만방 보호 cycle 빈도 | binary cycle parameter | "100cy 마다 1회" 형식 | 본인 답에서 명시 |
| Si 함량 (PF 매핑) | discrete | Gen6+ 15% / Gen6++ 25% / Gen6 0% | 셀 매트릭스 자동 매핑 |

**fit form**:
- DOD = SOC100 - SOC_lower(V_low) → 정의 흡수 (전임자(랩장님) cross-check 필요)
- cycle fade 항에 **Si-protection factor** = f(DOD, Si 함량) multiplier
- form-mediated extrapolation (ADR-0003) 위에서 운영

## 4. 박사급 peer challenge 사전 준비

| Q | A 요지 |
|---|--------|
| "왜 만방 상향이 Si 보호?" | (a) cyclic stress range ↓ + (b) full deli 회피 — Wood 2015, Berla 2014 reference |
| "Trade-off 정량?" | 만방 V vs 수명 vs capacity Pareto front. Gen6+ 에서 만방 3.3V → 수명 +30% / capacity -8% |
| "Gen6 Gr only 셀에 적용 효과?" | Si 함량 0% → Si-protection factor ≈ 0. 만방 V 상향 효과 미미 (Graphite 의 cyclic stress range 영향만, 작음) |
| "DOD 정의는?" | 전임자 cross-check 필요 (Flagged #9). 우선 SOC100 - SOC_lower(V_low) form 가정. |
| "측정 envelope 안에서 검증?" | ADR-0002 envelope 의 V상하한 축 = 만방 V 차원 자연 통합. 측정 점에서 fit, form-mediated extrapolation (ADR-0003) 으로 양산 적용 V 점 예측. |

## Follow-up

- [ ] Wood et al. 2015 정독 + 본 wiki 에 deep-dive 분리
- [ ] Berla et al. 2014 정독
- [ ] Schweidler et al. 2018 (Si-Graphite blend) — Gen6+/Gen6++ 의 SiC 함량 별 stage expansion 정량
- [ ] DOD 정의 — 전임자(랩장님) cross-check (Flagged #9)
- [ ] '실수명 예측' fit form 의 cycle fade 항 구조 분석 (월요일 첫 작업)
- [ ] 선행Lab 「소재 전공자」 파트와 Si 보호 메커니즘 frame 협의 (현재 정책 vs 본인 모델링 frame 정합)
- [ ] Pareto front 시각화 PoC — Gen6+/Gen6++ 셀의 만방 V sweep 시뮬
