"""PNE .sch binary dump — Phase 0-1 audit (사용자 명시 작업).

목적: parser 가 무시하는 ~588 bytes / step + 1916 bytes header 의
모든 식별 가능 field 를 list-up.

Usage:
    python sch_dump.py <sch_path>
    python sch_dump.py --all          # 5개 sample 종합
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

HEADER_SIZE = 1920
BLOCK_SIZE = 652


def try_decode_strings(b: bytes, min_len: int = 4) -> list[tuple[int, str, str]]:
    """ASCII / UTF-16-LE / CP949 string 후보 추출.

    Returns: list of (offset, encoding, text)
    """
    out = []
    # ASCII printable 연속 chunk
    cur_start = -1
    cur = []
    for i, c in enumerate(b):
        if 0x20 <= c <= 0x7E:
            if cur_start < 0:
                cur_start = i
            cur.append(chr(c))
        else:
            if cur_start >= 0 and len(cur) >= min_len:
                out.append((cur_start, 'ascii', ''.join(cur)))
            cur_start = -1
            cur = []
    if cur_start >= 0 and len(cur) >= min_len:
        out.append((cur_start, 'ascii', ''.join(cur)))

    # UTF-16-LE: 짝수 offset 부터, char 가 ASCII 이거나 한글 영역
    i = 0
    while i < len(b) - 1:
        if i % 2 == 1:
            i += 1
            continue
        try:
            cluster_start = i
            chars = []
            while i < len(b) - 1:
                lo = b[i]
                hi = b[i + 1]
                code = lo | (hi << 8)
                if (0x20 <= code <= 0x7E) or (0xAC00 <= code <= 0xD7A3) or code == 0x0020:
                    chars.append(chr(code))
                    i += 2
                else:
                    break
            if len(chars) >= min_len:
                text = ''.join(chars)
                # 너무 짧거나 ASCII-only 인 utf16 후보는 ASCII 가 잡았을 것 → skip
                if any(0xAC00 <= ord(c) <= 0xD7A3 for c in text) or len(text) >= 8:
                    out.append((cluster_start, 'utf16le', text))
            else:
                i += 2
        except Exception:
            i += 2

    # CP949 한글 (ASCII 깨진 결과의 원본 추정) — 조각만 빠르게
    try:
        decoded = b.decode('cp949', errors='ignore')
        if decoded.strip():
            # 한글 chunk 추출
            cur = []
            cur_idx = -1
            for j, ch in enumerate(decoded):
                code = ord(ch)
                if 0xAC00 <= code <= 0xD7A3 or 0x20 <= code <= 0x7E:
                    if not cur:
                        cur_idx = j
                    cur.append(ch)
                else:
                    if len(cur) >= min_len:
                        text = ''.join(cur).strip()
                        if any(0xAC00 <= ord(c) <= 0xD7A3 for c in text):
                            out.append((cur_idx, 'cp949', text))
                    cur = []
            if len(cur) >= min_len:
                text = ''.join(cur).strip()
                if any(0xAC00 <= ord(c) <= 0xD7A3 for c in text):
                    out.append((cur_idx, 'cp949', text))
    except Exception:
        pass

    return out


def dump_uint32_pattern(b: bytes, prefix: str = "") -> list[tuple[int, int, float]]:
    """4-byte aligned uint32/float32 후보 dump (비0 만)."""
    out = []
    for i in range(0, len(b) - 3, 4):
        u = struct.unpack_from('<I', b, i)[0]
        if u == 0:
            continue
        f = struct.unpack_from('<f', b, i)[0]
        out.append((i, u, f))
    return out


def analyze_header(data: bytes, label: str = "") -> dict:
    """Header 1920 bytes 분석."""
    if len(data) < HEADER_SIZE:
        return {'error': 'too short'}

    hdr = data[:HEADER_SIZE]
    print(f"\n{'='*80}")
    print(f"HEADER ANALYSIS — {label}")
    print(f"{'='*80}")
    print(f"Size: {len(hdr)} bytes")

    # Magic
    magic = struct.unpack_from('<I', hdr, 0)[0]
    print(f"\n[+0] Magic: {magic} (expect 740721 = 0x{740721:X})")

    # Strings
    print(f"\n[STRING FIELDS — header]")
    strings = try_decode_strings(hdr, min_len=4)
    seen = set()
    for ofs, enc, text in sorted(strings, key=lambda x: x[0]):
        key = (ofs // 4, text[:30])
        if key in seen:
            continue
        seen.add(key)
        text_disp = text if len(text) < 80 else text[:77] + '...'
        print(f"  +{ofs:5d} ({enc:8s}) {text_disp!r}")

    # 비0 uint32/float 영역 (첫 32 entry)
    print(f"\n[NON-ZERO uint32/float — header, first 32]")
    non_zero = dump_uint32_pattern(hdr)
    for i, (ofs, u, f) in enumerate(non_zero[:32]):
        # float plausible range
        f_disp = f"{f:.3g}" if abs(f) < 1e10 and abs(f) > 1e-10 else "—"
        print(f"  +{ofs:5d}  uint32={u:12d}  float={f_disp}")

    return {'strings': strings, 'non_zero': non_zero, 'magic': magic}


def analyze_step_block(data: bytes, idx: int, label: str = "") -> dict:
    """Single step block 652 bytes 분석."""
    ofs = HEADER_SIZE + idx * BLOCK_SIZE
    if ofs + BLOCK_SIZE > len(data):
        return {'error': 'out of range'}

    blk = data[ofs:ofs + BLOCK_SIZE]
    print(f"\n{'='*80}")
    print(f"STEP BLOCK [{idx}] — {label}")
    print(f"{'='*80}")
    print(f"Block offset: +{ofs}")

    # Known fields
    step_num = struct.unpack_from('<I', blk, 0)[0]
    type_code = struct.unpack_from('<I', blk, 8)[0]
    print(f"\n[KNOWN FIELDS]")
    print(f"  +0   step_number     = {step_num}")
    print(f"  +8   type_code       = 0x{type_code:04X}")

    # 모든 4-byte aligned uint32/float 비0 dump
    print(f"\n[NON-ZERO uint32/float — block, all]")
    non_zero = dump_uint32_pattern(blk)
    for ofs_in_blk, u, f in non_zero:
        f_disp = f"{f:.4g}" if abs(f) < 1e10 and abs(f) > 1e-10 else "—"
        # heuristic interpretation
        hint = ''
        if ofs_in_blk == 0:
            hint = '<- step_number'
        elif ofs_in_blk == 8:
            hint = '<- type_code'
        elif ofs_in_blk == 12:
            hint = '<- voltage_mV (CHG)'
        elif ofs_in_blk == 16:
            hint = '<- voltage_mV (DCHG)'
        elif ofs_in_blk == 20:
            hint = '<- current_mA'
        elif ofs_in_blk == 24:
            hint = '<- time_limit_s'
        elif ofs_in_blk == 28:
            hint = '<- end_voltage_mV'
        elif ofs_in_blk == 32:
            hint = '<- end_current_mA'
        elif ofs_in_blk == 52:
            hint = '<- goto_target_step (LOOP)'
        elif ofs_in_blk == 56:
            hint = '<- loop_count / goto_target'
        elif ofs_in_blk == 104:
            hint = '<- capacity_limit_mAh'
        elif ofs_in_blk == 336:
            hint = '<- record_interval_s (?)'
        elif ofs_in_blk == 372:
            hint = '<- end_condition_value_pct'
        elif ofs_in_blk == 500:
            hint = '<- end_condition_type'
        elif ofs_in_blk == 504:
            hint = '<- end_condition_enabled'
        elif ofs_in_blk == 580:
            hint = '<- goto_repeat_count (LOOP)'
        else:
            hint = '?? UNKNOWN ??'
        print(f"  +{ofs_in_blk:3d}  uint32={u:12d}  float={f_disp:>12s}  {hint}")

    # Block 안 string (일부 PNE 는 step description 가능)
    strings = try_decode_strings(blk, min_len=4)
    if strings:
        print(f"\n[STRING IN BLOCK]")
        seen = set()
        for s_ofs, enc, text in strings:
            key = (s_ofs // 4, text[:20])
            if key in seen:
                continue
            seen.add(key)
            text_disp = text if len(text) < 60 else text[:57] + '...'
            print(f"  +{s_ofs:3d} ({enc:8s}) {text_disp!r}")

    return {'step_num': step_num, 'type_code': type_code, 'non_zero': non_zero}


def main(paths: list[str]):
    for p in paths:
        path = Path(p)
        if not path.exists():
            print(f"NOT FOUND: {p}")
            continue
        with open(path, 'rb') as f:
            data = f.read()

        label = path.parent.parent.name + ' / ' + path.name
        print(f"\n\n{'#'*80}\n# FILE: {label}\n# Size: {len(data)} bytes")
        print(f"# n_steps = {(len(data) - HEADER_SIZE) // BLOCK_SIZE}")
        print('#' * 80)

        analyze_header(data, label=label)
        # First 3 step blocks
        n_steps = (len(data) - HEADER_SIZE) // BLOCK_SIZE
        for i in [0, 1, min(2, n_steps - 1)]:
            if i < n_steps:
                analyze_step_block(data, i, label=label)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1:])
    else:
        # 5 시험종류 sample
        samples = [
            r"C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\성능_hysteresis\260202_260210_05_현혜정_4875mAh_LWN Gen5 MP1-1 0.5C hysteresis\M01Ch022[022]\260202_260210_05_현혜정_4875mAh_LWN Gen5 MP1-1 0.5C hysteresis.sch",
            r"C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\수명_복합floating\250116_250501_05_김영환_4905mAh_ATL Gen5 4C HT floating\M01Ch049[049]\250116_250501_05_김영환_4905mAh_ATL Gen5 4C HT floating.sch",
            r"C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\성능\240821 선행랩 류성택 Gen4pGr mini-ATL-WD-Proto-422mAh-20C-450V-GITT-15도\M01Ch005[005]\240821 선행랩 류성택 Gen4pGr ATL-Mini-422mAh-GITT-15도.sch",
            r"C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\수명\251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202\M01Ch008[008]\251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202.sch",
        ]
        main(samples)
