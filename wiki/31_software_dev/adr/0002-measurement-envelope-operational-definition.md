# ADR-0002 — Measurement envelope: operational definition (T × V × 수명축, grid-only, similar-cell transfer)

- Status: accepted
- Date: 2026-05-02
- Deciders: 본인 (선행배터리랩 「성능·수명 해석」 파트)
- Follows: [[0001-lifetime-prediction-tool-split]]

## Context

[ADR-0001](0001-lifetime-prediction-tool-split.md) 이 empirical interpolation (envelope 안) ↔ EC model extrapolation (envelope 외) 의 분할 정책을 박았다. 이 정책이 실무에서 의미 있으려면 **measurement envelope 의 운영 정의** — 어느 차원에서 어떻게 boundary 잡고, 안/밖 어떻게 판정하고, 새 셀 도착·시험 진행 시 어떻게 갱신할지 — 가 필요하다.

단일 셀의 측정 매트릭스로 모든 (T · V상하한 · DOD · C-rate · 수명) 조합을 cover 하는 것은 시험 자원·일정 한계로 불가능하다. 협력사 데이터 + 자주검증 데이터 + 사내 시험 데이터 모두 제한적이다. 한 셀에 대해서도 사이클 누적·calendar 시간 축의 envelope 는 시험 진행 중에 동적으로 확장된다. 이런 현실에서 envelope 가 비현실적으로 좁으면 empirical interpolation 영역이 거의 없어 ADR-0001 의 균형이 무너지고, 너무 넓으면 측정 안 한 영역까지 envelope 안으로 흡수해 박사급 peer 청중 (CL3·CL4) 의 epistemic challenge 에 약점이 생긴다.

## Decision

측정 envelope 의 운영 정의:

- **차원** = **T × V상하한 × 사이클 누적·calendar 시간 (수명축)**. DOD / C-rate 차원은 현재 single point 일 가능성 — envelope 의 차원 축소 (hyperplane) 으로 처리, 추후 측정 누적 시 차원 추가.
- **형식** = **grid points only (strict)**. 측정 점만 envelope 안. 모서리·grid 사이 보간 영역도 정의상 envelope **밖**. 보간은 grid 점 간 가까운 거리에 한해 신뢰.
- **갱신** = **dynamic**. 사이클·calendar 축 boundary 가 시험 진행 따라 확장. 보고 시점 별 envelope 명시 (예: "2026-05-02 기준 Gen6+ envelope = 23°C × 4.4V cutoff × 800사이클").
- **보강** = **유사 셀 데이터 transfer**. 단일 셀 envelope 부족 시 다른 PF · 모델 · 제조사 의 유사 거동 셀 데이터로 envelope 보강. 직접 측정 영역과 transfer 영역은 신뢰도 별도 표시.

용어 정의는 [[../../CONTEXT|CONTEXT.md]] 의 "측정 envelope" / "유사 셀 데이터 transfer" entry 참조.

## Consequences

**Positive**:
- Conservative empirical — envelope 가 좁아 EC model 측 영역이 명료하게 보임. 박사급 peer 가독성 ↑.
- Dynamic 갱신 = 시험 진행이 자연스럽게 envelope 확장으로 추적. 별도 운영 부담 없이 시험 누적 = envelope 누적.
- Transfer 보강 명시 = 박사급 peer 가 "단일 셀 envelope 부족하면?" challenge 들어오기 전 본인이 먼저 정직하게 답 가능 (epistemic humility).
- 보고 시점 별 envelope 명시 = 동일 셀의 다른 시점 보고가 비교 가능 (예: 보고 1 = 800사이클 envelope, 보고 2 = 1500사이클 envelope).

**Negative**:
- 보고 시 envelope 명시 부담 — 매 보고에 envelope 차원·범위·갱신 시점 1슬라이드 또는 별첨 필요.
- Transfer 데이터 영역의 stratify 표시 필요 — BDT '실수명 예측' 탭 결과 시각화 시 직접 측정 vs transfer 보강 영역 색상/주석 분리 (UI 보강 작업).
- Grid-only strict 정책으로 envelope 안 영역이 좁아 → 사용자 (그룹원) 가 BDT 탭 결과를 envelope 외 영역에서 신뢰하지 않도록 안내 필요.

**Neutral / follow-up**:
- **Transfer 신뢰도 정량화 frame 미해소** (CONTEXT.md Flagged #5) — 유사도 정의, transfer 신뢰도 metric, fit uncertainty propagation. 별도 grill 또는 작업 중 발견 시 frame 정의.
- **BDT '실수명 예측' 탭의 envelope 시각화 기능 추가 후보** — 별도 ADR 후보. 직접 측정 grid 점 / transfer 보강 영역 / EC model 영역 3-tier 색상 분리.
- **DOD / C-rate 차원 추가 시점** — 측정 누적 따라 환원. 추후 ADR-0001 / ADR-0002 의 amendment 또는 superseding 후속 ADR.

## Alternatives considered

- **(a) Hyperrectangle (각 축 [min, max] product)** — 운영 단순하나 측정 안 한 모서리 (예: 15°C × 4.7V) 까지 envelope 안 흡수. 박사급 peer 가 corner 측정 부재 즉 challenge. **Rejected**.
- **(b) Convex hull (측정점 폐포)** — 모서리는 폐포 외로 정확히 처리 가능하나 N≥3 차원에서 시각화·운영 부담. **Rejected**.
- **(α) 표준 측정 매트릭스만 (모든 신규 셀 동일 시험)** — 신규 셀별 시험 자원·일정 한계로 표준 매트릭스 강요 불가능. **Rejected**.
- **(γ) 표준 + 셀별 보강 (transfer 없음)** — single-cell 측정 한계를 메우지 못함. envelope 가 비현실적으로 좁아 ADR-0001 의 empirical 영역 거의 없음. **Rejected**.
- **단일 셀 envelope (transfer 없음)** — 데이터 부족 인정 안 하는 frame. 박사급 peer 가독성 ↓. **Rejected**.
