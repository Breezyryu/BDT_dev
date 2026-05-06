---
date: 2026-05-07
type: changelog
tags: [bdt, cycle, xlsxwriter, excel, bugfix]
---

# 사이클 분석 Excel 저장 — 시트명 금지 문자 자동 치환

## 증상

사이클 분석 Excel 저장 중 다음 예외 발생, 저장 실패:

```
File "xlsxwriter\workbook.py", line 909, in _check_sheetname
xlsxwriter.exceptions.InvalidWorksheetName:
  Invalid Excel character '[]:*?/\\' in the sheetname 'Rest End [V]'
```

## 원인

`_cycle_sheet_specs` / `_save_cycle_excel_data` 가 정의한 시트명에
Excel 시트명 금지 문자 `[ ]` 가 포함됨.

영향 시트명:
`Rest End [V]`, `Rest End Chg [V]`, `평균 전압 [V]`,
`SOC70_DCIR [mΩ]`, `SOC70_RSS [mΩ]`, `RSS [mΩ]`, `DCIR [mΩ]`,
`RSS_OCV [V]`, `RSS_CCV [V]`, `충전전압 [V]`, `방전전압 [V]`

`output_data()` 는 `sheetname[:30]` 으로 길이 제한만 처리하고
금지 문자(`[ ] : * ? / \`) 는 검사하지 않았음.

## 변경 사항 — `DataTool_dev_code/DataTool_optRCD_proto_.py`

### `_excel_sheet_name(name)` 헬퍼 추가 (모듈 수준)

```python
_EXCEL_SHEET_BAD = str.maketrans({
    '[': '(', ']': ')',
    ':': '-', '*': '', '?': '',
    '/': '_', '\\': '_',
})

def _excel_sheet_name(name: str) -> str:
    """xlsxwriter 시트명 제약(금지문자 + 31자) 통과시킨 안전 시트명을 반환."""
    return str(name).translate(_EXCEL_SHEET_BAD)[:31]
```

치환 규칙:
- `[` → `(`, `]` → `)` — 단위 표기 의미 보존 (`[V]` → `(V)`)
- `:` → `-` (시각 표기 보존)
- `*`, `?` → 제거
- `/`, `\` → `_`
- 31자 길이 제한 (xlsxwriter 한계)

### `output_data()` 에서 sanitize 적용

```python
def output_data(df, sheetname, ...):
    df.to_excel(writer, sheet_name=_excel_sheet_name(sheetname), ...)
```

→ specs 정의·UI 탭 라벨·`_DECIMALS` dict 키는 **원본 그대로** (`[V]`)
유지하고, **Excel 저장 시점에만** 안전 이름으로 변환.

## 영향 / 호환성

- **사용자 화면 (사이클 탭 inner-tab)**: `Rest End [V]` 그대로 표시
- **저장된 Excel 시트명**: `Rest End (V)` 로 변환되어 저장
- 기존 `_DECIMALS.get(sheet_name, 3)`, `sheets_per_channel[sheet_name]`
  등 dict 매칭 로직 영향 없음 (specs 키 = 원본 이름)
- 외부 매크로/스크립트가 시트명을 `Rest End [V]` 로 참조했다면
  `Rest End (V)` 로 갱신 필요 — 지금까지는 저장 자체가 실패했으므로
  실사용 영향 없음

## 검증

- 파이썬 구문 검증 통과 (`python -m ast`)
- sanitizer 단위 검증:
  - `Rest End [V]` → `Rest End (V)`
  - `Rest End Chg [V]` → `Rest End Chg (V)`
  - `SOC70_DCIR [mΩ]` → `SOC70_DCIR (mΩ)`
  - `foo:bar*?` → `foo-bar`
  - `a/b\c` → `a_b_c`

## 관련 코드 위치

- `_excel_sheet_name`: `DataTool_optRCD_proto_.py:5026`
- `output_data`: `DataTool_optRCD_proto_.py:5038`
- 시트명 정의: `_cycle_sheet_specs` `DataTool_optRCD_proto_.py:23006-23037`
- 시트 출력: `_save_cycle_excel_data` `DataTool_optRCD_proto_.py:23039+`
