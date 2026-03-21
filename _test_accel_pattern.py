"""가속수명 패턴 분석 단위 테스트 (최소 의존성)."""
import os
import numpy as np
import pandas as pd


def _extract_toyo_step_currents(channel_path, totl_cycle, condition):
    cycle_file = os.path.join(channel_path, '%06d' % totl_cycle)
    if not os.path.isfile(cycle_file):
        return (0.0, 0.0)
    try:
        raw = pd.read_csv(cycle_file, sep=',', skiprows=3,
                          encoding='cp949', on_bad_lines='skip')
    except Exception:
        return (0.0, 0.0)
    cur_col = 'Current[mA]'
    cond_col = 'Condition'
    if cur_col not in raw.columns or cond_col not in raw.columns:
        return (0.0, 0.0)
    active = raw[(raw[cond_col] == condition) & (raw[cur_col].abs() > 0)]
    if active.empty:
        return (0.0, 0.0)
    currents = active[cur_col].abs().values
    max_cur = currents.max()
    cc_plateau = currents[currents >= max_cur * 0.95]
    cc_current = float(np.median(cc_plateau)) if len(cc_plateau) > 0 else float(max_cur)
    cv_cutoff = float(currents[-1])
    return (cc_current, cv_cutoff)


def _analyze_accel_pattern_toyo(channel_path, capacity):
    cap_log_path = os.path.join(channel_path, 'capacity.log')
    if not os.path.isfile(cap_log_path):
        for f in os.listdir(channel_path):
            if f.upper() == 'CAPACITY.LOG':
                cap_log_path = os.path.join(channel_path, f)
                break
        else:
            return None
    try:
        df = pd.read_csv(cap_log_path, sep=',', encoding='cp949', on_bad_lines='skip')
    except Exception:
        return None
    col_map = {'Total Cycle': 'TotlCycle', 'Capacity[mAh]': 'Cap[mAh]',
               'End Factor': 'Finish', 'Peak Volt.[V]': 'PeakVolt[V]'}
    df.rename(columns={k: v for k, v in col_map.items() if k in df.columns}, inplace=True)
    for need in ('Condition', 'TotlCycle', 'Finish', 'PeakVolt[V]', 'Cap[mAh]'):
        if need not in df.columns:
            return None
    conds = df['Condition'].values
    i = 0
    chg_start = chg_end = dchg_start = dchg_end = None
    while i < len(df):
        start = i
        cond = int(conds[i])
        while i < len(df) and int(conds[i]) == cond:
            i += 1
        if cond == 1 and (i - start) >= 2 and chg_start is None:
            chg_start, chg_end = start, i
            if i < len(df) and int(conds[i]) == 2:
                dchg_start = i
                while i < len(df) and int(conds[i]) == 2:
                    i += 1
                dchg_end = i
            break
    if chg_start is None:
        return None
    charge_steps = []
    for idx, row_idx in enumerate(range(chg_start, chg_end)):
        row = df.iloc[row_idx]
        tc = int(row['TotlCycle'])
        finish = str(row['Finish']).strip()
        peak_v = float(row['PeakVolt[V]'])
        step_cap = float(row['Cap[mAh]'])
        cc_cur, cv_cut = _extract_toyo_step_currents(channel_path, tc, 1)
        if finish in ('Cur', 'Cur.'):
            charge_steps.append({'step': idx+1, 'mode': 'CCCV',
                'crate': round(cc_cur/capacity, 2), 'current_mA': round(cc_cur, 1),
                'voltage_cutoff': round(peak_v, 3),
                'current_cutoff_crate': round(cv_cut/capacity, 2),
                'current_cutoff_mA': round(cv_cut, 1),
                'capacity_mAh': round(step_cap, 1)})
        else:
            charge_steps.append({'step': idx+1, 'mode': 'CC',
                'crate': round(cc_cur/capacity, 2), 'current_mA': round(cc_cur, 1),
                'voltage_cutoff': round(peak_v, 3),
                'capacity_mAh': round(step_cap, 1)})
    discharge_steps = []
    if dchg_start is not None and dchg_end is not None:
        for idx, row_idx in enumerate(range(dchg_start, dchg_end)):
            row = df.iloc[row_idx]
            tc = int(row['TotlCycle'])
            peak_v = float(row['PeakVolt[V]'])
            step_cap = float(row['Cap[mAh]'])
            cc_cur, _ = _extract_toyo_step_currents(channel_path, tc, 2)
            cycle_file = os.path.join(channel_path, '%06d' % tc)
            min_v = peak_v
            if os.path.isfile(cycle_file):
                try:
                    raw = pd.read_csv(cycle_file, sep=',', skiprows=3,
                                      encoding='cp949', on_bad_lines='skip')
                    part = raw[raw['Condition'] == 2]
                    if not part.empty:
                        min_v = float(part['Voltage[V]'].min())
                except Exception:
                    pass
            discharge_steps.append({'step': idx+1, 'mode': 'CC',
                'crate': round(cc_cur/capacity, 2), 'current_mA': round(cc_cur, 1),
                'voltage_cutoff': round(min_v, 3), 'capacity_mAh': round(step_cap, 1)})
    return {'charge_steps': charge_steps, 'discharge_steps': discharge_steps,
            'n_charge_steps': len(charge_steps), 'n_discharge_steps': len(discharge_steps)}


def _analyze_accel_pattern_pne(channel_path, capacity):
    restore_path = os.path.join(channel_path, 'Restore')
    if not os.path.isdir(restore_path):
        return None
    sed_file = None
    for f in os.listdir(restore_path):
        if 'SaveEndData' in f and f.endswith('.csv'):
            sed_file = f
            break
    if not sed_file:
        return None
    try:
        df = pd.read_csv(os.path.join(restore_path, sed_file),
                         header=None, encoding='cp949', on_bad_lines='skip')
    except Exception:
        return None
    if df.shape[1] < 41:
        return None
    real = df[df[2] != 8]
    first_accel_cyc = None
    for cyc, group in real.groupby(27):
        n_chg = (group[2] == 1).sum()
        n_dchg = (group[2] == 2).sum()
        if n_chg >= 2 and n_dchg >= 1:
            first_accel_cyc = cyc
            break
    if first_accel_cyc is None:
        return None
    cyc_data = real[real[27] == first_accel_cyc]
    charge_steps = []
    for idx, (_, row) in enumerate(cyc_data[cyc_data[2] == 1].iterrows()):
        end_state = int(row[6])
        end_v = row[8] / 1e6
        end_cur = row[9] / 1000
        cc_time = row[38] / 100
        cc_cap = row[39] / 1000
        cv_cap = row[40] / 1000
        if end_state == 66 and cc_time > 0:
            cc_cur = cc_cap / (cc_time / 3600)
            cutoff_cur = abs(end_cur)
            charge_steps.append({'step': idx+1, 'mode': 'CCCV',
                'crate': round(cc_cur/capacity, 2), 'current_mA': round(cc_cur, 1),
                'voltage_cutoff': round(end_v, 3),
                'current_cutoff_crate': round(cutoff_cur/capacity, 2),
                'current_cutoff_mA': round(cutoff_cur, 1),
                'capacity_mAh': round(cc_cap + cv_cap, 1)})
        else:
            charge_steps.append({'step': idx+1, 'mode': 'CC',
                'crate': round(abs(end_cur)/capacity, 2),
                'current_mA': round(abs(end_cur), 1),
                'voltage_cutoff': round(end_v, 3), 'capacity_mAh': round(cc_cap, 1)})
    discharge_steps = []
    for idx, (_, row) in enumerate(cyc_data[cyc_data[2] == 2].iterrows()):
        end_v = row[8] / 1e6
        end_cur = abs(row[9] / 1000)
        dchg_cap = row[11] / 1000
        discharge_steps.append({'step': idx+1, 'mode': 'CC',
            'crate': round(end_cur/capacity, 2), 'current_mA': round(end_cur, 1),
            'voltage_cutoff': round(end_v, 3), 'capacity_mAh': round(dchg_cap, 1)})
    return {'charge_steps': charge_steps, 'discharge_steps': discharge_steps,
            'n_charge_steps': len(charge_steps), 'n_discharge_steps': len(discharge_steps)}


def format_accel_pattern(pattern):
    lines = []
    lines.append('    > 가속수명 충방전 패턴:')
    for s in pattern['charge_steps']:
        if s['mode'] == 'CCCV':
            lines.append(f'      CHG Step {s["step"]}: CCCV {s["crate"]:.2f}C -> {s["voltage_cutoff"]:.3f}V, {s["current_cutoff_crate"]:.2f}C cutoff')
        else:
            lines.append(f'      CHG Step {s["step"]}: CC {s["crate"]:.2f}C -> {s["voltage_cutoff"]:.3f}V')
    for s in pattern['discharge_steps']:
        lines.append(f'      DCHG Step {s["step"]}: CC {s["crate"]:.2f}C -> {s["voltage_cutoff"]:.3f}V')
    return lines


if __name__ == '__main__':
    print('=' * 60)
    print('Toyo 가속수명 패턴 분석')
    print('=' * 60)
    toyo_path = r'rawdata/250207_250307_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 1-100cyc/30'
    ap = _analyze_accel_pattern_toyo(toyo_path, 1689)
    if ap:
        for line in format_accel_pattern(ap):
            print(line)
        print()
        for s in ap['charge_steps']:
            print(f"  {s}")
        for s in ap['discharge_steps']:
            print(f"  {s}")
    else:
        print('FAIL')

    print()
    print('=' * 60)
    print('PNE 가속수명 패턴 분석')
    print('=' * 60)
    pne_path = r'rawdata/251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202/M01Ch008[008]'
    ap2 = _analyze_accel_pattern_pne(pne_path, 2335)
    if ap2:
        for line in format_accel_pattern(ap2):
            print(line)
        print()
        for s in ap2['charge_steps']:
            print(f"  {s}")
        for s in ap2['discharge_steps']:
            print(f"  {s}")
    else:
        print('FAIL')
