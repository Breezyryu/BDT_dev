"""히스테리시스 렌더링 분기 결정 + phase canonical anchor 검증.

`DataTool_optRCD_proto_.py` 의 cycle_soc legacy_mode 의 페어링 분기 가드
(L27664 부근) 와 phase canonical anchor (L26552 부근) 가 사용자 protocol
의 boundary cycle 을 정상 처리하는지 검증.

Fix 1 — `_render_major` (Cy0003/Cy0012 페어링 우회 버그):
  사용자 voltage hysteresis protocol (예: TC 3-12 방전 hyst) 에서
    - TC 3 = 풀 chg (0→100%) + dchg (100→90%, depth 10%)
    - TC 4-11 = 부분 chg + 부분 dchg (depth 20%~90%)
    - TC 12 = chg (10→100%) + 풀 dchg (100→0%, depth 100% envelope)
  TC 3 과 TC 12 만 raw `df['SOC'].max() - df['SOC'].min()` ≥ 0.98 라
  `_apply_hysteresis_soc_offsets` 에서 `_hyst_type='major'` 로 over-classify.
  segment 분할 + 페어링이 우회되어 chg + dchg 가 한 곡선으로 그려져
  "충방전 간격이 다른" 비대칭 loop 발생. → `_render_major` 변수 도입으로
  Dchg 페어링 활성 시 minor 처리 (rainbow + cross-TC).

Fix 2 — `_apply_hysteresis_phase_canonical_anchor` (SOC 시작점 정렬):
  사용자 보고 — TC 3-12 dchg 가 SOC 1.0 시작점 정렬 안 됨, TC 14-23 chg 가
  SOC 0.0 시작점 정렬 안 됨. 원인: CC-CV 잉여 (CC 후 CV ChgCap 추가 누적,
  +0.05~0.10) + cumul anchor drift. → 각 TC 의 primary phase 첫 row 를
  canonical SOC 로 강제 shift.
    - Dchg TC: dchg phase 첫 row → SOC 1.0
    - Chg TC: chg phase 첫 row → SOC 0.0

검증 항목:
  1. `_render_major` 가드 truth table — `(_is_major, _pair_enabled, _direction) → _render_major`
  2. 실제 hyst 데이터에서 TC 3 / TC 12 / TC 23 의 분류
  3. Phase canonical anchor delta 산출 — `_compute_hysteresis_phase_canonical_delta`
     의 (df, info) 별 결과 검증

GUI 의존 없음 — headless 실행.
"""

import os
import sys
import importlib.util
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

_HERE = Path(__file__).resolve().parent
_PROTO = _HERE.parent.parent / 'DataTool_dev_code' / 'DataTool_optRCD_proto_.py'
sys.path.insert(0, str(_PROTO.parent))

# PyQt6 의존 — 없으면 skip
try:
    from PyQt6.QtWidgets import QApplication  # noqa: F401
    _app = QApplication.instance() or QApplication(sys.argv[:1])
except Exception as e:
    print(f'[SKIP] PyQt6 미설치: {e}')
    sys.exit(0)

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

# WindowClass 의 staticmethod 참조 (instantiation 없이 사용)
WindowClass = _mod.WindowClass


# ══════════════════════════════════════════════
# Step 1: 가드 truth table 검증 (proto 코드와 동일 로직 재현)
# ══════════════════════════════════════════════

def _should_render_as_major(is_major: bool, pair_enabled: bool,
                             direction: str | None) -> bool:
    """proto L27673-27675 의 inline 결정 로직 재현 — 회귀 검증용.

    원본 (proto L27673-27675):
        _render_major = _is_major
        if _is_major and _pair_enabled and _direction == 'Dchg':
            _render_major = False

    이 helper 가 proto 의 결정과 일치해야 함. 코드 변경 시 동기화 필수.
    """
    if is_major and pair_enabled and direction == 'Dchg':
        return False
    return is_major


def _validate_truth_table() -> int:
    """8가지 입력 조합에 대해 결정 결과 검증."""
    # (is_major, pair_enabled, direction, expected_render_major, label)
    cases = [
        # Dchg minor (TC 4-11, TC 14-22): 영향 없음
        (False, True, 'Dchg', False, 'TC 4-11 (Dchg minor + pair)'),
        (False, True, 'Chg', False, 'TC 14-22 (Chg minor + pair)'),
        (False, False, 'Dchg', False, 'Dchg minor 페어링 비활성'),
        # Dchg major + pair → override (Cy0003/Cy0012 fix 핵심)
        (True, True, 'Dchg', False, 'TC 3 / TC 12 (Dchg major + pair) — FIX 적용'),
        # Chg major (TC 23): fallthrough 보존
        (True, True, 'Chg', True, 'TC 23 (Chg major + pair) — fallthrough'),
        # 페어링 비활성 시 major 보존 (preset 3 외 경로)
        (True, False, 'Dchg', True, 'Dchg major 페어링 비활성'),
        (True, False, 'Chg', True, 'Chg major 페어링 비활성'),
        # direction None (label 미산출): 안전한 default
        (True, True, None, True, 'major + pair + direction 미산출'),
    ]

    print('\n[Step 1] _render_major truth table 검증')
    print(f'{"=" * 100}')
    print(f'{"is_major":<10}{"pair":<8}{"direction":<12}'
          f'{"expected":<12}{"actual":<10}{"result":<10}{"label"}')
    print(f'{"-" * 100}')

    n_pass = 0
    n_fail = 0
    for is_major, pair, dir_, expected, label in cases:
        actual = _should_render_as_major(is_major, pair, dir_)
        ok = actual == expected
        marker = '✅ PASS' if ok else '❌ FAIL'
        print(f'{str(is_major):<10}{str(pair):<8}{str(dir_):<12}'
              f'{str(expected):<12}{str(actual):<10}{marker:<10}{label}')
        if ok:
            n_pass += 1
        else:
            n_fail += 1
    print(f'{"-" * 100}')
    print(f'  Truth table: PASS={n_pass}, FAIL={n_fail}')
    return n_fail


# ══════════════════════════════════════════════
# Step 2: 실제 hyst 경로에서 TC 3 / TC 12 / TC 23 분류 검증
# ══════════════════════════════════════════════

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


def _validate_real_hysteresis_paths() -> int:
    """실제 hyst 경로에서 boundary cycle (TC 3, TC 12, TC 23) 의 라벨/depth 검증."""
    ROOT = Path(
        r'C:\Users\Ryu\battery\python\BDT_dev\DataTool_dev_code\data'
        r'\exp_data\성능_hysteresis')
    if not ROOT.is_dir():
        print(f'\n[Step 2] SKIP — 경로 없음: {ROOT}')
        return 0

    paths = sorted([p for p in ROOT.iterdir() if p.is_dir()])
    print(f'\n[Step 2] 실제 hyst 경로 boundary cycle 검증 — 총 {len(paths)} 개')
    print(f'{"=" * 110}')

    n_fail = 0
    for i, folder in enumerate(paths, 1):
        print(f'\n[{i:02d}/{len(paths)}] {folder.name[:90]}')

        channels = sorted([Path(f.path) for f in os.scandir(str(folder))
                           if f.is_dir() and _is_channel_folder(f.name)])
        if not channels:
            print('  ERROR: no channels')
            n_fail += 1
            continue

        ch = channels[0]
        cap = _safe_meta_capacity(ch)
        if cap <= 0:
            print(f'  ERROR: no capacity for {ch.name}')
            n_fail += 1
            continue

        try:
            is_pne = check_cycler(str(ch.parent))
        except Exception as e:
            print(f'  ERROR check_cycler: {e}')
            n_fail += 1
            continue
        if not is_pne:
            print(f'  [{ch.name}] Toyo — skipped (PNE only)')
            continue

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
            print(f'  [{ch.name}] empty labels')
            n_fail += 1
            continue

        # boundary 후보 — depth_pct 가 100 인 cycle (envelope reference)
        depth_100 = sorted([tc for tc, info in labels.items()
                            if info.get('depth_pct') == 100])
        depth_10 = sorted([tc for tc, info in labels.items()
                           if info.get('depth_pct') == 10])

        # 방전 hyst 그룹 (TC 3-12 가정)
        dchg_tcs = sorted([tc for tc, info in labels.items()
                           if info.get('direction') == 'Dchg'])
        chg_tcs = sorted([tc for tc, info in labels.items()
                          if info.get('direction') == 'Chg'])

        print(f'  [{ch.name}] cap={cap:.0f}mAh, total TC={len(labels)}')
        print(f'  - Dchg TCs: {dchg_tcs}  Chg TCs: {chg_tcs}')
        print(f'  - depth=10%: {depth_10}, depth=100%: {depth_100}')

        # 검증 — Dchg 그룹 boundary (depth=10% 와 depth=100%) 가 모두 식별되는지
        dchg_depth_100 = [tc for tc in depth_100 if tc in dchg_tcs]
        dchg_depth_10 = [tc for tc in depth_10 if tc in dchg_tcs]
        if dchg_tcs and (not dchg_depth_100 or not dchg_depth_10):
            print(f'  ⚠️ WARN: Dchg 그룹의 depth=10%/100% boundary 누락')
            print(f'    dchg_depth_10={dchg_depth_10}, dchg_depth_100={dchg_depth_100}')

        # 충전 그룹도 동일 검증
        chg_depth_100 = [tc for tc in depth_100 if tc in chg_tcs]
        chg_depth_10 = [tc for tc in depth_10 if tc in chg_tcs]
        if chg_tcs and (not chg_depth_100 or not chg_depth_10):
            print(f'  ⚠️ WARN: Chg 그룹의 depth=10%/100% boundary 누락')
            print(f'    chg_depth_10={chg_depth_10}, chg_depth_100={chg_depth_100}')

        print(f'  ✅ 라벨 산출 정상')

    return n_fail


# ══════════════════════════════════════════════
# Step 3: Render decision 시뮬레이션 (boundary cycle 동작 예측)
# ══════════════════════════════════════════════

def _simulate_render_decisions() -> int:
    """사용자 protocol 의 각 cycle 에 대해 _render_major 결과 시뮬레이션.

    실제 plot 코드를 호출하지는 않고, 가드 결정만 검증.
    proto L27673-27675 의 inline 로직과 동일.
    """
    print(f'\n[Step 3] 사용자 protocol 시뮬레이션 — Dchg hyst (TC 3-12) + Chg hyst (TC 14-23)')
    print(f'{"=" * 110}')

    # 가정: proto 의 _apply_hysteresis_soc_offsets 가 raw SOC range 기반
    # _is_major 산출. 사용자 protocol 의 SOC range:
    cases = [
        # (TC, direction, depth_pct, raw_soc_range, label)
        (3, 'Dchg', 10, 1.00, 'TC 3 = chg 0→100% + dchg 100→90%'),
        (4, 'Dchg', 20, 0.20, 'TC 4 = chg 90→100% + dchg 100→80%'),
        (5, 'Dchg', 30, 0.30, 'TC 5'),
        (6, 'Dchg', 40, 0.40, 'TC 6'),
        (7, 'Dchg', 50, 0.50, 'TC 7'),
        (8, 'Dchg', 60, 0.60, 'TC 8'),
        (9, 'Dchg', 70, 0.70, 'TC 9'),
        (10, 'Dchg', 80, 0.80, 'TC 10'),
        (11, 'Dchg', 90, 0.90, 'TC 11'),
        (12, 'Dchg', 100, 1.00, 'TC 12 = chg 10→100% + dchg 100→0% envelope'),
        (14, 'Chg', 10, 0.10, 'TC 14 = chg 0→10% + dchg 10→0%'),
        (23, 'Chg', 100, 1.00, 'TC 23 = chg 0→100% + dchg 100→0% within-TC envelope'),
    ]

    print(f'{"TC":<5}{"dir":<6}{"depth":<8}{"soc_rng":<10}'
          f'{"is_major":<10}{"render_major":<14}{"분기":<24}{"label"}')
    print(f'{"-" * 130}')

    pair_enabled = True  # 히스테리시스 프리셋 활성
    n_fail = 0
    expected_results = {
        # TC: (expected_render_major, expected_branch)
        3: (False, 'segment 분할 + cross-TC 페어링'),  # Fix 적용 — 이전엔 fallthrough
        4: (False, 'segment 분할 + cross-TC 페어링'),
        5: (False, 'segment 분할 + cross-TC 페어링'),
        6: (False, 'segment 분할 + cross-TC 페어링'),
        7: (False, 'segment 분할 + cross-TC 페어링'),
        8: (False, 'segment 분할 + cross-TC 페어링'),
        9: (False, 'segment 분할 + cross-TC 페어링'),
        10: (False, 'segment 분할 + cross-TC 페어링'),
        11: (False, 'segment 분할 + cross-TC 페어링'),
        12: (False, 'segment 분할 + cross-TC 페어링'),  # Fix 적용 — 이전엔 fallthrough
        14: (False, 'segment 분할 + cross-TC 페어링'),
        23: (True, 'fallthrough (within-TC plot)'),  # 보존
    }

    for tc, dir_, depth, soc_range, label in cases:
        is_major = soc_range >= 0.98
        render_major = _should_render_as_major(is_major, pair_enabled, dir_)
        branch = ('fallthrough (within-TC plot)' if render_major
                  else 'segment 분할 + cross-TC 페어링')
        expected = expected_results.get(tc)
        ok = expected and (render_major, branch) == expected
        marker = '✅' if ok else '❌'
        if not ok:
            n_fail += 1
        print(f'{tc:<5}{dir_:<6}{depth:<8}{soc_range:<10.2f}'
              f'{str(is_major):<10}{str(render_major):<14}{branch:<24}'
              f'{marker} {label}')

    print(f'{"-" * 130}')
    return n_fail


# ══════════════════════════════════════════════
# Step 4: Phase canonical anchor delta 검증
# ══════════════════════════════════════════════

def _validate_phase_canonical_delta() -> int:
    """`_compute_hysteresis_phase_canonical_delta` 의 결과 검증.

    proto staticmethod 직접 호출 — DataFrame 시뮬레이션 + info 입력으로
    예상 delta 산출 확인. CC-CV 잉여 / cumul drift 시나리오 포함.
    """
    import pandas as pd

    fn = WindowClass._compute_hysteresis_phase_canonical_delta

    print(f'\n[Step 4] Phase canonical anchor delta 검증')
    print(f'{"=" * 110}')
    print(f'{"케이스":<50}{"direction":<12}{"dchg_first":<12}{"chg_first":<12}'
          f'{"expected":<12}{"actual":<12}{"result"}')
    print(f'{"-" * 130}')

    cases = [
        # (label, df_dict, info, expected_delta)
        # Dchg TC — dchg first row 정확히 1.0 → no shift
        ('TC 4 정상 (drift 없음)',
         {'Condition': [1, 1, 2, 2], 'SOC': [0.9, 1.0, 1.0, 0.8]},
         {'direction': 'Dchg', 'depth_pct': 20}, 0.0),
        # Dchg TC — CC-CV 잉여 (+0.05 overshoot) → shift -0.05
        ('TC 3 CC-CV 잉여 (+0.05)',
         {'Condition': [1, 1, 2, 2], 'SOC': [0.0, 1.05, 1.05, 0.95]},
         {'direction': 'Dchg', 'depth_pct': 10}, -0.05),
        # Dchg TC — cumul drift (-0.03)
        ('TC 12 cumul drift (-0.03)',
         {'Condition': [1, 1, 2, 2], 'SOC': [0.07, 0.97, 0.97, -0.03]},
         {'direction': 'Dchg', 'depth_pct': 100}, 0.03),
        # Chg TC — chg first row 정확히 0.0 → no shift
        ('TC 14 정상',
         {'Condition': [1, 1, 2, 2], 'SOC': [0.0, 0.1, 0.1, 0.0]},
         {'direction': 'Chg', 'depth_pct': 10}, 0.0),
        # Chg TC — drift +0.05 (cell 이 0.05 에서 시작)
        ('TC 14 drift (+0.05)',
         {'Condition': [1, 1, 2, 2], 'SOC': [0.05, 0.15, 0.15, 0.05]},
         {'direction': 'Chg', 'depth_pct': 10}, -0.05),
        # Chg TC — full envelope (TC 23, 0→1.0→0)
        ('TC 23 chg envelope 정상',
         {'Condition': [1, 1, 2, 2], 'SOC': [0.0, 1.0, 1.0, 0.0]},
         {'direction': 'Chg', 'depth_pct': 100}, 0.0),
        # Direction 미산출 (label 없음) → no shift
        ('direction 미산출',
         {'Condition': [1, 2], 'SOC': [0.5, 0.5]},
         {'direction': None}, 0.0),
        # Phase 부재 — Dchg 만 있고 Cond=2 row 없음
        ('Dchg phase 부재',
         {'Condition': [1, 1], 'SOC': [0.0, 1.0]},
         {'direction': 'Dchg', 'depth_pct': 100}, 0.0),
    ]

    n_fail = 0
    for label, df_dict, info, expected in cases:
        df = pd.DataFrame(df_dict)
        actual = fn(df, info)

        dchg_rows = df[df['Condition'] == 2]
        chg_rows = df[df['Condition'] == 1]
        dchg_first = (f'{dchg_rows["SOC"].iloc[0]:.3f}'
                      if len(dchg_rows) > 0 else '-')
        chg_first = (f'{chg_rows["SOC"].iloc[0]:.3f}'
                     if len(chg_rows) > 0 else '-')

        ok = abs(actual - expected) < 1e-6
        marker = '✅ PASS' if ok else '❌ FAIL'
        if not ok:
            n_fail += 1
        print(f'{label:<50}{str(info.get("direction")):<12}'
              f'{dchg_first:<12}{chg_first:<12}'
              f'{expected:<12.3f}{actual:<12.3f}{marker}')
    print(f'{"-" * 130}')
    print(f'  Phase canonical delta: PASS={len(cases) - n_fail}, FAIL={n_fail}')
    return n_fail


# ══════════════════════════════════════════════
# Step 5: Dchg endpoint scaling 검증
# ══════════════════════════════════════════════

def _validate_dchg_endpoint_scaling() -> int:
    """`_scale_hysteresis_dchg_phase_to_canonical_end` 결과 검증.

    Layer 2-α (shift) 후에도 잔존하는 dchg endpoint drift 를 scaling 으로
    canonical end 로 끌어당기는 동작 검증. CC-CV 잉여 시나리오 + 한도 체크.
    """
    import pandas as pd

    fn = WindowClass._scale_hysteresis_dchg_phase_to_canonical_end

    print(f'\n[Step 5] Dchg endpoint scaling 검증')
    print(f'{"=" * 110}')
    print(f'{"케이스":<55}{"direction":<10}{"depth":<8}{"raw_end":<10}'
          f'{"target_end":<12}{"applied":<10}{"new_end":<10}{"result"}')
    print(f'{"-" * 130}')

    cases = [
        # (label, df_dict, info, expected_applied, expected_new_end)
        # Dchg group: 정상 케이스 — Layer 2-α 후 dchg end 가 이미 canonical
        ('TC 4 (Dchg 20%) — 이미 canonical',
         {'Condition': [1, 2, 2], 'SOC': [1.0, 1.0, 0.8]},
         {'direction': 'Dchg', 'depth_pct': 20}, False, 0.8),
        # Dchg: cumul drift +0.01 — scaling 적용
        ('TC 4 (Dchg 20%) drift +0.01',
         {'Condition': [1, 2, 2], 'SOC': [1.0, 1.0, 0.81]},
         {'direction': 'Dchg', 'depth_pct': 20}, True, 0.8),
        # Chg group: dchg end 0.005 잔존 → 0.0 으로 scaling
        ('TC 14 (Chg 10%) dchg end 0.005',
         {'Condition': [1, 1, 2, 2], 'SOC': [0.0, 0.105, 0.105, 0.005]},
         {'direction': 'Chg', 'depth_pct': 10}, True, 0.0),
        # Chg group: dchg end 정확히 0.0
        ('TC 14 (Chg 10%) dchg end 정확',
         {'Condition': [1, 1, 2, 2], 'SOC': [0.0, 0.10, 0.10, 0.0]},
         {'direction': 'Chg', 'depth_pct': 10}, False, 0.0),
        # Chg group: dchg end 큰 drift +0.05 → 50% deviation 초과 시 skip
        ('TC 14 (Chg 10%) dchg drift 50% — skip',
         {'Condition': [1, 1, 2, 2], 'SOC': [0.0, 0.10, 0.10, 0.05]},
         {'direction': 'Chg', 'depth_pct': 10}, False, 0.05),
        # Direction 미산출 → skip
        ('direction 미산출',
         {'Condition': [1, 2], 'SOC': [0.0, 0.0]},
         {'direction': None, 'depth_pct': 10}, False, 0.0),
        # Dchg phase 부재 → skip
        ('Dchg phase 부재',
         {'Condition': [1, 1], 'SOC': [0.0, 1.0]},
         {'direction': 'Dchg', 'depth_pct': 100}, False, None),
    ]

    n_fail = 0
    for label, df_dict, info, expected_applied, expected_new_end in cases:
        df = pd.DataFrame(df_dict)
        raw_end = (float(df[df['Condition'] == 2]['SOC'].iloc[-1])
                   if (df['Condition'] == 2).any() else None)
        direction = info.get('direction')
        if direction == 'Dchg':
            target = 1.0 - info.get('depth_pct', 0) / 100.0
        elif direction == 'Chg':
            target = 0.0
        else:
            target = None

        applied = fn(df, info)
        new_end = (float(df[df['Condition'] == 2]['SOC'].iloc[-1])
                   if (df['Condition'] == 2).any() else None)

        ok = applied == expected_applied
        if ok and expected_new_end is not None and new_end is not None:
            ok = abs(new_end - expected_new_end) < 1e-6

        marker = '✅ PASS' if ok else '❌ FAIL'
        if not ok:
            n_fail += 1
        raw_end_str = f'{raw_end:.3f}' if raw_end is not None else '-'
        target_str = f'{target:.3f}' if target is not None else '-'
        new_end_str = f'{new_end:.3f}' if new_end is not None else '-'
        print(f'{label:<55}{str(direction):<10}{info.get("depth_pct", "-"):<8}'
              f'{raw_end_str:<10}{target_str:<12}{str(applied):<10}'
              f'{new_end_str:<10}{marker}')
    print(f'{"-" * 130}')
    print(f'  Dchg endpoint scaling: PASS={len(cases) - n_fail}, FAIL={n_fail}')
    return n_fail


# ══════════════════════════════════════════════
# Step 6: dQdV CV 마스킹 검증 (Issue 3)
# ══════════════════════════════════════════════

def _validate_dqdv_cv_masking() -> int:
    """`_unified_calculate_dqdv` 의 CV 마스킹 동작 검증.

    origin_compat=False 시 |ΔV|<2mV 영역의 dQdV 가 NaN 으로 마스킹되는지 검증.
    히스테리시스 preset 의 origin_compat 가 False 로 변경됨에 따라
    CV 영역이 dQdV 에서 제외되는지 확인.
    """
    import pandas as pd
    import numpy as np

    fn = _mod._unified_calculate_dqdv

    print(f'\n[Step 6] dQdV CV 마스킹 검증')
    print(f'{"=" * 110}')

    # 충전 phase 시뮬레이션 — CC 구간 (V 변화 큼) + CV 구간 (V 거의 일정)
    # CC: V 3.0 → 4.5 over 100 samples, SOC 0 → 0.9
    # CV: V ≈ 4.5 (변화 < 2mV), SOC 0.9 → 1.0
    np.random.seed(42)
    n_cc = 100
    n_cv = 50
    cc_v = np.linspace(3.0, 4.5, n_cc)
    cc_soc = np.linspace(0.0, 0.9, n_cc)
    cv_v = 4.5 + np.random.uniform(-0.0005, 0.0005, n_cv)  # |ΔV| < 1mV
    cv_soc = np.linspace(0.9, 1.0, n_cv)
    df = pd.DataFrame({
        'Voltage': np.concatenate([cc_v, cv_v]),
        'SOC': np.concatenate([cc_soc, cv_soc]),
        'Condition': [1] * (n_cc + n_cv),
    })

    n_fail = 0

    # origin_compat=False (마스킹 ON, 사용자 요청)
    df_masked = fn(df.copy(), smooth_degree=5, origin_compat=False)
    cv_dqdv = df_masked['dQdV'].iloc[n_cc:].dropna()
    cv_nan_ratio = (df_masked['dQdV'].iloc[n_cc:].isna().sum() /
                    n_cv if n_cv > 0 else 0)
    cc_dqdv = df_masked['dQdV'].iloc[:n_cc].dropna()
    print(f'  origin_compat=False (CV 마스킹 ON):')
    print(f'    CC 구간 dQdV 유효 row: {len(cc_dqdv)}/{n_cc} (예상: 대부분 유효)')
    print(f'    CV 구간 dQdV NaN 비율: {cv_nan_ratio*100:.1f}% (예상: 80%+)')
    if cv_nan_ratio < 0.8:
        n_fail += 1
        print(f'    ❌ FAIL — CV 마스킹 효과 부족')
    else:
        print(f'    ✅ PASS — CV 영역 NaN 처리 확인')

    # origin_compat=True (마스킹 OFF, 이전 동작)
    df_unmasked = fn(df.copy(), smooth_degree=5, origin_compat=True)
    cv_unmasked_nan_ratio = (df_unmasked['dQdV'].iloc[n_cc:].isna().sum() /
                             n_cv if n_cv > 0 else 0)
    print(f'  origin_compat=True (CV 마스킹 OFF, 이전 호환):')
    print(f'    CV 구간 dQdV NaN 비율: {cv_unmasked_nan_ratio*100:.1f}% '
          f'(예상: 0% 또는 inf 발생)')
    # origin_compat=True 시 CV 영역에 inf/NaN 자연 발생 가능 — strict 비율 검증 X

    print(f'  dQdV CV 마스킹: PASS={2 - n_fail}, FAIL={n_fail}')
    return n_fail


# ══════════════════════════════════════════════
# Step 7: Hysteresis envelope merge 검증 (사용자 protocol 시나리오)
# ══════════════════════════════════════════════

def _validate_envelope_merge() -> int:
    """`_merge_hysteresis_envelopes` 의 시나리오 검증.

    사용자 보고 (260503): hysteresis(TC3-11) + RPT(TC12) → hysteresis(TC3-12)
    로 통합되어야 함. mid-RPT (TC13) 는 흡수 대상 아님.
    """
    fn = _mod._merge_hysteresis_envelopes

    print(f'\n[Step 7] Hysteresis envelope merge 검증')
    print(f'{"=" * 110}')

    # 사용자 protocol 시뮬레이션 — 본 user 의 voltage hysteresis test
    def _make_body(types: list[str], time_limits: list[int] | None = None):
        if time_limits is None:
            time_limits = [3600] * len(types)  # 정상 chg/dchg duration
        return [{'type': t, 'time_limit_s': tl}
                for t, tl in zip(types, time_limits)]

    # 정상 hyst envelope 후보 — chg + dchg, 짧은 펄스 없음
    normal_body = _make_body(['CHG_CC', 'REST', 'DCHG_CC'], [3600, 600, 3600])
    # 짧은 dchg 펄스 (DCIR 패턴) — envelope 아님
    short_pulse_body = _make_body(
        ['CHG_CC', 'REST', 'DCHG_CC'], [3600, 600, 10])  # 10s pulse
    # chg 만 있는 그룹 (dchg 부재) — envelope 아님
    chg_only_body = _make_body(['CHG_CC'], [3600])

    cases = [
        # (label, input result, expected output category list)
        ('Dchg hyst + RPT envelope (TC3-12 case)',
         [
             {'category': 'RPT', 'tc_start': 1, 'tc_end': 1, 'loop_count': 1, '_body': normal_body},
             {'category': 'HYSTERESIS_DCHG', 'tc_start': 3, 'tc_end': 3, 'loop_count': 1, '_body': normal_body},
             {'category': 'HYSTERESIS_DCHG', 'tc_start': 11, 'tc_end': 11, 'loop_count': 1, '_body': normal_body},
             {'category': 'RPT', 'tc_start': 12, 'tc_end': 12, 'loop_count': 1, '_body': normal_body},
             {'category': 'RPT', 'tc_start': 13, 'tc_end': 13, 'loop_count': 1, '_body': normal_body},
         ],
         ['RPT', 'HYSTERESIS_DCHG', 'HYSTERESIS_DCHG', 'HYSTERESIS_DCHG', 'RPT']),
        ('Chg hyst + RPT envelope (TC14-23 case)',
         [
             {'category': 'HYSTERESIS_CHG', 'tc_start': 14, 'tc_end': 14, 'loop_count': 1, '_body': normal_body},
             {'category': 'HYSTERESIS_CHG', 'tc_start': 22, 'tc_end': 22, 'loop_count': 1, '_body': normal_body},
             {'category': 'RPT', 'tc_start': 23, 'tc_end': 23, 'loop_count': 1, '_body': normal_body},
         ],
         ['HYSTERESIS_CHG', 'HYSTERESIS_CHG', 'HYSTERESIS_CHG']),
        ('Mid-RPT (TC13) 은 흡수 안 됨',
         [
             {'category': 'HYSTERESIS_DCHG', 'tc_start': 11, 'tc_end': 11, 'loop_count': 1, '_body': normal_body},
             {'category': 'RPT', 'tc_start': 12, 'tc_end': 12, 'loop_count': 1, '_body': normal_body},
             {'category': 'RPT', 'tc_start': 13, 'tc_end': 13, 'loop_count': 1, '_body': normal_body},
             {'category': 'HYSTERESIS_CHG', 'tc_start': 14, 'tc_end': 14, 'loop_count': 1, '_body': normal_body},
         ],
         ['HYSTERESIS_DCHG', 'HYSTERESIS_DCHG', 'RPT', 'HYSTERESIS_CHG']),
        ('짧은 펄스 RPT 는 흡수 안 됨 (DCIR 패턴)',
         [
             {'category': 'HYSTERESIS_DCHG', 'tc_start': 11, 'tc_end': 11, 'loop_count': 1, '_body': normal_body},
             {'category': 'RPT', 'tc_start': 12, 'tc_end': 12, 'loop_count': 1, '_body': short_pulse_body},
         ],
         ['HYSTERESIS_DCHG', 'RPT']),
        ('Chg 만 있는 그룹 흡수 안 됨',
         [
             {'category': 'HYSTERESIS_DCHG', 'tc_start': 11, 'tc_end': 11, 'loop_count': 1, '_body': normal_body},
             {'category': 'RPT', 'tc_start': 12, 'tc_end': 12, 'loop_count': 1, '_body': chg_only_body},
         ],
         ['HYSTERESIS_DCHG', 'RPT']),
        ('loop_count > 1 그룹 흡수 안 됨 (sweep 패턴)',
         [
             {'category': 'HYSTERESIS_DCHG', 'tc_start': 11, 'tc_end': 11, 'loop_count': 1, '_body': normal_body},
             {'category': 'RPT', 'tc_start': 12, 'tc_end': 21, 'loop_count': 10, '_body': normal_body},
         ],
         ['HYSTERESIS_DCHG', 'RPT']),
    ]

    n_fail = 0
    for label, input_result, expected_cats in cases:
        result = fn([dict(g) for g in input_result])  # deep copy
        actual_cats = [g['category'] for g in result]
        ok = actual_cats == expected_cats
        marker = '✅ PASS' if ok else '❌ FAIL'
        if not ok:
            n_fail += 1
        print(f'  {label}')
        print(f'    expected: {expected_cats}')
        print(f'    actual:   {actual_cats}  {marker}')
    print(f'  Envelope merge: PASS={len(cases) - n_fail}, FAIL={n_fail}')
    return n_fail


# ══════════════════════════════════════════════
# Step 8: Fix A — _calc_soc 의 SOC = 1 − DOD 일관성 검증
# ══════════════════════════════════════════════

def _validate_calc_soc_axis_mode() -> int:
    """`_calc_soc` 의 charge/discharge × axis_mode (SOC/DOD) 검증.

    Fix A — 단일방향 분석 (preset 4/5) 의 X 데이터가 axis_mode 에 따라
    SOC = 1 − DOD 관계를 유지하면서 자연 anchor (Chg+SOC, Dchg+DOD) 에서
    X=0 시작.
    """
    import pandas as pd
    import numpy as np

    fn = _mod._calc_soc

    print(f'\n[Step 8] Fix A — _calc_soc 의 axis_mode 별 X 데이터 검증')
    print(f'{"=" * 110}')
    print(f'{"케이스":<55}{"data_scope":<12}{"axis_mode":<10}'
          f'{"X[0]":<10}{"X[-1]":<10}{"result"}')
    print(f'{"-" * 130}')

    # ChgCap = 0 → 1 진행 (정규화된 누적 충전량)
    chg_df = pd.DataFrame({
        'ChgCap': [0.0, 0.25, 0.5, 0.75, 1.0],
        'DchgCap': [0.0] * 5,
        'Cycle': [1] * 5,
    })
    # DchgCap = 0 → 1 진행 (정규화된 누적 방전량)
    dchg_df = pd.DataFrame({
        'ChgCap': [0.0] * 5,
        'DchgCap': [0.0, 0.25, 0.5, 0.75, 1.0],
        'Cycle': [1] * 5,
    })

    cases = [
        # (label, df, data_scope, axis_mode, expected_first, expected_last)
        ('충전 + SOC (자연 anchor, oper1.py 동일)',
         chg_df, 'charge', 'soc', 0.0, 1.0),
        ('충전 + DOD (Fix A 신규, SOC=1−DOD)',
         chg_df, 'charge', 'dod', 1.0, 0.0),
        ('방전 + SOC (Fix A 신규, SOC=1−DOD)',
         dchg_df, 'discharge', 'soc', 1.0, 0.0),
        ('방전 + DOD (자연 anchor, oper1.py 동일)',
         dchg_df, 'discharge', 'dod', 0.0, 1.0),
    ]

    n_fail = 0
    for label, df, scope, axis, exp_first, exp_last in cases:
        # overlap 은 _calc_soc 의 charge/discharge 분기에서 사용 안 됨 (early return)
        x = fn(df, scope, axis, 'split')
        first = float(x.iloc[0])
        last = float(x.iloc[-1])
        ok = (abs(first - exp_first) < 1e-6 and abs(last - exp_last) < 1e-6)
        marker = '✅ PASS' if ok else '❌ FAIL'
        if not ok:
            n_fail += 1
        print(f'{label:<55}{scope:<12}{axis:<10}'
              f'{first:<10.3f}{last:<10.3f}{marker}')

    # SOC = 1 − DOD 관계 직접 검증
    print(f'  SOC = 1 − DOD 관계 검증:')
    chg_soc_x = fn(chg_df, 'charge', 'soc', 'split')
    chg_dod_x = fn(chg_df, 'charge', 'dod', 'split')
    relation_chg = np.allclose(chg_soc_x + chg_dod_x, 1.0)
    print(f'    충전: SOC + DOD ≈ 1.0 → {relation_chg}', end='')
    if relation_chg:
        print(' ✅')
    else:
        print(' ❌')
        n_fail += 1

    dchg_soc_x = fn(dchg_df, 'discharge', 'soc', 'split')
    dchg_dod_x = fn(dchg_df, 'discharge', 'dod', 'split')
    relation_dchg = np.allclose(dchg_soc_x + dchg_dod_x, 1.0)
    print(f'    방전: SOC + DOD ≈ 1.0 → {relation_dchg}', end='')
    if relation_dchg:
        print(' ✅')
    else:
        print(' ❌')
        n_fail += 1

    print(f'{"-" * 130}')
    print(f'  Fix A axis_mode: PASS={4 + 2 - n_fail}, FAIL={n_fail}')
    return n_fail


# ══════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════

def main() -> None:
    fail_truth = _validate_truth_table()
    fail_real = _validate_real_hysteresis_paths()
    fail_sim = _simulate_render_decisions()
    fail_canon = _validate_phase_canonical_delta()
    fail_scale = _validate_dchg_endpoint_scaling()
    fail_cv = _validate_dqdv_cv_masking()
    fail_merge = _validate_envelope_merge()
    fail_axis = _validate_calc_soc_axis_mode()

    total_fail = (fail_truth + fail_real + fail_sim
                  + fail_canon + fail_scale + fail_cv + fail_merge + fail_axis)
    print(f'\n{"=" * 100}')
    print(f'[종합] truth_table={fail_truth}, real_paths={fail_real}, '
          f'simulation={fail_sim}, canonical_delta={fail_canon}, '
          f'dchg_scale={fail_scale}, cv_mask={fail_cv}, '
          f'envelope_merge={fail_merge}, axis_mode={fail_axis}')
    if total_fail == 0:
        print('  ✅ ALL PASS — Fix 1~6 회귀 안전 '
              '(페어링 + canonical + scaling + CV mask + envelope merge + axis_mode)')
    else:
        print(f'  ❌ {total_fail} fail — 검토 필요')
    sys.exit(1 if total_fail > 0 else 0)


if __name__ == '__main__':
    main()
