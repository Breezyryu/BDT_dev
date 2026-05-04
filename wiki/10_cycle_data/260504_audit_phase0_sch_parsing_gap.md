---
title: "Phase 0-1: `.sch` parser gap audit (코드 review)"
date: 2026-05-04
tags: [audit, sch-parser, classify, gap-analysis, phase0, cycle-classify]
related:
  - "[[260504_plan_22cat_audit_and_eval_overlay]]"
  - "[[260418_p3_cyc_tier2_loop_detect]]"
  - "[[260419_사이클분류_전면재검토]]"
status: phase-0-1-complete
---

# Phase 0-1: `.sch` parser gap audit — 코드 review

> 22 카테고리 재검증 5단계의 첫 단계 — parser 가 `.sch` 의 어떤 정보를 읽고 / 무시하는지 + 분류기가 parser output 의 어떤 필드를 사용하는지 식별.

---

## TL;DR

- **Parser (`_parse_pne_sch`, L7594)** 가 step block 652 bytes 중 **~64 bytes 만 read** (~588 bytes 미사용, 90%).
- Header 1920 bytes 중 **+0 magic 4 bytes 만 read** (~1916 bytes 미사용 — string metadata 포함).
- **분류기 (`_classify_loop_group`, L7975)** 의 22 카테고리 판정은 parser output 의 ~10 필드만 사용.
- ⚠️ **즉시 fix 가능 bug 1건 발견**: 분류기 L8053 의 `v_chg_mV`/`v_chg` 키가 parser output (`voltage_mV`) 과 mismatch → **FLOATING 카테고리 분류 무력화**.
- **누락 의심 1순위**: header metadata (test_type, schedule name, comment 등 string field).
- **다음 단계 (0-2)**: 187 폴더 전수 hex dump → header string field 추출.

---

## 1. Parser 가 읽는 영역

### Header (1920 bytes)

| Offset | Type | 의미 | 사용 |
|---|---|---|---|
| +0 | uint32 | Magic (`740721`) | ✅ 검증만 |
| +4 ~ +1919 | ? | (미상) ~1916 bytes | ❌ 전부 미사용 |

**Raw cat 결과** (hysteresis sample, 성능_hysteresis/260202.../M01Ch022[022]/*.sch):

```
PNE power supply schedule file.
'_'
2026-02-02 ... 6:50:05
4875mAh 0.5C Voltage hysteresis test       ← schedule name / test description
(null)
2026-02-02 ... 6:50:17
```

→ Header 영역에 **schedule name, 날짜, comment** 등 string field 다수. parser 가 모두 무시.

### Step block (652 bytes / step)

| Offset | Type | 필드 | parser read | 분류기 사용 |
|---|---|---|---|---|
| +0 | uint32 | step_number | ✅ | (저장만) |
| +4 ~ +7 | ? | (미상) | ❌ | — |
| +8 | uint32 | type_code → `_SCH_TYPE_MAP` (14 types) | ✅ | ✅ all |
| +12 | float32 | voltage_mV (CHG) | ✅ | ⚠️ key mismatch (§3) |
| +16 | float32 | voltage_mV (DCHG) | ✅ | (저장만) |
| +20 | float32 | current_mA | ✅ | ✅ RPT 0.2C 판정 |
| +24 | float32 | time_limit_s | ✅ | ✅ GITT/FLOATING/PULSE |
| +28 | float32 | end_voltage_mV | ✅ | (저장만) |
| +32 | float32 | end_current_mA | ✅ | (CCCV alias 만) |
| +36 ~ +51 | ? | (미상) 16 bytes | ❌ | — |
| +52 | uint32 | goto_target_step (LOOP only) | ✅ | (outer goto 확장) |
| +56 | uint32 | loop_count (LOOP) / goto_target (GOTO) | ✅ | ✅ N |
| +60 ~ +103 | ? | (미상) 44 bytes | ❌ | — |
| +104 | float32 | capacity_limit_mAh | ✅ | ❌ (§4 #5) |
| +108 ~ +335 | ? | (미상) **228 bytes** — 최대 unknown | ❌ | — |
| +336 | uint32 | record_interval_s (주석에만 존재) | ❌ | — |
| +340 ~ +371 | ? | (미상) 32 bytes | ❌ | — |
| +372 | float32 | end_condition_value_pct | ✅ | ❌ (§4 #6) |
| +376 ~ +499 | ? | (미상) 124 bytes | ❌ | — |
| +500 | uint32 | end_condition_type (2048=DOD%, 18432=SOC%) | ✅ | ✅ HYSTERESIS, SOC_DCIR |
| +504 | uint32 | end_condition_enabled | ✅ | ✅ |
| +508 ~ +579 | ? | (미상) 72 bytes | ❌ | — |
| +580 | uint32 | goto_repeat_count (LOOP only) | ✅ | (outer goto 확장) |
| +584 ~ +651 | ? | (미상) 68 bytes | ❌ | — |

**합계**: parser read = ~64 bytes / 652 bytes (≈ **10%**) → 90% byte unknown.

---

## 2. 분류기가 사용하는 parser output

`_classify_loop_group` (L7975) 22 카테고리 판정 입력:

| 입력 | 출처 | 사용 카테고리 |
|---|---|---|
| `body` (loop 내 step list) | parser steps | 모든 |
| `loop_count` (N) | parser LOOP +56 | 모든 |
| `position`, `total_loops` | `_build_loop_group_info` 외부 계산 | INIT, TERMINATION |
| `capacity_mAh` | **외부 입력 (사용자 + 경로 테이블)** | RPT 판정 |
| `s['type']` | parser type_code → MAP | 모든 |
| `s['end_condition']['type']` | parser +500 | HYSTERESIS_DCHG (2048), HYSTERESIS_CHG (18432), SOC_DCIR |
| `s['end_condition']['value_pct']` | parser +372 | (저장만, 분류기 미사용) |
| `s['time_limit_s']` | parser +24 | GITT_PULSE (≥600s), short pulse (≤30s), FLOATING (≥43200s), REST_LONG (≥3600s) |
| `s['current_mA']` | parser +20 | RPT 0.2C ±30% |
| `s['v_chg_mV']` 또는 `s['v_chg']` | ⚠️ **parser 미발생 키** | FLOATING (§3) |

---

## 3. ⚠️ 즉시 fix 가능 bug 발견 — `v_chg` 키 mismatch

**위치**: `_classify_loop_group` L8049-8055 (FLOATING 판정 룰).

```python
# 2b. Floating: CC/CCCV 장시간(≥12h) 충전 + 방전 없음
if chg_steps and not dchg_steps:
    max_chg_time = max(
        (s.get('time_limit_s', 0) for s in chg_steps), default=0)
    has_v_cut = any(
        s.get('v_chg_mV', s.get('v_chg', 0)) > 0 for s in chg_steps)  # ⚠️
    if max_chg_time >= 43200 and has_v_cut:
        return 'FLOATING'
```

**문제**:
- Parser L7689 emit 하는 key: `'voltage_mV'`
- 분류기 L8053 lookup 하는 key: `'v_chg_mV'` 또는 `'v_chg'`
- 두 fallback 모두 parser output 에 없음 → `has_v_cut` **항상 `False`**
- → FLOATING 카테고리 **분류 불가** (max_chg_time 조건 만족해도 has_v_cut 게이트로 차단)

**영향 범위**: `수명_복합floating/` 22 폴더 + `성능/` 의 floating 시험들 (예: `Q7M Inner 2C 상온수명`, `LGES Gen5+ 1C Floating`, ...).

**Grep 확인**: `v_chg_mV` / `v_chg` 키는 parser 출력 어디에도 emit 되지 않음 (L7689, L7711 모두 `voltage_mV`).

**Fix 옵션**:
1. **분류기 수정** (1줄) — L8053 의 `v_chg_mV`/`v_chg` → `voltage_mV` 로 통일
2. **Parser 수정** (2줄) — L7689 / L7711 에 `'v_chg_mV': voltage_mV` alias 추가 (CHG 만)
3. **양쪽 모두** — robust

→ **권장: (1) 분류기 수정**. parser output schema 가 이미 일관 (`voltage_mV`), 분류기 코드만 정합 안 됨. fix 단순.

→ **검증 필요**: 187 폴더 중 floating 시험 (수명_복합floating 22 + 성능/수명 의 *floating* 폴더) 에서 fix 전후 카테고리 변화 비교.

→ Phase (c) 코드 fix 의 첫 PR 후보.

---

## 4. 누락 의심 (분류 정확도 손해 후보)

### 1. Header metadata (1916 bytes) — ⭐ **1순위**

`.sch` 의 hex 시작 부분에 string field 다수 발견:
- `PNE power supply schedule file.` (file signature)
- 작성 날짜 (예: `2026-02-02`)
- **schedule name / test description** (예: `4875mAh 0.5C Voltage hysteresis test`)
- comment / null

**활용 가능성**: schedule name 의 keyword (예: "hysteresis", "GITT", "ECT", "floating", "RPT", "DCIR") 가 카테고리 판정의 강력한 hint.

**현재 손해**: 분류기가 step pattern (type_code + EC + time_limit) 만 보고 판정 → **같은 step pattern 이 여러 카테고리에 매핑되는 ambiguous 케이스**에서 정확도 손해.

**예시 ambiguous 케이스**:
- HYSTERESIS_DCHG vs RSS_DCIR — 둘 다 N=1, dchg, EC 조건 일부 공유
- GITT_PULSE vs SWEEP_PULSE — 둘 다 N≥10, body≤3
- ACCEL vs SOC_DCIR — N 임계값과 EC 다양성 휴리스틱 충돌 가능

→ schedule name keyword classifier 가 보강 layer 로 추가되면 ambiguous 케이스 disambiguate 가능.

**다음 단계 (0-2)**: 187 .sch hex dump → header string field 의 byte offset/length 패턴 추출 → parser 보강.

### 2. Step block middle (~228 bytes at +108~+335) — 2순위

가장 큰 unknown 영역.

**활용 가능성**: 
- temperature limit (high/low cutoff)
- current direction sign / mode flag
- voltage rate (sweep test 의 dV/dt)
- per-step comment

**다음 단계**: PNE vendor spec 문서 확보 또는 binary diff (시험종류별 sample 비교).

### 3. `record_interval_s` (+336) — 4순위

Parser docstring 에 명시 (L7627) but 실제 코드 미참조.

활용 가능성: 시험 장비 sampling rate 메타. 분류 정확도 영향 작음.

### 4. `capacity_limit_mAh` (+104) — 5순위

Parser read 후 step_info 에 저장 (L7687). 분류기 미사용.

**활용 가능성**: 외부 입력 `capacity_mAh` (경로 테이블 "용량" 컬럼) 와 cross-check → 사용자 오입력 detection.

분류 정확도 향상보다는 정합성 검증 도구.

### 5. `end_condition_value_pct` (+372) — 6순위

Parser read + step_info 저장. 분류기는 EC `type` 만 사용, `value_pct` 는 미사용.

**활용 가능성**: 
- HYSTERESIS depth (10%, 20%, ...) 자동 매칭 → cross-TC pairing 정확도 향상
- 현재 `_merge_hysteresis_envelopes` 별도 휴리스틱 → value_pct 활용 시 단순화

---

## 5. Phase 0-2 다음 단계

> **0-1b 후속**: 4 sample binary dump 결과 → [[260504_audit_phase0_extractable_fields]] 에 식별 가능 field 전체 list-up 완료. 본 §5 의 sub-step 들이 0-1b 의 발견 사항으로 일부 갱신됨.

| Sub-step | 작업 | Cost |
|---|---|---|
| **0-2-α** | 187 폴더 .sch 전수 dump ([`sch_dump.py`](../../tools/sch_dump.py) 적용) | 자동, ~30분 |
| **0-2-β** | Header schema 검증 — `+0/+4/+8` invariant, `+664 schedule_description` 187 분포 | wiki md |
| **0-2-γ** | Step block schema 검증 — `+84/+92/+96/+100/+388/+496` 의 187 분포 | wiki md |
| **0-2-δ** | Keyword classifier 후보 — `+664` description 의 시험종류별 빈도 | wiki md |
| **0-2-ε** | `v_chg` 키 fix (즉시 가능) — 분류기 L8053 수정 | 코드 1줄 |

산출물: `wiki/10_cycle_data/260504_audit_phase0_2_187_schema_validation.md`

---

## 6. 본 audit 의 결론

### 즉시 조치 (Phase c 의 첫 PR 후보)
- ⚠️ **`v_chg` 키 mismatch fix** — 1줄 수정. FLOATING 카테고리 활성화. 22 폴더 + α 의 분류 결과 변화 검증 필요.

### 22 카테고리 신뢰도 손해의 prime suspect
1. **Header metadata 활용 부재** — keyword classifier 가 ambiguous 케이스 보강 layer.
2. **Step block ~588 bytes unknown** — vendor spec 확보 또는 binary diff 필요.
3. **`v_chg` 키 mismatch** — 즉시 fix.
4. (간접) `capacity_limit_mAh`, `value_pct` 미사용 — cross-check / pairing 정확도 보강 후보.

### 권장 다음 단계
**Phase 0-2 (header string extraction)** 진행. 본 turn 의 grilling wrap 후 별도 session.

---

## Related

- [[260504_plan_22cat_audit_and_eval_overlay]] — 5단계 plan
- [[260418_p3_cyc_tier2_loop_detect]] — TC 분류기 P3
- [[260419_사이클분류_전면재검토]] — 분류기 전면 재검토
- [[260504_daily_worklog]] — 본 grilling 진행일

---

## 참고 코드 위치

- `DataTool_dev_code/DataTool_optRCD_proto_.py:7560` — `# PNE .sch 바이너리 파서 (내장)`
- L7570-7584 — `_SCH_TYPE_MAP` (14 type codes)
- L7594-7768 — `_parse_pne_sch` 본체
- L7975-8143 — `_classify_loop_group` 22 카테고리 판정 룰
- L8053 — ⚠️ `v_chg` 키 mismatch bug
- L9430-9458 — `_CLASSIFIED_COLORS` (22 → 10 색상 팔레트)
- L9465-9549 — `_build_timeline_blocks_tc_by_loop` (사이클 바 블록 생성)
- L9674 — `CycleTimelineBar` 위젯
