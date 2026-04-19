"""Phase 0 — 신 9종 카테고리 + 서브태그 결정트리 프로토타입.

입력: exp_data/ 하위 모든 .sch 파일
출력:
  - 전체 카테고리 분포
  - UNKNOWN 남은 패턴
  - 기존(14종) → 신(9종) 매핑 비교

재사용: parse_all_sch.py 의 parse_sch, split_into_loop_groups, format_group_body
"""
import sys
import io
import re
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, r'C:\Users\Ryu\battery\python\BDT_dev\.claude\worktrees\jovial-sinoussi-e0059e')
from parse_all_sch import parse_sch, split_into_loop_groups, format_group_body, classify_loop_group as OLD_CLASSIFY

BASE = Path(r'c:\Users\Ryu\battery\python\BDT_dev\DataTool_dev_code\data\exp_data')

EC_DOD = 2048         # 0x0800
EC_SOC = 16384        # 0x4000
EC_SOC_CHG = 18432    # 0x4800
EC_CAP = 1024         # 0x0400
EC_VOL = 512          # 0x0200


def classify_new(body_steps, loop_count, position, total_loops):
    """9종 + 서브태그 결정트리. 반환 (category, subtag|None)."""
    N = loop_count
    n_steps = len(body_steps)
    if n_steps == 0:
        return ('UNKNOWN', None)

    types = [s['type'] for s in body_steps]
    type_set = set(types)
    chg_count = sum(1 for t in types if t.startswith('CHG'))
    dchg_count = sum(1 for t in types if t.startswith('DCHG'))
    has_chg_cp = 'CHG_CP' in type_set
    has_unk_step = any(t.startswith('UNK_') for t in types)
    ec_steps = [s for s in body_steps if s.get('ec_enabled', 0) > 0]
    n_ec = len(ec_steps)
    ec_types = [s.get('ec_type', 0) for s in ec_steps]
    rest_steps = [s for s in body_steps if s['type'] == 'REST']
    max_rest_time = max((s.get('time_limit', 0) for s in rest_steps), default=0)
    first_rest_time = body_steps[0].get('time_limit', 0) if types and types[0] == 'REST' else 0

    # 긴 DCHG_CC (≥3h) 여부 (저장준비 판별)
    long_dchg = any(
        s['type'] == 'DCHG_CC' and s.get('time_limit', 0) >= 10800
        for s in body_steps
    )
    max_dchg_time = max(
        (s.get('time_limit', 0) for s in body_steps if s['type'].startswith('DCHG')),
        default=0,
    )

    # Rule 1 — EC 기반
    if N == 1 and ec_steps:
        # 히스테리시스 충전/방전 (EC=SOC_CHG 또는 DOD 단일 사용)
        if any(et == EC_SOC_CHG for et in ec_types) and any(
            s['type'].startswith('CHG') for s in ec_steps
        ):
            return ('히스테리시스', '충전')
        if any(et == EC_DOD for et in ec_types) and any(
            s['type'].startswith('DCHG') for s in ec_steps
        ):
            return ('히스테리시스', '방전')

    # SOC별 사이클 — EC 타입 다양성 ≥3 (각 SOC 마다 다른 type 인코딩) + N < 20
    # (N≥20 은 가속수명 우선 — Rule 4 에서 처리)
    ec_types_distinct = {s.get('ec_type', 0) for s in ec_steps}
    if 5 <= N < 20 and n_ec >= 4 and n_steps >= 8 and len(ec_types_distinct) >= 3:
        return ('SOC별 사이클', None)

    # Rule 2 — GITT (펄스 + 긴 REST × 다수반복, 스텝 순서 무관)
    # - full GITT: 전류 소 (반셀/저전류 ≤500mA) → D_Li, OCV 측정 (반셀 케이스 포함)
    # - simplified GITT: 일반 전류 → RSS 확산저항 측정
    if N >= 10 and n_steps <= 3 and max_rest_time >= 3600:
        non_rest_currents = [
            abs(s.get('current', 0)) for s in body_steps if s['type'] != 'REST'
        ]
        if non_rest_currents and max(non_rest_currents) <= 500:  # 0.1C 대역 추정
            return ('GITT', 'full')
        return ('GITT', 'simplified')

    # Rule 3 — DCIR (펄스 테스트 — EC 있음, 짧은 REST)
    # N=1 AND dchg≥4 AND EC → 기존 RSS_DCIR (실제는 DCIR at 여러 SOC 레벨)
    if N == 1 and dchg_count >= 4 and n_ec >= 1 and n_steps >= 10:
        # REST 시간으로 DCIR vs GITT(simplified, ≈RSS) 구분
        if max_rest_time >= 1800:  # 30m+
            return ('GITT', 'simplified')
        return ('DCIR', None)

    # Rule 4 — 사이클 반복 (chg≥1 AND dchg≥1 AND N≥2)
    if N >= 2 and chg_count >= 1 and dchg_count >= 1:
        if 2 <= N <= 10 and position <= 2:
            return ('사이클', 'FORMATION')
        return ('사이클', 'ACCEL')

    # Rule 5 — RPT (단발 1회 사이클)
    if N == 1 and chg_count >= 1 and dchg_count >= 1 and n_steps <= 8:
        return ('RPT', None)

    # Rule 5.5 — Floating (Rule 6 앞에 배치, N 무관)
    # CC/CCCV 장시간(≥12h) 충전 + V cutoff + 방전 없음 → 저장(floating)
    # 패턴: CC 충전 → V 도달 후 CV 유지 → 일~수개월 방치 (SEI 성장·calendar aging)
    # HaeanProto N=999, 김영환 Floating N=1 모두 커버
    if chg_count >= 1 and dchg_count == 0:
        max_chg_time = max(
            (s.get('time_limit', 0) for s in body_steps if s['type'].startswith('CHG')),
            default=0,
        )
        has_v_cut = any(
            s['type'].startswith('CHG') and s.get('v_chg', 0) > 0
            for s in body_steps
        )
        if max_chg_time >= 43200 and has_v_cut:
            return ('저장', 'floating')

    # Rule 6 — 단독 충전
    if N == 1 and chg_count >= 1 and dchg_count == 0:
        if type_set <= {'CHG_CC', 'CHG_CCCV', 'CHG_CP', 'REST', 'REST_SAFE'}:
            return ('충전', '세팅')

    # Rule 7 — 단독 방전
    if N == 1 and dchg_count >= 1 and chg_count == 0:
        if long_dchg or max_dchg_time >= 10800:
            return ('방전', '저장준비')
        if position == total_loops - 1:
            return ('방전', '종료')
        if position <= 1:
            return ('방전', '초기')
        # DCHG_CCCV 는 SOC 세팅 목적
        if any(t == 'DCHG_CCCV' for t in types):
            return ('방전', 'SOC세팅')
        return ('방전', None)

    # Rule 8 — 단독 휴지/저장
    if has_chg_cp:
        return ('저장', None)
    if n_steps == 1 and types[0] == 'REST':
        if max_rest_time >= 7200:
            return ('저장', None)
        if max_rest_time >= 1800:
            return ('저장', None)

    # 미지원 step code — 파서 보완 필요
    if has_unk_step:
        return ('UNKNOWN', 'PARSER_GAP')

    return ('UNKNOWN', None)


def label(cat, sub):
    return f'{cat}({sub})' if sub else cat


def main():
    variant_re = re.compile(r'_\d{3}\.sch$')

    new_counter = Counter()
    old_counter = Counter()
    transition_matrix = defaultdict(int)  # (old, new_label) -> count
    unknown_patterns = []
    seen = set()
    failure_exps = []
    per_exp = []

    for sp in sorted(BASE.rglob('*.sch')):
        parts = sp.relative_to(BASE).parts
        if len(parts) < 3:
            continue
        if variant_re.search(sp.name):
            continue
        steps = parse_sch(sp)
        if not steps:
            continue
        groups = split_into_loop_groups(steps)
        total_loops = len(groups)
        exp_new_cats = []
        exp_has_unknown = False
        for idx, g in enumerate(groups):
            old = OLD_CLASSIFY(g['body'], g['loop_count'], idx, total_loops)
            new_cat, sub = classify_new(g['body'], g['loop_count'], idx, total_loops)
            new_lbl = label(new_cat, sub)
            old_counter[old] += 1
            new_counter[new_lbl] += 1
            transition_matrix[(old, new_lbl)] += 1
            exp_new_cats.append((new_lbl, g['loop_count']))
            if new_cat == 'UNKNOWN':
                exp_has_unknown = True
                body = format_group_body(g['body'])
                key = (g['loop_count'], body[:140])
                if key not in seen:
                    seen.add(key)
                    unknown_patterns.append(
                        (parts[1][:45], g['loop_count'], body, idx, total_loops, sub)
                    )
        per_exp.append((parts[0], parts[1], exp_new_cats))
        if exp_has_unknown:
            failure_exps.append((parts[0], parts[1]))

    print('=' * 72)
    print('[1] 신 9종 + 서브태그 분포')
    print('=' * 72)
    for lbl, cnt in new_counter.most_common():
        print(f'  {lbl:<26} {cnt:>5}')
    total_groups = sum(new_counter.values())
    unk_count = sum(c for lbl, c in new_counter.items() if lbl.startswith('UNKNOWN'))
    print(f'\n  총 loop group: {total_groups} / UNKNOWN {unk_count} ({unk_count / total_groups * 100:.1f}%)')

    print()
    print('=' * 72)
    print('[2] 구→신 전이 매트릭스 (상위 30)')
    print('=' * 72)
    for (old, new), cnt in sorted(
        transition_matrix.items(), key=lambda x: -x[1]
    )[:30]:
        print(f'  {old:<20} → {new:<30} {cnt:>5}')

    print()
    print('=' * 72)
    print(f'[3] 신 분류기에서 UNKNOWN 남은 고유 패턴 ({len(unknown_patterns)}건)')
    print('=' * 72)
    for exp, n, body, idx, total, sub in sorted(unknown_patterns, key=lambda r: -r[1]):
        sub_str = f' [{sub}]' if sub else ''
        print(f'  N={n:<4} pos={idx + 1}/{total}{sub_str}  [{exp}]')
        print(f'      {body[:200]}')

    print()
    print('=' * 72)
    print(f'[4] UNKNOWN 포함 실험 — 구 vs 신')
    print('=' * 72)
    # 구 UNKNOWN 포함 실험 재확인
    old_unk_exps = 0
    new_unk_exps = len(failure_exps)
    for top, exp, cats in per_exp:
        pass  # skip
    # 구 분류기로도 재계산
    for sp in sorted(BASE.rglob('*.sch')):
        parts = sp.relative_to(BASE).parts
        if len(parts) < 3 or variant_re.search(sp.name):
            continue
        steps = parse_sch(sp)
        if not steps:
            continue
        groups = split_into_loop_groups(steps)
        total_loops = len(groups)
        has_unk = False
        for idx, g in enumerate(groups):
            if OLD_CLASSIFY(g['body'], g['loop_count'], idx, total_loops) == 'UNKNOWN':
                has_unk = True
                break
        if has_unk:
            old_unk_exps += 1

    print(f'  구 분류기 UNKNOWN 포함 실험: {old_unk_exps}')
    print(f'  신 분류기 UNKNOWN 포함 실험: {new_unk_exps}')

    print()
    print('=' * 72)
    print('[5] 240919 SOC별DCIR 케이스 신 분류 검증')
    print('=' * 72)
    target = None
    for sp in BASE.rglob('*.sch'):
        if '240919' in str(sp) and 'SOC' in str(sp) and not variant_re.search(sp.name):
            target = sp
            break
    if target:
        steps = parse_sch(target)
        groups = split_into_loop_groups(steps)
        tc = 1
        for idx, g in enumerate(groups):
            old = OLD_CLASSIFY(g['body'], g['loop_count'], idx, len(groups))
            new_cat, sub = classify_new(g['body'], g['loop_count'], idx, len(groups))
            n = g['loop_count']
            rng = f'TC {tc}' if n == 1 else f'TC {tc}-{tc + n - 1} ({n})'
            print(f'  #{idx + 1:<2} 구:{old:<16} 신:{label(new_cat, sub):<24} {rng}')
            tc += n


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()
