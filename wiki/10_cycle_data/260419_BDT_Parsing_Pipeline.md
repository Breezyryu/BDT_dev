---
relocated: 2026-04-22
source_vault: "docs/vault/04_Development/260419_BDT_Parsing_Pipeline.md"
tags:
  - bdt
  - pipeline
  - parsing
  - pandas
created: 2026-04-19
aliases:
  - BDT 파싱 파이프라인
  - Parsing Pipeline Trace
---

# BDT 파싱 파이프라인 — 사이클 분석 vs 프로파일 분석

사이클 분석과 프로파일 분석이 **동일한 원시 데이터와 Phase 0 캐시**를 공유하지만, 출력 레이어에서 분기하여 완전히 다른 형태의 DataFrame을 만든다. 각 단계에서 pandas DataFrame이 어떻게 변형되는지 추적한다.

## 공통 골격

```
┌────────────── 입력 (채널 폴더) ──────────────┐
│  PNE: Restore/SaveData*.csv (바이너리형 CSV)  │
│  Toyo: 000001, 000002, ... (파일 = 사이클)    │
│  공통: Pattern/ 폴더 + .sch 스케줄 파일       │
└──────────────────┬───────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │  Phase 0: 메타 수집  │ ← ChannelMeta 캐시
         │  (사이클러 판별,     │
         │   용량, cycle_map)   │
         └─────────┬──────────┘
                   │
           ┌───────┴────────┐
           ▼                ▼
    ┌────────────┐    ┌────────────────┐
    │ 사이클 분석 │    │  프로파일 분석   │
    │ (요약/사이클)│    │ (시계열/샘플)    │
    └─────────────┘    └────────────────┘
```

**ChannelMeta** (`DataTool_optRCD_proto_.py:275`)
```python
ChannelMeta(
    cycler_type="PNE" | "TOYO",
    min_capacity=422.0,
    cycle_map={1: {'all': (1,1), 'chg': [1], 'dchg': [1], ...}, ...},
    classified=[...],
    max_tc=500,
)
```
두 파이프라인이 공유. 매 호출마다 재계산되지 않음.

## 1. 입력 스키마

### PNE SaveData (바이너리형 CSV)
48개 고정 컬럼, 정수형 μ 단위.

| col | 의미 | 단위 | 예 |
|---|---|---|---|
| 0 | Index | - | 1, 2, 3 |
| 1 | Stepmode (SaveEndData) | enum | 1=CCCV, 2=CC, 3=CV, 4=OCV |
| 2 | Condition | enum | 1=CHG, 2=DCHG, 3=REST, 9=CC |
| 7 | StepNo | - | 1, 2, 3 |
| 8 | Voltage | μV | 3700000 (=3.7V) |
| 9 | Current | μA | 50000 (=50mA) |
| 10 | ChgCap (per-step) | μAh | **스텝 단위 리셋!** |
| 11 | DchgCap (per-step) | μAh | **스텝 단위 리셋!** |
| 14/15 | ChgWh/DchgWh | μWh | |
| 17 | StepTime | /100s | |
| 18/19 | TotTime(day, /100s) | | |
| 21 | Temp1 | 0.1°C | |
| 27 | TotlCycle | int | 1, 2, 3 |

### Toyo (사이클당 파일)
```
Condition, TotlCycle, PassTime[Sec], Voltage[V],
Current[mA], Cap[mAh], Pow[mWh], Temp1[Deg], Ocv, AveVolt[V], PeakVolt[V]
```
값이 **이미 물리 단위**. 사이클당 한 파일이므로 TotlCycle=1로 시작.

## 2. 사이클 분석 파이프라인

사이클 **요약 통계 1행/사이클**을 만든다. 최종 DataFrame은 수십~수천 행.

### Phase 1 — 원시 로딩
- PNE: `_process_pne_cycleraw` (`DataTool_optRCD_proto_.py:8864`)
- Toyo: `toyo_cycle_data` (`DataTool_optRCD_proto_.py:3812`)

### Phase 2 — 스텝 머지 (카테고리화 첫 단계)
"연속된 같은 Condition = 한 스텝"으로 그룹핑 후 대표값 1행 생성.

Toyo 예 (`DataTool_optRCD_proto_.py:3836`):
```python
cond_series = Cycleraw["Condition"]
merge_group = ((cond_series != cond_series.shift())
               | (~cond_series.isin([1, 2]))).cumsum()
```

병합 규칙:
- CHG 행 병합 → Cap 합산, Ocv = 첫 값 유지
- DCHG 행 병합 → Cap/Pow 합산, AveVolt = Pow/Cap 재계산
- REST → 그대로 유지

결과: **수십만 행 → 사이클당 약 3~5 행** (CHG-REST-DCHG-REST)

### Phase 3 — TotlCycle → 논리사이클 매핑
cycle_map으로 TotlCycle(물리 스텝번호) → 논리사이클(BDT 의미단위) 변환.
- General 모드: 1:1 (수명 시험)
- Sweep 모드: n:1 (GITT/DCIR, 수십 TC가 한 논리사이클)

```
df["Cycle"] = 논리사이클     (UI/표시용)
df["OriCyc"] = 원본 TotlCycle (역추적)
```

### Phase 4 — 사이클별 집계 (`df.NewData`)
사이클별 그룹핑 → 1행/사이클 통계:

| 컬럼 | 단위 | 계산 |
|---|---|---|
| Chg | % | ChgCap / 공칭용량 |
| Dchg | % | DchgCap / 공칭용량 |
| Eff | - | Dchg/Chg (동일 사이클) |
| Eff2 | - | Chg(n+1)/Dchg(n) (교차효율) |
| AvgV | V | 평균 방전 전압 |
| RndV | V | 충전후 휴지 전압 (~OCV) |
| Temp | °C | 방전중 최고 온도 |
| DchgEng | Wh | |
| dcir | mΩ | RSS 기반 |
| dcir2, soc70_* | mΩ | mkdcir 모드 |
| rssocv, rssccv | V | mkdcir 모드 |

### Phase 5 — 출력
`graph_output_cycle()` 6개 서브플롯 + Excel 저장.

### DataFrame 행 수 변화
```
Phase 1:  🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦  수백만 행 (Raw)
Phase 2:  🟦🟦🟦🟦🟦                 수십만 행 (스텝 단위)
Phase 3:  🟦🟦🟦                    논리사이클 정렬
Phase 4:  🟦                        1 행 / 사이클 (nd)
```

## 3. 프로파일 분석 파이프라인

시계열 원시 해상도 유지. 1 사이클당 수천~수만 행.

`unified_profile_core` (`DataTool_optRCD_proto_.py:2171`)의 6 Stage:

### Stage 1 — 판별 + cycle_map 확보
```python
is_pne = is_pne_folder(...)           # Phase 0 캐시 hit
mincapacity = pne_min_cap(...) / toyo_min_cap(...)
cycle_map, _ = get_cycle_map(...)     # lru_cache (256)
```

### Stage 2 — 원시 로딩
`_unified_pne_load_raw` (`DataTool_optRCD_proto_.py:1084`) / `_unified_toyo_load_raw` (`DataTool_optRCD_proto_.py:1278`)

PNE 로더 출력 컬럼 (모두 `_raw` 접미사):
```
Condition, Step, Cycle,
Voltage_raw(μV), Current_raw(μA),
ChgCap_raw(μAh), DchgCap_raw(μAh),
ChgWh_raw, DchgWh_raw,
StepTime_raw, TotTime_Day, TotTime_Sec_raw(/100s),
Temp_raw(0.1°C),
+ OCV_raw, CCV_raw   (SaveEndData merge, 스텝 종료 행에만)
+ Stepmode            (SaveEndData col[1] 브로드캐스트)
+ CyclerType="PNE"
+ PhysicalCycle       (cycle_map 적용 시 원본 TotlCycle 보존)
```

### Stage 3 — 필터 + CV 제거
`_unified_filter_condition` (`DataTool_optRCD_proto_.py:1554`)

카테고리화 규칙:

| data_scope | 유지할 Condition |
|---|---|
| charge | 1 |
| discharge | 2 |
| cycle | 1, 2 |

추가:
- 인터펄스 휴지 (target-REST-target 패턴) 무조건 포함
- 경계 휴지 (include_rest 옵션)
- CV 구간 제거 (include_cv=False 시):
  - Stepmode=3 (순수 CV) → 스텝 전체 제외
  - Stepmode=1 (CC-CV) → CC 구간만 유지 (max_V − 5mV 경계)
- PNE Condition=9 (CC 방향 미구분)는 전류 부호로 1/2 재분류

### Stage 4 — 정규화
`_unified_normalize_pne` (`DataTool_optRCD_proto_.py:1390`) / `_unified_normalize_toyo` (`DataTool_optRCD_proto_.py:1470`)

μ 단위 → 물리 단위 + ChgCap/DchgCap을 **mincapacity 대비 0~1 분율**로.
```
cap_divisor = mincap × 1_000_000  (is_micro_unit=True)
            = mincap × 1_000      (아닐 때)
ChgCap = ChgCap_raw / cap_divisor     → 0~1
DchgCap = DchgCap_raw / cap_divisor   → 0~1
Voltage = Voltage_raw / 1_000_000     → V
Current_mA = Current_raw / 1000       → mA
Crate = Current_mA / mincapacity
Time_s = TotTime_Day × 86400 + TotTime_Sec_raw/100
Temp = Temp_raw / 10                  → °C
OCV/CCV = OCV_raw/CCV_raw / 1e6       → V
```

### Stage 5 — 스텝 병합 (누적)
`_unified_merge_steps` (`DataTool_optRCD_proto_.py:1794`)

PNE의 ChgCap/DchgCap는 **스텝 단위로 리셋**되므로 사이클 전체 누적을 만들기 위해 오프셋 적용:
```
CHG step 1: ChgCap 0→0.05  (per-step)
CHG step 2: 0→0.03
  ↓ offset 적용
CHG step 1: 0→0.05
CHG step 2: 0.05→0.08      (offset=0.05 더함)
```

**ffill 단계** (260419 추가):
- 소속 condition 행만 anchor로 두고 시간순 ffill
- REST·DCHG 행의 ChgCap = 직전 CHG의 누적값 상속
- REST·CHG 행의 DchgCap = 직전 DCHG의 누적값 상속
- → 모든 행이 "시점까지의 누적 Chg/Dchg" 보유

### Stage 6 — 축 계산 + Cutoff + dQ/dV
`_unified_calculate_axis` (`DataTool_optRCD_proto_.py:2075`)

overlap 분기:
- continuous → Time_s 시작점만 0 보정
- split → Cycle/Condition별 Time_s 리셋 + NaN 경계
- sequential → 사이클별 리셋, CHG→DCHG 순차
- connected → 히스테리시스 (충전 끝=방전 시작)

SOC 계산:

| scope × axis × overlap | SOC 공식 |
|---|---|
| charge | ChgCap (0~1) |
| discharge | DchgCap (0~1, DOD) |
| cycle+soc+split | Condition별 각각 ChgCap/DchgCap |
| cycle+soc+connected | 히스테리시스 루프 |
| cycle+time | ChgCap − DchgCap |

Cutoff 의미 (scope × axis):
- charge + soc → Voltage ≥ cutoff (Chg 프로파일, V 하한)
- charge + time → Crate ≥ cutoff (Step/Rate, 저율 제외)
- discharge → Voltage ≥ cutoff

### 최종 출력 — `UnifiedProfileResult`
```python
UnifiedProfileResult(
    df=pd.DataFrame(...),       # 시계열 샘플 (수천~수만 행)
    mincapacity=422.0,
    columns=[...],
    cycfile_soc=pd.DataFrame(...), # OCV/CCV vs SOC 요약 (있을 때만)
    metadata={...}
)
```

df 컬럼 (옵션별 가변):
- base: TimeMin, SOC, Voltage, Crate, Temp, Vol, Cycle, Condition
- + dQdV: Energy, dQdV, dVdQ
- + continuous: TimeSec, Curr
- + OCV/CCV 있을 때: OCV, CCV

## 4. 두 파이프라인 비교표

| | 사이클 분석 | 프로파일 분석 |
|---|---|---|
| Stage 1 (raw) | 수백만 행, 48컬럼 (PNE) | 동일 (공유 로더) |
| Stage 2 (filter/카테고리화) | 연속 Condition 그룹 병합 → 스텝당 1행 | scope별 Condition 필터 → 수만 행 유지 |
| Stage 3 (정규화) | 단위 변환 + Cap 합산 | μ → V/mA + 0~1 분율 |
| Stage 4 (병합) | 사이클 단위 집계 (1행/사이클) | 스텝 오프셋 + ffill 누적 |
| Stage 5 (파생) | Eff, DCIR, RndV | TimeMin, SOC, dQ/dV |
| 최종 | `df.NewData` (수천 행) | `UnifiedProfileResult.df` (수만 행) |

## 5. 캐시 계층 (공유)

| 캐시 | 키 | 용도 |
|---|---|---|
| `lru_cache(256)` `_get_pne_cycle_map` | (path, cap, crate) | PNE 사이클맵 |
| `lru_cache(256)` `_get_toyo_cycle_map` | (path, cap, crate) | Toyo 사이클맵 |
| `lru_cache(256)` `_get_pne_sch_struct` | (path, cap) | .sch 구조 |
| `lru_cache(128)` `_find_sch_file` | (path,) | .sch 경로 |
| dict `_channel_meta_store` | path | ChannelMeta |
| dict `_channel_cache` | path | I/O 버퍼 |

두 파이프라인 모두 `_reset_all_caches()`로 일괄 초기화. Phase 0 이후 동일 세션에서 재분석 시 I/O 없이 Stage 2부터 시작 가능.

## 6. 단계별 추적 — 디버그 유틸

`DataTool_optRCD_proto_.py`에 `_DEBUG_PROFILE_TRACE` 플래그가 있다. 런타임에 True로 켜면 각 Stage의 DataFrame을 pickle로 저장한다.

```python
import DataTool_dev_code.DataTool_optRCD_proto_ as bdt
bdt._DEBUG_PROFILE_TRACE = True
bdt._DEBUG_TRACE_DIR = r"C:\tmp\bdt_trace"   # 저장 경로 (선택)
# GUI에서 프로파일 분석 1회 실행
# 종료 후 tools/profile_trace_viewer.ipynb 로 열어보기
```

저장되는 스냅샷:
- `S2_load_raw` — 원시 로더 출력
- `S3_filter_condition` — 카테고리화 후
- `S4_normalize` — 단위 정규화 후
- `S5_merge_steps` — 스텝 병합 + ffill 후
- `S6_calc_axis` — SOC/TimeMin 계산 후
- `S7_output_df` — 최종 result_df
- `S7_output_cycfile_soc` — OCV/CCV 요약

각 pickle payload:
```python
{
    "stage": "S5_merge_steps",
    "tag": "cycle",
    "ts": 1745000000.0,
    "shape": (12345, 18),
    "columns": [...],
    "dtypes": {...},
    "head": <DataFrame 30 rows>,
    "df": <DataFrame 전체>,
}
```

## 관련 노트

- [[260411_analysis_cycle_pipeline_complete]] — 사이클 파이프라인 이전 분석
- [[260418_profile_pipeline_dedup_cv_precision]] — 최근 정리 변경로그
