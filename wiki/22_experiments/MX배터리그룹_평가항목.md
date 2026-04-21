---
title: "MX배터리그룹 평가항목"
tags: [Experiments, 평가, CTQ, QCP, 설계]
type: reference
status: active
related:
  - "[[신뢰성_평가]]"
  - "[[충방전기_정밀도]]"
  - "[[DCIR_측정_업체별]]"
created: 2025-12-15
updated: 2026-03-15
source: "origin/MX배터리그룹-평가항목.md"
---

Proto
- 상온수명(EU)
- 상온수명(2step)
- 고온/저온 수명
- Dimension(SOC별 두께)
- 표준용량
- 충전시간
- 율별 충전/방전
- 고온 동작
- 고온저장방지(85도 for 8일)
- 고온저장방지(60도 for 21,30일)
- 고온고습
- Floating charge (45도 for 50일)
- 3전극
- DC-IR
- EIS
- 가열
- Dent

# 설계항목
- 에너지밀도 (Wh/L)
- Size (mm)
- Rated capacity (mAh)
- Typical capacity (mAh)
- 전류밀도 (mA/cm2)
- N/P ratio
- 양음극
	- 활물질
	- 비용량 (mAh/g)
	- L/L (press) (mg/cm2)
	- 합제밀도 (g/cc)
- 적층수 (H/C, F/C, Anode)

## 세부항목
- 음극: SC2A(Team), G14(Group)
- 음극 바인더(PAA X, Li-PAA O)
- 음극 기재 (고연신, 초고강도)
- 분리막 (MFS 9.5)
- 전해액 : 1.35M, EP10, FEC10, LiDFOB1
	- 함침 개선 / Wettability >> swelling 두께 감소
	- ![[Pasted image 20250818104715.png]]
- 주액계수 1.35~1.25 g/Ah
	- ![[Pasted image 20250818104416.png]]


# 공정
## 1. 극판
	양극, 음극 코팅
## 2. 조립
	STACK - PKG
## 3. 화성
	AG1(RT/24hr) - AG2(HT/6hr) - Degassing - HPC - AG(RT/12hr) - D/F - CT - CD - AG(RT/12hr) - IR/OCV#2 - 고온AG4(24hr) - 저온AG4(24hr) - IR/OCV#3 - CP - AG3(RT/24hr) - IR/OCV#3 - 포장/출하 검사 - ETD/ETA

HPC![[Pasted image 20250818104500.png]]

## 공정불량 항목
- 극판공정: 슬리팅(프레스 기타 불량, 극판 수량 부족), B코팅(조건도출 불량)
- Stack공정: Vision-접힘(Bottom) 불량, Notching 불량, Vision-A/C align -#a 불량
- 조립공정: 전해액 주입 하한 불량, No edge(taping), 상부 양극 S/T PP Tape폭 max불량
- 화성공정: IR/OCV #3: 표준편차 delta V, HPC: DC NG, C/T 화성 - 찍힘


# CTQ

| Process        | Detail       | Process/Product Item                               | Control Plan                                            |        |                      |
|----------------|--------------|----------------------------------------------------|---------------------------------------------------------|--------|----------------------|
|                |              |                                                    | Spec.                                                   | Unit   | Measurement          |
| Mixing         | Anode        | Viscosity                                          | 3000±1500                                               | CPS    | Viscosity            |
|                | Cathode      | Viscosity                                          | 3500±1500                                               | CPS    | Viscosity            |
|                | Anode        | Solid Contents                                     | 49.41±1.5                                               | %      | Solid Contents       |
|                | Cathode      | Solid Contents                                     | 78.5±1.5                                                | %      | Solid Contents       |
| Coating        | Anode        | Loading level                                      | 14.79±0.4                                               | mg/cm2 | Weight               |
|                | Cathode      | Loading level                                      | 34.45±0.4                                               | mg/cm2 | Weight               |
|                | Half Cathode | Loading level                                      | 15.21±0.4                                               | mg/cm2 | Weight               |
|                | Anode        | Electrode adhesion                                 | 0.8＜                                                    | gf/mm  | 180º Peel-off        |
|                | Cathode      | Electrode adhesion                                 | 0.5＜                                                    | gf/mm  | 180º Peel-off        |
|                | Half Cathode | Electrode adhesion                                 | 0.4＜                                                    | gf/mm  | 180º Peel-off        |
| Pressing       | Anode        | Press thickness                                    | 94±3                                                    | ㎛      | Micrometer           |
|                | Cathode      | Press thickness                                    | 90±3                                                    | ㎛      | Micrometer           |
|                | Half Cathode | Press thickness                                    | 59±3                                                    | ㎛      | Micrometer           |
|                | Anode        | Electrode adhesion                                 | 0.3＜                                                    | gf/mm  | 180º Peel-off        |
|                | Anode        | Edge sliding                                       | Max 10                                                  | ㎛      | Micrometer           |
|                | Anode        | SAICAS                                             | ≥50                                                     | %      | SAICAS               |
|                | Cathode      | Press thickness(Notching Area Cathode Max. – Min.) | ≤4                                                      | ㎛      | Vision               |
| Slitting       | Anode        | Burr                                               | N/A                                                     | ㎛      | VM                   |
|                | Cathode      | Burr                                               | N/A                                                     | ㎛      | VM                   |
|                | Anode        | Width                                              | 86.0±0.1                                                | mm     | Vernier calipers     |
|                | Cathode      | Width                                              | 87.0±0.1                                                | mm     | Vernier calipers     |
| Vacuum Dry     | Anode        | Moisture content (140℃)                            | Max 200                                                 | ppm    | 수분측정기                |
|                | Cathode      | Moisture content (140℃)                            | Max 200                                                 | ppm    | 수분측정기                |
| Notching/Stack | Cathode      | Foil Burr Cutting Burr                             | Max 4.25                                                | ㎛      | VM                   |
|                | Notching     | Electrode Notching Width                           | FC : 59.47±0.10<br/>음극 : 60.17±0.10<br/>HC : 59.37±0.10 | mm     | Vision               |
|                | Notching     | Electrode Notching Height                          | FC : 68.80±0.10<br/>음극 : 70.30±0.10<br/>HC : 68.70±0.10 | mm     | Vision               |
|                | Alignment    | Separator - Anode alignment                        | #2,3 : 1.45±0.60<br/>#6,7 : 1.05±0.60                   | mm     | Vision               |
|                | Alignment    | Andoe - Cathode alignment                          | #2,3 : 1.15±0.20<br/>#1,4,5,6,7,8 : 0.35±0.20           | mm     | Vision               |
| Packaging      | Forming      | Forming depth                                      | 4.21±0.10                                               | mm     | Laser Pointer(depth) |
|                | Anode        | Tab Welding (Between JR tab and S/T)               | Min 1.5                                                 | kgf    | 인스트롱                 |
|                | Cathode      | Tab Welding (Between JR tab and S/T)               | Min 1.0                                                 | kgf    | 인스트롱                 |
|                | Appearance   | Tab Distance                                       | 22.0±0.8                                                | mm     | Steel Ruler          |
|                | Sealing      | Top sealing strength (anode tab area)              | Min 1.0                                                 | kgf    | 인스트롱                 |
|                | Sealing      | Top sealing strength (cathode tab area)            | Min 1.0                                                 | kgf    | 인스트롱                 |
|                | Sealing      | Top sealing strength (tab to tab area)             | Min 1.5                                                 | kgf    | 인스트롱                 |
|                | Sealing      | Top sealing thickness (anode tab area)             | 365±30                                                  | ㎛      | Micrometer           |
|                | Sealing      | Top sealing thickness (cathode tab area)           | 365±30                                                  | ㎛      | Micrometer           |
|                | Sealing      | Top sealing thickness (anode non-tab area)         | 172±15                                                  | ㎛      | Micrometer           |
|                | Sealing      | Top sealing thickness (tab to tab area area)       | 172±15                                                  | ㎛      | Micrometer           |
|                | Sealing      | Top sealing thickness (cathode non-tab area)       | 172±15                                                  | ㎛      | Micrometer           |
|                | Sealing      | Terrace sealing width                              | 2.8±0.5                                                 | mm     | Steel Ruler          |
|                | Sealing      | Side sealing strength                              | Min 1.5                                                 | ㎛      | 인스트롱                 |
|                | Sealing      | Side sealing thickness (top)                       | 172±15                                                  | ㎛      | Micrometer           |
|                | Sealing      | Side sealing thickness (middle)                    | 172±15                                                  | ㎛      | Micrometer           |
|                | Sealing      | Side sealing thickness (bottom)                    | 172±15                                                  | ㎛      | Micrometer           |
|                | Sealing      | Side sealing width                                 | 5.0±0.5                                                 | mm     | Steel Ruler          |
|                | Injection    | Electrolyte weight                                 | 6.49±0.05                                               | g      | MES                  |
| HPC            | HPC          | OCV                                                | 4100~4500                                               | mV     | MES                  |
| Degas/Folding  | Sealing      | Side sealing thickness (top)                       | 172±15                                                  | ㎛      | Micrometer           |
|                | Sealing      | Side sealing thickness (bottom)                    | 172±15                                                  | ㎛      | Micrometer           |
|                | Sealing      | Side sealing width                                 | Min 1.0                                                 | mm     | Steel ruler          |
|                | DF           | Electrolyte weight                                 | Min 6.40                                                | g      | MES                  |
| Formation      | Formation    | OCV (@shipping charge)                             | 3760~3800(SOC30)TBD<br/>3980~4040(SOC62)TBD             | mV     | MES                  |
|                | Formation    | IR (@shipping charge)                              | 1~17_TBD                                                | mΩ     | MES                  |
|                | Formation    | Delta OCV                                          | -2~10                                                   | mV     | MES                  |
|                | Formation    | Cell thickness (@shipping charge)                  | 5.66±0.11(SOC30)_TBD<br/>4.99±0.11(SOC62)_TBD           | mm     | PPG(500g)            |
|                | Formation    | Shipping Capacity                                  | 4871_TBD                                                | mAh    | Ch/Dischger          |


# QCP
| PROCESS                            | FLOW  | DETAIL PROCESS                                                                                                                                                                                                                                                                    | CRITICAL                                           | 평가/ 측정방법                      | Sample 크기 | 검사주기                    | 관리방법   |
| ---------------------------------- | ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- | ----------------------------- | --------- | ----------------------- | ------ |
|                                    | CHART |                                                                                                                                                                                                                                                                                   | CONTROL POINT                                      |                               |           |                         |        |
| Cathode<br/><br/>Binder Sol Mixing |       | ●  Solvent Input<br/>  ●  Binder Powder Input                                                                                                                                                                                                                                     | Solvent Material Quality                           | In-coming Material Inspection | ALL       | 1Time/Month             | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Solvent Input                                      | Flow-Meter                    | ALL       | 1Time/Batch             | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Binder Powder Material Quality                     | In-coming Material Inspection | ALL       | 1Time/Month             | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Binder Powder Input                                | Scale                         | 1         | 1Time/Batch             | System |
|                                    |       | ●  Binder Solution Manufacturing                                                                                                                                                                                                                                                  | Binder Mixing Time                                 | Timer                         | ALL       | 1Time/Batch             | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Binder Mixing Rpm                                  | Rpm meter                     | ALL       | 1Time/Batch             | System |
|                                    |       | ●  Binder Solution Measurement                                                                                                                                                                                                                                                    | Binder Solution Temp                               | Thermometer                   | 1         | 1Time/Batch             | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Binder Solution Viscosity                          | Viscometer                    | 1         | 1Time/Batch             | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Binder Solution Solid Contents                     | *Scale                        | 1         | 1Time/Batch             | System |
| Cathode<br/><br/>Slurry Mixing     |       | ●  Active Material Input<br/>  ●  Conductive Material Input<br/>  ●  Binder Solution Input<br/>  ●  Solvent Input                                                                                                                                                                 | Binder Sol'n Input                                 | Flow-Meter                    | ALL       | 1Time/Batch             | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Conductive Material Quality                        | In-coming Material Inspection | ALL       | 1Time/Month             | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Conductive Material Input                          | Scale                         | 1         | 1Time/Batch             | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Solvent Material Quality                           | In-coming Material Inspection | ALL       | 1Time/Month             | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Solvent Input                                      | Flow-Meter                    | 1         | 1Time/Batch             | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Active Material Quality                            | In-coming Material Inspection | 1         | 1Time/LOT               | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Active Material Input                              | Scale                         | 1         | 1Time/Batch             | System |
|                                    |       | ● Slurry Manufacturing                                                                                                                                                                                                                                                            | Slurry Mixing Time                                 | Timer                         | ALL       | 1Time/Batch             | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Slurry Mixing Rpm                                  | Rpm meter                     | ALL       | 1Time/Batch             | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Slurry Output Volume (Filmics)                     | Flow-Meter                    | 1         | 1Time/Batch             | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Wheel Rotation Speed (Filmics)                     | Speed meter                   | 1         | 1Time/Batch             | System |
|                                    |       | ● Slurry Measurement                                                                                                                                                                                                                                                              | Slurry Temp                                        | Thermometer                   | 1         | 1Time/Batch             | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Slurry Viscosity                                   | Viscometer                    | 1         | 1Time/Batch             | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Slurry Solid Contents                              | *Scale                        | 1         | 1Time/Batch             | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Content Of metal(Fe, Cr, Ni, Zn)                   | ICP-AES                       | 1         | 1Time/Batch             | System |
|                                    |       | ● Slurry Storage                                                                                                                                                                                                                                                                  | Mixer rpm                                          | Rpm meter                     | 1         | 1Time/Batch             | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Storage Time                                       | Timer                         | 1         | 1Time/Batch             | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Storage Pressure                                   | Pressure gauge                | 1         | 1Time/Batch             | System |
| Cathode<br/><br/>Coating           |       | ●  Unwinder<br/>  ●  Coating<br/>  ●  Drying<br/>  ●  rewinding                                                                                                                                                                                                                   | Type of Slurry                                     | Lot Card                      | 1         | 1Time/Batch Group       | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Al-Foil Input                                      | In-coming Material Inspection | 1         | 1Time/LOT               | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Unwinder Tension                                   | Tension Controller            | ALL       | 1Time/Batch Group       | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Coater Tension                                     | Tension Controller            | ALL       | 1Time/Batch Group       | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Dimension Set                                      | Dimension controller          | 1         | 1Time/Batch Group       | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Line Speed                                         | speedmeter                    | ALL       | 1Time/Batch             | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Dry Temp                                           | Thermometer                   | ALL       | 1Time/Batch Group       | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Dry Airflow                                        | Amperemeter                   | ALL       | 1Time/Batch Group       | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | L/L(Continuous)                                    | β-Ray Scanner                 | ALL       | Continuous              | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Accumlator Tension                                 | Tension Controller            | ALL       | 1Time/Batch Group       | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Outfeed Tension                                    | Tension Controller            | ALL       | 1Time/Batch Group       | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Rewinder Tension                                   | Tension Controller            | ALL       | 1Time/Batch Group       | System |
|                                    |       | ● Electrode Measurement                                                                                                                                                                                                                                                           | Slurry Content Of metal(Fe, Cr, Ni, Zn)            | ICP-AES                       | 1         | 1Time/JC<br/>1Time/24Hr | System |
|                                    |       |                                                                                                                                                                                                                                                                                   | Side A L/L                                         | *Scale                        | 9         | 1Time/Batch Group       | System |
