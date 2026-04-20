# ECT path 체크 시 프로파일 분석을 항상 ECT 핸들러로 위임

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수: `unified_profile_confirm_button()` (L24153)

## 배경 / 문제

사용자 보고:
> "ECT path 사용 체크하고 프로필 분석해도 아래 데이터 범위 옵션에 맞춰서 plot된다."

ECT path 사용 체크박스를 켠 뒤 프로파일 분석을 실행해도, 데이터 범위 옵션(오버레이 / 스플릿 / 사이클-충전-방전 축 등)에 맞춰 일반 통합 프로파일 흐름이 동작했다. 사용자 기대는 **ECT 체크 시 무조건 ECT 전용 연속 시간축 플롯**.

## 원인

`unified_profile_confirm_button` 의 ECT 위임 분기가 **`overlap == "continuous"` 조건까지 함께 요구**하고 있었다.

```python
# Before (L24162-24163)
if options["overlap"] == "continuous" and self.chk_ectpath.isChecked():
    self.ect_confirm_button()
    return
```

- 사용자가 데이터 범위 옵션을 "오버레이" 등 `continuous` 가 아닌 값으로 두면 ECT 체크가 무시되고 일반 통합 흐름 진입
- UI 레벨에서는 `_update_ect_columns_state` (L22946) 가 stepnum 과 테이블 col 4-5 만 토글할 뿐, 데이터 범위 옵션 그룹은 활성 그대로 노출되어 사용자가 "옵션 적용된다"라고 오인할 여지도 병존

도메인적으로 ECT path 의 목적은 PyBaMM / ECM 모델 입력용 **연속 시간축 데이터** 생성(+ `ect_saveok` 체크 시 CSV 저장)이다. `ect_confirm_button` (L24788) 은 `pne_Profile_continue_data` 를 사용해 6개 고정 서브플롯(Vol/Crate/SOC × 충·방전)을 그리며, overlap / axis_mode / data_scope 옵션을 전혀 수용하지 않는다. 따라서 ECT 모드에서 다른 범위 옵션은 의미 없음.

## 수정

ECT 체크 시 `overlap` 값과 무관하게 항상 ECT 핸들러로 위임하도록 조건 축소.

```python
# After (L24162-24165)
# ECT 경로 체크 시 기존 Continue(ECT) 핸들러로 무조건 위임
# (데이터 범위 옵션은 ECT 모드에서 의미 없음 — 연속 시간축 전용)
if self.chk_ectpath.isChecked():
    self.ect_confirm_button()
    return
```

## 영향 범위

- `unified_profile_confirm_button()` 진입부 조건 1줄 변경
- `ect_confirm_button()` 내부 및 일반 통합 흐름 로직 미변경
- ECT 체크가 꺼진 경우 동작 불변
- ECT 체크 + `overlap != continuous` 조합에서만 동작 변경: **기존에는 일반 플롯, 수정 후에는 ECT 플롯**

## 동작 변화 요약

| chk_ectpath | overlap 옵션 | Before | After |
|---|---|---|---|
| OFF | any | 일반 통합 플롯 | 일반 통합 플롯 (동일) |
| ON | `continuous` (이어서) | ECT 플롯 | ECT 플롯 (동일) |
| **ON** | **`split` / `connected`** | **일반 통합 플롯** | **ECT 플롯 ← 변경** |

## 검증 포인트

- [ ] chk_ectpath 체크 + 데이터 범위 "오버레이" 선택 → 프로파일 분석 → 6개 서브플롯 ECT 레이아웃 출력 확인
- [ ] chk_ectpath 체크 + 데이터 범위 "이어서" → 기존과 동일한 ECT 플롯
- [ ] chk_ectpath 해제 상태에서 각 데이터 범위 옵션 정상 동작 확인 (회귀 없음)
- [ ] `ect_saveok` 체크 시 CSV 저장 동작 정상

## 후속 과제 (별건)

사용자 혼란 원천 차단을 위한 UI 레벨 개선은 이번 범위에서 제외:
- 데이터 범위 옵션 그룹을 ECT 체크 시 비활성화(disabled)하여 시각적으로도 "무시됨" 명시
- `_data_scope_groupbox` 타이틀에 "(ECT 모드 시 비활성)" 힌트 추가
- `_update_ect_columns_state` 에 옵션 그룹 토글 로직 추가

필요 시 별도 PR 로 진행.
