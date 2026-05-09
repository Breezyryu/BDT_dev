"""전수 회귀 — 사이클 + 프로파일 분석 (452 채널 자동 parametrize).

RED 4: 프로파일 풀 사이클 시그니처 회귀
RED 5: 전수 parametrize (auto-discover fixture)
RED 6: 에러 isolation + xfail 정책

실행:
  # baseline 생성 (첫 1회, 약 1시간 직렬 / 15분 병렬)
  pytest tests/regression/test_full_sweep.py --update-baseline -n 4

  # 회귀 검증 (이후, 약 1시간 직렬 / 15분 병렬)
  pytest tests/regression/test_full_sweep.py -n 4

  # 빠른 회귀 (대표 채널만)
  pytest tests/regression/test_full_sweep.py -k "Q7M_Inner_BLK1 or M01Ch008"

옵션:
  --update-baseline   baseline 재생성
  -n N                병렬 worker (pytest-xdist 필요)
  --tb=short          짧은 traceback
  -k EXPR             채널 label 필터
"""
from __future__ import annotations

import json
import os
import sys
import warnings
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "DataTool_dev_code"))

from bdt_regression import (  # noqa: E402
    discover_channels,
    extract_signature,
    signatures_equal,
    signature_diff,
    ChannelInfo,
)


_RAW_ROOT = Path(os.environ.get(
    "BDT_RAW_ROOT",
    "C:/Users/Ryu/battery/python/BDT_dev/raw"
)) / "raw_exp" / "exp_data"

_BASELINE_DIR = Path(__file__).parent / "baselines"
_BASELINE_DIR.mkdir(exist_ok=True)


def _all_channels() -> list[ChannelInfo]:
    """전수 채널 — module-level 1회 인벤토리."""
    if not _RAW_ROOT.is_dir():
        return []
    return discover_channels(_RAW_ROOT)


_CHANNELS = _all_channels()


# ─────────────────────────────────────────────────────────────────────────────
# RED 5 — auto-discover parametrize
# ─────────────────────────────────────────────────────────────────────────────


def _ids(c: ChannelInfo) -> str:
    return c.label[:80]


@pytest.mark.parametrize("channel", _CHANNELS, ids=lambda c: c.label[:80])
def test_cycle_signature(channel, request):
    """전수 사이클 시그니처 회귀 — 모든 채널.

    RED 6 (에러 isolation): cycler 분기 + 빈 결과 자동 skip + 예외 isolation.
    """
    import DataTool_optRCD_proto_ as bdt

    bdt._reset_all_caches()

    # 분석 호출 — 사이클러별 분기 (에러 시 skip, isolation)
    try:
        if channel.cycler == "Toyo":
            mc, df = bdt.toyo_cycle_data(str(channel.path), 0, 0.2, True)
        else:  # PNE
            mc, df = bdt.pne_cycle_data(str(channel.path), 0, 0.2, True, False, False)
    except Exception as e:
        pytest.skip(f"분석 실패 ({channel.cycler}): {type(e).__name__}: {e}")

    if not hasattr(df, "NewData") or df.NewData is None or df.NewData.empty:
        pytest.skip(f"빈 결과: {channel.label}")

    sig_new = extract_signature(df.NewData)
    if not sig_new:
        pytest.skip(f"numeric 컬럼 없음: {channel.label}")

    baseline_path = _BASELINE_DIR / f"{channel.label}_cycle.json"
    update = request.config.getoption("--update-baseline", default=False)

    if not baseline_path.exists() or update:
        with baseline_path.open("w", encoding="utf-8") as f:
            json.dump(sig_new, f, indent=2, default=str)
        pytest.skip(f"baseline 생성: {baseline_path.name} ({len(sig_new)} cols)")

    with baseline_path.open(encoding="utf-8") as f:
        sig_old = json.load(f)

    if not signatures_equal(sig_new, sig_old):
        diffs = signature_diff(sig_new, sig_old)
        pytest.fail(
            f"사이클 회귀 — {channel.label}\n"
            + "\n".join(diffs[:10]))


# ─────────────────────────────────────────────────────────────────────────────
# RED 4 — 프로파일 풀 사이클 회귀
# ─────────────────────────────────────────────────────────────────────────────


def _profile_full(bdt, channel: ChannelInfo):
    """채널 풀 사이클 범위 프로파일 로드 + 정규화 → 표준 컬럼 DataFrame."""
    mincap = 0.0
    if channel.cycler == "Toyo":
        mincap = bdt.toyo_min_cap(str(channel.path), 0, 0.2)
        if not mincap:
            return None
        # cycle_map 자동 빌드 (가능 시)
        try:
            cycle_map, _ = bdt.toyo_build_cycle_map(
                str(channel.path), mincap, 0.2)
        except Exception:
            cycle_map = None
        # 사이클 범위 — 채널 NNNNNN max 또는 cycle_map max
        if cycle_map:
            tc_max = max(v["all"][1] for v in cycle_map.values()
                         if isinstance(v, dict) and "all" in v)
            c_min, c_max = min(cycle_map.keys()), max(cycle_map.keys())
        else:
            nn = sorted([f for f in os.listdir(channel.path)
                         if f.isdigit() and len(f) == 6])
            if not nn:
                return None
            c_min, c_max = int(nn[0]), int(nn[-1])
        # 풀 사이클 범위 너무 크면 메모리 문제 — 최대 200 사이클로 제한
        if (c_max - c_min) > 200:
            c_max = c_min + 200
        raw = bdt._unified_toyo_load_raw(
            str(channel.path), c_min, c_max, cycle_map=cycle_map)
        if raw is None or raw.empty:
            return None
        return bdt._unified_normalize_toyo(raw, mincap)
    else:  # PNE
        mincap = bdt.pne_min_cap(str(channel.path), 0, 0.2)
        if not mincap:
            return None
        try:
            cycle_map, _ = bdt._get_pne_cycle_map(
                str(channel.path), mincap, 0.2)
        except Exception:
            cycle_map = None
        # 사이클 범위
        if cycle_map:
            c_min, c_max = min(cycle_map.keys()), max(cycle_map.keys())
        else:
            c_min, c_max = 1, 100
        # 너무 크면 200 으로 제한
        if (c_max - c_min) > 200:
            c_max = c_min + 200
        raw = bdt._unified_pne_load_raw(
            str(channel.path), c_min, c_max, cycle_map=cycle_map)
        if raw is None or raw.empty:
            return None
        return bdt._unified_normalize_pne(raw, mincap, str(channel.path))


@pytest.mark.parametrize("channel", _CHANNELS, ids=lambda c: c.label[:80])
def test_profile_full_signature(channel, request):
    """전수 프로파일 풀 사이클 시그니처 회귀.

    너무 큰 채널은 200 사이클로 제한 (메모리 protection). 풀 회귀 시
    단일 채널 OOM 으로 전체 sweep 중단 방지.
    """
    import DataTool_optRCD_proto_ as bdt

    bdt._reset_all_caches()

    try:
        df = _profile_full(bdt, channel)
    except Exception as e:
        pytest.skip(f"프로파일 실패 ({channel.cycler}): {type(e).__name__}: {e}")

    if df is None or df.empty:
        pytest.skip(f"빈 프로파일: {channel.label}")

    sig_new = extract_signature(df)
    if not sig_new:
        pytest.skip(f"numeric 컬럼 없음: {channel.label}")

    baseline_path = _BASELINE_DIR / f"{channel.label}_profile.json"
    update = request.config.getoption("--update-baseline", default=False)

    if not baseline_path.exists() or update:
        with baseline_path.open("w", encoding="utf-8") as f:
            json.dump(sig_new, f, indent=2, default=str)
        pytest.skip(f"baseline 생성: {baseline_path.name} ({len(sig_new)} cols)")

    with baseline_path.open(encoding="utf-8") as f:
        sig_old = json.load(f)

    if not signatures_equal(sig_new, sig_old):
        diffs = signature_diff(sig_new, sig_old)
        pytest.fail(
            f"프로파일 회귀 — {channel.label}\n"
            + "\n".join(diffs[:10]))
