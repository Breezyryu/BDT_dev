# Step-level CSV ↔ .sch alignment (Phase 0-1d)

## Floating_2688mAh_120D

- CSV: `Ref_4.55V Floating 2688mAh +120D.csv`
- .sch: `260112_260312_03_나무늬_2688mAh_Gen5+B SDI MP2 2.0C EPF HT Floating + 120D.sch`

- CSV steps (raw): 5, after skip Cycle/완료: 3, .sch steps: 4

```
  CSV step 2: Type=Charge, Mode=CC/CV
  .sch step 1: type_name=CHG_CCCV (0x0101)
    CSV values:
      VRef = 0.0 V
      IRef = 2.15 A = 2150.0 mA
      End = t > 120d 00:00:00.0
      V Limit = V≤4.6  -> lo=None hi=4.6
      I Limit = 2.1≤I≤2.2  -> lo=2.1 hi=2.2
    .sch non-zero fields:
      +  0  uint32=           1  float=             —
      +  8  uint32=         257  float=             —
      + 12  uint32=  1166946304  float=          4550
      + 20  uint32=  1158045696  float=          2150
      + 24  uint32=  1260270592  float=     1.037e+07
      + 88  uint32=  1167048704  float=          4600
      + 96  uint32=  1158250496  float=          2200
      +100  uint32=  1157840896  float=          2100
      +104  uint32=  1165754368  float=          4032
      +336  uint32=  1114636288  float=            60
      +388  uint32=  1114636288  float=            60
    Auto-match:
      VRef (V→mV) = 0.0 -> +0 (float_div1000=0.00, diff=0.00)
      IRef (A→mA) = 2150.0 -> +20 (float=2150.00, diff=0.00)
      V Limit hi (V→mV) = 4600.0 -> +88 (float=4600.00, diff=0.00)
      I Limit lo (A→mA) = 2100.0 -> +100 (float=2100.00, diff=0.00)
      I Limit hi (A→mA) = 2200.0 -> +96 (float=2200.00, diff=0.00)

  CSV step 3: Type=Rest, Mode=
  .sch step 2: type_name=REST (0xFF03)
    CSV values:
      End = t >  00:10:00.0  -> t > 600 s
    .sch non-zero fields:
      +  0  uint32=           2  float=             —
      +  8  uint32=       65283  float=             —
      + 24  uint32=  1142292480  float=           600
      +336  uint32=  1133903872  float=           300
      +388  uint32=  1114636288  float=            60
    Auto-match:
      End t (s) = 600.0 -> +24 (float=600.00, diff=0.00)

  CSV step 4: Type=Loop, Mode=
  .sch step 3: type_name=LOOP (0xFF08)
    CSV values:
      End = Repeat 1 Next Step Move
    .sch non-zero fields:
      +  0  uint32=           3  float=             —
      +  8  uint32=       65288  float=             —
      + 56  uint32=           1  float=             —
      +580  uint32=           1  float=             —
    Auto-match:

  *** Mismatch: CSV (post-skip) 3 vs .sch 4
```

---

## 4.53V_5000mAh_4cycle_SOC30

- CSV: `Ref_4.53V_Si_5000mAh 0.2C recovery capacity 4cycle SOC30 setting.csv`
- .sch: `260109_260112_05_이근준_5000mAh_Gen5P Si5 ATL T2 3M 보관 용량 측정 4cycle SOC 30 setting ch7 to 12.sch`

- CSV steps (raw): 15, after skip Cycle/완료: 11, .sch steps: 14

```
  CSV step 2: Type=DisCharge, Mode=CC
  .sch step 1: type_name=DCHG_CC (0x0202)
    CSV values:
      VRef = 2.5 V
      IRef = 1.0 A = 1000.0 mA
      End = V < 3.0  -> V < 3000 mV
      V Limit = 2.45≤V  -> lo=2.45 hi=None
    .sch non-zero fields:
      +  0  uint32=           1  float=             —
      +  8  uint32=         514  float=             —
      + 16  uint32=  1159479296  float=          2500
      + 20  uint32=  1148846080  float=          1000
      + 28  uint32=  1161527296  float=          3000
      + 84  uint32=           1  float=             —
      + 92  uint32=  1161322496  float=          2950
      +104  uint32=  1168891904  float=          5500
      +336  uint32=  1114636288  float=            60
      +388  uint32=  1114636288  float=            60
    Auto-match:
      VRef (V→mV) = 2500.0 -> +16 (float=2500.00, diff=0.00)
      IRef (A→mA) = 1000.0 -> +20 (float=1000.00, diff=0.00)
      End V (V→mV) = 3000.0 -> +28 (float=3000.00, diff=0.00)
      V Limit lo (V→mV) = 2450.0 -> NO MATCH

  CSV step 3: Type=Rest, Mode=
  .sch step 2: type_name=REST (0xFF03)
    CSV values:
      End = t >  00:10:00.0  -> t > 600 s
    .sch non-zero fields:
      +  0  uint32=           2  float=             —
      +  8  uint32=       65283  float=             —
      + 24  uint32=  1142292480  float=           600
      +336  uint32=  1114636288  float=            60
      +388  uint32=  1114636288  float=            60
    Auto-match:
      End t (s) = 600.0 -> +24 (float=600.00, diff=0.00)

  CSV step 4: Type=Loop, Mode=
  .sch step 3: type_name=LOOP (0xFF08)
    CSV values:
      End = Repeat 1 Next Step Move
    .sch non-zero fields:
      +  0  uint32=           3  float=             —
      +  8  uint32=       65288  float=             —
      + 56  uint32=           1  float=             —
      +580  uint32=           1  float=             —
    Auto-match:

  CSV step 6: Type=Charge, Mode=CC/CV
  .sch step 4: type_name=REST_SAFE (0xFF07)
    CSV values:
      VRef = 0.0 V
      IRef = 1.0 A = 1000.0 mA
      End = I < 0.1  -> I < 100 mA
      V Limit = V≤4.58  -> lo=None hi=4.58
    .sch non-zero fields:
      +  0  uint32=           4  float=             —
      +  8  uint32=       65287  float=             —
    Auto-match:
      VRef (V→mV) = 0.0 -> +0 (float_div1000=0.00, diff=0.00)
      IRef (A→mA) = 1000.0 -> NO MATCH
      End I (A→mA) = 100.0 -> NO MATCH
      V Limit hi (V→mV) = 4580.0 -> NO MATCH

  CSV step 7: Type=Rest, Mode=
  .sch step 5: type_name=CHG_CCCV (0x0101)
    CSV values:
      End = t >  00:10:00.0  -> t > 600 s
    .sch non-zero fields:
      +  0  uint32=           5  float=             —
      +  8  uint32=         257  float=             —
      + 12  uint32=  1166905344  float=          4530
      + 20  uint32=  1148846080  float=          1000
      + 32  uint32=  1120403456  float=           100
      + 84  uint32=           1  float=             —
      + 88  uint32=  1167007744  float=          4580
      +104  uint32=  1168891904  float=          5500
      +336  uint32=  1114636288  float=            60
      +388  uint32=  1114636288  float=            60
    Auto-match:
      End t (s) = 600.0 -> NO MATCH

  CSV step 8: Type=DisCharge, Mode=CC
  .sch step 6: type_name=REST (0xFF03)
    CSV values:
      VRef = 2.5 V
      IRef = 1.0 A = 1000.0 mA
      End = V < 3.0  -> V < 3000 mV
      V Limit = 2.45≤V  -> lo=2.45 hi=None
    .sch non-zero fields:
      +  0  uint32=           6  float=             —
      +  8  uint32=       65283  float=             —
      + 24  uint32=  1142292480  float=           600
      + 84  uint32=           1  float=             —
      +336  uint32=  1114636288  float=            60
      +388  uint32=  1114636288  float=            60
    Auto-match:
      VRef (V→mV) = 2500.0 -> NO MATCH
      IRef (A→mA) = 1000.0 -> NO MATCH
      End V (V→mV) = 3000.0 -> NO MATCH
      V Limit lo (V→mV) = 2450.0 -> NO MATCH

  CSV step 9: Type=Rest, Mode=
  .sch step 7: type_name=DCHG_CC (0x0202)
    CSV values:
      End = t >  00:10:00.0  -> t > 600 s
    .sch non-zero fields:
      +  0  uint32=           7  float=             —
      +  8  uint32=         514  float=             —
      + 16  uint32=  1159479296  float=          2500
      + 20  uint32=  1148846080  float=          1000
      + 28  uint32=  1161527296  float=          3000
      + 84  uint32=           1  float=             —
      + 92  uint32=  1161322496  float=          2950
      +104  uint32=  1168891904  float=          5500
      +336  uint32=  1114636288  float=            60
      +388  uint32=  1114636288  float=            60
    Auto-match:
      End t (s) = 600.0 -> NO MATCH

  CSV step 10: Type=Loop, Mode=
  .sch step 8: type_name=REST (0xFF03)
    CSV values:
      End = Repeat 4 Next Step Move
    .sch non-zero fields:
      +  0  uint32=           8  float=             —
      +  8  uint32=       65283  float=             —
      + 24  uint32=  1142292480  float=           600
      +336  uint32=  1114636288  float=            60
      +388  uint32=  1114636288  float=            60
    Auto-match:

  CSV step 12: Type=Charge, Mode=CC
  .sch step 9: type_name=LOOP (0xFF08)
    CSV values:
      VRef = 0.0 V
      IRef = 1.0 A = 1000.0 mA
      V Limit = V≤4.58  -> lo=None hi=4.58
    .sch non-zero fields:
      +  0  uint32=           9  float=             —
      +  8  uint32=       65288  float=             —
      + 56  uint32=           4  float=             —
      + 84  uint32=           1  float=             —
    Auto-match:
      VRef (V→mV) = 0.0 -> +84 (float_div1000=0.00, diff=0.00)
      IRef (A→mA) = 1000.0 -> NO MATCH
      V Limit hi (V→mV) = 4580.0 -> NO MATCH

  CSV step 13: Type=Rest, Mode=
  .sch step 10: type_name=REST_SAFE (0xFF07)
    CSV values:
      End = t >  00:10:00.0  -> t > 600 s
    .sch non-zero fields:
      +  0  uint32=          10  float=             —
      +  8  uint32=       65287  float=             —
    Auto-match:
      End t (s) = 600.0 -> NO MATCH

  CSV step 14: Type=Loop, Mode=
  .sch step 11: type_name=CHG_CC (0x0201)
    CSV values:
      End = Repeat 1 Next Step Move
    .sch non-zero fields:
      +  0  uint32=          11  float=             —
      +  8  uint32=         513  float=             —
      + 12  uint32=  1166905344  float=          4530
      + 20  uint32=  1148846080  float=          1000
      + 84  uint32=           1  float=             —
      + 88  uint32=  1167007744  float=          4580
      +104  uint32=  1168891904  float=          5500
      +336  uint32=  1114636288  float=            60
      +372  uint32=  1106247680  float=            30
      +388  uint32=  1114636288  float=            60
      +500  uint32=        2048  float=             —
      +504  uint32=           1  float=             —
    Auto-match:

  *** Mismatch: CSV (post-skip) 11 vs .sch 14
```

---

## ECT_5882mAh_GITT

- CSV: `Ref_5882mAh_ECT 패턴11 GITT.csv`
- .sch: `260316_270318_00_이성일_5882mAh_M47 ATL ECT GITT.sch`

- CSV steps (raw): 29, after skip Cycle/완료: 21, .sch steps: 28

```
  CSV step 2: Type=Charge, Mode=CC/CV
  .sch step 1: type_name=CHG_CCCV (0x0101)
    CSV values:
      VRef = 0.0 V
      IRef = 1.177 A = 1177.0 mA
      End = I < 0.118 or t >  07:00:00.0 or C > 6.0  -> I < 118 mA  -> t > 25200 s
      V Limit = V≤4.58  -> lo=None hi=4.58
      I Limit = 1.127≤I≤1.227  -> lo=1.127 hi=1.227
    .sch non-zero fields:
      +  0  uint32=           1  float=             —
      +  8  uint32=         257  float=             —
      + 12  uint32=  1166905344  float=          4530
      + 20  uint32=  1150492672  float=          1177
      + 24  uint32=  1187307520  float=      2.52e+04
      + 32  uint32=  1122762752  float=           118
      + 36  uint32=  1169915904  float=          6000
      + 88  uint32=  1167007744  float=          4580
      + 96  uint32=  1150902272  float=          1227
      +100  uint32=  1150083072  float=          1127
      +104  uint32=  1170315264  float=          6195
      +336  uint32=  1065353216  float=             1
      +396  uint32=  1102577664  float=            23
    Auto-match:
      VRef (V→mV) = 0.0 -> +0 (float_div1000=0.00, diff=0.00)
      IRef (A→mA) = 1177.0 -> +20 (float=1177.00, diff=0.00)
      End I (A→mA) = 118.0 -> +32 (float=118.00, diff=0.00)
      End t (s) = 25200.0 -> +24 (float=25200.00, diff=0.00)
      V Limit hi (V→mV) = 4580.0 -> +88 (float=4580.00, diff=0.00)
      I Limit lo (A→mA) = 1127.0 -> +100 (float=1127.00, diff=0.00)
      I Limit hi (A→mA) = 1227.0 -> +96 (float=1227.00, diff=0.00)

  CSV step 3: Type=Rest, Mode=
  .sch step 2: type_name=REST (0xFF03)
    CSV values:
      End = t >  00:30:00.0  -> t > 1800 s
    .sch non-zero fields:
      +  0  uint32=           2  float=             —
      +  8  uint32=       65283  float=             —
      + 24  uint32=  1155596288  float=          1800
      + 88  uint32=  1167151104  float=          4650
      + 92  uint32=  1153138688  float=          1500
      +336  uint32=  1065353216  float=             1
      +396  uint32=  1102577664  float=            23
    Auto-match:
      End t (s) = 1800.0 -> +24 (float=1800.00, diff=0.00)

  CSV step 4: Type=DisCharge, Mode=CC
  .sch step 3: type_name=DCHG_CC (0x0202)
    CSV values:
      VRef = 2.5 V
      IRef = 1.177 A = 1177.0 mA
      End = V < 2.75 or t >  06:00:00.0 or C > 6.0  -> V < 2750 mV  -> t > 21600 s
      V Limit = 1.8≤V  -> lo=1.8 hi=None
      I Limit = 0.001≤I≤6.0  -> lo=0.001 hi=6.0
    .sch non-zero fields:
      +  0  uint32=           3  float=             —
      +  8  uint32=         514  float=             —
      + 16  uint32=  1159479296  float=          2500
      + 20  uint32=  1150492672  float=          1177
      + 24  uint32=  1185464320  float=      2.16e+04
      + 28  uint32=  1160503296  float=          2750
      + 40  uint32=  1169915904  float=          6000
      + 92  uint32=  1160298496  float=          2700
      + 96  uint32=  1150902272  float=          1227
      +100  uint32=  1150083072  float=          1127
      +104  uint32=  1170315264  float=          6195
      +336  uint32=  1065353216  float=             1
      +396  uint32=  1102577664  float=            23
    Auto-match:
      VRef (V→mV) = 2500.0 -> +16 (float=2500.00, diff=0.00)
      IRef (A→mA) = 1177.0 -> +20 (float=1177.00, diff=0.00)
      End V (V→mV) = 2750.0 -> +28 (float=2750.00, diff=0.00)
      End t (s) = 21600.0 -> +24 (float=21600.00, diff=0.00)
      V Limit lo (V→mV) = 1800.0 -> NO MATCH
      I Limit lo (A→mA) = 1.0 -> +336 (float=1.00, diff=0.00)
      I Limit hi (A→mA) = 6000.0 -> +40 (float=6000.00, diff=0.00)

  CSV step 5: Type=Rest, Mode=
  .sch step 4: type_name=REST (0xFF03)
    CSV values:
      End = t >  00:30:00.0  -> t > 1800 s
    .sch non-zero fields:
      +  0  uint32=           4  float=             —
      +  8  uint32=       65283  float=             —
      + 24  uint32=  1155596288  float=          1800
      + 88  uint32=  1167151104  float=          4650
      + 92  uint32=  1153138688  float=          1500
      +336  uint32=  1065353216  float=             1
      +396  uint32=  1102577664  float=            23
    Auto-match:
      End t (s) = 1800.0 -> +24 (float=1800.00, diff=0.00)

  CSV step 6: Type=Loop, Mode=
  .sch step 5: type_name=GITT_START (0x0008)
    CSV values:
      End = Repeat 3 Next Step Move
    .sch non-zero fields:
      +  0  uint32=           5  float=             —
      +  8  uint32=           8  float=             —
      + 56  uint32=           3  float=             —
    Auto-match:

  CSV step 8: Type=Rest, Mode=
  .sch step 6: type_name=GITT_END (0x0007)
    CSV values:
      End = t >  00:30:00.0  -> t > 1800 s
    .sch non-zero fields:
      +  0  uint32=           6  float=             —
      +  8  uint32=           7  float=             —
    Auto-match:
      End t (s) = 1800.0 -> NO MATCH

  CSV step 9: Type=DisCharge, Mode=CC
  .sch step 7: type_name=REST (0xFF03)
    CSV values:
      VRef = 1.9 V
      IRef = 0.059 A = 59.0 mA
      End = V < 2.0 or t > 5d 00:00:00.0 or C > 6.0  -> V < 2000 mV
      V Limit = 1.8≤V  -> lo=1.8 hi=None
      I Limit = 0.001≤I≤6.0  -> lo=0.001 hi=6.0
    .sch non-zero fields:
      +  0  uint32=           7  float=             —
      +  8  uint32=       65283  float=             —
      + 24  uint32=  1155596288  float=          1800
      + 88  uint32=  1167151104  float=          4650
      + 92  uint32=  1153138688  float=          1500
      +336  uint32=  1065353216  float=             1
      +396  uint32=  1102577664  float=            23
    Auto-match:
      VRef (V→mV) = 1900.0 -> NO MATCH
      IRef (A→mA) = 59.0 -> NO MATCH
      End V (V→mV) = 2000.0 -> NO MATCH
      V Limit lo (V→mV) = 1800.0 -> +24 (float=1800.00, diff=0.00)
      I Limit lo (A→mA) = 1.0 -> +336 (float=1.00, diff=0.00)
      I Limit hi (A→mA) = 6000.0 -> NO MATCH

  CSV step 10: Type=Rest, Mode=
  .sch step 8: type_name=DCHG_CC (0x0202)
    CSV values:
      End = t >  01:00:00.0  -> t > 3600 s
    .sch non-zero fields:
      +  0  uint32=           8  float=             —
      +  8  uint32=         514  float=             —
      + 16  uint32=  1156415488  float=          1900
      + 20  uint32=  1114374144  float=            59
      + 24  uint32=  1221783552  float=      4.32e+05
      + 28  uint32=  1157234688  float=          2000
      + 40  uint32=  1169915904  float=          6000
      + 92  uint32=  1156825088  float=          1950
      + 96  uint32=  1121583104  float=           109
      +100  uint32=  1091567616  float=             9
      +104  uint32=  1170315264  float=          6195
      +336  uint32=  1065353216  float=             1
      +396  uint32=  1102577664  float=            23
    Auto-match:
      End t (s) = 3600.0 -> NO MATCH

  CSV step 11: Type=Loop, Mode=
  .sch step 9: type_name=REST (0xFF03)
    CSV values:
      End = Repeat 1 Next Step Move
    .sch non-zero fields:
      +  0  uint32=           9  float=             —
      +  8  uint32=       65283  float=             —
      + 24  uint32=  1163984896  float=          3600
      + 88  uint32=  1167151104  float=          4650
      + 92  uint32=  1153138688  float=          1500
      +336  uint32=  1065353216  float=             1
      +396  uint32=  1102577664  float=            23
    Auto-match:

  CSV step 13: Type=Charge, Mode=CC
  .sch step 10: type_name=GITT_START (0x0008)
    CSV values:
      VRef = 0.0 V
      IRef = 0.589 A = 589.0 mA
      End = V > 4.59 or t >  00:06:00.0 or C > 6.0  -> V > 4590 mV  -> t > 360 s
      V Limit = V≤4.64  -> lo=None hi=4.64
      I Limit = 0.539≤I≤0.639  -> lo=0.539 hi=0.639
    .sch non-zero fields:
      +  0  uint32=          10  float=             —
      +  8  uint32=           8  float=             —
      + 56  uint32=           1  float=             —
    Auto-match:
      VRef (V→mV) = 0.0 -> +56 (float_div1000=0.00, diff=0.00)
      IRef (A→mA) = 589.0 -> NO MATCH
      End V (V→mV) = 4590.0 -> NO MATCH
      End t (s) = 360.0 -> NO MATCH
      V Limit hi (V→mV) = 4640.0 -> NO MATCH
      I Limit lo (A→mA) = 539.0 -> NO MATCH
      I Limit hi (A→mA) = 639.0 -> NO MATCH

  CSV step 14: Type=Rest, Mode=
  .sch step 11: type_name=GITT_END (0x0007)
    CSV values:
      End = t >  01:00:00.0  -> t > 3600 s
    .sch non-zero fields:
      +  0  uint32=          11  float=             —
      +  8  uint32=           7  float=             —
    Auto-match:
      End t (s) = 3600.0 -> NO MATCH

  CSV step 15: Type=Loop, Mode=
  .sch step 12: type_name=CHG_CC (0x0201)
    CSV values:
      End = Repeat 120 Next Step Move
    .sch non-zero fields:
      +  0  uint32=          12  float=             —
      +  8  uint32=         513  float=             —
      + 12  uint32=  1167048704  float=          4600
      + 20  uint32=  1142112256  float=           589
      + 24  uint32=  1135869952  float=           360
      + 28  uint32=  1167028224  float=          4590
      + 36  uint32=  1169915904  float=          6000
      + 64  uint32=          16  float=             —
      + 88  uint32=  1167130624  float=          4640
      + 96  uint32=  1142931456  float=           639
      +100  uint32=  1141293056  float=           539
      +104  uint32=  1170315264  float=          6195
      +336  uint32=  1065353216  float=             1
      +396  uint32=  1102577664  float=            23
    Auto-match:

  CSV step 17: Type=Rest, Mode=
  .sch step 13: type_name=REST (0xFF03)
    CSV values:
      End = t >  01:00:00.0  -> t > 3600 s
    .sch non-zero fields:
      +  0  uint32=          13  float=             —
      +  8  uint32=       65283  float=             —
      + 24  uint32=  1163984896  float=          3600
      + 88  uint32=  1167151104  float=          4650
      + 92  uint32=  1153138688  float=          1500
      +336  uint32=  1065353216  float=             1
      +396  uint32=  1102577664  float=            23
    Auto-match:
      End t (s) = 3600.0 -> +24 (float=3600.00, diff=0.00)

  CSV step 18: Type=Loop, Mode=
  .sch step 14: type_name=GITT_START (0x0008)
    CSV values:
      End = Repeat 1 Next Step Move
    .sch non-zero fields:
      +  0  uint32=          14  float=             —
      +  8  uint32=           8  float=             —
      + 56  uint32=         120  float=             —
      + 84  uint32=           1  float=             —
    Auto-match:

  CSV step 20: Type=DisCharge, Mode=CC
  .sch step 15: type_name=GITT_END (0x0007)
    CSV values:
      VRef = 1.9 V
      IRef = 0.589 A = 589.0 mA
      End = V < 2.0 or t >  00:06:00.0 or C > 6.0  -> V < 2000 mV  -> t > 360 s
      V Limit = 1.8≤V  -> lo=1.8 hi=None
      I Limit = 0.001≤I≤6.0  -> lo=0.001 hi=6.0
    .sch non-zero fields:
      +  0  uint32=          15  float=             —
      +  8  uint32=           7  float=             —
    Auto-match:
      VRef (V→mV) = 1900.0 -> NO MATCH
      IRef (A→mA) = 589.0 -> NO MATCH
      End V (V→mV) = 2000.0 -> NO MATCH
      End t (s) = 360.0 -> NO MATCH
      V Limit lo (V→mV) = 1800.0 -> NO MATCH
      I Limit lo (A→mA) = 1.0 -> +0 (uint32_div1000=0.01, diff=0.98)
      I Limit hi (A→mA) = 6000.0 -> NO MATCH

  CSV step 21: Type=Rest, Mode=
  .sch step 16: type_name=REST (0xFF03)
    CSV values:
      End = t >  01:00:00.0  -> t > 3600 s
    .sch non-zero fields:
      +  0  uint32=          16  float=             —
      +  8  uint32=       65283  float=             —
      + 24  uint32=  1163984896  float=          3600
      + 88  uint32=  1167151104  float=          4650
      + 92  uint32=  1153138688  float=          1500
      +336  uint32=  1065353216  float=             1
      +396  uint32=  1102577664  float=            23
    Auto-match:
      End t (s) = 3600.0 -> +24 (float=3600.00, diff=0.00)

  CSV step 22: Type=Loop, Mode=
  .sch step 17: type_name=GITT_START (0x0008)
    CSV values:
      End = Repeat 120 Next Step Move
    .sch non-zero fields:
      +  0  uint32=          17  float=             —
      +  8  uint32=           8  float=             —
      + 56  uint32=           1  float=             —
    Auto-match:

  CSV step 24: Type=Rest, Mode=
  .sch step 18: type_name=REST_SAFE (0xFF07)
    CSV values:
      End = t >  01:00:00.0  -> t > 3600 s
    .sch non-zero fields:
      +  0  uint32=          18  float=             —
      +  8  uint32=       65287  float=             —
    Auto-match:
      End t (s) = 3600.0 -> NO MATCH

  CSV step 25: Type=Loop, Mode=
  .sch step 19: type_name=DCHG_CC (0x0202)
    CSV values:
      End = Repeat 1 Next Step Move
    .sch non-zero fields:
      +  0  uint32=          19  float=             —
      +  8  uint32=         514  float=             —
      + 16  uint32=  1156415488  float=          1900
      + 20  uint32=  1142112256  float=           589
      + 24  uint32=  1135869952  float=           360
      + 28  uint32=  1157234688  float=          2000
      + 40  uint32=  1169915904  float=          6000
      + 92  uint32=  1156825088  float=          1950
      + 96  uint32=  1142931456  float=           639
      +100  uint32=  1141293056  float=           539
      +104  uint32=  1170315264  float=          6195
      +336  uint32=  1065353216  float=             1
      +396  uint32=  1102577664  float=            23
    Auto-match:

  CSV step 27: Type=DisCharge, Mode=CC
  .sch step 20: type_name=REST (0xFF03)
    CSV values:
      VRef = 2.7 V
      IRef = 5.882 A = 5882.0 mA
      End = V < 2.75 or t >  00:00:01.0 or C > 5.2  -> V < 2750 mV  -> t > 1 s
      V Limit = 1.8≤V  -> lo=1.8 hi=None
      I Limit = 0.001≤I≤6.0  -> lo=0.001 hi=6.0
    .sch non-zero fields:
      +  0  uint32=          20  float=             —
      +  8  uint32=       65283  float=             —
      + 24  uint32=  1163984896  float=          3600
      + 88  uint32=  1167151104  float=          4650
      + 92  uint32=  1153138688  float=          1500
      +336  uint32=  1065353216  float=             1
      +396  uint32=  1102577664  float=            23
    Auto-match:
      VRef (V→mV) = 2700.0 -> NO MATCH
      IRef (A→mA) = 5882.0 -> NO MATCH
      End V (V→mV) = 2750.0 -> NO MATCH
      End t (s) = 1.0 -> +336 (float=1.00, diff=0.00)
      V Limit lo (V→mV) = 1800.0 -> NO MATCH
      I Limit lo (A→mA) = 1.0 -> +336 (float=1.00, diff=0.00)
      I Limit hi (A→mA) = 6000.0 -> NO MATCH

  CSV step 28: Type=Loop, Mode=
  .sch step 21: type_name=LOOP (0xFF08)
    CSV values:
      End = Repeat 1 Next Step Move
    .sch non-zero fields:
      +  0  uint32=          21  float=             —
      +  8  uint32=       65288  float=             —
      + 56  uint32=         120  float=             —
      + 84  uint32=           1  float=             —
    Auto-match:

  *** Mismatch: CSV (post-skip) 21 vs .sch 28
```

---
