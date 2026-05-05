"""DCIR sample 의 step type / EC type 전수 dump → 실제 ref-step 사용 step 식별."""
from __future__ import annotations

import struct
import sys
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

# Phase 0-4 sample
DCIR_PATH = EXP_ROOT / (
    "성능/250513_250526_05_나무늬_2610mAh_Gen5+B SDI MP1 Main SBR 0.9 DCIR/"
    "M01Ch037[037]/"
    "250513_250526_05_나무늬_2610mAh_Gen5+B SDI MP1 Main SBR 0.9 DCIR.sch"
)


def main() -> int:
    data = DCIR_PATH.read_bytes()
    n_steps = (len(data) - HEADER_SIZE) // BLOCK_SIZE
    print(f"File: {DCIR_PATH.name}")
    print(f"  n_steps: {n_steps}")
    print()
    print("idx | step# | type | +12/+16 (V) | +20 (I) | +24 (t) | "
          "+28 (Vend) | +32 (Iend) | +500 (EC) | +504 (en) | +372 (pct)")
    print('-' * 130)
    for i in range(n_steps):
        ofs = HEADER_SIZE + i * BLOCK_SIZE
        blk = data[ofs:ofs + BLOCK_SIZE]
        step_num = struct.unpack_from('<I', blk, 0)[0]
        type_code = struct.unpack_from('<I', blk, 8)[0]
        type_name = SCH_TYPE_MAP.get(type_code, f'UNK_0x{type_code:04X}')
        v12 = struct.unpack_from('<f', blk, 12)[0]
        v16 = struct.unpack_from('<f', blk, 16)[0]
        i20 = struct.unpack_from('<f', blk, 20)[0]
        t24 = struct.unpack_from('<f', blk, 24)[0]
        v28 = struct.unpack_from('<f', blk, 28)[0]
        i32 = struct.unpack_from('<f', blk, 32)[0]
        ec500 = struct.unpack_from('<I', blk, 500)[0]
        ec504 = struct.unpack_from('<I', blk, 504)[0]
        pct372 = struct.unpack_from('<f', blk, 372)[0]
        v_disp = v12 if 'CHG' in type_name and 'D' not in type_name else v16
        print(f"{i:3} | {step_num:3} | {type_name:12} | "
              f"{v_disp:6.1f} | {i20:8.2f} | {t24:6.0f} | "
              f"{v28:6.1f} | {i32:6.2f} | {ec500:5} | {ec504} | {pct372:.2f}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
