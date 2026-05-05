"""Phase 0-5-α: ref_step_kind / ref_basis / jump_target_step 식별 시도.

Strategy:
  1. 1,169 ref-using steps 의 모든 byte/uint16/uint32 offset 비교
  2. ref-using steps 에서는 비0/특정값, non-ref steps 에서는 0/다른값 인 offset 식별
  3. ref_step_kind enum 후보: 모든 ref-using step 에서 같은 값 (Char.)
  4. ref_basis enum 후보: 모든 ref-using step 에서 같은 값 (AH)
  5. jump_target_step 후보: NEXT (0?) 또는 step_num 후보
"""
from __future__ import annotations

import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

EXP_ROOT = Path(r"C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data")
HEADER_SIZE = 1920
BLOCK_SIZE = 652


def main() -> int:
    files = sorted(EXP_ROOT.rglob('*.sch'))
    print(f"Scanning {len(files)} files...", file=sys.stderr)

    # Collect ref-using steps + non-ref steps for comparison
    ref_blocks: list[bytes] = []
    nonref_blocks: list[bytes] = []
    ref_step_nums: list[int] = []  # own step_num
    ref_step_refs: list[int] = []  # +501

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
        n = (len(data) - HEADER_SIZE) // BLOCK_SIZE
        for i in range(n):
            ofs = HEADER_SIZE + i * BLOCK_SIZE
            blk = data[ofs:ofs + BLOCK_SIZE]
            ec504 = struct.unpack_from('<I', blk, 504)[0]
            ec500 = struct.unpack_from('<I', blk, 500)[0]
            type_code = struct.unpack_from('<I', blk, 8)[0]
            if ec504 == 1 and ec500 != 0:
                ref_blocks.append(blk)
                ref_step_nums.append(struct.unpack_from('<I', blk, 0)[0])
                ref_step_refs.append((ec500 >> 8) & 0xFF)
            elif (type_code in (0x0101, 0x0102, 0x0201, 0x0202)
                  and ec504 == 0):
                # active CHG/DCHG step without ref
                nonref_blocks.append(blk)

    print(f"Ref-using blocks: {len(ref_blocks)}")
    print(f"Non-ref active blocks: {len(nonref_blocks)}")
    print()

    # ===== 1. 모든 ref-using 에서 동일한 byte 값 (enum 후보) =====
    print("== 1. Offsets where ALL ref-using blocks have same byte value ==")
    print("  (potential ref_step_kind / ref_basis enum, constant across all)")
    print()
    if not ref_blocks:
        return 0

    ref_first_byte = ref_blocks[0]
    same_byte_offsets: list[int] = []
    for ofs in range(BLOCK_SIZE):
        v = ref_first_byte[ofs]
        if all(b[ofs] == v for b in ref_blocks):
            # Check if non-ref blocks have different value
            nonref_vals = Counter(b[ofs] for b in nonref_blocks[:200])  # sample
            if v in (0, 1, 2, 3, 4, 5):  # likely enum values
                # Skip if 0 (too generic)
                if v == 0:
                    continue
                # Skip if non-ref also has same value mostly
                if nonref_vals.get(v, 0) > len(nonref_blocks) * 0.5:
                    continue
                same_byte_offsets.append(ofs)
                print(f"  +{ofs}: all = {v} (nonref top: {nonref_vals.most_common(3)})")
    print(f"  Total: {len(same_byte_offsets)} candidate offsets")
    print()

    # ===== 2. uint32 offsets where ALL ref-using have same value (filter out
    #         common system constants) =====
    print("== 2. uint32 offsets where ALL ref-using have same non-zero value ==")
    print()
    common_uint32: list[tuple[int, int]] = []
    for ofs in range(0, BLOCK_SIZE - 3, 4):
        v0 = struct.unpack_from('<I', ref_blocks[0], ofs)[0]
        if v0 == 0:
            continue
        if not all(struct.unpack_from('<I', b, ofs)[0] == v0 for b in ref_blocks):
            continue
        # Check if nonref blocks also have v0 mostly (filter system constants)
        nonref_match = sum(
            1 for b in nonref_blocks[:500]
            if struct.unpack_from('<I', b, ofs)[0] == v0)
        sample_size = min(500, len(nonref_blocks))
        if sample_size > 0 and nonref_match / sample_size > 0.7:
            continue  # too common
        common_uint32.append((ofs, v0))
    for ofs, v in common_uint32[:30]:
        as_float = struct.unpack('<f', struct.pack('<I', v))[0]
        print(f"  +{ofs}: {v} (float={as_float:g}, hex=0x{v:08X})")
        # Compare with sample non-ref blocks
        nonref_vals = Counter(struct.unpack_from('<I', b, ofs)[0]
                               for b in nonref_blocks[:50])
        print(f"    nonref top: {nonref_vals.most_common(3)}")
    print(f"  Total: {len(common_uint32)} candidate uint32 offsets")
    print()

    # ===== 3. uint16 offsets where ALL ref-using have same value =====
    print("== 3. uint16 offsets where ALL ref-using have same non-zero value (small) ==")
    print()
    common_uint16: list[tuple[int, int]] = []
    for ofs in range(0, BLOCK_SIZE - 1, 2):
        v0 = struct.unpack_from('<H', ref_blocks[0], ofs)[0]
        if v0 == 0:
            continue
        if v0 > 1000:  # skip large
            continue
        if not all(struct.unpack_from('<H', b, ofs)[0] == v0 for b in ref_blocks):
            continue
        nonref_match = sum(
            1 for b in nonref_blocks[:500]
            if struct.unpack_from('<H', b, ofs)[0] == v0)
        sample_size = min(500, len(nonref_blocks))
        if sample_size > 0 and nonref_match / sample_size > 0.7:
            continue
        common_uint16.append((ofs, v0))
    for ofs, v in common_uint16[:30]:
        nonref_vals = Counter(struct.unpack_from('<H', b, ofs)[0]
                               for b in nonref_blocks[:50])
        print(f"  +{ofs} (uint16): {v} (nonref top: {nonref_vals.most_common(3)})")
    print()

    # ===== 4. uint8 offsets =====
    print("== 4. uint8 offsets where ALL ref-using have same non-zero value ==")
    print()
    common_uint8: list[tuple[int, int]] = []
    for ofs in range(BLOCK_SIZE):
        v0 = ref_blocks[0][ofs]
        if v0 == 0:
            continue
        if not all(b[ofs] == v0 for b in ref_blocks):
            continue
        nonref_match = sum(1 for b in nonref_blocks[:500] if b[ofs] == v0)
        sample_size = min(500, len(nonref_blocks))
        if sample_size > 0 and nonref_match / sample_size > 0.7:
            continue
        common_uint8.append((ofs, v0))
    for ofs, v in common_uint8[:50]:
        nonref_vals = Counter(b[ofs] for b in nonref_blocks[:50])
        print(f"  +{ofs} (uint8): {v} (nonref top: {nonref_vals.most_common(3)})")
    print()

    # ===== 5. Search for jump_target_step variation =====
    # If jump_target = NEXT, all ref-using would have same value (e.g., 0)
    # If jump_target varies (some "Move Step N"), there should be variation
    print("== 5. Per-block byte variation analysis (jump_target candidate) ==")
    print("  offsets where ref-using values vary AND most are step_num+1 ==")
    print()
    for ofs in range(0, BLOCK_SIZE - 3, 4):
        vals = [struct.unpack_from('<I', b, ofs)[0] for b in ref_blocks[:200]]
        # Check if values look like step numbers (small integers)
        small_vals = [v for v in vals if 0 < v < 256]
        if len(small_vals) > 100:  # most are small
            uniq = len(set(small_vals))
            if 5 < uniq < 100:  # varied enough
                top = Counter(small_vals).most_common(5)
                print(f"  +{ofs} uint32: top vals: {top} (unique={uniq})")

    return 0


if __name__ == '__main__':
    sys.exit(main())
