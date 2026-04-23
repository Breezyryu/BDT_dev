---
title: "marker-pdf 제거 → MinerU 를 PDF 1순위로 승격"
date: 2026-04-22
tags: [software_dev, doc_converter, mineru, dependency, pillow]
---

# 배경 / 목적

사내 PC `uv pip install -r requirements.txt` 실행 중 의존성 충돌 발생:

```
mineru[core]>=3.1.0 depends on pillow>=11.0.0.
marker-pdf>=1.10.0 depends on pillow>=10.1.0, <11.0.0
marker-pdf>=1.10.0 and mineru[core]>=3.1.0 are incompatible
```

조사 중 **marker-pdf 의 또 다른 문제** 발견:

```
$ uv pip show marker-pdf | grep Requires
Requires: anthropic, click, filetype, ftfy, google-genai, markdown2, markdownify,
          openai, pdftext, pillow, pre-commit, pydantic, pydantic-settings,
          python-dotenv, rapidfuzz, regex, scikit-learn, surya-ocr, torch, ...
```

**marker-pdf 가 anthropic / openai / google-genai 3대 클라우드 AI SDK 를 transitively 설치**. 이는 사용자 방침 "외부 AI 서비스 접근 금지" (`feedback_local_only.md`) 위반. 즉 pillow 충돌 여부와 무관하게 제거 대상.

# 변경 내용

**marker-pdf 를 전면 제거하고 MinerU 를 PDF 변환 1순위로 승격.**

## 파이프라인 라우팅 변경

| 포맷 | 변경 전 | 변경 후 |
|------|---------|---------|
| PDF  | marker-pdf → docling → pymupdf → markitdown | **MinerU 2.5-Pro** → docling → pymupdf → markitdown |
| 기타 | (변경 없음) | (변경 없음) |

## 코드 수정

- `tools/doc_converter/convert.py`
  - `get_marker()`, `convert_marker()` 제거
  - `convert_mineru()` 신규 추가 — subprocess 로 `mineru -p <src> -o <work> -b pipeline -l korean` 호출 후 출력물 정리
  - PDF 라우팅 루프: `(convert_marker, ...)` → `(convert_mineru, ...)`
- `tools/doc_converter/requirements.txt` — marker-pdf 제거
- `tools/doc_converter/pyproject.toml` — marker-pdf 제거
- `tools/doc_converter/prefetch_models.py` — surya (marker 의존) 제거, MinerU CLI warm-up 추가
- `tools/doc_converter/setup.bat` — 순차 설치 fallback 에서 marker-pdf 제거
- `tools/doc_converter/README.md` — 지원 포맷 표 + 의존성 명시 갱신

# 정당성 근거

2026-04-22 3-way 비교 (`260422_dev_doxa_vs_local_oss_comparison` + 후속 MinerU 테스트) 에서:

| 항목 | DoXA | marker-pdf | MinerU 2.5-Pro |
|------|------|-----------|-----------------|
| PDF Approval (MP102) | ★★★★★ | ★★★ (이미지 누락 0) | ★★★★★ (52개 추출) |
| HTML colspan/rowspan | ✅ | ❌ (마크다운 표) | ✅ |
| 셀 안 `<img>` | ✅ | ❌ | ✅ |
| 외부 AI SDK | (사내 API) | **anthropic/openai/google-genai** | **없음** |

→ MinerU 는 DoXA 와 동급 품질 + 외부 AI 의존성 제로. marker-pdf 대비 우월.

# 영향 범위

- PDF 변환 1순위 엔진 교체 (품질 향상)
- pillow 충돌 해소 → `uv pip install -r requirements.txt` 정상 동작
- 설치 용량 감소 (anthropic / openai / google-genai SDK 및 deps 제거)
- PyInstaller 로 DataTool.exe 빌드 시 여전히 영향 없음 (BDT 는 이들 라이브러리 import 하지 않음)

# 관련

- [[260422_dev_doc_converter_tool]] — 원본 도구 추가
- [[260422_dev_doxa_vs_local_oss_comparison]] — DoXA vs 로컬 OSS 비교
- [[260422_dev_doxa_adapter_and_web_vs_api_plan]] — DoXA 어댑터
- [[feedback_local_only]] — 로컬 OSS 강제 원칙
