---
title: "260422_W17_biweekly_exec_report"
tags: [Work_Log, 상무보고, 격주보고, 선행Lab, 성능수명, dVdQ, POR, Q8]
type: report_draft
status: draft
related:
  - "[[260422_9w_exec_report]]"
  - "[[MOC_Work_Log]]"
created: 2026-04-22
updated: 2026-04-22
---

# 17주차 상무 보고 — 슬라이드별 Bullet (초안)

> **보고 대상**: 배터리그룹 상무님
> **주기**: 격주 (9주차 → 17주차)
> **소속**: 선행Lab. 성능/수명 파트
> **작성일**: 2026-04-22

---

## Lab 주간 보고 ↔ 상무 보고 테마 매핑

| Lab 목표 (4대 툴) | 9주차 상무 테마 | 금주 업무 상태 |
|---|---|---|
| 전기화학 성능 예측툴 | 3. 성능 시뮬 (전기화학) | Q8 모델링 진행 |
| 수명 예측 툴 (승인/실사용) | 4. 수명 예측 (Empirical) | Empirical 검토 |
| 열화 분석툴 (dVdQ) | 2. dV/dQ 양음극 분리 | POR 셀 열화 해석 |
| 코인/삼전극 제작 process | 1. 소재 전기화학 물성 DB화 | Q8 코인셀 평가 |
| — (인프라) | 전 테마 기반 tool 연동 | BDT ECT Output 개선 |

**결론**: 17주차 상무 보고도 9주차와 동일한 4테마 구조 유지하여 일관성 확보. 프레임은 그대로, 내용만 업데이트.

---

## [P1] 요약

- 지난 2개월 핵심 4건
	- **dV/dQ 스무딩 3중 파이프라인 완성** → Peak 자동 산출
	- **POR (급방전 이슈) 셀 실사례 해석 착수** — 현장 이슈 대응
	- Q8 업체(ATL / SDI / COSMX) 평가 Item 정리
	- BDT ECT 데이터 저장·처리 기능 개선
- Empirical fade 모델 Q8 적용 검토 개시

## [P2] 로드맵 현황

- 9주차 Q1~Q4 표 재사용, 상태 마커만 업데이트
- Q1 ✓ 완료 / Q2 ▶ 진행 중 / Q3 일부 사전 착수

## [P3] 소재 물성 DB화

- Q8 코인셀 평가 Item 정리 중 — ATL · SDI · COSMX
- 자체 측정 선행, 결여 항목만 업체에 요청
- 반전극(삼전극) 데이터 — 개발팀 차기 과제에 별도 요청
- 코인/삼전극 SOP 기반 측정 파이프라인 가동

## [P4] 열화 모드 분리 (dV/dQ) — **핵심**

- dV/dQ 스무딩 파이프라인 완성 (3중)
	- ① 시간대별 중앙값 — 데이터 밀림 해소
	- ② Wavelet Denoising — 고주파 노이즈 제거
	- ③ Savitzky-Golay — Peak 형상 보존
- Peak point 자동 산출 기능 구현
- **적용 사례 — POR (급방전 이슈) 셀**
	- 0.2C 방전 프로파일 dV/dQ peak 추출
	- 프레쉬셀 반전극(양극·음극 OCP) 기반 dV/dQ 와 비교
	- Peak shift / shrink 패턴 → LLI · LAM 기여도 해석 검토 중

**첨부 그림**
- 그림 ① `docs/presentations/260422_17w/fig1_dvdq_smoothing_pipeline.svg` — 스무딩 3중 파이프라인
- 그림 ② `docs/presentations/260422_17w/fig2_por_dvdq_concept.svg` — POR vs Fresh dV/dQ Peak 비교

## [P5] 성능 시뮬레이션 (전기화학)

- Q8 코인셀 측정 데이터 기반 모델 캘리브레이션 개시
- BDT 시뮬 탭 (P2D · SPM · SPMe) 기존 인프라 연속 활용
- 9주차 그림 재사용 가능

## [P6] 수명 예측 (Empirical)

- 기존 fade 모델 → Q8 세트 (PF · SDI · ATL · COSMX) 적용 검토
- 업체별 온도 fade 파라미터 도출 → 승인/실사용 EOL 산출
- Si 하한 계수 반영은 후속 과제로 유지
- 9주차 그래프 재사용 가능

## [P7] BDT 인프라 개선

- ECT 데이터 저장·처리 로직 개선 (기존 기능 보완)
- 4개 테마 공통 데이터 허브로 운용

## [P8] 이슈 & 다음 단계

- POR 셀 해석 결과 → 개발팀 피드백 루프
- Q8 업체 회신 타이밍 = Q3 진척 선행 조건
- Q3 킥오프 예정: Tool 내부 dV/dQ 탭 통합 · 급속충전 risk SW

---

## 9주차 대비 "변화 포인트" (신규 반영 사항)

1. **POR 셀 열화 해석** (NEW) — 9주차엔 없던 실사례 기반 분석. "툴이 실제 이슈에 쓰였다"는 메시지 전달. 열화 모드 슬라이드 내 서브섹션으로 추가.
2. **업체 협업 구체화** — "업체 데이터 수급" 우선순위를 **"ATL/SDI/COSMX Item 요청 리스트 확정·송부"** 진척으로 업데이트.
3. **BDT ECT Output** — "BDT 버전업 연계"의 구체화. 4테마 관통 인프라 레이어로 별도 슬라이드 할애.

---

## 답변받은 금주 업무 상세

1. **POR 셀** = 급방전 이슈 셀. 0.2C 방전 프로파일 dVdQ peak 과 프레쉬셀 반전극(양음극) profile dVdQ peak 분석 검토 중.
	- dVdQ 스무딩 파이프라인 완료: 각 시간대별 중앙값 선택(데이터 밀림 해소) → Wavelet Denoising → Savitzky-Golay Filter 3중 적용
	- Peak point 산출
2. **BDT ECT Output** = 기존 ECT 데이터 저장·처리 개선 (② 옵션).
3. **Q8 반전극 데이터** = 앞으로 진행할 개발팀 과제에서 별도 요청.
4. **Empirical 수명** = 기존 fade 모델로 Q8 등 모델에 적용.
