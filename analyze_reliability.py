"""
===============================================================================
신뢰성 데이터 종합 현황 분석기 (Reliability Data Status Analyzer)
===============================================================================
  Rawdata/ 하위의 모든 yymmdd 폴더를 스캔하여:
    1) 파일명에서 메타데이터 파싱 (모델, 제조사, 개발단계, 온도, 사이클 등)
    2) 폴더별 이력 추적 → 최신 기준 종합 리스트 생성
    3) 텍스트 리포트 + CSV + JSON 출력

  사용법:
    python analyze_reliability.py [Rawdata경로]           # 메타데이터만 분석
    python analyze_reliability.py [Rawdata경로] --excel    # Excel COM으로 데이터까지 검증
    python analyze_reliability.py [Rawdata경로] --auto     # Excel 유무 자동감지
  기본값:  스크립트와 같은 위치, --auto 모드
===============================================================================
"""
import os
import re
import csv
import json
import sys
import time
import traceback
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ── Excel COM 사용 가능 여부 감지 ──
EXCEL_AVAILABLE = False
try:
    import xlwings as xw
    import pandas as pd
    # 실제 Excel 프로세스 생성 테스트
    _app = xw.App(visible=False, add_book=False)
    _app.quit()
    EXCEL_AVAILABLE = True
except Exception:
    pass

# ── CLI 파싱 ──
def _parse_args():
    args = sys.argv[1:]
    rawdata = None
    mode = 'auto'  # auto / meta / excel
    for a in args:
        if a == '--excel':
            mode = 'excel'
        elif a == '--meta':
            mode = 'meta'
        elif a == '--auto':
            mode = 'auto'
        elif not a.startswith('-'):
            rawdata = a
    if rawdata is None:
        rawdata = str(Path(__file__).parent)
    resolved = Path(rawdata).resolve()
    if not resolved.is_dir():
        print(f"ERROR: 경로가 존재하지 않습니다: {resolved}")
        sys.exit(1)
    return resolved, mode

RAWDATA_DIR, RUN_MODE = _parse_args()

# auto 모드: Excel 유무에 따라 결정
if RUN_MODE == 'auto':
    USE_EXCEL = EXCEL_AVAILABLE
elif RUN_MODE == 'excel':
    USE_EXCEL = True
else:
    USE_EXCEL = False

if USE_EXCEL and not EXCEL_AVAILABLE:
    print("ERROR: --excel 모드이나 Excel COM을 사용할 수 없습니다.")
    print("  xlwings/pandas 설치 및 Microsoft Excel 설치를 확인하세요.")
    sys.exit(1)

# yymmdd 폴더 패턴 (뒤에 test 등 텍스트 붙은 것도 허용)
FOLDER_RE = re.compile(r'^(\d{6})(\D.*)?$')

VENDOR_KEYWORDS = [
    'ATL', 'SDI', 'LGES', 'COSMX', 'LWN', 'LWM', 'LWI', 'BYD',
    'EVE', 'LIWINON', 'ICF', 'TSDI', 'EVERPOWER',
]

# 제조사명 정규화 매핑 (대소문자/약어 통합)
VENDOR_NORMALIZE = {
    'COSMX': 'Cosmx',
    'LIWINON': 'Liwinon',
    'EVERPOWER': 'Everpower',
    'TSDI': 'TSDI',
    'LWI': 'Liwinon',
}

DEV_STAGE_KEYWORDS = [
    'MP3', 'MP2', 'MP1', 'POC', 'PP', 'EVT', 'DVT', 'PVT',
]

CATEGORY_RULES = [
    (r'Buds?\d*',             'Buds'),
    (r'\bTab\b',              'Tab'),
    (r'Watch\d*|W\d+u',      'Watch'),
    (r'Ring|SmartRing',       'Ring'),
    (r'Jinju|Robot',          'Robot'),
    (r'\bJDM\b|\[JDM\]',     'Phone(JDM)'),
    (r'GB\d|Laptop',          'Laptop'),
    (r'\bGalaxy\b',           'Phone'),
]
DEFAULT_CATEGORY = 'Phone'


# ═══════════════════════════════════════════════════════════════════
# 2. 유틸리티 함수
# ═══════════════════════════════════════════════════════════════════
def discover_date_folders(rawdata_dir):
    """yymmdd 형식 폴더들을 날짜순으로 반환."""
    folders = []
    for entry in os.listdir(rawdata_dir):
        full = rawdata_dir / entry
        if not full.is_dir():
            continue
        m = FOLDER_RE.match(entry)
        if m:
            datestr = m.group(1)
            suffix = m.group(2) or ''
            try:
                yr = int(datestr[:2])
                mo = int(datestr[2:4])
                dy = int(datestr[4:6])
                if 18 <= yr <= 30 and 1 <= mo <= 12 and 1 <= dy <= 31:
                    folders.append((datestr, suffix, entry, full))
            except ValueError:
                pass
    folders.sort(key=lambda x: x[0])
    return folders


def list_xls_files(folder_path):
    """폴더 내 .xls 파일 목록 반환."""
    try:
        return sorted([
            f for f in os.listdir(folder_path)
            if f.lower().endswith('.xls') and not f.startswith('~$')
        ])
    except PermissionError:
        return []


def extract_vendor(text):
    """파일명에서 제조사(vendor) 추출. 정규화된 이름 반환."""
    text_upper = text.upper()
    for v in VENDOR_KEYWORDS:
        pattern = r'(?<![A-Z])' + v + r'(?![A-Z])'
        if re.search(pattern, text_upper):
            return VENDOR_NORMALIZE.get(v, v)
    return '-'


def extract_dev_stage(text):
    """파일명에서 개발단계 추출."""
    text_upper = text.upper()
    for stage in DEV_STAGE_KEYWORDS:
        if re.search(r'\b' + stage + r'\b', text_upper):
            return stage
    return '-'


def extract_generation(text):
    """세대 정보 추출 (1st, 2nd, 3rd, 7th 등)."""
    m = re.search(r'\b(\d+)\s*(?:st|nd|rd|th)\b', text, re.IGNORECASE)
    if m:
        return m.group(0).strip()
    return ''


def extract_voltage(text):
    """전압 추출 (4.50V, 455V→4.55V 등)."""
    # [455V ...] 또는 [45V ...]  패턴
    m = re.search(r'(\d{3,4})V', text)
    if m:
        val = int(m.group(1))
        if val >= 100:
            return round(val / 100, 2)
        return round(val / 10, 2)
    # 4.5V, 4.55V 패턴
    m = re.search(r'(\d+\.\d+)\s*V', text)
    if m:
        return float(m.group(1))
    return None


def extract_capacity_mah(text):
    """mAh 추출 (BDT name_capacity 호환)."""
    raw = re.sub(r'[._@\[\]\(\)]', ' ', text)
    # VmAh 오타 처리
    m = re.search(r'(\d+)V?mAh', raw, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def extract_temperature(text):
    """온도 조건 추출."""
    temps = set()
    # [15], [23], [45] 패턴
    for m in re.finditer(r'\[(\d{2})\]', text):
        t = int(m.group(1))
        if t in (15, 23, 45, 60):
            temps.add(t)
    # Life15, Lifecycle23 패턴
    for m in re.finditer(r'Life(?:cycle)?(\d{2})', text, re.IGNORECASE):
        t = int(m.group(1))
        if t in (15, 23, 45, 60):
            temps.add(t)
    # [T23] 패턴
    for m in re.finditer(r'\bT(\d{2})\b', text):
        t = int(m.group(1))
        if t in (15, 23, 45, 60):
            temps.add(t)
    return sorted(temps)


def extract_cell_count(text):
    """셀 수(EA) 추출."""
    m = re.search(r'(\d+)\s*[Ee][Aa]\b', text)
    if m:
        return int(m.group(1))
    return None


def extract_blk(text):
    """BLK(블록) 번호 추출."""
    blks = set()
    for m in re.finditer(r'[Bb][Ll][Kk]\s*(\d+)', text):
        blks.add(f"BLK{m.group(1)}")
    return sorted(blks)


def extract_cycle_hints(text):
    """사이클 관련 힌트 추출 (600CY, 1200, 300CY~, restart 등)."""
    hints = []
    for m in re.finditer(r'(\d+)\s*[Cc][Yy]', text):
        hints.append(f"{m.group(1)}CY")
    if re.search(r'\b1200\b', text):
        hints.append('1200CY')
    if re.search(r'\brestart', text, re.IGNORECASE):
        hints.append('restart')
    if re.search(r'\bretry', text, re.IGNORECASE):
        hints.append('retry')
    if re.search(r'\bre\b', text, re.IGNORECASE):
        hints.append('re-test')
    if re.search(r'[Aa]fter\d+', text):
        m2 = re.search(r'[Aa]fter(\d+)', text)
        hints.append(f"After{m2.group(1)}")
    if re.search(r'(\d+)start', text):
        m2 = re.search(r'(\d+)start', text)
        hints.append(f"{m2.group(1)}start")
    return list(dict.fromkeys(hints))  # 중복 제거, 순서 유지


def extract_date_from_filename(text):
    """파일명에서 날짜(yymmdd) 추출."""
    dates = []
    for m in re.finditer(r'\b(\d{6})\b', text):
        d = m.group(1)
        yr, mo, dy = int(d[:2]), int(d[2:4]), int(d[4:6])
        if 18 <= yr <= 30 and 1 <= mo <= 12 and 1 <= dy <= 31:
            dates.append(d)
    return dates[-1] if dates else None  # 마지막 것이 보통 데이터 날짜


def extract_tags(text):
    """기타 태그 추출 (R tape, Graphite, Boosting, ICF 등)."""
    tags = []
    tag_patterns = [
        (r'R[\-\s]?[Tt]ape', 'R-tape'),
        (r'\bGr(?:aphite)?\b', 'Graphite'),
        (r'\b[Bb]oost(?:ing)?\b', 'Boosting'),
        (r'\bICF\b', 'ICF'),
        (r'\bRC\b', 'RC'),
        (r'\bSUS\b', 'SUS'),
        (r'\bSUS[\s_]CAN\b', 'SUS_CAN'),
        (r'[Bb]ottom[\s_][Tt]ape', 'Bottom_Tape'),
        (r'\bSide[\s_]Tape\b', 'Side_Tape'),
        (r'CELL[\s_]CHANGE', 'CELL_CHANGE'),
        (r'PR[\s_]SET', 'PR_SET'),
        (r'Low[\s_]Voltage', 'LowVoltage'),
        (r'CHARGE\d+', lambda m: m.group(0)),
        (r'[Mm]ixing', 'MixingFactory'),
        (r'\bsepa\b', 'sepa'),
    ]
    for pat, tag in tag_patterns:
        m = re.search(pat, text)
        if m:
            t = tag(m) if callable(tag) else tag
            if t not in tags:
                tags.append(t)
    return tags


def classify_category(text):
    """파일명에서 제품 카테고리 분류."""
    for pattern, cat in CATEGORY_RULES:
        if re.search(pattern, text, re.IGNORECASE):
            return cat
    return DEFAULT_CATEGORY


def extract_model_name(text):
    """파일명에서 모델명 추출 (제조사/개발단계/온도 등 제거 후 핵심 모델명)."""
    # 대괄호 안 내용 제거
    clean = re.sub(r'\[.*?\]', ' ', text)
    # 소괄호 안 내용 제거
    clean = re.sub(r'\(.*?\)', ' ', clean)
    # 날짜 제거
    clean = re.sub(r'\b\d{6}\b', ' ', clean)
    # '#숫자_숫자ea' 등 제거
    clean = re.sub(r'#\d+[\-_]?\d*[Ee][Aa]?', ' ', clean)
    # '숫자ea' 제거
    clean = re.sub(r'\b\d+\s*[Ee][Aa]\b', ' ', clean)
    # BLK 제거
    clean = re.sub(r'[Bb][Ll][Kk]\s*\d+', ' ', clean)
    # Lifecycle/Life 제거
    clean = re.sub(r'Life(?:cycle)?\d*', ' ', clean, flags=re.IGNORECASE)
    # 제조사명 제거
    for v in VENDOR_KEYWORDS:
        clean = re.sub(r'(?<![A-Za-z])' + v + r'(?![A-Za-z])', ' ', clean, flags=re.IGNORECASE)
    # 개발단계 제거
    for s in DEV_STAGE_KEYWORDS:
        clean = re.sub(r'\b' + s + r'\b', ' ', clean, flags=re.IGNORECASE)
    # 세대 제거
    clean = re.sub(r'\b\d+\s*(?:st|nd|rd|th)\b', ' ', clean, flags=re.IGNORECASE)
    # 특수문자 정리
    clean = re.sub(r'[\-_~.#+]', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    # xls 확장자 제거
    clean = re.sub(r'\.xls$', '', clean, flags=re.IGNORECASE)
    # 'xls' 잔류 제거
    clean = re.sub(r'\bxls\b', '', clean, flags=re.IGNORECASE)
    # mAh 정보 제거 (그룹키에서 capacity로 별도 관리)
    clean = re.sub(r'\d+V?mAh', '', clean, flags=re.IGNORECASE)
    # 전압 패턴 제거 (455V, 447V, 4.55V 등)
    clean = re.sub(r'\b\d{3,4}V\b', '', clean)
    clean = re.sub(r'\b\d+\.\d+V\b', '', clean)
    # EA 패턴 제거
    clean = re.sub(r'\b\d+\s*[Ee][Aa]\b', '', clean)
    # 사이클 힌트 제거
    clean = re.sub(r'\b\d+CY\b', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\b1200\b', '', clean)
    # 'After숫자', '숫자start' 제거
    clean = re.sub(r'[Aa]fter\d+', '', clean)
    clean = re.sub(r'\d+start', '', clean)
    # restart/retry/re 제거
    clean = re.sub(r'\b(?:restart|retry)\b', '', clean, flags=re.IGNORECASE)
    # 날짜 제거 (6자리 순수숫자)
    clean = re.sub(r'\b\d{6}\b', '', clean)
    # 정리
    clean = re.sub(r'\s+', ' ', clean).strip()

    # 앞쪽 의미 있는 토큰 추출
    tokens = clean.split()
    model_tokens = []
    for tok in tokens:
        if tok.lower() in ('blk', 're', 'ea', 'restart', 'retry', 'after',
                           'start', 'test', 'change', 'tape', 'cy', 'ch'):
            break
        if re.match(r'^\d{3,}$', tok):  # 순수 숫자 3자리 이상 → 스킵
            continue
        model_tokens.append(tok)
        if len(model_tokens) >= 5:
            break

    return ' '.join(model_tokens) if model_tokens else text.split()[0]


# ═══════════════════════════════════════════════════════════════════
# 3. 파일 파싱 → FileRecord
# ═══════════════════════════════════════════════════════════════════
class FileRecord:
    """하나의 .xls 파일에서 추출한 모든 메타데이터 + Excel 검증 결과."""
    __slots__ = (
        'filename', 'folder_date', 'folder_name', 'file_size',
        'category', 'model', 'vendor', 'dev_stage', 'generation',
        'voltage', 'capacity_mah', 'temperatures', 'cell_count',
        'blks', 'cycle_hints', 'date_in_file', 'tags',
        'mah_auto_ok',
        # Excel 검증 결과 (USE_EXCEL=True 일 때만 채워짐)
        'excel_status',     # 'OK' / 'WARN' / 'ERROR' / None
        'excel_issues',     # List[str]
        'excel_warnings',   # List[str]
        'excel_data_rows',  # int or None
        'excel_data_cols',  # int or None
        'excel_sheets',     # List[str] or None
        'excel_merge_needed',  # bool or None
    )

    def __init__(self, filename, folder_date, folder_name, folder_path):
        self.filename = filename
        self.folder_date = folder_date
        self.folder_name = folder_name
        fpath = folder_path / filename
        self.file_size = os.path.getsize(fpath) if fpath.is_file() else 0
        self.category = classify_category(filename)
        self.model = extract_model_name(filename)
        self.vendor = extract_vendor(filename)
        self.dev_stage = extract_dev_stage(filename)
        self.generation = extract_generation(filename)
        self.voltage = extract_voltage(filename)
        self.capacity_mah = extract_capacity_mah(filename)
        self.temperatures = extract_temperature(filename)
        self.cell_count = extract_cell_count(filename)
        self.blks = extract_blk(filename)
        self.cycle_hints = extract_cycle_hints(filename)
        self.date_in_file = extract_date_from_filename(filename)
        self.tags = extract_tags(filename)
        self.mah_auto_ok = self.capacity_mah is not None
        # Excel 검증 필드 초기화 (나중에 validate_with_excel로 채움)
        self.excel_status = None
        self.excel_issues = []
        self.excel_warnings = []
        self.excel_data_rows = None
        self.excel_data_cols = None
        self.excel_sheets = None
        self.excel_merge_needed = None

    @property
    def group_key(self):
        """동일 시험 항목으로 그룹핑하기 위한 키.
        모델 + 제조사 + 개발단계 + 용량 기준으로 그룹핑."""
        cap_key = self.capacity_mah or 0
        return (self.category, self.model, self.vendor, self.dev_stage, cap_key)

    def to_dict(self):
        return {
            'filename': self.filename,
            'folder_date': self.folder_date,
            'folder_name': self.folder_name,
            'file_size': self.file_size,
            'category': self.category,
            'model': self.model,
            'vendor': self.vendor,
            'dev_stage': self.dev_stage,
            'generation': self.generation,
            'voltage': self.voltage,
            'capacity_mah': self.capacity_mah,
            'temperatures': self.temperatures,
            'cell_count': self.cell_count,
            'blks': self.blks,
            'cycle_hints': self.cycle_hints,
            'date_in_file': self.date_in_file,
            'tags': self.tags,
            'mah_auto_ok': self.mah_auto_ok,
            'excel_status': self.excel_status,
            'excel_issues': self.excel_issues,
            'excel_warnings': self.excel_warnings,
            'excel_data_rows': self.excel_data_rows,
            'excel_data_cols': self.excel_data_cols,
            'excel_sheets': self.excel_sheets,
            'excel_merge_needed': self.excel_merge_needed,
        }


# ═══════════════════════════════════════════════════════════════════
# 4. TestGroup: 같은 시험 항목의 이력 집합
# ═══════════════════════════════════════════════════════════════════
class TestGroup:
    """동일 그룹 키로 묶인 시험 항목 집합."""
    def __init__(self, key):
        self.key = key  # (category, model, vendor, dev_stage, cap)
        self.records = []  # List[FileRecord], folder_date 순

    def add(self, rec):
        self.records.append(rec)

    @property
    def category(self):
        return self.key[0]

    @property
    def model(self):
        return self.key[1]

    @property
    def vendor(self):
        return self.key[2]

    @property
    def dev_stage(self):
        return self.key[3]

    @property
    def capacity(self):
        return self.key[4] or None

    @property
    def all_temperatures(self):
        temps = set()
        for r in self.records:
            temps.update(r.temperatures)
        return sorted(temps)

    @property
    def temp_completeness(self):
        """15/23/45°C 3조건 중 몇 개 확보했는지."""
        covered = set()
        for t in self.all_temperatures:
            if t in (15, 23, 45):
                covered.add(t)
        return f"{len(covered)}/3"

    @property
    def all_blks(self):
        blks = set()
        for r in self.records:
            blks.update(r.blks)
        return sorted(blks)

    @property
    def total_ea(self):
        eas = [r.cell_count for r in self.records if r.cell_count]
        return sum(eas) if eas else None

    @property
    def all_cycle_hints(self):
        hints = []
        for r in self.records:
            for h in r.cycle_hints:
                if h not in hints:
                    hints.append(h)
        return hints

    @property
    def all_tags(self):
        tags = []
        for r in self.records:
            for t in r.tags:
                if t not in tags:
                    tags.append(t)
        return tags

    @property
    def folder_dates(self):
        return sorted(set(r.folder_date for r in self.records))

    @property
    def first_seen(self):
        return self.folder_dates[0]

    @property
    def last_seen(self):
        return self.folder_dates[-1]

    @property
    def folder_count(self):
        return len(self.folder_dates)

    @property
    def file_count(self):
        return len(self.records)

    @property
    def latest_records(self):
        """최신 폴더의 레코드만."""
        last = self.last_seen
        return [r for r in self.records if r.folder_date == last]

    @property
    def latest_file_count(self):
        return len(self.latest_records)

    @property
    def total_size_kb(self):
        return sum(r.file_size for r in self.latest_records) / 1024

    @property
    def voltage(self):
        """최신 레코드에서 전압 추출."""
        for r in reversed(self.records):
            if r.voltage is not None:
                return r.voltage
        return None

    @property
    def generation(self):
        for r in reversed(self.records):
            if r.generation:
                return r.generation
        return ''

    @property
    def mah_auto_ok(self):
        return any(r.mah_auto_ok for r in self.latest_records)

    @property
    def size_change(self):
        """최초 → 최신 파일 크기 변화율."""
        if self.folder_count < 2:
            return None
        first_recs = [r for r in self.records if r.folder_date == self.first_seen]
        last_recs = self.latest_records
        sz_first = sum(r.file_size for r in first_recs)
        sz_last = sum(r.file_size for r in last_recs)
        if sz_first == 0:
            return None
        return round((sz_last - sz_first) / sz_first * 100, 1)


# ═══════════════════════════════════════════════════════════════════
# 5. Excel COM 검증 (USE_EXCEL=True 일 때만 사용)
# ═══════════════════════════════════════════════════════════════════
def validate_file_with_excel(app, fpath, rec):
    """단일 파일을 Excel COM으로 열어 BDT 로딩 로직을 시뮬레이션.
    결과를 rec(FileRecord)에 직접 기록."""
    wb = None
    try:
        wb = app.books.open(str(fpath))  # xlwings는 str 경로 필요
        rec.excel_sheets = [s.name for s in wb.sheets]

        if "Plot Base Data" not in rec.excel_sheets:
            rec.excel_status = 'ERROR'
            rec.excel_issues = [
                f"'Plot Base Data' 시트 없음. 존재 시트: {rec.excel_sheets}"
            ]
            return

        ws = wb.sheets["Plot Base Data"]
        df = ws.used_range.offset(1, 0).options(
            pd.DataFrame, index=False, header=False
        ).value

        if df is None or (isinstance(df, pd.DataFrame) and df.empty):
            rec.excel_status = 'ERROR'
            rec.excel_issues = ["Plot Base Data 시트에 데이터 없음"]
            return

        # BDT 로직: drop(0) -> iloc[:, 1::2]
        df = df.drop(0)
        df_data = df.iloc[:, 1::2]
        df_data.reset_index(drop=True, inplace=True)
        df_data.index = df_data.index + 1

        rec.excel_data_rows = len(df_data)
        rec.excel_data_cols = len(df_data.columns)

        if rec.excel_data_cols == 0:
            rec.excel_status = 'ERROR'
            rec.excel_issues = ["홀수 열에 데이터 없음 (채널 데이터 0개)"]
            return

        # 용량 나누기 테스트
        cap = rec.capacity_mah or 0
        if cap > 0:
            df_ratio = df_data / cap
        else:
            df_ratio = df_data  # cap=0이면 비율 검사 스킵

        # 데이터 무결성 검사
        issues = []
        warnings = []
        numeric_df = df_data.apply(pd.to_numeric, errors='coerce')
        total_cells = numeric_df.shape[0] * numeric_df.shape[1]

        # NaN 비율
        nan_count = int(numeric_df.isna().sum().sum())
        nan_ratio = nan_count / total_cells if total_cells > 0 else 0
        if nan_ratio > 0.5:
            warnings.append(f"NaN {nan_ratio:.0%} ({nan_count}/{total_cells})")
        elif nan_ratio > 0.2:
            warnings.append(f"NaN {nan_ratio:.0%}")

        # 음수 값
        neg_count = int((numeric_df < 0).sum().sum())
        if neg_count > 0:
            warnings.append(f"음수 {neg_count}건")

        # 행 수 체크
        if rec.excel_data_rows < 5:
            warnings.append(f"행수 매우 적음: {rec.excel_data_rows}")

        # 병합 셀 로직 테스트
        rec.excel_merge_needed = False
        if cap > 0 and len(df_ratio) > 2:
            try:
                val0 = df_ratio.iat[0, 0]
                val2 = df_ratio.iat[2, 0]
                if pd.notna(val0) and pd.notna(val2) and val0 != 0:
                    if val2 < val0 * 0.5:
                        rec.excel_merge_needed = True
                        warnings.append("행 병합 로직 트리거")
            except Exception:
                pass

        rec.excel_issues = issues
        rec.excel_warnings = warnings
        rec.excel_status = 'ERROR' if issues else ('WARN' if warnings else 'OK')

    except Exception as e:
        rec.excel_status = 'ERROR'
        rec.excel_issues = [f"예외: {e}"]
    finally:
        if wb:
            try:
                wb.close()
            except Exception:
                pass


def run_excel_validation(all_records, rawdata_dir):
    """전체 파일에 대해 Excel COM 검증 수행."""
    print(f"\n{'='*80}")
    print(f"  Excel COM 데이터 검증 시작 (총 {len(all_records)}개 파일)")
    print(f"{'='*80}")

    app = None
    try:
        app = xw.App(visible=False, add_book=False)
        app.display_alerts = False
        app.screen_updating = False

        for idx, rec in enumerate(all_records, 1):
            fpath = (rawdata_dir / rec.folder_name / rec.filename).resolve()
            if not fpath.is_file():
                rec.excel_status = 'ERROR'
                rec.excel_issues = [f'파일 없음: {fpath}']
                print(f"  [{idx:3d}/{len(all_records)}] SKIP | 파일 없음: {fpath}")
                continue
            t0 = time.time()
            validate_file_with_excel(app, fpath, rec)
            elapsed = time.time() - t0

            icon = {'OK': '  OK', 'WARN': 'WARN', 'ERROR': 'FAIL'}.get(
                rec.excel_status, '????')
            short_name = rec.filename[:70]
            print(f"  [{idx:3d}/{len(all_records)}] {icon} | {short_name:<70s} | {elapsed:.1f}s")
            for iss in rec.excel_issues:
                print(f"           X {iss}")
            for w in rec.excel_warnings:
                print(f"           ! {w}")

    except Exception as e:
        print(f"\nExcel COM 오류: {e}")
        print("Excel이 설치되어 있고, NASCA DRM 플러그인이 활성화되어 있는지 확인하세요.")
    finally:
        if app:
            try:
                app.quit()
            except Exception:
                pass

    ok = sum(1 for r in all_records if r.excel_status == 'OK')
    warn = sum(1 for r in all_records if r.excel_status == 'WARN')
    fail = sum(1 for r in all_records if r.excel_status == 'ERROR')
    print(f"\n  검증 완료: OK={ok} / WARN={warn} / FAIL={fail}")


# ═══════════════════════════════════════════════════════════════════
# 6. 메인 스캔 로직
# ═══════════════════════════════════════════════════════════════════
def scan_all(rawdata_dir):
    """전체 스캔 → (folders_info, groups_dict, all_records)."""
    date_folders = discover_date_folders(rawdata_dir)
    if not date_folders:
        print(f"ERROR: {rawdata_dir}에 yymmdd 폴더가 없습니다.")
        sys.exit(1)

    print(f"스캔 대상: {rawdata_dir}")
    print(f"날짜 폴더: {len(date_folders)}개 ({date_folders[0][0]} ~ {date_folders[-1][0]})")

    groups = {}  # group_key → TestGroup
    folder_stats = []  # 각 폴더별 통계
    all_records = []  # 모든 FileRecord (Excel 검증용)

    for datestr, suffix, dirname, fullpath in date_folders:
        files = list_xls_files(fullpath)
        folder_stats.append({
            'date': datestr, 'suffix': suffix, 'dirname': dirname,
            'file_count': len(files),
        })

        for fname in files:
            try:
                rec = FileRecord(fname, datestr, dirname, fullpath)
                key = rec.group_key
                if key not in groups:
                    groups[key] = TestGroup(key)
                groups[key].add(rec)
                all_records.append(rec)
            except Exception as e:
                print(f"  WARN: 파싱 실패 [{dirname}/{fname}]: {e}")

    return date_folders, folder_stats, groups, all_records


# ═══════════════════════════════════════════════════════════════════
# 6. 리포트 생성
# ═══════════════════════════════════════════════════════════════════
def generate_report(date_folders, folder_stats, groups, rawdata_dir):
    """텍스트 리포트, CSV, JSON 생성."""
    latest_date = date_folders[-1][0]
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    all_groups = sorted(groups.values(), key=lambda g: (g.category, g.model, g.vendor))

    # 최신 폴더에 있는 그룹
    latest_groups = [g for g in all_groups if g.last_seen == latest_date]
    # 최신 폴더에 없는(과거에만 존재) 그룹
    past_only = [g for g in all_groups if g.last_seen != latest_date]

    lines = []
    def pr(s=''):
        lines.append(s)

    SEP = '=' * 140

    pr(SEP)
    pr(f"  신뢰성 데이터 종합 현황 리포트  |  최신 폴더: {latest_date}  |  분석일: {now}")
    mode_str = 'Excel COM 검증 포함' if USE_EXCEL else '메타데이터 분석 전용'
    pr(f"  분석 모드: {mode_str}")
    pr(SEP)

    # ── 데이터 규모 ──
    total_records = sum(g.file_count for g in all_groups)
    pr()
    pr("■ 데이터 규모")
    pr(f"  날짜 폴더 수: {len(date_folders)}개 ({date_folders[0][0]} ~ {latest_date})")
    pr(f"  총 파일 레코드: {total_records}개")
    pr(f"  고유 시험 항목(그룹): {len(all_groups)}개")
    pr(f"  최신 폴더 포함: {len(latest_groups)}개 / 미포함(과거만): {len(past_only)}개")

    # ── 폴더별 파일 수 추이 ──
    pr()
    pr(SEP)
    pr("■ 폴더별 파일 수 추이 (최근 20개)")
    recent_stats = [s for s in folder_stats if s['file_count'] > 0][-20:]
    for s in recent_stats:
        bar = '#' * min(s['file_count'] // 2, 80)
        sfx = f" ({s['suffix']})" if s['suffix'] else ''
        pr(f"  {s['date']}{sfx:10s} | {s['file_count']:4d}개 {bar}")

    # ── 카테고리별 현황 ──
    pr()
    pr(SEP)
    pr("■ 카테고리별 현황")
    cat_map = defaultdict(list)
    for g in all_groups:
        cat_map[g.category].append(g)

    pr(f"  {'카테고리':12s} | {'전체':>4s} | {'최신':>4s} | {'모델수':>5s} | 제조사")
    pr("  " + "-" * 100)
    for cat in sorted(cat_map):
        items = cat_map[cat]
        latest_cnt = sum(1 for g in items if g.last_seen == latest_date)
        models = set(g.model for g in items)
        vendors = sorted(set(g.vendor for g in items if g.vendor != '-'))
        pr(f"  {cat:12s} | {len(items):4d} | {latest_cnt:4d} | {len(models):5d} | {', '.join(vendors)}")

    # ── 최신 기준 종합 리스트 ──
    pr()
    pr(SEP)
    pr(f"■ 최신 기준 종합 리스트 (최신 폴더 {latest_date} 포함 항목)")
    pr(SEP)
    header = (
        f"  {'No':>3s} | {'카테':6s} | {'모델':24s} | {'제조사':10s} | {'개발':5s} "
        f"| {'세대':5s} | {'전압':6s} | {'용량':>6s} | {'온도셋':18s} | {'완성':5s} "
        f"| {'EA':>4s} | {'BLK':10s} | {'사이클힌트':20s} "
        f"| {'최초':6s} | {'최종':6s} | {'폴더':>4s} | {'파일':>4s} | {'크기':>7s} "
        f"| {'변화':>8s} | mAh | 태그"
    )
    pr(header)
    pr("  " + "-" * 200)

    for idx, g in enumerate(latest_groups, 1):
        temps_str = '/'.join(f"{t}°C" for t in g.all_temperatures) or '-'
        blks_str = ', '.join(g.all_blks) or '-'
        hints_str = '; '.join(g.all_cycle_hints) or '-'
        tags_str = ', '.join(g.all_tags) or '-'
        ea_str = str(g.total_ea) if g.total_ea else '-'
        cap_str = str(g.capacity) if g.capacity else '-'
        volt_str = f"{g.voltage:.2f}" if g.voltage else ''
        gen_str = g.generation or ''
        sz_str = f"{g.total_size_kb:.0f}K"
        change = g.size_change
        change_str = f"{change:+.0f}%" if change is not None else '-'
        mah_icon = '●' if g.mah_auto_ok else '○'

        pr(f"  {idx:3d} | {g.category:6s} | {g.model:24s} | {g.vendor:10s} "
           f"| {g.dev_stage:5s} | {gen_str:5s} | {volt_str:6s} | {cap_str:>6s} "
           f"| {temps_str:18s} | {g.temp_completeness:5s} | {ea_str:>4s} "
           f"| {blks_str:10s} | {hints_str:20s} "
           f"| {g.first_seen:6s} | {g.last_seen:6s} | {g.folder_count:4d} "
           f"| {g.latest_file_count:4d} | {sz_str:>7s} | {change_str:>8s} "
           f"| {mah_icon:3s} | {tags_str}")

    pr(f"\n  최신 포함: {len(latest_groups)}개 항목")

    # ── 과거에만 있는 항목 ──
    if past_only:
        pr()
        pr(SEP)
        pr(f"■ 과거에만 존재 (최신 폴더 {latest_date}에 미포함) → 완료/중단 추정")
        pr(SEP)
        pr(f"  {'No':>3s} | {'카테':6s} | {'모델':24s} | {'제조사':10s} | {'개발':5s} "
           f"| {'온도':18s} | {'최초':6s} | {'최종':6s} | {'폴더':>4s} | {'파일':>4s} | 상태추정")
        pr("  " + "-" * 150)
        for idx, g in enumerate(past_only, 1):
            temps_str = '/'.join(f"{t}°C" for t in g.all_temperatures) or '-'
            # 상태 추정: 최종→최신 간격으로 추정
            last_int = int(g.last_seen)
            latest_int = int(latest_date)
            gap = latest_int - last_int
            if gap > 500:
                status = "완료(오래)"
            elif gap > 100:
                status = "완료/중단"
            else:
                status = "최근누락?"
            pr(f"  {idx:3d} | {g.category:6s} | {g.model:24s} | {g.vendor:10s} "
               f"| {g.dev_stage:5s} | {temps_str:18s} | {g.first_seen:6s} "
               f"| {g.last_seen:6s} | {g.folder_count:4d} | {g.file_count:4d} | {status}")

    # ── 제조사별 현황 ──
    pr()
    pr(SEP)
    pr("■ 제조사별 현황")
    vendor_map = defaultdict(list)
    for g in all_groups:
        vendor_map[g.vendor].append(g)
    pr(f"  {'제조사':12s} | {'전체':>4s} | {'최신':>4s} | 카테고리")
    pr("  " + "-" * 80)
    for v in sorted(vendor_map, key=lambda x: -len(vendor_map[x])):
        items = vendor_map[v]
        latest_cnt = sum(1 for g in items if g.last_seen == latest_date)
        cats = sorted(set(g.category for g in items))
        pr(f"  {v:12s} | {len(items):4d} | {latest_cnt:4d} | {', '.join(cats)}")

    # ── 온도 완성도 ──
    pr()
    pr(SEP)
    pr("■ 온도 완성도 (15/23/45°C 3조건 확보율)")
    comp_dist = defaultdict(int)
    for g in latest_groups:
        comp_dist[g.temp_completeness] += 1
    for k in sorted(comp_dist):
        pr(f"  {k}: {comp_dist[k]}개 항목")

    # ── mAh 자동추출 호환성 ──
    pr()
    pr(SEP)
    pr("■ BDT mAh 자동추출 호환성 (최신 기준)")
    mah_ok = [g for g in latest_groups if g.mah_auto_ok]
    mah_fail = [g for g in latest_groups if not g.mah_auto_ok]
    pr(f"  자동추출 가능: {len(mah_ok)}개")
    pr(f"  수동입력 필요: {len(mah_fail)}개")
    if mah_fail:
        pr("  [수동입력 필요 항목]:")
        for g in mah_fail:
            pr(f"    → {g.model} / {g.vendor} / {g.dev_stage}")

    # ── 이력 추적 : 파일 수 변화가 큰 항목 ──
    pr()
    pr(SEP)
    pr("■ 이력 변화 감지 (2개 이상 폴더에 존재하며 파일수/크기 변동)")
    multi_folder = [g for g in latest_groups if g.folder_count >= 2]
    if multi_folder:
        pr(f"  {'모델':24s} | {'제조사':10s} | {'폴더수':>4s} | {'최초파일':>6s} → {'최신파일':>6s} | {'크기변화':>8s}")
        pr("  " + "-" * 100)
        for g in sorted(multi_folder, key=lambda x: -(x.size_change or 0)):
            first_cnt = len([r for r in g.records if r.folder_date == g.first_seen])
            last_cnt = g.latest_file_count
            change = g.size_change
            change_str = f"{change:+.0f}%" if change is not None else '-'
            pr(f"  {g.model:24s} | {g.vendor:10s} | {g.folder_count:4d} "
               f"| {first_cnt:6d} → {last_cnt:6d} | {change_str:>8s}")
    else:
        pr("  (이력 변화 항목 없음 - 단일 폴더 데이터)")

    # ── Excel COM 검증 결과 (USE_EXCEL 일 때만) ──
    if USE_EXCEL:
        all_recs_flat = []
        for g in all_groups:
            all_recs_flat.extend(g.records)
        validated = [r for r in all_recs_flat if r.excel_status is not None]
        if validated:
            ok_cnt = sum(1 for r in validated if r.excel_status == 'OK')
            warn_cnt = sum(1 for r in validated if r.excel_status == 'WARN')
            fail_cnt = sum(1 for r in validated if r.excel_status == 'ERROR')

            pr()
            pr(SEP)
            pr("■ Excel COM 데이터 검증 결과")
            pr(f"  검증 파일: {len(validated)}개")
            pr(f"  정상(OK): {ok_cnt}개 / 경고(WARN): {warn_cnt}개 / 실패(ERROR): {fail_cnt}개")

            # 열(채널) 수 분포
            col_dist = defaultdict(int)
            row_list = []
            for r in validated:
                if r.excel_data_cols is not None and r.excel_data_cols > 0:
                    col_dist[r.excel_data_cols] += 1
                if r.excel_data_rows is not None:
                    row_list.append(r.excel_data_rows)
            if col_dist:
                pr("\n  [데이터 열(채널) 수 분포]:")
                for k in sorted(col_dist):
                    pr(f"    {k:3d}열: {col_dist[k]:3d}개")
            if row_list:
                import statistics
                pr(f"\n  [데이터 행(사이클) 수]: "
                   f"최소={min(row_list)} / 중앙값={statistics.median(row_list):.0f} / "
                   f"최대={max(row_list)}")

            # 실패 파일 상세
            fail_recs = [r for r in validated if r.excel_status == 'ERROR']
            if fail_recs:
                pr(f"\n  [실패 파일 ({len(fail_recs)}개)]:")
                for r in fail_recs:
                    pr(f"    X {r.folder_name}/{r.filename}")
                    for iss in r.excel_issues:
                        pr(f"      -> {iss}")

            # 경고 파일 상세
            warn_recs = [r for r in validated if r.excel_status == 'WARN']
            if warn_recs:
                pr(f"\n  [경고 파일 ({len(warn_recs)}개)]:")
                for r in warn_recs:
                    warns = '; '.join(r.excel_warnings)
                    pr(f"    ! {r.folder_name}/{r.filename}: {warns}")

            # 병합 필요 파일
            merge_recs = [r for r in validated if r.excel_merge_needed]
            if merge_recs:
                pr(f"\n  [병합 로직 트리거 ({len(merge_recs)}개)]:")
                for r in merge_recs:
                    pr(f"    ~ {r.folder_name}/{r.filename}")

    pr()
    pr(SEP)
    pr("분석 완료.")

    return '\n'.join(lines)


def export_csv(groups, latest_date, output_path):
    """최신 기준 종합 리스트를 CSV로 내보내기."""
    all_groups = sorted(groups.values(), key=lambda g: (g.category, g.model, g.vendor))
    latest_groups = [g for g in all_groups if g.last_seen == latest_date]

    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([
            'No', '카테고리', '모델', '제조사', '개발단계', '세대', '전압(V)',
            '용량(mAh)', '온도', '온도완성', 'EA수', 'BLK', '사이클힌트',
            '최초폴더', '최종폴더', '폴더수', '파일수', '크기(KB)',
            '크기변화(%)', 'mAh자동', '태그',
        ])
        for idx, g in enumerate(latest_groups, 1):
            writer.writerow([
                idx, g.category, g.model, g.vendor, g.dev_stage,
                g.generation, g.voltage or '', g.capacity or '',
                '/'.join(f"{t}°C" for t in g.all_temperatures),
                g.temp_completeness,
                g.total_ea or '', ', '.join(g.all_blks),
                '; '.join(g.all_cycle_hints),
                g.first_seen, g.last_seen, g.folder_count,
                g.latest_file_count, round(g.total_size_kb),
                g.size_change if g.size_change is not None else '',
                'O' if g.mah_auto_ok else 'X',
                ', '.join(g.all_tags),
            ])


def export_json(groups, latest_date, output_path):
    """전체 레코드를 JSON으로 내보내기."""
    all_groups = sorted(groups.values(), key=lambda g: (g.category, g.model, g.vendor))
    data = {
        'latest_date': latest_date,
        'total_groups': len(all_groups),
        'groups': [],
    }
    for g in all_groups:
        data['groups'].append({
            'key': {
                'category': g.category,
                'model': g.model,
                'vendor': g.vendor,
                'dev_stage': g.dev_stage,
                'capacity_mah': g.capacity,
            },
            'temperatures': g.all_temperatures,
            'temp_completeness': g.temp_completeness,
            'blks': g.all_blks,
            'total_ea': g.total_ea,
            'cycle_hints': g.all_cycle_hints,
            'tags': g.all_tags,
            'first_seen': g.first_seen,
            'last_seen': g.last_seen,
            'folder_count': g.folder_count,
            'file_count': g.file_count,
            'latest_file_count': g.latest_file_count,
            'total_size_kb': round(g.total_size_kb),
            'mah_auto_ok': g.mah_auto_ok,
            'voltage': g.voltage,
            'generation': g.generation,
            'in_latest': g.last_seen == latest_date,
            'records': [r.to_dict() for r in g.records],
        })
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


# ═══════════════════════════════════════════════════════════════════
# 7. 엔트리포인트
# ═══════════════════════════════════════════════════════════════════
def main():
    print(f"========== 신뢰성 데이터 종합 분석기 ==========")
    print(f"대상 경로: {RAWDATA_DIR}")
    print(f"분석 모드: {'Excel COM 검증 포함' if USE_EXCEL else '메타데이터 전용'}")
    print()

    date_folders, folder_stats, groups, all_records = scan_all(RAWDATA_DIR)
    latest_date = date_folders[-1][0]

    # Excel COM 검증 (USE_EXCEL=True일 때)
    if USE_EXCEL:
        run_excel_validation(all_records, RAWDATA_DIR)

    # 리포트 생성
    report_text = generate_report(date_folders, folder_stats, groups, RAWDATA_DIR)

    # 콘솔 출력
    print(report_text)

    # 파일 저장
    txt_path = RAWDATA_DIR / '_신뢰성_종합현황.txt'
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    print(f"\n텍스트 리포트 저장: {txt_path}")

    csv_path = RAWDATA_DIR / '_신뢰성_종합현황.csv'
    export_csv(groups, latest_date, csv_path)
    print(f"CSV 저장: {csv_path}")

    json_path = RAWDATA_DIR / '_신뢰성_종합현황.json'
    export_json(groups, latest_date, json_path)
    print(f"JSON 저장: {json_path}")


if __name__ == '__main__':
    main()
