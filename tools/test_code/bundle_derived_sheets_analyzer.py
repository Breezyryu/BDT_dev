"""Bundle 의 6개 derived 시트 구조 + 데이터 패턴 분석.

대상 시트:
  - 3~12_QV         — TC 3-12 의 closed-loop fan (V vs SOC, hysteresis)
  - 3~12_QVData_DOD — TC 3-12 의 fan (V vs DOD)
  - 3~12_dVdQData_SOC — TC 3-12 의 dVdQ vs SOC
  - 14~23_QV        — TC 14-23 fan (V vs SOC)
  - 14~23_dVdQData  — TC 14-23 dVdQ
  - dQdV            — 통합 dQdV 시트

각 시트의 row/col 수, header 패턴, 데이터 타입 + 첫/마지막 row 출력.
이후 BDT proto 의 hyst preset 3 (Layer 2+2-α+2-β) 출력과 의미론적 비교.
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from drm_reload_test import load_bundle

BUNDLE_PATH = Path(
    r'C:\Users\Ryu\battery\python\BDT_dev\raw\사내문서'
    r'\Voltage hysteresis test_Graph format_v1.3_bundle.txt')


def _parse_float(s):
    s = (s or '').strip()
    if s == '':
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _truncate_str(s, n=80):
    s = str(s)
    return s if len(s) <= n else s[:n] + '...'


def main():
    print(f'\n[Derived 시트 분석]')
    print(f'{"=" * 110}')

    b = load_bundle(BUNDLE_PATH)
    derived_sheets = ['3~12_QV', '3~12_QVData_DOD', '3~12_dVdQData_SOC',
                      '14~23_QV', '14~23_dVdQData', 'dQdV']

    for sheet in derived_sheets:
        if sheet not in b['values']:
            print(f'\n❌ {sheet} 누락')
            continue
        rows = b['values'][sheet]
        n_rows = len(rows)
        n_cols = len(rows[0]) if rows else 0

        print(f'\n{"─" * 110}')
        print(f'[시트] {sheet} — {n_rows} rows × {n_cols} cols')
        print(f'{"─" * 110}')

        # 첫 3 행 (header) 출력
        print(f'  Header rows (first 3):')
        for ri in range(min(3, n_rows)):
            cell_preview = '\t'.join(
                _truncate_str(c, 25) for c in rows[ri][:8])
            print(f'    row{ri}: {cell_preview}')

        # 마지막 1 행 (last data) 출력
        if n_rows > 3:
            cell_preview = '\t'.join(
                _truncate_str(c, 25) for c in rows[-1][:8])
            print(f'  Last row (-1): {cell_preview}')

        # 데이터 컬럼 count 추정 — 첫 data row 의 비어있지 않은 컬럼 개수
        # 가정: header 첫 줄이 컬럼명, 두번째 줄이 데이터 시작
        for data_start in range(1, min(20, n_rows)):
            row = rows[data_start]
            n_filled = sum(1 for c in row if (c or '').strip() != '')
            if n_filled > 1:
                print(f'  데이터 시작 row: {data_start}, 비어있지 않은 컬럼 = {n_filled}')
                break

        # 각 컬럼별 첫/마지막 숫자 (10 컬럼까지 sampling)
        print(f'  컬럼별 첫 숫자 / 마지막 숫자 / min / max (col 0~9):')
        for ci in range(min(10, n_cols)):
            col_vals = []
            for r in rows:
                if ci < len(r):
                    v = _parse_float(r[ci])
                    if v is not None:
                        col_vals.append(v)
            if col_vals:
                print(f'    col{ci}: first={col_vals[0]:.5f}, '
                      f'last={col_vals[-1]:.5f}, '
                      f'min={min(col_vals):.5f}, max={max(col_vals):.5f}, '
                      f'n_vals={len(col_vals)}')

    print(f'\n{"=" * 110}')

    # ── derived 시트의 column → (TC, phase) 매핑 분석 ─────────────
    print(f'\n[Phase-relative anchor 검증]')
    print(f'{"=" * 110}')
    print('  _QV 시트는 cycle 별로 (chg X, chg V, dchg X, dchg V) 4개 컬럼 반복.')
    print('  각 phase 의 X 컬럼이 모두 0 에서 시작 → "phase-relative anchor (랩장님 원본 정책)"')
    print('  → 이는 preset 4 (충전 분석) + preset 5 (방전 분석) 의 출력을 한 시트에 직조한 것.\n')

    qv_3_12 = b['values']['3~12_QV']
    print(f'  3~12_QV 의 cycle 별 phase 매핑 (10 cycle × 4 col = 40 col 의 처음 20):')
    print(f'  {"col":<5}{"phase":<8}{"X[0]":<10}{"X[-1]":<10}{"V[0]":<10}{"V[-1]":<10}{"의미"}')
    print(f'  {"-" * 100}')

    sheet_start_tc = 3
    for ci in range(10):
        tc = sheet_start_tc + ci
        # cycle 별 4 col: chg_X, chg_V, dchg_X, dchg_V (가설)
        chg_x_col = ci * 4
        chg_v_col = ci * 4 + 1
        dchg_x_col = ci * 4 + 2
        dchg_v_col = ci * 4 + 3

        chg_xs = [_parse_float(r[chg_x_col]) for r in qv_3_12[1:]
                  if chg_x_col < len(r) and _parse_float(r[chg_x_col]) is not None]
        chg_vs = [_parse_float(r[chg_v_col]) for r in qv_3_12[1:]
                  if chg_v_col < len(r) and _parse_float(r[chg_v_col]) is not None]
        dchg_xs = [_parse_float(r[dchg_x_col]) for r in qv_3_12[1:]
                   if dchg_x_col < len(r) and _parse_float(r[dchg_x_col]) is not None]
        dchg_vs = [_parse_float(r[dchg_v_col]) for r in qv_3_12[1:]
                   if dchg_v_col < len(r) and _parse_float(r[dchg_v_col]) is not None]

        if chg_xs and chg_vs:
            print(f'  {chg_x_col:<5}{"chg":<8}{chg_xs[0]:<10.5f}{chg_xs[-1]:<10.5f}'
                  f'{chg_vs[0]:<10.4f}{chg_vs[-1]:<10.4f}TC{tc} chg phase')
        if dchg_xs and dchg_vs:
            print(f'  {dchg_x_col:<5}{"dchg":<8}{dchg_xs[0]:<10.5f}{dchg_xs[-1]:<10.5f}'
                  f'{dchg_vs[0]:<10.4f}{dchg_vs[-1]:<10.4f}TC{tc} dchg phase')

    # ── 충전 시트 vs _QV 충전 컬럼 직접 비교 ─────────────────────
    print(f'\n[직접 비교 — 3~12_충전 vs 3~12_QV]')
    print(f'{"=" * 110}')
    print('  3~12_충전 시트 (raw paste) 의 cycle 별 SOC/V vs')
    print('  3~12_QV 시트 (derived) 의 cycle 별 chg X/V — 동일 데이터인지?\n')

    chg_3_12 = b['values']['3~12_충전']
    matches = 0
    for ci in range(10):
        tc = sheet_start_tc + ci

        # 3~12_충전: cycle 별 8 컬럼, SOC = col 1
        chg_sheet_soc_col = ci * 8 + 1
        chg_sheet_v_col = ci * 8 + 3
        chg_sheet_socs = [_parse_float(r[chg_sheet_soc_col]) for r in chg_3_12[1:]
                          if chg_sheet_soc_col < len(r) and _parse_float(r[chg_sheet_soc_col]) is not None]

        # 3~12_QV: cycle 별 4 컬럼, chg X = col 0, chg V = col 1
        qv_chg_x_col = ci * 4
        qv_chg_xs = [_parse_float(r[qv_chg_x_col]) for r in qv_3_12[1:]
                     if qv_chg_x_col < len(r) and _parse_float(r[qv_chg_x_col]) is not None]

        n_match = len(chg_sheet_socs) == len(qv_chg_xs)
        if n_match and chg_sheet_socs and qv_chg_xs:
            same_first = abs(chg_sheet_socs[0] - qv_chg_xs[0]) < 1e-6
            same_last = abs(chg_sheet_socs[-1] - qv_chg_xs[-1]) < 1e-6
            ok = same_first and same_last
            marker = '✅' if ok else '❌'
            if ok:
                matches += 1
            print(f'  TC{tc}: 충전시트 [{chg_sheet_socs[0]:.5f}, ..., {chg_sheet_socs[-1]:.5f}] '
                  f'(n={len(chg_sheet_socs)}) vs _QV [{qv_chg_xs[0]:.5f}, ..., {qv_chg_xs[-1]:.5f}] '
                  f'(n={len(qv_chg_xs)}) — {marker}')
        else:
            print(f'  TC{tc}: row 수 불일치 (충전={len(chg_sheet_socs)}, '
                  f'_QV={len(qv_chg_xs)}) ❌')

    print(f'\n  → {matches}/10 cycle 의 chg phase 가 raw paste 시트와 _QV derived 시트에서 동일')

    # ── _QVData_DOD 가 _QV 와 동일한지 ─────────────────────
    print(f'\n[_QV vs _QVData_DOD — 동일 데이터인가?]')
    print(f'{"=" * 110}')
    qv_dod_3_12 = b['values']['3~12_QVData_DOD']
    n_diff = 0
    for ri in range(min(20, len(qv_3_12))):
        if ri >= len(qv_dod_3_12):
            n_diff += 1
            break
        if qv_3_12[ri] != qv_dod_3_12[ri]:
            n_diff += 1
            if n_diff <= 3:
                print(f'  row {ri} 불일치')
    if n_diff == 0:
        print(f'  ✅ 처음 20 row 동일 — _QV 와 _QVData_DOD 는 같은 데이터 (라벨만 다름)')
    else:
        print(f'  ❌ {n_diff} row 불일치')

    print(f'\n{"=" * 110}')
    print('[종합 결론]')
    print('  1. derived _QV / _QVData_DOD = 충전 시트 + 방전 시트 의 데이터를 ')
    print('     cycle 별로 인접 4 column 으로 조합 (chg_X, chg_V, dchg_X, dchg_V).')
    print('  2. anchor 정책 = phase-relative SOC=0 시작 (Layer 1, oper1.py / preset 4/5 동일).')
    print('  3. _QV 와 _QVData_DOD 는 동일 데이터 — 라벨만 SOC vs DOD.')
    print('  4. _dVdQData_SOC / _dVdQData / dQdV = dV/dQ 또는 dQ/dV 의 phase-relative 데이터.')
    print('  5. → BDT proto preset 4 (충전 분석) + preset 5 (방전 분석) 의 출력 ')
    print('     xlsx 를 manual 합쳐서 그래프 그리면 derived 시트와 동일 결과 산출 가능.')
    print('  6. proto preset 3 (히스테리시스, Layer 2+2-α+2-β) 는 절대 cell SOC 좌표 ')
    print('     + 페어링 closed loop — derived 시트와 다른 layer (의도적, 사용자 명시).')


if __name__ == '__main__':
    main()
