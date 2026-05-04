"""PNE 패턴 CSV (CTSEditor export) ↔ .sch binary cross-check.

각 CSV 의 [Schedule] / [Safety Condition] / [Step] 섹션을 파싱하고,
매칭되는 .sch 파일의 binary parse 결과와 비교하여
22 카테고리 분류기의 ground truth 검증.

Usage:
    python sch_csv_crosscheck.py
"""
from __future__ import annotations

import re
import struct
import sys
from pathlib import Path

CSV_DIR = Path(r"C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\pattern")
EXP_ROOT = Path(r"C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data")

# 사용자가 제공한 매칭 (CSV name → .sch path or folder)
USER_MAPPING = [
    {
        'csv': 'Gen5+B 2335mAh 2C Si Hybrid 상온 RT.csv',
        'sch': r'수명\251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202',  # folder
    },
    {
        'csv': 'Ref_Gen5+B 2335 mAh 2C Si Hybrid 상온.csv',
        'sch': r'수명\251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202',
    },
    {
        'csv': 'Ref_4.53V_Si_5000mAh 0.2C recovery capacity 4cycle SOC30 setting.csv',
        'sch': r'성능\260109_260112_05_이근준_5000mAh_Gen5P Si5 ATL T2 3M 보관 용량 측정 4cycle SOC 30 setting ch7 to 12\M01Ch007[007]\260109_260112_05_이근준_5000mAh_Gen5P Si5 ATL T2 3M 보관 용량 측정 4cycle SOC 30 setting ch7 to 12.sch',
    },
    {
        'csv': 'Ref_4.55V Floating 2688mAh +120D.csv',
        'sch': r'성능\260112_260312_03_나무늬_2688mAh_Gen5+B SDI MP2 2.0C EPF HT Floating + 120D\M01Ch057[057]\260112_260312_03_나무늬_2688mAh_Gen5+B SDI MP2 2.0C EPF HT Floating + 120D.sch',
    },
    {
        'csv': 'Ref_4.55V_Q8 Sub_2485mAh 2C Rss 2step 방전 3.0V 0-1600cyc SEU4.csv',
        'sch': r'수명\260119_260616_03_홍승기_2485mAh_Q8 ATL Sub 2.0C Rss RT\M02Ch069[069]\260119_260616_03_홍승기_2485mAh_Q8 ATL Sub 2.0C Rss RT.sch',
    },
    {
        'csv': 'Ref_4755mAh_ECT 패턴1 ACT 가변.csv',
        'sch': r'성능\250827_251028_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter1',  # folder
    },
    {
        'csv': 'Ref_5882mAh_ECT 패턴11 GITT.csv',
        'sch': r'성능\260316_270318_00_이성일_5882mAh_M47 ATL ECT GITT\M01Ch005[005]\260316_270318_00_이성일_5882mAh_M47 ATL ECT GITT.sch',
    },
    {
        'csv': 'Ref_LWN 6490mAh Si25P 율별Profile.csv',
        'sch': r'성능\251209_251213_05_현혜정_6490mAh_LWN Si25P SPL 율별방전Profile\M01Ch030[030]\251209_251213_05_현혜정_6490mAh_LWN Si25P SPL 율별방전Profile.sch',
    },
    {
        'csv': 'Ref_SOC별 DCIR 충방전_2610mAh.csv',
        'sch': r'성능\250513_250526_05_나무늬_2610mAh_Gen5+B SDI MP1 Main SBR 0.9 DCIR\M01Ch037[037]\250513_250526_05_나무늬_2610mAh_Gen5+B SDI MP1 Main SBR 0.9 DCIR.sch',
    },
    {
        'csv': 'Ref_율별용량 5075mAh+ hybrid.csv',
        'sch': r'성능\260202_260226_05_문현규_5075mAh_Cosmx 25Si 율별용량+Hybrid ch54\M01Ch054[054]\260202_260226_05_문현규_5075mAh_Cosmx 25Si 율별용량+Hybrid ch54.sch',
    },
]


# ─── CSV parser ───
SECTION_RE = re.compile(r'^\[(\w[\w\s]*)\]$')


def parse_csv(csv_path: Path) -> dict:
    """PNE CSV 파싱."""
    sections = {}
    cur_section = None
    cur_lines = []
    try:
        with open(csv_path, encoding='cp949', errors='replace') as f:
            for line in f:
                line = line.rstrip('\r\n')
                m = SECTION_RE.match(line.strip())
                if m:
                    if cur_section:
                        sections[cur_section] = cur_lines
                    cur_section = m.group(1)
                    cur_lines = []
                else:
                    cur_lines.append(line)
            if cur_section:
                sections[cur_section] = cur_lines
    except Exception as e:
        return {'error': str(e)}

    out = {'_path': str(csv_path), '_sections': list(sections.keys())}

    # Schedule
    sched = {}
    for line in sections.get('Schedule', []):
        if ',' in line:
            k, v = line.split(',', 1)
            sched[k.strip()] = v.strip()
    out['schedule'] = sched

    # Safety Condition
    safety = {}
    for line in sections.get('Safety Condition', []):
        if ',' in line:
            k, v = line.split(',', 1)
            safety[k.strip()] = v.strip()
    out['safety'] = safety

    # Steps
    steps = []
    step_lines = sections.get('Step', [])
    if step_lines:
        # 첫 줄 = header
        header_cols = [c.strip() for c in step_lines[0].split(',')]
        for line in step_lines[1:]:
            if not line.strip():
                continue
            cols = line.split(',')
            row = {}
            for i, col_name in enumerate(header_cols):
                if i < len(cols):
                    row[col_name] = cols[i].strip()
            if row.get('StepNo'):
                steps.append(row)
    out['steps'] = steps
    out['n_steps'] = len(steps)

    # Type 분포
    type_count = {}
    for s in steps:
        t = s.get('Type', '?')
        type_count[t] = type_count.get(t, 0) + 1
    out['type_count'] = type_count

    return out


# ─── .sch parser (lite) ───
HEADER_SIZE = 1920
BLOCK_SIZE = 652


def parse_sch_lite(sch_path: Path) -> dict:
    """sch_dump_lite 의 lite parse 재사용 + step type 분포."""
    try:
        with open(sch_path, 'rb') as f:
            data = f.read()
    except Exception as e:
        return {'error': str(e)}

    if len(data) < HEADER_SIZE + BLOCK_SIZE:
        return {'error': 'too_short'}

    magic = struct.unpack_from('<I', data, 0)[0]
    if magic != 740721:
        return {'error': 'magic_mismatch'}

    n_steps = (len(data) - HEADER_SIZE) // BLOCK_SIZE

    # Step type 분포
    sch_type_map = {
        0x0101: 'CHG_CCCV', 0x0102: 'DCHG_CCCV',
        0x0201: 'CHG_CC', 0x0202: 'DCHG_CC', 0x0209: 'CHG_CP',
        0xFF03: 'REST', 0xFF06: 'GOTO', 0xFF07: 'REST_SAFE',
        0xFF08: 'LOOP',
        0x0003: 'GITT_PAUSE', 0x0006: 'END',
        0x0007: 'GITT_END', 0x0008: 'GITT_START',
    }
    type_count = {}
    capacity_limit = None
    for i in range(n_steps):
        ofs = HEADER_SIZE + i * BLOCK_SIZE
        type_code = struct.unpack_from('<I', data, ofs + 8)[0]
        type_name = sch_type_map.get(type_code, f'UNK_0x{type_code:04X}')
        type_count[type_name] = type_count.get(type_name, 0) + 1
        if capacity_limit is None and type_code in (0x0101, 0x0102, 0x0201, 0x0202, 0x0209):
            capacity_limit = round(struct.unpack_from('<f', data, ofs + 104)[0], 1)

    return {
        '_path': str(sch_path),
        'n_steps': n_steps,
        'type_count': type_count,
        'capacity_limit_mAh': capacity_limit,
    }


def find_first_sch(p: Path) -> Path | None:
    """파일이면 그대로, 폴더면 첫 .sch 찾기."""
    if p.is_file():
        return p
    if p.is_dir():
        files = sorted(p.rglob('*.sch'))
        return files[0] if files else None
    return None


# ─── Cross-check ───
def crosscheck(csv_data: dict, sch_data: dict) -> dict:
    """CSV vs .sch 일치/불일치."""
    diffs = []

    # n_steps 비교 (Loop / Cycle 같은 가상 step 차이로 다를 수 있음)
    csv_n = csv_data.get('n_steps', 0)
    sch_n = sch_data.get('n_steps', 0)
    diffs.append({
        'field': 'n_steps',
        'csv': csv_n,
        'sch': sch_n,
        'match': csv_n == sch_n,
    })

    # Capacity upper (Safety vs +104)
    safety = csv_data.get('safety', {})
    cap_upper_str = safety.get('Capacity upper', '')
    csv_cap_mAh = None
    if cap_upper_str:
        m = re.match(r'([\d.]+)\s*Ah', cap_upper_str)
        if m:
            csv_cap_mAh = round(float(m.group(1)) * 1000, 1)
    sch_cap = sch_data.get('capacity_limit_mAh')
    diffs.append({
        'field': 'capacity_mAh (CSV Capacity upper vs sch +104)',
        'csv': csv_cap_mAh,
        'sch': sch_cap,
        'match': csv_cap_mAh == sch_cap if (csv_cap_mAh and sch_cap) else None,
    })

    return diffs


def main():
    out_lines = []
    out_lines.append("# CSV ↔ .sch Cross-check (Phase 0-1c)")
    out_lines.append("")
    out_lines.append("> 사용자 제공 PNE 패턴 CSV 10개 ↔ .sch 9개 매칭 검증.")
    out_lines.append("")

    for entry in USER_MAPPING:
        csv_name = entry['csv']
        sch_rel = entry['sch']
        csv_path = CSV_DIR / csv_name
        sch_target = EXP_ROOT / sch_rel
        sch_path = find_first_sch(sch_target)

        out_lines.append(f"## {csv_name}")
        out_lines.append("")
        out_lines.append(f"- CSV: `{csv_path}`")
        out_lines.append(f"- .sch target: `{sch_target}`")
        out_lines.append(f"- .sch resolved: `{sch_path}`" if sch_path else f"- ⚠️ .sch NOT FOUND: `{sch_target}`")
        out_lines.append("")

        if not csv_path.exists():
            out_lines.append(f"⚠️ CSV NOT FOUND")
            out_lines.append("")
            continue

        csv_data = parse_csv(csv_path)
        if 'error' in csv_data:
            out_lines.append(f"⚠️ CSV parse error: {csv_data['error']}")
            out_lines.append("")
            continue

        # CSV summary
        sched = csv_data.get('schedule', {})
        safety = csv_data.get('safety', {})
        type_count = csv_data.get('type_count', {})
        out_lines.append(f"**CSV Summary**")
        out_lines.append(f"- Sections: {csv_data.get('_sections')}")
        out_lines.append(f"- Schedule: {dict(sched)}")
        out_lines.append(f"- Safety: {dict(safety)}")
        out_lines.append(f"- Steps n={csv_data['n_steps']}, type_count={dict(type_count)}")
        out_lines.append("")

        if not sch_path or not sch_path.exists():
            out_lines.append("⚠️ .sch 없음 — cross-check skip")
            out_lines.append("")
            continue

        sch_data = parse_sch_lite(sch_path)
        if 'error' in sch_data:
            out_lines.append(f"⚠️ .sch parse error: {sch_data['error']}")
            out_lines.append("")
            continue

        out_lines.append(f"**.sch Summary**")
        out_lines.append(f"- Steps n={sch_data['n_steps']}, type_count={dict(sch_data['type_count'])}")
        out_lines.append(f"- capacity_limit_mAh (+104) = {sch_data['capacity_limit_mAh']}")
        out_lines.append("")

        # Cross-check
        diffs = crosscheck(csv_data, sch_data)
        out_lines.append(f"**Cross-check**")
        out_lines.append(f"")
        out_lines.append(f"| Field | CSV | .sch | Match |")
        out_lines.append(f"|---|---|---|---|")
        for d in diffs:
            mark = '✅' if d['match'] is True else ('❌' if d['match'] is False else '?')
            out_lines.append(f"| {d['field']} | {d['csv']} | {d['sch']} | {mark} |")
        out_lines.append("")
        out_lines.append("---")
        out_lines.append("")

    out_path = Path(__file__).parent / 'sch_csv_crosscheck.md'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out_lines))
    print(f"Wrote {out_path}", file=sys.stderr)


if __name__ == '__main__':
    main()
