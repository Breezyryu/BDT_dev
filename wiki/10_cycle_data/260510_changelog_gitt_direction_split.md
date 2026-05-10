---
title: "[Changelog] GITT 방향 분기 — sequential 단방향 별도 카테고리"
date: 2026-05-10
tags: [changelog, classification, gitt, taxonomy, 사이클분류]
related:
  - "[[260411_analysis_cycle_concepts_unification]]"
  - "[[260419_사이클분류_Phase2_UI색상]]"
  - "[[260510_changelog_cycle_operation_reference_html]]"
status: applied
---

# GITT 방향 분기 — sequential 단방향 GITT 별도 카테고리

> 작업 요청자: 류성택 — 240821 GITT (충전 105cy + 방전 105cy sequential) 단일 `GITT(full)` 블록 식별

## TL;DR

- ✅ **GITT 방향 분기** — `GITT(charge)` / `GITT(discharge)` / `GITT(full)` 3분기
- ✅ **`_GITT_PAIR_THRESHOLD = 3`** — 단방향 그룹 ≥ 3 cycle 시 sequential, 미만 시 alternating
- ✅ **schedule 덮어쓰기 보존** — `_apply_sch_categories_to_classified`에 GITT 방향 가드
- ✅ **240821 GITT** 검증: 단일 블록 → 2분기 (충전 105cy + 방전 105cy)
- ✅ **exp_data 전수 영향**: charge 19 + discharge 15 + full 17 = 51 GITT entries (분기 안정)
- ✅ **회귀 0** — non-GITT dataset 동작 불변, classify regression 760 entries PASS

## 변경 요약

| 위치 | 변경 |
|---|---|
| `_merge_pulse_groups` (proto_:6732) | `_GITT_PAIR_THRESHOLD = 3` + direction-aware merge |
| `_apply_sch_categories_to_classified` (proto_:6604) | sch 덮어쓰기 시 GITT 방향 entry 보존 |
| `_CLASSIFIED_COLORS` (proto_:10778) | `GITT(charge)` / `GITT(discharge)` 추가 (idx=3 동일, desc 분기) |
| `CATEGORY_LABELS` (proto_:6440) | "GITT 충전방향 / 방전방향 (sequential)" 라벨 |
| `_HEURISTIC_CAT_NORMALIZE` (proto_:6525) | GITT 방향 passthrough (`fwd`) |
| `tools/export_all_cycle_timelines.py:_block_color` | 시각 색조 변형 (#F8B89D 밝은 살구 / #D67555 어두운 살구) |

## 분기 정책

### Sequential phase test (≥ 3 cycle 단방향 시퀀스)

```
105 CHG_ONLY pulse → 105 DCHG_ONLY pulse  
→ GITT(charge) [TC 5-109, 105cy]
→ GITT(discharge) [TC 110-214, 105cy]
```

### Alternating GITT (각 그룹 < 3 cycle, 충/방전 교차)

```
1 CHG + 1 DCHG + 1 CHG + 1 DCHG ...  
→ GITT(full) [모든 TC, alternating]
```

### threshold=3 의 근거

- alternating GITT는 보통 각 그룹 1 (페어드 alternating) 또는 짧음 (≤2)
- 3 이상 동일 방향 연속 = sequential phase test (charge GITT 측정 또는 discharge GITT 측정)

## 시각 표현

| 카테고리 | 색상 (export render) | 의미 |
|---|---|---|
| `GITT(charge)` | `#F8B89D` 밝은 살구 | 충전방향 GITT (sequential) |
| `GITT(discharge)` | `#D67555` 어두운 살구 | 방전방향 GITT (sequential) |
| `GITT(full)` | `#F39B7F` 표준 살구 (idx 3) | 충방전 alternating GITT |
| `GITT(simplified)` | `#F39B7F` (idx 3) | RSS 측정용 simplified |

proto_ 의 `_CLASSIFIED_COLORS` 는 모두 idx=3 동일 — 색상 변형은 export 렌더 단계에서만 적용.
사이클 탭 본 화면 (`CycleTimelineBar`) 영향 0. 추후 사용자 검토 후 필요 시 본 화면도 반영.

## 240821 검증

### Before
```
classified: 5 entries
[5] GITT(full) n_charge=105 n_discharge=105 raw_range=5-214 raw_cycles=210

blocks: 3
[1-1]   방전(초기)
[2-4]   사이클(FORMATION)
[5-214] GITT(full) ← 단일 블록 (210cy)
```

### After
```
classified: 6 entries
[5]   GITT(charge)    n_charge=105 n_discharge=0   raw_range=5-109   raw_cycles=105
[110] GITT(discharge) n_charge=0   n_discharge=105 raw_range=110-214 raw_cycles=105

blocks: 4
[1-1]     방전(초기)
[2-4]     사이클(FORMATION)
[5-109]   GITT(charge)    ← 105cy 분기 (밝은 살구)
[110-214] GITT(discharge) ← 105cy 분기 (어두운 살구)
```

## exp_data 전수 영향

| 카테고리 | 빈도 | 비고 |
|---|---|---|
| `GITT(charge)` | 19 | 신규 |
| `GITT(discharge)` | 15 | 신규 |
| `GITT(full)` | 17 | alternating GITT 유지 |
| `GITT(simplified)` | 0 | (현 fixture에서 미발견) |
| `GITT` (legacy alias) | 1 | 하위호환 |

170+ non-GITT dataset 분류 동일 — 본 변경 code path 미진입.

## 회귀

| 검증 | 결과 |
|---|---|
| `regression_classify_pne_cycles.py --verify` | `[PASS] 760 entries 완전 일치` |
| 240821 GITT 분기 | 2 블록 분기 ✓ |
| 240919 SOC별DCIR | 영향 없음 (GITT 미포함) |
| 260109 보관 4cy | 영향 없음 (GITT 미포함, 별건) |
| 전수 export | 204 dataset 26.7s (회귀 0) |

## 영향 범위

### 직접 영향
- 240821 GITT 같은 sequential phase GITT — 시각 분기 회복
- 타임라인 바 / pill / tooltip — 방향 정보 노출

### 간접 영향
- 추후 GITT 방향별 OCV / D_Li 측정 분리 분석 인프라 기반
- `meta.cycle_groups` 의 `LogicalCycleGroup.category` 확장 후보

### 무영향
- non-GITT dataset 분류 결과 불변
- 짧은 alternating GITT 시험 — `GITT(full)` 그대로 유지
- 사이클 탭 색상 (idx=3 단일 유지)

## Why

[[260510_changelog_cycle_operation_reference_html#case-f]] 의 사용자 보고 4건 중 첫 번째 — GITT 방향 정보 노출이 phase test 성격 시각화에 핵심.

분류 단순화 v2 (10 카테고리 통합) 가 검토 중인 상황에서, **방향 분기는 분류 정밀도 ↑ 방향**으로 단순화 v2와 다른 축. v2 머지 시 `GITT(charge)/(discharge)`을 어떻게 표현할지 (single GITT 카테고리 + direction sub-tag? 별도 카테고리?) 추가 결정 필요.

## Related

- `docs/code/01_변경로그/260510_gitt_direction_split.md` — 코드 상세 변경
- `docs/code/02_레퍼런스/260510_exp_data_cycle_timelines_v3.html` — v3 결과 (방향 분기 + C-rate)
- `tools/debug_classification.py` — 240821 / 240919 / 260109 진단 출력
- `tools/export_all_cycle_timelines.py` — exp_data 전수 export 도구

## 후속 작업 후보

1. **Case ② 240919 SOC별 사이클 sub-tag** — (전)/(후) 또는 가속수명 idx 위치 기반 자동 라벨링
2. **Case ③ 260109 보관 → HYSTERESIS_CHG 오분류** — schedule rule 5 가드 보강 (페어 / N≥2 / 후속 long-rest 부재 검증)
3. **C-rate 기반 가속수명 vs RPT 자동 disambiguation** — 분류기 자체에서 임계 적용
4. **`gitt_direction` 필드 `meta.cycle_groups` 까지 전파** — LogicalCycleGroup 통합
