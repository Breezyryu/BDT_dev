"""save_end_schema.py — PNE SaveEndData.csv 47컬럼 스키마.

**공식 정의**: origin 코드 `BAK/BatteryDataTool_origin.py` L1583-1590의 주석.
(pne_dcir_chk_cycle 함수. 배터리 팀이 장비사에서 받은 정식 문서 기반.)

주석 원문:
    0:Index  1:Stepmode(1:CC-CV, 2:CC, 3:CV, 4:OCV)
    2:StepType(1:충전, 2:방전, 3:휴지, 4:OCV, 5:Impedance, 6:End, 8:loop)
    3:ChgDchg  4:State  5:Loop(Loop:1)
    6:Code(66:충전, 65:방전, 64:휴지, 64:loop)
    7:StepNo  8:Voltage(uV)  9:Current(uA)
    10:ChgCap(uAh)  11:DchgCap(uAh)  12:ChgPower(uW)  13:DchgPower(uW)
    14:ChgWattHour(Wh)  15:DchgWattHour(Wh)
    17:StepTime(/100s)  18:TotTime(day)  19:TotTime(/100s)  20:imp
    21:Temp1  22:Temp2  23:Temp3  24:Temperature(°C)
    27:TotalCycle  28:CurrCycle  29:AvgVoltage(mV)  30:AvgCurrent(A)
    33:date  34:time
    44:누적step(Loop, 완료 제외)  45:voltage max

핵심 활용:
    col[1] Stepmode: CC-CV 구분 (1=CC-CV 통합 스텝, 2=CC, 3=CV, 4=OCV)
                     → CV 제외 필터링 기준
    col[2] StepType: origin OCV/CCV 구분: 3=OCV, 1|2=CCV
    col[6] Code: 스텝 종료 원인 (66=CV종료, 65=CC종료, 64=REST종료)
    col[27] TotalCycle: GOTO 재순환 포함 누적 TC (단조증가 100%)
    col[28] CurrentCycle: Loop 내 반복 번호 (그룹 전환 시 1로 리셋)

이전 스키마의 잘못된 부분 (교정됨):
    col[1] "Default2" → Stepmode (origin 정의)
    col[5] "CCCV 0=CC/1=CV" → Loop 플래그 (origin 정의, 사용자 추정도 오류)
    col[12]/[13] mW → uW
    col[24] "Temp4" → Temperature(°C) 단일 기본 온도
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
    # 출처: origin `BAK/BatteryDataTool_origin.py` L1583-1590 공식 주석
    ColumnSpec(0,  "Index",          "",       "[ORIGIN] 레코드 번호 (RecIdx)"),
    ColumnSpec(1,  "Stepmode",       "",       "[ORIGIN] 1=CC-CV, 2=CC, 3=CV, 4=OCV "
                                               "(스텝 전체 모드. CV 제외 필터링 기준)"),
    ColumnSpec(2,  "StepType",       "",       "[ORIGIN] 1=충전, 2=방전, 3=휴지, 4=OCV, "
                                               "5=Impedance, 6=End, 8=Loop"),
    ColumnSpec(3,  "ChgDchg",        "",       "[ORIGIN] ChgDchg 플래그"),
    ColumnSpec(4,  "State",          "",       "[ORIGIN] 장비 내부 상태"),
    ColumnSpec(5,  "Loop",           "",       "[ORIGIN] Loop 플래그 (Loop:1)"),
    ColumnSpec(6,  "Code",           "",       "[ORIGIN] 66=충전종료, 65=방전종료, 64=휴지/Loop종료 "
                                               "(+ 69=PAT_END, 78=용량컷, 67/152 실측관찰)"),
    ColumnSpec(7,  "StepNo",         "",       "[ORIGIN] 스텝 번호 (GOTO 시 리셋)"),
    ColumnSpec(8,  "Voltage",        "uV",     "[ORIGIN] Voltage (uV)"),
    ColumnSpec(9,  "Current",        "uA",     "[ORIGIN] Current (uA)"),
    ColumnSpec(10, "ChgCapacity",    "uAh",    "[ORIGIN] Chg Capacity (uAh)"),
    ColumnSpec(11, "DchgCapacity",   "uAh",    "[ORIGIN] Dchg Capacity (uAh)"),
    ColumnSpec(12, "ChgPower",       "uW",     "[ORIGIN] Chg Power (uW)  ※ mW 아님"),
    ColumnSpec(13, "DchgPower",      "uW",     "[ORIGIN] Dchg Power (uW)  ※ mW 아님"),
    ColumnSpec(14, "ChgWattHour",    "Wh",     "[ORIGIN] Chg WattHour (Wh)"),
    ColumnSpec(15, "DchgWattHour",   "Wh",     "[ORIGIN] Dchg WattHour (Wh)"),
    ColumnSpec(16, "Reserved16",     "",       "[ORIGIN] 미정의"),
    ColumnSpec(17, "StepTime",       "/100s",  "[ORIGIN] StepTime (/100s)"),
    ColumnSpec(18, "TotTimeDay",     "day",    "[ORIGIN] TotTime (day)"),
    ColumnSpec(19, "TotTime",        "/100s",  "[ORIGIN] TotTime (/100s)"),
    ColumnSpec(20, "Impedance",      "",       "[ORIGIN] imp"),
    ColumnSpec(21, "Temperature1",   "",       "[ORIGIN] Temp1"),
    ColumnSpec(22, "Temperature2",   "",       "[ORIGIN] Temp2"),
    ColumnSpec(23, "Temperature3",   "",       "[ORIGIN] Temp3"),
    ColumnSpec(24, "Temperature",    "°C",     "[ORIGIN] Temperature (°C)  ※ 기본 온도"),
    ColumnSpec(25, "Reserved25",     "",       "[ORIGIN] 미정의"),
    ColumnSpec(26, "Reserved26",     "",       "[ORIGIN] 미정의"),
    ColumnSpec(27, "TotalCycle",     "",       "[ORIGIN] Total Cycle (GOTO 재순환 포함)"),
    ColumnSpec(28, "CurrentCycle",   "",       "[ORIGIN] Current Cycle (Loop 내 반복)"),
    ColumnSpec(29, "AvgVoltage",     "mV",     "[ORIGIN] Average voltage (mV)  ※ uV 아님"),
    ColumnSpec(30, "AvgCurrent",     "A",      "[ORIGIN] Average current (A)  ※ uA 아님"),
    ColumnSpec(31, "Reserved31",     "",       "[ORIGIN] 미정의"),
    ColumnSpec(32, "Reserved32",     "",       "[ORIGIN] 미정의"),
    ColumnSpec(33, "Date",           "YYMMDD", "[ORIGIN] date"),
    ColumnSpec(34, "Time",           "HHMMssss/100s", "[ORIGIN] time"),
    ColumnSpec(35, "Reserved35",     "",       "[ORIGIN] 미정의"),
    ColumnSpec(36, "Reserved36",     "",       "[ORIGIN] 미정의"),
    ColumnSpec(37, "Reserved37",     "",       "[ORIGIN] 미정의"),
    ColumnSpec(38, "Reserved38",     "",       "[ORIGIN] 미정의"),
    ColumnSpec(39, "Reserved39",     "",       "[ORIGIN] 미정의"),
    ColumnSpec(40, "Reserved40",     "",       "[ORIGIN] 미정의"),
    ColumnSpec(41, "Reserved41",     "",       "[ORIGIN] 미정의"),
    ColumnSpec(42, "Reserved42",     "",       "[ORIGIN] 미정의"),
    ColumnSpec(43, "Reserved43",     "",       "[ORIGIN] 미정의"),
    ColumnSpec(44, "AccumStep",      "",       "[ORIGIN] 누적 step (Loop, 완료 제외)"),
    ColumnSpec(45, "VoltageMax",     "uV",     "[ORIGIN] voltage max"),
    ColumnSpec(46, "Reserved46",     "",       "[ORIGIN] 미정의"),
]

# 인덱스 상수 (origin 주석 기반 공식 정의, 매직 넘버 금지)
IDX_INDEX = 0
IDX_STEPMODE = 1                # ★ 1=CC-CV, 2=CC, 3=CV, 4=OCV
IDX_STEP_TYPE = 2               # 1=CHG 2=DCHG 3=REST 4=OCV 5=IMP 6=END 8=LOOP
IDX_CHG_DCHG = 3
IDX_STATE = 4
IDX_LOOP_FLAG = 5               # ★ (구 IDX_CCCV, 실은 Loop flag)
IDX_CODE = 6                    # ★ 스텝 종료 코드 (구 IDX_END_STATE)
IDX_END_STATE = 6               # 하위 호환 별칭 (Code 컬럼)
IDX_STEP_NO = 7
IDX_STEP = 7                    # 하위 호환 별칭
IDX_VOLTAGE = 8
IDX_CURRENT = 9
IDX_CHG_CAP = 10
IDX_DCHG_CAP = 11
IDX_CHG_POWER = 12              # uW
IDX_DCHG_POWER = 13             # uW
IDX_CHG_WH = 14
IDX_DCHG_WH = 15
IDX_STEP_TIME = 17
IDX_TOT_TIME_DAY = 18
IDX_TOT_TIME = 19
IDX_IMPEDANCE = 20
IDX_TEMP1 = 21
IDX_TEMP2 = 22
IDX_TEMP3 = 23
IDX_TEMPERATURE = 24            # °C, 기본 온도
IDX_TOTAL_CYCLE = 27            # ★ TC single source of truth
IDX_CURRENT_CYCLE = 28          # ★ Loop 내 반복 번호
IDX_AVG_VOLTAGE = 29            # mV
IDX_AVG_CURRENT = 30            # A
IDX_DATE = 33
IDX_TIME = 34
IDX_ACCUM_STEP = 44
IDX_VOLTAGE_MAX = 45

# --- 하위 호환 (deprecated, 향후 제거) ---
IDX_REPEAT_PATTERN = 16
IDX_REPEAT_COUNT = 26
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

# Stepmode 코드 (col[1]) — CV 필터링 기준
STEPMODE_CC_CV = 1              # CC-CV 통합 스텝 (CC 구간 + CV 구간)
STEPMODE_CC = 2                 # CC만
STEPMODE_CV = 3                 # CV만 (드묾)
STEPMODE_OCV = 4                # OCV 측정

STEPMODE_NAMES = {
    1: "CC-CV",
    2: "CC",
    3: "CV",
    4: "OCV",
}

def stepmode_has_cv(stepmode: int) -> bool:
    """해당 Stepmode가 CV 구간을 포함하는가 (CV 제외 필터 대상)."""
    return stepmode in (STEPMODE_CC_CV, STEPMODE_CV)


# ChgDchg 코드 (col[3], 미검증)
CHG_DCHG_CV = 1
CHG_DCHG_CC = 2
CHG_DCHG_REST = 255

# Code (col[6]) — 스텝 종료 원인
CODE_PAT_START = 0
CODE_REST_DONE = 64
CODE_DISCHARGE_DONE = 65
CODE_CHARGE_DONE = 66
CODE_PAT_END = 69
CODE_CAPACITY_CUT = 78

# 하위 호환 별칭
END_STATE_PAT_START = CODE_PAT_START
END_STATE_REST_DONE = CODE_REST_DONE
END_STATE_CC_DONE = CODE_DISCHARGE_DONE    # 실은 방전종료 (origin 주석 기반)
END_STATE_CV_DONE = CODE_CHARGE_DONE       # 실은 충전종료
END_STATE_PAT_END = CODE_PAT_END
END_STATE_CAPACITY_CUT = CODE_CAPACITY_CUT

CODE_NAMES = {
    0: "PAT_START",
    64: "REST_DONE / LOOP_DONE",
    65: "DISCHARGE_DONE",
    66: "CHARGE_DONE",
    69: "PAT_END",
    78: "CAPACITY_CUT",
}
END_STATE_NAMES = CODE_NAMES    # 하위 호환 별칭


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
