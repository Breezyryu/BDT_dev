---
date: 2026-04-10
tags: [python, BDT, 코드학습, PNE, 바이너리, cyc, CSV, SaveEndData, SaveData]
aliases: [pne_cyc_csv_comparison, PNE파일구조비교]
---

# PNE .cyc 바이너리 vs CSV 파일 구조 상세 비교

> **학습 목표**: PNE 충방전기의 원본 `.cyc` 바이너리 파일과,
> 자정마다 자동 출력되는 `SaveEndData.csv` / `chXX_SaveDataXXXX.csv` 파일의
> **행/열 구조를 1:1로 대응**시켜 이해한다.

**선행 학습**: [[260409_study_01_cycle_data_pipeline_overview|Study 01: 파이프라인 전체 흐름]]
             [[260409_study_03_pne_cycle_data|Study 03: PNE 사이클 데이터 처리]]

---

## 1. PNE 데이터 파일 체계 (원본 → 파생)

```
PNE 충방전기 (장비)
│
├── ch01_xxxx.cyc          ← 🔴 원본: 바이너리 실시간 기록 (시험 중 계속 갱신)
│
└── Restore/               ← 🟢 파생: 자정마다 .cyc → CSV 자동 변환
    ├── SaveEndData.csv           ← 사이클 요약 (스텝 종료 시점 1행씩)
    ├── savingFileIndex_start.csv ← SaveData 파일별 시작 인덱스
    ├── chXX_SaveData0001.csv     ← 시계열 상세 데이터 (파일 1)
    ├── chXX_SaveData0002.csv     ← 시계열 상세 데이터 (파일 2)
    └── ...
```

### 핵심 관계

| 구분 | `.cyc` | `SaveEndData.csv` | `chXX_SaveDataXXXX.csv` |
|------|--------|-------------------|------------------------|
| **역할** | 원본 바이너리 | 사이클/스텝 요약 | 시계열 상세 데이터 |
| **갱신 시점** | 실시간 (시험 중) | 자정 자동 출력 | 자정 자동 출력 |
| **1행 = ?** | 1 레코드 (고정 간격 샘플링) | 1 스텝 종료 시점 | 1 레코드 (시계열 샘플) |
| **행 수 (예시)** | 수십만~수백만 행 | 수백~수천 행 | 수만~수십만 행/파일 |
| **용도 (BDT)** | 프로파일, .cyc 보충 | **사이클 분석 주력** | 프로파일 분석 |
| **인코딩** | 바이너리 (little-endian) | cp949 (CSV) | cp949 (CSV) |

---

## 2. SaveEndData.csv — 사이클 요약 (스텝 종료 데이터)

> BDT에서 사이클 분석의 **주력 데이터 소스**.
> 자정마다 `.cyc`에서 각 스텝의 **마지막 레코드(종료 시점)**를 추출하여 1행으로 기록.

### 컬럼 구조 (48개 컬럼, 정수 인덱스 0~47)

| 컬럼 인덱스 | 필드명 | 단위 | 설명 | BDT 사용 여부 |
|:-----------:|--------|------|------|:------------:|
| **0** | Index | - | 전체 레코드 순번 (0부터) | ✅ `pne_search_cycle` 파일 위치 산정 |
| 1 | StepMode | - | 1=CC-CV, 2=CC, 3=CV, 4=OCV | - |
| **2** | StepType | - | 1=충전, 2=방전, 3=휴지, 4=OCV, 5=Impedance, 6=End, 8=Loop, 9=CC-CV합산 | ✅ Condition |
| 3 | ChgDchg | - | 충방전 구분 | - |
| 4 | State | - | 상태 코드 | - |
| 5 | Loop | - | 루프 플래그 (255=패턴, 1=루프) | - |
| **6** | EndState | - | 종료 조건: 64=휴지/loop, 65=전압도달, 66=전류도달(충전), 78=용량도달 | ✅ DCIR 필터 |
| **7** | StepNo | - | 스텝 번호 | ✅ 프로파일 |
| **8** | Voltage | **μV** | 스텝 종료 시 전압 | ✅ Ocv, volmax |
| **9** | Current | **μA** | 스텝 종료 시 전류 | ✅ Curr |
| **10** | ChgCapacity | **μAh** | 누적 충전 용량 | ✅ chgCap |
| **11** | DchgCapacity | **μAh** | 누적 방전 용량 | ✅ DchgCap |
| 12 | ChgPower | μW | 충전 전력 | - |
| 13 | DchgPower | μW | 방전 전력 | - |
| 14 | ChgWattHour | Wh | 충전 에너지 | ✅ 프로파일 |
| **15** | DchgWattHour | Wh | 방전 에너지 | ✅ DchgEngD |
| 16 | - | - | (미사용) | - |
| **17** | StepTime | **/100초** | 스텝 경과 시간 (= 실제초 × 100) | ✅ steptime, DCIR 필터 |
| 18 | TotTime(day) | day | 총 시간 (일 부분) | ✅ 연속 프로파일 |
| 19 | TotTime(/100s) | /100초 | 총 시간 (초 부분) | ✅ 연속 프로파일 |
| **20** | imp | **μΩ** | 임피던스 (내부저항) | ✅ dcir 계산 |
| 21 | Temp1 | **m°C** | 온도1 (= °C × 1000) | ✅ 프로파일 Temp |
| 22 | Temp2 | m°C | 온도2 | - |
| 23 | Temp3 | m°C | 온도3 | - |
| **24** | Temperature | **m°C** | 대표 온도 (= °C × 1000) | ✅ Temp |
| 25 | - | - | (미사용) | - |
| 26 | - | - | (미사용) | - |
| **27** | TotalCycle | - | 전체 사이클 번호 | ✅ TotlCycle (핵심 키) |
| 28 | CurrCycle | - | 현재 사이클 번호 | - |
| **29** | AverageVoltage | **mV** | 평균 전압 | ✅ AvgV |
| 30 | AverageCurrent | A | 평균 전류 | - |
| 31 | - | - | (미사용) | - |
| 32 | - | - | (미사용) | - |
| 33 | date | - | 날짜 | - |
| 34 | time | - | 시간 | - |
| 35~43 | - | - | (미사용) | - |
| 44 | 누적step | - | 누적 스텝 수 (Loop/완료 제외) | - |
| **45** | voltage_max | **μV** | 스텝 내 최대 전압 | ✅ volmax |
| 46 | - | - | (미사용) | - |
| 47 | - | - | (미사용) | - |

### BDT가 사용하는 13개 핵심 컬럼

```python
# pne_cycle_data() L7315 — SaveEndData에서 추출하는 컬럼
Cycleraw = save_end_cached[[27, 2, 10, 11, 8, 20, 45, 15, 17, 9, 24, 29, 6]].copy()
Cycleraw.columns = ["TotlCycle", "Condition", "chgCap", "DchgCap", "Ocv", "imp",
                     "volmax", "DchgEngD", "steptime", "Curr", "Temp", "AvgV", "EndState"]
```

| Cycleraw 컬럼 | CSV 인덱스 | 원시 단위 | BDT 변환 후 단위 |
|:-------------:|:---------:|:---------:|:---------------:|
| TotlCycle | 27 | - | - (그대로) |
| Condition | 2 | - | - (1=충전, 2=방전, 3=휴지, 8=루프) |
| chgCap | 10 | μAh | → mAh (÷1000) → ratio (÷공칭용량) |
| DchgCap | 11 | μAh | → mAh (÷1000) → ratio (÷공칭용량) |
| Ocv | 8 | μV | → V (÷1,000,000) |
| imp | 20 | μΩ | → mΩ (÷1000) |
| volmax | 45 | μV | → V (÷1,000,000) |
| DchgEngD | 15 | Wh | → Wh (그대로) |
| steptime | 17 | /100초 | → 초 (÷100) |
| Curr | 9 | μA | → C-rate (÷공칭용량÷1000) |
| Temp | 24 | m°C | → °C (÷1000) |
| AvgV | 29 | mV | → V (÷1000) |
| EndState | 6 | - | - (64=휴지, 65=전압, 66=전류) |

### SaveEndData 행 구조 예시 (1 사이클 = 여러 행)

```
사이클 1의 스텝 구조 예시:
┌──────────┬───────────┬────────┬──────────┬────────┬──────────┐
│ Index(0) │ StepType(2)│Voltage(8)│Current(9)│StepTime(17)│TotlCycle(27)│
├──────────┼───────────┼────────┼──────────┼────────┼──────────┤
│    0     │  1 (충전)  │ 4200000│  500000  │  360000│    1     │  ← CC 충전 종료
│    1     │  1 (충전)  │ 4200000│   25000  │  180000│    1     │  ← CV 충전 종료
│    2     │  3 (휴지)  │ 4185000│       0  │   60000│    1     │  ← 충전 후 휴지
│    3     │  2 (방전)  │ 2500000│ -500000  │  360000│    1     │  ← CC 방전 종료
│    4     │  3 (휴지)  │ 3200000│       0  │   60000│    1     │  ← 방전 후 휴지
│    5     │  8 (루프)  │ 3200000│       0  │      0 │    1     │  ← 사이클 루프 마커
└──────────┴───────────┴────────┴──────────┴────────┴──────────┘
사이클 2:
│    6     │  1 (충전)  │ 4200000│  500000  │  360000│    2     │
│   ...    │   ...     │  ...   │   ...    │  ...   │   ...    │
```

**핵심 포인트**:
- **1 사이클 ≠ 1행**. 1 사이클 = 충전/CV/휴지/방전/휴지/루프 등 **여러 스텝의 종료 행**
- BDT는 `pivot_table(index="TotlCycle")` 로 사이클 단위로 집계
- 루프 마커(StepType=8)는 사이클 경계 식별에 사용

---

## 3. chXX_SaveDataXXXX.csv — 시계열 상세 데이터

> 충방전 중 **일정 간격으로 샘플링**한 전체 시계열 데이터.
> BDT에서 **프로파일 분석** (전압-시간 곡선, dQ/dV 등)에 사용.

### 컬럼 구조 (SaveEndData와 동일한 48개 컬럼)

`SaveEndData.csv`와 **완전히 동일한 컬럼 구조**를 가진다. 차이는 **행의 의미**:

| 구분 | SaveEndData.csv | chXX_SaveDataXXXX.csv |
|------|-----------------|----------------------|
| **1행의 의미** | 스텝 **종료** 시점 | 일정 간격 **샘플링** 시점 |
| **행 수** | 스텝 수 (수백~수천) | 샘플 수 (수만~수십만) |
| **시간 해상도** | 스텝 단위 (분~시간) | 초 단위 (0.1~10초 간격) |
| **용도** | 사이클 요약/트렌드 | 프로파일/파형 분석 |

### SaveData 파일 분할 규칙

- PNE 장비는 **파일당 최대 행 수**에 도달하면 새 파일 생성
- `SaveData0001.csv` → `SaveData0002.csv` → ...
- `savingFileIndex_start.csv`에 각 파일의 시작 Index 기록
- BDT의 `pne_search_cycle()`이 이 인덱스로 **필요한 파일만 선택 로드**

```python
# pne_data() L6515-6534 — 프로파일용 SaveData 로드
def pne_data(raw_file_path, inicycle):
    filepos = pne_search_cycle(rawdir, inicycle, inicycle + 1)  # 파일 위치 산정
    for files in subfile[filepos[0]:filepos[1]+1]:
        if "SaveData" in files:
            dfs.append(pd.read_csv(...))  # 해당 파일만 로드
    df.Profileraw = pd.concat(dfs)
```

### BDT가 프로파일에서 사용하는 컬럼

```python
# pne_chg_Profile_data() L7392 — 충전 프로파일
df.Profileraw = df.Profileraw[[17, 8, 9, 10, 14, 21, 7]]
#                               │   │   │   │   │   │   └─ 7: StepNo
#                               │   │   │   │   │   └──── 21: Temp1 (m°C)
#                               │   │   │   │   └─────── 14: ChgWattHour (Wh)
#                               │   │   │   └────────── 10: ChgCapacity (μAh)
#                               │   │   └───────────── 9: Current (μA)
#                               │   └──────────────── 8: Voltage (μV)
#                               └─────────────────── 17: StepTime (/100s)
df.Profileraw.columns = ["PassTime[Sec]", "Voltage[V]", "Current[mA]",
                          "Chgcap", "Chgwh", "Temp1[Deg]", "step"]
```

---

## 4. .cyc 바이너리 파일 — 원본 데이터

> `.cyc`는 PNE 장비가 **실시간으로 기록**하는 바이너리 파일.
> SaveEndData/SaveData CSV는 이 파일에서 자정마다 파생된다.

### 바이너리 구조

```
┌─────────────────────────────────────────┐
│ 헤더 (0x000 ~ 0x1AF)                     │
│  ├─ 0x148: n_fields (uint32 LE)          │  ← 레코드당 필드 수
│  ├─ 0x14C: FieldID 배열 (uint16 × n)     │  ← 각 필드의 종류 식별자
│  └─ (기타 메타데이터)                      │
├─────────────────────────────────────────┤
│ 데이터 영역 (0x1B0 ~)                     │
│  ├─ Record 0: [float32 × n_fields]       │  ← 1 레코드 = n_fields개 float32
│  ├─ Record 1: [float32 × n_fields]       │
│  ├─ ...                                  │
│  └─ Record N: [float32 × n_fields]       │
└─────────────────────────────────────────┘

레코드 크기 = n_fields × 4 bytes
총 레코드 수 = (파일크기 - 0x1B0) / 레코드크기
```

### FieldID → 물리량 매핑

`.cyc` 파일의 각 필드는 **FieldID** (uint16)로 식별된다.
헤더의 FieldID 배열 순서가 곧 레코드 내 float32 배열의 순서.

| FieldID | 물리량 | .cyc 내부 단위 | 비고 |
|:-------:|--------|:-------------:|------|
| **1** | Voltage | **mV** | CSV의 col[8]에 대응 |
| **2** | Current | **mA** | CSV의 col[9]에 대응 |
| **6** | StepTime | **초** | CSV의 col[17]에 대응 |
| **12** | Temp1 | **°C** | CSV의 col[21]에 대응 |
| **24** | AvgVoltage | **mV** | CSV의 col[29]에 대응 |
| **26** | ChgCapacity | **mAh** | CSV의 col[10]에 대응 |
| **27** | DchgCapacity | **mAh** | CSV의 col[11]에 대응 |
| **35** | DchgWattHour | **Wh** | CSV의 col[15]에 대응 |
| **45** | VoltageMax | **μV** | CSV의 col[45]에 대응 |
| **49** | Temp4 | **°C 또는 m°C** | CSV의 col[24]에 대응 (자동 감지) |

### .cyc 행 = CSV 행의 관계

| 관점 | .cyc | SaveEndData.csv | SaveDataXXXX.csv |
|------|------|-----------------|------------------|
| **1행** | float32 × n_fields (샘플) | 스텝 종료 시점의 값 | 샘플링 시점의 값 |
| **행 수** | 전체 샘플 수 (가장 많음) | 스텝 수 (가장 적음) | 샘플 수 (≈ .cyc) |
| **관계** | SaveEndData ⊂ SaveData ≈ .cyc | .cyc에서 스텝 종료만 추출 | .cyc와 거의 1:1 |

```
.cyc 레코드 (시간 순서)
│ rec 0 │ rec 1 │ ... │ rec 100 │ rec 101 │ ... │ rec 200 │ ...
└───── 충전 스텝 ──────┘         └──── 방전 스텝 ────┘
        ↓ StepTime=0 감지                 ↓
   SaveEndData: rec 100 (충전 종료)   SaveEndData: rec 200 (방전 종료)
   SaveData: rec 0~100 전체           SaveData: rec 101~200 전체
```

---

## 5. 단위 체계 비교 — .cyc vs CSV

> **가장 중요한 차이점**: `.cyc`와 CSV의 단위가 다르다.
> BDT의 `_cyc_to_cycle_df()`가 .cyc 단위 → CSV 단위로 변환한다.

| 물리량 | .cyc 단위 | CSV 단위 | 변환식 | 코드 위치 |
|--------|:---------:|:--------:|--------|:---------:|
| **Voltage** | mV | **μV** | `× 1000` | L6787 |
| **Current** | mA | **μA** | `× 1000` | L6788 |
| **DchgCapacity** | mAh | **μAh** | `× 1000` | L6789 |
| **ChgCapacity** | mAh | **μAh** | `× 1000` | L6790 |
| **StepTime** | 초 | **/100초** | `× 100` | L6791 |
| **Temperature** | °C 또는 m°C | **m°C** | `× 1000` (자동감지) | L6792-6797 |
| **AvgVoltage** | mV | **mV** (×1000) | `× 1000` | L6799 |
| **VoltageMax** | μV | **μV** | 그대로 | L6798 |
| **DchgWattHour** | Wh | **Wh** | 그대로 | L6800 |
| **imp** | - | **μΩ** | .cyc에서 직접 계산 | L6772-6784 |

### 단위 변환 코드 (L6786-6800)

```python
# _cyc_to_cycle_df() 내부 — .cyc float32 → CSV 정수 단위 변환
volt_uv   = int(float(last[p_volt]) * 1000)       # mV → μV
curr_ua   = int(float(last[p_curr]) * 1000)        # mA → μA
dchg_uah  = int(float(last[p_dchg]) * 1000)        # mAh → μAh
chg_uah   = int(float(last[p_chg]) * 1000)         # mAh → μAh
time_cs   = int(round(float(last[p_time]) * 100))  # 초 → /100초 (centisecond)
temp_mc   = int(float(last[p_temp]) * 1000)         # °C → m°C (milli-Celsius)
avgv      = int(float(last[p_avgv]) * 1000)         # mV → mV (×1000 의미 확인 필요)
```

**왜 .cyc → CSV 단위로 변환하는가?**
BDT의 모든 하류 함수(`_process_pne_cycleraw`, `pne_simul_cycle_data` 등)는
SaveEndData.csv 단위를 전제로 코딩되어 있다. `.cyc` 보충 데이터도 동일 단위로 맞춰야
기존 코드와 호환된다.

---

## 6. .cyc의 스텝/사이클 경계 인식

> CSV는 StepType 컬럼(col[2])이 명시적으로 스텝 타입을 알려주지만,
> `.cyc`는 바이너리 시계열이므로 **스텝 경계를 자체 추론**해야 한다.

### 스텝 경계 감지 (L6716-6718)

```python
fid6 = data[:, p_time]                    # StepTime 컬럼 추출
step_starts = np.where(fid6 == 0.0)[0]    # StepTime이 0인 레코드 = 새 스텝 시작
boundaries = step_starts + [N]             # 경계 배열 구성
```

**원리**: PNE 장비는 새 스텝이 시작될 때 StepTime을 0으로 리셋한다.
따라서 StepTime=0인 레코드가 곧 스텝의 시작점.

### StepType 추론 (L6753-6760)

```python
mean_c = float(np.mean(main_seg[:, p_curr]))   # 스텝 내 평균 전류
if mean_c > 10.0:                               # 양수 전류
    stype = 1   # 충전                            → CSV StepType = 1
elif mean_c < -10.0:                            # 음수 전류
    stype = 2   # 방전                            → CSV StepType = 2
else:                                           # 전류 ≈ 0
    stype = 3   # 휴지                            → CSV StepType = 3
```

### EndState 추론 (L6762-6770)

```python
# 스텝 후반부 전류의 변동성으로 CC vs CV 구분
tail_n = max(n_main // 3, min(n_main, 3))
tail_c = main_seg[-tail_n:, p_curr]             # 끝부분 전류
t_std = float(np.std(tail_c))                   # 전류 표준편차
t_abs = float(np.mean(np.abs(tail_c)))          # 전류 절대평균

if stype in (1, 2):
    es = 66 if t_std / max(t_abs, 1.0) > 0.05 else 65
    # 변동 크면(CV 종료 → 전류 감소) = 66(전류조건), 변동 작으면(CC) = 65(전압조건)
else:
    es = 64   # 휴지                              → CSV EndState = 64
```

### 루프 마커 감지 (L6736-6743)

```python
# 루프 마커: 스텝 마지막 레코드가 시간 점프 or 비정상 용량 패턴
has_loop = False
if M >= 2:
    cond_a = (float(seg_t[-1]) - float(seg_t[-2])) > 300.0  # 시간 300초 이상 점프
    cond_b = (main_curr < 20.0 and main_dmed == 0.0          # 전류≈0, 방전용량≈0인데
              and last_d > 100.0)                             # 마지막만 용량 큼
    has_loop = cond_a or cond_b
```

루프 마커가 감지되면:
- 본체 스텝 + 루프 마커 = **2행** 출력 (CSV의 스텝행 + 루프행에 대응)
- 루프 마커의 Condition = 8, EndState = 64

---

## 7. .cyc → SaveEndData 보충 메커니즘

> BDT는 `.cyc`가 CSV보다 최신 데이터를 가지면 **자동 보충**한다.
> 이는 자정 CSV 출력 이후 ~ 현재까지의 진행 데이터를 반영하기 위함.

### 보충 흐름 (L939-976)

```
_cached_pne_restore_files()
│
├─ 1. SaveEndData.csv 로드                    → save_end_data
├─ 2. .cyc 파일 찾기 & 파싱                     → _cyc_to_cycle_df()
├─ 3. .cyc 결과를 CSV 컬럼 형식으로 변환          → _cyc_df_to_save_end_format()
├─ 4. CSV 최신 사이클 이후 데이터만 필터            → supplement = mapped[TC > csv_max_tc]
└─ 5. CSV + 보충 데이터 합치기                    → pd.concat([save_end, supplement])
```

### _cyc_df_to_save_end_format() — 컬럼 역매핑 (L6842-6871)

```python
# .cyc 파서의 13개 컬럼 → SaveEndData의 48개 컬럼 형식으로 배치
_SAVE_END_MAP = {
    27: 'TotlCycle',    # col[27] ← TotlCycle
    2:  'Condition',     # col[2]  ← Condition (StepType)
    10: 'chgCap',        # col[10] ← chgCap
    11: 'DchgCap',       # col[11] ← DchgCap
    8:  'Ocv',           # col[8]  ← Ocv (Voltage)
    20: 'imp',           # col[20] ← imp
    45: 'volmax',        # col[45] ← volmax
    15: 'DchgEngD',      # col[15] ← DchgEngD
    17: 'steptime',      # col[17] ← steptime
    9:  'Curr',          # col[9]  ← Curr
    24: 'Temp',          # col[24] ← Temp
    29: 'AvgV',          # col[29] ← AvgV
    6:  'EndState',      # col[6]  ← EndState
}
# 나머지 35개 컬럼은 0으로 채움
```

---

## 8. PNE21/PNE22 특수 단위 (μA 모드)

> PNE21/PNE22 장비 또는 코인셀 모드에서는 **단위가 한 단계 더 작다**.

```python
# is_micro_unit() L708-710
def is_micro_unit(raw_file_path):
    return ('PNE21' in raw_file_path) or ('PNE22' in raw_file_path) or _coincell_mode
```

| 물리량 | 일반 PNE CSV 단위 | PNE21/22 CSV 단위 | 차이 |
|--------|:-----------------:|:-----------------:|:----:|
| Current | μA | **nA** (= μA × 1000) | ×1000 |
| Capacity | μAh | **nAh** (= μAh × 1000) | ×1000 |

BDT 변환 시:
```python
if is_micro_unit(raw_file_path):
    df["Curr"] = df["Current[mA]"] / mincapacity / 1_000_000   # nA → C-rate
    df["Dchg"] = df["DchgCap"] / mincapacity / 1_000_000       # nAh → ratio
else:
    df["Curr"] = df["Current[mA]"] / mincapacity / 1_000       # μA → C-rate
    df["Dchg"] = df["DchgCap"] / mincapacity / 1_000           # μAh → ratio
```

---

## 9. 전체 단위 변환 경로 요약

```
┌─────────────┐    ×1000     ┌──────────────┐    ÷1000÷mincap    ┌────────────┐
│ .cyc 바이너리 │ ──────────→ │ SaveEndData  │ ─────────────────→ │ df.NewData  │
│  (mV, mA,   │  _cyc_to_   │  (μV, μA,    │  _process_pne_    │  (V, ratio, │
│   mAh, s)   │  cycle_df   │   μAh, /100s)│  cycleraw         │   mΩ, °C)   │
└─────────────┘             └──────────────┘                    └────────────┘

구체적 변환 경로 (전압 예시):
  .cyc: 4200.0 (mV, float32)
    → ×1000 → SaveEndData: 4200000 (μV, int)
      → ÷1,000,000 → df.NewData: 4.2 (V, float)

구체적 변환 경로 (방전용량 예시):
  .cyc: 1500.0 (mAh, float32)
    → ×1000 → SaveEndData: 1500000 (μAh, int)
      → ÷1000÷mincapacity → df.NewData: 0.987 (ratio, float)

구체적 변환 경로 (온도 예시):
  .cyc: 25.3 (°C, float32)
    → ×1000 → SaveEndData: 25300 (m°C, int)
      → ÷1000 → df.NewData: 25.3 (°C, float)

구체적 변환 경로 (시간 예시):
  .cyc: 3600.0 (초, float32)
    → ×100 → SaveEndData: 360000 (/100초, int)
      → ÷100 → df.NewData: 3600.0 (초, float)
```

---

## 10. imp (내부저항) 계산 차이

| 소스 | imp 값의 출처 | 계산 방식 |
|------|-------------|----------|
| **CSV (SaveEndData)** | col[20]에 기록된 값 | PNE 장비 펌웨어가 자체 계산 |
| **.cyc (BDT 파서)** | `_cyc_to_cycle_df()` L6772-6784 | BDT가 10초 시점 DC 저항으로 자체 계산 |

```python
# .cyc imp 계산 로직 (L6772-6784)
if stype in (1, 2) and n_main >= 2:
    v_ocv = float(main_seg[0, p_volt])           # 스텝 시작 전압 (mV)
    idx10 = int(np.searchsorted(times, 10.0))     # 10초 시점 인덱스
    if abs(t_act - 10.0) <= 2.0:                  # 10±2초 허용
        v10 = float(main_seg[idx10, p_volt])      # 10초 시점 전압
        i10 = float(main_seg[idx10, p_curr])      # 10초 시점 전류
        imp_val = int(abs(v_ocv - v10) / abs(i10) * 1e6)  # mV/mA × 1e6 = μΩ
```

**주의**: CSV의 imp (장비 계산)와 .cyc의 imp (BDT 계산)는 **값이 다를 수 있다**.
- 장비는 특정 프로토콜로 측정 (내부 알고리즘)
- BDT는 단순 10초 DC-IR로 근사
- 보충 데이터의 imp는 BDT 자체 계산값

---

## 11. 요약: 3가지 파일의 역할 비교표

| 비교 항목 | `.cyc` (원본) | `SaveEndData.csv` | `SaveDataXXXX.csv` |
|----------|:------------:|:-----------------:|:------------------:|
| **생성 주체** | PNE 장비 | PNE 장비 (자정 출력) | PNE 장비 (자정 출력) |
| **형식** | 바이너리 (float32) | CSV (정수) | CSV (정수) |
| **1행 의미** | 샘플링 시점 | 스텝 종료 시점 | 샘플링 시점 |
| **행 수** | 최대 (수십만~) | 최소 (수백~수천) | 중간 (≈ .cyc) |
| **컬럼 수** | n_fields (가변, FieldID로 식별) | 48개 (고정 인덱스) | 48개 (고정 인덱스) |
| **전압 단위** | mV | μV | μV |
| **전류 단위** | mA | μA | μA |
| **용량 단위** | mAh | μAh | μAh |
| **시간 단위** | 초 | /100초 | /100초 |
| **온도 단위** | °C (또는 m°C) | m°C | m°C |
| **갱신 시점** | 실시간 | 자정 | 자정 |
| **BDT 주용도** | .cyc 보충 | 사이클 분석 | 프로파일 분석 |
| **BDT 진입 함수** | `_cyc_to_cycle_df()` | `_cached_pne_restore_files()` | `pne_data()` |
| **BDT 단위 변환** | mV→μV 등 (×1000) | μV→V 등 (÷1e6) | μV→V 등 (÷1e6) |

---

## 12. 학습 활동

### A. 실제 파일 열어보기
1. 아무 PNE 채널 폴더에서 `Restore/SaveEndData.csv` 열기
2. 컬럼 인덱스 0, 2, 8, 9, 10, 11, 17, 20, 24, 27, 29, 45 확인
3. 같은 사이클(col[27])에 속하는 행들을 묶어서 스텝 구조 파악

### B. 단위 변환 직접 계산
1. SaveEndData의 col[8] 값 (예: 4200000) → V로 변환: 4200000 / 1,000,000 = 4.2V
2. SaveEndData의 col[11] 값 (예: 1500000) → 용량 비율: 1500000 / 1000 / 공칭용량
3. SaveEndData의 col[17] 값 (예: 360000) → 초: 360000 / 100 = 3600초 = 1시간

### C. .cyc 보충 로직 추적
1. `_cached_pne_restore_files()` (L900) 에서 `.cyc` 보충 조건 확인
2. CSV의 최대 TotlCycle과 .cyc의 최대 TotlCycle 비교
3. 보충 발생 시 콘솔 로그 확인: `[.cyc 보충] chXX: CSV TC≤100, .cyc TC 101~105 추가`

---

## 13. 참고 자료

### 관련 학습 시리즈
- [[260409_study_01_cycle_data_pipeline_overview|Study 01: 파이프라인 전체 흐름]]
- [[260409_study_03_pne_cycle_data|Study 03: PNE 사이클 데이터 처리]]
- [[260409_study_05_df_newdata_deep_dive|Study 05: df.NewData 심화]]

### 코드 위치
- `.cyc` 파서: `DataTool_optRCD_proto_.py` L6604-6871
- SaveEndData 로드: L900-981
- SaveData 로드: `pne_data()` L6515-6534
- .cyc → CSV 단위 변환: `_cyc_to_cycle_df()` L6786-6800
- CSV → df.NewData 변환: `_process_pne_cycleraw()` L6874-7144

### vault 연계
- [[DCIR_측정_업체별.md]] — DCIR 측정 프로토콜
- [[데이터_전처리_통합]] — 데이터 전처리 원칙 (Gen4 ATL 섹션)

---

## Appendix: 실측 데이터 비교 결과

> **대상**: `251029_260429_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 30CY @1-1202` / `M01Ch011[011]`

### A-1. 파일 개요

| 항목 | `.cyc` | `SaveEndData.csv` | `SaveData*.csv` (100개) |
|------|:------:|:-----------------:|:----------------------:|
| **파일 크기** | 50,922,112 bytes (48.6 MB) | ~1.5 MB | 합계 ~60 MB |
| **총 행 수** | 303,105 | 7,158 | 303,110 |
| **컬럼 수** | 42 (FieldID 기반) | 47 (고정 인덱스) | 47 (동일) |
| **행 차이** | - | - | .cyc 대비 **+5행** |

### A-2. FieldID 배열 (이 파일 기준)

```
[22, 41, 6, 42, 7, 1, 2, 26, 27, 34, 35, 23, 24, 12, 36, 37, 40, 28,
 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 64, 65,
 65, 66, 67, 68, 69, 70, 71]
```

| 위치 | FID | 물리량 | rec[0] | rec[1] | 확인된 CSV col |
|:----:|:---:|--------|:------:|:------:|:-------------:|
| 0 | 22 | Index | 1.0 | 2.0 | col[0] |
| 2 | 6 | StepTime (s) | 0.0 | 0.1 | col[17] (×100) |
| 5 | 1 | Voltage (mV) | 3778.0 | 3754.5 | col[8] (×1000) |
| 6 | 2 | Current (mA) | 0.0 | -465.4 | col[9] (×1000) |
| 7 | 26 | ChgCap (mAh) | 0.0 | 0.0 | col[10] (×1000) |
| 8 | 27 | DchgCap (mAh) | 0.0 | 0.006 | col[11] (×1000) |
| 10 | 35 | DchgEng (Wh) | 0.0 | 0.0 | col[15] |
| 12 | 24 | AvgVolt (mV) | 0.0 | 0.0 | col[29] (×1000) |
| 13 | 12 | Temp1 (°C) | 23.186 | 23.186 | col[21] (×1000) |
| 16 | 40 | ?(setpoint?) | 23.0 | 23.0 | - |
| 20 | 45 | Vmax (μV) | 3777991 | 3754528 | col[45] |
| 22 | 47 | Temp2? (°C) | 23.186 | 23.186 | col[22] (×1000) |
| 23 | 48 | Temp3? (°C) | 23.186 | 23.186 | col[23] (×1000) |
| 24 | 49 | Temp4 | 0.0 | 0.0 | col[24] |

### A-3. .cyc vs SaveData 시계열 1:1 비교 (처음 10행)

```
  Row | Field      | .cyc (raw)   | CSV (raw)  | .cyc -> CSV | Match
------+------------+--------------+------------+-------------+------
    0 | Index      |        1.000 |          1 |           1 |  OK
    0 | StepTime   |        0.000 |          0 |           0 |  OK
    0 | Voltage    |     3777.991 |    3777991 |     3777991 |  OK
    0 | Current    |        0.000 |          0 |           0 |  OK
    0 | ChgCap     |        0.000 |          0 |           0 |  OK
    0 | DchgCap    |        0.000 |          0 |           0 |  OK
   ---+
    1 | Index      |        2.000 |          2 |           2 |  OK
    1 | Voltage    |     3754.528 |    3754528 |     3754528 |  OK
    1 | Current    |     -465.411 |    -465411 |    -465411  |  OK
    1 | DchgCap    |        0.006 |          6 |           6 |  OK
   ---+
    2 | Voltage    |     3737.164 |    3737164 |     3737164 |  OK
    2 | Current    |     -465.986 |    -465986 |    -465986  |  OK
   ...
    9 | Voltage    |     3702.421 |    3702421 |     3702421 |  OK
    9 | Current    |     -466.042 |    -466042 |    -466042  |  OK
```

**결론**: Index, StepTime, Voltage, Current, ChgCap, DchgCap **모두 완벽 일치** (×1000 변환).

### A-4. 온도 컬럼 매핑 확인

```
  Row | cyc FID12  cyc FID47  cyc FID48  cyc FID49 | CSV[21]  CSV[22]  CSV[23]  CSV[24]
 -----+---------------------------------------------+--------------------------------
    0 |    23.186    23.186    23.186      0.000     |  23186   23186   23186       0
    2 |    23.165    23.065    23.186     23.000     |  23165   23065   23186   23000
   50 |    23.086    22.995    23.186     23.000     |  23086   22995   23186   23000
  100 |    23.074    23.045    23.145     23.000     |  23074   23045   23145   23000
```

| .cyc FieldID | CSV 컬럼 | 물리량 | 변환 |
|:------------:|:--------:|--------|:----:|
| **FID 12** | **col[21]** (Temp1) | 센서 온도 1 | ×1000 (°C → m°C) |
| **FID 47** | **col[22]** (Temp2) | 센서 온도 2 | ×1000 |
| **FID 48** | **col[23]** (Temp3) | 센서 온도 3 | ×1000 |
| **FID 49** | **col[24]** (Temp4) | 설정 온도(정수) | 그대로 or ×1000 (자동감지) |

### A-5. SaveEndData ↔ SaveData 완벽 일치 확인

```
검증 대상: SaveEndData 7,158행 전체
방법: SaveEndData.col[0](Index) → SaveData에서 같은 Index 행 → Voltage/Current 비교
결과: 7,158 / 7,158 = 100.00% 완벽 일치
```

**SaveEndData는 SaveData의 특정 행(스텝 종료 시점)을 그대로 복사한 것**임을 실증.

### A-6. .cyc ↔ SaveData 순서 매칭 한계

```
불일치 시작 행: row 437
  row 434: cyc_V=4547.980 mV → CSV_V=4547980 μV  OK
  row 435: cyc_V=4545.543 mV → CSV_V=4545543 μV  OK
  row 436: cyc_V=4544.686 mV → CSV_V=4544686 μV  OK
  row 437: cyc_V=   0.000 mV → CSV_V=4544198 μV  MISMATCH !!
  
유효 전압 레코드: 12,641 / 303,105 (4.2%)
```

**원인 분석**: .cyc 바이너리의 row 437부터 float32 해석이 깨짐.
Raw hex 비교 결과 **바이트 정렬(alignment) 불일치** — .cyc 파일 내부에
PNE 장비가 삽입하는 체크포인트/동기화 마커가 존재하여
단순 `(offset - 0x1B0) / rec_size` 계산으로는 후반부 레코드에 접근 불가.

> **BDT의 대응**: BDT는 `.cyc`를 전체 시계열로 읽지 않음.
> `_cyc_to_cycle_df()`는 StepTime=0 기반으로 **스텝 단위 요약**만 추출하며,
> 실제 시계열 분석은 **SaveData CSV**를 사용.
> .cyc는 SaveEndData 이후의 **최신 사이클 보충용**으로만 활용.

### A-7. 사이클 구조 실측

```
총 사이클: 801 (TotlCycle 1~801)
SaveEndData 스텝 분포:
  StepType 1 (충전): 3,170행
  StepType 2 (방전): 1,590행
  StepType 3 (휴지): 1,599행
  StepType 8 (루프): 799행
  
사이클별 스텝 예시:
  Cycle 1: 3 steps [방전, 휴지, 루프] — 초기 방전 (포메이션 전 OCV 확인)
  Cycle 2: 5 steps [충전, 휴지, 방전, 휴지, 루프] — 단순 CC-CV 사이클
  Cycle 3: 9 steps [충전×4, 휴지, 방전×2, 휴지, 루프] — 다단 CC-CV + CC 방전
```

### A-8. SaveData 파일 분할 구조

```
savingFileIndex_start.csv:
  File  1 → Index    1 (2025-10-29)   ← 시험 시작일
  File  2 → Index 1497 (2025-10-30)
  File  3 → Index 5192 (2025-10-31)
  ...
  File 100 → Index 302961 (2026-02-16) ← 마지막 파일

규칙: 자정마다 새 파일 생성, 이전 SaveData에 이어서 Index 연번
```

### A-9. .cyc vs CSV 전류값 차이 — 휴지(Rest) 스텝 미소전류

> **9개 채널 전수 분석 결과**, .cyc ↔ CSV 전류 불일치는 **100% 휴지 스텝에서만 발생**한다.
> 충전/방전/루프 스텝에서는 불일치 **0건**.

#### 실측 데이터 (M01Ch009, 2335mAh Q8 선상 ATL 2.9V 30Cy LT)

```
전류 불일치: 6,589 / 111,618 행 (5.90%)

StepType별 분포:
  StepType     전체      불일치     비율
  ────────────────────────────────────
  1 (충전)    78,727         0    0.0%
  2 (방전)    25,403         0    0.0%
  3 (휴지)     7,188     6,589   91.7%  ← 100% 여기서만 발생
  8 (루프)       300         0    0.0%

불일치 패턴 (6,589건 전부 동일):
  .cyc:  전류 = 0.000 mA  (float32 정확히 0)
  CSV:   전류 = -100 ~ -500 μA  (중앙값 -163 μA)
```

#### 원인: PNE 장비의 전류 기록 방식 차이

| 구분 | .cyc 바이너리 | CSV (SaveData) |
|------|:------------:|:--------------:|
| **휴지 스텝 전류** | **0.000 mA** (하드 제로) | **-100 ~ -500 μA** (실측값) |
| **기록 방식** | 전류 인가 회로 OFF → 명목상 0 기록 | ADC가 실측한 잔류 전류 기록 |
| **물리적 의미** | "전류를 인가하지 않음" | "셀에 실제 흐르는 미소 전류" |

#### CSV에 기록되는 미소 전류의 물리적 해석

```
CSV 휴지 전류 (실측):
  범위:  -2,706 ~ +39 μA
  중앙값: -163 μA
  평균:  -320 μA
  |I| < 500 μA:  87.1%
  |I| < 1000 μA: 91.0%
```

이 미소 전류는 다음의 합산값이다:

1. **셀 자기방전(self-discharge) 전류**: 셀 내부의 미소 부반응·누설에 의한 전류 (~수 μA)
2. **측정 장비 오프셋 전류**: PNE 충방전기 ADC의 zero-offset (~수백 μA)
3. **전자 노이즈**: 측정 회로의 열잡음 등 (~수십 μA)

> **주의**: 자기방전 전류(K-value) 계산 시에는 **CSV 값(실측)**을 사용해야 하며,
> .cyc의 0값을 사용하면 자기방전이 측정되지 않는다.

#### float32 정밀도와의 관계

이것은 **float32 정밀도 문제가 아니다**.
float32는 0.150 mA (= 150 μA)를 nA 단위까지 정확히 표현 가능하다.

```python
np.float32(0.150)  # = 0.15000000596...
# 분해능 = 0.000015 μA (= 0.015 nA) → 충분히 표현 가능

# → PNE 장비가 .cyc에서 휴지 전류를 의도적으로 0으로 기록하는 것
```

#### BDT에서의 영향

| BDT 기능 | 영향 | 이유 |
|----------|:----:|------|
| 사이클 분석 (df.NewData) | **없음** | SaveEndData의 col[9](Curr) 사용, 휴지 행은 pivot에서 제외 |
| DCIR 계산 | **없음** | 충방전 스텝만 대상 |
| .cyc 보충 로직 | **미소 영향** | 보충 시 휴지 전류가 0이 됨 (실용상 무시 가능) |
| 프로파일 분석 | **미소 영향** | SaveData CSV 사용 → 정상 기록됨 |
| K-value 계산 | **주의 필요** | .cyc가 아닌 CSV 데이터 사용 필수 |

---

**작성일**: 2026-04-10
**작성자**: Claude Code 학습 시스템
**버전**: 3.0 (휴지 전류 차이 분석 추가)
