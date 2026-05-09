"""BDT 회귀 검증 인프라 — exp_data 전수 채널 자동 발견 + 시그니처 추출.

ADR-0008 fixture α/β 측 layer. 사이클·프로파일 분석의 byte-level / signature
회귀 검증을 자동화. 임계 의존성 X — 표준 라이브러리 + numpy/pandas 만 사용.

설계 원칙:
- 채널 발견은 cycler 판별 함수 (`is_pne_folder`) 와 빈 채널 정책
  ([[260509_policy_toyo_data_operation]] §4) 에 정합.
- 시그니처 = 컬럼별 (n, sum, median, min, max) — NaN-safe, byte-level 보다
  ~10000x 작은 baseline (1 MB / 452 채널).
- byte-level 모드는 옵션 (대표 채널만, parquet baseline).
"""
from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import sys

# BDT 본 모듈 (lazy)
_BDT = None


def _bdt():
    global _BDT
    if _BDT is None:
        import DataTool_optRCD_proto_ as bdt
        _BDT = bdt
    return _BDT


@dataclass(frozen=True)
class ChannelInfo:
    """전수 회귀 측 채널 메타.

    Fields:
        path: 채널 폴더 절대 경로 (Path)
        label: 회귀 fixture key 측 unique 라벨 — `<category>__<dataset>__<ch>`
        category: exp_data 직속 카테고리 (성능/수명/수명_Toyo/...)
        cycler: 'PNE' or 'Toyo'
    """
    path: Path
    label: str
    category: str
    cycler: str


def _is_toyo_channel(ch_path: Path) -> bool:
    """Toyo 채널 판별 — 폴더명 digit + CAPACITY.LOG 또는 NNNNNN 존재."""
    name = ch_path.name
    if not name.isdigit():
        return False
    try:
        items = os.listdir(ch_path)
    except OSError:
        return False
    has_caplog = any(f.upper() == "CAPACITY.LOG" for f in items)
    has_nnnnnn = any(f.isdigit() and len(f) == 6 for f in items)
    return has_caplog or has_nnnnnn


def _is_empty_toyo(ch_path: Path) -> bool:
    """빈 Toyo 채널 — NNNNNN 0개 ∧ CAPACITY.LOG 부재 ([[260509_policy_toyo_data_operation]] §A1)."""
    try:
        items = os.listdir(ch_path)
    except OSError:
        return True
    has_caplog = any(f.upper() == "CAPACITY.LOG" for f in items)
    nnnnnn = [f for f in items if f.isdigit() and len(f) == 6]
    return not has_caplog and not nnnnnn


def _label(category: str, dataset: str, ch_name: str) -> str:
    """unique 라벨 — fixture key 측."""
    # 비-ASCII / 공백 / 특수문자 → underscore (parquet 파일명 측 정합)
    def _slug(s: str) -> str:
        return "".join(c if c.isalnum() else "_" for c in s).strip("_")
    return f"{_slug(category)}__{_slug(dataset)[:60]}__{_slug(ch_name)}"


def discover_channels(exp_data_root: str | Path) -> list[ChannelInfo]:
    """exp_data root → 전수 채널 list.

    구조 가정:
        exp_data/<category>/<dataset>/<channel>/...

    PNE 채널: `is_pne_folder()` 양의 분기 (M01Ch008[008] 패턴 등).
    Toyo 채널: digit-only 폴더명 + CAPACITY.LOG/NNNNNN 존재.
    빈 채널 자동 skip.
    """
    bdt = _bdt()
    root = Path(exp_data_root)
    if not root.is_dir():
        return []

    out: list[ChannelInfo] = []
    for cat_path in sorted(root.iterdir()):
        if not cat_path.is_dir():
            continue
        category = cat_path.name
        for ds_path in sorted(cat_path.iterdir()):
            if not ds_path.is_dir():
                continue
            dataset = ds_path.name
            for ch_path in sorted(ds_path.iterdir()):
                if not ch_path.is_dir():
                    continue
                ch_name = ch_path.name
                # PNE 분기
                try:
                    is_pne = bdt.is_pne_folder(str(ch_path))
                except Exception:
                    is_pne = False
                if is_pne:
                    out.append(ChannelInfo(
                        path=ch_path,
                        label=_label(category, dataset, ch_name),
                        category=category,
                        cycler="PNE",
                    ))
                    continue
                # Toyo 분기
                if _is_toyo_channel(ch_path):
                    if _is_empty_toyo(ch_path):
                        continue  # 빈 채널 skip
                    out.append(ChannelInfo(
                        path=ch_path,
                        label=_label(category, dataset, ch_name),
                        category=category,
                        cycler="Toyo",
                    ))
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Signature 추출 + 비교 — byte-level 보다 가벼운 회귀 unit
# ─────────────────────────────────────────────────────────────────────────────


def extract_signature(df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """DataFrame → numeric 컬럼별 (n, sum, median, min, max) dict.

    NaN-safe (dropna 후 통계). string / object 컬럼 무시.
    동일 DataFrame → 동일 dict (`signatures_equal` 측 사용).

    Returns
    -------
    dict[col_name, dict[stat_name, value]]
        col_name: 컬럼 이름
        stat_name ∈ {'n', 'sum', 'median', 'min', 'max'}
        value: float | int | None (모든 NaN 컬럼은 sum/median/min/max=None)
    """
    if df is None or df.empty:
        return {}
    out: dict[str, dict[str, Any]] = {}
    for col in df.columns:
        s = df[col]
        # numeric 만 — string/object 무시
        if not np.issubdtype(s.dtype, np.number):
            continue
        v = s.dropna()
        n = int(len(v))
        if n == 0:
            out[col] = {"n": 0, "sum": None, "median": None,
                        "min": None, "max": None}
            continue
        out[col] = {
            "n": n,
            "sum": float(v.sum()),
            "median": float(v.median()),
            "min": float(v.min()),
            "max": float(v.max()),
        }
    return out


def _stat_eq(a: Any, b: Any, *, rel_tol: float = 0.0, abs_tol: float = 0.0) -> bool:
    """단일 stat 비교 — None / NaN / float 모두 처리."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    # int 일치
    if isinstance(a, int) and isinstance(b, int):
        return a == b
    # float — NaN 양쪽 동일 → equal
    fa, fb = float(a), float(b)
    if math.isnan(fa) and math.isnan(fb):
        return True
    if math.isnan(fa) or math.isnan(fb):
        return False
    if rel_tol == 0.0 and abs_tol == 0.0:
        return fa == fb  # byte-level
    return math.isclose(fa, fb, rel_tol=rel_tol, abs_tol=abs_tol)


def signatures_equal(
    sig_a: dict[str, dict[str, Any]],
    sig_b: dict[str, dict[str, Any]],
    *,
    rel_tol: float = 0.0,
    abs_tol: float = 0.0,
) -> bool:
    """두 시그니처 dict 비교 — byte-level (default) 또는 허용 오차.

    Default rel_tol=abs_tol=0 → 정확 일치 (byte-level).
    NaN-safe — 양쪽 NaN 이면 동일.
    """
    if set(sig_a.keys()) != set(sig_b.keys()):
        return False
    for col in sig_a:
        sa, sb = sig_a[col], sig_b[col]
        if set(sa.keys()) != set(sb.keys()):
            return False
        for stat in sa:
            if not _stat_eq(sa[stat], sb[stat], rel_tol=rel_tol, abs_tol=abs_tol):
                return False
    return True


def signature_diff(
    sig_a: dict[str, dict[str, Any]],
    sig_b: dict[str, dict[str, Any]],
    *,
    rel_tol: float = 0.0,
    abs_tol: float = 0.0,
) -> list[str]:
    """차이 list — 회귀 시 사용자 진단 측 보고서 메시지."""
    diffs: list[str] = []
    keys_a = set(sig_a.keys())
    keys_b = set(sig_b.keys())
    only_a = keys_a - keys_b
    only_b = keys_b - keys_a
    if only_a:
        diffs.append(f"missing in new: {sorted(only_a)[:5]}")
    if only_b:
        diffs.append(f"new columns: {sorted(only_b)[:5]}")
    for col in sorted(keys_a & keys_b):
        sa, sb = sig_a[col], sig_b[col]
        for stat in sorted(set(sa.keys()) & set(sb.keys())):
            if not _stat_eq(sa[stat], sb[stat], rel_tol=rel_tol, abs_tol=abs_tol):
                diffs.append(f"{col}.{stat}: {sa[stat]} vs {sb[stat]}")
    return diffs
