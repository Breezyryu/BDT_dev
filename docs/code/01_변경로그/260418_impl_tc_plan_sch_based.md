# TC Plan (.sch 기반 TotalCycle 재구성) — P1 초기 구현

**날짜**: 2026-04-18  
**작업자**: Ryu + Claude  
**관련 브랜치/워크트리**: `claude/agitated-liskov-6c436a`

## 배경 / 목적

기존 `_cyc_to_cycle_df()`(라인 7991~8169)의 TC 재구성은 `.cyc` 바이너리의 StepTime 경계 + 휴리스틱(`_LOOP_JUMP=300s`, `_CC_CV_RATIO=0.05`, `last_d>100mAh`)에 의존한다. `.cyc`에는 TC/LoopCount 필드가 없어 부정확한 경계 판정 위험이 있다:

| 시나리오 | 현 휴리스틱 신뢰도 |
|---------|-------------------|
| 표준 Loop End 종료 | 🟢 높음 |
| 짧은 부분 방전 (<100 mAh) | 🔴 `cond_b` 실패 |
| 휴지 없는 연속 Loop | 🟠 `cond_a` 실패 |
| Loop 없는 반복 (충/방 쌍) | 🔴 TC=1 고정 |
| floating 장기 유지 | 🟠 판정 애매 |

`.sch` 시험 스케줄은 Loop 구조가 **정의상 100% 정확**하다는 특성을 이용해, `.cyc`·CSV 무관하게 StepNo → TC 매핑을 사전 산출하는 `TCPlan` 모듈을 신규 도입한다.

## 변경 내용

### 신규 파일

- `DataTool_dev_code/tools/tc_plan.py` (신규)
- `DataTool_dev_code/tools/tc_plan_verify.py` (신규 — 검증 스크립트)

### 주요 API

```python
@dataclass
class TCPlan:
    channel_dir: str
    active_sch: SchVariant
    variants: list[SchVariant]            # _NNN.sch 변경 이력
    step_to_tc_start: dict[int, int]      # StepNo → 해당 그룹 첫 TC
    tc_to_group: dict[int, TCGroup]       # TC → 그룹 메타
    groups: list[TCGroup]
    max_tc: int
    warnings: list[str]                   # variant diff 요약

    def resolve_tc(step_num, rep_idx=0) -> int | None
    def steps_of_tc(tc) -> list[int]
    def category_of_tc(tc) -> str | None

def build_tc_plan(channel_dir, step_num_offset=1) -> TCPlan | None
def discover_sch_variants(channel_dir) -> list[SchVariant]
def select_active_sch(variants) -> SchVariant | None
```

### 다중 `.sch` 대응

실증 결과 데이터셋 전반에 `_NNN.sch` 변경 이력이 흔함 (`성능/` 일부는 3개 버전).

**정책**:
- `이름.sch` (suffix 없음) = 현재 활성 패턴 → TC 계산 기준
- `이름_NNN.sch` = 변경 이력 → diff만 `warnings`에 기록
- 근거: `parse_all_sch.py`의 "잔여 사이클" 해석과 일치

### StepNo 오프셋

**실측 발견**: `.sch`의 1-based `step_num` ↔ 실측 SaveEndData `col[7]` StepNo 간 오프셋이 채널마다 다름:

| 케이스 | 오프셋 | 추정 원인 |
|-------|--------|----------|
| `ch55 floating` | +1 | 장비 내부 "Init Step 0" 추정 |
| `복합floating/최웅철` | +0 | .sch 1-based 그대로 |

→ `step_num_offset` 파라미터(기본 +1)로 노출. 검증 스크립트가 0~3 스캔하여 최적값 자동 선택.

### 제어 스텝(LOOP/REST_SAFE/GOTO) 그룹 귀속

이전: `split_into_loop_groups`에서 LOOP/REST_SAFE/GOTO를 body에서 완전 제외.
변경: **각 제어 스텝을 해당 그룹의 `control_step_nums`에 편입**. LOOP 마커의 실측 StepNo(StepType=8)도 `step_to_tc_start`에 매핑되어 범위 판정에 포함.

## 검증 결과

`exp_data/` 하위에서 `.sch + Restore` 모두 있는 채널 20개 전수 검증:

```
전체 일치율: 30.72%  (1621/5276)
오프셋 분포: {+0: 19, +1: 1}
```

**케이스별**:
- **단순 케이스 (2~11행)**: 100% 일치 (5/20 채널)
- **대량 반복 케이스 (200~400행)**: **23~45% 로 급락** (15/20 채널)

### 불일치 근본 원인: **GOTO 재순환 미구현**

예: `260126_ATL GEN4 / M01Ch051`
- 플랜 예상: `max_tc=16` (7개 그룹)
- 실측: `TC 1~40` (16 이후에도 StepNo 44~50이 같은 구조로 반복)
- **`.sch` 끝의 GOTO로 재순환되는 사이클이 TC 카운팅에 반영되지 않음**

현재 `split_into_loop_groups`는 GOTO를 "흐름 제어 마커"로만 처리하고 재실행 시맨틱을 무시.

## 영향 범위

### 추가된 것
- `tools/tc_plan.py` — 단일 모듈, 외부 의존성 `pandas` 미사용 (stdlib만)
- `tools/tc_plan_verify.py` — `pandas` 의존 (SaveEndData CSV 읽기)

### 기존 코드 영향
- **없음** — 신규 모듈만 추가, 기존 `_cyc_to_cycle_df`/`pne_build_cycle_map` 등 미수정
- 현재 상태에서는 검증 도구로서의 의미만 있음 (P4 통합 전까지)

## 다음 단계 (P2+)

1. **P2: GOTO 재순환 처리**
   - `.sch`의 GOTO target을 따라 가상 실행기(expand_schedule) 구현
   - 무한 루프 방지를 위한 `max_iterations` 제한 + `.cyc` 실측 타임스탬프로 실제 종료 추정
2. **P3: 교차검증 확장**
   - 수명/성능/복합floating 전 카테고리에서 일치율 ≥95% 확보
   - 실패 채널은 `.sch` 구조를 개별 분석 → 휴리스틱 보강
3. **P4: 기존 API 교체**
   - `get_cycle_map`, `_cyc_to_cycle_df`를 `TCPlan` 기반으로 리빌드
   - 소비자 12개 함수 회귀 테스트
4. **P5: 휴리스틱 제거**
   - `_LOOP_JUMP`, `_CC_CV_RATIO`, `last_d>100` 등 상수 삭제 (약 200줄 감량)

## 참고

- 관련 커밋: `a365032`, `6447953`, `c68aae4` (.cyc 프로파일 경로 도입)
- 관련 docs: `docs/code/03_코드리뷰_코드학습/260410_study_pne_cyc_vs_csv_structure.md`
- 검증 로그: `verify_plan` 실행 결과 (본 문서 검증 결과 섹션)
