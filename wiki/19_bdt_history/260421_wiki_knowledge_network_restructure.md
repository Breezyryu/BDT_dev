---
title: "📝 wiki 지식 네트워크 재구성"
date: 2026-04-21
tags: [changelog, meta, moc, knowledge-graph]
type: changelog
status: completed
---

# 260421 — wiki 지식 네트워크 재구성

## 배경
`wiki/` 하위 4개 시간순 누적 폴더(changelog 28 / analysis 31 / learning 30 / tech-docs 3)에 MOC가 없어 Karpathy-style "LLM이 소유·유지하는 지식 베이스" 원칙에 비해 탐색성이 떨어졌음. vault는 MOC가 있었지만 orphan 노트 9건 존재. 상위 네비게이션(Master Index)도 부재.

## 핵심 내용

### 신규 파일 (10개)
- **Wiki_Master_Index.md** — wiki 루트 최상위 인덱스
- **changelog/_INDEX.md** — 9 클러스터 (Unified Profile / Logical Cycle / Cycle Pipeline / Testing / UI / Bug / Docs / Device / Refactor History)
- **analysis/_INDEX.md** — 12 클러스터, 5 big branches
- **learning/_INDEX.md** — 8 클러스터 + 3개 학습 경로 (초심자 / 리팩토링 / 최적화)
- **tech-docs/_INDEX.md** — 3 문서 + 차기 후보 3건
- **_hubs/hub_logical_cycle.md** — TC ↔ 논리사이클 매핑 집결지
- **_hubs/hub_unified_profile.md** — `unified_profile_core` 6-stage 파이프라인 허브
- **_hubs/hub_cycle_pipeline.md** — 경로→그래프 전체 흐름 허브
- **_hubs/hub_dcir.md** — 3 모드 DCIR 통합 분류 허브

### 수정 파일 (4개)
- **vault/00_Index/00_Home.md** — "Code Knowledge" + "Cross-Domain Hubs" 섹션 신설
- **vault/01_Modeling_AI/MOC_Modeling_AI.md** — 📦 참조·인프라 섹션 + BDT 코드 연계
- **vault/02_Experiments/MOC_Experiments.md** — 🗒️ 최근 업무 노트 섹션 + BDT 코드 연계
- **vault/03_Battery_Knowledge/MOC_Battery_Knowledge.md** — DLC_detail / SiC_Graphite 연결 + BDT 코드 연계

## 영향 범위
- wiki 전체 문서 수: ~120 → ~134 (14 신규/수정)
- vault orphan: 9 → 1 (중복 가능성 1건 보류)
- 모든 폴더에 MOC 존재 (`06_Inbox` / `00_Index` 제외 — 설계상 정상)
- 크로스 도메인 주제 허브 4개로 코드 ↔ 배터리 도메인 교차 참조 가능

## 재구성 원칙
1. **시간순 → 주제별** — 파일명 날짜는 유지하되 MOC에서 주제 클러스터로 재조직
2. **깊이 없는 링크** — 각 MOC는 수평 링크만, 계층은 `Wiki_Master_Index` 하나만
3. **Hub = 허브** — 여러 폴더에 걸친 큰 주제는 `_hubs/` 에 집결
4. **BDT 코드 ↔ 도메인 지식** — 양방향 교차 참조 섹션을 각 MOC 말미에 표준화

## 후속 작업 후보
- `changelog/_INDEX` 자동 갱신 스크립트 (신규 파일 감지 → 클러스터 제안)
- `wiki health check` — orphan/stale/dead-link 주기 감사
- 크로스 도메인 허브 확장: `hub_lifetime_prediction`, `hub_reliability_pipeline`
