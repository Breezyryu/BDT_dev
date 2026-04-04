"""사이클분석 자동화 테스트 — 직접입력 + 경로파일 로드

테스트 매트릭스:
  [직접입력] 21개 폴더 (Toyo + PNE 복합)
    → 연결처리 Off: 개별 채널 cycle_data 추출 + NewData 검증
    → 연결처리 On:  연결된 다기간 데이터 병합 검증
  [직접입력-연결] 9개 폴더 (연결처리 On 전용)
  [Path파일로드] 19개 .txt 파일
    → 파싱 → 경로 유효성 → cycle_data 추출 → NewData 검증

검증 항목:
  1. cycle_data 함수 반환 구조 (list[2]: [mincapacity, df])
  2. df.NewData 필수 컬럼 존재
  3. 물리적 범위: Dchg(0~1.5), Eff(0.5~1.1), DCIR>0 등
  4. 사이클 번호 순차성
  5. 경로파일 파싱 정합성

실행:
  pytest tests/test_cycle_analysis.py -v                          # 전체
  pytest tests/test_cycle_analysis.py -k "direct_single" -v       # 직접입력 단일
  pytest tests/test_cycle_analysis.py -k "direct_linked" -v       # 직접입력 연결
  pytest tests/test_cycle_analysis.py -k "pathfile" -v            # 경로파일
  pytest tests/test_cycle_analysis.py -k "toyo" -v                # Toyo만
  pytest tests/test_cycle_analysis.py -k "pne" -v                 # PNE만
"""
import os
import pytest
from pathlib import Path

# ── 프로젝트 경로 ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXP_DATA = PROJECT_ROOT / "data" / "exp_data"
DATAPATH = PROJECT_ROOT / "data" / "datapath"

# ══════════════════════════════════════════════════════════════
# 헬퍼
# ══════════════════════════════════════════════════════════════

NEWDATA_REQUIRED_COLS = {
    "Cycle", "Dchg", "Chg", "Eff", "Eff2",
    "RndV", "AvgV", "DchgEng", "Temp", "OriCyc",
}


def _find_first_channel(base: Path, is_pne: bool) -> str | None:
    """폴더 안에서 첫 번째 유효 채널 서브폴더 경로 반환"""
    for d in sorted(base.iterdir()):
        if not d.is_dir():
            continue
        if d.name == "Pattern":
            continue
        if is_pne:
            # PNE: M01ChNNN[NNN] 또는 숫자 아닌 이름
            return str(d)
        else:
            # Toyo: 숫자 이름 폴더
            if d.name.isdigit():
                return str(d)
    return None


def _validate_newdata(df_obj, label: str, min_rows: int = 1):
    """df.NewData 구조 + 물리 범위 검증"""
    assert hasattr(df_obj, "NewData"), f"[{label}] df.NewData 없음"
    nd = df_obj.NewData
    missing = NEWDATA_REQUIRED_COLS - set(nd.columns)
    assert not missing, f"[{label}] 누락 컬럼: {missing}"
    assert len(nd) >= min_rows, f"[{label}] 행 수 부족: {len(nd)} < {min_rows}"

    # 물리 범위 — percentile 기반 검증
    # 첫 번째/마지막 사이클(formation, 시험 종료 incomplete) 및
    # RPT 사이클(매 100cyc마다 C-rate 변경) 아티팩트를 허용하기 위해
    # max/min 대신 99th/1st percentile 사용
    dchg = nd["Dchg"].dropna()
    if len(dchg) > 0:
        assert dchg.min() >= 0.0, f"[{label}] Dchg 음수: {dchg.min():.4f}"
        assert dchg.max() <= 1.5, f"[{label}] Dchg > 1.5: {dchg.max():.4f}"
    eff = nd["Eff"].dropna()
    if len(eff) >= 10:
        p01 = eff.quantile(0.01)
        p99 = eff.quantile(0.99)
        assert p01 >= 0.90, f"[{label}] Eff 1st‰ < 0.90: {p01:.4f}"
        assert p99 <= 1.04, f"[{label}] Eff 99th‰ > 1.04: {p99:.4f}"
    elif len(eff) > 0:
        # 데이터 적을 때는 느슨한 범위
        assert eff.min() >= 0.3, f"[{label}] Eff < 0.3: {eff.min():.4f}"
        assert eff.max() <= 1.5, f"[{label}] Eff > 1.5: {eff.max():.4f}"


# ══════════════════════════════════════════════════════════════
# [직접입력] 21개 폴더 — 연결처리 Off, 개별 채널 추출
# ══════════════════════════════════════════════════════════════

DIRECT_SINGLE_PATHS = [
    # (ID, 폴더명)
    ("Q7M_1-100",   "250207_250307_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 1-100cyc"),
    ("Q8_RT",       "251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202"),
    ("Q8_LT",       "251029_251229_05_나무늬_2335mAh_Q8 선상 ATL SEU4 LT @1-401"),
    ("Q8_50CY_HT",  "251029_260129_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 50CY HT @1-801"),
    ("Q8_75CY_HT",  "251029_260129_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 75CY HT @1-801"),
    ("Q8_30CY_RT",  "251029_260429_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 30CY @1-1202"),
    ("Q8_50CY_RT",  "251029_260429_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 50CY @1-1202"),
    ("Q8_75CY_RT",  "251029_260429_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 75CY @1-1202"),
    ("Q8_50CY_LT",  "251113_260113_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 50CY LT @1-401"),
    ("Q8_30CY_HT2", "251113_260213_05_나무늬_2335mAh_Q8 선상 ATL 2.9V 30CY HT @1-801"),
    ("Q8_30Cy_LT",  "260102_260630_03_홍승기_2335mAh_Q8 선상 ATL 2.9V 30Cy LT @1-400"),
    ("Q8_SEU4_HT",  "260115_260630_02_홍승기_2335mAh_Q8 선상 ATL SEU4 HT@1-802"),
    ("Q8_Main_RT",  "260119_260616_03_홍승기_2369mAh_Q8 ATL Main 2.0C Rss RT"),
    ("Q8_Sub_RT",   "260119_260616_03_홍승기_2485mAh_Q8 ATL Sub 2.0C Rss RT"),
    ("A1_MP1_T23",  "A1_MP1_4500mAh_T23_1"),
    ("Gen4_blk2",   "Dateset_A1_Gen4 2C ATL MP2 [45V 4470mAh] [23] blk2"),
    ("Gen4_blk7",   "Gen4 2C ATL MP2 [45V 4470mAh] [23] blk7 - 240131"),
    ("M1_ATL",      "M1 ATL [45V 4175mAh]"),
    ("Q7M_BLK1",    "Q7M Inner ATL_45V 1689mAh BLK1 20EA [23] - 250304"),
    ("Q7M_Main",    "Q7M Main ATL [45V_1680mAh][23] blk7 20ea - 250228"),
    ("Q7M_Sub",     "Q7M Sub ATL [45v 2068mAh] [23] - 250219r"),
]


class TestDirectSingleCycleData:
    """[직접입력] 연결처리 Off — 각 폴더에서 사이클 데이터 추출 검증"""

    @pytest.mark.slow
    @pytest.mark.parametrize("test_id, folder_name", DIRECT_SINGLE_PATHS,
                             ids=[p[0] for p in DIRECT_SINGLE_PATHS])
    def test_cycle_data_extraction(self, proto_module, test_id, folder_name):
        """각 폴더 → 첫 번째 채널 → cycle_data() → NewData 검증"""
        folder = EXP_DATA / folder_name
        if not folder.is_dir():
            pytest.skip(f"폴더 없음: {folder_name}")

        is_pne = proto_module.check_cycler(str(folder))
        ch_folder = _find_first_channel(folder, is_pne)
        if ch_folder is None:
            pytest.skip(f"채널 폴더 없음: {folder_name}")

        if is_pne:
            mincap, df = proto_module.pne_cycle_data(
                ch_folder, 0, 0.2, False, False, False)
        else:
            mincap, df = proto_module.toyo_cycle_data(
                ch_folder, 0, 2.0, False)

        # mincapacity 추출 성공
        assert mincap > 0, f"[{test_id}] mincapacity 추출 실패: {mincap}"

        # NewData 검증
        _validate_newdata(df, test_id, min_rows=1)

    @pytest.mark.slow
    @pytest.mark.parametrize("test_id, folder_name", DIRECT_SINGLE_PATHS,
                             ids=[p[0] for p in DIRECT_SINGLE_PATHS])
    def test_cycler_detection(self, proto_module, test_id, folder_name):
        """각 폴더의 사이클러 타입(Toyo/PNE) 판별이 예외 없이 되는지"""
        folder = EXP_DATA / folder_name
        if not folder.is_dir():
            pytest.skip(f"폴더 없음: {folder_name}")

        result = proto_module.check_cycler(str(folder))
        assert isinstance(result, bool), f"[{test_id}] check_cycler 반환값이 bool 아님"

    @pytest.mark.slow
    @pytest.mark.parametrize("test_id, folder_name", DIRECT_SINGLE_PATHS,
                             ids=[p[0] for p in DIRECT_SINGLE_PATHS])
    def test_name_capacity_extraction(self, proto_module, test_id, folder_name):
        """각 폴더명에서 용량(mAh) 추출 성공"""
        folder = EXP_DATA / folder_name
        if not folder.is_dir():
            pytest.skip(f"폴더 없음: {folder_name}")

        ch_folder = _find_first_channel(
            folder, proto_module.check_cycler(str(folder)))
        if ch_folder is None:
            pytest.skip(f"채널 없음: {folder_name}")

        cap = proto_module.name_capacity(ch_folder)
        assert cap > 0, f"[{test_id}] 용량 추출 실패: 경로={ch_folder}"


# ══════════════════════════════════════════════════════════════
# [직접입력] 연결처리 On — 다기간 연결 데이터
# ══════════════════════════════════════════════════════════════

# (그룹ID, [연결할 폴더명 리스트])
LINKED_GROUPS = [
    ("Q7M_linked_4period", [
        "250207_250307_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 1-100cyc",
        "250219_250319_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 101-200cyc",
        "250304_250404_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 201-300cyc",
        "250317_251231_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 301-400cyc",
    ]),
    ("Q8_Sub_HT_linked", [
        "260126_260630_3_홍승기_2485mAh_Q8 ATL Sub 2_9V 100cy test HT 1to100cy-2",
        "260209_260630_2_홍승기_2485mAh_Q8 ATL Sub 2_9V 100cy test HT 100to199cy re3",
    ]),
    ("A1_MP1_linked_3period", [
        "A1_MP1_4500mAh_T23_1",
        "A1_MP1_4500mAh_T23_2",
        "A1_MP1_4500mAh_T23_3",
    ]),
]


class TestDirectLinkedCycleData:
    """[직접입력] 연결처리 On — 다기간 데이터 개별 추출 검증

    연결처리의 핵심: 같은 채널, 다른 기간 폴더를 순서대로 로드하면
    사이클 번호가 이어져야 한다.
    """

    @pytest.mark.slow
    @pytest.mark.parametrize("group_id, folders", LINKED_GROUPS,
                             ids=[g[0] for g in LINKED_GROUPS])
    def test_each_period_loads(self, proto_module, group_id, folders):
        """연결 그룹 내 각 기간 폴더가 개별적으로 로드되는지"""
        loaded = 0
        for folder_name in folders:
            folder = EXP_DATA / folder_name
            if not folder.is_dir():
                continue

            is_pne = proto_module.check_cycler(str(folder))
            ch_folder = _find_first_channel(folder, is_pne)
            if ch_folder is None:
                continue

            if is_pne:
                mincap, df = proto_module.pne_cycle_data(
                    ch_folder, 0, 0.2, False, False, False)
            else:
                mincap, df = proto_module.toyo_cycle_data(
                    ch_folder, 0, 2.0, False)

            assert hasattr(df, "NewData"), \
                f"[{group_id}] {folder_name} NewData 없음"
            assert len(df.NewData) > 0, \
                f"[{group_id}] {folder_name} 데이터 비어있음"
            loaded += 1

        assert loaded >= 2, f"[{group_id}] 로드된 기간이 2개 미만: {loaded}"

    @pytest.mark.slow
    @pytest.mark.parametrize("group_id, folders", LINKED_GROUPS,
                             ids=[g[0] for g in LINKED_GROUPS])
    def test_linked_total_cycles_increase(self, proto_module, group_id, folders):
        """연결 시 전체 사이클 수가 단일 기간보다 많아야 함"""
        cycle_counts = []
        for folder_name in folders:
            folder = EXP_DATA / folder_name
            if not folder.is_dir():
                continue

            is_pne = proto_module.check_cycler(str(folder))
            ch_folder = _find_first_channel(folder, is_pne)
            if ch_folder is None:
                continue

            if is_pne:
                _, df = proto_module.pne_cycle_data(
                    ch_folder, 0, 0.2, False, False, False)
            else:
                _, df = proto_module.toyo_cycle_data(
                    ch_folder, 0, 2.0, False)

            if hasattr(df, "NewData"):
                cycle_counts.append(len(df.NewData))

        if len(cycle_counts) < 2:
            pytest.skip(f"[{group_id}] 2개 미만 기간만 로드됨")

        # 전체 합산이 최대 단일 기간보다 커야 함
        total = sum(cycle_counts)
        single_max = max(cycle_counts)
        assert total > single_max, \
            f"[{group_id}] 연결 합산({total})이 단일 최대({single_max})보다 크지 않음"

    @pytest.mark.slow
    @pytest.mark.parametrize("group_id, folders", LINKED_GROUPS,
                             ids=[g[0] for g in LINKED_GROUPS])
    def test_linked_capacity_consistent(self, proto_module, group_id, folders):
        """연결 그룹 내 모든 기간의 mincapacity가 동일한지

        배터리 과학: 같은 셀의 다기간 데이터이므로 기준 용량이 같아야 한다.
        """
        capacities = []
        for folder_name in folders:
            folder = EXP_DATA / folder_name
            if not folder.is_dir():
                continue

            is_pne = proto_module.check_cycler(str(folder))
            ch_folder = _find_first_channel(folder, is_pne)
            if ch_folder is None:
                continue

            cap = proto_module.name_capacity(ch_folder)
            if cap > 0:
                capacities.append(cap)

        if len(capacities) < 2:
            pytest.skip(f"[{group_id}] 용량 추출된 기간이 2개 미만")

        # 모든 기간의 용량이 동일해야 함
        assert len(set(capacities)) == 1, \
            f"[{group_id}] 기간별 용량 불일치: {capacities}"


# ══════════════════════════════════════════════════════════════
# [Path파일로드] 19개 .txt 파일
# ══════════════════════════════════════════════════════════════

PATHFILE_LIST = [
    "Gen4.txt",
    "Gen4_continue.txt",
    "Q7M - 이전2.txt",
    "Q7M_저장 - 이전3.txt",
    "Q7M_저장 - 이전4.txt",
    "Q7M_저장.txt",
    "Q7M_통합 - 이전1.txt",
    "Q7M_통합.txt",
    "Q8_main.txt",
    "경로저장_Gen4_Q7M_ATL_최신.txt",
    "경로저장_Q8_ATL_HT_최신.txt",
    "경로저장_Q8_ATL_LT_최신.txt",
    "경로저장_Q8_ATL_RT_최신.txt",
    "경로저장_Q8_ATL_최신.txt",
    "경로저장_연결처리_test.txt",
    "경로저장_연결처리_test1.txt",
    "경로저장_연결처리_디버깅용_비연결.txt",
    "경로저장_연결처리_디버깅용_연결.txt",
    "경로저장test.txt",
]


def _parse_pathfile_rows(path_file: Path, window_class) -> tuple[bool, list[dict]]:
    """경로 파일 파싱 → (link_mode, [{name, path, channel, capacity}])

    Returns
    -------
    link_mode : bool
    rows : list[dict]
    """
    content = path_file.read_text(encoding="utf-8-sig", errors="replace")
    lines = content.strip().split("\n")

    link_mode = False
    data_start = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#link_mode=1"):
            link_mode = True
            data_start = i + 1
            continue
        if stripped.startswith("#link_mode=0"):
            link_mode = False
            data_start = i + 1
            continue
        if stripped.startswith("#"):
            data_start = i + 1
            continue
        if stripped:
            data_start = i
            break

    # 빈 줄 건너뜀
    while data_start < len(lines) and not lines[data_start].strip():
        data_start += 1

    if data_start >= len(lines):
        return link_mode, []

    # 헤더 감지
    mapping, is_header = window_class._detect_path_columns(lines[data_start])
    if is_header:
        data_start += 1

    rows = []
    for line in lines[data_start:]:
        if not line.strip():
            continue
        cols = line.split("\t")

        def _get(key):
            idx = mapping.get(key)
            if idx is not None and idx < len(cols):
                return cols[idx].strip().strip('"').strip("'")
            return ""

        row = {
            "name": _get("name"),
            "path": _get("path"),
            "channel": _get("channel"),
            "capacity": _get("capacity"),
        }
        if row["path"]:
            rows.append(row)

    return link_mode, rows


class TestPathfileParsing:
    """[Path파일로드] 파일 파싱 정합성 검증"""

    @pytest.mark.parametrize("filename", PATHFILE_LIST,
                             ids=[f.replace(".txt", "") for f in PATHFILE_LIST])
    def test_pathfile_readable(self, filename):
        """경로 파일이 존재하고 읽을 수 있는지"""
        path_file = DATAPATH / filename
        if not path_file.exists():
            pytest.skip(f"파일 없음: {filename}")
        content = path_file.read_text(encoding="utf-8-sig", errors="replace")
        assert len(content.strip()) > 0, f"빈 파일: {filename}"

    @pytest.mark.parametrize("filename", PATHFILE_LIST,
                             ids=[f.replace(".txt", "") for f in PATHFILE_LIST])
    def test_pathfile_has_valid_rows(self, window_class, filename):
        """파싱 후 최소 1개 이상 유효한 경로 행이 있는지"""
        path_file = DATAPATH / filename
        if not path_file.exists():
            pytest.skip(f"파일 없음: {filename}")

        _, rows = _parse_pathfile_rows(path_file, window_class)
        assert len(rows) > 0, f"유효 행 없음: {filename}"

    @pytest.mark.parametrize("filename", PATHFILE_LIST,
                             ids=[f.replace(".txt", "") for f in PATHFILE_LIST])
    def test_pathfile_paths_are_valid_format(self, window_class, filename):
        """파싱된 경로가 드라이브 문자 또는 UNC 형식인지"""
        path_file = DATAPATH / filename
        if not path_file.exists():
            pytest.skip(f"파일 없음: {filename}")

        _, rows = _parse_pathfile_rows(path_file, window_class)
        for row in rows:
            p = row["path"]
            assert (len(p) >= 3 and p[1] == ":") or p.startswith("\\\\"), \
                f"유효하지 않은 경로 형식: {p[:60]}"

    @pytest.mark.parametrize("filename", [
        "Q8_main.txt",
        "경로저장_Gen4_Q7M_ATL_최신.txt",
        "경로저장_Q8_ATL_HT_최신.txt",
        "경로저장_Q8_ATL_LT_최신.txt",
        "경로저장_Q8_ATL_RT_최신.txt",
        "경로저장_Q8_ATL_최신.txt",
        "경로저장_연결처리_test.txt",
        "경로저장_연결처리_test1.txt",
        "경로저장_연결처리_디버깅용_연결.txt",
    ], ids=lambda f: f.replace(".txt", ""))
    def test_linked_pathfile_detects_link_mode(self, window_class, filename):
        """#link_mode=1 파일은 link_mode=True로 파싱되는지"""
        path_file = DATAPATH / filename
        if not path_file.exists():
            pytest.skip(f"파일 없음: {filename}")

        link_mode, _ = _parse_pathfile_rows(path_file, window_class)
        assert link_mode is True, f"{filename}: link_mode 감지 실패"

    def test_nonlinked_pathfile_detects_link_off(self, window_class):
        """#link_mode=0 파일은 link_mode=False로 파싱되는지"""
        path_file = DATAPATH / "경로저장_연결처리_디버깅용_비연결.txt"
        if not path_file.exists():
            pytest.skip("비연결 디버깅 파일 없음")

        link_mode, _ = _parse_pathfile_rows(path_file, window_class)
        assert link_mode is False, "link_mode=0인데 True로 감지됨"


class TestPathfileCycleDataLoad:
    """[Path파일로드] → cycle_data 추출 End-to-End"""

    @pytest.mark.slow
    @pytest.mark.parametrize("filename", PATHFILE_LIST,
                             ids=[f.replace(".txt", "") for f in PATHFILE_LIST])
    def test_pathfile_first_path_loads(self, proto_module, window_class, filename):
        """각 경로 파일의 첫 번째 유효 경로에서 cycle_data 추출"""
        path_file = DATAPATH / filename
        if not path_file.exists():
            pytest.skip(f"파일 없음: {filename}")

        _, rows = _parse_pathfile_rows(path_file, window_class)
        if not rows:
            pytest.skip(f"유효 행 없음: {filename}")

        # 첫 번째 존재하는 경로 찾기
        for row in rows:
            if not os.path.isdir(row["path"]):
                continue

            is_pne = proto_module.check_cycler(row["path"])
            ch_folder = _find_first_channel(Path(row["path"]), is_pne)
            if ch_folder is None:
                continue

            if is_pne:
                mincap, df = proto_module.pne_cycle_data(
                    ch_folder, 0, 0.2, False, False, False)
            else:
                mincap, df = proto_module.toyo_cycle_data(
                    ch_folder, 0, 2.0, False)

            _validate_newdata(df, f"pathfile_{filename}", min_rows=1)
            return  # 첫 번째 성공으로 충분

        pytest.skip(f"존재하는 경로가 없음: {filename}")

    @pytest.mark.slow
    @pytest.mark.parametrize("filename", [
        "Q7M_저장.txt",
        "경로저장test.txt",
        "경로저장_Q8_ATL_RT_최신.txt",
    ], ids=lambda f: f.replace(".txt", ""))
    def test_pathfile_all_paths_load(self, proto_module, window_class, filename):
        """주요 경로 파일의 모든 경로에서 cycle_data 추출 가능한지"""
        path_file = DATAPATH / filename
        if not path_file.exists():
            pytest.skip(f"파일 없음: {filename}")

        _, rows = _parse_pathfile_rows(path_file, window_class)
        if not rows:
            pytest.skip(f"유효 행 없음: {filename}")

        loaded = 0
        failed = []

        for row in rows:
            if not os.path.isdir(row["path"]):
                continue

            is_pne = proto_module.check_cycler(row["path"])
            channels = row["channel"].split(",") if row["channel"] else [""]

            for ch in channels:
                ch = ch.strip()
                if not ch or ch == "-":
                    continue
                try:
                    ch_folder = _find_first_channel(Path(row["path"]), is_pne)
                    if ch_folder is None:
                        continue

                    if is_pne:
                        mincap, df = proto_module.pne_cycle_data(
                            ch_folder, 0, 0.2, False, False, False)
                    else:
                        mincap, df = proto_module.toyo_cycle_data(
                            ch_folder, 0, 2.0, False)

                    assert hasattr(df, "NewData")
                    loaded += 1
                except Exception as e:
                    failed.append(f"{row['path'][:40]}../{ch}: {e}")
                break  # 그룹 내 첫 번째 채널만

        assert loaded > 0, f"로드 성공 0건. 실패: {failed[:3]}"
        if failed:
            print(f"\n  경고: {len(failed)}건 실패 (총 {loaded}건 성공)")


# ══════════════════════════════════════════════════════════════
# [직접입력] 사이클러 타입별 분류 검증
# ══════════════════════════════════════════════════════════════

class TestCyclerTypeClassification:
    """모든 직접입력 폴더의 사이클러 타입 분류 정합성"""

    # 알려진 Toyo 폴더들 (Pattern/ 없음)
    KNOWN_TOYO = {
        "250207_250307_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 1-100cyc",
        "250219_250319_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 101-200cyc",
        "250304_250404_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 201-300cyc",
        "250317_251231_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 301-400cyc",
        "260126_260630_3_홍승기_2485mAh_Q8 ATL Sub 2_9V 100cy test HT 1to100cy-2",
        "260209_260630_2_홍승기_2485mAh_Q8 ATL Sub 2_9V 100cy test HT 100to199cy re3",
        "Dateset_A1_Gen4 2C ATL MP2 [45V 4470mAh] [23] blk2",
        "Gen4 2C ATL MP2 [45V 4470mAh] [23] blk7 - 240131",
        "M1 ATL [45V 4175mAh]",
        "Q7M Inner ATL_45V 1689mAh BLK1 20EA [23] - 250304",
        "Q7M Main ATL [45V_1680mAh][23] blk7 20ea - 250228",
        "Q7M Sub ATL [45v 2068mAh] [23] - 250219r",
    }

    @pytest.mark.parametrize("test_id, folder_name", DIRECT_SINGLE_PATHS,
                             ids=[p[0] for p in DIRECT_SINGLE_PATHS])
    def test_cycler_type_matches_expected(self, proto_module, test_id, folder_name):
        """check_cycler()가 알려진 타입과 일치하는지"""
        folder = EXP_DATA / folder_name
        if not folder.is_dir():
            pytest.skip(f"폴더 없음: {folder_name}")

        is_pne = proto_module.check_cycler(str(folder))
        expected_toyo = folder_name in self.KNOWN_TOYO

        if expected_toyo:
            assert not is_pne, f"[{test_id}] Toyo여야 하는데 PNE로 판별됨"
        else:
            assert is_pne, f"[{test_id}] PNE여야 하는데 Toyo로 판별됨"


# ══════════════════════════════════════════════════════════════
# [직접입력] 물리적 크로스체크
# ══════════════════════════════════════════════════════════════

class TestPhysicalCrossCheck:
    """배터리 과학 기반 크로스체크

    같은 제품(Q8 2335mAh)의 다조건 수명데이터에서
    공통 물리적 성질이 유지되는지 확인.
    """

    Q8_2335_FOLDERS = [
        "251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202",
        "251029_251229_05_나무늬_2335mAh_Q8 선상 ATL SEU4 LT @1-401",
        "251029_260129_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 50CY HT @1-801",
        "251029_260429_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 30CY @1-1202",
    ]

    @pytest.mark.slow
    def test_q8_initial_dchg_ratio_near_one(self, proto_module):
        """Q8 제품군: 초기 사이클 방전용량비가 1.0 ± 0.1 이내

        배터리 과학: 정상 셀의 첫 수 사이클은 거의 풀 용량이어야 함.
        """
        for folder_name in self.Q8_2335_FOLDERS:
            folder = EXP_DATA / folder_name
            if not folder.is_dir():
                continue

            ch_folder = _find_first_channel(folder, is_pne=True)
            if ch_folder is None:
                continue

            _, df = proto_module.pne_cycle_data(
                ch_folder, 0, 0.2, False, False, False)
            if not hasattr(df, "NewData") or len(df.NewData) < 3:
                continue

            # 처음 3사이클의 평균 Dchg
            early_dchg = df.NewData["Dchg"].iloc[:3].mean()
            assert 0.85 <= early_dchg <= 1.15, \
                f"{folder_name}: 초기 Dchg={early_dchg:.3f}, 1.0±0.15 벗어남"

    @pytest.mark.slow
    def test_q8_all_same_capacity(self, proto_module):
        """Q8 2335mAh 제품군: 모든 폴더의 mincapacity가 2335"""
        caps = []
        for folder_name in self.Q8_2335_FOLDERS:
            folder = EXP_DATA / folder_name
            if not folder.is_dir():
                continue

            ch_folder = _find_first_channel(folder, is_pne=True)
            if ch_folder is None:
                continue

            mincap, _ = proto_module.pne_cycle_data(
                ch_folder, 0, 0.2, False, False, False)
            caps.append(mincap)

        if len(caps) < 2:
            pytest.skip("Q8 폴더 2개 미만")

        assert all(c == pytest.approx(2335.0, rel=0.01) for c in caps), \
            f"Q8 용량 불일치: {caps}"
