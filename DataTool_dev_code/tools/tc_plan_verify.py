"""tc_plan_verify.py — TCPlan/ExpandedSchedule vs 실측 대조 (하이브리드).

검증 전략:
    1. .sch → build_tc_plan() + expand_schedule() 로 (StepNo, TC, occurrence) 시퀀스 생성
       (GOTO 재순환 포함, LOOP 반복 포함)
    2. SaveEndData.csv가 있으면 (RecIdx, StepNo, TC) 실측과 대조 → 정확도 리포트
       없으면 .cyc StepNo 시퀀스 기반 검증만 수행 (CSV-less 모드)
    3. step_num_offset 자동 스캔 (0~3)

하이브리드 포인트:
    - .sch 구조(스케줄 설계) + .cyc 실측(진행도) + CSV(있으면 정답지)
    - 1시간 주기 .cyc 업데이트에 의존해도 TC가 정확 (재순환 회차를 occurrence로 추적)
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict
from typing import Optional

import pandas as pd

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)
from tc_plan import TCPlan, build_tc_plan, describe_plan  # noqa: E402
from sch_expander import ExpandedSchedule, expand_schedule  # noqa: E402


# ---------- SaveEndData 로드 ----------
def find_save_end_csv(channel_dir: str) -> Optional[str]:
    restore = os.path.join(channel_dir, "Restore")
    if not os.path.isdir(restore):
        return None
    candidates = [
        os.path.join(restore, n)
        for n in os.listdir(restore)
        if "SaveEndData" in n and n.lower().endswith(".csv")
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda p: os.path.getsize(p))


def load_save_end(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(
        csv_path,
        sep=",",
        header=None,
        encoding="cp949",
        engine="c",
        on_bad_lines="skip",
    )
    return df[[0, 2, 7, 27]].rename(
        columns={0: "RecIdx", 2: "StepType", 7: "StepNo", 27: "TC"}
    )


# ---------- Expanded 시퀀스 → (step_num, occurrence) → TC 룩업 ----------
def build_occurrence_index(expanded: ExpandedSchedule) -> dict[tuple[int, int], int]:
    """(.sch step_num, occurrence) → TC 매핑."""
    idx: dict[tuple[int, int], int] = {}
    for es in expanded.steps:
        idx[(es.step_num, es.occurrence)] = es.tc
    return idx


# ---------- 검증 ----------
def verify_with_expanded(
    plan: TCPlan,
    expanded: ExpandedSchedule,
    save_end: pd.DataFrame,
    step_num_offset: int = 0,
) -> dict:
    """expanded sequence 기반 대조.

    save_end의 각 행에 대해:
      - StepNo - step_num_offset = .sch step_num
      - 해당 step_num이 몇 번째 등장인지 카운트 (occurrence)
      - (step_num, occurrence) 의 예측 TC와 실측 TC 대조
    """
    occ_idx = build_occurrence_index(expanded)

    total = len(save_end)
    matches = 0
    missing = 0                # step_num이 expanded에 없음 (.sch 밖)
    out_of_range = 0           # occurrence가 넘침 (max_cycles 부족 등)
    mismatches: list[tuple] = []

    occ_counter: dict[int, int] = defaultdict(int)

    for row in save_end.itertuples(index=False):
        rec, sn, actual_tc = int(row.RecIdx), int(row.StepNo), int(row.TC)
        sch_sn = sn - step_num_offset
        occ = occ_counter[sch_sn]
        occ_counter[sch_sn] += 1

        predicted = occ_idx.get((sch_sn, occ))
        if predicted is None:
            # occurrence가 expanded 범위 밖
            if (sch_sn, 0) not in occ_idx:
                missing += 1
            else:
                out_of_range += 1
            continue

        if predicted == actual_tc:
            matches += 1
        else:
            mismatches.append((rec, sn, occ, actual_tc, predicted))

    return {
        "total": total,
        "matches": matches,
        "missing": missing,
        "out_of_range": out_of_range,
        "mismatches": mismatches,
        "match_rate": matches / total if total else 0.0,
    }


def estimate_required_cycles(
    plan_max_tc: int, actual_max_tc: int, safety: float = 1.5
) -> int:
    """실측 최대 TC를 커버하기 위한 max_cycles 추정."""
    if plan_max_tc <= 0:
        return 50
    ratio = actual_max_tc / plan_max_tc
    return max(int(ratio * safety) + 3, 10)


def scan_offsets_with_expanded(
    channel_dir: str,
    save_end: pd.DataFrame,
) -> list[tuple[int, dict, ExpandedSchedule]]:
    """오프셋 0~3 스캔 + 각 오프셋마다 expanded 기반 검증."""
    results = []

    # 기본 plan으로 max_tc 추정
    base_plan = build_tc_plan(channel_dir, step_num_offset=0)
    if base_plan is None:
        return []

    actual_max_tc = int(save_end["TC"].max()) if not save_end.empty else 1
    max_cycles = estimate_required_cycles(base_plan.max_tc, actual_max_tc)

    # expanded는 offset 무관 (원본 .sch step_num 기준)
    expanded = expand_schedule(
        base_plan.active_sch.path, max_cycles=max_cycles
    )
    if expanded is None:
        return []

    for off in range(4):
        p = build_tc_plan(channel_dir, step_num_offset=off)
        if p is None:
            continue
        r = verify_with_expanded(p, expanded, save_end, step_num_offset=off)
        results.append((off, r, expanded))
    return results


# ---------- CSV-less 모드 (향후 .cyc 직접 파싱) ----------
def verify_csv_less(
    channel_dir: str,
) -> dict:
    """SaveEndData 없을 때: .sch 구조 요약만 리포트.

    (향후 P3에서 .cyc StepNo 시퀀스 직접 파싱으로 확장 예정)
    """
    plan = build_tc_plan(channel_dir)
    if plan is None:
        return {"status": "no_sch"}

    expanded = expand_schedule(plan.active_sch.path, max_cycles=100)
    if expanded is None:
        return {"status": "expand_failed"}

    return {
        "status": "plan_only",
        "plan_max_tc": plan.max_tc,
        "expanded_max_tc_at_100_cycles": expanded.max_tc,
        "n_cycles_simulated": expanded.n_cycles,
        "groups": len(plan.groups),
        "truncated": expanded.truncated,
    }


# ---------- 채널 단위 검증 ----------
def verify_channel(channel_dir: str, verbose: bool = True) -> Optional[dict]:
    se_path = find_save_end_csv(channel_dir)
    if se_path is None:
        if verbose:
            print(f"[CSV-less] {os.path.basename(channel_dir)}")
            info = verify_csv_less(channel_dir)
            print(f"  {info}")
        return None

    save_end = load_save_end(se_path)
    if save_end.empty:
        if verbose:
            print(f"[SKIP] SaveEndData 비어있음: {se_path}")
        return None

    results = scan_offsets_with_expanded(channel_dir, save_end)
    if not results:
        if verbose:
            print(f"[SKIP] .sch 없음: {channel_dir}")
        return None

    best_off, best_res, expanded = max(results, key=lambda x: x[1]["match_rate"])
    plan = build_tc_plan(channel_dir, step_num_offset=best_off)

    if verbose:
        name = os.path.basename(channel_dir)
        print(f"\n=== {name} ===")
        print(f"SaveEndData rows : {best_res['total']}")
        print(f"Actual TC max    : {int(save_end['TC'].max())}")
        print(f"Plan (1회전) max : {plan.max_tc}")
        print(f"Expanded max TC  : {expanded.max_tc} (cycles={expanded.n_cycles}"
              f"{', truncated' if expanded.truncated else ''})")
        print(f"Best offset      : +{best_off}")
        print(f"Match rate       : {best_res['match_rate']*100:.1f}%"
              f"  ({best_res['matches']}/{best_res['total']})")
        print(f"Missing StepNo   : {best_res['missing']}")
        print(f"Out of range     : {best_res['out_of_range']}")
        print(f"TC mismatches    : {len(best_res['mismatches'])}")
        if best_res["mismatches"][:5]:
            print("  샘플 불일치 (RecIdx, StepNo, occ, actual_TC, predicted_TC):")
            for row in best_res["mismatches"][:5]:
                print(f"    {row}")
        print("  오프셋 스캔:")
        for off, r, _ in results:
            marker = " *" if off == best_off else "  "
            print(f"   {marker} offset=+{off}: {r['match_rate']*100:5.1f}% "
                  f"({r['matches']}/{r['total']})")

    return {
        "channel": channel_dir,
        "best_offset": best_off,
        "result": best_res,
        "plan": plan,
        "expanded": expanded,
    }


# ---------- 전수 스캔 ----------
def find_channel_dirs(base: str, max_channels: int = 50) -> list[str]:
    found: list[str] = []
    if not os.path.isdir(base):
        return found
    for exp_name in os.listdir(base):
        exp_dir = os.path.join(base, exp_name)
        if not os.path.isdir(exp_dir):
            continue
        for sub_name in os.listdir(exp_dir):
            sub_dir = os.path.join(exp_dir, sub_name)
            if not os.path.isdir(sub_dir):
                continue
            for ch_name in os.listdir(sub_dir):
                ch_dir = os.path.join(sub_dir, ch_name)
                if not os.path.isdir(ch_dir):
                    continue
                if not ch_name.startswith("M"):
                    continue
                has_sch = any(f.lower().endswith(".sch") for f in os.listdir(ch_dir))
                if has_sch:
                    found.append(ch_dir)
                    if len(found) >= max_channels:
                        return found
    return found


if __name__ == "__main__":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

    if len(sys.argv) >= 2:
        verify_channel(sys.argv[1])
    else:
        base = r"C:\Users\Ryu\battery\python\BDT_dev\DataTool_dev_code\data\exp_data"
        channels = find_channel_dirs(base, max_channels=30)
        print(f"{len(channels)}개 채널 검증 시작\n")

        agg_total = 0
        agg_match = 0
        offset_counts: dict[int, int] = defaultdict(int)
        low_match: list[dict] = []
        csv_less: list[str] = []

        for ch in channels:
            r = verify_channel(ch, verbose=False)
            if r is None:
                # CSV-less 또는 .sch 없음 — 간단 라인
                se = find_save_end_csv(ch)
                if se is None:
                    csv_less.append(ch)
                    name = os.path.basename(os.path.dirname(ch)) + "/" + os.path.basename(ch)
                    print(f"  · CSV-less      {name}")
                continue
            res = r["result"]
            exp = r["expanded"]
            agg_total += res["total"]
            agg_match += res["matches"]
            offset_counts[r["best_offset"]] += 1
            rate = res["match_rate"]
            name = os.path.basename(os.path.dirname(ch)) + "/" + os.path.basename(ch)
            status = "✓" if rate >= 0.95 else ("~" if rate >= 0.5 else "✗")
            trunc = "T" if exp.truncated else " "
            print(f"  {status} off=+{r['best_offset']}  {rate*100:5.1f}%  "
                  f"({res['matches']:>5}/{res['total']:<5}) cyc={exp.n_cycles:<3}{trunc} {name}")
            if rate < 0.95:
                low_match.append(r)

        print()
        print("=" * 70)
        if agg_total > 0:
            print(f"전체 일치율: {agg_match/agg_total*100:.2f}%  ({agg_match}/{agg_total})")
        print(f"오프셋 분포: {dict(offset_counts)}")
        print(f"CSV-less 채널: {len(csv_less)}개")
        if low_match:
            print(f"일치율 <95%: {len(low_match)}개")
