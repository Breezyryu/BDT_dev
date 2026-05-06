# ADR-0006 — Reporting format: core + appendix, audience/cadence-tiered, AI/wiki/BDT = pptx components only

- Status: accepted
- Date: 2026-05-02
- Deciders: 본인 (선행배터리랩 「성능·수명 해석」 파트)
- Anchors: [[0001-lifetime-prediction-tool-split]], [[0005-bdt-dual-primary-user]]

## Context

새 plan 명시: "보고자료 (핵심만 간략하게, 자세한 내용은 **appendix로**)". 박사급 peer (CL3·CL4) + 그룹장 (상무) + 일반 동료 (80명) 다층 청중 + 3 cadence (그룹장 8주, 테크미팅 6개월, 주간그룹공유 3개월). 이전 grill ([memory feedback_substance_audience.md](C:/Users/Ryu/.claude/projects/c--Users-Ryu-battery-python-BDT-dev/memory/feedback_substance_audience.md)) 의 "**한 deck 으로 3계층 동시 만족 못함**" frame 의 직접 후속.

운영 제약 (사용자 명시):
- **pptx 자체는 본인 수동 조립** — AI / wiki / BDT 자동 출력 ❌
- AI / wiki / BDT 산출물 = pptx 의 **component** (이미지, 표, bullet 텍스트)
- **포맷 = .md 선호** (pptx 에 바로 붙여넣기 편한 형태)
- **Appendix 도 ppt 슬라이드로 구성** (별도 docx 아님)
- **pptx 는 bullet 스타일** (단락 X, bullet 단위)

이 제약이 [`wiki/CLAUDE.md`](../../CLAUDE.md) 의 docs/ 출력 의미를 바꿈 — `docs/*.pptx` 자동 출력은 의도 X. 대신 `docs/*.png` · `docs/*.xlsx` 와 `wiki/` 의 .md (bullet) 가 component source. pptx 조립은 본인 수작업.

## Decision

### 청중·cadence 차등 frame

| cadence | 핵심 슬라이드 | Appendix | 청중 |
|---------|------------|---------|------|
| **그룹장 보고 (8주)** | 3~5 (1: KPI·의사결정 / 2~5: detail) | minimal + appendix 추가 | 그룹장 (상무) |
| **테크미팅 (6개월)** | 3~5 (결과 + 핵심 그래프) | **풀 detail (박사급 standard)** | 박사급 peer + 일반 동료 |
| **주간그룹공유 (3개월)** | 3~5 highlight | minimal | 80 그룹원 + 랩장·그룹장 |

### 출력 형식

- **pptx 자체 = 본인 수동 조립**. AI / wiki / BDT 자동 .pptx 출력 금지.
- **AI / wiki / BDT 산출물 = pptx component**:
  - 이미지 → `docs/*.png`, `docs/*.svg`
  - 표 → `docs/*.xlsx` (또는 .md table)
  - **Bullet 텍스트 → `wiki/` 안 .md** (pptx 에 바로 붙여넣기 편한 형태)
- **Appendix = 같은 ppt 슬라이드** 형식 (별도 docx 아님)
- **pptx 는 bullet 스타일** — 한 슬라이드 ~3-7 bullets

### Bullet 텍스트 .md 작성 규칙

- **한 슬라이드 = 한 .md 섹션** (`## 슬라이드 제목`)
- **Bullet = `-` 또는 `*`** (depth 2 이내)
- **Bullet 당 한 줄** (~30~50자, 1초 가독성)
- **학계 reference / ADR cross-link = footnote 또는 별도 줄** (pptx footer 영역 매핑)
- **표** = 슬라이드 component 인 경우 별도 .xlsx 또는 .md table 로 (pptx 표 도구로 조립)
- **이미지** = `![alt](docs/path.png)` 형식 reference, 본문은 bullet 캡션만

### Source ↔ 출력 매핑

```
[wiki/CONTEXT.md, wiki/30_modeling, wiki/20_materials,
 ADR-0001~0005, wiki/19_bdt_history/, BDT 분석 결과 (PNG/XLSX)]
                ↓ source 합성
        ┌───────┴────────┐
        ↓                ↓
   [핵심 .md]       [Appendix .md]
   bullet 슬라이드  bullet 슬라이드
        ↓                ↓
   본인 수동 조립 → pptx (.pptx)
        ↓
   docs/*.pptx (조립 결과)
   docs/*.png, docs/*.xlsx (component, BDT/AI 자동 출력)
```

### 파일 위치 정합 (BDT 3-layer policy)

- Component 측:
  - **`wiki/`** — bullet 텍스트 .md (pptx component 측 source). cadence prefix 권장: `wiki/40_work_log/260513_W19_groupleader_core.md`
  - **`docs/`** — 이미지 (PNG/SVG), 표 (XLSX), 기타 바이너리. 본인이 pptx 조립 시 reference.
- 조립 결과:
  - **`docs/*.pptx`** — 본인 수동 조립 산출물

## Consequences

**Positive**:
- 청중·cadence 차등 frame = "한 deck 동시 만족 못함" 의 운영 specialization
- AI / wiki / BDT = component 측, 본인 수작업 = 조립 측 → 역할 분리 명료
- .md bullet 형식 = pptx 붙여넣기 편함 + wiki 보존성 ↑ + 다른 cadence 재사용 ↑
- ADR-0001~0005 의 frame 이 자연스럽게 appendix 슬라이드의 학계 reference / ADR cross-link source
- BDT 의 시각화 출력 (사이클 plot, Pareto front, envelope 시각화) 이 docs/*.png 의 자연 source

**Negative**:
- pptx 자동 출력 X — 본인 수동 조립 시간 부담
- .md bullet 형식 정합 작성 부담 (제목 / depth / bullet 길이 규칙)
- AI / wiki 가 pptx 의 어느 슬라이드용 component 인지 매핑 부담 — wiki 측 정리 필요
- BDT 측 시각화 출력의 docs/*.png 자동 저장 기능 추가 후보 (별도 작업)

**Neutral / follow-up**:
- **wiki/99_templates/ 에 핵심+appendix bullet .md 템플릿 신규** — pptx 슬라이드 단위 .md skeleton (cadence 별 3 템플릿: groupleader / techmeeting / weekly)
- **BDT 시각화 출력 → docs/*.png 자동 저장 기능** — 별도 작업 (사이클 / Pareto / envelope 시각화 등)
- ADR-0005 의 (5) 보고 source 항목 자연 후속 — 본인 보고 ↔ 그룹원 활용 측 같은 component 재사용
- 학계 reference 인용 형식 표준화 — appendix 슬라이드 footer 매핑 (별도 grill 후보)

## Alternatives considered

- **pptx 자동 출력 (AI / BDT 가 .pptx 직접 생성)** — 사용자 답 명시 "ppt는 직접 만듬". **Rejected**.
- **Appendix = docx** — 핵심 pptx + appendix docx. 사용자 답 "appendix도 ppt 슬라이드". **Rejected**.
- **단순 .md 텍스트 (bullet 형식 미지정)** — pptx 붙여넣기 시 정합 부족, cadence 재사용 ↓. **Rejected**.
- **그룹장 보고 = 1 슬라이드 압축** — 사용자 답 "3~5 슬라이드 (1: KPI / 2~5: detail)" 정정. **Rejected**.
- **CONTEXT.md entry 만 — ADR 미작성** — 형식 frame 의 hard-to-reverse + surprising + trade-off 충족 → ADR 가치 큼. **Rejected**.
