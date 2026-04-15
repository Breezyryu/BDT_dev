# TC 전기화학 정보 및 논리사이클 그룹 정의 추가

> **작성일**: 2026-04-15
> **대상 파일**: `DataTool_dev_code/DataTool_optRCD_proto_.py`
> **목적**: TC 단위 C-rate/전압 한계 정보와 LC 의미 그룹을 `ChannelMeta`에 표준화된 형태로 노출.

---

## 1. 배경

기존 `ChannelMeta`·`cycle_map`은 **사이클 구조**(TC↔LC)만 정의하고 다음 정보가 빠져 있었다:

1. **TC 단위 전기화학 정보** — 각 TotlCycle의 충/방전 C-rate, 전압 상/하한, 충전 모드
2. **LC 의미 그룹** — 연속된 논리사이클을 "화성", "RPT#1", "가속수명#1", "보관" 같은 시험 단위로 묶은 표현

결과:
- UI/프로파일 소비자가 매번 SaveEndData 를 재집계하거나 `accel_pattern`(첫 가속 루프만 대표) 으로 근사 → 일관성 결여.
- `.sch` 파싱은 `loop_groups` 수준에 머물러 TC 단위 활용이 어려움.
- 툴팁/보고서마다 그룹 명명이 제각각.

---

## 2. 정책 — 사전정보 + 실측 2단 파이프라인

| 소스 | 의미 | 시점 | 우선순위 |
|---|---|---|---|
| `.sch` / `.ptn` | 사전(prior) 정보 — 정의 한계값, 루프별 C-rate | I/O 없음 (이미 파싱됨) | **빠른 접근** |
| `SaveEndData` / `capacity.log` | 실측(measured) 정보 — 관측 V/I | 채널 로딩 시 | **최종 기준** |

**머지 규칙** (`_merge_tc_info`):
- `chg_crate` / `dchg_crate` / `v_max` / `v_min` / `mode_chg` → 실측이 not-None 이면 우선
- `v_cutoff_chg` / `v_cutoff_dchg` → 사전만 존재 (실측으로는 정의 한계를 알 수 없음)
- `source` 태그로 출처 추적: `'prior' | 'measured' | 'hybrid'`

---

## 3. 신규 데이터 구조

### `TcInfo` (dataclass)

TotlCycle 단위 전기화학 정보.

| 필드 | 타입 | 출처 | 설명 |
|---|---|---|---|
| `tc` | int | — | TotlCycle 번호 |
| `chg_crate` | float\|None | 사전/실측 | 대표 충전 C-rate |
| `dchg_crate` | float\|None | 사전/실측 | 대표 방전 C-rate |
| `v_max` | float\|None | 실측 | 충전 스텝 EndVoltage 최대 (V) |
| `v_min` | float\|None | 실측 | 방전 스텝 EndVoltage 최소 (V) |
| `v_cutoff_chg` | float\|None | 사전 | `.sch/.ptn` 정의 상한 (V) |
| `v_cutoff_dchg` | float\|None | 사전 | `.sch/.ptn` 정의 하한 (V) |
| `mode_chg` | str\|None | 사전/실측 | `'CC' \| 'CCCV'` |
| `source` | str | — | `'prior' \| 'measured' \| 'hybrid'` |

### `LogicalCycleGroup` (dataclass)

논리사이클 의미 그룹 — UI 경로 그룹인 `CycleGroup`과 **별개 개념**.

| 필드 | 타입 | 설명 |
|---|---|---|
| `name` | str | "화성", "RPT#1", "가속수명#1" ... |
| `category` | str | `'formation' \| 'RPT' \| 'accel' \| 'storage' \| 'gitt' \| 'initial' \| 'unknown'` |
| `lc_range` | tuple[int,int] | (시작 LC, 끝 LC) 포함 |
| `tc_range` | tuple[int,int] | `cycle_map['all']`로 펼친 TC 범위 |
| `n_cycles` | int | 포함 LC 수 |
| `v_window` | tuple[float,float]\|None | (대표 v_min, v_max) — tc_info의 median |
| `crate_profile` | tuple[float,float]\|None | (대표 chg_crate, dchg_crate) — tc_info의 median |
| `source` | str | `'schedule' \| 'classified' \| 'hybrid'` |

### `ChannelMeta` 확장

```python
tc_info: dict | None       # {TC: TcInfo}
cycle_groups: list | None  # [LogicalCycleGroup, ...]
```

---

## 4. 추가된 함수

| 함수 | 역할 | 파일 내 위치 |
|---|---|---|
| `_extract_tc_info_pne(raw_df, capacity)` | SaveEndData 1-pass → TC별 실측 {crate, v_max, v_min, mode_chg} | `_analyze_accel_pattern_pne` 바로 앞 |
| `_extract_tc_info_toyo(raw_df, capacity)` | capacity.log → TC별 실측 {v_max=PeakVolt, v_min≈OCV} | `toyo_build_cycle_map` 바로 앞 |
| `_prior_tc_info_from_loop_groups(loop_groups, accel_pattern)` | `.sch` loop_groups → TC별 사전 {crate, v_cutoff, mode_chg} | `_find_sch_file` 바로 앞 |
| `_merge_tc_info(prior, measured)` | 사전↔실측 병합. 실측 필드 not-None 시 우선 | `_prior_tc_info_from_loop_groups` 뒤 |
| `_build_cycle_groups(classified, cycle_map, tc_info, schedule_struct)` | classified RLE 병합 → LogicalCycleGroup 리스트 | `detect_test_type` 뒤 |

---

## 5. PNE 실측 집계 상세

`_extract_tc_info_pne` 는 SaveEndData 의 검증된 컬럼 스킴을 재사용한다 (기존 `_analyze_accel_pattern_pne` 와 동일).

| 컬럼 | 의미 |
|---|---|
| [2] | StepType (1=Chg, 2=Dchg, 3=Rest, 8=Loop) |
| [6] | EndState (65=CC, 66=CCCV) |
| [8] | EndVoltage (μV) |
| [9] | EndCurrent (μA) |
| [27] | TotlCycle |
| [38] | CC 구간 시간 (centisec) |
| [39] | CC 구간 용량 (μAh) |

1-pass 흐름:
1. `StepType == 8` (Loop 마커) 제외 — v_max 왜곡 방지
2. `groupby(27)` → TC 단위
3. StepType==1 행의 EndVoltage max → `v_max`, CCCV 존재 시 `mode_chg='CCCV'`
4. CCCV 충전 C-rate 는 `cc_cap / (cc_time/3600)` 역산, CC 는 `abs(EndCurrent)`
5. StepType==2 행의 EndVoltage min → `v_min`

---

## 6. Toyo 실측 집계 한계

`capacity.log` 에는 전류/시간 컬럼이 없어 **실측 C-rate 산정 불가**. 따라서:
- `chg_crate` / `dchg_crate` → `None` (사전정보 `_parse_toyo_ptn` 에서만 채워짐)
- `v_max` → `PeakVolt[V]` (충전 TC 최대)
- `v_min` → `Ocv` (방전 후 rest 전압) — **진정한 방전 최저점 아님**. 정밀 필요 시 상세 프로파일 CSV(000001 등) 재파싱 필요 (본 변경에 미포함).

---

## 7. 논리사이클 그룹 빌더

`_build_cycle_groups` 알고리즘:
1. `classified` 를 `category` 기준으로 RLE 병합 (연속 동일 category → 한 그룹)
2. 동일 category 2회 이상 등장 시 `#1, #2, ...` 인덱스 부여 (예: `RPT#1`, `RPT#2`)
3. `lc_range` → `cycle_map[lc_start]['all'][0]` / `cycle_map[lc_end]['all'][1]` 로 `tc_range` 계산
4. `tc_info` 있으면 해당 TC 범위의 `v_min`/`v_max`/`chg_crate`/`dchg_crate` 를 **median** 으로 요약 (mean 아님 — GITT 같은 편차 큰 그룹 대응)

**분류 매핑**:

| `classified.category` | `LogicalCycleGroup.category` | `name` |
|---|---|---|
| `initial` | `initial` | "초기" |
| `formation` | `formation` | "화성" |
| `RPT` | `RPT` | "RPT" 또는 "RPT#n" |
| `가속수명` / `Rss` | `accel` | "가속수명" 또는 "가속수명#n" |
| `GITT` / `_pulse` | `gitt` | "GITT" 또는 "GITT#n" |
| 기타 | `unknown` | "기타" 또는 "기타#n" |

---

## 8. `_build_channel_meta` 통합

기존 5단계 파이프라인(용량→분류→스케줄→시험유형→cycle_map) 뒤에 두 단계 추가:

- **Step 6**: TC 정보 구축 — `prior = _prior_tc_info_from_loop_groups(...)` → `measured = _extract_tc_info_{pne|toyo}(...)` → `_merge_tc_info(prior, measured)`
- **Step 7**: 논리사이클 그룹 구축 — `_build_cycle_groups(classified, cycle_map, tc_info, schedule_struct)`

`raw_df` 는 이미 Step 2 에서 로딩되어 있어 **추가 I/O 없음**.

---

## 9. 기존 소비자 영향

- `cycle_map` 구조 불변 → 기존 호출부 무영향
- `ChannelMeta` 기존 필드 (cycle_map/classified/test_type/accel_pattern 등) 값/의미 불변
- 신규 필드는 기본 `None` → 기존 경로에서 참조하지 않으므로 안전

---

## 10. 검증

### 단위 검증
```python
# Python REPL
from DataTool_dev_code.DataTool_optRCD_proto_ import _build_channel_meta
meta = _build_channel_meta(r"<PNE 채널 경로>", capacity_override=0)
print(len(meta.tc_info))                              # 전체 TC 수
print({t: v.source for t, v in list(meta.tc_info.items())[:5]})
for g in meta.cycle_groups:
    print(g.name, g.lc_range, g.tc_range, g.v_window, g.crate_profile, g.source)
```

### 기대 결과
- `.sch` 있는 PNE 채널: `source` 대부분 `'hybrid'`
- `.sch` 없음: `'measured'`
- Toyo: `v_max`/`v_min` 채워짐, crate 는 `.ptn` 존재 시에만 `'hybrid'`
- `cycle_groups`: `classified.category` 시퀀스 RLE 병합 결과와 일치

### 회귀 확인
- 기존 필드 (`cycle_map`/`classified`/`test_type`) 값 불변
- `get_cycle_map()` 결과 완전 동일
- 사이클/프로파일 탭 스모크 테스트 (신규 필드 미참조 → 영향 없어야 함)

### 성능
- `_build_channel_meta()` 실행 시간 +5% 이내 예상 (raw_df 재사용)
- 추가 lru_cache 불필요 (cycle_map/sch_struct 캐시에 의존)

---

## 11. 향후 고도화 여지

- Toyo v_min 정밀화: 상세 프로파일 CSV(000001...) 재파싱으로 실측 방전 최저점
- Toyo 실측 C-rate: 상세 프로파일의 `Current[mA].max()` 기반 TC 평균
- `schedule_struct.loop_groups.category` → `LogicalCycleGroup.category` 직접 매핑 옵션 (schedule source)
- `cycle_map` entry에 `tc_info_subset` 역참조 캐시 (hot path 최적화)
