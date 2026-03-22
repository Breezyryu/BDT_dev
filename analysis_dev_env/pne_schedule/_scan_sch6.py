"""Phase 4b: .sch 스텝 블록 구조 해독 - 오프셋 간격 수정 (step+8=type)."""
import os
import struct
import sys
from collections import Counter

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


# Half cell 분석에서 발견된 패턴:
# offset 1920: uint32=1  (step 1)
# offset 1928: uint32=65283 (type code)  ← +8 gap
# offset 2572: uint32=2  (step 2)
# offset 2580: uint32=65288 (type code)  ← +8 gap

KNOWN_TYPES = {
    0x0000FF03: 'REST_TIME',     # 65283: 시간제한 Rest
    0x0000FF07: 'REST_?',        # 65287
    0x0000FF08: 'LOOP',          # 65288: Loop
    0x0000FF06: 'GOTO',          # 65286: GoTo
    0x00000101: 'CHG_CV?',       # 257: 충전 (CC? CV? CCCV?)
    0x00000201: 'CHG_CCCV?',     # 513
    0x00000102: 'DCHG?',         # 258
    0x00000202: 'DCHG_CC?',      # 514
}

# 범위 확대: 다른 타입코드도 있을 수 있음
ALL_TYPE_CODES = set(KNOWN_TYPES.keys())


def find_step_sequence(raw):
    """스텝 시퀀스 탐색: uint32(N) at offset X, uint32(type) at offset X+8."""
    candidates = []
    for i in range(0, len(raw) - 11, 4):
        val = struct.unpack_from('<I', raw, i)[0]
        if not (1 <= val <= 300):
            continue
        # +8 바이트에 타입 코드
        type_val = struct.unpack_from('<I', raw, i + 8)[0]
        if type_val in ALL_TYPE_CODES:
            candidates.append({
                'step_num': val,
                'type_code': type_val,
                'type_name': KNOWN_TYPES.get(type_val, f'UNK_{type_val:#x}'),
                'offset': i,
            })
    
    if not candidates:
        return []
    
    # step=1부터 시작하는 가장 긴 순증 시퀀스
    best_seq = []
    for idx, c in enumerate(candidates):
        if c['step_num'] != 1:
            continue
        seq = [c]
        expected = 2
        for c2 in candidates[idx+1:]:
            if c2['step_num'] == expected and c2['offset'] > seq[-1]['offset']:
                seq.append(c2)
                expected += 1
        if len(seq) > len(best_seq):
            best_seq = seq
    
    return best_seq


# ── 1차: 모든 타입 코드 탐색 ──
print("=" * 90)
print("Phase 4b: 타입 코드 전수 탐색")
print("=" * 90)

# Half cell 파일로 타입 코드 탐색 범위 확대
sch_path = find_sch("251218_251230_00_박민희_3-45mAh_M1 ATL Cathode Half T23")
with open(sch_path, 'rb') as f:
    raw = f.read()

print(f"\nHalf cell ({len(raw):,}B) - 모든 step-like 패턴 (1~30):")
for i in range(0, len(raw) - 11, 4):
    val = struct.unpack_from('<I', raw, i)[0]
    if not (1 <= val <= 30):
        continue
    # 주변 값 확인
    prev4 = struct.unpack_from('<I', raw, max(0,i-4))[0] if i >= 4 else 0
    next4 = struct.unpack_from('<I', raw, i+4)[0]
    next8 = struct.unpack_from('<I', raw, i+8)[0]
    
    # step_num의 앞이 0이고 뒤가 0이거나 non-trivial
    if prev4 == 0 and (next4 == 0 or next4 > 60000):
        type_at_8 = next8
        type_str = KNOWN_TYPES.get(type_at_8, f'{type_at_8:#010x}')
        print(f"  off={i:>5}: step={val:>3}, +4={next4:#010x}, +8={type_at_8:#010x} ({type_str})")


# ── 2차: 확대된 타입코드로 다시 탐색 ──
# Half cell에서 발견된 모든 "알 수 있는" 타입 코드
print("\n\nHalf cell 파일 raw 4바이트 전수 스캔 (0xFF?? 범위):")
for i in range(0, len(raw) - 3, 4):
    val = struct.unpack_from('<I', raw, i)[0]
    # 0xFF00 ~ 0xFFFF 또는 0x0100 ~ 0x0FFF 범위
    if (0xFF00 <= val <= 0xFFFF) or (0x0100 <= val <= 0x0FFF):
        # 앞 4바이트가 step number (1~30)?
        if i >= 8:
            prev8 = struct.unpack_from('<I', raw, i-8)[0]
            prev4 = struct.unpack_from('<I', raw, i-4)[0]
        else:
            prev8 = prev4 = 0
        print(f"  off={i:>5}: val={val:#010x} ({val:>6}), -8={prev8:>5}, -4={prev4:>5}")


# ── 3차: 연속 step 시퀀스 탐색 (타입코드 무시) ──
print("\n\n연속 step 시퀀스 탐색 (타입코드 무시):")
for ds_label, ds_name in [
    ("Half cell", "251218_251230_00_박민희_3-45mAh_M1 ATL Cathode Half T23"),
    ("SEU4 RT", "251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202"),
    ("Rss RT", "260119_260616_03_홍승기_2369mAh_Q8 ATL Main 2.0C Rss RT"),
]:
    sch_path = find_sch(ds_name)
    if not sch_path:
        print(f"  [SKIP] {ds_label}")
        continue
    with open(sch_path, 'rb') as f:
        raw = f.read()
    
    print(f"\n  --- [{ds_label}] {len(raw):,}B ---")
    
    # 모든 "작은 uint32" (1~100) 위치 수집
    small_vals = []
    for i in range(0, len(raw) - 3, 4):
        val = struct.unpack_from('<I', raw, i)[0]
        if 1 <= val <= 100:
            prev = struct.unpack_from('<I', raw, max(0,i-4))[0] if i >= 4 else -1
            nxt = struct.unpack_from('<I', raw, i+4)[0] if i+4 < len(raw)-3 else -1
            small_vals.append((i, val, prev, nxt))
    
    # 연속 1, 2, 3... 패턴 찾기
    for start_idx in range(len(small_vals)):
        if small_vals[start_idx][1] != 1:
            continue
        seq = [small_vals[start_idx]]
        expected = 2
        for sv in small_vals[start_idx+1:]:
            if sv[1] == expected:
                seq.append(sv)
                expected += 1
            elif sv[1] > expected + 3:
                break
        if len(seq) >= 5:  # 최소 5스텝
            print(f"  시퀀스 발견 (start={seq[0][0]}, {len(seq)}스텝):")
            for off, val, prev, nxt in seq:
                nxt8 = struct.unpack_from('<I', raw, off+8)[0] if off+8 < len(raw)-3 else 0
                print(f"    off={off:>6}: step={val:>3}, prev={prev:>8}, +4={nxt:#010x}, +8={nxt8:#010x}")
            # 블록 크기 (스텝 간 간격)
            if len(seq) > 1:
                gaps = [seq[j+1][0] - seq[j][0] for j in range(len(seq)-1)]
                print(f"  블록 간격: {gaps[:15]}")
            break  # 첫 시퀀스만

print("\n분석 완료")
