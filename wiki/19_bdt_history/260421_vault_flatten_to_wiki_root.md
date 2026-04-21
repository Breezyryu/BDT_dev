---
title: "📝 vault/ 를 wiki/ 로 flatten"
date: 2026-04-21
tags: [changelog, meta, restructure, obsidian]
type: changelog
status: completed
---

# 260421 — vault/ → wiki/ flatten

## 배경
`wiki/vault/` 는 `.gitignore` 대상이라 tracked되지 않았고, 상위 `wiki/` 와 구조가 이중화되어 있었음. Obsidian 볼트 루트도 `wiki/vault/` 였음. Karpathy-style "LLM이 소유·유지하는 wiki" 철학을 단일 루트에서 일관되게 적용하기 위해 vault 하위를 wiki/ 로 flatten.

## 핵심 내용

### 1. 폴더 이동 (9개)
- `wiki/vault/00_Index/` → `wiki/00_Index/`
- `wiki/vault/01_Modeling_AI/` → `wiki/01_Modeling_AI/`
- `wiki/vault/02_Experiments/` → `wiki/02_Experiments/`
- `wiki/vault/03_Battery_Knowledge/` → `wiki/03_Battery_Knowledge/`
- `wiki/vault/04_Development/` → `wiki/04_Development/`
- `wiki/vault/05_Work_Log/` → `wiki/05_Work_Log/`
- `wiki/vault/06_Inbox/` → `wiki/06_Inbox/`
- `wiki/vault/_Templates/` → `wiki/_Templates/`
- `wiki/vault/origin/` → `wiki/origin/`
- `wiki/vault/.obsidian/` → `wiki/.obsidian/` (볼트 루트 이동)
- `wiki/vault/` 제거

### 2. `.gitignore` 수정
- `vault/` 라인 제거 (wiki/ 통합 후 tracked로 전환). 주석으로 이력 남김.

### 3. 경로 참조 갱신
- `[[../vault/XX]]` → `[[../XX]]` (hubs, analysis/_INDEX, tech-docs/_INDEX)
- `[[vault/XX]]` → `[[XX]]` (Wiki_Master_Index)
- `[[../../Wiki_Master_Index]]` → `[[../Wiki_Master_Index]]` (00_Home)
- `[[...]]` → `[[...]]` (3 MOC 파일의 BDT 코드 연계 섹션)
- `wiki/vault/` 단어 언급 → `wiki/` (CLAUDE.md, Wiki_Master_Index 구조 도식)

### 4. 구조 문서 갱신
- `wiki/CLAUDE.md` — 디렉토리 도식 재작성, "Code Knowledge" / "Battery Domain" / "Cross-Domain & Origin" 3 섹션 구분
- `wiki/Wiki_Master_Index.md` — 같은 3 섹션 구조, 볼륨 테이블 경로 수정
- `wiki/00_Index/!Guide_Vault_Organization.md` — 폴더 구조 블록 재작성

## 변경 후 wiki/ 루트

```
wiki/
├── CLAUDE.md               스키마
├── Wiki_Master_Index.md    최상위 인덱스
├── .obsidian/              Obsidian 설정 (볼트 루트)
│  ─── 💻 Code Knowledge
├── changelog/ analysis/ learning/ tech-docs/
│  ─── 🧠 Battery Domain
├── 00_Index/ 01_Modeling_AI/ 02_Experiments/
├── 03_Battery_Knowledge/ 04_Development/ 05_Work_Log/ 06_Inbox/
├── _Templates/
│  ─── 🌐 Cross-Domain & Origin
├── _hubs/
└── origin/                 원본 보존 (수정 금지)
```

## 영향 범위
- **Obsidian 볼트 루트 변경**: `wiki/vault/` → `wiki/`. 사용자는 Obsidian 재오픈 시 볼트 경로 재지정 필요.
- **git tracked 파일 증가**: 기존 ignored였던 120+ md 노트 + .obsidian 설정이 tracked 후보가 됨. 다음 커밋 시 일괄 추가됨.
- **[[wikilink]] 해석**: Obsidian이 `wiki/` 루트 기준으로 재해석. 파일명 기반 wikilink는 모두 유효.

## 후속 작업
- `origin/` 폴더는 CLAUDE.md 규칙상 "수정 금지". git add는 하되 edit은 하지 않음.
- `.obsidian/workspace.json` 등 사용자별 UI 상태는 `.gitignore` 추가 검토 (선택).
- 커밋 시 바이너리/대용량 파일 확인 권장.
