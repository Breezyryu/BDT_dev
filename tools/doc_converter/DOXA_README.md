# DoXA 어댑터 — 사내 API 기반 문서 변환

## 전제 조건
- **사내 네트워크** (아래 3가지 URL 중 최소 1개 접근 가능)
  1. 직접 : `https://doxa.sec.samsung.net`
  2. iPaaS 사내 : `https://ipaas-sca.sec.samsung.net/sec/kr/doxa_parser_document_v2/1.0`
  3. iPaaS 외부 : `https://sca.ipaas.samsung.com/sec/kr/doxa_parser_document_v2/1.0`
- Python 3.12+, uv
- AI Asset Hub 에서 발급받은 `DOXA_TOKEN`
- DoXA SDK (`doxa-sdk`) — 사내 GitHub 에서 설치

### 네트워크 존별 권장 URL
| 환경 | 권장 URL | 환경변수 설정 |
|------|----------|---------------|
| 사내 PC 직접 접속 가능 | `doxa.sec.samsung.net` (기본) | (설정 불필요) |
| 사내 PC 에서 iPaaS 경유 | iPaaS 사내 | `set DOXA_URL=https://ipaas-sca.sec.samsung.net/sec/kr/doxa_parser_document_v2/1.0` + `set IPAAS_TOKEN=<토큰>` |
| 외부/VPN | iPaaS 외부 | `set DOXA_URL=https://sca.ipaas.samsung.com/sec/kr/doxa_parser_document_v2/1.0` + `set IPAAS_TOKEN=<토큰>` |

**어떤 URL 이 되는지 자동 확인**: `uv run python doxa_smoke_test.py` 는 3개 URL 모두 시도해서 동작하는 것을 알려줍니다.

## 사내 PC 첫 셋업 (1회)

```bat
REM 1. 저장소 clone
git clone <BDT_dev repo>
cd BDT_dev\tools\doc_converter

REM 2. 기본 의존성 (로컬 OSS 파이프라인용)
setup.bat

REM 3. DoXA SDK 추가 설치 — 세 가지 방법 중 택1
REM   A) 사내 GitHub 에서 직접 설치
.venv\Scripts\python.exe -m pip install git+https://github.sec.samsung.net/ProductivityTool/doxa-sdk.git

REM   B) 로컬 clone 한 경로에서 editable install
.venv\Scripts\python.exe -m pip install -e C:\path\to\doxa-sdk-main

REM   C) uv 환경이면
uv pip install -e C:\path\to\doxa-sdk-main

REM 4. 토큰 설정 — 아래 3가지 중 하나
REM   (A) 권장: .env 파일 (gitignored, git pull 해도 유지)
copy tools\doc_converter\.env.example tools\doc_converter\.env
REM    → .env 편집해 DOXA_TOKEN=<토큰> 채우기

REM   (B) setx 영구 환경변수 (시스템 전체)
setx DOXA_TOKEN "<토큰>"

REM   (C) 현재 세션만
set DOXA_TOKEN=<AI Asset Hub에서 발급한 토큰>
```

## 토큰 관리 — 반드시 지킬 것

- ❌ **파일 하드코딩 금지** (스크립트/노트북/배치파일 전부)
- ❌ **git commit 금지** — 현재 리포 `github.com/Breezyryu/BDT_dev` 는 **외부 공개 GitHub**
- ✅ **`.env` 사용** — `tools/doc_converter/.env.example` 복사 → `.env` 로 이름 변경 후 값 채우기
- ✅ **스크립트는 `python-dotenv` 로 .env 자동 로드** — 따로 import 없이 동작
- ✅ **만료 확인** — JWT `exp` 필드로 확인 (smoke test 가 자동 출력)

## 사용법

### 단일 파일
```bat
doxa_convert.bat "C:\path\file.pdf"
doxa_convert.bat "C:\path\file.pdf" "C:\output"
```

### 디렉토리 일괄 처리
```bat
doxa_convert.bat "C:\path\raw\g5p_at"
```

### 응답 포맷 지정
```bat
REM 옵션: standard (기본), markdown_only, json_only, json_with_image, debug_info
doxa_convert.bat "C:\path\file.pdf" "C:\output" --format markdown_only
```

## Web UI vs API 품질 비교 절차

사내 피드백상 "API 결과물 품질이 Web 대비 다소 낮다"는 보고가 있어, 양자 대조:

```bat
REM 1. 기존 Web UI 결과물 위치
set WEB_DIR=C:\Users\Ryu\battery\python\BDT_dev\raw

REM 2. 동일 파일을 API 로 재변환
set API_DIR=C:\tmp\doxa_api_out
doxa_convert.bat "C:\Users\Ryu\battery\python\BDT_dev\raw\g5p_at\MP102. 선행_MP1 1차 Cell Approve Sheet_Gen5+_ATL_250722.pdf" "%API_DIR%"
doxa_convert.bat "C:\Users\Ryu\battery\python\BDT_dev\raw\g5p_at\CA01. 선행_CA 과제완료 보고서_Gen5+_ATL_251231.pptx" "%API_DIR%"
doxa_convert.bat "C:\Users\Ryu\battery\python\BDT_dev\raw\g5p_at\MP104. 선행_MP1 1차 Cycle data_Gen5+_ATL_250804.xlsx" "%API_DIR%"

REM 3. 자동 비교 리포트 생성
.venv\Scripts\activate
python compare_outputs.py "%WEB_DIR%" "%API_DIR%" --label-a "DoXA-Web" --label-b "DoXA-API" --save-md C:\tmp\doxa_web_vs_api.md
```

생성되는 `doxa_web_vs_api.md` 에서 확인 가능:
- 파일 크기·라인 수·한글 글자 수 증감
- `<table>` / `rowspan` / `colspan` / `page-break` 카운트
- 텍스트 유사도 (%)
- A만/B만 존재하는 파일 목록

## 출력 구조

```
<output_dir>/
└── <stem>/
    ├── <stem>.md              # Markdown 본문 (standard 포맷)
    ├── <stem>.json            # 구조화 데이터 (standard 포맷)
    ├── image/                 # 본문 이미지
    │   └── *.png
    └── page_image/            # 페이지 스냅샷
        └── *.png
```

`response_format` 에 따라 구조 차이:
| format | MD | JSON | page_image | image |
|--------|:--:|:----:|:----------:|:-----:|
| `standard` | ✅ | ✅ | ✅ | ✅ |
| `markdown_only` | ✅ | | | ✅ |
| `json_only` | | ✅ | | |
| `json_with_image` | | ✅ | | ✅ |
| `page_image_only` | | | ✅ | |
| `debug_info` | ✅ | ✅ | ✅ | ✅ (디버그 정보 추가) |

## 토큰 관리 주의

- ❌ **하드코딩 금지** — 스크립트/노트북에 직접 쓰지 말 것
- ❌ **git commit 금지** — `.env`, `*.token` 은 `.gitignore` 에 추가
- ❌ **로그에 찍지 말 것** — 본 스크립트는 토큰을 출력하지 않음
- ✅ **환경변수만** — `set DOXA_TOKEN=...` (세션) 또는 `setx` (영구)
- ✅ **만료 확인** — JWT `exp` 필드로 만료일 확인 가능
- ✅ **그룹 권한** — 토큰은 발급 그룹에 따라 권한 다름 (e.g., `Advanced_Battery_Lab`)

## 트러블슈팅

| 증상 | 원인 | 조치 |
|------|------|------|
| `ConnectionRefusedError: WinError 10061` | 사외 네트워크 | 사내 VPN 또는 사내 PC 에서 실행 |
| `401 Unauthorized` | 토큰 만료·잘못됨 | AI Asset Hub 에서 재발급 |
| `403 Forbidden` | 그룹 권한 부족 | 해당 서비스 접근 권한 요청 |
| `No module named 'doxa'` | SDK 설치 안 됨 | `pip install git+https://github.sec.samsung.net/...` |
| `urllib3 InsecureRequestWarning` | DoXA 내부 `verify=False` | 정상 (본 스크립트가 경고 억제) |

## 파이프라인 통합 (향후)

`convert.py` 메인 라우터에 DoXA 우선 분기 추가 예정:
```
PDF/pptx/docx/xlsx → (DOXA_TOKEN 설정 시) DoXA API
                   → MinerU 2.5-Pro
                   → docling
                   → markitdown
```
