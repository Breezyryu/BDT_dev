# 260505 — Phase 0-5 분류기 v2 — 187 폴더 / 368 .sch 전수 분류 도구 추가

## 배경

[[wiki/10_cycle_data/260504_audit_phase0_5_classifier_input_spec]] 의 분류기 v2 spec 을
`raw/raw_exp/exp_data/` 187 폴더 / 368 `.sch` 전수에 적용. 사이클(loop group) 단위 정의를
CSV·md 로 산출.

## 변경 사항

### 신규 파일

- `tools/sch_phase0_5_classify_all.py` (553 줄) — Phase 0-5 self-contained 분류기 v2 batch 스크립트
- `tools/sch_phase0_5_groups.csv` (8,298 row × 24 col) — 사이클 단위 정의
- `tools/sch_phase0_5_files.csv` (368 row × 13 col) — 파일 단위 메타
- `tools/sch_phase0_5_summary.md` (자동 생성) — cross-table + UNKNOWN list + 폴더별 분포
- `wiki/10_cycle_data/260505_phase0_5_187_cycle_definitions.md` — 분석 결과 정식 노트

### Phase 0-5 spec 적용

1. ⚠️ `v_chg` 키 mismatch fix → batch script 에서 `voltage_mV` 사용 (proto 코드는 미수정)
2. CC vs CCCV V cutoff 분리 (사용자 통찰)
3. 9 신규 parser field 추가 (`v_safety_*`, `i_safety_*`, `chg/dchg_end_capacity_cutoff`,
   `record_interval_s`, `chamber_temp_c`, `mode_flag`, header `format_version` /
   `header_record_count` / `block_count_meta` / `schedule_description`)
4. Schedule keyword classifier (header `+664`)
5. `+336 < 5` short_sampling hint

### 핵심 결과

- **368 .sch parsed (0 failed) / 8,298 사이클 그룹 분류**
- 카테고리 분포: RPT 34.2 % > CHG_DCHG 11.7 % > ACCEL 11.2 % > PULSE_DCIR 10.3 %
- ⭐ FLOATING 30 group 활성화 (`v_chg` fix 효과)
- ⚠️ UNKNOWN 1.7 % (142 group, dedup 14 종) — 모두 `복합floating` 의 `N=14`
  mid-range 패턴 (Phase 0-5-α 후속 검증 필요)

### proto 코드 영향

**없음.** 본 batch script 는 self-contained 으로, `DataTool_optRCD_proto_.py` 의
`_parse_pne_sch` (L7594) / `_classify_loop_group` (L7975) 에는 변경 없음.
proto 본체에 PR 적용은 Phase c (코드 fix) 단계에서 별도 진행.

## 재현 방법

```bash
cd C:\Users\Ryu\battery\python\BDT_dev\.claude\worktrees\adoring-hopper-e1c07f
python tools/sch_phase0_5_classify_all.py
```

## 추가 작업 (260505 동일 일자)

### Phase 0-5-α — ref_step_number binary offset 식별

`260504_audit_phase0_5_classifier_input_spec.md` §3.3 의 미식별 5 field 후보 중
**`ref_step_number = +501 (uint8)`** 식별 완료 (368 .sch 전수 1,169 step 검증).

신규 도구 + 노트:
- `tools/sch_phase0_5_alpha_dump.py` — DCIR sample step 구조 dump
- `tools/sch_phase0_5_alpha_binary_search.py` — DCIR sample binary search
- `tools/sch_phase0_5_alpha_validate.py` — 368 .sch 전수 cross-validate
- `tools/sch_phase0_5_alpha_other_fields.py` — kind/basis/jump_target enum search
- `wiki/10_cycle_data/260505_phase0_5_alpha_ref_step_field_identified.md` — 정식 노트

핵심 발견:
- `+500 uint32 = (ref_step_number << 8) | type_marker_low_byte`
- `+501 byte = ref_step_number` (uint8, 본 데이터셋 6~181 범위)
- `+500 byte 0` = type marker (모든 sample 에서 0 — default Char./AH 인코딩)
- Phase 0-5 spec 의 `2048 = 8<<8` (ref_step=8), `18432 = 72<<8` (ref_step=72)
  로 hysteresis 분류 룰의 정체 확인
- 나머지 4 field (kind/basis/jump_target/delta_vp) 는 본 데이터셋에 default 케이스만
  등장 → 식별 보류 (vendor spec 또는 non-default sample 필요)

## 다음 단계

1. **Phase c-α**: proto L8053 의 `v_chg` 키 fix → 1줄 수정
2. **Phase c-β**: parser 9 신규 field 추가 → `_parse_pne_sch` 보강
3. **Phase c-γ**: parser `end_condition` 에 `ref_step_number` 추가 (Phase 0-5-α 발견)
4. **Phase 0-5-α**: ACCEL `N=14` mid-range gap fix → UNKNOWN 142 → 0 (target)
5. **분류기 v3**: ref_step_number 기반 HYSTERESIS / RSS_DCIR / SOC_DCIR /
   PULSE_DCIR disambiguate 룰 일반화
6. **Phase b**: 22 카테고리 spec audit — sub_tag 변형 (예: `ACCEL_Si_Hybrid`,
   `HYSTERESIS_0.5C_60min`) 정식화

## 추가 작업 (260505 동일 일자) — 분류 로직 설명서

박사급 peer 검토 가능 수준의 reference 문서:
- `wiki/10_cycle_data/260505_phase0_5_classifier_logic.md` (788 줄)

내용:
1. 분류 단위 (사이클 그룹) 정의 + 입력 5 base + 1
2. CC vs CCCV V cutoff 분리 (사용자 통찰)
3. End Condition 인코딩 — Multi-condition OR + ref-step jump (Phase 0-5-α)
4. 22 카테고리 도메인 의미 + .sch 패턴 + 판별 룰
5. 분류 우선순위 (decision order) + 흐름도
6. v2 vs v3 비교
7. UNKNOWN 케이스 분석 + Phase 0-5-α 후속 fix 후보
8. Sub-tag 활용
9. Limitations & Caveats (mincapacity, outer-goto, Toyo, Phase 0-5-α 보류 4 field)

## Related

- [[wiki/10_cycle_data/260505_phase0_5_187_cycle_definitions]] — 본 결과 정식 노트
- [[wiki/10_cycle_data/260505_phase0_5_alpha_ref_step_field_identified]] — Phase 0-5-α
- [[wiki/10_cycle_data/260505_phase0_5_classifier_logic]] — 분류 로직 설명서
- [[wiki/10_cycle_data/260504_audit_phase0_5_classifier_input_spec]] — 분류기 v2 spec
- [[wiki/10_cycle_data/260504_plan_22cat_audit_and_eval_overlay]] — 5단계 audit plan
