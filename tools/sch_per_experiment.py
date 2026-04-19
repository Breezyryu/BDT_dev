"""실험 폴더별로 .sch 분류 + 240919 SOC별DCIR 케이스 집중 분석.
parse_all_sch.py 의 파서·분류기를 재사용하되, 그룹핑 키를 실험 폴더(parts[0]/parts[1])로 바꿔서 돌림.
"""
import sys
import io
from pathlib import Path
from collections import Counter, defaultdict

# 파서·분류기 재사용
sys.path.insert(0, r'C:\Users\Ryu\battery\python\BDT_dev\.claude\worktrees\jovial-sinoussi-e0059e')
from parse_all_sch import parse_sch, split_into_loop_groups, classify_loop_group, format_group_body

BASE = Path(r'c:\Users\Ryu\battery\python\BDT_dev\DataTool_dev_code\data\exp_data')

# 실험별 집계: key = (top, experiment), value = list of sch paths
exp_map = defaultdict(list)
for sp in sorted(BASE.rglob('*.sch')):
    parts = sp.relative_to(BASE).parts
    if len(parts) < 3:
        continue
    top = parts[0]
    exp = parts[1]
    exp_map[(top, exp)].append(sp)

print(f'총 실험 폴더 수: {len(exp_map)}')
print(f'총 .sch 파일 수: {sum(len(v) for v in exp_map.values())}')
print()

category_counter = Counter()
failure_cases = []  # experiments with any UNKNOWN
composite_cases = []  # experiments with >= 3 distinct categories
per_exp_summary = []

# 간결 요약 + 실패/복합 케이스 검출
for (top, exp), schs in sorted(exp_map.items()):
    # 첫 sch 를 대표로 사용 (변형 _000, _001 은 LOOP 카운트만 다름)
    rep_sch = None
    for s in schs:
        if '_0' not in s.name:  # 원본 우선
            rep_sch = s
            break
    if rep_sch is None:
        rep_sch = schs[0]

    steps = parse_sch(rep_sch)
    if steps is None:
        per_exp_summary.append((top, exp, None, None, None, 'PARSE_FAIL'))
        continue

    groups = split_into_loop_groups(steps)
    total_loops = len(groups)
    cats = []
    total_tc = 0
    for idx, g in enumerate(groups):
        cat = classify_loop_group(g['body'], g['loop_count'], idx, total_loops)
        cats.append((cat, g['loop_count']))
        total_tc += g['loop_count']
        category_counter[cat] += 1

    cat_set = set(c for c, _ in cats)
    per_exp_summary.append((top, exp, len(cats), total_tc, cats, ','.join(sorted(cat_set))))

    if 'UNKNOWN' in cat_set:
        failure_cases.append((top, exp, cats))
    if len(cat_set) >= 4:
        composite_cases.append((top, exp, cats))

# ─── 결과 1: 카테고리 분포 ───
print('=' * 70)
print('[1] 카테고리 분포 (loop group 단위)')
print('=' * 70)
for cat, cnt in category_counter.most_common():
    print(f'  {cat:<20} {cnt:>5}')

# ─── 결과 2: UNKNOWN 발생 케이스 ───
print()
print('=' * 70)
print(f'[2] UNKNOWN 발생 실험 ({len(failure_cases)}건)')
print('=' * 70)
for top, exp, cats in failure_cases:
    print(f'  [{top}] {exp}')
    for cat, n in cats:
        marker = ' ★' if cat == 'UNKNOWN' else ''
        print(f'      {cat:<18} N={n}{marker}')

# ─── 결과 3: 복합(≥4 카테고리) 케이스 ───
print()
print('=' * 70)
print(f'[3] 복합 프로파일 실험 (≥4 카테고리, {len(composite_cases)}건)')
print('=' * 70)
for top, exp, cats in composite_cases[:20]:
    cat_seq = ' → '.join(f'{c}({n})' for c, n in cats)
    print(f'  [{top}] {exp[:60]}')
    print(f'      {cat_seq}')

# ─── 결과 4: 240919 SOC별DCIR 집중 분석 ───
print()
print('=' * 70)
print('[4] 240919 SOC별DCIR 케이스 상세')
print('=' * 70)
target_schs = [s for (top, exp), lst in exp_map.items()
               if '240919' in exp and 'SOC' in exp for s in lst]
if not target_schs:
    print('  (파일 없음)')
else:
    for sp in target_schs:
        print(f'\n--- {sp.name} ---')
        steps = parse_sch(sp)
        if steps is None:
            print('  파싱 실패')
            continue
        groups = split_into_loop_groups(steps)
        total_loops = len(groups)
        tc_cur = 1
        for idx, g in enumerate(groups):
            cat = classify_loop_group(g['body'], g['loop_count'], idx, total_loops)
            n = g['loop_count']
            body = format_group_body(g['body'])
            tc_str = f'TC {tc_cur}' if n == 1 else f'TC {tc_cur}-{tc_cur + n - 1} ({n})'
            print(f'  #{idx+1:<2} {cat:<18} {tc_str}')
            print(f'       {body}')
            tc_cur += n
        print(f'  총 스텝 {len(steps)} / 총 loop 그룹 {total_loops} / 총 TC {tc_cur - 1}')

# ─── 결과 5: 전체 요약 테이블 ───
print()
print('=' * 70)
print('[5] 실험 전체 요약 (카테고리 다양성 순)')
print('=' * 70)
sorted_exps = sorted(per_exp_summary, key=lambda r: (-len(set(c for c, _ in (r[4] or []))), r[0], r[1]))
for top, exp, n_groups, total_tc, cats, cat_label in sorted_exps[:30]:
    if cats is None:
        print(f'  [{top}] {exp[:55]:<55}  PARSE_FAIL')
        continue
    n_distinct = len(set(c for c, _ in cats))
    print(f'  [{top}] {exp[:55]:<55}  grp={n_groups} TC={total_tc} ndist={n_distinct} ({cat_label})')

print()
print(f'(상위 30개만 표시, 총 {len(per_exp_summary)}건)')
