# DCIR / GITT 패턴 통합 분류 및 코드 매핑 분석

> 📎 2026-04-21: `260310_fix_soc70_dcir_condition.md`, `260405_fix_condition9_pulse_filter.md` 병합 (§8 SOC70 분기 수정, §9 Condition=9 CC 재분류)

> 작성일: 2026-06-20  
> 대상 파일: `DataTool_dev/DataTool_optRCD_proto_.py`  
> 분석 범위: 16개 .sch 데이터셋, 5개 DCIR 코드 경로

---

## 1. 배경 / 목적

DataTool의 사이클 분석에서 DCIR 계산은 **3개 라디오버튼(dcirchk / pulsedcir / mkdcir)** 에 의해 분기되고, 별도 **Profile DCIR(pne_dcir_chk_cycle → pne_dcir_Profile_data)** 경로도 존재한다.

현재 문제:
- `pne_dcir_chk_cycle`의 **`steptime==2000` 하드코딩** 때문에, 20s를 0.1+0.9+9+10s로 분할한 Type B DCIR 패턴을 검출하지 못함
- 각 데이터 유형에 어떤 코드 경로를 사용해야 하는지 기준이 명확하지 않음
- GITT 데이터는 DCIR이 아닌데 혼동 가능성 있음

**목표**: 모든 .sch 패턴을 체계적으로 분류하고, 각 패턴이 어떤 코드 경로에 매핑되는지 정리

---

## 2. .sch 패턴 통합 분류표

### 5개 패턴 유형

| Type | 이름 | 방전 펄스 | 충전 펄스 | SOC 포인트 | REST |
|:---:|------|:---:|:---:|:---:|:---:|
| **A** | SOC별 DCIR (Profile) | 20s × 4율 | 20s × 4율 (선택) | 10개 (SOC 100~5%) | 30min |
| **B** | Multi-rate split DCIR | (0.1+0.9+9+10)s × 1율 | 20s × 1율 (선택) | 10개 (SOC 100~5%) | 30min |
| **C** | GITT | 6min × 105~120 loops | 6min (선택) | N/A (연속) | 1hr |
| **D** | Rss 수명 (방전 only) | 1s × 1율 | 없음 | 4개 (SOC ~50/30/10/0%) | 31min |
| **E** | Rss 수명 (충+방전) | 1s × 1율 | 1s × 1율 | 3개 (SOC 30/50/70%) | 15min |

---

### Type A — SOC별 DCIR (Profile DCIR)

**대표 데이터셋**: Gen5+B Main/DoE, SOC별DCIR 15도, LWN 25P DCIR

```
스케줄 구조 (반복 단위):
  CHG 0.2C → REST 10min → DCHG 0.2C (기준 사이클)
  
  [SOC별 DCIR 블록 - 10개 SOC 포인트, 각 포인트별 4율]
  DCHG 0.2C [10%] → REST 30min →
    DCHG 0.2C   20s → REST ... → (0.2C 20s)
    DCHG 0.5C   20s → REST ... → (0.5C 20s)
    DCHG 1.0C   20s → REST ... → (1.0C 20s)
    DCHG 2.0C   20s → REST ... → (2.0C 20s)
    CHG  20s ... (역방향, 선택)
  → LOOP ×9~10 (SOC 포인트 수)

  CHG CCCV → DCHG → LOOP ×1 (다음 블록)
```

**펄스 특성**:
- 시간: **20s 단일 스텝**
- 전류: 다중 율 (0.2C, 0.5C, 1C, 2C)
- 방향: 충전+방전 또는 방전만
- CSV StepTime: **2000** (0.01s 단위)

---

### Type B — Multi-rate split DCIR

**대표 데이터셋**: Phase2 고온수명후/Fresh, PS/PA1 연속저장, POR 40C PA1/PA3

```
스케줄 구조 (반복 단위):
  CHG 0.2C → REST 10min → DCHG 0.2C (기준 사이클)
  
  [DCIR 블록]
  REST 30min →
    DCHG 1C  0.1s →     ← steptime = 10
    DCHG 1C  0.9s →     ← steptime = 90
    DCHG 1C  9.0s →     ← steptime = 900
    DCHG 1C 10.0s →     ← steptime = 1000
    CHG  1C 20.0s →     ← steptime = 2000 (단일!)
  → DCHG [10%] → LOOP ×9

  CCCV 충전 → DCHG → LOOP
```

**펄스 특성**:
- 시간: **4개 서브스텝 합 = 20s** (0.1 + 0.9 + 9 + 10)
- 전류: 단일 율 (1C)
- 방향: 방전은 분할, 충전은 단일 20s
- CSV StepTime: **10, 90, 900, 1000** (개별) — ❌ `2000` 단일 스텝 없음

---

### Type C — GITT

**대표 데이터셋**: A17 ATL GITT, A17 SDI GITT, Gen4pGr GITT

```
스케줄 구조:
  CHG_CCCV 0.1C  6min (또는 DCHG 0.1C  6min)
  REST      1hr
  → LOOP ×105~120
```

**펄스 특성**:
- 시간: **360s** (6min)
- 전류: 0.1C (극히 낮은 C-rate)
- REST: 1hr (평형 전압 도달 목적)
- **DCIR 분석 대상 아님** — 확산계수(D) 산출용

---

### Type D — Rss 수명 (방전 pulse only)

**대표 데이터셋**: Q8 ATL Main 2.0C Rss RT, Q8 ATL Sub 2.0C Rss RT

```
스케줄 구조 (반복 단위 — 5블록, 각 LOOP ×97~98):
  CHG 0.2C → REST 10min → DCHG 0.2C (기준 사이클)
  
  [RSS/1s Pulse DCIR 블록 — 4 SOC 포인트]
  DCHG 0.2C [30%] → DCHG 1C 1s → REST 31min   (SOC ~50%)
  DCHG 0.2C [20%] → DCHG 1C 1s → REST 31min   (SOC ~30%)
  DCHG 0.2C [20%] → DCHG 1C 1s → REST 31min   (SOC ~10%)
  DCHG 0.2C [15%] → DCHG 1C 1s → REST 1.5hr   (SOC ~0%)
  DCHG 0.2C → REST 10min (방전 잔량)
  
  CHG CCCV (2C→1.65C→1.4C→1C) → REST → DCHG 1C+0.5C → REST
  → LOOP ×97~98
```

**펄스 특성**:
- 시간: **1s 단일 스텝**
- 전류: 1C (2369/2485 mA)
- 방향: **방전만**
- CSV StepTime: **100** (0.01s 단위)
- REST: **186000** (31min), 최종 **540000** (1.5hr)
- 총 펄스: 24건 (4 SOC × 6블록)

---

### Type E — Rss 수명 (충+방전 pulse)

**대표 데이터셋**: A1_MP1 상온 (0-601, 600-1000, 1001-2000)

```
스케줄 구조 (반복 단위):
  CHG 0.2C → REST → DCHG 0.2C (기준 사이클)
  
  [충방전 SOC 체크 — 전류동일, 펄스 없음]
  CHG 0.2C [30%→20%→20%→full]
  DCHG 0.2C [30%→20%→20%→full]
  
  [충전 RSS/1s Pulse — 3 SOC 포인트]
  CHG 0.1C [30%] → CHG 1C 1s → REST 15min   (SOC ~30%)
  CHG 0.1C [20%] → CHG 1C 1s → REST 15min   (SOC ~50%)
  CHG 0.1C [20%] → CHG 1C 1s → REST 15min   (SOC ~70%)
  CHG 0.2C full → REST 10min
  
  [방전 RSS/1s Pulse — 3 SOC 포인트]
  DCHG 0.1C [30%] → DCHG 1C 1s → REST 15min   (SOC ~70%)
  DCHG 0.1C [20%] → DCHG 1C 1s → REST 15min   (SOC ~50%)
  DCHG 0.1C [20%] → DCHG 1C 1s → REST 15min   (SOC ~30%)
  DCHG 0.2C full → REST 10min
  
  CHG CCCV (2C→1.65C→1.4C→1C) → REST → DCHG 0.5C → REST
  → LOOP ×47~97
```

**펄스 특성**:
- 시간: **1s 단일 스텝**
- 전류: 1C (4500 mA)
- 방향: **충전 + 방전 모두**
- CSV StepTime: **100** (0.01s 단위)
- REST: **90000** (15min)
- 총 펄스: 충전 3~9건 + 방전 3~9건

---

## 3. 코드 경로 매핑

### 3.1 현재 코드 경로 (5개)

| 코드 경로 | UI 선택 | 진입 조건 | 계산 방식 |
|---|---|---|---|
| ① `chkir` 분기 | dcirchk 라디오 | `Condition==2, volmax>4100000` | `imp / 1000` |
| ② `mkdcir` 분기 | mkdcir 라디오 | `steptime==100` (1s pulse) | 벡터화 RSS/Pulse 계산 |
| ③ `else` 분기 | pulsedcir 라디오 | `Condition==2, steptime≤6000` | `imp / 1000` |
| ④ `pne_dcir_chk_cycle` | DCIR 버튼 | `steptime==2000` (20s) | 사이클 범위 반환 |
| ⑤ `pne_dcir_Profile_data` | DCIR 버튼 | `StepTime==20`, 4율 | linregress slope |

### 3.2 패턴 → 코드 매핑

| Type | 올바른 코드 경로 | 현재 상태 | 문제점 |
|:---:|---|:---:|---|
| **A** | ④→⑤ (Profile DCIR) | ✅ 정상 | — |
| **B** | ④→⑤ (Profile DCIR) | ⚠️ 부분 실패 | 방전 `steptime==2000` 미존재 → ④ 검출 실패 |
| **C** | 별도 처리 필요 | ➖ 대상 아님 | GITT ≠ DCIR |
| **D** | ② mkdcir | ✅ 정상 | `steptime==100` ✓, REST `186000` ✓ |
| **E** | ② mkdcir | ✅ 정상 | `steptime==100` ✓, REST `90000` ✓, 충+방전 ✓ |

---

## 4. 핵심 문제점

### 문제 1: Type B 방전 DCIR 검출 실패 (치명적)

**위치**: `pne_dcir_chk_cycle()` L4053

```python
# 현재 코드
filtered_df = df[(df['Condition'] == 2) & (df['EndState'] == 64) & (df['steptime'] == 2000)]
```

Type B 방전 스텝의 StepTime 값:
| 스텝 | 시간 | StepTime (0.01s) |
|---|---|---|
| DCHG 0.1s | 0.1초 | 10 |
| DCHG 0.9s | 0.9초 | 90 |
| DCHG 9.0s | 9.0초 | 900 |
| DCHG 10.0s | 10.0초 | 1000 |

→ **개별 스텝에 `2000`이 없음** → `filtered_df` 가 빈 DataFrame → 방전 DCIR 사이클 범위를 반환하지 못함

충전은 20s 단일 스텝(`steptime=2000`)이 있어 검출 가능.

**개선안**: 연속 DCHG 스텝시간 합산이 ~20s인 패턴도 검출하거나, steptime 하드코딩 대신 "짧은 시간(≤30s) DCIR pulse" 범용 기준 사용

### 문제 2: Type B Profile DCIR 시간축 불일치

**위치**: `pne_dcir_Profile_data()` L4098 부근

```python
dcir_time = [0.0, 0.3, 1.0, 10.0, 20.0]
```

Type B의 실제 시간 경계:
- **0.0s** → ✅ (펄스 시작 직전)
- **0.1s** → 첫 번째 서브스텝 종료  ← `0.3`과 불일치
- **1.0s** → ✅ (0.1+0.9s)
- **10.0s** → ✅ (0.1+0.9+9.0s)
- **20.0s** → ✅ (0.1+0.9+9.0+10.0s)

→ `dcir_time[1] = 0.3` 은 Type A(단일 20s) 기준. Type B에서는 `0.1`이 되어야 함.

### 문제 3: mkdcir REST 시간 확장 필요성

**위치**: `_process_pne_cycleraw()` L3437

```python
dcirtemp3 = Cycleraw.loc[
    (Cycleraw['steptime'].isin([90000, 180000, 186000, 546000]))
    ...
```

현재 허용값: 15min(90000), 30min(180000), 31min(186000), 91min(546000)

- Type D REST 31min → **186000** ✓
- Type E REST 15min → **90000** ✓
- Type D 마지막 REST 1.5hr = 5400s = **540000** ← `546000`과 미세 차이?

→ 현재는 정상 동작하지만, 새로운 스케줄이 추가되면 하드코딩 목록 확장 필요.
  **장기 개선안**: 하드코딩 대신 "Condition==3 + 일정 시간 이상(예: ≥15min)" 범용 기준

---

## 5. UI 라디오버튼 선택 가이드

| 데이터 유형 | 선택해야 할 라디오버튼 |
|---|---|
| Type A: SOC별 DCIR (20s, 다중 율) | **DCIR 버튼** (pne_dcir_chk_cycle → Profile) |
| Type B: Split DCIR (0.1+0.9+9+10s) | **DCIR 버튼** (⚠️ 방전 실패) 또는 **pulsedcir** (else 분기) |
| Type C: GITT | DCIR 분석 대상 아님 |
| Type D: Rss 수명 (방전 1s) | **mkdcir** 라디오 |
| Type E: Rss 수명 (충+방전 1s) | **mkdcir** 라디오 |

---

## 6. 영향 범위

| 함수 | 영향받는 Type | 수정 필요 |
|---|:---:|:---:|
| `pne_dcir_chk_cycle` (L4028) | B | ⚠️ steptime 검출 기준 |
| `pne_dcir_Profile_data` (L4063) | B | ⚠️ dcir_time 배열 |
| `_process_pne_cycleraw` mkdcir (L3427) | D, E | ✅ 정상 |
| `_process_pne_cycleraw` chkir (L3390) | — | ✅ 정상 |
| `_process_pne_cycleraw` else (L3553) | B? | 대안 경로 검토 |

---

## 7. 향후 개선 제안

### 단기 (현재 코드 최소 수정)
1. **Type B 방전 검출**: `pne_dcir_chk_cycle`에서 `steptime==2000` 외에 연속 DCHG 짧은 스텝 합산≈2000 패턴도 검사
2. **Type B dcir_time**: 검출된 패턴에 따라 `[0.0, 0.1, 1.0, 10.0, 20.0]` vs `[0.0, 0.3, 1.0, 10.0, 20.0]` 자동 선택

### 중기 (리팩토링)
3. **자동 패턴 인식**: .sch 파일 또는 Cycleraw에서 DCIR 패턴 타입(A/B/D/E)을 자동 판별하여 적절한 코드 경로로 라우팅
4. **REST 시간 범용화**: `dcirtemp3`의 steptime 하드코딩을 `Condition==3 & steptime >= threshold` 범용 기준으로 변경
5. **GITT 분류 경고**: GITT 데이터에 DCIR 분석을 시도하면 경고 메시지 표시

---

## 8. SOC70 분기 수정 (260310)

### 대상 파일 / 위치
- `DataTool_dev/DataTool_optRCD_proto_.py` (L1949)

### 변경 내용
```python
# Before
if (len(soc70_dcir) // 6)  > (len(df.NewData.index) // 100):

# After
if (len(soc70_dcir) // 6)  >= (len(df.NewData.index) // 100):
```

### 원인
- `same_add()` 후 DCIR 데이터 36개 → `36 // 6 = 6`
- 601 사이클 데이터 → `601 // 100 = 6`
- `6 > 6 = False` → else 분기(`[::4]`)로 잘못 진입
- else 분기는 4개 SOC 측정 패턴용이므로 6개 SOC 데이터에서 그룹 경계를 넘나들며 선택

### 증상
- SOC70 DCIR/RSS 그래프 사이클 인덱스가 `[3, 7, 105, 203, 207, 304, 402, 406, 504]`로 잘못 표시
- 100사이클 간격이 아닌 불규칙한 패턴

### 수정 후
- `6 >= 6 = True` → if 분기(`[3:][::6]`)로 정상 진입
- SOC70 인덱스: `[6, 106, 206, 305, 405, 505]` (≈100사이클 간격)

---

## 9. Condition=9 CC 재분류 (260405)

### 배경 / 목적

펄스 스윕(펄스+보충전, 방전), GITT, 스텝 충전 등의 데이터에서 `data_scope="charge"` 또는 `"discharge"`로 프로필을 출력할 때, 반대 방향의 CC 스텝 데이터가 섞여 들어가 프로필이 이상하게 출력되는 문제가 있었다.

**사이클(cycle) 모드에서는 정상 출력**되었는데, 충전/방전 단독 모드에서만 문제가 발생했다.

### 원인 분석

PNE 사이클러의 Condition 값 체계:
- `1` = CCCV 충전
- `2` = 방전
- `3` = 휴지
- **`9` = CC 전용 (충전/방전 구분 없음)**

기존 `_unified_filter_condition()` 로직:
```python
# 기존: Condition=9를 충전/방전 양쪽 필터에 모두 포함
charge   → [9, 1]   # ← CC 방전 펄스도 포함됨!
discharge → [9, 2]   # ← CC 충전 펄스도 포함됨!
```

펄스/GITT 패턴에서는 CC 충전 펄스와 CC 방전 펄스가 번갈아 나오는데, Condition=9만으로는 방향을 구분할 수 없어서 양쪽 데이터가 섞였다. 이후 `_unified_merge_steps()`가 이를 전부 같은 방향으로 취급하며 시간/용량을 누적하여 프로필이 깨졌다.

### Before / After 비교

**Before (기존)**
```python
def _unified_filter_condition(df, data_scope, include_rest):
    if data_scope == "charge":
        cond_values = [9, 1]       # CC(9)가 충전/방전 구분 없이 포함
    elif data_scope == "discharge":
        cond_values = [9, 2]       # 동일 문제
    elif data_scope == "cycle":
        cond_values = [9, 1, 2]
    ...
    return df.loc[df["Condition"].isin(cond_values)].copy()
```

**After (수정)**
```python
def _unified_filter_condition(df, data_scope, include_rest):
    df = df.copy()

    # --- Condition=9 재분류: 전류 부호 기반 ---
    if "Current_mA" in df.columns:
        cc_mask = df["Condition"] == 9
        if cc_mask.any():
            curr = df.loc[cc_mask, "Current_mA"]
            df.loc[cc_mask & (curr > 0).values, "Condition"] = 1   # CC 충전
            df.loc[cc_mask & (curr < 0).values, "Condition"] = 2   # CC 방전
            df.loc[cc_mask & (curr == 0).values, "Condition"] = 3  # 전류 0 → 휴지

    # --- 필터 적용 (이제 Condition=9가 없으므로 깔끔) ---
    if data_scope == "charge":
        cond_values = [1]       # 충전만
    elif data_scope == "discharge":
        cond_values = [2]       # 방전만
    elif data_scope == "cycle":
        cond_values = [1, 2]
    ...
```

### 수정 핵심 로직

`Current_mA` 부호(양수=충전, 음수=방전)를 기준으로 Condition=9를 사전 재분류:

| 조건 | 재분류 |
|------|--------|
| `Current_mA > 0` | Condition=1 (충전) |
| `Current_mA < 0` | Condition=2 (방전) |
| `Current_mA == 0` | Condition=3 (휴지) |

재분류 후에는 Condition=9가 더 이상 존재하지 않으므로, charge/discharge 필터가 정확하게 동작한다.

### 영향 범위

| 영향 | 범위 |
|------|------|
| 수정 함수 | `_unified_filter_condition()` (DataTool_optRCD_proto_.py) |
| 영향받는 데이터 | PNE 사이클러의 펄스, GITT, 스텝 충전, DCIR, 히스테리시스 데이터 |
| 영향받지 않는 것 | Toyo 데이터 (Condition=9 없음), cycle 모드 (전체 포함이므로 방향 구분 불필요) |
| 테스트 | 1834 passed, 0 failed, 118 skipped (전체 통과) |

### 부수 수정

- 파일 끝부분(`_pybamm_dchg_add_step` 함수)이 이전 세션에서 잘려있던 것을 HEAD 원본에서 복원 (302줄)
