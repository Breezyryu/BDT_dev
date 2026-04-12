"""
BDT Cycle / Profile 탭 — UX 개선 PyQt6 목업
Before(현행) / After(개선안) 탭 전환으로 비교
Windows PC에서 실행: python 260412_cycle_profile_ux_mockup.py
"""
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QRadioButton, QCheckBox, QLineEdit, QPushButton,
    QLabel, QTabWidget, QButtonGroup, QFrame, QSizePolicy,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea,
    QAbstractItemView, QStyleFactory,
)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette, QPainter, QPen, QBrush

# ═══════════════════════════════════════════
# 스타일 상수
# ═══════════════════════════════════════════
FONT_FAMILY = "Malgun Gothic"
FONT_SIZE = 9
NAVY = "#3C5488"
RED = "#E64B35"
TEAL = "#00A087"
CYAN = "#4DBBD5"
BG = "#F0F0F0"
BG_LIGHT = "#F7F7F7"
BG_FIELD = "#FAFAFA"

GLOBAL_QSS = f"""
QWidget {{
    font-family: '{FONT_FAMILY}', 'Segoe UI', sans-serif;
    font-size: {FONT_SIZE}pt;
    color: #1A1D23;
}}
QGroupBox {{
    font-weight: bold;
    border: 1px solid #BFBFBF;
    border-radius: 3px;
    margin-top: 10px;
    padding-top: 16px;
    background: {BG_LIGHT};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 8px;
    padding: 0 4px;
    background: {BG};
    color: #333;
}}
QLineEdit {{
    border: 1px solid #BFBFBF;
    border-radius: 2px;
    padding: 2px 5px;
    background: white;
    font-size: {FONT_SIZE}pt;
}}
QLineEdit:focus {{
    border-color: {NAVY};
}}
QPushButton {{
    padding: 5px 16px;
    border: 1px solid #B0B0B0;
    border-radius: 3px;
    background: #F5F5F5;
    font-size: {FONT_SIZE}pt;
}}
QPushButton:hover {{ background: #E0E0E0; }}
QPushButton:pressed {{ background: #D0D0D0; }}
QPushButton:disabled {{ color: #AAA; background: #EBEBEB; border-color: #C8C8C8; }}
QTabWidget::pane {{
    border: 1px solid #C0C0C0;
    background: {BG};
}}
QTabBar::tab {{
    padding: 5px 14px;
    border: 1px solid #C0C0C0;
    border-bottom: none;
    background: #E8E8E8;
    margin-right: 1px;
}}
QTabBar::tab:selected {{
    background: {BG};
    font-weight: bold;
    border-bottom: 1px solid {BG};
}}
QTableWidget {{
    border: 1px solid #BFBFBF;
    gridline-color: #E8E8E8;
    background: white;
    font-size: 8.5pt;
}}
QTableWidget::item {{
    padding: 2px 4px;
}}
QHeaderView::section {{
    background: #F0F0F0;
    border: none;
    border-right: 1px solid #D0D0D0;
    border-bottom: 1px solid #C0C0C0;
    padding: 3px 5px;
    font-weight: 600;
    font-size: 8.5pt;
}}
QScrollArea {{
    border: none;
    background: {BG};
}}
"""

# ═══════════════════════════════════════════
# 커스텀 위젯: Segmented Control
# ═══════════════════════════════════════════
class SegmentedControl(QWidget):
    """2~4개 옵션의 세그먼트 컨트롤 (토글 버튼 그룹)"""

    def __init__(self, labels: list[str], default: int = 0, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.buttons: list[QPushButton] = []

        for i, text in enumerate(labels):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setChecked(i == default)
            btn.setMinimumHeight(22)
            btn.setStyleSheet(self._btn_qss(i, len(labels)))
            self.group.addButton(btn, i)
            self.buttons.append(btn)
            layout.addWidget(btn)

    @staticmethod
    def _btn_qss(index: int, total: int) -> str:
        """세그먼트 위치별 border-radius 처리"""
        left_r = "3px" if index == 0 else "0"
        right_r = "3px" if index == total - 1 else "0"
        border_right = "" if index == total - 1 else "border-right: none;"
        return f"""
            QPushButton {{
                padding: 3px 10px;
                border: 1px solid #B0B0B0;
                border-radius: 0;
                border-top-left-radius: {left_r};
                border-bottom-left-radius: {left_r};
                border-top-right-radius: {right_r};
                border-bottom-right-radius: {right_r};
                {border_right}
                background: #E8E8E8;
                font-size: 8.5pt;
                color: #555;
                min-width: 48px;
            }}
            QPushButton:checked {{
                background: {NAVY};
                color: white;
                font-weight: 600;
                border-color: {NAVY};
            }}
            QPushButton:hover:!checked {{ background: #D8D8D8; }}
        """


# ═══════════════════════════════════════════
# 커스텀 위젯: DCIR 카드 선택
# ═══════════════════════════════════════════
class DcirCard(QFrame):
    """DCIR 옵션 카드 — 클릭으로 선택"""

    def __init__(self, name: str, desc: str, badge: str, selected: bool = False, parent=None):
        super().__init__(parent)
        self._selected = selected
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        # 라디오 표시 (원형 — paintEvent에서 그림)
        self._radio_widget = QWidget()
        self._radio_widget.setFixedSize(16, 16)
        layout.addWidget(self._radio_widget, 0, Qt.AlignmentFlag.AlignTop)

        # 텍스트 영역
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self._name_label = QLabel(name)
        self._name_label.setFont(QFont(FONT_FAMILY, FONT_SIZE, QFont.Weight.Bold))

        self._desc_label = QLabel(desc)
        self._desc_label.setStyleSheet("color: #888; font-size: 7.5pt;")
        self._desc_label.setWordWrap(True)

        self._badge_label = QLabel(badge)
        self._badge_label.setStyleSheet(
            "background: #E8E8E8; color: #666; font-size: 7pt; "
            "padding: 1px 5px; border-radius: 2px;"
        )
        self._badge_label.setFixedHeight(16)
        self._badge_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

        text_layout.addWidget(self._name_label)
        text_layout.addWidget(self._desc_label)
        text_layout.addWidget(self._badge_label)
        layout.addLayout(text_layout, 1)

        self._update_style()

    @property
    def selected(self) -> bool:
        return self._selected

    @selected.setter
    def selected(self, val: bool) -> None:
        self._selected = val
        self._update_style()
        self.update()

    def _update_style(self) -> None:
        if self._selected:
            self.setStyleSheet(
                f"DcirCard {{ background: #EEF2FA; border: 1.5px solid {NAVY}; border-radius: 4px; }}"
            )
            self._name_label.setStyleSheet(f"color: {NAVY}; font-weight: bold;")
            self._badge_label.setStyleSheet(
                f"background: #D6DEF0; color: {NAVY}; font-size: 7pt; "
                "padding: 1px 5px; border-radius: 2px;"
            )
        else:
            self.setStyleSheet(
                "DcirCard { background: white; border: 1px solid #D0D0D0; border-radius: 4px; }"
            )
            self._name_label.setStyleSheet("color: #333; font-weight: bold;")
            self._badge_label.setStyleSheet(
                "background: #E8E8E8; color: #666; font-size: 7pt; "
                "padding: 1px 5px; border-radius: 2px;"
            )

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        # 라디오 원 그리기
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rx = self._radio_widget.x() + 8
        ry = self._radio_widget.y() + 8
        if self._selected:
            painter.setPen(QPen(QColor(NAVY), 1.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(rx - 7, ry - 7, 14, 14)
            painter.setBrush(QBrush(QColor(NAVY)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(rx - 4, ry - 4, 8, 8)
        else:
            painter.setPen(QPen(QColor("#999"), 1.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(rx - 7, ry - 7, 14, 14)
        painter.end()

    def mousePressEvent(self, event) -> None:
        # 부모 DcirCardGroup에게 알림
        parent = self.parent()
        if parent and hasattr(parent, 'select_card'):
            parent.select_card(self)
        super().mousePressEvent(event)


class DcirCardGroup(QWidget):
    """DCIR 카드 그룹 — 하나만 선택"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self._cards: list[DcirCard] = []

    def add_card(self, name: str, desc: str, badge: str, selected: bool = False) -> DcirCard:
        card = DcirCard(name, desc, badge, selected, self)
        self._cards.append(card)
        self._layout.addWidget(card)
        return card

    def select_card(self, card: DcirCard) -> None:
        for c in self._cards:
            c.selected = (c is card)


# ═══════════════════════════════════════════
# 필드 그룹 프레임
# ═══════════════════════════════════════════
class FieldGroupFrame(QFrame):
    """연한 배경의 필드 그룹 프레임"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"FieldGroupFrame {{ background: {BG_FIELD}; border: 1px solid #E8E8E8; border-radius: 3px; }}"
        )
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 6, 8, 6)
        self._layout.setSpacing(4)

    @property
    def inner_layout(self) -> QVBoxLayout:
        return self._layout


# ═══════════════════════════════════════════
# 헬퍼 함수
# ═══════════════════════════════════════════
def _label(text: str, color: str = "#555", bold: bool = False, size: float = 8.5) -> QLabel:
    lbl = QLabel(text)
    weight = "bold" if bold else "normal"
    lbl.setStyleSheet(f"color: {color}; font-size: {size}pt; font-weight: {weight};")
    return lbl


def _lineedit(text: str = "", width: int = 45) -> QLineEdit:
    le = QLineEdit(text)
    le.setFixedWidth(width)
    le.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return le


def _primary_btn(text: str, height: int = 32) -> QPushButton:
    btn = QPushButton(text)
    btn.setMinimumHeight(height)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {NAVY}; color: white; border-color: {NAVY};
            font-weight: 600; font-size: 10pt; border-radius: 3px;
            padding: 5px 16px;
        }}
        QPushButton:hover {{ background: #2D4070; }}
        QPushButton:pressed {{ background: #253660; }}
    """)
    return btn


def _secondary_btn(text: str, height: int = 32, enabled: bool = True) -> QPushButton:
    btn = QPushButton(text)
    btn.setMinimumHeight(height)
    btn.setEnabled(enabled)
    if not enabled:
        btn.setStyleSheet("color: #999;")
    return btn


# ═══════════════════════════════════════════
# 경로 입력 GroupBox (공통)
# ═══════════════════════════════════════════
def _build_path_group(improved: bool = False) -> QGroupBox:
    grp = QGroupBox("1. 경로 입력")
    layout = QVBoxLayout(grp)
    layout.setContentsMargins(8, 18, 8, 8)
    layout.setSpacing(4)

    # 상단 체크박스 + 버튼
    top_row = QHBoxLayout()
    top_row.setSpacing(4)
    top_row.addWidget(QCheckBox("연결처리"))
    top_row.addWidget(QCheckBox("ECT path"))
    top_row.addStretch()

    if improved:
        for icon, text in [("📂", "불러오기"), ("💾", "저장")]:
            b = QPushButton(f"{icon} {text}")
            b.setStyleSheet("padding: 2px 8px; font-size: 8pt;")
            top_row.addWidget(b)
        b_del = QPushButton("🗑")
        b_del.setStyleSheet("padding: 2px 8px; font-size: 8pt; color: #999;")
        top_row.addWidget(b_del)
    layout.addLayout(top_row)

    # 테이블
    rows = 3 if improved else 5
    cols = 7
    headers = ["시험명", "경로", "채널", "용량", "사이클", "Raw", "모드"]
    table = QTableWidget(rows, cols)
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setDefaultSectionSize(22)
    table.verticalHeader().setVisible(True)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    table.setMaximumHeight(22 * rows + 26)

    hh = table.horizontalHeader()
    hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
    hh.resizeSection(0, 55)
    hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
    for c in range(2, 7):
        hh.setSectionResizeMode(c, QHeaderView.ResizeMode.Fixed)
        hh.resizeSection(c, [45, 42, 50, 38, 38][c - 2])

    if improved:
        # 경로/사이클 헤더 강조
        for col in [1, 4]:
            item = QTableWidgetItem(headers[col])
            f = item.font()
            f.setBold(True)
            item.setFont(f)
            item.setForeground(QColor(NAVY))
            table.setHorizontalHeaderItem(col, item)

        # 예시 데이터 1행
        data = ["수명-45℃", "E:\\U..\\ch54", "054", "5075", "2-308", "1-420", "Gen"]
        for c, val in enumerate(data):
            item = QTableWidgetItem(val)
            if c == 4:  # 사이클 열
                item.setForeground(QColor(NAVY))
                f = item.font()
                f.setBold(True)
                item.setFont(f)
            elif c == 6:  # 모드 열
                item.setForeground(QColor("#888"))
            table.setItem(0, c, item)
        table.selectRow(0)

    if not improved:
        # 우측 버튼 (현행)
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(2)
        for icon in ["📂", "💾", "🗑"]:
            b = QPushButton(icon)
            b.setFixedSize(24, 24)
            b.setStyleSheet("padding: 1px; font-size: 11px;")
            btn_layout.addWidget(b)
        btn_layout.addStretch()

        h = QHBoxLayout()
        h.setSpacing(2)
        h.addWidget(table, 1)
        v_wrap = QVBoxLayout()
        v_wrap.addSpacing(22)
        v_wrap.addLayout(btn_layout)
        h.addLayout(v_wrap)
        layout.addLayout(h)
    else:
        layout.addWidget(table)

    return grp


# ═══════════════════════════════════════════
# BEFORE — Cycle 탭
# ═══════════════════════════════════════════
def _build_before_cycle() -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(6, 6, 6, 6)
    layout.setSpacing(4)

    # 2. DCIR 옵션 (현행 — 긴 라디오 라벨)
    grp_dcir = QGroupBox("2. DCIR 옵션 선택")
    dl = QVBoxLayout(grp_dcir)
    dl.setContentsMargins(8, 20, 8, 8)
    dl.setSpacing(6)
    bg = QButtonGroup(page)
    texts = [
        "PNE 설비 DCIR (SOC100 10s 방전 Pulse)",
        "PNE 10s DCIR (SOC5, 50 10s 방전 Pulse)",
        "PNE DCIR (SOC 30/50/70 충전, SOC 70/50/30 방전,\n"
        "  1s Pulse/RSS) – 그래프 방전 70%",
    ]
    for i, t in enumerate(texts):
        rb = QRadioButton(t)
        if i == 2:
            rb.setChecked(True)
        bg.addButton(rb, i)
        dl.addWidget(rb)
    layout.addWidget(grp_dcir)

    # 3. 그래프 옵션 (현행)
    grp_graph = QGroupBox("3. 그래프 옵션")
    gl = QVBoxLayout(grp_graph)
    gl.setContentsMargins(8, 20, 8, 8)
    gl.setSpacing(5)
    gl.addWidget(QCheckBox("DCIR 고정 해제"))

    r1 = QHBoxLayout()
    r1.addWidget(QLabel("Y축 최대")); r1.addWidget(_lineedit("1.10", 50))
    r1.addSpacing(10)
    r1.addWidget(QLabel("Y축 최소")); r1.addWidget(_lineedit("0.65", 50))
    r1.addStretch()
    gl.addLayout(r1)

    r2 = QHBoxLayout()
    r2.addWidget(QLabel("X축 최대")); r2.addWidget(_lineedit("0", 50))
    r2.addSpacing(10)
    r2.addWidget(QLabel("DCIR scale 늘리기 (x ?배)")); r2.addWidget(_lineedit("0", 40))
    r2.addStretch()
    gl.addLayout(r2)
    layout.addWidget(grp_graph)

    # 4. 사이클 분석 (현행)
    grp_run = QGroupBox("4. 사이클 분석")
    rl = QHBoxLayout(grp_run)
    rl.setContentsMargins(8, 20, 8, 8)
    rl.setSpacing(8)
    bg2 = QButtonGroup(page)
    rb_indiv = QRadioButton("개별 탭")
    rb_indiv.setChecked(True)
    rb_total = QRadioButton("통합 탭")
    bg2.addButton(rb_indiv, 0)
    bg2.addButton(rb_total, 1)
    rl.addWidget(rb_indiv)
    rl.addWidget(rb_total)
    rl.addStretch()
    btn_run = QPushButton("Cycle 분석")
    btn_run.setStyleSheet(
        f"background:{NAVY}; color:white; border-color:{NAVY}; font-weight:600; min-height:28px;"
    )
    rl.addWidget(btn_run)
    btn_rst = QPushButton("초기화")
    btn_rst.setEnabled(False)
    btn_rst.setMinimumHeight(28)
    rl.addWidget(btn_rst)
    layout.addWidget(grp_run)

    layout.addStretch()
    return page


# ═══════════════════════════════════════════
# BEFORE — Profile 탭
# ═══════════════════════════════════════════
def _build_before_profile() -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(6, 6, 6, 6)
    layout.setSpacing(4)

    # 상단 라디오 + 체크
    top = QHBoxLayout()
    top.setSpacing(4)
    bg = QButtonGroup(page)
    for i, t in enumerate(["사이클 통합", "셀별 통합", "전체 통합"]):
        rb = QRadioButton(t)
        if i == 0:
            rb.setChecked(True)
        bg.addButton(rb, i)
        top.addWidget(rb)
    chk_dqdv = QCheckBox("dQdV")
    chk_dqdv.setChecked(True)
    top.addSpacing(8)
    top.addWidget(chk_dqdv)
    top.addWidget(QCheckBox("코인셀"))
    top.addStretch()
    layout.addLayout(top)

    # TC / ▶
    tc_row = QHBoxLayout()
    tc_row.addStretch()
    btn_tc = QPushButton("TC")
    btn_tc.setFixedSize(28, 18)
    btn_tc.setStyleSheet("font-size:7pt; padding:0;")
    tc_row.addWidget(btn_tc)
    btn_det = QPushButton("▶")
    btn_det.setFixedSize(22, 18)
    btn_det.setStyleSheet("font-size:7pt; padding:0;")
    tc_row.addWidget(btn_det)
    layout.addLayout(tc_row)

    # 1. 데이터 범위
    grp1 = QGroupBox("1. 데이터 범위")
    g1l = QVBoxLayout(grp1)
    g1l.setContentsMargins(8, 20, 8, 8)
    g1l.setSpacing(5)

    r1 = QHBoxLayout()
    r1.setSpacing(3)
    r1.addWidget(QLabel("데이터:"))
    bg2 = QButtonGroup(page)
    for i, t in enumerate(["사이클", "충전", "방전"]):
        rb = QRadioButton(t)
        if i == 2:
            rb.setChecked(True)
        bg2.addButton(rb, i)
        r1.addWidget(rb)
    r1.addSpacing(8)
    r1.addWidget(QLabel("연속성:"))
    bg3 = QButtonGroup(page)
    for i, t in enumerate(["오버레이", "이어서"]):
        rb = QRadioButton(t)
        if i == 1:
            rb.setChecked(True)
        bg3.addButton(rb, i)
        r1.addWidget(rb)
    r1.addStretch()
    g1l.addLayout(r1)

    r2 = QHBoxLayout()
    r2.setSpacing(3)
    r2.addWidget(QLabel("X축:"))
    bg4 = QButtonGroup(page)
    for i, t in enumerate(["SOC(DOD)", "시간"]):
        rb = QRadioButton(t)
        if i == 1:
            rb.setChecked(True)
        bg4.addButton(rb, i)
        r2.addWidget(rb)
    r2.addSpacing(6)
    chk_rest = QCheckBox("Rest")
    chk_rest.setChecked(True)
    chk_cv = QCheckBox("CV")
    chk_cv.setChecked(True)
    r2.addWidget(chk_rest)
    r2.addWidget(chk_cv)
    r2.addWidget(QCheckBox("루프"))
    r2.addStretch()
    g1l.addLayout(r2)
    layout.addWidget(grp1)

    # 2. 그래프 옵션
    grp2 = QGroupBox("2. 그래프 옵션")
    g2l = QVBoxLayout(grp2)
    g2l.setContentsMargins(8, 20, 8, 8)
    g2l.setSpacing(5)

    row_a = QHBoxLayout()
    row_a.addWidget(QLabel("Y축 최소")); row_a.addWidget(_lineedit("2.5"))
    row_a.addWidget(QLabel("Y축 :")); row_a.addWidget(_lineedit("4.7"))
    row_a.addWidget(QLabel("Y축 간격")); row_a.addWidget(_lineedit("0.1"))
    row_a.addStretch()
    g2l.addLayout(row_a)

    row_b = QHBoxLayout()
    row_b.addWidget(QLabel("Smooth (0 이면 자동)")); row_b.addWidget(_lineedit("0"))
    row_b.addSpacing(8)
    row_b.addWidget(QLabel("컷오프 C-RATE")); row_b.addWidget(_lineedit("0"))
    row_b.addStretch()
    g2l.addLayout(row_b)

    row_c = QHBoxLayout()
    row_c.addWidget(QLabel("DQDV scale 늘리기")); row_c.addWidget(_lineedit("1"))
    row_c.addStretch()
    g2l.addLayout(row_c)
    layout.addWidget(grp2)

    # 3. 프로필 분석
    grp3 = QGroupBox("3. 프로필 분석")
    g3l = QHBoxLayout(grp3)
    g3l.setContentsMargins(8, 20, 8, 8)
    g3l.setSpacing(8)
    btn_p = QPushButton("프로필 분석")
    btn_p.setStyleSheet(
        f"background:{NAVY}; color:white; border-color:{NAVY}; font-weight:600; min-height:28px;"
    )
    btn_d = QPushButton("DCIR")
    btn_d.setMinimumHeight(28)
    btn_r = QPushButton("초기화")
    btn_r.setMinimumHeight(28)
    btn_r.setEnabled(False)
    g3l.addWidget(btn_p, 2)
    g3l.addWidget(btn_d, 1)
    g3l.addWidget(btn_r, 1)
    layout.addWidget(grp3)

    layout.addStretch()
    return page


# ═══════════════════════════════════════════
# AFTER — Cycle 탭 (개선)
# ═══════════════════════════════════════════
def _build_after_cycle() -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(6, 6, 6, 6)
    layout.setSpacing(4)

    # 2. DCIR 옵션 — 카드형
    grp_dcir = QGroupBox("2. DCIR 옵션")
    dl = QVBoxLayout(grp_dcir)
    dl.setContentsMargins(8, 20, 8, 8)

    cards = DcirCardGroup()
    cards.add_card("설비 DCIR", "SOC100 → 10s 방전 Pulse", "PNE 설비 기본")
    cards.add_card("10s Pulse DCIR", "SOC 5%, 50% → 10s 방전 Pulse", "2-point SOC")
    cards.add_card(
        "MK DCIR (1s Pulse/RSS)",
        "충전 SOC 30/50/70 + 방전 SOC 70/50/30 — 그래프 방전 70%",
        "DCIR + DCIR2 통합",
        selected=True,
    )
    dl.addWidget(cards)
    layout.addWidget(grp_dcir)

    # 3. 그래프 옵션 — 영역화
    grp_graph = QGroupBox("3. 그래프 옵션")
    gl = QVBoxLayout(grp_graph)
    gl.setContentsMargins(8, 20, 8, 8)
    gl.setSpacing(6)
    gl.addWidget(QCheckBox("DCIR 고정 해제"))

    ff = FieldGroupFrame()
    r1 = QHBoxLayout()
    r1.addWidget(_label("Y축"))
    r1.addWidget(_lineedit("0.65", 48))
    r1.addWidget(_label("~", "#AAA"))
    r1.addWidget(_lineedit("1.10", 48))
    r1.addWidget(_label("(최소~최대)", "#AAA", size=7.5))
    r1.addStretch()
    r1.addWidget(_label("X축 최대"))
    r1.addWidget(_lineedit("0", 40))
    r1.addWidget(_label("(0=auto)", "#AAA", size=7.5))
    ff.inner_layout.addLayout(r1)

    r2 = QHBoxLayout()
    r2.addWidget(_label("DCIR 스케일"))
    r2.addWidget(_lineedit("0", 40))
    r2.addWidget(_label("배 (0=자동)", "#AAA", size=7.5))
    r2.addStretch()
    ff.inner_layout.addLayout(r2)
    gl.addWidget(ff)
    layout.addWidget(grp_graph)

    # 4. 사이클 분석 — 버튼 위계 강화
    grp_run = QGroupBox("4. 사이클 분석")
    rl = QVBoxLayout(grp_run)
    rl.setContentsMargins(8, 20, 8, 8)
    rl.setSpacing(8)

    seg_row = QHBoxLayout()
    seg_row.addWidget(_label("출력 형식:", "#888"))
    seg_row.addWidget(SegmentedControl(["개별 탭", "통합 탭"], default=0))
    seg_row.addStretch()
    rl.addLayout(seg_row)

    btn_row = QHBoxLayout()
    btn_row.setSpacing(8)
    btn_row.addWidget(_primary_btn("▶  Cycle 분석"), 2)
    btn_row.addWidget(_secondary_btn("초기화", enabled=False), 1)
    rl.addLayout(btn_row)
    layout.addWidget(grp_run)

    layout.addStretch()
    return page


# ═══════════════════════════════════════════
# AFTER — Profile 탭 (개선)
# ═══════════════════════════════════════════
def _build_after_profile() -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(6, 6, 6, 6)
    layout.setSpacing(4)

    # 상단 세그먼트 + 체크박스
    top = QHBoxLayout()
    top.setSpacing(6)
    top.addWidget(_label("보기:", "#888"))
    top.addWidget(SegmentedControl(["사이클 통합", "셀별 통합", "전체 통합"], default=0))
    top.addStretch()
    chk_dqdv = QCheckBox("dQdV")
    chk_dqdv.setChecked(True)
    top.addWidget(chk_dqdv)
    top.addWidget(QCheckBox("코인셀"))
    layout.addLayout(top)

    # 1. 데이터 범위 — 세그먼트 + 영역화
    grp1 = QGroupBox("1. 데이터 범위")
    g1l = QVBoxLayout(grp1)
    g1l.setContentsMargins(8, 20, 8, 8)

    ff1 = FieldGroupFrame()
    r1 = QHBoxLayout()
    r1.addWidget(_label("데이터", size=8.5))
    r1.addWidget(SegmentedControl(["사이클", "충전", "방전"], default=2))
    r1.addSpacing(10)
    r1.addWidget(_label("연속성", size=8.5))
    r1.addWidget(SegmentedControl(["오버레이", "이어서"], default=1))
    r1.addStretch()
    ff1.inner_layout.addLayout(r1)

    r2 = QHBoxLayout()
    r2.addWidget(_label("X축", size=8.5))
    r2.addWidget(SegmentedControl(["SOC(DOD)", "시간"], default=1))
    r2.addSpacing(10)
    chk_rest = QCheckBox("Rest")
    chk_rest.setChecked(True)
    chk_cv = QCheckBox("CV")
    chk_cv.setChecked(True)
    r2.addWidget(chk_rest)
    r2.addWidget(chk_cv)
    r2.addWidget(QCheckBox("루프"))
    r2.addStretch()
    ff1.inner_layout.addLayout(r2)
    g1l.addWidget(ff1)
    layout.addWidget(grp1)

    # 2. 그래프 옵션 — 범위 패턴 + 단위
    grp2 = QGroupBox("2. 그래프 옵션")
    g2l = QVBoxLayout(grp2)
    g2l.setContentsMargins(8, 20, 8, 8)

    ff2 = FieldGroupFrame()
    ra = QHBoxLayout()
    ra.addWidget(_label("Y축"))
    ra.addWidget(_lineedit("2.5"))
    ra.addWidget(_label("~", "#AAA"))
    ra.addWidget(_lineedit("4.7"))
    ra.addWidget(_label("(V)", "#AAA", size=7.5))
    ra.addSpacing(8)
    ra.addWidget(_label("간격"))
    ra.addWidget(_lineedit("0.1", 38))
    ra.addWidget(_label("V", "#AAA", size=7.5))
    ra.addStretch()
    ff2.inner_layout.addLayout(ra)

    rb = QHBoxLayout()
    rb.addWidget(_label("Smooth"))
    rb.addWidget(_lineedit("0", 38))
    rb.addWidget(_label("(0=auto)", "#AAA", size=7.5))
    rb.addSpacing(8)
    rb.addWidget(_label("컷오프"))
    rb.addWidget(_lineedit("0", 38))
    rb.addWidget(_label("C", "#AAA", size=7.5))
    rb.addStretch()
    ff2.inner_layout.addLayout(rb)

    rc = QHBoxLayout()
    rc.addWidget(_label("dQ/dV 스케일"))
    rc.addWidget(_lineedit("1", 38))
    rc.addWidget(_label("배", "#AAA", size=7.5))
    rc.addStretch()
    ff2.inner_layout.addLayout(rc)
    g2l.addWidget(ff2)
    layout.addWidget(grp2)

    # 3. 프로필 분석 — 버튼 위계
    grp3 = QGroupBox("3. 프로필 분석")
    g3l = QHBoxLayout(grp3)
    g3l.setContentsMargins(8, 20, 8, 8)
    g3l.setSpacing(8)
    g3l.addWidget(_primary_btn("▶  프로필 분석"), 2)
    g3l.addWidget(_secondary_btn("DCIR"), 1)
    g3l.addWidget(_secondary_btn("초기화", enabled=False), 1)
    layout.addWidget(grp3)

    layout.addStretch()
    return page


# ═══════════════════════════════════════════
# 메인 윈도우
# ═══════════════════════════════════════════
class MockupWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BDT — Cycle/Profile UX 개선 목업")
        self.resize(520, 800)
        self.setStyleSheet(GLOBAL_QSS)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 헤더
        hdr = QLabel("  Cycle / Profile 탭 — UX 개선 목업")
        hdr.setFixedHeight(36)
        hdr.setStyleSheet(f"background:{NAVY}; color:white; font-size:12pt; font-weight:bold;")
        root.addWidget(hdr)

        # Before / After 탭
        main_tab = QTabWidget()
        main_tab.setStyleSheet("""
            QTabBar::tab { padding: 6px 20px; font-size: 10pt; }
            QTabBar::tab:selected { font-weight: bold; }
        """)

        # ── BEFORE 탭 ──
        before_page = QWidget()
        before_page.setStyleSheet(f"background: {BG};")
        bl = QVBoxLayout(before_page)
        bl.setContentsMargins(6, 6, 6, 6)

        bl.addWidget(_build_path_group(improved=False))

        inner_before = QTabWidget()
        inner_before.addTab(_build_before_cycle(), "Cycle")
        inner_before.addTab(_build_before_profile(), "Profile")
        bl.addWidget(inner_before)

        # 스크롤 래핑
        scroll_before = QScrollArea()
        scroll_before.setWidget(before_page)
        scroll_before.setWidgetResizable(True)
        main_tab.addTab(scroll_before, "Before (현행)")

        # ── AFTER 탭 ──
        after_page = QWidget()
        after_page.setStyleSheet(f"background: {BG};")
        al = QVBoxLayout(after_page)
        al.setContentsMargins(6, 6, 6, 6)

        al.addWidget(_build_path_group(improved=True))

        inner_after = QTabWidget()
        inner_after.addTab(_build_after_cycle(), "Cycle")
        inner_after.addTab(_build_after_profile(), "Profile")
        al.addWidget(inner_after)

        scroll_after = QScrollArea()
        scroll_after.setWidget(after_page)
        scroll_after.setWidgetResizable(True)
        main_tab.addTab(scroll_after, "After (개선안)")

        root.addWidget(main_tab)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MockupWindow()
    win.show()
    sys.exit(app.exec())
