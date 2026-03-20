#!/usr/bin/env python
"""sync_ui.py — proto_.py의 Ui_sitool → DataTool_UI.ui 역동기화 유틸리티

proto_.py의 Ui_sitool 클래스를 실행하여 위젯 트리를 구성한 뒤,
Qt Designer가 읽을 수 있는 .ui XML 파일로 변환합니다.

사용법:
    python sync_ui.py

결과:
    DataTool_dev/DataTool_UI.ui 파일을 현재 Ui_sitool 기준으로 재생성

주의:
    - BorderDelegate, PathElideDelegate 등 커스텀 delegate는 .ui에 반영 불가
    - addStretch()는 spacer item으로 근사 변환됩니다
    - setSectionResizeMode 등 일부 헤더 설정은 .ui에서 지원하지 않습니다
    - 재생성 후 Qt Designer에서 열어 시각적으로 확인하세요
"""

import sys
import re
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring, indent

from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QApplication, QMainWindow


# ── 커스텀 Delegate 스텁 (.ui에 반영 불가) ──
class BorderDelegate(QtWidgets.QStyledItemDelegate):
    BORDER_ROLE = QtCore.Qt.ItemDataRole.UserRole + 100
    def __init__(self, parent=None):
        super().__init__(parent)

class PathElideDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)


# ── Ui_sitool 클래스 추출 및 로드 ──

def load_ui_class(proto_path: Path):
    """proto_.py에서 Ui_sitool 클래스를 추출하고 exec"""
    source = proto_path.read_text(encoding='utf-8')

    match = re.search(r'^class Ui_sitool\(object\):', source, re.MULTILINE)
    if not match:
        raise RuntimeError(f"Ui_sitool 클래스를 찾을 수 없습니다: {proto_path}")

    start = match.start()
    rest = source[start:]
    lines = rest.split('\n')

    # 클래스 끝점: 다음 top-level class/def 정의
    # (retranslateUi의 여러 줄 문자열이 column 0에서 시작할 수 있으므로
    #  단순 들여쓰기 검사가 아닌 class/def 패턴으로 감지)
    end_idx = len(lines)
    for i, line in enumerate(lines[1:], 1):
        if re.match(r'^(class |def )\w', line):
            end_idx = i
            break

    class_source = '\n'.join(lines[:end_idx])

    namespace = {
        'QtWidgets': QtWidgets,
        'QtCore': QtCore,
        'QtGui': QtGui,
        'BorderDelegate': BorderDelegate,
        'PathElideDelegate': PathElideDelegate,
    }

    exec(class_source, namespace)
    UiClass = namespace['Ui_sitool']

    # setupUi에서 참조하는 누락 메서드 폴백
    for method_name in ['_pybamm_close_run_tab']:
        if not hasattr(UiClass, method_name):
            setattr(UiClass, method_name, lambda self, *a, **kw: None)

    return UiClass


# ── XML 빌더 ──

class UiXmlBuilder:
    """위젯 트리를 .ui XML로 변환"""

    def __init__(self, ui_instance, main_window):
        self.ui = ui_instance
        self.win = main_window
        self._processed = set()

    def build(self) -> str:
        root = Element('ui', version='4.0')
        SubElement(root, 'class').text = 'sitool'

        # 메인 다이얼로그 (기존 .ui 호환: QDialog)
        dlg = SubElement(root, 'widget')
        dlg.set('class', 'QDialog')
        dlg.set('name', 'sitool')

        w, h = self.win.width(), self.win.height()
        self._add_geometry(dlg, 0, 0, w, h)
        self._add_font(dlg, self.win.font())
        self._add_string(dlg, 'windowTitle', self.win.windowTitle())

        # layoutWidget (절대 좌표: QDialog 호환)
        lw = self.ui.layoutWidget
        lw_elem = SubElement(dlg, 'widget')
        lw_elem.set('class', 'QWidget')
        lw_elem.set('name', 'layoutWidget')
        self._add_geometry(lw_elem, 12, 12, w - 19, h - 21)
        self._add_font(lw_elem, lw.font())

        self._write_layout(lw_elem, self.ui.verticalLayout_39)

        SubElement(root, 'resources')
        SubElement(root, 'connections')

        indent(root, space=' ')
        xml_str = tostring(root, encoding='unicode', xml_declaration=False)
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str + '\n'

    # ── 레이아웃 ──
    def _write_layout(self, parent_xml, layout):
        if layout is None:
            return

        cls_name = type(layout).__name__
        name = layout.objectName() or ''

        lx = SubElement(parent_xml, 'layout')
        lx.set('class', cls_name)
        lx.set('name', name)

        for i in range(layout.count()):
            item = layout.itemAt(i)
            item_xml = SubElement(lx, 'item')

            if isinstance(layout, QtWidgets.QGridLayout):
                row, col, rspan, cspan = layout.getItemPosition(i)
                item_xml.set('row', str(row))
                item_xml.set('column', str(col))
                if rspan > 1:
                    item_xml.set('rowSpan', str(rspan))
                if cspan > 1:
                    item_xml.set('colSpan', str(cspan))

            if item.widget():
                self._write_widget(item_xml, item.widget())
            elif item.layout():
                self._write_layout(item_xml, item.layout())
            elif item.spacerItem():
                self._write_spacer(item_xml, item.spacerItem())

    # ── 위젯 (분기) ──
    def _write_widget(self, parent_xml, widget):
        wid = id(widget)
        if wid in self._processed:
            return
        self._processed.add(wid)

        name = widget.objectName() or ''

        if isinstance(widget, QtWidgets.QTabWidget):
            self._write_tab_widget(parent_xml, widget, name)
        elif isinstance(widget, QtWidgets.QTableWidget):
            self._write_table_widget(parent_xml, widget, name)
        elif isinstance(widget, QtWidgets.QComboBox):
            self._write_combo_box(parent_xml, widget, name)
        elif isinstance(widget, QtWidgets.QGroupBox):
            self._write_group_box(parent_xml, widget, name)
        elif isinstance(widget, QtWidgets.QScrollArea):
            self._write_scroll_area(parent_xml, widget, name)
        elif isinstance(widget, QtWidgets.QStackedWidget):
            self._write_stacked_widget(parent_xml, widget, name)
        elif isinstance(widget, QtWidgets.QListWidget):
            self._write_list_widget(parent_xml, widget, name)
        elif (isinstance(widget, QtWidgets.QFrame)
              and widget.frameShape() in (
                  QtWidgets.QFrame.Shape.HLine, QtWidgets.QFrame.Shape.VLine)):
            self._write_line(parent_xml, widget, name)
        else:
            self._write_generic(parent_xml, widget, name)

    # ── 일반 위젯 ──
    def _write_generic(self, parent_xml, widget, name):
        cls_name = type(widget).__name__
        wx = SubElement(parent_xml, 'widget')
        wx.set('class', cls_name)
        wx.set('name', name)

        self._write_common_props(wx, widget)
        self._write_typed_props(wx, widget)

        layout = widget.layout()
        if layout:
            self._write_layout(wx, layout)

    # ── 공통 속성 ──
    def _write_common_props(self, elem, widget):
        parent = widget.parentWidget()

        ms = widget.minimumSize()
        if ms.width() > 0 or ms.height() > 0:
            self._add_size(elem, 'minimumSize', ms)

        mx = widget.maximumSize()
        if mx.width() < 16777215 or mx.height() < 16777215:
            self._add_size(elem, 'maximumSize', mx)

        bs = widget.baseSize()
        if bs.width() > 0 or bs.height() > 0:
            self._add_size(elem, 'baseSize', bs)

        parent_font = parent.font() if parent else QtGui.QFont()
        if widget.font() != parent_font:
            self._add_font(elem, widget.font())

    # ── 위젯 타입별 속성 ──
    def _write_typed_props(self, elem, widget):
        # toolTip (공통)
        tt = widget.toolTip()
        if tt:
            self._add_string(elem, 'toolTip', tt)

        if isinstance(widget, QtWidgets.QPushButton):
            text = widget.text()
            if text:
                self._add_string(elem, 'text', text)
            if widget.isCheckable():
                self._add_bool(elem, 'checkable', True)
                if widget.isChecked():
                    self._add_bool(elem, 'checked', True)

        elif isinstance(widget, QtWidgets.QCheckBox):
            text = widget.text()
            if text:
                self._add_string(elem, 'text', text)
            if widget.isChecked():
                self._add_bool(elem, 'checked', True)

        elif isinstance(widget, QtWidgets.QRadioButton):
            text = widget.text()
            if text:
                self._add_string(elem, 'text', text)
            if widget.isCheckable():
                self._add_bool(elem, 'checkable', True)
            if widget.isChecked():
                self._add_bool(elem, 'checked', True)

        elif isinstance(widget, QtWidgets.QLabel):
            text = widget.text()
            if text:
                self._add_string(elem, 'text', text)
            default_align = (QtCore.Qt.AlignmentFlag.AlignLeft
                             | QtCore.Qt.AlignmentFlag.AlignVCenter)
            if widget.alignment() != default_align:
                self._add_set(elem, 'alignment',
                              self._alignment_str(widget.alignment()))
            if widget.wordWrap():
                self._add_bool(elem, 'wordWrap', True)

        elif isinstance(widget, QtWidgets.QLineEdit):
            text = widget.text()
            if text:
                self._add_string(elem, 'text', text)
            ph = widget.placeholderText()
            if ph:
                self._add_string(elem, 'placeholderText', ph)
            imh = widget.inputMethodHints()
            if imh != QtCore.Qt.InputMethodHint.ImhNone:
                self._add_set(elem, 'inputMethodHints', self._imh_str(imh))
            default_align = (QtCore.Qt.AlignmentFlag.AlignLeft
                             | QtCore.Qt.AlignmentFlag.AlignVCenter)
            if widget.alignment() != default_align:
                self._add_set(elem, 'alignment',
                              self._alignment_str(widget.alignment()))
            mask = widget.inputMask()
            if mask is not None and mask != '':
                self._add_string(elem, 'inputMask', mask)

        elif isinstance(widget, QtWidgets.QPlainTextEdit):
            text = widget.toPlainText()
            if text:
                self._add_string(elem, 'plainText', text)
            imh = widget.inputMethodHints()
            if imh != QtCore.Qt.InputMethodHint.ImhNone:
                self._add_set(elem, 'inputMethodHints', self._imh_str(imh))

        elif isinstance(widget, QtWidgets.QProgressBar):
            self._add_number(elem, 'value', widget.value())

    # ── QTabWidget ──
    def _write_tab_widget(self, parent_xml, widget, name):
        wx = SubElement(parent_xml, 'widget')
        wx.set('class', 'QTabWidget')
        wx.set('name', name)

        self._write_common_props(wx, widget)

        tp = widget.tabPosition()
        if tp != QtWidgets.QTabWidget.TabPosition.North:
            self._add_enum(wx, 'tabPosition', f'QTabWidget::{tp.name}')

        ts = widget.tabShape()
        if ts != QtWidgets.QTabWidget.TabShape.Rounded:
            self._add_enum(wx, 'tabShape', f'QTabWidget::{ts.name}')

        self._add_number(wx, 'currentIndex', widget.currentIndex())

        if widget.tabsClosable():
            self._add_bool(wx, 'tabsClosable', True)

        for i in range(widget.count()):
            page = widget.widget(i)
            title = widget.tabText(i)
            self._processed.add(id(page))

            pw = SubElement(wx, 'widget')
            pw.set('class', 'QWidget')
            pw.set('name', page.objectName() or f'page_{i}')

            attr = SubElement(pw, 'attribute', name='title')
            SubElement(attr, 'string').text = title

            layout = page.layout()
            if layout:
                self._write_layout(pw, layout)

    # ── QTableWidget ──
    def _write_table_widget(self, parent_xml, widget, name):
        wx = SubElement(parent_xml, 'widget')
        wx.set('class', 'QTableWidget')
        wx.set('name', name)

        self._write_common_props(wx, widget)

        # 스크롤바 정책
        hsp = widget.horizontalScrollBarPolicy()
        if hsp != QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded:
            self._add_enum(wx, 'horizontalScrollBarPolicy', f'Qt::{hsp.name}')
        vsp = widget.verticalScrollBarPolicy()
        if vsp != QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded:
            self._add_enum(wx, 'verticalScrollBarPolicy', f'Qt::{vsp.name}')

        rc = widget.rowCount()
        cc = widget.columnCount()
        if rc > 0:
            self._add_number(wx, 'rowCount', rc)
        if cc > 0:
            self._add_number(wx, 'columnCount', cc)

        # 수평 헤더
        hh = widget.horizontalHeader()
        if not hh.isVisible():
            attr = SubElement(wx, 'attribute', name='horizontalHeaderVisible')
            SubElement(attr, 'bool').text = 'false'
        hh_dss = hh.defaultSectionSize()
        if hh_dss != 100:
            attr = SubElement(wx, 'attribute', name='horizontalHeaderDefaultSectionSize')
            SubElement(attr, 'number').text = str(hh_dss)
        if not hh.highlightSections():
            attr = SubElement(wx, 'attribute', name='horizontalHeaderHighlightSections')
            SubElement(attr, 'bool').text = 'false'
        hh_mss = hh.minimumSectionSize()
        if hh_mss != hh_dss and hh_mss > 0:
            attr = SubElement(wx, 'attribute', name='horizontalHeaderMinimumSectionSize')
            SubElement(attr, 'number').text = str(hh_mss)
        if hh.stretchLastSection():
            attr = SubElement(wx, 'attribute', name='horizontalHeaderStretchLastSection')
            SubElement(attr, 'bool').text = 'true'

        # 수직 헤더
        vh = widget.verticalHeader()
        if not vh.isVisible():
            attr = SubElement(wx, 'attribute', name='verticalHeaderVisible')
            SubElement(attr, 'bool').text = 'false'
        vh_dss = vh.defaultSectionSize()
        if vh_dss != 30:
            attr = SubElement(wx, 'attribute', name='verticalHeaderDefaultSectionSize')
            SubElement(attr, 'number').text = str(vh_dss)
        vh_mss = vh.minimumSectionSize()
        if vh_mss != vh_dss and vh_mss > 0:
            attr = SubElement(wx, 'attribute', name='verticalHeaderMinimumSectionSize')
            SubElement(attr, 'number').text = str(vh_mss)

        # 행 헤더
        for row in range(rc):
            vhi = widget.verticalHeaderItem(row)
            if vhi and vhi.text():
                row_elem = SubElement(wx, 'row')
                prop = SubElement(row_elem, 'property', name='text')
                SubElement(prop, 'string').text = vhi.text()

        # 열 헤더
        for col in range(cc):
            hhi = widget.horizontalHeaderItem(col)
            if hhi and hhi.text():
                col_elem = SubElement(wx, 'column')
                prop = SubElement(col_elem, 'property', name='text')
                SubElement(prop, 'string').text = hhi.text()

        # 셀 아이템
        for row in range(rc):
            for col in range(cc):
                item = widget.item(row, col)
                if item is None:
                    continue
                item_elem = SubElement(wx, 'item', row=str(row), column=str(col))

                text = item.text()
                if text:
                    prop = SubElement(item_elem, 'property', name='text')
                    SubElement(prop, 'string').text = text

                talign = item.textAlignment()
                if talign and talign != 0:
                    prop = SubElement(item_elem, 'property', name='textAlignment')
                    SubElement(prop, 'set').text = self._alignment_str(
                        QtCore.Qt.AlignmentFlag(talign))

                fg = item.foreground()
                if fg.style() == QtCore.Qt.BrushStyle.SolidPattern:
                    c = fg.color()
                    if c != QtGui.QColor(0, 0, 0):
                        self._add_brush(item_elem, 'foreground', c)

                bg = item.background()
                if bg.style() == QtCore.Qt.BrushStyle.SolidPattern:
                    c = bg.color()
                    if c.alpha() > 0:
                        self._add_brush(item_elem, 'background', c)

    # ── QComboBox ──
    def _write_combo_box(self, parent_xml, widget, name):
        wx = SubElement(parent_xml, 'widget')
        wx.set('class', 'QComboBox')
        wx.set('name', name)

        self._write_common_props(wx, widget)

        mvi = widget.maxVisibleItems()
        if mvi != 10:
            self._add_number(wx, 'maxVisibleItems', mvi)

        for i in range(widget.count()):
            it = SubElement(wx, 'item')
            prop = SubElement(it, 'property', name='text')
            SubElement(prop, 'string').text = widget.itemText(i)

    # ── QGroupBox ──
    def _write_group_box(self, parent_xml, widget, name):
        wx = SubElement(parent_xml, 'widget')
        wx.set('class', 'QGroupBox')
        wx.set('name', name)

        self._write_common_props(wx, widget)

        title = widget.title()
        if title:
            self._add_string(wx, 'title', title)

        layout = widget.layout()
        if layout:
            self._write_layout(wx, layout)

    # ── QScrollArea ──
    def _write_scroll_area(self, parent_xml, widget, name):
        wx = SubElement(parent_xml, 'widget')
        wx.set('class', 'QScrollArea')
        wx.set('name', name)

        self._write_common_props(wx, widget)

        if widget.widgetResizable():
            self._add_bool(wx, 'widgetResizable', True)

        hsp = widget.horizontalScrollBarPolicy()
        if hsp != QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded:
            self._add_enum(wx, 'horizontalScrollBarPolicy', f'Qt::{hsp.name}')

        fs = widget.frameShape()
        if fs != QtWidgets.QFrame.Shape.StyledPanel:
            self._add_enum(wx, 'frameShape', f'QFrame::{fs.name}')

        inner = widget.widget()
        if inner:
            self._processed.add(id(inner))
            iw = SubElement(wx, 'widget')
            iw.set('class', 'QWidget')
            iw.set('name', inner.objectName() or 'scrollAreaWidgetContents')

            g = inner.geometry()
            self._add_geometry(iw, g.x(), g.y(), g.width(), g.height())

            layout = inner.layout()
            if layout:
                self._write_layout(iw, layout)

    # ── QStackedWidget ──
    def _write_stacked_widget(self, parent_xml, widget, name):
        wx = SubElement(parent_xml, 'widget')
        wx.set('class', 'QStackedWidget')
        wx.set('name', name)

        self._write_common_props(wx, widget)
        self._add_number(wx, 'currentIndex', widget.currentIndex())

        for i in range(widget.count()):
            page = widget.widget(i)
            self._processed.add(id(page))
            pw = SubElement(wx, 'widget')
            pw.set('class', 'QWidget')
            pw.set('name', page.objectName() or f'page_{i}')

            layout = page.layout()
            if layout:
                self._write_layout(pw, layout)

    # ── QListWidget ──
    def _write_list_widget(self, parent_xml, widget, name):
        wx = SubElement(parent_xml, 'widget')
        wx.set('class', 'QListWidget')
        wx.set('name', name)

        self._write_common_props(wx, widget)

        sm = widget.selectionMode()
        if sm != QtWidgets.QAbstractItemView.SelectionMode.SingleSelection:
            self._add_enum(wx, 'selectionMode', f'QAbstractItemView::{sm.name}')

        for i in range(widget.count()):
            it = SubElement(wx, 'item')
            prop = SubElement(it, 'property', name='text')
            SubElement(prop, 'string').text = widget.item(i).text()

    # ── Line (QFrame) ──
    def _write_line(self, parent_xml, widget, name):
        wx = SubElement(parent_xml, 'widget')
        wx.set('class', 'Line')
        wx.set('name', name)

        self._write_common_props(wx, widget)

        if widget.frameShape() == QtWidgets.QFrame.Shape.HLine:
            self._add_enum(wx, 'orientation', 'Qt::Horizontal')
        else:
            self._add_enum(wx, 'orientation', 'Qt::Vertical')

    # ── Spacer ──
    def _write_spacer(self, parent_xml, spacer):
        sp = SubElement(parent_xml, 'spacer', name='')

        hpol = spacer.sizePolicy().horizontalPolicy()
        orient = ('Qt::Horizontal'
                  if hpol == QtWidgets.QSizePolicy.Policy.Expanding
                  else 'Qt::Vertical')
        self._add_enum(sp, 'orientation', orient)

        hint = spacer.sizeHint()
        prop = SubElement(sp, 'property', name='sizeHint')
        prop.set('stdset', '0')
        sz = SubElement(prop, 'size')
        SubElement(sz, 'width').text = str(hint.width())
        SubElement(sz, 'height').text = str(hint.height())

    # ── 속성 헬퍼 ──
    def _add_geometry(self, parent, x, y, w, h):
        prop = SubElement(parent, 'property', name='geometry')
        rect = SubElement(prop, 'rect')
        SubElement(rect, 'x').text = str(x)
        SubElement(rect, 'y').text = str(y)
        SubElement(rect, 'width').text = str(w)
        SubElement(rect, 'height').text = str(h)

    def _add_size(self, parent, name, size):
        prop = SubElement(parent, 'property', name=name)
        sz = SubElement(prop, 'size')
        SubElement(sz, 'width').text = str(size.width())
        SubElement(sz, 'height').text = str(size.height())

    def _add_font(self, parent, font):
        prop = SubElement(parent, 'property', name='font')
        f = SubElement(prop, 'font')
        SubElement(f, 'family').text = font.family()
        SubElement(f, 'pointsize').text = str(font.pointSize())
        if font.bold():
            SubElement(f, 'weight').text = str(font.weight())
            SubElement(f, 'bold').text = 'true'
        if font.underline():
            SubElement(f, 'underline').text = 'true'
        if font.italic():
            SubElement(f, 'italic').text = 'true'

    def _add_string(self, parent, name, text):
        prop = SubElement(parent, 'property', name=name)
        SubElement(prop, 'string').text = text

    def _add_number(self, parent, name, value):
        prop = SubElement(parent, 'property', name=name)
        SubElement(prop, 'number').text = str(int(value))

    def _add_bool(self, parent, name, value):
        prop = SubElement(parent, 'property', name=name)
        SubElement(prop, 'bool').text = 'true' if value else 'false'

    def _add_enum(self, parent, name, value):
        prop = SubElement(parent, 'property', name=name)
        SubElement(prop, 'enum').text = value

    def _add_set(self, parent, name, value):
        prop = SubElement(parent, 'property', name=name)
        SubElement(prop, 'set').text = value

    def _add_brush(self, parent, name, color):
        prop = SubElement(parent, 'property', name=name)
        brush = SubElement(prop, 'brush', brushstyle='SolidPattern')
        clr = SubElement(brush, 'color', alpha='255')
        SubElement(clr, 'red').text = str(color.red())
        SubElement(clr, 'green').text = str(color.green())
        SubElement(clr, 'blue').text = str(color.blue())

    # ── Enum 변환 ──
    def _alignment_str(self, align):
        parts = []
        a = int(align)
        if a & int(QtCore.Qt.AlignmentFlag.AlignLeft):
            parts.append('Qt::AlignLeft')
        if a & int(QtCore.Qt.AlignmentFlag.AlignRight):
            parts.append('Qt::AlignRight')
        if a & int(QtCore.Qt.AlignmentFlag.AlignHCenter):
            parts.append('Qt::AlignHCenter')
        if a & int(QtCore.Qt.AlignmentFlag.AlignTop):
            parts.append('Qt::AlignTop')
        if a & int(QtCore.Qt.AlignmentFlag.AlignBottom):
            parts.append('Qt::AlignBottom')
        if a & int(QtCore.Qt.AlignmentFlag.AlignVCenter):
            parts.append('Qt::AlignVCenter')
        return '|'.join(parts) if parts else 'Qt::AlignCenter'

    def _imh_str(self, imh):
        """InputMethodHint → .ui 문자열"""
        if hasattr(imh, 'name') and imh.name:
            return f'Qt::{imh.name}'
        # combined flags
        flag_map = {
            'ImhDigitsOnly': QtCore.Qt.InputMethodHint.ImhDigitsOnly,
            'ImhFormattedNumbersOnly': QtCore.Qt.InputMethodHint.ImhFormattedNumbersOnly,
            'ImhNone': QtCore.Qt.InputMethodHint.ImhNone,
        }
        parts = []
        for text, flag in flag_map.items():
            try:
                if imh & flag:
                    parts.append(f'Qt::{text}')
            except TypeError:
                pass
        return '|'.join(parts) if parts else 'Qt::ImhNone'


# ── 메인 ──

def main():
    app = QApplication(sys.argv)

    base = Path(__file__).parent
    proto_path = base / 'DataTool_dev' / 'DataTool_optRCD_proto_.py'
    output_path = base / 'DataTool_dev' / 'DataTool_UI.ui'

    print(f"소스: {proto_path.name}")
    print(f"출력: {output_path.name}")

    UiClass = load_ui_class(proto_path)

    win = QMainWindow()
    ui = UiClass()
    ui.setupUi(win)
    ui.retranslateUi(win)

    builder = UiXmlBuilder(ui, win)
    xml_str = builder.build()

    output_path.write_text(xml_str, encoding='utf-8')
    print(f"완료: {output_path.name} ({len(xml_str):,} bytes)")

    app.quit()
    return 0


if __name__ == '__main__':
    sys.exit(main())
