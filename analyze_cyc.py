#!/usr/bin/env python3
"""
PNE .cyc 파일 포맷 분석
"""
import struct
import os

# .cyc 파일 읽기
cyc_file = r"C:\Users\Ryu\battery\python\BDT_dev\rawdata\250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half-14pi-GITT-0.1C-T23\M01Ch025[025]\250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half-14pi-GITT-0.1C-T23.cyc"

print(f"파일 존재 확인: {os.path.exists(cyc_file)}")
print(f"파일 경로: {cyc_file}\n")

with open(cyc_file, 'rb') as f:
    # 헤더 읽기
    header = f.read(256)
    
    # 처음 몇 uint32 값 읽기
    f.seek(0)
    vals = struct.unpack('<4I', f.read(16))
    print(f"처음 4개 uint32: {vals}")
    print(f"  0x{vals[0]:08X}, 0x{vals[1]:08X}, 0x{vals[2]:08X}, 0x{vals[3]:08X}")
    
    # 파일 크기 확인
    f.seek(0, 2)
    file_size = f.tell()
    print(f"\n파일 크기: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
    
    # 다양한 오프셋에서 데이터 구조 확인
    print("\n=== 주요 영역 분석 ===")
    f.seek(0)
    print(f"Offset 0-7: {f.read(8).hex(' ')}")
    f.seek(8)
    date_time = f.read(20)
    print(f"Offset 8-27 (ASCII): {date_time}")
    f.seek(72)
    print(f"Offset 72-103: {f.read(32)}")  # "PNE record data file."
    
    f.seek(128)
    data = f.read(32)
    print(f"Offset 128-159 (hex): {data.hex(' ')}")
    print(f"Offset 128-159 (uint32): {struct.unpack('<8I', data)}")
    
    # 더 깊은 분석: 데이터 레코드 구조 찾기
    print("\n=== 반복 블록 분석 ===")
    for offset in [256, 512, 768, 1024, 2048, 4096]:
        f.seek(offset)
        block = f.read(32)
        print(f"Offset {offset}: {block.hex(' ')}")
        # 처음 8바이트를 uint32로 해석
        try:
            vals = struct.unpack('<8H', block)  # 16비트 값으로
            print(f"  └─ uint16x8: {vals}")
        except:
            pass

    # 파일의 마지막 부분도 확인
    print("\n=== 파일 끝부분 분석 ===")
    f.seek(max(0, file_size - 256))
    last_block = f.read(256)
    print(f"마지막 256바이트 (hex): {last_block[-64:].hex(' ')}")
    
    # 반복 패턴 찾기: 블록 크기 추정
    print("\n=== 블록 크기 추정 ===")
    # 다양한 블록 크기를 시도
    for block_size in [256, 512, 1024, 2048, 4096, 8192]:
        num_blocks = file_size // block_size
        if num_blocks > 0:
            print(f"블록 크기 {block_size:5d}: {num_blocks:8,} 블록 ({file_size - num_blocks * block_size:,} 바이트 여유)")
