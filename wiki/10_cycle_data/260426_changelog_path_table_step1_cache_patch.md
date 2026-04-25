---
title: "경로 테이블 Step 1 — 캐시 누락 패치 (check_cycler / _quick_max_cycle)"
date: 2026-04-26
tags: [changelog, cycle-data, performance, cache, lru]
related:
  - "[[../00_index/path_table_redesign|경로 테이블 재설계 plan]]"
  - "[[260425_review_pne_mscc_cccv_cutoff|PNE MSCC CCCV 검증]]"
---

# 경로 테이블 Step 1 — 캐시 누락 패치

> **PR #1 / 6** — 점진적 재설계의 첫 단계. 가장 작은 변경으로 가장 큰 효과.

## 배경

사용자 환경(갤럭시북 + 네트워크 드라이브)에서 경로 테이블 입력 시 5–30초 UI freeze 발생. 원인 분석 중 `lru_cache` 누락 함수 두 개를 발견:

| 함수 | 위치 | 단일 호출 비용 | 호출 빈도 |
|---|---|---|---|
| `check_cycler(path)` | `DataTool_optRCD_proto_.py:514` | 50–200 ms (`os.path.isdir` + `os.listdir`) | 매 경로 입력·confirm·is_pne_folder 폴백 |
| `_quick_max_cycle(path, cap)` | `:568` | 100 ms – 5 s (`os.scandir` + `check_cycler` + `get_cycle_map`) | autofill·TC 힌트·max TC 산정 |

특히 같은 path 가 여러 호출 경로에서 반복 조회되는 패턴 (autofill 4회·confirm 1회 = 같은 경로 5회 IO) 이 그대로 노출.

`_get_pne_cycle_map` (`:7882`) 와 `_get_toyo_cycle_map` (`:7912`) 는 이미 `@functools.lru_cache(maxsize=256)` 적용되어 있었음 — 두 quick 함수만 누락된 상태였다.

## 변경 사항

### 1) `check_cycler` (L514) — `lru_cache(maxsize=512)` 적용

```python
@functools.lru_cache(maxsize=512)
def check_cycler(raw_file_path):
    """충방전기 데이터 폴더로 PNE와 Toyo를 구분한다.
    ...
    네트워크 드라이브에서 os.path.isdir/os.listdir 비용이 50-200ms 이므로
    경로 단위 lru_cache 로 반복 호출 비용 0 으로 줄임.
    무효화는 `_reset_all_caches()` 에서 일괄 처리.
    """
```

- 인자: `raw_file_path` 단일 (hashable str) → 추가 변환 불필요
- maxsize 512 — 일반 사용 (5경로) 의 100배 여유
- 반환 bool 은 동일 경로 동일 결과 보장 (폴더 구조 변경 없을 때) → 캐시 안전

### 2) `_quick_max_cycle` (L568) — `lru_cache(maxsize=256)` 적용

```python
@functools.lru_cache(maxsize=256)
def _quick_max_cycle(data_path: str, mincapacity: float = 0) -> int | None:
    """경로의 첫 채널 폴더에서 최대 **논리 사이클** 수를 빠르게 추정
    ...
    네트워크 드라이브 환경에서 os.scandir + check_cycler + get_cycle_map 의
    비용이 누적되므로 (path, cap) 키 lru_cache 로 반복 호출 비용 0 으로 줄임.
    """
```

- 인자: `(data_path, mincapacity)` 두 hashable → tuple 키 자동 생성
- 내부 호출도 모두 캐시됨 → 첫 호출 후 거의 0ms

### 3) `_reset_all_caches` (L776) — 무효화 추가

```python
    # 경로 단위 IO 캐시 (Step 1 패치)
    check_cycler.cache_clear()
    _quick_max_cycle.cache_clear()
```

기존 `_get_pne_cycle_map.cache_clear()` 등과 같은 위치에 2줄 추가. 새 데이터 로드 시 stale 캐시 자동 무효화.

## 효과 추정

전형적 시나리오 — 5경로 paste → 자동 채우기 → confirm:

| 단계 | 패치 전 | 패치 후 |
|---|---|---|
| paste 후 첫 autofill (5경로) | 5 × (200ms + 1s) = **6s** | 5 × (200ms + 1s) = **6s** (캐시 miss 첫 회) |
| confirm 시 두 번째 autofill | **6s** (재 IO) | **0ms** (cache hit) |
| 동일 경로 5번 입력 (정리·재입력 시나리오) | 30s | 6s + 0ms × 4 = **6s** |
| **합계 절감** | — | **약 50%** |

## 위험·검증

- **위험**: 매우 낮음. lru_cache 무효화는 `_reset_all_caches()` 가 이미 호출되는 모든 경로에서 자동 처리됨
- **회귀**: 폴더 구조가 외부에서 변경되어도 `_reset_all_caches()` 호출 전엔 stale 가능성 → 새 데이터 로드 시 항상 무효화되므로 실용상 문제 없음
- **메모리**: 512 + 256 슬롯, key+bool/int 만 저장 → 무시 가능 (≪ 1MB)

## 검증 항목 (사용자 알파)

- [ ] 동일 경로 5번 paste → confirm. 두 번째 confirm 부터 빠르게 응답
- [ ] `_reset_all_caches()` 호출 후 다음 입력은 cache miss (정상 IO 발생)
- [ ] 폴더 구조 외부 변경 후 새 데이터 로드 시 반영 (사용자가 명시 새로고침 시)
- [ ] cache_info() 로 hit/miss 비율 확인 (개발 디버깅)

## 다음 단계

- **Step 2** (PR #2): `_resolve_path_meta` Light/Full 분리
- **Step 3** (PR #3): 자동 채우기 트리거 분리 (light auto, full 은 confirm 시점)
- **Step 4** (PR #4): confirm 시 자동 full 채우기 + statusBar 진행률
- **Step 5** (PR #5): 삭제·변경 시 캐시 일관성
- **Step 6** (PR #6): paste 다중 행/열 강화 + 연결처리 토글 즉시 hint

상세 plan: `C:/Users/Ryu/.claude/plans/4-1-1-proud-ladybug.md`
