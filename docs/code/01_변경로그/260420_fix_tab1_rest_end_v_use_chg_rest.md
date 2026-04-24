# 탭1 1-6 Rest End V 의미 정정 — 충전 후 Rest 종료 (방전 직전) 전압 사용

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`

## 배경

사용자 정정:
> "1-6 Rest End Voltage 컨셉은 **충전 레스트 방전 직전 전압**이다."

Step 3 (커밋 `504aa3a`) 에서 1-6 ax6 에 기존 `RndV` 컬럼을 그대로 사용했으나, `RndV` 는 `pivot_data["Ocv"][3].min()` 계산상 실제로는 **방전 후 Rest 종료 전압 (가장 낮은 OCV ≈ 3.0V)** 을 반환하고 있었다. 사용자 의도는 **충전 후 Rest = 방전 직전 전압 (만충 OCV ≈ 4.1V)**.

또한 스크린샷에서 탭2 2-5 (Charge Rest End V = `RndV_chg_rest`) 플롯이 **전부 비어 있음** → 데이터 누락 진단 필요.

## 변경 내용

### 1. 탭1 1-6 ax6 데이터 소스 변경 (`graph_output_cycle`)

```python
# 1-6 ax6: 충전 후 Rest 종료 = 방전 직전 전압 (만충 OCV ≈ 4.1V)
# RndV_chg_rest (Step 1 신규 파생) 우선, 없거나 전부 NaN 이면 기존 RndV 폴백
_rest_series = None
_rest_ylow, _rest_yhi, _rest_ystep = 4.00, 4.25, 0.05
if ('RndV_chg_rest' in df.NewData.columns
        and not df.NewData.RndV_chg_rest.dropna().empty):
    _rest_series = df.NewData.RndV_chg_rest
elif 'RndV' in df.NewData.columns:
    _rest_series = df.NewData.RndV
    _rest_ylow, _rest_yhi, _rest_ystep = 3.00, 4.00, 0.1
if _rest_series is not None:
    artists.append(graph_cycle(
        _x, _rest_series, ax6,
        _rest_ylow, _rest_yhi, _rest_ystep,
        "Cycle", "Rest End Voltage (V)", temp_lgnd, xscale, color))
```

- 기본: `RndV_chg_rest` (사용자 의도)
- 폴백: 기존 `RndV` (데이터 누락 시 안전망)
- y 범위 자동: chg_rest=4.00–4.25, RndV 폴백=3.00–4.00

### 2. `_ensure_rndv_split_columns` 데이터 누락 진단 로그

함수 말미에 결과가 전부 NaN 인 경우 경고 로그:

```python
if nd['RndV_chg_rest'].dropna().empty:
    _perf_logger.warning(
        '_ensure_rndv_split_columns: RndV_chg_rest 전부 NaN — '
        f'cycle_map entries={len(cycle_map) if cycle_map else 0} '
        f'entry types={_cm_types} '
        f'chg_rest_tcs={len(chg_rest_tcs)} '
        f'rest_rows(Condition=={rest_cond})={len(rest_rows)} '
        f'Condition dist={_cond_dist}')
```

로그 내용:
- `cycle_map entries`: cycle_map 항목 개수
- `entry types`: cycle_map value 의 타입 집합 (`dict` / `int` 혼재 여부)
- `chg_rest_tcs`: cycle_map 에서 수집한 충전후 Rest TC 개수
- `rest_rows`: Cycleraw 에서 Condition==3 행 개수
- `Condition dist`: Condition 값 분포 (StepType 1/2/3/8 등 개수)

→ 사용자 재실행 시 어느 단계에서 실패하는지 파악:
1. cycle_map entries=0 → 캐시 실패
2. entry types={'int'} → General 모드 1:1 매핑이라 dict 분기 진입 못 함 → 폴백 의존
3. chg_rest_tcs=0 + rest_rows=0 → Condition==3 데이터 부재
4. rest_rows 있는데 chg_rest_tcs=0 → 폴백 전이 로직 실패

## 탭별 최종 매핑 (Step 3 이후 정정)

### 탭 1
| 위치 | 지표 | 컬럼 | 의미 |
|---|---|---|---|
| 1-6 | Rest End V | **`RndV_chg_rest` (폴백: `RndV`)** | **충전 후 Rest = 방전 직전 V (만충 OCV)** |

### 탭 2
| 위치 | 지표 | 컬럼 | 의미 |
|---|---|---|---|
| 2-5 | Charge Rest End V | `RndV_chg_rest` | 충전 후 Rest (1-6 과 동일 데이터, 참조) |
| 2-6 | Discharge Rest End V | `RndV` | 방전 후 Rest (pivot min 방식, 실제 값 ≈ 3.0V) |

## 영향 범위

- `graph_output_cycle` 함수만 수정 (탭1)
- 탭2 (`graph_output_cycle_tab2`) 는 불변
- `_ensure_rndv_split_columns` 에 로그만 추가 (로직 불변)
- 회귀 없음: `RndV_chg_rest` 비면 `RndV` 로 자동 폴백 → 최소한 기존 Step 3 동작 유지

## 검증 포인트

- [ ] `RndV_chg_rest` 정상 생성 시 탭1 ax6 가 4.0–4.25V 영역의 scatter 점 표시
- [ ] `RndV_chg_rest` 누락 시 로그에 원인 경고 출력, ax6 는 기존 `RndV` (3.0V 근처) 폴백
- [ ] 탭2 2-5 / 2-6 동작 불변
- [ ] Toyo 데이터에서 `RndV_chg_rest ≈ RndV` (Toyo 는 복사됨) 인 경우 ax6 4.0–4.25 범위 부적합 → 폴백 조건 검토 필요 (후속)

## 다음 단계

- 사용자 재실행 → 진단 로그 확인 → 필요 시 `_ensure_rndv_split_columns` 폴백 로직 강화
- 연결처리 "첫 그룹만 plot" 이슈는 별도 진단 (후속 커밋)
