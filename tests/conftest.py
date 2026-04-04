"""BDT 테스트 공통 설정 및 픽스처

테스트 레벨:
  - Level A (headless): GUI 없이 데이터 파싱/로딩/변환 함수만 테스트
  - Level B (smoke-gui): pytest-qt로 실제 앱을 띄우고 버튼 클릭 → 결과 검증

실행:
  pytest tests/ -m "not gui"        # Level A만 (Linux/CI 가능)
  pytest tests/ -m "gui"            # Level B만 (Windows + 실데이터 필요)
  pytest tests/                     # 전체
"""
import os
import sys
from pathlib import Path

import pytest

# ── 프로젝트 루트를 sys.path에 추가 ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATATOOL_DEV = PROJECT_ROOT / "DataTool_dev"
DATA_DIR = PROJECT_ROOT / "data"
DATAPATH_DIR = DATA_DIR / "datapath"
EXP_DATA_DIR = DATA_DIR / "exp_data"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(DATATOOL_DEV))


# ── 마커 등록 ──
def pytest_configure(config):
    config.addinivalue_line("markers", "gui: GUI 필요 테스트 (pytest-qt, Windows)")
    config.addinivalue_line("markers", "slow: 대용량 데이터 또는 오래 걸리는 테스트")


# ══════════════════════════════════════════════
# Level A: 헤드리스 픽스처 — 디렉토리/파일
# ══════════════════════════════════════════════

@pytest.fixture
def datapath_dir():
    """data/datapath/ 디렉토리 경로 반환"""
    return DATAPATH_DIR


@pytest.fixture
def exp_data_dir():
    """data/exp_data/ 디렉토리 경로 반환"""
    return EXP_DATA_DIR


@pytest.fixture
def sample_path_files(datapath_dir):
    """테스트용 경로 파일 3종 경로 반환"""
    return {
        'basic': datapath_dir / "경로저장test.txt",
        'linked': datapath_dir / "경로저장_연결처리_test.txt",
        'linked2': datapath_dir / "경로저장_연결처리_test1.txt",
    }


# ══════════════════════════════════════════════
# 실험 데이터 폴더 픽스처
# ══════════════════════════════════════════════

# ── Toyo 폴더 ──

@pytest.fixture
def toyo_folder(exp_data_dir):
    """Toyo 사이클러 데이터 폴더 (Pattern 폴더 없음)"""
    candidates = [
        exp_data_dir / "250207_250307_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 1-100cyc",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    pytest.skip("Toyo 테스트 데이터 폴더 없음")


@pytest.fixture
def toyo_folder_2nd(exp_data_dir):
    """Toyo Q7M 101-200cyc (연결처리 2번째 경로용)"""
    p = exp_data_dir / "250219_250319_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 101-200cyc"
    if not p.is_dir():
        pytest.skip("Toyo 2nd 폴더 없음")
    return p


@pytest.fixture
def toyo_ch30(toyo_folder):
    """Toyo Q7M 30번 채널 폴더

    실제 폴더명은 '30' (선행 0 없음).
    datapath 파일에서 '030'으로 기재하지만 실제 폴더는 '30'.
    """
    ch = toyo_folder / "30"
    if not ch.is_dir():
        # 대체: 폴더 내 숫자 이름 서브폴더 중 첫 번째
        for d in sorted(toyo_folder.iterdir()):
            if d.is_dir() and d.name.isdigit():
                return d
        pytest.skip("Toyo 채널 폴더 없음")
    return ch


@pytest.fixture
def toyo_ch31(toyo_folder):
    """Toyo Q7M 31번 채널 폴더"""
    ch = toyo_folder / "31"
    if not ch.is_dir():
        pytest.skip("Toyo ch31 폴더 없음")
    return ch


# ── PNE 폴더 ──

@pytest.fixture
def pne_folder(exp_data_dir):
    """PNE 사이클러 데이터 폴더 (Pattern 폴더 있음)"""
    candidates = [
        exp_data_dir / "251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202",
        exp_data_dir / "240821 선행랩 류성택 Gen4pGr mini-ATL-WD-Proto-422mAh-20C-450V-GITT-15도",
    ]
    for c in candidates:
        if c.is_dir() and (c / "Pattern").is_dir():
            return c
    pytest.skip("PNE 테스트 데이터 폴더 없음")


@pytest.fixture
def pne_ch008(pne_folder):
    """PNE Q8 008 채널 폴더"""
    candidates = ["M01Ch008[008]", "008"]
    for name in candidates:
        ch = pne_folder / name
        if ch.is_dir():
            return ch
    # 대체: Pattern 아닌 첫 번째 서브폴더
    for d in sorted(pne_folder.iterdir()):
        if d.is_dir() and d.name != "Pattern":
            return d
    pytest.skip("PNE 채널 폴더 없음")


@pytest.fixture
def pne_continue_pa1_folder(exp_data_dir):
    """PNE PA1 연속저장 DCIR 폴더 (빈 SaveEndData 포함)"""
    p = exp_data_dir / "260226_260228_05_문현규_3885mAh_PA1 연속저장 DCIR"
    if not p.is_dir():
        pytest.skip("PA1 연속저장 폴더 없음")
    return p


@pytest.fixture
def pne_continue_ps_folder(exp_data_dir):
    """PNE PS 연속저장 DCIR 폴더"""
    p = exp_data_dir / "260226_260228_05_문현규_3876mAh_PS 연속저장 DCIR"
    if not p.is_dir():
        pytest.skip("PS 연속저장 폴더 없음")
    return p


@pytest.fixture
def pne_halfcell_folder(exp_data_dir):
    """PNE Half cell 폴더 (소용량, GITT)"""
    candidates = [
        exp_data_dir / "250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half-14pi-GITT-0.1C-T23",
        exp_data_dir / "251218_251230_00_박민희_3-45mAh_M1 ATL Cathode Half T23",
    ]
    for c in candidates:
        if c.is_dir() and (c / "Pattern").is_dir():
            return c
    pytest.skip("Half cell 테스트 데이터 없음")


@pytest.fixture
def pne_dcir_folder(exp_data_dir):
    """PNE SOC별 DCIR 폴더"""
    candidates = [
        exp_data_dir / "240919 선행랩 류성택 Gen4pGr mini-ATL-WD-Proto-422mAh-20C-450V-SOC별DCIR-15도",
        exp_data_dir / "260306_260318_05_현혜정_6330mAh_LWN 25P(after LT100cy) SOC별 DCIR 신규",
    ]
    for c in candidates:
        if c.is_dir() and (c / "Pattern").is_dir():
            return c
    pytest.skip("SOC별 DCIR 테스트 데이터 없음")


# ══════════════════════════════════════════════
# 경로 케이스 픽스처 (7가지)
# ══════════════════════════════════════════════

@pytest.fixture
def path_case_c1(exp_data_dir):
    """C1: Toyo 단일경로, 연결처리 Off

    Q7M 1-100cyc, ch030, 1689mAh
    """
    folder = exp_data_dir / "250207_250307_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 1-100cyc"
    if not folder.is_dir():
        pytest.skip("C1 데이터 없음")
    return {
        'case': 'C1_toyo_single',
        'cycler': 'toyo',
        'link_mode': False,
        'rows': [
            {'name': 'ATL Q7M Inner 2C 상온수명 1-100cyc',
             'path': str(folder), 'channel': '030', 'capacity': '1689'},
        ],
        'capacity': 1689.0,
        'crate': 2.0,
        'cycles': '1 50 100',
    }


@pytest.fixture
def path_case_c2(exp_data_dir):
    """C2: Toyo 연결처리 On

    Q7M 1-100cyc + 101-200cyc 연결, ch030
    """
    f1 = exp_data_dir / "250207_250307_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 1-100cyc"
    f2 = exp_data_dir / "250219_250319_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 101-200cyc"
    if not f1.is_dir() or not f2.is_dir():
        pytest.skip("C2 데이터 없음")
    return {
        'case': 'C2_toyo_linked',
        'cycler': 'toyo',
        'link_mode': True,
        'rows': [
            {'name': 'ATL Q7M Inner 2C 상온수명', 'path': str(f1),
             'channel': '030', 'capacity': '1689'},
            {'name': '', 'path': str(f2), 'channel': '030', 'capacity': ''},
        ],
        'capacity': 1689.0,
        'crate': 2.0,
        'cycles': '1 50 100 150',
    }


@pytest.fixture
def path_case_c3(exp_data_dir):
    """C3: PNE 단일경로, 연결처리 Off

    Q8 ATL RT @1-1202, ch008, 2335mAh
    """
    folder = exp_data_dir / "251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202"
    if not folder.is_dir():
        pytest.skip("C3 데이터 없음")
    return {
        'case': 'C3_pne_single',
        'cycler': 'pne',
        'link_mode': False,
        'rows': [
            {'name': 'Q8 ATL 선상 SEU4 RT @1-1202',
             'path': str(folder), 'channel': '008', 'capacity': '2335'},
        ],
        'capacity': 2335.0,
        'crate': 0.2,
        'cycles': '1 50 100',
    }


@pytest.fixture
def path_case_c4(exp_data_dir):
    """C4: PNE 연결처리 On

    Q8 RT + HT 연결
    """
    f1 = exp_data_dir / "251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202"
    f2 = exp_data_dir / "251029_260129_05_나무늬_2335mAh_Q8 선상 ATL SEU4 HT @1-801"
    if not f1.is_dir() or not f2.is_dir():
        pytest.skip("C4 데이터 없음")
    return {
        'case': 'C4_pne_linked',
        'cycler': 'pne',
        'link_mode': True,
        'rows': [
            {'name': 'Q8 ATL RT', 'path': str(f1),
             'channel': '008', 'capacity': '2335'},
            {'name': '', 'path': str(f2), 'channel': '008', 'capacity': ''},
        ],
        'capacity': 2335.0,
        'crate': 0.2,
        'cycles': '1 50 100',
    }


@pytest.fixture
def path_case_c5(exp_data_dir):
    """C5: PNE 연속저장 (Restore)

    PA1 연속저장 DCIR — continue_confirm_button용
    """
    folder = exp_data_dir / "260226_260228_05_문현규_3885mAh_PA1 연속저장 DCIR"
    if not folder.is_dir():
        pytest.skip("C5 데이터 없음")
    # Restore 있는 채널 찾기
    channels = []
    for d in sorted(folder.iterdir()):
        if d.is_dir() and d.name != "Pattern" and (d / "Restore").is_dir():
            channels.append(d.name)
    if not channels:
        pytest.skip("C5 Restore 채널 없음")
    return {
        'case': 'C5_pne_continue',
        'cycler': 'pne',
        'link_mode': False,
        'rows': [
            {'name': 'PA1 연속저장 DCIR', 'path': str(folder),
             'channel': channels[0].split('[')[-1].rstrip(']') if '[' in channels[0] else channels[0],
             'capacity': '3885'},
        ],
        'capacity': 3885.0,
        'crate': 0.2,
        'cycles': '1 5',
        'restore_channels': channels,
    }


@pytest.fixture
def path_case_c6(exp_data_dir):
    """C6: Half cell (소용량, GITT)

    M2-SDI ca-half GITT, 4.187mAh
    """
    folder = exp_data_dir / "250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half-14pi-GITT-0.1C-T23"
    if not folder.is_dir():
        pytest.skip("C6 데이터 없음")
    # 첫 번째 채널 폴더 찾기
    ch_name = None
    for d in sorted(folder.iterdir()):
        if d.is_dir() and d.name != "Pattern":
            ch_name = d.name
            break
    if not ch_name:
        pytest.skip("C6 채널 없음")
    ch_num = ch_name.split('[')[-1].rstrip(']') if '[' in ch_name else ch_name
    return {
        'case': 'C6_halfcell',
        'cycler': 'pne',
        'link_mode': False,
        'rows': [
            {'name': 'M2-SDI ca-half GITT', 'path': str(folder),
             'channel': ch_num, 'capacity': '4.187'},
        ],
        'capacity': 4.187,
        'crate': 0.1,
        'cycles': '1 2',
    }


@pytest.fixture
def path_case_c7(exp_data_dir):
    """C7: 다채널 (multi-channel)

    Q7M ch030,031 동시 처리
    """
    folder = exp_data_dir / "250207_250307_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 1-100cyc"
    if not folder.is_dir():
        pytest.skip("C7 데이터 없음")
    return {
        'case': 'C7_multichannel',
        'cycler': 'toyo',
        'link_mode': False,
        'rows': [
            {'name': 'ATL Q7M Inner 2C 다채널',
             'path': str(folder), 'channel': '030,031', 'capacity': '1689'},
        ],
        'capacity': 1689.0,
        'crate': 2.0,
        'cycles': '1 50',
    }


# ══════════════════════════════════════════════
# datapath 파일 픽스처
# ══════════════════════════════════════════════

@pytest.fixture
def pathfile_basic_4col(datapath_dir):
    """4열 기본 경로파일 (cyclename/cyclepath/channel/capacity)"""
    p = datapath_dir / "경로저장test.txt"
    if not p.exists():
        pytest.skip("경로저장test.txt 없음")
    return p


@pytest.fixture
def pathfile_linked(datapath_dir):
    """연결처리 경로파일 (#link_mode=1)"""
    p = datapath_dir / "경로저장_연결처리_test.txt"
    if not p.exists():
        pytest.skip("연결처리 경로파일 없음")
    return p


@pytest.fixture
def pathfile_2col(datapath_dir):
    """2열 경로파일 (cyclename/cyclepath만)"""
    p = datapath_dir / "Q7M.txt"
    if not p.exists():
        pytest.skip("2열 경로파일 없음")
    return p


@pytest.fixture
def pathfile_3col(datapath_dir):
    """3열 경로파일 (cyclepath/channel/capacity, 이름 없음)"""
    p = datapath_dir / "Q7M_저장 - 이전3.txt"
    if not p.exists():
        pytest.skip("3열 경로파일 없음")
    return p


@pytest.fixture
def pathfile_q8_linked(datapath_dir):
    """Q8 연결처리 경로파일 (PNE 다채널)"""
    p = datapath_dir / "경로저장_Q8_ATL_RT_최신.txt"
    if not p.exists():
        pytest.skip("Q8 연결처리 파일 없음")
    return p


# ══════════════════════════════════════════════
# Level A: window_class (static method 추출용)
# ══════════════════════════════════════════════

@pytest.fixture
def window_class():
    """WindowClass static method 접근용 (GUI 없이)"""
    try:
        from types import SimpleNamespace
        import re

        proto_path = DATATOOL_DEV / "DataTool_optRCD_proto_.py"
        src = proto_path.read_text(encoding='utf-8-sig')

        ha_match = re.search(
            r'_HEADER_ALIASES\s*=\s*\{([^}]+)\}', src, re.DOTALL)
        ect_match = re.search(
            r'_ECT_HEADER_KEYS\s*=\s*\{([^}]+)\}', src, re.DOTALL)

        header_aliases = eval('{' + ha_match.group(1) + '}') if ha_match else {}
        ect_keys = eval('{' + ect_match.group(1) + '}') if ect_match else set()

        def _detect_path_columns(header_line: str):
            cols = [c.strip().lower() for c in header_line.rstrip('\n\r').split('\t')]
            mapping = {'name': None, 'path': None, 'channel': None, 'capacity': None}
            matched = False
            for idx, col in enumerate(cols):
                key = header_aliases.get(col)
                if key:
                    mapping[key] = idx
                    matched = True
            if mapping['path'] is None:
                mapping['path'] = 0
            return mapping, matched

        def _split_name_path_fallback(text: str):
            text = text.strip()
            if not text:
                return '', ''
            m = re.search(r'(?:(?<=\s)|^)["\'][A-Za-z]:\\', text)
            if m:
                name = text[:m.start()].strip()
                path = text[m.start():].strip().strip('"').strip("'")
                return name, path
            m = re.search(r'(?:(?<=\s)|^)[A-Za-z]:\\', text)
            if m:
                name = text[:m.start()].strip()
                path = text[m.start():].strip().strip('"').strip("'")
                return name, path
            m = re.search(r'(?:(?<=\s)|^)\\\\', text)
            if m:
                name = text[:m.start()].strip()
                path = text[m.start():].strip().strip('"').strip("'")
                return name, path
            return '', text.strip('"').strip("'")

        ns = SimpleNamespace(
            _HEADER_ALIASES=header_aliases,
            _ECT_HEADER_KEYS=ect_keys,
            _detect_path_columns=staticmethod(_detect_path_columns),
            _split_name_path_fallback=staticmethod(_split_name_path_fallback),
        )
        return ns

    except Exception as e:
        pytest.skip(f"WindowClass 로딩 실패: {e}")


# ══════════════════════════════════════════════
# Level A: proto 모듈 직접 접근 픽스처
# ══════════════════════════════════════════════

@pytest.fixture(scope="session")
def proto_module():
    """proto_ 모듈 임포트 (세션 1회, GUI 윈도우 없이 함수만 접근).

    WindowClass 인스턴스화 없이 모듈 레벨 함수만 사용.
    PyQt6 설치 필수 (pyproject.toml 의존성).
    """
    try:
        import importlib.util
        import sys
        from PyQt6.QtWidgets import QApplication

        _app = QApplication.instance() or QApplication(sys.argv[:1])

        spec = importlib.util.spec_from_file_location(
            "bdt_proto", DATATOOL_DEV / "DataTool_optRCD_proto_.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["bdt_proto"] = mod
        spec.loader.exec_module(mod)
        return mod
    except Exception as e:
        pytest.skip(f"proto 모듈 로딩 실패: {e}")


# ══════════════════════════════════════════════
# Level B: GUI 픽스처
# ══════════════════════════════════════════════

@pytest.fixture
def app_window(request):
    """WindowClass 인스턴스 생성 (GUI 스모크 테스트용).

    pytest-qt 필요. 없으면 skip.
    """
    try:
        qtbot = request.getfixturevalue("qtbot")
    except pytest.FixtureLookupError:
        pytest.skip("pytest-qt 미설치. 설치: pip install pytest-qt")

    from PyQt6.QtWidgets import QApplication
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "bdt_proto_gui", DATATOOL_DEV / "DataTool_optRCD_proto_.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    window = mod.WindowClass()
    qtbot.addWidget(window)
    window.show()
    return window
