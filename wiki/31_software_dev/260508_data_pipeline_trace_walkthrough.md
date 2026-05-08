# 데이터 처리 파이프라인 walkthrough — trace 모드 1라운드

작성: 260508 / 사용자(류성택) 요청

## 목적

- `DataTool_optRCD_proto_.py` (36,449줄 monolith) 의 데이터 처리 흐름을 함수 단위·데이터 변화 단위로 추적.
- 스텝별 전처리 소요시간 정량화 → 최적화 후보 식별.
- PNE / Toyo / 사이클 / 프로파일 / 연결처리 모든 부분을 대표 raw 경로로 walkthrough.

1라운드 범위 (회귀 risk 격리 위해 좁힘):

| # | 시나리오 | 예시 raw 경로 | 핵심 함수 진입점 |
|---|---|---|---|
| α | PNE 신형 사이클 | `raw/raw_exp/exp_data/수명/251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202/M01Ch008[008]/` | `pne_build_cycle_map` (6019) → `unified_cyc_confirm_button` (23563) |
| β | PNE 신형 프로파일 GITT | `raw/raw_exp/exp_data/성능/240821 선행랩 류성택 Gen4pGr mini-ATL-WD-Proto-422mAh-20C-450V-GITT-15도/M01Ch005[005]/` | `unified_profile_core` (3099) Stage 1~7 |
| ζ | 연결처리 디버깅 쌍 | `raw/raw_exp/datapath/경로저장_연결처리_디버깅용_연결.txt` vs `_비연결.txt` | `CycleGroup` 매핑 + path table 파싱 |

2라운드 (인프라 검증 후 추가 예정): γ PNE 프로파일 hysteresis (preset 3), δ Toyo 사이클, ε Toyo 프로파일.

---

## trace 인프라 ON/OFF

### 활성화 (dev 환경)

```bat
set BDT_TRACE=1
set BDT_TRACE_LEVEL=substep      :: stage|substep
:: BDT_TRACE_DIR 미설정 시: <BDT_dev 부모>\bdt_trace (build 폴더와 동등 레벨)
python DataTool_dev_code\DataTool_optRCD_proto_.py
```

또는 헬퍼 배치 사용:

```bat
run_with_trace.bat                                  :: 기본 substep + <BDT_dev 부모>\bdt_trace
run_with_trace.bat C:\tmp\my_trace                  :: 디렉토리 override
run_with_trace.bat C:\tmp\my_trace stage            :: stage 단위만 (sub-step 미수집)
```

### 비활성화 (운영 / exe 빌드)

- 환경변수 미설정 → monolith stub 들이 fast-path no-op (비용 ~ns).
- PyInstaller 빌드 (`build_exe_onepath.bat`) 는 `--exclude-module bdt_trace` 적용 → exe 에 trace 코드 0 포함.
- 빌드된 exe 에서 BDT_TRACE 켜도 `import bdt_trace` 실패 → silent OFF.

### 산출물 위치

기본값 — 사내환경 build 폴더와 동등 레벨:

```
<BDT_dev 부모>\bdt_trace\session_<TS>\
  ├── step.csv            -- 한 행 = 한 측정 (raw 데이터)
  ├── step_summary.md     -- 사람용 요약 (Top-10 hotspot, Stage 누적, 캐시 통계)
  ├── step_hotspot.png    -- Top-15 가로 막대 차트
  └── NNN_<stage>_<tag>.pkl  -- Stage 끝 DataFrame snapshot (S2/S3/S4/S5/S6/S7)
```

예 (사내 PC): BDT_dev 가 `C:\Users\Ryu\battery\python\BDT_dev\` → trace 는
`C:\Users\Ryu\battery\python\bdt_trace\session_<TS>\`. build 산출물 (`...\python\build\`)
과 같은 부모 디렉토리.

`BDT_TRACE_DIR` 환경변수로 override 가능. 결정 실패 시 `C:\tmp\bdt_trace` 로 폴백.

---

## α — PNE 사이클 walkthrough

### 함수 흐름 (요약)

```
사용자 클릭 (사이클 분석 [확인])
    ↓
unified_cyc_confirm_button (23563)              [@log_perf]
    ↓
PerfSection('Phase 0 메타데이터')
    └─ _build_channel_meta — 채널별 ChannelMeta 생성
        └─ check_cycler — Pattern/Restore 폴더로 PNE/Toyo 판별
        └─ _cached_pne_restore_files — SaveData / SaveEndData / .cyc 캐시
        └─ pne_min_cap — name_capacity (mAh 추출) 또는 첫 사이클 추정
        └─ pne_build_cycle_map (6019)
            ├─ [substep] saveend_cache_lookup — _cached_pne_restore_files 재사용
            ├─ [substep] pivot — TotlCycle × Condition (chgCap/DchgCap)
            ├─ [substep] mode_decision — .sch sweep_mode 우선, 휴리스틱 폴백
            └─ [iterative] cycle_map 생성 (general or sweep)
    ↓
PerfSection('데이터 로딩')
    └─ ThreadPoolExecutor (channel-level 병렬)
        └─ pne_cycle_data (or toyo_cycle_data)
            └─ SaveEndData → cycle 별 집계
                (DchgCap / Eff / RndV / dcir vs cycle_no)
    ↓
plot 렌더링 + Excel writer (해당 시)
```

### 데이터 shape 변화 (대표값)

예시 입력: 채널 폴더 1개, TotlCycle 약 1200개 (논리사이클 1~1202)

| 단계 | 산출 | 행 수 | 비고 |
|---|---|---|---|
| `_cached_pne_restore_files` | `save_end_cached` (SaveEndData CSV concat) | ~1200 × N (스텝 수) | 모든 TC 의 스텝 종료 레코드 |
| `pne_build_cycle_map` pivot | `pivot[chgCap]`, `pivot[DchgCap]` | 1200 (TC unique) | 충방전 용량 별 컬럼 |
| `pne_build_cycle_map` 결과 | `cycle_map` dict | 1202 entries | `{논리사이클: {all, chg, dchg, chg_rest, dchg_rest}}` |
| `pne_cycle_data` 병합 | `Cycleraw` DataFrame | 1202 rows × ~15 cols | cycle 단위 Eff/Cap/RndV/dcir |
| Plot data | matplotlib lines 4종 | n_points = n_cycle | DchgCap, Eff, RndV, dcir vs cycle_no |

### 예상 hotspot

| 후보 | 측정 위치 | 주요 비용 |
|---|---|---|
| `_cached_pne_restore_files` (cache miss) | `CycleMap_PNE / saveend_cache_lookup` | NAS I/O × 수백~수천 SaveEndData 파일 |
| `pivot_table` | `CycleMap_PNE / pivot` | TotlCycle 수 큰 경우 |
| `mode_decision` 휴리스틱 | `CycleMap_PNE / mode_decision` | .sch 부재 시 데이터 휴리스틱 |
| dcir 병렬 read | `pne_cycle_data` 내부 (콜백 timing 만, sub-step 미배치) | 파일별 .csv read |

---

## β — PNE 프로파일 GITT walkthrough

### 함수 흐름

```
사용자 클릭 (프로파일 분석 [확인])
    ↓
unified_profile_confirm_button (28215)          [@log_perf]
    ↓
unified_profile_core (3099)
    ├─ Stage 1: cycler 판별 + cycle_map 확보
    │   └─ [substep] cycler_and_capmap
    │       (is_pne_folder, pne_min_cap, get_cycle_map)
    ├─ Stage 2: raw 로딩 (Layer A — ADR 0002, 모든 Cond/TC)
    │   └─ [substep] dispatch (PNE/TOYO 분기)
    │       ↓
    │       _unified_pne_load_raw (1678)
    │       ├─ [substep] cache_lookup — channel cache (TC 범위 키)
    │       ├─ [substep] cyc_attempt — _try_cyc_profile (.cyc 우선)
    │       ├─ [substep] csv_concat (.cyc 실패 시 — Restore SaveData N개 read+concat)
    │       ├─ [substep] column_map — 컬럼 인덱스 → 이름, cycle_map 적용
    │       └─ [substep] saveend_merge — OCV/CCV/Stepmode (SaveEndData merge)
    │   --- snapshot: S2_load_raw_PNE_cycN-M.pkl ---
    ├─ Stage 3: Condition 필터링 (CC 재분류 + 휴지 분류 + 보충전 제외)
    │   └─ [substep] apply (_unified_filter_condition)
    │   --- snapshot: S3_filter_condition_<scope>.pkl ---
    ├─ Stage 4: 정규화 (μV→V, μA→mA, μAh→mAh)
    │   └─ [substep] apply (_unified_normalize_pne)
    │   --- snapshot: S4_normalize_PNE.pkl ---
    ├─ Stage 5: 스텝 병합 + Block 컬럼 (multi-TC 용량 누적)
    │   ├─ [substep] apply (_unified_merge_steps)
    │   └─ [substep] block_alloc (sweep + cycle scope)
    │   --- snapshot: S5_merge_steps_cycle.pkl ---
    ├─ Stage 6: 축 계산 (X = SOC | time)
    │   ├─ [substep] axis (_unified_calculate_axis)
    │   ├─ [substep] cutoff (전압/Crate 하한)
    │   └─ [substep] dqdv (옵션)
    │   --- snapshot: S6_calc_axis_<scope>_<axis>_<overlap>.pkl ---
    └─ Stage 7: 출력 컬럼 구성 + cycfile_soc 산출
        --- snapshot: S7_output_df_<scope>_<axis>_<overlap>.pkl ---
    ↓
unified_render_loop — TC 별 plot 분기
```

### 데이터 shape 변화 (대표값)

예시 입력: GITT 채널, TC 1~30 (펄스 30회), preset 4 (충전 분석), cycle (1, 30)

| Stage | 컬럼 추가/제거 | 행 수 변화 (대략) |
|---|---|---|
| S2 raw | Index, Condition, Step, Voltage_raw (μV), Current_raw (μA), ChgCap_raw (μAh), DchgCap_raw, ChgWh_raw, DchgWh_raw, StepTime_raw (/100s), TotTime_Day, TotTime_Sec_raw, Temp_raw, Cycle, **+ OCV_raw / CCV_raw / Stepmode** (SaveEndData merge) | 100k~1M (TC 30 × 스텝 길이) |
| S3 filter | (컬럼 그대로) — Condition 마스크만 | 절반 정도 (charge scope 시) |
| S4 normalize | **Voltage / Current_mA / ChgCap / DchgCap / Crate / Temp** (단위 변환) | 동일 |
| S5 merge | **+RawCycle** (multi-TC 용량 리셋 추적), **+Block** (1=chg, 2=dchg) | 동일 |
| S6 axis | **+SOC** (정규화 0~1), **+TimeMin** | cutoff 적용 시 일부 row 드롭 |
| S6 dqdv (옵션) | **+dQdV / dVdQ / Energy** | 동일 |
| S7 output | base_cols + Vol + Cycle + Condition (호환성 + 색상 구분) | 동일 (final 출력) |

### 예상 hotspot

| 후보 | 측정 위치 | 주요 비용 |
|---|---|---|
| CSV concat (`.cyc` miss) | `S2_load_raw / csv_concat` | N개 SaveData 파일 read+concat (NAS I/O) |
| SaveEndData merge | `S2_load_raw / saveend_merge` | DataFrame.merge × 2 (OCV, CCV) + map(StepNo→Stepmode) |
| Stage 3 filter | `S3_filter_condition / apply` | numpy mask 1-pass (CC 재분류) |
| Stage 5 merge_steps | `S5_merge_steps / apply` | multi-TC 용량 누적 (groupby 또는 cumsum) |
| Stage 6 axis | `S6_calc_axis / axis` | SOC 계산 (anchor + scaling) |

---

## ζ — 연결처리 walkthrough

### 입력 비교

`raw/raw_exp/datapath/경로저장_연결처리_디버깅용_연결.txt` vs `경로저장_연결처리_디버깅용_비연결.txt`

연결 모드:
- 한 그룹 안에 paths 2개 이상 → `CycleGroup.is_link=True`
- 채널 위치 매핑 (`channel_link_map`) 으로 paths 별 채널 병합
- 사이클 분석에서만 적용 (프로파일은 채널 단위)

비연결 모드:
- 한 그룹 = path 1개 → `CycleGroup.is_link=False`

### 함수 흐름

```
사용자 [경로 업로드 / 직접 입력]
    ↓
path table 파싱 — 각 path 파일에서 (folder, channels, capacity, v_nom) 추출
    ↓
CycleGroup 객체 N개 생성
    각 그룹: paths[], path_names[], per_path_channels[], channel_link_map (연결 모드만)
    ↓
unified_cyc_confirm_button (23563)
    ↓
PerfSection('Phase 0 메타데이터') — 채널별 메타 (paths 1+ 모두 처리)
    ↓
PerfSection('데이터 로딩')
    └─ 그룹별 처리:
        if is_link:
            전체 paths 의 cycle_map 병합 — 채널 매핑 + 용량 정규화
        else:
            단일 path 의 cycle_map 사용
    ↓
연결 그룹 = 한 plot 의 한 trace
비연결 그룹 = 한 plot 의 별도 trace
```

### 디버깅 포인트 (비교)

| 측정 위치 | 비연결 | 연결 |
|---|---|---|
| `Phase 0 메타데이터` | paths=1 | paths=N (병렬 channel 메타) |
| `데이터 로딩` | 단일 path I/O | N path I/O 합산 |
| cycle_map 매핑 | 단일 cycle_map | N cycle_map 의 위치 기반 합성 |

trace step.csv 의 `extra` 컬럼에서 `paths=N` 으로 두 모드 자동 구분.

---

## 산출물 활용 — `step_summary.md` 읽는 법

### Top-10 hotspot 표

```
| rank | stage | sub_step | elapsed (ms) | % of total |
|---:|---|---|---:|---:|
| 1 | S2_load_raw | csv_concat | 4231.5 | 38.4 |
| 2 | S2_load_raw | saveend_merge | 1832.1 | 16.6 |
| ...
```

해석:
- "rank 1 csv_concat 38%" → SaveData 파일 N개의 read+concat 이 38% 차지. 캐시화 또는 병렬 read 후보.
- "rank 2 saveend_merge 16%" → DataFrame.merge × 2 가 16%. merge 컬럼 인덱싱 또는 .apply 대신 .map 검토.

### Stage 별 누적

```
| stage | sum (ms) | n | % |
|---|---:|---:|---:|
| S2_load_raw | 7234.2 | 8 | 65.7 |
| S6_calc_axis | 1820.4 | 5 | 16.5 |
```

해석: Stage 2 가 전체 65% — 데이터 로딩이 본진 비용. Stage 6 (축 계산) 이 16% 로 두 번째.

### 캐시 통계

```
- hit: 12
- miss: 3
```

해석: 15회 측정 중 캐시 hit 12회. miss 3회의 위치 (`step.csv` 의 `cache_hit=miss` 행) 점검 → TTL/key 정책 재검토 후보.

### 데이터 shape 변화 표

```
| stage | tag | rows_out |
|---|---|---:|
| S2_load_raw | PNE_cyc1-30 | 837421 |
| S3_filter_condition | charge | 412305 |
| S4_normalize | PNE | 412305 |
| ...
```

해석: Stage 2 → Stage 3 에서 행 수가 절반 (charge scope 마스킹). Stage 4 normalize 는 행 변화 없음. Stage 6 cutoff 가 또 행 수 줄임 등.

---

## 회귀 안전성

| 보장 항목 | 수단 |
|---|---|
| exe 빌드 영향 | bdt_trace 미포함 (`--exclude-module bdt_trace` + .spec excludes) |
| 운영 환경 비용 | dormant 시 콜백 list 빈 검사 (~ns) |
| 데이터 처리 정확성 | sub-step hook 은 `with` 블록으로 둘러싸기만 함 — 기존 로직 그대로 |
| 스냅샷 부작용 | dormant 시 no-op (pickle 저장 안 함) |

---

## 미해결 / 후속 (2라운드)

1. γ **PNE 프로파일 hysteresis (preset 3)** — `unified_flow=True` 분기, envelope merge, cross-TC pairing
2. δ **Toyo 사이클** — `toyo_cycle_data` 의 sub-step (capacity.log read, merge_group, dcir 병렬 read)
3. ε **Toyo 프로파일** — `_unified_toyo_load_raw` 의 sub-step
4. **dcir 병렬 read** sub-step 배치 (현재는 함수 단위 timing 만)
5. **UI 메뉴** (도구 → 처리 추적 모드 ON) — 1라운드는 환경변수 only, 인프라 검증 후 추가
