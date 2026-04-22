---
title: "DoXA API 어댑터 추가 + Web UI vs API 품질 검증 계획"
date: 2026-04-22
tags: [software_dev, doxa, samsung, document_parsing, comparison]
---

# 배경 / 목적

2026-04-22 대화에서 다음 순서로 작업이 진행됨:

1. 로컬 OSS 파이프라인 (marker-pdf + docling + markitdown) 으로 `raw/g5p_at/` 45/46 변환 완료
2. MinerU 2.5-Pro 도입 → 동일 3개 샘플에서 DoXA 와 근접 품질 확인
3. 사내 DoXA SDK (`doxa-sdk`) 받음 → API 기반 어댑터 작성
4. **핵심 제보**: 기존 비교에 사용된 `raw/CA01, raw/MP102, raw/MP104` 은 **DoXA 웹 UI** 로 변환된 결과물. 사내 사용자들로부터 "**API 변환은 Web 대비 품질이 떨어진다**"는 피드백이 있음 → 실제 격차 검증 필요

# 변경 내용

`tools/doc_converter/` 에 DoXA 어댑터 + 비교 도구 추가.

| 파일 | 역할 |
|------|------|
| `doxa_convert.py` | DoXA API 호출, 응답(ZIP/JSON/Text) 자동 전개, stem 디렉토리 구조 생성 |
| `doxa_convert.bat` | 사내 실행용 런처. `DOXA_TOKEN` 환경변수 체크 + `.venv` 활성화 |
| `doxa_smoke_test.py` | 파일 업로드 전 네트워크·토큰 사전 검증 (JWT 디코드 + 엔드포인트 ping) |
| `compare_outputs.py` | 두 디렉토리 산출물 자동 비교 (파일 수, MD 크기, 테이블/rowspan/colspan 카운트, 한글 글자 수, 텍스트 유사도) |
| `DOXA_README.md` | 사내 PC 셋업·사용·트러블슈팅 가이드 |

# 아키텍처 결정

- **토큰은 환경변수만** (`DOXA_TOKEN`, `DOXA_URL`, `IPAAS_TOKEN`) — 하드코딩/커밋 금지
- `DocumentRequestParam` 기본값: `standard` 포맷 + `korean` OCR + `hybrid` 모듈 + `recognize_table=True`
- SDK 의 `verify=False` 에 따른 urllib3 경고는 스크립트에서 억제
- 응답 Content-Type 에 따라 자동 분기 (`application/zip` → 전개, `application/json` → 파일 저장, 기타 → text)

# Web UI vs API 검증 계획 (사내 PC 실행 필요)

## 검증 대상
동일 3개 파일을 두 경로로 변환 후 `compare_outputs.py` 로 정량 비교:

1. `CA01. 선행_CA 과제완료 보고서_Gen5+_ATL_251231.pptx`
2. `MP102. 선행_MP1 1차 Cell Approve Sheet_Gen5+_ATL_250722.pdf`
3. `MP104. 선행_MP1 1차 Cycle data_Gen5+_ATL_250804.xlsx`

## 예상 절차

```bat
REM 사내 PC 에서
cd BDT_dev\tools\doc_converter
setup.bat
.venv\Scripts\python.exe -m pip install -e <doxa-sdk 경로>
set DOXA_TOKEN=<토큰>

REM 0. 연결성 확인
python doxa_smoke_test.py

REM 1. API 재변환
doxa_convert.bat "..\..\raw\g5p_at\MP102. ...pdf" "C:\tmp\doxa_api_out"
doxa_convert.bat "..\..\raw\g5p_at\CA01. ...pptx" "C:\tmp\doxa_api_out"
doxa_convert.bat "..\..\raw\g5p_at\MP104. ...xlsx" "C:\tmp\doxa_api_out"

REM 2. 자동 대조
python compare_outputs.py "..\..\raw" "C:\tmp\doxa_api_out" ^
    --label-a DoXA-Web --label-b DoXA-API ^
    --save-md "..\..\wiki\31_software_dev\260422_doxa_web_vs_api_result.md"
```

## 검증 지표 (compare_outputs.py 자동 측정)

| 지표 | 의미 | 격차 해석 |
|------|------|-----------|
| MD 크기 (B) | 추출된 정보량 | ↓ → 정보 손실 가능 |
| 한글 글자 수 | OCR 누락 여부 | Web 대비 ↓ → API OCR 약함 |
| `<table>` 수 | 표 인식률 | ↓ → 표 구조 해석 실패 |
| `rowspan`/`colspan` | 병합 셀 보존 | ↓ → 셀 구조 평탄화 |
| `<img>` / `![]()` | 이미지 참조 | ↓ → 이미지 추출 누락 |
| `page-break` | 페이지 마커 | 없음 → RAG 청킹 어려움 |
| 텍스트 유사도 (%) | diff ratio | < 80% → 내용 차이 유의 |

# 영향 범위

- 신규 파일만 추가, 기존 코드에 영향 없음
- 사외에서는 `ConnectionRefusedError` 로 실패 (정상 동작). 사내 PC 필요
- 토큰은 절대 저장소에 커밋되지 않음 (환경변수만)

# 관련

- [[feedback_local_only]] — 로컬 OSS 강제 원칙 (DoXA 는 사내 "로컬" 에 해당)
- [[260422_dev_doc_converter_tool]] — 모 파이프라인 문서
- [[project_fasoo_drm_xls]] / [[project_nasca_drm_pdf]] — 사내 DRM 체계

# TODO (후속)

- 사내 PC 실행 후 `compare_outputs.py` 결과를 `260422_doxa_web_vs_api_result.md` 로 저장
- 격차가 크면 DoXA API 파라미터 튜닝 검토 (`layout_model`, `image_captioning_level`, `bbox_scale` 등)
- 허용 격차라면 `convert.py` 메인 라우터에 DoXA 우선 분기 정식 추가
