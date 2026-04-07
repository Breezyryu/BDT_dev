"""ECT 경로 파일 파싱 호환성 검증 스크립트
# -*- coding: utf-8 -*-

구버전(260204) ect_confirm_button과 현재버전(proto_)의 파싱 결과를 비교하여
동일한 파라미터가 pne_Profile_continue_data에 전달되는지 확인한다.

사용법:
    python tests/verify_ect_path_compat.py
"""
import re
import numpy as np
import pandas as pd
from pathlib import Path

# ── 경로 설정 ──
BASE = Path(__file__).resolve().parent.parent
OLD_FILE = BASE / "data" / "exp_data" / "path_ECT_PA2 SDI ECT 파라미터 추출 250929.txt"
NEW_FILE = BASE / "data" / "exp_data" / "path_ECT_PA2 SDI ECT 파라미터 추출 250929_v2.txt"


# ============================================================
# 1. 구버전 파싱 (260204 ect_confirm_button 로직 재현)
# ============================================================
def parse_old_format(filepath: Path) -> list[dict]:
    """구버전(260204)의 ect_confirm_button 파싱 로직 재현.

    pd.read_csv → cycle_path.path / cycle_path.cycle / cycle_path.CD / cycle_path.save
    """
    cycle_path = pd.read_csv(
        filepath, sep="\t", engine="c", encoding="UTF-8",
        skiprows=1, on_bad_lines='skip')
    ect_path = np.array(cycle_path.path.tolist())
    ect_cycle = np.array(cycle_path.cycle.tolist())
    ect_CD = np.array(cycle_path.CD.tolist())
    ect_save = np.array(cycle_path.save.tolist())

    results = []
    for i in range(len(ect_path)):
        # 구버전: ect_cycle[i].split(" ")
        cycle_str = str(ect_cycle[i]).strip()
        chg_dchg_dcir_no = list(cycle_str.split(" "))
        for step in chg_dchg_dcir_no:
            if "-" in step:
                s, e = map(int, step.split("-"))
            else:
                s, e = int(step), int(step)
            results.append({
                'path': str(ect_path[i]).strip(),
                'cycle_start': s,
                'cycle_end': e,
                'cd': str(ect_CD[i]).strip(),
                'save': str(ect_save[i]).strip(),
            })
    return results


# ============================================================
# 2. 현재버전 파싱 (proto_ ect_confirm_button 로직 재현)
# ============================================================

# _HEADER_ALIASES 재현
_HEADER_ALIASES = {
    'cyclename': 'name', 'name': 'name', 'save': 'name', 'pathname': 'name',
    'cyclepath': 'path', 'path': 'path',
    'channel': 'channel', 'ch': 'channel',
    'cycle': 'cycle', '사이클': 'cycle',
    'cd': 'mode', 'mode': 'mode', '모드': 'mode',
    'capacity': 'capacity', 'cap': 'capacity',
    'cycleraw': 'cycleraw', 'totlcycle': 'cycleraw', 'totl_cycle': 'cycleraw',
}
_ECT_HEADER_KEYS_BASE = {'cd', 'save'}
_ECT_HEADER_CYCLE_KEYS = {'cycle', 'totlcycle'}


def _detect_columns(header_line: str) -> tuple[dict, bool]:
    cols = [c.strip().lower() for c in header_line.rstrip('\n\r').split('\t')]
    mapping = {'name': None, 'path': None, 'channel': None,
               'capacity': None, 'cycle': None, 'cycleraw': None, 'mode': None}
    matched = False
    for idx, col in enumerate(cols):
        key = _HEADER_ALIASES.get(col)
        if key:
            mapping[key] = idx
            matched = True
    if mapping['path'] is None:
        mapping['path'] = 0
    return mapping, matched


def parse_new_format(filepath: Path) -> list[dict]:
    """현재버전(proto_)의 _load_path_file_to_table + ect_confirm_button 파싱 재현."""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        all_lines = f.readlines()

    # 메타데이터 + 헤더 탐색
    header_idx = None
    ect_mode = None
    for i, raw in enumerate(all_lines):
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith('#ect_mode='):
            ect_mode = stripped.split('=', 1)[1].strip() == '1'
            continue
        if stripped.startswith('#'):
            continue
        header_idx = i
        break

    if header_idx is None:
        return []

    header_line = all_lines[header_idx]
    col_map, is_header = _detect_columns(header_line)
    data_start = header_idx + 1 if is_header else header_idx

    # 데이터 파싱
    rows = []
    for line in all_lines[data_start:]:
        if not line.strip():
            continue
        parts = [p.strip().strip('"').strip("'")
                 for p in line.rstrip('\n\r').split('\t')]
        path = parts[col_map['path']] if col_map['path'] < len(parts) else ''
        name = parts[col_map['name']] if col_map['name'] is not None and col_map['name'] < len(parts) else ''
        cycle = parts[col_map['cycle']] if col_map['cycle'] is not None and col_map['cycle'] < len(parts) else ''
        cycleraw = parts[col_map['cycleraw']] if col_map['cycleraw'] is not None and col_map['cycleraw'] < len(parts) else ''
        mode = parts[col_map['mode']] if col_map['mode'] is not None and col_map['mode'] < len(parts) else ''
        if path:
            rows.append({'name': name, 'path': path, 'cycle': cycle,
                         'cycleraw': cycleraw, 'mode': mode})

    # ECT 호환: cycle → cycleraw 이동 (구형 파일에서 cycle만 있을 때)
    _header_cols_lower = set(
        c.strip().lower() for c in header_line.rstrip('\n\r').split('\t'))
    is_ect = (ect_mode is True) or (
        is_header
        and _ECT_HEADER_KEYS_BASE.issubset(_header_cols_lower)
        and bool(_header_cols_lower & _ECT_HEADER_CYCLE_KEYS))

    if is_ect:
        _has_cycleraw_col = col_map.get('cycleraw') is not None
        if not _has_cycleraw_col:
            for row in rows:
                if row.get('cycle') and not row.get('cycleraw'):
                    row['cycleraw'] = row['cycle']
                    row['cycle'] = ''

    # ect_confirm_button 시뮬레이션: cycleraw 파싱
    results = []
    for row in rows:
        cycle_str = str(row['cycleraw']).strip()
        chg_dchg_dcir_no = [s.strip() for s in re.split(r'[,\s]+', cycle_str) if s.strip()]
        for step in chg_dchg_dcir_no:
            if "-" in step:
                s, e = map(int, step.split("-"))
            else:
                s, e = int(step), int(step)
            results.append({
                'path': row['path'],
                'cycle_start': s,
                'cycle_end': e,
                'cd': row['mode'],
                'save': row['name'],
            })
    return results


# ============================================================
# 3. 비교 실행
# ============================================================
def compare_results(old_results: list[dict], new_results: list[dict]) -> bool:
    """두 파싱 결과의 동일성 비교."""
    if len(old_results) != len(new_results):
        print(f"  ❌ 행 수 불일치: 구버전={len(old_results)}, 현재버전={len(new_results)}")
        return False

    all_match = True
    for i, (old, new) in enumerate(zip(old_results, new_results)):
        mismatches = []
        for key in ['path', 'cycle_start', 'cycle_end', 'cd', 'save']:
            # 경로 끝의 \ 유무 차이 무시
            oval = str(old[key]).rstrip('\\')
            nval = str(new[key]).rstrip('\\')
            if oval != nval:
                mismatches.append(f"  {key}: '{old[key]}' vs '{new[key]}'")
        if mismatches:
            all_match = False
            print(f"  ❌ Row {i}: {old['save']}")
            for m in mismatches:
                print(m)
    return all_match


def main():
    print("=" * 70)
    print("ECT 경로 파일 파싱 호환성 검증")
    print("=" * 70)

    # ── Test 1: 구형 파일을 구버전 로직으로 파싱 ──
    print("\n[1] 구형 파일 → 구버전 파싱")
    old_from_old = parse_old_format(OLD_FILE)
    print(f"    파싱 결과: {len(old_from_old)}건")

    # ── Test 2: 구형 파일을 현재버전 로직으로 파싱 (하위호환) ──
    print("\n[2] 구형 파일 → 현재버전 파싱 (하위호환 테스트)")
    new_from_old = parse_new_format(OLD_FILE)
    print(f"    파싱 결과: {len(new_from_old)}건")

    print("\n    [비교] 구형파일: 구버전 vs 현재버전")
    if compare_results(old_from_old, new_from_old):
        print("    ✅ 완전 일치 — 하위호환 정상")
    else:
        print("    ⚠️  불일치 발견")

    # ── Test 3: 신형 파일을 현재버전 로직으로 파싱 ──
    print(f"\n[3] 신형 파일(v2) → 현재버전 파싱")
    new_from_new = parse_new_format(NEW_FILE)
    print(f"    파싱 결과: {len(new_from_new)}건")

    print("\n    [비교] 구버전 원본 vs 신형파일")
    if compare_results(old_from_old, new_from_new):
        print("    ✅ 완전 일치 — 신형 파일 변환 정상")
    else:
        print("    ⚠️  불일치 발견")

    # ── 상세 출력 (처음 5건) ──
    print("\n" + "-" * 70)
    print("상세 비교 (처음 5건)")
    print("-" * 70)
    fmt = "{:>3} | {:35} | {:>6}-{:<6} | {:>5} | {:35}"
    print(fmt.format("#", "save", "start", "end", "CD", "path (마지막 30자)"))
    print("-" * 120)
    for i, r in enumerate(old_from_old[:5]):
        path_short = r['path'][-30:] if len(r['path']) > 30 else r['path']
        print(fmt.format(i, r['save'], r['cycle_start'], r['cycle_end'],
                         r['cd'], path_short))

    print("\n" + "=" * 70)
    print("검증 완료")


if __name__ == "__main__":
    main()
