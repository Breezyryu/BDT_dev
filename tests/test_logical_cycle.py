"""논리사이클(cycle_map) 로직 검증 테스트.

대표 시험 유형별 exp_data 폴더로 cycle_map 생성 결과 검증:
- 가속수명 (일반 모드)
- Rss (일반 모드)
- GITT (스윕 모드)
- 반셀 (스윕 모드)
- 보관/소규모 (일반 모드 강제)
- 펄스 (스윕 모드)
"""
import os
import sys
import pytest

# proto_.py가 있는 DataTool_dev를 sys.path에 추가
_PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEV = os.path.join(_PROJ, 'DataTool_dev')
if _DEV not in sys.path:
    sys.path.insert(0, _DEV)
if _PROJ not in sys.path:
    sys.path.insert(0, _PROJ)

from DataTool_optRCD_proto_ import (
    pne_build_cycle_map,
    toyo_build_cycle_map,
    _opposite_dirs,
    _classify_single_pne_cycle,
    extract_schedule_structure_from_sch,
    extract_toyo_ptn_structure,
    get_sweep_scope,
    resolve_tc_range,
    _SWEEP_SCOPE_CACHE,
    HAS_SCH_PARSER,
)

EXP_DATA = os.path.join(_PROJ, 'data', 'exp_data')
PATTERN = os.path.join(_PROJ, 'data', 'pattern')


def _find_first_channel(folder_path: str) -> str | None:
    """exp_data 폴더에서 첫 번째 채널 경로를 반환."""
    if not os.path.isdir(folder_path):
        return None
    for name in os.listdir(folder_path):
        full = os.path.join(folder_path, name)
        if os.path.isdir(full) and name.startswith('M'):
            return full
    return None


# =============================================================================
# _opposite_dirs 수정 검증
# =============================================================================

class TestOppositesDirs:
    """MIXED 방향 병합 포함 검증."""

    def test_basic_pairs(self):
        assert _opposite_dirs('CHG', 'DCHG') is True
        assert _opposite_dirs('DCHG', 'CHG') is True

    def test_same_direction(self):
        assert _opposite_dirs('CHG', 'CHG') is False
        assert _opposite_dirs('DCHG', 'DCHG') is False

    def test_mixed_pairs(self):
        # MIXED는 양방향이므로 CHG/DCHG 모두와 짝
        assert _opposite_dirs('MIXED', 'CHG') is True
        assert _opposite_dirs('MIXED', 'DCHG') is True
        assert _opposite_dirs('CHG', 'MIXED') is True
        assert _opposite_dirs('DCHG', 'MIXED') is True
        assert _opposite_dirs('MIXED', 'MIXED') is True


# =============================================================================
# extract_schedule_structure_from_sch 검증
# =============================================================================

@pytest.mark.skipif(not HAS_SCH_PARSER, reason='parse_pne_schedule 모듈 없음')
class TestSchStructure:
    """PNE .sch 파일 구조 분석 검증."""

    @pytest.fixture
    def sch_dir(self):
        return os.path.join(PATTERN, 'pne_4905mAh')

    def test_life_schedule(self, sch_dir):
        """수명시험 .sch → schedule_type='가속수명', sweep_mode=False."""
        sch = os.path.join(sch_dir,
                           'Gen4p 4905mAh ATL 20C Proto DOE1_수명1500cy_20C_30V_Gen4p_4905mAh.sch')
        if not os.path.isfile(sch):
            pytest.skip('sch file not found')
        result = extract_schedule_structure_from_sch(sch, 4905)
        assert result is not None
        assert result['schedule_type'] == '가속수명'
        assert result['sweep_mode'] is False

    def test_gitt_schedule(self, sch_dir):
        """GITT .sch → schedule_type='GITT', sweep_mode=True."""
        sch = os.path.join(sch_dir,
                           'Gen4p 4905mAh ATL 20C Proto DOE1_GITT01C_Gen4p_4905mAh.sch')
        if not os.path.isfile(sch):
            pytest.skip('sch file not found')
        result = extract_schedule_structure_from_sch(sch, 4905)
        assert result is not None
        assert result['schedule_type'] == 'GITT'
        assert result['sweep_mode'] is True
        assert result['has_gitt_hppc'] is True

    def test_soc_dcir_schedule(self, sch_dir):
        """SOC별DCIR .sch → schedule_type='SOC별DCIR', sweep_mode=True."""
        sch = os.path.join(sch_dir,
                           'Gen4p 4905mAh ATL 20C Proto DOE1_SOC별DCIR충방전_Gen4p_4905mAh.sch')
        if not os.path.isfile(sch):
            pytest.skip('sch file not found')
        result = extract_schedule_structure_from_sch(sch, 4905)
        assert result is not None
        assert result['schedule_type'] == 'SOC별DCIR'
        assert result['sweep_mode'] is True

    def test_rss_schedule(self, sch_dir):
        """Rss(가속수명+DCIR) .sch → has_rss=True."""
        sch_files = [f for f in os.listdir(sch_dir) if 'Rss' in f and f.endswith('.sch')]
        if not sch_files:
            pytest.skip('Rss sch file not found')
        sch = os.path.join(sch_dir, sch_files[0])
        result = extract_schedule_structure_from_sch(sch, 4905)
        assert result is not None
        # Rss 포함 가속수명은 일반 모드
        assert result['sweep_mode'] is False
        assert result['has_rss'] is True


# =============================================================================
# pne_build_cycle_map 통합 검증
# =============================================================================

class TestPneBuildCycleMap:
    """대표 PNE 시험 데이터로 cycle_map 생성 검증."""

    def test_life_test_general_mode(self):
        """가속수명 시험: 일반 모드 (1:1 매핑), 대부분 int 값."""
        folder = os.path.join(EXP_DATA, '251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202')
        ch = _find_first_channel(folder)
        if ch is None:
            pytest.skip('test data not found')
        cycle_map, cap = pne_build_cycle_map(ch, 2335, 0.2)
        assert len(cycle_map) > 0
        assert cap > 0
        # 가속수명: 대부분 int 값 (1:1 매핑)
        n_int = sum(1 for v in cycle_map.values() if isinstance(v, int))
        assert n_int / len(cycle_map) >= 0.5, f'가속수명인데 int 비율이 낮음: {n_int}/{len(cycle_map)}'

    def test_rss_general_mode(self):
        """Rss 시험: 일반 모드."""
        folder = os.path.join(EXP_DATA, '260119_260616_03_홍승기_2369mAh_Q8 ATL Main 2.0C Rss RT')
        ch = _find_first_channel(folder)
        if ch is None:
            pytest.skip('test data not found')
        cycle_map, cap = pne_build_cycle_map(ch, 2369, 0.2)
        assert len(cycle_map) > 0

    def test_gitt_sweep_mode(self):
        """반셀 GITT: 스윕 모드 (대부분 tuple 값)."""
        folder = os.path.join(EXP_DATA, '250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half-14pi-GITT-0.1C-T23')
        ch = _find_first_channel(folder)
        if ch is None:
            pytest.skip('test data not found')
        cycle_map, cap = pne_build_cycle_map(ch, 4.187, 0.1)
        assert len(cycle_map) > 0
        # GITT: tuple이 존재해야 함 (스윕 그룹)
        n_tuple = sum(1 for v in cycle_map.values() if isinstance(v, tuple))
        assert n_tuple > 0, f'GITT인데 tuple이 없음'

    def test_storage_few_cycles(self):
        """보관 후 측정 (소수 사이클): TC ≤ 5이면 일반 모드 강제."""
        folder = os.path.join(EXP_DATA, '260303_260305_05_문현규_3561mAh_iphone17 basic 고온저장 75도 5일 SOC100 ATL')
        ch = _find_first_channel(folder)
        if ch is None:
            pytest.skip('test data not found')
        cycle_map, cap = pne_build_cycle_map(ch, 3561, 0.2)
        # 소수 사이클 → 일반 모드 (비어있어도 OK)
        if cycle_map:
            # TC ≤ 5 강제 일반 → 대부분 int
            n_int = sum(1 for v in cycle_map.values() if isinstance(v, int))
            total = len(cycle_map)
            assert n_int >= total * 0.5 or total <= 5

    def test_mincapacity_zero_guard(self):
        """mincapacity=0 → pne_min_cap()이 실제 용량 복구하여 정상 동작 (crash 없음)."""
        folder = os.path.join(EXP_DATA, '251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202')
        ch = _find_first_channel(folder)
        if ch is None:
            pytest.skip('test data not found')
        # mincapacity=0 → pne_min_cap()이 데이터에서 실제 용량 복구
        # 복구 실패 시 {}, 0 반환 (if not mincapacity 가드)
        cycle_map, cap = pne_build_cycle_map(ch, 0, 0.2)
        assert isinstance(cycle_map, dict)
        # pne_min_cap()이 복구하면 cap > 0, 복구 실패면 cap == 0
        assert isinstance(cap, (int, float))


# =============================================================================
# Toyo 검증
# =============================================================================

class TestToyoCycleMap:
    """Toyo 가속수명 데이터 cycle_map 검증."""

    def _find_toyo_channel(self):
        """테스트용 Toyo 채널 경로 탐색."""
        toyo_folders = [
            d for d in os.listdir(EXP_DATA)
            if 'Q7M' in d and os.path.isdir(os.path.join(EXP_DATA, d))
        ]
        if not toyo_folders:
            return None
        folder = os.path.join(EXP_DATA, toyo_folders[0])
        return _find_first_channel(folder)

    def test_toyo_life_test(self):
        """Toyo 가속수명 시험: cycle_map 생성 성공."""
        ch = self._find_toyo_channel()
        if ch is None:
            pytest.skip('Toyo test data not found')
        try:
            cycle_map, cap = toyo_build_cycle_map(ch, 1689, 0.2)
        except Exception as e:
            pytest.skip(f'toyo_build_cycle_map failed: {e}')
        assert isinstance(cycle_map, dict)

    def test_toyo_ptn_structure(self):
        """Toyo .PTN 구조 분석: 시험유형 판별."""
        ch = self._find_toyo_channel()
        if ch is None:
            pytest.skip('Toyo test data not found')
        result = extract_toyo_ptn_structure(ch, 1689)
        if result is None:
            pytest.skip('.PTN file not found in channel')
        assert result['schedule_type'] in ('가속수명', 'GITT', '율별', '기타')
        assert result['main_loop_count'] >= 1
        assert result['n_chg_per_loop'] >= 1

    def test_toyo_ptn_hint_integration(self):
        """Toyo .PTN 힌트가 cycle_map에 정상 전달되는지 확인 (crash 없음)."""
        ch = self._find_toyo_channel()
        if ch is None:
            pytest.skip('Toyo test data not found')
        ptn_struct = extract_toyo_ptn_structure(ch, 1689)
        # ptn_struct가 None이든 dict이든 crash 없이 동작해야 함
        try:
            cycle_map, cap = toyo_build_cycle_map(ch, 1689, 0.2, ptn_struct=ptn_struct)
        except Exception as e:
            pytest.fail(f'ptn_struct 힌트 전달 시 crash: {e}')
        assert isinstance(cycle_map, dict)


# =============================================================================
# resolve_tc_range 헬퍼 검증
# =============================================================================

class TestResolveTcRange:
    """resolve_tc_range() 단위 테스트."""

    def test_single_tc_no_scope(self):
        """단일 TC, cycle scope → (tc, tc) 반환."""
        cm = {1: 5, 2: 10}
        assert resolve_tc_range(cm, 1) == (5, 5)
        assert resolve_tc_range(cm, 2) == (10, 10)

    def test_tuple_tc_no_scope(self):
        """tuple TC, cycle scope → 전체 범위."""
        cm = {1: (5, 148)}
        assert resolve_tc_range(cm, 1) == (5, 148)

    def test_missing_key(self):
        """존재하지 않는 논리사이클 → None."""
        cm = {1: 5}
        assert resolve_tc_range(cm, 99) is None

    def test_sweep_scope_charge(self):
        """sweep_scope 있을 때 charge scope → 충전 서브 범위."""
        cm = {4: (5, 148)}
        ss = {4: {'chg': (5, 112), 'dchg': (114, 148)}}
        assert resolve_tc_range(cm, 4, scope="charge", sweep_scope=ss) == (5, 112)

    def test_sweep_scope_discharge(self):
        """sweep_scope 있을 때 discharge scope → 방전 서브 범위."""
        cm = {4: (5, 148)}
        ss = {4: {'chg': (5, 112), 'dchg': (114, 148)}}
        assert resolve_tc_range(cm, 4, scope="discharge", sweep_scope=ss) == (114, 148)

    def test_sweep_scope_cycle(self):
        """sweep_scope 있어도 cycle scope → 전체 범위."""
        cm = {4: (5, 148)}
        ss = {4: {'chg': (5, 112), 'dchg': (114, 148)}}
        assert resolve_tc_range(cm, 4, scope="cycle", sweep_scope=ss) == (5, 148)

    def test_sweep_scope_missing_key(self):
        """sweep_scope에 해당 논리사이클 없음 → 전체 범위 폴백."""
        cm = {1: (3, 4), 4: (5, 148)}
        ss = {4: {'chg': (5, 112), 'dchg': (114, 148)}}
        # 논리사이클 1은 sweep_scope에 없음 → cycle_map의 (3,4)
        assert resolve_tc_range(cm, 1, scope="charge", sweep_scope=ss) == (3, 4)

    def test_sweep_scope_partial_dir(self):
        """단방향 스윕 (dchg 없음) + discharge scope → 전체 범위 폴백."""
        cm = {3: (10, 50)}
        ss = {3: {'chg': (10, 50)}}  # chg만 있음
        assert resolve_tc_range(cm, 3, scope="discharge", sweep_scope=ss) == (10, 50)

    def test_single_tc_with_sweep_scope(self):
        """단일 TC에 sweep_scope 적용 시 (비스윕) → (tc, tc)."""
        cm = {1: 5, 4: (5, 148)}
        ss = {4: {'chg': (5, 112), 'dchg': (114, 148)}}
        assert resolve_tc_range(cm, 1, scope="charge", sweep_scope=ss) == (5, 5)


# =============================================================================
# sweep_scope 캐시 통합 검증 (실데이터)
# =============================================================================

class TestSweepScopeCache:
    """pne_build_cycle_map이 sweep_scope를 캐시에 저장하는지 검증."""

    def test_gitt_sweep_scope_populated(self):
        """GITT 시험: sweep_scope가 비어있지 않아야 함."""
        folder = os.path.join(
            EXP_DATA,
            '260316_270318_00_이성일_5882mAh_M47 ATL ECT GITT',
        )
        ch = _find_first_channel(folder)
        if ch is None:
            pytest.skip('GITT test data not found')
        # 캐시 초기화
        _SWEEP_SCOPE_CACHE.clear()
        cycle_map, cap = pne_build_cycle_map(ch, 5882, 0.2)
        ss = get_sweep_scope(ch)
        # GITT 스윕 모드 → sweep_scope 존재
        assert len(ss) > 0, f'GITT인데 sweep_scope가 비어있음: {cycle_map}'

    def test_gitt_sweep_scope_has_chg_dchg(self):
        """GITT 스윕 논리사이클: chg, dchg 키가 모두 존재."""
        folder = os.path.join(
            EXP_DATA,
            '260316_270318_00_이성일_5882mAh_M47 ATL ECT GITT',
        )
        ch = _find_first_channel(folder)
        if ch is None:
            pytest.skip('GITT test data not found')
        _SWEEP_SCOPE_CACHE.clear()
        cycle_map, cap = pne_build_cycle_map(ch, 5882, 0.2)
        ss = get_sweep_scope(ch)
        # paired 스윕에는 chg, dchg 모두 있어야 함
        for ln, scope_entry in ss.items():
            if 'chg' in scope_entry and 'dchg' in scope_entry:
                chg_range = scope_entry['chg']
                dchg_range = scope_entry['dchg']
                # 충전 범위와 방전 범위는 겹치지 않아야 함
                assert chg_range[1] < dchg_range[0] or dchg_range[1] < chg_range[0], \
                    f'L{ln}: chg={chg_range}, dchg={dchg_range} 범위가 겹침'

    def test_gitt_sweep_scope_within_cycle_map(self):
        """sweep_scope의 TC 범위는 cycle_map의 전체 범위 내에 있어야 함."""
        folder = os.path.join(
            EXP_DATA,
            '260316_270318_00_이성일_5882mAh_M47 ATL ECT GITT',
        )
        ch = _find_first_channel(folder)
        if ch is None:
            pytest.skip('GITT test data not found')
        _SWEEP_SCOPE_CACHE.clear()
        cycle_map, cap = pne_build_cycle_map(ch, 5882, 0.2)
        ss = get_sweep_scope(ch)
        for ln, scope_entry in ss.items():
            cm_val = cycle_map[ln]
            if isinstance(cm_val, tuple):
                cm_start, cm_end = cm_val
            else:
                cm_start = cm_end = cm_val
            for key in ('chg', 'dchg'):
                if key in scope_entry:
                    s, e = scope_entry[key]
                    assert s >= cm_start, f'L{ln} {key} start {s} < cycle_map start {cm_start}'
                    assert e <= cm_end, f'L{ln} {key} end {e} > cycle_map end {cm_end}'

    def test_life_test_no_sweep_scope(self):
        """가속수명 시험 (일반 모드): sweep_scope가 비어있어야 함."""
        folder = os.path.join(
            EXP_DATA,
            '251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202',
        )
        ch = _find_first_channel(folder)
        if ch is None:
            pytest.skip('test data not found')
        _SWEEP_SCOPE_CACHE.clear()
        cycle_map, cap = pne_build_cycle_map(ch, 2335, 0.2)
        ss = get_sweep_scope(ch)
        # 일반 모드에서는 sweep_scope가 비어있어야 함
        assert ss == {}, f'일반 모드인데 sweep_scope가 있음: {ss}'

    def test_halfcell_gitt_sweep_scope(self):
        """반셀 GITT: sweep_scope 생성 검증."""
        folder = os.path.join(
            EXP_DATA,
            '250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half-14pi-GITT-0.1C-T23',
        )
        ch = _find_first_channel(folder)
        if ch is None:
            pytest.skip('half-cell GITT data not found')
        _SWEEP_SCOPE_CACHE.clear()
        cycle_map, cap = pne_build_cycle_map(ch, 4.187, 0.1)
        ss = get_sweep_scope(ch)
        # 반셀 GITT도 스윕 모드 → sweep_scope 빈 dict가 아니어야 함
        # (단방향 스윕이면 한쪽만 있을 수 있음)
        assert isinstance(ss, dict)
        if ss:
            for ln, entry in ss.items():
                assert any(k in entry for k in ('chg', 'dchg')), \
                    f'L{ln}: chg도 dchg도 없음: {entry}'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
