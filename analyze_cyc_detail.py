#!/usr/bin/env python3
"""
PNE .cyc 파일 상세 분석 - 데이터 레코드 구조 파악
"""
import struct
import numpy as np

# .cyc 파일 읽기
cyc_file = r"C:\Users\Ryu\battery\python\BDT_dev\rawdata\250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half-14pi-GITT-0.1C-T23\M01Ch025[025]\250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half-14pi-GITT-0.1C-T23.cyc"

with open(cyc_file, 'rb') as f:
    # 헤더 읽기
    f.seek(0)
    header_vals = struct.unpack('<2I', f.read(8))
    print(f"헤더: {header_vals} (0x{header_vals[0]:04X}, 0x{header_vals[1]:04X})")
    
    date_time = f.read(20)
    print(f"날짜/시간: {date_time.strip(b'\\x00')}")
    
    f.seek(72)
    desc = f.read(32).strip(b'\x00')
    print(f"설명: {desc}")
    
    # 데이터 레코드 구조 분석
    print("\n=== 데이터 레코드 구조 추정 ===")
    
    # Offset 512부터 float 데이터로 추정
    f.seek(512)
    
    # 가능한 입력 구조: float32 x8 = 32바이트가 한 레코드
    record = f.read(32)
    floats = struct.unpack('<8f', record)
    print(f"\nOffset 512 (float32 x8): {floats}")
    
    # 해석 시도:
    # 일반적인 배터리 데이터: Time, Voltage, Current, Capacity, ...
    print("\n해석 추측:")
    print(f"  [0] {floats[0]:12.4f} - 시간?")
    print(f"  [1] {floats[1]:12.4f} - 전압?")
    print(f"  [2] {floats[2]:12.4f} - 전류?")
    print(f"  [3] {floats[3]:12.4f} - 용량?")
    for i in range(4, 8):
        print(f"  [{i}] {floats[i]:12.4f}")
    
    # 여러 레코드를 읽어서 패턴 분석
    print("\n\n=== 다중 레코드 분석 ===")
    f.seek(512)
    for i in range(5):
        record = f.read(32)
        if len(record) < 32:
            break
        floats = struct.unpack('<8f', record)
        print(f"레코드 {i}: {[f'{v:.2f}' for v in floats]}")
    
    # 오프셋 512가 정확한 시작이 맞는지 확인
    print("\n\n=== 오프셋 512 전후 분석 ===")
    f.seek(480)
    data = f.read(128)
    print(f"Offset 480-511 (마지막 32바이트): {data[-32:].hex(' ')}")
    
    # 실제 데이터 레코드 크기 추정
    # 많은 바이너리 파일은 고정 크기 레코드를 사용
    f.seek(0, 2)
    file_size = f.tell()
    
    # 헤더 크기 추정 (512 바이트)
    header_size = 512
    data_size = file_size - header_size
    
    print(f"\n파일 크기: {file_size:,} bytes")
    print(f"추정 헤더 크기: {header_size} bytes")
    print(f"추정 데이터 크기: {data_size:,} bytes")
    
    # 다양한 레코드 크기로 나누어떨어지는지 확인
    print("\n=== 가능한 레코드 크기 ===")
    for record_size in [4, 8, 12, 16, 24, 32, 48, 64, 128, 256]:
        if data_size % record_size == 0:
            num_records = data_size // record_size
            print(f"레코드 크기 {record_size:3d}바이트: {num_records:12,} 개 레코드 ✓")
        else:
            remainder = data_size % record_size
            print(f"레코드 크기 {record_size:3d}바이트: {data_size // record_size:12,} 개 + {remainder} 바이트 남음")
    
    # 32바이트 레코드 가정 시 float 값들
    print("\n\n=== 32바이트 레코드 (float32 x8) 샘플 ===")
    f.seek(512)
    for i in range(10):
        record = f.read(32)
        if len(record) < 32:
            break
        floats = struct.unpack('<8f', record)
        # 배터리 데이터로 해석
        print(f"레코드 {i:3d}: V={floats[0]:8.3f}V I={floats[1]:8.2f}mA Q={floats[2]:8.2f}mAh Step={floats[3]:3.0f}")
