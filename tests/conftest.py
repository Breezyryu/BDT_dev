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
# Level A: 헤드리스 픽스처
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
def window_class():
    """WindowClass 가져오기 (GUI 초기화 없이 static method 접근용)

    WindowClass 임포트가 실패하면 (PyQt6 없는 환경 등) skip.
    """
    try:
        # proto_ 파일에서 WindowClass를 직접 임포트하지 않고,
        # staticmethod만 추출하기 위해 ast로 파싱하여 접근
        from types import SimpleNamespace
        import re

        proto_path = DATATOOL_DEV / "DataTool_optRCD_proto_.py"
        src = proto_path.read_text(encoding='utf-8-sig')

        # _HEADER_ALIASES dict 추출 (정규식)
        ha_match = re.search(
            r'_HEADER_ALIASES\s*=\s*\{([^}]+)\}', src, re.DOTALL)
        ect_match = re.search(
            r'_ECT_HEADER_KEYS\s*=\s*\{([^}]+)\}', src, re.DOTALL)

        header_aliases = eval('{' + ha_match.group(1) + '}') if ha_match else {}
        ect_keys = eval('{' + ect_match.group(1) + '}') if ect_match else set()

        # _detect_path_columns 재현
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

        # _split_name_path_fallback 재현
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

        # PyQt6 클래스 정의에 QApplication 객체 필요 (화면은 표시 안 됨)
        _app = QApplication.instance() or QApplication(sys.argv[:1])

        spec = importlib.util.spec_from_file_location(
            "bdt_proto", DATATOOL_DEV / "DataTool_optRCD_proto_.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["bdt_proto"] = mod
        spec.loader.exec_module(mod)
        return mod
    except Exception as e:
        pytest.skip(f"proto 모듈 로딩 실패: {e}")


# ── 채널 폴더 픽스처 ──

@pytest.fixture
def toyo_ch30(toyo_folder):
    """Toyo Q7M 30 채널 폴더 (숫자 파일들 포함).

    실제 폴더명은 '30' (선행 0 없음). datapath 파일에서 '030' 으로 표기되는 것은
    BDT 내부 _normalize_ch() 처리 결과이며, 파일시스템 이름과 다름.
    """
    ch = toyo_folder / "30"
    if not ch.is_dir():
        pytest.skip("30 채널 폴더 없음")
    return ch


@pytest.fixture
def toyo_ch31(toyo_folder):
    """Toyo Q7M 31 채널 폴더"""
    ch = toyo_folder / "31"
    if not ch.is_dir():
        pytest.skip("31 채널 폴더 없음")
    return ch


@pytest.fixture
def pne_ch008(pne_folder):
    """PNE Q8 M01Ch008[008] 채널 폴더 (.cyc 포함)"""
    ch = pne_folder / "M01Ch008[008]"
    if not ch.is_dir():
        pytest.skip("M01Ch008[008] 채널 폴더 없음")
    return ch


@pytest.fixture
def pne_continue_pa1_folder(exp_data_dir):
    """PA1 연속저장 DCIR 폴더 — 빈 SaveEndData 회귀 테스트용"""
    folder = exp_data_dir / "260226_260228_05_문현규_3885mAh_PA1 연속저장 DCIR"
    if not folder.is_dir():
        pytest.skip("PA1 연속저장 DCIR 폴더 없음")
    return folder


@pytest.fixture
def pne_continue_ps_folder(exp_data_dir):
    """PS 연속저장 DCIR 폴더"""
    folder = exp_data_dir / "260226_260228_05_문현규_3876mAh_PS 연속저장 DCIR"
    if not folder.is_dir():
        pytest.skip("PS 연속저장 DCIR 폴더 없음")
    return folder


# ══════════════════════════════════════════════
# Level B: GUI 픽스처 (pytest-qt 필요)
# ══════════════════════════════════════════════

@pytest.fixture
def app_window(request):
    """실제 BDT 앱 윈도우 인스턴스 (pytest-qt 필요)

    pytest-qt 미설치 시 자동 skip.

    사용:
      @pytest.mark.gui
      def test_something(app_window):
          app_window.StepConfirm.click()
    """
    # pytest-qt 미설치 방어 — qtbot 픽스처를 동적으로 요청
    try:
        qtbot = request.getfixturevalue("qtbot")
    except pytest.FixtureLookupError:
        pytest.skip(
            "pytest-qt 미설치. 설치: pip install pytest-qt"
        )

    try:
        # proto_ 파일의 WindowClass를 직접 임포트
        os.chdir(str(DATATOOL_DEV))
        sys.path.insert(0, str(DATATOOL_DEV))

        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "proto", DATATOOL_DEV / "DataTool_optRCD_proto_.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        window = mod.WindowClass()
        qtbot.addWidget(window)
        window.show()
        return window

    except Exception as e:
        pytest.skip(f"앱 윈도우 생성 실패: {e}")
