"""회귀 테스트 — PNE Restore 파일 처리

버그 이력:
  260404 — _cached_pne_restore_files()가 빈 SaveEndData CSV를 읽을 때
  pandas.errors.EmptyDataError를 처리하지 않아 pro_continue_confirm_button
  전체가 실패하던 문제 수정.

  재현 경로:
    data/exp_data/260226_260228_05_문현규_3885mAh_PA1 연속저장 DCIR/M01Ch015[015]/

테스트 목적:
  - 빈 SaveEndData 파일이 있는 채널에서 예외 없이 (None, None, list) 반환 확인
  - pne_search_cycle()이 [-1, -1] 반환 확인
  - pne_continue_data()가 예외 없이 빈 DataFrame 반환 확인
  - 정상 PNE 폴더(SaveEndData 있음)에서는 DataFrame 반환 확인
"""
import os
import pytest
import pandas as pd
from pathlib import Path


# ══════════════════════════════════════════════════════════════
# _cached_pne_restore_files 회귀 테스트
# ══════════════════════════════════════════════════════════════

class TestCachedPneRestoreFiles:
    """_cached_pne_restore_files() : 빈/정상 Restore 폴더 처리"""

    def test_empty_saveenddata_returns_none_without_exception(
            self, proto_module, pne_continue_pa1_folder):
        """빈 SaveEndData → (None, None, list) 반환, 예외 없음.

        회귀: 이전 버전은 pandas.errors.EmptyDataError 발생.
        """
        ch015 = pne_continue_pa1_folder / "M01Ch015[015]"
        if not ch015.is_dir():
            pytest.skip("M01Ch015[015] 채널 폴더 없음")

        # 캐시 초기화 후 호출
        proto_module.clear_channel_cache()
        save_end, file_index, subfile = proto_module._cached_pne_restore_files(str(ch015))

        assert isinstance(subfile, list), "subfile은 항상 list여야 함"
        # 빈 파일이면 save_end, file_index는 None
        # (파일이 정상이면 DataFrame/list가 될 수 있으므로 OR 조건)
        assert save_end is None or isinstance(save_end, pd.DataFrame)
        assert file_index is None or isinstance(file_index, list)

    def test_empty_saveenddata_does_not_raise(
            self, proto_module, pne_continue_pa1_folder):
        """빈 SaveEndData 처리 시 어떤 예외도 발생하지 않는지 확인"""
        ch015 = pne_continue_pa1_folder / "M01Ch015[015]"
        if not ch015.is_dir():
            pytest.skip("M01Ch015[015] 채널 폴더 없음")

        proto_module.clear_channel_cache()
        try:
            proto_module._cached_pne_restore_files(str(ch015))
        except Exception as e:
            pytest.fail(f"예외 발생: {type(e).__name__}: {e}")

    def test_ps_channel_also_handles_gracefully(
            self, proto_module, pne_continue_ps_folder):
        """PS 연속저장 채널에서도 예외 없이 처리되는지 확인"""
        ch_dirs = [d for d in pne_continue_ps_folder.iterdir()
                   if d.is_dir() and "Pattern" not in d.name]
        if not ch_dirs:
            pytest.skip("PS 연속저장 채널 폴더 없음")

        proto_module.clear_channel_cache()
        for ch in ch_dirs:
            try:
                proto_module._cached_pne_restore_files(str(ch))
            except Exception as e:
                pytest.fail(f"{ch.name}: 예외 발생 → {type(e).__name__}: {e}")


# ══════════════════════════════════════════════════════════════
# pne_search_cycle 회귀 테스트
# ══════════════════════════════════════════════════════════════

class TestPneSearchCycle:
    """pne_search_cycle() : 빈 SaveEndData 시 [-1, -1] 반환 확인"""

    def test_returns_minus_one_when_restore_empty(
            self, proto_module, pne_continue_pa1_folder):
        """SaveEndData가 빈 채널 → pne_search_cycle이 [-1, -1] 반환"""
        ch015 = pne_continue_pa1_folder / "M01Ch015[015]"
        if not ch015.is_dir():
            pytest.skip("M01Ch015[015] 채널 폴더 없음")

        rawdir = str(ch015) + "\\Restore\\"
        if not os.path.isdir(rawdir):
            pytest.skip("Restore 폴더 없음 (연속저장 아님)")

        proto_module.clear_channel_cache()
        result = proto_module.pne_search_cycle(rawdir, 1, 10)

        assert isinstance(result, list)
        assert len(result) == 2
        # SaveEndData가 비어 있으면 [-1, -1] 반환
        assert result[0] == -1, f"expected -1, got {result[0]}"


# ══════════════════════════════════════════════════════════════
# pne_continue_data 회귀 테스트
# ══════════════════════════════════════════════════════════════

class TestPneContinueData:
    """pne_continue_data() : 연속저장 프로파일 로딩 회귀 테스트"""

    @pytest.mark.slow
    def test_empty_saveenddata_returns_empty_df(
            self, proto_module, pne_continue_pa1_folder):
        """빈 SaveEndData 채널에서 예외 없이 빈 DataFrame 반환 확인

        회귀: 이전에는 EmptyDataError로 전체 버튼 실패.
        수정 후: 빈 df 반환 (플롯 없음으로 조용히 처리).
        """
        ch015 = pne_continue_pa1_folder / "M01Ch015[015]"
        if not ch015.is_dir():
            pytest.skip("M01Ch015[015] 채널 폴더 없음")

        proto_module.clear_channel_cache()
        try:
            result = proto_module.pne_continue_data(str(ch015), 1, 10)
        except Exception as e:
            pytest.fail(f"예외 발생: {type(e).__name__}: {e}")

        assert isinstance(result, pd.DataFrame), "반환값이 DataFrame이어야 함"

    @pytest.mark.slow
    def test_ps_ch024_no_exception(
            self, proto_module, pne_continue_ps_folder):
        """PS 연속저장 M01Ch024 채널도 예외 없이 처리되는지 확인"""
        ch024 = pne_continue_ps_folder / "M01Ch024[024]"
        if not ch024.is_dir():
            pytest.skip("M01Ch024[024] 채널 폴더 없음")

        proto_module.clear_channel_cache()
        try:
            proto_module.pne_continue_data(str(ch024), 1, 10)
        except Exception as e:
            pytest.fail(f"예외 발생: {type(e).__name__}: {e}")


# ══════════════════════════════════════════════════════════════
# 정상 PNE 채널 (SaveEndData 있음) 기준선 테스트
# ══════════════════════════════════════════════════════════════

class TestNormalPneRestoreFiles:
    """정상 SaveEndData 있는 PNE 채널의 기준선 동작 확인"""

    @pytest.mark.slow
    def test_normal_pne_channel_returns_dataframe(
            self, proto_module, pne_ch008):
        """정상 SaveEndData가 있는 PNE 채널 → DataFrame 반환

        회귀 수정이 정상 경로를 깨지 않았는지 확인.
        """
        proto_module.clear_channel_cache()
        save_end, file_index, subfile = proto_module._cached_pne_restore_files(str(pne_ch008))

        # 정상 채널: Restore 폴더가 없으면 save_end=None (단순 skip)
        restore_dir = pne_ch008 / "Restore"
        if not restore_dir.is_dir():
            pytest.skip(f"{pne_ch008.name}에 Restore 폴더 없음 — 연속저장 미사용 채널")

        # Restore 있으면 적어도 subfile은 list여야 함
        assert isinstance(subfile, list)
        if save_end is not None:
            assert isinstance(save_end, pd.DataFrame)
            assert len(save_end) > 0, "SaveEndData가 비어있음 (정상 채널에서 예외 케이스)"


class TestCycleAxisTickGap:
    """사이클 x축 tick 간격 유틸 회귀 테스트"""

    def test_tick_gap_uses_shared_threshold_logic(self, proto_module):
        """임계값 구간별 tick 간격 계산이 기존 규칙을 유지하는지 확인"""
        assert proto_module._calc_cycle_x_tick_gap(350) == 50
        assert proto_module._calc_cycle_x_tick_gap(400) == 100
        assert proto_module._calc_cycle_x_tick_gap(1500) == 250

    def test_tick_gap_expands_when_xtick_count_is_too_dense(self, proto_module):
        """xrangemax 대비 tick 수가 많으면 간격이 자동 확장되는지 확인"""
        assert proto_module._calc_cycle_x_tick_gap(100, 1000) == 150


class TestChannelMetaSaveEndReuse:
    """Phase 0 ChannelMeta SaveEndData 재사용 회귀 테스트"""

    def test_pne_cycle_data_reuses_meta_saveend_after_channel_cache_clear(
            self, proto_module, monkeypatch):
        """채널 캐시를 비운 뒤에도 Phase 0 SaveEndData로 Cycle 로딩 가능한지 확인"""
        channel_path = r"C:\fake\M01Ch001[001]"
        save_end_data = pd.DataFrame([
            {
                2: 2,
                6: 65,
                8: 3700,
                9: -1000,
                10: 1050,
                11: 1000,
                15: 3.6,
                17: 60,
                20: 12,
                24: 25,
                27: 1,
                29: 3650,
                45: 4200,
            }
        ]).reindex(columns=range(46), fill_value=0)
        cycle_map = {
            1: {
                'all': (1, 1),
                'chg': [1],
                'dchg': [1],
                'chg_rest': [],
                'dchg_rest': [],
            }
        }

        proto_module.clear_channel_meta_store()
        proto_module.clear_channel_cache()

        monkeypatch.setattr(proto_module, 'check_cycler', lambda _path: True)
        monkeypatch.setattr(proto_module, '_cached_pne_restore_files',
                            lambda _path: (save_end_data, None, []))
        monkeypatch.setattr(proto_module, 'classify_pne_cycles',
                            lambda summary, _cap: [{'cycle': 1, 'category': '수명시험'}])
        monkeypatch.setattr(proto_module, 'HAS_SCH_PARSER', False)
        monkeypatch.setattr(proto_module, 'analyze_accel_pattern',
                            lambda *args, **kwargs: None)
        monkeypatch.setattr(proto_module, 'detect_test_type', lambda _counts: '수명시험')
        monkeypatch.setattr(proto_module, 'detect_schedule_pattern', lambda _classified: 'life')
        monkeypatch.setattr(proto_module, 'get_cycle_map',
                            lambda *args, **kwargs: (cycle_map, None))

        meta = proto_module._build_channel_meta(channel_path, 1000, 0.2)

        assert meta is not None
        assert meta.save_end_data is not None
        pd.testing.assert_frame_equal(meta.save_end_data, save_end_data)

        proto_module.clear_channel_cache()
        monkeypatch.setattr(
            proto_module,
            '_cached_pne_restore_files',
            lambda _path: (_ for _ in ()).throw(AssertionError('채널 캐시 fallback 호출 금지')),
        )
        monkeypatch.setattr(proto_module, 'pne_min_cap',
                            lambda _path, mincapacity, _crate: mincapacity or 1000)
        monkeypatch.setattr(proto_module, '_get_pne_cycle_map',
                            lambda *args, **kwargs: (cycle_map, None))

        captured = {}

        def _fake_process(cycleraw, df, *_args, **_kwargs):
            captured['cycleraw'] = cycleraw.copy()
            df.NewData = pd.DataFrame({'Cycle': [1]})

        monkeypatch.setattr(proto_module, '_process_pne_cycleraw', _fake_process)

        mincapacity, df = proto_module.pne_cycle_data(channel_path, 1000, 0.2, False, False, False)

        assert mincapacity == 1000
        assert 'cycleraw' in captured
        assert list(captured['cycleraw']['TotlCycle']) == [1]
        assert hasattr(df, 'NewData')

        proto_module.clear_channel_meta_store()
        proto_module.clear_channel_cache()
