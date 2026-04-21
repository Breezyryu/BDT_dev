---
title: "📐 Hub — DCIR"
aliases: [DCIR Hub, DC-IR 허브]
tags: [hub, dcir, impedance, unified-classification]
type: hub
status: active
updated: 2026-04-21
---

# 📐 Hub — DCIR (DC Internal Resistance)

> 기본(10s) / RSS / SOC5·50 1s 펄스 — 3가지 DCIR 계산 모드의 통합 분류.

> 상위 → [[../Wiki_Master_Index]]

---

## 📖 한 문단 요약

DCIR(DC Internal Resistance)은 배터리 직류 내부저항이고, BDT는 **3가지 계산 방식**을 지원합니다:
1. **기본(MK) 10s** — 방전 펄스 시작과 10s 지점 전압 차
2. **RSS** — 여러 전류 step의 전압 응답을 최소제곱 회귀
3. **SOC5 / SOC50 1s 펄스** — 특정 SOC에서 1s 짧은 펄스로 측정

각 모드는 원래 코드에서 개별 분기·컬럼으로 분산되어 있었고, `260620_analysis_dcir_unified_classification` 에서 **통합 분류 체계**로 설계되었습니다. 실제 버그는 초기 SOC70 분기 조건 `>` → `>=` 수정, Condition=9 CC 단계 필터 등이 있었습니다.

---

## 🎯 통합 설계 (Analysis)

| 문서 | 핵심 |
|---|---|
| [[260620_analysis_dcir_unified_classification]] | 3 모드 통합 분류 (⭐) |
| [[260310_toyo_cycle_data_pipeline_analysis]] | Toyo DCIR 파이프라인 |
| [[260312_origin_vs_optRCD_proto_matching#결과 차이 (260211) — 병합 흡수]] | origin vs opt DCIR 계산 차이 (병합됨) |

---

## 🛠️ 구현 / 버그 수정 (Changelog)

| 문서 | 핵심 |
|---|---|
| [[260620_analysis_dcir_unified_classification#8. SOC70 분기 수정 (260310)|260620_analysis_dcir_unified_classification §8]] | SOC70 분기 `>` → `>=` 수정 |
| [[260620_analysis_dcir_unified_classification#9. Condition=9 CC 재분류 (260405)|260620_analysis_dcir_unified_classification §9]] | Condition=9 CC 단계 전류 부호 재분류 |
| [[260412_cycle_pipeline_refactor]] | DCIR 컬럼 정비 (7가지 중 1) |

---

## 📚 학습 (Learning)

| 문서 | 핵심 |
|---|---|
| [[260409_study_03_pne_cycle_data]] | PNE 처리 라인별, 3 DCIR 모드 구현 (⭐) |
| [[260409_study_05_df_newdata_deep_dive]] | `df.NewData` DCIR 컬럼 물리 의미 |
| [[260321_review_cycle_classification_logic]] | Rss/가속수명/GITT — DCIR 시험 분류 |

---

## 🔬 도메인 연결 (Vault)

- [[DCIR_측정_업체별]] — 업체별 DCIR 측정 방식 (중요)
- [[HIOKI_전극저항_측정]] — 전극 저항 측정
- [[Electrochemical_parameter]] — 전기화학 파라미터
- [[GITT]] — GITT (DCIR 스윕 대표)

---

## 🗝️ 3 Modes Cheat Sheet

| 모드 | 펄스 길이 | SOC 타겟 | 계산 방식 | 사용 |
|------|---------|---------|---------|------|
| 기본 (MK) | 10s | 전 SOC | ΔV / ΔI (10s) | 표준 DCIR |
| RSS | 가변 | 전 SOC | 최소제곱 회귀 | 정밀 모드 |
| 1s 펄스 | 1s | SOC5, SOC50 | ΔV / ΔI (1s) | 특정 SOC 저항 프로파일 |

---

## ❓ 자주 묻는 질문

- **Q**: SOC70 버그는 왜 생겼나?
  → 분기 조건이 `>` 이면 `SOC==70` 일 때 DCIR 분기를 놓침. `>=` 로 수정. [[260620_analysis_dcir_unified_classification#8. SOC70 분기 수정 (260310)|260620_analysis_dcir_unified_classification §8]]
- **Q**: Condition=9 펄스 필터는?
  → PNE에서 CC 단계의 전류 부호로 충/방전을 재분류해야 펄스 데이터가 정확히 분리됨. [[260620_analysis_dcir_unified_classification#9. Condition=9 CC 재분류 (260405)|260620_analysis_dcir_unified_classification §9]]
- **Q**: RSS 모드는 언제 쓰나?
  → 정밀 DCIR이 필요하고 다수 전류 step이 확보된 시험에서. GITT와 유사한 구조.

---

## 🔗 관련 허브

- [[hub_logical_cycle]] — DCIR 스윕 시험은 cycle_map 스윕 모드와 연동
- [[hub_cycle_pipeline]] — DCIR 컬럼은 파이프라인 최종 출력
