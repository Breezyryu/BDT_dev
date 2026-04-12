# Instruction 파일 전면 개선

**날짜**: 2026-03-19  
**카테고리**: refactor  

## 배경

`.github/instructions/` 폴더의 instruction 파일들이 실제 프로젝트 구조와 불일치하거나, 프로젝트와 무관한 웹 기술 내용을 포함하고 있어 전면 검토 및 개선을 진행함.

## 변경 파일 및 내용

### 1. `project-rules.instructions.md` — 전면 보강

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| 프로젝트 구조 | 없음 | 폴더/파일별 역할 테이블 추가 |
| 개발 워크플로우 | 없음 | proto → 프로덕션 병합 흐름 명시 |
| 파일 보호 | `BatteryDataTool_UI.py` (구 파일명) | `DataTool_dev/DataTool_UI.py` (현재 파일명) |
| Git 커밋 규칙 | 없음 | `[카테고리] 요약` 형식 추가 |
| 경로 규칙 | 기본적 | EXE 환경 분기 코드 예시 추가 |
| Python/PyQt6 | `BatteryDataTool.py`에서 수정 (구 파일명) | 프로덕션 메인 파일에서 수정 + UI 동기화 규칙 |
| 선택적 의존성 | 없음 | `try-except` + `HAS_<LIB>` 패턴 명시 |
| PyInstaller | `--hidden-import`만 언급 | `--collect-all`, 런타임 후크, `.spec` 관리 추가 |
| 마크다운 규칙 | 기본적 | 카테고리별 접두어 권장 (changelog, analysis, fix 등) |
| 스킬 활용 | 1줄 | 스킬별 적용 시기 구체 명시 |

### 2. `python-style.instructions.md` — import 예시 수정

- `from BatteryDataTool_UI import Ui_sitool` → `from DataTool_UI import Ui_sitool`
- 현재 프로젝트의 모듈명(`DataTool_UI`)에 맞춤

### 3. `frontend-design.instructions.md` — PyQt6 전용으로 전면 재작성

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| 대상 기술 | 웹 (React, HTML, CSS) | PyQt6 데스크톱 앱 |
| 색상/테마 | CSS 변수 | THEME 딕셔너리 + QSS |
| 레이아웃 | CSS Grid, Flexbox | QVBoxLayout, QHBoxLayout, QGridLayout |
| 애니메이션 | CSS transition, scroll-trigger | — (해당 없음, 삭제) |
| 폰트 규칙 | 웹 폰트 사용 금지 | 맑은 고딕 기본 (한글 지원) |
| 차트 | — | matplotlib FigureCanvas 통합 가이드 |
| 테이블 성능 | — | QTableWidget 대량 데이터 최적화 패턴 |
| 금지 사항 | AI 미학 관련 | 절대 좌표, GUI 스레드 블로킹 등 |

### 4. `instruct.instructions.md` — 메타 가이드로 재정의

- 변경 전: 템플릿 플레이스홀더만 존재 ("Describe when these instructions should be loaded")
- 변경 후: instruction 파일 작성·관리 규칙 (YAML 프론트매터 형식, applyTo 패턴 가이드, 작성 원칙)
- `applyTo: '**/*.instructions.md'` 로 실제 적용 범위 설정

### 5. `docx.instructions.md` — Python 기반으로 전면 재작성

- 변경 전: JavaScript `docx-js` (npm) + 존재하지 않는 스크립트 (`scripts/office/unpack.py` 등)
- 변경 후: `python-docx` 기반 (Document, Paragraph, Table, 스타일, 페이지 설정 등)

### 6. `pptx.instructions.md` — Python 기반으로 전면 재작성

- 변경 전: JavaScript `pptxgenjs` (npm) + 존재하지 않는 스크립트 (`scripts/thumbnail.py` 등)
- 변경 후: `python-pptx` 기반 (슬라이드 생성, 텍스트/테이블/도형, matplotlib 차트 삽입)
- BDT 프로젝트 THEME 팔레트와 연동하는 색상 가이드 포함

## 변경하지 않은 파일

| 파일 | 사유 |
|------|------|
| `pybamm.instructions.md` | 도메인 특화 규칙. 정확하고 프로젝트에 맞음 |
| `pdf.instructions.md` | Python 기반(pypdf, pdfplumber, reportlab). 적절함 |
| `xlsx.instructions.md` | Python 기반(pandas, openpyxl). 적절함 |
