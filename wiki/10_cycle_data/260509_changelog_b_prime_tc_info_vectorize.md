---
title: "Changelog: B′ 구현 — _extract_tc_info_toyo 벡터화 (류성택 요청)"
date: 2026-05-09
tags: [changelog, code, toyo, performance, b-prime, vectorize, phase0]
related:
  - "[[260509_review_b_step_feasibility_roi]]"
  - "[[260509_proposal_toyo_speedup_to_pne_parity]]"
status: applied
---

# Changelog: B′ 구현 — `_extract_tc_info_toyo` 벡터화

> 작업 요청자: 류성택 (사용자) — `B′ _extract_tc_info_toyo 벡터화. 기존과 다른 데이터 결과물이 나오면 안된다.`

---

## TL;DR

- ✅ **5/5 채널 byte-level 정합 PASS** — NaN 포함 모든 필드 정확 일치
- ✅ **평균 25.7x speedup** — 4955 entries: 1042 → 35 ms (29.2x)
- ✅ **Phase 0 build 전체** — 1076.8 → 87~118 ms (**약 10x**, 제안 §4 목표 도달)
- ✅ **사이클 분석 무영향** — A 단계 후 51 ms 그대로 (B′ 는 build 측만 가속)

---

## 변경 사항 — `DataTool_dev_code/DataTool_optRCD_proto_.py`

`_extract_tc_info_toyo` proto_:5716~5803 — Python loop groupby → pandas groupby + agg 벡터화.

### 정합 보존 측 핵심

기존 동작 정합:
- `chg.empty` / `dchg.empty` 체크 → None (count=0 분기로 변환)
- `max()` / `min()` 결과 NaN 도 `float() → round()` 통과 (NaN 보존)
- `try/except (TypeError, ValueError)` 패턴 유지
- `groupby(sort=True)` 기본 정렬 — `sorted(unique())` 로 동등 유지

### 변경 전 (Python loop)

```python
for tc, grp in raw_df.groupby('TotlCycle'):
    chg = grp[grp['Condition'] == 1]
    dchg = grp[grp['Condition'] == 2]
    v_max = float(chg['PeakVolt[V]'].max()) if not chg.empty else None
    v_min = float(dchg['Ocv'].min()) if not dchg.empty else None
    out[int(tc)] = TcInfo(...)
```

### 변경 후 (벡터화)

```python
# 그룹별 max + count (Cond=1)
_chg_grouped = raw_df.loc[raw_df['Condition'] == 1].groupby('TotlCycle')['PeakVolt[V]']
v_max_series = _chg_grouped.max()
chg_count_series = _chg_grouped.size()

# 그룹별 min + count (Cond=2)
_dchg_grouped = raw_df.loc[raw_df['Condition'] == 2].groupby('TotlCycle')['Ocv']
v_min_series = _dchg_grouped.min()
dchg_count_series = _dchg_grouped.size()

tcs = sorted(raw_df['TotlCycle'].unique())  # groupby(sort=True) 정합

out = {}
for tc in tcs:
    tc_int = int(tc)
    # count > 0 = chg.empty == False 분기 정합
    v_max = round(float(v_max_series.loc[tc]), 3) if chg_count_series.get(tc, 0) > 0 else None
    v_min = round(float(v_min_series.loc[tc]), 3) if dchg_count_series.get(tc, 0) > 0 else None
    out[tc_int] = TcInfo(tc=tc_int, v_max=v_max, v_min=v_min, source='measured')
```

### 회귀 검증 — 5채널 byte-level 정합

`tc_info_eq()` NaN-safe 비교 함수로 신·구 dict 검증:
- Keys 일치
- 각 TcInfo 의 모든 필드 (`tc`, `v_max`, `v_min`, `source`, `chg_crate`, `dchg_crate`, `v_cutoff_chg`, `v_cutoff_dchg`, `mode_chg`) 일치
- NaN 양쪽 NaN 인 경우 동일 처리

| 채널 | entries | 이전 (ms) | 신 (ms) | speedup | byte-level |
|---|---:|---:|---:|---:|---|
| Q7M Inner BLK1 ch11 | 4955 | 1026.1 | **35.2** | **29.2x** | ✅ |
| Q7M Sub ch10 | 5841 | 1191.0 | **66.1** | **18.0x** | ✅ |
| Q7M Main ch21 | 4956 | 1007.0 | **33.7** | **29.9x** | ✅ |
| M1 ch10 | 1717 | 342.7 | **12.5** | **27.4x** | ✅ |
| 김건희 245 장수명 ch22 | 796 | 158.7 | **6.7** | **23.8x** | ✅ |

**총 diffs: 0 / 평균 speedup: 25.7x**

### Phase 0 build 전체 효과

| 시점 | 이전 | B′ 후 |
|---|---:|---:|
| iteration 1 | 1076.8 ms | **118.4 ms** |
| iteration 2 | — | **90.2 ms** |
| iteration 3 | — | **87.6 ms** |

→ **9~12x speedup**, 제안 §4 의 목표 (~100 ms) 도달 ✅.

### 사이클 분석 무영향 확인

| 시점 | 이전 (A 단계 후) | B′ 후 |
|---|---:|---:|
| `toyo_cycle_data` cold | 89.9 ms | **59.1 ms** |
| `toyo_cycle_data` warm | 52.6 ms | **51.5 ms** |

→ B′ 는 build 측만 가속, 사이클 분석 측 무영향 ✅. PR #8 의 byte-level 정합 보존.

---

## Why

`_extract_tc_info_toyo` 가 Phase 0 build 1076 ms 의 96.8% 차지 ([[260509_review_b_step_feasibility_roi|B 검토]] §2.2).
원인: `for tc, grp in raw_df.groupby('TotlCycle')` × 4955 entries Python loop.

벡터화로 핫스팟 제거 → 현황 탭 분류 156 채널 시간 약 168s → 16s (10x) 도달 가능.

---

## 영향 범위

### 직접 영향

- **현황 탭 분류 / 시험유형 식별 가속** — 156 채널 메타 빌드 약 10x 도달.
- **`ChannelMeta.tc_info` 사용처 무영향** — `_merge_tc_info`, `_build_cycle_groups`, `_prior_tc_info_from_loop_groups` 측 dict lookup 만 사용 (순서 무관).

### 간접 영향

- C 단계 (사이드카 cache) 진입 시 build 비용 1100 ms → 100 ms 로 사이드카 변환 시간 단축.
- B 단계 (Toyo Phase 0 dataclass 활용) 의 build 부담 감소 — 그러나 [[260509_review_b_step_feasibility_roi|B 단독 추진]] 은 여전히 ROI 마이너스.

### 무영향

- 사이클 분석 (`toyo_cycle_data`) — 51 ms 그대로
- 프로파일 분석 (`_unified_toyo_load_raw`) — 230 ms 그대로
- PNE 측 `_extract_tc_info_pne` — 무수정
- raw 데이터 무수정

---

## 검증

- [x] 5채널 byte-level 정합 (NaN 포함)
- [x] Phase 0 build 9~12x speedup
- [x] 사이클 분석 byte-level 정합 (PR #8 회귀 시나리오)
- [x] groupby(sort=True) 기본 정합 — `sorted(unique())` 일치
- [x] `try/except (TypeError, ValueError)` 패턴 보존
- [x] NaN 보존 (chg.empty == False ∧ max() == NaN → v_max=NaN)

---

## Related

- [[260509_review_b_step_feasibility_roi]] — B 단계 ROI 검토 (B 기각 + B′ 권고)
- [[260509_proposal_toyo_speedup_to_pne_parity]] — 4 trajectory 제안
- [[260509_changelog_a_step_implementation]] — A 단계 (PNE 동등 진입)
