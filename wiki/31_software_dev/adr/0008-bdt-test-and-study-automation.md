# ADR-0008 — BDT 자동화 테스트 + 스터디 자료 frame: 새 frame, 양립 1순위 동등, 4 fixture, dual-env

- Status: accepted
- Date: 2026-05-02
- Deciders: 본인 (선행배터리랩 「성능·수명 해석」 파트)
- Anchors: [[0005-bdt-dual-primary-user]], [[0007-workflow-efficiency-pipeline]]

## Context

ADR-0005 (3) 검증 게이트 2종 (본인 회귀 + 그룹원 smoke) 과 ADR-0007 의 (2)+(3) BDT 분석 자동화 2순위 의 운영 layer 가 미정.

**기존 자산 발견 (2026-05-02)**: `tools/test_code/` 에 20+ test 모듈 + `conftest.py` + fixture 데이터 (`test_data_accel.sch`, `test_data_gitt.sch`) 존재. 단 사용자 인지도 = **"몰랐음"** — 작성자가 본인 X (전임자 / 이전 시점 Copilot 등 추정). 즉 기존 자산이 본인 frame 과 정합 X.

**추가 제약**:
- 사용자 = **Python 비전문가** — 35K lines monolith (`DataTool_optRCD_proto_.py`, 221 top-level functions/classes) 의 본인 파악 부담 강함
- Test 의 1차 사용자 양립 — **본인 학습 도구 + release QA 동등 1순위**
- 환경 dual:
  - **사외 PC** (현재 작업 환경, AI 가능, 일부 fixture 데이터만)
  - **사내 PC** (AI 금지, 풀 fixture 데이터)

**매번 시간 소비 영역 (사용자 명시)**: 데이터 경로 입력 / 전처리 확인 / 그래프 확인 / 저장 데이터 확인 — 4 fixture 자동화로 직접 매핑.

## Decision

### (1) Test frame 새 frame 채택

기존 `tools/test_code/` 20+ 자산은 **reference 로만**, 새 frame 으로 처음부터 구축:
- **pytest-qt** 기반 PyQt6 UI test 표준화
- **pytest-mpl** (matplotlib image regression)
- **pytest-snapshot** (data regression — 전처리 결과 baseline diff)
- `conftest.py` 에 standard 4 fixture
- `test_<module>_<scenario>.py` 명명 + 학습-친화 docstring 표준

기존 자산은 reference / migration source — 점진 deprecate 또는 새 frame 으로 흡수.

### (2) 1차 사용자 양립 (R)

Test 자체가 학습 도구 + QA 동시:
- **학습 측**: test name = 한국어 시나리오 ("Toyo PNE 이종 사이클러 → 사이클 분석 → dQdV 출력"), docstring = 도메인 매핑 + 동작 흐름 + ADR cross-link
- **QA 측**: pytest auto-trigger (pre-commit / 정기 / release 게이트), fail-fast, conftest.py 의 standard error message

**Priority trade-off** (양립 1순위 동등이지만 작업 단계별):
- **인계 / 학습 단계** (현재) = 학습 우선 — slow test, verbose docstring, `@pytest.mark.learning` 허용
- **Release / 정기 단계** (안정 후) = QA 우선 — fast test, `@pytest.mark.slow` 분리, CI 적용

### (3) 4 Fixture 표준 — 병목 4개 직접 매핑

| Fixture | 정의 | 도구 / 형식 |
|---------|-----|-----------|
| **(α) 표준 데이터 경로** | conftest.py 의 PNE / Toyo / 자주검증 sample 경로 fixture | `@pytest.fixture(scope="session")` |
| **(β) 전처리 골든 레퍼런스** | 표준 fixture 의 전처리 결과 baseline | parquet / pickle / pytest-snapshot |
| **(γ) 그래프 골든 image** | 표준 fixture 의 그래프 출력 baseline PNG | pytest-mpl `@pytest.mark.mpl_image_compare` |
| **(δ) 저장 데이터 schema** | 출력 파일 (csv/xlsx/png) 의 필드·dtype·범위 자동 체크 | tools/schema_verify.py 통합 |

→ 본인 매번 검증 시간 ↓↓ — 코드 변경 후 `pytest` 한 번에 4 측 모두 검증.

### (4) Dual-environment fixture 운영

```
사외 PC (현재 작업, AI 가능, subset 데이터)
    │
    ├── conftest.py 의 subset fixture (test_data/sample/ in-repo)
    ├── 학습 + 빠른 iteration 측
    └── 신규 test 작성 + 1차 검증
                │
                ↓ git push
                │
사내 PC (AI 금지, full 데이터)
    │
    ├── conftest.py 의 full fixture (실제 시험 데이터, 자주검증, 협력사)
    ├── Release / 정기 QA 측
    └── 사외 작성 test 가 사내에서도 정합 동작
```

ENV var (`BDT_TEST_ENV=local|office`) 또는 conftest.py fixture chain 으로 분기.

### (5) 스터디 자료 자동화 (Python 비전문가용)

각 test 모듈의 **docstring + test name** 이 도메인 매핑 source. 자동 wiki ingest:
- `pytest --collect-only` 출력 → `wiki/31_software_dev/test_index.md` (자동 생성, 분기별 갱신)
- Test docstring + ADR cross-link → `wiki/31_software_dev/study/<module>.md` (test 모듈 별 학습 노트)
- BDT 9 탭 별 test mapping 표 → `wiki/CONTEXT.md` 의 BDT 인계 자산 entry 보강

ADR-0007 의 (4) wiki ingest 자동 연결 pipeline 의 specialization.

### (6) 검증 게이트 운영 (ADR-0005 (3) specialization)

```
git commit 시도
    ↓
pre-commit hook (선택, 후속 작업)
    ↓
[게이트 1: 본인 회귀 (1순위)]
  pytest -m "not slow and not office_full" → 사외 subset 빠른 검증
    ↓ pass
[게이트 2: 그룹원 smoke (2순위)]
  pytest tools/test_code/test_smoke_gui.py + exe smoke (PyInstaller 산출물)
    ↓ pass
git commit 허용
```

Release 시 사내 PC 에서 `pytest -m "office_full"` 추가 — 풀 fixture QA.

## Consequences

**Positive**:
- ADR-0005 의 (3) 검증 게이트 2종 운영 layer 명료
- 4 fixture = 매번 시간 소비 4 영역 자동화 ↓↓
- Dual-env 운영 = 사외/사내 환경 분리 + 정합 (memory `project_office_pc_no_ai.md` 정합)
- Test = 학습 도구 + QA — 두 측 동시 만족
- 35K monolith 의 점진 학습 도구 — test docstring + collect 결과가 자동 wiki 로
- 박사급 peer 보고 시 "이 결과의 검증 chain 어디?" challenge 에 즉시 답 (test path + fixture name)

**Negative**:
- 기존 `tools/test_code/` 20+ 모듈 deprecate 부담 (또는 점진 흡수 부담)
- pytest-qt / pytest-mpl / pytest-snapshot 등 신규 의존성 추가
- 학습 측 docstring 작성 부담 (한국어 시나리오 + ADR cross-link)
- Dual-env conftest 운영 부담 — ENV var 분기 + fixture override 정합

**Neutral / follow-up**:
- 기존 test_code/ 의 fixture 데이터 (`test_data_*.sch`) 는 신규 conftest 로 흡수
- pre-commit hook (autohook / pre-commit framework) 구축 — 후속 작업
- **35K monolith 의 점진 모듈 분리** (improve-codebase-architecture skill 영역) — test 의 unit boundary 가 자연스럽게 모듈 분리의 anchor 가 됨. 별도 grill 후보.
- 사내 PC 에서 풀 fixture 운영 시 보안·데이터 권한 규정 cross-check 필요
- ADR-0007 의 (4)+(5) wiki ↔ 보고 자동 연결의 component source — γ (그래프 골든 image) 가 docs/*.png 자연 source

## Alternatives considered

- **(A) 기존 위에 빈틈 메우기** — 20+ 모듈 활용. 사용자가 기존 자산 미인지 + frame 정합 X 판정. **Rejected**.
- **(C) 하이브리드 (기존 = 본인 회귀, 신규 = 그룹원 smoke + exe + 스터디)** — 두 layer 분리 운영 부담, frame 흐림. **Rejected**.
- **단일 환경 fixture (사외 only)** — 사내 PC 운영 (실제 데이터) 측 무시. 인계 자산의 본격 검증 어려움. **Rejected**.
- **학습 측 docstring 미요구 (QA only)** — Python 비전문가 + 35K monolith 파악 부담 무시. ADR-0005 양립 frame 의 (6) 문서 layer 위반. **Rejected**.
- **CONTEXT.md entry 만 — ADR 미작성** — frame 결정의 hard-to-reverse + surprising + trade-off 충족 → ADR 가치 큼. **Rejected**.
