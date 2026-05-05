# mode_flag 좁힌 가설 검증 — schedule keyword × step type × mode

- Source: `mode_flag_step_dump.csv` (28779 step rows)

## H1 — keyword × step_type × mode_flag 3-way 매트릭스

각 (keyword, step_type) 조합에서 mode=0/1/257 비율. mode_flag 이 시험 유형별로 어떻게 분기되는지 직접 가시화.

### CHG_CC

| keyword | total | mode=0 | mode=1 | mode=257 | mode=1 비율 |
|---|---|---|---|---|---|
| accel_si | 922 | 0 | 922 | 0 | 100% |
| ect | 61 | 25 | 36 | 0 | 59% |
| floating | 66 | 38 | 28 | 0 | 42% |
| formation | 8 | 0 | 8 | 0 | 100% |
| gitt | 57 | 27 | 30 | 0 | 53% |
| hysteresis | 158 | 0 | 158 | 0 | 100% |
| other | 160 | 17 | 143 | 0 | 89% |
| rss | 108 | 0 | 108 | 0 | 100% |

### CHG_CCCV

| keyword | total | mode=0 | mode=1 | mode=257 | mode=1 비율 |
|---|---|---|---|---|---|
| accel_si | 1564 | 0 | 1564 | 0 | 100% |
| dcir | 34 | 0 | 34 | 0 | 100% |
| ect | 1156 | 482 | 674 | 0 | 58% |
| floating | 370 | 328 | 42 | 0 | 11% |
| formation | 8 | 0 | 8 | 0 | 100% |
| gitt | 11 | 9 | 2 | 0 | 18% |
| hysteresis | 238 | 0 | 238 | 0 | 100% |
| other | 535 | 24 | 511 | 0 | 96% |
| rss | 248 | 0 | 248 | 0 | 100% |
| soc_dcir | 178 | 2 | 176 | 0 | 99% |

### DCHG_CC

| keyword | total | mode=0 | mode=1 | mode=257 | mode=1 비율 |
|---|---|---|---|---|---|
| accel_si | 1600 | 0 | 1600 | 0 | 100% |
| dcir | 131 | 9 | 122 | 0 | 93% |
| ect | 1029 | 519 | 510 | 0 | 50% |
| floating | 370 | 332 | 38 | 0 | 10% |
| formation | 8 | 0 | 8 | 0 | 100% |
| gitt | 80 | 46 | 34 | 0 | 42% |
| hysteresis | 414 | 0 | 414 | 0 | 100% |
| other | 981 | 47 | 934 | 0 | 95% |
| rss | 635 | 0 | 635 | 0 | 100% |
| soc_dcir | 172 | 0 | 166 | 6 | 97% |

### DCHG_CCCV

| keyword | total | mode=0 | mode=1 | mode=257 | mode=1 비율 |
|---|---|---|---|---|---|
| dcir | 18 | 9 | 9 | 0 | 50% |
| formation | 8 | 0 | 8 | 0 | 100% |
| other | 55 | 22 | 33 | 0 | 60% |
| soc_dcir | 8 | 0 | 8 | 0 | 100% |

### CHG_CP

| keyword | total | mode=0 | mode=1 | mode=257 | mode=1 비율 |
|---|---|---|---|---|---|
| ect | 108 | 37 | 71 | 0 | 66% |

### REST

| keyword | total | mode=0 | mode=1 | mode=257 | mode=1 비율 |
|---|---|---|---|---|---|
| accel_si | 2242 | 0 | 2242 | 0 | 100% |
| dcir | 57 | 23 | 34 | 0 | 60% |
| ect | 2944 | 2928 | 16 | 0 | 1% |
| floating | 502 | 474 | 28 | 0 | 6% |
| formation | 64 | 16 | 48 | 0 | 75% |
| gitt | 133 | 109 | 24 | 0 | 18% |
| hysteresis | 810 | 0 | 810 | 0 | 100% |
| other | 1002 | 250 | 752 | 0 | 75% |
| rss | 540 | 154 | 386 | 0 | 71% |
| soc_dcir | 172 | 4 | 168 | 0 | 98% |

### REST_SAFE

| keyword | total | mode=0 | mode=1 | mode=257 | mode=1 비율 |
|---|---|---|---|---|---|
| accel_si | 1106 | 271 | 835 | 0 | 75% |
| dcir | 50 | 41 | 9 | 0 | 18% |
| ect | 1412 | 1412 | 0 | 0 | 0% |
| floating | 194 | 194 | 0 | 0 | 0% |
| formation | 32 | 32 | 0 | 0 | 0% |
| gitt | 115 | 113 | 2 | 0 | 2% |
| hysteresis | 396 | 396 | 0 | 0 | 0% |
| other | 481 | 382 | 99 | 0 | 21% |
| rss | 165 | 113 | 52 | 0 | 32% |
| soc_dcir | 54 | 52 | 2 | 0 | 4% |

### LOOP

| keyword | total | mode=0 | mode=1 | mode=257 | mode=1 비율 |
|---|---|---|---|---|---|
| accel_si | 1165 | 59 | 1106 | 0 | 95% |
| dcir | 59 | 7 | 52 | 0 | 88% |
| ect | 1527 | 1519 | 8 | 0 | 1% |
| floating | 250 | 226 | 24 | 0 | 10% |
| formation | 48 | 48 | 0 | 0 | 0% |
| gitt | 134 | 55 | 79 | 0 | 59% |
| hysteresis | 414 | 18 | 396 | 0 | 96% |
| other | 536 | 119 | 417 | 0 | 78% |
| rss | 174 | 68 | 106 | 0 | 61% |
| soc_dcir | 60 | 8 | 52 | 0 | 87% |

### GOTO

| keyword | total | mode=0 | mode=1 | mode=257 | mode=1 비율 |
|---|---|---|---|---|---|
| accel_si | 59 | 0 | 59 | 0 | 100% |
| dcir | 9 | 9 | 0 | 0 | 0% |
| ect | 115 | 115 | 0 | 0 | 0% |
| floating | 56 | 56 | 0 | 0 | 0% |
| formation | 16 | 16 | 0 | 0 | 0% |
| gitt | 24 | 24 | 0 | 0 | 0% |
| hysteresis | 18 | 18 | 0 | 0 | 0% |
| other | 55 | 52 | 3 | 0 | 5% |
| rss | 9 | 9 | 0 | 0 | 0% |
| soc_dcir | 6 | 6 | 0 | 0 | 0% |

## H2 — CHG_CC mode=1 = multi-step charge intermediate 검증

가설: 같은 schedule 내에서 mode=1 CHG_CC step 이 연속하여 V_end 가 점진적으로 증가.
검증 방법: file 내 CHG_CC step (idx 순서대로) 추출 → V_end sequence 패턴 분석.

- multi-step pattern 검출 file (≥3 CHG_CC, V_end 단조증가): **12** files
- single/short pattern files (≤2 CHG_CC): 35 files

### multi-step sample 10 — V_end sequence + mode_flag sequence

| sch | n_chg_cc | V_end sequence | mode sequence |
|---|---|---|---|
| 251224_260110_00_박민희_4-04mAh_M1 ATL Anode Half T23 | 9 | 3000 → 3000 → 3000 → 3000 → 3000 → 3000 → 3050 → 3050 → 3050 | 1 → 1 → 1 → 1 → 1 → 1 → 1 → 1 → 1 |
| 251224_260110_00_박민희_4-04mAh_M1 ATL Anode Half T23 | 9 | 2500 → 2500 → 2500 → 2500 → 2500 → 2500 → 3050 → 3050 → 3050 | 1 → 1 → 1 → 1 → 1 → 1 → 1 → 1 → 1 |
| 260316_270318_00_이성일_5882mAh_M47 ATL ECT parameter | 4 | 4130 → 4150 → 4210 → 4230 | 1 → 1 → 1 → 1 |
| 240221 1파트 한정구 Gen4 2C ATL MP1차 Main 4500mAh 상온 ve | 4 | 4140 → 4140 → 4160 → 4160 | 1 → 1 → 1 → 1 |
| 240507 1파트 한정구 Gen4 2C ATL MP1차 Main 4500mAh 상온 ve | 4 | 4140 → 4140 → 4160 → 4160 | 1 → 1 → 1 → 1 |
| 260130_260531_01_최웅철_2485mAh_Q8 SUB SDI GEN5+B 2C  | 4 | 4140 → 4140 → 4160 → 4160 | 1 → 1 → 1 → 1 |
| 260223_260531_01_최웅철_2369mAh_Q8main ATL GEN5+B 2.0 | 4 | 4140 → 4140 → 4160 → 4160 | 1 → 1 → 1 → 1 |
| 260223_260531_01_최웅철_2369mAh_Q8main COSMX GEN5+B 2 | 4 | 4140 → 4140 → 4160 → 4160 | 1 → 1 → 1 → 1 |
| 260223_260531_01_최웅철_2485mAh_Q8 sub ATL GEN5+B 2.0 | 4 | 4140 → 4140 → 4160 → 4160 | 1 → 1 → 1 → 1 |
| 260309_260731_01_최웅철_2485mAh_Q8 sub SDI GEN5+B 2.0 | 4 | 4140 → 4140 → 4160 → 4160 | 1 → 1 → 1 → 1 |
| 260413_260930_05_김영환_3365mAh_Gen6+VB ATL Proto1 고온 | 4 | 4140 → 4140 → 4160 → 4160 | 1 → 1 → 1 → 1 |
| 260413_260930_05_박기진_4948mAh_Gen6+VB SDI Proto1 고온 | 8 | 4140 → 4140 → 4140 → 4140 → 4160 → 4160 → 4160 → 4160 | 1 → 1 → 1 → 1 → 1 → 1 → 1 → 1 |

### multi-step file 의 첫/마지막 CHG_CC 의 mode_flag

- 첫 CHG_CC mode: {1: 12}
- 마지막 CHG_CC mode: {1: 12}
- 중간 CHG_CC mode: {1: 38}

## H3 — schedule 마지막 step (mode=0 93%) type 분포 검증

가설: 마지막 step 이 mode=0 인 것은 TERMINATION (사이클 외부) 표시.

### 마지막 step type × mode_flag

| type | mode=0 | mode=1 | total |
|---|---|---|---|
| GOTO | 190 | 14 | 204 |

### 마지막 step keyword × mode_flag

| keyword | mode=0 | mode=1 | total |
|---|---|---|---|
| ect | 105 | 0 | 105 |
| other | 28 | 1 | 29 |
| floating | 21 | 0 | 21 |
| accel_si | 0 | 13 | 13 |
| hysteresis | 12 | 0 | 12 |
| gitt | 9 | 0 | 9 |
| dcir | 5 | 0 | 5 |
| soc_dcir | 4 | 0 | 4 |
| rss | 4 | 0 | 4 |
| formation | 2 | 0 | 2 |

## H4 — DCHG_CCCV mode=0 (100% EC enabled) = DCIR pulse 검증

가설: DCHG_CCCV mode=0 (모두 ref-step 사용) 은 DCIR pulse measurement.

### DCHG_CCCV mode 별 schedule keyword 분포

| keyword | mode=0 | mode=1 |
|---|---|---|
| other | 22 | 33 |
| dcir | 9 | 9 |
| formation | 0 | 8 |
| soc_dcir | 0 | 8 |

### DCHG_CCCV mode=0 step 의 file + desc (전수 31 step)

| sch | step# | I (mA) | I_end (mA) | desc |
|---|---|---|---|---|
| 260211_260310_05_문현규_3885mAh_POR 40C pulse PA1 ATL.sch | 33 | 777 | 156 | POR���� v2 ������pulse PA1 ATL |
| 260211_260310_05_문현규_3885mAh_POR 40C pulse PA1 ATL.sch | 80 | 777 | 156 | POR���� v2 ������pulse PA1 ATL |
| 260211_260310_05_문현규_3885mAh_POR 40C pulse PA1 ATL_000.sch | 33 | 777 | 156 | POR���� v2 ������pulse PA1 ATL |
| 260211_260310_05_문현규_3885mAh_POR 40C pulse PA1 ATL_000.sch | 80 | 777 | 156 | POR���� v2 ������pulse PA1 ATL |
| 260211_260310_05_문현규_3885mAh_POR 40C pulse PA1 SDI.sch | 33 | 777 | 156 | POR���� v2 ������ pulse PA1 SDI(stack) |
| 260211_260310_05_문현규_3885mAh_POR 40C pulse PA1 SDI.sch | 80 | 777 | 156 | POR���� v2 ������ pulse PA1 SDI(stack) |
| 260211_260310_05_문현규_3885mAh_POR 40C pulse PA1 SDI_000.sch | 33 | 777 | 156 | POR���� v2 ������ pulse PA1 SDI(stack) |
| 260211_260310_05_문현규_3885mAh_POR 40C pulse PA1 SDI_000.sch | 80 | 777 | 156 | POR���� v2 ������ pulse PA1 SDI(stack) |
| 260211_260310_05_문현규_3885mAh_POR 40C pulse PA1 SDI_001.sch | 33 | 777 | 156 | POR���� v2 ������ pulse PA1 SDI(stack) |
| 260211_260310_05_문현규_3885mAh_POR 40C pulse PA1 SDI_001.sch | 80 | 777 | 156 | POR���� v2 ������ pulse PA1 SDI(stack) |
| 260211_260310_05_문현규_4855mAh_POR 40C pulse PA3 ATL.sch | 33 | 971 | 195 | POR���� v2 ������ pulse PA3 ATL |
| 260211_260310_05_문현규_4855mAh_POR 40C pulse PA3 ATL.sch | 81 | 971 | 195 | POR���� v2 ������ pulse PA3 ATL |
| 260211_260310_05_문현규_4855mAh_POR 40C pulse PA3 ATL_000.sch | 33 | 971 | 195 | POR���� v2 ������ pulse PA3 ATL |
| 260211_260310_05_문현규_4855mAh_POR 40C pulse PA3 ATL_000.sch | 81 | 971 | 195 | POR���� v2 ������ pulse PA3 ATL |
| 260211_260310_05_문현규_4855mAh_POR 40C pulse PA3 ATL_001.sch | 33 | 971 | 195 | POR���� v2 ������ pulse PA3 ATL |
| 260211_260310_05_문현규_4855mAh_POR 40C pulse PA3 ATL_001.sch | 81 | 971 | 195 | POR���� v2 ������ pulse PA3 ATL |
| 260211_260310_05_문현규_4855mAh_POR 40C pulse PA3 SDI.sch | 33 | 971 | 195 | POR���� v2 ������ pulse PA3 SDI |
| 260211_260310_05_문현규_4855mAh_POR 40C pulse PA3 SDI.sch | 81 | 971 | 195 | POR���� v2 ������ pulse PA3 SDI |
| 260211_260310_05_문현규_4855mAh_POR 40C pulse PA3 SDI_000.sch | 33 | 971 | 195 | POR���� v2 ������ pulse PA3 SDI |
| 260211_260310_05_문현규_4855mAh_POR 40C pulse PA3 SDI_000.sch | 81 | 971 | 195 | POR���� v2 ������ pulse PA3 SDI |
| 260211_260310_05_문현규_4855mAh_POR 40C pulse PA3 SDI_001.sch | 33 | 971 | 195 | POR���� v2 ������ pulse PA3 SDI |
| 260211_260310_05_문현규_4855mAh_POR 40C pulse PA3 SDI_001.sch | 81 | 971 | 195 | POR���� v2 ������ pulse PA3 SDI |
| 260212_260215_05_한지영_5432mAh_SDI Phase2 MP2 Fresh DCIR SOC10 | 33 | 1087 | 218 | SDI Phase2 MP2 5432mAh DCIR |
| 260212_260215_05_한지영_5432mAh_SDI Phase2 MP2 Fresh DCIR SOC10 | 33 | 1087 | 218 | SDI Phase2 MP2 5432mAh DCIR |
| 260212_260215_05_한지영_5432mAh_SDI Phase2 MP2 고온수명후 DCIR SOC10 | 23 | 1087 | 218 | SDI Phase2 MP2 5432mAh DCIR |
| 260212_260215_05_한지영_5432mAh_SDI Phase2 MP2 고온수명후 DCIR SOC10 | 23 | 1087 | 218 | SDI Phase2 MP2 5432mAh DCIR |
| 260226_260228_05_문현규_3876mAh_PS 연속저장 DCIR.sch | 33 | 777 | 156 | DCIR 3885mAh |
| 260226_260228_05_문현규_3876mAh_PS 연속저장 DCIR.sch | 33 | 777 | 156 | DCIR 3885mAh |
| 260226_260228_05_문현규_3885mAh_PA1 연속저장 DCIR.sch | 33 | 777 | 156 | DCIR 3885mAh |
| 260226_260228_05_문현규_3885mAh_PA1 연속저장 DCIR_000.sch | 33 | 777 | 156 | DCIR 3885mAh |
| 260226_260228_05_문현규_3885mAh_PA1 연속저장 DCIR.sch | 33 | 777 | 156 | DCIR 3885mAh |

## H5 — REST mode=0 + chamber≠0 의 keyword 분포 (보관/대기 가설)

가설: chamber ≠ 0 인 REST mode=0 = 환경 control 필요한 보관/대기 step (= ECT/floating).

### REST mode=0 + chamber≠0 의 keyword 분포 (n=2418)

| keyword | count | chamber 값 분포 (top 5) |
|---|---|---|
| ect | 2389 | 23°C:1280, 45°C:815, -10°C:192, 15°C:57, -5°C:45 |
| gitt | 25 | 23°C:25 |
| soc_dcir | 4 | 23°C:4 |

### REST mode=1 (chamber 1.6%만 사용) keyword 분포

| keyword | count |
|---|---|
| accel_si | 2242 |
| hysteresis | 810 |
| other | 752 |
| rss | 386 |
| soc_dcir | 168 |
| formation | 48 |
| dcir | 34 |
| floating | 28 |
| gitt | 24 |
| ect | 16 |

## H6 — LOOP body 내 mode=1 step 수 vs loop_count 상관

가설: mode=1 step = "사이클 카운트에 인입되는 step". LOOP loop_count 와 body 내 mode=1 step 의 비율이 의미 있는 패턴 형성.

- 분석한 LOOP body 그룹: 4367

### loop_count 구간 별 body 내 mode=1 비율

| loop_count | n_groups | body 내 mode=1 평균 % | min~max % |
|---|---|---|---|
| N=1 | 3469 | 59.2% | 0.0~100.0% |
| N=2~5 | 49 | 79.6% | 0.0~100.0% |
| N=6~10 | 119 | 64.4% | 0.0~100.0% |
| N=11~19 | 26 | 69.2% | 0.0~100.0% |
| N=20~99 | 627 | 91.2% | 0.0~100.0% |
| N=100~999 | 77 | 44.6% | 0.0~100.0% |

### keyword × loop_count bucket 별 body 내 mode=1 비율

| keyword | N=1 | N=2~10 | N=11~19 | N=20~99 | N=100~999 | N≥1000 |
|---|---|---|---|---|---|---|
| accel_si | 100% (n=704) | - | - | 100% (n=431) | 100% (n=30) | - |
| dcir | 76% (n=39) | 85% (n=20) | - | - | - | - |
| ect | 25% (n=1451) | 89% (n=9) | - | 40% (n=67) | - | - |
| floating | 20% (n=222) | 34% (n=34) | 43% (n=14) | - | 0% (n=16) | - |
| formation | 50% (n=32) | 100% (n=16) | - | - | - | - |
| gitt | 66% (n=60) | 6% (n=18) | - | 42% (n=25) | 14% (n=31) | - |
| hysteresis | 100% (n=519) | - | - | - | - | - |
| other | 77% (n=300) | 85% (n=57) | - | 98% (n=38) | - | - |
| rss | 79% (n=120) | - | - | 100% (n=54) | - | - |
| soc_dcir | 66% (n=22) | 100% (n=14) | 100% (n=12) | 100% (n=12) | - | - |

## H7 — mode=257 6건 full sequence context

가설: bit 8 = "schedule init conditioning step" — 시험 첫 step 의 1초 셀 점검 DCHG.

### 240919 선행랩 류성택  Gen4pGr ATL-mini-WD-Proto-422mAh-20C-450V-SO

| step# | type | mode | I (mA) | t (s) | V (mV) | EC | desc |
|---|---|---|---|---|---|---|---|
| 1 | DCHG_CC | 257 | 422 | 1 | 0 | 0 | SOC��DCIR������_422mAh |
| 1 | DCHG_CC | 257 | 422 | 1 | 0 | 0 | SOC��DCIR������_422mAh |
| 2 | LOOP | 0 | 0 | 0 | 0 | 0 | SOC��DCIR������_422mAh |
| 2 | LOOP | 0 | 0 | 0 | 0 | 0 | SOC��DCIR������_422mAh |
| 3 | REST_SAFE | 0 | 0 | 0 | 0 | 0 | SOC��DCIR������_422mAh |
| 3 | REST_SAFE | 0 | 0 | 0 | 0 | 0 | SOC��DCIR������_422mAh |

### 250513_250526_05_나무늬_2610mAh_Gen5+B SDI MP1 DoE SBR 0.7 DCIR

| step# | type | mode | I (mA) | t (s) | V (mV) | EC | desc |
|---|---|---|---|---|---|---|---|
| 1 | DCHG_CC | 257 | 2610 | 1 | 0 | 0 | SOC�� DCIR ������_2610mAh |
| 2 | LOOP | 0 | 0 | 0 | 0 | 0 | SOC�� DCIR ������_2610mAh |
| 3 | REST_SAFE | 0 | 0 | 0 | 0 | 0 | SOC�� DCIR ������_2610mAh |
| 4 | CHG_CCCV | 1 | 2088 | 0 | 0 | 0 | SOC�� DCIR ������_2610mAh |
| 5 | REST | 1 | 0 | 600 | 0 | 0 | SOC�� DCIR ������_2610mAh |
| 6 | DCHG_CC | 1 | 1307 | 0 | 3000 | 0 | SOC�� DCIR ������_2610mAh |

### 250513_250526_05_나무늬_2610mAh_Gen5+B SDI MP1 Main SBR 0.9 DCI

| step# | type | mode | I (mA) | t (s) | V (mV) | EC | desc |
|---|---|---|---|---|---|---|---|
| 1 | DCHG_CC | 257 | 2610 | 1 | 0 | 0 | SOC�� DCIR ������_2610mAh |
| 2 | LOOP | 0 | 0 | 0 | 0 | 0 | SOC�� DCIR ������_2610mAh |
| 3 | REST_SAFE | 0 | 0 | 0 | 0 | 0 | SOC�� DCIR ������_2610mAh |
| 4 | CHG_CCCV | 1 | 2088 | 0 | 0 | 0 | SOC�� DCIR ������_2610mAh |
| 5 | REST | 1 | 0 | 600 | 0 | 0 | SOC�� DCIR ������_2610mAh |
| 6 | DCHG_CC | 1 | 1307 | 0 | 3000 | 0 | SOC�� DCIR ������_2610mAh |

### 260306_260318_05_현혜정_6330mAh_LWN 25P(after LT100cy) SOC별 DCI

| step# | type | mode | I (mA) | t (s) | V (mV) | EC | desc |
|---|---|---|---|---|---|---|---|
| 1 | DCHG_CC | 257 | 6330 | 1 | 0 | 0 | LWN Si25P SPL 6330mAh SOC�� DCIR v251124 |
| 1 | DCHG_CC | 257 | 6330 | 1 | 0 | 0 | LWN Si25P SPL 6330mAh SOC�� DCIR v251124 |
| 2 | LOOP | 0 | 0 | 0 | 0 | 0 | LWN Si25P SPL 6330mAh SOC�� DCIR v251124 |
| 2 | LOOP | 0 | 0 | 0 | 0 | 0 | LWN Si25P SPL 6330mAh SOC�� DCIR v251124 |
| 3 | REST_SAFE | 0 | 0 | 0 | 0 | 0 | LWN Si25P SPL 6330mAh SOC�� DCIR v251124 |
| 3 | REST_SAFE | 0 | 0 | 0 | 0 | 0 | LWN Si25P SPL 6330mAh SOC�� DCIR v251124 |
