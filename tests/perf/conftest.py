"""성능 회귀 fixture — Toyo·PNE 표준 채널.

ADR-0008 정합 측 (α) 표준 데이터 경로 fixture. 사외 PC 측 raw 경로 의존이라
실제 fixture 사용은 raw 데이터 접근 가능 환경에서만 작동.

raw 경로 환경변수 `BDT_RAW_ROOT` (기본: `C:/Users/Ryu/battery/python/BDT_dev/raw`)
로 override 가능.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


# BDT 본 코드 import path
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "DataTool_dev_code"))


def _raw_root() -> Path:
    """raw 데이터 root 경로."""
    env = os.environ.get("BDT_RAW_ROOT")
    if env:
        return Path(env)
    return Path("C:/Users/Ryu/battery/python/BDT_dev/raw")


# 표준 5채널 fixture — 다양한 step 수 + Toyo/PNE
TOYO_LIFE_ROOT = _raw_root() / "raw_exp" / "exp_data" / "수명_Toyo"
PNE_LIFE_ROOT = _raw_root() / "raw_exp" / "exp_data" / "수명"


_TOYO_CHANNELS = {
    # (label, sub_path, expected_steps)
    "Q7M_Inner_BLK1_4956": (
        "Q7M Inner ATL_45V 1689mAh BLK1 20EA [23] - 250304/11", 4956),
    "Q7M_Sub_5841": (
        "Q7M Sub ATL [45v 2068mAh] [23] - 250219r/10", 5841),
    "M1_1717": (
        "M1 ATL [45V 4175mAh]/10", 1717),
    "Kim_245_796": (
        "260318_260428_3_김건희_245mAh_ATL JINJU  SUS 상온장수명 601-800/22", 796),
}

_PNE_CHANNELS = {
    "M01Ch008_765TC": (
        "251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202/M01Ch008[008]", 765),
    "M01Ch014_764TC": (
        "251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202/M01Ch014[014]", 764),
}


def _resolve(root: Path, sub: str) -> Path:
    """Windows 백슬래시 정규화 + 존재 확인."""
    p = root / sub.replace("/", os.sep)
    return p


@pytest.fixture(scope="session", params=list(_TOYO_CHANNELS.keys()))
def toyo_channel(request):
    """Toyo 채널 4종 — 4956 / 5841 / 1717 / 796 step."""
    label = request.param
    sub, n_steps = _TOYO_CHANNELS[label]
    p = _resolve(TOYO_LIFE_ROOT, sub)
    if not p.is_dir():
        pytest.skip(f"raw 경로 없음: {p}")
    return {"label": label, "path": str(p), "n_steps": n_steps, "cycler": "Toyo"}


@pytest.fixture(scope="session", params=list(_PNE_CHANNELS.keys()))
def pne_channel(request):
    """PNE 채널 2종 — 765 / 764 TC."""
    label = request.param
    sub, n_tc = _PNE_CHANNELS[label]
    p = _resolve(PNE_LIFE_ROOT, sub)
    if not p.is_dir():
        pytest.skip(f"raw 경로 없음: {p}")
    return {"label": label, "path": str(p), "n_tc": n_tc, "cycler": "PNE"}


@pytest.fixture(scope="function")
def bdt():
    """BDT 본 모듈 import + 캐시 reset (테스트 간 격리)."""
    import DataTool_optRCD_proto_ as _bdt
    _bdt._reset_all_caches()
    yield _bdt
    _bdt._reset_all_caches()
