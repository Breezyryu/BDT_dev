"""시그니처 추출 — DataFrame → column-wise stats dict.

byte-level baseline 보다 ~10000x 작은 회귀 비교 unit. 동일 시그니처면
numerical 측 동일 (NaN-safe + float 정밀도 측 정합).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "DataTool_dev_code"))

from bdt_regression import extract_signature, signatures_equal  # noqa: E402


def _sample_df():
    return pd.DataFrame({
        "Cycle": [1, 2, 3, 4, 5],
        "Dchg": [1.0, 0.99, 0.98, np.nan, 0.96],
        "Eff": [0.99, 0.99, np.nan, 0.99, 0.98],
        "label": ["a", "b", "c", "d", "e"],  # non-numeric — 무시
    })


def test_signature_returns_dict_per_numeric_column():
    """시그니처 = numeric 컬럼별 stats dict (string 컬럼 무시)."""
    sig = extract_signature(_sample_df())
    assert "Cycle" in sig and "Dchg" in sig and "Eff" in sig
    assert "label" not in sig


def test_signature_includes_n_sum_med_min_max():
    """각 컬럼 시그니처 = (n_valid, sum, median, min, max)."""
    sig = extract_signature(_sample_df())
    cycle = sig["Cycle"]
    assert cycle["n"] == 5
    assert cycle["sum"] == pytest.approx(15.0)
    assert cycle["median"] == pytest.approx(3.0)
    assert cycle["min"] == 1.0
    assert cycle["max"] == 5.0


def test_signature_handles_nan():
    """NaN 무시 — n_valid count + sum/median/min/max 모두 dropna."""
    sig = extract_signature(_sample_df())
    dchg = sig["Dchg"]
    assert dchg["n"] == 4  # 5 - 1 NaN
    assert dchg["sum"] == pytest.approx(3.93)


def test_signature_empty_df():
    """빈 DataFrame → empty dict."""
    sig = extract_signature(pd.DataFrame())
    assert sig == {}


def test_signature_all_nan_column():
    """모든 NaN 컬럼 → n=0, 다른 stat 은 None."""
    df = pd.DataFrame({"x": [np.nan, np.nan, np.nan]})
    sig = extract_signature(df)
    assert sig["x"]["n"] == 0
    assert sig["x"]["sum"] is None


def test_signatures_equal_byte_level():
    """동일 DataFrame → 시그니처 동일."""
    sig1 = extract_signature(_sample_df())
    sig2 = extract_signature(_sample_df())
    assert signatures_equal(sig1, sig2)


def test_signatures_equal_detects_difference():
    """1 값 변경 시 시그니처 다름."""
    df1 = _sample_df()
    df2 = df1.copy()
    df2.loc[0, "Dchg"] = 99.9  # 한 값 변경
    sig1 = extract_signature(df1)
    sig2 = extract_signature(df2)
    assert not signatures_equal(sig1, sig2)


def test_signatures_equal_nan_safe():
    """NaN 양쪽 동일 — equal 판정."""
    df = pd.DataFrame({"x": [1.0, np.nan, 3.0]})
    sig1 = extract_signature(df)
    sig2 = extract_signature(df.copy())
    assert signatures_equal(sig1, sig2)
