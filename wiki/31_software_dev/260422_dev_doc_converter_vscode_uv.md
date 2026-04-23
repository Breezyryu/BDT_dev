---
title: "doc_converter VS Code 통합 + uv 가상환경 전환"
date: 2026-04-22
tags: [software_dev, doc_converter, vscode, uv, interactive]
---

# 배경 / 목적

2026-04-22 사용자 요청:
1. "VS Code 에서 실행만 하면 진행되도록 변경" → **F5 / Ctrl+Shift+B 한 번으로 즉시 사용 가능**하도록 UX 개선
2. "가상환경은 uv 로 설정하고 싶다. 현재 BDT 기준으로 uv 환경을 구성했기 때문에" → **BDT 프로젝트 표준 (uv) 와 통일**

# 변경 내용

## 1. 대화식 모드 (CLI 인자 없을 때 GUI 다이얼로그)

기존: `python convert.py <source> [output] [--force]` 만 허용.
변경: 인자 없이 실행하면 **tkinter 파일 다이얼로그** 로 소스·출력 폴더 선택.

- `convert.py::_pick_folders_interactive` — 소스 폴더 + 출력 폴더 + 재변환 여부
- `doxa_convert.py::_pick_interactive` — 단일 파일/폴더 선택 + 출력 + 응답 포맷 + DOXA_TOKEN 사전 체크
- `compare_outputs.py::_pick_interactive` — 비교 대상 A·B 폴더 + 리포트 저장 경로

→ **F5 → 파일 선택창 → 진행** 흐름으로 매뉴얼 CLI 호출 불필요.

## 2. VS Code 통합 (`.vscode/`)

`tools/doc_converter/.vscode/` 신규 생성:
- `launch.json` — F5 디버그 구성 5개 (로컬 OSS 변환 / DoXA / 스모크 / 비교 / 현재 파일)
- `tasks.json` — Run Task 엔트리 6개 (셋업 / 4종 변환·비교 / 모델 prefetch)
- `settings.json` — Python 인터프리터 `${workspaceFolder}/.venv/Scripts/python.exe` 자동 지정 + `PYTHONIOENCODING=utf-8`

루트 `.vscode/launch.json` 에도 `doc_converter:` 접두사로 4개 엔트리 추가 (BDT_dev 루트를 열었을 때도 바로 사용 가능).

## 3. uv 전환 + 공유 venv junction

기존 `python -m venv / pip install` → **`uv venv / uv pip install`** 로 전환.

사내 표준 레이아웃 대응:
```
<workdir>/
├── .venv/          ← 공유 uv venv (BDT_code 형제)
└── BDT_code/
    └── tools/doc_converter/
        └── .venv/  ← junction → ../../../.venv (setup.bat 자동 처리)
```

- `setup.bat` 탐지 순서:
  1. `<repo>/../.venv` (BDT_code 부모 = 사내 표준) 발견 → `mklink /J .venv <path>` junction 연결
  2. `<repo>/.venv` (저장소 루트) 발견 → junction 연결
  3. 둘 다 없음 → 로컬 `uv venv --python 3.12` 로 신규 생성
  → VS Code 설정과 `.bat` 런처는 모두 `tools/doc_converter/.venv/Scripts/python.exe` 로 일관 접근

- `convert.bat` / `doxa_convert.bat` : `call .venv\Scripts\activate.bat && python ...` → `uv run python ...`
- `pyproject.toml` 신규 추가 — uv 프로젝트 메타데이터 + 의존성 명시

BDT 루트 `pyproject.toml` 과 동일한 uv 기반 구조.

## 4. `.gitignore` 수정

`.vscode/` 는 전역 무시이나, **`tools/doc_converter/.vscode/` 만 예외 허용** (공유 설정이기 때문):
```
.vscode/
!tools/doc_converter/.vscode/
!tools/doc_converter/.vscode/**
```

## 5. stderr 래핑 방어 코드

`sys.stdout = io.TextIOWrapper(...)` 를 모듈 최상위에서 수행하면 **import 시점**에도 실행되어 테스트 환경에서 "lost sys.stderr" 오류 발생.
→ `if __name__ == "__main__":` 블록 + `try/except (AttributeError, ValueError)` 로 방어.

# 사용자 흐름 (변경 후)

```
1. BDT_dev clone
2. VS Code 로 tools/doc_converter/ 열기
3. Ctrl+Shift+P → Tasks: Run Task → "0. 셋업"  (1회)
4. F5 → ① 문서 변환 (로컬 OSS, 대화식)
5. 파일 선택창 → 소스 폴더 선택 → 진행
```

사내 PC 에서 DoXA 사용 시:
```
set DOXA_TOKEN=<토큰>
code .
F5 → ② 문서 변환 (DoXA API)
```

# 영향 범위

- 기존 CLI 호출 방식은 그대로 유지 (`convert.py <source>` 정상 동작)
- 대화식 모드는 인자 없을 때만 발동
- uv 로 전환해도 `.venv/Scripts/python.exe` 는 동일 위치이므로 `.vscode/launch.json` 호환성 유지
- DoXA SDK 는 별도 설치 필요 (`uv pip install -e <doxa-sdk 경로>`) — 사내 GitHub 접근 가능 시만

# 관련

- [[260422_dev_doc_converter_tool]] — 원본 도구 추가
- [[260422_dev_doxa_adapter_and_web_vs_api_plan]] — DoXA 어댑터 + 검증 계획
