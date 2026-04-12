# 260404 — `_profile_render_loop()` Strategy Pattern 리팩토링: 작동원리 및 학습 자료

**날짜**: 2026-04-04
**대상 함수**: `_profile_render_loop()`, `step_confirm_button()`, `rate_confirm_button()`, `chg_confirm_button()`, `dchg_confirm_button()`
**대상 파일**: `DataTool_dev/DataTool_optRCD_proto_.py`

---

## 1. 이 리팩토링을 왜 하는가?

### 문제 상황

사이클데이터 탭에는 6개의 프로필 분석 버튼이 있다. 각 버튼은 **서로 다른 데이터**(스텝 충전, Rate, 충전 프로필, 방전 프로필 등)를 그리지만, **그리는 방식(3-모드 루프)**은 동일하다.

```
CycProfile 모드:   채널마다 fig 1개 → 사이클을 오버레이
CellProfile 모드:  사이클마다 fig 1개 → 채널을 오버레이
AllProfile 모드:   fig 1개 → 모든 데이터를 오버레이
```

이 3-모드 분기 로직이 6개 버튼에 각각 200~280줄씩 **복사-붙여넣기**되어 있었다.

### 핵심 통찰

6개 버튼을 비교하면, 차이점은 **하나의 (채널, 사이클) 쌍에 대해 무엇을 그리느냐** 뿐이다.

| 공통 (변하지 않는 것) | 차이 (버튼마다 다른 것) |
|---------------------|---------------------|
| fig 생성, axes 배치 | 어떤 데이터를 어떤 축에 그리는가 |
| 3-모드 분기 (if/elif/else) | 어떤 포맷으로 Excel에 저장하는가 |
| 폴더/채널/사이클 3중 루프 | dQ/dV 토글 여부 |
| 프로그레스바 업데이트 | 범례 위치 |
| 채널맵 구성 (인터랙티브 범례) | axes 축 순서 (스텝은 3↔4 스왑) |
| 탭 마무리 + 이미지 저장 | |

---

## 2. Strategy Pattern이란?

### 개념

**Strategy Pattern**(전략 패턴)은 알고리즘의 골격을 고정하고, 알고리즘의 특정 단계만 교체 가능하게 만드는 디자인 패턴이다.

일반적인 형태:

```python
def algorithm(data, strategy_fn):
    """골격 — 변하지 않는 부분"""
    준비()
    for item in data:
        result = strategy_fn(item)  # ← 교체 가능한 전략
        후처리(result)
    마무리()
```

### BDT에서의 적용

```python
def _profile_render_loop(self, ..., plot_one_fn, fallback_fn, ...):
    """골격 — 3-모드 루프, fig 생성, 채널맵, 탭 마무리"""
    for folder in all_data_folder:
        for channel in subfolder:
            for cycle in CycleNo:
                temp = loaded_data.get(key) or fallback_fn(...)  # 전략 1: 데이터 로딩
                writecolno, artists = plot_one_fn(temp, axes, ...)  # 전략 2: 플롯
```

여기서:
- **골격** = `_profile_render_loop()` — 3-모드 분기, 프로그레스, 채널맵, 탭 생성
- **전략 1** (`fallback_fn`) = 캐시 미스 시 데이터 로딩 방법
- **전략 2** (`plot_one_fn`) = 하나의 데이터를 어떻게 그리고 저장하는가

---

## 3. Python 기법: 클로저(Closure)와 콜백(Callback)

### 클로저란?

함수 안에서 함수를 정의하면, 안쪽 함수는 바깥 함수의 변수를 "기억"한다.

```python
def chg_confirm_button(self):
    # 바깥 함수의 변수들
    dqscale = float(self.dqdvscale.text())  # dQ/dV 스케일
    dvscale = float(self.volrnggap.text())   # dV/dQ 스케일
    smoothdegree = int(self.smooth.text())   # 스무딩 차수
    use_dqdv = self.chk_dqdv.isChecked()     # dQ/dV 표시 토글

    def _chg_plot_one(temp, axes, headername, lgnd, temp_lgnd,
                      writer, save_file_name, writecolno, CycNo):
        # ↑ 이 안쪽 함수는 dqscale, dvscale, smoothdegree, use_dqdv를 "기억"
        return self.graph_profile(
            axes, temp[1].Profile, temp[0], headername, lgnd,
            dqscale, dvscale, smoothdegree, ...)
        #       ^^^^^^^ ^^^^^^^ ^^^^^^^^^^^
        #       바깥 함수에서 캡처한 변수들

    # 골격 함수에 콜백으로 전달
    self._profile_render_loop(plot_one_fn=_chg_plot_one, ...)
```

**왜 클로저를 쓰는가?**
- `_profile_render_loop()`는 `dqscale` 같은 버튼별 파라미터를 알 필요가 없다
- 각 버튼이 자기 파라미터를 클로저로 감싸서 전달 → 골격 함수는 범용으로 유지

### 콜백 계약 (Callback Contract)

`plot_one_fn`은 다음 **계약**을 지켜야 한다:

```python
def plot_one_fn(
    temp,           # (capacity, data_object, ...) — 원본 데이터 튜플 전체
    axes,           # (ax1, ax2, ax3, ax4, ax5, ax6) — 6개 subplot Axes
    headername,     # "폴더명, 채널명, Ncy, " — Excel 헤더용
    lgnd,           # "0001" — 범례 라벨
    temp_lgnd,      # "그룹명 0001" — 상세 범례 라벨
    writer,         # ExcelWriter 또는 None
    save_file_name, # 저장 경로 또는 None
    writecolno,     # 현재 Excel 열 번호
    CycNo,          # 사이클 번호 (int)
) -> tuple[int, list]:
    # 반환: (갱신된 writecolno, matplotlib artist 리스트)
```

**처음 설계에서 실수한 점**: `temp` 대신 `data_obj = getattr(temp[1], data_attr)`만 전달하려 했다.
하지만 `step_confirm_button`은 `temp[0]`(capacity)도 필요하고, `rate_confirm_button`은 `temp[0]`으로 `capacitytext`를 업데이트한다. 결국 **temp 튜플 전체**를 전달하는 것이 올바른 설계.

> **교훈**: 콜백의 입력을 너무 좁게 잡으면, 나중에 다른 버튼을 추가할 때 계약을 깨야 한다. 범용 인터페이스는 약간 넉넉하게 잡는 것이 유리하다.

---

## 4. `_profile_render_loop()` 작동 원리

### 전체 흐름도

```
_profile_render_loop() 시작
│
├─ axes_order 결정 (None → [0,1,3,2,4,5])
├─ 모드 판별: AllProfile? CycProfile? CellProfile?
│
├─ [AllProfile만] fig/axes 사전 생성 ─────────────────────────┐
│                                                             │
├─ for i, cyclefolder in enumerate(all_data_folder):          │
│   ├─ subfolder 스캔                                         │
│   ├─ is_pne = check_cycler(cyclefolder)                     │
│   │                                                         │
│   ├─ [CycProfile] ─────────────────────────────────────┐    │
│   │   for j, FolderBase in subfolder:                   │    │
│   │     fig/axes 생성 (채널당 1개)                        │    │
│   │     for CycNo in CycleNo:                           │    │
│   │       temp = cache.get() or fallback_fn()            │    │
│   │       writecolno, artists = plot_one_fn(temp, axes)  │    │
│   │       채널맵 업데이트                                  │    │
│   │     _setup_legend + _finalize_plot_tab               │    │
│   │     tab_no += 1                                      │    │
│   │                                                       │    │
│   ├─ [AllProfile] ─────────────────────────────────────┐  │    │
│   │   for j, FolderBase in subfolder:                   │  │    │
│   │     for CycNo in CycleNo:                           │  │    │
│   │       temp = cache.get() or fallback_fn()            │  │    │
│   │       writecolno, artists = plot_one_fn(temp, axes)  │  │    │
│   │       3레벨 채널맵 업데이트 (ch → sub → cyc)          │  │    │
│   │                                                       │  │    │
│   └─ [CellProfile] ───────────────────────────────────┐  │  │    │
│       for CycNo in CycleNo:                            │  │  │    │
│         fig/axes 생성 (사이클당 1개)                      │  │  │    │
│         for j, FolderBase in subfolder:                 │  │  │    │
│           temp = cache.get() or fallback_fn()            │  │  │    │
│           writecolno, artists = plot_one_fn(temp, axes)  │  │  │    │
│           채널맵 업데이트                                  │  │  │    │
│         _setup_legend + _finalize_plot_tab               │  │  │    │
│         tab_no += 1                                      │  │  │    │
│                                                           │  │  │    │
├─ [AllProfile] _setup_legend + _finalize_plot_tab ─────────┘──┘──┘────┘
├─ Excel writer 저장/닫기
└─ progressBar 100%
```

### 3-모드 차이점

| | CycProfile | CellProfile | AllProfile |
|---|-----------|-------------|------------|
| **fig 생성 시점** | 채널마다 | 사이클마다 | 루프 시작 전 1회 |
| **외부 루프** | 채널 | 사이클 | 채널 |
| **내부 루프** | 사이클 | 채널 | 사이클 |
| **탭 제목** | `폴더=채널` | `Ncy` | `All Data` |
| **채널맵** | 2레벨 (ch→cyc) | 2레벨 (ch→cyc) | 3레벨 (ch→sub→cyc) |

### axes_order가 필요한 이유

step 프로필의 2×3 subplot은 물리적으로 이런 배치이다:

```
ax[0]: Time-Voltage    ax[1]: Time-Current    ax[2]: Time-StepCapacity
ax[3]: Time-dQdV       ax[4]: Time-Temperature ax[5]: Time-Energy
```

그런데 step 프로필은 범례/마무리에서 **ax[3]과 ax[4]의 순서를 바꿔서** 처리한다:
```python
axes_list = [ax[0], ax[1], ax[3], ax[2], ax[4], ax[5]]  # 3↔2 스왑
```

반면 rate/chg/dchg는 자연 순서를 쓴다:
```python
axes_list = [ax[0], ax[1], ax[2], ax[3], ax[4], ax[5]]  # 자연 순서
```

이 차이를 `axes_order` 매개변수로 추상화:
- `None` (기본값) → `[0,1,3,2,4,5]` — step 스타일
- `[0,1,2,3,4,5]` — 자연 순서 (rate/chg/dchg)

---

## 5. 데이터 인풋 / 아웃풋

### 전체 데이터 파이프라인

```
[사용자 입력]          [병렬 로딩]           [_profile_render_loop]      [출력]
경로 테이블 ─┐
사이클 번호  ─┤   _load_all_*_parallel()   ┌─ plot_one_fn() ─────── matplotlib Figure
분석 옵션   ─┤   → ThreadPoolExecutor      │  └─ graph_step()         → 탭에 추가
C-rate      ─┘   → loaded_data dict        │  └─ graph_profile()      → 이미지 저장
                       │                    │  └─ _plot_and_save_      → Excel 저장
                       │                    │     step_data()          → CSV 저장
                       ▼                    │
                  loaded_data ──────────────┘
                  key: (folder_idx, channel_idx, cycle_no)
                  val: (capacity, DataObject, ...)
```

### 입력 데이터 구조

**loaded_data**: `dict[tuple[int, int, int], tuple]`

```python
loaded_data = {
    (0, 0, 100): (3450.2, <ProfileData>, ...),  # 폴더0, 채널0, 100사이클
    (0, 0, 200): (3428.1, <ProfileData>, ...),  # 폴더0, 채널0, 200사이클
    (0, 1, 100): (3445.0, <ProfileData>, ...),  # 폴더0, 채널1, 100사이클
    ...
}
```

각 튜플의 구조:
- `temp[0]` — capacity (float): 기준 용량값
- `temp[1]` — DataObject: 분석별 데이터 속성을 가진 객체
  - `.stepchg` — 스텝 충전 데이터 (step_confirm용)
  - `.rateProfile` — Rate 프로필 데이터 (rate_confirm용)
  - `.Profile` — 충방전 프로필 데이터 (chg/dchg_confirm용)

### 출력물

| 출력 | 형태 | 조건 |
|------|------|------|
| matplotlib Figure | cycle_tab에 QTabWidget 탭 추가 | 항상 |
| 인터랙티브 범례 | 클릭으로 채널/사이클 show/hide | 항상 |
| Excel (.xlsx) | 분석 데이터 컬럼별 저장 | `saveok` 체크 시 |
| CSV (.csv) | step 데이터 (step_confirm 전용) | `saveok` 체크 시 |
| 이미지 (.png) | fig 이미지 저장 | `figsaveok` 체크 시 |

---

## 6. 버튼별 콜백 상세 비교

### step_confirm_button → `_step_plot_one`

```python
def _step_plot_one(temp, axes, headername, lgnd, temp_lgnd,
                   writer, save_file_name, writecolno, CycNo):
    return self._plot_and_save_step_data(
        axes, temp[1].stepchg, temp[0],       # stepchg 데이터 + capacity
        headername, lgnd, temp_lgnd,
        writer, writecolno, save_file_name, CycNo,
        save_csv=True)                          # CSV 저장 활성화
```

**특징**:
- 기존 헬퍼 함수 `_plot_and_save_step_data()` 재사용
- 6개 subplot: 전압, 전류, 스텝용량, dQ/dV, 온도, 에너지
- `axes_order` = 기본값 `[0,1,3,2,4,5]` (ax3↔ax4 스왑)
- CSV 저장 별도 수행

### rate_confirm_button → `_rate_plot_one`

```python
def _rate_plot_one(temp, axes, headername, lgnd, temp_lgnd,
                   writer, save_file_name, writecolno, CycNo):
    self.capacitytext.setText(str(temp[0]))    # UI 용량 표시 업데이트
    graph_step(axes[0], temp[1].rateProfile, "Voltage", ...)     # ax1: 전압
    graph_step(axes[1], temp[1].rateProfile, "Crate", ...)       # ax2: C-rate
    graph_step(axes[2], temp[1].rateProfile, "SOC", ...)         # ax3: SOC
    graph_step(axes[3], temp[1].rateProfile, "Voltage", ...)     # ax4: 전압 (확대)
    graph_step(axes[4], temp[1].rateProfile, "Crate", ...)       # ax5: C-rate (확대)
    _artists = graph_step(axes[5], temp[1].rateProfile, "Temp", ...)  # ax6: 온도
    # Excel 저장: 5 columns (Time, Voltage, Current, Crate, Temperature)
    return (writecolno + 5, _artists)
```

**특징**:
- 6개 `graph_step()` 호출로 Rate 프로필의 6가지 관점 표시
- `axes_order = [0,1,2,3,4,5]` — 자연 순서
- `temp[0]`으로 `self.capacitytext` 업데이트 (Rate 분석의 고유 기능)

### chg_confirm_button → `_chg_plot_one`

```python
def _chg_plot_one(temp, axes, headername, lgnd, temp_lgnd,
                  writer, save_file_name, writecolno, CycNo):
    # ← 클로저: dqscale, dvscale, smoothdegree, use_dqdv 캡처
    _artists = self.graph_profile(
        axes, temp[1].Profile, temp[0], headername, lgnd,
        dqscale, dvscale, smoothdegree,
        chg=True, dqdv=use_dqdv,         # 충전 모드, dQ/dV 토글
        temp_lgnd=temp_lgnd, ...)
    # Excel 저장: 8 columns (Time, SOC, Energy, Voltage, Crate, dQdV, dVdQ, Temp)
    return (writecolno + 8, _artists)
```

**특징**:
- `chk_dqdv` 체크박스에 따라 dQ/dV 표시 방향 전환
  - 체크됨: X=Voltage, Y=dQ/dV
  - 미체크: X=dQ/dV, Y=Voltage
- X축이 SOC 기반 (`graph_profile`의 `chg=True` 옵션)
- 클로저로 `dqscale`, `dvscale`, `smoothdegree` 캡처

### dchg_confirm_button → `_dchg_plot_one`

```python
def _dchg_plot_one(temp, axes, headername, lgnd, temp_lgnd,
                   writer, save_file_name, writecolno, CycNo):
    # ← 클로저: dqscale, dvscale, smoothdegree 캡처
    _artists = self.graph_profile(
        axes, temp[1].Profile, temp[0], headername, lgnd,
        dqscale, dvscale, smoothdegree,
        chg=False,                         # 방전 모드
        temp_lgnd=temp_lgnd, ...)
    return (writecolno + 8, _artists)
```

**특징**:
- 방전 프로필이므로 X축이 DOD(방전심도) 기반
- dQ/dV 스케일이 **음수 방향**: `-5 * dqscale` ~ `0.5 * dqscale`
- dQ/dV 토글 없음 (충전과 다르게 항상 같은 방식)
- 범례 위치 다름: `["lower left", "upper left", ...]`

---

## 7. 인터랙티브 범례(채널맵) 구조

### 3레벨 계층

```
AllProfile 모드의 채널맵:

all_ch_map (레벨 1: 충방전기별)
├── "Toyo1" → {artists: [...], color: "#3C5488"}
└── "PNE3"  → {artists: [...], color: "#E64B35"}

all_sub_map (레벨 2: 채널별)
├── "Toyo1 CH01" → {artists: [...], color: "#3C5488", parent: "Toyo1"}
├── "Toyo1 CH02" → {artists: [...], color: "#00A087", parent: "Toyo1"}
└── "PNE3 CH05"  → {artists: [...], color: "#E64B35", parent: "PNE3"}

all_sub2_map (레벨 3: 사이클별)
├── "Toyo1 CH01 0100" → {artists: [...], color: "#3C5488", parent: "Toyo1 CH01"}
├── "Toyo1 CH01 0200" → {artists: [...], color: "#4DBBD5", parent: "Toyo1 CH01"}
└── ...
```

팝업 메뉴에서 레벨 1을 토글하면 하위 모든 artists가 show/hide된다.

### CycProfile/CellProfile은 2레벨

```
channel_map (레벨 1)
└── sub2_channel_map (레벨 2: 사이클별)
```

---

## 8. 핵심 Python 문법 정리

### 8.1 키워드 전용 인자 (`*`)

```python
def _profile_render_loop(self, *, loaded_data, all_data_folder, ...):
#                              ^
#                              이 * 뒤의 모든 인자는 반드시 이름을 지정해서 호출해야 함
```

```python
# 올바른 호출
self._profile_render_loop(loaded_data=data, all_data_folder=folders, ...)

# 오류 — 위치 인자로 전달 불가
self._profile_render_loop(data, folders, ...)  # TypeError!
```

**왜 쓰는가?** 매개변수가 12개나 되므로, 호출 시 이름을 강제하면 순서 실수를 방지한다.

### 8.2 `getattr(obj, attr_name)` — 동적 속성 접근

```python
data_attr = "stepchg"
value = getattr(temp[1], data_attr)  # = temp[1].stepchg
```

문자열로 속성명을 전달받아 접근. `_profile_render_loop()`가 어떤 속성을 체크할지 모르므로 동적으로 접근.

### 8.3 리스트 컴프리헨션으로 축 재배열

```python
axes_order = [0, 1, 3, 2, 4, 5]
axes_list = [axes[k] for k in axes_order]
# → [axes[0], axes[1], axes[3], axes[2], axes[4], axes[5]]
```

하드코딩 대신 인덱스 리스트를 매개변수로 받아 유연하게 재배열.

### 8.4 `dict.get(key)` — 안전한 딕셔너리 접근

```python
temp = loaded_data.get((i, j, CycNo))  # 없으면 None 반환
if temp is None:
    temp = fallback_fn(FolderBase, CycNo, is_pne)  # 폴백 로딩
```

`loaded_data[(i, j, CycNo)]`는 키가 없으면 `KeyError`를 발생시키지만, `.get()`은 `None`을 반환하여 안전하게 폴백 처리 가능.

---

## 9. 요약: 이 리팩토링에서 배울 점

1. **Strategy Pattern**: 변하는 부분(콜백)과 변하지 않는 부분(골격)을 분리하면, 코드 중복을 제거하면서도 각 버튼의 고유 로직은 보존할 수 있다.

2. **클로저**: Python에서 콜백 함수가 외부 변수를 기억하는 메커니즘. 각 버튼의 UI 입력값(dqscale 등)을 골격 함수에 전달하지 않고도 콜백 안에서 사용할 수 있다.

3. **콜백 계약 설계**: 처음부터 넉넉한 인터페이스를 설계하는 것이 중요하다. `temp` 전체를 전달하면 각 콜백이 자유롭게 필요한 데이터를 꺼내 쓸 수 있다.

4. **매개변수화**: `axes_order` 같은 사소한 차이도 매개변수로 추상화하면, 하나의 골격이 여러 변형을 지원할 수 있다.

5. **코드량 감소의 본질**: 1,025줄 → 445줄은 단순한 압축이 아니라, **"진짜 다른 부분"만 남기고 "같은 부분"을 한 곳에 모은 것**이다. 버그 수정이나 새 기능 추가 시 한 곳만 고치면 된다.
