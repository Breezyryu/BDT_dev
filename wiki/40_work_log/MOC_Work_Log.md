---
title: "📝 MOC — 업무 기록"
aliases:
  - 업무 MOC
  - Work Log MOC
tags:
  - Work_Log
  - MOC
type: reference
status: active
updated: 2026-03-15
---

# 📝 업무 기록

> [!abstract] 개요
> 업무 목표, cadence pipeline (일/주/8w/3m/6m/Q), 주간 보고(SRIB RUL), 프로젝트 기획, 행정 기록의 허브.

---

## ⏱️ Cadence Pipeline (ADR-0011)

> [!important] 5-layer cadence pipeline
> 데일리 → **위클리 (★ source-of-truth)** → 청중·cadence 별 view 파생 + MBO 분기 갱신.
> 자세히는 [[31_software_dev/adr/0011-daily-weekly-quarterly-pipeline]].

| Layer | Cadence | 파일명 컨벤션 | 청중 |
|---|---|---|---|
| 데일리 워크로그 | 매일 (작업 있는 날) | `YYMMDD_daily_worklog.md` | 본인 |
| 위클리 로그 ★ | 매주 금요일 | `YYMMDD_W{nn}_weekly_log.md` | 본인 (source-of-truth) |
| 그룹장 보고 | 8주 | `YYMMDD_W{nn}_groupleader_8w.md` | 그룹장 (상무) |
| 그룹원 공람 | 3개월 | `YYMMDD_W{nn}_weekly_3m_share.md` | 80 그룹원 |
| 테크미팅 | 6개월 | `YYMMDD_W{nn}_techmeeting_6m.md` | 박사급 peer |
| MBO 수시피드백 | 분기 (3개월) | `YYMMDD_Q{n}_mbo_review.md` + [[mbo_2026]] 갱신 | 평가 시스템 |

**자연어 트리거**:
- "오늘 한 일 정리해줘" → 데일리
- "이번 주 위클리 정리해줘" → 위클리
- "8주차 그룹장 보고 만들어줘" / "3개월 그룹원 공람" / "6개월 테크미팅"
- "Q1 MBO 수시피드백 작성해줘"

**Anchors**: [[31_software_dev/adr/0006-reporting-format-core-and-appendix|ADR-0006]] (청중·cadence 차등) · [[31_software_dev/adr/0007-workflow-efficiency-pipeline|ADR-0007]] (6단계 업무 flow) · [[31_software_dev/adr/0010-mbo-track-mapping|ADR-0010]] (7트랙 매핑) · [[31_software_dev/adr/0011-daily-weekly-quarterly-pipeline|ADR-0011]] (cadence pipeline)

---

## 🎯 목표 & 기획

- [[업무목표]] — 7개 주요 과제 + 5개 알파 과제 (구체적 성공 기준 포함)
- [[업무_정리]] — W33~W52 주간 진행 요약
- [[업무목표]] — S27 SBP, BMS 알고리즘 개발 로드맵
- [[과제_Process]] — 과제 진행 프로세스
- [[수시평가]] — 수시 평가 기록

---

## 📊 SRIB RUL 프로젝트 (주간 보고)

> [!note] SRIB 프로젝트 흐름
> CC1 특성 한계 분석 → IOD 특성 제안 → 체인/스택 모델 비교 → Transfer Learning 최적화

| 날짜 | 노트 | 주요 내용 |
|------|------|-----------|
| 2025-08-21 | [[250821_SRIB_weekly_RUL]] | CC1 한계, IOD 제안 |
| 2025-08-29 | [[250829_SRIB_RUL]] | 진행 사항 |
| 2025-09-05 | [[250905_SRIB_weekly_RUL]] | 진행 사항 |
| 2025-09-12 | [[250912_SRIB_RUL_weekly]] | 체인/스택 모델 비교 |
| 2025-09-23 | [[250923_SRIB_Weekly_RUL]] | 하이퍼파라미터 튜닝 |
| 2025-09-30 | [[250930_W40_SRIB_weekly_RUL]] | Transfer Learning |

---

## 📋 분기 / 연간 보고

- [[25_W49]] — 2025 W49 주간 보고
- [[25_3Q_QTR]] — 2025 3Q 분기 보고

---

## 🔬 프로젝트별

- [[BYD_Gen5_소재_DOE]] — BYD Gen5+ 소재 DOE
- [[S27_적용방안]] — S27 적용 방안
- [[SBP_진단기능]] — SBP 진단 기능 요약
- [[시스템디바이스_OJT]] — 시스템디바이스 OJT
- [[승인수명_소요일]] — 승인 수명 소요일 분석

---

## 🏛️ 행정 / 기타

- [[배터리_QPA]] — 배터리 QPA 품질 감사
- [[투자_및_그룹예산]] — 그룹 예산 및 투자
- [[유해화학물질_택배배송]] — 화학물질 배송 절차
- [[전해액_관리]] — 실험실 전해액 관리
- [[시험소도구]] — 시험소 도구 목록
- [[전화면접_전기화학]] — 전기화학 면접 준비
- [[Altair_Conference]] — Altair 컨퍼런스 기록

---

## 🔗 연관 카테고리
- 모델 개발: [[MOC_Modeling_AI]]
- 실험 절차: [[MOC_Experiments]]
