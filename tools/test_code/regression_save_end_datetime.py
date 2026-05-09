"""SaveEndData col[33]/[34] datetime 추출 회귀 슈트.

대상 함수 (DataTool_optRCD_proto_.py):
    - _decode_save_end_datetime
    - _extract_save_end_dt_summary

사용법:
    python tools/test_code/regression_save_end_datetime.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'DataTool_dev_code'))

_MAIN_ROOT = Path(__file__).resolve().parents[5] if len(Path(__file__).resolve().parents) >= 6 else ROOT

CSV_FIXTURE = (
    _MAIN_ROOT / 'raw' / 'raw_exp' / 'exp_data' / '수명' /
    '251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202' /
    'M01Ch008[008]' / 'Restore' / 'ch08_SaveEndData.csv'
)

from DataTool_optRCD_proto_ import (  # noqa: E402
    _decode_save_end_datetime,
    _extract_save_end_dt_summary,
)


def test_decode_basic():
    """ch08 row[0] 실측: 20251028 / 71949013 → 2025-10-28 07:19:49.013"""
    ts = _decode_save_end_datetime(20251028, 71949013)
    assert ts is not None
    assert ts.year == 2025 and ts.month == 10 and ts.day == 28
    assert ts.hour == 7 and ts.minute == 19 and ts.second == 49
    assert ts.microsecond == 13_000  # ms 13 → μs 13_000
    print(f'[PASS] _decode_save_end_datetime(20251028, 71949013) → {ts.isoformat()}')


def test_decode_last_row():
    """ch08 row[6791] 실측: 20260219 / 230726813 → 2026-02-19 23:07:26.813"""
    ts = _decode_save_end_datetime(20260219, 230726813)
    assert ts is not None
    assert ts.month == 2 and ts.day == 19
    assert ts.hour == 23 and ts.minute == 7 and ts.second == 26
    assert ts.microsecond == 813_000
    print(f'[PASS] _decode_save_end_datetime(20260219, 230726813) → {ts.isoformat()}')


def test_decode_invalid():
    """0/negative/out-of-range → None."""
    assert _decode_save_end_datetime(0, 0) is None
    assert _decode_save_end_datetime(20251028, -1) is None
    assert _decode_save_end_datetime(99999999, 71949013) is None
    assert _decode_save_end_datetime(20251332, 71949013) is None  # month 13 invalid
    assert _decode_save_end_datetime(20251028, 250000000) is None  # hour 25 invalid
    assert _decode_save_end_datetime(None, None) is None  # type-error path
    print('[PASS] _decode_save_end_datetime(invalid → None)')


def test_summary_real():
    """ch08 SaveEndData 전체: first=2025-10-28, last=2026-02-19, duration ~114일."""
    if not CSV_FIXTURE.exists():
        print(f'[SKIP] {CSV_FIXTURE.name} 없음')
        return
    df = pd.read_csv(str(CSV_FIXTURE), header=None, encoding='cp949', on_bad_lines='skip')
    out = _extract_save_end_dt_summary(df)
    assert out['is_present'] is True
    assert out['first_dt'].year == 2025 and out['first_dt'].month == 10
    assert out['last_dt'].year == 2026 and out['last_dt'].month == 2
    assert 100.0 < out['duration_days'] < 120.0, f"duration_days={out['duration_days']}"
    assert out['n_dt_valid'] > 0 and out['n_total'] > 0
    assert out['n_dt_valid'] <= out['n_total']
    print(f'[PASS] _extract_save_end_dt_summary(우정협 ch08):')
    print(f'       first={out["first_dt"].isoformat()}')
    print(f'       last ={out["last_dt"].isoformat()}')
    print(f'       duration={out["duration_days"]} days  '
          f'valid={out["n_dt_valid"]}/{out["n_total"]}')


def test_summary_empty():
    """빈 DataFrame / col 부족 → is_present=False."""
    out = _extract_save_end_dt_summary(pd.DataFrame())
    assert out['is_present'] is False
    out = _extract_save_end_dt_summary(pd.DataFrame({0: [1], 1: [2]}))
    assert out['is_present'] is False
    print('[PASS] _extract_save_end_dt_summary(empty/short → is_present=False)')


def test_summary_loop_only():
    """모든 row 가 StepType=8 (loop marker) 만 → real 비어 → is_present=False."""
    df = pd.DataFrame({c: [0] * 5 for c in range(47)})
    df[2] = 8
    df[33] = 20251028
    df[34] = 71949013
    out = _extract_save_end_dt_summary(df)
    assert out['is_present'] is False
    print('[PASS] _extract_save_end_dt_summary(StepType==8 only → is_present=False)')


def test_summary_invalid_dt_rows():
    """일부 row 만 valid dt — first/last 가 valid row 에서 추출."""
    df = pd.DataFrame({c: [0] * 5 for c in range(47)})
    df[2] = [1, 2, 1, 2, 1]
    df[27] = [1, 1, 2, 2, 3]
    df[33] = [0, 20251028, 0, 20251029, 0]            # row 1, 3 만 valid
    df[34] = [0, 71949013, 0, 80000000, 0]
    out = _extract_save_end_dt_summary(df)
    assert out['is_present'] is True
    assert out['n_dt_valid'] == 2
    assert out['first_dt'].day == 28
    assert out['last_dt'].day == 29
    print(f'[PASS] _extract_save_end_dt_summary(partial valid): '
          f'first={out["first_dt"].day} last={out["last_dt"].day}')


def main() -> int:
    tests = [
        test_decode_basic,
        test_decode_last_row,
        test_decode_invalid,
        test_summary_real,
        test_summary_empty,
        test_summary_loop_only,
        test_summary_invalid_dt_rows,
    ]
    fail = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f'[FAIL] {t.__name__}: {e}')
            fail += 1
        except Exception as e:
            print(f'[ERROR] {t.__name__}: {type(e).__name__}: {e}')
            fail += 1
    print(f'\n{"=" * 60}\nResult: {len(tests) - fail}/{len(tests)} passed')
    return 0 if fail == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
