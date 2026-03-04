# BatteryDataTool - 세트 결과 탭 SOP
### Battery Status Log 및 ECT(ChemBatt) 결과 분석

---

## 📌 1. 탭 개요

| 항목 | 내용 |
|------|------|
| **탭 이름** | 세트 결과 |
| **목적** | 세트(단말기) 로그 데이터를 기반으로 Battery Status / ECT(전기화학 트윈) 결과를 시각화·분석 |
| **데이터 소스** | Battery Status CSV, Battery Dump 폴더, ECT(ChemBatt) 앱 로그 (.txt) |
| **분석 항목** | 충방전 Profile, Cycle 수명, SOC 정확도, Short 검출, SOH, Anode Potential 등 |

---

## 📌 2. 화면 구성

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ┌── 용량기준 (mAh) ──┐  ┌── ECT 세팅 관련 ────────────────────────────┐ │
│ │ [4565]              │  │ Max_capacity (SOC→용량 환산): [___]         │ │
│ └────────────────────┘  │ SET off 전압 기준 (45s Avg, V): [___]       │ │
│ ┌── Max Cycle ───────┐  │                                              │ │
│ │ [0]                 │  │ SOC 오차 Max: [___]    SOC 오차 Avg: [___]  │ │
│ └────────────────────┘  │ ECT SOC 오차 Max: [___] ECT SOC 오차 Avg: [___]│
│ ┌── Cycle 세팅 관련 ──┐  └──────────────────────────────────────────────┘ │
│ │ ○ 실제 사이클       │                                                  │
│ │ ● 보정사이클         │  Battery Log 결과 확인    ECT(ChemBatt) 결과 확인│
│ │ X축 최대: [0]       │  ┌──────────────────┐ ┌──────────────────┐      │
│ │ ○ 전체 사이클       │  │  Tab Reset       │ │  ECT SOC         │      │
│ │ ● 최근 사이클 [20]  │  ├──────────────────┤ ├──────────────────┤      │
│ │ ○ 지정 사이클 [0 0] │  │Battery Dump Prof.│ │  ECT Short       │      │
│ └────────────────────┘  ├──────────────────┤ ├──────────────────┤      │
│                          │Battery Status Prof│ │  ECT profile     │      │
│                          ├──────────────────┤ ├──────────────────┤      │
│                          │Battery Status Cyc.│ │  ECT cycle       │      │
│                          ├──────────────────┤ ├──────────────────┤      │
│                          │                  │ │  ECT log         │      │
│                          │                  │ │  ECT log vs App  │      │
│                          └──────────────────┘ └──────────────────┘      │
│  ┌─ set_tab (결과 표시 영역) ─────────────────────────────────────────┐  │
│  │  [탭1] [탭2] ...  (각 분석 결과가 탭으로 추가됨)                    │  │
│  │                                                                     │  │
│  │  matplotlib FigureCanvas + NavigationToolbar                        │  │
│  │  (확대/축소/저장 가능)                                               │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 📌 3. 설정 패널 상세

### 3-1. 공통 설정

| 설정 | 위젯 | 기본값 | 설명 |
|------|------|--------|------|
| 용량기준 (mAh) | `SetMincapacity` | 4565 | 용량 판정 기준치 |
| Max Cycle | `SetMaxCycle` | 0 | 데이터 로드 후 자동 설정됨 |

### 3-2. Cycle 세팅 관련 (`gCyclesetting`)

| 라디오 버튼 | 위젯 | 설명 |
|-------------|------|------|
| **실제 사이클** | `realcyc` | 로그에 기록된 그대로 사이클 사용 |
| **보정사이클** (기본) | `resetcycle` | 충전↔방전 전환점 기준으로 사이클 재산출 |
| **전체 사이클** | `allcycle` | 전체 범위 표시 |
| **최근 사이클** (기본) | `recentcycle` + `recentcycleno` (20) | 최근 N 사이클만 표시 |
| **지정 사이클** | `manualcycle` + `manualcycleno` (0 0) | 시작~끝 또는 개별 사이클 지정 |
| X축 최대 | `setcyclexscale` (0) | Cycle 그래프 X축 최대 (0=자동) |

### 3-3. ECT 세팅 관련 (`groupBox`)

| 설정 | 위젯 | 설명 |
|------|------|------|
| Max_capacity | `socmaxcapacity` | SOC→용량 환산 결과 (자동 표시) |
| SET off 전압 기준 | `setoffvoltage` | 45초 평균 전압 기준, 방전 종료 판정 (V) |
| SOC 오차 Max/Avg | `socerrormax` / `socerroravg` | SOC vs SOCref 오차 (자동 표시) |
| ECT SOC 오차 Max/Avg | `ectsocerrormax` / `ectsocerroravg` | SOCect vs SOCref 오차 (자동 표시) |

---

## 📌 4. 조작 순서 (SOP)

### Step 1: 설정값 확인/입력
- 용량기준(mAh), Cycle 세팅 옵션, ECT off 전압 기준 등을 확인

### Step 2: 원하는 분석 버튼 클릭
- 좌측 열 = **Battery Log** 계열 (세트 Battery Status 원시 로그)
- 우측 열 = **ECT(ChemBatt)** 계열 (전기화학 트윈 앱 로그)

### Step 3: 파일/폴더 선택 대화상자
- 각 버튼마다 파일 또는 폴더 선택 (복수 파일 지원)

### Step 4: 결과 확인
- `set_tab`에 그래프 탭이 추가됨 (toolbar로 확대/저장 가능)
- 필요 시 **Tab Reset** 으로 결과 탭 전체 초기화

---

## 📌 5. 버튼별 기능 상세

### 5-1. Battery Log 계열 (좌측)

| 버튼 | 함수 | 입력 | 그래프 구성 |
|------|------|------|------------|
| **Tab Reset** | `set_tab_reset_button` | — | set_tab 내 모든 탭 삭제 |
| **Battery Dump Profile** | `set_log_confirm_button` | 폴더 선택 (battery_dump) | 5×1: CCV/OCV, Curr, SOC/rawSOC, 4종 Temp, Cap_max |
| **Battery Status Profile** | `set_confirm_button` | 파일 선택 (복수) | 5×2: 충전(좌)·방전(우) — Vol, Curr, Temp, SOC, realSOC |
| **Battery Status Cycle** | `set_cycle_button` | 폴더 선택 | 1×2: ASOC1/BSOH/ASOC3 비율 + Full Cap Nom/Rep 용량 |

### 5-2. ECT(ChemBatt) 계열 (우측)

| 버튼 | 함수 | 입력 | 그래프 구성 |
|------|------|------|------------|
| **ECT SOC** | `ect_soc_button` | 파일 선택 (복수) | 4×2: 좌(Vol/AnodeE/Curr/Temp) + 우(ECT SOC 비교/SOC Error/SOCref vs Error) |
| **ECT Short** | `ect_short_button` | 파일 선택 (복수) | 7×2: 좌(Cyc/Vol/AnodeE/Curr/Temp/ECT ASOC/SOC) + 우(Short Value/V acc/V avg/Score/I/Grade/R) |
| **ECT profile** | `ect_set_profile_button` | 파일 선택 (복수) | 5×2: 충전(좌)·방전(우) — Vol/AnodeE/CurrAvg/Temp/SOC+SOCect + LUT 전압 가이드 |
| **ECT cycle** | `ect_set_cycle_button` | 폴더 선택 | 2×3: SOH+SOH_CA / SOH_dR / SC_SCORE / SOH_X / LUT_VOLT(4step) / SC_VALUE |
| **ECT log vs App** | `ect_set_log_button` | 폴더 선택 (복수) | 5×2: 좌(App vs log: Vol/Curr/Temp/SOC/AnodeE) + 우(차이값 delta) |
| **ECT log** | `ect_set_log2_button` | 폴더 선택 (복수) | 5×2: 좌(Vol+LUT/Curr+ISD/Temp/SOC계열/AnodeE) + 우(SOH_dR/SOH+SOH_CA/SOH_X/ISD Value+Score/ISD R) |

---

## 📌 6. 데이터 흐름

```
[버튼 클릭] → 파일/폴더 선택 대화상자
     │
     ├─ Battery Log 계열:
     │   CSV 파일 → pd.read_csv → 컬럼 파싱
     │   ├─ Profile 계열: 사이클별 충/방전 분리 → graph_set_profile()
     │   └─ Cycle 계열: 중복 제거·정렬 → graph_cycle()
     │
     └─ ECT 계열:
         ect_data() 공통 전처리:
         ├─ CSV 로드 (skiprows=1)
         ├─ 컬럼 정규화 (특수문자 제거)
         ├─ 25개 핵심 컬럼 추출 (Vol,Curr,Temp,SOC,AnodeE,Short...)
         ├─ 시간 변환 (datetime → 경과시간 hr)
         ├─ 타입 변환 (float/int)
         └─ 보정사이클 적용 (충전↔방전 전환점 cumsum)
     │
     ▼
matplotlib figure 생성 → FigureCanvas + Toolbar
     │
     ▼
set_tab에 새 탭으로 추가 (탭 이름 = 파일/폴더명)
     │
     ├─ [saveok 체크 시] → pd.ExcelWriter → .xlsx 저장
     └─ [figsaveok 체크 시] → output_fig() → 그래프 이미지 저장
```

---

## 📌 7. ECT 데이터 컬럼 참조

### ECT 앱 로그 주요 컬럼 (ChemBatt_LOG)

| 인덱스 | 컬럼명 | 설명 |
|--------|--------|------|
| 0 | Time | 타임스탬프 |
| 1 | voltage_now(mV) | 현재 전압 |
| 4 | Current Avg. | 평균 전류 |
| 5 | Level | 배터리 레벨(SOC) |
| 14 | Temperature(BA) | 배터리 온도 |
| 23 | ectSOC | ECT 산출 ASOC |
| 24 | RSOC | ECT RSOC |
| 25 | SOC_RE | ECT 보정 SOC |
| 27 | SOH | 건강상태 |
| 28 | AnodePotential | 음극 전위 |
| 29~31 | SOH_dR/CA/X | SOH 세부(저항/용량/매스밸런스) |
| 32~35 | SC_VALUE/SCORE/V_Acc/V_Avg | Short 검출 관련 |
| 36~39 | LUT_VOLT0~3 | 충전 Cutoff 전압 (4단계) |

### Battery Status 로그 주요 컬럼

| 인덱스 | 컬럼명 | 설명 |
|--------|--------|------|
| 0 | Time | 타임스탬프 |
| 1 | Level | 배터리 SOC |
| 2 | Charging | 충전 상태 |
| 3 | Temperature(BA) | 배터리 온도 |
| 6 | Voltage(mV) | 전압 |
| 20 | Battery_Cycle | 배터리 사이클 |
| 34 | Current Avg. | 평균 전류 |
| 35 | ASOC1 | ASOC 값1 |
| 37 | ASOC2 | ASOC 값2 |
| 47 | BSOH | 배터리 SOH |

---

## 📌 8. 그래프 레이아웃 요약

| 기능 | 레이아웃 | 핵심 표시 항목 |
|------|---------|---------------|
| Battery Dump Profile | 5×1 | CCV+OCV / Curr / SOC+rawSOC / 4종 Temp / Cap_max |
| Battery Status Profile | 5×2 | 충전(좌)·방전(우): Vol / Curr / Temp / SOC / realSOC |
| Battery Status Cycle | 1×2 | ASOC1+BSOH+ASOC3 비율 / Full Cap Nom+Rep 용량 |
| ECT SOC | 4×2 | Vol+Vavg·AnodeE·Curr·Temp / ECT SOC비교·SOC+SOCect+SOCref·Error·SOCref-Error |
| ECT Short | 7×2 | Cyc·Vol·AnodeE·Curr·Temp·ECT ASOC·SOC / Short Value·Vacc·Vavg·Score·I·Grade·R |
| ECT Profile | 5×2 | 충전(좌)·방전(우): Vol+LUT·AnodeE·CurrAvg·Temp·SOC+SOCect |
| ECT Cycle | 2×3 | SOH+SOH_CA / SOH_dR / SC_SCORE / SOH_X / LUT_VOLT / SC_VALUE |
| ECT log vs App | 5×2 | App(좌) vs Log(좌) 비교 / 우측=차이(delta) |
| ECT log | 5×2 | Vol+LUT·Curr+ISD·Temp·SOC계열·AnodeE / SOH_dR·SOH·SOH_X·ISD Value·ISD R |

---

## 📌 9. 주의사항

| 항목 | 설명 |
|------|------|
| **보정사이클** | 기본 선택 — Charging↔Discharging 전환점에서 사이클 재산출 (cumsum) |
| **복수 파일** | Profile 계열은 복수 파일 선택 → 파일별 탭 자동 생성 |
| **ECT log vs App** | ChemBatt_LOG + ect_inputlog + ect_outputlog 3종 파일이 같은 폴더에 필요 |
| **ECT log** | ect_inputlog + ect_outputlog 2종 파일 필요 (출력 헤더 24/25 컬럼 자동 감지) |
| **SET off 전압** | ECT SOC 분석 시 방전 종료 전압 기준 설정 (45초 이동평균 기준) |
| **SOC 오차** | ECT SOC 버튼 실행 후 자동 계산 → Max/Avg 위젯에 표시 |
| **saveok 체크** | 체크 시 Excel (.xlsx) 파일로 원시 데이터 내보내기 |
| **figsaveok 체크** | 체크 시 그래프 이미지 자동 저장 |
| **Tab Reset** | set_tab 내 모든 결과 탭 제거 (메모리 해제) |
