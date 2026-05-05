"""'만충저장' 패턴 분석 — 복합floating schedule 의 FORMATION 오분류 검증.

사용자 도메인 지적 (260505):
  "복합사이클 분류에서 중간중간 formation으로 분류되는 것들의 사이클 목적은 '만충저장' 이다."
  → 4.5V 만충 + 고온 저장 + 주기적 capacity check 패턴.
  현재 v3 룰에서 FORMATION (2≤N≤10 + CHG+DCHG) 으로 잘못 분류.

검증 대상:
  1. 해당 schedule 의 group body 구조 (V/I/t)
  2. 전체 v3 결과 중 '복합floating' 폴더의 FORMATION 분류 group
  3. 도메인 정확한 분류 후보 (FORMATION strict / STORAGE / FLOATING / ACCEL ...)
"""
from __future__ import annotations

import csv
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

OUT_DIR = Path(__file__).parent
EXP_ROOT = Path(r"C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data")
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
            'i_32': struct.unpack_from('<f', blk, 32)[0],
            'mode_flag': struct.unpack_from('<I', blk, 84)[0],
            'rec_iv': struct.unpack_from('<f', blk, 336)[0],
            'chamber': struct.unpack_from('<f', blk, 396)[0],
            'loop_count': struct.unpack_from('<I', blk, 56)[0],
        }
        steps.append(s)
    return steps


def main() -> int:
    md = []
    md.append('# 만충저장 패턴 분석 — 복합floating schedule')
    md.append('')
    md.append('> 사용자 지적: "복합사이클 분류에서 중간중간 formation으로 분류되는'
              ' 것들의 사이클 목적은 \'만충저장\' 이다."')
    md.append('')

    # 1. 사용자 지정 schedule 직접 분석
    target = EXP_ROOT / (
        "수명_복합floating/260203_260531_01_최웅철_4268mAh_SDI GB6 PRO14 GEN4 1.3C "
        "고온복합/M01Ch054[054]/"
        "260203_260531_01_최웅철_4268mAh_SDI GB6 PRO14 GEN4 1.3C 고온복합.sch"
    )
    md.append(f'## 1. 사용자 지정 schedule 분석')
    md.append('')
    md.append(f'- file: `{target.name}`')
    md.append('')

    if not target.exists():
        md.append('파일 없음')
        return 1

    data = target.read_bytes()
    steps = parse_steps(data)
    md.append(f'- total steps: {len(steps)}')
    md.append('')

    md.append('### 전체 step sequence (V/I/t)')
    md.append('')
    md.append('| step# | type | mode | I (mA) | t (s) | V_cut (mV) | V_disp (mV) | I_end |')
    md.append('|---|---|---|---|---|---|---|---|')
    for s in steps[:60]:
        md.append(f"| {s['step_num']} | {s['type']:10} | {s['mode_flag']} | "
                  f"{s['i_20']:.0f} | {s['t_24']:.0f} | "
                  f"{s['v_28']:.0f} | {s['v_disp']:.0f} | {s['i_32']:.0f} |")
    if len(steps) > 60:
        md.append(f'| ... | (+{len(steps) - 60} more) |')
    md.append('')

    # LOOP 위치 + loop_count
    loops = [s for s in steps if s['type'] == 'LOOP']
    md.append(f'### LOOP step 위치 + 반복 횟수')
    md.append('')
    md.append('| step# | loop_count | 의미 |')
    md.append('|---|---|---|')
    for s in loops:
        md.append(f"| {s['step_num']} | {s['loop_count']} | — |")
    md.append('')

    # 2. v3 분류 결과에서 이 schedule 의 group 분류
    md.append('## 2. v3 분류 결과 — 사용자 지적 schedule')
    md.append('')
    rel_target = str(target.relative_to(EXP_ROOT))
    rel_norm = rel_target.replace('\\', '/').replace('/', '\\')
    found = []
    csv_path = OUT_DIR / 'sch_phase0_5_v3_groups.csv'
    if csv_path.exists():
        with open(csv_path, encoding='utf-8-sig') as f:
            for r in csv.DictReader(f):
                if (rel_target in r['rel_path']
                        or '260203_260531_01_최웅철' in r['rel_path']):
                    found.append(r)
    if found:
        md.append('| TC | N | category | sub_tag | n_chg | n_dchg | n_rest | body | C-rate (chg/dchg) |')
        md.append('|---|---|---|---|---|---|---|---|---|')
        for r in found[:30]:
            md.append(f"| {r['tc_start']}-{r['tc_end']} | {r['loop_count']} | "
                      f"**{r['category']}** | {r.get('sub_tag', '')} | "
                      f"{r['n_chg_step']} | {r['n_dchg_step']} | {r['n_rest_step']} | "
                      f"{r['body_size']} | {r['chg_crate']}/{r['dchg_crate']} |")
        if len(found) > 30:
            md.append(f'(+{len(found) - 30} more)')
    md.append('')

    # 3. 전체 '수명_복합floating' 폴더의 FORMATION 분류 group
    md.append('## 3. 전체 \'수명_복합floating\' 의 FORMATION 분류 group 전수')
    md.append('')
    formation_in_floating = []
    if csv_path.exists():
        with open(csv_path, encoding='utf-8-sig') as f:
            for r in csv.DictReader(f):
                if (r['test_category'] == '수명_복합floating'
                        and r['category'] == 'FORMATION'):
                    formation_in_floating.append(r)
    md.append(f'총 **{len(formation_in_floating)} group** FORMATION 분류 (수명_복합floating).')
    md.append('')
    if formation_in_floating:
        md.append('### dedup by (folder, body signature)')
        md.append('')
        seen = set()
        unique = []
        for r in formation_in_floating:
            key = (r['exp_folder'], r['n_chg_step'], r['n_dchg_step'],
                   r['n_rest_step'], r['body_size'], r['loop_count'],
                   r['chg_crate'], r['dchg_crate'])
            if key not in seen:
                seen.add(key)
                unique.append(r)
        md.append(f'unique signatures: **{len(unique)}**')
        md.append('')
        md.append('| folder | TC | N | body | chg/dchg/rest | C-rate chg/dchg | desc |')
        md.append('|---|---|---|---|---|---|---|')
        for r in unique[:30]:
            md.append(f"| {r['exp_folder'][:50]} | {r['tc_start']}-{r['tc_end']} | "
                      f"{r['loop_count']} | {r['body_size']} | "
                      f"{r['n_chg_step']}/{r['n_dchg_step']}/{r['n_rest_step']} | "
                      f"{r['chg_crate']}/{r['dchg_crate']} | "
                      f"{r['schedule_desc'][:30]} |")
        if len(unique) > 30:
            md.append(f'(+{len(unique) - 30} more)')
    md.append('')

    # 4. 모든 FORMATION 의 C-rate 분포 — 진짜 화성 (0.1~0.2C) vs 만충저장 (≥0.5C) 구분
    md.append('## 4. 전체 FORMATION 분류 group 의 C-rate 분포')
    md.append('')
    md.append('도메인적으로 FORMATION = 신규 셀 SEI 형성 (0.1~0.2C 저속).')
    md.append('만충저장 = ≥0.5C 충전 + 4.5V 만충 + 고온 저장.')
    md.append('')
    formation_all = []
    if csv_path.exists():
        with open(csv_path, encoding='utf-8-sig') as f:
            for r in csv.DictReader(f):
                if r['category'] == 'FORMATION':
                    formation_all.append(r)
    md.append(f'전체 FORMATION group: **{len(formation_all)}**')
    md.append('')
    md.append('### chg_crate 분포')
    md.append('')
    md.append('| chg_crate (rounded) | count | 도메인 의미 |')
    md.append('|---|---|---|')
    crate_dist: Counter = Counter()
    for r in formation_all:
        try:
            cr = float(r['chg_crate']) if r['chg_crate'] else 0
            crate_dist[round(cr, 1)] += 1
        except ValueError:
            crate_dist[0] += 1
    for cr, n in sorted(crate_dist.items()):
        meaning = ''
        if cr <= 0.25:
            meaning = '⭐ 진짜 FORMATION (0.1~0.2C 저속)'
        elif cr >= 0.5:
            meaning = '⚠️ 만충저장 또는 fast cycling (FORMATION 아님)'
        else:
            meaning = '경계 (0.3~0.5C)'
        md.append(f'| {cr:.1f}C | {n} | {meaning} |')
    md.append('')

    md.append('### dchg_crate 분포')
    md.append('')
    md.append('| dchg_crate (rounded) | count |')
    md.append('|---|---|')
    crate_d_dist: Counter = Counter()
    for r in formation_all:
        try:
            cr = float(r['dchg_crate']) if r['dchg_crate'] else 0
            crate_d_dist[round(cr, 1)] += 1
        except ValueError:
            crate_d_dist[0] += 1
    for cr, n in sorted(crate_d_dist.items()):
        md.append(f'| {cr:.1f}C | {n} |')
    md.append('')

    # 5. 도메인 룰 후보
    md.append('## 5. 룰 수정 후보 — FORMATION strict')
    md.append('')
    md.append('현재 v3 룰: `2 ≤ N ≤ 10 AND chg AND dchg`')
    md.append('')
    md.append('도메인 정확화:')
    md.append('1. **FORMATION strict**: `2 ≤ N ≤ 10 AND chg AND dchg AND chg_crate ≤ 0.3 AND dchg_crate ≤ 0.5`')
    md.append('2. 위 조건 안 걸리는 N=2~10 + CHG+DCHG → CHG_DCHG fall-through 또는 신규 카테고리')
    md.append('3. 4.5V 만충 + 고온 chamber + 0.5~1.3C 충전 = "만충저장" 패턴')
    md.append('')

    out_md = OUT_DIR / 'storage_inspect.md'
    with open(out_md, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    print(f"Wrote {out_md}", file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
