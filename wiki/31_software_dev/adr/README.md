# Architectural Decision Records (ADRs) — BDT

This folder holds the architectural decision records for **BDT 작업 전반** — 코드 (도구), 모델링 정책, 운영 정책 모두 포함.

> **Layout note** — Per BDT 3-layer policy, ADRs live under `wiki/31_software_dev/adr/`, not the conventional `docs/adr/`. `.md` 파일은 wiki/ 안에만 둔다 (cf. [`wiki/CLAUDE.md`](../../CLAUDE.md)).

> **Scope note** — 첫 README 는 "BDT codebase ADR" 로 좁게 시작했으나, 2026-05-02 ADR-0001 (lifetime-prediction-tool-split) 채택 시점부터 **모델링 정책 결정도 ADR 영역에 포함** 하도록 확장.

## Filename convention

```
0001-<slug>.md
0002-<slug>.md
...
```

- Sequential 4-digit numbers, no gaps. Allocate the next number when starting a new ADR.
- `<slug>` is a short kebab-case summary (e.g. `0001-lifetime-prediction-tool-split`).

## Body skeleton

```markdown
# ADR-NNNN — <decision title>

- Status: proposed | accepted | superseded by ADR-XXXX
- Date: 2026-MM-DD
- Deciders: <names or roles>

## Context

What problem are we facing? What constraints (regulatory, technical, organisational) bound the decision?

## Decision

What did we decide, in one or two sentences? Use the vocabulary from [`wiki/CONTEXT.md`](../../CONTEXT.md).

## Consequences

- Positive: …
- Negative: …
- Neutral / follow-up work: …

## Alternatives considered

- Option A — why rejected
- Option B — why rejected
```

## When to write an ADR

All three must be true:

1. **Hard to reverse** — database schema, file format, public API, modeling tool role.
2. **Surprising without context** — future reader/agent will wonder "왜 이렇게 했지?"
3. **Result of real trade-off** — genuine alternatives existed; specific reasons drove the pick.

Trivial choices ("renamed this function", "switched to f-strings") do not need an ADR. The bar is **"would I want to know *why* in six months?"**.

### What qualifies (BDT 측 examples)

- **Architectural shape** — 3-layer raw → wiki → docs schema (settled 2026-04-22).
- **Modeling tool roles** — empirical interpolation vs EC model extrapolation 분리 (ADR-0001).
- **Data format / encoding** — PNE `.cyc` vs CSV current encoding rule (rest-step difference).
- **DRM scope** — Fasoo / NASCA scope, where decryption is permitted.
- **Pipeline policy** — local-only OSS only (외부 API 금지).
- **Boundary decisions** — wiki/ ↔ docs/ ↔ raw/ 분리 룰.
- **Integration patterns** — BDT ↔ external sim tool (PyBaMM main + House Code 발굴 only).

### Trivial (skip)

- 함수 rename, f-string 전환, 한 줄 fix, 변수 이름 변경, 문서 typo.

## Numbering

Scan this folder for the highest existing number; increment by one.

## Existing ADRs

| # | Title | Status | Date |
|---|-------|--------|------|
| [0001](0001-lifetime-prediction-tool-split.md) | Lifetime prediction tool split — empirical interpolation vs EC model extrapolation | accepted | 2026-05-02 |
| [0002](0002-measurement-envelope-operational-definition.md) | Measurement envelope: operational definition (T × V × 수명축, grid-only, similar-cell transfer) | accepted | 2026-05-02 |
| [0003](0003-functional-form-mediated-extrapolation.md) | Functional form fit 기반 limited extrapolation 의 epistemic 권한 (form-mediated ≠ raw) | accepted | 2026-05-02 |
| [0004](0004-cell-design-to-p2d-parameter-mapping.md) | Cell design-to-P2D parameter mapping: 4 categories (Direct/Derived/Fit-driven/문헌) + physics-based transfer | accepted | 2026-05-02 |
| [0005](0005-bdt-dual-primary-user.md) | BDT primary user: 본인 + 그룹원 80명 양립 frame (Default/Advanced 분리 + 자동화 layer + 검증 게이트 2종) | accepted | 2026-05-02 |
| [0006](0006-reporting-format-core-and-appendix.md) | Reporting format: 핵심+appendix 청중/cadence 차등, AI/wiki/BDT = pptx components only (.md bullet + PNG + XLSX) | accepted | 2026-05-02 |
| [0007](0007-workflow-efficiency-pipeline.md) | Workflow efficiency: 1순위 (4)+(5) wiki↔보고 자동 연결 + 2순위 (2)+(3) BDT 분석 자동화. metric = 자동화/Re-use/Cognitive load↓ | accepted | 2026-05-02 |
| [0008](0008-bdt-test-and-study-automation.md) | BDT 자동화 테스트 + 스터디 자료 frame: 새 frame (pytest-qt/mpl/snapshot), 양립 1순위 동등, 4 fixture (α/β/γ/δ), dual-env | accepted | 2026-05-02 |
| [0009](0009-expert-level-code-and-study.md) | Python 비전문가의 전문가 수준 코드 + 스터디 frame: dataclass/Protocol/type hints + 학습 docstring 표준 + 4-layer 스터디 (P/Q/R/W) | accepted | 2026-05-02 |
| [0010](0010-mbo-track-mapping.md) | MBO Track Mapping: 5트랙→7트랙 재구조 + dual-credit 점수 룰 + 외부 frame 정합 (부서 KPI / 운영방향 / Simulation 고도화 TF main) + AX 듀얼 운영 (사외 LLM + 사내 Gauss) | accepted | 2026-05-04 |

### Future ADR seeds

- 3-layer raw → wiki → docs schema (retrospective — settled 2026-04-22, [`wiki/CLAUDE.md`](../../CLAUDE.md))
- PyBaMM main + House Code 고도화 발굴 (모델링 도구 운영 정책)
- PNE `.cyc` vs CSV current encoding rule (rest-step difference)
- Fasoo DRM scope (사내 환경만 decrypt)
- NASCA DRM scope
- Local-only pipelines (외부 API 금지)
