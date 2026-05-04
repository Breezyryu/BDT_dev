# 0002. Layer A 단일화 — `data_scope` 를 view-only 옵션으로 전환

날짜: 2026-05-04
상태: Accepted

## Context

현재 Layer A (Stage 2 raw load) 가 `data_scope` 파라미터를 받아 PNE raw 로딩 시 `data_scope` 별로 row 를 직접 선택한다 (`_unified_pne_load_raw(data_scope=scope)`).

```python
# 현재
if is_pne:
    raw = _unified_pne_load_raw(
        raw_file_path, cycle_start, cycle_end,
        cycle_map=cycle_map,
        data_scope=_data_scope_pipe,  # ← scope 별 raw filter
    )
```

→ 사용자가 `data_scope` 토글 (cycle ↔ charge ↔ discharge) 시 raw 재로드 발생. Layer A 캐시가 `data_scope` 별로 분리됨.

같은 채널·TC 범위에서 `data_scope` 만 다른 분석을 빈번히 전환하는 것이 사용자 시나리오 — 이 경우 raw IO 가 매번 재실행 (수백 ms ~ 수 초).

## Decision

Layer A 의 raw load 가 **항상 모든 Cond (1, 2, 3) row 를 로딩** 하도록 단일화한다. `data_scope` 는 Layer C (view step 1) 의 row mask 단계에서만 적용.

```python
# 변경 후
if is_pne:
    raw = _unified_pne_load_raw(
        raw_file_path, cycle_start, cycle_end,
        cycle_map=cycle_map,
        # data_scope 파라미터 제거 — 항상 전체 Cond 로드
    )
# view layer Step 1 의 mask 가 scope 적용 (이미 구현됨)
```

→ Layer A 캐시 키에서 `data_scope` 제거 → `(raw_path, cycle_range)` 만으로 키 결정.
→ 같은 채널·TC 의 모든 scope 분석이 같은 raw 캐시 공유.

## Consequences

**좋아짐**:
- 사용자 시나리오 (scope 토글) 에서 raw IO 0회 → 즉시 재계산 (Layer C 만 재실행)
- Layer A 의 캐시 키 단순화 → 메모리 효율 ↑ (scope 별 중복 캐시 없음)
- Layer A 가 옵션 무관 → 진짜로 "Source" 책임만 가짐 (3-layer 모델의 일관성)

**나빠짐**:
- Raw load 가 더 많은 row 읽음 — `data_scope=charge` 일 때 dchg row 도 로딩
  - 영향: 메모리 ~2배 (chg/dchg 비율 50/50 가정), CPU ~20-30% 증가 (raw parsing)
- 큰 채널 (수만 row) 에서 첫 로드가 더 느림

**리스크**:
- 메모리 부담 — 사용자가 동시에 다중 채널 + 큰 TC 범위 분석 시 OOM 가능
- 완화책: 현재 Layer A 캐시는 채널 단위 dict — 사용 안 한 채널 cache 자동 evict 메커니즘 추가 검토

## Alternatives considered

- **현 상태 유지** (`data_scope` 가 Layer A 영향): 캐시 분리로 단순하지만 사용자 시나리오 최적화 못함
- **Lazy lazy loading** (Cond 별 sub-cache): 구현 복잡, 메모리/CPU trade-off 가 단일화와 비슷

## Related

- 3-layer 모델: `docs/adr/0001-profile-pipeline-3-layer-model.md`
- 도메인 용어: `CONTEXT.md` § "옵션 → Layer 영향 매트릭스"
- 향후 작업: Layer B 캐시 추가 (이 결정의 효과를 극대화)
- Grilling 세션: 260504 Q5

## 구현 상태

❌ **미구현** — 본 ADR 은 결정만 기록. 실제 코드 변경은 후속 PR.

PR 분리 권장:
1. **PR-1**: `_unified_pne_load_raw` 의 `data_scope` 파라미터 제거 + view step 1 mask 검증
2. **PR-2**: Layer B 캐시 추가 (`_channel_cache['unified_transformed']`)
3. **PR-3**: 캐시 무효화 trigger 정의 + 메모리 evict 정책
