# v2 vs v3 분류 diff

- v2 groups: 8298
- v3 groups: 8298
- common keys: 8298

## 1. 카테고리 분포 diff

| Category | v2 | v3 | diff | 변동 |
|---|---|---|---|---|
| RPT | 2842 | 2833 | -9 | ↓ |
| ACCEL | 929 | 1071 | +142 | ↑↑ |
| CHG_DCHG | 970 | 970 | 0 |  |
| PULSE_DCIR | 856 | 856 | 0 |  |
| CHARGE_SET | 561 | 551 | -10 | ↓ |
| FORMATION | 382 | 382 | 0 |  |
| REST_LONG | 330 | 330 | 0 |  |
| HYSTERESIS_DCHG | 230 | 198 | -32 | ↓ |
| HYSTERESIS_CHG | 198 | 217 | +19 | ↑ |
| DCHG_SET | 192 | 192 | 0 |  |
| INIT | 191 | 191 | 0 |  |
| UNKNOWN | 142 | 0 | -142 | ↓↓ ✅ |
| TERMINATION | 122 | 122 | 0 |  |
| POWER_CHG | 108 | 108 | 0 |  |
| DISCHARGE_SET | 84 | 84 | 0 |  |
| GITT_PULSE | 71 | 71 | 0 |  |
| RSS_DCIR | 8 | 40 | +32 | ↑ |
| REST_SHORT | 32 | 32 | 0 |  |
| FLOATING | 30 | 30 | 0 |  |
| SOC_DCIR | 20 | 20 | 0 |  |

## 2. v2 → v3 transition matrix (변경된 group 만)

각 cell = v2 의 카테고리 X 가 v3 에서 카테고리 Y 로 변한 group 수.

| v2 카테고리 → v3 카테고리 | count |
|---|---|
| UNKNOWN → **ACCEL** | 142 |
| HYSTERESIS_DCHG → **RSS_DCIR** | 32 |
| CHARGE_SET → **HYSTERESIS_CHG** | 10 |
| RPT → **HYSTERESIS_CHG** | 9 |

## 3. v2 UNKNOWN 142 group → v3 어디로 분류되었는가

| v3 분류 | count |
|---|---|
| ACCEL(mid_life) | 142 |

## 4. ECT 신규 79 group 의 v2 카테고리

| v2 카테고리 | count |
|---|---|

### ECT 분류된 unique 파일 (전수 0 파일)


## 5. HYSTERESIS 카테고리 변동 (ref_step 일반화 효과)

### v2 → v3 HYSTERESIS_DCHG transition

| v2 카테고리 | v3 = HYSTERESIS_DCHG count |
|---|---|
| HYSTERESIS_DCHG | 198 |

### v2 → v3 HYSTERESIS_CHG transition

| v2 카테고리 | v3 = HYSTERESIS_CHG count |
|---|---|
| HYSTERESIS_CHG | 198 |
| CHARGE_SET | 10 |
| RPT | 9 |

## 6. v3 ACCEL 의 sub_tag 분포

| sub_tag | count |
|---|---|
| multi_step | 814 |
| mid_life | 142 |
| multi_step+ect | 67 |
| (none) | 48 |

## 7. v3 PULSE_DCIR 의 sub_tag 분포

| sub_tag | count |
|---|---|
| short_sampling | 770 |
| short_sampling+dchg_cccv_pulse | 86 |

## 8. v3 ECT 의 sub_tag 분포

| sub_tag | count |
|---|---|
