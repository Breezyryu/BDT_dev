---
title: "260507 그룹 공유 §3 — 사이클·프로파일 결과 데이터 서브탭"
tags: [presentation, group_share, BDT, data_subtab, qtableview, performance]
date: 2026-05-07
parent: "[[260507_BDT_update_groupshare]]"
status: draft
---

# §3. 사이클·프로파일 결과 — 데이터 서브탭 신설

발표 본문 §3 보충 자료.

## 배경

- 그래프만으로는 "사이클 12 방전 용량"의 정확한 값을 읽기 어려움
- 기존 워크플로우 — 결과 export → 엑셀 열기 → 셀 찾기. 한 사이클당 30초 이상 소요
- 그룹 사용 패턴 — 회의 중 즉석에서 숫자를 뽑아 공유하는 빈도가 높음

## 변경 내역

| Commit | 날짜 | 요지 |
|---|---|---|
| `b5d12fc` | 5/3 | 사이클 분석 결과 '데이터' 서브탭 — 엑셀 시트 형태 view |
| `bcee163` | 5/3 | 프로파일 분석 결과 '데이터' 서브탭 — (채널×사이클) DataFrame view |
| `babb5d6` | 5/4 | 프로파일 데이터 서브탭 QTableWidget → QTableView (40s → 20ms) |
| `0d86593` | 5/3 | 데이터 탭 다중 셀 선택·복사 — ExtendedSelection + Ctrl+C |
| `5a39af9` | 5/3 | 데이터 서브탭 'Cycle' 컬럼 중복 + offset 진단 로그 |

## 구현 흐름

### 1. 사이클 결과 데이터 서브탭

- 기존 사이클 분석 결과 = 그래프 only
- 서브탭 추가 — 채널 × 사이클 매트릭스
- 컬럼 — 채널 ID / Cycle / Dchg / Chg / Eng / fade ratio 등
- 행 — 사이클 1 ~ N

### 2. 프로파일 결과 데이터 서브탭

- 프로파일 분석 결과의 (채널 × 사이클) DataFrame 을 그대로 view
- 컬럼 — 채널 / Cycle / Step / Time / V / I / Q / E / SOC / phase
- 대용량 시험 — 채널 수 × 사이클 수 × 데이터 포인트 수

### 3. 성능 — QTableWidget → QTableView

- 기존 — QTableWidget. 셀마다 widget 객체 생성. 채널 32 × 사이클 200 × 컬럼 12 ≈ 76,800 셀에서 약 40초 로딩
- 변경 — QTableView + Model/View 패턴. lazy rendering
- 결과 — 동일 데이터 약 20 ms (≈ 2,000배)
- 대용량 시험에서도 즉시 로딩, 스크롤 frame drop 없음

### 4. 다중 선택·복사

- SelectionMode = ExtendedSelection — Shift·Ctrl 다중 선택 정상화
- Ctrl+C 단축키 → 탭 구분 텍스트로 클립보드 복사
- 엑셀에 그대로 Ctrl+V 시 같은 표 형태로 붙여넣기

### 5. Cycle 컬럼 중복 + offset 진단

- 기존 — 데이터 서브탭 'Cycle' 컬럼이 두 번 나타나는 케이스 (sub-cycle offset 처리 잘못)
- 변경 — 단일 컬럼으로 통일 + offset 계산 로그 추가 (디버깅 용이)

## 사용자 체감

- 그래프 → 데이터 서브탭 클릭 → 셀 다중 선택 → Ctrl+C → 엑셀 Ctrl+V
- 4 단계, 수 초 안에 끝
- 회의 중 화면 공유에서 즉석 숫자 응답 가능

## 검증

- QTableView 전환 후 — 채널 32 × 사이클 200 케이스 로딩 시간 측정 (40s → 20ms)
- Ctrl+C 복사 → 엑셀 붙여넣기 round-trip 검증

## Q&A 보강

- "QTableView 전환 외에 다른 성능 개선은?"
  → Layer A 단일화 (§4.2) — raw 로딩 중복 제거. 같은 시험을 여러 scope 으로 봐도 한 번만 로딩
- "데이터 서브탭에서 직접 편집은 가능한가?"
  → 읽기 전용. 분석 결과 무결성을 지키려고 편집은 차단
- "큰 시험(채널 64 × 사이클 1000+) 에서도 즉시 로딩되나?"
  → QTableView lazy rendering 이라 rendering 자체는 OK. raw 로딩은 Layer A 단일화로 1회만 발생
- "엑셀 export 기능은 그대로인가?"
  → 별도 export 버튼은 그대로 유지. 데이터 서브탭은 즉석 확인용

## 관련 자료

- `wiki/10_cycle_data/260427_changelog_data_subtab.md`
- `wiki/10_cycle_data/260428_changelog_profile_data_subtab.md`
- `wiki/40_work_log/260426_perf_responsiveness.md`
