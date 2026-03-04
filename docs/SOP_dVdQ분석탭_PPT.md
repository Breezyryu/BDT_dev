# BatteryDataTool - dVdQ 분석 탭 SOP
### Differential Voltage Analysis (미분 전압 분석)

---

## 📌 1. 탭 개요

| 항목 | 내용 |
|------|------|
| **탭 이름** | dVdQ 분석 |
| **목적** | Full Cell 충방전 프로파일을 양극/음극 개별 프로파일로 분리·피팅하여 열화 메커니즘(질량 손실, 슬립) 분석 |
| **데이터 소스** | 양극/음극 개별 Profile (.tsv), 실측 Full Cell Profile (.tsv) |
| **분석 항목** | Voltage Profile 피팅, dV/dQ 곡선 비교, 양극/음극 Mass·Slip 파라미터, RMS 오차 |
| **핵심 원리** | Full Cell 전압 = 양극 전압 − 음극 전압 → Mass/Slip 4개 파라미터를 조절하여 실측 dVdQ와 예측 dVdQ를 최소 오차로 맞춤 |

---

## 📌 2. 화면 구성

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ┌── 입력 경로 ──────────────────────────────────────────────────────┐   │
│ │ 양극 profile 경로: [________________________]                     │   │
│ │ 음극 profile 경로: [________________________]                     │   │
│ │ 실측 profile 경로: [________________________]                     │   │
│ └──────────────────────────────────────────────────────────────────┘   │
│ ┌── SOC 범위 & Smoothing ──┐  ┌── 용량 정보 (자동 계산) ────────┐   │
│ │ 시작 기준: [7]            │  │ 셀 총용량:  [___]              │   │
│ │ 끝 기준:   [100]          │  │ 양극 총용량: [___]              │   │
│ │ Smoothing 기준: [500]     │  │ 음극 총용량: [___]              │   │
│ └──────────────────────────┘  └─────────────────────────────────┘   │
│ ┌── Fitting 파라미터 (초기치) ──────────────────────────────────────┐   │
│ │ 양극 mass: [___] □Fix    양극 Slip: [___] □Fix                  │   │
│ │ 음극 mass: [___] □Fix    음극 Slip: [___] □Fix                  │   │
│ └──────────────────────────────────────────────────────────────────┘   │
│ ┌── 실행 설정 ────────┐                                               │
│ │ 실행 횟수: [100]     │                                               │
│ │ RMS (%):   [___]     │                                               │
│ └─────────────────────┘                                               │
│ ┌── 버튼 ──────────────────────────────────────────────────────────┐   │
│ │ [초기치 Reset] [1)소재 결과 Load] [2)실험 결과 Load]              │   │
│ │ [Tab Reset]    [dVdQ 자동 Fitting 실행] [dVdQ 수동 조절]         │   │
│ └──────────────────────────────────────────────────────────────────┘   │
│ ┌─ dvdq_simul_tab (결과 표시 영역, 1200×830) ────────────────────┐   │
│ │  [탭1] [탭2] ...                                                 │   │
│ │  ┌─ 상단: Voltage Profile ─────────────────────────────────────┐ │   │
│ │  │  양극(적) / 음극(청, 우축) / 예측(녹,점선) / 실측(흑)        │ │   │
│ │  └─────────────────────────────────────────────────────────────┘ │   │
│ │  ┌─ 하단: dV/dQ 곡선 ─────────────────────────────────────────┐ │   │
│ │  │  음극 dVdQ(청) / 양극 dVdQ(적) / 예측 dVdQ(녹) / 실측 dVdQ(흑)│ │   │
│ │  └─────────────────────────────────────────────────────────────┘ │   │
│ │  NavigationToolbar (확대/축소/저장)                               │   │
│ └─────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 📌 3. 설정 패널 상세

### 3-1. 입력 경로

| 설정 | 위젯 | 설명 |
|------|------|------|
| 양극 profile 경로 | `ca_mat_dvdq_path` | 양극(Cathode) 반쪽전지 충방전 데이터 (TSV: 용량, 전압) |
| 음극 profile 경로 | `an_mat_dvdq_path` | 음극(Anode) 반쪽전지 충방전 데이터 (TSV: 용량, 전압) |
| 실측 profile 경로 | `pro_dvdq_path` | Full Cell 실측 충방전 데이터 (TSV: 용량, 전압) |

### 3-2. SOC 범위 & Smoothing

| 설정 | 위젯 | 기본값 | 설명 |
|------|------|--------|------|
| 시작 기준 | `dvdq_start_soc` | 7 | 피팅 영역 시작 SOC (%) — 저SOC 노이즈 제외 |
| 끝 기준 | `dvdq_end_soc` | 100 | 피팅 영역 종료 SOC (%) |
| Smoothing 기준 | `dvdq_full_smoothing_no` | 500 | 미분(diff) 시 period 값 — 클수록 dVdQ 곡선 부드러움 |

### 3-3. 용량 정보 (자동 계산)

| 설정 | 위젯 | 설명 |
|------|------|------|
| 셀 총용량 | `full_cell_max_cap_txt` | = max(실측 용량) — Fitting 후 자동 표시 |
| 양극 총용량 | `ca_max_cap_txt` | = max(양극 원시용량) × ca_mass — Fitting 후 자동 표시 |
| 음극 총용량 | `an_max_cap_txt` | = max(음극 원시용량) × an_mass — Fitting 후 자동 표시 |

### 3-4. Fitting 파라미터

| 파라미터 | 위젯 | Fix 체크박스 | 물리적 의미 |
|----------|------|-------------|-------------|
| 양극 mass | `ca_mass_ini` | `ca_mass_ini_fix` | 양극 활물질 질량 비율 (용량 스케일링) |
| 양극 Slip | `ca_slip_ini` | `ca_slip_ini_fix` | 양극 용량 축 이동량 (리튬 손실 등) |
| 음극 mass | `an_mass_ini` | `an_mass_ini_fix` | 음극 활물질 질량 비율 (용량 스케일링) |
| 음극 Slip | `an_slip_ini` | `an_slip_ini_fix` | 음극 용량 축 이동량 (리튬 손실 등) |

> **Fix 체크 시**: 해당 파라미터를 고정(min=max)하여 탐색 범위에서 제외

### 3-5. 실행 설정

| 설정 | 위젯 | 기본값 | 설명 |
|------|------|--------|------|
| 실행 횟수 | `dvdq_test_no` | 100 | 랜덤 파라미터 생성·평가 반복 횟수 |
| RMS (%) | `dvdq_rms` | — | 최적 Fitting 결과의 RMS 오차 (자동 표시) |

---

## 📌 4. 조작 순서 (SOP)

### Step 1: 소재 데이터 로드
- **[1) 소재 결과 Load]** 클릭
- 양극 Profile → 음극 Profile 순서로 파일 선택 대화상자 표시
- TSV 형식 (탭 구분, 2열: 용량/전압)

### Step 2: 실험 데이터 로드
- **[2) 실험 결과 Load]** 클릭
- Full Cell 실측 Profile 파일 선택
- TSV 형식 (탭 구분, 2열: 용량/전압)
- 파일명에 `mAh` 포함 시 정격용량 자동 추출 (예: `4565mAh`)

### Step 3: 분석 조건 설정
- SOC 범위(시작/끝 기준), Smoothing 기준 확인
- 실행 횟수 설정 (기본 100회, 정밀도 필요 시 증가)
- 초기치는 자동 계산되지만, 경험값이 있으면 직접 입력 가능

### Step 4: 자동 Fitting 실행
- **[dVdQ 자동 Fitting 실행]** 클릭
- 진행률이 ProgressBar에 표시됨
- 완료 시: 그래프 + 파라미터 + RMS 자동 갱신

### Step 5: 반복 Fitting (수렴 향상)
- 같은 **[dVdQ 자동 Fitting 실행]** 버튼을 재클릭
- 탐색 범위가 자동 축소 (fittingdegree × 1.2)
- RMS가 개선될 때까지 반복 (3~5회 권장)
- 특정 파라미터 확정 시 **□Fix** 체크 후 재실행

### Step 6: 수동 조절 (선택사항)
- 파라미터를 직접 수정 후 **[dVdQ 수동 조절]** 클릭
- 입력된 값 그대로 시뮬레이션하여 즉시 결과 확인
- fittingdegree와 min_rms가 리셋됨

### Step 7: 결과 확인 및 저장
- `dvdq_simul_tab`에 그래프 탭이 추가됨
  - 상단: Voltage Profile (양극/음극/예측/실측)
  - 하단: dV/dQ 곡선 비교
  - 제목에 최적 파라미터(ca_mass, ca_slip, an_mass, an_slip, rms%) 표시
- **saveok** 체크 시: Excel 파일 저장 대화상자 → parameter + dvdq 시트 저장

---

## 📌 5. 버튼별 기능 상세

| 버튼 | 함수 | 동작 |
|------|------|------|
| **초기치 Reset** | `dvdq_ini_reset_button` | 4개 파라미터(mass/slip) 입력란 초기화, fittingdegree=1, min_rms=∞ |
| **1) 소재 결과 Load** | `dvdq_material_button` | 양극 → 음극 순서로 파일 선택 → 경로 표시 |
| **2) 실험 결과 Load** | `dvdq_profile_button` | 실측 Full Cell 파일 선택 → 경로 표시 |
| **Tab Reset** | `tab_delete(dvdq_simul_tab)` | 결과 탭 전체 삭제 |
| **dVdQ 자동 Fitting 실행** | `dvdq_fitting_button` | 랜덤 탐색 기반 자동 Fitting 실행 (상세: §6) |
| **dVdQ 수동 조절** | `dvdq_fitting2_button` | 현재 입력된 파라미터로 즉시 시뮬레이션·그래프 표시 |

---

## 📌 6. 데이터 흐름

```
[1)소재 결과 Load] → 양극/음극 TSV 파일 선택
     │                  (용량, 전압 2열)
     ▼
[2)실험 결과 Load] → 실측 Full Cell TSV 파일 선택
     │                  (용량, 전압 2열)
     ▼
[dVdQ 자동 Fitting 실행]
     │
     ├─ 초기값 설정
     │   ├─ 빈 칸 → 자동 계산: mass = 셀용량/소재용량, slip = 1
     │   └─ 값 있음 → 기존치 사용
     │
     ├─ 탐색 범위 결정 (fittingdegree 기반)
     │   ├─ mass: ±10%/fittingdegree
     │   ├─ slip: ±(셀용량 × 5%/fittingdegree)
     │   └─ Fix 체크 → min=max (고정)
     │
     ├─ 랜덤 탐색 (N회 반복)
     │   ├─ generate_params() → uniform 분포 랜덤 4파라미터
     │   ├─ generate_simulation_full()
     │   │   ├─ 양극: ca_cap_new = ca_cap × ca_mass − ca_slip
     │   │   ├─ 음극: an_cap_new = an_cap × an_mass − an_slip
     │   │   ├─ 0.1 간격 보간 (np.interp)
     │   │   ├─ 예측 전압 = 양극전압 − 음극전압
     │   │   ├─ SOC 변환: cap/rated_cap × 100
     │   │   └─ dV/dQ 계산: diff(periods=smoothing) / diff(periods=smoothing)
     │   ├─ SOC 범위 필터 (시작~끝 기준)
     │   ├─ RMS = √(mean((예측dVdQ − 실측dVdQ)²))
     │   └─ min_rms 갱신 시 → 파라미터/UI 업데이트
     │
     ├─ [결과 없을 때 → dvdq_fitting2_button 자동 호출]
     │
     ▼
dvdq_graph() → matplotlib Figure 생성
     │
     ├─ 상단 (ax1): Voltage Profile
     │   ├─ 양극 전압 (적색)
     │   ├─ 음극 전압 (청색, 우축 0~1.5V)
     │   ├─ 예측 전압 (녹색 점선)
     │   └─ 실측 전압 (흑색)
     │
     ├─ 하단 (ax2): dV/dQ 곡선
     │   ├─ 음극 dVdQ (청색)
     │   ├─ 양극 dVdQ (적색)
     │   ├─ 예측 dVdQ (녹색 점선)
     │   └─ 실측 dVdQ (흑색)
     │
     ├─ suptitle: 4파라미터 + RMS(%) 표시
     │
     ▼
dvdq_simul_tab에 새 탭으로 추가
     │
     └─ [saveok 체크 시] → Excel 저장
         ├─ sheet "parameter": [ca_mass, ca_slip, an_mass, an_slip]
         └─ sheet "dvdq": simul_full 전체 DataFrame
```

---

## 📌 7. Fitting 알고리즘 상세

### 7-1. 자동 Fitting 메커니즘

| 단계 | 설명 |
|------|------|
| **1. 초기치 산출** | mass = 셀 총용량 ÷ 소재 총용량, slip = 1 (비어있을 때) |
| **2. 범위 축소** | fittingdegree를 매 실행마다 ×1.2 → 탐색 범위 자동 수렴 |
| **3. 랜덤 탐색** | `np.random.uniform`으로 N회 파라미터 조합 생성 |
| **4. RMS 비교** | 지정 SOC 범위 내에서 예측·실측 dVdQ의 RMS 계산 |
| **5. 최적 갱신** | RMS가 기존 최적보다 작을 때만 갱신 |
| **6. Fallback** | min_params 없으면(갱신 실패) → `dvdq_fitting2_button` 호출 |

### 7-2. 수동 조절

| 항목 | 설명 |
|------|------|
| **동작** | 현재 UI에 입력된 4개 파라미터 값으로 즉시 시뮬레이션 |
| **리셋** | fittingdegree=1, min_rms=∞ 초기화 후 실행 |
| **용도** | 경험치 기반 미세 조정, 결과 즉시 확인용 |

### 7-3. 핵심 수식

$$V_{full}(SOC) = V_{cathode}(SOC) - V_{anode}(SOC)$$

$$\frac{dV}{dQ}\bigg|_{full} = \frac{dV}{dQ}\bigg|_{cathode} - \frac{dV}{dQ}\bigg|_{anode}$$

$$cap_{cathode,new} = cap_{cathode} \times mass_{ca} - slip_{ca}$$

$$cap_{anode,new} = cap_{anode} \times mass_{an} - slip_{an}$$

$$RMS = \sqrt{\frac{1}{N}\sum_{i=1}^{N}\left(\frac{dV}{dQ}\bigg|_{predicted,i} - \frac{dV}{dQ}\bigg|_{measured,i}\right)^2}$$

---

## 📌 8. 입력 데이터 형식

### TSV 파일 포맷 (탭 구분, 헤더 없음)

| 파일 | 1열 | 2열 | 비고 |
|------|-----|-----|------|
| **양극 Profile** | 용량 (mAh) | 전압 (V) | 반쪽전지 충방전 결과 |
| **음극 Profile** | 용량 (mAh) | 전압 (V) | 반쪽전지 충방전 결과 |
| **실측 Profile** | 용량 (mAh) | 전압 (V) | Full Cell 충방전 결과 |

> 파일명에 `mAh` 포함 시 (예: `Cell_4565mAh_25deg.tsv`) → 정격용량 자동 추출하여 SOC(%) 환산에 사용  
> 미포함 시 기본 100을 적용

---

## 📌 9. 그래프 레이아웃 요약

| 영역 | 축 | 곡선 | 색상 | Y축 범위 |
|------|-----|------|------|---------|
| **상단 Voltage Profile** | ax1 (좌) | 양극 전압 | 적색 (실선) | 2.0 ~ 4.6 V |
|  | ax1 (좌) | 예측 Full 전압 | 녹색 (점선) | 2.0 ~ 4.6 V |
|  | ax1 (좌) | 실측 Full 전압 | 흑색 (실선) | 2.0 ~ 4.6 V |
|  | ax1_right (우) | 음극 전압 | 청색 (실선) | 0 ~ 1.5 V |
| **하단 dV/dQ** | ax2 | 음극 dVdQ | 청색 | −0.02 ~ 0.02 |
|  | ax2 | 양극 dVdQ | 적색 | −0.02 ~ 0.02 |
|  | ax2 | 예측 dVdQ | 녹색 (점선) | −0.02 ~ 0.02 |
|  | ax2 | 실측 dVdQ | 흑색 | −0.02 ~ 0.02 |

- X축: SOC (%) — 눈금 −5 ~ 105, 23분할 (5% 간격)
- suptitle: `ca_mass:__, ca_slip:__, an_mass:__, an_slip:__, rms(%):__`

---

## 📌 10. 주의사항

| 항목 | 설명 |
|------|------|
| **파일 순서** | 소재 Load 시 양극 → 음극 순서로 2번 연속 파일 선택 필요 |
| **반복 Fitting** | 1회 실행으로 최적해 미도달 → 3~5회 반복 클릭하여 수렴 (fittingdegree 자동 감소) |
| **Fix 활용** | 확정된 파라미터에 체크하면 나머지 파라미터만 탐색 → 수렴 속도 향상 |
| **초기치 Reset** | 새로운 셀 분석 시 반드시 Reset 후 시작 (이전 fittingdegree 잔존 주의) |
| **Smoothing 기준** | 값이 클수록 dVdQ 곡선이 부드러워짐, 너무 크면 특징 피크가 소실될 수 있음 |
| **SOC 범위** | 시작 기준 7% — 저SOC 영역 노이즈/비선형 구간 제외 목적 |
| **용량 자동 추출** | 파일명 내 `mAh` 앞 숫자를 정규식으로 추출 (예: `4565mAh` → 4565.0) |
| **saveok 체크** | Fitting 완료 후 Excel 저장 → parameter 시트 + dvdq 시트 |
| **결과 미갱신 시** | 랜덤 탐색에서 기존 RMS 미달 → 자동으로 수동 조절(dvdq_fitting2) 호출 |
| **Tab Reset** | 결과 탭 전체 삭제 — 메모리 해제 및 새 분석 준비 |
