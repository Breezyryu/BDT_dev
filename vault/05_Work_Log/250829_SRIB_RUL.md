---
title: "250829_SRIB_RUL"
tags: [Work_Log, SRIB, RUL, 주간보고]
type: meeting
status: active
related:
  - "[[250821_SRIB_weekly_RUL]]"
  - "[[250905_SRIB_weekly_RUL]]"
created: 2025-08-29
updated: 2026-03-15
source: "origin/250829_SRIB_RUL.md"
---

#### 회의 제목

SRIB Weekly - RUL

#### 회의 일시

- 2025/08/28(목) 13:30 ~ 14:22 (Asia/Seoul GMT +09:00)

#### 참석자

<삼성전자>

- 선행Battery Lab.(MX) : 안성진 랩장/Safety Agent, 류성택
- Mobile Battery : Samarth Agarwal Head of Part, Herojit Sharma Laipubam, rahul.km@samsung.com, Subramanian Swernath Brahmadathan

#### 모델 성능 평가 및 데이터 분석

• Q7M 데이터셋과 A2 데이터셋 간 용량 감소 차이 분석

- Q7M 데이터셋에서 A2 대비 용량 감소가 다르게 나타남

- Q7M 데이터셋은 노이즈가 많음

• 훈련 데이터셋 변경에 따른 주요 결과

- A2에서 Q7M으로 훈련 데이터 변경 시 성능 변화 관찰

- 훈련 데이터 변경으로 인한 오류 발생 가능성

• 테스트 데이터셋 결과 분석

- 메인 및 서브 데이터셋에서 테스트 수행

- 일부 셀에서 높은 오류 발생 (아웃라이어 가능성)

• 새로운 기능 제안

- 저항 변화율(IRR drop)을 추가 기능으로 고려

- 저항 변화율이 용량 예측에 유용할 가능성

#### 전압 범위 조정 및 알고리즘 개선

• 전압 범위 조정 효과

- 3.2V ~ 4.0V 범위에서 용량 예측 정확도 향상

- 2.2V ~ 4.2V 범위 대비 1000 사이클 이후 예측 정확도 개선

• CC1 및 CC2 특성 분석

- CC1: 3.6V ~ 4.2V 범위 사용

- CC2: 낮은 SOC에서 용량 감소가 더 두드러짐

• 저항 변화율(IRR drop) 활용

- 저항 변화율이 용량 예측에 유용할 가능성

- 셀 간 저항 변동성 고려 필요

#### 데이터 품질 및 노이즈 제거

• 데이터 노이즈 문제

- Q7M 데이터셋에서 노이즈가 많음

- 노이즈 데이터 제거 필요성

• 셀 간 변동성 고려

- 셀 간 저항 및 용량 변동성 분석

- 저항 변화율(IRR drop) 사용 시 셀 간 변동성 고려 필요

#### 향후 작업 및 개선 방향

• 저항 변화율(IRR drop) 추가 기능 검토

- 모든 셀에 대해 저항 변화율 평가 후 추가 기능으로 고려

• 전압 범위 조정 및 알고리즘 개선

- 3.2V ~ 4.0V 범위 사용 시 예측 정확도 향상 가능성

- CC1 및 CC2 특성 분석 후 적절한 전압 범위 선택

• 데이터 품질 개선

- 노이즈 데이터 제거 및 셀 간 변동성 고려

- 저항 변화율(IRR drop) 활용 가능성 검토

## 관련 문서

- [[250821_SRIB_weekly_RUL]] (Meeting)
- [[250905_SRIB_weekly_RUL]] (Meeting)
- [[250912_SRIB_RUL_weekly]] (Meeting)
- [[250923_SRIB_Weekly_RUL]] (Meeting)
- [[250930_(W40) SRIB weekly RUL]] (Meeting)
- [[모델링 방향]] (Meeting)
