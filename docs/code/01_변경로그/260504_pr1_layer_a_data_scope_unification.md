# PR-1 — Layer A 단일화: `_unified_pne_load_raw` 의 `data_scope` 파라미터 제거

날짜: 2026-05-04
관련 ADR: [`docs/adr/0002-layer-a-data-scope-single-load.md`](../../adr/0002-layer-a-data-scope-single-load.md)
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수:
- `_unified_pne_load_raw` (L1468) — signature 변경
- `unified_profile_core` (caller, L2864) — 호출 인자 정리
- `unified_profile_batch_continue` (caller, L3305) — 호출 인자 정리

## 배경 — ADR 0002

기존 `_unified_pne_load_raw(data_scope=scope)` 가 `data_scope` 별 raw 로딩을 분리. 사용자가 `data_scope` 토글 (cycle ↔ charge ↔ discharge) 시 raw 재로드 발생 — 사용자 시나리오 (분석 옵션 빈번한 변경) 에서 IO 비효율.

3-layer 모델 (ADR 0001) 의 Layer A 책임은 "옵션 무관 + 채널/TC 만 의존" 이어야 함. `data_scope` 가 Layer A 에 영향 → Layer 정의 위반.

## 변경 요약

### 1. `_unified_pne_load_raw` signature

```python
# Before
def _unified_pne_load_raw(
    raw_file_path: str,
    cycle_start: int,
    cycle_end: int,
    cycle_map: dict | None = None,
    *,
    data_scope: str = "cycle",
) -> pd.DataFrame | None:
```

```python
# After
def _unified_pne_load_raw(
    raw_file_path: str,
    cycle_start: int,
    cycle_end: int,
    cycle_map: dict | None = None,
) -> pd.DataFrame | None:
```

### 2. 내부 TC 선택 로직

```python
# Before (L1522)
tc_list = _cm_tc_list(entry, data_scope)  # scope 별 TC

# After
tc_list = _cm_tc_list(entry, 'cycle')  # 항상 모든 TC
```

### 3. Caller 정리

```python
# unified_profile_core L2864 — Before
raw = _unified_pne_load_raw(
    raw_file_path, cycle_start, cycle_end,
    cycle_map=cycle_map,
    data_scope=_data_scope_pipe,
)

# After (data_scope 키워드 제거)
raw = _unified_pne_load_raw(
    raw_file_path, cycle_start, cycle_end,
    cycle_map=cycle_map,
)
```

`unified_profile_batch_continue` L3305 도 동일하게 정리.

## 영향 범위

### Sweep test (chg/dchg TCs disjoint)

| Cycle map entry | Before (scope=charge) | Before (scope=discharge) | After (모든 scope) |
|---|---|---|---|
| `{'all':(1,3), 'chg':[1], 'dchg':[2,3]}` | TC=[1] | TC=[2,3] | **TC=[1,2,3] (cache 통합)** |

→ Sweep test 에서 사용자가 scope 토글 시 raw 재로드 0회 (이전엔 매번 재로드).

### 일반 cycle (chg/dchg TCs 동일)

| Cycle map entry | Before | After | 변화 |
|---|---|---|---|
| `{'all':(3,5), 'chg':[3,4], 'dchg':[4,5]}` | scope 별 동일 TC=[3,4] 또는 [4,5] | TC=[3,4,5] | 약간 더 많은 TC |

→ 메모리 ~10-30% 증가 (rest TC 추가 로드), CPU 미미.

### Downstream 영향

- **Stage 3 (`_unified_filter_condition`)**: `_data_scope_pipe` 받아 row 필터링 — 변경 없음. raw 가 더 많은 TC 갖고 있어도 Cond 필터로 정확히 좁혀짐.
- **Layer C view step 1**: 동일하게 row mask — 변경 없음.
- **결과 DataFrame**: numerical 동일 (downstream filter 가 같은 결과 산출).

## 검증

### 1. 신규 검증 스크립트

[`tools/test_code/layer_a_unification_validator.py`](../../../tools/test_code/layer_a_unification_validator.py) — 4-step:

1. **Signature 검증** — `data_scope` 파라미터 제거 확인 ✅
2. **`_cm_tc_list(scope='cycle')` 동작** — 일반/multi-TC/sweep 케이스 ✅
3. **Cache 키 시뮬레이션** — sweep 시험에서 단일화 효과 확인 ✅
4. **Caller source 검증** — 모든 호출에서 `data_scope=` 인자 제거 확인 ✅

### 2. 기존 회귀 검증 (Fix 1~6)

[`tools/test_code/hysteresis_render_decision_validator.py`](../../../tools/test_code/hysteresis_render_decision_validator.py) — 49/49 PASS 유지.

```
[종합] truth_table=0, real_paths=0, simulation=0, canonical_delta=0,
       dchg_scale=0, cv_mask=0, envelope_merge=0, axis_mode=0
  ✅ ALL PASS — Fix 1~6 회귀 안전
```

## 사용자 검증 가이드 (사내 PC)

1. **사용자 시나리오 — scope 토글 속도 향상 확인**:
   - Hyst 데이터 (TC 3-12) 로 preset 4 (충전 분석) 실행 → raw 로딩 시간 측정
   - 동일 데이터 + preset 5 (방전 분석) 실행 → raw 로딩 시간 측정
   - **기대**: 두 번째 실행에서 "캐시 히트" 로그 출력, 로딩 시간 ≈ 0
   - 로그 메시지: `[unified_raw] 캐시 히트: TC X~Y`

2. **메모리 영향 모니터링** (큰 채널 + 큰 TC 범위):
   - 실측: TC 1-1000 같은 범위에서 raw 로드 시 메모리 사용량 (sweep 시험 기준 ~10-30% 증가 예상)

3. **회귀 검증** — 기존 preset 4/5 출력의 numerical 동일성:
   - PR-1 적용 전후 동일 데이터·동일 옵션으로 xlsx 출력
   - SOC, V, dQdV 컬럼 비교 — 일치해야 함

## 후속 작업

- **PR-2**: Layer B 캐시 추가 (`_channel_cache['unified_transformed']`)
- **PR-3**: 캐시 무효화 trigger + 메모리 evict 정책

## 관련 문서

- ADR 0001 — 3-layer 모델
- ADR 0002 — Layer A 단일화 (본 PR 의 결정 근거)
- CONTEXT.md § "옵션 → Layer 영향 매트릭스"
- Grilling 세션 260504 Q5
