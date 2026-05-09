# SaveEndData col[33]/[34] datetime 추출 — Date/Time 활용 진입

**날짜**: 2026-05-09
**요청자**: 류성택 ("col 33/34 (Date/Time) 활용하자")
**대상 함수**: `_decode_save_end_datetime`, `_extract_save_end_dt_summary` (모두 신규)

---

## 배경

PNE SaveEndData 47 컬럼 중 col 33/34 가 step 종료 시각을 ms 정밀도로
기록하지만 BDT 가 이를 활용하지 않았다.

| col | 형식 | ch08 row[0] 예 | 의미 |
|---|---|---:|---|
| 33 | `YYYYMMDD` (8 digit int) | 20251028 | 2025-10-28 |
| 34 | `HHMMSSmmm` (9 digit int, ms) | 71949013 | 07:19:49.013 |

`.cyc` FID 43/44 ([proto_:10119, 11521](../../DataTool_dev_code/DataTool_optRCD_proto_.py))
와 동일 의미론. SaveEndData 측은 step 종료 시각 (record-level) 보다 abstract 한
step-level 시각이라 채널 진행 시각 요약에 적합.

### 정정 — col 14/15 (ChgWh/DchgWh) 분류 오류

이전 답변에서 col 14/15 를 "❌ 미활용" 으로 분류했으나, **실제로는
시계열·프로파일 영역에서 활용 중**:

- [`_unified_pne_load_raw`](../../DataTool_dev_code/DataTool_optRCD_proto_.py:1924) — `ChgWh_raw / DchgWh_raw` 로 매핑 + cap_divisor 적용
- [proto_:2170~2271](../../DataTool_dev_code/DataTool_optRCD_proto_.py) — 시계열 cumsum, 누적 에너지
- [proto_:3433~3639](../../DataTool_dev_code/DataTool_optRCD_proto_.py) — 프로파일 분석 Energy axis (`ChgWh - DchgWh`)

→ **시계열 시각화·프로파일 분석은 활용**, **`_extract_tc_info_pne` (TC 단위
메타) 에서만 미활용**. BDT 사용 비율 정정: SaveEndData 14/47 col 활용 (~30%).

---

## 활용 가치

채널 시간축을 ms 정밀도로 알 수 있어 다음 가능:

| 용도 | 비고 |
|---|---|
| **`.log` first_start_dt cross-check** | SaveData 첫 dt 가 `.log` 작업 시작과 ±1h 정상 — sanity |
| **endpoint anomaly 보강** | SaveData last_dt + `.cyc` FID 43/44 last_dt 비교 (silent corruption 시간 단서) |
| **Phase 0 콘솔 last_dt 표시** | 운영자가 채널 마지막 갱신 시각 인지 |
| **in_progress stale time** | 마지막 갱신이 N 일 이상 오래 → 시험 중단 의심 |
| **시험 진행 기간** | duration_days = (last - first) / 86400 |

---

## 신규 함수 2종

### 1. `_decode_save_end_datetime(date_int, time_int) → pd.Timestamp | None`

단일 row 의 col 33/34 → ms 정밀도 Timestamp.

- 0/negative/out-of-range (year < 1900 또는 ≥ 3000) → None
- TypeError path (None 입력) → None
- month/day/hour/minute/second 범위 검증 후 `pd.Timestamp` 생성

### 2. `_extract_save_end_dt_summary(raw_df) → dict`

채널의 SaveEndData 전체에서 시간축 요약 (StepType==8 loop 마커 제외).

```python
{
    'first_dt': pd.Timestamp | None,
    'last_dt': pd.Timestamp | None,
    'duration_days': float,        # (last - first) days
    'n_dt_valid': int,              # 디코딩 성공 row 수
    'n_total': int,                 # StepType==8 제외 row 수
    'is_present': bool,
}
```

numpy 마스크 + np.argmax 로 first/last valid row 1 회씩만 디코딩 (760 TC 채널
기준 < 10 ms).

---

## 회귀 슈트

[`tools/test_code/regression_save_end_datetime.py`](../../tools/test_code/regression_save_end_datetime.py) — 7 테스트 모두 통과:

```
[PASS] _decode_save_end_datetime(20251028, 71949013) → 2025-10-28T07:19:49.013000
[PASS] _decode_save_end_datetime(20260219, 230726813) → 2026-02-19T23:07:26.813000
[PASS] _decode_save_end_datetime(invalid → None)
[PASS] _extract_save_end_dt_summary(우정협 ch08):
       first=2025-10-28T07:19:49.013000
       last =2026-02-19T23:07:26.813000
       duration=114.66 days  valid=6033/6033
[PASS] _extract_save_end_dt_summary(empty/short → is_present=False)
[PASS] _extract_save_end_dt_summary(StepType==8 only → is_present=False)
[PASS] _extract_save_end_dt_summary(partial valid): first=28 last=29

Result: 7/7 passed
```

검증 내용:
- ch08 row[0] 디코딩: 20251028/71949013 → 2025-10-28 07:19:49.013
  - sanity: `.log` 작업 시작 5:59:12 + 첫 dchg 4840.65s 종료 = 7:19:52 (≈+3s 일치)
- ch08 row[6791] 디코딩: 20260219/230726813 → 2026-02-19 23:07:26.813
- 5 invalid 케이스 (0, negative, year out-of-range, month 13, hour 25, None)
- 실측 fixture 전체: first/last/duration_days/valid count
- 빈 DataFrame, col 부족, StepType=8 only, partial valid 4 edge case

---

## 보류 — ChannelMeta 통합 + Phase 0 콘솔

이번 회기 범위: **단위 함수 2 + 회귀 슈트 7 통과까지**.

다음 단계 (사용자 결정 시 별도 회기):

1. **ChannelMeta** ([proto_:380~417](../../DataTool_dev_code/DataTool_optRCD_proto_.py))
   에 신규 필드:
   - `data_first_dt: pd.Timestamp | None`
   - `data_last_dt: pd.Timestamp | None`
   - `data_duration_days: float`
2. **`_build_channel_meta`** 에 통합 — `_extract_save_end_dt_summary(_raw_df)` 호출 후
   ChannelMeta 에 박제
3. **Phase 0 콘솔** — 채널 main line 또는 detail line 에 `last=YYYY-MM-DD HH:MM` 추가
4. **`.log` cross-check** — `data_first_dt` vs `log_summary['first_start_dt']` ±1h 검증
   → mismatch 시 timestamp anomaly flag (`_classify_pne_integrity` 의 추가 trigger)
5. **`.cyc` FID 43/44 와 통합** — `_check_endpoint_anomaly` 가 시간축으로도 비교

---

## 변경 위치

1. [`DataTool_optRCD_proto_.py`](../../DataTool_dev_code/DataTool_optRCD_proto_.py)
   — `_check_endpoint_anomaly` 직후 (line ~8270 추정) 에 함수 2개 신규
2. [`tools/test_code/regression_save_end_datetime.py`](../../tools/test_code/regression_save_end_datetime.py)
   — 단위 회귀 슈트 7 테스트 신규

---

## 후속

- ChannelMeta 통합 (사용자 결정)
- `.log` first_start_dt cross-check (timestamp sanity 추가 layer)
- `.cyc` FID 43/44 와의 정합성 비교 (silent corruption 시간 단서)
