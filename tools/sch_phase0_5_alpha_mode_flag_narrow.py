"""mode_flag 가설을 더 좁혀서 검증 — schedule_description × step type × mode 3-way + sequence patterns.

추가 검증:
  H1: schedule_description keyword × step type × mode 3-way 매트릭스
  H2: CHG_CC mode=1 = multi-step charge intermediate → 같은 file 내 연속 4.14→4.16→4.30→4.55 패턴
  H3: TERMINATION 마지막 step (mode=0 93%) 의 type 분포
  H4: DCHG_CCCV mode=0 (100% EC) 의 schedule keyword 분포
  H5: REST mode=0 + chamber≠0 의 schedule keyword 분포 (보관/대기 가설)
  H6: schedule body 내 mode=1 step 수 vs LOOP loop_count 상관 (cycling step 가설)
  H7: mode=257 6건 full context (sch_file 별 step 1 전후 sequence)
"""
from __future__ import annotations

import csv
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

OUT_DIR = Path(__file__).parent
INPUT_CSV = OUT_DIR / 'mode_flag_step_dump.csv'
EXP_ROOT = Path(r"C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data")
HEADER_SIZE = 1920
BLOCK_SIZE = 652


def load_rows() -> list[dict]:
    rows = []
    with open(INPUT_CSV, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            r['mode_flag'] = int(r['mode_flag'])
            for k in ('step_idx', 'step_num', 'ec500', 'ec504'):
                r[k] = int(r[k])
            for k in ('v_disp', 'i_20', 't_24', 'v_28_end',
                      'i_32_end', 'rec_iv', 'chamber'):
                r[k] = float(r[k])
            rows.append(r)
    return rows


# Schedule description → keyword (확장 분류)
def classify_keyword(desc: str) -> str:
    d = desc.lower()
    # Order matters — 먼저 매치되는 것 선택
    if 'rss' in d:
        return 'rss'
    if 'hysteresis' in d:
        return 'hysteresis'
    if 'gitt' in d:
        return 'gitt'
    if 'ect' in d:
        return 'ect'
    if 'floating' in d or '120d' in d or '280day' in d:
        return 'floating'
    if 'soc' in d.replace(' ', '') and 'dcir' in d:
        return 'soc_dcir'
    if 'dcir' in d:
        return 'dcir'
    if 'rpt' in d:
        return 'rpt'
    if 'formation' in d or '화성' in d:
        return 'formation'
    if 'si hybrid' in d or 'si_hybrid' in d:
        return 'accel_si'
    if 'seu' in d:
        return 'accel_seu'
    return 'other'


def main() -> int:
    rows = load_rows()
    for r in rows:
        r['kw'] = classify_keyword(r['desc'])
    print(f"Loaded {len(rows)} rows", file=sys.stderr)

    md = []
    md.append('# mode_flag 좁힌 가설 검증 — schedule keyword × step type × mode')
    md.append('')
    md.append(f'- Source: `mode_flag_step_dump.csv` ({len(rows)} step rows)')
    md.append('')

    # ===== H1: keyword × step_type × mode 3-way matrix =====
    md.append('## H1 — keyword × step_type × mode_flag 3-way 매트릭스')
    md.append('')
    md.append('각 (keyword, step_type) 조합에서 mode=0/1/257 비율. '
              'mode_flag 이 시험 유형별로 어떻게 분기되는지 직접 가시화.')
    md.append('')

    # Group by (keyword, step_type)
    cube: defaultdict[tuple, Counter] = defaultdict(Counter)
    for r in rows:
        cube[(r['kw'], r['type'])][r['mode_flag']] += 1

    # 주요 step type 만 출력
    main_types = ['CHG_CC', 'CHG_CCCV', 'DCHG_CC', 'DCHG_CCCV', 'CHG_CP',
                  'REST', 'REST_SAFE', 'LOOP', 'GOTO']
    keywords = sorted(set(r['kw'] for r in rows))

    for t in main_types:
        md.append(f'### {t}')
        md.append('')
        md.append('| keyword | total | mode=0 | mode=1 | mode=257 | mode=1 비율 |')
        md.append('|---|---|---|---|---|---|')
        for kw in keywords:
            c = cube.get((kw, t), Counter())
            tot = sum(c.values())
            if tot == 0:
                continue
            m0 = c.get(0, 0)
            m1 = c.get(1, 0)
            m257 = c.get(257, 0)
            md.append(f'| {kw} | {tot} | {m0} | {m1} | {m257} | '
                      f'{m1/tot*100:.0f}% |')
        md.append('')

    # ===== H2: CHG_CC mode=1 multi-step sequence 검증 =====
    md.append('## H2 — CHG_CC mode=1 = multi-step charge intermediate 검증')
    md.append('')
    md.append('가설: 같은 schedule 내에서 mode=1 CHG_CC step 이 연속하여 V_end 가 점진적으로 증가.')
    md.append('검증 방법: file 내 CHG_CC step (idx 순서대로) 추출 → V_end sequence 패턴 분석.')
    md.append('')

    by_file: defaultdict[str, list[dict]] = defaultdict(list)
    for r in rows:
        if r['type'] == 'CHG_CC':
            by_file[r['sch_file']].append(r)

    multi_step_files: list[tuple[str, list[float], list[int]]] = []
    single_step_files: list[tuple[str, list[float], list[int]]] = []
    for sch, chg_rows in by_file.items():
        chg_rows.sort(key=lambda r: r['step_idx'])
        v_seq = [r['v_28_end'] for r in chg_rows if r['v_28_end'] > 0]
        m_seq = [r['mode_flag'] for r in chg_rows if r['v_28_end'] > 0]
        if len(v_seq) >= 3:
            # Check if monotone increasing (multi-step pattern)
            increasing = all(v_seq[i] <= v_seq[i+1] for i in range(len(v_seq)-1))
            if increasing and len(set(v_seq)) >= 2:
                multi_step_files.append((sch, v_seq, m_seq))
        elif len(v_seq) >= 1:
            single_step_files.append((sch, v_seq, m_seq))

    md.append(f'- multi-step pattern 검출 file (≥3 CHG_CC, V_end 단조증가): '
              f'**{len(multi_step_files)}** files')
    md.append(f'- single/short pattern files (≤2 CHG_CC): {len(single_step_files)} files')
    md.append('')
    md.append('### multi-step sample 10 — V_end sequence + mode_flag sequence')
    md.append('')
    md.append('| sch | n_chg_cc | V_end sequence | mode sequence |')
    md.append('|---|---|---|---|')
    for sch, vs, ms in multi_step_files[:15]:
        v_str = ' → '.join(f'{int(v)}' for v in vs)
        m_str = ' → '.join(str(m) for m in ms)
        md.append(f'| {sch[:50]} | {len(vs)} | {v_str} | {m_str} |')
    md.append('')

    # Aggregate: mode=1 적용 빈도 in multi-step pattern
    md.append('### multi-step file 의 첫/마지막 CHG_CC 의 mode_flag')
    md.append('')
    first_mode: Counter = Counter()
    last_mode: Counter = Counter()
    middle_mode: Counter = Counter()  # 첫/마지막 제외 중간
    for sch, vs, ms in multi_step_files:
        if not ms:
            continue
        first_mode[ms[0]] += 1
        last_mode[ms[-1]] += 1
        for m in ms[1:-1]:
            middle_mode[m] += 1
    md.append(f'- 첫 CHG_CC mode: {dict(first_mode)}')
    md.append(f'- 마지막 CHG_CC mode: {dict(last_mode)}')
    md.append(f'- 중간 CHG_CC mode: {dict(middle_mode)}')
    md.append('')

    # ===== H3: TERMINATION 마지막 step 분석 =====
    md.append('## H3 — schedule 마지막 step (mode=0 93%) type 분포 검증')
    md.append('')
    md.append('가설: 마지막 step 이 mode=0 인 것은 TERMINATION (사이클 외부) 표시.')
    md.append('')

    by_file_all: defaultdict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_file_all[r['sch_file']].append(r)

    last_type_mode: defaultdict[str, Counter] = defaultdict(Counter)
    last_kw_mode: defaultdict[str, Counter] = defaultdict(Counter)
    for sch, frows in by_file_all.items():
        if not frows:
            continue
        frows.sort(key=lambda r: r['step_idx'])
        last = frows[-1]
        last_type_mode[last['type']][last['mode_flag']] += 1
        last_kw_mode[last['kw']][last['mode_flag']] += 1

    md.append('### 마지막 step type × mode_flag')
    md.append('')
    md.append('| type | mode=0 | mode=1 | total |')
    md.append('|---|---|---|---|')
    for t, c in sorted(last_type_mode.items(),
                        key=lambda x: -sum(x[1].values())):
        tot = sum(c.values())
        md.append(f'| {t} | {c.get(0, 0)} | {c.get(1, 0)} | {tot} |')
    md.append('')

    md.append('### 마지막 step keyword × mode_flag')
    md.append('')
    md.append('| keyword | mode=0 | mode=1 | total |')
    md.append('|---|---|---|---|')
    for kw, c in sorted(last_kw_mode.items(), key=lambda x: -sum(x[1].values())):
        tot = sum(c.values())
        md.append(f'| {kw} | {c.get(0, 0)} | {c.get(1, 0)} | {tot} |')
    md.append('')

    # ===== H4: DCHG_CCCV mode=0 (DCIR pulse) keyword 분포 =====
    md.append('## H4 — DCHG_CCCV mode=0 (100% EC enabled) = DCIR pulse 검증')
    md.append('')
    md.append('가설: DCHG_CCCV mode=0 (모두 ref-step 사용) 은 DCIR pulse measurement.')
    md.append('')
    md.append('### DCHG_CCCV mode 별 schedule keyword 분포')
    md.append('')
    md.append('| keyword | mode=0 | mode=1 |')
    md.append('|---|---|---|')
    dcccv_kw: defaultdict[str, Counter] = defaultdict(Counter)
    for r in rows:
        if r['type'] == 'DCHG_CCCV':
            dcccv_kw[r['kw']][r['mode_flag']] += 1
    for kw, c in sorted(dcccv_kw.items(), key=lambda x: -sum(x[1].values())):
        md.append(f'| {kw} | {c.get(0, 0)} | {c.get(1, 0)} |')
    md.append('')

    # DCHG_CCCV mode=0 의 file 별 desc dump
    md.append('### DCHG_CCCV mode=0 step 의 file + desc (전수 31 step)')
    md.append('')
    md.append('| sch | step# | I (mA) | I_end (mA) | desc |')
    md.append('|---|---|---|---|---|')
    for r in rows:
        if r['type'] == 'DCHG_CCCV' and r['mode_flag'] == 0:
            md.append(f"| {r['sch_file'][:60]} | {r['step_num']} | "
                      f"{r['i_20']:.0f} | {r['i_32_end']:.0f} | {r['desc'][:40]} |")
    md.append('')

    # ===== H5: REST mode=0 + chamber 사용 keyword =====
    md.append('## H5 — REST mode=0 + chamber≠0 의 keyword 분포 (보관/대기 가설)')
    md.append('')
    md.append('가설: chamber ≠ 0 인 REST mode=0 = 환경 control 필요한 보관/대기 step (= ECT/floating).')
    md.append('')
    md.append('### REST mode=0 + chamber≠0 의 keyword 분포 (n=2418)')
    md.append('')
    md.append('| keyword | count | chamber 값 분포 (top 5) |')
    md.append('|---|---|---|')
    rest0_chamber_kw: defaultdict[str, list[float]] = defaultdict(list)
    for r in rows:
        if r['type'] == 'REST' and r['mode_flag'] == 0 and r['chamber'] != 0:
            rest0_chamber_kw[r['kw']].append(r['chamber'])
    for kw, vals in sorted(rest0_chamber_kw.items(), key=lambda x: -len(x[1])):
        c = Counter(round(v) for v in vals)
        top = ', '.join(f'{v}°C:{n}' for v, n in c.most_common(5))
        md.append(f'| {kw} | {len(vals)} | {top} |')
    md.append('')
    md.append('### REST mode=1 (chamber 1.6%만 사용) keyword 분포')
    md.append('')
    md.append('| keyword | count |')
    md.append('|---|---|')
    rest1_kw = Counter(r['kw'] for r in rows
                       if r['type'] == 'REST' and r['mode_flag'] == 1)
    for kw, n in rest1_kw.most_common():
        md.append(f'| {kw} | {n} |')
    md.append('')

    # ===== H6: schedule 의 LOOP body 내 mode=1 step vs loop_count 상관 =====
    md.append('## H6 — LOOP body 내 mode=1 step 수 vs loop_count 상관')
    md.append('')
    md.append('가설: mode=1 step = "사이클 카운트에 인입되는 step". '
              'LOOP loop_count 와 body 내 mode=1 step 의 비율이 의미 있는 패턴 형성.')
    md.append('')

    # Re-parse from .sch directly to get loop_count + body steps
    files = sorted(EXP_ROOT.rglob('*.sch'))
    body_pattern_data: list[dict] = []
    for path in files[:368]:
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if len(data) < HEADER_SIZE + BLOCK_SIZE:
            continue
        if struct.unpack_from('<I', data, 0)[0] != 740721:
            continue
        n = (len(data) - HEADER_SIZE) // BLOCK_SIZE
        # Read schedule_description
        desc_b = data[664:664 + 64]
        end_idx = desc_b.find(b'\x00')
        if end_idx >= 0:
            desc_b = desc_b[:end_idx]
        try:
            desc = desc_b.decode('ascii', errors='replace').strip()
        except Exception:
            desc = ''
        kw = classify_keyword(desc)

        # Walk steps, detect LOOP groups
        body_start = 0
        for i in range(n):
            ofs = HEADER_SIZE + i * BLOCK_SIZE
            type_code = struct.unpack_from('<I', data, ofs + 8)[0]
            if type_code != 0xFF08:  # LOOP
                continue
            loop_count = struct.unpack_from('<I', data, ofs + 56)[0]
            # Body = body_start ~ i-1, exclude REST_SAFE/LOOP/GOTO/END
            mode_counter: Counter = Counter()
            body_size = 0
            for j in range(body_start, i):
                ofs_j = HEADER_SIZE + j * BLOCK_SIZE
                t_j = struct.unpack_from('<I', data, ofs_j + 8)[0]
                if t_j in (0xFF03, 0x0101, 0x0102, 0x0201, 0x0202, 0x0209,
                           0x0003, 0x0006, 0x0007, 0x0008):  # active types
                    m_j = struct.unpack_from('<I', data, ofs_j + 84)[0]
                    mode_counter[m_j] += 1
                    body_size += 1
            if body_size > 0:
                body_pattern_data.append({
                    'sch': path.name,
                    'kw': kw,
                    'loop_count': loop_count,
                    'body_size': body_size,
                    'mode_0': mode_counter.get(0, 0),
                    'mode_1': mode_counter.get(1, 0),
                    'mode_257': mode_counter.get(257, 0),
                    'pct_mode_1': mode_counter.get(1, 0) / body_size * 100,
                })
            # Next body start
            body_start = i + 1

    md.append(f'- 분석한 LOOP body 그룹: {len(body_pattern_data)}')
    md.append('')

    # body 내 mode=1 비율 분포 (per loop_count bucket)
    md.append('### loop_count 구간 별 body 내 mode=1 비율')
    md.append('')
    md.append('| loop_count | n_groups | body 내 mode=1 평균 % | min~max % |')
    md.append('|---|---|---|---|')
    buckets = [(1, 1, 'N=1'), (2, 5, 'N=2~5'), (6, 10, 'N=6~10'),
               (11, 19, 'N=11~19'), (20, 99, 'N=20~99'),
               (100, 999, 'N=100~999'), (1000, 999999, 'N≥1000')]
    for lo, hi, label in buckets:
        bgs = [b for b in body_pattern_data if lo <= b['loop_count'] <= hi]
        if not bgs:
            continue
        avgs = [b['pct_mode_1'] for b in bgs]
        md.append(f'| {label} | {len(bgs)} | {mean(avgs):.1f}% | '
                  f'{min(avgs):.1f}~{max(avgs):.1f}% |')
    md.append('')

    md.append('### keyword × loop_count bucket 별 body 내 mode=1 비율')
    md.append('')
    md.append('| keyword | N=1 | N=2~10 | N=11~19 | N=20~99 | N=100~999 | N≥1000 |')
    md.append('|---|---|---|---|---|---|---|')
    for kw in sorted(set(b['kw'] for b in body_pattern_data)):
        bgs_kw = [b for b in body_pattern_data if b['kw'] == kw]
        cells = []
        for lo, hi, label in [(1, 1, ''), (2, 10, ''), (11, 19, ''),
                               (20, 99, ''), (100, 999, ''), (1000, 999999, '')]:
            bgs = [b for b in bgs_kw if lo <= b['loop_count'] <= hi]
            if not bgs:
                cells.append('-')
            else:
                avg = mean(b['pct_mode_1'] for b in bgs)
                cells.append(f'{avg:.0f}% (n={len(bgs)})')
        md.append(f'| {kw} | ' + ' | '.join(cells) + ' |')
    md.append('')

    # ===== H7: mode=257 6건 full context =====
    md.append('## H7 — mode=257 6건 full sequence context')
    md.append('')
    md.append('가설: bit 8 = "schedule init conditioning step" — '
              '시험 첫 step 의 1초 셀 점검 DCHG.')
    md.append('')

    sch_257 = sorted({r['sch_file'] for r in rows if r['mode_flag'] == 257})
    for sch in sch_257:
        sch_rows = sorted([r for r in rows if r['sch_file'] == sch],
                          key=lambda r: r['step_idx'])
        md.append(f'### {sch[:80]}')
        md.append('')
        # Show first 6 steps
        md.append('| step# | type | mode | I (mA) | t (s) | V (mV) | EC | desc |')
        md.append('|---|---|---|---|---|---|---|---|')
        for r in sch_rows[:6]:
            md.append(f"| {r['step_num']} | {r['type']} | {r['mode_flag']} | "
                      f"{r['i_20']:.0f} | {r['t_24']:.0f} | "
                      f"{r['v_28_end']:.0f} | {r['ec500']} | "
                      f"{r['desc'][:40]} |")
        md.append('')

    # ===== Output =====
    out_md = OUT_DIR / 'mode_flag_narrow.md'
    with open(out_md, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    print(f"Wrote {out_md}", file=sys.stderr)

    return 0


if __name__ == '__main__':
    sys.exit(main())
