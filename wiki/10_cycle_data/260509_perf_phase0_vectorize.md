# Phase 0 hot 함수 벡터화 — 50x speedup

**날짜**: 2026-05-09
**요청자**: 류성택 ("속도 개선 포인트가 있을까?")
**적용 함수**:
- [`_extract_tc_info_pne`](../../DataTool_dev_code/DataTool_optRCD_proto_.py)
- [`classify_pne_cycles`](../../DataTool_dev_code/DataTool_optRCD_proto_.py)

---

## 결과

| 함수 | 벡터화 전 | 벡터화 후 | speedup |
|---|---:|---:|---:|
| `_extract_tc_info_pne` | 254.39 ms | 4.37 ms | **58.23x** |
| `classify_pne_cycles` | 154.68 ms | 3.77 ms | **41.03x** |
| 합 (Phase 0 일부) | 409 ms | 8.14 ms | **50.2x** |

픽스처: 우정협 5196mAh ATL 2335mAh Q8 ATL 선상 SEU4 RT @1-1202 / M01Ch008
(SaveEndData.csv 6,792 row × 47 col / 760 TC).

회귀 슈트:
- [`tools/test_code/regression_extract_tc_info_pne.py`](../../tools/test_code/regression_extract_tc_info_pne.py) — 760 TC × 9 fields byte-equal
- [`tools/test_code/regression_classify_pne_cycles.py`](../../tools/test_code/regression_classify_pne_cycles.py) — 760 entries 완전 일치

---

## 근본 원인

두 함수 공통 패턴: `for cyc, group in real.groupby('TotlCycle'):` 외곽 루프
+ 매 group 마다 `.sum()`, `.isin()`, `.iterrows()` 반복.

| 함수 | 외곽 루프 | 내곽 hot |
|---|---|---|
| `_extract_tc_info_pne` | 760 TC × `groupby(27)` | TC당 chg_rows iterrows + cc_time/cc_cap/end_state per-row Python |
| `classify_pne_cycles` | 760 TC × `groupby('TotlCycle')` | TC당 `_classify_single_pne_cycle` 호출 (4× `.sum`, `.isin`, `.values`) |

groupby 자체는 cython이지만 group iter + Python row 연산이 GIL bound.

---

## 처방 — 사전 계산 column + groupby 빌트인 agg

### 공통 전략

1. **모든 row 의 boolean/numeric flag 를 numpy 로 사전 계산** (한 번)
2. **NaN 마스크 column** 추가 — `np.where(is_chg, value, np.nan)` — groupby 가 NaN 무시 max/min 자동
3. **groupby.agg(빌트인만)** — `'sum'`, `'max'`, `'min'` 만 사용 (lambda 0건)
4. **agg 결과를 numpy 배열로 추출** 후 TC 가짓수만큼만 Python 루프 (760 회 — 무시할 수준)

### `_extract_tc_info_pne` 구체 변경

```python
# 사전 계산 — 모든 row 의 충전 current_mA
cccv_mode = is_cccv & (cc_time_s > 0)
cccv_curr = cc_cap_mAh * 3600 / np.where(cc_time_s > 0, cc_time_s, 1.0)
chg_curr_mA = np.where(cccv_mode, cccv_curr, end_curr_abs_mA)

# NaN 마스크 — 충전 row 만 v_chg_uV 가지도록
real2 = real.assign(_v_chg_uV=np.where(is_chg, end_volt_uV, np.nan), ...)

# groupby 빌트인 agg
agg = real2.groupby(27).agg({'_v_chg_uV': 'max', ...})
```

### `classify_pne_cycles` 구체 변경

```python
# 사전 계산 — 분류 트리에 필요한 모든 boolean count
real2 = real.assign(
    _chg=is_chg.astype(int), _dchg=is_dchg.astype(int), _rest=is_rest.astype(int),
    _es78=(end_state == 78).astype(int),
    _chg_es65=(is_chg & (end_state == 65)).astype(int),
    _chg_es66=(is_chg & (end_state == 66)).astype(int),
    _long_chg=(is_chg_or_extra & (step_time / 100 >= 300)).astype(int),
)
agg = real2.groupby('TotlCycle').agg({...: 'sum'})

# TC 가짓수만큼만 분류 트리 평가 (Python — 760 회)
for i in range(len(idx_arr)):
    ...
    if action in ('CHG_ONLY', 'DCHG_ONLY'): cat = '_pulse'
    elif has_es78 and n_charge >= 2 and n_discharge >= 2: cat = 'DCIR'
    ...
```

`_merge_pulse_groups` 는 inherently sequential (인접 펄스 쌍 병합) 이라 그대로
유지. 입력 raw_results 가 빠르게 만들어지면 충분.

---

## 회귀 검증

각 함수마다 베이스라인 캡처 → 벡터화 적용 → byte-equal 검증.

### `_extract_tc_info_pne`

```
[BASELINE] mean=254.39 ms
[CURRENT ] mean=4.37 ms / p95=4.75 ms
[SPEEDUP ] 58.23x
[PASS] 760 TC × 9 fields byte-equal
```

검증 fields: `tc, chg_crate, dchg_crate, v_max, v_min, mode_chg, source,
v_cutoff_chg, v_cutoff_dchg`

부동소수점 비교: `abs(expected - actual) > 1e-6` 시 fail.

### `classify_pne_cycles`

```
[BASELINE] mean=154.68 ms
[CURRENT ] mean=3.77 ms / p95=4.48 ms
[SPEEDUP ] 41.03x
[PASS] 760 entries 완전 일치
```

검증 fields: `cycle, category, n_charge, n_discharge, raw_cycles, raw_range`.

---

## 보류 — `_cyc_to_cycle_df` (Hot #1, ~220ms)

이전 hot 분석 (260508 추정) 에서 `_cyc_to_cycle_df` 도 220ms 로 식별됐으나
이번 회기에서 **벡터화 보류**.

### 보류 사유

1. **가변 segment + 분기**: step boundary 마다 `has_loop` 분기 (`seg` vs
   `seg[:-1]`) → segment 길이 가변. `np.add.reduceat` 적용하려면 분기
   사전에 평탄화 필요.
2. **회귀 위험 큼**:
   - `imp_val` (10초 DC 내부저항) → 사이클 711-714 voc 이슈와 직접 관련
   - `EndState` 추론 (CC/CV 변동률) → CCCV 분기 critical
3. **이득 대비 위험**: 220ms × 60 채널 ÷ ThreadPool 4 = wall clock ~3s
   감소. ② `.log` integrity 다층 cross-check 의 silent corruption 탐지
   가치가 운영자에게 더 크다.

별도 회기에서 `np.add.reduceat` + 분기 평탄화 + 회귀 슈트 (imp/EndState
field 별 byte-equal) 갖춘 뒤 진행 추천.

---

## 변경 위치

1. [`DataTool_optRCD_proto_.py:7881~7960`](../../DataTool_dev_code/DataTool_optRCD_proto_.py)
   — `_extract_tc_info_pne` 벡터화
2. [`DataTool_optRCD_proto_.py:6603~6717`](../../DataTool_dev_code/DataTool_optRCD_proto_.py)
   — `classify_pne_cycles` 벡터화 (`_classify_single_pne_cycle` 의
   `_pulse`/'_pulse' 분기 그대로 보존)
3. [`tools/test_code/regression_extract_tc_info_pne.py`](../../tools/test_code/regression_extract_tc_info_pne.py)
   — 회귀 슈트 신규
4. [`tools/test_code/regression_classify_pne_cycles.py`](../../tools/test_code/regression_classify_pne_cycles.py)
   — 회귀 슈트 신규
5. `tools/test_code/_regression_baseline_*.pkl` — baseline pickle (Git 추적)

---

## 후속

- ② `.log` integrity 다층 cross-check 진입 (silent corruption 탐지)
- ③ `_cyc_to_cycle_df` 별도 회기 (위험 평가 후)
