"""사용자 보고 3건 분류 진단 — GITT 방향 / 240919 cycle6 중복 / 260109 보관 오분류."""
from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "DataTool_dev_code"))
import DataTool_optRCD_proto_ as bdt  # noqa


CASES = [
    ("CASE 1: GITT 방향 미구분",
     r"C:/Users/Ryu/battery/python/BDT_dev/raw/raw_exp/exp_data/성능/240821 선행랩 류성택 Gen4pGr mini-ATL-WD-Proto-422mAh-20C-450V-GITT-15도"),
    ("CASE 2: 240919 SOC별DCIR cycle6 중복",
     r"C:/Users/Ryu/battery/python/BDT_dev/raw/raw_exp/exp_data/성능/240919 선행랩 류성택 Gen4pGr mini-ATL-WD-Proto-422mAh-20C-450V-SOC별DCIR-15도"),
    ("CASE 3: 260109 보관 → hysteresis 오분류",
     r"C:/Users/Ryu/battery/python/BDT_dev/raw/raw_exp/exp_data/성능/260109_260112_05_이근준_5000mAh_Gen5P Si5 ATL T2 3M 보관 용량 측정 4cycle SOC 30 setting ch7 to 12"),
]


def show(meta, label):
    if meta is None:
        print(f"  meta 없음 — {label}")
        return
    print(f"  is_pne: {meta.is_pne}, max_tc: {meta.max_tc}, "
          f"min_capacity: {meta.min_capacity}")
    if meta.classified:
        print(f"  classified: {len(meta.classified)} entries")
        for cl in meta.classified[:30]:
            cyc = cl.get('cycle')
            cat = cl.get('category')
            extra = []
            for k in ('action', 'n_charge', 'n_discharge', 'has_es78',
                     'raw_range', 'raw_cycles'):
                if k in cl:
                    extra.append(f"{k}={cl[k]}")
            print(f"    [{cyc}] {cat:<20} {' '.join(extra)}")
        if len(meta.classified) > 30:
            print(f"    ... {len(meta.classified) - 30} more")


def show_blocks(meta, label):
    blocks = bdt._build_timeline_blocks_tc_by_loop(
        meta.classified, cycle_map=meta.cycle_map)
    print(f"  blocks: {len(blocks)}")
    for b in blocks:
        print(f"    {b['start']:>4}-{b['end']:>4}  "
              f"{b['pattern']:<20}  count={b['count']}")


for label, ds_path in CASES:
    print(f"\n{'='*70}\n{label}\n  {ds_path}\n{'='*70}")
    p = Path(ds_path)
    if not p.is_dir():
        print(f"  경로 없음")
        continue
    chs = [c for c in sorted(p.iterdir())
           if c.is_dir() and bdt._is_channel_folder(c.name)]
    if not chs:
        print(f"  채널 없음")
        continue
    ch = chs[0]
    print(f"  대표 채널: {ch.name}")
    try:
        meta = bdt._build_channel_meta(str(ch))
    except Exception as e:
        print(f"  meta 빌드 예외: {e}")
        continue
    show(meta, label)
    print(f"\n  --- 타임라인 블록 ---")
    show_blocks(meta, label)
