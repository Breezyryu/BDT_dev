"""Phase 5: .sch 스텝 블록 내부 필드 맵 확정 - 652B 고정 블록."""
import os
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'C:\Users\Ryu\battery\python\BDT_dev\Rawdata'
STEP_SIZE = 652  # 블록 크기 고정!
STEP_START_OFFSET = 1920  # 첫 스텝 시작 고정!

KNOWN_TYPES = {
    0xFF03: 'REST_TIME',
    0xFF07: 'REST_SAFE',
    0xFF08: 'LOOP',
    0xFF06: 'GOTO',
    0x0101: 'CHG_CC',      # CC 충전
    0x0201: 'CHG_CCCV',    # CCCV 충전
    0x0102: 'DCHG_CC_?',   # CC 방전?
    0x0202: 'DCHG_CC',     # CC 방전
}


def find_sch(dataset_name):
    ds_path = os.path.join(BASE, dataset_name)
    if not os.path.isdir(ds_path):
        return None
    for root, dirs, files in os.walk(ds_path):
        for f in files:
            if f.endswith('.sch') and '_000' not in f:
                return os.path.join(root, f)
    return None


def parse_steps(raw):
    """652B 고정 블록으로 스텝 파싱."""
    steps = []
    off = STEP_START_OFFSET
    step_expected = 1
    while off + STEP_SIZE <= len(raw):
        step_num = struct.unpack_from('<I', raw, off)[0]
        if step_num != step_expected:
            break
        type_code = struct.unpack_from('<I', raw, off + 8)[0]
        type_name = KNOWN_TYPES.get(type_code, f'UNK_{type_code:#x}')
        
        # 블록 내 모든 float32/uint32 추출
        fields = {}
        for j in range(0, STEP_SIZE, 4):
            f32 = struct.unpack_from('<f', raw, off + j)[0]
            u32 = struct.unpack_from('<I', raw, off + j)[0]
            fields[j] = {'f32': f32, 'u32': u32}
        
        steps.append({
            'num': step_num,
            'type_code': type_code,
            'type_name': type_name,
            'offset': off,
            'fields': fields,
        })
        off += STEP_SIZE
        step_expected += 1
    return steps


# ── 분석 대상 ──
SAMPLES = [
    ("Half cell (3.45mAh)", "251218_251230_00_박민희_3-45mAh_M1 ATL Cathode Half T23"),
    ("GITT (4.187mAh)", "250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half-14pi-GITT-0.1C-T23"),
    ("SEU4 RT (2335mAh)", "251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202"),
    ("SEU4 LT (2335mAh)", "251029_251229_05_나무늬_2335mAh_Q8 선상 ATL SEU4 LT @1-401"),
    ("SEU4 HT (2335mAh)", "251029_260129_05_나무늬_2335mAh_Q8 선상 ATL SEU4 HT @1-801"),
    ("2.9V 50CY (2335mAh)", "251029_260429_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 50CY @1-1202"),
    ("Rss RT (2369mAh)", "260119_260616_03_홍승기_2369mAh_Q8 ATL Main 2.0C Rss RT"),
    ("Sub Rss (2485mAh)", "260119_260616_03_홍승기_2485mAh_Q8 ATL Sub 2.0C Rss RT"),
]

print("=" * 90)
print("Phase 5: 652B 고정 블록 내부 필드 맵 확정")
print("=" * 90)

# ── 1. 타입별 충방전 스텝 내부 비교 ──
all_chg_cc = []     # 0x0101
all_chg_cccv = []   # 0x0201
all_dchg = []       # 0x0202
all_rest = []       # 0xFF03
all_loop = []       # 0xFF08

for label, ds_name in SAMPLES:
    sch_path = find_sch(ds_name)
    if not sch_path:
        continue
    with open(sch_path, 'rb') as f:
        raw = f.read()
    
    steps = parse_steps(raw)
    for s in steps:
        entry = {'label': label, 'step': s}
        if s['type_code'] == 0x0101:
            all_chg_cc.append(entry)
        elif s['type_code'] == 0x0201:
            all_chg_cccv.append(entry)
        elif s['type_code'] == 0x0202:
            all_dchg.append(entry)
        elif s['type_code'] == 0xFF03:
            all_rest.append(entry)
        elif s['type_code'] == 0xFF08:
            all_loop.append(entry)

# ── 2. CHG_CC (0x0101) 필드 맵 ──
print(f"\n\n{'='*60}")
print(f"CHG_CC (0x0101) - {len(all_chg_cc)}개 스텝")
print(f"{'='*60}")

# 각 스텝의 non-zero 필드 위치와 값 비교
for entry in all_chg_cc[:8]:
    s = entry['step']
    print(f"\n  [{entry['label']}] Step {s['num']}:")
    for j in range(0, STEP_SIZE, 4):
        v = s['fields'][j]
        if v['u32'] != 0 and v['f32'] == v['f32']:
            f32_str = f"{v['f32']:.2f}" if abs(v['f32']) < 1e7 else "big"
            print(f"    +{j:>3}: f32={f32_str:>12}  u32={v['u32']:>10}")

# ── 3. CHG_CCCV (0x0201) 필드 맵 ──
print(f"\n\n{'='*60}")
print(f"CHG_CCCV (0x0201) - {len(all_chg_cccv)}개 스텝")
print(f"{'='*60}")

for entry in all_chg_cccv[:6]:
    s = entry['step']
    print(f"\n  [{entry['label']}] Step {s['num']}:")
    for j in range(0, STEP_SIZE, 4):
        v = s['fields'][j]
        if v['u32'] != 0 and v['f32'] == v['f32']:
            f32_str = f"{v['f32']:.2f}" if abs(v['f32']) < 1e7 else "big"
            print(f"    +{j:>3}: f32={f32_str:>12}  u32={v['u32']:>10}")

# ── 4. DCHG_CC (0x0202) 필드 맵 ──
print(f"\n\n{'='*60}")
print(f"DCHG_CC (0x0202) - {len(all_dchg)}개 스텝")
print(f"{'='*60}")

for entry in all_dchg[:6]:
    s = entry['step']
    print(f"\n  [{entry['label']}] Step {s['num']}:")
    for j in range(0, STEP_SIZE, 4):
        v = s['fields'][j]
        if v['u32'] != 0 and v['f32'] == v['f32']:
            f32_str = f"{v['f32']:.2f}" if abs(v['f32']) < 1e7 else "big"
            print(f"    +{j:>3}: f32={f32_str:>12}  u32={v['u32']:>10}")

# ── 5. REST (0xFF03) 필드 맵 ──
print(f"\n\n{'='*60}")
print(f"REST (0xFF03) - {len(all_rest)}개 스텝")
print(f"{'='*60}")

for entry in all_rest[:4]:
    s = entry['step']
    print(f"\n  [{entry['label']}] Step {s['num']}:")
    for j in range(0, STEP_SIZE, 4):
        v = s['fields'][j]
        if v['u32'] != 0 and v['f32'] == v['f32']:
            f32_str = f"{v['f32']:.2f}" if abs(v['f32']) < 1e7 else "big"
            print(f"    +{j:>3}: f32={f32_str:>12}  u32={v['u32']:>10}")

# ── 6. LOOP (0xFF08) 필드 맵 ──
print(f"\n\n{'='*60}")
print(f"LOOP (0xFF08) - {len(all_loop)}개 스텝")
print(f"{'='*60}")

for entry in all_loop[:4]:
    s = entry['step']
    print(f"\n  [{entry['label']}] Step {s['num']}:")
    for j in range(0, STEP_SIZE, 4):
        v = s['fields'][j]
        if v['u32'] != 0 and v['f32'] == v['f32']:
            f32_str = f"{v['f32']:.2f}" if abs(v['f32']) < 1e7 else "big"
            print(f"    +{j:>3}: f32={f32_str:>12}  u32={v['u32']:>10}")

# ── 7. 필드 오프셋 일관성 분석 ──
print(f"\n\n{'='*60}")
print("필드 위치 일관성 분석 (CHG_CC | CHG_CCCV | DCHG_CC)")
print(f"{'='*60}")

# 각 타입에서 non-zero가 나타나는 필드 오프셋 통계
for type_name, entries in [("CHG_CC", all_chg_cc), ("CHG_CCCV", all_chg_cccv), ("DCHG_CC", all_dchg)]:
    field_usage = {}
    for entry in entries:
        for j in range(12, STEP_SIZE, 4):  # 0,4,8 제외 (step_num, pad, type)
            v = entry['step']['fields'][j]
            if v['u32'] != 0:
                if j not in field_usage:
                    field_usage[j] = []
                f32 = v['f32'] if abs(v['f32']) < 1e7 and v['f32'] == v['f32'] else None
                field_usage[j].append(f32)
    
    print(f"\n  {type_name} ({len(entries)}스텝):")
    for j in sorted(field_usage.keys()):
        vals = field_usage[j]
        count = len(vals)
        pct = count / len(entries) * 100
        # 특징적인 값들
        numeric_vals = [v for v in vals if v is not None]
        if numeric_vals:
            unique = sorted(set(round(v, 1) for v in numeric_vals))
            val_str = str(unique[:5]) if len(unique) <= 5 else f"{unique[:3]}... ({len(unique)}종)"
        else:
            val_str = "non-float"
        if pct > 50:  # 50% 이상 출현하는 필드만
            print(f"    +{j:>3}: {pct:>5.0f}% ({count}/{len(entries)}) | 값: {val_str}")

print("\n분석 완료")
