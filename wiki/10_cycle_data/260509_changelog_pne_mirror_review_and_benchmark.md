---
title: "Changelog: PNE 측 동일 영역 검토 + pytest-benchmark 인프라 도입 (류성택 요청)"
date: 2026-05-09
tags: [changelog, code, pne, toyo, benchmark, pytest, regression]
related:
  - "[[260509_changelog_a_step_implementation]]"
  - "[[260509_changelog_b_prime_tc_info_vectorize]]"
  - "[[260509_changelog_c_prime_toyo_cache]]"
status: applied
---

# Changelog: PNE 측 동일 영역 검토 + pytest-benchmark

> 작업 요청자: 류성택 (사용자) — `pytest-benchmark 도입 / PNE 측 동일 영역 검토`

---

## TL;DR

- ✅ **PNE 측 검토 결과** — A·B′·C′ 와 동등한 가속이 **이미 대부분 적용됨**:
  - `_extract_tc_info_pne` 이미 벡터화 (5 ms / 765 TC, B′ 와 동일 패턴 — proto_:8175 docstring 명시)
  - `_unified_pne_load_raw` 이미 cache 적용 (`unified_raw` single-entry, C′ 가 PNE mirror)
  - SaveEndData positional indexing (A1 측 usecols 와 등가 효과)
- 🔥 **PNE 핫스팟 발견** — `_cached_pne_restore_files` 292 ms (Phase 0 build 339 ms 의 **87%**)
  - SaveEndData CSV read + `.cyc` gap-fill — 향후 가속 trigger 영역 (별도 트랙)
- ✅ **pytest-benchmark 인프라 도입** — `tests/perf/` 신설, Toyo 4 + PNE 2 표준 채널 fixture
- ✅ **10 tests 전체 PASS** — A·B′·C′ 회귀 임계 통과

---

## PNE vs Toyo 가속 매트릭스 — 2026-05-09 측정

### Toyo (오늘 작업 후)

| 영역 | 시간 | 가속 source |
|---|---:|---|
| `_extract_tc_info_toyo` (4955 TC) | **35 ms** | B′ groupby + agg 벡터화 (PR #9) |
| `_unified_toyo_load_raw` (100cyc cold) | **141 ms** | A2 ThreadPool (PR #8) |
| `_unified_toyo_load_raw` (100cyc warm) | **0.45 ms** | C′ memory cache (PR #10) |
| `toyo_cycle_data` cold | **60~95 ms** | A1 usecols + A3 agg (PR #8) |
| `toyo_cycle_data` warm | **51 ms** | lru_cache hit |
| Phase 0 build cold | **90 ms** | B′ 효과 |

### PNE (현재)

| 영역 | 시간 | 가속 source | 상태 |
|---|---:|---|---|
| `_extract_tc_info_pne` (765 TC) | **5 ms** | numpy mask + groupby agg (이전 작업 — proto_:8175) | ✅ 이미 가속 |
| `_unified_pne_load_raw` cache | hit 시 즉시 | `_get_channel_cache()['unified_raw']` (이전 작업 — proto_:1839) | ✅ 이미 가속 |
| `pne_cycle_data` cold | **288 ms** | Phase 0 ChannelMeta + pivot_table | ⚠️ 여유 |
| `pne_cycle_data` warm | **15 ms** | cache hit | ✅ 빠름 |
| `_cached_pne_restore_files` cold | **259 ms** | 캐시 1차 호출 | 🔥 핫스팟 |
| Phase 0 build cold | **282 ms** | Toyo 90 ms 대비 **3x 느림** | 🔥 핫스팟 |

### 핵심 통찰

1. **PNE B′ 등가 작업은 이미 끝남** — `_extract_tc_info_pne` 측 5x speedup 달성 (이전 commit, proto_:8175 docstring "iterrows / 람다 0건. 760 TC 기준 ~254ms → ~50ms (5x)")
2. **PNE C′ 등가 작업도 이미 끝남** — `_unified_pne_load_raw` 측 channel single-entry cache (proto_:1839~1903). C′ 는 정확 PNE mirror.
3. **PNE 측 추가 가속 여지** — `_cached_pne_restore_files` 259~292 ms 가 Phase 0 build 의 87%. SaveEndData read 측 usecols 적용 (Toyo A1 mirror) 가능.

---

## pytest-benchmark 인프라

### 신설 디렉토리

```
tests/
└── perf/
    ├── __init__.py
    ├── conftest.py          # 표준 채널 fixture (Toyo 4 + PNE 2)
    ├── test_toyo_perf.py    # A·B′·C′ 회귀 임계
    └── test_pne_perf.py     # PNE 측 가속 + 핫스팟 추적
```

### 표준 채널 fixture

| 라벨 | 사이클러 | 사이즈 | 비고 |
|---|---|---|---|
| `Q7M_Inner_BLK1_4956` | Toyo | 4956 step | 큰 채널 (가속수명) |
| `Q7M_Sub_5841` | Toyo | 5841 step | 큰 채널 (가속수명) |
| `M1_1717` | Toyo | 1717 step | 중 채널 |
| `Kim_245_796` | Toyo | 796 step | 작은 채널 (장수명) |
| `M01Ch008_765TC` | PNE | 765 TC | Q8 RT 수명 |
| `M01Ch014_764TC` | PNE | 764 TC | Q8 RT 수명 |

### 회귀 임계 — 10 tests

#### Toyo (5 tests, 임계 단일 채널 기준)

| 테스트 | 임계 (ms) | A·B′·C′ baseline (Kim_245) | margin |
|---|---:|---:|---:|
| `test_toyo_cycle_cold` | 250 | 26.2 | ~10x |
| `test_toyo_cycle_warm` | 100 | 20.4 | ~5x |
| `test_toyo_phase0_build_cold` | 200 | 24.2 | ~8x |
| `test_toyo_profile_100cyc_cold` | 500 | 146 | ~3x |
| `test_toyo_profile_100cyc_warm_cprime` | 5 | **0.10** | ~50x |

#### PNE (5 tests, M01Ch008 기준)

| 테스트 | 임계 (ms) | baseline | margin |
|---|---:|---:|---:|
| `test_pne_cycle_cold` | 500 | 288 | ~1.7x |
| `test_pne_cycle_warm` | 50 | 15.1 | ~3.3x |
| `test_pne_phase0_build_cold` | 500 | 282 | ~1.8x |
| `test_pne_extract_tc_info` | 20 | 4.1 | ~5x |
| `test_pne_restore_files_cold` | 500 | 259 | ~1.9x |

### 실행

```bash
# 전체 perf 회귀
pytest tests/perf -m perf --benchmark-only

# baseline 저장 (회귀 비교용)
pytest tests/perf -m perf --benchmark-save=baseline_2026_05_09

# baseline 비교 (가속·퇴보 검출)
pytest tests/perf -m perf --benchmark-compare=baseline_2026_05_09

# 특정 채널만
pytest tests/perf -m perf -k "Kim_245" --benchmark-only
```

### marker 정책

`pyproject.toml` 측 `addopts` 갱신:
- 기본 실행: `-m 'not gui and not perf'` — perf 테스트 제외 (raw 데이터 의존)
- 명시 실행: `-m perf` 또는 `--benchmark-only`

---

## 변경 사항

### 1. `pyproject.toml`

```diff
 [project.optional-dependencies]
 test = [
     "pytest>=8.0",
     "pytest-qt>=4.4",
+    "pytest-benchmark>=4.0",
 ]

 [tool.pytest.ini_options]
 testpaths = ["tests"]
 markers = [
     "gui: GUI 필요 테스트 (pytest-qt, Windows)",
     "slow: 대용량 데이터 또는 오래 걸리는 테스트",
+    "perf: 성능 회귀 검증 (pytest-benchmark) — 사용자 raw 데이터 의존",
 ]
-addopts = "-m 'not gui' -v"
+addopts = "-m 'not gui and not perf' -v"
```

### 2. 신규 파일 4건

- `tests/perf/__init__.py` — package marker
- `tests/perf/conftest.py` — 표준 채널 fixture (Toyo 4 + PNE 2) + bdt 모듈 fixture
- `tests/perf/test_toyo_perf.py` — 5 benchmark (cold/warm × cycle/build/profile)
- `tests/perf/test_pne_perf.py` — 5 benchmark (cycle/build/extract/restore)

---

## 검증

- [x] 10 tests 전체 PASS (Toyo 5 + PNE 5)
- [x] PNE `_extract_tc_info_pne` 이미 벡터화 확인 (5 ms / 765 TC)
- [x] PNE `_unified_pne_load_raw` cache 이미 적용 확인 (proto_:1839~1903)
- [x] PNE Phase 0 핫스팟 식별 (`_cached_pne_restore_files` 87%)
- [x] pyproject.toml marker `perf` 기본 제외 (raw 데이터 의존성 정합)

---

## Why

[[260509_proposal_toyo_speedup_to_pne_parity|Toyo 가속 4 trajectory]] 의 후속 작업:
- A·B′·C′ 가속 효과 회귀 검증 인프라 필요 (pytest-benchmark)
- PNE 측 동일 가속 영역 검토 — 이미 적용 / 추가 여지 식별

검토 결과: **PNE 측은 대부분 이미 가속**. Toyo 가 따라잡은 셈. 추가 가속 여지는 `_cached_pne_restore_files` 측만 — 별도 트랙 (PNE A1 mirror).

---

## 영향 범위

### 직접 영향

- **회귀 검증 자동화** — A·B′·C′ 효과 보존 자동 검증 (성능 퇴보 시 즉시 발견)
- **baseline 비교** — `--benchmark-save` / `--benchmark-compare` 측 정기 회귀 검증
- **PNE 핫스팟 추적** — `_cached_pne_restore_files` cold 측정 통해 향후 가속 trigger

### 간접 영향

- **ADR-0008 정합** — fixture α 의 `tests/data_*` 표준 측 본 perf fixture 가 baseline 역할
- **신규 가속 작업 시 회귀 빠른 검증** — 코드 변경 후 `pytest -m perf` 한 줄

### 무영향

- BDT 본 코드 (`DataTool_optRCD_proto_.py`) 변경 0
- raw 데이터 무수정
- 기존 `tools/test_code/` 회귀 슈트 보존 (`regression_extract_tc_info_pne.py` 등)

---

## 후속 작업 (옵션)

1. **PNE A1 mirror — `_cached_pne_restore_files` usecols 가속** — 핫스팟 87% 제거 trigger
2. **사외 PC baseline 저장** — `pytest -m perf --benchmark-save=baseline_2026_05_09`
3. **CI 통합** — pre-commit / 사외 PC 정기 실행
4. **추가 fixture 채널** — 신뢰성 충방전기 / BLK5200 등 변종 검증

---

## Related

- [[260509_changelog_a_step_implementation]] — A 단계 (PR #8)
- [[260509_changelog_b_prime_tc_info_vectorize]] — B′ 벡터화 (PR #9)
- [[260509_changelog_c_prime_toyo_cache]] — C′ Toyo cache mirror (PR #10)
- [[260509_review_b_step_feasibility_roi]] — B 검토 (Phase 0 핫스팟)
- [[260509_review_c_step_feasibility_roi]] — C 검토 (사이드카 기각)
- [[31_software_dev/adr/0008-bdt-test-and-study-automation|ADR-0008]] — fixture α/β/γ/δ 정합
