"""End Condition 파싱 통합 테스트 (임시 — 검증 후 삭제)"""
import sys
sys.path.insert(0, '.')

from analysis_dev_env.pne_schedule.parse_pne_schedule import (
    extract_accel_pattern_from_sch,
    extract_schedule_structure_from_sch,
)
from DataTool_dev.DataTool_optRCD_proto_ import format_accel_pattern

# 1) Rss .sch
sch_rss = (
    r'C:\Users\Ryu\battery\python\BDT_dev\rawdata'
    r'\260119_260616_03_홍승기_2485mAh_Q8 ATL Sub 2.0C Rss RT'
    r'\M02Ch081[081]'
    r'\260119_260616_03_홍승기_2485mAh_Q8 ATL Sub 2.0C Rss RT.sch'
)
result = extract_accel_pattern_from_sch(sch_rss, capacity=2485)
print('=== Rss .sch 패턴 추출 ===')
if result:
    for line in format_accel_pattern(result):
        print(line)
    print(f"CHG: {result['n_charge_steps']}, DCHG: {result['n_discharge_steps']}")
else:
    print('None (패턴 없음)')

# 2) 일반 가속수명 .sch
sch_accel = (
    r'C:\Users\Ryu\battery\python\BDT_dev\rawdata'
    r'\260119_260616_03_홍승기_2485mAh_Q8 ATL Sub 2C 2.9V 100Cy'
    r'\M02Ch066[066]'
    r'\260119_260616_03_홍승기_2485mAh_Q8 ATL Sub 2C 2.9V 100Cy..sch'
)
result2 = extract_accel_pattern_from_sch(sch_accel, capacity=2485)
print()
print('=== 일반 가속수명 .sch 패턴 추출 ===')
if result2:
    for line in format_accel_pattern(result2):
        print(line)
    print(f"CHG: {result2['n_charge_steps']}, DCHG: {result2['n_discharge_steps']}")
else:
    print('None (패턴 없음)')

# 3) 스케줄 구조 분석 (Rss .sch)
struct_rss = extract_schedule_structure_from_sch(sch_rss, capacity=2485)
if struct_rss:
    print()
    print('=== Rss .sch 구조 분석 ===')
    for sec in struct_rss['sections']:
        cat = sec['category']
        lc = sec['loop_count']
        nc = sec['n_chg']
        nd = sec['n_dchg']
        print(f"  {cat:10s} LOOP={lc:3d} CHG={nc} DCHG={nd}")
    print(f"has_rss: {struct_rss['has_rss']}")
    print(f"schedule_type: {struct_rss['schedule_type']}")
