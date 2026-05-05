"""Phase 0-5 spec: 187 폴더 / 368 .sch 전수 사이클별 정의.

`260504_audit_phase0_5_classifier_input_spec.md` 의 분류기 v2 spec 적용.

핵심:
  1. Parser 보강 — Phase 0-2/0-3/0-4 confirmed 9 신규 field
     (v_safety_*, i_safety_*, chg/dchg_end_capacity_cutoff,
      record_interval_s, chamber_temp_c, mode_flag, schedule_description)
  2. v_chg 키 mismatch fix (Phase 0-1a) — `voltage_mV` 사용
  3. CC vs CCCV V cutoff 분리 (사용자 통찰):
     - CC mode: +28 end_voltage_mV = 실제 cutoff
     - CCCV mode: +12 voltage_mV = CC target = CV target
  4. schedule keyword classifier (header +664) — ambiguous case prior
  5. +336 < 5 hint → GITT/PULSE 강한 hint

산출:
  tools/sch_phase0_5_groups.csv  — 사이클(loop group)별 정의 한 row
  tools/sch_phase0_5_files.csv   — 파일별 메타 + 카테고리 분포
  tools/sch_phase0_5_summary.md  — 시험종류·카테고리 분포 + 폴더 list
"""
from __future__ import annotations

import csv
import re
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

EXP_ROOT = Path(r"C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data")
OUT_DIR = Path(__file__).parent
HEADER_SIZE = 1920
BLOCK_SIZE = 652

# ===========================================================
# Step type map (proto file L7570 — 2026-04-26 swap 정정 후)
# ===========================================================
SCH_TYPE_MAP: dict[int, str] = {
    0x0101: 'CHG_CCCV', 0x0102: 'DCHG_CCCV',
    0x0201: 'CHG_CC',   0x0202: 'DCHG_CC',
    0x0209: 'CHG_CP',
    0xFF03: 'REST', 0xFF06: 'GOTO', 0xFF07: 'REST_SAFE', 0xFF08: 'LOOP',
    0x0003: 'GITT_PAUSE', 0x0006: 'END',
    0x0007: 'GITT_END', 0x0008: 'GITT_START',
}

CHG_TYPES = frozenset({'CHG_CC', 'CHG_CCCV', 'CHG_CP'})
DCHG_TYPES = frozenset({'DCHG_CC', 'DCHG_CCCV'})
GITT_TYPES = frozenset({'GITT_PAUSE', 'GITT_END', 'GITT_START'})
CTRL_TYPES = frozenset({'LOOP', 'GOTO', 'REST_SAFE', 'END'})


# ===========================================================
# 1. Phase 0-5 enhanced parser
# ===========================================================
def parse_pne_sch_v2(sch_path: Path) -> dict | None:
    try:
        with open(sch_path, 'rb') as f:
            data = f.read()
    except OSError:
        return None
    if len(data) < HEADER_SIZE + BLOCK_SIZE:
        return None
    if struct.unpack_from('<I', data, 0)[0] != 740721:
        return None

    n_steps = (len(data) - HEADER_SIZE) // BLOCK_SIZE
    if n_steps <= 0:
        return None

    # ---- Header (Phase 0-2 confirmed schema) ----
    header = {
        'magic': struct.unpack_from('<I', data, 0)[0],
        'format_version': struct.unpack_from('<I', data, 4)[0],   # 131077
        'header_record_count': struct.unpack_from('<I', data, 8)[0],   # 50
        'block_count_meta': struct.unpack_from('<I', data, 656)[0],
    }
    desc_b = data[664:664 + 64]
    end = desc_b.find(b'\x00')
    if end >= 0:
        desc_b = desc_b[:end]
    try:
        header['schedule_description'] = desc_b.decode('ascii',
                                                       errors='replace').strip()
    except Exception:
        header['schedule_description'] = ''

    # ---- Step blocks ----
    steps: list[dict] = []
    loop_steps: list[dict] = []
    chg_steps: list[dict] = []
    dchg_steps: list[dict] = []

    for i in range(n_steps):
        ofs = HEADER_SIZE + i * BLOCK_SIZE
        blk = data[ofs:ofs + BLOCK_SIZE]
        step_num = struct.unpack_from('<I', blk, 0)[0]
        type_code = struct.unpack_from('<I', blk, 8)[0]
        type_name = SCH_TYPE_MAP.get(type_code, f'UNK_0x{type_code:04X}')

        s: dict = {
            'step': step_num,
            'idx': i,
            'type': type_name,
            'type_code': type_code,
        }

        if type_name in CHG_TYPES:
            s.update({
                'voltage_mV':       struct.unpack_from('<f', blk, 12)[0],
                'current_mA':       struct.unpack_from('<f', blk, 20)[0],
                'time_limit_s':     struct.unpack_from('<f', blk, 24)[0],
                'end_voltage_mV':   struct.unpack_from('<f', blk, 28)[0],
                'end_current_mA':   struct.unpack_from('<f', blk, 32)[0],
                'capacity_limit_mAh': struct.unpack_from('<f', blk, 104)[0],
                'chg_end_capacity_cutoff_mAh': struct.unpack_from('<f', blk, 36)[0],
            })
            chg_steps.append(s)
        elif type_name in DCHG_TYPES:
            s.update({
                'voltage_mV':       struct.unpack_from('<f', blk, 16)[0],
                'current_mA':       struct.unpack_from('<f', blk, 20)[0],
                'time_limit_s':     struct.unpack_from('<f', blk, 24)[0],
                'end_voltage_mV':   struct.unpack_from('<f', blk, 28)[0],
                'end_current_mA':   struct.unpack_from('<f', blk, 32)[0],
                'capacity_limit_mAh': struct.unpack_from('<f', blk, 104)[0],
                'dchg_end_capacity_cutoff_mAh': struct.unpack_from('<f', blk, 40)[0],
            })
            dchg_steps.append(s)
        elif type_name == 'LOOP':
            s['loop_count'] = struct.unpack_from('<I', blk, 56)[0]
            gtgt = struct.unpack_from('<I', blk, 52)[0]
            grep = struct.unpack_from('<I', blk, 580)[0]
            if gtgt > 0 and grep > 0:
                s['goto_target_step'] = int(gtgt)
                s['goto_repeat_count'] = int(grep)
            loop_steps.append(s)
        elif type_name in ('REST', 'REST_SAFE'):
            s['time_limit_s'] = struct.unpack_from('<f', blk, 24)[0]
        elif type_name == 'GOTO':
            s['goto_target'] = struct.unpack_from('<I', blk, 56)[0]

        # ---- Phase 0-2 confirmed common fields (active types) ----
        s['v_safety_upper_mV']   = struct.unpack_from('<f', blk, 88)[0]
        s['v_safety_lower_mV']   = struct.unpack_from('<f', blk, 92)[0]
        s['i_safety_upper_mA']   = struct.unpack_from('<f', blk, 96)[0]
        s['i_safety_lower_mA']   = struct.unpack_from('<f', blk, 100)[0]
        s['record_interval_s']   = struct.unpack_from('<f', blk, 336)[0]
        s['chamber_temp_c']      = struct.unpack_from('<f', blk, 396)[0]
        s['mode_flag']           = struct.unpack_from('<I', blk, 84)[0]

        # ---- End condition (SOC/DOD ref-step jump) ----
        ec_type = struct.unpack_from('<I', blk, 500)[0]
        ec_enabled = struct.unpack_from('<I', blk, 504)[0]
        if ec_type != 0 and ec_enabled == 1:
            ec_value = struct.unpack_from('<f', blk, 372)[0]
            s['end_condition'] = {
                'type': ec_type,
                'value_pct': round(ec_value, 2),
            }

        steps.append(s)

    if not steps:
        return None

    return {
        'header': header,
        'steps': steps,
        'loop_steps': loop_steps,
        'charge_steps': chg_steps,
        'discharge_steps': dchg_steps,
    }


# ===========================================================
# 2. Loop group decompose + outer goto expand (proto L7936/8300)
# ===========================================================
def decompose_loop_groups(steps: list[dict]) -> list[dict]:
    groups: list[dict] = []
    body_start = 0
    body_start_step = 1
    for i, s in enumerate(steps):
        if s['type'] == 'LOOP':
            body = [steps[j] for j in range(body_start, i)
                    if steps[j]['type'] not in CTRL_TYPES]
            groups.append({
                'loop_count': s.get('loop_count', 1),
                'body': body,
                'body_start_step': body_start_step,
                'goto_target_step': s.get('goto_target_step'),
                'goto_repeat_count': s.get('goto_repeat_count', 0),
                'loop_step_idx': i,
            })
            nxt = i + 1
            if nxt < len(steps) and steps[nxt]['type'] == 'REST_SAFE':
                nxt += 1
            body_start = nxt
            body_start_step = nxt + 1
    return groups


def expand_with_outer_goto(groups: list[dict]) -> list[dict]:
    if not groups:
        return groups
    expanded = []
    i = 0
    while i < len(groups):
        g = groups[i]
        expanded.append(g)
        gtgt = g.get('goto_target_step')
        grep = g.get('goto_repeat_count', 0) or 0
        if gtgt and grep > 0:
            target_idx = None
            for j in range(len(groups)):
                bs = groups[j].get('body_start_step', 0)
                if bs <= gtgt:
                    target_idx = j
                else:
                    break
            if target_idx is None or target_idx > i:
                i += 1
                continue
            block = groups[target_idx:i + 1]
            for _ in range(grep):
                expanded.extend(block)
        i += 1
    return expanded


# ===========================================================
# 3. Phase 0-5 v2 classifier
# ===========================================================
def classify_loop_group_v2(
    body: list[dict],
    loop_count: int,
    position: int,
    total_loops: int,
    capacity_mAh: float,
    schedule_desc: str = '',
) -> tuple[str, str]:
    """Return (category, sub_tag).

    category: 22 카테고리 (proto L7975 + Phase 0-5 fix)
    sub_tag:  Phase 0-5 추가 — 'cc_only' / 'cccv_only' / 'multi_step' / 'gitt_block' / ''
    """
    if not body:
        return 'EMPTY', ''

    N = loop_count
    types = [s['type'] for s in body]
    type_set = set(types)

    chg = [s for s in body if s['type'] in CHG_TYPES]
    dchg = [s for s in body if s['type'] in DCHG_TYPES]
    rest = [s for s in body if s['type'] == 'REST']
    ec_steps = [s for s in body
                if s.get('end_condition', {}).get('type', 0) != 0]
    has_ec = bool(ec_steps)
    ec_on_dchg = [s for s in ec_steps if s['type'] in DCHG_TYPES]
    ec_on_chg = [s for s in ec_steps if s['type'] in CHG_TYPES]
    has_chg_cp = 'CHG_CP' in type_set
    has_dchg_cccv = 'DCHG_CCCV' in type_set
    has_gitt_block = bool(type_set & GITT_TYPES)
    has_short_dchg = any(0 < s.get('time_limit_s', 0) <= 30 for s in dchg)
    has_short_chg = any(0 < s.get('time_limit_s', 0) <= 30 for s in chg)
    rate_02c = capacity_mAh * 0.2 if capacity_mAh > 0 else 0

    # Phase 0-5: schedule keyword prior (used as final tie-breaker only)
    desc_lower = schedule_desc.lower()
    desc_kw = ''
    if 'hysteresis' in desc_lower:
        desc_kw = 'hysteresis'
    elif 'gitt' in desc_lower:
        desc_kw = 'gitt'
    elif 'ect' in desc_lower:
        desc_kw = 'ect'
    elif 'floating' in desc_lower or '120d' in desc_lower:
        desc_kw = 'floating'
    elif 'rss' in desc_lower:
        desc_kw = 'rss'
    elif 'dcir' in desc_lower:
        desc_kw = 'dcir'
    elif 'rpt' in desc_lower:
        desc_kw = 'rpt'
    elif 'formation' in desc_lower or '화성' in desc_lower:
        desc_kw = 'formation'

    # Phase 0-5: short sampling rate hint (+336 < 5 → pulse measurement)
    short_sampling = any(
        0 < s.get('record_interval_s', 60) < 5 for s in body)

    # 1. INIT: 첫 Loop, 방전만(+REST), N=1
    if position == 0 and N == 1:
        if all(s['type'] in (DCHG_TYPES | {'REST'}) for s in body):
            if any(s['type'] in DCHG_TYPES for s in body):
                return 'INIT', ''

    # 2. GITT_PULSE
    if has_gitt_block and N >= 10:
        return 'GITT_PULSE', 'gitt_block'
    max_rest_s = max((s.get('time_limit_s', 0) for s in rest), default=0)
    if N >= 10 and len(body) <= 3 and max_rest_s >= 600:
        non_rest = [s for s in body if s['type'] != 'REST']
        if non_rest and any(s['type'] in (CHG_TYPES | DCHG_TYPES)
                            for s in non_rest):
            sub = 'short_sampling' if short_sampling else ''
            return 'GITT_PULSE', sub

    # 2b. FLOATING (Phase 0-1a fix: 'voltage_mV' 사용)
    if chg and not dchg:
        max_chg_time = max((s.get('time_limit_s', 0) for s in chg), default=0)
        # Fix: voltage_mV (parser actually emits this key)
        has_v_cut = any(s.get('voltage_mV', 0) > 0 for s in chg)
        if max_chg_time >= 43200 and has_v_cut:
            sub = ''
            if all(s['type'] == 'CHG_CCCV' for s in chg):
                sub = 'cccv'
            elif all(s['type'] == 'CHG_CC' for s in chg):
                sub = 'cc'
            return 'FLOATING', sub

    # 3. ACCEL: 다단충전(CHG≥2) + 방전, N≥20
    if N >= 20 and len(chg) >= 2 and dchg:
        sub = 'multi_step' if len(chg) >= 3 else ''
        return 'ACCEL', sub

    # 4. HYSTERESIS_DCHG
    if (N == 1 and not has_short_dchg and any(
            s.get('end_condition', {}).get('type') == 2048
            for s in ec_on_dchg)):
        return 'HYSTERESIS_DCHG', desc_kw if desc_kw == 'hysteresis' else ''

    # 5. HYSTERESIS_CHG
    if (N == 1 and not has_short_chg and any(
            s.get('end_condition', {}).get('type') == 18432
            for s in ec_on_chg)):
        return 'HYSTERESIS_CHG', desc_kw if desc_kw == 'hysteresis' else ''

    # 6. SOC_DCIR
    if 5 <= N < 20 and len(ec_steps) >= 4 and len(body) >= 8:
        ec_type_set = {s.get('end_condition', {}).get('type', 0)
                       for s in ec_steps}
        if len(ec_type_set) >= 3:
            return 'SOC_DCIR', ''

    # 7. PULSE_DCIR (Phase 0-5: short_sampling 추가 hint)
    if has_ec and has_short_dchg and len(dchg) >= 2 and len(body) >= 5:
        sub = 'short_sampling' if short_sampling else ''
        return 'PULSE_DCIR', sub

    # 8. RSS_DCIR
    if N == 1 and has_ec and len(dchg) >= 4 and len(body) >= 10:
        return 'RSS_DCIR', ''

    # 9. DISCHARGE_SET
    if N == 1 and has_dchg_cccv and len(body) <= 2:
        return 'DISCHARGE_SET', ''

    # 10. POWER_CHG
    if has_chg_cp:
        return 'POWER_CHG', ''

    # 11. REST_LONG
    if len(body) == 1 and types[0] == 'REST':
        if body[0].get('time_limit_s', 0) >= 3600:
            return 'REST_LONG', ''

    # 12. FORMATION
    if 2 <= N <= 10 and chg and dchg:
        return 'FORMATION', ''

    # 13. CHARGE_SET
    if N == 1 and chg and not dchg:
        if type_set <= (CHG_TYPES | {'REST', 'REST_SAFE'}):
            sub = ''
            if all(s['type'] == 'CHG_CCCV' for s in chg):
                sub = 'cccv'
            return 'CHARGE_SET', sub

    # 14. TERMINATION
    if position == total_loops - 1 and N == 1 and dchg and not chg:
        return 'TERMINATION', ''

    # 14b. DCHG_SET
    if N == 1 and dchg and not chg:
        return 'DCHG_SET', ''

    # 15. RPT
    if N == 1 and chg and dchg and rate_02c > 0:
        currents = [s.get('current_mA', 0) for s in chg + dchg
                    if s.get('current_mA', 0) > 0]
        if currents and all(
                abs(I - rate_02c) / rate_02c < 0.3 for I in currents):
            return 'RPT', ''

    # 16. CHG_DCHG
    if N == 1 and chg and dchg:
        return 'CHG_DCHG', ''

    # 17. SWEEP_PULSE
    if N >= 10 and len(body) <= 3:
        return 'SWEEP_PULSE', ''

    # 18. REST_SHORT
    if len(body) == 1 and types[0] == 'REST':
        return 'REST_SHORT', ''

    return 'UNKNOWN', ''


def step_v_cutoff_mV(s: dict) -> float:
    """Phase 0-5 사용자 통찰: CC vs CCCV 의 V cutoff 의미 분리."""
    t = s.get('type', '')
    if t in ('CHG_CCCV', 'DCHG_CCCV'):
        return s.get('voltage_mV', 0)  # CV target
    if t in ('CHG_CC', 'DCHG_CC'):
        return s.get('end_voltage_mV', 0)  # EndCondition
    return 0


# ===========================================================
# 4. Per-folder capacity extraction (path table fallback)
# ===========================================================
_CAP_PATTERNS = [
    re.compile(r'(\d+)\s*mAh', re.IGNORECASE),
    re.compile(r'_(\d{3,5})mAh_', re.IGNORECASE),
    re.compile(r'(\d{3,5})\s*[mM][aA][hH]'),
]


def extract_capacity_from_name(name: str) -> float:
    """폴더명에서 capacity (mAh) 추출. 없으면 0."""
    for pat in _CAP_PATTERNS:
        m = pat.search(name)
        if m:
            try:
                v = float(m.group(1))
                if 100 <= v <= 100000:  # sane range
                    return v
            except ValueError:
                continue
    return 0.0


# ===========================================================
# 5. Main batch
# ===========================================================
def main() -> int:
    if not EXP_ROOT.exists():
        print(f"ERROR: {EXP_ROOT} not found.", file=sys.stderr)
        return 1

    sch_files = sorted(EXP_ROOT.rglob('*.sch'))
    print(f"Found {len(sch_files)} .sch files under {EXP_ROOT}",
          file=sys.stderr)

    file_rows: list[dict] = []
    group_rows: list[dict] = []
    failed_files: list[str] = []

    # Aggregations
    cat_by_test: defaultdict[str, Counter] = defaultdict(Counter)
    folders_by_test: defaultdict[str, set] = defaultdict(set)
    cat_global: Counter = Counter()

    for fi, sch_path in enumerate(sch_files):
        if fi % 50 == 0 and fi > 0:
            print(f"  [{fi}/{len(sch_files)}]", file=sys.stderr)

        try:
            rel = sch_path.relative_to(EXP_ROOT)
        except ValueError:
            rel = sch_path
        rel_str = str(rel)
        parts = rel.parts
        test_cat = parts[0] if len(parts) >= 1 else 'UNKNOWN'
        exp_folder = parts[1] if len(parts) >= 2 else parts[0]

        parsed = parse_pne_sch_v2(sch_path)
        if parsed is None:
            failed_files.append(rel_str)
            continue

        header = parsed['header']
        desc = header.get('schedule_description', '')
        capacity_mAh = extract_capacity_from_name(exp_folder)
        if capacity_mAh == 0:
            # fallback: from schedule_description
            capacity_mAh = extract_capacity_from_name(desc)
        if capacity_mAh == 0:
            # fallback: from +104 (per-step capacity_limit) — first non-zero
            for s in parsed['steps']:
                cl = s.get('capacity_limit_mAh', 0)
                if cl and cl > 0:
                    capacity_mAh = cl
                    break

        # File-level aggregates
        intervals = [s.get('record_interval_s', 0) for s in parsed['steps']
                     if s.get('record_interval_s', 0) > 0]
        chambers = [s.get('chamber_temp_c', 0) for s in parsed['steps']
                    if s.get('chamber_temp_c', 0) != 0]
        v_uppers = [s.get('v_safety_upper_mV', 0) for s in parsed['steps']
                    if s.get('v_safety_upper_mV', 0) > 0]
        first_iv = intervals[0] if intervals else 0
        first_chamber = chambers[0] if chambers else 0
        first_vu = v_uppers[0] if v_uppers else 0

        # Decompose + expand
        groups = decompose_loop_groups(parsed['steps'])
        expanded = expand_with_outer_goto(groups)

        # Classify each group
        tc = 1
        n_total_groups = len(expanded)
        per_file_cats: Counter = Counter()
        per_file_groups: list[dict] = []

        for gi, g in enumerate(expanded):
            n = max(g['loop_count'], 1)
            cat, sub = classify_loop_group_v2(
                g['body'], g['loop_count'], gi, n_total_groups,
                capacity_mAh, desc)

            chg_cr = None
            dchg_cr = None
            if capacity_mAh > 0:
                chg_currents = [s.get('current_mA', 0) for s in g['body']
                                if s['type'] in CHG_TYPES
                                and s.get('current_mA', 0) > 0]
                dchg_currents = [s.get('current_mA', 0) for s in g['body']
                                 if s['type'] in DCHG_TYPES
                                 and s.get('current_mA', 0) > 0]
                if chg_currents:
                    chg_cr = round(max(chg_currents) / capacity_mAh, 2)
                if dchg_currents:
                    dchg_cr = round(max(dchg_currents) / capacity_mAh, 2)

            # CC vs CCCV V cutoff (Phase 0-5)
            chg_v_cuts = sorted({
                round(step_v_cutoff_mV(s)) for s in g['body']
                if s['type'] in CHG_TYPES and step_v_cutoff_mV(s) > 0
            })
            dchg_v_cuts = sorted({
                round(step_v_cutoff_mV(s)) for s in g['body']
                if s['type'] in DCHG_TYPES and step_v_cutoff_mV(s) > 0
            })

            n_chg = len([s for s in g['body'] if s['type'] in CHG_TYPES])
            n_dchg = len([s for s in g['body'] if s['type'] in DCHG_TYPES])
            n_rest = len([s for s in g['body'] if s['type'] == 'REST'])

            # Body sample interval (use first non-zero)
            body_intervals = [s.get('record_interval_s', 0) for s in g['body']
                              if s.get('record_interval_s', 0) > 0]
            min_iv = min(body_intervals) if body_intervals else 0

            # End condition types (DOD%/SOC%) used in body
            ec_types_used = sorted({
                s.get('end_condition', {}).get('type', 0)
                for s in g['body']
                if s.get('end_condition', {}).get('type', 0) != 0
            })

            row = {
                'test_category': test_cat,
                'exp_folder': exp_folder,
                'sch_file': rel.name,
                'rel_path': rel_str,
                'capacity_mAh': round(capacity_mAh, 1),
                'schedule_desc': desc,
                'group_idx': gi,
                'tc_start': tc,
                'tc_end': tc + n - 1,
                'loop_count': n,
                'category': cat,
                'sub_tag': sub,
                'chg_crate': chg_cr,
                'dchg_crate': dchg_cr,
                'n_chg_step': n_chg,
                'n_dchg_step': n_dchg,
                'n_rest_step': n_rest,
                'body_size': len(g['body']),
                'chg_v_cutoff_mV': ';'.join(str(v) for v in chg_v_cuts),
                'dchg_v_cutoff_mV': ';'.join(str(v) for v in dchg_v_cuts),
                'min_record_interval_s': min_iv,
                'ec_types': ';'.join(str(t) for t in ec_types_used),
                'chamber_c': first_chamber,
                'v_upper_mV': first_vu,
                'has_outer_goto': bool(g.get('goto_target_step')),
            }
            per_file_groups.append(row)
            group_rows.append(row)
            cat_global[cat] += 1
            cat_by_test[test_cat][cat] += 1
            per_file_cats[cat] += 1
            tc += n

        folders_by_test[test_cat].add(exp_folder)
        # Total TC count = last tc - 1
        total_tc = tc - 1
        cat_summary = ', '.join(f'{c}:{n}'
                                for c, n in per_file_cats.most_common())
        file_rows.append({
            'test_category': test_cat,
            'exp_folder': exp_folder,
            'sch_file': rel.name,
            'rel_path': rel_str,
            'capacity_mAh': round(capacity_mAh, 1),
            'schedule_desc': desc,
            'n_steps': len(parsed['steps']),
            'n_groups_expanded': n_total_groups,
            'total_tc': total_tc,
            'first_record_interval_s': first_iv,
            'first_chamber_c': first_chamber,
            'first_v_upper_mV': first_vu,
            'category_summary': cat_summary,
        })

    # ----- CSV outputs -----
    groups_csv = OUT_DIR / 'sch_phase0_5_groups.csv'
    if group_rows:
        with open(groups_csv, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=list(group_rows[0].keys()))
            writer.writeheader()
            writer.writerows(group_rows)
        print(f"Wrote {groups_csv} ({len(group_rows)} groups)",
              file=sys.stderr)

    files_csv = OUT_DIR / 'sch_phase0_5_files.csv'
    if file_rows:
        with open(files_csv, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=list(file_rows[0].keys()))
            writer.writeheader()
            writer.writerows(file_rows)
        print(f"Wrote {files_csv} ({len(file_rows)} files)", file=sys.stderr)

    # ----- Total folder count (entire test category, with or w/o .sch) -----
    total_folders_per_cat: dict[str, int] = {}
    for cat in folders_by_test.keys():
        cat_dir = EXP_ROOT / cat
        if cat_dir.exists():
            total_folders_per_cat[cat] = sum(
                1 for p in cat_dir.iterdir() if p.is_dir())
        else:
            total_folders_per_cat[cat] = 0
    n_total_folders = sum(total_folders_per_cat.values())
    n_folders_with_sch = sum(len(s) for s in folders_by_test.values())

    # ----- Summary md -----
    md = []
    md.append(f'# Phase 0-5 분류기 v2 — '
              f'{n_total_folders} 폴더 / {len(sch_files)} .sch 사이클별 정의')
    md.append('')
    md.append(f'- 입력 root: `{EXP_ROOT}`')
    md.append(f'- 실험 폴더: **{n_total_folders}** '
              f'(`.sch` 보유 {n_folders_with_sch}, '
              f'미보유 {n_total_folders - n_folders_with_sch} = Toyo `.ptn` 또는 미확보)')
    md.append(f'- .sch 파일: **{len(sch_files)}** '
              f'(parsed {len(file_rows)}, failed {len(failed_files)})')
    md.append(f'- 총 loop group (outer-goto expanded): **{len(group_rows)}**')
    md.append(f'- 산출물:')
    md.append(f'  - [`sch_phase0_5_groups.csv`](sch_phase0_5_groups.csv) — '
              f'사이클(loop group) 단위 정의 한 row')
    md.append(f'  - [`sch_phase0_5_files.csv`](sch_phase0_5_files.csv) — '
              f'파일 단위 메타 + 카테고리 분포')
    md.append('')
    md.append('## 1. 시험종류 × 카테고리 cross-table')
    md.append('')
    cat_order = [c for c, _ in cat_global.most_common()]
    test_order = sorted(folders_by_test.keys())
    md.append('| 시험종류 | 폴더(.sch/전체) | 파일 | TC총수 | '
              + ' | '.join(cat_order) + ' |')
    md.append('|' + '---|' * (4 + len(cat_order)))
    for tc_name in test_order:
        n_folders = len(folders_by_test[tc_name])
        n_total = total_folders_per_cat.get(tc_name, n_folders)
        n_files = sum(1 for r in file_rows if r['test_category'] == tc_name)
        n_tc = sum(r['total_tc'] for r in file_rows
                   if r['test_category'] == tc_name)
        cells = [str(cat_by_test[tc_name].get(c, 0)) for c in cat_order]
        md.append(f'| {tc_name} | {n_folders}/{n_total} | {n_files} | {n_tc} | '
                  + ' | '.join(cells) + ' |')
    md.append('')

    md.append('## 2. 카테고리 전역 분포')
    md.append('')
    md.append('| Category | count | 비율 |')
    md.append('|---|---|---|')
    total_g = sum(cat_global.values())
    for c, n in cat_global.most_common():
        pct = n / total_g * 100 if total_g else 0
        md.append(f'| {c} | {n} | {pct:.1f}% |')
    md.append('')

    md.append('## 3. UNKNOWN / EMPTY 발생 파일 (sch + body signature 단위 dedup)')
    md.append('')
    unknown_groups = [r for r in group_rows
                      if r['category'] in ('UNKNOWN', 'EMPTY')]
    if unknown_groups:
        # body signature 로 dedup — 같은 .sch 내 outer-goto 확장으로 인한 중복 제거
        seen: set[tuple] = set()
        unknown_dedup: list[dict] = []
        for r in unknown_groups:
            sig = (
                r['rel_path'],
                r['loop_count'],
                r['body_size'],
                r['n_chg_step'],
                r['n_dchg_step'],
                r['n_rest_step'],
                r['ec_types'],
            )
            if sig not in seen:
                seen.add(sig)
                unknown_dedup.append(r)
        md.append(f'총 **{len(unknown_groups)}** 그룹 '
                  f'(dedup body-signature 기준 **{len(unknown_dedup)}** 종).')
        md.append(f'대다수는 outer-goto 확장으로 인한 동일 body 중복.')
        md.append('')
        md.append('| 시험종류 | 폴더 | sch | N | body | chg/dchg/rest |'
                  ' EC types | desc |')
        md.append('|' + '---|' * 8)
        for r in unknown_dedup[:30]:
            md.append(
                f"| {r['test_category']} | {r['exp_folder'][:40]} |"
                f" {r['sch_file'][:50]} | {r['loop_count']} |"
                f" {r['body_size']} |"
                f" {r['n_chg_step']}/{r['n_dchg_step']}/{r['n_rest_step']} |"
                f" {r['ec_types']} | {r['schedule_desc'][:30]} |")
        if len(unknown_dedup) > 30:
            md.append(f'\n(+{len(unknown_dedup) - 30} more — see CSV)')
    else:
        md.append('없음 ✅')
    md.append('')

    md.append('## 4. 폴더 × 카테고리 분포 (실험 폴더 단위)')
    md.append('')
    md.append('한 폴더 내 채널별 .sch 가 동일 schedule 인 케이스가 있어, '
              '동일 폴더의 categories 는 채널 수만큼 곱해진 집계.')
    md.append('')
    folder_cats: defaultdict[tuple, Counter] = defaultdict(Counter)
    folder_files: defaultdict[tuple, int] = defaultdict(int)
    for r in group_rows:
        folder_cats[(r['test_category'], r['exp_folder'])][r['category']] += 1
    for r in file_rows:
        folder_files[(r['test_category'], r['exp_folder'])] += 1
    md.append('| 시험종류 | 폴더 | n_sch | TC총수 | 카테고리 분포 |')
    md.append('|---|---|---|---|---|')
    for (tc_name, folder), cats in sorted(folder_cats.items()):
        n_tc = sum(r['total_tc'] for r in file_rows
                   if r['test_category'] == tc_name
                   and r['exp_folder'] == folder)
        n_sch = folder_files[(tc_name, folder)]
        cat_str = ', '.join(f'{c}({n})' for c, n in cats.most_common())
        md.append(f'| {tc_name} | {folder[:60]} | {n_sch} | {n_tc} | {cat_str} |')
    md.append('')

    md.append('## 5. 폴더명 ↔ 카테고리 정합성 의심 list')
    md.append('')
    md.append('폴더명에 키워드는 있는데 해당 카테고리가 0인 케이스:')
    md.append('')
    md.append('| 시험종류 | 폴더 | 키워드 | 발견 카테고리 |')
    md.append('|---|---|---|---|')
    suspicious = []
    KW_MAP = {
        'hysteresis': 'HYSTERESIS',
        'floating': 'FLOATING',
        'dcir': '_DCIR',
        'rss': 'RSS_DCIR',
        'gitt': 'GITT_PULSE',
        'rpt': 'RPT',
    }
    for (tc_name, folder), cats in sorted(folder_cats.items()):
        flow = folder.lower()
        for kw, cat_kw in KW_MAP.items():
            if kw in flow:
                hit = any(cat_kw in c for c in cats.keys())
                if not hit:
                    suspicious.append((tc_name, folder, kw, cats))
    for tc_name, folder, kw, cats in suspicious[:40]:
        cat_str = ', '.join(f'{c}({n})' for c, n in cats.most_common(3))
        md.append(f'| {tc_name} | {folder[:60]} | `{kw}` | {cat_str} |')
    if len(suspicious) > 40:
        md.append(f'\n(+{len(suspicious) - 40} more)')
    md.append('')

    if failed_files:
        md.append('## 6. ⚠️ Parse 실패 파일')
        md.append('')
        for p in failed_files[:30]:
            md.append(f'- `{p}`')
        if len(failed_files) > 30:
            md.append(f'- (+{len(failed_files) - 30} more)')
        md.append('')

    md.append('## 7. 분류기 v2 spec 적용 사항 (Phase 0-5)')
    md.append('')
    md.append('1. ⚠️ **`v_chg` 키 mismatch fix** (Phase 0-1a) —'
              ' L8053 `v_chg_mV/v_chg` → `voltage_mV` 사용.')
    md.append('   FLOATING 카테고리 분류 활성화.')
    md.append('2. **CC vs CCCV V cutoff 분리** (사용자 통찰):')
    md.append('   - CC mode: `+28 end_voltage_mV` = 실제 cutoff')
    md.append('   - CCCV mode: `+12 voltage_mV` = CC target = CV target')
    md.append('3. **9 신규 field parser 추가** — `v_safety_upper/lower_mV`,'
              ' `i_safety_upper/lower_mA`,'
              ' `chg/dchg_end_capacity_cutoff_mAh`,'
              ' `record_interval_s`, `chamber_temp_c`, `mode_flag`,'
              ' header `format_version`/`header_record_count`/'
              '`block_count_meta`/`schedule_description`.')
    md.append('4. **Schedule keyword classifier** (header `+664`) —'
              ' hysteresis/gitt/ect/floating/rss/dcir/rpt/formation prior.')
    md.append('5. **`+336 < 5` short_sampling hint** —'
              ' GITT_PULSE / PULSE_DCIR sub-tag.')
    md.append('')

    out_md = OUT_DIR / 'sch_phase0_5_summary.md'
    with open(out_md, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    print(f"Wrote {out_md}", file=sys.stderr)
    print('Done.', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
