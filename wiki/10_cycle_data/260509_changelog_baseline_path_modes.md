---
title: "Changelog: 경로 모드 3종 + 프로파일 옵션별 baseline (TDD, 류성택 요청)"
date: 2026-05-09
tags: [changelog, code, regression, baseline, path-modes, profile-options]
related:
  - "[[260509_changelog_full_regression_sweep]]"
  - "[[260310_link_cycle_multi_path_analysis]]"
status: applied
---

# Changelog: 경로 모드 + 프로파일 옵션별 baseline

> 작업 요청자: 류성택 (사용자) — `* 일반경로, 다중경로, 다중경로+일반경로(연결처리) * 사이클데이터 분석 * 프로파일 분석 옵션별 : 아직 옵션별 완성도가 높지않다.`

---

## TL;DR

- ✅ **경로 모드 3종 fixture** — single / multi / connected 자동 발견 (`PathBundle`)
- ✅ **사이클 분석 baseline** — 모든 경로 모드 측 첫 채널 시그니처 회귀
- ✅ **`_get_max_tc` 다중경로 회귀** — multi/connected 측 BDT 호환 검증
- ✅ **프로파일 옵션 4 조합 baseline** — `unified_profile_batch` 핵심 옵션 cover (현재 완성도 한계)
- ✅ **30 tests / 29 PASS** (1 skip = 옵션 미지원 진단 신호)

---

## 경로 모드 정의 (`PathBundle`)

| Mode | 정의 | 발견 채택 시나리오 |
|---|---|---|
| **single** | 1 dataset 단독 | 카테고리당 1 dataset (수명_Toyo / 수명 / 성능_코인셀) |
| **multi** | 동일 셀의 여러 dataset | 김건희 245mAh 수명 시리즈 (single space, 첫 3개) |
| **connected** | 시계열 연속 dataset | 김동진 Q7M Inner 1-100 + 101-200 + 201-300 + 301-400 cyc |

발견된 5 bundles:

```
single__수명_Toyo__260115_260130_3_김건희_222mAh_ATL_JINJU_SUS_상온수명_1_100
single__수명__251028_260428_05_나무늬_2335mAh_Q8_ATL_선상_SEU4_RT__1_1202
single__성능_코인셀__260121_260124_05_조용득_70mAh_BAT_ATL_GITT__1_1
multi__Toyo_Kim245_life_series       (3 datasets)
connected__Toyo_KimDJ_Q7M_Inner_1_400cyc  (4 datasets, 시계열 연결)
```

---

## 프로파일 옵션 4 조합

| Label | data_scope | axis_mode | overlap | include_rest |
|---|---|---|---|---|
| `scope_charge_axis_time` | charge | time | split | False |
| `scope_discharge_axis_time` | discharge | time | split | False |
| `scope_cycle_axis_soc` | cycle | soc | split | False |
| `scope_cycle_axis_time_with_rest` | cycle | time | split | True |

**완성도 한계 박제**:
- `overlap="connected"` 측 옵션은 후속 (현재 빈 결과 多)
- `calc_dqdv=True` 측은 후속 (smooth_degree 측 정합 측정 후)
- `cutoff` / `include_cv` 측은 dataset 의존 — 후속

향후 옵션 완성도 높아지면 baseline 갱신 또는 조합 추가.

---

## 테스트 구조 — 30 tests

```
tests/regression/test_path_modes.py
  test_cycle_path_mode_baseline       — 5 bundles × 1 = 5
  test_get_max_tc_path_mode           — 5 bundles × 1 = 5
  test_profile_options_baseline       — 5 bundles × 4 옵션 = 20
                                                          ─────
                                                            30
```

검증:
- 첫 실행: baseline JSON 생성 (`tests/regression/baselines/<label>__<suffix>.json`) → 30 skipped
- 2차 실행: baseline 비교 → **29 passed / 1 skipped** (옵션 빈 결과 진단)

---

## 변경 사항

### 1. `bdt_regression.py` — 신규 API 2건

```python
@dataclass(frozen=True)
class PathBundle:
    label: str
    mode: str           # 'single' | 'multi' | 'connected'
    data_folders: tuple[Path, ...]
    cycler: str

def discover_path_bundles(exp_data_root) -> list[PathBundle]:
    """경로 모드 3종 자동 발견 — single ~3 + multi ~1 + connected ~1."""
```

### 2. 신규 테스트 — `tests/regression/test_path_modes.py`

| 함수 | 역할 |
|---|---|
| `_first_channel(bundle)` | bundle 첫 dataset 의 첫 채널 — sweep entry |
| `_save_or_compare(label, suffix, sig, request)` | baseline 공통 저장/비교 헬퍼 |
| `test_cycle_path_mode_baseline` | 사이클 분석 시그니처 (5 tests) |
| `test_get_max_tc_path_mode` | `_get_max_tc(all_data_folder)` 다중경로 (5 tests) |
| `test_profile_options_baseline` | `unified_profile_batch` 4 옵션 × 5 bundles (20 tests) |

---

## 사용법

```bash
# 첫 1회 baseline 생성 (모든 경로 모드 + 옵션)
pytest tests/regression/test_path_modes.py --update-baseline

# 정기 회귀 검증
pytest tests/regression/test_path_modes.py

# 특정 모드만
pytest tests/regression/test_path_modes.py -k "connected"

# 프로파일 옵션만
pytest tests/regression/test_path_modes.py -k "profile_options"
```

---

## 영향 범위

### 직접 영향

- **다중경로·연결 시나리오 회귀 자동화** — BDT 핵심 운영 모드 cover
- **프로파일 옵션 진단 신호** — 옵션 미지원/빈 결과 시 자동 skip → 완성도 측정
- **기존 `test_full_sweep.py` 보완** — 단일 채널 측 904 tests + 경로 모드 측 30 tests

### 간접 영향

- **옵션 완성도 진단** — skip 수 변화로 옵션 측 진척 추적 가능
- **`_get_max_tc` 다중경로 입력 측 회귀** — multi-path GUI 운영 측 안전망

### 무영향

- BDT 본 코드 변경 0 — `bdt_regression.py` 측 fixture 추가만
- 기존 회귀 인프라 (PR #11) 보존 — 별도 테스트 파일

---

## 검증

- [x] `discover_path_bundles` — 5 bundles 자동 발견 (single 3 + multi 1 + connected 1)
- [x] 30 tests PASS/SKIP 정상 (29 PASS + 1 SKIP — 옵션 진단)
- [x] baseline JSON 자동 생성·비교
- [x] BDT 본 코드 변경 0
- [ ] 사외 PC 사용자 측 baseline 1회 생성
- [ ] 옵션 완성도 향상 시 baseline 갱신

---

## Why

[[260509_changelog_full_regression_sweep|PR #11 전수 sweep]] 가 단일 채널 분석 만 cover.
사용자 운영 측 핵심 시나리오 = **경로 모드 3종** (일반·다중·연결 처리) — 별도 회귀 인프라 필요.

프로파일 분석 측 옵션은 현재 완성도가 높지 않음 — **검증 자체가 옵션 진척 측정 도구**:
- `--update-baseline` 으로 현재 가능한 옵션의 baseline 박제
- 향후 옵션 완성 시 baseline 깨지면 = 의도된 변경 → 수동 갱신 → 진척 trace
- 옵션 미지원 / 빈 결과 → skip → 완성도 진단

---

## Related

- [[260509_changelog_full_regression_sweep]] — PR #11 전수 sweep (단일 채널)
- [[260310_link_cycle_multi_path_analysis]] — 연결 사이클 multi-path 분석
- [[260509_changelog_pne_mirror_review_and_benchmark]] — PR #11 성능 회귀
