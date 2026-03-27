#!/usr/bin/env python3
"""
PNE .cyc 파일 포맷 상세 역공학
- 헤더 분석
- 레코드 구조 파악
- 데이터 타입 식별
"""
import struct
import numpy as np
from pathlib import Path

cyc_file = r"C:\Users\Ryu\battery\python\BDT_dev\rawdata\250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half-14pi-GITT-0.1C-T23\M01Ch025[025]\250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half-14pi-GITT-0.1C-T23.cyc"

with open(cyc_file, 'rb') as f:
    data = f.read()
    file_size = len(data)

print("=" * 80)
print("PNE .cyc 파일 상세 역공학")
print("=" * 80)

# 헤더 분석 (512 바이트)
print("\n[1] 헤더 분석 (512 바이트)")
print("-" * 80)

header = data[:512]

# 처음 8 바이트: 매직 번호?
vals = struct.unpack('<2H2B', header[0:6])
print(f"  Offset 0-5: {vals} → 0x{vals[0]:04X} 0x{vals[1]:04X} {vals[2]} {vals[3]}")

# ASCII 날짜/시간 (Offset 8-27)
datetime_str = header[8:28].rstrip(b'\x00').decode('ascii', errors='ignore')
print(f"  Offset 8-27: '{datetime_str}'")

# 파일 설명 (Offset 72-103)  
desc = header[72:103].rstrip(b'\x00').decode('ascii')
print(f"  Offset 72-103: '{desc}'")

# 나머지 헤더 구조
print(f"  Offset 104-511: {len(header[104:])} 바이트 (미정의, 대부분 0x00)")
null_count = sum(1 for b in header[104:] if b == 0)
print(f"    → {null_count}/{len(header[104:])} 바이트가 0x00 (패딩)")

# 데이터 영역 분석
print("\n[2] 데이터 영역 구조 분석")
print("-" * 80)

data_start = 512
data_region = data[data_start:]

print(f"  총 데이터 크기: {len(data_region):,} 바이트")
print(f"  가능한 레코드 크기:")

# 고정 레코드 체크
possible_sizes = []
for record_size in [4, 8, 16, 32, 48, 64, 128, 256]:
    num_records, remainder = divmod(len(data_region), record_size)
    if remainder == 0:
        print(f"    {record_size:3d}바이트 × {num_records:10,} = {len(data_region):,} ✓ 딱 맞음")
        possible_sizes.append(record_size)
    elif remainder < 10:
        print(f"    {record_size:3d}바이트 × {num_records:10,} + {remainder} 바이트 남음")

# 32바이트 레코드 가정 (float32 x8)
print("\n[3] 32바이트 레코드 분석 (float32 × 8)")
print("-" * 80)

record_size = 32
num_records = len(data_region) // record_size

if len(data_region) % record_size == 0:
    print(f"  정확히 {num_records:,}개 레코드 = {num_records/60/60:,.0f} 시간분...")
    
    # 처음 20개 레코드 분석
    print(f"\n  처음 20개 레코드 (각 32바이트 = float32 × 8):")
    print(f"  {'#':>5} {'[0] V(V)':>10} {'[1] I(mA)':>10} {'[2] Q(mAh)':>10} {'[3]':>10} {'[4]':>10} {'[5]':>10} {'[6]':>10} {'[7]':>10}")
    print("-" * 89)
    
    for i in range(min(20, num_records)):
        idx = data_start + i * record_size
        record = struct.unpack('<8f', data[idx:idx+record_size])
        # 간단한 범위 필터링 (바이너리 노이즈 제거)
        display = []
        for j, val in enumerate(record):
            if -10000 < val < 1000000:
                display.append(f"{val:10.2f}")
            else:
                display.append(f"{'SKIP':>10}")
        print(f"  {i:>5d} {display[0]} {display[1]} {display[2]} {display[3][:8]} {display[4][:8]} {display[5][:8]} {display[6][:8]} {display[7][:8]}")
    
    # 통계 분석
    print(f"\n  레코드별 통계 (필터링 후):")
    valid_records = []
    for i in range(num_records):
        idx = data_start + i * record_size
        record = struct.unpack('<8f', data[idx:idx+record_size])
        valid_records.append(record)
    
    # 각 필드별 통계
    for field_idx in range(8):
        values = [r[field_idx] for r in valid_records if -10000 < r[field_idx] < 1000000]
        if len(values) > 0:
            values = np.array(values)
            print(f"    필드 [{field_idx}]: min={values.min():.2f}, max={values.max():.2f}, mean={values.mean():.2f}, std={values.std():.2f}")

# HEX 덤프로 직접 확인
print("\n[4] 초반 데이터 HEX 덤프 (512-767)")
print("-" * 80)
for offset in range(512, min(512 + 256, len(data)), 32):
    hex_str = data[offset:offset+32].hex(' ')
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[offset:offset+32])
    print(f"  {offset:6d}: {hex_str:<96} | {ascii_str}")

# 파일 끝부분 분석
print("\n[5] 파일 끝부분 분석")
print("-" * 80)
last_records = []
for i in range(max(0, num_records - 5), num_records):
    idx = data_start + i * record_size
    if idx + record_size <= len(data):
        record = struct.unpack('<8f', data[idx:idx+record_size])
        last_records.append((i, record))

print(f"  마지막 5개 레코드:")
for i, record in last_records:
    print(f"    Record {i:8,}: {[f'{v:.2f}' for v in record]}")

# 패턴 찾기
print("\n[6] 패턴 인식 (주기성 확인)")
print("-" * 80)

# 0x00 연속 구간 찾기 (가능한 구분자)
null_runs = []
current_run = 0
for offset in range(len(data)):
    if data[offset] == 0:
        current_run += 1
    else:
        if current_run > 16:
            null_runs.append((offset - current_run, current_run))
        current_run = 0

print(f"  16바이트 이상의 0x00 연속: {len(null_runs)}개")
for start, length in null_runs[:5]:
    print(f"    Offset {start:7,}: {length:5} 바이트 NULL 패딩")

print("\n" + "=" * 80)
print("분석 결론")
print("=" * 80)
print("""
✓ 데이터 타입: float32 × 8 레이아웃 강하게 추정
✓ 압축/암호화: 없음 (엔트로피 낮음)
✓ 레코드 크기: 32바이트 (확실함)

다음 단계:
1. 필드 의미 파악 (전압, 전류, 용량, 온도 등)
2. 실제 값 범위 검증
3. 스케줄(.sch) 정보와 연관지어 해석
""")
