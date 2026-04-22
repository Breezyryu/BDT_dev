---
title: "doc_converter 도구 추가 (문서 → Markdown 로컬 OSS 파이프라인)"
date: 2026-04-22
tags: [software_dev, tool, markdown, docling, marker-pdf, offline]
---

# 배경 / 목적

사내 기밀 개발 문서(과제계획서/Approval Sheet/DFMEA/분해분석 등 `raw/g5p_at/`)를 외부 서비스(pdf2md.app 등) 업로드 없이 **로컬 오픈소스**로 Markdown 변환해야 했음.

- 외부 API 업로드 = 사내 NDA/Fasoo DRM/NASCA DRM 정책 위반 소지
- `raw/g5p_at/` 46개 파일 (pptx/docx/xlsx/pdf/eml) 변환 검증 완료 → 45/46 성공 (1개는 NASCA DRM 으로 불가)

사내 PC 에서도 동작하도록 `git clone → setup.bat → convert.bat` 흐름의 독립 도구로 분리.

# 변경 내용

신규 추가: `tools/doc_converter/`

| 파일 | 역할 |
|------|------|
| `convert.py` | 메인 파이프라인 (PDF/xlsx/pptx/docx/eml 라우팅 + DRM 감지) |
| `prefetch_models.py` | HF 모델 사전 다운로드 (Surya/docling-layout/TableFormer/EasyOCR) |
| `requirements.txt` | 의존성 pin (docling, marker-pdf, markitdown, easyocr, pymupdf, pandas) |
| `setup.bat` | venv 생성 + pip install + 모델 prefetch (1회) |
| `convert.bat` | 변환 실행 (`HF_HUB_OFFLINE=1` 자동 설정) |
| `README.md` | 사용법 + HF 차단 환경 우회 (`~/.cache/huggingface` 수동 복사) |

# 파이프라인 라우팅

```
PDF   → marker-pdf (Surya OCR ko/en) → docling → pymupdf → markitdown
xlsx  → docling → pandas (in-memory custom_doc_props strip) → markitdown
pptx  → docling → markitdown
docx  → docling → markitdown
eml   → markitdown
```

핵심 설계 결정:
- **marker-pdf 우선**: 2026 PDF→MD 벤치마크 종합 1위, Surya OCR 로 한글 지원
- **docling 차선**: office 포맷 네이티브 + 구조화 보존 강점
- **pandas xlsx 복구**: openpyxl `custom_doc_props` NoneType 버그 회피를 위해 `customXml/` + `docProps/custom.xml` 을 **in-memory zip re-pack** 으로 스트립 (Windows 파일잠금 회피)
- **DRM 감지**: 파일 헤더 바이트 패턴으로 NASCA DRM 자동 감지 → SKIP 리포트 기재
- **오프라인 강제**: `HF_HUB_OFFLINE=1` + `TRANSFORMERS_OFFLINE=1` 환경변수로 재다운로드 차단

# 영향 범위

- 신규 도구, 기존 BDT 코드에 영향 없음
- `raw/*_md/` 패턴으로 출력 (원본 옆에 배치)
- 의존성 ~3GB (모델 가중치 HF 캐시) — PyInstaller 번들 미포함, pip 기반

# 테스트 결과 (2026-04-22, `raw/g5p_at/` 46 파일)

| 엔진 | 처리 건수 | 비고 |
|------|----------|------|
| docling | 32 | pptx/docx/xlsx 대부분 |
| marker-pdf | 0 (fallback 미발생) | 1차 변환은 docling 으로 완료 |
| markitdown | 9 | PDF fallback + eml |
| pandas-xlsx | 2 | MP106/MP207 분해분석 복구 |
| 실패 | 1 | PA04 (NASCA DRM 래퍼) |

**성공률: 45/46 (97.8%)**

# 관련

- [[feedback_local_only]] — 로컬 OSS 강제 원칙
- [[project_nasca_drm_pdf]] — NASCA DRM 탐지/대응
- [[project_fasoo_drm_xls]] — Fasoo DRM 유사 사례
