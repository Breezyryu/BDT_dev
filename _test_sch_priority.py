"""classify_channel_path() .sch 우선 전략 검증 테스트

PNE 채널에서 .sch가 있으면 test_type/pattern이 .sch 기반인지,
없으면 CSV 폴백인지 확인.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'DataTool_dev'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'analysis_dev_env', 'pne_schedule'))

from DataTool_optRCD_proto_ import classify_channel_path, _find_sch_file

# ── PNE 채널 샘플 (rawdata에서 .sch 있는 경로) ──
rawdata = os.path.join(os.path.dirname(__file__), 'rawdata')

test_cases = []
for entry in os.scandir(rawdata):
    if not entry.is_dir() or entry.name.startswith('!'):
        continue
    # 채널 서브폴더 찾기 (M01Ch...[NNN] 또는 [NNN] 패턴)
    for sub in os.scandir(entry.path):
        if sub.is_dir() and '[' in sub.name and sub.name != 'Pattern':
            test_cases.append((entry.name, sub.path))
            break  # 첫 번째 채널만

print(f'=== .sch 우선 전략 검증 ({len(test_cases)}개 데이터셋) ===\n')

ok = 0
fail = 0
for dataset_name, ch_path in test_cases:
    sch = _find_sch_file(ch_path)
    has_sch = sch is not None

    cr = classify_channel_path(ch_path, 0)
    if cr is None:
        print(f'  SKIP  {dataset_name}  (분류 실패)')
        continue

    has_sch_info = 'sch_info' in cr
    src = 'sch' if has_sch_info else 'csv'

    # 검증: .sch 있으면 sch_info 존재해야 함
    if has_sch and has_sch_info:
        status = 'OK'
        ok += 1
    elif not has_sch and not has_sch_info:
        status = 'OK'
        ok += 1
    else:
        status = 'FAIL'
        fail += 1

    print(f'  {status}  [{src}] {dataset_name}')
    print(f'         test_type={cr["test_type"]}  pattern={cr["schedule_pattern"][:60]}')
    if has_sch_info:
        info = cr['sch_info']
        print(f'         sch: type={info["schedule_type"]}  rss={info["has_rss"]}  gitt={info["has_gitt_hppc"]}')
    print()

print(f'결과: OK={ok}  FAIL={fail}  총={ok + fail}')
