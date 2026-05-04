# 0001. Profile 분석 파이프라인의 3-layer 모델 (A: Source / B: Transform / C: View)

날짜: 2026-05-04
상태: Accepted

## Context

`unified_profile_core` 가 사용자 옵션 (data_scope, axis_mode, overlap, cutoff, include_rest 등) 변경 시 매번 raw load 부터 dQdV 계산까지 전체 파이프라인을 재실행한다. 사용자가 axis 만 토글해도 raw IO + 정규화 + 병합 + dQdV 계산이 모두 다시 일어난다.

기존 캐시는 **Layer A (raw IO)** 에만 존재 (`_channel_cache['unified_raw']`). Stage 3-6 의 결과는 캐시 안 됨 → 옵션 토글마다 재계산.

3 가지 alternative 가 있었다:
- (i) 단일 stage — 모든 처리를 한 함수에 (현재와 유사, 캐시 가능 단위 모호)
- (ii) Stage 7-8 단계 (현재 코드의 Stage 1-6 + view step 1-4) — 단계는 많으나 캐시 boundary 가 모호
- (iii) 3-layer 모델 — Source / Transform / View 책임 분리 + 옵션 영향도 매핑

## Decision

**3-layer 모델 (A / B / C)** 채택:

- **Layer A (Source)** — 옵션 무관, 채널·TC 범위만 의존. Raw load + 사이클러 판별. 영구 캐시.
- **Layer B (Transform)** — 데이터 가공 옵션 (`include_cv`, `mincapacity`, `firstCrate`) 만 의존. 필터·정규화·병합. (TC range, B 옵션) 키로 캐시.
- **Layer C (View)** — 표시 옵션 (`data_scope`, `axis_mode`, `overlap`, `cutoff`, `include_rest`, `dQdV*`, `unified_flow`) 의존. SOC 변환 + cutoff + dQdV 계산. **캐시 안 함** (옵션 조합 너무 많고 결과 DataFrame 큼).

기존 stage 정의는 유지 — Stage 1-2 가 Layer A, Stage 3-5.5 가 Layer B, Stage 6 + view step 1-4 가 Layer C.

## Consequences

**좋아짐**:
- 옵션-layer 영향도 매트릭스 명확 → 어느 옵션이 어느 캐시를 무효화하는지 결정적
- 사용자 시나리오 (axis 토글, cutoff 변경 등) 에서 Layer B 캐시 hit → raw 재로드 + 정규화 절감
- 테스트 단위 분리 — 각 layer 가 순수 함수 (DataFrame in / out)
- 향후 dual flow (C1/C2) 통합 시 영향 범위가 Layer C 안으로 한정

**나빠짐**:
- 코드 mental model 추가 (3 layer 개념을 신규 개발자가 학습해야 함)
- Layer 경계 위반 발생 가능 (예: Layer B 가 axis_mode 참조하면 캐시 무효 위험)

**리스크**:
- Layer A 단일화 (별도 ADR 0002) 와 결합 시 raw load 가 항상 모든 Cond 로딩 → 메모리 사용 증가 (~2배). 큰 채널에서 영향 가능.

## Alternatives considered

- **(i) 단일 stage 유지**: 캐시 boundary 결정 곤란, 옵션-layer 매핑 불가능, 사용자 시나리오 별 최적화 불가
- **(ii) 더 세분화된 stage (현재 8 단계)**: 캐시 boundary 가 stage 단위로 8개 → 메모리/관리 비용 증가, ROI 낮음

## Related

- Layer A 단일화 결정: `docs/adr/0002-layer-a-data-scope-single-load.md`
- Dual flow (C1/C2) 보존 결정: `docs/adr/0003-dual-flow-c1-c2-preservation.md`
- 도메인 용어 정의: `CONTEXT.md` § "Profile 분석 파이프라인"
- Grilling 세션: 260504 (Q3-Q5 결정)
