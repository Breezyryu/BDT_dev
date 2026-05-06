"""Path 12 (Si 10%) 의 SOC offset OVR 원인 진단.

WARN 판정된 경로의 capacity 값과 raw cumul_net 추이를 확인한다.
"""
import os
import sys
import importlib.util
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
_PROTO = _HERE.parent / 'DataTool_optRCD_proto_.py'
_spec = importlib.util.spec_from_file_location('bdt_proto', _PROTO)
_mod = importlib.util.module_from_spec(_spec)
sys.modules['bdt_proto'] = _mod
_spec.loader.exec_module(_mod)

_compute_tc_soc_offsets = _mod._compute_tc_soc_offsets
get_channel_save_end_data = _mod.get_channel_save_end_data
get_channel_meta = _mod.get_channel_meta

PATHS = [
    (r'C:\Users\Ryu\battery\python\BDT_dev\DataTool_dev_code\data\exp_data\성능_hysteresis\260330_260405_05_신용호_4960mAh_Gen6+ ATL proto1차 Si 10% Hysteresis 측정\M01Ch060[060]', 'Si 10%'),
    (r'C:\Users\Ryu\battery\python\BDT_dev\DataTool_dev_code\data\exp_data\성능_hysteresis\260330_260405_05_신용호_4960mAh_Gen6+ ATL proto1차 Si 15% Hysteresis 측정\M01Ch059[059]', 'Si 15%'),
    (r'C:\Users\Ryu\battery\python\BDT_dev\DataTool_dev_code\data\exp_data\성능_hysteresis\260202_260210_05_현혜정_4875mAh_LWN Gen5 MP1-1 0.5C hysteresis\M01Ch022[022]', 'LWN Gen5 (정상)'),
]

for ch_path, label in PATHS:
    print(f'\n[{label}]')
    print(f'  channel: {ch_path}')
    nominal_cap = 4960 if 'Si' in label else 4875

    # meta 우선
    meta = get_channel_meta(ch_path)
    meta_cap = meta.min_capacity if meta and meta.min_capacity else None
    print(f'  nominal: {nominal_cap} mAh, meta.min_capacity: {meta_cap}')

    # SaveEndData 직접 조회
    se = get_channel_save_end_data(ch_path)
    if se is None or se.empty:
        print('  SaveEndData empty')
        continue

    cr = se[[27, 2, 10, 11]].copy()
    cr.columns = ['TC', 'Cond', 'ChgCap', 'DchgCap']
    cap_uah = nominal_cap * 1000

    cumul = 0.0
    print(f'  TC | chg(uAh) | dchg(uAh) | net(uAh) | cumul(uAh) | cumul/cap')
    for tc in sorted(cr['TC'].unique())[:25]:
        rows = cr[cr['TC'] == tc]
        chg = rows.loc[rows['Cond'] == 1, 'ChgCap'].sum()
        dchg = rows.loc[rows['Cond'] == 2, 'DchgCap'].sum()
        net = chg - dchg
        old_cumul = cumul
        cumul += net
        print(f'  {int(tc):2d} | {chg:>10.0f} | {dchg:>10.0f} | {net:>+10.0f} | '
              f'{cumul:>+11.0f} | {old_cumul/cap_uah:+.3f}')

    # 보정 결과
    offsets = _compute_tc_soc_offsets(ch_path, nominal_cap)
    print(f'\n  최종 offsets (after anchor shift):')
    for tc in sorted(offsets.keys())[:25]:
        print(f'    TC {tc:2d}: {offsets[tc]:+.4f}')
