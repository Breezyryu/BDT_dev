"""tc_plan.py — .sch 기반 TotalCycle (TC) Plan 생성기.

채널 디렉토리의 .sch 패턴 파일에서 StepNum → TC 매핑을 사전 산출한다.
.cyc / SaveEndData.csv 없이 시험 구조 정의만으로 TC 경계를 100% 확정.

다중 버전 .sch 정책 (실증):
    이름.sch        → 현재 활성 패턴 (TC 계산 기준)
    이름_NNN.sch    → 변경 이력 (diff만 warnings에 기록)

핵심 파싱 상수/로직은 parse_all_sch.py와 동일 (상수 변경 시 양쪽 동기화 필요).
"""
from __future__ import annotations

import os
import re
import struct
from dataclasses import dataclass, field
from typing import Optional

# ---------- .sch 포맷 상수 (parse_all_sch.py와 동기화) ----------
HEADER_SIZE = 1920
STEP_SIZE = 652
MAGIC = 740721

TYPE_CODES = {
    0x0101: "CHG_CC",
    0x0102: "DCHG_CCCV",
    0x0201: "CHG_CCCV",
    0x0202: "DCHG_CC",
    0x0209: "CHG_CP",
    0xFF03: "REST",
    0xFF06: "GOTO",
    0xFF07: "REST_SAFE",
    0xFF08: "LOOP",
    0x0003: "GITT_PAUSE",
    0x0007: "GITT_END",
    0x0008: "GITT_START",
}

EC_TYPE_MAP = {
    0: "NONE",
    256: "CUR",
    512: "VOL",
    1024: "CAP",
    2048: "DOD",
    4096: "WATT",
    8192: "ENERGY",
    16384: "SOC",
    18432: "SOC_CHG",
}

# ---------- 데이터 클래스 ----------
@dataclass
class SchVariant:
    """하나의 .sch 파일 메타."""

    path: str
    suffix: Optional[str]  # None = 활성(.sch), "000"/"001"... = 변경 이력
    mtime: float
    size: int

    @property
    def name(self) -> str:
        return os.path.basename(self.path)

    @property
    def is_active(self) -> bool:
        return self.suffix is None


@dataclass
class TCGroup:
    """TC 범위를 공유하는 Loop 그룹 (활성 .sch의 전개 결과).

    body: 데이터 수집 스텝 (CHG/DCHG/REST) — 사용자가 의미를 부여
    control: 제어 마커 (LOOP/REST_SAFE) — 장비가 StepType=8로 기록하지만
             동일 TC에 속함 (LOOP는 직전 반복의 말미로 집계됨)
    """

    idx: int                       # 0-based 그룹 순번
    category: str                  # INIT/ACCEL/RPT/FORMATION/...
    loop_count: int                # 반복 횟수 (N)
    tc_start: int                  # 이 그룹이 차지하는 TC 시작 (1-based)
    tc_end: int                    # tc_start + loop_count - 1
    body_step_nums: list[int]      # body 스텝의 원본 .sch step_num
    body_step_types: list[str]     # 동일 길이의 type 이름
    control_step_nums: list[int]   # LOOP/REST_SAFE 마커 step_num (그룹 경계)
    body_desc: str                 # 사람 읽기용 요약

    def contains_tc(self, tc: int) -> bool:
        return self.tc_start <= tc <= self.tc_end

    @property
    def all_step_nums(self) -> list[int]:
        return list(self.body_step_nums) + list(self.control_step_nums)


@dataclass
class TCPlan:
    """채널의 TC 계획 — .sch 기반으로 사전 산출된 불변 스케줄."""

    channel_dir: str
    active_sch: SchVariant
    variants: list[SchVariant] = field(default_factory=list)   # _NNN.sch들

    # 핵심 매핑
    step_to_tc_start: dict[int, int] = field(default_factory=dict)
    # step_num(활성 .sch의 고유 step_num) → 해당 스텝이 속한 그룹의 tc_start.
    # Loop 내 step_num은 모든 반복에서 동일하므로 "첫 TC"만 기록.
    # 실제 레코드의 TC 산출은 resolve_tc(plan, step_num, rep_idx)로.

    tc_to_group: dict[int, TCGroup] = field(default_factory=dict)
    groups: list[TCGroup] = field(default_factory=list)
    max_tc: int = 0
    warnings: list[str] = field(default_factory=list)

    # ---- 편의 API ----
    def resolve_tc(self, step_num: int, rep_idx: int = 0) -> Optional[int]:
        """(step_num, rep_idx) → TC. rep_idx는 Loop 내 0-based 반복 인덱스."""
        tc_start = self.step_to_tc_start.get(step_num)
        if tc_start is None:
            return None
        grp = self.tc_to_group.get(tc_start)
        if grp is None:
            return tc_start
        # rep_idx가 범위를 벗어나면 clamp (데이터 이상 케이스 방지)
        tc = tc_start + max(0, min(rep_idx, grp.loop_count - 1))
        return tc

    def steps_of_tc(self, tc: int) -> list[int]:
        """특정 TC에 속한 step_num 리스트."""
        grp = self.tc_to_group.get(tc)
        return list(grp.body_step_nums) if grp else []

    def category_of_tc(self, tc: int) -> Optional[str]:
        grp = self.tc_to_group.get(tc)
        return grp.category if grp else None


# ---------- .sch 발견 & 선택 ----------
_SUFFIX_RE = re.compile(r"_(\d{3})\.sch$", re.IGNORECASE)


def _extract_suffix(filename: str) -> Optional[str]:
    m = _SUFFIX_RE.search(filename)
    return m.group(1) if m else None


def discover_sch_variants(channel_dir: str) -> list[SchVariant]:
    """채널 폴더 내 모든 .sch 파일을 발견. 에러 시 빈 리스트."""
    if not os.path.isdir(channel_dir):
        return []

    out: list[SchVariant] = []
    for name in os.listdir(channel_dir):
        if not name.lower().endswith(".sch"):
            continue
        full = os.path.join(channel_dir, name)
        if not os.path.isfile(full):
            continue
        try:
            st = os.stat(full)
        except OSError:
            continue
        out.append(
            SchVariant(
                path=full,
                suffix=_extract_suffix(name),
                mtime=st.st_mtime,
                size=st.st_size,
            )
        )
    return out


def select_active_sch(variants: list[SchVariant]) -> Optional[SchVariant]:
    """활성 .sch 선택.

    우선순위:
      1) suffix 없는 `.sch`가 있으면 그중 mtime 최신
      2) 없으면 전체에서 mtime 최신 (suffix 있는 변형 중)
    """
    if not variants:
        return None
    actives = [v for v in variants if v.is_active]
    if actives:
        return max(actives, key=lambda v: v.mtime)
    return max(variants, key=lambda v: v.mtime)


# ---------- .sch 바이너리 파싱 ----------
def parse_sch(filepath: str) -> Optional[list[dict]]:
    """.sch 바이너리 → step 딕셔너리 리스트. 포맷 위반 시 None."""
    try:
        with open(filepath, "rb") as f:
            data = f.read()
    except OSError:
        return None

    if len(data) < HEADER_SIZE:
        return None

    magic = struct.unpack_from("<I", data, 0)[0]
    if magic != MAGIC:
        return None

    steps: list[dict] = []
    offset = HEADER_SIZE
    while offset + STEP_SIZE <= len(data):
        step_num = struct.unpack_from("<I", data, offset + 0)[0]
        type_code = struct.unpack_from("<I", data, offset + 8)[0]
        v_chg = struct.unpack_from("<f", data, offset + 12)[0]
        v_dchg = struct.unpack_from("<f", data, offset + 16)[0]
        current = struct.unpack_from("<f", data, offset + 20)[0]
        time_limit = struct.unpack_from("<f", data, offset + 24)[0]
        cv_voltage = struct.unpack_from("<f", data, offset + 28)[0]
        cv_cutoff = struct.unpack_from("<f", data, offset + 32)[0]
        loop_count = struct.unpack_from("<I", data, offset + 56)[0]
        cap_limit = struct.unpack_from("<f", data, offset + 104)[0]
        ec_value = struct.unpack_from("<f", data, offset + 372)[0]
        ec_type = struct.unpack_from("<I", data, offset + 500)[0]
        ec_enabled = struct.unpack_from("<I", data, offset + 504)[0]

        steps.append(
            {
                "step_num": step_num,
                "type_code": type_code,
                "type": TYPE_CODES.get(type_code, f"UNK_0x{type_code:04X}"),
                "v_chg": v_chg,
                "v_dchg": v_dchg,
                "current": current,
                "time_limit": time_limit,
                "cv_voltage": cv_voltage,
                "cv_cutoff": cv_cutoff,
                "loop_count": loop_count,
                "goto_target": loop_count,  # 같은 필드
                "cap_limit": cap_limit,
                "ec_value": ec_value,
                "ec_type": ec_type,
                "ec_enabled": ec_enabled,
            }
        )
        offset += STEP_SIZE
    return steps


def split_into_loop_groups(steps: list[dict]) -> list[dict]:
    """LOOP 마커 기준으로 스텝을 body 그룹으로 분할.

    Returns 리스트의 각 dict:
        'body': 데이터 수집 스텝들
        'loop_count': 반복 횟수
        'loop_step': LOOP 스텝 dict (None 가능)
        'control': 해당 그룹에 속한 제어 스텝들 (LOOP + 뒤따르는 REST_SAFE)
                  → 실측 StepNo 매핑에서 이들도 같은 TC로 귀속
    """
    groups: list[dict] = []
    body: list[dict] = []
    pending_controls: list[dict] = []

    for s in steps:
        t = s["type"]
        if t == "LOOP":
            # LOOP는 직전 그룹을 마감. LOOP 자신과 뒤따르는 REST_SAFE는
            # 직전 반복의 "종료 마커"로서 같은 그룹에 귀속.
            controls = list(pending_controls)
            controls.append(s)
            groups.append(
                {
                    "body": body,
                    "loop_count": s["loop_count"],
                    "loop_step": s,
                    "control": controls,
                }
            )
            body = []
            pending_controls = []
        elif t == "REST_SAFE":
            # REST_SAFE는 보통 LOOP 직후에 위치 → 다음 그룹의 시작 경계 마커.
            # 하지만 실측 SaveEndData에서는 직전 LOOP와 같은 TC로 기록됨.
            # 따라서 "직전 그룹의 control"로 편입하기 위해 groups의 마지막에 추가.
            if groups:
                groups[-1].setdefault("control", []).append(s)
            else:
                # LOOP 전에 REST_SAFE가 먼저 나오는 드문 케이스 → 다음 그룹으로 연기
                pending_controls.append(s)
        elif t == "GOTO":
            # GOTO는 보통 파일 끝 흐름 제어 — 마지막 그룹 control에 편입
            if groups:
                groups[-1].setdefault("control", []).append(s)
        else:
            body.append(s)

    # LOOP 없이 남은 body (trailing 그룹)
    if body:
        groups.append(
            {
                "body": body,
                "loop_count": 1,
                "loop_step": None,
                "control": list(pending_controls),
            }
        )

    # control 키 기본값 보장
    for g in groups:
        g.setdefault("control", [])
    return groups


def classify_loop_group(
    body_steps: list[dict], loop_count: int, position: int, total_loops: int
) -> str:
    """Loop 그룹 카테고리 판별 (parse_all_sch.py와 동일 분기)."""
    n_steps = len(body_steps)
    if n_steps == 0:
        return "EMPTY"

    N = loop_count
    types = [s["type"] for s in body_steps]
    type_set = set(types)
    chg_count = sum(1 for t in types if t.startswith("CHG"))
    dchg_count = sum(1 for t in types if t.startswith("DCHG"))
    has_chg_cp = "CHG_CP" in type_set
    ec_steps = [s for s in body_steps if s.get("ec_enabled", 0) > 0]
    has_ec = bool(ec_steps)
    ec_on_dchg = [s for s in ec_steps if s["type"].startswith("DCHG")]
    ec_on_chg = [s for s in ec_steps if s["type"].startswith("CHG")]

    # 1. INIT (첫 그룹, 방전 + REST만)
    if position == 0 and N == 1:
        if type_set <= {"DCHG_CC", "DCHG_CCCV", "REST", "REST_SAFE"} and any(
            t.startswith("DCHG") for t in types
        ):
            return "INIT"

    # 2. GITT_PULSE (REST 선행 + 짧은 충방전 반복)
    if N >= 10 and n_steps <= 3 and types and types[0] == "REST":
        rest_t = body_steps[0].get("time_limit", 0)
        if rest_t >= 600 and any(t in ("CHG_CCCV", "CHG_CC", "DCHG_CC") for t in types[1:]):
            return "GITT_PULSE"

    # 3. ACCEL (대량 반복 + 충방전 쌍)
    if N >= 20 and chg_count >= 2 and dchg_count >= 1:
        return "ACCEL"

    # 4. HYSTERESIS_DCHG
    if N == 1 and ec_on_dchg and any(s.get("ec_type") == 2048 for s in ec_on_dchg):
        return "HYSTERESIS_DCHG"

    # 5. HYSTERESIS_CHG
    if N == 1 and ec_on_chg and any(s.get("ec_type") == 18432 for s in ec_on_chg):
        return "HYSTERESIS_CHG"

    # 6. SOC_DCIR (SOC별 저항 측정)
    if N >= 5 and len(ec_steps) >= 4 and n_steps >= 8:
        return "SOC_DCIR"

    # 7. RSS_DCIR (1회성 DCIR)
    if N == 1 and has_ec and dchg_count >= 4 and n_steps >= 10:
        return "RSS_DCIR"

    # 8. RATE_TEST
    if N > 1 and has_ec and chg_count >= 2 and dchg_count >= 2:
        return "RATE_TEST"

    # 9. KVALUE (CP 충전 또는 장기 휴지)
    if has_chg_cp:
        return "KVALUE"
    if n_steps == 1 and types[0] == "REST" and body_steps[0].get("time_limit", 0) >= 7200:
        return "KVALUE"

    # 10. FORMATION (초기 2~10 사이클 충방전)
    if 2 <= N <= 10 and chg_count >= 1 and dchg_count >= 1 and position <= 2:
        return "FORMATION"

    # 11. CHARGE_SET (충전만)
    if N == 1 and chg_count >= 1 and dchg_count == 0:
        if type_set <= {"CHG_CC", "CHG_CCCV", "CHG_CP", "REST", "REST_SAFE"}:
            return "CHARGE_SET"

    # 12. TERMINATION (마지막 그룹, 방전만)
    if position == total_loops - 1 and N == 1 and dchg_count >= 1 and chg_count == 0:
        return "TERMINATION"

    # 13. RPT (1회성 충방전 쌍)
    if N == 1 and chg_count >= 1 and dchg_count >= 1 and n_steps <= 8:
        return "RPT"

    return "UNKNOWN"


# ---------- body 요약 (디버그용) ----------
def _format_ec_info(step: dict) -> str:
    if step.get("ec_enabled", 0) <= 0:
        return ""
    ec_type = step.get("ec_type", 0)
    ec_val = step.get("ec_value", 0)
    if ec_type == 2048:
        return f"[DOD {ec_val:.1f}%]"
    if ec_type in (16384, 18432):
        return f"[SOC {ec_val:.1f}%]"
    if ec_type == 1024:
        return f"[CAP {ec_val:.1f}mAh]"
    if ec_type == 512:
        return f"[VOL {ec_val:.1f}mV]"
    name = EC_TYPE_MAP.get(ec_type, f"TYPE_{ec_type}")
    return f"[{name} {ec_val:.1f}]"


def _format_step(step: dict) -> str:
    t = step["type"]
    detail = []
    if t in ("CHG_CC", "DCHG_CC"):
        detail.append(f"I={step['current']:.0f}mA")
        if step["time_limit"] > 0:
            detail.append(f"t={step['time_limit']:.0f}s")
    elif t in ("CHG_CCCV", "DCHG_CCCV"):
        detail.append(f"I={step['current']:.0f}mA")
        if step["cv_voltage"] > 0:
            detail.append(f"CV={step['cv_voltage']:.0f}mV")
        if step["cv_cutoff"] > 0:
            detail.append(f"cut={step['cv_cutoff']:.0f}mA")
    elif t == "CHG_CP":
        detail.append(f"P={step['current']:.0f}mW")
    elif t == "REST":
        ts = step["time_limit"]
        if ts >= 3600:
            detail.append(f"{ts / 3600:.1f}h")
        elif ts >= 60:
            detail.append(f"{ts / 60:.0f}m")
        elif ts > 0:
            detail.append(f"{ts:.0f}s")

    ec = _format_ec_info(step)
    if ec:
        detail.append(ec)
    return f"{t}({','.join(detail)})" if detail else t


def _format_body(body_steps: list[dict]) -> str:
    if not body_steps:
        return "(empty)"
    return " → ".join(_format_step(s) for s in body_steps)


# ---------- TC Plan 빌더 ----------
def build_tc_plan(
    channel_dir: str,
    step_num_offset: int = 1,
) -> Optional[TCPlan]:
    """채널 디렉토리의 활성 .sch를 기준으로 TCPlan 생성.

    Parameters
    ----------
    channel_dir : str
        `M01Ch055[055]` 등 PNE 채널 폴더 경로 (내부에 *.sch 포함).
    step_num_offset : int
        실측 데이터(SaveEndData col7) StepNo와 .sch의 step_num 간 오프셋.
        실측 검증 결과 PNE 장비는 .sch의 1-based step_num에 +1을 적용해
        SaveEndData.csv에 기록함 (내부 "Step 0 = Init" 관습 추정).
        기본값 1. 장비/펌웨어가 다르면 0 또는 다른 값으로 조정.

    Returns
    -------
    TCPlan | None
        활성 .sch를 찾지 못하거나 파싱 실패 시 None.
    """
    variants = discover_sch_variants(channel_dir)
    if not variants:
        return None

    active = select_active_sch(variants)
    if active is None:
        return None

    others = [v for v in variants if v.path != active.path]

    steps = parse_sch(active.path)
    if steps is None:
        return None

    groups = split_into_loop_groups(steps)
    total_loops = len(groups)

    plan_groups: list[TCGroup] = []
    step_to_tc_start: dict[int, int] = {}
    tc_to_group: dict[int, TCGroup] = {}

    tc_current = 1
    for idx, g in enumerate(groups):
        category = classify_loop_group(g["body"], g["loop_count"], idx, total_loops)
        n = g["loop_count"]
        tc_start = tc_current
        tc_end = tc_current + n - 1

        # .sch 원본 step_num → 실측 StepNo로 오프셋 보정
        body_step_nums = [s["step_num"] + step_num_offset for s in g["body"]]
        body_step_types = [s["type"] for s in g["body"]]
        control_step_nums = [s["step_num"] + step_num_offset for s in g.get("control", [])]
        body_desc = _format_body(g["body"])

        tcg = TCGroup(
            idx=idx,
            category=category,
            loop_count=n,
            tc_start=tc_start,
            tc_end=tc_end,
            body_step_nums=body_step_nums,
            body_step_types=body_step_types,
            control_step_nums=control_step_nums,
            body_desc=body_desc,
        )
        plan_groups.append(tcg)

        for tc in range(tc_start, tc_end + 1):
            tc_to_group[tc] = tcg
        # body 스텝 + 제어 스텝(LOOP/REST_SAFE) 모두 이 그룹의 tc_start로 매핑
        for sn in tcg.all_step_nums:
            step_to_tc_start.setdefault(sn, tc_start)

        tc_current += n

    # 변형 .sch diff 수집
    warnings: list[str] = []
    for var in others:
        msg = _compare_variants(active, var)
        if msg:
            warnings.append(msg)

    return TCPlan(
        channel_dir=channel_dir,
        active_sch=active,
        variants=others,
        step_to_tc_start=step_to_tc_start,
        tc_to_group=tc_to_group,
        groups=plan_groups,
        max_tc=tc_current - 1,
        warnings=warnings,
    )


def _compare_variants(active: SchVariant, variant: SchVariant) -> Optional[str]:
    """활성 .sch 대비 변형의 loop_count 차이 요약."""
    a_steps = parse_sch(active.path)
    v_steps = parse_sch(variant.path)
    if a_steps is None or v_steps is None:
        return None

    a_groups = split_into_loop_groups(a_steps)
    v_groups = split_into_loop_groups(v_steps)

    diffs: list[str] = []
    for i, ag in enumerate(a_groups):
        if i >= len(v_groups):
            diffs.append(f"#{i + 1}: 변형에서 삭제됨 (활성 N={ag['loop_count']})")
            continue
        vg = v_groups[i]
        if ag["loop_count"] != vg["loop_count"]:
            diffs.append(
                f"#{i + 1}: loop_count {vg['loop_count']}→{ag['loop_count']}"
            )
    for i in range(len(a_groups), len(v_groups)):
        diffs.append(f"#{i + 1}: 변형에만 존재 (N={v_groups[i]['loop_count']})")

    if not diffs:
        return None
    return f"[variant {variant.name}] {', '.join(diffs)}"


# ---------- 디버그 유틸 ----------
def describe_plan(plan: TCPlan) -> str:
    """TCPlan 요약 문자열 (디버그/검증용)."""
    lines = [
        f"=== TC Plan: {os.path.basename(plan.channel_dir)} ===",
        f"Active .sch: {plan.active_sch.name} (size={plan.active_sch.size}B, "
        f"mtime={plan.active_sch.mtime:.0f})",
        f"Variants   : {len(plan.variants)}"
        + (", ".join(f" {v.name}" for v in plan.variants) if plan.variants else ""),
        f"Total TC   : {plan.max_tc}",
        f"Groups     : {len(plan.groups)}",
        "",
    ]
    for g in plan.groups:
        rng = (
            f"TC {g.tc_start:>4}"
            if g.loop_count == 1
            else f"TC {g.tc_start:>4}-{g.tc_end:<4}({g.loop_count})"
        )
        lines.append(f"  #{g.idx + 1:<3} {g.category:<18} {rng}  {g.body_desc}")
    if plan.warnings:
        lines.append("")
        lines.append("Warnings:")
        for w in plan.warnings:
            lines.append(f"  - {w}")
    return "\n".join(lines)


# ---------- CLI 진입점 ----------
if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 2:
        ch_dir = sys.argv[1]
    else:
        # 기본: ch55 floating 데이터
        ch_dir = (
            r"C:\Users\Ryu\battery\python\BDT_dev\DataTool_dev_code\data\exp_data"
            r"\복합floating\260413_261230_05_문현규_3650mAh_Cosmx 25SiC 타사spl floating ch55 61"
            r"\M01Ch055[055]"
        )

    plan = build_tc_plan(ch_dir)
    if plan is None:
        print(f"No valid .sch found in: {ch_dir}")
        sys.exit(1)

    # Windows 콘솔 UTF-8
    try:
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

    print(describe_plan(plan))
