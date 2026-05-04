---
title: "Phase 0-1b: `.sch` 식별 가능 field 전체 list-up (4 sample binary dump)"
date: 2026-05-04
tags: [audit, sch-parser, binary, gap-analysis, phase0, extractable-fields]
related:
  - "[[260504_plan_22cat_audit_and_eval_overlay]]"
  - "[[260504_audit_phase0_sch_parsing_gap]]"
status: phase-0-1b-complete
---

# Phase 0-1b: `.sch` 식별 가능 field 전체 list-up

> 사용자 명시 작업 (260504): "어떤 정보를 파싱할 수 있는 지 전부 리스트업".
> 4 sample binary dump 결과로 식별 가능한 모든 field 정리.

---

## TL;DR

- 5 시험종류 중 4 sample (`hysteresis`, `floating`, `GITT`, `수명`) binary dump 완료.
- **Header (1920 bytes) 식별 가능 field = 11개** (parser 사용 1 / 미사용 10).
  - ⭐⭐⭐ `+664 schedule description` = **시험명 (가장 강력한 keyword hint)**
  - ⭐⭐ `+336 user_category` (cp949) — 사용자 분류 ("개인_현혜정", "선행랩_류성택")
  - ⭐⭐ `+728 comment` (ASCII) — 부가 설명 (조건/cycle range)
  - 2 datetime (created, modified)
  - version/count meta 4종
- **Step block (652 bytes) 신규 식별 field = 6개** (parser 미사용):
  - ⭐ `+84 mode_flag` (uint32, 1 or 0)
  - ⭐ `+92, +96, +100` voltage/current safety bounds (float32)
  - ⭐ `+388 record_interval_secondary` (float32, 60s)
  - `+496 capacity_safety` (float32, 수명 sample only)
- Parser 사용율 = **10% (64 / 652 bytes per step + ~30 / 1920 bytes header)**.
- 본 dump 가 phase 0-2 (187 전수) 의 **schema baseline**.
- 도구: [`tools/sch_dump.py`](../../tools/sch_dump.py) — 187 전수 dump 에 재사용.

---

## 1. 4 Sample 비교

| 시험종류 | Schedule description (+664) | Comment (+728) | User category (+336) | n_steps |
|---|---|---|---|---|
| 성능_hysteresis | `4875mAh 0.5C Voltage hysteresis test` | `(null)` | `개인_현혜정` | 136 |
| 수명_복합floating | `4.53V 4C 4905mAh Floating` | `Floating` | (없음) | 13 |
| 성능 (GITT) | `GITT01C_422mAh` | `4.5V-3.0V/15,23,45` | `선행랩_류성택` | 17 |
| 수명 | `Gen5+B 2335 mAh 2C Si Hybrid` | `4.55V 2C SEU4@1-1202` | `개인_나무늬` | 178 |

**시험명 keyword 패턴 (분류 hint 후보)**:
| Keyword | 22 카테고리 매핑 후보 |
|---|---|
| `hysteresis` / `Voltage hysteresis` | HYSTERESIS_DCHG / HYSTERESIS_CHG |
| `Floating` | FLOATING |
| `GITT` | GITT_PULSE |
| `ECT parameter` (이전 sample) | **현 22 카테고리에 없음 — 신규 후보** |
| `SOC별DCIR` / `DCIR` | SOC_DCIR / PULSE_DCIR / RSS_DCIR |
| `RPT` | RPT |
| `Si Hybrid` / `SEU4` | ACCEL |
| `FORMATION` / `화성` | FORMATION |

---

## 2. Header Field — 식별 가능 list (1920 bytes)

| Offset | 길이 | Type | Encoding | Field 의미 | Sample 값 | Parser 사용 |
|---|---|---|---|---|---|---|
| +0 | 4 | uint32 | - | **Magic** | 740721 (4 sample 동일) | ✅ 검증만 |
| +4 | 4 | uint32 | - | **Version** | 131077 (4 sample 동일) | ❌ |
| +8 | 4 | uint32 | - | **Header sub-size or count** | 50 (4 sample 동일) | ❌ |
| +72 | ~32 | string | ASCII | **File signature** | `PNE power supply schedule file.` | ❌ |
| +336 | ~32 | string | cp949 | ⭐⭐ **User category / 작성자** | `개인_현혜정`, `선행랩_류성택`, `개인_나무늬` | ❌ |
| +587 ~ +610 | ~21 | string | cp949 | ⭐ **Created datetime (Korean)** | `2026-02-02 오후 6:50:05` | ❌ |
| +656 | 4 | uint32 | - | **Block-count meta (?)** | 1 (hyst), 13 (float), 13 (GITT), 5 (수명) — n_step 와 무관 | ❌ |
| +664 | ~32-64 | string | ASCII | ⭐⭐⭐ **Schedule description / 시험명** | `4875mAh 0.5C Voltage hysteresis test`, `4.53V 4C 4905mAh Floating`, `GITT01C_422mAh`, `Gen5+B 2335 mAh 2C Si Hybrid` | ❌ |
| +728 | ~16-32 | string | ASCII | ⭐⭐ **Comment / 부가 설명** | `(null)`, `Floating`, `4.5V-3.0V/15,23,45`, `SEU4@1-1202` | ❌ |
| +910 ~ +940 | ~21 | string | cp949 | ⭐ **Modified datetime (Korean)** | `2026-02-02 오후 6:50:17` | ❌ |
| +940 ~ +1919 | ~979 | ? | ? | 추가 metadata 영역 (대부분 0) | sparse non-zero | ❌ |

**+656 의미 추측**: n_steps (136, 13, 17, 178) 와 무관. 추정 후보:
- main loop iteration count
- sub-block 카운트
- protocol type indicator (1=hysteresis, 13=floating/GITT, 5=수명?)

→ Phase 0-2 에서 187 sample 분포로 의미 확정 가능.

---

## 3. Step Block Field — 식별 가능 list (652 bytes)

| Offset | Type | 의미 | Sample 값 (DCHG step 0) | Parser 사용 |
|---|---|---|---|---|
| +0 | uint32 | step_number | 1 | ✅ |
| +4 | uint32 | (미상) | 0 | ❌ |
| +8 | uint32 | type_code | 514 (0x0202=DCHG_CC) | ✅ |
| +12 | float32 | voltage_mV (CHG slot) | 0 in DCHG sample | ✅ |
| +16 | float32 | voltage_mV (DCHG slot) | 2500 | ✅ |
| +20 | float32 | current_mA | 466 / 1001 / 422 / 2438 (sample 별) | ✅ |
| +24 | float32 | time_limit_s | 1 (DCHG init) / 600 (REST) | ✅ |
| +28 | float32 | end_voltage_mV | 3000 | ✅ |
| +32 | float32 | end_current_mA | (CCCV only) | ✅ |
| +36 ~ +51 | 16B | (미상) | 0 | ❌ |
| +52 | uint32 | goto_target_step (LOOP) | (LOOP only) | ✅ |
| +56 | uint32 | loop_count / goto_target | (LOOP only) | ✅ |
| +60 ~ +83 | 24B | (미상) | 0 | ❌ |
| **+84** | uint32 | ⭐ **mode flag** | 1 (CHG/DCHG/REST), 0 (LOOP/GOTO) | ❌ |
| +88 | uint32 | (미상) | 0 | ❌ |
| **+92** | float32 | ⭐ **safety upper voltage (?)** | 2950 (4 sample 모두 동일 in DCHG) | ❌ |
| **+96** | float32 | ⭐ **safety upper current (?)** | 516 / 1051 / 472 (≈ +20 + 50) | ❌ |
| **+100** | float32 | ⭐ **safety lower current (?)** | 416 / 951 / 372 (≈ +20 - 50) | ❌ |
| +104 | float32 | capacity_limit_mAh | 5363 / 5396 / 464 / 2569 | ✅ (저장만) |
| +108 ~ +335 | 228B | (미상) — 최대 unknown | 0 (4 sample 모두) | ❌ |
| **+336** | float32 | ⭐ **record_interval_s (primary)** | 60 (4 sample 모두 동일) | ❌ docstring 만 |
| +340 ~ +371 | 32B | (미상) | 0 | ❌ |
| +372 | float32 | end_condition_value_pct | (EC steps only) | ✅ (저장만) |
| +376 ~ +387 | 12B | (미상) | 0 | ❌ |
| **+388** | float32 | ⭐ **record_interval_s (secondary)** | 60 (4 sample 모두 동일) | ❌ |
| +392 ~ +495 | 104B | (미상) | 0 | ❌ |
| **+496** | float32 | ⭐ **추가 capacity safety (?)** | 5400 (수명 sample only) | ❌ |
| +500 | uint32 | end_condition_type | (EC steps only, e.g. 2048=DOD%) | ✅ |
| +504 | uint32 | end_condition_enabled | 1 (EC enabled) | ✅ |
| +508 ~ +579 | 72B | (미상) | 0 | ❌ |
| +580 | uint32 | goto_repeat_count (LOOP) | (LOOP only) | ✅ |
| +584 ~ +651 | 68B | (미상) | 0 | ❌ |

**Parser 사용 통계**:
- 사용: 64 bytes / step (10%) — 14 fields
- 신규 식별: +28 bytes / step — 6 fields (+84, +92, +96, +100, +336, +388, +496)
- 여전히 unknown: +560 bytes / step (86%) — 대부분 zero, 일부 노이즈

---

## 4. 식별 가능 field 의 활용도 (분류 정확도 영향)

### Tier 1: 즉시 활용 가능 — Keyword classifier ⭐⭐⭐

`+664 schedule_description` 에서 keyword 추출 → 22 카테고리 disambiguate:

```python
# 의사 코드 — Phase c 의 보강 PR 후보
def _classify_by_keyword(schedule_desc: str) -> str | None:
    desc = schedule_desc.lower()
    if 'hysteresis' in desc:
        # voltage 방향까지 보면 dchg/chg 구분 가능
        return 'HYSTERESIS_DCHG'  # 또는 HYSTERESIS_CHG
    if 'floating' in desc:
        return 'FLOATING'
    if 'gitt' in desc:
        return 'GITT_PULSE'
    if 'ect parameter' in desc:
        return 'ECT'  # 신규 카테고리 후보
    if 'soc별dcir' in desc.replace(' ', '') or 'dcir' in desc:
        return 'SOC_DCIR'  # 또는 PULSE_DCIR
    if 'rpt' in desc:
        return 'RPT'
    if 'si hybrid' in desc or 'seu' in desc:
        return 'ACCEL'
    return None  # step pattern 으로 위임
```

이 layer 가 step pattern 분류기 위에 prior 또는 vote 로 통합되면 ambiguous 케이스 (HYSTERESIS_DCHG vs RSS_DCIR, GITT_PULSE vs SWEEP_PULSE 등) 정확도 큰 폭 향상 기대.

### Tier 2: 정합성 검증 — 사용자 입력 cross-check ⭐⭐

`+104 capacity_limit_mAh` (sch) ↔ 경로 테이블 `용량` 컬럼 — 사용자 오입력 detection.

| Sample | sch capacity | 경로 테이블 용량 |
|---|---|---|
| 성능_hysteresis | 5363 | (4875 입력 시) → 차이 ≈ 488 — capacity_limit 은 protection cap 으로 큼 |
| 수명_복합floating | 5396 | (4905 입력) → 491 차이 |
| 성능 (GITT) | 464 | (422 입력) → 42 차이 |
| 수명 | 2569 | (2335 입력) → 234 차이 |

→ `capacity_limit_mAh` ≈ 경로테이블용량 × 1.1 ± α (over-protection cap). 비율 검증으로 사용자 오입력 감지 가능.

### Tier 3: 메타데이터 활용 — 시험 lifecycle ⭐

- `+587 created_at`, `+910 modified_at` — schedule version 추적. modified > created 면 사용자가 수정한 protocol.
- `+336 user_category` — 사용자별 protocol library (개인 vs 선행랩). 평가 보고서 metadata.
- `+656 block_count_meta` — 의미 후속 검증.

### Tier 4: 안전 한계 — overshoot detection ⭐

- `+92, +96, +100` — voltage/current safety bounds. 실측 데이터의 spike detection.
- `+336, +388 record_interval_s` — sampling rate 메타.
- `+496` — 추가 capacity safety (수명 sample only).

---

## 5. Phase 0-2 다음 단계 (187 전수)

본 노트 = 4 sample baseline. Phase 0-2 = 187 폴더 전수 dump → schema 일관성 + keyword 분포 확정.

| Sub-step | 작업 | 산출 |
|---|---|---|
| 0-2-α | 187 .sch 전수 dump 자동 (`sch_dump.py --all-folders`) | CSV per file (offset, type, value) |
| 0-2-β | Header schema 검증 — `+0/+4/+8` invariant, `+664` schedule string 187 분포 | wiki md |
| 0-2-γ | Step block schema 검증 — `+84/+92/+96/+100/+336/+388/+496` 의 187 sample 값 분포 | wiki md |
| 0-2-δ | Keyword classifier 후보 — schedule description 의 시험종류별 빈도 + 카테고리 매핑 정확도 | wiki md |

산출물 위치: `wiki/10_cycle_data/260504_audit_phase0_2_187_schema_validation.md`

---

## 6. 본 dump 의 결론

### Parser 보강 priority (분류 정확도 영향 큰 순)

1. ⭐⭐⭐ **+664 schedule description (ASCII)** — keyword classifier 의 input. ambiguous 22 카테고리 disambiguate. ECT 같은 신규 카테고리 detect 도 가능.
2. ⭐⭐ **+336 user_category, +728 comment (cp949 / ASCII)** — schedule description 보강.
3. ⭐⭐ **+104 capacity_limit cross-check** — 사용자 오입력 detection.
4. ⭐ **+587/+910 datetimes** — protocol version 추적.
5. ⭐ **+92/+96/+100 safety bounds** — overshoot detection (분류기 영향 small).
6. ⭐ **+336/+388 record_interval** — sampling rate 메타 (분류기 영향 zero).

### 즉시 fix 가능 (이전 audit + 본 dump)

1. ⚠️ **`v_chg` 키 mismatch** ([phase0_sch_parsing_gap §3](260504_audit_phase0_sch_parsing_gap.md#3-즉시-fix-가능-bug-발견--v_chg-키-mismatch)) — FLOATING 카테고리 분류 무력. 1줄 수정.
2. **Parser 보강 PR 후보**: `_parse_pne_sch` 에 header 의 5 핵심 field 추출 (`+664 description`, `+336 user_category`, `+728 comment`, `+587 created`, `+910 modified`).

### 권장 작업 흐름

본 turn (phase 0-1b) 완료 → 별도 session 에서:
- **Phase 0-2** (187 전수 schema 검증) — `sch_dump.py` 가 baseline 도구
- **Phase c-α** (즉시 fix): `v_chg` 키 fix + parser header field 추출 보강

---

## Related

- [[260504_plan_22cat_audit_and_eval_overlay]] — 5단계 plan
- [[260504_audit_phase0_sch_parsing_gap]] — Phase 0-1a (코드 review only)
- 도구: [`tools/sch_dump.py`](../../tools/sch_dump.py) — 본 dump 스크립트, phase 0-2 전수 적용 가능
- [[hub_logical_cycle]] — 논리 사이클 hub

---

## 참고 코드 위치

- `DataTool_dev_code/DataTool_optRCD_proto_.py:7560` — PNE .sch parser
- L7594-7768 — `_parse_pne_sch` (header magic 만 read)
- L7975-8143 — `_classify_loop_group` 22 카테고리 룰
- L8053 — ⚠️ `v_chg` 키 mismatch bug
