"""v2 vs v3 분류 결과 diff — 카테고리별 변동 + 변경 group list."""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

OUT_DIR = Path(__file__).parent
V2_CSV = OUT_DIR / 'sch_phase0_5_groups.csv'
V3_CSV = OUT_DIR / 'sch_phase0_5_v3_groups.csv'


def load(csv_path: Path) -> dict[tuple, dict]:
    """key = (rel_path, group_idx, tc_start, tc_end) → row."""
    rows: dict[tuple, dict] = {}
    with open(csv_path, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            key = (r['rel_path'], int(r['group_idx']),
                   int(r['tc_start']), int(r['tc_end']))
            rows[key] = r
    return rows


def main() -> int:
    v2 = load(V2_CSV)
    v3 = load(V3_CSV)
    print(f"v2: {len(v2)} groups, v3: {len(v3)} groups")
    common_keys = set(v2.keys()) & set(v3.keys())
    print(f"common keys: {len(common_keys)}")

    md = []
    md.append('# v2 vs v3 분류 diff')
    md.append('')
    md.append(f'- v2 groups: {len(v2)}')
    md.append(f'- v3 groups: {len(v3)}')
    md.append(f'- common keys: {len(common_keys)}')
    md.append('')

    # 1. 카테고리 분포 diff
    v2_cats = Counter(r['category'] for r in v2.values())
    v3_cats = Counter(r['category'] for r in v3.values())
    all_cats = sorted(set(v2_cats.keys()) | set(v3_cats.keys()))

    md.append('## 1. 카테고리 분포 diff')
    md.append('')
    md.append('| Category | v2 | v3 | diff | 변동 |')
    md.append('|---|---|---|---|---|')
    for c in sorted(all_cats, key=lambda x: -max(v2_cats.get(x, 0), v3_cats.get(x, 0))):
        n2 = v2_cats.get(c, 0)
        n3 = v3_cats.get(c, 0)
        d = n3 - n2
        sign = '+' if d > 0 else ''
        marker = ''
        if d > 0:
            marker = '↑↑' if d >= 50 else '↑'
        elif d < 0:
            marker = '↓↓' if d <= -50 else '↓'
        if c in ('UNKNOWN', 'EMPTY') and n2 > 0 and n3 == 0:
            marker += ' ✅'
        if c == 'ECT' and n2 == 0 and n3 > 0:
            marker += ' 🆕'
        md.append(f'| {c} | {n2} | {n3} | {sign}{d} | {marker} |')
    md.append('')

    # 2. v2 → v3 transition matrix
    md.append('## 2. v2 → v3 transition matrix (변경된 group 만)')
    md.append('')
    md.append('각 cell = v2 의 카테고리 X 가 v3 에서 카테고리 Y 로 변한 group 수.')
    md.append('')

    transitions: defaultdict[tuple, int] = defaultdict(int)
    for k in common_keys:
        c2 = v2[k]['category']
        c3 = v3[k]['category']
        if c2 != c3:
            transitions[(c2, c3)] += 1

    md.append('| v2 카테고리 → v3 카테고리 | count |')
    md.append('|---|---|')
    for (c2, c3), n in sorted(transitions.items(), key=lambda x: -x[1]):
        md.append(f'| {c2} → **{c3}** | {n} |')
    md.append('')

    # 3. UNKNOWN 추적 (v2 에서 142 group 이 v3 에서 어디로?)
    md.append('## 3. v2 UNKNOWN 142 group → v3 어디로 분류되었는가')
    md.append('')
    unknown_to_v3: defaultdict[str, int] = defaultdict(int)
    unknown_examples: defaultdict[str, list] = defaultdict(list)
    for k in common_keys:
        if v2[k]['category'] == 'UNKNOWN':
            v3_cat = v3[k]['category']
            v3_sub = v3[k].get('sub_tag', '')
            unknown_to_v3[f'{v3_cat}({v3_sub})' if v3_sub else v3_cat] += 1
            if len(unknown_examples[v3_cat]) < 3:
                unknown_examples[v3_cat].append(k)

    md.append('| v3 분류 | count |')
    md.append('|---|---|')
    for c, n in sorted(unknown_to_v3.items(), key=lambda x: -x[1]):
        md.append(f'| {c} | {n} |')
    md.append('')

    # 4. ECT 신규 79건의 source
    md.append('## 4. ECT 신규 79 group 의 v2 카테고리')
    md.append('')
    ect_from_v2: defaultdict[str, int] = defaultdict(int)
    ect_files: list[str] = []
    for k in common_keys:
        if v3[k]['category'] == 'ECT':
            v2_cat = v2[k]['category']
            v2_sub = v2[k].get('sub_tag', '')
            ect_from_v2[f'{v2_cat}({v2_sub})' if v2_sub else v2_cat] += 1
            if k[0] not in ect_files:
                ect_files.append(k[0])

    md.append('| v2 카테고리 | count |')
    md.append('|---|---|')
    for c, n in sorted(ect_from_v2.items(), key=lambda x: -x[1]):
        md.append(f'| {c} | {n} |')
    md.append('')
    md.append(f'### ECT 분류된 unique 파일 (전수 {len(ect_files)} 파일)')
    md.append('')
    for f in ect_files[:15]:
        md.append(f'- `{f}`')
    if len(ect_files) > 15:
        md.append(f'- (+{len(ect_files) - 15} more)')
    md.append('')

    # 5. HYSTERESIS 변동
    md.append('## 5. HYSTERESIS 카테고리 변동 (ref_step 일반화 효과)')
    md.append('')
    md.append('### v2 → v3 HYSTERESIS_DCHG transition')
    md.append('')
    md.append('| v2 카테고리 | v3 = HYSTERESIS_DCHG count |')
    md.append('|---|---|')
    h_dchg_src: defaultdict[str, int] = defaultdict(int)
    for k in common_keys:
        if v3[k]['category'] == 'HYSTERESIS_DCHG':
            h_dchg_src[v2[k]['category']] += 1
    for c, n in sorted(h_dchg_src.items(), key=lambda x: -x[1]):
        md.append(f'| {c} | {n} |')
    md.append('')

    md.append('### v2 → v3 HYSTERESIS_CHG transition')
    md.append('')
    md.append('| v2 카테고리 | v3 = HYSTERESIS_CHG count |')
    md.append('|---|---|')
    h_chg_src: defaultdict[str, int] = defaultdict(int)
    for k in common_keys:
        if v3[k]['category'] == 'HYSTERESIS_CHG':
            h_chg_src[v2[k]['category']] += 1
    for c, n in sorted(h_chg_src.items(), key=lambda x: -x[1]):
        md.append(f'| {c} | {n} |')
    md.append('')

    # 6. ACCEL 변동 (mid_life)
    md.append('## 6. v3 ACCEL 의 sub_tag 분포')
    md.append('')
    md.append('| sub_tag | count |')
    md.append('|---|---|')
    accel_subs: Counter = Counter()
    for r in v3.values():
        if r['category'] == 'ACCEL':
            accel_subs[r.get('sub_tag', '')] += 1
    for s, n in accel_subs.most_common():
        md.append(f'| {s if s else "(none)"} | {n} |')
    md.append('')

    # 7. PULSE_DCIR sub_tag 분포 (DCHG_CCCV mode=0 효과)
    md.append('## 7. v3 PULSE_DCIR 의 sub_tag 분포')
    md.append('')
    md.append('| sub_tag | count |')
    md.append('|---|---|')
    pulse_subs: Counter = Counter()
    for r in v3.values():
        if r['category'] == 'PULSE_DCIR':
            pulse_subs[r.get('sub_tag', '')] += 1
    for s, n in pulse_subs.most_common():
        md.append(f'| {s if s else "(none)"} | {n} |')
    md.append('')

    # 8. ECT sub_tag 분포
    md.append('## 8. v3 ECT 의 sub_tag 분포')
    md.append('')
    md.append('| sub_tag | count |')
    md.append('|---|---|')
    ect_subs: Counter = Counter()
    for r in v3.values():
        if r['category'] == 'ECT':
            ect_subs[r.get('sub_tag', '')] += 1
    for s, n in ect_subs.most_common():
        md.append(f'| {s if s else "(none)"} | {n} |')
    md.append('')

    out_md = OUT_DIR / 'sch_phase0_5_v2_v3_diff.md'
    with open(out_md, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    print(f"Wrote {out_md}")
    return 0


if __name__ == '__main__':
    main()
