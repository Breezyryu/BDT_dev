"""187 .sch header lite extract — phase 0-2-α.

각 .sch 의 header 1920 bytes 만 read 해서 핵심 메타만 추출.
PNE 패턴 툴 (CTSEditor) 에서 직접 열어 cross-check 할 수 있도록
파일 path + schedule description + comment + user_category + dates 정리.

Usage:
    python sch_list_lite.py [root_dir]
    (default: C:\\Users\\Ryu\\battery\\python\\BDT_dev\\raw\\raw_exp\\exp_data)

Output:
    tools/sch_list_lite.csv  — UTF-8 CSV (excel 호환 BOM 포함)
    tools/sch_list_lite.md   — markdown table
"""
from __future__ import annotations

import csv
import struct
import sys
from pathlib import Path

HEADER_SIZE = 1920
BLOCK_SIZE = 652

DEFAULT_ROOT = r"C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data"


def _decode_string(b: bytes, ofs: int, max_len: int = 64) -> str:
    """offset 부터 null/non-printable 까지 ASCII 문자열 추출 (cp949 fallback)."""
    chunk = b[ofs:ofs + max_len]
    # ASCII 우선
    out = []
    for c in chunk:
        if 0x20 <= c <= 0x7E:
            out.append(chr(c))
        elif c == 0:
            break
        else:
            # ASCII 가 아니면 cp949 시도
            break
    ascii_text = ''.join(out).strip()
    if ascii_text and len(ascii_text) >= 3:
        return ascii_text

    # cp949 fallback
    try:
        # null 까지
        end = chunk.find(b'\x00')
        if end > 0:
            chunk = chunk[:end]
        return chunk.decode('cp949', errors='ignore').strip()
    except Exception:
        return ''


def _decode_korean(b: bytes, ofs: int, max_len: int = 32) -> str:
    """cp949 한글 우선 디코드."""
    chunk = b[ofs:ofs + max_len]
    end = chunk.find(b'\x00')
    if end > 0:
        chunk = chunk[:end]
    try:
        text = chunk.decode('cp949', errors='ignore').strip()
        # 한글 또는 ASCII printable 만 keep
        result = []
        for c in text:
            code = ord(c)
            if 0xAC00 <= code <= 0xD7A3 or 0x20 <= code <= 0x7E or code == ord('_'):
                result.append(c)
            elif result:
                break
        return ''.join(result).strip()
    except Exception:
        return ''


def parse_lite(sch_path: Path) -> dict | None:
    """Header lite 파싱 + first DCHG step 의 capacity_limit 추출."""
    try:
        with open(sch_path, 'rb') as f:
            data = f.read()
    except Exception as e:
        return {'error': str(e)}

    if len(data) < HEADER_SIZE + BLOCK_SIZE:
        return {'error': 'too_short'}

    # Magic 검증
    magic = struct.unpack_from('<I', data, 0)[0]
    if magic != 740721:
        return {'error': f'magic_mismatch_{magic}'}

    n_steps = (len(data) - HEADER_SIZE) // BLOCK_SIZE

    # Header field 추출
    user_category = _decode_korean(data, 336, max_len=32)
    schedule_desc = _decode_string(data, 664, max_len=64)
    comment = _decode_string(data, 728, max_len=32)
    created_at = _decode_korean(data, 587, max_len=24)
    modified_at = _decode_korean(data, 910, max_len=24)
    block_count_meta = struct.unpack_from('<I', data, 656)[0]

    # First non-LOOP step 의 capacity_limit
    capacity_limit = None
    for i in range(n_steps):
        ofs = HEADER_SIZE + i * BLOCK_SIZE
        type_code = struct.unpack_from('<I', data, ofs + 8)[0]
        if type_code in (0x0101, 0x0102, 0x0201, 0x0202, 0x0209):
            capacity_limit = round(
                struct.unpack_from('<f', data, ofs + 104)[0], 1)
            break

    return {
        'n_steps': n_steps,
        'file_size': len(data),
        'user_category': user_category,
        'schedule_description': schedule_desc,
        'comment': comment,
        'created_at': created_at,
        'modified_at': modified_at,
        'block_count_meta': block_count_meta,
        'capacity_limit_mAh': capacity_limit,
    }


def find_test_category(sch_path: Path, root: Path) -> str:
    """sch_path 의 시험종류 (성능/수명/...) 추출."""
    try:
        rel = sch_path.relative_to(root)
        return rel.parts[0] if rel.parts else 'UNKNOWN'
    except ValueError:
        return 'UNKNOWN'


def main(root_dir: str = DEFAULT_ROOT):
    root = Path(root_dir)
    if not root.exists():
        print(f"NOT FOUND: {root_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning {root} for .sch files...", file=sys.stderr)

    # 모든 .sch 찾기 (channel 폴더 안에 있음)
    sch_files = sorted(root.rglob('*.sch'))
    print(f"Found {len(sch_files)} .sch files.", file=sys.stderr)

    rows = []
    for i, sch_path in enumerate(sch_files):
        if i % 50 == 0 and i > 0:
            print(f"  [{i}/{len(sch_files)}]", file=sys.stderr)

        test_cat = find_test_category(sch_path, root)
        # folder name (시험 폴더, channel 한 단계 위)
        try:
            test_folder = sch_path.parent.parent.name
            channel = sch_path.parent.name
        except Exception:
            test_folder = ''
            channel = ''

        result = parse_lite(sch_path)
        rel_path = str(sch_path.relative_to(root)).replace('\\', '/')

        if result is None or 'error' in (result or {}):
            rows.append({
                'idx': i + 1,
                'test_category': test_cat,
                'test_folder': test_folder,
                'channel': channel,
                'sch_path': rel_path,
                'n_steps': '',
                'schedule_description': '',
                'comment': '',
                'user_category': '',
                'created_at': '',
                'modified_at': '',
                'block_count_meta': '',
                'capacity_limit_mAh': '',
                'error': (result or {}).get('error', 'unknown'),
            })
            continue

        rows.append({
            'idx': i + 1,
            'test_category': test_cat,
            'test_folder': test_folder,
            'channel': channel,
            'sch_path': rel_path,
            'n_steps': result['n_steps'],
            'schedule_description': result['schedule_description'],
            'comment': result['comment'],
            'user_category': result['user_category'],
            'created_at': result['created_at'],
            'modified_at': result['modified_at'],
            'block_count_meta': result['block_count_meta'],
            'capacity_limit_mAh': result.get('capacity_limit_mAh'),
            'error': '',
        })

    # CSV 저장 (UTF-8 BOM, Excel 호환)
    out_csv = Path(__file__).parent / 'sch_list_lite.csv'
    with open(out_csv, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows -> {out_csv}", file=sys.stderr)

    # Markdown table
    out_md = Path(__file__).parent / 'sch_list_lite.md'
    with open(out_md, 'w', encoding='utf-8') as f:
        f.write(f"# .sch parsed file list (n={len(rows)})\n\n")
        f.write(f"Source root: `{root}`\n\n")
        # 시험종류별 summary
        from collections import Counter
        cat_count = Counter(r['test_category'] for r in rows)
        f.write("## 시험종류별 분포\n\n")
        f.write("| 시험종류 | 파일 수 |\n|---|---|\n")
        for cat, n in sorted(cat_count.items()):
            f.write(f"| {cat} | {n} |\n")
        f.write(f"\n**합계**: {len(rows)}\n\n")

        f.write("## File list (path + 시험명)\n\n")
        f.write("| # | 시험종류 | n_steps | Schedule description (+664) | Comment (+728) | User category (+336) | Capacity (mAh) | Path |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            desc = (r['schedule_description'] or '').replace('|', '\\|')
            cmt = (r['comment'] or '').replace('|', '\\|')
            user = (r['user_category'] or '').replace('|', '\\|')
            cap = r['capacity_limit_mAh'] or ''
            f.write(
                f"| {r['idx']} | {r['test_category']} | {r['n_steps']} | "
                f"`{desc}` | `{cmt}` | `{user}` | {cap} | `{r['sch_path']}` |\n"
            )
    print(f"Wrote markdown -> {out_md}", file=sys.stderr)
    print('Done.', file=sys.stderr)


if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROOT
    main(root)
