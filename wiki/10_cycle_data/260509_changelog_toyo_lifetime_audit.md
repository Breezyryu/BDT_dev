---
title: "Changelog: TOYO 수명 데이터 전수조사 (류성택 요청)"
date: 2026-05-09
tags: [changelog, doc, toyo, audit, anomaly]
related:
  - "[[260509_audit_toyo_lifetime_full_inventory]]"
  - "[[260509_policy_toyo_data_operation]]"
  - "[[260508_raw_data_schema_unified_reference]]"
status: applied
---

# Changelog: TOYO 수명 데이터 전수조사

> 작업 요청자: 류성택 (사용자) — `"C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\수명_Toyo" 전수조사하라.`

---

## 변경 사항

### 1. 신규 wiki 문서 1개

- **위치**: `wiki/10_cycle_data/260509_audit_toyo_lifetime_full_inventory.md`
- **목적**: schema reference (`260508`) + 운영 정책 (`260509_policy`) 의 실제 데이터 정합 검증
- **범위**: 26 datasets · 156 channels · 358,847 NNNNNN files 전수
- **산출**:
  - 가족 분류 9 family (Q7M Inner/Main/Sub · Gen4 blk2/blk7 · M1 · 김건희 SUS 222/245 수명/장수명)
  - 채널당 NNNNNN 분포 (min=0, p50=1715, max=5954)
  - 신규 file types 5종 (CHCMT.TXT / COMMON_ENV.CFG / LCOUNT.TMP / LCOUNT2.TMP / TEMP.LOG)
  - CAPACITY.LOG 헤더 변종 2종 (17 / 19 컬럼)
  - **anomaly 7건** (A1~A7) — 빈 채널·capacity 불일치·multi-PTN·LCOUNT 누락 등
  - **운영 정책 갱신 권고 4건** (G1~G4)
  - **schema reference 갱신 권고** — 신규 file types 5종 박제

### 2. _INDEX.md 등록

- **위치**: `wiki/10_cycle_data/_INDEX.md` § "Toyo / PNE 데이터 구조"
- **추가 항목**: ⭐ `[[260509_audit_toyo_lifetime_full_inventory]] — TOYO 수명 데이터 전수조사 (26 datasets 156 ch 358K NNNNNN)`

---

## Why

### 기존 문제

- `260509_policy_toyo_data_operation` 의 운영 결정이 **실제 데이터 측 정합 검증 부재** 상태.
- `260508_raw_data_schema_unified_reference` 의 file 인벤토리가 **6종** (PTN/Option/Option2/CAPACITY.LOG/NNNNNN/CMT) 으로만 박제 — 실제 channel 측에는 **11종** 존재.
- 신규 작업자 onboarding 시 데이터 ingest 부담 — 어떤 가족이 몇 채널 / 어떤 anomaly 가 있는지 single-doc 부재.

### 해결

- **전수조사 single-doc** = 156 channels 측 inventory · file type census · anomaly 박제.
- **schema reference (260508) 갱신 권고** § 8 — 신규 file types 5종 추가 항목.
- **운영 정책 (260509_policy) 갱신 권고** § 7 — 빈 채널 skip / multi-PTN 우선순위 / capacity 산정 우선순위 / 신규 file types 무시 4건.
- **가족 분류 표** — 향후 가속수명 vs 일반수명 / 김건희 vs 김동진 / Q7M 3종 (Inner/Main/Sub) 비교 분석 시 즉시 baseline.

---

## 영향 범위

### 직접 영향

- 신규 작업자 onboarding: schema (260508) → 운영 정책 (260509_policy) → 전수조사 (260509_audit) 3-layer 학습 경로.
- `260508` reference 의 file 인벤토리 **갱신 trigger** — §8 권고 박제.
- `260509_policy` 의 §6.3 (multi-PTN), §11 (mincapacity), §13 (한계) 갱신 trigger — §7 권고 박제.
- BDT 분석 자동화 ([[31_software_dev/adr/0008-bdt-test-and-study-automation|ADR-0008]]) 의 fixture α 측 sample 후보 식별 (F3).

### 간접 영향

- **김건희 데이터셋 정리 trigger** — 빈 222mAh 4 채널 / `_32` sub-dataset / 수명 vs 장수명 protocol 차이 사용자 확인 필요 (F2, F5).
- **multi-PTN 우선순위 코드** (`_find_ptn_file()` proto_:7221) — 36 채널 영향 → 회귀 테스트 fixture 필요 (F1).
- **김건희 222mAh** — 시험 abort 폴더 → 별도 archive 폴더 이동 검토.

### 무영향

- 코드 동작 변경 없음 (audit 문서만 신설, 로직 변경 0).
- 기존 wiki 문서 (260508 reference, 260509 policy) 내용 보존 — 갱신 권고만 박제.
- raw 데이터 무수정 — read-only audit.

---

## 검증

- [x] wiki 문서 마크다운 문법 정상 (Obsidian frontmatter, [[wikilink]], 표)
- [x] _INDEX.md 등록 완료
- [x] Markmap-friendly 구조 (헤딩 계층 명시, 짧은 명사구, 불릿 우선)
- [x] 26 datasets · 156 channels · 358,847 NNNNNN 전수 카운트 일치
- [x] 가족 분류 합 = 156 channels (UNCATEGORIZED 0)
- [x] cp949 인코딩 sanity (PTN / CAPACITY.LOG sample 검증)
- [x] BLK3600 균질 확인 (BLK5200 0건)

---

## 후속 작업 박제 — F1~F5

본 audit § 10 측 후속 작업:

1. **F1**: multi-PTN content byte-diff (36 채널)
2. **F2**: 김건희 수명 vs 장수명 PTN protocol diff
3. **F3**: pytest fixture α sample 등록 (ADR-0008 정합)
4. **F4**: 빈 채널 자동 skip 코드 구현
5. **F5**: 김건희 ch=32 dedup 결정 (사용자 확인 후)

---

## Related

- [[260509_audit_toyo_lifetime_full_inventory]] — 본 changelog의 산출물 (audit 문서)
- [[260509_policy_toyo_data_operation]] — 운영 정책 (갱신 권고 대상)
- [[260508_raw_data_schema_unified_reference]] — schema fact (갱신 권고 대상)
- [[260508_changelog_raw_data_schema_doc]] — 260508 의 changelog (정합 형식)
- [[260409_study_02_toyo_cycle_data]] — Toyo 코드 라인별 분석
- [[31_software_dev/adr/0008-bdt-test-and-study-automation|ADR-0008]] — 검증 fixture 4종
