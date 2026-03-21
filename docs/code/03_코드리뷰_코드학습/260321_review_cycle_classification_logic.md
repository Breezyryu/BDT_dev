# 사이클 분류 로직 정리

> **대상 파일**: `analyze_cycle_category.py`  
> **작성일**: 2026-03-21  
> **목적**: 배터리 시험 데이터의 raw cycle을 카테고리별로 분류하는 로직 전체를 정리

---

## 1. 개요

`analyze_cycle_category.py`는 PNE / Toyo 두 종류의 사이클러(cycler) 데이터를 읽어, 각 raw cycle을 아래 6개 카테고리 중 하나로 분류한다.

| 카테고리 | 라벨 | 의미 |
|----------|------|------|
| `RPT` | RPT (0.2C 충방전) | 잔존 용량 측정용 참조 사이클 |
| `Rss` | Rss (DCIR pulse) | 내부저항(DCIR) 측정 펄스 사이클 |
| `가속수명` | 가속수명 (멀티스텝 충전) | 실제 수명 시험 반복 사이클 |
| `GITT` | GITT (펄스 그룹) | 갈바노스태틱 간헐 적정 시험 (다수 raw cycle 병합) |
| `initial` | initial (초기 반사이클) | 시험 시작 시 초기 방전/REST만 포함 |
| `unknown` | unknown (분류불가) | 위 기준에 해당하지 않는 사이클 |

---

## 2. PNE 데이터 분류 (3단계 파이프라인)

PNE 사이클러의 `SaveEndData.csv`를 기반으로 분류한다.

### 2.1 사용하는 컬럼

| 컬럼명 | 인덱스 | 의미 | 핵심 값 |
|--------|--------|------|---------|
| `TotlCycle` | [27] | raw cycle 번호 | 정수 |
| `StepType` | [2] | 스텝 종류 | 1=충전, 2=방전, 3=REST, 8=루프마커 |
| `EndState` | [6] | 종료 조건 | 78=용량 컷오프 (Rss 판별 핵심) |

### 2.2 전처리

```
StepType == 8 (루프 마커) 행 제거 → 실제 동작 스텝만 남김
```

### 2.3 1단계: raw cycle별 기본 분류 (`_classify_single_pne_cycle`)

각 raw cycle(같은 `TotlCycle` 값을 가진 행 그룹)에 대해 아래 특성을 계산한다:

```
n_charge   = StepType==1 (충전) 스텝 수
n_discharge = StepType==2 (방전) 스텝 수
n_rest     = StepType==3 (REST) 스텝 수
has_es78   = EndState==78 존재 여부
action     = 활성 스텝(충전/방전)만 모았을 때 동작 종류
```

**action 판별:**

| 조건 | action 값 |
|------|-----------|
| 활성 스텝 없음 (REST만) | `REST_ONLY` |
| 활성 스텝 전부 충전 | `CHG_ONLY` |
| 활성 스텝 전부 방전 | `DCHG_ONLY` |
| 충전+방전 혼합 | `MIXED` |

**카테고리 판별 (순서가 중요!):**

```
① n_charge==0 AND n_discharge==0  →  initial    (REST만 있는 사이클)
② action이 CHG_ONLY 또는 DCHG_ONLY  →  _pulse   (GITT 병합 대상 후보)
③ has_es78 == True               →  Rss         (DCIR 펄스)
④ n_charge >= 2 AND n_discharge >= 1  →  가속수명 (멀티스텝 충전)
⑤ n_charge == 1 AND n_discharge >= 1  →  RPT     (단일 충전 + 방전)
⑥ 그 외                           →  unknown
```

> **핵심**: ②번이 ③~⑤보다 **먼저** 체크된다. 이렇게 해야 방전+REST만 있는 GITT 펄스(DCHG_ONLY)가 `initial`이 아닌 `_pulse`로 분류된다.

#### 각 카테고리 판별 근거 (자세한 설명)

**Rss (DCIR pulse)**
- `EndState == 78` → 용량 컷오프로 종료되었다는 의미
- Rss 시험에서는 짧은 전류 펄스 인가 후 용량 기준으로 종료하므로, 이 값이 존재하면 DCIR 측정
- 충전+방전이 혼합(`MIXED`)인 사이클에서만 도달 (②에서 단일 동작은 이미 `_pulse` 처리)

**RPT (0.2C 충방전)**
- 충전 1회 + 방전 1회 이상의 단순 구조
- 정격 용량의 일정 비율 이상 방전하는 참조 사이클
- `n_charge == 1`로 멀티스텝 충전인 가속수명과 구분

**가속수명 (멀티스텝 충전)**
- `n_charge >= 2` → CC-CV 또는 다단계 충전 프로파일
- 실제 수명 시험의 반복 사이클 (전체 사이클의 95%+ 차지)

**_pulse (GITT 병합 대상)**
- 내부 임시 카테고리 (최종 출력에는 나타나지 않음)
- 하나의 동작만 포함: 충전만(CHG_ONLY) 또는 방전만(DCHG_ONLY)
- 예: GITT 시험의 `DCHG-REST-DCHG-REST-...` 연속 펄스 중 각 raw cycle

### 2.4 2단계: 펄스 그룹 병합 (`_merge_pulse_groups`)

`_pulse`로 분류된 연속 raw cycle들을 GITT 논리 사이클로 병합한다.

#### 병합 규칙

```
1단계: 세그먼트화
  - 연속된 _pulse 중 같은 action(CHG_ONLY/DCHG_ONLY) → 하나의 펄스 그룹
  - 일반 사이클(RPT, 가속수명 등) → 그대로 유지

2단계: 페어링
  - 인접 반대 동작 펄스 그룹 1쌍 → 하나의 GITT 논리 사이클로 합침
  - 최대 1쌍만 페어링 (탐욕적 확장 방지)

3단계: GITT 판별 조건
  - has_multi_pulse: 쌍 중 하나라도 2개 이상의 raw cycle 포함 → True
  - has_multi_pulse == False → 단순 CHG+DCHG 1:1 쌍이므로 GITT 아님 → initial로 복원
```

#### 왜 "반복 펄스" 조건이 필요한가?

가속수명 시험 끝에 단독 CHG raw cycle이 1개 남은 경우를 생각하면:
- 이 CHG는 `_pulse`(CHG_ONLY)로 분류됨
- 직전의 단독 DCHG도 `_pulse`(DCHG_ONLY)로 분류될 수 있음
- 단순 1+1 쌍은 GITT가 아니라 초기/마무리 반사이클일 뿐
- **연속 동일 동작 ≥ 2개**가 없으면(반복 펄스 패턴이 없으면) → `initial`로 복원

#### GITT 사이클 출력 형태

병합 결과의 GITT 논리 사이클에는 추가 메타데이터가 포함된다:

| 필드 | 의미 | 예시 |
|------|------|------|
| `raw_cycles` | 병합된 raw cycle 수 | 121 |
| `raw_range` | raw cycle 번호 범위 | "2-122" |
| `n_charge` | 병합된 총 충전 스텝 수 | 0 |
| `n_discharge` | 병합된 총 방전 스텝 수 | 121 |

### 2.5 3단계: 결과 정리 (`classify_pne_cycles`)

내부 임시 필드(`action`, `has_es78` 등)를 제거하고 최종 결과를 반환한다.

### 2.6 PNE 분류 흐름도

```
Raw SaveEndData.csv
     │
     ▼ StepType==8 제거
     │
     ▼ TotlCycle별 groupby
     │
     ├─ REST만 ──────────────────────── → initial
     │
     ├─ CHG_ONLY / DCHG_ONLY ────────── → _pulse (임시)
     │     │
     │     ▼ 연속 동일 action 그룹화
     │     │
     │     ▼ 인접 반대 동작 1쌍 페어링
     │     │
     │     ├─ 반복펄스(≥2) 있음 ──── → GITT
     │     └─ 반복펄스 없음 ───────── → initial
     │
     ├─ EndState==78 포함 ──────────── → Rss
     │
     ├─ n_charge ≥ 2, n_discharge ≥ 1 → 가속수명
     │
     ├─ n_charge == 1, n_discharge ≥ 1 → RPT
     │
     └─ 그 외 ──────────────────────── → unknown
```

---

## 3. Toyo 데이터 분류

Toyo 사이클러의 `CAPACITY.LOG`를 기반으로 분류한다.

### 3.1 사용하는 컬럼

| 컬럼명 | 의미 | 핵심 값 |
|--------|------|---------|
| `Condition` | 동작 조건 | 1=충전, 2=방전, 3=REST 등 |
| `Cap[mAh]` | 용량 (mAh) | 실수 |

### 3.2 전처리: 연속 동일 Condition 병합

```
Condition 1, 1, 1, 2, 2  →  (CHG, 3행, 합계cap), (DCHG, 2행, 합계cap)
```
같은 Condition이 연속되면 하나의 **그룹**으로 묶고, 해당 구간의 용량 합계를 계산한다.

### 3.3 논리 사이클 구성 및 분류

충전 그룹 + 방전 그룹 쌍을 하나의 논리 사이클로 묶은 후 분류한다.

**분류 기준 (충전 행 수만으로 판별):**

| 조건 | 카테고리 | 설명 |
|------|----------|------|
| 충전 0행 (방전만) | `initial` | 초기 방전 반사이클 |
| 충전 1행 | `RPT` | 단일 충전 = 0.2C 참조 충방전 |
| 충전 ≥ 2행 | `가속수명` | 멀티스텝 CC-CV 충전 프로파일 |
| 그 외 | `unknown` | (현재 데이터에서 발생하지 않음) |

> **왜 용량 threshold를 쓰지 않는가?**  
> 초기 설계에서는 `방전 cap > capacity × 0.85`를 RPT 판별에 사용했으나, 장수명 시험 진행 시 용량 열화로 RPT 방전 용량이 정격의 85% 미만으로 떨어지면 RPT가 `unknown`으로 오분류되는 문제가 있었다. Toyo 가속수명은 항상 멀티스텝 충전(충전 ≥ 2행)이므로, **충전 행 수만으로 RPT(1행) vs 가속수명(2행+)을 완전히 구분**할 수 있다.

### 3.4 Toyo 분류 흐름도

```
Raw CAPACITY.LOG
     │
     ▼ 연속 동일 Condition 병합
     │
     ▼ CHG+DCHG 쌍 구성
     │
     ├─ 충전 0행 ──────────────────── → initial
     │
     ├─ 충전 1행 ──────────────────── → RPT
     │
     ├─ 충전 ≥ 2행 ───────────────── → 가속수명
     │
     └─ 그 외 ─────────────────────── → unknown
```

---

## 4. Toyo vs PNE 차이점 비교

| 항목 | PNE | Toyo |
|------|-----|------|
| 원본 파일 | SaveEndData.csv | CAPACITY.LOG |
| 사이클 구분 키 | TotlCycle 컬럼 | 직접 구성 (Condition 연속 병합) |
| Rss 판별 | EndState==78 ✅ | 불가 ❌ (EndState 컬럼 없음) |
| GITT 판별 | 펄스 그룹 병합 ✅ | 불가 ❌ (Toyo에 GITT 데이터 없음) |
| RPT 판별 기준 | 충전 1회 + 방전 존재 | 충전 1행 + 방전 cap > 85% |
| 가속수명 기준 | 충전 ≥ 2스텝 | 충전 ≥ 2행 |
| 사이클 정의 | raw cycle = TotlCycle 값 | 논리 사이클 = CHG+DCHG 쌍 |

---

## 5. 시험 종류 자동 감지 (`detect_test_type`)

분류 결과의 카테고리 분포를 기반으로 채널의 시험 종류를 추정한다.

| 조건 (우선순위 순) | 판정 결과 |
|---------------------|-----------|
| GITT > 전체의 30% | GITT 시험 |
| 가속수명 > 50% | 가속수명 시험 |
| Rss > 30% | Rss/DCIR 시험 |
| RPT > 50% | RPT 전용 |
| 가속수명 > 0 AND Rss > 0 | 가속수명 + Rss 복합 |
| 그 외 | 기타 |

---

## 6. 실제 분류 결과 예시 (rawdata/ 기준)

| 데이터 유형 | 채널 수 | 분류 결과 |
|-------------|---------|-----------|
| 가속수명 (Q7M/Q8 수명시험) | 164 | 가속수명 98.5%, RPT 1.2% |
| GITT 하프셀 (cathode) | 2~8 | GITT=2, raw 130~181개 → 2 논리사이클 |
| GITT 하프셀 (anode) | 2~8 | GITT=2, raw 194개 → 2 논리사이클 |
| RatedCh 하프셀 | 18 | RPT=5 (정상 충방전 반복) |
| 스케줄 미실행 (M01Ch042) | 1 | initial=2 (기타) |
