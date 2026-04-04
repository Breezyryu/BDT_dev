# 사이클 데이터 탭 코드 완전 해부 — 물리적 의미와 코드 로직

**작성일**: 2026-04-04  
**대상 파일**: `DataTool_dev/DataTool_optRCD_proto_.py`  
**대상 함수**: `unified_cyc_confirm_button`, `_load_all_cycle_data_parallel`, `toyo_cycle_data`, `_process_pne_cycleraw`, `graph_output_cycle`

---

## 이 문서의 목적

사이클 데이터 탭의 "실행" 버튼을 누르는 순간부터 그래프가 그려지기까지,  
코드가 내부에서 무엇을 하는지 **물리적 의미**와 함께 단계별로 설명한다.  
배터리 엔지니어가 코드를 처음 접할 때 "이 숫자가 무엇인가?"를 바로 이해할 수 있도록 작성했다.

---

## 1. 전체 파이프라인 개요

```
[사용자가 "실행" 버튼 클릭]
        ↓
unified_cyc_confirm_button()     ← 입력값 파싱, 저장 경로 설정
        ↓
_load_all_cycle_data_parallel()  ← 채널별 병렬 데이터 로딩 (진행바 0~50%)
        ↓
  ┌─────────────────────────────┐
  │  [Toyo 채널]                │  [PNE 채널]
  │  toyo_cycle_data()          │  pne_cycle_data()
  │  CSV 파일 읽기              │  바이너리 .cyc 읽기
  │  Cycleraw 구성              │  Cycleraw 구성
  │  df.NewData 생성            │  _process_pne_cycleraw()
  └─────────────────────────────┘
        ↓
graph_output_cycle()             ← 6개 서브플롯 그리기 (진행바 50~100%)
        ↓
[화면에 그래프 표시, 엑셀/그림 저장]
```

**핵심 개념**: 데이터 흐름의 중심은 `df.NewData`라는 표(DataFrame)이다.  
Toyo든 PNE든 모두 이 동일한 형식의 표로 변환되기 때문에, 그래프 함수는 제조사를 구분하지 않는다.

---

## 2. 코드에서 자주 나오는 개념 설명

### 2.1 DataFrame (데이터프레임)이란?

코드에서 `df`, `Cycleraw`, `df.NewData` 등이 자주 등장한다.  
이것들은 모두 **엑셀 시트처럼 행(row)과 열(column)로 이루어진 표**이다.

```python
# 예시: Cycleraw의 구조 (PNE 기준)
#   TotlCycle  Condition  DchgCap   chgCap   Ocv       Temp    Curr
#   1          1          0         1689000  4.2V       23      1689
#   1          2          1689000   0        3.5V after 23      1689
#   1          3          0         0        4.18V rest 23      0
#   2          1          0         1685000  4.2V       23      1689
#   ...
```

- **행(row)**: 하나의 충전 스텝, 방전 스텝, 또는 휴지(Rest) 스텝 종료 기록
- **열(column)**: 해당 스텝에서 측정된 물리량 (전압, 용량, 온도 등)

### 2.2 인덱스(Index)란?

표의 행 번호이다. 엑셀의 행 번호(1, 2, 3...)와 같다.  
BDT에서는 인덱스를 사이클 번호로 쓰는 경우가 많다.

```python
dcir.index = [1, 2, 3, 4, ...]  # 각 행이 몇 번 사이클 데이터인지
```

### 2.3 Series와 DataFrame의 차이

- **Series** = 하나의 열(column). 예: 방전용량만 뽑은 목록
- **DataFrame** = 여러 열의 묶음. 예: 방전용량 + 충전용량 + 효율이 모인 표

---

## 3. Cycleraw — 가장 기초적인 원시 데이터

### 3.1 물리적 의미

`Cycleraw`는 **스텝 종료 시점의 요약 기록**이다.  
배터리 충방전기(사이클러)는 실험을 "스텝" 단위로 진행한다:

```
[1사이클 = 스텝 3개]
  스텝 1: 충전 (CC-CV) → 종료 → 기록 1행
  스텝 2: 휴지 (Rest)  → 종료 → 기록 1행
  스텝 3: 방전 (CC)    → 종료 → 기록 1행
```

따라서 100사이클이면 Cycleraw는 약 300행이 된다.

### 3.2 PNE Cycleraw의 컬럼 구조 (13개)

| 열 이름 | 물리적 의미 | 단위 | 비고 |
|---------|-----------|------|------|
| `TotlCycle` | 사이클 번호 | — | 충방전기 내부 카운터 |
| `Condition` | 스텝 종류 | — | **1=충전, 2=방전, 3=휴지** |
| `DchgCap` | 방전 용량 | μAh | 방전 스텝에서만 의미 있음, ×1000배 변환 필요 |
| `chgCap` | 충전 용량 | μAh | 충전 스텝에서만 의미 있음 |
| `Ocv` | 전압 기록 | μV | 스텝 종료 시점의 전압 (×1,000,000 → V) |
| `Temp` | 온도 | m°C | ÷1000 → °C |
| `imp` | 저항 (DCIR) | μΩ | ÷1000 → mΩ |
| `Curr` | 전류 | μA | 양수=충전, 음수=방전 |
| `DchgEngD` | 방전 에너지 | μWh | ÷1000 → mWh |
| `steptime` | 스텝 지속 시간 | ms | DCIR 펄스 판별에 사용 |
| `EndState` | 스텝 종료 이유 | — | 64=시간, 78=SOC 도달 |

### 3.3 Condition 컬럼의 핵심 역할

`Condition`은 각 행이 어떤 종류의 스텝인지를 나타내는 **숫자 코드**이다.

```
1 = 충전 (Charge)   → 배터리에 전류를 넣는 스텝
2 = 방전 (Discharge) → 배터리에서 전류를 빼는 스텝
3 = 휴지 (Rest)     → 전류 없이 쉬는 스텝 (OCV 측정용)
```

이 구분은 이후 모든 계산의 기초가 된다:  
- 방전 용량 = Condition==2인 행의 `DchgCap` 합계  
- 충전 후 OCV = Condition==3인 행의 `Ocv`  

---

## 4. pivot_table — Cycleraw에서 df.NewData 만들기

### 4.1 왜 pivot_table이 필요한가?

Cycleraw는 "스텝 단위" 표다. 그런데 우리가 그래프로 보고 싶은 것은 "사이클 단위" 요약이다.

```
[변환 전: Cycleraw — 스텝 단위]
  사이클1-충전: 용량=1689 mAh
  사이클1-방전: 용량=1685 mAh
  사이클1-휴지: OCV=4.18V
  사이클2-충전: 용량=1687 mAh
  ...

[변환 후: df.NewData — 사이클 단위]
  사이클1: 충전용량=1689, 방전용량=1685, 효율=99.8%, OCV=4.18V
  사이클2: ...
```

이 변환을 수행하는 도구가 `pivot_table`이다.  
엑셀의 "피벗 테이블" 기능과 동일한 개념이다.

### 4.2 pivot_table 코드 설명 (PNE)

```python
# DataTool_optRCD_proto_.py 라인 3479
pivot_data = Cycleraw.pivot_table(
    index="TotlCycle",    # 행 기준: 사이클 번호
    columns="Condition",  # 열 기준: 1(충전)/2(방전)/3(휴지)로 나눔
    values=["DchgCap", "DchgEngD", "chgCap", "Ocv", "Temp"],  # 집계할 값들
    aggfunc={
        "DchgCap": "sum",   # 방전 용량: 합계 (분할 방전 시 더해야 함)
        "DchgEngD": "sum",  # 방전 에너지: 합계
        "chgCap": "sum",    # 충전 용량: 합계
        "Ocv": "min",       # OCV: 최솟값 (휴지 직후가 가장 낮음, 실제로 min=마지막 안정값)
        "Temp": "max"       # 온도: 최댓값 (방전 중 가장 높은 온도를 대표값으로)
    }
)
```

결과는 아래와 같은 2차원 표가 된다:

```
           DchgCap         chgCap          Ocv             Temp
Condition  1    2    3     1    2    3     1    2    3     1    2    3
TotlCycle
1          0    1685 0     1689 0    0     0    0    4180  23   24   23
2          0    1683 0     1687 0    0     0    0    4179  23   24   23
```

이후 `pivot_data["DchgCap"][2]`로 방전 용량만 추출한다 (Condition==2 열).

---

## 5. df.NewData — 분석의 최종 결과표

### 5.1 구조와 크기

df.NewData는 **사이클 1개 = 행 1개**인 요약 표이다.  
100사이클 실험이면 df.NewData는 100행이다.

### 5.2 각 컬럼의 물리적 의미

#### 기본 용량 지표

| 컬럼 | 계산 방법 | 물리적 의미 | 정상 범위 |
|------|---------|-----------|--------|
| `Cycle` | 1부터 순차 부여 | 재정의된 사이클 번호 (충방전 쌍 기준) | 1, 2, 3, ... |
| `Dchg` | 방전용량 / 기준용량 | **방전 용량 비율** (SOH와 유사) | 0.7 ~ 1.0 (100사이클 이내) |
| `Chg` | 충전용량 / 기준용량 | **충전 용량 비율** | Dchg보다 약간 크거나 같음 |

```
Dchg = 1.000  → 기준 용량의 100%를 방전함 (신품 수준)
Dchg = 0.800  → 기준 용량의 80%만 방전 가능 (열화 진행)
Dchg = 0.700  → EOL(End of Life) 기준 근접
```

> **물리적 배경**: 사이클이 반복될수록 SEI(고체전해질계면) 성장, 활물질 손실 등으로  
> 배터리가 저장할 수 있는 리튬 양이 감소한다. Dchg는 이 손실을 수치화한 것이다.

#### 효율 지표

| 컬럼 | 계산 방법 | 물리적 의미 |
|------|---------|-----------|
| `Eff` | Dchg / Chg (같은 사이클) | **쿨롱 효율** — 충전한 만큼 방전되는 비율 |
| `Eff2` | Chg(n+1) / Dchg(n) (다음 사이클 충전 / 현재 사이클 방전) | **크로스-사이클 효율** — BDT 독자 지표 |

```
Eff = 방전용량 / 충전용량
    = 1.000이면 충전한 전하량을 모두 방전 (이상적)
    = 0.998이면 충전한 전하량의 99.8%만 방전 → 0.2%가 부반응으로 소비
    
Eff > 1.0이면 측정 오류 또는 불완전한 CV 스텝 가능성
```

> **물리적 배경**: Eff < 1.0의 이유는 SEI 성장이나 리튬 석출(Plating) 등의  
> 부반응이 충전 전류를 소비하기 때문이다. Eff가 갑자기 떨어지는 사이클은  
> 부반응이 급격히 증가한 시점을 의미한다.

#### 전압 지표

| 컬럼 | 계산 방법 | 물리적 의미 |
|------|---------|-----------|
| `RndV` | 충전 종료 후 휴지 마지막 전압 | **OCV 근사값** (충전 후 Rest 전압) |
| `AvgV` | 방전 에너지 / 방전 용량 | **방전 평균 전압** (mWh / mAh = V) |

```
RndV (Rest End Voltage, 단위: V):
  - 이론적으로 충분한 휴지 후에는 OCV(개방전압)와 같아짐
  - 사이클이 진행될수록 RndV 감소 → 내부 저항 증가 또는 용량 손실 신호
  - 정상 범위: NMC 기준 4.10~4.20V (충전 상한 전압에 따라 다름)

AvgV (Average Voltage, 단위: V):
  - 방전 에너지를 방전 용량으로 나눈 값
  - 내부 저항이 높아지면 → 방전 중 전압 강하 증가 → AvgV 감소
  - 열화의 초기 징후를 RndV보다 빨리 감지할 수 있음
```

#### 에너지 지표

| 컬럼 | 물리적 의미 | 단위 |
|------|-----------|------|
| `DchgEng` | 방전 에너지 | mWh |

```
DchgEng = 방전 중 V(t) × I(t)를 시간에 대해 적분한 값
         = 배터리가 실제로 공급한 에너지

에너지 = 용량 × 평균전압
DchgEng ≈ Dchg × mincapacity × AvgV
```

> **왜 에너지가 중요한가?** 배터리 팩의 실제 성능은 용량(Ah)보다 에너지(Wh)로 표현된다.  
> 내부 저항이 증가하면 용량은 크게 안 줄어도 에너지가 먼저 줄 수 있다.

#### 온도 지표

| 컬럼 | 물리적 의미 | 단위 |
|------|-----------|------|
| `Temp` | 방전 중 최고 온도 | °C |

```
Temp = 방전 스텝(Condition==2)에서 측정된 최대 온도

온도 상승 원인:
  신품: ΔT = I² × R × t / (mass × Cp) — 전류에 의한 저항 열 (줄 열)
  노화: R 증가 → 같은 전류에서 더 많은 열 발생 → ΔT 증가
```

#### 원래 사이클 번호

| 컬럼 | 물리적 의미 |
|------|-----------|
| `OriCyc` | 충방전기 내부의 원래 사이클 번호 |

BDT는 충방전 쌍을 기준으로 사이클을 재정의(1, 2, 3...)한다.  
`Cycle`은 재정의된 번호, `OriCyc`는 장비의 원래 번호이다.  
연속저장(연결처리) 시 두 번호가 다를 수 있다.

#### DCIR 지표 (DCIR 옵션 체크 시 추가)

| 컬럼 | 물리적 의미 | 단위 |
|------|-----------|------|
| `dcir` | DC 내부 저항 (모드에 따라 다름) | mΩ |
| `dcir2` | 1초 펄스 DCIR (MK 모드) | mΩ |
| `soc70_dcir` | SOC 70% 지점의 DCIR | mΩ |
| `soc70_rss_dcir` | SOC 70% 지점의 RSS-DCIR | mΩ |

#### 충전 전압 추적 (v260206 이후 추가)

| 컬럼 | 물리적 의미 |
|------|-----------|
| `ChgVolt` | 해당 사이클의 충전 상한 전압 (V) |
| `DchgVolt` | 해당 사이클의 방전 하한 전압 (V) |
| `ChgSteps` | 해당 사이클의 충전 스텝 수 (RPT vs 수명 구분) |

---

## 6. DCIR 계산 — 세 가지 모드

DC 내부 저항(DCIR)은 "배터리의 건강 지표"이다.  
저항이 높아질수록 전압 강하가 커지고, 출력 성능이 저하된다.

### 6.1 일반 DCIR 모드 (`chkir=True`)

PNE 충방전기가 자동으로 계산한 내부 저항값(`imp` 컬럼)을 직접 사용한다.

```python
# 라인 3428
if chkir:
    dcirtemp = Cycleraw[(Cycleraw["Condition"] == 2)    # 방전 스텝
                        & (Cycleraw["volmax"] > 4100000)]  # 충전 전압 > 4.1V 이상인 사이클
    dcir = dcirtemp.imp / 1000  # μΩ → mΩ
```

- 충전 전압이 4.1V 이상인 방전 직전에 장비가 측정한 DCIR 사용
- 가장 간단하고 신뢰성 높음
- 단점: 장비에서 DCIR 측정 스텝이 없으면 값이 없음

### 6.2 MK DCIR 모드 (`mkdcir=True`)

펄스(pulse) 실험 데이터를 BDT가 직접 계산하는 모드이다.

```
[MK DCIR 프로토콜]
  → SOC 5%, 20%, 50%, 70%(SOC70), 90% 지점에서 각각:
    - CCV 방전 (Condition==2, steptime==100ms) ← 1s 펄스
    - Rest (Condition==3, steptime==90~546초) ← OCV 안정화
    
[계산 방식]
  RSS-DCIR = |OCV_rest - V_CCV| / I_pulse     ← 준정적 저항
  1s-DCIR  = |V_CCV_after - V_CCV_before| / ΔI  ← 빠른 저항
```

```python
# 라인 3467-3468
_rss = np.abs((_v3 - _v1) / _safe_c1 * 1000)   # RSS: (OCV - 방전V) / 전류 × 1000
_pulse = np.abs((_v2 - _v1) / _safe_diff * 1000)  # Pulse: 전압변화 / 전류변화
```

- `_v1` = CCV(방전) 종료 전압
- `_v3` = 이후 Rest 종료 전압 (≈OCV)
- SOC70 지점 값만 추출하여 `soc70_dcir`, `soc70_rss_dcir`에 저장

### 6.3 표준 펄스 DCIR 모드 (기본, `chkir=False`, `mkdcir=False`)

짧은 방전 펄스(steptime ≤ 6초)에서 장비가 기록한 `imp` 값을 사용한다.

```python
# 라인 3476
dcirtemp = Cycleraw[(Cycleraw["Condition"] == 2) 
                    & (Cycleraw["steptime"] <= 6000)]  # 6초 이하 짧은 스텝
dcirtemp["dcir"] = dcirtemp.imp / 1000
```

---

## 7. Toyo vs PNE — 같은 결과, 다른 경로

### 7.1 check_cycler() — 제조사 자동 판별

```python
def check_cycler(raw_file_path):
    # Pattern 폴더가 있으면 PNE, 없으면 Toyo
    return os.path.isdir(raw_file_path + "\\Pattern")
```

- **Toyo 폴더**: `채널번호/` 하위에 숫자 파일만 있음 (예: `000001`, `000002`, ...)  
- **PNE 폴더**: `채널번호/Pattern/` 서브폴더가 있음

### 7.2 toyo_cycle_data() — CSV 파일 읽기

**데이터 흐름**:
```
채널 폴더 (예: 30/)
  ├── 000001  ← 1사이클 CSV 파일
  ├── 000002  ← 2사이클 CSV 파일
  └── ...
        ↓
toyo_cycle_import()  ← 모든 파일 읽어서 이어붙임
        ↓
Cycleraw (dataraw 속성)
        ↓
병합 (연속된 동일 Condition 행들을 합침)
        ↓
Chg, Dchg, Ocv, Temp, DchgEng 추출
        ↓
df.NewData 구성 → return [mincapacity, df]
```

**Toyo 고유 특성**:
- 파일명이 `000001`처럼 6자리 숫자로 된 파일들이 각 사이클 데이터
- 폴더명은 `30`, `31` 등 선행 0이 없음 (datapath에서는 `030`으로 표기하지만 실제 파일시스템은 `30`)
- CC, CV 등 다단계 충전이 여러 행으로 기록됨 → `merge_rows()`로 합산

### 7.3 pne_cycle_data() → _process_pne_cycleraw() — 바이너리 변환

**데이터 흐름**:
```
채널 폴더 (예: M01Ch008[008]/)
  ├── Pattern/          ← PNE 식별자
  ├── Restore/          ← 연속저장 데이터
  └── *.cyc 파일        ← 바이너리 사이클 데이터
        ↓
pne_read_cyc()  ← 바이너리 파싱
        ↓
Cycleraw (13 컬럼, 단위: μAh, μV 등)
        ↓
_process_pne_cycleraw()
  ├── pivot_table()  ← 스텝 단위 → 사이클 단위
  ├── DCIR 계산 (세 가지 모드)
  └── df.NewData 구성
        ↓
return [mincapacity, df]
```

**두 경로의 공통점**: 최종 반환 형식이 `[mincapacity, df]`로 동일하다.  
그래서 `_load_cycle_data_task()`는 제조사를 모르는 상태에서도 동작할 수 있다.

---

## 8. name_capacity() — 폴더명에서 용량 자동 추출

```python
# 예시 폴더명에서 용량 추출
"250207_250307_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명"
                          ↑
                       1689.0 mAh를 추출

"250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half"
                          ↑
                       4.187 mAh 추출 (소수점 `-` 대신 하이픈 사용)
```

- `mAh` 앞의 숫자를 정규식으로 탐색
- 하이픈(-)으로 쓰인 소수점도 처리 (예: `4-187` → `4.187`)
- 폴더명에 mAh가 없으면 0 반환
- 입력이 문자열이 아니면(예: 리스트) 0 반환

---

## 9. 병렬 로딩 — _load_all_cycle_data_parallel()

### 9.1 왜 병렬 처리가 필요한가?

채널이 20개이고 각 채널 로딩에 2초가 걸린다면:
- **순차 처리**: 2 × 20 = 40초
- **병렬 처리**: ≈ 2초 (20개를 동시에)

```python
# 라인 12820 (approximate)
with ThreadPoolExecutor(max_workers=min(8, len(task_list))) as executor:
    futures = {executor.submit(_load_cycle_data_task, *args): key
               for key, args in task_list.items()}
```

`ThreadPoolExecutor`는 **여러 채널을 동시에 처리**하는 도구이다.  
최대 8개 채널을 동시에 읽는다.

### 9.2 진행바 업데이트

```
로딩 단계:  진행바 0% → 50%  (채널 수에 비례해 증가)
그래프 단계: 진행바 50% → 100% (그래프 개수에 비례해 증가)
```

---

## 10. graph_output_cycle() — 6개 서브플롯의 물리적 의미

6개의 그래프는 배터리 상태를 다양한 관점에서 보여준다.

```python
# 라인 606
def graph_output_cycle(df, xscale, ylimitlow, ylimithigh, irscale, temp_lgnd, 
                       colorno, graphcolor, dcir, ax1, ax2, ax3, ax4, ax5, ax6):
```

### ax1 — 방전 용량 비율 (Discharge Capacity Ratio)

```python
graph_cycle(..., df.NewData.Dchg, ax1, ylimitlow, ylimithigh, ...)
```

- X축: 사이클 번호
- Y축: Dchg (무단위 비율, 1.0 = 100%)
- **의미**: 배터리 열화의 가장 직접적인 지표. 사이클이 늘수록 감소.
- 기본 Y축 범위: 사용자 입력값 (ylimitlow ~ ylimithigh)

### ax2 — 쿨롱 효율 (Discharge/Charge Efficiency)

```python
graph_cycle(..., df.NewData.Eff, ax2, 0.992, 1.004, 0.002, ...)
```

- Y축: Eff = 방전용량/충전용량
- 기본 범위: 0.992 ~ 1.004 (0.002 간격)
- **의미**: 99.2~100.4% 범위. 1.0에서 벗어날수록 이상 징후.
- 갑작스러운 하락: SEI 성장 가속화 또는 리튬 석출 시작 가능성

### ax3 — 온도 (Temperature)

```python
graph_cycle(..., df.NewData.Temp, ax3, 0, 50, 5, ...)
```

- Y축: °C (기본 범위 0~50°C)
- **의미**: 방전 중 최고 온도. 내부 저항 증가 시 온도도 상승.
- 다온도 실험(15°C, 23°C, 45°C)에서 각 셀의 실제 온도 확인에 사용

### ax4 — DC 내부 저항 (DC-IR)

```python
# MK 모드 (두 개의 DCIR):
graph_cycle(..., df.NewData.soc70_dcir, ax4, ...)     ← 1s 펄스
graph_cycle_empty(..., df.NewData.soc70_rss_dcir, ax4, ...)  ← RSS

# 일반 모드 (하나의 DCIR):
graph_cycle(..., df.NewData.dcir, ax4, ...)
```

- Y축: mΩ (기본 범위 0 ~ 120×irscale)
- **의미**: 내부 저항 증가 추이. SOC70% 지점에서 비교.
- DCIR 상승 → 출력 성능 저하, 발열 증가
- 점선 연결선이 있어 추이를 보기 쉽게 표시

### ax5 — Eff2 (Cross-cycle Efficiency)

```python
graph_cycle(..., df.NewData.Eff2, ax5, 0.996, 1.008, 0.002, ...)
```

- Y축: Eff2 = 다음사이클 충전용량 / 현재사이클 방전용량
- **의미**: BDT 독자 지표. 연속 사이클 간의 에너지 연계 효율.
- 이 값이 1.0보다 크면 이전 방전에서 못 꺼낸 용량을 다음 충전에서 흡수한 것

### ax6 — 평균 방전 전압 + Rest 종료 전압 (Average/Rest Voltage)

```python
graph_cycle(..., df.NewData.RndV, ax6, ...)    ← 점 (filled)
graph_cycle_empty(..., df.NewData.AvgV, ax6, ...)  ← 원 (empty)
```

- Y축: V (기본 범위 3.00 ~ 4.00V, 0.1 간격)
- **두 개의 시리즈를 같은 그래프에**:
  - 채워진 점(●): RndV — 충전 후 Rest 전압 (OCV 근사)
  - 빈 원(○): AvgV — 방전 평균 전압
- **의미**: 두 전압 모두 하락하면 열화 진행 중. AvgV가 먼저 떨어지면 내부 저항 증가 신호.

---

## 11. 주요 파라미터 — "기준 용량(mincapacity)"

모든 계산에서 가장 중요한 기준값이다.

```python
# name_capacity()로 자동 추출
mincapacity = 1689  # mAh (폴더명에서 추출)

# 용량 비율 계산 시 사용
Dchg = 방전용량_mAh / mincapacity  # 예: 1685/1689 = 0.9976
```

- 폴더명에 `1689mAh`가 있으면 자동으로 1689를 기준으로 사용
- 없으면 첫 번째 사이클의 충전 C-rate로 역산
- 이 값이 틀리면 Dchg가 1.0에서 크게 벗어나게 됨 (예: 2배 차이)

---

## 12. 코드 흐름 추적 — 한 채널의 데이터가 그래프가 되기까지

```
1. 사용자가 채널 경로를 입력 (예: C:\data\exp_data\...\30)

2. check_cycler("...\\30") → False (Pattern 폴더 없음 = Toyo)

3. name_capacity("...\\30") → 1689.0 (폴더명 "1689mAh"에서 추출)

4. toyo_cycle_data("...\\30", 0, 2.0, False)
   ├── toyo_min_cap() → mincapacity = 1689
   ├── toyo_cycle_import() → Cycleraw (약 300행 × 15열)
   │     [각 행 = 1개 스텝 종료 기록]
   ├── merge_rows() → 연속 충전/방전 스텝 합산
   ├── Chg, Dchg 추출 → 용량/mincapacity = 비율로 변환
   ├── Eff = Dchg / Chg
   ├── Eff2 = Chg.shift(-1) / Dchg
   └── df.NewData 구성 (100행 × 12열)
   
5. return [1689.0, df]

6. graph_output_cycle(df, ...)
   ├── ax1: df.NewData.Dchg 산점도
   ├── ax2: df.NewData.Eff 산점도
   ├── ax3: df.NewData.Temp 산점도
   ├── ax4: df.NewData.dcir 산점도 (선 연결)
   ├── ax5: df.NewData.Eff2 산점도
   └── ax6: df.NewData.RndV + df.NewData.AvgV 산점도 (2개 시리즈)

7. 엑셀 저장 (saveok 체크 시): df.NewData → 엑셀 시트
   그림 저장 (figsaveok 체크 시): matplotlib figure → PNG/PDF
```

---

## 13. 자주 마주치는 값들의 단위 변환 요약

| 원본 단위 | 변환 | 결과 단위 | 해당 컬럼 |
|---------|------|---------|---------|
| μAh | ÷ 1000 | mAh | DchgCap, chgCap |
| μV | ÷ 1,000,000 | V | Ocv |
| m°C | ÷ 1000 | °C | Temp |
| μΩ | ÷ 1000 | mΩ | imp → dcir |
| mAh | ÷ mincapacity | 무단위 비율 | Dchg, Chg |
| μWh | ÷ 1000 | mWh | DchgEngD → DchgEng |

---

## 14. 핵심 요약

| 질문 | 답 |
|------|----|
| df.NewData란? | 사이클 1개 = 1행인 분석 결과 표 (100사이클 → 100행) |
| Cycleraw란? | 스텝 1개 = 1행인 원시 데이터 표 (100사이클 → ~300행) |
| pivot_table이란? | Cycleraw(스텝 단위)를 df.NewData(사이클 단위)로 변환하는 함수 |
| Dchg가 1.0이란? | 기준 용량의 100%를 방전했다는 의미 |
| DCIR가 증가란? | 내부 저항 상승 → 열화 진행 중 |
| Eff와 Eff2의 차이는? | Eff=같은 사이클 내 효율, Eff2=연속 사이클 간 효율 |
| Toyo/PNE가 같은 그래프인 이유는? | 두 경로 모두 df.NewData 형식으로 통일되기 때문 |

---

## 관련 파일 경로

- 메인 코드: [DataTool_dev/DataTool_optRCD_proto_.py](../../../DataTool_dev/DataTool_optRCD_proto_.py)
- 테스트: [tests/test_cycle_data_loading.py](../../../tests/test_cycle_data_loading.py)
- 회귀 테스트: [tests/test_pne_restore.py](../../../tests/test_pne_restore.py)
- 변경 로그: [docs/code/01_변경로그/260404_refactor_profile_render_loop.md](../01_변경로그/260404_refactor_profile_render_loop.md)
