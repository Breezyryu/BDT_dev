# ECT용 데이터 저장 경로 복구 (proto)

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수: `ect_confirm_button()` — 약 24835~ 라인

## 문제

사용자 보고: "ECT path 사용 + ECT용 데이터 저장 체크를 활성화해도 proto 코드에서는 CSV 저장이 안 된다."

## 원인 분석

원본(`DataTool_260306.py:12262`)과 proto의 저장 경로 우선순위가 반대로 바뀌어 있었음.

| 항목 | 원본 | Proto (수정 전) |
|---|---|---|
| 저장 조건 | 무조건 | `ect_saveok.isChecked()` 필요 |
| 1순위 경로 | `D:\` | 스크립트/exe 디렉토리 |
| 폴백 | 없음 | `D:\` (1순위가 항상 존재해 사실상 미발동) |

결과적으로 proto는 CSV 파일을 `DataTool_dev_code/` 같은 스크립트 디렉토리에 저장했고, 사용자가 원본과 동일하게 `D:\` 루트를 확인했을 때 파일이 없어 "저장이 안 된다"고 인식함.

## 수정

우선순위를 원본 동작으로 복구: `D:\` 우선, 없을 때만 스크립트/exe 디렉토리로 폴백. 저장 직후 `print()`로 실제 저장 경로를 콘솔에 출력해 사용자가 위치를 즉시 확인할 수 있도록 함.

```python
if self.ect_saveok.isChecked():
    continue_df = ...
    _ect_csv_dir = "D:\\"
    if not os.path.isdir(_ect_csv_dir):
        _ect_csv_dir = (os.path.dirname(sys.executable)
                        if getattr(sys, 'frozen', False)
                        else os.path.dirname(os.path.abspath(__file__)))
    if os.path.isdir(_ect_csv_dir):
        _ect_csv_path = os.path.join(_ect_csv_dir, str(ect_save[i]) + ".csv")
        continue_df.to_csv(_ect_csv_path, ...)
        print(f'[ECT 저장] {_ect_csv_path}')
```

- `ect_saveok` 체크박스 가드는 유지 (사용자가 원치 않을 때 저장 안 함 — 개선된 동작 보존).
- `str(ect_save[i])` 로 타입 안전성 강화 (table 경로/파일 경로 양쪽 호환).

## 영향 범위

`ect_confirm_button()` 내부 1곳만 변경. `Chg`/`Dchg` 프로파일의 ECT 저장(`save_file_name + _%04d.csv` 패턴, 24320/24375 라인)은 원본과 동일하게 `save_file_name` 기반이므로 미수정.

## 검증 포인트

- [ ] ECT path 체크 + ECT용 데이터 저장 체크 후 Profile Confirm 실행 → `D:\<save이름>.csv` 생성 확인
- [ ] `D:\` 가 없는 머신에서 실행 → 스크립트 디렉토리에 저장, 콘솔 로그에서 경로 확인
- [ ] 테이블 모드(`name` 열)와 파일 모드(`save` 열) 모두 동일하게 동작
