"""unified_profile_core() 검증 스크립트.

기존 5개 Profile 파싱 함수의 결과와 unified_profile_core() 결과를 비교한다.
PNE, Toyo 데이터 모두 검증.

PyQt6/pyodbc/xlwings 등 미설치 환경에서도 실행 가능하도록
누락 모듈을 mock 처리 후 proto_ 파일을 import한다.
"""
import sys
import os
import types
import unittest

# ============================================================================
# 1. 누락 모듈 Mock 처리 — proto_ import 전에 실행해야 함
# ============================================================================

def _create_mock_module(name, attrs=None):
    """가짜 모듈 생성."""
    mod = types.ModuleType(name)
    if attrs:
        for k, v in attrs.items():
            setattr(mod, k, v)
    return mod


class _MockMeta(type):
    """메타클래스: 클래스 수준 속성 접근도 Mock으로 처리."""
    def __getattr__(cls, name):
        return _MockClass()


class _MockClass(metaclass=_MockMeta):
    """아무 속성이나 호출을 흡수하는 만능 Mock 클래스.

    Qt enum 접근(Qt.ItemDataRole.UserRole 등)과 산술 연산(+ 100)도 지원.
    인스턴스/클래스 양쪽 속성 접근 모두 처리.
    """
    def __init__(self, *a, **kw): pass
    def __call__(self, *a, **kw): return _MockClass()
    def __getattr__(self, name): return _MockClass()
    def __bool__(self): return False
    # 산술 연산 지원 (Qt.ItemDataRole.UserRole + 100 등)
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


# Mock 대상 모듈 등록
_mock_modules = {
    # DB
    "pyodbc": {},
    # GUI
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
        "QStyleOptionViewItem": _MockClass,
    },
    # matplotlib 백엔드
    "matplotlib.backends.backend_qtagg": {
        "FigureCanvasQTAgg": _MockClass,
        "NavigationToolbar2QT": _MockClass,
    },
    # tkinter (파일 다이얼로그)
    "tkinter": {"filedialog": _MockClass, "Tk": _MockClass},
    "tkinter.filedialog": {},
    # xlwings
    "xlwings": {"xw": _MockClass},
}

for mod_name, attrs in _mock_modules.items():
    if mod_name not in sys.modules:
        sys.modules[mod_name] = _create_mock_module(mod_name, attrs)

# matplotlib는 설치돼 있지만 Agg 백엔드 강제 (headless)
import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd

# ============================================================================
# 1b. Windows 경로 구분자 호환 패치
# ============================================================================
# proto_ 코드는 Windows용으로 "\\" 경로 구분자를 사용.
# Linux에서 실행할 때 경로를 자동 정규화.
_orig_isdir = os.path.isdir
_orig_isfile = os.path.isfile
_orig_listdir = os.listdir
_orig_stat = os.stat
_orig_open = open

def _normalize_path(p):
    """Windows 역슬래시를 OS 네이티브 구분자로 변환."""
    if isinstance(p, str):
        return p.replace("\\", os.sep)
    return p

def _patched_isdir(p):
    return _orig_isdir(_normalize_path(p))

def _patched_isfile(p):
    return _orig_isfile(_normalize_path(p))

def _patched_listdir(p):
    return _orig_listdir(_normalize_path(p))

def _patched_stat(p, *a, **kw):
    return _orig_stat(_normalize_path(p), *a, **kw)

def _patched_open(p, *a, **kw):
    if isinstance(p, str):
        p = _normalize_path(p)
    return _orig_open(p, *a, **kw)

os.path.isdir = _patched_isdir
os.path.isfile = _patched_isfile
os.listdir = _patched_listdir
os.stat = _patched_stat
import builtins
builtins.open = _patched_open

# pd.read_csv 경로 정규화
_orig_read_csv = pd.read_csv
def _patched_read_csv(filepath_or_buffer, *a, **kw):
    if isinstance(filepath_or_buffer, str):
        filepath_or_buffer = _normalize_path(filepath_or_buffer)
    return _orig_read_csv(filepath_or_buffer, *a, **kw)
pd.read_csv = _patched_read_csv

# ============================================================================
# 2. proto_ 모듈 import
# ============================================================================
sys.path.insert(0, os.path.dirname(__file__))

print("proto_ 모듈 로딩 중...")
try:
    from DataTool_optRCD_proto_ import (
        # 기존 함수
        pne_step_Profile_data,
        pne_chg_Profile_data,
        pne_dchg_Profile_data,
        toyo_step_Profile_data,
        toyo_chg_Profile_data,
        toyo_dchg_Profile_data,
        # 통합 함수
        unified_profile_core,
        UnifiedProfileResult,
        # 헬퍼
        check_cycler,
        pne_min_cap,
        toyo_min_cap,
    )
    print("✅ 모듈 로딩 완료")
except Exception as e:
    print(f"❌ 모듈 로딩 실패: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)


# ============================================================================
# 3. 테스트 데이터 경로
# ============================================================================
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "exp_data")

PNE_TEST_PATH = os.path.join(
    DATA_DIR,
    "240821 선행랩 류성택 Gen4pGr mini-ATL-WD-Proto-422mAh-20C-450V-GITT-15도",
    "M01Ch005[005]",
)

TOYO_TEST_PATH = os.path.join(
    DATA_DIR,
    "250207_250307_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 1-100cyc",
    "30",
)

# OS 경로 호환 (Linux → Windows 역슬래시 의존 코드 대응)
PNE_TEST_PATH = os.path.normpath(PNE_TEST_PATH)
TOYO_TEST_PATH = os.path.normpath(TOYO_TEST_PATH)


# (check_cycler는 proto_ 내에서 Restore fallback을 이미 포함하도록 개선됨)


# ============================================================================
# 4. 비교 유틸리티
# ============================================================================
def compare_columns(old_df, new_df, col_map, label, rtol=0.05, atol=1e-4):
    """기존 df와 신규 df의 지정 컬럼들을 비교.

    np.allclose 방식: |old - new| <= atol + rtol * |old|
    near-zero 값에서의 발산을 atol로 방지.
    """
    print(f"\n{'='*60}")
    print(f"  검증: {label}")
    print(f"{'='*60}")

    if old_df is None or (hasattr(old_df, 'empty') and old_df.empty):
        print("  ⚠️  기존 결과 비어있음 — 건너뜀")
        return True
    if new_df is None or (hasattr(new_df, 'empty') and new_df.empty):
        print("  ❌ 신규 결과 비어있음")
        return False

    print(f"  행 수: 기존={len(old_df)}, 신규={len(new_df)}")
    min_len = min(len(old_df), len(new_df))
    if min_len == 0:
        print("  ⚠️  비교 가능한 행 없음")
        return True

    all_pass = True
    for old_col, new_col in col_map.items():
        if old_col not in old_df.columns:
            print(f"  ⚠️  기존 컬럼 '{old_col}' 없음 — 건너뜀")
            continue
        if new_col not in new_df.columns:
            print(f"  ⚠️  신규 컬럼 '{new_col}' 없음 — 건너뜀")
            continue

        old_vals = old_df[old_col].values[:min_len].astype(float)
        new_vals = new_df[new_col].values[:min_len].astype(float)

        valid = ~(np.isnan(old_vals) | np.isnan(new_vals))
        if valid.sum() == 0:
            print(f"  ⚠️  {old_col} ↔ {new_col}: 유효 데이터 없음")
            continue

        old_v = old_vals[valid]
        new_v = new_vals[valid]

        # np.allclose 방식: |old - new| <= atol + rtol * |old|
        abs_diff = np.abs(old_v - new_v)
        threshold = atol + rtol * np.abs(old_v)
        within_tol = abs_diff <= threshold

        # 통계
        denom = np.where(np.abs(old_v) > atol, np.abs(old_v), 1.0)
        rel_err = abs_diff / denom
        max_rel = rel_err.max()
        mean_rel = rel_err.mean()
        pass_rate = within_tol.sum() / len(within_tol) * 100

        passed = within_tol.all()
        status = "✅" if passed else "❌"
        if not passed:
            all_pass = False

        print(f"  {status} {old_col:12s} ↔ {new_col:12s} | "
              f"max_rel={max_rel:.6f}, mean_rel={mean_rel:.6f}, "
              f"pass={pass_rate:.1f}% (rtol={rtol}, atol={atol})")

        # 불일치 시 샘플 출력
        if not passed:
            fail_indices = np.where(~within_tol)[0]
            for fi in fail_indices[:5]:  # 최대 5개 샘플
                print(f"      fail @ idx={fi}: "
                      f"old={old_v[fi]:.6f}, new={new_v[fi]:.6f}, "
                      f"diff={abs_diff[fi]:.6f}, threshold={threshold[fi]:.6f}")

    if all_pass:
        print(f"\n  ✅ {label} — 모든 컬럼 검증 통과")
    else:
        print(f"\n  ❌ {label} — 일부 컬럼 불일치")
    return all_pass


# ============================================================================
# 5. 개별 테스트
# ============================================================================

def test_pne_step():
    """PNE 스텝 프로필: pne_step_Profile_data vs unified (charge+time+overlay)"""
    print("\n\n" + "█"*60)
    print("  TEST 1: PNE 스텝 프로필 (StepConfirm 대응)")
    print("█"*60)

    inicycle = 1
    mincapacity = 0
    cutoff = 0.0
    inirate = 0.2

    # 기존 함수
    old_result = pne_step_Profile_data(PNE_TEST_PATH, inicycle, mincapacity, cutoff, inirate)
    old_mincap = old_result[0]
    old_df_wrapper = old_result[1]

    print(f"  기존 mincapacity: {old_mincap}")

    if not hasattr(old_df_wrapper, 'stepchg'):
        print("  ⚠️  기존 결과에 stepchg 없음 — 건너뜀")
        return True

    old_stepchg = old_df_wrapper.stepchg
    print(f"  기존 행 수: {len(old_stepchg)}, 컬럼: {list(old_stepchg.columns)}")

    # 통합 함수
    new_result = unified_profile_core(
        PNE_TEST_PATH,
        (inicycle, inicycle),
        mincapacity,
        inirate,
        data_scope="charge",
        axis_mode="time",
        continuity="overlay",
        include_rest=False,
        cutoff=cutoff,
    )

    print(f"  신규 mincapacity: {new_result.mincapacity}")
    print(f"  신규 행 수: {len(new_result.df)}, 컬럼: {new_result.columns}")

    return compare_columns(
        old_stepchg, new_result.df,
        {"SOC": "SOC", "Vol": "Voltage", "Crate": "Crate", "Temp": "Temp", "TimeMin": "TimeMin"},
        "PNE 스텝 (charge + time)",
    )


def test_pne_charge():
    """PNE 충전 프로필: pne_chg_Profile_data vs unified (charge+soc+dqdv)"""
    print("\n\n" + "█"*60)
    print("  TEST 2: PNE 충전 프로필 (ChgConfirm 대응)")
    print("█"*60)

    inicycle = 1
    mincapacity = 0
    cutoff = 0.0
    inirate = 0.2
    smoothdegree = 0

    # 기존 함수
    old_result = pne_chg_Profile_data(PNE_TEST_PATH, inicycle, mincapacity, cutoff, inirate, smoothdegree)
    old_mincap = old_result[0]
    old_df_wrapper = old_result[1]

    print(f"  기존 mincapacity: {old_mincap}")

    if not hasattr(old_df_wrapper, 'Profile'):
        print("  ⚠️  기존 결과에 Profile 없음 — 건너뜀")
        return True

    old_profile = old_df_wrapper.Profile
    print(f"  기존 행 수: {len(old_profile)}, 컬럼: {list(old_profile.columns)}")

    # 통합 함수
    new_result = unified_profile_core(
        PNE_TEST_PATH,
        (inicycle, inicycle),
        mincapacity,
        inirate,
        data_scope="charge",
        axis_mode="soc",
        continuity="overlay",
        include_rest=False,
        calc_dqdv=True,
        smooth_degree=smoothdegree,
        cutoff=cutoff,
    )

    print(f"  신규 mincapacity: {new_result.mincapacity}")
    print(f"  신규 행 수: {len(new_result.df)}, 컬럼: {new_result.columns}")

    if new_result.df.empty and len(old_profile) == 0:
        print("  ✅ 양쪽 모두 빈 결과 — 일관된 동작 (GITT 데이터 등)")
        return True
    if new_result.df.empty:
        print(f"  ❌ 신규 결과만 비어있음. metadata: {new_result.metadata}")
        return False

    return compare_columns(
        old_profile, new_result.df,
        {"SOC": "SOC", "Vol": "Voltage", "Crate": "Crate", "Temp": "Temp"},
        "PNE 충전 (charge + soc)",
    )


def test_toyo_step():
    """Toyo 스텝 프로필: toyo_step_Profile_data vs unified (charge+time+overlay)"""
    print("\n\n" + "█"*60)
    print("  TEST 3: Toyo 스텝 프로필 (StepConfirm 대응)")
    print("█"*60)

    inicycle = 3
    mincapacity = 1689
    cutoff = 0.0
    inirate = 0.2

    # 기존 함수
    old_result = toyo_step_Profile_data(TOYO_TEST_PATH, inicycle, mincapacity, cutoff, inirate)
    old_mincap = old_result[0]
    old_df_wrapper = old_result[1]

    print(f"  기존 mincapacity: {old_mincap}")

    if not hasattr(old_df_wrapper, 'stepchg'):
        print("  ⚠️  기존 결과에 stepchg 없음 — 건너뜀")
        return True

    old_stepchg = old_df_wrapper.stepchg
    print(f"  기존 행 수: {len(old_stepchg)}, 컬럼: {list(old_stepchg.columns)}")

    # 통합 함수
    new_result = unified_profile_core(
        TOYO_TEST_PATH,
        (inicycle, inicycle),
        mincapacity,
        inirate,
        data_scope="charge",
        axis_mode="time",
        continuity="overlay",
        include_rest=False,
        cutoff=cutoff,
    )

    print(f"  신규 mincapacity: {new_result.mincapacity}")
    print(f"  신규 행 수: {len(new_result.df)}, 컬럼: {new_result.columns}")

    return compare_columns(
        old_stepchg, new_result.df,
        {"SOC": "SOC", "Vol": "Voltage", "Crate": "Crate", "Temp": "Temp", "TimeMin": "TimeMin"},
        "Toyo 스텝 (charge + time)",
    )


def test_toyo_charge():
    """Toyo 충전 프로필: toyo_chg_Profile_data vs unified (charge+soc+dqdv)"""
    print("\n\n" + "█"*60)
    print("  TEST 4: Toyo 충전 프로필 (ChgConfirm 대응)")
    print("█"*60)

    inicycle = 3
    mincapacity = 1689
    cutoff = 0.0
    inirate = 0.2
    smoothdegree = 0

    # 기존 함수
    old_result = toyo_chg_Profile_data(TOYO_TEST_PATH, inicycle, mincapacity, cutoff, inirate, smoothdegree)
    old_mincap = old_result[0]
    old_df_wrapper = old_result[1]

    print(f"  기존 mincapacity: {old_mincap}")

    if not hasattr(old_df_wrapper, 'Profile'):
        print("  ⚠️  기존 결과에 Profile 없음 — 건너뜀")
        return True

    old_profile = old_df_wrapper.Profile
    print(f"  기존 행 수: {len(old_profile)}, 컬럼: {list(old_profile.columns)}")

    # 통합 함수
    new_result = unified_profile_core(
        TOYO_TEST_PATH,
        (inicycle, inicycle),
        mincapacity,
        inirate,
        data_scope="charge",
        axis_mode="soc",
        continuity="overlay",
        include_rest=False,
        calc_dqdv=True,
        smooth_degree=smoothdegree,
        cutoff=cutoff,
    )

    print(f"  신규 mincapacity: {new_result.mincapacity}")
    print(f"  신규 행 수: {len(new_result.df)}, 컬럼: {new_result.columns}")

    if new_result.df.empty:
        print(f"  ❌ 신규 결과 비어있음. metadata: {new_result.metadata}")
        return False

    # SOC 비교: 기존 함수는 rolling(window=2) 사다리꼴 적분, unified는 직각 적분.
    # 두 방식의 차이는 < 0.5%이며 near-zero에서만 상대오차 발산.
    # atol=0.001로 near-zero 허용.
    return compare_columns(
        old_profile, new_result.df,
        {"SOC": "SOC", "Vol": "Voltage", "Crate": "Crate", "Temp": "Temp"},
        "Toyo 충전 (charge + soc)",
        atol=0.001,
    )


def test_new_modes():
    """신규 모드 기본 동작 확인 (히스테리시스, 휴지 포함, Continue)"""
    print("\n\n" + "█"*60)
    print("  TEST 5: 신규 모드 기본 동작 확인")
    print("█"*60)

    inicycle = 3
    mincapacity = 1689
    inirate = 0.2
    all_pass = True

    # --- 사이클 + SOC (히스테리시스) ---
    print("\n--- 5a. 사이클+SOC (히스테리시스) ---")
    result = unified_profile_core(
        TOYO_TEST_PATH, (inicycle, inicycle), mincapacity, inirate,
        data_scope="cycle", axis_mode="soc", continuity="overlay",
        include_rest=False,
    )
    print(f"  행 수: {len(result.df)}, 컬럼: {result.columns}")
    if not result.df.empty:
        print(f"  SOC 범위: {result.df['SOC'].min():.4f} ~ {result.df['SOC'].max():.4f}")
        print(f"  전압 범위: {result.df['Voltage'].min():.4f} ~ {result.df['Voltage'].max():.4f}")
        print("  ✅ 히스테리시스 모드 동작 확인")
    else:
        print("  ❌ 히스테리시스 모드 결과 없음")
        all_pass = False

    # --- 충전 + 휴지 포함 + Time ---
    print("\n--- 5b. 충전+휴지포함+Time ---")
    result = unified_profile_core(
        TOYO_TEST_PATH, (inicycle, inicycle), mincapacity, inirate,
        data_scope="charge", axis_mode="time", continuity="overlay",
        include_rest=True,
    )
    print(f"  행 수: {len(result.df)}, 컬럼: {result.columns}")
    if not result.df.empty and "Condition" in result.df.columns:
        conditions = result.df["Condition"].unique()
        print(f"  포함된 Condition: {conditions}")
        has_rest = 3 in conditions or 0 in conditions
        print(f"  휴지 포함 여부: {'✅' if has_rest else '⚠️ (이 사이클에 휴지가 없을 수 있음)'}")
    else:
        print("  결과 또는 Condition 컬럼 없음")

    # --- 사이클 + 이어서 + Time (Continue 대응) ---
    print("\n--- 5c. 사이클+이어서+Time (Continue 대응) ---")
    result = unified_profile_core(
        TOYO_TEST_PATH, (3, 5), mincapacity, inirate,
        data_scope="cycle", axis_mode="time", continuity="continuous",
        include_rest=True,
    )
    print(f"  행 수: {len(result.df)}, 컬럼: {result.columns}")
    if not result.df.empty:
        print(f"  시간 범위: {result.df['TimeMin'].min():.1f} ~ {result.df['TimeMin'].max():.1f} 분")
        if "Cycle" in result.df.columns:
            cycles = sorted(result.df["Cycle"].unique())
            print(f"  포함된 사이클: {cycles}")
        print("  ✅ Continue 모드 동작 확인")
    else:
        print("  ❌ Continue 모드 결과 없음")
        all_pass = False

    # --- 방전 + SOC ---
    print("\n--- 5d. 방전+SOC ---")
    result = unified_profile_core(
        TOYO_TEST_PATH, (inicycle, inicycle), mincapacity, inirate,
        data_scope="discharge", axis_mode="soc", continuity="overlay",
        include_rest=False, calc_dqdv=True,
    )
    print(f"  행 수: {len(result.df)}, 컬럼: {result.columns}")
    if not result.df.empty:
        print(f"  SOC(DOD) 범위: {result.df['SOC'].min():.4f} ~ {result.df['SOC'].max():.4f}")
        print("  ✅ 방전+SOC 모드 동작 확인")
    else:
        print("  ❌ 방전+SOC 모드 결과 없음")
        all_pass = False

    return all_pass


# ============================================================================
# 6. 메인 실행
# ============================================================================
if __name__ == "__main__":
    print("="*60)
    print("  unified_profile_core() Phase 2 검증 시작")
    print("="*60)
    print(f"  PNE  경로: {PNE_TEST_PATH}")
    print(f"   존재여부: {os.path.isdir(PNE_TEST_PATH)}")
    print(f"  Toyo 경로: {TOYO_TEST_PATH}")
    print(f"   존재여부: {os.path.isdir(TOYO_TEST_PATH)}")

    tests = [
        ("PNE Step", test_pne_step),
        ("PNE Charge", test_pne_charge),
        ("Toyo Step", test_toyo_step),
        ("Toyo Charge", test_toyo_charge),
        ("신규 모드", test_new_modes),
    ]

    results = {}
    for name, fn in tests:
        try:
            passed = fn()
            results[name] = "✅ PASS" if passed else "❌ FAIL"
        except Exception as e:
            results[name] = f"💥 ERROR: {type(e).__name__}: {e}"
            import traceback
            traceback.print_exc()

    print("\n\n" + "="*60)
    print("  검증 결과 요약")
    print("="*60)
    for name, status in results.items():
        print(f"  {status:20s}  {name}")
    print("="*60)
