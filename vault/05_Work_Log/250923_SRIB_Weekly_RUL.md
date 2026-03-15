---
title: "250923_SRIB_Weekly_RUL"
tags: [Work_Log, SRIB, RUL, 주간보고]
type: meeting
status: active
related:
  - "[[250912_SRIB_RUL_weekly]]"
  - "[[250930_W40_SRIB_weekly_RUL]]"
created: 2025-09-23
updated: 2026-03-15
source: "origin/250923_SRIB_Weekly_RUL.md"
---

#### 회의 일시

- 2025/09/23(화) 11:29 ~ 12:28 (Asia/Seoul GMT +09:00)

#### 참석자

<삼성전자>

- 선행Battery Lab.(MX) : 안성진 랩장/Safety Agent, 류성택
- Mobile Battery : Samarth Agarwal Head of Part, Herojit Sharma Laipubam, Rahul Kumar, Subramanian Swernath Brahmadathan

#### 저항 및 용량 모델링 결과 분석

• 저항(R) 및 제한 용량(Limited Capacity) 특성 활용 결과

- 저항만 사용 시: 메인 셀에서 높은 오차 발생 (약 0.3%~1.5%)

- 제한 용량만 사용 시: 메인 셀에서 용량 감소 현상 관찰 (약 250 사이클 부근)

- 저항과 제한 용량 동시 사용 시: 예측 종료 시점에서 용량 증가 현상 발생 (반복적 검증 필요)

• 온도 영향 분석

- 메인 셀에서 250 사이클 부근의 용량 감소는 온도 영향 가능성 존재

- 서브 셀 및 인너 셀에서는 용량 감소 현상 미관찰

• 전압 범위 조정 필요성

- 제한 용량 계산 시 전압 범위 조정 필요 (플랫폼별 차이 고려)

- 저항 계산 시 전압 범위 조정은 불필요 (CC1→CC2 전환점 안정적 범위 유지)

#### 체인 모델(Chain Model) 결과 분석

• A2 셀과 CL 셀 간 용량 변화 차이

- A2 셀 훈련 데이터와 CL 셀 테스트 데이터 간 높은 오차 발생

- CL 셀의 초기 용량 감소 현상 관찰

• 새로운 파이프라인 적용 결과

- R&D 용량 모델과 그룹 용량 모델 통합 사용

- 메인 셀에서 높은 오차 발생 (이전 모델과 유사)

- 서브 셀 및 인너 셀에서는 KPI 내 결과 도출

• 하이퍼파라미터 조정 필요성

- 새로운 파이프라인 적용 시 하이퍼파라미터 재검증 필요

- 이전 모델과의 일관성 유지 필요

#### 향후 작업 및 개선 방향

• 스택 모델(Stack Model) 개발 시작

- 다음 주부터 스택 모델 개발 시작 예정

- 초기 결과 도출 후 추가 검증 진행

• 새로운 특성 추가 검토

- 이완 전압(Relaxation Voltage) 특성 추가 가능성 검토

- 저항 및 제한 용량 특성 간 비교 분석 필요

• 회의 일정 조정

- 다음 날 15:00 KST에 추가 회의 예정

- 주요 이슈 및 개선 방향 논의 예정

## 관련 문서

- [[250821_SRIB_weekly_RUL]] (Meeting)
- [[250905_SRIB_weekly_RUL]] (Meeting)
- [[250912_SRIB_RUL_weekly]] (Meeting)
- [[250930_(W40) SRIB weekly RUL]] (Meeting)
- [[250829_SRIB_RUL]] (Meeting)
- [[모델링 방향]] (Meeting)
