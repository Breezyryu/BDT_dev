"""사이클데이터 탭 E2E 자동화 — 수동 검증 루틴 재현.

시나리오:
  S1. 경로 입력 → 사이클 분석 → 데이터 + Plot 검증
  S2. 경로 + TC 입력 → 프로파일 분석 (옵션별) → Plot 검증

pytest-qt가 QApplication 중복 생성에 민감하므로 개별 실행 권장:
  pytest DataTool_dev_code/test_code/test_cycle_tab_e2e.py::test_cycle_analysis_e2e_floating -m gui -v
  pytest DataTool_dev_code/test_code/test_cycle_tab_e2e.py::test_profile_options_rest_cv -m gui -v

일괄 실행은 --forked (각 테스트 별도 프로세스) 또는 pytest --dist=each 권장.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# test_code 디렉토리를 sys.path에 추가 (plot_verify import)
_TEST_CODE = Path(__file__).resolve().parent
if str(_TEST_CODE) not in sys.path:
    sys.path.insert(0, str(_TEST_CODE))

# exp_data 경로 (conftest fixture 대신 직접 계산 — 경로 버그 우회)
_EXP_DATA = _TEST_CODE.parent / "data" / "exp_data"


# ══════════════════════════════════════════════════════════════
# 헬퍼
# ══════════════════════════════════════════════════════════════

def _inject_path(app_window, row: int, path: str) -> None:
    """경로 테이블 특정 행에 경로 주입 (사용자 '붙여넣기' 재현)."""
    from PyQt6 import QtWidgets
    tbl = app_window.cycle_path_table
    while tbl.rowCount() <= row:
        tbl.insertRow(tbl.rowCount())
    tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(path))


def _set_table_cell(app_window, row: int, col: int, text: str) -> None:
    from PyQt6 import QtWidgets
    tbl = app_window.cycle_path_table
    tbl.setItem(row, col, QtWidgets.QTableWidgetItem(text))


def _clear_table(app_window) -> None:
    tbl = app_window.cycle_path_table
    for r in range(tbl.rowCount()):
        for c in range(tbl.columnCount()):
            tbl.setItem(r, c, None)


def _find_floating_ch55() -> Path | None:
    target = (_EXP_DATA / "복합floating"
              / "260413_261230_05_문현규_3650mAh_Cosmx 25SiC 타사spl floating ch55 61")
    return target if target.is_dir() else None


def _find_lifetime_1202() -> Path | None:
    for name in (
        "251029_260429_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 75CY @1-1202",
        "251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202",
    ):
        p = _EXP_DATA / "수명" / name
        if p.is_dir():
            return p
    return None


# ══════════════════════════════════════════════════════════════
# S1. 사이클 분석 E2E
# ══════════════════════════════════════════════════════════════

@pytest.mark.gui
def test_cycle_analysis_e2e_floating(app_window):
    """복합floating 데이터로 사이클 분석 end-to-end.

    수동 루틴 재현:
      1. 경로 테이블 주소 입력
      2. 자동 채우기 (_autofill)
      3. 사이클 분석 버튼
      4. 탭 추가 확인
      5. Figure 구조 + 데이터 검증
    """
    from plot_verify import (
        extract_current_tab_figure, verify_figure_structure,
        verify_axes_has_data,
    )

    target = _find_floating_ch55()
    if target is None:
        pytest.skip(f"테스트 데이터 없음: {_EXP_DATA}/복합floating/...")

    _clear_table(app_window)
    _inject_path(app_window, 0, str(target))

    # 2. 자동 채우기 — 채널/용량/TC 자동 산정
    app_window._autofill_table_empty_cells()

    # 자동 산정 결과 검증
    ch_val = app_window._get_table_cell(0, 2)
    cap_val = app_window._get_table_cell(0, 3)
    cyc_val = app_window._get_table_cell(0, 4)
    assert ch_val, f"채널 자동 산정 실패 (col2={ch_val!r})"
    assert cap_val, f"용량 자동 산정 실패 (col3={cap_val!r})"
    assert cyc_val, f"TC 자동 산정 실패 (col4={cyc_val!r})"

    # 3. 사이클 분석 실행
    pre_tab_count = app_window.cycle_tab.count()
    app_window.unified_cyc_confirm_button()

    # 4. 탭 추가
    post_tab_count = app_window.cycle_tab.count()
    assert post_tab_count > pre_tab_count, (
        f"사이클 분석 탭 미생성: {pre_tab_count} → {post_tab_count}"
    )

    # 5. Figure 검증
    fig = extract_current_tab_figure(app_window)
    assert fig is not None, "현재 탭에서 Figure 추출 실패"
    verify_figure_structure(fig)  # axes 수 변할 수 있어 강제 X
    axes = fig.get_axes()
    n_with_data = sum(1 for ax in axes if ax.get_lines())
    assert n_with_data >= 1, (
        f"데이터 있는 subplot 0개 / 전체 {len(axes)}"
    )


# ══════════════════════════════════════════════════════════════
# S2. 프로파일 분석 E2E (옵션 parametrize)
# ══════════════════════════════════════════════════════════════

PROFILE_OPT_CASES = [
    # (rest, cv, view_mode, tc_range) — floating ch55는 max_tc=3
    (True, True, "CycProfile", "2"),
    (False, True, "CycProfile", "2"),
    (True, False, "CycProfile", "2"),
    (True, True, "AllProfile", "1-3"),
]


@pytest.mark.gui
@pytest.mark.parametrize("rest_on,cv_on,view_mode,tc_range", PROFILE_OPT_CASES)
def test_profile_options_matrix(
    app_window, rest_on, cv_on, view_mode, tc_range,
):
    """프로파일 분석 옵션별 E2E 검증.

    각 (Rest, CV, view_mode, TC) 조합으로 실행 → crash 없음 + fig 구조 확인.
    """
    from plot_verify import (
        extract_current_tab_figure, verify_figure_structure,
        verify_axes_has_data, compute_fig_fingerprint,
    )

    target = _find_floating_ch55() or _find_lifetime_1202()
    if target is None:
        pytest.skip(f"테스트 데이터 없음")

    _clear_table(app_window)
    _inject_path(app_window, 0, str(target))
    app_window._autofill_table_empty_cells()

    # TC 사용자 입력 주입 (col4)
    _set_table_cell(app_window, 0, 4, tc_range)

    # 옵션 설정
    if hasattr(app_window, "profile_rest_chk"):
        app_window.profile_rest_chk.setChecked(rest_on)
    if hasattr(app_window, "profile_cv_chk"):
        app_window.profile_cv_chk.setChecked(cv_on)

    # view_mode 라디오
    for name in ("CycProfile", "CellProfile", "AllProfile"):
        if hasattr(app_window, name):
            getattr(app_window, name).setChecked(name == view_mode)

    pre = app_window.cycle_tab.count()
    try:
        app_window.unified_profile_confirm_button()
    except Exception as e:
        pytest.fail(
            f"프로파일 분석 crash: opts={rest_on,cv_on,view_mode,tc_range} — {e}"
        )

    # 데이터 없으면 탭 미생성이 정상 (1d002a9 커밋 반영)
    # 데이터 있으면 최소 1개 이상 추가
    post = app_window.cycle_tab.count()
    if post == pre:
        pytest.skip(f"데이터 없음 (옵션: {rest_on,cv_on,view_mode,tc_range})")

    # Figure 검증
    fig = extract_current_tab_figure(app_window)
    assert fig is not None, "Figure 추출 실패"
    axes = fig.get_axes()
    assert len(axes) >= 1, "axes 없음"
    n_with_data = sum(1 for ax in axes if ax.get_lines())
    assert n_with_data >= 1, (
        f"데이터 subplot 0 (opts={rest_on,cv_on,view_mode,tc_range})"
    )


# ══════════════════════════════════════════════════════════════
# S3. 사이클 + 프로파일 연속 실행 (통합 시나리오)
# ══════════════════════════════════════════════════════════════

@pytest.mark.gui
def test_cycle_then_profile_full_flow(app_window):
    """사용자 실제 워크플로우: 사이클 분석 → 프로파일 분석 연속."""
    from plot_verify import extract_all_tab_figures

    target = _find_floating_ch55()
    if target is None:
        pytest.skip("테스트 데이터 없음")

    _clear_table(app_window)
    _inject_path(app_window, 0, str(target))
    app_window._autofill_table_empty_cells()

    # Step 1: 사이클 분석
    pre = app_window.cycle_tab.count()
    app_window.unified_cyc_confirm_button()
    after_cyc = app_window.cycle_tab.count()
    assert after_cyc > pre, "사이클 분석 탭 미생성"

    # Step 2: TC 수동 입력 (col4)
    _set_table_cell(app_window, 0, 4, "2")

    # Step 3: 프로파일 분석 (기본 옵션)
    app_window.unified_profile_confirm_button()
    after_prof = app_window.cycle_tab.count()

    # 탭 최소 1개 이상 추가 또는 동일 (데이터 없음 케이스)
    assert after_prof >= after_cyc

    # 모든 탭에 Figure 존재 확인
    figs = extract_all_tab_figures(app_window)
    assert len(figs) >= 1
    for fig in figs:
        assert fig is not None
        assert len(fig.get_axes()) >= 1
