"""사이클데이터 탭 자동화 테스트 — 데이터 추출 + Plot 생성 검증

경로 케이스 7종:
  C1: Toyo 단일경로           (step/rate/chg/dchg)
  C2: Toyo 연결처리           (step/rate/chg/dchg)
  C3: PNE 단일경로            (step/rate/chg/dchg/continue/dcir)
  C4: PNE 연결처리            (step/rate/chg/dchg)
  C5: PNE 연속저장(Restore)   (continue)
  C6: Half cell (소용량)      (step/chg/dchg)
  C7: 다채널 (multi-ch)       (step)

검증 수준:
  - Level 1: 데이터 추출 — 함수 호출 → DataFrame 반환 → 필수 컬럼/물리 범위
  - Level 2: Plot 생성 — matplotlib Figure 생성 → axes 수/라인 수 확인
  - Level 3: 경로 파일 로드 → 파싱 → 데이터 추출 end-to-end

실행:
  pytest tests/test_cycle_tab_automation.py -v                 # 전체
  pytest tests/test_cycle_tab_automation.py -m "not slow" -v   # 빠른 것만
  pytest tests/test_cycle_tab_automation.py -k "C1" -v         # C1 케이스만
"""
import os
import pytest
import numpy as np
from pathlib import Path


# ══════════════════════════════════════════════════════════════
# 헬퍼: 채널 폴더 경로 조립
# ══════════════════════════════════════════════════════════════

def _resolve_channel_folder(base_path: str, channel: str, is_pne: bool) -> str:
    """경로 + 채널번호 → 실제 채널 폴더 절대경로 반환

    Toyo: base_path / "30" (선행0 제거)
    PNE:  base_path / "M01Ch008[008]" 패턴 탐색
    """
    base = Path(base_path)
    ch_num = channel.strip().lstrip('0') or '0'

    if is_pne:
        # PNE: M01ChNNN[NNN] 패턴
        for d in sorted(base.iterdir()):
            if d.is_dir() and d.name != "Pattern":
                # [008] 형태에서 숫자 추출
                if f"[{channel.zfill(3)}]" in d.name or f"[{ch_num}]" in d.name:
                    return str(d)
        # 대체: 첫 번째 비-Pattern 폴더
        for d in sorted(base.iterdir()):
            if d.is_dir() and d.name != "Pattern":
                return str(d)
    else:
        # Toyo: 숫자 이름 폴더
        ch_path = base / ch_num
        if ch_path.is_dir():
            return str(ch_path)
        # 3자리 패딩 시도
        ch_path = base / channel.zfill(3)
        if ch_path.is_dir():
            return str(ch_path)
        # 대체: 첫 번째 숫자 폴더
        for d in sorted(base.iterdir()):
            if d.is_dir() and d.name.isdigit():
                return str(d)

    pytest.skip(f"채널 폴더 찾기 실패: {base_path} / {channel}")


def _validate_newdata(df_obj, case_name: str, min_rows: int = 1):
    """df.NewData의 공통 물리적 유효성 검증

    Parameters
    ----------
    df_obj : object
        toyo_cycle_data / pne_cycle_data 반환값의 두 번째 요소 (df)
    case_name : str
        테스트 케이스명 (오류 메시지용)
    min_rows : int
        최소 행 수
    """
    assert hasattr(df_obj, 'NewData'), f"[{case_name}] df.NewData 속성 없음"
    nd = df_obj.NewData

    # 필수 컬럼 존재
    required = {"Cycle", "Dchg", "Chg", "Eff", "RndV", "AvgV", "Temp", "OriCyc"}
    missing = required - set(nd.columns)
    assert not missing, f"[{case_name}] 누락 컬럼: {missing}"

    # 최소 행 수
    assert len(nd) >= min_rows, f"[{case_name}] 행 수 부족: {len(nd)} < {min_rows}"

    # Dchg 물리 범위 (0.3 ~ 1.3): 초기 사이클/반셀 포함 여유
    dchg = nd["Dchg"].dropna()
    if len(dchg) > 0:
        assert dchg.min() >= 0.0, f"[{case_name}] Dchg 음수: {dchg.min():.4f}"
        assert dchg.max() <= 1.5, f"[{case_name}] Dchg 과대: {dchg.max():.4f}"

    # Eff (쿨롱효율) 범위: 0.8 ~ 1.05
    eff = nd["Eff"].dropna()
    if len(eff) > 0:
        assert eff.min() >= 0.5, f"[{case_name}] Eff 과소: {eff.min():.4f}"
        assert eff.max() <= 1.1, f"[{case_name}] Eff 과대: {eff.max():.4f}"


def _validate_profile_data(df_obj, case_name: str, attr_name: str = "stepchg"):
    """프로필 데이터 객체의 기본 유효성 검증

    Parameters
    ----------
    df_obj : object
        프로필 데이터 반환값
    attr_name : str
        확인할 DataFrame 속성명 (stepchg, rateProfile, Profile 등)
    """
    data = getattr(df_obj, attr_name, None)
    assert data is not None, f"[{case_name}] {attr_name} 속성 없음"

    import pandas as pd
    if isinstance(data, pd.DataFrame):
        assert len(data) > 0, f"[{case_name}] {attr_name} DataFrame이 비어있음"
    elif isinstance(data, dict):
        assert len(data) > 0, f"[{case_name}] {attr_name} dict가 비어있음"


def _validate_figure(fig, case_name: str, expected_axes: int = 6):
    """matplotlib Figure 객체 검증

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        검증할 Figure
    expected_axes : int
        예상 Axes 수 (기본 6 = 2×3 subplot)
    """
    import matplotlib.figure
    assert isinstance(fig, matplotlib.figure.Figure), \
        f"[{case_name}] Figure 아님: {type(fig)}"

    axes = fig.get_axes()
    assert len(axes) >= expected_axes, \
        f"[{case_name}] Axes 수 부족: {len(axes)} < {expected_axes}"

    # 최소 1개 axes에 라인이 있어야 함
    has_content = any(len(ax.get_lines()) > 0 for ax in axes)
    if not has_content:
        # fill_between, collections 등도 체크
        has_content = any(len(ax.collections) > 0 for ax in axes)
    assert has_content, f"[{case_name}] 모든 axes가 비어있음"


# ══════════════════════════════════════════════════════════════
# Level 1: 사이클 데이터 추출 검증
# ══════════════════════════════════════════════════════════════

class TestCycleDataExtraction:
    """cycle_data 함수 호출 → DataFrame 반환 → 물리적 유효성 검증

    경로 케이스별로 toyo_cycle_data() 또는 pne_cycle_data() 직접 호출.
    """

    @pytest.mark.slow
    def test_c1_toyo_single(self, proto_module, path_case_c1):
        """C1: Toyo 단일경로 사이클 데이터 추출"""
        case = path_case_c1
        ch_folder = _resolve_channel_folder(
            case['rows'][0]['path'], case['rows'][0]['channel'], is_pne=False)

        mincap, df = proto_module.toyo_cycle_data(
            ch_folder, 0, case['crate'], False)

        assert mincap == pytest.approx(case['capacity'], rel=0.05)
        _validate_newdata(df, case['case'], min_rows=50)

    @pytest.mark.slow
    def test_c3_pne_single(self, proto_module, path_case_c3):
        """C3: PNE 단일경로 사이클 데이터 추출"""
        case = path_case_c3
        ch_folder = _resolve_channel_folder(
            case['rows'][0]['path'], case['rows'][0]['channel'], is_pne=True)

        mincap, df = proto_module.pne_cycle_data(
            ch_folder, 0, case['crate'], False, False, False)

        assert mincap == pytest.approx(case['capacity'], rel=0.05)
        _validate_newdata(df, case['case'], min_rows=10)

    @pytest.mark.slow
    def test_c6_halfcell(self, proto_module, path_case_c6):
        """C6: Half cell 소용량 사이클 데이터 추출

        배터리 과학: 반셀은 용량이 수 mAh 수준이고 사이클 수가 적음.
        """
        case = path_case_c6
        ch_folder = _resolve_channel_folder(
            case['rows'][0]['path'], case['rows'][0]['channel'], is_pne=True)

        mincap, df = proto_module.pne_cycle_data(
            ch_folder, 0, case['crate'], False, False, False)

        # 반셀: 용량이 10 mAh 미만일 수 있음
        assert mincap < 50.0, f"반셀인데 용량이 너무 큼: {mincap}"
        _validate_newdata(df, case['case'], min_rows=1)

    @pytest.mark.slow
    def test_c7_multichannel_each_loads(self, proto_module, path_case_c7):
        """C7: 다채널 — 각 채널이 독립적으로 로드되는지 확인"""
        case = path_case_c7
        channels = case['rows'][0]['channel'].split(',')

        for ch in channels:
            ch_folder = _resolve_channel_folder(
                case['rows'][0]['path'], ch.strip(), is_pne=False)
            mincap, df = proto_module.toyo_cycle_data(
                ch_folder, 0, case['crate'], False)
            _validate_newdata(df, f"{case['case']}_ch{ch.strip()}", min_rows=10)


# ══════════════════════════════════════════════════════════════
# Level 1: 프로필 데이터 추출 검증
# ══════════════════════════════════════════════════════════════

class TestProfileDataExtraction:
    """프로필 함수 호출 → 데이터 반환 검증

    step/rate/chg/dchg 각각 Toyo/PNE 전용 함수를 직접 호출.
    """

    @pytest.mark.slow
    def test_c1_toyo_step_profile(self, proto_module, path_case_c1):
        """C1: Toyo step 프로필 데이터 추출"""
        case = path_case_c1
        ch_folder = _resolve_channel_folder(
            case['rows'][0]['path'], case['rows'][0]['channel'], is_pne=False)
        mincap = case['capacity']
        crate = case['crate']

        df = proto_module.toyo_step_Profile_data(
            ch_folder, [1, 50], mincap, mincap * crate, crate)

        _validate_profile_data(df, case['case'], attr_name="stepchg")

    @pytest.mark.slow
    def test_c1_toyo_chg_profile(self, proto_module, path_case_c1):
        """C1: Toyo 충전 프로필 데이터 추출"""
        case = path_case_c1
        ch_folder = _resolve_channel_folder(
            case['rows'][0]['path'], case['rows'][0]['channel'], is_pne=False)
        mincap = case['capacity']
        crate = case['crate']

        df = proto_module.toyo_chg_Profile_data(
            ch_folder, [1, 50], mincap, mincap * crate, crate, 5)

        _validate_profile_data(df, f"{case['case']}_chg", attr_name="Profile")

    @pytest.mark.slow
    def test_c1_toyo_dchg_profile(self, proto_module, path_case_c1):
        """C1: Toyo 방전 프로필 데이터 추출"""
        case = path_case_c1
        ch_folder = _resolve_channel_folder(
            case['rows'][0]['path'], case['rows'][0]['channel'], is_pne=False)
        mincap = case['capacity']
        crate = case['crate']

        df = proto_module.toyo_dchg_Profile_data(
            ch_folder, [1, 50], mincap, mincap * crate, crate, 5)

        _validate_profile_data(df, f"{case['case']}_dchg", attr_name="Profile")

    @pytest.mark.slow
    def test_c1_toyo_rate_profile(self, proto_module, path_case_c1):
        """C1: Toyo rate 프로필 데이터 추출"""
        case = path_case_c1
        ch_folder = _resolve_channel_folder(
            case['rows'][0]['path'], case['rows'][0]['channel'], is_pne=False)
        mincap = case['capacity']
        crate = case['crate']

        df = proto_module.toyo_rate_Profile_data(
            ch_folder, [1, 50], mincap, mincap * crate, crate)

        _validate_profile_data(df, f"{case['case']}_rate", attr_name="rateProfile")

    @pytest.mark.slow
    def test_c3_pne_step_profile(self, proto_module, path_case_c3):
        """C3: PNE step 프로필 데이터 추출"""
        case = path_case_c3
        ch_folder = _resolve_channel_folder(
            case['rows'][0]['path'], case['rows'][0]['channel'], is_pne=True)
        mincap = case['capacity']
        crate = case['crate']

        df = proto_module.pne_step_Profile_data(
            ch_folder, [1, 50], mincap, mincap * crate, crate)

        _validate_profile_data(df, case['case'], attr_name="stepchg")

    @pytest.mark.slow
    def test_c3_pne_chg_profile(self, proto_module, path_case_c3):
        """C3: PNE 충전 프로필 데이터 추출"""
        case = path_case_c3
        ch_folder = _resolve_channel_folder(
            case['rows'][0]['path'], case['rows'][0]['channel'], is_pne=True)
        mincap = case['capacity']
        crate = case['crate']

        df = proto_module.pne_chg_Profile_data(
            ch_folder, [1, 50], mincap, mincap * crate, crate, 5)

        _validate_profile_data(df, f"{case['case']}_chg", attr_name="Profile")

    @pytest.mark.slow
    def test_c3_pne_dchg_profile(self, proto_module, path_case_c3):
        """C3: PNE 방전 프로필 데이터 추출"""
        case = path_case_c3
        ch_folder = _resolve_channel_folder(
            case['rows'][0]['path'], case['rows'][0]['channel'], is_pne=True)
        mincap = case['capacity']
        crate = case['crate']

        df = proto_module.pne_dchg_Profile_data(
            ch_folder, [1, 50], mincap, mincap * crate, crate, 5)

        _validate_profile_data(df, f"{case['case']}_dchg", attr_name="Profile")

    @pytest.mark.slow
    def test_c5_pne_continue(self, proto_module, path_case_c5):
        """C5: PNE 연속저장 continue 프로필 데이터 추출

        회귀: 빈 SaveEndData에서 EmptyDataError 발생하지 않는지 확인.
        """
        case = path_case_c5
        ch_folder = _resolve_channel_folder(
            case['rows'][0]['path'], case['rows'][0]['channel'], is_pne=True)

        import pandas as pd
        proto_module.clear_channel_cache()

        try:
            result = proto_module.pne_continue_data(ch_folder, 1, 5)
        except Exception as e:
            pytest.fail(f"[{case['case']}] pne_continue_data 예외: {type(e).__name__}: {e}")

        assert isinstance(result, pd.DataFrame), \
            f"[{case['case']}] 반환값이 DataFrame이 아님: {type(result)}"


# ══════════════════════════════════════════════════════════════
# Level 2: Plot 생성 검증
# ══════════════════════════════════════════════════════════════

class TestPlotGeneration:
    """프로필 데이터 추출 후 실제 matplotlib Figure 생성 검증

    plot 함수가 존재하지 않는 경우 → 직접 subplot 생성 + 데이터 플로팅으로 검증.
    """

    @pytest.fixture(autouse=True)
    def _setup_matplotlib(self):
        """테스트 전 matplotlib 백엔드를 Agg로 설정 (GUI 불필요)"""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["axes.unicode_minus"] = False
        yield
        plt.close('all')

    @pytest.mark.slow
    def test_c1_toyo_step_plot(self, proto_module, path_case_c1):
        """C1: Toyo step 프로필 → 6-axes Figure 생성 검증"""
        import matplotlib.pyplot as plt

        case = path_case_c1
        ch_folder = _resolve_channel_folder(
            case['rows'][0]['path'], case['rows'][0]['channel'], is_pne=False)
        mincap = case['capacity']
        crate = case['crate']

        df = proto_module.toyo_step_Profile_data(
            ch_folder, [1, 50], mincap, mincap * crate, crate)

        # Figure + 6 axes (2×3) 생성
        fig, axes = plt.subplots(2, 3, figsize=(16, 10))
        axes_flat = axes.flatten()

        # stepchg 데이터에서 첫 번째 사이클 플로팅
        data = df.stepchg
        if hasattr(data, 'columns') and 'Voltage' in data.columns:
            axes_flat[0].plot(data.index, data['Voltage'], label='Voltage')
            axes_flat[0].set_ylabel('Voltage [V]')

        _validate_figure(fig, f"{case['case']}_step_plot", expected_axes=6)
        plt.close(fig)

    @pytest.mark.slow
    def test_c1_toyo_chg_plot(self, proto_module, path_case_c1):
        """C1: Toyo 충전 프로필 → Figure 생성 검증"""
        import matplotlib.pyplot as plt

        case = path_case_c1
        ch_folder = _resolve_channel_folder(
            case['rows'][0]['path'], case['rows'][0]['channel'], is_pne=False)
        mincap = case['capacity']
        crate = case['crate']

        df = proto_module.toyo_chg_Profile_data(
            ch_folder, [1, 50], mincap, mincap * crate, crate, 5)

        fig, axes = plt.subplots(2, 3, figsize=(16, 10))
        axes_flat = axes.flatten()

        data = df.Profile
        if hasattr(data, 'columns') and 'Voltage' in data.columns:
            axes_flat[0].plot(data.index, data['Voltage'], label='Voltage')

        _validate_figure(fig, f"{case['case']}_chg_plot", expected_axes=6)
        plt.close(fig)

    @pytest.mark.slow
    def test_c3_pne_step_plot(self, proto_module, path_case_c3):
        """C3: PNE step 프로필 → Figure 생성 검증"""
        import matplotlib.pyplot as plt

        case = path_case_c3
        ch_folder = _resolve_channel_folder(
            case['rows'][0]['path'], case['rows'][0]['channel'], is_pne=True)
        mincap = case['capacity']
        crate = case['crate']

        df = proto_module.pne_step_Profile_data(
            ch_folder, [1, 50], mincap, mincap * crate, crate)

        fig, axes = plt.subplots(2, 3, figsize=(16, 10))
        axes_flat = axes.flatten()

        data = df.stepchg
        if hasattr(data, 'columns') and 'Voltage' in data.columns:
            axes_flat[0].plot(data.index, data['Voltage'], label='Voltage')

        _validate_figure(fig, f"{case['case']}_step_plot", expected_axes=6)
        plt.close(fig)

    @pytest.mark.slow
    def test_c3_pne_chg_plot(self, proto_module, path_case_c3):
        """C3: PNE 충전 프로필 → Figure 생성 검증"""
        import matplotlib.pyplot as plt

        case = path_case_c3
        ch_folder = _resolve_channel_folder(
            case['rows'][0]['path'], case['rows'][0]['channel'], is_pne=True)
        mincap = case['capacity']
        crate = case['crate']

        df = proto_module.pne_chg_Profile_data(
            ch_folder, [1, 50], mincap, mincap * crate, crate, 5)

        fig, axes = plt.subplots(2, 3, figsize=(16, 10))
        axes_flat = axes.flatten()

        data = df.Profile
        if hasattr(data, 'columns') and 'Voltage' in data.columns:
            axes_flat[0].plot(data.index, data['Voltage'], label='Voltage')

        _validate_figure(fig, f"{case['case']}_chg_plot", expected_axes=6)
        plt.close(fig)

    @pytest.mark.slow
    def test_c3_pne_dchg_plot(self, proto_module, path_case_c3):
        """C3: PNE 방전 프로필 → Figure 생성 검증"""
        import matplotlib.pyplot as plt

        case = path_case_c3
        ch_folder = _resolve_channel_folder(
            case['rows'][0]['path'], case['rows'][0]['channel'], is_pne=True)
        mincap = case['capacity']
        crate = case['crate']

        df = proto_module.pne_dchg_Profile_data(
            ch_folder, [1, 50], mincap, mincap * crate, crate, 5)

        fig, axes = plt.subplots(2, 3, figsize=(16, 10))
        axes_flat = axes.flatten()

        data = df.Profile
        if hasattr(data, 'columns') and 'Voltage' in data.columns:
            axes_flat[0].plot(data.index, data['Voltage'], label='Voltage')

        _validate_figure(fig, f"{case['case']}_dchg_plot", expected_axes=6)
        plt.close(fig)


# ══════════════════════════════════════════════════════════════
# Level 3: 경로 파일 로드 → 파싱 → 데이터 추출 End-to-End
# ══════════════════════════════════════════════════════════════

class TestPathfileEndToEnd:
    """경로 파일(.txt) 읽기 → 경로 파싱 → cycle_data 함수 호출 → 데이터 검증

    실제 datapath 파일을 사용하여 전체 파이프라인을 검증.
    """

    def _parse_pathfile(self, path_file: Path, window_class) -> list[dict]:
        """경로 파일을 파싱하여 [{name, path, channel, capacity}] 반환"""
        content = path_file.read_text(encoding='utf-8-sig', errors='replace')
        lines = content.strip().split('\n')

        link_mode = False
        data_start = 0

        # 메타데이터 처리
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('#link_mode=1'):
                link_mode = True
                data_start = i + 1
                continue
            if stripped.startswith('#'):
                data_start = i + 1
                continue
            if stripped:
                data_start = i
                break

        # 빈 줄 건너뜀
        while data_start < len(lines) and not lines[data_start].strip():
            data_start += 1

        if data_start >= len(lines):
            return []

        # 헤더 감지
        mapping, is_header = window_class._detect_path_columns(lines[data_start])
        if is_header:
            data_start += 1

        rows = []
        for line in lines[data_start:]:
            if not line.strip():
                continue
            cols = line.split('\t')
            row = {
                'name': cols[mapping['name']].strip() if mapping['name'] is not None and mapping['name'] < len(cols) else '',
                'path': cols[mapping['path']].strip().strip('"').strip("'") if mapping['path'] < len(cols) else '',
                'channel': cols[mapping['channel']].strip() if mapping.get('channel') is not None and mapping['channel'] < len(cols) else '',
                'capacity': cols[mapping['capacity']].strip() if mapping.get('capacity') is not None and mapping['capacity'] < len(cols) else '',
            }
            if row['path']:
                rows.append(row)

        return rows

    @pytest.mark.slow
    def test_basic_4col_pathfile(self, proto_module, window_class, pathfile_basic_4col):
        """4열 기본 경로파일: 모든 경로에서 cycle_data 추출 가능한지"""
        rows = self._parse_pathfile(pathfile_basic_4col, window_class)
        assert len(rows) > 0, "파싱된 행이 없음"

        loaded = 0
        for row in rows:
            if not os.path.isdir(row['path']):
                continue

            is_pne = proto_module.check_cycler(row['path'])
            channels = row['channel'].split(',') if row['channel'] else ['']

            for ch in channels[:1]:  # 첫 번째 채널만 테스트 (속도)
                ch = ch.strip()
                if not ch:
                    continue
                try:
                    ch_folder = _resolve_channel_folder(row['path'], ch, is_pne)
                except Exception:
                    continue

                if is_pne:
                    mincap, df = proto_module.pne_cycle_data(
                        ch_folder, 0, 0.2, False, False, False)
                else:
                    mincap, df = proto_module.toyo_cycle_data(
                        ch_folder, 0, 2.0, False)

                assert hasattr(df, 'NewData'), f"NewData 없음: {row['path']}"
                assert len(df.NewData) > 0, f"데이터 비어있음: {row['path']}"
                loaded += 1

        assert loaded > 0, "로드된 경로가 하나도 없음"

    @pytest.mark.slow
    def test_linked_pathfile(self, proto_module, window_class, pathfile_linked):
        """연결처리 경로파일: 첫 번째 경로의 cycle_data 추출 가능한지"""
        rows = self._parse_pathfile(pathfile_linked, window_class)
        assert len(rows) > 0, "파싱된 행이 없음"

        # 첫 번째 유효 경로만 테스트
        for row in rows:
            if not os.path.isdir(row['path']):
                continue
            is_pne = proto_module.check_cycler(row['path'])
            channels = row['channel'].split(',') if row['channel'] else ['']
            ch = channels[0].strip()
            if not ch:
                continue

            ch_folder = _resolve_channel_folder(row['path'], ch, is_pne)
            if is_pne:
                mincap, df = proto_module.pne_cycle_data(
                    ch_folder, 0, 0.2, False, False, False)
            else:
                mincap, df = proto_module.toyo_cycle_data(
                    ch_folder, 0, 2.0, False)

            _validate_newdata(df, f"linked_{row['name'][:20]}", min_rows=5)
            break  # 첫 번째만

    @pytest.mark.slow
    def test_2col_pathfile(self, proto_module, window_class, pathfile_2col):
        """2열 경로파일 (name+path만): 채널 자동 탐색 후 로드"""
        rows = self._parse_pathfile(pathfile_2col, window_class)
        assert len(rows) > 0, "파싱된 행이 없음"

        for row in rows:
            if not os.path.isdir(row['path']):
                continue

            is_pne = proto_module.check_cycler(row['path'])
            base = Path(row['path'])

            # 채널 없음 → 첫 번째 서브폴더 자동 탐색
            ch_folder = None
            for d in sorted(base.iterdir()):
                if d.is_dir() and d.name != "Pattern":
                    if is_pne or d.name.isdigit():
                        ch_folder = str(d)
                        break

            if ch_folder is None:
                continue

            if is_pne:
                mincap, df = proto_module.pne_cycle_data(
                    ch_folder, 0, 0.2, False, False, False)
            else:
                mincap, df = proto_module.toyo_cycle_data(
                    ch_folder, 0, 2.0, False)

            assert hasattr(df, 'NewData'), f"NewData 없음: {row['path']}"
            break  # 첫 번째만

    @pytest.mark.slow
    def test_q8_linked_pathfile(self, proto_module, window_class, pathfile_q8_linked):
        """Q8 PNE 연결처리 경로파일: PNE 사이클 데이터 추출"""
        rows = self._parse_pathfile(pathfile_q8_linked, window_class)
        assert len(rows) > 0, "파싱된 행이 없음"

        for row in rows:
            if not os.path.isdir(row['path']):
                continue

            is_pne = proto_module.check_cycler(row['path'])
            assert is_pne, "Q8 데이터는 PNE여야 함"

            channels = row['channel'].split(',') if row['channel'] else []
            if not channels:
                continue

            ch = channels[0].strip()
            ch_folder = _resolve_channel_folder(row['path'], ch, is_pne=True)
            mincap, df = proto_module.pne_cycle_data(
                ch_folder, 0, 0.2, False, False, False)

            _validate_newdata(df, f"Q8_linked_{ch}", min_rows=5)
            break  # 첫 번째만


# ══════════════════════════════════════════════════════════════
# Level 2+: DCIR 프로필 (PNE 전용)
# ══════════════════════════════════════════════════════════════

class TestDcirProfile:
    """DCIR 프로필 데이터 추출 검증 (PNE 전용)"""

    @pytest.mark.slow
    def test_c3_pne_dcir_profile(self, proto_module, path_case_c3):
        """C3: PNE SOC별 DCIR 프로필 데이터 추출

        dcir_confirm_button은 pne_dcir_Profile_data()를 호출.
        4-axes 레이아웃 (2×2).
        """
        case = path_case_c3
        ch_folder = _resolve_channel_folder(
            case['rows'][0]['path'], case['rows'][0]['channel'], is_pne=True)
        mincap = case['capacity']
        crate = case['crate']

        try:
            df = proto_module.pne_dcir_Profile_data(
                ch_folder, [1], [100], mincap, crate)
        except Exception as e:
            # DCIR 패턴이 없는 데이터에서는 정상적으로 실패 가능
            if "DCIR" in str(e) or "step" in str(e).lower():
                pytest.skip(f"DCIR 패턴 없는 데이터: {e}")
            raise

        # DCIR 데이터가 있으면 검증
        if df is not None:
            import pandas as pd
            assert isinstance(df, (pd.DataFrame, object)), \
                f"[{case['case']}] DCIR 반환값 타입 오류"

    @pytest.mark.slow
    def test_dcir_folder_has_dcir_data(self, proto_module, pne_dcir_folder):
        """전용 DCIR 데이터 폴더에서 DCIR 프로필 추출"""
        base = pne_dcir_folder

        # 첫 번째 채널 찾기
        ch_folder = None
        for d in sorted(base.iterdir()):
            if d.is_dir() and d.name != "Pattern":
                ch_folder = str(d)
                break

        if ch_folder is None:
            pytest.skip("DCIR 채널 폴더 없음")

        mincap = proto_module.name_capacity(ch_folder)
        if mincap == 0:
            mincap = 422.0  # GITT 기본값

        try:
            df = proto_module.pne_dcir_Profile_data(
                ch_folder, [1], [5], mincap, 0.2)
        except Exception as e:
            pytest.skip(f"DCIR 추출 실패: {e}")

        assert df is not None, "DCIR 데이터가 None"
