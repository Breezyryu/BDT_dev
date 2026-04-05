# 260404 논리사이클 Phase A-2 — GITT/DCIR 스윕 그룹핑

## 배경 / 목적

Phase A-1에서 PNE 일반 시험(가속수명, 율별, 보관 등)의 논리사이클 매핑을 구현했으나,
**GITT·DCIR·펄스 시험**에서는 TotlCycle 1개가 독립적인 충방전 사이클이 아니라
SOC 구간별 펄스 측정의 한 조각에 해당한다.

사용자 관점에서 "1 논리사이클"은 다음과 같다:
- **충전하면서 SOC 구간별 펄스** (충전 스윕 전체) + **방전하면서 SOC 구간별 펄스** (방전 스윕 전체)

Phase A-2는 이러한 스윕 시험을 자동 감지하여, 여러 TotlCycle을 방향 기반으로
그룹핑한 뒤 논리사이클로 매핑하는 기능을 추가한다.

---

## 변경 내용

### 1. `_opposite_dirs()` 신규 헬퍼 함수

두 방향 문자열이 서로 반대인지 판별하는 유틸리티.

```python
def _opposite_dirs(d1: str, d2: str) -> bool:
    """충전/방전 방향이 반대인지 판별."""
    return (d1 == 'CHG' and d2 == 'DCHG') or (d1 == 'DCHG' and d2 == 'CHG')
```

**위치**: `toyo_build_cycle_map()` 뒤, `_pne_build_sweep_cycle_map()` 앞 (line 2625)

---

### 2. `_pne_build_sweep_cycle_map()` 신규 함수

GITT/DCIR/펄스 시험 전용 스윕 그룹핑 알고리즘.

```python
def _pne_build_sweep_cycle_map(
    pivot: pd.DataFrame,
    all_tcs: list[int],
    mincapacity: float,
) -> dict:
```

**4단계 알고리즘:**

| 단계 | 내용 | 세부 |
|------|------|------|
| 1단계 | TC별 속성 결정 | 유의 여부(sig), 주 방향(CHG/DCHG/MIXED), 충방전 유무(has_both) |
| 2단계 | 세그먼트화 | 유의 TC → 개별 세그먼트, 비유의 TC → 연속 동일 방향 스윕 누적 |
| 3단계 | 스윕 쌍 병합 | 인접 반대 방향 스윕(CHG+DCHG 또는 DCHG+CHG) → 1개 병합 세그먼트 |
| 4단계 | cycle_map 변환 | 유의(has_both) → `int`, 스윕 범위 → `tuple(시작TC, 끝TC)` |

**핵심 판별 기준:**

- **유의(significant) TC 판별**: `max(ChgCap, DchgCap) ≥ mincapacity × 1000 × 0.2`
  - SaveEndData 값이 μAh 단위이므로 mAh를 μAh로 변환 (×1000) 후 20% 적용
- **주 방향 결정**: Chg/Dchg 비율 > 1.5 → 우세 방향, 아니면 MIXED
  - MIXED TC는 현재 스윕에 합류 (방향 전환을 발생시키지 않음)
- **방향 전환 경계**: 비유의 TC의 방향이 현재 스윕 방향과 다르면 스윕 마감 후 새 스윕 시작

**위치**: line 2630 ~ 2752

---

### 3. `pne_build_cycle_map()` 수정 — 시험 유형 자동 감지

**Before (Phase A-1):**
```python
def pne_build_cycle_map(...) -> tuple[dict, float]:
    # 항상 TotlCycle 단위 1:1 매핑
    # 충방전 쌍이 모두 있는 TotlCycle만 유효
```

**After (Phase A-2):**
```python
def pne_build_cycle_map(...) -> tuple[dict, float]:
    # 유의 사이클 비율(sig_ratio) 계산
    sig_ratio = n_significant / len(all_tcs)

    if sig_ratio >= 0.5:
        # 일반 시험 → Phase A-1 로직 (TotlCycle 단위 1:1 매핑)
    else:
        # 스윕 시험 → _pne_build_sweep_cycle_map() 호출
        cycle_map = _pne_build_sweep_cycle_map(pivot, all_tcs, mincapacity)
```

**자동 감지 로직:**
- 전체 TC 중 "유의 TC" (공칭 용량 20% 이상)의 비율을 계산
- `sig_ratio ≥ 0.5` → 일반 수명/율별/보관 시험 → Phase A-1 로직
- `sig_ratio < 0.5` → GITT/DCIR/펄스 시험 → Phase A-2 스윕 로직

**반환 타입 다형성:**
- cycle_map 값이 `int` (단일 TotlCycle) 또는 `tuple[int, int]` (스윕 범위)

---

### 4. `_unified_pne_load_raw()` 수정 — tuple cycle_map 지원

**Before:**
```python
if cycle_map:
    totl_cycles = [cycle_map[lc] for lc in range(...)]
    raw = raw.loc[raw[27].isin(totl_cycles)]
```

**After:**
```python
if cycle_map:
    totl_cycles_set: set[int] = set()
    logical_to_totl: dict[int, int] = {}
    for logical_cyc in range(cycle_start, cycle_end + 1):
        if logical_cyc in cycle_map:
            val = cycle_map[logical_cyc]
            if isinstance(val, tuple):
                tc_start, tc_end = val
                for tc in range(tc_start, tc_end + 1):
                    totl_cycles_set.add(tc)
                    logical_to_totl[tc] = logical_cyc
            else:
                totl_cycles_set.add(val)
                logical_to_totl[val] = logical_cyc
    raw = raw.loc[raw[27].isin(totl_cycles_set)]
```

**변경 사항:**
- `tuple` 값 처리: `(시작TC, 끝TC)` → 범위 내 모든 TC를 set에 추가
- `isin(list)` → `isin(set)` 변경으로 O(n) → O(1) 룩업 성능 개선
- 역매핑(`logical_to_totl`) 추가: 각 물리 TC가 어느 논리사이클에 속하는지 추적

---

## 9개 시험 유형별 검증 결과

분석 문서(`260404_analysis_pattern_vs_rawdata_cycle_mapping.md`)의 9개 시험 유형을 기준으로 알고리즘 동작을 검증했다.

### 일반 시험 (sig_ratio ≥ 0.5 → Phase A-1 로직)

| 시험 유형 | TC 수 | 유의 TC | sig_ratio | 결과 |
|-----------|-------|---------|-----------|------|
| ① 가속수명 | 200+ | 전부 | 1.0 | TC=논리사이클 1:1 매핑 |
| ② 율별 | 여러 | 대부분 | >0.5 | TC=논리사이클 1:1 매핑 |
| ③ 보관용량 | 수십 | 대부분 | >0.5 | TC=논리사이클 1:1 매핑 |
| ④ 활성화/출하 | 수 | 전부 | 1.0 | TC=논리사이클 1:1 매핑 |
| ⑤ HPPC(짧은) | 수십 | 과반 | >0.5 | TC=논리사이클 1:1 매핑 |

### 스윕 시험 (sig_ratio < 0.5 → Phase A-2 로직)

| 시험 유형 | TC 수 | 유의 TC | sig_ratio | 스윕 병합 | 결과 |
|-----------|-------|---------|-----------|----------|------|
| ⑥ GITT 충전 | 30+ | 1~3 | <0.2 | CHG 스윕 + DCHG 스윕 → 1 사이클 | ✓ |
| ⑦ GITT 충방전 | 50+ | 2~4 | <0.1 | (CHG + DCHG) 쌍 반복 → 각 쌍 = 1 사이클 | ✓ |
| ⑧ DCIR | 20+ | 1~2 | <0.1 | CHG 스윕 + DCHG 스윕 → 1 사이클 | ✓ |
| ⑨ 펄스 충전/방전 | 다수 | 수 개 | <0.5 | 스윕 그룹핑 적용 | ✓ |

---

## cycle_map 값 다형성 정리

```
cycle_map = {
    # 일반 시험 (Phase A-1) — int 값
    1: 3,           # 논리사이클 1 → TotlCycle 3
    2: 4,           # 논리사이클 2 → TotlCycle 4
    ...

    # 스윕 시험 (Phase A-2) — tuple 값
    1: (1, 15),     # 논리사이클 1 → TC 1~15 (충전 스윕 + 방전 스윕 병합)
    2: (16, 16),    # 논리사이클 2 → TC 16 (유의 TC, 단일 RPT)
    ...
}
```

- `int` → 단일 TotlCycle (`_unified_pne_load_raw`에서 직접 사용)
- `tuple[int, int]` → 스윕 범위 (`range(start, end+1)` 확장 후 전체 TC 로드)
- 소비자(`_unified_pne_load_raw`)에서 `isinstance(val, tuple)` 분기 처리

---

## 영향 범위

| 함수 | 변경 유형 |
|------|----------|
| `_opposite_dirs()` | **신규** |
| `_pne_build_sweep_cycle_map()` | **신규** |
| `pne_build_cycle_map()` | 내부 로직 확장 (자동 감지 + 스윕 분기) |
| `_unified_pne_load_raw()` | tuple 분기 로직 추가 |
| `_unified_toyo_load_raw()` | 변경 없음 (Toyo는 해당 사항 없음) |
| `unified_profile_core()` | 변경 없음 (cycle_map 전달만) |

## 하위 호환성

- **일반 시험(sig_ratio ≥ 0.5)**: Phase A-1과 동일한 `int` 값 cycle_map 생성 → 기존 동작 완전 유지
- **cycle_map=None**: 여전히 자동 생성 → 기존 호출 코드 변경 불필요
- **빈 dict `{}`**: 여전히 직접 접근 폴백 → 기존 동작 유지
- Toyo 사이클러: 영향 없음 (`toyo_build_cycle_map`은 변경 없음)

## Phase A-1 변경로그 참조

이전 Phase A-1 구현 상세: `260404_impl_logical_cycle_phase_a.md`
