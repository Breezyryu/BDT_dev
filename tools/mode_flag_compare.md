# mode_flag=0 vs 1 — V/I/t 분포 정밀 비교

- Source: `mode_flag_step_dump.csv` (28779 step rows)

## CHG_CC

- total = 1540 (mode=1: **1433** (93%), mode=0: **107** (7%))

### 통계 비교 (mode=1 vs mode=0)

| field | mode=1 stats | mode=1 top values | mode=0 stats | mode=0 top values |
|---|---|---|---|---|
| **+12/+16 V (display)** | n=1433, nz=1433, min=2500.0, med=4300.0, mean=4330.7, max=4650.0 | 4300:1062, 4550:168, 4530:103, 4500:36 | n=107, nz=107, min=4221.0, med=4470.0, mean=4402.2, max=4600.0 | 4470:26, 4600:22, 4300:17, 4221:16 |
| **+20 current (mA)** | n=1433, nz=1433, min=0.0, med=3912.0, mean=4066.8, max=11323.0 | 4670:389, 3853:288, 3852:101, 4640:72 | n=107, nz=107, min=0.3, med=501.0, mean=3859.8, max=9710.0 | 0:16, 501:16, 413:16, 9510:13 |
| **+24 time (s)** | n=1433, nz=50, min=360.0, med=3600.0, mean=2714.4, max=3600.0 | 3600:36, 360:11, 720:3 | n=107, nz=25, min=180.0, med=360.0, mean=302.4, max=360.0 | 360:17, 180:8 |
| **+28 V end (mV)** | n=1433, nz=1220, min=2000.0, med=4140.0, mean=4118.4, max=4600.0 | 4140:573, 4160:573, 4130:14, 4150:14 | n=107, nz=107, min=4100.0, med=4240.0, mean=4292.9, max=4590.0 | 4220:32, 4240:32, 4550:16, 4160:11 |
| **+32 I end (mA)** | all 0 (n=1433) | (all 0) | all 0 (n=107) | (all 0) |
| **+336 rec_iv (s)** | n=1433, nz=1433, min=1.0, med=5.0, mean=19.6, max=300.1 | 5:994, 60:261, 10:140, 300:20 | n=107, nz=107, min=1.0, med=60.0, mean=86.0, max=300.1 | 60:73, 1:18, 300:16 |
| **+396 chamber (°C)** | n=1433, nz=36, min=23.0, med=23.0, mean=27.9, max=45.0 | 23:28, 45:8 | n=107, nz=30, min=-5.0, med=23.0, mean=24.5, max=45.0 | 23:23, 45:4, 15:2, -5:1 |

- EC enabled (+504=1): mode=1 → 213/1433 (14.9%), mode=0 → 0/107 (0.0%)

### +28 V end (mV) histogram — V cutoff 의미 비교

- mode=1: zero=213 | <3000=14 | 3.0~4.0kV=14 | 4.0~4.15kV=587 | 4.15~4.25kV=595 | 4.25~4.35kV=0 | 4.35~4.45kV=0 | 4.45~4.6kV=8 | ≥4.6kV=2
- mode=0: zero=0 | <3000=0 | 3.0~4.0kV=0 | 4.0~4.15kV=6 | 4.15~4.25kV=75 | 4.25~4.35kV=0 | 4.35~4.45kV=0 | 4.45~4.6kV=26 | ≥4.6kV=0

### +24 time (s) histogram

- mode=1: 0=1383 | 1~30s=0 | 30s~10m=11 | 10m~1h=3 | 1h~12h=36 | ≥12h=0
- mode=0: 0=82 | 1~30s=0 | 30s~10m=25 | 10m~1h=0 | 1h~12h=0 | ≥12h=0

## CHG_CCCV

- total = 4342 (mode=1: **3497** (81%), mode=0: **845** (19%))

### 통계 비교 (mode=1 vs mode=0)

| field | mode=1 stats | mode=1 top values | mode=0 stats | mode=0 top values |
|---|---|---|---|---|
| **+12/+16 V (display)** | n=3497, nz=3497, min=4140.0, med=4510.0, mean=4473.6, max=4570.0 | 4550:1091, 4530:578, 4300:573, 4510:354 | n=845, nz=845, min=4200.0, med=4500.0, mean=4494.4, max=4550.0 | 4470:336, 4530:260, 4550:135, 4500:66 |
| **+20 current (mA)** | n=3497, nz=3497, min=0.3, med=1177.0, mean=1874.3, max=9800.0 | 466:645, 2335:383, 3269:333, 972:245 | n=845, nz=845, min=3.4, med=972.0, mean=1623.4, max=11764.0 | 972:165, 951:114, 1177:111, 251:40 |
| **+24 time (s)** | n=3497, nz=1446, min=1.0, med=7200.0, mean=68790.8, max=17193600.0 | 7200:634, 25200:464, 20:134, 3600:116 | n=845, nz=121, min=1.0, med=1.0, mean=1553802.3, max=10368000.0 | 1:78, 7776000:16, 86400:14, 25200:7 |
| **+28 V end (mV)** | all 0 (n=3497) | (all 0) | all 0 (n=845) | (all 0) |
| **+32 I end (mA)** | n=3497, nz=3377, min=0.1, med=118.0, mean=700.6, max=5706.0 | 48:645, 2320:461, 234:458, 98:365 | n=845, nz=653, min=0.1, med=98.0, mean=312.1, max=4855.0 | 98:203, 118:140, 96:107, 5:32 |
| **+336 rec_iv (s)** | n=3497, nz=3497, min=0.1, med=60.0, mean=36.2, max=60.0 | 60:1756, 10:581, 1:556, 30:494 | n=845, nz=845, min=0.1, med=1.0, mean=23.9, max=300.1 | 1:495, 60:288, 0:54, 300:8 |
| **+396 chamber (°C)** | n=3497, nz=538, min=23.0, med=23.0, mean=27.2, max=45.0 | 23:436, 45:102 | n=845, nz=487, min=-5.0, med=23.0, mean=27.1, max=45.0 | 23:324, 45:123, 15:21, -5:19 |

- EC enabled (+504=1): mode=1 → 152/3497 (4.3%), mode=0 → 54/845 (6.4%)

### +28 V end (mV) histogram — V cutoff 의미 비교

- mode=1: zero=3497 | <3000=0 | 3.0~4.0kV=0 | 4.0~4.15kV=0 | 4.15~4.25kV=0 | 4.25~4.35kV=0 | 4.35~4.45kV=0 | 4.45~4.6kV=0 | ≥4.6kV=0
- mode=0: zero=845 | <3000=0 | 3.0~4.0kV=0 | 4.0~4.15kV=0 | 4.15~4.25kV=0 | 4.25~4.35kV=0 | 4.35~4.45kV=0 | 4.45~4.6kV=0 | ≥4.6kV=0

### +24 time (s) histogram

- mode=1: 0=2051 | 1~30s=164 | 30s~10m=24 | 10m~1h=0 | 1h~12h=1232 | ≥12h=24
- mode=0: 0=724 | 1~30s=78 | 30s~10m=0 | 10m~1h=0 | 1h~12h=7 | ≥12h=30

## CHG_CP

- total = 108 (mode=1: **71** (66%), mode=0: **37** (34%))

### 통계 비교 (mode=1 vs mode=0)

| field | mode=1 stats | mode=1 top values | mode=0 stats | mode=0 top values |
|---|---|---|---|---|
| **+12/+16 V (display)** | n=71, nz=71, min=4510.0, med=4510.0, mean=4523.1, max=4540.0 | 4510:40, 4540:31 | n=37, nz=37, min=4510.0, med=4520.0, mean=4521.6, max=4540.0 | 4520:22, 4510:8, 4540:7 |
| **+20 current (mA)** | all 0 (n=71) | (all 0) | all 0 (n=37) | (all 0) |
| **+24 time (s)** | all 0 (n=71) | (all 0) | all 0 (n=37) | (all 0) |
| **+28 V end (mV)** | n=71, nz=71, min=4470.0, med=4470.0, mean=4496.2, max=4530.0 | 4470:40, 4530:31 | n=37, nz=37, min=4470.0, med=4470.0, mean=4481.4, max=4530.0 | 4470:30, 4530:7 |
| **+32 I end (mA)** | n=71, nz=71, min=2750.0, med=2750.0, mean=2859.2, max=3000.0 | 2750:40, 3000:31 | n=37, nz=37, min=2750.0, med=2750.0, mean=2797.3, max=3000.0 | 2750:30, 3000:7 |
| **+336 rec_iv (s)** | n=71, nz=71, min=1.0, med=1.0, mean=1.0, max=1.0 | 1:71 | n=37, nz=37, min=1.0, med=1.0, mean=1.0, max=1.0 | 1:37 |
| **+396 chamber (°C)** | n=71, nz=52, min=-10.0, med=23.0, mean=14.8, max=45.0 | 23:24, -10:19, 45:9 | n=37, nz=37, min=-5.0, med=23.0, mean=28.6, max=45.0 | 45:16, 23:13, 15:4, -5:4 |

- EC enabled (+504=1): mode=1 → 0/71 (0.0%), mode=0 → 0/37 (0.0%)

### +28 V end (mV) histogram — V cutoff 의미 비교

- mode=1: zero=0 | <3000=0 | 3.0~4.0kV=0 | 4.0~4.15kV=0 | 4.15~4.25kV=0 | 4.25~4.35kV=0 | 4.35~4.45kV=0 | 4.45~4.6kV=71 | ≥4.6kV=0
- mode=0: zero=0 | <3000=0 | 3.0~4.0kV=0 | 4.0~4.15kV=0 | 4.15~4.25kV=0 | 4.25~4.35kV=0 | 4.35~4.45kV=0 | 4.45~4.6kV=37 | ≥4.6kV=0

### +24 time (s) histogram

- mode=1: 0=71 | 1~30s=0 | 30s~10m=0 | 10m~1h=0 | 1h~12h=0 | ≥12h=0
- mode=0: 0=37 | 1~30s=0 | 30s~10m=0 | 10m~1h=0 | 1h~12h=0 | ≥12h=0

## DCHG_CC

- total = 5420 (mode=1: **4461** (82%), mode=0: **953** (18%))

### 통계 비교 (mode=1 vs mode=0)

| field | mode=1 stats | mode=1 top values | mode=0 stats | mode=0 top values |
|---|---|---|---|---|
| **+12/+16 V (display)** | n=4461, nz=4461, min=1.0, med=2500.0, mean=2479.5, max=2700.0 | 2500:3615, 2700:516, 1900:250, 2400:50 | n=953, nz=953, min=1.0, med=2600.0, mean=2587.3, max=3000.0 | 2600:480, 2500:282, 2900:72, 3000:48 |
| **+20 current (mA)** | n=4461, nz=4461, min=0.0, med=999.0, mean=1423.1, max=5882.0 | 466:675, 1160:440, 2335:346, 477:208 | n=953, nz=953, min=0.3, med=972.0, mean=1298.2, max=16993.0 | 972:199, 1177:132, 951:93, 50:56 |
| **+24 time (s)** | n=4461, nz=2295, min=0.1, med=18000.0, mean=11603.7, max=21600.0 | 18000:979, 1:515, 21600:414, 0:93 | n=953, nz=134, min=0.1, med=1.0, mean=23764.6, max=432000.0 | 1:78, 360:20, 180:11, 0:11 |
| **+28 V end (mV)** | n=4461, nz=3119, min=10.0, med=3000.0, mean=3056.6, max=3750.0 | 2750:723, 3000:712, 3650:556, 2900:540 | n=953, nz=766, min=10.0, med=2750.0, mean=2825.1, max=3400.0 | 2750:474, 3000:186, 3300:68, 2000:14 |
| **+32 I end (mA)** | all 0 (n=4461) | (all 0) | all 0 (n=953) | (all 0) |
| **+336 rec_iv (s)** | n=4461, nz=4461, min=0.1, med=60.0, mean=39.8, max=300.1 | 60:2833, 1:1030, 0:576, 300:16 | n=953, nz=953, min=0.1, med=1.0, mean=26.8, max=300.1 | 1:557, 60:304, 0:65, 300:22 |
| **+396 chamber (°C)** | n=4461, nz=391, min=-10.0, med=23.0, mean=9.6, max=45.0 | 23:187, -10:177, 45:27 | n=953, nz=529, min=-5.0, med=23.0, mean=29.1, max=45.0 | 23:325, 45:172, 15:16, -5:16 |

- EC enabled (+504=1): mode=1 → 630/4461 (14.1%), mode=0 → 85/953 (8.9%)

### +28 V end (mV) histogram — V cutoff 의미 비교

- mode=1: zero=1342 | <3000=1343 | 3.0~4.0kV=1776 | 4.0~4.15kV=0 | 4.15~4.25kV=0 | 4.25~4.35kV=0 | 4.35~4.45kV=0 | 4.45~4.6kV=0 | ≥4.6kV=0
- mode=0: zero=187 | <3000=505 | 3.0~4.0kV=261 | 4.0~4.15kV=0 | 4.15~4.25kV=0 | 4.25~4.35kV=0 | 4.35~4.45kV=0 | 4.45~4.6kV=0 | ≥4.6kV=0

### +24 time (s) histogram

- mode=1: 0=2352 | 1~30s=680 | 30s~10m=29 | 10m~1h=3 | 1h~12h=1397 | ≥12h=0
- mode=0: 0=830 | 1~30s=78 | 30s~10m=31 | 10m~1h=0 | 1h~12h=7 | ≥12h=7

## DCHG_CCCV

- total = 89 (mode=1: **58** (65%), mode=0: **31** (35%))

### 통계 비교 (mode=1 vs mode=0)

| field | mode=1 stats | mode=1 top values | mode=0 stats | mode=0 top values |
|---|---|---|---|---|
| **+12/+16 V (display)** | n=58, nz=58, min=10.0, med=3000.0, mean=2610.0, max=3300.0 | 3000:31, 3300:11, 10:8, 2750:8 | n=31, nz=31, min=2900.0, med=2900.0, mean=2900.0, max=2900.0 | 2900:31 |
| **+20 current (mA)** | n=58, nz=58, min=0.4, med=971.0, mean=1070.2, max=2428.0 | 777:15, 971:12, 0:8, 1266:8 | n=31, nz=31, min=777.0, med=971.0, mean=892.1, max=1087.0 | 777:15, 971:12, 1087:4 |
| **+24 time (s)** | all 0 (n=58) | (all 0) | all 0 (n=31) | (all 0) |
| **+28 V end (mV)** | all 0 (n=58) | (all 0) | all 0 (n=31) | (all 0) |
| **+32 I end (mA)** | n=58, nz=58, min=0.1, med=98.0, mean=148.4, max=379.0 | 78:15, 98:12, 0:8, 254:8 | n=31, nz=31, min=156.0, med=195.0, mean=179.1, max=218.0 | 156:15, 195:12, 218:4 |
| **+336 rec_iv (s)** | n=58, nz=58, min=60.0, med=60.0, mean=60.0, max=60.0 | 60:58 | n=31, nz=31, min=60.0, med=60.0, mean=60.0, max=60.0 | 60:31 |
| **+396 chamber (°C)** | n=58, nz=8, min=23.0, med=23.0, mean=23.0, max=23.0 | 23:8 | all 0 (n=31) | (all 0) |

- EC enabled (+504=1): mode=1 → 4/58 (6.9%), mode=0 → 31/31 (100.0%)

### +28 V end (mV) histogram — V cutoff 의미 비교

- mode=1: zero=58 | <3000=0 | 3.0~4.0kV=0 | 4.0~4.15kV=0 | 4.15~4.25kV=0 | 4.25~4.35kV=0 | 4.35~4.45kV=0 | 4.45~4.6kV=0 | ≥4.6kV=0
- mode=0: zero=31 | <3000=0 | 3.0~4.0kV=0 | 4.0~4.15kV=0 | 4.15~4.25kV=0 | 4.25~4.35kV=0 | 4.35~4.45kV=0 | 4.45~4.6kV=0 | ≥4.6kV=0

### +24 time (s) histogram

- mode=1: 0=58 | 1~30s=0 | 30s~10m=0 | 10m~1h=0 | 1h~12h=0 | ≥12h=0
- mode=0: 0=31 | 1~30s=0 | 30s~10m=0 | 10m~1h=0 | 1h~12h=0 | ≥12h=0

## REST

- total = 8466 (mode=1: **4508** (53%), mode=0: **3958** (47%))

### 통계 비교 (mode=1 vs mode=0)

| field | mode=1 stats | mode=1 top values | mode=0 stats | mode=0 top values |
|---|---|---|---|---|
| **+12/+16 V (display)** | all 0 (n=4508) | (all 0) | all 0 (n=3958) | (all 0) |
| **+20 current (mA)** | all 0 (n=4508) | (all 0) | all 0 (n=3958) | (all 0) |
| **+24 time (s)** | n=4508, nz=4508, min=1.0, med=600.0, mean=1004.5, max=36000.0 | 600:3849, 1860:216, 1800:181, 3600:84 | n=3958, nz=3958, min=1.0, med=1800.0, mean=2915.4, max=21600.0 | 3600:1069, 1800:870, 600:791, 60:691 |
| **+28 V end (mV)** | all 0 (n=4508) | (all 0) | all 0 (n=3958) | (all 0) |
| **+32 I end (mA)** | all 0 (n=4508) | (all 0) | all 0 (n=3958) | (all 0) |
| **+336 rec_iv (s)** | n=4508, nz=4508, min=1.0, med=60.0, mean=69.4, max=600.0 | 60:4302, 300:148, 1:34, 600:16 | n=3958, nz=3958, min=1.0, med=1.0, mean=75.5, max=300.1 | 1:2594, 300:830, 60:470, 300:63 |
| **+396 chamber (°C)** | n=4508, nz=72, min=23.0, med=23.0, mean=23.0, max=23.0 | 23:72 | n=3958, nz=2418, min=-10.0, med=23.0, mean=27.1, max=45.0 | 23:1309, 45:815, -10:192, 15:57 |

- EC enabled (+504=1): mode=1 → 0/4508 (0.0%), mode=0 → 0/3958 (0.0%)

### +24 time (s) histogram

- mode=1: 0=0 | 1~30s=11 | 30s~10m=0 | 10m~1h=4306 | 1h~12h=191 | ≥12h=0
- mode=0: 0=0 | 1~30s=58 | 30s~10m=691 | 10m~1h=1817 | 1h~12h=1392 | ≥12h=0

## REST_SAFE

- total = 4005 (mode=1: **999** (25%), mode=0: **3006** (75%))

### 통계 비교 (mode=1 vs mode=0)

| field | mode=1 stats | mode=1 top values | mode=0 stats | mode=0 top values |
|---|---|---|---|---|
| **+12/+16 V (display)** | all 0 (n=999) | (all 0) | all 0 (n=3006) | (all 0) |
| **+20 current (mA)** | all 0 (n=999) | (all 0) | all 0 (n=3006) | (all 0) |
| **+24 time (s)** | all 0 (n=999) | (all 0) | all 0 (n=3006) | (all 0) |
| **+28 V end (mV)** | all 0 (n=999) | (all 0) | all 0 (n=3006) | (all 0) |
| **+32 I end (mA)** | all 0 (n=999) | (all 0) | all 0 (n=3006) | (all 0) |
| **+336 rec_iv (s)** | all 0 (n=999) | (all 0) | all 0 (n=3006) | (all 0) |
| **+396 chamber (°C)** | all 0 (n=999) | (all 0) | all 0 (n=3006) | (all 0) |

- EC enabled (+504=1): mode=1 → 0/999 (0.0%), mode=0 → 0/3006 (0.0%)

### +24 time (s) histogram

- mode=1: 0=999 | 1~30s=0 | 30s~10m=0 | 10m~1h=0 | 1h~12h=0 | ≥12h=0
- mode=0: 0=3006 | 1~30s=0 | 30s~10m=0 | 10m~1h=0 | 1h~12h=0 | ≥12h=0

## LOOP

- total = 4367 (mode=1: **2240** (51%), mode=0: **2127** (49%))

### 통계 비교 (mode=1 vs mode=0)

| field | mode=1 stats | mode=1 top values | mode=0 stats | mode=0 top values |
|---|---|---|---|---|
| **+12/+16 V (display)** | all 0 (n=2240) | (all 0) | all 0 (n=2127) | (all 0) |
| **+20 current (mA)** | all 0 (n=2240) | (all 0) | all 0 (n=2127) | (all 0) |
| **+24 time (s)** | all 0 (n=2240) | (all 0) | all 0 (n=2127) | (all 0) |
| **+28 V end (mV)** | all 0 (n=2240) | (all 0) | all 0 (n=2127) | (all 0) |
| **+32 I end (mA)** | all 0 (n=2240) | (all 0) | all 0 (n=2127) | (all 0) |
| **+336 rec_iv (s)** | all 0 (n=2240) | (all 0) | all 0 (n=2127) | (all 0) |
| **+396 chamber (°C)** | all 0 (n=2240) | (all 0) | all 0 (n=2127) | (all 0) |

- EC enabled (+504=1): mode=1 → 0/2240 (0.0%), mode=0 → 0/2127 (0.0%)

### +24 time (s) histogram

- mode=1: 0=2240 | 1~30s=0 | 30s~10m=0 | 10m~1h=0 | 1h~12h=0 | ≥12h=0
- mode=0: 0=2127 | 1~30s=0 | 30s~10m=0 | 10m~1h=0 | 1h~12h=0 | ≥12h=0

## GOTO

- total = 367 (mode=1: **62** (17%), mode=0: **305** (83%))

### 통계 비교 (mode=1 vs mode=0)

| field | mode=1 stats | mode=1 top values | mode=0 stats | mode=0 top values |
|---|---|---|---|---|
| **+12/+16 V (display)** | all 0 (n=62) | (all 0) | all 0 (n=305) | (all 0) |
| **+20 current (mA)** | all 0 (n=62) | (all 0) | all 0 (n=305) | (all 0) |
| **+24 time (s)** | all 0 (n=62) | (all 0) | all 0 (n=305) | (all 0) |
| **+28 V end (mV)** | all 0 (n=62) | (all 0) | all 0 (n=305) | (all 0) |
| **+32 I end (mA)** | all 0 (n=62) | (all 0) | all 0 (n=305) | (all 0) |
| **+336 rec_iv (s)** | all 0 (n=62) | (all 0) | all 0 (n=305) | (all 0) |
| **+396 chamber (°C)** | all 0 (n=62) | (all 0) | all 0 (n=305) | (all 0) |

- EC enabled (+504=1): mode=1 → 0/62 (0.0%), mode=0 → 0/305 (0.0%)

### +24 time (s) histogram

- mode=1: 0=62 | 1~30s=0 | 30s~10m=0 | 10m~1h=0 | 1h~12h=0 | ≥12h=0
- mode=0: 0=305 | 1~30s=0 | 30s~10m=0 | 10m~1h=0 | 1h~12h=0 | ≥12h=0

## GITT_START

- total = 28 (mode=1: **7** (25%), mode=0: **21** (75%))

### 통계 비교 (mode=1 vs mode=0)

| field | mode=1 stats | mode=1 top values | mode=0 stats | mode=0 top values |
|---|---|---|---|---|
| **+12/+16 V (display)** | all 0 (n=7) | (all 0) | all 0 (n=21) | (all 0) |
| **+20 current (mA)** | all 0 (n=7) | (all 0) | all 0 (n=21) | (all 0) |
| **+24 time (s)** | all 0 (n=7) | (all 0) | all 0 (n=21) | (all 0) |
| **+28 V end (mV)** | all 0 (n=7) | (all 0) | all 0 (n=21) | (all 0) |
| **+32 I end (mA)** | all 0 (n=7) | (all 0) | all 0 (n=21) | (all 0) |
| **+336 rec_iv (s)** | all 0 (n=7) | (all 0) | all 0 (n=21) | (all 0) |
| **+396 chamber (°C)** | all 0 (n=7) | (all 0) | all 0 (n=21) | (all 0) |

- EC enabled (+504=1): mode=1 → 0/7 (0.0%), mode=0 → 0/21 (0.0%)

### +24 time (s) histogram

- mode=1: 0=7 | 1~30s=0 | 30s~10m=0 | 10m~1h=0 | 1h~12h=0 | ≥12h=0
- mode=0: 0=21 | 1~30s=0 | 30s~10m=0 | 10m~1h=0 | 1h~12h=0 | ≥12h=0

## CHG_CC: mode=1 의 V cutoff 가 multi-step charge 인지 검증

가설: mode=1 = multi-step charge intermediate (4.14/4.16/4.30/4.55V 점진적), mode=0 = standard cutoff (4.30/4.55V 단일)

### CHG_CC +28 V end value top 15

| value (mV) | mode=1 count | mode=0 count |
|---|---|---|
| 4160 | 573 | 11 |
| 4140 | 573 | 3 |
| 4240 | 0 | 32 |
| 4220 | 0 | 32 |
| 4550 | 8 | 16 |
| 4130 | 14 | 0 |
| 4150 | 14 | 0 |
| 2000 | 8 | 0 |
| 3000 | 8 | 0 |
| 2500 | 6 | 0 |
| 3050 | 6 | 0 |
| 4230 | 4 | 0 |
| 4210 | 4 | 0 |
| 4530 | 0 | 4 |
| 4100 | 0 | 3 |

### CHG_CC +20 current (mA) top 10

| value (mA) | mode=1 count | mode=0 count |
|---|---|---|
| 3850 | 389 | 0 |
| 4670 | 389 | 0 |
| 4640 | 72 | 0 |
| 3830 | 72 | 0 |
| 1000 | 55 | 0 |
| 0 | 38 | 16 |
| 1270 | 45 | 0 |
| 4100 | 42 | 0 |
| 4970 | 42 | 0 |
| 4740 | 40 | 0 |

## REST: mode=1 짧은 vs mode=0 긴 휴지 가설

### REST +24 time (s) 분포 cross

| time bucket | mode=1 | mode=0 |
|---|---|---|
| 0~60s | 11 | 58 |
| 1~10m | 0 | 691 |
| 10~30m | 3909 | 947 |
| 30m~1h | 397 | 870 |
| 1~12h | 191 | 1392 |
| 12~24h | 0 | 0 |
| ≥24h | 0 | 0 |

### REST chamber 온도 사용 (+396 비0)

- mode=1: 72/4508 (1.6%) chamber 명시
- mode=0: 2418/3958 (61.1%) chamber 명시

→ chamber 명시 = 시험 환경 control 필요한 보관/대기 step (= longer rest)

## per-file step position 분석

한 파일 내에서 mode_flag=0 step 의 step_num 분포 — schedule 시작/끝/중간 어디 위치?

### Step normalized position (시작=0, 끝=1) 분포

- mode=1 (n=17336): 0~10%=6737 | 10~30%=6124 | 30~70%=3244 | 70~90%=824 | 90~100%=407
- mode=0 (n=11437): 0~10%=2833 | 10~30%=3379 | 30~70%=3319 | 70~90%=1245 | 90~100%=661

## "loop body vs boundary" 가설 검증

가설: mode=1 = 반복 사이클 내부 (loop body), mode=0 = setup/boundary (LOOP/GOTO/REST_SAFE 인근, schedule init/end)

| 위치 컨텍스트 | mode=0 | mode=1 | mode=257 |
|---|---|---|---|
| schedule 첫 step | 71 | 129 | 4 |
| schedule 마지막 step | 190 | 14 | 0 |
| LOOP 직전 step | 2132 | 2229 | 6 |
| REST_SAFE 직후 step | 1107 | 2898 | 0 |
| 일반 body step | 5927 | 13906 | 2 |
