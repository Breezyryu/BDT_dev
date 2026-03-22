"""Phase 4: .sch 스텝 블록 구조 해독 - 스텝번호 기반 경계 탐지."""
import os
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'C:\Users\Ryu\battery\python\BDT_dev\Rawdata'


def find_sch(dataset_name):
    ds_path = os.path.join(BASE, dataset_name)
    if not os.path.isdir(ds_path):
        return None
    for root, dirs, files in os.walk(ds_path):
        for f in files:
            if f.endswith('.sch') and '_000' not in f:
                return os.path.join(root, f)
    for root, dirs, files in os.walk(ds_path):
        for f in files:
            if f.endswith('.sch'):
                return os.path.join(root, f)
    return None


def find_step_numbers(raw):
    """스텝 번호 (1, 2, 3, ...) 위치 탐색.
    Half cell 분석에서 발견: 스텝 시작에 uint32 = step_number 가 있음.
    그 뒤에 uint32 "type code" (65283=0x03FF, 65287=0x07FF, 65288=0x08FF,
                                  257=0x0101, 513=0x0201, 514=0x0202)
    """
    steps = []
    # 연속 증가하는 숫자 패턴 찾기
    for i in range(0, len(raw) - 7, 4):
        val = struct.unpack_from('<I', raw, i)[0]
        if val == 0:
            continue
        if 1 <= val <= 200:
            # 다음 4바이트
            next_val = struct.unpack_from('<I', raw, i + 4)[0]
            # 알려진 타입 코드인지
            known_types = {
                0xFF03: 'REST_TIME',     # 65283 = 시간제한 Rest
                0xFF07: 'REST_LOOP',     # 65287 
                0xFF08: 'LOOP',          # 65288 = Loop 스텝
                0xFF06: 'GOTO',          # 65286 = GoTo 스텝
                0x0101: 'CHG_CC',        # 257 = CC 충전  
                0x0201: 'CHG_CCCV',      # 513 = CCCV 충전
                0x0102: 'DCHG_CC',       # 258 = CC 방전?
                0x0202: 'DCHG_CCCV',     # 514 = CC 방전
            }
            if next_val in known_types:
                steps.append({
                    'step_num': val,
                    'type_code': next_val,
                    'type_name': known_types[next_val],
                    'offset': i,
                })
    return steps


def analyze_step_block(raw, offset, next_offset=None):
    """스텝 블록 내부 float32/uint32 유의미한 값 추출."""
    end = next_offset if next_offset else min(offset + 2000, len(raw))
    block_size = end - offset
    
    values = []
    for j in range(offset, end - 3, 4):
        f32 = struct.unpack_from('<f', raw, j)[0]
        u32 = struct.unpack_from('<I', raw, j)[0]
        if u32 != 0 and f32 == f32:
            rel = j - offset
            values.append({
                'rel_offset': rel,
                'abs_offset': j,
                'float32': round(f32, 2) if abs(f32) < 1e7 else None,
                'uint32': u32,
            })
    return block_size, values


# ── 파일별 분석 ──
SAMPLES = [
    ("Half cell", "251218_251230_00_박민희_3-45mAh_M1 ATL Cathode Half T23"),
    ("GITT", "250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half-14pi-GITT-0.1C-T23"),
    ("SEU4 RT", "251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202"),
    ("SEU4 LT", "251029_251229_05_나무늬_2335mAh_Q8 선상 ATL SEU4 LT @1-401"),
    ("SEU4 HT", "251029_260129_05_나무늬_2335mAh_Q8 선상 ATL SEU4 HT @1-801"),
    ("2.9V 50CY", "251029_260429_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 50CY @1-1202"),
    ("Rss RT", "260119_260616_03_홍승기_2369mAh_Q8 ATL Main 2.0C Rss RT"),
    ("Rss RE", "260130_260630_03_홍승기_2369mAh_Q8 Main 2C Rss RT CH32 57Cy-RE"),
]

print("=" * 90)
print("Phase 4: .sch 스텝 블록 구조 해독")
print("=" * 90)

for label, ds_name in SAMPLES:
    sch_path = find_sch(ds_name)
    if not sch_path:
        print(f"\n[SKIP] {label} - .sch 없음")
        continue

    with open(sch_path, 'rb') as f:
        raw = f.read()

    fn = os.path.basename(sch_path)
    print(f"\n{'='*80}")
    print(f"[{label}] {fn[:65]} ({len(raw):,}B)")
    print(f"{'='*80}")

    # 스텝 번호 탐색
    steps = find_step_numbers(raw)
    
    # 중복 제거 및 정렬
    seen = set()
    unique_steps = []
    for s in sorted(steps, key=lambda x: x['offset']):
        key = (s['step_num'], s['offset'])
        if key not in seen:
            seen.add(key)
            unique_steps.append(s)
    
    # 스텝번호가 1부터 시작하고 대체로 순증하는 시퀀스만 필터
    # 가장 긴 순증 부분수열 찾기
    if not unique_steps:
        print("  스텝 번호 미발견!")
        continue
    
    # 스텝 1이 여러 번 나올 수 있음 → 가장 이른 offset의 step=1부터 추적
    best_seq = []
    for start_idx, start_step in enumerate(unique_steps):
        if start_step['step_num'] != 1:
            continue
        seq = [start_step]
        expected = 2
        for s in unique_steps[start_idx+1:]:
            if s['step_num'] == expected:
                seq.append(s)
                expected += 1
        if len(seq) > len(best_seq):
            best_seq = seq
    
    if not best_seq:
        # step=1 없으면 전체 출력
        best_seq = unique_steps
    
    print(f"  스텝 수: {len(best_seq)}개")
    print(f"  {'Step':>4} {'TypeCode':>10} {'TypeName':<14} {'Offset':>8} {'BlockSize':>9}")
    print(f"  {'-'*4} {'-'*10} {'-'*14} {'-'*8} {'-'*9}")
    
    for i, s in enumerate(best_seq):
        next_off = best_seq[i+1]['offset'] if i+1 < len(best_seq) else len(raw)
        block_sz = next_off - s['offset']
        print(f"  {s['step_num']:>4} {s['type_code']:>10} {s['type_name']:<14} {s['offset']:>8} {block_sz:>9}")
    
    # 블록 크기 통계
    block_sizes = []
    for i, s in enumerate(best_seq):
        next_off = best_seq[i+1]['offset'] if i+1 < len(best_seq) else len(raw)
        block_sizes.append((s['type_name'], next_off - s['offset']))
    
    # 타입별 블록 크기
    type_sizes = {}
    for tn, sz in block_sizes:
        if tn not in type_sizes:
            type_sizes[tn] = []
        type_sizes[tn].append(sz)
    
    print(f"\n  타입별 블록 크기:")
    for tn, sizes in sorted(type_sizes.items()):
        if len(set(sizes)) == 1:
            print(f"    {tn:<14}: {sizes[0]:>6}B (일정)")
        else:
            print(f"    {tn:<14}: {min(sizes):>6}~{max(sizes):>6}B ({len(sizes)}개, 값: {sizes[:5]})")
    
    # 충전/방전 스텝의 전류/전압 값 추출
    print(f"\n  충방전 스텝 상세:")
    for i, s in enumerate(best_seq):
        if s['type_name'] not in ('CHG_CC', 'CHG_CCCV', 'DCHG_CC', 'DCHG_CCCV'):
            continue
        
        next_off = best_seq[i+1]['offset'] if i+1 < len(best_seq) else len(raw)
        block_sz, values = analyze_step_block(raw, s['offset'], next_off)
        
        # 의미있는 float32 (전류/전압 범위)
        interesting = [v for v in values 
                      if v['float32'] is not None and 0.01 < abs(v['float32']) < 50000
                      and v['rel_offset'] >= 8]  # 스텝번호/타입코드 이후
        
        print(f"    Step {s['step_num']} ({s['type_name']}, {block_sz}B):")
        for v in interesting[:15]:
            print(f"      +{v['rel_offset']:>4}: f32={v['float32']:>10.2f}  u32={v['uint32']:>10}")

print("\n분석 완료")
