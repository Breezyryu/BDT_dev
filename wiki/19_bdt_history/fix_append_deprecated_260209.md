# `_append` → `pd.concat` 일괄 교체 (2026.02.09)

## 문제

- `DataFrame._append()`는 **pandas 2.0에서 삭제**됨
- Step 확인 시 사이클 범위를 넓히면 `AttributeError: 'DataFrame' object has no attribute '_append'` 발생
- 사이클 2~4는 `Condition >= 2`라 while 루프 미진입 → 정상 작동
- **사이클 5**는 `Condition < 2`로 while 루프 진입 → `_append` 호출 → 에러

## 수정

파일 전체 `._append()` → `pd.concat([])` 일괄 교체

| 구분 | 수량 |
|------|------|
| 활성 코드 교체 | 17개 |
| 주석 내 미수정 (실행 안됨) | 3개 |

## 영향 범위

- `toyo_step_Profile_batch` / `toyo_step_Profile_data` / `toyo_Profile_continue_data`
- `toyo_dchg_Profile_data`
- SET 프로파일 관련 (`ect_set_profile_button`, `ect_set_log_button` 등)
- EU 수명 예측 fitting (`eu_fitting_confirm_button`, `eu_constant_fitting_confirm_button`, `eu_indiv_constant_fitting_confirm_button`)

## 대상 파일

`BatteryDataTool_260206_edit copy/BatteryDataTool.py`
