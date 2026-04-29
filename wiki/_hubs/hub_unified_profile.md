---
title: "🧪 Hub — Unified Profile"
aliases: [Unified Profile Hub, 통합 프로파일 허브]
tags: [hub, profile-unified, refactor, strategy-pattern, 4-modes]
type: hub
status: active
updated: 2026-04-28
---

# 🧪 Hub — Unified Profile (통합 프로파일)

> 5 프로파일 분석 함수(Step / Rate / Chg / Dchg / Continue) → **`unified_profile_core()`** 6-stage 파이프라인 통합.

> 상위 → [[../Wiki_Master_Index]]

---

## 📖 한 문단 요약

프로파일 분석은 Step, Rate, Chg, Dchg, Continue 5가지 기능이 각각 독립 함수로 구현되어 있었고, 공통 로직(로드·단위변환·dQ/dV·스텝연결)이 중복되었습니다. **`unified_profile_core()`** 는 이 5개 함수를 4개 옵션(mode, overlay, continuous, time)으로 통합한 단일 엔진입니다. UI 측에서는 5 버튼 → 4 옵션 위젯 + 1 버튼으로 축소되었고, 렌더링 측에서는 6 버튼의 공통 루프를 `_profile_render_loop()` (Strategy Pattern)로 추상화해 코드 56%를 제거했습니다.

---

## 🧩 6-Stage Core Pipeline

```
Stage 1: LOAD         raw 데이터 1회 로드 (채널/사이클별 캐시)
Stage 2: UNIT CONV    μV/μA/μAh → V/A/Ah (PNE), 단위 정규화
Stage 3: STEP MERGE   step 단위 병합 (cumsum 기반 그룹핑)
Stage 4: CONTINUOUS   연속 시간 축 결합 (옵션: continuous)
Stage 5: DQDV         dQ/dV 계산 (옵션: overlay='dQdV')
Stage 6: RENDER       _profile_render_loop (3-mode: CycProfile/CellProfile/AllProfile)
```

---

## 📐 분석 모델 Spec (4종, 2026-04-28 draft)

> 코드 아키텍처(unified_profile_core)는 옵션 조합 모델이지만, 사용자 mental model은 4종 분석(방전/충전/전체/히스테리시스). 본 spec 셋은 후자 관점에서 target을 정의하고 현재 코드와의 격차를 명시.

| 문서 | 핵심 |
|---|---|
| [[260428_profile_4modes_spec]] | 4종 분석 모델 명세 — X축/Y축/페어링/좌표계 ⭐ |
| [[260428_profile_view_color_spec]] | 그래프 구성·색상 체계 — 경로/채널/사이클 × 단일/다중탭 |
| [[260428_profile_gap_current_vs_target]] | 격차 분석 G1~G5 + Phase 로드맵 |

---

## 🎯 설계·검증 (Analysis)

| 문서 | 핵심 |
|---|---|
| [[260317_cycle_profile_data_summary]] | 6축 구성·병렬 로딩·전체 흐름 |
| [[260404_comparison_unified_profile_validation]] | 기존 5함수와 동일성 검증 (실데이터 PASS) |
| [[260410_analysis_profile_option_redesign]] | 로드 1회 + Stage 캐싱 (150ms → 5ms) |
| [[260707_analysis_profile_unified_architecture]] | 통합 아키텍처 완성도 검증 |

---

## 🛠️ 구현 (Changelog)

| 문서 | 영역 | 핵심 |
|---|---|---|
| [[260404_changelog_unified_profile_core]] | Core | 4 옵션 엔진 신규 (설계 상세 포함) |
| [[260404_changelog_unified_profile_batch]] | Batch | 10 → 1 배치 함수 (병렬 ThreadPoolExecutor 포함) |
| [[260404_changelog_unified_profile_ui]] | UI | 5 버튼 → 4 옵션 위젯 |
| [[260404_refactor_profile_render_loop]] | Render | `_profile_render_loop()` 추출 (56% ↓, Strategy Pattern 포함) |
| [[260404_comparison_unified_profile_validation]] | 🐛 | 실환경 버그 5건 수정 (Phase 4) |
| [[260405_changelog_test_profile_analysis]] | Test | 1,900건 자동 검증 |
| [[260620_analysis_dcir_unified_classification#9. Condition=9 CC 재분류 (260405)|260620_analysis_dcir_unified_classification §9]] | 🐛 | Condition=9 CC 단계 필터 |

---

## 📚 학습 (Learning)

| 문서 | 핵심 |
|---|---|
| [[260405_review_cycle_and_profile_analysis_logic]] | 데이터 처리 파이프라인 상세 |
| [[260404_changelog_unified_profile_core#설계 상세|260404_changelog_unified_profile_core §설계 상세]] | Core 설계 원리 (⭐, 병합됨) |
| [[260404_refactor_profile_render_loop#학습 / Strategy Pattern 설명|260404_refactor_profile_render_loop §학습]] | Strategy Pattern 리팩토링 (병합됨) |
| [[260404_changelog_unified_profile_batch#아키텍처 (ThreadPoolExecutor)|260404_changelog_unified_profile_batch §아키텍처]] | 병렬 ThreadPoolExecutor 배치 (병합됨) |
| [[260405_review_cycle_and_profile_analysis_logic]] | 전체 로직 완전 해석 |
| [[260411_review_cycle_pipeline_full_analysis]] | 통합 리빌딩 + 로직 상세 |

---

## 🎛️ Ch Popup / Render Detail

| 문서 | 핵심 |
|---|---|
| [[260317_3level_ch_popup_chg_dchg_continue]] | 3-level 채널 계층 |
| [[260317_ch_popup_profile_functions]] | 프로파일 함수 Line2D 반환 |
| [[260311_legend_ch_popup_analysis]] | 5가지 모드별 채널 그룹 |

---

## 🔬 도메인 연결 (Vault)

- [[데이터_전처리_통합]] — 충방전 전처리 통합 (Overview / Load / PNE / Gen4 ATL)
- [[충방전_매커니즘]]

---

## 🗝️ Key Function Signature

```python
def unified_profile_core(
    data,
    mode: Literal['CycProfile', 'CellProfile', 'AllProfile'],
    overlay: Literal['none', 'dQdV', 'incremental'],
    continuous: bool,
    time: bool,
) -> dict: ...
```

4 옵션 조합 → 5 기존 함수 동작 완전 커버.

---

## ❓ 자주 묻는 질문

- **Q**: 왜 Strategy Pattern인가?
  → 3 렌더 모드(CycProfile/CellProfile/AllProfile)가 데이터 구조와 축 계산이 다르지만 공통 루프 구조를 가지므로.
- **Q**: 옵션 캐싱은 어디에서 되나?
  → Stage 1~3 결과를 채널×사이클 키로 캐시. 재클릭 시 Stage 4~6만 재실행.
- **Q**: Condition=9 버그는 왜 생겼나?
  → PNE 펄스 데이터에서 CC 단계의 전류 부호가 조건 번호와 맞지 않아, 충전/방전 재분류가 필요했음. [[260620_analysis_dcir_unified_classification#9. Condition=9 CC 재분류 (260405)|260620_analysis_dcir_unified_classification §9]].
