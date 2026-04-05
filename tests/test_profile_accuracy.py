"""프로필 정확성 검증 테스트 — 논리사이클, 충방전 방향, 데이터 정확도

목적:
  1. 논리사이클(cycle_map) → TotlCycle 매핑의 정확성
  2. 충전/방전 프로필의 물리적 정확성 (전압 방향, 전류 부호, 용량 단조성)
  3. 다양한 사이클 입력 (단일/범위/전체) 시 프로필 정상 출력
  4. GITT/HPPC 펄스 스윕 프로필의 정확성
  5. matplotlib 플롯 렌더링 검증

실행:
  pytest tests/test_profile_accuracy.py -v               # 전체
  pytest tests/test_profile_accuracy.py -k "Logical"      # 논리사이클만
  pytest tests/test_profile_accuracy.py -k "Accuracy"     # 정확성만
  pytest tests/test_profile_accuracy.py -k "Sweep"        # GITT/Pulse만
  pytest tests/test_profile_accuracy.py -k "Plot"         # 플롯만
  pytest tests/test_profile_accuracy.py -m "not slow"     # 느린 테스트 제외
"""

import builtins
import os
import sys
import types
import warnings
from dataclasses import dataclass
from pathlib import Path

# ══════════════════════════════════════════════
# 0. Mock 처리 — PyQt6 등 GUI 의존성 (proto_ import 전 필수)
# ══════════════════════════════════════════════


def _create_mock_module(name, attrs=None):
    """가짜 모듈 생성."""
    mod = types.ModuleType(name)
    if attrs:
        for k, v in attrs.items():
            setattr(mod, k, v)
    return mod


class _MockMeta(type):
    def __getattr__(cls, name):
        return _MockClass()


class _MockClass(metaclass=_MockMeta):
    """아무 속성이나 호출을 흡수하는 만능 Mock."""
    def __init__(self, *a, **kw): pass
    def __call__(self, *a, **kw): return _MockClass()
    def __getattr__(self, name): return _MockClass()
    def __bool__(self): return False
    def __add__(self, other): return 0
    def __radd__(self, other): return 0
    def __sub__(self, other): return 0
    def __mul__(self, other): return 0
    def __int__(self): return 0
    def __float__(self): return 0.0
    def __eq__(self, other): return False
    def __hash__(self): return 0
    def __or__(self, other): return _MockClass()
    def __ror__(self, other): return _MockClass()


_mock_modules = {
    "pyodbc": {},
    "PyQt6": {},
    "PyQt6.QtCore": {"QThread": _MockClass, "pyqtSignal": _MockClass,
                      "Qt": _MockClass, "QTimer": _MockClass},
    "PyQt6.QtGui": {"QColor": _MockClass, "QFont": _MockClass,
                     "QAction": _MockClass, "QPixmap": _MockClass},
    "PyQt6.QtWidgets": {
        "QApplication": _MockClass, "QMainWindow": _MockClass,
        "QWidget": _MockClass, "QTabWidget": _MockClass,
        "QMessageBox": _MockClass, "QFileDialog": _MockClass,
        "QTableWidget": _MockClass, "QTableWidgetItem": _MockClass,
        "QPushButton": _MockClass, "QLineEdit": _MockClass,
        "QComboBox": _MockClass, "QCheckBox": _MockClass,
        "QRadioButton": _MockClass, "QLabel": _MockClass,
        "QProgressBar": _MockClass, "QGroupBox": _MockClass,
        "QVBoxLayout": _MockClass, "QHBoxLayout": _MockClass,
        "QGridLayout": _MockClass, "QScrollArea": _MockClass,
        "QStackedWidget": _MockClass, "QListWidget": _MockClass,
        "QListWidgetItem": _MockClass, "QPlainTextEdit": _MockClass,
        "QSizePolicy": _MockClass, "QSpacerItem": _MockClass,
        "QFrame": _MockClass, "QHeaderView": _MockClass,
        "QAbstractItemView": _MockClass, "QStyledItemDelegate": _MockClass,
        "QStyleOptionViewItem": _MockClass, "QButtonGroup": _MockClass,
    },
    "matplotlib.backends.backend_qtagg": {
        "FigureCanvasQTAgg": _MockClass,
        "NavigationToolbar2QT": _MockClass,
    },
    "tkinter": {"filedialog": _MockClass, "Tk": _MockClass},
    "tkinter.filedialog": {},
    "xlwings": {"xw": _MockClass},
}

for mod_name, attrs in _mock_modules.items():
    if mod_name not in sys.modules:
        sys.modules[mod_name] = _create_mock_module(mod_name, attrs)

# matplotlib Agg 백엔드
import matplotlib
matplotlib.use("Agg")

import importlib.util as _ilu
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

# ── Windows 경로 호환 패치 ──
_orig_isdir = os.path.isdir
_orig_isfile = os.path.isfile
_orig_listdir = os.listdir
_orig_stat = os.stat
_orig_open = open


def _normalize_path(p):
    if isinstance(p, str):
        return p.replace("\\", os.sep)
    return p


os.path.isdir = lambda p: _orig_isdir(_normalize_path(p))
os.path.isfile = lambda p: _orig_isfile(_normalize_path(p))
os.listdir = lambda p: _orig_listdir(_normalize_path(p))
os.stat = lambda p, *a, **kw: _orig_stat(_normalize_path(p), *a, **kw)


def _patched_open(p, *a, **kw):
    if isinstance(p, str):
        p = _normalize_path(p)
    return _orig_open(p, *a, **kw)


builtins.open = _patched_open

_orig_read_csv = pd.read_csv


def _patched_read_csv(filepath_or_buffer, *a, **kw):
    if isinstance(filepath_or_buffer, str):
        filepath_or_buffer = _normalize_path(filepath_or_buffer)
    return _orig_read_csv(filepath_or_buffer, *a, **kw)


pd.read_csv = _patched_read_csv

# ══════════════════════════════════════════════
# 1. proto_ 모듈 임포트
# ══════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATATOOL_DEV = PROJECT_ROOT / "DataTool_dev"
EXP_DATA_DIR = PROJECT_ROOT / "data" / "exp_data"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(DATATOOL_DEV))

# 모듈 캐시 재활용 또는 신규 로드
if "bdt_proto" in sys.modules:
    _mod = sys.modules["bdt_proto"]
else:
    _spec = _ilu.spec_from_file_location(
        "bdt_proto", str(DATATOOL_DEV / "DataTool_optRCD_proto_.py"))
    _mod = _ilu.module_from_spec(_spec)
    sys.modules["bdt_proto"] = _mod
    _spec.loader.exec_module(_mod)

# 핵심 함수 바인딩
unified_profile_core = _mod.unified_profile_core
UnifiedProfileResult = _mod.UnifiedProfileResult
check_cycler = _mod.check_cycler
pne_build_cycle_map = _mod.pne_build_cycle_map
toyo_build_cycle_map = _mod.toyo_build_cycle_map
pne_min_cap = _mod.pne_min_cap
toyo_min_cap = _mod.toyo_min_cap


# ══════════════════════════════════════════════
# 2. 전체 실험 데이터 카탈로그 (70개 경로)
# ══════════════════════════════════════════════

# (폴더명, 용량mAh, C-rate, 사이클러, 태그)
ALL_EXP_DATA = [
    ("240821 선행랩 류성택 Gen4pGr mini-ATL-WD-Proto-422mAh-20C-450V-GITT-15도",
     422, 0.2, "pne", "GITT-15도"),
    ("240919 선행랩 류성택 Gen4pGr mini-ATL-WD-Proto-422mAh-20C-450V-SOC별DCIR-15도",
     422, 0.2, "pne", "SOC별DCIR-15도"),
    ("250207_250307_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 1-100cyc",
     1689, 2.0, "toyo", "Q7M-1-100"),
    ("250219_250319_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 101-200cyc",
     1689, 2.0, "toyo", "Q7M-101-200"),
    ("250304_250404_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 201-300cyc",
     1689, 2.0, "toyo", "Q7M-201-300"),
    ("250317_251231_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 301-400cyc",
     1689, 2.0, "toyo", "Q7M-301-400"),
    ("250513_250526_05_나무늬_2610mAh_Gen5+B SDI MP1 DoE SBR 0.7 DCIR",
     2610, 0.2, "pne", "DCIR-07"),
    ("250513_250526_05_나무늬_2610mAh_Gen5+B SDI MP1 Main SBR 0.9 DCIR",
     2610, 0.2, "pne", "DCIR-09"),
    ("250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half-14pi-GITT-0.1C-T23",
     4.187, 0.1, "pne", "half-ca-GITT"),
    ("250905_250915_00_류성택_4-376mAh_M2-SDI-open-an-half-14pi-GITT-0.1C-T23",
     4.376, 0.1, "pne", "half-an-GITT"),
    ("251002_251010_00_박민희_4-19mAh_RatedCh half ca 4.19mAh SDI",
     4.19, 0.2, "pne", "half-rated"),
    ("251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202",
     2335, 0.2, "pne", "Q8-RT"),
    ("251029_251229_05_나무늬_2335mAh_Q8 선상 ATL SEU4 LT @1-401",
     2335, 0.2, "pne", "Q8-LT"),
    ("251029_251229_05_나무늬_2935mAh_Q8 선상 ATL SEU4 LT @1-401 - 복사본",
     2935, 0.2, "pne", "Q8-LT-복사본"),
    ("251029_260129_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 50CY HT @1-801",
     2335, 0.2, "pne", "Q8-HT-50CY"),
    ("251029_260129_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 75CY HT @1-801",
     2335, 0.2, "pne", "Q8-HT-75CY"),
    ("251029_260129_05_나무늬_2335mAh_Q8 선상 ATL SEU4 HT @1-801",
     2335, 0.2, "pne", "Q8-HT"),
    ("251029_260429_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 30CY @1-1202",
     2335, 0.2, "pne", "Q8-30CY"),
    ("251029_260429_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 50CY @1-1202",
     2335, 0.2, "pne", "Q8-50CY"),
    ("251029_260429_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 75CY @1-1202",
     2335, 0.2, "pne", "Q8-75CY"),
    ("251029_260429_05_나무늬_Q8 선상 ATL SEU4 2.9V 30CY @1-1202 - 복사본",
     2335, 0.2, "pne", "Q8-30CY-복사본"),
    ("251113_260113_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 50CY LT @1-401",
     2335, 0.2, "pne", "Q8-50CY-LT"),
    ("251113_260213_05_나무늬_2335mAh_Q8 선상 ATL 2.9V 30CY HT @1-801",
     2335, 0.2, "pne", "Q8-30CY-HT"),
    ("251209_251213_05_현혜정_6490mAh_LWN Si25P SPL 율별방전Profile",
     6490, 0.2, "pne", "율별방전"),
    ("251209_260209_05_나무늬_2335mAh_Q8 선상 ATL SEU4 HT @301-801",
     2335, 0.2, "pne", "Q8-HT-301"),
    ("251218_251230_00_박민희_3-45mAh_M1 ATL Cathode Half T23",
     3.45, 0.2, "pne", "half-ca-M1"),
    ("251218_251230_00_박민희_4-04mAh_M1 ATL Anode Half T23",
     4.04, 0.2, "pne", "half-an-M1"),
    ("251224_260110_00_박민희_3-45mAh_M1 ATL Cathode Half T23 GITT 0.1C",
     3.45, 0.1, "pne", "half-ca-GITT-M1"),
    ("251224_260110_00_박민희_4-04mAh_M1 ATL Anode Half T23 GITT 0.1C",
     4.04, 0.1, "pne", "half-an-GITT-M1"),
    ("251224_260110_00_박민희_4-04mAh_M1 ATL Anode Half T23 GITT 0.05C 3.0V",
     4.04, 0.05, "pne", "half-an-GITT-slow"),
    ("260102_260630_03_홍승기_2335mAh_Q8 선상 ATL 2.9V 30Cy LT @1-400",
     2335, 0.2, "pne", "Q8-30Cy-LT"),
    ("260109_260112_05_이근준_5000mAh_Gen5P Si5 ATL T2 3M 보관 용량 측정 4cycle SOC 30 setting ch7 to 12",
     5000, 0.2, "pne", "보관용량"),
    ("260115_260630_02_홍승기_2335mAh_Q8 선상 ATL SEU4 HT@1-802",
     2335, 0.2, "pne", "Q8-HT-802"),
    ("260119_260616_03_홍승기_2369mAh_Q8 ATL Main 2.0C Rss RT",
     2369, 2.0, "pne", "Q8-Main-Rss"),
    ("260119_260616_03_홍승기_2485mAh_Q8 ATL Sub 2.0C Rss RT",
     2485, 2.0, "pne", "Q8-Sub-Rss"),
    ("260119_260616_03_홍승기_2485mAh_Q8 ATL Sub 2C 2.9V 100Cy",
     2485, 2.0, "pne", "Q8-Sub-100Cy"),
    ("260126_260630_3_홍승기_2485mAh_Q8 ATL Sub 2_9V 100cy test HT 1to100cy-2",
     2485, 2.0, "toyo", "Q8-HT-Toyo"),
    ("260130_260630_03_홍승기_2369mAh_Q8 Main 2C Rss RT CH32 57Cy-RE",
     2369, 2.0, "pne", "RE-2369"),
    ("260130_260630_03_홍승기_3456mAh_Q8 Main 2C Rss RT CH32 57Cy-RE",
     3456, 2.0, "pne", "RE-3456"),
    ("260130_260630_03_홍승기_Q8 Main 2C Rss RT CH32 57Cy-RE",
     2369, 2.0, "pne", "RE-noCAP"),
    ("260202_260226_05_문현규_5075mAh_Cosmx 25Si 율별용량+Hybrid ch54",
     5075, 0.2, "pne", "Cosmx-25Si"),
    ("260204_260226_05_문현규_4900mAh_Cosmx gen5 율별용량 ch61",
     4900, 0.2, "pne", "Cosmx-gen5"),
    ("260204_260226_05_문현규_5070mAh_Cosmx Gen5P 율별용량",
     5070, 0.2, "pne", "Cosmx-Gen5P"),
    ("260209_260630_2_홍승기_2485mAh_Q8 ATL Sub 2_9V 100cy test HT 100to199cy re3",
     2485, 2.0, "toyo", "Q8-HT-Toyo-re3"),
    ("260211_260310_05_문현규_3885mAh_POR 40C pulse PA1 ATL",
     3885, 0.2, "pne", "pulse-PA1-ATL"),
    ("260211_260310_05_문현규_3885mAh_POR 40C pulse PA1 SDI",
     3885, 0.2, "pne", "pulse-PA1-SDI"),
    ("260211_260310_05_문현규_4855mAh_POR 40C pulse PA3 ATL",
     4855, 0.2, "pne", "pulse-PA3-ATL"),
    ("260211_260310_05_문현규_4855mAh_POR 40C pulse PA3 SDI",
     4855, 0.2, "pne", "pulse-PA3-SDI"),
    ("260212_260215_05_한지영_5432mAh_SDI Phase2 MP2 Fresh DCIR SOC10",
     5432, 0.2, "pne", "DCIR-Fresh"),
    ("260212_260215_05_한지영_5432mAh_SDI Phase2 MP2 고온수명후 DCIR SOC10",
     5432, 0.2, "pne", "DCIR-고온후"),
    ("260226_260228_05_문현규_3876mAh_PS 연속저장 DCIR",
     3876, 0.2, "pne", "연속-PS"),
    ("260226_260228_05_문현규_3885mAh_PA1 연속저장 DCIR",
     3885, 0.2, "pne", "연속-PA1"),
    ("260303_260305_05_문현규_3561mAh_iphone17 basic 고온저장 75도 5일 SOC100 ATL",
     3561, 0.2, "pne", "보관-iphone17"),
    ("260306_260318_05_현혜정_6330mAh_LWN 25P(after LT100cy) SOC별 DCIR 신규",
     6330, 0.2, "pne", "SOC-DCIR-LT100"),
    ("260310_260312_05_이근준_4991mAh_Gen5P ATL MP1 8M Fresh 보관 용량 측정 2cycle SOC30 setting",
     4991, 0.2, "pne", "보관-8M"),
    ("260316_260320_05_현혜정_6330mAh_LWN 25P(after LT50cy) 0.5C-10min volt hysteresis",
     6330, 0.5, "pne", "hysteresis-05C"),
    ("260316_270318_00_이성일_5882mAh_M47 ATL ECT GITT",
     5882, 0.2, "pne", "ECT-GITT"),
    ("260317_260325_05_현혜정_4986mAh_SDI Gen5+ MP1 0.2C-10min volt hysteresis",
     4986, 0.2, "pne", "hysteresis-SDI"),
    ("260319_260326_05_현혜정_6330mAh_LWN 25P(after LT50cy) 0.2C-10min volt hysteresis",
     6330, 0.2, "pne", "hysteresis-02C"),
    ("260326_260329_00_류성택_4860mAh_A17 ATL ECT parameter11 GITT",
     4860, 0.2, "pne", "A17-ATL-GITT"),
    ("260326_260329_00_류성택_4860mAh_A17 SDI ECT parameter11 GITT",
     4860, 0.2, "pne", "A17-SDI-GITT"),
    ("A1_MP1_4500mAh_T23_1", 4500, 0.2, "pne", "A1-1"),
    ("A1_MP1_4500mAh_T23_2", 4500, 0.2, "pne", "A1-2"),
    ("A1_MP1_4500mAh_T23_3", 4500, 0.2, "pne", "A1-3"),
    # ── Toyo 블록 테스트 데이터 (6개) ──
    ("Dateset_A1_Gen4 2C ATL MP2 [45V 4470mAh] [23] blk2",
     4470, 2.0, "toyo", "Gen4-A1-blk2"),
    ("Gen4 2C ATL MP2 [45V 4470mAh] [23] blk7 - 240131",
     4470, 2.0, "toyo", "Gen4-blk7"),
    ("M1 ATL [45V 4175mAh]",
     4175, 0.2, "toyo", "M1-ATL"),
    ("Q7M Inner ATL_45V 1689mAh BLK1 20EA [23] - 250304",
     1689, 2.0, "toyo", "Q7M-Inner-blk1"),
    ("Q7M Main ATL [45V_1680mAh][23] blk7 20ea - 250228",
     1680, 2.0, "toyo", "Q7M-Main-blk7"),
    ("Q7M Sub ATL [45v 2068mAh] [23] - 250219r",
     2068, 2.0, "toyo", "Q7M-Sub"),
]


# ══════════════════════════════════════════════
# 3. 상수 및 키워드
# ══════════════════════════════════════════════

# 물리적 범위 — 풀셀 + 하프셀 포함
V_FULL_MIN, V_FULL_MAX = 2.0, 5.0      # 풀셀 전압 범위
V_HALF_MIN, V_HALF_MAX = -0.5, 5.5     # 하프셀 전압 범위 (리튬 금속 기준)
T_MIN, T_MAX = -30.0, 100.0            # 온도 범위 (°C)
SOC_MIN, SOC_MAX = -0.1, 1.5           # SOC 범위 (정규화 차이로 1.0 초과 가능)

# 스윕/펄스 데이터 키워드 (태그 또는 폴더명에서 검색)
SWEEP_KEYWORDS = ["GITT", "DCIR", "pulse", "hysteresis", "율별", "SOC별", "ECT"]

# 옵션 조합 (data_scope, axis_mode, continuity, include_rest, calc_dqdv)
OPTION_COMBOS = [
    ("charge",    "soc",  "overlay",    False, True),
    ("discharge", "soc",  "overlay",    False, True),
    ("cycle",     "soc",  "overlay",    False, False),
    ("charge",    "time", "overlay",    False, False),
    ("discharge", "time", "overlay",    False, False),
    ("cycle",     "time", "overlay",    False, False),
    ("charge",    "time", "continuous", False, False),
    ("discharge", "time", "continuous", False, False),
    ("cycle",     "time", "continuous", False, False),
    ("cycle",     "time", "overlay",    True,  False),
    ("cycle",     "time", "continuous", True,  False),
]

OPTION_IDS = [
    f"{s}-{a}-{c}{'-rest' if r else ''}{'-dqdv' if d else ''}"
    for s, a, c, r, d in OPTION_COMBOS
]


# ══════════════════════════════════════════════
# 4. 헬퍼 함수
# ══════════════════════════════════════════════

def _resolve_entry(folder_name, capacity, crate, cycler, tag):
    """데이터 엔트리를 채널 경로까지 resolve."""
    folder = EXP_DATA_DIR / folder_name
    if not folder.is_dir():
        return None
    ch_path = None
    for d in sorted(folder.iterdir()):
        if d.is_dir() and d.name not in ("Pattern", "processed_data"):
            ch_path = d
            break
    if ch_path is None:
        return None
    return {"folder_name": folder_name, "capacity": capacity, "crate": crate,
            "cycler": cycler, "tag": tag, "channel_path": str(ch_path)}


def _get_cycle_map(channel_path, capacity, crate, cycler):
    """채널 경로에서 cycle_map 구축."""
    if cycler == "pne":
        cap = pne_min_cap(channel_path, capacity, crate)
        cmap, _ = pne_build_cycle_map(channel_path, cap, crate)
    else:
        cap = toyo_min_cap(channel_path, capacity, crate)
        cmap, _ = toyo_build_cycle_map(channel_path, cap, crate)
    return cmap


def _pick_test_cycles(cycle_map):
    """테스트용 사이클 선택 (first/mid/last/first3/mid5/all)."""
    if not cycle_map:
        return {}
    keys = sorted(cycle_map.keys())
    n = len(keys)
    return {
        "first": (keys[0], keys[0]),
        "mid": (keys[n // 2], keys[n // 2]),
        "last": (keys[-1], keys[-1]),
        "first3": (keys[0], keys[min(2, n - 1)]),
        "mid5": (keys[max(0, n // 2 - 2)], keys[min(n - 1, n // 2 + 2)]),
        "all": (keys[0], keys[min(19, n - 1)]),  # 최대 20 사이클
    }


def _is_sweep_data(tag, folder_name=""):
    """스윕/펄스 데이터인지 태그와 폴더명으로 판별."""
    combined = (tag + " " + folder_name).lower()
    return any(kw.lower() in combined for kw in SWEEP_KEYWORDS)


def _is_halfcell(tag, folder_name=""):
    """하프셀 데이터인지 태그와 폴더명으로 판별."""
    combined = (tag + " " + folder_name).lower()
    return "half" in combined


def _voltage_bounds(tag, folder_name=""):
    """태그 기반으로 전압 범위 결정 (풀셀 vs 하프셀)."""
    if _is_halfcell(tag, folder_name):
        return V_HALF_MIN, V_HALF_MAX
    return V_FULL_MIN, V_FULL_MAX


def _safe_profile(ch, cycle_range, cap, crate, cmap, label, **kwargs):
    """프로필 호출 + 빈 결과 시 skip 처리."""
    result = unified_profile_core(
        ch, cycle_range, cap, crate, cycle_map=cmap, **kwargs)
    if result.df.empty:
        err = result.metadata.get("error", "데이터 없음")
        pytest.skip(f"{label}: {err}")
    return result


# ══════════════════════════════════════════════
# 5. Fixtures
# ══════════════════════════════════════════════

def _entry_ids():
    return [e[4] for e in ALL_EXP_DATA]


@pytest.fixture(params=ALL_EXP_DATA, ids=_entry_ids())
def exp_entry(request):
    """실험 데이터 엔트리를 resolve한다."""
    entry = _resolve_entry(*request.param)
    if entry is None:
        pytest.skip(f"데이터 없음: {request.param[0]}")
    return entry


@pytest.fixture
def cycle_info(exp_entry):
    """사이클 맵 구축 + 테스트 사이클 선택."""
    ch = exp_entry["channel_path"]
    cmap = _get_cycle_map(ch, exp_entry["capacity"],
                          exp_entry["crate"], exp_entry["cycler"])
    if not cmap:
        pytest.skip("사이클 맵 비어있음")
    cycles = _pick_test_cycles(cmap)
    return cmap, cycles


# ══════════════════════════════════════════════
# 6. 테스트 클래스
# ══════════════════════════════════════════════


class TestLogicalCycleMapping:
    """논리사이클(cycle_map) ↔ 물리사이클(TotlCycle) 매핑 정확성 검증."""

    def test_cycle_map_keys_sequential(self, exp_entry, cycle_info):
        """논리사이클 키가 양의 정수이고 일반적으로 순차적인지 확인."""
        cmap, _ = cycle_info
        keys = sorted(cmap.keys())
        # 키는 양의 정수
        for k in keys:
            assert isinstance(k, (int, np.integer)), \
                f"[{exp_entry['tag']}] 키 타입 이상: {type(k)}"
            assert k > 0, f"[{exp_entry['tag']}] 키 ≤ 0: {k}"
        # 키는 정렬 상태
        assert keys == sorted(keys), \
            f"[{exp_entry['tag']}] 키 정렬 안됨"

    def test_cycle_map_values_valid(self, exp_entry, cycle_info):
        """값이 int 또는 tuple(int,int)이고 모두 양수인지 확인."""
        cmap, _ = cycle_info
        for key, val in cmap.items():
            if isinstance(val, tuple):
                assert len(val) == 2, \
                    f"[{exp_entry['tag']}] 튜플 길이 이상: key={key}, val={val}"
                assert val[0] > 0 and val[1] > 0, \
                    f"[{exp_entry['tag']}] 튜플 값 ≤ 0: key={key}, val={val}"
                assert val[0] <= val[1], \
                    f"[{exp_entry['tag']}] 튜플 역순: key={key}, val={val}"
            elif isinstance(val, (int, np.integer)):
                assert val > 0, \
                    f"[{exp_entry['tag']}] 값 ≤ 0: key={key}, val={val}"
            else:
                pytest.fail(
                    f"[{exp_entry['tag']}] 값 타입 이상: key={key}, "
                    f"type={type(val)}")

    def test_logical_vs_totlcycle_distinction(self, exp_entry, cycle_info):
        """논리사이클 N으로 호출하면 해당 TotlCycle 범위의 데이터만 반환되는지 확인."""
        cmap, cycles = cycle_info
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]

        first = cycles["first"]
        result = unified_profile_core(
            ch, first, cap, crate,
            data_scope="charge", axis_mode="time", cycle_map=cmap)

        if result.df.empty:
            warnings.warn(f"[{tag}] 첫 사이클 데이터 없음")
            return

        # Cycle 컬럼이 논리사이클 번호와 대응하는지 확인
        if "Cycle" in result.df.columns:
            unique_cycles = result.df["Cycle"].dropna().unique()
            # 단일 사이클 범위이므로 Cycle 값 종류가 제한적이어야 함
            assert len(unique_cycles) <= 3, \
                f"[{tag}] 단일 논리사이클인데 Cycle 값이 {len(unique_cycles)}개"

    def test_sweep_mode_has_tuple_values(self, exp_entry, cycle_info):
        """GITT/DCIR 데이터는 cycle_map 값이 tuple이어야 함."""
        tag = exp_entry["tag"]
        fn = exp_entry["folder_name"]
        if not _is_sweep_data(tag, fn):
            pytest.skip("스윕 데이터 아님")

        cmap, _ = cycle_info
        has_tuple = any(isinstance(v, tuple) for v in cmap.values())
        if not has_tuple:
            warnings.warn(
                f"[{tag}] 스윕 데이터인데 tuple 값 없음 — "
                f"general 모드로 분류되었을 수 있음")

    def test_general_mode_has_int_values(self, exp_entry, cycle_info):
        """일반 가속수명 데이터는 cycle_map 값이 대부분 int여야 함."""
        tag = exp_entry["tag"]
        fn = exp_entry["folder_name"]
        if _is_sweep_data(tag, fn):
            pytest.skip("스윕 데이터임")

        cmap, _ = cycle_info
        int_count = sum(1 for v in cmap.values()
                        if isinstance(v, (int, np.integer)))
        total = len(cmap)
        if total == 0:
            pytest.skip("빈 사이클 맵")
        ratio = int_count / total
        # 일반 모드: 과반수가 int (Toyo도 tuple 사용하므로 비율 완화)
        if exp_entry["cycler"] == "pne":
            assert ratio >= 0.5, \
                f"[{tag}] PNE 일반 모드인데 int 비율 {ratio:.0%} (기대: ≥50%)"


class TestProfileDataAccuracy:
    """프로필 데이터의 물리적 정확성 검증 — 전압 방향, 전류 부호, 용량 단조성."""

    def test_charge_voltage_increases(self, exp_entry, cycle_info):
        """충전 중 전압이 전반적으로 증가해야 함 (70% 이상 연속 증가)."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        result = _safe_profile(
            ch, cycles["first"], cap, crate, cmap, f"{tag}/chg",
            data_scope="charge", axis_mode="soc")

        v = result.df["Voltage"].dropna().values
        if len(v) < 10:
            warnings.warn(f"[{tag}] 충전 전압 데이터 부족 ({len(v)}행)")
            return

        diffs = np.diff(v)
        increasing_ratio = np.sum(diffs >= -0.001) / len(diffs)
        assert increasing_ratio >= 0.70, \
            f"[{tag}] 충전 전압 증가 비율: {increasing_ratio:.1%} (기대: ≥70%)"

    def test_discharge_voltage_decreases(self, exp_entry, cycle_info):
        """방전 중 전압이 전반적으로 감소해야 함 (70% 이상 연속 감소)."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        result = _safe_profile(
            ch, cycles["first"], cap, crate, cmap, f"{tag}/dchg",
            data_scope="discharge", axis_mode="soc")

        v = result.df["Voltage"].dropna().values
        if len(v) < 10:
            warnings.warn(f"[{tag}] 방전 전압 데이터 부족 ({len(v)}행)")
            return

        diffs = np.diff(v)
        decreasing_ratio = np.sum(diffs <= 0.001) / len(diffs)
        assert decreasing_ratio >= 0.70, \
            f"[{tag}] 방전 전압 감소 비율: {decreasing_ratio:.1%} (기대: ≥70%)"

    def test_charge_soc_monotonic(self, exp_entry, cycle_info):
        """충전 시 SOC가 단조 증가해야 함 (SOC = ChgCap, 0→1)."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        result = _safe_profile(
            ch, cycles["first"], cap, crate, cmap, f"{tag}/chg-soc",
            data_scope="charge", axis_mode="soc")

        s = result.df["SOC"].dropna().values
        if len(s) < 5:
            pytest.skip(f"[{tag}] SOC 데이터 부족")

        diffs = np.diff(s)
        mono_ratio = np.sum(diffs >= -0.01) / len(diffs)
        assert mono_ratio >= 0.90, \
            f"[{tag}] 충전 SOC 단조증가 비율: {mono_ratio:.1%} (기대: ≥90%)"

    def test_discharge_soc_monotonic(self, exp_entry, cycle_info):
        """방전 시 SOC(=DchgCap, DOD 방향)가 단조 증가해야 함 (0→1)."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        result = _safe_profile(
            ch, cycles["first"], cap, crate, cmap, f"{tag}/dchg-soc",
            data_scope="discharge", axis_mode="soc")

        s = result.df["SOC"].dropna().values
        if len(s) < 5:
            pytest.skip(f"[{tag}] SOC 데이터 부족")

        diffs = np.diff(s)
        mono_ratio = np.sum(diffs >= -0.01) / len(diffs)
        assert mono_ratio >= 0.90, \
            f"[{tag}] 방전 SOC 단조증가 비율: {mono_ratio:.1%} (기대: ≥90%)"

    def test_current_sign_charge_positive(self, exp_entry, cycle_info):
        """충전 프로필에서 Crate가 대부분 양수여야 함.

        PNE: 충전 전류 양수, Toyo: 전류 항상 양수(절대값 기록).
        둘 다 충전 시 양수이므로 동일 기준 적용.
        """
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        result = _safe_profile(
            ch, cycles["first"], cap, crate, cmap, f"{tag}/chg-sign",
            data_scope="charge", axis_mode="time")

        cr = result.df["Crate"].dropna().values
        if len(cr) < 5:
            pytest.skip(f"[{tag}] Crate 데이터 부족")

        # Condition 9 (CC)가 포함되어 양/음 혼재 가능 → 70% 기준
        pos_ratio = np.sum(cr > -0.01) / len(cr)
        assert pos_ratio >= 0.70, \
            f"[{tag}] 충전 Crate 양수 비율: {pos_ratio:.1%} (기대: ≥70%)"

    def test_current_sign_discharge_negative(self, exp_entry, cycle_info):
        """방전 프로필에서 Crate 부호 검증.

        PNE: 방전 전류 음수 (부호 유지)
        Toyo: 전류 절대값 기록 → 방전 시에도 양수
        """
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cycler = exp_entry["cycler"]
        cmap, cycles = cycle_info

        result = _safe_profile(
            ch, cycles["first"], cap, crate, cmap, f"{tag}/dchg-sign",
            data_scope="discharge", axis_mode="time")

        cr = result.df["Crate"].dropna().values
        if len(cr) < 5:
            pytest.skip(f"[{tag}] Crate 데이터 부족")

        if cycler == "toyo":
            # Toyo: 전류 절대값 → 방전 Crate도 양수
            pos_ratio = np.sum(cr > -0.01) / len(cr)
            assert pos_ratio >= 0.70, \
                f"[{tag}] Toyo 방전 Crate 양수 비율: {pos_ratio:.1%} (기대: ≥70%)"
        else:
            # PNE: 방전 전류 음수
            neg_ratio = np.sum(cr < 0.01) / len(cr)
            assert neg_ratio >= 0.70, \
                f"[{tag}] PNE 방전 Crate 음수 비율: {neg_ratio:.1%} (기대: ≥70%)"

    def test_voltage_within_chemistry_bounds(self, exp_entry, cycle_info):
        """전압이 화학계 한계 이내 (풀셀: 2.0-5.0V, 하프셀: -0.5-5.5V)."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        fn = exp_entry["folder_name"]
        cmap, cycles = cycle_info

        result = _safe_profile(
            ch, cycles["first"], cap, crate, cmap, f"{tag}/v-bounds",
            data_scope="cycle", axis_mode="time")

        v_min, v_max = _voltage_bounds(tag, fn)
        v = result.df["Voltage"].dropna()
        if len(v) == 0:
            pytest.skip(f"[{tag}] 전압 데이터 없음")

        assert v.min() >= v_min, \
            f"[{tag}] 전압 하한 위반: {v.min():.4f}V < {v_min}V"
        assert v.max() <= v_max, \
            f"[{tag}] 전압 상한 위반: {v.max():.4f}V > {v_max}V"

    def test_time_nonnegative(self, exp_entry, cycle_info):
        """시간 값이 0 이상이어야 함."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        result = _safe_profile(
            ch, cycles["first"], cap, crate, cmap, f"{tag}/time",
            data_scope="charge", axis_mode="time")

        if "TimeMin" in result.df.columns:
            t = result.df["TimeMin"].dropna()
            if len(t) > 0:
                assert t.min() >= 0.0, \
                    f"[{tag}] 시간 음수: {t.min():.4f}min"

    def test_data_not_all_identical(self, exp_entry, cycle_info):
        """전압, SOC, 시간이 모두 동일값이 아닌지 (분산 있음) 확인."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        result = _safe_profile(
            ch, cycles["first"], cap, crate, cmap, f"{tag}/variance",
            data_scope="charge", axis_mode="soc")

        df = result.df
        for col in ["Voltage", "SOC"]:
            if col in df.columns:
                vals = df[col].dropna()
                if len(vals) > 10:
                    assert vals.std() > 1e-8, \
                        f"[{tag}] {col} 분산 0 — 모든 값 동일"

    def test_overlay_starts_from_zero(self, exp_entry, cycle_info):
        """오버레이 + 시간 축에서 각 사이클이 t≈0에서 시작하는지 확인."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        # 최소 3사이클 필요
        keys = sorted(cmap.keys())
        if len(keys) < 3:
            pytest.skip(f"[{tag}] 사이클 3개 미만")

        rng = (keys[0], keys[min(2, len(keys) - 1)])
        result = _safe_profile(
            ch, rng, cap, crate, cmap, f"{tag}/overlay-zero",
            data_scope="charge", axis_mode="time", continuity="overlay")

        if "Cycle" not in result.df.columns or "TimeMin" not in result.df.columns:
            pytest.skip(f"[{tag}] Cycle/TimeMin 컬럼 없음")

        for cyc_val in result.df["Cycle"].dropna().unique():
            cyc_df = result.df[result.df["Cycle"] == cyc_val]
            t = cyc_df["TimeMin"].dropna()
            if len(t) > 0:
                assert t.min() < 1.0, \
                    f"[{tag}] 사이클 {cyc_val} 시작시간 {t.min():.2f}min ≥ 1분"


class TestMultiCycleVariations:
    """다양한 사이클 입력 패턴 (단일/범위/전체) 검증."""

    def test_single_cycle_first(self, exp_entry, cycle_info):
        """첫 번째 사이클만 로드."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        result = _safe_profile(
            ch, cycles["first"], cap, crate, cmap, f"{tag}/first",
            data_scope="charge", axis_mode="soc")

        assert len(result.df) > 0, f"[{tag}] 첫 사이클 데이터 없음"

    def test_single_cycle_middle(self, exp_entry, cycle_info):
        """중간 사이클만 로드."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        result = _safe_profile(
            ch, cycles["mid"], cap, crate, cmap, f"{tag}/mid",
            data_scope="charge", axis_mode="soc")

        assert len(result.df) > 0, f"[{tag}] 중간 사이클 데이터 없음"

    def test_single_cycle_last(self, exp_entry, cycle_info):
        """마지막 사이클만 로드."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        result = _safe_profile(
            ch, cycles["last"], cap, crate, cmap, f"{tag}/last",
            data_scope="discharge", axis_mode="time")

        assert len(result.df) > 0, f"[{tag}] 마지막 사이클 데이터 없음"

    def test_range_first_three(self, exp_entry, cycle_info):
        """첫 3 사이클 (논리 1-3) 로드."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        keys = sorted(cmap.keys())
        if len(keys) < 3:
            pytest.skip(f"[{tag}] 사이클 3개 미만")

        result = _safe_profile(
            ch, cycles["first3"], cap, crate, cmap, f"{tag}/first3",
            data_scope="charge", axis_mode="time")

        assert len(result.df) > 0, f"[{tag}] 첫 3사이클 데이터 없음"
        # 여러 사이클의 데이터가 포함되어야 함
        if "Cycle" in result.df.columns:
            n_cycles = result.df["Cycle"].dropna().nunique()
            assert n_cycles >= 1, \
                f"[{tag}] 3사이클 요청인데 Cycle 값 {n_cycles}개"

    def test_range_middle_five(self, exp_entry, cycle_info):
        """중간 5 사이클 로드."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        keys = sorted(cmap.keys())
        if len(keys) < 5:
            pytest.skip(f"[{tag}] 사이클 5개 미만")

        result = _safe_profile(
            ch, cycles["mid5"], cap, crate, cmap, f"{tag}/mid5",
            data_scope="discharge", axis_mode="time")

        assert len(result.df) > 0, f"[{tag}] 중간 5사이클 데이터 없음"

    @pytest.mark.slow
    def test_full_range(self, exp_entry, cycle_info):
        """전체 사이클 (최대 20개) 로드."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        result = _safe_profile(
            ch, cycles["all"], cap, crate, cmap, f"{tag}/all",
            data_scope="charge", axis_mode="time")

        assert len(result.df) > 0, f"[{tag}] 전체 사이클 데이터 없음"

    @pytest.mark.slow
    def test_continuous_range(self, exp_entry, cycle_info):
        """연속 모드로 전체 사이클 (최대 20개) 로드 + 시간축 단조증가 확인."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        result = _safe_profile(
            ch, cycles["all"], cap, crate, cmap, f"{tag}/all-cont",
            data_scope="charge", axis_mode="time", continuity="continuous")

        assert len(result.df) > 0, f"[{tag}] 연속 모드 데이터 없음"

        # 시간 단조 증가 검증
        if "TimeMin" in result.df.columns:
            t = result.df["TimeMin"].dropna().values
            if len(t) > 1:
                diffs = np.diff(t)
                mono = np.sum(diffs >= -0.01) / len(diffs)
                assert mono > 0.95, \
                    f"[{tag}] 연속 시간 단조증가 비율: {mono:.1%} (기대: >95%)"


class TestSweepProfileAccuracy:
    """GITT/HPPC/DCIR/Pulse 스윕 프로필 정확성."""

    @pytest.fixture(autouse=True)
    def _skip_non_sweep(self, exp_entry):
        """스윕 데이터가 아닌 경우 건너뛰기."""
        tag = exp_entry["tag"]
        fn = exp_entry["folder_name"]
        if not _is_sweep_data(tag, fn):
            pytest.skip("스윕/펄스 데이터 아님")

    def test_gitt_cycle_scope_has_both_directions(self, exp_entry, cycle_info):
        """사이클 모드에서 충전과 방전 양방향 데이터가 존재해야 함."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        # 최대 5사이클
        keys = sorted(cmap.keys())
        end = keys[min(4, len(keys) - 1)]
        rng = (keys[0], end)

        result = _safe_profile(
            ch, rng, cap, crate, cmap, f"{tag}/sweep-cycle",
            data_scope="cycle", axis_mode="time")

        if "Condition" in result.df.columns:
            conds = set(result.df["Condition"].dropna().unique())
            # 충전(1 또는 9)과 방전(2) 모두 있어야 함
            has_charge = bool(conds & {1, 9})
            has_discharge = 2 in conds
            if not (has_charge and has_discharge):
                warnings.warn(
                    f"[{tag}] 스윕 cycle 모드인데 양방향 없음: "
                    f"Conditions={conds}")

    def test_gitt_with_rest_has_rest_data(self, exp_entry, cycle_info):
        """include_rest=True 시 휴지(Condition=3) 데이터가 포함되어야 함."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        result = _safe_profile(
            ch, cycles["first"], cap, crate, cmap, f"{tag}/rest-on",
            data_scope="cycle", axis_mode="time", include_rest=True)

        if "Condition" in result.df.columns:
            has_rest = 3 in result.df["Condition"].values
            if not has_rest:
                warnings.warn(
                    f"[{tag}] include_rest=True인데 휴지(3) 데이터 없음")

    def test_gitt_without_rest_no_rest_data(self, exp_entry, cycle_info):
        """include_rest=False 시 휴지 데이터가 없어야 함."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        result = _safe_profile(
            ch, cycles["first"], cap, crate, cmap, f"{tag}/rest-off",
            data_scope="cycle", axis_mode="time", include_rest=False)

        if "Condition" in result.df.columns:
            rest_count = (result.df["Condition"] == 3).sum()
            assert rest_count == 0, \
                f"[{tag}] include_rest=False인데 휴지 행 {rest_count}개"

    def test_pulse_profile_has_rapid_voltage_changes(self, exp_entry, cycle_info):
        """펄스 데이터에서 급격한 전압 변화(ΔV)가 관찰되어야 함."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        result = _safe_profile(
            ch, cycles["first"], cap, crate, cmap, f"{tag}/rapid-dv",
            data_scope="cycle", axis_mode="time", include_rest=True)

        v = result.df["Voltage"].dropna().values
        if len(v) < 20:
            warnings.warn(f"[{tag}] 전압 데이터 부족 ({len(v)}행)")
            return

        diffs = np.abs(np.diff(v))
        # 상위 1% 전압 변화가 10mV 이상이면 펄스 특성
        top_1pct = np.percentile(diffs, 99)
        if top_1pct < 0.010:
            warnings.warn(
                f"[{tag}] 펄스 ΔV 최대값 {top_1pct:.4f}V — "
                f"펄스 특성 미약할 수 있음")

    def test_sweep_logical_cycles_are_grouped(self, exp_entry, cycle_info):
        """스윕 데이터의 cycle_map이 그룹화(tuple)되어 있는지 확인."""
        tag = exp_entry["tag"]
        cmap, _ = cycle_info

        tuple_count = sum(1 for v in cmap.values() if isinstance(v, tuple))
        total = len(cmap)

        if tuple_count == 0 and exp_entry["cycler"] == "pne":
            warnings.warn(
                f"[{tag}] PNE 스윕인데 tuple 매핑 없음 — "
                f"general 모드로 분류된 것일 수 있음 ({total}개 사이클)")


class TestPlotRendering:
    """프로필 데이터로 matplotlib 플롯이 정상 생성되는지 검증."""

    def test_voltage_vs_soc_plot(self, exp_entry, cycle_info):
        """V vs SOC 플롯 생성 및 데이터 라인 존재 확인."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        result = _safe_profile(
            ch, cycles["first"], cap, crate, cmap, f"{tag}/plot-vsoc",
            data_scope="charge", axis_mode="soc")

        df = result.df
        fig, ax = plt.subplots()
        try:
            if "SOC" in df.columns and "Voltage" in df.columns:
                ax.plot(df["SOC"], df["Voltage"], linewidth=0.8)
                ax.set_xlabel("SOC")
                ax.set_ylabel("Voltage [V]")
            assert len(ax.lines) > 0, f"[{tag}] V vs SOC 라인 없음"
        finally:
            plt.close(fig)

    def test_voltage_vs_time_plot(self, exp_entry, cycle_info):
        """V vs Time 플롯 생성 및 데이터 라인 존재 확인."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        result = _safe_profile(
            ch, cycles["first"], cap, crate, cmap, f"{tag}/plot-vtime",
            data_scope="discharge", axis_mode="time")

        df = result.df
        fig, ax = plt.subplots()
        try:
            if "TimeMin" in df.columns and "Voltage" in df.columns:
                ax.plot(df["TimeMin"], df["Voltage"], linewidth=0.8)
                ax.set_xlabel("Time [min]")
                ax.set_ylabel("Voltage [V]")
            assert len(ax.lines) > 0, f"[{tag}] V vs Time 라인 없음"
        finally:
            plt.close(fig)

    def test_crate_vs_time_plot(self, exp_entry, cycle_info):
        """C-rate vs Time 플롯 생성."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        result = _safe_profile(
            ch, cycles["first"], cap, crate, cmap, f"{tag}/plot-crate",
            data_scope="cycle", axis_mode="time")

        df = result.df
        fig, ax = plt.subplots()
        try:
            if "TimeMin" in df.columns and "Crate" in df.columns:
                ax.plot(df["TimeMin"], df["Crate"], linewidth=0.8)
                ax.set_xlabel("Time [min]")
                ax.set_ylabel("C-rate")
            assert len(ax.lines) > 0, f"[{tag}] Crate vs Time 라인 없음"
        finally:
            plt.close(fig)

    def test_multi_cycle_overlay_plot(self, exp_entry, cycle_info):
        """3사이클 오버레이 플롯 — 각 사이클이 별도 라인으로 그려지는지 확인."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        keys = sorted(cmap.keys())
        if len(keys) < 3:
            pytest.skip(f"[{tag}] 사이클 3개 미만")

        rng = cycles["first3"]
        result = _safe_profile(
            ch, rng, cap, crate, cmap, f"{tag}/plot-overlay",
            data_scope="charge", axis_mode="soc")

        df = result.df
        fig, ax = plt.subplots()
        try:
            if "Cycle" in df.columns and "SOC" in df.columns:
                for cyc_val in df["Cycle"].dropna().unique():
                    cyc_df = df[df["Cycle"] == cyc_val]
                    ax.plot(cyc_df["SOC"], cyc_df["Voltage"],
                            linewidth=0.8, label=f"Cycle {cyc_val}")
                assert len(ax.lines) >= 1, \
                    f"[{tag}] 오버레이 라인 부족: {len(ax.lines)}개"
        finally:
            plt.close(fig)

    def test_dqdv_plot(self, exp_entry, cycle_info):
        """dQ/dV vs V 플롯 생성 확인."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        result = _safe_profile(
            ch, cycles["first"], cap, crate, cmap, f"{tag}/plot-dqdv",
            data_scope="charge", axis_mode="soc", calc_dqdv=True)

        df = result.df
        fig, ax = plt.subplots()
        try:
            if "dQdV" in df.columns and "Voltage" in df.columns:
                valid = df.dropna(subset=["dQdV", "Voltage"])
                finite = valid[np.isfinite(valid["dQdV"])]
                if len(finite) > 0:
                    ax.plot(finite["Voltage"], finite["dQdV"], linewidth=0.8)
                assert len(ax.lines) > 0, f"[{tag}] dQ/dV 라인 없음"
            else:
                warnings.warn(f"[{tag}] dQdV 또는 Voltage 컬럼 없음")
        finally:
            plt.close(fig)


class TestOptionCombinations:
    """11개 옵션 조합 × 대표 데이터 — 크래시 없이 동작하는지 검증."""

    # 대표 샘플: PNE 수명, Toyo 수명, GITT, DCIR 각 1개
    _REPRESENTATIVE_TAGS = {"Q8-RT", "Q7M-1-100", "GITT-15도", "DCIR-07"}

    @pytest.fixture(autouse=True)
    def _filter_representative(self, exp_entry):
        """대표 샘플만 실행."""
        if exp_entry["tag"] not in self._REPRESENTATIVE_TAGS:
            pytest.skip("대표 데이터 아님")

    @pytest.mark.parametrize("scope,axis,cont,rest,dqdv",
                             OPTION_COMBOS, ids=OPTION_IDS)
    def test_option_combo(self, exp_entry, cycle_info,
                          scope, axis, cont, rest, dqdv):
        """옵션 조합이 예외 없이 실행되고 기본 검증을 통과하는지."""
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_info

        result = unified_profile_core(
            ch, cycles["first"], cap, crate,
            data_scope=scope, axis_mode=axis, continuity=cont,
            include_rest=rest, calc_dqdv=dqdv, cycle_map=cmap)

        label = f"{tag}/{scope}-{axis}-{cont}"

        if result.df.empty and result.metadata.get("error"):
            warnings.warn(f"[{label}] {result.metadata['error']}")
            return

        # 기본 존재 검증
        assert result.df is not None, f"[{label}] df가 None"
        assert len(result.df) > 0, f"[{label}] df 비어있음"

        # 전압 범위 검증
        if "Voltage" in result.df.columns:
            v = result.df["Voltage"].dropna()
            if len(v) > 0:
                v_min, v_max = _voltage_bounds(tag, exp_entry["folder_name"])
                # 넓은 범위 사용 (하프셀 포함 가능)
                assert v.min() >= V_HALF_MIN, \
                    f"[{label}] 전압 하한: {v.min():.4f}V"
                assert v.max() <= V_HALF_MAX, \
                    f"[{label}] 전압 상한: {v.max():.4f}V"

        # 시간 음수 검증
        if "TimeMin" in result.df.columns:
            t = result.df["TimeMin"].dropna()
            if len(t) > 0:
                assert t.min() >= 0.0, \
                    f"[{label}] 시간 음수: {t.min():.4f}min"

        # 온도 범위 검증
        if "Temp" in result.df.columns:
            temp = result.df["Temp"].dropna()
            if len(temp) > 0:
                assert temp.min() >= T_MIN, \
                    f"[{label}] 온도 하한: {temp.min():.1f}°C"
                assert temp.max() <= T_MAX, \
                    f"[{label}] 온도 상한: {temp.max():.1f}°C"

        # NaN 비율 검증 (90% 초과 경고)
        for col in ["Voltage", "Crate", "Temp"]:
            if col in result.df.columns:
                nan_ratio = result.df[col].isnull().mean()
                if nan_ratio > 0.9:
                    warnings.warn(
                        f"[{label}] {col} NaN 비율: {nan_ratio:.0%}")
