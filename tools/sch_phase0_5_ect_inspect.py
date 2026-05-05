"""ECT 분류된 group 의 실제 step pattern 검증 — '단순 긴 REST' 가설 검토."""
from __future__ import annotations

import csv
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

OUT_DIR = Path(__file__).parent
EXP_ROOT = Path(r"C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data")
HEADER_SIZE = 1920
BLOCK_SIZE = 652
V3_GROUPS_CSV = OUT_DIR / 'sch_phase0_5_v3_groups.csv'

SCH_TYPE_MAP: dict[int, str] = {
    0x0101: 'CHG_CCCV', 0x0102: 'DCHG_CCCV',
    0x0201: 'CHG_CC', 0x0202: 'DCHG_CC',
    0x0209: 'CHG_CP',
    0xFF03: 'REST', 0xFF06: 'GOTO', 0xFF07: 'REST_SAFE', 0xFF08: 'LOOP',
    0x0003: 'GITT_PAUSE', 0x0006: 'END',
    0x0007: 'GITT_END', 0x0008: 'GITT_START',
}


def parse_steps(data: bytes) -> list[dict]:
    n = (len(data) - HEADER_SIZE) // BLOCK_SIZE
    steps = []
    for i in range(n):
        ofs = HEADER_SIZE + i * BLOCK_SIZE
        blk = data[ofs:ofs + BLOCK_SIZE]
        type_code = struct.unpack_from('<I', blk, 8)[0]
        type_name = SCH_TYPE_MAP.get(type_code, f'UNK_0x{type_code:04X}')
        s = {
            'idx': i,
            'step_num': struct.unpack_from('<I', blk, 0)[0],
            'type': type_name,
            'i_20': struct.unpack_from('<f', blk, 20)[0],
            't_24': struct.unpack_from('<f', blk, 24)[0],
            'v_28': struct.unpack_from('<f', blk, 28)[0],
            'v_disp': (struct.unpack_from('<f', blk, 12)[0]
                       if 'CHG' in type_name and 'DCHG' not in type_name
                       else struct.unpack_from('<f', blk, 16)[0]),
            'mode_flag': struct.unpack_from('<I', blk, 84)[0],
            'rec_iv': struct.unpack_from('<f', blk, 336)[0],
            'chamber': struct.unpack_from('<f', blk, 396)[0],
        }
        steps.append(s)
    return steps


def main() -> int:
    # 1. v3 ECT groups 추출
    ect_rows = []
    with open(V3_GROUPS_CSV, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if r['category'] == 'ECT':
                ect_rows.append(r)
    print(f"v3 ECT groups: {len(ect_rows)}", file=sys.stderr)

    md = []
    md.append('# ECT 분류 79 group 실제 step pattern 검증')
    md.append('')
    md.append('> 사용자 지적 — "ECT (신규) 는 단순 rest 가 긴 거 아닌가?"')
    md.append('> → ECT 분류된 group 의 body step pattern 을 raw 로 확인하여 검증.')
    md.append('')
    md.append(f'- v3 ECT groups: **{len(ect_rows)}**')
    md.append(f'- unique sch files: **{len(set(r["sch_file"] for r in ect_rows))}**')
    md.append('')

    # 2. ECT group 의 sub_tag, body_size, n_chg/dchg/rest 통계
    md.append('## 1. ECT group 의 body 구성 통계')
    md.append('')
    md.append('| 통계 | 값 |')
    md.append('|---|---|')
    body_sizes = [int(r['body_size']) for r in ect_rows]
    n_chgs = [int(r['n_chg_step']) for r in ect_rows]
    n_dchgs = [int(r['n_dchg_step']) for r in ect_rows]
    n_rests = [int(r['n_rest_step']) for r in ect_rows]
    loop_counts = [int(r['loop_count']) for r in ect_rows]
    md.append(f'| body size | min={min(body_sizes)}, '
              f'mean={mean(body_sizes):.1f}, max={max(body_sizes)} |')
    md.append(f'| n_chg | min={min(n_chgs)}, '
              f'mean={mean(n_chgs):.1f}, max={max(n_chgs)} |')
    md.append(f'| n_dchg | min={min(n_dchgs)}, '
              f'mean={mean(n_dchgs):.1f}, max={max(n_dchgs)} |')
    md.append(f'| n_rest | min={min(n_rests)}, '
              f'mean={mean(n_rests):.1f}, max={max(n_rests)} |')
    md.append(f'| loop_count (N) | min={min(loop_counts)}, '
              f'mean={mean(loop_counts):.1f}, max={max(loop_counts)} |')
    md.append('')

    # body size = 1 + type=REST 체크 ("단순 긴 REST" 케이스)
    pure_rest = []
    for r in ect_rows:
        if int(r['body_size']) == 1 and int(r['n_rest_step']) == 1:
            pure_rest.append(r)
    md.append(f'### "단순 1-step REST" 케이스: **{len(pure_rest)} / {len(ect_rows)}**'
              f' ({len(pure_rest)/len(ect_rows)*100:.0f}%)')
    md.append('')

    # 3. 실제 schedule 의 ECT-classified group body 표시 (대표 5건)
    md.append('## 2. ECT 분류 group 의 실제 body step sequence (대표 sample)')
    md.append('')

    seen_files = set()
    samples = []
    for r in ect_rows:
        if r['sch_file'] in seen_files:
            continue
        seen_files.add(r['sch_file'])
        samples.append(r)
        if len(samples) >= 8:
            break

    for r in samples:
        md.append(f'### {r["sch_file"][:80]}')
        md.append(f'- group_idx={r["group_idx"]}, TC={r["tc_start"]}-{r["tc_end"]}, '
                  f'N={r["loop_count"]}, body={r["body_size"]}, '
                  f'sub_tag={r["sub_tag"]}')
        md.append(f'- desc: {r["schedule_desc"]}')
        md.append(f'- chamber={r["chamber_c"]}°C')
        md.append('')

        # Re-parse 해서 group body 추출
        path = EXP_ROOT / r['rel_path']
        try:
            data = path.read_bytes()
        except OSError:
            md.append('(파일 read 실패)')
            md.append('')
            continue
        all_steps = parse_steps(data)

        # group body 위치: tc_start 가 1-based, body 는 LOOP 직전까지
        # 그냥 tc_start 부터 tc_start + body_size 만큼 표시 (근사)
        # 더 정확하게는 group_idx 기반 LOOP 분할 필요 — 여기선 sample 표시 목적
        body_size = int(r['body_size'])
        # ECT-parameter schedule 의 typical 구조: schedule 시작부터 LOOP 직전까지
        # 정확한 group body 추출: LOOP 기준 분할
        body_start = 0
        body_end = 0
        gi = 0
        for i, s in enumerate(all_steps):
            if s['type'] == 'LOOP':
                if gi == int(r['group_idx']):
                    body_end = i
                    break
                # next group
                gi += 1
                body_start = i + 1
                if (body_start < len(all_steps)
                        and all_steps[body_start]['type'] == 'REST_SAFE'):
                    body_start += 1

        md.append('| step# | type | mode | I (mA) | t (s) | V cut (mV) | '
                  'V disp (mV) | rec_iv | chamber |')
        md.append('|---|---|---|---|---|---|---|---|---|')
        body_steps = [s for s in all_steps[body_start:body_end]
                      if s['type'] not in ('LOOP', 'GOTO', 'REST_SAFE', 'END')]
        for s in body_steps[:25]:
            md.append(f"| {s['step_num']} | {s['type']} | {s['mode_flag']} | "
                      f"{s['i_20']:.0f} | {s['t_24']:.0f} | "
                      f"{s['v_28']:.0f} | {s['v_disp']:.0f} | "
                      f"{s['rec_iv']:.1f} | {s['chamber']:.0f} |")
        if len(body_steps) > 25:
            md.append(f'| ... | (+{len(body_steps) - 25} more) |')
        md.append('')

    # 4. ECT group 의 type_set 분포
    md.append('## 3. ECT group 의 step type 구성 패턴')
    md.append('')
    type_patterns: Counter = Counter()
    rest_only_count = 0
    for r in ect_rows:
        chg = int(r['n_chg_step'])
        dchg = int(r['n_dchg_step'])
        rest = int(r['n_rest_step'])
        body = int(r['body_size'])
        if rest == body and chg == 0 and dchg == 0:
            rest_only_count += 1
            pattern = f'REST only (body={body})'
        else:
            pattern = f'CHG={chg}, DCHG={dchg}, REST={rest}, body={body}'
        type_patterns[pattern] += 1

    md.append('| 패턴 | count |')
    md.append('|---|---|')
    for p, n in type_patterns.most_common(20):
        md.append(f'| {p} | {n} |')
    md.append('')
    md.append(f'### "REST only" group: **{rest_only_count} / {len(ect_rows)}** '
              f'({rest_only_count/len(ect_rows)*100:.0f}%)')
    md.append('')

    # 5. ECT group 의 실제 REST 시간 분포 + chamber 사용
    md.append('## 4. ECT-classified group 들의 LOOP body 내 REST 시간 분포')
    md.append('')
    md.append('실제 .sch 를 parse 해서 ECT 분류된 group 의 REST step 의 t_24 (= 휴지 시간) 분포 dump.')
    md.append('')

    rest_times: list[float] = []
    rest_with_chamber: list[float] = []
    rest_with_short_sampling: list[float] = []
    chg_times: list[float] = []
    dchg_times: list[float] = []

    # group-level: re-parse each ECT file once
    files_done = set()
    for r in ect_rows:
        if r['rel_path'] in files_done:
            continue
        files_done.add(r['rel_path'])
        path = EXP_ROOT / r['rel_path']
        try:
            data = path.read_bytes()
        except OSError:
            continue
        all_steps = parse_steps(data)
        for s in all_steps:
            if s['type'] == 'REST':
                if s['t_24'] > 0:
                    rest_times.append(s['t_24'])
                    if s['chamber'] != 0:
                        rest_with_chamber.append(s['t_24'])
                    if 0 < s['rec_iv'] < 5:
                        rest_with_short_sampling.append(s['t_24'])
            elif s['type'] in ('CHG_CC', 'CHG_CCCV', 'CHG_CP'):
                if s['t_24'] > 0:
                    chg_times.append(s['t_24'])
            elif s['type'] in ('DCHG_CC', 'DCHG_CCCV'):
                if s['t_24'] > 0:
                    dchg_times.append(s['t_24'])

    if rest_times:
        md.append(f'### REST step 시간 (n={len(rest_times)})')
        md.append('')
        md.append('| 통계 | 값 |')
        md.append('|---|---|')
        md.append(f'| 전체 mean | {mean(rest_times):.0f}s = {mean(rest_times)/3600:.1f}h |')
        md.append(f'| 전체 median | {median(rest_times):.0f}s |')
        md.append(f'| 전체 min/max | {min(rest_times):.0f}~{max(rest_times):.0f}s |')
        md.append('')
        md.append('| REST 시간 bucket | count |')
        md.append('|---|---|')
        bins = [(0, 60, '<60s'), (60, 600, '1~10m'), (600, 1800, '10~30m'),
                (1800, 3600, '30m~1h'), (3600, 7200, '1~2h'),
                (7200, 21600, '2~6h'), (21600, 86400, '6~24h'),
                (86400, 99999999, '≥24h')]
        for lo, hi, label in bins:
            c = sum(1 for t in rest_times if lo <= t < hi)
            md.append(f'| {label} | {c} |')
        md.append('')

    md.append(f'- chamber≠0 인 REST step: {len(rest_with_chamber)}')
    md.append(f'- short sampling (rec_iv<5) 인 REST step: '
              f'{len(rest_with_short_sampling)}')
    md.append('')

    if chg_times:
        md.append(f'### CHG step 시간 (n={len(chg_times)})')
        md.append(f'- mean: {mean(chg_times):.0f}s, median: {median(chg_times):.0f}s')
        md.append(f'- min/max: {min(chg_times):.0f}~{max(chg_times):.0f}s')
    if dchg_times:
        md.append(f'### DCHG step 시간 (n={len(dchg_times)})')
        md.append(f'- mean: {mean(dchg_times):.0f}s, median: {median(dchg_times):.0f}s')
        md.append(f'- min/max: {min(dchg_times):.0f}~{max(dchg_times):.0f}s')
    md.append('')

    # 6. 결론 hint
    md.append('## 5. 결론 hint')
    md.append('')
    md.append('아래 질문에 대한 답을 위 데이터로 추론:')
    md.append('1. **ECT body 가 REST only 이면** — 사용자 지적 맞음, 단순 긴 휴지')
    md.append('2. **ECT body 가 CHG/DCHG/REST 혼재** — pulse + REST sequence (GITT-like)')
    md.append('3. **ECT body 의 REST 시간 분포** —')
    md.append('   - 일정 (예: 모두 600s) → 표준 protocol')
    md.append('   - 다양 (예: 60s~24h) → 시험 단계별 다른 목적')
    md.append('4. **CHG/DCHG step 이 짧은 (≤30s) 펄스** → DCIR 또는 GITT 변형')
    md.append('5. **CHG/DCHG step 이 긴 (≥1h)** → 일반 cycling 또는 ECT 자체의 measurement')
    md.append('')

    out_md = OUT_DIR / 'ect_inspect.md'
    with open(out_md, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    print(f"Wrote {out_md}", file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
