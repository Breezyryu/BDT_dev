# ADR-0001 — Lifetime prediction tool split: empirical interpolation vs EC model extrapolation

- Status: accepted
- Date: 2026-05-02
- Deciders: 본인 (선행배터리랩 「성능·수명 해석」 파트)

## Context

배터리 셀의 수명 예측은 두 영역으로 나뉜다 — **측정한 V·T·SOC·C-rate 조건 안의 보간** 과 **측정 안 한 영역의 추정**. 한 도구 (예: empirical fit 만, 또는 P2D 시뮬 만) 로 두 영역을 모두 다루면 박사급 peer 청중 (CL3·CL4 과반) 이 즉 challenge 하는 epistemic 빈틈이 생긴다:

- empirical 모델은 한 번 fit 하면 모든 V·T 조건 예측 가능해 보이지만, 실제로는 **측정 grid 위 보간만 신뢰 가능** 하다. 측정 envelope 외 영역의 empirical extrapolation 은 박사급 peer 에게 권한 없는 추측이다.
- PyBaMM / MSMD / GH-MSMD 같은 P2D 는 물리 기반이라 envelope 외 extrapolation 의 유일한 정직한 도구지만, 파라미터 추정 (inverse problem) 의 identifiability + UQ 부담을 진다.

본인 작업의 시간 비중도 이 분할에 정합한다 — empirical 70%, EC model 30%.

## Decision

**측정 envelope 의 boundary 가 두 도구의 division line 이다.**

- **Envelope 안** (측정한 V·T 조건 사이의 보간) = **Empirical interpolation** (4번 트랙). 도구 = BDT 의 '승인 수명 예측' / '실수명 예측' 탭.
- **Envelope 외** (새 chemistry · 새 V·T 조건 · design 변경) = **EC model extrapolation** (5번 트랙). 도구 = PyBaMM main + House Code (MSMD/GH-MSMD) 고도화 발굴.

두 도구는 alternative 가 아니라 **complement**. 한 셀의 실사용 수명 frame = 두 도구의 union.

용어 정의는 [`wiki/CONTEXT.md`](../../CONTEXT.md) 참조.

## Consequences

**Positive**:
- 박사급 peer 가 도구 선택 근거를 즉시 이해 (envelope boundary 가 명시 division line).
- Cross-validation 자연 — envelope **안** 에서 두 도구 결과 일치 확인 시 envelope **외** extrapolation 신뢰의 anchor 가 됨.
- 도구 한계의 명시적 인정 (empirical 의 envelope 외 권한 없음) → epistemic humility = peer review 통과 가능성 ↑.
- 시간 70/30 분할이 도구 분할과 정합 → 작업 단위·청중·도구가 한 frame 으로 묶임.

**Negative**:
- BDT '실수명 예측' 탭 운영 시 envelope 추적이 부담 — 어느 점이 측정·보간·EC extrapolation 인지 시각 표시 필요 (UI 보강 작업).
- 신규 셀 도착 시 측정 envelope 새로 정의 → 두 도구 division line 재계산 필요.
- 사용자 (그룹원) 가 '실수명 예측' 탭 결과를 envelope 외에서도 신뢰하지 않도록 안내 필요.

**Neutral / follow-up**:
- 빅데이터 user 시나리오 (form factor 별 user 분포) — **(2026-05-02 해소)** flagship-only + FG 히트맵 + 2-bin cohort. CONTEXT.md Flagged #4 ✅.
- **측정 envelope 의 운영 정의 — [[0002-measurement-envelope-operational-definition|ADR-0002]]** 로 박힘 (T × V × 수명축, grid-only, similar-cell transfer).
- 5-3 (수명 시뮬 확장) 단계에서 NREL Smith 모델 도입 시 envelope 외 영역의 P2D + empirical-on-grid hybrid 구조 재검토 가능.
- BDT UI 에 envelope 시각 표시 기능 추가 (별도 ADR 후보 — ADR-0002 의 follow-up).
- **House Code (MSMD/GH-MSMD) 의 mechanical 모듈 cross-check** — D1 작업 시 즉시 확인. 확인 시 EC model capability 의 미발견 자산 발견 → 5번 트랙 substance 잠재 확장.
- **Empirical "extrapolation 금지" 의 strict 해석은 [[0003-functional-form-mediated-extrapolation|ADR-0003]] 으로 보강** — 학계 표준 functional form 위에서의 limited extrapolation 은 form-mediated 카테고리로 허용 (1000cy 측정 → 80% 도달 점 예측 등). raw extrapolation 은 여전히 금지.

## Alternatives considered

- **(a) Stochastic user profile 단독** — 빅데이터 user trace 만으로 모든 영역 cover. 측정 envelope 외에서 신뢰 안 됨, 박사급 peer 가 envelope 외 동작 즉 challenge. **Rejected**.
- **(b) Parametric V·T sweep 단독 (한 도구)** — empirical 한 도구로 모든 V·T 조건 fit. envelope 외 extrapolation 의 한계 무시 → epistemic 빈틈. **Rejected**.
- **(c) Hybrid surrogate × trace 적분** — parametric grid 가 surrogate, user trace 가 적용 path. 단일 frame 에 두 영역 흡수 시도. 박사급 peer 에게 도구 한계가 모호 (어느 영역이 측정 기반, 어느 영역이 물리 기반인지 흐림). **Rejected**.
