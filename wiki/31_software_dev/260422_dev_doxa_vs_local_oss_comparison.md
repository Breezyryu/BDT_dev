---
title: "DoXA vs 로컬 OSS (marker-pdf/docling) 문서 변환 비교"
date: 2026-04-22
tags: [software_dev, doxa, docling, marker-pdf, markitdown, benchmark, comparison]
---

# 요약

3종 샘플 (pptx/pdf/xlsx) 을 **사내 DoXA** 와 **로컬 OSS 파이프라인** (docling + marker-pdf + markitdown) 으로 동시 변환해 결과를 비교.

**결론**: 모든 포맷에서 **DoXA 가 구조 보존·이미지 추출·가독성 면에서 로컬 OSS 를 능가**. 다만 수치 데이터 완전성 측면에선 docling 이 우위.

# 테스트 샘플

| # | 파일 | 원본 크기 | 포맷 특성 |
|---|------|---------|----------|
| 1 | `CA01. 선행_CA 과제완료 보고서_Gen5+_ATL_251231.pptx` | 21 MB | 33 슬라이드, 병합 표, 한글/영/漢 혼재, 차트 다수 |
| 2 | `MP102. 선행_MP1 1차 Cell Approve Sheet_Gen5+_ATL_250722.pdf` | 2.3 MB | 33 페이지, 양식 PDF, 서명/스탬프 이미지 |
| 3 | `MP104. 선행_MP1 1차 Cycle data_Gen5+_ATL_250804.xlsx` | 526 KB | 다중 시트, 수명 cycle 데이터 (1000+ 행) |

# 결과 메트릭

| 항목 | CA01 (pptx) | MP102 (pdf) | MP104 (xlsx) |
|------|-------------|-------------|--------------|
| **DoXA MD 크기** | 49.9 KB | 64.9 KB | 192 KB |
| **로컬 MD 크기** | 67.0 KB | 47.4 KB | 1,107 KB |
| **DoXA 이미지 수** | 64 JPEG | 18 JPEG | 0 |
| **로컬 이미지 수** | 75 PNG | **0** (markitdown fallback) | 0 |
| **DoXA 엔진** | 네이티브 | 네이티브 | 네이티브 |
| **로컬 엔진** | docling | markitdown (fallback) | docling |
| **DoXA 페이지 마커** | 33 개 | 33 개 | 있음 |
| **로컬 페이지 마커** | ❌ 없음 | ❌ 없음 | ❌ 없음 |

# 정성 비교

## 1) 테이블 구조 (가장 큰 차이)

### DoXA (CA01 Summary 테이블)
```html
<table><tbody>
  <tr><td>과제명</td><td>Gen5+ HHP 向 Si 음극 배터리 플랫폼 개발</td>
      <td>개발 일정</td><td>'24.09~'25.12 (16 개월)</td></tr>
  <tr><td>과제 개요</td>
      <td colspan="3">■ Gen5+ HHP 向 Si 음극 배터리 플랫폼 개발<br />
      1) 4.53V Si 음극 배터리 설계 ...</td></tr>
</tbody></table>
```
- ✅ `colspan`/`rowspan` 정확 보존
- ✅ `<br />` 로 원본 줄바꿈 재현
- ✅ 병합 셀 의미론적 복원

### 로컬 (docling)
```md
| 과제명 | Gen5+ HHP向 Si 음극 배터리 플랫폼 개발 | Gen5+ HHP向 Si 음극 배터리 플랫폼 개발 | 개발 일정 | ‘24.09~’25.12 (16개월) |
| 과제 개요 | ■ Gen5+ ... | ■ Gen5+ ... | ■ Gen5+ ... | ■ Gen5+ ... |
```
- ❌ 병합 셀을 **단순 복제**하여 중복 발생 → 의미 왜곡
- ❌ 한 셀 내용이 수백 자 일 때도 단일 행으로 표현 → 가독성 심각 저하
- ✅ 표준 Markdown 이라 도구 호환성 좋음

### 판정: **DoXA 압승**. 특히 Approval Sheet (MP102) 같은 서식 PDF에서는 로컬(markitdown fallback)이 테이블 구조를 완전히 상실한 반면 DoXA 는 `<table>` + 이미지 참조까지 병합 셀 내 정확히 배치.

## 2) 이미지 추출

| 항목 | DoXA | 로컬 |
|------|------|------|
| **CA01.pptx** | 64 JPEG, 파일명 `{페이지}p_{인덱스}.jpeg` (e.g. `3p_8.jpeg`) | 75 PNG, 파일명 `image_000000_{hash}.png` (해시) |
| **MP102.pdf** | 18 JPEG (서명/스탬프 포함) | **0** (markitdown fallback 은 텍스트 추출만) |
| **파일명 체계** | 원본 위치 추적 가능 | 해시 기반, 원본 위치 불명 |
| **포맷** | JPEG (더 작음) | PNG (무손실) |

### 판정: **DoXA 우위**. PDF에서 로컬이 이미지를 전혀 추출하지 못한 점이 결정적. 파일명 규칙도 DoXA가 디버깅·RAG 인덱싱에 유리.

## 3) 한글/영/漢 정확도

두 도구 모두 **임베디드 텍스트**는 정확. pptx/docx/xlsx 는 텍스트가 XML 로 포함되어 있어 OCR 불필요. 차이는 PDF 에서만 발생:

| 항목 | DoXA | 로컬 (marker-pdf + docling + markitdown) |
|------|------|-------------------------------------|
| 한글 (본문) | ✅ 정확 | ✅ 정확 (marker 가 선호 되었을 때) |
| 영문 (영어 라벨) | ✅ 정확 | ✅ 정확 |
| 중국어 (`向`, `社`, `比`) | ✅ 정확 | ✅ 정확 |
| 수식/단위 (`↑`, `↓`, `×10⁻⁶`) | ✅ 정확 | ✅ 정확 |
| 특수문자 (`□`, `■`, `△T`) | ✅ 정확 | ✅ 정확 |

### 판정: **동급**. OSS 파이프라인도 2026년 기준 충분한 품질.

## 4) 페이지/슬라이드 추적

| 항목 | DoXA | 로컬 |
|------|------|------|
| 페이지 마커 | `<!-- page-break:page-N -->` 삽입 | ❌ 없음 |
| RAG 청크 용도 | 페이지 단위 분할 가능 | 제목 기반 휴리스틱 필요 |
| 원본 위치 역추적 | 가능 | 어려움 |

### 판정: **DoXA 우위**. RAG 파이프라인에 곧바로 투입 가능한 구조.

## 5) 수치 데이터 완전성 (xlsx)

MP104.xlsx 는 1000+ 행의 cycle 데이터 포함:

| 항목 | DoXA | 로컬 (docling) |
|------|------|----------------|
| MD 크기 | 192 KB | **1,107 KB** (5.7×) |
| MD 줄 수 | 15,110 | 1,829 |
| 행 포함 | 일부 시트 구조만 | **전체 데이터** |

DoXA 는 문서 이해 중심(요약/헤더), docling 은 원본 복제 중심. **데이터 분석/post-processing 용도로는 docling 우위**. DoXA 는 전체 테이블을 HTML 로 표현하려 해 행당 10+ 줄로 분할되며 실제 데이터는 상위 일부만 포함한 것으로 보임.

# 종합 매트릭스

| 평가 축 | DoXA | 로컬 OSS | 비고 |
|---------|------|----------|------|
| 테이블 구조 (colspan/rowspan) | ★★★★★ | ★★★ | DoXA HTML 병합 셀 완벽 |
| 이미지 추출 (PDF) | ★★★★★ | ★★ | 로컬은 PDF에서 markitdown fallback 시 0개 |
| 이미지 추출 (pptx) | ★★★★ | ★★★★ | 거의 동급 |
| 텍스트 정확도 (한/영/漢) | ★★★★★ | ★★★★★ | 동급 |
| 페이지 추적 | ★★★★★ | ★ | 로컬 미지원 |
| 양식 PDF 이해 (Approval Sheet) | ★★★★★ | ★★ | 로컬 구조 상실 |
| 대용량 xlsx 데이터 완전성 | ★★★ | ★★★★★ | docling 이 전체 행 포함 |
| MD 표준성/도구 호환 | ★★★ (HTML 혼합) | ★★★★ (순수 MD) | 후처리 파이프라인 차이 |
| 보안 (사내 인증) | ★★★★★ | ★★★ | DoXA 는 사내 IAM 내 |
| 오프라인 동작 | ★★★★★ | ★★★★★ (HF 캐시 후) | 둘 다 오프라인 OK |

# 권장 사용

| 상황 | 권장 도구 |
|------|-----------|
| **사내 PC + 기밀 문서** | **DoXA** (사내 IAM, 구조 보존, 이미지 완전) |
| 사내 PC + 대용량 xlsx (수치 분석) | **로컬 docling** (전체 행 보존) |
| 사외 PC / 오픈 논문 | **로컬 OSS** (marker-pdf → docling) |
| Approval Sheet / 서식 PDF | **DoXA 필수** (로컬은 양식 구조 상실) |
| RAG 인덱싱 (페이지 단위 청크) | **DoXA** (page-break 마커) |

# 하이브리드 파이프라인 제안

`tools/doc_converter/convert.py` 에 DoXA 어댑터 추가 시:

```python
def process_file(f, out_root, force):
    if os.environ.get("DOXA_API_URL") and is_corporate_network():
        ok, msg = convert_doxa(f, out_dir)   # 사내 우선
        if ok:
            return ok, msg
    # 사외 또는 DoXA 실패 시 로컬 OSS fallback
    return local_pipeline(f, out_dir)
```

→ 사내에선 DoXA 구조·이미지 품질 활용, 사외에선 동일 출력 구조로 OSS 파이프라인 가동.

# 미확인 사항

- DoXA xlsx 행 truncation 여부 (192KB 제한?) — 사내 위키 확인 필요
- DoXA OCR engine 종류 (HVFA 추정) — 공식 스펙 미공개
- DoXA API 호출 방법 / 인증 체계 — 사내 Confluence 참조 필요

# 관련

- [[260422_dev_doc_converter_tool]] — 로컬 파이프라인 구축
- [[feedback_local_only]] — 로컬 OSS 강제 원칙
- [[project_nasca_drm_pdf]] — DRM PDF 회피 필요 사례
