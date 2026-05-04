"""Step-level alignment: CSV (CTSEditor) ↔ .sch binary.

각 step 의 CSV 컬럼 (VRef/IRef/End/V Limit/I Limit/V1-3 trips/I1-3 trips)
과 .sch step block 의 모든 4-byte aligned float/uint32 field 를
1:1 매핑하여 unknown byte (+108~+335 등) 의 의미 추정.
"""
from __future__ import annotations

import re
import struct
import sys
from pathlib import Path

CSV_DIR = Path(r"C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\pattern")
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

SAMPLES = [
    {
        'label': 'Floating_2688mAh_120D',
        'csv': CSV_DIR / 'Ref_4.55V Floating 2688mAh +120D.csv',
        'sch': EXP_ROOT / r'성능\260112_260312_03_나무늬_2688mAh_Gen5+B SDI MP2 2.0C EPF HT Floating + 120D\M01Ch057[057]\260112_260312_03_나무늬_2688mAh_Gen5+B SDI MP2 2.0C EPF HT Floating + 120D.sch',
    },
    {
        'label': '4.53V_5000mAh_4cycle_SOC30',
        'csv': CSV_DIR / 'Ref_4.53V_Si_5000mAh 0.2C recovery capacity 4cycle SOC30 setting.csv',
        'sch': EXP_ROOT / r'성능\260109_260112_05_이근준_5000mAh_Gen5P Si5 ATL T2 3M 보관 용량 측정 4cycle SOC 30 setting ch7 to 12\M01Ch007[007]\260109_260112_05_이근준_5000mAh_Gen5P Si5 ATL T2 3M 보관 용량 측정 4cycle SOC 30 setting ch7 to 12.sch',
    },
    {
        'label': 'ECT_5882mAh_GITT',
        'csv': CSV_DIR / 'Ref_5882mAh_ECT 패턴11 GITT.csv',
        'sch': EXP_ROOT / r'성능\260316_270318_00_이성일_5882mAh_M47 ATL ECT GITT\M01Ch005[005]\260316_270318_00_이성일_5882mAh_M47 ATL ECT GITT.sch',
    },
]


def read_csv_steps(csv_path: Path) -> list[dict]:
    """CSV 의 [Step] 섹션을 dict list 로."""
    in_step = False
    header = None
    steps = []
    with open(csv_path, encoding='cp949', errors='replace') as f:
        for line in f:
            line = line.rstrip('\r\n')
            if line.startswith('[Step]'):
                in_step = True
                continue
            if line.startswith('[') and in_step:
                break
            if in_step:
                if header is None:
                    header = [c.strip() for c in line.split(',')]
                else:
                    if line.strip():
                        cols = line.split(',')
                        row = {h: (cols[i].strip() if i < len(cols) else '')
                               for i, h in enumerate(header)}
                        if row.get('StepNo'):
                            steps.append(row)
    return steps


def dump_sch_step(data: bytes, step_idx: int) -> dict:
    """Step block 의 모든 비0 4-byte field dump."""
    ofs = HEADER_SIZE + step_idx * BLOCK_SIZE
    blk = data[ofs:ofs + BLOCK_SIZE]
    type_code = struct.unpack_from('<I', blk, 8)[0]
    type_name = SCH_TYPE_MAP.get(type_code, f'UNK_0x{type_code:04X}')

    fields = []
    for i in range(0, BLOCK_SIZE, 4):
        u = struct.unpack_from('<I', blk, i)[0]
        if u == 0:
            continue
        f = struct.unpack_from('<f', blk, i)[0]
        fields.append({'ofs': i, 'uint32': u, 'float': f})

    return {
        'step_idx': step_idx,
        'step_num': struct.unpack_from('<I', blk, 0)[0],
        'type_code': type_code,
        'type_name': type_name,
        'non_zero_fields': fields,
    }


def parse_csv_step_value(s: str, kind: str) -> dict:
    """CSV step 컬럼의 의미 추출.

    kind: 'vref', 'iref', 'end', 'vlimit', 'ilimit', 'climit', 'trip'
    """
    s = (s or '').strip()
    if not s:
        return {}

    if kind == 'vref' or kind == 'iref':
        try:
            return {'value': float(s)}
        except ValueError:
            return {'raw': s}

    if kind == 'end':
        # "V < 3.0", "V > 4.14", "I < 0.048", "t > 00:10:00.0", or compound
        out = {'raw': s}
        m_v = re.search(r'V\s*([<>=]+)\s*([\d.]+)', s)
        if m_v:
            out['v_op'] = m_v.group(1)
            out['v_value'] = float(m_v.group(2))
        m_i = re.search(r'I\s*([<>=]+)\s*([\d.]+)', s)
        if m_i:
            out['i_op'] = m_i.group(1)
            out['i_value'] = float(m_i.group(2))
        m_t = re.search(r't\s*([<>=]+)\s*([\d:.]+)', s)
        if m_t:
            out['t_op'] = m_t.group(1)
            t_str = m_t.group(2)
            # HH:MM:SS.s → seconds
            try:
                parts = t_str.split(':')
                if len(parts) == 3:
                    h, m, sec = parts
                    out['t_seconds'] = int(h) * 3600 + int(m) * 60 + float(sec)
            except Exception:
                pass
        return out

    if kind == 'vlimit':
        # "2.45≤V" or "V≤4.59" or "2.45≤V≤4.59"
        out = {'raw': s}
        m = re.match(r'^([\d.]+)\s*[≤<]+\s*V\s*[≤<]*\s*([\d.]*)\s*$', s)
        if m:
            out['v_lo'] = float(m.group(1)) if m.group(1) else None
            out['v_hi'] = float(m.group(2)) if m.group(2) else None
        else:
            m2 = re.match(r'^V\s*[≤<]+\s*([\d.]+)\s*$', s)
            if m2:
                out['v_hi'] = float(m2.group(1))
        return out

    if kind == 'ilimit':
        # "0.416≤I≤3.516"
        out = {'raw': s}
        m = re.match(r'^([\d.]+)\s*[≤<]+\s*I\s*[≤<]+\s*([\d.]+)\s*$', s)
        if m:
            out['i_lo'] = float(m.group(1))
            out['i_hi'] = float(m.group(2))
        return out

    return {'raw': s}


def find_match(target: float, fields: list[dict], tol: float = 0.5) -> list[dict]:
    """비0 fields 중 target 값과 가까운 것 찾기 (float 또는 mV/mA 환산)."""
    matches = []
    for fld in fields:
        f_val = fld['float']
        u_val = fld['uint32']
        for variant_name, variant_val in [
            ('float', f_val),
            ('float_x1000', f_val * 1000),  # V → mV
            ('float_div1000', f_val / 1000),  # mV → V
            ('uint32', u_val),
            ('uint32_div1000', u_val / 1000),
        ]:
            try:
                if variant_val == 0:
                    continue
                if abs(variant_val - target) <= tol:
                    matches.append({
                        'ofs': fld['ofs'],
                        'variant': variant_name,
                        'sch_value': variant_val,
                        'csv_target': target,
                        'diff': abs(variant_val - target),
                    })
            except Exception:
                pass
    return matches


def align_step(csv_step: dict, sch_step: dict) -> list[str]:
    """1 step 의 CSV ↔ .sch 매칭 라인 생성."""
    out = []
    out.append(f"  CSV step {csv_step.get('StepNo')}: Type={csv_step.get('Type')}, Mode={csv_step.get('Mode')}")
    out.append(f"  .sch step {sch_step['step_num']}: type_name={sch_step['type_name']} (0x{sch_step['type_code']:04X})")

    # Parse CSV values
    vref = parse_csv_step_value(csv_step.get('VRef(V)', ''), 'vref')
    iref = parse_csv_step_value(csv_step.get('IRef(A)', ''), 'iref')
    end = parse_csv_step_value(csv_step.get('End', ''), 'end')
    vlimit = parse_csv_step_value(csv_step.get('V Limit', ''), 'vlimit')
    ilimit = parse_csv_step_value(csv_step.get('I Limit', ''), 'ilimit')

    out.append(f"    CSV values:")
    if vref.get('value') is not None:
        out.append(f"      VRef = {vref['value']} V")
    if iref.get('value') is not None:
        out.append(f"      IRef = {iref['value']} A = {iref['value']*1000:.1f} mA")
    if end.get('raw'):
        e_summary = end.get('raw')
        if 'v_value' in end:
            e_summary += f"  -> V {end['v_op']} {end['v_value']*1000:.0f} mV"
        if 'i_value' in end:
            e_summary += f"  -> I {end['i_op']} {end['i_value']*1000:.0f} mA"
        if 't_seconds' in end:
            e_summary += f"  -> t {end['t_op']} {end['t_seconds']:.0f} s"
        out.append(f"      End = {e_summary}")
    if vlimit.get('raw'):
        out.append(f"      V Limit = {vlimit.get('raw')}  -> lo={vlimit.get('v_lo')} hi={vlimit.get('v_hi')}")
    if ilimit.get('raw'):
        out.append(f"      I Limit = {ilimit.get('raw')}  -> lo={ilimit.get('i_lo')} hi={ilimit.get('i_hi')}")

    out.append(f"    .sch non-zero fields:")
    fields = sch_step['non_zero_fields']
    for fld in fields:
        ofs = fld['ofs']
        u = fld['uint32']
        f = fld['float']
        f_disp = f"{f:.4g}" if abs(f) < 1e9 and abs(f) > 1e-6 else "—"
        out.append(f"      +{ofs:3d}  uint32={u:>12d}  float={f_disp:>14s}")

    # 자동 매칭
    out.append(f"    Auto-match:")
    targets = []
    if vref.get('value') is not None:
        v_mv = vref['value'] * 1000
        targets.append(('VRef (V→mV)', v_mv))
    if iref.get('value') is not None:
        i_ma = iref['value'] * 1000
        targets.append(('IRef (A→mA)', i_ma))
    if end.get('v_value') is not None:
        targets.append(('End V (V→mV)', end['v_value'] * 1000))
    if end.get('i_value') is not None:
        targets.append(('End I (A→mA)', end['i_value'] * 1000))
    if end.get('t_seconds') is not None:
        targets.append(('End t (s)', end['t_seconds']))
    if vlimit.get('v_lo') is not None:
        targets.append(('V Limit lo (V→mV)', vlimit['v_lo'] * 1000))
    if vlimit.get('v_hi') is not None:
        targets.append(('V Limit hi (V→mV)', vlimit['v_hi'] * 1000))
    if ilimit.get('i_lo') is not None:
        targets.append(('I Limit lo (A→mA)', ilimit['i_lo'] * 1000))
    if ilimit.get('i_hi') is not None:
        targets.append(('I Limit hi (A→mA)', ilimit['i_hi'] * 1000))

    for label, target in targets:
        matches = find_match(target, fields, tol=2.0)
        if matches:
            best = min(matches, key=lambda m: m['diff'])
            out.append(f"      {label} = {target:.1f} -> +{best['ofs']} ({best['variant']}={best['sch_value']:.2f}, diff={best['diff']:.2f})")
        else:
            out.append(f"      {label} = {target:.1f} -> NO MATCH")
    out.append('')
    return out


def main():
    out_lines = []
    out_lines.append("# Step-level CSV ↔ .sch alignment (Phase 0-1d)")
    out_lines.append("")

    for sample in SAMPLES:
        label = sample['label']
        csv_path = sample['csv']
        sch_path = sample['sch']

        out_lines.append(f"## {label}")
        out_lines.append("")
        out_lines.append(f"- CSV: `{csv_path.name}`")
        out_lines.append(f"- .sch: `{sch_path.name}`")
        out_lines.append("")

        if not csv_path.exists() or not sch_path.exists():
            out_lines.append("⚠️ Skip — file missing.")
            out_lines.append("")
            continue

        csv_steps_raw = read_csv_steps(csv_path)
        # CSV 에는 'Cycle' (가상 marker, .sch 미저장) 과 '완료' (END marker) 가 있음 → skip
        csv_steps = [s for s in csv_steps_raw
                     if s.get('Type') not in ('Cycle', '완료')]
        with open(sch_path, 'rb') as f:
            data = f.read()
        n_sch = (len(data) - HEADER_SIZE) // BLOCK_SIZE

        out_lines.append(f"- CSV steps (raw): {len(csv_steps_raw)}, "
                         f"after skip Cycle/완료: {len(csv_steps)}, "
                         f".sch steps: {n_sch}")
        out_lines.append("")
        out_lines.append("```")

        for i in range(min(len(csv_steps), n_sch)):
            csv_s = csv_steps[i]
            sch_s = dump_sch_step(data, i)
            out_lines.extend(align_step(csv_s, sch_s))

        if len(csv_steps) != n_sch:
            out_lines.append(f"  *** Mismatch: CSV (post-skip) {len(csv_steps)} "
                             f"vs .sch {n_sch}")

        out_lines.append("```")
        out_lines.append("")
        out_lines.append("---")
        out_lines.append("")

    out_path = Path(__file__).parent / 'sch_csv_step_align.md'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out_lines))
    print(f"Wrote {out_path}", file=sys.stderr)


if __name__ == '__main__':
    main()
