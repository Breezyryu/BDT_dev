# 사이클데이터 탭 — Cycle / Profile 변수·데이터 정리

> 대상 파일: `DataTool_dev/DataTool_optRCD_proto_.py`
> 작성일: 2026-03-17

---

## 1. Cycle 기능 (사이클 수명 그래프)

### 1-1. UI 입력 변수 (`cyc_ini_set`)

| UI 위젯 | 변수명 | 타입 | 설명 |
|---|---|---|---|
| `ratetext` | `firstCrate` | float | 초기 C-rate |
| `inicaprate` / `inicaptype` | `mincapacity` | float | 공칭 용량 (0=자동산정, 그 외=수동입력) |
| `tcyclerng` | `xscale` | int | X축 눈금 간격 |
| `tcyclerngyhl` | `ylimithigh` | float | Y축 상한 |
| `tcyclerngyll` | `ylimitlow` | float | Y축 하한 |
| `dcirscale` | `irscale` | float | DC-IR Y축 스케일 |
| `dcirchk` | — | bool | DCIR(기본) 체크 |
| `dcirchk_2` | — | bool | DCIR(연속기준) 체크 |
| `mkdcir` | — | bool | RSS/1s pulse DCIR 체크 |
| `chk_coincell_cyc` | — | bool | 코인셀 모드 |
| `saveok` | — | bool | 엑셀 저장 여부 |
| `figsaveok` | — | bool | 그래프 이미지 저장 여부 |

### 1-2. Cycle 데이터 로딩 결과 (`df.NewData`)

`toyo_cycle_data()` / `pne_cycle_data()` 반환값: `[mincapacity, df]` → `df.NewData` DataFrame

| 컬럼명 | 의미 | 단위/비고 |
|---|---|---|
| `Dchg` | 방전 용량 비율 | Cap / mincapacity |
| `Chg` | 충전 용량 비율 | Cap / mincapacity |
| `RndV` | Rest End Voltage (OCV) | V |
| `AvgV` | 평균 방전 전압 | V (Pow / Cap) |
| `Eff` | 충방전 효율 | Dchg / Chg |
| `Eff2` | 방충전 효율 | Chg(next) / Dchg |
| `DchgEng` | 방전 에너지 | mWh |
| `Temp` | 피크 온도 | ℃ |
| `OriCyc` | 원본 사이클 번호 | Raw 파일의 TotlCycle |
| `dcir` | DC-IR (기본/RSS) | mΩ |
| `dcir2` | 1s pulse DC-IR (mkdcir 시) | mΩ |
| `rssocv` | RSS OCV (mkdcir 시) | V |
| `rssccv` | RSS CCV (mkdcir 시) | V |
| `soc70_dcir` | SOC70% 1s pulse DCIR | mΩ |
| `soc70_rss_dcir` | SOC70% RSS DCIR | mΩ |

### 1-3. 원시 CSV 로딩 컬럼

#### Toyo (`toyo_cycle_import`)

```
TotlCycle, Condition, Cap[mAh], Ocv, Finish, Mode, PeakVolt[V], Pow[mWh], PeakTemp[Deg], AveVolt[V]
```

#### PNE (`pne_cycle_data` — SaveEndData.csv, header=None)

| 인덱스 | 변환 후 컬럼명 | 설명 |
|---|---|---|
| 27 | `TotlCycle` | 총 사이클 |
| 2 | `Condition` | 충/방/휴지 구분 |
| 10 | `chgCap` | 충전 용량 (mAh) |
| 11 | `DchgCap` | 방전 용량 (mAh) |
| 8 | `Ocv` | 개방 전압 |
| 20 | `imp` | 임피던스 |
| 45 | `volmax` | 최대 전압 |
| 15 | `DchgEngD` | 방전 에너지 |
| 17 | `steptime` | 스텝 시간 |
| 9 | `Curr` | 전류 |
| 24 | `Temp` | 온도 |
| 29 | `AvgV` | 평균 전압 |
| 6 | `EndState` | 종료 상태 코드 |

### 1-4. Cycle 그래프 6축 구성 (`graph_output_cycle`)

| 축 | 데이터 | X축 | Y축 |
|---|---|---|---|
| `ax1` | `Dchg` | Cycle | Discharge Capacity Ratio |
| `ax2` | `Eff` | Cycle | Discharge/Charge Efficiency |
| `ax3` | `Temp` | Cycle | Temperature (℃) |
| `ax4` | `dcir` / `soc70_dcir` / `soc70_rss_dcir` | Cycle | DC-IR (mΩ) |
| `ax5` | `Eff2` | Cycle | Charge/Discharge Efficiency |
| `ax6` | `RndV` (filled) + `AvgV` (empty) | Cycle | Rest End / Average Voltage (V) |

### 1-5. 버튼별 동작

| 버튼 | 메서드 | 동작 |
|---|---|---|
| **개별 Cycle** | `indiv_cyc_confirm_button` | 폴더(조건)별 별도 6축 그래프 (탭 분리) |
| **통합 Cycle** | `overall_cyc_confirm_button` | 모든 채널을 하나의 6축 그래프에 중첩 |
| **연결 Cycle** | `link_cyc_confirm_button` | 다경로 데이터 연결 (전처리 → 병합 plot) |
| **연결개별** | `link_cyc_indiv_confirm_button` | 연결 + 개별 |
| **연결통합** | `link_cyc_overall_confirm_button` | 연결 + 통합 |
| **AppCycle** | `app_cyc_confirm_button` | 외부 엑셀(.xlsx) 승인 사이클 데이터 로딩 |

### 1-6. 엑셀 저장 시트 구성

| 시트명 | 컬럼 | 비고 |
|---|---|---|
| 방전용량 | `OriCyc`, `Dchg` | |
| Rest End | `OriCyc`, `RndV` | |
| 평균 전압 | `OriCyc`, `AvgV` | |
| 충방효율 | `OriCyc`, `Eff` | |
| 충전용량 | `OriCyc`, `Chg` | |
| 방충효율 | `OriCyc`, `Eff2` | |
| 방전Energy | `OriCyc`, `DchgEng` | |
| DCIR | `OriCyc`, `dcir` | 기본 모드 |
| SOC70_DCIR | `OriCyc`, `soc70_dcir` | mkdcir 모드 |
| SOC70_RSS | `OriCyc`, `soc70_rss_dcir` | mkdcir 모드 |
| RSS | `OriCyc`, `dcir` | mkdcir 모드 |
| RSS_OCV | `OriCyc`, `rssocv` | mkdcir 모드 |
| RSS_CCV | `OriCyc`, `rssccv` | mkdcir 모드 |

---

## 2. Profile 기능 (충방전 프로파일 그래프)

### 2-1. UI 입력 변수 (`Profile_ini_set`)

| UI 위젯 | 변수명 | 타입 | 설명 |
|---|---|---|---|
| `ratetext` | `firstCrate` | float | 초기 C-rate |
| `inicaprate` / `inicaptype` | `mincapacity` | float | 공칭 용량 |
| `stepnum` | `CycleNo` | list[int] | 프로파일 대상 사이클 번호 리스트 |
| `smooth` | `smoothdegree` | int | dQ/dV 미분 스무딩 차수 |
| `cutoff` | `mincrate` | float | 전류 cut-off (C-rate) |
| `dqdvscale` | `dqscale` / `dvscale` | float | dQ/dV, dV/dQ Y축 스케일 |
| `volrngyhl` | `vol_y_hlimit` | float | 전압 Y축 상한 |
| `volrngyll` | `vol_y_llimit` | float | 전압 Y축 하한 |
| `volrnggap` | `vol_y_gap` | float | 전압 Y축 간격 |

### 2-2. Profile 종류별 로딩 함수 & 출력

| Profile 종류 | Toyo 함수 | PNE 함수 | 출력 속성 | 출력 컬럼 |
|---|---|---|---|---|
| **Step (충전)** | `toyo_step_Profile_batch` | `pne_step_Profile_batch` | `df.stepchg` | `TimeMin`, `SOC`, `Vol`, `Crate`, `Temp` |
| **Rate (율별 충전)** | `toyo_rate_Profile_batch` | `pne_rate_Profile_batch` | `df.rateProfile` | `TimeMin`, `SOC`, `Vol`, `Crate`, `Temp` |
| **Chg (충전 dQ/dV)** | `toyo_chg_Profile_batch` | `pne_chg_Profile_batch` | `df.Profile` | `TimeMin`, `SOC`, `Energy`, `Vol`, `Crate`, `dQdV`, `dVdQ`, `Temp` |
| **Dchg (방전 dQ/dV)** | `toyo_dchg_Profile_batch` | `pne_dchg_Profile_batch` | `df.Profile` | `TimeMin`, `SOC`, `Energy`, `Vol`, `Crate`, `dQdV`, `dVdQ`, `Temp` |
| **Continue** | `toyo_continue_Profile_batch` | `pne_continue_Profile_batch` | — | 논리 사이클 → 파일 번호 자동 변환 |

### 2-3. 원시 프로파일 CSV 로딩 컬럼

#### Toyo (`toyo_Profile_import`)

```
PassTime[Sec], Voltage[V], Current[mA], Condition, Temp1[Deg]
```

#### PNE (SaveData, header=None)

| 인덱스 | 컬럼 | 단위 변환 |
|---|---|---|
| 17 | `PassTime[Sec]` | /100/60 → min |
| 8 | `Voltage[V]` | /1,000,000 → V |
| 9 | `Current[mA]` | /(mincap × 1000) → C-rate |
| 10 | `Chgcap` (충전) | /(mincap × 1000) → SOC ratio |
| 11 | `Dchgcap` (방전) | 동일 |
| 14 | `Chgwh` | Wh (충전 에너지) |
| 15 | `Dchgwh` | Wh (방전 에너지) |
| 21 | `Temp1[Deg]` | /1000 → ℃ |
| 7 | `step` | 스텝 연결 처리용 |

> **참고:** PNE21/22/코인셀(`is_micro_unit`)일 경우 divisor가 `mincapacity × 1,000,000`으로 변경됨

### 2-4. Step Profile 그래프 6축 구성 (`_plot_and_save_step_data`)

| 축 | 데이터 | X축 | Y축 |
|---|---|---|---|
| `step_ax1`, `step_ax2`, `step_ax3` | `Vol` | Time(min) | Voltage(V) |
| `step_ax4` | `SOC` | Time(min) | SOC |
| `step_ax5` | `Crate` | Time(min) | C-rate |
| `step_ax6` | `Temp` | Time(min) | Temperature (℃) |

---

## 3. 공통 경로/파일 관련 변수

| 변수명 | 소스 | 설명 |
|---|---|---|
| `all_data_folder` | `pne_path_setting()` 반환[0] | 데이터 폴더 경로 배열 |
| `all_data_name` | `pne_path_setting()` 반환[1] | 채널/조건 이름 배열 |
| `datafilepath` | `pne_path_setting()` 반환[2] | 원본 경로 (path 파일 또는 폴더) |
| `subfolder` | `os.scandir(cyclefolder)` | 채널별 하위 폴더 리스트 |
| `cycnamelist` | `FolderBase.split("\\")` | 폴더 경로 분할 → 범례/제목용 |
| `headername` | `cycnamelist[-2] + ", " + cycnamelist[-1]` | 엑셀 컬럼 헤더 |
| `ch_label` / `sub_label` | `_make_channel_labels()` | 채널 범례 라벨 (부모폴더/채널) |

---

## 4. 병렬 처리 구조

### Cycle 데이터

```
_load_all_cycle_data_parallel()
  └─ ThreadPoolExecutor
       └─ _load_cycle_data_task()
            ├─ PNE  → pne_cycle_data()
            └─ Toyo → toyo_cycle_data()
```

### Profile 데이터 (Step)

```
_load_all_step_data_parallel()
  └─ ThreadPoolExecutor
       └─ _load_step_batch_task()
            ├─ PNE  → pne_step_Profile_batch()
            └─ Toyo → toyo_step_Profile_batch()
```

### Profile 데이터 (Rate / Chg / Dchg / Continue)

```
_load_all_profile_data_parallel()
  └─ ThreadPoolExecutor
       └─ _load_profile_batch_task()
            ├─ profile_type='rate'     → toyo/pne_rate_Profile_batch()
            ├─ profile_type='chg'      → toyo/pne_chg_Profile_batch()
            ├─ profile_type='dchg'     → toyo/pne_dchg_Profile_batch()
            └─ profile_type='continue' → toyo/pne_continue_Profile_batch()
```

---

## 5. 전체 데이터 흐름

```
┌─────────────────────────────────────────────────────────┐
│  UI 입력                                                 │
│  cyc_ini_set() / Profile_ini_set()                       │
└──────────────┬──────────────────────────────────────────┘
               ▼
┌─────────────────────────────────────────────────────────┐
│  경로 설정                                               │
│  pne_path_setting() → all_data_folder, all_data_name     │
└──────────────┬──────────────────────────────────────────┘
               ▼
┌─────────────────────────────────────────────────────────┐
│  데이터 로딩 (병렬)                                       │
│  _load_all_cycle_data_parallel()                         │
│  _load_all_step_data_parallel()                          │
│  _load_all_profile_data_parallel()                       │
│    ↕                                                     │
│  toyo_cycle_data() / pne_cycle_data()                    │
│  toyo_*_Profile_batch() / pne_*_Profile_batch()          │
│    ↕                                                     │
│  반환: [mincapacity, df]                                  │
│    df.NewData (Cycle) / df.stepchg / df.Profile          │
└──────────────┬──────────────────────────────────────────┘
               ▼
┌─────────────────────────────────────────────────────────┐
│  그래프 출력                                              │
│  graph_output_cycle()      → 사이클 6축                   │
│  _plot_and_save_step_data() → 스텝 프로파일 6축           │
│  graph_profile()           → 충방전 프로파일               │
└──────────────┬──────────────────────────────────────────┘
               ▼
┌─────────────────────────────────────────────────────────┐
│  저장                                                    │
│  output_data()  → 엑셀 (.xlsx)                           │
│  output_fig()   → 그래프 이미지                           │
│  .to_csv()      → CSV (Continue 모드)                    │
└─────────────────────────────────────────────────────────┘
```
