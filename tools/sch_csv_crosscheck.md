# CSV ↔ .sch Cross-check (Phase 0-1c)

> 사용자 제공 PNE 패턴 CSV 10개 ↔ .sch 9개 매칭 검증.

## Gen5+B 2335mAh 2C Si Hybrid 상온 RT.csv

- CSV: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\pattern\Gen5+B 2335mAh 2C Si Hybrid 상온 RT.csv`
- .sch target: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\수명\251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202`
- .sch resolved: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\수명\251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202\M01Ch008[008]\251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202.sch`

**CSV Summary**
- Sections: ['Model name', 'Schedule', 'Safety Condition', 'Step']
- Schedule: {'Schedule Name': '???一?????匠?祈牢摩묠뿳A', 'User': '', 'Make Time': '?????뼠샀????5', 'Description': '????匠???株日'}
- Safety: {'Voltage upper': '4.6 V', 'Voltage lower': '2.35 V', 'Current upper': '12.0 A', 'Current lower': '0.0 A', 'Capacity upper': '2.569 Ah', 'Capacity lower': '0.0 Ah', 'Temperature upper': '60.0 °C', 'Temperature lower': '0.0 °C'}
- Steps n=179, type_count={'Cycle': 24, 'DisCharge': 33, 'Rest': 47, 'Loop': 24, 'Charge': 50, '완료': 1}

**.sch Summary**
- Steps n=178, type_count={'DCHG_CC': 33, 'REST': 47, 'LOOP': 24, 'REST_SAFE': 23, 'CHG_CCCV': 32, 'CHG_CC': 18, 'GOTO': 1}
- capacity_limit_mAh (+104) = 2569.0

**Cross-check**

| Field | CSV | .sch | Match |
|---|---|---|---|
| n_steps | 179 | 178 | ❌ |
| capacity_mAh (CSV Capacity upper vs sch +104) | 2569.0 | 2569.0 | ✅ |

---

## Ref_Gen5+B 2335 mAh 2C Si Hybrid 상온.csv

- CSV: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\pattern\Ref_Gen5+B 2335 mAh 2C Si Hybrid 상온.csv`
- .sch target: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\수명\251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202`
- .sch resolved: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\수명\251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202\M01Ch008[008]\251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202.sch`

**CSV Summary**
- Sections: ['Model name', 'Schedule', 'Safety Condition', 'Step']
- Schedule: {'Schedule Name': '???一?????匠?祈牢摩묠뿳A', 'User': '', 'Make Time': '?????뼠죀????0', 'Description': '????匠???株日'}
- Safety: {'Voltage upper': '4.6 V', 'Voltage lower': '2.45 V', 'Current upper': '12.0 A', 'Current lower': '0.0 A', 'Capacity upper': '2.569 Ah', 'Capacity lower': '0.0 Ah', 'Temperature upper': '60.0 °C', 'Temperature lower': '0.0 °C'}
- Steps n=179, type_count={'Cycle': 24, 'DisCharge': 33, 'Rest': 47, 'Loop': 24, 'Charge': 50, '완료': 1}

**.sch Summary**
- Steps n=178, type_count={'DCHG_CC': 33, 'REST': 47, 'LOOP': 24, 'REST_SAFE': 23, 'CHG_CCCV': 32, 'CHG_CC': 18, 'GOTO': 1}
- capacity_limit_mAh (+104) = 2569.0

**Cross-check**

| Field | CSV | .sch | Match |
|---|---|---|---|
| n_steps | 179 | 178 | ❌ |
| capacity_mAh (CSV Capacity upper vs sch +104) | 2569.0 | 2569.0 | ✅ |

---

## Ref_4.53V_Si_5000mAh 0.2C recovery capacity 4cycle SOC30 setting.csv

- CSV: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\pattern\Ref_4.53V_Si_5000mAh 0.2C recovery capacity 4cycle SOC30 setting.csv`
- .sch target: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\성능\260109_260112_05_이근준_5000mAh_Gen5P Si5 ATL T2 3M 보관 용량 측정 4cycle SOC 30 setting ch7 to 12\M01Ch007[007]\260109_260112_05_이근준_5000mAh_Gen5P Si5 ATL T2 3M 보관 용량 측정 4cycle SOC 30 setting ch7 to 12.sch`
- .sch resolved: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\성능\260109_260112_05_이근준_5000mAh_Gen5P Si5 ATL T2 3M 보관 용량 측정 4cycle SOC 30 setting ch7 to 12\M01Ch007[007]\260109_260112_05_이근준_5000mAh_Gen5P Si5 ATL T2 3M 보관 용량 측정 4cycle SOC 30 setting ch7 to 12.sch`

**CSV Summary**
- Sections: ['Model name', 'Schedule', 'Safety Condition', 'Step']
- Schedule: {'Schedule Name': '??彖楓???桁?金?敲??????瑩???敬匠???瑥??', 'User': '', 'Make Time': '?????뼠샀??特呼5', 'Description': '?????????????嘶???????????????????卓′???瘠??'}
- Safety: {'Voltage upper': '4.58 V', 'Voltage lower': '2.35 V', 'Current upper': '15.0 A', 'Current lower': '0.0 A', 'Capacity upper': '5.5 Ah', 'Capacity lower': '0.0 Ah', 'Temperature upper': '60.0 °C', 'Temperature lower': '0.0 °C'}
- Steps n=15, type_count={'Cycle': 3, 'DisCharge': 2, 'Rest': 4, 'Loop': 3, 'Charge': 2, '완료': 1}

**.sch Summary**
- Steps n=14, type_count={'DCHG_CC': 2, 'REST': 4, 'LOOP': 3, 'REST_SAFE': 2, 'CHG_CCCV': 1, 'CHG_CC': 1, 'GOTO': 1}
- capacity_limit_mAh (+104) = 5500.0

**Cross-check**

| Field | CSV | .sch | Match |
|---|---|---|---|
| n_steps | 15 | 14 | ❌ |
| capacity_mAh (CSV Capacity upper vs sch +104) | 5500.0 | 5500.0 | ✅ |

---

## Ref_4.55V Floating 2688mAh +120D.csv

- CSV: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\pattern\Ref_4.55V Floating 2688mAh +120D.csv`
- .sch target: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\성능\260112_260312_03_나무늬_2688mAh_Gen5+B SDI MP2 2.0C EPF HT Floating + 120D\M01Ch057[057]\260112_260312_03_나무늬_2688mAh_Gen5+B SDI MP2 2.0C EPF HT Floating + 120D.sch`
- .sch resolved: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\성능\260112_260312_03_나무늬_2688mAh_Gen5+B SDI MP2 2.0C EPF HT Floating + 120D\M01Ch057[057]\260112_260312_03_나무늬_2688mAh_Gen5+B SDI MP2 2.0C EPF HT Floating + 120D.sch`

**CSV Summary**
- Sections: ['Model name', 'Schedule', 'Safety Condition', 'Step']
- Schedule: {'Schedule Name': '???????一?洸桁?株?', 'User': '', 'Make Time': '?????뼠샀???呼5', 'Description': '??'}
- Safety: {'Voltage upper': '4.6 V', 'Voltage lower': '2.5 V', 'Current upper': '10.0 A', 'Current lower': '0.0 A', 'Capacity upper': '4.032 Ah', 'Capacity lower': '0.0 Ah', 'Temperature upper': '60.0 °C', 'Temperature lower': '0.0 °C'}
- Steps n=5, type_count={'Cycle': 1, 'Charge': 1, 'Rest': 1, 'Loop': 1, '완료': 1}

**.sch Summary**
- Steps n=4, type_count={'CHG_CCCV': 1, 'REST': 1, 'LOOP': 1, 'GOTO': 1}
- capacity_limit_mAh (+104) = 4032.0

**Cross-check**

| Field | CSV | .sch | Match |
|---|---|---|---|
| n_steps | 5 | 4 | ❌ |
| capacity_mAh (CSV Capacity upper vs sch +104) | 4032.0 | 4032.0 | ✅ |

---

## Ref_4.55V_Q8 Sub_2485mAh 2C Rss 2step 방전 3.0V 0-1600cyc SEU4.csv

- CSV: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\pattern\Ref_4.55V_Q8 Sub_2485mAh 2C Rss 2step 방전 3.0V 0-1600cyc SEU4.csv`
- .sch target: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\수명\260119_260616_03_홍승기_2485mAh_Q8 ATL Sub 2.0C Rss RT\M02Ch069[069]\260119_260616_03_홍승기_2485mAh_Q8 ATL Sub 2.0C Rss RT.sch`
- .sch resolved: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\수명\260119_260616_03_홍승기_2485mAh_Q8 ATL Sub 2.0C Rss RT\M02Ch069[069]\260119_260616_03_홍승기_2485mAh_Q8 ATL Sub 2.0C Rss RT.sch`

**CSV Summary**
- Sections: ['Model name', 'Schedule', 'Safety Condition', 'Step']
- Schedule: {'Schedule Name': '??彖?匠???洵桁一?獒??整?????????????', 'User': '', 'Make Time': '?????뼠샀????3', 'Description': '?????????????嘶??????????????????卒?쀠볥룶???1'}
- Safety: {'Voltage upper': '4.6 V', 'Voltage lower': '2.495 V', 'Current upper': '15.0 A', 'Current lower': '0.0 A', 'Capacity upper': '2.734 Ah', 'Capacity lower': '0.0 Ah', 'Temperature upper': '0.0 °C', 'Temperature lower': '0.0 °C'}
- Steps n=216, type_count={'Cycle': 20, 'DisCharge': 73, 'Rest': 62, 'Loop': 20, 'Charge': 40, '완료': 1}

**.sch Summary**
- Steps n=215, type_count={'DCHG_CC': 73, 'REST': 62, 'LOOP': 20, 'REST_SAFE': 19, 'CHG_CCCV': 28, 'CHG_CC': 12, 'GOTO': 1}
- capacity_limit_mAh (+104) = 2734.0

**Cross-check**

| Field | CSV | .sch | Match |
|---|---|---|---|
| n_steps | 216 | 215 | ❌ |
| capacity_mAh (CSV Capacity upper vs sch +104) | 2734.0 | 2734.0 | ✅ |

---

## Ref_4755mAh_ECT 패턴1 ACT 가변.csv

- CSV: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\pattern\Ref_4755mAh_ECT 패턴1 ACT 가변.csv`
- .sch target: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\성능\250827_251028_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter1`
- .sch resolved: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\성능\250827_251028_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter1\M01Ch009[009]\250827_251028_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter1.sch`

**CSV Summary**
- Sections: ['Model name', 'Schedule', 'Safety Condition', 'Step']
- Schedule: {'Schedule Name': '??????탆쿅????꾺', 'User': '', 'Make Time': '?????뼠샀????5', 'Description': '?????V'}
- Safety: {'Voltage upper': '4.55 V', 'Voltage lower': '2.5 V', 'Current upper': '20.0 A', 'Current lower': '0.0 A', 'Capacity upper': '5.04 Ah', 'Capacity lower': '0.0 Ah', 'Temperature upper': '0.0 °C', 'Temperature lower': '0.0 °C'}
- Steps n=128, type_count={'Cycle': 21, 'Charge': 21, 'Rest': 47, 'DisCharge': 17, 'Loop': 21, '완료': 1}

**.sch Summary**
- Steps n=127, type_count={'CHG_CC': 2, 'CHG_CCCV': 19, 'REST': 47, 'DCHG_CC': 17, 'LOOP': 21, 'REST_SAFE': 20, 'GOTO': 1}
- capacity_limit_mAh (+104) = 5040.0

**Cross-check**

| Field | CSV | .sch | Match |
|---|---|---|---|
| n_steps | 128 | 127 | ❌ |
| capacity_mAh (CSV Capacity upper vs sch +104) | 5040.0 | 5040.0 | ✅ |

---

## Ref_5882mAh_ECT 패턴11 GITT.csv

- CSV: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\pattern\Ref_5882mAh_ECT 패턴11 GITT.csv`
- .sch target: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\성능\260316_270318_00_이성일_5882mAh_M47 ATL ECT GITT\M01Ch005[005]\260316_270318_00_이성일_5882mAh_M47 ATL ECT GITT.sch`
- .sch resolved: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\성능\260316_270318_00_이성일_5882mAh_M47 ATL ECT GITT\M01Ch005[005]\260316_270318_00_이성일_5882mAh_M47 ATL ECT GITT.sch`

**CSV Summary**
- Sections: ['Model name', 'Schedule', 'Safety Condition', 'Step']
- Schedule: {'Schedule Name': '?勞????탆쿅ㄱ??T', 'User': '', 'Make Time': '?????뼠샀????1', 'Description': '?????'}
- Safety: {'Voltage upper': '4.7 V', 'Voltage lower': '1.8 V', 'Current upper': '20.0 A', 'Current lower': '0.0 A', 'Capacity upper': '6.195 Ah', 'Capacity lower': '0.0 Ah', 'Temperature upper': '0.0 °C', 'Temperature lower': '0.0 °C'}
- Steps n=29, type_count={'Cycle': 7, 'Charge': 2, 'Rest': 8, 'DisCharge': 4, 'Loop': 7, '완료': 1}

**.sch Summary**
- Steps n=28, type_count={'CHG_CCCV': 1, 'REST': 8, 'DCHG_CC': 4, 'GITT_START': 4, 'GITT_END': 3, 'CHG_CC': 1, 'REST_SAFE': 3, 'LOOP': 3, 'GOTO': 1}
- capacity_limit_mAh (+104) = 6195.0

**Cross-check**

| Field | CSV | .sch | Match |
|---|---|---|---|
| n_steps | 29 | 28 | ❌ |
| capacity_mAh (CSV Capacity upper vs sch +104) | 6195.0 | 6195.0 | ✅ |

---

## Ref_LWN 6490mAh Si25P 율별Profile.csv

- CSV: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\pattern\Ref_LWN 6490mAh Si25P 율별Profile.csv`
- .sch target: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\성능\251209_251213_05_현혜정_6490mAh_LWN Si25P SPL 율별방전Profile\M01Ch030[030]\251209_251213_05_현혜정_6490mAh_LWN Si25P SPL 율별방전Profile.sch`
- .sch resolved: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\성능\251209_251213_05_현혜정_6490mAh_LWN Si25P SPL 율별방전Profile\M01Ch030[030]\251209_251213_05_현혜정_6490mAh_LWN Si25P SPL 율별방전Profile.sch`

**CSV Summary**
- Sections: ['Model name', 'Schedule', 'Safety Condition', 'Step']
- Schedule: {'Schedule Name': '??????楓??닀낺?景?e', 'User': '', 'Make Time': '?????뼠샀??ㄵ?5', 'Description': ''}
- Safety: {'Voltage upper': '4.6 V', 'Voltage lower': '2.5 V', 'Current upper': '10.0 A', 'Current lower': '0.0 A', 'Capacity upper': '7.139 Ah', 'Capacity lower': '0.0 Ah', 'Temperature upper': '60.0 °C', 'Temperature lower': '0.0 °C'}
- Steps n=35, type_count={'Cycle': 6, 'DisCharge': 6, 'Rest': 11, 'Loop': 6, 'Charge': 5, '완료': 1}

**.sch Summary**
- Steps n=34, type_count={'DCHG_CC': 6, 'REST': 11, 'LOOP': 6, 'REST_SAFE': 5, 'CHG_CCCV': 5, 'GOTO': 1}
- capacity_limit_mAh (+104) = 7139.0

**Cross-check**

| Field | CSV | .sch | Match |
|---|---|---|---|
| n_steps | 35 | 34 | ❌ |
| capacity_mAh (CSV Capacity upper vs sch +104) | 7139.0 | 7139.0 | ✅ |

---

## Ref_SOC별 DCIR 충방전_2610mAh.csv

- CSV: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\pattern\Ref_SOC별 DCIR 충방전_2610mAh.csv`
- .sch target: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\성능\250513_250526_05_나무늬_2610mAh_Gen5+B SDI MP1 Main SBR 0.9 DCIR\M01Ch037[037]\250513_250526_05_나무늬_2610mAh_Gen5+B SDI MP1 Main SBR 0.9 DCIR.sch`
- .sch resolved: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\성능\250513_250526_05_나무늬_2610mAh_Gen5+B SDI MP1 Main SBR 0.9 DCIR\M01Ch037[037]\250513_250526_05_나무늬_2610mAh_Gen5+B SDI MP1 Main SBR 0.9 DCIR.sch`

**CSV Summary**
- Sections: ['Model name', 'Schedule', 'Safety Condition', 'Step']
- Schedule: {'Schedule Name': '?멃???쌠맦샦????h', 'User': '', 'Make Time': '?????뼠샀????3', 'Description': '??????金?異?????敲??????????金?????┰???┰ㄺ???┵??????⁴봲냃￡'}
- Safety: {'Voltage upper': '4.75 V', 'Voltage lower': '1.9 V', 'Current upper': '10.0 A', 'Current lower': '0.0 A', 'Capacity upper': '2.871 Ah', 'Capacity lower': '0.0 Ah', 'Temperature upper': '60.0 °C', 'Temperature lower': '0.0 °C'}
- Steps n=106, type_count={'Cycle': 9, 'DisCharge': 30, 'Loop': 9, 'Charge': 29, 'Rest': 28, '완료': 1}

**.sch Summary**
- Steps n=105, type_count={'DCHG_CC': 30, 'LOOP': 9, 'REST_SAFE': 8, 'CHG_CCCV': 29, 'REST': 28, 'GOTO': 1}
- capacity_limit_mAh (+104) = 2871.0

**Cross-check**

| Field | CSV | .sch | Match |
|---|---|---|---|
| n_steps | 106 | 105 | ❌ |
| capacity_mAh (CSV Capacity upper vs sch +104) | 2871.0 | 2871.0 | ✅ |

---

## Ref_율별용량 5075mAh+ hybrid.csv

- CSV: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\pattern\Ref_율별용량 5075mAh+ hybrid.csv`
- .sch target: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\성능\260202_260226_05_문현규_5075mAh_Cosmx 25Si 율별용량+Hybrid ch54\M01Ch054[054]\260202_260226_05_문현규_5075mAh_Cosmx 25Si 율별용량+Hybrid ch54.sch`
- .sch resolved: `C:\Users\Ryu\battery\python\BDT_dev\raw\raw_exp\exp_data\성능\260202_260226_05_문현규_5075mAh_Cosmx 25Si 율별용량+Hybrid ch54\M01Ch054[054]\260202_260226_05_문현규_5075mAh_Cosmx 25Si 율별용량+Hybrid ch54.sch`

**CSV Summary**
- Sections: ['Model name', 'Schedule', 'Safety Condition', 'Step']
- Schedule: {'Schedule Name': '닀낺?꺷??洵桁?票牢摩', 'User': '', 'Make Time': '?????뼠샀????2', 'Description': '닀낺?꺷???????金????C'}
- Safety: {'Voltage upper': '4.6 V', 'Voltage lower': '2.4 V', 'Current upper': '11.0 A', 'Current lower': '0.0 A', 'Capacity upper': '5.72 Ah', 'Capacity lower': '0.0 Ah', 'Temperature upper': '60.0 °C', 'Temperature lower': '0.0 °C'}
- Steps n=155, type_count={'Cycle': 21, 'DisCharge': 27, 'Rest': 41, 'Loop': 21, 'Charge': 44, '완료': 1}

**.sch Summary**
- Steps n=154, type_count={'DCHG_CC': 27, 'REST': 41, 'LOOP': 21, 'REST_SAFE': 20, 'CHG_CCCV': 28, 'CHG_CC': 16, 'GOTO': 1}
- capacity_limit_mAh (+104) = 5720.0

**Cross-check**

| Field | CSV | .sch | Match |
|---|---|---|---|
| n_steps | 155 | 154 | ❌ |
| capacity_mAh (CSV Capacity upper vs sch +104) | 5720.0 | 5720.0 | ✅ |

---
