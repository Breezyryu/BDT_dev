# ampworks 레포지토리 분석 + BDT 차용 제안

**날짜**: 2026-04-19
**대상 레포**: [NatLabRockies/ampworks](https://github.com/NatLabRockies/ampworks) (BSD-3-Clause, Python, Corey R. Randall / National Laboratory of the Rockies, 2025-03 기준)

---

## 1. ampworks 개요

**성격**: 배터리 실험 데이터의 **파라미터 추출·시각화** 전용 Python 툴킷. GUI 는 Dash/Plotly 웹 기반.

**목적 키워드**:
- 열화 모드(degradation mode) 분석 (LAM/LLI)
- 표준 프로토콜(GITT/ICI/HPPC) 파라미터 추출
- 물리 기반 모델(SPM/P2D)용 물성 추출

**라이센스**: BSD-3-Clause → **수식·알고리즘 차용 자유** (저작자 표기만 필요).

### 1.1 디렉토리 구조
```
src/ampworks/
├─ _core/         # 기반 클래스
├─ datasets/      # 데이터 로더·관리
├─ dqdv/          # dQ/dV 피팅 + LAM/LLI 열화 모드
│  ├─ _dqdv_spline.py   # B-spline smoothing
│  ├─ _dqdv_fitter.py   # grid_search + constrained_fit (stoichiometry 추정)
│  ├─ _lam_lli.py       # LAM/LLI 계산 + 불확실성 전파
│  ├─ _tables.py        # DqdvFitTable / DegModeTable
│  └─ gui_files/        # Dash/Plotly 웹 GUI (multi-page)
├─ gitt/          # GITT → D_s(solid-phase diffusivity) + E_eq + SOC
├─ hppc/          # HPPC → impedance + ASI (multi-timepoint)
├─ ici/           # ICI → D_s + E_eq (rest phase 기반)
├─ ocv/           # OCV peak matching
├─ plotutils/
├─ utils/
├─ _checks.py     # 검증·에러처리
├─ cli.py         # `ampworks -h`, `ampworks --app`
└─ labels.py
```

### 1.2 핵심 설계 원칙
- **모듈 분할**: 분석법별 독립 서브패키지 (gitt/hppc/ici/dqdv/ocv).
- **API 패턴**: Fitter 클래스 + `.grid_search()` → `.constrained_fit()` 2단계 + Table 객체로 배치 결과 집계.
- **불확실성**: Numerical Hessian 으로 ±σ 자동 계산·전파.
- **Jupyter 통합**: `run_gui(mode='inline'|'external')` — 노트북 내장 실행.
- **CLI**: 단일 명령어에서 GUI 선택 실행.

---

## 2. 모듈별 핵심 기술 요약

### 2.1 `gitt._extract_params` — **D_s 추출**
**입력**: `{Seconds, Amps, Volts}`, `radius` (입자 반경 m), `tmin/tmax` (회귀 구간)

**수식** (√t 선형회귀):
```
V = m√t + b          # pulse 초반 voltage response
b  = E_eq            # 평형전위
m  = dU/d√t          # 회귀 기울기

D_s = (4 / 9π) × (radius × dE/dt / dU/d√t)²
```

**출력**: 각 SOC 레벨별 `{D_s, E_eq, SOC}` 테이블.

### 2.2 `ici._extract_params` — GITT 의 rest-phase 변형
**입력**: `{Seconds, Amps, Volts}` — pulse 간 rest 포함
**핵심**: rest 중 voltage relaxation 에 대해 √t 회귀 → D_s + E_eq 추출 (pulse 초기 아닌 rest 이용).
→ BDT 의 "simplified GITT" 카테고리 데이터에 바로 적용 가능.

### 2.3 `hppc._extract_impedance` — 펄스 임피던스
**출력**: multi-timepoint impedance
- `R_instant` (첫 샘플)
- `R_eop` (end-of-pulse)
- `R_at(t_i)` (사용자 지정 시간점)
- ASI (Ohms·cm², 전극 면적 곱)

**수식**: `R = |ΔV| / |I_avg|`

### 2.4 `dqdv` — **LAM/LLI 열화 모드** (가장 유용한 차용 후보)

**피팅 파이프라인**:
1. **Input**: 음극 반셀 dQ/dV + 양극 반셀 dQ/dV + 풀셀 충방전 데이터 (BOL + EOL)
2. **Smoothing**: `DqdvSpline().fit()` — B-spline 평활
3. **Grid search**: 4개 stoichiometry (xn0, xn1, xp0, xp1) 초기값 coarse 탐색
4. **Constrained fit**: trust-region 최적화 + numerical Hessian 으로 ±σ 추정
5. **열화 계산**:

```python
Q_n = Ah / (xn1 - xn0)                    # 음극 가용용량
Q_p = Ah / (xp1 - xp0)                    # 양극 가용용량
LAM_n = 1 - Q_n / Q_n[0]                   # 음극 활물질 손실
LAM_p = 1 - Q_p / Q_p[0]                   # 양극 활물질 손실
Inv   = xn0 · Q_n + (1 - xp0) · Q_p        # Li 인벤토리
LLI   = 1 - Inv / Inv[0]                   # Li 인벤토리 손실
```

6. **Uncertainty 전파**: first-order Taylor 로 σ(LAM), σ(LLI) 계산.

### 2.5 GUI — Dash/Plotly 멀티페이지
- Navbar + Sidebar(접힘 가능) + 페이지 컨테이너 + Footer
- Window breakpoints 로 반응형 (≤1200px 모바일/데스크탑 전환)
- 페이지: `dqdv_fitting`, `figures`, `user_guide`
- Jupyter 노트북 내장 실행 지원

---

## 3. BDT 대비 비교

| 영역 | BDT (현재) | ampworks | 평가 |
|------|-----------|---------|------|
| **파일 구조** | 29K+ 줄 모놀리식 `proto_.py` | 분석법별 모듈 분할 | ampworks 유지보수성 ↑ |
| **GUI 스택** | PyQt6 데스크탑 | Dash/Plotly 웹 + Jupyter | 용도 다름 (BDT 사내 데스크탑 적합) |
| **GITT** | 사이클 분류 + 프로파일 시각화 | **D_s/E_eq 정량 추출** | ampworks 압도 |
| **dQ/dV** | 그래프 표시만 | **LAM/LLI 열화모드 계산** | ampworks 압도 |
| **HPPC** | 미지원 (데이터 없음) | impedance multi-timepoint | 미래 대비 |
| **ICI** | 미지원 | √t 회귀 기반 | 신규 기능 후보 |
| **OCV** | 산점도 시각화 | peak matching | 후보 |
| **Uncertainty** | 없음 | Hessian 기반 ±σ 전파 | 고급 기능 |
| **테스트/문서** | 변경로그 중심 | nox + readthedocs | 체계화 아이디어 |
| **CLI** | 없음 | `ampworks -h/--app` | 배치 처리 아이디어 |
| **Jupyter 통합** | 제한적 | 1급 시민 | 내부 리포트 자동화 |

---

## 4. BDT 차용 우선순위 제안

### 🔴 최우선 (★★★★★)

#### P1. LAM/LLI 열화모드 계산
**왜**: 배터리 수명 분석의 **핵심 지표**. BDT 이미 dQ/dV 탭 있음 — 공식 추가만으로 큰 가치 창출.
**방법**:
- 반셀 dQ/dV + 풀셀 데이터 로딩 (BDT 이미 지원하는 240821 GITT, M2 SDI 반셀 등 활용 가능)
- stoichiometry 4개 파라미터 피팅 (grid_search → scipy `minimize(method='trust-constr')`)
- 위 공식으로 LAM_n, LAM_p, LLI 계산 → 엑셀 출력 컬럼 추가
- 이미 있는 dvdqraw 폴더 (`!dvdqraw/S25_291_anode_dchg_02C_gen4`, cathode) 가 반셀 데이터 소스
**구현 난이도**: 중 (200~300줄 + 테스트)
**리스크**: 음극/양극 dQ/dV 데이터 품질에 민감 — B-spline smoothing 필수.

#### P2. GITT → D_s (solid-phase diffusivity) 자동 추출
**왜**: BDT 에 GITT 실험 많음 (240821, 성능 GITT, M2 SDI 반셀 등) — 프로파일만 보고 D_s 는 수기 계산. 자동화하면 전공자 시간 절감.
**방법**:
- 펄스 구간 자동 감지 (사이클 분류기 `GITT(full)` 결과 재활용)
- 각 펄스의 √t vs V 선형회귀
- `D_s = (4/9π)(r·dE/dt / dU/d√t)²`
- SOC vs D_s 플롯 + 테이블 출력
- **입력 추가 필요**: 입자 반경 r (UI 에 입력 필드 하나만 추가)
**구현 난이도**: 중 (150~200줄)
**리스크**: 반셀 GITT 경우 dE/dt 기준이 다를 수 있음 — ampworks 코드 참조 시 확인.

---

### 🟡 중간 (★★★)

#### P3. 파라미터 fitting 결과의 ±σ 자동 리포트
**왜**: BDT 의 DCIR/dv-dq fitting 등에 σ 가 없어 신뢰구간 불명.
**방법**: scipy `curve_fit` 의 `pcov` → `σ_i = sqrt(pcov[i,i])`. 엑셀에 ±σ 컬럼 추가.
**구현 난이도**: 하 (50줄)

#### P4. ICI (Incremental Current Interruption) 분석
**왜**: BDT 의 simplified GITT 카테고리(Phase 0/1 에서 48건 식별됨) 데이터에 바로 적용 가능. rest phase 만으로 D_s 추출.
**방법**: `ici._extract_params` 공식 그대로 포팅.
**구현 난이도**: 중 (150줄)
**잠재 데이터**: 260306 현혜정 LWN 25P SOC별 DCIR 신규 등 RSS 측정 세트.

---

### 🟢 후순위 (★★)

#### P5. HPPC impedance multi-timepoint
**왜**: 현 데이터셋엔 HPPC 없지만 미래 대비 + BDT 의 DCIR 기능 일반화 가능.
**방법**: `hppc._extract_impedance` 포팅.
**구현 난이도**: 중 (200줄)

#### P6. OCV peak matching
**방법**: dQ/dV 피크 검출(scipy.signal.find_peaks) + 양·음극 피크 매칭.

---

### ⚪ 구조/아키텍처 차용 (★)

#### P7. 모듈 분할 점진 리팩토링
**방향**:
- `proto_.py` 29K 줄 → 기능별 서브모듈 (cycle_classify, gitt_analysis, dqdv_analysis, ...)
- 외부 인터페이스는 유지 (WindowClass)
- 점진적 추출 (한 번에 하지 말 것 — 회귀 리스크)
**구현 난이도**: 상 (장기 작업 — Phase 단위로 분할)

#### P8. 테스트·문서 체계
**차용점**:
- `nox` 기반 테스트 자동화 (pyproject.toml 이미 있음)
- 예제 스크립트 디렉토리(`examples/`) 정립
- README + readthedocs 스타일 입문서

---

## 5. 즉시 착수 가능한 구현 플랜

### 제안 Phase 3 (사이클 분류 마감 후 후속 작업)

| 단계 | 작업 | 예상 공수 | 의존성 |
|------|------|---------|-------|
| **A** | P2 GITT D_s 추출 | 1~2일 | 이미 있는 GITT 분류(`GITT(full)` 카테고리 활용) |
| **B** | P3 ±σ 리포트 공통화 | 0.5일 | 없음 |
| **C** | P1 LAM/LLI 계산 | 3~4일 | dvdqraw 반셀 데이터 로더 (이미 있음) |
| **D** | P4 ICI | 1~2일 | simplified GITT 분류 활용 |

**총 7~9일** 에 4개 고가치 기능 확보 가능.

---

## 6. 차용 시 주의사항

1. **라이센스 준수**: BSD-3-Clause — 파일 상단에 ampworks 저작권 표기(Copyright © National Laboratory of the Rockies, Corey R. Randall) + BSD 텍스트 포함. 수식만 차용은 어텐션 표기.
2. **의존성**: ampworks 는 `scipy`, `numpy`, `pandas` 만 필요 — BDT 의존성과 겹침. 추가 설치 부담 없음.
3. **단위계**:
   - ampworks: SI (seconds, amps, volts, meters)
   - BDT: 일부 μA/μAh 혼재 → 입력 단계에서 단위 정규화 필수
4. **Dash/Plotly GUI 는 차용 안 함**: BDT 의 PyQt6 데스크탑 UX 와 맞지 않음. 수식·계산 로직만 포팅.
5. **반셀 데이터 포맷**: ampworks 는 `{SOC, Volts}` 형태 기대. BDT 의 `!dvdqraw/*.txt` 는 내부 포맷이라 변환 layer 필요.

---

## 7. 핵심 차용 권장사항 (one-liner)

| 우선순위 | 기능 | 근거 |
|---------|------|------|
| ★★★★★ | **LAM/LLI 열화모드** | 수명해석 핵심, BDT dQ/dV 연계로 즉시 고부가 |
| ★★★★★ | **GITT D_s 추출** | 기존 GITT 데이터 다수, 수기계산 자동화 |
| ★★★ | **±σ 불확실성 리포트** | 모든 fitting 에 공통 적용 가능, 50줄 |
| ★★★ | **ICI 분석** | simplified GITT 카테고리 이미 식별됨 |
| ★★ | HPPC | 미래 대비 |
| ★ | 모듈 분할 | 장기 리팩토링 |

---

## 관련 문서

- [ampworks GitHub](https://github.com/NatLabRockies/ampworks)
- [ampworks Docs](https://ampworks.readthedocs.io)
- [[ACIR_DCIR_RSS]] — BDT 내부 저항 도메인 지식
- [260419_사이클분류_전면재검토.md](../02_변경검토/260419_사이클분류_전면재검토.md) — Phase 1/2 에서 확립한 9종 분류 체계와 연동
