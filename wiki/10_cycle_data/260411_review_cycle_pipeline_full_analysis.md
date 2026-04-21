# BDT 사이클 데이터 파이프라인 전체 분석

> **작성일**: 2026-04-11
> **최종 갱신**: 2026-04-21 — 리뷰 시리즈 통합
> **대상**: `DataTool_dev/DataTool_optRCD_proto_.py`
> **목적**: 경로 입력 → TC 사이클 → 논리 사이클 → UI 표시까지 전체 데이터 흐름 정비
>
> 📎 2026-04-21: `260402_cycle_analysis_pipeline`, `260404_review_cycle_data_tab`, `260406_review_unified_cycle_profile_pipeline` 병합.

---

## 진화 이력 (Timeline)

사이클 파이프라인 리뷰 문서의 진화 기록. 각 단계의 핵심 관점과 기여점.

### 260402 — 초기 아키텍처 (from `260402_cycle_analysis_pipeline`)

**관점**: 디버깅/유지보수 레퍼런스로서 전체 아키텍처를 함수 호출 트리와 함께 체계화.

핵심 기여:

- **함수 호출 트리** — `unified_cyc_confirm_button` → `_load_all_cycle_data_parallel` → `_load_cycle_data_task` → `pne_cycle_data`/`toyo_cycle_data` 전체 call graph 정리
- **DCIR 3모드 상세 분석**:
  - 모드 A (`chkir=True`): 방전 + 고전압 `imp` 추출
  - 모드 B (`mkdcir=True`): RSS + 1s 펄스 3-way (dcirtemp1/2/3 서브셋)
  - 모드 C (기본): 10s 이하 펄스
- **SaveEndData.csv 13컬럼 매핑** — PNE 원본 CSV 컬럼 인덱스 ↔ 변수명 ↔ 단위 (μV/μA/μAh/mC/cs → V/A/Ah/°C/초)
- **Toyo 17단계 inline 처리** — `toyo_cycle_data()` 내부 flow (방전 시작 보정, merge_group cumsum, 다단 CC 병합, 위치 기반 Chg/Dchg 재정렬)
- **캐싱 아키텍처** — `_channel_cache[raw_file_path]` 전역 dict 구조 (`pne_restore`, `min_cap`, `capacity_log` 3키)
- **엑셀 저장 시트 매핑** — 14개 시트 × 조건부 생성 (방전용량, RSS, SOC70_DCIR 등)
- **전체 분기 조건 맵** — 데이터 소스 / DCIR / 탭-모드 / 용량 분기 (매트릭스 형태)

### 260404 — 물리 의미 + 로직 해설 (from `260404_review_cycle_data_tab`)

**관점**: 배터리 엔지니어가 처음 코드를 접할 때 "이 숫자가 무엇인가"를 바로 이해하도록 물리 의미 중심 해설.

핵심 기여:

- **DataFrame 개념 입문** — `df`, `Cycleraw`, `df.NewData`를 "엑셀 시트처럼 행/열로 된 표"로 설명
- **pivot_table 물리적 의미** — "스텝 단위" → "사이클 단위" 변환 도구. aggfunc dict 상세 (DchgCap: sum, Ocv: min, Temp: max)
- **Cycleraw 컬럼 13개 물리 의미 매핑** — TotlCycle/Condition/DchgCap/chgCap/Ocv/Temp/imp/Curr/DchgEngD/steptime/EndState
- **df.NewData 컬럼별 정상 범위** — Dchg(0.7~1.0), Eff(0.992~1.004), RndV(NMC 4.10~4.20V), Temp(0~50°C)
- **효율 지표 물리 배경** — Eff < 1.0 이유 = SEI 성장 / Li plating 부반응. Eff > 1.0 = 측정 오류
- **OCV vs AvgV 차이의 진단적 의미** — RndV(무부하)와 AvgV(부하)의 간격이 벌어지면 내부 저항 증가 신호
- **name_capacity() 정규식 예시** — `1689mAh`, `4-187mAh` (하이픈 소수점)
- **단위 변환 요약 테이블** — μAh→mAh, μV→V, m°C→°C, μΩ→mΩ, μWh→mWh
- **한 채널의 데이터가 그래프가 되기까지** — check_cycler → name_capacity → toyo_cycle_data → graph_output_cycle 추적

### 260406 — 사이클+프로필 통합 관점 (from `260406_review_unified_cycle_profile_pipeline`)

**관점**: 사이클분석과 프로파일분석이 **cycle_map을 공유**하는 통합 아키텍처 리빌딩. "왜 통합했는가" 설계 결정 분석.

핵심 기여:

- **리빌딩 배경** — 기존 5개 독립 프로필 함수(step/rate/chg/dchg/continue) × PNE/Toyo 분기 → 코드 중복 60%+
- **cycle_map 공유 핵심 아이디어** — 논리사이클 ↔ 물리사이클 매핑 딕셔너리를 한 번 빌드하여 사이클/프로필이 **동일한 사이클 정의**를 공유
- **cycle_map 형식 설계** — `{1: 100, 2: (101,105), 3: 106}` — int=일반, tuple=스윕. `isinstance(v, tuple)` 한 줄로 스윕 감지
- **Toyo cycle_map 5단계 알고리즘** — ①Condition 병합 ②임계값 결정 ③Pass1 방전 기반 ④Pass2 충전 전용 ⑤정렬/순번 부여
- **PNE 일반/스윕 자동 판별** — sig_ratio ≥ 50% AND has_both_ratio ≥ 30% → 일반, 아니면 스윕. TC ≤ 5 → 일반 강제
- **스윕 cycle_map 4단계** — ①TC 분류 ②세그먼트 생성 ③흡수(Absorption) ④반대 방향 스윕 병합
- **unified_profile_core() 6-Stage 파이프라인**:
  1. 원시 로딩 (`_unified_pne_load_raw` / `_unified_toyo_load_raw`)
  2. Condition 필터링 (Condition=9 전류 부호 기반 재분류 **버그 픽스 포인트**)
  3. 단위 정규화 (μV→V, μA→mA, mC→°C)
  4. 스텝 병합 (다단 CC 충전 시간/용량 오프셋)
  5. X축 & SOC 계산 (overlay/continuous, NaN 삽입)
  6. 파생값 (dQdV, dVdQ, Energy)
- **14가지 유효 옵션 조합** — data_scope(3) × axis_mode(2) × continuity(2) + include_rest
- **옵션 의존성 규칙** — SOC 모드 → overlay 강제, continuous 모드 → time 강제
- **코드 규모 변화** — 22,525 → 25,382줄 (+2,857, 기능 확장 반영). 프로필 함수 15 → 12 감소
- **Condition=9 재분류 버그 픽스** — 기존 charge/discharge 양쪽 필터에 Condition=9 포함 → 펄스/GITT에서 반대방향 스텝 섞임. 수정: `Current_mA > 0 → Cond=1`, `< 0 → Cond=2`, `== 0 → Cond=3`

### 260411 — 현재 문서 (최종 정비)

**관점**: 4가지 "사이클" 개념을 명시적으로 분리하고, 경로 테이블 7열 구조를 중심으로 파이프라인 재정비. ECT 시험 파라미터까지 확장.

---

## 최종 정비 (260411)

## 1. 전체 파이프라인 개요

```
┌─────────────────────────────────────────────────────────────────────┐
│                        BDT 사이클 데이터 파이프라인                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [1] 경로 입력 (Path Input)                                          │
│   │  UI: cycle_path_table (7열 테이블)                                │
│   │  파일: .txt 경로 파일 로드/저장                                     │
│   ▼                                                                  │
│  [2] 입력 파싱 (_parse_cycle_input)                                   │
│   │  CycleGroup 생성 (folder/excel 분류)                              │
│   │  link_mode, ECT mode 판별                                        │
│   ▼                                                                  │
│  [3] 사이클러 판별 (check_cycler)                                     │
│   │  PNE (바이너리) vs Toyo (CSV) 자동 감지                            │
│   ▼                                                                  │
│  [4] Raw 데이터 로드                                                  │
│   │  Toyo: CAPACITY.LOG → toyo_cycle_data()                          │
│   │  PNE:  SaveEndData.csv → pne_cycle_data()                       │
│   ▼                                                                  │
│  [5] TC → 논리사이클 매핑 (cycle_map)                                  │
│   │  toyo_build_cycle_map() / pne_build_cycle_map()                  │
│   │  다단 충전, GITT 펄스 등을 1개 논리사이클로 그룹화                     │
│   ▼                                                                  │
│  [6] df.NewData 구성                                                  │
│   │  Cycle(1,2,3,...), Dchg, Chg, Eff, RndV, AvgV, Temp,            │
│   │  OriCyc, dcir, dcir2, soc70_dcir ...                             │
│   ▼                                                                  │
│  [7] 연결 처리 (Link Mode Merge)                                     │
│   │  동일 채널 데이터 인덱스 오프셋 + 연결                               │
│   ▼                                                                  │
│  [8] 그래프 출력 (graph_output_cycle)                                 │
│   │  6개 subplot: 용량잔존율, 효율, 온도, DCIR, Eff2, 전압              │
│   │  X축 = df.NewData.index (논리 사이클 번호)                         │
│   ▼                                                                  │
│  [9] UI 탭 표시                                                       │
│      cycle_tab QTabWidget에 결과 탭 추가                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. 사이클 번호 체계 — 4가지 "사이클" 개념 정의

BDT에서 "사이클"이라는 용어는 문맥에 따라 4가지 다른 의미를 가진다. 이 구분이 파이프라인 이해의 핵심이다.

### 2.1 TC (TotlCycle) — 충방전기 물리 사이클

**정의**: 충방전기(Toyo/PNE)가 기록하는 원시 사이클 번호. 하나의 충전 스텝, 하나의 방전 스텝, 하나의 Rest 스텝이 각각 별도의 TC로 카운트된다.

**Toyo 예시 (Q7M 2C 수명시험 CAPACITY.LOG):**

```
TC=    1  Cond=1  Mode= 1  Cap=  889.8  Finish=Cur    ← 초기 CC 충전
TC=    1  Cond=2  Mode= 1  Cap= 1725.8  Finish=Vol    ← 초기 방전
TC=    2  Cond=1  Mode= 2  Cap=  502.9  Finish=Vol    ← CC 충전 1단 (Vol까지)
TC=    3  Cond=1  Mode= 3  Cap=  219.3  Finish=Vol    ← CC 충전 2단
TC=    4  Cond=1  Mode= 4  Cap=  469.9  Finish=Cur    ← CC 충전 3단 (CV전환)
TC=    5  Cond=1  Mode= 5  Cap=  502.6  Finish=Cur    ← CC 충전 4단 (CV컷오프)
TC=    5  Cond=2  Mode= 5  Cap= 1179.4  Finish=Vol    ← 2C 방전
TC=    6  Cond=2  Mode= 6  Cap=  447.2  Finish=Vol    ← 방전 나머지/Rest
```

→ TC 1~6 = **물리적으로 6개 TC**, 하지만 배터리 과학적으로는 **1개 충방전 사이클**

**PNE 예시 (SaveEndData.csv):**

```
컬럼 인덱스: [0]=행번호, [1]=TotlCycle상태, [2]=Condition, ...
각 행 = 1개 스텝의 종료 데이터
TotlCycle은 컬럼[27]에 인코딩
```

### 2.2 논리 사이클 (Logical Cycle) — cycle_map이 정의

**정의**: cycle_map 알고리즘이 여러 TC를 묶어 "배터리 과학적으로 의미 있는 1회 충방전"으로 정의한 사이클. df.NewData의 각 행이 1개 논리 사이클에 대응.

```python
cycle_map[1] = {
    'all': (2, 6),        # TC 2~6이 이 논리 사이클을 구성
    'chg': [2, 3, 4, 5],  # 충전 TC들 (다단 CC-CV)
    'dchg': [5, 6],       # 방전 TC들
    'chg_rest': [],        # 충전 후 Rest TC
    'dchg_rest': [],       # 방전 후 Rest TC
}
```

**매핑 관계:**

| 논리 사이클 | TC 범위     | 구성                           |
|:----------:|:----------:|:-------------------------------|
| 1          | TC 2~6     | 4단 CC충전 + 2C방전             |
| 2          | TC 7~11    | 4단 CC충전 + 2C방전             |
| 3          | TC 12~16   | 4단 CC충전 + 2C방전             |
| ...        | ...        | 5 TC/논리사이클 패턴 반복          |

### 2.3 UI 입력 사이클 — 사용자가 경로 테이블에 입력하는 사이클

**정의**: cycle_path_table의 "사이클" 열(cycle 열)에 사용자가 입력하는 값. 논리 사이클 번호 기준.

```
경로 테이블 입력 예시:
pathname | path                        | ch  | capacity | cycle | cycleraw | mode
Test_A   | D:\data\testA\             | CH1 | 2500     | 1-50  |          |
Test_B   | D:\data\testB\             | CH3 | 3000     |       | 33       | DCHG
```

- **cycle 열 (논리 사이클)**: 사이클 분석용. "1-50" → 논리 사이클 1~50만 분석
- **cycleraw 열 (TC 사이클)**: ECT 프로필 분석용. 특정 TC를 직접 지정

### 2.4 UI 표시 사이클 — 그래프 X축의 사이클 번호

**정의**: graph_output_cycle()에서 df.NewData.index로 표시되는 X축 값. 기본적으로 1, 2, 3, ... 순차 번호.

연결 처리(link_mode) 시에는 이전 데이터의 마지막 인덱스에 오프셋을 더하여 연속 번호를 부여:

```
파일 A: 논리사이클 1~100 → X축 1~100
파일 B: 논리사이클 1~100 → X축 101~200 (오프셋 +100)
파일 C: 논리사이클 1~100 → X축 201~300 (오프셋 +200)
```

---

## 3. 단계별 상세 분석

### 3.1 Stage 1: 경로 입력 (Path Input)

#### 경로 테이블 구조 (cycle_path_table, 7열)

| 열 인덱스 | 내부 키      | UI 표시명  | 용도                                    |
|:---------:|:----------:|:---------:|:----------------------------------------|
| 0         | pathname   | 시험명     | 레전드/탭 이름에 사용                       |
| 1         | path       | 경로      | 충방전기 데이터 폴더 경로 (Windows 절대경로)   |
| 2         | ch         | 채널      | 채널 필터 (콤마/대시; "-"=스킵)              |
| 3         | capacity   | 용량      | 셀 공칭 용량 (mAh), 비어있으면 자동 추출       |
| 4         | cycle      | 사이클     | 논리 사이클 필터 (사이클 분석용)               |
| 5         | cycleraw   | TotlCycle | TC 번호 필터 (ECT 프로필 분석용)             |
| 6         | mode       | 모드      | ECT 모드 (CYC, DCHG, CHG, GITT, Rss 등)  |

#### 경로 파일 포맷 비교 (v1 vs v2)

**v1 포맷** (레거시 4열: path, cycle, CD, save):

```
path	cycle	CD	save
C:\...\ECT-parameter1	33	DCHG	TR01_SDI_PA2_DCH_CC_0.2
```

- `path`: 데이터 경로, `cycle`: TC 번호, `CD`: DCHG/CHG/Cycle, `save`: 출력 식별자

**v2 포맷** (현재 7열, #메타데이터 헤더 포함):

```
#ect_mode=1
pathname	path	ch	capacity	cycle	cycleraw	mode
TR01_SDI_PA2_DCH_CC_0.2	x:\PNE-5\...\parameter1\			33	DCHG
```

- `#link_mode=0|1`: 연결처리 모드
- `#ect_mode=0|1`: ECT 프로필 모드
- `cycleraw`에 TC 번호, `mode`에 방향(DCHG/CHG/Cycle)

#### 핵심 함수

**`_load_path_file_to_table()` (~Line 20053)**

1. 파일 다이얼로그로 .txt 선택
2. 헤더 포맷 자동 감지 (4열 레거시 / 7열 신규)
3. `#link_mode=`, `#ect_mode=` 메타데이터 → 체크박스 복원
4. 테이블 채우기 → `_set_table_rows()`
5. 비어있는 셀 자동 채우기 (경로에서 용량/채널 추출)

**`_save_table_to_path_file()` (~Line 20200)**

1. 메타데이터 헤더 작성 (`#link_mode=`, `#ect_mode=`)
2. 7열 탭 구분 파일로 저장
3. link_mode 시 빈 행(그룹 구분자) 보존

---

### 3.2 Stage 2: 입력 파싱

**`_parse_cycle_input()` (~Line 18347)**

경로 테이블 → CycleGroup 리스트 변환

```python
@dataclass
class CycleGroup:
    name: str                # 시험명
    paths: list[str]         # 폴더 경로들
    path_names: list[str]    # 사용자 지정 이름
    data_type: str           # 'folder' 또는 'excel'
    file_idx: int            # 탭 분리용 인덱스
    source_file: str         # 원본 txt 경로
    is_link: bool            # 연결처리 여부
    per_path_capacities: list[float]
    per_path_channels: list[list[str]]
    channel_link_map: dict   # 채널별 연결 매핑
```

**동작 분기:**

```
link_mode ON:  빈 행 = 그룹 구분자
               같은 그룹 내 경로들 → 채널별로 merge
               
link_mode OFF: 각 행 = 독립 그룹
               각 채널 개별 색상으로 플롯
```

---

### 3.3 Stage 3: 사이클러 판별

**`check_cycler()` (~Line 420)**

```python
def check_cycler(raw_file_path: str) -> bool:
    """PNE=True, Toyo=False 판별"""
    # 우선순위 1: Pattern 폴더 존재 → PNE
    # 우선순위 2: Restore 폴더 + SaveData 파일 → PNE (GITT/DCIR)
    # 그 외 → Toyo
```

**판별 기준 정리:**

| 디렉토리 구조                        | 판별 결과 |
|:-------------------------------------|:-------:|
| `M01ChXXX[XXX]/` 패턴 폴더 존재        | PNE     |
| `Restore/SaveData*.csv` 존재           | PNE     |
| 숫자만으로 된 채널 폴더 (11, 23, 54 등)  | Toyo    |
| `CAPACITY.LOG` 존재                    | Toyo    |

---

### 3.4 Stage 4: Raw 데이터 로드

#### Toyo 데이터 구조

**파일 계층:**

```
테스트폴더/
├── 11/                     ← 채널 번호 (숫자)
│   ├── 000001              ← 바이너리 시계열 파일 (각 TC별)
│   ├── 000002
│   ├── ...
│   ├── 004956              ← TC 4956까지
│   ├── CAPACITY.LOG        ← 핵심! TC별 요약 CSV
│   ├── *.PTN              ← 실험 패턴 파일
│   └── CHCMT.TXT
├── 23/
├── ...
└── *.CMT                   ← 테스트 완료 마커
```

**CAPACITY.LOG 컬럼 (19열):**

| 컬럼              | 의미                    | 예시                |
|:-----------------|:-----------------------|:-------------------|
| Date             | 날짜                    | 2025/02/07         |
| Time             | 시간                    | 13:10:07           |
| **Condition**    | **1=충전, 2=방전**       | 1, 2               |
| **Mode**         | **패턴 내 스텝 번호**     | 1~30               |
| Cycle            | 패턴 내 사이클 (루프 횟수)  | 1                  |
| **TotlCycle**    | **누적 TC 번호 (핵심)**   | 1~4956             |
| Cap[mAh]         | 해당 스텝 용량            | 1725.860           |
| PassTime         | 스텝 소요 시간            | 005:29:58          |
| TotlPassTime     | 누적 시간                | 006:52:36          |
| Pow[mWh]         | 에너지                   | 7101.765           |
| AveVolt[V]       | 평균 전압                | +4.0503            |
| PeakVolt[V]      | 최대 전압                | +4.5000            |
| (빈열)            | —                      |                    |
| PeakTemp[Deg]    | 최대 온도                | +22.50             |
| Ocv              | 개방전압                 | +3.1125            |
| (빈열)            | —                      |                    |
| **Finish**       | **종료 조건 (Vol/Cur)**  | Vol, Cur           |
| DchCycle         | 방전 사이클               |                    |
| PassedDate       | 경과일                   |                    |

**Condition × Finish의 물리적 의미:**

| Condition | Finish | 의미                              |
|:---------:|:------:|:----------------------------------|
| 1         | Vol    | CC충전 → 전압 상한 도달 (CV 전환점)   |
| 1         | Cur    | CV충전 → 전류 컷오프 도달 (충전 완료)  |
| 2         | Vol    | CC방전 → 전압 하한 도달 (방전 완료)    |
| 2         | Cur    | — (드물게 시간 제한 종료)              |

#### Toyo 다단 충전 패턴 예시 (Q7M 2C 수명시험)

```
[패턴 1사이클 = 5 TC]

TC n+0: Cond=1, Mode=2, Finish=Vol  ← CC 충전 1단 (낮은 C-rate)
TC n+1: Cond=1, Mode=3, Finish=Vol  ← CC 충전 2단
TC n+2: Cond=1, Mode=4, Finish=Cur  ← CC 충전 3단 (CV 전환)
TC n+3: Cond=1, Mode=5, Finish=Cur  ← CV 충전 (컷오프 도달)
TC n+3: Cond=2, Mode=5, Finish=Vol  ← 2C 방전 (같은 TC!)
TC n+4: Cond=2, Mode=6, Finish=Vol  ← 방전 Rest/종료

→ 논리 사이클 1개 = TC 5개
→ 4956 TC ÷ 5 TC/논리사이클 ≈ 991 논리 사이클
```

**중요**: 같은 TC 번호에 Cond=1과 Cond=2가 모두 나올 수 있다 (TC n+3에서 충전 끝 + 방전 시작이 같은 TC).

#### PNE 데이터 구조

**파일 계층:**

```
테스트폴더/
├── M01Ch005[005]/           ← 채널 폴더 (PNE 명명 규칙)
│   ├── *.cts               ← 스케줄 파일 (바이너리)
│   ├── *.cyc               ← 실시간 바이너리 기록
│   ├── *.db                ← PNE 데이터베이스
│   ├── *.sch               ← 스케줄 정의
│   └── Restore/
│       ├── ch05_SaveData0001.csv   ← 시계열 CSV (매일 자정 분할)
│       ├── ch05_SaveData0002.csv
│       ├── ...
│       ├── ch05_SaveEndData.csv    ← 핵심! 스텝별 요약
│       └── savingFileIndex_*.csv
└── *.CMT
```

**SaveEndData.csv (44열, 헤더 없음):**

| 인덱스 | 의미                      | 단위/스케일               |
|:------:|:-------------------------|:------------------------|
| 0      | 행 번호                   |                         |
| 1      | TotlCycle 상태             |                         |
| 2      | **Condition** (1=Chg, 2=Dchg) |                     |
| 6      | EndState                  |                         |
| 8      | **Ocv (전압)**             | μV (÷1000000 → V)      |
| 9      | **Current**               | μA (÷1000000 → A)      |
| 10     | **chgCap**                | μAh (÷1000000 → Ah)    |
| 11     | **DchgCap**               | μAh                     |
| 15     | **DchgEngD**              | μWh                     |
| 17     | **steptime**              | ÷100 → 초               |
| 20     | **imp (IMP)**             |                         |
| 24     | **Temp**                  | m°C (÷1000 → °C)       |
| 27     | **TotlCycle**             | 누적 TC 번호              |
| 29     | **AvgV**                  | μV                      |
| 45     | **volmax**                |                         |

---

### 3.5 Stage 5: TC → 논리사이클 매핑 (cycle_map)

이것이 전체 파이프라인에서 가장 복잡한 로직이다.

#### `toyo_build_cycle_map()` (~Line 3428)

**알고리즘 개요:**

```
Phase 0: CAPACITY.LOG 로드 → 연속 동일 Condition 그룹 병합
Phase 1: 방전 기반 사이클 식별
         ├─ 유효 방전 그룹 (Cap > threshold) 찾기
         ├─ 앞의 충전 그룹 연결
         └─ 뒤의 Rest 그룹 연결
Phase 2: 충전 전용 사이클 (방전 없이 남은 유효 충전)
Phase 3: 정렬 → 논리 사이클 번호 부여 (1, 2, 3, ...)
```

**상세 처리:**

```python
# Phase 0: 연속 동일 Condition 병합
# Toyo는 다단 CC-CV 충전을 여러 행으로 기록
# Condition이 같으면 → 하나의 그룹으로 병합 (용량 합산)

cond_series = Cycleraw["Condition"]
merge_group = ((cond_series != cond_series.shift()) | 
               (~cond_series.isin([1, 2]))).cumsum()

# 예시: TC 2,3,4,5 모두 Cond=1 → 1개 충전 그룹 (Cap 합산)
# TC 5(Cond=2), TC 6(Cond=2) → 1개 방전 그룹

# Phase 1: 방전 기반 사이클 조립
for 각 유효 방전 그룹:
    - 직전 충전 그룹이 있으면 → 같은 논리사이클에 포함
    - 뒤따르는 Rest/비활성 그룹 → 같은 논리사이클에 포함
    - "used" 마킹

# Phase 2: 남은 충전 전용 사이클
for 미사용 유효 충전 그룹:
    - 독립 논리사이클로 생성

# Phase 3: 시작 TC 기준 정렬 → 논리 사이클 번호 부여
```

**용량 threshold:**

```python
base_threshold = mincapacity / 60    # 공칭 용량의 ~1.67%
# GITT 모드: .ptn에서 min_pulse_cap_mAh 추출 → 0.5배 사용
```

#### `pne_build_cycle_map()` (~Line 3806)

**모드 자동 감지 알고리즘:**

```python
# .sch 파일에 sweep_mode가 정의되어 있으면 → 직접 사용
# 아니면 데이터 기반 휴리스틱:

sig_ratio = "용량 > 20% 공칭" TC 비율
has_both_ratio = "충전+방전 모두 있는" TC 비율

if TC ≤ 5:
    mode = "general"    # 보관시험 등 소수 TC
elif sig_ratio ≥ 0.5 and has_both_ratio ≥ 0.3:
    mode = "general"    # 일반 수명 시험
else:
    mode = "sweep"      # GITT, DCIR, 펄스 시험
```

**General 모드**: 모든 TC를 논리사이클로 매핑. 유의미하지 않은 TC는 인접 논리사이클에 병합.

**Sweep 모드**: `_pne_build_sweep_cycle_map()` 호출. 방향별(충전/방전) 그룹화 후 인접 반대방향 그룹을 병합.

#### cycle_map 딕셔너리 최종 구조

```python
cycle_map = {
    1: {
        'all': (2, 6),          # TC 시작~끝 (포함)
        'chg': [2, 3, 4, 5],    # 충전 TC 목록
        'dchg': [5, 6],         # 방전 TC 목록
        'chg_rest': [],          # 충전 후 Rest TC
        'dchg_rest': [],         # 방전 후 Rest TC
    },
    2: {
        'all': (7, 11),
        'chg': [7, 8, 9, 10],
        'dchg': [10, 11],
        ...
    },
    ...
}
```

---

### 3.6 Stage 6: df.NewData 구성

toyo_cycle_data() / pne_cycle_data()의 최종 산출물.

#### df.NewData 컬럼 정의

| 컬럼          | 의미               | 계산 방식                                    | 단위     |
|:-------------|:-------------------|:--------------------------------------------|:---------|
| **Cycle**    | 논리 사이클 순번      | 1, 2, 3, ... (순차 부여)                      | -        |
| **Dchg**     | 방전 용량 잔존율      | 방전용량 / 공칭용량 × 100                       | %        |
| **Chg**      | 충전 용량 잔존율      | 충전용량 / 공칭용량 × 100                       | %        |
| **Eff**      | 쿨롱 효율            | 방전용량(n) / 충전용량(n)                       | ratio    |
| **Eff2**     | 교차 사이클 효율      | 충전용량(n+1) / 방전용량(n)                     | ratio    |
| **RndV**     | Rest 전압 (OCV 근사) | 충전 후 Rest 종료 시 전압                       | V        |
| **AvgV**     | 방전 평균 전압        | 방전 에너지 / 방전 용량                          | V        |
| **Temp**     | 피크 온도             | 방전 중 최고 온도                               | °C       |
| **DchgEng**  | 방전 에너지           | ∫V·I dt                                      | mWh      |
| **OriCyc**   | 원본 TC 번호         | 해당 논리사이클의 마지막 TC                       | -        |
| **dcir**     | DCIR (Rss)          | ΔV/ΔI (방전 시작~끝)                           | mΩ       |
| **dcir2**    | DCIR (1초)           | ΔV/ΔI (1초 시점)                              | mΩ       |
| **soc70_dcir** | SOC70% DCIR        | SOC 70% 지점의 DCIR                           | mΩ       |

#### Toyo에서의 다단충전 용량 합산 로직

```python
# 연속 동일 Condition 그룹 병합
# 충전: 용량 합산, OCV = 첫 행 보존
# 방전: 용량 합산, 에너지 합산, 평균전압 재계산

def merge_rows(group):
    if Condition == 1:  # 충전
        Cap = sum(group["Cap"])        # 다단 CC-CV 총 충전량
        Ocv = group.iloc[0]["Ocv"]     # 충전 시작 OCV
    elif Condition == 2:  # 방전
        Cap = sum(group["Cap"])
        Pow = sum(group["Pow"])
        AveVolt = Pow / Cap            # 가중 평균 전압
```

---

### 3.7 Stage 7: 연결 처리 (Link Mode)

**`chk_link_cycle` 체크박스 ON 시 동작:**

```
경로 파일:
  Test_A  D:\path1\  CH1  2500  1-100
  Test_B  D:\path2\  CH1  2500  1-100
  (빈 행)
  Test_C  D:\path3\  CH1  3000  1-50

→ 그룹 1: Test_A + Test_B (CH1끼리 연결)
   CH1: A의 1~100 + B의 1~100 → X축 1~200 (인덱스 오프셋)

→ 그룹 2: Test_C (독립)
   CH1: C의 1~50 → X축 1~50
```

**인덱스 오프셋 계산:**

```python
# 같은 sub_label(채널명)의 데이터 순차 연결
for 같은_채널 in grouped:
    offset = 이전_데이터의_마지막_인덱스
    현재_df.NewData.index += offset
    결과 = pd.concat([이전, 현재])
```

---

### 3.8 Stage 8: 그래프 출력

**`graph_output_cycle()` (~Line 2659)**

6개 subplot 구성:

```
┌───────────────┬───────────────┐
│ ax1: 용량잔존율  │ ax2: Eff 효율   │
│ Y: Dchg (%)    │ Y: Eff (ratio) │
├───────────────┼───────────────┤
│ ax3: 온도       │ ax4: DCIR      │
│ Y: Temp (°C)   │ Y: dcir (mΩ)   │
├───────────────┼───────────────┤
│ ax5: Eff2 효율   │ ax6: 전압       │
│ Y: Eff2 (ratio) │ Y: RndV, AvgV  │
└───────────────┴───────────────┘

모든 subplot X축 = df.NewData.index (논리 사이클 번호)
```

**X축 스케일 제어 (tcyclerng):**

- 0 = 자동
- n > 0 → X축 주눈금 간격 = n 사이클

**Y축 범위 제어:**

- `tcyclerngyhl`: 용량잔존율 Y축 상한 (기본 1.10 = 110%)
- `tcyclerngyll`: 용량잔존율 Y축 하한 (기본 0.65 = 65%)
- `dcirscale`: DCIR Y축 스케일 팩터

---

### 3.9 Stage 9: 전체 오케스트레이션

**`unified_cyc_confirm_button()` (~Line 18481) — 메인 실행 버튼**

```python
def unified_cyc_confirm_button():
    # 1. 초기화
    cyc_ini_set()
    # → firstCrate, mincapacity, xscale, ylimitlow, ylimithigh, irscale

    # 2. 입력 파싱
    groups = _parse_cycle_input()
    # → CycleGroup 리스트 (folder/excel 분류)

    # 3. 자동 채우기
    _autofill_table_empty_cells()
    # → 경로에서 용량, 채널 자동 추출

    # 4. Excel 그룹 처리 (신뢰성 데이터)
    for excel_group in excel_groups:
        # xlwings로 "Plot Base Data" 시트 읽기
        # 공칭 용량으로 정규화
        # ax1에 플롯

    # 5. 폴더 그룹 처리 (충방전기 데이터)
    # Phase 0: 메타데이터 빌드 (사이클러 타입, 사이클 수)
    _build_all_channel_meta_parallel()
    
    # Phase 1: 데이터 로드 (병렬 처리)
    _load_all_cycle_data_parallel(all_paths, mincapacity, ...)
    # → check_cycler() → toyo_cycle_data() / pne_cycle_data()
    # → df.NewData + df.cycle_map 반환

    # Phase 2: 연결 처리 (link_mode 시)
    # → 채널별 인덱스 오프셋 + 연결

    # Phase 3: 그래프 생성
    for 각 채널/그룹:
        graph_output_cycle(df, xscale, ...)
    
    # 6. 탭 추가 + Excel 저장
```

---

## 4. Raw 실험 데이터 구조 (exp_data 분석)

### 4.1 데이터 분류

| 유형              | 사이클러 | 예시 폴더                                        | TC 규모     |
|:-----------------|:------:|:------------------------------------------------|:----------:|
| 수명시험 (사이클)    | Toyo   | Q7M Inner ATL_45V 1689mAh BLK1 20EA            | ~5000 TC   |
| 수명시험 (사이클)    | PNE    | 250207_...ATL Q7M Inner 2C 상온수명 1-100cyc      | ~500 TC    |
| GITT              | PNE    | 240821_...GITT-15도                              | ~650 스텝   |
| SOC별 DCIR        | PNE    | 240919_...SOC별DCIR-15도                          | ~400 스텝   |
| ECT 파라미터       | PNE    | 250827_...ECT-parameter1~9                       | 다양        |
| Floating 시험     | Toyo   | 250314_...Gen5 SDI Pre-MP Si5% Floating+9D       | —          |

### 4.2 Toyo 다단충전 패턴 실측 분석

Q7M 2C 수명시험 CAPACITY.LOG에서 추출한 실제 반복 패턴:

```
[1 논리사이클 구성]
Mode 2: CC충전 1단 → Cond=1, Finish=Vol (전압 도달)  Cap ≈ 480~500 mAh
Mode 3: CC충전 2단 → Cond=1, Finish=Vol              Cap ≈ 200 mAh
Mode 4: CC충전 3단 → Cond=1, Finish=Cur (CV 전환)    Cap ≈ 440 mAh
Mode 5: CV충전    → Cond=1, Finish=Cur (컷오프)      Cap ≈ 500 mAh
Mode 5: CC방전    → Cond=2, Finish=Vol (하한 도달)   Cap ≈ 1200 mAh
Mode 6: 방전완료   → Cond=2, Finish=Vol               Cap ≈ 430 mAh

총 충전: ~1620 mAh (4단 합산)
총 방전: ~1630 mAh (2스텝 합산)
공칭 용량: 1689 mAh
```

**핵심 관찰:**

1. **같은 TC에 충전+방전**: Mode 5에서 충전(Cond=1)과 방전(Cond=2)이 동일 TotlCycle을 공유
2. **Mode 번호 재사용**: Mode 2~6이 반복됨 (패턴 루프)
3. **Condition 분포**: 충전(Cond=1) 3965행 vs 방전(Cond=2) 1989행 ≈ 2:1 (다단충전이므로)
4. **Mode 분포**: Mode 25~29가 가장 많음 (693~1386행) → 후반부 패턴에서 가속시험 반복

### 4.3 ECT 파라미터 추출 패턴

경로 파일에서 확인된 ECT 시험 구조:

```
PA2-SDI 셀, 4온도 조건:
  TR = Room Temp (23°C)
  TL = Low (15°C) 
  TM = Medium (35°C?)
  TH = High (45°C)

각 온도 × 다수 파라미터 시험:
  parameter1: CC방전 0.2C, 1C
  parameter2: CC방전 0.5C + 다단충전 FC_Multi
  parameter3: Dynamic 방전 A-패턴 0.33C, 0.65C
  parameter4: Dynamic 방전 M-패턴 0.33C, 0.65C
  parameter5: CC충전 0.2C, 0.5C
  parameter6: CC방전 0.1C + CC충전 2.0C/1C/1.4C/1.8C + Activation_ISD(17-46cyc)
  parameter7: Dynamic 방전 A 0.15C + CC충전 0.3~1.6C + ISD_7Cycle
  parameter8: GITT (1-3=Pre, 4-233=본시험)
  parameter9: M47 ECT GITT
```

**cycleraw 컬럼 사용 예:**

```
cycleraw=33  → TC 33번째 스텝만 추출 (특정 방전 프로필)
cycleraw=4-233 → TC 4~233 범위 추출 (GITT 본시험 영역)
cycleraw=17-46 → TC 17~46 범위 (Activation ISD 사이클)
```

---

## 5. 논리사이클 매핑의 핵심 문제점 및 엣지 케이스

### 5.1 현재 로직의 강점

1. **다단 충전 자동 병합**: 연속 동일 Condition 그룹을 인식하여 다단 CC-CV를 1개 충전으로 합산
2. **GITT/DCIR 자동 감지**: sig_ratio + has_both_ratio 기반 sweep/general 모드 분류
3. **패턴 파일(.ptn) 활용**: 용량 threshold를 패턴에서 추출하여 GITT 펄스와 본 사이클 구분

### 5.2 주의가 필요한 엣지 케이스

| 케이스                              | 문제                                         | 현재 처리 방식                    |
|:------------------------------------|:--------------------------------------------|:-------------------------------|
| RPT 사이클 (0.2C 방전)               | 가속시험과 다른 패턴이지만 유효 방전임             | cap threshold 통과 → 독립 사이클   |
| 초기 화성(Formation)                 | 패턴이 다르고 용량이 다름                        | 첫 TC 그룹은 별도 논리사이클        |
| GITT 미세 펄스                      | 개별 펄스가 threshold 미달                     | sweep 모드에서 그룹으로 병합        |
| 중간 시험 변경 (패턴 교체)             | 같은 폴더 내 패턴이 바뀜                        | 새 PTN 파일 자동 감지              |
| 동일 TC에 충전+방전                   | Toyo에서 Cond=1, Cond=2가 같은 TC              | merge_group에서 별도 그룹          |

### 5.3 cycle ↔ cycleraw 컬럼의 역할 분리

```
[사이클 분석 (Tab 1: 실행 버튼)]
  → cycle 열 사용 (논리 사이클 기준)
  → unified_cyc_confirm_button()
  → 6-subplot 그래프 출력

[프로필 분석 (Tab 1: 프로필 버튼)]  
  → cycleraw 열 사용 (TC 기준)
  → unified_profile_confirm_button()
  → 시계열 프로필 그래프 출력

[ECT 분석 (chk_ectpath ON)]
  → cycleraw + mode 열 사용
  → 특정 TC의 특정 방향(CHG/DCHG) 프로필 추출
```

---

## 6. 변환 함수 참조 (Logical ↔ TC)

### `_logical_to_totl_str()` (~Line 553)

```python
def _logical_to_totl_str(logical_str: str, cycle_map: dict) -> str:
    """논리 사이클 범위 → TC 범위 변환
    
    입력: "1-3" (논리 사이클 1~3)
    cycle_map으로 변환:
      사이클 1 = TC(2,6)
      사이클 2 = TC(7,11)
      사이클 3 = TC(12,16)
    출력: "2-6,7-11,12-16"
    """
```

### `_totl_to_logical_str()` (~Line 587)

```python
def _totl_to_logical_str(totl_str: str, cycle_map: dict) -> str:
    """TC 범위 → 논리 사이클 범위 변환 (역변환)
    
    입력: "33" (TC 33)
    cycle_map에서 TC 33을 포함하는 논리사이클 찾기
    출력: "7" (논리사이클 7이 TC 33을 포함)
    """
```

---

## 7. 파이프라인 데이터 흐름 요약도

```
                Raw Data Sources
    ┌──────────────┬──────────────────┐
    │ Toyo         │ PNE              │
    │ CAPACITY.LOG │ SaveEndData.csv  │
    │ (CSV, 19열)   │ (CSV, 44열)      │
    │ + 000001~N   │ + SaveData*.csv  │
    │   (바이너리)   │ + .cyc (바이너리) │
    └──────┬───────┴──────┬───────────┘
           │              │
           ▼              ▼
    ┌──────────────────────────────┐
    │  TC별 요약 데이터 (스텝 끝)     │
    │  TotlCycle, Condition,        │
    │  Cap, Voltage, Temp, Finish   │
    └──────────────┬───────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │  다단 스텝 병합                │
    │  연속 동일 Condition 그룹      │
    │  → 용량 합산, 전압 가중평균     │
    └──────────────┬───────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │  cycle_map 생성               │
    │  TC들 → 논리사이클 그룹화       │
    │  {1: {all:(2,6), chg:[...],  │
    │       dchg:[...], ...}}       │
    └──────────────┬───────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │  df.NewData 구성              │
    │  Cycle | Dchg | Chg | Eff |  │
    │  RndV | AvgV | Temp |        │
    │  OriCyc | dcir | ...         │
    │  (각 행 = 1 논리사이클)         │
    └──────────────┬───────────────┘
                   │
          ┌────────┴────────┐
          │                 │
          ▼                 ▼
    ┌────────────┐   ┌────────────────┐
    │ 사이클 분석  │   │ 프로필 분석      │
    │ X축=논리사이클│   │ X축=시간/SOC    │
    │ 6-subplot   │   │ 시계열 그래프    │
    │ (Dchg,Eff,  │   │ (V, I, T vs t) │
    │  Temp,DCIR, │   │                │
    │  Eff2,V)    │   │                │
    └────────────┘   └────────────────┘
```

---

## 8. 용어 정리 (Quick Reference)

| 용어              | 의미                                           | 코드 변수              |
|:-----------------|:-----------------------------------------------|:---------------------|
| **TC**           | TotlCycle, 충방전기 물리 사이클 번호                 | `TotlCycle`, `OriCyc`|
| **논리 사이클**    | cycle_map이 정의한 의미 있는 1회 충방전              | `Cycle` in NewData   |
| **Condition**    | 1=충전, 2=방전                                    | `Condition`, `Cond`  |
| **Mode**         | 패턴 내 스텝 번호 (Toyo)                           | `Mode`               |
| **Finish**       | 종료 조건 (Vol=전압한계, Cur=전류컷오프)              | `Finish`             |
| **cycle_map**    | {논리사이클번호: {all, chg, dchg, ...}} 딕셔너리     | `df.cycle_map`       |
| **link_mode**    | 다중 경로 연결 처리 모드                             | `chk_link_cycle`     |
| **ECT mode**     | ECT 프로필 추출 모드 (TC 직접 지정)                  | `chk_ectpath`        |
| **cycle 열**     | 경로 테이블의 논리 사이클 필터                         | column index 4       |
| **cycleraw 열**  | 경로 테이블의 TC 필터 (ECT용)                        | column index 5       |
| **df.NewData**   | 논리사이클별 요약 DataFrame                          | `df.NewData`         |
| **threshold**    | 유효 사이클 판별 용량 기준 (공칭/60)                  | `cap_threshold`      |

---

## 관련 문서

- [[260318_cycle_unified_refactor]] — 통합 전/후 구조 정비
- [[260405_review_cycle_and_profile_analysis_logic]] — 사이클/프로필 로직 설명서
- [[260411_analysis_cycle_concepts_unification]] — 4가지 사이클 개념 분리
- [[260411_analysis_cycle_pipeline_complete]] — 파이프라인 완성
- [[260412_cycle_pipeline_refactor]] — 이후 리팩토링
