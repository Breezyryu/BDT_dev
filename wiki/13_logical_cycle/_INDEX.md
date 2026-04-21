---
title: "🔄 13 Logical Cycle — INDEX"
aliases: [Logical Cycle INDEX, 13 INDEX]
tags: [MOC, logical-cycle, cycle-mapping]
type: index
updated: 2026-04-21
---

# 🔄 13 Logical Cycle — MOC

> 물리 TC(TotlCycle) ↔ 논리사이클 양방향 매핑. `cycle_map` 자료구조 중심. (7 files)

> 상위 → [[Wiki_Master_Index]] · 허브 → [[hub_logical_cycle]]

---

## 🎯 설계

- [[260404_analysis_pattern_vs_rawdata_cycle_mapping]] — Toyo PTN / PNE `.sch` ↔ Raw Data
- [[260406_review_logical_vs_original_cycle_flow]] — 원본 vs 논리 매핑 + 초기 설계 (⭐)

## 🛠️ 구현 Phase

- [[260404_impl_logical_cycle_phase_a]] — Phase A-1 + A-2: cycle_map 자동 생성 + GITT/DCIR 스윕 tuple
- [[260404_impl_logical_cycle_phase_b_label]] — Phase B: 경로 테이블 라벨
- [[260405_logical_cycle_redefinition]] — 정의 확장 (충방전+충전전용) + cycle_data 파이프라인 통합

## 🐛 수정

- [[260404_fix_gitt_halfcell_cycle_map]] — GITT 반셀 단방향 펄스
- [[260407_fix_ect_cycle_map_and_del_unlock]] — ECT 전체 TC 포함, Del 키

---

## 🔗 관련
- [[hub_logical_cycle]] · [[hub_cycle_pipeline]]
- [[GITT]] (21_electrochem) — GITT 시험 (스윕 대표)
- [[DCIR_측정_업체별]] (22_experiments)
- [[10_cycle_data/_INDEX\|10 Cycle Data]] — Toyo/PNE 파이프라인
