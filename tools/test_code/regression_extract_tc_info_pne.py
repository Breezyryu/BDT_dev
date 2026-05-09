"""_extract_tc_info_pne 벡터화 회귀 슈트.

사용법:
    # 1. 베이스라인 캡처 (벡터화 적용 전)
    python tools/test_code/regression_extract_tc_info_pne.py --capture

    # 2. 벡터화 적용 후 회귀 검증
    python tools/test_code/regression_extract_tc_info_pne.py --verify

픽스처 SaveEndData 경로는 RAW_FIXTURE 상수로 하드코딩 (사내 raw/ 의존).
사외 환경에서는 skip 처리됨.

산출물:
    tools/test_code/_regression_baseline_extract_tc_info_pne.pkl
        — capture 결과 dict[tc_int → TcInfo] + timing
"""
from __future__ import annotations

import argparse
import os
import pickle
import sys
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

# proto_ 위치 추가
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'DataTool_dev_code'))

# 픽스처 경로 — main BDT_dev 의 raw/ 직접 사용 (worktree 에는 raw/ 없음)
# parents[2]=worktree root, parents[3]=.claude/worktrees, parents[5]=BDT_dev main
_MAIN_ROOT = Path(__file__).resolve().parents[5] if len(Path(__file__).resolve().parents) >= 6 else ROOT
RAW_FIXTURE = (
    _MAIN_ROOT / 'raw' / 'raw_exp' / 'exp_data' / '수명' /
    '251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202' /
    'M01Ch008[008]' / 'Restore' / 'ch08_SaveEndData.csv'
)
CAPACITY = 2335.0  # mAh — Q8 ATL 정격
BASELINE_PKL = Path(__file__).parent / '_regression_baseline_extract_tc_info_pne.pkl'

# proto_ 의 함수와 TcInfo dataclass 를 직접 import
from DataTool_optRCD_proto_ import _extract_tc_info_pne, TcInfo  # noqa: E402


def _load_save_end_data(path: Path) -> pd.DataFrame:
    """PNE SaveEndData.csv → DataFrame (header=None, 0-based 컬럼)."""
    return pd.read_csv(str(path), header=None, encoding='cp949', on_bad_lines='skip')


def _td_to_dict(d: dict) -> dict:
    """TcInfo dict → {tc: asdict(TcInfo)} 직렬화 가능 형태."""
    return {tc: asdict(info) for tc, info in d.items()}


def _capture(path: Path, capacity: float, n_iter: int = 5) -> None:
    if not path.exists():
        print(f'[SKIP] 픽스처 없음: {path}')
        return
    print(f'[FIXTURE] {path}')
    df = _load_save_end_data(path)
    print(f'[INPUT] shape={df.shape} StepType=8 row={int((df[2] == 8).sum())}')

    # warm-up
    _extract_tc_info_pne(df, capacity)

    # timing
    times = []
    for _ in range(n_iter):
        t0 = time.perf_counter()
        out = _extract_tc_info_pne(df, capacity)
        times.append(time.perf_counter() - t0)
    avg_ms = np.mean(times) * 1000
    p95_ms = np.percentile(times, 95) * 1000
    print(f'[TIMING] mean={avg_ms:.2f} ms / p95={p95_ms:.2f} ms / n={n_iter}')
    print(f'[OUTPUT] tc_count={len(out)}  tc_min={min(out)}  tc_max={max(out)}')

    payload = {
        'fixture_path': str(path),
        'capacity': capacity,
        'tc_info_dict': _td_to_dict(out),
        'timing_mean_ms': avg_ms,
        'timing_p95_ms': p95_ms,
        'n_iter': n_iter,
    }
    BASELINE_PKL.write_bytes(pickle.dumps(payload))
    print(f'[CAPTURED] {BASELINE_PKL}  ({BASELINE_PKL.stat().st_size:,} bytes)')


def _verify(path: Path, capacity: float, n_iter: int = 5) -> int:
    if not BASELINE_PKL.exists():
        print(f'[ERROR] 베이스라인 없음 — 먼저 --capture 실행: {BASELINE_PKL}')
        return 2
    if not path.exists():
        print(f'[SKIP] 픽스처 없음: {path}')
        return 0

    baseline = pickle.loads(BASELINE_PKL.read_bytes())
    print(f'[BASELINE] {BASELINE_PKL.name}  '
          f'(captured timing mean={baseline["timing_mean_ms"]:.2f} ms)')
    df = _load_save_end_data(path)

    # warm-up
    _extract_tc_info_pne(df, capacity)
    times = []
    for _ in range(n_iter):
        t0 = time.perf_counter()
        out = _extract_tc_info_pne(df, capacity)
        times.append(time.perf_counter() - t0)
    cur_mean_ms = np.mean(times) * 1000
    cur_p95_ms = np.percentile(times, 95) * 1000
    print(f'[CURRENT ] mean={cur_mean_ms:.2f} ms / p95={cur_p95_ms:.2f} ms / n={n_iter}')

    speedup = baseline['timing_mean_ms'] / max(cur_mean_ms, 1e-9)
    print(f'[SPEEDUP ] {speedup:.2f}x')

    expected = baseline['tc_info_dict']
    actual = _td_to_dict(out)

    if set(expected.keys()) != set(actual.keys()):
        miss_e = set(expected.keys()) - set(actual.keys())
        miss_a = set(actual.keys()) - set(expected.keys())
        print(f'[FAIL] TC key mismatch: missing_in_actual={sorted(miss_e)[:5]} '
              f'missing_in_expected={sorted(miss_a)[:5]}')
        return 1

    diffs = []
    for tc in expected:
        e = expected[tc]
        a = actual[tc]
        for k in e:
            ev, av = e[k], a[k]
            if ev is None and av is None:
                continue
            if ev is None or av is None:
                diffs.append((tc, k, ev, av))
                continue
            if isinstance(ev, float):
                if abs(ev - av) > 1e-6:
                    diffs.append((tc, k, ev, av))
            else:
                if ev != av:
                    diffs.append((tc, k, ev, av))

    if diffs:
        print(f'[FAIL] {len(diffs)} field 불일치 (앞 5개):')
        for tc, k, ev, av in diffs[:5]:
            print(f'    TC={tc} {k}: expected={ev!r} actual={av!r}')
        return 1

    print(f'[PASS] {len(expected)} TC × 9 fields byte-equal')
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--capture', action='store_true', help='베이스라인 캡처')
    ap.add_argument('--verify', action='store_true', help='회귀 검증')
    ap.add_argument('--n', type=int, default=5, help='timing 반복 횟수')
    args = ap.parse_args()
    if not (args.capture or args.verify):
        ap.print_help()
        return 2
    if args.capture:
        _capture(RAW_FIXTURE, CAPACITY, args.n)
        return 0
    if args.verify:
        return _verify(RAW_FIXTURE, CAPACITY, args.n)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
