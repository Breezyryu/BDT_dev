# doc_converter — 문서 → Markdown + 이미지 변환

**로컬 OSS 전용** — 외부 API 호출 없음. 사내 환경에서 기밀 문서(과제계획서/Approval Sheet/DFMEA/분해분석 등)를 안전하게 Markdown 으로 변환.

## 지원 포맷
| 입력 | 엔진 (순차 fallback) |
|------|---------------------|
| `.pdf` | marker-pdf (Surya OCR ko/en) → docling → pymupdf → markitdown |
| `.xlsx` | docling → pandas (custom_doc_props strip) → markitdown |
| `.pptx` / `.docx` | docling → markitdown |
| `.eml` / `.mht` | markitdown |

## 빠른 시작 (사내 PC)

```bat
# 1. 최초 1회 — 의존성 설치 + 모델 다운로드 (인터넷 필요, ~3GB)
setup.bat

# 2. 변환 실행 (오프라인 가능)
convert.bat "C:\path\to\source_folder"
# → 생성: C:\path\to\source_folder_md\<파일명>\<파일명>.md + images/
```

옵션:
- `convert.bat <src> <out>` : 출력 폴더 지정
- `convert.bat <src> --force` : 기존 MD 무시 재변환

## HuggingFace 접속 차단 환경 대응

사내망에서 `huggingface.co` 차단 시:
1. **사외 PC** 에서 `setup.bat` 실행 → `%USERPROFILE%\.cache\huggingface` 폴더 생성
2. 해당 폴더를 사내 PC 의 **동일 경로**로 복사
3. 사내 PC 에서 `setup.bat` 재실행 (pip install 만 수행, 모델은 캐시 재사용)
4. 이후 `convert.bat` 는 완전 오프라인 동작 (`HF_HUB_OFFLINE=1`)

## DRM 파일 처리
- **NASCA DRM PDF** (`<## NASCA DRM FILE -` 헤더): 자동 감지 → SKIP 리포트 기재. 사내 NASCA viewer 로 수동 처리 필요
- **Fasoo DRM xls/xlsx**: 사내 환경에서만 decrypt 가능. 사외 실행 시 COM 에러 발생

## 의존성
- Python 3.12+
- `requirements.txt` 참조 (docling, marker-pdf, markitdown, easyocr, pymupdf, pandas)
- 최초 다운로드 모델 ~3GB (Surya, docling-layout, TableFormer, EasyOCR ko/en)

## 리포트
변환 완료 후 `<output>/_conversion_report.md` 에 파일별 성공/실패 상세 기록.
