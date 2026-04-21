---
title: "🗺️ Wiki Master Index"
aliases: [Wiki Master, Master Index, Knowledge Map]
tags: [MOC, master-index, navigation, home]
type: index
status: active
updated: 2026-04-21
---

# 🗺️ BDT Wiki — Master Index

> Topic-centric 지식 그래프. 주제별 폴더 + 크로스 허브 + 시작 인덱스.
> 스키마 → [[CLAUDE]]

---

## 🧭 폴더 빠른 이동

| 주제 | 폴더 | MOC |
|------|------|-----|
| 🧬 Cycle Data | [[10_cycle_data]] | [[10_cycle_data/_INDEX\|📘 INDEX]] |
| 🧪 Profile Analysis | [[11_profile_analysis]] | [[11_profile_analysis/_INDEX\|📘 INDEX]] |
| 📐 DCIR | [[12_dcir]] | [[12_dcir/_INDEX\|📘 INDEX]] |
| 🔄 Logical Cycle | [[13_logical_cycle]] | [[13_logical_cycle/_INDEX\|📘 INDEX]] |
| 📜 BDT History | [[19_bdt_history]] | [[19_bdt_history/_INDEX\|📘 INDEX]] |
| 🔬 Materials | [[20_materials]] | [[MOC_Battery_Knowledge\|📘 MOC]] (공유) |
| ⚗️ Electrochem | [[21_electrochem]] | [[MOC_Battery_Knowledge\|📘 MOC]] |
| 🧑‍🔬 Experiments | [[22_experiments]] | [[MOC_Experiments\|📘 MOC]] |
| 🧠 Modeling & AI | [[30_modeling]] | [[MOC_Modeling_AI\|📘 MOC]] |
| 💻 Software Dev | [[31_software_dev]] | [[MOC_Development\|📘 MOC]] |
| 📝 Work Log | [[40_work_log]] | [[MOC_Work_Log\|📘 MOC]] |

---

## 🏗️ Knowledge Graph 구조

```
wiki/                              ← Obsidian 볼트 루트
├── CLAUDE.md                      ← 스키마 정의
├── Wiki_Master_Index.md           ← 이 파일
│
│  ─── 💻 BDT 코드 주제 ───
├── 10_cycle_data/                 사이클 데이터 파이프라인 (31)
├── 11_profile_analysis/           통합 프로파일 (20)
├── 12_dcir/                       DCIR 3-모드 (3)
├── 13_logical_cycle/              TC↔논리사이클 매핑 (10)
├── 19_bdt_history/                기타 changelog·tech·잡식 (38)
│
│  ─── 🔬 배터리 도메인 ───
├── 20_materials/                  양극·음극·전해액·분리막 (24)
├── 21_electrochem/                이론·파라미터·시스템·BMS (22)
├── 22_experiments/                SOP·장비·전처리 (21)
├── 30_modeling/                   PyBaMM·PINN·수명 (22)
├── 31_software_dev/               Python·Julia·CUDA (11)
├── 40_work_log/                   주간보고·업무 (26)
│
│  ─── 🌐 인프라 ───
├── _index/                        Home · Dashboard · Base (3)
├── _hubs/                         크로스 주제 허브 (4)
├── 50_inbox/                      미분류 (1)
├── 99_templates/                  Obsidian 템플릿 (5)
└── 90_origin/                     원본 보존 — 수정 금지 (159)
```

---

## 🌐 크로스 도메인 허브 (Topic Hubs)

| 허브 | 설명 | 걸쳐진 폴더 |
|---|---|---|
| [[hub_logical_cycle\|🔄 Logical Cycle]] | TC ↔ 논리사이클 매핑 | 13 · 10 · 22 |
| [[hub_unified_profile\|🧪 Unified Profile]] | `unified_profile_core()` 파이프라인 | 11 · 10 · 22 |
| [[hub_cycle_pipeline\|🧬 Cycle Pipeline]] | 경로→그래프 전체 흐름 | 10 · 13 · 22 |
| [[hub_dcir\|📐 DCIR]] | 3-모드 통합 분류 | 12 · 21 · 22 |

---

## 🔗 코드 ↔ 도메인 교차 참조

| 코드 주제 | ↔ | 도메인 주제 |
|---------|---|-----------|
| [[260620_analysis_dcir_unified_classification]] (12) | ↔ | [[DCIR_측정_업체별]] (22) |
| [[260409_study_05_df_newdata_deep_dive]] (10) | ↔ | [[충방전_매커니즘]] (21) |
| [[lifetime_prediction_deep_search]] (19) | ↔ | [[수명_해석_방향]] · [[Empirical_Degradation_Models]] (30) |
| [[260410_analysis_library_recommendation_for_bdt]] (19) | ↔ | [[MOC_Modeling_AI]] · [[Python_환경설정]] (30 · 31) |
| [[260320_plan_battery_db_roadmap]] (19) | ↔ | [[배터리_정보_실험데이터_DB화]] (21) |
| [[260322_SOP_convert_reliability_to_csv]] (19) | ↔ | [[신뢰성_평가]] (22) |
| [[pybamm_output_variables_260226]] (19) | ↔ | [[PyBaMM_정리]] · [[PyBaMM_Solve]] (30) |

---

## 📊 볼륨 (2026-04-22 docs→wiki 통폐합 후)

| 폴더 | 04-21 중복통합 | 04-22 docs흡수 | Δ |
|------|-----|-----|----|
| 10_cycle_data | 26 | **61** | +35 (docs 이동) |
| 11_profile_analysis | 17 | **29** | +12 |
| 12_dcir | 2 | **3** | +1 |
| 13_logical_cycle | 8 | **14** | +6 |
| 19_bdt_history | 31 | **40** | +9 |
| 20_materials | 18 | **18** | — |
| 21_electrochem | 22 | **22** | — |
| 22_experiments | 17 | **18** | +1 |
| 30_modeling | 19 | **24** | +5 |
| 31_software_dev | 11 | **12** | +1 |
| 40_work_log | 25 | **25** | — |
| _hubs | 4 | 4 | — |
| _index | 3 | 3 | — |
| 50_inbox | 1 | 1 | — |
| 99_templates | 5 | 5 | — |
| 90_origin | 160 | 159 | — (수정 금지) |
| **합계** | **209** (+origin) | **440** (**281 non-origin**) | **+70 from docs merge** |

**docs/ (바이너리 전용)**: `.docx` · `.pptx` · `.xlsx` · `.pdf` · `.html` · `mockups/` · `reports/` · `_viz_output/` · `licenses/` · `testing/` (2026-04-22 .md 제거 완료)

---

## 📜 Schema / Rules

- **Naming**: `YYMMDD_<category-prefix>_<slug>.md` (code 측) · 자유 이름 (domain 측)
- **3층**: `raw/` (immutable) → `wiki/` (LLM-owned) → `outputs/` (answers)
- **폴더 선택**: 파일이 어느 주제에 가장 강하게 속하는지만 판단, 한 폴더 한 번만

## 🔧 Maintenance

- 🆕 새 문서 추가 시: 주제 폴더에 직접 드롭 + 해당 `_INDEX.md` 클러스터에 한 줄 추가
- 📅 3개월+ 업데이트 없는 문서 → `90_origin/` 또는 archive 후보
- ⚠️ 코드 변경 후 문서 검증: `> ⚠️ STALE (YYMMDD)` 마킹
