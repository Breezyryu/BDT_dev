"""tc_plan_verify.py — TCPlan vs SaveEndData col27 실측 대조 스크립트.

채널 디렉토리가 주어지면:
  1) tc_plan.build_tc_plan()으로 .sch 기반 TCPlan 생성
  2) Restore/SaveEndData.csv 읽어서 실측 (StepNo, TC) 쌍 추출
  3) TCPlan.resolve_tc(StepNo, rep_idx)로 예측 TC 산출
  4) 일치/불일치 통계 + 샘플 출력

오프셋 자동 감지 옵션도 제공 (step_num_offset 을 0~3 범위에서 스캔).
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict
from typing import Optional

import pandas as pd

# tc_plan 모듈 로드 (동일 폴더)
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)
from tc_plan import TCPlan, build_tc_plan, describe_plan  # noqa: E402


def find_save_end_csv(channel_dir: str) -> Optional[str]:
    """채널 폴더 내 Restore/*SaveEndData*.csv 검색."""
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
    # 가장 큰 파일(최신 누적)을 우선
    return max(candidates, key=lambda p: os.path.getsize(p))


def load_save_end(csv_path: str) -> pd.DataFrame:
    """SaveEndData.csv → DataFrame. 주요 컬럼만 반환."""
    df = pd.read_csv(
        csv_path,
        sep=",",
        header=None,
        encoding="cp949",
        engine="c",
        on_bad_lines="skip",
    )
    # 컬럼: 0=RecIdx, 2=StepType, 7=StepNo, 27=TC
    return df[[0, 2, 7, 27]].rename(
        columns={0: "RecIdx", 2: "StepType", 7: "StepNo", 27: "TC"}
    )


def compute_rep_indices(save_end: pd.DataFrame) -> pd.DataFrame:
    """각 (StepNo, TC) 행에 rep_idx 컬럼 추가.

    rep_idx: 해당 StepNo가 TC 내 몇 번째 반복인지 (TC 내 첫 등장 = 0).
    실제로는 같은 TC 안에서 StepNo가 반복되는 일은 거의 없음 (Loop 내 StepNo는
    전반복 동일). TC 번호 자체가 반복 인덱스 역할.
    """
    save_end = save_end.copy()
    save_end["rep_idx"] = 0  # 단순화: 현재는 사용하지 않음
    return save_end


def verify_plan(
    plan: TCPlan,
    save_end: pd.DataFrame,
) -> dict:
    """plan vs 실측 대조 결과 dict 반환."""
    total = len(save_end)
    matches = 0
    missing = 0           # StepNo가 plan에 없음
    mismatches: list[tuple] = []   # (RecIdx, StepNo, actual_tc, predicted_tc)

    # plan의 그룹 순서대로, 각 그룹에 속한 StepNo들을 시퀀셜하게 소비
    # 전제: 실측 데이터는 시간 순서 = TC 오름차순 → 그룹 순서와 일치
    # 따라서 plan.tc_to_group[tc] 로 예측 TC가 올바른지 확인

    for row in save_end.itertuples(index=False):
        rec, stype, sn, actual_tc = row.RecIdx, row.StepType, row.StepNo, row.TC
        grp_start = plan.step_to_tc_start.get(int(sn))
        if grp_start is None:
            missing += 1
            continue
        grp = plan.tc_to_group.get(grp_start)
        if grp is None:
            missing += 1
            continue

        # 예측: 이 StepNo가 속한 그룹의 TC 범위 안에 actual_tc가 있으면 일치
        # (Loop의 rep_idx는 SaveEndData에서 tc 자체가 rep_idx로 동작)
        if grp.tc_start <= int(actual_tc) <= grp.tc_end:
            matches += 1
        else:
            mismatches.append((int(rec), int(sn), int(actual_tc), grp_start))

    return {
        "total": total,
        "matches": matches,
        "missing": missing,
        "mismatches": mismatches,
        "match_rate": matches / total if total else 0.0,
    }


def scan_offsets(channel_dir: str, save_end: pd.DataFrame) -> list[tuple[int, dict]]:
    """step_num_offset을 0~3으로 스캔하여 일치율이 높은 값 탐색."""
    results = []
    for off in range(4):
        p = build_tc_plan(channel_dir, step_num_offset=off)
        if p is None:
            continue
        r = verify_plan(p, save_end)
        results.append((off, r))
    return results


def verify_channel(channel_dir: str, verbose: bool = True) -> Optional[dict]:
    """단일 채널 검증. verbose=True면 요약 출력."""
    se_path = find_save_end_csv(channel_dir)
    if se_path is None:
        if verbose:
            print(f"[SKIP] SaveEndData.csv 없음: {channel_dir}")
        return None

    save_end = load_save_end(se_path)
    if save_end.empty:
        if verbose:
            print(f"[SKIP] SaveEndData 비어있음: {se_path}")
        return None

    # 오프셋 자동 스캔
    scan = scan_offsets(channel_dir, save_end)
    if not scan:
        if verbose:
            print(f"[SKIP] .sch 없음: {channel_dir}")
        return None

    best_off, best_res = max(scan, key=lambda x: x[1]["match_rate"])
    plan = build_tc_plan(channel_dir, step_num_offset=best_off)

    if verbose:
        name = os.path.basename(channel_dir)
        print(f"\n=== {name} ===")
        print(f"SaveEndData rows : {best_res['total']}")
        print(f"Best offset      : +{best_off}")
        print(f"Match rate       : {best_res['match_rate']*100:.1f}%"
              f"  ({best_res['matches']}/{best_res['total']})")
        print(f"Missing StepNo   : {best_res['missing']}")
        print(f"TC mismatches    : {len(best_res['mismatches'])}")
        if best_res["mismatches"][:5]:
            print("  샘플 불일치 (RecIdx, StepNo, actual_TC, predicted_tc_start):")
            for row in best_res["mismatches"][:5]:
                print(f"    {row}")
        # 다른 오프셋들과 비교
        print("  오프셋 스캔:")
        for off, r in scan:
            marker = " *" if off == best_off else "  "
            print(f"   {marker} offset=+{off}: {r['match_rate']*100:5.1f}% "
                  f"({r['matches']}/{r['total']})")

    return {
        "channel": channel_dir,
        "best_offset": best_off,
        "result": best_res,
        "plan": plan,
    }


def find_channel_dirs(base: str, max_channels: int = 50) -> list[str]:
    """exp_data 아래에서 .sch + Restore 둘 다 있는 채널 폴더 수집."""
    found = []
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
            # sub_dir 아래 M01ChXXX 채널 탐색
            for ch_name in os.listdir(sub_dir):
                ch_dir = os.path.join(sub_dir, ch_name)
                if not os.path.isdir(ch_dir):
                    continue
                if not ch_name.startswith("M"):
                    continue
                # .sch + Restore 존재 확인
                has_sch = any(f.lower().endswith(".sch") for f in os.listdir(ch_dir))
                has_restore = os.path.isdir(os.path.join(ch_dir, "Restore"))
                if has_sch and has_restore:
                    found.append(ch_dir)
                    if len(found) >= max_channels:
                        return found
    return found


if __name__ == "__main__":
    # Windows 콘솔 UTF-8
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

    if len(sys.argv) >= 2:
        # 단일 채널 모드
        ch = sys.argv[1]
        verify_channel(ch)
    else:
        # 전수 탐색 모드 — exp_data 하위 전체
        base = r"C:\Users\Ryu\battery\python\BDT_dev\DataTool_dev_code\data\exp_data"
        channels = find_channel_dirs(base, max_channels=20)
        print(f"{len(channels)}개 채널 검증 시작\n")

        agg_total = 0
        agg_match = 0
        offset_counts = defaultdict(int)
        low_match = []

        for ch in channels:
            r = verify_channel(ch, verbose=False)
            if r is None:
                continue
            res = r["result"]
            agg_total += res["total"]
            agg_match += res["matches"]
            offset_counts[r["best_offset"]] += 1
            rate = res["match_rate"]
            name = os.path.basename(os.path.dirname(ch)) + "/" + os.path.basename(ch)
            status = "✓" if rate >= 0.95 else ("~" if rate >= 0.5 else "✗")
            print(f"  {status} off=+{r['best_offset']}  {rate*100:5.1f}%  "
                  f"({res['matches']:>5}/{res['total']:<5})  {name}")
            if rate < 0.95:
                low_match.append(r)

        print()
        print("=" * 70)
        print(f"전체 일치율: {agg_match/agg_total*100:.2f}%  ({agg_match}/{agg_total})")
        print(f"오프셋 분포: {dict(offset_counts)}")
        if low_match:
            print(f"\n일치율 <95% 채널 {len(low_match)}개 — 상세 분석 필요")
