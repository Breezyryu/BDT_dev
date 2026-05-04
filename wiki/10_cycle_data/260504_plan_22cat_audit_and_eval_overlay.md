---
title: "사이클 분류기 (22 카테고리) 재검증 + 6 평가 항목 매핑 — Plan"
date: 2026-05-04
tags: [plan, cycle-classify, evaluation-mapping, profile-analysis, audit, sch-parsing]
related:
  - "[[260428_profile_4modes_spec]]"
  - "[[260428_changelog_profile_data_subtab]]"
  - "[[260427_changelog_data_subtab]]"
  - "[[260418_p3_cyc_tier2_loop_detect]]"
  - "[[260419_사이클분류_전면재검토]]"
  - "[[hub_logical_cycle]]"
status: active
---

# 사이클 분류기 (22 카테고리) 재검증 + 6 평가 항목 매핑 — Plan

> Grilling 결과 (260504): 평가 매핑 = **(c) 직교 layer** (22 자동 + 6 평가자 매핑).
> 단 prerequisite = 22 카테고리 자체 재검증. → 5단계 audit plan 우선 진행.

---

## TL;DR

- 사이클 데이터 / 프로파일 분석 결과 탭에 **초기 셀 평가 6 항목** 지표 추가하는 계획.
- 6 항목 = 초기 방전 용량 / 율별 충전 비교 / 율별 방전 비교 / Hysteresis 방전 / 1달 방치 후 0.2C / DCIR-OCV·SOC.
- 매핑 방식 = **(c) 직교 layer** — 22 자동 분류 + 6 평가자 매핑이 별 axis. 사이클 바에 두 layer (auto 배경 + eval frame).
- 매핑 layer 의 신뢰는 22 카테고리 정확도가 base. → **22 재검증** 5단계 plan 우선 진행.
- 검증 대상: `raw/raw_exp/exp_data/` 하위 **187 폴더 전수**. 산출물 = wiki md.

---

## 1. Grilling 결정 (260504 session)

### Q1. 지표 조직 단위 — (c) 2-layer
- **Phase A** (TC → 지표 산출) = 자동 100%, `_classify_loop_group` 결과 활용
- **Phase B** (평가 view) = 평가자 매핑 main, 자동은 가이드

### Q2. Phase B 입력 UX — (1) Direct TC 범위 입력
- 경로 테이블 `TC` 컬럼 + 사이클 바 드래그 sync
- 영속화 키 = **`.sch` 파일 내부 패턴** (file hash 또는 step pattern signature)
- spec = 6 항목 고정 권장, 평가자 변경 가능

### Q3. UI 형식 — (C) 사이클 바 multi-region 색상 마킹
- 매핑 = 색상 구분, 상세 = 토글 expand
- **이미 구현되어 있는 기능**: `CycleTimelineBar` (L9674), `_CLASSIFIED_COLORS` dict (L9430), `_build_timeline_blocks_tc_by_loop` (L9465)

### Q4. 색상 layer 관계 — (c) 직교 layer
- **22 카테고리** (자동, `.sch` 파싱) ↔ **6 평가 항목** (평가자 주관)
- 사이클 바 = 두 layer:
  - 배경 (auto layer): 22 색상 (현재 그대로)
  - 전경 (eval layer): 6 평가 항목 frame/border (평가자 매핑된 TC 만)
- 토글: auto only / eval only / both
- **전제조건**: `.sch` 분석 로직 신뢰도 = 22 카테고리 정확도

### Q5. 22 재검증 — (0)→(a)→(b)→(c)→(d) 5단계
0. **`_classify_loop_group` parsing gap 검토** — `.sch` 누락된 정보 식별 (사용자 추가)
1. **(a) 187 폴더 전수 분류 → 통계 dump** (wiki md)
2. **(b) 22 카테고리 spec audit** — 도메인 명문화
3. **(c) `_classify_loop_group` 룰 fix**
4. **(d) 정확도 측정** — confusion matrix

---

## 2. 검증 대상

| 시험 종류 | 폴더 수 | 위치 |
|---|---|---|
| 성능 | 103 | `raw/raw_exp/exp_data/성능/` |
| 성능_hysteresis | 16 | 동상 |
| 성능_시험직후 | 10 | 동상 |
| 수명 | 36 | 동상 |
| 수명_복합floating | 22 | 동상 |
| **합계** | **187** | |

`.sch` = PNE binary schedule file (`PNE power supply schedule file`).
Toyo 는 `.ptn` 사용 — 별도 검증 (본 plan scope 외).

내장 parser 위치: `DataTool_optRCD_proto_.py` L64 (`HAS_SCH_PARSER=True`), L7560 부근 (`PNE .sch 바이너리 파서 (내장)`).

---

## 3. 5단계 작업 spec

### (0) `_classify_loop_group` parsing gap 검토

**목표**: 분류기 input 의 완전성 검증 — `.sch` 의 어떤 정보가 parser → 분류기로 전달 안 되는지 식별.

**3 sub-step**:
| Step | 작업 | Cost |
|---|---|---|
| (0-1) | parser 코드 audit — 파서가 읽는 필드 list, 무시되는 byte offset | 빠름 (코드 review only) |
| (0-2) | 187 `.sch` 전수 parser output dump (dict per file) | 중간 (자동, 1-2 시간) |
| (0-3) | hex/string field cross-check (sample 5-10) — raw vs parser output diff | 중간 |

**산출물**:
- ✅ **(0-1a) 완료**: [[260504_audit_phase0_sch_parsing_gap]] — parser 코드 review + ⚠️ `v_chg` 키 mismatch bug 발견
- ✅ **(0-1b) 완료**: [[260504_audit_phase0_extractable_fields]] — 4 sample binary dump → header field 전체 list
- ✅ **(0-1c) 완료**: [`tools/sch_csv_crosscheck.md`](../../tools/sch_csv_crosscheck.md) — 10 CSV ↔ 9 .sch capacity 100% 일치
- ✅ **(0-1d) 완료**: [[260504_audit_phase0_csv_sch_step_alignment]] — step-level alignment (3 sample) + 5 신규 + 1 정정
- ✅ **(0-2) 완료**: [[260504_audit_phase0_2_187_validation]] — **368 파일 / 28,779 step 전수** 가설 검증. **8 가설 중 6 ⭐⭐⭐ + 2 partial**.
- ✅ **(0-3) 완료**: [[260504_audit_phase0_3_pne_ui_review]] — PNE 패턴 편집기 UI 캡처 (ECT GITT) cross-check. 신규 15+ field 발견.
- ✅ **(0-4) 완료**: [[260504_audit_phase0_4_dcir_pattern_review]] — DCIR 패턴 (SOC별 DCIR_2610mAh) UI cross-check. ⭐⭐⭐ **SOC/DOD 이동 조건 mechanism** 식별.
- ✅ **(0-5) 완료**: [[260504_audit_phase0_5_classifier_input_spec]] — Phase 0 audit 종합. 4 추가 sample (hysteresis / RSS / 일반수명 / 복합floating) + ⭐⭐⭐ **사용자 핵심 통찰**: CC vs CCCV voltage 컬럼 의미 분리, 분류 input 5 base (mincapacity / 인가 전류 / 전압 / EndCondition / sampling). **분류기 v2 spec + Phase c implementation plan**. ⭐ Phase 0 audit **종료**.
- 도구: [`tools/sch_dump.py`](../../tools/sch_dump.py), [`tools/sch_list_lite.py`](../../tools/sch_list_lite.py), [`tools/sch_csv_crosscheck.py`](../../tools/sch_csv_crosscheck.py), [`tools/sch_csv_step_align.py`](../../tools/sch_csv_step_align.py), [`tools/sch_phase0_2_validation.py`](../../tools/sch_phase0_2_validation.py)

### (a) 187 폴더 전수 통계 dump

**목표**: 22 카테고리 × 187 폴더 분포 → spec audit 우선순위 결정.

**산출물 wiki md content (jamin schema)**:
1. **폴더별 분류 결과 table** — 행=폴더 (187), 열= 22 카테고리 + Unknown + TC 총수
2. **시험종류별 cross-table** — 행=5 시험종류, 열=22 카테고리, 셀=발견 빈도
3. **Unknown / 빈 결과 list** — 분류기 실패 케이스 (우선 손볼 대상)
4. **폴더명-카테고리 불일치 의심 list** — 폴더명 'hysteresis' 인데 HYSTERESIS 0개 등
5. **카테고리별 빈도 ranking** — drill-down 우선순위

**산출물 위치**: `wiki/10_cycle_data/260504_audit_phase_a_187_stats.md`

### (b) 22 카테고리 spec audit

**목표**: 카테고리 정의의 모호성 제거 — 평가자 + 코드 합의.

(a) 결과로 우선순위 5-7 카테고리 선정. 80% cover.

**산출물**: `wiki/13_logical_cycle/260504_audit_phase_b_category_spec.md` — 카테고리별 도메인 정의 + `.sch` 패턴 + 분류 룰.

### (c) `_classify_loop_group` 룰 fix

**목표**: (b) spec 기준으로 분류기 코드 수정.

**산출물**: PR 1+ 건 + changelog wiki.

### (d) 정확도 측정

**목표**: confusion matrix (per-category precision/recall).

**Ground truth**: (b) spec + 평가자 manual review (또는 `.sch` metadata + SaveEndData cross-check).

**산출물**: `wiki/10_cycle_data/260504_audit_phase_d_accuracy.md` — 정확도 metrics + remaining issues.

---

## 4. 후속 (audit 완료 후): 6 평가 항목 매핑 layer

22 재검증 완료 후 본 plan 의 다음 phase:

| Phase | 작업 | 비고 |
|---|---|---|
| **Eval-1** | TC 카테고리 × 지표 함수 dict 구축 (`_tc_indicator_specs(tc, df) → dict`) | 자동 산출, Phase A |
| **Eval-2** | 6 평가 항목 mapping UI — 사이클 바 over-paint + 토글 상세 | UI, Phase B |
| **Eval-3** | 영속화 — `.sch` signature → 매핑 cache | json/QSettings |
| **Eval-4** | 평가 view 출력 — 데이터 서브탭 inner 탭 / 별도 outer 탭 / plot annotation | UI 결정 필요 |
| **Eval-5** | default mapping rule (6 → 22 super-grouping) — yaml 또는 hardcode | spec 결정 필요 |

**ADR 후보**: 평가 매핑 (c) 직교 layer 결정 → audit 완료 후 ADR-0012 로 정식화 (ADR-0011 은 daily-weekly-quarterly-pipeline 에 이미 사용).

---

## 5. 6 평가 항목 spec (참고, audit 후 정식화)

평가자가 초기 셀 평가 시 보는 항목 (260504 사용자 정의):

| # | 평가 항목 | sub-지표 | 22 카테고리 default mapping (잠정) |
|---|---|---|---|
| 1 | 초기 방전 용량 | 방전용량 값 / nominal voltage | `방전(초기)`, `사이클(FORMATION)` 첫 dchg |
| 2 | 율별 충전 비교 | 시간별 V·Crate·SOC / 10·30분 충전량 / 멀티스텝 구간별 / CCCV 완료 시간 | `충전(세팅)`, `사이클(ACCEL)` |
| 3 | 율별 방전 비교 | SOC-V / SOC-T / Max T / DOD (Cell·Pack spec) | `방전`, `사이클(ACCEL)` |
| 4 | Hysteresis 방전 (TC3-12) | hyst SOC define / 1.0C·0.5C 스텝 / 발열·DOD ratio·방전시간 ratio | `히스테리시스(방충전)`, `히스테리시스(충방전)` |
| 5 | 1달 방치 후 0.2C 용량 | 방치 전후 용량 비교 | `저장`, `RPT` 페어 |
| 6 | DCIR-OCV / DCIR-SOC | DCIR vs OCV/SOC 곡선 | `DCIR`, `GITT` |

각 sub-지표는 Phase A 의 `_tc_indicator_specs` 함수가 자동 산출.

---

## 6. Related

- [[260428_profile_4modes_spec]] — 4 종 분석 모델 spec
- [[260428_changelog_profile_data_subtab]] — 데이터 서브탭 (현재 raw DataFrame)
- [[260427_changelog_data_subtab]] — 사이클 분석 데이터 서브탭 (`_cycle_sheet_specs` 패턴)
- [[260418_p3_cyc_tier2_loop_detect]] — TC 분류기 P3
- [[260419_사이클분류_전면재검토]] — 분류기 전면 재검토
- [[hub_logical_cycle]] — 논리 사이클 hub
- [[260504_daily_worklog]] — 본 grilling 진행일

---

## 7. CONTEXT.md / ADR 정합

- **CONTEXT.md** "미해결 / 후속 작업" → 본 plan 으로 Item 1 (옵션별 plot + 데이터 출력) 발전 + 신규 Item 6 (22 재검증) 추가.
- **ADR-0012 후보**: 평가 매핑 (c) 직교 layer — audit 완료 후 (5단계 (d) 통과 시) 정식화. (ADR-0011 은 daily-weekly-quarterly-pipeline 에 사용됨)
- **`.sch` parsing 검증 결과는 ADR 0001~0003 (3-layer pipeline) 의 Layer A "raw IO + 사이클러 판별 + 메타 확보" 의 신뢰도 base** — Layer A 의 메타 (TC 분류) 가 Layer C 의 평가 view 의미를 결정.
