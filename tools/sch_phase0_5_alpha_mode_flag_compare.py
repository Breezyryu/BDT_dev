"""mode_flag=0 vs 1 — step type 별 V/I/t 분포 비교 + 도메인 추론.

전수 dump CSV 를 step type 별로 sort 하여 mode_flag 의 의미를 추론한다.
"""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median, stdev

OUT_DIR = Path(__file__).parent
INPUT_CSV = OUT_DIR / 'mode_flag_step_dump.csv'


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


def histogram(values: list[float], bins: list[tuple[float, float, str]]) -> str:
    """values 를 bin 구간별로 카운트해서 표 형식 반환."""
    out = []
    for lo, hi, label in bins:
        n = sum(1 for v in values if lo <= v < hi)
        out.append(f'{label}={n}')
    return ' | '.join(out)


def stats_summary(values: list[float]) -> str:
    """min/median/mean/max + nonzero count."""
    nz = [v for v in values if v != 0]
    if not nz:
        return f'all 0 (n={len(values)})'
    return (f'n={len(values)}, nz={len(nz)}, '
            f'min={min(nz):.1f}, med={median(nz):.1f}, '
            f'mean={mean(nz):.1f}, max={max(nz):.1f}')


def top_values(values: list[float], n: int = 5, round_digits: int = 0) -> str:
    nz = [round(v, round_digits) for v in values if v != 0]
    if not nz:
        return '(all 0)'
    c = Counter(nz)
    return ', '.join(f'{v:.0f}:{n}' for v, n in c.most_common(n))


def analyze_step_type(rows: list[dict], step_type: str, md: list[str]) -> None:
    """한 step type 에 대해 mode=0 vs mode=1 비교."""
    rows_t = [r for r in rows if r['type'] == step_type]
    if not rows_t:
        return
    rows_1 = [r for r in rows_t if r['mode_flag'] == 1]
    rows_0 = [r for r in rows_t if r['mode_flag'] == 0]
    if not rows_1 or not rows_0:
        return

    md.append(f'## {step_type}')
    md.append(f'')
    md.append(f'- total = {len(rows_t)} (mode=1: **{len(rows_1)}** ({len(rows_1)/len(rows_t)*100:.0f}%),'
              f' mode=0: **{len(rows_0)}** ({len(rows_0)/len(rows_t)*100:.0f}%))')
    md.append(f'')

    # Field 별 비교
    fields = [
        ('v_disp', '+12/+16 V (display)', 0),
        ('i_20', '+20 current (mA)', 0),
        ('t_24', '+24 time (s)', 0),
        ('v_28_end', '+28 V end (mV)', 0),
        ('i_32_end', '+32 I end (mA)', 0),
        ('rec_iv', '+336 rec_iv (s)', 1),
        ('chamber', '+396 chamber (°C)', 0),
    ]
    md.append('### 통계 비교 (mode=1 vs mode=0)')
    md.append('')
    md.append('| field | mode=1 stats | mode=1 top values | mode=0 stats | mode=0 top values |')
    md.append('|---|---|---|---|---|')
    for f, label, digits in fields:
        v1 = [r[f] for r in rows_1]
        v0 = [r[f] for r in rows_0]
        md.append(f'| **{label}** | {stats_summary(v1)} | {top_values(v1, 4, digits)} '
                  f'| {stats_summary(v0)} | {top_values(v0, 4, digits)} |')
    md.append('')

    # EC sub-field
    ec_use_1 = sum(1 for r in rows_1 if r['ec504'] == 1)
    ec_use_0 = sum(1 for r in rows_0 if r['ec504'] == 1)
    md.append(f'- EC enabled (+504=1): mode=1 → {ec_use_1}/{len(rows_1)}'
              f' ({ec_use_1/len(rows_1)*100:.1f}%), '
              f'mode=0 → {ec_use_0}/{len(rows_0)}'
              f' ({ec_use_0/len(rows_0)*100:.1f}%)')
    md.append('')

    # V cutoff histogram (CHG/DCHG types — both mode 비교)
    if 'CHG' in step_type:
        md.append('### +28 V end (mV) histogram — V cutoff 의미 비교')
        md.append('')
        bins = [(0, 1, 'zero'), (1, 3000, '<3000'), (3000, 4000, '3.0~4.0kV'),
                (4000, 4150, '4.0~4.15kV'), (4150, 4250, '4.15~4.25kV'),
                (4250, 4350, '4.25~4.35kV'), (4350, 4450, '4.35~4.45kV'),
                (4450, 4600, '4.45~4.6kV'), (4600, 9999, '≥4.6kV')]
        v1_28 = [r['v_28_end'] for r in rows_1]
        v0_28 = [r['v_28_end'] for r in rows_0]
        md.append(f'- mode=1: {histogram(v1_28, bins)}')
        md.append(f'- mode=0: {histogram(v0_28, bins)}')
        md.append('')

    # +24 time histogram
    md.append('### +24 time (s) histogram')
    md.append('')
    t_bins = [(0, 1, '0'), (1, 30, '1~30s'), (30, 600, '30s~10m'),
              (600, 3600, '10m~1h'), (3600, 43200, '1h~12h'),
              (43200, 9999999, '≥12h')]
    t1 = [r['t_24'] for r in rows_1]
    t0 = [r['t_24'] for r in rows_0]
    md.append(f'- mode=1: {histogram(t1, t_bins)}')
    md.append(f'- mode=0: {histogram(t0, t_bins)}')
    md.append('')


def analyze_in_file_position(rows: list[dict], md: list[str]) -> None:
    """같은 file 내에서 mode=1 vs 0 의 step 위치 패턴 — schedule 어디에 위치하는가."""
    md.append('## per-file step position 분석')
    md.append('')
    md.append('한 파일 내에서 mode_flag=0 step 의 step_num 분포 — '
              'schedule 시작/끝/중간 어디 위치?')
    md.append('')

    # group rows by file
    by_file: defaultdict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_file[r['sch_file']].append(r)

    # Per-file: mode=0 step 의 normalized position (0.0=시작, 1.0=끝)
    pos_0_normalized: list[float] = []
    pos_1_normalized: list[float] = []
    pos_0_first: Counter = Counter()  # mode=0 의 첫 step 위치
    pos_0_last: Counter = Counter()  # mode=0 의 마지막 step 위치

    for sch, frows in by_file.items():
        n_steps = len(frows)
        if n_steps == 0:
            continue
        for r in frows:
            norm = r['step_idx'] / max(n_steps - 1, 1)
            if r['mode_flag'] == 0:
                pos_0_normalized.append(norm)
            elif r['mode_flag'] == 1:
                pos_1_normalized.append(norm)

    bins = [(0.0, 0.1, '0~10%'), (0.1, 0.3, '10~30%'),
            (0.3, 0.7, '30~70%'), (0.7, 0.9, '70~90%'),
            (0.9, 1.01, '90~100%')]
    md.append('### Step normalized position (시작=0, 끝=1) 분포')
    md.append('')
    md.append(f'- mode=1 (n={len(pos_1_normalized)}): {histogram(pos_1_normalized, bins)}')
    md.append(f'- mode=0 (n={len(pos_0_normalized)}): {histogram(pos_0_normalized, bins)}')
    md.append('')


def analyze_active_vs_passive_hypothesis(rows: list[dict], md: list[str]) -> None:
    """가설: mode=1 = active step (loop body 내 실제 측정), mode=0 = boundary/passive.

    검증: schedule 내 LOOP step 직전 step 의 mode_flag 분포.
    """
    md.append('## "loop body vs boundary" 가설 검증')
    md.append('')
    md.append('가설: mode=1 = 반복 사이클 내부 (loop body), '
              'mode=0 = setup/boundary (LOOP/GOTO/REST_SAFE 인근, schedule init/end)')
    md.append('')

    by_file: defaultdict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_file[r['sch_file']].append(r)

    # 각 step 의 "직후 step 이 LOOP 인지" 또는 "직전 step 이 REST_SAFE 인지"
    n_before_loop_mode: Counter = Counter()
    n_after_rest_safe_mode: Counter = Counter()
    n_first_step_mode: Counter = Counter()
    n_last_step_mode: Counter = Counter()
    n_in_body_mode: Counter = Counter()  # not boundary

    for sch, frows in by_file.items():
        for i, r in enumerate(frows):
            mode = r['mode_flag']
            if i == 0:
                n_first_step_mode[mode] += 1
            if i == len(frows) - 1:
                n_last_step_mode[mode] += 1
            # before LOOP
            if i + 1 < len(frows) and frows[i + 1]['type'] == 'LOOP':
                n_before_loop_mode[mode] += 1
            # after REST_SAFE
            if i > 0 and frows[i - 1]['type'] == 'REST_SAFE':
                n_after_rest_safe_mode[mode] += 1
            # body step (not LOOP/GOTO/REST_SAFE/END, not first/last)
            if (r['type'] not in ('LOOP', 'GOTO', 'REST_SAFE', 'END')
                    and i not in (0, len(frows) - 1)):
                n_in_body_mode[mode] += 1

    md.append('| 위치 컨텍스트 | mode=0 | mode=1 | mode=257 |')
    md.append('|---|---|---|---|')
    md.append(f'| schedule 첫 step | {n_first_step_mode[0]} | '
              f'{n_first_step_mode[1]} | {n_first_step_mode[257]} |')
    md.append(f'| schedule 마지막 step | {n_last_step_mode[0]} | '
              f'{n_last_step_mode[1]} | {n_last_step_mode[257]} |')
    md.append(f'| LOOP 직전 step | {n_before_loop_mode[0]} | '
              f'{n_before_loop_mode[1]} | {n_before_loop_mode[257]} |')
    md.append(f'| REST_SAFE 직후 step | {n_after_rest_safe_mode[0]} | '
              f'{n_after_rest_safe_mode[1]} | {n_after_rest_safe_mode[257]} |')
    md.append(f'| 일반 body step | {n_in_body_mode[0]} | '
              f'{n_in_body_mode[1]} | {n_in_body_mode[257]} |')
    md.append('')


def analyze_v28_pattern(rows: list[dict], md: list[str]) -> None:
    """CHG_CC mode=1 vs 0 의 V cutoff 패턴 — multi-step charge 의미."""
    md.append('## CHG_CC: mode=1 의 V cutoff 가 multi-step charge 인지 검증')
    md.append('')
    md.append('가설: mode=1 = multi-step charge intermediate (4.14/4.16/4.30/4.55V 점진적), '
              'mode=0 = standard cutoff (4.30/4.55V 단일)')
    md.append('')

    chg_cc_1 = [r for r in rows if r['type'] == 'CHG_CC' and r['mode_flag'] == 1]
    chg_cc_0 = [r for r in rows if r['type'] == 'CHG_CC' and r['mode_flag'] == 0]

    # +28 (V end) — round to 10mV
    md.append('### CHG_CC +28 V end value top 15')
    md.append('')
    md.append('| value (mV) | mode=1 count | mode=0 count |')
    md.append('|---|---|---|')
    v1 = Counter(round(r['v_28_end'] / 10) * 10 for r in chg_cc_1 if r['v_28_end'] > 0)
    v0 = Counter(round(r['v_28_end'] / 10) * 10 for r in chg_cc_0 if r['v_28_end'] > 0)
    all_keys = sorted(set(v1.keys()) | set(v0.keys()),
                       key=lambda v: -(v1[v] + v0[v]))
    for v in all_keys[:15]:
        md.append(f'| {v} | {v1[v]} | {v0[v]} |')
    md.append('')

    # I (+20)
    md.append('### CHG_CC +20 current (mA) top 10')
    md.append('')
    md.append('| value (mA) | mode=1 count | mode=0 count |')
    md.append('|---|---|---|')
    i1 = Counter(round(r['i_20'] / 10) * 10 for r in chg_cc_1 if r['i_20'] > 0)
    i0 = Counter(round(r['i_20'] / 10) * 10 for r in chg_cc_0 if r['i_20'] > 0)
    all_keys = sorted(set(i1.keys()) | set(i0.keys()),
                       key=lambda v: -(i1[v] + i0[v]))
    for v in all_keys[:10]:
        md.append(f'| {v} | {i1[v]} | {i0[v]} |')
    md.append('')


def analyze_rest_pattern(rows: list[dict], md: list[str]) -> None:
    """REST mode=1 vs 0 — 짧은 휴지 (cluster 내) vs 긴 휴지 (cluster 종료)."""
    md.append('## REST: mode=1 짧은 vs mode=0 긴 휴지 가설')
    md.append('')

    rest_1 = [r for r in rows if r['type'] == 'REST' and r['mode_flag'] == 1]
    rest_0 = [r for r in rows if r['type'] == 'REST' and r['mode_flag'] == 0]

    md.append('### REST +24 time (s) 분포 cross')
    md.append('')
    md.append('| time bucket | mode=1 | mode=0 |')
    md.append('|---|---|---|')
    bins = [(0, 60, '0~60s'), (60, 600, '1~10m'), (600, 1800, '10~30m'),
            (1800, 3600, '30m~1h'), (3600, 43200, '1~12h'),
            (43200, 86400, '12~24h'), (86400, 9999999, '≥24h')]
    for lo, hi, label in bins:
        n1 = sum(1 for r in rest_1 if lo <= r['t_24'] < hi)
        n0 = sum(1 for r in rest_0 if lo <= r['t_24'] < hi)
        md.append(f'| {label} | {n1} | {n0} |')
    md.append('')

    md.append('### REST chamber 온도 사용 (+396 비0)')
    md.append('')
    n1_chamber = sum(1 for r in rest_1 if r['chamber'] != 0)
    n0_chamber = sum(1 for r in rest_0 if r['chamber'] != 0)
    md.append(f'- mode=1: {n1_chamber}/{len(rest_1)} ({n1_chamber/len(rest_1)*100:.1f}%) chamber 명시')
    md.append(f'- mode=0: {n0_chamber}/{len(rest_0)} ({n0_chamber/len(rest_0)*100:.1f}%) chamber 명시')
    md.append('')
    md.append('→ chamber 명시 = 시험 환경 control 필요한 보관/대기 step (= longer rest)')
    md.append('')


def main() -> int:
    rows = load_rows()
    print(f"Loaded {len(rows)} rows", file=sys.stderr)

    md = []
    md.append('# mode_flag=0 vs 1 — V/I/t 분포 정밀 비교')
    md.append('')
    md.append(f'- Source: `{INPUT_CSV.name}` ({len(rows)} step rows)')
    md.append('')

    # Active types — mode 의미 차이가 가장 큼
    for t in ['CHG_CC', 'CHG_CCCV', 'CHG_CP', 'DCHG_CC', 'DCHG_CCCV',
              'REST', 'REST_SAFE', 'LOOP', 'GOTO', 'GITT_START']:
        analyze_step_type(rows, t, md)

    analyze_v28_pattern(rows, md)
    analyze_rest_pattern(rows, md)
    analyze_in_file_position(rows, md)
    analyze_active_vs_passive_hypothesis(rows, md)

    out_md = OUT_DIR / 'mode_flag_compare.md'
    with open(out_md, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    print(f"Wrote {out_md}", file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
