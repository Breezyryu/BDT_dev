"""plot_verify.py — matplotlib Figure 검증 헬퍼 (Layer 4a).

Plot 결과를 "보이는 요소의 구조/숫자"로 검증.
이미지 비교(pytest-mpl) 없이도 회귀 방지 가능.

사용 예:
    fig = some_function_that_plots(...)
    verify_figure_structure(fig, n_axes=6)
    verify_axes_has_data(fig.get_axes()[0], min_lines=1)
    verify_monotonic(fig.get_axes()[0].get_lines()[0], axis='y', direction='any')
"""
from __future__ import annotations

import math
from typing import Iterable, Literal, Optional

import numpy as np


# ══════════════════════════════════════════════════════════════
# 구조 검증
# ══════════════════════════════════════════════════════════════

def verify_figure_structure(
    fig, n_axes: Optional[int] = None,
    suptitle: Optional[str] = None,
) -> None:
    """Figure의 기본 구조(axes 개수, suptitle) 검증."""
    assert fig is not None, "fig is None"
    axes = fig.get_axes()
    if n_axes is not None:
        assert len(axes) == n_axes, (
            f"axes 개수: 예상 {n_axes}, 실제 {len(axes)}"
        )
    if suptitle is not None:
        actual = fig._suptitle.get_text() if fig._suptitle else ""
        assert suptitle in actual, (
            f"suptitle 불일치: 예상 '{suptitle}' in '{actual}'"
        )


def verify_axes_has_data(
    ax, min_lines: int = 1, min_points_per_line: int = 2,
) -> None:
    """단일 axes에 데이터가 있는지 + 최소 라인/포인트 수."""
    lines = ax.get_lines()
    assert len(lines) >= min_lines, (
        f"라인 수 부족: 예상 ≥{min_lines}, 실제 {len(lines)}"
    )
    for i, line in enumerate(lines):
        x = line.get_xdata()
        y = line.get_ydata()
        assert len(x) >= min_points_per_line, (
            f"라인 {i}: 포인트 {len(x)}개 (<{min_points_per_line})"
        )
        assert not np.all(np.isnan(np.asarray(y, dtype=float))), (
            f"라인 {i}: 모든 y가 NaN"
        )


def verify_axes_xlim_within(
    ax, lo: float, hi: float, *, strict: bool = False,
) -> None:
    """xlim이 [lo, hi] 범위 안에 있는지."""
    xmin, xmax = ax.get_xlim()
    op = (lambda a, b: a >= b) if strict else (lambda a, b: a >= b - 1e-9)
    assert op(xmin, lo) and op(hi, xmax), (
        f"xlim [{xmin:.4g}, {xmax:.4g}] out of [{lo:g}, {hi:g}]"
    )


def verify_axes_ylim_within(ax, lo: float, hi: float) -> None:
    ymin, ymax = ax.get_ylim()
    assert ymin >= lo - 1e-9 and ymax <= hi + 1e-9, (
        f"ylim [{ymin:.4g}, {ymax:.4g}] out of [{lo:g}, {hi:g}]"
    )


# ══════════════════════════════════════════════════════════════
# 데이터 특성 검증
# ══════════════════════════════════════════════════════════════

def verify_monotonic(
    line, axis: Literal["x", "y"] = "y",
    direction: Literal["increasing", "decreasing", "any"] = "any",
    allow_eps: float = 1e-6,
) -> None:
    """line 데이터가 단조(증가/감소)인지.

    direction='any' → 둘 중 하나 만족하면 OK (충전/방전 자동 감지).
    """
    data = np.asarray(
        line.get_xdata() if axis == "x" else line.get_ydata(),
        dtype=float,
    )
    data = data[~np.isnan(data)]
    if len(data) < 2:
        return
    diffs = np.diff(data)
    inc_ok = np.all(diffs >= -allow_eps)
    dec_ok = np.all(diffs <= allow_eps)
    if direction == "increasing":
        assert inc_ok, f"단조증가 위반: min diff {float(diffs.min()):.4g}"
    elif direction == "decreasing":
        assert dec_ok, f"단조감소 위반: max diff {float(diffs.max()):.4g}"
    else:
        assert inc_ok or dec_ok, (
            f"단조성 위반 (inc/dec 모두 실패): "
            f"min={float(diffs.min()):.4g}, max={float(diffs.max()):.4g}"
        )


def verify_voltage_range(line, axis: Literal["x", "y"] = "y") -> None:
    """전압 데이터가 일반적인 배터리 범위(2.0~5.0V) 내."""
    data = np.asarray(
        line.get_xdata() if axis == "x" else line.get_ydata(),
        dtype=float,
    )
    valid = data[~np.isnan(data)]
    if len(valid) == 0:
        return
    vmin, vmax = float(valid.min()), float(valid.max())
    assert 2.0 <= vmin <= 5.0 and 2.0 <= vmax <= 5.0, (
        f"전압 범위 이상: [{vmin:.3f}, {vmax:.3f}] V"
    )


def verify_soc_range(line, axis: Literal["x", "y"] = "x") -> None:
    """SOC 데이터가 0~100% 또는 0~1 범위 내."""
    data = np.asarray(
        line.get_xdata() if axis == "x" else line.get_ydata(),
        dtype=float,
    )
    valid = data[~np.isnan(data)]
    if len(valid) == 0:
        return
    vmin, vmax = float(valid.min()), float(valid.max())
    # 허용: [0, 1] (비율) 또는 [0, 100] (%)
    if vmax <= 1.1:
        assert -0.05 <= vmin <= 1.05, f"SOC(비율) 이상: [{vmin:.3f}, {vmax:.3f}]"
    else:
        assert -5 <= vmin <= 105, f"SOC(%) 이상: [{vmin:.2f}, {vmax:.2f}]"


# ══════════════════════════════════════════════════════════════
# PyQt6 탭에서 Figure 추출
# ══════════════════════════════════════════════════════════════

def extract_current_tab_figure(app_window):
    """app_window의 현재 활성 탭에서 matplotlib Figure 추출.

    탭은 FigureCanvas를 포함하는 QWidget.
    """
    try:
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    except ImportError:
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg  # type: ignore

    tab_widget = app_window.cycle_tab
    current = tab_widget.currentWidget()
    if current is None:
        return None

    for child in current.findChildren(FigureCanvasQTAgg):
        return child.figure
    return None


def extract_all_tab_figures(app_window) -> list:
    """모든 탭의 Figure 추출 (탭 순서대로)."""
    try:
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    except ImportError:
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg  # type: ignore

    tab_widget = app_window.cycle_tab
    figs = []
    for i in range(tab_widget.count()):
        tab = tab_widget.widget(i)
        for child in tab.findChildren(FigureCanvasQTAgg):
            figs.append(child.figure)
            break
    return figs


# ══════════════════════════════════════════════════════════════
# 스크린샷 캡처 (수동 검토 + 향후 LLM 검토용)
# ══════════════════════════════════════════════════════════════

def save_fig_snapshot(fig, out_path: str, dpi: int = 100) -> str:
    """Figure를 PNG로 저장. 회귀 베이스라인 또는 LLM 검토용."""
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    return out_path


def compute_fig_fingerprint(fig) -> dict:
    """Figure의 "지문" — axes별 라인/데이터 요약. 회귀 비교 가능.

    baseline과 비교: 같은 수의 axes, 같은 라인 수,
    각 라인의 (x min/max, y min/max, n_points)가 근접.
    """
    axes = fig.get_axes()
    summary = {"n_axes": len(axes), "axes": []}
    for ax in axes:
        ax_info = {
            "n_lines": len(ax.get_lines()),
            "xlim": tuple(float(v) for v in ax.get_xlim()),
            "ylim": tuple(float(v) for v in ax.get_ylim()),
            "xlabel": ax.get_xlabel(),
            "ylabel": ax.get_ylabel(),
            "title": ax.get_title(),
            "lines": [],
        }
        for line in ax.get_lines():
            x = np.asarray(line.get_xdata(), dtype=float)
            y = np.asarray(line.get_ydata(), dtype=float)
            x_v = x[~np.isnan(x)]
            y_v = y[~np.isnan(y)]
            ax_info["lines"].append({
                "n": int(len(x)),
                "x_range": (
                    float(x_v.min()) if len(x_v) else None,
                    float(x_v.max()) if len(x_v) else None,
                ),
                "y_range": (
                    float(y_v.min()) if len(y_v) else None,
                    float(y_v.max()) if len(y_v) else None,
                ),
                "label": line.get_label(),
            })
        summary["axes"].append(ax_info)
    return summary


def compare_fingerprints(
    expected: dict, actual: dict, *, tol_rel: float = 0.05,
) -> list[str]:
    """두 지문 비교. 차이 문자열 리스트 반환 (빈 리스트 = 일치)."""
    diffs = []
    if expected.get("n_axes") != actual.get("n_axes"):
        diffs.append(
            f"axes 수 변경: {expected.get('n_axes')} → {actual.get('n_axes')}"
        )
        return diffs

    for i, (e, a) in enumerate(zip(expected["axes"], actual["axes"])):
        if e["n_lines"] != a["n_lines"]:
            diffs.append(
                f"axes[{i}] 라인 수: {e['n_lines']} → {a['n_lines']}"
            )
        # xlim/ylim 상대 허용
        for key in ("xlim", "ylim"):
            for j, (ev, av) in enumerate(zip(e[key], a[key])):
                if ev == 0:
                    if abs(av) > tol_rel:
                        diffs.append(f"axes[{i}] {key}[{j}]: {ev} → {av}")
                elif abs((av - ev) / max(abs(ev), 1e-9)) > tol_rel:
                    diffs.append(
                        f"axes[{i}] {key}[{j}]: {ev:.4g} → {av:.4g} "
                        f"(>{tol_rel*100:.0f}%)"
                    )
    return diffs
