---
title: "260507 그룹 공유 §1 — 현황 탭 필터링 상세"
tags: [presentation, group_share, BDT, status_filter, classifier_v3, storage_cycle]
date: 2026-05-07
parent: "[[260507_BDT_update_groupshare]]"
status: draft
---

# §1. 현황 탭 — 필터링 상세

발표 본문 §1 보충 자료. 발표에서 1~2줄로 정리한 항목을 commit·동기·구현 흐름 단위로 풀어둔다.

## 배경

- 260409 시점 — 채널 리스트 sub-tab 안에 `btn_filter`가 함께 있었다
- 사용자 동선 — 필터를 켠 채로 채널을 바꾸면 채널이 줄어든 이유를 추적하기 어렵다
- 분류 측면 — 보관(Storage) 사이클이 일반 cycling과 같은 카테고리에 묶여 dQ/dV 형상이 겹친다

## 변경 내역

| Commit | 날짜 | 요지 |
|---|---|---|
| `2b11b3d` | 4/29 | 현황/필터링 탭 분리 + 충방전기명 검색 |
| `72ef2bc` | 4/29 | 필터링 탭을 현황 탭 내부 sub-tab으로 이동 |
| `3d4ba2b` | 4/29 | 채널 리스트 sub-tab 의 `btn_filter` 제거 |
| `f91ab31` | 5/2 | Phase 0-5 분류기 v3 + STORAGE_CYCLE 신규 카테고리 |
| `bece8ee` | 5/2 | 분류기 .sch Phase 0 audit 5단계 종합 |
| `c88e2cb` | 5/5 | 빈 필터 진단 + scope 미스매치 폴백 |

## 구현 흐름

### 1. 탭 분리

- 현황 탭 = `채널 리스트` + `필터링` 두 sub-tab
- `btn_filter`는 필터링 sub-tab 전용. 채널 리스트 쪽 호출 경로는 없다
- 충방전기명 검색은 필터링 sub-tab 안 검색창 1줄

### 2. 분류기 v3

- Phase 0 — `.sch` 우선 파싱 (정확도 우선)
- Phase 1~4 — JSON-first 분류 + CSV cross-check (보강)
- Phase 5 — 휴리스틱 fallback (분류 실패 시)
- 카테고리 — 기존 카테고리에 **STORAGE_CYCLE** 추가
  - 보관·사이클 혼합 시험을 별도로 분류
  - 일반 cycling fade fit 흐름과 분리

### 3. 진단 메시지

- 빈 필터 — "X 카테고리 0건 / Y scope 0건 / Z 검색어 0건" 형식으로 어디서 비었는지 표시
- scope 미스매치 폴백 — 사용자가 잡은 범위에 데이터가 없으면 인접 범위로 자동 전환하고 알림을 띄운다

## 사용자 체감

- 채널을 바꿨는데 표시가 줄면 — 필터가 아니라 채널 리스트 sub-tab을 먼저 확인하면 된다
- STORAGE_CYCLE 카테고리 — 보관 평가만 따로 보고 싶을 때 한 번에 골라낸다
- 빈 필터 — "분류명을 잘못 골랐다" / "검색어가 너무 좁다" 가 한 줄로 식별된다

## 검증

- 회귀 검증기 (BDT 4-케이스 표준) 격자 통과
- Phase 0 audit (`bece8ee`) — `.sch` 187 항목 cross-check, 분류 정확도 baseline 갱신

## Q&A 보강

- "분류기 v3 의 v2 대비 변화는?"
  → JSON-first + CSV cross-check + Phase 5 휴리스틱 fallback. 정확도 baseline 비교는 회귀 검증기 노트 참조 (`reference_cycle_regression_validator`)
- "STORAGE_CYCLE 분리 기준은 무엇인가?"
  → `.sch` 패턴 + condition col[2] cross-check. 기준은 Phase 0-5 audit 노트 (`260504_audit_phase0_5_classifier_input_spec`)
- "필터를 적용한 상태에서 export 결과는 무엇이 빠지는가?"
  → 필터에 잡힌 채널만 결과 시트에 들어간다. scope·카테고리·검색어 3축 모두 적용

## 관련 자료

- `wiki/10_cycle_data/260427_split_filter_into_separate_tab.md`
- `wiki/10_cycle_data/260427_filter_subtab_inside_status.md`
- `wiki/10_cycle_data/260505_phase0_5_v3_implementation.md`
- `wiki/10_cycle_data/260504_audit_phase0_5_classifier_input_spec.md`
- `wiki/10_cycle_data/260504_audit_phase0_csv_sch_step_alignment.md`
