---
tags: [bdt, hysteresis, profile-analysis, refactor, level-2-flow, work-log]
date: 2026-04-29
status: implemented
---

# 히스테리시스 분석 — 레벨 2 단일 flow + Origin 호환 + long-format 시트

## 배경

BDT origin (`BatteryDataTool 260204.py`) 과 엑셀 후처리 (`Voltage hysteresis test_Graph format_v1.3.xlsx`, 169k 수식, 10 시트) 의 흐름을 proto (`DataTool_optRCD_proto_.py`) 의 히스테리시스 분석으로 내재화. 동일 raw 데이터로 처리 시 엑셀 골든 레퍼런스와 numerically 등가한 통합 long-format 시트를 자동 출력.

## 사용자 결정사항

- **Q1**: dQdV CV 마스킹은 origin 호환 (CV 영역 마스킹 OFF) 채택.
- **Q2**: 출력은 long-format 통합 시트 한 장 (10 시트 펼침의 단일 표).
- **Q3**: 별도 UI 토글 없이 **히스테리시스 프리셋** (`overlap=connected` + `profile_hyst_pair_chk`) 자동 활성.
- **레벨 2** 단일 flow 리팩터: 파이프라인은 항상 cycle scope 통합 처리, `data_scope` 분기는 마지막 view 단계로 이동.

## 변경 항목

### 1. 신규 함수 (2)

| 함수 | 위치 | 역할 |
|---|---|---|
| `_unified_apply_view(df, data_scope, axis_mode, overlap, *, cutoff, include_rest)` | 모듈 함수 | Stage 6 view layer — row mask + 시간 정규화 + cutoff. 기존 `_axis_*`/`_calc_soc` 재사용. |
| `self._build_hysteresis_long_dataframe(loaded_data, all_data_folder, all_data_name, mincapacity)` | UI 클래스 메서드 | TC × 데이터포인트 long-format DataFrame 생성. 컬럼: folder/channel/TC/direction/depth_pct/window_label/loop_type/TimeMin/SOC_local/SOC_abs/DOD_abs/Voltage/Crate/dQdV/dVdQ/Energy/Temp. |

### 2. 시그니처 확장 (4)

- `_unified_calculate_dqdv(..., *, origin_compat=False)` — True 시 `|ΔV|<2mV` 마스킹 OFF.
- `unified_profile_core(..., unified_flow=False, origin_compat=False)` — 단일 flow + dQdV 호환 모드.
- `unified_profile_batch(..., unified_flow=False, origin_compat=False)` — 호출 전달.
- `_unified_process_single_cycle_from_raw(..., unified_flow=False, origin_compat=False)` — 동일.

### 3. 내부 흐름 분기

`unified_flow=True` 시 다음 동작:

```
Stage 2 (raw load):     data_scope="cycle" 강제 → 캐시키 통일, 옵션 토글 시 raw 재로드 방지
Stage 3 (filter):       data_scope="cycle" + include_rest=True 강제 → 모든 Condition (1/2/3) 살림
Stage 5 (merge):        data_scope="cycle" 으로 호출
Stage 5.5 (Block 할당): 조건이 cycle scope 매치되어 정상 동작
Stage 6 통합:           dQdV 우선 계산 → _unified_apply_view 한방 적용
```

기존 `unified_flow=False` 분기는 그대로 유지 — 완벽한 후방 호환.

### 4. 자동 감지 (`_read_profile_options`)

```python
is_hysteresis_mode = (overlap == "connected" and hyst_pair)
unified_flow      = is_hysteresis_mode
origin_compat     = is_hysteresis_mode
```

→ 사용자가 프리셋 콤보에서 "히스테리시스" 선택만 하면 단일 flow + origin 호환 dQdV 자동 활성.

### 5. Hysteresis_Analysis 시트 출력

- `_apply_hysteresis_soc_offsets` 직후 `self._pending_hyst_long_df = self._build_hysteresis_long_dataframe(...)` 빌드.
- `_profile_render_loop` 의 `writer.close()` 직전에 `self._pending_hyst_long_df` 가 있으면 `Hysteresis_Analysis` 시트로 출력.
- 프리셋 비활성 시 `_pending_hyst_long_df=None` → 시트 추가되지 않음.

## Long-format 시트 컬럼

| 컬럼 | 의미 |
|---|---|
| folder_idx, folder_name, channel | 멀티 경로/채널 식별 |
| TC, LogicalCycle | 물리/논리 사이클 |
| direction | "Chg" / "Dchg" |
| depth_pct | 10/20/.../100 |
| window_label | "Chg 100%", "Dchg 10%" 등 — 엑셀 헤더와 동일 |
| loop_type | "major" (SOC 범위≥0.98) / "minor" |
| TimeMin | 사이클 내 경과 시간 |
| SOC_local | 보정 전 사이클별 SOC |
| SOC_abs | 절대 SOC 좌표 (`_compute_tc_soc_offsets` 적용) |
| DOD_abs | `1 - SOC_abs` |
| Voltage, Crate, dQdV, dVdQ, Energy, Temp | 표준 8컬럼 파생값 |

→ Excel 6 가공시트 (`_QV`, `_QVData_DOD`, `_dVdQData_SOC`, ..., `dQdV`) 모두 이 long-format 에서 pivot/filter 로 재구성 가능.

## 검증 가이드 (사용자 실행)

1. proto 실행 → 이 실험의 raw PNE 폴더 등록 (사내 PC 에서만 접근 가능).
2. 프리셋 콤보 → **히스테리시스** 선택 → 자동으로 사이클·연결·SOC·CV 옵션 + TC 페어링 ON.
3. 사이클 범위에 `3-23` 또는 `3-12, 14-23` 입력.
4. **Profile 분석** 버튼 → 결과 xlsx 의 `Hysteresis_Analysis` 시트 확인.
5. Excel 골든 레퍼런스 (`raw/Voltage hysteresis test_Graph format_v1.3_bundle.txt`) 의 4 raw paste 시트 (`3~12_충전`, `3~12_방전`, `14~23_충전`, `14~23_방전`) 셀값과 비교:
   - TimeMin, SOC, Energy, Voltage, Crate, dQdV, dVdQ, Temp 일치 여부 (소수점 6자리)
6. Excel 6 가공시트 (`_QV`, `_QVData_DOD`, `_dVdQData_SOC`, `dQdV` 등) 의 누적 SOC 좌표 와 long-format 의 `SOC_abs` 일치 확인:
   - Excel `[3~12_QV]` 행 1383 우측 헤더 "Chg 100%, Dchg 10%, ..." 윈도우 라벨 = long-format 의 `window_label` 컬럼

## 주의

- `unified_flow=True` 분기는 히스테리시스 프리셋 진입 시에만 자동 활성화. 다른 프리셋 (전체 진단 / ICA / 충전 분석 / 방전 분석) 은 `unified_flow=False` 로 기존 동작 유지.
- CV 마스킹 OFF는 origin (260204.py) 동작과 numerically 일치를 위함이지, 일반 분석에서 CV 영역 dQdV 발산 정보가 유의미한 것은 아님 — 히스테리시스 프리셋에서만 활성화.
- Long-format 시트는 `Hysteresis_Analysis` 단일 시트. 기존 Profile 시트는 그대로 출력됨.

## 참고 위치

- Excel 골든 레퍼런스: `raw/Voltage hysteresis test_Graph format_v1.3_bundle.txt`
- Origin 함수: `DataTool_dev_code/BAK/260204_sy_origin/BatteryDataTool 260204.py` L1366-1477 (`pne_chg_Profile_data` / `pne_dchg_Profile_data`)
- 변경 대상: `DataTool_dev_code/DataTool_optRCD_proto_.py`
