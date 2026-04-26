"""BDT PyBaMM 시뮬레이션 코어 — lazy 로드 게이트.

이 모듈을 import 하는 시점에 `pybamm` 은 절대 로드되지 않는다.
`is_available()` / `run_simulation()` / `is_empty_solution()` /
`okane2022_param_values()` 첫 호출 시점에만 import 가 트리거되며, frozen 빌드에서는
같은 시점에 casadi MinGW DLL 8개도 한 번만 선로드된다.

PyBaMM 탭을 켜지 않는 사용자는 콜드 스타트에서 pybamm/casadi 가 sys.modules 에 들어오지 않는다.
"""
from __future__ import annotations

import importlib.util
import os
import sys

_pybamm_mod = None
_dlls_loaded = False
_CASADI_DLLS = (
    "libwinpthread-1.dll",
    "libgcc_s_seh-1.dll",
    "libstdc++-6.dll",
    "libgfortran-5.dll",
    "libquadmath-0.dll",
    "libgomp-1.dll",
    "libcasadi.dll",
    "libcasadi-tp-openblas.dll",
)


def _ensure_pybamm_runtime() -> None:
    """frozen 빌드에서 casadi DLL 8개 선로드 + PATH 등록. 두 번째 호출부터 NOOP."""
    global _dlls_loaded
    if _dlls_loaded:
        return
    _dlls_loaded = True
    if not getattr(sys, "frozen", False):
        return
    base = getattr(sys, "_MEIPASS", None)
    if not base:
        return
    casadi_dir = os.path.join(base, "casadi")
    if not os.path.isdir(casadi_dir):
        return
    try:
        os.add_dll_directory(casadi_dir)
        os.add_dll_directory(base)
    except OSError:
        pass
    os.environ["PATH"] = casadi_dir + os.pathsep + base + os.pathsep + os.environ.get("PATH", "")
    import ctypes
    for name in _CASADI_DLLS:
        path = os.path.join(casadi_dir, name)
        if os.path.isfile(path):
            try:
                ctypes.CDLL(path)
            except OSError:
                pass


def _lazy_pybamm():
    """실제 pybamm 모듈을 lazy 로 import 후 캐시. 실패 시 ImportError 그대로 전파."""
    global _pybamm_mod
    if _pybamm_mod is not None:
        return _pybamm_mod
    _ensure_pybamm_runtime()
    import pybamm  # noqa: WPS433 — lazy intentional
    _pybamm_mod = pybamm
    return pybamm


def is_installed() -> bool:
    """패키지 설치 여부만 확인. 실제 import 는 발생하지 않음 — 콜드 스타트 영향 없음."""
    return importlib.util.find_spec("pybamm") is not None


def is_available() -> bool:
    """PyBaMM 사용 가능 여부 (실제 import 시도)."""
    try:
        _lazy_pybamm()
        return True
    except Exception:
        return False


def is_empty_solution(sol) -> bool:
    """pybamm.EmptySolution 또는 __getitem__ 미지원 결과인지 검사."""
    try:
        pybamm = _lazy_pybamm()
    except Exception:
        return True
    return isinstance(sol, pybamm.EmptySolution) or not hasattr(sol, "__getitem__")


def okane2022_param_values():
    """`pybamm.ParameterValues("OKane2022")` lazy 래퍼."""
    pybamm = _lazy_pybamm()
    return pybamm.ParameterValues("OKane2022")


# ===== 시뮬레이션 엔진 (proto 의 run_pybamm_simulation 본문 이전) =====
def run_simulation(model_name, params_dict, experiment_config):
    """PyBaMM 전기화학 시뮬레이션 실행.

    Parameters
    ----------
    model_name : str
        "SPM" | "SPMe" | "DFN"
    params_dict : dict
        테이블에서 읽은 파라미터 값 (한글 키 → float/str)
    experiment_config : dict
        mode: "ccv" | "charge" | "discharge" | "custom" | "gitt"

    Returns
    -------
    (solution, param)
        pybamm Solution 과 적용된 ParameterValues
    """
    pybamm = _lazy_pybamm()

    # 1) 모델 — 리튬 plating 서브모델 포함
    model_map = {
        "SPM": pybamm.lithium_ion.SPM,
        "SPMe": pybamm.lithium_ion.SPMe,
        "DFN": pybamm.lithium_ion.DFN,
    }
    if model_name not in model_map:
        raise ValueError(f"지원하지 않는 모델: {model_name}")
    model = model_map[model_name]({
        "lithium plating": "irreversible",
        "thermal": "lumped",
    })

    # 2) 파라미터 (OKane2022 기본 + 테이블 값 덮어쓰기)
    param = pybamm.ParameterValues("OKane2022")
    _key_map = {
        "양극 두께":              ("Positive electrode thickness [m]", 1e-6),
        "양극 입자 반경":          ("Positive particle radius [m]", 1e-6),
        "양극 활물질 비율":        ("Positive electrode active material volume fraction", 1),
        "양극 기공률":            ("Positive electrode porosity", 1),
        "음극 두께":              ("Negative electrode thickness [m]", 1e-6),
        "음극 입자 반경":          ("Negative particle radius [m]", 1e-6),
        "음극 활물질 비율":        ("Negative electrode active material volume fraction", 1),
        "음극 기공률":            ("Negative electrode porosity", 1),
        "분리막 두께":             ("Separator thickness [m]", 1e-6),
        "분리막 기공률":           ("Separator porosity", 1),
        "전극 면적(폭)":          ("Electrode width [m]", 1),
        "전극 높이":              ("Electrode height [m]", 1),
        "적층 수":                ("Number of electrodes connected in parallel to make a cell", 1),
        "셀 용량":                ("Nominal cell capacity [A.h]", 1),
        "양극 고상확산계수":       ("Positive electrode diffusivity [m2.s-1]", 1),
        "음극 고상확산계수":       ("Negative electrode diffusivity [m2.s-1]", 1),
        "전해질 확산계수":         ("Electrolyte diffusivity [m2.s-1]", 1),
        "전해질 이온전도도":       ("Electrolyte conductivity [S.m-1]", 1),
        "양극 전자전도도":         ("Positive electrode conductivity [S.m-1]", 1),
        "음극 전자전도도":         ("Negative electrode conductivity [S.m-1]", 1),
        "전해질 농도":             ("Initial concentration in electrolyte [mol.m-3]", 1),
        "양극 Bruggeman":         ("Positive electrode Bruggeman coefficient (electrolyte)", 1),
        "음극 Bruggeman":         ("Negative electrode Bruggeman coefficient (electrolyte)", 1),
        "분리막 Bruggeman":       ("Separator Bruggeman coefficient (electrolyte)", 1),
        "양극 교환전류밀도":       ("Positive electrode exchange-current density [A.m-2]", 1),
        "음극 교환전류밀도":       ("Negative electrode exchange-current density [A.m-2]", 1),
        "양극 최대농도":           ("Maximum concentration in positive electrode [mol.m-3]", 1),
        "음극 최대농도":           ("Maximum concentration in negative electrode [mol.m-3]", 1),
        "Plating 속도상수":       ("Lithium plating kinetic rate constant [m.s-1]", 1),
        "Plating 전달계수":       ("Lithium plating transfer coefficient", 1),
        "양극 OCP":               ("Positive electrode OCP [V]", 1),
        "음극 OCP":               ("Negative electrode OCP [V]", 1),
        "온도":                   ("Ambient temperature [K]", 1),
        "열전달 계수":             ("Total heat transfer coefficient [W.m-2.K-1]", 1),
        "상한 전압":              ("Upper voltage cut-off [V]", 1),
        "하한 전압":              ("Lower voltage cut-off [V]", 1),
    }
    for kr_name, val_str in params_dict.items():
        if kr_name not in _key_map:
            continue
        pybamm_key, scale = _key_map[kr_name]
        stripped = val_str.strip()
        if stripped.lower() == "auto" or stripped.startswith("f("):
            continue
        try:
            val = float(stripped)
        except ValueError:
            continue
        if kr_name == "온도":
            val = val + 273.15
        else:
            val = val * scale
        try:
            param[pybamm_key] = val
            if kr_name == "온도":
                param["Initial temperature [K]"] = val
        except Exception:
            pass

    mode = experiment_config.get("mode", "ccv")
    user_soc = experiment_config.get("init_soc", "auto")
    init_soc = None
    if user_soc and user_soc != "auto":
        try:
            init_soc = float(user_soc)
        except ValueError:
            init_soc = None
    if init_soc is None:
        if mode == "charge":
            init_soc = 0.0
        elif mode in ("discharge", "gitt"):
            init_soc = 1.0
        elif mode == "ccv":
            init_soc = 0.0
        else:
            init_soc = 0.5

    if mode == "ccv":
        chg_c = experiment_config.get("chg_crate", 1.0)
        dchg_c = experiment_config.get("dchg_crate", 1.0)
        v_max = experiment_config.get("v_max", 4.2)
        v_min = experiment_config.get("v_min", 2.5)
        cv_cutoff = experiment_config.get("cv_cutoff", 0.05)
        cycles = int(experiment_config.get("cycles", 1))
        exp_steps = [
            f"Charge at {chg_c}C until {v_max}V",
            f"Hold at {v_max}V until {cv_cutoff}C",
            f"Discharge at {dchg_c}C until {v_min}V",
        ]
        experiment = pybamm.Experiment(exp_steps * cycles)
    elif mode in ("charge", "discharge"):
        steps = experiment_config.get("steps", [])
        if not steps:
            raise ValueError("충방전 스텝이 비어있습니다. 스텝을 추가해주세요.")
        cycles = int(experiment_config.get("cycles", 1))
        experiment = pybamm.Experiment(steps * cycles)
    elif mode == "custom":
        steps = experiment_config.get("steps", [])
        if not steps:
            raise ValueError("커스텀 모드: 실험 단계가 비어있습니다.")
        experiment = pybamm.Experiment(steps)
    elif mode == "gitt":
        pattern_type = experiment_config.get("pattern_type", "GITT")
        pulse_c = experiment_config.get("pulse_current", 0.5)
        pulse_t = experiment_config.get("pulse_time", 600)
        rest_t = experiment_config.get("rest_time", 3600)
        repeats = int(experiment_config.get("repeats", 20))
        v_min = experiment_config.get("v_min", 2.5)
        if pattern_type == "GITT":
            step_pair = [
                f"Discharge at {pulse_c}C for {pulse_t}s or until {v_min}V",
                f"Rest for {rest_t}s",
            ]
        else:
            step_pair = [
                f"Discharge at {pulse_c}C for {pulse_t}s or until {v_min}V",
                f"Rest for {rest_t}s",
                f"Charge at {pulse_c}C for {pulse_t}s or until 4.2V",
                f"Rest for {rest_t}s",
            ]
        experiment = pybamm.Experiment(step_pair * repeats)
    else:
        raise ValueError(f"지원하지 않는 모드: {mode}")

    period_str = experiment_config.get("period", "auto")
    if period_str and period_str != "auto":
        try:
            period_sec = float(period_str)
            if period_sec > 0:
                new_steps = []
                for step in experiment.steps:
                    raw = str(step)
                    if "period" not in raw.lower():
                        raw += f" ({period_sec:g} second period)"
                    new_steps.append(raw)
                experiment = pybamm.Experiment(new_steps)
        except (ValueError, TypeError):
            pass

    sim = pybamm.Simulation(model, experiment=experiment, parameter_values=param)
    solution = sim.solve(initial_soc=init_soc)
    return solution, param
