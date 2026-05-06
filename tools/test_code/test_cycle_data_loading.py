"""Level A + Slow — 사이클 데이터 로딩 통합 테스트

테스트 대상 함수 (모두 proto_ 모듈 레벨 순수 함수):
  - name_capacity()        : 폴더명에서 용량(mAh) 추출
  - check_cycler()         : PNE/Toyo 판별
  - toyo_cycle_data()      : Toyo CSV → df.NewData
  - pne_cycle_data()       : PNE .cyc/CSV → df.NewData
  - 데이터 구조 검증        : 반환 DataFrame의 물리적 유효성

마커:
  - (없음)      : 빠른 단위 테스트 (headless, < 1 s)
  - @slow       : 실제 데이터 I/O 포함 테스트 (수 초 소요)

실행:
  pytest tests/test_cycle_data_loading.py -v                 # 전체
  pytest tests/test_cycle_data_loading.py -m "not slow" -v   # 빠른 것만
"""
import os
import pytest
from pathlib import Path


# ══════════════════════════════════════════════════
# name_capacity 테스트
# ══════════════════════════════════════════════════

class TestNameCapacity:
    """name_capacity() : 폴더명 → 용량(float) 추출"""

    def test_1689mah_in_path(self, proto_module):
        """Toyo Q7M 폴더명에서 1689.0 mAh 추출"""
        path = (r"C:\Users\Ryu\battery\python\BDT_dev\data\exp_data"
                r"\250207_250307_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 1-100cyc"
                r"\030")
        result = proto_module.name_capacity(path)
        assert result == 1689.0

    def test_3885mah_in_path(self, proto_module):
        """PA1 연속저장 폴더명에서 3885.0 mAh 추출"""
        path = (r"C:\data\exp_data"
                r"\260226_260228_05_문현규_3885mAh_PA1 연속저장 DCIR"
                r"\M01Ch015[015]")
        result = proto_module.name_capacity(path)
        assert result == 3885.0

    def test_2335mah_in_path(self, proto_module):
        """Q8 PNE 폴더명에서 2335.0 mAh 추출"""
        path = (r"C:\data\251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202"
                r"\M01Ch008[008]")
        result = proto_module.name_capacity(path)
        assert result == 2335.0

    def test_decimal_capacity(self, proto_module):
        """소수점 용량: 4.187mAh 추출 (GITT 하프셀)"""
        path = r"C:\data\250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half"
        result = proto_module.name_capacity(path)
        assert result == pytest.approx(4.187, rel=1e-3)

    def test_no_mah_in_path(self, proto_module):
        """mAh 없는 경로 → 0 반환"""
        result = proto_module.name_capacity(r"C:\data\test_folder\channel")
        assert result == 0

    def test_list_input_returns_zero(self, proto_module):
        """list 타입 입력 → 0 반환 (다중 경로 케이스)"""
        result = proto_module.name_capacity(["path1", "path2"])
        assert result == 0


# ══════════════════════════════════════════════════
# check_cycler 테스트 (실제 폴더 사용)
# ══════════════════════════════════════════════════

class TestCheckCyclerWithProto:
    """check_cycler() : proto 모듈 함수로 PNE/Toyo 판별"""

    def test_toyo_returns_false(self, proto_module, toyo_folder):
        """Toyo 폴더 → Pattern 없음 → False"""
        result = proto_module.check_cycler(str(toyo_folder))
        assert result is False

    def test_pne_returns_true(self, proto_module, pne_folder):
        """PNE 폴더 → Pattern 있음 → True"""
        result = proto_module.check_cycler(str(pne_folder))
        assert result is True

    def test_pne_continue_returns_true(self, proto_module, pne_continue_pa1_folder):
        """PNE 연속저장 폴더 → Pattern 있음 → True"""
        result = proto_module.check_cycler(str(pne_continue_pa1_folder))
        assert result is True

    def test_nonexistent_folder(self, proto_module):
        """존재하지 않는 폴더 → False (os.path.isdir 기반)"""
        result = proto_module.check_cycler(r"C:\nonexistent\fake_folder")
        assert result is False


# ══════════════════════════════════════════════════
# toyo_cycle_data 테스트 (실제 데이터 I/O)
# ══════════════════════════════════════════════════

class TestToyoCycleData:
    """toyo_cycle_data() : Toyo CSV → [mincapacity, df] 반환 검증"""

    # df.NewData의 필수 컬럼 (database.instructions.md 기준)
    REQUIRED_COLS = {"Cycle", "Dchg", "Chg", "Eff", "Eff2",
                     "RndV", "AvgV", "DchgEng", "Temp", "OriCyc"}

    @pytest.mark.slow
    def test_returns_list_of_two(self, proto_module, toyo_ch30):
        """반환값이 [mincapacity, df] 형식인지 확인"""
        result = proto_module.toyo_cycle_data(str(toyo_ch30), 0, 2.0, False)
        assert isinstance(result, list)
        assert len(result) == 2

    @pytest.mark.slow
    def test_mincapacity_is_1689(self, proto_module, toyo_ch30):
        """폴더명에서 용량 자동 감지: 1689 mAh"""
        mincap, _ = proto_module.toyo_cycle_data(str(toyo_ch30), 0, 2.0, False)
        assert mincap == pytest.approx(1689.0, rel=0.01)

    @pytest.mark.slow
    def test_newdata_has_required_columns(self, proto_module, toyo_ch30):
        """df.NewData에 필수 컬럼 모두 존재하는지 확인"""
        _, df = proto_module.toyo_cycle_data(str(toyo_ch30), 0, 2.0, False)
        assert hasattr(df, "NewData"), "df.NewData 속성이 없음"
        missing = self.REQUIRED_COLS - set(df.NewData.columns)
        assert not missing, f"누락 컬럼: {missing}"

    @pytest.mark.slow
    def test_newdata_has_rows(self, proto_module, toyo_ch30):
        """df.NewData 행 수가 0보다 큰지 확인 (최소 50 사이클 기대)"""
        _, df = proto_module.toyo_cycle_data(str(toyo_ch30), 0, 2.0, False)
        assert len(df.NewData) >= 50, f"사이클 수 부족: {len(df.NewData)}"

    @pytest.mark.slow
    def test_dchg_ratio_physical_range(self, proto_module, toyo_ch30):
        """방전 용량 비율이 물리적 범위 [0.5, 1.2] 이내인지 확인

        배터리 과학: 방전용량비 < 0.5 는 불량, > 1.2 는 측정 오류.
        """
        _, df = proto_module.toyo_cycle_data(str(toyo_ch30), 0, 2.0, False)
        dchg = df.NewData["Dchg"].dropna()
        assert dchg.between(0.5, 1.2).all(), (
            f"물리적 범위 벗어남: min={dchg.min():.3f}, max={dchg.max():.3f}")

    @pytest.mark.slow
    def test_cycle_index_is_sequential(self, proto_module, toyo_ch30):
        """Cycle 컬럼이 1부터 순차적으로 증가하는지 확인"""
        _, df = proto_module.toyo_cycle_data(str(toyo_ch30), 0, 2.0, False)
        cycles = df.NewData["Cycle"].tolist()
        assert cycles == list(range(1, len(cycles) + 1)), "Cycle 번호가 순차적이지 않음"

    @pytest.mark.slow
    def test_ch31_also_loads(self, proto_module, toyo_ch31):
        """31 채널도 동일 구조로 로딩되는지 확인"""
        mincap, df = proto_module.toyo_cycle_data(str(toyo_ch31), 0, 2.0, False)
        assert mincap == pytest.approx(1689.0, rel=0.01)
        assert hasattr(df, "NewData")
        assert len(df.NewData) >= 50


# ══════════════════════════════════════════════════
# pne_cycle_data 테스트 (실제 데이터 I/O)
# ══════════════════════════════════════════════════

class TestPneCycleData:
    """pne_cycle_data() : PNE .cyc → [mincapacity, df] 반환 검증"""

    REQUIRED_COLS = {"Cycle", "Dchg", "Chg", "Eff", "Eff2",
                     "RndV", "AvgV", "DchgEng", "Temp", "OriCyc"}

    @pytest.mark.slow
    def test_returns_list_of_two(self, proto_module, pne_ch008):
        """반환값이 [mincapacity, df] 형식인지 확인"""
        result = proto_module.pne_cycle_data(str(pne_ch008), 0, 0.2, False, False, False)
        assert isinstance(result, list)
        assert len(result) == 2

    @pytest.mark.slow
    def test_mincapacity_is_2335(self, proto_module, pne_ch008):
        """폴더명에서 용량 자동 감지: 2335 mAh"""
        mincap, _ = proto_module.pne_cycle_data(str(pne_ch008), 0, 0.2, False, False, False)
        assert mincap == pytest.approx(2335.0, rel=0.01)

    @pytest.mark.slow
    def test_newdata_has_required_columns(self, proto_module, pne_ch008):
        """df.NewData에 필수 컬럼 모두 존재하는지 확인"""
        _, df = proto_module.pne_cycle_data(str(pne_ch008), 0, 0.2, False, False, False)
        assert hasattr(df, "NewData"), "df.NewData 속성이 없음"
        missing = self.REQUIRED_COLS - set(df.NewData.columns)
        assert not missing, f"누락 컬럼: {missing}"

    @pytest.mark.slow
    def test_newdata_has_rows(self, proto_module, pne_ch008):
        """df.NewData 행 수가 0보다 큰지 확인"""
        _, df = proto_module.pne_cycle_data(str(pne_ch008), 0, 0.2, False, False, False)
        assert len(df.NewData) > 0, "사이클 데이터가 비어있음"

    @pytest.mark.slow
    def test_dchg_ratio_physical_range(self, proto_module, pne_ch008):
        """방전 용량 비율이 물리적 범위 [0.4, 1.2] 이내인지 확인

        PNE 데이터는 초기 RPT + 수명 사이클 혼재 가능 → 허용 범위 넓게 설정.
        """
        _, df = proto_module.pne_cycle_data(str(pne_ch008), 0, 0.2, False, False, False)
        dchg = df.NewData["Dchg"].dropna()
        assert dchg.between(0.4, 1.2).all(), (
            f"물리적 범위 벗어남: min={dchg.min():.3f}, max={dchg.max():.3f}")


# ══════════════════════════════════════════════════
# datapath 파일 경로 → 사이클 데이터 연결 테스트
# ══════════════════════════════════════════════════

class TestDatapathToLoad:
    """경로저장test.txt 파일의 경로들이 실제로 존재하는지 확인"""

    def test_q7m_path_file_paths_exist(self, datapath_dir):
        """Q7M_통합.txt에 기록된 모든 cyclepath가 실제 디렉토리로 존재하는지"""
        path_file = datapath_dir / "Q7M_통합.txt"
        if not path_file.exists():
            pytest.skip("Q7M_통합.txt 없음")

        content = path_file.read_text(encoding="utf-8-sig", errors="replace")
        lines = [l for l in content.strip().split("\n") if l.strip()]

        # 헤더 건너뜀
        data_lines = lines[1:] if "\t" in lines[0] and "path" in lines[0].lower() else lines

        missing = []
        for line in data_lines:
            cols = line.split("\t")
            # path 컬럼: 헤더에 cyclepath가 있으면 1번째, 없으면 0번째
            path_val = cols[1].strip() if len(cols) >= 2 else cols[0].strip()
            path_val = path_val.strip('"')
            if path_val and not os.path.isdir(path_val):
                missing.append(path_val[:60])

        assert not missing, f"존재하지 않는 경로 {len(missing)}개:\n" + "\n".join(missing)

    def test_경로저장test_toyo_paths_loadable(self, proto_module, datapath_dir):
        """경로저장test.txt의 Q7M(Toyo) 경로에서 채널 폴더가 검색되는지"""
        path_file = datapath_dir / "경로저장test.txt"
        if not path_file.exists():
            pytest.skip("경로저장test.txt 없음")

        content = path_file.read_text(encoding="utf-8-sig", errors="replace")
        lines = [l for l in content.strip().split("\n") if l.strip()]

        # 첫 번째 데이터 경로 추출 (헤더 제외)
        data_lines = lines[1:] if "path" in lines[0].lower() else lines
        found_toyo = False
        for line in data_lines:
            cols = line.split("\t")
            path_val = cols[1].strip().strip('"') if len(cols) >= 2 else ""
            if not path_val or not os.path.isdir(path_val):
                continue
            # Toyo 판별 (Pattern 없음)
            if not proto_module.check_cycler(path_val):
                found_toyo = True
                # 채널 폴더가 존재하는지 확인
                channels = [f for f in os.scandir(path_val)
                            if f.is_dir() and f.name.isdigit()]
                assert len(channels) > 0, f"Toyo 채널 폴더 없음: {path_val}"
                break
        if not found_toyo:
            pytest.skip("경로저장test.txt에서 Toyo 경로를 찾지 못함")
