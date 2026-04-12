# BatteryDataTool 데이터 파싱 후 처리 로직 정리

## 1. 데이터 구조 비교

### Toyo 충방전기
```
250207_..._1689mAh_ATL Q7M Inner 2C 상온수명 1-100cyc/
├── .CMT                    ← 설정 파일
└── 30/                     ← 채널 폴더 (subfolder)
    ├── 000001              ← cycle 1 데이터 (파일)
    ├── 000002              ← cycle 2 데이터
    ├── ...
    └── 000240
```

### PNE 충방전기
```
A1_MP1_4500mAh_T23_2/
├── Pattern/                ← 패턴 폴더 (스킵 대상)
├── M02Ch073[073]/          ← 채널 폴더 (subfolder)
│   ├── *.cts, *.cyc, *.saf, *.sch  ← 설정 파일
│   ├── Restore/            ← 실제 데이터
│   │   ├── ch09_SaveData0001.csv
│   │   ├── ch09_SaveData0002.csv
│   │   └── ...
│   └── StepStart/
└── M02Ch074[074]/
    └── ...
```

---

## 2. 충방전기 구분 로직

```
check_cycler(raw_file_path)
    │
    ├── Pattern 폴더 존재 → PNE (return True)
    └── Pattern 폴더 없음 → Toyo (return False)
```

---

## 3. 데이터 파싱 흐름

### Toyo 파싱

```
toyo_read_csv(폴더경로, cycle번호)
    │
    ├── args=1개 → filepath = args[0] + "\\capacity.log"  (사이클 데이터)
    └── args=2개 → filepath = args[0] + "\\%06d" % args[1] (프로파일 데이터)
                   예: cycle=1 → "30\\000001"
                       cycle=2 → "30\\000002"
    │
    └── pd.read_csv(filepath, ...) → DataFrame 반환
```

### PNE 파싱

```
pne_data(raw_file_path, inicycle)
    │
    ├── rawdir = raw_file_path + "\\Restore\\"
    ├── pne_search_cycle(rawdir, inicycle, inicycle + 1)
    │   └── SaveData CSV 파일들에서 해당 사이클이 포함된 파일 범위 탐색
    │       ★ filepos[0] == -1 이면 → filepos[0] = 0 으로 보정
    │
    └── subfile[filepos[0] : filepos[1]+1] 범위의 CSV 순차 로딩
        └── "SaveData" 포함 파일만 pd.read_csv → pd.concat → df.Profileraw
```

---

## 4. 기능별 데이터 처리 함수 매핑

| GUI 버튼 | 호출 메서드 | Toyo 함수 | PNE 함수 |
|----------|-----------|-----------|----------|
| **Step** | `step_confirm_button` | `toyo_step_Profile_data` | `pne_step_Profile_data` |
| **Rate** | `rate_confirm_button` | `toyo_rate_Profile_data` | `pne_rate_Profile_data` |
| **Chg** | `chg_confirm_button` | `toyo_chg_Profile_data` | `pne_chg_Profile_data` |
| **Dchg** | `dchg_confirm_button` | `toyo_dchg_Profile_data` | `pne_dchg_Profile_data` |
| **Continue** | `pro_continue_confirm_button` | `toyo_Profile_continue_data` | `pne_Profile_continue_data` |
| **DCIR** | `dcir_confirm_button` | ❌ (PNE only) | `pne_dcir_Profile_data` |
| **Cycle** | `indiv/overall/link_cyc_*` | `toyo_cycle_data` | `pne_cycle_data` |

---

## 5. 공통 처리 로직 (모든 프로파일 기능)

### 5-1. 초기화 단계

```python
# 모든 프로파일 기능이 동일하게 수행
init_data = self._init_confirm_button(button)
    ├── button.setDisabled(True)         # 중복 클릭 방지
    ├── config = self.Profile_ini_set()  # UI에서 설정값 로드
    │   ├── firstCrate    ← C-rate 설정
    │   ├── mincapacity   ← 최소 용량 (mAh)
    │   ├── CycleNo       ← 사이클 번호 리스트 (stepnum 텍스트 파싱)
    │   ├── smoothdegree  ← dQ/dV 스무딩 정도
    │   ├── mincrate      ← cutoff C-rate
    │   ├── dqscale       ← dQ/dV 스케일
    │   └── dvscale       ← dV/dQ 스케일
    ├── pne_path = self.pne_path_setting()  # 데이터 경로 설정
    │   ├── all_data_folder  ← 폴더 경로 리스트
    │   └── all_data_name    ← 표시 이름 리스트
    └── button.setEnabled(True)
```

### 5-2. 파일 저장 설정

```python
writer, save_file_name = self._setup_file_writer()
    ├── saveok 체크 → Excel writer 생성 (.xlsx)
    └── ect_saveok 체크 → CSV 저장 경로 설정
```

### 5-3. 폴더 순회 구조 (공통 3중 루프)

```
for i, cyclefolder in enumerate(all_data_folder):     ← 데이터 폴더
    │
    ├── is_pne = check_cycler(cyclefolder)            ← 충방전기 판별 (1회)
    │
    └── for FolderBase in subfolder:                  ← 채널 폴더
        │
        ├── "Pattern" in FolderBase → skip            ← PNE 패턴 폴더 제외
        │
        └── for CycNo in CycleNo:                    ← 사이클 번호
            │
            ├── if not is_pne:
            │   └── temp = toyo_xxx_data(FolderBase, CycNo, ...)
            │
            └── else:
                └── temp = pne_xxx_data(FolderBase, CycNo, ...)
```

### 5-4. 프로파일 모드 분기 (공통)

```
┌─────────────────────────────────────────────────────────┐
│  CycProfile 체크?  AllProfile 체크?  → 어떤 모드?       │
├─────────────────────────────────────────────────────────┤
│  ✅ CycProfile     -                → 채널별 개별 탭     │
│  ❌                ✅ AllProfile    → 전체 1개 탭 통합   │
│  ❌                ❌              → 사이클별 개별 탭    │
└─────────────────────────────────────────────────────────┘
```

| 모드 | fig 생성 | 탭 생성 | 범례 |
|------|---------|--------|------|
| **CycProfile** | 채널마다 새 fig | 채널마다 새 탭 | 사이클 번호 (`%04d`) |
| **AllProfile** | 루프 전 1개 | 루프 후 1개 | `채널명 + 사이클번호` |
| **기본(사이클별)** | 사이클마다 새 fig | 사이클마다 새 탭 | 채널명 |

### 5-5. 그래프 출력 (공통 6패널)

```
fig (2×3 subplots)
┌──────────┬──────────┬──────────┐
│  ax1     │  ax2     │  ax3     │
│ V vs X   │ dQ/dV    │ SOC/V   │
│          │ or C-rate│          │
├──────────┼──────────┼──────────┤
│  ax4     │  ax5     │  ax6     │
│ V (확대) │ C-rate   │ Temp    │
│ or dV/dQ │ or SOC   │          │
└──────────┴──────────┴──────────┘
```

각 기능별 6패널 내용:

| 패널 | Step | Rate | Chg/Dchg | Continue | DCIR |
|------|------|------|----------|----------|------|
| ax1 | V-Time | V-Time | V-SOC | V-Time | OCV/CCV-SOC |
| ax2 | V-Time | C-Time | dQdV-V | C-rate-Time | DCIR-SOC |
| ax3 | V-Time | SOC-Time | V-SOC | SOC-Time | SOC-V |
| ax4 | SOC-Time | V-Time | dVdQ-SOC | V+OCV/CCV-Time | DCIR-OCV |
| ax5 | C-Time | C-Time | C-SOC | OCV/CCV-SOC | - |
| ax6 | Temp-Time | Temp-Time | Temp-SOC | Temp-Time | - |

### 5-6. 데이터 저장 (공통)

```python
# Excel 저장 (saveok)
if self.saveok.isChecked() and save_file_name:
    df.to_excel(writer, sheet_name="...", startcol=write_column_num, ...)
    write_column_num += N  # 컬럼 오프셋 증가

# CSV 저장 (ect_saveok) - ECT 포맷
if self.ect_saveok.isChecked() and save_file_name:
    continue_df = df[["TimeSec", "Vol", "Curr", "Temp"]]
    continue_df.to_csv(..., header=["time(s)", "Voltage(V)", "Current(A)", "Temp."])
```

### 5-7. 탭 마무리 (공통)

```python
# 범례 설정
self._setup_legend(axes_list, all_data_name, positions, fig=fig)
    ├── 항목 < LEGEND_THRESHOLD(15) → 일반 범례
    └── 항목 ≥ LEGEND_THRESHOLD     → 그라데이션 + 컬러바

# 탭 최종화
self._finalize_plot_tab(tab, tab_layout, canvas, toolbar, tab_no)
    ├── toolbar + canvas 추가
    └── cycle_tab에 탭 등록

# 그래프 이미지 저장
output_fig(self.figsaveok, title)
```

---

## 6. 반환 데이터 구조 (공통)

```python
temp = toyo/pne_xxx_data(...)
temp[0]  → capacity (mAh)           ← int/float
temp[1]  → 프로파일 데이터 객체
    ├── .stepchg    (Step/Continue)  ← DataFrame
    ├── .Profile    (Chg/Dchg)       ← DataFrame
    ├── .rateProfile (Rate)          ← DataFrame
    │
    │   공통 컬럼:
    │   ├── TimeMin  ← 시간 (분)
    │   ├── TimeSec  ← 시간 (초)
    │   ├── Vol      ← 전압 (V)
    │   ├── Curr     ← 전류 (A)
    │   ├── Crate    ← C-rate
    │   ├── SOC      ← 충전상태
    │   ├── Temp     ← 온도 (℃)
    │   ├── dQdV     ← 미분용량 (Chg/Dchg만)
    │   ├── dVdQ     ← 미분전압 (Chg/Dchg만)
    │   └── Energy   ← 에너지 (Chg/Dchg만)
    │
temp[2]  → OCV/CCV 데이터 (Continue/DCIR만)  ← DataFrame (optional)
    ├── AccCap / SOC
    ├── OCV
    └── CCV
```

---

## 7. 사이클 데이터 처리 (Cycle 기능)

```
_load_all_cycle_data_parallel()  ← ThreadPoolExecutor 병렬 처리
    │
    ├── toyo_cycle_data(path, mincapacity, inirate, chkir)
    └── pne_cycle_data(path, mincapacity, inirate, chkir)
    │
    └── 반환: DataFrame (사이클별 요약)
        ├── ChgCap     ← 충전 용량
        ├── DchgCap    ← 방전 용량
        ├── Efficiency ← 쿨롱 효율
        ├── CE         ← 에너지 효율
        ├── IR         ← 내부저항
        └── Temp       ← 온도

그래프 출력 (graph_output_cycle):
    ax1: 충전 용량 vs Cycle
    ax2: 방전 용량 vs Cycle
    ax3: 쿨롱 효율 vs Cycle
    ax4: 에너지 효율 vs Cycle
    ax5: IR vs Cycle
    ax6: 온도 vs Cycle
```

---

## 8. 사이클 표시 모드 비교 (Cycle 기능)

| 모드 | 메서드 | 그래프 | 설명 |
|------|--------|--------|------|
| **개별** | `indiv_cyc_confirm_button` | 채널당 1개 fig | 각 채널 독립 그래프 |
| **통합** | `overall_cyc_confirm_button` | 전체 1개 fig | 모든 채널 오버레이 |
| **연결** | `link_cyc_confirm_button` | 전체 1개 fig | X축 사이클 연결 |

---

## 9. 사이클 데이터 파싱 상세

### 9-1. 용량 산정 (공통 선행 처리)

```
사용자 입력 mincapacity
    │
    ├── mincapacity > 0 → 그대로 사용
    │
    └── mincapacity == 0 → 자동 산정
        │
        ├── "mAh" in 경로명 → name_capacity(경로)로 파일명에서 추출
        │
        ├── Toyo: toyo_min_cap()
        │   └── 첫 사이클(000001) 로딩 → Current[mA].max() / inirate
        │       예) 3378mA / 0.2C → 16890 → round → 16890mAh (× 실제로는 mAh 단위)
        │
        └── PNE: pne_min_cap()
            └── SaveData0001.csv 로딩 → abs(iloc[2, 9]) / 1000 / ini_crate
                예) 3378000μA → 3378mA / 0.2C → 16890mAh
```

### 9-2. Toyo 사이클 데이터 파싱

```
toyo_cycle_data(raw_file_path, mincapacity, inirate, chkir)
    │
    ├── toyo_min_cap() → mincapacity 산정
    │
    ├── toyo_cycle_import(raw_file_path)
    │   └── toyo_read_csv(raw_file_path)  ← args=1개 → capacity.log 로딩
    │       └── DataFrame (모든 스텝의 요약 데이터)
    │           컬럼: TotlCycle, Condition, Cap[mAh], Ocv, Finish, Mode,
    │                 PeakVolt[V], Pow[mWh], PeakTemp[Deg], AveVolt[V]
    │
    ├── 전처리
    │   ├── OriCycle 백업 (원본 사이클 번호 보존)
    │   ├── 방전 시작 보정: 첫 행이 Condition==2이면 TotlCycle -= 1
    │   └── 연속 동일 Condition 병합 (merge_rows)
    │       ├── 충전(1): Cap 합산, Ocv는 첫 번째
    │       └── 방전(2): Cap/Pow 합산, AveVolt 재계산
    │
    ├── 충전 데이터 추출
    │   └── Condition==1 ∧ Finish!="Vol"/"Volt" ∧ Cap > mincap/60
    │       → Chg (충전용량), Ocv (Rest End Voltage)
    │
    ├── 방전 데이터 추출
    │   └── Condition==2 ∧ Cap > mincap/60
    │       → Dchg(방전용량), Temp(온도), DchgEng(에너지), AvgV(평균전압)
    │
    ├── DCIR 추출
    │   └── Condition==2 ∧ Finish=="Tim"/"Time" ∧ Cap < mincap/60
    │       → 해당 사이클의 원시 데이터 로딩 → (Vmax - Vmin) / Imax * 10^6
    │
    ├── 효율 계산
    │   ├── Eff = Dchg / Chg           (방전/충전 효율)
    │   └── Eff2 = Chg_next / Dchg     (충전/방전 효율)
    │
    ├── 용량 정규화
    │   ├── Dchg = Dchg / mincapacity  (ratio 변환)
    │   └── Chg = Chg / mincapacity
    │
    └── 반환: [mincapacity, df]
        └── df.NewData = DataFrame
            ├── Dchg    (방전용량 ratio)
            ├── RndV    (Rest End Voltage)
            ├── Eff     (방충효율)
            ├── Chg     (충전용량 ratio)
            ├── DchgEng (방전에너지)
            ├── Eff2    (충방효율)
            ├── Temp    (온도)
            ├── AvgV    (평균전압)
            ├── OriCyc  (원본 사이클번호)
            └── dcir    (내부저항, mΩ)
```

### 9-3. PNE 사이클 데이터 파싱

```
pne_cycle_data(raw_file_path, mincapacity, ini_crate, chkir, chkir2, mkdcir)
    │
    ├── pne_min_cap() → mincapacity 산정
    │
    ├── SaveEndData.csv 로딩 (각 스텝 종료 시점 요약)
    │   └── 원시 컬럼 인덱스 매핑:
    │       27:TotlCycle, 2:Condition(1=충전,2=방전,3=휴지,8=loop)
    │       10:chgCap, 11:DchgCap, 8:Ocv(mV→V), 20:imp
    │       45:volmax, 15:DchgEngD, 17:steptime, 9:Curr
    │       24:Temp, 29:AvgV, 6:EndState
    │
    ├── PNE21/PNE22 보정 (단위 차이: /1000 추가)
    │
    ├── DCIR 모드 분기
    │   │
    │   ├── chkir=True (기본 DCIR)
    │   │   └── Condition==2 ∧ volmax > 4100000 → imp/1000
    │   │
    │   ├── mkdcir=True (1s pulse + RSS DCIR)
    │   │   ├── dcirtemp1: EndState==78 ∧ |Curr| ≥ 0.15C → RSS CCV
    │   │   ├── dcirtemp2: steptime==100 ∧ EndState==64 ∧ Condition∈{1,2} → 1s pulse CCV
    │   │   ├── dcirtemp3: steptime∈{90000,...} ∧ EndState==64 ∧ Condition==3 → RSS OCV
    │   │   └── 계산:
    │   │       ├── RSS DCIR = |OCV_rest - CCV_rss| / I_rss * 1000
    │   │       ├── 1s DCIR = |CCV_1s - CCV_rss| / (I_rss - I_1s) * 1000
    │   │       ├── SOC70 추출: 6개 중 4번째 or 4개 중 1번째
    │   │       └── rssocv, rssccv 저장
    │   │
    │   └── else (10s pulse DCIR)
    │       └── Condition==2 ∧ steptime ≤ 6000 → imp/1000
    │
    ├── pivot_table로 사이클별 집계 (한번에 계산)
    │   ├── DchgCap: sum (Condition=2) → / mincapacity / 1000
    │   ├── DchgEngD: sum (Condition=2) → / 1000
    │   ├── chgCap: sum (Condition=1) → / mincapacity / 1000
    │   ├── Ocv: min (Condition=3) → / 1000000
    │   └── Temp: max (Condition=2) → / 1000
    │
    ├── 효율 계산
    │   ├── Eff = Dchg / Chg
    │   ├── Eff2 = Chg_next / Dchg
    │   └── AvgV = DchgEng / Dchg / mincapacity * 1000
    │
    └── 반환: [mincapacity, df]
        └── df.NewData = DataFrame (Toyo와 동일 구조)
            ├── Dchg, RndV, Eff, Chg, DchgEng, Eff2, Temp, AvgV, OriCyc
            ├── dcir          (RSS 또는 10s pulse)
            ├── dcir2         (1s pulse, mkdcir 시)
            ├── rssocv        (RSS OCV, mkdcir 시)
            ├── rssccv        (RSS CCV, mkdcir 시)
            ├── soc70_dcir    (SOC70 1s DCIR, mkdcir 시)
            └── soc70_rss_dcir (SOC70 RSS DCIR, mkdcir 시)
```

### 9-4. Toyo vs PNE 사이클 파싱 비교

| 항목 | Toyo | PNE |
|------|------|-----|
| **데이터 소스** | `capacity.log` (1파일) | `SaveEndData.csv` (1파일) |
| **Condition 코드** | 1=충전, 2=방전 | 1=충전, 2=방전, 3=휴지, 8=loop |
| **EndState** | `Finish` 문자열 (Vol, Tim) | 숫자 코드 (64=휴지, 65=전압, 66=전류, 78=용량) |
| **단위** | mAh, V, ℃ 그대로 | μV→V(/10⁶), μA→A(/10³), m℃→℃(/10³) |
| **PNE21/22** | - | 추가 /1000 보정 필요 |
| **병합 로직** | 연속 동일 Condition 그룹화 | 불필요 (SaveEndData가 이미 스텝별 1행) |
| **DCIR** | 원시 프로파일 로딩 후 계산 | imp 컬럼 직접 사용 또는 계산 |
| **DCIR 종류** | 단순 (Vmax-Vmin)/I | 기본/10s pulse/1s pulse+RSS 3모드 |

---

## 10. 사이클 데이터 병렬 처리 상세

### 10-1. 병렬 로딩 아키텍처

```
GUI 버튼 클릭 (indiv/overall/link_cyc_confirm_button)
    │
    ├── cyc_ini_set() → firstCrate, mincapacity, xscale, ylimit, irscale
    ├── pne_path_setting() → all_data_folder, all_data_name
    │
    ├── _load_all_cycle_data_parallel(max_workers=4)
    │   │
    │   ├── 태스크 수집 (모든 폴더/채널 조합)
    │   │   for i, cyclefolder in all_data_folder:
    │   │       is_pne = check_cycler(cyclefolder)
    │   │       for j, folder_path in subfolder:
    │   │           if "Pattern" not in folder_path:
    │   │               tasks.append((folder_path, mincap, crate, dcir옵션, is_pne, i, j))
    │   │
    │   ├── ThreadPoolExecutor 실행
    │   │   ├── _load_cycle_data_task(task_info) × N개 병렬
    │   │   │   ├── is_pne → pne_cycle_data()
    │   │   │   └── !is_pne → toyo_cycle_data()
    │   │   │
    │   │   └── 진행률: 0% ~ 50% (로딩 단계)
    │   │
    │   └── 반환: results = {(i, j): (folder_path, cyctemp), ...}
    │
    └── 그래프 생성 루프 (50% ~ 100%)
        for i, cyclefolder in all_data_folder:
            for sub_idx, FolderBase in subfolder:
                (folder_path, cyctemp) = loaded_data[(i, sub_idx)]
                graph_output_cycle(cyctemp, ...)
```

### 10-2. graph_output_cycle 6패널 상세

```
graph_output_cycle(df, xscale, ylimitlow, ylimithigh, irscale, lgnd, temp_lgnd,
                   colorno, graphcolor, dcir, ax1~ax6)

┌─────────────────────┬─────────────────────┬─────────────────────┐
│ ax1                 │ ax2                 │ ax3                 │
│ Dchg vs Cycle       │ Eff(방충) vs Cycle   │ Temp vs Cycle       │
│ Y: ylimitlow~high   │ Y: 0.992~1.004      │ Y: 0~50℃           │
├─────────────────────┼─────────────────────┼─────────────────────┤
│ ax4                 │ ax5                 │ ax6                 │
│ DCIR vs Cycle       │ Eff2(충방) vs Cycle  │ RndV + AvgV vs Cyc  │
│ Y: 0~120*irscale    │ Y: 0.996~1.008      │ Y: 3.0~4.0V         │
│                     │                     │ (실선=RndV, 빈원=AvgV)│
└─────────────────────┴─────────────────────┴─────────────────────┘

DCIR 모드별 ax4:
├── mkdcir 체크 + dcir2 존재 → soc70_dcir(빈원) + soc70_rss_dcir(실선)
└── 기본 → dcir (실선)
```

### 10-3. 사이클 표시 모드별 차이 상세

#### 개별 (indiv_cyc_confirm_button)
```
for i, cyclefolder:            ← 폴더별 새 fig 생성
    fig = plt.subplots(2, 3)
    for FolderBase:            ← 같은 fig에 오버레이
        graph_output_cycle()
    tab에 추가               ← 폴더당 1개 탭
    colorno = 0 (리셋)
```

#### 통합 (overall_cyc_confirm_button)
```
fig = plt.subplots(2, 3)      ← 전체 1개 fig
for i, cyclefolder:
    for FolderBase:
        graph_output_cycle()   ← 전부 같은 fig에 오버레이
    colorno = colorno % 9 + 1  ← 폴더별 색상 순환
tab에 추가                    ← 전체 1개 탭
+ Legend ON/OFF 체크박스 추가
```

#### 연결 (link_cyc_confirm_button)
```
fig = plt.subplots(2, 3)      ← 전체 1개 fig
CycleMax = [0,0,0,0,0]        ← 채널별 누적 사이클 수
link_writerownum = [0,0,0,0,0]

for i, cyclefolder:
    for FolderBase:
        writerowno = link_writerownum[Chnl] + CycleMax[Chnl]
        cyctemp.NewData.index += writerowno  ★ X축 이어붙이기
        graph_output_cycle()
        CycleMax[Chnl] = len(cyctemp.NewData)
        link_writerownum[Chnl] = writerowno
tab에 추가                    ← 전체 1개 탭
```

#### 개별연결 (link_cyc_indiv_confirm_button)
```
for k, datafilepath:           ← CSV 파일별 새 fig
    fig = plt.subplots(2, 3)
    all_data_folder → CSV에서 읽기
    for i, cyclefolder:
        for FolderBase:
            index += writerowno  ★ X축 이어붙이기
    tab에 추가                ← 파일당 1개 탭
```

#### 통합연결 (link_cyc_overall_confirm_button)
```
fig = plt.subplots(2, 3)      ← 전체 1개 fig
for k, datafilepath:           ← 여러 CSV 파일
    all_data_folder → CSV에서 읽기
    for i, cyclefolder:
        for FolderBase:
            index += writerowno  ★ X축 이어붙이기
    maxcolor 업데이트          ← 파일별 색상 오프셋
tab에 추가                    ← 전체 1개 탭
```

---

## 11. 사이클 데이터 엑셀 저장 구조

```
output_data(df.NewData, 컬럼명, writecolno, writerowno, 시트명, headername)

저장되는 시트 목록:
├── "Dchg"      → 방전용량 ratio
├── "RndV"      → Rest End Voltage
├── "AvgV"      → 평균 전압
├── "Eff"       → 방전/충전 효율
├── "Chg"       → 충전용량 ratio
├── "Eff2"      → 충전/방전 효율
├── "DchgEng"   → 방전 에너지
├── "dcir"      → RSS DCIR (mkdcir 시)
├── "dcir2"     → 1s pulse DCIR (mkdcir 시)
├── "rssocv"    → RSS OCV (mkdcir 시)
├── "rssccv"    → RSS CCV (mkdcir 시)
├── "soc70_dcir"     → SOC70 1s DCIR (mkdcir 시)
├── "soc70_rss_dcir" → SOC70 RSS DCIR (mkdcir 시)
└── "OriCyc"    → 원본 충방전기 사이클 번호

연결 모드 시: writerowno 오프셋으로 행 위치 조정
    → 여러 폴더 데이터가 세로로 이어짐
```
