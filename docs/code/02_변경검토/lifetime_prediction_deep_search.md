# 수명 예측 기능 딥서치 보고서

## 대상 코드

`BatteryDataTool_origin/BatteryDataTool.py` (14,168줄)

> 작성일: 2026-02-19

---

## 목차

1. [공통 수학 모델 — 복합 지수 열화 방정식](#1-공통-수학-모델--복합-지수-열화-방정식)
2. [EU 수명 예측 (tab_4)](#2-eu-수명-예측-tab_4)
3. [승인 수명 예측 (tab_3)](#3-승인-수명-예측-tab_3)
4. [실수명 예측 (FitTab)](#4-실수명-예측-fittab)
5. [기능 비교 요약](#5-기능-비교-요약)
6. [데이터 흐름 다이어그램](#6-데이터-흐름-다이어그램)

---

## 1. 공통 수학 모델 — 복합 지수 열화 방정식

세 기능 모두 **동일한 형태의 8-파라미터 복합 지수 열화 모델**을 사용한다. 이 모델은 배터리 용량 열화를 **두 개의 독립적인 열화 메커니즘의 합**으로 표현한다.

### 1.1 기본 방정식 (BaseEquation)

$$
\text{BaseEquation}(x, T) = \exp(a \cdot T + b) \cdot (x \cdot f_d)^{b_1} + \exp(c \cdot T + d) \cdot (x \cdot f_d)^{(e \cdot T + f)}
$$

여기서:
- $x$ : 사이클 수 (또는 일수)
- $T$ : 온도 (켈빈, K)
- $f_d$ : 가속 계수 (frequency/degradation factor)
- $a, b, b_1, c, d, e, f$ : 피팅 파라미터 (총 7개)
- $f_d$ : 가속비 파라미터 (1개)

### 1.2 용량 열화 모델 (capacityfit)

$$
\text{SOH}(x, T) = 1 - \text{BaseEquation}(x, T)
$$

- 초기 SOH = 1 (100%)에서 시작
- BaseEquation의 값이 커질수록 용량 열화 증가
- **첫 번째 항** $\exp(a \cdot T + b) \cdot (x \cdot f_d)^{b_1}$ → SEI 성장 등 **calendar aging** 관련 열화
- **두 번째 항** $\exp(c \cdot T + d) \cdot (x \cdot f_d)^{(e \cdot T + f)}$ → 리튬 석출 등 **cycle aging** 관련 열화

### 1.3 스웰링 모델 (swellingfit)

$$
\text{Swelling}(x, T) = \text{BaseEquation}(x, T)
$$

- 스웰링은 BaseEquation 값 자체가 팽창량을 나타냄
- `fix_swelling_eu` 체크 시 활성화

### 1.4 8개 파라미터 초기값

```python
parini1 = [a=0.03, b=-18, b1=0.7, c=2.3, d=-782, e=-0.28, f=96, fd=1]
```

| 파라미터 | 기본값 | 물리적 의미 |
|----------|--------|-------------|
| a | 0.03 | 온도 의존 계수 (1차 항) |
| b | -18 | 상수 오프셋 (1차 항) |
| b1 | 0.7 | 사이클 지수 (1차 항, ~√x 거동) |
| c | 2.3 | 온도 의존 계수 (2차 항) |
| d | -782 | 상수 오프셋 (2차 항) |
| e | -0.28 | 온도-사이클 교차 계수 |
| f | 96 | 사이클 지수 상수항 |
| fd | 1 | 가속 계수 (배율) |

### 1.5 모델 특성

- **아레니우스(Arrhenius) 기반**: 온도 T가 지수 계수에 곱해져 온도 가속을 표현
- **타펠(Tafel) 기반**: 전압/전류 영향을 지수 함수로 모델링
- **이중 열화 메커니즘**: 두 항이 서로 다른 온도/사이클 의존성을 가짐
- **유연성**: 8개 파라미터로 다양한 열화 패턴 피팅 가능

---

## 2. EU 수명 예측 (tab_4)

### 2.1 개요

| 항목 | 내용 |
|------|------|
| **탭 이름** | "Eu 수명 예측" |
| **탭 위젯** | `tab_4` |
| **목적** | 다중 온도 시험 데이터로부터 8-파라미터 열화 모델을 피팅하고 수명(EOL cycle)을 예측 |
| **출력 탭** | `cycle_simul_tab_eu` |

### 2.2 UI 구성요소

| 위젯 | 용도 |
|------|------|
| `aTextEdit_eu` ~ `fdTextEdit_eu` | 8개 파라미터 입력/표시 (a, b, b1, c, d, e, f, fd) |
| `fdTextEdit_eu_2` | 가속 상수 결과 표시 (const_fd) |
| `cycparameter_eu` | 파라미터 파일 경로 표시 |
| `simul_x_max_eu` | X축(사이클) 최대값 (기본: 5000) |
| `simul_y_max_eu` | Y축 최대값 (기본: 1.0) |
| `simul_y_min_eu` | Y축 최소값 (기본: 0.8) |
| `fix_swelling_eu` | 스웰링 모드 체크박스 |
| `FitConfirm_eu` | "변수 계산" 버튼 |
| `ConstFitConfirm_eu` | "변수 고정" 버튼 |
| `indivConstFitConfirm_eu` | "개별 결과 변수 고정" 버튼 |
| `ParameterReset_eu` | 파라미터 초기화 버튼 |
| `TabReset_eu` | 탭 초기화 버튼 |
| `load_cycparameter_eu` | 파라미터 불러오기 |
| `save_cycparameter_eu` | 파라미터 저장 |

### 2.3 서브 기능 3가지

#### 2.3.1 변수 계산 (`eu_fitting_confirm_button`)

**흐름**:

1. **데이터 로딩**: TSV 파일 선택 (다중 온도 시험 데이터)
2. **데이터 구조 판별**:
   - 컬럼명이 숫자 → 온도 값으로 해석 (예: "23", "35", "45")
   - 3열 단위 데이터 → (사이클수, 온도, 용량비) 순서
3. **초기 용량 보정**: 첫 2점 선형보간으로 cycle=0 시점의 100% 용량 추정
4. **절대온도 변환**: $T < 273$이면 $T = T + 273$ (°C → K)
5. **curve_fit 실행**: `scipy.optimize.curve_fit`으로 8개 파라미터 동시 피팅
   - `maxfev=100000` (최대 반복 횟수)
   - 용량 모드: `capacityfit(x, a, b, b1, c, d, e, f, fd)`
   - 스웰링 모드: `swellingfit(x, a, b, b1, c, d, e, f, fd)`
6. **R² 계산**: $R^2 = 1 - \frac{SS_{res}}{SS_{tot}}$
7. **EOL 산정**: 
   - 용량 모드: $|\text{result} - 0.8|$이 최소인 사이클 = 80% 수명
   - 스웰링 모드: $|0.08 - \text{result}|$이 최소인 사이클 = 8% 팽창 수명
8. **그래프 출력**: 온도별 예측 곡선 + 실데이터 scatter

**입력 데이터 형식**:
```
cycle  23   35   45        ← 온도가 컬럼명
1      1.00 1.00 1.00
2      0.99 0.99 0.99
...
```
또는:
```
cycle  temp  capacity  cycle  temp  capacity  ...    ← 3열 반복
1      23    0.995     1      35    0.993
```

**그래프 출력** (용량 모드):
- 23°C: 파란색 곡선 + scatter
- 35°C: 주황색 곡선 + scatter
- 45°C: 빨간색 곡선 + scatter
- suptitle에 피팅된 8개 파라미터 값 표시

#### 2.3.2 변수 고정 (`eu_constant_fitting_confirm_button`)

**목적**: a~f 파라미터를 고정하고 **fd(가속 계수)만 피팅**

**흐름**:

1. 기존 a~f 파라미터를 UI에서 읽어 **고정**
2. 시험 데이터 로딩 (3열 형식: cycle, temp, capacity)
3. `curve_fit`으로 **fd 1개만** 피팅 (`p0=[fd_par1]`)
4. 5개 온도 (23, 28, 35, 40, 45°C)에 대해 예측 곡선 생성
5. 각 온도별 EOL 사이클 계산
6. 가속 상수 = `popt[0] / p0[0]` (피팅된 fd / 초기 fd)

**용도**: 이미 모델이 피팅된 상태에서 **새로운 셀/조건의 가속비를 빠르게 확인**

#### 2.3.3 개별 결과 변수 고정 (`eu_indiv_constant_fitting_confirm_button`)

**목적**: 각 데이터 파일을 **개별적으로** fd만 피팅하여 결과를 비교

**흐름**:

1. a~f 파라미터 고정 (2.3.2와 동일)
2. 23°C 데이터만 `dfall.t == 296`으로 필터링
3. 각 파일별로 개별적으로 fd 피팅
4. EOL 사이클, R², 가속 상수를 개별 탭에 표시
5. 결과를 `result_all` DataFrame에 누적 → "estimation" 시트로 저장

### 2.4 파라미터 관리

| 기능 | 메서드 | 동작 |
|------|--------|------|
| 초기화 | `eu_parameter_reset_button()` | 8개 파라미터를 기본값으로 리셋 |
| 불러오기 | `eu_load_cycparameter_button()` | TSV 파일에서 "02C" 컬럼 파라미터 로드 |
| 저장 | `eu_save_cycparameter_button()` | 현재 파라미터를 `d:/para_*.txt` 파일로 저장 |

### 2.5 EOL 기준

| 모드 | EOL 조건 |
|------|----------|
| 용량 | SOH = 80% (capacity ratio ≥ 0.8) |
| 스웰링 | 스웰링 = 8% (swelling ≤ 0.08) |

---

## 3. 승인 수명 예측 (tab_3)

### 3.1 개요

| 항목 | 내용 |
|------|------|
| **탭 이름** | "승인 수명 예측" |
| **탭 위젯** | `tab_3` |
| **목적** | 실제 충방전 데이터(PNE 사이클러)에서 0.5C/0.2C 데이터를 분리 → 기존 파라미터 기반으로 가속비(fd) 피팅 → 실제 수명 곡선과 비교 |
| **출력 탭** | `cycle_simul_tab` |

### 3.2 EU 수명 예측과의 핵심 차이

| 항목 | EU 수명 예측 | 승인 수명 예측 |
|------|-------------|--------------|
| **입력 데이터** | TSV 파일 (가공된 수명 데이터) | PNE 충방전기 Raw 데이터 |
| **피팅 대상** | 8개 파라미터 전체 또는 fd만 | **fd만** (02C/05C 각각) |
| **파라미터 세트** | 1개 | **2개** (02C용 + 05C용) |
| **데이터 전처리** | 없음 (이미 가공됨) | `pne_simul_cycle_data()`로 Raw → 수명 데이터 변환 |
| **장수명 보정** | 없음 | `cyc_long_life`, `simul_long_life` 옵션 |
| **온도** | 다중 온도 | **23°C 고정** |

### 3.3 UI 구성요소

| 위젯 | 용도 |
|------|------|
| `aTextEdit_02c` ~ `fdTextEdit_02c` | 0.2C 파라미터 (8개) |
| `aTextEdit_05c` ~ `fdTextEdit_05c` | 0.5C 파라미터 (8개) |
| `cycparameter` | 0.2C 파라미터 파일 경로 |
| `cycparameter2` | 0.5C 파라미터 파일 경로 |
| `simul_x_max` | X축 최대 (기본: 2000) |
| `simul_y_max` / `simul_y_min` | Y축 범위 (기본: 0.8~1.1) |
| `cyc_long_life` | "평가 중 장수명 적용" 체크 |
| `simul_long_life` | "결과 중 장수명 반영" 체크 |
| `load_cycparameter` | 02C/05C 파라미터 순차 로드 |
| `pathappcycestimation` | Cyclepath 선택 버튼 |
| `folderappcycestimation` | 데이터 file 선택 버튼 |

### 3.4 데이터 전처리 — `pne_simul_cycle_data()`

Raw PNE 데이터를 승인 평가용 수명 데이터로 변환하는 핵심 함수:

**반환값**: `[mincapacity, df05, df05_cap_max, df02, df02_cap_max, df05_long_cycle, df05_long_value, df_all]`

| 인덱스 | 변수 | 내용 |
|--------|------|------|
| 0 | `mincapacity` | 셀 용량 (mAh) |
| 1 | `df05` | 0.5C 방전 데이터 (사이클 vs 용량비) |
| 2 | `df05_cap_max` | 0.5C 최대 용량 |
| 3 | `df02` | 0.2C 방전 데이터 (사이클 vs 용량비) |
| 4 | `df02_cap_max` | 0.2C 최대 용량 |
| 5 | `df05_long_cycle` | 장수명 적용 사이클 목록 |
| 6 | `df05_long_value` | 장수명 보정 값 목록 |
| 7 | `df_all` | 전체 원시 데이터 |

**전처리 로직**:

1. SaveEndData.csv 로드 → 사이클별 방전용량/전류/온도/전압 피벗 테이블
2. 전류 기준 0.5C (0.49~0.51 범위) 필터링 → `df05`
3. 전류 기준 0.2C (0.19~0.21 범위) 필터링 → `df02`
4. 최대 용량 보정: 첫 30사이클 기울기 역추정 → cycle=0 용량 추정
5. 용량비 = 방전용량 / 추정 최대용량
6. **장수명 감지**: 충전 최대전압 급감(-15mV) 또는 방전 최소전압 급증(+50mV) 시 장수명 이벤트로 판정 → `long_acc` 누적 보정

### 3.5 서브 기능 2가지

#### 3.5.1 Cyclepath 선택 (`path_approval_cycle_estimation_button`)

**흐름**:

1. `pne_path_setting()`으로 PNE 충방전기 경로 설정
2. 각 폴더 내 서브폴더(채널)를 순회
3. `pne_simul_cycle_data(FolderBase, ...)` → 0.5C/0.2C 데이터 추출
4. 장수명 보정 적용 (`cyc_long_life` 체크 시)
5. **0.5C 데이터** → 02C 파라미터 기반 fd 피팅
   - `curve_fit(cyccapparameter, (x, T=296), y, p0=[fd_par1])` 
6. **0.2C 데이터** → 05C 파라미터 기반 fd 피팅
   - `curve_fit(cyccapparameter02, (x, T=296), y, p0=[fd_par2])`
7. R² 및 가속비 계산
8. 실데이터 + 예측 곡선 오버레이 그래프
9. Excel 출력: `app_cycle`, `highrate_cycle`, `rate02c_cycle` 시트

**결과 그래프 범례**:
- `가속 = {fd_fitted / fd_initial}` (가속비)
- `오차 = {R²}` (결정 계수)
- 실선: 0.5C 예측, 점선: 0.2C 예측

#### 3.5.2 데이터 file 선택 (`folder_approval_cycle_estimation_button`)

**목적**: 이미 가공된 TSV 파일에서 직접 승인 수명 평가 (PNE 접근 없이)

**흐름**:

1. TSV 파일 선택 (6열 단위: TotlCycle, Dchg, Temp, Curr, max_vol, min_vol)
2. `pne_simul_cycle_data_file(df_trim, ...)` → 파일 기반 수명 데이터 추출
3. 3.5.1과 동일한 피팅 및 그래프 로직

### 3.6 장수명(Long-life) 보정 메커니즘

시험 중 "장수명 모드"가 적용되면 충전 전압이 하향 조정되어 용량이 급격히 감소한다. 이를 보정:

```python
# 감지: 최대전압 -15mV 감소 OR 최소전압 +50mV 증가
if (max_vol_diff < -15) or (min_vol_diff > 50):
    long_event_detected → long_acc 누적

# 보정:
df05["Dchg"] = df05["Dchg"] - df05["long_acc"]
```

- **`cyc_long_life`**: 피팅 입력 데이터에서 장수명 효과 제거
- **`simul_long_life`**: 결과 예측 곡선에 장수명 효과 반영
  - `real_y1 = dfall.y * cap_max - cyctemp[1]["long_acc"]`

---

## 4. 실수명 예측 (FitTab)

### 4.1 개요

| 항목 | 내용 |
|------|------|
| **탭 이름** | "실수명 예측" |
| **탭 위젯** | `FitTab` |
| **목적** | 사이클 + 저장 복합 열화를 시뮬레이션하여 **실사용 시나리오 기반** 배터리 수명 예측 |
| **출력 탭** | `real_cycle_simul_tab` |

### 4.2 EU/승인 수명 예측과의 핵심 차이

| 항목 | EU/승인 수명 예측 | 실수명 예측 |
|------|----------------|------------|
| **접근 방식** | 피팅 기반 (curve_fit) | **시뮬레이션 기반** (반복 계산) |
| **파라미터 세트** | 1~2개 | **4개** (사이클 용량/저항 + 저장 용량/저항) |
| **열화 요인** | 사이클만 | **사이클 + 저장1 + 저장2** |
| **온도** | 다중 온도 피팅 | **조건별 단일 온도** |
| **가속 계수 산정** | 단순 fd | **Tafel식 + 아레니우스식 복합** |
| **출력** | 용량 곡선만 | **용량 + 저항 + 상세 분해** |

### 4.3 UI 구성요소

#### 4.3.1 파라미터 그룹 (4세트 × 8개 = 32개)

| 그룹 | 위젯 접미사 | 용도 |
|------|-----------|------|
| 사이클 용량 | `aTextEdit` ~ `fdTextEdit` | 사이클에 의한 용량 열화 |
| 저장 용량 | `aTextEdit_2` ~ `fdTextEdit_2` | 저장에 의한 용량 열화 |
| 사이클 저항 | `aTextEdit_3` ~ `fdTextEdit_3` | 사이클에 의한 저항 증가 |
| 저장 저항 | `aTextEdit_4` ~ `fdTextEdit_4` | 저장에 의한 저항 증가 |

#### 4.3.2 시뮬레이션 조건

| 위젯 | 의미 | 기본값 |
|------|------|--------|
| `xaxixTextEdit` | X축 최대 (사이클) | 1500 |
| `UsedCapTextEdit` | 1회 사용 용량 (비율) | 1 |
| `DODTextEdit` | DOD (비율) | 1 |
| `CrateTextEdit` | 충전 C-rate | 1 |
| `DcrateTextEdit` | 방전 C-rate | 1 |
| `SOCTextEdit` | 최대 전압 (V) | 4.43 |
| `TempTextEdit` | 사이클 온도 (°C) | 23 |

#### 4.3.3 저장 조건 (2단계)

| 위젯 | 저장1 | 저장2 |
|------|-------|-------|
| 전압(V) | `SOCTextEdit_3` (4.43) | `SOCTextEdit_2` (4.43) |
| 온도(°C) | `TempTextEdit_3` (23) | `TempTextEdit_2` (23) |
| 방치시간(day) | `RestTextEdit_2` (0.167) | `RestTextEdit` (0.167) |
| Count(hr/cycle) | `txt_storageratio` (0) | `txt_storageratio2` (0) |

#### 4.3.4 장수명 및 표시 옵션

| 위젯 | 용도 |
|------|------|
| `nolonglife` | 장수명 미적용 라디오 |
| `hhp_longlife` | 장수명 적용 라디오 |
| `txt_longcycleno` | 장수명 사이클 번호 (예: "0 300 400 700 1000") |
| `txt_longcyclevol` | 장수명 전압 감소량 (예: "0 0.02 0.04 0.06 0.11") |
| `txt_relcap` | 실제 용량비 (예: "96.5 95.1 93.7 92.3 88.8") |
| `chk_cell_cycle` | Cell 수명 표시 |
| `chk_set_cycle` | SET 수명 표시 |
| `chk_detail_cycle` | 상세 수명 (사이클/저장별 분해) 표시 |

### 4.4 시뮬레이션 알고리즘 — `simulation_confirm_button()`

#### 4.4.1 파라미터 로드

```
d://parameter/
├── para_cyccapparameter.txt   → df_cyc  (사이클 가속 계수)
├── para_stgcapparameter.txt   → df_stg  (저장 가속 계수)
├── para_capparameter.txt      → df_par  (사이클/저장 용량 파라미터)
├── para_cycirparameter.txt    → df_cyc2 (사이클 저항 가속 계수)
├── para_stgirparameter.txt    → df_stg2 (저장 저항 가속 계수)
└── para_irparameter.txt       → df_par2 (사이클/저장 저항 파라미터)
```

- `df_par` 에서 사이클 용량(열 0) + 저장 용량(열 1) 파라미터 로드
- `df_par2` 에서 사이클 저항(열 0) + 저장 저항(열 1) 파라미터 로드
- `df_cyc`, `df_stg` 에서 **가속 계수 테이블** 로드

#### 4.4.2 가속 계수(fd) 산정

**사이클 fd** — 타펠식 × 아레니우스식 복합:

$$
f_{d,\text{cycle}} = (\alpha_1 \cdot C_{\text{rate}} + \alpha_2) \cdot (\beta_1 \cdot V_{\text{SOC}} + \beta_2) \cdot (\gamma_1 \cdot \text{DOD} + \gamma_2) \cdot f_{d,\text{base}}
$$

```python
cycle_cap_simul_fd = (df_cyc.Crate[0] * cycle_crate + df_cyc.Crate[1]) 
                   * (df_cyc.SOC[0] * cycle_soc_cal + df_cyc.SOC[1]) 
                   * (df_cyc.DOD[0] * cycle_dod + df_cyc.DOD[1]) 
                   * df_cyc.fd[0]
```

**저장 fd** — 타펠식 직접 산출:

$$
f_{d,\text{storage}} = \exp(\alpha \cdot V_{\text{SOC}} + \beta)
$$

```python
storage_cap_simul_fd = np.exp(df_stg[0] * storage_soc + df_stg[1])
```

#### 4.4.3 반복 시뮬레이션 루프

**각 반복(i = 0 ~ 100,000)**에서 다음 3단계를 순차 실행:

```
┌─────────────────────────────────────────────────┐
│  Step 1: 사이클 열화                              │
│  ├─ 현재 SOH로 등가 사이클 역산 (root_scalar)      │
│  ├─ usedcap만큼 사이클 진행                        │
│  ├─ 용량 열화 △cap + 저항 열화 △ir 계산             │
│  └─ SOH 갱신, 시간 누적                           │
│                                                 │
│  Step 2: 저장1 열화                               │
│  ├─ 현재 SOH로 등가 저장 시간 역산 (root_scalar)    │
│  ├─ storage_rest1 만큼 방치                       │
│  ├─ 용량 열화 + 저항 열화 계산                      │
│  └─ SOH 갱신, 시간 누적                           │
│                                                 │
│  Step 3: 저장2 열화                               │
│  ├─ 현재 SOH로 등가 저장 시간 역산 (root_scalar)    │
│  ├─ storage_rest2 만큼 방치                       │
│  ├─ 용량 열화 + 저항 열화 계산                      │
│  └─ SOH 갱신, 시간 누적                           │
│                                                 │
│  종료 조건: SOH < 0.75 또는 NaN 또는 cycle > xscale│
└─────────────────────────────────────────────────┘
```

#### 4.4.4 역함수 계산 (root_scalar)

현재 SOH에서 "등가 사이클 수"를 역산하는 핵심 단계:

$$
\text{cyccapparameter}(x) = 1 - \text{BaseEquation}(a, b, f_d, b_1, c, d, e, f, T, -\text{SOH}, x) = 0
$$

`scipy.optimize.root_scalar(cyccapparameter, bracket=[0, 500000], method='brentq')`

→ 현재 SOH에 해당하는 등가 사이클 $x_0$을 Brent 법으로 탐색

→ $x_0$에서 $x_0 + \text{usedcap}$ 까지의 열화 증분을 계산:

$$
\Delta\text{cap} = f(x_0) - f(x_0 + \text{usedcap})
$$

#### 4.4.5 장수명 보정 로직

```python
# 장수명 사이클 스텝: [0, 300, 400, 700, 1000]
# 장수명 전압 감소: [0, 0.02, 0.04, 0.06, 0.11]
# 실제 용량비:     [96.5, 95.1, 93.7, 92.3, 88.8]

for cyc_i in range(0, len(long_cycle) - 1):
    if complexcycle >= long_cycle[cyc_i] and complexcycle <= long_cycle[cyc_i + 1]:
        cycle_soc_cal = cycle_soc - long_cycle_vol[cyc_i]  # 전압 보정
        para_rsoh = real_cap[cyc_i] / 100                  # 실용량 보정
```

→ 시뮬레이션 진행에 따라 **충전 전압이 단계적으로 감소** → fd 감소 → 열화 속도 저감

#### 4.4.6 결과 DataFrame

| 컬럼 | 의미 |
|------|------|
| `cycle` | 누적 사이클 수 |
| `time` | 누적 시간 (day) |
| `storagecycle` | 저장 환산 사이클 |
| `degree_cycle_cap` | 사이클 용량 열화 증분 |
| `degree_storage1_cap` | 저장1 용량 열화 증분 |
| `degree_storage2_cap` | 저장2 용량 열화 증분 |
| `degree_cycle_dcir` | 사이클 저항 열화 증분 |
| `degree_storage1_dcir` | 저장1 저항 열화 증분 |
| `degree_storage2_dcir` | 저장2 저항 열화 증분 |
| `SOH` | 현재 용량 건전도 (0~1) |
| `rSOH` | 실제 SET 용량 (장수명 반영) |
| `SOIR` | 누적 저항 증가율 |

### 4.5 출력 그래프 (2×2 배치)

| 축 | X축 | Y축 | 내용 |
|----|------|------|------|
| `axe1` | cycle | Capacity | Cell/SET 용량 + 상세 분해 |
| `axe4` | day | Capacity | 시간 기준 용량 |
| `axe2` | cycle | Swelling | 저항 증가 + 상세 분해 |
| `axe5` | day | Swelling | 시간 기준 저항 |

**표시 옵션**:
- `chk_cell_cycle` → Cell 수명 (파란색, SOH)
- `chk_set_cycle` → SET 수명 (검정색, rSOH = SOH × 실용량비)
- `chk_detail_cycle` → 상세 분해 (빨강=사이클, 초록=저장1, 자홍=저장2)

### 4.6 입력 조건 파일 형식

조건 파일 (TSV)은 다음 순서로 구성:

| 행 | 파라미터 | 예시 |
|----|----------|------|
| 0 | 장수명 사이클 번호 | 0 300 400 700 1000 |
| 1 | 장수명 전압 감소 | 0 0.02 0.04 0.06 0.11 |
| 2 | 실제 용량비 | 96.5 95.1 93.7 ... |
| 3 | X축 최대 | 1500 |
| 4 | 사용 용량 | 1 |
| 5 | DOD | 1 |
| 6 | 충전 C-rate | 1 |
| 7 | 최대 전압 (V) | 4.43 |
| 8 | 방전 C-rate | 1 |
| 9 | 온도 (°C) | 23 |
| 10 | 저장1 전압 | 4.43 |
| 11 | 저장1 온도 | 23 |
| 12 | 저장1 방치시간 | 0.167 |
| 13 | 저장2 전압 | 4.43 |
| 14 | 저장2 온도 | 23 |
| 15 | 저장2 방치시간 | 0.167 |

---

## 5. 기능 비교 요약

### 5.1 전체 비교표

| 항목 | EU 수명 예측 | 승인 수명 예측 | 실수명 예측 |
|------|-------------|--------------|------------|
| **탭** | tab_4 | tab_3 | FitTab |
| **방법론** | 다중온도 피팅 | 가속비 비교 | 시간 적분 시뮬레이션 |
| **입력** | TSV (가공 데이터) | PNE Raw 또는 TSV | 조건 파일 + 파라미터 폴더 |
| **피팅** | curve_fit (8개 또는 1개) | curve_fit (fd만, 2세트) | root_scalar (역산) |
| **온도** | 23/35/40/45°C | 23°C 고정 | 사용자 지정 |
| **열화 요인** | 사이클만 | 사이클만 | 사이클 + 저장1 + 저장2 |
| **파라미터 세트** | 1개 (8파라미터) | 2개 (02C/05C) | 4개 (32파라미터) |
| **가속 계수 산정** | fd 직접 | fd 직접 | Tafel × Arrhenius 복합 |
| **장수명 보정** | 없음 | 전압 보정 | 전압 + 실용량 보정 |
| **출력 지표** | SOH, EOL cycle | SOH, 가속비, R² | SOH, rSOH, SOIR |
| **그래프** | 온도별 곡선 | 실데이터+예측 오버레이 | 2×2 (cycle/day × 용량/저항) |
| **종료 조건** | EOL = 80% | 사용자 설정 | SOH < 75% |

### 5.2 활용 시나리오

```
[1단계] EU 수명 예측
  └─ 다중 온도 수명 데이터 → 8-파라미터 피팅 → 기본 열화 모델 확립

[2단계] 승인 수명 예측
  └─ 실제 시험 데이터 + 기존 파라미터 → 가속비 확인 → 시험 조건 검증

[3단계] 실수명 예측
  └─ 확립된 파라미터 + 실사용 시나리오 → 사이클+저장 복합 시뮬레이션 → 제품 수명 예측
```

---

## 6. 데이터 흐름 다이어그램

### 6.1 EU 수명 예측

```
TSV 파일 (온도별 수명 데이터)
    │
    ▼
┌──────────────────────┐
│ 데이터 파싱            │
│ (컬럼명 또는 3열 구조)  │
└──────────┬───────────┘
           │
    ▼──────▼──────▼
  23°C   35°C   45°C
    │      │      │
    ▼──────▼──────▼
┌──────────────────────┐
│ 초기 용량 보정          │
│ (선형 보간 → y(0)=1)   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ curve_fit              │
│ 8-파라미터 피팅          │
│ maxfev=100,000         │
└──────────┬───────────┘
           │
    ┌──────┼──────┐
    ▼      ▼      ▼
  예측곡선  R²   EOL cycle
    │      │      │
    ▼──────▼──────▼
┌──────────────────────┐
│ 그래프 + Excel 출력     │
└──────────────────────┘
```

### 6.2 승인 수명 예측

```
PNE 충방전기 Raw 데이터 (SaveEndData.csv)
    │
    ▼
┌──────────────────────────────┐
│ pne_simul_cycle_data()         │
│ ├─ pivot_table (사이클별 요약)   │
│ ├─ 0.5C/0.2C 분리              │
│ ├─ 초기 용량 추정                │
│ └─ 장수명 이벤트 감지             │
└──────────┬───────────────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
  0.5C 데이터    0.2C 데이터
    │             │
    ▼             ▼
┌────────────┐ ┌────────────┐
│ curve_fit   │ │ curve_fit   │
│ fd 1개 피팅  │ │ fd 1개 피팅  │
│ (02C 모델)  │ │ (05C 모델)  │
└─────┬──────┘ └─────┬──────┘
      │              │
      ▼──────────────▼
┌──────────────────────────────┐
│ 가속비 계산: fd_fitted / fd_init│
│ R² 계산                        │
│ 오버레이 그래프                   │
└──────────────────────────────┘
```

### 6.3 실수명 예측

```
파라미터 폴더 (6개 파일)     조건 파일 (TSV)
    │                          │
    ▼                          ▼
┌─────────────────────────────────────┐
│ 파라미터 로드 (4세트 × 8 = 32개)       │
│ + 가속 계수 테이블 (Crate, SOC, DOD)   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ fd 산정 (Tafel × Arrhenius 복합)      │
│ ├─ cycle_cap_fd, cycle_dcir_fd       │
│ ├─ storage1_cap_fd, storage1_dcir_fd │
│ └─ storage2_cap_fd, storage2_dcir_fd │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 반복 시뮬레이션 (i = 0 ~ 100,000)     │
│                                     │
│  for each iteration:                │
│   1) root_scalar → 등가 사이클 역산    │
│   2) 사이클 열화 △cap, △ir 계산       │
│   3) SOH, SOIR 갱신                  │
│   4) 저장1 열화 계산 → SOH 갱신        │
│   5) 저장2 열화 계산 → SOH 갱신        │
│   6) 장수명 보정 (해당 시)              │
│                                     │
│  종료: SOH < 0.75 or NaN             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 결과 그래프 (2×2)                      │
│ ├─ (cycle, SOH) + (day, SOH)         │
│ ├─ (cycle, SOIR) + (day, SOIR)       │
│ └─ 상세 분해: cyc/stg1/stg2           │
│                                     │
│ Excel 출력 (선택)                      │
└─────────────────────────────────────┘
```

---

## 부록: 관련 함수 인덱스

| 함수/메서드 | 줄 번호 | 기능 |
|------------|---------|------|
| `graph_eu_set()` | L363 | EU 그래프 기본 설정 (축 범위, 폰트, 범례) |
| `graph_simulation()` | L351 | 시뮬레이션 그래프 기본 설정 |
| `pne_simul_cycle_data()` | L984 | PNE Raw → 승인용 수명 데이터 변환 |
| `pne_simul_cycle_data_file()` | L1076 | 파일 기반 승인용 수명 데이터 변환 |
| `eu_fitting_confirm_button()` | L12853 | EU 변수 계산 |
| `eu_constant_fitting_confirm_button()` | L13053 | EU 변수 고정 |
| `eu_indiv_constant_fitting_confirm_button()` | L13264 | EU 개별 변수 고정 |
| `eu_parameter_reset_button()` | L12785 | EU 파라미터 초기화 |
| `eu_load_cycparameter_button()` | L12798 | EU 파라미터 로드 |
| `eu_save_cycparameter_button()` | L12835 | EU 파라미터 저장 |
| `load_cycparameter_button()` | L12450 | 승인 02C/05C 파라미터 로드 |
| `path_approval_cycle_estimation_button()` | L12487 | 승인 Cyclepath 선택 |
| `folder_approval_cycle_estimation_button()` | L12646 | 승인 데이터 파일 선택 |
| `simulation_confirm_button()` | L13459 | 실수명 시뮬레이션 실행 |
| `simulation_tab_reset_confirm_button()` | L13454 | 실수명 탭 초기화 |
