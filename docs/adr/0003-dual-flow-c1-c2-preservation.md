# 0003. Layer C 안의 dual flow (C1 / C2) 보존 — 통합은 별도 후속 작업

날짜: 2026-05-04
상태: Accepted

## Context

`unified_profile_core` 의 Stage 6 (Layer C) 가 `unified_flow` 플래그에 따라 두 경로로 분기:

```
Stage 1-5.5 (공통)
  ├─ if unified_flow=True (히스테리시스 모드, 신 흐름):
  │     1. _unified_calculate_dqdv (cutoff 전, 모든 Cond)
  │     2. _unified_apply_view (Step 1-4: scope mask → time → SOC → cutoff)
  │
  └─ else (기존 흐름):
        1. _unified_calculate_axis (Stage 6: SOC + 시간축)
        2. cutoff (inline)
        3. _unified_calculate_dqdv (cutoff 후, 필터된 row)
```

두 경로는 **dQdV 산출량이 다름** (cutoff 전 vs 후 계산). 단순 코드 중복이 아니라 **의미가 다른 두 알고리즘**.

- C1 (`unified_flow=True`, 히스테리시스 preset 3): CV 영역도 dQdV 계산 후 Fix 4 mask 로 NaN 처리
- C2 (`unified_flow=False`, preset 1/2/4/5): cutoff 로 일부 row 빠진 후 dQdV → smoothing window 가 cutoff 위치에 의존

## Decision

**C1 / C2 dual flow 를 현 상태로 보존**한다. 통합 시도하지 않고, 3-layer 모델 안에서 Layer C 의 sub-algorithm 으로 명문화.

| Sub-flow | 트리거 | dQdV 위치 | 적용 preset |
|---|---|---|---|
| **C1** (`unified_flow=True`) | preset 3 (히스테리시스) 자동 | cutoff **전** | preset 3 |
| **C2** (`unified_flow=False`) | 그 외 | cutoff **후** | preset 1, 2, 4, 5 |

C2 → C1 으로의 통합 (단일 alg 화) 은 **별도 후속 PR** — 회귀 risk 가 본 작업 scope 넘어섬.

## Consequences

**좋아짐**:
- 즉시 breaking 회피 — preset 1/2/4/5 의 출력 보존
- Layer C 안에 dual-algorithm 이 명시 → 미래 reader 가 "왜 두 경로?" 의문 시 ADR 참조 가능
- 통합은 별도 작업으로 분리 → 충분한 회귀 검증 후 진행 가능

**나빠짐**:
- 코드 복잡도 유지 — Layer C 안에 분기 로직 존재
- dQdV 결과의 의미가 preset 별로 미묘하게 다름 → 사용자 인지 부담

**리스크**:
- C1 / C2 결과 차이가 사용자 보고로 부각될 가능성 (특히 dQdV 시각 비교 시)
- 완화책: CONTEXT.md 의 "Dual flow" 절에 차이 명시, wiki 노트 (260429) 참조

## Alternatives considered

- **(가) C1 으로 통일** (legacy C2 제거): preset 1/2/4/5 의 출력이 미세하게 변할 risk 큼. 회귀 검증 (모든 사내 protocol 30+ 종) 필요. 본 작업 scope 초과
- **(나) 코드 중복만 제거** (cutoff/dQdV 위치는 유지, 함수 추출): 의미 차이 보존하지만 정형화 효과 작음

## Related

- 3-layer 모델: `docs/adr/0001-profile-pipeline-3-layer-model.md`
- 도메인 용어: `CONTEXT.md` § "Dual flow (C1 / C2)"
- 통합 작업의 baseline: `wiki/40_work_log/260429_hysteresis_unified_flow.md`
- Fix 4 (CV 마스킹): `docs/code/01_변경로그/260503_fix_hysteresis_dchg_major_cross_tc_pair.md` § Fix 4
- Grilling 세션: 260504 Q4
