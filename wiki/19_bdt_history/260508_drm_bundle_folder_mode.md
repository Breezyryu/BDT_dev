# 260508 DRM 번들 출력 — 폴더 모드 + Excel 분리 .txt

## 배경

`tools/drm_reload_test.py` 의 사내 추출 결과가 `<stem>_bundle.txt` 단일 파일이라
사람이 검토할 때 모든 시트·차트가 한 파일에 섞여 있어 가독성이 낮음.

사용자 요구:

- 문서 변환 시 **폴더를 생성**하고 그 안에 텍스트 파일 출력
- 엑셀 **수식·차트 데이터** 가 모두 기록되는지 확인
- 외부 환경에서 **차트 데이터** 가 정확히 동일하게 복원되어야 (색상은 무관)

## 결론 — 사용자 질문에 대한 답

| 항목 | 보존 여부 | 근거 |
| ---- | -------- | ---- |
| 모든 셀 수식 | ✅ 셀 주소(A1)+수식 그대로 | `===FORMULAS===` / `formulas_<sheet>.txt` |
| 차트 시리즈 X/Y | ✅ 원본 값 그대로 | `===CHARTS===` / `chart_<idx>_<name>.txt` |
| 차트 축 제목·차트 제목 | ✅ | 동일 |
| 차트 색상·스타일 | ❌ 손실 | openpyxl LineChart 기본값 사용 |
| 시트별 raw 값 | ✅ TSV | `===VALUES===` / `values_<sheet>.txt` |

## 변경 내역

### 신규 함수

- **`export_excel_bundle_dir(src, out_dir)`**
  - Excel 한 번 열어 다음 5종 산출물 동시 출력:
    - `_bundle.txt` — 통합 (기존 형식, `load_bundle` / `--to-xlsx` / `--render` 호환)
    - `_meta.txt` — 사람용 요약 (파일 목록·통계·복원 명령)
    - `values_<sheet>.txt` — 시트별 TSV
    - `formulas_<sheet>.txt` — 시트별 셀↔수식 매핑
    - `chart_<idx:02d>_<name>.txt` — 차트별 시리즈 X/Y (전역 일련번호)
  - 모든 .txt 첫 줄 공란 (Fasoo proto_:22176 회피).

- **`_bundle_path_resolve(path)`**
  - 입력이 폴더면 폴더 안 `_bundle.txt` 로 해석.
  - `load_bundle` / 모든 `render_*` 함수가 이를 거쳐 폴더·파일 양방 입력 허용.

### 수정 함수

| 함수 | 변경 |
| ---- | ---- |
| `load_bundle` | 첫 줄에 `path = _bundle_path_resolve(path)` 추가 — 폴더 입력 자동 분기 |
| `_cmd_extract` | 출력 경로를 `<stem>_bundle/` 폴더로 (전 포맷). Excel 만 분리 .txt 추가 |
| `_cmd_render` | 폴더 입력 허용 (`is_file() or is_dir()`). 기본 출력은 폴더면 폴더 내 `charts/` |
| `_cmd_restore` | 폴더 입력 허용. 기본 출력 stem 은 `<stem>_restored.<ext>` |
| `_process_one` | Excel→`export_excel_bundle_dir`. PPT/PDF/Word→폴더 안 `_bundle.txt` |

### 그대로 유지

- `export_excel_bundle` (단일 파일 출력) — 기존 호출자 호환
- `export_pptx_bundle` / `export_pdf_bundle` / `export_word_bundle` — 단일 .txt 출력 그대로 (폴더 안에 두는 식)
- `_collect_batch_inputs` — `*_bundle.txt` 만 .txt 로 인정하므로 분리 .txt(`values_*.txt` 등)는 자동 제외

## 출력 구조 — 한눈에

### Excel (`.xlsx/.xls/.xlsm`)

```
<stem>_bundle/
    _bundle.txt                  ← 통합 (호환)
    _meta.txt                    ← 사람용 요약
    values_Sheet1.txt            ← 시트별 TSV
    values_Sheet2.txt
    formulas_Sheet1.txt          ← 셀↔수식
    chart_01_Sheet1_Chart1.txt   ← 차트별 X/Y
    chart_02_Sheet1_Chart2.txt
    ...
```

### PPT / PDF / Word

```
<stem>_bundle/
    _bundle.txt                  ← 단일 (분리 없음)
```

## 사용법

### 사내 추출

```bash
# 단일
python drm_reload_test.py <입력파일>
#   → <입력파일경로>_bundle/ 폴더 생성

# 배치 (파일/디렉터리 혼합)
python drm_reload_test.py --batch [--out <dir>] <path>...
```

### 외부 복원·렌더링

```bash
# 차트 PNG (폴더 또는 _bundle.txt 둘 다 OK)
python drm_reload_test.py --render <stem>_bundle/ <out_dir>
python drm_reload_test.py --render <stem>_bundle/_bundle.txt <out_dir>

# xlsx 복원 (수식·차트 데이터 보존, 색상 손실)
python drm_reload_test.py --to-xlsx <stem>_bundle/ <out.xlsx>
```

## 호환성

- 신규 출력 폴더의 `_bundle.txt` 는 **기존 단일 파일과 동일한 형식**
  → 기존 외부 도구·스크립트 그대로 작동
- 옛 `<stem>_bundle.txt` 단일 파일도 `load_bundle` / `--render` / `--to-xlsx` 모두 그대로 받음
- `_collect_batch_inputs` 가 `*_bundle.txt` 만 .txt 로 인정 → 분리 파일이 차트 렌더링 노이즈로 잡히지 않음

## 검증

- `python -m py_compile` — 통과
- `from drm_reload_test import export_excel_bundle_dir, load_bundle, _bundle_path_resolve, _cmd_extract` — 통과
- 사내 실측 (xlwings·Fasoo 환경 필요) 은 별도

## 한계

- **차트 색상·선 스타일·마커** 는 openpyxl LineChart 기본값으로 그려짐 (사용자 요구 명시 — 데이터만 정확하면 OK)
- **차트 종류** 는 모두 LineChart 로 통일 (원본이 막대·산점도여도 선형). 추후 차트 종류 메타 추가 검토 가능
- **PPT/PDF/Word** 는 폴더만 만들고 안에 `_bundle.txt` 단일. 분리 .txt 미지원 (사용자 요구가 엑셀 중심)

## 후속 — 필요 시

- PPT 슬라이드별 .txt, PDF 페이지별 .txt, Word 단락+표별 .txt 분리
- 차트 종류 메타(Line/Bar/Scatter) 보존 + `--to-xlsx` 에서 분기 생성
- `_meta.txt` 에 시트별 행/열 차원·차트별 시리즈 수 요약 추가
