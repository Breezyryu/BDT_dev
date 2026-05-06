# ADR-0009 — Python 비전문가의 전문가 수준 코드 + 스터디 자료 frame

- Status: accepted
- Date: 2026-05-02
- Deciders: 본인 (선행배터리랩 「성능·수명 해석」 파트)
- Anchors: [[0005-bdt-dual-primary-user]], [[0007-workflow-efficiency-pipeline]], [[0008-bdt-test-and-study-automation]]

## Context

사용자 = Python 비전문가 (현재). 인계 자산 (`DataTool_optRCD_proto_.py`, 35K lines monolith, 221 functions/classes) 의 깊은 파악 + 적극 개선 진행 중 (506 commits in 3 months). 박사급 peer (CL3·CL4 과반) 청중 + ADR-0005 양립 frame.

이전 frame ([ADR-0008](0008-bdt-test-and-study-automation.md)): test 측 학습 docstring + 4 fixture + dual-env. 단 **production code 작성 frame 미정**.

**새 plan (2026-05-02)**: "Python 비전문가이지만, 전문가 수준으로 코드를 구현하고 스터디 자료를 제공하라". 즉:
- "비전문가 가독성" 이 frame X — 학습 cycle 의 일부로 **전문가 패턴 적극 사용**
- 코드 자체 = 학습 input
- 스터디 자료 = 비전문가가 전문가 수준 코드 이해 도구

박사급 peer 청중 측에서 단순 함수만 쓰면 코드 architecture 미흡. 전문가 패턴 (학계 / 오픈소스 = PyBaMM, NumPy, scikit-learn 수준) 적극 사용 + 학습 docstring + 자동 스터디 자료 양립 frame 명시 필요.

## Decision

BDT production code 작성 frame:

### (1) 코드 측 — 전문가 수준 패턴 적극 사용

**Best practice 패턴**:
- `@dataclass` (PEP 557) — spec table / config / 결과 묶음
- `Protocol` typing (PEP 544) — strategy / adapter interface
- Type hints (PEP 484, 585, 604) — 모든 public 함수 / 파라미터 / 반환
- `context manager` — resource / state
- `pathlib.Path` (vs `os.path` string)

**Python idiom**:
- list / dict comprehension (가독성 우선, nested 제한)
- generator (yield) — 큰 시퀀스 lazy
- decorator — `@property`, `@functools.cache`, custom
- f-string 표준
- walrus `:=` — 가독성 ↑ 시만

**Architecture pattern**:
- **Strategy** — view_mode (3 adapter), legacy_mode (5 callback)
- **Factory** — adapter / spec 인스턴스 생성
- **Adapter** — Toyo / PNE 데이터 abstraction
- **Observer / signal-slot** — Qt 의 표준 활용 ✓ 이미 사용

**학계 / OSS 표준 정합**:
- PyBaMM의 model class 구조 (parameters / variables / submodels)
- NumPy 의 vectorize / broadcasting
- scikit-learn 의 fit / transform / predict API

### (2) 학습 docstring 표준

모든 public 함수 / class / dataclass / Protocol 에 docstring:

```python
def example_function(...) -> ...:
    """한국어 한 줄 시나리오 요약.

    [Detail 학습용 — 비전문가 entry]
    배경: 도메인 / 사용 맥락 + 필요 사전 지식 (CONTEXT.md / wiki cross-link).
    입력: param 별 의미 / 단위 / 도메인 (4 카테고리 매핑 if applicable).
    출력: 반환 의미 / 단위.
    부작용: side effect (in-place / log / file 등).

    [전문가 frame — 패턴 인용]
    패턴: Strategy / Factory / Protocol 등.
    학계 reference: 관련 논문 / docs URL.

    [참조]
    - ADR-XXXX (관련 결정)
    - wiki/<topic>/<note>.md (deep-dive)
    """
```

### (3) 스터디 자료 4-layer 결합 (S)

**Layer P** — Inline docstring (위 표준)
**Layer Q** — Test docstring (ADR-0008 (2)+(5) 정합)
**Layer R** — 자동 생성:
- `pdoc` 또는 `sphinx` — 코드 → HTML / PDF auto-doc
- `pytest --collect-only` → `wiki/31_software_dev/test_index.md`
- `wiki/31_software_dev/study/<module>.md` — module 별 학습 노트 (자동 stub + 수동 보강)
**Layer W** — Wiki 직접 노트:
- `wiki/19_bdt_history/learning/<topic>.md` — 학습 cycle 노트
- ADR cross-link / 학계 reference 풀

### (4) Code → Test → Study 연결 cycle

```
Production code (전문가 패턴 + 학습 docstring)
        ↓ [pytest]
Test (학습+QA 양립, ADR-0008)
        ↓ [pytest --collect-only + custom script]
test_index.md (wiki 자동 생성)
        ↓ [본인 보강]
study/<module>.md (학습 노트 + 구조도 + 예제)
        ↓
ADR cross-link / 학계 reference (CONTEXT.md / 30_modeling/)
```

ADR-0007 의 (4)+(5) + ADR-0008 의 (5) 의 production code 측 specialization.

## Consequences

**Positive**:
- Production code 자체 = 학습 cycle 의 input
- 박사급 peer 측 코드 가독성 ↑↑ — 학계/OSS 표준 패턴
- ADR-0005 (6) 문서 layer specialization (test + production 모두)
- ADR-0008 의 test 측 frame + ADR-0009 의 production 측 frame = 코드 전체 학습 / QA 양립
- 6개월~1년 후 본인 전문가 수준 도달 — frame 자체가 learning trajectory
- 그룹원 측 코드 가독성 ↑ (전문가 패턴 표준이면 검색 / 학습 source 풍부)

**Negative**:
- 코드 작성 부담 ↑ (dataclass / Protocol / 학습 docstring boilerplate)
- 비전문가 학습 cost — 단기 작업 속도 ↓
- 35K monolith 의 점진 정정 부담 (기존 코드도 frame 적용 시 대규모 변경)
- pdoc / sphinx 등 자동 doc 도구 도입 부담
- Type hints 정합 부담 (PyQt6 의 typing stub 정합 필요 — typing-stub 패키지 활용)

**Neutral / follow-up**:
- **학습 docstring template** 정의 — `wiki/99_templates/docstring_template.md` 후보
- pdoc / sphinx 도입 — 별도 작업
- Type hints 점진 정합 — 새 코드부터 적용 (mypy 의존성 추가 후보)
- 기존 35K monolith 의 frame 적용은 **점진** — C3~C5 deepening 진행 시 자연 흡수
- 학계/OSS 표준 reference 매핑 표 — 별도 wiki 노트 (`wiki/31_software_dev/oss_reference_patterns.md` 후보)

## Alternatives considered

- **단순 함수 + 비전문가 친화 (이전 frame, ADR-0008 의 scope 함의)** — 학습 정체. 박사급 peer 측 코드 가독성 한계. **Rejected**.
- **전문가 수준 only (스터디 자료 X)** — 비전문가 진입 장벽. 학습 cycle 운영 어려움. **Rejected**.
- **ADR-0008 amendment** — scope 가 test 측만 (production 미포함). 새 ADR 분리가 layer 명료. **Rejected**.
- **CONTEXT.md entry 만 — ADR 미작성** — frame scope 가 모든 production code 에 영향. ADR 가치 큼. **Rejected**.
