"""Tier 2 (.cyc 단독) 전수 검증 — SaveEndData를 ground truth로 사용."""
import os
import sys

sys.path.insert(0, "DataTool_dev_code/tools")
from tc_rebuilder import (
    find_save_end_csv, find_cyc_file,
    load_from_save_end, load_from_cyc,
)

base = r"C:\Users\Ryu\battery\python\BDT_dev\DataTool_dev_code\data\exp_data"

# 채널 수집
channels = []
for root, _dirs, files in os.walk(base):
    has_sch = any(f.lower().endswith(".sch") for f in files)
    has_cyc = any(f.lower().endswith(".cyc") for f in files)
    if has_sch and has_cyc:
        if os.path.isdir(os.path.join(root, "Restore")):
            channels.append(root)
    if len(channels) >= 20:
        break

print(f"테스트 {len(channels)} 채널\n")
print(f"{'T1행':<6} {'T2행':<6} {'공통':<5} {'일치':<6} {'Acc%':<7} Channel")

agg_total = 0
agg_match = 0
results = []
for ch in channels:
    se_path = find_save_end_csv(ch)
    cyc_path = find_cyc_file(ch)
    if se_path is None or cyc_path is None:
        continue
    m_se = load_from_save_end(se_path)
    m_cyc = load_from_cyc(cyc_path, initial_tc=1)
    if m_se is None or m_cyc is None:
        continue

    # SaveEndData 기준으로 initial_tc 맞추기 (첫 레코드 TC)
    first_idx_se = m_se.rec_indices[0] if m_se.rec_indices else None

    # RecIdx → TC 매핑
    se_map = dict(zip(m_se.rec_indices, m_se.tcs))
    cyc_map = dict(zip(m_cyc.rec_indices, m_cyc.tcs))

    common = set(se_map.keys()) & set(cyc_map.keys())

    # initial_tc 오프셋 자동 맞춤 (공통의 첫 RecIdx에서 TC 차이)
    if common:
        sample = min(common)
        tc_diff = se_map[sample] - cyc_map[sample]
    else:
        tc_diff = 0

    match = sum(1 for r in common if cyc_map[r] + tc_diff == se_map[r])
    total = len(common)
    acc = match / total * 100 if total else 0
    agg_total += total
    agg_match += match

    name = os.path.basename(os.path.dirname(ch)) + "/" + os.path.basename(ch)
    print(f"{len(m_se.tcs):<6} {len(m_cyc.tcs):<6} {total:<5} {match:<6} "
          f"{acc:<6.1f} {name}")

print()
print("=" * 70)
if agg_total:
    print(f"Tier 2 전체 정확도: {agg_match/agg_total*100:.2f}%  "
          f"({agg_match}/{agg_total})")
