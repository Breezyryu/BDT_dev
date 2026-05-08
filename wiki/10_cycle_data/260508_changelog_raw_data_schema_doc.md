---
title: "Changelog: Raw Data Schema 통합 Reference 문서 + docstring 링크 (류성택 요청)"
date: 2026-05-08
tags: [changelog, doc, raw-data, ptn, sch, capacity-log, save-end-data]
related:
  - "[[260508_raw_data_schema_unified_reference]]"
status: applied
---

# Changelog: Raw Data Schema 통합 Reference 문서

> 작업 요청자: 류성택 (사용자) — `(3) raw data schema 문서를 BDT 코드 docstring/wiki에 통합`

---

## 변경 사항

### 1. 신규 wiki 문서 1개

- **위치**: `wiki/10_cycle_data/260508_raw_data_schema_unified_reference.md`
- **내용**:
  - Toyo 5종 + PNE 6종 raw 파일 schema 전체 정리
  - 6 차원 (D1~D6) 추출 매트릭스
  - Toyo↔PNE 동등성 11/12 검증 (시험 환경 온도만 Toyo 누락)
  - 6 카테고리 (initial/RPT/Rss/GITT/HPPC/가속수명) 결정 신호
  - 자원 정책 (P0/P1/P2) — 제 1원칙 부담 최소화
  - 알려진 한계 (Toyo·PNE·공통)
  - 핵심 코드 위치 (line 번호 포함)

### 2. _INDEX.md 등록

- **위치**: `wiki/10_cycle_data/_INDEX.md` § "Toyo / PNE 데이터 구조"
- **추가 항목**: `⭐ [[260508_raw_data_schema_unified_reference]] — Toyo + PNE 통합 reference (6 차원 매트릭스, 동등성)`

### 3. BDT 본 코드 docstring 링크 추가 (5개 함수)

위치: `DataTool_dev_code/DataTool_optRCD_proto_.py`

| 함수 | 라인 | 추가된 reference |
|---|---|---|
| `toyo_read_csv` | L5095 | §2.4-2.5 (CAPACITY.LOG + NNNNNN) |
| `_parse_ptn_step` | L7251 | §2.1 (PTN 고정폭) |
| `extract_toyo_ptn_structure` | L7427 | §2.1-2.3 (PTN + Option + Option2) |
| `_unified_pne_load_raw` | L1678 | §3.4-3.5 (SaveEndData + SaveData) |
| `_cached_pne_restore_files` | L1482 | §3.4-3.5 (Restore 폴더) |
| `_parse_pne_sch` | L8039 | §3.1 + 260504 audit cross-link |

---

## Why

기존 문제:
- Toyo + PNE raw schema가 **여러 wiki 문서에 분산** (`260409_study_02_toyo`, `260409_study_03_pne`, `260410_study_pne_cyc_vs_csv`, `260504_audit_phase0_extractable_fields` 등)
- **양 시스템 동등성 매트릭스 없음** → "이 정보를 Toyo/PNE 어디서 추출하는가?" 답하려면 여러 문서 교차 참조 필요
- BDT 본 코드 docstring에서 wiki link 부재 → 코드 ↔ 지식 베이스 간극

해결:
- **단일 reference 문서** (`260508_raw_data_schema_unified_reference.md`) 1개로 모든 raw 파일 schema 통합
- 6 차원 매트릭스로 "어떤 정보를 어디서 가져올지" 1표로 답
- 동등성 매트릭스로 Toyo·PNE 간극 명시 (Toyo의 chamber 온도 누락 등)
- 핵심 함수 docstring에 wiki § 번호 명시 → 코드 reading 시 즉시 참조 가능

---

## 영향 범위

### 직접 영향
- 신규 작업자 onboarding: 단일 문서로 raw schema 전체 파악 가능
- 사이클 정의/매핑 통합 작업 (LC v2 매핑 + CycleProfile prototype)의 **schema baseline** 제공

### 간접 영향
- 향후 raw 파일 형식 변경/확장 시 본 reference 문서를 SSOT로 갱신
- 신규 cycler 추가 시 (예: Arbin) 동일 형식으로 컬럼 추가 가능

### 무영향
- 코드 동작 변경 없음 (docstring만 추가, 로직 변경 0)
- 기존 wiki 문서 (260504, 260409 시리즈) 내용 보존 — cross-link만 추가

---

## 검증

- [x] wiki 문서 마크다운 문법 정상 (Obsidian frontmatter, [[wikilink]], 표)
- [x] _INDEX.md 등록 완료
- [x] BDT 본 코드 docstring 5개 함수 링크 추가 (L5095, L7251, L7427, L1678, L1482, L8039)
- [x] 코드 동작 변경 0 (docstring only)

---

## 후속 작업 (옵션)

1. **Toyo `_Option2.PTN` 의미 해석**: 현재 미활용. 안전 cutoff 임계값 추정 → 향후 보강 시 reference 문서 §2.3 갱신.
2. **PNE EndState 코드 사전**: SaveEndData의 sparse 컬럼 (28~47) 의미 미공개. 추후 분석 시 reference §3.4 갱신.
3. **Schema 자동 검증**: 신규 데이터셋 ingest 시 schema 일치 여부 자동 점검 (현재는 수동).

---

## Related

- [[260508_raw_data_schema_unified_reference]] — 본 changelog의 산출물
- [[260504_audit_phase0_extractable_fields]] — PNE .sch 정밀 분석 (cross-link)
- [[260409_study_02_toyo_cycle_data]] · [[260409_study_03_pne_cycle_data]] — 기존 학습 시리즈
