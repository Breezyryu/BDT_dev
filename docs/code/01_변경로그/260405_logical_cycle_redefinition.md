# 논리사이클 재정의 — 충전→방전 사이클 + 충전 전용 사이클 지원

**날짜**: 2026-04-05
**대상 파일**: `DataTool_dev/DataTool_optRCD_proto_.py`
**카테고리**: 리팩토링 / 로직 변경

---

## 배경 / 목적

기존 논리사이클 정의는 **방전이 있는 사이클만** 인식했다.

- 충전→방전 쌍이 있어야 논리사이클로 매핑됨
- 화성(formation) 충전 등 **충전 전용 사이클은 누락**
- 방전 후 휴지(rest) 구간이 **사이클 범위에서 제외**되어 프로필 분석 시 데이터 손실 가능

**새 정의**:
1. **충전 → 방전 → 휴지(방전 후)** = 1 논리사이클 (휴지 포함)
2. **충전 전용** (방전 없음) = 독립 논리사이클
3. Toyo + PNE 모두 적용, 모든 시험 유형 (일반/GITT/스윕) 적용

---

## 변경 내역

### 1. `toyo_build_cycle_map()` (line ~2633)

**Before**: 유효 방전 그룹만 순회, 직전 충전 포함하여 `(charge_OriMin, discharge_OriMax)` 매핑

**After**:
- **Pass 1**: 방전 기반 사이클 — 직전 충전 + 방전 + **방전 후 연속 비충전/비방전 그룹(휴지)** 포함
- **Pass 2**: 충전 전용 사이클 — 방전 없이 충전만 있는 그룹을 독립 논리사이클로 추가
- 시작 파일 기준 정렬 → 논리사이클 번호 재부여

```python
# Pass 1: 방전 기반 (충전 + 방전 + 방전 후 휴지)
# Pass 2: 충전 전용 (used_indices에 없는 충전 그룹)
events.sort(key=lambda x: x[0])  # 시작 파일 기준 정렬
```

### 2. `toyo_cycle_data()` (line ~2558, ~2591)

**Before**: `dropna(subset=['Dchg'])` → 방전 없는 행 모두 제거

**After**:
- `dropna(subset=['Dchg', 'Chg'], how='all')` → Dchg 또는 Chg 중 하나라도 있으면 유지
- cycle_map 적용 후, **충전 전용 사이클을 df.NewData에 추가**
  - cycle_map에는 있지만 df.NewData에 없는 논리사이클 = 충전 전용
  - chgdata에서 해당 범위의 충전 데이터를 조회하여 행 추가
  - Dchg=NaN, Chg=충전용량비, RndV=OCV, 나머지=NaN

### 3. `pne_build_cycle_map()` — 일반 시험 분기 (line ~2933)

**Before**: `valid_totl_cycles = dchg_cap.dropna().index.intersection(chg_cap.dropna().index)` → 충방전 쌍만

**After**:
- `valid_dchg_tcs`: 충방전 쌍 있는 TC (기존)
- `chg_only_tcs`: 충전만 있는 TC (방전 없는 TC)
- `valid_totl_cycles = sorted(valid_dchg_tcs | chg_only_tcs)` → 합집합

### 4. `_process_pne_cycleraw()` (line ~5305)

**Before**: `dropna(subset=['Dchg', 'Chg'], how='any')` → Dchg 또는 Chg 중 하나라도 NaN이면 제거

**After**: `dropna(subset=['Dchg', 'Chg'], how='all')` → 둘 다 NaN일 때만 제거

### 5. `_pne_build_sweep_cycle_map()` — 2.5단계 "방전 마무리 흡수" 추가

**Before**: 유의 TC 직후의 비유의 DCHG 스윕이 별도 세그먼트로 분류되어 후속 CHG 스윕과 잘못 병합됨

**After**: **2.5단계 추가** — 유의 TC(has_both=True) 직후의 DCHG 스윕을 유의 TC에 흡수

```
예: [sig TC3(C+D)] + [sweep DCHG TC4] → TC3에 TC4 흡수 → cycle_map[3] = (3, 4)
```

이 변경으로 흡수 후 CHG 스윕과 DCHG 스윕이 인접하게 되어 올바른 쌍 병합 가능:
- 흡수 전: sig → **DCHG sweep** → CHG sweep → DCHG sweep (DCHG+CHG 잘못 병합)
- 흡수 후: sig(+DCHG) → **CHG sweep** → DCHG sweep (CHG+DCHG 올바른 병합)

또한 4단계에서 유의 TC가 여러 TotlCycle을 포함할 수 있도록 `(min, max)` 튜플 변환 추가

---

## 영향 범위

| 구성 요소 | 영향 |
|-----------|------|
| 사이클 데이터 탭 — 사이클 분석 | cycle_map 변경 → 논리사이클 번호 체계 변경 |
| 사이클 데이터 탭 — 프로필 분석 | 방전 후 휴지가 사이클 범위에 포함됨 |
| 세트 결과 탭 | df.NewData에 충전 전용 행 추가 (Dchg=NaN) |
| 수명 예측 탭 | df.NewData 구조 변경 — Dchg=NaN 행 존재 가능 |
| dVdQ 분석 | cycle_map 범위 변경 (프로필 데이터 범위 확장) |

**주의사항**: 충전 전용 사이클(Dchg=NaN)이 df.NewData에 포함되므로, Dchg 기반 그래프/계산에서 NaN 처리가 필요할 수 있음.
