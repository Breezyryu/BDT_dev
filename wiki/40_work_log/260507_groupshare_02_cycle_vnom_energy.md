---
title: "260507 그룹 공유 §2 — 사이클 정격V + Energy ratio"
tags: [presentation, group_share, BDT, cycle_tab, vnom, energy_ratio]
date: 2026-05-07
parent: "[[260507_BDT_update_groupshare]]"
status: draft
---

# §2. 사이클 탭 — 정격전압 + Energy ratio

발표 본문 §2 보충 자료.

## 배경

- 절대값 그래프 한계 — Q_nom 이 다른 셀끼리는 y축 범위가 달라 한 plot에 겹쳐 두면 비교가 흐려짐
- Energy 그래프도 같은 문제 — 셀 용량·정격전압이 다르면 절대값으로는 fade 양상이 잘 안 잡힘
- 발표 본문 메시지 — "ratio 가 답이다"

## 변경 내역

| Commit | 날짜 | 요지 |
|---|---|---|
| `bbe9dda` | 5/3 | 경로 테이블 '정격V' 컬럼 추가 — 상세 2-4 Energy ratio 입력값 |
| `15c6089` | 5/3 | 정격V default 3.7 V → 3.9 V, ylabel V_nom 표기 제거 |
| `b9a03d7` | 5/3 | `graph_output_cycle_tab2` default v_nom NameError 수정 |
| `786abe1` | 5/3 | 상세 2-4 Discharge Energy → E / (Q_nom × 3.7V) ratio |
| `c7cfc28` | 5/3 | 사이클 상세 비율 그래프 3개 ylim/ytick 통일 (Dchg/Chg/Eng) |
| `2285d6d` | 5/2 | 사이클 바 상세정보 토글/패널 제거 — UI 단순화 |
| `5803272` | 5/1 | 사이클 분류 정규화 — schedule + 휴리스틱 분류 명칭 통일 |

## 구현 흐름

### 1. 정격V 컬럼

- 경로 테이블 컬럼 추가 — 행 단위로 셀별 정격V 입력
- 셀 스펙 자동 추출은 의도적으로 빼 둠 — 외부 셀·비교 평가용 셀까지 받기 위해
- 미입력 시 default — 3.9 V (예전 3.7 V → high-Ni NCM 셀에 맞춤)

### 2. Energy ratio 정의

- 정의 — `E_dchg / (Q_nom × V_nom)`
  - 분자 — 측정된 방전 에너지 (Wh)
  - 분모 — 정격 용량 × 정격 전압 (Wh, 셀 spec)
  - 결과 — 1.0 근방의 무차원 ratio
- 위치 — 사이클 상세 탭 (탭 2-4)

### 3. ylim/ytick 통일

- 비율 그래프 3종 — Dchg ratio / Chg ratio / Eng ratio
- ylim·ytick 동일 강제 → 위아래 stack 시 fade 양상이 정량 비교됨
- ylabel V_nom 표기는 떼고 ratio만 표시 — 정격V는 컬럼에서 확인

### 4. 사이클 바 상세정보 패널

- 제거 사유 — 같은 정보가 사이클 상세 탭에 이미 있어 화면을 잠식
- 토글·패널 모두 제거, 핵심 metric만 사이클 바 자체 라벨로

### 5. 분류 정규화

- 기존 — schedule 기반 분류 명칭과 휴리스틱 분류 명칭이 달라 동일 시험이 두 이름으로 혼재
- 변경 — 신 명칭 체계로 일원화 → 후속 fade fit·히스테리시스 분석에서 카테고리 매칭이 안정됨

## 사용자 체감

- 셀 용량·정격전압이 다른 시험을 한 plot에 올려도 fade 양상이 직접 비교됨
- 정격V 변경 시 ratio가 즉시 재계산
- 사이클 바가 깔끔해짐 — 상세 패널이 사라져서

## 검증

- 회귀 검증기 (BDT 4-케이스) — Dchg/Chg/Eng 비율 그래프 baseline 비교
- `b9a03d7` NameError 케이스 — `graph_output_cycle_tab2` 단위 테스트로 default 처리 확인

## Q&A 보강

- "정격V를 셀 스펙에서 자동으로 가져오면 안 되나?"
  → 외부 셀·비교 평가용 셀까지 받기 위해. 자동 추정은 후속 과제
- "default 3.9 V는 어떻게 정했나?"
  → 최근 high-Ni NCM 라인업 평균 — Q8 라인업 (ATL/SDI/COSMX). 셀 별도 입력 시 무시됨
- "Energy ratio가 1.0을 넘는 케이스는?"
  → 측정 정격이 spec 정격보다 높거나, 정격V·Q_nom 입력이 spec과 다른 경우. 비율 자체는 정량 지표라 1.0 cap을 강제하지 않음
- "사이클 바 상세 패널을 다시 켤 수는 있나?"
  → 현재는 영구 제거. 필요 metric은 사이클 바 라벨 또는 사이클 상세 탭에서 확인

## 관련 자료

- `wiki/10_cycle_data/260426_fix_cycle_axes_y_fit.md`
- `wiki/10_cycle_data/260505_sync_detail_tab_ratio_axes_ylim.md`
- `wiki/10_cycle_data/260415_tc_info_and_cycle_groups.md`
- `wiki/10_cycle_data/260411_analysis_cycle_pipeline_complete.md`
