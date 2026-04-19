# ampworks 기능별 정밀 분석 — BDT 차용 블루프린트

**날짜**: 2026-04-19
**선행**: [260419_ampworks_분석_BDT차용제안.md](260419_ampworks_분석_BDT차용제안.md) (우선순위 제안)
**목적**: 각 기능의 **소스 수준** 정밀 분석 — 입력·알고리즘·출력·엣지케이스·BDT 연결점·공수·리스크

---

## 차용 후보 기능 전체 목록

| ID | 기능 | ampworks 경로 | 우선순위 |
|---|------|----------------|:---:|
| **F1** | GITT → D_s 추출 | `gitt/_extract_params.py` | ★★★★★ |
| **F2** | ICI → D_s 추출 (rest-phase 변형) | `ici/_extract_params.py` | ★★★★ |
| **F3** | dQ/dV 스플라인 스무딩 | `dqdv/_dqdv_spline.py` | ★★★★ |
| **F4** | dQ/dV stoichiometry 피팅 | `dqdv/_dqdv_fitter.py` | ★★★★★ |
| **F5** | LAM / LLI 열화모드 계산 | `dqdv/_lam_lli.py` | ★★★★★ |
| **F6** | HPPC multi-timepoint impedance | `hppc/_extract_impedance.py` | ★★ |
| **F7** | OCV peak matching (iR 동시 추정) | `ocv/_match_peaks.py` | ★★★ |
| **F8** | 파라미터 ±σ 불확실성 전파 | (여러 곳) | ★★★★ |

---

## F1. GITT → D_s 추출 (pulse 기반)

### 1.1 알고리즘 핵심
**√t vs V 선형회귀 — pulse 초반부**:
1. 입력 `{Seconds, Amps, Volts}` 데이터에서 state 분류 (R/C/D)
2. SOC 계산: `cumulative_trapezoid(|Amps|, Seconds/3600)` 정규화
3. Pulse 감지: `State != R` 이면서 직전이 R 인 지점 → `Pulse` 번호 할당
4. 각 pulse 의 `[tmin, tmax]` (default 1~60s) 구간에서 `√StepTime` vs `Volts` 선형회귀
   - 기울기 = `dU/d√t` (= `m`)
   - 절편 = `E_eq` (= `b`)
5. Pulse 간 평형전위 변화율 `dE/dt` 계산 (`np.gradient(Volts, cumsum(dt_pulse))`)
6. **D_s 공식**:
   ```
   D_s = (4/9π) × (radius × dE/dt / dU/d√t)²
   ```

### 1.2 입출력
**입력**:
- `data` (DataFrame): `{Seconds, Amps, Volts}` 필수
- `radius` (float): 입자 반경 [m]
- `tmin=1, tmax=60` [s]: 회귀 윈도우
- `return_all=False`: True 면 `(params, stats)` 튜플 반환

**출력** (`params` DataFrame):
- `SOC`, `Ds`, `Eeq` (SOC 오름차순 정렬)
- `stats` (return_all): Pulse 단위 상세 — `Eeq_err, dUdrt, dUdrt_err, dt_rest, dt_pulse, dEdt` 등

### 1.3 엣지케이스
- 충전과 방전 혼재 → **에러 발생** (한 방향 데이터만 허용)
- 마지막 사이클이 R 로 끝나지 않으면 제거
- Pulse 내 `[tmin, tmax]` 샘플 수 ≤ 1 → NaN
- `Amps == 0` 이 완벽히 지켜져야 함 (float 허용오차 고려 필요)

### 1.4 BDT 연결점
**데이터 소스 (이미 분류 완료 — Phase 1)**:
- `GITT(full)` 카테고리 — 성능 폴더 60 loop group (예: 240821 GITT, 박민희 M1 ATL GITT 0.1C, M2 SDI 반셀 등)

**코드 위치 제안**:
- 신규 모듈 `DataTool_dev_code/analysis/gitt_params.py`
- 진입점: `extract_gitt_params(raw_df: pd.DataFrame, radius_m: float) -> pd.DataFrame`
- UI: `tab_6` (프로파일) 의 GITT 분석 버튼 옆에 "D_s 추출" 메뉴 추가

**BDT 단위 매핑**:
| ampworks | BDT 원본 (PNE SaveEndData) | 변환 |
|----------|---------------------------|------|
| Seconds [s] | `StepTime/100` [0.01s] or `TotTime/100` | ÷100 |
| Amps [A] | `Current` [uA] (col 9) | ÷1e6 |
| Volts [V] | `Voltage` [uV] (col 8) | ÷1e6 |

**UI 변경 최소화**:
- 입자 반경 입력 필드 하나 추가 (기본값: 양극 5 μm, 음극 12 μm — 배터리 기본값 설정)
- 결과 출력: SOC vs D_s 플롯 + 엑셀 시트 추가 (`gitt_params` 시트)

### 1.5 공수 / 리스크
- **공수**: 1.5일 (포팅 0.5일 + UI 연결 0.5일 + 검증 0.5일)
- **리스크**:
  - 반셀 GITT 의 전류 부호 관례 차이 (ampworks: charging>0, BDT 는 내부 부호 다를 수 있음)
  - 샘플링 주기가 낮으면 `[1, 60s]` 윈도우가 2~3점밖에 안될 수 있음 → 회귀 불안정
- **완화**: 전류 방향 자동 감지 로직 (이미 ampworks 있음), 최소 샘플수 하한 파라미터화

---

## F2. ICI → D_s 추출 (rest-phase 변형)

### 2.1 알고리즘 핵심
GITT 와 반대: **rest 구간의 voltage relaxation** 에 √t 회귀 적용.

```
V_rest = m·√t + b      (pulse 종료 후 rest 구간 [tmin, tmax])
기울기 m   → dU/d√t
절편 b     → E_eq (relaxation 이 완료된 평형전위)
pulse 간 E_eq 변화율 → dE/dt
D_s = (4/9π)(radius × dE/dt / m)²
```

### 2.2 GITT vs ICI 차이
| 항목 | GITT (F1) | ICI (F2) |
|------|-----------|---------|
| 프로토콜 | 저율 pulse (10~30분) + 긴 rest (1h+) | 5분 pulse + 10초 rest |
| 회귀 대상 | **pulse 초기** voltage response | **rest 초기** voltage relaxation |
| 기본 tmin/tmax | 1~60 s (pulse 내) | 1~10 s (rest 내) |
| 추출 E_eq | pulse 개시 직전 voltage | rest 끝 voltage (relaxation 완료) |
| 장점 | 완전 평형 → 정확 E_eq | 짧은 rest 로 빠른 시험 |
| 단점 | 시험 시간 매우 김 | 완전 평형 못 이룸 |

### 2.3 BDT 연결점
**데이터 소스**: `GITT(simplified)` 48건 (Phase 1 이후 분류) — 김영환 수명시험 내 GITT 세트 등.

**코드 제안**:
- 동일 `analysis/gitt_params.py` 내 `extract_ici_params()` 병행 구현 (회귀 대상만 다름)
- UI: "RSS 측정" 카테고리에 D_s 추출 옵션 추가

**공수**: 0.5일 (F1 구현 재활용)

---

## F3. dQ/dV 스플라인 스무딩

### 3.1 알고리즘
- `scipy.make_splrep(x, y, s=s)` — B-spline 회귀
- `s=0` → 엄밀 보간, `s>0` → 평활 (MSE 상한)
- 권장 시작값: `s=1e-4`, 경험적 조정

### 3.2 BDT 현재 방식과 비교
- BDT 현재: `scipy.ndimage.gaussian_filter1d` 또는 moving average (확인 필요)
- ampworks 방식 우위: **smoothing 계수를 노이즈 수준에 적응** 가능, 도함수 품질 우수

### 3.3 입출력
**입력** DataFrame — `capacity_method='auto'` 일 때:
- `{Ah, Volts}` 또는 `{Seconds, Amps, Volts}` 택 1 (Ah 우선)
- Ah 는 monotonic-increasing, 최소값 0

**출력** (DqdvSpline 인스턴스):
- `.Volts(SOC)`, `.SOC(Volts)` 메서드
- `.dVdQ(...)`, `.dQdV(...)` 메서드 — analytic 미분

### 3.4 BDT 연결
- dvdqraw 폴더 데이터 (현재 노이즈 이슈 가능성) → 이 방식으로 smoothing 품질 개선
- **공수**: 0.5일 (함수 포팅)

---

## F4. dQ/dV stoichiometry 피팅 (DqdvFitter)

### 4.1 알고리즘

**4개 파라미터**:
- `xn0, xn1`: 음극 lithiation at 풀셀 SOC=0, 1
- `xp0, xp1`: 양극 delithiation at 풀셀 SOC=0, 1

**제약조건**: `xn0 < xn1`, `xp0 < xp1`

**모델**:
```
V_full(SOC) = U_p(xp0 + SOC·(xp1-xp0)) - U_n(xn0 + SOC·(xn1-xn0)) + iR·I
```

**손실 함수** (MAPE 기반, 3항 가중합 × 1e-2):
1. `voltage`: V_model vs V_measured
2. `dqdv`: dQ/dV_model vs dQ/dV_measured
3. `dvdq`: dV/dQ_model vs dV/dQ_measured

`cost_terms='all'` 시 3개 모두, `'dqdv'` 만 등 선택 가능.

**두 단계 파이프라인**:
1. **grid_search(Nx)**: 4D 그리드 탐색 → 최소 error 조합 반환
2. **constrained_fit(x0, bounds)**:
   - trust-constr 알고리즘 (`scipy.optimize.minimize`)
   - Linear constraints 로 x0<x1 보장
   - Bounds: 기본 `±0.1` (symmetric around x0), 내부에서 `[0.001, 1]` 로 clip
   - Hessian 으로 `x_std` 근사

### 4.2 BDT 연결
**전제 데이터**:
- 음극 반셀 dQ/dV → `!dvdqraw/*_anode_*.txt` (이미 있음)
- 양극 반셀 dQ/dV → `!dvdqraw/*_cathode_*.txt`
- 풀셀 저율 충/방전 → BDT 의 RPT 데이터 (0.2C) — 이미 분류 체계로 식별 가능

**BDT 의 기존 dv-dq 탭**: 이미 반셀+풀셀 로딩은 있지만 **stoichiometry 피팅은 없음** (dV/dQ 비교만). 이 코드를 포팅하면 큰 가치.

**코드 제안**:
- `DataTool_dev_code/analysis/dqdv_fit.py`:
  - `DqdvSpline` 클래스 (F3)
  - `DqdvFitter` 클래스 (F4)
- UI: dv-dq 탭 에 "Stoichiometry 피팅" 버튼 추가 → 결과 테이블 팝업

### 4.3 공수 / 리스크
- **공수**: 3일 (Spline 0.5 + Fitter 1.5 + UI 연결 0.5 + 검증 0.5)
- **리스크**:
  - 반셀 dQ/dV 품질에 민감 (노이즈 많으면 fit 불안정) → F3 Spline smoothing 필수
  - 초기값(x0) 잘못 주면 grid_search 가 비용 큼 (4D × Nx^4 계산)

---

## F5. LAM / LLI 열화모드 계산

### 5.1 공식 완전 정리

**전극 용량**:
```
Q_n = Ah / (xn1 - xn0)     # 음극 가용용량
Q_p = Ah / (xp1 - xp0)     # 양극 가용용량
Q_c = Ah                    # 풀셀 용량 (그대로)
```

**LAM (Loss of Active Material)** — 초기 대비 용량 감소율:
```
LAM_n = 1 - Q_n / Q_n[0]   # Q_n[0] = BOL 음극 용량
LAM_p = 1 - Q_p / Q_p[0]
```

**LLI (Loss of Lithium Inventory)** — Li 재고 감소율:
```
Inv = xn0·Q_n + (1 - xp0)·Q_p     # 현재 Li 재고
LLI = 1 - Inv / Inv[0]
```

### 5.2 불확실성 전파 (First-order Taylor)

각 파라미터 ±σ → 편미분 × σ 합 (quadrature):
```
σ(Q_n) = √[(∂Q_n/∂xn1·σ_xn1)² + (∂Q_n/∂xn0·σ_xn0)²]

∂Q_n/∂xn1 = -Ah/(xn1-xn0)² = -Q_n/(xn1-xn0)
∂Q_n/∂xn0 = +Q_n/(xn1-xn0)

σ(LAM_n) = σ(Q_n) / Q_n[0]
σ(LLI)   = √[4개 x_i 기여도 합]
```

### 5.3 입출력
**입력** (DqdvFitTable):
- `Ah, xn0, xn0_std, xn1, xn1_std, xp0, xp0_std, xp1, xp1_std, iR, iR_std, fun, success, message` + 사용자 extra_cols

**출력** (DegModeTable):
- `Qn, Qn_std, Qp, Qp_std, Qc, LAMn, LAMn_std, LAMp, LAMp_std, LLI, LLI_std`

**Plot** (`plot_lam_lli`): 2×3 서브플롯 — 상단 Q_n/Q_p/Q_c, 하단 LAM_n/LAM_p/LLI, ±1σ 음영 대역.

### 5.4 BDT 연결점
**데이터 흐름**:
```
수명시험 중 주기적 RPT (N회)
  ↓
F3 DqdvSpline 으로 각 RPT 의 dQ/dV 스무딩
  ↓
F4 DqdvFitter 로 각 RPT 의 stoichiometry 피팅 → DqdvFitTable 누적
  ↓
F5 calc_lam_lli → DegModeTable (주기 vs LAM_n/LAM_p/LLI)
  ↓
결과 엑셀 시트 + 플롯
```

**BDT 현재**: 수명시험 capacity retention 만 계산. **열화 원인 분해 없음** — 이 기능 도입 시 "용량 감소가 음극 때문인지, 양극 때문인지, Li inventory 때문인지" 분리 가능 → 셀 설계 의사결정 근거.

### 5.5 공수 / 리스크
- **공수**: F4 완성 가정 시 **+1일** (LAM/LLI 공식 자체는 50줄)
- **리스크**:
  - RPT 마다 fit 이 모두 성공해야 — 실패 fit 건너뛰기 로직 필요
  - BOL 기준점 선택 중요 (첫 RPT = BOL 가정)

---

## F6. HPPC multi-timepoint impedance

### 6.1 알고리즘
1. `_detect_pulses()`:
   - State R/C/D 전이 감지
   - `[tmin, tmax]` 내 지속시간만 valid
   - pulse 전후 R 로 감싸진 것만 허용
2. 각 pulse:
   - baseline = `Volts[0]` (pulse 직전)
   - `R(t) = |V(t) - baseline| / |I_avg|`
   - sample_times 에서 np.interp 로 보간
3. 출력: `[R_prepulse=0, R_instant, R_t1, ..., R_eop]` 시리즈

### 6.2 BDT 연결점
**현황**: Phase 1 분석 결과 BDT 데이터셋에 **HPPC 없음** (한 SOC 다전류 레벨 pulse 세트 부재).

**미래 활용**:
- 차량·ESS 용 셀 평가 시 HPPC 보편적
- BDT 의 DCIR 기능을 multi-timepoint 로 확장할 수 있음 (현재 고정 시점 R 만)

**공수**: 2일 (현시점 우선순위 낮음)

---

## F7. OCV peak matching (iR 동시 추정)

### 7.1 알고리즘
저율 충전/방전 dQ/dV 커브를 iR-shift 로 겹쳐서 OCV 추출:

```
dQ/dV_chg_shifted (V) = dQ/dV_chg (V - iR)
dQ/dV_dis_shifted (V) = dQ/dV_dis (V + iR)
    (대칭 shift)

min_iR  ‖dQ/dV_chg_shifted - dQ/dV_dis_shifted‖²
    (L-BFGS-B bounded optimization)

OCV ≈ midpoint(dQ/dV_chg_shifted, dQ/dV_dis_shifted)
```

### 7.2 입출력
**입력**:
- `charge`: DqdvSpline (저율 충전)
- `discharge`: DqdvSpline (저율 방전)
- `x0` (선택): iR 초기값 (없으면 피크 위치 기반 휴리스틱)

**출력**:
- `iR` (float): 최적 대칭 voltage shift [V]
- `DqdvSpline`: OCV proxy (shifted curves 의 midpoint)

### 7.3 BDT 연결
- BDT 의 연속 OCV / CCV scatter 시각화와 연동 가능
- 반셀 없이 풀셀 충/방전만으로 OCV 추정 가능 — 별도 반셀 데이터 필요없는 장점
- **공수**: 1일 (SciPy optimize 구현이 핵심, simple)

---

## F8. 파라미터 ±σ 불확실성 전파

### 8.1 두 가지 방법

**방법 A — scipy.curve_fit.pcov**:
```python
popt, pcov = curve_fit(model, x, y, ...)
perr = np.sqrt(np.diag(pcov))    # ±σ
```
→ 거의 **50줄 추가만으로 모든 fit 결과에 σ 자동 첨부** 가능.

**방법 B — Hessian 기반** (ampworks DqdvFitter 방식):
- trust-constr 등 minimize 결과의 Hessian 사용
- `cov = inv(H)`, `σ = √diag(cov)`
- Newton-like 방법에서 자연 부산물

### 8.2 Taylor 전파 (파생 변수)

파라미터 `x_i` 에 σ_i 있을 때, 파생량 `f(x)` 의 σ:
```
σ(f) = √Σ_i (∂f/∂x_i · σ_i)²
```

### 8.3 BDT 연결
- 현재 BDT 의 capacity retention, dcir 등 fitting 에 σ 부재 → 신뢰구간 리포트 불가
- **공수**: 0.5일 (helper 함수 `_uncertainty_propagate(func, x, x_std)` 작성 + 주요 fit 호출부 10군데 업데이트)

---

## 9. 전체 통합 공수 / 의존성

```
F3 Spline (0.5d) ──┐
                   ├─► F4 Fitter (3d) ──► F5 LAM/LLI (1d)  ──► [가치 ★★★★★]
F8 Uncertainty (0.5d) ─┘
                                                          ┌─► F7 OCV peak (1d)
F1 GITT D_s (1.5d) ──┐                                    │
                     ├─► 공통 pulse/rest 유틸 ────────────┤
F2 ICI D_s (0.5d) ───┘                                    │
                                                          └─► F6 HPPC (2d) [후순위]
```

**권장 실행 순서 (8일 플랜)**:
1. F8 (0.5d) — 기반 헬퍼
2. F3 (0.5d) — 스무딩 기반
3. F1 (1.5d) — 첫 독립 기능 (빠른 가치 검증)
4. F2 (0.5d) — F1 재활용
5. F4 (3d) — 피팅 파이프라인
6. F5 (1d) — LAM/LLI (F4 위에 즉시)
7. F7 (1d) — OCV peak
— F6 (HPPC) 는 데이터 확보 후 별도

---

## 10. 라이센스·저작권 준수 (BSD-3-Clause)

차용 시 **모든 포팅 파일 상단에** 다음 notice 필수:

```python
# Portions derived from ampworks (https://github.com/NatLabRockies/ampworks),
# Copyright © 2025 National Laboratory of the Rockies — Corey R. Randall.
# Licensed under BSD-3-Clause. See docs/licenses/ampworks-BSD-3.txt
```

그리고 `docs/licenses/ampworks-BSD-3.txt` 에 원문 라이센스 복사본 보관.

---

## 11. 정밀 입출력 스키마 요약 (한 눈에)

| 기능 | 입력 (DataFrame 컬럼) | 파라미터 | 출력 컬럼 |
|-----|----------------------|---------|----------|
| F1 GITT | Seconds, Amps, Volts | radius, tmin, tmax | SOC, Ds, Eeq |
| F2 ICI | Seconds, Amps, Volts | radius, tmin, tmax | SOC, Ds, Eeq |
| F3 Spline | Ah, Volts (or Seconds, Amps, Volts) | s (smoothing) | .Volts(), .SOC(), .dVdQ(), .dQdV() |
| F4 Fitter | (n, p, cell) 각 {SOC, Volts}, cell 은 +Ah | Nx (grid), bounds | DqdvFitResult (x, x_std) |
| F5 LAM/LLI | DqdvFitTable | — | Qn, Qp, Qc, LAMn, LAMp, LLI (+std) |
| F6 HPPC | Seconds, Amps, Volts | tmin, tmax, area, sample_times, steps | PulseNum, State, SOC_0, Ohms_0..N, ASI_0..N |
| F7 OCV | DqdvSpline (chg/dis) | x0 | iR, DqdvSpline |

---

## 12. 다음 액션

1. 본 문서 리뷰 후 도입 순서 확정
2. **F8 → F3 → F1** 순서 시작 권장 (기반 + 독립 고가치)
3. 진행 시 각 기능별 단독 변경로그 생성 (BDT 문서 체계 준수)

관련 문서:
- [ampworks 상세 우선순위](260419_ampworks_분석_BDT차용제안.md)
- [vault ACIR/DCIR/RSS](../../vault/03_Battery_Knowledge/ACIR_DCIR_RSS.md)
- [사이클분류 재검토](../02_변경검토/260419_사이클분류_전면재검토.md)
