# ADR-0011 — Personal layer (daily/weekly) + Evaluation layer (quarterly MBO) — weekly = single source-of-truth

- Status: accepted
- Date: 2026-05-04
- Deciders: 본인 (선행배터리랩 「성능·수명 해석」 파트) — `/grill-with-docs` 세션 결과
- Anchors: [[0006-reporting-format-core-and-appendix]], [[0007-workflow-efficiency-pipeline]], [[0010-mbo-track-mapping]]

## Context

ADR-0006 (청중·cadence 차등 보고) + ADR-0007 (6단계 업무 flow + (4)+(5) 자동 연결 1순위 병목) 가 보고 component 측을 frame했지만, **(4) wiki ingest 의 sub-cadence (일·주 단위 working memory)** 와 **분기 MBO 수시피드백** 의 운영이 미정의.

기존 ADR frame 의 cadence:
- 그룹장 보고 (8주) / 테크미팅 (6개월) / 주간그룹공유 (3개월) — 모두 외부 청중 측
- (4) wiki ingest = "분석 후 즉시 ingest, retroactive 작성 금지" 정책만 있음, 구체 운영 미정의

신규 운영 요구:
1. **본인 working memory** — "내가 한 일을 내가 파악" 하기 위한 일·주 단위 self-tracking
2. **분기 MBO 수시피드백** — 1Q/2Q/3Q/4Q 평가 시 input source 로 활용할 자료. mbo_2026.md + ADR-0010 7트랙 매핑 갱신 동반

박사급 peer 빈틈 금지 + 청중 3계층 압축률 분리 ([[feedback_substance_audience]]) frame 위에서, **personal layer (일·주) → public layer (8주/3개월/6개월) → evaluation layer (분기)** 로 운영을 specialization.

## Decision

### 1. 5-layer cadence pipeline (ADR-0006 frame 위 확장)

```
[git commit + 대화 컨텍스트 + 비-commit 메모 (ECT 등)]
       ↓ (작업 있는 날만, 사용자 자연어 트리거)
[데일리 워크로그]   ← raw, 영구 보존 (working artifact)
       ↓ (매주 금요일, 사용자 자연어 트리거)
[위클리 로그]       ★ source-of-truth (working artifact, 영구)
       ↓ 청중·cadence 별 view 파생
       ├→ [그룹장 보고 8w]    = 위클리 8개 + 마일스톤 헤더 + bullet 가공
       ├→ [그룹원 공람 3m]   = 위클리 12개 + highlight 압축
       ├→ [테크미팅 6m]      = 위클리 24개 + 풀 appendix
       └→ [MBO 분기 수시피드백] = 위클리 12개 + ADR-0010 7트랙 매핑 → mbo_2026.md 갱신
                                  + 별도 review 노트
       ↓ (본인 수동 조립 — ADR-0006)
[docs/*.pptx] (그룹장·테크미팅·그룹공유 측만)
```

### 2. Layer 별 운영 정책

| Layer | Cadence | 주체·청중 | 역할 | 형식 |
|---|---|---|---|---|
| 데일리 워크로그 | 매일 (작업 있는 날만) | 본인 | (4) wiki ingest 의 raw 일별 흡수 | 자유 형식 (TL;DR + 그룹별 디테일) |
| 위클리 로그 | 매주 금요일 | 본인 | source-of-truth, 데일리 합산 + 인덱스 | 자유 형식 (working memory) |
| 그룹장 보고 | 8주 (ADR-0006) | 그룹장 (상무) | KPI 1슬라이드 + detail 2~4슬라이드 | bullet .md (ADR-0006) |
| 그룹원 공람 | 3개월 (ADR-0006) | 80 그룹원 + 랩장·그룹장 | 3~5 highlight | bullet .md (ADR-0006) |
| 테크미팅 | 6개월 (ADR-0006) | 박사급 peer + 일반 동료 | 결과 + 풀 appendix (박사급 standard) | bullet .md (ADR-0006) |
| MBO 분기 수시피드백 | 분기 (3개월) | 평가 시스템·HR | mbo_2026.md 갱신 + review 노트 | 자유 형식 + KPI 표 |

### 3. 파일명 컨벤션 (ADR-0006 의 `YYMMDD_<cadence>_<topic>.md` 정합)

```
wiki/40_work_log/
├── 260504_daily_worklog.md            ← 데일리 (오늘 인스턴스)
├── 260505_daily_worklog.md
├── 260508_W19_weekly_log.md           ★ 매주 금요일 source-of-truth
├── 260515_W20_weekly_log.md
├── 260612_W24_groupleader_8w.md       ← 8주 cadence 도달 시 (그룹장)
├── 260612_W24_weekly_3m_share.md      ← 3개월 cadence (그룹원 공람)
├── 260901_W36_techmeeting_6m.md       ← 6개월 cadence (테크미팅)
├── 260331_Q1_mbo_review.md            ← 분기 MBO 수시피드백 review 노트
└── mbo_2026.md                        ← 분기마다 갱신 (살아있는 문서)
```

### 4. 데일리 → 위클리 합산 정책

- **트리거**: 사용자 자연어 ("이번 주 위클리 정리해줘") → Claude 가 그 주 데일리 + git log + 대화 메모리 합산
- **위클리 본문 구성** (자유 형식이지만 권장):
  - TL;DR (3~5 bullet)
  - 영역별 (BDT / 사이클 / 모델링 / 측정 / AI TF / ECT 등) commit·작업 흐름표
  - 데일리 노트 링크 인덱스
  - 다음 주 후속 작업 후보
- **데일리 보존 정책**: 위클리 합산 후에도 데일리 영구 보존. 위클리는 본문 + 링크 둘 다 가짐

### 5. 위클리 → 보고자료 view 파생 정책

- **그룹장 보고 (8주)**: 위클리 8개 본문 → bullet 가공 + KPI 슬라이드 (마일스톤 헤더). 마일스톤은 [[mbo_2026]] + ADR-0010 7트랙 매핑에서 추출
- **그룹원 공람 (3개월)**: 위클리 12개 → 3~5 highlight 압축. 청중 80명 cognitive bandwidth 고려
- **테크미팅 (6개월)**: 위클리 24개 → 결과 슬라이드 + 풀 appendix. 박사급 peer standard ([[feedback_substance_audience]] 4종 set: 가정·UQ·검증·한계)
- **누락 주 처리**: 빈 주는 "(없음)" 또는 직전 주에 흡수. retroactive 위클리 작성 금지

### 6. 위클리 → MBO 분기 수시피드백 절차

```
[그 분기의 위클리 12개]
        ↓ ADR-0010 7트랙 매핑 적용
[트랙별 진척률·산출물·KPI 매핑 표]
        ↓
        ├→ [mbo_2026.md 갱신] (살아있는 문서)
        └→ [YYMMDD_Q{n}_mbo_review.md] (review 노트, 평가 input)
```

- **MBO 갱신 항목**: 1.1 Project 결과 / 1.2 Project 혁신 / 2.1 AX 성과 / 2.2 특허 / 3.1 TF / 4.1 역량강화
- **트랙 dual-credit 룰**: ADR-0010 § "MBO 점수 비중" 그대로 (예: 4번 트랙 deliverable 이 1.1 + 1.1.2 도전 동시 점수)

### 7. 자동화 트리거 정책 (ADR-0007 정합)

- **사용자 자연어 트리거 only.** Cron / scheduled wakeup 안 함.
- 데일리: "오늘 한 일 정리해줘" → Claude 가 git log + 대화 메모리 + 사용자 직접 입력 (예: ECT 같은 비-commit 작업) 합산
- 위클리: "이번 주 위클리 정리해줘" → Claude 가 그 주 데일리 + git log 합산
- 보고자료: "8주차 그룹장 보고 만들어줘" / "3개월 그룹원 공람 만들어줘" / "6개월 테크미팅 만들어줘" → Claude 가 해당 cadence 위클리 합산 + 청중별 view 가공
- MBO: "Q1 MBO 수시피드백 작성해줘" → Claude 가 분기 위클리 12개 + ADR-0010 매핑 + mbo_2026.md 갱신

### 8. 휘발 정책

- **데일리·위클리 모두 영구 보존.** 분기 MBO 작성 시 디테일 source 로 사용 가능.
- 위클리는 데일리 링크 인덱스 + 본문 모두 가짐 — 보고자료 작성 시 위클리 한 곳만 보면 되고, 깊이 들어갈 때 데일리 진입.

## Consequences

**Positive**:
- "분석 → 보고" critical path (ADR-0007 1순위 병목) 의 sub-cadence 가 명료. 일·주 단위 ingest layer 정책 박제.
- 위클리 = single source-of-truth → 보고자료 4종 (그룹장·그룹원·테크·MBO) 모두 같은 source 에서 view 파생. 정합성 확보.
- ADR-0006 의 청중 3계층 + ADR-0010 의 7트랙 매핑이 분기 MBO 작성 시 자연스럽게 통합.
- 자연어 트리거 → cron 의존 없음. 사용자 통제권 유지.
- 데일리·위클리 영구 보존 → 분기 회고 시 디테일 복원 가능 (ADR-0007 cognitive load metric 측정 자료).

**Negative**:
- 영구 보존이 wiki 노트 수 증가 (연 ~250 데일리 + ~50 위클리 + ~6 그룹장 + ~4 그룹원 + ~2 테크 + ~4 MBO ≈ 320 노트/년). Obsidian 검색·태그로 관리.
- 사용자 트리거 의존 → 위클리 빠뜨림 시 분기 MBO 정확도 ↓. 매주 금요일 routine 화 필요.
- 보고자료 cadence (8w/3m/6m) 가 위클리 cadence (1w) 와 다른 주기 → 합산 일자 계산 부담 (8 위클리 × 5영업일 = 40영업일 ≈ 8주, 12위클리 ≈ 12주, 24위클리 ≈ 24주). Claude 가 합산 시 자동 계산.

**Neutral / follow-up**:
- **위클리 첫 인스턴스** = `260508_W19_weekly_log.md` (이번 주 금요일). `260504_daily_worklog.md` 가 첫 데일리 인스턴스.
- **ADR-0007 의 `wiki/99_templates/` 템플릿 3종** 작성 미완 — 본 ADR 의 layer 별 템플릿 (5종) 으로 확장 가능: `template_daily.md`, `template_weekly.md`, `template_groupleader_8w.md`, `template_techmeeting_6m.md`, `template_weekly_3m.md`, `template_mbo_quarterly.md` (별도 작업).
- **MBO 분기 수시피드백 review 노트 형식** — 첫 인스턴스 (`260331_Q1_mbo_review.md` — Q1 이미 지났으므로 retroactive 작성은 grilling 이후 결정 — 또는 Q2 부터 적용)
- **그룹장 보고 (8w) 와 기존 격주 상무 보고** — 기존 `260422_W17_biweekly_exec_report.md` 가 격주(2주) cadence. ADR-0006 는 8주. 사용자 메모 검토 필요 — 본 ADR 은 ADR-0006 cadence (8주) 그대로 채택.
- **SRIB weekly RUL 트랙** = 외부 협력 보고로 본 ADR scope 외. 별도 cadence 그대로 유지.

## Alternatives considered

- **데일리 layer 폐지 (위클리만 직접 작성)** — git commit 메시지만으로 한 주를 reconstruct 시 비-commit 작업 (ECT·TabS12+ 같은) 누락 위험. 오늘 진행 패턴 (`260504_daily_worklog.md`) 이 풍부한 디테일을 자연어 트리거로 흡수함을 검증. **Rejected**.
- **데일리 source-of-truth (위클리는 view 1단계)** — 데일리 누락 발생 시 위클리 합산 정확도 ↓. 영구 보존되어야 할 source 가 매일 작성 부담을 갖는 것은 위험. **Rejected**.
- **각 layer 별 source-of-truth (부분 redundancy 허용)** — 정합성 깨짐 위험, source 다중화로 분기 MBO 작성 시 어느 source 신뢰할지 모호. **Rejected**.
- **데일리는 작성 후 위클리 합산 시 삭제** — 분기 MBO 작성 시 디테일 복원 불가, 디스크 비용 무시 가능한데 정보만 손실. **Rejected**.
- **Cron 자동 트리거 (매주 금요일 자동 위클리 작성)** — ADR-0007 정신 (사용자 통제권 유지) 위반. 자동 트리거가 retroactive 작성 위험 ↑. **Rejected**.
- **그룹장 보고를 매주로 변경 (ADR-0006 cadence 변경)** — 8주 cadence 가 KPI 의사결정 속도와 상무 cognitive bandwidth 에 정합. ADR-0006 검증된 frame 변경 시 전체 ADR chain 재정합 부담. **Rejected**.
- **CONTEXT.md entry 만 — ADR 미작성** — 5-layer cadence pipeline 의 hard-to-reverse (변경 시 누적된 노트 형식 모두 영향) + surprising (왜 데일리는 작업한 날만? 왜 위클리가 source? 의문) + real trade-off (9 조합 중 명시적 선택) 모두 충족. **Rejected**.
