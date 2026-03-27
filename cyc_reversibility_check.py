#!/usr/bin/env python3
"""
PNE .cyc 파일 역공학 가능성 평가
- 암호화 패턴 분석
- 데이터 복구 가능성 검토
"""
import struct
import numpy as np
from collections import Counter
import os

cyc_file = r"C:\Users\Ryu\battery\python\BDT_dev\rawdata\250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half-14pi-GITT-0.1C-T23\M01Ch025[025]\250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half-14pi-GITT-0.1C-T23.cyc"

with open(cyc_file, 'rb') as f:
    # 헤더와 초반 데이터 로드
    f.seek(0)
    header = f.read(512)
    
    # 데이터 영역 샘플 (여러 위치)
    samples = {}
    for offset in [512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]:
        f.seek(offset)
        data = f.read(256)
        samples[offset] = data
    
    print("=" * 70)
    print("PNE .cyc 파일 역공학 현실성 평가")
    print("=" * 70)
    
    # 1. 인코딩 검사: 평문인가 암호화된가?
    print("\n[1] 암호화 여부 판정")
    print("-" * 70)
    
    # 엔트로피 계산 (0-1, 낮을수록 패턴화된 데이터, 높을수록 난수/암호화)
    def shannon_entropy(data):
        """Shannon entropy 계산 (bits)"""
        byte_counts = Counter(data)
        entropy = 0
        for count in byte_counts.values():
            p = count / len(data)
            entropy -= p * (np.log2(p) if p > 0 else 0)
        return entropy
    
    for offset, data in list(samples.items())[:5]:
        entropy = shannon_entropy(data)
        print(f"  Offset {offset:6d}: entropy={entropy:.3f} bits", end="")
        if entropy > 7.5:
            print(" → 높음 (암호화/압축 가능성) ⚠️")
        elif entropy > 6.0:
            print(" → 중간 (부분 암호화 가능성)")
        else:
            print(" → 낮음 (평문 데이터)")
    
    # 2. 반복 패턴 분석
    print("\n[2] 반복 패턴 분석 (암호화되면 반복 없음)")
    print("-" * 70)
    
    def find_repeating_patterns(data, min_size=4, max_size=64):
        """16바이트 이상의 반복 패턴 찾기"""
        for size in [16, 32, 64]:
            patterns = {}
            for i in range(0, len(data) - size, 1):
                chunk = data[i:i+size]
                if chunk not in patterns:
                    patterns[chunk] = []
                patterns[chunk].append(i)
            
            repeats = {k: v for k, v in patterns.items() if len(v) > 1}
            if repeats:
                print(f"    크기 {size}바이트: {len(repeats)}개 반복 패턴 발견 ✓")
                for chunk, positions in sorted(repeats.items(), key=lambda x: -len(x[1]))[:3]:
                    print(f"      {chunk.hex()[:40]}... @ {positions[:3]}")
                return True
        return False
    
    has_pattern = False
    for offset, data in list(samples.items())[:3]:
        print(f"  Offset {offset}:")
        if find_repeating_patterns(data):
            has_pattern = True
    
    if not has_pattern:
        print("    ❌ 명확한 반복 패턴 없음 → 암호화 가능성 높음")
    
    # 3. 바이너리 시그니처와 구조 분석
    print("\n[3] 알려진 파일 포맷 시그니처 검사")
    print("-" * 70)
    
    # gzip, deflate, zlib 등 압축 시그니처
    sigs = {
        'GZIP': b'\x1f\x8b',
        'DEFLATE': b'\x78\x9c',
        'ZIP': b'PK\x03\x04',
        'RAR': b'Rar!',
        '7z': b'7z\xbc\xaf',
    }
    
    for name, sig in sigs.items():
        if header[64:64+len(sig)] == sig:
            print(f"    ✓ {name} 서명 발견! 이 포맷으로 압축됨")
        for offset, data in samples.items():
            if data[:len(sig)] == sig:
                print(f"    ✓ Offset {offset}에서 {name} 발견")
    
    # 4. 데이터 구간별 특성 분석
    print("\n[4] 데이터 구간별 통계")
    print("-" * 70)
    
    # 바이트 분포 분석
    f.seek(512)
    first_4kb = f.read(4096)
    
    byte_dist = Counter(first_4kb)
    unique_bytes = len(byte_dist)
    most_common = byte_dist.most_common(5)
    
    print(f"  처음 4KB의 바이트 분포:")
    print(f"    고유 바이트: {unique_bytes}/256 ({unique_bytes/256*100:.1f}%)")
    print(f"    가장 흔한 바이트: {', '.join([f'0x{b[0]:02X}({b[1]}회)' for b in most_common])}")
    
    if unique_bytes < 100:
        print(f"    ➜ 대부분의 바이트가 사용되지 않음 → 압축 가능성")
    elif unique_bytes > 240:
        print(f"    ➜ 거의 모든 바이트 사용 → 암호화 가능성")
    
    # 5. 32비트 float 값 분석 (이전 시도)
    print("\n[5] float32 구조 검증")
    print("-" * 70)
    
    f.seek(512)
    floats = struct.unpack('<32f', f.read(128))
    
    valid_float_count = 0
    reasonable_values = []
    
    for val in floats:
        # 배터리 데이터로 합리적인 범위인지 확인
        # 전압: 0-5V, 전류: -500~500mA, 용량: 0-10000mAh, 온도: -50~100°C
        if (0 <= val <= 5) or (-500 <= val <= 500) or (0 <= val <= 10000) or (-50 <= val <= 100):
            valid_float_count += 1
            reasonable_values.append(val)
        elif val == 0.0:
            valid_float_count += 1
    
    print(f"  32개 float32 중 {valid_float_count}개가 배터리 값으로 합리적")
    if valid_float_count > 20:
        print(f"  ✓ 대부분의 값이 의미 있음 → 32바이트 float32 레이아웃 가능성")
        print(f"  샘플값: {[f'{v:.2f}' for v in reasonable_values[:10]]}")
    else:
        print(f"  ❌ 대부분의 값이 비정상 → XOR/암호화 가능성")
    
    # 6. 종합 평가
    print("\n" + "=" * 70)
    print("종합 평가")
    print("=" * 70)
    
    entropy_avg = np.mean([shannon_entropy(samples[o]) for o in list(samples.keys())[:3]])
    print(f"\n평균 엔트로피: {entropy_avg:.3f} bits")
    print(f"예상 상황:")
    
    if entropy_avg > 7.8:
        print("  → 🔴 강력한 암호화 또는 압축 (복구 불가능성 높음)")
        print("     권장: 대안 2번 (MySQL 데이터베이스 직접 접속)")
    elif entropy_avg > 7.0:
        print("  → 🟡 부분 암호화 또는 압축 (부분 복구 가능)")
        print("     권장: 일단 시도해보되, 실패 시 대안 2번으로")
    else:
        print("  → 🟢 대부분 평문 (완전 복구 가능)")
        print("     권장: 3번 진행 가능")

print("\n" + "=" * 70)
print("다음 단계")
print("=" * 70)
print("""
결과에 따른 대응:
- 엔트로피 < 7.0: .cyc 파서 개발 진행
- 엔트로피 > 7.8: 즉시 대안 2번(MySQL) 또는 1번(CSV 자동화) 추천
- 엔트로피 7.0~7.8: 헤더 분석 + XOR/간단한 암호화 시도
""")
