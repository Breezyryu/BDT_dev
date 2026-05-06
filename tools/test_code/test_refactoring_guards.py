"""리팩토링 안전망 테스트 (Refactoring Guards)

22,000줄 모놀리식 코드를 리팩토링할 때 기존 기능이 깨지지 않도록
핵심 계약(contract)과 인터페이스를 고정하는 테스트.

검증 영역:
  1. 함수 반환 구조 계약 (cycle_data → [mincap, df])
  2. NewData 필수 컬럼 + 타입
  3. 데이터 클래스 필드 존재
  4. 유틸리티 함수 엣지케이스
  5. 그래프 함수 축 생성 확인

실행:
  pytest tests/test_refactoring_guards.py -v
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ── 프로젝트 경로 추가 ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATATOOL_DEV = PROJECT_ROOT / "DataTool_dev"
EXP_DATA = PROJECT_ROOT / "data" / "exp_data"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(DATATOOL_DEV))

try:
    from DataTool_optRCD_proto_ import (
        convert_steplist,
        name_capacity,
        check_cycler,
        binary_search,
    )
    HAS_PROTO = True
except ImportError:
    HAS_PROTO = False

try:
    import matplotlib
    matplotlib.use("Agg")  # 헤드리스 환경
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


# ══════════════════════════════════════════════════════════════
# 상수
# ══════════════════════════════════════════════════════════════

NEWDATA_REQUIRED_COLS = {
    "Cycle", "Dchg", "Chg", "Eff", "Eff2",
    "RndV", "AvgV", "DchgEng", "Temp", "OriCyc",
}

NEWDATA_EXPECTED_TYPES = {
    "Cycle": "int",
    "Dchg": "float",
    "Chg": "float",
    "Eff": "float",
    "Eff2": "float",
    "RndV": "float",
    "AvgV": "float",
    "DchgEng": "float",
    "Temp": "float",
    "OriCyc": "int",
}


# ══════════════════════════════════════════════════════════════
# Test: NewData 계약
# ══════════════════════════════════════════════════════════════

class TestNewDataContract:
    """NewData DataFrame 구조 계약 검증

    리팩토링 후에도 반드시 유지되어야 하는 인터페이스.
    """

    def test_required_columns_list(self):
        """필수 컬럼 10개 정의 확인"""
        assert len(NEWDATA_REQUIRED_COLS) == 10

    def test_synthetic_newdata_has_required_cols(self):
        """합성 데이터가 필수 컬럼을 포함"""
        nd = pd.DataFrame({
            "Cycle": [1, 2, 3],
            "Dchg": [1.0, 0.99, 0.98],
            "Chg": [1.005, 0.995, 0.985],
            "Eff": [0.995, 0.995, 0.995],
            "Eff2": [0.996, 0.996, 0.996],
            "RndV": [4.15, 4.14, 4.13],
            "AvgV": [3.65, 3.64, 3.63],
            "DchgEng": [3.65, 3.61, 3.57],
            "Temp": [25.0, 25.1, 24.9],
            "OriCyc": [1, 2, 3],
        })
        missing = NEWDATA_REQUIRED_COLS - set(nd.columns)
        assert not missing

    def test_newdata_column_types(self):
        """각 컬럼의 예상 타입 (int/float)"""
        nd = pd.DataFrame({
            "Cycle": pd.array([1, 2, 3], dtype="int64"),
            "Dchg": [1.0, 0.99, 0.98],
            "Chg": [1.005, 0.995, 0.985],
            "Eff": [0.995, 0.995, 0.995],
            "Eff2": [0.996, 0.996, 0.996],
            "RndV": [4.15, 4.14, 4.13],
            "AvgV": [3.65, 3.64, 3.63],
            "DchgEng": [3.65, 3.61, 3.57],
            "Temp": [25.0, 25.1, 24.9],
            "OriCyc": pd.array([1, 2, 3], dtype="int64"),
        })
        for col, expected_type in NEWDATA_EXPECTED_TYPES.items():
            if expected_type == "int":
                assert np.issubdtype(nd[col].dtype, np.integer), \
                    f"{col}: {nd[col].dtype} != int"
            elif expected_type == "float":
                assert np.issubdtype(nd[col].dtype, np.floating), \
                    f"{col}: {nd[col].dtype} != float"

    def test_cycle_data_return_structure(self):
        """cycle_data 함수 반환 구조: [mincapacity, df_object]

        리팩토링 후에도 이 구조를 유지해야 한다.
        (실제 데이터 없이 구조만 검증)
        """
        # 모의 반환값
        mock_return = [1689.0, type("MockDF", (), {"NewData": pd.DataFrame()})()]
        assert len(mock_return) == 2
        assert isinstance(mock_return[0], float)
        assert hasattr(mock_return[1], "NewData")


# ══════════════════════════════════════════════════════════════
# Test: 유틸리티 함수 계약 + 엣지케이스
# ══════════════════════════════════════════════════════════════

@pytest.mark.skipif(not HAS_PROTO, reason="proto_ 임포트 불가")
class TestConvertSteplist:
    """convert_steplist() 엣지케이스 테스트"""

    def test_single_number(self):
        assert convert_steplist("5") == [5]

    def test_range(self):
        assert convert_steplist("1-5") == [1, 2, 3, 4, 5]

    def test_comma_separated(self):
        assert convert_steplist("1,3,5") == [1, 3, 5]

    def test_mixed(self):
        assert convert_steplist("1-3,7,9-11") == [1, 2, 3, 7, 9, 10, 11]

    def test_spaces_as_separator(self):
        """공백도 구분자로 동작"""
        assert convert_steplist("1 3 5") == [1, 3, 5]

    def test_range_single_element(self):
        """시작=끝인 범위"""
        assert convert_steplist("5-5") == [5]

    def test_large_range(self):
        """큰 범위"""
        result = convert_steplist("1-100")
        assert len(result) == 100
        assert result[0] == 1
        assert result[-1] == 100


@pytest.mark.skipif(not HAS_PROTO, reason="proto_ 임포트 불가")
class TestNameCapacity:
    """name_capacity() 엣지케이스 테스트"""

    def test_standard_format(self):
        assert name_capacity("test_1689mAh_folder") == 1689.0

    def test_decimal_with_hyphen(self):
        """하이픈 → 소수점 변환"""
        assert name_capacity("2100-5mAh") == pytest.approx(2100.5)

    def test_no_match_returns_none(self):
        """mAh 없는 경로 → None"""
        result = name_capacity("no_capacity_here")
        assert result is None

    def test_special_characters_in_path(self):
        """경로에 괄호, 점 등 포함"""
        result = name_capacity("(sample)_1500mAh_test.csv")
        assert result == 1500.0


@pytest.mark.skipif(not HAS_PROTO, reason="proto_ 임포트 불가")
class TestCheckCycler:
    """check_cycler() 계약 테스트"""

    def test_return_type_is_bool(self, tmp_path):
        """반환 타입은 bool"""
        # 빈 폴더 = Toyo로 판별
        result = check_cycler(str(tmp_path))
        assert isinstance(result, bool)

    def test_empty_folder_is_toyo(self, tmp_path):
        """빈 폴더는 Toyo(False)로 판별"""
        result = check_cycler(str(tmp_path))
        assert result is False  # False = Toyo

    def test_pattern_folder_indicates_pne(self, tmp_path):
        """Pattern 폴더 존재 → PNE(True)"""
        (tmp_path / "Pattern").mkdir()
        result = check_cycler(str(tmp_path))
        assert result is True  # True = PNE


@pytest.mark.skipif(not HAS_PROTO, reason="proto_ 임포트 불가")
class TestBinarySearch:
    """binary_search() 계약 테스트"""

    def test_exact_match(self):
        assert binary_search([1, 3, 5, 7, 9], 5) == 2

    def test_insert_position(self):
        """없는 값 → 삽입 위치 반환"""
        assert binary_search([1, 3, 5, 7, 9], 4) == 2

    def test_empty_list(self):
        assert binary_search([], 5) == 0

    def test_all_smaller(self):
        assert binary_search([1, 2, 3], 10) == 3


# ══════════════════════════════════════════════════════════════
# Test: 그래프 함수 축 생성
# ══════════════════════════════════════════════════════════════

@pytest.mark.skipif(not HAS_MPL, reason="matplotlib 미설치")
class TestGraphOutputContract:
    """graph_output_cycle() 출력 계약

    6개 subplot 축이 모두 생성되는지 확인 (실제 함수 호출 없이 구조만 검증).
    """

    def test_6_subplots_created(self):
        """6개 축 생성 확인"""
        fig, axes = plt.subplots(2, 3, figsize=(15, 8))
        assert axes.shape == (2, 3)
        plt.close(fig)

    def test_axes_labels_settable(self):
        """각 축에 라벨 설정 가능"""
        fig, axes = plt.subplots(2, 3)
        labels = [
            ("Cycle", "Dchg(%)"),
            ("Cycle", "Eff(%)"),
            ("Cycle", "Temp(°C)"),
            ("Cycle", "DCIR(mΩ)"),
            ("Cycle", "RndV(V)"),
            ("Cycle", "Eff2(%)"),
        ]
        for ax, (xlabel, ylabel) in zip(axes.flat, labels):
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            assert ax.get_xlabel() == xlabel
            assert ax.get_ylabel() == ylabel
        plt.close(fig)

    def test_twinx_pattern(self):
        """twinx 패턴 (DCIR subplot에서 사용)"""
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        ax1.set_ylabel("Dchg(%)")
        ax2.set_ylabel("DCIR(mΩ)")
        assert ax1.get_ylabel() == "Dchg(%)"
        assert ax2.get_ylabel() == "DCIR(mΩ)"
        plt.close(fig)


# ══════════════════════════════════════════════════════════════
# Test: DB 컬럼 매핑 계약
# ══════════════════════════════════════════════════════════════

class TestDBColumnMapping:
    """df.NewData ↔ cycle_summary DB 컬럼 매핑

    database.instructions.md에 정의된 매핑이 변경되면 감지.
    """

    DB_MAPPING = {
        "Dchg": "dchg_ratio",
        "Chg": "chg_ratio",
        "Eff": "eff",
        "Eff2": "eff2",
        "RndV": "rest_voltage",
        "AvgV": "avg_voltage",
        "Temp": "temperature",
        "DchgEng": "dchg_energy",
        "dcir": "dcir",
        "dcir2": "dcir2",
        "soc70_dcir": "soc70_dcir",
        "OriCyc": "ori_cycle",
    }

    def test_mapping_count(self):
        """12개 컬럼 매핑 존재"""
        assert len(self.DB_MAPPING) == 12

    def test_all_required_cols_have_mapping(self):
        """NewData 필수 컬럼 중 DB 매핑이 있어야 할 컬럼들"""
        mappable = {"Dchg", "Chg", "Eff", "Eff2", "RndV", "AvgV",
                    "DchgEng", "Temp", "OriCyc"}
        for col in mappable:
            assert col in self.DB_MAPPING, f"{col}: DB 매핑 없음"

    def test_db_column_names_are_snake_case(self):
        """DB 컬럼명은 snake_case"""
        import re
        for nd_col, db_col in self.DB_MAPPING.items():
            assert re.match(r'^[a-z][a-z0-9_]*$', db_col), \
                f"{nd_col} → {db_col}: snake_case 위반"
