---
title: "[Changelog] .cyc 보충 TC 중복 dedup — DchgCap 2배 누적 차단"
date: 2026-05-10
tags: [changelog, bugfix, cyc, supplement, dedup, dchg]
related:
  - "[[260418_cyc_supplement_log_extension]]"
  - "[[260419_BDT_Parsing_Pipeline]]"
  - "[[260509_log_integrity_layers]]"
status: applied
---

# .cyc 보충 TC 중복 dedup — DchgCap 2배 누적 차단

> 작업 요청자: 류성택 — 우정협 Tab S12 dataset LC 709-711 방전 용량이 정상값의 2배(~1.748) 출력 보고

## TL;DR

- ✅ **TC 가드 추가** — `_cached_pne_restore_files` 의 .cyc 보충 필터에 `csv_tcs` 가드 결합
- ✅ **2배 누적 제거** — 우정협 LC 709-711 1.74 → 0.87 (정상)
- ✅ **회귀 0** — `regression_classify_pne_cycles.py` 760 entries PASS, exp_data 전수 export 204/204
- ✅ **`save_end` 정합 회복** — 5777 → 5750 행 (.cyc 27 중복행 제거)

## 근본 원인

CSV 와 `.cyc` 가 **같은 TC를 다른 RecIdx로 양쪽 기록** (장비 재시작·chunk 재기록):

| TC | CSV RecIdx | .cyc RecIdx | 결과 |
|---|---|---|---|
| 711 | 374572, 374624 | 373224, 373276 | RecIdx 다름 → 필터 통과 → 4 dchg 행 |
| 712 | 374909, 374961 | 373561, 373613 | 동일 |
| 713 | 375247, 375299 | 373898, 373950 | 동일 |
| 714 | 375566 | 374235, 374287 | 동일 |

`pivot_table(aggfunc=sum)` 에서 같은 TC 의 4 dchg 행 합산 → DchgCap 2배 → norm 1.748.

## 변경 — 2 줄 추가

```python
# Before
csv_rec_indices = set(int(x) for x in save_end_data[0].unique())
supplement = _cyc_mapped[
    ~_cyc_mapped[0].astype(int).isin(csv_rec_indices)]

# After (260510 fix)
csv_rec_indices = set(int(x) for x in save_end_data[0].unique())
csv_tcs = set(int(x) for x in save_end_data[27].unique())   # NEW
supplement = _cyc_mapped[
    ~_cyc_mapped[0].astype(int).isin(csv_rec_indices)
    & ~_cyc_mapped[27].astype(int).isin(csv_tcs)]            # NEW
```

### 정책
- **CSV는 가장 신뢰 가능한 최신 기록** (장비가 chunk 단위로 마지막에 재기록)
- `.cyc 보충` 본 의도 = **gap-fill** (CSV 가 가지지 않은 신규 TC 추가)
- TC가 CSV·.cyc 양쪽 → CSV 우선, .cyc 무시 (중복 차단)

## 검증

| 채널 | LC 709 Before | After | LC 710 Before | After | LC 711 Before | After |
|---|---|---|---|---|---|---|
| Ch013 | 1.7483 | **0.8744** | 1.7482 | **0.8743** | 1.7479 | **0.8740** |
| Ch014 | 1.7464 | **0.8735** | 1.7462 | **0.8733** | 1.7460 | **0.8731** |
| Ch015 | 1.7461 | **0.8733** | 1.7458 | **0.8731** | 1.7455 | **0.8729** |

전체 Dchg > 1.2 인 LC: 3 → **0**

## "어제 픽스" 추적

사용자 표현 "어제 픽스 진행했는데" 는 `b907425` (260418, `.cyc 보충 로그 확장`) 추정. 해당 commit 은 **로그 출력만 개선** 하고 dedup 로직은 그대로였음. 본 fix 가 dedup 의 실질적 개선 (RecIdx-only → RecIdx + TC).

## 호환성

- **정상 gap-fill** (.cyc TC ⊄ CSV TC): 동작 불변 — 보충 그대로 동작
- **TC overlap 케이스** (재시작 시나리오): TC 가드로 차단 → CSV 사용
- **.cyc 단독** (Restore 없음): 영향 없음 (별도 경로)
- **Toyo**: 영향 없음 (PNE-only 경로)

## 영향 범위

### 직접 영향
- 우정협 Tab S12 dataset 3 채널 LC 709-711 정상화
- 동일 TC 중복 패턴 데이터셋 자동 정상화

### 간접 영향
- Phase 0 메타 (cycle_map / classified / max_tc) 일관성 회복
- 사이클·프로파일 분석·연결처리 라우팅 모두 정합

### 무영향
- 정상 gap-fill / .cyc 단독 / 비-PNE 데이터

## Why

[[260418_cyc_supplement_log_extension]] 의 로그 확장 fix 는 dedup 로직을 건드리지 않아 RecIdx-only 필터가 그대로 유지됨. 사용자가 "어제 픽스" 라고 인식한 것은 로그 가시성 개선이었지 실질 dedup 가 아니었음 — 본 fix 가 그 갭 메움.

[[260509_log_integrity_layers]] 의 `_check_endpoint_anomaly` 는 `.cyc < SaveData` 케이스를 감지하지만 본 케이스는 .cyc·CSV TC overlap (silent corruption 의 변종) — 별도 가드 필요.

## Related

- `docs/code/01_변경로그/260510_cyc_supplement_tc_dedup.md` — 코드 상세 변경
- `docs/code/02_레퍼런스/260510_exp_data_cycle_timelines_v4.html` — fix 적용 후 전수 시각화
- `tools/debug_woojh_dchg.py` — 진단 도구

## 후속 정합 후보

1. **`.cyc 보충` 로그에 차단된 TC 표시** — `차단된 .cyc TC: 711-714` 사용자 가시성
2. **`_classify_pne_integrity` 4-tier 에 TC overlap 케이스 추가** — `compromised_overlap` 등
3. **integrity_check 자동 호출** — TC overlap 감지 시 사용자에게 경고 다이얼로그
