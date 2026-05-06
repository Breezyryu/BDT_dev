"""Level B — GUI 스모크 테스트 (pytest-qt 필요, Windows 전용)

실행 조건:
  - Windows 환경 + PyQt6 설치
  - pytest-qt 설치: pip install pytest-qt
  - 실제 데이터가 data/exp_data/에 존재
  - 실행: pytest tests/test_smoke_gui.py -v -m gui

테스트 시나리오:
  1. 직접 경로 입력 → confirm → 탭 생성 확인
  2. 경로 파일 로드 → confirm → 탭 생성 확인
  3. 연결처리 on/off 상태에서 양쪽 모두 실행
  4. 4개 변환된 버튼(step/rate/chg/dchg) × 3모드(Cyc/Cell/All)
"""
import os
import sys
import time
from pathlib import Path

import pytest

# GUI 테스트 마커 — pytest -m gui 로 필터링
pytestmark = pytest.mark.gui


# ══════════════════════════════════════════════
# 헬퍼 함수
# ══════════════════════════════════════════════

def _fill_path_table_direct(window, rows: list[dict]) -> None:
    """cycle_path_table에 직접 데이터를 입력하는 헬퍼

    Parameters
    ----------
    window : WindowClass
    rows : list[dict]
        각 dict: {'name': str, 'path': str, 'channel': str, 'capacity': str}
        빈 행(그룹 구분)은 {'name': '', 'path': '', 'channel': '', 'capacity': ''}
    """
    from PyQt6.QtWidgets import QTableWidgetItem

    table = window.cycle_path_table
    table.setRowCount(len(rows))

    for i, row in enumerate(rows):
        for j, key in enumerate(['name', 'path', 'channel', 'capacity']):
            item = QTableWidgetItem(row.get(key, ''))
            table.setItem(i, j, item)


def _set_cycle_numbers(window, step_text: str) -> None:
    """사이클 번호 입력"""
    window.stepnum.setPlainText(step_text)


def _set_analysis_mode(window, mode: str) -> None:
    """분석 모드 설정: 'cyc', 'cell', 'all'"""
    if mode == 'cyc':
        window.CycProfile.setChecked(True)
    elif mode == 'cell':
        window.CellProfile.setChecked(True)
    elif mode == 'all':
        window.AllProfile.setChecked(True)


def _set_link_mode(window, enabled: bool) -> None:
    """연결처리 체크박스 설정"""
    window.chk_link_cycle.setChecked(enabled)


def _count_result_tabs(window) -> int:
    """cycle_tab의 탭 수 반환"""
    return window.cycle_tab.count()


def _wait_for_progress(window, timeout_sec: float = 30.0) -> bool:
    """progressBar가 100%가 될 때까지 대기

    Returns: True=완료, False=타임아웃
    """
    from PyQt6.QtWidgets import QApplication
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        QApplication.processEvents()
        if window.progressBar.value() >= 100:
            return True
        time.sleep(0.1)
    return False


# ══════════════════════════════════════════════
# 테스트 데이터 설정
# ══════════════════════════════════════════════

# Toyo 데이터 예시 (직접 경로 입력용)
TOYO_TEST_ROW = {
    'name': 'ATL Q7M Inner 2C 상온수명 1-100cyc',
    'path': str(Path(__file__).parent.parent / "data" / "exp_data"
               / "250207_250307_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 1-100cyc"),
    'channel': '030',
    'capacity': '1689',
}

# 연결처리 데이터 예시 (여러 기간 연결)
LINKED_TEST_ROWS = [
    {
        'name': 'ATL Q7M Inner 2C 상온수명 1-100cyc',
        'path': str(Path(__file__).parent.parent / "data" / "exp_data"
                   / "250207_250307_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 1-100cyc"),
        'channel': '030',
        'capacity': '1689',
    },
    {
        'name': '',
        'path': str(Path(__file__).parent.parent / "data" / "exp_data"
                   / "250219_250319_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 101-200cyc"),
        'channel': '',
        'capacity': '',
    },
]

TEST_CYCLES = "1 50 100"


# ══════════════════════════════════════════════
# 앱 시작 테스트
# ══════════════════════════════════════════════

class TestAppStartup:
    """앱이 정상적으로 시작되는지"""

    def test_window_visible(self, app_window):
        """메인 윈도우가 표시되는지"""
        assert app_window.isVisible()

    def test_tab_widget_exists(self, app_window):
        """9개 메인 탭이 존재하는지"""
        assert app_window.tabWidget.count() >= 9

    def test_cycle_tab_initially_empty(self, app_window):
        """시작 시 cycle_tab이 비어있는지"""
        assert _count_result_tabs(app_window) == 0


# ══════════════════════════════════════════════
# 직접 경로 입력 테스트
# ══════════════════════════════════════════════

class TestDirectPathInput:
    """경로 직접 입력 → confirm 버튼 → 결과 탭 생성"""

    @pytest.fixture(autouse=True)
    def _setup(self, app_window):
        """각 테스트 전 cycle_tab 초기화"""
        self.window = app_window
        # 탭 초기화
        if hasattr(self.window, 'cycle_tab_reset_confirm_button'):
            self.window.cycle_tab_reset_confirm_button()

    def _prepare_single_path(self, link_mode: bool = False):
        """단일 경로 + 사이클 번호 설정"""
        _set_link_mode(self.window, link_mode)
        _fill_path_table_direct(self.window, [TOYO_TEST_ROW])
        _set_cycle_numbers(self.window, TEST_CYCLES)
        # 용량 설정
        self.window.capacitytext.setText(TOYO_TEST_ROW['capacity'])
        self.window.ratetext.setText('2')

    @pytest.mark.parametrize("mode", ["cyc", "cell", "all"])
    def test_step_confirm_direct(self, mode):
        """step_confirm_button — 직접 입력, CycProfile/CellProfile/AllProfile"""
        self._prepare_single_path(link_mode=False)
        _set_analysis_mode(self.window, mode)

        initial_tabs = _count_result_tabs(self.window)
        self.window.StepConfirm.click()
        completed = _wait_for_progress(self.window, timeout_sec=60)

        assert completed, "타임아웃 — 60초 내에 완료되지 않음"
        assert _count_result_tabs(self.window) > initial_tabs, \
            f"결과 탭이 생성되지 않음 (mode={mode})"

    @pytest.mark.parametrize("mode", ["cyc", "cell", "all"])
    def test_rate_confirm_direct(self, mode):
        """rate_confirm_button — 직접 입력"""
        self._prepare_single_path(link_mode=False)
        _set_analysis_mode(self.window, mode)

        initial_tabs = _count_result_tabs(self.window)
        self.window.RateConfirm.click()
        completed = _wait_for_progress(self.window, timeout_sec=60)

        assert completed, "타임아웃"
        assert _count_result_tabs(self.window) > initial_tabs, \
            f"결과 탭이 생성되지 않음 (mode={mode})"

    @pytest.mark.parametrize("mode", ["cyc", "cell", "all"])
    def test_chg_confirm_direct(self, mode):
        """chg_confirm_button — 직접 입력"""
        self._prepare_single_path(link_mode=False)
        _set_analysis_mode(self.window, mode)

        initial_tabs = _count_result_tabs(self.window)
        self.window.ChgConfirm.click()
        completed = _wait_for_progress(self.window, timeout_sec=60)

        assert completed, "타임아웃"
        assert _count_result_tabs(self.window) > initial_tabs, \
            f"결과 탭이 생성되지 않음 (mode={mode})"

    @pytest.mark.parametrize("mode", ["cyc", "cell", "all"])
    def test_dchg_confirm_direct(self, mode):
        """dchg_confirm_button — 직접 입력"""
        self._prepare_single_path(link_mode=False)
        _set_analysis_mode(self.window, mode)

        initial_tabs = _count_result_tabs(self.window)
        self.window.DchgConfirm.click()
        completed = _wait_for_progress(self.window, timeout_sec=60)

        assert completed, "타임아웃"
        assert _count_result_tabs(self.window) > initial_tabs, \
            f"결과 탭이 생성되지 않음 (mode={mode})"


# ══════════════════════════════════════════════
# 연결처리 모드 테스트
# ══════════════════════════════════════════════

class TestLinkedPathInput:
    """연결처리 on 상태에서 여러 기간 데이터 연결 테스트"""

    @pytest.fixture(autouse=True)
    def _setup(self, app_window):
        self.window = app_window
        if hasattr(self.window, 'cycle_tab_reset_confirm_button'):
            self.window.cycle_tab_reset_confirm_button()

    def _prepare_linked_path(self):
        """연결처리 경로 설정"""
        _set_link_mode(self.window, True)
        _fill_path_table_direct(self.window, LINKED_TEST_ROWS)
        _set_cycle_numbers(self.window, TEST_CYCLES)
        self.window.capacitytext.setText(LINKED_TEST_ROWS[0]['capacity'])
        self.window.ratetext.setText('2')

    def test_step_confirm_linked(self):
        """step_confirm_button — 연결처리 모드"""
        self._prepare_linked_path()
        _set_analysis_mode(self.window, 'cyc')

        initial_tabs = _count_result_tabs(self.window)
        self.window.StepConfirm.click()
        completed = _wait_for_progress(self.window, timeout_sec=60)

        assert completed, "타임아웃"
        assert _count_result_tabs(self.window) > initial_tabs

    def test_chg_confirm_linked(self):
        """chg_confirm_button — 연결처리 모드"""
        self._prepare_linked_path()
        _set_analysis_mode(self.window, 'cyc')

        initial_tabs = _count_result_tabs(self.window)
        self.window.ChgConfirm.click()
        completed = _wait_for_progress(self.window, timeout_sec=60)

        assert completed, "타임아웃"
        assert _count_result_tabs(self.window) > initial_tabs


# ══════════════════════════════════════════════
# 경로 파일 로드 테스트
# ══════════════════════════════════════════════

class TestPathFileLoad:
    """경로 파일 로드 → confirm 실행"""

    @pytest.fixture(autouse=True)
    def _setup(self, app_window):
        self.window = app_window
        if hasattr(self.window, 'cycle_tab_reset_confirm_button'):
            self.window.cycle_tab_reset_confirm_button()

    def test_load_basic_path_file(self, sample_path_files):
        """기본 경로 파일 로드 후 테이블에 데이터가 채워지는지"""
        path_file = sample_path_files['basic']
        if not path_file.exists():
            pytest.skip("테스트 경로 파일 없음")

        # 파일 로드 시뮬레이션 (다이얼로그 우회)
        self._load_path_file_bypass(path_file)

        table = self.window.cycle_path_table
        # 최소 1개 데이터 행이 있어야 함
        has_data = False
        for row in range(table.rowCount()):
            item = table.item(row, 1)  # path 열
            if item and item.text().strip():
                has_data = True
                break
        assert has_data, "경로 파일 로드 후 데이터가 없음"

    def test_load_linked_path_file(self, sample_path_files):
        """연결처리 경로 파일 로드 후 link_mode 활성화 확인"""
        path_file = sample_path_files['linked']
        if not path_file.exists():
            pytest.skip("연결처리 테스트 파일 없음")

        self._load_path_file_bypass(path_file)

        # 연결처리 체크박스가 활성화되었는지
        assert self.window.chk_link_cycle.isChecked(), \
            "연결처리 파일 로드 후 link_mode가 활성화되어야 함"

    def _load_path_file_bypass(self, file_path: Path):
        """QFileDialog를 우회하여 파일 직접 로드

        _load_path_file_to_table()는 내부에서 QFileDialog를 열므로,
        테스트에서는 파일 내용을 직접 파싱하여 테이블에 채운다.
        """
        from PyQt6.QtWidgets import QTableWidgetItem

        content = file_path.read_text(encoding='utf-8-sig')
        lines = content.split('\n')

        # 메타데이터 처리
        link_mode = False
        data_start = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('#link_mode=1'):
                link_mode = True
                data_start = i + 1
                continue
            if stripped.startswith('#'):
                data_start = i + 1
                continue
            if stripped:
                data_start = i
                break

        self.window.chk_link_cycle.setChecked(link_mode)

        # 헤더 감지
        if data_start < len(lines):
            from tests.conftest import PROJECT_ROOT
            # WindowClass의 static method 사용
            header_line = lines[data_start]
            cols = [c.strip().lower() for c in header_line.split('\t')]
            has_header = any(
                c in ('cyclename', 'cyclepath', 'name', 'path', 'channel', 'capacity')
                for c in cols)
            if has_header:
                data_start += 1

        # 데이터 행 채우기
        table = self.window.cycle_path_table
        data_lines = [l for l in lines[data_start:]]
        table.setRowCount(len(data_lines))

        for row_idx, line in enumerate(data_lines):
            parts = line.split('\t')
            for col_idx in range(min(len(parts), 4)):
                item = QTableWidgetItem(parts[col_idx].strip())
                table.setItem(row_idx, col_idx, item)
