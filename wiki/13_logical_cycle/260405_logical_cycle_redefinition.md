# 논리사이클 재정의 — 충전→방전 사이클 + 충전 전용 사이클 지원

> 📎 2026-04-21: `260404_impl_logical_cycle_in_cycle_data.md` 병합 (§cycle_data 파이프라인 통합)

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

---

## cycle_data 파이프라인 통합 (260404)

### 배경 / 목적

기존에 `pne_build_cycle_map()`과 `toyo_build_cycle_map()`으로 논리사이클 매핑(cycle_map)이 구현되어 있었으나,
**프로필 로딩**과 **UI 표시**에서만 사용되고 있었다. 핵심 사이클 데이터 처리 함수인
`pne_cycle_data()`와 `toyo_cycle_data()`는 cycle_map을 사용하지 않아, `NewData['Cycle']` 컬럼이
단순 순번(1, 2, 3...)으로만 부여되었다.

특히 **스윕 시험**(GITT, DCIR 등)에서는 다수의 물리 TotlCycle이 하나의 논리사이클로 그룹핑되어야 하므로,
기존의 TotlCycle 단위 처리로는 의미 있는 사이클 요약 데이터를 생성할 수 없었다.

### Before / After 비교

**Before**

```
pne_cycle_data() / toyo_cycle_data()
  → pivot by TotlCycle
  → dropna(Dchg, Chg)
  → Cycle = 순번 1, 2, 3, ...    (물리 TC와 무관한 재번호)
  → OriCyc = 물리 TotlCycle
  → cycle_map 없음
```

**After**

```
pne_cycle_data() / toyo_cycle_data()
  → pne_build_cycle_map() / toyo_build_cycle_map() 호출 → cycle_map 생성
  → pivot by TotlCycle (기존과 동일)
  → dropna(Dchg, Chg)
  → cycle_map 기반 Cycle 번호 부여:
    ├─ 일반 시험: OriCyc → cycle_map 역매핑 → 논리사이클 번호
    └─ 스윕 시험: 같은 논리사이클의 행을 groupby 집계
  → OriCyc = 대표 물리 TotlCycle (유지)
  → df.cycle_map = {...} 저장
```

### 변경 상세

#### 1. `_process_pne_cycleraw()` — cycle_map 파라미터 추가

```python
def _process_pne_cycleraw(
    Cycleraw, df, raw_file_path, mincapacity,
    chkir, chkir2, mkdcir,
    cycle_map=None,  # ← 추가
) -> None:
```

dropna 이후 Cycle 번호 부여 로직:

- **cycle_map 있음 + 스윕**: `_tc_to_ln` 역매핑 → groupby(논리사이클).agg() → Eff/Eff2 재계산
- **cycle_map 있음 + 일반**: `_tc_to_ln` 역매핑 → Cycle = 논리사이클 번호
- **cycle_map 없음**: 기존 방식 (순번 1, 2, 3, ...)

#### 2. `pne_cycle_data()` — cycle_map 생성 및 전달

```python
_cycle_map, _ = pne_build_cycle_map(raw_file_path, mincapacity, ini_crate)
_process_pne_cycleraw(..., cycle_map=_cycle_map)
df.cycle_map = _cycle_map if _cycle_map else {}
```

#### 3. `toyo_cycle_data()` — cycle_map 생성 및 저장

```python
_cycle_map, _ = toyo_build_cycle_map(raw_file_path, mincapacity, inirate)
# OriCyc → 논리사이클 역매핑으로 Cycle 번호 부여
df.cycle_map = _cycle_map if _cycle_map else {}
```

#### 4. `unified_cyc_confirm_button()` — 논리사이클 로그 출력

데이터 로딩 완료 후 각 경로별 cycle_map 요약을 콘솔에 출력:
```
논리사이클: path0 [M01Ch001[001]]  일반  758개 논리사이클
```

### 영향 범위 (파이프라인 통합)

| 함수 | 변경 내용 |
|------|----------|
| `_process_pne_cycleraw()` | `cycle_map` 파라미터 추가, Cycle 번호 재정의 로직 변경 |
| `pne_cycle_data()` | cycle_map 생성/전달/저장 |
| `toyo_cycle_data()` | cycle_map 생성/저장, Cycle 번호 재정의 |
| `unified_cyc_confirm_button()` | 논리사이클 로그 출력 추가 |
| `df.NewData['Cycle']` | 순번 → 논리사이클 번호 (cycle_map 있을 때) |
| `df.cycle_map` | 새 속성: 논리사이클 매핑 딕셔너리 |

### 주의사항 (파이프라인 통합)

- **하위 호환성**: cycle_map이 없거나 빈 경우 기존 동작(순번) 유지
- **스윕 집계**: Dchg/Chg은 합산, Eff/Eff2는 집계 후 재계산, DCIR은 평균
- **OriCyc 보존**: 전압 트래킹(ChgVolt, DchgVolt) 등 기존 코드는 OriCyc 기반이므로 영향 없음
- **성능**: `pne_build_cycle_map()`은 SaveEndData 캐시를 사용하므로 추가 I/O 최소화
