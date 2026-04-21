# 사이클 데이터 파이프라인 완전 분석

> **작성일**: 2026-04-11
> **목적**: 경로 입력 → TC 사이클 → 논리사이클 → UI 입력 사이클 → UI 사이클 바까지 전체 파이프라인 분석
> **대상 파일**: `DataTool_dev/DataTool_optRCD_proto_.py` (29,196줄)

---

## 1. 전체 파이프라인 개요

```
┌─────────────────────────────────────────────────────────────────┐
│  Stage 0: 경로 입력                                              │
│  ─ Path 파일 로드 / 수동 입력 / 폴더 선택                         │
│  ─ cycle_path_table (7열) 채워짐                                  │
│  ─ _autofill_table_empty_cells() → 용량·채널·사이클 자동 산정      │
├─────────────────────────────────────────────────────────────────┤
│  Stage 1: 실행 트리거 (cycle_confirm 버튼)                        │
│  ─ _parse_cycle_input() → list[CycleGroup] 생성                  │
│  ─ 개별/연결/ECT 모드 분기                                        │
├─────────────────────────────────────────────────────────────────┤
│  Stage 2: Phase 0 — 채널 메타데이터                               │
│  ─ check_cycler() → PNE/Toyo 판별                                │
│  ─ cycle_map 빌드 (논리↔물리 매핑)                                │
│  ─ ChannelMeta 캐시                                               │
├─────────────────────────────────────────────────────────────────┤
│  Stage 3: Phase 1/2 — 데이터 로딩 & 처리                         │
│  ─ toyo_cycle_data() 또는 pne_cycle_data()                       │
│  ─ Cycleraw → 병합 → Pivot → df.NewData 생성                    │
├─────────────────────────────────────────────────────────────────┤
│  Stage 4: Phase 3 — 논리사이클 리매핑                             │
│  ─ TotlCycle → Logical Cycle 변환                                │
│  ─ UI 입력 범위 ("1-100") 적용                                   │
├─────────────────────────────────────────────────────────────────┤
│  Stage 5: Phase 4/5 — 그래프 출력 & 엑셀 저장                    │
│  ─ graph_output_cycle() → 6개 서브플롯                           │
│  ─ cycle_tab에 탭 추가                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 핵심 개념 정의

### 2.1 TotlCycle (TC, 물리사이클)

**정의**: 충방전기 하드웨어가 자동 부여하는 순차 번호. 충전/방전/휴지 각각이 별도 TC를 가짐.

**PNE**: SaveEndData의 28번째 컬럼 (0-indexed col 27). 각 스텝 종료 시 TC 증가.
**Toyo**: CAPACITY.LOG의 `TotlCycle` 컬럼. 각 Condition(충전/방전/휴지) 전환 시 TC 증가.

```
예: 1C 충방전 수명시험 (PNE)
TC 1: CC 충전 → TC 2: CV 충전 → TC 3: Rest → TC 4: CC 방전 → TC 5: Rest
TC 6: CC 충전 → TC 7: CV 충전 → TC 8: Rest → TC 9: CC 방전 → TC 10: Rest
...
→ 1개 풀사이클 = TC 5개 소모
→ 100사이클 시험 = TC 500개
```

### 2.2 논리사이클 (Logical Cycle)

**정의**: BDT가 정의하는 "의미 있는 단위 사이클". 사용자가 인식하는 사이클 번호.

```
논리사이클 1 = TC 1~5 (충전+CV+Rest+방전+Rest)
논리사이클 2 = TC 6~10
...
논리사이클 100 = TC 496~500
```

**cycle_map 구조**:
```python
cycle_map = {
    1: {'all': (1, 5),   'chg': [1, 2], 'dchg': [4], 'chg_rest': [3], 'dchg_rest': [5]},
    2: {'all': (6, 10),  'chg': [6, 7], 'dchg': [9], 'chg_rest': [8], 'dchg_rest': [10]},
    # ...
}
```

### 2.3 UI 입력 사이클 (User Cycle Input)

**정의**: 사용자가 테이블 col 4 ("사이클")에 입력하는 범위 문자열.

- **논리사이클 기준**: `"1-100"` = 논리사이클 1~100번
- **회색 힌트**: 자동 산정값 (예: `"1-496"`) — 사용자 미입력 시 표시
- **검은 글씨**: 사용자 수동 입력값 — 자동값보다 우선

### 2.4 UI 사이클 바 (Cycle Range Display)

**정의**: 그래프 X축에 표시되는 사이클 범위. df.NewData의 인덱스.

- `tcyclerng`: X축 범위 (cycle 수)
- `tcyclerngyhl` / `tcyclerngyll`: Y축 상한/하한 (용량비 %)

---

## 3. 상세 파이프라인

### 3.1 Stage 0: 경로 입력

#### 3.1.1 cycle_path_table 구조 (7열)

| Col | 헤더 | 역할 | 자동채움 | 비고 |
|-----|------|------|---------|------|
| 0 | 시험명 | 범례/탭 표시명 | ✅ 경로명 파싱 | 30자 초과 시 축약 |
| 1 | 경로(필수입력) | 데이터 폴더 절대경로 | ❌ | 유일한 필수 입력 |
| 2 | 채널 | 채널 필터 (`"032,073"`) | ✅ scandir | 빈칸=전채널 |
| 3 | 용량 | 공칭용량 (mAh) | ✅ 3단계 추정 | 자동: name→meta→I/O |
| 4 | 사이클 | **논리사이클** 범위 | ✅ 회색힌트 | `"1-100"` 형식 |
| 5 | Raw | **TotlCycle** 범위 | ✅ 회색힌트 | cycle_map max TC |
| 6 | 모드 | ECT 모드 코드 | ❌ 수동 | DCH/CYC/RGE 등 |

#### 3.1.2 _autofill_table_empty_cells() 산정 로직

```
Pass 1: 각 행별 자동값 산정
─────────────────────────────────────
경로명(col 0):
  basename 파싱 → "mAh_" 뒤 부분 추출 → 30자 제한

채널(col 2):
  scandir(path) → _is_channel_folder() 필터 → 괄호 내 번호 추출
  예: M01Ch005[005] → "005"

용량(col 3): 3단계 우선순위
  1. 힌트(기존값) + name_capacity() 교차검증 (10% 이내 = 유효)
  2. ChannelMeta 캐시 (Phase 0 결과)
  3. name_capacity(path) → 경로명에서 "NNNNmAh" 추출
  4. pne_min_cap() / toyo_min_cap() → 실제 I/O

사이클(col 4): 최대 논리사이클 추정
  1. ChannelMeta.max_logical_cycle (캐시)
  2. _quick_max_cycle(path, capacity) → cycle_map 빌드
  → 결과를 "1-{max}" 형태로 회색 힌트 표시

Raw(col 5): 최대 TotlCycle 추정
  1. cycle_map의 max(val['all'][1]) 계산
  → "1-{max_tc}" 형태로 회색 힌트 표시

Pass 2: 셀 채우기 (연결모드 시 그룹 내 중복 제거)
─────────────────────────────────────
- 빈 셀 → 자동값으로 채움
- 기존값 ≠ 자동값 → 기존값 유지, bold 표시
- 연결모드: 첫 행에만 경로명 표시, 후속 행 중복 생략
- 사이클(col 4): 연결모드 첫 행 = 그룹 내 전 경로 사이클 합산
```

#### 3.1.3 Path 파일 로드 (_load_path_file_to_table)

```
4가지 헤더 포맷 자동감지:
━━━━━━━━━━━━━━━━━━━━━━━━━━
신규:  cyclename / cyclepath / channel / capacity / cycle / mode / cycleraw
이전1: name / path / channel / capacity / cycle / mode / cycleraw
이전2: name / path / channel / capacity
이전3: [탭 구분] name / path / ...
이전4: [드라이브 문자 감지] D:\... 형태

메타데이터:
  #link_mode=1  → chk_link_cycle 체크
  #ect_mode=1   → chk_ectpath 체크
```

### 3.2 Stage 1: _parse_cycle_input() — CycleGroup 생성

```
┌─ 테이블 데이터 있음? ─┐
│  YES                    │  NO → 파일/폴더 선택 다이얼로그
├─────────────────────────┤
│  연결모드? ─────────────┼──── NO → 각 행 = 개별 CycleGroup
│  YES                    │
│  ↓                      │
│  빈 행으로 그룹 분리    │
│  그룹 내: txt/xls 분리  │
│  폴더 = 통합 CycleGroup │
│  txt = file_idx별 분리  │
└─────────────────────────┘

CycleGroup 필드:
  name: str                    # 범례/탭명
  paths: list[str]             # 데이터 경로 목록
  path_names: list[str]        # per-path cyclename
  is_link: bool                # 연결 여부
  data_type: 'folder' | 'excel'
  per_path_channels: list      # [[ch1,ch2], [ch3]] 경로별 채널
  per_path_capacities: list    # [1689, 1689] 경로별 용량
  channel_link_map: dict       # 위치 기반 채널 매핑
```

### 3.3 Stage 2: Phase 0 — 채널 메타데이터

#### 3.3.1 check_cycler() — 사이클러 판별

```python
def check_cycler(raw_file_path) -> bool:  # True=PNE, False=Toyo
    # 1. Pattern 폴더 존재 → PNE
    # 2. Restore/SaveData CSV 존재 → PNE (Pattern-less GITT fallback)
    # 3. 그 외 → Toyo
```

#### 3.3.2 cycle_map 빌드

**PNE: pne_build_cycle_map()**
```
1. SaveEndData 로드 → TotlCycle × Condition pivot
2. 모드 감지 (general vs sweep):
   ─ sig_ratio ≥ 0.5 AND has_both_ratio ≥ 0.3 → general (1:1)
   ─ 그 외 → sweep (GITT/DCIR 펄스)
   ─ TC ≤ 5 → 강제 general (저장/소규모)

General 모드:
  TC N → 논리사이클 N (1:1 매핑)

Sweep 모드 (_pne_build_sweep_cycle_map):
  1. 유의 임계값 = max_tc_cap × 0.5
  2. TC 분류: 유의(significant) vs 비유의(insignificant)
  3. 유의 TC = 개별 논리사이클
  4. 비유의 TC = 방향(CHG/DCHG)별 그룹핑
  5. 인접 반대 방향 스윕 병합 → 1 논리사이클
```

**Toyo: toyo_build_cycle_map()**
```
1. CAPACITY.LOG 로드
2. 연속 동일 Condition 행 병합 (다단 CC 충전 → 1 그룹)
3. 유효 방전 식별: Condition==2 AND Cap > mincapacity/60
4. 2-pass 논리사이클 구축:
   Pass 1: 유효 방전 기준으로 충전→방전→휴지 묶음
   Pass 2: 독립 충전 (충전만 있고 방전 없는 그룹)
```

#### 3.3.3 ChannelMeta 생성 & 캐시

```python
@dataclass
class ChannelMeta:
    channel_path: str          # 채널 폴더 절대경로
    parent_path: str           # 상위 경로
    cycler: str                # 'PNE' | 'Toyo'
    is_pne: bool
    min_capacity: float        # 확정 공칭용량 (mAh)
    capacity_source: str       # 'table' | 'path_name' | 'file' | 'auto'
    sch_file: str | None       # .sch/.ptn 파일 경로
    sch_parsed: dict | None    # 스케줄 파싱 원본
    schedule_struct: dict | None  # 구조화된 스케줄
    classified: list | None    # 사이클 분류 결과
    cycle_map: dict | None     # 논리↔물리 매핑
    max_logical_cycle: int | None  # 최대 논리사이클
```

### 3.4 Stage 3: Phase 1/2 — 데이터 로딩

#### 3.4.1 Toyo 데이터 흐름 (toyo_cycle_data)

```
CAPACITY.LOG (CSV)
  ↓ toyo_cycle_import()
Cycleraw DataFrame (TotlCycle, Condition, Cap, Pow, Ocv, Temp, Finish, OriCycle)
  ↓ OriCycle 보존 (원본 TotlCycle)
  ↓ 고아 방전 제거 (첫 행이 Condition==2면 삭제)
  ↓ 연속 동일 Condition 병합 (merge_group)
     └─ 충전: Cap 합산, Ocv 마지막값
     └─ 방전: Cap 합산, AveVolt 재계산, Temp 최대값
  ↓ 유효 필터링 (Cap > mincapacity/60)
  ↓ Chg/Dchg 추출
  ↓ DCIR 계산 (선택)
  ↓ 효율 계산 (Eff = Dchg/Chg, Eff2 = Chg(n+1)/Dchg(n))
  ↓
df.NewData (10+ 컬럼)
```

#### 3.4.2 PNE 데이터 흐름 (pne_cycle_data → _process_pne_cycleraw)

```
SaveEndData.csv (이진 CSV)
  ↓ _cached_pne_restore_files()
Cycleraw DataFrame (TotlCycle, Condition, chgCap, DchgCap, Ocv, imp, volmax, ...)
  ↓ 코인셀 단위 변환 (PNE21/22: μAh → mAh, ÷1000)
  ↓ DCIR 계산 (3 모드):
     └─ chkir: 단순 펄스 (volmax > 4.1V 시 방전)
     └─ mkdcir: RSS + 1s 펄스 (3-step DCIR)
     └─ default: steptime ≤ 6000s 펄스
  ↓ Pivot Table (TotlCycle × Condition)
     └─ chgCap: Condition==1의 합
     └─ DchgCap: Condition==2의 합
     └─ Ocv: Condition==3의 min (Rest End Voltage)
     └─ Temp: Condition==2의 max
  ↓ 정규화 (mincapacity × 1000 기준)
  ↓ cycle_map 리매핑 (TC → 논리사이클)
  ↓
df.NewData (10+ 컬럼)
```

### 3.5 Stage 4: 논리사이클 리매핑

```
df.NewData 생성 시점에서 리매핑 실행:

1. cycle_map 없는 경우:
   X축 인덱스 = 순차 (1, 2, 3, ...) = 물리적 유효 사이클 순서
   OriCyc = 원본 TotlCycle

2. cycle_map 있는 경우 (PNE):
   ─ 물리 TotlCycle → 논리 Cycle 번호로 치환
   ─ 매핑 안 되는 TC 행은 삭제
   ─ sweep 모드: 여러 TC → 1 논리사이클로 축소
   ─ Cycle 컬럼 추가, PhysicalCycle 보존

3. UI 입력 사이클 범위 적용:
   ─ 사용자 입력: "1-50" → 논리사이클 1~50만 필터링
   ─ _logical_to_totl_str(cycle_map, "1-50") → 실제 TC 범위 변환
   ─ 해당 TC 범위의 데이터만 로드
```

### 3.6 Stage 5: 그래프 출력

#### 3.6.1 graph_output_cycle() — 6개 서브플롯

```
ax1: 방전용량비 (Dchg)     ─ X: Cycle, Y: % (ylimitlow ~ ylimithigh)
ax2: 효율 (Eff)            ─ X: Cycle, Y: 0.992~1.004
ax3: 온도 (Temp)            ─ X: Cycle, Y: °C (0~50)
ax4: DCIR (dcir/dcir2)      ─ X: Cycle, Y: mΩ (0~irscale)
ax5: 역효율 (Eff2)          ─ X: Cycle, Y: ratio
ax6: 전압 (RndV+AvgV)       ─ X: Cycle, Y: V (3.0~4.0)
```

#### 3.6.2 X축 = df.NewData 인덱스 (논리사이클)

```
X축 값 계산:
  x = df.NewData.index * xscale

  xscale = float(tcyclerng) if 입력값 있음 else 1.0

  tcyclerng: 사이클 스케일링 팩터
    ─ 기본값: 1 (1사이클 = 1 X단위)
    ─ 커스텀: 예) 0.5 (2사이클마다 1 X단위)
```

---

## 4. 사이클 번호 변환 함수 상세

### 4.1 _logical_to_totl_str()

```
입력: cycle_map, cycle_str="1-3"
처리:
  논리 1 → cycle_map[1]['all'] = (10, 10) → TC 10
  논리 2 → cycle_map[2]['all'] = (11, 11) → TC 11
  논리 3 → cycle_map[3]['all'] = (12, 18) → TC 12~18
출력: "10-18"
```

**사용 위치**: UI 사이클 입력 → 실제 데이터 로딩 범위 결정

### 4.2 _totl_to_logical_str()

```
입력: cycle_map, raw_str="10-18, 25"
처리:
  TC 10 → 역매핑 → 논리 1
  TC 11 → 역매핑 → 논리 2
  TC 12~18 → 역매핑 → 논리 3
  TC 25 → 직접 매핑 없음 → _find_nearest_logical()로 가장 가까운 논리사이클
출력: "1-3, 5" (예시)
```

**사용 위치**: ECT 다중 경로에서 Raw TC 입력 → 논리사이클 표시

### 4.3 갭 TC 처리 전략

```
cycle_map 범위 사이의 갭에 있는 TC:
  ─ 범위 내부: 가장 가까운 논리사이클에 할당
  ─ 범위 밖 (min 미만): 첫 논리사이클로 클램핑
  ─ 범위 밖 (max 초과): 마지막 논리사이클로 클램핑

목적: ECT 다중 경로에서 경로별 max TC가 다를 때 빈칸 방지
```

---

## 5. 실험 데이터 분석 (data/exp_data)

### 5.1 폴더 네이밍 규칙

```
YYMMDD_YYMMDD_NN_이름_용량mAh_설명

시작일_종료일_연구원ID_연구원명_공칭용량_시험타입

예:
250207_250307_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 1-100cyc
260326_260329_00_류성택_4860mAh_A17 ATL ECT parameter1
```

### 5.2 PNE 데이터 구조 (127개 폴더)

```
[폴더명]/
├── M0*Ch###[###]/          ← 채널 폴더 (PNE 채널 번호)
│   ├── [파일명].cyc        ← 실시간 바이너리 (float32: mV, mA, mAh, s, °C)
│   ├── [파일명].sch        ← 스케줄 바이너리
│   └── Restore/
│       ├── ch##_SaveData0001~N.csv  ← 시계열 데이터 (int: μV, μA, μAh, /100s, m°C)
│       ├── ch##_SaveEndData.csv     ← 스텝 종료 요약 (1 row/step)
│       └── savingFileIndex_*.csv    ← 파일 인덱스 메타
└── Pattern/                ← 패턴 폴더 (비어있거나 패턴 데이터)
```

**핵심**: SaveEndData.csv가 cycle_map 빌드와 사이클 요약의 주 데이터 소스

### 5.3 Toyo 데이터 구조 (7개 폴더)

```
[폴더명]/
├── 30/ (또는 31, 32 등)    ← 채널 번호 폴더
│   ├── CAPACITY.LOG        ← 사이클 요약 (TSV)
│   ├── 000001 ~ 000496     ← 사이클별 시계열 파일
│   ├── [이름].PTN           ← 패턴 파일
│   └── CHCMT.TXT           ← 채널 메타
└── Pattern/
```

**CAPACITY.LOG 컬럼**:
```
Date, Time, Condition, Mode, Cycle, TotlCycle, Cap[mAh], PassTime,
TotlPassTime, Pow[mWh], AveVolt[V], PeakVolt[V], PeakTemp[Deg], Ocv, Finish
```

### 5.4 ECT 데이터 특성 (61개 폴더)

```
ECT (Electrochemical-Thermal) 파라미터 시험:
─ 동일 셀 설계에 대해 8~10개 파라미터 변형
─ 각 파라미터 = 별도 폴더 (별도 채널)
─ 온도 변형: RT, HT(45°C), LT
─ 재측정: "45재측정" 접미사

구조: PNE 타입과 동일
특이점: 다중 경로를 ECT 모드로 묶어 분석
```

### 5.5 시험 유형별 TC/논리사이클 관계

| 시험 유형 | TC 패턴 | TC/논리사이클 비율 | 예시 |
|----------|---------|-------------------|------|
| **수명시험 (CC-CV)** | CC충→CV충→Rest→CC방→Rest | 5:1 | 100cyc = TC 500 |
| **수명시험 (CC only)** | CC충→CC방→Rest | 3:1 | 100cyc = TC 300 |
| **GITT** | (Rest→Pulse)×N | 수십:1 | 1회 = TC 50~200 |
| **DCIR** | SOC별 펄스 | 다대1 (sweep) | 10 SOC점 = TC 30~50 |
| **ECT parameter** | 파라미터별 반복 | 다양 | 파라미터별 TC 범위 상이 |
| **Rate capability** | C-rate별 방전 | 다대1 | 5 C-rate = TC 15~25 |
| **저장수명 (Floating)** | 장시간 Rest → 측정 | 비정기 | 월 1회 = TC 3~5 |

---

## 6. df.NewData 컬럼 상세

### 6.1 공통 컬럼 (PNE + Toyo)

| 컬럼 | 단위 | 계산식 | 물리적 의미 |
|------|------|--------|------------|
| **Dchg** | % (비율) | DchgCap / (mincapacity × 1000) | 방전용량비 (기준용량 대비) |
| **Chg** | % (비율) | ChgCap / (mincapacity × 1000) | 충전용량비 |
| **Eff** | 무차원 | Dchg / Chg | 쿨롱효율 (같은 사이클) |
| **Eff2** | 무차원 | Chg(n+1) / Dchg(n) | 교차 쿨롱효율 |
| **RndV** | V | Rest End Voltage / 1,000,000 (PNE) | 충전 후 휴지전압 ≈ OCV |
| **AvgV** | V | DchgEng / Dchg / mincapacity × 1000 | 평균 방전전압 |
| **DchgEng** | Wh | 방전 에너지 | 방전 에너지 |
| **Temp** | °C | 방전 중 최고 온도 | 셀 표면 온도 |
| **OriCyc** | int | 원본 TotlCycle | 원시 데이터 역추적용 |

### 6.2 DCIR 모드별 추가 컬럼

| 모드 | 추가 컬럼 | 계산 |
|------|----------|------|
| **default** | `dcir` | (Vmax - Vmin) / Imax × 1,000,000 [μΩ→mΩ] |
| **chkir** (단순) | `dcir` | volmax > 4.1V 조건 방전 펄스 |
| **mkdcir** (RSS+1s) | `dcir`, `dcir2`, `rssocv`, `rssccv` | 3-step 복합 DCIR |
| **soc70** | `soc70_dcir`, `soc70_rss_dcir` | SOC 70% 지점 DCIR |

### 6.3 인덱스 구조

```
기본: 순차 정수 인덱스 (0, 1, 2, ...)
  ─ reset_index() 호출 → 논리사이클 순서
  ─ 그래프 X축에 직접 사용

cycle_map 적용 시:
  ─ Cycle 컬럼 추가 (논리사이클 번호)
  ─ PhysicalCycle 컬럼 추가 (원본 TC)
  ─ 인덱스는 여전히 순차 (0, 1, 2, ...)
```

---

## 7. 모드별 동작 차이

### 7.1 개별 모드 (chk_link_cycle OFF)

```
각 테이블 행 = 독립 CycleGroup
  ─ 별도 figure, 별도 탭
  ─ 사이클 번호 독립 (1부터 시작)
  ─ 색상 팔레트 행별 독립
```

### 7.2 연결 모드 (chk_link_cycle ON)

```
빈 행으로 구분된 그룹 = 1 CycleGroup
  ─ 그룹 내 모든 경로 통합 figure
  ─ 사이클 연속 번호 (경로1: 1-100, 경로2: 101-200)
  ─ 동일 채널은 단일 범례 색상

사이클 합산: 첫 행에 그룹 전체 누적 표시
  예: 경로1 max=100, 경로2 max=200 → 첫 행 "1-300"
```

### 7.3 ECT 모드 (chk_ectpath ON)

```
다중 파라미터 경로를 ECT 분석용으로 묶음
  ─ 빈 경로 셀 forward-fill (같은 그룹 내)
  ─ 모드 컬럼(col 6) 활성화: DCH, CYC, RGE 등
  ─ TotlCycle(Raw) 범위 사용 가능
  ─ _totl_to_logical_str()로 Raw→논리 변환
```

---

## 8. 주요 캐싱 계층

```
Layer 1: _channel_meta_store (ChannelMeta)
  ─ 키: channel_path (절대 경로)
  ─ 유효성: _meta_fingerprint (경로+용량 해시)
  ─ 포함: cycler, capacity, cycle_map, classified, ...

Layer 2: _cached_pne_restore_files() (SaveEndData)
  ─ PNE 채널별 캐시
  ─ .cyc 보충 포함 (최신 데이터 보정)

Layer 3: _get_pne_cycle_map() (cycle_map)
  ─ (channel_path, capacity, crate) → (cycle_map, capacity)
  ─ _get_pne_sch_struct() 연동 (.sch 파싱 재사용)

Layer 4: _path_cache (autofill용)
  ─ 동일 경로 중복 스캔 방지 (세션 내)

무효화: _reset_all_caches() → 새 데이터 로드 전 호출
```

---

## 9. 현재 로직의 관찰 사항 및 정비 포인트

### 9.1 아키텍처 관찰

| # | 관찰 | 영향 |
|---|------|------|
| 1 | **cycle_map 이중 생성**: autofill에서 1회, Phase 0에서 1회 = 같은 연산 2번 | 성능 낭비 |
| 2 | **Toyo/PNE 분기가 파이프라인 곳곳에 분산**: check_cycler() 호출이 10+ 위치 | 유지보수 어려움 |
| 3 | **df.NewData 컬럼이 모드에 따라 가변**: dcir, dcir2, soc70_dcir 등 조건부 존재 | 하류 코드에서 hasattr/try 필요 |
| 4 | **논리사이클 ↔ TC 변환이 양방향 함수 2개**: 역매핑 시 갭 TC 추정 로직 복잡 | 엣지케이스 버그 가능성 |
| 5 | **sweep 모드 감지 휴리스틱**: sig_ratio, has_both_ratio 기반 = 경계값 의존 | 특이 시험 패턴에서 오분류 |
| 6 | **연결 모드 사이클 합산**: 단순 합산 (경로1 max + 경로2 max) = 겹치는 경우 과대추정 | 드물지만 가능 |
| 7 | **용량 산정 3단계**: name→meta→I/O 우선순위 명확하나 경로명 파싱 regex 제한적 | "4-187mAh" 같은 특수 형태 |

### 9.2 데이터 흐름 병목

```
1. SaveEndData I/O (PNE): 대용량 CSV 반복 읽기
   → 캐시로 해결되었으나, 첫 로드 시 느림

2. cycle_map 빌드 (PNE sweep 모드): pivot + 분류 + 그룹핑
   → O(n²) 가능성 (TC 수 × 논리사이클 수)

3. Toyo Condition 병합: 연속 동일 Condition 감지
   → pd.DataFrame 조작 비용 (groupby + agg)

4. DCIR 계산 (mkdcir 모드): 3-step 펄스 패턴 매칭
   → 복잡한 조건 분기, 디버깅 어려움
```

### 9.3 사이클 번호 체계의 혼선 위험

```
사용자 관점:
  "사이클 50" = 50번째 충방전

코드 내부:
  ─ TotlCycle 50 ≠ 논리사이클 50 (TC 5개/사이클이면 논리 10)
  ─ df.NewData 인덱스 50 ≠ 논리사이클 50 (필터링 후 재인덱싱)
  ─ OriCyc 50 = 원본 TC 50 (역추적용)

잠재 혼선:
  1. UI 사이클 입력 = 논리사이클 (cycle_map 기준)
  2. UI Raw 입력 = TotlCycle (물리)
  3. graph X축 = df.NewData 인덱스 × xscale
  4. Excel 출력 = df.NewData 인덱스 (1-based)
  5. OriCyc = 원본 TC (디버깅/역추적용)
```

---

## 10. 용어 정리

| 용어 | 코드 변수 | 의미 |
|------|----------|------|
| TotlCycle (TC) | `TotlCycle`, col 27 | 충방전기 물리 스텝 번호 |
| 논리사이클 | `cycle_map` key, `Cycle` col | BDT 정의 의미 단위 사이클 |
| OriCyc | `df.NewData['OriCyc']` | 원본 TC (역추적용) |
| UI 사이클 | `cycle_path_table` col 4 | 사용자 입력 논리사이클 범위 |
| UI Raw | `cycle_path_table` col 5 | 사용자 입력 TC 범위 |
| X축 사이클 | `df.NewData.index * xscale` | 그래프 표시 사이클 |
| cycle_map | `{ln: {'all':..}}` | 논리↔TC 매핑 딕셔너리 |
| CycleGroup | dataclass | 분석 단위 그룹 (경로+메타) |
| ChannelMeta | dataclass | 채널별 메타 캐시 |
