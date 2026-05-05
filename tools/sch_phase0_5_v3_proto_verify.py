"""proto 본체에 적용된 v3 분류기를 직접 호출해 187 폴더 분류 결과 검증.

self-contained batch (sch_phase0_5_v3_classify.py) 와 결과가 일치하는지 비교.
"""
from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from pathlib import Path

# proto 모듈 import
PROTO_DIR = Path(__file__).parent.parent / 'DataTool_dev_code'
sys.path.insert(0, str(PROTO_DIR))

# Heavy import — proto 의 분류기 함수 사용
import importlib.util
spec = importlib.util.spec_from_file_location(
    'proto', PROTO_DIR / 'DataTool_optRCD_proto_.py')
proto = importlib.util.module_from_spec(spec)
# Import error 방지: GUI 의존성 import 시 실패할 수 있으므로 분류 함수만 추출
# 직접 source 에서 함수 추출
import struct

EXP_ROOT = Path(r"C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data")
OUT_DIR = Path(__file__).parent

# proto 의 _parse_pne_sch / _classify_loop_group / _decompose_loop_groups /
# _expand_groups_with_outer_goto / _build_loop_group_info 만 추출 실행

# 빠른 검증: source 에서 해당 함수만 exec
PROTO_FILE = PROTO_DIR / 'DataTool_optRCD_proto_.py'
src = PROTO_FILE.read_text(encoding='utf-8')

# 필요한 모듈만 namespace 에 주입
ns = {
    'struct': struct,
    'open': open,
}

# 필요한 일부 dataclass 의존 안 하도록 분류 관련 부분만 추출
# 가장 안전한 방법: ast 로 함수 추출
import ast
tree = ast.parse(src)

# 추출할 함수 / 변수 목록
WANTED_NAMES = {
    '_SCH_TYPE_MAP', '_SCH_CHG_TYPES', '_SCH_DCHG_TYPES', '_SCH_GITT_TYPES',
    '_SCH_BLOCK_SIZE', '_SCH_HEADER_SIZE',
    '_parse_pne_sch', '_decompose_loop_groups', '_expand_groups_with_outer_goto',
    '_classify_loop_group', '_build_loop_group_info',
    '_step_v_cutoff_mV', '_schedule_desc_keyword',
    '_merge_hysteresis_envelopes', '_is_compatible_with_hyst_envelope',
}

# 함수/할당 노드 추출
extracted_nodes = []
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in WANTED_NAMES:
        extracted_nodes.append(node)
    elif isinstance(node, ast.Assign):
        for tgt in node.targets:
            if isinstance(tgt, ast.Name) and tgt.id in WANTED_NAMES:
                extracted_nodes.append(node)
                break
    elif isinstance(node, ast.AnnAssign):
        if isinstance(node.target, ast.Name) and node.target.id in WANTED_NAMES:
            extracted_nodes.append(node)

mini_module = ast.Module(body=extracted_nodes, type_ignores=[])
mini_code = compile(mini_module, str(PROTO_FILE), 'exec')
exec(mini_code, ns)

print(f"Extracted {len(extracted_nodes)} nodes from proto", file=sys.stderr)
print(f"WANTED present: {sorted(set(WANTED_NAMES) & set(ns.keys()))}",
      file=sys.stderr)

_parse_pne_sch = ns['_parse_pne_sch']
_build_loop_group_info = ns['_build_loop_group_info']

# capacity from folder name
_CAP_PATTERN = re.compile(r'(\d+)\s*mAh', re.IGNORECASE)


def extract_capacity(name: str) -> float:
    m = _CAP_PATTERN.search(name)
    if m:
        try:
            v = float(m.group(1))
            if 100 <= v <= 100000:
                return v
        except ValueError:
            pass
    return 0.0


def main() -> int:
    sch_files = sorted(EXP_ROOT.rglob('*.sch'))
    print(f"Scanning {len(sch_files)} .sch files...", file=sys.stderr)

    cat_counter: Counter = Counter()
    total_groups = 0
    failed = []
    rows = []

    for fi, p in enumerate(sch_files):
        if fi % 50 == 0 and fi > 0:
            print(f"  [{fi}/{len(sch_files)}]", file=sys.stderr)
        try:
            rel = p.relative_to(EXP_ROOT)
        except ValueError:
            rel = p
        parts = rel.parts
        exp_folder = parts[1] if len(parts) >= 2 else parts[0]
        capacity = extract_capacity(exp_folder)

        parsed = _parse_pne_sch(str(p))
        if parsed is None:
            failed.append(str(rel))
            continue
        if capacity == 0:
            for s in parsed['steps']:
                cl = s.get('capacity_limit_mAh', 0)
                if cl and cl > 0:
                    capacity = cl
                    break

        groups = _build_loop_group_info(parsed, capacity)
        for g in groups:
            cat_counter[g['category']] += 1
            total_groups += 1
            rows.append({
                'rel_path': str(rel),
                'exp_folder': exp_folder,
                'capacity_mAh': capacity,
                'tc_start': g['tc_start'],
                'tc_end': g['tc_end'],
                'loop_count': g['loop_count'],
                'category': g['category'],
                'chg_crate': g.get('chg_crate'),
                'dchg_crate': g.get('dchg_crate'),
            })

    print(f"\nTotal groups: {total_groups}", file=sys.stderr)
    print(f"Failed: {len(failed)}", file=sys.stderr)
    print(f"\nCategory distribution (proto v3):", file=sys.stderr)
    for c, n in cat_counter.most_common():
        print(f"  {c}: {n}", file=sys.stderr)

    # CSV
    csv_out = OUT_DIR / 'proto_v3_groups.csv'
    with open(csv_out, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {csv_out}", file=sys.stderr)

    return 0


if __name__ == '__main__':
    sys.exit(main())
