---
title: "260507 그룹 공유 §4 — 프로파일 분석 개편"
tags: [presentation, group_share, BDT, profile, hysteresis, layer_a, dod_axis]
date: 2026-05-07
parent: "[[260507_BDT_update_groupshare]]"
status: draft
---

# §4. 프로파일 데이터 분석 — 개편

발표 본문 §4 보충 자료. 4월 28일 ~ 5월 5일 사이 30+ commit. 네 갈래로 정리.

## 갈래 요약

| 갈래 | 핵심 commit | 한 줄 |
|---|---|---|
| 4.1 사이클 바 (경로 테이블) | `cb6c4a9` 외 | 7→6열 + Excel 드래그 + Ctrl+C/V + stale TC 갱신 |
| 4.2 데이터 범위 분류 (Layer A) | `5d72c53` | `_unified_pne_load_raw` 의 `data_scope` 분기 제거 |
| 4.3 히스테리시스 6건 통합 | `600f2cf` | 페어링·anchor·scaling·CV·분류·axis_mode 한 묶음 |
| 4.4 옵션 체계 정리 | `8ec54e8` 외 | continuity+loop → overlap, 무의미 조합 비활성화 |

---

## 4.1 사이클 바 (경로 테이블) 개편

### 변경 내역

| Commit | 요지 |
|---|---|
| `cb6c4a9` | 경로 테이블 — TC 항상 편집 가능 + Excel-style 드래그 채우기 |
| `0d86593` | 다중 셀 선택·복사 — ExtendedSelection + Ctrl+C |
| `c88e2cb` | 경로 교체 시 stale TC 자동 갱신 |
| 다단계 step1~6 | path table 캐시 / light meta / trigger split / progress / consistency / paste header (260426 changelog 참고) |

### 핵심

- TC 컬럼 — 토글 없이 늘 편집 가능. 키 입력 줄어듦
- 7열 → 6열 — 사용 빈도 낮은 컬럼 1개 뺌
- Excel 드래그 — 한 셀 입력하고 우하단을 끌면 아래로 채워짐
- Ctrl+C / Ctrl+V — 다중 셀에서도 동작
- 경로 교체 시 — 이전 경로 TC 메타가 캐시에 남던 버그 해결 (`c88e2cb`)
- Autofill 버튼 (`0426_fix_autofill_button_link_mode`) — Link mode 호환

### 사용자 체감

- 셀 30개를 드래그 한 번에 채움
- 경로 바꿨을 때 옛 TC 정보가 안 남아 혼동 없음

---

## 4.2 데이터 범위 분류 — Layer A 단일화 (PR-1)

### 배경

- 기존 — `unified_profile_core` 파이프라인의 첫 stage `_unified_pne_load_raw` 안에 `data_scope` 분기가 있었음
- 부작용 — 같은 raw 데이터를 scope 별로 다시 읽음. CV / 충전 / 방전 각각 한 번씩 로딩
- 추가로 — Layer A 안에 view 레벨 분기 로직이 누수

### 변경 (`5d72c53`)

- Layer A — **단일 raw 로딩만** 담당
- scope 분기 — view 단계로 옮김
- 같은 시험을 여러 scope로 봐도 raw 로딩은 1회

### overlap 옵션 통일

- `cfa5259` — 충전/방전 데이터 범위에서 '이어서' overlap 옵션 제거
- `4535564` — 프로파일 옵션 체계 통일 — continuity + loop → overlap

### 사용자 체감

- 같은 시험 scope 전환 — 로딩 대기 사라짐
- '이어서' overlap 옵션이 한 곳에 — 사용자가 어느 옵션을 켰는지 추적 쉬움

### 검증

- 회귀 검증기 (BDT 4-케이스) — Layer A 단일화 뒤 baseline 동일 (PR-1 노트)
- 후속 PR-2 ~ PR-N — `data_scope` 의존하는 다른 stage 식별·정비 (`260504_daily_worklog` 참고)

---

## 4.3 히스테리시스 6건 통합 수정

### 통합 commit (`600f2cf`)

| # | 항목 | 무엇을 고쳤나 | 선행 commit |
|---|---|---|---|
| 1 | 페어링 | TC N + TC N+1 보완 phase 결합 (체크박스 + 진단 로그) | `a55e16e`, `9364904` |
| 2 | anchor | SOC 오프셋 anchor shift 보정 — 기준점 어긋남 | `29d77a6` |
| 3 | scaling | y축 스케일 일관화 — major / minor 그룹별 dim (Option B) | `0bba268` |
| 4 | CV | CV 영역 필터링 robustness — saveok ON일 때만 long-format 빌드 | `cd4ac67` |
| 5 | 분류 | RSS 측정 사이클이 HYSTERESIS 로 오분류 | `316fa22` |
| 6 | axis_mode | DOD 축 좌표 — 사이클+분리/연결 물리 좌표계 회복 | `a4517ba` |

### 부수 변경

- `923ab5b` — 히스테리시스 사이클 라벨/색상 깊이 기반 (Dchg/Chg X%) — major/minor 시각 구분
- `3656b17` — 히스테리시스 프리셋 — 단일 flow + Origin 호환 dQdV 시트 + Hysteresis_Analysis long-format 시트
- `c88e2cb` — 부분 TC 선택 지원 (sweep PULSE_DCIR)
- `f17fd18` — 라벨 off-by-one — classified 기반 hysteresis TC 필터링
- `399ac53` — 후처리 색상 detection 이 페어링 모드 segment 순서를 cycle 경계로 오인하던 문제

### 핵심 흐름

- 페어링 — TC N (충전) + TC N+1 (방전) 보완 phase 를 하나의 hysteresis pair로 묶음. 체크박스로 on/off
- anchor — SOC 0 기준점이 시험별로 다른 케이스를 자동 보정
- scaling — major (full DOD) 와 minor (부분 DOD) 사이클을 같이 plot할 때 minor만 dim
- CV — 충전 종지 CV 영역의 robustness 필터. saveok 비활성 시 long-format 빌드 skip (성능)
- 분류 — RSS 측정 사이클의 hysteresis 오분류 — schedule cross-check로 정정
- axis_mode — DOD 축 좌표가 사이클+분리·사이클+연결 옵션에서 깨지던 문제. 물리 좌표계로 복원

### 사용자 체감

- 페어링 결과가 시험 간에 일관됨
- DOD 축에서 Charge/Discharge 양쪽 phase가 정확한 좌표
- Origin 호환 dQdV 시트 — 외부 분석 그대로 사용

### 검증

- 회귀 검증기 (BDT 4-케이스) — hysteresis 4 케이스 baseline 동일
- 6건이 한 commit으로 묶여 회귀 risk 집중 → 검증기 1회로 동시 검증

---

## 4.4 프로파일 옵션 체계 정리

### 변경 내역

| Commit | 요지 |
|---|---|
| `4535564` | continuity + loop → **overlap 단일 옵션** 통합 |
| `8ec54e8` | 사이클+분리+시간 조합 비활성화 (결과값이 물리적으로 의미 없음) |
| `e30900c` | 옵션 4종 모델 spec 명시 + 다중경로 색상 G6 통일 |
| `6373f94` | 모든 옵션의 plot 색상 로직 통합 — `_cycle_id_tag` 단일화 |
| `e30900c` | 4종 모델 spec — 사이클·분리·시간·CV 조합 정합성 |

### 핵심

- 옵션 단순화 — 사용자가 켜는 토글 수 줄어듦
- 무의미 조합 차단 — 사용자가 잘못 조합해 결과 해석 오류 막음
- 색상 — 다중 경로·사이클 적은 케이스에서 group 대신 distinct 색상 (`182d6c9`)

---

## Q&A 보강

- "히스테리시스 6건 통합은 BDT 4-케이스 표준 회귀 검증으로 검증되었나?"
  → 검증 완료. baseline 동일. 회귀 검증기는 별도 wiki 노트 (`reference_cycle_regression_validator`)
- "Layer A 단일화로 깨지는 기능은 없나?"
  → PR-1 범위는 raw 로딩 stage만. view 단계 분기 로직은 그대로. 4-케이스 회귀에서 변동 없음
- "프로파일 옵션 4종이 정확히 무엇인가?"
  → 사이클·분리·시간·CV 조합 4종. spec은 `260428_profile_4modes_spec` 노트
- "axis_mode = DOD 가 깨졌던 케이스를 다시 보고 싶다"
  → `260505_dod_axis_logic_fix.md` + commit `a4517ba` 비교 화면

## 관련 자료

- `wiki/11_profile_analysis/260428_profile_4modes_spec.md`
- `wiki/11_profile_analysis/260503_anchor_layer_separation.md`
- `wiki/11_profile_analysis/260505_dod_axis_logic_fix.md`
- `wiki/11_profile_analysis/260420_hysteresis_major_threshold.md`
- `wiki/40_work_log/260429_hysteresis_unified_flow.md`
- `wiki/40_work_log/260430_fix_hysteresis_soc_offset_clip_relax.md`
- `wiki/10_cycle_data/260426_changelog_path_table_step1_cache_patch.md` ~ `step6_paste_header_link_hint.md`
