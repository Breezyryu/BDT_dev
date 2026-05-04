---
title: "AI TF 배터리 용어집 — SBP 카테고리 (v1)"
tags: [AI_TF, glossary, terminology, SBP, BMS, FGIC, SOC, SOH, CSD, ISD, SBA, EDV, NVT, SDI, ADI, TI]
type: reference
status: active
aliases:
  - AI TF SBP 용어
  - SBP 알고리즘 용어집 — BMS 파트
  - Smart Battery Pack Glossary
related:
  - "[[AI_TF_Glossary_Simulation]]"
  - "[[Fuel_Gauge_IC_Architectures]]"
  - "[[!용어]]"
  - "[[MOC_Battery_Knowledge]]"
  - "[[Summary_AI_Tech_Stack]]"
  - "[[Empirical_Degradation_Models]]"
  - "[[Knee_point]]"
scope: "AI TF 배터리 용어 정리 활동의 SBP(Smart Battery Pack) 카테고리 — NVT/SDI/ADI/TI 4개 IC 벤더 알고리즘 비교 자료(SBP_알고리즘비교_Ver2.1.pptx) 기반. 14개 그룹 137개 항목."
source_tsv: "Downloads/SBP알고/용어_SBP_v1.txt"
source_origin: "Downloads/SBP알고/SBP_알고리즘비교_Ver2.1_bundle.txt (44 slides) + 31 PNG slide captures"
created: 2026-05-04
updated: 2026-05-04
---

# AI TF 배터리 용어집 — SBP

> SBP(Smart Battery Pack)에 탑재되는 BMS 알고리즘 용어 정리. **NVT(Nuvoton) / SDI(Samsung SDI) / ADI(Analog Devices) / TI(Texas Instruments)** 4개 IC 벤더의 SOC, SOH, Cell Swelling Detection (CSD), Internal Short Detection (ISD), Silicon Battery Algorithm (SBA), Dynamic EDV, R-Table, SOC Smoothing 알고리즘 비교 자료에서 추출.
>
> Fuel Gauge IC 회로 아키텍처는 [[Fuel_Gauge_IC_Architectures]], 배터리 모델·시뮬레이션 용어는 [[AI_TF_Glossary_Simulation]] 참조. 일반 용어는 [[!용어]].

## 📑 14개 그룹 빠른 이동

| # | 그룹 | 항목 |
|---|---|---|
| 1 | SBP / IC 일반 | 10 |
| 2 | SOC 변수 (벤더별) | 6 |
| 3 | 용량 (Q*) 변수 (벤더별) | 15 |
| 4 | SOC 알고리즘 기법 | 9 |
| 5 | EDV / Cut-off | 7 |
| 6 | OCV 관련 | 11 |
| 7 | R-Table / 저항 | 15 |
| 8 | SOH 알고리즘 | 7 |
| 9 | **Cell Swelling Detection (CSD)** | 7 |
| 10 | **Internal Short Detection (ISD)** | 13 |
| 11 | **Silicon Battery Algorithm (SBA)** | 6 |
| 12 | Dynamic / Smart EDV | 6 |
| 13 | SOC Smoothing | 11 |
| 14 | Register · Concept | 14 |
| | **합계** | **137** |

## 🏷️ 4개 IC 벤더 변수명 매핑 (핵심만)

| 개념 | NVT | SDI | ADI | TI |
|---|---|---|---|---|
| 최대 용량 | Qmax / CellQmax / Qabs | MaxCap | FullCapNom | Qmax |
| 보고 SOC | RSOC | RSOC | RepSOC | RSOC |
| 내부 변수 | ASOC, AvSOC | — | VFSOC | TrueSOC |
| Mixing | (해당 없음) | (해당 없음) | Mixing Algorithm + Servo Mixing | (해당 없음) |
| Qmax 갱신 | 2-point OCV + FastOcvQmax | 2-point OCV | 2-point OCV (Q_Max1 = ΔQ / abs(VFSOC1−VFSOC2)) | 2-point OCV + Fast Qmax + Cycle Adjust |
| R-Table | Ra Table 16점 + Differential Pressure | ESR (Ra-table 직결) | RComp0 / nXTable / TempCo / QRTable | Ra Table 15점 + Rb Table (온도) + Fast R Scaling |
| CSD | CSD 1.5/2.0 (3-factor) | ESR↑ + High-T/SOC time | — | — |
| ISD | CIS 3.0/4.0 (CCP) + SVK | 적산 용량 ISC (ΔAh_CCM−ΔAh_ISC) | — | — |
| SBA | Si Loss + 3.6 V peak | Partial Hysteresis (40% 임계) | — | — |
| Smoothing | 40 sec 0% 수렴 | — | Converge-to-Empty (RepLow/VoltLowOff/MinSlopeX) | 99% Hold + Term Smooth Time |

## 🔗 다른 카테고리와의 분리

본 SBP 카테고리는 다음과 차별화 처리:

- **DCIR / ACIR / ESR**: '성능/상태 지표'·'시뮬레이션' 카테고리 정의는 일반 개념, 본 카테고리는 SBP/SOH 2.0·CSD 활용 맥락
- **EKF (SBP)**: '시뮬레이션' 카테고리의 Extended Kalman Filter 일반 정의를 NVT의 SOC 추정 적용 맥락으로 한정
- **dV/dQ 분석 (SBA)**: '분석/측정' 카테고리의 dQ/dV 분석과 미분 방향이 다름. SBA Si Loss 추출에 사용
- **OCV Hysteresis**: SBA 보상 메커니즘으로 한정 (일반 hysteresis는 '안전성/열화')

---

## 1. SBP / IC 일반

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| SBP (스마트 배터리 팩) | Smart Battery Pack |  | 셀에 게이지 IC(FGIC)와 보호 IC(AFE)를 일체화하여 SOC/SOH·안전 진단을 자체 수행하고 호스트와 SMBus/I2C로 통신하는 IT 기기용 배터리 팩. | 셀 단위 정밀 추정·진단 가능. | 셀·IC·펌웨어 검증 비용 증가. |
| 연료게이지 IC | Fuel Gauge IC | FGIC, Gas Gauge IC | V/I/T를 측정하는 ADC와 SOC·SOH·CSD·ISD 추정 펌웨어를 탑재한 게이지 칩. SBP의 두뇌. | 측정 정밀도와 알고리즘 채택이 추정 성능을 결정. | 칩 선정이 제품 사이클을 좌우. |
| 아날로그 프론트엔드 | Analog Front End (AFE) |  | 셀 전압·전류 측정과 1차 보호(과충전·과방전·과전류·과온)를 담당하는 보호 IC. FGIC와 함께 SBP를 구성. |  |  |
| 스마트 배터리 사양 | Smart Battery Specification (SBS) |  | SBP가 호스트와 교환하는 표준 레지스터·통신 사양. SMBus 위에서 동작. |  | 벤더별 확장 레지스터로 호환성 차이 발생. |
| NVT | Nuvoton | 노바텍 (구 Novatek) | 대만 IC 벤더. SBP 게이지에 EKF + EDV simulation 기반 SOC, 2-point OCV Qmax 기반 SOH 1.0/2.0, CSD 1.5/2.0, CIS 3.0/4.0 알고리즘을 탑재. |  |  |
| SDI | Samsung SDI |  | 자체 게이지 IC와 알고리즘. 2-point OCV 기반 SOC/SOH, ESR-증가율 + 고온/High-SOC 시간 기반 CSD, 적산 용량 기반 ISD. |  |  |
| ADI | Analog Devices | (구 Maxim Integrated) | VFSOC + Mixing Algorithm + Empty Compensation 구조의 게이지 IC. RepCap/FullCapRep/MixCap 변수 체계. |  |  |
| TI | Texas Instruments | bq시리즈 | bq 게이지 IC. RM = Qmax × (DODfinal − DODstart) 기반 SOC, OCV prediction · Fast Qmax update · Fast Resistance Scaling 지원. |  |  |
| MPC7011C | MPC7011C |  | NVT의 Built-in EIS 지원 신세대 게이지 IC. SOH 2.0과 CSD에 임피던스 활용. |  |  |
| SMBus / I2C / HDQ | SMBus / I2C / HDQ |  | SBP 호스트-게이지 IC 간 통신 버스 규격. SBS 위에서 동작. |  |  |

## 2. SOC 변수 (벤더별)

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| RSOC | Relative State-of-Charge |  | 사용자에게 보고되는 0~100% 잔량. RSOC = RM / FCC. 호스트 UI 표시값. |  |  |
| ASOC | Absolute State-of-Charge |  | Designed Capacity 기준 절대 잔량(%). NVT가 내부 변수로 사용. |  |  |
| AvSOC | Available SOC |  | 부하·온도 보정 EDV simulation으로 EDV 도달까지 사용 가능한 SOC. NVT의 RSOC 산출 중간 단계. |  |  |
| VFSOC | Voltage Fuel-gauge SOC |  | OCV→SOC 환산 추정값. ADI의 mixing 입력 및 End-of-charge detection 게이트로 사용. |  |  |
| TrueSOC | True SOC |  | TI 게이지의 실 SOC 추정값. Smoothing 적용 전 단계. |  |  |
| RepSOC | Reported SOC |  | ADI 게이지가 호스트에 보고하는 RSOC. RepCap / FullCapRep로 산출. |  |  |

## 3. 용량 (Q*) 변수 (벤더별)

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| Qmax | Maximum Capacity |  | 셀이 가용한 최대 용량(완충~완방, Ah). 2-point OCV로 갱신. | SOH의 핵심 입력. | Flat region 회피 등 갱신 조건이 까다로움. |
| Qrelax | Qrelax (NVT) |  | NVT — 휴지 후 측정된 OCV에서 ASOC를 환산해 산출한 잔여 용량. Qrelax = Qmax × (ASOCEOC − ASOC0). |  |  |
| Qstart | Qstart (TI) |  | TI — 30분 휴지 후 매 100 sec OCV 측정으로 DOD를 환산해 산출한 방전 시작 시점 용량. |  |  |
| RM | Remaining Capacity |  | 현재 시점에 남은 가용 용량(Ah). EDV simulation 결과로 산출. |  |  |
| FCC | Full Charge Capacity |  | 현 SOH 기준의 완충 용량. FCC = RM + PassedCharge + Q_start/relax. |  |  |
| PassedCharge | Passed Charge |  | 방전 중 적산된 전류량(Ah). CCM 누적 결과. |  |  |
| MixCap | MixCap (ADI) |  | ADI — OCV estimation과 CCM의 가중 합산 용량. Power-on reset 직후 OCV-dominant. |  |  |
| AvCap | AvCap (ADI) |  | ADI — MixCap에 부하·온도 Empty Compensation 적용한 가용 용량. |  |  |
| RepCap | RepCap (ADI) |  | ADI — AvCap의 jump 방지를 위한 필터링 후 보고 용량. |  |  |
| FullCapRep | FullCapRep (ADI) | Application Capacity | ADI — End-of-charge detection으로 갱신되는 application 표시 용량. |  |  |
| FullCapNom | FullCapNom (ADI) |  | ADI — 2-point OCV 기반 nominal full capacity. Q_Max1 = ΔQ / \|VFSOC1 − VFSOC2\|. |  |  |
| CellQmax | CellQmax (NVT) |  | NVT — 10 cycle 마다 평균한 Qmax. SOH_FCC 입력. |  |  |
| Qabs | Qabs (NVT) |  | NVT — OCV 2-point 측정 기반 즉시 Qmax. dSOC ≥ 37% 또는 dSOC ≥ 90% 만족 시 매 순간 갱신. |  |  |
| SOH_FCC | SOH-FCC (NVT) |  | NVT — SOH 산출용 FCC. (ASOCEOC − ASOCEDV) × Qmax. SOH = SOH_FCC / Cell Designed Capacity. |  |  |
| MaxCap | MaxCap (SDI) |  | SDI — Qmax에 해당하는 SDI 변수. MaxCap = ΔQ / (SOC2 − SOC1). SOH = MaxCap × (SOC@eoc − SOC@eod) / Designed Capacity. |  |  |

## 4. SOC 알고리즘 기법

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| 쿨롱 카운팅 | Coulomb Counting Method (CCM) |  | 전류 적산 ∫I dt 로 사용 용량을 추정. 단기 정확하나 누적 오차로 OCV 보정과 결합 필요. | 실시간성 우수. | 센서 오차·드리프트 누적. |
| OCV 추정 | OCV Estimation | Voltage Fuel Gauge | V_terminal − I·R_SS = OCV 형태로 OCV를 추정. ADI mixing 입력. (OCV 산출 방법은 비공개) |  |  |
| EDV 시뮬레이션 | EDV Simulation | Empty Compensation | 현재 부하·온도에서 V = OCV(DOD,T) − I·Ra(DOD,T) 식으로 미래 단자 전압을 모사하여 EDV 도달 시점의 DOD/SOC를 RM 산출에 사용. NVT/TI/ADI 공통. |  |  |
| Mixing 알고리즘 | Mixing Algorithm |  | ADI — OCV estimation과 CCM의 가중 합산. 0~2 cycle: OCV→CCM dominant 천이(지수함수), 2 cycle 이후: Servo mixing. |  |  |
| Servo Mixing | Servo Mixing |  | ADI — 2 cycle 이후 적용. CCM 단독 + 고정된 적산 오차값 보정 + OCV estimation error 부호로 보정 방향 결정. |  |  |
| End-of-Charge Detection | End-of-Charge Detection | EoC Detection | ADI — VFSOC > FullSOCThr ∧ IChgTerm × 0.125 < I < IChgTerm × 1.25 ∧ AvgCurrent 동일 윈도우 만족 시 FullCapRep을 적산 결과로 갱신. |  |  |
| Empty Compensation | Empty Compensation |  | ADI — MixCap → AvCap 변환을 위한 부하·온도 보정. EDV simulation의 ADI 명칭. |  |  |
| Power-on Reset | Power-on Reset (POR) |  | 게이지 재기동. CCM 적산 초기값 확보를 위해 Mixing ratio가 OCV-dominant로 설정됨. |  |  |
| 확장 칼만 필터 (SBP) | Extended Kalman Filter (EKF, SBP) |  | NVT — Battery model 파라미터(오프라인 + 실시간 학습) 기반 EKF로 SOC 추정. 전류 적산과 전압 보정의 혼합 형태. (시뮬레이션 카테고리의 EKF 일반 정의를 SBP에 적용) |  |  |

## 5. EDV / Cut-off

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| EDV | End-of-Discharge Voltage |  | 정해진 부하·온도에서 SOC 0%로 정의되는 단자 전압. SOC smoothing 수렴 목표이자 EDV simulation 종지값. |  |  |
| Term Voltage | Terminal Voltage / Term Voltage | TermV | 호스트가 RSOC 0%로 표시할 단자 전압 임계값. EDV와 구분하여 펌웨어 register로 관리. |  |  |
| Term Voltage Delta | Term Voltage Delta |  | Term Voltage 대비 추가 마진. Rapid Ra Update 트리거 조건(Voltage < TermV + ΔV)에 사용. |  |  |
| Taper Current | Taper Current | IChgTerm | CV 충전 종료 판정 전류. CV 모드에서 전류가 감소해 도달하는 종지값. |  |  |
| CCCV | Constant-Current Constant-Voltage Charging |  | 표준 충전 프로토콜. CC → CV 단계의 taper로 만충 판정. |  |  |
| CV Termination Condition | CV Termination Condition |  | CV 단계에서 taper current 도달 또는 전류 변화율 임계 만족 시 충전을 종료하는 조건. taper current 변화율 5 mA/30 sec 등. |  |  |
| Designed Capacity | Designed Capacity |  | 셀 설계 용량(공칭, mAh). FCC/Qmax 비교 기준이자 ΔQ 임계 비율(예: 37%, 90%)의 분모. |  |  |

## 6. OCV 관련

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| OCV-SOC 테이블 | OCV-to-SOC / OCV-to-DOD Table | OCV LUT | OCV ↔ SOC/DOD 변환 룩업. 휴지 OCV → RSOC 환산의 핵심. | 모든 게이지의 기본 LUT. | 열화·온도·hysteresis로 시간에 따라 변동. |
| OCV 히스테리시스 | OCV Hysteresis |  | 충·방전 방향에 따라 OCV 곡선이 다르게 나타나는 현상. Si 음극에서 두드러지며 SBA에서 방향별 별도 table로 보상. |  |  |
| OCV Shift | OCV Shift |  | 열화·Si Loss에 따라 OCV-SOC 곡선이 평행 이동하는 현상. Si Loss table 기반 보정. |  |  |
| OCV 예측 | OCV Prediction |  | TI — OCV 측정 조건 미충족 시 충방전·휴지 시간·휴지 전압 수집 데이터로 OCV를 외삽 추정. 사용자가 enable 가능. | 측정 미충족 환경에서도 Qmax 갱신 지속. | 외삽 오차 누적 가능. |
| 2-point OCV | 2-point OCV Method |  | 두 시점의 휴지 OCV에서 ASOC/DOD 차이를 구하고, 사이의 충·방전 적산량과 비교해 Qmax 갱신. SOH 1.0의 기본. |  |  |
| FastOcvQmax | FastOcvQmax |  | NVT — 15 min 휴지만으로 OCV를 환산해 Qmax를 갱신. dV/dt ≤ 20 µV/s, 2 hr standby. CellQmax = k1·FastOcvQmax + k2·Qmax (k1, k2는 ∆cycle 의존). | 저사용 환경에서 Qmax 갱신 빈도 확보. | 허용 dV/dt가 커져 noise 영향 증가. |
| Long Time Rest / Short Time Rest | Long Time Rest / Short Time Rest |  | Qmax 업데이트 분기 조건. dV/dt ≤ 4 µV/s + ≥ 5 hr = Long, FastOcv 적용 시 dV/dt ≤ 20 µV/s + ≥ 2 hr = Short. |  |  |
| Relaxation Condition | Relaxation Condition |  | OCV 측정 유효화 조건. dV/dt + standby time + 온도(0~80 ℃) + 전류 적산 오차(≤ 3% Designed Capacity) 등을 동시 만족. |  |  |
| Flat Region | Flat Region (No-update Zone) |  | OCV-DOD 곡선의 평탄 구간(예: 3.737~3.7 V 또는 ASOC 15~30%). OCV→SOC 환산 오차가 커서 Qmax 업데이트에서 회피. |  | LFP/Si 함량에 따라 폭이 달라짐. |
| Fast Qmax Update | Fast Qmax Update |  | TI — RSOC < 10%까지 방전한 1-OCV 측정만으로 Qmax 업데이트. ΔQ가 작을수록 가중치를 낮추는 1차 LPF 적용. |  | 외삽 영역 특성상 노이즈에 민감. |
| Cycle-based Qmax Adjustment | Cycle-based Qmax Adjustment |  | TI — 지정 Cycle까지 추가 OCV 갱신이 없으면 Qmax = Qmax × (1 − CycleAdjIncr × CycleAdjustThreshold / 10000) 식으로 감소. |  |  |

## 7. R-Table / 저항

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| DCIR | Direct Current Internal Resistance |  | DC 펄스 응답으로 측정한 내부 저항. ('성능/상태 지표' 카테고리에도 등재 — 본 항목은 SBP/SOH 2.0 활용 맥락). |  |  |
| ACIR | Alternating Current Internal Resistance |  | 특정 주파수에서 측정한 AC 내부 저항. CSD 1.5의 본래 의도(현 S27 단계에서는 DCIR 형태). |  |  |
| ESR | Equivalent Series Resistance |  | R-table에서 갱신되는 직렬 등가 저항. SDI CSD의 핵심 입력. |  |  |
| Built-in EIS | Built-in EIS |  | 게이지 IC에 통합된 EIS 임피던스 측정 모듈. NVT MPC7011C 등 신세대 칩이 지원. SOH 2.0·CSD 활용. |  | 저전류 펄스 + 고정밀 ADC 필요. |
| Ra Table | Ra Table (Resistance Table) |  | DOD 기준 저항 LUT. NVT 16점 (Ra[0]~Ra[15]), TI 15점 (Ra0~Ra14, 11.1%/3.2% 간격), ADI 12점 추정. EDV simulation의 핵심. | 저항 정확도가 EDV·RSOC 정확도를 좌우. | Cell-to-cell 변동·열화로 지속 갱신 필요. |
| Rb Table | Rb Table (Temp Coefficient Table) |  | TI — Ra의 온도 보정 계수. 사용 시 R = Ra[DOD] × exp(Rb[DOD] × T)로 변환, 저장 시 0 ℃ 기준으로 환산. |  |  |
| RComp0 | RComp0 (ADI) |  | ADI register — 단일 저항 값(모든 SOC 동일 저항 가정 추정). |  |  |
| nXTable0~11 | nXTable0~11 (ADI) |  | ADI register — DOD 12개 breakpoint 저항 table 추정. |  |  |
| TempCo | TempCo (ADI) |  | ADI register — 온도-저항 방정식 계수 저장 register 추정. |  |  |
| QRTable00~30 | QRTable00~30 (ADI) |  | ADI register — 온도 4개 breakpoint 스케일링 팩터 추정. |  |  |
| 차분 압력 업데이트 | Differential Pressure Update (Ra) |  | NVT — Qmax update 완료 ∧ CCM error < 5% Q_design ∧ V difference > 0 충족 시 Ra 갱신. 1차 LPF + Ra Max delta 제한. |  |  |
| Rapid Ra Update | Rapid Voltage Difference Update |  | NVT — RSOC ≤ Fast Scale Start SOC 또는 V < TermV + ΔV 조건 만족 시, 30 sec 마다 DeltaVScale = (ΔV_new / ΔV_old) × 1000 을 Ra에 적용. |  |  |
| Fast Resistance Scaling | Fast Resistance Scaling |  | TI — Rapid Ra Update에 대응. R Scale = (R_new / R_old) × 1000 적용. NVT의 Rapid Update와 등가. |  |  |
| Resistance Update Voltage | Resistance Update Voltage |  | TI 옵션 — 저전류 application에서 ΔV가 임계 초과 시 IR drop으로 R 갱신을 트리거. |  |  |
| 1차 저역 통과 필터 | 1st-Order Low-Pass Filter (LPF) |  | Update = new × (1 − filter) + old × filter 형식의 Ra 갱신 평활화. NVT/TI 공통. |  |  |

## 8. SOH 알고리즘

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| Delta Voltage | Delta Voltage |  | TI — 평균 전압 대비 순시 voltage drop. EDV simulation 기준 전압 = TermV + Delta Voltage. |  |  |
| SOH 1.0 | SOH 1.0 (NVT) |  | NVT — Qmax update + EDV simulation 기반 SOH(개발 완료). SOH = SOH_FCC / Cell Designed Capacity. |  |  |
| SOH 2.0 | SOH 2.0 (NVT) |  | NVT — DCIR 또는 Built-in EIS 임피던스(Z_re) 기반 SOH (26.03 완료 예정). | 저사용 환경에서도 SOH 갱신. | Z_re-Qmax 상관 모델의 셀별 보정 필요. |
| Mixing Algorithm (SOH) | Mixing Algorithm (SOH) |  | NVT — Qmax와 FastOcvQmax를 ∆cycle 의존 가중치로 합산해 CellQmax 산출. \|∆cycle\| ≤ 20: k1=k2=0.5, 외 영역에서는 0.005·\|∆cycle−20\| 비례 조정. |  |  |
| Z_re | Real Impedance (Z_re) |  | EIS 임피던스의 실수부. SOH 2.0 입력. |  |  |
| Z_re-to-Qmax Table | Z_re-to-Qmax Table |  | Z_re → Qmax 환산 LUT. SOH 2.0 핵심 LUT. |  |  |
| Empirical Lifetime Model (Corner Case 1) | Empirical Lifetime Model — Charging/Discharging without rest |  | NVT — 휴지 부재 운전에서 Q 적산을 cycle count로 환산하는 단순 모델. 26.04 도입 예정. 온도·SOC range는 미고려. |  |  |

## 9. Cell Swelling Detection (CSD)

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| High-SOC Storage Degradation Model (Corner Case 2) | High-SOC Storage Degradation Model — TA 상시 연결 |  | NVT — TA 상시 연결 시 SOC·Temperature 의존 degradation 모델. (완료 일정 미정) |  |  |
| CSD | Cell Swelling Detection |  | 셀 두께 증가(스웰링)를 게이지 IC가 비파괴적으로 진단하는 알고리즘. |  |  |
| CSD 1.5 | CSD 1.5 (NVT) |  | NVT — Floating charge 환경의 가스 스웰링 진단. 저항·저항 기울기·Stress model 3-factor 조합. |  |  |
| CSD 2.0 | CSD 2.0 (NVT) |  | NVT — Cycling/Storage 등 다양한 운전 조건의 스웰링까지 확장 (개발 진행 중). |  |  |
| Floating Charge | Floating Charge | 부동 충전 | 만충 후 충전기를 연결한 채 유지되는 충전 상태. 가스 스웰링의 주된 트리거. |  |  |
| Gas Swelling | Gas Swelling |  | 전해액 분해 등으로 발생한 가스에 의한 부피 팽창. CSD의 1차 표적. |  |  |
| Hard Swelling / Si-Swelling | Hard Swelling / Si-Swelling |  | Si 음극의 부피 팽창에 의한 영구적 두께 증가. SBA 파트에서 별도 진단 (CSD와 OR 조건). |  |  |

## 10. Internal Short Detection (ISD)

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| Stress Model (CSD) | Stress Model (CSD) |  | 온도별 floating 충전 시간을 정규화한 누적 스트레스 지표. 고온일수록 더 큰 가중치. |  |  |
| CSD 3-Factor | CSD 3-Factor (NVT) |  | 저항값·저항 기울기(또는 분산)·Stress model의 OR/AND 조합으로 알람 판정. Gr 음극과 Si 음극 별 별도 임계. |  |  |
| ESR-Increase based CSD | ESR-Increase Based CSD (SDI) |  | SDI — Ra-table에서 갱신되는 ESR의 증가율로 Si 음극 cycling 스웰링 검출. SOC 사용 영역(0~100, 10~100, 25~100, 35~100, 50~100%) 별 DOE. |  |  |
| High-T/High-SOC Storage based CSD | High-T/High-SOC Storage CSD (SDI) |  | SDI — 35/45 ℃ × 100/95/90/85% SOC DOE 기반. 정규화된 보관 시간이 임계 초과 시 알람. ESR 증가율과 AND 조건. |  |  |
| Si-Loss to Si-Swelling Correlation | Si-Loss → Si-Swelling Correlation Model |  | NVT SBA — Si 손실량과 Si 스웰링의 상관 모델. 온도/Low SOC(< 3.6 V) 패턴이 입력. 추정값 10% 도달 시 알람. |  |  |
| ISD | Internal Short Detection |  | 미세 단락(micro short)을 운전 중 검출하는 알고리즘. 안전성 1차 방어선. |  |  |
| CIS | Current Internal Short (CIS) |  | NVT의 ISD 명칭. CIS 3.0 — 오차 5 mA, CIS 4.0 — 오차 10 mA(온도 변화 ±3 ℃ 허용). |  |  |
| CCP | Cycle Characteristic Point (CCP) |  | CV 충전 중 taper current 기준으로 정의된 4개 이상의 특성 포인트. 동일 CCP 간 충방전 용량 차이로 단락 누설 추정. |  |  |
| Valid CCP | Valid CCP (VCCP) |  | 온도·시간(12 hr~10 day) 조건 만족한 CCP. 3개 이상 누적 시 ISD 진단 동작. |  |  |
| RISC | Internal Short Resistance (RISC) |  | CCP 간 용량 누설로 환산된 등가 단락 저항. median value를 대표값으로 선정. |  |  |
| IISC | Internal Short Current (IISC) |  | IISC = V_avg / RISC. 5 mA 미만 시 0 처리(RISC = ∞ = 65535). |  |  |
| ISC Flag | ISC Flag |  | 단락 검출 플래그. CCP 조건 + Elapsed time 조건 + VCCP_Flag ≥ 3 만족 시 set. |  |  |
| ISR Valid Count | ISR Valid Count |  | Lv.1 가성진단 방지 카운터. ISR 점수 누적 60점 도달 시 Lv.1 알람. ISR > 1333 또는 ≤ 200 (@4.0 V)이면 0으로 초기화. |  |  |

## 11. Silicon Battery Algorithm (SBA)

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| ISD Alarm Level | ISD Alarm Level (Lv.1/2/3) |  | ISR 범위에 따른 단계별 알람. Lv.3는 SVK가 별도 담당. |  |  |
| SVK | Rest Voltage Drop (SVK) |  | NVT — 휴지 구간(I < 50 mA, V > 3.4 V, 2 hr 이상)에서 voltage drop으로 Lv.3 (> 20 Ω) 단락 검출. CIS 4.0과 함께 26.1Q 탑재. |  |  |
| 적산 용량 ISC | Cumulative Capacity ISC (SDI) |  | SDI — 만충~만충 간 ΔAh_CCM에서 쿨롱 효율(Δah_η), 센서 오차(Δah_sen_err), masking 보정(Δah_masking)을 차감해 ΔAh_ISC 산출. IISC = ΔAh_ISC / Elapsed time. |  |  |
| ΔAh_CCM | ΔAh_CCM |  | 만충~만충 간 적산 용량(SDI ISD 입력). |  |  |
| ΔAh_ISC | ΔAh_ISC |  | 단락 누설 용량. CCM 적산에서 정상 손실분을 차감해 산출. |  |  |
| ISC 적합성 조건 | ISC Applicability Condition (SDI) |  | SDI — 안정 CV(taper 변화율 5 mA/30 s 이하) ∧ 완충 시점 간 ΔI ≤ 5 mA, ΔV ≤ 10 mV, ΔT < 10 ℃, 2 hr < Δt < 48 hr ∧ 10 ℃ < T < 45 ℃ 등을 동시 만족. |  |  |

## 12. Dynamic / Smart EDV

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| SBA | Silicon Battery Algorithm |  | Si 음극 셀의 hysteresis·shift·loss 보상을 담당하는 알고리즘. NVT/SDI 모두 보유. |  |  |
| Si Loss | Si Loss |  | Si 음극에 의한 effective 용량 손실. 실제 Si 질량이 아닌 사용 가능 용량 기준. Hysteresis·Shift 보정의 입력. |  |  |
| 3.6 V Peak Detection | 3.6 V Peak Detection |  | NVT — dV/dQ 곡선의 3.6 V 부근 peak가 Si 기여 시작점. 열화에 따라 peak 전압 위치는 거의 변하지 않음. |  |  |
| dV/dQ 분석 | dV/dQ Analysis |  | 저전류(0.2 C 이하) 정전류 방전 곡선의 미분. Si Loss model·SOH 분석의 표준 기법. ('분석/측정' 카테고리의 dQ/dV의 역함수). |  |  |
| OCV 히스테리시스 보상 | OCV Hysteresis Compensation (SBA) |  | 충·방전 방향별 별도 OCV table 적용. NVT는 SOC 100%부터 2% 간격(50개), 충전 0%부터 5% 간격이나 보정에 미반영. |  |  |
| OCV Shift Compensation | OCV Shift Compensation |  | Si Loss에 비례한 OCV 곡선 평행 이동 보상. SBA의 핵심 보정. |  |  |

## 13. SOC Smoothing

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| 부분 방전 히스테리시스 | Partial Discharge Hysteresis |  | SDI — SOC 40% 임계로 분기. 40% 이상 방전 후 충전: 방전 OCV table, 40% 이하 방전 후 충전: 충/방전 OCV 사이값. Si 영역 사용 여부가 hysteresis 발현을 결정. |  |  |
| Dynamic EDV / Smart EDV | Dynamic EDV Control / Smart EDV Control | Terminal Voltage Dynamic Control | 사용 패턴·열화에 따라 EDV를 ±50 mV 단위로 능동 조정. NVT/SDI 자체 개발 (SET 적용 여부 미확정). | 보증 cycle까지 swelling 한계 준수. | 상한선 table·하한선(CCV 3.0 V) 등 운영 정책이 복잡. |
| User Habits Analysis | User Habits Analysis (Step 1) |  | Dynamic EDV — 만충 30회마다 온도·CCV 사용 하한을 분석해 사용자 패턴 추출. |  |  |
| Fading/Swelling Simulation | Fading/Swelling Simulation (Step 2) |  | Dynamic EDV — Step 1 패턴이 보증 cycle까지 유지된다고 가정해 swelling 수준(예: 10% @1200 cycle) 예측. |  |  |
| EDV Adjustment | EDV Adjustment (Step 3) |  | Dynamic EDV — Step 2 결과가 보증 swelling 초과: EDV +50 mV / 미만: EDV −50 mV × n. 50 mV ≈ 용량 2% 수준. |  |  |
| CCV / OCV 동시 Cut-off | CCV + OCV Dual Cut-off |  | SDI — 폐회로 전압(CCV)과 개방회로 전압(OCV)을 동시에 cut-off 기준으로 사용해 EDV 정밀화. |  |  |
| Long-life Algorithm | Long-life Algorithm |  | Dynamic EDV의 EDV 조정 하한선을 결정하는 옵션 알고리즘. |  |  |
| 방전 Smoothing | Discharging Smoothing |  | V ≤ TermV + Smooth ΔV Start 만족 시 40 sec 내 0% 수렴(NVT) / Term Smooth Time 동안 0% 수렴(TI). V ≤ TermV − Smooth ΔV Start 시 즉시 0%(TI). |  |  |
| 충전 Smoothing | Charging Smoothing |  | Charge term taper window 내 RM이 FCC로 수렴(NVT) / Charging termination 조건 만족 시 99% → 100% 변환(TI, RSOCL=1). |  |  |
| Converge-to-Empty | Converge-to-Empty |  | ADI — RepLow / VoltLowOff 임계로 SOC under/over-estimation 분기. Over-estimation 시 RepSOC = RepSOC − (AvgVCell − Vempty) / VoltLowOff. |  |  |
| VoltLowOff | VoltLowOff (ADI) |  | ADI register — Smoothing 시작 전압 정의. VoltLow = Vempty − VoltLowOff. |  |  |

## 14. Register · Concept

| 한글 | 영어 | 동의어 | 정의 | 성능 영향 | Trade-off |
|---|---|---|---|---|---|
| RepLow | RepLow (ADI) |  | ADI register — Smoothing 시작 RSOC 임계. |  |  |
| MinSlopeX | MinSlopeX (ADI) |  | ADI register — Smoothing 동안 SOC 최소 변화량 제어. Under-estimation 분기에서 RepSOC 감소 속도 저감에 사용. |  |  |
| Term Smooth Start Cell V Delta | Term Smooth Start Cell V Delta (TI) |  | TI — Smoothing 시작 ΔV 임계. TermV 대비 +/− 방향에 따라 점진/즉시 0% 수렴 분기. |  |  |
| Charge Term Taper Window | Charge Term Taper Window Time (TI) |  | TI — Charging smoothing 수렴 시간 window. RM이 FCC로 수렴하는 기간. |  |  |
| I2C Gauging Configuration [RSOCL] | I2C Gauging Configuration [RSOCL] (TI) |  | TI register — 1: 99% 유지 후 charging termination 만족 시 100% / 0: 99% 유지 없이 소수점부터 100% 표시. |  |  |
| Static/Relax Mode Smoothing | Smoothing in Static / Relax Mode |  | 휴지 구간 RSOC 변화 정책. 일반적으로 감소만 허용(NVT). TI는 휴지 jump 또는 smoothing 중 선택 가능. |  |  |
| BatteryStatus | BatteryStatus (SBS register) |  | SBS 표준 status register. DSG/CHG 등 비트 플래그. Charging termination 평가에 [DSG]=0 사용. |  |  |
| AverageCurrent | AverageCurrent (register) |  | 평균 전류 register. End-of-charge·ISC 적합성 평가의 입력. |  |  |
| ChargingVoltage | ChargingVoltage (register) |  | 충전기 인가 전압 register. Charging termination 조건 V() + ChgTermV ≥ ChargingVoltage() 평가. |  |  |
| TAPER_VOLT | TAPER_VOLT (TI status bit) |  | TI — taper voltage 도달 플래그. Charging termination 게이트. |  |  |
| IChgTerm | IChgTerm (Charge Termination Current) |  | 충전 종료 판정 전류 register. End-of-charge detection의 비대칭 windows(× 0.125 ~ × 1.25)에 사용. |  |  |
| Cycle Count | Cycle Count |  | 누적 cycle 수 register. SBA·CSD·SOH 갱신 주기 결정. (10 cycle, 30 cycle 등). |  |  |
| Designed Capacity Threshold | Designed Capacity Threshold |  | Qmax 갱신 ΔQ 임계 (예: ≥ 37%, ≥ 90%) 또는 CCM error 임계(< 5%)의 분모로 사용되는 셀 설계 용량. |  |  |
| OCV 측정 점 회피 | OCV Measurement Point Avoidance |  | TI — DOD1/DOD2 측정점이 3.737~3.7 V 영역에 있으면 제외 (No in flat region). Chemistry별로 영역 가변. |  |  |
