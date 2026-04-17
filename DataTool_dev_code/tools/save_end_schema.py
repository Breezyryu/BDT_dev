"""save_end_schema.py — PNE SaveEndData.csv 47컬럼 스키마.

사용자 정리 테이블 + 실측 검증 (50 채널, schema_verify.py 결과, 2026-04-18).

검증 상태 태그:
    [VERIFIED]  : 실측으로 확정
    [PARTIAL]   : 추정값 중 일부만 관찰됨 (드문 값 미관찰)
    [SUSPECT]   : 추정 외 값이 실측에 발견됨 — 추가 조사 필요
    [INFERRED]  : 실측 분포로부터 해석한 추론값

핵심 활용:
    col[27] TotalCycle      [VERIFIED] GOTO 재순환 포함 누적 TC (100% 단조증가)
    col[28] CurrentCycle    [VERIFIED] Loop 내 반복 번호 (98.7% 리셋)
    col[7]  Step            .sch 원본 step_num (+ 장비 오프셋)
    col[6]  EndState        [SUSPECT] 67, 152 추정 외 값 발견
    col[2]  StepType        [SUSPECT] 6 희소 값 발견 (1회)
    col[33]/[34]            Date/Time 레코드 타임스탬프
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ---------- 컬럼 의미 테이블 ----------
@dataclass(frozen=True)
class ColumnSpec:
    idx: int
    name: str
    unit: str = ""
    notes: str = ""


SAVE_END_COLUMNS: list[ColumnSpec] = [
    ColumnSpec(0,  "Index",          "",       "[VERIFIED] 레코드 번호 (RecIdx)"),
    ColumnSpec(1,  "Default2",       "",       "[SUSPECT] 대부분 2, 드물게 1 (채널 모드 추정)"),
    ColumnSpec(2,  "StepType",       "",       "[SUSPECT] 1=CHG 2=DCHG 3=REST 4=OCV 5=IMP 8=LOOP  "
                                               "+ 6(희소 1회 관찰, 미지)"),
    ColumnSpec(3,  "ChgDchg",        "",       "[VERIFIED] 1=CV구간/2=CC구간/255=rest  "
                                               "ST=1+CCCV=1 → 1, ST=1+CCCV=0 or ST=2 → 2, ST=3/8 → 255"),
    ColumnSpec(4,  "CurrentApp",     "",       "[PARTIAL] 추정 1=비인가직전 2=인가, 실측은 1만 관찰"),
    ColumnSpec(5,  "CCCV",           "",       "[VERIFIED] 0=CC 1=CV"),
    ColumnSpec(6,  "EndState",       "",       "[SUSPECT] 64=REST 65=CC 66=CV 69=PAT종료 78=용량컷  "
                                               "+ 67, 152 추정 외 값 관찰"),
    ColumnSpec(7,  "Step",           "",       "count step. Repeat:카운트유지, Goto:특정 step으로 점프"),
    ColumnSpec(8,  "Voltage",        "uV",     "[VERIFIED] 2.75M~4.57M uV 범위 = 2750~4570 mV"),
    ColumnSpec(9,  "Current",        "uA",     "[VERIFIED] -4.98M~9.89M uA = -4980~9890 mA"),
    ColumnSpec(10, "ChgCapacity",    "uAh",    "[VERIFIED] 0~8.88M uAh; step별 충전 합산 필요"),
    ColumnSpec(11, "DchgCapacity",   "uAh",    "[VERIFIED] 0~5.40M uAh"),
    ColumnSpec(12, "ChgPower",       "mW",     "[INFERRED]"),
    ColumnSpec(13, "DchgPower",      "mW",     "[INFERRED]"),
    ColumnSpec(14, "ChgWattHour",    "Wh",     "[INFERRED]"),
    ColumnSpec(15, "DchgWattHour",   "Wh",     "[INFERRED]"),
    ColumnSpec(16, "RepeatPattern",  "",       "[PARTIAL] 주로 0, 큰 값(36, 100) 드물게 — "
                                               "StepType=8/9 만날 때 카운터 추정"),
    ColumnSpec(17, "StepTime",       "/100s",  "[VERIFIED] 0~8.34M/100s = 0~83420s (~23h)"),
    ColumnSpec(18, "TotTimeDay",     "day",    "[INFERRED] 누적 시간(day 단위)"),
    ColumnSpec(19, "TotTime",        "/100s",  "[VERIFIED] 누적 시간(/100s)"),
    ColumnSpec(20, "Impedance",      "",       "[INFERRED]"),
    ColumnSpec(21, "Temperature1",   "",       "[INFERRED] 일반적으로 1/1000°C (m°C)"),
    ColumnSpec(22, "Temperature2",   "",       "[INFERRED]"),
    ColumnSpec(23, "Temperature3",   "",       "[INFERRED]"),
    ColumnSpec(24, "Temperature4",   "",       "[INFERRED]"),
    ColumnSpec(25, "Unknown25",      "",       "[VERIFIED] 0 or 2, 의미 미확인"),
    ColumnSpec(26, "RepeatCount",    "",       "[PARTIAL] 0~5 범위; Loop 내 카운터 추정"),
    ColumnSpec(27, "TotalCycle",     "",       "[VERIFIED] GOTO 재순환 포함 누적 TC, 단조증가 100%"),
    ColumnSpec(28, "CurrentCycle",   "",       "[VERIFIED] Loop 그룹 내 반복 번호, 그룹 전환 시 1로 리셋 98.7%"),
    ColumnSpec(29, "AvgVoltage",     "uV",     "[VERIFIED]"),
    ColumnSpec(30, "AvgCurrent",     "uA",     "[SUSPECT] max=2.14e9 오버플로우 값 존재"),
    ColumnSpec(31, "Reserved31",     "",       "[INFERRED]"),
    ColumnSpec(32, "CVSection",      "",       "[INFERRED] CV 구간"),
    ColumnSpec(33, "Date",           "YYMMDD", "[INFERRED] 레코드 타임스탬프 (.cyc FID43과 동일)"),
    ColumnSpec(34, "Time",           "HHMMssss/100s", "[INFERRED] (.cyc FID44과 동일)"),
    ColumnSpec(35, "Reserved35",     "",       ""),
    ColumnSpec(36, "Reserved36",     "",       ""),
    ColumnSpec(37, "Reserved37",     "",       ""),
    ColumnSpec(38, "PerStep",        "",       "[INFERRED] Step별 ?"),
    ColumnSpec(39, "CCCharge",       "",       "[INFERRED] CC 충전 구간"),
    ColumnSpec(40, "CVSection40",    "",       "[INFERRED] CV 구간"),
    ColumnSpec(41, "Discharge",      "",       "[INFERRED] 방전"),
    ColumnSpec(42, "Reserved42",     "",       ""),
    ColumnSpec(43, "SectionAvgV",    "",       "[INFERRED] 구간별 평균 전압"),
    ColumnSpec(44, "AccumStep",      "",       "[INFERRED] 누적 step"),
    ColumnSpec(45, "VoltageMax",     "uV",     "[VERIFIED]"),
    ColumnSpec(46, "VoltageMin",     "uV",     "[VERIFIED]"),
]

# 인덱스 상수 (코드에서 매직 넘버 대신 사용)
IDX_INDEX = 0
IDX_STEP_TYPE = 2
IDX_CHG_DCHG = 3
IDX_CCCV = 5
IDX_END_STATE = 6
IDX_STEP = 7
IDX_VOLTAGE = 8
IDX_CURRENT = 9
IDX_CHG_CAP = 10
IDX_DCHG_CAP = 11
IDX_REPEAT_PATTERN = 16
IDX_STEP_TIME = 17
IDX_TOT_TIME = 19
IDX_TEMP1 = 21
IDX_REPEAT_COUNT = 26
IDX_TOTAL_CYCLE = 27            # ★ TC single source of truth
IDX_CURRENT_CYCLE = 28          # ★ Loop 내 반복 번호
IDX_AVG_VOLTAGE = 29
IDX_DATE = 33
IDX_TIME = 34
IDX_VOLTAGE_MAX = 45
IDX_VOLTAGE_MIN = 46

# StepType 코드
STEP_TYPE_CHARGE = 1
STEP_TYPE_DISCHARGE = 2
STEP_TYPE_REST = 3
STEP_TYPE_OCV = 4
STEP_TYPE_IMPEDANCE = 5
STEP_TYPE_LOOP = 8

STEP_TYPE_NAMES = {
    1: "CHARGE",
    2: "DISCHARGE",
    3: "REST",
    4: "OCV",
    5: "IMPEDANCE",
    8: "LOOP",
}

# ChgDchg 코드
CHG_DCHG_CV = 1
CHG_DCHG_CC = 2
CHG_DCHG_REST = 255

# EndState 코드
END_STATE_PAT_START = 0
END_STATE_REST_DONE = 64
END_STATE_CC_DONE = 65
END_STATE_CV_DONE = 66
END_STATE_PAT_END = 69
END_STATE_CAPACITY_CUT = 78

END_STATE_NAMES = {
    0: "PAT_START",
    64: "REST_DONE",
    65: "CC_DONE",
    66: "CV_DONE",
    69: "PAT_END",
    78: "CAPACITY_CUT",
}


# ---------- 편의 함수 ----------
def is_loop_marker(step_type: int) -> bool:
    return step_type == STEP_TYPE_LOOP


def is_rest(step_type: int) -> bool:
    return step_type == STEP_TYPE_REST


def is_charge(step_type: int) -> bool:
    return step_type == STEP_TYPE_CHARGE


def is_discharge(step_type: int) -> bool:
    return step_type == STEP_TYPE_DISCHARGE


def is_capacity_cutoff(end_state: int) -> bool:
    """EndState=78: 용량 컷오프 — RPT/partial discharge 판별에 사용."""
    return end_state == END_STATE_CAPACITY_CUT


def describe_column(idx: int) -> Optional[ColumnSpec]:
    if 0 <= idx < len(SAVE_END_COLUMNS):
        return SAVE_END_COLUMNS[idx]
    return None


def rename_columns_dict() -> dict[int, str]:
    """pd.DataFrame.rename(columns=...) 용 {int: str} 매핑."""
    return {c.idx: c.name for c in SAVE_END_COLUMNS}


# ---------- Date/Time 파싱 ----------
def parse_date(date_int: int) -> tuple[int, int, int]:
    """YYMMDD int → (year_full, month, day). year는 20xx로 확장."""
    d = int(date_int)
    y = d // 10000
    m = (d // 100) % 100
    dd = d % 100
    return (2000 + y, m, dd)


def parse_time(time_int: int) -> tuple[int, int, int, int]:
    """HHMMssss/100s int → (hour, minute, second, centisecond)."""
    t = int(time_int)
    h = t // 1000000
    mn = (t // 10000) % 100
    ss = (t // 100) % 100
    cs = t % 100
    return (h, mn, ss, cs)


def record_datetime(date_int: int, time_int: int):
    """(Date, Time) → Python datetime. 파싱 실패 시 None."""
    from datetime import datetime

    try:
        y, m, d = parse_date(date_int)
        h, mn, ss, cs = parse_time(time_int)
        return datetime(y, m, d, h, mn, ss, cs * 10_000)  # cs → microseconds
    except (ValueError, TypeError):
        return None


if __name__ == "__main__":
    # 스키마 덤프
    print(f"{'idx':>3} {'name':<18} {'unit':<10} notes")
    print("-" * 90)
    for c in SAVE_END_COLUMNS:
        print(f"{c.idx:>3} {c.name:<18} {c.unit:<10} {c.notes}")
