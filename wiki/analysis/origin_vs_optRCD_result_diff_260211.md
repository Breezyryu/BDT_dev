# Origin vs optRCD 코드 변경에 따른 결과 차이 분석

> **작성일**: 2026-02-11  
> **비교 대상**:
> - Origin: `BatteryDataTool_origin/BatteryDataTool.py` (14,168줄)
> - optRCD: `BatteryDataTool_260206_edit copy/BatteryDataTool_optRCD.py` (15,275줄)

---

## 1. `smoothdegree` float → int 변환 (결과 달라짐)

### 영향 함수
- `pne_chg_Profile_data` / `pne_chg_Profile_batch`
- `pne_dchg_Profile_data` / `pne_dchg_Profile_batch`

### 발생 조건
- UI에서 `smoothdegree = 0`으로 설정 시 자동 계산 로직이 동작

### 변경 전 (Origin)
```python
# pne_chg_Profile_data (Origin L1407)
# pne_dchg_Profile_data (Origin L1465)
if smoothdegree == 0:
    smoothdegree = len(df.Profile) / 30   # ← Python3에서 float 반환 (예: 3.333...)
df.Profile["delvol"] = df.Profile["Voltage[V]"].diff(periods=smoothdegree)
df.Profile["delcap"] = df.Profile["Chgcap"].diff(periods=smoothdegree)
```
- Python3의 `/` 연산자는 항상 float 반환 → `diff(periods=3.333...)`
- 최신 pandas에서는 `periods`에 float 전달 시 **TypeError** 발생 가능
- 구버전 pandas에서는 내부적으로 int 변환되어 동작하지만, 명시적이지 않음

### 변경 후 (optRCD individual — L1856, L1911)
```python
if smoothdegree == 0:
    smoothdegree = int(len(df.Profile) / 30)   # ← 명시적 int 변환
df.Profile["delvol"] = df.Profile["Voltage[V]"].diff(periods=smoothdegree)
df.Profile["delcap"] = df.Profile["Chgcap"].diff(periods=smoothdegree)
```
- `int()` 변환으로 pandas 버전 호환성 확보
- 결과는 Origin 구버전 pandas와 동일

### 변경 후 (optRCD batch — L961, L1019)
```python
sd = smoothdegree if smoothdegree != 0 else max(int(len(df.Profile) / 30), 1)
df.Profile["delvol"] = df.Profile["Voltage[V]"].diff(periods=sd)
df.Profile["delcap"] = df.Profile["Chgcap"].diff(periods=sd)
```
- `max(..., 1)` 추가로 **최소 periods=1 보장**
- Profile 행이 30개 미만인 경우:
  - Origin/optRCD individual: `int(25 / 30) = 0` → `diff(periods=0)` → dQdV/dVdQ 모두 NaN/0
  - optRCD batch: `max(0, 1) = 1` → `diff(periods=1)` → **실제 차분값 계산됨**

### 결과 차이

| 조건 | Origin | optRCD individual | optRCD batch |
|---|---|---|---|
| Profile ≥ 30행 | 동일 (float이지만 동일 결과) | 동일 | 동일 |
| Profile < 30행 | dQdV/dVdQ = NaN/inf | dQdV/dVdQ = NaN/inf | **실제 차분값** |
| pandas 최신 | TypeError 가능 | 정상 | 정상 |

---

## 2. `self.dvscale` vs `dvscale` 혼용 버그 수정 (결과 달라짐)

### 영향 함수
- `dchg_confirm_button` 내 dVdQ 그래프 Y축 스케일 설정

### 발생 조건
- 방전 Profile (Dchg) 확인 버튼 클릭 시 항상 발생

### 변경 전 (Origin — L9715, L9807)
```python
# dchg_confirm_button 내 graph_profile 호출
graph_profile(Dchgtemp[1].Profile.SOC, Dchgtemp[1].Profile.dVdQ, Chg_ax4,
              0, 1.3, 0.1, -5 * dvscale, 0.5 * self.dvscale, 0.5 * self.dvscale,
              #                ↑ 로컬변수      ↑ 인스턴스변수       ↑ 인스턴스변수
              "DOD", "dVdQ", temp_lgnd)
```
- `dvscale`은 `Profile_ini_set()`에서 반환된 **로컬 변수**
- `self.dvscale`은 `chg_confirm_button()`에서만 설정됨 (L8116: `self.dvscale = self.dqscale`)
- **문제점**:
  1. `chg_confirm_button`을 먼저 실행하지 않으면 → `AttributeError: 'Ui_sitool' has no attribute 'dvscale'`
  2. 먼저 실행한 경우에도 이전 chg 설정값이 적용 → 현재 dchg 설정과 불일치
  3. 같은 `graph_profile` 호출에서 x_min은 `dvscale`, y_hlimit/y_gap은 `self.dvscale`로 **스케일 불일치**

### 변경 후 (optRCD — L10769)
```python
graph_profile(Dchgtemp[1].Profile.SOC, Dchgtemp[1].Profile.dVdQ, Chg_ax4,
              0, 1.3, 0.1, -5 * dvscale, 0.5 * dvscale, 0.5 * dvscale,
              #                ↑ 로컬변수       ↑ 로컬변수       ↑ 로컬변수
              "DOD", "dVdQ", temp_lgnd)
```
- 모든 인자가 로컬 변수 `dvscale` 통일
- `chg_confirm_button` 실행 여부와 무관하게 정상 동작

### 결과 차이

| 조건 | Origin | optRCD |
|---|---|---|
| chg 미실행 후 dchg 실행 | **AttributeError 크래시** | 정상 |
| chg 실행(scale=1) 후 dchg(scale=2) | x_min=-10, y_hlimit=0.5, y_gap=0.5 (불일치) | x_min=-10, y_hlimit=1.0, y_gap=1.0 (일치) |

---

## 3. `pne_search_cycle` index_min 빈 경우 처리 (결과 달라짐)

### 영향 함수
- PNE 데이터 로딩 전반 (`_pne_load_profile_raw` vs `pne_search_cycle` → `pne_data`)

### 발생 조건
- SaveEndData에 요청한 사이클의 **이전 사이클**이 없는 경우 (엣지 케이스)
- 예: 사이클 5를 요청했으나 SaveEndData에 사이클 4가 기록되지 않은 경우

### 변경 전 (Origin — pne_search_cycle L906~L909)
```python
if len(index_min) != 0:
    file_start = binary_search(index2, index_min[-1] + 1) - 1
    file_end = binary_search(index2, index_max[-1]) - 1
else:
    file_start = -1   # ← -1 반환
    file_end = -1
```
```python
# pne_data (Origin L874)
if os.path.isdir(rawdir) and (filepos[0] != -1):  # filepos[0] == -1 → 전체 스킵
    # 데이터 로딩...
```
- `file_start = -1` → `pne_data`에서 조건 불충족 → 데이터 **없음** (빈 DataFrame 반환)

### 변경 후 (optRCD batch — _pne_load_profile_raw L840~L843)
```python
if len(index_min) == 0:
    file_start = 0    # ← 0으로 설정 (첫 파일부터 탐색)
else:
    file_start = binary_search(file_index_list, index_min[-1] + 1) - 1
file_end = binary_search(file_index_list, index_max[-1]) - 1
if file_start < 0:
    file_start = 0
```
- `file_start = 0` → 첫 SaveData 파일부터 로딩 시도 → 데이터 **있음**

### 결과 차이

| 조건 | Origin | optRCD batch |
|---|---|---|
| 이전 사이클이 SaveEndData에 없음 | 데이터 누락 (빈 결과) | 데이터 로딩 성공 |
| 정상적인 경우 | 동일 | 동일 |

> **참고**: optRCD의 individual 함수(`pne_rate/chg/dchg_Profile_data`)는 여전히 `pne_data()` → `pne_search_cycle()` 경로를 사용하므로 Origin과 동일하게 동작. 차이는 **batch 함수 사용 시에만 발생**.

---

## 결과가 달라지지 않는 변경 (성능 최적화만)

| 변경 내용 | 위치 | 결과 영향 |
|---|---|---|
| `ThreadPoolExecutor` 병렬 데이터 로딩 | 모든 confirm_button | 없음 — 같은 데이터를 병렬로 읽을 뿐 |
| `_pne_load_profile_raw` SaveData 일괄 로딩 | PNE batch 함수 | 없음 — 같은 CSV를 한번에 읽고 메모리에서 필터링 |
| `pne_min_cap` / `toyo_min_cap` 1회 호출 | batch 함수 | 없음 — 같은 입력이면 같은 결과 |
| `check_cycler` cyclefolder당 1회 호출 | confirm_button | 없음 — 같은 폴더에 대해 항상 같은 판정 |
| `lru_cache` on `_load_pne_index_files` | PNE 관련 | 없음 — 같은 입력 → 같은 결과 (캐시) |
| `global writer` → 로컬 `writer` | confirm_button | 없음 — 쓰기 동작 동일 |
| `_init_confirm_button` / `_setup_file_writer` 등 헬퍼 | confirm_button | 없음 — 기존 로직을 함수로 추출 |
| `_create_plot_tab` / `_finalize_plot_tab` 헬퍼 | confirm_button | 없음 — UI 생성 로직 동일 |
| `_setup_legend` 헬퍼 | confirm_button | 없음 — legend 설정 동일 |
| `dQdV=0, dVdQ=0, delcap=0, delvol=0` 초기화 생략 (batch) | PNE chg/dchg batch | 없음 — `.diff()`가 즉시 덮어쓰므로 |
| `AllProfile` 모드 추가 | chg/dchg/rate/continue confirm | **새 기능** — 기존 동작에 영향 없음 |

---

## 종합 평가

| # | 변경 | 분류 | 실 영향도 |
|---|---|---|---|
| 1 | `smoothdegree` int 변환 | **버그 수정** | 낮음 (Profile < 30행인 경우만) |
| 2 | `self.dvscale` → `dvscale` | **버그 수정** | 높음 (dchg 단독 실행 시 크래시) |
| 3 | `index_min` 빈 경우 처리 | **버그 수정** | 낮음 (엣지 케이스, batch만) |

세 건 모두 **Origin의 버그가 optRCD에서 수정된 것**으로, 의도치 않은 결과 변경은 없습니다.
