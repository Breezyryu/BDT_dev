"""Phase 0-5-α: +84 mode_flag 의 의미 추론 — 전수 dump.

Phase 0-2 H7 partial result:
  - +84 는 단순 binary (0/1) 가 아닌 multi-purpose mode field
  - DCHG_CC 의 +84=257 6회 등장 — 특이값
  - REST/REST_SAFE/LOOP 모두 0/1 혼재 — 의미 미해결

본 스크립트는 사용자 도메인 추론을 위해 다음 차원의 dump 제공:
  1. 전체 값 분포 + step type 별
  2. step type 별 +84=1 vs 0 의 다른 field 값 차이 (V/I/t)
  3. Special values (≠ 0/1) 의 전체 컨텍스트
  4. Per-file consistency — 한 파일 내 +84 분포
  5. schedule_description keyword 별 +84 분포
"""
from __future__ import annotations

import csv
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
    0x0201: 'CHG_CC', 0x0202: 'DCHG_CC',
    0x0209: 'CHG_CP',
    0xFF03: 'REST', 0xFF06: 'GOTO', 0xFF07: 'REST_SAFE', 0xFF08: 'LOOP',
    0x0003: 'GITT_PAUSE', 0x0006: 'END',
    0x0007: 'GITT_END', 0x0008: 'GITT_START',
}


def main() -> int:
    files = sorted(EXP_ROOT.rglob('*.sch'))
    print(f"Scanning {len(files)} files...", file=sys.stderr)

    # ---- Per-step rows ----
    rows: list[dict] = []
    # Per-file +84 distribution
    file_mode_dist: dict[Path, Counter] = {}

    for fi, path in enumerate(files):
        if fi % 50 == 0 and fi > 0:
            print(f"  [{fi}/{len(files)}]", file=sys.stderr)
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if len(data) < HEADER_SIZE + BLOCK_SIZE:
            continue
        if struct.unpack_from('<I', data, 0)[0] != 740721:
            continue

        # schedule description
        desc_b = data[664:664 + 64]
        end = desc_b.find(b'\x00')
        if end >= 0:
            desc_b = desc_b[:end]
        try:
            desc = desc_b.decode('ascii', errors='replace').strip()
        except Exception:
            desc = ''

        try:
            rel = path.relative_to(EXP_ROOT)
            test_cat = rel.parts[0] if rel.parts else 'UNKNOWN'
            exp_folder = rel.parts[1] if len(rel.parts) > 1 else rel.parts[0]
        except ValueError:
            test_cat = 'UNKNOWN'
            exp_folder = path.parent.name

        n_steps = (len(data) - HEADER_SIZE) // BLOCK_SIZE
        file_mode_count: Counter = Counter()

        for i in range(n_steps):
            ofs = HEADER_SIZE + i * BLOCK_SIZE
            blk = data[ofs:ofs + BLOCK_SIZE]
            type_code = struct.unpack_from('<I', blk, 8)[0]
            type_name = SCH_TYPE_MAP.get(type_code, f'UNK_0x{type_code:04X}')
            step_num = struct.unpack_from('<I', blk, 0)[0]
            mode_flag = struct.unpack_from('<I', blk, 84)[0]

            v12 = struct.unpack_from('<f', blk, 12)[0]
            v16 = struct.unpack_from('<f', blk, 16)[0]
            i20 = struct.unpack_from('<f', blk, 20)[0]
            t24 = struct.unpack_from('<f', blk, 24)[0]
            v28 = struct.unpack_from('<f', blk, 28)[0]
            i32 = struct.unpack_from('<f', blk, 32)[0]
            ec500 = struct.unpack_from('<I', blk, 500)[0]
            ec504 = struct.unpack_from('<I', blk, 504)[0]
            rec336 = struct.unpack_from('<f', blk, 336)[0]
            chamber396 = struct.unpack_from('<f', blk, 396)[0]

            file_mode_count[mode_flag] += 1
            rows.append({
                'test_cat': test_cat,
                'exp_folder': exp_folder[:50],
                'sch_file': path.name[:60],
                'desc': desc[:50],
                'step_idx': i,
                'step_num': step_num,
                'type': type_name,
                'mode_flag': mode_flag,
                'mode_hex': f'0x{mode_flag:08X}',
                'v_disp': v12 if 'CHG' in type_name and 'D' not in type_name else v16,
                'i_20': i20,
                't_24': t24,
                'v_28_end': v28,
                'i_32_end': i32,
                'ec500': ec500,
                'ec504': ec504,
                'rec_iv': rec336,
                'chamber': chamber396,
            })

        file_mode_dist[path] = file_mode_count

    print(f"Total step rows: {len(rows)}", file=sys.stderr)

    # ===== Aggregations =====
    md = []
    md.append('# +84 mode_flag 의미 추론 — 368 .sch 전수 dump')
    md.append('')
    md.append(f'- Total step rows: **{len(rows)}**')
    md.append('')

    # 1. 전체 값 분포
    md.append('## 1. mode_flag 값 전체 분포')
    md.append('')
    val_dist = Counter(r['mode_flag'] for r in rows)
    md.append('| value (dec) | hex | count | 비율 |')
    md.append('|---|---|---|---|')
    for v, n in val_dist.most_common():
        md.append(f'| {v} | 0x{v:08X} | {n} | {n/len(rows)*100:.2f}% |')
    md.append('')

    # 2. step type 별 mode_flag
    md.append('## 2. step type × mode_flag cross-table')
    md.append('')
    type_mode: defaultdict[str, Counter] = defaultdict(Counter)
    for r in rows:
        type_mode[r['type']][r['mode_flag']] += 1
    all_modes = sorted(val_dist.keys())
    md.append('| Type | total | ' + ' | '.join(f'mode={m}' for m in all_modes) + ' |')
    md.append('|' + '---|' * (2 + len(all_modes)))
    for t in sorted(type_mode.keys()):
        c = type_mode[t]
        total = sum(c.values())
        cells = [str(c.get(m, 0)) for m in all_modes]
        md.append(f'| {t} | {total} | ' + ' | '.join(cells) + ' |')
    md.append('')

    # 3. mode_flag=1 vs 0 의 다른 field 비교 (per step type)
    md.append('## 3. mode_flag=1 vs 0 — 같은 step type 내 다른 field 통계')
    md.append('')
    md.append('각 step type 에서 mode_flag=1 vs 0 인 step 들의 +20 (current),'
              ' +24 (time), +28 (V end), +32 (I end), +500 (EC), +336 (rec_iv) 비교.')
    md.append('값이 다르면 mode_flag 가 그 field 의 enable 또는 의미 modifier 일 가능성.')
    md.append('')
    for t in ['CHG_CC', 'CHG_CCCV', 'DCHG_CC', 'DCHG_CCCV', 'REST', 'REST_SAFE',
              'LOOP', 'GOTO']:
        rows_t = [r for r in rows if r['type'] == t]
        if not rows_t:
            continue
        rows_1 = [r for r in rows_t if r['mode_flag'] == 1]
        rows_0 = [r for r in rows_t if r['mode_flag'] == 0]
        if not rows_1 or not rows_0:
            continue

        md.append(f'### {t} (n_total={len(rows_t)}, mode=1: {len(rows_1)},'
                  f' mode=0: {len(rows_0)})')
        md.append('')
        md.append('| field | mode=1 mean | mode=1 nonzero | '
                  'mode=0 mean | mode=0 nonzero |')
        md.append('|---|---|---|---|---|')
        for field, label in [('i_20', '+20 current'),
                             ('t_24', '+24 time'),
                             ('v_28_end', '+28 V end'),
                             ('i_32_end', '+32 I end'),
                             ('rec_iv', '+336 rec_iv'),
                             ('chamber', '+396 chamber'),
                             ('ec500', '+500 EC'),
                             ('ec504', '+504 EC en')]:
            v1 = [r[field] for r in rows_1]
            v0 = [r[field] for r in rows_0]
            m1 = sum(v1) / len(v1) if v1 else 0
            m0 = sum(v0) / len(v0) if v0 else 0
            nz1 = sum(1 for v in v1 if v != 0)
            nz0 = sum(1 for v in v0 if v != 0)
            md.append(f'| {label} | {m1:.2f} | {nz1}/{len(v1)} | '
                      f'{m0:.2f} | {nz0}/{len(v0)} |')
        md.append('')

    # 4. Special values (≠ 0, 1)
    md.append('## 4. Special values (≠ 0, 1) — 전체 컨텍스트')
    md.append('')
    special = [r for r in rows if r['mode_flag'] not in (0, 1)]
    if special:
        md.append(f'Total: {len(special)} step rows.')
        md.append('')
        md.append('| test_cat | exp_folder | sch | step# | type | mode (hex) | '
                  '+20 (I) | +24 (t) | +28 (V) | +500 (EC) | desc |')
        md.append('|' + '---|' * 11)
        for r in special:
            md.append(f"| {r['test_cat']} | {r['exp_folder'][:30]} | "
                      f"{r['sch_file'][:40]} | {r['step_num']} | {r['type']} | "
                      f"{r['mode_flag']} ({r['mode_hex']}) | "
                      f"{r['i_20']:.1f} | {r['t_24']:.0f} | {r['v_28_end']:.1f} | "
                      f"{r['ec500']} | {r['desc'][:30]} |")
    else:
        md.append('없음 (모든 mode_flag ∈ {0, 1}).')
    md.append('')

    # 5. Per-file consistency (한 파일 내 +84 분포)
    md.append('## 5. Per-file consistency — 같은 파일 내 +84 분포')
    md.append('')
    md.append('한 schedule 내에서 mode_flag 가 어떻게 변동하는지 — '
              'unique value 개수가 클수록 다양한 mode 사용.')
    md.append('')
    file_uniq: defaultdict[int, int] = defaultdict(int)
    for path, c in file_mode_dist.items():
        file_uniq[len(c)] += 1
    md.append('| unique mode values per file | count files |')
    md.append('|---|---|')
    for k in sorted(file_uniq.keys()):
        md.append(f'| {k} | {file_uniq[k]} |')
    md.append('')

    # 6. schedule keyword 별 mode_flag 분포
    md.append('## 6. schedule_description keyword × mode_flag (per file)')
    md.append('')
    kw_mode: defaultdict[str, Counter] = defaultdict(Counter)
    seen_files = set()
    for r in rows:
        key = (r['sch_file'], r['exp_folder'])
        if key in seen_files:
            continue
        seen_files.add(key)
        # ... 이 logic 은 step level 이라 부정확. file level 로 다시
    # 다시 file level 로 redoing
    file_kw: dict = {}
    file_modes: dict = {}
    for r in rows:
        key = r['sch_file']
        d = r['desc'].lower()
        if 'hysteresis' in d:
            kw = 'hysteresis'
        elif 'gitt' in d:
            kw = 'gitt'
        elif 'ect' in d:
            kw = 'ect'
        elif 'floating' in d or '120d' in d:
            kw = 'floating'
        elif 'rss' in d:
            kw = 'rss'
        elif 'dcir' in d:
            kw = 'dcir'
        elif 'rpt' in d:
            kw = 'rpt'
        elif 'formation' in d or '화성' in d:
            kw = 'formation'
        else:
            kw = 'other'
        file_kw[key] = kw
        file_modes.setdefault(key, Counter())[r['mode_flag']] += 1

    kw_step_mode: defaultdict[str, Counter] = defaultdict(Counter)
    for key, mc in file_modes.items():
        kw = file_kw.get(key, 'other')
        for m, n in mc.items():
            kw_step_mode[kw][m] += n
    md.append('| keyword | total steps | mode_flag 분포 (top) |')
    md.append('|---|---|---|')
    for kw in sorted(kw_step_mode.keys()):
        c = kw_step_mode[kw]
        total = sum(c.values())
        top = ', '.join(f'{m}:{n}' for m, n in c.most_common(5))
        md.append(f'| {kw} | {total} | {top} |')
    md.append('')

    # 7. CSV: special-value steps 전체 dump
    md.append('## 7. 산출')
    md.append('')
    md.append('- `mode_flag_special_steps.csv` — mode_flag ∉ {0,1} step 전수 (full row)')
    md.append('- `mode_flag_step_dump.csv` — 모든 step 의 mode_flag + key fields')
    md.append('')

    # Special CSV
    if special:
        sp_csv = OUT_DIR / 'mode_flag_special_steps.csv'
        with open(sp_csv, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=list(special[0].keys()))
            writer.writeheader()
            writer.writerows(special)
        print(f"Wrote {sp_csv}", file=sys.stderr)

    # Full step CSV (모든 step row)
    full_csv = OUT_DIR / 'mode_flag_step_dump.csv'
    with open(full_csv, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {full_csv}", file=sys.stderr)

    # MD
    out_md = OUT_DIR / 'mode_flag_analysis.md'
    with open(out_md, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    print(f"Wrote {out_md}", file=sys.stderr)

    return 0


if __name__ == '__main__':
    sys.exit(main())
