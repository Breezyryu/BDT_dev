"""Rawdata 폴더 전체에서 .sch 파일 탐색 및 구조 교차 분석."""
import os
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'C:\Users\Ryu\battery\python\BDT_dev\Rawdata'

# ── 1단계: 전수 .sch 파일 수집 ──
sch_files = []
for root, dirs, files in os.walk(BASE):
    for f in files:
        if f.endswith('.sch'):
            fp = os.path.join(root, f)
            sz = os.path.getsize(fp)
            ch = os.path.basename(root)
            ds = os.path.basename(os.path.dirname(root))
            sch_files.append({
                'path': fp, 'name': f, 'size': sz,
                'channel': ch, 'dataset': ds,
            })

print(f"총 .sch 파일: {len(sch_files)}개\n")

# 고유 파일명(=스케줄)별 그룹핑
by_name = {}
for item in sch_files:
    key = item['name']
    if key not in by_name:
        by_name[key] = {'size': item['size'], 'count': 0, 'items': [], 'datasets': set()}
    by_name[key]['count'] += 1
    by_name[key]['items'].append(item)
    by_name[key]['datasets'].add(item['dataset'])

print(f"고유 .sch 스케줄: {len(by_name)}개\n")
print("=" * 100)
for fn, info in sorted(by_name.items(), key=lambda x: -x[1]['size']):
    print(f"{info['size']:>10,} bytes | {info['count']:>3}채널 | {fn[:90]}")
    for ds in sorted(info['datasets']):
        print(f"            └─ {ds[:80]}")
print("=" * 100)

# ── 2단계: 대표 파일 1개씩 뽑아 구조 분석 ──
print("\n\n=== .sch 구조 비교 분석 ===\n")

# 분석할 대표 파일들 (스케줄명별 첫 파일)
representatives = []
for fn, info in sorted(by_name.items(), key=lambda x: -x[1]['size']):
    representatives.append(info['items'][0])

# 핵심 키 전압/전류값 (검색 대상)
KEY_VOLTAGES = [3000.0, 3650.0, 4140.0, 4160.0, 4200.0, 4300.0, 4350.0, 4500.0, 4550.0]
KEY_CURRENTS = [100.0, 200.0, 234.0, 466.0, 840.0, 1160.0, 1680.0, 1689.0, 2320.0, 2335.0, 2369.0, 2485.0, 3376.0, 4640.0, 4670.0, 4738.0, 4970.0, 9000.0]

for item in representatives:
    fp = item['path']
    fn = item['name']
    sz = item['size']
    
    with open(fp, 'rb') as f:
        raw = f.read()
    
    print(f"\n{'─'*90}")
    print(f"파일: {fn[:80]}")
    print(f"크기: {sz:,} bytes | 채널수: {by_name[fn]['count']}")
    
    # UTF-16 메타데이터 추출
    header = raw[16:3000]
    strings = header.decode('utf-16-le', errors='ignore')
    parts = [s.strip() for s in strings.split('\x00') if s.strip() and len(s.strip()) > 1]
    print(f"메타데이터 ({len(parts)}개):")
    for i, p in enumerate(parts[:8]):
        # 한글/영문만 필터
        cleaned = ''.join(c for c in p if ord(c) > 31)
        if len(cleaned) > 2:
            print(f"  [{i}] {cleaned[:60]}")
    
    # 첫 16바이트 (매직넘버/버전)
    magic = struct.unpack_from('<4I', raw, 0)
    print(f"헤더 4×uint32: {magic}")
    
    # float32 스캔: 전압 키값
    print(f"전압 키값 검색:")
    for tv in KEY_VOLTAGES:
        positions = []
        for i in range(0, len(raw) - 3, 4):
            val = struct.unpack_from('<f', raw, i)[0]
            if abs(val - tv) < 0.5:
                positions.append(i)
        if positions:
            print(f"  {tv:>7.0f} mV → {len(positions):>2}회 @ offsets {positions[:6]}")
    
    # float32 스캔: 전류 키값
    print(f"전류 키값 검색:")
    for tv in KEY_CURRENTS:
        positions = []
        for i in range(0, len(raw) - 3, 4):
            val = struct.unpack_from('<f', raw, i)[0]
            if abs(val - tv) < 1.0:
                positions.append(i)
        if positions:
            print(f"  {tv:>7.0f} mA → {len(positions):>2}회 @ offsets {positions[:6]}")
    
    # 특징적 float32 값들 (100~10000 범위) 모두 추출 → 고유값 카운트
    all_floats = {}
    for i in range(0, len(raw) - 3, 4):
        val = struct.unpack_from('<f', raw, i)[0]
        if 50 < abs(val) < 50000 and val == val:  # NaN 제외
            rounded = round(val, 1)
            all_floats[rounded] = all_floats.get(rounded, 0) + 1
    
    # 상위 15개 빈출 float32
    top = sorted(all_floats.items(), key=lambda x: -x[1])[:20]
    print(f"빈출 float32 (상위 20, |50|~|50000|):")
    for val, cnt in top:
        print(f"  {val:>10.1f} × {cnt}회")

print(f"\n{'='*90}")
print("분석 완료")
