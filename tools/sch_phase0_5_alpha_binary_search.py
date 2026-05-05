"""Phase 0-5-α: SOC/DOD ref-step jump binary offset 식별 (binary search) — v2.

Real binary structure (from sch_phase0_5_alpha_dump.py):
  idx 17 (step#18): DCHG_CC 133mA, +500=4608 (DOD), pct=100
                    → ref CHG step = idx 16 (step#17, CHG 0.05C, 20s)
                    → expected ref_step_number = 17 (or 16 if 0-based)
  idx 20 (step#21): DCHG_CC 263mA, +500=5376 (DOD), pct=100
                    → ref CHG step = idx 19 (step#20, CHG 0.1C, 20s)
                    → expected = 20
  idx 23 (step#24): DCHG_CC 522mA, +500=6144 (DOD), pct=100
                    → ref CHG step = idx 22 (step#23, CHG 0.2C, 20s)
                    → expected = 23
  idx 26 (step#27): DCHG_CC 1307mA, +500=6912 (DOD), pct=100
                    → ref CHG step = idx 25 (step#26, CHG 0.5C, 20s)
                    → expected = 26
  idx 27 (step#28): CHG_CCCV 522mA, +500=2816 (SOC), pct=1.0
                    → ref CHG step (cluster start) = idx ??, expected = 4 or 9 (early CHG)

전략:
  4 DCHG-with-DOD steps 의 모든 uint32 offset 비교 →
  4 step 에서 모두 step_num-1 (preceding CHG) 인 offset 식별.
  Phase 0-4 spec 의 "Step 27" reference label = preceding CHG step number.

추가:
  idx 27 의 SOC 1% — ref step 은 cluster 첫 CHG step (idx 4 = step#5 또는 idx 9 = step#10)
  를 의미. 검증 필요.
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

EXP_ROOT = Path(r"C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data")
HEADER_SIZE = 1920
BLOCK_SIZE = 652

DCIR_PATH = EXP_ROOT / (
    "성능/250513_250526_05_나무늬_2610mAh_Gen5+B SDI MP1 Main SBR 0.9 DCIR/"
    "M01Ch037[037]/"
    "250513_250526_05_나무늬_2610mAh_Gen5+B SDI MP1 Main SBR 0.9 DCIR.sch"
)


def read_step_block(data: bytes, step_idx: int) -> bytes:
    ofs = HEADER_SIZE + step_idx * BLOCK_SIZE
    return data[ofs:ofs + BLOCK_SIZE]


def main() -> int:
    data = DCIR_PATH.read_bytes()
    n_steps = (len(data) - HEADER_SIZE) // BLOCK_SIZE
    print(f"Sample: {DCIR_PATH.name}")
    print(f"  size: {len(data)} bytes, n_steps: {n_steps}")
    print()

    # 4 DCHG-with-DOD-100% steps + 1 CHG-with-SOC-1% step
    # Each tuple: (idx, expected_ref_step_number, label)
    targets = [
        (17, 17, "DCHG idx17 step#18 ref CHG step#17"),
        (20, 20, "DCHG idx20 step#21 ref CHG step#20"),
        (23, 23, "DCHG idx23 step#24 ref CHG step#23"),
        (26, 26, "DCHG idx26 step#27 ref CHG step#26"),
    ]
    # SOC 1% step — ref to cluster start. Expected step_num: try 5 or 10 first
    soc_idx = 27
    soc_candidates = [5, 10, 11, 16]  # possible cluster-start CHG step numbers

    blocks = [(idx, expected, label, read_step_block(data, idx))
              for idx, expected, label in targets]

    # ---- 1. Scan every uint32 aligned offset ----
    # Find offsets where block[i] uint32 == expected_i for ALL i
    print("== Scan: uint32 offsets where ALL 4 DCHG-with-DOD steps match expected ref_step ==")
    print()
    candidate_offsets = []
    for ofs in range(0, BLOCK_SIZE - 3, 4):
        match_all = True
        for idx, expected, label, blk in blocks:
            v = struct.unpack_from('<I', blk, ofs)[0]
            if v != expected:
                match_all = False
                break
        if match_all:
            candidate_offsets.append(ofs)
            print(f"  ⭐ +{ofs}: all 4 match")
            for idx, expected, label, blk in blocks:
                v = struct.unpack_from('<I', blk, ofs)[0]
                print(f"    {label}: +{ofs} = {v}")
    if not candidate_offsets:
        print("  No fully-aligned match.")
    print()

    # ---- 2. Loosen: scan offsets where MOST steps match ----
    print("== Scan: offsets where ≥3 of 4 DCHG steps have value == expected ref_step ==")
    print()
    for ofs in range(0, BLOCK_SIZE - 3, 4):
        n_match = 0
        vals = []
        for idx, expected, label, blk in blocks:
            v = struct.unpack_from('<I', blk, ofs)[0]
            vals.append((v, expected))
            if v == expected:
                n_match += 1
        if n_match >= 3:
            print(f"  +{ofs}: {n_match}/4 match. values:")
            for (v, e), (_, _, label, _) in zip(vals, blocks):
                tag = "✓" if v == e else f"≠{e}"
                print(f"    {label}: {v} {tag}")
    print()

    # ---- 3. Try monotone increasing offsets ----
    # ref_step_number 가 17→20→23→26 으로 monotone 증가하는 offset 찾기
    print("== Scan: offsets with monotone-increasing values (17,20,23,26) or "
          "(16,19,22,25) ==")
    print()
    expected_v1 = [17, 20, 23, 26]
    expected_v2 = [16, 19, 22, 25]  # 0-based interpretation
    expected_v3 = [18, 21, 24, 27]  # +1 offset
    for ofs in range(0, BLOCK_SIZE - 3, 4):
        vals = [struct.unpack_from('<I', blk, ofs)[0]
                for idx, expected, label, blk in blocks]
        if vals == expected_v1:
            print(f"  ⭐⭐⭐ +{ofs}: matches expected_v1 (17,20,23,26) — ref CHG step_num")
        elif vals == expected_v2:
            print(f"  ⭐⭐ +{ofs}: matches expected_v2 (16,19,22,25) — 0-based or alt")
        elif vals == expected_v3:
            print(f"  ⭐ +{ofs}: matches expected_v3 (18,21,24,27) — DCHG step_num itself")
        elif (vals[1] - vals[0] == 3 and vals[2] - vals[1] == 3
              and vals[3] - vals[2] == 3 and 0 < vals[0] < 100):
            print(f"  +{ofs}: monotone delta=3, values={vals}")
    print()

    # ---- 4. Search for SOC 1% ref step in idx 27 ----
    print("== SOC 1% step (idx 27): scan for small uint32 values ==")
    print()
    soc_blk = read_step_block(data, soc_idx)
    print(f"  Looking for: typical CHG cluster start step_num (5, 10, 11, 16)")
    for cand in soc_candidates:
        hits = []
        for ofs in range(0, BLOCK_SIZE - 3, 4):
            v = struct.unpack_from('<I', soc_blk, ofs)[0]
            if v == cand:
                hits.append(ofs)
        print(f"  value {cand}: at offsets {hits}")
    print()

    # ---- 5. ref_kind / ref_basis enum candidates ----
    # All 4 DCHG-DOD steps + idx27 CHG-SOC step share:
    #   ref_step_kind (Char.) — should be same enum value across all 5
    #   ref_basis (AH) — should be same enum value across all 5
    print("== Search: offsets where all 5 ref-using steps have same uint32 value ==")
    print("  (potential ref_step_kind = 'Char.' or ref_basis = 'AH' enum)")
    print()
    all_blocks = [blk for _, _, _, blk in blocks] + [soc_blk]
    for ofs in range(0, BLOCK_SIZE - 3, 4):
        vals = [struct.unpack_from('<I', b, ofs)[0] for b in all_blocks]
        if (len(set(vals)) == 1 and vals[0] != 0
                and vals[0] not in (1, 2610, 4550, 105, 522)):  # filter common
            # Compare vs idx 0 (DCHG_CC INIT, no ref-step) — should differ
            init_blk = read_step_block(data, 0)
            v_init = struct.unpack_from('<I', init_blk, ofs)[0]
            if v_init != vals[0]:
                # Also check idx 4 (REST, no ref) and idx 18 (REST 1800s, no ref)
                rest1_blk = read_step_block(data, 18)
                v_rest = struct.unpack_from('<I', rest1_blk, ofs)[0]
                if v_rest != vals[0] or v_rest == 0:
                    print(f"  +{ofs}: all 5 = {vals[0]}, init={v_init}, "
                          f"rest18={v_rest}  ⭐ candidate enum")
    print()

    # ---- 6. ref pct_threshold (already +372) — verify ----
    print("== Verify pct_threshold field (+372) ==")
    print()
    for idx, expected, label, blk in blocks:
        v = struct.unpack_from('<f', blk, 372)[0]
        print(f"  {label}: +372 = {v} (expected 100.0)")
    soc_pct = struct.unpack_from('<f', soc_blk, 372)[0]
    print(f"  SOC step idx27: +372 = {soc_pct} (expected 1.0)")
    print()

    # ---- 6b. uint16 scan (ref_step might be 16-bit) ----
    print("== uint16 scan: 4 DCHG-DOD steps for expected step_num ==")
    print()
    expected_v1 = [17, 20, 23, 26]  # ref CHG step_num (preceding step)
    expected_v2 = [16, 19, 22, 25]
    expected_v3 = [18, 21, 24, 27]  # = own step_num
    for ofs in range(0, BLOCK_SIZE - 1, 2):
        vals = [struct.unpack_from('<H', blk, ofs)[0]
                for idx, expected, label, blk in blocks]
        if vals == expected_v1:
            print(f"  ⭐⭐⭐ +{ofs} (uint16): matches (17,20,23,26) — ref CHG step_num")
        elif vals == expected_v2:
            print(f"  ⭐⭐ +{ofs} (uint16): matches (16,19,22,25)")
        elif vals == expected_v3:
            print(f"  ⭐ +{ofs} (uint16): matches own step_num+1")
    print()

    # ---- 6c. unaligned uint32 scan — full byte-by-byte ----
    print("== Unaligned uint32 scan: 4 DCHG-DOD steps ==")
    print()
    matches_any = False
    for ofs in range(0, BLOCK_SIZE - 3):
        vals = [struct.unpack_from('<I', blk, ofs)[0]
                for idx, expected, label, blk in blocks]
        if vals == expected_v1:
            print(f"  ⭐⭐⭐ +{ofs} (unaligned uint32): matches (17,20,23,26)")
            matches_any = True
        elif vals == expected_v2:
            print(f"  ⭐⭐ +{ofs} (unaligned uint32): matches (16,19,22,25)")
            matches_any = True
    if not matches_any:
        print("  No unaligned uint32 match for ref CHG step_num.")
    print()

    # ---- 6d. uint8 scan (ref_step might fit in 1 byte) ----
    print("== uint8 scan: 4 DCHG-DOD steps ==")
    print()
    matches_any = False
    for ofs in range(0, BLOCK_SIZE):
        vals = [blk[ofs] for idx, expected, label, blk in blocks]
        if vals == expected_v1:
            print(f"  ⭐⭐⭐ +{ofs} (uint8): matches (17,20,23,26)")
            matches_any = True
        elif vals == expected_v2:
            print(f"  ⭐⭐ +{ofs} (uint8): matches (16,19,22,25)")
            matches_any = True
        elif vals == [v & 0xFF for v in expected_v3]:
            pass  # too noisy, +0 = step_num low byte
    if not matches_any:
        print("  No uint8 match for ref CHG step_num.")
    print()

    # ---- 6e. Search for ANY pattern with delta=3 in 4 steps (small values) ----
    print("== Pattern: 4 values with delta=3 (any base, uint8/uint16) ==")
    print()
    # uint16
    for ofs in range(0, BLOCK_SIZE - 1, 1):
        vals = [struct.unpack_from('<H', blk, ofs)[0]
                for idx, expected, label, blk in blocks]
        if (0 < vals[0] < 200
                and vals[1] - vals[0] == 3
                and vals[2] - vals[1] == 3
                and vals[3] - vals[2] == 3):
            print(f"  +{ofs} (uint16): values={vals} delta=3")
    # uint8
    for ofs in range(0, BLOCK_SIZE):
        vals = [blk[ofs] for idx, expected, label, blk in blocks]
        if (0 < vals[0] < 200
                and vals[1] - vals[0] == 3
                and vals[2] - vals[1] == 3
                and vals[3] - vals[2] == 3):
            print(f"  +{ofs} (uint8): values={vals} delta=3")
    print()

    # ---- 7. Search for jump_target = NEXT or step_num+1 ----
    # NEXT 의 binary 표현 추정: 0 (default) 또는 step_num+1
    # 우선 "step_num+1" 후보 탐색
    print("== Search: jump_target candidates (NEXT = 0 or step_num+1) ==")
    print()
    targets_step_plus1 = [18, 21, 24, 27, 28]  # step_num+1 for each ref step
    print("  Looking for values [18, 21, 24, 27, 28] across 5 ref steps:")
    for ofs in range(0, BLOCK_SIZE - 3, 4):
        vals = [struct.unpack_from('<I', b, ofs)[0] for b in all_blocks]
        if vals == targets_step_plus1:
            print(f"  ⭐ +{ofs}: matches step_num+1 — candidate jump_target")
    print()
    # NEXT = 0 case: all 5 should be 0 — too generic
    print("  All 5 = 0 case (NEXT default — too generic, skipped)")
    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
