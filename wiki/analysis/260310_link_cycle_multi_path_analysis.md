# 연결Cycle 멀티 경로 로딩 & 데이터 처리 로직 분석

> 대상 파일: `DataTool_dev/DataTool_optRCD_proto_.py`

---

## 1. UI 버튼 & 진입 메서드

| 구분 | UI 요소 / 메서드 | 라인 | 기능 |
|------|-----------------|------|------|
| 버튼 | `self.link_cycle` | L8919 | "연결 Cycle" 메인 버튼 |
| 버튼 | `self.link_cycle_indiv` | L8921 | "연결 Cycle 개별" (파일별 그래프) |
| 버튼 | `self.link_cycle_overall` | L8923 | "연결 Cycle 전체" (통합 그래프) |
| 메서드 | `link_cyc_confirm_button()` | L11240 | 자동 경로 기반 연결 처리 |
| 메서드 | `link_cyc_indiv_confirm_button()` | L11434 | 개별 그래프 (CSV당 figure) |
| 메서드 | `link_cyc_overall_confirm_button()` | L11641 | 통합 그래프 (전체 1 figure) |

---

## 2. 전체 처리 흐름도

```
사용자 버튼 클릭
    │
    ├── link_cyc_confirm_button()
    │     └─ pne_path_setting() → 경로 배열 [path1, path2, ...]
    │
    ├── link_cyc_indiv_confirm_button()
    │     └─ filedialog.askopenfilenames() → [file1.csv, file2.csv, ...]
    │        └─ 각 CSV에서 cyclepath/cyclename 컬럼 읽기 → 경로 배열
    │
    └── link_cyc_overall_confirm_button()
          └─ filedialog.askopenfilenames() → (위와 동일)
    │
    ▼
병렬 데이터 로딩: _load_all_cycle_data_parallel()
    │
    ├─ ThreadPoolExecutor (max_workers=4)
    │   ├─ Thread 1: _load_cycle_data_task()
    │   │   ├─ check_cycler() → PNE/TOYO 판별
    │   │   ├─ pne_cycle_data() or toyo_cycle_data() 호출
    │   │   └─ return (folder_idx, subfolder_idx, folder_path, cyctemp)
    │   ├─ Thread 2, 3, 4: (동일)
    │   └─ results dict 구축
    │
    ▼
진행률: 0% → 50%
    │
    ▼
그래프 생성 (graph_output_cycle)
    ├─ indiv: 각 CSV파일마다 새 figure(2×3 subplots)
    └─ overall: 단일 figure에 모든 데이터 누적
    │
    ▼
진행률: 50% → 100%
    │
    ▼
탭 추가 (_finalize_cycle_tab) & Excel 저장 (선택)
```

---

## 3. 경로 수집 방식 (3가지 모드)

### 3-1. 경로 파일 기반 (`pne_path_setting()`, `chk_cyclepath` 체크 시)

```
filedialog.askopenfilename() → "paths.tsv"

TSV 형식:
    cyclename    cyclepath
    Sample-A     D:/Test/Cell_001/
    Sample-B     D:/Test/Cell_002/
```

- 탭 기준 마지막 컬럼이 `cyclepath`, 나머지가 `cyclename`
- 복수 cyclename 지원

### 3-2. 텍스트 직접 입력 (`stepnum_2.toPlainText()`)

```
UI 텍스트 박스에 줄 단위로 경로 입력:
    D:/Test/Cell_001/
    D:/Test/Cell_002/
    D:/Test/Cell_003/
```

### 3-3. 폴더 반복 선택 (기본 모드)

```python
multi_askopendirnames()  # L139
# → 대화상자로 폴더 선택 → 반복 (취소 누를 때까지)
# → return [folder_path, ...]
```

---

## 4. 핵심 지원 메서드

| 메서드 | 라인 | 역할 | 반환값 |
|--------|------|------|--------|
| `_load_all_cycle_data_parallel()` | L10612 | ThreadPoolExecutor 병렬 로딩 | `(results dict, subfolder_map)` |
| `_load_cycle_data_task()` | L10597 | 단일 폴더 로딩 작업 | `(idx, folder_path, cyctemp)` |
| `cyc_ini_set()` | L10650 | UI 설정값 수집 | `(C-rate, capacity, xscale, y_limit, ir_scale)` |
| `pne_path_setting()` | L10695 | 3가지 경로 모드 처리 | `[all_data_folder, all_data_name, datafilepath]` |
| `check_cycler()` | L239 | PNE/TOYO 사이클러 판별 | `bool (True=PNE)` |
| `multi_askopendirnames()` | L139 | 폴더 반복 선택 대화상자 | `[folder_path, ...]` |
| `graph_output_cycle()` | L331 | 6개 축에 데이터 그리기 | `([artists], color)` |
| `output_data()` | L605 | Excel 시트에 저장 | `None` |
| `toyo_cycle_data()` | L723 | TOYO 사이클러 데이터 로딩 | `(capacity, DataFrame)` |
| `pne_cycle_data()` | L1885 | PNE 사이클러 데이터 로딩 | `(capacity, DataFrame)` |
| `_finalize_cycle_tab()` | L10326 | 탭 완성 (canvas 추가) | `None` |

---

## 5. 데이터 구조

### 5-1. 병렬 로딩 결과

```python
loaded_data = {
    (folder_idx, subfolder_idx): (folder_path, cyctemp),
    (0, 0): ("/path/folder1/sub1/", (4500.0, DataFrame)),
    (0, 1): ("/path/folder1/sub2/", (4500.0, DataFrame)),
    (1, 0): ("/path/folder2/sub1/", (4800.0, DataFrame)),
}

subfolder_map = {
    0: ["/path/folder1/sub1/", "/path/folder1/sub2/"],
    1: ["/path/folder2/sub1/"],
}
```

### 5-2. cyctemp (사이클 데이터)

```python
cyctemp[0]  # float: 최소 용량 (mAh)
cyctemp[1]  # DataFrame (속성: .NewData)

cyctemp[1].NewData:  # Index = 누적 Cycle 번호
    ├─ OriCyc        # 원본 Cycle 번호
    ├─ Dchg          # 방전 용량 (%)
    ├─ Eff           # 충방효율
    ├─ Temp          # 온도 (°C)
    ├─ RndV          # Rest End Voltage (V)
    ├─ Eff2          # 방충효율
    ├─ AvgV          # 평균 전압 (V)
    ├─ dcir          # DC-IR (mΩ)
    ├─ dcir2         # 대체 DC-IR (mkdcir 체크 시)
    ├─ soc70_dcir    # SOC 70% DC-IR
    ├─ soc70_rss_dcir# SOC 70% RSS DC-IR
    ├─ rssocv        # RSS_OCV
    └─ rssccv        # RSS_CCV
```

### 5-3. 채널 맵 (통합 범례 관리)

```python
channel_map = {
    "Sample A": {'artists': [scatter1, ..., scatter6], 'color': '#3C5488'},
    "Sample B": {'artists': [scatter1, ..., scatter6], 'color': '#E64B35'},
    "Sample A (2)": {'artists': [...], 'color': '#00A087'},  # 동일 이름 충돌 시
}
```

---

## 6. 3가지 모드 비교

| 항목 | link_cyc (기본) | indiv (개별) | overall (전체) |
|------|----------------|-------------|---------------|
| **경로 입력** | pne_path_setting() | CSV 파일 다중 선택 | CSV 파일 다중 선택 |
| **figure 개수** | 1개 (2×3) | CSV 파일 수 만큼 | 1개 (2×3) |
| **데이터 표시** | 모든 폴더 1 figure | 파일별 독립 figure | 모든 파일 누적 |
| **범례 관리** | channel_map | 파일별 독립 | channel_map 통합 |
| **진행률 기준** | total_folders | total_files | total_folders |

---

## 7. Index 누적 처리 (Cycle 연결 핵심)

```python
for i, cyclefolder in enumerate(all_data_folder):
    for sub_idx, FolderBase in enumerate(subfolder):
        if (i, sub_idx) in loaded_data:
            cyctemp = loaded_data[(i, sub_idx)][1]
            
            # 이전 Cycle 최대값 + 현재 데이터 → 연속 인덱스
            writerowno = link_writerownum[Chnl_num] + CycleMax[Chnl_num]
            cyctemp.NewData.index = cyctemp.NewData.index + writerowno
            
            # 그래프에 누적 표시
            graph_output_cycle(cyctemp[1], ...)
```

- 여러 폴더/파일의 Cycle 데이터를 **연속된 인덱스**로 이어붙이는 것이 핵심
- `CycleMax[Chnl_num]`: 채널별 누적 최대 Cycle 수 추적

---

## 8. 그래프 축 구성 (2×3 subplots)

| 위치 | 축 | 데이터 | Y축 범위 |
|------|------|--------|---------|
| (1,1) | ax1 | 방전 용량 (%) | ylimitlow ~ ylimithigh |
| (1,2) | ax2 | 충방효율 (%) | 0.992 ~ 1.004 |
| (1,3) | ax3 | 온도 (°C) | 0 ~ 50 |
| (2,1) | ax4 | DC-IR (mΩ) | 0 ~ 120×irscale |
| (2,2) | ax5 | 방충효율 (%) | 0.996 ~ 1.008 |
| (2,3) | ax6 | Rest/Avg 전압 (V) | 3.00 ~ 4.00 |

---

## 9. 색상 팔레트

```python
THEME['PALETTE'] = [
    '#3C5488',  # 진한 남색
    '#E64B35',  # 빨강
    '#00A087',  # 청록
    '#F39B7F',  # 연한 오렌지
    '#4DBBD5',  # 하늘색
    '#8491B4', '#B09C85', '#91D1C2', '#DC0000', '#7E6148'
]
# 순환: colorno % len(THEME['PALETTE'])
```

---

## 10. Excel 출력 구조

```
Sheet: "방전용량"   → OriCyc | Dchg (Sample A) | OriCyc | Dchg (Sample B) | ...
Sheet: "충방효율"   → OriCyc | Eff  | ...
Sheet: "Rest End"  → OriCyc | RndV | ...
Sheet: "평균 전압"  → OriCyc | AvgV | ...
Sheet: "DCIR"      → dcir, dcir2(선택), soc70_dcir, RSS 등
```
