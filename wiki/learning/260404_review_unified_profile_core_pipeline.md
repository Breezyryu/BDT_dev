# unified_profile_core() 파이프라인 설계 원리

## 대상 함수 / 클래스

- **파일**: `DataTool_dev/DataTool_optRCD_proto_.py`
- **위치**: 라인 606~ (기존 `_merge_step_profiles()` 직후)
- **함수**: `unified_profile_core()` 및 `_unified_*` 헬퍼 8개

---

## 1. 왜 통합이 필요했는가

기존에는 프로필 분석 버튼마다 별도 함수가 있었다:

```
pne_step_Profile_data()    → StepConfirm 전용
pne_rate_Profile_data()    → RateConfirm 전용
pne_chg_Profile_data()     → ChgConfirm 전용
pne_dchg_Profile_data()    → DchgConfirm 전용
pne_Profile_continue_data() → ContinueConfirm 전용
```

5개 함수의 처리 흐름을 비교하면:

```
[원시 로딩] → [Condition 필터] → [단위 정규화] → [스텝 병합] → [SOC 계산] → [가공]
```

이 6단계 중 **4단계(로딩, 정규화, 병합, SOC계산)가 거의 동일**했다.
차이는 Condition 필터 값(1 vs 2 vs 전체)과 후처리(dQdV 유무) 정도.

이 중복은 두 가지 문제를 일으킨다:
1. **수정 비용**: 단위 변환 버그를 고치려면 5곳을 동시에 수정해야 함
2. **확장 제한**: "휴지 포함" 같은 새 기능을 추가하면 5개 함수 모두 변경 필요

---

## 2. 파이프라인 6단계 상세 설명

### Stage 1: 원시 로딩 — 사이클러 추상화

```python
if is_pne:
    raw = _unified_pne_load_raw(path, start, end)
else:
    raw = _unified_toyo_load_raw(path, start, end)
```

**핵심 원리**: PNE와 Toyo는 데이터 형식이 완전히 다르다.
- PNE: 바이너리 CSV, 컬럼 인덱스 기반, μV/μA 단위
- Toyo: 텍스트 CSV, 컬럼명 기반, V/mA 단위, 사이클별 개별 파일

하지만 **출력은 동일한 표준 컬럼 구조**로 통일한다:

```
Condition(1/2/3), Voltage_raw, Current_raw, Temp_raw,
ChgCap_raw, DchgCap_raw, ChgWh_raw, DchgWh_raw,
Step, Cycle, CyclerType
```

이 "표준 중간 표현(Standard Intermediate Representation)"이 핵심이다.
Stage 2 이후는 사이클러 종류를 알 필요가 없다.

### Stage 2: Condition 필터링 — 옵션1 + 옵션4 매핑

```python
# PNE Condition 값의 의미:
# 1 = CCCV 충전
# 2 = 방전
# 3 = 휴지
# 9 = CC (충전 또는 방전의 CC 구간)
```

옵션 조합에 따라 필터할 Condition 값을 결정한다:

| data_scope | include_rest=False | include_rest=True |
|------------|-------------------|-------------------|
| charge     | [9, 1]            | [9, 1, 3]         |
| discharge  | [9, 2]            | [9, 2, 3]         |
| cycle      | [9, 1, 2]         | [9, 1, 2, 3]      |

**왜 9를 포함하는가?**
PNE에서 CC 충전과 CCCV 충전이 별도 Condition으로 기록된다.
CC 구간(9) 없이 CCCV(1)만 필터하면 CC-CV 전환 이전 데이터가 누락됨.

### Stage 3: 정규화 — 단위 변환의 핵심

PNE의 단위 체계가 복잡한 이유:

```
일반 PNE (PNE1~20):
  전압: 1,000,000 단위 (μV)
  전류: mincapacity × 1,000 으로 나눠서 C-rate 화
  시간: /100초 단위 → ÷100 → 초

PNE21/22 (코인셀):
  전류: mincapacity × 1,000,000 으로 나눠서 C-rate 화
  (용량이 μAh 단위이므로 divisor가 1000배 더 큼)
```

`is_micro_unit()` 함수가 경로에 "PNE21" 또는 "PNE22"가 있는지 체크해서 분기한다.

**Toyo는 단순하다**: 이미 V/mA/°C 단위이므로 변환이 거의 불필요.
단, Toyo는 용량을 직접 제공하지 않으므로 **시간적분으로 계산**해야 한다:

```python
# Toyo 용량 계산 (벡터화)
dt = np.diff(Time_s)                    # 시간 간격 (초)
current_a = Current_mA / 1000           # mA → A
cap_increment = |current_a| × dt / 3600 # A·s → Ah
ChgCap = cumsum(충전구간만)              # 정규화 (÷ mincapacity)
DchgCap = cumsum(방전구간만)
```

### Stage 4: 스텝 병합 — 시간/용량 연속성

PNE에서 하나의 사이클이 여러 스텝(Step 번호)으로 나뉘는 경우가 있다.
예: CC 충전(Step=1) → CV 충전(Step=2) → CC 방전(Step=3)

각 스텝의 시간과 용량이 0부터 시작하므로, 이어 붙일 때 **이전 스텝의 마지막 값을 더해줘야** 한다:

```python
# Step 1: Time 0~100s,  Cap 0~0.3
# Step 2: Time 0~50s,   Cap 0~0.1
# 병합 후:
# Step 1: Time 0~100s,  Cap 0~0.3
# Step 2: Time 100~150s, Cap 0.3~0.4  ← 누적
```

**cycle 모드에서는 병합하지 않는다**: 충전→휴지→방전이 이미 시간순으로 나열되어 있기 때문.

### Stage 5: X축 계산 — Time vs SOC

**Time 모드** (`axis_mode="time"`):
- `continuity="overlay"`: 각 사이클의 시작 시간을 0으로 리셋
- `continuity="continuous"`: 사이클 간 시간 연속 유지

**SOC 모드** (`axis_mode="soc"`):
- charge: SOC = ChgCap (0→1 방향)
- discharge: SOC = DchgCap (0→1, DOD 방향)
- cycle: SOC = ChgCap - DchgCap (양방향, 히스테리시스용)

```
SOC 모드에서 "사이클" 데이터의 형태:

충전 구간: SOC 0.0 → 0.95 (전압 상승)
휴지 구간: SOC 0.95 유지 (전압 하강 = 이완) → 수직선!
방전 구간: SOC 0.95 → 0.0 (전압 하강)
```

이것이 바로 **충방전 히스테리시스 플롯**이 된다.

### Stage 6: 파생값 — dQ/dV 계산

dQ/dV는 용량 변화량을 전압 변화량으로 나눈 값이다:

```python
dQdV = ΔQ / ΔV = (SOC 차분) / (Voltage 차분)
```

`smooth_degree`는 diff()의 periods 파라미터로, 노이즈 억제 역할을 한다.
0이면 `len(data) / 30`으로 자동 설정.

**휴지 구간 특별 처리**:
휴지에서는 전류=0이므로 ΔQ=0, ΔV≠0 → dQdV=0, dVdQ=∞가 된다.
이 값은 물리적 의미가 없으므로 NaN으로 처리한다.

---

## 3. 핵심 Python 문법/패턴

### dataclass (데이터 클래스)

```python
from dataclasses import dataclass, field

@dataclass
class UnifiedProfileResult:
    df: pd.DataFrame
    mincapacity: float
    columns: list = field(default_factory=list)  # 가변 기본값
    metadata: dict = field(default_factory=dict)
```

`@dataclass`는 `__init__`, `__repr__`을 자동 생성한다.
`field(default_factory=list)`는 **가변 객체를 기본값으로** 안전하게 사용하는 방법이다.
(리스트/딕셔너리를 직접 기본값으로 쓰면 모든 인스턴스가 같은 객체를 공유하는 버그 발생)

### numpy 벡터화 연산

```python
# 나쁜 예 (느림): for 루프
for i in range(len(df)):
    if df.iloc[i]["Condition"] == 2:
        cap[i] = abs(current[i]) * dt[i] / 3600

# 좋은 예 (빠름): 벡터화
dchg_mask = (df["Condition"].values == 2)
dchg_increments = np.where(dchg_mask, np.abs(current_a) * dt / 3600, 0)
DchgCap = np.cumsum(dchg_increments)
```

`np.where(조건, 참값, 거짓값)`은 마스크 기반 조건부 계산의 핵심이다.
10만 행 기준 for 루프 대비 **100배 이상 빠르다**.

### 키워드 전용 인자 (*)

```python
def unified_profile_core(
    raw_file_path: str,
    cycle_range: tuple[int, int],
    mincapacity: float,
    inirate: float,
    *,                          # ← 이 이후는 반드시 키워드로만 전달
    data_scope: str = "charge",
    axis_mode: str = "soc",
```

`*` 이후의 인자는 `unified_profile_core(path, (1,1), 100, 0.2, "charge")` 처럼
위치 인자로 전달할 수 없다. 반드시 `data_scope="charge"`로 명시해야 한다.
옵션이 많을 때 순서 혼동을 방지하는 Python 관용 패턴이다.

---

## 4. 기존 코드와의 관계

현재 단계에서는 기존 5개 함수를 **건드리지 않았다**.
`unified_profile_core()`는 독립적으로 존재하며, 같은 원시 데이터를 읽지만 별도 파이프라인을 탄다.

향후 Phase 4에서 UI 버튼을 통합할 때, 기존 함수 호출을 `unified_profile_core()` 호출로 교체하게 된다.
그 전에 Phase 2에서 **기존 함수 결과와 1:1 비교 검증**을 수행하여 정합성을 확인한다.
