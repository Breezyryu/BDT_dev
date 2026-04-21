---
title: "📝 전체 문서 중복 통폐합"
date: 2026-04-21
tags: [changelog, meta, dedup, consolidation]
type: changelog
status: completed
---

# 260421 — 전체 문서 중복 통폐합

## 배경
Topic-centric 재카테고리화 완료 후 각 주제 폴더 내부에 남은 중복·중첩 문서를 병렬 에이전트 스캔으로 식별·병합.
도메인 폴더도 수정·삭제 허용 규칙 변경 (2026-04-21 같은 날).

## 결과 요약

| 영역 | 감소 | 주요 병합 |
|------|-----|----------|
| 10_cycle_data | 32 → 26 | 260318 시리즈 3→1, review 4→1, 260327→260405 |
| 11_profile_analysis | 21 → 17 | core/render/batch/validation 각 2→1 (4 쌍) |
| 12_dcir | 4 → 2 | SOC70+Condition9 → 260620 primary |
| 13_logical_cycle | 11 → 8 | phase_a+a2, design+review, redef+in_cycle_data |
| 19_bdt_history | 38 → 31 | 초기 changelog 4→1, merge 로직 2→1 (new `merge_pipeline_explanation`), 개선안 2→1, origin-diff 2→1 |
| 20_materials | 24 → 18 | 전해액 2→1, SiC→Silicon, DLC_detail→분리막_기능층, SiC_Graphite→Silicon, Battery_Science_MOC→MOC_Battery_Knowledge (+2 relocate out) |
| 21_electrochem | 22 → 22 | Battery_Electrochemical_properties→Electrochemical_parameter 병합 + SDI_코팅·업체별_분리막 relocate in |
| 22_experiments | 21 → 17 | 데이터 전처리 4→1 (new `데이터_전처리_통합`), 글로브박스 2→1 |
| 30_modeling | 22 → 19 | PyBaMM ExpressionTree+Phase1 → PyBaMM_정리, 모델링_방향→수명_해석_방향 (+1 relocate in) |
| 31_software_dev | 11 → 11 | IT투자 2→1, pyqt6 relocate in |
| 40_work_log | 26 → 25 | 2026_로드맵→업무목표 |

**총합**: 245 → 209 (**−36 파일**, −15%)

## 작업 내역

### Priority 1 — 즉시 실행 (8건)
- `전해액.md` ← `전해액_분석_및_조성.md` 병합
- `Electrochemical_parameter.md` ← `Battery_Electrochemical_properties.md` (빈 파일 삭제)
- `MOC_Battery_Knowledge.md` ← `Battery_Science_MOC.md`
- `Silicon.md` ← `SiC.md` (빈 파일 병합)
- `IT투자_SW.md` ← `SW_투자검토.md` (빈 템플릿 2개 → 1)
- `업무목표.md` ← `2026_로드맵.md`
- 재배치 3건: `pybamm_output_variables` → 30_modeling, `SDI_코팅_음극_접착력` + `업체별_분리막_설계` → 21_electrochem
- 명확한 중복 3건: `vectorized_merge copy`, `260320_r_` (빈 파일), `pyqt6` → 31

### Priority 2 — 병렬 에이전트 6개
각 에이전트에 특정 폴더/그룹의 병합을 위임:
- **10_cycle_data** 에이전트 — 260318 시리즈 3→1, review 4→1, 260327→260405 (삭제 6)
- **11_profile_analysis** 에이전트 — 4 쌍 각 2→1 (삭제 4)
- **12_dcir + 13_logical_cycle** 에이전트 — 2+3 병합 (삭제 5)
- **19_bdt_history** 에이전트 — 4 그룹 병합, 1 신규 문서 생성 (삭제 7, 신규 1)
- **20_materials + 22_experiments** 에이전트 — DLC_detail, SiC_Graphite, 전처리 4→1, 글로브박스 2→1 (삭제 6, 신규 1)
- **30_modeling** 에이전트 — PyBaMM 4→2, PINN 링크 정돈, 수명·열화 5→3 (삭제 3)

## 병합 원칙
1. **정보 손실 없음** — absorb 파일의 고유 콘텐츠를 primary에 섹션으로 편입
2. **Primary 우선** — 최신/완전성 높은 문서를 primary로 선정
3. **섹션 설계** — 단순 append 아닌, primary 구조 재고려
4. **주석 표기** — 각 primary 상단에 `> 📎 2026-04-21: {absorb} 병합 ({섹션명})` 주석
5. **Wikilink sed 치환** — 삭제된 파일명 참조를 primary로 일괄 전환 (90_origin 제외)
6. **90_origin 보호** — 원본 보존, 수정 금지 유지

## 신규 생성 문서 (2개)
- `22_experiments/데이터_전처리_통합.md` — 4 원본 파일의 계층 통합
- `19_bdt_history/merge_pipeline_explanation.md` — cumsum 그룹핑 + groupby().apply() 집계 2단계 통합

## 규칙 변경 (CLAUDE.md 반영)
- **이전**: 도메인 카테고리 기존 노트 내용 삭제 금지 (보완만 허용)
- **변경**: `90_origin/` 외 모든 폴더 수정·삭제·통폐합 자유

## 영향 범위
- **탐색성 향상** — 중복 문서 병합으로 동일 정보 한 곳에서 파악 가능
- **wikilink 자동 재연결** — sed 일괄 치환으로 36 개 삭제 파일 참조가 primary로 리다이렉트
- **Obsidian 링크 그래프** — 크기 감소 + 밀도 증가 (허브 주변 응집)

## 후속 작업 후보
- `_hubs/*.md` 의 section-anchor 링크 (`[[file#header]]`) 검증 — Obsidian 에서 실제 점프 확인 필요
- SRIB Weekly RUL 시리즈 (40_work_log 6 파일) — 주간별 공통 헤더 추출 여지
- PINN 4 파일의 교차 링크 정돈 후 유지 중 — 필요시 추가 병합 재검토
