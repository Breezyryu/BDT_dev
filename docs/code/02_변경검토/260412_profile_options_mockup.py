"""
BDT Profile 옵션 탭 — PyQt6 목업
스크린샷 기반 충실 재현 (Fusion 스타일)
"""
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QRadioButton, QCheckBox, QLineEdit, QPushButton,
    QLabel, QTabWidget, QButtonGroup, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont


# ── 스타일 상수 ──
FONT_FAMILY = "Malgun Gothic"
FONT_SIZE = 9          # pt
GROUPBOX_QSS = """
QGroupBox {
    font-weight: bold;
    border: 1px solid #BFBFBF;
    border-radius: 3px;
    margin-top: 10px;
    padding-top: 14px;
    background: #F7F7F7;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 8px;
    padding: 0 4px;
    background: #F0F0F0;
    color: #333;
}
"""
BTN_QSS = """
QPushButton {
    padding: 5px 18px;
    border: 1px solid #B0B0B0;
    border-radius: 3px;
    background: #F5F5F5;
    font-size: 9pt;
}
QPushButton:hover { background: #E0E0E0; }
QPushButton:pressed { background: #D0D0D0; }
QPushButton#primaryBtn {
    background: #3C5488;
    color: white;
    border-color: #3C5488;
    font-weight: bold;
}
QPushButton#primaryBtn:hover { background: #2D4070; }
QPushButton:disabled {
    color: #AAA;
    background: #EBEBEB;
    border-color: #C8C8C8;
}
"""
SMALL_BTN_QSS = """
QPushButton {
    padding: 1px 6px;
    border: 1px solid #B0B0B0;
    border-radius: 2px;
    background: #F5F5F5;
    font-size: 8pt;
    min-width: 22px;
    min-height: 16px;
}
QPushButton:hover { background: #E0E0E0; }
QPushButton:checked {
    background: #3C5488;
    color: white;
    border-color: #3C5488;
}
"""
LINEEDIT_QSS = """
QLineEdit {
    border: 1px solid #BFBFBF;
    border-radius: 2px;
    padding: 2px 4px;
    background: white;
    font-size: 9pt;
}
QLineEdit:focus {
    border-color: #3C5488;
}
"""


def _make_radio(text: str, checked: bool = False) -> QRadioButton:
    r = QRadioButton(text)
    r.setChecked(checked)
    return r


def _make_checkbox(text: str, checked: bool = False) -> QCheckBox:
    c = QCheckBox(text)
    c.setChecked(checked)
    return c


def _make_lineedit(text: str = "", width: int = 40) -> QLineEdit:
    le = QLineEdit(text)
    le.setFixedWidth(width)
    le.setAlignment(Qt.AlignmentFlag.AlignCenter)
    le.setStyleSheet(LINEEDIT_QSS)
    return le


def _make_label(text: str, bold: bool = False, color: str = "#333") -> QLabel:
    lbl = QLabel(text)
    font = QFont(FONT_FAMILY, FONT_SIZE)
    if bold:
        font.setBold(True)
    lbl.setFont(font)
    lbl.setStyleSheet(f"color: {color};")
    return lbl


class ProfileOptionsPanel(QWidget):
    """프로필 옵션 패널 — 스크린샷 충실 재현"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QWidget {{
                font-family: '{FONT_FAMILY}';
                font-size: {FONT_SIZE}pt;
                color: #1A1D23;
                background: #F0F0F0;
            }}
        """)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(4)

        # ═══════════════════════════════════════
        # 탭 위젯 (Cycle / Profile)
        # ═══════════════════════════════════════
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #C0C0C0;
                background: #F0F0F0;
            }
            QTabBar::tab {
                padding: 5px 16px;
                min-width: 60px;
                border: 1px solid #C0C0C0;
                border-bottom: none;
                background: #E8E8E8;
                margin-right: 1px;
            }
            QTabBar::tab:selected {
                background: #F0F0F0;
                font-weight: bold;
                border-bottom: 1px solid #F0F0F0;
            }
        """)

        # ── Cycle 탭 (빈 탭, 구조 표현용) ──
        cycle_page = QWidget()
        cycle_page.setStyleSheet("background: #F0F0F0;")
        tab_widget.addTab(cycle_page, "Cycle")

        # ── Profile 탭 ──
        profile_page = QWidget()
        profile_page.setStyleSheet("background: #F0F0F0;")
        profile_layout = QVBoxLayout(profile_page)
        profile_layout.setContentsMargins(6, 8, 6, 6)
        profile_layout.setSpacing(4)

        # ── 상단: 통합 모드 라디오 + 체크박스 ──
        top_row = QHBoxLayout()
        top_row.setSpacing(4)

        self.profile_view_group = QButtonGroup(self)
        rb_cyc = _make_radio("사이클 통합", checked=True)
        rb_cell = _make_radio("셀별 통합")
        rb_all = _make_radio("전체 통합")
        self.profile_view_group.addButton(rb_cyc, 0)
        self.profile_view_group.addButton(rb_cell, 1)
        self.profile_view_group.addButton(rb_all, 2)

        top_row.addWidget(rb_cyc)
        top_row.addWidget(rb_cell)
        top_row.addWidget(rb_all)

        self.chk_dqdv = _make_checkbox("dQdV", checked=True)
        self.chk_dqdv.setStyleSheet("""
            QCheckBox { spacing: 4px; }
            QCheckBox::indicator:checked { background: #3C5488; border: 1px solid #3C5488; border-radius: 2px; }
        """)
        top_row.addSpacing(8)
        top_row.addWidget(self.chk_dqdv)

        self.chk_coincell = _make_checkbox("코인셀")
        top_row.addSpacing(4)
        top_row.addWidget(self.chk_coincell)

        top_row.addStretch()
        profile_layout.addLayout(top_row)

        # ── TC 토글 + ▶ 버튼 (우측 정렬) ──
        tc_row = QHBoxLayout()
        tc_row.setSpacing(3)
        tc_row.addStretch()

        self.btn_tc = QPushButton("TC")
        self.btn_tc.setCheckable(True)
        self.btn_tc.setStyleSheet(SMALL_BTN_QSS)
        self.btn_tc.setFixedSize(28, 18)
        tc_row.addWidget(self.btn_tc)

        self.btn_detail = QPushButton("▶")
        self.btn_detail.setStyleSheet(SMALL_BTN_QSS)
        self.btn_detail.setFixedSize(22, 18)
        tc_row.addWidget(self.btn_detail)

        profile_layout.addLayout(tc_row)

        # ═══════════════════════════════════════
        # GroupBox 1: 데이터 범위
        # ═══════════════════════════════════════
        grp_data = QGroupBox("1. 데이터 범위")
        grp_data.setStyleSheet(GROUPBOX_QSS)
        g1_layout = QVBoxLayout(grp_data)
        g1_layout.setContentsMargins(8, 16, 8, 6)
        g1_layout.setSpacing(6)

        # Row 1: 데이터 + 연속성
        row_data = QHBoxLayout()
        row_data.setSpacing(3)
        row_data.addWidget(_make_label("데이터:"))

        self.scope_group = QButtonGroup(self)
        rb_scope_cyc = _make_radio("사이클", checked=False)
        rb_scope_chg = _make_radio("충전", checked=False)
        rb_scope_dchg = _make_radio("방전", checked=True)
        self.scope_group.addButton(rb_scope_cyc, 0)
        self.scope_group.addButton(rb_scope_chg, 1)
        self.scope_group.addButton(rb_scope_dchg, 2)
        row_data.addWidget(rb_scope_cyc)
        row_data.addWidget(rb_scope_chg)
        row_data.addWidget(rb_scope_dchg)

        row_data.addSpacing(12)
        row_data.addWidget(_make_label("연속성:"))

        self.cont_group = QButtonGroup(self)
        rb_overlay = _make_radio("오버레이")
        rb_cont = _make_radio("이어서")
        self.cont_group.addButton(rb_overlay, 0)
        self.cont_group.addButton(rb_cont, 1)
        # 스크린샷에서는 둘 다 미선택으로 보이지만, 기본값은 이어서
        rb_cont.setChecked(True)
        row_data.addWidget(rb_overlay)
        row_data.addWidget(rb_cont)
        row_data.addStretch()

        g1_layout.addLayout(row_data)

        # Row 2: X축 + 체크박스들
        row_xaxis = QHBoxLayout()
        row_xaxis.setSpacing(3)
        row_xaxis.addWidget(_make_label("X축:"))

        self.axis_group = QButtonGroup(self)
        rb_soc = _make_radio("SOC(DOD)")
        rb_time = _make_radio("시간", checked=True)
        self.axis_group.addButton(rb_soc, 0)
        self.axis_group.addButton(rb_time, 1)
        row_xaxis.addWidget(rb_soc)
        row_xaxis.addWidget(rb_time)

        row_xaxis.addSpacing(8)

        self.chk_rest = _make_checkbox("Rest", checked=True)
        self.chk_cv = _make_checkbox("CV", checked=True)
        self.chk_loop = _make_checkbox("루프")

        row_xaxis.addWidget(self.chk_rest)
        row_xaxis.addWidget(self.chk_cv)
        row_xaxis.addWidget(self.chk_loop)
        row_xaxis.addStretch()

        g1_layout.addLayout(row_xaxis)
        profile_layout.addWidget(grp_data)

        # ═══════════════════════════════════════
        # GroupBox 2: 그래프 옵션
        # ═══════════════════════════════════════
        grp_graph = QGroupBox("2. 그래프 옵션")
        grp_graph.setStyleSheet(GROUPBOX_QSS)
        g2_layout = QGridLayout(grp_graph)
        g2_layout.setContentsMargins(8, 16, 8, 6)
        g2_layout.setSpacing(4)
        g2_layout.setVerticalSpacing(6)

        # Row 0: Y축 최소 / Y축 / Y축 간격
        g2_layout.addWidget(_make_label("Y축 최소"), 0, 0)
        self.vol_min = _make_lineedit("2.5", 50)
        g2_layout.addWidget(self.vol_min, 0, 1)

        g2_layout.addWidget(_make_label("Y축 :"), 0, 2)
        self.vol_max = _make_lineedit("4.7", 50)
        g2_layout.addWidget(self.vol_max, 0, 3)

        g2_layout.addWidget(_make_label("Y축 간격"), 0, 4)
        self.vol_gap = _make_lineedit("0.1", 50)
        g2_layout.addWidget(self.vol_gap, 0, 5)

        # Row 1: Smooth / 컷오프 C-RATE
        g2_layout.addWidget(_make_label("Smooth (0 이면 자동)"), 1, 0, 1, 2)
        self.smooth = _make_lineedit("0", 50)
        g2_layout.addWidget(self.smooth, 1, 2)

        g2_layout.addWidget(_make_label("컷오프 C-RATE"), 1, 3, 1, 2)
        self.cutoff = _make_lineedit("0", 50)
        g2_layout.addWidget(self.cutoff, 1, 5)

        # Row 2: DQDV scale
        g2_layout.addWidget(_make_label("DQDV scale 늘리기"), 2, 0, 1, 2)
        self.dqdv_scale = _make_lineedit("1", 50)
        g2_layout.addWidget(self.dqdv_scale, 2, 2)

        profile_layout.addWidget(grp_graph)

        # ═══════════════════════════════════════
        # GroupBox 3: 프로필 분석
        # ═══════════════════════════════════════
        grp_action = QGroupBox("3. 프로필 분석")
        grp_action.setStyleSheet(GROUPBOX_QSS)
        g3_layout = QHBoxLayout(grp_action)
        g3_layout.setContentsMargins(8, 18, 8, 8)
        g3_layout.setSpacing(8)

        self.btn_profile = QPushButton("프로필 분석")
        self.btn_profile.setObjectName("primaryBtn")
        self.btn_profile.setStyleSheet(BTN_QSS)
        self.btn_profile.setMinimumHeight(30)

        self.btn_dcir = QPushButton("DCIR")
        self.btn_dcir.setStyleSheet(BTN_QSS)
        self.btn_dcir.setMinimumHeight(30)

        self.btn_reset = QPushButton("초기화")
        self.btn_reset.setStyleSheet(BTN_QSS)
        self.btn_reset.setMinimumHeight(30)
        self.btn_reset.setEnabled(False)  # 스크린샷에서 비활성

        g3_layout.addWidget(self.btn_profile)
        g3_layout.addWidget(self.btn_dcir)
        g3_layout.addWidget(self.btn_reset)

        profile_layout.addWidget(grp_action)
        profile_layout.addStretch()

        tab_widget.addTab(profile_page, "Profile")
        tab_widget.setCurrentIndex(1)  # Profile 탭 활성

        root.addWidget(tab_widget)


class MockupWindow(QWidget):
    """목업 윈도우"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("BDT — Profile 옵션 목업 (PyQt6)")
        self.setFixedSize(420, 430)
        self.setStyleSheet(f"""
            QWidget {{
                font-family: '{FONT_FAMILY}';
                font-size: {FONT_SIZE}pt;
                background: #F0F0F0;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(ProfileOptionsPanel(self))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MockupWindow()
    win.show()
    sys.exit(app.exec())
