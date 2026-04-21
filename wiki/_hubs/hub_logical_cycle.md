---
title: "🔄 Hub — Logical Cycle"
aliases: [Logical Cycle Hub, 논리사이클 허브]
tags: [hub, logical-cycle, cycle-mapping]
type: hub
status: active
updated: 2026-04-21
---

# 🔄 Hub — Logical Cycle (논리사이클)

> 물리 TC(TotlCycle) ↔ 논리사이클 양방향 매핑. `cycle_map` 자료구조 중심의 전 문서 집결지.

> 상위 → [[../Wiki_Master_Index]]

---

## 📖 한 문단 요약

**논리사이클**은 사용자가 인식하는 논리적 사이클 번호이고, **TC(TotlCycle/OriCyc)**는 충방전기가 기록하는 물리적 사이클 번호입니다. 두 체계를 이어주는 자료구조가 **`cycle_map`** 이며, 이것은 dict 형태로 `{논리 사이클 번호: TC 또는 TC 범위}` 를 저장합니다. 일반 시험(1:1 매핑)과 스윕 시험(GITT·DCIR, tuple 범위 매핑) 두 모드를 자동 판별합니다.

---

## 🧩 핵심 개념 계층

```
TC (TotlCycle)          ← 물리적 충방전기 사이클 번호 (PNE/Toyo 원본)
  │
  ▼  cycle_map[논리번호] = TC 또는 (TC_start, TC_end)
  │
논리사이클 (Logical)     ← 사용자가 "1사이클" 이라고 부르는 단위
  │
  ▼  logical → UI
  │
UI 사이클                ← 사이클 바에 표시되는 블록
```

---

## 🎯 설계 (Analysis)

| 문서 | 핵심 |
|---|---|
| [[260406_review_logical_vs_original_cycle_flow#1. 초기 설계 (260404)|260406_review_logical_vs_original_cycle_flow §1]] | 원칙 설정, 패턴별 적용, cycle_map 매핑 테이블 (병합됨) |
| [[260411_analysis_cycle_concepts_unification]] | TC / 논리 / UI / 사이클바 4개 개념 통일 |
| [[260411_analysis_cycle_pipeline_complete]] | 경로→TC→논리→UI→사이클바 전체 |
| [[260404_analysis_pattern_vs_rawdata_cycle_mapping]] | Toyo PTN / PNE `.sch` ↔ Raw Data 매핑 |

---

## 🛠️ 구현 (Changelog)

| 문서 | Phase | 핵심 |
|---|---|---|
| [[260404_impl_logical_cycle_phase_a]] | A-1 | 기본 cycle_map 자동 생성 (PNE/Toyo) |
| [[260404_impl_logical_cycle_phase_a#Phase A-2: GITT/DCIR 스윕 그룹핑|260404_impl_logical_cycle_phase_a §A-2]] | A-2 | GITT/DCIR 스윕 자동 감지, tuple 범위 (병합됨) |
| [[260404_impl_logical_cycle_phase_b_label]] | B | 경로 테이블 아래 라벨 표시 |
| [[260405_logical_cycle_redefinition#cycle_data 파이프라인 통합 (260404)|260405_logical_cycle_redefinition §cycle_data 통합]] | 통합 | cycle_data 파이프라인에 cycle_map 통합 (병합됨) |
| [[260404_fix_gitt_halfcell_cycle_map]] | 🐛 | GITT 반셀 단방향 펄스 수정 |
| [[260405_logical_cycle_redefinition]] | 확장 | 충방전 + 충전전용 사이클 |
| [[260407_fix_ect_cycle_map_and_del_unlock]] | 🐛 | ECT 전체 TC 포함 |
| [[260412_cycle_pipeline_refactor]] | 통합 | cycle_map 중복 정비 + PNE/Toyo 분기 통합 |

---

## 📚 학습 (Learning)

| 문서 | 핵심 |
|---|---|
| [[260321_review_cycle_classification_logic]] | 분류 로직: RPT/Rss/가속수명/GITT/initial |
| [[260406_review_logical_vs_original_cycle_flow]] | 논리 vs 원본 번호 체계 매핑 (필독) |
| [[260411_review_cycle_pipeline_full_analysis]] | 경로→TC→논리→UI 전체 |

---

## 🔬 도메인 연결 (Vault)

- [[GITT]] — GITT 시험 정의 (스윕 패턴의 대표)
- [[DCIR_측정_업체별]] — DCIR 시험 패턴
- [[충방전_매커니즘]] — 물리 의미

---

## 🗝️ Key Data Structures

```python
cycle_map = {
    1: 1,                    # 일반: 논리 1 = TC 1
    2: 2,
    ...
    # 스윕(GITT): 논리 10 = TC 20-35 (충방전 휴지 15 스텝)
    10: (20, 35),
    11: (36, 51),
    ...
}
```

---

## ❓ 자주 묻는 질문

- **Q**: TC와 논리사이클이 왜 다른가?
  → GITT/DCIR 시험은 1 사이클 내부에 여러 펄스 step이 들어가서 물리 사이클 번호가 급증함. 논리사이클은 "사용자 관점의 1사이클"을 유지.
- **Q**: cycle_map은 어디서 생성되나?
  → PNE의 경우 `.sch` 패턴 파일, Toyo의 경우 `PTN` 파일을 파싱해서 자동 생성. 스윕 여부는 `sig_ratio` + `has_both_ratio` 로 판별.
- **Q**: ECT 모드와 일반 모드 차이?
  → ECT(Extended Cycle Test)는 전체 TC를 cycle_map에 포함시켜야 함. [[260407_fix_ect_cycle_map_and_del_unlock]] 참고.
