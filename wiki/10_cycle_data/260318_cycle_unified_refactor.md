# Cycle 통합 리팩토링 — 6개 함수 → 1개 통합 함수 전환

> 작성일: 2026-03-18 (통합 작업 당시)
> 최종 갱신: 2026-04-21 — 관련 문서 병합
> 대상 파일: `DataTool_dev/DataTool_optRCD_proto_.py`
>
> 📎 2026-04-21: `260318_cycle_parse_load_plot_finalize` (변경 전 구조 분석) + `260318_unify_6_cycle_functions` (삭제/추가 로그) 병합.

---

## 변경 요약

| 항목 | 변경 전 | 변경 후 |
|---|---|---|
| 버튼 수 | 6개 (`indiv_cycle`, `overall_cycle`, `link_cycle`, `link_cycle_indiv`, `link_cycle_overall`, `AppCycConfirm`) | 1개 (`cycle_confirm`) |
| 라디오 | 없음 | `radio_indiv` / `radio_overall` |
| 체크박스 | 없음 | `chk_link_cycle` (연결처리) |
| 진입 함수 | 6개 독립 함수 | `unified_cyc_confirm_button()` 1개 |
| 입력 파싱 | `pne_path_setting()` (폴더/path파일) + 각 함수 내 직접 처리 | `_parse_cycle_input()` → `list[CycleGroup]` |
| 입력 타입 판별 | 함수별 하드코딩 | `CycleGroup.data_type`, `is_link` 로 통일 |
| index 오프셋 | `CycleMax[5]`, `link_writerownum[5]` 배열 (최대 5채널 제한) | `channel_state[sub_label]` dict (채널 수 제한 없음) |
| 탭 할당 | 모드별 별도 로직 | `tab_units` 리스트로 통일 |

> **`pne_path_setting()`**: 사이클 탭에서는 더 이상 사용 안 함.
> Profile, DCIR, 승인 수명 예측 등 다른 기능에서 계속 사용 중 (삭제 불가).

---

## ① 변경 전 구조 — parse → load → plot → finalize 흐름

### 공통 초기화 — `cyc_ini_set()`

기존 6개 함수가 제일 먼저 호출함.

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

### PHASE 1 (기존) — PARSE (`pne_path_setting()`)

**반환**: `[all_data_folder, all_data_name, datafilepath]`

```
입력 방식 분기:
  chk_cyclepath.isChecked() → .txt path파일 선택
      ↓ 파싱: tab 구분, 마지막 필드=cyclepath, 나머지=cyclename
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

> **`link_cyc_indiv/overall_confirm_button`**: `pne_path_setting()` 미사용.
> 대신 `filedialog.askopenfilenames()`로 `.txt` 파일 복수 선택 → 함수 내부에서 `pd.read_csv(sep="\t")`로 직접 파싱.

### PHASE 2 (기존) — LOAD (`_load_all_cycle_data_parallel()`)

```python
def _load_all_cycle_data_parallel(self, all_data_folder, mincapacity, firstCrate,
                                   dcirchk, dcirchk_2, mkdcir, max_workers=4)
```

**반환**: `(results, subfolder_map)`

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

| 변수 | 타입 | 설명 |
|---|---|---|
| `subfolder_map` | `dict{int: [str]}` | `{folder_idx: [subfolder_path, ...]}` |
| `results` (=`loaded_data`) | `dict{(int,int): (str, obj)}` | `{(i,j): (folder_path, cyctemp)}` |
| `cyctemp` | `tuple` | `[mincapacity(float), df_obj]` |
| `cyctemp[1].NewData` | `pd.DataFrame` | 실제 사이클 데이터 |

#### `cyctemp[1].NewData` 컬럼

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

### PHASE 3 (기존) — PLOT (`graph_output_cycle()`)

```python
def graph_output_cycle(df, xscale, ylimitlow, ylimithigh, irscale, temp_lgnd,
                       colorno, graphcolor, dcir, ax1, ax2, ax3, ax4, ax5, ax6)
```

**반환**: `(artists, color)`

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

> **예외: `app_cyc_confirm_button` (신뢰성)** — `fig, ((ax1)) = plt.subplots(1, 1)` — **ax1만** 존재. xlwings로 `.xlsx` 읽어 `df/mincapacity` 후 `graph_cycle(ax1, ...)` 직접 호출.

#### `_make_channel_labels(cycnamelist, all_data_name, folder_idx)` (기존 규칙)

```
ch_label:
  all_data_name이 있으면 → all_data_name[folder_idx]  (지정Path)
  없으면                → cycnamelist[-2]             (직접입력/폴더)
  "mAh_" 포함 시        → "mAh_" 이후 부분만 사용
  30자 초과 시          → 앞 30자 + "..."

sub_label:
  항상 → extract_text_in_brackets(cycnamelist[-1])
```

#### channel_map / sub_channel_map (artist 추적)

```python
channel_map     = {ch_label:  {'artists': [Artist, ...], 'color': color}}
sub_channel_map = {sub_label: {'artists': [Artist, ...], 'color': color, 'parent': ch_label}}
```

### PHASE 4 (기존) — FINALIZE (`_finalize_cycle_tab()`)

```python
def _finalize_cycle_tab(self, tab, tab_layout, canvas, toolbar, tab_no,
                        channel_map, fig, axes_list, sub_channel_map=None)
```

| 단계 | 동작 |
|---|---|
| `_create_cycle_channel_control(channel_map, ...)` | 채널 토글 버튼 생성 (오버레이) |
| `toolbar_row = QHBoxLayout` | toolbar + toggle_btn 한 줄 배치 |
| `tab_layout.addWidget(canvas)` | 그래프 추가 |
| `self.cycle_tab.addTab(tab, str(tab_no))` | 탭 등록 |
| `plt.tight_layout(pad=1, ...)` | 여백 조정 |

> **진행률**: plot 완료 후 `progressBar` 50 → 100%

### 기존 6개 함수 비교

| 함수 | 버튼 (objectName) | 입력 | 탭 생성 규칙 | 연결 방식 | 신뢰성 |
|---|---|---|---|---|---|
| `app_cyc_confirm_button` | `AppCycConfirm` | filedialog (.xlsx 복수) | 파일별 1탭 | 없음 | ✅ ax1만 |
| `indiv_cyc_confirm_button` | `indiv_cycle` | pne_path_setting | folder별 1탭 | 없음 | ❌ |
| `overall_cyc_confirm_button` | `overall_cycle` | pne_path_setting | 전체 1탭 | 없음 | ❌ |
| `link_cyc_confirm_button` | `link_cycle` | pne_path_setting | 1탭 | sub_label 병합 | ❌ |
| `link_cyc_indiv_confirm_button` | `link_cycle_indiv` | openfilenames (.txt) | .txt 파일별 1탭 | cyclename(sub_label) 병합 | ❌ |
| `link_cyc_overall_confirm_button` | `link_cycle_overall` | openfilenames (.txt) | 전체 통합 1탭 | cyclename(sub_label) 병합 | ❌ |

### Link 모드 전용 변수 (기존)

| 변수 | 타입 | 의미 |
|---|---|---|
| `merged` | `dict` | `{merge_label: {'frames':[], 'colorno':int, 'ch_label':str}}` |
| `merge_label` | `str` or `(k, str)` | 병합 키 (`link_indiv`/`overall`는 `(file_idx, sub_label)`) |
| `CycleMax[5]` | `list[int]` | **채널별 누적 사이클 수 (최대 5채널 제한)** |
| `link_writerownum[5]` | `list[int]` | 채널별 엑셀 행 시작 위치 |
| `Chnl_num` | `int` | 현재 폴더 내 채널 번호 |
| `writerowno` | `int` | 현재 엑셀 출력 행 |
| `_first_ch_label` | `str` | 첫 번째 ch_label 고정 (link 모드: 모든 폴더가 동일 label) |

---

## ② 변경 내용 — 통합 후 코드 구조

### 신규 데이터 구조 — `CycleGroup` dataclass (L200)

```python
@dataclass
class CycleGroup:
    name: str                          # 범례/탭 표시명
    paths: list = field(...)           # 데이터 경로 목록
    path_names: list = field(...)      # per-path cyclename (path 파일 출처)
    is_link: bool = False              # 연결 여부 (paths 2개 이상)
    data_type: str = 'folder'          # 'folder' | 'excel'
    file_idx: int = 0                  # 출처 path 파일 번호 (통합 탭 기준)
    source_file: str = ''              # 원본 path 파일 경로 (mAh 추출용)
```

| 필드 | 설명 |
|---|---|
| `name` | 탭/범례에 표시될 그룹명 |
| `paths` | 분석할 폴더 경로 목록 (연결 시 2개 이상) |
| `path_names` | 각 path에 대응하는 cyclename (지정Path .txt 출처일 때만 유효) |
| `is_link` | `len(paths) > 1` → 연결 모드 |
| `data_type` | `'excel'` = 신뢰성(.xlsx), `'folder'` = 일반 폴더 |
| `file_idx` | 출처 .txt 파일 번호 (통합 라디오 시 같은 파일 = 1탭) |
| `source_file` | 용량 추출 및 suptitle용 원본 파일 경로 |

### PHASE 1 — PARSE (신규)

#### 신규 UI 위젯

| 위젯 | 타입 | 의미 |
|---|---|---|
| `radio_indiv` | QRadioButton (기본 ON) | 개별 탭 모드 |
| `radio_overall` | QRadioButton | 통합 탭 모드 |
| `chk_link_cycle` | QCheckBox | 직접입력 연결처리 ON/OFF |
| `cycle_confirm` | QPushButton | 단일 실행 버튼 |

#### `_parse_cycle_input()` → `list[CycleGroup]` (L11034)

```
분기 1: chk_cyclepath.isChecked()  →  지정Path (다중 파일 선택)
  for fp in filedialog.askopenfilenames():
    ext == '.xlsx'  → CycleGroup(data_type='excel', paths=[fp])
    ext in '.txt/.csv'  → _parse_path_file(fp)
                          name_order = OrderedDict()  # cyclename으로 그룹화
                          동일 cyclename = 자동 is_link=True
                          → CycleGroup(data_type='folder', is_link=len>1)
    else (폴더 경로)  → CycleGroup(data_type='folder', paths=[fp])

분기 2: stepnum_2.toPlainText().strip()  →  직접입력
  link_mode = chk_link_cycle.isChecked()
  link_mode=True:
    빈 줄 = 그룹 구분 → _build_group_from_lines(current_group)
  link_mode=False:
    각 줄 → _build_group_from_lines([stripped])  # is_link=False

분기 3: else  →  폴더 선택 다이얼로그
  for fp in multi_askopendirnames():
    → CycleGroup(data_type='folder', is_link=False, paths=[fp])
```

#### `_parse_path_file(filepath)` (L10993, staticmethod)

`.txt` 파일을 파싱하여 `[(cyclename, cyclepath), ...]` 반환.

```
헤더 1줄 스킵
각 줄: tab 구분 → parts
  cyclename = ' '.join(parts[:-1])
  cyclepath = parts[-1]
```

#### `_build_group_from_lines(lines, file_idx)` (L11004)

직접입력 줄 목록으로 `CycleGroup` 생성. 확장자에 따라 자동 판별.

```
for line in lines:
  ext == '.xlsx'      → data_type='excel', all_paths.append(line)
  ext in '.txt/.csv'  → _parse_path_file(line) 재파싱
                         all_paths += cpaths, path_names += cnames
  else               → all_paths.append(line) (폴더)

반환: CycleGroup(
  name=os.path.basename(all_paths[0]),
  paths=all_paths, path_names=path_names,
  is_link=len(all_paths) > 1,
  data_type=data_type, file_idx=file_idx,
  source_file=source_file
)
```

### PHASE 2 — LOAD (신규)

`_load_all_cycle_data_parallel()` **구조 변경 없음** (위 ① 참조).

신규 변수: `flat_idx_of` (통합 진입 시 구성)

```python
all_paths = []
flat_idx_of = {}       # {(gi, pi): flat_idx}
for gi, g in enumerate(folder_groups):
    for pi, p in enumerate(g.paths):
        flat_idx_of[(gi, pi)] = len(all_paths)
        all_paths.append(p)

loaded_data, subfolder_map = self._load_all_cycle_data_parallel(np.array(all_paths), ...)
```

| 변수 | 타입 | 설명 |
|---|---|---|
| `all_paths` | `list[str]` | folder_groups의 모든 paths 평탄화 |
| `flat_idx_of` | `dict{(gi,pi): int}` | group/path 인덱스 → flat index 매핑 |
| `flat_indices` | `list[int]` | group 내 paths의 flat index 목록 |

### PHASE 3 — PLOT (신규)

#### 탭 할당 — `tab_units` (L11257)

```python
if is_individual:
    tab_units = [[gi] for gi in range(len(folder_groups))]
    # 그룹(CycleGroup)별 1탭
else:
    by_file = OrderedDict()
    for gi, g in enumerate(folder_groups):
        by_file.setdefault(g.file_idx, []).append(gi)
    tab_units = list(by_file.values())
    # file_idx별 1탭 (동일 .txt 파일 출처 = 통합)
```

| 라디오 | 탭 단위 |
|---|---|
| `radio_indiv` (개별) | `CycleGroup` 1개 = 1탭 |
| `radio_overall` (통합) | 동일 `file_idx` = 1탭 |

#### 연결 모드 (`group.is_link = True`) 내 변수 (L11288)

| 변수 | 타입 | 설명 |
|---|---|---|
| `merged` | `dict{sub_label: {'frames', 'colorno', 'ch_label'}}` | 채널별 DataFrame 병합 누적 |
| `channel_state` | `dict{sub_label: {'offset': int, 'last_len': int}}` | index 오프셋 추적 |
| `_first_ch_label` | `str` | 연결 시 모든 폴더에 동일 ch_label 적용 |
| `local_colorno` | `int` | 그룹 내 색상 인덱스 |
| `writerowno` | `int` | `st['offset'] + st['last_len']` |

##### `channel_state` 오프셋 계산 (구 `CycleMax[5]` 대체)

```python
# 구 방식 (배열 인덱스 기반, 최대 5채널)
writerowno = link_writerownum[Chnl_num] + CycleMax[Chnl_num]
CycleMax[Chnl_num] = len(cyctemp[1].NewData)
link_writerownum[Chnl_num] = writerowno

# 신 방식 (sub_label 키 기반 → 채널 수 제한 없음)
st = channel_state[sub_label]          # {'offset': int, 'last_len': int}
writerowno = st['offset'] + st['last_len']
cyctemp[1].NewData.index += writerowno
st['offset'] = writerowno
st['last_len'] = len(cyctemp[1].NewData)
```

##### 병합 후 plot

```python
for sub_label, info in merged.items():
    merged_df = pd.concat(info['frames']).sort_index()
    _wrapper = type('CycData', (), {'NewData': merged_df})()
    _artists, _color = graph_output_cycle(_wrapper, ...)
```

#### 비연결 모드 (`group.is_link = False`) 내 변수 (L11396)

이전 `indiv_cyc` / `overall_cyc_confirm_button`과 동일 구조.

| 변수 | 설명 |
|---|---|
| `_seen_ch_labels` | 통합 모드 범례 중복 방지 set |
| `lgnd` | 개별=`sub_label`, 통합=첫 등장시 ch_label / 이후 `"_nolegend_"` |
| `colorno` | 개별 탭 시작 시 `0` 리셋, 통합 시 `+1` 유지 |

##### 색상 리셋 규칙

```python
if is_individual:
    colorno = 0          # 탭(그룹)별 색상 리셋
else:
    colorno = colorno % len(THEME['PALETTE']) + 1  # 누적
```

#### ch_label 생성 규칙 (연결/비연결 공통)

`_make_channel_labels()` 함수 대신 `unified_cyc_confirm_button` 내부에 인라인 구현. 규칙은 동일:

```python
sub_label = extract_text_in_brackets(cycnamelist[-1])

# ch_label:
if group.path_names and group.path_names[path_idx]:
    ch_label = str(group.path_names[path_idx]).strip()   # 지정Path
else:
    ch_label = cycnamelist[-2]                           # 직접/폴더
if "mAh_" in ch_label:
    ch_label = ch_label.split("mAh_", 1)[1]
if len(ch_label) > 30:
    ch_label = ch_label[:30] + "..."
```

> `_make_channel_labels()` 함수(L234)는 아직 코드에 존재하나, `unified_cyc_confirm_button`에서는 미사용.

#### suptitle 결정 (L11483)

```python
suptitle_name = cycnamelist[-2]      # 기본: 마지막 처리 폴더의 부모명
for gi in group_indices:
    g = folder_groups[gi]
    if g.source_file:
        base = os.path.splitext(os.path.basename(g.source_file))[0]
        if base:
            suptitle_name = base     # 우선: source_file(.txt) 이름
        break
```

### PHASE 4 — FINALIZE (신규)

`_finalize_cycle_tab()` **구조 변경 없음**.

범례 설정 분기 추가:

```python
if not is_individual:
    # 중복 제거 + 명시적 handles/labels 전달 (통합 모드)
    for _ax, _loc, _anchor in _legend_locs:
        _hl_unique = [중복 제거 로직]
        _ax.legend(..., bbox_to_anchor=_anchor, ...)
else:
    # 단순 legend (개별 모드)
    ax1.legend(loc="lower left")
    ...
```

### Excel 그룹 (신뢰성 `.xlsx`) 처리 (L11157)

```python
excel_groups = [g for g in groups if g.data_type == 'excel']
if excel_groups:
    fig, ((ax1,)) = plt.subplots(nrows=1, ncols=1, figsize=(14, 8))
    # ax1만 사용, xlwings로 .xlsx 읽어 graph_cycle(ax1, ...) 호출
    # 채널 토글 없음 (channel_map 미생성)
    # tab_layout.addWidget(toolbar) + canvas 직접 추가
    # _finalize_cycle_tab() 미호출
```

### 전체 변수 흐름 요약 (신규)

```
[UI 입력]
  chk_cyclepath / stepnum_2 + chk_link_cycle / 폴더다이얼로그
  radio_indiv / radio_overall
        ↓ _parse_cycle_input()
[PARSE]
  groups: list[CycleGroup]
    ├─ excel_groups: data_type='excel'
    └─ folder_groups: data_type='folder'
        ↓
[LOAD]
  all_paths (flatten) + flat_idx_of{(gi,pi):int}
  loaded_data {(fi,sj): (path, cyctemp)}
  subfolder_map {fi: [subfolder_path,...]}
        ↓ tab_units 결정
[TAB 할당]
  개별: [[0],[1],[2],...]       → group별 1탭
  통합: [[0,1],[2,3],...]       → file_idx별 1탭
        ↓ per tab_unit 루프
[PLOT — is_link=True (연결)]
  channel_state {sub_label: {offset, last_len}}
  merged {sub_label: {frames, colorno, ch_label}}
    → merged_df = pd.concat(frames).sort_index()
    → _wrapper = CycData(NewData=merged_df)
    → graph_output_cycle(_wrapper, ...)
[PLOT — is_link=False (비연결)]
  graph_output_cycle(cyctemp[1], ...)
        ↓ 공통
  channel_map {ch_label: {artists, color}}
  sub_channel_map {sub_label: {artists, color, parent}}
        ↓ _finalize_cycle_tab()
[FINALIZE]
  toggle_btn + canvas + toolbar → cycle_tab.addTab(tab, str(tab_no))
```

### connect 변경 (L9449~9451)

```python
self.cycle_tab_reset.clicked.connect(self.cycle_tab_reset_confirm_button)
self.cycle_confirm.clicked.connect(self.unified_cyc_confirm_button)
```

기존 6개 연결 → 2개로 축소.

### 입력 방식별 동작 매트릭스

| 입력 방식 | chk_link_cycle | data_type | is_link | 탭 규칙 |
|---|---|---|---|---|
| 직접입력(`stepnum_2`) | OFF | folder | False | radio 기준 |
| 직접입력(`stepnum_2`) | ON | folder | True (빈줄 기준) | radio 기준 |
| 직접입력 — .xlsx 경로 | 무관 | excel | False | 신뢰성 탭 1개 |
| 직접입력 — .txt 경로 | 무관 | folder | cyclename 기반 | radio 기준 |
| 지정Path(.txt) | 무관 | folder | cyclename 동일=True | radio 기준 |
| 지정Path(.xlsx) | 무관 | excel | False | 신뢰성 탭 1개 |
| 폴더 선택 | 무관 | folder | False (항상 개별) | radio 기준 |

---

## ③ Before / After 함수 목록

### 삭제된 함수 (6개 + 헬퍼 1개)

| 함수 | 역할 |
|------|------|
| `app_cyc_confirm_button` | 신뢰성 Cycle (.xlsx) |
| `indiv_cyc_confirm_button` | 개별 Cycle (폴더별 1탭) |
| `overall_cyc_confirm_button` | 통합 Cycle (모든 폴더 1탭) |
| `link_cyc_confirm_button` | 연결 Cycle (채널별 병합) |
| `link_cyc_indiv_confirm_button` | 연결 Cycle 여러개 개별 (파일별 1탭) |
| `link_cyc_overall_confirm_button` | 연결 Cycle 여러개 통합 (전체 1탭) |
| `app_pne_path_setting` | 미사용 헬퍼 (삭제) |

### 추가된 함수 (4개)

| 함수 | 역할 |
|------|------|
| `_parse_path_file(filepath)` | .txt path 파일 파싱 (static) |
| `_build_group_from_lines(lines, file_idx)` | 직접입력 줄 → CycleGroup 변환 |
| `_parse_cycle_input()` | 3가지 입력 모드 통합 파싱 → `list[CycleGroup]` |
| `unified_cyc_confirm_button()` | 통합 사이클 분석 메인 함수 |

### CycleGroup dataclass 변경

- `path_names` 필드 추가 (per-path cyclename)
- `source_file` 필드 추가 (원본 파일 경로, mAh 추출용)

### UI 변경 (setupUi)

- **삭제**: 6개 버튼 (`indiv_cycle`, `overall_cycle`, `link_cycle`, `AppCycConfirm`, `link_cycle_indiv`, `link_cycle_overall`)
- **삭제**: `horizontalLayout_92` (3번째 버튼 행)
- **추가**: `radio_indiv` (개별 라디오, 기본 선택)
- **추가**: `radio_overall` (통합 라디오)
- **추가**: `chk_link_cycle` (연결처리 체크박스)
- **추가**: `cycle_confirm` (Cycle 분석 버튼, 430x70)

### retranslateUi 변경

- 6개 버튼 텍스트 → 3개 위젯 텍스트 (`개별`, `통합`, `연결처리`, `Cycle 분석`)

### connect 변경

- 6개 `.clicked.connect()` → 1개 `cycle_confirm.clicked.connect(unified_cyc_confirm_button)`

### 통합 동작 규칙

#### 입력 모드별 동작

| 입력 방식 | 연결처리 체크박스 | 동작 |
|-----------|-----------------|------|
| 지정Path (.xlsx) | 무관 | 신뢰성 모드 (1x1, ax1만) |
| 지정Path (.txt) | 무관 | cyclename 동일 = 자동 연결 |
| 직접입력 | ✅ ON | 빈줄 없이 연속 = 연결, 빈줄 = 구분 |
| 직접입력 | ❌ OFF | 모든 줄 = 개별 |
| 폴더선택 | 무관 | 항상 개별 |

#### 탭 생성 규칙

| 모드 | 규칙 |
|------|------|
| 개별 (radio_indiv) | CycleGroup별 1탭 |
| 통합 (radio_overall) | file_idx별 1탭 |

#### 연결 모드 개선

- 기존: `CycleMax[5]` 고정 배열 (최대 5채널)
- 변경: `channel_state` dict (채널 수 제한 없음)

---

## ④ 관련 문서

- [[260319_review_cycle_data_tab]] — 변경 후 탭 리뷰
- [[260321_review_cycle_classification_logic]] — 사이클 분류 로직
- [[260405_review_cycle_and_profile_analysis_logic]] — 사이클/프로필 통합 로직 설명서
- [[260411_review_cycle_pipeline_full_analysis]] — 파이프라인 전체 분석
- [[260411_analysis_cycle_concepts_unification]] — 사이클 개념 통합
- [[260411_analysis_cycle_pipeline_complete]] — 파이프라인 완성 문서
