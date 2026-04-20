# 260421 DRM reload 테스트 스크립트 추가

## 배경 / 목적

Fasoo DRM 이 걸린 `.xlsx` / `.pptx` 를 새 파일로 복제할 때, **어떤 저장 경로가 DRM 을
벗겨내는지** 확인하기 위한 유틸리티.

핵심 지식(사용자 교정):
- **Office `SaveAs`** 는 Fasoo 훅이 잡아 DRM 이 새 파일로 **상속됨 → 회피 불가**.
- **데이터만 메모리로 읽어와 새 파일을 처음부터 쓰는 방식** 은 SaveAs 훅을 거치지 않음 → **회피 가능**.
- proto_(`DataTool_optRCD_proto_.py`) 의 신뢰성 Excel 저장 로직이 이미 이 패턴:
  - 읽기: `xw.App(visible=False).books.open(path)` → `sh.used_range.options(pd.DataFrame).value`
    (line 20410, 20433-20435)
  - 쓰기: `pd.ExcelWriter(save_file, engine="xlsxwriter")` 로 **새 파일을 처음부터 작성**
    (line 20386, 20490)

## 변경 내역

### 신규 파일

**`tools/drm_reload_test.py`** — 단일 진입점 스크립트 (경로 인자 or SRC/DST 상수)

**Excel (`.xlsx/.xls/.xlsm`) 처리** — proto 패턴 그대로
1. `xlwings.App(visible=False)` 로 열기 (read_only=True)
2. 모든 시트에 대해 `sh.used_range.options(pd.DataFrame, index=False, header=False).value`
   로 DataFrame 추출
3. 원본 닫기
4. `pd.ExcelWriter(dst, engine="xlsxwriter")` 로 **새 파일을 처음부터 작성**,
   시트명 유지(31자 제한)
- 한계: 서식/수식/차트 손실. 수식은 계산된 값으로 변환됨.

**PowerPoint (`.pptx/.ppt/.pptm`) 처리** — 이미지 재작성 방식
1. `win32com.client.DispatchEx("PowerPoint.Application")` 로 열기 (ReadOnly=True)
2. 각 슬라이드를 `Slide.Export(path, "PNG", w, h)` 로 PNG 추출 (2배 해상도)
3. 원본 닫기
4. `python-pptx` 로 빈 Presentation 생성, 원본과 동일한 슬라이드 크기 설정,
   각 슬라이드에 blank 레이아웃 + 전체 화면 이미지 삽입
- 한계: 텍스트 편집성 손실 (이미지 기반). 시각적 내용은 보존.

### 변경된 기존 파일

없음.

## 추가 — 수식 txt 덤프 (첫 줄 공란 트릭)

사용자 요구: `xlsxwriter` 로 새 xlsx 를 쓸 때 **수식이 계산된 값으로 변환되어 손실**되는
한계를 보완. Fasoo 는 txt 파일의 **첫 바이트 시그니처** 로 DRM 여부를 판단하므로 첫 줄을
공란으로 두면 서명 패턴 매칭 실패 → 평문 취급 → 외부 환경 반출 가능.

proto_ 는 path txt 저장 시 이미 동일 트릭 사용 중:
`DataTool_optRCD_proto_.py:22176  f.write("\n")  # DRM 회피용 공란`

### Excel 처리 확장

Excel 파일 하나당 **두 개의 출력** 생성:
1. `<stem>_export.xlsx` — 값 (기존과 동일, xlsxwriter 재작성)
2. `<stem>_formula.txt` — 수식만 덤프 (**첫 줄 공란**)

같은 xlwings 세션 안에서 `sh.used_range.formula` 속성으로 2D 수식 배열을 추출해, `=` 로
시작하는 셀만 `<셀주소>\t<수식>` 형식으로 기록. 시트 경계는 `[시트명]` 헤더로 구분.

수식 txt 포맷:
```
<빈 줄>                       ← DRM 회피 핵심
# DRM-bypass formula dump
# Source: <원본 경로>
# Exported: <ISO datetime>
# Sheets: N, Formulas: M
# Format: [SheetName] header, then '<cell>\t<formula>' per line.

[Sheet1]
A1	=SUM(B1:B10)
C3	=VLOOKUP(A3, Sheet2!A:B, 2, FALSE)

[Sheet2]
...
```

### 재로드 헬퍼

`load_formula_txt(path) -> dict[str, dict[str, str]]` 추가. 사내에서 뽑아온 수식 txt 를
현재 환경에서 `{sheet: {cell: formula}}` 로 로드해 참조 데이터로 재사용.

## 의존성

- `xlwings` (proto_에 이미 사용 중 — 추가 없음)
- `pandas`, `xlsxwriter` (proto_에 이미 사용 중)
- `pywin32` (PowerPoint COM — 신규)
- `python-pptx` (신규, `pip install python-pptx`)

## Fasoo DRM 동작 정리 (이번 작업 기준)

| 저장 방식 | DRM 상속 | 메커니즘 |
|---|---|---|
| `Workbook.SaveAs` (COM 직접) | O | Fasoo SaveAs 훅 |
| `Presentation.SaveAs` (COM 직접) | O | Fasoo SaveAs 훅 |
| COM 으로 값 읽기 → `xlsxwriter` 로 새 파일 | X | 훅 경로 우회 |
| COM 으로 슬라이드 PNG export → `python-pptx` 로 새 파일 | X | 훅 경로 우회 |
| **수식 → 첫 줄 공란 .txt 로 직접 기록** | **X** | **Fasoo 서명 패턴 매칭 실패** |

## 테스트

실제 DRM 파일 검증은 사용자 환경(사내 Fasoo)에서 수행 필요.
출력 파일을 Fasoo 미설치 PC 로 복사해 열어보는 방식으로 확인.

## 후속 개선 여지

- Excel: `openpyxl` 로 읽으면 서식 일부 보존 가능 — 단 Fasoo decrypt 는 COM 경로만
  지원하므로 xlwings 읽기 + openpyxl 재작성 하이브리드가 필요
- PPT: `Presentation.ExportAsFixedFormat(PDF)` → PDF 를 이미지로 쪼개 pptx 재구성
  시 페이지 번호/메타데이터 보존 가능
