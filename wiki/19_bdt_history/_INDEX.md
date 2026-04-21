---
title: "📜 19 BDT History — INDEX"
aliases: [BDT History INDEX, 19 INDEX]
tags: [MOC, bdt-history, misc, meta]
type: index
updated: 2026-04-21
---

# 📜 19 BDT History — MOC

> 주제별 4개 폴더에 속하지 않는 BDT 이력: 초기 리팩토링, UI, 개발 지침, 수명 예측, 신뢰성, DB 로드맵, 테스트 전략, 성능 최적화, 참고자료 등. (31 files — 2026-04-21 중복 7건 병합)

> 상위 → [[Wiki_Master_Index]]

---

## 📚 큰 줄기 리팩토링 이력

- [[260406_git_full_changelog]] — Git 전체 커밋 이력 (⭐ 통합 changelog — 초기 Phase, 17항목 비교 포함)
- [[260312_origin_vs_optRCD_proto_matching]] — 기능 대응 + 결과 차이 (260211) 포함
- [[260421_wiki_knowledge_network_restructure]] — Wiki MOC/허브 재구성
- [[260421_vault_flatten_to_wiki_root]] — vault → wiki flatten

---

## 🎨 UI / 초기 수정

- [[260310_bg_color_c_level_change]] — 현황 탭 배경색
- [[260310_remove_battery_from_filenames]] — `BatteryDataTool` 접두어 제거
- [[260407_fix_table_multi_paste]] — 테이블 다중 붙여넣기
- [[250613_search_white_bg_and_total_count]] — 검색 UI

## 🐛 초기 버그

- [[fix_append_deprecated_260209]] — pandas `_append()` → `pd.concat()`

## 📖 개발 지침 / Meta

- [[260319_instruction_files_improvement]] — `.github/instructions/` 6 파일 보강
- [[260310_battery_data_tool_update_mail]] — 업데이트 안내 메일
- [[260310_foldable8_ut_application]] — Foldable 8 UT 신청
- [[chat_summary_260209]] — 논리사이클·피크온도·단위 요약

---

## ⚡ 성능 최적화 이력

- [[260312_E1_pd_concat_optimization]] — `pd.concat` O(n²) → O(n)
- [[260312_improvement_priority_matrix]] — 34개 개선 매트릭스 + 상세 제안 본문 (병합)
- [[merge_pipeline_explanation]] — Toyo cycle 병합 파이프라인 (cumsum 그룹핑 + `groupby().apply()` 집계)
- [[button_workflow_analysis_260211]] — 버튼 6종 분류
- [[data_processing_logic_260211]] — 파싱 후처리 로직

---

## 📊 데이터 / 검증 (.txt 포함)

- [[260327_cyc_validation_report]] — `.cyc` 검증 리포트 (txt)
- [[250714_analysis_sch_field_map]] — PNE `.sch` 필드맵 (44파일·895블록)
- [[260318_reliability_multi_folder_analyzer]] — 신뢰성 32폴더·106항목

---

## 🧠 수명 예측 / 라이브러리

- [[lifetime_prediction_deep_search]] — DCIR+용량 선형회귀
- [[parameter_generator_v9.4_analysis_260220]] — Parameter Generator v9.4
- [[240323_pybamm_plot_axis_matching]] — PyBaMM OCP 곡선
- [[260410_analysis_library_recommendation_for_bdt]] — PyMOO / SymPy / PyTorch 추천
- [[pyinstaller_warnings_260306]] — PyInstaller 빌드 경고

> 📎 `pybamm_output_variables_260226` 은 `30_modeling/` 으로 이동됨.

---

## 🧾 Plan / SOP (옛 tech-docs)

- [[260320_plan_battery_db_roadmap]] — PostgreSQL DB 전략·Phase 0-5
- [[260407_plan_testing_strategy]] — 22k줄 테스트 전략 Level S/A/B/C
- [[260322_SOP_convert_reliability_to_csv]] — DRM `.xls` → CSV 변환

---

## 🔗 관련

- [[hub_cycle_pipeline]] · [[hub_unified_profile]] · [[hub_logical_cycle]] · [[hub_dcir]]
- [[MOC_Modeling_AI]] (30_modeling) — 수명 예측 연결
- [[MOC_Experiments]] (22_experiments) — 신뢰성 연결
- [[배터리_정보_실험데이터_DB화]] (21_electrochem) — DB 연결
