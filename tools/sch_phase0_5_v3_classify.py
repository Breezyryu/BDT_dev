"""Phase 0-5 v3 분류기 — 모든 발견 통합 (v2 + Phase 0-5-α + mode_flag).

v3 의 v2 대비 변경:
  ⭐ Parser 보강:
    1. ref_step_number = +501 byte (Phase 0-5-α 발견)
    2. mode_flag = +84 (cycle counter 인식 표시)
    3. (Tier 1 Only) record_interval_s = +336, schedule_description = +664

  ⭐ 분류기 룰 보강:
    A. ref_step 기반 hysteresis/DCIR 일반화
       - HYSTERESIS_DCHG: N=1 + DCHG + ref_step≠0 + DCHG ref step (was: ec_type==2048)
       - HYSTERESIS_CHG:  N=1 + CHG  + ref_step≠0 + CHG ref step (was: ec_type==18432)
       - 분류기는 type=2048/18432 외 임의 값 인식
    B. PULSE_DCIR 보강: DCHG_CCCV + mode=0 → 강한 hint
    C. ECT 신규 카테고리: REST 다수 mode=0 + chamber≠0 + +336=1s
    D. ACCEL N=14 mid-range gap fix:
       - 기존: N≥20
       - v3:  N≥10 + multi-step (≥3 CHG) — sub_tag 'mid_life' if N<20
    E. schedule keyword prior (v2 에 이미)
    F. CC vs CCCV V cutoff helper (v2 에 이미)
    G. v_chg 키 fix (v2 에 이미)

산출:
  tools/sch_phase0_5_v3_groups.csv  — v3 사이클 그룹 정의
  tools/sch_phase0_5_v3_files.csv   — v3 파일 메타
  tools/sch_phase0_5_v3_summary.md  — v3 분류 결과 요약
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
# 1. v3 enhanced parser (ref_step_number + mode_flag + record_interval_s)
# ===========================================================
def parse_pne_sch_v3(sch_path: Path) -> dict | None:
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

    # Header
    header = {
        'magic': struct.unpack_from('<I', data, 0)[0],
        'format_version': struct.unpack_from('<I', data, 4)[0],
        'header_record_count': struct.unpack_from('<I', data, 8)[0],
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
            # ⭐ v3 신규: mode_flag (cycle counter 인식)
            'mode_flag': struct.unpack_from('<I', blk, 84)[0],
            # ⭐ v3 신규: record_interval_s
            'record_interval_s': struct.unpack_from('<f', blk, 336)[0],
            # ⭐ v3 신규: chamber_temp_c (ECT 식별)
            'chamber_temp_c': struct.unpack_from('<f', blk, 396)[0],
        }

        if type_name in CHG_TYPES:
            s.update({
                'voltage_mV':       struct.unpack_from('<f', blk, 12)[0],
                'current_mA':       struct.unpack_from('<f', blk, 20)[0],
                'time_limit_s':     struct.unpack_from('<f', blk, 24)[0],
                'end_voltage_mV':   struct.unpack_from('<f', blk, 28)[0],
                'end_current_mA':   struct.unpack_from('<f', blk, 32)[0],
                'capacity_limit_mAh': struct.unpack_from('<f', blk, 104)[0],
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

        # ⭐ v3 신규: ref_step_number = +501 byte (Phase 0-5-α)
        ec500 = struct.unpack_from('<I', blk, 500)[0]
        ec504 = struct.unpack_from('<I', blk, 504)[0]
        if ec500 != 0 and ec504 == 1:
            ec_value = struct.unpack_from('<f', blk, 372)[0]
            s['end_condition'] = {
                'type': ec500,                          # legacy field
                'value_pct': round(ec_value, 2),
                'ref_step_number': (ec500 >> 8) & 0xFF,  # ⭐ Phase 0-5-α
                'type_marker': ec500 & 0xFF,             # 항상 0 in observed
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
# 2. Loop group decompose + outer goto (v2 동일)
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
# 3. v3 classifier with all enhancements
# ===========================================================
def classify_loop_group_v3(
    body: list[dict],
    loop_count: int,
    position: int,
    total_loops: int,
    capacity_mAh: float,
    schedule_desc: str = '',
) -> tuple[str, str]:
    """v3 분류기 — return (category, sub_tag)."""
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

    # ⭐ v3 신규: ref_step 기반 룰
    has_ref_step_dchg = any(
        s.get('end_condition', {}).get('ref_step_number', 0) > 0
        for s in ec_on_dchg)
    has_ref_step_chg = any(
        s.get('end_condition', {}).get('ref_step_number', 0) > 0
        for s in ec_on_chg)

    # ⭐ v3 신규: mode_flag 활용 (DCIR pulse 식별)
    n_dchg_cccv_mode0 = sum(
        1 for s in body
        if s['type'] == 'DCHG_CCCV' and s.get('mode_flag', 0) == 0)
    has_dchg_cccv_pulse = n_dchg_cccv_mode0 > 0

    # ⭐ v3 신규: ECT 식별 — REST 다수 mode=0 + chamber≠0
    n_rest_mode0_chamber = sum(
        1 for s in rest
        if s.get('mode_flag', 0) == 0 and s.get('chamber_temp_c', 0) != 0)
    n_rest = len(rest)
    rest_mode0_chamber_ratio = (
        n_rest_mode0_chamber / n_rest if n_rest > 0 else 0)

    # ⭐ v3 신규: schedule keyword prior
    desc_lower = schedule_desc.lower()
    desc_kw = ''
    if 'rss' in desc_lower:
        desc_kw = 'rss'
    elif 'hysteresis' in desc_lower:
        desc_kw = 'hysteresis'
    elif 'gitt' in desc_lower:
        desc_kw = 'gitt'
    elif 'ect' in desc_lower:
        desc_kw = 'ect'
    elif 'floating' in desc_lower or '120d' in desc_lower or '280day' in desc_lower:
        desc_kw = 'floating'
    elif 'rss' in desc_lower:
        desc_kw = 'rss'
    elif 'dcir' in desc_lower:
        desc_kw = 'dcir'
    elif 'rpt' in desc_lower:
        desc_kw = 'rpt'
    elif 'formation' in desc_lower or '화성' in desc_lower:
        desc_kw = 'formation'

    # ⭐ v3 신규: short sampling (record_interval_s < 5)
    short_sampling = any(
        0 < s.get('record_interval_s', 60) < 5 for s in body)

    # ⭐ v3 신규: body 내 mode=1 비율 (active cycling 정도)
    active_steps = [s for s in body
                    if s['type'] in (CHG_TYPES | DCHG_TYPES | {'REST'})]
    n_mode1 = sum(1 for s in active_steps if s.get('mode_flag', 0) == 1)
    mode1_ratio = (n_mode1 / len(active_steps) if active_steps else 0)

    # ============================================================
    # 분류 룰 (v3)
    # ============================================================

    # 1. INIT
    if position == 0 and N == 1:
        if all(s['type'] in (DCHG_TYPES | {'REST'}) for s in body):
            if any(s['type'] in DCHG_TYPES for s in body):
                return 'INIT', ''

    # ⭐ ECT 는 별도 카테고리가 아닌 ACCEL/GITT_PULSE 의 sub_tag 으로 처리.
    # 도메인 검증 (사용자 지적, 260505): ECT-parameter schedule 의 step pattern 은
    # 4-step multi-step charge + 0.5C 부분 DCHG + 60s REST × N=30 cycles =
    # ACCEL 의 정확한 시그니처. 단 chamber 온도가 명시된 점만 차이.
    # → ECT 신규 카테고리 제거. ACCEL/GITT_PULSE 룰의 sub_tag 으로 통합.
    is_ect_signal = (desc_kw == 'ect' or
                     (rest_mode0_chamber_ratio >= 0.5 and short_sampling
                      and len(body) >= 5))

    # 2. GITT_PULSE
    if has_gitt_block and N >= 10:
        sub_parts = ['gitt_block']
        if is_ect_signal:
            sub_parts.append('ect')
        return 'GITT_PULSE', '+'.join(sub_parts)
    max_rest_s = max((s.get('time_limit_s', 0) for s in rest), default=0)
    if N >= 10 and len(body) <= 3 and max_rest_s >= 600:
        non_rest = [s for s in body if s['type'] != 'REST']
        if non_rest and any(s['type'] in (CHG_TYPES | DCHG_TYPES)
                            for s in non_rest):
            sub_parts = []
            if short_sampling:
                sub_parts.append('short_sampling')
            if is_ect_signal:
                sub_parts.append('ect')
            return 'GITT_PULSE', '+'.join(sub_parts)

    # 2b. FLOATING
    if chg and not dchg:
        max_chg_time = max((s.get('time_limit_s', 0) for s in chg), default=0)
        has_v_cut = any(s.get('voltage_mV', 0) > 0 for s in chg)
        if max_chg_time >= 43200 and has_v_cut:
            sub = ''
            if all(s['type'] == 'CHG_CCCV' for s in chg):
                sub = 'cccv'
            elif all(s['type'] == 'CHG_CC' for s in chg):
                sub = 'cc'
            return 'FLOATING', sub

    # 3. ACCEL — 기존 N≥20 strong 룰 유지 (SOC_DCIR 와 disambiguate 위해)
    if N >= 20 and len(chg) >= 2 and dchg:
        sub_parts = []
        if len(chg) >= 3:
            sub_parts.append('multi_step')
        if is_ect_signal:
            sub_parts.append('ect')   # ⭐ ECT-parameter 의 chamber-controlled cycling
        return 'ACCEL', '+'.join(sub_parts)

    # ⭐ 3c. RSS_DCIR — 도메인 정확성 (긴 DCHG = 정상상태) + cluster sub_tag
    # 도메인 분리:
    #   - RSS_DCIR  = 긴 DCHG (정상상태 도달, 확산 포함)
    #   - PULSE_DCIR = 짧은 DCHG (≤30s 펄스, 정상상태 미도달)
    # → not has_short_dchg 조건 = RSS 만 잡고 PULSE 는 §7 에서 매칭
    if (N == 1 and has_ec and len(dchg) >= 4 and len(body) >= 10
            and not has_short_dchg):
        ref_steps_dchg = {
            s.get('end_condition', {}).get('ref_step_number', 0)
            for s in ec_on_dchg
            if s.get('end_condition', {}).get('ref_step_number', 0) > 0
        }
        sub_parts = []
        if len(ref_steps_dchg) >= 2:
            sub_parts.append('multi_cluster')
        if desc_kw == 'rss':
            sub_parts.append('desc_kw')
        return 'RSS_DCIR', '+'.join(sub_parts)

    # ⭐ 4. HYSTERESIS_DCHG — ref_step 일반화 (Phase 0-5-α)
    # v2: ec_type == 2048 (ref_step=8 만 매칭)
    # v3: ref_step ≠ 0 (임의 ref_step 매칭) — 단 N=1 + DCHG + no short pulse 유지
    if (N == 1 and not has_short_dchg and has_ref_step_dchg):
        sub = 'desc_kw' if desc_kw == 'hysteresis' else ''
        return 'HYSTERESIS_DCHG', sub

    # ⭐ 5. HYSTERESIS_CHG — ref_step 일반화
    if (N == 1 and not has_short_chg and has_ref_step_chg):
        sub = 'desc_kw' if desc_kw == 'hysteresis' else ''
        return 'HYSTERESIS_CHG', sub

    # 6. SOC_DCIR (ACCEL N=11~19 mid_life 보다 먼저 — disambiguate)
    if 5 <= N < 20 and len(ec_steps) >= 4 and len(body) >= 8:
        ec_type_set = {s.get('end_condition', {}).get('type', 0)
                       for s in ec_steps}
        if len(ec_type_set) >= 3:
            return 'SOC_DCIR', ''

    # ⭐ 7. PULSE_DCIR — v2 순서 보존 (PULSE 가 RSS 보다 먼저)
    # 도메인: PULSE = 짧은 DCHG (≤30s) 펄스. RSS = 긴 DCHG + 긴 REST (정상상태).
    # v3 신규 sub_tag: dchg_cccv_pulse (mode_flag 활용)
    if has_ec and has_short_dchg and len(dchg) >= 2 and len(body) >= 5:
        sub_tags = []
        if short_sampling:
            sub_tags.append('short_sampling')
        if has_dchg_cccv_pulse:
            sub_tags.append('dchg_cccv_pulse')  # ⭐ v3 신규
        return 'PULSE_DCIR', '+'.join(sub_tags)

    # ⭐ 7b. PULSE_DCIR (강한 hint) — DCHG_CCCV mode=0 단독으로도 식별
    if has_dchg_cccv_pulse and len(dchg) >= 2:
        return 'PULSE_DCIR', 'dchg_cccv_pulse'

    # 8. RSS_DCIR fallback (이미 §3c 에서 처리되었으므로 도달 거의 없음)
    if N == 1 and has_ec and len(dchg) >= 4 and len(body) >= 10:
        return 'RSS_DCIR', 'fallback'

    # ⭐ 3b. ACCEL mid_life — N=11~19 multi-step charge (Phase 0-5-α gap fix)
    # SOC_DCIR / PULSE_DCIR / RSS_DCIR 룰 이후 처리하여 disambiguate.
    if 11 <= N <= 19 and len(chg) >= 3 and dchg:
        sub_parts = ['mid_life']
        if is_ect_signal:
            sub_parts.append('ect')
        return 'ACCEL', '+'.join(sub_parts)

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

    # 12. FORMATION (N=2~10, CHG+DCHG) — v2 와 동일 보존
    if 2 <= N <= 10 and chg and dchg:
        sub = 'ect' if is_ect_signal else ''
        return 'FORMATION', sub

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


# ===========================================================
# 4. Per-folder capacity extraction
# ===========================================================
_CAP_PATTERNS = [
    re.compile(r'(\d+)\s*mAh', re.IGNORECASE),
]


def extract_capacity_from_name(name: str) -> float:
    for pat in _CAP_PATTERNS:
        m = pat.search(name)
        if m:
            try:
                v = float(m.group(1))
                if 100 <= v <= 100000:
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
    print(f"Found {len(sch_files)} .sch files", file=sys.stderr)

    file_rows: list[dict] = []
    group_rows: list[dict] = []
    failed_files: list[str] = []

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
        test_cat = parts[0] if parts else 'UNKNOWN'
        exp_folder = parts[1] if len(parts) >= 2 else parts[0]

        parsed = parse_pne_sch_v3(sch_path)
        if parsed is None:
            failed_files.append(rel_str)
            continue

        header = parsed['header']
        desc = header.get('schedule_description', '')
        capacity_mAh = extract_capacity_from_name(exp_folder)
        if capacity_mAh == 0:
            capacity_mAh = extract_capacity_from_name(desc)
        if capacity_mAh == 0:
            for s in parsed['steps']:
                cl = s.get('capacity_limit_mAh', 0)
                if cl and cl > 0:
                    capacity_mAh = cl
                    break

        intervals = [s.get('record_interval_s', 0) for s in parsed['steps']
                     if s.get('record_interval_s', 0) > 0]
        chambers = [s.get('chamber_temp_c', 0) for s in parsed['steps']
                    if s.get('chamber_temp_c', 0) != 0]
        first_iv = intervals[0] if intervals else 0
        first_chamber = chambers[0] if chambers else 0

        groups = decompose_loop_groups(parsed['steps'])
        expanded = expand_with_outer_goto(groups)

        tc = 1
        n_total_groups = len(expanded)
        per_file_cats: Counter = Counter()

        for gi, g in enumerate(expanded):
            n = max(g['loop_count'], 1)
            cat, sub = classify_loop_group_v3(
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

            n_chg = len([s for s in g['body'] if s['type'] in CHG_TYPES])
            n_dchg = len([s for s in g['body'] if s['type'] in DCHG_TYPES])
            n_rest = len([s for s in g['body'] if s['type'] == 'REST'])

            # ref_step values used in body
            ref_steps_used = sorted({
                s.get('end_condition', {}).get('ref_step_number', 0)
                for s in g['body']
                if s.get('end_condition', {}).get('ref_step_number', 0) > 0
            })

            # mode_flag stats in body
            active_steps_b = [s for s in g['body']
                              if s['type'] in (CHG_TYPES | DCHG_TYPES | {'REST'})]
            n_mode1_body = sum(1 for s in active_steps_b
                               if s.get('mode_flag', 0) == 1)
            mode1_pct = (n_mode1_body / len(active_steps_b) * 100
                         if active_steps_b else 0)

            n_dchg_cccv_m0 = sum(
                1 for s in g['body']
                if s['type'] == 'DCHG_CCCV' and s.get('mode_flag', 0) == 0)

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
                'ref_steps_used': ';'.join(str(r) for r in ref_steps_used),
                'mode1_pct': round(mode1_pct, 1),
                'n_dchg_cccv_mode0': n_dchg_cccv_m0,
                'chamber_c': first_chamber,
            }
            group_rows.append(row)
            cat_global[cat] += 1
            cat_by_test[test_cat][cat] += 1
            per_file_cats[cat] += 1
            tc += n

        folders_by_test[test_cat].add(exp_folder)
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
            'category_summary': cat_summary,
        })

    # ===== Output =====
    groups_csv = OUT_DIR / 'sch_phase0_5_v3_groups.csv'
    with open(groups_csv, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(group_rows[0].keys()))
        writer.writeheader()
        writer.writerows(group_rows)
    print(f"Wrote {groups_csv} ({len(group_rows)} groups)", file=sys.stderr)

    files_csv = OUT_DIR / 'sch_phase0_5_v3_files.csv'
    with open(files_csv, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(file_rows[0].keys()))
        writer.writeheader()
        writer.writerows(file_rows)
    print(f"Wrote {files_csv}", file=sys.stderr)

    # Summary
    md = []
    md.append('# Phase 0-5 v3 분류기 — 187 폴더 / 368 .sch 결과')
    md.append('')
    md.append(f'- .sch 파일: **{len(sch_files)}** (parsed {len(file_rows)}, '
              f'failed {len(failed_files)})')
    md.append(f'- 총 loop group: **{len(group_rows)}**')
    md.append('')
    md.append('## 카테고리 분포 (v3)')
    md.append('')
    md.append('| Category | count | 비율 |')
    md.append('|---|---|---|')
    total = sum(cat_global.values())
    for c, n in cat_global.most_common():
        md.append(f'| {c} | {n} | {n/total*100:.1f}% |')
    md.append('')

    md.append('## 시험종류 × 카테고리 cross-table')
    md.append('')
    cat_order = [c for c, _ in cat_global.most_common()]
    md.append('| 시험종류 | 폴더 | 파일 | TC총수 | ' +
              ' | '.join(cat_order) + ' |')
    md.append('|' + '---|' * (4 + len(cat_order)))
    for tc_name in sorted(folders_by_test.keys()):
        n_folders = len(folders_by_test[tc_name])
        n_files = sum(1 for r in file_rows if r['test_category'] == tc_name)
        n_tc = sum(r['total_tc'] for r in file_rows
                   if r['test_category'] == tc_name)
        cells = [str(cat_by_test[tc_name].get(c, 0)) for c in cat_order]
        md.append(f'| {tc_name} | {n_folders} | {n_files} | {n_tc} | ' +
                  ' | '.join(cells) + ' |')
    md.append('')

    with open(OUT_DIR / 'sch_phase0_5_v3_summary.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    print(f"Wrote summary md", file=sys.stderr)
    print('Done.', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
