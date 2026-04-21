# Parameter Generator v9.4 상세 분석 및 BDT 기능 추출 계획

> 작성일: 2026-02-20  
> 목적: Parameter Generator v9.4 (A_Pre-treat, B_Parameter_Generator)의 GITT 분석 로직을 상세히 파악하고, BatteryDataTool에 추가할 기능을 정리한다.

---

## 1. 전체 구조 개요

### 1.1 파일 구성

| 파일 | 역할 | 의존성 |
|------|------|--------|
| `A_Pre-treat_v9.4.py` (132줄) | GITT 원시 CSV에서 CC/Rest 경계점 추출 → 8개 txt 파일 생성 | `pandas`, `numpy` |
| `B_Parameter_Generator_v9.4.py` (861줄) | Pre-treat 결과를 이용하여 전극 파라미터 도출 (OCP, stoichiometry, dV/dSOC matching) | `pandas`, `numpy`, `scipy.interpolate`, `xlwings`, `matplotlib`, `win32api` |
| `Files_Default_v9.4/` | Anode 기본 GITT 데이터 (`gitt_an_ch_v9.4.txt`, `gitt_an_dis_v9.4.txt`) + Excel 템플릿 (`Presets_template_v9.4.xlsx`) |

### 1.2 처리 흐름도

```
┌──────────────────────────────────────────────────────────────────────┐
│                    A_Pre-treat_v9.4.py                              │
│                                                                      │
│  [CSV 원시 데이터]                                                   │
│       │                                                              │
│       ▼                                                              │
│  1. 시간 분해능 필터링 (>0.11s 간격 데이터만)                        │
│       │                                                              │
│       ▼                                                              │
│  2. 전류 변화 감지 → CC/Rest 경계점 분류                             │
│       │                                                              │
│       ├── 충전 CC 시작/종료 (ch1_cc_st, ch2_cc_fin)                  │
│       ├── 충전 Rest 시작/종료 (ch3_rest_st, ch4_rest_fin)            │
│       ├── 방전 CC 시작/종료 (dis1_cc_st, dis2_cc_fin)                │
│       └── 방전 Rest 시작/종료 (dis3_rest_st, dis4_rest_fin)          │
│       │                                                              │
│       ▼                                                              │
│  3. 충/방전 q_ocp, soc_oc, V_OCV 테이블 생성                        │
│                                                                      │
│  ──→ 8개 txt 파일 출력 (results/ 폴더)                               │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                  B_Parameter_Generator_v9.4.py                      │
│                                                                      │
│  1. Pre-treat 결과 로드 (ch2, ch4, dis2, dis4)                      │
│       │                                                              │
│       ▼                                                              │
│  2. Cell GITT에서 q_ocp, soc_oc, v_ocp 계산                         │
│       │                                                              │
│       ▼                                                              │
│  3. SOC=0, SOC=1 경계 OCV 도출                                      │
│       │                                                              │
│       ▼                                                              │
│  4. dV/dSOC Peak Matching (Cell ↔ Anode, 반복 수렴)                  │
│       │                                                              │
│       ▼                                                              │
│  5. Cathode OCP 도출 (V_cell = V_cathode - V_anode)                  │
│       │                                                              │
│       ▼                                                              │
│  6. 전극 면적 / Stoichiometry 계산                                   │
│       │                                                              │
│       ▼                                                              │
│  7. Cathode dV/dSOC 도출                                             │
│       │                                                              │
│       ▼                                                              │
│  8. Excel/txt 파라미터 출력 + 그래프 저장                            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. A_Pre-treat_v9.4.py 상세 분석

### 2.1 입력 데이터 형식

- **CSV 파일** (ANSI 인코딩)
- 컬럼 구조: `[시간(s), 전압(V), 전류(A), 온도(°C)]` (인덱스 기반 접근, 컬럼명 없음)
- 처음 4열만 사용

### 2.2 시간 필터링

```python
# 0.1s 간격 데이터 제거 (고속 샘플링 노이즈 제거)
data_csv = data_csv[data_csv.iloc[:,0] != 0.1].reset_index(drop=True)

# 0.11s 이상 간격의 데이터만 유지 (시간 분해능 필터)
tf_time = ((time_now - time_prev) > 0.11)
data_csv = data_csv[tf_time].reset_index(drop=True)
```

- **목적**: GITT에서 CC 펄스 + Rest 구간의 경계만 추출하기 위해 고빈도 샘플링 행 제거
- **기준**: 연속 데이터의 시간 간격 > 0.11초

### 2.3 CC/Rest 경계점 분류 알고리즘

전류값의 변화(`current_now - current_prev`)를 기준으로 경계 자동 감지:

| 구분 | 조건 | 의미 |
|------|------|------|
| **충전 CC 시작** | `ΔI > 0.01` AND `I > 0.01` | 전류가 양의 방향으로 증가 → CC 충전 시작 |
| **충전 Rest 시작** | `ΔI < -0.01` AND `I == 0` | 전류 급감 후 0이 됨 → CC 종료, Rest 시작 |
| **방전 CC 시작** | `ΔI < -0.01` AND `I < -0.01` | 전류가 음의 방향으로 감소 → CC 방전 시작 |
| **방전 Rest 시작** | `ΔI > 0.01` AND `I == 0` | 전류 급증 후 0이 됨 → CC 종료, Rest 시작 |

- **cc_start** = CC 시작점 행
- **cc_end** = Rest 시작 직전 행 (`idx_rest_start - 1`)
- **rest_start** = CC 종료 직후 행
- **rest_end** = 다음 CC 시작 직전 행 (`idx_cc_start - 1`)

### 2.4 용량/SOC/OCV 테이블 생성

```python
# 충전 q_step 계산 (mAh)
q_step = abs(current) * (time_cc_end - time_rest_end_prev) / 3.6

# SOC 계산
soc = q_accum / q_max  (충전)
soc = 1 - (q_accum / q_max)  (방전)

# OCV = rest_end 시점의 전압
V_OCV = data_rest_end[voltage]
```

### 2.5 출력 파일 (8개)

| 파일명 패턴 | 내용 | 컬럼 구조 |
|-------------|------|-----------|
| `*_data_ch1_cc_st.txt` | 충전 CC 시작점 데이터 | time, voltage, current, temperature |
| `*_data_ch2_cc_fin.txt` | 충전 CC 종료점 데이터 | 〃 |
| `*_data_ch3_rest_st.txt` | 충전 Rest 시작점 데이터 | 〃 |
| `*_data_ch4_rest_fin.txt` | 충전 Rest 종료점 데이터 (= OCV) | 〃 |
| `*_data_dis1_cc_st.txt` | 방전 CC 시작점 데이터 | 〃 |
| `*_data_dis2_cc_fin.txt` | 방전 CC 종료점 데이터 | 〃 |
| `*_data_dis3_rest_st.txt` | 방전 Rest 시작점 데이터 | 〃 |
| `*_data_dis4_rest_fin.txt` | 방전 Rest 종료점 데이터 (= OCV) | 〃 |

---

## 3. B_Parameter_Generator_v9.4.py 상세 분석

### 3.1 입력 데이터

| 데이터 | 소스 | 컬럼 |
|--------|------|------|
| Anode 충전 GITT (기본) | `gitt_an_ch_v9.4.txt` | q_ocp, x, v_ocp |
| Anode 방전 GITT (기본) | `gitt_an_dis_v9.4.txt` | q_ocp, x, v_ocp |
| Cell 충전 CC종료 | `*ch2_cc_fin.txt` (Pre-treat 결과) | time, voltage, current, temp |
| Cell 충전 Rest종료 | `*ch4_rest_fin.txt` (Pre-treat 결과) | 〃 |
| Cell 방전 CC종료 | `*dis2_cc_fin.txt` (Pre-treat 결과) | 〃 |
| Cell 방전 Rest종료 | `*dis4_rest_fin.txt` (Pre-treat 결과) | 〃 |

### 3.2 전극 파라미터 초기값

```python
# Anode stoichiometry 범위
x_soc0_dis = 0.02    # SOC=0일 때 Anode stoichiometry
x_soc1_dis = 0.91    # SOC=1일 때 Anode stoichiometry

# Anode 물성
eps_s_a = 0.680      # Anode 활물질 체적분율
thick_an = 65        # Anode 두께 (μm)
cs_a_max = 28606     # Anode 최대 리튬 농도 (mol/m³)

# Cathode 물성
eps_s_c = 0.667      # Cathode 활물질 체적분율
thick_ca = 50        # Cathode 두께 (μm)
cs_c_max = 52109     # Cathode 최대 리튬 농도 (mol/m³)

dx = 5               # 전극 이산화 간격 (μm)
```

### 3.3 Cell GITT에서 q_ocp, soc_oc, v_ocp 계산

```python
# 충전
gitt_cell_ch['v_ocp'] = rest_fin의 전압 (OCV)
gitt_cell_ch['q_ocp'] = current × (time_cc_fin - time_rest_fin_prev) / 3.6  → cumsum
gitt_cell_ch['soc_oc'] = q_ocp / q_ocp.max()

# 방전
gitt_cell_dis['v_ocp'] = rest_fin의 전압 (OCV)
gitt_cell_dis['q_ocp'] = |current| × (time_cc_fin - time_rest_fin_prev) / 3.6  → cumsum
gitt_cell_dis['soc_oc'] = 1 - (q_ocp / q_ocp.max())
```

### 3.4 SOC=0, SOC=1 경계 OCV 도출

```python
ocv_soc_0 = max(충전 OCV 최소, 방전 OCV 최소)  # 완전방전 OCV 중 큰 값
ocv_soc_1 = min(충전 OCV 최대, 방전 OCV 최대)  # 완전충전 OCV 중 작은 값
q_st = min(충전 용량, 방전 용량)                # 충/방전 GITT 용량 중 작은 값
```

### 3.5 dV/dSOC 계산 방법

**중심 차분법 (Central Difference)**을 사용:

```python
# Cell dV/dSOC
dvds[i] = (v_ocp[i+1] - v_ocp[i-1]) / (soc[i+1] - soc[i-1])

# Anode dV/dSOC (부호 반전: anode OCP는 SOC 증가 시 감소하므로)
dvds[i] = -(v_ocp[i+1] - v_ocp[i-1]) / (soc[i+1] - soc[i-1])

# 경계 처리: 첫/마지막 포인트는 이웃값 복사
dvds[0] = dvds[1]
dvds[-1] = dvds[-2]
```

### 3.6 dV/dSOC Peak Matching 알고리즘 (핵심 반복 수렴 로직)

**목표**: Cell의 dV/dSOC 피크 위치와 Anode의 dV/dSOC 피크 위치를 일치시키는 stoichiometry 파라미터 `x_soc0`, `x_soc1` 자동 최적화

#### 3.6.1 보간 (Interpolation)

```python
# SOC 1% 간격으로 보간하여 비교 테이블 생성
soc_match = np.arange(soc_min, soc_max, 0.01)

# quadratic interpolation 사용
f_interp = interpolate.interp1d(soc, dvds, kind='quadratic')
dvds_match = f_interp(soc_match)
```

#### 3.6.2 피크 검출 (3-Point Peak Finding)

SOC ≈ 0.5 부근 피크 (`peak05`)와 SOC ≈ 0.1 부근 피크 (`peak01`)를 각각 검출:

```
peak05 범위: array1[40:71]  → SOC 0.40~0.70 부근에서 최대값 탐색
peak01 범위: array1[1:18]   → SOC 0.01~0.17 부근에서 최소값 탐색
```

**3-Point 피크 정밀화 알고리즘**:
1. 범위 내 최대(또는 최소)점 `y2` 탐색 → 인덱스 `idx2`
2. 인접 2점 `y1`, `y3` (작은 쪽/큰 쪽) 결정
3. 선형보간으로 정밀 피크 위치 `x_peak` 계산:
   ```
   slope = (y2 - y1) / (x2 - x1)
   x_peak = (x3 + (y3/slope) + ((x1*y2 - x2*y1) / (y2 - y1))) / 2
   y_peak = slope × x_peak + y1 - slope × x1
   ```

#### 3.6.3 수렴 루프

```python
accuracy = 0.00001  # 피크 GAP 허용 오차 (0.001%)
ratio_match = 0.2   # 보정 비율 (한 번에 20%씩 조정)

while not (모든 gap < accuracy):
    # Gap 계산: Anode peak - Cell peak
    gap05_ch = soc_an_ch_peak05 - soc_cell_ch_peak05
    gap01_ch = soc_an_ch_peak01 - soc_cell_ch_peak01
    gap05_dis = soc_an_dis_peak05 - soc_cell_dis_peak05
    gap01_dis = soc_an_dis_peak01 - soc_cell_dis_peak01

    # Stoichiometry 파라미터 조정
    x_soc1_ch += gap05_ch × 0.2   # peak05 → x_soc1 조정
    x_soc0_ch += gap01_ch × 0.2   # peak01 → x_soc0 조정
    x_soc1_dis += gap05_dis × 0.2
    x_soc0_dis += gap01_dis × 0.2
```

**총 8개 피크 매칭** (Cell ch/dis × peak05/01 + Anode ch/dis × peak05/01)

### 3.7 Cathode OCP 도출

```
V_cell = V_cathode - V_anode
→ V_cathode = V_cell + V_anode  (정방향)
```

충전과 방전 각각:
```python
ocp_match_ca = ocp_match_cell + ocp_match_an
```

#### SOC ≈ 0.99 부근 스무딩 처리

Cathode OCP의 고 SOC 영역 (0.99 부근) 급변 구간을 아래 로직으로 평탄화:
1. SOC=0.99 기준 하방 3~90포인트 이동 평균 slope 계산
2. slope가 0.0001 이하인 가장 작은 기울기 지점 탐색
3. 해당 지점 이하/이상을 선형 외삽으로 대체

### 3.8 충/방전 OCP 차이 보정

```python
# 방전 OCP > 충전 OCP인 경우 → 충전 OCP를 방전 + 0.0002로 보정
# 충전 OCP > 방전 OCP인 경우 → 방전 OCP를 충전 - 0.0002로 보정
```

### 3.9 전극 면적 및 Cathode Stoichiometry 계산

```python
# 전극 면적 (m²)
dx_dis = x_soc1_dis - x_soc0_dis
area = q_st / dx_dis / eps_s_a × 10¹⁴ / thick_an / cs_a_max / 96485 × 3.6 → 반올림 → /10⁸

# Cathode stoichiometry 변화량
dy_dis = q_st / (eps_s_c × area × thick_ca × cs_c_max × 96485 / 3.6) × 10⁶

# Cathode stoichiometry (y) 범위
y_soc0_dis = 1 + (soc_y_1_dis × dy_dis)    # SOC=0 → y≈1 근처
y_soc1_dis = y_soc0_dis - dy_dis            # SOC=1 → y < y_soc0
```

**핵심 물리 관계식**:
$$\text{area} = \frac{Q_{st}}{\Delta x \cdot \varepsilon_{s,a} \cdot L_a \cdot c_{s,a,max} \cdot F / 3.6}$$

$$\Delta y = \frac{Q_{st}}{\varepsilon_{s,c} \cdot A \cdot L_c \cdot c_{s,c,max} \cdot F / 3.6}$$

여기서:
- $Q_{st}$: GITT 측정 용량 (mAh)
- $\Delta x$: Anode stoichiometry 변화량 ($x_{soc1} - x_{soc0}$)
- $\varepsilon_{s}$: 활물질 체적분율
- $L$: 전극 두께 (μm)
- $c_{s,max}$: 최대 리튬 농도 (mol/m³)
- $F = 96485$ C/mol (패러데이 상수)

### 3.10 Cathode stoichiometry 0, 1 지점 외삽

y=0, y=1 지점의 Cathode OCP를 마지막 2점 선형 외삽으로 계산:

```python
# y=1 지점 (충전 완료)
v_y_1 = v_edge + (1 - y_edge) / (y_edge - y_adjacent) × (v_edge - v_adjacent)

# y=0 지점 (방전 완료)
v_y_0 = v_edge + (0 - y_edge) / (y_edge - y_adjacent) × (v_edge - v_adjacent)
```

### 3.11 출력 결과물

| 출력 | 형식 | 내용 |
|------|------|------|
| `Presets_<cell>_v9.4.xlsx` | Excel | Anode/Cathode OCP 테이블, 전극 파라미터 |
| `Presets_<cell>_v9.4.txt` | Tab-separated | Excel과 동일 (파라미터 최적화용) |
| `OCV_SOC-0___OCV_SOC-1___Q_OCV___.txt` | 3행 1열 | ocv_soc_0, ocv_soc_1, q_st |
| `Image_dVdSOC_SOC_<cell>_v9.4.png` | 이미지 | dV/dSOC vs. SOC 매칭 그래프 (2×3) |
| `Image_OCP_SOC_<cell>_v9.4.png` | 이미지 | OCP vs. SOC 그래프 (2×4) |

### 3.12 Excel Presets 구조

| 셀/범위 | 내용 |
|---------|------|
| B4 | Anode 격자수 = thick_an / dx |
| B6 | Cathode 격자수 = thick_ca / dx |
| B7 | 격자 크기 = dx / 10⁶ (m) |
| B11 | Anode ε_s |
| B12 | Cathode ε_s |
| B27 | cs_a_max |
| B28 | cs_c_max |
| B29 | 전극 면적 |
| B30-B31 | x_soc0_dis, x_soc1_dis |
| B32-B33 | y_soc1_dis, y_soc0_dis |
| P-Q열 | Anode 방전 OCP (x vs v_ocp) |
| S-T열 | Cathode 방전 OCP (y vs v_ocp) |
| V-W열 | Cell 방전 OCP (soc vs v_ocp) |
| AW-AX열 | Anode 충전 OCP |
| AZ-BA열 | Cathode 충전 OCP |
| BC-BD열 | Cell 충전 OCP |

### 3.13 시각화 그래프 구성

#### dV/dSOC vs. SOC (2×3 격자)
- **상단 3개**: 방전 — SOC 범위별 확대 (저SOC, 중간, 고SOC)
- **하단 3개**: 충전 — 동일 구성
- **각 패널 4개 곡선**: Cell (검정), Anode (파랑), Cathode (빨강), Ca-An 합계 (녹색)

#### OCP vs. SOC (2×4 격자)
- **상단 4개**: 방전 — SOC 범위별 확대 (저SOC, 전체, 고SOC, 전 범위)
- **하단 4개**: 충전 — 동일 구성
- **각 패널 4개 곡선**: Cell (검정), Anode (파랑), Cathode (빨강), Ca-An 계산값 (녹색)

---

## 4. BDT 현재 상태 (GITT 관련)

### 4.1 기존 GITT 기능

| 항목 | 상태 |
|------|------|
| GITT 데이터 로딩 | ⚠️ "Continue" 모드에서 전체 프로파일 로딩만 가능 (GITT 전용 분석 없음) |
| CC/Rest 경계 감지 | ❌ 없음 |
| OCV 추출 (Rest 종료점) | ❌ 없음 (Cycle 데이터 내 Ocv 컬럼만 존재) |
| dV/dSOC 계산 | ❌ 없음 (dVdQ만 있음) |
| dV/dSOC Peak Matching | ❌ 없음 |
| 전극 OCP 분리 | ❌ 없음 |
| Stoichiometry 계산 | ❌ 없음 |
| 전극 면적 계산 | ❌ 없음 |
| 확산 계수 (D_Li) 계산 | ❌ 없음 (PG에도 없음) |

### 4.2 BDT 기존 관련 기능 (재활용 가능)

| 기존 기능 | PG 대응 | 재활용 방법 |
|-----------|---------|-------------|
| `pne_Profile_continue_data()` | Pre-treat CSV 로딩 | GITT 원시 데이터 로딩의 기반 |
| dVdQ / dQdV 계산 | dV/dSOC 계산 | 유사 로직 확장 (SOC 기반으로 변경) |
| `generate_simulation_full()` | dV/dSOC Matching | Anode/Cathode 반전지 데이터 보간 로직 재활용 가능 |
| `np.interp` 사용 | `scipy.interpolate.interp1d` | quadratic 보간으로 업그레이드 필요 |
| matplotlib 그래프 | PG 그래프 | 2×3, 2×4 격자 그래프 추가 |

---

## 5. BDT에 추가할 기능 정의

### 5.1 기능 1: GITT 데이터 전처리 (Pre-treat)

**소스 참조**: `A_Pre-treat_v9.4.py` 전체

| 세부 기능 | 설명 | 우선순위 |
|-----------|------|----------|
| GITT CSV 로딩 | ANSI 인코딩 CSV, 4열 (time, voltage, current, temp) | 상 |
| 시간 분해능 필터링 | 0.11s 이상 간격 데이터만 유지 | 상 |
| CC/Rest 경계 자동 감지 | 전류 변화 기반 충전/방전 CC_start/end, Rest_start/end 분류 | **핵심** |
| OCV 테이블 생성 | q_ocp, soc_oc, V_OCV (rest_fin 전압) | **핵심** |
| 경계점 데이터 저장/표시 | 8종 경계점 데이터 (UI에서 확인 가능하게) | 중 |

**구현 고려사항**:
- BDT의 기존 `Profile_continue_data()` 함수에서 로딩된 연속 프로파일 데이터를 입력으로 활용
- 전류 임계값 0.01A는 셀 용량에 따라 파라미터화 필요
- PNE/Toyo 양쪽 사이클러 데이터 지원

### 5.2 기능 2: Cell GITT OCP 계산

**소스 참조**: `B_Parameter_Generator_v9.4.py` L85~122

| 세부 기능 | 설명 | 우선순위 |
|-----------|------|----------|
| 충전 q_ocp / soc_oc / v_ocp 계산 | CC종료 전류 × 시간 → 적산 용량, OCV | **핵심** |
| 방전 q_ocp / soc_oc / v_ocp 계산 | 동일 (SOC = 1 - q/q_max) | **핵심** |
| SOC=0/1 경계 OCV 도출 | 충/방전 OCV min/max 비교 | 상 |
| OCV vs SOC 그래프 | 충/방전 OCV 곡선 시각화 | 상 |

### 5.3 기능 3: dV/dSOC 계산 및 Peak 검출

**소스 참조**: `B_Parameter_Generator_v9.4.py` L127~290

| 세부 기능 | 설명 | 우선순위 |
|-----------|------|----------|
| dV/dSOC 중심 차분 계산 | 경계 포인트 처리 포함 | **핵심** |
| SOC 1% 간격 보간 | `scipy.interpolate.interp1d(kind='quadratic')` | **핵심** |
| 3-Point Peak 검출 | SOC 0.1/0.5 부근 피크 자동 검출 | 상 |
| dV/dSOC vs. SOC 그래프 | Cell/Anode/Cathode/합계 4종 곡선 | 상 |

### 5.4 기능 4: dV/dSOC Peak Matching (자동 Stoichiometry 최적화)

**소스 참조**: `B_Parameter_Generator_v9.4.py` L126~395

| 세부 기능 | 설명 | 우선순위 |
|-----------|------|----------|
| Anode 기본 GITT 데이터 로딩 | txt 파일 (q_ocp, x, v_ocp) | 상 |
| Peak GAP 계산 (Cell-Anode) | 충전/방전 × peak05/peak01 = 4개 GAP | **핵심** |
| 자동 반복 수렴 | accuracy=0.00001, ratio=0.2로 x_soc0/x_soc1 조정 | **핵심** |
| 전극 물성 파라미터 입력 UI | eps_s, thick, cs_max 등 6개 입력 | 상 |
| Matching 결과 표시 | 최종 x_soc0, x_soc1 + GAP 수렴 이력 | 중 |

### 5.5 기능 5: Cathode OCP 도출

**소스 참조**: `B_Parameter_Generator_v9.4.py` L396~490

| 세부 기능 | 설명 | 우선순위 |
|-----------|------|----------|
| V_cathode = V_cell + V_anode | SOC 매칭된 OCP에서 역산 | **핵심** |
| 고SOC 영역 스무딩 | 이동평균 slope 기반 외삽 | 상 |
| 충/방전 OCP 차이 보정 | 0.0002V 오프셋 | 중 |
| Cathode OCP vs. SOC 그래프 | 충전/방전 양쪽 | 상 |

### 5.6 기능 6: 전극 면적 / Stoichiometry 계산

**소스 참조**: `B_Parameter_Generator_v9.4.py` L491~530

| 세부 기능 | 설명 | 우선순위 |
|-----------|------|----------|
| 전극 면적 계산 | q_st, dx, eps_s_a, thick_an, cs_a_max, F 이용 | 상 |
| Cathode dy 계산 | q_st, area, eps_s_c, thick_ca, cs_c_max 이용 | 상 |
| y_soc0, y_soc1 계산 | Cathode stoichiometry 범위 | 상 |
| Stoichiometry 0/1 외삽 | 선형 외삽으로 y=0, y=1 지점 OCP 추정 | 중 |

### 5.7 기능 7: 파라미터 출력

**소스 참조**: `B_Parameter_Generator_v9.4.py` L606~680

| 세부 기능 | 설명 | 우선순위 |
|-----------|------|----------|
| Excel Presets 파일 생성 | 템플릿 기반, 파라미터 + OCP 테이블 | 상 |
| TXT 파일 출력 | Tab-separated, 15자리 정밀도 | 중 |
| OCV 경계값 파일 출력 | ocv_soc_0, ocv_soc_1, q_st | 중 |

### 5.8 기능 8: 시각화

**소스 참조**: `B_Parameter_Generator_v9.4.py` L683~860

| 세부 기능 | 설명 | 우선순위 |
|-----------|------|----------|
| dV/dSOC vs. SOC 격자 그래프 (2×3) | SOC 범위별 확대 3구간 × 충방전 2종 | 상 |
| OCP vs. SOC 격자 그래프 (2×4) | SOC 범위별 확대 4구간 × 충방전 2종 | 상 |

---

## 6. 구현 전략 및 우선순위

### 6.1 Phase 1 — GITT 전처리 (Pre-treat 포팅)

**목표**: BDT에서 GITT 원시 데이터를 로딩하고 CC/Rest 경계를 자동 분류

1. GITT 데이터 로딩 경로를 기존 `Profile_continue_data()` 활용
2. CC/Rest 경계 감지 함수 `detect_gitt_boundaries()` 신규 구현
3. OCV 테이블 (q_ocp, soc_oc, V_OCV) 자동 생성
4. 결과를 UI 테이블 또는 그래프로 표시

### 6.2 Phase 2 — OCP 분석 (Cell OCP + dV/dSOC)

**목표**: 충/방전 OCV 곡선 + dV/dSOC 계산 및 시각화

1. Cell GITT OCP 계산 로직 구현
2. dV/dSOC 중심 차분 + 보간 함수 구현
3. OCV vs. SOC, dV/dSOC vs. SOC 그래프 추가

### 6.3 Phase 3 — 전극 파라미터 도출 (Peak Matching + Cathode OCP)

**목표**: Anode 기본 데이터와의 Peak Matching으로 전극 파라미터 자동 도출

1. Anode 기본 GITT 데이터 로딩 UI
2. 전극 물성 파라미터 입력 UI (6개)
3. dV/dSOC Peak Matching 자동 수렴 로직
4. Cathode OCP 도출 + 스무딩
5. 전극 면적 / Stoichiometry 계산
6. Presets 결과 파일 출력

### 6.4 Phase 4 — 확장 기능 (PG v9.4에 없는 추가 기능)

**목표**: PG에 없지만 GITT 분석에 유용한 추가 기능

1. **확산 계수 ($D_{Li^+}$) 계산**: GITT Sand's equation 기반
   $$D = \frac{4}{\pi\tau}\left(\frac{m_B V_M}{M_B S}\right)^2\left(\frac{\Delta E_s}{\Delta E_\tau}\right)^2$$
2. **내부 저항 (R_i) 추출**: 각 펄스의 즉시 전압 강하로부터 Ohmic 저항 계산
3. **SOC별 확산 계수 프로파일**: D vs. SOC 곡선
4. **$\sqrt{t}$ vs. V 선형 피팅**: 확산 조건 검증

---

## 7. 데이터 흐름 매핑 (PG → BDT)

```
┌─────────────────┐     ┌──────────────────────────────────────┐
│  PG v9.4        │     │  BDT                                 │
│                 │     │                                      │
│  CSV 수동 입력  │ ──→ │  Profile Continue 로딩 (기존)        │
│                 │     │  또는 직접 CSV 로딩 (신규)           │
│                 │     │                                      │
│  input() 대화   │ ──→ │  UI 입력 위젯 (QLineEdit, QComboBox) │
│                 │     │                                      │
│  path 하드코딩  │ ──→ │  QFileDialog 파일 선택               │
│                 │     │                                      │
│  np.savetxt()   │ ──→ │  UI 테이블 표시 + CSV/Excel 내보내기 │
│                 │     │                                      │
│  plt.savefig()  │ ──→ │  matplotlib 임베딩 그래프            │
│                 │     │                                      │
│  xlwings Excel  │ ──→ │  openpyxl 또는 직접 DataFrame 출력   │
│                 │     │                                      │
│  win32api 팝업  │ ──→ │  QMessageBox                         │
│                 │     │                                      │
│  os.startfile() │ ──→ │  QDesktopServices.openUrl()          │
└─────────────────┘     └──────────────────────────────────────┘
```

---

## 8. 사용하는 주요 라이브러리 (BDT 추가 필요)

| 라이브러리 | PG 용도 | BDT 현재 상태 | 추가 필요 여부 |
|-----------|---------|---------------|---------------|
| `scipy.interpolate` | `interp1d(kind='quadratic')` | ❌ 미사용 (`np.interp`만 사용) | **추가 필요** |
| `xlwings` | Excel 파일 쓰기 | ❌ 미사용 | `openpyxl`로 대체 가능 |
| `win32api` | 완료 메시지 팝업 | ❌ 미사용 | PyQt6 `QMessageBox`로 대체 |
| `shutil` | 파일 복사 | ⚠️ 부분 사용 | 기존 활용 가능 |
| `glob` | 파일 패턴 매칭 | ✅ 사용 중 | 기존 활용 가능 |
| `math` | `ceil`, `floor` | ✅ 사용 중 | 기존 활용 가능 |

---

## 9. 핵심 알고리즘 요약 (BDT 이식 시 주의사항)

### 9.1 전류 변화 기반 CC/Rest 경계 감지
- **임계값 0.01A**: 셀 용량에 비례하여 조정 가능하게 파라미터화 필요
- **prev 생성 방식**: `pd.concat([초기값, shift된 시리즈])` — BDT에서는 `df.shift()` 활용 가능
- **경계 데이터**: `idx - 1` 로 이전 행 참조 → 인덱스 범위 검증 필요

### 9.2 dV/dSOC 중심 차분
- 경계 처리 (`[0]`, `[-1]`)를 이웃값 복사로 처리 — 차분 계산 불가 포인트
- Anode dV/dSOC는 부호 반전 (OCP 감소 방향)

### 9.3 Peak Matching 수렴
- 수렴 조건: 4개 GAP 모두 0.001% 이하
- 발산 방지: ratio_match=0.2 (20%씩 점진 보정)
- **무한 루프 위험**: BDT에서는 최대 반복 횟수 제한 추가 필요

### 9.4 Cathode OCP 스무딩
- SOC=0.99 기준 하방 탐색 → 이동평균 기울기 최소 지점 찾기
- 외삽 시 `(v[i-1] - v[i-3])/2` 패턴 사용 — 2nd order 근사

---

## 10. 부록: 변수 명명 규칙 대응 표

| PG 변수 | 의미 | BDT 권장 명칭 |
|---------|------|--------------|
| `gitt_cell_ch` | Cell 충전 GITT DataFrame | `df_cell_ch` |
| `gitt_cell_dis` | Cell 방전 GITT DataFrame | `df_cell_dis` |
| `gitt_an_ch` | Anode 충전 GITT DataFrame | `df_anode_ch` |
| `gitt_an_dis` | Anode 방전 GITT DataFrame | `df_anode_dis` |
| `gitt_ca_dis_ext` | Cathode 방전 OCP (확장) | `df_cathode_dis_ext` |
| `dvds_match_cell_ch` | 보간된 Cell 충전 dV/dSOC | `dvds_interp_cell_ch` |
| `ocp_match_ca_dis` | 보간된 Cathode 방전 OCP | `ocp_interp_cathode_dis` |
| `soc_match_ch` | 충전 SOC 매칭 배열 | `soc_grid_ch` |
| `x_soc0_dis` | 방전 Anode stoich @SOC=0 | `x_anode_soc0_dis` |
| `eps_s_a` | Anode 활물질 체적분율 | `eps_active_anode` |
| `thick_an` | Anode 두께 (μm) | `thickness_anode` |
| `cs_a_max` | Anode 최대 Li 농도 | `cs_max_anode` |
