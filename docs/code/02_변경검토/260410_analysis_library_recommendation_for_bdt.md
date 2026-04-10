---
date: 2026-04-10
tags: [python, library, pyinstaller, pybamm, optimization]
aliases: [BDT 라이브러리 추천]
---

# BDT 코드에 유용한 라이브러리/스킬 종합 추천

> **평가 기준**: BDT 기능 관련성 × PyInstaller 호환성 × 도입 난이도
> **BDT 현황**: PyQt6 모놀리식 앱(27,000줄), PyInstaller `--onefile` 빌드, pybamm+casadi 포함

---

## 평가 프레임워크

### PyInstaller 호환성 등급

| 등급 | 의미 | 예시 |
|:--:|------|------|
| 🟢 | **문제없음** — 순수 Python 또는 PyInstaller 공식 지원 | scikit-learn, statsmodels, sympy |
| 🟡 | **주의 필요** — `--hidden-import` 또는 `--collect-all` 추가 필요 | pymc, torch, pymatgen |
| 🔴 | **위험** — C/Fortran 바이너리 복잡, DLL 충돌 가능, EXE 크기 폭증 | tensorflow, qiskit, astropy |
| ⚫ | **불가/무의미** — PyInstaller로 번들 불가 또는 서버사이드 전용 | Modal(클라우드), Dask(분산), DB서버 |

### BDT 관련성 등급 (이전 평가 유지)

| 등급 | 의미 |
|:--:|------|
| ⭐ | **매우 유용** — BDT 핵심 기능 직접 강화 |
| ✅ | **유용** — 특정 워크플로우에 명확한 가치 |
| 🔶 | **조건부** — 특정 Phase/시나리오에서만 가치 |
| ⚠️ | **과잉** — BDT 규모 대비 복잡도 초과 |
| ❌ | **무관** — 배터리 데이터 분석과 무관한 도메인 |

---

## 1단계: 즉시 도입 추천 (Priority 1)

> BDT에 직접 가치 + PyInstaller 호환 양호 + 기존 의존성과 충돌 없음

### ⭐ PyMOO — 다목적 최적화

| 항목 | 내용 |
|------|------|
| **PyInstaller** | 🟢 순수 Python + NumPy, 추가 설정 불필요 |
| **용도** | PyBaMM 파라미터 다목적 피팅 (OCV + DCIR + 용량 동시 최적화) |
| **EXE 크기** | +~2 MB (무시 가능) |
| **도입 방법** | `try-except` + `HAS_PYMOO` 플래그, PyBaMM 탭에 "최적화 피팅" 버튼 추가 |
| **구체적 활용** | `NSGA-II`로 `_key_map` 14개 파라미터 중 선택 파라미터 최적화 |

```python
# 도입 예시
try:
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.optimize import minimize
    HAS_PYMOO = True
except ImportError:
    HAS_PYMOO = False
```

### ⭐ SymPy — 기호 수학

| 항목 | 내용 |
|------|------|
| **PyInstaller** | 🟢 순수 Python, PyInstaller 공식 지원 |
| **용도** | 수명 예측 모델 수식 표시, 편미분 자동 계산, 단위 검증 |
| **EXE 크기** | +~15 MB |
| **도입 방법** | `try-except` + `HAS_SYMPY`, Eu/승인/실수명 탭에서 피팅 수식 렌더링 |
| **구체적 활용** | `Q(n) = 1 - a*n^b - c*exp(d*(n-e))` 수식의 야코비안 자동 계산 → curve_fit 정확도 향상 |

### ✅ scikit-learn + SHAP — 파라미터 민감도

| 항목 | 내용 |
|------|------|
| **PyInstaller** | 🟢 scikit-learn은 PyInstaller 공식 지원, SHAP도 호환 양호 |
| **용도** | PyBaMM 파라미터 중요도 분석 (어떤 파라미터가 용량/DCIR에 가장 영향 큰지) |
| **EXE 크기** | +~30 MB (scikit-learn + joblib + SHAP) |
| **도입 방법** | optional dependency, 시뮬레이션 결과 분석 기능으로 추가 |
| **주의사항** | `--hidden-import sklearn.utils._cython_blas` 등 2-3개 hidden import 필요 |

### ✅ statsmodels — 통계 모델링

| 항목 | 내용 |
|------|------|
| **PyInstaller** | 🟢 이미 scipy/numpy 의존성이 있어 추가 부담 최소 |
| **용도** | 사이클 수명 트렌드 통계 검정, ARIMA 시계열 예측, 잔차 분석 |
| **EXE 크기** | +~8 MB |
| **도입 방법** | optional dependency, 실수명 예측 탭에 통계 검정 기능 |

---

## 2단계: 중기 도입 추천 (Priority 2)

> BDT 확장에 유용하지만 PyInstaller 설정 추가 필요 또는 특정 Phase에서만 필요

### ✅ Pymatgen — 소재 물성 DB

| 항목 | 내용 |
|------|------|
| **PyInstaller** | 🟡 `--collect-all pymatgen` 필요, spglib C 바이너리 포함 |
| **용도** | Materials Project API에서 양극/음극 소재 물성 자동 조회 → PyBaMM 파라미터 |
| **EXE 크기** | +~50 MB (spglib + monty + ruamel.yaml) |
| **도입 방법** | **별도 스크립트 권장** — EXE 번들에 포함하지 않고 개발 환경에서만 사용 |
| **구체적 활용** | `_key_map_extended`의 양극 최대 농도, 진밀도 등을 DB에서 자동 조회 |

> ⚠️ **PyInstaller 권장**: BDT EXE에 포함하지 말고 `ingest_material_data.py` 별도 스크립트로 운영

### 🔶 PyMC — 베이지안 불확실성

| 항목 | 내용 |
|------|------|
| **PyInstaller** | 🔴 pytensor(구 aesara) C 컴파일 의존 → PyInstaller 번들 매우 어려움 |
| **용도** | PyBaMM 파라미터 사후분포 추정, 수명 예측 신뢰구간 |
| **EXE 크기** | +~200 MB 이상 (pytensor + C 런타임) |
| **도입 방법** | **EXE 번들 불가** → 개발 환경 전용 또는 별도 Jupyter 노트북에서 사용 |
| **대안** | `scipy.optimize.curve_fit`의 `pcov` + bootstrap으로 간이 불확실성 추정 가능 |

### 🔶 Polars — 고속 DataFrame

| 항목 | 내용 |
|------|------|
| **PyInstaller** | 🟡 Rust 바이너리 포함, `--collect-binaries polars` 필요 |
| **용도** | DB Phase 5+(프로필 시계열) 대용량 데이터 처리 속도 개선 |
| **EXE 크기** | +~25 MB |
| **도입 시점** | DB Phase 5 이후, 프로필 데이터 100만+ 행 처리 시 |
| **주의사항** | pandas API와 호환되지 않으므로 기존 코드 수정 필요 |

---

## 3단계: 장기/연구용 (Priority 3)

> PINN 연구나 고급 분석에 유용하지만 BDT EXE에는 포함하지 않는 것이 바람직

### 🔶 PyTorch Lightning — PINN 학습

| 항목 | 내용 |
|------|------|
| **PyInstaller** | 🔴 torch 자체가 ~2GB, CUDA 포함 시 ~5GB → EXE 번들 비현실적 |
| **용도** | PINN 기반 수명 예측 모델 학습 |
| **도입 방법** | **절대 BDT EXE에 포함 금지** → 별도 `pinn_training/` 프로젝트로 분리 |
| **BDT 연동** | 학습된 ONNX 모델을 BDT에서 `onnxruntime`으로 추론만 수행 |

```
[권장 아키텍처]
pinn_training/          ← PyTorch Lightning, GPU 서버
  ├── train.py
  └── export_onnx.py    → model.onnx 출력

BDT (PyInstaller EXE)   ← onnxruntime만 포함 (~20MB)
  └── pinn_inference()   → model.onnx 로드 → 수명 예측
```

### 🔶 UMAP-learn — 차원 축소

| 항목 | 내용 |
|------|------|
| **PyInstaller** | 🟡 numba JIT 의존 → `--collect-all numba` 필요, +~100MB |
| **용도** | 다품목 사이클 데이터 클러스터링, 열화 패턴 분류 시각화 |
| **도입 방법** | optional, DB Phase 4(DB Compare 탭) 이후 |
| **대안** | `sklearn.decomposition.PCA` + `sklearn.manifold.TSNE`로 대체 가능 (추가 의존성 없음) |

### 🔶 aeon — 시계열 ML

| 항목 | 내용 |
|------|------|
| **PyInstaller** | 🟡 numba/sktime 의존, hidden-import 다수 |
| **용도** | 사이클 수명 시계열 분류, 이상 탐지 |
| **대안** | scikit-learn의 시계열 feature extraction으로 충분한 경우 많음 |

---

## 전면 제외 목록 (BDT 무관 또는 PyInstaller 비호환)

### ❌ 도메인 무관 (배터리 과학과 관계 없음)

| 패키지 | 분야 | 제외 사유 |
|--------|------|----------|
| **Biopython, Scanpy, AnnData** | 생명과학/유전체 | 바이오인포매틱스 전용 |
| **RDKit, DeepChem** | 화학정보학 | 분자 구조/약물 설계 전용 |
| **ESMFold, AlphaFold, ProDy** | 단백질 공학 | 단백질 접힘 전용 |
| **MONAI, TorchXRayVision** | 의료 영상 | 의료 AI 전용 |
| **MNE-Python, NiLearn** | 뇌과학 | 뇌파/fMRI 전용 |
| **FHIR, HL7** | 의료 표준 | 전자건강기록 전용 |
| **ETE3, DendroPy** | 계통학 | 진화 계통수 전용 |
| **COBRApy** | 대사 모델링 | 생체 대사 네트워크 전용 |
| **Astropy** | 천문학 | 천체 데이터 전용 |
| **GeoPandas, GeoMaster** | 지리공간 | 지도/위치 데이터 전용 |
| **Qiskit, Cirq, PennyLane, QuTiP** | 양자컴퓨팅 | 양자 회로 시뮬레이션 전용 |
| **Transformers (HuggingFace)** | NLP/LLM | BDT는 텍스트 생성 기능 없음 |
| **Stable Baselines3, PufferLib** | 강화학습 | 배터리 데이터 분석에 RL 불필요 |
| **Torch Geometric** | 그래프 ML | 배터리 데이터는 그래프 구조 아님 |
| **FluidSim** | CFD | 유체역학 전용 |
| **NetworkX** | 네트워크 분석 | BDT 데이터에 네트워크 구조 없음 |
| **TimesFM** | Google 시계열 | 서버 추론 전용, PyInstaller 번들 불가 |

### ⚠️ 유용할 수 있으나 PyInstaller 호환성 문제

| 패키지 | PyInstaller 문제 | 대안 |
|--------|-----------------|------|
| **PyMC** | pytensor C 컴파일 → EXE 번들 불가 | scipy curve_fit + bootstrap |
| **Dask** | 분산처리 → EXE와 무관 | pandas chunked processing |
| **Vaex** | C++ 바이너리 복잡 → 번들 어려움 | polars (더 나은 호환성) |
| **MATLAB/Octave (oct2py)** | 외부 런타임 필요 → EXE 불가 | scipy + numpy로 대체 |

---

## 문서 처리 스킬 (BDT 외부 도구)

> 이 스킬들은 BDT EXE가 아닌 **보고서 자동화/문서 생성** 워크플로우에서 활용

| 스킬/패키지 | 용도 | BDT 연동 방식 |
|------------|------|-------------|
| **python-docx** | Word 보고서 자동 생성 | 별도 스크립트: 사이클 데이터 → 보고서 |
| **openpyxl** | Excel 결과 내보내기 | BDT 내 선택적 포함 가능 (🟢 PyInstaller 호환) |
| **python-pptx** | 프레젠테이션 자동 생성 | 별도 스크립트: 그래프 → PPT |
| **Mermaid** | 다이어그램 생성 | 문서 작성 시 활용 (BDT 코드 무관) |
| **Matplotlib/Seaborn** | 시각화 | ✅ 이미 BDT 핵심 의존성 |

---

## 특수 추천: SimPy — 시험 스케줄링 시뮬레이션

| 항목 | 내용 |
|------|------|
| **PyInstaller** | 🟢 순수 Python, 의존성 없음 |
| **용도** | 충방전기 채널 스케줄링 최적화 시뮬레이션 |
| **EXE 크기** | +~0.5 MB |
| **활용 시나리오** | "PNE 25채널 + Toyo 5채널에 30개 시험을 어떻게 배분하면 최적인가?" |
| **도입 시점** | 현황 탭(Tab 0) 고도화 시 |
| **판정** | 🔶 조건부 — 시험 스케줄링 자동화 요구 시에만 |

---

## 최종 추천 로드맵 (PyInstaller 호환성 반영)

### Phase A: 즉시 도입 (EXE 포함 가능)

```
BDT EXE 번들 가능 — 추가 EXE 크기 ~55 MB
┌─────────────────────────────────────────────────┐
│  PyMOO ⭐        → PyBaMM 파라미터 다목적 최적화  │
│  SymPy ⭐        → 수식 표시 + 야코비안 자동 계산  │
│  scikit-learn ✅  → 파라미터 민감도 분석           │
│  SHAP ✅         → 파라미터 중요도 시각화           │
│  statsmodels ✅   → 수명 트렌드 통계 검정           │
│  openpyxl ✅      → Excel 결과 내보내기             │
└─────────────────────────────────────────────────┘

build_exe_onefile.bat 추가 사항:
  --hidden-import pymoo
  --hidden-import sklearn.utils._cython_blas
  --hidden-import sklearn.neighbors._typedefs
  --hidden-import shap
  --hidden-import statsmodels
```

### Phase B: 개발 환경 전용 (EXE 미포함)

```
BDT EXE에 포함하지 않음 — 별도 스크립트/노트북
┌─────────────────────────────────────────────────┐
│  Pymatgen 🔶      → 소재 물성 DB 조회 스크립트    │
│  PyMC 🔶          → 파라미터 불확실성 분석 노트북  │
│  Polars 🔶        → DB Phase 5+ 대용량 처리       │
│  python-docx 🔶   → 보고서 자동 생성 스크립트      │
│  python-pptx 🔶   → 프레젠테이션 자동 생성         │
└─────────────────────────────────────────────────┘
```

### Phase C: 연구 프로젝트 분리

```
별도 프로젝트 — BDT 코드베이스와 분리
┌─────────────────────────────────────────────────┐
│  PyTorch Lightning → PINN 학습 (pinn_training/)  │
│  → BDT에는 onnxruntime만 포함하여 추론            │
│                                                   │
│  UMAP 🔶          → 다품목 열화 패턴 클러스터링    │
│  → sklearn PCA/TSNE로 대체 가능                   │
└─────────────────────────────────────────────────┘
```

### PINN 추론 아키텍처 (PyInstaller 호환)

```
[학습 서버 / Jupyter]          [BDT EXE]
PyTorch Lightning              onnxruntime (~20MB, 🟢)
  ↓ export                       ↓ load
model.onnx  ──────────────→  pinn_inference()
                                ↓
                            수명 예측 결과 → 실수명 예측 탭
```

`onnxruntime`은 PyInstaller 호환성이 양호하며, `--collect-binaries onnxruntime` 하나만 추가하면 됩니다.

---

## PyInstaller 빌드 영향도 요약

| 라이브러리 | EXE 크기 증가 | 추가 설정 | 빌드 시간 영향 |
|-----------|:----------:|----------|:----------:|
| pymoo | +2 MB | `--hidden-import` 1개 | 무시 |
| sympy | +15 MB | 없음 | 미미 |
| scikit-learn | +25 MB | `--hidden-import` 2-3개 | 중간 |
| SHAP | +5 MB | `--hidden-import` 1개 | 미미 |
| statsmodels | +8 MB | 없음 | 미미 |
| openpyxl | +3 MB | 없음 | 무시 |
| **합계** | **+~58 MB** | **hidden-import 5-7개** | **~30초 증가** |
| (참고) 현재 BDT EXE | ~350 MB | pybamm+casadi+PyQt6 | ~3분 |

> 현재 EXE 350MB 대비 +58MB(16% 증가)는 합리적인 수준입니다.

---

## 인터넷 검색 추가 발견 — 배터리 전용 라이브러리 (2026-04-10)

> GitHub, PyPI, 학술 논문에서 발견한 **배터리/전기화학 특화 오픈소스 도구**

### ⭐ lmfit — 고급 커브 피팅 (scipy.optimize 상위 호환)

| 항목 | 내용 |
|------|------|
| **GitHub** | [lmfit/lmfit-py](https://github.com/lmfit/lmfit-py) ★2,000+ |
| **PyInstaller** | 🟢 순수 Python (scipy/numpy만 의존) |
| **용도** | BDT 수명 예측 피팅(`Q(n) = 1 - a*n^b - c*exp(d*(n-e))`) 강화 |
| **EXE 크기** | +~2 MB (무시 가능) |
| **scipy.optimize.curve_fit 대비 장점** | |

```
scipy.optimize.curve_fit          lmfit
─────────────────────             ─────
bounds=(lower, upper) 만 가능     → 파라미터 fix/link/constraint 가능
공분산 행렬만 반환                → 신뢰구간 자동 계산
모델 클래스 없음                  → Model 클래스로 재사용 가능
```

```python
# BDT 수명 예측 피팅 예시 — lmfit 적용
from lmfit import Model, Parameters

def capacity_fade(n, a, b, c, d, e):
    """수명 예측 경험적 모델"""
    return 1 - a * n**b - c * np.exp(d * (n - e))

model = Model(capacity_fade)
params = Parameters()
params.add('a', value=0.01, min=0)       # a ≥ 0 강제
params.add('b', value=0.5, min=0.1, max=1.0)  # 0.1 ≤ b ≤ 1.0
params.add('c', value=0.001, min=0)
params.add('d', value=0.005, min=0)
params.add('e', value=500, min=0)        # knee point 위치

result = model.fit(y_data, params, n=x_data)
print(result.fit_report())  # 파라미터 + 신뢰구간 + R² 자동 출력
```

> **즉시 도입 강력 추천**: 기존 `curve_fit` 코드를 최소 수정으로 교체 가능하며, 파라미터 제약조건 + 불확실성 정량화가 핵심 가치

### ✅ cellpy — 배터리 사이클 데이터 통합 파서

| 항목 | 내용 |
|------|------|
| **GitHub** | [jepegit/cellpy](https://github.com/jepegit/cellpy) ★~500, JOSS 2024 논문 |
| **PyInstaller** | 🟢 순수 Python (pandas 기반) |
| **용도** | Arbin/BioLogic/Gamry 등 다양한 사이클러 포맷 파싱, dQ/dV 분석 내장 |
| **BDT 활용** | 현재 Toyo+PNE만 지원 → cellpy로 Arbin/BioLogic 포맷 추가 가능 |
| **도입 시점** | DB Phase 2+ (외부 업체 데이터 통합 시) |
| **주의** | BDT 자체 파서와 기능 중복 — 기존 코드 교체보다는 새 포맷 추가용으로 권장 |

### ✅ impedance.py — 전기화학 임피던스 분석 (EIS)

| 항목 | 내용 |
|------|------|
| **GitHub** | [ECSHackWeek/impedance.py](https://github.com/ECSHackWeek/impedance.py) ★~600 |
| **PyInstaller** | 🟢 순수 Python (scipy 의존) |
| **용도** | EIS 데이터 로드 → Kramers-Kronig 검증 → 등가회로 피팅 |
| **BDT 활용** | DCIR 탭 확장: 펄스 DCIR → R₀(옴) + R_ct(전하이동) 분리 추출 |
| **도입 시점** | DCIR 심화 분석 기능 추가 시 |

```python
# R₀ + R_ct 분리 추출 예시
from impedance.models.circuits import CustomCircuit
circuit = CustomCircuit('R0-p(R1,C1)-p(R2,C2)')
circuit.fit(frequencies, Z_data)
# R0 = 옴 저항, R1 = SEI 저항, R2 = 전하이동 저항
```

### 🔶 BEEP — 배터리 수명 조기 예측 (NREL)

| 항목 | 내용 |
|------|------|
| **GitHub** | [TRI-AMDD/beep](https://github.com/TRI-AMDD/beep) ★~1,500 |
| **PyInstaller** | 🟢 pandas/scikit-learn 기반 |
| **용도** | 대량 사이클 데이터 자동 검증, 특성 추출, ML 기반 수명 조기 예측 |
| **BDT 활용** | 데이터 검증 규칙(CE 이상, DCIR 음수 등) 참고 → BDT QA 로직 강화 |
| **도입 방법** | 코드 참조용 — BEEP의 검증 로직을 BDT에 이식하는 것이 현실적 |

### 🔶 galvani — 사이클러 파일 포맷 변환

| 항목 | 내용 |
|------|------|
| **GitHub** | [echemdata/galvani](https://github.com/echemdata/galvani) ★~200 |
| **PyInstaller** | 🟢 순수 Python |
| **용도** | BioLogic .mpr, Arbin .res 등 독점 포맷 → pandas DataFrame |
| **BDT 활용** | cellpy와 유사 — 외부 사이클러 데이터 추가 지원 시 |

### 🔶 pyimpspec — 고급 EIS 스펙트럼 분석

| 항목 | 내용 |
|------|------|
| **GitHub** | [vyrjana/pyimpspec](https://github.com/vyrjana/pyimpspec) ★~300 |
| **PyInstaller** | 🟢 순수 Python |
| **용도** | impedance.py보다 고급: CNLS 피팅, DRT(Distribution of Relaxation Times) 분석 |
| **도입 시점** | EIS 기반 열화 진단 연구 시 |

---

## 인터넷 검색 추가 발견 — Claude 스킬 및 참고 리소스

### 배터리 도메인 참고 리소스

| 리소스 | URL | BDT 활용 |
|--------|-----|---------|
| **awesome-battery-data** | [pauljgasper/awesome-battery-data](https://github.com/pauljgasper/awesome-battery-data) | 오픈소스 배터리 데이터셋, 모델링 코드, 분석 도구 종합 목록 |
| **Battery Intelligence Lab** | [battery-intelligence-lab.github.io](https://battery-intelligence-lab.github.io/) | Oxford 대학 배터리 연구그룹 — 오픈 데이터/코드 |
| **PyBOP** | PyBaMM 기반 파라미터화/최적화 도구 | PyMOO 대안 — PyBaMM 팀이 직접 개발한 파라미터 최적화 |
| **NASA Prognostics** | NASA 배터리 예측 모델 라이브러리 | 수명 예측 알고리즘 참고 |

### Claude Code 스킬 리포지토리

| 리소스 | URL | 활용 |
|--------|-----|------|
| **awesome-claude-code** | [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | Claude Code 기능/스킬 모음 |
| **awesome-claude-skills** | [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills) | 커뮤니티 스킬 큐레이션 |
| **220+ Claude Skills** | [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) | 엔지니어링/제품/컴플라이언스 스킬 |
| **antigravity-awesome-skills** | [sickn33/antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills) | 1,370+ 에이전틱 스킬, CLI 설치 |

> Claude Code 스킬은 BDT EXE와 무관하며, **개발 워크플로우 효율화**용입니다.
> BDT 프로젝트에는 이미 맞춤 instruction 파일(`battery-science`, `pybamm`, `python-style` 등)이 있으므로, 외부 스킬보다 기존 instruction 체계가 더 적합합니다.

---

## 최종 추천 로드맵 (통합 업데이트)

### Phase A: 즉시 도입 (EXE 포함 가능) — 7개

```
BDT EXE 번들 가능 — 추가 EXE 크기 ~60 MB
┌──────────────────────────────────────────────────────┐
│  PyMOO ⭐         → PyBaMM 파라미터 다목적 최적화     │
│  SymPy ⭐         → 수식 표시 + 야코비안 자동 계산     │
│  lmfit ⭐ [신규]  → 수명 피팅 강화 (curve_fit 상위호환) │
│  scikit-learn ✅   → 파라미터 민감도 분석              │
│  SHAP ✅          → 파라미터 중요도 시각화              │
│  statsmodels ✅    → 수명 트렌드 통계 검정              │
│  openpyxl ✅       → Excel 결과 내보내기                │
└──────────────────────────────────────────────────────┘

build_exe_onefile.bat 추가 사항:
  --hidden-import pymoo
  --hidden-import sklearn.utils._cython_blas
  --hidden-import sklearn.neighbors._typedefs
  --hidden-import shap
  --hidden-import statsmodels
  --hidden-import lmfit
```

### Phase B: 개발 환경 전용 + 기능 확장 시 (EXE 미포함)

```
BDT EXE에 포함하지 않음 — 별도 스크립트/노트북
┌──────────────────────────────────────────────────────┐
│  Pymatgen 🔶       → 소재 물성 DB 조회 스크립트       │
│  PyMC 🔶           → 파라미터 불확실성 분석 노트북     │
│  Polars 🔶         → DB Phase 5+ 대용량 처리          │
│  cellpy ✅ [신규]  → Arbin/BioLogic 포맷 추가 지원    │
│  impedance.py ✅ [신규] → EIS 기반 DCIR 분리 분석     │
│  python-docx 🔶    → 보고서 자동 생성 스크립트         │
│  python-pptx 🔶    → 프레젠테이션 자동 생성            │
└──────────────────────────────────────────────────────┘
```

### Phase C: 연구 프로젝트 분리

```
별도 프로젝트 — BDT 코드베이스와 분리
┌──────────────────────────────────────────────────────┐
│  PyTorch Lightning  → PINN 학습 (pinn_training/)     │
│  → BDT에는 onnxruntime만 포함하여 추론               │
│                                                       │
│  UMAP 🔶           → 다품목 열화 패턴 클러스터링       │
│  → sklearn PCA/TSNE로 대체 가능                       │
│                                                       │
│  pyimpspec 🔶 [신규] → EIS DRT 분석 (연구용)         │
│  BEEP 🔶 [신규]     → 데이터 검증 규칙 참고/이식      │
└──────────────────────────────────────────────────────┘
```

### PINN 추론 아키텍처 (PyInstaller 호환)

```
[학습 서버 / Jupyter]          [BDT EXE]
PyTorch Lightning              onnxruntime (~20MB, 🟢)
  ↓ export                       ↓ load
model.onnx  ──────────────→  pinn_inference()
                                ↓
                            수명 예측 결과 → 실수명 예측 탭
```

`onnxruntime`은 PyInstaller 호환성이 양호하며, `--collect-binaries onnxruntime` 하나만 추가하면 됩니다.

---

## PyInstaller 빌드 영향도 요약 (업데이트)

| 라이브러리 | EXE 크기 증가 | 추가 설정 | 빌드 시간 영향 |
|-----------|:----------:|----------|:----------:|
| pymoo | +2 MB | `--hidden-import` 1개 | 무시 |
| sympy | +15 MB | 없음 | 미미 |
| lmfit [신규] | +2 MB | 없음 | 무시 |
| scikit-learn | +25 MB | `--hidden-import` 2-3개 | 중간 |
| SHAP | +5 MB | `--hidden-import` 1개 | 미미 |
| statsmodels | +8 MB | 없음 | 미미 |
| openpyxl | +3 MB | 없음 | 무시 |
| **합계** | **+~60 MB** | **hidden-import 5-7개** | **~30초 증가** |
| (참고) 현재 BDT EXE | ~350 MB | pybamm+casadi+PyQt6 | ~3분 |

> 현재 EXE 350MB 대비 +60MB(17% 증가)는 합리적인 수준입니다.

---

## 결론

100+ 패키지 + 인터넷 검색 결과를 종합하면, **BDT EXE에 실제로 번들하여 쓸 수 있는 것은 7개**입니다.
배터리 전용 라이브러리(cellpy, impedance.py, BEEP 등)는 기능 확장 시 개발 환경에서 활용합니다.

**핵심 원칙**: BDT는 PyInstaller `--onefile` 배포 도구이므로,
→ 순수 Python 또는 잘 알려진 C 확장만 EXE에 포함
→ 무거운 ML/과학 라이브러리는 별도 스크립트/프로젝트로 분리
→ PINN은 학습-추론 분리 아키텍처 (PyTorch → ONNX → onnxruntime)
→ 배터리 전용 도구(cellpy, impedance.py)는 기능 확장 Phase에서 선택적 도입
→ Claude 스킬은 BDT 기존 instruction 체계(`battery-science.instructions.md` 등)가 이미 최적화되어 있어 외부 스킬 추가 불필요

### 최우선 도입 3개 (가성비 최고)

| 순위 | 라이브러리 | 이유 |
|:---:|-----------|------|
| 1 | **lmfit** | curve_fit 드롭인 대체, 파라미터 제약+신뢰구간, +2MB, 설정 0개 |
| 2 | **PyMOO** | PyBaMM 다목적 최적화의 핵심, +2MB, 순수 Python |
| 3 | **SymPy** | 수식 렌더링+자동미분, 수명 예측 모델 정확도 향상, +15MB |
