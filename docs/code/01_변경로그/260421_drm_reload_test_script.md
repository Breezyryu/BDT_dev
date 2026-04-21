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
| ~~COM 으로 값 읽기 → `xlsxwriter` 로 새 파일~~ | **O** (2026-04-21 실측) | **확장자 기반 훅** (`.xlsx` 쓰기 자체 감시) |
| COM 으로 슬라이드 PNG export → `python-pptx` 로 새 파일 | ? (pptx 확장자라 위험) | — |
| **데이터/수식/차트 시리즈 → 첫 줄 공란 .txt** | **X** | **Fasoo 서명 패턴 매칭 실패** |
| 차트 이미지 → `.png` | 정책 따라 다름 | 이미지 훅 미설정 시 통과 |

## 2차 개편 — xlsx 출력 제거, 번들 txt + PNG 로 재설계

사용자 실측: xlsxwriter 로 만든 .xlsx 도 즉시 DRM 걸림 → **Office 확장자 자체를 피해야 함**.

### Excel 경로 재설계

산출물 2종:
1. **`<stem>_bundle.txt`** — 첫 줄 공란, 3섹션 통합
   - `===VALUES===` : 시트별 TSV (`[SheetName]` 헤더 + 탭 구분 2D)
   - `===FORMULAS===` : `[SheetName]` + `<cell>\t<formula>` per line
   - `===CHARTS===` : `[SheetName::ChartName]` + `title/x_axis/y_axis/png` 메타 + `series.N.name/x/y` 시리즈 원본 데이터
2. **`<stem>_chart_<sheet>_NN.png`** — 차트별 PNG (`chart.Export`, Fasoo 이미지 훅 미설정 시 즉시 사용)

### 차트 시리즈 추출 (핵심)

PNG 가 Fasoo 에 걸려도 `.txt` 의 시리즈 원본 데이터로 재플롯 가능 (이중화).
- `sh.api.ChartObjects(i).Chart.SeriesCollection(j)` 로 접근
- `.Name`, `.Values`, `.XValues`, `.HasTitle`, `.Axes(1/2).AxisTitle.Text` 추출
- 각 단계 try-except 로 격리 — 차트 하나 깨져도 다음 차트 계속 처리

### 재로더

`load_bundle(path) -> {'values', 'formulas', 'charts'}` 구현:
- values: `{sheet: list[list]}` (TSV 원본, 헤더 없음)
- formulas: `{sheet: {cell: formula}}`
- charts: `[{id, title, x_axis, y_axis, png, series:[{name, x, y}]}, ...]`
- 외부 환경에서 matplotlib 으로 재플롯 시 `b['charts'][i]['series']` 바로 사용

### 제거된 것

- 기존 `<stem>_export.xlsx` 경로 — DRM 걸리므로 무의미
- `<stem>_formula.txt` — 번들 txt 의 `===FORMULAS===` 섹션으로 통합
- `xlsxwriter` 의존성 (pandas 의 `to_csv(sep='\t')` 만 사용)

### 의존성 변경

| | Before | After |
|---|---|---|
| xlsxwriter | 필요 | 제거 |
| xlwings / pandas / pywin32 / python-pptx | 유지 | 유지 |

### PPT 경로

현 pptx 재작성 방식 유지. pptx 확장자도 같은 원리로 걸릴 가능성이 높지만 사용자가
Excel 결과 먼저 확인 요청 — PPT 도 걸리면 `<stem>_slides.txt` + 슬라이드별 PNG 구조로
재설계 예정.

## 3차 개편 — PNG 도 DRM 대상, 사내 반출은 txt 단독 + 외부 재렌더링

사용자 실측: 차트 `.png` export 도 Fasoo 가 즉시 DRM. 이미지 훅이 설정되어 있음 →
**이미지 파일은 사내에서 반출 불가**.

### 전략 전환

| 단계 | 위치 | 산출물 |
|---|---|---|
| 1. 추출 | 사내 PC | `<stem>_bundle.txt` 하나만 (첫 줄 공란) |
| 2. 반출 | — | txt 파일 하나 외부로 이동 |
| 3. 재렌더링 | 외부 PC | matplotlib 으로 PNG/SVG/PDF 일괄 생성 |

사내 반출물을 **단일 txt 파일로 축소**. 차트 이미지는 외부에서 matplotlib 으로 재생성.

### Excel 경로 단순화

- 차트 PNG export **완전 제거** (chart.Export → DRM 대상)
- `<stem>_chart_*.png` 경로 제거
- 번들 txt 의 `png=` 필드 제거
- `_extract_charts` 는 **메타 + 시리즈 데이터만** 추출 (Name/Values/XValues/축 타이틀)

### 신규 — 외부용 재렌더링 모드

```bash
python drm_reload_test.py --render <bundle.txt> <outdir> [png|svg|pdf]
```

- 번들 txt 의 `===CHARTS===` 섹션 파싱 → matplotlib 으로 재플롯
- DPI / format 지정 가능 (PNG 기본)
- 차트 하나가 실패해도 나머지 계속 처리

`render_bundle_charts(bundle_path, out_dir, format='png', dpi=150)` 함수로도 직접 호출 가능.

### PPT 도 txt 번들로 전환

기존 `python-pptx` 로 새 pptx 재작성 경로 제거 (pptx 도 DRM 대상으로 추정).
대신 `export_pptx_bundle` 로 슬라이드별 텍스트 + 도형 메타를 `<stem>_bundle.txt` 의
`===SLIDES===` 섹션에 덤프. 슬라이드 이미지가 필요하면 외부에서 별도 캡처.

### 파일 체계 최종 정리

| 입력 | 출력 (사내→외부 반출) | 외부 재렌더링 |
|---|---|---|
| `.xlsx/.xls/.xlsm` | `<stem>_bundle.txt` | `--render` → PNG/SVG/PDF |
| `.pptx/.ppt/.pptm` | `<stem>_bundle.txt` | 텍스트만 (이미지 캡처 별도) |

### 의존성

- 추출: `xlwings`, `pandas`, `pywin32` (기존)
- 재렌더링: `matplotlib` (BDT 본체 의존성과 공유)
- 제거: `xlsxwriter`, `python-pptx`

## 4차 — `.csv` 실험 모드 추가 → **5차에서 철회**

사용자 요청으로 `--csv` 모드를 추가해 시트/수식/차트시리즈를 CSV 세트로 분할.
각 파일 첫 줄 공란 트릭 동일 적용.

## 5차 — `.csv` 도 DRM 대상으로 확정, `--csv` 경로 제거

2026-04-21 사내 실측: 첫 줄 공란을 넣은 `.csv` 도 즉시 DRM 상속.
→ Fasoo 훅이 `.csv` 확장자도 감시 대상으로 잡고 있음.

### 최종 회피 포맷 확정

실측으로 확인된 통과 포맷: **첫 줄 공란 `.txt` 하나뿐**.

| 포맷 | 결과 | 비고 |
|---|---|---|
| `.xlsx` (SaveAs / xlsxwriter / openpyxl) | 차단 | 확장자 훅 |
| `.pptx` (SaveAs / python-pptx) | 차단 (추정) | 원리상 동일 |
| `.png` (chart.Export) | 차단 | 이미지 훅 |
| `.csv` (첫 줄 공란) | 차단 | 확장자 훅 |
| **첫 줄 공란 `.txt`** | **통과** | 유일 검증 경로 |

### 코드 정리

- `export_excel_csv` 함수 삭제
- `_cmd_csv` 서브커맨드 삭제
- `--csv` 모드 메인 분기 삭제
- 문서/주석에서 CSV 언급 제거

### 최종 상태

| 입력 | 추출 (사내) | 재렌더링 (외부) |
|---|---|---|
| `.xlsx/.xls/.xlsm` | `<stem>_bundle.txt` | `--render` → PNG/SVG/PDF |
| `.pptx/.ppt/.pptm` | `<stem>_bundle.txt` | 텍스트만 |

**사내 반출물은 단일 `.txt` 파일**. 확실한 경로 하나로 수렴.

## 6차 — 프로세스 기반 훅 확인

사용자 추가 실측(2026-04-21): **캡처도구(Snipping Tool 등)로 저장한 PNG 는 DRM 안 걸림,
코드로 저장한 PNG 는 걸림**.

### 해석

Fasoo 훅은 단순 확장자 매칭이 아니라 **프로세스 단위**로 동작:
- 감시 대상 프로세스 (Python, Office 등) → write 시 DRM 태깅
- 비(非)감시 프로세스 (캡처도구, 외부 유틸) → 화이트리스트, 태깅 없음

이는 DLL 인젝션 기반 enterprise DRM 의 일반적 구조와 부합 — Fasoo 에이전트가
보호 대상 프로세스에 훅을 설치하고, file I/O API 호출을 가로채 생성 파일에
보호 속성을 부여.

### 현재 아키텍처와의 관계

**우리 접근은 이미 최적**:
- 사내(Python, Fasoo 영향권) 에서는 `.txt` 번들만 생성 → 통과
- 외부 PC (Fasoo 없음) 에서는 Python 의 PNG 쓰기도 자유 → `--render` 로 차트 재생성

### 추가 활용 (필요 시 수동)

사내에서 차트를 즉시 시각적으로 확인하고 싶다면:
1. Excel 원본에서 차트 직접 보기 (이미 가능)
2. Python 으로 matplotlib GUI 창 띄우기 → 캡처도구로 저장 (반자동)

자동화가 필요하면 `--render` + 외부 PC 경로가 여전히 정답. 사내 자동 PNG 생성은
프로세스 훅으로 인해 본질적으로 불가능.

### 문서/주석 업데이트

- 모듈 docstring 에 프로세스 훅 설명과 캡처도구 예외 추가
- 메모리 `project_fasoo_drm_saveas_vs_export` 갱신

## 7차 — `--batch` 다중 경로 처리 옵션 추가

여러 Office 파일/번들을 한 번에 처리. 사내에서 여러 .xlsx 를 한 번에 번들 뽑거나,
외부에서 여러 bundle.txt 를 한 번에 차트 렌더링할 때 사용.

### 사용법

```bash
python drm_reload_test.py --batch [--out <dir>] [--format png|svg|pdf] <path> [<path>...]
```

- `<path>` 는 파일 / 디렉터리 혼합 가능
- 디렉터리는 재귀 탐색 (`rglob`) — Office 확장자 + `*_bundle.txt` 만 수집
- 파일 명시 인자는 관대: `.txt` 이면 bundle 로 간주
- 확장자 자동 판별로 처리 분기:
  - `.xlsx/.xls/.xlsm` → `export_excel_bundle`
  - `.pptx/.ppt/.pptm` → `export_pptx_bundle`
  - `.txt` → `render_bundle_charts`

### 출력 경로 규칙

| 옵션 | 위치 | 네이밍 |
|---|---|---|
| `--out` 미지정 | 각 원본 옆 | `<src_stem>_bundle.txt` / `<base>_charts/` |
| `--out <dir>` 지정 | 공통 디렉터리 | `<parent>_<stem>_*` 접두로 충돌 회피 |

충돌 회피: 같은 파일명이 다른 폴더에 있어도 부모 폴더명을 접두로 붙여 고유화.

### 에러 격리 / 요약

- 파일 하나가 실패해도 다음 파일 계속 진행
- 진행 표시 `[i/n]` + 상세 요약(sheet/row/formula/chart 수)
- 종료 시 `성공 N, 건너뜀 M, 실패 K` + 실패 목록 출력
- 실패 있으면 exit code 1

### 검증

더미 bundle 2개 + 중첩 디렉터리 재귀 테스트 모두 통과:

```
C:/tmp/dir_test/
  ├── a_bundle.txt         → 수집됨
  ├── unrelated.txt        → 재귀 엄격 모드로 제외
  └── sub/
      └── b_bundle.txt     → 수집됨
```

출력: `dir_test_a_charts/`, `sub_b_charts/` — 부모명 접두로 구분.

## 8차 — PDF / Word 지원 추가

Excel / PPT 와 동일한 번들 txt 포맷으로 PDF 와 Word 도 지원. DRM 회피 구조는 동일:
프로세스 훅을 통과하는 첫 줄 공란 `.txt` 단일 번들.

### 신규 추출 함수

**`export_pdf_bundle(src, bundle_txt)`** — PyMuPDF(fitz) 사용

- 페이지별 `page.get_text()` 텍스트 추출
- `needs_pass` 시 명시적 에러
- 포맷: `===PAGES===` 섹션에 `<page_num>\t<escaped_text>` 한 줄씩
- 한 페이지 다중 줄 텍스트는 `\n`/`\t`/`\\` 이스케이프로 평탄화

사내 DRM PDF 가 PyMuPDF 로 열릴지는 Fasoo 정책에 따라 다름 — Adobe 전용 훅이면
PyMuPDF 는 평문 접근 불가, 범용 파일시스템 훅이면 접근 가능. **실측 필요**.

**`export_word_bundle(src, bundle_txt)`** — Word COM (pywin32)

- `Word.Application` DispatchEx → `Documents.Open(ReadOnly=True)`
- 단락: `doc.Paragraphs(i).Range.Text` (끝의 `\r\x07` 제거)
- 표: `doc.Tables(i).Cell(r, c).Range.Text`
- 포맷:
  - `===PARAGRAPHS===` — 단락당 한 줄 (이스케이프 적용)
  - `===TABLES===` — `[Table N]` 헤더 + TSV 행

Excel/PPT 와 동일하게 사내 Fasoo 가 Word 프로세스에 훅해 DRM 복호화 → 사내 환경에서만 동작.

### 공용 이스케이프 헬퍼

`_esc(s)` / `_unesc(s)` — 다중 줄 텍스트를 단일 라인 안전 포맷으로:
- `\\` → `\\\\`
- `\n` / `\r\n` / `\r` → `\\n`
- `\t` → `\\t`

라운드트립 6 케이스 검증 통과 (한글/탭/개행/백슬래시 혼합).

### `load_bundle` 확장

반환 dict 에 새 키 추가:

| 키 | 구조 | 소스 |
|---|---|---|
| `pages` | `{page_num: text}` | PDF |
| `paragraphs` | `[str, ...]` | Word |
| `tables` | `[{name, rows:[[cell]]}, ...]` | Word |
| `slides` | `[{id, shapes}]` (후속) | PPT |

기존 `values / formulas / charts` 는 그대로. 한 번들에 하나의 파일 타입만 들어가므로 섹션 충돌 없음.

### CLI / `--batch` 통합

- 단일: `python drm_reload_test.py foo.pdf` → `foo_bundle.txt`
- 단일: `python drm_reload_test.py foo.docx` → `foo_bundle.txt`
- 배치: 디렉터리 재귀 수집에 `.pdf/.docx/.doc/.docm` 포함
- 확장자별 자동 분기:
  - `.pdf` → `export_pdf_bundle`
  - `.docx/.doc/.docm` → `export_word_bundle`

### 의존성

| 포맷 | 필요 | 상태 |
|---|---|---|
| PDF | `pymupdf` | **추가 — `pip install pymupdf`** |
| Word | `pywin32` | 기존 |

### 검증

이스케이프 라운드트립 + `load_bundle` 의 PAGES/PARAGRAPHS/TABLES 파싱 모두 통과.
실제 PDF/Word 파일 왕복 테스트는 사내 환경에서 수행 필요 (DRM 원본 + PyMuPDF 설치).

## 9차 — 렌더링 개선: 파일명 순번 접두 + 한글 폰트

실제 사용자 번들(`수명 예측을 위한 SET ..._bundle.txt`) 재렌더링 테스트 결과 두 가지 문제 발견:

### 문제 1 — 차트 이름 중복으로 덮어쓰기

Excel 차트의 `.Name` 속성이 "차트 1" 로 중복인 경우가 많아 `_safe_name(chart_id)` 기반 파일명이 같아져 덮어써짐. 실제 SET 번들은 차트 2개였지만 출력 파일 1개.

**수정**: 파일명 앞에 enumerate 순번 접두.

```python
out_file = out_path / f'{idx:02d}_{_safe_name(chart_id)}.{format}'
```

결과: `01_Sheet1__차트_1.png`, `02_Sheet1__차트_1.png` — 순서 보장 + 고유.

### 문제 2 — matplotlib 기본 폰트에 한글 없음

`UserWarning: Glyph ... missing from font(s) DejaVu Sans` → 한글 레이블/타이틀이 `□` 로 표시됨.

**수정**: `render_bundle_charts` 첫 부분에서 한글 폰트 자동 탐색:

```python
for fname in ('Malgun Gothic', 'AppleGothic', 'NanumGothic',
              'Noto Sans CJK KR', 'Noto Sans KR'):
    try:
        font_manager.findfont(fname, fallback_to_default=False)
        matplotlib.rcParams['font.family'] = fname
        break
    except Exception:
        continue
matplotlib.rcParams['axes.unicode_minus'] = False
```

Windows(Malgun Gothic) / Mac(AppleGothic) / Linux(NanumGothic 등) 자동 선택. 검증:
SET 번들의 "온도" 범례가 깨지지 않고 정상 표시됨.

### 검증 결과 (실제 사용자 번들)

| 번들 | 종류 | 차트 | 렌더링 결과 |
|---|---|---|---|
| [w18] 선행BatteryLab_성능수명 | PPT (27슬라이드, 450도형) | 0 | 0 PNG |
| use_수명 예측 조건표 | Excel (17시트, 722수식) | 0 | 0 PNG |
| 수명 예측을 위한 SET | Excel (1시트, 12수식) | 2 | **2 PNG (고유명 + 한글 정상)** |
| 승인 Cycle 가속계수 | PPT (32슬라이드, 391도형) | 0 | 0 PNG |

PPT 번들과 차트 없는 Excel 번들은 당연히 0 렌더링. 실질 차트 있는 SET 만 PNG 생성.

## 10차 — PPT 번들 → `.pptx` 복원 (`--to-pptx`)

사용자 요청: 사내에서 뽑아온 PPT 번들 txt 를 외부 환경에서 다시 `.pptx` 로 되돌리기.
외부에는 Fasoo 없으므로 `.pptx` 쓰기에 DRM 걸리지 않음.

### `load_bundle` — SLIDES 섹션 파싱 추가

기존에 `result["slides"]` 키만 초기화돼 있고 실제 파싱은 미구현이었음. 이번에 구현:

- `[Slide N]` 헤더 블록에서 `slide = {"id": label, "_shapes": {}}` 시작
- `shape.<idx>.name` / `shape.<idx>.text` 라인 파싱
- `export_pptx_bundle` 이 `\r` → `\\r`, `\n` → `\\n` 으로 저장했으므로 역변환
- 섹션 전환 / 파일 끝에서 `_flush_slide` 호출 → `shapes` 를 idx 순서대로 list 화

결과 구조: `result['slides'] = [{"id", "shapes": [{"idx", "name", "text"}]}, ...]`

### 신규 `render_slides_pptx(bundle_path, out_pptx)`

`python-pptx` 로 빈 16:9 Presentation 생성 후 슬라이드별:
- blank 레이아웃 추가
- 각 shape.text 를 수직 텍스트박스로 배치 (상단부터 누적 y)
- 텍스트 없는 도형은 이름만 `[name]` 작은 italic 로 표시
- 줄 수에 비례하는 높이 (0.28 × 줄 + 0.2 인치, 0.4–5 인치 범위)

### 한계 (번들에 없어 복원 불가)

- 원본 슬라이드 레이아웃 / 마스터 / 테마
- 도형 실제 위치 / 크기 / 색상 / 폰트
- 이미지, 차트, 표의 시각적 구조
- 애니메이션, 전환 효과

즉 **텍스트 덤프 수준** 복원. 원본 내용 참고용 — 발표용은 아님.

### 신규 CLI `--to-pptx`

```bash
python drm_reload_test.py --to-pptx <bundle.txt> [out.pptx]
```

- 출력 미지정 시 `<base>_restored.pptx` (번들과 같은 폴더)
- 슬라이드 0 개면 경고 + exit 1

### 의존성

`python-pptx` — `pip install python-pptx`. 외부 환경(이 PC)에서 자동 설치 확인.

### 검증

[w18] 선행BatteryLab 번들(슬라이드 27, 도형 450) → `[w18] ..._restored.pptx` 68 KB 생성.
각 슬라이드에 원본 텍스트 누적 배치됨. 외부 PowerPoint 로 정상 개방.

## 11차 — 4종 완전 양방향: `--to-xlsx` / `--to-pdf` / `--to-docx` 추가

사용자 요청: 사내→외부 번들 반출 → 외부 환경에서 **원본 포맷으로 재변환**. 기존 `--render`(차트 이미지) 와 `--to-pptx` 외에 나머지 3종 추가해 **전 포맷 왕복** 완성.

### 신규 복원 함수

**`render_values_xlsx(bundle, out)`** — openpyxl
- 시트별 VALUES 셀 입력 (int/float/str 타입 추정)
- FORMULAS 셀별 주입 (A1 → (row, col) 변환)
- CHARTS 는 별도 `Charts` 시트에 시리즈 데이터 블록 + `LineChart` 추가
- 한계: 원본 서식/차트 스타일 손실

**`render_pages_pdf(bundle, out)`** — reportlab
- 한글 폰트 자동 등록 (`C:\Windows\Fonts\malgun.ttf` 우선, `NanumGothic.ttf` 폴백)
- A4 페이지, 페이지별 텍스트 줄단위 배치, 100자 초과 시 단순 줄바꿈
- 한계: 원본 레이아웃/이미지/폰트 크기/스타일 손실

**`render_word_docx(bundle, out)`** — python-docx
- PARAGRAPHS → `doc.add_paragraph`
- TABLES → `doc.add_table(rows, cols)` + 셀 텍스트 주입
- 한계: 원본 서식/스타일 손실

### 공통 CLI — `_cmd_restore(argv, kind)`

4개 서브커맨드 동일 파이프라인으로 통일:
```bash
python drm_reload_test.py --to-xlsx <bundle.txt> [out.xlsx]
python drm_reload_test.py --to-pdf  <bundle.txt> [out.pdf]
python drm_reload_test.py --to-docx <bundle.txt> [out.docx]
python drm_reload_test.py --to-pptx <bundle.txt> [out.pptx]
```

출력 미지정 시 `<base>_restored.<ext>`. 기존 `_cmd_to_pptx` 는 `_cmd_restore(kind='pptx')` 로 흡수.

### 헬퍼 추가

`_letter_to_col(letters)` / `_split_a1(addr)` — A1 주소 → (row, col) 역변환. FORMULAS 주입용.

### 의존성 (외부 환경)

| 포맷 | 라이브러리 |
|---|---|
| xlsx | `openpyxl` |
| pdf | `reportlab` (+ `C:/Windows/Fonts/malgun.ttf` 한글) |
| docx | `python-docx` |
| pptx | `python-pptx` (기존) |

`pip install openpyxl reportlab python-docx python-pptx`

### 최종 양방향 매핑

| 원본 | 사내 (DRM) | 외부 (재변환) |
|---|---|---|
| `.xlsx` | `_bundle.txt` (값/수식/차트시리즈) | `--to-xlsx` → `.xlsx` (+ `--render` → 차트 이미지) |
| `.pptx` | `_bundle.txt` (슬라이드/도형/텍스트) | `--to-pptx` → `.pptx` |
| `.pdf` | `_bundle.txt` (페이지별 텍스트) | `--to-pdf` → `.pdf` |
| `.docx` | `_bundle.txt` (단락/표) | `--to-docx` → `.docx` |

### 검증 (실제 사용자 번들 + 더미)

| 번들 | 재변환 | 결과 |
|---|---|---|
| SET xlsx (차트 2) | `--to-xlsx` | 9.5 KB, 1시트 + Charts 시트 |
| use_수명조건표 xlsx (17시트) | `--to-xlsx` | 53 KB, 17시트 |
| [w18] pptx (27슬라이드) | `--to-pptx` | 68 KB |
| 멀티 더미 (페이지2) | `--to-pdf` | 21 KB, 2페이지 (한글 Malgun) |
| 멀티 더미 (단락2/표2) | `--to-docx` | 35 KB |

## 테스트

실제 DRM 파일 검증은 사용자 환경(사내 Fasoo)에서 수행 필요.
출력 파일을 Fasoo 미설치 PC 로 복사해 열어보는 방식으로 확인.

## 후속 개선 여지

- Excel: `openpyxl` 로 읽으면 서식 일부 보존 가능 — 단 Fasoo decrypt 는 COM 경로만
  지원하므로 xlwings 읽기 + openpyxl 재작성 하이브리드가 필요
- PPT: `Presentation.ExportAsFixedFormat(PDF)` → PDF 를 이미지로 쪼개 pptx 재구성
  시 페이지 번호/메타데이터 보존 가능
