# ADR-0003 — Functional form fit 기반 limited extrapolation 의 epistemic 권한

- Status: accepted
- Date: 2026-05-02
- Deciders: 본인 (선행배터리랩 「성능·수명 해석」 파트)
- Anchors: [[0001-lifetime-prediction-tool-split]], [[0002-measurement-envelope-operational-definition]]

## Context

[ADR-0001](0001-lifetime-prediction-tool-split.md) 이 empirical interpolation (envelope 안) ↔ EC model extrapolation (envelope 외) 의 분할 정책을 박았다. [ADR-0002](0002-measurement-envelope-operational-definition.md) 가 envelope 의 운영 정의 (T × V × 수명축, grid-only strict, similar-cell transfer) 를 박았다.

그러나 실무에서 **PRA 승인 수명 측 시험은 1000~1600cy 까지만 진행** 되며, **80% retention 도달 cycle** 은 시험 cycle 외 영역의 extrapolation 으로 예측한다. ADR-0001 의 "empirical extrapolation 금지" 를 strict 해석하면 80% 점 예측 자체가 권한 없음 — 그러나 이 영역의 측정을 수년간 진행하는 것은 양산 일정·시험 자원 측 비현실. EU 수명 / 승인 수명 / 실사용 수명 3 트랙 모두 동일 한계.

학계 표준 functional form (NREL Smith calendar fade √t Arrhenius, Wang / Ploehn cycle fade DOD-coupled, Spotnitz dual-mechanism 등) 위에서의 fit 후 evaluation 은 **raw extrapolation 과 epistemic 차이가 있다** — form 자체가 학계 표준 검증을 받은 모델이기 때문이다.

박사급 peer (CL3·CL4 과반) 청중에서 "fit form-mediated extrapolation" 은 익숙·수용 영역이지만, 보고에서 **form 의 학계 근거·extrapolation 영역·UQ** 명시가 안 되면 즉 challenge 들어온다.

## Decision

ADR-0001 의 분할 frame 위에 다음 정책을 추가한다.

**학계 표준 functional form 위에서의 limited extrapolation 을 허용** — 단 다음 3 조건을 모두 충족할 때:

1. **Form 의 학계 근거 명시** — fit form 이 검증된 학계 표준 (예: NREL Smith calendar √t Arrhenius, Wang cycle DOD-coupled, Spotnitz dual-mechanism 등) reference 명시.
2. **Extrapolation 영역 명시** — ADR-0002 의 측정 envelope 사이클 축 boundary 대비 extrapolation 정도 (예: "측정 1000cy → 1500cy 점 = 1.5x extrapolation, 학계 표준 form 기준 valid range 내").
3. **UQ 정량** — fit 결과 confidence interval (95% CI 권장), envelope 외 영역에서 CI 가 확장되는 시각 표기.

용어:
- **Form-mediated extrapolation** = ADR-0001 의 "empirical extrapolation 금지" 의 예외 카테고리. 위 3 조건 충족 시 허용.
- **Raw extrapolation** = 검증된 form 없이 polynomial / spline 외삽. **여전히 금지**.

용어 정의는 [[../../CONTEXT|CONTEXT.md]] 의 Language 섹션 참조.

## Consequences

**Positive**:
- 박사급 peer 가독성 ↑ — fit form 의 학계 근거 + extrapolation 영역 + UQ 명시 = epistemic 정직 frame.
- EU 수명 / 승인 수명 / 실사용 수명 3 empirical 트랙 모두 **동일 form-mediated frame** 적용 가능. 80% 점 예측이 모든 트랙에서 자연 수용.
- ADR-0001 의 strict 해석을 보강 — 운영 부담 ↓ (80% 시험 수년 진행 압박 해소).
- BDT 의 '승인 수명 예측' / 'EU 수명 예측' / '실수명 예측' 탭 출력에 학계 reference 표시 + UQ 그림자 표시 권장 (UI 보강 후보).

**Negative**:
- Form 별 학계 reference 정리 부담 — `wiki/30_modeling/` 에 functional form 카탈로그 노트 필요 ([[../../30_modeling/Empirical_Degradation_Models]] 보강).
- UQ 정량 부담 — fit 결과 CI propagation, form 의 hyperparameter sensitivity 분석.
- "Limited" 의 정량 기준 모호 — 1.5x? 2x? form 별 valid range 다를 수 있음 → 추후 form 별 정리.

**Neutral / follow-up**:
- Form-mediated vs raw extrapolation 의 case-by-case 판정 = 작업 중 발견 시 ADR-0003 의 운영 노트로 누적.
- BDT '실수명 예측' 탭 UI 에 form-mediated extrapolation 영역 vs envelope 안 영역 색상 분리 — ADR-0002 의 envelope 시각화 후속.
- Form 카탈로그 노트 작성 — NREL Smith / Wang / Spotnitz / Bloom·Christophersen 등 표준 form reference + valid range 정리.

## Alternatives considered

- **(β) Envelope 정의를 fit form valid 영역으로 확장** — "envelope = fit form 학계 표준 valid 영역" 으로 재정의. ADR-0002 의 grid-only strict 와 충돌, envelope 정의 모호화. **Rejected**.
- **(γ) 80% 점은 EC model 영역으로 분류** — 1000cy 외는 P2D 시뮬 + empirical hybrid 로 보냄. functional form fit 이 자연스럽게 evaluation 가능한데 EC model 부담. **Rejected**.
- **ADR-0001 amendment 형식** — strict 해석을 form-mediated 허용으로 명료화. 단 ADR layer 가 흐림 — "도구 분할 frame" 과 "fit form 권한" 이 같은 ADR 안에 들어가면 신규 reader 가독성 ↓. **Rejected** (ADR-0003 신규로 layer 분리 채택).
- **CONTEXT.md entry 만** — ADR 형식 부담 회피. 단 frame 결정의 hard-to-reverse + surprising w/o context + real trade-off 모두 충족 → ADR 가치 충분. **Rejected**.
