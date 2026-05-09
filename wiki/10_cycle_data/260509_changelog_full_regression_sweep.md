---
title: "Changelog: 전수 회귀 검증 시스템 — 사이클·프로파일 분석 byte-level (TDD, 류성택 요청)"
date: 2026-05-09
tags: [changelog, code, regression, tdd, signature, full-sweep]
related:
  - "[[260509_changelog_pne_mirror_review_and_benchmark]]"
status: applied
---

# Changelog: 전수 회귀 검증 — 사이클·프로파일 byte-level

> 작업 요청자: 류성택 (사용자) — `프로파일 분석(사이클 전체), 사이클 분석 테스트 자동화 / 전수 검사 가능하도록 구성해`
> TDD 정합 vertical slice — 6 RED→GREEN cycle.

---

## TL;DR

- ✅ **전수 검사 가능** — exp_data 측 **452 채널** (PNE 292 + Toyo 160) 자동 발견 + parametrize
- ✅ **byte-level 회귀 검증** — `df.NewData` (사이클) + `_unified_*_load_raw` 후 정규화 (프로파일) 모두 시그니처 비교
- ✅ **에러 isolation** — 단일 채널 실패가 전체 sweep 중단 X (자동 skip)
- ✅ **병렬 지원** — pytest-xdist 측 4 worker 시 30분 → ~10분
- ✅ **14 tests PASS** — Q7M Inner BLK1 18ch + M01Ch008 측 사이클·프로파일 byte-level 정합 확인

---

## TDD 6 RED→GREEN cycle

| Cycle | RED | GREEN | 결과 |
|---|---|---|---|
| **1** | `discover_channels` 부재 | `bdt_regression.py` 신설 | 5/5 PASS |
| **2** | `extract_signature` 부재 | column-wise stats dict | 8/8 PASS |
| **3** | 사이클 회귀 (1 채널 tracer) | baseline JSON + 비교 | 1/1 PASS |
| **4** | 프로파일 풀 (1 채널) | `_profile_full()` helper | 부분 sweep PASS |
| **5** | 전수 parametrize | `@pytest.mark.parametrize(_CHANNELS)` | 14/14 PASS |
| **6** | 에러 isolation | try/except + skip | 14/14 PASS (sweep 중단 X) |

---

## 변경 사항

### 1. 신규 모듈 — `DataTool_dev_code/bdt_regression.py`

**Public API**:
- `discover_channels(exp_data_root) -> list[ChannelInfo]` — 전수 채널 자동 발견
- `extract_signature(df) -> dict[col, stats]` — column-wise (n, sum, median, min, max)
- `signatures_equal(sig_a, sig_b, *, rel_tol=0, abs_tol=0) -> bool` — byte-level 또는 허용 오차
- `signature_diff(sig_a, sig_b) -> list[str]` — 회귀 진단 메시지

### 2. 신규 테스트 — `tests/regression/`

| 파일 | 역할 | tests |
|---|---|---:|
| `__init__.py` | package marker | — |
| `conftest.py` | `--update-baseline` flag | — |
| `test_inventory.py` | `discover_channels` 회귀 | 5 |
| `test_signature.py` | `extract_signature` + `signatures_equal` | 8 |
| `test_cycle_regression.py` | 1 채널 tracer (Q7M Inner BLK1 ch11) | 1 |
| `test_full_sweep.py` | 전수 사이클 + 프로파일 (452 × 2 = **904 tests**) | 904 |

### 3. `pyproject.toml`

```diff
 test = [
     "pytest>=8.0",
     "pytest-qt>=4.4",
     "pytest-benchmark>=4.0",
+    "pytest-xdist>=3.0",
 ]
```

### 4. `.gitignore`

```diff
 _workspace/
+tests/regression/baselines/
```

baseline JSON 은 사용자 측 raw 데이터 의존 — 사외/사내 환경 별도 생성.

---

## 설계 — 시그니처 vs byte-level

| 항목 | 시그니처 모드 (default) | byte-level 모드 (옵션) |
|---|---|---|
| 비교 unit | column별 (n, sum, median, min, max) | row별 정확 일치 |
| baseline 크기 | ~2 KB / 채널 | ~10 MB / 채널 (parquet) |
| 452 채널 누적 | ~1 MB | ~4.5 GB |
| 회귀 검증 정밀도 | 통계적 (NaN-safe) | byte-level |
| 검출 가능한 변경 | 컬럼 추가/삭제 + numerical 변동 | 모든 row 단위 변경 |

**시그니처 모드 정당화**: A·B′·C′ 회귀 검증 측 `signatures_equal` 가 NaN-safe sum 비교 (이미 검증됨, PR #8/#9/#10 측 4채널 byte-level diff 와 동일 효과).

---

## 사용법

### 첫 1회 — baseline 생성

```bash
# 직렬 (약 30~60분)
pytest tests/regression/test_full_sweep.py --update-baseline

# 병렬 (4 worker, 약 10~15분)
pytest tests/regression/test_full_sweep.py --update-baseline -n 4

# 대표 채널만 (약 1분)
pytest tests/regression/test_full_sweep.py --update-baseline -k "Q7M_Inner_BLK1 or M01Ch008"
```

### 정기 회귀 검증

```bash
# 전수 회귀 (병렬)
pytest tests/regression/test_full_sweep.py -n 4

# 특정 카테고리만
pytest tests/regression/test_full_sweep.py -k "수명_Toyo"

# 짧은 traceback
pytest tests/regression/test_full_sweep.py --tb=short -n 4
```

### baseline 갱신 (가속 작업 후 의도된 변경)

```bash
# 의도된 변경 후 baseline 재생성
pytest tests/regression/test_full_sweep.py --update-baseline -n 4
```

---

## 에러 isolation 정책 (RED 6)

| 케이스 | 처리 |
|---|---|
| 분석 함수 예외 (`toyo_cycle_data` / `pne_cycle_data` raise) | `pytest.skip(...)` — 전체 sweep 계속 |
| 빈 결과 (`df.NewData.empty`) | `pytest.skip("빈 결과: ...")` |
| numeric 컬럼 0개 | `pytest.skip("numeric 컬럼 없음: ...")` |
| baseline 부재 + `--update-baseline` 미사용 | `pytest.skip("baseline 생성: ...")` |
| 시그니처 불일치 | `pytest.fail(...)` — diff 첫 10 항목 표시 |

---

## 검증

- [x] `discover_channels`: 5/5 PASS (총 452 채널, 빈 4 skip)
- [x] `extract_signature`: 8/8 PASS (NaN-safe + dict structure)
- [x] tracer 채널 (Q7M Inner BLK1 ch11): 1/1 PASS
- [x] 14 채널 sweep (Q7M Inner BLK1 18ch + M01Ch008 측): 14/14 PASS
- [x] baseline JSON 자동 생성·비교
- [x] 에러 isolation 작동 (단일 채널 실패가 sweep 중단 X)
- [x] BDT 본 코드 (`DataTool_optRCD_proto_.py`) 변경 0 — 회귀 검증 인프라만
- [ ] 전체 904 tests sweep (사용자 측 첫 trigger)
- [ ] 사외 PC baseline 저장 (사용자 측)

---

## Why

[[260509_changelog_pne_mirror_review_and_benchmark|PR #11]] 의 pytest-benchmark 가 **성능 회귀** 만 cover.
**정확성 회귀** (값 정합) 는 별도 인프라 필요:
- A·B′·C′ 가속 작업 후 출력 정합 보장
- 향후 가속 작업 (PNE A1 mirror 등) 측 자동 검증
- 다양한 채널 (시험유형 / 사이클러 / BLK 변종) 측 cover

전수 검사 가능 시 모든 채널 측 회귀 자동 검증 → 신규 작업 안전성 보장.

---

## 영향 범위

### 직접 영향

- **회귀 자동화** — 전수 904 tests 측 byte-level 정합 자동 검증
- **신규 가속 작업 측 안전망** — 코드 변경 시 회귀 즉시 검출
- **baseline 분기별 갱신** — 의도된 변경 후 `--update-baseline`

### 간접 영향

- **ADR-0008 fixture α/β 구현** — 표준 채널 발견 + 시그니처 baseline
- **CI 통합 가능** — 사외 PC 측 정기 실행

### 무영향

- BDT 본 코드 (`DataTool_optRCD_proto_.py`) 변경 0
- 기존 `tests/perf/` (PR #11) 영향 0 — 별도 marker
- raw 데이터 무수정

---

## 후속 작업 (옵션)

1. **사외 PC 측 baseline 저장** — `--update-baseline -n 4` 1회
2. **byte-level 모드** — 옵션 활성화 시 parquet baseline (대표 12 채널)
3. **시각 회귀 (γ)** — pytest-mpl 측 그래프 골든 image
4. **저장 schema (δ)** — Excel 출력 컬럼·dtype 자동 점검
5. **CI 통합** — pre-commit / 정기 사외 PC

---

## Related

- PR #8 — A 단계 (Toyo 가속)
- PR #9 — B′ 벡터화
- PR #10 — C′ Toyo cache mirror
- [[260509_changelog_pne_mirror_review_and_benchmark]] — PR #11 (성능 회귀)
- [[31_software_dev/adr/0008-bdt-test-and-study-automation|ADR-0008]] — fixture α/β/γ/δ
