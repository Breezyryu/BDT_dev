"""PNE .sch 바이너리 스케줄 파일 파서

PNE 충방전기 스케줄 파일(.sch)의 바이너리 구조를 직접 파싱하여
의도된 충전/방전 조건(전압·전류·모드)을 추출한다.

바이너리 구조 (교차 검증 완료, 44개 스케줄 895개 블록):
  - 오프셋 0~15   : 매직 헤더 (4 × uint32)
  - 오프셋 72~103  : ASCII 식별자 "PNE power supply schedule file"
  - 오프셋 1920    : 스텝 블록 시작
  - 각 블록 652바이트 고정
"""

__all__ = [
    "parse_pne_schedule",
    "extract_accel_pattern_from_sch",
    "extract_schedule_structure_from_sch",
]

import logging
import struct
from pathlib import Path

logger = logging.getLogger(__name__)

# ── 상수 ──────────────────────────────────────────────────────────

# 파일 헤더
MAGIC = (740721, 131077, 50, 0)
HEADER_SIZE = 1920       # 스텝 블록 시작 오프셋 (바이트)
BLOCK_SIZE = 652          # 스텝 블록 크기 (바이트)

# 타입 코드
TYPE_CHG_CC   = 0x0101    # 정전류 충전
TYPE_CHG_CCCV = 0x0201    # 정전류정전압 충전
TYPE_DCHG_CC  = 0x0202    # 정전류 방전
TYPE_REST     = 0xFF03    # 시간 기반 휴지
TYPE_GOTO     = 0xFF06    # 무조건 점프
TYPE_REST_SAFE = 0xFF07   # 안전조건 휴지
TYPE_LOOP     = 0xFF08    # 반복

TYPE_NAMES = {
    TYPE_CHG_CC:    "CHG_CC",
    TYPE_CHG_CCCV:  "CHG_CCCV",
    TYPE_DCHG_CC:   "DCHG_CC",
    TYPE_REST:      "REST",
    TYPE_GOTO:      "GOTO",
    TYPE_REST_SAFE: "REST_SAFE",
    TYPE_LOOP:      "LOOP",
}

# 충전/방전 타입 집합
CHG_TYPES = {TYPE_CHG_CC, TYPE_CHG_CCCV}
DCHG_TYPES = {TYPE_DCHG_CC}


# ── 내부 유틸 ────────────────────────────────────────────────────

def _f32(block: bytes, offset: int) -> float:
    """블록 내 offset에서 float32(little-endian) 읽기."""
    return struct.unpack_from("<f", block, offset)[0]


def _u32(block: bytes, offset: int) -> int:
    """블록 내 offset에서 uint32(little-endian) 읽기."""
    return struct.unpack_from("<I", block, offset)[0]


def _is_nonzero_f32(val: float) -> bool:
    """float32 값이 유효한(0이 아닌) 값인지 판단."""
    return abs(val) > 1e-9


# ── 블록 파싱 ────────────────────────────────────────────────────

def _parse_chg_cc(block: bytes) -> dict:
    """CHG_CC (0x0101) 블록에서 충전 조건 추출.

    필드 맵:
      +12 : voltage_cutoff (mV)
      +20 : cc_current (mA)
      +24 : time_limit (s) — 선택
      +32 : cv_cutoff_current (mA) — CC에서도 CV전환 기준 전류 설정
      +104: capacity_limit (mAh)
      +336: recording_interval (s)
    """
    voltage_mv = _f32(block, 12)
    current_ma = _f32(block, 20)
    time_limit = _f32(block, 24)
    cv_cutoff = _f32(block, 32)
    cap_limit = _f32(block, 104)

    step = {
        "type": "CHG_CC",
        "voltage_cutoff_mV": voltage_mv,
        "current_mA": current_ma,
        "capacity_limit_mAh": cap_limit,
    }

    # 시간 한도가 유효하면 추가
    if _is_nonzero_f32(time_limit):
        step["time_limit_s"] = time_limit

    # CV cutoff 전류가 유효하면 추가
    if _is_nonzero_f32(cv_cutoff):
        step["cv_cutoff_mA"] = cv_cutoff

    return step


def _parse_chg_cccv(block: bytes) -> dict:
    """CHG_CCCV (0x0201) 블록에서 충전 조건 추출.

    필드 맵:
      +12 : voltage_cutoff (mV) — CC구간 상한 전압
      +20 : cc_current (mA)
      +24 : time_limit (s) — 선택
      +28 : cv_voltage (mV) — CV구간 유지 전압
      +104: capacity_limit (mAh)
    """
    voltage_mv = _f32(block, 12)
    current_ma = _f32(block, 20)
    time_limit = _f32(block, 24)
    cv_voltage = _f32(block, 28)
    cap_limit = _f32(block, 104)

    step = {
        "type": "CHG_CCCV",
        "voltage_cutoff_mV": voltage_mv,
        "current_mA": current_ma,
        "cv_voltage_mV": cv_voltage,
        "capacity_limit_mAh": cap_limit,
    }

    if _is_nonzero_f32(time_limit):
        step["time_limit_s"] = time_limit

    return step


def _parse_dchg_cc(block: bytes) -> dict:
    """DCHG_CC (0x0202) 블록에서 방전 조건 추출.

    필드 맵 (주의: 전압 오프셋이 CHG와 다름):
      +16 : voltage_cutoff (mV) — 방전 하한 전압
      +20 : dchg_current (mA)
      +24 : time_limit (s) — 선택
      +104: capacity_limit (mAh)
    """
    voltage_mv = _f32(block, 16)
    current_ma = _f32(block, 20)
    time_limit = _f32(block, 24)
    cap_limit = _f32(block, 104)

    step = {
        "type": "DCHG_CC",
        "voltage_cutoff_mV": voltage_mv,
        "current_mA": current_ma,
        "capacity_limit_mAh": cap_limit,
    }

    if _is_nonzero_f32(time_limit):
        step["time_limit_s"] = time_limit

    return step


def _parse_rest(block: bytes) -> dict:
    """REST (0xFF03) 블록에서 휴지 조건 추출.

    필드 맵:
      +24 : rest_duration (s)
      +336: recording_interval (s)
    """
    duration = _f32(block, 24)
    return {
        "type": "REST",
        "duration_s": duration if _is_nonzero_f32(duration) else 0.0,
    }


def _parse_loop(block: bytes) -> dict:
    """LOOP (0xFF08) 블록에서 반복 조건 추출.

    필드 맵:
      +56 : loop_count (uint32) — 반복 횟수
      +580: target_step (uint32) — 점프 대상 (추정)
    """
    loop_count = _u32(block, 56)
    target_step = _u32(block, 580)
    return {
        "type": "LOOP",
        "loop_count": loop_count,
        "target_step": target_step,
    }


def _parse_goto(block: bytes) -> dict:
    """GOTO (0xFF06) 블록 — 구조 미상, 기본 정보만."""
    return {"type": "GOTO"}


def _parse_rest_safe(block: bytes) -> dict:
    """REST_SAFE (0xFF07) 블록 — 안전조건 휴지."""
    duration = _f32(block, 24)
    return {
        "type": "REST_SAFE",
        "duration_s": duration if _is_nonzero_f32(duration) else 0.0,
    }


# 타입별 파서 디스패치
_PARSERS = {
    TYPE_CHG_CC:    _parse_chg_cc,
    TYPE_CHG_CCCV:  _parse_chg_cccv,
    TYPE_DCHG_CC:   _parse_dchg_cc,
    TYPE_REST:      _parse_rest,
    TYPE_LOOP:      _parse_loop,
    TYPE_GOTO:      _parse_goto,
    TYPE_REST_SAFE: _parse_rest_safe,
}


# ── 공개 API ─────────────────────────────────────────────────────

def parse_pne_schedule(sch_path: str | Path) -> dict | None:
    """PNE .sch 바이너리 파일을 파싱하여 스케줄 정보를 반환.

    Parameters
    ----------
    sch_path : str | Path
        .sch 파일 경로

    Returns
    -------
    dict | None
        파싱 성공 시:
        {
            'file': str,
            'total_steps': int,
            'steps': [
                {'step_num': 1, 'type': 'CHG_CC', 'voltage_cutoff_mV': ..., ...},
                ...
            ],
            'charge_steps': [충전 스텝만 필터링],
            'discharge_steps': [방전 스텝만 필터링],
            'loop_steps': [LOOP 스텝만 필터링],
            'capacity_limit_mAh': float,  # 첫 충전/방전 스텝의 용량한도
            'estimated_nameplate_mAh': float,  # capacity_limit / 1.1
        }
        실패 시 None
    """
    sch_path = Path(sch_path)

    if not sch_path.is_file():
        logger.warning("파일 없음: %s", sch_path)
        return None

    data = sch_path.read_bytes()

    # 매직 헤더 검증
    if len(data) < HEADER_SIZE:
        logger.warning("파일 크기 부족: %s (%d bytes)", sch_path.name, len(data))
        return None

    magic = struct.unpack_from("<4I", data, 0)
    if magic != MAGIC:
        logger.warning("매직 헤더 불일치: %s → %s", sch_path.name, magic)
        return None

    # 스텝 블록 수 계산
    body = len(data) - HEADER_SIZE
    if body % BLOCK_SIZE != 0:
        logger.warning(
            "블록 정합성 오류: %s (body=%d, remainder=%d)",
            sch_path.name, body, body % BLOCK_SIZE,
        )
        return None

    total_steps = body // BLOCK_SIZE
    steps = []

    for i in range(total_steps):
        offset = HEADER_SIZE + i * BLOCK_SIZE
        block = data[offset:offset + BLOCK_SIZE]

        step_num = _u32(block, 0)
        type_code = _u32(block, 8)

        parser = _PARSERS.get(type_code)
        if parser is None:
            logger.debug("미지 타입 코드 0x%04X (step %d)", type_code, step_num)
            step_info = {"type": f"UNKNOWN_0x{type_code:04X}"}
        else:
            step_info = parser(block)

        step_info["step_num"] = step_num
        steps.append(step_info)

    # 충전/방전/루프 분류
    charge_steps = [s for s in steps if s["type"] in ("CHG_CC", "CHG_CCCV")]
    discharge_steps = [s for s in steps if s["type"] == "DCHG_CC"]
    loop_steps = [s for s in steps if s["type"] == "LOOP"]

    # 대표 용량한도 추출 (첫 충전 또는 방전 스텝에서)
    cap_limit = 0.0
    for s in charge_steps + discharge_steps:
        cl = s.get("capacity_limit_mAh", 0.0)
        if cl > 0:
            cap_limit = cl
            break

    result = {
        "file": sch_path.name,
        "total_steps": total_steps,
        "steps": steps,
        "charge_steps": charge_steps,
        "discharge_steps": discharge_steps,
        "loop_steps": loop_steps,
        "capacity_limit_mAh": cap_limit,
        "estimated_nameplate_mAh": round(cap_limit / 1.1, 1) if cap_limit > 0 else 0.0,
    }

    logger.debug(
        "%s: %d steps (CHG=%d, DCHG=%d, LOOP=%d)",
        sch_path.name, total_steps,
        len(charge_steps), len(discharge_steps), len(loop_steps),
    )

    return result


def extract_accel_pattern_from_sch(
    sch_path: str | Path,
    capacity: float = 0,
) -> dict | None:
    """_analyze_accel_pattern_pne() 호환 형태로 .sch에서 가속수명 패턴 추출.

    기존 CSV 기반 분석(`_analyze_accel_pattern_pne`)과 동일한 딕셔너리 형태를
    반환하되, .sch에서 직접 읽은 **의도된(설계) 값**을 사용한다.

    Parameters
    ----------
    sch_path : str | Path
        .sch 파일 경로
    capacity : float
        공칭 용량(mAh). 폴더명에서 파싱한 값 필수.
        0 이하이면 C-rate 계산 불가로 None 반환.

    Returns
    -------
    dict | None
        {
            'charge_steps': [{'step', 'mode', 'crate', 'current_mA', ...}, ...],
            'discharge_steps': [...],
            'n_charge_steps': int,
            'n_discharge_steps': int,
            'source': 'sch',
        }
    """
    parsed = parse_pne_schedule(sch_path)
    if parsed is None:
        return None

    # 공칭 용량 검증 (폴더명 파싱값 필수, .sch capacity_limit 참조 안 함)
    if capacity <= 0:
        logger.warning("용량 미제공 — 폴더명에서 파싱한 용량이 필요합니다: %s", sch_path)
        return None

    # ── 가속수명 구간 찾기 ──
    # 전략: "초기 RPT 이후, LOOP 직전까지의 충전+방전 스텝"을
    # 가속수명 사이클로 간주. LOOP가 가속수명 반복 구간을 감싸는 패턴.
    #
    # 일반적 PNE 스케줄 구조:
    #   [초기 DCHG → REST → LOOP(초기RPT)] → [REST_SAFE]
    #   → [CHG → REST → DCHG → REST → ...] → [LOOP(가속수명)]
    #
    # 마지막 LOOP 직전의 충전/방전 시퀀스가 "가속수명 1사이클 패턴"

    steps = parsed["steps"]
    if not steps:
        return None

    # 마지막 LOOP 찾기 (가장 긴 반복 = 가속수명)
    last_loop_idx = None
    max_loop_count = 0
    for i, s in enumerate(steps):
        if s["type"] == "LOOP":
            lc = s.get("loop_count", 0)
            if lc >= max_loop_count:
                max_loop_count = lc
                last_loop_idx = i

    if last_loop_idx is None:
        # LOOP가 없는 스케줄 (단발성 포메이션 등)
        # 전체 충/방전 스텝을 반환
        return _build_pattern_result(
            parsed["charge_steps"],
            parsed["discharge_steps"],
            capacity,
        )

    # 마지막 LOOP 직전 구간에서 가속수명 충/방전 스텝 추출
    # REST_SAFE 직후 ~ LOOP 직전 범위 검색
    accel_start = 0
    for i in range(last_loop_idx - 1, -1, -1):
        if steps[i]["type"] in ("REST_SAFE", "LOOP"):
            accel_start = i + 1
            break

    accel_region = steps[accel_start:last_loop_idx]
    chg = [s for s in accel_region if s["type"] in ("CHG_CC", "CHG_CCCV")]
    dchg = [s for s in accel_region if s["type"] == "DCHG_CC"]

    if not chg and not dchg:
        return None

    return _build_pattern_result(chg, dchg, capacity)


def _build_pattern_result(
    chg_steps: list[dict],
    dchg_steps: list[dict],
    capacity: float,
) -> dict:
    """충전/방전 스텝 리스트를 analyze_accel_pattern 호환 딕셔너리로 변환."""
    charge_out = []
    for idx, s in enumerate(chg_steps):
        current = s.get("current_mA", 0)
        voltage = s.get("voltage_cutoff_mV", 0)

        entry = {
            "step": idx + 1,
            "current_mA": round(current, 1),
            "voltage_cutoff": round(voltage / 1000, 3),
        }

        if s["type"] == "CHG_CCCV":
            entry["mode"] = "CCCV"
            cv_v = s.get("cv_voltage_mV", 0)
            if cv_v > 0:
                entry["cv_voltage"] = round(cv_v / 1000, 3)
            entry["crate"] = round(current / capacity, 2) if capacity else 0
        else:
            # CHG_CC
            cv_cutoff = s.get("cv_cutoff_mA", 0)
            if cv_cutoff > 0 and cv_cutoff < current:
                # CC 모드이지만 CV cutoff이 설정됨 → 실질 CCCV
                entry["mode"] = "CCCV"
                entry["crate"] = round(current / capacity, 2) if capacity else 0
                entry["current_cutoff_crate"] = (
                    round(cv_cutoff / capacity, 2) if capacity else 0
                )
                entry["current_cutoff_mA"] = round(cv_cutoff, 1)
            else:
                entry["mode"] = "CC"
                entry["crate"] = round(current / capacity, 2) if capacity else 0

        charge_out.append(entry)

    discharge_out = []
    for idx, s in enumerate(dchg_steps):
        current = s.get("current_mA", 0)
        voltage = s.get("voltage_cutoff_mV", 0)

        discharge_out.append({
            "step": idx + 1,
            "mode": "CC",
            "crate": round(current / capacity, 2) if capacity else 0,
            "current_mA": round(current, 1),
            "voltage_cutoff": round(voltage / 1000, 3),
        })

    return {
        "charge_steps": charge_out,
        "discharge_steps": discharge_out,
        "n_charge_steps": len(charge_out),
        "n_discharge_steps": len(discharge_out),
        "source": "sch",
    }


# ── 스케줄 구조 분석 ─────────────────────────────────────────────

# 구간 분류 임계값
_ACCEL_LOOP_MIN = 20       # 가속수명 LOOP 최소 횟수 (SEU4:98~99, Gen4p:47)
_RATE_LOOP_MIN = 5         # Rate 테스트 LOOP 최소 횟수
_PULSE_STEP_MIN = 5        # Rss/DCIR 펄스 구간 최소 충·방전 스텝 수
_GITT_HPPC_LOOP_MIN = 10   # GITT/HPPC LOOP 최소 횟수


def _classify_section(n_chg: int, n_dchg: int, n_rest: int,
                      loop_count: int, has_loop: bool) -> str:
    """LOOP 구간의 충/방전 구성으로 카테고리 추정.

    분류 규칙 (우선순위 순):
      1) 가속수명: LOOP ≥ 20 & (CHG ≥ 2 or DCHG ≥ 1)
      2) Rate:     LOOP ≥ 5 & CHG ≥ 2 & DCHG ≥ 2
      3) Rss/DCIR: LOOP = 1 & (CHG ≥ 5 or DCHG ≥ 5)
      4) GITT/HPPC: LOOP ≥ 10 & (CHG + DCHG ≤ 3)
      5) RPT:      LOOP = 1 & CHG = 1 & DCHG = 1
      6) 초기방전:  LOOP 없음 & DCHG ≥ 1 & CHG = 0
      7) 구간경계:  REST_SAFE만 (LOOP 없음)
    """
    if not has_loop:
        if n_dchg >= 1 and n_chg == 0 and n_rest == 0:
            return "초기방전"
        return "구간경계"

    # 가속수명: 대량 반복
    if loop_count >= _ACCEL_LOOP_MIN and (n_chg >= 2 or n_dchg >= 1):
        return "가속수명"

    # Rate: 다항목 충방전 + 중간 반복
    if loop_count >= _RATE_LOOP_MIN and n_chg >= 2 and n_dchg >= 2:
        return "Rate"

    # GITT/HPPC: 적은 스텝 + 큰 반복
    if loop_count >= _GITT_HPPC_LOOP_MIN and (n_chg + n_dchg) <= 3:
        return "GITT/HPPC"

    # Rss/DCIR 펄스: 단일 반복 + 다수 충·방전
    if loop_count <= 2 and (n_chg >= _PULSE_STEP_MIN or n_dchg >= _PULSE_STEP_MIN):
        return "Rss/DCIR"

    # RPT: 단일 충방전 쌍
    if loop_count <= 2 and n_chg == 1 and n_dchg == 1:
        return "RPT"

    # 단일구간 (LOOP=1, 소수 스텝)
    if loop_count <= 2:
        return "단일구간"

    return "기타"


def _split_sections(steps: list[dict]) -> list[dict]:
    """REST_SAFE / LOOP 기준으로 구간 분할."""
    sections = []
    buf = []
    for s in steps:
        buf.append(s)
        if s["type"] in ("LOOP", "REST_SAFE"):
            sections.append(list(buf))
            buf = []
    if buf:
        sections.append(list(buf))

    result = []
    for sec in sections:
        types = [x["type"] for x in sec]
        n_chg = sum(1 for t in types if t.startswith("CHG"))
        n_dchg = sum(1 for t in types if t == "DCHG_CC")
        n_rest = sum(1 for t in types if t.startswith("REST"))
        loop_items = [x for x in sec if x["type"] == "LOOP"]
        has_loop = bool(loop_items)
        lc = loop_items[0]["loop_count"] if loop_items else 0
        target = loop_items[0]["target_step"] if loop_items else 0

        cat = _classify_section(n_chg, n_dchg, n_rest, lc, has_loop)

        # 대표 전류/전압 수집
        currents = []
        for x in sec:
            if x["type"] in ("CHG_CC", "CHG_CCCV", "DCHG_CC"):
                currents.append({
                    "type": x["type"],
                    "current_mA": x.get("current_mA", 0),
                })

        result.append({
            "n_steps": len(sec),
            "n_chg": n_chg,
            "n_dchg": n_dchg,
            "n_rest": n_rest,
            "loop_count": lc,
            "target_step": target,
            "category": cat,
            "currents": currents,
        })
    return result


def extract_schedule_structure_from_sch(
    sch_path: str | Path,
    capacity: float = 0,
) -> dict | None:
    """LOOP 구조 분석으로 스케줄 설계 의도를 추출.

    Parameters
    ----------
    sch_path : str | Path
        .sch 파일 경로
    capacity : float
        공칭 용량(mAh). C-rate 계산에 사용. 0이면 C-rate 생략.

    Returns
    -------
    dict | None
        {
            'file': str,
            'total_steps': int,
            'total_designed_cycles': int,
            'accel_blocks': [{'block_idx', 'loop_count', 'n_chg', 'n_dchg'}, ...],
            'n_accel_blocks': int,
            'sections': [{'category', 'loop_count', ...}, ...],
            'pattern_string': str,
            'has_rss': bool,
            'has_gitt_hppc': bool,
            'schedule_type': str,
            'source': 'sch',
        }
    """
    parsed = parse_pne_schedule(sch_path)
    if parsed is None:
        return None

    sections = _split_sections(parsed["steps"])

    # 가속수명 블록 집계
    accel_blocks = []
    total_designed = 0
    for i, sec in enumerate(sections):
        if sec["category"] == "가속수명":
            accel_blocks.append({
                "block_idx": i,
                "loop_count": sec["loop_count"],
                "n_chg": sec["n_chg"],
                "n_dchg": sec["n_dchg"],
            })
            total_designed += sec["loop_count"]

    # 플래그
    cats = {sec["category"] for sec in sections}
    has_rss = "Rss/DCIR" in cats
    has_gitt_hppc = "GITT/HPPC" in cats
    has_rate = "Rate" in cats

    # 패턴 문자열 생성
    parts = []
    for sec in sections:
        cat = sec["category"]
        lc = sec["loop_count"]
        if cat == "구간경계":
            continue
        if lc > 1:
            parts.append(f"{cat}×{lc}")
        else:
            parts.append(cat)
    pattern_string = " → ".join(parts) if parts else ""

    # 스케줄 타입 결정
    type_parts = []
    if accel_blocks:
        type_parts.append("가속수명")
    if has_rate:
        type_parts.append("Rate")
    if has_rss:
        type_parts.append("Rss/DCIR")
    if has_gitt_hppc:
        type_parts.append("GITT/HPPC")
    if any(sec["category"] == "RPT" for sec in sections):
        type_parts.append("RPT")
    schedule_type = " + ".join(type_parts) if type_parts else "기타"

    # sections 요약 (currents 제외)
    section_summary = []
    for sec in sections:
        entry = {
            "category": sec["category"],
            "loop_count": sec["loop_count"],
            "n_chg": sec["n_chg"],
            "n_dchg": sec["n_dchg"],
        }
        # C-rate 첨부
        if capacity > 0 and sec["currents"]:
            entry["crates"] = sorted(set(
                round(c["current_mA"] / capacity, 2)
                for c in sec["currents"] if c["current_mA"] > 0
            ))
        section_summary.append(entry)

    return {
        "file": Path(sch_path).name,
        "total_steps": parsed["total_steps"],
        "total_designed_cycles": total_designed,
        "accel_blocks": accel_blocks,
        "n_accel_blocks": len(accel_blocks),
        "sections": section_summary,
        "pattern_string": pattern_string,
        "has_rss": has_rss,
        "has_gitt_hppc": has_gitt_hppc,
        "schedule_type": schedule_type,
        "source": "sch",
    }


# ── CLI 실행 ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    import sys

    logging.basicConfig(level=logging.DEBUG, format="%(message)s")

    if len(sys.argv) < 2:
        print("사용법: python parse_pne_schedule.py <sch_path> [capacity_mAh]")
        sys.exit(1)

    sch = Path(sys.argv[1])
    cap = float(sys.argv[2]) if len(sys.argv) > 2 else 0

    result = parse_pne_schedule(sch)
    if result:
        # 전체 파싱 결과 요약
        print(f"\n{'='*60}")
        print(f"파일: {result['file']}")
        print(f"총 스텝: {result['total_steps']}")
        print(f"용량한도: {result['capacity_limit_mAh']} mAh")
        print(f"추정 공칭용량: {result['estimated_nameplate_mAh']} mAh")
        print(f"{'='*60}")

        for s in result["steps"]:
            num = s["step_num"]
            stype = s["type"]
            extras = {k: v for k, v in s.items() if k not in ("step_num", "type")}
            extra_str = ", ".join(f"{k}={v}" for k, v in extras.items())
            print(f"  Step {num:2d}: {stype:<12s} {extra_str}")

        # 가속수명 패턴
        print(f"\n{'='*60}")
        print("가속수명 패턴 분석:")
        print(f"{'='*60}")
        pattern = extract_accel_pattern_from_sch(sch, cap)
        if pattern:
            print(json.dumps(pattern, indent=2, ensure_ascii=False))
        else:
            print("가속수명 패턴 없음")
