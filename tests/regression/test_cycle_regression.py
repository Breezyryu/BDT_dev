"""사이클 분석 회귀 — 1 채널 tracer (RED 3).

워크플로우:
  1. 첫 실행 (또는 --update-baseline): baseline 시그니처 생성 → skip
  2. 이후 실행: 신 시그니처 vs baseline 비교 → byte-level 정합 검증

baseline: tests/regression/baselines/<label>_cycle.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "DataTool_dev_code"))

from bdt_regression import (  # noqa: E402
    discover_channels,
    extract_signature,
    signatures_equal,
    signature_diff,
)


_BASELINE_DIR = Path(__file__).parent / "baselines"
_BASELINE_DIR.mkdir(exist_ok=True)


# tracer 채널 — Q7M Inner BLK1 ch11 (Toyo, 4956 step, A·B′·C′ 회귀 검증 표준)
TRACER_CHANNEL_HINT = "Q7M Inner ATL_45V 1689mAh BLK1 20EA"
TRACER_CH_NAME = "11"


@pytest.fixture(scope="module")
def tracer_channel():
    """Q7M Inner BLK1 ch11 자동 발견."""
    import os
    raw = Path(os.environ.get(
        "BDT_RAW_ROOT",
        "C:/Users/Ryu/battery/python/BDT_dev/raw"
    )) / "raw_exp" / "exp_data"
    chs = [c for c in discover_channels(raw)
           if TRACER_CHANNEL_HINT in str(c.path) and c.path.name == TRACER_CH_NAME]
    if not chs:
        pytest.skip(f"tracer 채널 없음: {TRACER_CHANNEL_HINT}/{TRACER_CH_NAME}")
    return chs[0]


def test_cycle_signature_baseline_exists_or_create(tracer_channel, request):
    """tracer 채널 사이클 시그니처 — baseline 생성 또는 회귀 검증."""
    import DataTool_optRCD_proto_ as bdt

    bdt._reset_all_caches()
    mc, df = bdt.toyo_cycle_data(str(tracer_channel.path), 0, 0.2, True)
    assert hasattr(df, "NewData") and not df.NewData.empty, \
        f"toyo_cycle_data 빈 결과: {tracer_channel.label}"

    sig_new = extract_signature(df.NewData)
    baseline_path = _BASELINE_DIR / f"{tracer_channel.label}_cycle.json"

    update = request.config.getoption("--update-baseline")
    if not baseline_path.exists() or update:
        with baseline_path.open("w", encoding="utf-8") as f:
            json.dump(sig_new, f, indent=2, default=str)
        pytest.skip(f"baseline 생성: {baseline_path.name} ({len(sig_new)} cols)")

    with baseline_path.open(encoding="utf-8") as f:
        sig_old = json.load(f)

    if not signatures_equal(sig_new, sig_old):
        diffs = signature_diff(sig_new, sig_old)
        pytest.fail(
            f"사이클 시그니처 회귀 — {tracer_channel.label}\n"
            + "\n".join(diffs[:10]))
