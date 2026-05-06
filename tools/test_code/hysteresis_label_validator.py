"""히스테리시스 깊이 라벨 산출 검증 — 16개 경로 일괄 확인.

`_compute_tc_hysteresis_labels` + `_build_depth_rank_map` 의 동작을 16개
hysteresis 경로에 대해 점검:
  1. TC 별 라벨 (direction + depth_pct) 산출
  2. depth_pct 가 [10, 100] 범위인지
  3. TC 3-12 (방전 위주) 가 'Dchg' direction 인지
  4. TC 14-23 (충전 위주) 가 'Chg' direction 인지
  5. depth rank 가 100% → 0, 10% → N-1 로 정상 매핑되는지

GUI 의존 없음 — headless 실행.
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

_compute_tc_hysteresis_labels = _mod._compute_tc_hysteresis_labels
_build_depth_rank_map = _mod._build_depth_rank_map
get_channel_meta = _mod.get_channel_meta
_is_channel_folder = _mod._is_channel_folder
check_cycler = _mod.check_cycler
_build_channel_meta = _mod._build_channel_meta

ROOT = Path(r'C:\Users\Ryu\battery\python\BDT_dev\DataTool_dev_code\data\exp_data\성능_hysteresis')


def _safe_meta_capacity(channel: Path) -> float:
    try:
        m = get_channel_meta(str(channel))
        if m and getattr(m, 'min_capacity', None):
            return float(m.min_capacity)
    except Exception:
        pass
    parent = channel.parent.name
    import re
    m = re.search(r'(\d+)\s*mAh', parent)
    if m:
        return float(m.group(1))
    return 0.0


def main():
    if not ROOT.is_dir():
        print(f'[ERROR] root not found: {ROOT}')
        sys.exit(1)

    paths = sorted([p for p in ROOT.iterdir() if p.is_dir()])
    print(f'\n[히스테리시스 깊이 라벨 검증] 총 {len(paths)} 개\n')
    print(f'{"=" * 110}')

    overall_pass = 0
    overall_warn = 0
    overall_fail = 0

    for i, folder in enumerate(paths, 1):
        print(f'\n[{i:02d}/{len(paths)}] {folder.name[:90]}')

        channels = sorted([Path(f.path) for f in os.scandir(str(folder))
                           if f.is_dir() and _is_channel_folder(f.name)])
        if not channels:
            print('  ERROR: no channels')
            overall_fail += 1
            continue

        ch = channels[0]  # 대표 채널
        cap = _safe_meta_capacity(ch)
        if cap <= 0:
            print(f'  ERROR: no capacity for {ch.name}')
            overall_fail += 1
            continue

        try:
            is_pne = check_cycler(str(ch.parent))
        except Exception as e:
            print(f'  ERROR check_cycler: {e}')
            overall_fail += 1
            continue
        if not is_pne:
            print(f'  [{ch.name}] Toyo — skipped (PNE only)')
            continue

        # Phase 0 메타 빌드 (validator standalone 실행 — GUI 미경유)
        meta = get_channel_meta(str(ch))
        if meta is None:
            try:
                meta = _build_channel_meta(str(ch), capacity_override=cap)
            except Exception as e:
                print(f'  [{ch.name}] meta build 실패: {e}')

        classified = (meta.classified if meta and getattr(meta, 'classified', None)
                      else None)
        labels = _compute_tc_hysteresis_labels(str(ch), cap, classified)
        if not labels:
            print(f'  [{ch.name}] empty labels (no hysteresis TCs in classified)')
            overall_fail += 1
            continue
        ranks = _build_depth_rank_map(labels)

        # 분류 — TC 3-12, TC 14-23 그룹별 라벨 확인
        tc_3_12 = {tc: labels[tc] for tc in range(3, 13) if tc in labels}
        tc_14_23 = {tc: labels[tc] for tc in range(14, 24) if tc in labels}

        def _fmt_group(name, group):
            if not group:
                return f'  - {name}: 없음'
            dirs = set(g['direction'] for g in group.values())
            depths = sorted(set(g['depth_pct'] for g in group.values()), reverse=True)
            return (f'  - {name}: n={len(group)}, '
                    f'directions={dirs}, depth%={depths[:5]}{"..." if len(depths)>5 else ""}')

        print(f'  [{ch.name}] cap={cap:.0f}mAh, total TC={len(labels)}')
        print(_fmt_group('TC 3-12 (방전 hysteresis)', tc_3_12))
        print(_fmt_group('TC 14-23 (충전 hysteresis)', tc_14_23))

        # 검증
        warn = False
        # 1) 방전 hysteresis 그룹은 'Dchg' 가 우세해야 함
        if tc_3_12:
            n_dchg = sum(1 for g in tc_3_12.values() if g['direction'] == 'Dchg')
            if n_dchg < len(tc_3_12) * 0.5:  # 절반 이상 Dchg 기대
                print(f'  ⚠️  WARN: TC 3-12 방전 우세 아님 (Dchg={n_dchg}/{len(tc_3_12)})')
                warn = True

        # 2) 충전 hysteresis 그룹은 'Chg' 가 우세해야 함
        if tc_14_23:
            n_chg = sum(1 for g in tc_14_23.values() if g['direction'] == 'Chg')
            if n_chg < len(tc_14_23) * 0.5:
                print(f'  ⚠️  WARN: TC 14-23 충전 우세 아님 (Chg={n_chg}/{len(tc_14_23)})')
                warn = True

        # 3) depth_pct 범위 확인
        out_of_range = [tc for tc, g in labels.items()
                        if g['depth_pct'] < 10 or g['depth_pct'] > 100]
        if out_of_range:
            print(f'  ⚠️  WARN: depth_pct out of [10, 100]: TC={out_of_range}')
            warn = True

        # 4) rank 일관성 — rank 0 의 깊이가 max 와 일치해야 함
        if ranks:
            rank_0_tc = [tc for tc, r in ranks.items() if r == 0][0]
            max_depth = max(g['depth_pct'] for g in labels.values())
            if labels[rank_0_tc]['depth_pct'] != max_depth:
                print(f'  ⚠️  WARN: rank 0 TC={rank_0_tc} depth={labels[rank_0_tc]["depth_pct"]} '
                      f'≠ max={max_depth}')
                warn = True

        if warn:
            overall_warn += 1
        else:
            print(f'  ✅ PASS')
            overall_pass += 1

    print(f'\n{"=" * 110}')
    print(f'[종합] PASS={overall_pass}, WARN={overall_warn}, FAIL={overall_fail}')


if __name__ == '__main__':
    main()
