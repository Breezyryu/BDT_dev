# 사이클 분석 파이프라인 — 완전 아키텍처 문서

**대상 파일**: `DataTool_dev/DataTool_optRCD_proto_.py`  
**작성일**: 2026-04-02  
**용도**: 디버깅/유지보수 레퍼런스  

---

## 목차

1. [전체 아키텍처 개요](#1-전체-아키텍처-개요)
2. [파이프라인 진입점](#2-파이프라인-진입점-unified_cyc_confirm_button)
3. [병렬 데이터 로딩](#3-병렬-데이터-로딩)
4. [PNE 사이클 처리](#4-pne-사이클-처리)
5. [Toyo 사이클 처리](#5-toyo-사이클-처리)
6. [DCIR 계산 3모드](#6-dcir-계산-3모드-상세)
7. [사이클 카테고리 분류](#7-사이클-카테고리-분류)
8. [그래프 출력](#8-그래프-출력-graph_output_cycle)
9. [탭 및 모드 처리](#9-탭-분기-및-모드-처리)
10. [연결 모드 상세](#10-연결처리-연결-모드-상세)
11. [엑셀 저장](#11-엑셀-저장)
12. [캐싱 아키텍처](#12-캐싱-아키텍처)
13. [DataFrame 컬럼 추적](#13-dataframe-컬럼-추적)
14. [PNE vs Toyo 비교](#14-pne-vs-toyo-비교)
15. [미사용 변수 목록](#15-미사용-변수-목록)
16. [전체 분기 조건 맵](#16-전체-분기-조건-맵)

---

## 1. 전체 아키텍처 개요

### 1.1 파이프라인 전체 흐름도

```
UI 버튼 클릭 (cycle_confirm)
    │
    ▼
unified_cyc_confirm_button()  [라인 13282]
    │
    ├── 1. cyc_ini_set()  ← UI 파라미터 수집
    ├── 2. _parse_cycle_input()  ← 테이블에서 경로 그룹 파싱
    ├── 3. Excel Writer 생성 (saveok 체크 시)
    ├── 4. 데이터 그룹 분류 (excel_groups / folder_groups)
    │
    ├── [Excel 그룹]  ← 신뢰성 데이터 (xlwings)
    │   └── "Plot Base Data" 시트 → ax1 플로팅
    │
    └── [Folder 그룹]  ← 메인 파이프라인
        │
        ├── 5. _load_all_cycle_data_parallel()  [병렬]
        │   └── _load_cycle_data_task()  × N개 채널
        │       ├── [PNE] → pne_cycle_data()
        │       └── [Toyo] → toyo_cycle_data()
        │
        ├── 6. classify_channel_path()  [병렬]
        │
        ├── 7. 탭 할당 (개별/통합 모드)
        │
        ├── 8. 플로팅 (연결/비연결 모드)
        │   └── graph_output_cycle()  × 채널
        │
        ├── 9. _save_cycle_excel_data()  × 채널
        │
        └── 10. _finalize_cycle_tab()
            ├── 채널 컨트롤 버튼 생성
            ├── 분류 정보 바
            ├── 범례 배치
            └── tight_layout 조정
```

### 1.2 함수 호출 트리

```
unified_cyc_confirm_button() [L13282]
├─ cyc_ini_set()
├─ _parse_cycle_input()
├─ _load_all_cycle_data_parallel() [L12808]
│  ├─ clear_channel_cache() [L417]
│  └─ _load_cycle_data_task() [L12792] × N (ThreadPoolExecutor)
│     ├─ pne_cycle_data() [L3743]
│     │  ├─ pne_min_cap() [L3591]
│     │  │  ├─ _get_channel_cache() [L419]
│     │  │  └─ name_capacity() [L336]
│     │  ├─ _cached_pne_restore_files() [L426]
│     │  │  └─ pd.read_csv() (SaveEndData.csv)
│     │  ├─ _cyc_to_cycle_df() [L3205]
│     │  │  ├─ _parse_cyc_header() [L3151]
│     │  │  ├─ _build_fid_pos() [L3196]
│     │  │  └─ _read_cyc_records() [L3174]
│     │  └─ _process_pne_cycleraw() [L3381]
│     │     ├─ is_micro_unit() [L405]
│     │     └─ same_add() [L533]
│     └─ toyo_cycle_data() [L1141]
│        ├─ toyo_min_cap() [L1124]
│        ├─ toyo_cycle_import() [L1103]
│        │  └─ toyo_read_csv() [L1068]
│        └─ (inline DCIR 계산)
├─ classify_channel_path() [L1626] × N (ThreadPoolExecutor)
│  ├─ classify_pne_cycles() / classify_toyo_cycles()
│  ├─ detect_test_type()
│  └─ detect_schedule_pattern()
├─ graph_output_cycle() [L598] × 채널
├─ _save_cycle_excel_data() [L12860] × 채널
│  └─ output_data()
└─ _finalize_cycle_tab() [L12259]
   ├─ _create_cycle_channel_control()
   └─ _build_classify_info_label()
```

---

## 2. 파이프라인 진입점: `unified_cyc_confirm_button()`

**라인**: 13282–14105  
**UI 연결**: `self.cycle_confirm` 버튼 클릭 → 라인 11011

### 2.1 단계별 처리

#### 단계 1: UI 파라미터 수집 (L13285–13291)

```python
firstCrate, mincapacity, xscale, ylimithigh, ylimitlow, irscale = self.cyc_ini_set()
is_individual = self.radio_indiv.isChecked()
graphcolor = THEME['PALETTE']
```

| 파라미터 | UI 위젯 | 예시 | 설명 |
|---------|---------|------|------|
| `firstCrate` | — | 80 (%) | 첫 번째 방전 구간 비율 |
| `mincapacity` | — | 2800 (mAh) | 기본 용량 |
| `xscale` | — | 50 | X축 사이클 단위 |
| `ylimithigh` | — | 105 (%) | Y축 상한 |
| `ylimitlow` | — | 80 (%) | Y축 하한 |
| `irscale` | — | 0 or auto | DCIR 스케일 |

#### 체크박스 옵션

| 위젯 | 변수 | 의미 |
|-----|------|------|
| `dcirchk` | `chkir` | SOC 범위 기반 DCIR |
| `dcirchk_2` | `chkir2` | SOC70 DCIR 보조 옵션 |
| `mkdcir` | `mkdcir` | MK DCIR (1s Pulse + RSS) |
| `saveok` | — | 엑셀 파일 저장 여부 |
| `radio_indiv` | `is_individual` | 개별 탭 모드 (True) vs 통합 (False) |
| `chk_link_cycle` | `is_link` | 연결 모드 활성화 |

#### 단계 2: 입력 파싱 (L13293)

```python
groups = self._parse_cycle_input()
```

- **소스**: `cycle_path_table` (QTableWidget, 5행 × 4열)
- **컬럼**: 경로명 | 경로(필수) | 채널 | 용량
- **반환**: `CycleGroup[]` — 개별/통합/연결 모드 지원

#### 단계 3: 파일 저장 설정 (L13301–13310)

```python
if self.saveok.isChecked():
    save_file_name = filedialog.asksaveasfilename(...)
    writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
```

#### 단계 4: 데이터 그룹 분류 (L13312–13313)

```python
excel_groups = [g for g in groups if g.data_type == 'excel']   # 신뢰성 데이터
folder_groups = [g for g in groups if g.data_type == 'folder']  # 폴더 기반 (메인)
```

---

## 3. 병렬 데이터 로딩

### 3.1 `_load_all_cycle_data_parallel()` (L12808–12859)

```python
def _load_all_cycle_data_parallel(
    self, all_data_folder, mincapacity, firstCrate,
    dcirchk, dcirchk_2, mkdcir, max_workers=None,
    per_path_capacities=None
):
```

#### 입력

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `all_data_folder` | `np.ndarray[str]` | 모든 폴더 경로 |
| `mincapacity` | `int` | 기본 용량 (mAh) |
| `firstCrate` | `float` | 첫 방전 구간 비율 |
| `dcirchk` / `dcirchk_2` / `mkdcir` | `bool` | DCIR 옵션 3종 |
| `per_path_capacities` | `list[float]` | 테이블별 커스텀 용량 (> 0이면 우선) |

#### 반환

```python
(results: dict, subfolder_map: dict)
# results: {(folder_idx, subfolder_idx): (folder_path, cyctemp)}
#   cyctemp = [mincapacity, df]  (df.NewData = 사이클 지표)
# subfolder_map: {folder_idx: [채널경로, ...]}
```

#### 처리 흐름

```
1. 캐시 초기화
   clear_channel_cache()

2. 폴더 스캔
   for each folder:
       subfolder = [채널 폴더] (_is_channel_folder() 필터)

3. 용량 선택 (테이블값 > 자동 검출)
   per_path_capacities[i] > 0 ? 테이블값 : mincapacity

4. Cycler 타입 판별
   is_pne = check_cycler(cyclefolder)

5. 병렬 작업 구성 & 실행
   ThreadPoolExecutor(max_workers = calc_optimal_workers(len(tasks)))
   futures = {submit(_load_cycle_data_task, task): task}

6. 진행률 (50%까지)
   progressBar.setValue(int(completed / total_tasks * 50))
```

### 3.2 `_load_cycle_data_task()` (L12792–12807)

단일 채널의 데이터 로딩 (ThreadPoolExecutor에서 호출):

```python
def _load_cycle_data_task(self, task_info):
    folder_path, mincapacity, firstCrate, dcirchk, dcirchk_2, mkdcir, is_pne, fi, si = task_info

    if is_pne:
        cyctemp = pne_cycle_data(folder_path, mincapacity, firstCrate, dcirchk, dcirchk_2, mkdcir)
    else:
        cyctemp = toyo_cycle_data(folder_path, mincapacity, firstCrate, dcirchk_2)

    return (fi, si, folder_path, cyctemp)
```

---

## 4. PNE 사이클 처리

### 4.1 전체 호출 흐름

```
pne_cycle_data() [L3743]
  ├─→ pne_min_cap() [L3591]          용량 산정
  ├─→ _cached_pne_restore_files()    SaveEndData CSV 캐시 로드
  ├─→ _cyc_to_cycle_df()             .cyc 바이너리 파싱 (보충/대체)
  └─→ _process_pne_cycleraw()        핵심 계산 (DCIR, pivot, NewData)
```

### 4.2 `pne_min_cap()` (L3591–3608)

**용량 산정 우선순위**:

```
1. mincapacity != 0  → 입력값 그대로 사용
2. cache['min_cap'] 존재  → 캐시 반환
3. 경로에 "mAh" 포함  → name_capacity() 파싱 (예: "2670mAh" → 2670)
4. SaveData0001.csv 존재  → 첫 스텝 용량 / ini_crate
```

### 4.3 `_cached_pne_restore_files()` (L426–461)

**역할**: PNE Restore 폴더에서 SaveEndData.csv와 파일 인덱스를 캐싱

```python
# 반환값
(save_end_data: pd.DataFrame | None,   # CSV 전체 (47컬럼)
 file_index_list: list[int] | None,    # savingFileIndex_start에서 추출
 subfile: list[str])                   # Restore 폴더의 .csv 목록
```

**캐시 키**: `cache['pne_restore']`

#### SaveEndData.csv 필요 컬럼 (13개)

pne_cycle_data()에서 선택하는 컬럼 인덱스:

| CSV [인덱스] | 변수명 | 타입 | 단위 | 설명 |
|-------------|--------|------|------|------|
| [27] | TotlCycle | int | — | 누적 사이클 번호 |
| [2] | Condition | int | — | 1=충전, 2=방전, 3=휴지, 8=루프 |
| [10] | chgCap | int | uAh | 충전 용량 적분 |
| [11] | DchgCap | int | uAh | 방전 용량 적분 |
| [8] | Ocv | int | uV | 개로셀 전압 |
| [20] | imp | int | µΩ | 내부저항 (10s 펄스) |
| [45] | volmax | int | uV | 최대 전압 |
| [15] | DchgEngD | float | Wh | 방전 에너지 |
| [17] | steptime | int | cs (0.01s) | 스텝 소요 시간 |
| [9] | Curr | int | uA | 스텝 종료 전류 |
| [24] | Temp | int | mC (0.001°C) | 온도 |
| [29] | AvgV | int | mV | 평균 전압 |
| [6] | EndState | int | — | 64=휴지, 65=CV, 66=CC, 78=용량완료 |

### 4.4 `_cyc_to_cycle_df()` (L3205–3380)

**역할**: .cyc 바이너리 파일 → SaveEndData와 동일 구조의 13컬럼 DataFrame

#### 처리 단계

```
1. 헤더 파싱: _parse_cyc_header() → n_fields, fids, data_start, rec_size
2. 레코드 로드: _read_cyc_records() → shape (N, n_fields) float32
3. FieldID 매핑: _build_fid_pos() → {FID: 레코드 인덱스}
4. 온도 단위 감지: 샘플 > |200| → 이미 mC 단위
5. 스텝 경계 식별: StepTime == 0.0 → 새 스텝 시작
6. 루프 감지: 시간 점프 > 300s OR 저전류+0용량+마지막만 고용량
7. StepType 추론: mean(current) > 10→충전, < -10→방전, else→휴지
8. EndState 추론: 꼬리 전류 변동률 > 0.05 → CV(66), else → CC(65)
9. imp 계산: |V_ocv - V@10s| / |I@10s| × 1e6 (µΩ)
10. 단위 변환: mV→uV, mA→uA, mAh→uAh, sec→cs
11. DataFrame 생성: 13컬럼 동일 구조
```

#### .cyc 보충/대체 로직 (L3776–3789)

```
조건 A: CSV + .cyc 보충
  CSV 최신 사이클 < .cyc 최신 사이클
  → supplement = cyc_df[cycle > csv_max]
  → Cycleraw = concat([CSV, supplement])

조건 B: .cyc 단독 재구성
  CSV 없음 + .cyc 존재
  → Cycleraw = _cyc_to_cycle_df(cyc_path)
```

### 4.5 `_process_pne_cycleraw()` (L3381–3588)

**역할**: Cycleraw(13컬럼) → df.NewData(9~19컬럼) 변환

```python
def _process_pne_cycleraw(
    Cycleraw, df, raw_file_path, mincapacity, chkir, chkir2, mkdcir
) -> None:  # df.NewData를 직접 수정
```

#### 처리 단계

```
1. 코인셀 단위 변환
   is_micro_unit() → DchgCap, chgCap, Curr ÷ 1000

2. DCIR 계산 (3가지 모드 → 6절 상세 참고)

3. Pivot Table 생성
   pivot(index=TotlCycle, columns=Condition, values=[DchgCap, DchgEngD, chgCap, Ocv, Temp])

4. 사이클 지표 계산
   Dchg = pivot["DchgCap"][2] / mincapacity / 1000
   Chg  = pivot["chgCap"][1] / mincapacity / 1000
   Eff  = Dchg / Chg
   Eff2 = Chg.shift(-1) / Dchg
   Ocv  = pivot["Ocv"][3] / 1_000_000
   Temp = pivot["Temp"][2] / 1000
   AvgV = DchgEng / Dchg / mincapacity * 1000

5. df.NewData 구성 (DCIR 모드별 컬럼 수 차이)

6. 전압/전류 추적 (ChgVolt, DchgVolt, ChgSteps, DchgCurr)

7. NaN 행 제거 (Dchg 또는 Chg가 None인 행)
```

### 4.6 `pne_cycle_data()` (L3743–3789)

**메인 진입점** — 위 함수들을 조합:

```python
def pne_cycle_data(raw_file_path, mincapacity, ini_crate, chkir, chkir2, mkdcir):
    # 1. 용량 산정
    mincapacity = pne_min_cap(raw_file_path, mincapacity, ini_crate)
    # 2. SaveEndData 캐시 로드
    save_end_cached, _, _ = _cached_pne_restore_files(raw_file_path)
    # 3. Cycleraw 구성 (CSV 13컬럼 선택)
    Cycleraw = save_end_cached[[27, 2, 10, 11, 8, 20, 45, 15, 17, 9, 24, 29, 6]].copy()
    # 4. .cyc 보충/대체
    # 5. _process_pne_cycleraw() → df.NewData
    return [mincapacity, df]
```

---

## 5. Toyo 사이클 처리

### 5.1 전체 호출 흐름

```
toyo_cycle_data() [L1141]
  ├─→ toyo_min_cap() [L1124]     용량 산정
  └─→ toyo_cycle_import() [L1103]
      └─→ toyo_read_csv() [L1068]   capacity.log 캐시 읽기
```

**핵심 차이**: PNE와 달리 Toyo는 메인 처리가 모두 `toyo_cycle_data()` 내부에서 inline으로 수행됨.

### 5.2 `toyo_read_csv()` (L1068–1090)

| 호출 형태 | 파일 경로 | skiprows | 캐싱 |
|---------|---------|---------|------|
| `toyo_read_csv(path)` | `path\capacity.log` | 0 | **YES** (`cache['capacity_log']`) |
| `toyo_read_csv(path, n)` | `path\%06d` (사이클 번호) | 3 | NO |

### 5.3 `toyo_cycle_import()` (L1103–1122)

**역할**: capacity.log 읽기 → 표준 10컬럼으로 정규화

| 표준 컬럼 | 타입 | 설명 |
|----------|------|------|
| TotlCycle | int | 누적 사이클 번호 |
| Condition | int | 1=충전, 2=방전 |
| Cap[mAh] | float | 사이클 용량 |
| Ocv | float | 개회로 전압 (V) |
| Finish | str | 종료 요인 ("Tim", "Vol") |
| Mode | str | 충방전 모드 |
| PeakVolt[V] | float | 최대 전압 |
| Pow[mWh] | float | 에너지 |
| PeakTemp[Deg] | float | 최고 온도 (°C) |
| AveVolt[V] | float | 평균 전압 |

### 5.4 `toyo_min_cap()` (L1124–1139)

**용량 산정 우선순위**:

```
1. mincapacity != 0  → 입력값 사용
2. cache['min_cap'] 존재  → 캐시 반환
3. 경로에 "mAh" 포함  → name_capacity() 파싱
4. 나머지  → 사이클 1의 max(Current) / inirate
```

### 5.5 `toyo_cycle_data()` (L1141–1305)

**165줄 inline 처리 — 17단계**:

```python
def toyo_cycle_data(raw_file_path, mincapacity, inirate, chkir):
    # 반환: [mincapacity, df]  (df.NewData = 9~13컬럼)
```

#### 단계 1–3: 초기 데이터 로드

```
1. mincapacity = toyo_min_cap(...)
2. Cycleraw = toyo_cycle_import(...).dataraw  (10컬럼)
3. Cycleraw["OriCycle"] = Cycleraw["TotlCycle"]  (11컬럼으로 확대)
```

#### 단계 4: 방전 시작 시 보정 (L1160–1164)

첫 행이 방전이고 두 번째 행이 사이클 1인 경우:
- 모든 방전 TotlCycle -= 1
- 첫 방전 행 삭제

#### 단계 5: 연속 동일 Condition 그룹화 (L1167–1168)

```python
merge_group = ((cond != cond.shift()) | (~cond.isin([1, 2]))).cumsum()
```

> 같은 Condition(1 또는 2)이 연속되면 같은 그룹 번호 할당

#### 단계 6: 충전 피크 전압/스텝 수 사전 저장 (L1187–1201)

병합 전에 충전 데이터 보존:
- `_chg_volt_map`: 그룹별 피크 전압 (TotlCycle → V)
- `_chg_steps_map`: 그룹별 스텝 수 (TotlCycle → int)

#### 단계 7: merge_rows()로 그룹 병합 (L1203–1205)

| Condition | 병합 규칙 |
|-----------|---------|
| 충전 (1) | Cap 합산, Ocv는 첫 행값, 나머지는 마지막 행 |
| 방전 (2) | Cap 합산, Pow 합산, AveVolt 재계산 (Pow/Cap), Ocv 첫 행 |

#### 단계 8–9: 충전 데이터 추출 (L1207–1214)

```python
chgdata = Cycleraw[(Condition == 1)
                   & (Finish != "Vol" 계열)
                   & (Cap > mincapacity/60)]
Chg = chgdata["Cap[mAh]"]
_ChgVolt = _chg_volt_map.reindex(chgdata.index)
```

#### 단계 10–12: DCIR 계산 (L1218–1254)

```python
# DCIR 대상: Finish == "Tim" + Condition == 2 + Cap < mincapacity/60
for cycle in dcir_cycles:
    dcirpro = pd.read_csv(path + "\\%06d" % cycle)   # 사이클별 상세 CSV
    dcircal = dcirpro[dcirpro["Condition"] == 2]      # 방전 구간
    dcir = (V_max - V_min) / I_max × 1e6              # µΩ
```

#### 단계 13: 방전 데이터 추출 (L1256–1263)

```python
Dchgdata = Cycleraw[(Condition == 2) & (Cap > mincapacity/60)]
Dchg, Temp, DchgEng, AvgV, OriCycle = ... (각 Series)
```

#### 단계 15: Chg/Dchg 정렬 매칭 (L1272–1290)

Toyo는 충전/방전 인덱스가 어긋나므로 **위치 기반 재정렬**:

```python
if Dchg.index[0] < Chg.index[0]:
    Dchg = Dchg.iloc[1:]   # 대응 충전 없는 초기 방전 제거
_nmin = min(len(Chg), len(Dchg))
Chg = pd.Series(Chg.values[:_nmin], index=Dchg.index[:_nmin])  # 위치 기반 매핑
```

#### 단계 16: 효율 계산 (L1291–1295)

```python
Eff  = Dchg / Chg           # 방전/충전 효율
Eff2 = Chg.shift(-1) / Dchg # 다음충전/방전 효율
Dchg = Dchg / mincapacity   # 정규화
Chg  = Chg / mincapacity
```

#### 단계 17: df.NewData 구성 (L1297–1308)

```python
df.NewData = pd.DataFrame({
    "Dchg": Dchg, "RndV": Ocv, "Eff": Eff, "Chg": Chg,
    "DchgEng": DchgEng, "Eff2": Eff2, "Temp": Temp,
    "AvgV": AvgV, "OriCyc": OriCycle
})
# + dcir, ChgVolt, ChgSteps (조건부)
```

---

## 6. DCIR 계산 3모드 상세

### 6.1 모드 A: `chkir == True` (일반 DCIR)

**함수**: `_process_pne_cycleraw()` L3394–3397

```python
dcirtemp = Cycleraw[(Condition == 2) & (volmax > 4_100_000)]  # 방전 + 고전압
dcir = dcirtemp.imp / 1000  # µΩ → mΩ
dcir = dcir[~dcir.index.duplicated()]  # 첫 등장만 유지
```

**용도**: SSA, GITT 등 빠른 방전 후 고전압 임펄스 측정

### 6.2 모드 B: `mkdcir == True` (MK DCIR: RSS + 1s 펄스)

**함수**: `_process_pne_cycleraw()` L3398–3489

3개 서브셋 생성:

| 서브셋 | 조건 | 용도 |
|-------|------|------|
| `dcirtemp1` | EndState=78, \|Curr\| >= 0.15C | RSS CCV (충방전 완료 CC) |
| `dcirtemp2` | steptime=100, EndState=64, Condition∈[1,2] | 1s 펄스 CCV |
| `dcirtemp3` | steptime∈{90000,180000,186000,546000}, EndState=64, Condition=3 | RSS OCV (휴지) |

**DCIR 계산공식**:

$$\text{RSS DCIR} = \left| \frac{V_{\text{OCV(dcirtemp3)}} - V_{\text{CC(dcirtemp1)}}}{I_1} \right| \times 10^3 \text{ (mΩ)}$$

$$\text{1s Pulse DCIR} = \left| \frac{V_{\text{pulse(dcirtemp2)}} - V_{\text{CC(dcirtemp1)}}}{I_1 - I_2} \right| \times 10^3 \text{ (mΩ)}$$

#### SOC70 DCIR 추출 (chkir2 활성 시)

사이클당 SOC 포인트 수(mode)에 따라:
- **6개 포인트 (5,20,35,50,65,80%)**: indices `[3::6]` → SOC70 데이터만 추출
- **4개 포인트 (20,40,60,80%)**: indices `[::4]` → 첫 번째부터 추출

### 6.3 모드 C: 기타 (SOC5/50 10s 펄스)

**함수**: `_process_pne_cycleraw()` L3490–3493

```python
dcirtemp = Cycleraw[(Condition == 2) & (steptime <= 6000)]  # 60초 이하 펄스
dcir = dcirtemp.imp / 1000  # µΩ → mΩ
```

### 6.4 Toyo DCIR (파일 기반)

**함수**: `toyo_cycle_data()` L1226–1240

```python
for cycle in dcir_cycles:
    dcirpro = pd.read_csv(path + "\\%06d" % cycle, skiprows=3)
    dcircal = dcirpro[Condition == 2]
    dcir = (V_max - V_min) / I_max × 1e6  # µΩ
```

---

## 7. 사이클 카테고리 분류

### 7.1 `classify_channel_path()` (L1626–1755)

```python
def classify_channel_path(channel_path: str, capacity: float = 0) -> dict | None
```

#### 분류 흐름

```
1. Cycler 타입 판별 (PNE: SaveEndData/.cyc, Toyo: capacity.log)
2. 데이터 로드 (캐시 활용)
3. 사이클 분류: classify_pne_cycles() / classify_toyo_cycles()
4. 카운트 집계: {RPT: n, 가속수명: n, 일반수명: n, ...}
5. 테스트 타입 감지:
   - 우선 1: .sch 파일 (PNE + HAS_SCH_PARSER)
   - 우선 2: CSV 기반 detect_test_type() + detect_schedule_pattern()
```

#### 반환값

```python
{
    'cycler': 'PNE' | 'Toyo',
    'total_cycles': int,
    'counts': {'RPT': n, '가속수명': n, '일반수명': n, ...},
    'classified': [...],           # 전체 사이클 리스트 (탭 저장 시 제거)
    'schedule_pattern': str,
    'test_type': str,
    'sch_info': {...} | None,      # .sch 파싱 결과
    'accel_pattern': {...} | None, # 가속 패턴 감지 결과
    'channel': str,                # 오케스트레이터에서 추가
}
```

---

## 8. 그래프 출력: `graph_output_cycle()`

### 8.1 함수 시그니처 (L598–650)

```python
def graph_output_cycle(
    df, xscale, ylimitlow, ylimithigh, irscale, temp_lgnd,
    colorno, graphcolor, dcir, ax1, ax2, ax3, ax4, ax5, ax6
):
```

### 8.2 6개 Subplot 배치

```
┌────────────────┬────────────────┬────────────────┐
│      ax1       │      ax2       │      ax3       │
│  방전용량 (%)   │  효율(Dchg/Chg)│    온도 (°C)    │
│  Y:[low,high]  │ Y:[0.992,1.004]│   Y:[0, 50]    │
├────────────────┼────────────────┼────────────────┤
│      ax4       │      ax5       │      ax6       │
│   DC-IR (mΩ)   │  효율(Chg/Dchg)│  평균전압 (V)   │
│ Y:[0,120×ir]   │ Y:[0.996,1.008]│ Y:[3.00,4.00]  │
└────────────────┴────────────────┴────────────────┘
```

### 8.3 DCIR 그래프 분기 (ax4)

```
dcir.isChecked() AND dcir2 컬럼 존재? (SOC70 모드)
├─ YES: soc70_dcir (빈 마커) + soc70_rss_dcir (채운 마커)
│       + 대시선 (dcir) + 실선 (rss)
└─ NO:  dcir (채운 마커) + 실선
```

### 8.4 범례 전략 (채널 수 기반)

| 채널 수 | 범례 위치 | 폰트 | ncol |
|--------|---------|------|------|
| > 15 | figure 오른쪽 외부 | x-small | 1 (30개↑: 2) |
| 8~15 | 각 subplot | x-small | 2 |
| < 8 | subplot별 위치 | normal | 1 |

---

## 9. 탭 분기 및 모드 처리

### 9.1 개별 모드 (`radio_indiv = True`)

```
각 group마다 별도 탭 생성
탭명: "0", "1", "2", ...
색상: sub_label별 다른 색 (colorno += 1, 탭 끝에 reset)
범례: sub_label 기반
Figure 폭: 서브폴더 수에 비례
```

### 9.2 통합 모드 (`radio_indiv = False`)

```
모든 group → 1개 탭에 병합
탭명: "0" (단일)
색상: group별 1색 (colorno 연속 증가, reset 없음)
범례: ch_label 기반 (그룹 간 중복 제거)
```

### 9.3 `_finalize_cycle_tab()` (L12259–12331)

```python
def _finalize_cycle_tab(
    self, tab, tab_layout, canvas, toolbar, tab_no,
    channel_map, fig, axes_list, sub_channel_map=None,
    classify_info=None, classify_by_group=None,
    save_context=None, voltage_condition_text=None,
    group_names=None
)
```

처리:
1. classify_info에서 'classified' 리스트 제거 (크기 절감)
2. 채널 컨트롤 버튼 생성 (`_create_cycle_channel_control()`)
3. 분류 정보 바 (`_build_classify_info_label()`)
4. Canvas & 범례 배치
5. tight_layout 조정 (범례 외부 시 18% 우측 여백)

---

## 10. 연결처리 (연결 모드) 상세

### 10.1 활성화 조건

```python
self.chk_link_cycle.toggled → _update_group_separators()
is_link = group.is_link  # _parse_cycle_input()에서 설정
```

### 10.2 연결 모드 처리 흐름 (L13486–13615)

```python
merged = {}  # {sub_label: {'frames': [df, ...], 'colorno': int, 'ch_label': str}}
channel_state = {}  # {sub_label: offset 정보}

for each path:
    for each sub_label (채널):
        # offset 계산 (누적)
        writerowno = offset + last_len
        cyctemp[1].NewData.index += writerowno

        merged[sub_label]['frames'].append(cyctemp[1].NewData)

        # 엑셀 저장 (offset 적용한 행번호)
        _save_cycle_excel_data(..., writerowno, ...)

# 최종 병합
for sub_label, info in merged.items():
    merged_df = pd.concat(info['frames']).sort_index()
    graph_output_cycle(merged_df, ...)  # 병합된 데이터로 그래프
```

### 10.3 비연결 모드 (L13616–13750)

```
for each folder:
    for each sub_label:
        graph_output_cycle(...)   # 독립적 그래프
        _save_cycle_excel_data(...)
        writecolno += 2          # 다음 컬럼
```

### 10.4 연결 vs 비연결 비교

| 항목 | 연결 모드 | 비연결 모드 |
|-----|---------|----------|
| 데이터 병합 | sub_label별 concat | 개별 유지 |
| 인덱스 | 누적 offset (0→n→2n...) | 각 채널 0부터 |
| Excel 저장 | 단일 시트에 연속 행 | 채널별 writecolno 증가 |
| 그래프 | 병합 후 1번 | 채널별 독립 |

---

## 11. 엑셀 저장

### 11.1 `_save_cycle_excel_data()` (L12860–12907)

```python
def _save_cycle_excel_data(self, nd, writecolno, start_row, headername):
```

### 11.2 시트 구성

| 시트명 | X축 데이터 | Y축 데이터 | 저장 조건 |
|-------|----------|----------|---------|
| 방전용량 | OriCyc | Dchg | 항상 |
| Rest End | OriCyc | RndV | 항상 |
| 평균 전압 | OriCyc | AvgV | 항상 |
| 충방효율 | OriCyc | Eff | 항상 |
| 충전용량 | OriCyc | Chg | 항상 |
| 방충효율 | OriCyc | Eff2 | 항상 |
| 방전Energy | OriCyc | DchgEng | 항상 |
| DCIR | OriCyc | dcir | `dcir` 컬럼 존재 시 |
| RSS | OriCyc | dcir (RSS) | mkdcir ✓ + `dcir2` 존재 시 |
| DCIR (1s pulse) | OriCyc | dcir2 | mkdcir ✓ + `dcir2` 존재 시 |
| RSS_OCV | OriCyc | rssocv | mkdcir ✓ + `rssocv` 존재 시 |
| RSS_CCV | OriCyc | rssccv | mkdcir ✓ + `rssccv` 존재 시 |
| SOC70_DCIR | OriCyc | soc70_dcir | mkdcir ✓ + 존재 시 |
| SOC70_RSS | OriCyc | soc70_rss_dcir | mkdcir ✓ + 존재 시 |
| 충전전압 | OriCyc | ChgVolt | `ChgVolt` 컬럼 존재 시 |
| 방전전압 | OriCyc | DchgVolt | `DchgVolt` 컬럼 존재 시 |

### 11.3 Writer 라이프사이클

```
1. 생성 (L13312): pd.ExcelWriter(save_file_name, engine="xlsxwriter")
2. Excel 그룹 쓰기 (L13376): dfoutput.to_excel(writer, "Approval_cycle")
3. 사이클 그룹 쓰기 (L13630): _save_cycle_excel_data() × 채널
4. 종료 (L14106): writer.close()
```

---

## 12. 캐싱 아키텍처

### 12.1 전역 캐시 구조

```python
_channel_cache: dict[str, dict] = {}
# key: 채널 폴더 경로
# value: {
#     'pne_restore': (SaveEndData_df, file_index_list, subfile),
#     'min_cap': int,
#     'capacity_log': pd.DataFrame,
# }
```

### 12.2 캐시 함수

| 함수 | 라인 | 역할 |
|-----|------|------|
| `_get_channel_cache(path)` | L419 | 채널별 캐시 딕셔너리 반환 (없으면 생성) |
| `clear_channel_cache()` | L417 | 전역 캐시 딕셔너리 초기화 |

### 12.3 캐시 키별 사용처

| 캐시 키 | 설정 함수 | 사용 함수 | 설명 |
|---------|---------|---------|------|
| `pne_restore` | `_cached_pne_restore_files()` | `pne_cycle_data()`, `classify_channel_path()` | SaveEndData + 파일인덱스 |
| `min_cap` | `pne_min_cap()`, `toyo_min_cap()` | 동일 함수 (재호출 시) | 공칭 용량 |
| `capacity_log` | `toyo_read_csv()` | `toyo_cycle_import()`, `classify_channel_path()` | capacity.log 전체 |

### 12.4 캐시 라이프사이클

```
_load_all_cycle_data_parallel() 시작
    │
    ├── clear_channel_cache()  ← 전체 초기화
    │
    ├── [병렬 로딩 task #1~N]
    │   ├── pne_min_cap() → cache['min_cap'] 설정
    │   ├── _cached_pne_restore_files() → cache['pne_restore'] 설정
    │   └── toyo_read_csv() → cache['capacity_log'] 설정
    │
    └── [분류 task #1~N]  ← 같은 캐시 재활용
        ├── _cached_pne_restore_files() → cache['pne_restore'] 히트
        └── toyo_read_csv() → cache['capacity_log'] 히트
```

> **핵심**: 로딩과 분류가 같은 캐시를 공유 → CSV 재읽기 방지

---

## 13. DataFrame 컬럼 추적

### 13.1 PNE 컬럼 변환 흐름

```
SaveEndData.csv (47컬럼)
    ↓ [27,2,10,11,8,20,45,15,17,9,24,29,6] 선택
Cycleraw (13컬럼)
    ↓ _process_pne_cycleraw()
    ↓ pivot_table + DCIR 계산 + 전압 추적
df.NewData (9~19컬럼)
```

### 13.2 Toyo 컬럼 변환 흐름

```
capacity.log (10컬럼)
    ↓ toyo_cycle_import() 정규화
Cycleraw (10컬럼)
    ↓ OriCycle 추가
Cycleraw (11컬럼)
    ↓ merge_rows() 병합
    ↓ 필터링 + DCIR + 매칭
df.NewData (9~13컬럼)
```

### 13.3 df.NewData 전체 컬럼 (PNE + Toyo 합산)

| 컬럼 | 타입 | 단위 | PNE | Toyo | 설명 |
|-----|------|------|-----|------|------|
| **Dchg** | float | 배수(%) | ✅ | ✅ | 방전 용량 (정규화) |
| **RndV** | float | V | ✅ | ✅ | REST 종료 전압 |
| **Eff** | float | — | ✅ | ✅ | 효율 (Dchg/Chg) |
| **Chg** | float | 배수(%) | ✅ | ✅ | 충전 용량 (정규화) |
| **DchgEng** | float | Wh(PNE)/mWh(Toyo) | ✅ | ✅ | 방전 에너지 |
| **Eff2** | float | — | ✅ | ✅ | 역효율 (다음Chg/Dchg) |
| **Temp** | float | °C | ✅ | ✅ | 온도 |
| **AvgV** | float | V | ✅ | ✅ | 평균 전압 |
| **OriCyc** | int | — | ✅ | ✅ | 원본 사이클 번호 |
| dcir | float | mΩ | ✅ | ✅ | DC-IR (모드별) |
| dcir2 | float | mΩ | ✅(mkdcir) | ❌ | 1s 펄스 DCIR |
| rssocv | float | V | ✅(mkdcir) | ❌ | RSS OCV |
| rssccv | float | V | ✅(mkdcir) | ❌ | RSS CCV |
| soc70_dcir | float | mΩ | ✅(mkdcir+chkir2) | ❌ | SOC70 DCIR |
| soc70_rss_dcir | float | mΩ | ✅(mkdcir+chkir2) | ❌ | SOC70 RSS DCIR |
| ChgVolt | float | V | ✅ | ✅ | 충전 상한 전압 |
| ChgSteps | int | — | ✅ | ✅ | 충전 스텝 수 |
| DchgVolt | float | V | ✅ | ❌ | 방전 하한 전압 |
| DchgCurr | float | A | ✅ | ❌ | 방전 CC 전류 |

> **굵은 글씨**: 항상 존재하는 필수 9컬럼

---

## 14. PNE vs Toyo 비교

### 14.1 입력 데이터

| 항목 | PNE | Toyo |
|-----|-----|------|
| 주 입력 | SaveEndData.csv (N행 = N 스텝) | capacity.log (N행 = N 사이클) |
| 보조 입력 | .cyc 바이너리 (실시간 보충) | 없음 |
| DCIR 소스 | SaveEndData.csv의 imp 컬럼 | 사이클별 상세 CSV 파일 |
| 캐시 대상 | SaveEndData + 파일인덱스 | capacity.log |

### 14.2 처리 방식

| 항목 | PNE | Toyo |
|-----|-----|------|
| 함수 구조 | 별도 함수 `_process_pne_cycleraw()` | 모두 inline |
| 집계 방식 | `pivot_table(index=TotlCycle)` | `merge_group + merge_rows()` |
| Chg/Dchg 매칭 | 사이클 인덱스 기반 | 위치 기반 (값 배열만 취함) |
| DCIR 계산 | 조건식 (chkir/mkdcir/기타) | 파일 루프 읽기 |
| 단위 | µV, µA, µAh, mC | mV, mA, mAh, °C |
| 코인셀 지원 | ✅ (`is_micro_unit()`) | ❌ |

### 14.3 에러 처리

| 시나리오 | PNE | Toyo |
|---------|-----|------|
| 데이터 미존재 | `[None, df]` 반환 | — |
| 파일 읽기 실패 | try-except 침묵 | 건너뜀 |
| .cyc 파싱 실패 | CSV만 사용 | — |

---

## 15. 미사용 변수 목록

### 15.1 PNE

| 함수 | 변수 | 라인 | 상태 |
|-----|------|------|------|
| `_cyc_to_cycle_df` | `file_size` | L3210 | 선언만, 미사용 |
| `_process_pne_cycleraw` | `ChgCap2` | L3533 | Eff2 계산만, 컬럼 미저장 |
| `_process_pne_cycleraw` | `cyccal` | L3580 | DCIR 인덱싱용이나 디버그 후 불필요할 수 있음 |

### 15.2 Toyo

| 함수 | 변수 | 라인 | 상태 |
|-----|------|------|------|
| `toyo_cycle_import` | `Mode` | capacity.log 컬럼 | 읽기만 함, 미사용 |

### 15.3 DataFrame에서 미사용 컬럼

| 데이터 | 컬럼 | 상태 |
|-------|------|------|
| SaveEndData.csv | [0],[1],[3]~[7],[12]~[14],[16],[18]~[19],[21]~[23],[25]~[26],[28],[30]~[44],[46] | 선택 안 됨 |
| capacity.log | `Mode`, `Finish` | Mode 미사용, Finish는 필터링에만 사용 |

---

## 16. 전체 분기 조건 맵

### 16.1 데이터 소스 분기

| 조건 | 결과 |
|------|------|
| `check_cycler() == True` | PNE 파이프라인 |
| `check_cycler() == False` | Toyo 파이프라인 |
| SaveEndData CSV 존재 + .cyc 존재 | CSV 기반 + .cyc 보충 |
| SaveEndData CSV 없음 + .cyc 존재 | .cyc 단독 재구성 |
| CSV만 존재 | CSV만 사용 |

### 16.2 DCIR 분기 (PNE)

| chkir | mkdcir | 결과 |
|-------|--------|------|
| True | — | 모드 A: 고전압 방전 imp 추출 |
| — | True | 모드 B: RSS + 1s 펄스 3-way |
| False | False | 모드 C: 10s 이하 펄스 |

### 16.3 탭/모드 분기

| radio_indiv | is_link | 결과 |
|------------|---------|------|
| True | False | 개별 탭, 독립 그래프 |
| True | True | 개별 탭, 연결 병합 |
| False | False | 통합 1탭, 독립 그래프 |
| False | True | 통합 1탭, 연결 병합 |

### 16.4 용량 분기

| per_path_cap > 0 | mincapacity != 0 | 경로에 "mAh" | 결과 |
|------------------|------------------|-------------|------|
| ✅ | — | — | 테이블값 사용 |
| ❌ | ✅ | — | 입력값 사용 |
| ❌ | ❌ | ✅ | 경로명 파싱 |
| ❌ | ❌ | ❌ | 첫 사이클 기반 자동 산정 |

### 16.5 기타 분기

| 분기 | 조건 | 동작 |
|------|------|------|
| 코인셀 단위 변환 | `is_micro_unit() == True` | DchgCap, chgCap, Curr ÷ 1000 |
| 루프 마커 감지 | 시간 점프 > 300s OR 패턴 감지 | Condition=8 레코드 추가 |
| CC/CV 판별 | 꼬리 전류 변동률 > 0.05 | CV(EndState=66) vs CC(65) |
| 온도 단위 감지 | 샘플값 > \|200\| | 이미 mC 단위 (÷1 아닌 ÷1000) |
| 방전 시작 보정 (Toyo) | 첫 행=방전 + 두번째=사이클1 | 모든 방전 TotlCycle -= 1 |
| DCIR 시트 조건부 생성 | dcir/dcir2/rssocv/... 컬럼 존재 여부 | 해당 시트만 생성 |

---

## 부록: 주요 변수명-역할 매핑

| 변수 | 타입 | 용도 |
|------|------|------|
| `flatidx_of` | `dict[(gi, pi) → int]` | 그룹+경로 인덱스 → flat 배열 인덱스 |
| `loaded_data` | `dict[(fi, si) → (path, cyctemp)]` | 로딩 결과 전체 |
| `subfolder_map` | `dict[fi → [path, ...]]` | 폴더별 채널 목록 |
| `channel_map` | `dict[ch_label → {...}]` | 범례 중복 제거 (채널 단위) |
| `sub_channel_map` | `dict[sub_label → {...}]` | Artist 추적 (서브폴더 단위) |
| `channel_state` | `dict[sub_label → offset]` | 연결 모드 인덱스 누적 |
| `merged` | `dict[sub_label → frames]` | 연결 모드 프레임 수집 |
| `writecolno` | `int` | 현재 엑셀 컬럼 (2씩 증가) |
| `writerowno` | `int` | 현재 엑셀 행 (연결 모드 offset) |
| `colorno` | `int` | THEME['PALETTE'] 색상 인덱스 |

---

**문서 끝**
