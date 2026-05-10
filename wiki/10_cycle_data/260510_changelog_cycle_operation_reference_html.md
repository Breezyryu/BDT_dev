---
title: "[Changelog] 사이클 타임라인 바 + 경로 테이블 운영 체계 HTML 레퍼런스"
date: 2026-05-10
tags: [changelog, reference, cycle-data, html, path-table, timeline-bar, link-mode]
related:
  - "[[260411_analysis_cycle_concepts_unification]]"
  - "[[260412_cycle_pipeline_refactor]]"
  - "[[260426_changelog_path_table_step1_cache_patch]]"
  - "[[260426_changelog_path_table_step6_paste_header_link_hint]]"
  - "[[260509_changelog_baseline_path_modes]]"
status: applied
---

# 사이클 타임라인 바 + 경로 테이블 운영 체계 — HTML 레퍼런스 신설

> 작업 요청자: 류성택 — `사이클 타임라인 바와 - 경로테이블 사이클 운영 체계 기준을 html로 정리해. 연결처리, 다중그룹 등 모든 케이스에 대해서 포함시켜`

## TL;DR

- ✅ **HTML 단일 레퍼런스** 신설 — `docs/code/02_레퍼런스/260510_사이클_타임라인바_경로테이블_운영체계.html`
- ✅ **운영 케이스 6종** 명시 — 단일 / 다중 / 연결단일그룹 / 연결다중그룹 / ECT / **첫 분석 가드(F)**
- ✅ **PNE/Toyo TC 단위 분기** 정합 (260509 90e1bba 반영)
- ✅ **사이클 바 ↔ col4 동기화 모델** 도식
- ✅ **Case F 신규** (260510 류성택 보고) — v2 guard col4 user input 유실 vector 진단 + fix 권고
- ✅ **Follow-up 행 비채움 정책** 명시 (260510 류성택) — col 2/3 그룹 내 일치 시 공란, 채널 매칭 / 용량 불일치 시에만 텍스트 노출
- ✅ **wiki SSOT 보존** — 본 changelog만 wiki, 본문은 docs 렌더 자산 (3-layer 정책)

## 위치

- 본문: `docs/code/02_레퍼런스/260510_사이클_타임라인바_경로테이블_운영체계.html`
- 신설 디렉토리: `docs/code/02_레퍼런스/` — 향후 렌더 자산 (HTML 등) 전용
- 본 changelog: `wiki/10_cycle_data/260510_changelog_cycle_operation_reference_html.md`

## 포함 범위 — 9개 섹션

| § | 제목 | 핵심 |
|---|---|---|
| 1 | 개요 — 두 위젯의 역할과 단위 일원화 | TC = single source, col4 = CycleNo |
| 2 | 사이클러별 TC/논리사이클 의미 | PNE: TotlCycle = TC; Toyo: 충방전 그룹핑 = TC |
| 3 | 사이클 타임라인 바 위젯 구조 | `CycleTimelineBar` (L11026), 행 모델, 블록 빌드 파이프라인, 마우스 매트릭스 |
| 4 | 경로 테이블 7컬럼 + 자동 채우기 | light/full 분리, 트리거 매트릭스, 캐시 일관성 (Step 5), paste 헤더 (Step 6) |
| 5 | 운영 케이스 5종 | A/B/C/D/E ASCII 다이어그램 + 표 |
| 6 | 연결처리 동작 | 토글 시그널, 누적 hint, offset 라우팅, continue/overlay 모드, sub_label 매칭 |
| 7 | 타임라인 바 ↔ col4 동기화 | `_timeline_syncing` 가드, 폰트/색상 규칙, 행→바 매핑 |
| 8 | 패턴 색상 팔레트 | `_PATTERN_CATEGORIES` (8종) + `_CLASSIFIED_COLORS` (10 idx, Phase 2) |
| 9 | 알려진 버그 / 회귀 가드 | 회귀 인프라 (test_path_modes 30 tests), 미수정 Bug 1·2, Perf 1·2, 최근 fix 이력 |

## 운영 케이스 매트릭스

| 케이스 | 행 수 | 빈 행 | link 토글 | 사이클바 | col4 placeholder | 그룹 번호 |
|---|---|---|---|---|---|---|
| A 단일 | 1 | 0 | 무관 | 1행 | "1-{max_tc}" | 표시 안 함 |
| B 다중(연결OFF) | ≥2 | 0 | OFF | N행 | 각 행 개별 | 표시 안 함 |
| C 연결+단일그룹 | ≥2 | 0 | ON | 1행 (offset 합산) | 첫 행만 "1-{cumul_tc}" | "1" |
| D 연결+다중그룹 | ≥2 | ≥1 | ON | M행 (그룹 수) | 그룹 첫 행만 누적 | "1","2","..." |
| E ECT 모드 | ≥1 | 무관 | 강제 OFF | (ECT 별도) | 항상 편집 가능 | — |
| **F 첫 분석 가드** | 무관 | 무관 | 무관 | 무관 | **v2 guard 자동 덮어쓰기 (검정)** | — |

## Case F 추가 (260510)

### 사용자 보고
> "프로파일 분석 시, 해당 경로의 사이클 동작을 확인했고 또 다시 입력 후 사이클 분석하여 입력 사이클이 사라지는 케이스" — 류성택 260510

### 진단 결과 (코드 추적)

`unified_profile_confirm_button` (proto_:29012) v2 guard가 새 경로 진입 시 col4 user input(검정)을 무차별 덮어쓰는 vector 확인:

| Step | 위치 | 동작 | 부수효과 |
|---|---|---|---|
| 1 | L29060-29068 | 현재 경로 vs `_rows_last_analyzed_path` 비교 | path 다르면 guard 진입 |
| 2 | L29071 | 매핑 즉시 커밋 | 다음 클릭부터 guard skip |
| 3 | **L29094** | **`item4.setText(f"1-{_max}")`** | **⚠ user input 덮어쓰기** |
| 4 | **L29095** | **`setForeground(검정)`** | **⚠ user input 취급** |
| 5 | L29104-29106 | `setEnabled(True)` + return | 분석 skip — 메시지 의도 |

### 권고 fix (HTML F-5 참조)

```python
# L29089 부근에 user input 보존 분기 추가
_existing = item4.text() if item4 else ''
_is_user_input = (item4 and
                  item4.foreground().color() == QtGui.QColor(0, 0, 0))
if _is_user_input and _existing.strip():
    item4.setToolTip(f"입력: {_existing}  (새 경로 max TC: {_max})")
    continue   # 덮어쓰지 않음
# 기존 로직: 회색 placeholder만 갱신 (검정 → 회색)
item4.setForeground(QtGui.QColor(160, 160, 160))   # ← 회색
```

`L29141-29150`의 "TC 범위 초과" 검증 로직이 user input 보존하더라도 다음 클릭에서 max TC 초과를 차단하므로 안전.

### 잔여 가능성 (재현 시 추가 추적 필요)
- `_remove_duplicates_across_rows` (L20297) — 다중 행 col4 중복 제거 시 user input도 빈 문자열로 덮음 가능
- link mode follow-up 행 — `_autofill_row` L26033 `item4.setText('')` 강제 클리어
- 탭 reset 핸들러 후 다음 분석에서 guard 재진입

## Follow-up 행 비채움 정책 (Section 6.5 신규, 260510)

### 사용자 정책 명시
> "용량, 채널에서 빈칸이 아닌 경우는 채널 매칭 정보 입력, 용량이 다른 경우 입력 시에만 텍스트 노출하도록 변경하자" — 류성택 260510

### 컬럼별 채움 규칙

| 컬럼 | 비채움 (기본) | 채움 (예외) |
|---|---|---|
| col 0 시험명 | 항상 공란 (그룹 첫 행만 표시) | 없음 |
| col 2 채널 | 그룹 내 채널 set 일치 시 공란 | **채널 매칭 정보 입력 시** (예 `032,-,-` 위치 기반 또는 경로 간 채널 다름) |
| col 3 용량 | 그룹 내 용량 동일 시 공란 | **용량이 다를 때만** (mismatch 행만 표기) |
| col 4 TC | follow-up 항상 공란 | 없음 (그룹 첫 행 누적 전용) |

### 현재 구현 정합성
- `_autofill_row` (L25990-26028) `skip_dup` 분기는 이미 `auto_val.strip() == first_val.strip()` 시 비채움 → 정책 일치 ✓
- `_highlight_channel_mismatch` (L26817) — 위치 수 부족/누락 채널 빨간 폰트
- `_highlight_capacity_mismatch` (L26918) — 다수결 + Phase 2 실측 교차검증 후 소수파 빨간색

### 의미 — 사용자 멘탈 모델
- 공란 = "그룹 첫 행과 동일" (불필요한 정보 제거, 가독성 ↑)
- 텍스트 = "특별한 매칭 입력 또는 mismatch" (사용자 주의 필요 신호)
- 빨간 폰트 = "validation 후 mismatch 후보 강조"

## 의도

- **단일 진실원천 (SSOT)** — 사이클 운영 체계의 케이스 분기·단위·동기화 모델을 한 문서로 묶어 실무 트러블슈팅에 즉시 참조 가능
- **Markmap 호환 hierarchy** — H1/H2/H3 정렬 + 짧은 노드 + 표/불릿 우선 (사용자 cadence 정합)
- **사외 협업 가능** — 네트워크 의존 없이 단일 HTML, 외부 서비스 업로드 0 (로컬 OSS only feedback 정합)

## 영향 범위

### 직접 영향
- BDT 사용자가 사이클 탭 사용 중 case 구분이 헷갈릴 때 단일 레퍼런스로 즉시 해결
- 연결처리 Toyo 정합(260509) 결과를 영구 박제 — 추후 회귀 발생 시 SSOT 비교 기준
- 신규 인계자(BDT 후속 담당)가 케이스 5종 + 5컬럼 + 동기화 가드를 1회 학습으로 흡수

### 간접 영향
- `references/` 외부 학술 문서와 별도 — BDT 본진 운영 체계 문서로 분류
- ADR 0001~0003(profile 3-layer) 와 동일 docs 트리 — code 운영 체계는 02_레퍼런스, 결정은 adr/

### 무영향
- 본 changelog 외 wiki 본문 변경 0 — 기존 wiki 분석/계획 문서 보존
- BDT proto 코드 변경 0 — 본 PR 은 docs/wiki 추가만

## 검증

- [x] HTML 단일 파일 (외부 의존 0, 임베디드 CSS/구조)
- [x] 9개 섹션 + TOC + 케이스 5종 ASCII + 표 + 색상 팔레트 swatch
- [x] 코드 라인 인용 (L11026 CycleTimelineBar, L25638 _has_table_data, L25645 _get_table_row_groups, L28562 _update_cycle_timeline 등)
- [x] PNE/Toyo TC 단위 분기 4 위치 명시 (classify_paths_summary, _resolve_path_meta, _get_row_max_cycle_info, _update_cycle_hints_for_link)
- [x] 미리보기 panel 표시 확인
- [ ] 사용자 검토 후 추가 케이스/섹션 보강

## Why

[[260509_changelog_baseline_path_modes]] 가 **회귀 인프라**를 갖췄다면, 본 문서는 **운영 멘탈 모델**을 박제. 두 산출물의 결합으로:
1. **운영 체계** = HTML 레퍼런스 (단일 진실원천)
2. **회귀 검증** = `pytest tests/regression/test_path_modes.py` (30 tests)
3. **변경 이력** = `wiki/10_cycle_data/260426_changelog_path_table_step{1..6}_*.md` + `260509_*` + `260510_*`

세 자산이 함께 움직이며 사이클 탭 운영 체계를 정합 상태로 유지.

## Related

- [[260411_analysis_cycle_concepts_unification]] — 사이클 개념 통일 (사용자 레이어 = 논리사이클)
- [[260412_cycle_pipeline_refactor]] — 7개 정비 + 사이클 바 UX 전면 개선
- [[260415_tc_info_and_cycle_groups]] — TcInfo / LogicalCycleGroup 표준화
- [[260426_changelog_path_table_step1_cache_patch]] ~ [[260426_changelog_path_table_step6_paste_header_link_hint]] — 6 PR 시리즈
- [[260509_changelog_baseline_path_modes]] — 경로 모드 3종 회귀 baseline (PR #12)
- `docs/code/01_변경로그/260509_link_toyo_tc_fallback.md` — 연결처리 Toyo TC 정정 (commit 90e1bba)
