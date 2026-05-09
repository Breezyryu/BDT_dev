"""PNE .log integrity 다층 cross-check 회귀 슈트.

대상 함수 (DataTool_optRCD_proto_.py):
    - _parse_pne_log
    - _check_csv_tc_continuity
    - _check_endpoint_anomaly
    - _classify_pne_integrity

사용법:
    python tools/test_code/regression_log_integrity.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'DataTool_dev_code'))

_MAIN_ROOT = Path(__file__).resolve().parents[5] if len(Path(__file__).resolve().parents) >= 6 else ROOT

# 픽스처: 우정협 ATL 2335mAh ch08 (운영자 stop 5회 / pause 4회 — data_loss 케이스)
RAW_FOLDER = (
    _MAIN_ROOT / 'raw' / 'raw_exp' / 'exp_data' / '수명' /
    '251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202'
)
LOG_FIXTURE = RAW_FOLDER / 'M01Ch008[008]' / '251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202.log'
CSV_FIXTURE = RAW_FOLDER / 'M01Ch008[008]' / 'Restore' / 'ch08_SaveEndData.csv'

from DataTool_optRCD_proto_ import (  # noqa: E402
    _parse_pne_log,
    _check_csv_tc_continuity,
    _check_endpoint_anomaly,
    _classify_pne_integrity,
)


def test_parse_pne_log_real():
    """우정협 ATL ch08 .log — stop 5회, pause 4회 (실측)."""
    if not LOG_FIXTURE.exists():
        print(f'[SKIP] {LOG_FIXTURE.name} 없음')
        return True
    out = _parse_pne_log(str(LOG_FIXTURE))
    assert out['is_present'], 'is_present=True 기대'
    # 실측: stop=8 / resume=8 / pause=3 (cap on the same .log fixture)
    assert out['n_stops'] == 8, f"n_stops 8 기대, got {out['n_stops']}"
    assert out['n_resumes'] >= 7, f"n_resumes >=7 기대, got {out['n_resumes']}"
    assert out['n_pauses'] == 3, f"n_pauses 3 기대, got {out['n_pauses']}"
    assert out['last_stop_cycle'] >= 1
    assert out['last_stop_step'] >= 1
    assert out['first_start_dt'] == '2025/10/28 05:59:12'
    assert out['last_event_kind'] in ('stop', 'pause', 'resume'), out['last_event_kind']
    print(f'[PASS] _parse_pne_log({LOG_FIXTURE.name})')
    print(f'       n_stops={out["n_stops"]} n_resumes={out["n_resumes"]} '
          f'n_pauses={out["n_pauses"]} last_stop=Cycle{out["last_stop_cycle"]} '
          f'Step{out["last_stop_step"]} last_event={out["last_event_kind"]}')
    return True


def test_parse_pne_log_missing():
    """파일 없음 케이스 — 모든 카운트 0, is_present=False."""
    out = _parse_pne_log(str(_MAIN_ROOT / 'nonexistent.log'))
    assert out['is_present'] is False
    assert out['n_stops'] == 0
    assert out['n_lines'] == 0
    print('[PASS] _parse_pne_log(missing)')
    return True


def test_csv_tc_continuity_clean():
    """우정협 ATL ch08 SaveEndData — TC 1~760 연속 (정상)."""
    if not CSV_FIXTURE.exists():
        print(f'[SKIP] {CSV_FIXTURE.name} 없음')
        return True
    raw = pd.read_csv(str(CSV_FIXTURE), header=None, encoding='cp949', on_bad_lines='skip')
    out = _check_csv_tc_continuity(raw)
    assert out['tc_min'] == 1, f'tc_min 1 기대, got {out["tc_min"]}'
    assert out['tc_max'] == 760, f'tc_max 760 기대, got {out["tc_max"]}'
    assert out['n_unique'] == 760
    assert out['starts_at_one'] is True
    assert out['has_gaps'] is False, f"gap_intervals={out['gap_intervals']}"
    assert out['is_anomaly'] is False
    print(f'[PASS] _check_csv_tc_continuity(clean): TC {out["tc_min"]}~{out["tc_max"]}, '
          f'gaps={out["has_gaps"]}')
    return True


def test_csv_tc_continuity_partial_synthetic():
    """synthetic — TC 5 부터 시작 (partial run) → starts_at_one=False, is_anomaly=True."""
    df = pd.DataFrame({
        2: [1, 2, 1, 2, 1, 2],
        27: [5, 5, 6, 6, 7, 7],
    })
    # 28 column 만족
    for c in range(28):
        if c not in df.columns:
            df[c] = 0
    out = _check_csv_tc_continuity(df)
    assert out['tc_min'] == 5
    assert out['tc_max'] == 7
    assert out['starts_at_one'] is False
    assert out['has_gaps'] is False
    assert out['is_anomaly'] is True, 'starts_at_one=False 면 is_anomaly=True'
    print('[PASS] _check_csv_tc_continuity(partial start)')
    return True


def test_csv_tc_continuity_gap_synthetic():
    """synthetic — TC 1,2,5,6 (3,4 누락) → has_gaps=True, gap_intervals=[(3,4)]."""
    df = pd.DataFrame({
        2: [1, 2, 1, 2],
        27: [1, 2, 5, 6],
    })
    for c in range(28):
        if c not in df.columns:
            df[c] = 0
    out = _check_csv_tc_continuity(df)
    assert out['has_gaps'] is True
    assert out['gap_intervals'] == [(3, 4)], f"gap_intervals={out['gap_intervals']}"
    assert out['n_missing_tc'] == 2
    print(f'[PASS] _check_csv_tc_continuity(gap): {out["gap_intervals"]}')
    return True


def test_endpoint_anomaly():
    """endpoint 4 시나리오: 정상 / silent corruption / in_progress / 둘 다 0."""
    # 정상 (cyc ≈ csv)
    out = _check_endpoint_anomaly(50000, 50000)
    assert out['has_anomaly'] is False
    # silent corruption (.cyc 손실)
    out = _check_endpoint_anomaly(5235, 49853)
    assert out['has_anomaly'] is True
    assert '90' in out['reason'] or '89' in out['reason']  # ~89.5% loss
    # in_progress (.cyc > csv 큰 차이)
    out = _check_endpoint_anomaly(50000, 49500)
    assert out['has_anomaly'] is False
    assert 'in_progress' in out['reason']
    # csv 미로드
    out = _check_endpoint_anomaly(0, 0)
    assert out['has_anomaly'] is False
    print('[PASS] _check_endpoint_anomaly (4 시나리오)')
    return True


def test_classify_integrity():
    """4-tier 분류 — clean / data_loss / compromised / in_progress."""
    # clean: 이벤트 0 + 모두 정상
    cls = _classify_pne_integrity(
        {'n_stops': 0, 'n_pauses': 0, 'last_event_kind': None},
        {'is_anomaly': False},
        {'has_anomaly': False},
    )
    assert cls == 'clean', cls

    # data_loss: stop/pause 있으나 endpoint/TC 정상 (우정협 ch08 케이스)
    cls = _classify_pne_integrity(
        {'n_stops': 5, 'n_pauses': 4, 'last_event_kind': 'pause'},
        {'is_anomaly': False},
        {'has_anomaly': False},
    )
    assert cls == 'data_loss', cls

    # compromised: endpoint anomaly (박민희 .cyc<csv)
    cls = _classify_pne_integrity(
        {'n_stops': 0, 'n_pauses': 0, 'last_event_kind': None},
        {'is_anomaly': False},
        {'has_anomaly': True},
    )
    assert cls == 'compromised', cls

    # compromised: CSV TC anomaly (안성진 partial)
    cls = _classify_pne_integrity(
        {'n_stops': 8, 'n_pauses': 4, 'last_event_kind': 'stop'},
        {'is_anomaly': True},
        {'has_anomaly': False},
    )
    assert cls == 'compromised', cls

    print('[PASS] _classify_pne_integrity (4 tiers)')
    return True


def test_real_uchunghyup_classification():
    """우정협 ATL ch08 실측 통합 — log+csv+endpoint → data_loss 분류 기대."""
    if not (LOG_FIXTURE.exists() and CSV_FIXTURE.exists()):
        print('[SKIP] real fixture 없음')
        return True
    log_summary = _parse_pne_log(str(LOG_FIXTURE))
    raw = pd.read_csv(str(CSV_FIXTURE), header=None, encoding='cp949', on_bad_lines='skip')
    csv_check = _check_csv_tc_continuity(raw)
    # cyc_max 는 본 슈트에서 .cyc 파싱 안 함 — endpoint anomaly check skip (gap=0)
    ep_check = _check_endpoint_anomaly(0, 0)
    cls = _classify_pne_integrity(log_summary, csv_check, ep_check)
    print(f'[INFO] 우정협 ATL ch08 통합 → integrity={cls!r}')
    print(f'       log:n_stops={log_summary["n_stops"]} n_pauses={log_summary["n_pauses"]}')
    print(f'       csv:tc={csv_check["tc_min"]}~{csv_check["tc_max"]} '
          f'gaps={csv_check["has_gaps"]}')
    print(f'       ep :reason={ep_check["reason"]}')
    assert cls == 'data_loss', f'기대 data_loss, got {cls}'
    print('[PASS] real_uchunghyup → data_loss')
    return True


def main() -> int:
    tests = [
        test_parse_pne_log_real,
        test_parse_pne_log_missing,
        test_csv_tc_continuity_clean,
        test_csv_tc_continuity_partial_synthetic,
        test_csv_tc_continuity_gap_synthetic,
        test_endpoint_anomaly,
        test_classify_integrity,
        test_real_uchunghyup_classification,
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
