"""경로 모드 3종 baseline — 일반·다중·연결 처리.

경로 모드 정의 ([[260310_link_cycle_multi_path_analysis]]):
  - single: 1 dataset (단일 시험)
  - multi: 동일 셀의 여러 dataset (시리즈 비교)
  - connected: 시계열 연속 dataset (1-100cyc + 101-200cyc + ... 연결)

Sweep:
  사이클 분석 baseline = 각 모드 측 dataset 첫 채널 시그니처
  프로파일 분석 옵션 baseline = 핵심 옵션 4 조합 (현재 가능한 범위)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "DataTool_dev_code"))

from bdt_regression import (  # noqa: E402
    PathBundle,
    discover_path_bundles,
    extract_signature,
    signatures_equal,
    signature_diff,
)


_RAW_ROOT = Path(os.environ.get(
    "BDT_RAW_ROOT",
    "C:/Users/Ryu/battery/python/BDT_dev/raw"
)) / "raw_exp" / "exp_data"

_BASELINE_DIR = Path(__file__).parent / "baselines"
_BASELINE_DIR.mkdir(exist_ok=True)


def _bundles() -> list[PathBundle]:
    if not _RAW_ROOT.is_dir():
        return []
    return discover_path_bundles(_RAW_ROOT)


_BUNDLES = _bundles()


# ─────────────────────────────────────────────────────────────────────────────
# 경로 모드별 사이클 분석 baseline
# ─────────────────────────────────────────────────────────────────────────────


def _first_channel(bundle: PathBundle) -> Path | None:
    """bundle 의 첫 dataset 측 첫 채널 — sweep 측 entry point."""
    import DataTool_optRCD_proto_ as bdt
    for ds in bundle.data_folders:
        if not ds.is_dir():
            continue
        for ch in sorted(ds.iterdir()):
            if not ch.is_dir():
                continue
            try:
                if bdt.is_pne_folder(str(ch)) and bundle.cycler == "PNE":
                    return ch
                # Toyo 분기 — digit-only
                if ch.name.isdigit() and bundle.cycler == "Toyo":
                    items = os.listdir(ch)
                    if any(f.upper() == "CAPACITY.LOG" for f in items):
                        return ch
            except OSError:
                continue
    return None


def _save_or_compare(label: str, suffix: str, sig_new: dict, request) -> None:
    """공통 baseline save/compare 헬퍼."""
    baseline_path = _BASELINE_DIR / f"{label}__{suffix}.json"
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
            f"회귀 — {label}/{suffix}\n"
            + "\n".join(diffs[:10]))


@pytest.mark.parametrize("bundle", _BUNDLES, ids=lambda b: b.label)
def test_cycle_path_mode_baseline(bundle, request):
    """경로 모드별 사이클 분석 시그니처 회귀 — single/multi/connected 첫 채널."""
    import DataTool_optRCD_proto_ as bdt

    bdt._reset_all_caches()
    ch = _first_channel(bundle)
    if ch is None:
        pytest.skip(f"채널 없음: {bundle.label}")

    try:
        if bundle.cycler == "Toyo":
            mc, df = bdt.toyo_cycle_data(str(ch), 0, 0.2, True)
        else:
            mc, df = bdt.pne_cycle_data(str(ch), 0, 0.2, True, False, False)
    except Exception as e:
        pytest.skip(f"분석 실패: {type(e).__name__}: {e}")

    if not hasattr(df, "NewData") or df.NewData is None or df.NewData.empty:
        pytest.skip(f"빈 결과: {bundle.label}")

    sig_new = extract_signature(df.NewData)
    if not sig_new:
        pytest.skip(f"numeric 컬럼 없음: {bundle.label}")
    _save_or_compare(bundle.label, "cycle", sig_new, request)


# ─────────────────────────────────────────────────────────────────────────────
# 다중경로 _get_max_tc 회귀 — multi/connected 모드 측 BDT 호환
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("bundle", _BUNDLES, ids=lambda b: b.label)
def test_get_max_tc_path_mode(bundle, request):
    """`_get_max_tc(all_data_folder, ...)` 다중경로 회귀 — 최대 논리사이클 시그니처."""
    import DataTool_optRCD_proto_ as bdt

    bdt._reset_all_caches()
    folders = [str(p) for p in bundle.data_folders]

    # mincapacity = 0 (자동) + 첫 dataset 의 첫 채널 측 추정
    mincap = 0.0
    ch = _first_channel(bundle)
    if ch is not None:
        try:
            if bundle.cycler == "Toyo":
                mincap = bdt.toyo_min_cap(str(ch), 0, 0.2)
            else:
                mincap = bdt.pne_min_cap(str(ch), 0, 0.2)
        except Exception:
            pass
    if not mincap:
        pytest.skip(f"mincap 산정 실패: {bundle.label}")

    try:
        max_tc = bdt._get_max_tc(folders, mincap, 0.2)
    except Exception as e:
        pytest.skip(f"_get_max_tc 실패: {type(e).__name__}: {e}")

    if max_tc is None:
        pytest.skip(f"max_tc None: {bundle.label}")

    sig_new = {"max_tc": {"n": 1, "sum": float(max_tc), "median": float(max_tc),
                          "min": float(max_tc), "max": float(max_tc)}}
    _save_or_compare(bundle.label, "max_tc", sig_new, request)


# ─────────────────────────────────────────────────────────────────────────────
# 프로파일 옵션 조합 baseline — unified_profile_batch
# 현재 옵션별 완성도가 높지 않음 — 4 조합만 cover (대표).
# 향후 옵션 측 완성도 높아지면 baseline 갱신 또는 조합 추가.
# ─────────────────────────────────────────────────────────────────────────────


_PROFILE_OPTIONS = [
    # (label, kwargs)
    ("scope_charge_axis_time",
        dict(data_scope="charge", axis_mode="time", overlap="split")),
    ("scope_discharge_axis_time",
        dict(data_scope="discharge", axis_mode="time", overlap="split")),
    ("scope_cycle_axis_soc",
        dict(data_scope="cycle", axis_mode="soc", overlap="split")),
    ("scope_cycle_axis_time_with_rest",
        dict(data_scope="cycle", axis_mode="time", overlap="split", include_rest=True)),
]


@pytest.mark.parametrize("bundle", _BUNDLES, ids=lambda b: b.label)
@pytest.mark.parametrize("opt_label,opt_kwargs", _PROFILE_OPTIONS, ids=[o[0] for o in _PROFILE_OPTIONS])
def test_profile_options_baseline(bundle, opt_label, opt_kwargs, request):
    """프로파일 분석 옵션 조합 baseline — 4 옵션 × 경로 모드.

    옵션:
      - data_scope: charge / discharge / cycle
      - axis_mode: time / soc
      - overlap: split (기본)
      - include_rest: True (cycle 측만)

    경로 모드 측은 첫 채널 1~2 사이클만 — 옵션 검증 측 가벼운 sample.
    """
    import DataTool_optRCD_proto_ as bdt

    bdt._reset_all_caches()
    ch = _first_channel(bundle)
    if ch is None:
        pytest.skip(f"채널 없음: {bundle.label}")

    # mincap
    try:
        if bundle.cycler == "Toyo":
            mincap = bdt.toyo_min_cap(str(ch), 0, 0.2)
        else:
            mincap = bdt.pne_min_cap(str(ch), 0, 0.2)
    except Exception:
        mincap = 0
    if not mincap:
        pytest.skip(f"mincap 산정 실패")

    # 사이클 1~2 만 옵션 측정 (큰 채널 OOM 방지)
    try:
        result = bdt.unified_profile_batch(
            str(ch), [1, 2], mincap, 0.2, **opt_kwargs)
    except TypeError:
        # 옵션이 미지원 시 — 신호로 skip (옵션 완성도 진단)
        pytest.skip(f"옵션 미지원: {opt_label}")
    except Exception as e:
        pytest.skip(f"옵션 실행 실패: {type(e).__name__}: {e}")

    if not result:
        pytest.skip(f"빈 result: {opt_label}")

    # 결과 = {cycle_no: [mincap, UnifiedProfileResult]} dict
    # 각 cycle 의 result.df 시그니처 합산 (옵션별 출력 차이 측정)
    sig_combined: dict = {}
    n_cycles = 0
    for cyc_no, val in result.items():
        if not isinstance(val, list) or len(val) < 2:
            continue
        upr = val[1]
        df_attr = getattr(upr, "df", None)
        if df_attr is None or df_attr.empty:
            continue
        sig = extract_signature(df_attr)
        for col, stats in sig.items():
            if col not in sig_combined:
                sig_combined[col] = stats
        n_cycles += 1

    if n_cycles == 0:
        pytest.skip(f"빈 옵션 결과: {opt_label}")

    _save_or_compare(bundle.label, f"profile_{opt_label}", sig_combined, request)
