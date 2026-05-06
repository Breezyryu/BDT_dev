# ADR-0007 — Workflow efficiency: pipeline automation (4→5) + BDT analysis (2+3) + cognitive load ↓

- Status: accepted
- Date: 2026-05-02
- Deciders: 본인 (선행배터리랩 「성능·수명 해석」 파트)
- Anchors: [[0001-lifetime-prediction-tool-split]], [[0005-bdt-dual-primary-user]], [[0006-reporting-format-core-and-appendix]]

## Context

새 plan: "내 업무 flow 효율화". ADR-0001~0006 + CONTEXT v2 의 frame 잡힌 다음 단계 = pipeline 자동화.

업무 flow 단계 (6 단계):
1. 데이터 receiving (외부, 효율화 어려움)
2. BDT 입력·전처리
3. 분석 (empirical / P2D / 양음극 분리 등)
4. wiki ingest (분석 결과 + 학습 + frame)
5. 보고 component (bullet .md + PNG + XLSX, ADR-0006)
6. pptx 수동 조립 (ADR-0006 명시, 효율화 대상 X)

**병목 진단**:
- **1순위** = (4) wiki ingest + (5) 보고 component 의 **자동 연결 부재** — "분석 → 보고" critical path
- **2순위** = (2)+(3) BDT 분석 자동화 (이미 506 commits 자체 progress 중)

**Metric 선택**:
- input 지표 = (b) 자동화 + (d) Re-use + (e) cognitive load ↓ — 직접 control 가능
- 결과지표 = (a) 시간 단축 — input 지표 control 시 자연 도출

박사급 peer (CL3·CL4 과반) 청중 + ADR-0001~0006 frame 위에서 본인 1주 단위 작업 사이클이 안정 운영되려면 (4)+(5) 의 자동 연결 mechanism 필요.

## Decision

업무 flow 효율화 정책:

### 1순위 — (4) wiki ingest + (5) 보고 component 의 자동 연결 pipeline

```
[BDT 분석 결과 (in-memory)]
        ↓ auto-export
[docs/*.png (시각화) + docs/*.xlsx (표)]
        ↓
[wiki/ .md (bullet 텍스트)]   ← cadence 별 템플릿 적용
        ↓
[wiki/40_work_log/YYMMDD_<cadence>_<topic>.md]
        ↓ (본인 수동 조립 — ADR-0006)
[docs/*.pptx]
```

**구체 작업 (follow-up backlog)**:
- **`wiki/99_templates/` — cadence 별 bullet .md 템플릿 신규 (3 종)**:
  - `template_groupleader_8w.md` (그룹장 8주, 3~5 슬라이드 KPI+detail)
  - `template_techmeeting_6m.md` (테크미팅 6개월, 3~5 슬라이드 결과+풀 appendix)
  - `template_weekly_3m.md` (주간그룹공유 3개월, 3~5 highlight)
  - 템플릿 = 슬라이드 단위 .md skeleton + bullet 형식 + ADR cross-link footer + 학계 reference footer
- **BDT 시각화 출력 → docs/*.png 자동 저장** 기능 추가 (1주 작업 후속)
- **분석 결과 → wiki ingest 표준 form** — 분석 함수 별 (사이클 fit / P2D 시뮬 / 양음극 분리) ingest stub 자동 생성

### 2순위 — (2)+(3) BDT 분석 자동화 (self-progress 보강)

506 commits 자체 progress. 추가 효율화:
- **회귀 검증 자동화** — [reference_cycle_regression_validator](C:/Users/Ryu/.claude/projects/c--Users-Ryu-battery-python-BDT-dev/memory/reference_cycle_regression_validator.md) + ADR-0005 의 (3) 게이트 통합. `tools/tier2_validate.py` 와 통합 후보.
- **분석 batch entry (Script / CLI)** — ADR-0005 의 (2) 자동화 layer specialization. 본인 power user 측.

### Metric (input 지표 — 직접 control)

| 지표 | 정의 | 측정 |
|------|------|------|
| **자동화 비율** | 반복 작업의 script / pipeline 화 정도 | self-audit (매월) |
| **Component re-use 횟수** | 같은 PNG / .md / .xlsx 의 cadence 간 재사용 | 보고 deck 별 reference 카운트 |
| **Cognitive load** | 새 분석 시 mental overhead | 정성적 self-report |

결과지표 (시간 단축) 은 input 지표 control 시 자연 도출 — 직접 측정은 보조.

### 효율화 안티패턴 (금지)

- **One-off scripting 누적** — 매번 분석마다 ad-hoc 코드, 재사용 X. Component re-use frame 으로 처리.
- **wiki ingest 의 retroactive 작성** — 분석 후 며칠/주 뒤 ingest. Pipeline 으로 즉시 처리.
- **PPT 자동 조립 시도** — ADR-0006 명시 금지.
- **그룹원 측 ignored** — ADR-0005 양립 frame 위반. 효율화 작업도 (3) 검증 게이트 2종 적용.

## Consequences

**Positive**:
- "분석 → 보고" critical path 단축
- Re-use 가능한 component 누적 → 다음 cadence / 분석에서 자연 활용
- Cognitive load ↓ — frame 잡혀 있어 새 분석 시 mental overhead ↓
- ADR-0001~0006 frame 의 운영 specialization (effort 어디 투입할지 명료)

**Negative**:
- Pipeline 구축 초기 부담 — `wiki/99_templates` 작성, BDT PNG 자동 저장 기능 추가
- Component re-use 의 정합 부담 (어느 분석 결과가 어느 슬라이드 component 인지 매핑)
- 회귀 검증 자동화 부담 (ADR-0005 (3) 게이트의 운영 layer)

**Neutral / follow-up**:
- **`wiki/99_templates/` bullet .md 템플릿 3 종** 작성 — 1주 작업의 보고 측 자연 흡수
- **BDT 시각화 자동 저장 기능** — 1주 작업 후속 (ADR-0006 follow-up)
- **ADR-0005 (3) 게이트 자동화** — `tools/test_code/` 와 통합 후보
- **효율화 metric 의 정량 measurement** — 추후 정기적 self-audit (예: 매월 work_log 에 효율화 지표 1줄)

## Alternatives considered

- **(2)+(3) BDT 분석 자동화 1순위** — 506 commits 자체 progress 라 (4)+(5) 가 더 critical 한 병목. **Rejected**.
- **(a) 시간 단축 metric 1순위** — 결과지표라 직접 control 어려움. input 지표가 효율 control 측에 적합. **Rejected**.
- **수동 운영 유지 (효율화 정책 X)** — frame 잡혀 있어도 매번 ad-hoc 작성, 재사용 ↓. 본인 시간 부담 누적. **Rejected**.
- **CONTEXT.md entry 만 — ADR 미작성** — 사용자 yes 명시. 운영 정책 박제. **Rejected**.
