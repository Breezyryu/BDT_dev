"""Rawdata .sch 파일 교차 구조 분석 → JSON 출력."""
import json
import os
import struct

BASE = r'C:\Users\Ryu\battery\python\BDT_dev\Rawdata'
OUT = r'C:\Users\Ryu\battery\python\BDT_dev\_sch_analysis.json'

# 전수 .sch 수집
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

# 고유 이름별 그룹
by_name = {}
for item in sch_files:
    key = item['name']
    if key not in by_name:
        by_name[key] = {'size': item['size'], 'count': 0, 'items': []}
    by_name[key]['count'] += 1
    by_name[key]['items'].append(item)

# 대표 파일 분석
results = []
for fn, info in sorted(by_name.items(), key=lambda x: -x[1]['size']):
    fp = info['items'][0]['path']
    with open(fp, 'rb') as f:
        raw = f.read()

    # 헤더 4 x uint32
    magic = list(struct.unpack_from('<4I', raw, 0))

    # UTF-16 메타데이터
    header = raw[16:3000]
    strings = header.decode('utf-16-le', errors='replace')
    parts = [s.strip() for s in strings.split('\x00') if s.strip() and len(s.strip()) > 1]
    # 한글/영문/숫자만 필터
    meta_clean = []
    for p in parts[:10]:
        cleaned = ''.join(c for c in p if (0xAC00 <= ord(c) <= 0xD7A3)  # 한글
                          or (0x0020 <= ord(c) <= 0x007E)  # ASCII
                          or c in '._-@()[]')
        if len(cleaned) > 3:
            meta_clean.append(cleaned)

    # float32 전체 스캔
    float_map = {}
    for i in range(0, len(raw) - 3, 4):
        val = struct.unpack_from('<f', raw, i)[0]
        if 50 < abs(val) < 50000 and val == val:
            rounded = round(val, 1)
            if rounded not in float_map:
                float_map[rounded] = []
            float_map[rounded].append(i)

    # 상위 30 빈출값
    top_floats = sorted(float_map.items(), key=lambda x: -len(x[1]))[:30]

    # 알려진 전압/전류 키값 검색
    KEY_VALS = [234, 466, 840, 1160, 1680, 1689, 2068, 2320, 2335, 2369, 2485,
                3376, 3829, 4140, 4160, 4175, 4190, 4200, 4210, 4300, 4350,
                4470, 4500, 4550, 4600, 4640, 4670, 4738, 4905, 4970,
                3000, 3650, 2900, 2850, 60, 100, 200, 300, 600, 1200, 1202, 801, 401, 400]
    key_hits = {}
    for kv in KEY_VALS:
        if float(kv) in float_map:
            key_hits[str(kv)] = {
                'count': len(float_map[float(kv)]),
                'offsets': float_map[float(kv)][:8],
            }

    # 4550.0 발견 위치 간격 분석 (레코드 크기 추정)
    record_gaps = {}
    for anchor_val in [4550.0, 4300.0]:
        if anchor_val in float_map and len(float_map[anchor_val]) >= 2:
            offsets = sorted(float_map[anchor_val])
            gaps = [offsets[i+1] - offsets[i] for i in range(len(offsets)-1)]
            record_gaps[str(anchor_val)] = gaps

    entry = {
        'filename': fn,
        'size': info['size'],
        'channel_count': info['count'],
        'header_magic': magic,
        'metadata': meta_clean,
        'top_floats': [[v, len(offs)] for v, offs in top_floats],
        'key_hits': key_hits,
        'record_gaps': record_gaps,
    }
    results.append(entry)

output = {
    'total_sch_files': len(sch_files),
    'unique_schedules': len(by_name),
    'analyses': results,
}

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Done: {len(results)} schedules analyzed -> {OUT}")
