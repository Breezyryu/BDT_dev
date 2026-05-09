---
title: "Changelog: Toyo 가속 제안 — PNE 동등 수준 도달 (류성택 요청)"
date: 2026-05-09
tags: [changelog, doc, proposal, toyo, performance, optimization]
related:
  - "[[260509_proposal_toyo_speedup_to_pne_parity]]"
  - "[[260509_policy_data_parsing_pipeline]]"
status: applied
---

# Changelog: Toyo 가속 제안 — PNE 동등 수준 도달

> 작업 요청자: 류성택 (사용자) — `toyo 사이클, 프로파일 소요를 pne 동등 수준으로 끌어올릴 방법은?`

---

## 변경 사항

### 1. 신규 wiki 문서 1개

- **위치**: `wiki/10_cycle_data/260509_proposal_toyo_speedup_to_pne_parity.md`
- **목적**: PNE 우위 4 원인 분해 → Toyo 가속 4 trajectory 박제
- **구조 14 § 박제**:
  1. TL;DR (4 trajectory)
  2. 현황 vs 목표 비용 표 (사이클·프로파일 × 현재·A후·C후)
  3. PNE 우위 4 원인 (C1~C4) 분해
  4. 가속 방안 매트릭스 9건 (효과·비용·우선순위)
  5. A 단계 — Quick win (A1~A3, 1~2 일)
  6. B 단계 — Toyo Phase 0 (B1~B3, 1주)
  7. C 단계 — 사이드카 cache (C1~C4, 1~2주)
  8. D 단계 — binary 변환 (장기, 기각 가능)
  9. 단계별 로드맵 + MBO 정합
  10. 위험·trade-off (정합·disk·메모리·정책)
  11. 회귀 검증 (fixture α/β/γ/δ + benchmark)
  12. 핵심 코드 위치 (수정 거점)
  13. Open Decision D12~D15
  14. Related + 변경 이력

### 2. _INDEX.md 등록

- **위치**: `wiki/10_cycle_data/_INDEX.md` § "Toyo / PNE 데이터 구조"
- **추가 항목**: ⭐ `[[260509_proposal_toyo_speedup_to_pne_parity]] — Toyo 가속 제안 (PNE 동등 — 4 trajectory A·B·C·D)`

---

## Why

### 기존 문제

- `260509_policy_data_parsing_pipeline` 측 컴퓨팅 비용 비교 (Toyo 사이클 50~235 ms vs PNE 20~100 ms · Toyo 프로파일 N×1~10 ms vs PNE warm 30~200 ms) 가 **현황 진단** 만 박제 — **가속 경로** 부재.
- 사용자 (류성택) 측 "PNE 동등 수준 도달" 요구가 명시 — 4 trajectory 별 효과·비용·우선순위 single-doc 부재.
- A 단계 (Quick win) 의 즉시 적용 가능 항목 (`usecols` 미적용 proto_:5230 + 프로파일 ThreadPool 미적용 proto_:1988~2065) 가 코드 측에서 발견됨.

### 해결

- **PNE 우위 4 원인 분해** — Phase 0 캐시 / DCIR I/O 0 / pivot_table 1-pass / .cyc warm cache.
- **4 trajectory 가속** (누적):
  - **A**: Quick win (1~2 일) — usecols + 병렬 + 벡터화 → **2~5x speedup**
  - **B**: Toyo Phase 0 (1주) — ToyoChannelMeta dataclass → **PNE Phase 0 동등 패러다임**
  - **C**: 사이드카 cache (1~2주) — `<channel>/.bdt_cache/timeseries.parquet` → **PNE warm 동등**
  - **D**: binary 변환 (장기) — Toyo NNNNNN → BDT 자체 binary → 기각 가능
- **목표 도달**: A 후 PNE 동등 진입 / C 후 PNE warm 동등 / D 시 PNE 우위.
- **Open Decision D12~D15** 명시 — 사이드카 trigger UX / LRU max / D 채택 여부 / benchmark fixture 채널.

---

## 영향 범위

### 직접 영향

- A 단계 즉시 추진 가능 — PR 분리 가능 (A1·A2·A3 독립).
- B·C 단계 = ADR 박제 + 회귀 fixture 갱신 trigger.
- 운영 정책 (260509_policy_toyo) §5.2 캐시 무효화 정책 갱신 trigger — 사이드카 cache 측 fingerprint/schema_version 추가.
- 데이터 파싱 정책 (260509_policy_parsing) §6.3 캐시 4계층 측 갱신 trigger — Toyo Phase 0 / 사이드카 추가.

### 간접 영향

- BDT 분석 자동화 (ADR-0008) fixture α/β/γ/δ 갱신 — 단계별 회귀 검증.
- MBO 1.2 혁신 (개발자용 SW + AI 협업 도구) 측 직접 기여 — A·B 단계.
- MBO 1.2.2 도전 (사이클 데이터 이상 감지·빅데이터 인프라) 측 anchor — C 단계.
- 사외/사내 dual-env 정합 ([[31_software_dev/adr/0008-bdt-test-and-study-automation|ADR-0008]]) — pyarrow 외부 의존 없음 (사내 PC 호환).

### 무영향

- 코드 동작 변경 없음 (제안 문서만 신설, 로직 변경 0).
- raw 데이터 무수정 정책 보존 — 사이드카는 `<channel>/.bdt_cache/` 별도 폴더.
- 기존 wiki 문서 (260508 reference, 260509 정책·전수조사·파싱 정책) 내용 보존.

---

## 검증

- [x] wiki 문서 마크다운 문법 정상 (Obsidian frontmatter, [[wikilink]], 표)
- [x] _INDEX.md 등록 완료
- [x] Markmap-friendly 구조 (헤딩 계층 명시, 짧은 명사구, 불릿 우선)
- [x] PNE 우위 4 원인 분해 (C1~C4) — 코드 line 번호 실측 정합
- [x] A 단계 Quick win 코드 거점 검증 — `usecols` 미적용 (proto_:5230), 프로파일 ThreadPool 부재 (proto_:1988~2065) 확인
- [x] 4 trajectory 효과·비용·우선순위 표 (9 방안 ID 부여)
- [x] Open Decision D12~D15 명시
- [x] 회귀 fixture 영향 표 (α/β/γ/δ × A/B/C 단계)

---

## 후속 작업 (옵션)

1. **A 단계 즉시 추진** — A1·A2·A3 PR 분리 발행. 회귀 fixture β 갱신 동시.
2. **D15 결정** — benchmark fixture 채널 선정 (Q7M Inner BLK1 ch11 4956 step 1순위 안). pytest-benchmark 도입.
3. **B 단계 ADR 박제** — `ToyoChannelMeta` dataclass schema 결정 + `_toyo_meta_store` LRU 정책 (D13).
4. **C 단계 진입 시 D12 결정** — 자동 변환 vs 수동 trigger vs 백그라운드 사전 변환.
5. **운영 정책 (260509_policy_toyo) §5.2 갱신** — 사이드카 cache 정책 박제 (B·C 단계 적용 후).

---

## Related

- [[260509_proposal_toyo_speedup_to_pne_parity]] — 본 changelog의 산출물
- [[260509_policy_data_parsing_pipeline]] — baseline 비용 (현황)
- [[260509_policy_toyo_data_operation]] — 운영 정책 (raw 무수정·캐시 무효화)
- [[260509_audit_toyo_lifetime_full_inventory]] — 156 채널 분포 (cache 크기 산정 근거)
- [[260410_study_pne_cyc_vs_csv_structure]] — `.cyc` 벤치마크 (목표)
- [[31_software_dev/adr/0008-bdt-test-and-study-automation|ADR-0008]] — 검증 fixture 4종
