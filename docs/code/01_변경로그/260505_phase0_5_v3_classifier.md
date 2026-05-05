# 260505 — Phase 0-5 분류기 v3 — 모든 발견 통합 batch script

## 배경

Phase 0-5 spec ([[wiki/10_cycle_data/260504_audit_phase0_5_classifier_input_spec]])
의 분류기 v2 + Phase 0-5-α (`ref_step_number = +501` 식별) +
mode_flag 도메인 분석 결과를 모두 통합한 v3 batch 분류기 구축.

## 변경 사항

### 신규 파일

- `tools/sch_phase0_5_v3_classify.py` — v3 batch 분류기 (623 줄, self-contained)
- `tools/sch_phase0_5_v3_groups.csv` — 8,298 group × 22 col
- `tools/sch_phase0_5_v3_files.csv` — 368 file × 12 col
- `tools/sch_phase0_5_v3_summary.md` — 자동 생성 v3 요약
- `tools/sch_phase0_5_v2_v3_diff.py` — v2 vs v3 transition matrix 도구
- `tools/sch_phase0_5_v2_v3_diff.md` — v2 vs v3 diff 분석
- `wiki/10_cycle_data/260505_phase0_5_v3_implementation.md` — v3 구현 정식 노트

### v3 의 v2 대비 핵심 변경

#### Parser 보강 (Tier 1 — 분류 룰 직접 영향)

```python
# 신규 step_info 필드
'mode_flag':         struct.unpack_from('<I', blk, 84)[0]
'record_interval_s': struct.unpack_from('<f', blk, 336)[0]
'chamber_temp_c':    struct.unpack_from('<f', blk, 396)[0]

# end_condition 에 ref_step_number 추가 (Phase 0-5-α)
step_info['end_condition']['ref_step_number'] = (ec500 >> 8) & 0xFF
step_info['end_condition']['type_marker'] = ec500 & 0xFF
```

#### 분류기 룰 변경

| # | 룰 | 효과 |
|---|---|---|
| A | `v_chg` 키 fix | FLOATING 30 활성화 |
| B | CC vs CCCV V cutoff 분리 | multi-step charge 정확 식별 |
| C | schedule keyword prior (8 keyword) | ECT/RSS/Hysteresis prior |
| D | ref_step 일반화 hysteresis | +27 hysteresis group |
| E | RSS_DCIR multi-cluster sub_tag | RSS_DCIR +32 |
| F | ACCEL `N=14` mid_life | UNKNOWN 142 → 0 |
| G | DCHG_CCCV mode=0 → PULSE_DCIR sub_tag | DCIR pulse 식별 |
| H | ECT sub_tag (mode=0 + chamber + +336<5 OR desc_kw) | 79 group → ACCEL/FORMATION/GITT_PULSE 의 `ect` sub_tag |

### 핵심 결과

| | v2 | v3 | 변동 |
|---|---|---|---|
| **UNKNOWN** | **142** | **0** | **-142 ✅** |
| ACCEL | 929 | 1071 | +142 (UNKNOWN 흡수) |
| RSS_DCIR | 8 | 40 | +32 (multi_cluster) |
| HYSTERESIS_CHG | 198 | 217 | +19 (ref_step 일반화) |
| HYSTERESIS_DCHG | 230 | 198 | -32 (multi_cluster → RSS) |
| 기타 | — | — | minor |

총 **205 group 재분류** (v2 의 2.5%, 모두 도메인 의미 향상 방향).
**22 카테고리 유지** (ECT 는 sub_tag 으로 통합, 도메인 검증 후 결정).

### 사용자 도메인 검증 (260505)

> "ECT (신규)는 단순 rest가 긴 거 아닌가?"

→ ECT 분류 79 group의 실제 step pattern 검증 결과:
- "단순 1-step REST" 케이스 0/79 (0%)
- 실제 body: 4-step multi-step charge + 부분 DCHG + 60s REST × N=30
- = **ACCEL 의 정확한 시그니처** (chamber 온도 명시만 차이)

→ v3 수정: ECT 별도 카테고리 제거 → ACCEL/FORMATION/GITT_PULSE 의 `ect` sub_tag으로 통합.
도메인 의미상 ECT는 cycling 의 chamber-controlled 변형이므로 sub_tag이 정확.

### proto 코드 영향

**없음.** v3 는 self-contained batch script. proto `DataTool_optRCD_proto_.py` 본체에는
변경 없음. proto 적용은 Phase c 의 별도 PR 단계에서 진행 권장 (총 ~8.5 시간 추정).

## 재현

```bash
cd C:\Users\Ryu\battery\python\BDT_dev\.claude\worktrees\adoring-hopper-e1c07f
python tools/sch_phase0_5_v3_classify.py
python tools/sch_phase0_5_v2_v3_diff.py
```

## 다음 단계

1. **Phase c-α**: proto L8053 `v_chg` 키 fix (1줄)
2. **Phase c-β**: parser 신규 field 추가 (~1.5시간)
3. **Phase c-γ**: helper 함수 (CC vs CCCV cutoff, schedule keyword) (~1.5시간)
4. **Phase c-δ**: 분류 룰 v3 통합 (~5시간)
5. **Phase b**: 22 → 23 카테고리 spec 업데이트 (ECT 정식화)
6. **Phase d**: 정확도 측정 (confusion matrix vs 도메인 review)

## Related

- [[wiki/10_cycle_data/260505_phase0_5_v3_implementation]] — 본 결과 정식 노트
- [[wiki/10_cycle_data/260505_phase0_5_187_cycle_definitions]] — v2 결과
- [[wiki/10_cycle_data/260505_phase0_5_alpha_ref_step_field_identified]] — Phase 0-5-α
- [[wiki/10_cycle_data/260505_phase0_5_classifier_logic]] — 분류 로직 설명서
- [[wiki/10_cycle_data/260504_audit_phase0_5_classifier_input_spec]] — 분류기 v2 spec
