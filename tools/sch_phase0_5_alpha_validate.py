"""Phase 0-5-α: ref_step_number = +501 (uint8) 가설 cross-validate.

Hypothesis (DCIR sample 검증):
  +500 uint32 = (ref_step_number << 8) | end_condition_type_marker
  → +501 (uint8) = ref_step_number
  → +500 (uint8) = type marker (0 in observed cases)

Validate against:
  1. Hysteresis sample — Phase 0-5 spec said +500=2048 (DCHG DOD%) → ref_step=8
  2. Hysteresis sample — Phase 0-5 spec said +500=18432 (CHG SOC%) → ref_step=72
  3. ECT sample — multi-step with various ref step jumps
  4. Random sample from 368 .sch → 분포 + 비0 ref_step 사용 빈도

Also try to identify:
  - ref_step_kind (Char./Dis. enum)
  - ref_basis (AH or V enum)
  - jump_target_step
"""
from __future__ import annotations

import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

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

CHG_TYPES = frozenset({'CHG_CC', 'CHG_CCCV', 'CHG_CP'})
DCHG_TYPES = frozenset({'DCHG_CC', 'DCHG_CCCV'})


def parse_steps(data: bytes) -> list[dict]:
    n = (len(data) - HEADER_SIZE) // BLOCK_SIZE
    steps = []
    for i in range(n):
        ofs = HEADER_SIZE + i * BLOCK_SIZE
        blk = data[ofs:ofs + BLOCK_SIZE]
        type_code = struct.unpack_from('<I', blk, 8)[0]
        type_name = SCH_TYPE_MAP.get(type_code, f'UNK_0x{type_code:04X}')
        ec500 = struct.unpack_from('<I', blk, 500)[0]
        ec504 = struct.unpack_from('<I', blk, 504)[0]
        # decompose +500
        b500 = ec500 & 0xFF        # type marker
        b501 = (ec500 >> 8) & 0xFF  # ref_step_number (hypothesis)
        b502 = (ec500 >> 16) & 0xFF
        b503 = (ec500 >> 24) & 0xFF
        steps.append({
            'idx': i,
            'step_num': struct.unpack_from('<I', blk, 0)[0],
            'type': type_name,
            'type_code': type_code,
            'ec500_full': ec500,
            'ec500_b0': b500,
            'ec500_b1_ref': b501,
            'ec500_b2': b502,
            'ec500_b3': b503,
            'ec504_enabled': ec504,
            'pct_372': struct.unpack_from('<f', blk, 372)[0],
            'i_20': struct.unpack_from('<f', blk, 20)[0],
            't_24': struct.unpack_from('<f', blk, 24)[0],
            'blk': blk,
        })
    return steps


def find_first_match(pattern_substring: str) -> Path | None:
    """Find first .sch matching folder name substring."""
    for p in EXP_ROOT.rglob('*.sch'):
        try:
            rel = p.relative_to(EXP_ROOT)
        except ValueError:
            continue
        if pattern_substring.lower() in str(rel).lower():
            return p
    return None


def main() -> int:
    samples = [
        ("DCIR (known)", "SBR 0.9 DCIR"),
        ("Hysteresis 1", "0.5C-10min volt hysteresis"),
        ("Hysteresis 2", "0.2C-10min volt hysteresis"),
        ("ECT-parameter", "ECT-parameter1"),
        ("Floating", "Floating+9D"),
        ("Accel 수명", "ATL Q7M Inner 2C 상온수명"),
        ("RSS DCIR", "Q8 ATL Main 2.0C Rss"),
    ]

    for label, pat in samples:
        path = find_first_match(pat)
        if path is None:
            print(f"== {label}: '{pat}' — NOT FOUND ==\n")
            continue
        print(f"== {label}: {path.name[:80]}")
        try:
            data = path.read_bytes()
        except OSError as e:
            print(f"  read error: {e}\n")
            continue
        steps = parse_steps(data)

        # Show steps with ec504_enabled=1 (ref-step in use)
        ref_using = [s for s in steps if s['ec504_enabled'] == 1]
        print(f"  total steps: {len(steps)}, ref-using (ec504=1): {len(ref_using)}")
        if not ref_using:
            print()
            continue
        print("  idx | step# | type      | +500_uint32 | type_byte | "
              "ref_step | pct_372 | summary")
        print("  ----|-------|-----------|-------------|-----------|----------"
              "|---------|--------")
        for s in ref_using[:15]:
            t_short = s['type'][:9]
            print(f"  {s['idx']:3} | {s['step_num']:3} | {t_short:9} | "
                  f"{s['ec500_full']:11} | {s['ec500_b0']:9} | "
                  f"{s['ec500_b1_ref']:8} | {s['pct_372']:7.2f} | "
                  f"b2={s['ec500_b2']} b3={s['ec500_b3']}")
        if len(ref_using) > 15:
            print(f"  (+{len(ref_using) - 15} more)")
        print()

    # ===== 187 전수 통계: ref-step 사용 빈도 + +500 분해 분포 =====
    print("=" * 80)
    print("== 368 .sch 전수 통계 ==")
    print("=" * 80)
    print()

    files = sorted(EXP_ROOT.rglob('*.sch'))
    n_files = 0
    total_steps = 0
    n_ref_using = 0
    refstep_dist: Counter = Counter()
    typebyte_dist: Counter = Counter()
    refstep_by_steptype: defaultdict[str, Counter] = defaultdict(Counter)
    pct_dist_at_refstep: defaultdict[float, int] = defaultdict(int)
    file_with_ref: list[tuple[Path, int]] = []  # (path, n_ref_steps)
    high_byte_dist: Counter = Counter()  # +500 b2/b3 if any non-zero

    for path in files:
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if len(data) < HEADER_SIZE + BLOCK_SIZE:
            continue
        if struct.unpack_from('<I', data, 0)[0] != 740721:
            continue
        n_files += 1
        steps = parse_steps(data)
        total_steps += len(steps)
        n_ref_in_file = 0
        for s in steps:
            if s['ec504_enabled'] != 1:
                continue
            n_ref_using += 1
            n_ref_in_file += 1
            refstep_dist[s['ec500_b1_ref']] += 1
            typebyte_dist[s['ec500_b0']] += 1
            refstep_by_steptype[s['type']][s['ec500_b1_ref']] += 1
            pct_dist_at_refstep[round(s['pct_372'], 1)] += 1
            if s['ec500_b2'] != 0 or s['ec500_b3'] != 0:
                high_byte_dist[(s['ec500_b2'], s['ec500_b3'])] += 1
        if n_ref_in_file > 0:
            file_with_ref.append((path, n_ref_in_file))

    print(f"Files parsed: {n_files} / total steps: {total_steps}")
    print(f"Ref-step using steps: {n_ref_using} ({n_ref_using/total_steps*100:.1f}%)")
    print(f"Files with ≥1 ref-step: {len(file_with_ref)}")
    print()

    print("=== ref_step_number (+501 byte) distribution ===")
    print(f"  unique values: {len(refstep_dist)}")
    print(f"  range: {min(refstep_dist):d} ~ {max(refstep_dist):d}"
          if refstep_dist else "  (empty)")
    print(f"  Top 20:")
    for v, n in refstep_dist.most_common(20):
        print(f"    {v}: {n}")
    print()

    print("=== type_byte (+500 byte 0) distribution ===")
    for v, n in typebyte_dist.most_common():
        print(f"  byte=0x{v:02X} ({v}): {n}")
    print()

    print("=== ref_step_number by step type ===")
    for t, c in sorted(refstep_by_steptype.items()):
        top = c.most_common(5)
        print(f"  {t}: total={sum(c.values())}, top values: {top}")
    print()

    print("=== pct_threshold (+372) distribution at ref-step ===")
    for v, n in sorted(pct_dist_at_refstep.items())[:30]:
        print(f"  {v:6.1f}%: {n}")
    print()

    print("=== +500 high bytes (b2, b3) distribution (non-zero only) ===")
    if high_byte_dist:
        for (b2, b3), n in high_byte_dist.most_common(10):
            print(f"  (b2={b2}, b3={b3}): {n}")
    else:
        print("  All zero — high bytes unused.")
    print()

    print("=== Files with most ref-step usage ===")
    file_with_ref.sort(key=lambda x: -x[1])
    for path, n in file_with_ref[:10]:
        try:
            rel = path.relative_to(EXP_ROOT)
            print(f"  {n:3} ref-steps: {rel}")
        except ValueError:
            print(f"  {n:3} ref-steps: {path}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
