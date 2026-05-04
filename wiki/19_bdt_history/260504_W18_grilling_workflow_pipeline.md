---
title: "Grilling — workflow cadence pipeline (ADR-0011 박제)"
date: 2026-05-04
tags: [changelog, grilling, workflow, cadence-pipeline, adr-0011, daily, weekly, mbo]
type: changelog
status: completed
related:
  - "[[31_software_dev/adr/0011-daily-weekly-quarterly-pipeline]]"
  - "[[31_software_dev/adr/0006-reporting-format-core-and-appendix]]"
  - "[[31_software_dev/adr/0007-workflow-efficiency-pipeline]]"
  - "[[31_software_dev/adr/0010-mbo-track-mapping]]"
  - "[[MOC_Work_Log]]"
  - "[[260504_daily_worklog]]"
---

# 2026-05-04 — `/grill-with-docs` 세션: workflow cadence pipeline 박제

## 배경

사용자 신규 plan: **"데일리 워크로그 → 금요일 위클리 → 보고자료(그룹장/그룹원) → 분기 MBO 수시피드백"**.

기존 ADR-0006 (reporting format) + ADR-0007 (workflow efficiency) frame 위에서 일·주 단위 personal layer + 분기 MBO evaluation layer 가 미정의. 본 grilling 으로 5-layer cadence pipeline 정합화.

## Grilling 세션 기록

### Q1 — 보고자료(그룹장, 그룹원)의 정의

**A** 채택 — 두 청중에 두 종. 그룹장 보고용 = 그룹원 공람용 + 마일스톤·일정 헤더.

근거: 사용자 메모 "청중 3계층 압축률 분리" 정합 + ADR-0006 의 "그룹장 (8주) = 3~5 슬라이드 (1: KPI / 2~5: detail)" 와 정확히 일치.

### Q2 — 신규 플로우 cadence·source 매핑

**기존 ADR-0006/0007 frame 정합 확인**:
- 데일리·위클리 = personal layer (working memory) — ADR 미정의 → ADR-0011 신규
- 그룹원 공람 (3m) / 그룹장 보고 (8w) / 테크미팅 (6m) = ADR-0006 그대로 유지
- MBO 분기 = 위클리를 input source 로 활용, mbo_2026.md 갱신 + ADR-0010 7트랙 매핑

### Q3 — Source-of-truth

**A 채택** — 위클리 로그 = single source-of-truth.

근거:
1. 데일리 영구 보존이지만 working artifact (휘발성 컨텍스트 raw)
2. 위클리가 영구 보존 + 보고자료 4종의 derivation source
3. ADR-0006/0007 frame 의 (4) wiki ingest sub-cadence 정합

### Q4 — 데일리 운영 정책

**B + X 채택** — 작업 있는 날만 자연어 트리거 + 영구 보존.

근거:
1. 오늘 진행 패턴 (`260504_daily_worklog.md`) 검증
2. 강제력은 git commit 메시지가 자연 제공
3. 영구 보존이 분기 MBO 디테일 복원 보장

## 박제 결과

### 1. ADR-0011 신규 — `wiki/31_software_dev/adr/0011-daily-weekly-quarterly-pipeline.md`

5-layer cadence pipeline + Layer 별 운영 정책 + 파일명 컨벤션 + 자동화 트리거 (자연어 only) + 휘발 정책 (영구 보존). Anchors: ADR-0006, 0007, 0010.

### 2. MOC_Work_Log.md 갱신

상단에 "⏱️ Cadence Pipeline (ADR-0011)" 섹션 신규. 6-layer 표 + 자연어 트리거 + ADR cross-link.

### 3. 첫 인스턴스

- **데일리**: [[260504_daily_worklog]] (오늘 작성)
- **위클리**: 첫 인스턴스 = `260508_W19_weekly_log.md` (이번 주 금요일 예정)

## 다음 단계 (follow-up backlog)

- **wiki/99_templates/ 템플릿 6종 작성** (ADR-0007 의 3종 → ADR-0011 의 6종으로 확장):
  - `template_daily.md`
  - `template_weekly.md`
  - `template_groupleader_8w.md`
  - `template_weekly_3m_share.md`
  - `template_techmeeting_6m.md`
  - `template_mbo_quarterly.md`
- **첫 위클리 (W19)** 이번 금요일 작성 — `/grill-with-docs` 결과 검증
- **Q2 MBO 수시피드백** (~6월말) 첫 인스턴스 — Q1 은 retroactive 작성 여부 별도 결정
- **기존 격주 상무보고 (`260422_W17_biweekly_exec_report.md`) cadence 정합** — ADR-0006 (8주) vs 기존 격주 (2주) 충돌 검토 (별도 grilling 후보)

## ADR 가치 검증 (3 조건)

| 기준 | 충족 |
|---|---|
| Hard to reverse | ✅ 매주 매일 운영하는 정책. 변경 시 누적된 노트 형식 모두 영향 |
| Surprising without context | ✅ "왜 데일리는 작업한 날만? 왜 위클리가 source?" 등 향후 본인이 의문 가능 |
| Real trade-off | ✅ A/B/C × X/Y/Z 9 조합 중 명시적 선택 (5 alternatives 명시 reject) |
