# 사이클 분석 & 프로필 분석 — 데이터 처리 파이프라인 상세 문서

> **작성일**: 2026-03-27  
> **대상 파일**: `DataTool_dev/DataTool_optRCD_proto_.py`  
> **목적**: 사이클 탭의 두 가지 분석(Cycle / Profile) 전체 데이터 흐름을 정리하고, 통합 가능성과 성능 병목을 분석한다.

---

## 목차

1. [전체 아키텍처 개요](#1-전체-아키텍처-개요)
2. [PNE vs Toyo — 사이클러별 차이](#2-pne-vs-toyo--사이클러별-차이)
3. [경로 그룹 시스템 (Path Grouping)](#3-경로-그룹-시스템-path-grouping)
4. [사이클 분석 파이프라인](#4-사이클-분석-파이프라인)
5. [프로필 분석 파이프라인](#5-프로필-분석-파이프라인)
6. [개별 탭 vs 통합 탭](#6-개별-탭-vs-통합-탭)
7. [범례 처리 및 CH 제어 팝업](#7-범례-처리-및-ch-제어-팝업)
8. [데이터프레임 컬럼 사전](#8-데이터프레임-컬럼-사전)
9. [데이터 저장/내보내기 로직](#9-데이터-저장내보내기-로직)
10. [메모리 관리 — 데이터 생명주기](#10-메모리-관리--데이터-생명주기)
11. [성능 상세 분석](#11-성능-상세-분석)
12. [Cycle ↔ Profile 파이프라인 통합 가능성 분석](#12-cycle--profile-파이프라인-통합-가능성-분석)

---

## 1. 전체 아키텍처 개요

사이클데이터 탭(`CycTab`)에는 두 가지 독립적인 분석 파이프라인이 존재한다:

```
┌─────────────────────────────────────────────────────────────────┐
│                         사이클데이터 탭                           │
├──────────────────────────┬──────────────────────────────────────┤
│  [분석 옵션] 서브탭        │  [프로필 옵션] 서브탭                  │
│                          │                                      │
│  cycle_confirm 버튼  ──→  │  StepConfirm                        │
│  → Cycle 분석 실행        │  ChgConfirm                         │
│                          │  DchgConfirm         ──→             │
│  ■ 용량 추이 6축 그래프    │  RateConfirm           Profile 분석   │
│  ■ 사이클 카테고리 분류    │  ContinueConfirm                     │
│  ■ 충방전 패턴 분석       │  DCIRConfirm                         │
│                          │                                      │
│                          │  ■ 시계열 프로파일 그래프               │
│                          │  ■ dQ/dV, dV/dQ 미분 분석             │
│                          │  ■ DCIR 분석                          │
├──────────────────────────┴──────────────────────────────────────┤
│  [결과 출력 영역] cycle_tab (QTabWidget) ← 동적 탭 추가           │
└─────────────────────────────────────────────────────────────────┘
```

### 공통 입력 소스

두 파이프라인 모두 **동일한 UI 요소**에서 경로/설정을 읽는다:

| UI 위젯 | 용도 | 두 파이프라인 공유 |
|---------|------|:--:|
| `cycle_path_table` | 경로 입력 테이블 (5행 × 4열) | ✅ |
| `ratetext` | C-rate / 용량(mAh) 입력 | ✅ |
| `radio_indiv` / `radio_overall` | 개별/통합 모드 | Cycle만 |
| `CycProfile` / `CellProfile` / `AllProfile` | 프로필 모드 | Profile만 |
| `stepnum` | 스텝 번호 / 사이클 번호 목록 | Profile만 |

---

## 2. PNE vs Toyo — 사이클러별 차이

### 2.1 사이클러 판별 (line ~391)

```python
def check_cycler(raw_file_path: str) -> bool:
    """PNE/Toyo 구분. True=PNE, False=Toyo.
    
    판별 기준: 경로 내에 'Pattern' 서브폴더가 존재하면 PNE.
    """
    return os.path.isdir(os.path.join(raw_file_path, "Pattern"))
```

### 2.2 폴더 구조 비교

```
■ PNE 채널 폴더 구조                    ■ Toyo 채널 폴더 구조
Channel_folder/                         Channel_folder/
├── Pattern/                            ├── Summary.csv        ← 사이클 요약
│   └── schedule.sch                    ├── 000001             ← DCIR 프로파일
├── Restore/                            ├── 000002
│   ├── SaveEndData.csv  ← 핵심 요약    ├── ...
│   ├── SaveData_0001.csv ← 프로파일    └── capacity.log       ← 사이클 카테고리
│   ├── SaveData_0002.csv
│   └── savingFileIndex_start.csv
└── (기타 로그)
```

### 2.3 핵심 데이터 파일 비교

| 항목 | PNE | Toyo |
|------|-----|------|
| **사이클 요약 파일** | `Restore/SaveEndData.csv` | `Summary.csv` |
| **인코딩** | `cp949` | `cp949` 또는 `utf-8` |
| **헤더** | 없음 (숫자 인덱스) | 있음 (컬럼명) |
| **프로파일 파일** | `SaveData_NNNN.csv` (여러 파일 이어붙이기) | `NNNNNN` (사이클별 1파일) |
| **카테고리 분류 소스** | `SaveEndData.csv` col[2] StepType | `capacity.log` Condition 컬럼 |
| **스케줄 파일** | `Pattern/*.sch` (바이너리) | 없음 |
| **단위 체계** | μV, μA, 0.001℃, 0.01초 | V, A, ℃, 초 |

### 2.4 사이클 카테고리 분류 기준

#### PNE 분류 (`classify_pne_cycles`, line ~1322)

SaveEndData에서 `StepType==8` (루프마커) 행 제외 후, 사이클별 스텝 조합을 분석:

| 조건 | 카테고리 | 설명 |
|------|---------|------|
| 충전+방전 포함, `n_charge >= 2` | **가속수명** | 다단계 CC-CV 충방전 |
| 충전+방전 포함, `EndState==78` | **Rss** | 내부저항 측정 사이클 |
| 충전+방전 포함, `n_charge == 1` | **RPT** | 정기 성능 평가 |
| 만충 → 방전펄스 반복 | **GITT** | 갈바노스태틱 간헐적 적정 |
| 방전만 존재 | **initial** | 초기 방전 사이클 |

#### Toyo 분류 (`classify_toyo_cycles`, line ~1405)

`capacity.log`의 Condition 컬럼 기준:

| 조건 | 카테고리 |
|------|---------|
| 충전 행 0개 | **initial** |
| 충전 행 1개 | **RPT** |
| 충전 행 2개 이상 | **가속수명** |

---

## 3. 경로 그룹 시스템 (Path Grouping)

### 3.1 CycleGroup 데이터 클래스 (line ~226)

모든 입력 경로는 `CycleGroup` 단위로 관리된다:

```python
@dataclass
class CycleGroup:
    name: str                    # 범례/탭 표시명 (예: "ATL B8 RT")
    paths: list[str]             # 데이터 폴더 경로 목록
    path_names: list[str]        # 경로별 별칭 (표시용)
    is_link: bool = False        # 연결 여부 (paths 2개 이상 → True)
    data_type: str = 'folder'    # 'folder' | 'excel'
    file_idx: int = 0            # 소스 파일 인덱스 (통합탭 그룹핑 기준)
    source_file: str = ''        # 원본 경로 파일명
    per_path_channels: list = [] # [[ch1, ch2], [ch3]] path별 채널 필터
    channel_link_map: dict = {}  # {원본채널: 통합채널} 연결 매핑
    per_path_capacities: list = []  # [float, ...] 테이블 입력 용량
```

### 3.2 경로 입력 → CycleGroup 변환 (`_parse_cycle_input`, line ~12581)

```
┌──────────────────────────────────────────┐
│           cycle_path_table (UI)          │
│  ┌──────┬────────────┬────────┬───────┐  │
│  │ 이름 │   경로     │  채널  │ 용량  │  │
│  ├──────┼────────────┼────────┼───────┤  │
│  │ A    │ Y:\PNE\... │032,073 │ 2335  │  ← 행0: CycleGroup 0
│  │ B    │ Y:\PNE\... │032,073 │ 2335  │  ← 행1: CycleGroup 0 (연결시)
│  │      │            │        │       │  ← 빈 행 = 그룹 구분자 (연결모드)
│  │ C    │ Y:\PNE\... │ -      │ 2935  │  ← 행3: CycleGroup 1
│  │      │            │        │       │  │
│  └──────┴────────────┴────────┴───────┘  │
└──────────────────────────────────────────┘
```

**테이블 컬럼 규칙:**

| 열(Col) | 내용 | 자동 채우기 |
|---------|------|----------|
| 0 | 경로명 (범례 표시) | basename에서 `mAh_` 이후 텍스트 추출 |
| 1 | 데이터 폴더 전체 경로 | 필수 입력 |
| 2 | 채널 필터 (`032,073` 등, `-`는 무시) | 비어있으면 전체 채널 |
| 3 | 용량(mAh) | 비어있으면 폴더명에서 숫자 추출 |

**개별 모드** (`chk_link_cycle` 미체크):
- 각 행 = 독립된 CycleGroup
- 연결 없음 (paths에 경로 1개씩)

**연결 모드** (`chk_link_cycle` 체크):
- 빈 행을 그룹 구분자로 사용
- 같은 블록의 행들 → `is_link=True`로 하나의 CycleGroup에 합침
- 연결된 경로의 사이클 데이터는 순서대로 이어붙여 하나의 연속 데이터로 처리

### 3.3 3단계 경로 계층 구조

```
경로그룹 (folder_groups)                     ← CycleGroup 리스트
  └── 그룹0: CycleGroup(name="ATL B8 RT")
        └── paths: ["Y:\실험1", "Y:\실험2"]   ← 연결 경로 (is_link=True)
              └── 채널: [032], [073], [074]    ← 각 경로 내 채널 서브폴더
                    └── 사이클: 1~400cyc        ← 연결 후 합산

경로그룹 (CycleGroup)
    ↓  (1:N)
  채널그룹 (subfolder_map에서 추적)
    ↓  (1:N)
  사이클그룹 (classify_channel_path 결과로 분류)
```

### 3.4 인덱스 매핑 체계

사이클 분석에서 데이터를 추적하기 위한 3개 딕셔너리:

```python
# (1) flat_idx_of: (그룹번호, 경로번호) → 평탄화 인덱스
#     CycleGroup의 paths를 1차원 배열로 펼침
flat_idx_of = {}
all_paths = []
for gi, g in enumerate(folder_groups):
    for pi, p in enumerate(g.paths):
        flat_idx_of[(gi, pi)] = len(all_paths)
        all_paths.append(p)

# 예시: folder_groups = [그룹0(2paths), 그룹1(1path)]
# all_paths = [path_0_0, path_0_1, path_1_0]
# flat_idx_of = {(0,0):0, (0,1):1, (1,0):2}

# (2) subfolder_map: 평탄화인덱스 → [채널경로1, 채널경로2, ...]
subfolder_map = {
    0: ["Y:\실험1\[032]", "Y:\실험1\[073]"],
    1: ["Y:\실험2\[032]", "Y:\실험2\[073]"],
    2: ["Y:\실험3\[105]"],
}

# (3) _classify_results: 평탄화인덱스 → {채널인덱스: classify결과}
_classify_results = {
    0: {0: {'cycler':'PNE', 'total_cycles':400, ...},
        1: {'cycler':'PNE', 'total_cycles':400, ...}},
    1: {0: {...}, 1: {...}},
}
```

**역방향 변환:**
```python
# 그룹 gi, 경로 pi에 해당하는 채널 목록 찾기:
fi = flat_idx_of[(gi, pi)]          # → 평탄화 인덱스
channels = subfolder_map[fi]         # → [채널경로, ...]
classify = _classify_results[fi][j]  # → j번째 채널의 분류 결과
```

---

## 4. 사이클 분석 파이프라인

### 4.1 전체 흐름도

```
unified_cyc_confirm_button() 클릭 (line ~12751)
│
├── (1) cyc_ini_set() — UI 설정값 읽기
│     ├── 용량(mAh), 배율 → mincapacity, firstCrate
│     ├── Y축 범위 → ylimitlow, ylimithigh
│     ├── X축 범위 → xscale (0=자동)
│     ├── DCIR 스케일 → irscale
│     └── DCIR 모드 → dcir1, dcir2, mkdcir
│
├── (2) is_individual = radio_indiv.isChecked()
│
├── (3) _parse_cycle_input() — 경로 파싱
│     └── → folder_groups: list[CycleGroup]
│
├── (4) _autofill_table_empty_cells() — 테이블 자동 채우기
│
├── ┌── [Excel 그룹 처리] (data_type=='excel')
│   │   └── 신뢰성 현황 xlsx → 승인수명용 6축 플롯
│   │
│   └── [Folder 그룹 처리] (data_type=='folder')
│       │
│       ├── (5) 평탄화 인덱스 구성 (flat_idx_of, all_paths)
│       │
│       ├── (6) _load_all_cycle_data_parallel()  ◀ PerfSection('데이터 로딩')
│       │     ├── ThreadPoolExecutor (채널 단위 병렬)
│       │     ├── PNE: pne_cycle_data(channel_path, ...)
│       │     └── Toyo: toyo_cycle_data(channel_path, ...)
│       │     → results: {(fi, si): (path, cyctemp)}
│       │     → subfolder_map: {fi: [ch_path, ...]}
│       │
│       ├── (7) classify_channel_path()  ◀ PerfSection('사이클 카테고리 분류')
│       │     ├── classify_pne_cycles() 또는 classify_toyo_cycles()
│       │     ├── analyze_accel_pattern() — 가속수명 패턴 분석
│       │     └── _track_accel_voltage_changes_pne() — 전압변경 트래킹
│       │     → _classify_results: {fi: {si: result_dict}}
│       │
│       ├── (8) 콘솔 요약 출력 (그룹별, 패턴 중복 제거)
│       │
│       ├── (9) tab_units 결정 (개별/통합)
│       │
│       └── (10) 탭별 반복
│             ├── fig 생성: 2×3 subplot (ax1~ax6)
│             ├── 채널별 데이터 플롯 (graph_cycle)
│             ├── _auto_adjust_cycle_axes() — 축 자동조정
│             ├── channel_map 구성
│             ├── _finalize_cycle_tab() — 탭 + 위젯 조립
│             └── → cycle_tab에 탭 추가
│
└── progressBar.setValue(100)
```

### 4.2 데이터 로딩 상세 (`_load_all_cycle_data_parallel`, line ~12407)

```python
# 병렬 처리 아키텍처
tasks = []
for fi, cyclefolder in enumerate(all_paths):
    subfolder = [채널 폴더들 스캔]
    for si, channel_path in enumerate(subfolder):
        task = (channel_path, mincap, firstCrate, dcir1, dcir2, mkdcir, is_pne, fi, si)
        tasks.append(task)

max_workers = calc_optimal_workers(len(tasks))  # CPU코어 기반 최적화
with ThreadPoolExecutor(max_workers=max_workers) as executor:
    for future in as_completed(futures):
        fi, si, folder_path, cyctemp = future.result()
        results[(fi, si)] = (folder_path, cyctemp)
# → 진행률: 0~50%
```

**반환값 `cyctemp` 구조:**
```python
cyctemp = (mincapacity_value, df_object)
# cyctemp[0] = float: 기준 용량 (정규화 분모)
# cyctemp[1].NewData = DataFrame: 사이클별 요약 데이터
```

### 4.3 6축 그래프 구조

```
┌────────────────┬────────────────┬────────────────┐
│     ax1        │     ax2        │     ax3        │
│  방전용량비     │  충방 효율     │  온도           │
│  Y: 0.65~1.05  │  Y: 0.992~1.004│  Y: 0~50       │
│  X: Cycle No   │  X: Cycle No   │  X: Cycle No   │
├────────────────┼────────────────┼────────────────┤
│     ax4        │     ax5        │     ax6        │
│  DC-IR (mΩ)    │  방충 효율     │  전압 (V)      │
│  Y: 0~120×scale│  Y: 0.996~1.008│  Y: 3.0~4.0    │
│  X: Cycle No   │  X: Cycle No   │  X: Cycle No   │
└────────────────┴────────────────┴────────────────┘

※ xscale=0이면 _auto_adjust_cycle_axes()가 데이터 범위에 맞춰 자동 조정
※ ax6에는 RndV(Rest 전압)와 AvgV(평균 전압) 2개 시리즈가 오버레이
```

**X축 자동 범위 규칙** (`_auto_adjust_cycle_axes`, line ~660):

| 데이터 최대 사이클 | X축 상한 | 틱 간격 |
|:--:|:--:|:--:|
| < 400 | 100 단위 올림 | 50 |
| 400~799 | 100 단위 올림 | 100 |
| 800~1499 | 100 단위 올림 | 150 |
| 1500~2999 | 100 단위 올림 | 350 |
| 3000~5999 | 100 단위 올림 | 450 |
| ≥ 6000 | 100 단위 올림 | 850 |

---

## 5. 프로필 분석 파이프라인

### 5.1 6개 분석 버튼 비교

| 버튼 | 함수 (line) | 데이터 타입 | 축 구조 | 주요 특징 |
|------|:--:|:--:|:--:|------|
| **Step** | `step_confirm_button` (~14409) | 다단계 충방전 | 2×3 (6축) | 여러 스텝 이어붙인 시계열 |
| **Rate** | `rate_confirm_button` (~14616) | 율별 프로파일 | 2×3 (6축) | 시간 vs 용량/전류/온도 |
| **Chg** | `chg_confirm_button` (~14879) | 충전 프로파일 | 2×3 (6축) | SOC vs 전압, dQ/dV 포함 |
| **Dchg** | `dchg_confirm_button` (~15159) | 방전 프로파일 | 2×3 (6축) | DOD vs 전압, dQ/dV 포함 |
| **Continue** | `continue_confirm_button` (~15435) | 연속 시계열 | 2×3 (6축) | stepnum 파싱, OCV/CCV |
| **DCIR** | `dcir_confirm_button` (~15752) | DCIR 임피던스 | 2×2 (4축) | SOC vs OCV/DCIR/RSS |

### 5.2 공통 초기화 흐름

모든 프로필 분석은 동일한 초기화를 거친다:

```
*_confirm_button() 클릭
│
├── (1) _init_confirm_button() — 공통 설정값 읽기
│     ├── firstCrate: C-rate (정규화 기준)
│     ├── mincapacity: 최소 용량 (mAh)
│     ├── CycleNo: 사이클 번호 배열 (stepnum에서 파싱)
│     ├── smoothdegree: dQ/dV 평활도
│     ├── dqscale, dvscale: dQ/dV 등 그래프 스케일
│     └── folders, names: 입력 폴더/별칭
│
├── (2) CycProfile / CellProfile / AllProfile 모드 결정
│
├── (3) 병렬 데이터 로딩 (_load_all_profile_data_parallel)
│     └── 채널 × 사이클 조합별 병렬 로딩
│
├── (4) 모드별 반복 + 플롯
│     ├── CycProfile: 채널별 탭, 사이클 오버레이
│     ├── CellProfile: 사이클별 탭, 채널 오버레이
│     └── AllProfile: 단일 탭, 전체 오버레이
│
└── (5) _finalize_plot_tab() + 범례/CH제어 연결
```

### 5.3 stepnum 파싱 규칙

`stepnum` 텍스트 필드에서 사이클/스텝 번호를 파싱:

```
입력: "2 3-5 8 10-12"

파싱 결과:
  "2"    → CycleNo = [2]
  "3-5"  → CycleNo = [3, 4, 5]
  "8"    → CycleNo = [8]
  "10-12"→ CycleNo = [10, 11, 12]

※ 공백 구분, 하이픈(-) = 범위 지정
※ Continue 분석: 스텝 번호로 해석
※ 기타 분석: 사이클 번호로 해석
```

### 5.4 3가지 프로필 모드 비교

```
■ CycProfile (사이클 프로필)
  ┌───────────┐  ┌───────────┐
  │ 탭0: CH032│  │ 탭1: CH073│  ← 채널별 탭 생성
  │           │  │           │
  │ ── cyc010 │  │ ── cyc010 │  ← 같은 채널의 사이클들을 오버레이
  │ ── cyc020 │  │ ── cyc020 │
  │ ── cyc030 │  │ ── cyc030 │
  └───────────┘  └───────────┘
  
■ CellProfile (셀 프로필)
  ┌───────────┐  ┌───────────┐
  │ 탭0: cyc10│  │ 탭1: cyc20│  ← 사이클별 탭 생성
  │           │  │           │
  │ ── CH032  │  │ ── CH032  │  ← 같은 사이클의 채널들을 오버레이
  │ ── CH073  │  │ ── CH073  │
  │ ── CH074  │  │ ── CH074  │
  └───────────┘  └───────────┘

■ AllProfile (전체 프로필)
  ┌──────────────────────────┐
  │ 탭0: ALL                 │  ← 단일 탭
  │                          │
  │ ── ATL_B8 CH032 cyc010   │  ← 모든 폴더×채널×사이클 오버레이
  │ ── ATL_B8 CH032 cyc020   │
  │ ── ATL_B8 CH073 cyc010   │
  │ ── SDI_M2 CH105 cyc010   │
  └──────────────────────────┘
```

### 5.5 프로필별 축 배치

#### Step / Rate Confirm

```
┌────────────────┬────────────────┬────────────────┐
│     ax1        │     ax2        │     ax3        │
│  Time - Vol    │  Time - Crate  │  Time - SOC    │
├────────────────┼────────────────┼────────────────┤
│     ax4        │     ax5        │     ax6        │
│  Time - Temp   │  (미사용/2차)  │  (미사용/2차)  │
└────────────────┴────────────────┴────────────────┘
```

#### Chg Confirm

```
┌────────────────┬────────────────┬────────────────┐
│     ax1        │     ax2        │     ax3        │
│  SOC - Vol     │  Voltage-dQ/dV │  SOC - Vol(2nd)│
│  (충전곡선)     │  (미분용량)     │                │
├────────────────┼────────────────┼────────────────┤
│     ax4        │     ax5        │     ax6        │
│  SOC - dV/dQ   │  SOC - Crate   │  SOC - Temp    │
│  (역미분)       │                │                │
└────────────────┴────────────────┴────────────────┘
```

#### Dchg Confirm

```
┌────────────────┬────────────────┬────────────────┐
│     ax1        │     ax2        │     ax3        │
│  DOD - Vol     │  dQ/dV - Vol   │  DOD - Vol(2nd)│
├────────────────┼────────────────┼────────────────┤
│     ax4        │     ax5        │     ax6        │
│  DOD - dV/dQ   │  DOD - Crate   │  DOD - Temp    │
└────────────────┴────────────────┴────────────────┘
```

#### Continue Confirm

```
┌────────────────┬────────────────┬────────────────┐
│     ax1        │     ax2        │     ax3        │
│  Time - Vol    │  Time - Crate  │  Time - SOC    │
├────────────────┼────────────────┼────────────────┤
│     ax4        │     ax5        │     ax6        │
│  Time-Vol+OCV  │  SOC - OCV/CCV │  Time - Temp   │
└────────────────┴────────────────┴────────────────┘
```

#### DCIR Confirm (2×2)

```
┌────────────────┬────────────────┐
│     ax1        │     ax3        │
│  SOC - OCV     │  Volt - SOC    │
│  SOC - rOCV    │                │
│  SOC - CCV     │                │
├────────────────┼────────────────┤
│     ax2        │     ax4        │
│  SOC - DCIR    │  OCV - DCIR    │
│  (0.1s/1s/10s  │                │
│   /20s/RSS)    │                │
└────────────────┴────────────────┘
```

### 5.6 PNE vs Toyo 프로필 로딩 함수 매핑

| 프로필 | Toyo 함수 (line) | PNE 함수 (line) |
|--------|:-:|:-:|
| Step | `toyo_step_Profile_data` (~2625) | `pne_step_Profile_data` (~3359) |
| Rate | `toyo_rate_Profile_data` (~2680) | `pne_rate_Profile_data` (~3405) |
| Chg | `toyo_chg_Profile_data` (~2733) | `pne_chg_Profile_data` (~3437) |
| Dchg | `toyo_dchg_Profile_data` (~2771) | `pne_dchg_Profile_data` (~3493) |
| Continue | `toyo_Profile_continue_data` | `pne_Profile_continue_data` |
| DCIR | `toyo_dcir_Profile_data` | `pne_dcir_Profile_data` |

### 5.7 dQ/dV 계산 로직 (Chg/Dchg 프로필)

```python
# 평활도 자동 결정 (smoothdegree=0일 때)
smoothdegree = max(int(len(df.Profile) / 30), 1)

# 미분 계산
df.Profile["delvol"] = df.Profile["Voltage[V]"].diff(periods=smoothdegree)
df.Profile["delcap"] = df.Profile["Chgcap"].diff(periods=smoothdegree)
df.Profile["dQdV"] = df.Profile["delcap"] / df.Profile["delvol"]  # 미분 용량
df.Profile["dVdQ"] = df.Profile["delvol"] / df.Profile["delcap"]  # 역미분 전압
```

---

## 6. 개별 탭 vs 통합 탭

### 6.1 사이클 분석에서의 탭 할당

```python
# 개별 모드 (radio_indiv.isChecked())
tab_units = [[0], [1], [2]]      # 그룹당 1개 탭
# → folder_groups 3개 → 탭 3개

# 통합 모드 (radio_overall.isChecked())
# file_idx 기준으로 그룹 병합
by_file = OrderedDict()
for gi, g in enumerate(folder_groups):
    by_file.setdefault(g.file_idx, []).append(gi)
tab_units = list(by_file.values())
# → file_idx=[0,0,1] → tab_units=[[0,1], [2]] → 탭 2개
```

**개별 vs 통합 플롯 차이:**

| 항목 | 개별 탭 | 통합 탭 |
|------|--------|--------|
| 탭 수 | 그룹 수 = 탭 수 | 파일당 1탭 |
| 축 범위 | 그룹 데이터에 맞춤 | 전체 데이터 통합 범위 |
| 범례 | 채널명만 | 그룹명 + 채널명 |
| channel_map | 그룹 내 채널만 | 파일 내 모든 채널 |

### 6.2 프로필 분석에서의 탭 할당

프로필 분석은 **개별/통합 라디오와 무관**하게, `CycProfile/CellProfile/AllProfile`로 탭 구조가 결정:

| 모드 | 탭 생성 기준 | 탭 수 |
|------|-----------|:--:|
| CycProfile | 채널당 1탭 | 채널 수 |
| CellProfile | 사이클당 1탭 | 사이클 수 |
| AllProfile | 항상 1탭 | 1 |

---

## 7. 범례 처리 및 CH 제어 팝업

### 7.1 범례 자동 처리

범례 항목이 많아지면 자동으로 그라데이션 모드로 전환된다:

```
항목 수 < LEGEND_THRESHOLD(15) → 일반 범례 (이름 표시)
항목 수 ≥ LEGEND_THRESHOLD(15) → 그라데이션 모드 (colormap 자동 적용)
```

**colormap 매핑:**
- AllProfile → `turbo` (Cell × Cycle 조합이 많을 때)
- CycProfile → `viridis` (사이클 라벨 기준)
- CellProfile / 기타 → `tab20` 또는 `hsv` (채널 구분)

### 7.2 CH 제어 팝업 — 3단 계층 토글

`_create_cycle_channel_control()` (line ~10869)이 생성하는 팝업 구조:

```
┌────────────────────────────────────────────┐
│ [▶ CH] 버튼 클릭 → Tool 플로팅 윈도우      │
│                                            │
│  ☑ "전체 표시"                              │ ← 전체 on/off
│  ────────────────────                      │
│  [Tier 1: 채널 그룹]                        │
│  ☑ ■ ATL_B8                               │ ← main channel_map
│  ☑ ■ SDI_M2                               │
│  ────────────────────                      │
│  [Tier 2: 서브채널]          (있을 때만)     │
│  ☑ ■ ATL_B8 [032]                         │ ← sub_channel_map
│  ☑ ■ ATL_B8 [073]                         │
│  ☑ ■ SDI_M2 [105]                         │
│  ────────────────────                      │
│  [Tier 3: 사이클]            (AllProfile만) │
│  ☑ ■ ATL_B8 [032] 0010                    │ ← sub2_channel_map
│  ☑ ■ ATL_B8 [032] 0020                    │
│  ☑ ■ ATL_B8 [073] 0010                    │
└────────────────────────────────────────────┘
```

### 7.3 계층별 채널 맵 구조

```python
# Tier 1: 메인 채널 (폴더 단위)
channel_map = {
    "ATL_B8": {
        'color': '#E64B35',
        'artists': [Line2D, Line2D, ...],  # matplotlib artist 객체
        'visible': True
    },
    "SDI_M2": { ... }
}

# Tier 2: 서브채널 (채널 폴더 단위)
sub_channel_map = {
    "ATL_B8 [032]": {
        'color': '#3C5488',
        'parent': 'ATL_B8',       # ← Tier 1 연결
        'artists': [...],
    },
}

# Tier 3: 서브2채널 (사이클 단위) — AllProfile에서만 사용
sub2_channel_map = {
    "ATL_B8 [032] 0010": {
        'color': '#00A087',
        'parent': 'ATL_B8 [032]', # ← Tier 2 연결
        'artists': [...],
    },
}
```

### 7.4 부모-자식 연동 논리

```
Tier 1 체크 변경 (ATL_B8 체크 해제)
    ↓
  하위 Tier 2 전체 자동 체크 해제 (ATL_B8 [032], ATL_B8 [073])
    ↓
  하위 Tier 3 전체 자동 체크 해제 (ATL_B8 [032] 0010, 0020, ...)
    ↓
  해당 artists 전부 set_visible(False)
    ↓
  canvas.draw_idle()  ← 화면 갱신
```

### 7.5 하이라이트 기능

개별 채널 클릭 시:
- 선택된 채널: `alpha=1.0` (원본 색상)
- 나머지 채널: `alpha=0.15` (흐리게 dim 처리)
- 범례도 선택된 채널만 두껍게 표시

---

## 8. 데이터프레임 컬럼 사전

### 8.1 Cycle 분석 — NewData DataFrame

사이클 분석에서 `pne_cycle_data()` / `toyo_cycle_data()`가 반환하는 DataFrame:

| 컬럼 | 타입 | 단위 | 설명 |
|------|------|------|------|
| `Dchg` | float | 비율 | 방전용량비 (= 방전용량 / 기준용량) |
| `Chg` | float | 비율 | 충전용량비 |
| `Eff` | float | 비율 | 충방효율 (= Dchg / Chg) |
| `Eff2` | float | 비율 | 방충효율 (= Chg_next / Dchg) |
| `Temp` | float | ℃ | 온도 |
| `RndV` | float | V | Rest End Voltage (OCV) |
| `AvgV` | float | V | 평균방전전압 (= Energy / 용량) |
| `dcir` | float | mΩ | DC-IR |
| `dcir2` | float | mΩ | 두 번째 DCIR (PNE 전용) |
| `rssocv` | float | V | RSS Open Circuit Voltage |
| `rssccv` | float | V | RSS Constant Current Voltage |
| `soc70_dcir` | float | mΩ | SOC 70% DCIR (MK DCIR 모드) |
| `soc70_rss_dcir` | float | mΩ | SOC 70% RSS DCIR |
| `OriCyc` | int | — | 원본 사이클 번호 |
| `DchgEng` | float | Wh | 방전 에너지 |

**인덱스**: 통상 0부터 (리셋), `OriCyc`에 원본 사이클 번호 보존

### 8.2 Profile 분석 — 프로필별 컬럼

#### Step / Rate Profile

| 컬럼 | 설명 |
|------|------|
| `TimeMin` | 시간 (분) |
| `SOC` | State of Charge (정규화 0~1) |
| `Vol` | 전압 (V) |
| `Crate` | C-rate (전류/용량, 정규화) |
| `Temp` | 온도 (℃) |

#### Chg / Dchg Profile

| 컬럼 | 설명 |
|------|------|
| `TimeMin` | 시간 (분) |
| `SOC` | 충전: SOC, 방전: DOD (정규화) |
| `Energy` | 에너지 (Wh) |
| `Vol` | 전압 (V) |
| `Crate` | C-rate |
| `dQdV` | 미분용량 (ΔQ/ΔV) |
| `dVdQ` | 역미분전압 (ΔV/ΔQ) |
| `Temp` | 온도 (℃) |

#### Continue Profile

| 컬럼 | 설명 |
|------|------|
| `TimeSec` | 시간 (초) |
| `Vol` | 전압 (V) |
| `Curr` | 전류 (A) |
| `Temp` | 온도 (℃) |
| `OCV` | Open Circuit Voltage (선택) |
| `CCV` | Constant Current Voltage (선택) |

#### DCIR Profile

| 컬럼 | 설명 |
|------|------|
| `AccCap` | 누적용량 |
| `SOC` | State of Charge (%) |
| `OCV` | Open Circuit Voltage |
| `rOCV` | Relaxed OCV |
| `CCV` | Constant Current Voltage |
| `DCIR_0.1s` | 0.1초 pulse DC-IR (mΩ) |
| `DCIR_1.0s` | 1.0초 pulse DC-IR |
| `DCIR_10.0s` | 10초 pulse DC-IR |
| `DCIR_20.0s` | 20초 pulse DC-IR |
| `RSS` | Root Sum of Squares DC-IR |

### 8.3 PNE SaveEndData.csv 원본 컬럼 인덱스

| Index | 내용 | 단위 |
|:--:|------|------|
| 2 | StepType (1=충전, 2=방전, 3=휴지, 8=loop) | 코드 |
| 6 | EndState | 코드 |
| 8 | EndVoltage | μV (÷1,000,000 → V) |
| 9 | EndCurrent | μA (÷1,000,000 → A) |
| 10 | ChgCapacity | mAh (÷1,000) |
| 11 | DchgCapacity | mAh (÷1,000) |
| 15 | DchgWattHour | Wh |
| 17 | StepTime | 0.01초 단위 |
| 20 | DCIR/임피던스 | mΩ × 1000 |
| 24 | Temperature | 0.001℃ |
| 27 | TotalCycle | 사이클 번호 |
| 29 | AverageVoltage | μV |
| 45 | VoltageMax | μV |

---

## 9. 데이터 저장/내보내기 로직

### 9.1 데이터 저장 (`saveok` 체크박스)

사용자가 `saveok`를 체크하면 분석 완료 시 Excel/CSV로 저장:

**사이클 분석 저장:**
```
파일: 사용자 지정.xlsx (ExcelWriter)
시트:
  - "Approval_cycle": 신뢰성 승인용 데이터
  - "방전용량": 사이클 × 채널 매트릭스
  - "Rest End": 사이클 × 채널 (OCV)
  - "평균 전압": 사이클 × 채널
  - "충방효율": 사이클 × 채널
  - "방충효율": 사이클 × 채널
  - "DCIR": (dcir 체크 시)
  - "SOC70_DCIR": (mkdcir 체크 시)
```

**프로필 분석 저장:**
```
파일: 사용자 지정.xlsx
시트: (프로필별) 채널×사이클 조합의 시계열 데이터
```

### 9.2 그래프 저장 (`figsaveok` 체크박스)

```python
def output_fig(figsaveokchk, filename):
    if figsaveokchk.isChecked():
        plt.savefig(
            'd:/' + filename + '.png',
            dpi=THEME['DPI'],
            facecolor=THEME['FIG_FACECOLOR'],
            bbox_inches='tight'
        )
```

**⚠️ 주의**: 저장 경로가 `d:/`로 고정되어 있음 (하드코딩)

---

## 10. 메모리 관리 — 데이터 생명주기

### 10.1 인스턴스 변수별 생명주기

| 변수 | 생성 시점 | 소멸 시점 | 예상 크기 |
|------|---------|---------|---------|
| `self.df` | 데이터 로드 시 | 새 데이터 로드로 덮어씌워질 때 | 채널당 10~100MB |
| `self.AllchnlData` | 프로필 로드 시 | 새 데이터 로드로 덮어씌워질 때 | 전체 채널 합산 |
| `self.ptn_df_select` | 패턴 선택 시 | 새 패턴 로드 시 | 1~50MB |
| `self.pne_ptn_merged_df` | PNE 패턴 병합 시 | 새 병합 시 | 1~50MB |

### 10.2 로컬 변수 생명주기 (함수 스택)

| 변수 | 스코프 | 소멸 시점 |
|------|-------|---------|
| `results` (로딩 결과) | `unified_cyc_confirm_button` | 함수 종료 시 GC |
| `loaded_data` (프로필) | `*_confirm_button` | 함수 종료 시 GC |
| `fig`, `axes` | 탭 생성 루프 | `plt.close(fig)` 호출 또는 탭 삭제시 |
| `channel_map` | 클로저로 캡처됨 | 팝업 위젯 삭제 시 |
| `cyctemp` | `_load_cycle_data_task` | results에 저장 후 해제 |

### 10.3 탭 초기화 시 메모리 동작

```python
def cycle_tab_reset_confirm_button(self):
    self.tab_delete(self.cycle_tab)  # 탭 UI 삭제
    self.tab_no = 0
```

**⚠️ 문제점**: `tab_delete()`는 탭 위젯만 제거.
- Figure 객체: `plt.close()` 명시 호출이 없으면 matplotlib 내부에 잔존
- `self.df`, `self.AllchnlData`: 여전히 메모리에 남아있음
- channel_map 클로저: 탭 위젯이 삭제되면 참조 해제 → GC 대상

### 10.4 메모리 최적화 포인트

```
[개선 가능 영역]

1. plt.close() 누락
   - cycle_tab_reset 시 열린 figure를 명시적으로 닫아야 함
   - 현재는 탭 UI만 삭제하고 figure는 잔존

2. self.df 덮어쓰기 방식
   - 이전 데이터가 GC 되기 전에 새 데이터 로드 시 피크 메모리 2배
   - del self.df → 새 할당 순서가 안전

3. 대용량 프로필 데이터
   - AllProfile 모드: 채널×사이클 전체 데이터가 1회 메모리에 적재
   - 채널 20개 × 사이클 10개 = 200개 DataFrame 동시 보유
```

---

## 11. 성능 상세 분석

### 11.1 성능 계측 구조

```python
# 성능 로거 (BDT.perf 네임스페이스)
_perf_logger = logging.getLogger('BDT.perf')

# 데코레이터: 함수 전체 실행시간 계측
@log_perf
def step_confirm_button(self): ...

# 컨텍스트 매니저: 구간별 세분화 계측
with PerfSection('데이터 로딩'):
    results = _load_all_cycle_data_parallel(...)

with PerfSection('사이클 카테고리 분류'):
    classify_channel_path(...)
```

### 11.2 사이클 분석 — 성능 병목 분석

```
전체 실행시간 분해 (예상 비율, 채널 30개 × 400cyc 기준):

┌─────────────────────────────────────────────────────────┐
│ ■■■■■■■■■■■■■■■■■■■■ 데이터 로딩 (40~60%)              │
│   ├── CSV 읽기 (pd.read_csv)                            │
│   ├── DataFrame 구성 + 정규화                            │
│   └── DCIR 계산 (사이클별 파일 열기 — Toyo 특히 느림)     │
│                                                         │
│ ■■■■■ 사이클 분류 (5~10%)                               │
│   ├── SaveEndData 읽기 (PNE)                            │
│   ├── 카테고리 판별                                      │
│   └── 패턴 분석 + 스케줄 파일 파싱                       │
│                                                         │
│ ■■■■■■■■■■ 플롯 생성 (20~35%)                          │
│   ├── scatter/line 그리기 (채널×6축)                     │
│   ├── 축 조정 (_auto_adjust_cycle_axes)                  │
│   └── tight_layout + canvas 렌더링                      │
│                                                         │
│ ■■ 탭 생성 + UI 조립 (5~10%)                            │
│   ├── _finalize_cycle_tab                               │
│   ├── _build_classify_info_label                        │
│   └── _create_cycle_channel_control                     │
└─────────────────────────────────────────────────────────┘
```

### 11.3 프로필 분석 — 성능 병목 분석

```
전체 실행시간 분해 (채널 10개 × 사이클 5개 기준):

┌─────────────────────────────────────────────────────────┐
│ ■■■■■■■■■■■■■■■■■■■■■■■ 프로파일 로딩 (50~70%)         │
│   ├── PNE: SaveData_NNNN.csv 다중 파일 이어붙이기        │
│   │   └── savingFileIndex로 파일 위치 찾기               │
│   ├── Toyo: 사이클별 Summary 파서 + 개별 파일 열기        │
│   ├── 단위 변환 (μV→V, μA→A 등)                        │
│   └── dQ/dV 계산 (Chg/Dchg 한정)                       │
│                                                         │
│ ■■■■■■■■■ 플롯 생성 (20~40%)                           │
│   ├── profile curve 그리기 (채널×사이클×6축)              │
│   └── 범례 설정 (그라데이션 시 colormap 재적용)           │
│                                                         │
│ ■■ 탭 생성 + UI (5~10%)                                 │
│   └── _finalize_plot_tab + CH 제어                      │
└─────────────────────────────────────────────────────────┘
```

### 11.4 병렬화 현황

| 파이프라인 | 병렬 단위 | 실행 방식 | 최적화 여부 |
|-----------|---------|---------|:--:|
| Cycle 데이터 로딩 | 채널별 | `ThreadPoolExecutor` | ✅ |
| Cycle 분류 | 채널별 | **순차** | ❌ 병렬화 가능 |
| Profile 데이터 로딩 | 채널별 (사이클 배치) | `ThreadPoolExecutor` | ✅ |
| 플롯 생성 | 탭별 | **순차** (matplotlib 단일 스레드) | — |

### 11.5 주요 성능 병목

1. **PNE 다중 CSV 이어붙이기**: `SaveData_NNNN.csv` 파일이 수십~수백 개 → 파일 열기 오버헤드
2. **Toyo DCIR 개별 파일 열기**: 각 DCIR 사이클마다 별도 파일 → I/O 집중
3. **matplotlib scatter/line 대량 추가**: 채널 30개 × 6축 = 180번 플롯 호출
4. **tight_layout 반복 호출**: 탭마다 레이아웃 재계산
5. **dQ/dV diff 계산**: Chg/Dchg 프로필에서 전체 데이터에 대해 미분 수행

---

## 12. Cycle ↔ Profile 파이프라인 통합 가능성 분석

### 12.1 현재 구조 비교

```
┌───────────────────────────────────┬──────────────────────────────────────┐
│         사이클 분석                 │           프로필 분석                 │
├───────────────────────────────────┼──────────────────────────────────────┤
│ 경로파싱: _parse_cycle_input()     │ 경로파싱: _init_confirm_button()     │
│    → CycleGroup 리스트             │    → folders, names (튜플)           │
│    → flat_idx_of 매핑              │    → 직접 enumerate                  │
│                                   │                                      │
│ 로딩: _load_all_cycle_data_parallel│ 로딩: _load_all_profile_data_parallel│
│    → results: {(fi,si): data}     │    → loaded_data: {(i,j,cyc): data} │
│                                   │                                      │
│ 분류: classify_channel_path()      │ 분류: (없음)                         │
│    → 사이클 카테고리 + 패턴 분석    │                                      │
│                                   │                                      │
│ 탭할당: tab_units (개별/통합)      │ 탭할당: CycProfile/CellProfile/All   │
│                                   │                                      │
│ 완성: _finalize_cycle_tab()        │ 완성: _finalize_plot_tab()           │
│    → 분류정보 바 + CH제어          │    → CH제어만                        │
└───────────────────────────────────┴──────────────────────────────────────┘
```

### 12.2 통합 가능한 부분

| 영역 | 통합 가능 | 상세 |
|------|:--:|------|
| **경로 파싱** | ✅ | `_parse_cycle_input()`의 CycleGroup 체계를 Profile에서도 사용 가능. 현재 Profile은 `_init_confirm_button()`에서 별도로 경로를 읽는데, CycleGroup으로 통일하면 채널 필터, 연결 처리, 용량 자동감지 등을 재활용 가능 |
| **채널 스캔** | ✅ | 두 파이프라인 모두 `os.scandir → _is_channel_folder` 패턴 사용. 공통 함수로 추출 가능 |
| **PNE/Toyo 판별** | ✅ | 이미 `check_cycler()` 공용 함수 사용 중 |
| **병렬 로딩 프레임** | ⚠️ 부분 | 두 파이프라인 모두 `ThreadPoolExecutor` 사용하나, task 구조가 다름 (Cycle: 채널 단위, Profile: 채널×사이클 단위). 공통 래퍼는 가능하지만 task 구성은 분리 필요 |
| **인덱스 매핑** | ✅ | `flat_idx_of` + `subfolder_map` 체계를 Profile에서도 도입하면 코드 일관성 향상 |
| **탭 완성** | ⚠️ 부분 | `_finalize_cycle_tab`과 `_finalize_plot_tab`은 유사하나 Cycle 전용 분류정보 바가 있어 완전 통합은 어려움. 공통 기반 함수 + 확장 패턴은 가능 |
| **CH 제어** | ✅ | `_create_cycle_channel_control()`은 이미 두 파이프라인에서 공유 사용 중 |
| **범례 처리** | ✅ | 자동 그라데이션 로직은 이미 공통으로 적용 |

### 12.3 통합 불가능한 부분

| 영역 | 이유 |
|------|------|
| **데이터 로딩 함수** | Cycle(pne_cycle_data)과 Profile(pne_chg_Profile_data 등)이 읽는 데이터가 근본적으로 다름 (요약 vs 시계열) |
| **6축 구성** | 사이클: 고정 6축(Dchg/Eff/Temp/DCIR/Eff2/Voltage), 프로필: 타입별로 6축 구성이 다름 |
| **사이클 분류** | Cycle 분석 전용 기능 (Profile에는 불필요) |

### 12.4 통합 제안 — 단계적 리팩토링 로드맵

```
Phase 1: 경로 파싱 통일 (영향 범위: 낮음)
  └── Profile 분석에서도 CycleGroup 사용
  └── _init_confirm_button()에서 _parse_cycle_input() 호출
  └── per_path_channels, per_path_capacities 활용

Phase 2: 채널 스캔 + 인덱스 통일 (영향 범위: 중간)
  └── flat_idx_of + subfolder_map 공통 유틸리티 함수 추출
  └── Profile 로딩도 동일 인덱스 체계 사용

Phase 3: 탭 생성 기반 통합 (영향 범위: 중간)
  └── _finalize_base_tab() 공통 기반 + 확장 패턴
  └── Cycle: + 분류정보 바
  └── Profile: standard
```

---

## 부록: 핵심 함수 위치 색인

| 함수명 | 라인 (approx.) | 역할 |
|--------|:--:|------|
| `check_cycler()` | ~391 | PNE/Toyo 판별 |
| `_auto_adjust_cycle_axes()` | ~660 | 축 자동조정 |
| `graph_cycle()` | ~489 | 사이클 플롯 |
| `graph_profile()` | ~796 | 프로필 플롯 |
| `output_fig()` | ~913 | 그래프 PNG 저장 |
| `toyo_cycle_data()` | ~1018 | Toyo 사이클 데이터 로딩 |
| `_classify_single_pne_cycle()` | ~1223 | PNE 단일 사이클 분류 |
| `classify_pne_cycles()` | ~1322 | PNE 배치 분류 |
| `classify_toyo_cycles()` | ~1405 | Toyo 배치 분류 |
| `classify_channel_path()` | ~1478 | 채널 분류 진입점 |
| `_analyze_accel_pattern_pne()` | ~1891 | 가속수명 패턴 분석 |
| `_track_accel_voltage_changes_pne()` | ~2015 | 전압 변경 트래킹 |
| `analyze_accel_pattern()` | ~2100 | 패턴 분석 디스패처 |
| `format_accel_pattern()` | ~2189 | 패턴 포맷 출력 |
| `toyo_step_Profile_data()` | ~2625 | Toyo Step 프로필 |
| `toyo_chg_Profile_data()` | ~2733 | Toyo 충전 프로필 |
| `toyo_dchg_Profile_data()` | ~2771 | Toyo 방전 프로필 |
| `pne_data()` | ~2917 | PNE 프로필 raw 로딩 |
| `pne_cycle_data()` | ~3177 | PNE 사이클 데이터 |
| `pne_step_Profile_data()` | ~3359 | PNE Step 프로필 |
| `pne_chg_Profile_data()` | ~3437 | PNE 충전 프로필 |
| `pne_dchg_Profile_data()` | ~3493 | PNE 방전 프로필 |
| `_init_confirm_button()` | ~10806 | 프로필 공통 초기화 |
| `_create_cycle_channel_control()` | ~10869 | CH 토글 팝업 |
| `_finalize_cycle_tab()` | ~11888 | 사이클 탭 완성 |
| `_build_classify_info_label()` | ~11939 | 분류 정보 바 |
| `_finalize_plot_tab()` | ~12118 | 프로필 탭 완성 |
| `_load_all_profile_data_parallel()` | ~12309 | 프로필 병렬 로딩 |
| `_load_all_cycle_data_parallel()` | ~12407 | 사이클 병렬 로딩 |
| `_parse_cycle_input()` | ~12581 | 경로 파싱 |
| `unified_cyc_confirm_button()` | ~12751 | 사이클 분석 진입점 |
| `step_confirm_button()` | ~14409 | Step 프로필 |
| `rate_confirm_button()` | ~14616 | Rate 프로필 |
| `chg_confirm_button()` | ~14879 | 충전 프로필 |
| `dchg_confirm_button()` | ~15159 | 방전 프로필 |
| `continue_confirm_button()` | ~15435 | Continue 프로필 |
| `dcir_confirm_button()` | ~15752 | DCIR 프로필 |
