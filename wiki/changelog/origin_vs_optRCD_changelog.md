# BatteryDataTool 변경 내역 비교

## 비교 대상

| 항목 | 파일 |
|------|------|
| **원본 (ORIGIN)** | `BatteryDataTool_origin/BatteryDataTool.py` (14,168줄) |
| **최적화 (OPTIMIZED)** | `BatteryDataTool_260206_edit copy/BatteryDataTool_optRCD.py` (16,056줄) |

> 작성일: 2026-02-19

---

## 목차

1. [Import 및 의존성 변경](#1-import-및-의존성-변경)
2. [THEME 시스템 도입](#2-theme-시스템-도입)
3. [코인셀/마이크로 단위 통합](#3-코인셀마이크로-단위-통합)
4. [그래프 함수 테마 적용](#4-그래프-함수-테마-적용)
5. [Toyo Cycle 병합 로직 벡터화](#5-toyo-cycle-병합-로직-벡터화)
6. [PNE 인덱스 파일 캐싱 (lru_cache)](#6-pne-인덱스-파일-캐싱-lru_cache)
7. [배치 프로파일 함수 신규 추가](#7-배치-프로파일-함수-신규-추가)
8. [병렬 로딩 (ThreadPoolExecutor)](#8-병렬-로딩-threadpoolexecutor)
9. [범례 자동 전환 (LEGEND_THRESHOLD)](#9-범례-자동-전환-legend_threshold)
10. [AllProfile 모드 신규 추가](#10-allprofile-모드-신규-추가)
11. [WindowClass 헬퍼 메서드 추출](#11-windowclass-헬퍼-메서드-추출)
12. [toyo_Profile_continue_data 재작성](#12-toyo_profile_continue_data-재작성)
13. [PNE-to-Toyo 패턴 변환기](#13-pne-to-toyo-패턴-변환기)
14. [Deprecated API 제거](#14-deprecated-api-제거)
15. [버그 수정](#15-버그-수정)
16. [UI 변경 사항](#16-ui-변경-사항)
17. [기타 변경](#17-기타-변경)

---

## 1. Import 및 의존성 변경

| 변경 사항 | ORIGIN | OPTIMIZED |
|-----------|--------|-----------|
| `functools.lru_cache` | 없음 | **추가** (PNE 인덱스 캐싱용) |
| `concurrent.futures` | 없음 | **추가** (`ThreadPoolExecutor`, `as_completed`) |
| `matplotlib.cm` | 없음 | **추가** (컬러맵 지원) |
| `matplotlib.colors` (mcolors) | 없음 | **추가** (컬러 정규화) |
| Matplotlib 백엔드 모듈 | `backend_qt5agg` | `backend_qtagg` (PyQt6 네이티브) |

---

## 2. THEME 시스템 도입

ORIGIN은 그래프 스타일이 함수마다 하드코딩되어 있었으나, OPTIMIZED에서는 **Pro-Nature 테마 딕셔너리**로 중앙 집중화되었다.

### THEME 딕셔너리 구조

```python
THEME = {
    'PALETTE': ['#3C5488', '#E64B35', '#00A087', '#F39B7F', '#4DBBD5',
                '#8491B4', '#B09C85', '#91D1C2', '#DC0000', '#7E6148'],
    'FIG_FACECOLOR': '#FFFFFF',
    'AX_FACECOLOR':  '#FAFBFD',
    'TITLE_SIZE': 15,       'LABEL_SIZE': 12,      'TICK_SIZE': 10,
    'SCATTER_SIZE': 10,     'SCATTER_EMPTY_SIZE': 14,
    'SCATTER_ALPHA': 0.55,  'SCATTER_SET_SIZE': 4,
    'EDGE_WIDTH': 0,        'EDGE_COLOR': 'none',
    'LINE_WIDTH': 1.4,      'LINE_ALPHA': 0.6,     'MARKER_SIZE': 5,
    'GRID_ALPHA': 0.18,     'GRID_STYLE': '--',    'GRID_WIDTH': 0.5,
    'GRID_COLOR': '#666666','SPINE_COLOR': '#666666','SPINE_WIDTH': 0.6,
    'CMAP': 'coolwarm',
    'SUPTITLE_SIZE': 15,    'SUPTITLE_WEIGHT': 'bold',
    'LEGEND_SIZE': 'small', 'LEGEND_FRAMEALPHA': 0.85,
    'LEGEND_EDGECOLOR': '#CCCCCC',
    'DPI': 150,
}
```

### 전역 rcParams 적용 (17개 항목)

| 설정 | 값 |
|------|----|
| `figure.facecolor` | `#FFFFFF` |
| `axes.facecolor` | `#FAFBFD` |
| `axes.spines.top / right` | `False` (상단/우측 축선 제거) |
| `axes.edgecolor / linewidth` | `#666666` / `0.6` |
| `axes.grid` | `True` (기본 그리드 활성화) |
| `grid.*` | 점선, 폭 0.5, 투명도 0.18 |
| `xtick/ytick.direction` | `"in"` |
| `lines.linewidth` | `1.4` |
| `axes.prop_cycle` | 10색 팔레트 자동 순환 |

---

## 3. 코인셀/마이크로 단위 통합

### ORIGIN
- `PNE21`/`PNE22` 판별이 **각 함수마다 개별 하드코딩**
- 코인셀 모드 통합 불가

### OPTIMIZED
- **글로벌 헬퍼 함수**로 통합 (약 14곳에서 사용):

```python
_coincell_mode = False

def set_coincell_mode(enabled):
    """코인셀 체크박스 상태 설정 (처리 시작 전 호출)"""
    global _coincell_mode
    _coincell_mode = enabled

def is_micro_unit(raw_file_path):
    """PNE21/22 또는 코인셀 모드에서 μA/μAh 단위 사용 여부 판별"""
    return ('PNE21' in raw_file_path) or ('PNE22' in raw_file_path) or _coincell_mode
```

- CycTab에 `chk_coincell_cyc` 체크박스 추가로 Cycle 탭에서도 코인셀 모드 활성화 가능

---

## 4. 그래프 함수 테마 적용

모든 그래프 함수에서 하드코딩 값이 THEME 참조로 교체되었다.

### `graph_base_parameter()`

| 속성 | ORIGIN | OPTIMIZED |
|------|--------|-----------|
| xlabel fontsize | `12` | `THEME['LABEL_SIZE']` |
| ylabel fontsize | `12` | `THEME['LABEL_SIZE'] - 1` |
| tick_params | `direction='in'` | `direction='in', labelsize=THEME['TICK_SIZE']` |
| grid | `linestyle='--', linewidth=1.0` | `linestyle, linewidth, alpha, color` 전부 THEME 참조 |

### `graph_cycle()` (filled scatter)

| 속성 | ORIGIN | OPTIMIZED |
|------|--------|-----------|
| scatter size | `s=5` | `s=THEME['SCATTER_SIZE']` |
| 추가 파라미터 | — | `alpha`, `edgecolors`, `linewidths`, `zorder=3` |

### `graph_cycle_empty()` (empty scatter)

| 속성 | ORIGIN | OPTIMIZED |
|------|--------|-----------|
| scatter size | `s=8` | `s=THEME['SCATTER_EMPTY_SIZE']` |
| 추가 파라미터 | — | `alpha`, `linewidths=0.6`, `zorder=3` |

### `graph_output_cycle()` — 색상 인덱스

| 속성 | ORIGIN | OPTIMIZED |
|------|--------|-----------|
| 색상 모듈로 | `colorno % 9` (하드코딩) | `colorno % len(THEME['PALETTE'])` (동적, =10) |

### 기타 그래프 함수 공통 변경

| 함수 | 변경 내용 |
|------|-----------|
| `graph_step` | `linewidth`, `alpha` 추가 |
| `graph_continue` | `linewidth`, `alpha`, `markersize` 추가 |
| `graph_soc_continue` | 동일 |
| `graph_dcir` | 동일 |
| `graph_soc_dcir` | 동일 |
| `graph_profile` | `linewidth`, `alpha` 추가 |
| `graph_soc_set` | 색상: 하드코딩 → `THEME['PALETTE']`, `s=1` → `SCATTER_SET_SIZE`, `alpha` 추가 |
| `graph_soc_err` | 색상 → THEME 팔레트 |
| `graph_set_profile` | 색상 → THEME, scatter size → THEME, `alpha` 추가 |
| `graph_eu_set` | fontsize/labelsize → THEME 기반 계산 |
| `graph_default` | 색상 → THEME, `alpha` 추가 |
| `output_para_fig` | `dpi`, `facecolor`, `bbox_inches='tight'` 추가 |
| `output_fig` | `dpi`, `facecolor`, `bbox_inches='tight'` 추가 |

---

## 5. Toyo Cycle 병합 로직 벡터화

### ORIGIN — while 루프 기반 행별 순회

```python
i = 0
while i < len(Cycleraw) - 1:
    current_cond = Cycleraw.loc[i, "Condition"]
    next_cond = Cycleraw.loc[i + 1, "Condition"]
    if current_cond in (1, 2) and current_cond == next_cond:
        Cycleraw = Cycleraw.drop(i, axis=0).reset_index(drop=True)
    else:
        i += 1
```

- **문제점**: 매 반복마다 `drop()` + `reset_index()` → O(n²) 복잡도

### OPTIMIZED — 벡터화 그룹 기반 병합

```python
cond_series = Cycleraw["Condition"]
merge_group = ((cond_series != cond_series.shift()) | (~cond_series.isin([1, 2]))).cumsum()

def merge_rows(group):
    if len(group) == 1: return group.iloc[0]
    cond = group["Condition"].iloc[0]
    result = group.iloc[-1].copy()
    if cond == 1:
        result["Cap[mAh]"] = group["Cap[mAh]"].sum()
        result["Ocv"] = group["Ocv"].iloc[0]
    elif cond == 2:
        result["Cap[mAh]"] = group["Cap[mAh]"].sum()
        result["Pow[mWh]"] = group["Pow[mWh]"].sum()
        result["Ocv"] = group["Ocv"].iloc[0]
        if result["Cap[mAh]"] != 0:
            result["AveVolt[V]"] = result["Pow[mWh]"] / result["Cap[mAh]"]
    return result

Cycleraw = Cycleraw.groupby(merge_group, group_keys=False).apply(merge_rows)
```

- **효과**: O(n) 복잡도, 대규모 데이터 처리 시 2~5배 속도 향상
- **추가**: 충방전 인덱스 보정 로직 (위치 기반 재정렬)

```python
if Dchg.index[0] < Chg.index[0]:
    Dchg = Dchg.iloc[1:]  # 초기 부분 방전 제거
_nmin = min(len(Chg), len(Dchg))
Chg = pd.Series(Chg.values[:_nmin], index=Dchg.index[:_nmin])
```

---

## 6. PNE 인덱스 파일 캐싱 (lru_cache)

### ORIGIN
- `pne_search_cycle()` 호출마다 SaveEndData + savingFileIndex_start.csv를 **매번 디스크에서 읽음**

### OPTIMIZED

```python
@lru_cache(maxsize=32)
def _load_pne_index_files(rawdir):
    """SaveEndData와 savingFileIndex_start를 1회만 읽어 캐싱"""
    # vectorized parsing:
    file_index = df2[3].str.replace(',', '').astype(int).tolist()
    return save_end, file_index

def pne_search_cycle(rawdir, start, end):
    save_end, file_index = _load_pne_index_files(rawdir)  # 캐시 히트
    ...

def pne_search_cycle_cache_clear():
    """경로 변경 시 캐시 초기화"""
    _load_pne_index_files.cache_clear()
```

- **효과**: 동일 폴더 반복 호출 시 디스크 I/O 완전 제거

---

## 7. 배치 프로파일 함수 신규 추가

ORIGIN은 사이클마다 개별 함수 호출이었으나, OPTIMIZED에서는 min_cap·인덱스 파일을 1회만 읽고 사이클을 반복하는 **배치 패턴**으로 리팩터링되었다.

### 신규 함수 목록 (12개)

| 유형 | Toyo | PNE |
|------|------|-----|
| Step Profile | `toyo_step_Profile_batch()` | `pne_step_Profile_batch()` |
| Rate Profile | `toyo_rate_Profile_batch()` | `pne_rate_Profile_batch()` |
| Chg Profile | `toyo_chg_Profile_batch()` | `pne_chg_Profile_batch()` |
| Dchg Profile | `toyo_dchg_Profile_batch()` | `pne_dchg_Profile_batch()` |
| Continue Profile | `toyo_continue_Profile_batch()` | `pne_continue_Profile_batch()` |

### 공통 헬퍼

| 함수 | 용도 |
|------|------|
| `_pne_load_profile_raw()` | PNE SaveData 파일 일괄 로딩 (min~max cycle 범위) |
| `toyo_build_cycle_map()` | capacity.log 기반 논리 사이클 → 원본 파일 범위 매핑 |

### 배치 최적화 패턴

```
┌──────────────────────────────────────────────────────┐
│ 1. min_cap 1회 산정                                    │
│ 2. 인덱스 파일(SaveEndData 등) 1회 로딩                  │
│ 3. 전체 범위 SaveData 1회 일괄 로딩 (all_raw)            │
│ 4. is_micro_unit()로 단위 계수 1회 결정                  │
│ 5. cycle_list 반복: all_raw에서 메모리 필터링             │
│ 6. results[cycle] = [mincapacity, df] dict 반환         │
└──────────────────────────────────────────────────────┘
```

**ORIGIN**: 사이클마다 `pne_data()` → 매번 디스크 I/O  
**OPTIMIZED**: `_pne_load_profile_raw()` 1회 → 메모리 분배

---

## 8. 병렬 로딩 (ThreadPoolExecutor)

WindowClass에 병렬 로딩 메서드가 추가되어 **다채널 데이터를 동시에 처리**한다.

| 메서드 | 용도 |
|--------|------|
| `_load_step_batch_task()` | ThreadPool 개별 채널 step 배치 태스크 |
| `_load_all_step_data_parallel()` | 전체 채널 step 데이터 병렬 로딩 (max_workers=4) |
| `_load_profile_batch_task()` | ThreadPool 개별 채널 rate/chg/dchg/continue 배치 태스크 |
| `_load_all_profile_data_parallel()` | 전체 채널 프로파일 데이터 병렬 로딩 |

---

## 9. 범례 자동 전환 (LEGEND_THRESHOLD)

### ORIGIN
- 모든 그래프에 수동 `.legend()` 호출

### OPTIMIZED

```python
LEGEND_THRESHOLD = 15  # 이 수를 초과하면 그라데이션+컬러바로 전환
```

`_setup_legend()` 메서드:
1. `ax.get_lines()` 개수를 카운트
2. **15개 이하** → 기존 범례 표시
3. **15개 초과** → 범례 제거, **그라데이션 컬러맵 + 컬러바**로 전환
4. 컬러맵 자동 선택: AllProfile → `'turbo'`, CycProfile → `'viridis'`, 기타 → `'tab20'`/`'hsv'`
5. `fig.add_axes([0.90, 0.10, 0.02, 0.78])`에 컬러바 추가
6. `self._has_colorbar = True` 설정 → `tight_layout(rect=[0, 0, 0.88, 1])` 자동 조정

---

## 10. AllProfile 모드 신규 추가

| 항목 | ORIGIN | OPTIMIZED |
|------|--------|-----------|
| `AllProfile` 라디오버튼 | 없음 | **추가** (tab_6, CycProfile 옆) |
| 기능 | — | 모든 채널 데이터를 **1개 그래프**에 합쳐서 표시 |
| CycProfile | 채널별 개별 탭 | 유지 (채널별 개별 탭) |

---

## 11. WindowClass 헬퍼 메서드 추출

ORIGIN에서 인라인으로 반복되던 패턴이 재사용 가능한 메서드로 추출되었다.

| 메서드 | 용도 | ORIGIN |
|--------|------|--------|
| `_get_config()` | 설정값 표준 딕셔너리 반환 | 인라인 변수 |
| `_setup_file_writer()` | 저장 파일 + writer 생성 (global writer 패턴 제거) | `global writer` 인라인 |
| `_create_plot_tab()` | 탭/레이아웃/캔버스/툴바 튜플 생성 | 매번 중복 코드 |
| `_finalize_plot_tab()` | 탭 마무리 + 컬러바 tight_layout 조정 | 매번 중복 코드 |
| `_setup_legend()` | 자동 범례/컬러바 전환 | 수동 `.legend()` |

---

## 12. toyo_Profile_continue_data 재작성

### ORIGIN
- 단순 연결: PassTime 수동 누적, Cap 벡터화 계산
- 출력 컬럼: `["TimeMin", "SOC", "Vol", "Crate", "Temp"]` (5개)
- 반환값: `[mincapacity, df]` (2개)

### OPTIMIZED
- **PassTime 리셋 보정**: `diff().clip(lower=0)` 후 누적합으로 파일 경계 자동 처리
- **signed_current**: 방전 시 전류 부호 반전으로 SOC 정확한 산정
- **OCV/CCV 자동 추출**: Condition 전환점(rest→load=OCV, load→rest=CCV)에서 직접 추출
- **CycfileSOC**: capacity.log 기반 AccCap + OCV/CCV 테이블 생성
- 출력 컬럼: `["TimeSec", "TimeMin", "SOC", "Vol", "Curr", "Crate", "Temp", "OCV", "CCV"]` (9개)
- 반환값: `[mincapacity, df, CycfileSOC]` (3개, **시그니처 변경**)

---

## 13. PNE-to-Toyo 패턴 변환기

OPTIMIZED에 **완전히 새로운** 패턴 변환 기능이 추가되었다.

### 메서드

| 메서드 | 용도 |
|--------|------|
| `ptn_toyo_convert_button()` | 메인 변환 실행 |
| `_pne_steps_to_toyo_substeps()` | PNE 스텝 → Toyo 서브스텝 변환 |
| `_toyo_build_header()` | Toyo 파일 헤더 생성 |
| `_toyo_build_option()` | Toyo option 파일 생성 |
| `_toyo_build_option2()` | Toyo option2 파일 생성 |
| `_toyo_build_puls_dir()` | Toyo Fld_Puls DIR 파일 생성 |
| `_toyo_build_loop()` | Toyo 반복 구조 생성 |
| `_toyo_build_line()` | Toyo 라인 데이터 생성 |

### 출력 파일 (패턴당 6개)

```
PATRN{N}.1
Patrn{N}.option
Patrn{N}.option2
Fld_Puls{N}.DIR
Fld_Thermo{N}.DIR
THPTNNO.1
```

---

## 14. Deprecated API 제거

| ORIGIN | OPTIMIZED | 적용 범위 |
|--------|-----------|-----------|
| `df._append(other)` | `pd.concat([df, other])` | 배치 함수, EU fitting, 데이터 누적 전체 |

pandas 2.0+에서 `DataFrame._append()` 메서드가 제거되었으므로 호환성을 위한 필수 변경.

---

## 15. 버그 수정

### 15-1. 충방전 인덱스 어긋남 보정

`toyo_cycle_data()` 에서 Chg/Dchg 시리즈의 인덱스가 1칸씩 어긋나는 문제를 위치 기반 재정렬로 해결:

```python
if Dchg.index[0] < Chg.index[0]:
    Dchg = Dchg.iloc[1:]  # 초기 부분 방전 제거
_nmin = min(len(Chg), len(Dchg))
Chg = pd.Series(Chg.values[:_nmin], index=Dchg.index[:_nmin])
```

### 15-2. int64 컬럼에 float 할당 오류 방지

`pne_cycle_data()` mkdcir 분기에서 DCIR 계산 시 타입 불일치 오류 수정:

```python
# ORIGIN: int64 컬럼에 float 직접 할당 → 오류 가능
dcirtemp1 = dcirtemp1.iloc[:min_dcir_count]

# OPTIMIZED: .copy() + astype(float) 으로 안전하게 변환
dcirtemp1 = dcirtemp1.iloc[:min_dcir_count].copy()
dcirtemp1[dcirtemp1.columns[5]] = dcirtemp1.iloc[:, 5].astype(float)
```

### 15-3. smoothdegree 정수 캐스팅

ORIGIN에서 `smoothdegree = len(df.Profile) / 30`은 float이 될 수 있어 `diff(periods=...)` 호출 시 오류 가능. OPTIMIZED에서 `int()` 캐스팅 추가 (4곳).

### 15-4. pne_data() filepos 폴백

```python
# ORIGIN: filepos[0] == -1이면 아무것도 안함
if os.path.isdir(rawdir) and (filepos[0] != -1):

# OPTIMIZED: filepos[0] == -1일 때 0으로 폴백
if os.path.isdir(rawdir):
    if (filepos[0] == -1):
        filepos[0] = 0  # 첫 파일부터 읽기
```

---

## 16. UI 변경 사항

| 항목 | ORIGIN | OPTIMIZED |
|------|--------|-----------|
| `chk_coincell_cyc` | 없음 | CycTab에 코인셀 체크박스 추가 |
| `AllProfile` 라디오버튼 | 없음 | tab_6에 추가 (CycProfile 옆) |
| `mount_pne_5` 라벨 | `"U: 3F A PNE17~21"` | `"U: 3F A PNE17~25"` |
| `pro_continue_confirm_button()` | 인라인 | 별도 메서드로 분리, OCV/CCV 그래프 지원 |
| ECT 저장 경로 | `"D:\\" + ect_save[i] + ".csv"` | `save_file_name + "_" + "%04d" % tab_no + ".csv"` |
| Excel 출력 컬럼 | 5컬럼 | OCV 존재 시 8컬럼 + OCV_CCV 시트 |

---

## 17. 기타 변경

### 17-1. Qt 예외 후크

OPTIMIZED의 `__main__` 블록에 예외 후크 추가:

```python
def _exception_hook(exctype, value, traceback):
    sys.__excepthook__(exctype, value, traceback)
sys.excepthook = _exception_hook
```

Qt 슬롯 내부 예외가 콘솔에 출력되도록 하여 디버깅 편의성 향상.

### 17-2. 파일 I/O 패턴 변경

| 항목 | ORIGIN | OPTIMIZED |
|------|--------|-----------|
| Writer 생성 | `global writer` 인라인 | `self._setup_file_writer()` 메서드 |
| 반환값 | — | `(writer, save_file_name)` 튜플 |

---

## 변경 요약

| 카테고리 | 수량 | 핵심 내용 |
|----------|------|-----------|
| 신규 배치 함수 | **12개** | step/rate/chg/dchg/continue × toyo/pne |
| 신규 헬퍼 함수 | **4개** | `is_micro_unit`, `_pne_load_profile_raw`, `_load_pne_index_files`, `toyo_build_cycle_map` |
| 신규 WindowClass 메서드 | **8개** | `_get_config`, `_setup_file_writer`, `_create_plot_tab`, `_finalize_plot_tab`, `_setup_legend`, 병렬 로딩 3개 |
| 벡터화 리팩터링 | **1개** | `toyo_cycle_data` while → groupby |
| lru_cache 적용 | **1개** | PNE 인덱스 파일 I/O |
| 시그니처 변경 | **1개** | `toyo_Profile_continue_data` 반환값 2개 → 3개 |
| 코인셀 통합 | **~14곳** | 하드코딩 → `is_micro_unit()` |
| Deprecated API 제거 | 전체 | `_append()` → `pd.concat()` |
| 버그 수정 | **4건** | 인덱스 보정, float 캐스팅, smoothdegree, filepos 폴백 |
| THEME 적용 | **~20개 함수** | 하드코딩 → THEME 딕셔너리 참조 |
| 신규 UI 요소 | **2개** | AllProfile 라디오버튼, CycTab 코인셀 체크박스 |
| 신규 기능 | **1개** | PNE-to-Toyo 패턴 변환기 |
