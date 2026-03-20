# 코드 리뷰 & 학습: 사이클데이터 탭 전체 구조 분석

> **파일**: `DataTool_dev/DataTool_optRCD_proto_.py`
> **작성일**: 2026-03-19
> **목적**: 사이클데이터 탭의 전체 동작 흐름과 핵심 함수 구조 이해

---

## 1. 사이클데이터 탭이란?

충방전기(Toyo, PNE)에서 수집한 배터리 충방전 사이클 데이터를 불러와 **6개 그래프**로 시각화하고 **엑셀로 저장**하는 탭이다.

```
사용자 → 폴더/파일 선택 → 데이터 읽기(병렬) → 가공 → 그래프 생성 → 탭에 표시
```

---

## 2. 탭 구성 요소 (UI)

```
사이클데이터 탭 (CycTab)
├── [좌측 패널] 설정 영역
│   ├── 입력 방식 선택
│   │   ├── chk_cyclepath   : 지정Path 파일 사용 여부 체크박스
│   │   ├── chk_link_cycle  : 연결 모드 (여러 폴더를 하나로 이어붙임)
│   │   └── cycle_path_table: 경로 직접 입력 테이블 (이름/경로/채널/용량)
│   ├── 용량 설정 그룹 (capacitygroup)
│   │   ├── inicaprate      : 파일명에서 mAh 자동 추출 라디오버튼
│   │   ├── inicaptype      : 직접 입력 라디오버튼
│   │   ├── capacitytext    : 용량 입력창 (mAh)
│   │   └── ratetext        : 첫 사이클 C-rate 입력창 (기본 0.2)
│   ├── 그래프 범위 설정
│   │   ├── tcyclerng       : X축 범위 (사이클 수)
│   │   ├── tcyclerngyhl    : Y축 상한 (방전용량 비율)
│   │   ├── tcyclerngyll    : Y축 하한
│   │   └── dcirscale       : DC-IR 스케일
│   ├── 옵션 체크박스
│   │   ├── dcirchk         : 기본 DCIR 표시 여부
│   │   ├── dcirchk_2       : DCIR 방식 선택
│   │   ├── mkdcir          : 1s pulse/RSS DCIR 계산
│   │   ├── saveok          : 엑셀 저장 여부
│   │   └── figsaveok       : 그림 파일 저장 여부
│   ├── 표시 방식
│   │   ├── radio_indiv     : 개별 모드 (폴더별 별도 색상, 탭)
│   │   └── (통합 모드)     : 같은 파일에서 읽은 항목을 하나의 탭으로
│   └── 버튼
│       ├── cycle_confirm   : 실행 버튼 → unified_cyc_confirm_button()
│       └── cycle_tab_reset : 생성된 탭 초기화 → cycle_tab_reset_confirm_button()
└── [우측] cycle_tab (QTabWidget)
    └── 탭 0, 1, 2, ... : 각 그래프가 들어가는 탭
```

---

## 3. 전체 처리 흐름

```
[사용자: 실행 버튼 클릭]
         │
         ▼
unified_cyc_confirm_button()         ← 메인 진입점 (line 11195)
         │
         ├─① cyc_ini_set()           ← UI에서 파라미터 수집
         │
         ├─② _parse_cycle_input()    ← 입력 방식 판단 + CycleGroup 목록 생성
         │
         ├─③ (엑셀 파일이면)         ← 신뢰성 Excel 데이터 처리 (별도 경로)
         │
         └─④ (폴더면)
              │
              ├─ _load_all_cycle_data_parallel()  ← 병렬 데이터 로딩
              │       │
              │       └─ _load_cycle_data_task()  ← 채널별 1개 작업 단위
              │               │
              │               ├─ pne_cycle_data()   (PNE 장비)
              │               └─ toyo_cycle_data()  (Toyo 장비)
              │
              ├─ graph_output_cycle()              ← 6개 그래프 그리기
              │
              ├─ _finalize_cycle_tab()             ← 탭 위젯에 그래프 추가
              │
              └─ _save_cycle_excel_data()          ← (선택) 엑셀 저장
```

---

## 4. 핵심 함수 상세 분석

### 4-1. `cyc_ini_set()` — UI 설정값 수집 (line 11661)

```python
def cyc_ini_set(self):
    set_coincell_mode(self.chk_coincell_cyc.isChecked())  # 코인셀 모드 설정
    firstCrate = float(self.ratetext.text())              # 첫 사이클 C-rate
    if self.inicaprate.isChecked():
        mincapacity = 0   # 0이면 나중에 자동 산정
    elif self.inicaptype.isChecked():
        mincapacity = float(self.capacitytext.text())     # 직접 입력값 사용
    xscale    = int(self.tcyclerng.text())      # X축 최대 사이클 수
    ylimithigh = float(self.tcyclerngyhl.text()) # Y축 상한
    ylimitlow  = float(self.tcyclerngyll.text()) # Y축 하한
    irscale    = float(self.dcirscale.text())    # DC-IR 스케일 배율
    return firstCrate, mincapacity, xscale, ylimithigh, ylimitlow, irscale
```

**요점**: UI 위젯에서 값을 읽어 숫자형으로 변환 후 반환. `mincapacity=0`이 반환되면 이후 함수에서 자동 계산.

---

### 4-2. `check_cycler()` — 충방전기 장비 판별 (line 354)

```python
def check_cycler(raw_file_path):
    # 폴더 안에 "Pattern" 서브폴더가 있으면 PNE 장비, 없으면 Toyo 장비
    cycler = os.path.isdir(raw_file_path + "\\Pattern")
    return cycler   # True = PNE, False = Toyo
```

**요점**: PNE 충방전기는 데이터 폴더 안에 `Pattern` 이라는 서브폴더를 만든다. 이 폴더 유무로 장비를 구분.

---

### 4-3. `toyo_min_cap()` — 최소 용량(기준 용량) 산정 (line 884)

```python
def toyo_min_cap(raw_file_path, mincapacity, inirate):
    if mincapacity == 0:             # 자동 산정 모드
        if "mAh" in raw_file_path:   # 폴더명에 "mAh" 포함 시
            mincap = name_capacity(raw_file_path)  # 이름에서 숫자 추출
        else:
            # 첫 사이클 데이터에서 최대 전류 ÷ C-rate로 용량 추정
            inicapraw = toyo_read_csv(raw_file_path, 1)
            mincap = int(round(inicapraw["Current[mA]"].max() / inirate))
    else:
        mincap = mincapacity         # 직접 입력값 그대로 사용
    return mincap
```

**요점**: 기준 용량(정격 용량)은 이후 방전 용량 비율을 계산하는 기준이 된다. 폴더명에서 자동 추출하거나, 첫 사이클 전류로 역산한다.

> **공식**: 용량 = 최대 전류 ÷ C-rate
> 예) 첫 사이클에 0.2C로 충전하면 → 전류 200mA ÷ 0.2 = 1000mAh

---

### 4-4. `toyo_cycle_data()` — Toyo 사이클 데이터 처리 (line 898)

**입력**: 채널 폴더 경로, 기준 용량, C-rate, DCIR 체크
**출력**: `[mincapacity, df]`  (df.NewData: 사이클별 요약 DataFrame)

#### 처리 단계:

```
① toyo_min_cap()     → 기준 용량 확정
② toyo_cycle_import() → CSV 파일 읽기
③ 사이클 재정의     → 방전 시작 첫 행 보정
④ 연속 행 병합     → merge_rows() 내부 함수
⑤ 충전/방전 분리   → chgdata, Dchgdata 필터링
⑥ DCIR 계산        → (선택) 프로파일 파일에서 전압차/전류로 계산
⑦ 효율 계산        → Eff = 방전용량 / 충전용량
⑧ 최종 DataFrame 생성 → df.NewData
```

#### 사이클 재정의 로직 (방전 시작 보정):

```python
# 데이터가 '방전'(Condition=2)으로 시작하고, 첫 번째 사이클 번호가 1이면
if Cycleraw.loc[0, "Condition"] == 2 and len(Cycleraw.index) > 2:
    if Cycleraw.loc[1, "TotlCycle"] == 1:
        # 방전 행들의 사이클 번호를 1씩 줄임 (0번 방전은 제거)
        Cycleraw.loc[Cycleraw["Condition"] == 2, "TotlCycle"] -= 1
        Cycleraw = Cycleraw.drop(0, axis=0)
```

> **왜?**: Toyo 장비는 간혹 사이클 0번(포메이션 방전)부터 기록한다. 이를 정규 사이클 1번이 시작되기 전의 불완전 데이터로 보고 제거하거나 사이클 번호를 재정렬한다.

#### 연속 행 병합 로직:

```python
# 충방전 Condition이 연속으로 동일한 경우 하나의 행으로 묶음
cond_series = Cycleraw["Condition"]
merge_group = ((cond_series != cond_series.shift()) |
               (~cond_series.isin([1, 2]))).cumsum()

def merge_rows(group):
    if len(group) == 1:
        return group.iloc[0]        # 단일 행이면 그대로
    result = group.iloc[-1].copy()  # 마지막 행 기준
    if cond == 1:  # 충전
        result["Cap[mAh]"] = group["Cap[mAh]"].sum()  # 용량 합산
    elif cond == 2:  # 방전
        result["Cap[mAh]"]   = group["Cap[mAh]"].sum()
        result["Pow[mWh]"]   = group["Pow[mWh]"].sum()
        result["AveVolt[V]"] = result["Pow[mWh]"] / result["Cap[mAh]"]  # 재계산
    return result
```

> **왜?**: 한 사이클의 충전이 여러 스텝(CC/CV 등)으로 분리 기록된 경우 하나로 합쳐야 한 사이클의 총 용량을 얻을 수 있다.

#### 최종 출력 DataFrame (`df.NewData`):

| 컬럼명 | 의미 | 단위 |
|--------|------|------|
| `Dchg` | 방전 용량 비율 | 기준 용량 대비 (0~1) |
| `Chg` | 충전 용량 비율 | 기준 용량 대비 |
| `Eff` | 충방효율 (방전/충전) | 0~1 |
| `Eff2` | 방충효율 (다음 충전/방전) | 0~1 |
| `RndV` | Rest End Voltage (충전 전 휴지 전압) | V |
| `AvgV` | 방전 평균 전압 | V |
| `Temp` | 최고 온도 | ℃ |
| `DchgEng` | 방전 에너지 | mWh |
| `OriCyc` | 원본 사이클 번호 | - |
| `dcir` | DC-IR | mΩ |

---

### 4-5. `pne_cycle_data()` — PNE 사이클 데이터 처리 (line 2060)

**Toyo와 차이점**:

| 항목 | Toyo | PNE |
|------|------|-----|
| 데이터 파일 | CSV (사이클 요약) | `Restore\SaveEndData.csv` |
| 데이터 구조 | 1행 = 1스텝 결과 | 1행 = 1스텝 (열 번호로 접근) |
| 용량 단위 | mAh | μAh (PNE21/22의 경우 ÷1000) |
| DCIR 방식 | 프로파일 파일 별도 읽기 | SaveEndData 내 imp 컬럼 활용 |
| 사이클 병합 | 필요 (연속 스텝 병합) | pivot_table로 사이클별 집계 |

**DCIR 3가지 모드**:

```
chkir=True  → 기본 DCIR: volmax > 4.1V 조건의 imp 컬럼 사용
mkdcir=True → 1s pulse DCIR + RSS DCIR:
              dcirtemp1 = RSS CCV (SOC 종료 스텝)
              dcirtemp2 = 1s pulse CCV (steptime == 100)
              dcirtemp3 = REST OCV (휴지 전압)
              RSS = |rest전압 - CCV| / 전류
              DCIR1s = |pulse전압 - CCV| / 전류차
else        → SOC5,50 기반 10s pulse DCIR (steptime ≤ 6000)
```

---

### 4-6. `_load_cycle_data_task()` / `_load_all_cycle_data_parallel()` — 병렬 로딩 (line 10882, 10898)

```python
# 단일 작업 단위 (스레드 1개가 처리)
def _load_cycle_data_task(self, task_info):
    folder_path, mincapacity, firstCrate, dcirchk, dcirchk_2, mkdcir,
    is_pne, folder_idx, subfolder_idx = task_info
    if is_pne:
        cyctemp = pne_cycle_data(...)   # PNE 처리
    else:
        cyctemp = toyo_cycle_data(...)  # Toyo 처리
    return (folder_idx, subfolder_idx, folder_path, cyctemp)

# 병렬 실행 관리자
def _load_all_cycle_data_parallel(self, all_data_folder, ...):
    tasks = []
    for i, cyclefolder in enumerate(all_data_folder):
        subfolder = [f.path for f in os.scandir(cyclefolder) if f.is_dir()]
        is_pne = check_cycler(cyclefolder)
        for j, folder_path in enumerate(subfolder):
            if "Pattern" not in folder_path:   # Pattern 폴더 제외
                tasks.append((folder_path, ..., i, j))

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(self._load_cycle_data_task, task): task
                   for task in tasks}
        for future in as_completed(futures):
            result = future.result()
            # 완료된 것부터 results 딕셔너리에 저장
            results[(folder_idx, subfolder_idx)] = (folder_path, cyctemp)
            # 진행률 업데이트 (데이터 로딩 = 0~50%)
            self.progressBar.setValue(int(completed / total_tasks * 50))
    return results, subfolder_map
```

> **핵심 개념 — `ThreadPoolExecutor`**:
> 여러 채널 폴더를 **동시에** 처리한다. 예를 들어 채널이 8개라면 4개씩 묶어서 두 번에 처리한다. 한 채널씩 순서대로 처리하는 것보다 4배 빠르다.
>
> - `executor.submit(함수, 인자)` → 스레드에 작업 제출, 즉시 `Future` 객체 반환
> - `as_completed(futures)` → 완료되는 순서대로 결과 수거 (빠른 것부터)

---

### 4-7. `graph_output_cycle()` — 6개 그래프 한 번에 그리기 (line 449)

```python
def graph_output_cycle(df, xscale, ylimitlow, ylimithigh, irscale,
                       temp_lgnd, colorno, graphcolor, dcir,
                       ax1, ax2, ax3, ax4, ax5, ax6):
    color = graphcolor[colorno % len(THEME['PALETTE'])]   # 색상 순환
    # ax1: 방전 용량 비율 (Discharge Capacity Ratio)
    graph_cycle(df.NewData.index, df.NewData.Dchg, ax1, ...)
    # ax2: 충방 효율 (Discharge/Charge Efficiency)
    graph_cycle(df.NewData.index, df.NewData.Eff,  ax2, ...)
    # ax3: 온도 (Temperature)
    graph_cycle(df.NewData.index, df.NewData.Temp, ax3, ...)
    # ax4: DC-IR (조건에 따라 1s pulse 또는 RSS)
    if dcir.isChecked() and hasattr(df.NewData, "dcir2"):
        graph_cycle_empty(...)  # 빈 원 = DCIR1s
        graph_cycle(...)        # 채운 원 = RSS
    else:
        graph_cycle(...)        # 기본 DCIR
    # ax5: 방충 효율 (Charge/Discharge Efficiency)
    graph_cycle(df.NewData.index, df.NewData.Eff2, ax5, ...)
    # ax6: Rest End Voltage + 평균 전압 (2가지 겹쳐 표시)
    graph_cycle(df.NewData.index, df.NewData.RndV, ax6, ...)      # 채운 원 = Rest V
    graph_cycle_empty(df.NewData.index, df.NewData.AvgV, ax6, ...) # 빈 원 = Avg V
    return artists, color
```

**그래프 배치 (2행 3열)**:

```
┌──────────────┬──────────────┬──────────────┐
│ ax1          │ ax2          │ ax3          │
│ 방전 용량 비율│ 충방 효율     │ 온도         │
├──────────────┼──────────────┼──────────────┤
│ ax4          │ ax5          │ ax6          │
│ DC-IR        │ 방충 효율     │ 전압 (휴지+평균)│
└──────────────┴──────────────┴──────────────┘
```

---

### 4-8. `_parse_cycle_input()` — 입력 방식 판단 (line 11049)

세 가지 우선순위로 입력 방식을 결정:

```
우선순위 ①: chk_cyclepath 체크됨
            → 파일 선택 다이얼로그 (.txt/.xlsx/.xls/폴더 경로)

우선순위 ②: 테이블에 데이터 있음 (_has_table_data() == True)
            → 테이블 4열 (이름/경로/채널/용량)에서 읽기

우선순위 ③: 아무것도 없으면
            → 폴더 선택 다이얼로그 (연속 선택 가능)
```

반환값: `list[CycleGroup]`

```python
@dataclass
class CycleGroup:
    name: str               # 범례/탭 표시명
    paths: list             # 데이터 폴더 경로 목록 (연결 시 여러 개)
    path_names: list        # path별 이름 (path 파일에서 읽은 경우)
    is_link: bool           # True면 여러 폴더를 이어붙임
    data_type: str          # 'folder' | 'excel'
    file_idx: int           # 출처 path 파일 번호 (통합 탭 묶기용)
    source_file: str        # 원본 path 파일 경로 (mAh 추출용)
    per_path_channels: list # 채널 필터 [[ch1],[ch2]] (빈=전체)
```

---

### 4-9. `_finalize_cycle_tab()` — 탭에 그래프 추가 (line 10590)

```python
def _finalize_cycle_tab(self, tab, tab_layout, canvas, toolbar, tab_no,
                        channel_map, fig, axes_list, sub_channel_map=None):
    if channel_map:
        # CH 토글 버튼 생성 (클릭 시 채널 제어 팝업 열림)
        toggle_btn = self._create_cycle_channel_control(
            channel_map, canvas, fig, axes_list, ...)
        # toolbar + toggle_btn 을 한 줄로 배치
        toolbar_row = QHBoxLayout()
        toolbar_row.addWidget(toolbar)
        toolbar_row.addWidget(toggle_btn)
        tab_layout.addLayout(toolbar_row)
    else:
        tab_layout.addWidget(toolbar)
    tab_layout.addWidget(canvas)
    self.cycle_tab.addTab(tab, str(tab_no))  # 탭 추가
    self.cycle_tab.setCurrentWidget(tab)     # 방금 추가한 탭으로 포커스 이동
    plt.tight_layout(...)
```

**CH 버튼 동작**:
툴바 옆 `▶ CH` 버튼을 누르면 채널 제어 팝업이 열린다. 각 채널을 체크/언체크해서 그래프에서 숨기거나 표시할 수 있다. `Lazy Init` 패턴 사용 — 첫 클릭 시에만 팝업 위젯을 생성한다.

---

### 4-10. `_save_cycle_excel_data()` — 엑셀 저장 (line 10940)

```python
def _save_cycle_excel_data(self, nd, writecolno, start_row, headername):
    cyc_head = ["Cycle"]
    _dc = writecolno + 1    # 데이터 열 = 헤더 열 + 1

    # 시트별 저장: "방전용량", "Rest End", "평균 전압", "충방효율", ...
    output_data(nd, "방전용량", writecolno, start_row, "OriCyc", cyc_head)
    output_data(nd, "방전용량", _dc,        start_row, "Dchg",   headername)
    # ... 나머지 항목도 동일 패턴

    # DCIR: 선택된 모드에 따라 시트 분기
    if self.mkdcir.isChecked() and "dcir2" in nd.columns:
        # RSS / DCIR1s / RSS_OCV / RSS_CCV / SOC70 시트들
        output_data(cyctempdcir, "RSS", ...)
        output_data(cyctempdcir2, "DCIR", ...)
        # SOC70 DCIR (있으면)
        if "soc70_dcir" in nd.columns:
            output_data(..., "SOC70_DCIR", ...)
    else:
        output_data(cyctempdcir, "DCIR", ...)
```

**저장 구조**: 컬럼 2개씩 (사이클번호 + 데이터값) 반복 추가. 채널이 여러 개면 옆 열에 순서대로 쌓인다.

---

## 5. 연결 모드 (Link Mode) 특별 처리

`chk_link_cycle` 체크 시 활성화. 여러 폴더의 사이클 데이터를 이어붙여 하나의 채널처럼 취급한다.

```
폴더A (사이클 1~200)  ──┐
폴더B (사이클 1~200)  ──┤  → 사이클 1~400 으로 이어진 1개 선
폴더C (사이클 1~100)  ──┘
```

```python
# 연결 시 인덱스 오프셋 적용
if sub_label not in channel_state:
    channel_state[sub_label] = {'offset': 0, 'last_len': 0}
st = channel_state[sub_label]
writerowno = st['offset'] + st['last_len']           # 이전 폴더 마지막 사이클번호부터 이어서
cyctemp[1].NewData.index = cyctemp[1].NewData.index + writerowno
st['offset'] = writerowno
st['last_len'] = len(cyctemp[1].NewData)
```

---

## 6. 통합 모드 vs 개별 모드

| 항목 | 개별 모드 (`radio_indiv`) | 통합 모드 |
|------|--------------------------|-----------|
| 탭 단위 | 그룹(폴더)마다 별도 탭 | 같은 path 파일에서 온 것은 같은 탭 |
| 색상 | 채널마다 다른 색 | 하나의 채널 = 하나의 색 (범례 구분) |
| 범례 위치 | ax1만 lower left | 각 축마다 위치 지정 |
| 활용 | 폴더 하나 확인 | 여러 셀을 한 화면에 비교 |

---

## 7. 주요 Python 문법 해설

### 7-1. `@dataclass` (line 200)
```python
from dataclasses import dataclass, field

@dataclass
class CycleGroup:
    name: str
    paths: list = field(default_factory=list)  # 기본값을 빈 리스트로
```
> `@dataclass` 데코레이터를 붙이면 `__init__`, `__repr__` 등을 자동으로 만들어준다.
> `field(default_factory=list)` 는 "기본값이 빈 리스트" 라는 뜻. 단순히 `paths: list = []` 로 쓰면 모든 인스턴스가 같은 리스트를 공유하는 버그가 생기기 때문에 반드시 `field(default_factory=...)` 를 사용한다.

### 7-2. `groupby` + `apply` (line 942)
```python
Cycleraw = Cycleraw.groupby(merge_group, group_keys=False).apply(merge_rows, include_groups=False)
```
> 데이터프레임을 `merge_group` 기준으로 묶어서, 각 그룹에 `merge_rows()` 함수를 적용하고 결과를 다시 합친다.
> `include_groups=False` → pandas 2.x에서 그룹 키 컬럼을 함수 인자에서 제외하는 옵션.

### 7-3. `pivot_table` (line 2133)
```python
pivot_data = Cycleraw.pivot_table(
    index="TotlCycle",
    columns="Condition",
    values=["DchgCap", "chgCap", ...],
    aggfunc={"DchgCap": "sum", "Ocv": "min", ...}
)
```
> 엑셀의 피벗 테이블과 같다. 행 = 사이클번호, 열 = Condition(충전=1/방전=2/휴지=3), 값 = 각 집계 결과.
> 예) `pivot_data["DchgCap"][2]` = Condition이 2(방전)인 행들의 DchgCap 합계를 사이클별로.

### 7-4. `ThreadPoolExecutor` (line 10927)
```python
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(함수, 인자): 인자 for 인자 in 작업목록}
    for future in as_completed(futures):
        result = future.result()
```
> 동시에 4개 작업을 실행하는 병렬 처리. `submit()` 으로 작업을 등록하면 즉시 별도 스레드에서 실행된다. `as_completed()` 는 빠른 것부터 결과를 받는 이터레이터.

### 7-5. `OrderedDict` (line 11082)
```python
name_order = OrderedDict()
for row in rows:
    name_order.setdefault(row['name'], []).append(row)
```
> 딕셔너리인데 **삽입 순서를 보장**한다. `.setdefault(키, 기본값)` 은 "키가 없으면 기본값으로 초기화하고 반환, 있으면 기존 값 반환". 같은 이름의 항목들을 순서대로 모으는 용도.

### 7-6. Lazy Init 패턴 (line 9703)
```python
_lazy = {'dialog': None}    # 처음에는 None

def _ensure_dialog():
    if _lazy['dialog'] is not None:
        return _lazy['dialog']          # 이미 있으면 재사용
    _lazy['dialog'] = self._build_channel_dialog(...)  # 처음만 생성
    return _lazy['dialog']
```
> 팝업 다이얼로그를 사용자가 처음 클릭할 때만 생성한다. 클릭하지 않으면 아예 만들지 않아 메모리/성능 절약.
> 딕셔너리 `{'dialog': None}` 을 사용하는 이유: 내부 함수(`_ensure_dialog`)에서 외부 변수를 수정할 때 Python의 클로저 제약을 우회하기 위함.

### 7-7. `@log_perf` 데코레이터 (line 77)
```python
def log_perf(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        _perf_logger.info(f'▶ {func.__qualname__} 시작')
        t0 = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - t0
        _perf_logger.info(f'◀ {func.__qualname__} 완료  [{elapsed:.3f}s]')
        return result
    return wrapper
```
> `@log_perf` 를 함수 위에 붙이면, 그 함수가 언제 시작되고 얼마나 걸렸는지를 콘솔에 자동으로 출력한다. 실제 함수 코드는 수정하지 않아도 된다.

---

## 8. 데이터 흐름 요약 다이어그램

```
[충방전기 원본 데이터]
        │
        ├─ Toyo: 채널 폴더\000001, 000002, ... (CSV 파일들)
        └─ PNE:  채널 폴더\Restore\SaveEndData.csv
                │
                ▼
        [toyo/pne_cycle_data()]
                │
                │  ① CSV 읽기
                │  ② 행 병합 또는 피벗
                │  ③ 충전/방전 분리
                │  ④ 효율/DCIR 계산
                │  ⑤ 용량 비율 정규화 (값 ÷ 기준용량)
                │
                ▼
        [df.NewData] ← 사이클당 1행 요약 DataFrame
        Columns: Dchg, Chg, Eff, Eff2, RndV, AvgV, Temp, DchgEng, dcir, OriCyc
                │
                ▼
        [graph_output_cycle()]
                │
                │  6개 axes에 scatter 그래프 그리기
                │
                ▼
        [_finalize_cycle_tab()]
                │
                │  QTabWidget에 탭 추가
                │  CH 토글 버튼 생성
                │
                ▼
        [사이클데이터 탭 우측 화면에 표시됨]
```

---

## 9. 자주 발생하는 오류 포인트

| 상황 | 원인 | 해결 |
|------|------|------|
| 데이터가 안 나타남 | `Pattern` 폴더가 없는 PNE 폴더를 Toyo로 인식 | 폴더 구조 확인, `check_cycler()` 반환값 확인 |
| 용량이 이상하게 나옴 | `mincapacity` 자동 산정 오류 | `ratetext` 값 확인, 폴더명에 mAh 포함 확인 |
| DCIR가 0만 나옴 | pulse 스텝이 없음 | 충방전 패턴에 DCIR 스텝 포함 여부 확인 |
| 그래프가 연결 안 됨 | `chk_link_cycle` 미체크 상태 | 연결 모드 체크 필요 |
| SOC70 DCIR 없음 | `mkdcir` 모드이지만 pulse 스텝 구조 불일치 | `soc_count` 변수가 6 또는 4인지 확인 |
