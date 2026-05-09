"""전수 인벤토리 — exp_data 측 채널 자동 발견.

ADR-0008 fixture α 측 채널 발견 layer. 회귀 검증의 source.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


# 본 코드 import
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "DataTool_dev_code"))

from bdt_regression import discover_channels, ChannelInfo  # noqa: E402


_RAW_ROOT = Path(os.environ.get(
    "BDT_RAW_ROOT",
    "C:/Users/Ryu/battery/python/BDT_dev/raw"
)) / "raw_exp" / "exp_data"


def test_discover_channels_returns_list():
    """ChannelInfo 객체의 list 반환."""
    channels = discover_channels(_RAW_ROOT)
    assert isinstance(channels, list)
    assert all(isinstance(c, ChannelInfo) for c in channels)


def test_discover_channels_finds_both_cyclers():
    """PNE + Toyo 두 사이클러 모두 발견."""
    channels = discover_channels(_RAW_ROOT)
    cyclers = {c.cycler for c in channels}
    assert "PNE" in cyclers
    assert "Toyo" in cyclers


def test_discover_channels_skips_empty():
    """빈 채널 (NNNNNN 0개, CAPACITY.LOG 부재) 자동 skip."""
    channels = discover_channels(_RAW_ROOT)
    # 빈 채널 — 222mAh 측 4 채널은 발견 list 에 없어야 함
    paths = {str(c.path) for c in channels}
    empty_dataset = "260115_260130_3_김건희_222mAh_ATL JINJU SUS 상온수명 1-100"
    assert not any(empty_dataset in p for p in paths), \
        f"빈 dataset 채널이 발견됨"


def test_discover_channels_total_count():
    """전수 인벤토리 — 452 ± 5% 범위 (실제 raw 데이터 의존)."""
    channels = discover_channels(_RAW_ROOT)
    # 측정 baseline (2026-05-09): PNE 292 + Toyo 160 = 452
    assert 430 <= len(channels) <= 480, \
        f"채널 수 {len(channels)} (예상 452 ± 5%)"


def test_discover_channels_provides_label():
    """각 ChannelInfo 가 unique label (회귀 fixture key 측 사용)."""
    channels = discover_channels(_RAW_ROOT)
    labels = [c.label for c in channels]
    assert len(labels) == len(set(labels)), "label 중복"
