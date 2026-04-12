# Toyo 사이클 데이터 로딩 및 변환 로직 분석

> 분석 대상: `DataTool_dev/DataTool_optRCD_proto_.py` — `toyo_cycle_data()` 함수 (Line 649~789)

---

## 1. 전체 흐름 요약

```
capacity.log (CSV)
   │
   ├─ [1] toyo_min_cap()        → 용량(mincapacity) 산정
   ├─ [2] toyo_cycle_import()   → capacity.log 로딩 (10개 컬럼)
   ├─ [3] 방전 시작 보정         → 첫 행이 방전이면 TotlCycle 조정
   ├─ [4] 연속 동일 Condition 병합 → groupby + merge_rows
   ├─ [5] 충전/방전/DCIR 분리    → Condition 기반 필터링
   ├─ [6] DCIR 계산             → Profile 파일(000001 등) 직접 읽어 계산
   ├─ [7] 효율/인덱스 정렬       → Chg↔Dchg 위치 기반 매칭
   └─ [8] DataFrame 조립        → df.NewData 생성 및 반환
```

---

## 2. 단계별 상세 분석

### 2.1 용량 산정 — `toyo_min_cap()`

```python
def toyo_min_cap(raw_file_path, mincapacity, inirate):
```

| 조건 | 산정 방법 |
|------|-----------|
| `mincapacity == 0` + 경로에 `"mAh"` 포함 | `name_capacity()`로 파일명에서 추출 (예: `3000mAh` → 3000) |
| `mincapacity == 0` + `"mAh"` 없음 | 첫 사이클 파일(`000001`) 로딩 → `Current[mA].max() / inirate` |
| `mincapacity != 0` | 입력값 그대로 사용 |

- `inirate`는 초기 C-rate (기본 0.2C 가정)

---

### 2.2 CSV 로딩 — `toyo_cycle_import()`

**소스 파일**: `{raw_file_path}\capacity.log`

```python
df.dataraw = toyo_read_csv(raw_file_path)  # skiprows=0
```

**선택되는 10개 컬럼:**

| 컬럼명 | 의미 | 비고 |
|--------|------|------|
| `TotlCycle` | 총 사이클 번호 | 인덱스로 사용 |
| `Condition` | 1=충전, 2=방전 | PNE의 3(휴지)에 해당하는 별도 코드 없음 |
| `Cap[mAh]` | 용량 (mAh) | 충전/방전 모두 동일 컬럼 |
| `Ocv` | Open Circuit Voltage | 충전 시 첫 값 = Rest End Voltage |
| `Finish` | 종료 조건 | `"Vol"`, `"Tim"`, `"Time"` 등 |
| `Mode` | 운전 모드 | 분석에는 미사용 |
| `PeakVolt[V]` | 최대 전압 | 분석에는 미사용 |
| `Pow[mWh]` | 에너지 (mWh) | 방전 에너지 계산용 |
| `PeakTemp[Deg]` | 최대 온도 | Temp으로 사용 |
| `AveVolt[V]` | 평균 전압 | AvgV로 사용 |

**기기별 컬럼명 호환 처리** (BLK 3600/3000 vs BLK5200):
- `Cap[mAh]` ↔ `Capacity[mAh]`
- `Ocv` ↔ `OCV[V]`
- `Finish` ↔ `End Factor`
- 등 컬럼명을 통일

---

### 2.3 방전 시작 보정

```python
if Cycleraw.loc[0, "Condition"] == 2 and len(Cycleraw.index) > 2:
    if Cycleraw.loc[1, "TotlCycle"] == 1:
        Cycleraw.loc[Cycleraw["Condition"] == 2, "TotlCycle"] -= 1
        Cycleraw = Cycleraw.drop(0, axis=0).reset_index()
```

- **목적**: 테스트가 방전으로 시작하는 경우, 방전 사이클 번호를 1 감소시키고 첫 행(불완전 방전)을 제거
- **조건**: 첫 행 Condition==2(방전) + 두 번째 행 TotlCycle==1

---

### 2.4 연속 동일 Condition 병합 ★

Toyo 데이터의 핵심 전처리 단계. **같은 Condition이 연속으로 나오는 행들을 하나로 합산**한다.

```python
cond_series = Cycleraw["Condition"]
merge_group = ((cond_series != cond_series.shift()) | (~cond_series.isin([1, 2]))).cumsum()
```

**그룹핑 로직**:
- Condition이 이전 행과 **다르거나**, 충방전(1,2)이 **아닌** 경우 → 새 그룹 시작
- 결과: 연속된 충전 행들은 같은 그룹, 연속된 방전 행들은 같은 그룹

**`merge_rows()` 병합 규칙:**

| Condition | 병합 방식 |
|-----------|-----------|
| **충전 (1)** | `Cap[mAh]` 합산 / `Ocv`는 **첫 번째** 행 값 사용 / 나머지는 마지막 행 기준 |
| **방전 (2)** | `Cap[mAh]`, `Pow[mWh]` 합산 / `Ocv`는 **첫 번째** 행 값 / `AveVolt[V]` 재계산 (`Pow/Cap`) |
| **기타** | 단일 행 그대로 반환 |

**예시**: CC-CV 충전이 CC 충전 행 + CV 충전 행으로 분리되어 있으면 → 하나의 충전 행으로 합산

---

### 2.5 충전/방전/DCIR 데이터 분리

#### 충전 데이터 (`chgdata`)

```python
chgdata = Cycleraw[
    (Cycleraw["Condition"] == 1) 
    & (Cycleraw["Finish"] != "Vol") & (Cycleraw["Finish"] != "Volt")  # 전압 종료 제외
    & (Cycleraw["Cap[mAh]"] > (mincapacity/60))                       # 너무 작은 충전 제외
]
```

- **추출 항목**: `Chg` (충전 용량), `Ocv` (Rest End Voltage = RndV)
- `Finish`가 `"Vol"` 또는 `"Volt"`인 행 제외 → CV 종료 전압 단계를 이미 병합했으므로 순수 전압 종료만 필터
- 최소 용량 임계값: `mincapacity / 60` (약 1분 충전에 해당하는 미만 데이터 제외)

#### 방전 데이터 (`Dchgdata`)

```python
Dchgdata = Cycleraw[
    (Cycleraw["Condition"] == 2) 
    & (Cycleraw["Cap[mAh]"] > (mincapacity/60))
]
```

- **추출 항목**: `Dchg`, `Temp`, `DchgEng`, `AvgV`, `OriCycle`

#### DCIR 후보 데이터

```python
dcir = Cycleraw[
    ((Cycleraw["Finish"] == "Tim") | (Cycleraw["Finish"] == "Time"))  # 시간 종료
    & (Cycleraw["Condition"] == 2)                                     # 방전
    & (Cycleraw["Cap[mAh]"] < (mincapacity/60))                       # 작은 용량 (펄스)
]
```

- **선정 기준**: 시간으로 종료 + 방전 + 용량 작음 → **DCIR 펄스 Step으로 추정**

---

### 2.6 DCIR 계산 — Profile 파일 직접 읽기

```python
for cycle in cycnum:
    dcirpro = pd.read_csv(raw_file_path + "\\%06d" % cycle, ...)
    dcircal = dcirpro[(dcirpro["Condition"] == 2)]
    dcir.loc[cycle, "dcir"] = (
        (dcircal["Voltage[V]"].max() - dcircal["Voltage[V]"].min()) 
        / round(dcircal["Current[mA]"].max()) * 1000000
    )
```

**DCIR 계산 공식:**

$$DCIR = \frac{V_{max} - V_{min}}{I_{max}} \times 10^6 \quad [m\Omega]$$

- 해당 사이클의 **Profile 파일** (예: `000023`)을 직접 로딩
- 방전 구간의 최대/최소 전압 차이를 최대 전류로 나눔
- `× 1,000,000`: V/mA → mΩ 단위 변환

**DCIR 사이클 매핑 (cyccal):**

| `chkir` 값 | 매핑 방식 |
|-------------|-----------|
| `True` (체크됨) | 순차적 1, 2, 3, 4, ... (매 DCIR 포인트마다 1씩 증가) |
| `False` | 교대 패턴: 홀수 인덱스에서 `+1`, 짝수 인덱스에서 `+dcirstep-1` 건너뜀 |

`dcirstep` 계산: `ceil(총방전수 / (DCIR수/2) / 10) × 10` — DCIR 측정 간격 추정

---

### 2.7 충방전 효율 계산 및 인덱스 정렬 ★

Toyo의 병합 후 인덱스 문제를 처리하는 핵심 로직:

```
예시 (병합 후):
Chg 인덱스:  [8, 13, 18, 23, ...]   ← 충전 TotlCycle
Dchg 인덱스: [9, 14, 19, 24, ...]   ← 방전 TotlCycle
→ 1칸씩 어긋남 → 위치(순서) 기반으로 재매칭
```

**처리 순서:**

1. **초기 부분 방전 제거**: `Dchg.index[0] < Chg.index[0]`이면 → 매칭되는 충전 없이 시작된 방전이므로 첫 번째 Dchg 행 삭제

2. **위치 기반 재정렬**: Chg/Ocv 값을 Dchg 인덱스에 매핑
   ```python
   _nmin = min(len(Chg), len(Dchg))
   Chg = pd.Series(Chg.values[:_nmin], index=Dchg.index[:_nmin])
   Ocv = pd.Series(Ocv.values[:_nmin], index=Dchg.index[:_nmin])
   ```

3. **효율 계산:**

$$Eff = \frac{Dchg}{Chg}$$

$$Eff2 = \frac{Chg_{n+1}}{Dchg_n}$$

4. **용량 정규화:**
   ```python
   Dchg = Dchg / mincapacity   # → Capacity Ratio
   Chg  = Chg  / mincapacity
   ```

---

### 2.8 최종 DataFrame 조립

```python
df.NewData = pd.DataFrame({
    "Dchg": Dchg,         # 방전 용량비 (Capacity Ratio)
    "RndV": Ocv,          # Rest End Voltage (충전 첫 행의 OCV)
    "Eff": Eff,           # 방전효율 (Dchg/Chg)
    "Chg": Chg,           # 충전 용량비
    "DchgEng": DchgEng,   # 방전 에너지 (mWh)
    "Eff2": Eff2,         # 쿨롱효율 (Chg_next/Dchg)
    "Temp": Temp,         # 최대 온도 (PeakTemp)
    "AvgV": AvgV,         # 평균 방전 전압
    "OriCyc": OriCycle    # 원본 사이클 번호
})
```

- `dropna(how='all', subset=['Dchg'])` → Dchg가 모두 NaN인 행 제거
- `reset_index()` → 0부터 시작하는 새 인덱스
- DCIR 데이터 병합: `dcir["dcir"]` 컬럼을 outer join으로 추가
- `TotlCycle` 컬럼 제거

---

## 3. PNE vs Toyo 비교

| 항목 | Toyo | PNE |
|------|------|-----|
| **소스 파일** | `capacity.log` (1개 파일) | `SaveEndData.csv` (Restore 폴더) |
| **로딩 단위** | 행 = 1개 Step | 행 = 1개 Step |
| **충방전 구분** | `Condition` (1=충전, 2=방전) | `Condition` (1=충전, 2=방전, 3=휴지, 8=루프) |
| **단위** | mAh, V, mWh (원 단위 그대로) | μV, μA, μAh (÷1,000,000 변환 필요) |
| **집계 방식** | `groupby` 병합 + 필터링 | `pivot_table` (TotlCycle × Condition) |
| **RndV 출처** | 충전 행의 `Ocv` (충전 시작 전 OCV = 방전 후 rest 끝 전압) | `pivot_data["Ocv"][3]` (Rest Condition의 min OCV → 방전 후 rest 전압 선택) |
| **AvgV** | `capacity.log`의 `AveVolt[V]` 컬럼 직접 사용 | `DchgEng / Dchg / mincapacity × 1000` 계산 |
| **DCIR 계산** | Profile 파일 직접 읽기 → (Vmax-Vmin)/Imax | `imp` 컬럼 사용 또는 3-point 계산 (RSS/1s pulse) |
| **DCIR 모드** | 단일 (`chkir`) | 3가지 (`chkir`, `mkdcir`, 기본 10s pulse) |
| **μA 단위 대응** | 불필요 (mA 단위) | `is_micro_unit()` 체크 후 ÷1000 |
| **효율 계산** | 위치 기반 Chg↔Dchg 재매칭 (인덱스 어긋남 보정) | pivot 결과로 인덱스 자동 정렬 |

---

## 4. 주요 필터링 조건 정리

```
충전 선택 조건:
  ✓ Condition == 1
  ✓ Finish ≠ "Vol" and ≠ "Volt"      (전압 종료 스텝 제외)
  ✓ Cap[mAh] > mincapacity / 60      (미소 충전 제외)

방전 선택 조건:
  ✓ Condition == 2
  ✓ Cap[mAh] > mincapacity / 60      (미소 방전 = DCIR 펄스 제외)

DCIR 후보 선택 조건:
  ✓ Condition == 2
  ✓ Finish == "Tim" or "Time"         (시간 종료 스텝)
  ✓ Cap[mAh] < mincapacity / 60      (작은 용량 = 펄스)
```

---

## 5. 데이터 흐름 다이어그램

```
capacity.log
  │
  ▼
┌────────────────────────────┐
│ toyo_cycle_import()        │  → 10개 컬럼 선택 + 컬럼명 통일
└────────────────────────────┘
  │
  ▼
┌────────────────────────────┐
│ 방전시작 보정               │  → 첫행 Condition==2이면 TotlCycle -1 후 제거
└────────────────────────────┘
  │
  ▼
┌────────────────────────────┐
│ 연속 Condition 병합         │  → CC+CV 분리행 합산 (Cap합산, Ocv는 첫값)
│ (merge_rows)               │
└────────────────────────────┘
  │
  ├──────────────────┬──────────────────┐
  ▼                  ▼                  ▼
┌──────────┐   ┌──────────┐   ┌──────────────────┐
│ chgdata  │   │ Dchgdata │   │ dcir 후보        │
│ Cond==1  │   │ Cond==2  │   │ Cond==2 + Tim    │
│ Cap>임계 │   │ Cap>임계 │   │ Cap<임계          │
└──────────┘   └──────────┘   └──────────────────┘
  │ Chg, Ocv     │ Dchg, Temp    │
  │               │ DchgEng, AvgV │  ┌──────────────────┐
  │               │               ├─▶│ Profile 파일 로딩 │
  │               │               │  │ (000001 등)       │
  │               │               │  │ → DCIR 계산       │
  │               │               │  └──────────────────┘
  ▼               ▼               ▼
┌───────────────────────────────────────────┐
│ 인덱스 재정렬 (위치 기반 Chg↔Dchg 매칭)   │
│ → Eff, Eff2 계산                          │
│ → Dchg/Chg 정규화 (÷mincapacity)         │
└───────────────────────────────────────────┘
  │
  ▼
┌───────────────────────────────────────────┐
│ df.NewData (최종 DataFrame)               │
│ [Dchg, RndV, Eff, Chg, DchgEng,          │
│  Eff2, Temp, AvgV, OriCyc, dcir]         │
└───────────────────────────────────────────┘
```

---

## 6. 반환값

```python
return [mincapacity, df]
```

| 인덱스 | 값 | 설명 |
|--------|-----|------|
| `[0]` | `mincapacity` | 산정된 최소 용량 (mAh) |
| `[1]` | `df` | `df.NewData` 속성에 사이클 데이터 DataFrame 포함 |

### df.NewData 컬럼 상세

| 컬럼 | 단위/형태 | 산출 방식 |
|------|-----------|-----------|
| `Dchg` | Ratio (무단위) | `Cap[mAh] / mincapacity` |
| `RndV` | V | 충전 첫 행의 `Ocv` 값 |
| `Eff` | Ratio | `Dchg_raw / Chg_raw` |
| `Chg` | Ratio (무단위) | `Cap[mAh] / mincapacity` |
| `DchgEng` | mWh | `Pow[mWh]` 직접 사용 |
| `Eff2` | Ratio | `Chg_next / Dchg_raw` |
| `Temp` | °C | `PeakTemp[Deg]` 직접 사용 |
| `AvgV` | V | `AveVolt[V]` 직접 사용 |
| `OriCyc` | 정수 | 원본 사이클 번호 |
| `dcir` | mΩ | `(Vmax-Vmin)/Imax × 10^6` 또는 0 |
