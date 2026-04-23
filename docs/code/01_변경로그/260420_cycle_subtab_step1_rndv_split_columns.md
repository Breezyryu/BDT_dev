# 사이클 서브탭 확장 Step 1 — RndV 충/방전 Rest 분리 파생 컬럼

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
관련 계획: `.claude/plans/4-1-1-proud-ladybug.md`

## 배경

사이클 분석 결과를 **서브탭 2개(요약/상세)** 로 확장하기 위한 4-Step 작업의 **Step 1 (데이터 레이어만)**.

UI 변경 없이 `df.NewData` 에 두 개의 신규 파생 컬럼이 **항상** 생성된다:

- `RndV_chg_rest` : 충전 직후 Rest 종료 전압 (만충 OCV ≈ 4.05–4.25V)
- `RndV_dchg_rest` : 방전 직후 Rest 종료 전압 (만방 OCV ≈ 2.80–3.30V)

기존 `RndV` 컬럼은 `Condition==3` 전체 Ocv 의 `min` 으로 계산돼 충전/방전 Rest 가 섞여 있었음 (사실상 방전 후 OCV 가 선택). 분리하면 만충/만방 OCV 드리프트를 독립적으로 트래킹 가능 → 수명 분석에서 필수.

## 변경 내용

### 1. 신규 유틸 함수 `_ensure_rndv_split_columns()` (≈L898 직후)

```python
def _ensure_rndv_split_columns(nd, cycleraw, cycle_map=None, *,
                               ocv_scale=1.0,
                               chg_cond=1, dchg_cond=2, rest_cond=3):
    """df.NewData 에 RndV_chg_rest / RndV_dchg_rest 컬럼 생성."""
```

알고리즘:
1. **기본**: 두 컬럼을 NaN 으로 보장 (컬럼 누락 방지)
2. **cycle_map 기반** (PNE 주 경로): `chg_rest`/`dchg_rest` TC 목록으로 Cycleraw 필터 → `groupby(TotlCycle)['Ocv'].last() * ocv_scale` → OriCyc 매핑
3. **폴백** (cycle_map 없거나 결과 비어있는 경우): `Condition` 전이 기반
   - `(cur==rest) & (prev==chg)` → chg_rest
   - `(cur==rest) & (prev==dchg)` → dchg_rest

파라미터 `ocv_scale`:
- PNE: `1 / 1_000_000` (μV → V)
- Toyo: `1.0` (이미 V 단위)

### 2. PNE 호출 — `_process_pne_cycleraw` (L9418 직후)

```python
if hasattr(df, 'NewData'):
    _ensure_dcir_columns(df.NewData)
# 신규 추가
if hasattr(df, 'NewData'):
    _ensure_rndv_split_columns(
        df.NewData, Cycleraw, cycle_map, ocv_scale=1.0 / 1_000_000)
```

호출 시점은 dropna 전 → `OriCyc` 매핑이 온전히 작동.

### 3. PNE Sweep 집계 확장 (L9446-9453)

`_agg` dict 에 두 컬럼 추가:
```python
_agg = {
    ..., 'OriCyc': 'last',
    'RndV_chg_rest': 'first',   # Sweep 에서는 SOC 별 의미 혼재 → 'first'
    'RndV_dchg_rest': 'first',
}
```

필수 컬럼 보장 for 루프 (L9470) 도 확장:
```python
for _req in ['dcir', 'dcir2', ..., 'RndV_chg_rest', 'RndV_dchg_rest']:
    if _req not in _grouped.columns:
        _grouped[_req] = np.nan
```

### 4. Toyo 호출 — `toyo_cycle_data` (L4181 직후)

```python
_ensure_dcir_columns(df.NewData)
# 신규 추가
if 'RndV' in df.NewData.columns:
    df.NewData['RndV_chg_rest'] = df.NewData['RndV']   # 기존 RndV = 충전 후 OCV
_ensure_rndv_split_columns(
    df.NewData, Cycleraw, cycle_map=None, ocv_scale=1.0)
```

Toyo 는 기존 `RndV` 가 이미 `chgdata["Ocv"]` (충전 직후 OCV) → 바로 복사. `RndV_dchg_rest` 는 유틸의 폴백(전이 기반)으로 추출. Toyo `Condition` 값 매핑 (1/2/3) 가 PNE 와 동일하다고 가정하고 폴백 작동. 데이터 부재 시 NaN 으로 안전 fallback.

## 동작 매트릭스

| 경로 / 모드 | RndV_chg_rest | RndV_dchg_rest | 비고 |
|---|---|---|---|
| PNE General (1 논리 = 1 TC) | cycle_map chg_rest TC 기반 | cycle_map dchg_rest TC 기반 | 가장 정확 |
| PNE Sweep (GITT/DCIR) | Sweep agg `first` | Sweep agg `first` | 대표 TC 값 |
| PNE cycle_map 없음 | 폴백 (전이 기반) | 폴백 (전이 기반) | 드문 경우 |
| Toyo | `RndV` 복사 (충전 OCV) | 폴백 (전이 기반) 또는 NaN | Toyo Condition 값 확인 필요 |
| 데이터 부족 | NaN | NaN | 하류 코드 `dropna().empty` 가드 안전 |

## 영향 범위

- 신규 컬럼 2개 **항상** 추가 (값 없으면 NaN)
- UI/그래프 코드 **전혀 변경 없음** → 탭1 동작 완전 보존 (회귀 위험 0)
- Excel 저장(`_save_cycle_excel_data`) 은 이번 Step 범위 외. `nd.columns` 를 반복하지 않고 특정 컬럼만 추출하므로 신규 컬럼이 자동으로 시트에 추가되지 않음 → Step 4 에서 명시적으로 추가 예정
- `_agg` / 필수 컬럼 보장 루프 확장으로 Sweep 집계 후에도 컬럼 보존

## 검증 포인트

- [ ] 일반 PNE 수명 데이터 로드 → `df.NewData.columns` 에 `RndV_chg_rest`, `RndV_dchg_rest` 존재
- [ ] `df.NewData['RndV_chg_rest'].describe()` 값이 **4.05–4.25 V** 범위 (만충 OCV)
- [ ] `df.NewData['RndV_dchg_rest'].describe()` 값이 **2.80–3.30 V** 범위 (만방 OCV)
- [ ] 기존 탭1 2×3 그래프 시각적 완전 동일 (회귀 없음)
- [ ] Sweep (GITT/DCIR) 데이터에서도 두 컬럼이 존재 (first 값, 또는 NaN)
- [ ] Toyo 데이터에서 `RndV_chg_rest ≈ RndV` (복사 정상) 확인
- [ ] Toyo 데이터에서 `RndV_dchg_rest` 가 폴백으로 값 또는 NaN (에러 없음)
- [ ] `saveok` 체크 후 기존 엑셀 시트 구조 불변 (신규 컬럼은 Step 4 에서 추가)

## 다음 단계

- **Step 2**: 외부 탭 내부에 `QTabWidget` 중첩 도입, tab1 은 "요약" 에 이동 (placeholder)
- **Step 3**: `graph_output_cycle_tab2()` 신규 함수로 "상세" 탭 6개 그래프 구현
- **Step 4**: `_save_cycle_excel_data` 에 `Rest End Chg` / `Rest End Dchg` 시트 추가

## 관련 계획

`.claude/plans/4-1-1-proud-ladybug.md` — 4-Step 전체 설계 문서
