---
title: "🧪 11 Profile Analysis — INDEX"
aliases: [Profile INDEX, 11 INDEX]
tags: [MOC, profile, unified-core, render-loop]
type: index
updated: 2026-04-28
---

# 🧪 11 Profile Analysis — MOC

> 5 프로파일 함수 → `unified_profile_core()` 6-stage · `_profile_render_loop()` Strategy Pattern · Ch Popup. (16+ files)

> 상위 → [[Wiki_Master_Index]] · 허브 → [[hub_unified_profile]]

---

## 📐 4종 분석 모델 Spec (2026-04-28, draft)

- [[260428_profile_4modes_spec]] — 4종 분석 (방전/충전/전체/히스테리시스) 모델 명세 ⭐
- [[260428_profile_view_color_spec]] — 그래프 구성(경로/채널/사이클) × 탭 구조 × 색상 체계
- [[260428_profile_gap_current_vs_target]] — 현재 코드 vs target 격차 (G1~G6) + Phase 로드맵

## 🛠️ Phase 2.5 — G6 적용 changelog (2026-04-28)

- [[260428_changelog_g6_path_color]] — 전체통합+다중경로 plot 색상 path 차원 회복 ✅

---

## 🎯 Core 엔진

- [[260404_changelog_unified_profile_core]] — 4 옵션 엔진 신규 (⭐, 설계 상세 포함)
- [[260404_comparison_unified_profile_validation]] — 5 기존 함수 동일성 검증 + 실환경 버그 5건
- [[260410_analysis_profile_option_redesign]] — 옵션 캐싱 (150ms→5ms)
- [[260707_analysis_profile_unified_architecture]] — 완성도 검증
- [[profile_confirm_analysis]] — 프로파일 확인

## 🔁 Render Loop

- [[260404_refactor_profile_render_loop]] — `_profile_render_loop()` 추출 (56%↓, Strategy Pattern 포함)

## 📦 Batch Loader

- [[260404_changelog_unified_profile_batch]] — 10→1 배치 (병렬 ThreadPoolExecutor 포함)
- [[batch_loading_optimization_260209]] — Step Profile 반복 제거

## 🎨 UI · 버그

- [[260404_changelog_unified_profile_ui]] — 5버튼→4옵션+1버튼
- [[260405_changelog_test_profile_analysis]] — 1,900건 자동 검증

## 🎛️ Channel Popup

- [[260317_3level_ch_popup_chg_dchg_continue]] — 3-level 채널 계층
- [[260317_ch_popup_profile_functions]] — Line2D 반환
- [[260311_legend_ch_popup_analysis]] — 5 모드별 채널 그룹

## 🧪 Toyo vs PNE (프로파일 측)

- [[260310_profile_data_toyo_vs_pne_comparison]] — 프로파일 로딩·변환 비교

## ⚡ 최적화 (개별 함수)

- [[optimize_pro_continue_260210]] — global writer / check_cycler 캐싱
- [[optimize_rate_chg_dchg_260210]] — rate/chg/dchg 3함수 동일 패턴

---

## 🔗 관련
- [[hub_unified_profile]] · [[hub_cycle_pipeline]]
- [[10_cycle_data/_INDEX\|10 Cycle Data]] (프로파일 ↔ 사이클 결합)
