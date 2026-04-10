---
date: 2026-04-10
tags: [BDT, 프로파일, 아키텍처, 분석, 리팩토링, 스텝필터]
---

# 프로파일 분석 옵션 구조 재설계 검토

## 1. 현재 구조 요약

### 1.1 UI 옵션 (4축 × 추가 옵션)

| 축 | 옵션 | 값 | 기본값 |
|---|------|---|-------|
| **데이터 범위** (data_scope) | 사이클/충전/방전 | cycle, charge, discharge | cycle |
| **연속성** (continuity) | 오버레이/이어서 | overlay, continuous | continuous |
| **X축** (axis_mode) | 시간/SOC | time, soc | time |
| **추가** | 휴지 포함 | bool | False |
| **추가** | dQ/dV | bool | False |

### 1.2 옵션 의존성 (현재 강제 규칙)

```
data_scope ≠ cycle  →  continuity = overlay (강제)
axis_mode = soc     →  continuity = overlay (강제)
continuity = continuous  →  axis_mode = time (강제)
```

### 1.3 유효 옵션 조합 (9가지)

| # | scope | continuity | axis | 용도 | 현재 코드 경로 |
|---|-------|-----------|------|------|---------------|
| 1 | cycle | continuous | time | **연속 프로파일** (주력) | `pro_continue_confirm_button` (레거시) |
| 2 | charge | continuous | time | 충전 연속 | `pro_continue_confirm_button` (레거시) |
| 3 | discharge | continuous | time | 방전 연속 | `pro_continue_confirm_button` (레거시) |
| 4 | cycle | overlay | time | 사이클 오버레이 | `unified (step)` |
| 5 | charge | overlay | time | 충전 오버레이 | `unified (step)` |
| 6 | discharge | overlay | time | 방전 오버레이 | `unified (step)` |
| 7 | charge | overlay | soc | 충전 SOC+dQdV | `unified (chg)` |
| 8 | discharge | overlay | soc | 방전 SOC+dQdV | `unified (dchg)` |
| 9 | cycle | overlay | soc | 사이클 SOC+dQdV | `unified (cycle_soc)` |

---

## 2. 문제점 5가지

### P1. 옵션 변경마다 전체 데이터 재로드

```
사용자: "충전 → 방전" 변경 후 ▶ 클릭
  → SaveData CSV 또는 .cyc 재로드 (동일 데이터)
  → Stage 1~7 전체 재실행

실제 변경 영향: Stage 3 (필터) 이후만 다시 계산하면 됨
```

**현재 비용**: 옵션 변경당 ~150ms (대형 파일)
**이상적 비용**: ~5ms (필터+정규화+축만 재계산)

### P2. continue 모드가 별도 코드 경로

```
조합 #1~3 (continuous) → pro_continue_confirm_button()
  → pne_continue_data() → pne_Profile_continue_data()
  → 완전 다른 코드 (레거시 경로, OCV/CCV merge 포함)

조합 #4~9 (overlay) → unified_profile_confirm_button()
  → _load_all_unified_parallel() → unified_profile_core()
  → 정규화된 파이프라인

결과: .cyc 최적화를 양쪽에 별도 적용 필요
      OCV/CCV 기능이 continue에만 존재
```

### P3. 옵션 의존성 이중 관리

```
UI: _profile_opt_scope_changed() → setEnabled/setChecked
코어: unified_profile_core() L1999-2002 → 동일 강제

→ 새 옵션 추가 시 두 곳 수정 필요
→ 불일치 가능성
```

### P4. 사이클 패턴별 차이 미고려

```
패턴 A (55.9%): 충전×4 → 방전×2 → 정상
패턴 D (4.8%): 방전만 → "충전" scope 선택 시 빈 결과
패턴 F (0.4%): HPPC 60+ 스텝 → 스텝 병합 시 비효율
패턴 E (6.0%): 충전만 → "방전" scope 선택 시 빈 결과
```

### P5. 레거시 함수 잔존

```
숨김 버튼 5개 + 대응 함수 5개가 코드에 남아있음
→ step_confirm_button, chg_confirm_button, dchg_confirm_button,
   continue_confirm_button, rate_confirm_button
→ 직접 호출되지 않지만 코드 복잡도 증가
```

---

## 3. 개선안: "로드 1회 + 옵션별 재처리" 아키텍처

### 3.1 핵심 아이디어

```
┌─────────────────────────────────────────────────────────┐
│  ▶ 버튼 클릭                                             │
│                                                         │
│  [Stage 1-2] 원시 데이터 로드 (1회, 캐시)                  │
│    .cyc seek 또는 CSV → raw DataFrame (숫자 인덱스 컬럼)    │
│    캐시 키: (channel_path, cycle_range)                   │
│    → _raw_profile_cache[channel] = raw_df                │
│                                                         │
│  [Stage 3+] 옵션별 처리 (캐시된 raw에서 재계산)             │
│    raw → filter(scope) → normalize → merge → axis → dQdV │
│    옵션 변경 시 이 단계만 재실행                              │
│                                                         │
│  [렌더링] 그래프 출력                                      │
└─────────────────────────────────────────────────────────┘
```

### 3.2 데이터 로드 계층

```
Level 0: .cyc 바이너리 (디스크)
  ↓ seek+read (0.3ms/사이클, 150ms/전체)
Level 1: raw_profile_cache (메모리, 숫자 인덱스 48컬럼)
  ↓ filter + normalize (~5ms)
Level 2: processed_cache (메모리, 명명 컬럼)
  ↓ axis + dQdV (~2ms)
Level 3: UnifiedProfileResult (그래프용)
```

**옵션 변경 시 영향 범위**:

| 옵션 변경 | 재실행 시작 Level | 예상 시간 |
|----------|-----------------|----------|
| data_scope 변경 | Level 1 → 2 (필터부터) | ~5ms |
| continuity 변경 | Level 2 → 3 (축 계산부터) | ~2ms |
| axis_mode 변경 | Level 2 → 3 | ~2ms |
| include_rest 변경 | Level 1 → 2 | ~5ms |
| calc_dqdv 변경 | Level 2 → 3 | ~2ms |
| **사이클 범위 변경** | **Level 0 → 1 (재로드)** | **~150ms** |

### 3.3 continue 모드 통합

```
[현재] 2개 분리 경로
  overlay → unified_profile_core() → _unified_pne_load_raw()
  continuous → pro_continue_confirm_button() → pne_continue_data()

[개선] 1개 통합 경로
  모든 옵션 → unified_profile_core()
  continuous 모드에서 OCV/CCV가 필요하면:
    → Stage 4.5에서 SaveEndData 기반 OCV/CCV merge 추가
    → 별도 레거시 경로 불필요
```

### 3.4 옵션 의존성 단일 관리

```python
# 단일 함수로 옵션 정규화
def _normalize_profile_options(data_scope, continuity, axis_mode,
                                include_rest, calc_dqdv) -> dict:
    """옵션 의존성을 한 곳에서 강제."""
    if data_scope != "cycle":
        continuity = "overlay"
    if axis_mode == "soc":
        continuity = "overlay"
    if continuity == "continuous":
        axis_mode = "time"
    if axis_mode == "soc":
        calc_dqdv = True
    return {
        "data_scope": data_scope,
        "continuity": continuity,
        "axis_mode": axis_mode,
        "include_rest": include_rest,
        "calc_dqdv": calc_dqdv,
    }

# UI: _normalize_profile_options() 호출 → 위젯 상태 업데이트
# 코어: _normalize_profile_options() 호출 → 처리 진행
# → 단일 소스, 불일치 불가
```

---

## 4. 사이클 패턴별 고려사항

### 4.1 패턴-옵션 호환 매트릭스

| 패턴 | cycle | charge | discharge | overlay | continuous |
|------|:-----:|:------:|:---------:|:-------:|:---------:|
| **A. 다단CC+CC방전** (56.8%) | O | O | O | O | O |
| **B. 다단CC+단일방전** (21.3%) | O | O | O | O | O |
| **C. 단순 CC충/방전** (4.2%) | O | O | O | O | O |
| **D. 초기방전** (4.8%) | O | X(빈) | O | O | O |
| **E. 충전만** (6.0%) | O | O | X(빈) | O | O |
| **F. HPPC/Pulse** (0.4%) | O | O(짧) | O(펄스) | O | O |
| **G. ECT 스윕** (2.4%) | O | O | O | O | O |

### 4.2 빈 결과 처리 전략

```python
# 현재: 빈 결과 → 무응답 (그래프 없음, 에러 없음)
# 개선: 빈 결과 → 사용자에게 알림

if filtered.empty:
    # 해당 사이클에 {scope} 데이터가 없습니다.
    # 예: "사이클 1은 초기방전 패턴으로, 충전 데이터가 없습니다."
    pattern_hint = _detect_cycle_pattern(raw)  # 패턴 자동 감지
    return UnifiedProfileResult(
        df=pd.DataFrame(),
        metadata={"warning": f"TC {cycle}: {pattern_hint} — {scope} 데이터 없음"}
    )
```

---

## 5. 구현 단계

### Phase 1: 원시 데이터 캐시 계층 추가 (핵심)

```
목표: .cyc 또는 CSV에서 1회 로드한 raw DataFrame을 채널별 캐시
영향: _unified_pne_load_raw() 수정
수정 범위: ~50줄
효과: 옵션 변경 시 I/O 제거 (150ms → 0ms)
```

### Phase 2: continue 모드를 unified 경로로 통합

```
목표: pro_continue_confirm_button()의 레거시 경로 제거
      unified_profile_core()에서 continuous + OCV/CCV 지원
영향: unified_profile_core Stage 4.5 추가
수정 범위: ~100줄
효과: 코드 경로 통합, .cyc 최적화 자동 적용
```

### Phase 3: 옵션 의존성 단일화 + 빈 결과 알림

```
목표: _normalize_profile_options() 도입
      UI/코어 양쪽에서 동일 함수 호출
      빈 결과 시 패턴 기반 가이드 메시지
수정 범위: ~30줄
효과: 옵션 관리 단순화, UX 개선
```

### Phase 4: 레거시 함수 정리

```
목표: 숨김 버튼 5개 + 대응 함수 5개 제거
전제: Phase 1~3 완료 후 regression 확인
효과: 코드 ~500줄 감소
```

---

## 6. 기대 효과 요약

| 항목 | 현재 | 개선 후 |
|------|------|--------|
| 옵션 변경 시 응답 | ~150ms (재로드) | ~5ms (캐시 재처리) |
| 코드 경로 | 2개 (unified + continue 레거시) | 1개 (unified) |
| 옵션 의존성 관리 | 2곳 (UI + 코어) | 1곳 (_normalize) |
| .cyc 최적화 적용 | 2곳 별도 적용 | 1곳 자동 적용 |
| 빈 결과 대응 | 무응답 | 패턴 기반 안내 메시지 |
| 레거시 코드 | ~500줄 잔존 | 제거 |

---

## 8. 스텝 필터 규칙 (확정)

### 8.1 필터 결정 테이블

```
┌──────────────┬───────────────┬───────────────┬───────────────┐
│              │  scope=cycle  │ scope=charge  │scope=discharge│
├──────────────┼───────────────┼───────────────┼───────────────┤
│ CHG (1, 9)   │    포함        │    포함        │    제외        │
│ DCHG (2)     │    포함        │    제외        │    포함        │
│ REST (3)     │  include_rest │  include_rest │  include_rest │
│ LOOP (8)     │    제외        │    제외        │    제외        │
└──────────────┴───────────────┴───────────────┴───────────────┘
```

- **scope**: CHG/DCHG 포함 여부만 결정
- **include_rest**: 모든 REST 스텝의 포함/제외를 제어 (그룹 사이 휴지 의미)
- **LOOP**: 항상 제외

### 8.2 카테고리별 적용 결과

```
[A] 다단CC+CC방전 — 충전x4 → 휴지 → 방전x2 → 휴지 → 루프
    cycle,  rest=OFF:  CHGx4 + DCHGx2           = 6/9
    charge, rest=OFF:  CHGx4                     = 4/9
    dchg,   rest=OFF:  DCHGx2                    = 2/9

[B] 다단CC+단일방전 — 충전x4 → 휴지 → 방전 → 휴지 → 루프
    cycle,  rest=OFF:  CHGx4 + DCHGx1           = 5/8
    charge, rest=OFF:  CHGx4                     = 4/8
    dchg,   rest=OFF:  DCHGx1                    = 1/8

[E] 충전만/RPT — 충전 → 휴지 → 루프
    cycle,  rest=OFF:  CHGx1                     = 1/3
    charge, rest=OFF:  CHGx1                     = 1/3
    dchg,   rest=OFF:  (빈 결과!)                       ← 안내 메시지

[D] 초기방전 — 방전 → 휴지 → 루프
    cycle,  rest=OFF:  DCHGx1                    = 1/3
    charge, rest=OFF:  (빈 결과!)                       ← 안내 메시지
    dchg,   rest=OFF:  DCHGx1                    = 1/3

[C] 단순CC — 충전 → 휴지 → 방전 → 휴지 → 루프
    cycle,  rest=OFF:  CHGx1 + DCHGx1           = 2/5
    charge, rest=OFF:  CHGx1                     = 1/5
    dchg,   rest=OFF:  DCHGx1                    = 1/5

[G] ECT 스윕 — (휴지→충전→방전)x5 → 충전 → 루프
    cycle,  rest=OFF:  CHGx5 + DCHGx4           = 9/14
    charge, rest=OFF:  CHGx5                     = 5/14
    charge, rest=ON:   (REST+CHG)x5             = 10/14
    dchg,   rest=OFF:  DCHGx4                    = 4/14
    dchg,   rest=ON:   (DCHG+REST)x4            = 8/14

[F] HPPC — 충전x4 → 휴지 → (방전→휴지)x33
    cycle,  rest=OFF:  CHGx4 + DCHGx33          = 37/~70
    charge, rest=OFF:  CHGx4                     = 4/~70
    dchg,   rest=OFF:  DCHGx33                   = 33/~70
    dchg,   rest=ON:   (DCHG+REST)x33           = 66/~70
```

### 8.3 빈 결과 처리

```
조건: scope 필터 후 CHG/DCHG가 0개 (REST만 또는 완전히 빈 결과)
동작: 그래프 영역에 안내 → "TC {N}: 충전 데이터 없음 (초기방전 패턴)"
      사이클 건너뛰기 (에러 아님)

발생 조합:
  패턴 D(초기방전, 4.8%) + scope=charge     → 빈
  패턴 E(충전만,   6.0%) + scope=discharge  → 빈
```

### 8.4 구현 의사코드

```python
def filter_profile_steps(raw_df, scope, include_rest):
    condition = raw_df[2]  # StepType
    mask = condition != 8  # LOOP 제외

    if scope == "charge":
        mask &= condition.isin([1, 9]) | (condition == 3)
    elif scope == "discharge":
        mask &= (condition == 2) | (condition == 3)

    if not include_rest:
        mask &= condition != 3

    return raw_df.loc[mask]
```

---

## 7. 개선 전후 데이터 흐름 비교

### 현재 (Before)

```
┌─ ▶ 클릭 ──────────────────────────────────────────────┐
│                                                       │
│  if continuous:                                       │
│    pro_continue_confirm_button()                      │
│      → pne_continue_data() → CSV/CYC 로드             │
│      → pne_Profile_continue_data() → OCV/CCV merge    │
│      → pne_continue_profile_scale_change()            │
│      → 렌더링 (별도 루프)                               │
│                                                       │
│  else:                                                │
│    unified_profile_confirm_button()                    │
│      → _load_all_unified_parallel()                   │
│        → unified_profile_batch()                      │
│          → _unified_pne_load_raw() → CSV 로드          │
│          → filter → normalize → merge → axis → dQdV   │
│      → _profile_render_loop()                         │
│                                                       │
│  옵션 변경 시: 전체 재실행                                │
└───────────────────────────────────────────────────────┘
```

### 개선 후 (After)

```
┌─ ▶ 클릭 ──────────────────────────────────────────────┐
│                                                       │
│  [1회] _load_raw_cached()                              │
│    → .cyc seek (캐시 히트 시 0ms)                       │
│    → raw_cache[channel] = raw_df                      │
│                                                       │
│  [매번] _process_with_options(raw_df, options)          │
│    → filter(scope, include_rest)                      │
│    → normalize(units)                                 │
│    → merge(steps)                                     │
│    → axis(time or soc)                                │
│    → dqdv(if needed)                                  │
│    → OCV/CCV(if continuous + CDstate=="")             │
│    → UnifiedProfileResult                             │
│                                                       │
│  [렌더링] 통합 render loop                               │
│                                                       │
│  옵션 변경 시: [매번] 블록만 재실행 (~5ms)                 │
└───────────────────────────────────────────────────────┘
```
