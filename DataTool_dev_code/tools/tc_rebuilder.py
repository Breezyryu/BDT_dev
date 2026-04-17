"""tc_rebuilder.py — 하이브리드 TC 재구성 (SaveEndData + .cyc + .sch).

3-Tier 전략:
    Tier 1 (최선, 자정 이후 Restore 가능):
        SaveEndData.csv col[27] TotalCycle 직접 사용 → 100% 정확
        col[28] CurrentCycle로 Loop 반복 위치 파악
    Tier 2 (자정 전, .cyc만 있음):
        .cyc StepType=8 (Loop 마커) 경계마다 TC++
        "장비가 SaveEndData에 기록하는 규칙을 .cyc에 그대로 적용"
    Tier 3 (메타 라벨):
        .sch 그룹 구조로 각 TC의 카테고리(RPT/ACCEL/RSS_DCIR/...) 부여

설계 근거:
    사용자 제공 SaveEndData 스키마에서 col[27]이 GOTO 재순환을 포함한
    누적 TC를 장비가 직접 기록. 재구성 필요 없음.
    col[7] Step이 GOTO 시 리셋되는 관찰도 이 규칙에 부합.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)
from save_end_schema import (  # noqa: E402
    IDX_CURRENT_CYCLE,
    IDX_INDEX,
    IDX_STEP,
    IDX_STEP_TYPE,
    IDX_TOTAL_CYCLE,
    IDX_END_STATE,
    STEP_TYPE_LOOP,
)
from tc_plan import TCGroup, TCPlan, build_tc_plan  # noqa: E402


# ---------- Tier 1: SaveEndData ground truth ----------
@dataclass
class MeasuredTC:
    """채널의 실측 TC 시퀀스 (SaveEndData 또는 .cyc 추론)."""

    source: str                             # "save_end" | "cyc_inferred"
    rec_indices: list[int]
    step_nos: list[int]
    step_types: list[int]
    tcs: list[int]
    current_cycles: list[int]               # Loop 내 반복 번호
    end_states: list[int]
    n_records: int = 0

    def __post_init__(self) -> None:
        self.n_records = len(self.rec_indices)


def load_from_save_end(csv_path: str) -> Optional[MeasuredTC]:
    """Tier 1: SaveEndData.csv col[27]을 그대로 ground truth로 로드."""
    try:
        df = pd.read_csv(
            csv_path, sep=",", header=None, encoding="cp949",
            engine="c", on_bad_lines="skip",
        )
    except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError,
            UnicodeDecodeError):
        return None
    if df.empty:
        return None

    return MeasuredTC(
        source="save_end",
        rec_indices=df[IDX_INDEX].astype(int).tolist(),
        step_nos=df[IDX_STEP].astype(int).tolist(),
        step_types=df[IDX_STEP_TYPE].astype(int).tolist(),
        tcs=df[IDX_TOTAL_CYCLE].astype(int).tolist(),
        current_cycles=df[IDX_CURRENT_CYCLE].astype(int).tolist(),
        end_states=df[IDX_END_STATE].astype(int).tolist(),
    )


# ---------- Tier 2: .cyc 기반 TC 재구성 ----------
def rebuild_tc_from_step_sequence(
    step_nos: list[int],
    step_types: list[int],
    initial_tc: int = 1,
) -> list[int]:
    """StepType=8 (Loop 마커) 만나면 TC +=1 규칙.

    장비가 SaveEndData에 기록하는 규칙과 동일. GOTO 시맨틱 무관.

    Parameters
    ----------
    step_nos : list[int]
    step_types : list[int]
    initial_tc : int
        첫 TC 번호 (기본 1).

    Returns
    -------
    list[int]
        step_nos와 동일 길이의 TC 시퀀스.
    """
    out: list[int] = []
    tc = initial_tc
    for stype in step_types:
        out.append(tc)
        if stype == STEP_TYPE_LOOP:
            tc += 1
    return out


def infer_current_cycle(
    step_nos: list[int],
    step_types: list[int],
    tcs: list[int],
) -> list[int]:
    """Loop 내 반복 번호 추정.

    규칙: 같은 그룹(연속된 Loop 내부) 안에서 TC가 증가하면 CurrentCycle +=1.
    그룹 전환(StepType=8 이후 StepNo가 이전 그룹 범위 밖으로 점프)하면 CurC=1 리셋.
    """
    if not step_nos:
        return []

    out: list[int] = []
    curc = 1
    prev_tc = tcs[0]
    # "그룹 전환" 감지: StepNo가 이전 StepType=8 이후로 크게 감소하거나 새 범위 진입
    # 간단 휴리스틱: 이전 step_no보다 낮으면 새 그룹 시작 (= CurC 리셋)
    prev_sn = None

    for sn, stype, tc in zip(step_nos, step_types, tcs):
        if prev_sn is not None and sn < prev_sn and prev_tc == tc:
            # 같은 TC 안에서 StepNo 감소 → 이상 (드물음)
            pass

        if tc != prev_tc:
            # TC 증가
            if prev_sn is not None and sn < prev_sn:
                # 그룹 전환 (재순환 또는 다음 그룹) → CurC=1
                curc = 1
            else:
                # 같은 그룹 내 반복 → CurC++
                curc += 1
            prev_tc = tc

        out.append(curc)
        prev_sn = sn

    return out


# ---------- Tier 3: .sch 메타 라벨 ----------
def label_tcs_with_category(
    plan: TCPlan,
    measured: MeasuredTC,
) -> dict[int, str]:
    """실측 각 TC에 .sch 그룹 카테고리 부여.

    단순 매핑: measured.step_nos를 offset 보정 후 plan.step_to_tc_start로 조회.
    재순환으로 TC가 plan.max_tc를 넘어도, StepNo는 .sch 내 스텝이므로 매핑 가능.
    """
    # offset 자동 감지 (단순): 가장 많은 매칭을 주는 offset 선택
    best_off, best_matches = 0, 0
    for off in range(4):
        m = sum(
            1
            for sn in measured.step_nos
            if (sn - off) in plan.step_to_tc_start
        )
        if m > best_matches:
            best_matches = m
            best_off = off

    labels: dict[int, str] = {}
    for sn, tc in zip(measured.step_nos, measured.tcs):
        if tc in labels:
            continue
        grp_start = plan.step_to_tc_start.get(sn - best_off)
        if grp_start is None:
            continue
        grp = plan.tc_to_group.get(grp_start)
        if grp is not None:
            labels[tc] = grp.category
    return labels


# ---------- 상위 API ----------
@dataclass
class ChannelTC:
    """채널의 TC 정보 전체."""

    channel_dir: str
    measured: Optional[MeasuredTC]
    plan: Optional[TCPlan]
    tc_to_category: dict[int, str] = field(default_factory=dict)
    step_num_offset: int = 0
    tier: str = "none"                      # "save_end" | "cyc_inferred" | "plan_only"


def find_save_end_csv(channel_dir: str) -> Optional[str]:
    restore = os.path.join(channel_dir, "Restore")
    if not os.path.isdir(restore):
        return None
    cands = [
        os.path.join(restore, n)
        for n in os.listdir(restore)
        if "SaveEndData" in n and n.lower().endswith(".csv")
    ]
    if not cands:
        return None
    return max(cands, key=lambda p: os.path.getsize(p))


def build_channel_tc(channel_dir: str) -> ChannelTC:
    """채널의 TC 정보를 3-Tier 전략으로 구성."""
    plan = build_tc_plan(channel_dir)

    # Tier 1: SaveEndData
    se_path = find_save_end_csv(channel_dir)
    if se_path is not None:
        m = load_from_save_end(se_path)
        if m is not None:
            tc_cat = label_tcs_with_category(plan, m) if plan is not None else {}
            return ChannelTC(
                channel_dir=channel_dir,
                measured=m,
                plan=plan,
                tc_to_category=tc_cat,
                tier="save_end",
            )

    # Tier 2: .cyc only (향후 cyc_reader 통합 시)
    # 현재는 placeholder — P3에서 구현
    # .cyc 파싱 후 (step_nos, step_types) 추출 필요.

    # Tier 3: plan only
    return ChannelTC(
        channel_dir=channel_dir,
        measured=None,
        plan=plan,
        tc_to_category={},
        tier="plan_only" if plan is not None else "none",
    )


# ---------- 검증 ----------
def compare_rebuilt_with_measured(m: MeasuredTC) -> dict:
    """rebuild_tc_from_step_sequence 결과가 실측 col[27]과 일치하는지 검증.

    SaveEndData의 첫 TC로 initial_tc를 맞추면, StepType=8 규칙만으로
    나머지 TC가 모두 재현되는지 확인.
    """
    if not m.tcs:
        return {"total": 0, "matches": 0, "rate": 0.0}

    rebuilt = rebuild_tc_from_step_sequence(
        m.step_nos, m.step_types, initial_tc=m.tcs[0]
    )
    matches = sum(1 for a, b in zip(rebuilt, m.tcs) if a == b)
    total = len(m.tcs)
    return {
        "total": total,
        "matches": matches,
        "rate": matches / total if total else 0.0,
        "rebuilt": rebuilt,
        "actual": list(m.tcs),
    }


# ---------- CLI ----------
if __name__ == "__main__":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

    if len(sys.argv) < 2:
        print("Usage: tc_rebuilder.py <channel_dir>")
        sys.exit(1)

    ch = sys.argv[1]
    info = build_channel_tc(ch)

    print(f"=== {os.path.basename(ch)} ===")
    print(f"Tier           : {info.tier}")
    if info.measured:
        m = info.measured
        print(f"Records        : {m.n_records}")
        print(f"TC range       : {min(m.tcs)} ~ {max(m.tcs)}")

        # StepType=8 규칙 검증
        verify = compare_rebuilt_with_measured(m)
        print(f"\n[Tier 2 규칙 검증 (StepType=8 → TC++)]")
        print(f"  재구성 일치율: {verify['rate']*100:.2f}% "
              f"({verify['matches']}/{verify['total']})")
        if verify['matches'] != verify['total']:
            # 불일치 샘플
            mism = [
                (i, a, b) for i, (a, b) in enumerate(
                    zip(verify['actual'], verify['rebuilt'])
                ) if a != b
            ]
            print(f"  불일치 {len(mism)}개, 첫 5개:")
            for i, actual, rebuilt in mism[:5]:
                print(f"    idx={i}: actual={actual}, rebuilt={rebuilt}, "
                      f"StepNo={m.step_nos[i]}, ST={m.step_types[i]}")

    if info.plan:
        print(f"\n[.sch 카테고리 매핑]")
        print(f"  plan max_tc : {info.plan.max_tc}")
        print(f"  라벨링된 TC: {len(info.tc_to_category)}개")
        for tc in sorted(info.tc_to_category.keys())[:20]:
            print(f"    TC {tc:>3}: {info.tc_to_category[tc]}")
