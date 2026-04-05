# 260404 — Phase 3: 통합 프로필 배치 로더 추가

## 배경 / 목적

Phase 2에서 `unified_profile_core()`가 기존 5개 파싱 함수와 동일한 결과를 산출함을 검증했다.
Phase 3에서는 **배치 로딩 계층**을 통합한다.

기존 구조: 10개 배치 함수(toyo/pne × step/rate/chg/dchg/continue) + 2개 병렬 로더(`_load_step_batch_task`, `_load_profile_batch_task`)가 개별적으로 작동.

통합 목표: 1개 배치 함수 + 1개 병렬 로더로 교체하되, **PNE SaveData 1회 I/O 최적화**를 유지.

## 변경 내용

### 신규 함수 (proto_.py)

| 함수명 | 위치 | 역할 |
|--------|------|------|
| `_unified_process_single_cycle_from_raw()` | 라인 1331~ | 이미 로드된 원시 데이터에서 단일 사이클 Stage 2~6 실행 |
| `unified_profile_batch()` | 라인 1452~ | **메인 배치 함수** — PNE/Toyo 분기, cycle_list 전체 처리 |
| `unified_profile_batch_continue()` | 라인 1579~ | Continue 전용 배치 — step_ranges 단위 처리 |
| `_load_unified_batch_task()` | 라인 14101~ | ThreadPoolExecutor용 채널 단위 태스크 (WindowClass 메서드) |
| `_load_all_unified_parallel()` | 라인 14138~ | **통합 병렬 로더** — 모든 폴더 병렬 처리 (WindowClass 메서드) |

### 기존 10개 배치 함수 → 통합 매핑

| 기존 함수 | 통합 호출 |
|-----------|----------|
| `toyo_step_Profile_batch` | `unified_profile_batch(data_scope="charge", axis_mode="time", continuity="overlay")` |
| `pne_step_Profile_batch` | 동일 (PNE 자동 감지) |
| `toyo_rate_Profile_batch` | `unified_profile_batch(data_scope="charge", axis_mode="time", continuity="overlay")` ※ 스텝 병합 없음 |
| `pne_rate_Profile_batch` | 동일 |
| `toyo_chg_Profile_batch` | `unified_profile_batch(data_scope="charge", axis_mode="soc", calc_dqdv=True)` |
| `pne_chg_Profile_batch` | 동일 |
| `toyo_dchg_Profile_batch` | `unified_profile_batch(data_scope="discharge", axis_mode="soc", calc_dqdv=True)` |
| `pne_dchg_Profile_batch` | 동일 |
| `toyo_continue_Profile_batch` | `unified_profile_batch_continue(step_ranges=[...])` |
| `pne_continue_Profile_batch` | 동일 |

### 기존 2개 병렬 로더 → 통합 매핑

| 기존 | 통합 |
|------|------|
| `_load_step_batch_task` + `_load_all_step_data_parallel` | `_load_unified_batch_task` + `_load_all_unified_parallel` |
| `_load_profile_batch_task` + `_load_all_profile_data_parallel` | 동일 |

## 핵심 설계 결정

### 1. PNE 1회 I/O 최적화 유지

```
기존: _pne_load_profile_raw() → all_raw 1회 로드 → 사이클별 분배
통합: _unified_pne_load_raw(min, max) → all_raw 1회 로드
      → Cycle 컬럼으로 슬라이싱
      → _unified_process_single_cycle_from_raw() 사이클별 Stage 2~6
```

PNE SaveData는 수백 MB 단위의 바이너리 CSV이므로 **사이클별 개별 로드**는 I/O 병목.
기존 최적화를 그대로 유지하면서 통합 파이프라인의 Stage 2~6을 적용한다.

### 2. Toyo는 사이클별 unified_profile_core() 직접 호출

Toyo는 사이클별 개별 파일(`000001`, `000002`, ...)이므로 일괄 로드의 이점이 없다.
`unified_profile_core()`를 루프 호출하되, `min_cap` 산정은 1회만 수행.

### 3. Continue 모드 분리

Continue 모드는 다른 모드와 인터페이스가 다르다:
- 입력: `step_ranges = [(start, end), ...]` (사이클 범위 쌍)
- 옵션: `continuity="continuous"` 고정, `data_scope="cycle"` 고정

`unified_profile_batch_continue()`로 분리하여 명확성 확보.

### 4. 반환 형식 호환

```python
# 기존 배치 함수
{cycle_no: [mincapacity, df]}

# 통합 배치 함수
{cycle_no: [mincapacity, UnifiedProfileResult]}
# UnifiedProfileResult.df → 기존 df와 동일 컬럼 구조
```

Phase 4 UI 통합 시, `result.df`로 접근하면 기존 렌더러와 호환.

## Before / After 비교

### Before
```
10개 배치 함수 × (PNE/Toyo 분기 내장)
2개 병렬 로더 × (profile_type 분기)
= 12개 함수, ~500줄 코드
```

### After
```
1개 배치 함수 (unified_profile_batch)
1개 Continue 전용 (unified_profile_batch_continue)
1개 내부 헬퍼 (_unified_process_single_cycle_from_raw)
1개 병렬 로더 (_load_all_unified_parallel)
1개 태스크 함수 (_load_unified_batch_task)
= 5개 함수, ~300줄 코드
```

## 영향 범위

- **변경된 파일**: `DataTool_dev/DataTool_optRCD_proto_.py`
- **추가된 코드**: ~300줄
  - `_unified_process_single_cycle_from_raw()`: 라인 1331~
  - `unified_profile_batch()`: 라인 1452~
  - `unified_profile_batch_continue()`: 라인 1579~
  - `_load_unified_batch_task()`: 라인 14101~ (WindowClass 메서드)
  - `_load_all_unified_parallel()`: 라인 14138~ (WindowClass 메서드)
- **기존 함수**: 변경 없음 (유지, Phase 5에서 제거 예정)
- **UI**: 변경 없음 (Phase 4에서 통합 UI 구현 예정)

## 다음 단계

- ~~Phase 3: 배치 로더 통합~~ ✅ 완료
- Phase 4: UI 통합 (5개 버튼 → 1개 통합 버튼 + 4개 옵션 위젯)
- Phase 5: 기존 10개 배치 함수 + 2개 병렬 로더 deprecated → 제거
