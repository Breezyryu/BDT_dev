---
title: "250905_SRIB_weekly_RUL"
tags: [Work_Log, SRIB, RUL, 주간보고]
type: meeting
status: active
related:
  - "[[250829_SRIB_RUL]]"
  - "[[250912_SRIB_RUL_weekly]]"
created: 2025-09-05
updated: 2026-03-15
source: "origin/250905_SRIB_weekly_RUL.md"
---

# 회의 제목

SRIB Weekly - RUL

# 회의 일시

- 2025/09/04(목) 11:29 ~ 12:10 (Asia/Seoul GMT +09:00)

# 참석자

<삼성전자>

- 선행Battery Lab.(MX) : 안성진 랩장/Safety Agent, 류성택
- Mobile Battery : Samarth Agarwal Head of Part, Herojit Sharma Laipubam, Rahul Kumar, Subramanian Swernath Brahmadathan

# 코드 및 알고리즘 분석

• 저항과 Q의 상관관계 분석

- 저항이 Q와 강한 상관관계를 보임

- DQ VP 알고리즘 두 가지 탐색: 첫 번째 알고리즘은 전체와 상관관계가 있으나 서브 셀과는 상관관계가 낮음

- 두 번째 알고리즘은 상관관계가 매우 낮음

• TC 1 결과 공유

- 4V 상한 제한에서 정확도 개선 및 오차 감소 확인

- WHY BAS 팀의 용량 가뭄 및 초기 사이클(200~300 사이클) 관련 데이터 분석

- 전압 범위: 4.2V에서 3.2V까지

• 온도 및 용량 변화 분석

- 250VC에서 약 10도 온도 하락 관측

- 용량 변동은 200~300 사이클 구간에서 주로 발생

• 새로운 기능 소개

- 저항을 통한 용량 예측 가능성 논의

- DQDV를 통한 0.2C 용량 예측 가능성 검토

- 시리얼 및 병렬 작업 흐름 비교: 시리얼 방식(용량 예측 후 0.2C 용량 예측) vs 병렬 방식(동시에 예측)

• SOP 배터리 알고리즘 분석

- SOP 배터리에서 낮은 상관관계 관측

- 전압 범위 조정 필요성: 3.6V 대신 3.7V 사용 검토

- CC1과 CC2 전환점에서의 DQDV 분석 결과: 상관관계가 낮음

• 예측 결과 및 KPI 분석

- 4V 상한 제한에서 오차 감소 확인

- 0.2C 용량 예측을 위한 제한 용량 사용

- 훈련 데이터 범위(최대 1,200 사이클) 내에서 예측 결과 KPI 충족

- 2,000 사이클 이상 예측 시 오차 증가 가능성

• RUL 예측 및 SOH 분석

- RUL 알고리즘을 통한 SOH 예측 필요성 논의

- 물리 기반 모델과 머신러닝 결합 가능성 검토

- 45°C 데이터 활용 가능성: 가속화된 열화 데이터로 무릎 지점 예측 시도

- 현재 연구 결과: 좋은 예측 결과 도출되었으나 무릎 지점 예측은 어려움

• 향후 계획 및 액션 아이템

- 병렬 방식 알고리즘 설계 검토

- SOP 배터리 전압 범위 조정 및 알고리즘 개선

- RUL 예측을 위한 새로운 접근 방식 모색

- 45°C 데이터 활용 가능성 검토 및 추가 연구 진행

## 관련 문서

- [[250821_SRIB_weekly_RUL]] (Meeting)
- [[250912_SRIB_RUL_weekly]] (Meeting)
- [[250923_SRIB_Weekly_RUL]] (Meeting)
- [[250930_(W40) SRIB weekly RUL]] (Meeting)
- [[250829_SRIB_RUL]] (Meeting)
- [[수명_해석_방향]] (Meeting)
