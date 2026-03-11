# 현황 탭 & 사이클데이터 탭 딥서치 분석 보고서

> **작성일:** 2026-03-12  
> **비교 대상:** `DataTool.py` (현재) vs `BAK/BatteryDataTool_origin.py` (원본)

---

## 목차

1. [현황 탭](#1-현황-탭)
   - [1.1 코드 변경점](#11-코드-변경점-origin--current)
   - [1.2 기능 상세 로직](#12-기능-상세-로직)
   - [1.3 코드 설명](#13-코드-설명-파이썬-기초-관점)
   - [1.4 성능 개선 가능 부분](#14-성능-개선-가능-부분)
2. [사이클데이터 탭](#2-사이클데이터-탭)
   - [2.1 코드 변경점](#21-코드-변경점-origin--current)
   - [2.2 기능 상세 로직](#22-기능-상세-로직)
   - [2.3 코드 설명](#23-코드-설명-파이썬-기초-관점)
   - [2.4 성능 개선 가능 부분](#24-성능-개선-가능-부분)

---

## 1. 현황 탭

### 1.1 코드 변경점 (Origin → Current)

#### (1) `toyo_base_data_make` — 타입 변환 버그 수정

| 항목 | Origin | Current |
|------|--------|---------|
| **위치** | `BAK/BatteryDataTool_origin.py` L10387-10423 | `DataTool.py` L12739-12786 |
| **핵심 변경** | `int` 컬럼에 문자열 직접 할당 | `.astype(object)` 추가 후 문자열 할당 |
| **에러 방지** | 파일 없으면 에러 발생 | 빈 DataFrame 반환 |

**Origin 코드 (문제)**
```python
toyo_data["use"] = toyo_data["use"].astype(int)
# ... 중략 ...
# ❌ int 타입 컬럼에 문자열("완료", "작업정지") 직접 할당 → 경고/에러 가능
toyo_data.loc[(toyo_data["chno"] == 1) & (toyo_data["use"] == 0), "use"] = "완료"
toyo_data.loc[(toyo_data["chno"] == 0) & (toyo_data["use"] == 0), "use"] = "작업정지"
toyo_data.loc[toyo_data["use"] == 1, "use"] = "작업중"
```

**Current 코드 (수정됨)**
```python
toyo_data["use"] = toyo_data["use"].astype(int)
# ... 중략 ...
toyo_data["use"] = toyo_data["use"].astype(object)  # ✅ 타입 변환 추가
toyo_data.loc[(toyo_data["chno"] == 1) & (toyo_data["use"] == 0), "use"] = "완료"
toyo_data.loc[(toyo_data["chno"] == 0) & (toyo_data["use"] == 0), "use"] = "작업정지"
toyo_data.loc[toyo_data["use"] == 1, "use"] = "작업중"
```

- **왜 바뀌었나?**: pandas에서 `int` 타입의 컬럼에 문자열을 넣으면 경고가 발생하거나 예기치 않은 동작을 할 수 있음. `astype(object)`로 먼저 타입을 변환하면 숫자/문자열을 자유롭게 혼합할 수 있음
- **추가**: 파일이 없을 때 빈 DataFrame 반환하도록 `else` 분기 추가 (에러 방지)

---

#### (2) `pne_table_make` — JSON 인코딩 및 에러 처리 추가

| 항목 | Origin | Current |
|------|--------|---------|
| **위치** | `BAK/BatteryDataTool_origin.py` L10517-10603 | `DataTool.py` L12874-12960 |
| **인코딩** | `open(path)` (기본 인코딩) | `open(path, encoding='cp949', errors='ignore')` |
| **에러 처리** | 없음 | `json.JSONDecodeError` 예외 처리 추가 |

**Origin 코드**
```python
with open(pneworkpath) as f1:       # ❌ 인코딩 미지정 → 한글 깨짐 가능
    js1 = json.loads(f1.read())
```

**Current 코드**
```python
with open(pneworkpath, encoding='cp949', errors='ignore') as f1:  # ✅ CP949 인코딩 명시
    js1 = json.loads(f1.read())

# 단일 모듈 파일만 있는 경우:
with open(pneworkpath, encoding='cp949', errors='ignore') as f1:
    try:
        js1 = json.loads(f1.read())
    except json.JSONDecodeError as e:  # ✅ JSON 파싱 에러 처리
        print(f"JSON 오류: {e} 라인 {e.line} 수정 필요")
```

- **왜 바뀌었나?**: PNE 충방전기의 JSON 파일에 한글이 포함되어 있어, CP949(Windows 한글) 인코딩으로 명시해야 파일을 제대로 읽을 수 있음. `errors='ignore'`는 읽을 수 없는 문자를 무시

---

#### (3) 변경 없는 부분

아래 메서드들은 Origin과 Current 간 **코드 차이 없음**:

- `tb_cycler_combobox()` — 사이클러 선택 시 테이블 갱신
- `tb_room_combobox()` — 실험실 선택 시 사이클러 목록 변경
- `tb_info_combobox()` — 정보 유형 변경 시 테이블 갱신
- `toyo_table_make()` — Toyo 데이터 테이블 시각화
- `table_reset()` — 테이블 초기화
- `change_drive()` — 드라이브 문자 변환

---

### 1.2 기능 상세 로직

#### 전체 흐름도

```
사용자가 "현황" 탭 진입
  ├─ 실험실 선택 (tb_room 콤보박스)
  │   └─ tb_room_combobox() → 사이클러 목록 업데이트
  ├─ 사이클러 선택 (tb_cycler 콤보박스)
  │   └─ tb_cycler_combobox()
  │       ├─ table_reset() → 테이블 초기화
  │       ├─ [Toyo인 경우] toyo_table_make()
  │       │   └─ toyo_base_data_make() → 데이터 수집
  │       └─ [PNE인 경우] pne_table_make()
  │           └─ JSON 파일 읽기 → 데이터 가공
  └─ 정보 유형 변경 (tb_info 콤보박스)
      └─ tb_info_combobox() → tb_cycler_combobox() 재호출
```

#### `tb_room_combobox()` — 실험실 선택

| Index | 실험실 | 사이클러 목록 |
|-------|--------|-------------|
| 0 | 기본 | Toyo1~5, PNE1~5 |
| 1 | PNE 그룹1 | PNE01~PNE08 |
| 2 | PNE 그룹2 | PNE09~PNE16 |
| 3 | PNE 그룹3 | PNE17~PNE25 |
| 4 | 전체 | 위 전부 (35개) |

- 콤보박스(드롭다운)에서 실험실을 선택하면, 해당 실험실에 속한 사이클러 목록을 `tb_cycler` 콤보박스에 채워 넣음

#### `tb_cycler_combobox()` — 사이클러별 데이터 표시

1. 사이클러 이름(예: "Toyo1", "PNE05")을 딕셔너리에서 검색
2. 딕셔너리 값에는 `(열 수, 행 수, 인덱스, 사이클러 이름)` 정보가 있음
3. Toyo → `toyo_table_make()` / PNE → `pne_table_make()` 호출

#### `toyo_base_data_make()` — Toyo 데이터 수집

1. **경로**: `z:\Working\[블록명]\Chpatrn.cfg` 파일 읽기
2. **데이터 구조**: CSV 형식, 마지막 쉼표 제거 후 7, 1, 5, 9번째 컬럼만 추출
3. **상태 보고서**: `ExperimentStatusReport.dat`에서 온도, 사이클, 전압 추출
4. **상태 코드 변환**:
   - `chno=1, use=0` → "완료" (실험 끝남)
   - `chno=0, use=0` → "작업정지" (중단됨)
   - `use=1` → "작업중" (진행 중)

#### `toyo_table_make()` — 색상 코딩 규칙

| 조건 | 배경색 | 의미 |
|------|--------|------|
| 작업정지/완료 | 주황색 (255,127,0) | 사용 가능 또는 완료된 채널 |
| 전압 없음 ("-") | 하늘색 (200,255,255) | 전압 측정 안 됨 |
| Toyo1 ch>64 | 빨강 글씨 | 고온 구역 |
| Toyo2 ch>64 | 파랑 글씨 | 저온 구역 |
| Toyo3 ch>64 | 빨강 글씨 | 고온 구역 |
| 검색 불일치 | 회색 글씨 (175,175,175) | 필터링 제외된 항목 |

#### `pne_table_make()` — PNE 데이터 수집 및 표시

1. **데이터 소스**: `Module_1_channel_info.json`, `Module_2_channel_info.json`
2. **온도 단위**: JSON의 `Temperature` 값 × 1000 → 정수 변환
3. **사이클 정보**: `Step_No / Current_Cycle_Num / Total_Cycle_Num` 형태로 조합
4. **경로 변환**: `change_drive()`로 D:/E: 드라이브 → 설정된 경로로 변경

**PNE 색상 코딩 규칙**:

| 조건 | 배경색/글씨색 | 의미 |
|------|-------------|------|
| 대기/준비 | 하늘색 배경 | 사용 가능 채널 |
| 완료 | 주황색 배경 | 실험 완료 |
| 작업멈춤 | 분홍색 배경 (255,200,229) | 실험 중단 |
| 온도 10~20°C | 파란 글씨 | 저온 (약 15°C) |
| 온도 30~40°C | 녹색 글씨 | 중온 (약 35°C) |
| 온도 40~50°C | 빨간 글씨 | 고온 (약 45°C) |

---

### 1.3 코드 설명 (파이썬 기초 관점)

#### 콤보박스 연동 패턴

```python
# 콤보박스: 드롭다운 메뉴에서 항목을 선택하는 UI 요소
self.tb_room.currentIndexChanged.connect(self.tb_room_combobox)
```
- `currentIndexChanged`: 사용자가 드롭다운에서 다른 항목을 선택할 때 발생하는 "신호(Signal)"
- `.connect(함수이름)`: 이 신호가 발생하면 `tb_room_combobox` 함수를 자동으로 실행
- PyQt6의 **Signal-Slot 패턴**: 사용자가 UI를 조작하면 → 미리 연결해둔 함수가 실행됨

#### 딕셔너리 기반 분기 처리

```python
toyo_table_makers = {
    "Toyo1": (8, 16, 0, self.toyo_cycler_name[0]),  # (열 수, 행 수, 인덱스, 이름)
    "Toyo2": (8, 16, 1, self.toyo_cycler_name[1]),
    ...
}
cycler_text = self.tb_cycler.currentText()  # 사용자가 선택한 텍스트
if cycler_text in toyo_table_makers:
    col_count, row_count, index, name = toyo_table_makers[cycler_text]
    self.toyo_table_make(col_count, row_count, index, name)
```
- **딕셔너리**: `{키: 값}` 형태의 자료구조. 여기서 키="사이클러 이름", 값="설정 튜플"
- **튜플 언팩킹**: `(8, 16, 0, name)` → 각각 `col_count`, `row_count`, `index`, `name` 변수에 대입
- `if-elif` 체인 대신 딕셔너리를 사용하면 코드가 깔끔해짐

#### QTableWidget 셀 설정

```python
# 테이블의 (j-1)행, (i-1)열에 텍스트 넣기
self.tb_channel.setItem(j - 1, i - 1, 
    QtWidgets.QTableWidgetItem("001| 작동중"))

# 배경색 변경
self.tb_channel.item(j - 1, i - 1).setBackground(QtGui.QColor(255, 127, 0))

# 글자색 변경
self.tb_channel.item(j - 1, i - 1).setForeground(QtGui.QColor(0, 0, 255))
```
- `QTableWidgetItem`: 테이블 한 칸에 들어갈 데이터 객체
- `QColor(R, G, B)`: RGB 값(0~255)으로 색상 지정. 예: (255,0,0)=빨강, (0,0,255)=파랑

#### lambda 표현식과 .where()

```python
self.df["day"] = self.df['testname'].apply(self.split_value0)
self.df["vol"] = self.df["Voltage"].where(self.df["Voltage"].astype('float') > 0.04, "-")
```
- `.apply(함수)`: DataFrame의 각 행에 함수를 적용. `split_value0`은 테스트명에서 날짜를 추출
- `.where(조건, 대체값)`: 조건이 참이면 원래 값 유지, 거짓이면 "-"로 대체

---

### 1.4 성능 개선 가능 부분

#### (1) 네트워크 드라이브 I/O 병목

```python
# 현재: Z 드라이브(네트워크 공유)에서 직접 읽기
toyoworkpath = "z:\\Working\\" + self.toyo_blk_list[toyo_num] + "\\Chpatrn.cfg"
```

**문제**: Z 드라이브 접근 시 네트워크 지연이 발생하면 UI가 멈추는("프리징") 현상 발생  
**개선안**:
- `QThread`나 `threading.Thread`로 데이터 로딩을 백그라운드에서 처리
- 로딩 중 프로그레스바 또는 로딩 인디케이터 표시
- 캐시 도입: 최초 로드 후 일정 시간 내 재호출 시 캐시 데이터 사용

#### (2) JSON 파일 반복 읽기

```python
# pne_data_make()와 pne_table_make()에서 동일한 JSON을 중복 읽음
pneworkpath = self.pne_work_path_list[pne_num] + "\\Module_1_channel_info.json"
```

**개선안**: JSON 읽기 결과를 인스턴스 변수에 캐시하여 중복 I/O 제거

#### (3) 이중 for 루프 — UI 배치 업데이트

```python
for i in range(1, num_i + 1):
    for j in range(1, num_j + 1):
        chnl_name = i + (j - 1) * num_i
        # ... 셀 하나하나 설정
```

**문제**: Toyo1의 경우 8×16=128개 셀을 개별적으로 `setItem`, `setFont`, `setBackground`, `setForeground` 호출 → UI 갱신이 빈번  
**개선안**:
- `tb_channel.setUpdatesEnabled(False)` → 루프 완료 후 `setUpdatesEnabled(True)` 로 배치 업데이트
- `QTableWidget.blockSignals(True)` 로 루프 중 불필요한 시그널 차단

#### (4) 검색 필터 — 반복 호출 제거

```python
if (str(self.FindText.text()) == "") or (str(self.FindText.text()) in self.df.loc[...,"testname"]):
```

**문제**: 매 셀마다 `self.FindText.text()` 를 호출 (128회 이상)  
**개선안**: 루프 전에 한 번만 `search_text = self.FindText.text()` 로 변수 저장

---

## 2. 사이클데이터 탭

### 2.1 코드 변경점 (Origin → Current)

#### 전체 변경 요약

| 구분 | Origin | Current | 변경 타입 |
|------|--------|---------|----------|
| **색상 팔레트** | 하드코딩 리스트 10색 | `THEME['PALETTE']` 상수 | 아키텍처 개선 |
| **데이터 로딩** | 순차(1개씩) | `ThreadPoolExecutor` 병렬(4개 동시) | **핵심 성능 개선** |
| **그래프 함수** | 반환값 없음 | `(artists, color)` 반환 | 기능 추가 |
| **채널 제어** | 없음 | `channel_map` + 토글 버튼 팝업 | **신규 기능** |
| **탭 생성** | 매 루프마다 생성 | 첫 유효 데이터에서만 | 버그 수정 |
| **범례 처리** | 빈 문자열 `""` | `"_nolegend_"` + 중복 제거 | 버그 수정 |
| **코드 중복** | 각 메서드마다 동일 코드 반복 | 헬퍼 메서드 추출 | 리팩토링 |
| **global writer** | 전역 변수 사용 | 로컬 변수 사용 (프로필 분석) | 리팩토링 |
| **범례 길이** | 무제한 | 최대 40자 제한 | UI 개선 |
| **코인셀 모드** | 없음 | `set_coincell_mode()` + `is_micro_unit()` | **신규 기능** |

---

#### (1) `THEME` 상수 도입 (L46-76)

**Origin**:
```python
# 사용 위치마다 하드코딩
graphcolor = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
```

**Current**:
```python
THEME = {
    'PALETTE': ['#3C5488', '#E64B35', '#00A087', '#F39B7F', '#4DBBD5',
                '#8491B4', '#B09C85', '#91D1C2', '#DC0000', '#7E6148'],
    'FIG_FACECOLOR': '#FFFFFF',
    'AX_FACECOLOR': '#FAFBFD',
    'SCATTER_SIZE': 7,
    'GRID_ALPHA': 0.18,
    'SUPTITLE_SIZE': 15,
    'LEGEND_SIZE': 'small',
    # ... 등등
}
```
- 색상 팔레트가 기본 matplotlib 색상에서 **학술 논문 스타일 색상**으로 변경됨
- 그래프의 모든 스타일 설정을 한 곳에서 관리 가능

---

#### (2) 병렬 데이터 로딩 (핵심 변경)

**Origin** — 순차 로딩:
```python
# 폴더 하나씩 순서대로 처리 (느림)
for FolderBase in subfolder:
    if not check_cycler(cyclefolder):
        cyctemp = toyo_cycle_data(FolderBase, ...)
    else:
        cyctemp = pne_cycle_data(FolderBase, ...)
    # 바로 그래프 그리기
```

**Current** — 병렬 로딩:
```python
# 1단계: 모든 폴더의 데이터를 동시에 로딩 (ThreadPoolExecutor)
loaded_data = self._load_all_cycle_data_parallel(
    all_data_folder, mincapacity, firstCrate,
    ..., max_workers=4   # 최대 4개 작업 동시 실행
)

# 2단계: 로딩 완료된 데이터로 그래프 그리기
for i, cyclefolder in enumerate(all_data_folder):
    for sub_idx, FolderBase in enumerate(subfolder):
        if (i, sub_idx) not in loaded_data:
            continue
        folder_path, cyctemp = loaded_data[(i, sub_idx)]
        # 그래프 그리기
```

**병렬 로딩 구현 세부** (`_load_all_cycle_data_parallel`, L10182-10213):
1. 모든 폴더 경로를 `tasks` 리스트에 수집
2. `ThreadPoolExecutor(max_workers=4)` 로 4개의 워커 스레드 생성
3. 각 워커가 `_load_cycle_data_task()` 실행 → CSV 파일 읽기 및 처리
4. 결과를 `(폴더인덱스, 서브폴더인덱스)` 키로 딕셔너리에 저장
5. 진행률 0~50% → 데이터 로딩, 50~100% → 그래프 생성

---

#### (3) `graph_output_cycle()` 반환값 추가

**Origin** (L223-245):
```python
def graph_output_cycle(df, xscale, ..., ax1, ax2, ax3, ax4, ax5, ax6):
    graph_cycle(...)    # 그래프만 그리고 끝
    graph_cycle(...)
    # 반환값 없음
    colorno = colorno % 9 + 1
```

**Current** (L315-340):
```python
def graph_output_cycle(df, xscale, ..., ax1, ax2, ax3, ax4, ax5, ax6):
    artists = []        # 그래프 요소(점/선)를 수집
    color = graphcolor[colorno % len(THEME['PALETTE'])]
    artists.append(graph_cycle(...))    # 각 그래프의 아티스트 수집
    artists.append(graph_cycle(...))
    # ...
    return artists, color   # ✅ 채널 제어에 사용
```
- `artists`: 각 점/선 그래프 요소를 모아둠 → 나중에 채널 표시/숨기기에 활용
- `color`: 해당 채널의 색상 → 팝업 범례에서 색상 표시에 사용

---

#### (4) 채널 제어 기능 (신규)

Origin에는 존재하지 않는 **완전히 새로운 기능**

**구성 요소**:

| 메서드 | 위치 | 역할 |
|--------|------|------|
| `_finalize_cycle_tab()` | L9896-9920 | 탭에 채널 제어 토글 버튼 붙이기 |
| `_create_cycle_channel_control()` | L9440-9895 | 채널 표시/숨기기 팝업 UI 전체 생성 (약 450줄) |

**동작 원리**:
1. 각 채널의 그래프 요소(`artists`)를 `channel_map` 딕셔너리에 색상별로 저장
2. 탭 상단에 토글 버튼 추가 → 클릭하면 채널 목록 팝업 표시
3. 팝업에서 채널 선택/해제 시 해당 채널의 모든 그래프 요소를 `set_visible(True/False)`로 전환
4. 하이라이트 기능: 선택한 채널만 강조하고 나머지는 흐리게 처리
5. 서브 채널별 개별 제어도 가능 (`sub_channel_map`)

---

#### (5) 헬퍼 메서드 추출 (리팩토링)

Origin에서 각 버튼마다 반복되던 코드를 공통 메서드로 추출:

| 헬퍼 메서드 | 위치 | 대체한 반복 코드 |
|------------|------|----------------|
| `_init_confirm_button()` | L9377-9402 | 버튼 비활성화 + 설정 로드 + 경로 설정 |
| `_setup_file_writer()` | L9405-9440 | Excel 파일 저장 다이얼로그 + writer 생성 |
| `_create_plot_tab()` | 프로필 분석용 | 탭 + 캔버스 + 툴바 생성 |
| `_finalize_plot_tab()` | L9921-9931 | 일반 플롯 탭 최종 조립 |
| `_setup_legend()` | L9932-9950+ | 범례 자동 설정 (항목 수에 따라 컬러바 전환) |

**예시 — `_init_confirm_button()`**:
```python
# Origin: 각 버튼 메서드마다 이 코드가 반복됨
self.StepConfirm.setDisabled(True)
firstCrate, mincapacity, CycleNo, ... = self.Profile_ini_set()
pne_path = self.pne_path_setting()
all_data_folder = pne_path[0]
all_data_name = pne_path[1]
self.StepConfirm.setEnabled(True)

# Current: 한 줄로 대체
init_data = self._init_confirm_button(self.StepConfirm)
firstCrate = init_data['firstCrate']
all_data_folder = init_data['folders']
```

---

#### (6) 범례 처리 개선

**Origin**:
```python
temp_lgnd = ""  # 빈 문자열 → matplotlib가 빈 범례 항목 생성
```

**Current**:
```python
temp_lgnd = "_nolegend_"  # matplotlib 특수 문자열 → 범례에서 자동 제외

# 범례 중복 제거 로직 추가 (overall에서)
_handles, _labels = _ax.get_legend_handles_labels()
_seen = set()
_hl_unique = []
for h, l in _hl:
    if l not in _seen:
        _seen.add(l)
        _hl_unique.append((h, l))
```

- `"_nolegend_"`: matplotlib에서 `_`로 시작하는 라벨은 범례에 표시하지 않는 규칙 활용
- 중복 제거: 같은 이름의 범례가 여러 번 나오는 것을 방지

---

#### (7) 코인셀 모드 (신규 기능)

```python
# L231-234: 전역 설정 함수
def set_coincell_mode(enabled):
    global _coincell_mode
    _coincell_mode = enabled

# L236-238: 마이크로 단위 판별
def is_micro_unit(raw_file_path):
    return ('PNE21' in raw_file_path) or ('PNE22' in raw_file_path) or _coincell_mode
```

- 코인셀 실험 시 전류/용량 단위가 μA/μAh (마이크로암페어/마이크로암페어시)
- `chk_coincell_cyc` 체크박스로 활성화 → 데이터 로딩 시 1000으로 나눠 mA/mAh로 변환

---

#### (8) 프로필 분석 병렬 로딩 (사이클 외)

프로필 확인 버튼들(step/rate/chg/dchg)도 병렬 로딩 적용:

| 메서드 | 대상 |
|--------|------|
| `_load_all_step_data_parallel()` L10016-10089 | 스텝 프로필 |
| `_load_all_profile_data_parallel()` L10090-10181 | rate/chg/dchg/continue 프로필 |

---

### 2.2 기능 상세 로직

#### 탭 구조

사이클데이터 탭(`CycTab`)은 크게 **좌측 설정 영역**과 **우측 그래프 영역**으로 나뉨:

```
┌─ CycTab ─────────────────────────────────────────────────┐
│ ┌─ 좌측 설정 (470px) ──────┐ ┌─ 우측 그래프 (1350px) ─┐ │
│ │ [경로 설정/용량 설정]     │ │                         │ │
│ │ ┌─ tabWidget_2 ────────┐ │ │  cycle_tab (결과 탭)    │ │
│ │ │ Tab5: 사이클 분석     │ │ │                         │ │
│ │ │ Tab6: 프로필 분석     │ │ │  - 2×3 subplot 그래프   │ │
│ │ └──────────────────────┘ │ │  - 채널 토글 버튼       │ │
│ └──────────────────────────┘ └─────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

#### 설정 영역 위젯

| 위젯 | 용도 | 기본값 |
|------|------|--------|
| `chk_cyclepath` | 경로 파일(.txt) 사용 여부 | 체크됨 |
| `chk_ectpath` | ECT 데이터 경로 사용 | 체크 안 됨 |
| `stepnum_2` | 직접 경로 입력 (여러 줄) | 빈 칸 |
| `inicaprate` | C-rate 기준 용량 산정 | 선택됨 |
| `ratetext` | C-rate 값 입력 | — |
| `inicaptype` | 고정 용량(mAh) 기준 | 미선택 |
| `capacitytext` | 최소 용량 입력 (mAh) | — |
| `tcyclerng` | 사이클 X축 범위 | — |
| `tcyclerngyhl` / `tcyclerngyll` | Y축 상한/하한 | — |
| `dcirscale` | DCIR 스케일 | — |
| `dcirchk` / `pulsedcir` / `mkdcir` | DCIR 계산 방식 선택 | — |

#### 버튼별 기능

**Tab5 - 사이클 분석 버튼들**:

| 버튼 | 메서드 | 기능 | 차트 구성 |
|------|--------|------|----------|
| 개별 사이클 | `indiv_cyc_confirm_button()` | 각 폴더별 개별 그래프 생성 | 폴더당 1개 탭, 2×3 서브플롯 |
| 통합 사이클 | `overall_cyc_confirm_button()` | 모든 샘플을 1개 그래프에 | 전체 1개 탭, 2×3 서브플롯 |
| 연결 사이클 | `link_cyc_confirm_button()` | 여러 LOT의 사이클 연결 | 전체 1개 탭, 2×3 서브플롯 |
| 연결(개별) | `link_cyc_indiv_confirm_button()` | CSV 파일 기반 개별 연결 | 파일당 1개 탭 |
| 연결(통합) | `link_cyc_overall_confirm_button()` | CSV 파일 기반 통합 연결 | 전체 1개 탭 |
| 인증 사이클 | `app_cyc_confirm_button()` | Excel 인증 데이터 분석 | 전체 1개 탭, 1개 서브플롯 |

**Tab6 - 프로필 분석 버튼들**:

| 버튼 | 메서드 | 기능 |
|------|--------|------|
| 스텝 확인 | `step_confirm_button()` | 스텝 충/방전 프로필 |
| 율별 확인 | `rate_confirm_button()` | C-rate별 충전 프로필 |
| 충전 확인 | `chg_confirm_button()` | 충전 프로필 + dQ/dV |
| 방전 확인 | `dchg_confirm_button()` | 방전 프로필 + dQ/dV |
| 연속 확인 | `continue_confirm_button()` | 연속 사이클 프로필 |
| DCIR 확인 | `dcir_confirm_button()` | DCIR 측정 데이터 |

#### 2×3 서브플롯 구성 (사이클 분석)

```
┌────────────────────┬────────────────────┬────────────────────┐
│ ax1                │ ax2                │ ax3                │
│ 방전용량비          │ 방전/충전 효율      │ 온도 (℃)           │
│ Dchg Capacity Ratio│ Dchg/Chg Efficiency│ Temperature        │
├────────────────────┼────────────────────┼────────────────────┤
│ ax4                │ ax5                │ ax6                │
│ DC-IR (mΩ)         │ 충전/방전 효율      │ 평균/Rest 전압      │
│ 또는 RSS/1s DCIR   │ Chg/Dchg Efficiency│ Avg/Rest Voltage   │
└────────────────────┴────────────────────┴────────────────────┘
```

#### 데이터 로딩 흐름 (사이클 분석)

```
[버튼 클릭]
  │
  ├─ cyc_ini_set() → 설정값 읽기 (C-rate, 용량, X/Y축 범위 등)
  ├─ pne_path_setting() → 경로 파일 or 직접 경로 or 폴더 선택
  ├─ _load_all_cycle_data_parallel() → 병렬 데이터 로딩
  │   ├─ ThreadPoolExecutor(max_workers=4)
  │   └─ _load_cycle_data_task() × N개
  │       ├─ check_cycler() → PNE/Toyo 구분
  │       ├─ [PNE] pne_cycle_data() → SaveEndData.csv 처리
  │       └─ [Toyo] toyo_cycle_data() → CSV 처리
  │
  ├─ [각 폴더 루프] graph_output_cycle() → 6개 서브플롯에 데이터 그리기
  │   └─ artists, color 반환 → channel_map에 저장
  │
  └─ _finalize_cycle_tab() → 탭에 그래프 + 채널 토글 버튼 추가
```

#### `pne_path_setting()` — 경로 설정 분기

```
경로 설정 시작
  │
  ├─ [chk_cyclepath 체크됨]
  │   ├─ 파일 선택 다이얼로그 열기
  │   ├─ 탭 구분 텍스트 파일 읽기
  │   │   └─ 형식: "이름<TAB>경로" (마지막 탭 필드가 경로)
  │   └─ all_data_folder, all_data_name 반환
  │
  ├─ [stepnum_2에 텍스트 있음]
  │   └─ 텍스트 박스의 줄별로 경로 추출
  │
  └─ [그 외]
      └─ multi_askopendirnames() → 폴더 선택 다이얼로그 반복
```

#### `toyo_cycle_data()` — Toyo 사이클 데이터 처리 핵심 로직

1. **최소 용량 산정**: 첫 사이클의 전류값과 C-rate로 계산
2. **CSV 로딩**: `toyo_cycle_import()` → 기본 Toyo CSV 형식 파싱
3. **연속 동일 Condition 병합**: 같은 충/방전 상태가 연속되면 하나로 합침
   ```python
   # 핵심 로직: 연속된 같은 조건(충전-충전, 방전-방전)을 하나로 병합
   cond_series = Cycleraw["Condition"]
   merge_group = ((cond_series != cond_series.shift()) | 
                  (~cond_series.isin([1, 2]))).cumsum()
   Cycleraw = Cycleraw.groupby(merge_group).apply(merge_rows)
   ```
4. **충전 용량 추출**: `Condition==1` (충전) & 용량 > 최소값
5. **방전 용량/온도/에너지/평균전압 추출**: `Condition==2` (방전)
6. **DCIR 추출**: 짧은 시간 방전 펄스 데이터
7. **용량비 계산**: `Dchg / maxDchg` (최대 방전 대비 비율)
8. **효율 계산**: `Eff = Dchg / Chg`, `Eff2 = Chg / Dchg`

#### `pne_cycle_data()` — PNE 사이클 데이터 처리

1. **CSV 로딩**: `SaveEndData.csv` 파일 (PNE 고유 형식)
2. **컬럼 매핑**: 인덱스 기반 (27=사이클, 2=조건, 10=충전용량, 11=방전용량 등)
3. **마이크로 단위 변환**: PNE21/22 또는 코인셀 → `/1000`
4. **DCIR 3가지 계산 방식**:
   - `dcirchk`: 기본 연속 DCIR (10s 펄스)
   - `mkdcir`: RSS DCIR (특정 스텝 조건 기반, 충전 중 펄스)
   - `pulsedcir`: SOC5/50 10s 펄스 DCIR

---

### 2.3 코드 설명 (파이썬 기초 관점)

#### ThreadPoolExecutor (병렬 처리)

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=4) as executor:
    # 각 작업을 별도 스레드에서 동시 실행
    futures = {executor.submit(self._load_cycle_data_task, task): task 
               for task in tasks}
    
    # 완료되는 순서대로 결과 수집
    for future in as_completed(futures):
        result = future.result()
```

- **`ThreadPoolExecutor`**: "일손 4명(max_workers=4)으로 작업 분담" 하는 매니저
- **`executor.submit(함수, 인자)`**: 빈 일손에게 작업을 맡기는 것
- **`as_completed(futures)`**: 먼저 끝난 작업부터 결과를 받음 (순서 무관)
- **비유**: 4개의 CSV 파일을 1명이 순서대로 읽으면 40초, 4명이 동시에 읽으면 약 10초

#### Signal-Slot 연결 (버튼 → 함수)

```python
self.indiv_cycle.clicked.connect(self.indiv_cyc_confirm_button)
```
- `self.indiv_cycle`: "개별 사이클" 버튼 객체
- `.clicked`: 버튼을 클릭했을 때 발생하는 신호
- `.connect(함수)`: 이 신호가 발생하면 `indiv_cyc_confirm_button` 함수 실행
- **비유**: "초인종(클릭)이 울리면(신호), 문을 열어라(함수 실행)"

#### matplotlib 서브플롯

```python
fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(nrows=2, ncols=3, figsize=(14, 8))
```
- **`fig`**: 전체 그림(도화지)
- **`ax1~ax6`**: 6개 영역(2행×3열). 각 영역에 독립적인 그래프를 그림
- **`figsize=(14, 8)`**: 도화지 크기 (가로 14인치, 세로 8인치)

#### FigureCanvas (그래프 → PyQt6 위젯)

```python
canvas = FigureCanvas(fig)
toolbar = NavigationToolbar(canvas, None)
tab_layout.addWidget(toolbar)
tab_layout.addWidget(canvas)
```
- **`FigureCanvas`**: matplotlib 그래프를 PyQt6 위젯으로 변환하는 다리 역할
- **`NavigationToolbar`**: 확대/축소/저장 등의 도구 모음 (네비게이션 바)
- **`tab_layout.addWidget()`**: 탭 안에 위젯을 위에서 아래로 순서대로 배치

#### 딕셔너리 기반 결과 저장

```python
results = {}
results[(folder_idx, subfolder_idx)] = (folder_path, cyctemp)
# 나중에 사용:
if (i, sub_idx) not in loaded_data:
    continue
folder_path, cyctemp = loaded_data[(i, sub_idx)]
```
- **키**: `(폴더 번호, 서브폴더 번호)` 의 튜플 → 유일한 식별자
- **값**: `(경로, 데이터)` 의 튜플
- 병렬 로딩은 순서가 랜덤이므로, 키-값 딕셔너리로 정확한 위치의 데이터를 찾음

#### pandas `.apply()` 와 `.groupby()`

```python
# .apply(): 각 행에 함수를 적용
toyo_data["day"] = toyo_data['testname'].apply(self.split_value0)

# .groupby(): 같은 그룹끼리 묶어서 처리
Cycleraw.groupby(merge_group).apply(merge_rows)
```
- `.apply(함수)`: 엑셀의 "각 셀에 수식 적용"과 같은 개념
- `.groupby(기준)`: 엑셀의 "피벗테이블"처럼 같은 값끼리 묶음

#### 채널 표시/숨기기 (set_visible)

```python
# 그래프 요소의 표시 여부 전환
for artist in channel_map[channel_name]['artists']:
    artist.set_visible(True)   # 보이기
    artist.set_visible(False)  # 숨기기
canvas.draw_idle()  # 화면 갱신
```
- `artist`: matplotlib에서 점, 선, 텍스트 등 화면에 그려지는 모든 요소
- `set_visible()`: 요소를 지우지 않고 보이기/숨기기만 전환 → 매우 빠름
- `draw_idle()`: 다음 프레임에서 화면을 다시 그림

---

### 2.4 성능 개선 가능 부분

#### (1) GUI 프리징 — 메인 스레드 블로킹

**현재 문제**: 데이터 로딩은 `ThreadPoolExecutor`로 병렬화했지만, 그래프 생성/렌더링은 여전히 **메인 스레드(UI 스레드)**에서 실행 → 많은 채널이 있으면 그래프 생성 중 UI 멈춤

```python
# 현재: 버튼 클릭 → 메인 스레드에서 모든 처리
def indiv_cyc_confirm_button(self):
    loaded_data = self._load_all_cycle_data_parallel(...)  # ← 병렬 OK
    for i, cyclefolder in enumerate(all_data_folder):       # ← 메인 스레드에서 루프
        graph_output_cycle(...)                              # ← UI 블로킹!
```

**개선안**: `QThread`/`QRunnable`을 사용하여 그래프 생성도 백그라운드에서 처리하고, `pyqtSignal`로 완료 시 UI 업데이트

#### (2) 대규모 데이터 범례 오버플로우

**현재**: `LEGEND_THRESHOLD = 15` 이상이면 컬러바로 전환하는 로직이 있지만, 사이클 분석(`overall`)에서는 적용되지 않음

**개선안**: `overall_cyc_confirm_button()`에도 `_setup_legend()` 적용하여, 채널이 많을 때 자동으로 컬러바 전환

#### (3) 메모리 관리 — Figure 누적

```python
# 현재: plt.close()가 일부 경로에서 누락될 수 있음
fig, (...) = plt.subplots(...)
# ... 처리 중 예외 발생 시 fig가 닫히지 않음
```

**개선안**: `try-finally` 패턴으로 fig 생성/닫기를 보장
```python
fig, axes = plt.subplots(...)
try:
    # 처리 로직
finally:
    plt.close(fig)  # 항상 닫기
```

#### (4) global writer 잔존

사이클 분석 버튼(`indiv_cyc_confirm_button`, `overall_cyc_confirm_button`, `link_cyc_confirm_button`)에서 여전히 `global writer` 사용:

```python
def indiv_cyc_confirm_button(self):
    global writer           # ← 전역 변수 사용 중
    ...
```

프로필 분석 버튼들(`step_confirm_button`, `rate_confirm_button` 등)은 이미 `_setup_file_writer()`로 로컬화됨. 사이클 분석 버튼들도 동일하게 적용 가능.

#### (5) 중복 코드 — 사이클 분석 버튼 3종

`indiv_cyc_confirm_button`, `overall_cyc_confirm_button`, `link_cyc_confirm_button` 세 메서드의 코드 구조가 약 70% 유사:

| 공통 부분 | 내용 |
|-----------|------|
| 초기화 | `cyc_ini_set()`, `pne_path_setting()`, 파일 저장 설정 |
| 데이터 로딩 | `_load_all_cycle_data_parallel()` |
| 루프 구조 | `for i, cyclefolder → for sub_idx, FolderBase` |
| 그래프 출력 | `graph_output_cycle()` |
| 데이터 저장 | `output_data()` 호출 패턴 |
| 탭 마무리 | `_finalize_cycle_tab()` |

**개선안**: 공통 로직을 하나의 메서드로 추출하고, 차이점(개별/통합/연결)만 파라미터로 분기

#### (6) 색상 인덱스 관리

```python
# 현재: colorno가 각 메서드에서 다르게 관리됨
colorno = colorno % len(THEME['PALETTE']) + 1  # overall
colorno = colorno + 1                          # indiv
```

**개선안**: 색상 인덱스 관리를 일관성 있게 통일

#### (7) 파일 저장 다이얼로그 타이밍

```python
# 현재: 데이터 로딩 전에 저장 다이얼로그 표시
save_file_name = filedialog.asksaveasfilename(...)
# ... 데이터 처리 (오래 걸림)
# ... 처리 완료 후 저장
writer.close()
```

**문제**: 파일명을 먼저 정하고 나서 데이터 처리를 시작 → 처리 중 오류 발생 시 빈 파일이 남을 수 있음  
**개선안**: 데이터 처리 완료 후 저장 다이얼로그 표시하거나, 임시 파일에 먼저 쓰고 나중에 이동

---

## 부록: 주요 메서드 위치 맵

### 현황 탭 관련

| 메서드 | DataTool.py 위치 | Origin 위치 |
|--------|------------------|-------------|
| UI 생성 | L2876-3111 | L2048-2283 |
| 이벤트 연결 | L9191-9193 | L8127-8129 |
| `toyo_base_data_make()` | L12739-12786 | L10387-10423 |
| `toyo_data_make()` | L12787-12789 | L10425-10429 |
| `toyo_table_make()` | L12790-12839 | L10430-10473 |
| `pne_data_make()` | L12840-12873 | L10474-10516 |
| `pne_table_make()` | L12874-12960 | L10517-10603 |
| `table_reset()` | L12961-12962 | L10604-10606 |
| `change_drive()` | L12963-12971 | L10607-10614 |
| `tb_cycler_combobox()` | L12975-13023 | L10618-10666 |
| `tb_room_combobox()` | L13024-13043 | L10667-10686 |
| `tb_info_combobox()` | L13044-13045 | L10687-10689 |

### 사이클데이터 탭 관련

| 메서드 | DataTool.py 위치 | Origin 위치 | 변경 여부 |
|--------|------------------|-------------|----------|
| UI 생성 | L3112-3827 | L2284-2977 | 위젯 추가 |
| 이벤트 연결 | L9206-9243 | L8142-8175 | 버튼 추가 |
| **THEME 상수** | L46-76 | N/A | **신규** |
| **set_coincell_mode()** | L231-234 | N/A | **신규** |
| **is_micro_unit()** | L236-238 | N/A | **신규** |
| **graph_output_cycle()** | L315-340 | L223-245 | **반환값 추가** |
| **_init_confirm_button()** | L9377-9402 | N/A | **신규** |
| **_setup_file_writer()** | L9405-9440 | N/A | **신규** |
| **_create_cycle_channel_control()** | L9440-9895 | N/A | **신규 (450줄)** |
| **_finalize_cycle_tab()** | L9896-9920 | N/A | **신규** |
| **_setup_legend()** | L9932-9950+ | N/A | **신규** |
| **_load_all_step_data_parallel()** | L10016-10089 | N/A | **신규** |
| **_load_all_profile_data_parallel()** | L10090-10181 | N/A | **신규** |
| **_load_cycle_data_task()** | L10167-10180 | N/A | **신규** |
| **_load_all_cycle_data_parallel()** | L10182-10213 | N/A | **신규** |
| `cyc_ini_set()` | L10215-10227 | 해당 위치 | 코인셀 모드 추가 |
| `tab_delete()` | L10246-10248 | 해당 위치 | 동일 |
| `pne_path_setting()` | L10260-10297 | 해당 위치 | **가변 컬럼 파싱** |
| `cycle_tab_reset_confirm_button()` | L10304-10306 | 해당 위치 | 동일 |
| `app_cyc_confirm_button()` | L10308-10403 | 해당 위치 | THEME 적용 |
| `indiv_cyc_confirm_button()` | L10405-10576 | L8423-8540 | **대규모 개편** |
| `overall_cyc_confirm_button()` | L10577-10778 | L8541-8661 | **대규모 개편** |
| `link_cyc_confirm_button()` | L10779-10956 | L8662-8780 | **대규모 개편** |
| `link_cyc_indiv_confirm_button()` | L10957-11148 | N/A | **신규** |
| `link_cyc_overall_confirm_button()` | L11149-11353 | N/A | **신규** |
| `step_confirm_button()` | L11354-11513 | 해당 위치 | **병렬화+리팩토링** |
| `rate_confirm_button()` | L11514-11726 | 해당 위치 | **병렬화+리팩토링** |
| `chg_confirm_button()` | L11727-11960 | 해당 위치 | **병렬화+리팩토링** |
| `dchg_confirm_button()` | L11961-12190 | 해당 위치 | **병렬화+리팩토링** |
| `continue_confirm_button()` | L12191-12195 | 해당 위치 | 라우터 구조 변경 |
| `dcir_confirm_button()` | L12476-12631 | 해당 위치 | 소폭 변경 |
