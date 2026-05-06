# ADR-0005 — BDT Primary user: 본인 + 그룹원 80명 양립 frame

- Status: accepted
- Date: 2026-05-02
- Deciders: 본인 (선행배터리랩 「성능·수명 해석」 파트)
- Anchors: [[0001-lifetime-prediction-tool-split]], [[0002-measurement-envelope-operational-definition]], [[0003-functional-form-mediated-extrapolation]], [[0004-cell-design-to-p2d-parameter-mapping]]

## Context

배터리데이터툴 (BDT) 의 사용자 정의가 표류 중. 이전 frame (메모리 [`user_profile.md`](C:/Users/Ryu/.claude/projects/c--Users-Ryu-battery-python-BDT-dev/memory/user_profile.md), [`CONTEXT.md`](../../CONTEXT.md) BDT 9 탭 entry) 은 그룹원 80명 측 강조 — 새 plan (2026-05-02) 은 본인 power user 측 균형. 사용자 명시: "그룹원 제공도 목표지만, **내가 제일 잘 활용하고자 함**" — 양립.

운영 기준이 미정이면 매 기능 추가·UI·성능·보고 결정마다 case-by-case 판정 부담 + 본인 측 (박사급 peer 보고) 과 그룹원 측 (저사양 노트PC + 단순 UX) 이 의도치 않게 충돌.

git log 증거: 2026-02-01 ~ 현재 506 commits, 일 5~6 commits 의 power user iterative 개선 패턴 — 본인 측 활용 강도 강함. 동시에 그룹원 80명 배포 사실은 변하지 않음.

박사급 peer (CL3·CL4 과반) 보고 + 그룹원 80명 노트PC 사용 = 두 측 모두 충족하는 운영 frame 의 명시 필수.

## Decision

BDT 의 primary user = **본인 + 그룹원 80명 양립**. 양립은 두 측 모두 primary 라는 의미이며, 두 측 동시 만족 압력을 의식적으로 frame 으로 처리한다.

### 양립 운영 기준 (6 항목)

**(1) Default + Advanced 분리**
- **Default mode** = 그룹원 친화 — 옵션 최소, 안정 default 값, UI 단순화
- **Advanced mode** = power user — 옵션 풀 노출, 본인 분석 흐름 자동화
- 같은 GUI 안에 토글 / 메뉴 / progressive disclosure 로 분기
- 신규 기능 = default 측에 안정 default 정의 + advanced 측에 옵션 풀 노출 양 측 모두 design

**(2) 자동화 layer 분리**
- **GUI** = 두 측 공통 entry (그룹원 + 본인 모두 사용)
- **Script / CLI / batch entry** = 본인 전용 power user 자동화 layer (GUI 와 분석 core 함수 공유)
- 같은 core 함수를 두 entry 가 호출하면 양립 보장 + 코드 중복 ↓

**(3) 기능 추가 시 검증 게이트 2종**
- **(a) 본인 회귀 검증** ([reference_cycle_regression_validator](C:/Users/Ryu/.claude/projects/c--Users-Ryu-battery-python-BDT-dev/memory/reference_cycle_regression_validator.md)) = **1순위** — 본인 분석 케이스 통과
- **(b) 그룹원 smoke test** = **2순위** — 그룹원 사용 패턴 (단순 default flow + 저사양 PC 환경) 통과
- **두 측 모두 통과해야 release**. 한 측만 통과 시 hold + 부족 측 보강.

**(4) 성능 baseline 양 측**
- **본인 PC** = primary 측정 (개발 환경, 빠른 iteration)
- **그룹원 노트PC (저사양)** = secondary baseline (acceptable 기준 별도 정의 — 예 cycle 분석 50채널 < 30s)
- **양 측 모두 acceptable 한 성능만 release**. 본인 PC 만 빠르고 그룹원 측 비현실적 시 hold.

**(5) 보고 source**
- **본인 보고 (박사급 peer + 그룹장)** = 1순위 출력 — ADR-0001~0004 frame 적용 (envelope 시각화 + form-mediated UQ + 4 카테고리 매핑 표시)
- **그룹원이 자기 보고에 활용** = secondary — 같은 출력 form 재사용 (포맷 정합 확보)

**(6) 문서 / 가이드 layer 분리**
- **본인 작업 노트** (`wiki/19_bdt_history`, `wiki/30_modeling`, ...) = 1순위 — 박사급 peer 청중 정합
- **그룹원용 사용 가이드** (`wiki/19_bdt_history/SOP_bdt_user_guide.md` 후보) = 2순위 — 정기 업데이트, default mode 측 사용 흐름 위주
- ADR / CONTEXT.md / 학계 reference 노트 = 본인 측 (그룹원 비공개 OK)

### 양립 우선순위 충돌 시 판정

기능이 본인 측 ↔ 그룹원 측 양립 불가 (예: 본인만 가능한 power user 자동화) 일 때:
- (a) Default + Advanced 분리로 처리 가능 → (1) 적용, 양립 유지
- (b) 분리 어려움 → 본인 측 기능을 별도 entry (Script / CLI / batch) 로 격리 → (2) 적용, GUI 측 양립 유지
- (c) 그래도 분리 불가 → ADR-0005 amendment / case-by-case ADR 판정

## Consequences

**Positive**:
- 두 측 청중 모두 만족 frame — 박사급 peer 보고와 그룹원 사용 양 측에 정합
- 기능 priority 결정의 case-by-case 부담 ↓ — 6 운영 기준이 anchor
- "Default + Advanced 분리" + "자동화 layer 분리" 가 power user vs 단순화 trade-off 를 design pattern 으로 처리 — 양립이 trivial 하지 않다는 인정 위에 구축
- 검증 게이트 2종 = release 품질 안정 (한 측만 통과로 release 안 됨)
- ADR-0001~0004 의 박사급 peer 청중 측 frame 위에 ADR-0005 가 그룹원 layer 추가 → **5 ADR layer 운영**

**Negative**:
- 모든 기능 추가에 그룹원 UX 검증 필수 → development time ↑
- Default + Advanced 분리 + 자동화 layer 분리는 코드 구조 부담 ↑ (signature design 신중)
- 그룹원 smoke test 환경 / baseline 별도 운영 부담
- 두 측 측정 동시 만족 못하는 기능의 case-by-case 판정 부담 (위 "양립 우선순위 충돌" 항)

**Neutral / follow-up**:
- **그룹원용 사용 가이드 wiki 노트 신규** — `wiki/19_bdt_history/SOP_bdt_user_guide.md` 또는 별도 위치
- **그룹원 smoke test baseline 정의** — 본인 작업 진행 시 cycle 분석 등 typical case 의 acceptable 기준 정량
- **Default + Advanced 토글 UI 패턴** — BDT 9 탭에 점진 도입 (1주 작업의 사이클 / 프로파일 / 현황 탭 기능 추가 시 자연 흡수)
- **ADR-0005 의 (3) 검증 게이트** 와 [`tier2_validate.py`](tools/tier2_validate.py) / `tools/test_code/` 의 통합 — 본인 회귀 검증 + 그룹원 smoke test 의 자동화 pipeline 후보

## Alternatives considered

- **(A) Primary = 본인 단독, Secondary = 그룹원 (후속 cherry-pick)** — 운영 단순. 단 그룹원이 사용 못 하면 인계 자산의 가치 ↓ + 그룹장 보고 시 "그룹원 활용도?" 즉 challenge 영역. **Rejected**.
- **(C) Primary = 그룹원 단독, 본인 = 우연 1차 사용자** — 본인 power user 자동화 부담. 박사급 peer 보고 자료 만들기 어려움. git log 506 commits 패턴과 부정합. **Rejected**.
- **CONTEXT.md entry 만 — ADR 미작성** — 운영 frame 결정의 hard-to-reverse + surprising + real trade-off 모두 충족 → ADR 가치 큼. **Rejected**.
- **양립 운영 기준 미정의 (단순 "양립" 만 명시)** — 두 측 동시 만족이 trivial 하다는 가정. 실제 case-by-case 판정 부담 ↑. **Rejected**.
