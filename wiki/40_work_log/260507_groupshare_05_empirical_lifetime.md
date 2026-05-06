---
title: "260507 그룹 공유 §5 — Empirical 수명 예측, 시험 매트릭스 관점"
tags: [presentation, group_share, BDT, empirical_lifetime, interpolation, NREL_SSC]
date: 2026-05-07
parent: "[[260507_BDT_update_groupshare]]"
status: draft
---

# §5. Empirical 수명 예측 — 어떤 시험이 필요한가

발표 본문 §5 보충 자료. 모델 식이 아닌 **시험 매트릭스 관점**.

## 핵심 메시지

- Empirical fade 모델은 결국 **interpolation**
- 측정 격자가 없으면 예측도 없다
- 격자 외곽이 비면 그 영역은 외삽 — 신뢰도 낮음

## 시험 격자 (개념)

| 축 | 의미 | 일반적 격자 | 비고 |
|---|---|---|---|
| 온도 | Calendar / Cycle 모두 적용 | -10 / 0 / 25 / 45 / 60 °C | Arrhenius 흐름 가정 |
| SOC (Calendar) | 보관 SOC | 30 / 50 / 80 / 100 % | calendar fade 주 변수 |
| DOD (Cycle) | 사이클 깊이 | 80% (full) / 50% / 30% | cycle fade 주 변수 |
| C-rate (Cycle) | 충·방전 속도 | 0.5C / 1C / 2C | 충전 / 방전 별도 격자 권장 |

### 격자의 의미

- **격자 내부** — 측정 점들 사이는 interpolation. 신뢰도 높음
- **외곽 corner** — 격자 끝점. 측정해야 모델이 그 영역을 fit
- **외삽 영역** — 격자 밖. 모델 fit 범위 밖이라 신뢰도 낮음

### 격자 설계 가이드

- 외곽 corner만 채워도 fade 모델은 fit 가능
- 내부 점은 비어도 interpolation으로 메운다 — 외곽이 우선
- 새 셀 평가 계획 단계에서 매트릭스를 점검한다

## BDT 처리 흐름

### 1. 자동 normalize

- 측정된 사이클 fade curve를 자동 normalize
- ratio 그래프 (Dchg / Chg / Eng) — 발표 본문 §2 참고
- 셀 용량·정격전압 무관 비교 가능

### 2. Calendar / Cycle 분리

- 분류기 v3 (발표 본문 §1) — Calendar / Cycle 시험을 분류 단계에서 분리
- 각각 다른 fit 흐름 (Calendar fade ≠ Cycle fade)

### 3. STORAGE_CYCLE 분리

- 보관 + 사이클 혼합 시험은 STORAGE_CYCLE 카테고리로 별도 처리
- 일반 cycling fade fit과 섞이지 않는다

### 4. (후속) interpolation 시각화

- 격자 내부 / 외곽 / 외삽 영역을 색상으로 구분
- 어떤 조건에서 외삽 risk가 큰지 사용자 화면에서 직접 확인

## 모델 후보 (참고용)

> 본 발표 범위는 시험 매트릭스. 모델 식 자체는 별도 세션.

- **NREL SSC NMC fade 모델** — Calendar + Cycle 분리 fit
  - Calendar — Arrhenius (T) × power law (t) × SOC dependence
  - Cycle — Arrhenius (T) × power law (cycle) × DOD/C-rate dependence
- **PINN / phygnn / PINNSTRIPES** (NREL 계열) — physics-guided 가속 모델
- 메모리 reference — `reference_nrel_ssc_lifetime`, `reference_phygnn`, `reference_pinnstripes`

## 그룹에 대한 부탁

### 신규 셀 평가 계획 시

- **격자가 비지 않도록** 매트릭스를 점검합니다
- 외곽 corner만 채워주시면 BDT가 fade 모델 fit까지 자동화
- 시간·예산 제약이 있으면 외곽 corner 우선, 내부 점은 후속 보강

### 진행 중 시험에서

- Calendar / Cycle / STORAGE 가 어느 카테고리로 분류되는지 사전 확인
- 분류 결과는 현황 탭 필터링 sub-tab 에서 확인 (§1 참고)

## 후속 발표

- 별도 세션 — NREL SSC 기반 NMC Calendar/Cycle fade 모델 식 + Q8 라인업 적용 결과
- 메모리 — `project_bdt_work_tracks` Track 4 (empirical, MBO ~50%)

## Q&A 보강

- "Empirical 모델 식은 무엇인가?"
  → 본 발표 범위 외. 별도 세션에서 NREL SSC 기반 NMC Calendar/Cycle fade 모델로
- "interpolation vs 외삽의 신뢰도 차이는 정량화 가능한가?"
  → 격자 내부는 fit residual, 외삽은 confidence interval 발산으로 정량화. BDT 후속 시각화에서 색상 구분 예정
- "Si 음극 셀에는 적용 가능한가?"
  → Si 하한 계수 반영은 후속 과제 (`260422_W17_biweekly_exec_report` §P6 참고)
- "외곽 corner만 측정해도 fit이 깨지지 않는 이유는?"
  → fade 모델은 매끈한 함수형 (Arrhenius·power law). 외곽이 잡히면 함수 파라미터가 결정된다. 내부 점은 검증용

## 관련 자료

- 메모리 — `reference_nrel_ssc_lifetime` / `reference_phygnn` / `reference_pinnstripes`
- 메모리 — `project_bdt_work_tracks` (Track 4 empirical)
- `wiki/40_work_log/260422_W17_biweekly_exec_report.md` §P6
- `wiki/30_modeling/AI_TF_Glossary_Simulation.md` (수명 카테고리 8 항목)
