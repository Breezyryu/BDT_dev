# 260318 - 신뢰성 Cycle Estimation 직접 경로 입력 버그 수정

## 문제
- `path_approval_cycle_estimation_button()` 실행 시, `stepnum_2`(경로 입력 박스)에 직접 경로를 입력해도 **항상 파일 대화상자가 열리며** 직접 입력 경로가 무시됨

## 원인
- `pne_path_setting()` 호출 전에 `self.chk_cyclepath.setChecked(True)`로 체크박스를 강제 ON
- `pne_path_setting()` 내부에서 `chk_cyclepath`가 True이면 **첫 번째 분기**(파일 대화상자)로 진입
- `stepnum_2`에 텍스트가 있어도 **두 번째 분기**(elif)에 도달하지 못함

## 수정 내용
- **파일**: `DataTool_dev/DataTool_optRCD_proto_.py` (약 15536행)
- `stepnum_2`에 텍스트가 있으면 체크박스를 강제 True로 만들지 않고 `pne_path_setting()`이 직접 입력 경로를 처리하도록 분기 추가

### Before
```python
self.chk_cyclepath.setChecked(True)
pne_path = self.pne_path_setting()
self.chk_cyclepath.setChecked(False)
```

### After
```python
if self.stepnum_2.toPlainText().strip() == "":
    self.chk_cyclepath.setChecked(True)
    pne_path = self.pne_path_setting()
    self.chk_cyclepath.setChecked(False)
else:
    pne_path = self.pne_path_setting()
```
