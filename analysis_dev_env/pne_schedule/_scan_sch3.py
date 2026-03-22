"""Phase 2: .sch 구조 정밀 분석 - 헤더 공통부, 레코드 경계, 스텝 블록 패턴."""
import json
import os
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'C:\Users\Ryu\battery\python\BDT_dev\Rawdata'

# 전수 .sch 수집
sch_files = []
for root, dirs, files in os.walk(BASE):
    for f in files:
        if f.endswith('.sch'):
            fp = os.path.join(root, f)
            sz = os.path.getsize(fp)
            sch_files.append({'path': fp, 'name': f, 'size': sz})

# 고유 이름별 그룹 → 대표 1개씩
by_name = {}
for item in sch_files:
    if item['name'] not in by_name:
        by_name[item['name']] = item

print(f"=== {len(by_name)}개 고유 스케줄 분석 ===\n")

# ── 1. 헤더 매직넘버 비교 ──
print("1. 헤더 매직넘버 (첫 16바이트)")
print("-" * 60)
magic_groups = {}
for fn, item in sorted(by_name.items()):
    with open(item['path'], 'rb') as f:
        hdr = f.read(16)
    magic = struct.unpack_from('<4I', hdr, 0)
    key = str(magic)
    if key not in magic_groups:
        magic_groups[key] = []
    magic_groups[key].append((fn, item['size']))

for magic_str, files in magic_groups.items():
    print(f"\n  매직: {magic_str}")
    print(f"  해당 파일 {len(files)}개:")
    for fn, sz in files[:5]:
        print(f"    {sz:>10,}B  {fn[:70]}")
    if len(files) > 5:
        print(f"    ... 외 {len(files)-5}개")

# ── 2. UTF-16 메타데이터 영역 정밀 분석 ──
print(f"\n\n2. UTF-16 메타데이터 영역")
print("-" * 60)

# 다양한 크기의 파일 5개 선택
sizes = sorted(set(item['size'] for item in by_name.values()))
sample_sizes = [sizes[0], sizes[len(sizes)//4], sizes[len(sizes)//2], sizes[3*len(sizes)//4], sizes[-1]]
samples = []
for sz in sample_sizes:
    for fn, item in by_name.items():
        if item['size'] == sz and item not in samples:
            samples.append(item)
            break

for item in samples:
    with open(item['path'], 'rb') as f:
        raw = f.read()
    
    print(f"\n  --- {item['name'][:60]} ({item['size']:,}B) ---")
    
    # NULL 바이트 구간 탐색 → 메타데이터 종료 위치 추정
    # 연속 NULL 8바이트 이상인 첫 위치
    meta_end = None
    for i in range(16, min(5000, len(raw)) - 8):
        if raw[i:i+8] == b'\x00' * 8:
            # 이전에 non-null이 있었는지 확인
            if any(b != 0 for b in raw[max(16,i-4):i]):
                meta_end = i
                break
    
    # 메타데이터 구간 내 UTF-16 문자열 추출
    if meta_end:
        meta_block = raw[16:meta_end]
        # 한글 감지: 0xAC00-0xD7A3 범위 2바이트
        korean_found = False
        for j in range(0, len(meta_block)-1, 2):
            code = struct.unpack_from('<H', meta_block, j)[0]
            if 0xAC00 <= code <= 0xD7A3:
                korean_found = True
                break
        
        # UTF-16 디코드
        decoded = meta_block.decode('utf-16-le', errors='replace')
        parts = [s.strip() for s in decoded.split('\x00') if s.strip()]
        
        print(f"  메타 영역: offset 16 ~ {meta_end} ({meta_end-16} bytes)")
        print(f"  한글 감지: {korean_found}")
        for i, p in enumerate(parts[:6]):
            # 출력 가능 문자만
            safe = ''.join(c if (0xAC00 <= ord(c) <= 0xD7A3 or 0x20 <= ord(c) <= 0x7E) else '?' for c in p)
            if len(safe.replace('?','')) > 2:
                print(f"  [{i}] {safe[:80]}")
    else:
        print(f"  메타 영역 종료 감지 실패")

# ── 3. 레코드 블록 경계 분석 ──
print(f"\n\n3. 레코드 블록 경계 분석 (마커 바이트 패턴)")
print("-" * 60)

# 가설: 각 스텝은 특정 마커 바이트로 시작
# 이전 분석에서 4550.0이 충전 전압으로 반복 → 간격으로 레코드 크기 추정

for item in samples:
    with open(item['path'], 'rb') as f:
        raw = f.read()
    
    print(f"\n  --- {item['name'][:55]} ({item['size']:,}B) ---")
    
    # uint32 값 4550 찾기 (= 0x11C6 = 4550 in uint32)
    # float32 값 4550.0 위치
    anchor_offsets = []
    for i in range(0, len(raw) - 3, 4):
        val = struct.unpack_from('<f', raw, i)[0]
        if abs(val - 4550.0) < 0.5:
            anchor_offsets.append(i)
    
    if anchor_offsets:
        gaps = [anchor_offsets[i+1] - anchor_offsets[i] for i in range(len(anchor_offsets)-1)]
        print(f"  4550.0 발견: {len(anchor_offsets)}회 @ {anchor_offsets[:8]}")
        print(f"  간격: {gaps[:10]}")
        
        # 간격 패턴 요약
        from collections import Counter
        gap_counts = Counter(gaps)
        print(f"  간격 통계: {dict(gap_counts.most_common(5))}")
    else:
        # 다른 전압값으로 시도
        for test_v in [4200.0, 4350.0, 4500.0]:
            offsets = []
            for i in range(0, len(raw) - 3, 4):
                val = struct.unpack_from('<f', raw, i)[0]
                if abs(val - test_v) < 0.5:
                    offsets.append(i)
            if offsets:
                gaps = [offsets[j+1] - offsets[j] for j in range(len(offsets)-1)]
                from collections import Counter
                gap_counts = Counter(gaps)
                print(f"  {test_v} 발견: {len(offsets)}회, 간격: {dict(gap_counts.most_common(5))}")
                break
        else:
            print(f"  전압 앵커 없음")

# ── 4. 첫 4550.0 전후 바이트 패턴 비교 ──
print(f"\n\n4. 4550.0 전후 바이트 패턴 비교 (레코드 구조 추정)")
print("-" * 60)

# 4550이 있는 파일들에서, 4550 앞 32바이트의 패턴 비교
patterns_before = {}
for fn, item in sorted(by_name.items()):
    with open(item['path'], 'rb') as f:
        raw = f.read()
    
    offsets_4550 = []
    for i in range(0, len(raw) - 3, 4):
        val = struct.unpack_from('<f', raw, i)[0]
        if abs(val - 4550.0) < 0.5:
            offsets_4550.append(i)
    
    if not offsets_4550:
        continue
    
    first = offsets_4550[0]
    if first < 20:
        continue
    
    # 4550.0 앞 20바이트 = 5 x float32
    before = []
    for j in range(first - 20, first, 4):
        val = struct.unpack_from('<f', raw, j)[0]
        before.append(round(val, 1))
    
    # 4550.0 뒤 20바이트 = 5 x float32
    after = []
    for j in range(first + 4, min(first + 24, len(raw) - 3), 4):
        val = struct.unpack_from('<f', raw, j)[0]
        after.append(round(val, 1))
    
    key = (tuple(before), tuple(after))
    if key not in patterns_before:
        patterns_before[key] = []
    patterns_before[key].append(fn[:50])

print(f"  첫 4550.0 전후 float32 패턴 유형: {len(patterns_before)}개")
for (before, after), files in sorted(patterns_before.items(), key=lambda x: -len(x[1])):
    print(f"\n  앞5: {list(before)}  뒤5: {list(after)}")
    print(f"  해당: {len(files)}개 파일")
    for fn in files[:3]:
        print(f"    - {fn}")

# ── 5. 고정 오프셋 값 비교 ──
print(f"\n\n5. 고정 오프셋 float32 값 비교 (오프셋 0~200)")
print("-" * 60)

# 모든 파일의 오프셋 0~200에서 float32 값 수집
offset_vals = {}  # {offset: {val: count}}
for fn, item in by_name.items():
    with open(item['path'], 'rb') as f:
        raw = f.read(400)
    for off in range(0, 200, 4):
        val = struct.unpack_from('<f', raw, off)[0]
        rounded = round(val, 1) if (abs(val) < 1e6 and val == val) else 'nan'
        if off not in offset_vals:
            offset_vals[off] = {}
        offset_vals[off][rounded] = offset_vals[off].get(rounded, 0) + 1

for off in range(0, 200, 4):
    vals = offset_vals[off]
    top = sorted(vals.items(), key=lambda x: -x[1])[:3]
    # 고정값(모든 파일 동일)인지 확인
    is_fixed = top[0][1] == len(by_name)
    marker = "FIXED" if is_fixed else ""
    top_str = ", ".join(f"{v}({c})" for v, c in top)
    print(f"  off={off:>3}: {top_str} {marker}")

print("\n분석 완료")
