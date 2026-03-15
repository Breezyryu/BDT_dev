---
title: "250912_SRIB_RUL_weekly"
tags: [Work_Log, SRIB, RUL, 주간보고]
type: meeting
status: active
related:
  - "[[250905_SRIB_weekly_RUL]]"
  - "[[250923_SRIB_Weekly_RUL]]"
created: 2025-09-12
updated: 2026-03-15
source: "origin/250912_SRIB_RUL_weekly.md"
---

# Action/Item
1. **Implementation of new workflow and performance validation**
	- Comparison of Chained Regression vs. Stacked Regression
2. **Utilization of resistance information**
	- Validation between training and testing for A2 to Q7M

---
#### 회의 제목

SRIB Weekly - RUL

#### 회의 일시

- 2025/09/12(금) 11:28 ~ 12:24 (Asia/Seoul GMT +09:00)

#### 참석자

<삼성전자>

- 선행Battery Lab.(MX) : 안성진 랩장/Safety Agent, 류성택
- Mobile Battery : Samarth Agarwal Head of Part, Herojit Sharma Laipubam, Rahul Kumar, Subramanian Swernath Brahmadathan

#### 새로운 Workflow 및 모델 수정 방안 논의

• 기존 모델 수정 요청 및 새로운 Workflow 제안

- 기존 모델의 문제점 및 개선 방향 논의

- 새로운 Workflow: Chained Regression vs. Stacked Regression 비교

• Chained Regression

- 장점: Running Capacity와 Probe Capacity 간 상관관계 보장

- 단점: 오류 누적 가능성

• Stacked Regression

- 장점: 오류 누적 없음, 동시 예측 가능

- 단점: Running Capacity와 Probe Capacity 간 상관관계 보장 어려움

• 저항 정보 활용 방안

- 저항 정보를 활용한 모델 성능 개선 가능성 논의

- 저항 정보의 입력 단계(1단계 vs. 2단계) 검토 필요

#### DQDV 결과 및 개선 사항

• DQDV 결과 개선

- Subcell의 DQDV 결과 개선 방안 논의

- 전압 위치 조정(3.75V) 후 상관관계 개선

• 저항 정보 활용

- 저항 정보를 활용한 모델 성능 비교

- A2와 Q7M 간 저항 정보 차이 검토 필요

#### Kubernetes 및 데이터 처리 방안

• Kubernetes 관련 논의

- Subcell 및 Main Cell 간 데이터 처리 방안

- 저항 정보 활용을 통한 정확도 개선 가능성

• 데이터 노이즈 처리

- 온도 변화로 인한 데이터 노이즈 제거 방안 논의

- 시스템 오류 vs. 일반적인 노이즈 구분 필요

#### 새로운 Queue 및 R&D 통합 방안

• R&D ML Pipeline 통합

- R&D Queue와 기존 Queue 통합 결과 검토

- 저항 정보 활용을 통한 모델 성능 비교

• Stack Regression vs. Chained Regression 비교

- 두 방법 간 성능 비교 및 선택 방안 논의

- 저항 정보 활용을 통한 성능 개선 가능성

#### 향후 액션 아이템

• Stack Regression 구현 및 성능 검증

- 저항 정보 활용 방안 검토

- A2와 Q7M 간 데이터 비교 및 성능 검증

• 데이터 노이즈 처리 방안 검토

- 온도 변화로 인한 데이터 노이즈 제거 방안

• 저항 정보 활용을 통한 모델 성능 개선

- 저항 정보의 입력 단계 및 활용 방안 검토

• 새로운 Workflow 구현 및 성능 검증

- Chained Regression vs. Stacked Regression 비교 및 선택

• 보고서 작성 및 결과 공유

- 다음 주까지 결과 정리 및 공유 예정

## 관련 문서

- [[250821_SRIB_weekly_RUL]] (Meeting)
- [[250905_SRIB_weekly_RUL]] (Meeting)
- [[250923_SRIB_Weekly_RUL]] (Meeting)
- [[250930_(W40) SRIB weekly RUL]] (Meeting)
- [[250829_SRIB_RUL]] (Meeting)
- [[모델링 방향]] (Meeting)
