# Cycle 통합 리팩토링 — 변경 후 코드 분석

> 작성일: 2026-03-18 (코드 변경 후 재분석)
> 대상 파일: `DataTool_dev/DataTool_optRCD_proto_.py` (18572 lines)
> 이전 문서: `260318_cycle_parse_load_plot_finalize.md` (변경 전 19016 lines)

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
| index 오프셋 | `CycleMax[5]`, `link_writerownum[5]` 배열 | `channel_state[sub_label]` dict |
| 탭 할당 | 모드별 별도 로직 | `tab_units` 리스트로 통일 |

> **`pne_path_setting()`**: 사이클 탭에서는 더 이상 사용 안 함.
> Profile, DCIR, 승인 수명 예측 등 다른 기능에서 계속 사용 중 (삭제 불가).

---

## 신규 데이터 구조 — `CycleGroup` dataclass (L200)

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

---

## PHASE 1 — PARSE

### 신규 UI 위젯

| 위젯 | 타입 | 의미 |
|---|---|---|
| `radio_indiv` | QRadioButton (기본 ON) | 개별 탭 모드 |
| `radio_overall` | QRadioButton | 통합 탭 모드 |
| `chk_link_cycle` | QCheckBox | 직접입력 연결처리 ON/OFF |
| `cycle_confirm` | QPushButton | 단일 실행 버튼 |

---

### `_parse_cycle_input()` → `list[CycleGroup]` (L11034)

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

---

### `_parse_path_file(filepath)` (L10993, staticmethod)

`.txt` 파일을 파싱하여 `[(cyclename, cyclepath), ...]` 반환.

```
헤더 1줄 스킵
각 줄: tab 구분 → parts
  cyclename = ' '.join(parts[:-1])
  cyclepath = parts[-1]
```

---

### `_build_group_from_lines(lines, file_idx)` (L11004)

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

---

## PHASE 2 — LOAD

`_load_all_cycle_data_parallel()` **구조 변경 없음** (이전 문서 참조).

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

---

## PHASE 3 — PLOT

### 탭 할당 — `tab_units` (L11257)

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

---

### 연결 모드 (`group.is_link = True`) 내 변수 (L11288)

| 변수 | 타입 | 설명 |
|---|---|---|
| `merged` | `dict{sub_label: {'frames', 'colorno', 'ch_label'}}` | 채널별 DataFrame 병합 누적 |
| `channel_state` | `dict{sub_label: {'offset': int, 'last_len': int}}` | index 오프셋 추적 |
| `_first_ch_label` | `str` | 연결 시 모든 폴더에 동일 ch_label 적용 |
| `local_colorno` | `int` | 그룹 내 색상 인덱스 |
| `writerowno` | `int` | `st['offset'] + st['last_len']` |

#### `channel_state` 오프셋 계산 (구 `CycleMax[5]` 대체)

```python
# 구 방식 (배열 인덱스 기반)
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

#### 병합 후 plot

```python
for sub_label, info in merged.items():
    merged_df = pd.concat(info['frames']).sort_index()
    _wrapper = type('CycData', (), {'NewData': merged_df})()
    _artists, _color = graph_output_cycle(_wrapper, ...)
```

---

### 비연결 모드 (`group.is_link = False`) 내 변수 (L11396)

이전 `indiv_cyc` / `overall_cyc_confirm_button`과 동일 구조.

| 변수 | 설명 |
|---|---|
| `_seen_ch_labels` | 통합 모드 범례 중복 방지 set |
| `lgnd` | 개별=`sub_label`, 통합=첫 등장시 ch_label / 이후 `"_nolegend_"` |
| `colorno` | 개별 탭 시작 시 `0` 리셋, 통합 시 `+1` 유지 |

#### 색상 리셋 규칙

```python
if is_individual:
    colorno = 0          # 탭(그룹)별 색상 리셋
else:
    colorno = colorno % len(THEME['PALETTE']) + 1  # 누적
```

---

### ch_label 생성 규칙 (연결/비연결 공통)

`_make_channel_labels()` 함수 대신 `unified_cyc_confirm_button` 내부에 인라인 구현.
규칙은 동일:

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

---

### suptitle 결정 (L11483)

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

---

## PHASE 4 — FINALIZE

`_finalize_cycle_tab()` **구조 변경 없음** (이전 문서 참조).

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

---

## Excel 그룹 (신뢰성 `.xlsx`) 처리 (L11157)

```python
excel_groups = [g for g in groups if g.data_type == 'excel']
if excel_groups:
    fig, ((ax1,)) = plt.subplots(nrows=1, ncols=1, figsize=(14, 8))
    # ax1만 사용, xlwings로 .xlsx 읽어 graph_cycle(ax1, ...) 호출
    # 채널 토글 없음 (channel_map 미생성)
    # tab_layout.addWidget(toolbar) + canvas 직접 추가
    # _finalize_cycle_tab() 미호출
```

---

## 전체 변수 흐름 요약 (신규)

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

---

## connect (L9449~9451)

```python
self.cycle_tab_reset.clicked.connect(self.cycle_tab_reset_confirm_button)
self.cycle_confirm.clicked.connect(self.unified_cyc_confirm_button)
```

기존 6개 연결 → 2개로 축소.

---

## 입력 방식별 동작 매트릭스

| 입력 방식 | chk_link_cycle | data_type | is_link | 탭 규칙 |
|---|---|---|---|---|
| 직접입력(`stepnum_2`) | OFF | folder | False | radio 기준 |
| 직접입력(`stepnum_2`) | ON | folder | True (빈줄 기준) | radio 기준 |
| 직접입력 — .xlsx 경로 | 무관 | excel | False | 신뢰성 탭 1개 |
| 직접입력 — .txt 경로 | 무관 | folder | cyclename 기반 | radio 기준 |
| 지정Path(.txt) | 무관 | folder | cyclename 동일=True | radio 기준 |
| 지정Path(.xlsx) | 무관 | excel | False | 신뢰성 탭 1개 |
| 폴더 선택 | 무관 | folder | False (항상 개별) | radio 기준 |
