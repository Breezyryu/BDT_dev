"""임계값 교차검증 — extract_schedule_structure_from_sch()

SEU4 2335mAh + Gen4p 4905mAh 전체 .sch 파일로 조정된 임계값 검증.
"""
import sys
sys.path.insert(0, "analysis_dev_env")
from parse_pne_schedule import (
    parse_pne_schedule,
    extract_accel_pattern_from_sch,
    extract_schedule_structure_from_sch,
)
from pathlib import Path
import re


ALL_SCH = sorted(Path("rawdata").rglob("*.sch"))


def guess_capacity(path: Path) -> float:
    """폴더명/파일명에서 용량 추정."""
    s = str(path)
    m = re.search(r"(\d+(?:\.\d+)?)\s*mAh", s, re.IGNORECASE)
    return float(m.group(1)) if m else 0.0


def main():
    print(f"{'='*80}")
    print(f"임계값 교차검증 — {len(ALL_SCH)}개 .sch 파일")
    print(f"{'='*80}\n")

    ok = 0
    fail = 0
    results = []

    for sf in ALL_SCH:
        cap = guess_capacity(sf)
        r = extract_schedule_structure_from_sch(sf, capacity=cap)
        if r is None:
            fail += 1
            print(f"  ✗ {sf.name}: 파싱 실패")
            continue

        ok += 1
        results.append((sf, r, cap))

        short = sf.name[:55]
        cats = [s["category"] for s in r["sections"] if s["category"] != "구간경계"]
        uniq_cats = sorted(set(cats))

        print(f"  ✓ {short}")
        print(f"    type={r['schedule_type']}  designed={r['total_designed_cycles']}cy"
              f"  블록={r['n_accel_blocks']}  rss={r['has_rss']}  gitt={r['has_gitt_hppc']}")
        print(f"    패턴: {r['pattern_string'][:80]}")
        print(f"    카테고리: {uniq_cats}")
        print()

    # 요약
    print(f"\n{'='*80}")
    print(f"요약: {ok}/{ok+fail}개 파싱 성공")
    print(f"{'='*80}")

    from collections import Counter
    type_counts = Counter(r["schedule_type"] for _, r, _ in results)
    print(f"\n스케줄 타입 분포:")
    for t, cnt in type_counts.most_common():
        print(f"  {t:40s} : {cnt}개")

    # 가속수명 블록 통계
    accel_results = [(sf, r, c) for sf, r, c in results if r["n_accel_blocks"] > 0]
    if accel_results:
        print(f"\n가속수명 스케줄 상세 ({len(accel_results)}개):")
        for sf, r, cap in accel_results:
            blocks = r["accel_blocks"]
            loops = [b["loop_count"] for b in blocks]
            print(f"  {sf.name[:50]:50s}  블록={len(blocks)}  "
                  f"LOOP={loops}  합계={r['total_designed_cycles']}cy")

    # GITT/HPPC 확인
    gitt_results = [(sf, r) for sf, r, _ in results if r["has_gitt_hppc"]]
    if gitt_results:
        print(f"\nGITT/HPPC 스케줄 ({len(gitt_results)}개):")
        for sf, r in gitt_results:
            gitt_secs = [s for s in r["sections"] if s["category"] == "GITT/HPPC"]
            for gs in gitt_secs:
                crates = gs.get("crates", [])
                print(f"  {sf.name[:50]:50s}  LOOP={gs['loop_count']}  "
                      f"CHG={gs['n_chg']} DCHG={gs['n_dchg']}  C-rates={crates}")


if __name__ == "__main__":
    main()
