---
title: "🧬 Hub — Cycle Pipeline"
aliases: [Cycle Pipeline Hub, 사이클 파이프라인 허브]
tags: [hub, cycle-pipeline, data-flow, toyo-vs-pne]
type: hub
status: active
updated: 2026-04-21
---

# 🧬 Hub — Cycle Pipeline

> 경로 입력 → 파싱 → 병렬 로딩 → TC/논리사이클 매핑 → 카테고리 분류 → 그래프 출력.

> 상위 → [[../Wiki_Master_Index]]

---

## 📖 한 문단 요약

BDT 사이클 파이프라인은 **6단계 흐름**으로 동작합니다:
1. **경로 입력** (경로 테이블 or 신뢰성 엑셀)
2. **파싱** (PNE `.cyc`/`.sch` vs Toyo CSV/PTN)
3. **병렬 로딩** (ThreadPoolExecutor)
4. **사이클 매핑** (TC ↔ 논리사이클, `cycle_map`)
5. **카테고리 분류** (RPT / Rss / 가속수명 / GITT / initial)
6. **그래프 출력** (6 서브플롯: Dchg/Eff/Temp/DCIR/AvgV/Energy)

각 단계는 **Toyo vs PNE** 분기를 가지며, 두 사이클러의 근본적 차이(파일 단위 vs 통합, 스텝 vs 루프, μ단위 변환)를 흡수합니다.

---

## 🗺️ 전체 흐름 (Mermaid 개요)

전체 흐름을 Mermaid로 시각화한 문서 → [[260409_study_01_cycle_data_pipeline_overview]]

```
┌─ 경로 입력 ─┐
│ 경로 테이블 │
│ 신뢰성 엑셀 │
└──────┬──────┘
       ▼
┌─ 파싱 / 판별 ─┐
│ PNE or Toyo?  │   ← sig_ratio / has_both_ratio
└──────┬────────┘
       ▼
┌─ 병렬 로딩 ──┐
│ ThreadPool   │
│ per channel  │
└──────┬───────┘
       ▼
┌─ Cycle Map ──┐   ← 물리 TC ↔ 논리사이클
│ {논리: TC}   │   → Hub: Logical Cycle
└──────┬───────┘
       ▼
┌─ 카테고리 ───┐   ← RPT / Rss / 가속수명 / GITT
│ 분류 로직    │
└──────┬───────┘
       ▼
┌─ 그래프 ─────┐
│ 6 서브플롯   │
└──────────────┘
```

---

## 🎯 Architecture / Analysis

| 문서 | 핵심 |
|---|---|
| [[260411_analysis_cycle_pipeline_complete]] | 전체 파이프라인 완전 분석 (⭐) |
| [[260317_cycle_profile_data_summary]] | 6축 구성 · 병렬 로딩 |
| [[260310_toyo_cycle_data_pipeline_analysis]] | Toyo 용량산정·병합·효율 |
| [[260310_link_cycle_multi_path_analysis]] | 연결사이클 멀티경로 |

---

## 🛠️ 구현 (Changelog)

| 문서 | 핵심 |
|---|---|
| [[260407_fix_ect_cycle_map_and_del_unlock]] | ECT 전체 TC 포함 |
| [[260407_fix_table_multi_paste]] | 경로 테이블 다중 붙여넣기 |
| [[260412_cycle_pipeline_refactor]] | 7가지 로직 정비 (최종) |
| [[260405_logical_cycle_redefinition#cycle_data 파이프라인 통합 (260404)|260405_logical_cycle_redefinition §cycle_data 통합]] | cycle_map 파이프라인 통합 (병합됨) |

---

## 📚 학습 (Learning)

### 🎓 Study Series 01-05 (필독 학습 경로)
| 순서 | 문서 |
|---|---|
| 01 Overview | [[260409_study_01_cycle_data_pipeline_overview]] |
| 02 Toyo | [[260409_study_02_toyo_cycle_data]] |
| 03 PNE | [[260409_study_03_pne_cycle_data]] |
| 04 Graph | [[260409_study_04_graph_output_cycle]] |
| 05 DataFrame | [[260409_study_05_df_newdata_deep_dive]] |

### 🔄 리팩토링 여정
| 문서 | 핵심 |
|---|---|
| [[260318_cycle_unified_refactor]] | 6 → 1 통합 리팩토링 |
| [[260318_cycle_unified_refactor]] | 삭제/추가 함수 이력 |
| [[260411_review_cycle_pipeline_full_analysis]] | 아키텍처 문서 |
| [[260411_review_cycle_pipeline_full_analysis]] | 전체 정비 최종본 |

---

## ⚡ 성능 최적화 (Optimization)

| 문서 | 핵심 |
|---|---|
| [[260312_E1_pd_concat_optimization]] | `pd.concat` O(n²) → list append O(n) |
| [[260312_link_cyc_preprocess_refactor]] | 연결사이클 전처리 2단계 |
| [[toyo_cycle_data_optimization]] | `merge_loop` 2.36s → 벡터화 |
| [[pne_search_cycle_cache_optimization_260211]] | PNE CSV 캐싱 |
| [[batch_loading_optimization_260209]] | Step Profile 반복 제거 |

---

## 🔗 관련 허브

- [[hub_logical_cycle]] — cycle_map 중심
- [[hub_unified_profile]] — profile 측 파이프라인
- [[hub_dcir]] — 사이클 내 DCIR 추출

---

## 🔬 도메인 연결 (Vault)

- [[데이터_전처리_통합]] — 전처리 통합 (Overview / Load / PNE / Gen4 ATL)
- [[충방전기_정밀도]] — 충방전기 정밀도

---

## 🗝️ Key Data Structure: `df.NewData`

상세 컬럼별 물리 의미 → [[260409_study_05_df_newdata_deep_dive]]

| 컬럼 | 물리 의미 |
|---|---|
| `TotlCycle` | 물리 사이클 (PNE/Toyo 원본) |
| `Cycle` | 논리 사이클 (cycle_map 적용 후) |
| `DchgCap` | 방전 용량 |
| `Eff` | 쿨롱 효율 |
| `RndV`, `AvgV` | 평균 전압 |
| `Temp` | 온도 |
| `DCIR` | 기본 DCIR |
| `DchgEng` | 방전 에너지 |
