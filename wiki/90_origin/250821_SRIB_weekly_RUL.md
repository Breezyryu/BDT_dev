---
title: 250821_SRIB_weekly_RUL
category: Meeting
date: 2025-08-21
created: 2025-12-15
tags:
  - meeting
participants: []
---

#### 회의 일시

- 2025/08/21(목) 16:00 ~ 17:18 (Asia/Seoul GMT +09:00)

#### 참석자

<삼성전자>

- 선행Battery Lab.(MX) : 안성진 랩장/Safety Agent, 류성택
- Mobile Battery : Samarth Agarwal Head of Part, Herojit Sharma Laipubam, rahul.km@samsung.com, Subramanian Swernath Brahmadathan

#### CC1 기능 성능 분석

• CC1 기능의 한계
- Q7M 배터리에서 내부 서브 및 메인 배터리의 성능이 낮음
- SEM 기능 사용 시 0.2C 예측에서 모든 셀 타입(내부, 서브, 메인)에서 우수한 성능 보임
• 향후 개선 필요
- CC1 기능의 성능 향상을 위한 추가 작업 필요

#### 새로운 피처 도입
• IOD 드롭 피처 제안
- BSOH 분석에서도 논의된 IOD 드롭을 새로운 피처로 사용 가능성
- 저항 변화를 활용한 피처로, 사이클별 용량 변화와 상관관계 분석 예정
• 적용 계획
- 기존 피처와 함께 추가하여 알고리즘에 적용 검토

#### 전압 범위 조정 및 데이터 분석
• 전압 범위 조정 필요성
- 현재 전압 범위 설정으로 인한 성능 저하 가능성
- 4.2V에서 3.2V로 전압 범위 조정 후 성능 재평가 예정

• 데이터 재분석
- 다른 셀에서도 동일한 문제 발생 여부 확인
- 전압 범위 조정 후 DQDV 피처의 상관관계 재분석

#### SRIB 알고리즘 구조 및 성능

• SRIB 모델 구조
- FC6 레이어까지 사용하여 용량 감소 트렌드 학습
- 더 많은 레이어 추가 시 노이즈 학습 가능성

• 성능 비교
- SRIB 모델이 더 작은 데이터셋에 적합하도록 설계
- 향후 성능 저하시 레이어 추가 검토

#### 테스트 및 검증 결과

• A2 데이터셋 테스트
- Full 피처와 CC1 피처 모두에서 우수한 성능 보임
- Q7M 배터리에서 내부 및 메인 배터리 성능 저하 발생

• 향후 작업

- 전압 범위 조정 후 테스트 재수행
- 새로운 피처 도입 및 알고리즘 최적화

#### 액션 아이템

• 전압 범위 조정 및 데이터 재분석
- 4.2V에서 3.2V로 전압 범위 조정 후 성능 재평가
• 새로운 피처 도입 및 분석
- IOD 드롭 피처와 DQDV 피처의 상관관계 분석
• SRIB 알고리즘 최적화
- 레이어 구조 검토 및 성능 모니터링
• 테스트 및 검증
- 다른 셀 데이터셋에서 성능 재검증
- 전압 범위 조정 후 테스트 결과 비교

## 관련 문서

- [[250905_SRIB_weekly_RUL]] (Meeting)
- [[250912_SRIB_RUL_weekly]] (Meeting)
- [[250923_SRIB_Weekly_RUL]] (Meeting)
- [[250930_(W40) SRIB weekly RUL]] (Meeting)
- [[250829_SRIB_RUL]] (Meeting)
- [[모델링 방향]] (Meeting)
