"""classify_pne_cycles 벡터화 회귀 슈트.

사용법:
    python tools/test_code/regression_classify_pne_cycles.py --capture
    python tools/test_code/regression_classify_pne_cycles.py --verify
"""
from __future__ import annotations

import argparse
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'DataTool_dev_code'))

_MAIN_ROOT = Path(__file__).resolve().parents[5] if len(Path(__file__).resolve().parents) >= 6 else ROOT
RAW_FIXTURE = (
    _MAIN_ROOT / 'raw' / 'raw_exp' / 'exp_data' / '수명' /
    '251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202' /
    'M01Ch008[008]' / 'Restore' / 'ch08_SaveEndData.csv'
)
CAPACITY = 2335
BASELINE_PKL = Path(__file__).parent / '_regression_baseline_classify_pne_cycles.pkl'

from DataTool_optRCD_proto_ import classify_pne_cycles  # noqa: E402


def _load_summary(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(str(path), header=None, encoding='cp949', on_bad_lines='skip')
    if raw.shape[1] < 28:
        raise RuntimeError(f'unexpected column count: {raw.shape}')
    summary = raw[[27, 2, 6, 9, 10, 11, 17]].copy()
    summary.columns = ['TotlCycle', 'StepType', 'EndState', 'Current', 'ChgCap', 'DchgCap', 'StepTime']
    return summary


def _capture(path: Path, capacity: int, n_iter: int = 5) -> None:
    if not path.exists():
        print(f'[SKIP] 픽스처 없음: {path}')
        return
    print(f'[FIXTURE] {path}')
    summary = _load_summary(path)
    print(f'[INPUT] shape={summary.shape}  TC={summary["TotlCycle"].nunique()}')

    classify_pne_cycles(summary, capacity)  # warm-up
    times = []
    for _ in range(n_iter):
        t0 = time.perf_counter()
        out = classify_pne_cycles(summary, capacity)
        times.append(time.perf_counter() - t0)
    avg_ms = np.mean(times) * 1000
    p95_ms = np.percentile(times, 95) * 1000
    print(f'[TIMING] mean={avg_ms:.2f} ms / p95={p95_ms:.2f} ms / n={n_iter}')
    cats = {}
    for r in out:
        cats[r['category']] = cats.get(r['category'], 0) + 1
    print(f'[OUTPUT] entries={len(out)}  categories={cats}')

    BASELINE_PKL.write_bytes(pickle.dumps({
        'fixture_path': str(path),
        'capacity': capacity,
        'classified': out,
        'timing_mean_ms': avg_ms,
        'timing_p95_ms': p95_ms,
        'n_iter': n_iter,
    }))
    print(f'[CAPTURED] {BASELINE_PKL}  ({BASELINE_PKL.stat().st_size:,} bytes)')


def _verify(path: Path, capacity: int, n_iter: int = 5) -> int:
    if not BASELINE_PKL.exists():
        print(f'[ERROR] 베이스라인 없음 — 먼저 --capture: {BASELINE_PKL}')
        return 2
    if not path.exists():
        print(f'[SKIP] 픽스처 없음: {path}')
        return 0

    baseline = pickle.loads(BASELINE_PKL.read_bytes())
    print(f'[BASELINE] mean={baseline["timing_mean_ms"]:.2f} ms')
    summary = _load_summary(path)

    classify_pne_cycles(summary, capacity)  # warm-up
    times = []
    for _ in range(n_iter):
        t0 = time.perf_counter()
        out = classify_pne_cycles(summary, capacity)
        times.append(time.perf_counter() - t0)
    cur_mean = np.mean(times) * 1000
    cur_p95 = np.percentile(times, 95) * 1000
    print(f'[CURRENT ] mean={cur_mean:.2f} ms / p95={cur_p95:.2f} ms')
    print(f'[SPEEDUP ] {baseline["timing_mean_ms"] / max(cur_mean, 1e-9):.2f}x')

    expected = baseline['classified']
    if len(expected) != len(out):
        print(f'[FAIL] len mismatch: expected={len(expected)} actual={len(out)}')
        return 1

    diffs = []
    for i, (e, a) in enumerate(zip(expected, out)):
        if set(e.keys()) != set(a.keys()):
            diffs.append((i, 'keys', sorted(e.keys()), sorted(a.keys())))
            continue
        for k in e:
            if e[k] != a[k]:
                diffs.append((i, k, e[k], a[k]))

    if diffs:
        print(f'[FAIL] {len(diffs)} 불일치 (앞 5개):')
        for i, k, ev, av in diffs[:5]:
            print(f'    entry={i} {k}: expected={ev!r} actual={av!r}')
        return 1
    print(f'[PASS] {len(expected)} entries 완전 일치')
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--capture', action='store_true')
    ap.add_argument('--verify', action='store_true')
    ap.add_argument('--n', type=int, default=5)
    args = ap.parse_args()
    if not (args.capture or args.verify):
        ap.print_help()
        return 2
    if args.capture:
        _capture(RAW_FIXTURE, CAPACITY, args.n)
        return 0
    return _verify(RAW_FIXTURE, CAPACITY, args.n)


if __name__ == '__main__':
    raise SystemExit(main())
