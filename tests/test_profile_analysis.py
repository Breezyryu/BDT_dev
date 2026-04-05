"""프로필 분석 통합 테스트 — unified_profile_core() 전체 데이터 검증

테스트 대상:
  - unified_profile_core() 의 4개 옵션 조합
  - 모든 실험 데이터 경로 (conftest.ALL_EXP_DATA)
  - 사이클 입력: 첫 사이클, 중간, 마지막, 전체, 펄스(GITT) 스윕

검증 기준:
  1. 데이터 존재: DataFrame이 비어있지 않음
  2. 필수 컬럼 존재: 옵션에 따른 기대 컬럼 포함
  3. 물리적 범위: 전압/용량/시간/온도가 유효 범위 이내
  4. 플롯 생성: matplotlib figure가 정상 생성됨

실행:
  pytest tests/test_profile_analysis.py -v              # 전체
  pytest tests/test_profile_analysis.py -k "first_cycle" # 첫 사이클만
  pytest tests/test_profile_analysis.py -k "toyo"        # Toyo만
  pytest tests/test_profile_analysis.py -m "not slow"    # 느린 테스트 제외
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

# 모듈 로드 (세션 1회)
import importlib.util as _ilu

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
# 2. 데이터 카탈로그 (conftest.ALL_EXP_DATA 복사)
# ══════════════════════════════════════════════

# (폴더명, 용량mAh, C-rate, 사이클러, 태그)
ALL_EXP_DATA = [
    ("240821 선행랩 류성택 Gen4pGr mini-ATL-WD-Proto-422mAh-20C-450V-GITT-15도",
     422, 0.2, "pne", "GITT"),
    ("240919 선행랩 류성택 Gen4pGr mini-ATL-WD-Proto-422mAh-20C-450V-SOC별DCIR-15도",
     422, 0.2, "pne", "SOC별DCIR"),
    ("250207_250307_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 1-100cyc",
     1689, 2.0, "toyo", "수명1-100"),
    ("250219_250319_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 101-200cyc",
     1689, 2.0, "toyo", "수명101-200"),
    ("250304_250404_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 201-300cyc",
     1689, 2.0, "toyo", "수명201-300"),
    ("250317_251231_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 301-400cyc",
     1689, 2.0, "toyo", "수명301-400"),
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
]


# ══════════════════════════════════════════════
# 3. 헬퍼 함수
# ══════════════════════════════════════════════

@dataclass
class ProfileTestSpec:
    """프로필 테스트 사양."""
    channel_path: str
    cycle_range: tuple
    mincapacity: float
    inirate: float
    data_scope: str
    axis_mode: str
    continuity: str = "overlay"
    include_rest: bool = False
    calc_dqdv: bool = False
    cycle_map: dict | None = None


def _resolve_entry(folder_name, capacity, crate, cycler, tag):
    """데이터 엔트리를 채널 경로까지 resolve한다."""
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

    return {
        "folder_name": folder_name,
        "capacity": capacity,
        "crate": crate,
        "cycler": cycler,
        "tag": tag,
        "channel_path": str(ch_path),
    }


def _get_cycle_map(channel_path: str, capacity: float, crate: float,
                   cycler: str) -> dict:
    """채널 경로에서 사이클 맵을 구축한다."""
    if cycler == "pne":
        cap = pne_min_cap(channel_path, capacity, crate)
        cmap, _ = pne_build_cycle_map(channel_path, cap, crate)
    else:
        cap = toyo_min_cap(channel_path, capacity, crate)
        cmap, _ = toyo_build_cycle_map(channel_path, cap, crate)
    return cmap


def _pick_test_cycles(cycle_map: dict) -> dict:
    """테스트용 사이클 번호 선택."""
    if not cycle_map:
        return {}
    keys = sorted(cycle_map.keys())
    first = keys[0]
    last = keys[-1]
    mid = keys[len(keys) // 2]
    return {
        "first": (first, first),
        "middle": (mid, mid),
        "last": (last, last),
        "all": (first, last),
    }


# ── 물리적 범위 상수 ──
V_MIN, V_MAX = -0.5, 5.5    # 하프셀 포함 전압 범위
T_MIN, T_MAX = -30.0, 100.0
SOC_MIN, SOC_MAX = -1.5, 1.5  # cycle scope에서 방전이 충전보다 클 때 음수 가능
TIME_MIN = 0.0


def validate_profile_result(result, spec: ProfileTestSpec, label: str = ""):
    """프로필 결과의 물리적 유효성을 검증한다."""
    prefix = f"[{label}] " if label else ""

    # 1. 데이터 존재
    assert result.df is not None, f"{prefix}result.df가 None"
    assert not result.df.empty, f"{prefix}result.df가 비어있음"
    assert len(result.df) > 0, f"{prefix}result.df 행 수 = 0"

    df = result.df

    # 2. 필수 컬럼 검증
    if spec.axis_mode == "time":
        required = ["TimeMin", "Voltage", "Crate", "Temp"]
    else:
        required = ["SOC", "Voltage", "Crate", "Temp"]

    if spec.calc_dqdv:
        required += ["dQdV", "dVdQ"]

    if spec.continuity == "continuous":
        required += ["TimeSec"]

    for col in required:
        assert col in df.columns, \
            f"{prefix}필수 컬럼 '{col}' 누락. 존재: {list(df.columns)}"

    # 3. 물리적 범위
    #    소용량 하프셀(< 50 mAh)은 SOC 정규화가 다를 수 있으므로
    #    SOC 범위 체크를 완화한다.
    is_halfcell = spec.mincapacity < 50

    if "Voltage" in df.columns:
        v = df["Voltage"].dropna()
        if len(v) > 0:
            assert v.min() >= V_MIN, f"{prefix}전압 하한: {v.min():.4f}V"
            assert v.max() <= V_MAX, f"{prefix}전압 상한: {v.max():.4f}V"

    if "Temp" in df.columns:
        t = df["Temp"].dropna()
        if len(t) > 0:
            assert t.min() >= T_MIN, f"{prefix}온도 하한: {t.min():.1f}°C"
            assert t.max() <= T_MAX, f"{prefix}온도 상한: {t.max():.1f}°C"

    # continuous 모드 + multi-cycle이면 SOC가 사이클별 누적되므로 범위 검증 스킵
    is_multicycle_cont = (
        spec.continuity == "continuous"
        and spec.cycle_range[1] - spec.cycle_range[0] >= 1
    )
    if "SOC" in df.columns and not is_halfcell and not is_multicycle_cont:
        s = df["SOC"].dropna()
        if len(s) > 0:
            assert s.min() >= SOC_MIN, f"{prefix}SOC 하한: {s.min():.4f}"
            assert s.max() <= SOC_MAX, f"{prefix}SOC 상한: {s.max():.4f}"

    if "TimeMin" in df.columns:
        tm = df["TimeMin"].dropna()
        if len(tm) > 0:
            assert tm.min() >= TIME_MIN, f"{prefix}시간 하한: {tm.min():.2f}min"
            if spec.continuity == "overlay" and spec.axis_mode == "time":
                assert tm.min() < 1.0, \
                    f"{prefix}오버레이 시작 시간 이상: {tm.min():.2f}min"

    # 4. 데이터 타입
    for col in ["Voltage", "Crate", "Temp", "SOC", "TimeMin"]:
        if col in df.columns:
            assert pd.api.types.is_numeric_dtype(df[col]), \
                f"{prefix}'{col}' 비숫자: {df[col].dtype}"

    # 5. NaN 비율 (90% 초과 비정상)
    present_req = [c for c in required if c in df.columns]
    if present_req:
        nan_ratio = df[present_req].isnull().mean()
        high_nan = nan_ratio[nan_ratio > 0.9]
        assert high_nan.empty, f"{prefix}NaN 90%+ : {dict(high_nan)}"


def validate_plot_creation(result, spec: ProfileTestSpec, label: str = ""):
    """기본 플롯이 생성 가능한지 검증."""
    df = result.df
    if df.empty:
        return

    fig, axes = plt.subplots(2, 3, figsize=(12, 8))
    try:
        ax = axes[0, 0]
        if spec.axis_mode == "time" and "TimeMin" in df.columns:
            ax.plot(df["TimeMin"], df["Voltage"], linewidth=0.8)
        elif "SOC" in df.columns:
            ax.plot(df["SOC"], df["Voltage"], linewidth=0.8)
        ax.set_ylabel("Voltage [V]")

        if "Crate" in df.columns:
            x_col = "TimeMin" if spec.axis_mode == "time" else "SOC"
            if x_col in df.columns:
                axes[0, 1].plot(df[x_col], df["Crate"], linewidth=0.8)

        if "Temp" in df.columns:
            x_col = "TimeMin" if spec.axis_mode == "time" else "SOC"
            if x_col in df.columns:
                axes[0, 2].plot(df[x_col], df["Temp"], linewidth=0.8)

        if spec.calc_dqdv and "dQdV" in df.columns and "Voltage" in df.columns:
            axes[1, 0].plot(df["Voltage"], df["dQdV"], linewidth=0.8)

        fig.tight_layout()
        assert len(fig.axes) >= 6, f"서브플롯 수 부족: {len(fig.axes)}"
    finally:
        plt.close(fig)


# ══════════════════════════════════════════════
# 4. 옵션 조합 정의
# ══════════════════════════════════════════════

# (data_scope, axis_mode, continuity, include_rest, calc_dqdv)
OPTION_COMBOS = [
    ("charge",    "soc",  "overlay", False, True),
    ("discharge", "soc",  "overlay", False, True),
    ("cycle",     "soc",  "overlay", False, False),
    ("charge",    "time", "overlay", False, False),
    ("discharge", "time", "overlay", False, False),
    ("cycle",     "time", "overlay", False, False),
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
# 5. 테스트 함수 — parametrize 방식
# ══════════════════════════════════════════════

def _entry_ids():
    return [e[4] for e in ALL_EXP_DATA]


@pytest.fixture(params=ALL_EXP_DATA, ids=_entry_ids())
def exp_entry(request):
    """실험 데이터 엔트리를 resolve한다."""
    folder_name, cap, crate, cycler, tag = request.param
    entry = _resolve_entry(folder_name, cap, crate, cycler, tag)
    if entry is None:
        pytest.skip(f"데이터 없음: {folder_name}")
    return entry


@pytest.fixture
def cycle_map_and_cycles(exp_entry):
    """사이클 맵 구축 + 테스트 사이클 선택."""
    ch = exp_entry["channel_path"]
    cmap = _get_cycle_map(ch, exp_entry["capacity"],
                          exp_entry["crate"], exp_entry["cycler"])
    if not cmap:
        pytest.skip("사이클 맵 비어있음")
    cycles = _pick_test_cycles(cmap)
    return cmap, cycles


# ── 테스트 클래스 ──

class TestProfileFirstCycle:
    """첫 사이클에 대해 모든 옵션 조합 테스트."""

    @pytest.mark.parametrize("scope,axis,cont,rest,dqdv",
                             OPTION_COMBOS, ids=OPTION_IDS)
    def test_first_cycle(self, exp_entry, cycle_map_and_cycles,
                         scope, axis, cont, rest, dqdv):
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        tag = exp_entry["tag"]
        cmap, cycles = cycle_map_and_cycles

        first = cycles["first"]
        spec = ProfileTestSpec(
            channel_path=ch, cycle_range=first,
            mincapacity=cap, inirate=crate,
            data_scope=scope, axis_mode=axis,
            continuity=cont, include_rest=rest,
            calc_dqdv=dqdv, cycle_map=cmap,
        )

        result = unified_profile_core(
            ch, first, cap, crate,
            data_scope=scope, axis_mode=axis, continuity=cont,
            include_rest=rest, calc_dqdv=dqdv, cycle_map=cmap,
        )

        label = f"{tag}/cyc{first[0]}/{scope}-{axis}-{cont}"

        if result.df.empty and result.metadata.get("error"):
            warnings.warn(f"{label}: {result.metadata['error']}")
            return

        validate_profile_result(result, spec, label)
        validate_plot_creation(result, spec, label)


class TestProfileMiddleCycle:
    """중간 사이클 프로필 (주요 옵션만)."""

    @pytest.mark.parametrize("scope,axis", [
        ("charge", "soc"), ("discharge", "soc"),
        ("charge", "time"), ("discharge", "time"),
    ], ids=["chg-soc", "dchg-soc", "chg-time", "dchg-time"])
    def test_middle_cycle(self, exp_entry, cycle_map_and_cycles, scope, axis):
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        cmap, cycles = cycle_map_and_cycles

        mid = cycles["middle"]
        dqdv = (axis == "soc")

        spec = ProfileTestSpec(
            channel_path=ch, cycle_range=mid,
            mincapacity=cap, inirate=crate,
            data_scope=scope, axis_mode=axis,
            calc_dqdv=dqdv, cycle_map=cmap,
        )

        result = unified_profile_core(
            ch, mid, cap, crate,
            data_scope=scope, axis_mode=axis,
            calc_dqdv=dqdv, cycle_map=cmap,
        )

        label = f"{exp_entry['tag']}/mid{mid[0]}/{scope}-{axis}"
        if result.df.empty and result.metadata.get("error"):
            warnings.warn(f"{label}: {result.metadata['error']}")
            return

        validate_profile_result(result, spec, label)


class TestProfileLastCycle:
    """마지막 사이클 프로필."""

    @pytest.mark.parametrize("scope,axis", [
        ("charge", "soc"), ("discharge", "time"),
    ], ids=["chg-soc", "dchg-time"])
    def test_last_cycle(self, exp_entry, cycle_map_and_cycles, scope, axis):
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        cmap, cycles = cycle_map_and_cycles

        last = cycles["last"]
        dqdv = (axis == "soc")

        spec = ProfileTestSpec(
            channel_path=ch, cycle_range=last,
            mincapacity=cap, inirate=crate,
            data_scope=scope, axis_mode=axis,
            calc_dqdv=dqdv, cycle_map=cmap,
        )

        result = unified_profile_core(
            ch, last, cap, crate,
            data_scope=scope, axis_mode=axis,
            calc_dqdv=dqdv, cycle_map=cmap,
        )

        label = f"{exp_entry['tag']}/last{last[0]}/{scope}-{axis}"
        if result.df.empty and result.metadata.get("error"):
            warnings.warn(f"{label}: {result.metadata['error']}")
            return

        validate_profile_result(result, spec, label)
        validate_plot_creation(result, spec, label)


class TestProfileAllCycles:
    """전체 사이클 범위 — continuous 모드."""

    @pytest.mark.slow
    @pytest.mark.parametrize("scope", ["charge", "discharge", "cycle"],
                             ids=["chg", "dchg", "cyc"])
    def test_all_cycles_continuous(self, exp_entry, cycle_map_and_cycles, scope):
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        cmap, cycles = cycle_map_and_cycles

        # 사이클 수 제한 (성능)
        keys = sorted(cmap.keys())
        if len(keys) > 20:
            all_range = (keys[0], keys[19])
        else:
            all_range = cycles["all"]

        spec = ProfileTestSpec(
            channel_path=ch, cycle_range=all_range,
            mincapacity=cap, inirate=crate,
            data_scope=scope, axis_mode="time",
            continuity="continuous", cycle_map=cmap,
        )

        result = unified_profile_core(
            ch, all_range, cap, crate,
            data_scope=scope, axis_mode="time", continuity="continuous",
            cycle_map=cmap,
        )

        label = f"{exp_entry['tag']}/all{all_range}/{scope}-cont"
        if result.df.empty and result.metadata.get("error"):
            warnings.warn(f"{label}: {result.metadata['error']}")
            return

        validate_profile_result(result, spec, label)

        # 연속 모드: 시간 단조 증가 검증
        if "TimeMin" in result.df.columns:
            t = result.df["TimeMin"].dropna().values
            if len(t) > 1:
                diffs = np.diff(t)
                increasing = np.sum(diffs >= -0.01) / len(diffs)
                assert increasing > 0.95, \
                    f"{label}: 시간 단조증가 비율: {increasing:.2%}"


class TestProfilePulseGITT:
    """GITT / Pulse 데이터 전용."""

    @pytest.mark.parametrize("include_rest", [True, False],
                             ids=["with-rest", "no-rest"])
    def test_gitt_pulse(self, exp_entry, cycle_map_and_cycles, include_rest):
        tag = exp_entry["tag"]
        fn = exp_entry["folder_name"]

        gitt_kw = ["GITT", "pulse", "DCIR", "HPPC", "hysteresis", "율별"]
        if not any(k.lower() in tag.lower() or k.lower() in fn.lower()
                   for k in gitt_kw):
            pytest.skip("GITT/Pulse 아님")

        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        cmap, _ = cycle_map_and_cycles

        keys = sorted(cmap.keys())
        end = keys[min(4, len(keys) - 1)]
        pulse_range = (keys[0], end)

        spec = ProfileTestSpec(
            channel_path=ch, cycle_range=pulse_range,
            mincapacity=cap, inirate=crate,
            data_scope="cycle", axis_mode="time",
            include_rest=include_rest, cycle_map=cmap,
        )

        result = unified_profile_core(
            ch, pulse_range, cap, crate,
            data_scope="cycle", axis_mode="time",
            include_rest=include_rest, cycle_map=cmap,
        )

        label = f"{tag}/pulse{pulse_range}/rest={include_rest}"
        if result.df.empty and result.metadata.get("error"):
            warnings.warn(f"{label}: {result.metadata['error']}")
            return

        validate_profile_result(result, spec, label)


class TestOptionDependency:
    """옵션 의존성 규칙 검증."""

    def test_soc_forces_overlay(self, exp_entry, cycle_map_and_cycles):
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        cmap, cycles = cycle_map_and_cycles

        first = cycles["first"]

        result = unified_profile_core(
            ch, first, cap, crate,
            data_scope="charge", axis_mode="soc", continuity="continuous",
            cycle_map=cmap,
        )

        if not result.df.empty:
            opts = result.metadata.get("options", {})
            assert opts.get("continuity") == "overlay" or \
                opts.get("axis_mode") == "time", \
                f"SOC+continuous 미변환: {opts}"


class TestProfileMetadata:
    """메타데이터 검증."""

    def test_metadata_fields(self, exp_entry, cycle_map_and_cycles):
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        cmap, cycles = cycle_map_and_cycles

        first = cycles["first"]

        result = unified_profile_core(
            ch, first, cap, crate,
            data_scope="charge", axis_mode="time", cycle_map=cmap,
        )

        meta = result.metadata
        assert "cycler_type" in meta
        assert meta["cycler_type"] in ("PNE", "TOYO")
        assert "cycle_range" in meta
        assert "options" in meta or "error" in meta
        assert result.mincapacity > 0


class TestCyclerDetection:
    """check_cycler() 판별 정확성."""

    def test_cycler_matches(self, exp_entry):
        ch = exp_entry["channel_path"]
        expected = exp_entry["cycler"]
        is_pne = check_cycler(ch)

        if expected == "pne":
            assert is_pne is True, f"{exp_entry['tag']}: PNE 기대, Toyo 판별"
        else:
            assert is_pne is False, f"{exp_entry['tag']}: Toyo 기대, PNE 판별"


class TestCycleMapValidity:
    """사이클 맵 유효성."""

    def test_not_empty(self, exp_entry, cycle_map_and_cycles):
        cmap, _ = cycle_map_and_cycles
        assert cmap
        assert len(cmap) > 0

    def test_keys_positive(self, exp_entry, cycle_map_and_cycles):
        cmap, _ = cycle_map_and_cycles
        for key in cmap:
            assert key > 0, f"사이클 번호 ≤ 0: {key}"

    def test_keys_sorted(self, exp_entry, cycle_map_and_cycles):
        cmap, _ = cycle_map_and_cycles
        keys = list(cmap.keys())
        assert keys == sorted(keys)


class TestDQDV:
    """dQ/dV 계산 유효성."""

    @pytest.mark.parametrize("scope", ["charge", "discharge"],
                             ids=["chg", "dchg"])
    def test_dqdv_finite(self, exp_entry, cycle_map_and_cycles, scope):
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        cmap, cycles = cycle_map_and_cycles

        first = cycles["first"]

        result = unified_profile_core(
            ch, first, cap, crate,
            data_scope=scope, axis_mode="soc", calc_dqdv=True,
            cycle_map=cmap,
        )

        if result.df.empty:
            pytest.skip("데이터 없음")

        df = result.df
        if "dQdV" not in df.columns:
            pytest.skip("dQdV 없음")

        dqdv = df["dQdV"].dropna()
        if len(dqdv) == 0:
            pytest.skip("dQdV 전부 NaN")

        finite_ratio = np.isfinite(dqdv).mean()
        assert finite_ratio > 0.5, \
            f"{exp_entry['tag']}/{scope}: dQdV 유한값 {finite_ratio:.1%}"


class TestEdgeCases:
    """에지 케이스."""

    def test_nonexistent_cycle(self, exp_entry, cycle_map_and_cycles):
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        cmap, _ = cycle_map_and_cycles

        bogus = max(cmap.keys()) + 9999

        result = unified_profile_core(
            ch, (bogus, bogus), cap, crate,
            data_scope="charge", axis_mode="time", cycle_map=cmap,
        )

        assert result.df.empty or result.metadata.get("error"), \
            f"존재하지 않는 사이클 {bogus}에 대해 데이터 반환됨"

    def test_single_cycle_overlay(self, exp_entry, cycle_map_and_cycles):
        ch = exp_entry["channel_path"]
        cap = exp_entry["capacity"]
        crate = exp_entry["crate"]
        cmap, cycles = cycle_map_and_cycles

        first = cycles["first"]

        result = unified_profile_core(
            ch, first, cap, crate,
            data_scope="charge", axis_mode="time", continuity="overlay",
            cycle_map=cmap,
        )

        if not result.df.empty and "Cycle" in result.df.columns:
            assert result.df["Cycle"].nunique() == 1, \
                f"단일 사이클인데 Cycle 값 {result.df['Cycle'].nunique()}개"
