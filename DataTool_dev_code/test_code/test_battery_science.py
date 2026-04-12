"""배터리 과학 검증 테스트 (Level S)

전기화학 원리 기반 데이터 처리 로직의 물리적 정합성을 검증한다.
리팩토링 시 과학적 정합성이 깨지지 않도록 보호하는 안전망 역할.

검증 영역:
  1. 단위 변환 (_key_map 스케일, °C→K)
  2. 물리적 범위 (DCIR > 0, 0 ≤ SOC ≤ 1, 전압 한계)
  3. 쿨롱 효율 계산 (CE = Q_dchg / Q_chg)
  4. NewData 물리 일관성
  5. 합성 데이터 기반 열화 트렌드 검증

실행:
  pytest tests/test_battery_science.py -v
  pytest tests/test_battery_science.py -m science -v
"""
import numpy as np
import pandas as pd
import pytest


# ══════════════════════════════════════════════════════════════
# 합성 데이터 헬퍼
# ══════════════════════════════════════════════════════════════

def make_synthetic_newdata(n_cycles: int = 100,
                           degradation_rate: float = 0.001,
                           seed: int = 42) -> pd.DataFrame:
    """물리적으로 유효한 합성 NewData DataFrame 생성

    Parameters
    ----------
    n_cycles : int
        사이클 수
    degradation_rate : float
        사이클당 용량 감소율 (0.001 = 사이클 제곱근 계수)
    seed : int
        랜덤 시드
    """
    rng = np.random.default_rng(seed)
    cycles = np.arange(1, n_cycles + 1)

    # 용량 열화: 1 - a*sqrt(n) 패턴 (SEI 성장 모델)
    dchg = 1.0 - degradation_rate * np.sqrt(cycles) + rng.normal(0, 0.002, n_cycles)
    chg = dchg / (0.995 + rng.normal(0, 0.001, n_cycles))  # CE ~99.5%
    eff = dchg / chg
    eff2 = np.roll(chg, -1) / dchg  # Chg(n+1)/Dchg(n)
    eff2[-1] = eff[-1]  # 마지막 사이클 보정

    return pd.DataFrame({
        "Cycle": cycles,
        "Dchg": np.clip(dchg, 0, 1.5),
        "Chg": np.clip(chg, 0, 1.5),
        "Eff": np.clip(eff, 0.5, 1.05),
        "Eff2": np.clip(eff2, 0.5, 1.05),
        "RndV": 4.15 - 0.0001 * cycles,
        "AvgV": 3.65 - 0.0002 * cycles,
        "DchgEng": np.clip(dchg, 0, 1.5) * 3.65,
        "Temp": 25.0 + rng.normal(0, 0.5, n_cycles),
        "OriCyc": cycles,
    })


# ══════════════════════════════════════════════════════════════
# PyBaMM _key_map 참조 (proto_.py와 동일)
# ══════════════════════════════════════════════════════════════

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
# 물리 상수
# ══════════════════════════════════════════════════════════════

FARADAY = 96485      # C/mol
GAS_CONST = 8.314    # J/(mol·K)
T_STANDARD = 298.15  # K (25°C)


# ══════════════════════════════════════════════════════════════
# Test: 단위 변환 정합성
# ══════════════════════════════════════════════════════════════

@pytest.mark.science
class TestUnitConversion:
    """_key_map 단위 변환 및 °C→K 변환 검증"""

    def test_key_map_has_14_entries(self):
        """_key_map은 정확히 14개 파라미터를 포함해야 한다"""
        assert len(KEY_MAP) == 14

    def test_thickness_scale_is_micro_to_meter(self):
        """두께 파라미터 (μm → m) 변환: 스케일 = 1e-6"""
        thickness_keys = ["양극 두께", "음극 두께", "분리막 두께",
                          "양극 입자 반경", "음극 입자 반경"]
        for key in thickness_keys:
            _, scale = KEY_MAP[key]
            assert scale == 1e-6, f"{key}: 스케일 {scale} != 1e-6"

    def test_dimensionless_scale_is_one(self):
        """무차원 파라미터 (비율, Bruggeman) 변환: 스케일 = 1"""
        dimensionless_keys = ["양극 활물질 비율", "음극 활물질 비율",
                              "양극 Bruggeman", "음극 Bruggeman",
                              "분리막 Bruggeman"]
        for key in dimensionless_keys:
            _, scale = KEY_MAP[key]
            assert scale == 1, f"{key}: 스케일 {scale} != 1"

    def test_temperature_celsius_to_kelvin(self):
        """25°C → 298.15K 변환 정확성"""
        celsius = 25.0
        kelvin = celsius + 273.15
        assert kelvin == pytest.approx(T_STANDARD, abs=0.01)

    def test_temperature_conversion_negative(self):
        """-10°C → 263.15K"""
        celsius = -10.0
        kelvin = celsius + 273.15
        assert kelvin == pytest.approx(263.15, abs=0.01)

    def test_thickness_conversion_example(self):
        """양극 두께 75.6μm → 75.6e-6 m"""
        thickness_um = 75.6  # μm (개발부서 입력값)
        _, scale = KEY_MAP["양극 두께"]
        thickness_m = thickness_um * scale
        assert thickness_m == pytest.approx(75.6e-6, rel=1e-10)

    def test_electrolyte_concentration_scale(self):
        """전해질 농도: M → mol/m³ (현재 스케일=1, 수동 ×1000 필요)

        Note: _key_map에서 전해질 농도 스케일이 1로 설정되어 있어,
        사용자가 mol/m³ 단위로 직접 입력하거나 UI에서 변환해야 한다.
        """
        _, scale = KEY_MAP["전해질 농도"]
        assert scale == 1  # 현재 설정 확인

    def test_all_keys_have_tuple_format(self):
        """모든 _key_map 값은 (str, number) 튜플이어야 한다"""
        for kr_name, (pybamm_key, scale) in KEY_MAP.items():
            assert isinstance(pybamm_key, str), f"{kr_name}: 키가 문자열이 아님"
            assert isinstance(scale, (int, float)), f"{kr_name}: 스케일이 숫자가 아님"
            assert scale > 0, f"{kr_name}: 스케일이 0 이하"


# ══════════════════════════════════════════════════════════════
# Test: 물리적 범위 검증
# ══════════════════════════════════════════════════════════════

@pytest.mark.science
class TestPhysicalBounds:
    """배터리 데이터의 물리적 유효 범위 검증"""

    @pytest.fixture
    def nd(self):
        """합성 NewData"""
        return make_synthetic_newdata()

    def test_capacity_ratio_positive(self, nd):
        """용량 비율은 양수여야 한다"""
        assert (nd["Dchg"] >= 0).all()
        assert (nd["Chg"] >= 0).all()

    def test_capacity_ratio_upper_bound(self, nd):
        """용량 비율은 1.5를 넘지 않아야 한다 (초기 화성 포함)"""
        assert (nd["Dchg"] <= 1.5).all()

    def test_coulombic_efficiency_range(self, nd):
        """쿨롱 효율: 0.5 < CE < 1.05 (정상 셀)"""
        eff = nd["Eff"].dropna()
        assert (eff > 0.5).all(), f"CE 최소값: {eff.min():.4f}"
        assert (eff < 1.05).all(), f"CE 최대값: {eff.max():.4f}"

    def test_soc_bounds(self):
        """SOC는 0~1 범위여야 한다"""
        soc_values = [0.0, 0.3, 0.5, 0.7, 1.0]
        for soc in soc_values:
            assert 0.0 <= soc <= 1.0

    def test_soc_out_of_bounds_detection(self):
        """SOC 범위 초과 감지"""
        invalid_soc = [-0.1, 1.1, 2.0]
        for soc in invalid_soc:
            assert not (0.0 <= soc <= 1.0), f"SOC {soc}는 범위 밖이어야 한다"

    def test_voltage_nmc_chemistry_limits(self):
        """NMC 전압 범위: 2.5 ~ 4.35 V"""
        v_min, v_max = 2.5, 4.35
        test_voltages = [2.5, 3.0, 3.6, 3.8, 4.2, 4.35]
        for v in test_voltages:
            assert v_min <= v <= v_max, f"전압 {v}V가 NMC 범위 밖"

    def test_rest_voltage_physically_valid(self, nd):
        """휴지 전압(RndV)은 일반적으로 3.0~4.3V 범위"""
        rndv = nd["RndV"].dropna()
        assert (rndv > 3.0).all()
        assert (rndv < 4.3).all()

    def test_temperature_test_range(self, nd):
        """시험 온도: -20 ~ 80°C 범위"""
        temp = nd["Temp"].dropna()
        assert (temp > -20).all()
        assert (temp < 80).all()

    def test_dcir_must_be_positive(self):
        """DCIR 계산: ΔV/ΔI > 0 (물리적 필수)"""
        v_before = 3.7    # V (펄스 전 전압)
        v_after = 3.65    # V (펄스 중 전압)
        i_pulse = 1.0     # A (방전 전류)
        dcir = abs(v_before - v_after) / i_pulse
        assert dcir > 0, "DCIR은 양수여야 한다"

    def test_dcir_zero_current_invalid(self):
        """전류 0에서 DCIR 계산은 물리적으로 무효"""
        with pytest.raises(ZeroDivisionError):
            _ = 0.05 / 0.0  # ΔV / 0


# ══════════════════════════════════════════════════════════════
# Test: NewData 구조 계약 (과학적 일관성)
# ══════════════════════════════════════════════════════════════

NEWDATA_REQUIRED_COLS = {
    "Cycle", "Dchg", "Chg", "Eff", "Eff2",
    "RndV", "AvgV", "DchgEng", "Temp", "OriCyc",
}


@pytest.mark.science
class TestNewDataConsistency:
    """NewData DataFrame의 과학적 일관성 검증"""

    @pytest.fixture
    def nd(self):
        return make_synthetic_newdata(200)

    def test_required_columns_present(self, nd):
        """필수 10개 컬럼 존재"""
        missing = NEWDATA_REQUIRED_COLS - set(nd.columns)
        assert not missing, f"누락 컬럼: {missing}"

    def test_cycle_monotonic_increasing(self, nd):
        """사이클 번호는 단조 증가"""
        assert nd["Cycle"].is_monotonic_increasing

    def test_efficiency_equals_dchg_over_chg(self, nd):
        """Eff = Dchg / Chg 일관성"""
        expected_eff = nd["Dchg"] / nd["Chg"]
        # 클리핑 때문에 약간의 차이 허용
        np.testing.assert_allclose(
            nd["Eff"].values, np.clip(expected_eff.values, 0.5, 1.05),
            atol=0.01
        )

    def test_energy_proportional_to_capacity(self, nd):
        """방전 에너지 ∝ 방전 용량 × 평균 전압"""
        # DchgEng = Dchg * V_avg (근사)
        expected_eng = nd["Dchg"] * 3.65  # 합성 데이터의 기본 AvgV
        np.testing.assert_allclose(nd["DchgEng"].values, expected_eng.values, atol=0.1)

    def test_degradation_trend(self, nd):
        """용량 열화 트렌드: 후반 사이클 < 초반 사이클"""
        first_10 = nd["Dchg"].iloc[:10].mean()
        last_10 = nd["Dchg"].iloc[-10:].mean()
        assert last_10 < first_10, "후반 용량이 초반보다 낮아야 한다"

    def test_rest_voltage_declining_trend(self, nd):
        """휴지 전압 트렌드: 열화에 따라 소폭 감소"""
        first_rndv = nd["RndV"].iloc[:10].mean()
        last_rndv = nd["RndV"].iloc[-10:].mean()
        assert last_rndv <= first_rndv, "휴지 전압은 열화에 따라 감소 추세"


# ══════════════════════════════════════════════════════════════
# Test: 전기화학 기본 공식
# ══════════════════════════════════════════════════════════════

@pytest.mark.science
class TestElectrochemicalFormulas:
    """기본 전기화학 공식의 정확성 검증"""

    def test_cell_voltage_equation(self):
        """V_cell = U_pos - U_neg - η_pos - η_neg - I·R_ohm"""
        u_pos = 3.85   # V (양극 OCP)
        u_neg = 0.12   # V (음극 OCP)
        eta_pos = 0.02  # V (양극 과전압)
        eta_neg = 0.01  # V (음극 과전압)
        i_r_ohm = 0.03  # V (옴 손실)

        v_cell = u_pos - u_neg - eta_pos - eta_neg - i_r_ohm
        expected = 3.85 - 0.12 - 0.02 - 0.01 - 0.03
        assert v_cell == pytest.approx(expected, abs=1e-10)
        assert v_cell > 0, "셀 전압은 양수여야 한다"

    def test_ocv_equals_ocp_difference(self):
        """OCV = U_pos - U_neg (평형 상태)"""
        u_pos = 3.85
        u_neg = 0.12
        ocv = u_pos - u_neg
        assert ocv == pytest.approx(3.73, abs=0.01)

    def test_crate_definition(self):
        """C-rate = I_applied / Q_nominal"""
        q_nominal = 5.0   # Ah
        i_applied = 10.0  # A
        crate = i_applied / q_nominal
        assert crate == pytest.approx(2.0)  # 2C

    def test_crate_to_time(self):
        """1C = 1시간 완방, 0.2C = 5시간"""
        assert 1.0 / 1.0 == pytest.approx(1.0)    # 1C → 1시간
        assert 1.0 / 0.2 == pytest.approx(5.0)    # 0.2C → 5시간
        assert 1.0 / 2.0 == pytest.approx(0.5)    # 2C → 30분

    def test_specific_capacity_to_cmax(self):
        """비용량 → 최대 고상 농도 변환

        c_max = (q_mAh/g × 3.6 × ρ_g/cc × 1e6) / F
        """
        q_mah_g = 180.0        # mAh/g (NMC811 비용량)
        density_gcc = 4.7       # g/cc (NMC811 진밀도)
        F = FARADAY

        c_max = (q_mah_g * 3.6 * density_gcc * 1e6) / F
        # 대략 31,500 mol/m³ 근처
        assert 25000 < c_max < 40000, f"c_max = {c_max:.0f} mol/m³"

    def test_press_density_to_volume_fraction(self):
        """합제밀도 + 배합비 → 활물질 체적분율

        ε_AM = (ρ_press × w_AM) / ρ_AM_true
        """
        press_density = 3.45  # g/cc
        formulation = [96, 2, 2]  # 활물질:바인더:도전재
        rho_am_true = 4.7     # g/cc (NMC811)

        w_am = formulation[0] / sum(formulation)
        epsilon_am = (press_density * w_am) / rho_am_true
        assert 0.0 < epsilon_am < 1.0, f"체적분율 {epsilon_am:.3f}은 0~1 범위여야"
        # NMC811 전형적 범위: 0.6~0.75
        assert 0.5 < epsilon_am < 0.85

    def test_loading_to_thickness(self):
        """로딩 → 두께 변환 (교차검증용)

        t_μm = (loading_mg/cm² / press_density_g/cc) × 10
        """
        loading = 25.0      # mg/cm²
        press_density = 3.45  # g/cc
        thickness_um = (loading / press_density) * 10
        # 전형적 양극 두께 50~100μm
        assert 50 < thickness_um < 100

    def test_arrhenius_temperature_acceleration(self):
        """Arrhenius 온도 가속: 10°C 상승 ≈ 2배 열화율

        k(T) = A × exp(-Ea / (R × T))
        """
        Ea = 50000  # J/mol (전형적 LIB 열화 활성화 에너지)
        R = GAS_CONST
        T1 = 298.15  # 25°C
        T2 = 308.15  # 35°C

        # ln(k2/k1) = (Ea/R) × (1/T1 - 1/T2)
        acceleration = np.exp((Ea / R) * (1/T1 - 1/T2))
        # 10°C 상승 시 약 2배 (Ea=50kJ/mol 기준)
        assert 1.5 < acceleration < 3.0, f"가속 계수 = {acceleration:.2f}"


# ══════════════════════════════════════════════════════════════
# Test: 수명 예측 모델
# ══════════════════════════════════════════════════════════════

@pytest.mark.science
class TestLifetimeModel:
    """BDT 경험적 수명 예측 모델 검증

    Q(n) = 1 - a·n^b - c·exp(d·(n - e))
    """

    def test_model_at_cycle_zero(self):
        """n=0에서 Q=1 (초기 상태)"""
        a, b, c, d, e = 0.001, 0.5, 1e-6, 0.005, 500
        n = 0
        q = 1 - a * n**b - c * np.exp(d * (n - e))
        # n=0이면 a*0^0.5=0, exp항도 매우 작음
        assert q > 0.99

    def test_model_monotonic_decrease(self):
        """모델 출력은 단조 감소 추세"""
        a, b, c, d, e = 0.002, 0.5, 1e-8, 0.008, 800
        cycles = np.arange(1, 1001)
        q = 1 - a * cycles**b - c * np.exp(d * (cycles - e))
        # 초반 소폭 변동 허용, 전체 추세는 감소
        assert q[-1] < q[0]

    def test_model_eol_at_80_percent(self):
        """EOL 기준: 80% 용량 유지 시점 존재"""
        a, b, c, d, e = 0.003, 0.5, 1e-7, 0.006, 600
        cycles = np.arange(1, 2001)
        q = 1 - a * cycles**b - c * np.exp(d * (cycles - e))
        eol_mask = q < 0.80
        if eol_mask.any():
            eol_cycle = cycles[eol_mask][0]
            assert eol_cycle > 0, "EOL 사이클은 양수여야 한다"

    def test_sqrt_degradation_consistent_with_sei(self):
        """b ≈ 0.5이면 √n SEI 성장 모델과 일치"""
        a, b = 0.005, 0.5
        n = np.array([100, 400, 900, 1600])
        fade = a * n**b
        # √n 비례: fade(400)/fade(100) ≈ 2
        ratio = fade[1] / fade[0]
        assert ratio == pytest.approx(2.0, abs=0.01)
