"""PNE .sch 파일 전수 파싱 — Loop 그룹 분해 + TC 분류 스크립트"""
import struct
import os
import re
from pathlib import Path
from collections import defaultdict

HEADER_SIZE = 1920
STEP_SIZE = 652
MAGIC = 740721

TYPE_CODES = {
    0x0101: 'CHG_CC',
    0x0102: 'DCHG_CCCV',
    0x0201: 'CHG_CCCV',
    0x0202: 'DCHG_CC',
    0x0209: 'CHG_CP',
    0xFF03: 'REST',
    0xFF06: 'GOTO',
    0xFF07: 'REST_SAFE',
    0xFF08: 'LOOP',
    0x0003: 'GITT_PAUSE',
    0x0006: 'END',  # schedule terminator (LOOP 뒤 마지막 스텝, 모든 필드 0)
    0x0007: 'GITT_END',
    0x0008: 'GITT_START',
}

EC_TYPE_MAP = {
    0: 'NONE',
    256: 'CUR',       # 0x0100
    512: 'VOL',       # 0x0200
    1024: 'CAP',      # 0x0400
    2048: 'DOD',      # 0x0800
    4096: 'WATT',     # 0x1000
    8192: 'ENERGY',   # 0x2000
    16384: 'SOC',     # 0x4000
    18432: 'SOC_CHG', # 0x4800 (SOC variant for charge)
}


def parse_sch(filepath):
    """Parse a single .sch file and return list of steps."""
    with open(filepath, 'rb') as f:
        data = f.read()

    if len(data) < HEADER_SIZE:
        return None

    # Check magic
    magic = struct.unpack_from('<I', data, 0)[0]
    if magic != MAGIC:
        return None

    steps = []
    offset = HEADER_SIZE
    while offset + STEP_SIZE <= len(data):
        step_num = struct.unpack_from('<I', data, offset + 0)[0]
        type_code = struct.unpack_from('<I', data, offset + 8)[0]
        v_chg = struct.unpack_from('<f', data, offset + 12)[0]
        v_dchg = struct.unpack_from('<f', data, offset + 16)[0]
        current = struct.unpack_from('<f', data, offset + 20)[0]
        time_limit = struct.unpack_from('<f', data, offset + 24)[0]
        cv_voltage = struct.unpack_from('<f', data, offset + 28)[0]
        cv_cutoff = struct.unpack_from('<f', data, offset + 32)[0]
        loop_count = struct.unpack_from('<I', data, offset + 56)[0]
        goto_target = loop_count  # same field
        cap_limit = struct.unpack_from('<f', data, offset + 104)[0]
        ec_value = struct.unpack_from('<f', data, offset + 372)[0]
        ec_type = struct.unpack_from('<I', data, offset + 500)[0]
        ec_enabled = struct.unpack_from('<I', data, offset + 504)[0]

        type_name = TYPE_CODES.get(type_code, f'UNK_0x{type_code:04X}')

        steps.append({
            'step_num': step_num,
            'type_code': type_code,
            'type': type_name,
            'v_chg': v_chg,
            'v_dchg': v_dchg,
            'current': current,
            'time_limit': time_limit,
            'cv_voltage': cv_voltage,
            'cv_cutoff': cv_cutoff,
            'loop_count': loop_count,
            'goto_target': goto_target,
            'cap_limit': cap_limit,
            'ec_value': ec_value,
            'ec_type': ec_type,
            'ec_enabled': ec_enabled,
        })
        offset += STEP_SIZE

    return steps


def split_into_loop_groups(steps):
    """Split steps into loop groups based on LOOP steps."""
    groups = []
    body = []
    for s in steps:
        if s['type'] == 'LOOP':
            groups.append({
                'body': body,
                'loop_count': s['loop_count'],
                'loop_step': s,
            })
            body = []
        elif s['type'] == 'REST_SAFE':
            # REST_SAFE is a group boundary marker, not included in body
            if body:
                # If there are accumulated steps without a LOOP, flush them
                pass
            # Just skip it, don't add to body
            continue
        elif s['type'] == 'GOTO':
            # GOTO is typically at the end, skip
            continue
        elif s['type'] == 'END':
            # Schedule END marker (0x0006) - skip
            continue
        elif s['type'] in ('GITT_PAUSE', 'GITT_END', 'GITT_START'):
            # GITT markers - include in body
            body.append(s)
        else:
            body.append(s)

    # If there are leftover body steps without a LOOP, create a trailing group
    if body:
        groups.append({
            'body': body,
            'loop_count': 1,
            'loop_step': None,
        })

    return groups


def classify_loop_group(body_steps, loop_count, position, total_loops):
    """Classify a loop group based on its body steps."""
    N = loop_count
    n_steps = len(body_steps)
    if n_steps == 0:
        return 'EMPTY'

    types = [s['type'] for s in body_steps]
    type_set = set(types)
    chg_count = sum(1 for t in types if t.startswith('CHG'))
    dchg_count = sum(1 for t in types if t.startswith('DCHG'))
    has_chg_cp = 'CHG_CP' in type_set
    ec_steps = [s for s in body_steps if s.get('ec_enabled', 0) > 0]
    n_ec = len(ec_steps)
    has_ec = n_ec > 0
    ec_on_dchg = [s for s in ec_steps if s['type'].startswith('DCHG')]
    ec_on_chg = [s for s in ec_steps if s['type'].startswith('CHG')]

    # 1. INIT
    if position == 0 and N == 1:
        if type_set <= {'DCHG_CC', 'DCHG_CCCV', 'REST', 'REST_SAFE'} and any(t.startswith('DCHG') for t in types):
            return 'INIT'

    # 2. GITT_PULSE
    if N >= 10 and n_steps <= 3 and len(types) > 0 and types[0] == 'REST':
        rest_t = body_steps[0].get('time_limit', 0)
        if rest_t >= 600 and any(t in ('CHG_CCCV', 'CHG_CC', 'DCHG_CC') for t in types[1:]):
            return 'GITT_PULSE'

    # 3. ACCEL
    if N >= 20 and chg_count >= 2 and dchg_count >= 1:
        return 'ACCEL'

    # 4. HYSTERESIS_DCHG
    if N == 1 and ec_on_dchg and any(s.get('ec_type') == 2048 for s in ec_on_dchg):
        return 'HYSTERESIS_DCHG'

    # 5. HYSTERESIS_CHG
    if N == 1 and ec_on_chg and any(s.get('ec_type') == 18432 for s in ec_on_chg):
        return 'HYSTERESIS_CHG'

    # 6. SOC_DCIR
    if N >= 5 and n_ec >= 4 and n_steps >= 8:
        return 'SOC_DCIR'

    # 7. RSS_DCIR
    if N == 1 and has_ec and dchg_count >= 4 and n_steps >= 10:
        return 'RSS_DCIR'

    # 8. RATE_TEST
    if N > 1 and has_ec and chg_count >= 2 and dchg_count >= 2:
        return 'RATE_TEST'

    # 9. KVALUE
    if has_chg_cp:
        return 'KVALUE'
    if n_steps == 1 and types[0] == 'REST' and body_steps[0].get('time_limit', 0) >= 7200:
        return 'KVALUE'

    # 10. FORMATION
    if 2 <= N <= 10 and chg_count >= 1 and dchg_count >= 1 and position <= 2:
        return 'FORMATION'

    # 11. CHARGE_SET
    if N == 1 and chg_count >= 1 and dchg_count == 0:
        if type_set <= {'CHG_CC', 'CHG_CCCV', 'CHG_CP', 'REST', 'REST_SAFE'}:
            return 'CHARGE_SET'

    # 12. TERMINATION
    if position == total_loops - 1 and N == 1 and dchg_count >= 1 and chg_count == 0:
        return 'TERMINATION'

    # 13. RPT
    if N == 1 and chg_count >= 1 and dchg_count >= 1 and n_steps <= 8:
        return 'RPT'

    return 'UNKNOWN'


def format_ec_info(step):
    """Format EC condition info for a step."""
    if step.get('ec_enabled', 0) <= 0:
        return ''
    ec_type = step.get('ec_type', 0)
    ec_val = step.get('ec_value', 0)
    name = EC_TYPE_MAP.get(ec_type, f'TYPE_{ec_type}')
    if ec_type == 2048:  # DOD
        return f'[EC: DOD {ec_val:.1f}%]'
    elif ec_type in (16384, 18432):  # SOC / SOC_CHG
        return f'[EC: SOC {ec_val:.1f}%]'
    elif ec_type == 1024:  # CAP
        return f'[EC: CAP {ec_val:.1f}mAh]'
    elif ec_type == 512:  # VOL
        return f'[EC: VOL {ec_val:.1f}mV]'
    else:
        return f'[EC: {name} {ec_val:.1f}]'


def format_step_summary(step):
    """Format a single step for display."""
    t = step['type']
    parts = [t]
    detail_parts = []

    if t in ('CHG_CC', 'DCHG_CC'):
        detail_parts.append(f'I={step["current"]:.0f}mA')
        if t == 'CHG_CC' and step['v_chg'] > 0:
            detail_parts.append(f'V={step["v_chg"]:.0f}mV')
        if t == 'DCHG_CC' and step['v_dchg'] > 0:
            detail_parts.append(f'V={step["v_dchg"]:.0f}mV')
        if step['time_limit'] > 0:
            detail_parts.append(f't={step["time_limit"]:.0f}s')
    elif t in ('CHG_CCCV', 'DCHG_CCCV'):
        detail_parts.append(f'I={step["current"]:.0f}mA')
        if step['cv_voltage'] > 0:
            detail_parts.append(f'CV={step["cv_voltage"]:.0f}mV')
        if step['cv_cutoff'] > 0:
            detail_parts.append(f'cut={step["cv_cutoff"]:.0f}mA')
        if t == 'DCHG_CCCV' and step['v_dchg'] > 0:
            detail_parts.append(f'Vd={step["v_dchg"]:.0f}mV')
    elif t == 'CHG_CP':
        detail_parts.append(f'P={step["current"]:.0f}mW')
        if step['v_chg'] > 0:
            detail_parts.append(f'V={step["v_chg"]:.0f}mV')
        if step['time_limit'] > 0:
            detail_parts.append(f't={step["time_limit"]:.0f}s')
    elif t == 'REST':
        if step['time_limit'] > 0:
            t_s = step['time_limit']
            if t_s >= 3600:
                detail_parts.append(f'{t_s/3600:.1f}h')
            elif t_s >= 60:
                detail_parts.append(f'{t_s/60:.0f}m')
            else:
                detail_parts.append(f'{t_s:.0f}s')

    ec = format_ec_info(step)
    if ec:
        detail_parts.append(ec)

    if detail_parts:
        return f'{t}({",".join(detail_parts)})'
    return t


def format_group_body(body_steps):
    """Format the body of a loop group as a compact step chain."""
    if not body_steps:
        return '(empty)'

    # Group consecutive same-type steps with different currents
    formatted = []
    i = 0
    while i < len(body_steps):
        s = body_steps[i]
        # Check if this is a multi-current group (e.g., 4-stage CC charge)
        if s['type'] in ('CHG_CC', 'CHG_CCCV', 'DCHG_CC', 'DCHG_CCCV'):
            same_type = [s]
            j = i + 1
            while j < len(body_steps) and body_steps[j]['type'] == s['type']:
                same_type.append(body_steps[j])
                j += 1
            if len(same_type) > 1:
                currents = [f'{st["current"]:.0f}' for st in same_type]
                t = s['type']
                ec_parts = []
                for st in same_type:
                    ec = format_ec_info(st)
                    if ec:
                        ec_parts.append(ec)

                detail = f'{len(same_type)}단:{" → ".join(currents)}mA'
                if s['type'] in ('CHG_CCCV',) and same_type[0]['cv_voltage'] > 0:
                    detail += f',CV={same_type[0]["cv_voltage"]:.0f}mV'
                if ec_parts:
                    detail += ' ' + ' '.join(set(ec_parts))
                formatted.append(f'{t}({detail})')
                i = j
                continue

        formatted.append(format_step_summary(s))
        i += 1

    return ' → '.join(formatted)


def get_variant_suffix(filename):
    """Extract _000, _001 etc. suffix from filename."""
    m = re.search(r'_(\d{3})\.sch$', filename)
    if m:
        return m.group(1)
    return None


def main():
    base_dir = Path(r'c:\Users\Ryu\battery\python\BDT_dev\DataTool_dev_code\data\exp_data')

    # Collect all .sch files grouped by experiment folder
    exp_folders = defaultdict(lambda: defaultdict(list))
    # exp_folders[exp_name][channel_path] = [sch_files...]

    for sch_path in sorted(base_dir.rglob('*.sch')):
        # Get experiment folder (first level under exp_data)
        rel = sch_path.relative_to(base_dir)
        parts = rel.parts
        if len(parts) < 2:
            continue
        exp_name = parts[0]
        channel_dir = parts[1] if len(parts) >= 2 else ''
        exp_folders[exp_name][str(sch_path)] = sch_path

    # Reorganize: group by experiment folder, separate originals from variants
    # For each exp folder, find unique schedules
    all_results = {}

    for exp_name in sorted(exp_folders.keys()):
        sch_files = sorted(exp_folders[exp_name].values(), key=lambda p: str(p))

        # Separate originals from variants
        originals = []
        variants = {}  # suffix -> [paths]

        for sp in sch_files:
            suffix = get_variant_suffix(sp.name)
            if suffix is not None:
                variants.setdefault(suffix, []).append(sp)
            else:
                originals.append(sp)

        if not originals and not variants:
            continue

        # Parse the first original as representative
        rep_path = originals[0] if originals else list(variants.values())[0][0]
        steps = parse_sch(rep_path)
        if steps is None:
            continue

        n_channels = len(originals) if originals else len(list(variants.values())[0])

        groups = split_into_loop_groups(steps)
        total_loops = len(groups)

        # Classify and compute TC numbers
        tc_info = []
        tc_current = 1
        for idx, g in enumerate(groups):
            cat = classify_loop_group(g['body'], g['loop_count'], idx, total_loops)
            n = g['loop_count']
            tc_start = tc_current
            tc_end = tc_current + n - 1
            body_desc = format_group_body(g['body'])
            tc_info.append({
                'idx': idx + 1,
                'category': cat,
                'tc_start': tc_start,
                'tc_end': tc_end,
                'n': n,
                'body_desc': body_desc,
            })
            tc_current += n

        total_tc = tc_current - 1

        # Now parse variants and find differences
        variant_diffs = {}
        for suffix in sorted(variants.keys()):
            var_path = variants[suffix][0]
            var_steps = parse_sch(var_path)
            if var_steps is None:
                continue
            var_groups = split_into_loop_groups(var_steps)
            diffs = []
            # Compare loop counts
            for vi, vg in enumerate(var_groups):
                if vi < len(groups):
                    orig_n = groups[vi]['loop_count']
                    var_n = vg['loop_count']
                    if orig_n != var_n:
                        orig_cat = tc_info[vi]['category'] if vi < len(tc_info) else '?'
                        diffs.append((vi + 1, orig_cat, orig_n, var_n))
                else:
                    # Extra group in variant
                    var_cat = classify_loop_group(vg['body'], vg['loop_count'], vi, len(var_groups))
                    diffs.append((vi + 1, var_cat, 0, vg['loop_count']))

            if len(var_groups) < len(groups):
                for vi in range(len(var_groups), len(groups)):
                    orig_cat = tc_info[vi]['category'] if vi < len(tc_info) else '?'
                    diffs.append((vi + 1, orig_cat, groups[vi]['loop_count'], 0))

            if diffs:
                variant_diffs[suffix] = diffs

        all_results[exp_name] = {
            'n_channels': n_channels,
            'total_tc': total_tc,
            'tc_info': tc_info,
            'variant_diffs': variant_diffs,
        }

    # Output
    for exp_name, data in all_results.items():
        print(f"\n=== [{exp_name}] ({data['n_channels']}채널, 총 {data['total_tc']} TC) ===")
        for g in data['tc_info']:
            tc_range = ''
            if g['n'] == 1:
                tc_range = f"TC {g['tc_start']:>4}"
            else:
                tc_range = f"TC {g['tc_start']:>4}-{g['tc_end']:<4}({g['n']})"

            cat_str = f"{g['category']:<18}"
            print(f" #{g['idx']:<3} {cat_str} {tc_range}  {g['body_desc']}")

        for suffix, diffs in data.get('variant_diffs', {}).items():
            for (gidx, cat, orig_n, var_n) in diffs:
                if var_n == 0:
                    print(f"  * _{suffix} 변형: #{gidx} {cat} 삭제됨 (원본 N={orig_n})")
                elif orig_n == 0:
                    print(f"  * _{suffix} 변형: #{gidx} {cat} 추가됨 (N={var_n})")
                else:
                    print(f"  * _{suffix} 변형: #{gidx} {cat} N={orig_n}→{var_n} (잔여 사이클)")


if __name__ == '__main__':
    import sys
    import io
    # Force UTF-8 output
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()
