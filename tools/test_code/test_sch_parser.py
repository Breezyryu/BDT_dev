"""PNE .sch 내장 바이너리 파서 테스트.

테스트 대상:
  - _parse_pne_sch(): 바이너리 구조 파싱
  - extract_accel_pattern_from_sch(): 가속수명 패턴 추출
  - extract_schedule_structure_from_sch(): 시험유형 판별
"""
import os
import sys
import struct
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'DataTool_dev'))

# proto_.py에서 파서 함수만 임포트
from DataTool_optRCD_proto_ import (
    _parse_pne_sch,
    extract_accel_pattern_from_sch,
    extract_schedule_structure_from_sch,
    _SCH_BLOCK_SIZE,
    _SCH_HEADER_SIZE,
)

TEST_DIR = os.path.dirname(__file__)
ACCEL_SCH = os.path.join(TEST_DIR, 'test_data_accel.sch')
GITT_SCH = os.path.join(TEST_DIR, 'test_data_gitt.sch')


# ─────────────────────────────────────────
# _parse_pne_sch 기본 동작
# ─────────────────────────────────────────

class TestParsePneSchedule:
    """_parse_pne_sch() 바이너리 파싱 테스트."""

    def test_accel_basic_structure(self):
        """가속수명 .sch: 52스텝 (화성+RPT+메인+후RPT+RSS)."""
        result = _parse_pne_sch(ACCEL_SCH)
        assert result is not None
        assert len(result['steps']) == 52
        assert len(result['charge_steps']) == 10   # 5화성+2RPT+1메인+2후RPT
        assert len(result['discharge_steps']) == 15  # 5화성+2RPT+1메인+2후RPT+5RSS
        assert len(result['loop_steps']) == 2      # 화성(5회)+메인(50회)

    def test_accel_step_types_start(self):
        """처음 5스텝의 타입이 올바르게 식별되어야 함 (화성 첫사이클)."""
        result = _parse_pne_sch(ACCEL_SCH)
        types = [s['type'] for s in result['steps'][:5]]
        assert types == ['CHG_CCCV', 'REST', 'DCHG_CC', 'REST', 'CHG_CCCV']

    def test_accel_charge_params(self):
        """메인 가속수명 CHG_CCCV 스텝: 전류 1167mA, 전압 4200mV."""
        result = _parse_pne_sch(ACCEL_SCH)
        # 화성(5)+RPT(2) 이후 8번째가 메인 충전 (index 7)
        main_chg = result['charge_steps'][7]
        assert main_chg['type'] == 'CHG_CCCV'
        assert main_chg['current_mA'] == 1167
        assert main_chg['voltage_mV'] == 4200
        assert main_chg['cv_cutoff_mA'] == 117

    def test_accel_discharge_params(self):
        """메인 가속수명 DCHG_CC 스텝: 전류 2335mA, 전압 2500mV."""
        result = _parse_pne_sch(ACCEL_SCH)
        # 화성(5)+RPT(2) 이후 8번째가 메인 방전 (index 7)
        main_dchg = result['discharge_steps'][7]
        assert main_dchg['type'] == 'DCHG_CC'
        assert main_dchg['current_mA'] == 2335
        assert main_dchg['voltage_mV'] == 2500

    def test_accel_loop_count(self):
        """메인 LOOP 스텝: 50회 반복 (화성 루프 5회 + 메인 50회)."""
        result = _parse_pne_sch(ACCEL_SCH)
        assert result['loop_steps'][0]['loop_count'] == 5   # 화성
        assert result['loop_steps'][1]['loop_count'] == 50  # 메인

    def test_gitt_basic_structure(self):
        """GITT .sch: 4스텝 (REST, DCHG_CC, REST, LOOP)."""
        result = _parse_pne_sch(GITT_SCH)
        assert result is not None
        assert len(result['steps']) == 4
        assert len(result['charge_steps']) == 0
        assert len(result['discharge_steps']) == 1
        assert len(result['loop_steps']) == 1

    def test_gitt_loop_count(self):
        """GITT: 대형 루프 105회."""
        result = _parse_pne_sch(GITT_SCH)
        assert result['loop_steps'][0]['loop_count'] == 105

    def test_invalid_path_returns_none(self):
        """존재하지 않는 파일 → None."""
        assert _parse_pne_sch('/nonexistent/file.sch') is None

    def test_too_small_file_returns_none(self):
        """헤더보다 작은 파일 → None."""
        # 임시 파일 생성 (100 bytes)
        tmp = os.path.join(TEST_DIR, '_tmp_small.sch')
        try:
            with open(tmp, 'wb') as f:
                f.write(b'\x00' * 100)
            assert _parse_pne_sch(tmp) is None
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def test_wrong_magic_returns_none(self):
        """매직 넘버 불일치 → None."""
        tmp = os.path.join(TEST_DIR, '_tmp_badmagic.sch')
        try:
            data = bytearray(_SCH_HEADER_SIZE + _SCH_BLOCK_SIZE)
            struct.pack_into('<I', data, 0, 999999)  # 잘못된 매직
            with open(tmp, 'wb') as f:
                f.write(data)
            assert _parse_pne_sch(tmp) is None
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)


# ─────────────────────────────────────────
# extract_accel_pattern_from_sch
# ─────────────────────────────────────────

class TestExtractAccelPattern:
    """extract_accel_pattern_from_sch() 가속수명 패턴 추출 테스트."""

    def test_accel_pattern_extraction(self):
        """가속수명 패턴: 충전 1스텝 + 방전 1스텝 추출."""
        result = extract_accel_pattern_from_sch(ACCEL_SCH, capacity=2335)
        assert result is not None
        assert result['n_charge_steps'] == 1
        assert result['n_discharge_steps'] == 1

    def test_accel_charge_crate(self):
        """충전 C-rate: 1167 / 2335 ≈ 0.5C."""
        result = extract_accel_pattern_from_sch(ACCEL_SCH, capacity=2335)
        chg = result['charge_steps'][0]
        assert chg['mode'] == 'CCCV'
        assert chg['crate'] == 0.5

    def test_accel_discharge_crate(self):
        """방전 C-rate: 2335 / 2335 = 1.0C."""
        result = extract_accel_pattern_from_sch(ACCEL_SCH, capacity=2335)
        dchg = result['discharge_steps'][0]
        assert dchg['mode'] == 'CC'
        assert dchg['crate'] == 1.0

    def test_accel_cutoff_voltage(self):
        """충전 cutoff 4.2V, 방전 cutoff 2.5V."""
        result = extract_accel_pattern_from_sch(ACCEL_SCH, capacity=2335)
        assert result['charge_steps'][0]['voltage_cutoff'] == 4.2
        assert result['discharge_steps'][0]['voltage_cutoff'] == 2.5

    def test_accel_cv_cutoff(self):
        """CCCV 충전의 CV cutoff 전류."""
        result = extract_accel_pattern_from_sch(ACCEL_SCH, capacity=2335)
        chg = result['charge_steps'][0]
        assert 'current_cutoff_mA' in chg
        assert chg['current_cutoff_mA'] == 117
        assert chg['current_cutoff_crate'] == 0.05

    def test_gitt_no_accel_pattern(self):
        """GITT 스케줄은 루프 전 방전 1개만 → 패턴 반환은 됨."""
        result = extract_accel_pattern_from_sch(GITT_SCH, capacity=2335)
        # GITT에도 루프 전 DCHG가 있으므로 패턴이 있음
        assert result is not None
        assert result['n_discharge_steps'] == 1


# ─────────────────────────────────────────
# extract_schedule_structure_from_sch
# ─────────────────────────────────────────

class TestExtractScheduleStructure:
    """extract_schedule_structure_from_sch() 시험유형 판별 테스트."""

    def test_accel_schedule_type(self):
        """가속수명 스케줄 → schedule_type = '가속수명'."""
        result = extract_schedule_structure_from_sch(ACCEL_SCH, capacity=2335)
        assert result is not None
        assert result['schedule_type'] == '가속수명'
        assert result['sweep_mode'] is False  # 일반 모드

    def test_gitt_schedule_type(self):
        """GITT 스케줄 → schedule_type = 'GITT'."""
        result = extract_schedule_structure_from_sch(GITT_SCH, capacity=2335)
        assert result is not None
        assert result['schedule_type'] == 'GITT'
        assert result['sweep_mode'] is True  # 스윕 모드
        assert result['has_gitt_hppc'] is True

    def test_accel_pattern_string(self):
        """패턴 문자열이 비어있지 않아야 함."""
        result = extract_schedule_structure_from_sch(ACCEL_SCH)
        assert len(result['pattern_string']) > 0

    def test_invalid_path_returns_none(self):
        """존재하지 않는 파일 → None."""
        result = extract_schedule_structure_from_sch('/nonexistent.sch')
        assert result is None
