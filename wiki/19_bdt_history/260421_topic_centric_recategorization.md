---
title: "📝 Topic-centric 재카테고리화 (14 → 16 topic folders)"
date: 2026-04-21
tags: [changelog, meta, restructure, topic-centric]
type: changelog
status: completed
---

# 260421 — Topic-centric 재카테고리화

## 배경
이전 구조는 **이중 체계**였음:
- 시간순 누적 폴더: `changelog/ analysis/ learning/ tech-docs/` (코드 측)
- 도메인 카테고리 폴더: `01_Modeling_AI / 02_Experiments / 03_Battery_Knowledge / ...` (vault 계승)

같은 주제(예: cycle pipeline)가 4개 이상 폴더에 분산되어 탐색성이 낮았음.
주제 축 단일 체계로 재편.

## 핵심 내용

### 1. 폴더 재편 (14 → 16)
**삭제된 폴더**: `changelog/`, `analysis/`, `learning/`, `tech-docs/`, `03_Battery_Knowledge/`
**신설된 폴더**: `10_cycle_data/`, `11_profile_analysis/`, `12_dcir/`, `13_logical_cycle/`, `19_bdt_history/`, `20_materials/`, `21_electrochem/`
**rename된 폴더**:
- `01_Modeling_AI` → `30_modeling`
- `02_Experiments` → `22_experiments`
- `04_Development` → `31_software_dev`
- `05_Work_Log` → `40_work_log`
- `06_Inbox` → `50_inbox`
- `00_Index` → `_index`
- `_Templates` → `99_templates`
- `origin` → `90_origin`

### 2. 파일 이동 (총 149건)

| 주제 폴더 | 파일 수 | 주요 출처 |
|----------|---------|----------|
| 10_cycle_data | 31 | analysis/ + learning/ + changelog/ |
| 11_profile_analysis | 20 | changelog/ + analysis/ + learning/ |
| 12_dcir | 3 | changelog/ + analysis/ |
| 13_logical_cycle | 10 | changelog/ + analysis/ + learning/ |
| 19_bdt_history | 38 | 나머지 모든 code-knowledge + tech-docs |
| 20_materials | 24 | 03_Battery_Knowledge/ 소재 부분 |
| 21_electrochem | 22 | 03_Battery_Knowledge/ 이론·BMS 부분 |

### 3. Wikilink 일괄 갱신 (sed)
- `[[0X_FolderName/XXX]]` → `[[XXX]]` (파일명 기반으로 전환)
- `[[../changelog/XXX]]` → `[[XXX]]` (상대경로 제거)
- `[[../01_Modeling_AI/XXX]]` → `[[XXX]]` (상대경로 제거)
- `90_origin/` 제외. 원본 보존.

### 4. 문서 재작성
- `Wiki_Master_Index.md` — 주제 폴더 목록 + 볼륨 테이블 + 크로스 허브 재정렬
- `CLAUDE.md` — 스키마 섹션 전면 재작성 (Directory Rules, Ingest trigger 표, Query 분류, Maintenance 표)
- `10_cycle_data/_INDEX.md`, `11_profile_analysis/_INDEX.md`, `12_dcir/_INDEX.md`, `13_logical_cycle/_INDEX.md`, `19_bdt_history/_INDEX.md` — 5개 주제 MOC 신규 작성

## 변경 후 구조

```
wiki/
├── CLAUDE.md · Wiki_Master_Index.md · .obsidian/
│  ─── 💻 BDT 코드 주제 ───
├── 10_cycle_data/       11_profile_analysis/
├── 12_dcir/             13_logical_cycle/
├── 19_bdt_history/
│  ─── 🔬 배터리 도메인 ───
├── 20_materials/        21_electrochem/
├── 22_experiments/      30_modeling/
├── 31_software_dev/     40_work_log/
│  ─── 🌐 인프라 ───
├── _index/ _hubs/ 50_inbox/ 99_templates/ 90_origin/
```

## 영향 범위
- **탐색성**: 같은 주제 문서가 한 폴더에 모임. cycle pipeline 30+ 문서가 `10_cycle_data/` 하나에 응집.
- **Wikilink**: 파일명 기반이라 Obsidian은 대부분 자동 해결. 경로 포함 링크는 sed로 일괄 정리.
- **MOC**: 주제별 `_INDEX.md` 로 교체. 기존 4개 (changelog/analysis/learning/tech-docs `_INDEX.md`) 는 삭제.
- **기존 도메인 MOC**: `MOC_Modeling_AI`, `MOC_Experiments`, `MOC_Battery_Knowledge`, `MOC_Development`, `MOC_Work_Log` 는 파일명 그대로 각 새 폴더에 유지 (내부 링크는 파일명 기반이라 유효).

## 후속 작업 후보
- `20_materials`, `21_electrochem` 통합 MOC 필요 여부 검토 (기존 `MOC_Battery_Knowledge` 가 두 폴더에 걸친 상태).
- `_index/00_Home.md` 가 참조하는 사라진 경로 검증.
- `19_bdt_history` 가 비대 — 소재/전기화학/모델링 연관 문서는 해당 폴더로 추가 이관 가능.
