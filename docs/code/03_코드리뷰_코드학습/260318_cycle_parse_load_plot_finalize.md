# Cycle 통합 기능 — parse → load → plot → finalize 변수 & 흐름 분석

> 작성일: 2026-03-18
> 대상 파일: `DataTool_dev/DataTool_optRCD_proto_.py`
> 목적: Plan "Cycle 6개 기능 통합" 구현 전 기존 코드 스터디

---

## 0. 공통 초기화 — `cyc_ini_set()`

모든 6개 함수가 제일 먼저 호출함.

| 반환 변수 | 소스 UI | 의미 |
|---|---|---|
| `firstCrate` | `self.ratetext.text()` | 초기 C-rate (float) |
| `mincapacity` | `self.capacitytext.text()` or 0 | 기준 용량 (float, 0이면 path명에서 추출) |
| `xscale` | `self.tcyclerng.text()` | X축 최대 사이클 수 (int, 0=자동) |
| `ylimithigh` | `self.tcyclerngyhl.text()` | Y축 상한 (float) |
| `ylimitlow` | `self.tcyclerngyll.text()` | Y축 하한 (float) |
| `irscale` | `self.dcirscale.text()` | DCIR 축 배율 (float) |

DCIR 모드 판별 UI 위젯:

| UI 위젯 | 타입 | 의미 |
|---|---|---|
| `self.dcirchk` | QRadioButton | PNE 설비 DCIR (SOC100) |
| `self.pulsedcir` | QRadioButton | PNE 10s DCIR (SOC5/50) |
| `self.mkdcir` | QRadioButton | PNE DCIR 다중 SOC |
| `self.dcirchk_2` | QCheckBox | DCIR 고정 해제 |

---

## PHASE 1 — PARSE (`pne_path_setting()`)

**반환**: `[all_data_folder, all_data_name, datafilepath]`

### 입력 방식 분기

```
입력 방식 분기:
  chk_cyclepath.isChecked() → .txt path파일 선택
      ↓ 파싱: tab 구분, 마지막 필드=cyclepath, 나머지=cyclename
      → cycle_path (DataFrame, columns: cyclename, cyclepath)
      → all_data_folder = array(cyclepath)
      → all_data_name  = array(cyclename)
      → datafilepath   = .txt 파일 경로 (문자열)

  stepnum_2.toPlainText() != "" → 직접입력
      → datafilepath   = List[str] (줄별 파싱)
      → all_data_folder= np.array(datafilepath)
      → all_data_name  = []

  else → 폴더 선택 다이얼로그
      → all_data_folder= multi_askopendirnames() 반환 리스트
      → all_data_name  = []
      → datafilepath   = all_data_folder
```

### 반환 변수

| 변수 | 타입 | 설명 |
|---|---|---|
| `all_data_folder` | `np.array` or `list` | 데이터 폴더 경로 목록 |
| `all_data_name` | `np.array` or `[]` | 사이클 이름 목록 (지정Path 시만 존재) |
| `datafilepath` | `str` or `list` | 원본 입력 (용량 추출용) |

> **`link_cyc_indiv/overall_confirm_button`**: `pne_path_setting()` 미사용.
> 대신 `filedialog.askopenfilenames()`로 `.txt` 파일 복수 선택 → 함수 내부에서 `pd.read_csv(sep="\t")`로 직접 파싱.

---

## PHASE 2 — LOAD (`_load_all_cycle_data_parallel()`)

### 시그니처

```python
def _load_all_cycle_data_parallel(self, all_data_folder, mincapacity, firstCrate,
                                   dcirchk, dcirchk_2, mkdcir, max_workers=4)
```

**반환**: `(results, subfolder_map)`

### 내부 흐름

```
for i, cyclefolder in enumerate(all_data_folder):
    subfolder = [f.path for f in os.scandir(cyclefolder) if f.is_dir()]
    subfolder_map[i] = subfolder           # ← 폴더 캐시
    is_pne = check_cycler(cyclefolder)     # PNE/TOYO 판별
    for j, folder_path in enumerate(subfolder):
        if "Pattern" not in folder_path:
            tasks.append((folder_path, mincapacity, firstCrate,
                          dcirchk, dcirchk_2, mkdcir, is_pne, i, j))

ThreadPoolExecutor(max_workers=4)
  → _load_cycle_data_task(task_info)
      is_pne → pne_cycle_data(...)  or  toyo_cycle_data(...)
      returns (folder_idx, subfolder_idx, folder_path, cyctemp)

results[(folder_idx, subfolder_idx)] = (folder_path, cyctemp)
```

### 변수 목록

| 변수 | 타입 | 설명 |
|---|---|---|
| `tasks` | `list[tuple]` | 병렬 작업 목록 |
| `subfolder_map` | `dict{int: [str]}` | `{folder_idx: [subfolder_path, ...]}` |
| `results` (=`loaded_data`) | `dict{(int,int): (str, obj)}` | `{(i,j): (folder_path, cyctemp)}` |
| `cyctemp` | `tuple` | `[mincapacity(float), df_obj]` |
| `cyctemp[1]` | `object` | `.NewData` 속성 보유 |
| `cyctemp[1].NewData` | `pd.DataFrame` | 실제 사이클 데이터 |
| `is_pne` | `bool` | 사이클러 종류 |

### `cyctemp[1].NewData` 컬럼

| 컬럼 | 의미 |
|---|---|
| `index` | 사이클 번호 |
| `Dchg` | 방전용량비 |
| `Eff` | 방전/충전 효율 |
| `Temp` | 온도 |
| `RndV` | Rest End 전압 |
| `AvgV` | 평균 전압 |
| `Eff2` | 충전/방전 효율 |
| `dcir` | DC-IR |
| `dcir2` | DC-IR (mkdcir 모드) |
| `soc70_dcir` | SOC70 DC-IR |
| `soc70_rss_dcir` | SOC70 RSS DC-IR |

> **진행률**: 로딩 완료 시 `progressBar` 0 → 50%

---

## PHASE 3 — PLOT (`graph_output_cycle()`)

### 시그니처

```python
def graph_output_cycle(df, xscale, ylimitlow, ylimithigh, irscale, temp_lgnd,
                       colorno, graphcolor, dcir, ax1, ax2, ax3, ax4, ax5, ax6)
```

**반환**: `(artists, color)`

### axes 배치

```python
fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2, 3, figsize=(14, 8))
```

| axis | 데이터 | Y 범위 |
|---|---|---|
| `ax1` | Discharge Capacity Ratio (`Dchg`) | ylimitlow ~ ylimithigh |
| `ax2` | Discharge/Charge Efficiency (`Eff`) | 0.992 ~ 1.004 |
| `ax3` | Temperature (`Temp`) | 0 ~ 50 |
| `ax4` | DC-IR | 0 ~ 120×irscale |
| `ax5` | Charge/Discharge Efficiency (`Eff2`) | 0.996 ~ 1.008 |
| `ax6` | Average/Rest Voltage (`AvgV` + `RndV`) | 3.00 ~ 4.00 |

> **예외: `app_cyc_confirm_button` (신뢰성)**
> `fig, ((ax1)) = plt.subplots(1, 1)` — **ax1만** 존재
> xlwings로 `.xlsx` 읽어 `df/mincapacity` 후 `graph_cycle(ax1, ...)` 직접 호출

### 루프 내 label 관련 변수

| 변수 | 생성 위치 | 의미 |
|---|---|---|
| `cycnamelist` | `FolderBase.split("\\")` | 경로 분할 리스트 |
| `headername` | `[cycnamelist[-2] + ", " + cycnamelist[-1]]` | 엑셀 헤더명 |
| `ch_label` | `_make_channel_labels(...)` | 메인 채널 레이블 |
| `sub_label` | `_make_channel_labels(...)` | 서브 채널 레이블 |
| `temp_lgnd` / `lgnd` | 모드별 분기 | 범례 표시 문자열 |
| `colorno` | 정수 (0부터) | 색상 인덱스 |

### `_make_channel_labels(cycnamelist, all_data_name, folder_idx)` 규칙

```
ch_label:
  all_data_name이 있으면 → all_data_name[folder_idx]  (지정Path)
  없으면                → cycnamelist[-2]             (직접입력/폴더)
  "mAh_" 포함 시        → "mAh_" 이후 부분만 사용
  30자 초과 시          → 앞 30자 + "..."

sub_label:
  항상 → extract_text_in_brackets(cycnamelist[-1])
```

### channel_map / sub_channel_map (artist 추적)

```python
channel_map     = {ch_label:  {'artists': [Artist, ...], 'color': color}}
sub_channel_map = {sub_label: {'artists': [Artist, ...], 'color': color, 'parent': ch_label}}
```

`_finalize_cycle_tab`에 전달되어 채널 토글 버튼 생성에 사용됨.

### 중복 ch_label 처리 (동일 라벨-다른 색상)

```python
_base = ch_label
_sfx = 2
while ch_label in channel_map and channel_map[ch_label]['color'] != _color:
    ch_label = f"{_base} ({_sfx})"
    _sfx += 1
```

### 통합(overall) 모드 전용 변수

| 변수 | 의미 |
|---|---|
| `_seen_ch_labels` | `set` — 범례 중복 방지 |
| `temp_lgnd` | ch_label이 처음이면 label, 이후는 `"_nolegend_"` |
| `overall_xlimit` | 전체 중 최대 사이클 수 (x축 자동 범위) |

---

## PHASE 4 — FINALIZE (`_finalize_cycle_tab()`)

### 시그니처

```python
def _finalize_cycle_tab(self, tab, tab_layout, canvas, toolbar, tab_no,
                        channel_map, fig, axes_list, sub_channel_map=None)
```

### 처리 단계

| 단계 | 동작 |
|---|---|
| `_create_cycle_channel_control(channel_map, ...)` | 채널 토글 버튼 생성 (오버레이) |
| `toolbar_row = QHBoxLayout` | toolbar + toggle_btn 한 줄 배치 |
| `tab_layout.addWidget(canvas)` | 그래프 추가 |
| `self.cycle_tab.addTab(tab, str(tab_no))` | 탭 등록 |
| `plt.tight_layout(pad=1, ...)` | 여백 조정 |

> **진행률**: plot 완료 후 `progressBar` 50 → 100%

---

## 6개 함수 비교

| 함수 | 버튼 (objectName) | 입력 | 탭 생성 규칙 | 연결 방식 | 신뢰성 |
|---|---|---|---|---|---|
| `app_cyc_confirm_button` | `AppCycConfirm` | filedialog (.xlsx 복수) | 파일별 1탭 | 없음 | ✅ ax1만 |
| `indiv_cyc_confirm_button` | `indiv_cycle` | pne_path_setting | folder별 1탭 | 없음 | ❌ |
| `overall_cyc_confirm_button` | `overall_cycle` | pne_path_setting | 전체 1탭 | 없음 | ❌ |
| `link_cyc_confirm_button` | `link_cycle` | pne_path_setting | 1탭 | sub_label 병합 | ❌ |
| `link_cyc_indiv_confirm_button` | `link_cycle_indiv` | openfilenames (.txt) | .txt 파일별 1탭 | cyclename(sub_label) 병합 | ❌ |
| `link_cyc_overall_confirm_button` | `link_cycle_overall` | openfilenames (.txt) | 전체 통합 1탭 | cyclename(sub_label) 병합 | ❌ |

---

## Link 모드 전용 변수

| 변수 | 타입 | 의미 |
|---|---|---|
| `merged` | `dict` | `{merge_label: {'frames':[], 'colorno':int, 'ch_label':str}}` |
| `merge_label` | `str` or `(k, str)` | 병합 키 (`link_indiv`/`overall`는 `(file_idx, sub_label)`) |
| `CycleMax[5]` | `list[int]` | 채널별 누적 사이클 수 (index 오프셋 계산용) |
| `link_writerownum[5]` | `list[int]` | 채널별 엑셀 행 시작 위치 |
| `Chnl_num` | `int` | 현재 폴더 내 채널 번호 |
| `writerowno` | `int` | 현재 엑셀 출력 행 |
| `_first_ch_label` | `str` | 첫 번째 ch_label 고정 (link 모드: 모든 폴더가 동일 label) |

### 병합 후 plot 임시 wrapper

```python
merged_df = pd.concat(info['frames']).sort_index()
_wrapper = type('CycData', (), {'NewData': merged_df})()
# → graph_output_cycle(_wrapper, ...) 로 전달
```

---

## Excel 저장 흐름

```
writer (전역) = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
  ↓
_save_cycle_excel_data(nd, writecolno, start_row, headername)
  → output_data(nd, sheet_name, col, row, "OriCyc"/"Dchg"/..., header)
  writecolno += 2  (Cycle열 + 데이터열)
  ↓
writer.close()
```

### 저장 시트 목록

| 시트명 | 내용 |
|---|---|
| `방전용량` | OriCyc + Dchg |
| `Rest End` | OriCyc + RndV |
| `평균 전압` | OriCyc + AvgV |
| `충방효율` | OriCyc + Eff |
| `충전용량` | OriCyc + Chg |
| `방충효율` | OriCyc + Eff2 |
| `방전Energy` | OriCyc + DchgEng |
| `DCIR` or `RSS` | OriCyc + dcir / dcir2 |
| `SOC70_DCIR` | OriCyc + soc70_dcir (mkdcir 시) |
| `SOC70_RSS` | OriCyc + soc70_rss_dcir (mkdcir 시) |
| `RSS_OCV` / `RSS_CCV` | OriCyc + rssocv / rssccv (mkdcir 시) |

---

## connect 연결 (L9487~9493)

```python
self.cycle_tab_reset.clicked.connect(self.cycle_tab_reset_confirm_button)
self.indiv_cycle.clicked.connect(self.indiv_cyc_confirm_button)
self.overall_cycle.clicked.connect(self.overall_cyc_confirm_button)
self.link_cycle.clicked.connect(self.link_cyc_confirm_button)
self.link_cycle_indiv.clicked.connect(self.link_cyc_indiv_confirm_button)
self.link_cycle_overall.clicked.connect(self.link_cyc_overall_confirm_button)
self.AppCycConfirm.clicked.connect(self.app_cyc_confirm_button)
```

---

## 변수 전체 흐름 요약

```
[UI 입력]
  chk_cyclepath / stepnum_2 / 폴더다이얼로그
        ↓ pne_path_setting()
[PARSE]
  all_data_folder  : 폴더 경로 목록
  all_data_name    : 채널 이름 목록
  datafilepath     : 원본 경로 (용량 추출용)
        ↓ _load_all_cycle_data_parallel()
[LOAD]
  subfolder_map    : {i: [subfolder_path, ...]}
  loaded_data      : {(i,j): (folder_path, cyctemp)}
  cyctemp          : [mincapacity, obj(NewData=DataFrame)]
        ↓ 루프 내 _make_channel_labels()
[LABEL]
  ch_label         : 메인 채널명 (범례/채널 토글)
  sub_label        : 서브 채널명 (개별 추적)
  headername       : 엑셀 헤더
        ↓ graph_output_cycle()
[PLOT]
  artists          : scatter/line artist 목록
  color            : 현재 채널 색상
  channel_map      : {ch_label: {artists, color}}
  sub_channel_map  : {sub_label: {artists, color, parent}}
        ↓ _finalize_cycle_tab()
[FINALIZE]
  toggle_btn       : 채널 ON/OFF 토글 버튼
  tab              : QWidget 탭
  cycle_tab        : 최종 탭 위젯에 등록
```
