# ampworks 심화 분석 — F1 ~ F8 기능별

**날짜**: 2026-04-19
**선행 문서**:
- [기능별 정밀분석](260419_ampworks_정밀분석_기능별.md) — 입출력·공수·통합
- [차용 제안 개요](260419_ampworks_분석_BDT차용제안.md) — 우선순위

**본 문서의 추가 가치**: 각 기능의 **물리적 유도 + 알고리즘 수학 + BDT 실데이터 매칭 + 리스크 매트릭스** 까지 심층 분석.

---

## F1. GITT → D_s 추출 (pulse-phase √t 회귀)

### 1.1 물리적 직관
Li⁺ 이 구형 활물질 입자 내부를 Fickian 확산한다. 짧은 시간 영역(τ ≪ r²/D) 에서는 입자 표면이 **무한 반평면** 처럼 거동 — voltage response 가 √t 에 비례. 이 기울기에 D_s 정보가 들어있다.

### 1.2 수학적 유도
**Weppner-Huggins 공식** (GITT 원전, 1977):
```
D_s = (4/π) · (τ⁻¹) · (n_M V_M / S)² · (ΔE_s / ΔE_τ)²
```
- τ: pulse 시간, n_M V_M/S: 몰당 부피/계면 면적
- ΔE_s: pulse 후 E_eq 변화, ΔE_τ: pulse 중 voltage 변화

구형 입자 가정 후 `(n_M V_M / S) → r/3` 치환 → ampworks 구현 형태:
```
D_s = (4/9π) · (r · dE/dt / dU/d√t)²
```
- r: 입자 반경 [m]
- dE/dt: pulse 간 E_eq 변화율 (np.gradient 로 계산)
- dU/d√t: pulse 내 √t 회귀 기울기

### 1.3 ampworks 구현 특징
1. **Pulse 감지**: `(State != R) & (State.shift() == R)` → 누적합으로 pulse 번호
2. **State 분류**: Amps > 0 → C, Amps < 0 → D, 정확히 0 → R
3. **SOC 정규화**: `cumulative_trapezoid(|Amps|, Seconds/3600)` → [0, 1]
4. **회귀 윈도우 [tmin=1s, tmax=60s]** — 기본값, 반셀 GITT 는 조정 필요
5. **dE/dt 산출**: 각 pulse 시작점의 voltage 를 `np.cumsum(dt_pulse)` 에 대해 gradient

### 1.4 BDT 적용 시나리오

**데이터 소스** (신 9종 분류 연계):
| 실험 | 카테고리 | r 추정값 |
|------|----------|---------|
| 240821 GITT (Gen4pGr 422mAh 20C 450V) | GITT(full) × 210 | 음극 12 μm, 양극 5 μm |
| M2 SDI 반셀 음극 half-cell 14pi | GITT(full) × 120 | 12 μm |
| M2 SDI 반셀 양극 half-cell 14pi | GITT(full) × 120 | 5 μm |
| M1 ATL Cathode Half GITT 0.1C | GITT(full) × 223 | 5 μm |
| M1 ATL Anode Half GITT 0.05C/0.1C | GITT(full) × 253/223 | 12 μm |

→ **최소 5개 실험 × 평균 200 pulse = 1000+ D_s 샘플** 확보 가능.

### 1.5 리스크 매트릭스
| 리스크 | 발생 확률 | 영향 | 완화책 |
|--------|----------|------|--------|
| 샘플링 주기가 tmin=1s 보다 낮음 | 중 | 회귀 불안정 | PNE 는 100ms 단위 OK, Toyo 는 확인 필요 |
| 충방전 혼재 → ampworks 에러 | 높음 | 실행 실패 | 방향별 자동 분할 래퍼 |
| r 입력 오류 (입자 종류별 다름) | 중 | D_s 오계산 (∝ r²) | 재료 프로필 프리셋 DB |
| 반셀 전류 부호 관례 차이 | 중 | State 오분류 | 전류 기호 자동 감지 + 사용자 확인 |

### 1.6 우선순위 최종 판단
★★★★★ **최우선 포팅**. 근거:
- 이미 BDT 데이터에 1000+ pulse 확보
- 수식 단순 (50줄 이내)
- 배터리 소재 평가의 정량적 지표 (qualitative plot → quantitative number)

---

## F2. ICI → D_s 추출 (rest-phase 회귀)

### 2.1 물리적 직관
GITT 의 "pulse 직후 voltage relaxation" 은 Li⁺ 이 pulse 중 축적한 농도 gradient 가 확산으로 평형화되는 과정. 같은 Fickian 해가 적용되지만 시간 원점이 **rest 시작 시점**.

### 2.2 수식
```
V(t_rest) = E_eq + m · √t_rest        (rest 내 regression)
D_s       = (4/9π) · (r · dE/dt / m)²   (pulse 간 dE/dt 는 GITT 와 동일)
```

### 2.3 ampworks 구현 특징
- `rest['StepTime'] >= tmin AND <= tmax` 범위만 회귀
- 기본 tmin=1s, tmax=10s (짧은 rest 프로토콜)
- **동일한 D_s 공식** — 단 m 의 물리적 해석이 다름 (pulse 의 −m → rest 의 +m, 부호 반대)

### 2.4 GITT vs ICI 비교표
| 항목 | GITT | ICI |
|------|------|-----|
| 시험 시간 | 장 (rest 1h+) | 단 (rest 10s~1min) |
| 평형 완료 | ✅ 완전 | ❌ 부분 |
| E_eq 정확도 | 높음 | 중간 |
| 회귀 대상 | pulse 초기 | rest 초기 |
| BDT 카테고리 | GITT(full) | GITT(simplified), 일부 DCIR |

### 2.5 BDT 적용 시나리오
**데이터 소스**: `GITT(simplified)` 48건 + `SOC별 사이클` 32건 중 단일 SOC × pulse 반복형.

**주요 대상**:
- 현혜정 LWN 25P SOC별 DCIR 신규 (260306)
- 홍승기 Q8 ATL Main 2.0C Rss RT (260119) — "Rss" 라 불리지만 단 rest 있으면 ICI 적용 가능
- 김영환 / 문현규 2.0C Rss 계열

### 2.6 리스크 매트릭스
| 리스크 | 확률 | 영향 | 완화 |
|--------|-----|------|------|
| rest 10s 이내 sampling 점 부족 | 높음 | 회귀 불가능 | tmin=0.5s 완화 허용 옵션 |
| pulse 중 ΔSOC 너무 크면 non-linear | 중 | dE/dt 왜곡 | pulse 당 ΔSOC ≤ 5% 체크 |

### 2.7 우선순위
★★★★ — F1 구현 후 0.5일 추가로 완성. `GITT(simplified)` 카테고리 자동 식별 이미 가능.

---

## F3. dQ/dV Spline Smoothing

### 3.1 왜 필요한가
dQ/dV 는 voltage 의 미분값이라 **노이즈에 매우 민감**. 원본 voltage 데이터 1% 잡음 → dQ/dV 에 수십% 잡음 확산. 피크 분석 (dQ/dV peak matching, stoichiometry fitting) 이전에 반드시 smoothing 필요.

### 3.2 ampworks 방법
- `scipy.interpolate.make_splrep(x, y, s=s)` — B-spline 회귀
- 제약: `Σ (g(x) - y)² ≤ s`
- `s=0` → 완전 보간 (잡음 보존), `s>0` → 평활
- 권장 시작: `s=1e-4`, 경험적 조정

### 3.3 왜 B-spline 이 좋은가
- **Analytic 미분 가능** — `dQ/dV`, `dV/dQ` 를 수치 미분 없이 정확히 계산
- **로컬 support** — smoothing 이 국소화 (Gaussian filter 는 전역)
- **Knot 자동 배치** — scipy 가 최적 knot 배열

### 3.4 BDT 현재 방식과 비교
**확인 필요** — proto_.py 에서 dv-dq 탭의 smoothing 방법. 추정:
- Moving average 또는 Savitzky-Golay 가능성
- Gaussian filter (scipy.ndimage.gaussian_filter1d) 가능성

**차이점**:
- BDT 방식: 균일 창 smoothing, 미분은 `np.gradient` (수치차분) → 2차 도함수 오류 누적
- ampworks 방식: spline 의 analytic 미분 → dQ/dV 품질 우수

### 3.5 적용 대상
- `!dvdqraw/*_anode/cathode_*.txt` — 반셀 데이터 (노이즈 자주 포함)
- 풀셀 저율 방전 (0.2C RPT) → 스무딩 후 dQ/dV 피크 추출

### 3.6 리스크
| 리스크 | 완화 |
|--------|------|
| `s` 값이 실험별 다름 | GUI 에 slider 추가, 실시간 플롯 업데이트 |
| 모노토닉 아닌 Volts 데이터 에러 | 정렬·중복 제거 전처리 레이어 |

### 3.7 우선순위
★★★★ — F4 의 전제조건. 스탠드얼론 유용성도 있음 (dv-dq 탭 품질 향상).

---

## F4. DqdvFitter — Stoichiometry 피팅

### 4.1 물리적 직관
풀셀 voltage 는 양·음극 half-cell voltage 의 **차이**:
```
V_cell(SOC) = U_p(x_p(SOC)) − U_n(x_n(SOC)) − i·R
```
여기서 x_n, x_p 는 각 전극의 stoichiometry (Li 점유율).

선형 가정:
```
x_n(SOC) = xn0 + SOC · (xn1 − xn0)
x_p(SOC) = xp0 + SOC · (xp1 − xp0)
```

**4개 파라미터** `{xn0, xn1, xp0, xp1}` 을 피팅하면 풀셀과 반셀이 어떻게 정렬되는지 결정됨. 이 정렬이 무너진 정도 → 열화 모드 (LAM/LLI, F5).

### 4.2 Grid Search + Trust-region 2단계
**왜 단순 minimize 로 안 되나**: 손실 함수가 non-convex (peak matching 구간에 국소 최소 다수). 초기값이 나쁘면 잘못된 minimum 수렴.

**ampworks 전략**:
1. **Grid search** (Nx⁴ 격자): coarse 탐색 — 대략의 minimum 위치 파악
2. **Constrained fit** (`trust-constr`): fine 최적화 — 그리드 결과 근처에서 ±0.1 bounds, x0<x1 linear constraint

### 4.3 3-항 손실 함수
```
L = α_V · MAPE(V_model, V_meas) + α_dqdv · MAPE(dQ/dV) + α_dvdq · MAPE(dV/dQ)
```
(α_i ∈ {0, 1} 사용자 선택, `cost_terms='all'` 이면 모두)

**왜 3항인가**:
- V 만: peak 정보 희석됨 (전체 커브 통합)
- dQ/dV 만: baseline 정보 손실
- dV/dQ: peak 위치에 가장 민감
→ 3항 조합이 로버스트

### 4.4 Hessian 기반 불확실성
trust-constr 수렴 후 Hessian 근사 이용:
```
Σ = H⁻¹ (공분산 행렬 근사)
σ_xi = √(Σ_ii)
```
→ DqdvFitResult 에 `x_std` 첨부

### 4.5 BDT 적용 시나리오
**전제 데이터**:
- 음극 반셀 dQ/dV: `!dvdqraw/S25_291_anode_dchg_02C_gen4.txt` (이미 BDT 사용)
- 양극 반셀 dQ/dV: `!dvdqraw/S25_291_cathode_dchg_02C.txt`
- 풀셀 BOL + EOL: RPT 카테고리 0.2C 충방전 — 분류기로 자동 선별 가능

**수명시험 흐름**:
```
주기 RPT × N회 → 각각 stoichiometry 피팅 → DqdvFitTable
                                          ↓
                                   F5 LAM/LLI → 주기별 열화 분석
```

### 4.6 리스크
| 리스크 | 영향 | 완화 |
|--------|------|------|
| Grid search Nx⁴ 계산 | 4D × 20 = 160k 평가 가능 | Nx ≤ 20 권장, 캐싱 |
| 반셀 데이터 missing (양극만/음극만) | 피팅 불가 | 블랭킷 전용 모드 (전제 완화) 미구현 |
| 초기 stoichiometry 가 범위 밖 | 발산 | grid_search 가 bounds 자동 클램프 |

### 4.7 우선순위
★★★★★ — F5 의 전제. BDT 에 이미 있는 dv-dq 기능을 **정량 분석** 수준으로 상승시킴.

---

## F5. LAM / LLI 열화 모드 계산

### 5.1 물리적 직관
**LAM (Loss of Active Material)**: 양극 또는 음극 활물질이 전기적으로 분리/탈락/부식 → 실효 용량 감소.
**LLI (Loss of Lithium Inventory)**: SEI 성장·side reaction 으로 cyclable Li⁺ 이 불가역적으로 고정 → 가용 Li 감소.

두 원인은 수명 저하의 **분해 불가능한 두 축**. LAM 은 전극 교체 필요, LLI 는 ΔSOC 재조정으로 부분 회복 가능.

### 5.2 수식 완전 유도

**전극 가용 용량** — stoichiometry 범위와 풀셀 용량 관계:
```
Q_n · (xn1 − xn0) = Ah    (음극이 SOC 0→1 사이 사용한 Li 양)
∴ Q_n = Ah / (xn1 − xn0)

Q_p · (xp1 − xp0) = Ah
∴ Q_p = Ah / (xp1 − xp0)
```

**LAM** — BOL 대비 비율:
```
LAM_n = 1 − Q_n / Q_n[0]
LAM_p = 1 − Q_p / Q_p[0]
```

**Li 인벤토리** — 음극 내 Li 량 + 양극의 "빈 공간(Li 보관 가능)":
```
Inv = xn0 · Q_n + (1 − xp0) · Q_p
```
(BOL 에서는 양극 완전 충전 상태 `xp=xp0` 이 표준)

**LLI**:
```
LLI = 1 − Inv / Inv[0]
```

### 5.3 First-order Taylor 불확실성 전파
```
σ(Q_n) = √[(∂Q_n/∂xn1 · σ_xn1)² + (∂Q_n/∂xn0 · σ_xn0)²]

∂Q_n/∂xn1 = −Q_n / (xn1 − xn0)      (기울기의 −)
∂Q_n/∂xn0 = +Q_n / (xn1 − xn0)

σ(LAM_n) = σ(Q_n) / Q_n[0]
σ(LLI)   = (4개 x_i 편미분 × σ_i)² 합의 제곱근
```

### 5.4 LAM/LLI vs Capacity Retention
BDT 현재: **capacity retention** (Q_t / Q_0) 만 계산 — 열화 원인 불명.

LAM/LLI 도입 효과:
```
수명 저하 원인 분해:
  Capacity Fade = f(LAM_n, LAM_p, LLI, …)
  
예) 초기 5% fade 가
   - LAM_n=2%, LAM_p=1%, LLI=3% 면 → SEI 성장이 주원인
   - LAM_n=4%, LAM_p=0%, LLI=1% 면 → 음극 기계적 열화
```
→ **설계 의사결정 근거** (음극 binder 변경 vs 전해액 첨가제 vs 양극 코팅).

### 5.5 BDT 데이터 적합성
**주요 대상**: 장기 수명시험 (수명 폴더 23건)
- 251028 나무늬 Q8 ATL SEU4 RT @1-1202 (RPT × 9회 이상)
- 홍승기 Q8 ATL Main 2.0C (RPT 주기적)

**전제**: 각 RPT 에서 F4 로 fit 이 성공해야. 실패 시 NaN 전파.

### 5.6 리스크
| 리스크 | 완화 |
|--------|------|
| RPT 주기마다 반셀 데이터 없음 (1회만 있음) | 반셀 데이터는 BOL 시점 1회면 충분 (고정) |
| BOL 기준 정의 모호 | 첫 RPT = BOL 고정 / 사용자 선택 가능 |
| 4차원 fit 실패 확산 | failed-fit 건너뛰고 next 주기 진행 |

### 5.7 우선순위
★★★★★ — F4 완성 즉시 적용 가능. **배터리 수명 분석의 엔드게임**. 50줄 추가 코드.

---

## F6. HPPC Multi-timepoint Impedance

### 6.1 물리적 직관
**HPPC (Hybrid Pulse Power Characterization)**: 각 SOC 에서 다전류 레벨 pulse (예: 10s 방전 → 10s 충전, 전류 레벨 C/5, C/2, 1C, 2C) 로 전력 특성을 맵핑. 미국 DOE INL 프로토콜 표준.

**다전류 시점별 R**:
```
R(t) = |V(t) − V_baseline| / |I_avg|
```
시간 t 가 짧으면 (≤1s) → 주로 R_ohm, t 가 길면 (≥10s) → R_ohm + R_ct 포함.

### 6.2 ampworks 구현 특징
- **Pulse 자동 감지**: state 전이 + `[tmin, tmax]` 지속시간 필터
- **Baseline**: `Volts[0]` (pulse 직전 샘플)
- **Multi-time 샘플링**: `[t_instant, t_1, t_2, ..., t_eop]` 에서 np.interp 보간
- **ASI** (Area-Specific Impedance): `R × A_electrode` [Ω·cm²] — 전극 면적 알려져야

### 6.3 출력 구조
DataFrame 한 행 당 한 pulse:
```
PulseNum, State, Hours_0, SOC_0, AmpsAvg,
StepTime_0, Volts_0, Ohms_0, ASI_0,     # t=0 (baseline)
StepTime_1, Volts_1, Ohms_1, ASI_1,     # t=instant
StepTime_2, ..., Ohms_2, ASI_2,         # t=t_1
...
StepTime_N, Volts_N, Ohms_N, ASI_N,     # t=EOP
```

### 6.4 BDT 적용 시나리오 — **현재 데이터 부재**
Phase 0 분석 결과 **BDT 데이터셋에 HPPC 패턴 없음** (한 SOC 다전류 pulse 세트 부재). 신규 시험 계획 시 HPPC 추가 가능성.

### 6.5 DCIR 기능 일반화 가능성
BDT 의 기존 DCIR 은 "고정 시점(10s) 단일 R" 만 제공. HPPC 코드를 일반화하면:
- 사용자 지정 시점 배열 `[0.1s, 1s, 10s, 30s]` 에서 모두 R 계산
- Randles equivalent circuit fit 까지 확장 가능 (R_ohm, R_ct, 확산 tail 분리)

### 6.6 우선순위
★★ — 현 데이터 없음. 미래 HPPC 시험 도입 시 또는 DCIR multi-timepoint 확장 시 활용.

---

## F7. OCV Peak Matching (iR 동시 추정)

### 7.1 물리적 직관
저율 충전·방전 voltage 곡선은 동일 OCV 를 기준으로 **대칭적으로 양쪽에 ±iR shift** 되어 있다. 두 곡선을 iR 만큼 반대 방향 shift 해서 겹치면 OCV 근사 추출 가능. 덤으로 iR 값 (전체 평균 저항) 도 얻음.

### 7.2 ampworks 알고리즘
```
최소화: ‖dQ/dV_chg(V − iR) − dQ/dV_dis(V + iR)‖₂²
        (L-BFGS-B 구속 최적화)

초기 iR: |V_peak_chg − V_peak_dis| / 2  (휴리스틱)
OCV 추정: midpoint(shifted_chg, shifted_dis)
```

### 7.3 왜 대칭 shift 인가
전기화학 반대칭 가정: 충전은 +iR, 방전은 −iR 동일 크기. 비대칭 저항 (예: film 저항 방향 의존) 은 이 모델 위배 → 2-parameter 확장 가능.

### 7.4 BDT 적용 시나리오
- 반셀 없이 **풀셀 RPT (0.2C 충방전)** 만으로 OCV 추출 가능
- F3 spline 전제 (smoothed dQ/dV 필수)
- BDT 의 OCV/CCV scatter 플롯 (현재 프로파일 탭) 과 보완 관계

### 7.5 DqdvFitter (F4) 와의 차이
| 항목 | F4 Fitter | F7 Peak Matching |
|------|----------|------------------|
| 입력 | 풀셀 + 반셀 양쪽 | 풀셀 충·방전만 |
| 출력 | 4개 stoichiometry | iR + OCV curve |
| 전제 | 반셀 데이터 있음 | 저율 충·방전 있음 |
| 용도 | LAM/LLI 계산 | OCV 추출, iR 추정 |

→ 반셀 데이터 없는 셀도 F7 로 OCV 추출 가능 — **F4 의 데이터 요구 대안**.

### 7.6 우선순위
★★★ — F3 전제. 반셀 데이터 부재 상황에 유용. F4 와 상호보완.

---

## F8. 불확실성 전파 (±σ 리포팅)

### 8.1 두 가지 접근

**접근 A: scipy.curve_fit 의 pcov 활용** (가장 단순):
```python
popt, pcov = curve_fit(model, x, y, p0=p0)
perr = np.sqrt(np.diag(pcov))   # 파라미터별 ±σ
```
→ BDT 에 이미 scipy.curve_fit 사용처가 있으면 `pcov` 추가만으로 끝.

**접근 B: Hessian 근사** (trust-constr, Newton-like):
```python
result = minimize(loss, x0, method='trust-constr')
H = result.hess
cov = np.linalg.inv(H)
perr = np.sqrt(np.diag(cov))
```
→ ampworks DqdvFitter 방식.

### 8.2 Taylor 전파 — 파생 변수 σ
파라미터 `x = (x_1, …, x_n)` 에 σ_i 있을 때, 함수 `f(x)` 의 σ:
```
σ(f)² ≈ Σ_i (∂f/∂x_i · σ_i)²      (1차 근사, 파라미터 독립 가정)
```
공분산까지 고려하면:
```
σ(f)² = (∇f)ᵀ · Σ · (∇f)
```

### 8.3 BDT 적용 대상 (검색)
BDT 현재 fit 사용처 (개략):
- DCIR 선형 regression
- dV/dQ peak fitting
- capacity retention 피팅
- name_capacity 파라미터 추출
→ **전부 ±σ 리포트 가능**. 엑셀 출력 컬럼에 `param_std` 추가만 하면 됨.

### 8.4 UI 표시 형식
```
DCIR = 15.3 ± 0.4 mΩ         (1σ)
capacity retention = 92.1 ± 0.7 %
```
정책: ±1σ 기본 (68% 신뢰구간). 사용자 설정으로 ±2σ 지원 가능.

### 8.5 리스크
| 리스크 | 완화 |
|--------|------|
| fit 실패 시 pcov = inf | NaN 출력 + 경고 로그 |
| 상관관계 높은 파라미터 → σ 과대평가 | 공분산 전체 출력 옵션 |

### 8.6 우선순위
★★★★ — 가장 짧은 구현 (30~50줄). 전체 분석 결과 신뢰도 향상 효과 큼. 기반 인프라로 먼저 도입 권장.

---

## 요약 — 재평가된 차용 우선순위

심화 분석 후 우선순위 조정:

| 순위 | ID | 기능 | ★ | 공수 | 근거 (심화 분석 반영) |
|:---:|:---:|------|:---:|:---:|--------|
| 1 | **F1** | GITT D_s | ★★★★★ | 1.5d | 데이터 1000+ pulse 확보, 단순 수식, 즉시 정량 가치 |
| 2 | **F8** | ±σ 전파 | ★★★★ | 0.5d | 30줄 수준, 전체 분석 신뢰도 상승, 기반 |
| 3 | **F3** | Spline | ★★★★ | 0.5d | F4/F5/F7 전제, dv-dq 품질 즉각 개선 |
| 4 | **F4** | DqdvFitter | ★★★★★ | 3d | F5 전제, BDT dv-dq 탭 정량화 |
| 5 | **F5** | LAM/LLI | ★★★★★ | 1d | 배터리 수명 해석의 종착점 |
| 6 | **F2** | ICI D_s | ★★★★ | 0.5d | F1 재활용, GITT(simplified) 48건 |
| 7 | **F7** | OCV peak | ★★★ | 1d | 반셀 없어도 OCV — F4 대안 |
| 8 | **F6** | HPPC | ★★ | 2d | 데이터 부재, 향후 DCIR 확장 여지 |

**권장 실행 순서**: F8 → F3 → F1 → F4 → F5 → F2 → F7 → (F6)

**총 공수**: 10일 (F1~F5 핵심만 5.5일)

---

## 의존성 그래프

```
              ┌─ F2 ICI (0.5d)         [F1 재활용]
F8 (0.5d) ──┼─ F1 GITT (1.5d)         [독립 고가치]
            │
            │  ┌─ F7 OCV peak (1d)     [반셀 없을 때 대안]
            └─ F3 (0.5d) ──┤
                          └─ F4 (3d) ─► F5 (1d)   [대핵심]

F6 HPPC (2d) [독립, 후순위]
```

---

## 실행 대기 상태

현재:
- ✅ 소스 수집·분석 완료
- ✅ 라이센스·스캐폴딩 준비 완료 ([tools/ampworks_port/](../../../tools/ampworks_port/README.md))
- ✅ 이식 판정 체크리스트 정의
- ⬜ 실제 포팅 시작 — **사용자 지시 대기**

사용자 선택 후:
1. 해당 기능 폴더 `f{N}_{name}/` 생성
2. 독립 구현 + validate.py
3. 실데이터 검증 → 결과 아티팩트 축적
4. 체크리스트 A~E 통과 시 proto_.py 이식 Phase 착수
