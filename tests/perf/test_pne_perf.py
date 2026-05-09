"""PNE 성능 회귀 — 기존 가속 효과 보존 검증.

PNE 측 가속 현황 (2026-05-09 측정):
  - `_extract_tc_info_pne` 이미 벡터화 (5 ms / 765 TC)
  - `_unified_pne_load_raw` 이미 cache 적용 (`unified_raw` single-entry)
  - **핫스팟**: `_cached_pne_restore_files` 292 ms (Phase 0 build 339 ms 의 87%)
    → 향후 Toyo A1 (usecols) mirror 적용 시 가속 가능 (별도 트랙)

실행: pytest tests/perf/test_pne_perf.py -m perf --benchmark-only
"""
from __future__ import annotations

import pytest


_THRESHOLDS_MS = {
    "cycle_cold":         500,   # PNE cold 302 ms 의 ~1.7x
    "cycle_warm":          50,   # PNE warm 14.5 ms 의 ~3x
    "build_cold":         500,   # 339 ms 의 ~1.5x
    "extract_tc_info":     20,   # 5 ms 의 ~4x (벡터화 보존)
    "restore_files_cold": 500,   # 292 ms 의 ~1.7x (핫스팟 — 향후 가속 trigger 영역)
}


@pytest.mark.perf
def test_pne_cycle_cold(benchmark, bdt, pne_channel):
    """pne_cycle_data cold — Phase 0 + DCIR 회귀 검증."""
    def run():
        bdt._reset_all_caches()
        return bdt.pne_cycle_data(pne_channel["path"], 0, 0.2, True, False, False)
    result = benchmark.pedantic(run, rounds=3, iterations=1, warmup_rounds=0)
    mc, df = result
    assert hasattr(df, "NewData") and not df.NewData.empty
    elapsed_ms = benchmark.stats["mean"] * 1000
    assert elapsed_ms < _THRESHOLDS_MS["cycle_cold"], (
        f"cycle cold {elapsed_ms:.1f}ms > {_THRESHOLDS_MS['cycle_cold']}ms")


@pytest.mark.perf
def test_pne_cycle_warm(benchmark, bdt, pne_channel):
    """pne_cycle_data warm — cache hit 회귀 검증."""
    bdt.pne_cycle_data(pne_channel["path"], 0, 0.2, True, False, False)
    def run():
        return bdt.pne_cycle_data(pne_channel["path"], 0, 0.2, True, False, False)
    benchmark.pedantic(run, rounds=5, iterations=1, warmup_rounds=0)
    elapsed_ms = benchmark.stats["mean"] * 1000
    assert elapsed_ms < _THRESHOLDS_MS["cycle_warm"], (
        f"cycle warm {elapsed_ms:.1f}ms > {_THRESHOLDS_MS['cycle_warm']}ms")


@pytest.mark.perf
def test_pne_phase0_build_cold(benchmark, bdt, pne_channel):
    """_build_channel_meta cold — Phase 0 전체 회귀 검증."""
    def run():
        bdt._reset_all_caches()
        return bdt._build_channel_meta(pne_channel["path"], 0, 0.2)
    meta = benchmark.pedantic(run, rounds=3, iterations=1, warmup_rounds=0)
    assert meta is not None
    elapsed_ms = benchmark.stats["mean"] * 1000
    assert elapsed_ms < _THRESHOLDS_MS["build_cold"], (
        f"build cold {elapsed_ms:.1f}ms > {_THRESHOLDS_MS['build_cold']}ms")


@pytest.mark.perf
def test_pne_extract_tc_info(benchmark, bdt, pne_channel):
    """_extract_tc_info_pne — 이미 벡터화된 함수 회귀 보장 (Toyo B′ 와 동일 기준)."""
    bdt._reset_all_caches()
    save_end = bdt.get_channel_save_end_data(pne_channel["path"])
    if save_end is None:
        pytest.skip("SaveEndData 없음")
    def run():
        return bdt._extract_tc_info_pne(save_end, 2335)
    result = benchmark.pedantic(run, rounds=10, iterations=1, warmup_rounds=0)
    assert len(result) > 0
    elapsed_ms = benchmark.stats["mean"] * 1000
    assert elapsed_ms < _THRESHOLDS_MS["extract_tc_info"], (
        f"extract_tc_info {elapsed_ms:.1f}ms > {_THRESHOLDS_MS['extract_tc_info']}ms")


@pytest.mark.perf
def test_pne_restore_files_cold(benchmark, bdt, pne_channel):
    """_cached_pne_restore_files cold — Phase 0 핫스팟 추적 (향후 가속 trigger 영역)."""
    def run():
        bdt._reset_all_caches()
        return bdt._cached_pne_restore_files(pne_channel["path"])
    save_end, fi, sf = benchmark.pedantic(run, rounds=3, iterations=1, warmup_rounds=0)
    assert save_end is not None
    elapsed_ms = benchmark.stats["mean"] * 1000
    assert elapsed_ms < _THRESHOLDS_MS["restore_files_cold"], (
        f"restore cold {elapsed_ms:.1f}ms > {_THRESHOLDS_MS['restore_files_cold']}ms")
