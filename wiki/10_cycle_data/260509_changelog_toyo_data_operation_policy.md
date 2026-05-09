---
title: "Changelog: TOYO 데이터 운영 정책 신설 (류성택 요청)"
date: 2026-05-09
tags: [changelog, doc, toyo, operation, policy]
related:
  - "[[260509_policy_toyo_data_operation]]"
  - "[[260508_raw_data_schema_unified_reference]]"
status: applied
---

# Changelog: TOYO 데이터 운영 정책 신설

> 작업 요청자: 류성택 (사용자) — `TOYO 데이터 운영 정책을 수립하자. PNE와 차이점을 고려하자.`

---

## 변경 사항

### 1. 신규 wiki 문서 1개

- **위치**: `wiki/10_cycle_data/260509_policy_toyo_data_operation.md`
- **목적**: schema fact (`260508_raw_data_schema_unified_reference`) 위에 **운영 결정** 만 박제
- **17 영역 정책**:
  1. PNE 차이 — 운영 차이 매트릭스 (10건)
  2. 데이터 수집 정책 (채널 폴더 발견, raw 파일 인벤토리, 경로 입력)
  3. 인코딩 · 파일 형식 (cp949 강제, BLK 정규화)
  4. 자원 정책 P0/P1/P2/P3
  5. 캐싱 정책 (lru_cache, ChannelMeta)
  6. Logical Cycle 매핑 (Cycle 컬럼 사용 금지, TotlCycle 만)
  7. DCIR 식별 (Finish=Tim ∧ Cap<min/60 ∧ Cond=2)
  8. Chamber 온도 보강 (Toyo-only gap, Decision 8)
  9. Rest step 행 부재 보강
  10. 충방전 인덱스 정렬 (위치 기반)
  11. mincapacity 산정
  12. 검증 게이트 (ADR-0008 fixture α/β/γ/δ Toyo subset)
  13. 알려진 한계
  14. 미해결 결정 4건 (D8~D11)
  15. 핵심 코드 위치
  16. Related
  17. 변경 이력

### 2. _INDEX.md 등록

- **위치**: `wiki/10_cycle_data/_INDEX.md` § "Toyo / PNE 데이터 구조"
- **추가 항목**: ⭐ `[[260509_policy_toyo_data_operation]] — TOYO 운영 정책 (PNE 차이 매트릭스 + Open Decision 4건)`

---

## Why

### 기존 문제

- `260508_raw_data_schema_unified_reference` 는 **schema fact** 만 정리 (어떤 컬럼이 어디 있는가).
- 그 위의 **운영 결정** (cp949 강제? Cycle 컬럼 사용? chamber 온도 보강 어떻게? P0/P1/P2 경계?) 이 코드 안에 흩어져 있어 **단일 SSOT 부재**.
- PNE 와의 차이가 운영 차이를 만드는 지점 (chamber 온도 부재, Rest 행 부재, 1 step = 1 파일 등) 이 명시 박제되지 않음 → 신규 작업자 / 미래 본인이 매번 코드 탐색 반복.

### 해결

- **단일 정책 문서** = 운영 결정 17 영역 (어떻게 운영할지) 박제.
- **PNE 차이 매트릭스** = 1 표로 운영 차이 10건 비교.
- **미해결 결정 4건** (D8~D11) = 명시 trigger 와 함께 박제 — Q-별 sprint 측 검토 항목 명료화.
- **fact vs decision 분리** — schema 정리는 260508 reference 가 SSOT, 운영 결정은 본 정책이 SSOT.

---

## 영향 범위

### 직접 영향

- 신규 작업자 onboarding: schema (260508) → 운영 정책 (260509) 순으로 학습 경로 명확.
- 코드 변경 시 운영 정책 위반 여부 사전 점검 가능 (예: cp949 → utf-8 변경 안 됨, Cycle 컬럼 직접 사용 금지).
- BDT 분석 자동화 ([[31_software_dev/adr/0008-bdt-test-and-study-automation|ADR-0008]]) 의 Toyo subset fixture 정의 명료화.

### 간접 영향

- **Decision 8** (chamber 온도 보강) — Q-별 sprint 측 trigger 박제. 향후 yaml 도입 결정 시 본 문서 § 8 갱신.
- **Decision 11** (Arbin 등 추가 cycler) — 별도 정책 문서로 분리 trigger.
- 사이클 분류기 v3 (`260505_phase0_5_classifier_logic`) 의 카테고리 결정 신호와 본 정책의 DCIR / Rest 보강이 정합 — 향후 분류기 갱신 시 cross-link 추가 검토.

### 무영향

- 코드 동작 변경 없음 (정책 문서만 신설, 로직 변경 0).
- 기존 wiki 문서 (260508 reference, 260409 study 시리즈) 내용 보존 — cross-link 만 추가.

---

## 검증

- [x] wiki 문서 마크다운 문법 정상 (Obsidian frontmatter, [[wikilink]], 표)
- [x] _INDEX.md 등록 완료
- [x] Markmap-friendly 구조 (헤딩 계층 명시, 짧은 명사구, 불릿 우선)
- [x] PNE 차이 매트릭스 10건 — 260508 reference §5 동등성 표와 정합
- [x] Decision 8 (chamber) / Decision 11 (Arbin) 등 미해결 결정 명시
- [x] 코드 동작 변경 0 (정책 문서 only)

---

## 후속 작업 (옵션)

1. **Decision 8 해결** — chamber 온도 보강 yaml 도입 시점 결정 후 본 정책 § 8 갱신.
2. **Toyo subset pytest fixture 실제 구축** — ADR-0008 의 α/β/γ/δ 4 fixture 의 Toyo BLK3600 / BLK5200 sample 추가.
3. **PNE 운영 정책 sibling 문서** — 본 문서를 template 로 PNE 측 운영 정책 (binary parsing, .cyc gap-fill 정책 등) 박제.
4. **메모리 reference 추가** — `MEMORY.md` 측 Toyo 정책 pointer 등록 검토.

---

## Related

- [[260509_policy_toyo_data_operation]] — 본 changelog의 산출물 (정책 문서)
- [[260508_raw_data_schema_unified_reference]] — schema fact SSOT (sibling)
- [[260508_changelog_raw_data_schema_doc]] — 260508 reference 의 changelog (정합 형식)
- [[260409_study_02_toyo_cycle_data]] — Toyo 코드 라인별 분석 (학습)
- [[31_software_dev/adr/0008-bdt-test-and-study-automation|ADR-0008]] — 검증 fixture 4종
