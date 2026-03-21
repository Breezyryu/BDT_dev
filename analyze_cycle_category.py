"""
===============================================================================
사이클 카테고리 분석기 (Cycle Category Analyzer)
===============================================================================
  충방전 데이터 상위 경로를 스캔하여:
    1) PNE / Toyo 충방전기 자동 감지
    2) 각 사이클의 용도를 분류: RPT, Rss, 가속수명
    3) 스케줄 패턴 분석 및 통계
    4) 텍스트 리포트 + CSV + JSON 출력

  사이클 카테고리:
    - RPT      : 0.2C 충방전 (기준 용량 측정)
    - Rss      : DCIR 측정용 다단 pulse
    - 가속수명  : 멀티스텝 충전 (고속 충전 수명 시험)
    - GITT     : GITT 펄스 그룹 (동일 동작 펄스 반복 → 논리 사이클로 병합)
    - initial  : 초기 반사이클 (방전만)
    - unknown  : 분류 불가

  사이클 정의:
    하나의 '사이클'은 '충전→방전' 또는 '방전→충전' 쌍.
    같은 동작(CHG만 또는 DCHG만)의 펄스가 연속 반복되면 → 하나의 펄스 그룹으로 병합,
    인접한 반대 동작 펄스 그룹과 합쳐 하나의 논리 사이클 구성.

  사용법:
    python analyze_cycle_category.py [데이터경로]
    python analyze_cycle_category.py [데이터경로1] [데이터경로2] ...
  기본값: 스크립트와 같은 위치의 rawdata/ 폴더
===============================================================================
"""

import os
import re
import sys
import json
import time
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

import pandas as pd
import numpy as np

# stdout 버퍼링 해제
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass


# ═══════════════════════════════════════════════════════════════════
# 1. 상수 및 CLI
# ═══════════════════════════════════════════════════════════════════

CATEGORY_LABELS = {
    'RPT': 'RPT (0.2C 충방전)',
    'Rss': 'Rss (DCIR pulse)',
    '가속수명': '가속수명 (멀티스텝 충전)',
    'GITT': 'GITT (펄스 그룹)',
    'initial': 'initial (초기 반사이클)',
    'unknown': 'unknown (분류불가)',
}


def parse_args() -> list[Path]:
    """CLI 인자 파싱 → 분석 대상 경로 목록 반환."""
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    if not args:
        # 기본값: 스크립트 위치의 rawdata/
        default = Path(__file__).parent / 'rawdata'
        if default.is_dir():
            args = [str(default)]
        else:
            print("ERROR: rawdata/ 폴더를 찾을 수 없습니다.")
            print("  사용법: python analyze_cycle_category.py [데이터경로]")
            sys.exit(1)

    paths = []
    for a in args:
        p = Path(a)
        if not p.is_absolute():
            p = Path.cwd() / p
        if not p.is_dir():
            print(f"WARNING: 경로가 존재하지 않아 건너뜀: {p}")
            continue
        paths.append(p)

    if not paths:
        print("ERROR: 유효한 경로가 없습니다.")
        sys.exit(1)
    return paths


# ═══════════════════════════════════════════════════════════════════
# 2. 채널 탐색
# ═══════════════════════════════════════════════════════════════════

def discover_channels(base_path: Path) -> list[dict]:
    """상위 경로를 재귀 탐색하여 모든 충방전 채널 폴더를 찾는다.

    Returns
    -------
    list[dict]
        각 dict: path, cycler('PNE'|'Toyo'), parent, name, save_end_data(PNE만)
    """
    channels = []
    base_str = str(base_path)

    for root, dirs, files in os.walk(base_str):
        root_path = Path(root)

        # ── Toyo 채널: CAPACITY.LOG 존재 ──
        cap_log = None
        for f in files:
            if f.upper() == 'CAPACITY.LOG':
                cap_log = f
                break
        if cap_log:
            channels.append({
                'path': root_path,
                'cycler': 'Toyo',
                'parent': root_path.parent,
                'name': root_path.name,
                'cap_log': cap_log,
            })
            # Toyo 채널 하위 (숫자 파일들)는 더 탐색 불필요
            dirs.clear()
            continue

        # ── PNE 채널: Restore/ 안에 SaveEndData 존재 ──
        if 'Restore' in dirs:
            restore_path = root_path / 'Restore'
            try:
                restore_files = os.listdir(str(restore_path))
            except OSError:
                continue
            end_files = [f for f in restore_files
                         if 'SaveEndData' in f and f.endswith('.csv')]
            if end_files:
                channels.append({
                    'path': root_path,
                    'cycler': 'PNE',
                    'parent': root_path.parent,
                    'name': root_path.name,
                    'save_end_data': end_files[0],
                    'restore_path': restore_path,
                })
                # PNE 채널 내부는 더 탐색 불필요
                dirs[:] = [d for d in dirs if d != 'Restore']

    return channels


# ═══════════════════════════════════════════════════════════════════
# 3. 용량 추정
# ═══════════════════════════════════════════════════════════════════

def extract_capacity_from_path(path: Path) -> int | None:
    """경로 문자열에서 mAh 값 추출 (폴더명 기반)."""
    # 현재 폴더 → 부모 → 조부모 순으로 탐색
    for p in [path, path.parent, path.parent.parent]:
        text = p.name
        m = re.search(r'(\d+)\s*mAh', text, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None


def estimate_capacity_toyo(channel_path: Path) -> int | None:
    """Toyo 첫 사이클 파일(000001)의 최대 전류로 용량 추정.

    최대 전류 ÷ 0.2(C-rate) = 추정 용량.
    """
    cycle1 = channel_path / '000001'
    if not cycle1.is_file():
        return None
    try:
        df = pd.read_csv(
            str(cycle1), sep=',', skiprows=3,
            encoding='cp949', on_bad_lines='skip',
        )
        if 'Current[mA]' in df.columns and len(df) > 0:
            max_current = df['Current[mA]'].max()
            return int(round(max_current / 0.2))
    except Exception:
        pass
    return None


def estimate_capacity_pne(restore_path: Path) -> int | None:
    """PNE SaveData0001의 첫 레코드 전류로 용량 추정.

    첫 행 Column 9 (Current µA) ÷ 1000 ÷ 0.2(C-rate) = 추정 용량.
    """
    try:
        files = os.listdir(str(restore_path))
    except OSError:
        return None

    for f in sorted(files):
        if 'SaveData0001' in f and f.endswith('.csv'):
            fp = restore_path / f
            if fp.stat().st_size == 0:
                continue
            try:
                df = pd.read_csv(
                    str(fp), header=None, encoding='cp949', on_bad_lines='skip',
                )
                if len(df) > 1:
                    current_ua = abs(df.iloc[1, 9])
                    return int(round(current_ua / 1000 / 0.2))
            except Exception:
                pass
    return None


def get_capacity(channel: dict) -> int:
    """채널의 추정 용량(mAh)을 반환. 여러 방법 순차 시도."""
    # 1) 경로명에서 추출
    cap = extract_capacity_from_path(channel['path'])
    if cap and cap > 0:
        return cap

    # 2) 장비별 데이터 기반 추정
    if channel['cycler'] == 'Toyo':
        cap = estimate_capacity_toyo(channel['path'])
    else:
        cap = estimate_capacity_pne(channel.get('restore_path', channel['path'] / 'Restore'))

    return cap if cap and cap > 0 else 0


# ═══════════════════════════════════════════════════════════════════
# 4. 데이터 로딩
# ═══════════════════════════════════════════════════════════════════

def load_toyo_summary(channel_path: Path, cap_log: str) -> pd.DataFrame | None:
    """Toyo CAPACITY.LOG 로딩 → 핵심 컬럼만 반환."""
    fp = channel_path / cap_log
    try:
        df = pd.read_csv(str(fp), sep=',', encoding='cp949', on_bad_lines='skip')
    except Exception:
        return None

    needed = ['Condition', 'Mode', 'TotlCycle', 'Cap[mAh]']
    if not all(c in df.columns for c in needed):
        return None

    return df[needed].copy()


def load_pne_summary(channel: dict) -> pd.DataFrame | None:
    """PNE SaveEndData.csv 로딩 → 핵심 컬럼만 반환."""
    fp = channel['restore_path'] / channel['save_end_data']
    try:
        df = pd.read_csv(str(fp), header=None, encoding='cp949', on_bad_lines='skip')
    except Exception:
        return None

    if df.shape[1] < 28:
        return None

    # 핵심 컬럼 선택 및 이름 부여
    cols_idx = [27, 2, 6, 9, 10, 11, 17]
    col_names = ['TotlCycle', 'StepType', 'EndState', 'Current', 'ChgCap', 'DchgCap', 'StepTime']
    result = df[cols_idx].copy()
    result.columns = col_names
    return result


# ═══════════════════════════════════════════════════════════════════
# 5. 사이클 분류
# ═══════════════════════════════════════════════════════════════════

def _classify_single_pne_cycle(group: pd.DataFrame) -> dict:
    """단일 PNE raw cycle의 기본 정보 및 카테고리 분류."""
    n_charge = int((group['StepType'] == 1).sum())
    n_discharge = int((group['StepType'] == 2).sum())
    n_rest = int((group['StepType'] == 3).sum())
    has_es78 = 78 in group['EndState'].values
    total_steps = len(group)

    # 주 동작: REST 제외 후 어떤 동작인지 판별
    active_steps = [int(s) for s in group['StepType'].values if int(s) in (1, 2)]
    if not active_steps:
        action = 'REST_ONLY'
    elif all(s == 1 for s in active_steps):
        action = 'CHG_ONLY'
    elif all(s == 2 for s in active_steps):
        action = 'DCHG_ONLY'
    else:
        action = 'MIXED'  # 충전+방전 모두 포함

    # 카테고리 판별
    # 순서가 중요: 단일 동작 펄스(_pulse)를 먼저 체크해야
    # DCHG+REST 사이클이 initial이 아닌 _pulse로 분류됨
    if n_charge == 0 and n_discharge == 0:
        cat = 'initial'  # REST만
    elif action in ('CHG_ONLY', 'DCHG_ONLY'):
        cat = '_pulse'  # 단일 동작 펄스 → GITT 병합 대상
    elif has_es78:
        cat = 'Rss'
    elif n_charge >= 2 and n_discharge >= 1:
        cat = '가속수명'
    elif n_charge == 1 and n_discharge >= 1:
        cat = 'RPT'
    else:
        cat = 'unknown'

    return {
        'n_charge': n_charge,
        'n_discharge': n_discharge,
        'n_rest': n_rest,
        'total_steps': total_steps,
        'has_es78': has_es78,
        'action': action,
        'category': cat,
    }


def _merge_pulse_groups(raw_results: list[dict]) -> list[dict]:
    """연속 동일 동작 펄스(_pulse)를 GITT 논리 사이클로 병합.

    규칙:
      1) 연속 _pulse 중 같은 action → 하나의 펄스 그룹
      2) 인접 반대 동작 펄스 그룹 쌍 → 하나의 GITT 논리 사이클
      3) _pulse가 아닌 일반 사이클은 그대로 유지
    """
    if not raw_results:
        return []

    # 1단계: 연속 _pulse 그룹화
    segments = []  # (type, items) — type: 'pulse' or 'normal'
    for r in raw_results:
        if r['category'] == '_pulse':
            if segments and segments[-1][0] == 'pulse' and segments[-1][2] == r['action']:
                segments[-1][1].append(r)
            else:
                segments.append(('pulse', [r], r['action']))
        else:
            segments.append(('normal', [r], None))

    # 2단계: 인접 펄스 그룹 쌍 → GITT 논리 사이클로 병합
    merged = []
    si = 0
    while si < len(segments):
        seg_type, items, action = segments[si]

        if seg_type == 'normal':
            # 일반 사이클은 그대로
            for r in items:
                merged.append(r)
            si += 1
            continue

        # 펄스 그룹: 다음 세그먼트가 반대 동작 펄스인지 확인 (최대 1쌍만)
        paired_items = list(items)
        has_multi_pulse = len(items) >= 2  # 연속 동일 동작 ≥2 → 반복 펄스
        if (si + 1 < len(segments)
                and segments[si + 1][0] == 'pulse'
                and segments[si + 1][2] != action):
            si += 1
            paired_items.extend(segments[si][1])
            if len(segments[si][1]) >= 2:
                has_multi_pulse = True

        # 반복 펄스 패턴이 없으면 GITT가 아닌 initial로 복원
        # (단독 1개 펄스 또는 단순 CHG+DCHG 1+1 쌍)
        total_raw = len(paired_items)
        if not has_multi_pulse:
            for r in paired_items:
                r['category'] = 'initial'
                merged.append(r)
            si += 1
            continue

        # 펄스 그룹의 raw cycle 범위
        raw_cycles = [r['cycle'] for r in paired_items]
        total_chg = sum(r['n_charge'] for r in paired_items)
        total_dchg = sum(r['n_discharge'] for r in paired_items)
        total_rest = sum(r['n_rest'] for r in paired_items)
        total_steps = sum(r['total_steps'] for r in paired_items)

        merged.append({
            'cycle': raw_cycles[0],  # 첫 raw cycle 번호
            'category': 'GITT',
            'n_charge': total_chg,
            'n_discharge': total_dchg,
            'n_rest': total_rest,
            'total_steps': total_steps,
            'raw_cycles': total_raw,
            'raw_range': f'{min(raw_cycles)}-{max(raw_cycles)}',
        })
        si += 1

    return merged


def classify_pne_cycles(df: pd.DataFrame, capacity: int) -> list[dict]:
    """PNE SaveEndData 기반 사이클별 카테고리 분류.

    사이클 정의: '충전→방전' 또는 '방전→충전' 쌍이 하나의 논리 사이클.
    같은 동작(CHG만/DCHG만)의 펄스 반복 → GITT 펄스 그룹으로 병합.

    분류 기준 (StepType==8 루프마커 제외 후):
      - 충전+방전 포함, n_charge >= 2  → 가속수명 (멀티스텝 충전)
      - 충전+방전 포함, EndState==78    → Rss (DCIR pulse)
      - 충전+방전 포함, n_charge == 1   → RPT (0.2C 충방전)
      - 단일 동작 펄스 반복             → GITT (펄스 그룹 병합)
      - 방전만                          → initial (초기 반사이클)
    """
    # StepType 8 (루프 마커) 제외
    real = df[df['StepType'] != 8].copy()

    # 1단계: raw cycle별 기본 분류
    raw_results = []
    for cyc, group in real.groupby('TotlCycle'):
        info = _classify_single_pne_cycle(group)
        info['cycle'] = int(cyc)
        raw_results.append(info)

    # 2단계: 펄스 그룹 병합 (GITT 감지)
    merged = _merge_pulse_groups(raw_results)

    # 결과 정리 (내부 필드 제거)
    results = []
    for r in merged:
        entry = {
            'cycle': r['cycle'],
            'category': r['category'],
            'n_charge': r['n_charge'],
            'n_discharge': r['n_discharge'],
            'n_rest': r['n_rest'],
            'total_steps': r['total_steps'],
        }
        if 'raw_cycles' in r:
            entry['raw_cycles'] = r['raw_cycles']
            entry['raw_range'] = r['raw_range']
        results.append(entry)

    return results


def classify_toyo_cycles(df: pd.DataFrame, capacity: int) -> list[dict]:
    """Toyo CAPACITY.LOG 기반 사이클별 카테고리 분류.

    로직:
      1) 연속 동일 Condition 행을 병합 → 충전 그룹 / 방전 그룹
      2) 충전+방전 쌍 → 논리 사이클
      3) 분류 기준:
         - 충전 0행 (방전만)       → initial
         - 충전 1행 + 방전 Cap > 0.85 × capacity → RPT
         - 충전 2행 이상           → 가속수명
         - 그 외                   → unknown
    """
    results = []
    if df is None or df.empty:
        return results

    conds = df['Condition'].values
    caps = df['Cap[mAh]'].values

    # 연속 동일 Condition 병합
    groups = []
    i = 0
    while i < len(df):
        start = i
        cond = int(conds[i])
        while i < len(df) and int(conds[i]) == cond:
            i += 1
        total_cap = float(caps[start:i].sum())
        n_rows = i - start
        groups.append((cond, n_rows, total_cap))

    # 충전+방전 쌍 → 논리 사이클
    # 분류 기준: 충전 행 수만으로 판별 (용량 threshold 폐지)
    #   - chg_rows == 0 → initial (초기 방전)
    #   - chg_rows == 1 → RPT (단일 충전 = 0.2C 참조 사이클)
    #   - chg_rows >= 2 → 가속수명 (멀티스텝 CC-CV)
    # ※ 기존 capacity×0.85 threshold는 장수명 진행 시 용량 열화로
    #    RPT가 unknown으로 오분류되는 문제가 있어 제거
    gi = 0
    cycle_num = 0
    while gi < len(groups):
        cond, n, cap = groups[gi]

        if cond == 1:  # 충전 그룹
            chg_rows, chg_cap = n, cap
            if gi + 1 < len(groups) and groups[gi + 1][0] == 2:
                dchg_rows, dchg_cap = groups[gi + 1][1], groups[gi + 1][2]
                gi += 2
            else:
                dchg_rows, dchg_cap = 0, 0.0
                gi += 1
        elif cond == 2:  # 방전만 (초기 사이클)
            chg_rows, chg_cap = 0, 0.0
            dchg_rows, dchg_cap = n, cap
            gi += 1
        else:
            # Condition 3 (Rest) 등은 건너뛰기
            gi += 1
            continue

        cycle_num += 1

        if chg_rows == 0:
            cat = 'initial'
        elif chg_rows == 1:
            cat = 'RPT'
        elif chg_rows >= 2:
            cat = '가속수명'
        else:
            cat = 'unknown'

        results.append({
            'cycle': cycle_num,
            'category': cat,
            'chg_rows': chg_rows,
            'dchg_rows': dchg_rows,
            'chg_cap': round(chg_cap, 1),
            'dchg_cap': round(dchg_cap, 1),
        })

    return results


# ═══════════════════════════════════════════════════════════════════
# 6. 스케줄 패턴 분석
# ═══════════════════════════════════════════════════════════════════

def detect_schedule_pattern(classified: list[dict]) -> tuple[list[tuple], str]:
    """카테고리 시퀀스의 RLE(Run-Length Encoding) → 패턴 문자열 생성."""
    if not classified:
        return [], ''

    categories = [c['category'] for c in classified]
    rle = []
    current = categories[0]
    count = 1
    for cat in categories[1:]:
        if cat == current:
            count += 1
        else:
            rle.append((current, count))
            current = cat
            count = 1
    rle.append((current, count))

    parts = []
    for cat, n in rle:
        parts.append(f'{cat}×{n}' if n > 1 else cat)
    pattern_str = ' → '.join(parts)

    return rle, pattern_str


def detect_rpt_interval(classified: list[dict]) -> int | None:
    """RPT 사이클 간 평균 간격(사이클 수) 계산."""
    rpt_indices = [i for i, c in enumerate(classified) if c['category'] == 'RPT']
    if len(rpt_indices) < 2:
        return None
    intervals = [rpt_indices[j + 1] - rpt_indices[j] for j in range(len(rpt_indices) - 1)]
    return int(round(np.mean(intervals)))


def detect_test_type(counts: dict) -> str:
    """카테고리 분포로 시험 종류 추정."""
    total = sum(counts.values())
    if total == 0:
        return '데이터 없음'

    accel = counts.get('가속수명', 0)
    rss = counts.get('Rss', 0)
    rpt = counts.get('RPT', 0)
    gitt = counts.get('GITT', 0)

    if gitt > total * 0.3:
        return 'GITT 시험'
    if accel > total * 0.5:
        return '가속수명 시험'
    if rss > total * 0.3:
        return 'Rss/DCIR 시험'
    if rpt > total * 0.5:
        return 'RPT 전용'
    if accel > 0 and rss > 0:
        return '가속수명 + Rss 복합'
    return '기타'


# ═══════════════════════════════════════════════════════════════════
# 7. 채널 분석 메인 로직
# ═══════════════════════════════════════════════════════════════════

def analyze_channel(channel: dict) -> dict:
    """단일 채널 분석 → 결과 dict 반환."""
    result = {
        'path': str(channel['path']),
        'parent': str(channel['parent']),
        'name': channel['name'],
        'cycler': channel['cycler'],
        'capacity_mah': 0,
        'total_cycles': 0,
        'counts': {},
        'classified': [],
        'schedule_pattern': '',
        'rpt_interval': None,
        'test_type': '데이터 없음',
        'error': None,
    }

    # 용량 추정
    capacity = get_capacity(channel)
    result['capacity_mah'] = capacity

    # 데이터 로딩
    if channel['cycler'] == 'Toyo':
        df = load_toyo_summary(channel['path'], channel.get('cap_log', 'CAPACITY.LOG'))
        if df is None or df.empty:
            result['error'] = 'CAPACITY.LOG 로딩 실패'
            return result
        classified = classify_toyo_cycles(df, capacity)
    else:
        df = load_pne_summary(channel)
        if df is None or df.empty:
            result['error'] = 'SaveEndData 로딩 실패'
            return result
        classified = classify_pne_cycles(df, capacity)

    result['classified'] = classified
    result['total_cycles'] = len(classified)

    # 카테고리 카운트
    counts = Counter(c['category'] for c in classified)
    result['counts'] = dict(counts)

    # 스케줄 패턴
    _rle, pattern_str = detect_schedule_pattern(classified)
    result['schedule_pattern'] = pattern_str
    result['rpt_interval'] = detect_rpt_interval(classified)
    result['test_type'] = detect_test_type(counts)

    return result


# ═══════════════════════════════════════════════════════════════════
# 8. 리포트 생성
# ═══════════════════════════════════════════════════════════════════

def generate_report(all_results: list[dict], scan_paths: list[Path]) -> str:
    """전체 분석 결과 → 텍스트 리포트 생성."""
    lines = []
    def pr(s: str = '') -> None:
        lines.append(s)

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    sep = '=' * 120

    pr(sep)
    pr(f"  사이클 카테고리 분석 리포트  |  분석일: {now}")
    pr(sep)
    pr()
    pr("■ 스캔 대상 경로")
    for p in scan_paths:
        pr(f"  {p}")
    pr()

    # ── 전체 요약 ──
    total_channels = len(all_results)
    ok_results = [r for r in all_results if r['error'] is None]
    err_results = [r for r in all_results if r['error'] is not None]
    total_cycles = sum(r['total_cycles'] for r in ok_results)

    # 장비별 카운트
    toyo_count = sum(1 for r in all_results if r['cycler'] == 'Toyo')
    pne_count = sum(1 for r in all_results if r['cycler'] == 'PNE')

    # 전체 카테고리 합산
    global_counts = Counter()
    for r in ok_results:
        global_counts.update(r['counts'])

    pr("■ 전체 요약")
    pr(f"  총 채널 수: {total_channels}개 (Toyo: {toyo_count} / PNE: {pne_count})")
    pr(f"  분석 성공: {len(ok_results)}개 / 실패: {len(err_results)}개")
    pr(f"  총 논리 사이클: {total_cycles}개")
    pr()
    pr("  카테고리별 합계:")
    for cat in ['RPT', 'Rss', '가속수명', 'GITT', 'initial', 'unknown']:
        cnt = global_counts.get(cat, 0)
        pct = cnt / total_cycles * 100 if total_cycles > 0 else 0
        label = CATEGORY_LABELS.get(cat, cat)
        pr(f"    {label:30s} : {cnt:6d}  ({pct:5.1f}%)")
    pr()

    # ── 시험 종류별 분류 ──
    pr(sep)
    pr("■ 시험 종류별 분류")
    test_type_map = defaultdict(list)
    for r in ok_results:
        test_type_map[r['test_type']].append(r)
    for ttype in sorted(test_type_map):
        ch_list = test_type_map[ttype]
        pr(f"  {ttype}: {len(ch_list)}개 채널")
    pr()

    # ── 데이터셋별 상세 ──
    pr(sep)
    pr("■ 데이터셋별 상세")
    pr(sep)

    # 부모 폴더 기준 그룹핑
    parent_map = defaultdict(list)
    for r in all_results:
        parent_map[r['parent']].append(r)

    dataset_num = 0
    for parent in sorted(parent_map):
        channels_in_dataset = parent_map[parent]
        dataset_num += 1
        parent_name = Path(parent).name

        pr()
        pr(f"  ┌─ 데이터셋 #{dataset_num}: {parent_name}")
        pr(f"  │  경로: {parent}")
        pr(f"  │  채널 수: {len(channels_in_dataset)}개")
        pr(f"  │")

        for ch_result in channels_in_dataset:
            cycler = ch_result['cycler']
            name = ch_result['name']
            cap = ch_result['capacity_mah']
            cap_str = f"{cap} mAh" if cap > 0 else "추정불가"

            if ch_result['error']:
                pr(f"  │  ├─ [{cycler}] {name}  (용량: {cap_str})")
                pr(f"  │  │  ERROR: {ch_result['error']}")
                continue

            total = ch_result['total_cycles']
            counts = ch_result['counts']
            test_type = ch_result['test_type']
            rpt_int = ch_result['rpt_interval']

            pr(f"  │  ├─ [{cycler}] {name}  (용량: {cap_str})")
            pr(f"  │  │  시험 종류: {test_type}")
            pr(f"  │  │  총 사이클: {total}개")

            # 카테고리 분포
            cat_parts = []
            for cat in ['RPT', 'Rss', '가속수명', 'GITT', 'initial', 'unknown']:
                cnt = counts.get(cat, 0)
                if cnt > 0:
                    cat_parts.append(f"{cat}={cnt}")
            pr(f"  │  │  분류: {', '.join(cat_parts)}")

            if rpt_int is not None:
                pr(f"  │  │  RPT 주기: 약 {rpt_int}사이클 간격")

            # GITT 논리 사이클의 raw cycle 범위 표시
            gitt_entries = [c for c in ch_result['classified'] if c['category'] == 'GITT']
            if gitt_entries:
                raw_total = sum(c.get('raw_cycles', 1) for c in gitt_entries)
                ranges = [c.get('raw_range', '?') for c in gitt_entries]
                pr(f"  │  │  GITT: {len(gitt_entries)}개 논리사이클 (raw {raw_total}개 병합)")
                for ge in gitt_entries:
                    rr = ge.get('raw_range', '?')
                    rc = ge.get('raw_cycles', 1)
                    pr(f"  │  │    └ raw cycle {rr} ({rc}개 → 1 논리사이클)")

            # 스케줄 패턴 (길면 축약)
            pattern = ch_result['schedule_pattern']
            if len(pattern) > 90:
                pattern = pattern[:87] + '...'
            pr(f"  │  │  스케줄: {pattern}")

        pr(f"  └{'─' * 70}")

    # ── 에러 목록 ──
    if err_results:
        pr()
        pr(sep)
        pr("■ 분석 실패 목록")
        for r in err_results:
            pr(f"  [{r['cycler']}] {r['path']}")
            pr(f"    → {r['error']}")

    pr()
    pr(sep)
    pr("분석 완료.")
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════
# 9. 내보내기
# ═══════════════════════════════════════════════════════════════════

def export_csv(all_results: list[dict], output_path: Path) -> None:
    """채널별 요약을 CSV로 내보내기."""
    rows = []
    for r in all_results:
        rows.append({
            '데이터셋': Path(r['parent']).name,
            '채널': r['name'],
            '충방전기': r['cycler'],
            '용량(mAh)': r['capacity_mah'] if r['capacity_mah'] > 0 else '',
            '총사이클': r['total_cycles'],
            'RPT': r['counts'].get('RPT', 0),
            'Rss': r['counts'].get('Rss', 0),
            '가속수명': r['counts'].get('가속수명', 0),
            'GITT': r['counts'].get('GITT', 0),
            'initial': r['counts'].get('initial', 0),
            'unknown': r['counts'].get('unknown', 0),
            '시험종류': r['test_type'],
            'RPT주기': r['rpt_interval'] if r['rpt_interval'] else '',
            '스케줄패턴': r['schedule_pattern'],
            '에러': r['error'] if r['error'] else '',
            '경로': str(r['path']),
        })

    df = pd.DataFrame(rows)
    df.to_csv(str(output_path), index=False, encoding='utf-8-sig')


def export_json(all_results: list[dict], output_path: Path) -> None:
    """전체 결과를 JSON으로 내보내기."""
    # classified 리스트는 용량이 클 수 있으므로 요약만 포함
    export_data = {
        'analysis_date': datetime.now().isoformat(),
        'total_channels': len(all_results),
        'channels': [],
    }
    for r in all_results:
        ch = {
            'path': str(r['path']),
            'dataset': Path(r['parent']).name,
            'channel': r['name'],
            'cycler': r['cycler'],
            'capacity_mah': r['capacity_mah'],
            'total_cycles': r['total_cycles'],
            'counts': r['counts'],
            'test_type': r['test_type'],
            'rpt_interval': r['rpt_interval'],
            'schedule_pattern': r['schedule_pattern'],
            'error': r['error'],
            'cycles': r['classified'],
        }
        export_data['channels'].append(ch)

    with open(str(output_path), 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════
# 10. 메인
# ═══════════════════════════════════════════════════════════════════

def main() -> None:
    print("=" * 60)
    print("  사이클 카테고리 분석기")
    print("=" * 60)
    print()

    scan_paths = parse_args()
    for p in scan_paths:
        print(f"  대상 경로: {p}")
    print()

    # ── 채널 탐색 ──
    t_start = time.time()
    all_channels = []
    for base in scan_paths:
        print(f"[탐색] {base} ...", flush=True)
        channels = discover_channels(base)
        print(f"  → {len(channels)}개 채널 발견 "
              f"(Toyo: {sum(1 for c in channels if c['cycler']=='Toyo')}, "
              f"PNE: {sum(1 for c in channels if c['cycler']=='PNE')})", flush=True)
        all_channels.extend(channels)

    if not all_channels:
        print("\nERROR: 분석 가능한 충방전 데이터가 없습니다.")
        sys.exit(1)

    print(f"\n총 {len(all_channels)}개 채널 분석 시작...\n", flush=True)

    # ── 채널별 분석 ──
    all_results = []
    for idx, ch in enumerate(all_channels, 1):
        cycler = ch['cycler']
        name = ch['name']
        parent_name = ch['parent'].name
        print(f"  [{idx}/{len(all_channels)}] [{cycler}] {parent_name}/{name} ...",
              end='', flush=True)

        result = analyze_channel(ch)
        all_results.append(result)

        if result['error']:
            print(f" ERROR: {result['error']}")
        else:
            total = result['total_cycles']
            ttype = result['test_type']
            print(f" {total}사이클 ({ttype})")

    elapsed = time.time() - t_start
    print(f"\n분석 완료: {len(all_results)}개 채널, {elapsed:.1f}초 소요\n", flush=True)

    # ── 리포트 생성 ──
    report_text = generate_report(all_results, scan_paths)
    print(report_text)

    # ── 파일 저장 ──
    out_dir = Path.cwd()
    txt_path = out_dir / '_사이클카테고리_분석.txt'
    with open(str(txt_path), 'w', encoding='utf-8') as f:
        f.write(report_text)
    print(f"\n텍스트 리포트 저장: {txt_path}")

    csv_path = out_dir / '_사이클카테고리_분석.csv'
    export_csv(all_results, csv_path)
    print(f"CSV 저장: {csv_path}")

    json_path = out_dir / '_사이클카테고리_분석.json'
    export_json(all_results, json_path)
    print(f"JSON 저장: {json_path}")


if __name__ == '__main__':
    main()
