---
date: 2026-04-30
type: changelog
component: hysteresis_soc_offset
tags: [hysteresis, soc_offset, clip, golden_excel, bugfix]
related:
  - "[[260429_hysteresis_unified_flow]]"
  - "[[260429_fix_hysteresis_soc_offset_anchor_shift_and_dqdv_keyerror]]"
  - "[[260420_hysteresis_major_threshold]]"
golden_ref: "raw/Voltage hysteresis test_Graph format_v1.3_bundle.txt"
---

# 260430 — 히스테리시스 SOC offset `[0, 1]` 클립 완화

## 결함

`_compute_tc_soc_offsets` ([DataTool_optRCD_proto_.py:863](../../DataTool_dev_code/DataTool_optRCD_proto_.py)) 의 anchor 누적이 매 TC 마다 ``[0.0, 1.0]`` 으로 강제 클립되어, 정격용량(mincapacity) 보다 실측 용량이 큰 셀에서 raw 정규화 SOC 잉여 (+0.05 ~ +0.10) 가 누적 손실됨.

## 증상

mini-loop sweep 패턴 시험 (Voltage hysteresis window test) 에서 sweep 이 진행될수록 좌측 시프트 누적. cy12 시점 약 −7~8% 시프트 → 곡선이 ``[0, 1]`` 안쪽에 응축. 엑셀 v1.3 골든 레퍼런스 (`Voltage hysteresis test_Graph format_v1.3.xlsx`) 의 ``[0, 1.1]`` 자연 펼침과 불일치.

## 정량 비교 (cy3 chg max=1.0749 케이스)

| 단계 | 엑셀 v1.3 anchor | BDT 기존 (클립 [0,1]) | BDT 수정 (클립 [-0.2, 1.2]) |
|---|---|---|---|
| cy3 충전 끝 | 1.0749 | 1.0 (← 0.0749 손실) | 1.0749 ✓ |
| cy3 방전 끝 = cy4 충전 시작 | 0.9679 | 0.893 (−0.075) | 0.9679 ✓ |
| cy4 충전 끝 | 1.0749 | 1.0 (−0.075) | 1.0749 ✓ |
| cy4 방전 끝 = cy5 충전 시작 | 0.8649 | 0.79 (−0.075) | 0.8649 ✓ |
| cy12 시점 누적 시프트 | 0 | −0.075 | 0 ✓ |

## 원인

```python
# 변경 전 (DataTool_optRCD_proto_.py:925-928)
eff_chg = max(0.0, min(chg, 1.0 - prev_SOC))
end_chg = prev_SOC + eff_chg
eff_dchg = max(0.0, min(dchg, end_chg))
prev_SOC = end_chg - eff_dchg
```

`(1.0 - prev_SOC)` 상한이 raw chg 의 정규화 잉여 (CV 누적 + 실측>nominal) 를 모두 잘라냄. 매 사이클마다 손실 누적.

## 수정

상한·하한 한도를 모듈 상수로 추출하고 ``[-0.2, 1.2]`` 로 완화. 실측이 정격보다 클 수 있다는 도메인 사실 (예: nominal=4960mAh, actual=5300mAh → +6.85% 정규화 SOC 잉여) 을 흡수하면서, SaveEndData 정의 오류로 인한 폭주 (cap*N 누적 등) 는 차단.

```python
# 변경 후 (DataTool_optRCD_proto_.py:863-871)
_HYST_SOC_HARD_MAX = 1.2
_HYST_SOC_HARD_MIN = -0.2

# 변경 후 (DataTool_optRCD_proto_.py:929-933)
eff_chg = max(0.0, min(chg, _HYST_SOC_HARD_MAX - prev_SOC))
end_chg = prev_SOC + eff_chg
eff_dchg = max(0.0, min(dchg, end_chg - _HYST_SOC_HARD_MIN))
prev_SOC = end_chg - eff_dchg
```

## 영향 범위

`_compute_tc_soc_offsets` 호출처 (모두 hysteresis 경로):
- `DataTool_optRCD_proto_.py:1025` — `_compute_tc_hysteresis_labels` 안 (라벨링용 TC 시작 SOC).
- `DataTool_optRCD_proto_.py:26481` — `_apply_hysteresis_soc_offsets` (그래프 SOC 보정).
- `test_code/hysteresis_path_validator.py:118`, `inspect_si_hysteresis.py:64` — 검증.

비-hysteresis 경로 (cycle/profile/DCIR) 는 이 함수를 호출하지 않으므로 영향 없음.

## 검증 (수기 추적)

cy3 chg=1.0749, dchg=0.107 (Si 10% Hysteresis 측정 케이스, [DataTool_optRCD_proto_.py:925](../../DataTool_dev_code/DataTool_optRCD_proto_.py))

| TC | chg | dchg | prev_SOC (수정 전) | prev_SOC (수정 후) | 엑셀 |
|---|---|---|---|---|---|
| cy3 시작 | — | — | 0.000 | 0.000 | 0.000 |
| cy3 끝 | 1.0749 | 0.107 | 0.893 | 0.9679 | 0.9679 |
| cy4 끝 | 0.107 | 0.21 | 0.790 | 0.8649 | 0.8649 |
| cy5 끝 | 0.21 | 0.31 | 0.690 | 0.7650 | 0.7650 |

수정 후 BDT anchor = 엑셀 v1.3 anchor (line 1381 anchor 행) 정확히 일치.

## 후속

- [ ] `Voltage hysteresis test_Graph format_v1.3.xlsx` 4960mAh Si 10% Hysteresis 데이터로 재실행하여 BDT 1번 plot (SOC vs V) 이 엑셀 두 번째 이미지와 SOC=0~1.1 영역까지 자연 펼침 일치 확인.
- [ ] `inspect_si_hysteresis.py` 검증기 baseline 갱신 (anchor 값 비교 케이스 추가).
- [ ] dQdV/dVdQ plot (1.0+ SOC 영역) 재확인.

## 미해결 (별도 이슈)

이번 패치는 클립 완화만 다룬다. 다음 항목은 후속 이슈로 미뤘다:
- BDT 와 엑셀의 cycle 분할 정책 (BDT 한 번에 vs 엑셀 [3~12]/[14~23] 분리).
- DOD 좌표 anchor 계산 (`_calc_soc(dod, connected)`) 과 엑셀 `[3~12_QVData_DOD]` 시트 골든 비교.

## 참조

- 골든 레퍼런스: [`raw/Voltage hysteresis test_Graph format_v1.3_bundle.txt`](../../raw/Voltage%20hysteresis%20test_Graph%20format_v1.3_bundle.txt)
- 엑셀 anchor 행: line 1381 `[3~12_QV]` 시트, line 2107 `[3~12_dVdQData_SOC]` 시트
- 엑셀 anchor 수식: line 3561-3578 (AR1=AP1+MAX(A:A) 누적 패턴)
- 이전 변경: [[260429_fix_hysteresis_soc_offset_anchor_shift_and_dqdv_keyerror]]
