---
title: "Changelog: 데이터 파싱 정책 — 사이클·프로파일 × Toyo·PNE (류성택 요청)"
date: 2026-05-09
tags: [changelog, doc, policy, parsing, cycle, profile, toyo, pne]
related:
  - "[[260509_policy_data_parsing_pipeline]]"
  - "[[260509_policy_toyo_data_operation]]"
  - "[[260508_raw_data_schema_unified_reference]]"
status: applied
---

# Changelog: 데이터 파싱 정책 (사이클·프로파일 × Toyo·PNE)

> 작업 요청자: 류성택 (사용자) — `사이클분석, 프로파일분석에 따른 데이터 파싱 정책을 정리해. * raw 데이터 열 정보 * 어떤것만 파싱하는지 * 그 후 전처리 어떻게하는지 * 컴퓨팅 소스, 소요 시간도 * PNE와 같이 비교`

---

## 변경 사항

### 1. 신규 wiki 문서 1개

- **위치**: `wiki/10_cycle_data/260509_policy_data_parsing_pipeline.md`
- **목적**: 사용자 요청 5축 모두 박제 — raw 컬럼 / 추출 / 전처리 / 컴퓨팅 / PNE 비교
- **구조 12 § 박제**:
  1. TL;DR (5 핵심)
  2. 4 매트릭스 (사이클×프로파일 × Toyo×PNE)
  3. 사이클 분석 — Raw 컬럼 vs 추출 (Toyo 17~19→10, PNE 47+→13)
  4. 사이클 분석 — 전처리 (Toyo 13단계, PNE 9단계)
  5. 프로파일 분석 — Raw 컬럼 vs 추출 (Toyo 16→5, PNE 47+→14)
  6. 프로파일 분석 — 정규화 (Toyo 7변환, PNE 9변환)
  7. 컴퓨팅 비용 (사이클·프로파일 × 사이클러 + 캐시 4계층)
  8. 정책 결정 D1~D6 (컬럼 사용률·단위·DCIR·시간적분·캐시·schema 동결)
  9. 알려진 한계
  10. 회귀 검증 게이트
  11. 핵심 코드 위치 (line 번호 명시)
  12. Related + 변경 이력

### 2. _INDEX.md 등록

- **위치**: `wiki/10_cycle_data/_INDEX.md` § "Toyo / PNE 데이터 구조"
- **추가 항목**: ⭐ `[[260509_policy_data_parsing_pipeline]] — 데이터 파싱 정책 (사이클·프로파일 × Toyo·PNE 4 매트릭스)`

---

## Why

### 기존 문제

- **schema fact** (`260508`), **Toyo 운영 정책** (`260509_policy_toyo_data_operation`), **사이클 코드 학습** (`260409_study_02/03`) 가 분산.
- **사이클 vs 프로파일** 측 파싱 차이 (17→10 vs 16→5 vs 47+→13 vs 47+→14) 가 single-doc 부재.
- **컴퓨팅 비용 비교** — Toyo profile vs PNE profile 의 캐시 정책 차이 (lru_cache vs ChannelMeta vs `_cached_pne_restore_files` 4계층) 가 코드 측에만 산재.
- **DCIR 모드 사이클러별 정합** — Toyo 1 모드 vs PNE 3 모드 (chkir/mkdcir/10s) 의 식별 신호 표 부재.
- **단위 통일 SSOT** — Toyo `/1000`, PNE `/1e6`/`/1e9` 분기가 코드 분산. 잘못된 분기 시 단위 깨짐.

### 해결

- **5축 single-doc** — 사용자 요청 5개 영역 (raw 컬럼·추출·전처리·컴퓨팅·PNE 비교) 한 문서로 박제.
- **4 매트릭스 표** — 사이클 분석 × Toyo / 사이클 분석 × PNE / 프로파일 × Toyo / 프로파일 × PNE — 각 진입점 line 번호 명시.
- **컴퓨팅 비용 표** — 채널당 ms / 사이클 N개당 ms / 캐시 hit 효과 정량 (PNE warm 5~200x 인용).
- **정책 결정 D1~D6** — 컬럼 사용률 강제 / 단위 통일 / DCIR 분기 정합 / Toyo 시간적분 / 캐시 무효화 / schema 동결.
- **회귀 게이트** — fixture α/β/γ/δ 매핑 (ADR-0008 정합) — 컬럼·정규화 변경 시 자동 검출.

---

## 영향 범위

### 직접 영향

- 신규 작업자 onboarding: schema (260508) → 운영 정책 (260509_policy_toyo) → **파싱 정책 (260509_policy_parsing)** → 전수조사 (260509_audit) 4-layer 학습 경로 완성.
- **컬럼 추출 단일 진입점 강제** — `toyo_cycle_import`, `_unified_pne_load_raw` 등 변경 시 회귀 fixture 동시 갱신 trigger.
- **단위 통일 SSOT** — Toyo `/1000`, PNE `/1e6`/`/1e9` 분기 표준화. 신규 개발자가 PNE21/22 코인셀 미인지 시 사고 방지.
- **DCIR 모드 분기 명시** — chkir/mkdcir/10s pulse 식별 신호 표 → 신규 DCIR 패턴 추가 시 영향 범위 명확.

### 간접 영향

- **신규 컬럼 추가 시 ADR 박제 trigger** — D6 (schema 동결) 정책 측. 단순 추가 X, ADR + 회귀 fixture 함께.
- **새 사이클러 도입 시 (Arbin 등)** — 본 4 매트릭스 template 으로 별도 정책 박제. [[260509_policy_toyo_data_operation|§14 D11]] 와 정합.
- **캐시 정책 단일 진입점** — `clear_channel_cache()`, `clear_channel_meta_store()` 사용 표준화.

### 무영향

- 코드 동작 변경 없음 (정책 문서만 신설, 로직 변경 0).
- 기존 wiki 문서 (260508, 260509_policy_toyo, 260509_audit, 260409_study) 내용 보존 — cross-link 만 추가.
- raw 데이터 무수정.

---

## 검증

- [x] wiki 문서 마크다운 문법 정상 (Obsidian frontmatter, [[wikilink]], 표)
- [x] _INDEX.md 등록 완료
- [x] Markmap-friendly 구조 (헤딩 계층 명시, 짧은 명사구, 불릿 우선)
- [x] 4 매트릭스 사이클×프로파일 × Toyo×PNE 모두 박제
- [x] 컬럼 사용률 정량 (Toyo 53~59% / 31% · PNE ~28% / ~30%)
- [x] 컴퓨팅 비용 표 (Toyo 사이클 50~235ms · PNE 사이클 20~100ms · `.cyc` warm 1.6~6.6ms)
- [x] 코드 line 번호 실측 (proto_:5289, 11689, 5237, 1988, 2111, 2192 등)
- [x] 정책 결정 D1~D6 명시
- [x] 사용자 요청 5축 모두 커버 (raw 컬럼·추출·전처리·컴퓨팅·PNE 비교)

---

## 후속 작업 (옵션)

1. **신규 컬럼 사용률 audit** — `_Option2.PTN` (현재 미활용) 추가 시 본 정책 §3·§4 갱신.
2. **DCIR 모드 EndState 코드 사전화** — PNE 78/64/66 magic number 의 사내 검증 결과를 본 정책 §3.2·§7 D3 측 박제.
3. **표준 출력 컬럼 schema 자동 검증** — 회귀 fixture (δ) 측 dtype/범위 자동 체크 모듈 (현재는 수동).
4. **PNE 운영 정책 sibling 박제** — Toyo 운영 정책 (260509_policy_toyo) template 으로 PNE 측 정책 (`.cyc` 캐시·EndState·is_micro_unit) 별도 문서.
5. **벤치마크 회귀 검증** — Toyo 사이클 50~235 ms / PNE 사이클 20~100 ms 의 실측치 분기별 갱신 (성능 회귀 감시).

---

## Related

- [[260509_policy_data_parsing_pipeline]] — 본 changelog의 산출물
- [[260509_policy_toyo_data_operation]] — Toyo 운영 정책 (sibling)
- [[260509_audit_toyo_lifetime_full_inventory]] — 실제 데이터 전수조사
- [[260508_raw_data_schema_unified_reference]] — schema fact SSOT
- [[260409_study_02_toyo_cycle_data]] — Toyo 코드 라인별 학습
- [[260409_study_03_pne_cycle_data]] — PNE 코드 라인별 학습
- [[260410_study_pne_cyc_vs_csv_structure]] — `.cyc` 벤치마크 출처
- [[260411_analysis_cycle_pipeline_complete]] — 전체 사이클 파이프라인
- [[31_software_dev/adr/0008-bdt-test-and-study-automation|ADR-0008]] — 검증 fixture 4종
