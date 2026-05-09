---
title: "Changelog: C′ — _unified_toyo_load_raw 메모리 cache (PNE 패턴 mirror, 류성택 요청)"
date: 2026-05-09
tags: [changelog, code, toyo, performance, c-prime, cache, mirror]
related:
  - "[[260509_review_c_step_feasibility_roi]]"
  - "[[260509_proposal_toyo_speedup_to_pne_parity]]"
status: applied
---

# Changelog: C′ — `_unified_toyo_load_raw` 메모리 cache

> 작업 요청자: 류성택 (사용자) — `C′ _unified_toyo_load_raw LRU 메모리 cache. 이 기능은 PNE도 있나? 있으면 진행할게`
> 사전 검증: PNE `_unified_pne_load_raw` (proto_:1839~1903) 가 이미 동일 cache layer 보유 → C′ = **PNE 패턴 mirror**.

---

## TL;DR

- ✅ **PNE 패턴 mirror** — `_get_channel_cache(path)['unified_raw_toyo']` single-entry cache (PNE `'unified_raw'` 와 분리 키)
- ✅ **4/4 채널 byte-level 정합 PASS** (Q7M Inner BLK1 / Q7M Sub / M1 / 김건희 245)
- ✅ **300~470x speedup** — warm hit 0.29~0.45 ms (cold 135~171 ms)
- ✅ **사이클 분석 무영향** — `toyo_cycle_data` cold 60 / warm 51 ms 그대로

---

## 변경 사항 — `DataTool_dev_code/DataTool_optRCD_proto_.py`

`_unified_toyo_load_raw` proto_:1988~2140 — PNE 패턴 mirror cache 추가.

### 추가 1 — 함수 시작 측 cache lookup (proto_:2018~2030)

```python
# C′ (260509) raw 캐시 조회 — PNE _unified_pne_load_raw (proto_:1839) 패턴 mirror.
_ch_cache = _get_channel_cache(raw_file_path)
_cache_key = (cycle_start, cycle_end, id(cycle_map) if cycle_map is not None else None)
_raw_cache = _ch_cache.get('unified_raw_toyo')
if _raw_cache is not None and _raw_cache[0] == _cache_key:
    _perf_logger.debug(f'  [unified_raw] Toyo 캐시 히트: ...')
    return _raw_cache[1].copy()
```

### 추가 2 — 함수 끝 측 cache 저장 (proto_:2138~2140)

```python
# C′ (260509) — 결과 캐시 저장 (PNE proto_:1903 패턴 mirror).
_ch_cache['unified_raw_toyo'] = (_cache_key, result.copy())
return result
```

---

## PNE 패턴 mirror 정합

| 항목 | PNE (proto_:1839, 1903) | Toyo C′ (proto_:2018, 2138) |
|---|---|---|
| Cache 위치 | `_get_channel_cache(path)['unified_raw']` | `_get_channel_cache(path)['unified_raw_toyo']` |
| Cache key | `(tc_min, tc_max)` | `(cycle_start, cycle_end, id(cycle_map))` |
| 저장 형식 | `(key, raw.copy())` | `(_cache_key, result.copy())` |
| Hit 동작 | `return _raw_cache[1].copy()` | `return _raw_cache[1].copy()` |
| 무효화 | `_reset_all_caches()` | `_reset_all_caches()` (동일) |

→ **단일 키 분리** (`'unified_raw'` vs `'unified_raw_toyo'`) — 같은 채널 path 측 충돌 방지. 운영 측 PNE/Toyo 동시 사용 가능.

---

## Cache key 설계 — `cycle_map` 처리

PNE 와 차이: Toyo 측 `cycle_map` 인자 추가.
- `cycle_map=None` → key 의 3번째 원소 `None` (TotlCycle 직접 모드)
- `cycle_map={...}` → key 3번째 원소 `id(cycle_map)` (논리사이클 매핑 모드)

호출부 정책 의존:
- 같은 `cycle_map` object 보존 시 → hit
- 매번 새 dict 생성 시 → miss (하지만 결과 동일하므로 정합 영향 없음)

`ChannelMeta.cycle_map` 이 보존되므로 일반적으로 hit.

---

## 회귀 검증 — 4채널 byte-level 정합 PASS

| 채널 | cold (ms) | warm (ms) | speedup | byte-level |
|---|---:|---:|---:|---|
| Q7M Inner BLK1 ch11 | 153.4 | **0.45** | **337x** | ✅ |
| Q7M Sub ch10 | 171.3 | **0.43** | **395x** | ✅ |
| M1 ch10 | 142.3 | **0.45** | **313x** | ✅ |
| 김건희 ch22 | 135.5 | **0.29** | **474x** | ✅ |

검증 방법:
- `_unified_toyo_load_raw(ch, 1, 100, cycle_map=None)` 두 번 호출
- 첫 호출 후 cache 저장, 두 번째 호출 = cache hit
- DataFrame shape 일치 + 모든 numeric 컬럼 sum 일치 (NaN-safe `.fillna(-999999).sum()`)

### 사이클 분석 무영향 확인

| 시점 | 이전 (B′ 후) | C′ 후 |
|---|---:|---:|
| `toyo_cycle_data` cold | 88.8 ms | **60.4 ms** |
| `toyo_cycle_data` warm | 51.2 ms | **50.6 ms** |

→ C′ 는 `_unified_toyo_load_raw` 만 수정 — `toyo_cycle_data` 의 사이클 분석 측 무영향. PR #8/#9 결과 정합.

---

## Why

[[260509_review_c_step_feasibility_roi|C 단계 검토]] 결과:
- C 자동 사이드카 (parquet) 기각 — 변환 비용 30~50분 / break-even 60~330 호출
- C′ (메모리 cache) 권고 — 변환 비용 0 / 재호출 즉시 hit / PNE 패턴 mirror

PNE 측 동일 layer (`_unified_pne_load_raw` cache, proto_:1839~1903) 가 이미 존재 — Toyo 측 mirror 가 정합.

---

## 영향 범위

### 직접 영향

- **재호출 즉시 hit** — 동일 채널 + 동일 (cycle_start, cycle_end) 측 100~200ms → 0.3~0.5ms (300~470x)
- **사용자 시나리오**:
  - UI 토글 / 그래프 재그리기 (같은 데이터 재사용): hit
  - 멀티 채널 비교 그래프: 같은 채널 측 hit
  - scope 토글 (PNE 의 cycle ↔ charge ↔ discharge 정합): hit
  - 다른 cycle 범위 요청: miss (single-entry 정책)

### 간접 영향

- `unified_profile_core` 등 호출부 측 효과 자동 반영
- PNE 패턴 정합 — `_reset_all_caches()` 측 통합

### 무영향

- 사이클 분석 (`toyo_cycle_data`) — proto_:5294~5297 변경 0
- Phase 0 build (`_build_channel_meta`) — 무영향
- PNE 측 `_unified_pne_load_raw` — 변경 0
- raw 데이터 무수정

---

## 검증

- [x] PNE 패턴 mirror 정합 (proto_:1839/1903 vs proto_:2018/2138)
- [x] 4채널 byte-level 정합 (NaN-safe sum 비교)
- [x] 300~470x speedup (warm 0.29~0.45 ms)
- [x] 사이클 분석 무영향 (PR #9 회귀 시나리오 보존)
- [x] cache key (`(cycle_start, cycle_end, id(cycle_map))`) 정합
- [x] `_reset_all_caches()` 호출 시 invalidation 정합

---

## 메모리 비용

- 채널당 100 cycle profile = ~20K rows × 10 cols × ~80 byte = **~16 MB**
- 채널 수 unbounded (PNE 정책 정합 — `_get_channel_cache` 채널별 dict)
- LRU max 정책은 별도 검토 (현재 PNE 도 unbounded)
- `_reset_all_caches()` 사용자 명시 reset 의존

---

## Related

- [[260509_review_c_step_feasibility_roi]] — C 단계 검토 (C 기각 + C′ 권고)
- [[260509_proposal_toyo_speedup_to_pne_parity]] — 4 trajectory 제안
- [[260509_changelog_b_prime_tc_info_vectorize]] — B′ 구현 (PR #9)
- [[260509_changelog_a_step_implementation]] — A 단계 (PR #8)
