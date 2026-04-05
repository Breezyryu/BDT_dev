# 사이클 분석 & 프로필 분석 로직 설명서

> **작성일**: 2026-04-05
> **대상 파일**: `DataTool_dev/DataTool_optRCD_proto_.py`
> **범위**: Tab 1(사이클데이터) — 사이클 분석 + 프로필 분석 전체 파이프라인

---

## 목차

1. [전체 아키텍처 개요](#1-전체-아키텍처-개요)
2. [사이클 분석 파이프라인](#2-사이클-분석-파이프라인)
   - 2.1 진입점: `unified_cyc_confirm_button()`
   - 2.2 입력 파싱: `_parse_cycle_input()`
   - 2.3 병렬 데이터 로딩: `_load_all_cycle_data_parallel()`
   - 2.4 사이클러 판별: `check_cycler()`
   - 2.5 Toyo 사이클 데이터: `toyo_cycle_data()`
   - 2.6 PNE 사이클 데이터: `pne_cycle_data()`
   - 2.7 그래프 출력: `graph_output_cycle()`
   - 2.8 df.NewData 데이터 구조
3. [프로필 분석 파이프라인](#3-프로필-분석-파이프라인)
   - 3.1 진입점: `unified_profile_confirm_button()`
   - 3.2 코어 엔진: `unified_profile_core()`
   - 3.3 6-Stage 처리 파이프라인
   - 3.4 배치 처리: `unified_profile_batch()`
   - 3.5 DCIR 분석: `dcir_confirm_button()`
   - 3.6 UnifiedProfileResult 데이터 구조
4. [프로필 옵션 시스템](#4-프로필-옵션-시스템)
   - 4.1 4개 옵션 축
   - 4.2 옵션 간 의존성 규칙
   - 4.3 레거시 모드 매핑
5. [논리사이클 매핑 시스템](#5-논리사이클-매핑-시스템)
6. [캐싱 시스템](#6-캐싱-시스템)
7. [함수 호출 맵 (전체)](#7-함수-호출-맵-전체)

---

## 1. 전체 아키텍처 개요

사이클데이터 탭(Tab 1)은 두 가지 독립적인 분석 기능을 제공한다.

```
┌─────────────────────────────────────────────────────────────┐
│  Tab 1: 사이클데이터                                         │
│                                                             │
│  ┌──────────────────────┐  ┌──────────────────────────────┐ │
│  │  사이클 분석           │  │  프로필 분석                   │ │
│  │  (cycle_confirm)      │  │  (ProfileConfirm)            │ │
│  │                       │  │                              │ │
│  │  수백~수천 사이클의     │  │  개별 사이클의 시간/전압/     │ │
│  │  용량·효율·저항 추이    │  │  전류 파형 상세 분석          │ │
│  │  → 수명 트렌드 파악     │  │  → 충방전 프로파일 비교       │ │
│  └──────────────────────┘  └──────────────────────────────┘ │
│                                                             │
│  공통 인프라:                                                │
│  - check_cycler() : PNE/Toyo 판별                            │
│  - 논리사이클 매핑 : 물리TC → 논리사이클 변환                   │
│  - 채널 캐시 : 반복 I/O 방지                                   │
│  - 병렬 로딩 : ThreadPoolExecutor                             │
└─────────────────────────────────────────────────────────────┘
```

### 왜 두 가지 분석이 필요한가?

**사이클 분석**은 "숲"을 보는 것이다. 수백~수천 사이클에 걸친 용량 감소 추이, 효율 변화, 내부저항 증가를 한 눈에 파악하여 셀의 수명 트렌드와 열화 양상을 판단한다.

**프로필 분석**은 "나무"를 보는 것이다. 특정 사이클의 전압-시간 커브, 전류 프로파일, dQ/dV 미분 곡선을 상세히 분석하여 전극 반응 메커니즘, 충전 프로토콜 동작, 열화 모드를 진단한다.

---

## 2. 사이클 분석 파이프라인

### 2.1 진입점: `unified_cyc_confirm_button()` (라인 ~15733)

사이클 분석의 메인 핸들러로, 기존 6개 분석 함수를 통합한 함수다.

#### 전체 실행 흐름

```
[사용자: cycle_confirm 버튼 클릭]
         │
         ▼
① cyc_ini_set()
   → UI 필드에서 설정값 읽기
   → (firstCrate, mincapacity, xscale, ylimithigh, ylimitlow, irscale)
         │
         ▼
② _parse_cycle_input()
   → 입력 모드 판별 (테이블/파일/폴더)
   → list[CycleGroup] 반환
         │
         ▼
③ 그룹 분류
   → Excel 그룹 (신뢰성 테스트 .xls/.xlsx)
   → Folder 그룹 (충방전기 채널 폴더)
         │
         ├── [Excel 그룹] ──────────────────────────┐
         │   xlwings → DataFrame 읽기 → 정규화      │
         │   → graph_cycle()로 직접 플롯             │
         │                                          │
         ├── [Folder 그룹] ─────────────────────────┐│
         │   ④ _load_all_cycle_data_parallel()      ││
         │      → ThreadPoolExecutor 병렬 로딩       ││
         │      → check_cycler() 판별               ││
         │      ├─ PNE → pne_cycle_data()           ││
         │      └─ Toyo → toyo_cycle_data()         ││
         │                                          ││
         │   ⑤ classify_channel_path() (병렬)       ││
         │      → 사이클 카테고리 분류               ││
         │                                          ││
         │   ⑥ 탭 할당                              ││
         │      → 개별 모드: group별 탭              ││
         │      → 통합 모드: 전체 1탭               ││
         │                                          ││
         │   ⑦ graph_output_cycle()                 ││
         │      → 6개 서브플롯 생성                  ││
         │      → _auto_adjust_cycle_axes()          ││
         │      → place_avgrest_labels()             ││
         │      → place_dcir_labels()                ││
         │                                          │
         └── ⑧ 탭 추가 + Excel 저장 (선택)  ────────┘
```

#### 핵심 코드 구조 (의사코드)

```python
def unified_cyc_confirm_button(self):
    # ① 설정 읽기
    firstCrate, mincapacity, xscale, ylimithigh, ylimitlow, irscale = self.cyc_ini_set()
    is_individual = self.radio_indiv.isChecked()  # 개별 vs 통합

    # ② 입력 파싱
    groups = self._parse_cycle_input()

    # ③ Excel vs Folder 분류
    excel_groups = [g for g in groups if g.data_type == 'excel']
    folder_groups = [g for g in groups if g.data_type == 'folder']

    # [Excel 처리]
    if excel_groups:
        fig, axes = plt.subplots(2, 3)
        for g in excel_groups:
            # xlwings로 Excel 읽기 → 정규화 → graph_cycle()
            ...

    # [Folder 처리]
    if folder_groups:
        # ④ 병렬 데이터 로딩
        loaded_data, subfolder_map = self._load_all_cycle_data_parallel(...)

        # ⑤ 사이클 카테고리 분류 (병렬)
        _classify_results = ...  # ThreadPoolExecutor

        # ⑥ 탭 할당
        if is_individual:
            tab_units = [[gi] for gi in range(len(folder_groups))]  # 그룹별 독립 탭
        else:
            tab_units = [list(range(len(folder_groups)))]           # 전체 1탭

        # ⑦ 각 탭에서 그래프 생성
        for tab_idx, group_indices in enumerate(tab_units):
            fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2, 3)
            for gi in group_indices:
                for each_channel in channels:
                    _artists, _color = graph_output_cycle(
                        cyctemp, xscale, ylimitlow, ylimithigh, irscale,
                        lgnd, colorno, graphcolor, self.mkdcir,
                        ax1, ax2, ax3, ax4, ax5, ax6
                    )

            # 축 자동 조정 + 탭 추가
            _auto_adjust_cycle_axes(axes_list, ...)
            canvas = FigureCanvas(fig)
            self.cycle_tab.addTab(tab, tab_name)
```

### 2.2 입력 파싱: `_parse_cycle_input()` (라인 ~15597)

사용자 입력을 `CycleGroup` 리스트로 변환하는 함수다. 3가지 입력 모드를 자동 판별한다.

#### 판별 우선순위

```
① 테이블에 데이터가 있는가? (_has_table_data)
   ├─ YES → 테이블 파싱
   │   ├─ link_mode=True (chk_link_cycle 체크)
   │   │   → 빈 행 = 그룹 구분자
   │   │   → txt/csv 파일 행 자동 확장
   │   │   → 채널 매핑 생성 (channel_link_map)
   │   │
   │   └─ link_mode=False
   │       → 각 행 = 개별 그룹
   │
   └─ NO → 파일 선택 대화상자
       ├─ .xlsx/.xls → Excel 타입 CycleGroup
       ├─ .txt/.csv → 파일 파싱 후 cyclename별 그룹화
       └─ 기타 → 폴더 경로
```

#### CycleGroup 데이터 구조

```python
CycleGroup = namedtuple('CycleGroup', [
    'data_type',    # 'excel' | 'folder'
    'paths',        # list[str] — 데이터 경로 목록
    'label',        # str — 그룹 이름 (범례용)
    'capacity',     # float — 지정 용량 (0이면 자동)
    'channels',     # list[str] | None — 채널 필터
])
```

**왜 이렇게 복잡한가?**
실제 업무에서 데이터 입력 방식이 다양하기 때문이다. 단일 폴더를 직접 지정할 때도 있고, 여러 제품의 여러 채널을 한 번에 비교해야 할 때도 있다. 테이블 모드는 후자를 지원하며, txt/csv 파일은 경로 목록을 미리 작성해둔 배치 분석용이다.

### 2.3 병렬 데이터 로딩: `_load_all_cycle_data_parallel()` (라인 ~15284)

모든 채널의 사이클 데이터를 ThreadPoolExecutor로 병렬 로딩하는 함수다.

#### 처리 흐름

```python
def _load_all_cycle_data_parallel(self, all_data_folder, mincapacity, firstCrate,
                                   dcirchk, dcirchk_2, mkdcir, max_workers=None,
                                   per_path_capacities=None):

    # ① 채널 캐시 초기화
    clear_channel_cache()

    # ② 작업 큐 빌드
    tasks = []
    subfolder_map = {}
    for folder_idx, folder_path in enumerate(all_data_folder):
        subfolders = [d for d in os.scandir(folder_path)
                      if _is_channel_folder(d)]        # "Pattern" 폴더 제외
        subfolder_map[folder_idx] = subfolders
        for sub_idx, subfolder in enumerate(subfolders):
            cap = per_path_capacities[folder_idx] if per_path_capacities else mincapacity
            tasks.append((folder_idx, sub_idx, subfolder.path, cap))

    # ③ 최적 worker 수 결정
    n_workers = calc_optimal_workers(len(tasks)) if max_workers is None else max_workers

    # ④ 병렬 실행
    results = {}
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = {
            executor.submit(_load_cycle_data_task, task): task
            for task in tasks
        }
        for future in as_completed(futures):
            fi, si, path, cyctemp = future.result()
            results[(fi, si)] = (path, cyctemp)
            # 진행률 업데이트 (0~50%)

    return results, subfolder_map
```

#### `_load_cycle_data_task()` 내부

```python
def _load_cycle_data_task(task_info):
    fi, si, channel_path, cap = task_info
    is_pne = check_cycler(channel_path)
    if is_pne:
        cyctemp = pne_cycle_data(channel_path, cap, inirate, chkir, chkir2, mkdcir)
    else:
        cyctemp = toyo_cycle_data(channel_path, cap, inirate, chkir)
    return (fi, si, channel_path, cyctemp)
```

**왜 병렬 처리가 필요한가?**
하나의 테스트 그룹에 32~128개 채널이 있을 수 있고, 각 채널의 사이클 데이터 파싱에 수 초가 소요된다. 순차 처리 시 수 분이 걸리던 작업을 병렬화하여 체감 시간을 크게 단축한다.

### 2.4 사이클러 판별: `check_cycler()` (라인 ~392)

데이터 폴더 구조로 PNE와 Toyo 사이클러를 구분한다.

```python
def check_cycler(raw_file_path):
    """충방전기 데이터 폴더로 PNE와 Toyo를 구분한다.

    판별 기준 (우선순위):
    1. Pattern 폴더 존재 → PNE
    2. Restore 폴더 내 SaveData CSV 존재 → PNE
    3. 그 외 → Toyo
    """
    # 기준 1: Pattern 폴더
    if os.path.isdir(raw_file_path + "\\Pattern"):
        return True   # PNE

    # 기준 2: Restore/SaveData
    restore_dir = raw_file_path + "\\Restore"
    if os.path.isdir(restore_dir):
        files = os.listdir(restore_dir)
        if any("SaveData" in f for f in files):
            return True   # PNE

    return False  # Toyo
```

**왜 폴더 구조로 판별하는가?**
PNE 사이클러는 바이너리 데이터를 `Pattern/`, `Restore/` 폴더 구조로 저장하고, Toyo 사이클러는 사이클 번호(`000001`, `000002`, …)로 된 CSV 파일을 직접 저장한다. 이 구조적 차이가 가장 신뢰성 높은 판별 기준이다.

### 2.5 Toyo 사이클 데이터: `toyo_cycle_data()` (라인 ~2413)

Toyo 사이클러의 CSV 데이터를 파싱하여 사이클별 요약 정보를 생성한다.

#### 10단계 처리 파이프라인

```
[원시 CSV 파일]
      │
      ▼
① toyo_min_cap() — 기준 용량 산정
   └─ 파일명에서 "xxxmAh" 추출 또는 첫 사이클 최대전류/C-rate로 계산
      │
      ▼
② toyo_cycle_import() — capacity.log CSV 로딩
   └─ 전체 사이클의 요약 행(Condition, Cap, Ocv, AvgV, Temp 등) 로딩
      │
      ▼
③ 고아 방전(Orphan Discharge) 제거
   └─ 첫 행이 방전(Condition==2)이면서 다음 행이 사이클1이면 제거
   └─ 이유: 테스트 시작 전 방전이 불완전 사이클로 기록되는 경우 방지
      │
      ▼
④ 연속 동일 Condition 병합 (merge_rows)
   └─ 다단 CC 충전 (2C→1.6C→1.3C→1C) → 1개 충전 행으로 통합
   └─ 충전: 용량 합산, OCV는 첫 행 값
   └─ 방전: 용량+에너지 합산, AvgV = 에너지/용량으로 재계산
      │
      ▼
⑤ 충전/방전 분리 + 용량 필터링
   └─ Condition==1: 충전, Condition==2: 방전
   └─ 필터: Cap > mincapacity/60 (= 정상 사이클만, 매우 작은 DCIR 펄스 제외)
      │
      ▼
⑥ DC-IR 계산 (작은 방전 사이클에서)
   └─ mincapacity/60 이하 + 시간종료 방전 = DCIR 펄스로 판별
   └─ 각 펄스의 프로필 CSV 로딩 → ΔV/ΔI 계산 → μΩ 단위
      │
      ▼
⑦ 효율 계산
   └─ Eff  = Dchg / Chg (동일 사이클 방전/충전)
   └─ Eff2 = Chg(n+1) / Dchg(n) (교차 사이클)
      │
      ▼
⑧ 정규화
   └─ Dchg = Dchg / mincapacity (용량비, 1.0 = 100%)
   └─ Chg  = Chg / mincapacity
      │
      ▼
⑨ df.NewData DataFrame 구성 (10개 컬럼)
      │
      ▼
⑩ 논리사이클 매핑 (toyo_build_cycle_map)
   └─ 물리 사이클 번호 → 논리 사이클 번호 변환
   └─ "Cycle" 컬럼 삽입
```

#### 핵심 알고리즘: 연속 Condition 병합

```python
# Condition 시퀀스: [1, 1, 1, 2, 1, 1, 2, ...]
# 다단 CC 충전에서 각 단계가 별도 행으로 기록됨
# → 연속된 동일 Condition을 하나로 합치는 것이 핵심

cond_series = Cycleraw["Condition"]
# cumsum 트릭: 값이 바뀔 때마다 그룹 번호 증가
merge_group = ((cond_series != cond_series.shift()) | (~cond_series.isin([1, 2]))).cumsum()

def merge_rows(group):
    if len(group) == 1:
        return group.iloc[0]   # 단일 행 → 그대로
    cond = group["Condition"].iloc[0]
    result = group.iloc[-1].copy()   # 마지막 행 기준 (최종 전압 등)
    if cond == 1:  # 충전
        result["Cap[mAh]"] = group["Cap[mAh]"].sum()   # 용량 합산
        result["Ocv"] = group["Ocv"].iloc[0]            # 첫 행 OCV 유지
    elif cond == 2:  # 방전
        result["Cap[mAh]"] = group["Cap[mAh]"].sum()
        result["Pow[mWh]"] = group["Pow[mWh]"].sum()
        result["AveVolt[V]"] = result["Pow[mWh]"] / result["Cap[mAh]"]  # 재계산
    return result

Cycleraw = Cycleraw.groupby(merge_group).apply(merge_rows)
```

**왜 이 병합이 필요한가?**
Toyo 사이클러는 CC-CV 충전의 각 단계(CC 2C → CC 1.6C → CC 1.3C → CC 1C → CV)를 모두 별도 행으로 기록한다. 사이클 분석에서는 이들을 합산하여 "1회 충전"으로 취급해야 한다. `cumsum` 트릭으로 연속된 동일 Condition을 한 그룹으로 묶어 효율적으로 병합한다.

### 2.6 PNE 사이클 데이터: `pne_cycle_data()` (라인 ~5747)

PNE 사이클러의 바이너리/CSV 데이터를 파싱한다.

#### 6단계 처리 파이프라인

```
[PNE 채널 폴더]
      │
      ▼
① pne_min_cap() — 기준 용량 산정
      │
      ▼
② SaveEndData CSV 로딩 (_cached_pne_restore_files)
   └─ Restore 폴더의 SaveEndData 파일에서 사이클 요약 정보 추출
   └─ 컬럼 인덱스 기반: [27]=TotlCycle, [2]=Condition, [10]=chgCap, [11]=DchgCap, ...
      │
      ▼
③ .cyc 파일 보충 (_cyc_to_cycle_df)
   └─ SaveData CSV보다 최신인 진행 중 사이클 데이터 보충
   └─ CSV 최대 사이클 이후의 신규 사이클만 concat
      │
      ▼
④ pne_build_cycle_map() — 논리사이클 매핑 생성
      │
      ▼
⑤ _process_pne_cycleraw() — DCIR 계산 + df.NewData 구성
   └─ 충전/방전 분리 (Condition==1/2)
   └─ 용량 필터링 (mincapacity/60 기준)
   └─ DCIR 계산 (일반/Pulse/MK 방식 선택)
   └─ 효율·정규화·DataFrame 구성
      │
      ▼
⑥ cycle_map 저장 → df.cycle_map 속성
```

**Toyo와의 차이점:**

| 항목 | Toyo | PNE |
|------|------|-----|
| 데이터 형식 | 사이클별 개별 CSV | 통합 SaveEndData CSV + .cyc |
| 용량 기록 | capacity.log 요약 | SaveEndData 바이너리 인덱스 |
| DCIR 계산 | 프로필 CSV에서 ΔV/ΔI | _process_pne_cycleraw 내부 계산 |
| 실시간 보충 | 불필요 (CSV 즉시 생성) | .cyc 파일로 최신 데이터 보충 |

### 2.7 그래프 출력: `graph_output_cycle()` (라인 ~1870)

사이클 데이터를 6개 서브플롯에 산점도로 그리는 함수다.

#### 6개 서브플롯 구성

```
┌────────────────────┬────────────────────┬────────────────────┐
│  ax1: 방전용량비     │  ax2: 방전/충전 효율 │  ax3: 온도           │
│  Dchg (정규화)      │  Eff (%)           │  Temp (°C)         │
│  ○ 산점도           │  ○ 산점도           │  ○ 산점도           │
├────────────────────┼────────────────────┼────────────────────┤
│  ax4: DC-IR         │  ax5: 충전/방전 효율 │  ax6: 전압           │
│  dcir / soc70_dcir │  Eff2 (%)          │  RndV(●) + AvgV(○) │
│  (mΩ, 스케일 적용)  │  ○ 산점도           │  ●산점도 + ○빈마커    │
└────────────────────┴────────────────────┴────────────────────┘
```

```python
def graph_output_cycle(df, xscale, ylimitlow, ylimithigh, irscale, temp_lgnd,
                       colorno, graphcolor, dcir, ax1, ax2, ax3, ax4, ax5, ax6):
    color = graphcolor[colorno % len(THEME['PALETTE'])]  # 팔레트 순환
    artists = []

    # 주요 지표 6개를 각 축에 플롯
    artists.append(graph_cycle(df.NewData.index, df.NewData.Dchg, ax1, ...))   # 방전용량비
    artists.append(graph_cycle(df.NewData.index, df.NewData.Eff, ax2, ...))    # 효율
    artists.append(graph_cycle(df.NewData.index, df.NewData.Temp, ax3, ...))   # 온도
    artists.append(graph_cycle(df.NewData.index, df.NewData.Eff2, ax5, ...))   # 교차효율
    artists.append(graph_cycle(df.NewData.index, df.NewData.RndV, ax6, ...))   # 휴지전압 (채운 마커)
    artists.append(graph_cycle_empty(df.NewData.index, df.NewData.AvgV, ax6, ...))  # 평균전압 (빈 마커)

    # DCIR 조건부 처리
    if dcir.isChecked() and hasattr(df.NewData, "dcir2"):
        # SOC70 DCIR (Rss + 1s)
        artists.append(graph_cycle_empty(..., df.NewData.soc70_dcir, ax4, ...))
        artists.append(graph_cycle(..., df.NewData.soc70_rss_dcir, ax4, ...))
    else:
        # 일반 DCIR
        artists.append(graph_cycle(..., df.NewData.dcir, ax4, ...))

    return artists, color
```

**ax6의 이중 마커 패턴:**
RndV(휴지 후 전압)는 채운 마커(●), AvgV(평균 방전 전압)는 빈 마커(○)로 구분한다. 같은 축에 두 지표를 겹쳐 표시하면 전압 관련 추이를 한 눈에 비교할 수 있다. RndV는 OCV 근사값이고, AvgV는 부하 상태의 평균 전압이므로, 둘의 차이가 벌어지면 내부 저항 증가를 의미한다.

### 2.8 df.NewData 데이터 구조

사이클 분석의 핵심 데이터 구조다. Toyo와 PNE 모두 동일한 컬럼으로 통일된다.

| 컬럼 | 설명 | 단위 | 물리적 의미 |
|------|------|------|------------|
| `Cycle` | 논리 사이클 번호 | - | 매핑된 실제 분석 단위 |
| `Dchg` | 방전 용량비 | 무차원 (1.0=100%) | 셀 수명의 1차 지표 |
| `Chg` | 충전 용량비 | 무차원 | CE 계산용 |
| `Eff` | 방전/충전 효율 | 무차원 | 쿨롱 효율 (CE) |
| `Eff2` | 충전(n+1)/방전(n) | 무차원 | 교차 사이클 효율 |
| `Temp` | 온도 | °C | 열화 가속 인자 |
| `RndV` | 휴지 후 전압 | V | OCV 근사값 |
| `AvgV` | 평균 방전 전압 | V | 에너지 효율 지표 |
| `DchgEng` | 방전 에너지 | Wh | 에너지 열화 추적 |
| `OriCyc` | 원본 물리 사이클 | - | 원시 데이터 추적용 |
| `dcir` | DC-IR (내부저항) | mΩ | 임피던스 열화 추적 |

---

## 3. 프로필 분석 파이프라인

### 3.1 진입점: `unified_profile_confirm_button()` (라인 ~18348)

프로필 분석의 메인 UI 핸들러다. 4개 옵션 조합에 따라 데이터를 로딩하고 렌더링한다.

#### 전체 실행 흐름

```
[사용자: ProfileConfirm 버튼 클릭]
         │
         ▼
① _read_profile_options()
   → 4개 옵션 읽기 (data_scope, axis_mode, continuity, include_rest)
         │
         ▼
② _map_options_to_legacy_mode()
   → 렌더링 분기용 레거시 모드 결정
   → "step" | "chg" | "dchg" | "cycle_soc" | "continue"
         │
         ▼
③ _init_confirm_button()
   → 공통 초기화 (firstCrate, mincapacity, CycleNo, smoothdegree, cutoff 등)
         │
         ▼
④ _get_max_logical_cycle()
   → 각 채널의 최대 논리사이클 조회 → CycleNo 유효성 검증
         │
         ▼
⑤ _setup_file_writer()
   → Excel 저장 설정 (saveok 체크 시)
         │
         ▼
⑥ _load_all_unified_parallel()
   → 병렬 배치 로딩 (unified_profile_batch 호출)
   → UnifiedProfileResult 배열 반환
         │
         ▼
⑦ 호환성 변환
   → UnifiedProfileResult → 레거시 DataFrame 형식 래핑
   → _compat_data() 적용
         │
         ▼
⑧ 모드별 플롯 콜백 선택
   → step모드: graph_profile (V vs Time/SOC)
   → chg/dchg: graph_profile + dQ/dV 축 추가
   → cycle_soc: graph_profile (전체 사이클)
         │
         ▼
⑨ _profile_render_loop()
   → 통합 렌더링 (사이클별 루프, 축 설정, 범례, 탭 생성)
```

### 3.2 코어 엔진: `unified_profile_core()` (라인 ~1258)

프로필 분석의 핵심 로직으로, 기존 5개 프로필 함수(step/rate/chg/dchg/continue)를 통합한 공통 엔진이다.

#### 함수 시그니처

```python
def unified_profile_core(
    raw_file_path: str,
    cycle_range: tuple[int, int],   # (시작 논리사이클, 끝 논리사이클)
    mincapacity: float,
    inirate: float,
    *,
    data_scope: str = "charge",     # "charge" | "discharge" | "cycle"
    axis_mode: str = "soc",         # "soc" | "time"
    continuity: str = "overlay",    # "overlay" | "continuous"
    include_rest: bool = False,
    calc_dqdv: bool = False,
    smooth_degree: int = 0,
    cutoff: float = 0.0,
    cycle_map: dict | None = None,
) -> UnifiedProfileResult:
```

### 3.3 6-Stage 처리 파이프라인

이 파이프라인이 프로필 분석의 핵심이다. 원시 데이터에서 최종 분석 결과까지 6단계로 변환한다.

```
┌─────────────────────────────────────────────────────────────┐
│ Stage 1: 사이클러 판별 & 원시 로딩                            │
│                                                             │
│ check_cycler() → PNE/Toyo 판별                               │
│   ├─ PNE → pne_min_cap() + _unified_pne_load_raw()          │
│   └─ Toyo → toyo_min_cap() + _unified_toyo_load_raw()       │
│                                                             │
│ 출력: 표준화된 DataFrame (Condition, Voltage, Current, ...)   │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 2: Condition 필터링                                    │
│ _unified_filter_condition(df, data_scope, include_rest)      │
│                                                             │
│ data_scope별 필터:                                            │
│   "charge"    → Condition ∈ [9, 1]  (CC충전 + CCCV)         │
│   "discharge" → Condition ∈ [9, 2]  (CC + 방전)             │
│   "cycle"     → Condition ∈ [9, 1, 2]  (전부)               │
│   include_rest=True → 추가로 Condition==3 (휴지) 포함         │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 3: 정규화                                              │
│ _unified_normalize_pne() 또는 _unified_normalize_toyo()      │
│                                                             │
│ PNE 정규화:                                                  │
│   Voltage: μV → V (/1,000,000)                               │
│   Current: μA → mA (is_micro_unit 판별)                      │
│   Capacity: μAh → 0~1 정규화                                 │
│   Temp: mK → °C (/1,000)                                     │
│   Crate: Current / mincapacity                               │
│                                                             │
│ Toyo 정규화:                                                 │
│   Time_s: PassTime 리셋 보정 (음수 diff → 0 클리핑)           │
│   Capacity: 시간적분 (mAh → 정규화)                           │
│   Crate: Current / mincapacity                               │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 4: 스텝 병합                                           │
│ _unified_merge_steps(df, data_scope)                         │
│                                                             │
│ charge/discharge 모드:                                       │
│   → 멀티스텝 시간/용량 누적 연결                               │
│   for step in range(stepmin+1, stepmax+1):                   │
│       prev_max_time = parts[-1]["Time_s"].max()              │
│       part["Time_s"] += prev_max_time                        │
│       part[cap_col] += prev_max_cap                          │
│                                                             │
│ cycle 모드: 병합 불필요 (시간순 정렬만)                        │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 5: X축 & SOC 계산                                      │
│ _unified_calculate_axis(df, axis_mode, continuity)           │
│                                                             │
│ Overlay 모드:                                                │
│   → 각 사이클의 시작점을 0으로 리셋                            │
│   → cycle 모드: Condition 경계에 NaN 행 삽입 (선 끊기)        │
│                                                             │
│ Continuous 모드:                                             │
│   → 사이클 간 시간 연속 유지 (TotTime 기반)                   │
│                                                             │
│ SOC 계산:                                                    │
│   charge → SOC = ChgCap (0→1)                                │
│   discharge → SOC = DchgCap (DOD 방향)                       │
│   cycle → SOC = ChgCap - DchgCap (양방향)                    │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 6: 파생값 계산                                          │
│ _unified_calculate_dqdv(df, smooth_degree)                   │
│                                                             │
│ delvol = Voltage.diff(periods=smooth_degree)                 │
│ delcap = SOC.diff(periods=smooth_degree)                     │
│ dqdv = delcap / delvol                                       │
│ dvdq = delvol / delcap                                       │
│                                                             │
│ 휴지 구간(Condition==3) → NaN 처리                            │
│ smooth_degree==0 → 자동 (len/30)                             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ 최종: UnifiedProfileResult 반환                              │
│   .df       : 최종 DataFrame                                 │
│   .mincapacity : 기준 용량                                    │
│   .columns  : 유효 컬럼 목록                                  │
│   .metadata : 옵션, 사이클러 타입, 사이클맵 등                 │
└─────────────────────────────────────────────────────────────┘
```

#### Stage별 핵심 알고리즘 상세

**Stage 3 — PNE 정규화에서 `is_micro_unit()` 판별:**

```python
def is_micro_unit(raw_file_path):
    """PNE21/PNE22 또는 코인셀 모드면 μA/μAh 단위 사용"""
    return ('PNE21' in raw_file_path) or ('PNE22' in raw_file_path) or _coincell_mode
```

PNE 사이클러 중 PNE21/PNE22 모델은 소전류 측정용으로 μA/μAh 단위를 사용하고, 다른 모델(PNE25 등)은 mA/mAh를 사용한다. 이 구분 없이 정규화하면 값이 1000배 어긋난다.

**Stage 5 — Overlay에서 NaN 행 삽입:**

```python
# cycle 모드에서 Condition이 바뀌는 경계에 NaN 삽입
# → matplotlib가 선을 끊어서 충전/방전 구간이 분리됨
if data_scope == "cycle" and continuity == "overlay":
    cond_changes = df["Condition"].diff().ne(0)
    for boundary_idx in cond_changes[cond_changes].index:
        nan_row = pd.Series(np.nan, index=df.columns)
        # NaN 행 삽입 → 플롯에서 선이 끊어짐
```

### 3.4 배치 처리: `unified_profile_batch()` (라인 ~1588)

여러 사이클의 프로필을 일괄 처리하는 함수다.

```python
def unified_profile_batch(raw_file_path, cycle_list, mincapacity, inirate,
                          *, options, cycle_map=None):
    results = {}

    if options["continuity"] == "continuous":
        # 사이클 범위 단위 처리 → 시간 연속
        result = unified_profile_core(
            raw_file_path, (cycle_list[0], cycle_list[-1]),
            mincapacity, inirate,
            continuity="continuous", **options
        )
        results[(cycle_list[0], cycle_list[-1])] = [mincapacity, result]
    else:
        # 사이클별 개별 처리 → 오버레이
        for cyc in cycle_list:
            result = unified_profile_core(
                raw_file_path, (cyc, cyc),
                mincapacity, inirate,
                continuity="overlay", **options
            )
            results[cyc] = [mincapacity, result]

    return results
```

**Overlay vs Continuous의 차이:**

| 모드 | 동작 | 용도 |
|------|------|------|
| Overlay | 각 사이클 독립 처리, X축 0에서 시작 | 사이클 간 프로필 형태 비교 |
| Continuous | 사이클 간 시간 연속 | 장기 테스트 전체 파형 확인 |

### 3.5 DCIR 분석: `dcir_confirm_button()` (라인 ~19009)

DCIR(직류내부저항) 전용 분석으로, PNE 사이클러에서만 동작한다.

```
[사용자: DCIRConfirm 버튼 클릭]
         │
         ▼
① Profile_ini_set() → firstCrate, mincapacity, CycleNo 등 초기화
         │
         ▼
② pne_path_setting() → 경로 설정 (all_data_folder, all_data_name)
         │
         ▼
③ 각 폴더별 순회:
   │
   ├─ pne_dcir_chk_cycle() → DCIR 측정 사이클 확인
   │
   ├─ 각 DCIR 사이클별:
   │   │
   │   ├─ pne_dcir_Profile_data() → 프로필 데이터 추출
   │   │   └─ 시간: [0.0, 0.3, 1.0, 10.0, 20.0]초 기준 DCIR 계산
   │   │
   │   ├─ 4개 축 그래프 생성:
   │   │   ├─ OCV/CCV vs SOC
   │   │   ├─ DCIR vs SOC (R₀, R₁, R₁₀, R₂₀)
   │   │   ├─ 전류/전압 시간 프로필
   │   │   └─ SOC별 DCIR 상세
   │   │
   │   └─ Excel/CSV 저장
   │
   └─ 탭 추가 (chg/dchg 구분)
```

**DCIR 시간 기준:**

| 시간 | DCIR 명칭 | 물리적 의미 |
|------|-----------|------------|
| 0.0s | - | 기준점 (펄스 인가 직전) |
| 0.3s | R₀.₃ | 순수 옴 저항 + 초기 전하이동 |
| 1.0s | R₁ | 옴 + 전하이동 저항 (BDT "dcir2") |
| 10.0s | R₁₀ | + 고체상 확산 기여 |
| 20.0s | R₂₀ | 정상 상태 DCIR (BDT "dcir") |

### 3.6 UnifiedProfileResult 데이터 구조

```python
@dataclass
class UnifiedProfileResult:
    df: pd.DataFrame            # 최종 분석 데이터
    mincapacity: float          # 기준 용량 (mAh)
    columns: list[str]          # 유효 컬럼 목록
    cycfile_soc: pd.DataFrame | None = None   # .cyc 파일 SOC 데이터 (선택)
    metadata: dict = field(default_factory=dict)
```

#### DataFrame 컬럼 명세

**기본 컬럼 (모든 모드):**

| 컬럼 | 설명 | 단위 |
|------|------|------|
| `TimeMin` | 경과 시간 | 분 |
| `SOC` | 정규화 용량 | 0~1 |
| `Voltage` / `Vol` | 전압 | V |
| `Crate` | C-rate | 무차원 |
| `Temp` | 온도 | °C |
| `Cycle` | 논리사이클 번호 | - |
| `Condition` | 1=충전, 2=방전, 3=휴지 | - |

**dQ/dV 활성 시 추가:**

| 컬럼 | 설명 | 단위 |
|------|------|------|
| `Energy` | 에너지 | Wh |
| `dQdV` | dQ/dV 미분값 | Ah/V |
| `dVdQ` | dV/dQ 미분값 | V/Ah |

**Continuous 모드 추가:**

| 컬럼 | 설명 | 단위 |
|------|------|------|
| `TimeSec` | 경과 시간 | 초 |
| `Curr` | 전류 | A |

#### metadata 구조

```python
metadata = {
    "cycler_type": "PNE" | "TOYO",
    "cycle_range": (start, end),
    "cycle_map": {논리번호: 물리번호 또는 (시작TC, 끝TC)},
    "options": {
        "data_scope": "charge" | "discharge" | "cycle",
        "axis_mode": "soc" | "time",
        "continuity": "overlay" | "continuous",
        "include_rest": bool,
        "calc_dqdv": bool
    },
    "error": "오류 메시지"  # 데이터 없을 때만 존재
}
```

---

## 4. 프로필 옵션 시스템

### 4.1 4개 옵션 축

사용자는 Tab 1 좌측 패널의 "프로필 옵션" 탭에서 4개 독립 옵션을 설정한다.

```
┌─────────────────────────────────────────────┐
│ 데이터 범위 (data_scope)                      │
│   ○ 사이클 (cycle)  ← 충전+방전+휴지 전체    │
│   ○ 충전 (charge)   ← 충전 스텝만            │
│   ○ 방전 (discharge) ← 방전 스텝만           │
├─────────────────────────────────────────────┤
│ 연속성 (continuity)                           │
│   ○ 오버레이 (overlay) ← 각 사이클 독립      │
│   ○ 이어서 (continuous) ← 시간 연속          │
├─────────────────────────────────────────────┤
│ X축 (axis_mode)                               │
│   ○ SOC(DOD) ← 용량 기준                     │
│   ○ 시간 (time) ← 경과 시간 기준             │
├─────────────────────────────────────────────┤
│ 휴지 포함 (include_rest)                      │
│   □ 휴지 포함 ← 체크 시 Rest 구간도 표시     │
└─────────────────────────────────────────────┘
```

### 4.2 옵션 간 의존성 규칙

일부 옵션 조합은 물리적으로 무의미하거나 기술적으로 지원 불가하다. UI 핸들러가 자동으로 제약을 적용한다.

#### 의존성 다이어그램

```
data_scope ──→ continuity
   │              │
   │              ▼
   │         axis_mode
   │
   └─ scope가 charge/discharge면 → continuity는 overlay로 강제
      scope가 cycle이면 → continuity 선택 가능

continuity ──→ axis_mode
   └─ continuous면 → axis_mode는 time으로 강제
      (SOC + continuous 조합은 무의미)

axis_mode ──→ continuity
   └─ SOC면 → continuity는 overlay로 강제
```

#### 핸들러 코드

```python
def _profile_opt_scope_changed(self, btn_id, checked):
    """데이터 범위 변경 시 연속성 옵션 조정"""
    if not checked:
        return
    if btn_id == 0:  # 사이클
        # 연속성 옵션 활성화 (사이클 모드만 continuous 허용)
        self.profile_cont_overlay.setEnabled(True)
        self.profile_cont_continuous.setEnabled(True)
    else:  # 충전 또는 방전
        # 오버레이 강제
        self.profile_cont_overlay.setChecked(True)
        self.profile_cont_continuous.setEnabled(False)

def _profile_opt_axis_changed(self, btn_id, checked):
    """X축 변경 시 연속성 옵션 조정"""
    if not checked:
        return
    if btn_id == 0:  # SOC
        # SOC 모드에서는 오버레이 강제
        self.profile_cont_overlay.setChecked(True)
        self.profile_cont_continuous.setEnabled(False)

def _profile_opt_cont_changed(self, btn_id, checked):
    """연속성 변경 시 X축 옵션 조정"""
    if not checked:
        return
    if btn_id == 1:  # 이어서 (continuous)
        # 시간 축 강제
        self.profile_axis_time.setChecked(True)
        self.profile_axis_soc.setEnabled(False)
```

#### 유효 조합 매트릭스

| data_scope | axis_mode | continuity | 유효? | 용도 |
|------------|-----------|------------|-------|------|
| charge | soc | overlay | ✅ | 충전 프로필 비교 (기본) |
| charge | time | overlay | ✅ | 충전 시간 프로필 |
| discharge | soc | overlay | ✅ | 방전 프로필 비교 |
| discharge | time | overlay | ✅ | 방전 시간 프로필 |
| cycle | soc | overlay | ✅ | 풀사이클 SOC 프로필 |
| cycle | time | overlay | ✅ | 풀사이클 시간 프로필 |
| cycle | time | continuous | ✅ | 연속 시간 프로필 |
| charge | soc | continuous | ❌ | → overlay로 강제 |
| cycle | soc | continuous | ❌ | → overlay로 강제 |
| * | * | continuous + soc | ❌ | → time으로 강제 |

### 4.3 레거시 모드 매핑

옵션 조합은 `_map_options_to_legacy_mode()`에 의해 렌더링용 레거시 모드 문자열로 변환된다.

```python
def _map_options_to_legacy_mode(options):
    """4개 옵션 → 레거시 모드 문자열"""
    scope = options["data_scope"]
    cont = options["continuity"]
    axis = options["axis_mode"]

    if cont == "continuous":
        return "continue"          # 연속 프로필
    if scope == "charge":
        return "chg"               # 충전 프로필
    if scope == "discharge":
        return "dchg"              # 방전 프로필
    if scope == "cycle" and axis == "soc":
        return "cycle_soc"         # 풀사이클 SOC
    return "step"                  # 기본 (시간축 프로필)
```

**왜 레거시 모드가 필요한가?**
데이터 처리는 `unified_profile_core()`로 통합되었지만, 그래프 렌더링은 모드별로 축 설정, 범례 위치, 추가 축(dQ/dV 등)이 다르다. 레거시 모드 문자열은 이 렌더링 분기를 결정하는 키로 사용된다.

---

## 5. 논리사이클 매핑 시스템

### 왜 필요한가?

충방전기가 기록하는 "물리 사이클 번호"(TotlCycle)와 실제 분석에서 의미있는 "논리 사이클 번호"가 다른 경우가 빈번하다.

**예시: GITT 시험**
물리적으로는 100개 사이클(짧은 펄스 + 긴 휴지)이 기록되지만, 논리적으로는 이들이 1번의 "GITT 스윕"이다.

**예시: 다단 충전**
CC 2C → CC 1.6C → CC 1.3C → CC 1C → CV 4.2V가 각각 별도 사이클로 기록되지만, 논리적으로는 1번의 "충전"이다.

### 매핑 구조

```python
cycle_map = {
    논리사이클번호: 물리사이클번호 또는 (시작TC, 끝TC),
    1: 1,           # 1:1 매핑 (일반 시험)
    2: 2,
    3: (50, 99),    # 1:다 매핑 (GITT 스윕)
    4: 100,
    ...
}
```

### Toyo 매핑: `toyo_build_cycle_map()` (라인 ~2638)

```
capacity.log 읽기
    │
    ▼
연속 동일 Condition 벡터 그룹화
    │
    ▼
Pass 1: 방전 기반 — 충전+방전+(휴지) = 1 논리사이클
    │
    ▼
Pass 2: 충전 전용 사이클 (방전 없이 끝난 충전)
    │
    ▼
시작 파일 정렬 → 논리사이클 번호 부여
    │
    ▼
필터: mincapacity/60 이상만 유효 사이클
```

### PNE 매핑: `pne_build_cycle_map()` (라인 ~2892)

두 가지 전략을 자동 선택한다.

```
판별 로직:
    │
    ├─ .sch 파일 sweep_mode 확인 (최상위 기준)
    │
    ├─ 데이터 휴리스틱:
    │   sig_ratio = 유의TC(Cap > mincap/60) 비율
    │   has_both_ratio = 충방전 쌍 보유 비율
    │
    └─ 최종 결정:
        _use_general = (sch_sweep is False) or
                       (sig_ratio ≥ 0.5 and has_both_ratio ≥ 0.3)

    ├─ 일반 시험 (가속수명, 율별):
    │   → TotlCycle 1:1 매핑
    │
    └─ 스윕 시험 (GITT, DCIR):
        → 방향 기반 그룹핑
        → 매핑 값: tuple(start_TC, end_TC)
```

**왜 자동 판별이 중요한가?**
같은 PNE 사이클러라도 시험 종류에 따라 데이터 구조가 완전히 다르다. 가속수명 시험은 사이클 단위 분석이 자연스럽지만, GITT/HPPC 시험은 수십 개의 물리 사이클이 1개의 논리 단위다. 사용자가 매번 수동으로 지정하지 않아도 패턴 분석으로 자동 판별한다.

---

## 6. 캐싱 시스템

반복 I/O를 방지하는 전역 캐시 시스템이다.

```python
_channel_cache: dict[str, dict] = {}   # 전역 캐시

def _get_channel_cache(raw_file_path: str) -> dict:
    """채널별 캐시 가져오기 (없으면 생성)"""
    if raw_file_path not in _channel_cache:
        _channel_cache[raw_file_path] = {}
    return _channel_cache[raw_file_path]
```

#### 캐시 항목

| 키 | 저장 내용 | 활용 시점 |
|----|----------|----------|
| `min_cap` | 산정된 최소 용량 | 같은 채널 재분석 시 재계산 방지 |
| `capacity_log` | Toyo capacity.log DataFrame | 사이클+프로필 양쪽에서 사용 |
| `save_end_cached` | PNE SaveEndData DataFrame | 사이클+프로필 양쪽에서 사용 |
| `file_index_list` | PNE 파일 인덱스 목록 | 프로필 로딩 시 파일 탐색 최적화 |

**캐시 수명:**
`clear_channel_cache()`가 `_load_all_cycle_data_parallel()` 시작 시 호출되어 이전 세션의 캐시를 클리어한다. 하나의 분석 세션(cycle_confirm 또는 ProfileConfirm 1회 실행) 내에서만 캐시가 유효하다.

---

## 7. 함수 호출 맵 (전체)

### 사이클 분석 호출 트리

```
unified_cyc_confirm_button()                    [메인 핸들러]
├── cyc_ini_set()                               [UI 설정 읽기]
│   └── set_coincell_mode()
├── _parse_cycle_input()                        [입력 파싱]
│   ├── _has_table_data()
│   ├── _get_table_row_groups()
│   ├── _expand_txt_to_groups()
│   ├── _parse_channel_str()
│   └── _parse_capacity_value()
├── _load_all_cycle_data_parallel()             [병렬 로딩]
│   ├── clear_channel_cache()
│   ├── calc_optimal_workers()
│   ├── _is_channel_folder()
│   └── _load_cycle_data_task()
│       ├── check_cycler()                      [사이클러 판별]
│       ├── toyo_cycle_data()                   [Toyo 데이터]
│       │   ├── toyo_min_cap()
│       │   │   └── name_capacity()
│       │   ├── toyo_cycle_import()
│       │   └── toyo_build_cycle_map()
│       └── pne_cycle_data()                    [PNE 데이터]
│           ├── pne_min_cap()
│           ├── _cached_pne_restore_files()
│           ├── _cyc_to_cycle_df()
│           ├── pne_build_cycle_map()
│           └── _process_pne_cycleraw()
├── classify_channel_path()                     [카테고리 분류 (병렬)]
├── graph_output_cycle()                        [그래프 출력]
│   ├── graph_cycle()
│   └── graph_cycle_empty()
├── _auto_adjust_cycle_axes()                   [축 자동 조정]
├── place_avgrest_labels()                      [라벨 배치]
└── place_dcir_labels()
```

### 프로필 분석 호출 트리

```
unified_profile_confirm_button()                [메인 핸들러]
├── _read_profile_options()                     [옵션 읽기]
├── _map_options_to_legacy_mode()               [레거시 모드 매핑]
├── _init_confirm_button()                      [공통 초기화]
├── _get_max_logical_cycle()                    [사이클 범위 검증]
├── _setup_file_writer()                        [저장 설정]
├── _load_all_unified_parallel()                [병렬 배치 로딩]
│   └── unified_profile_batch()
│       └── unified_profile_core()              [코어 엔진]
│           ├── check_cycler()
│           ├── pne_min_cap() / toyo_min_cap()
│           ├── pne_build_cycle_map() / toyo_build_cycle_map()
│           ├── _unified_pne_load_raw() / _unified_toyo_load_raw()
│           ├── _unified_filter_condition()     [Stage 2]
│           ├── _unified_normalize_pne/toyo()   [Stage 3]
│           ├── _unified_merge_steps()          [Stage 4]
│           ├── _unified_calculate_axis()       [Stage 5]
│           └── _unified_calculate_dqdv()       [Stage 6]
├── _compat_data()                              [호환성 변환]
└── _profile_render_loop()                      [통합 렌더링]
    └── graph_profile()

dcir_confirm_button()                           [DCIR 전용]
├── Profile_ini_set()
├── pne_path_setting()
├── pne_dcir_chk_cycle()
├── pne_dcir_Profile_data()
├── graph_soc_continue()
├── graph_soc_dcir()
├── graph_continue()
└── graph_dcir()
```

### 탭 리셋

```
cycle_tab_reset_confirm_button()
├── _collapse_all_classify_popups()
└── tab_delete(self.cycle_tab)

profile_tab_reset_confirm_button()
├── _collapse_all_classify_popups()
└── tab_delete(self.cycle_tab)
```

---

## 부록: 주요 라인 번호 참조

> **주의**: 라인 번호는 2026-04-05 기준이며, 코드 수정에 따라 변동될 수 있다. `grep -n "def 함수명"` 으로 최신 위치를 확인할 것.

| 함수 | 라인 (대략) | 역할 |
|------|------------|------|
| `name_capacity()` | ~336 | 파일명에서 용량 추출 |
| `check_cycler()` | 392 | PNE/Toyo 판별 |
| `is_micro_unit()` | ~512 | μA 단위 판별 |
| `_get_channel_cache()` | ~526 | 캐시 관리 |
| `UnifiedProfileResult` | 644 | 프로필 결과 데이터클래스 |
| `_unified_pne_load_raw()` | ~667 | PNE 원시 로딩 |
| `_unified_toyo_load_raw()` | ~798 | Toyo 원시 로딩 |
| `_unified_normalize_pne()` | ~897 | PNE 정규화 |
| `_unified_normalize_toyo()` | ~961 | Toyo 정규화 |
| `_unified_filter_condition()` | ~1025 | Condition 필터링 |
| `_unified_merge_steps()` | ~1069 | 스텝 병합 |
| `_unified_calculate_axis()` | ~1121 | X축/SOC 계산 |
| `_unified_calculate_dqdv()` | ~1210 | dQ/dV 계산 |
| `unified_profile_core()` | 1258 | 프로필 코어 엔진 |
| `unified_profile_batch()` | ~1588 | 프로필 배치 처리 |
| `graph_output_cycle()` | 1870 | 사이클 그래프 출력 |
| `graph_profile()` | ~2181 | 프로필 그래프 출력 |
| `toyo_min_cap()` | ~2396 | Toyo 용량 산정 |
| `toyo_cycle_data()` | 2413 | Toyo 사이클 데이터 |
| `toyo_build_cycle_map()` | ~2638 | Toyo 사이클맵 |
| `pne_build_cycle_map()` | ~2892 | PNE 사이클맵 |
| `pne_cycle_data()` | 5767 | PNE 사이클 데이터 |
| `pne_dcir_Profile_data()` | ~6066 | PNE DCIR 프로필 |
| `_load_all_cycle_data_parallel()` | ~15284 | 병렬 사이클 로딩 |
| `_parse_cycle_input()` | ~15597 | 입력 파싱 |
| `unified_cyc_confirm_button()` | 15763 | 사이클 분석 메인 |
| `cyc_ini_set()` | ~16606 | 사이클 초기 설정 |
| `cycle_tab_reset_confirm_button()` | ~16658 | 사이클 탭 리셋 |
| `profile_tab_reset_confirm_button()` | ~16686 | 프로필 탭 리셋 |
| `_profile_opt_scope_changed()` | ~18252 | 범위 옵션 핸들러 |
| `_profile_opt_axis_changed()` | ~18271 | 축 옵션 핸들러 |
| `_profile_opt_cont_changed()` | ~18286 | 연속성 옵션 핸들러 |
| `unified_profile_confirm_button()` | 18358 | 프로필 분석 메인 |
| `dcir_confirm_button()` | 19019 | DCIR 분석 메인 |
