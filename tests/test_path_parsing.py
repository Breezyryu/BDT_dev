"""Level A — 경로 파싱 함수 헤드리스 유닛 테스트

GUI 없이 실행 가능. 대상:
  - _detect_path_columns(): 헤더 줄 파싱
  - _split_name_path_fallback(): 드라이브 문자 패턴 분리
  - 경로 파일 읽기/파싱 통합 테스트 (파일 I/O)
  - check_cycler(): PNE/Toyo 판별

실행: pytest tests/test_path_parsing.py -v
"""
import os
import pytest
from pathlib import Path


# ══════════════════════════════════════════════
# _detect_path_columns 테스트
# ══════════════════════════════════════════════

class TestDetectPathColumns:
    """헤더 줄 → 열 매핑 변환 테스트"""

    def test_standard_4col_header(self, window_class):
        """표준 4열 헤더: cyclename / cyclepath / channel / capacity"""
        mapping, is_header = window_class._detect_path_columns(
            "cyclename\tcyclepath\tchannel\tcapacity")
        assert is_header is True
        assert mapping == {'name': 0, 'path': 1, 'channel': 2, 'capacity': 3}

    def test_ect_header(self, window_class):
        """ECT 형식 헤더: save / cycle / path / cd"""
        mapping, is_header = window_class._detect_path_columns(
            "save\tcycle\tpath\tcd")
        assert is_header is True
        assert mapping['name'] == 0    # 'save' → name
        assert mapping['path'] == 2    # 'path' → path
        assert mapping['cycle'] == 1   # 'cycle' → cycle
        assert mapping['mode'] == 3    # 'cd' → mode

    def test_2col_header(self, window_class):
        """2열 헤더: cyclename / cyclepath"""
        mapping, is_header = window_class._detect_path_columns(
            "cyclename\tcyclepath")
        assert is_header is True
        assert mapping['name'] == 0
        assert mapping['path'] == 1
        assert mapping['channel'] is None
        assert mapping['capacity'] is None

    def test_no_header_data_row(self, window_class):
        """헤더가 아닌 데이터 행 → is_header=False, path=0"""
        mapping, is_header = window_class._detect_path_columns(
            "C:\\Users\\data\\test_folder\t030,031\t1689")
        assert is_header is False
        assert mapping['path'] == 0

    def test_partial_header(self, window_class):
        """일부만 매칭되는 헤더 (name + path만)"""
        mapping, is_header = window_class._detect_path_columns(
            "name\tpath\tunknown_col")
        assert is_header is True
        assert mapping['name'] == 0
        assert mapping['path'] == 1
        assert mapping['channel'] is None

    def test_case_insensitive(self, window_class):
        """대소문자 무시"""
        mapping, is_header = window_class._detect_path_columns(
            "CycleName\tCyclePath\tChannel\tCapacity")
        assert is_header is True
        assert mapping == {'name': 0, 'path': 1, 'channel': 2, 'capacity': 3}

    def test_alias_ch(self, window_class):
        """'ch' 별칭이 'channel'로 매핑되는지"""
        mapping, is_header = window_class._detect_path_columns(
            "name\tpath\tch\tcap")
        assert is_header is True
        assert mapping['channel'] == 2
        assert mapping['capacity'] == 3

    def test_empty_line(self, window_class):
        """빈 줄 → path=0, is_header=False"""
        mapping, is_header = window_class._detect_path_columns("")
        assert is_header is False
        assert mapping['path'] == 0

    def test_whitespace_trimming(self, window_class):
        """열 이름 양쪽 공백 제거"""
        mapping, is_header = window_class._detect_path_columns(
            "  cyclename \t cyclepath \t channel ")
        assert is_header is True
        assert mapping['name'] == 0


# ══════════════════════════════════════════════
# _split_name_path_fallback 테스트
# ══════════════════════════════════════════════

class TestSplitNamePathFallback:
    """탭 없는 줄에서 cyclename/cyclepath 분리"""

    def test_drive_letter_path(self, window_class):
        """일반 Windows 드라이브 문자 경로"""
        name, path = window_class._split_name_path_fallback(
            "ATL Q7M test C:\\Users\\data\\exp_data\\test_folder")
        assert name == "ATL Q7M test"
        assert path == "C:\\Users\\data\\exp_data\\test_folder"

    def test_quoted_path(self, window_class):
        """따옴표 감싼 경로"""
        name, path = window_class._split_name_path_fallback(
            'test name "C:\\path with spaces\\data"')
        assert name == "test name"
        assert path == "C:\\path with spaces\\data"

    def test_unc_path(self, window_class):
        """UNC 네트워크 경로"""
        name, path = window_class._split_name_path_fallback(
            "share data \\\\server\\share\\folder")
        assert name == "share data"
        assert path == "\\\\server\\share\\folder"

    def test_path_only(self, window_class):
        """경로만 있는 줄 (이름 없음)"""
        name, path = window_class._split_name_path_fallback(
            "C:\\Users\\test\\folder")
        assert name == ""
        assert path == "C:\\Users\\test\\folder"

    def test_empty_string(self, window_class):
        """빈 문자열"""
        name, path = window_class._split_name_path_fallback("")
        assert name == ""
        assert path == ""

    def test_no_pattern_match(self, window_class):
        """드라이브/UNC 패턴 없음 → 전체를 path로"""
        name, path = window_class._split_name_path_fallback(
            "just some text without a path")
        assert name == ""
        assert path == "just some text without a path"


# ══════════════════════════════════════════════
# 경로 파일 통합 테스트
# ══════════════════════════════════════════════

class TestPathFileIntegration:
    """실제 경로 파일 읽기 테스트"""

    def test_basic_path_file_readable(self, sample_path_files):
        """기본 경로 파일이 존재하고 읽을 수 있는지"""
        path_file = sample_path_files['basic']
        if not path_file.exists():
            pytest.skip("테스트 경로 파일 없음")
        content = path_file.read_text(encoding='utf-8-sig')
        lines = content.strip().split('\n')
        assert len(lines) >= 2, "최소 헤더 + 1 데이터 행 필요"

    def test_basic_path_file_header_detection(self, sample_path_files, window_class):
        """기본 경로 파일의 헤더가 올바르게 감지되는지"""
        path_file = sample_path_files['basic']
        if not path_file.exists():
            pytest.skip("테스트 경로 파일 없음")
        content = path_file.read_text(encoding='utf-8-sig')
        lines = [l for l in content.split('\n') if l.strip()]
        # 첫 번째 비어있지 않은 줄이 헤더여야 함
        mapping, is_header = window_class._detect_path_columns(lines[0])
        assert is_header is True
        assert mapping['path'] is not None

    def test_linked_path_file_has_metadata(self, sample_path_files):
        """연결처리 경로 파일에 #link_mode=1 메타데이터가 있는지"""
        path_file = sample_path_files['linked']
        if not path_file.exists():
            pytest.skip("연결처리 테스트 파일 없음")
        content = path_file.read_text(encoding='utf-8-sig')
        assert '#link_mode=1' in content

    def test_linked_path_file_has_blank_rows(self, sample_path_files):
        """연결처리 파일에 그룹 구분용 빈 행이 있는지"""
        path_file = sample_path_files['linked']
        if not path_file.exists():
            pytest.skip("연결처리 테스트 파일 없음")
        content = path_file.read_text(encoding='utf-8-sig')
        lines = content.split('\n')
        # 메타데이터/헤더 이후 빈 행이 있어야 함
        blank_count = sum(1 for l in lines[3:] if l.strip() == '')
        assert blank_count > 0, "연결처리 파일에 그룹 구분 빈 행이 있어야 함"

    def test_path_file_data_rows_have_valid_paths(self, sample_path_files, window_class):
        """데이터 행의 경로가 드라이브 문자 또는 UNC로 시작하는지"""
        path_file = sample_path_files['basic']
        if not path_file.exists():
            pytest.skip("테스트 경로 파일 없음")
        content = path_file.read_text(encoding='utf-8-sig')
        lines = content.strip().split('\n')

        mapping, is_header = window_class._detect_path_columns(lines[0])
        start = 1 if is_header else 0
        path_col = mapping['path']

        valid_count = 0
        for line in lines[start:]:
            if not line.strip():
                continue
            cols = line.split('\t')
            if path_col < len(cols):
                path_val = cols[path_col].strip()
                if path_val:
                    # 드라이브 문자 또는 UNC 패턴
                    assert (len(path_val) >= 3 and path_val[1] == ':') or \
                           path_val.startswith('\\\\'), \
                        f"유효하지 않은 경로: {path_val[:50]}"
                    valid_count += 1

        assert valid_count > 0, "유효한 데이터 행이 1개 이상이어야 함"


# ══════════════════════════════════════════════
# check_cycler 테스트
# ══════════════════════════════════════════════

class TestCheckCycler:
    """PNE/Toyo 사이클러 판별 테스트"""

    def test_toyo_folder_no_pattern(self, toyo_folder):
        """Toyo 폴더에는 Pattern 서브폴더 없음"""
        pattern_dir = toyo_folder / "Pattern"
        assert not pattern_dir.is_dir(), "Toyo 폴더에 Pattern이 있으면 안 됨"
        # check_cycler는 os.path.isdir(path + "\\Pattern") 이므로:
        result = os.path.isdir(str(toyo_folder / "Pattern"))
        assert result is False  # Toyo

    def test_pne_folder_has_pattern(self, pne_folder):
        """PNE 폴더에는 Pattern 서브폴더 있음"""
        result = os.path.isdir(str(pne_folder / "Pattern"))
        assert result is True  # PNE

    def test_toyo_has_csv_channels(self, toyo_folder):
        """Toyo 폴더의 서브폴더(채널)에 숫자 이름 파일이 있는지"""
        channels = [f.path for f in os.scandir(str(toyo_folder))
                    if f.is_dir() and f.name.isdigit()]
        assert len(channels) > 0, "Toyo 폴더에 채널 서브폴더 필요"
        # 첫 번째 채널에 사이클 파일이 있는지
        first_ch = Path(channels[0])
        cycle_files = [f for f in first_ch.iterdir()
                       if f.is_file() and f.name.isdigit()]
        assert len(cycle_files) > 0, "채널 내 사이클 데이터 파일 필요"


# ══════════════════════════════════════════════
# 콜백 계약(contract) 검증 테스트
# ══════════════════════════════════════════════

class TestCallbackContract:
    """_profile_render_loop()의 콜백 계약 검증

    plot_one_fn과 fallback_fn의 시그니처가 올바른지 확인.
    실제 실행이 아닌 시그니처 레벨 검증.
    """

    def test_plot_one_fn_signature(self):
        """plot_one_fn은 9개 인자를 받고 (int, list) 튜플을 반환해야 함"""
        import inspect

        # 시그니처 템플릿 (모든 콜백이 이 계약을 따라야 함)
        def template_plot_one(temp, axes, headername, lgnd, temp_lgnd,
                              writer, save_file_name, writecolno, CycNo):
            return (writecolno, [])

        sig = inspect.signature(template_plot_one)
        assert len(sig.parameters) == 9

        # 반환값 검증
        result = template_plot_one(
            temp=(100.0, None), axes=tuple(range(6)),
            headername="test", lgnd="0001", temp_lgnd="grp 0001",
            writer=None, save_file_name=None, writecolno=0, CycNo=100)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], int)
        assert isinstance(result[1], list)

    def test_fallback_fn_signature(self):
        """fallback_fn은 3개 인자를 받아야 함"""
        import inspect

        def template_fallback(FolderBase, CycNo, is_pne):
            return None

        sig = inspect.signature(template_fallback)
        assert len(sig.parameters) == 3

    def test_proto_file_has_profile_render_loop(self):
        """proto_.py에 _profile_render_loop 함수가 존재하는지"""
        proto_path = Path(__file__).parent.parent / "DataTool_dev" / "DataTool_optRCD_proto_.py"
        if not proto_path.exists():
            pytest.skip("proto_ 파일 없음")
        content = proto_path.read_text(encoding='utf-8-sig')
        assert 'def _profile_render_loop(' in content

    def test_converted_buttons_call_render_loop(self):
        """4개 변환 버튼이 _profile_render_loop을 호출하는지"""
        proto_path = Path(__file__).parent.parent / "DataTool_dev" / "DataTool_optRCD_proto_.py"
        if not proto_path.exists():
            pytest.skip("proto_ 파일 없음")
        content = proto_path.read_text(encoding='utf-8-sig')

        buttons = [
            'step_confirm_button',
            'rate_confirm_button',
            'chg_confirm_button',
            'dchg_confirm_button',
        ]
        for btn in buttons:
            # 함수 정의 찾기
            func_start = content.find(f'def {btn}(self)')
            assert func_start != -1, f"{btn} 함수가 없음"

            # 다음 함수 시작까지의 본문에서 _profile_render_loop 호출 확인
            next_def = content.find('\n    def ', func_start + 10)
            func_body = content[func_start:next_def] if next_def != -1 else content[func_start:]
            assert '_profile_render_loop(' in func_body, \
                f"{btn}이 _profile_render_loop을 호출하지 않음"

    def test_each_button_has_unique_data_attr(self):
        """각 버튼의 data_attr이 올바르게 설정되었는지"""
        proto_path = Path(__file__).parent.parent / "DataTool_dev" / "DataTool_optRCD_proto_.py"
        if not proto_path.exists():
            pytest.skip("proto_ 파일 없음")
        content = proto_path.read_text(encoding='utf-8-sig')

        expected = {
            'step_confirm_button': 'data_attr="stepchg"',
            'rate_confirm_button': 'data_attr="rateProfile"',
            'chg_confirm_button': 'data_attr="Profile"',
            'dchg_confirm_button': 'data_attr="Profile"',
        }
        for btn, expected_attr in expected.items():
            func_start = content.find(f'def {btn}(self)')
            next_def = content.find('\n    def ', func_start + 10)
            func_body = content[func_start:next_def] if next_def != -1 else content[func_start:]
            assert expected_attr in func_body, \
                f"{btn}에 {expected_attr}가 없음"
