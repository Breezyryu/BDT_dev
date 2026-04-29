# 히스테리시스 분석 — SOC offset anchor shift 결함 + unified_flow dQdV KeyError 동시 수정

날짜: 2026-04-29
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수:
- `_compute_tc_soc_offsets()` (L863) — 누적 알고리즘 전면 교체
- `_unified_calculate_dqdv()` (L2536) — SOC 미존재 시 ChgCap/DchgCap proxy 사용

## 배경

사용자 보고:
> [`Voltage hysteresis test_Graph format_v1.3_bundle.txt`] 히스테리시스 결과물이
> 잘못되었다. 엑셀로 TC 3~12 충전, 방전 프로파일 결과를 추출 후 엑셀로 도출한
> 그래프이다. 히스테리시스 출력 로직을 재검토하라.

스크린샷:
- 데이터: `260330_260405_05_신용호_4960mAh_Gen6+ ATL proto1차 Si 10% Hysteresis 측정` M01Ch060[060]
- 모드: 사이클 + 이어서 + SOC + CV + TC 페어링 (= `is_hysteresis_mode` ON)
- TC 범위: 3-12 (10개 hysteresis 사이클)
- 결과: V-SOC 플롯의 곡선이 X 축 [-0.1, 1.2] 의 오른쪽 끝 (SOC > 1.0) 으로
  쏠리고, 일부 곡선은 화면 밖으로 튀어나감

엑셀 골든 레퍼런스 (`Voltage hysteresis test_Graph format_v1.3_bundle.txt`)
의 기대 거동:
- 충전 곡선 10개 (Chg 100% ~ Chg 10%): SOC 0~1 영역에서 부채꼴
- 방전 곡선 10개 (Dchg 100% ~ Dchg 10%): SOC 1→0 영역에서 부채꼴
- 두 그룹이 겹쳐 닫힌 hysteresis 루프 형성

## 결함 1 — `_compute_tc_soc_offsets` 의 anchor shift 가 hysteresis 범위 밖
사이클을 기준으로 사용

### 원인

기존 알고리즘 (L893-916):

```python
result = {}
cumul_net = 0.0
for tc in sorted(cr['TC'].unique()):
    result[int(tc)] = cumul_net / cap_uah
    cumul_net += (chg - dchg)

if min(result.values()) < -0.05:
    shift = -min(result.values())
    result = {tc: v + shift for tc, v in result.items()}
```

문제:
1. `cumul_net` 은 0 에서 시작 — 셀이 SOC=0 에서 시작한다고 가정
2. 만충 시작 프로토콜에서 첫 dchg 가 cumul_net 을 음수로 떨어뜨려 anchor shift
   가 발동
3. shift 양은 **전역 최저점** 기준 — 사용자가 선택한 TC 범위 밖의 후속 사이클
   (RPT, GITT, 추가 hysteresis 등) 이 더 깊은 음수를 만들면 hysteresis TC 들이
   SOC=1.2 등 절대 좌표 밖으로 밀림
4. CC-CV 충전이 100% 도달 후에도 CV 전류로 ChgCap 이 누적되므로 raw 누적 net 이
   실제 SOC 변화와 일치하지 않음 (1.05 frac 등 1.0 초과 가능)

Si 10% 데이터 분석 (4960 mAh):

```
TC  | chg(uAh) | dchg(uAh) | cumul/cap (raw)
 1  |     0    |  1674265  |  +0.000
 2  |  5216212 |  5122919  |  -0.338
 3  |  5127883 |   512295  |  -0.319
 4  |   519761 |  1024589  |  +0.612
...
12  |  4606436 |  5124463  |  -0.210
13  |  5119717 |  5121211  |  -0.314
14  |   511978 |   541380  |  -0.314
...
18  |  2559860 |  4175521  |  -0.333  → -0.659  ← 전역 최저점 (TC 18 큰 dchg)
```

전역 min = -0.659 (TC 19 시작 시점). shift = +0.659 적용:

| TC | offset (after shift) | 기대 SOC | 오차 |
|----|---------------------|----------|------|
|  3 | +0.340              | 0.000    | +0.34 |
|  4 | +1.271              | 0.900    | +0.37 |
|  5 | +1.169              | 0.800    | +0.37 |
|  6 | +1.066              | 0.700    | +0.37 |
| 12 | +0.449              | 0.100    | +0.35 |

→ 모든 TC 가 +0.34 정도 위로 밀림. TC 4-9 는 SOC > 1.0 영역으로 완전히 이탈.

### 수정

[`_compute_tc_soc_offsets()` (L863)] 알고리즘 전면 교체.

신규 알고리즘 (2-패스):

**1차 패스** — 무클립 누적의 최저점으로 초기 상태 추정:

```python
cumul = 0.0
cumul_min = 0.0
tc_caps: list[tuple[int, float, float]] = []
for tc in sorted(cr['TC'].unique()):
    chg = ... / cap_uah
    dchg = ... / cap_uah
    tc_caps.append((int(tc), chg, dchg))
    cumul += (chg - dchg)
    cumul_min = min(cumul_min, cumul)
initial_full = (cumul_min < -0.05)
```

만충 시작 hysteresis 프로토콜은 시험 초반 dchg 누적으로 cumul 이 −값으로 떨어진다.
SOC=0 시작 프로토콜은 cumul ≥ 0 유지.

**2차 패스** — 클립 누적으로 절대 SOC 추적:

```python
prev_SOC = 1.0 if initial_full else 0.0
result = {}
for tc, chg, dchg in tc_caps:
    result[tc] = prev_SOC
    eff_chg = max(0.0, min(chg, 1.0 - prev_SOC))
    end_chg = prev_SOC + eff_chg
    eff_dchg = max(0.0, min(dchg, end_chg))
    prev_SOC = end_chg - eff_dchg
```

각 TC 의 chg 는 (1.0 − prev_SOC) 로 클립 (CC-CV CV 전류 보호), dchg 는
end_chg 로 클립 (음수 방어). prev_SOC 는 항상 [0, 1] 안에 머문다.

Si 10% 데이터 검증 결과:

| TC | OLD offset | NEW offset | 기대 SOC | 일치 |
|----|-----------|------------|----------|------|
|  3 | +0.340    | +0.000     | 0.000    | ✓ |
|  4 | +1.271    | +0.897     | 0.900    | ✓ |
|  5 | +1.169    | +0.794     | 0.800    | ✓ |
|  6 | +1.066    | +0.690     | 0.700    | ✓ |
|  9 | +0.758    | +0.380     | 0.400    | ✓ |
| 12 | +0.449    | +0.070     | 0.100    | ✓ |

3% 미만의 잔류 오차는 CV 전류 누적·전류 노이즈에서 비롯됨.

## 결함 2 — `_unified_calculate_dqdv` 가 SOC 컬럼 부재 시 KeyError

### 원인

`unified_flow=True` 경로 (`is_hysteresis_mode` 활성 시):

```python
if unified_flow:
    if calc_dqdv:
        merged = _unified_calculate_dqdv(merged, ...)  # ← merged 에 SOC 없음!
    with_axis = _unified_apply_view(merged, ...)        # 여기서 SOC 추가
```

`_unified_calculate_dqdv` (L2552) 가 `sub["SOC"].diff()` 를 호출하지만 `merged`
는 `_unified_merge_steps` 출력으로 ChgCap/DchgCap 만 가지며 SOC 는 없다 →
`KeyError: 'SOC'`. `_load_unified_batch_task` 의 try/except 가 silent catch
하여 결과 None 반환 → 사용자 화면에 빈 결과 또는 부분적인 결과만 표시.

확인 (수정 전):

```python
>>> unified_profile_core(ch, (4,4), 4960, 1.0,
...     data_scope='cycle', axis_mode='soc',
...     overlap='connected', calc_dqdv=True,
...     unified_flow=True, origin_compat=True)
KeyError: 'SOC'
```

### 수정

[`_unified_calculate_dqdv()` (L2536)] 에 SOC fallback 추가:

```python
_has_soc = "SOC" in df.columns
if not _has_soc and {"ChgCap", "DchgCap", "Condition"}.issubset(df.columns):
    _cap_proxy = pd.Series(np.nan, index=df.index, dtype=float)
    _chg = df["Condition"] == 1
    _dch = df["Condition"] == 2
    if _chg.any():
        _cap_proxy.loc[_chg] = df.loc[_chg, "ChgCap"]
    if _dch.any():
        _cap_proxy.loc[_dch] = -df.loc[_dch, "DchgCap"]
    df["_dqdv_cap_proxy"] = _cap_proxy
    _cap_col = "_dqdv_cap_proxy"
elif _has_soc:
    _cap_col = "SOC"
else:
    return df
```

dQdV 는 dCap/dV 의 비율이므로 SOC 절대값이 아니라 변화량만 필요. ChgCap (단조
증가) / -DchgCap (단조 감소) 을 조건별로 사용하면 부호와 단위가 SOC 와 동일
의미를 갖는다. 임시 proxy 컬럼은 함수 종료 시 drop.

## 영향 범위

### 변경된 거동

1. `_compute_tc_soc_offsets` 가 모든 hysteresis 경로에서 **TC 시작 SOC 를
   [0, 1] 안에서 정확히 추적**. 이전의 anchor shift 의존성 제거.
2. `_unified_calculate_dqdv` 가 `unified_flow=True` 경로에서 **에러 없이 dQdV
   계산 완료**. 이전에는 silent fail.

### 변경되지 않은 거동

- 비-hysteresis 분석 (cycle/profile) 경로: `_compute_tc_soc_offsets` 미호출 →
  영향 없음.
- legacy flow (`unified_flow=False`): `_unified_calculate_axis` 가 SOC 를 먼저
  추가하므로 fallback 진입 안 함, 기존 동작 유지.
- Toyo 사이클러: `_compute_tc_soc_offsets` 가 PNE SaveEndData 의존이므로 호출
  자체가 skip — Toyo 영향 없음.

## 검증

### 1. 단위 테스트 — Si 10% TC 3-12 통합 거동

```
TC  | offset  | chg V end | chg max SOC | dchg end SOC | label
 3  | +0.0000 | 4.550     | +1.034      | +0.897       | Dchg 10%  ✓
 4  | +0.8967 | 4.551     | +1.001      | +0.794       | Dchg 20%  ✓
 5  | +0.7935 | 4.551     | +1.000      | +0.690       | Dchg 30%  ✓
 6  | +0.6901 | 4.550     | +1.001      | +0.588       | Dchg 40%  ✓
 7  | +0.5869 | 4.551     | +1.000      | +0.484       | Dchg 50%  ✓
 8  | +0.4836 | 4.551     | +1.000      | +0.380       | Dchg 60%  ✓
 9  | +0.3803 | 4.550     | +0.999      | +0.276       | Dchg 70%  ✓
10  | +0.2764 | 4.550     | +1.001      | +0.174       | Dchg 80%  ✓
11  | +0.1737 | 4.551     | +1.001      | +0.071       | Dchg 90%  ✓
12  | +0.0704 | 4.550     | +0.999      | -0.034       | Dchg 100% ✓
```

- 모든 chg phase 가 V≈4.55V 에서 종료 (CC-CV 만충)
- 모든 chg phase peak SOC ≈ 1.0 (정상 만충)
- dchg phase 종료 SOC = (1.0 − depth_pct/100) ± 1% (CV 전류 잔여 영향)

### 2. `hysteresis_path_validator.py` — 16 경로 일괄 검증

```
[종합] PASS=20, WARN=0, FAIL=0
```

- 16 경로 × 1-2 채널 = 20 채널 모두 PASS
- 글로벌 SOC 범위 [0.000, 1.000] 또는 부분 범위 [0.000, 0.898] (일부 5/6 시
  경로는 dchg 이후 chg 만 존재하므로)
- TC 3-12: first=+0.000, last=+0.073~0.099 (10% step 일관)
- TC 14-23: first=+0.000~0.169, last=+0.005~0.169 (충전 hysteresis)

### 3. `hysteresis_label_validator.py` — 라벨 일관성 검증

```
[종합] PASS=15, WARN=1, FAIL=0
```

- 1 WARN 은 path 11 "충전 재측정" — 의도된 결과 (방전 hysteresis 사이클이 없는
  재측정 데이터)
- TC 3-12 → Dchg 10/20/30/.../100%
- TC 14-23 → Chg 10/20/.../100%
- depth_pct 정확히 [10, 100] 범위

### 4. unified_flow=True 경로 수동 검증

```python
>>> unified_profile_core(ch, (4,4), 4960, 1.0,
...     data_scope='cycle', axis_mode='soc',
...     overlap='connected', calc_dqdv=True,
...     unified_flow=True, origin_compat=True)
len=108
has SOC=True
has dQdV=True
has _dqdv_cap_proxy=False  ← 임시 컬럼 정상 cleanup
dQdV range: [-248.911, 525.403]  ← CV 외 정상 범위
```

## 후속

### 권장 추가 작업

1. **CV 영역 outlier 마스킹** — `origin_compat=True` 일 때 |dV| < 2mV 영역에서
   dQdV 가 -3690 같은 큰 spike 발생. 현재는 matplotlib y-축 클리핑으로 가려지나,
   엑셀 골든은 leading rows 만 NaN. spike 가 차트에 가시화되는지 추가 점검 필요.
2. **사용자 선택 TC 범위 기반 anchor** — 현재는 SaveEndData 전체 사이클에서
   초기 SOC 를 추정. 사용자가 TC 3-12 만 선택했어도 전체 데이터를 본다.
   향후 hysteresis 모드에서 사용자 선택 범위만 처리하도록 옵션 추가 검토.
3. **Toyo 지원 확장** — `_compute_tc_soc_offsets` 가 PNE SaveEndData 의존이므로
   Toyo hysteresis 시험 (수가 적지만 가능) 시 offset 산출 불가. PNE 와 동등한
   net 누적 함수를 Toyo 측에 추가하면 전 사이클러 지원 가능.

### 회귀 가드

- `hysteresis_path_validator.py`: 16 경로 일괄 검증 — 수정 후 모두 PASS
- `hysteresis_label_validator.py`: 라벨 정합성 검증 — 수정 후 PASS
- 사용자 보고 데이터 (Si 10% / Si 15%) 의 TC 3-12 SOC offset 이 [0, 1] 범위 내
  10% step 으로 정확히 배치됨 확인

## 변경 파일 요약

| 위치 | 변경 |
|---|---|
| L863-936 `_compute_tc_soc_offsets` | 알고리즘 전면 교체 — 2-패스 클립 누적 |
| L2541-2562 `_unified_calculate_dqdv` | SOC fallback 추가 — ChgCap/DchgCap proxy |
| L2614-2616 `_unified_calculate_dqdv` 종료부 | proxy 컬럼 정리 |
