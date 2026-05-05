# ECT 분류 79 group 실제 step pattern 검증

> 사용자 지적 — "ECT (신규) 는 단순 rest 가 긴 거 아닌가?"
> → ECT 분류된 group 의 body step pattern 을 raw 로 확인하여 검증.

- v3 ECT groups: **79**
- unique sch files: **70**

## 1. ECT group 의 body 구성 통계

| 통계 | 값 |
|---|---|
| body size | min=4, mean=7.1, max=20 |
| n_chg | min=1, mean=3.0, max=4 |
| n_dchg | min=1, mean=1.1, max=3 |
| n_rest | min=2, mean=2.8, max=7 |
| loop_count (N) | min=7, mean=30.8, max=120 |

### "단순 1-step REST" 케이스: **0 / 79** (0%)

## 2. ECT 분류 group 의 실제 body step sequence (대표 sample)

### 250827_251028_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter1.sch
- group_idx=0, TC=1-30, N=30, body=7, sub_tag=mode_flag_chamber
- desc: 4755mAh_ECT ����1 ACT ����
- chamber=23.0°C

| step# | type | mode | I (mA) | t (s) | V cut (mV) | V disp (mV) | rec_iv | chamber |
|---|---|---|---|---|---|---|---|---|
| 1 | CHG_CC | 0 | 9510 | 0 | 4220 | 4470 | 60.0 | 23 |
| 2 | CHG_CC | 0 | 7846 | 0 | 4240 | 4470 | 60.0 | 23 |
| 3 | CHG_CCCV | 0 | 6657 | 0 | 0 | 4300 | 60.0 | 23 |
| 4 | CHG_CCCV | 0 | 4755 | 0 | 0 | 4470 | 60.0 | 23 |
| 5 | REST | 0 | 0 | 60 | 0 | 0 | 60.0 | 23 |
| 6 | DCHG_CC | 0 | 2378 | 0 | 3300 | 2600 | 60.0 | 23 |
| 7 | REST | 0 | 0 | 60 | 0 | 0 | 60.0 | 23 |

### 250827_251028_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter2.sch
- group_idx=0, TC=1-30, N=30, body=7, sub_tag=mode_flag_chamber
- desc: 4755mAh_ECT ����2 ACT ����
- chamber=23.0°C

| step# | type | mode | I (mA) | t (s) | V cut (mV) | V disp (mV) | rec_iv | chamber |
|---|---|---|---|---|---|---|---|---|
| 1 | CHG_CC | 0 | 9510 | 0 | 4220 | 4470 | 60.0 | 23 |
| 2 | CHG_CC | 0 | 7846 | 0 | 4240 | 4470 | 60.0 | 23 |
| 3 | CHG_CCCV | 0 | 6657 | 0 | 0 | 4300 | 60.0 | 23 |
| 4 | CHG_CCCV | 0 | 4755 | 0 | 0 | 4470 | 60.0 | 23 |
| 5 | REST | 0 | 0 | 60 | 0 | 0 | 60.0 | 23 |
| 6 | DCHG_CC | 0 | 2378 | 0 | 3300 | 2600 | 60.0 | 23 |
| 7 | REST | 0 | 0 | 60 | 0 | 0 | 60.0 | 23 |

### 250827_251028_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter3.sch
- group_idx=0, TC=1-30, N=30, body=7, sub_tag=mode_flag_chamber
- desc: 4755mAh_ECT ����3 ACT ����
- chamber=23.0°C

| step# | type | mode | I (mA) | t (s) | V cut (mV) | V disp (mV) | rec_iv | chamber |
|---|---|---|---|---|---|---|---|---|
| 1 | CHG_CC | 0 | 9510 | 0 | 4220 | 4470 | 60.0 | 23 |
| 2 | CHG_CC | 0 | 7846 | 0 | 4240 | 4470 | 60.0 | 23 |
| 3 | CHG_CCCV | 0 | 6657 | 0 | 0 | 4300 | 60.0 | 23 |
| 4 | CHG_CCCV | 0 | 4755 | 0 | 0 | 4470 | 60.0 | 23 |
| 5 | REST | 0 | 0 | 60 | 0 | 0 | 60.0 | 23 |
| 6 | DCHG_CC | 0 | 2378 | 0 | 3300 | 2600 | 60.0 | 23 |
| 7 | REST | 0 | 0 | 60 | 0 | 0 | 60.0 | 23 |

### 250827_251028_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter4.sch
- group_idx=0, TC=1-30, N=30, body=7, sub_tag=mode_flag_chamber
- desc: 4755mAh_ECT ����4 ACT ����
- chamber=23.0°C

| step# | type | mode | I (mA) | t (s) | V cut (mV) | V disp (mV) | rec_iv | chamber |
|---|---|---|---|---|---|---|---|---|
| 1 | CHG_CC | 0 | 9510 | 0 | 4220 | 4470 | 60.0 | 23 |
| 2 | CHG_CC | 0 | 7846 | 0 | 4240 | 4470 | 60.0 | 23 |
| 3 | CHG_CCCV | 0 | 6657 | 0 | 0 | 4300 | 60.0 | 23 |
| 4 | CHG_CCCV | 0 | 4755 | 0 | 0 | 4470 | 60.0 | 23 |
| 5 | REST | 0 | 0 | 60 | 0 | 0 | 60.0 | 23 |
| 6 | DCHG_CC | 0 | 2378 | 0 | 3300 | 2600 | 60.0 | 23 |
| 7 | REST | 0 | 0 | 60 | 0 | 0 | 60.0 | 23 |

### 250827_251028_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter5.sch
- group_idx=0, TC=1-30, N=30, body=7, sub_tag=mode_flag_chamber
- desc: 4755mAh_ECT ����5 ACT ����
- chamber=23.0°C

| step# | type | mode | I (mA) | t (s) | V cut (mV) | V disp (mV) | rec_iv | chamber |
|---|---|---|---|---|---|---|---|---|
| 1 | CHG_CC | 0 | 9510 | 0 | 4220 | 4470 | 60.0 | 23 |
| 2 | CHG_CC | 0 | 7846 | 0 | 4240 | 4470 | 60.0 | 23 |
| 3 | CHG_CCCV | 0 | 6657 | 0 | 0 | 4300 | 60.0 | 23 |
| 4 | CHG_CCCV | 0 | 4755 | 0 | 0 | 4470 | 60.0 | 23 |
| 5 | REST | 0 | 0 | 60 | 0 | 0 | 60.0 | 23 |
| 6 | DCHG_CC | 0 | 2378 | 0 | 3300 | 2600 | 60.0 | 23 |
| 7 | REST | 0 | 0 | 60 | 0 | 0 | 60.0 | 23 |

### 250827_251028_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter6.sch
- group_idx=0, TC=1-30, N=30, body=7, sub_tag=mode_flag_chamber
- desc: 4755mAh_ECT ����6 ACT 23��
- chamber=23.0°C

| step# | type | mode | I (mA) | t (s) | V cut (mV) | V disp (mV) | rec_iv | chamber |
|---|---|---|---|---|---|---|---|---|
| 1 | CHG_CC | 0 | 9510 | 0 | 4220 | 4470 | 60.0 | 23 |
| 2 | CHG_CC | 0 | 7846 | 0 | 4240 | 4470 | 60.0 | 23 |
| 3 | CHG_CCCV | 0 | 6657 | 0 | 0 | 4300 | 60.0 | 23 |
| 4 | CHG_CCCV | 0 | 4755 | 0 | 0 | 4470 | 60.0 | 23 |
| 5 | REST | 0 | 0 | 60 | 0 | 0 | 60.0 | 23 |
| 6 | DCHG_CC | 0 | 2378 | 0 | 3300 | 2600 | 60.0 | 23 |
| 7 | REST | 0 | 0 | 60 | 0 | 0 | 60.0 | 23 |

### 250827_251028_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter7.sch
- group_idx=0, TC=1-30, N=30, body=7, sub_tag=mode_flag_chamber
- desc: 4755mAh_ECT ����7 ACT 23��
- chamber=23.0°C

| step# | type | mode | I (mA) | t (s) | V cut (mV) | V disp (mV) | rec_iv | chamber |
|---|---|---|---|---|---|---|---|---|
| 1 | CHG_CC | 0 | 9510 | 0 | 4220 | 4470 | 60.0 | 23 |
| 2 | CHG_CC | 0 | 7846 | 0 | 4240 | 4470 | 60.0 | 23 |
| 3 | CHG_CCCV | 0 | 6657 | 0 | 0 | 4300 | 60.0 | 23 |
| 4 | CHG_CCCV | 0 | 4755 | 0 | 0 | 4470 | 60.0 | 23 |
| 5 | REST | 0 | 0 | 60 | 0 | 0 | 60.0 | 23 |
| 6 | DCHG_CC | 0 | 2378 | 0 | 3300 | 2600 | 60.0 | 23 |
| 7 | REST | 0 | 0 | 60 | 0 | 0 | 60.0 | 23 |

### 250827_251028_06_이성일_4755mAh_PA2-SDI-447V-275V-ECT-parameter8.sch
- group_idx=1, TC=31-150, N=120, body=20, sub_tag=mode_flag_chamber
- desc: 4755mAh_ECT ����8 ACT GITT
- chamber=23.0°C

| step# | type | mode | I (mA) | t (s) | V cut (mV) | V disp (mV) | rec_iv | chamber |
|---|---|---|---|---|---|---|---|---|
| 10 | CHG_CCCV | 0 | 951 | 25200 | 0 | 4470 | 1.0 | 23 |
| 11 | REST | 0 | 0 | 1800 | 0 | 0 | 1.0 | 23 |
| 12 | DCHG_CC | 0 | 951 | 21600 | 2750 | 2500 | 1.0 | 23 |
| 13 | REST | 0 | 0 | 1800 | 0 | 0 | 1.0 | 23 |
| 14 | GITT_START | 0 | 0 | 0 | 0 | 0 | 0.0 | 0 |
| 15 | GITT_END | 0 | 0 | 0 | 0 | 0 | 0.0 | 0 |
| 16 | REST | 0 | 0 | 1800 | 0 | 0 | 1.0 | 23 |
| 17 | DCHG_CC | 0 | 48 | 432000 | 2000 | 1900 | 1.0 | 23 |
| 18 | REST | 0 | 0 | 3600 | 0 | 0 | 1.0 | 23 |
| 19 | GITT_START | 0 | 0 | 0 | 0 | 0 | 0.0 | 0 |
| 20 | GITT_END | 0 | 0 | 0 | 0 | 0 | 0.0 | 0 |
| 21 | CHG_CC | 0 | 476 | 360 | 4540 | 4580 | 1.0 | 23 |
| 22 | REST | 0 | 0 | 3600 | 0 | 0 | 1.0 | 23 |
| 23 | GITT_START | 1 | 0 | 0 | 0 | 0 | 0.0 | 0 |
| 24 | GITT_END | 0 | 0 | 0 | 0 | 0 | 0.0 | 0 |
| 25 | REST | 0 | 0 | 3600 | 0 | 0 | 1.0 | 23 |
| 26 | GITT_START | 0 | 0 | 0 | 0 | 0 | 0.0 | 0 |
| 27 | GITT_END | 0 | 0 | 0 | 0 | 0 | 0.0 | 0 |
| 28 | DCHG_CC | 0 | 476 | 360 | 2000 | 1900 | 1.0 | 23 |
| 29 | REST | 0 | 0 | 3600 | 0 | 0 | 1.0 | 23 |

## 3. ECT group 의 step type 구성 패턴

| 패턴 | count |
|---|---|
| CHG=3, DCHG=1, REST=3, body=7 | 48 |
| CHG=4, DCHG=1, REST=2, body=7 | 19 |
| CHG=1, DCHG=1, REST=2, body=4 | 9 |
| CHG=2, DCHG=3, REST=7, body=19 | 2 |
| CHG=2, DCHG=3, REST=7, body=20 | 1 |

### "REST only" group: **0 / 79** (0%)

## 4. ECT-classified group 들의 LOOP body 내 REST 시간 분포

실제 .sch 를 parse 해서 ECT 분류된 group 의 REST step 의 t_24 (= 휴지 시간) 분포 dump.

### REST step 시간 (n=2154)

| 통계 | 값 |
|---|---|
| 전체 mean | 3372s = 0.9h |
| 전체 median | 1800s |
| 전체 min/max | 1~21600s |

| REST 시간 bucket | count |
|---|---|
| <60s | 58 |
| 1~10m | 523 |
| 10~30m | 16 |
| 30m~1h | 666 |
| 1~2h | 701 |
| 2~6h | 171 |
| 6~24h | 19 |
| ≥24h | 0 |

- chamber≠0 인 REST step: 1796
- short sampling (rec_iv<5) 인 REST step: 1888

### CHG step 시간 (n=547)
- mean: 16778s, median: 25200s
- min/max: 360~25200s
### DCHG step 시간 (n=352)
- mean: 21051s, median: 21600s
- min/max: 1~432000s

## 5. 결론 hint

아래 질문에 대한 답을 위 데이터로 추론:
1. **ECT body 가 REST only 이면** — 사용자 지적 맞음, 단순 긴 휴지
2. **ECT body 가 CHG/DCHG/REST 혼재** — pulse + REST sequence (GITT-like)
3. **ECT body 의 REST 시간 분포** —
   - 일정 (예: 모두 600s) → 표준 protocol
   - 다양 (예: 60s~24h) → 시험 단계별 다른 목적
4. **CHG/DCHG step 이 짧은 (≤30s) 펄스** → DCIR 또는 GITT 변형
5. **CHG/DCHG step 이 긴 (≥1h)** → 일반 cycling 또는 ECT 자체의 measurement
