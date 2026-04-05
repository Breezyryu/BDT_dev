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

# ══════════════════════════════════════════════
# 프로필 분석 테스트용 — 전체 실험 데이터 카탈로그
# ══════════════════════════════════════════════

# 각 항목: (폴더명, 용량mAh, C-rate, 사이클러, 비고)
ALL_EXP_DATA = [
    # ── PNE GITT / DCIR ──
    ("240821 선행랩 류성택 Gen4pGr mini-ATL-WD-Proto-422mAh-20C-450V-GITT-15도",
     422, 0.2, "pne", "GITT"),
    ("240919 선행랩 류성택 Gen4pGr mini-ATL-WD-Proto-422mAh-20C-450V-SOC별DCIR-15도",
     422, 0.2, "pne", "SOC별DCIR"),

    # ── Toyo 수명 시리즈 (Q7M) ──
    ("250207_250307_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 1-100cyc",
     1689, 2.0, "toyo", "수명1-100"),
    ("250219_250319_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 101-200cyc",
     1689, 2.0, "toyo", "수명101-200"),
    ("250304_250404_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 201-300cyc",
     1689, 2.0, "toyo", "수명201-300"),
    ("250317_251231_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 301-400cyc",
     1689, 2.0, "toyo", "수명301-400"),

    # ── PNE DCIR 신규 ──
    ("250513_250526_05_나무늬_2610mAh_Gen5+B SDI MP1 DoE SBR 0.7 DCIR",
     2610, 0.2, "pne", "DCIR"),
    ("250513_250526_05_나무늬_2610mAh_Gen5+B SDI MP1 Main SBR 0.9 DCIR",
     2610, 0.2, "pne", "DCIR"),

    # ── PNE Half-cell GITT ──
    ("250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half-14pi-GITT-0.1C-T23",
     4.187, 0.1, "pne", "half-ca-GITT"),
    ("250905_250915_00_류성택_4-376mAh_M2-SDI-open-an-half-14pi-GITT-0.1C-T23",
     4.376, 0.1, "pne", "half-an-GITT"),

    # ── PNE RatedCh half ──
    ("251002_251010_00_박민희_4-19mAh_RatedCh half ca 4.19mAh SDI",
     4.19, 0.2, "pne", "half-rated"),

    # ── PNE Q8 수명 시리즈 ──
    ("251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202",
     2335, 0.2, "pne", "Q8-RT-장기"),
    ("251029_251229_05_나무늬_2335mAh_Q8 선상 ATL SEU4 LT @1-401",
     2335, 0.2, "pne", "Q8-LT"),
    ("251029_251229_05_나무늬_2935mAh_Q8 선상 ATL SEU4 LT @1-401 - 복사본",
     2935, 0.2, "pne", "Q8-LT-복사본"),
    ("251029_260129_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 50CY HT @1-801",
     2335, 0.2, "pne", "Q8-HT-50CY"),
    ("251029_260129_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 75CY HT @1-801",
     2335, 0.2, "pne", "Q8-HT-75CY"),
    ("251029_260129_05_나무늬_2335mAh_Q8 선상 ATL SEU4 HT @1-801",
     2335, 0.2, "pne", "Q8-HT"),
    ("251029_260429_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 30CY @1-1202",
     2335, 0.2, "pne", "Q8-30CY"),
    ("251029_260429_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 50CY @1-1202",
     2335, 0.2, "pne", "Q8-50CY"),
    ("251029_260429_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 75CY @1-1202",
     2335, 0.2, "pne", "Q8-75CY"),
    ("251029_260429_05_나무늬_Q8 선상 ATL SEU4 2.9V 30CY @1-1202 - 복사본",
     2335, 0.2, "pne", "Q8-30CY-복사본"),
    ("251113_260113_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 50CY LT @1-401",
     2335, 0.2, "pne", "Q8-50CY-LT"),
    ("251113_260213_05_나무늬_2335mAh_Q8 선상 ATL 2.9V 30CY HT @1-801",
     2335, 0.2, "pne", "Q8-30CY-HT"),

    # ── PNE 율별 / Pulse / Hysteresis ──
    ("251209_251213_05_현혜정_6490mAh_LWN Si25P SPL 율별방전Profile",
     6490, 0.2, "pne", "율별방전"),
    ("251209_260209_05_나무늬_2335mAh_Q8 선상 ATL SEU4 HT @301-801",
     2335, 0.2, "pne", "Q8-HT-301"),
    ("251218_251230_00_박민희_3-45mAh_M1 ATL Cathode Half T23",
     3.45, 0.2, "pne", "half-ca-M1"),
    ("251218_251230_00_박민희_4-04mAh_M1 ATL Anode Half T23",
     4.04, 0.2, "pne", "half-an-M1"),
    ("251224_260110_00_박민희_3-45mAh_M1 ATL Cathode Half T23 GITT 0.1C",
     3.45, 0.1, "pne", "half-ca-GITT"),
    ("251224_260110_00_박민희_4-04mAh_M1 ATL Anode Half T23 GITT 0.1C",
     4.04, 0.1, "pne", "half-an-GITT"),
    ("251224_260110_00_박민희_4-04mAh_M1 ATL Anode Half T23 GITT 0.05C 3.0V",
     4.04, 0.05, "pne", "half-an-GITT-slow"),

    # ── PNE 기타 ──
    ("260102_260630_03_홍승기_2335mAh_Q8 선상 ATL 2.9V 30Cy LT @1-400",
     2335, 0.2, "pne", "Q8-30Cy-LT"),
    ("260109_260112_05_이근준_5000mAh_Gen5P Si5 ATL T2 3M 보관 용량 측정 4cycle SOC 30 setting ch7 to 12",
     5000, 0.2, "pne", "보관용량"),
    ("260115_260630_02_홍승기_2335mAh_Q8 선상 ATL SEU4 HT@1-802",
     2335, 0.2, "pne", "Q8-HT-802"),
    ("260119_260616_03_홍승기_2369mAh_Q8 ATL Main 2.0C Rss RT",
     2369, 2.0, "pne", "Q8-Main-Rss"),
    ("260119_260616_03_홍승기_2485mAh_Q8 ATL Sub 2.0C Rss RT",
     2485, 2.0, "pne", "Q8-Sub-Rss"),
    ("260119_260616_03_홍승기_2485mAh_Q8 ATL Sub 2C 2.9V 100Cy",
     2485, 2.0, "pne", "Q8-Sub-100Cy"),

    # ── Toyo 기타 ──
    ("260126_260630_3_홍승기_2485mAh_Q8 ATL Sub 2_9V 100cy test HT 1to100cy-2",
     2485, 2.0, "toyo", "Q8-HT-Toyo"),

    # ── PNE RE / CH32 ──
    ("260130_260630_03_홍승기_2369mAh_Q8 Main 2C Rss RT CH32 57Cy-RE",
     2369, 2.0, "pne", "RE-2369"),
    ("260130_260630_03_홍승기_3456mAh_Q8 Main 2C Rss RT CH32 57Cy-RE",
     3456, 2.0, "pne", "RE-3456"),
    ("260130_260630_03_홍승기_Q8 Main 2C Rss RT CH32 57Cy-RE",
     2369, 2.0, "pne", "RE-noCAP"),

    # ── PNE 율별용량 / Cosmx ──
    ("260202_260226_05_문현규_5075mAh_Cosmx 25Si 율별용량+Hybrid ch54",
     5075, 0.2, "pne", "Cosmx-25Si"),
    ("260204_260226_05_문현규_4900mAh_Cosmx gen5 율별용량 ch61",
     4900, 0.2, "pne", "Cosmx-gen5"),
    ("260204_260226_05_문현규_5070mAh_Cosmx Gen5P 율별용량",
     5070, 0.2, "pne", "Cosmx-Gen5P"),

    # ── Toyo 수명 ──
    ("260209_260630_2_홍승기_2485mAh_Q8 ATL Sub 2_9V 100cy test HT 100to199cy re3",
     2485, 2.0, "toyo", "Q8-HT-Toyo-re3"),

    # ── PNE Pulse ──
    ("260211_260310_05_문현규_3885mAh_POR 40C pulse PA1 ATL",
     3885, 0.2, "pne", "pulse-PA1-ATL"),
    ("260211_260310_05_문현규_3885mAh_POR 40C pulse PA1 SDI",
     3885, 0.2, "pne", "pulse-PA1-SDI"),
    ("260211_260310_05_문현규_4855mAh_POR 40C pulse PA3 ATL",
     4855, 0.2, "pne", "pulse-PA3-ATL"),
    ("260211_260310_05_문현규_4855mAh_POR 40C pulse PA3 SDI",
     4855, 0.2, "pne", "pulse-PA3-SDI"),

    # ── PNE DCIR ──
    ("260212_260215_05_한지영_5432mAh_SDI Phase2 MP2 Fresh DCIR SOC10",
     5432, 0.2, "pne", "DCIR-Fresh"),
    ("260212_260215_05_한지영_5432mAh_SDI Phase2 MP2 고온수명후 DCIR SOC10",
     5432, 0.2, "pne", "DCIR-고온후"),

    # ── PNE 연속저장 DCIR ──
    ("260226_260228_05_문현규_3876mAh_PS 연속저장 DCIR",
     3876, 0.2, "pne", "연속-PS"),
    ("260226_260228_05_문현규_3885mAh_PA1 연속저장 DCIR",
     3885, 0.2, "pne", "연속-PA1"),

    # ── 혼합 (Toyo 폴더지만 PNE 채널명 구조) ──
    ("260303_260305_05_문현규_3561mAh_iphone17 basic 고온저장 75도 5일 SOC100 ATL",
     3561, 0.2, "toyo", "고온저장"),

    # ── PNE SOC별 DCIR / Hysteresis ──
    ("260306_260318_05_현혜정_6330mAh_LWN 25P(after LT100cy) SOC별 DCIR 신규",
     6330, 0.2, "pne", "SOC-DCIR-LT100"),
    ("260310_260312_05_이근준_4991mAh_Gen5P ATL MP1 8M Fresh 보관 용량 측정 2cycle SOC30 setting",
     4991, 0.2, "pne", "보관-8M"),
    ("260316_260320_05_현혜정_6330mAh_LWN 25P(after LT50cy) 0.5C-10min volt hysteresis",
     6330, 0.5, "pne", "hysteresis-05C"),
    ("260316_270318_00_이성일_5882mAh_M47 ATL ECT GITT",
     5882, 0.2, "pne", "ECT-GITT"),
    ("260317_260325_05_현혜정_4986mAh_SDI Gen5+ MP1 0.2C-10min volt hysteresis",
     4986, 0.2, "pne", "hysteresis-SDI"),
    ("260319_260326_05_현혜정_6330mAh_LWN 25P(after LT50cy) 0.2C-10min volt hysteresis",
     6330, 0.2, "pne", "hysteresis-02C"),

    # ── PNE ECT parameter GITT ──
    ("260326_260329_00_류성택_4860mAh_A17 ATL ECT parameter11 GITT",
     4860, 0.2, "pne", "A17-ATL-GITT"),
    ("260326_260329_00_류성택_4860mAh_A17 SDI ECT parameter11 GITT",
     4860, 0.2, "pne", "A17-SDI-GITT"),

    # ── PNE A1 시리즈 ──
    ("A1_MP1_4500mAh_T23_1", 4500, 0.2, "pne", "A1-1"),
    ("A1_MP1_4500mAh_T23_2", 4500, 0.2, "pne", "A1-2"),
    ("A1_MP1_4500mAh_T23_3", 4500, 0.2, "pne", "A1-3"),
]


@pytest.fixture(params=ALL_EXP_DATA, ids=lambda x: x[4])
def all_exp_entry(request, exp_data_dir):
    """모든 실험 데이터 경로에 대한 parametrize fixture.

    Returns
    -------
    dict
        folder, capacity, crate, cycler, tag, channel_path (첫 채널)
    """
    folder_name, capacity, crate, cycler, tag = request.param
    folder = exp_data_dir / folder_name
    if not folder.is_dir():
        pytest.skip(f"데이터 없음: {folder_name}")

    # 첫 번째 유효 채널 폴더 찾기
    ch_path = None
    for d in sorted(folder.iterdir()):
        if d.is_dir() and d.name != "Pattern" and d.name != "processed_data":
            ch_path = d
            break
    if ch_path is None:
        pytest.skip(f"채널 없음: {folder_name}")

    return {
        "folder": folder,
        "folder_name": folder_name,
        "capacity": capacity,
        "crate": crate,
        "cycler": cycler,
        "tag": tag,
        "channel_path": ch_path,
    }


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
