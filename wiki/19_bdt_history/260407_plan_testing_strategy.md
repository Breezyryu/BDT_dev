# BDT 테스팅 전략 (Testing Strategy)

> 작성일: 2026-04-07
> 목적: 리팩토링 안전망 + 배터리 과학 검증 + 신규 기능 품질 보증

---

## 1. 현황 분석

### 1.1 현재 테스트 커버리지

| 영역 | 테스트 파일 | 테스트 수 | 상태 |
|------|-----------|----------|------|
| 경로 파싱 | `test_path_parsing.py` | ~28 | ✅ 양호 |
| 사이클 분석 (직접입력/경로파일) | `test_cycle_analysis.py` | ~21+19 | ✅ 양호 |
| 프로필 분석 | `test_profile_analysis.py`, `test_profile_accuracy.py` | ~30+ | ✅ 양호 |
| 사이클 데이터 로딩 | `test_cycle_data_loading.py` | ~10 | ✅ 기본 |
| 논리 사이클 매핑 | `test_logical_cycle.py` | ~8 | ✅ 기본 |
| SCH 파서 | `test_sch_parser.py` | ~6 | ✅ 기본 |
| PNE 복원 | `test_pne_restore.py` | ~5 | ✅ 기본 |
| 사이클 탭 자동화 | `test_cycle_tab_automation.py` | ~15 | ✅ 양호 |
| GUI 스모크 | `test_smoke_gui.py` | ~19 | ✅ 기본 |

### 1.2 테스트 갭 (미커버 영역)

| 영역 | 위험도 | 설명 |
|------|--------|------|
| **DCIR 계산 로직** | 🔴 높음 | `pne_dcir_chk_cycle()`, `pne_dcir_Profile_data()` 전무 |
| **PyBaMM 시뮬레이션** | 🔴 높음 | `run_pybamm_simulation()`, 파라미터 변환, 플롯 전무 |
| **배터리 과학 검증** | 🔴 높음 | 물리량 범위, 단위 변환, 열화 모드 분류 검증 없음 |
| **사이클 매핑 엣지케이스** | 🟡 중간 | `_logical_to_totl_str()` 경계값/빈값 테스트 부족 |
| **그래프 출력** | 🟡 중간 | `graph_output_cycle()` matplotlib 렌더링 무검증 |
| **에러 핸들링** | 🟡 중간 | 손상 파일, 빈 채널, 네트워크 단절 시나리오 |
| **성능 회귀** | 🟢 낮음 | 대용량 데이터(>1000cyc) 처리 시간 추적 없음 |

---

## 2. 테스팅 피라미드

```
        ╱  E2E (Level C)  ╲         3-5개, 느림, 전체 워크플로우
       ╱  통합 (Level B)     ╲       20-30개, GUI 포함
      ╱  유닛 (Level A)        ╲     100+개, 빠름, 헤드리스
     ╱  과학 검증 (Level S)       ╲   50+개, 물리 법칙 검증
```

### Level S: 배터리 과학 검증 (신규)

> 데이터 처리 로직이 전기화학 원리를 올바르게 따르는지 검증

- 단위 변환 정합성 (BDT ↔ PyBaMM SI)
- 물리적 범위 검증 (DCIR > 0, 0 ≤ SOC ≤ 1, 전압 한계)
- 쿨롱 효율 계산 규칙
- 열화 모드 분류 일관성
- dV/dQ 피크 위치의 물리적 유효성

### Level A: 유닛 테스트 (헤드리스)

> 개별 함수의 입출력 정확성, GUI 의존 없음

- 데이터 로딩/파싱 (Toyo, PNE)
- 사이클 분류 (`classify_pne_cycles`, `classify_toyo_cycles`)
- 용량/DCIR 계산 로직
- 경로 파싱, 사이클 매핑
- PyBaMM 파라미터 변환 (`_key_map` 적용)
- 유틸리티 함수 (`convert_steplist`, `same_add` 등)

### Level B: 통합/GUI 테스트

> PyQt6 위젯 상호작용, 실데이터 기반 워크플로우

- 버튼 클릭 → 탭 생성 → 결과 검증
- PyBaMM 탭: 모델 선택 → 파라미터 로드 → 시뮬 실행
- 세트 탭: 경로 입력 → 분석 → 그래프 출력

### Level C: E2E 테스트

> 사용자 시나리오 전체 재현

- 경로 파일 로드 → 사이클 분석 → 세트 비교 → 수명 예측
- PyBaMM: 프리셋 선택 → CC-CV 시뮬 → 6서브플롯 생성 확인

---

## 3. 신규 테스트 계획

### 3.1 Phase 1: 배터리 과학 검증 (`test_battery_science.py`)

**목적**: 리팩토링 시 과학적 정합성이 깨지지 않도록 보호

| 테스트 | 검증 내용 | 우선순위 |
|--------|----------|---------|
| `test_unit_conversion_key_map` | `_key_map` 스케일 정확성 (μm→m = 1e-6) | P0 |
| `test_temperature_conversion` | °C→K 변환 (+273.15 정확) | P0 |
| `test_dcir_physical_bounds` | DCIR 계산 결과 > 0 | P0 |
| `test_soc_bounds` | 0 ≤ SOC ≤ 1 범위 검증 | P0 |
| `test_coulombic_efficiency_range` | 0.5 < CE < 1.05 (정상 셀) | P0 |
| `test_capacity_ratio_monotonic` | 용량 비율 추세 (대체로 단조감소) | P1 |
| `test_voltage_chemistry_limits` | NMC: 2.5–4.35V 범위 내 | P1 |
| `test_dcir_soc_dependence` | SOC 극단에서 DCIR 높음 (U자형) | P2 |
| `test_energy_voltage_consistency` | E = ∫V·I dt 일관성 | P2 |

### 3.2 Phase 2: PyBaMM 시뮬레이션 (`test_pybamm_simulation.py`)

**목적**: 모델 선택, 파라미터 변환, 실험 정의 로직 검증

| 테스트 | 검증 내용 | 우선순위 |
|--------|----------|---------|
| `test_model_map_valid_keys` | "SPM", "SPMe", "DFN" 매핑 정확 | P0 |
| `test_invalid_model_raises` | 잘못된 모델명 → ValueError | P0 |
| `test_key_map_completeness` | `_key_map` 14개 항목 존재 + 단위 | P0 |
| `test_preset_load_all` | 7개 프리셋 로드 시 KeyError 없음 | P0 |
| `test_experiment_string_format` | PyBaMM 문자열 형식 정합성 | P1 |
| `test_cutoff_parsing` | "0.05C", "C/50", "600s", "10m" → 정확 변환 | P1 |
| `test_init_soc_by_mode` | charge→0.0, discharge→1.0 등 | P1 |
| `test_spm_simulation_runs` | SPM + Chen2020 기본 실행 → Solution 반환 | P1 |
| `test_safe_variable_extraction` | `_safe()` 2D→1D 변환 정확 | P1 |
| `test_empty_steps_raises` | 빈 스텝 리스트 → ValueError | P1 |

### 3.3 Phase 3: DCIR 함수 (`test_dcir_functions.py`)

**목적**: DCIR 계산 로직의 물리적 정확성

| 테스트 | 검증 내용 | 우선순위 |
|--------|----------|---------|
| `test_dcir_formula` | DCIR = ΔV / ΔI 계산 정확성 | P0 |
| `test_dcir_vs_dcir2` | DCIR(ss) ≥ DCIR(1s) (확산 포함) | P1 |
| `test_soc70_dcir_extraction` | SOC 70% 지점 DCIR 추출 정확 | P1 |
| `test_pne_dcir_chk_cycle` | DCIR 사이클 자동 감지 | P1 |
| `test_dcir_column_mapping` | NewData dcir ↔ DB cycle_summary 매핑 | P2 |

### 3.4 Phase 4: 리팩토링 안전망 (`test_refactoring_guards.py`)

**목적**: 22,000줄 모놀리식 코드 리팩토링 시 기존 기능 보호

| 테스트 | 검증 내용 | 우선순위 |
|--------|----------|---------|
| `test_newdata_contract` | NewData 필수 10개 컬럼 존재 + 타입 | P0 |
| `test_cycle_data_return_shape` | `[mincapacity, df]` 반환 구조 불변 | P0 |
| `test_check_cycler_contract` | `check_cycler()` → bool 반환 | P0 |
| `test_name_capacity_regex` | 폴더명에서 mAh 추출 정확 | P0 |
| `test_graph_output_cycle_axes` | 6개 축 모두 생성 확인 | P1 |
| `test_channel_meta_fields` | ChannelMeta 필수 필드 존재 | P1 |
| `test_unified_profile_result_shape` | UnifiedProfileResult 계약 | P1 |
| `test_convert_steplist_edge` | 빈 문자열, 역순, 중복 처리 | P1 |

---

## 4. 테스트 인프라 가이드

### 4.1 마커 체계

```ini
# pytest.ini 확장
markers =
    gui: GUI 필요 테스트 (pytest-qt, Windows)
    slow: 대용량 데이터 또는 오래 걸리는 테스트
    science: 배터리 과학 검증 테스트 (Level S)
    pybamm: PyBaMM 의존 테스트 (설치 필요)
```

### 4.2 실행 명령

```powershell
# 전체 (GUI 제외 기본)
pytest

# 과학 검증만
pytest -m science -v

# PyBaMM 테스트 (pybamm 설치 필요)
pytest -m pybamm -v

# 리팩토링 안전망 (빠른 회귀 테스트)
pytest -m "not gui and not slow and not pybamm" -v

# 특정 Phase만
pytest tests/test_battery_science.py -v
pytest tests/test_pybamm_simulation.py -v
```

### 4.3 픽스처 확장 계획

```python
# conftest.py에 추가할 픽스처

@pytest.fixture
def sample_newdata():
    """검증용 표준 NewData DataFrame"""
    # 물리적으로 유효한 100사이클 합성 데이터

@pytest.fixture
def pybamm_default_params():
    """Chen2020 기본 파라미터 딕셔너리"""

@pytest.fixture
def dcir_pulse_data():
    """HPPC 펄스 테스트 데이터"""
```

### 4.4 합성 데이터 전략

실제 사이클러 데이터에 의존하지 않는 테스트를 위해 합성 데이터 사용:

| 데이터 | 용도 | 생성 방법 |
|--------|------|----------|
| 표준 NewData | 컬럼 계약 검증 | 100행 × 10열 DataFrame, 물리 범위 내 랜덤 |
| 전압 프로필 | dV/dQ 계산 검증 | NMC 방전 커브 수학 근사 |
| DCIR 펄스 | DCIR 계산 검증 | V_rest=3.7V, ΔV=50mV, I=1A |
| PyBaMM 파라미터 | 단위 변환 검증 | `_key_map` 키별 한국어↔영어 쌍 |

---

## 5. 커버리지 목표

### Phase별 목표 (증분)

| Phase | 기간 | 신규 테스트 | 누적 커버리지 |
|-------|------|-----------|-------------|
| 현재 | — | 0 | ~35% (데이터 파싱 중심) |
| Phase 1 (과학 검증) | 1주 | +15-20 | ~45% |
| Phase 2 (PyBaMM) | 1주 | +15-20 | ~55% |
| Phase 3 (DCIR) | 1주 | +10 | ~60% |
| Phase 4 (리팩토링 가드) | 지속 | +10-15 | ~65% |

### 함수별 커버리지 우선순위

```
[필수] check_cycler, name_capacity, convert_steplist
       toyo_cycle_data, pne_cycle_data (반환 구조)
       _key_map 단위 변환, 온도 변환
       DCIR 계산 (ΔV/ΔI)

[권장] classify_pne_cycles, classify_toyo_cycles
       unified_profile_core, unified_profile_batch
       run_pybamm_simulation (SPM 기본)
       graph_output_cycle (축 생성 확인)

[선택] 패턴 수정 탭 함수들
       세트 탭 비교 로직
       수명 예측 피팅 (a·n^b + c·exp(d·(n-e)))
```

---

## 6. CI/CD 통합 계획

### 6.1 GitHub Actions 워크플로우

```yaml
# .github/workflows/test.yml
name: BDT Tests
on: [push, pull_request]
jobs:
  test-headless:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install pytest pandas numpy scipy matplotlib
      - run: pytest -m "not gui and not slow and not pybamm" -v

  test-pybamm:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install pytest pybamm pandas numpy
      - run: pytest -m "pybamm" -v
```

### 6.2 Pre-commit 훅

```bash
# 커밋 전 빠른 회귀 테스트 (과학 검증 + 계약 테스트)
pytest -m "science" --tb=short -q
```

---

## 7. 테스트 작성 규칙

### 7.1 네이밍 컨벤션

```python
# 파일: test_{영역}.py
# 클래스: Test{기능그룹}
# 함수: test_{동작}_{조건}_{기대결과}

class TestDCIRCalculation:
    def test_dcir_positive_for_valid_pulse(self): ...
    def test_dcir_raises_on_zero_current(self): ...
    def test_soc70_dcir_within_expected_range(self): ...
```

### 7.2 Assertion 패턴

```python
# 물리 범위 검증 — 백분위 기반 (아티팩트 허용)
dchg = nd["Dchg"].dropna()
assert dchg.quantile(0.01) >= 0.0
assert dchg.quantile(0.99) <= 1.2

# 단위 변환 정확성 — 상대 오차
assert abs(converted - expected) / expected < 1e-10

# 구조 계약 — 필수 컬럼
assert set(REQUIRED_COLS).issubset(df.columns)

# PyBaMM 결과 — 타입 체크
assert not isinstance(sol, pybamm.EmptySolution)
```

### 7.3 합성 데이터 헬퍼 (conftest.py 확장)

```python
def make_synthetic_newdata(n_cycles=100, degradation_rate=0.001):
    """물리적으로 유효한 합성 NewData 생성

    Parameters
    ----------
    n_cycles : int
        사이클 수
    degradation_rate : float
        사이클당 용량 감소율 (0.001 = 0.1%/cyc)
    """
    cycles = np.arange(1, n_cycles + 1)
    dchg = 1.0 - degradation_rate * np.sqrt(cycles) + np.random.normal(0, 0.002, n_cycles)
    chg = dchg / (0.995 + np.random.normal(0, 0.001, n_cycles))  # CE ~99.5%
    eff = dchg / chg
    return pd.DataFrame({
        "Cycle": cycles,
        "Dchg": np.clip(dchg, 0, 1.5),
        "Chg": np.clip(chg, 0, 1.5),
        "Eff": np.clip(eff, 0.5, 1.05),
        "Eff2": np.clip(eff * 1.001, 0.5, 1.05),
        "RndV": 4.15 - 0.0001 * cycles,
        "AvgV": 3.65 - 0.0002 * cycles,
        "DchgEng": dchg * 3.65,
        "Temp": 25.0 + np.random.normal(0, 0.5, n_cycles),
        "OriCyc": cycles,
    })
```

---

## 8. 기존 테스트 → 전략 매핑

| 기존 파일 | Level | 전략 Phase | 확장 방향 |
|-----------|-------|----------|----------|
| `test_path_parsing.py` | A | Phase 4 | 엣지케이스 추가 (빈 경로, 특수문자) |
| `test_cycle_analysis.py` | A | Phase 4 | 물리 범위 검증 강화 (Phase 1 연동) |
| `test_profile_analysis.py` | A | Phase 1 | dV/dQ 피크 물리 검증 추가 |
| `test_logical_cycle.py` | A | Phase 4 | 경계값 테스트 확대 |
| `test_smoke_gui.py` | B | — | PyBaMM 탭 스모크 추가 |

---

## 9. 참고

- 전체 프로젝트 규칙: `.github/instructions/project-rules.instructions.md`
- 배터리 과학 원리: `.github/instructions/battery-science.instructions.md`
- PyBaMM 규칙: `.github/instructions/pybamm.instructions.md`
- 기존 테스트 가이드: `tests/README.md`
