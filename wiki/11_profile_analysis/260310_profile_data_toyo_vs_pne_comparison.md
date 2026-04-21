# Toyo vs PNE 프로파일 데이터 로딩 및 처리 로직 비교 분석

> 분석 대상: `DataTool_dev/DataTool_optRCD_proto_.py`  
> 프로파일 유형: Step, Rate, Chg, Dchg, Continue (5종)

---

## 1. 전체 구조 요약

### 프로파일 함수 매핑

| 유형 | Toyo 함수 | PNE 함수 | 목적 |
|------|-----------|----------|------|
| **Step** | `toyo_step_Profile_data()` | `pne_step_Profile_data()` | CC-CV 충전 전체 프로파일 |
| **Rate** | `toyo_rate_Profile_data()` | `pne_rate_Profile_data()` | 율별 충전 프로파일 |
| **Chg** | `toyo_chg_Profile_data()` | `pne_chg_Profile_data()` | 충전 프로파일 + dQ/dV |
| **Dchg** | `toyo_dchg_Profile_data()` | `pne_dchg_Profile_data()` | 방전 프로파일 + dQ/dV |
| **Continue** | `toyo_Profile_continue_data()` | `pne_Profile_continue_data()` | 연속 충방전 프로파일 |
| **배치** | `toyo_*_batch()` | `pne_*_batch()` | 여러 사이클 일괄 처리 |

---

## 2. 데이터 소스 및 로딩 방식 비교

### Toyo — 파일 기반 직접 로딩

```
{raw_file_path}\000001  ← 사이클 1번 Profile
{raw_file_path}\000002  ← 사이클 2번 Profile
        ...
```

```python
# toyo_Profile_import() → toyo_read_csv()
dataraw = pd.read_csv(filepath, sep=",", skiprows=3, engine="c", encoding="cp949")
# 선택 컬럼: PassTime[Sec], Voltage[V], Current[mA], Condition, Temp1[Deg]
```

- **1 사이클 = 1 파일** (파일명: `%06d` 형식, 예: `000023`)
- `skiprows=3` → 헤더 3줄 건너뜀
- 컬럼명 호환 처리: `PassTime[Sec]` ↔ `Passed Time[Sec]`, `Temp1[Deg]` ↔ `Temp1[deg]`

### PNE — SaveData 통합 파일 기반

```
{raw_file_path}\Restore\SaveData_xxx.csv  ← 모든 사이클 raw 데이터
{raw_file_path}\Restore\SaveEndData.csv   ← 사이클 인덱스 파일
{raw_file_path}\Restore\savingFileIndex_start.csv  ← 파일 인덱스
```

```python
# pne_data() → pne_search_cycle() → SaveData 파일 로딩
# 원하는 사이클이 어느 SaveData 파일에 있는지 인덱스로 검색 후 로딩
```

- **여러 사이클이 하나의 SaveData 파일에 통합**
- `pne_search_cycle()`로 해당 사이클의 파일 범위 검색
- 숫자 컬럼명 사용 (0, 2, 7, 8, 9, 10, 11, 15, 17, 18, 19, 21, 27 등)
- 사이클 필터: `df[27] == inicycle`

---

## 3. 단위 체계 비교 ★

| 물리량 | Toyo 원본 단위 | PNE 원본 단위 | PNE 변환 |
|--------|---------------|---------------|----------|
| **전압** | V | μV | ÷ 1,000,000 |
| **전류** | mA | μA (또는 mA) | ÷ 1,000 (또는 ÷ 1,000,000) |
| **용량** | mAh | μAh (또는 mAh) | ÷ 1,000 (또는 ÷ 1,000,000) |
| **시간** | Sec | 1/100 Sec | ÷ 100 |
| **온도** | °C × 1 | °C × 1000 | ÷ 1,000 |
| **에너지** | mWh | Wh | 그대로 사용 |

**PNE μA 단위 판별:**
```python
is_micro_unit(raw_file_path)  # PNE21/22 또는 코인셀이면 True
# True  → ÷ mincapacity × 1,000,000 (μA → C-rate)
# False → ÷ mincapacity × 1,000    (mA → C-rate)
```

---

## 4. 프로파일 유형별 상세 비교

### 4.1 Step 충전 프로파일

**목적**: CC-CV 충전 과정의 시간-전압-전류-용량 프로파일

#### Toyo Step

```
파일 로딩 → Condition==1 필터 → 다중 파일 연결 → 용량 직접 계산 → 단위 변환
```

1. **다중 파일 연결**: Condition에 방전(2)이 없으면 → 뒤 사이클 파일을 연속으로 읽어 합침
   ```python
   while maxcon == 1:    # 방전 나올 때까지 다음 파일 연결
       stepcyc += 1
       tempdata.dataraw["PassTime[Sec]"] += lasttime  # 시간 이어붙이기
   ```

2. **용량 직접 계산** (벡터화):

$$Cap_n = Cap_0 + \sum_{i=1}^{n} \frac{\Delta t_i \times I_{i+1}}{3600}$$

   ```python
   df.stepchg["delta_time"] = df.stepchg["PassTime[Sec]"].shift(-1) - df.stepchg["PassTime[Sec]"]
   df.stepchg["contribution"] = (delta_time * next_current) / 3600
   df.stepchg["Cap[mAh]"] = initial_cap + contribution.cumsum().shift(1)
   ```

3. **Cut-off**: `Current[mA] >= cutoff × mincapacity`
4. **단위 변환**: 시간→분, 전류→C-rate, 용량→ratio

#### PNE Step

```
SaveData 로딩 → Cycle+Condition 필터 → 스텝 연결 → 단위 변환 → Cut-off
```

1. **사이클 + Condition 필터**: `df[27] == inicycle & df[2].isin([9, 1])`
   - Condition `9` = OCV step, `1` = 충전
2. **컬럼 선택**: `[17, 8, 9, 21, 10, 7]` → PassTime, Voltage, Current, Temp, ChgCap, Step
3. **스텝 연결** (시간/용량 이어붙이기):
   ```python
   for i in range(1, stepdiv + 1):
       Profiles[-1]["PassTime[Sec]"] += Profiles[-2]["PassTime[Sec]"].max()
       Profiles[-1]["Chgcap"] += Profiles[-2]["Chgcap"].max()
   ```
4. **용량**: 장비에서 이미 계산된 `ChgCap` (컬럼 10) 사용 → **직접 계산 불필요**
5. **Cut-off**: `Current[mA] >= cutoff` (이미 C-rate로 변환 후)

#### 핵심 차이

| 항목 | Toyo Step | PNE Step |
|------|-----------|----------|
| 용량 산출 | **직접 계산** (시간×전류 적분) | 장비 기록값 사용 (컬럼 10) |
| 다중 파일 | 뒷 사이클 파일 자동 탐색 연결 | 스텝 번호 기반 연결 |
| 시간 연결 | PassTime 누적 합산 | PassTime 누적 합산 (동일) |
| Condition 코드 | 1 (충전) | 9 (OCV) + 1 (충전) |

---

### 4.2 Rate 충전 프로파일

**목적**: 특정 C-rate별 충전 프로파일

구조는 Step과 거의 동일하되:

| 항목 | Toyo Rate | PNE Rate |
|------|-----------|----------|
| 파일 연결 | **단일 파일만** (다중 파일 연결 없음) | 단일 사이클 (동일) |
| 용량 | 직접 계산 (시간×전류 적분) | 장비 기록값 사용 |
| 스텝 분리 | 없음 (하나의 충전 구간) | 없음 (필터링만) |
| 중복 계산 | 벡터화 + 2차 검증 로직 존재 | 단순 단위 변환만 |

> **참고**: Toyo Rate에는 벡터화 용량 계산 후 한 번 더 `diff().cumsum()` 방식으로 재계산하는 이중 검증 코드가 포함됨

---

### 4.3 Chg/Dchg 프로파일 (dQ/dV 분석 포함) ★

**목적**: 충전/방전 프로파일 + 미분 용량 분석 (dQ/dV, dV/dQ)

#### Toyo Chg/Dchg

```
파일 로딩 → Condition 필터 → 전압 Cut-off → 용량 직접 계산 → dQ/dV 계산 → 단위 변환
```

1. **Condition 필터**: Chg = `Condition == 1`, Dchg = `Condition == 2`
2. **Cut-off**: `Voltage[V] >= cutoff` (전압 기준)
3. **용량 계산** (rolling mean 기반):
   ```python
   df.Profile["deltime"] = df.Profile["PassTime[Sec]"].diff()
   df.Profile["delcurr"] = df.Profile["Current[mA]"].rolling(window=2).mean()
   df.Profile["delvol"] = df.Profile["Voltage[V]"].rolling(window=2).mean()
   df.Profile["delcap"] = deltime / 3600 * delcurr / mincapacity
   df.Profile["Cap[mAh]"] = delcap.cumsum()
   ```
4. **에너지 계산**:
   ```python
   df.Profile["delwh"] = delcap * mincapacity * delvol
   df.Profile["Chgwh"] = delwh.cumsum()  # 또는 Dchgwh
   ```

5. **dQ/dV 계산** (smoothing 적용):
   ```python
   smoothdegree = int(len(df.Profile) / 30)  # 기본값: 데이터 길이의 1/30

   delvol = Voltage[V].diff(periods=smoothdegree)
   delcap = Cap[mAh].diff(periods=smoothdegree)
   dQdV = delcap / delvol
   dVdQ = delvol / delcap
   ```

6. **Dchg 특수 처리**: 다음 사이클이 방전만이면 연결
   ```python
   if not tempdata2.dataraw["Condition"].isin([1]).any():  # 충전 없으면
       df.Profile2["PassTime[Sec]"] += lasttime             # 시간 이어붙이기
       df.Profile = pd.concat([df.Profile, df.Profile2])
   ```

#### PNE Chg/Dchg

```
SaveData 로딩 → Cycle+Condition 필터 → 스텝 연결 → 단위 변환 → Cut-off → dQ/dV 계산
```

1. **Condition 필터**:
   - Chg: `df[2].isin([9, 1])` (OCV + 충전)
   - Dchg: `df[2].isin([9, 2])` (OCV + 방전)
2. **컬럼 선택**:
   - Chg: `[17, 8, 9, 10, 14, 21, 7]` → 시간, 전압, 전류, **ChgCap**, **ChgWh**, 온도, 스텝
   - Dchg: `[17, 8, 9, 11, 15, 21, 7]` → 시간, 전압, 전류, **DchgCap**, **DchgWh**, 온도, 스텝
3. **용량/에너지**: 장비 기록값 직접 사용 (직접 계산 불필요)
4. **스텝 연결**: Step과 동일한 시간/용량 이어붙이기

5. **dQ/dV 계산** (Toyo와 동일한 공식):
   ```python
   delvol = Voltage[V].diff(periods=smoothdegree)
   delcap = Chgcap.diff(periods=smoothdegree)   # ← 장비 기록 용량 사용
   dQdV = delcap / delvol
   dVdQ = delvol / delcap
   ```

6. **Dchg 전류 처리**: `Current[mA] × (-1)` (방전 전류 부호 반전)

#### 핵심 차이

| 항목 | Toyo Chg/Dchg | PNE Chg/Dchg |
|------|---------------|--------------|
| **Cut-off 기준** | 전압 (`Voltage >= cutoff`) | 전류 (`Current >= cutoff`) (Step과 동일) |
| **용량 산출** | `deltime/3600 × delcurr.rolling(2)/mincap` | 장비값 (`ChgCap`, `DchgCap`) |
| **에너지 산출** | `delcap × mincap × delvol.rolling(2)` | 장비값 (`ChgWh`, `DchgWh`) |
| **dQ/dV** | `cumsum()` 후 `diff(smoothdegree)` | 장비 용량에 `diff(smoothdegree)` |
| **연속 방전** | 다음 사이클이 방전만이면 자동 연결 | 스텝 번호 기반 연결 |

---

### 4.4 Continue 프로파일

**목적**: 여러 사이클에 걸친 연속 충방전 데이터 + OCV/CCV 추출

#### Toyo Continue

```
여러 사이클 파일 연결 → PassTime 보정 → SOC 누적 계산 → OCV/CCV 전환점 추출
→ capacity.log에서 AccCap 산출 → CycfileSOC 생성
```

1. **다중 파일 로딩**: `inicycle` ~ `endcycle` 범위의 파일을 순서대로 `pd.concat`
2. **PassTime 리셋 보정** (파일 경계에서 시간 리셋 처리):
   ```python
   time_diffs = df.stepchg["PassTime[Sec]"].diff().clip(lower=0).fillna(0)
   df.stepchg["PassTime[Sec]"] = time_diffs.cumsum()
   ```
3. **SOC 계산** (전류 부호 반전 후 적분):
   ```python
   signed_current[Condition == 2] *= -1  # 방전 시 음수
   increments = (time_diffs / 3600) * signed_current
   df.stepchg["Cap[mAh]"] = increments.cumsum()
   ```
4. **OCV/CCV 추출** (Condition 전환점):
   ```python
   # OCV: rest(0) → load(1,2) 전환 = rest 마지막 행 전압
   ocv_mask = (cond == 0) & (next_cond.isin([1, 2]))
   # CCV: load(1,2) → rest(0) 전환 = load 마지막 행 전압
   ccv_mask = (cond.isin([1, 2])) & (next_cond == 0)
   ```
5. **CycfileSOC**: `capacity.log`의 `Cap[mAh]` 누적합으로 AccCap 산출

#### PNE Continue

```
SaveData 로딩 → CDstate에 따라 Condition 필터 → 단위 변환 → OCV/CCV (SaveEndData)
```

1. **CDstate별 필터링**:

   | CDstate | 필터 조건 |
   |---------|-----------|
   | `"CHG"` | `Condition.isin([9, 1])` |
   | `"DCHG"` / `"DCH"` | `Condition.isin([9, 2])` |
   | `"Cycle"` / `"7cyc"` / `"GITT"` | 전체 (필터 없음) |
   | `""` (빈 문자열) | 전체 + OCV/CCV 포함 |

2. **단위 변환**: `pne_continue_profile_scale_change()` 호출
   ```python
   TotTime = (TotTime[Day] × 8640000 + TotTime[Sec]) / 100   # → 초
   Voltage = Voltage / 1,000,000                               # μV → V  
   SOC = ChgCap + DchgCap                                     # 누적 SOC
   ```

3. **OCV/CCV** (SaveEndData 기반):
   ```python
   CycfileOCV = Cycrawtemp[Condition == 3]    # 휴지 행의 전압 = OCV
   CycfileCCV = Cycrawtemp[Condition.isin([1, 2])]  # 충방전 행의 전압 = CCV
   ```

4. **AccCap 계산**:
   ```python
   AccCap = (ChgCap.cumsum() - DchgCap.cumsum()) / 1000 / mincapacity
   ```

#### 핵심 차이

| 항목 | Toyo Continue | PNE Continue |
|------|---------------|--------------|
| **시간 처리** | PassTime `diff().clip(≥0).cumsum()` (리셋 보정) | `TotTime[Day] + TotTime[Sec]` 변환 |
| **SOC 계산** | 전류 부호 반전 후 시간적분 | 장비값 `ChgCap + DchgCap` |
| **OCV 추출** | Profile 데이터 Condition 전환점 | SaveEndData `Condition == 3` |
| **CCV 추출** | Profile 데이터 Condition 전환점 | SaveEndData `Condition ∈ [1,2]` |
| **AccCap** | `capacity.log` 기반 | `SaveEndData` 기반 |
| **CDstate 분기** | 없음 (항상 전체) | 있음 (CHG/DCHG/Cycle/빈값) |

---

## 5. 배치 처리 방식 비교

### Toyo 배치

```python
def toyo_step_Profile_batch(raw_file_path, cycle_list, mincapacity, cutoff, inirate):
    mincapacity = toyo_min_cap(...)   # 1회만 산정
    for inicycle in cycle_list:
        # 사이클별 파일 직접 로딩 (디스크 I/O 반복)
        tempdata = toyo_Profile_import(raw_file_path, inicycle)
        ...
```

- **min_cap 1회 산정** 후 사이클 반복
- 각 사이클마다 **개별 파일 로딩** (디스크 I/O N회)

### PNE 배치

```python
def pne_step_Profile_batch(raw_file_path, cycle_list, mincapacity, cutoff, inirate):
    mincapacity = pne_min_cap(...)    # 1회만 산정
    all_raw = pd.concat(SaveData...) # 전체 범위 1회 로딩
    for inicycle in cycle_list:
        # 메모리에서 사이클 필터링 (디스크 I/O 없음)
        cycle_raw = all_raw[all_raw[27] == inicycle]
        ...
```

- **min_cap 1회 산정** + **SaveData 1회 일괄 로딩**
- 이후 사이클별 **메모리 내 필터링** (디스크 I/O 0회)

| 배치 비교 | Toyo | PNE |
|-----------|------|-----|
| 디스크 I/O | 사이클 수 × 파일 읽기 | **1회** 일괄 로딩 |
| 메모리 사용 | 낮음 (1 사이클씩) | 높음 (전체 범위 상주) |
| 인덱스 검색 | 불필요 (파일명 = 사이클번호) | SaveEndData + fileIndex 검색 필요 |

---

## 6. 출력 DataFrame 비교

### Step / Rate 출력

| 컬럼명 | 의미 | Toyo 산출 | PNE 산출 |
|--------|------|-----------|----------|
| `TimeMin` | 시간 (분) | `PassTime/60` | `StepTime/100/60` |
| `SOC` | 용량비 (0~1) | 직접 계산 후 `÷mincap` | 장비값 `÷mincap` |
| `Vol` | 전압 (V) | 원본 그대로 | `÷1,000,000` |
| `Crate` | C-rate | `Current/mincap` | `Current/mincap/1000(or 1e6)` |
| `Temp` | 온도 (°C) | 원본 그대로 | `÷1,000` |

### Chg / Dchg 출력 (추가 컬럼)

| 컬럼명 | 의미 | Toyo 산출 | PNE 산출 |
|--------|------|-----------|----------|
| `Energy` | 에너지 (mWh/Wh) | `delcap × mincap × delvol` 적분 | 장비값 (컬럼 14/15) |
| `dQdV` | 미분 용량 | `delcap/delvol` (smoothed) | 동일 공식 |
| `dVdQ` | 미분 전압 | `delvol/delcap` (smoothed) | 동일 공식 |

### Continue 출력 (추가 컬럼)

| 컬럼명 | 의미 | Toyo 산출 | PNE 산출 |
|--------|------|-----------|----------|
| `TimeSec` | 시간 (초) | `PassTime` 보정값 | `TotTime` 변환값 |
| `Curr` | 전류 (A) | `signed_current/1000` | `Current/1e6(or 1e3)` |
| `OCV` | 개방 전압 | Condition 전환점 추출 | SaveEndData `Cond==3` |
| `CCV` | 부하 전압 | Condition 전환점 추출 | SaveEndData `Cond∈[1,2]` |

---

## 7. 데이터 흐름 다이어그램

### Toyo 프로파일 흐름

```
{raw_file_path}\000001 ... 000XXX  (사이클별 파일)
         │
         ▼
┌──────────────────────────────┐
│ toyo_Profile_import()        │  → 5개 컬럼 선택
│ [PassTime, Voltage, Current, │     + 컬럼명 호환 처리
│  Condition, Temp]            │
└──────────────────────────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    ▼         ▼          ▼          ▼
  Step       Rate       Chg       Dchg
    │         │          │          │
    ▼         ▼          ▼          ▼
 Cond==1   Cond==1    Cond==1    Cond==2
 다중파일   단일파일   단일파일   +뒷사이클
 연결                              연결
    │         │          │          │
    ▼         ▼          ▼          ▼
 용량 직접   용량 직접   용량 직접   용량 직접
 계산        계산       계산        계산
 (Δt×I)     (Δt×I)    (rolling    (rolling
                       mean)       mean)
    │         │          │          │
    │         │          ▼          ▼
    │         │       dQ/dV 계산  dQ/dV 계산
    │         │       (smoothed)  (smoothed)
    ▼         ▼          ▼          ▼
┌──────────────────────────────────────┐
│ 단위 변환                              │
│ 시간→분, 전류→C-rate, 용량→ratio      │
└──────────────────────────────────────┘
         │
         ▼
    [mincapacity, df]
```

### PNE 프로파일 흐름

```
{raw_file_path}\Restore\SaveData_XXX.csv  (통합 파일)
         │
         ▼
┌──────────────────────────────┐
│ pne_data()                   │  → pne_search_cycle()로 파일 범위 검색
│ → pne_search_cycle()         │  → SaveData 파일 로딩
│ → pd.read_csv(SaveData)     │  → df.Profileraw에 저장
└──────────────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ 사이클 + Condition 필터       │  → df[27]==inicycle
│ Step: [9,1]  Rate: [9,1]     │     & df[2].isin([...])
│ Chg:  [9,1]  Dchg: [9,2]    │
└──────────────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ 컬럼 선택 + 이름 부여         │  → 숫자 → 의미 있는 이름
│ [17,8,9,21,10,7] 등          │
└──────────────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ 단위 변환 (μV→V, μA→C-rate)  │  → is_micro_unit() 분기
│ + 스텝 연결 (시간/용량 누적)   │
└──────────────────────────────┘
         │
    ┌────┴────────────────┐
    ▼                     ▼
  Step/Rate             Chg/Dchg
  (용량=장비값)          (용량=장비값)
    │                     │
    ▼                     ▼
  Cut-off             dQ/dV 계산
  (전류 기준)          (smoothed)
    │                     │
    ▼                     ▼
     [mincapacity, df]
```

---

## 8. 요약: 핵심 차이점

| 비교 항목 | **Toyo** | **PNE** |
|-----------|----------|---------|
| 파일 구조 | 사이클별 개별 파일 | 통합 SaveData 파일 |
| 용량 산출 | **항상 직접 계산** (시간×전류 적분) | **장비 기록값** 사용 |
| 에너지 산출 | 직접 계산 (delcap × mincap × delvol) | 장비 기록값 사용 |
| 단위 변환 | 거의 불필요 (mA, V 원단위) | 필수 (μV, μA → V, C-rate) |
| 스텝 연결 | 파일 단위 (다음 파일 탐색) | 스텝 번호 기반 (메모리 내) |
| OCV/CCV | Condition 전환점 감지 | SaveEndData `Condition==3` |
| 배치 I/O | 사이클 수 × 파일 읽기 | 1회 일괄 로딩 후 메모리 분배 |
| dQ/dV 로직 | Toyo/PNE **동일** (`diff(smoothdegree)`) |
| 최종 출력 | Toyo/PNE **동일** 컬럼명 (`TimeMin, SOC, Vol, Crate, Temp, ...`) |
