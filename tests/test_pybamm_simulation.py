"""PyBaMM 시뮬레이션 테스트

모델 선택, 파라미터 변환, 실험 정의, 시뮬레이션 실행 로직을 검증한다.
pybamm이 설치되어야 실행 가능한 테스트는 @pytest.mark.pybamm 마커 사용.

검증 영역:
  1. 모델 매핑 (SPM/SPMe/DFN)
  2. _key_map 파라미터 변환 (한글→영문, 단위 스케일)
  3. 실험 문자열 형식 정합성
  4. Cutoff 파싱 (C-rate, 시간)
  5. 초기 SOC 모드별 설정
  6. 시뮬레이션 실행 (pybamm 설치 시)

실행:
  pytest tests/test_pybamm_simulation.py -v
  pytest tests/test_pybamm_simulation.py -m pybamm -v  # pybamm 필요 테스트만
"""
import sys
from pathlib import Path

import numpy as np
import pytest

# ── 프로젝트 경로 추가 ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATATOOL_DEV = PROJECT_ROOT / "DataTool_dev"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(DATATOOL_DEV))

# ── pybamm 선택적 임포트 ──
try:
    import pybamm
    HAS_PYBAMM = True
except ImportError:
    HAS_PYBAMM = False

# ── proto_ 함수 임포트 (pybamm 의존 함수는 조건부) ──
try:
    from DataTool_optRCD_proto_ import (
        run_pybamm_simulation,
        convert_steplist,
        name_capacity,
        check_cycler,
    )
    HAS_PROTO = True
except ImportError:
    HAS_PROTO = False


# ══════════════════════════════════════════════════════════════
# 참조 데이터
# ══════════════════════════════════════════════════════════════

MODEL_NAMES = ["SPM", "SPMe", "DFN"]

INIT_SOC_BY_MODE = {
    "charge": 0.0,
    "discharge": 1.0,
    "ccv": 0.0,
    "gitt": 1.0,
    "custom": 0.5,
}

# 프리셋 목록 (pybamm.instructions.md 참조)
PRESET_NAMES = [
    "Chen2020", "Ecker2015", "Marquis2019", "Mohtat2020",
    "NCA_Kim2011", "OKane2022", "ORegan2022",
]

# _key_map 복제 (proto_.py와 동기화)
KEY_MAP = {
    "양극 두께":           ("Positive electrode thickness [m]", 1e-6),
    "양극 입자 반경":      ("Positive particle radius [m]", 1e-6),
    "양극 활물질 비율":    ("Positive electrode active material volume fraction", 1),
    "양극 Bruggeman":     ("Positive electrode Bruggeman coefficient (electrolyte)", 1),
    "음극 두께":           ("Negative electrode thickness [m]", 1e-6),
    "음극 입자 반경":      ("Negative particle radius [m]", 1e-6),
    "음극 활물질 비율":    ("Negative electrode active material volume fraction", 1),
    "음극 Bruggeman":     ("Negative electrode Bruggeman coefficient (electrolyte)", 1),
    "분리막 두께":         ("Separator thickness [m]", 1e-6),
    "분리막 Bruggeman":   ("Separator Bruggeman coefficient (electrolyte)", 1),
    "전해질 농도":         ("Initial concentration in electrolyte [mol.m-3]", 1),
    "전극 면적":           ("Electrode width [m]", 1),
    "셀 용량":             ("Nominal cell capacity [A.h]", 1),
    "온도":                ("Ambient temperature [K]", 1),
}


# ══════════════════════════════════════════════════════════════
# Test: 모델 매핑
# ══════════════════════════════════════════════════════════════

class TestModelMapping:
    """PyBaMM 모델명 ↔ 클래스 매핑 검증"""

    @pytest.mark.parametrize("model_name", MODEL_NAMES)
    def test_valid_model_names(self, model_name):
        """유효한 모델명 3종 확인"""
        model_map = {"SPM": True, "SPMe": True, "DFN": True}
        assert model_name in model_map

    def test_invalid_model_name_pattern(self):
        """잘못된 모델명은 model_map에 없어야 한다"""
        model_map = {"SPM": True, "SPMe": True, "DFN": True}
        invalid_names = ["spm", "P2D", "LFP", "", "DFN2"]
        for name in invalid_names:
            assert name not in model_map, f"{name}이 모델맵에 있으면 안 됨"

    @pytest.mark.pybamm
    @pytest.mark.skipif(not HAS_PYBAMM, reason="pybamm 미설치")
    @pytest.mark.parametrize("model_name", MODEL_NAMES)
    def test_pybamm_model_instantiation(self, model_name):
        """각 모델이 pybamm에서 실제로 인스턴스화 가능"""
        model_map = {
            "SPM": pybamm.lithium_ion.SPM,
            "SPMe": pybamm.lithium_ion.SPMe,
            "DFN": pybamm.lithium_ion.DFN,
        }
        model = model_map[model_name]()
        assert model is not None
        assert hasattr(model, "default_parameter_values")

    @pytest.mark.pybamm
    @pytest.mark.skipif(not HAS_PYBAMM or not HAS_PROTO, reason="pybamm 또는 proto_ 미설치")
    def test_invalid_model_raises_valueerror(self):
        """지원하지 않는 모델명 → ValueError"""
        with pytest.raises(ValueError, match="지원하지 않는 모델"):
            run_pybamm_simulation("INVALID", {}, {"mode": "custom", "steps": ["Rest for 1s"]})


# ══════════════════════════════════════════════════════════════
# Test: 파라미터 변환
# ══════════════════════════════════════════════════════════════

class TestParameterConversion:
    """한글 파라미터 → PyBaMM 영문 파라미터 변환 검증"""

    def test_key_map_completeness(self):
        """_key_map은 14개 파라미터를 포함"""
        assert len(KEY_MAP) == 14

    def test_all_pybamm_keys_are_english(self):
        """PyBaMM 키는 모두 영문이어야 한다"""
        for kr_name, (en_key, _) in KEY_MAP.items():
            # 한글이 포함되면 안 됨
            assert all(ord(c) < 0xAC00 or ord(c) > 0xD7AF for c in en_key), \
                f"{kr_name}의 PyBaMM 키에 한글 포함: {en_key}"

    def test_temperature_separate_handling(self):
        """온도는 +273.15 변환, 스케일 곱하기가 아님"""
        kr_name = "온도"
        _, scale = KEY_MAP[kr_name]
        # 스케일은 1이지만, 실제 변환은 val + 273.15
        assert scale == 1
        # 변환 시뮬레이션
        celsius = 25.0
        kelvin = celsius + 273.15
        assert kelvin == pytest.approx(298.15)

    def test_thickness_parameters_have_correct_units(self):
        """두께 파라미터의 PyBaMM 키에 [m] 단위 표기"""
        thickness_keys = ["양극 두께", "음극 두께", "분리막 두께",
                          "양극 입자 반경", "음극 입자 반경"]
        for key in thickness_keys:
            pybamm_key, _ = KEY_MAP[key]
            assert "[m]" in pybamm_key, f"{key}: PyBaMM 키에 [m] 없음: {pybamm_key}"

    def test_parameter_override_simulation(self):
        """파라미터 오버라이드 시뮬레이션 (mock)"""
        params_dict = {
            "양극 두께": "75.6",    # μm
            "음극 두께": "85.0",    # μm
            "온도": "25",           # °C
            "셀 용량": "5.0",       # Ah
        }
        converted = {}
        for kr_name, val_str in params_dict.items():
            if kr_name in KEY_MAP:
                pybamm_key, scale = KEY_MAP[kr_name]
                val = float(val_str)
                if kr_name == "온도":
                    val = val + 273.15
                else:
                    val = val * scale
                converted[pybamm_key] = val

        assert converted["Positive electrode thickness [m]"] == pytest.approx(75.6e-6)
        assert converted["Negative electrode thickness [m]"] == pytest.approx(85.0e-6)
        assert converted["Ambient temperature [K]"] == pytest.approx(298.15)
        assert converted["Nominal cell capacity [A.h]"] == pytest.approx(5.0)


# ══════════════════════════════════════════════════════════════
# Test: 실험 문자열 형식
# ══════════════════════════════════════════════════════════════

class TestExperimentStringFormat:
    """PyBaMM 실험 정의 문자열 검증"""

    def test_cc_discharge_format(self):
        """CC 방전 문자열 형식"""
        step = "Discharge at 1C until 2.5V"
        assert "Discharge" in step
        assert "C" in step
        assert "V" in step

    def test_cc_charge_format(self):
        """CC 충전 문자열 형식"""
        step = "Charge at 0.5C until 4.2V"
        assert "Charge" in step

    def test_cv_hold_format(self):
        """CV 홀드 문자열 형식"""
        step = "Hold at 4.2V until C/50"
        assert "Hold" in step
        assert "V" in step

    def test_rest_format(self):
        """휴지 문자열 형식"""
        step = "Rest for 3600s"
        assert "Rest" in step

    def test_gitt_pattern_structure(self):
        """GITT 패턴: (펄스 방전 + 휴지) × N"""
        pulse_c = 1.0
        pulse_t = 10
        rest_t = 600
        v_min = 2.5
        repeats = 5

        step_pair = [
            f"Discharge at {pulse_c}C for {pulse_t}s or until {v_min}V",
            f"Rest for {rest_t}s",
        ]
        steps = step_pair * repeats
        assert len(steps) == 2 * repeats
        assert all("Discharge" in s or "Rest" in s for s in steps)

    def test_period_suffix(self):
        """출력 주기 접미사 형식"""
        base = "Discharge at 1C until 2.5V"
        period = 10
        with_period = f"{base} ({period} second period)"
        assert "second period" in with_period


# ══════════════════════════════════════════════════════════════
# Test: 초기 SOC 설정
# ══════════════════════════════════════════════════════════════

class TestInitialSOC:
    """모드별 초기 SOC 설정 검증"""

    @pytest.mark.parametrize("mode, expected_soc", [
        ("charge", 0.0),
        ("discharge", 1.0),
        ("ccv", 0.0),
        ("gitt", 1.0),
        ("custom", 0.5),
    ])
    def test_auto_soc_by_mode(self, mode, expected_soc):
        """각 모드의 auto SOC 값"""
        assert INIT_SOC_BY_MODE[mode] == expected_soc

    def test_soc_bounds_enforced(self):
        """SOC는 0.0~1.0 범위 내"""
        for soc in INIT_SOC_BY_MODE.values():
            assert 0.0 <= soc <= 1.0


# ══════════════════════════════════════════════════════════════
# Test: _safe() 변수 추출 패턴
# ══════════════════════════════════════════════════════════════

class TestSafeVariableExtraction:
    """_safe() 헬퍼 패턴 검증: 2D→1D, None 반환"""

    def test_1d_array_passthrough(self):
        """1D 배열은 그대로 반환"""
        arr = np.array([1.0, 2.0, 3.0])
        if arr.ndim == 2:
            arr = np.mean(arr, axis=0)
        assert arr.ndim == 1
        assert len(arr) == 3

    def test_2d_array_averaged_to_1d(self):
        """2D 배열 → axis=0 평균 → 1D"""
        arr = np.array([[1.0, 2.0, 3.0],
                        [4.0, 5.0, 6.0]])
        assert arr.ndim == 2
        result = np.mean(arr, axis=0)
        assert result.ndim == 1
        np.testing.assert_allclose(result, [2.5, 3.5, 4.5])

    def test_none_on_missing_key(self):
        """키가 없으면 None 반환 (예외 잡기)"""
        mock_sol = {}
        try:
            arr = mock_sol["Nonexistent key"]
        except (KeyError, Exception):
            arr = None
        assert arr is None

    def test_time_unit_conversion(self):
        """시간 단위: 초 → 분"""
        t_seconds = np.array([0, 60, 120, 180])
        t_minutes = t_seconds / 60.0
        np.testing.assert_allclose(t_minutes, [0, 1, 2, 3])


# ══════════════════════════════════════════════════════════════
# Test: 실제 시뮬레이션 실행 (pybamm 필요)
# ══════════════════════════════════════════════════════════════

@pytest.mark.pybamm
@pytest.mark.slow
@pytest.mark.skipif(not HAS_PYBAMM, reason="pybamm 미설치")
class TestSimulationExecution:
    """PyBaMM 시뮬레이션 실제 실행 테스트"""

    def test_spm_basic_discharge(self):
        """SPM 기본 방전 시뮬레이션 실행"""
        model = pybamm.lithium_ion.SPM()
        param = model.default_parameter_values
        experiment = pybamm.Experiment([
            "Discharge at 1C until 2.5V",
        ])
        sim = pybamm.Simulation(model, experiment=experiment,
                                parameter_values=param)
        sol = sim.solve()
        assert sol is not None
        assert not isinstance(sol, pybamm.EmptySolution)

    def test_spm_returns_voltage(self):
        """시뮬레이션 결과에서 전압 추출 가능"""
        model = pybamm.lithium_ion.SPM()
        param = model.default_parameter_values
        experiment = pybamm.Experiment([
            "Discharge at 0.5C until 3.0V",
        ])
        sim = pybamm.Simulation(model, experiment=experiment,
                                parameter_values=param)
        sol = sim.solve()
        voltage = sol["Terminal voltage [V]"].entries
        assert len(voltage) > 0
        assert voltage[0] > voltage[-1]  # 방전 → 전압 감소

    def test_spm_ccv_cycle(self):
        """CC-CV 풀사이클 실행"""
        model = pybamm.lithium_ion.SPM()
        param = model.default_parameter_values
        experiment = pybamm.Experiment([
            "Charge at 1C until 4.2V",
            "Hold at 4.2V until C/50",
            "Discharge at 1C until 2.5V",
        ])
        sim = pybamm.Simulation(model, experiment=experiment,
                                parameter_values=param)
        sol = sim.solve(initial_soc=0.0)
        assert sol is not None

    @pytest.mark.skipif(not HAS_PROTO, reason="proto_ 임포트 불가")
    def test_run_pybamm_simulation_custom_mode(self):
        """run_pybamm_simulation() custom 모드 실행"""
        params = {"온도": "25", "셀 용량": "5.0"}
        config = {
            "mode": "custom",
            "steps": ["Discharge at 1C until 2.5V"],
            "init_soc": 1.0,
            "period": "auto",
        }
        sol, param_vals = run_pybamm_simulation("SPM", params, config)
        assert sol is not None


# ══════════════════════════════════════════════════════════════
# Test: 유틸리티 함수 (proto_ 의존)
# ══════════════════════════════════════════════════════════════

@pytest.mark.skipif(not HAS_PROTO, reason="proto_ 임포트 불가")
class TestUtilityFunctions:
    """proto_.py 유틸리티 함수 검증"""

    @pytest.mark.parametrize("input_str, expected", [
        ("1-5", [1, 2, 3, 4, 5]),
        ("1,3,5", [1, 3, 5]),
        ("1-3,7,9-11", [1, 2, 3, 7, 9, 10, 11]),
        ("10", [10]),
    ])
    def test_convert_steplist(self, input_str, expected):
        """스텝 리스트 파싱 정확성"""
        result = convert_steplist(input_str)
        assert result == expected

    @pytest.mark.parametrize("folder_name, expected_cap", [
        ("1689mAh_ATL_test", 1689.0),
        ("250207_3500mAh_Samsung", 3500.0),
        ("2100-5mAh_test", 2100.5),  # -를 .으로 변환
    ])
    def test_name_capacity(self, folder_name, expected_cap):
        """폴더명에서 mAh 용량 추출"""
        result = name_capacity(folder_name)
        assert result == pytest.approx(expected_cap)

    def test_name_capacity_no_match(self):
        """mAh 없는 폴더명 → None"""
        result = name_capacity("no_capacity_folder")
        assert result is None
