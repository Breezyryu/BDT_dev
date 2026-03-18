# 260318 - 신뢰성 Cycle 직접 경로 입력 버그 수정

## 문제
- `stepnum_2`(경로 입력 박스)에 `.xls` 파일 경로를 직접 입력해도 cycle 분석 결과가 나오지 않음

## 원인

### 1. `.xls` 확장자 미인식 (핵심 원인)
- `_build_group_from_lines()`, `_parse_cycle_input()` 에서 `.xlsx`만 `data_type='excel'`로 분류
- `.xls` 파일은 `else` 분기로 빠져 `data_type='folder'`로 잘못 분류
- 이후 `os.path.isdir()` 체크에서 파일이므로 False → **조용히 건너뜀 (침묵 실패)**

### 2. `path_approval_cycle_estimation_button()` 체크박스 강제 조작 (이전 수정)
- `pne_path_setting()` 호출 전에 `chk_cyclepath`를 강제 True로 설정하여 직접 입력 무시

## 수정 내용

### 수정 1: `.xls` 확장자 인식 추가
- **`_build_group_from_lines()`**: `ext == '.xlsx'` → `ext in ('.xlsx', '.xls')`
- **`_parse_cycle_input()`**: 동일하게 `.xls` 추가
- xlwings는 Excel COM을 통해 `.xls`도 정상 지원 (사내 Excel 설치 환경)

### 수정 2: 체크박스 강제 조작 제거 (이전 수정)
- `stepnum_2`에 텍스트가 있으면 체크박스를 강제 True로 만들지 않도록 분기 추가

### After
```python
if self.stepnum_2.toPlainText().strip() == "":
    self.chk_cyclepath.setChecked(True)
    pne_path = self.pne_path_setting()
    self.chk_cyclepath.setChecked(False)
else:
    pne_path = self.pne_path_setting()
```
