---
title: "📝 docs ↔ wiki 역할 분리 + docs 통폐합"
date: 2026-04-22
tags: [changelog, meta, architecture, consolidation]
type: changelog
status: completed
---

# 260422 — docs ↔ wiki 역할 분리 + 통폐합

## 배경
`docs/code/`, `docs/vault/` 에 wiki 와 중복된 .md 문서가 다량 존재. 사용자가 명확한 역할 분리 규칙 제정:
- **`wiki/`** = Obsidian 볼트. **`.md` 전용**.
- **`docs/`** = 출력 문서. 바이너리·렌더 (`.docx`, `.pptx`, `.xlsx`, `.pdf`, `.png`, `.html` 등).

## 핵심 내용

### 1. CLAUDE.md 스키마 재작성
- 3-layer 다이어그램 갱신: `raw/` → `wiki/` (Obsidian vault) → `docs/` (binary output)
- Layer Rules 표에 **허용 확장자 컬럼** 추가
- 금지사항: `.md` 를 `docs/` 에 두지 않는다, `docs/` 는 바이너리·렌더 전용
- Directory Rules의 `outputs/` 섹션을 `docs/` 로 교체
- Query Workflow: 산출물 저장 경로 명시 (`docs/*.pptx`, `docs/*.docx`, `docs/_viz_output/`)

### 2. docs/vault 통폐합 (에이전트 A)
총 **300 파일 삭제**, 9 파일 wiki 이동:
- 119 파일 — 파일명이 wiki 에 이미 존재 (중복)
- 12 파일 — 2026-04-21 병합으로 wiki primary에 흡수된 파일들
- 4 추가 — PyBaMM / SiC / 전처리 병합 흡수 검출
- `docs/vault/origin/` 전체 — wiki/90_origin과 1:1 동일
- 4 `.base` 파일 — wiki/_index/와 동일

**wiki 이동 (9)**:
| Original | → | Destination |
|---|---|---|
| `Comparative_Electrochemical_OSS_Analysis.md` | → | `30_modeling/` |
| `phygnn_NREL.md` | → | `30_modeling/` |
| `PINNSTRIPES_NREL.md` | → | `30_modeling/` |
| `NREL_SSC_수명모델_참고.md` | → | `30_modeling/` |
| `PyBaMM_Variables_PPT.md` | → | `30_modeling/` |
| `ACIR_DCIR_RSS.md` | → | `12_dcir/` |
| `260419_GITT_확산계수_추출.md` | → | `22_experiments/` |
| `260419_BDT_Parsing_Pipeline.md` | → | `10_cycle_data/` |
| `SOP_개발환경_세팅.md` | → | `31_software_dev/` |

`docs/vault/` 폴더 완전 제거.

### 3. docs/code 통폐합 (에이전트 B)
총 **100 파일 삭제**, 70 파일 wiki 이동 (이후 13 파일은 비-md라 docs/ 로 되돌림 — 아래 4단계):
- 75 파일 — 파일명 중복
- 24 파일 — 병합 흡수
- 1 txt — cyc validation report

**wiki 이동 (md 59)**:
- `10_cycle_data/`: 34 (filter/status/tc/sch/classification/cycle_path)
- `11_profile_analysis/`: 12 (profile/hysteresis/cv/dod/crate)
- `13_logical_cycle/`: 6 (ECT path)
- `19_bdt_history/`: 7 (OSS/ampworks/drm 분석)

`docs/code/` 폴더 완전 제거.

### 4. wiki 내부 비-md 파일 → docs/ 로 재분류 (13 파일)
새 규칙 (wiki = .md only) 엄격 적용을 위해 에이전트가 이동한 비-md 파일을 다시 docs/ 로:
- **`docs/mockups/`** (신규) ← HTML/Python UI 목업 8개 (`260412_*_mockup.html`, `.py`)
- **`docs/reports/`** (신규) ← TXT 리포트 5개 (`260327_cyc_validation`, `260414_BDT_업데이트_이력`, `260419_sch_전수분류`, `신분류기_Phase0_결과` ×2)

### 5. docs/ 정리
- `docs/260319_DataTool_UI_Improvement.md` → `wiki/19_bdt_history/` 이동
- `docs/.obsidian/` 삭제 (wiki/.obsidian 이 유일한 볼트 설정)

## 최종 상태

### wiki/ (440 md)
```
wiki/
├── CLAUDE.md · Wiki_Master_Index.md · .obsidian/
├── 10_cycle_data/ (61)  11_profile_analysis/ (29)
├── 12_dcir/ (3)         13_logical_cycle/ (14)
├── 19_bdt_history/ (40) 20_materials/ (18)
├── 21_electrochem/ (22) 22_experiments/ (18)
├── 30_modeling/ (24)    31_software_dev/ (12)
├── 40_work_log/ (25)    50_inbox/ (1)
├── 90_origin/ (159)     99_templates/ (5)
└── _hubs/ (4)           _index/ (3)
```

### docs/ (바이너리·렌더 전용)
```
docs/
├── BDT_사용SOP_v1.0.docx · v2.0.docx
├── BDT_전기화학시뮬레이션_발표자료.pptx
├── battery_tool_update.pptx
├── _viz_output/           (HTML 시각화)
├── mockups/               (UI 목업 HTML/Python, 2026-04-22 신규)
├── reports/               (TXT 리포트, 2026-04-22 신규)
├── licenses/
└── testing/
```

## 영향 범위
- **지식 통합**: 462 docs 파일 중 400+ 삭제 (중복), 79 wiki 이동. docs/ 가 순수 출력물 폴더로 축소.
- **역할 명확화**: wiki 는 Obsidian 볼트 (모든 `.md`), docs 는 렌더 결과. 혼동 없음.
- **.md 위치 단일화**: 이제 wiki/ 내부가 `.md` 의 유일한 source of truth.

## 새 규칙 요약 (CLAUDE.md 반영)

```
wiki/   → Obsidian vault, .md only
docs/   → binary/rendered, no .md
raw/    → immutable source
```

1. `.md` 파일은 반드시 `wiki/` 안에만
2. `docs/` 는 `.docx / .pptx / .xlsx / .pdf / .png / .svg / .html` 등 렌더 결과만
3. `wiki/` → 렌더 파이프라인 → `docs/` 플로우 (export only)

## 후속 작업 후보
- wiki 주제 폴더 _INDEX.md 들의 신규 이동 파일 반영 (특히 10, 11, 12, 13, 19, 30, 31)
- Wiki_Master_Index 볼륨 테이블 갱신 (다음 세션)
- docs/mockups, docs/reports 의 파일들은 wiki의 어떤 .md 에서 참조되는지 연결 필요 (현재 링크 없음)
