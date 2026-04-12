# 260404 버그수정 — GITT/DCIR 스윕 시험 cycle_map 논리사이클 매핑 수정

## 배경 / 목적

GITT 반셀 시험 데이터(예: `M2-SDI-open-ca-half-14pi-GITT-0.1C-T23`)에서
프로필 분석 시 "cycle에 2 입력하고 분석했더니 첫 스텝 구간만 plot된다"는 문제가 발생했다.

원인 분석 결과, 논리사이클 매핑(Phase A) 로직이 이 유형의 데이터를 올바르게 처리하지 못했다.

---

## 근본 원인 분석

### GITT 반셀 데이터 구조

| TC 범위 | 방향 | 내용 | 용량(μAh) |
|---------|------|------|----------|
| TC 1 | CHG | 초기 만충전 | 3,807,178 |
| TC 2~122 | DCHG | 방전 GITT 펄스 (121개) | ~41,780 각 |
| TC 123~181 | CHG | 충전 GITT 펄스 (59개) | ~41,772 각 |

**핵심 특성**: 모든 TC가 단방향(CHG only 또는 DCHG only), 충방전 쌍 없음.

### 기존 코드 동작 흐름

```
1. sig_ratio 계산
   - threshold = 187 × 1000 × 0.2 = 37,400 μAh
   - 모든 TC 용량(41,780) > threshold → sig_ratio = 1.0

2. sig_ratio ≥ 0.5 → Phase A-1 (일반 시험) 경로 진입

3. Phase A-1: 충방전 쌍이 모두 있는 TC만 유효
   - 이 데이터에서는 모든 TC가 단방향 → 유효 TC = 0개

4. cycle_map = {} (빈 dict) 반환

5. unified_profile_core에서:
   - cycle_map if cycle_map else None → {} 은 falsy → None 변환
   - cycle_map=None → 물리 TC 직접 접근
   - 사용자가 "2" 입력 → TC 2 하나만 로드 (GITT 펄스 1개)
```

---

## 변경 내용

### 1. `pne_build_cycle_map()` — has_both_ratio 조건 추가

시험 유형 판별에 **has_both_ratio** (충방전 쌍 존재 비율) 조건을 추가.

**Before:**
```python
if sig_ratio >= 0.5:
    # 일반 시험 경로
```

**After:**
```python
# has_both 비율: 충방전 쌍이 모두 있는 TC의 비율
has_both_mask = (chg_s > 0) & (dchg_s > 0)
has_both_ratio = float(has_both_mask.sum()) / len(all_tcs)

if sig_ratio >= 0.5 and has_both_ratio >= 0.3:
    # 일반 시험 경로 (충방전 쌍이 있는 TC가 30% 이상)
else:
    # 스윕 시험 경로 (단방향 펄스 시험)
```

**판별 기준 변경:**

| 조건 | Before | After |
|------|--------|-------|
| 일반 시험 | `sig_ratio ≥ 0.5` | `sig_ratio ≥ 0.5 AND has_both_ratio ≥ 0.3` |
| 스윕 시험 | `sig_ratio < 0.5` | `sig_ratio < 0.5 OR has_both_ratio < 0.3` |

### 2. `_pne_build_sweep_cycle_map()` — has_both=False 유의 TC 포함

**Before:**
```python
if seg['kind'] == 'sig':
    # 유의 TC: 충방전 쌍이 있어야 유효
    if seg.get('has_both', False):
        ln += 1
        cycle_map[ln] = int(tcs[0])
```

**After:**
```python
if seg['kind'] == 'sig':
    # 유의 TC: 충방전 쌍 유무와 무관하게 논리사이클로 포함
    # (초기 충전, 단독 RPT 등 has_both=False인 유의 TC도 유효한 이벤트)
    ln += 1
    cycle_map[ln] = int(tcs[0])
```

### 3. `unified_profile_core/batch` — empty dict falsy 체크 제거

**Before:**
```python
raw = _unified_pne_load_raw(
    raw_file_path, cycle_start, cycle_end,
    cycle_map=cycle_map if cycle_map else None,
)
```

**After:**
```python
raw = _unified_pne_load_raw(
    raw_file_path, cycle_start, cycle_end,
    cycle_map=cycle_map,
)
```

`{}` (빈 dict)가 `None`으로 변환되지 않도록 수정. 3곳 수정:
- `unified_profile_core` PNE 경로 (line ~1340)
- `unified_profile_core` Toyo 경로 (line ~1351)
- `unified_profile_batch` PNE overlay (line ~1682)

---

## 수정 후 동작

### 스윕 시험 → 방향 기반 그룹핑 매핑

```
1. sig_ratio < 0.5 OR has_both_ratio < 0.3 → 스윕 시험 판정
2. _pne_build_sweep_cycle_map() 호출: 방향 기반 그룹핑
   - 유의 TC: 개별 논리사이클 (초기 충전, RPT 등)
   - 비유의 TC: 연속 동일 방향 → 1개 스윕 (tuple 범위)
   - 인접 반대 방향 스윕 쌍 → 1 논리사이클로 병합
3. GITT ca 예시: {1: TC1(초기충전), 2: (TC2, TC181)(DCHG+CHG 스윕)}
   사용자가 "2" 입력 → TC 2~181 전체 GITT 펄스 데이터 로드 ✓
```

**논리사이클 정의 원칙**: 충전 스윕 + 방전 스윕 = 1 논리사이클.
UI에서 보이는 사이클은 논리사이클이며, 내부에서는 TotlCycle 범위로 변환하여 데이터 로딩.

### `_quick_max_cycle` → 논리사이클 수 반환

경로 테이블 col 4에 TotlCycle 최대값 대신 `len(cycle_map)` 반환.
PNE: `pne_build_cycle_map()` 호출 → `len(cycle_map)` (실패 시 SaveEndData 폴백)

---

## 검증 (예측값)

| 데이터 | 용량(mAh) | TC수 | 논리사이클 | 유형 |
|--------|-----------|------|-----------|------|
| GITT 반셀 ca | 4 | 181 | **~2** | 스윕 그룹핑 (초기충전 + DCHG/CHG 스윕) |
| GITT 반셀 an | 4 | 194 | **~2~3** | 스윕 그룹핑 |
| Gen5+B DCIR | 2610 | 95 | **소수** | 유의 TC + 스윕 그룹 |
| Q8 RT 수명 | 2335 | 760 | **758** | 일반 (쌍 없는 2TC 제외) ✓ |
| Gen5P 보관 | 5000 | 6 | **4** | 일반 (쌍 없는 2TC 제외) ✓ |
| Cosmx 율별 | 5075 | 23 | **22** | 일반 (쌍 없는 1TC 제외) ✓ |

> 스윕 시험의 정확한 논리사이클 수는 TC별 용량/방향 분포에 따라 달라짐.
> 앱 재시작 후 경로 테이블에서 확인 필요.

---

## 영향 범위

| 함수 | 변경 유형 |
|------|----------|
| `pne_build_cycle_map()` | has_both_ratio 조건 추가 + 스윕 시 `_pne_build_sweep_cycle_map` 호출 |
| `_pne_build_sweep_cycle_map()` | has_both=False 유의 TC 포함 (스윕 경로에서 호출) |
| `_quick_max_cycle()` | PNE에서 cycle_map 기반 논리사이클 수 반환 |
| `unified_profile_core()` | cycle_map falsy 체크 제거 (3곳) |

## 하위 호환성

- 일반 수명시험: `sig_ratio ≥ 0.5 AND has_both_ratio ≥ 0.3` → Phase A-1 경로 유지
- 스윕 시험 (GITT/DCIR 등): **방향 기반 스윕 그룹핑** → 충전+방전 스윕 = 1 논리사이클
- `_unified_pne_load_raw`: tuple 범위 매핑 이미 구현됨 (line 715-720)

## Phase A 변경로그 참조

- Phase A-1: `260404_impl_logical_cycle_phase_a.md`
- Phase A-2: `260404_impl_logical_cycle_phase_a2_sweep.md`
- Phase B: `260404_impl_logical_cycle_phase_b_label.md`
