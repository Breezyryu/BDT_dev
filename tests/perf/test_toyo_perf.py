"""Toyo 성능 회귀 — A·B′·C′ 가속 효과 보존 검증.

실행:
  pytest tests/perf/test_toyo_perf.py -m perf --benchmark-only

baseline 저장:
  pytest tests/perf/test_toyo_perf.py -m perf --benchmark-save=baseline_2026_05_09

baseline 비교:
  pytest tests/perf/test_toyo_perf.py -m perf --benchmark-compare=baseline_2026_05_09

회귀 임계 (assertion):
  - 사이클 cold: ≤ 250 ms (큰 채널, A 단계 후 ~95 ms 의 ~2.5x 한계)
  - 사이클 warm: ≤ 100 ms (lru_cache hit, ~52 ms 의 ~2x)
  - Phase 0 build cold: ≤ 200 ms (B′ 후 ~90 ms 의 ~2x)
  - Profile 100cyc cold: ≤ 500 ms (A 후 ~230 ms 의 ~2x)
  - Profile 100cyc warm (C′ hit): ≤ 5 ms (~0.5 ms 의 10x)
"""
from __future__ import annotations

import pytest


# 회귀 임계 (A·B′·C′ 후 baseline 의 ~2x 안전 마진)
_THRESHOLDS_MS = {
    "cycle_cold":   250,
    "cycle_warm":   100,
    "build_cold":   200,
    "profile_cold": 500,
    "profile_warm":   5,
}


@pytest.mark.perf
def test_toyo_cycle_cold(benchmark, bdt, toyo_channel):
    """toyo_cycle_data cold — A 단계 (usecols + ThreadPool + agg) 후 회귀 검증."""
    def run():
        bdt._reset_all_caches()
        return bdt.toyo_cycle_data(toyo_channel["path"], 0, 0.2, True)
    result = benchmark.pedantic(run, rounds=3, iterations=1, warmup_rounds=0)
    mc, df = result
    assert hasattr(df, "NewData") and not df.NewData.empty
    elapsed_ms = benchmark.stats["mean"] * 1000
    assert elapsed_ms < _THRESHOLDS_MS["cycle_cold"], (
        f"cycle cold {elapsed_ms:.1f}ms > {_THRESHOLDS_MS['cycle_cold']}ms")


@pytest.mark.perf
def test_toyo_cycle_warm(benchmark, bdt, toyo_channel):
    """toyo_cycle_data warm — lru_cache hit 후 회귀 검증."""
    # 1차 호출로 cache 워밍
    bdt.toyo_cycle_data(toyo_channel["path"], 0, 0.2, True)
    def run():
        return bdt.toyo_cycle_data(toyo_channel["path"], 0, 0.2, True)
    benchmark.pedantic(run, rounds=5, iterations=1, warmup_rounds=0)
    elapsed_ms = benchmark.stats["mean"] * 1000
    assert elapsed_ms < _THRESHOLDS_MS["cycle_warm"], (
        f"cycle warm {elapsed_ms:.1f}ms > {_THRESHOLDS_MS['cycle_warm']}ms")


@pytest.mark.perf
def test_toyo_phase0_build_cold(benchmark, bdt, toyo_channel):
    """_build_channel_meta cold — B′ (_extract_tc_info_toyo 벡터화) 후 회귀 검증."""
    def run():
        bdt._reset_all_caches()
        return bdt._build_channel_meta(toyo_channel["path"], 0, 0.2)
    meta = benchmark.pedantic(run, rounds=3, iterations=1, warmup_rounds=0)
    assert meta is not None
    elapsed_ms = benchmark.stats["mean"] * 1000
    assert elapsed_ms < _THRESHOLDS_MS["build_cold"], (
        f"build cold {elapsed_ms:.1f}ms > {_THRESHOLDS_MS['build_cold']}ms")


@pytest.mark.perf
def test_toyo_profile_100cyc_cold(benchmark, bdt, toyo_channel):
    """_unified_toyo_load_raw cold — A2 (ThreadPool) 후 회귀 검증."""
    def run():
        bdt._reset_all_caches()
        return bdt._unified_toyo_load_raw(toyo_channel["path"], 1, 100, cycle_map=None)
    result = benchmark.pedantic(run, rounds=3, iterations=1, warmup_rounds=0)
    assert result is not None and not result.empty
    elapsed_ms = benchmark.stats["mean"] * 1000
    assert elapsed_ms < _THRESHOLDS_MS["profile_cold"], (
        f"profile 100cyc cold {elapsed_ms:.1f}ms > {_THRESHOLDS_MS['profile_cold']}ms")


@pytest.mark.perf
def test_toyo_profile_100cyc_warm_cprime(benchmark, bdt, toyo_channel):
    """_unified_toyo_load_raw warm — C′ (memory cache PNE mirror) 후 회귀 검증."""
    # 1차 호출로 cache 워밍
    bdt._unified_toyo_load_raw(toyo_channel["path"], 1, 100, cycle_map=None)
    def run():
        return bdt._unified_toyo_load_raw(toyo_channel["path"], 1, 100, cycle_map=None)
    benchmark.pedantic(run, rounds=10, iterations=1, warmup_rounds=0)
    elapsed_ms = benchmark.stats["mean"] * 1000
    assert elapsed_ms < _THRESHOLDS_MS["profile_warm"], (
        f"profile warm (C′ hit) {elapsed_ms:.1f}ms > {_THRESHOLDS_MS['profile_warm']}ms")
