# 사이클분석 · 프로파일분석 통합 리빌딩 — 동작 로직 상세 리뷰

> **작성일**: 2026-04-06
> **대상 파일**: `DataTool_dev/DataTool_optRCD_proto_.py` (25,382줄)
> **범위**: 논리사이클 정의(cycle_map), 사이클 요약 통계, 프로파일 파싱 엔진 통합

---

## 1. 리빌딩 배경 — 왜 통합했는가

### 기존 구조의 문제

사이클분석과 프로파일분석이 **각각 독립적으로** 사이클러 판별, 용량 산정, 파일 로딩을 수행하고 있었다.

**기존 프로파일 분석** — 5개 독립 함수:

| 함수 | 역할 | 문제 |
|------|------|------|
| `step_confirm_button()` | 스텝별 프로파일 (충전, Time축) | 각 함수가 |
| `rate_confirm_button()` | 율별 프로파일 | PNE/Toyo 분기를 |
| `chg_confirm_button()` | 충전 프로파일 (SOC축, dQ/dV) | 내부적으로 |
| `dchg_confirm_button()` | 방전 프로파일 (SOC축, dQ/dV) | 개별 구현 → |
| `continue_confirm_button()` | 연속 프로파일 | **코드 중복 60%+** |

**기존 사이클 분석** — 사이클러별 독립 파이프라인:

```
toyo_cycle_data() → Toyo 전용 로직 → df.NewData
pne_cycle_data()  → PNE 전용 로직  → df.NewData
```

두 분석 모두 **"논리사이클"이라는 공통 개념**이 필요한데, 각각 별도로 정의하고 있어서 사이클 분석에서 정의한 논리사이클 번호와 프로파일 분석에서 사용하는 사이클 번호가 불일치할 수 있었다.

### 통합 핵심 아이디어

**cycle_map** — 논리사이클 ↔ 물리사이클 매핑 딕셔너리를 한 번 빌드하여, 사이클분석과 프로파일분석이 **동일한 사이클 정의를 공유**하도록 한다.

```
cycle_map = {
    1: (1, 5),      # 논리사이클 1 = 물리파일 1~5
    2: (6, 10),     # 논리사이클 2 = 물리파일 6~10
    3: 11,          # 논리사이클 3 = TotlCycle 11
}
```

---

## 2. 통합 후 전체 아키텍처

```
┌── UI 레이어 ──────────────────────────────────────────────────┐
│                                                                │
│  [사이클분석] unified_cyc_confirm_button()                     │
│       │                                                        │
│  [프로파일분석] unified_profile_confirm_button()                │
│       │           └─ _read_profile_options() → 옵션 4개         │
│       │                                                        │
└───────┼────────────────────────────────────────────────────────┘
        │
        ▼
┌── 공유 인프라 ─────────────────────────────────────────────────┐
│                                                                │
│  check_cycler()     → PNE / Toyo 판별                          │
│  name_capacity()    → 파일명에서 용량(mAh) 추출                │
│  pne_min_cap()      → PNE 용량 자동 산정                       │
│  toyo_min_cap()     → Toyo 용량 자동 산정                      │
│                                                                │
│  ┌── cycle_map 빌더 (핵심 공유 자산) ──────────────────┐       │
│  │  pne_build_cycle_map()      → 일반/스윕 자동 판별   │       │
│  │  toyo_build_cycle_map()     → 방전 기반 사이클 그룹  │       │
│  │  _pne_build_sweep_cycle_map() → GITT/펄스 전용      │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                │
└────────────────────────────────────────────────────────────────┘
        │                             │
        ▼                             ▼
┌── 사이클분석 ──────────┐  ┌── 프로파일분석 ──────────────────┐
│                        │  │                                  │
│ toyo_cycle_data()      │  │ unified_profile_core()  ← 6단계 │
│ pne_cycle_data()       │  │ unified_profile_batch()          │
│                        │  │ unified_profile_batch_continue() │
│ → df.NewData           │  │ → UnifiedProfileResult           │
│   (요약 통계 테이블)    │  │   (프로파일 DataFrame)           │
│                        │  │                                  │
└────────────────────────┘  └──────────────────────────────────┘
```

---

## 3. 사이클러 판별과 용량 산정

### 3.1 check_cycler() — PNE vs Toyo 판별

```python
def check_cycler(raw_file_path) -> bool:  # True=PNE, False=Toyo
```

**판별 우선순위:**

| 순서 | 조건 | 결과 | 근거 |
|------|------|------|------|
| 1 | `raw_file_path\Pattern\` 폴더 존재 | PNE | PNE만 스케줄 기반 패턴 폴더 생성 |
| 2 | `Restore\` 내 "SaveData" 포함 파일 존재 | PNE | GITT 등 Pattern 없는 PNE 모드 |
| 3 | 위 모두 불충족 | Toyo | 기본값 |

**왜 이 순서인가:** PNE 사이클러는 반드시 `Pattern/` 폴더를 생성한다 (스케줄 파일 저장). 예외적으로 GITT 등 수동 모드에서는 Pattern이 없지만 `Restore/SaveData*.csv`는 존재한다. Toyo는 CSV 파일만 생성하고 이 두 폴더 구조를 쓰지 않는다.

### 3.2 name_capacity() — 파일명에서 용량 추출

```python
def name_capacity(data_file_path) -> float:  # mAh 또는 0
```

경로 문자열에서 `(\d+([\-.]\d+)?)mAh` 정규식으로 용량 추출.

**예시:**
- `Q8_5000mAh_RT_수명` → `5000.0`
- `CosmX_1.5mAh_half` → `1.5`
- `2026_rate_test` → `0` (mAh 패턴 없음 → 후속 함수에서 자동 산정)

### 3.3 용량 자동 산정 (mincapacity == 0일 때)

**PNE (`pne_min_cap`):**
1. 파일명에 "mAh" 포함 → `name_capacity()`로 추출
2. 없으면 → `SaveData0001.csv` 1행 9열(전류값) 읽기 → `abs(전류/1000) / ini_crate`
3. 캐시 저장 후 반환

**Toyo (`toyo_min_cap`):**
1. 파일명에서 추출 시도
2. 없으면 → 첫 사이클 CSV의 최대 전류 / ini_crate
3. 캐시 저장 후 반환

**자동 산정의 물리적 근거:** 첫 사이클의 CC 충전 전류 = 용량 × C-rate. 따라서 `용량 = 전류 / C-rate`. 예: 1C 충전에서 5A 전류 → 용량 = 5000mAh.

---

## 4. 논리사이클 정의 — cycle_map 빌드

### 4.1 "논리사이클"이란

배터리 시험에서 **물리적으로 기록되는 사이클 번호**(TotlCycle, 파일번호)와 **시험자가 의미하는 사이클 번호**는 다를 수 있다.

**예: 100회 가속수명 시험**

```
물리:  TC1(CC충전) → TC2(CV유지) → TC3(방전) → TC4(휴지) → TC5(CC충전) → ...
논리:  ───── 논리사이클 1 ──────────────────   ── 논리사이클 2 ─→ ...
```

**예: GITT (갈바노스태틱 간헐 적정)**

```
물리:  TC1(방전 10s) → TC2(휴지 1h) → TC3(방전 10s) → TC4(휴지 1h) → ... → TC20
논리:  ──────────────── 논리사이클 1 (스윕) ────────────────────────────────
```

### 4.2 Toyo cycle_map 빌드 (`toyo_build_cycle_map`)

```
입력: capacity.log (사이클 요약), mincapacity, ptn_struct (패턴 힌트)
출력: {논리사이클: (시작파일번호, 끝파일번호)}
```

**알고리즘 (5단계):**

**① 연속 동일 Condition 병합** — 연속된 동일 Condition(충전, 방전) 행을 하나로 묶는다.
- 다단 CC 충전(1C→2C→3C)이 별도 행으로 기록되는 것을 하나의 충전 이벤트로 통합
- 용량은 합산, 전압은 최대값, 온도는 마지막값 유지

**② 방전 임계값 결정** — "유의미한 방전"의 기준 설정
- 기본: mincapacity / 60 (공칭의 1.67%)
- GITT/펄스: ptn_struct의 min_pulse_cap_mAh × 0.5

**③ Pass 1: 방전 기반 사이클 그룹핑** — 유의미한 방전을 발견하면:
- 직전 충전 포함 (있으면)
- 이후 휴지/기타 포함 (있으면)
- → 1 논리사이클

**④ Pass 2: 충전 전용 사이클** — 사용되지 않은 충전 그룹을 독립 사이클로 등록
- 화성(Formation) 테스트에서 충전만 수행하는 경우 해당

**⑤ 정렬 → 순번 부여** — 시작 파일번호 기준 정렬, 논리사이클 1, 2, 3... 부여

**결과 형식:**
```python
{1: (1, 3), 2: (4, 7), 3: (8, 8)}
# 논리사이클 1 = 파일 1~3, 논리사이클 2 = 파일 4~7, ...
```

### 4.3 PNE cycle_map 빌드 (`pne_build_cycle_map`)

```
입력: SaveEndData (사이클 종료 요약), mincapacity, .sch 스케줄 힌트
출력: {논리사이클: TotlCycle} 또는 {논리사이클: (시작TC, 끝TC)}
```

PNE는 **시험 유형을 자동 판별**한 후 분기한다.

**자동 판별 기준:**

| 조건 | 판정 | 예시 |
|------|------|------|
| 유의미 TC 비율 ≥ 50% **AND** 충방전 쌍 ≥ 30% | **일반 모드** | 수명시험, 율별방전 |
| 위 기준 미달 | **스윕 모드** | GITT, DCIR, 펄스 |
| TC 5개 이하 | **일반 모드 강제** | 소규모 시험 |
| .sch 파일에 sweep_mode 지정 | **.sch 우선** | 스케줄 힌트 |

**유의미 TC** = max(ChgCap, DchgCap) ≥ 공칭의 20%

#### 일반 모드 cycle_map

- 충방전 쌍이 있는 TC → 1:1 논리사이클
- 충전만 있는 TC → 독립 논리사이클
- 연속 비유의미 TC → 하나의 스윕 그룹으로 묶기

```python
# 결과 예시 (수명시험)
{1: 1, 2: 2, 3: 3, ..., 100: 100}  # TC와 논리사이클이 1:1
```

#### 스윕 모드 cycle_map (`_pne_build_sweep_cycle_map`)

GITT, 펄스, DCIR 등 다수의 작은 TC가 하나의 논리사이클을 구성하는 경우.

**4단계 알고리즘:**

**① TC 분류** — 각 TC를 유의미/펄스로 분류하고, 방향(CHG/DCHG/MIXED) 결정
- 임계값: 최대 TC 용량의 50% (절대값 아닌 상대값 사용)

**② 세그먼트 생성** — 유의미 TC는 개별 세그먼트, 연속 펄스는 하나의 스윕 세그먼트

**③ 흡수(Absorption)** — 유의미 TC(충방전 쌍) 뒤에 오는 비유의미 DCHG 스윕을 흡수
- 물리적 근거: RPT 직후 GITT 방전 스윕이 오는 패턴에서, RPT+스윕을 하나의 논리사이클로 묶음

**④ 반대 방향 스윕 쌍 병합** — 연속된 CHG 스윕과 DCHG 스윕을 하나의 논리사이클로 합산
- 물리적 근거: 충전 GITT + 방전 GITT = 1회 완전 GITT 측정

```python
# 결과 예시 (GITT 20펄스)
{1: (1, 20)}  # 논리사이클 1 = TC 1~20 전체가 하나의 스윕
```

---

## 5. 사이클분석 — 요약 통계 테이블(df.NewData) 생성

### 5.1 Toyo 데이터 플로우

```
capacity.log → toyo_cycle_import()
     │
     ├─ Condition 병합 (연속 동일 Condition → 하나의 이벤트)
     ├─ 충전 데이터 추출 (Condition==1, Cap > 임계값)
     ├─ 방전 데이터 추출 (Condition==2, Cap > 임계값)
     ├─ DCIR 계산 (개별 원시 파일에서 V-drop / I 계산)
     ├─ 효율 계산 (Eff = Dchg/Chg, Eff2 = Chg(n+1)/Dchg(n))
     └─ cycle_map 적용 → 논리사이클 번호 부여
         │
         ▼
     df.NewData (요약 통계 테이블)
```

**Toyo 특이사항:**
- `capacity.log`에 사이클 요약이 있어 개별 파일을 읽지 않고도 요약 가능
- Condition 병합 핵심 로직: `cumsum( (Condition ≠ shifted) | ~Condition.isin([1,2]) )` — 동일 Condition 연속 구간을 하나의 그룹으로 묶음
- 효율 계산 시 위치 기반 매칭(position-based, not TC-based) — 인덱스 불일치 문제 방지

### 5.2 PNE 데이터 플로우

```
Restore/SaveData*.csv (또는 .cyc 실시간 데이터)
     │
     ├─ SaveEndData 13개 컬럼 추출 (TC, Condition, ChgCap, DchgCap, ...)
     ├─ .cyc 보충 (CSV에 없는 최신 사이클 추가)
     ├─ 코인셀 단위 변환 (필요시 /1000)
     ├─ DCIR 계산 (3가지 모드: 일반/MK/기본)
     ├─ 피벗 테이블 (index=TC, columns=Condition)
     ├─ 효율/전압 계산
     └─ cycle_map 적용 + 스윕 집계 (max 용량, mean 전압/DCIR)
         │
         ▼
     df.NewData (요약 통계 테이블)
```

**PNE 특이사항:**
- SaveEndData에 사이클 완료 시점의 요약값이 기록됨 (Toyo의 capacity.log에 해당)
- `.cyc` 파일은 실시간 기록용 바이너리 → CSV 보충 방식으로 최신 데이터 추가
- DCIR 3모드: (1) 일반(imp 컬럼 직접 사용), (2) MK(EndState==78 마커 기반 Rss+1s), (3) 기본(steptime ≤ 6000s 조건)

### 5.3 df.NewData 컬럼 정의

| 컬럼 | 의미 | 계산식 | 물리적 해석 |
|------|------|--------|------------|
| Cycle | 논리사이클 번호 | cycle_map 기반 | 시험자 관점의 반복 횟수 |
| Dchg | 방전 용량 비율 | DchgCap / mincapacity | 1.0 = 공칭 100% |
| Chg | 충전 용량 비율 | ChgCap / mincapacity | |
| RndV | 휴지 종료 전압 | min(Ocv, Condition==3) | OCV 근사값 (충전 후) |
| Eff | 쿨롱 효율 | Dchg / Chg | 99.5~99.99% 정상 |
| Eff2 | 교차 효율 | Chg(n+1) / Dchg(n) | 사이클 간 리튬 균형 |
| Temp | 최대 온도 | max(Temp, Condition==2) | 방전 중 발열 |
| AvgV | 평균 방전 전압 | DchgEng / Dchg | 저항 증가 시 하락 |
| DchgEng | 방전 에너지 | ∑(V×I×dt) | Wh 단위 |
| dcir | DC 내부저항 | ΔV / ΔI | mΩ 단위 |
| OriCyc | 원래 TC 번호 | TotlCycle 원본 | cycle_map 역추적용 |

---

## 6. 프로파일분석 — unified_profile_core 6단계 파이프라인

### 6.1 파이프라인 전체 흐름

```
┌─ Stage 1: 원시 로딩 ────────────────────────────────────────────┐
│ check_cycler() → PNE/Toyo 판별                                  │
│ cycle_map 자동 생성 (None이면)                                   │
│ _unified_pne_load_raw() 또는 _unified_toyo_load_raw()           │
│ 출력: Condition, Voltage_raw, Current_raw, Cap_raw, Temp_raw,   │
│       Time_s, Cycle, Step                                       │
└─────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─ Stage 2: Condition 필터링 ─────────────────────────────────────┐
│ _unified_filter_condition()                                     │
│ ① Condition=9(CC) → 전류 부호 기반 재분류 (1=충전, 2=방전)       │
│ ② data_scope에 따라 Condition 필터                              │
│    charge → [1], discharge → [2], cycle → [1,2]                 │
│ ③ include_rest=True면 Condition=3 추가 포함                     │
└─────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─ Stage 3: 단위 정규화 ─────────────────────────────────────────┐
│ _unified_normalize_pne() 또는 _unified_normalize_toyo()         │
│ PNE: μV→V, μA→mA, μAh→정규화(0~1), mK→°C, /100s→s            │
│ Toyo: V→V, mA→mA, 전류적분→정규화(0~1), °C→°C                  │
│ 출력: Time_s, Voltage, Current_mA, Crate, ChgCap, DchgCap,     │
│       ChgWh, DchgWh, Temp                                      │
└─────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─ Stage 4: 스텝 병합 ───────────────────────────────────────────┐
│ _unified_merge_steps()                                          │
│ cycle → 시간순 정렬만 (병합 없음)                                │
│ charge/discharge → 스텝 간 Time_s + Cap 누적 오프셋 적용         │
│   Step1(0~100s, 0~0.3) + Step2(0~50s, 0~0.2)                   │
│   → Step1 그대로 + Step2(100~150s, 0.3~0.5)                     │
└─────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─ Stage 5: X축 및 SOC 계산 ─────────────────────────────────────┐
│ _unified_calculate_axis()                                       │
│                                                                 │
│ [오버레이 모드]                                                  │
│   cycle: (사이클,Condition)별 시간 리셋 + NaN 행 삽입            │
│   charge/discharge: 사이클별 시간 리셋                           │
│                                                                 │
│ [이어서 모드]                                                    │
│   전체 시작점만 0으로 보정, 사이클 간 시간 유지                    │
│                                                                 │
│ SOC 계산:                                                       │
│   charge → SOC = ChgCap (0→1)                                   │
│   discharge → SOC = DchgCap (0→1, DOD 방향)                     │
│   cycle → SOC = ChgCap - DchgCap (양방향)                       │
│                                                                 │
│ TimeMin = Time_s / 60                                           │
└─────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─ Stage 6: 파생값 계산 (선택) ──────────────────────────────────┐
│ if calc_dqdv: _unified_calculate_dqdv()                         │
│   dQdV = ΔQ / ΔV  (smooth_degree 간격으로 차분)                 │
│   dVdQ = ΔV / ΔQ  (역수)                                       │
│   휴지 구간(Condition==3)은 NaN 처리                             │
│                                                                 │
│ Energy 컬럼 추가:                                               │
│   charge → ChgWh, discharge → DchgWh, cycle → ChgWh - DchgWh   │
└─────────────────────────────────────────────────────────────────┘
                    │
                    ▼
          UnifiedProfileResult
          (df, mincapacity, columns, metadata)
```

### 6.2 Stage별 상세 설명

#### Stage 1: 원시 로딩

**PNE (`_unified_pne_load_raw`)**
- `Restore/SaveData*.csv` 파일들을 읽어 연결
- cycle_map이 있으면 논리사이클 범위 → TotlCycle 집합으로 변환 후 해당 행만 로드
- 바이너리 인코딩: 컬럼 인덱스 기반 (0=Index, 2=Condition, 8=Voltage_raw(μV), 9=Current_raw(μA), ...)
- 스윕 사이클(tuple): `(start_TC, end_TC)` → 범위 내 모든 TC를 해당 논리사이클로 매핑

**Toyo (`_unified_toyo_load_raw`)**
- 개별 CSV 파일(XXXXXX 형식)을 사이클별로 로드
- cycle_map이 있으면 `(first_file, last_file)` 범위의 파일들을 순서대로 읽기
- Condition 재매핑: 0→3 (Toyo에서 0=휴지 → 통합 코드의 3=휴지로)
- 파일 경계 마킹: `_file_boundaries` 컬럼으로 시간 리셋 보정 지원

#### Stage 2: Condition 필터링 — Condition=9 재분류

이 단계가 최근 수정된 **핵심 버그 픽스 포인트**이다.

**문제:** PNE Condition=9(CC)는 충전/방전 구분이 없다. 기존 코드는 charge, discharge 양쪽 필터에 모두 Condition=9를 포함시켜, 펄스/GITT 데이터에서 반대 방향 CC 스텝이 섞였다.

**해결:** 필터 적용 전에 `Current_mA` 부호로 재분류:

```python
# Condition=9 행에 대해
if Current_mA > 0:  Condition = 1   # CC 충전
if Current_mA < 0:  Condition = 2   # CC 방전
if Current_mA == 0: Condition = 3   # 전류 없음 → 휴지
```

재분류 후에는 charge → `[1]`만, discharge → `[2]`만 필터하므로 정확한 방향 분리가 보장된다.

#### Stage 3: 단위 정규화

**PNE 정규화 — 핵심 변환:**

| 원시값 | 변환 | 결과 | 비고 |
|--------|------|------|------|
| Voltage_raw (μV) | ÷ 1,000,000 | V | |
| Current_raw (μA) | ÷ cap_divisor | 정규화 C-rate | cap_divisor = mincapacity × 10^6 (또는 10^3) |
| ChgCap_raw (μAh) | ÷ cap_divisor | 0~1 정규화 | 장비가 직접 제공 |
| TotTime | Day×8640000 + Sec÷100 | 초(s) | PNE 고유 이중 시간 포맷 |
| Temp_raw (mK) | ÷ 1,000 | °C | |

**Toyo 정규화 — 핵심 차이점:**

Toyo는 장비가 용량을 제공하지 않으므로 **전류 적분으로 계산**:
```python
dt = diff(Time_s)
current_a = Current_mA / 1000
chg_increments = where(Condition==1, |current_a| × dt / 3600, 0)
ChgCap = cumsum(chg_increments) / (mincapacity / 1000)
```

**시간 리셋 보정** — Toyo CSV의 PassTime은 파일 경계에서 리셋됨:
```python
diffs = diff(time_raw)
diffs[diffs < 0] = 0  # 음수(리셋) → 0으로 클리핑
Time_s = cumsum(diffs)  # 연속 시간 재구성
```

#### Stage 4: 스텝 병합

**왜 필요한가:** 다단 충전(1C CC → 4.2V CV → 0.5C CC → 4.35V CV) 같은 패턴에서, 각 스텝의 시간과 용량이 0부터 시작하므로 연속 프로파일로 보려면 누적 오프셋이 필요하다.

```
Before:  Step1(t: 0~100, cap: 0~0.3)  Step2(t: 0~50, cap: 0~0.2)
After:   Step1(t: 0~100, cap: 0~0.3)  Step2(t: 100~150, cap: 0.3~0.5)
```

**cycle 모드에서는 병합하지 않음** — 충전+방전이 하나의 시계열로 이미 시간순 정렬되어 있기 때문.

#### Stage 5: X축 및 SOC 계산

**옵션 의존성 규칙:**
- `axis_mode="soc"` → `continuity="overlay"` 강제 (SOC 축에서 "이어서"는 물리적으로 무의미)
- `continuity="continuous"` → `axis_mode="time"` 강제

**오버레이 모드의 NaN 삽입:**
cycle 스코프에서 하나의 사이클 내 충전→방전 전환점에 NaN 행을 삽입한다. matplotlib은 NaN을 만나면 선을 끊으므로, 충전 끝점에서 방전 시작점으로 이어지는 스퓨리어스 라인을 방지한다.

```python
# Cycle 1의 Condition별 그룹 사이에 NaN 행 삽입
parts = [충전 데이터] + [NaN 행] + [방전 데이터]
```

---

## 7. 옵션 조합과 14가지 유효 모드

4개 옵션(data_scope × axis_mode × continuity × include_rest)의 유효 조합:

| # | data_scope | axis_mode | continuity | 레거시 대응 | 용도 |
|---|-----------|-----------|-----------|-------------|------|
| 1 | charge | time | overlay | step (충전) | 사이클별 충전 프로파일 비교 |
| 2 | discharge | time | overlay | step (방전) | 사이클별 방전 프로파일 비교 |
| 3 | cycle | time | overlay | step (전체) | 사이클별 충방전 오버레이 |
| 4 | charge | soc | overlay | chg | SOC vs 전압 (충전) + dQ/dV |
| 5 | discharge | soc | overlay | dchg | SOC vs 전압 (방전) + dQ/dV |
| 6 | cycle | soc | overlay | cycle_soc | 양방향 SOC 루프 |
| 7 | charge | time | continuous | continue (충전) | 연속 충전 이력 |
| 8 | discharge | time | continuous | continue (방전) | 연속 방전 이력 |
| 9 | cycle | time | continuous | continue (전체) | 전체 시험 시계열 |
| 10~14 | 위 조합 + include_rest=True | | | | 휴지 구간 포함 버전 |

---

## 8. 사이클분석 ↔ 프로파일분석 cycle_map 공유

### 8.1 cycle_map 생성 지점

```
사이클분석:
  toyo_cycle_data() → toyo_build_cycle_map() → df.cycle_map에 저장
  pne_cycle_data()  → pne_build_cycle_map()  → df.cycle_map에 저장

프로파일분석:
  unified_profile_core(cycle_map=None) → 내부에서 자동 생성
  unified_profile_core(cycle_map=외부값) → 전달받은 맵 사용
```

### 8.2 현재 공유 방식

사이클분석과 프로파일분석은 **동일한 빌드 함수**(`pne_build_cycle_map`, `toyo_build_cycle_map`)를 호출하므로 **동일한 논리사이클 정의**를 얻는다. 다만 현재 UI에서는 각각 독립적으로 호출하고 있어, cycle_map이 채널당 2번 생성될 수 있다.

**최적화 포인트:** PNE는 `_get_pne_cycle_map()`의 캐시로 중복 생성을 방지. Toyo는 capacity.log 파싱 비용이 낮아 큰 부담 없음.

### 8.3 스윕 감지 연동

cycle_map의 값이 **int면 일반, tuple이면 스윕**:

```python
_is_sweep = any(isinstance(v, tuple) for v in cycle_map.values())
```

이 정보가 `_unified_filter_condition()`에 전달되어, 스윕 데이터에서 보충 충/방전을 추가 필터링한다.

---

## 9. 통합 전후 비교 — 정량 분석

### 9.1 코드 규모 변화

| 지표 | 통합 전 (HEAD) | 통합 후 (현재) | 변화 |
|------|---------------|---------------|------|
| 전체 줄 수 | 22,525 | 25,382 | +2,857 |
| 프로파일 관련 함수 수 | 5개 (독립) + 10개 (PNE/Toyo 분기) | 3개 (통합) + 9개 (인프라) | 15 → 12개 |
| cycle_map 빌드 함수 | 2개 (기본) | 4개 (기본 + 스윕 + 캐시 + 스케줄) | +2개 (스윕/스케줄 지원 추가) |
| 레거시 함수 | 전체 활성 | 50+개 유지 (하위 호환) | 점진적 제거 예정 |

### 9.2 기능 확장

| 기능 | 통합 전 | 통합 후 |
|------|---------|---------|
| 옵션 조합 | 5가지 (함수별 1개) | 14가지 (옵션 자유 조합) |
| 스윕 테스트 지원 | 미지원 | ✅ GITT, 펄스, DCIR, 히스테리시스 |
| .sch 스케줄 파싱 | 외부 모듈 의존 | ✅ 내부 구현 |
| Condition=9 방향 분리 | ❌ (양쪽 필터에 포함) | ✅ 전류 부호 기반 재분류 |
| cycle_map 공유 | ❌ (각각 독립 생성) | ✅ 동일 빌드 함수 + 캐시 |
| 결과 컨테이너 | dict / DataFrame | UnifiedProfileResult (메타데이터 포함) |
| 배치 병렬 처리 | 일부만 | ✅ ThreadPoolExecutor 전면 적용 |

### 9.3 제거된 중복

```
Before:
  pne_step_Profile_batch() + toyo_step_Profile_batch()   ← 거의 동일
  pne_rate_Profile_batch() + toyo_rate_Profile_batch()   ← 거의 동일
  pne_chg_Profile_batch()  + toyo_chg_Profile_batch()    ← 거의 동일
  pne_dchg_Profile_batch() + toyo_dchg_Profile_batch()   ← 거의 동일
  pne_continue_Profile_batch() + toyo_continue_batch()   ← 거의 동일

After:
  unified_profile_core()           ← 1개로 통합
  unified_profile_batch()          ← 배치 처리
  unified_profile_batch_continue() ← 연속 모드 배치
```

**10개 함수 → 3개 함수**로 축소. 사이클러 분기는 Stage 1 내부에서 처리.

---

## 10. 설계 결정 분석 — 왜 이렇게 설계했는가

### 10.1 옵션 기반 설계 vs 함수 분리

**결정:** 4개 옵션 파라미터로 14가지 모드를 하나의 함수에서 처리

**이유:**
- 6단계 중 Stage 1(로딩), Stage 3(정규화)는 옵션과 무관 → 무조건 중복
- Stage 2(필터)와 Stage 5(축 계산)만 옵션별 분기 → 내부 if문으로 충분
- 결과 컨테이너 구조도 동일 → 별도 함수로 나눌 이유 없음

### 10.2 cycle_map 딕셔너리 형식

**결정:** int값 = 일반 사이클, tuple값 = 스윕 범위

```python
{1: 100, 2: (101, 105), 3: 106}  # int=단일TC, tuple=범위
```

**이유:**
- isinstance(v, tuple) 한 줄로 스윕 감지 가능
- 일반 사이클은 TC 번호만 있으면 충분 (추가 구조 불필요)
- 스윕은 시작/끝 TC로 범위 표현 필요 → tuple이 가장 간결

### 10.3 레거시 함수 유지

**결정:** 기존 50+ 함수를 삭제하지 않고 병존

**이유:**
- 22,000줄 모놀리스에서 일괄 삭제는 회귀 리스크가 큼
- UI 시그널-슬롯이 레거시 함수를 직접 참조하는 곳이 있음
- 점진적 마이그레이션: 새 UI 진입점은 unified 함수 사용, 기존 진입점은 레거시 유지

---

## 11. 향후 개선 포인트

### 11.1 레거시 제거 (Phase B)
- 통합 함수로 완전 전환 후, 기존 10개 배치 함수 삭제
- UI 시그널 연결을 `unified_profile_confirm_button()`으로 통일

### 11.2 cycle_map 캐시 통합
- 사이클분석에서 생성한 cycle_map을 프로파일분석에 직접 전달하는 경로 구축
- 현재: 각각 독립 빌드 (PNE는 캐시로 완화, Toyo는 비용 낮음)

### 11.3 Toyo 용량 계산 정밀도
- 현재 전류 적분 방식은 고C-rate에서 오차 누적 가능
- 개선: 사다리꼴 적분(trapezoidal) 또는 Simpson 적분 적용 검토

### 11.4 Condition=9 재분류 확장
- 현재: 행별 전류 부호로 판별
- 개선: 스텝 단위 대표 전류(median)로 판별 → 노이즈 저항성 향상

### 11.5 테스트 커버리지
- `test_profile_analysis.py`: 61개 데이터 × 11개 옵션 조합 → 1,834건 통과
- 추가 필요: cycle_map 빌드 로직 단위 테스트 (특히 스윕 경계 조건)

---

## 부록 A: 주요 함수 위치 참조

| 함수 | 줄 번호 | 역할 |
|------|---------|------|
| `name_capacity()` | 329 | 파일명 용량 추출 |
| `check_cycler()` | 385 | PNE/Toyo 판별 |
| `UnifiedProfileResult` | 636 | 결과 데이터클래스 |
| `_unified_pne_load_raw()` | 660 | PNE 원시 로딩 |
| `_unified_toyo_load_raw()` | 791 | Toyo 원시 로딩 |
| `_unified_normalize_pne()` | 890 | PNE 단위 변환 |
| `_unified_normalize_toyo()` | 954 | Toyo 단위 변환 |
| `_unified_filter_condition()` | 1018 | Condition 필터+재분류 |
| `_unified_merge_steps()` | 1127 | 스텝 병합 |
| `_unified_calculate_axis()` | 1179 | X축/SOC 계산 |
| `_unified_calculate_dqdv()` | 1268 | dQ/dV 미분 용량 |
| `unified_profile_core()` | 1316 | **6단계 메인 엔진** |
| `toyo_cycle_data()` | 2484 | Toyo 사이클 분석 |
| `toyo_build_cycle_map()` | 2710 | Toyo cycle_map 빌드 |
| `_pne_build_sweep_cycle_map()` | 2839 | PNE 스윕 cycle_map |
| `pne_build_cycle_map()` | 2993 | PNE cycle_map 빌드 |
| `pne_min_cap()` | 6183 | PNE 용량 산정 |
| `pne_cycle_data()` | 6335 | PNE 사이클 분석 |
| `unified_cyc_confirm_button()` | 16322 | 사이클분석 UI 진입 |
| `_read_profile_options()` | 18870 | 프로파일 옵션 읽기 |
| `unified_profile_confirm_button()` | 18917 | 프로파일분석 UI 진입 |
