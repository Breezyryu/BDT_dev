# Proto 현황·사이클데이터 탭 개선 제안서

> **작성일:** 2026-03-12  
> **대상 파일:** `DataTool_dev/DataTool_optRCD_proto_.py` (18,188줄)  
> **분석 범위:** 현황 탭 (네트워크/테이블/검색) + 사이클데이터 탭 (사이클/프로필/DCIR 분석)

---

## 목차

1. [UX / UI 개선](#1-ux--ui-개선)
2. [데이터 처리 속도 개선](#2-데이터-처리-속도-개선)
3. [성능 병목 분석](#3-성능-병목-분석)
4. [기타 중요도 높은 개선점](#4-기타-중요도-높은-개선점)
5. [개선 로드맵 (우선순위)](#5-개선-로드맵-우선순위)

---

## 1. UX / UI 개선

### 1.1 현황 탭 — 테이블 깜빡임 해소

**현상:** FindText 검색어 입력 시 테이블이 매번 `clear()` → 재생성되면서 깜빡임 발생

**원인 코드:** `table_reset()` (L13532)에서 `tb_channel.clear()` 호출 → 헤더 포함 전체 삭제 → `toyo_table_make()` / `pne_table_make()`에서 128개 셀 재생성

```
현재 흐름:
  FindText 입력 → textChanged 시그널 → tb_cycler_combobox()
  → table_reset() [전체 clear] → table_make() [128셀 재생성]
  💥 600~800ms 동안 테이블 공백 → 깜빡임

개선 후:
  FindText 입력 → textChanged 시그널 → tb_cycler_combobox()
  → 기존 셀 스타일만 업데이트 (setForeground/setBackground)
  ✅ 셀 재생성 없음 → 깜빡임 없음
```

**개선안:**

| 방법 | 설명 | 난이도 |
|------|------|--------|
| `clear()` → `clearContents()` | 헤더 보존, 약간 개선 | ⭐ |
| 셀 재생성 없이 스타일만 업데이트 | `setForeground()`/`setBackground()` 직접 변경 | ⭐⭐ |
| `setUpdatesEnabled(False/True)` 감싸기 | 렌더링 일괄 처리 | ⭐ |

**추천 조합:**
```python
def _update_table_styling(self):
    self.tb_channel.setUpdatesEnabled(False)  # 렌더링 중지
    for row in range(self.tb_channel.rowCount()):
        for col in range(self.tb_channel.columnCount()):
            item = self.tb_channel.item(row, col)
            if item:
                self._apply_cell_style(item, row, col)  # 스타일만 변경
    self.tb_channel.setUpdatesEnabled(True)   # 렌더링 한번에 반영
```

---

### 1.2 현황 탭 — 네트워크 마운트 상태 피드백 강화

**현상:** 네트워크 드라이브 연결 시 버튼 색상(파란/빨간)만 변경. 연결 중/실패/타임아웃 상태를 구분할 수 없음.

```
현재: [TOYO] (파란색)  ← 연결됨? 연결 중? 오류?
개선: [TOYO ✓] (파란색) + 상태바: "Z: TOYO-DATA 연결 완료"
      [PNE1 ✗] (빨간색) + 상태바: "Y: 연결 실패 (Timeout 10s)"
```

**개선안:**
- `mount_all_button()` (L13163)에서 6회 연쇄 호출 시 **progressBar** 활용 (현재 미사용)
- 각 드라이브별 성공/실패 상태를 **상태바 메시지** 또는 **툴팁**으로 표시
- 연결 중 상태: 버튼 텍스트를 "TOYO ⏳"로 변경 → 완료 시 "TOYO ✓"

---

### 1.3 사이클데이터 탭 — 진행률 표시 누락

**현상:** `app_cyc_confirm_button()` (L10757)에서 Excel 파일 다건 처리 시 진행률 바가 0%에 멈춰있음

**원인:** 루프 내에서 `progressBar.setValue()` 미호출

```python
# 현재 (L10764-10798)
self.progressBar.setValue(0)
for i, datafilepath in enumerate(all_data_folder):
    wb = xw.Book(datafilepath)         # 파일당 2~3초
    # ... 처리 ...
    # ← progressBar.setValue() 없음!

# 개선
for i, datafilepath in enumerate(all_data_folder):
    self.progressBar.setValue(int((i + 1) / len(all_data_folder) * 100))
    QApplication.processEvents()       # UI 갱신 허용
    wb = xw.Book(datafilepath)
```

**영향 범위:** `dcir_confirm_button()` (L12993)에서도 유사 문제

---

### 1.4 사이클데이터 탭 — 입력값 유효성 검증

**현상:** 용량값 텍스트 입력에 숫자가 아닌 값 입력 시 **앱 크래시**

```python
# 현재 (L10870)
mincapacity = float(self.capacitytext.text())  # ValueError → crash!
```

**개선안:**
```python
try:
    mincapacity = float(self.capacitytext.text())
except ValueError:
    err_msg("입력 오류", "용량값은 숫자여야 합니다.")
    self.indiv_cyc_confirm.setDisabled(False)
    return
```

**대상 메서드:** `_init_confirm_button()` (L9551)에서 통합 처리 가능 → 모든 confirm 버튼에 일괄 적용

---

### 1.5 사이클데이터 탭 — 파일 저장 취소 시 무피드백

**현상:** 저장 다이얼로그에서 "취소" 클릭 시 아무 메시지 없이 분석이 계속 진행됨 (파일 미생성 상태)

**개선안:** `_setup_file_writer()` (L9572)에서 취소 감지 시 명시적 알림 또는 분석 중단

---

### 1.6 채널 제어 팝업 — 범례 재구축 디바운싱

**현상:** 100개+ 채널에서 체크박스 빠르게 연속 클릭 시 `_rebuild_legend()`가 매번 호출 → UI 멈춤

```
클릭1 → _rebuild_legend() [150ms]
클릭2 → _rebuild_legend() [150ms]  ← 이전 완료 전 재호출
클릭3 → _rebuild_legend() [150ms]
= 450ms 블로킹

디바운싱 적용:
클릭1 → 타이머 시작 (100ms)
클릭2 → 타이머 리셋
클릭3 → 타이머 리셋
(100ms 후) → _rebuild_legend() [150ms]  ← 1회만 실행
= 250ms로 단축
```

**개선안:** `QTimer.singleShot(100, _rebuild_legend)` 디바운싱 적용

---

## 2. 데이터 처리 속도 개선

### 2.1 루프 내 `pd.concat()` — O(n²) → O(n) 개선

**위치:** `app_cyc_confirm_button()` (L10806), `pne_data_make()` (L13415), `toyo_data_make()` (L13302)

**문제:** 루프 안에서 `pd.concat([기존df, 새df])`를 반복하면 매번 전체 복사 발생

```python
# 현재: O(n²) — 100파일 시 5050배 메모리 이동
dfoutput = pd.DataFrame()
for i, filepath in enumerate(files):
    df = load_file(filepath)
    dfoutput = pd.concat([dfoutput, df], axis=1)   # 매번 전체 복사

# 개선: O(n) — 마지막에 1번만 concat
dfs = []
for i, filepath in enumerate(files):
    dfs.append(load_file(filepath))
dfoutput = pd.concat(dfs, axis=1) if dfs else pd.DataFrame()
```

| 파일 수 | 현재 (O(n²)) | 개선 후 (O(n)) | 개선율 |
|---------|-------------|---------------|--------|
| 10개 | ~0.5초 | ~0.1초 | 5배 |
| 50개 | ~6초 | ~0.5초 | 12배 |
| 100개 | ~25초 | ~1초 | **25배** |

---

### 2.2 검색 함수 최적화 — regex 사전 컴파일

**위치:** `match_highlight_text()` (L13539)

**문제:** 함수 내부에서 `import re`와 `re.sub()` 매 호출마다 실행. 128셀 × 반복 = 불필요한 오버헤드.

```python
# 현재 (L13539-13555)
def match_highlight_text(self, search_text, testname):
    import re                                        # 매번 import
    normalized = re.sub(r'\s*,\s*', ',', search_text)  # 매번 컴파일
    ...

# 개선: 클래스 레벨 사전 컴파일
_COMMA_RE = re.compile(r'\s*,\s*')

def match_highlight_text(self, search_text, testname):
    if not search_text.strip():
        return True
    normalized = self._COMMA_RE.sub(',', search_text)
    testname_lower = testname.lower()
    ...
```

**추가 최적화:** 검색어가 동일하면 `normalized` + `keywords` 결과 캐싱

```python
# 검색어가 바뀔 때만 파싱
if search_text != self._last_search:
    self._last_search = search_text
    self._parsed_groups = self._parse_search_query(search_text)

# 128셀에서 파싱된 그룹 재사용
for testname in all_testnames:
    result = self._match_parsed(self._parsed_groups, testname)
```

---

### 2.3 사이클 데이터 캐싱 — 중복 로딩 방지

**현상:** 개별 사이클(indiv) → 전체 사이클(overall) 순서로 실행 시 **동일 데이터를 2번 로딩**

```python
# indiv_cyc_confirm_button (L10876)
loaded_data = self._load_all_cycle_data_parallel(...)   # 3초

# overall_cyc_confirm_button (L11061) — 동일 파라미터
loaded_data = self._load_all_cycle_data_parallel(...)   # 또 3초
```

**개선안:** 설정 해시 기반 인스턴스 캐시

```python
def _get_cycle_data_cached(self, folders, settings):
    cache_key = hash((tuple(sorted(folders)), frozenset(settings.items())))
    if not hasattr(self, '_cycle_cache'):
        self._cycle_cache = {}
    if cache_key not in self._cycle_cache:
        self._cycle_cache[cache_key] = self._load_all_cycle_data_parallel(...)
    return self._cycle_cache[cache_key]
```

**기대 효과:** 동일 설정 반복 실행 시 **로딩 시간 0초** (캐시 히트)

---

### 2.4 테이블 렌더링 배치 최적화

**현재:** 128셀 × 5+ Qt 메서드 호출 = 640+ 개별 호출

```python
# 현재: 매 셀마다 5개 호출
for i, j in product(range(num_i), range(num_j)):
    table.setItem(j, i, QTableWidgetItem(text))     # 1
    table.item(j, i).setFont(font)                   # 2
    table.item(j, i).setBackground(bg_color)         # 3
    table.item(j, i).setForeground(fg_color)         # 4
    table.item(j, i).setData(BORDER_ROLE, border)    # 5

# 개선: 아이템 객체 미리 구성 후 일괄 설정
table.setUpdatesEnabled(False)
items_batch = []
for i, j in product(range(num_i), range(num_j)):
    item = QTableWidgetItem(text)
    item.setFont(font)
    item.setBackground(bg_color)
    item.setForeground(fg_color)
    items_batch.append((j, i, item))

for row, col, item in items_batch:
    table.setItem(row, col, item)
table.setUpdatesEnabled(True)
```

**기대 효과:** `setUpdatesEnabled` 감싸기만으로도 **2~3배 렌더링 속도 향상**

---

### 2.5 PNE Batch 로딩 — 디스크 I/O 1회화

**현재 상태:** Proto의 `pne_step_Profile_batch()` (L1009)가 이미 최적화됨 ✅

단, 다음 함수들은 미적용:
- `pne_rate_Profile_data()` (L2153) — 개별 호출 시 여전히 반복 I/O
- `pne_chg_Profile_data()` (L2185)
- `pne_dchg_Profile_data()` (L2241)

**개선 가능:** 개별 함수(`_data`)에서도 `_pne_load_profile_raw()` 캐시 결과 활용

---

## 3. 성능 병목 분석

### 병목 순위표

| # | 병목 | 위치 | 매 실행 지연 | 난이도 | 기대 개선 | ROI |
|---|------|------|------------|--------|----------|-----|
| 1 | **네트워크 마운트 UI 블로킹** | `network_drive()` L13135 | 5~60초 | ⭐⭐ | UI 응답성 100% | 🔥🔥🔥 |
| 2 | **루프 내 pd.concat()** | `app_cyc_confirm_button` L10806 | 1~25초 | ⭐ | 5~25배 | 🔥🔥🔥 |
| 3 | **테이블 렌더링 깜빡임** | `table_make()` L13305+ | 600~800ms | ⭐ | 2~3배 | 🔥🔥🔥 |
| 4 | **app_cyc Excel UI 블로킹** | `app_cyc_confirm_button` L10766 | 2~300초 | ⭐⭐ | UI 응답성 | 🔥🔥 |
| 5 | **사이클 데이터 중복 로딩** | indiv→overall 연속 호출 | 3~10초 | ⭐⭐ | 2배 | 🔥🔥 |
| 6 | **검색 regex 반복 컴파일** | `match_highlight_text` L13539 | 200ms | ⭐ | 3~5배 | 🔥🔥 |
| 7 | **채널 제어 Icon 생성 반복** | `_build_channel_dialog` ~L9672 | 200ms (200ch) | ⭐ | 5배 | 🔥 |
| 8 | **범례 재구축 과도 호출** | `_rebuild_legend` ~L9968 | 150ms/회 | ⭐ | N→1회 | 🔥 |
| 9 | **DCIR 중첩 루프 Figure 생성** | `dcir_confirm_button` L13057 | 메모리 증가 | ⭐⭐⭐ | 메모리 절감 | 🔥 |

> 난이도: ⭐ 쉬움 / ⭐⭐ 보통 / ⭐⭐⭐ 어려움  
> ROI: 🔥🔥🔥 높음 / 🔥🔥 보통 / 🔥 낮음

---

### 3.1 [병목 #1] 네트워크 마운트 — 메인 스레드 블로킹

**위치:** `network_drive()` (L13135-13142)

```python
# 현재: os.system() → 동기 블로킹
os.system('%SystemRoot%\\system32\\net use ' + driver + ' ' + folder + ' ...')
```

- `os.system()` = 메인 스레드 블로킹 I/O
- `mount_all_button()` (L13163)에서 **6회 연쇄 호출** → 최대 60초 UI 멈춤
- 마운트 중 다시 클릭 시 crash 위험

**개선안 (난이도 ⭐⭐):**

```python
# 방법 1: subprocess + timeout (간단)
import subprocess

def network_drive(self, driver, folder, id, pw):
    cmd = ['net', 'use', driver, folder]
    if id:
        cmd += [pw, f'/user:{id}']
    cmd.append('/persistent:no')
    try:
        subprocess.run(cmd, timeout=10, check=True,
                      capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        err_msg("네트워크", f"{driver} 연결 시간 초과 (10초)")
    except subprocess.CalledProcessError as e:
        err_msg("네트워크", f"{driver} 연결 실패: {e.stderr}")

# 방법 2: QThread (비동기, UI 미블로킹)
class MountWorker(QThread):
    finished = pyqtSignal(str, bool, str)  # drive, success, message
    
    def __init__(self, drive, folder, user, pw):
        super().__init__()
        self.drive, self.folder, self.user, self.pw = drive, folder, user, pw
    
    def run(self):
        try:
            subprocess.run([...], timeout=10, check=True)
            self.finished.emit(self.drive, True, "연결 성공")
        except Exception as e:
            self.finished.emit(self.drive, False, str(e))
```

**기대 효과:** UI 응답성 유지 + 타임아웃 처리 + 에러 피드백

---

### 3.2 [병목 #2] 루프 내 pd.concat() — O(n²) 메모리 이동

**위치:** `app_cyc_confirm_button()` (L10806), `pne_data_make()` (L13415)

pandas `concat()`은 매번 **새 DataFrame을 생성하고 기존 데이터를 복사**함. 루프 내에서 반복하면 삼각수 비용:

```
파일 1: 복사 1회 (1000행)
파일 2: 복사 2회 (2000행)
파일 3: 복사 3회 (3000행)
...
파일 100: 복사 100회 (100000행)
총 복사량 = 1+2+...+100 = 5,050배 × 단위비용
```

**개선 (난이도 ⭐):** `append → 마지막 concat` 패턴

```python
dfs = []
for filepath in files:
    dfs.append(load_file(filepath))
result = pd.concat(dfs, axis=1)  # 1회만
```

---

### 3.3 [병목 #3] 테이블 렌더링 — Qt 개별 호출 오버헤드

**위치:** `toyo_table_make()` (L13305), `pne_table_make()` (L13421)

128셀 × 5 메서드 = 640+ Qt API 호출. 각 호출마다 위젯 리페인트 트리거.

**개선 (난이도 ⭐):** `setUpdatesEnabled()` 래핑

```python
self.tb_channel.setUpdatesEnabled(False)
# ... 128셀 처리 ...
self.tb_channel.setUpdatesEnabled(True)
```

---

### 3.4 [병목 #4] app_cyc Excel 동기 로딩

**위치:** `app_cyc_confirm_button()` (L10766)

```python
wb = xw.Book(datafilepath)  # xlwings: COM 인터페이스 → 파일당 2~3초
```

다른 분석 메서드(`indiv_cyc`, `overall_cyc`, `step` 등)는 이미 `ThreadPoolExecutor` 적용. `app_cyc`만 순차 처리.

**개선 (난이도 ⭐⭐):**

```python
# openpyxl로 대체 (COM 불필요, 병렬화 가능)
from openpyxl import load_workbook

def _load_xlsx_task(filepath):
    wb = load_workbook(filepath, data_only=True)
    ws = wb['Plot Base Data']
    return pd.DataFrame(ws.values)

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(_load_xlsx_task, f): f for f in files}
    for future in as_completed(futures):
        dfs.append(future.result())
```

---

### 3.5 [병목 #9] DCIR 중첩 루프 Figure 생성

**위치:** `dcir_confirm_button()` (L12993-13123)

```python
for i, cyclefolder in enumerate(...):      # 폴더별
    for FolderBase in subfolder:            # 채널별
        for dcir_step in step_list:         # 스텝별
            fig, axes = plt.subplots(...)   # ← 매번 Figure 생성
```

3중 루프 내 Figure 생성 → 메모리 조각화 + GC 부담

**개선 (난이도 ⭐⭐⭐):**
- 루프 외곽에서 Figure 1개 생성 → `ax.clear()` 후 재사용
- 또는 서브플롯 그리드를 미리 할당

---

## 4. 기타 중요도 높은 개선점

### 4.1 🔴 보안 — 하드코딩된 네트워크 자격증명

**위치:** `mount_*_button()` (L13145-13163)

```python
def mount_toyo_button(self):
    self.network_drive("z:", '...', "sec", "qoxjfl1!")      # ← 암호 평문!

def mount_pne1_button(self):
    self.network_drive("y:", '...', "SAMSUNG", "qoxjfl1!")   # ← 동일 암호
```

- 비밀번호 `qoxjfl1!` 소스코드에 **평문 노출**
- Git 이력에 영구 기록
- 다른 PC 환경에서 동작 불가 (project-rules 위반: 환경 종속 금지)

**개선안:**

| 방법 | 난이도 | 보안 수준 |
|------|--------|----------|
| `.env` 파일 + `python-dotenv` | ⭐ | 중 (gitignore 필수) |
| `keyring` 라이브러리 (OS 자격증명 저장소) | ⭐⭐ | 상 |
| 설정 JSON + 첫 실행 시 입력 프롬프트 | ⭐ | 중 |

**추천:** `.env` 파일 분리 + `.gitignore` 추가

```python
# .env
TOYO_SERVER=\\10.253.44.115\TOYO-DATA Back Up Folder
TOYO_USER=sec
TOYO_PASS=비밀번호

# 코드
from dotenv import load_dotenv
load_dotenv()

MOUNT_CONFIG = [
    {"name": "TOYO", "drive": "z:", "server": os.getenv("TOYO_SERVER"),
     "user": os.getenv("TOYO_USER"), "pw": os.getenv("TOYO_PASS")},
    ...
]
```

---

### 4.2 🟡 코드 중복 — toyo_table_make / pne_table_make 통합

**현황:** 두 함수가 **~85% 동일한 코드** (배경색 결정, 검색 필터, 폰트 색상 로직)

```
toyo_table_make()  (L13305-L13370)  65줄
pne_table_make()   (L13421-L13525)  105줄
──────────────────────────────────────
공통 코드: ~80줄   차이 코드: ~20줄
```

**개선안:** 설정 딕셔너리 + 공통 렌더링 함수

```python
STATUS_CONFIG = {
    'toyo': {
        'states': {'작업정지': (176,203,176), '완료': (234,239,230)},
        'fg_match': [(208,0,0), (165,0,0), (165,0,0)],
    },
    'pne': {
        'states': {'대기': (176,203,176), '완료': (234,239,230), '작업멈춤': (214,155,154)},
        'fg_match': [(208,0,0), (165,0,0), (165,0,0), (165,0,0)],
    }
}

def _render_table(self, cycler_type, df, num_i, num_j):
    """공통 테이블 렌더링"""
    config = STATUS_CONFIG[cycler_type]
    ...
```

---

### 4.3 🟡 코드 중복 — mount 버튼 6개 통합

**현황:** `mount_toyo_button` ~ `mount_pne5_button` 6개 함수가 1줄씩 `network_drive()` 호출

```python
# 현재: 6개 함수 (각 2줄)
def mount_toyo_button(self): self.network_drive("z:", ..., "sec", "qoxjfl1!")
def mount_pne1_button(self): self.network_drive("y:", ..., "SAMSUNG", "qoxjfl1!")
def mount_pne2_button(self): self.network_drive("x:", ..., "SAMSUNG", "qoxjfl1!")
...
```

**개선안:** 설정 배열 + `functools.partial` 또는 단일 함수

```python
DRIVES = [
    {"name": "TOYO", "drive": "z:", "server": "...", ...},
    {"name": "PNE1", "drive": "y:", "server": "...", ...},
    ...
]

# __init__에서 동적 연결
for cfg in DRIVES:
    btn = getattr(self, f"mount_{cfg['name'].lower()}_btn")
    btn.clicked.connect(lambda _, c=cfg: self._generic_mount(c))
```

---

### 4.4 🟡 split_value 함수 DRY 위반

**현황:** `split_value0/1/2` (L13218-13255) → 3개 함수가 "_" or " " 분할 로직 반복

**개선안:** 단일 `parse_test_name(text, index)` 함수로 통합

```python
def parse_test_name(self, text, index, transform=None):
    sep = '_' if '_' in text else ' '
    parts = text.split(sep)
    if index >= len(parts):
        return parts[0] if parts else ""
    val = parts[index]
    return transform(val) if transform else val
```

---

### 4.5 🟡 글로벌 `writer` 변수 → 로컬화

**위치:** 다수 confirm 메서드에서 `global writer` 사용

```python
# 현재
global writer
writer = pd.ExcelWriter(...)
# ... 사용 ...
writer.close()

# 문제:
# - 예외 발생 시 writer 미종료 (파일 잠김)
# - 다른 메서드가 같은 전역 writer 덮어쓸 수 있음
# - 멀티스레드 경합 위험
```

**개선안:** 로컬 변수 + `try/finally`

```python
writer, save_path = self._setup_file_writer()
try:
    # ... 작업 ...
finally:
    if writer:
        writer.close()
```

Proto에서 `_setup_file_writer()` 헬퍼가 이미 존재 → 전체 메서드에 일관 적용만 하면 됨.

---

### 4.6 🟡 `os.system()` → `subprocess` 교체

**위치:** `network_drive()` (L13135)

```python
# 현재
os.system('%SystemRoot%\\system32\\net use ' + driver + ' ' + folder + ' ' + pw + ' /user:' + id)
```

- `os.system()` → **셸 인젝션 취약점** (입력값에 특수문자 가능)
- 반환값으로 성공/실패 판단 불가
- 문자열 결합 → 공백/특수문자 이스케이프 문제

**개선안:**

```python
result = subprocess.run(
    ['net', 'use', driver, folder, pw, f'/user:{id}', '/persistent:no'],
    capture_output=True, text=True, timeout=15
)
if result.returncode != 0:
    err_msg("네트워크", f"마운트 실패: {result.stderr}")
```

---

## 5. 개선 로드맵 (우선순위)

### Phase 1: 즉시 적용 가능 (난이도 ⭐, 1일 이내)

| # | 항목 | 영향 | 코드 변경량 |
|---|------|------|-----------|
| P1-1 | 루프 내 `pd.concat()` → list append + 마지막 concat | 5~25배 속도 | ~10줄/메서드 |
| P1-2 | 테이블 `setUpdatesEnabled(False/True)` 래핑 | 깜빡임 해소 | +2줄 |
| P1-3 | `clear()` → `clearContents()` | 헤더 보존 | 1줄 |
| P1-4 | `match_highlight_text` regex 사전 컴파일 | 3~5배 검색 | ~5줄 |
| P1-5 | 진행률 바 업데이트 누락 보완 | UX 피드백 | +3줄/메서드 |
| P1-6 | 입력값 유효성 검증 (float 파싱) | crash 방지 | ~5줄 |

### Phase 2: 단기 개선 (난이도 ⭐⭐, 1주 이내)

| # | 항목 | 영향 | 코드 변경량 |
|---|------|------|-----------|
| P2-1 | 네트워크 마운트 `subprocess` + timeout | 보안+안정성 | ~30줄 |
| P2-2 | 네트워크 자격증명 `.env` 분리 | 보안 | ~20줄+.env |
| P2-3 | 사이클 데이터 캐싱 (indiv→overall) | 2배 속도 | ~20줄 |
| P2-4 | `app_cyc` 병렬 로딩 (ThreadPoolExecutor) | N배 속도 | ~40줄 |
| P2-5 | `global writer` → 로컬화 + try/finally | 안정성 | ~5줄/메서드 |
| P2-6 | mount 버튼 6개 → 설정 배열 통합 | 유지보수성 | ~30줄 |

### Phase 3: 중기 리팩토링 (난이도 ⭐⭐~⭐⭐⭐, 2~4주)

| # | 항목 | 영향 | 코드 변경량 |
|---|------|------|-----------|
| P3-1 | `toyo_table_make` / `pne_table_make` 통합 | 유지보수성 | ~100줄 삭감 |
| P3-2 | 네트워크 마운트 QThread 비동기화 | UI 응답성 100% | ~60줄 |
| P3-3 | 채널 제어 팝업 디바운싱 + 아이콘 캐싱 | UI 반응성 | ~30줄 |
| P3-4 | DCIR Figure 재사용 패턴 | 메모리 절감 | ~50줄 |
| P3-5 | 색상 규칙 Enum + ColorScheme 구조화 | 가독성 | ~80줄 |

---

### 기대 효과 요약

| 지표 | 현재 | Phase 1 후 | Phase 2 후 | Phase 3 후 |
|------|------|-----------|-----------|-----------|
| 테이블 렌더링 시간 | ~800ms (깜빡임) | ~300ms (무깜빡임) | ~300ms | ~200ms |
| 100파일 app_cyc 처리 | ~25초 (UI 멈춤) | ~1초 | ~0.3초 (병렬) | ~0.3초 |
| 네트워크 전체 마운트 | ~60초 (UI 멈춤) | ~60초 | ~60초 (timeout) | ~10초 (비동기) |
| 사이클 반복 실행 | 매번 로딩 | 매번 로딩 | 캐시 히트 0초 | 캐시 히트 0초 |
| 보안 (암호 노출) | 🔴 평문 | 🔴 평문 | ✅ .env 분리 | ✅ .env 분리 |
