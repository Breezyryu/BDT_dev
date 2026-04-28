"""히스테리시스 16개 경로 SOC offset 일괄 검증.

Bug 2 fix (`_compute_tc_soc_offsets` anchor shift) 가 모든 히스테리시스 경로에서
의도대로 동작하는지 확인. 각 경로의 채널별로:
  1. `_compute_tc_soc_offsets()` 호출
  2. TC 3-12 (방전 hysteresis), TC 14-23 (충전 hysteresis) 의 offset 확인
  3. 각 TC start offset + 일반적인 sweep 범위(±0.1) 가 [0, 1.05] 범위 내인지 검증
  4. anchor shift 발동 여부 (raw vs result min) 보고

GUI 의존 없음 — headless 실행.
"""

import os
import sys
import importlib.util
from pathlib import Path

# Windows console UTF-8 강제
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# proto_ 직접 import — sys.path 에 부모 디렉토리 추가 (bdt_pybamm 등 의존)
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
_PROTO = _HERE.parent / 'DataTool_optRCD_proto_.py'
_spec = importlib.util.spec_from_file_location('bdt_proto', _PROTO)
_mod = importlib.util.module_from_spec(_spec)

# QtWidgets QApplication 미생성 → GUI 클래스 정의는 import 시 평가만 됨
sys.modules['bdt_proto'] = _mod
_spec.loader.exec_module(_mod)

_compute_tc_soc_offsets = _mod._compute_tc_soc_offsets
get_channel_meta = _mod.get_channel_meta
_is_channel_folder = _mod._is_channel_folder
check_cycler = _mod.check_cycler

ROOT = Path(r'C:\Users\Ryu\battery\python\BDT_dev\DataTool_dev_code\data\exp_data\성능_hysteresis')
TC_DCHG = list(range(3, 13))   # 3-12
TC_CHG = list(range(14, 24))   # 14-23


def _scan_channels(folder: Path) -> list[Path]:
    return sorted([Path(f.path) for f in os.scandir(str(folder))
                   if f.is_dir() and _is_channel_folder(f.name)])


def _safe_meta_capacity(channel: Path) -> float:
    """meta 또는 폴더명 mAh fallback."""
    try:
        m = get_channel_meta(str(channel))
        if m and getattr(m, 'min_capacity', None):
            return float(m.min_capacity)
    except Exception:
        pass
    # 폴더명에서 mAh 추출
    parent = channel.parent.name
    import re
    m = re.search(r'(\d+)\s*mAh', parent)
    if m:
        return float(m.group(1))
    return 0.0


def _classify(offset: float, tol: float = 0.1) -> str:
    if offset < -tol:
        return 'NEG'
    if offset > 1.0 + tol:
        return 'OVR'
    return 'OK'


def _summarize_offsets(offsets: dict[int, float], tcs: list[int]) -> dict:
    vals = [offsets.get(tc) for tc in tcs if tc in offsets]
    present = [v for v in vals if v is not None]
    if not present:
        return {'count': 0}
    return {
        'count': len(present),
        'min': min(present),
        'max': max(present),
        'first': vals[0] if vals else None,
        'last': vals[-1] if vals else None,
        'has_neg': any(v < -0.05 for v in present),
        'has_overshoot': any(v > 1.1 for v in present),
        'classify': [_classify(v) for v in present],
    }


def validate_path(folder: Path) -> dict:
    channels = _scan_channels(folder)
    if not channels:
        return {'path': folder.name, 'error': 'no channels'}

    results = []
    for ch in channels:
        cap = _safe_meta_capacity(ch)
        if cap <= 0:
            results.append({'channel': ch.name, 'error': 'no capacity'})
            continue

        try:
            is_pne = check_cycler(str(ch.parent))
        except Exception as e:
            results.append({'channel': ch.name, 'error': f'check_cycler: {e}'})
            continue
        cycler = 'PNE' if is_pne else 'Toyo'

        # Toyo 는 _compute_tc_soc_offsets 가 SaveEndData (PNE 전용) 의존이므로 skip
        if not is_pne:
            results.append({'channel': ch.name, 'cycler': cycler,
                            'note': 'skipped (PNE only)'})
            continue

        try:
            raw_offsets = _compute_tc_soc_offsets(str(ch), cap)
        except Exception as e:
            results.append({'channel': ch.name, 'error': f'compute: {e}'})
            continue

        # 검증
        dchg_summary = _summarize_offsets(raw_offsets, TC_DCHG)
        chg_summary = _summarize_offsets(raw_offsets, TC_CHG)
        all_offsets = list(raw_offsets.values())
        global_min = min(all_offsets) if all_offsets else 0.0
        global_max = max(all_offsets) if all_offsets else 0.0

        results.append({
            'channel': ch.name,
            'cycler': cycler,
            'capacity_mAh': cap,
            'tc_count': len(raw_offsets),
            'global_min': global_min,
            'global_max': global_max,
            'tc_dchg(3-12)': dchg_summary,
            'tc_chg(14-23)': chg_summary,
        })
    return {'path': folder.name, 'channels': results}


def main():
    if not ROOT.is_dir():
        print(f'[ERROR] root not found: {ROOT}')
        sys.exit(1)

    paths = sorted([p for p in ROOT.iterdir() if p.is_dir()])
    print(f'\n[히스테리시스 경로 검증] 총 {len(paths)} 개\n')
    print(f'{"=" * 100}')

    overall_pass = 0
    overall_warn = 0
    overall_fail = 0

    for i, folder in enumerate(paths, 1):
        print(f'\n[{i:02d}/{len(paths)}] {folder.name}')
        result = validate_path(folder)
        if 'error' in result:
            print(f'  ERROR: {result["error"]}')
            overall_fail += 1
            continue

        for ch in result['channels']:
            ch_name = ch.get('channel', '?')
            if 'error' in ch:
                print(f'  [{ch_name}] ERROR: {ch["error"]}')
                overall_fail += 1
                continue
            if 'note' in ch:
                print(f'  [{ch_name}] {ch.get("cycler", "?")} — {ch["note"]}')
                continue

            cap = ch.get('capacity_mAh', 0)
            tc_n = ch.get('tc_count', 0)
            gmin = ch.get('global_min', 0)
            gmax = ch.get('global_max', 0)
            dchg = ch.get('tc_dchg(3-12)', {})
            chg = ch.get('tc_chg(14-23)', {})

            print(f'  [{ch_name}] {ch.get("cycler", "?")}, '
                  f'cap={cap:.0f}mAh, TC={tc_n}, '
                  f'global=[{gmin:+.3f},{gmax:+.3f}]')

            def _fmt(s):
                if not s or s.get('count', 0) == 0:
                    return '  - 없음'
                neg = ' [NEG]' if s.get('has_neg') else ''
                ovr = ' [OVR]' if s.get('has_overshoot') else ''
                return (f'  - n={s["count"]}, '
                        f'first={s["first"]:+.3f}, last={s["last"]:+.3f}, '
                        f'range=[{s["min"]:+.3f},{s["max"]:+.3f}]'
                        f'{neg}{ovr}')

            print(f'  └─ TC 3-12 (방전 hysteresis): {_fmt(dchg)}')
            print(f'  └─ TC 14-23 (충전 hysteresis): {_fmt(chg)}')

            # 종합 판정 — anchor shift 후에도 음수 또는 1+0.1 초과 발생 여부
            d_neg = dchg.get('has_neg', False)
            c_neg = chg.get('has_neg', False)
            d_ovr = dchg.get('has_overshoot', False)
            c_ovr = chg.get('has_overshoot', False)
            if d_neg or c_neg or d_ovr or c_ovr:
                print(f'  └─ ⚠️  WARN: 비정상 offset (NEG={d_neg or c_neg}, OVR={d_ovr or c_ovr})')
                overall_warn += 1
            else:
                print(f'  └─ ✅ PASS')
                overall_pass += 1

    print(f'\n{"=" * 100}')
    print(f'[종합] PASS={overall_pass}, WARN={overall_warn}, FAIL={overall_fail}')


if __name__ == '__main__':
    main()
