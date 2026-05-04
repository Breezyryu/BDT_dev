"""Phase 0-2: 187 전수 .sch dump → step-level alignment 가설 검증.

가설:
  H1: +88 = V Limit upper (mV) — CHG step 위주
  H2: +92 = V Limit lower (mV) — DCHG step 위주, 또는 system default
  H3: +96 = I Limit upper (mA), +100 = I Limit lower (mA)
  H4: +336 = record_interval_s (ECT/GITT = 1s, 일반 = 60s)
  H5: +396 = chamber_temp_c (ECT only, ~23)
  H6: +36/+40 = End Capacity cutoff (CHG/DCHG, mAh) — ECT 시험에 등장
  H7: +84 = mode flag (1 = CHG/DCHG/REST, 0 = LOOP/GOTO/END)
  H8: Header +0/+4/+8 invariant (740721/131077/50)

산출:
  tools/phase0_2_field_distribution.csv  — per-file 모든 비0 field summary
  tools/phase0_2_validation.md           — 가설별 검증 결과
"""
from __future__ import annotations

import csv
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median, stdev

EXP_ROOT = Path(r"C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data")
HEADER_SIZE = 1920
BLOCK_SIZE = 652

SCH_TYPE_MAP = {
    0x0101: 'CHG_CCCV', 0x0102: 'DCHG_CCCV',
    0x0201: 'CHG_CC', 0x0202: 'DCHG_CC', 0x0209: 'CHG_CP',
    0xFF03: 'REST', 0xFF06: 'GOTO', 0xFF07: 'REST_SAFE',
    0xFF08: 'LOOP',
    0x0003: 'GITT_PAUSE', 0x0006: 'END',
    0x0007: 'GITT_END', 0x0008: 'GITT_START',
}

CHG_TYPES = {'CHG_CC', 'CHG_CCCV', 'CHG_CP'}
DCHG_TYPES = {'DCHG_CC', 'DCHG_CCCV'}
REST_TYPES = {'REST', 'REST_SAFE'}
CONTROL_TYPES = {'LOOP', 'GOTO', 'END'}

# Phase 0-1d 에서 검증할 offset
TARGET_OFFSETS = [12, 16, 20, 24, 28, 32, 36, 40, 84, 88, 92, 96, 100,
                  104, 336, 372, 388, 396, 500, 504]


def parse_sch(sch_path: Path) -> dict | None:
    try:
        with open(sch_path, 'rb') as f:
            data = f.read()
    except Exception:
        return None

    if len(data) < HEADER_SIZE + BLOCK_SIZE:
        return None

    magic = struct.unpack_from('<I', data, 0)[0]
    if magic != 740721:
        return None

    n_steps = (len(data) - HEADER_SIZE) // BLOCK_SIZE

    # Header invariants
    hdr = {
        'magic': magic,
        'h4': struct.unpack_from('<I', data, 4)[0],
        'h8': struct.unpack_from('<I', data, 8)[0],
        'h656': struct.unpack_from('<I', data, 656)[0],
    }
    # +664 schedule description (ASCII)
    desc_bytes = data[664:664 + 64]
    end = desc_bytes.find(b'\x00')
    if end > 0:
        desc_bytes = desc_bytes[:end]
    try:
        schedule_desc = desc_bytes.decode('ascii', errors='replace').strip()
    except Exception:
        schedule_desc = ''

    # Step blocks
    steps = []
    for i in range(n_steps):
        ofs = HEADER_SIZE + i * BLOCK_SIZE
        type_code = struct.unpack_from('<I', data, ofs + 8)[0]
        type_name = SCH_TYPE_MAP.get(type_code, f'UNK_0x{type_code:04X}')
        step = {'idx': i, 'type_name': type_name, 'type_code': type_code}
        for off in TARGET_OFFSETS:
            f_val = struct.unpack_from('<f', data, ofs + off)[0]
            u_val = struct.unpack_from('<I', data, ofs + off)[0]
            step[f'f{off}'] = f_val if u_val != 0 else 0.0
            step[f'u{off}'] = u_val
        steps.append(step)

    return {
        'header': hdr,
        'schedule_desc': schedule_desc,
        'n_steps': n_steps,
        'steps': steps,
    }


def find_test_category(sch_path: Path, root: Path) -> str:
    try:
        rel = sch_path.relative_to(root)
        return rel.parts[0] if rel.parts else 'UNKNOWN'
    except ValueError:
        return 'UNKNOWN'


def main():
    print(f"Scanning {EXP_ROOT}...", file=sys.stderr)
    sch_files = sorted(EXP_ROOT.rglob('*.sch'))
    print(f"Found {len(sch_files)} .sch files.", file=sys.stderr)

    # Per-file summary CSV
    rows = []

    # 가설 검증 통계
    h1_88_chg = []           # CHG step 의 +88 (mV)
    h1_88_other = defaultdict(list)  # other step types 의 +88
    h2_92_dchg = []          # DCHG step 의 +92 (mV)
    h2_92_other = defaultdict(list)
    h3_96 = []               # +96 (mA)
    h3_100 = []              # +100 (mA)
    h4_336_by_cat = defaultdict(list)  # +336 by test_category
    h4_336_by_keyword = defaultdict(list)
    h5_396_by_cat = defaultdict(list)  # +396 by test_category
    h6_36_40 = defaultdict(int)  # +36/+40 등장 횟수
    h7_84_by_type = defaultdict(Counter)
    h8_header_invariants = Counter()
    h8_header_h656 = Counter()

    type_global = Counter()
    failed_files = []

    for i, sch_path in enumerate(sch_files):
        if i % 100 == 0 and i > 0:
            print(f"  [{i}/{len(sch_files)}]", file=sys.stderr)

        test_cat = find_test_category(sch_path, EXP_ROOT)
        parsed = parse_sch(sch_path)
        if parsed is None:
            failed_files.append(str(sch_path.relative_to(EXP_ROOT)))
            continue

        hdr = parsed['header']
        desc = parsed['schedule_desc']
        h8_header_invariants[(hdr['magic'], hdr['h4'], hdr['h8'])] += 1
        h8_header_h656[hdr['h656']] += 1

        # Schedule description keyword
        desc_lower = desc.lower()
        kw = 'OTHER'
        if 'hysteresis' in desc_lower:
            kw = 'hysteresis'
        elif 'gitt' in desc_lower or 'ect' in desc_lower:
            kw = 'GITT/ECT'
        elif 'floating' in desc_lower or '120d' in desc_lower:
            kw = 'floating'
        elif 'rss' in desc_lower or 'dcir' in desc_lower:
            kw = 'DCIR/RSS'
        elif 'rpt' in desc_lower:
            kw = 'RPT'
        elif 'formation' in desc_lower:
            kw = 'formation'

        # Per file row
        first_chg_88 = None
        first_dchg_92 = None
        first_chg_96 = None
        first_chg_100 = None
        first_336 = None
        first_396 = None
        has_36 = False
        has_40 = False
        has_396_nonzero = False

        for step in parsed['steps']:
            t = step['type_name']
            type_global[t] += 1

            # H1: +88 = V upper (CHG)
            if t in CHG_TYPES and step['f88'] != 0:
                h1_88_chg.append(step['f88'])
                if first_chg_88 is None:
                    first_chg_88 = step['f88']
            elif t in (DCHG_TYPES | REST_TYPES | CONTROL_TYPES):
                if step['f88'] != 0:
                    h1_88_other[t].append(step['f88'])

            # H2: +92 = V lower
            if t in DCHG_TYPES and step['f92'] != 0:
                h2_92_dchg.append(step['f92'])
                if first_dchg_92 is None:
                    first_dchg_92 = step['f92']
            elif t in (CHG_TYPES | REST_TYPES | CONTROL_TYPES):
                if step['f92'] != 0:
                    h2_92_other[t].append(step['f92'])

            # H3: +96, +100
            if t in CHG_TYPES and step['f96'] != 0:
                h3_96.append(step['f96'])
                if first_chg_96 is None:
                    first_chg_96 = step['f96']
            if t in CHG_TYPES and step['f100'] != 0:
                h3_100.append(step['f100'])
                if first_chg_100 is None:
                    first_chg_100 = step['f100']

            # H4: +336
            if step['f336'] != 0:
                if first_336 is None:
                    first_336 = step['f336']
                h4_336_by_cat[test_cat].append(step['f336'])
                h4_336_by_keyword[kw].append(step['f336'])

            # H5: +396
            if step['f396'] != 0:
                if first_396 is None:
                    first_396 = step['f396']
                has_396_nonzero = True
                h5_396_by_cat[test_cat].append(step['f396'])

            # H6: +36, +40
            if step['f36'] != 0:
                h6_36_40['+36'] += 1
                has_36 = True
            if step['f40'] != 0:
                h6_36_40['+40'] += 1
                has_40 = True

            # H7: +84 by type
            h7_84_by_type[t][step['u84']] += 1

        rows.append({
            'idx': i + 1,
            'test_category': test_cat,
            'sch_path': str(sch_path.relative_to(EXP_ROOT)),
            'schedule_desc': desc,
            'keyword': kw,
            'n_steps': parsed['n_steps'],
            'h_magic': hdr['magic'],
            'h_h4': hdr['h4'],
            'h_h8': hdr['h8'],
            'h_h656': hdr['h656'],
            'first_chg_88_v_upper': first_chg_88,
            'first_dchg_92_v_lower': first_dchg_92,
            'first_chg_96_i_upper': first_chg_96,
            'first_chg_100_i_lower': first_chg_100,
            'first_336_rec_interval': first_336,
            'first_396_temp_c': first_396,
            'has_+36': has_36,
            'has_+40': has_40,
            'has_+396': has_396_nonzero,
        })

    # CSV summary
    csv_out = Path(__file__).parent / 'phase0_2_field_distribution.csv'
    with open(csv_out, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {csv_out}", file=sys.stderr)

    # 가설 검증 wiki md
    md_lines = []
    md_lines.append("# Phase 0-2: 187 전수 가설 검증")
    md_lines.append("")
    md_lines.append(f"- Scanned: **{len(sch_files)} .sch files**")
    md_lines.append(f"- Parsed: {len(rows)} (failed {len(failed_files)})")
    md_lines.append(f"- Total steps analyzed: {sum(type_global.values())}")
    md_lines.append("")

    # H8 Header invariants
    md_lines.append("## H8: Header invariants (+0/+4/+8)")
    md_lines.append("")
    md_lines.append("| (magic, h4, h8) | count |")
    md_lines.append("|---|---|")
    for k, v in h8_header_invariants.most_common(10):
        md_lines.append(f"| {k} | {v} |")
    md_lines.append("")
    if len(h8_header_invariants) == 1:
        md_lines.append("✅ **모든 파일에서 (740721, 131077, 50) 동일** — 완전 invariant.")
    else:
        md_lines.append(f"⚠️ {len(h8_header_invariants)} 종류 발견.")
    md_lines.append("")
    md_lines.append("### +656 (block-count meta) 분포")
    md_lines.append("")
    md_lines.append("| +656 value | count |")
    md_lines.append("|---|---|")
    for k, v in sorted(h8_header_h656.most_common(20)):
        md_lines.append(f"| {k} | {v} |")
    md_lines.append("")

    # Type 분포
    md_lines.append("## Step type 분포 (전체)")
    md_lines.append("")
    md_lines.append("| Type | count |")
    md_lines.append("|---|---|")
    for t, n in type_global.most_common():
        md_lines.append(f"| {t} | {n} |")
    md_lines.append("")

    # H1 +88
    md_lines.append("## H1: +88 = V Limit upper (mV)")
    md_lines.append("")
    if h1_88_chg:
        md_lines.append(f"- CHG step n={len(h1_88_chg)}, mean={mean(h1_88_chg):.1f}, "
                        f"median={median(h1_88_chg):.1f}, "
                        f"std={(stdev(h1_88_chg) if len(h1_88_chg) > 1 else 0):.1f}")
        md_lines.append(f"  - min={min(h1_88_chg):.1f}, max={max(h1_88_chg):.1f}")
        # 상위 빈도
        rounded = Counter(round(v) for v in h1_88_chg)
        md_lines.append(f"  - Top values (rounded mV): {rounded.most_common(8)}")
    md_lines.append(f"- Other step types 등장 빈도:")
    for t, vals in h1_88_other.items():
        if vals:
            md_lines.append(f"  - {t}: n={len(vals)}, mean={mean(vals):.1f}, "
                            f"top={Counter(round(v) for v in vals).most_common(3)}")
    md_lines.append("")
    if h1_88_chg:
        most_common_88 = Counter(round(v) for v in h1_88_chg).most_common(1)[0]
        md_lines.append(f"→ CHG +88 의 가장 흔한 값: **{most_common_88[0]} mV** ({most_common_88[1]} occurrences)")
        md_lines.append(f"→ 분포가 시험별로 의미 있게 변동하면 V upper 가 schedule 별 가변 → H1 ✅")
    md_lines.append("")

    # H2 +92
    md_lines.append("## H2: +92 = V Limit lower (mV)")
    md_lines.append("")
    if h2_92_dchg:
        md_lines.append(f"- DCHG step n={len(h2_92_dchg)}, mean={mean(h2_92_dchg):.1f}, "
                        f"median={median(h2_92_dchg):.1f}")
        md_lines.append(f"  - min={min(h2_92_dchg):.1f}, max={max(h2_92_dchg):.1f}")
        rounded = Counter(round(v) for v in h2_92_dchg)
        md_lines.append(f"  - Top values: {rounded.most_common(8)}")
    md_lines.append(f"- Other types 등장 빈도:")
    for t, vals in h2_92_other.items():
        if vals:
            md_lines.append(f"  - {t}: n={len(vals)}, top={Counter(round(v) for v in vals).most_common(3)}")
    md_lines.append("")

    # H3 +96 +100
    md_lines.append("## H3: +96/+100 = I Limit upper/lower (mA)")
    md_lines.append("")
    if h3_96:
        md_lines.append(f"- +96 (CHG): n={len(h3_96)}, mean={mean(h3_96):.1f}, "
                        f"min={min(h3_96):.1f}, max={max(h3_96):.1f}")
    if h3_100:
        md_lines.append(f"- +100 (CHG): n={len(h3_100)}, mean={mean(h3_100):.1f}, "
                        f"min={min(h3_100):.1f}, max={max(h3_100):.1f}")
    if h3_96 and h3_100:
        # 짝지어 비교 (같은 step 의 +96 - +100)
        md_lines.append(f"  - mean(+96 - +100) ≈ {mean(h3_96) - mean(h3_100):.1f} mA — IRef 의 ± buffer 추정")
    md_lines.append("")

    # H4 +336 — by category
    md_lines.append("## H4: +336 = record_interval_s (시험별 분포)")
    md_lines.append("")
    md_lines.append("| 시험종류 | n | top values (s) |")
    md_lines.append("|---|---|---|")
    for cat, vals in sorted(h4_336_by_cat.items()):
        cnt = Counter(round(v, 2) for v in vals)
        top = cnt.most_common(5)
        md_lines.append(f"| {cat} | {len(vals)} | {top} |")
    md_lines.append("")
    md_lines.append("### Keyword 별 분포")
    md_lines.append("")
    md_lines.append("| Keyword | n | top values |")
    md_lines.append("|---|---|---|")
    for kw, vals in sorted(h4_336_by_keyword.items()):
        cnt = Counter(round(v, 2) for v in vals)
        md_lines.append(f"| {kw} | {len(vals)} | {cnt.most_common(5)} |")
    md_lines.append("")

    # H5 +396
    md_lines.append("## H5: +396 = chamber_temp_c (시험별 분포)")
    md_lines.append("")
    md_lines.append("| 시험종류 | n | top values |")
    md_lines.append("|---|---|---|")
    for cat, vals in sorted(h5_396_by_cat.items()):
        cnt = Counter(round(v, 1) for v in vals)
        md_lines.append(f"| {cat} | {len(vals)} | {cnt.most_common(8)} |")
    md_lines.append("")
    md_lines.append(f"### File-level: +396 비0 보유 파일 = {sum(1 for r in rows if r['has_+396'])}")
    md_lines.append("")

    # H6 +36 +40
    md_lines.append("## H6: +36/+40 = End Capacity cutoff")
    md_lines.append("")
    md_lines.append(f"- +36 occurrence count: {h6_36_40.get('+36', 0)} step")
    md_lines.append(f"- +40 occurrence count: {h6_36_40.get('+40', 0)} step")
    md_lines.append(f"- 파일 level: has_+36 = {sum(1 for r in rows if r['has_+36'])}, has_+40 = {sum(1 for r in rows if r['has_+40'])}")
    md_lines.append("")

    # H7 +84 by type
    md_lines.append("## H7: +84 = mode flag (type 별 값 분포)")
    md_lines.append("")
    md_lines.append("| Type | +84 분포 (top 5) |")
    md_lines.append("|---|---|")
    for t, c in sorted(h7_84_by_type.items()):
        md_lines.append(f"| {t} | {c.most_common(5)} |")
    md_lines.append("")

    # Failed
    if failed_files:
        md_lines.append("## ⚠️ Parse 실패 파일")
        md_lines.append("")
        for p in failed_files[:30]:
            md_lines.append(f"- `{p}`")
        if len(failed_files) > 30:
            md_lines.append(f"- (+{len(failed_files) - 30} more)")
        md_lines.append("")

    out_md = Path(__file__).parent / 'phase0_2_validation.md'
    with open(out_md, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    print(f"Wrote {out_md}", file=sys.stderr)
    print('Done.', file=sys.stderr)


if __name__ == '__main__':
    main()
