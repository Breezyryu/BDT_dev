---
title: "📂 볼트 구성 가이드"
aliases:
  - Vault Guide
  - 구성 가이드
tags:
  - Guide
  - Index
type: reference
status: active
updated: 2026-03-15
---

# 📂 볼트 구성 가이드

> [!info] 원본 보존 정책
> `origin/` 폴더의 파일은 **절대 수정하지 않습니다.**
> 모든 정리된 노트는 카테고리 폴더에 별도 저장됩니다.

---

## 1. 폴더 구조

```
wiki/                        ← Obsidian 볼트 루트 (2026-04-21 vault/→wiki/ 통합)
├── Wiki_Master_Index.md     ← 최상위 인덱스 (코드+도메인)
├── CLAUDE.md                ← 스키마 정의
│
│  ─── 🧠 Battery Domain ───
├── origin/                  ← 원본 보존 (수정 금지)
├── 00_Index/                ← 네비게이션 허브
│   ├── 00_Home.md
│   ├── 00_Dashboard.md
│   ├── All_Notes.base
│   ├── Battery_Knowledge_Base.base
│   ├── Modeling_AI_Base.base
│   └── Meeting_Tracker.base
├── 01_Modeling_AI/          ← PyBaMM, PINN, 경험적 모델, RUL
├── 02_Experiments/          ← SOP, 장비, 데이터 전처리
├── 03_Battery_Knowledge/    ← 소재, 전기화학, 물성
├── 04_Development/          ← Python, Julia, 환경 설정
├── 05_Work_Log/             ← 주간 보고, 업무 목표, 행정
├── 06_Inbox/                ← 미분류 (정리 후 이동)
├── _Templates/              ← 노트 템플릿 모음
│
│  ─── 💻 Code Knowledge ───
├── changelog/               ← 코드 변경 이력
├── analysis/                ← 코드 분석·비교
├── learning/                ← 코드 리뷰·학습
├── tech-docs/               ← SOP · 로드맵
└── _hubs/                   ← 크로스 도메인 허브 (logical_cycle, ...)
```

---

## 2. Frontmatter 표준

```yaml
---
title: "노트 제목"
aliases:
  - "별칭"
tags:
  - 카테고리태그      # Battery_Knowledge / Modeling_AI / Experiments / Development / Work_Log
  - 세부태그
type: knowledge | SOP | meeting | model | reference | experiment | development
status: active | draft | archived
related:
  - "[[연관노트]]"
created: YYYY-MM-DD
updated: YYYY-MM-DD
source: "origin/원본파일명.md"
---
```

---

## 3. 태그 체계

### 카테고리 (1depth)
- `Battery_Knowledge` — 배터리 도메인 지식
- `Modeling_AI` — 모델링 및 AI
- `Experiments` — 실험 및 분석
- `Development` — 개발 도구
- `Work_Log` — 업무 기록

### 세부 태그 (2depth 예시)
```
Battery_Knowledge: 양극, 음극, 전해액, 분리막, 전기화학, 소재, BMS
Modeling_AI: PINN, PyBaMM, 경험적모델, 딥러닝, RUL, SOH
Experiments: SOP, 분석장비, 데이터전처리
Development: Python, Julia, CUDA, 환경설정
Work_Log: SRIB, 주간보고, 업무목표, 행정
```

---

## 4. Obsidian 기능 활용

### Wikilinks
```markdown
[[노트명]]                    내부 링크
[[노트명|표시텍스트]]          커스텀 표시
[[폴더/노트명]]               폴더 명시
[[노트명#섹션]]               섹션 링크
```

### Callouts
```markdown
> [!abstract] 요약   — 노트 상단 요약
> [!tip]             — 핵심 포인트
> [!warning]         — 주의사항
> [!note]            — 보충 설명
> [!info]            — 기본 정보
> [!success]         — 결과/완료
> [!question]-       — 미해결 이슈 (접힘)
```

### Embeds
```markdown
![[노트명]]           노트 전체 임베드
![[노트명#섹션]]      섹션 임베드
![[파일.base]]        Base 뷰 임베드
```

### Bases (.base 파일)
동적 필터링 뷰. `00_Index/` 에 위치.
- `All_Notes.base` — 전체 노트
- `Battery_Knowledge_Base.base` — 배터리 지식
- `Modeling_AI_Base.base` — 모델링 AI
- `Meeting_Tracker.base` — 회의록 타임라인

---

## 5. 링크 전략

**Top-Down**: `00_Home` → `MOC` → 개별 노트

**Cross-Link 패턴**:
- 실험 데이터 → 모델 입력: `02_Experiments` ↔ `01_Modeling_AI`
- 소재 물성 → 열화 모델: `03_Battery_Knowledge` ↔ `01_Modeling_AI`
- 업무 목표 → 기술 노트: `05_Work_Log` → `01~04`

---

## 6. 노트 추가 워크플로우

1. `_Templates/` 에서 적절한 템플릿 선택
2. 해당 카테고리 폴더에 저장
3. Frontmatter의 `tags`, `type`, `related` 작성
4. 관련 MOC 파일에 링크 추가
5. `source`에 origin 원본 경로 기록
