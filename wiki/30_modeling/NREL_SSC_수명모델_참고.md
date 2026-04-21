---
relocated: 2026-04-22
source_vault: "docs/vault/03_Battery_Knowledge/NREL_SSC_수명모델_참고.md"
title: "NREL SSC 수명 모델 참고 (NMC Semi-Empirical + Calendar/Cycle)"
aliases:
  - SSC Battery Lifetime
  - NMC Wang Model
  - Calendar Cycle Aging Separation
tags:
  - Battery_Knowledge
  - reference
  - lifetime
  - degradation
  - NMC
type: reference
status: active
related:
  - "[[충방전_매커니즘]]"
  - "[[Battery_Electrochemical_properties]]"
created: 2026-04-19
updated: 2026-04-19
source: "https://github.com/NatLabRockies/ssc/tree/develop/shared"
---

# NREL SSC 수명 모델 참고

> [!abstract] 요약
> NREL SAM의 시뮬레이션 엔진 **SSC** 에 포함된 두 수명 모델을 BDT 사이클 탭 확장 시 **참고용**으로 정리. 코드 이식은 하지 않고, 수식과 구조만 기록한다.
> - `lib_battery_lifetime_nmc.*` — NMC 반경험 수명 모델 (Arrhenius + Li-loss + negative electrode)
> - `lib_battery_lifetime_calendar_cycle.*` — calendar vs cycle aging 분리 모델 + rainflow 카운팅

---

## 🎯 BDT 활용 목적

| 항목 | 내용 |
|---|---|
| **이식 여부** | ❌ **코드 이식 안 함**. 수식/알고리즘 참고만 |
| **BDT 쓰임새 1** | 사이클 탭에 *측정 용량 fade* vs *모델 예측 라인* 오버레이 |
| **BDT 쓰임새 2** | rest 구간 많은 프로파일에서 **calendar fade**와 **cycle fade** 분리 표시 |
| **원본 언어** | C++ (NREL SSC) |
| **라이선스** | 원본 BSD-3-Clause. 수식은 공지된 논문 기반 |

---

## 1. `lib_battery_lifetime_nmc.cpp` — NMC 반경험 모델

### 1-1. 전체 구조

- `lifetime_nmc_t` 클래스가 **두 축을 동시 추적**:
  - **QLi** — Lithium inventory loss (SEI + li-plating)
  - **QNeg** — Negative electrode (음극) 열화
- **q_relative = min(QLi, QNeg)** 로 실효 용량 결정 (어느 한 쪽이 먼저 제한됨)

### 1-2. 물리 상수

```
Rug   = 8.314      J/(K·mol)   # 기체상수
T_ref = 298.15     K            # 25 °C 기준
F     = 96485      C/mol        # 패러데이 상수
```

### 1-3. 온도 의존성 (Arrhenius)

계수마다 활성화 에너지 `Ea_*` 를 갖고 모두 같은 형태로 온도 보정:

```
Arr_x = exp( -(Ea_x / Rug) · (1/T_battery - 1/T_ref) )
```

대상 계수: `b1, b2, b3, c0, c2` — 각각 다른 Ea 사용.

### 1-4. 시간(Calendar) 성분

**b1 — Li loss 시간 성분:**
```
b1_dt = b1_ref · Arr_b1 · dt_day
```

**d0 (두 번째 차수 Arrhenius 포함):**
```
d0_t = d0_ref · exp( -(Ea_d0_1/Rug)·(1/T - 1/T_ref)
                     -(Ea_d0_2/Rug)·(1/T - 1/T_ref)² )
```

**시간 누적 캘린더 감쇠(제곱근 형태):**
```
dQLi1 / dt = b1 / sqrt(day_age_of_battery)       # t^(-0.5) 감쇠
```

→ 의미: 전형적인 SEI 성장의 `q ∝ √t` 법칙.

### 1-5. 전압·DOD 의존 성분

**b3 (전극 전위 영향):**
```
Tfl_b3 = exp( (α_a · F / Rug) · (V_oc/T - V_ref/T_ref) )
b3_dt  = b3_ref · Arr_b3 · Tfl_b3 · (1 + θ · DOD_max) · dt_day
```

→ 양극 개회로전위 `V_oc`와 DOD_max가 직접 가속 인자로 들어감.

### 1-6. 음극(Qneg) 성분

```
c0_dt = c0_ref · exp( -(Ea_c0/Rug)·(1/T - 1/T_ref) ) · dt_day
c2_dt = c2_ref · Arr_c2 · dt_day
```

### 1-7. 사이클 손상 (DOD² × cycles²)

```
dQLi2 ∝ b2_ref · b2 · sqrt( Σ( b2 · DOD² · cycles² ) )
```

→ 축적된 cycle damage에서 **DOD 제곱 가중**. 깊은 사이클이 강하게 패널티.

### 1-8. 용량 최종 합산

```
q_relative_li = (d0_t / Ah_ref) · 100 · (b0 - ΔqLi1 - ΔqLi2 - ΔqLi3)
q_relative_neg = ... (c0, c2 기반 유사 형태)
q_relative = min(q_relative_li, q_relative_neg)
```

### 1-9. OCV / Uneg 보간 테이블

SOC 0~1을 **0.1 단위 10구간**으로 선형 보간:
```cpp
Uneg = unegs[i] + (unegs[i+1]-unegs[i])/0.1 · (SOC - i/10)
Voc  = ocvs[i]  + (ocvs[i+1]-ocvs[i]) /0.1 · (SOC - i/10)
```

→ BDT에서 이미 보유한 OCV 데이터로 대체 가능.

### 1-10. estimateCycleDamage (한 사이클당 예상 손상률 %)

```cpp
QLi_damage  = dq_relative_li2  / max(1, n_cycles)
QNeg_damage = dq_relative_neg  / max(1, n_cycles)
return max(QLi_damage, QNeg_damage) · 100
```

---

## 2. `lib_battery_lifetime_calendar_cycle.*` — Calendar/Cycle 분리

### 2-1. 전체 구조 — 두 개의 독립 클래스

| 클래스 | 역할 | 입력 |
|---|---|---|
| `lifetime_calendar_t` | **시간 축** 열화만 | `T, SOC, dt` |
| `lifetime_cycle_t` | **사이클 축** 열화만 | `DOD` (rainflow) |

→ BDT의 rest 구간이 긴 프로파일(Continue, GITT)에서 **시간 성분 vs 사이클 성분**을 분리해 표시할 때 바로 이 이분법이 유용.

### 2-2. Calendar Model (3가지 선택)

**NONE** — 캘린더 열화 없음
**MODEL** — 파라미터 수식:
```
k_cal = a · exp( b·(1/T - 1/296) ) · exp( c·(SOC/T - 1/296) )

초기   : dq_new = k_cal · sqrt(dt_day)
이후   : dq_new = (0.5·k_cal² / dq_old) · dt_day + dq_old
최종   : q_relative_calendar = (q0 - dq_new) · 100
```

기본 파라미터: `q0=1.02, a=2.66e-3, b=-7280, c=930`

**TABLE** — day vs capacity 룩업 + 1차 보간:
```cpp
q_calendar = interpolate(day_lo, cap_lo, day_hi, cap_hi, day_age)
```

→ BDT가 로그에서 rest 구간 온도/SOC 시계열을 뽑을 수 있으므로 **MODEL 방식이 실측 비교에 유리**.

### 2-3. Cycle Model — DOD × cycles 이중선형 룩업

```cpp
dq = bilinear(cycle_range, cycles_at_range)
   - bilinear(cycle_range, cycles_at_range + 1)
if (dq > 0) q_relative_cycle -= dq
```

→ `(DOD, 누적 사이클 수)` 2D 테이블에서 **다음 사이클에서 빠질 용량**을 차분으로 계산.

### 2-4. Rainflow Counting (핵심 로직)

일반적 ASTM E1049 rainflow의 **4-점 알고리즘** 구현:

```cpp
if (|X| + tolerance < |Y|)
    retCode = LT_GET_DATA          // 피크 더 수집
else {
    cycle_range = Y                // Y를 한 사이클로 종결
    n_cycles++
    peaks pop-back                 // 스택에서 제거
}
```

- `X` = 가장 최근 range, `Y` = 그 직전 range
- Y > X 이면 Y는 완성된 cycle로 카운트 → `n_cycles++`
- `cycle_range`, `cycle_counts` 를 상태로 누적

→ BDT에서 **CC 사이클 프로토콜은 DOD가 일정**하지만, DST/WLTP 같은 **불규칙 프로파일**이 들어오면 rainflow가 필수. 현재 BDT는 사이클 번호 기반이라 rainflow가 없음.

### 2-5. estimateCycleDamage (다음 사이클 예상)

```cpp
DOD = (average_range > 0) ? average_range : 50
return bilinear(DOD, n+1) - bilinear(DOD, n+2)
```

→ 현재까지 평균 DOD 기준으로 **바로 다음 사이클의 한계 감쇠량** 반환.

### 2-6. State 구조체

**cycle_state:**
```
q_relative_cycle(%), rainflow_Xlt, rainflow_Ylt, rainflow_jlt,
rainflow_peaks[], cycle_counts[], cum_dt(day),
DOD_max, DOD_min, cycle_DOD_max(%)
```

**calendar_state:**
```
q_relative_calendar(%), dq_relative_calendar_old (0~1)
```

---

## 3. BDT 통합 시 검토 포인트

### 3-1. 바로 쓸 만한 것

- ✅ **Calendar MODEL 수식** — 파라미터 4개(q0, a, b, c)만 있으면 Python 5줄.
- ✅ **√t 형태의 SEI 캘린더 감쇠** — rest 구간이 많은 Continue 프로파일에 딱 맞음.
- ✅ **Rainflow 알고리즘** — BDT가 불규칙 프로파일(DST/WLTP) 지원하려면 필수. C++ 로직 그대로 Python 포팅 단순.

### 3-2. 그대로 쓰기엔 어려운 것

- ⚠️ **NMC 모델의 `b1_ref, b2_ref, b3_ref, d0_ref, Ea_*`** — SSC 코드에 하드코딩된 값은 특정 NMC 셀에 맞춘 피팅값. BDT에서 검증하려면 **실측 데이터로 다시 피팅**해야 의미 있음.
- ⚠️ **Cycle 테이블** — 2D 룩업 테이블 자체가 셀 종류별로 달라야 함. 제너릭 테이블은 참고용일 뿐.

### 3-3. BDT 확장 아이디어

1. **Calendar vs Cycle 기여도 분리 플롯**
   - x축: 사이클 수 (또는 일자)
   - y축: 용량 (%)
   - 3개 라인: 측정값, 모델(calendar only), 모델(calendar + cycle)

2. **파라미터 피팅 UI**
   - 측정 용량 fade에 `q_rel(t,N,DOD,T) = q0 - √(k_cal·t) - f_cycle(N, DOD)` 를 nonlinear fit
   - 추출된 `k_cal, a, b, c` 를 vault에 기록

3. **DOD 가중 누적값 추적**
   - `Σ DOD² · cycles` 를 실시간 막대 그래프로 표시 → 가속시험 설계에 바로 활용

---

## 4. 출처

- **SAM**: https://github.com/NatLabRockies/SAM (UI, NREL SAM 포크)
- **SSC**: https://github.com/NatLabRockies/ssc (compute modules)
- 대상 파일:
  - `shared/lib_battery_lifetime_nmc.h/cpp`
  - `shared/lib_battery_lifetime_calendar_cycle.h/cpp`
  - `shared/lib_battery_lifetime.h/cpp` (공통 베이스)

> [!note] 원본 논문
> 소스 주석에는 명시적 인용이 없음. NMC 모델은 NREL의 Kandler Smith 그룹 및 Wang et al. 계열의 반경험 프레임워크와 일치. 캘린더 모델 기본 파라미터(q0=1.02, a=2.66e-3, b=-7280, c=930)는 Kandler Smith 2017 계열로 추정. 정확한 문헌 확정은 별도 리뷰 필요.

## 관련 노트
- [[충방전_매커니즘]] — 열화 기본 메커니즘
- [[Battery_Electrochemical_properties]] — 전기화학 물성
- [[MOC_Battery_Knowledge]] — 배터리 지식 MOC
