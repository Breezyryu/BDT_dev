# BDT — 도메인 용어 정의

이 문서는 **도메인 전문가** (배터리 평가 엔지니어 + BDT 개발자) 가 공유하는 용어를 정의한다.
구현 디테일은 코드/wiki 에 두고, 여기에는 **의미** 만 기록한다.

용어가 새로 합의될 때마다 inline 업데이트 — 코드 PR 과 함께 진화.

---

## Profile 분석 파이프라인 (preset 4/5/3 공통)

### Layer 모델

3-layer 구조로 정형화 (260503 grilling 결정):

| Layer | 책임 | 옵션 의존 | 캐시 |
|---|---|---|---|
| **A. Source** | Raw IO + 사이클러 판별 + 메타 확보 | `raw_path`, `cycle_range` 만 | 채널 단위 영구 |
| **B. Transform** | 필터·정규화·병합·블록 할당 | `include_cv`, `mincapacity`, `firstCrate` | (TC range, 위 옵션) 단위 |
| **C. View** | scope/overlap/axis 변환 + cutoff + dQdV | `data_scope`, `axis_mode`, `overlap`, `cutoff`, `include_rest`, `smooth_degree`, `unified_flow`, `hyst_pair` | 캐시 안 함 (옵션 조합 너무 많음) |

**Layer A 단일화** (260503 결정): `data_scope` 가 view 단계에서만 적용됨. Raw load 는 항상 모든 Cond (1, 2, 3) 로딩 → scope 토글 시 raw 재로드 없음.

### Pipeline boundary (옵션 B)

`unified_profile_core(raw_path, tc_range, options)` 의 입출력이 파이프라인 경계.
- 시작: 함수 호출 (TC + 옵션 입력)
- 끝: `UnifiedProfileResult.df` 반환 (DataFrame + 메타)
- 미포함: 사용자 클릭 → 경로 정제, matplotlib artist 생성, Excel writer

이 경계는 테스트 가능성 (순수 함수) + 재사용성 (다른 분석기에서 결과 소비) 을 보장.

### Dual flow (C1 / C2)

Layer C 에 두 sub-algorithm 공존 (260503 grilling 결정):

| Sub-flow | 트리거 | dQdV 위치 | 적용 preset |
|---|---|---|---|
| **C1** (`unified_flow=True`) | hyst preset 3 자동 | cutoff **전** (모든 Condition row) | preset 3 (히스테리시스) |
| **C2** (`unified_flow=False`) | 그 외 | cutoff **후** (필터된 row 만) | preset 1, 2, 4, 5 |

차이는 **dQdV 산출량** — C1 은 CV 영역도 dQdV 계산 후 마스킹 (Fix 4), C2 는 cutoff 후 dQdV.

C2 → C1 으로의 통합은 **별도 후속 작업** (회귀 risk 큼).

### 사이클 데이터 탭의 sub-pipeline 분리

| Sub-tab | 파이프라인 | 도메인 |
|---|---|---|
| **Cycle** | `unified_cyc_confirm_button` | SaveEndData → cycle 별 집계 (DchgCap, Eff, RndV, dcir vs cycle_no) |
| **Profile** | `unified_profile_confirm_button` | Raw .cyc → within-cycle profile (V vs SOC per TC) |

**공유 layer**: 경로 테이블 파싱, 채널·TC autofill, 메타 캐시, raw load, SaveEndData 캐시, TC 분류기 (`_classify_loop_group`), .sch 파싱.

**분리 layer** (의도): 도메인 변환 + 시각화 (다른 의미).

---

## TC 분류 카테고리

`_classify_loop_group` (`.sch` 파싱 기반) 이 22 카테고리 분류:

```
INIT, FORMATION, ACCEL, RPT, CHG_DCHG, GITT_PULSE, SWEEP_PULSE,
SOC_DCIR, PULSE_DCIR, RSS_DCIR, HYSTERESIS_CHG, HYSTERESIS_DCHG,
CHARGE_SET, DISCHARGE_SET, DCHG_SET, TERMINATION, FLOATING,
POWER_CHG, REST_LONG, REST_SHORT, EMPTY, UNKNOWN
```

### 히스테리시스 카테고리 (260503 라벨 변경)

- **`HYSTERESIS_DCHG`** = 방충전 히스테리시스 — TC N 의 dchg + TC N+1 의 chg = closed loop (cross-TC pairing)
- **`HYSTERESIS_CHG`** = 충방전 히스테리시스 — TC N 의 chg + TC N 의 dchg = closed loop (within-TC pairing)

구 라벨 ('히스테리시스(방전)' / '히스테리시스(충전)') 는 alias 로 호환.

### Envelope (depth 100% reference)

Hysteresis fan 에서 **가장 outer 한 loop** = depth 100% = cell 의 풀 chg/dchg reference.

- `_merge_hysteresis_envelopes` (Fix 5) 가 자동 흡수 — `.sch` 의 voltage cutoff 기반 RPT 가 hyst 그룹 직후 인접 시 envelope 으로 분류 변경
- 사용자 protocol 의 TC 12 (방충전 envelope), TC 23 (충방전 envelope) 가 자동 인식

---

## SOC anchor

### Phase-relative anchor (Layer 1, oper1.py 정책)

각 phase 의 첫 row 가 X = 0 에서 출발하는 정규화된 누적 ChgCap/DchgCap.
- 충전 분석 (preset 4): X = ChgCap (0 → 1)
- 방전 분석 (preset 5): X = DchgCap (0 → 1, 라벨 "DOD")
- 사용자 manual Excel workflow 의 raw paste 시트 ([3~12_충전], [3~12_방전]) 와 numerically 동일

### Absolute cell SOC anchor (Layer 2, hysteresis preset 3)

각 TC 의 SOC 가 cell 의 절대 state of charge 좌표.
- `_compute_tc_soc_offsets` 가 cumul 로 산출
- `_apply_hysteresis_soc_offsets` 가 raw SOC 를 shift
- Cross-TC 페어링 (TC N dchg + TC N+1 chg) 으로 closed loop fan 형성

### Phase canonical anchor (Layer 2-α/β, 260503 추가)

Layer 2 의 cumul drift + CC-CV 잉여 보정.
- **2-α**: phase 첫 row → canonical SOC (Dchg→1.0, Chg→0.0) shift
- **2-β**: dchg phase 의 마지막 row → canonical end (`1 − depth%/100` Dchg, `0.0` Chg) linear scaling

### SOC = 1 − DOD 일관성 (Fix 6)

preset 4/5 의 axis_mode (SOC/DOD) 토글 시 `_calc_soc` 가 `1 − x` 변환으로 일관 유지.
- 충전 + SOC: ChgCap (0 → 1)
- 충전 + DOD: 1 − ChgCap (1 → 0)
- 방전 + SOC: 1 − DchgCap (1 → 0)
- 방전 + DOD: DchgCap (0 → 1)

---

## TC 메타데이터 (260503 grilling 결정)

각 TC 그룹의 추가 정보 — UI 표시 안 함, 메타정보만 보유 (미래 활용 여지).

| 항목 | Source | 적용 카테고리 |
|---|---|---|
| **SOC 범위** (시작/끝) | `.sch` 파싱 (EC 값) | `SOC_DCIR`, `RSS_DCIR`, `HYSTERESIS_*`, `GITT_PULSE` |
| **C-rate** (chg/dchg) | `.sch` 파싱 | 모든 카테고리 (이미 있음) |
| **휴지 시간** | `.sch` REST step 의 `time_limit_s` 합산 | 모든 카테고리 |
| **온도 평균** | 실측 raw 데이터 (`Temp` 컬럼) | 모든 카테고리, **TC 그룹 전체 평균** |

**산출 시점**: `_build_channel_meta` 에 통합 — meta cache 시점에 한 번만 계산, 이후 재사용.

---

## 옵션 → Layer 영향 매트릭스

| 옵션 | A | B | C | 비고 |
|---|---|---|---|---|
| `raw_path` | ✅ | | | 채널 식별 |
| `cycle_range` | ✅ | ✅ (multi_tc 분기) | | TC 범위 |
| `data_scope` | ❌ (단일화 후) | ❌ | ✅ | view 에서만 mask |
| `include_cv` | | ✅ | | Stage 3 CC 재분류 |
| `mincapacity` | | ✅ | | Stage 4 정규화 |
| `firstCrate` | | ✅ | | Stage 3 휴지 분류 |
| `axis_mode`, `overlap` | | | ✅ | view step 2-3 |
| `cutoff`, `include_rest` | | | ✅ | view step 1, 4 |
| `calc_dqdv`, `smooth_degree` | | | ✅ | dQdV 계산 |
| `unified_flow`, `hyst_pair` | | | ✅ | C1 vs C2 분기 |

### 사용자 시나리오 별 캐시 hit (Layer B 캐시 추가 후)

| 시나리오 | A 재사용 | B 재사용 | C 재실행 |
|---|---|---|---|
| 충전 ↔ 방전 분석 토글 | ✅ | ✅ (단일화 후) | ✅ |
| axis SOC ↔ DOD 토글 | ✅ | ✅ | ✅ |
| cutoff 변경 | ✅ | ✅ | ✅ |
| `include_cv` 토글 | ✅ | ❌ | ✅ |
| TC 범위 변경 | ❌ | ❌ | ✅ |

---

## 미해결 / 후속 작업

1. **Item 3 (옵션별 plot + 데이터 출력 + 저장)** — 6 평가 항목 매핑 + 사이클 바 직교 layer 로 발전. 단 22 카테고리 재검증 prerequisite. plan: `wiki/10_cycle_data/260504_plan_22cat_audit_and_eval_overlay.md`
2. **Toyo .ptn 파싱 강화** — 후속 (현재 PNE 위주)
3. **C2 → C1 dual flow 통합** — 별도 PR (회귀 risk 큰 작업)
4. **dQdV 별도 메모이즈** — 보류 (이점 marginal)
5. **사용자 override 메커니즘** (분류 수정) — 보류
6. **사이클 분류기 (22 카테고리) 재검증** (260504 grilling) — `.sch` parsing gap → 187 폴더 통계 → spec audit → 코드 fix → 정확도 측정. 5단계 plan 위 Item 1 참조. ADR-0012 후보 (평가 매핑 직교 layer) 는 audit 완료 후 정식화.
