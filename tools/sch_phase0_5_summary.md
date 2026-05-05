# Phase 0-5 분류기 v2 — 187 폴더 / 368 .sch 사이클별 정의

- 입력 root: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data`
- 실험 폴더: **187** (`.sch` 보유 173, 미보유 14 = Toyo `.ptn` 또는 미확보)
- .sch 파일: **368** (parsed 368, failed 0)
- 총 loop group (outer-goto expanded): **8298**
- 산출물:
  - [`sch_phase0_5_groups.csv`](sch_phase0_5_groups.csv) — 사이클(loop group) 단위 정의 한 row
  - [`sch_phase0_5_files.csv`](sch_phase0_5_files.csv) — 파일 단위 메타 + 카테고리 분포

## 1. 시험종류 × 카테고리 cross-table

| 시험종류 | 폴더(.sch/전체) | 파일 | TC총수 | RPT | CHG_DCHG | ACCEL | PULSE_DCIR | CHARGE_SET | FORMATION | REST_LONG | HYSTERESIS_DCHG | HYSTERESIS_CHG | DCHG_SET | INIT | UNKNOWN | TERMINATION | POWER_CHG | DISCHARGE_SET | GITT_PULSE | REST_SHORT | FLOATING | SOC_DCIR | RSS_DCIR |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 성능 | 102/103 | 197 | 12469 | 1180 | 862 | 80 | 176 | 198 | 48 | 321 | 27 | 27 | 173 | 50 | 0 | 119 | 108 | 84 | 71 | 32 | 6 | 20 | 0 |
| 성능_hysteresis | 16/16 | 20 | 450 | 64 | 24 | 0 | 0 | 0 | 0 | 0 | 171 | 171 | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 성능_시험직후 | 10/10 | 10 | 41 | 16 | 10 | 0 | 0 | 0 | 0 | 9 | 0 | 0 | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 수명 | 24/36 | 85 | 80631 | 1076 | 0 | 849 | 230 | 45 | 0 | 0 | 32 | 0 | 0 | 81 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 8 |
| 수명_복합floating | 21/22 | 56 | 21462 | 506 | 74 | 0 | 450 | 318 | 334 | 0 | 0 | 0 | 16 | 40 | 142 | 0 | 0 | 0 | 0 | 0 | 24 | 0 | 0 |

## 2. 카테고리 전역 분포

| Category | count | 비율 |
|---|---|---|
| RPT | 2842 | 34.2% |
| CHG_DCHG | 970 | 11.7% |
| ACCEL | 929 | 11.2% |
| PULSE_DCIR | 856 | 10.3% |
| CHARGE_SET | 561 | 6.8% |
| FORMATION | 382 | 4.6% |
| REST_LONG | 330 | 4.0% |
| HYSTERESIS_DCHG | 230 | 2.8% |
| HYSTERESIS_CHG | 198 | 2.4% |
| DCHG_SET | 192 | 2.3% |
| INIT | 191 | 2.3% |
| UNKNOWN | 142 | 1.7% |
| TERMINATION | 122 | 1.5% |
| POWER_CHG | 108 | 1.3% |
| DISCHARGE_SET | 84 | 1.0% |
| GITT_PULSE | 71 | 0.9% |
| REST_SHORT | 32 | 0.4% |
| FLOATING | 30 | 0.4% |
| SOC_DCIR | 20 | 0.2% |
| RSS_DCIR | 8 | 0.1% |

## 3. UNKNOWN / EMPTY 발생 파일 (sch + body signature 단위 dedup)

총 **142** 그룹 (dedup body-signature 기준 **14** 종).
대다수는 outer-goto 확장으로 인한 동일 body 중복.

| 시험종류 | 폴더 | sch | N | body | chg/dchg/rest | EC types | desc |
|---|---|---|---|---|---|---|---|
| 수명_복합floating | 260320_260923_03_안성진_251mAh_HaeanProtoDO | 260320_260923_03_안성진_251mAh_HaeanProtoDOE복합Floatin | 14 | 7 | 4/1/2 |  | 250-5mAh ��������Floating |
| 수명_복합floating | 260320_260923_03_안성진_251mAh_HaeanProtoDO | 260320_260923_03_안성진_251mAh_HaeanProtoDOE복합Floatin | 14 | 7 | 4/1/2 |  | 250-5mAh ��������Floating |
| 수명_복합floating | 260320_260923_03_안성진_251mAh_HaeanProtoDO | 260320_260923_03_안성진_251mAh_HaeanProtoDOE복합Floatin | 14 | 7 | 4/1/2 |  | 250-5mAh ��������Floating |
| 수명_복합floating | 260320_260923_03_안성진_251mAh_HaeanProtoDO | 260320_260923_03_안성진_251mAh_HaeanProtoDOE복합Floatin | 14 | 7 | 4/1/2 |  | 250-5mAh ��������Floating |
| 수명_복합floating | 260320_260923_03_안성진_251mAh_HaeanProtoMa | 260320_260923_03_안성진_251mAh_HaeanProtoMain복합Floati | 14 | 7 | 4/1/2 |  | 250-5mAh ��������Floating |
| 수명_복합floating | 260320_260923_03_안성진_251mAh_HaeanProtoMa | 260320_260923_03_안성진_251mAh_HaeanProtoMain복합Floati | 14 | 7 | 4/1/2 |  | 250-5mAh ��������Floating |
| 수명_복합floating | 260320_260923_03_안성진_251mAh_HaeanProtoMa | 260320_260923_03_안성진_251mAh_HaeanProtoMain복합Floati | 14 | 7 | 4/1/2 |  | 250-5mAh ��������Floating |
| 수명_복합floating | 260320_260923_03_안성진_251mAh_HaeanProtoMa | 260320_260923_03_안성진_251mAh_HaeanProtoMain복합Floati | 14 | 7 | 4/1/2 |  | 250-5mAh ��������Floating |
| 수명_복합floating | 260413_260930_05_김영환_3365mAh_Gen6+VB ATL | 260413_260930_05_김영환_3365mAh_Gen6+VB ATL Proto1 고온 | 14 | 8 | 4/2/2 |  | �������� 4.57V_Si 3365mAh 2C 2 |
| 수명_복합floating | 260413_260930_05_김영환_3365mAh_Gen6+VB ATL | 260413_260930_05_김영환_3365mAh_Gen6+VB ATL Proto1 고온 | 14 | 8 | 4/2/2 |  | �������� 4.57V_Si 3365mAh 2C 2 |
| 수명_복합floating | 260413_260930_05_박기진_4948mAh_Gen6+VB SDI | 260413_260930_05_박기진_4948mAh_Gen6+VB SDI Proto1 고온 | 14 | 8 | 4/2/2 |  | �������� 4.57V_Si 4948mAh 2C 2 |
| 수명_복합floating | 260413_260930_05_박기진_4948mAh_Gen6+VB SDI | 260413_260930_05_박기진_4948mAh_Gen6+VB SDI Proto1 고온 | 14 | 8 | 4/2/2 |  | �������� 4.57V_Si 4948mAh 2C 2 |
| 수명_복합floating | 260413_260930_05_박기진_4948mAh_Gen6+VB SDI | 260413_260930_05_박기진_4948mAh_Gen6+VB SDI Proto1 고온 | 14 | 8 | 4/2/2 |  | �������� 4.57V_Si 4948mAh 2C 2 |
| 수명_복합floating | 260413_260930_05_박기진_4948mAh_Gen6+VB SDI | 260413_260930_05_박기진_4948mAh_Gen6+VB SDI Proto1 고온 | 14 | 8 | 4/2/2 |  | �������� 4.57V_Si 4948mAh 2C 2 |

## 4. 폴더 × 카테고리 분포 (실험 폴더 단위)

한 폴더 내 채널별 .sch 가 동일 schedule 인 케이스가 있어, 동일 폴더의 categories 는 채널 수만큼 곱해진 집계.

| 시험종류 | 폴더 | n_sch | TC총수 | 카테고리 분포 |
|---|---|---|---|---|
| 성능 | 240821 선행랩 류성택 Gen4pGr mini-ATL-WD-Proto-422mAh-20C-450V-GIT | 2 | 428 | GITT_PULSE(4), INIT(2), FORMATION(2) |
| 성능 | 240919 선행랩 류성택 Gen4pGr mini-ATL-WD-Proto-422mAh-20C-450V-SOC | 2 | 192 | SOC_DCIR(8), ACCEL(4), INIT(2), FORMATION(2), RPT(2), CHARGE_SET(2) |
| 성능 | 250314_250705_05_나무늬_4900mAh_Gen5 SDI Pre-MP Si5% Floating+9 | 4 | 12 | INIT(4), RPT(4), FLOATING(4) |
| 성능 | 250513_250526_05_나무늬_2610mAh_Gen5+B SDI MP1 DoE SBR 0.7 DCIR | 1 | 95 | SOC_DCIR(4), ACCEL(2), INIT(1), FORMATION(1), RPT(1) |
| 성능 | 250513_250526_05_나무늬_2610mAh_Gen5+B SDI MP1 Main SBR 0.9 DCI | 1 | 95 | SOC_DCIR(4), ACCEL(2), INIT(1), FORMATION(1), RPT(1) |
| 성능 | 250827_251028_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter | 1 | 50 | RPT(12), CHG_DCHG(4), REST_LONG(3), ACCEL(1), CHARGE_SET(1) |
| 성능 | 250827_251028_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter | 1 | 50 | RPT(8), CHG_DCHG(8), REST_LONG(3), ACCEL(1), CHARGE_SET(1) |
| 성능 | 250827_251028_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter | 1 | 50 | RPT(8), POWER_CHG(8), REST_LONG(3), ACCEL(1), CHARGE_SET(1) |
| 성능 | 250827_251028_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter | 1 | 50 | RPT(8), POWER_CHG(8), REST_LONG(3), ACCEL(1), CHARGE_SET(1) |
| 성능 | 250827_251028_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter | 1 | 50 | RPT(13), CHG_DCHG(3), REST_LONG(3), ACCEL(1), CHARGE_SET(1) |
| 성능 | 250827_251028_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter | 1 | 76 | RPT(6), CHG_DCHG(5), ACCEL(2), REST_LONG(2), CHARGE_SET(1), POWER_CHG(1), DCHG_SET(1) |
| 성능 | 250827_251028_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter | 1 | 51 | RPT(5), CHG_DCHG(4), REST_LONG(2), ACCEL(1), CHARGE_SET(1), POWER_CHG(1), DCHG_SET(1), FORMATION(1) |
| 성능 | 250827_251028_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter | 1 | 150 | ACCEL(1), GITT_PULSE(1) |
| 성능 | 250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half-14pi-GITT- | 1 | 242 | GITT_PULSE(2), CHARGE_SET(1), DCHG_SET(1) |
| 성능 | 250905_250915_00_류성택_4-376mAh_M2-SDI-open-an-half-14pi-GITT- | 1 | 242 | GITT_PULSE(2), INIT(1), CHARGE_SET(1) |
| 성능 | 250915_250925_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter | 1 | 5 | RPT(3), REST_LONG(1), CHG_DCHG(1) |
| 성능 | 250915_250925_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter | 1 | 5 | RPT(2), CHG_DCHG(2), REST_LONG(1) |
| 성능 | 250915_250925_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter | 1 | 5 | RPT(2), POWER_CHG(2), REST_LONG(1) |
| 성능 | 250915_250925_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter | 1 | 5 | RPT(2), POWER_CHG(2), REST_LONG(1) |
| 성능 | 250915_250925_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter | 1 | 5 | RPT(3), REST_LONG(1), CHG_DCHG(1) |
| 성능 | 251002_251010_00_박민희_4-19mAh_RatedCh half ca 4.19mAh SDI | 2 | 12 | CHG_DCHG(8), REST_SHORT(2), DCHG_SET(2) |
| 성능 | 251209_251213_05_현혜정_6490mAh_LWN Si25P SPL 율별방전Profile | 1 | 6 | CHG_DCHG(4), INIT(1), RPT(1) |
| 성능 | 251218_251230_00_박민희_3-45mAh_M1 ATL Cathode Half T23 | 8 | 40 | REST_LONG(8), REST_SHORT(8), FORMATION(8) |
| 성능 | 251218_251230_00_박민희_4-04mAh_M1 ATL Anode Half T23 | 8 | 40 | REST_LONG(8), REST_SHORT(8), FORMATION(8) |
| 성능 | 251224_260110_00_박민희_3-45mAh_M1 ATL Cathode Half T23 GITT 0. | 8 | 1784 | GITT_PULSE(32), REST_SHORT(8), DCHG_SET(8), CHARGE_SET(8) |
| 성능 | 251224_260110_00_박민희_4-04mAh_M1 ATL Anode Half T23 GITT 0.05 | 3 | 759 | GITT_PULSE(12), REST_SHORT(3), DCHG_SET(3), CHARGE_SET(3) |
| 성능 | 251224_260110_00_박민희_4-04mAh_M1 ATL Anode Half T23 GITT 0.1C | 3 | 669 | GITT_PULSE(12), REST_SHORT(3), DCHG_SET(3), CHARGE_SET(3) |
| 성능 | 260109_260112_05_이근준_5000mAh_Gen5P Si5 ATL T2 3M 보관 용량 측정 4c | 6 | 36 | INIT(6), FORMATION(6), CHARGE_SET(6) |
| 성능 | 260112_260312_03_나무늬_2688mAh_Gen5+B SDI MP2 2.0C EPF HT Floa | 2 | 2 | FLOATING(2) |
| 성능 | 260202_260226_05_문현규_5075mAh_Cosmx 25Si 율별용량+Hybrid ch54 | 1 | 23 | CHG_DCHG(16), RPT(3), INIT(1), FORMATION(1) |
| 성능 | 260204_260226_05_문현규_4900mAh_Cosmx gen5 율별용량 ch61 | 1 | 15 | CHG_DCHG(8), RPT(3), INIT(1), FORMATION(1) |
| 성능 | 260204_260226_05_문현규_5070mAh_Cosmx Gen5P 율별용량 | 1 | 15 | CHG_DCHG(8), RPT(3), INIT(1), FORMATION(1) |
| 성능 | 260211_260310_05_문현규_3885mAh_POR 40C pulse PA1 ATL | 2 | 532 | RPT(112), CHG_DCHG(110), PULSE_DCIR(28), DISCHARGE_SET(14), CHARGE_SET(14), DCHG_SET(12), INIT(2), TERMINATION(2) |
| 성능 | 260211_260310_05_문현규_3885mAh_POR 40C pulse PA1 SDI | 3 | 798 | RPT(168), CHG_DCHG(165), PULSE_DCIR(42), DISCHARGE_SET(21), CHARGE_SET(21), DCHG_SET(18), INIT(3), TERMINATION(3) |
| 성능 | 260211_260310_05_문현규_4855mAh_POR 40C pulse PA3 ATL | 3 | 798 | RPT(168), CHG_DCHG(165), PULSE_DCIR(42), DISCHARGE_SET(21), CHARGE_SET(21), DCHG_SET(18), INIT(3), TERMINATION(3) |
| 성능 | 260211_260310_05_문현규_4855mAh_POR 40C pulse PA3 SDI | 3 | 798 | RPT(168), CHG_DCHG(165), PULSE_DCIR(42), DISCHARGE_SET(21), CHARGE_SET(21), DCHG_SET(18), INIT(3), TERMINATION(3) |
| 성능 | 260212_260215_05_한지영_5432mAh_SDI Phase2 MP2 Fresh DCIR SOC10 | 2 | 52 | PULSE_DCIR(4), INIT(2), FORMATION(2), DISCHARGE_SET(2), CHARGE_SET(2), TERMINATION(2) |
| 성능 | 260212_260215_05_한지영_5432mAh_SDI Phase2 MP2 고온수명후 DCIR SOC10 | 2 | 44 | PULSE_DCIR(4), INIT(2), CHARGE_SET(2), TERMINATION(2) |
| 성능 | 260226_260228_05_문현규_3876mAh_PS 연속저장 DCIR | 2 | 48 | PULSE_DCIR(4), INIT(2), RPT(2), DISCHARGE_SET(2), CHARGE_SET(2), TERMINATION(2) |
| 성능 | 260226_260228_05_문현규_3885mAh_PA1 연속저장 DCIR | 3 | 72 | PULSE_DCIR(6), INIT(3), RPT(3), DISCHARGE_SET(3), CHARGE_SET(3), TERMINATION(3) |
| 성능 | 260306_260318_05_현혜정_6330mAh_LWN 25P(after LT100cy) SOC별 DCI | 2 | 170 | RPT(4), SOC_DCIR(4), ACCEL(4), PULSE_DCIR(4), INIT(2), FORMATION(2), CHARGE_SET(2) |
| 성능 | 260310_260312_05_이근준_4991mAh_Gen5P ATL MP1 8M Fresh 보관 용량 측정 | 4 | 16 | INIT(4), FORMATION(4), CHARGE_SET(4) |
| 성능 | 260316_260320_05_현혜정_6330mAh_LWN 25P(after LT50cy) 0.5C-10mi | 1 | 23 | HYSTERESIS_DCHG(9), HYSTERESIS_CHG(9), CHG_DCHG(4), INIT(1) |
| 성능 | 260316_270318_00_이성일_5882mAh_M47 ATL ECT GITT | 2 | 244 | GITT_PULSE(2), REST_LONG(2), TERMINATION(2) |
| 성능 | 260316_270318_00_이성일_5882mAh_M47 ATL ECT parameter1 | 1 | 45 | RPT(8), REST_LONG(3), ACCEL(1), CHARGE_SET(1), POWER_CHG(1), DCHG_SET(1), TERMINATION(1) |
| 성능 | 260316_270318_00_이성일_5882mAh_M47 ATL ECT parameter10 | 2 | 94 | REST_LONG(6), RPT(6), ACCEL(2), CHARGE_SET(2), FORMATION(2), CHG_DCHG(2), DCHG_SET(2), TERMINATION(2) |
| 성능 | 260316_270318_00_이성일_5882mAh_M47 ATL ECT parameter2 | 1 | 45 | RPT(5), CHG_DCHG(3), REST_LONG(3), ACCEL(1), CHARGE_SET(1), POWER_CHG(1), DCHG_SET(1), TERMINATION(1) |
| 성능 | 260316_270318_00_이성일_5882mAh_M47 ATL ECT parameter3 | 1 | 45 | RPT(5), CHG_DCHG(4), REST_LONG(3), ACCEL(1), CHARGE_SET(1), DCHG_SET(1), TERMINATION(1) |
| 성능 | 260316_270318_00_이성일_5882mAh_M47 ATL ECT parameter4 | 1 | 45 | RPT(6), REST_LONG(3), POWER_CHG(3), ACCEL(1), CHARGE_SET(1), CHG_DCHG(1), TERMINATION(1) |
| 성능 | 260316_270318_00_이성일_5882mAh_M47 ATL ECT parameter5 | 1 | 45 | RPT(7), REST_LONG(3), CHG_DCHG(2), ACCEL(1), CHARGE_SET(1), POWER_CHG(1), TERMINATION(1) |
| 성능 | 260316_270318_00_이성일_5882mAh_M47 ATL ECT parameter6 | 1 | 45 | RPT(5), CHG_DCHG(4), REST_LONG(3), ACCEL(1), CHARGE_SET(1), DCHG_SET(1), TERMINATION(1) |
| 성능 | 260316_270318_00_이성일_5882mAh_M47 ATL ECT parameter7 | 1 | 45 | RPT(5), CHG_DCHG(3), REST_LONG(3), ACCEL(1), CHARGE_SET(1), POWER_CHG(1), DCHG_SET(1), TERMINATION(1) |
| 성능 | 260316_270318_00_이성일_5882mAh_M47 ATL ECT parameter8 | 1 | 45 | RPT(5), CHG_DCHG(3), REST_LONG(3), ACCEL(1), CHARGE_SET(1), POWER_CHG(1), DCHG_SET(1), TERMINATION(1) |
| 성능 | 260316_270318_00_이성일_5882mAh_M47 ATL ECT parameter9 | 1 | 45 | RPT(5), REST_LONG(3), CHG_DCHG(2), POWER_CHG(2), ACCEL(1), CHARGE_SET(1), DCHG_SET(1), TERMINATION(1) |
| 성능 | 260317_260325_05_현혜정_4986mAh_SDI Gen5+ MP1 0.2C-10min volt h | 1 | 23 | HYSTERESIS_DCHG(9), HYSTERESIS_CHG(9), RPT(4), INIT(1) |
| 성능 | 260319_260326_05_현혜정_6330mAh_LWN 25P(after LT50cy) 0.2C-10mi | 1 | 23 | HYSTERESIS_DCHG(9), HYSTERESIS_CHG(9), RPT(4), INIT(1) |
| 성능 | 260326_260329_00_류성택_4860mAh_A17 ATL ECT parameter1 | 3 | 135 | RPT(24), REST_LONG(9), ACCEL(3), CHARGE_SET(3), POWER_CHG(3), DCHG_SET(3), TERMINATION(3) |
| 성능 | 260326_260329_00_류성택_4860mAh_A17 ATL ECT parameter10 | 2 | 92 | REST_LONG(6), RPT(6), ACCEL(2), FORMATION(2), CHG_DCHG(2), DCHG_SET(2), TERMINATION(2) |
| 성능 | 260326_260329_00_류성택_4860mAh_A17 ATL ECT parameter11 GITT | 2 | 244 | GITT_PULSE(2), REST_LONG(2), TERMINATION(2) |
| 성능 | 260326_260329_00_류성택_4860mAh_A17 ATL ECT parameter2 | 3 | 135 | RPT(15), CHG_DCHG(9), REST_LONG(9), ACCEL(3), CHARGE_SET(3), POWER_CHG(3), DCHG_SET(3), TERMINATION(3) |
| 성능 | 260326_260329_00_류성택_4860mAh_A17 ATL ECT parameter3 | 3 | 135 | RPT(15), CHG_DCHG(12), REST_LONG(9), ACCEL(3), CHARGE_SET(3), DCHG_SET(3), TERMINATION(3) |
| 성능 | 260326_260329_00_류성택_4860mAh_A17 ATL ECT parameter4 | 3 | 135 | RPT(18), REST_LONG(9), POWER_CHG(9), ACCEL(3), CHARGE_SET(3), DCHG_SET(3), TERMINATION(3) |
| 성능 | 260326_260329_00_류성택_4860mAh_A17 ATL ECT parameter5 | 3 | 135 | RPT(21), REST_LONG(9), ACCEL(3), CHARGE_SET(3), CHG_DCHG(3), DCHG_SET(3), POWER_CHG(3), TERMINATION(3) |
| 성능 | 260326_260329_00_류성택_4860mAh_A17 ATL ECT parameter6 | 3 | 135 | RPT(15), CHG_DCHG(12), REST_LONG(9), ACCEL(3), CHARGE_SET(3), DCHG_SET(3), TERMINATION(3) |
| 성능 | 260326_260329_00_류성택_4860mAh_A17 ATL ECT parameter7 | 3 | 135 | RPT(15), CHG_DCHG(9), REST_LONG(9), ACCEL(3), CHARGE_SET(3), POWER_CHG(3), DCHG_SET(3), TERMINATION(3) |
| 성능 | 260326_260329_00_류성택_4860mAh_A17 ATL ECT parameter8 | 3 | 135 | RPT(15), CHG_DCHG(9), REST_LONG(9), ACCEL(3), CHARGE_SET(3), POWER_CHG(3), DCHG_SET(3), TERMINATION(3) |
| 성능 | 260326_260329_00_류성택_4860mAh_A17 ATL ECT parameter9 | 2 | 90 | RPT(10), REST_LONG(6), DCHG_SET(4), POWER_CHG(4), ACCEL(2), CHARGE_SET(2), CHG_DCHG(2), TERMINATION(2) |
| 성능 | 260326_260329_00_류성택_4860mAh_A17 SDI ECT parameter1 | 2 | 90 | RPT(16), REST_LONG(6), ACCEL(2), CHARGE_SET(2), POWER_CHG(2), DCHG_SET(2), TERMINATION(2) |
| 성능 | 260326_260329_00_류성택_4860mAh_A17 SDI ECT parameter11 GITT | 2 | 244 | GITT_PULSE(2), REST_LONG(2), TERMINATION(2) |
| 성능 | 260326_260329_00_류성택_4860mAh_A17 SDI ECT parameter2 | 2 | 90 | RPT(10), CHG_DCHG(6), REST_LONG(6), ACCEL(2), CHARGE_SET(2), POWER_CHG(2), DCHG_SET(2), TERMINATION(2) |
| 성능 | 260326_260329_00_류성택_4860mAh_A17 SDI ECT parameter3 | 2 | 90 | RPT(10), CHG_DCHG(8), REST_LONG(6), ACCEL(2), CHARGE_SET(2), DCHG_SET(2), TERMINATION(2) |
| 성능 | 260326_260329_00_류성택_4860mAh_A17 SDI ECT parameter4 | 2 | 90 | RPT(12), REST_LONG(6), POWER_CHG(6), ACCEL(2), CHARGE_SET(2), DCHG_SET(2), TERMINATION(2) |
| 성능 | 260326_260329_00_류성택_4860mAh_A17 SDI ECT parameter5 | 2 | 90 | RPT(14), REST_LONG(6), ACCEL(2), CHARGE_SET(2), CHG_DCHG(2), DCHG_SET(2), POWER_CHG(2), TERMINATION(2) |
| 성능 | 260326_260329_00_류성택_4860mAh_A17 SDI ECT parameter6 | 2 | 90 | RPT(10), CHG_DCHG(8), REST_LONG(6), ACCEL(2), CHARGE_SET(2), DCHG_SET(2), TERMINATION(2) |
| 성능 | 260326_270326_00_류성택_4860mAh_A17 SDI ECT Parameter10 | 2 | 92 | REST_LONG(6), RPT(6), ACCEL(2), FORMATION(2), CHG_DCHG(2), DCHG_SET(2), TERMINATION(2) |
| 성능 | 260326_270326_00_류성택_4860mAh_A17 SDI ECT Parameter7 | 2 | 90 | RPT(10), CHG_DCHG(6), REST_LONG(6), ACCEL(2), CHARGE_SET(2), POWER_CHG(2), DCHG_SET(2), TERMINATION(2) |
| 성능 | 260326_270326_00_류성택_4860mAh_A17 SDI ECT Parameter8 | 2 | 90 | RPT(10), CHG_DCHG(6), REST_LONG(6), ACCEL(2), CHARGE_SET(2), POWER_CHG(2), DCHG_SET(2), TERMINATION(2) |
| 성능 | 260326_270326_00_류성택_4860mAh_A17 SDI ECT Parameter9 | 2 | 90 | RPT(10), REST_LONG(6), DCHG_SET(4), POWER_CHG(4), ACCEL(2), CHARGE_SET(2), CHG_DCHG(2), TERMINATION(2) |
| 성능 | 260327_270405_00_이성일_5882mAh_ATL M47 ECT parameter1 RT | 2 | 30 | RPT(16), REST_LONG(6), CHARGE_SET(2), POWER_CHG(2), DCHG_SET(2), TERMINATION(2) |
| 성능 | 260327_270405_00_이성일_5882mAh_ATL M47 ECT parameter10 RT | 2 | 34 | REST_LONG(6), RPT(6), CHARGE_SET(2), FORMATION(2), CHG_DCHG(2), DCHG_SET(2), TERMINATION(2) |
| 성능 | 260327_270405_00_이성일_5882mAh_ATL M47 ECT parameter2 RT | 2 | 30 | RPT(10), CHG_DCHG(6), REST_LONG(6), CHARGE_SET(2), POWER_CHG(2), DCHG_SET(2), TERMINATION(2) |
| 성능 | 260327_270405_00_이성일_5882mAh_ATL M47 ECT parameter3 RT | 2 | 30 | RPT(10), CHG_DCHG(8), REST_LONG(6), CHARGE_SET(2), DCHG_SET(2), TERMINATION(2) |
| 성능 | 260327_270405_00_이성일_5882mAh_ATL M47 ECT parameter4 RT | 2 | 30 | RPT(12), REST_LONG(6), POWER_CHG(6), CHARGE_SET(2), CHG_DCHG(2), TERMINATION(2) |
| 성능 | 260327_270405_00_이성일_5882mAh_ATL M47 ECT parameter5 RT | 2 | 30 | RPT(14), REST_LONG(6), CHG_DCHG(4), CHARGE_SET(2), POWER_CHG(2), TERMINATION(2) |
| 성능 | 260327_270405_00_이성일_5882mAh_ATL M47 ECT parameter6 RT | 2 | 30 | RPT(10), CHG_DCHG(8), REST_LONG(6), CHARGE_SET(2), DCHG_SET(2), TERMINATION(2) |
| 성능 | 260327_270405_00_이성일_5882mAh_ATL M47 ECT parameter7 RT | 2 | 30 | RPT(10), CHG_DCHG(6), REST_LONG(6), CHARGE_SET(2), POWER_CHG(2), DCHG_SET(2), TERMINATION(2) |
| 성능 | 260327_270405_00_이성일_5882mAh_ATL M47 ECT parameter8 RT | 2 | 30 | RPT(10), CHG_DCHG(6), REST_LONG(6), CHARGE_SET(2), POWER_CHG(2), DCHG_SET(2), TERMINATION(2) |
| 성능 | 260327_270405_00_이성일_5882mAh_ATL M47 ECT parameter9 RT | 2 | 30 | RPT(10), REST_LONG(6), CHG_DCHG(4), POWER_CHG(4), CHARGE_SET(2), DCHG_SET(2), TERMINATION(2) |
| 성능 | 260403_260407_00_류성택_5882mAh_ATL M47 ECT parameter1 HT | 1 | 9 | RPT(4), REST_LONG(3), DCHG_SET(1), TERMINATION(1) |
| 성능 | 260403_260407_00_류성택_5882mAh_ATL M47 ECT parameter2 HT | 1 | 9 | REST_LONG(3), RPT(2), CHG_DCHG(2), DCHG_SET(1), TERMINATION(1) |
| 성능 | 260403_260407_00_류성택_5882mAh_ATL M47 ECT parameter3 HT | 1 | 9 | REST_LONG(3), RPT(2), CHG_DCHG(2), DCHG_SET(1), TERMINATION(1) |
| 성능 | 260403_260407_00_류성택_5882mAh_ATL M47 ECT parameter4 HT | 1 | 9 | REST_LONG(3), POWER_CHG(3), RPT(2), TERMINATION(1) |
| 성능 | 260403_260407_00_류성택_5882mAh_ATL M47 ECT parameter5 HT | 1 | 9 | RPT(4), REST_LONG(3), POWER_CHG(1), TERMINATION(1) |
| 성능 | 260403_260407_00_류성택_5882mAh_ATL M47 ECT parameter6 HT | 1 | 9 | REST_LONG(3), CHG_DCHG(2), RPT(2), DCHG_SET(1), TERMINATION(1) |
| 성능 | 260403_260407_00_류성택_5882mAh_ATL M47 ECT parameter7 HT | 1 | 9 | REST_LONG(3), RPT(2), CHG_DCHG(1), POWER_CHG(1), DCHG_SET(1), TERMINATION(1) |
| 성능 | 260403_260407_00_류성택_5882mAh_ATL M47 ECT parameter8 HT | 1 | 9 | REST_LONG(3), CHG_DCHG(2), RPT(2), DCHG_SET(1), TERMINATION(1) |
| 성능 | 260403_260407_00_류성택_5882mAh_ATL M47 ECT parameter9 HT | 1 | 9 | REST_LONG(3), RPT(2), POWER_CHG(1), CHG_DCHG(1), DCHG_SET(1), TERMINATION(1) |
| 성능 | 260406_260408_00_류성택_5882mAh_ATL M47 ECT parameter10 HT | 1 | 9 | REST_LONG(3), RPT(3), CHG_DCHG(1), DCHG_SET(1), TERMINATION(1) |
| 성능 | 260406_270408_00_류성택_5882mAh_M47 ATL ECT Parameter1 LT | 1 | 6 | REST_LONG(2), RPT(2), DCHG_SET(1), TERMINATION(1) |
| 성능 | 260406_270408_00_류성택_5882mAh_M47 ATL ECT Parameter2 LT | 1 | 6 | REST_LONG(2), RPT(1), CHG_DCHG(1), DCHG_SET(1), TERMINATION(1) |
| 성능 | 260406_270408_00_류성택_5882mAh_M47 ATL ECT Parameter3 LT | 1 | 6 | REST_LONG(2), RPT(1), CHG_DCHG(1), DCHG_SET(1), TERMINATION(1) |
| 성능 | 260406_270408_00_류성택_5882mAh_M47 ATL ECT Parameter4 LT | 1 | 6 | REST_LONG(2), POWER_CHG(2), RPT(1), TERMINATION(1) |
| 성능_hysteresis | 260202_260210_05_현혜정_4875mAh_LWN Gen5 MP1-1 0.5C hysteresis | 2 | 46 | HYSTERESIS_DCHG(18), HYSTERESIS_CHG(18), CHG_DCHG(8), INIT(2) |
| 성능_hysteresis | 260212_260226_05_현혜정_4875mAh_LWN Gen5 MP1-1 0.2C hysteresis | 2 | 46 | HYSTERESIS_DCHG(18), HYSTERESIS_CHG(18), RPT(8), INIT(2) |
| 성능_hysteresis | 260213_260226_05_현혜정_5000mAh_ATL Gen5+ 2C T-2 Stack 0.2C-10m | 1 | 23 | HYSTERESIS_DCHG(9), HYSTERESIS_CHG(9), RPT(4), INIT(1) |
| 성능_hysteresis | 260224_260304_05_현혜정_5000mAh_ATL Gen5+ 2C T-2 Stack 0.2C-60m | 1 | 23 | HYSTERESIS_DCHG(9), HYSTERESIS_CHG(9), RPT(4), INIT(1) |
| 성능_hysteresis | 260224_260304_05_현혜정_6330mAh_LWN 25P(after LT100cy) 0.2C-10m | 2 | 46 | HYSTERESIS_DCHG(18), HYSTERESIS_CHG(18), RPT(8), INIT(2) |
| 성능_hysteresis | 260303_260308_05_현혜정_6330mAh_LWN 25P(after LT100cy) 0.5C-10m | 2 | 46 | HYSTERESIS_DCHG(18), HYSTERESIS_CHG(18), CHG_DCHG(8), INIT(2) |
| 성능_hysteresis | 260316_260320_05_현혜정_6330mAh_LWN 25P(after LT50cy) 0.5C-10mi | 1 | 23 | HYSTERESIS_DCHG(9), HYSTERESIS_CHG(9), CHG_DCHG(4), INIT(1) |
| 성능_hysteresis | 260317_260325_05_현혜정_4986mAh_SDI Gen5+ MP1 0.2C-10min volt h | 1 | 23 | HYSTERESIS_DCHG(9), HYSTERESIS_CHG(9), RPT(4), INIT(1) |
| 성능_hysteresis | 260319_260326_05_현혜정_6330mAh_LWN 25P(after LT50cy) 0.2C-10mi | 1 | 23 | HYSTERESIS_DCHG(9), HYSTERESIS_CHG(9), RPT(4), INIT(1) |
| 성능_hysteresis | 260326_260330_05_박성철_7750mAh_Gen6++ ATL Si25% 7750mAh voltag | 1 | 23 | HYSTERESIS_DCHG(9), HYSTERESIS_CHG(9), RPT(4), INIT(1) |
| 성능_hysteresis | 260327_260402_05_현혜정_4986mAh_SDI Gen5+ MP1 0.2C-10min volt h | 1 | 13 | RPT(12), INIT(1) |
| 성능_hysteresis | 260330_260405_05_신용호_4960mAh_Gen6+ ATL proto1차 Si 10% Hyster | 1 | 23 | HYSTERESIS_DCHG(9), HYSTERESIS_CHG(9), RPT(4), INIT(1) |
| 성능_hysteresis | 260330_260405_05_신용호_4960mAh_Gen6+ ATL proto1차 Si 15% Hyster | 1 | 23 | HYSTERESIS_DCHG(9), HYSTERESIS_CHG(9), RPT(4), INIT(1) |
| 성능_hysteresis | 260403_260410_05_박기진_4948mAh_Gen6+VB 4.57V SDI Proto1 HYSTER | 1 | 23 | HYSTERESIS_DCHG(9), HYSTERESIS_CHG(9), CHG_DCHG(4), INIT(1) |
| 성능_hysteresis | 260406_260410_05_박기진_4948mAh_Gen6+VB SDI proto1 hysteresis r | 1 | 23 | HYSTERESIS_DCHG(9), HYSTERESIS_CHG(9), RPT(4), INIT(1) |
| 성능_hysteresis | 260414_260425_05_현혜정_6330mAh_LWN 25P(after3.0C HT800cy) 0.2C | 1 | 23 | HYSTERESIS_DCHG(9), HYSTERESIS_CHG(9), RPT(4), INIT(1) |
| 성능_시험직후 | 260413_260415_00_류성택_4860mAh_A17 ATL ECT parameter04 상온 재측정 | 1 | 2 | RPT(1), CHG_DCHG(1) |
| 성능_시험직후 | 260413_260415_00_류성택_4860mAh_A17 ATL ECT parameter05 상온 재측정 | 1 | 2 | RPT(1), CHG_DCHG(1) |
| 성능_시험직후 | 260413_260415_00_류성택_4860mAh_A17 ATL ECT parameter08 0도 재측정 | 1 | 3 | RPT(1), REST_LONG(1), CHG_DCHG(1) |
| 성능_시험직후 | 260413_260415_00_류성택_4860mAh_A17 ATL ECT parameter09 상온 0도 - | 1 | 9 | RPT(4), REST_LONG(2), CHG_DCHG(1), DCHG_SET(1), TERMINATION(1) |
| 성능_시험직후 | 260413_260415_00_류성택_4860mAh_A17 SDI ECT parameter04 상온 재측정 | 1 | 2 | RPT(1), CHG_DCHG(1) |
| 성능_시험직후 | 260413_260415_00_류성택_4860mAh_A17 SDI ECT parameter05 상온 재측정 | 1 | 2 | RPT(1), CHG_DCHG(1) |
| 성능_시험직후 | 260413_260415_00_류성택_4860mAh_A17 SDI ECT parameter08 0도 재측정 | 1 | 3 | RPT(1), REST_LONG(1), CHG_DCHG(1) |
| 성능_시험직후 | 260413_260415_00_류성택_4860mAh_A17 SDI ECT parameter09 상온 0도 - | 1 | 9 | RPT(4), REST_LONG(2), CHG_DCHG(1), DCHG_SET(1), TERMINATION(1) |
| 성능_시험직후 | 260413_260415_00_류성택_5882mAh_M47 ATL ECT parameter09 LT015 재 | 1 | 6 | REST_LONG(2), RPT(1), CHG_DCHG(1), DCHG_SET(1), TERMINATION(1) |
| 성능_시험직후 | 260413_260415_00_류성택_5882mAh_M47 ATL ECT parameter10 HT 보충 | 1 | 3 | REST_LONG(1), RPT(1), CHG_DCHG(1) |
| 수명 | 251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202 | 3 | 3609 | RPT(54), ACCEL(36), INIT(3) |
| 수명 | 251029_251229_05_나무늬_2335mAh_Q8 선상 ATL SEU4 LT @1-401 | 3 | 1206 | RPT(15), ACCEL(12), INIT(3), CHARGE_SET(3) |
| 수명 | 251029_251229_05_나무늬_2935mAh_Q8 선상 ATL SEU4 LT @1-401 - 복사본 | 3 | 1206 | RPT(15), ACCEL(12), INIT(3), CHARGE_SET(3) |
| 수명 | 251029_260129_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 50CY HT @1- | 4 | 3208 | RPT(40), ACCEL(36), INIT(4), CHARGE_SET(4) |
| 수명 | 251029_260129_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 75CY HT @1- | 4 | 3208 | RPT(40), ACCEL(36), INIT(4), CHARGE_SET(4) |
| 수명 | 251029_260129_05_나무늬_2335mAh_Q8 선상 ATL SEU4 HT @1-801 | 3 | 2406 | RPT(30), ACCEL(24), INIT(3), CHARGE_SET(3) |
| 수명 | 251029_260429_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 30CY @1-120 | 6 | 7218 | RPT(108), ACCEL(78), INIT(6) |
| 수명 | 251029_260429_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 50CY @1-120 | 6 | 7218 | RPT(108), ACCEL(78), INIT(6) |
| 수명 | 251029_260429_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 75CY @1-120 | 6 | 7218 | RPT(108), ACCEL(78), INIT(6) |
| 수명 | 251029_260429_05_나무늬_Q8 선상 ATL SEU4 2.9V 30CY @1-1202 - 복사본 | 6 | 7218 | RPT(108), ACCEL(78), INIT(6) |
| 수명 | 251113_260113_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 50CY LT @1- | 3 | 1206 | RPT(15), ACCEL(15), INIT(3), CHARGE_SET(3) |
| 수명 | 251113_260213_05_나무늬_2335mAh_Q8 선상 ATL 2.9V 30CY HT @1-801 | 3 | 2406 | RPT(30), ACCEL(27), INIT(3), CHARGE_SET(3) |
| 수명 | 251209_260209_05_나무늬_2335mAh_Q8 선상 ATL SEU4 HT @301-801 | 3 | 1806 | RPT(21), ACCEL(18), INIT(3), CHARGE_SET(3) |
| 수명 | 260102_260630_03_홍승기_2335mAh_Q8 선상 ATL 2.9V 30Cy LT @1-400 | 3 | 3609 | RPT(54), ACCEL(39), INIT(3) |
| 수명 | 260115_260630_02_홍승기_2335mAh_Q8 선상 ATL SEU4 HT@1-802 | 3 | 2406 | RPT(30), ACCEL(24), INIT(3), CHARGE_SET(3) |
| 수명 | 260119_260616_03_홍승기_2369mAh_Q8 ATL Main 2.0C Rss RT | 4 | 6404 | RPT(64), PULSE_DCIR(64), ACCEL(64), INIT(4), CHARGE_SET(4) |
| 수명 | 260119_260616_03_홍승기_2485mAh_Q8 ATL Sub 2.0C Rss RT | 3 | 4803 | RPT(48), PULSE_DCIR(48), ACCEL(48), INIT(3), CHARGE_SET(3) |
| 수명 | 260119_260616_03_홍승기_2485mAh_Q8 ATL Sub 2C 2.9V 100Cy | 3 | 2406 | RPT(30), ACCEL(24), INIT(3), CHARGE_SET(3) |
| 수명 | 260130_260630_03_홍승기_2369mAh_Q8 Main 2C Rss RT CH32 57Cy-RE | 1 | 1546 | ACCEL(16), RPT(15), PULSE_DCIR(15), CHARGE_SET(1) |
| 수명 | 260130_260630_03_홍승기_Q8 Main 2C Rss RT CH32 57Cy-RE | 1 | 1546 | ACCEL(16), RPT(15), PULSE_DCIR(15), CHARGE_SET(1) |
| 수명 | 260130_260630_05_이재연_5000mAh_4.53V Gen5P ATL 2.8C 고온수명 0-160 | 8 | 4768 | RPT(56), PULSE_DCIR(48), ACCEL(48), INIT(8) |
| 수명 | A1_MP1_4500mAh_T23_1 | 2 | 1202 | ACCEL(14), RPT(12), PULSE_DCIR(12), RSS_DCIR(8), HYSTERESIS_DCHG(4), INIT(2), CHARGE_SET(2) |
| 수명 | A1_MP1_4500mAh_T23_2 | 2 | 804 | RPT(16), HYSTERESIS_DCHG(8), PULSE_DCIR(8), ACCEL(8), INIT(2), CHARGE_SET(2) |
| 수명 | A1_MP1_4500mAh_T23_3 | 2 | 2004 | RPT(44), HYSTERESIS_DCHG(20), PULSE_DCIR(20), ACCEL(20) |
| 수명_복합floating | 250116_250501_05_김영환_4905mAh_ATL Gen5 4C HT floating | 2 | 6 | INIT(2), RPT(2), FLOATING(2) |
| 수명_복합floating | 250823_251231_05_김영환_5060mAh_LGES Gen5+ proto2 1C Floating | 2 | 6 | INIT(2), RPT(2), FLOATING(2) |
| 수명_복합floating | 251128_260630_05_김영환_5060mAh_LGES Gen5 MP1 main 1C HT Floati | 2 | 6 | INIT(2), RPT(2), FLOATING(2) |
| 수명_복합floating | 260126_260531_01_최웅철_4981mAh_GB6 PRO16 ATL GEN4 1.3C 고온복합 | 2 | 212 | FORMATION(24), RPT(24), CHARGE_SET(22), PULSE_DCIR(22), DCHG_SET(2) |
| 수명_복합floating | 260126_260531_01_최웅철_4981mAh_GB6 PRO16 SDI GEN4 1.3C 고온복합 | 2 | 212 | FORMATION(24), RPT(24), CHARGE_SET(22), PULSE_DCIR(22), DCHG_SET(2) |
| 수명_복합floating | 260130_260531_01_최웅철_2485mAh_Q8 SUB SDI GEN5+B 2C 고온복합 | 2 | 394 | FORMATION(44), RPT(44), CHARGE_SET(42), PULSE_DCIR(42), DCHG_SET(2) |
| 수명_복합floating | 260203_260531_01_최웅철_4268mAh_SDI GB6 PRO14 GEN4 1.3C 고온복합 | 2 | 208 | FORMATION(24), RPT(24), CHARGE_SET(22), PULSE_DCIR(22), DCHG_SET(2) |
| 수명_복합floating | 260223_260531_01_최웅철_2369mAh_Q8main ATL GEN5+B 2.0C 고온복합 | 2 | 394 | FORMATION(44), RPT(44), CHARGE_SET(42), PULSE_DCIR(42), DCHG_SET(2) |
| 수명_복합floating | 260223_260531_01_최웅철_2369mAh_Q8main COSMX GEN5+B 2.0C 고온복합 | 2 | 394 | FORMATION(44), RPT(44), CHARGE_SET(42), PULSE_DCIR(42), DCHG_SET(2) |
| 수명_복합floating | 260223_260531_01_최웅철_2485mAh_Q8 sub ATL GEN5+B 2.0C 고온복합 | 2 | 436 | FORMATION(44), RPT(44), CHARGE_SET(42), PULSE_DCIR(42), DCHG_SET(2) |
| 수명_복합floating | 260309_260731_01_최웅철_2485mAh_Q8 sub SDI GEN5+B 2.0C 고온복합 | 2 | 436 | FORMATION(44), RPT(44), CHARGE_SET(42), PULSE_DCIR(42), DCHG_SET(2) |
| 수명_복합floating | 260320_260923_03_안성진_251mAh_HaeanProtoDOE복합Floating | 4 | 140 | CHG_DCHG(16), RPT(8), UNKNOWN(8), INIT(4) |
| 수명_복합floating | 260320_260923_03_안성진_251mAh_HaeanProtoDOE일반Floating | 4 | 4004 | INIT(4), RPT(4), FLOATING(4) |
| 수명_복합floating | 260320_260923_03_안성진_251mAh_HaeanProtoDOE일반FloatingRe | 4 | 4004 | INIT(4), RPT(4), FLOATING(4) |
| 수명_복합floating | 260320_260923_03_안성진_251mAh_HaeanProtoMain복합Floating | 4 | 140 | CHG_DCHG(16), RPT(8), UNKNOWN(8), INIT(4) |
| 수명_복합floating | 260320_260923_03_안성진_251mAh_HaeanProtoMain일반Floating | 4 | 4004 | INIT(4), RPT(4), FLOATING(4) |
| 수명_복합floating | 260320_260923_03_안성진_251mAh_HaeanProtoMain일반FloatingRe | 4 | 4004 | INIT(4), RPT(4), FLOATING(4) |
| 수명_복합floating | 260413_260930_05_김영환_3365mAh_Gen6+VB ATL Proto1 고온복합Floating | 2 | 678 | RPT(44), PULSE_DCIR(44), UNKNOWN(42), INIT(2) |
| 수명_복합floating | 260413_260930_05_박기진_4948mAh_Gen6+VB SDI Proto1 고온복합Floating | 4 | 1356 | RPT(88), PULSE_DCIR(88), UNKNOWN(84), INIT(4) |
| 수명_복합floating | 260413_261230_05_문현규_3650mAh_Cosmx 25SiC 타사spl floating ch55 | 2 | 6 | INIT(2), RPT(2), FLOATING(2) |
| 수명_복합floating | 260413_261230_05_문현규_3650mAh_Cosmx 25SiC 타사spl 복합floating ch | 2 | 422 | RPT(42), CHARGE_SET(42), PULSE_DCIR(42), CHG_DCHG(42), FORMATION(42), INIT(2) |

## 5. 폴더명 ↔ 카테고리 정합성 의심 list

폴더명에 키워드는 있는데 해당 카테고리가 0인 케이스:

| 시험종류 | 폴더 | 키워드 | 발견 카테고리 |
|---|---|---|---|
| 성능_hysteresis | 260327_260402_05_현혜정_4986mAh_SDI Gen5+ MP1 0.2C-10min volt h | `hysteresis` | RPT(12), INIT(1) |
| 수명 | 260119_260616_03_홍승기_2369mAh_Q8 ATL Main 2.0C Rss RT | `rss` | RPT(64), PULSE_DCIR(64), ACCEL(64) |
| 수명 | 260119_260616_03_홍승기_2485mAh_Q8 ATL Sub 2.0C Rss RT | `rss` | RPT(48), PULSE_DCIR(48), ACCEL(48) |
| 수명 | 260130_260630_03_홍승기_2369mAh_Q8 Main 2C Rss RT CH32 57Cy-RE | `rss` | ACCEL(16), RPT(15), PULSE_DCIR(15) |
| 수명 | 260130_260630_03_홍승기_Q8 Main 2C Rss RT CH32 57Cy-RE | `rss` | ACCEL(16), RPT(15), PULSE_DCIR(15) |
| 수명_복합floating | 260320_260923_03_안성진_251mAh_HaeanProtoDOE복합Floating | `floating` | CHG_DCHG(16), RPT(8), UNKNOWN(8) |
| 수명_복합floating | 260320_260923_03_안성진_251mAh_HaeanProtoMain복합Floating | `floating` | CHG_DCHG(16), RPT(8), UNKNOWN(8) |
| 수명_복합floating | 260413_260930_05_김영환_3365mAh_Gen6+VB ATL Proto1 고온복합Floating | `floating` | RPT(44), PULSE_DCIR(44), UNKNOWN(42) |
| 수명_복합floating | 260413_260930_05_박기진_4948mAh_Gen6+VB SDI Proto1 고온복합Floating | `floating` | RPT(88), PULSE_DCIR(88), UNKNOWN(84) |
| 수명_복합floating | 260413_261230_05_문현규_3650mAh_Cosmx 25SiC 타사spl 복합floating ch | `floating` | RPT(42), CHARGE_SET(42), PULSE_DCIR(42) |

## 7. 분류기 v2 spec 적용 사항 (Phase 0-5)

1. ⚠️ **`v_chg` 키 mismatch fix** (Phase 0-1a) — L8053 `v_chg_mV/v_chg` → `voltage_mV` 사용.
   FLOATING 카테고리 분류 활성화.
2. **CC vs CCCV V cutoff 분리** (사용자 통찰):
   - CC mode: `+28 end_voltage_mV` = 실제 cutoff
   - CCCV mode: `+12 voltage_mV` = CC target = CV target
3. **9 신규 field parser 추가** — `v_safety_upper/lower_mV`, `i_safety_upper/lower_mA`, `chg/dchg_end_capacity_cutoff_mAh`, `record_interval_s`, `chamber_temp_c`, `mode_flag`, header `format_version`/`header_record_count`/`block_count_meta`/`schedule_description`.
4. **Schedule keyword classifier** (header `+664`) — hysteresis/gitt/ect/floating/rss/dcir/rpt/formation prior.
5. **`+336 < 5` short_sampling hint** — GITT_PULSE / PULSE_DCIR sub-tag.
