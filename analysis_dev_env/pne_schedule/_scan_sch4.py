"""Phase 3: .sch 바이너리 심층 구조 분석 - 헤더 후 블록 구조 해독."""
import os
import struct
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'C:\Users\Ryu\battery\python\BDT_dev\Rawdata'

# 5개 대표 파일 (크기 다양)
SAMPLES = [
    # Q7M Inner - 작은 패턴
    r"250207_250307_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 1-100cyc",
    # Q8 SEU4 RT - 중간 (이전 분석 기준)
    r"251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202",
    # Q8 Rss RT - 큰 패턴
    r"260119_260616_03_홍승기_2369mAh_Q8 ATL Main 2.0C Rss RT",
    # GITT
    r"250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half-14pi-GITT-0.1C-T23",
    # Half cell rated
    r"251218_251230_00_박민희_3-45mAh_M1 ATL Cathode Half T23",
]


def find_sch_in_dataset(dataset_name):
    """데이터셋 폴더 안 채널에서 .sch 파일 경로 1개 반환."""
    ds_path = os.path.join(BASE, dataset_name)
    if not os.path.isdir(ds_path):
        return None
    for root, dirs, files in os.walk(ds_path):
        for f in files:
            if f.endswith('.sch') and '_000' not in f:
                return os.path.join(root, f)
    # _000 파일이라도 반환
    for root, dirs, files in os.walk(ds_path):
        for f in files:
            if f.endswith('.sch'):
                return os.path.join(root, f)
    return None


def decode_utf16_meta(raw, start=16, max_end=500):
    """UTF-16LE로 메타데이터 문자열 추출."""
    results = []
    i = start
    while i < min(max_end, len(raw) - 1):
        # 문자열 시작: non-null 2바이트
        code = struct.unpack_from('<H', raw, i)[0]
        if code == 0:
            i += 2
            continue
        # 문자열 수집
        chars = []
        j = i
        while j < min(max_end, len(raw) - 1):
            code = struct.unpack_from('<H', raw, j)[0]
            if code == 0:
                break
            chars.append(chr(code))
            j += 2
        if chars:
            s = ''.join(chars)
            results.append((i, s))
            i = j + 2
        else:
            i += 2
    return results


print("=" * 90)
print("Phase 3: .sch 바이너리 심층 구조 분석")
print("=" * 90)

# ── 분석 1: 헤더 16바이트 해독 ──
print("\n1. 헤더 구조 (첫 16바이트)")
print("-" * 60)

# 전체 파일에서 헤더 확인
all_sch = []
for root, dirs, files in os.walk(BASE):
    for f in files:
        if f.endswith('.sch'):
            all_sch.append(os.path.join(root, f))

# 첫 16바이트를 다양한 형식으로 해석
with open(all_sch[0], 'rb') as f:
    hdr = f.read(16)

print(f"  Raw hex: {hdr.hex()}")
print(f"  4 x uint32 LE: {struct.unpack_from('<4I', hdr, 0)}")
print(f"  4 x int32 LE:  {struct.unpack_from('<4i', hdr, 0)}")
print(f"  8 x uint16 LE: {struct.unpack_from('<8H', hdr, 0)}")
print(f"  16 x uint8:    {list(hdr)}")
print(f"  740721 = 0x{740721:06X}")
print(f"  131077 = 0x{131077:06X}")

# ── 분석 2: 메타데이터 영역 (offset ~16 이후) ──
print("\n\n2. 메타데이터 영역 정밀 분석")
print("-" * 60)

for ds_name in SAMPLES:
    sch_path = find_sch_in_dataset(ds_name)
    if not sch_path:
        print(f"\n  [SKIP] {ds_name[:60]} - .sch 없음")
        continue

    with open(sch_path, 'rb') as f:
        raw = f.read()

    fn = os.path.basename(sch_path)
    print(f"\n  --- {fn[:70]} ({len(raw):,}B) ---")

    # 헤더 후 첫 non-zero 영역 찾기
    first_nonzero = None
    for i in range(16, min(1000, len(raw))):
        if raw[i] != 0:
            first_nonzero = i
            break
    print(f"  첫 non-zero: offset {first_nonzero}")

    # 메타 영역 raw bytes (offset 16 ~ 200)
    meta_area = raw[16:400]
    # 연속 non-zero 구간 찾기
    segments = []
    in_seg = False
    seg_start = 0
    for i, b in enumerate(meta_area):
        if b != 0 and not in_seg:
            seg_start = i + 16
            in_seg = True
        elif b == 0 and in_seg:
            # null 2개 이상이면 구간 끝
            if i + 1 < len(meta_area) and meta_area[i + 1] == 0:
                segments.append((seg_start, i + 16, i + 16 - seg_start))
                in_seg = False

    print(f"  non-zero 구간 ({len(segments)}개):")
    for start, end, length in segments[:10]:
        # 전체 hex
        seg_bytes = raw[start:end]
        # 해석 시도: uint8, uint16, uint32, UTF-16
        if length >= 4:
            u32 = struct.unpack_from('<I', raw, start)[0]
        else:
            u32 = None

        # UTF-16 해석
        if length >= 2 and length % 2 == 0:
            try:
                text = raw[start:end].decode('utf-16-le', errors='strict')
                is_text = all(0x20 <= ord(c) <= 0xFFFF for c in text)
            except:
                text = None
                is_text = False
        else:
            text = None
            is_text = False

        hex_str = seg_bytes[:20].hex()
        print(f"    [{start:>4}~{end:>4}] {length:>3}B | hex={hex_str[:40]}")
        if u32 is not None:
            print(f"      uint32={u32}, uint16={struct.unpack_from('<H', raw, start)[0]}")
        if text and is_text:
            safe = ''.join(c if (0xAC00 <= ord(c) <= 0xD7A3 or 0x20 <= ord(c) <= 0x7E) else '?' for c in text)
            print(f"      UTF-16: {safe[:60]}")

    # ── 분석 3: 오프셋 100~1100 구간 uint32/float32 탐색 ──
    # 헤더 끝 (103) 이후 첫 의미있는 데이터
    print(f"  offset 100~400 float32/uint32:")
    for off in range(100, min(400, len(raw) - 3), 4):
        f32 = struct.unpack_from('<f', raw, off)[0]
        u32 = struct.unpack_from('<I', raw, off)[0]
        if u32 != 0 and f32 == f32:  # non-zero, non-NaN
            interest = ""
            if 100 < f32 < 50000:
                interest = f" ★ float={f32:.1f}"
            elif u32 < 100000:
                interest = f" uint32={u32}"
            if interest:
                print(f"    off={off:>5}: u32={u32:>10} f32={f32:>12.2f}{interest}")


# ── 분석 3: 4550.0 앞의 "스텝 헤더" 패턴 ──
print(f"\n\n3. 스텝 블록 구조: 4550.0 앞 32바이트 정밀 분석")
print("-" * 60)

for ds_name in SAMPLES[:3]:  # 수명 시험 3개만
    sch_path = find_sch_in_dataset(ds_name)
    if not sch_path:
        continue

    with open(sch_path, 'rb') as f:
        raw = f.read()

    fn = os.path.basename(sch_path)
    print(f"\n  --- {fn[:70]} ---")

    # 4550.0 위치들
    offsets_4550 = []
    for i in range(0, len(raw) - 3, 4):
        val = struct.unpack_from('<f', raw, i)[0]
        if abs(val - 4550.0) < 0.5:
            offsets_4550.append(i)

    for idx, off in enumerate(offsets_4550[:6]):
        # 앞 40바이트 (10 x float32)
        print(f"\n    4550.0 #{idx+1} @ offset {off}:")
        before_start = max(0, off - 40)
        print(f"    앞 10 float32 (off {before_start}):")
        vals_before = []
        for j in range(before_start, off, 4):
            val = struct.unpack_from('<f', raw, j)[0]
            vals_before.append(round(val, 2) if (abs(val) < 1e7 and val == val) else 'NaN')
        print(f"      {vals_before}")

        # 뒤 40바이트 (10 x float32)
        print(f"    뒤 10 float32 (off {off+4}):")
        vals_after = []
        for j in range(off + 4, min(off + 44, len(raw) - 3), 4):
            val = struct.unpack_from('<f', raw, j)[0]
            vals_after.append(round(val, 2) if (abs(val) < 1e7 and val == val) else 'NaN')
        print(f"      {vals_after}")

        # 앞 40바이트를 uint32로도
        print(f"    앞 10 uint32:")
        uvals = []
        for j in range(before_start, off, 4):
            uvals.append(struct.unpack_from('<I', raw, j)[0])
        print(f"      {uvals}")


# ── 분석 4: 작은 파일 전체 덤프 ──
print(f"\n\n4. 작은 .sch 파일 구조 전체 덤프 (Half cell)")
print("-" * 60)

sch_path = find_sch_in_dataset(SAMPLES[4])  # Half cell - 9744B
if sch_path:
    with open(sch_path, 'rb') as f:
        raw = f.read()
    fn = os.path.basename(sch_path)
    print(f"  {fn} ({len(raw):,}B)")

    # 전체를 4바이트씩 float32로 덤프, 의미있는 값만
    print(f"  전체 float32 값 (!=0, !=NaN):")
    for i in range(0, len(raw) - 3, 4):
        f32 = struct.unpack_from('<f', raw, i)[0]
        u32 = struct.unpack_from('<I', raw, i)[0]
        if u32 != 0 and f32 == f32:
            is_interesting = (abs(f32) > 0.01) or (0 < u32 < 1000000)
            if is_interesting:
                print(f"    off={i:>5}: f32={f32:>12.2f}  u32={u32:>10}  hex={raw[i:i+4].hex()}")

print("\n분석 완료")
