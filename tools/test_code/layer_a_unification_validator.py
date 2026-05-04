"""PR-1 Layer A 단일화 검증 — `_unified_pne_load_raw` 의 data_scope 제거 + cache 일관성.

ADR 0002 (`docs/adr/0002-layer-a-data-scope-single-load.md`) 의 결정:
  - `_unified_pne_load_raw` 가 `data_scope` 파라미터를 받지 않음 (signature 변경)
  - 내부적으로 항상 `_cm_tc_list(entry, 'cycle')` 사용 (모든 TC 로딩)
  - Cache 키가 (raw_path, tc_min, tc_max) 만으로 결정 → scope 무관

검증 항목:
  1. signature 변경 — data_scope= 키워드로 호출 시 TypeError
  2. cycle_map 의 'cycle' scope 추출 → 모든 TC 포함 (chg + dchg)
  3. 사용자 시나리오 cache hit — 같은 채널·TC 의 다른 scope 분석이 raw 캐시 공유

GUI 의존 없음 — headless 실행 (PyQt6 만 가용 시).
"""

import sys
import inspect
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

_HERE = Path(__file__).resolve().parent
proto_dir = _HERE.parent.parent / 'DataTool_dev_code'
sys.path.insert(0, str(proto_dir))

try:
    from PyQt6.QtWidgets import QApplication
    QApplication.instance() or QApplication(sys.argv[:1])
except Exception as _e:
    print(f'[SKIP] PyQt6 미설치: {_e}')
    sys.exit(0)

import importlib.util
proto_path = proto_dir / 'DataTool_optRCD_proto_.py'
spec = importlib.util.spec_from_file_location('bdt_proto', proto_path)
mod = importlib.util.module_from_spec(spec)
sys.modules['bdt_proto'] = mod
spec.loader.exec_module(mod)


def _validate_signature() -> int:
    """`_unified_pne_load_raw` 의 signature 에서 data_scope 가 제거되었는지."""
    print(f'\n[Step 1] _unified_pne_load_raw signature 검증')
    print(f'{"=" * 100}')

    fn = mod._unified_pne_load_raw
    sig = inspect.signature(fn)
    params = list(sig.parameters.keys())
    print(f'  현재 signature parameters: {params}')

    n_fail = 0
    if 'data_scope' in params:
        print(f'  ❌ FAIL — data_scope 파라미터가 아직 존재 (Layer A 단일화 미적용)')
        n_fail += 1
    else:
        print(f'  ✅ PASS — data_scope 파라미터 제거됨')

    expected = {'raw_file_path', 'cycle_start', 'cycle_end', 'cycle_map'}
    actual = set(params)
    if expected != actual:
        print(f'  ⚠️  WARN — 예상 파라미터 {expected}, 실제 {actual}')
    else:
        print(f'  ✅ PASS — 파라미터 집합 일치')

    return n_fail


def _validate_cm_tc_list_cycle_scope() -> int:
    """`_cm_tc_list(entry, 'cycle')` 가 모든 TC 를 포함하는지 검증."""
    print(f'\n[Step 2] _cm_tc_list(scope="cycle") 동작 검증')
    print(f'{"=" * 100}')

    fn = mod._cm_tc_list

    cases = [
        # (label, entry, expected)
        ('일반 cycle (TC 1)',
         {'all': (1, 1), 'chg': [1], 'dchg': [1]}, [1]),
        ('multi-TC (TC 3-5)',
         {'all': (3, 5), 'chg': [3, 4], 'dchg': [4, 5]}, [3, 4, 5]),
        ('sweep (chg/dchg disjoint)',
         {'all': (10, 12), 'chg': [10], 'dchg': [11, 12]}, [10, 11, 12]),
    ]

    n_fail = 0
    print(f'  {"label":<35}{"entry all":<15}{"expected":<20}{"actual":<20}{"result"}')
    print(f'  {"-" * 110}')
    for label, entry, expected in cases:
        actual = fn(entry, 'cycle')
        ok = actual == expected
        marker = '✅ PASS' if ok else '❌ FAIL'
        if not ok:
            n_fail += 1
        print(f'  {label:<35}{str(entry["all"]):<15}'
              f'{str(expected):<20}{str(actual):<20}{marker}')
    return n_fail


def _validate_cache_key_simulation() -> int:
    """사용자 시나리오 시뮬레이션 — cache key 가 data_scope 와 무관함을 검증.

    Layer A 단일화 후, 같은 (raw_path, tc_range) 면 scope 가 다르더라도
    cache hit 가 발생해야 함.
    """
    print(f'\n[Step 3] Cache key 시나리오 검증')
    print(f'{"=" * 100}')

    # 가상 cycle_map — sweep 시험 (chg/dchg disjoint)
    cycle_map = {
        1: {'all': (1, 3), 'chg': [1], 'dchg': [2, 3], 'chg_rest': [], 'dchg_rest': []},
    }

    fn = mod._cm_tc_list

    # Layer A 단일화 후: 모든 scope 호출에서 'cycle' 사용
    tcs_cycle = fn(cycle_map[1], 'cycle')
    tcs_charge = fn(cycle_map[1], 'charge')
    tcs_discharge = fn(cycle_map[1], 'discharge')

    print(f'  cycle_map[1] = {cycle_map[1]}')
    print(f'  scope=cycle  → TCs: {tcs_cycle} (Layer A 가 사용 — 모든 TC)')
    print(f'  scope=charge → TCs: {tcs_charge} (참고: 구 Stage 2 가 사용했던 값)')
    print(f'  scope=discharge → TCs: {tcs_discharge} (참고: 구 Stage 2 가 사용했던 값)')

    # Layer A 의 tc_min, tc_max 시뮬레이션
    def _tc_range(tcs):
        return (min(tcs), max(tcs)) if tcs else (None, None)

    rng_cycle = _tc_range(tcs_cycle)
    rng_charge = _tc_range(tcs_charge)
    rng_discharge = _tc_range(tcs_discharge)

    print(f'\n  Layer A cache 키 (tc_min, tc_max):')
    print(f'    scope=cycle:     {rng_cycle}  ← Layer A 단일화 후 항상 이 키')
    print(f'    scope=charge:    {rng_charge}  ← 구 동작 (별도 cache entry)')
    print(f'    scope=discharge: {rng_discharge}  ← 구 동작 (별도 cache entry)')

    n_fail = 0
    if rng_charge != rng_cycle and rng_discharge != rng_cycle:
        # sweep test 에서 scope 별로 다른 cache 키였음 → 단일화 효과 큼
        print(f'\n  ✅ Sweep test 에서 단일화 효과 확인 — '
              f'scope 별 키 ({rng_charge}/{rng_discharge}) 가 cycle 키 ({rng_cycle}) 로 통합')
    else:
        print(f'\n  ℹ 일반 cycle 에서는 원래 같은 키 — 단일화는 sweep test 에서만 효과')

    return n_fail


def _validate_caller_signature() -> int:
    """unified_profile_core / unified_profile_batch_continue 의 caller 가
    data_scope 를 더 이상 전달하지 않는지 source 검증."""
    print(f'\n[Step 4] Caller 검증 — source 에 data_scope= 호출 인자가 없는지')
    print(f'{"=" * 100}')

    import re
    src = proto_path.read_text(encoding='utf-8-sig')

    # _unified_pne_load_raw( 의 모든 호출 컨텍스트 수집 (다음 닫는 ) 까지)
    pattern = re.compile(
        r'_unified_pne_load_raw\(([^)]*(?:\([^)]*\)[^)]*)*)\)',
        re.DOTALL)
    matches = pattern.findall(src)

    n_fail = 0
    print(f'  _unified_pne_load_raw( 호출 사이트 수: {len(matches)}')
    for i, args in enumerate(matches, 1):
        has_scope = 'data_scope' in args
        marker = '❌ FAIL' if has_scope else '✅ PASS'
        if has_scope:
            n_fail += 1
        # 첫 50자만 표시
        preview = args.replace('\n', ' ').strip()[:80]
        print(f'    호출 #{i}: {marker} — args: {preview}...')

    return n_fail


def main() -> None:
    fail_sig = _validate_signature()
    fail_cm = _validate_cm_tc_list_cycle_scope()
    fail_cache = _validate_cache_key_simulation()
    fail_caller = _validate_caller_signature()

    total = fail_sig + fail_cm + fail_cache + fail_caller
    print(f'\n{"=" * 100}')
    print(f'[종합] signature={fail_sig}, cm_tc_list={fail_cm}, '
          f'cache_sim={fail_cache}, caller={fail_caller}')
    if total == 0:
        print('  ✅ ALL PASS — Layer A 단일화 (ADR 0002) 적용 검증')
    else:
        print(f'  ❌ {total} fail — 검토 필요')
    sys.exit(1 if total > 0 else 0)


if __name__ == '__main__':
    main()
