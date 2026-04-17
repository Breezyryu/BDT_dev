"""sch_expander.py — .sch 가상 실행기 (LOOP + GOTO 재순환 포함).

TCPlan이 정적으로 계산하는 "1회전" TC 범위를 넘어, GOTO로 재순환되는 전체
실행 시퀀스를 시뮬레이션하여 (step_num, tc, occurrence_idx)를 산출한다.

핵심 규칙:
    LOOP(N)     : 직전 body 구간을 N-1회 더 반복 (TC는 매 반복마다 +1)
    REST_SAFE   : 흐름 제어, TC 변화 없이 skip
    GOTO(target): target StepNo로 점프 (뒤로 점프 = 재순환)
                  target=0 또는 target >= 현재 StepNo → 종료

안전장치: 최대 반복 수 (max_iterations) 초과 시 경고 + 종료.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Optional

# 동일 폴더의 tc_plan 재사용
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)
from tc_plan import parse_sch  # noqa: E402


@dataclass
class ExpandedStep:
    """가상 실행 시 방문된 스텝 한 개."""

    step_num: int          # .sch 원본 step_num (offset 미적용)
    tc: int                # 이 스텝이 속한 TC (1-based, 누적)
    occurrence: int        # 이 step_num이 시퀀스 내 몇 번째 등장인지 (0-based)
    step_type: str         # CHG_CC/REST/...
    in_cycle: int          # 재순환 회차 (0=첫번째, 1=GOTO 후 첫 재순환, ...)


@dataclass
class ExpandedSchedule:
    """가상 실행 결과."""

    steps: list[ExpandedStep] = field(default_factory=list)
    max_tc: int = 0
    n_cycles: int = 1                 # 총 재순환 횟수 (GOTO 기준)
    truncated: bool = False           # max_iterations 도달로 중단됐는지
    warnings: list[str] = field(default_factory=list)

    def occurrences_of(self, step_num: int) -> list[ExpandedStep]:
        """특정 step_num의 모든 등장."""
        return [s for s in self.steps if s.step_num == step_num]

    def tc_of_occurrence(self, step_num: int, occurrence: int) -> Optional[int]:
        """특정 step_num의 occurrence-번째 등장의 TC."""
        occs = self.occurrences_of(step_num)
        if 0 <= occurrence < len(occs):
            return occs[occurrence].tc
        return None


def _find_body_start_before(steps: list[dict], loop_idx: int) -> int:
    """steps[loop_idx]가 LOOP일 때, 그 body의 시작 인덱스 찾기.

    body 시작 = 직전 LOOP/REST_SAFE/GOTO 다음 스텝 또는 steps 시작.
    """
    i = loop_idx - 1
    while i >= 0:
        t = steps[i]["type"]
        if t in ("LOOP", "REST_SAFE", "GOTO"):
            return i + 1
        i -= 1
    return 0


def expand_schedule(
    sch_path: str,
    max_iterations: int = 500_000,
    max_cycles: int = 5_000,
) -> Optional[ExpandedSchedule]:
    """.sch를 가상 실행하여 전체 스텝 시퀀스 생성.

    Parameters
    ----------
    sch_path : str
        .sch 파일 경로.
    max_iterations : int
        가상 실행 총 스텝 방문 상한 (무한 루프 방지).
    max_cycles : int
        GOTO 재순환 최대 횟수.

    Returns
    -------
    ExpandedSchedule | None
        파싱 실패 시 None.
    """
    steps = parse_sch(sch_path)
    if steps is None or not steps:
        return None

    N = len(steps)
    # step_num → index (0-based) 매핑
    sn_to_idx: dict[int, int] = {s["step_num"]: i for i, s in enumerate(steps)}

    output: list[ExpandedStep] = []
    warnings: list[str] = []

    # 상태
    pc = 0                              # program counter (steps 인덱스)
    tc = 1                              # 현재 TC
    in_cycle = 0                        # 재순환 회차
    occurrence_counter: dict[int, int] = {}  # step_num → 지금까지 등장 수
    loop_state: dict[int, int] = {}     # loop step_num → 남은 반복 수
    iter_count = 0
    truncated = False

    while 0 <= pc < N:
        iter_count += 1
        if iter_count > max_iterations:
            truncated = True
            warnings.append(
                f"max_iterations({max_iterations}) 초과 — TC {tc}에서 중단"
            )
            break

        s = steps[pc]
        t = s["type"]

        if t == "LOOP":
            loop_sn = s["step_num"]
            remaining = loop_state.get(loop_sn, s["loop_count"] - 1)

            if remaining > 0:
                # 직전 body로 되돌아감 (Loop body 재실행)
                loop_state[loop_sn] = remaining - 1
                tc += 1                              # 새 반복 = 새 TC
                body_start_idx = _find_body_start_before(steps, pc)
                pc = body_start_idx
                continue
            else:
                # Loop 완료 — 다음 스텝으로. 단일 N=1 Loop도 여기 도달 전까지 1회 실행 완료.
                # 다음 그룹 진입 준비: TC 증가
                tc += 1
                loop_state.pop(loop_sn, None)
                pc += 1
                continue

        elif t == "REST_SAFE":
            # 그룹 경계 마커, TC 변화 없음
            pc += 1
            continue

        elif t == "GOTO":
            target_sn = s.get("goto_target", 0)
            cur_sn = s["step_num"]

            # PNE 관례:
            #   target=0 → 프로그램 처음(StepNo 1)부터 재시작 (무한 반복)
            #   target=N(N < cur) → StepNo N으로 뒤로 점프 (재순환)
            #   target=N(N > cur) → 앞으로 점프 (드문 케이스, 순차 스킵)
            if target_sn == 0:
                target_idx = 0
                is_restart = True
            else:
                target_idx = sn_to_idx.get(target_sn)
                if target_idx is None:
                    warnings.append(f"GOTO target={target_sn} 미존재 → 종료")
                    break
                is_restart = target_sn < cur_sn

            if is_restart:
                in_cycle += 1
                if in_cycle > max_cycles:
                    truncated = True
                    warnings.append(
                        f"max_cycles({max_cycles}) 초과 — 재순환 {in_cycle}에서 중단"
                    )
                    break
                # 재순환 시 loop_state 리셋 (각 재순환은 독립)
                loop_state = {}

            pc = target_idx
            continue

        else:
            # 일반 body 스텝 (CHG/DCHG/REST/GITT_*)
            sn = s["step_num"]
            occ = occurrence_counter.get(sn, 0)
            output.append(
                ExpandedStep(
                    step_num=sn,
                    tc=tc,
                    occurrence=occ,
                    step_type=t,
                    in_cycle=in_cycle,
                )
            )
            occurrence_counter[sn] = occ + 1
            pc += 1
            continue

    max_tc = max((s.tc for s in output), default=0)
    return ExpandedSchedule(
        steps=output,
        max_tc=max_tc,
        n_cycles=in_cycle + 1,
        truncated=truncated,
        warnings=warnings,
    )


# ---------- CLI ----------
if __name__ == "__main__":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

    if len(sys.argv) < 2:
        print("Usage: sch_expander.py <sch_path> [max_cycles]")
        sys.exit(1)

    sch_path = sys.argv[1]
    max_cyc = int(sys.argv[2]) if len(sys.argv) >= 3 else 50

    exp = expand_schedule(sch_path, max_cycles=max_cyc)
    if exp is None:
        print("Parse failed")
        sys.exit(1)

    print(f"총 방문 스텝: {len(exp.steps)}")
    print(f"Max TC      : {exp.max_tc}")
    print(f"재순환 횟수 : {exp.n_cycles}")
    print(f"Truncated   : {exp.truncated}")
    if exp.warnings:
        print("Warnings:")
        for w in exp.warnings:
            print(f"  - {w}")
    print()
    print("첫 20 스텝:")
    for s in exp.steps[:20]:
        print(f"  SN={s.step_num:>3} TC={s.tc:>3} occ={s.occurrence:<3} "
              f"cyc={s.in_cycle} {s.step_type}")
    print()
    if len(exp.steps) > 20:
        print(f"... 중간 생략 ...")
        print(f"마지막 5 스텝:")
        for s in exp.steps[-5:]:
            print(f"  SN={s.step_num:>3} TC={s.tc:>3} occ={s.occurrence:<3} "
                  f"cyc={s.in_cycle} {s.step_type}")
