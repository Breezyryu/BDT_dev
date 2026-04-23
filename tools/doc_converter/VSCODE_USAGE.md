# VS Code 에서 실행하기 — Quick Start

## 사전 조건

- **Python 3.12+** 설치
- **uv** 설치 (BDT 프로젝트 표준 가상환경 관리자)
  ```powershell
  # PowerShell
  irm https://astral.sh/uv/install.ps1 | iex
  ```

## 가상환경 위치 규칙 (중요)

사내 표준 레이아웃:
```
<workdir>/
├── .venv/              ← uv 가상환경 (BDT_code 형제)
└── BDT_code/           ← git clone 저장소
    └── tools/
        └── doc_converter/
            └── .venv/  ← setup.bat 이 공유 venv 로 junction 생성 (자동)
```

`setup.bat` 은 자동으로 탐지:
1. `<BDT_code>/../.venv` (사내 표준) 있으면 → `tools/doc_converter/.venv` 로 **junction 연결**
2. 없으면 → `tools/doc_converter/.venv` 에 **uv venv 로 신규 생성**

→ **VS Code 설정과 `.bat` 런처는 모두 `tools/doc_converter/.venv/Scripts/python.exe` 로 일관 접근** (junction 투명하게 동작)

## 사용 방식 (둘 중 하나 선택)

### ✅ 방식 A: doc_converter 폴더를 VS Code 로 열기 (권장)

1. VS Code → **파일 → 폴더 열기** → `tools\doc_converter` 선택
2. **처음 한 번만**: `Ctrl+Shift+P` → `Tasks: Run Task` → `0. 셋업 (venv + 의존성, 1회)` 실행
   - 내부 동작: `uv venv --python 3.12` → `uv pip install -r requirements.txt`
3. 이후:
   - **F5** 누르기 → 런치 목록에서 `① 문서 변환 (로컬 OSS, 대화식)` 선택
   - 또는 **Ctrl+Shift+B** → 기본 빌드 태스크 (로컬 OSS 변환) 실행
   - **폴더 선택 창**이 뜨면 원하는 소스 폴더 지정 → 진행

### 방식 B: BDT_dev 루트를 VS Code 로 열기

1. VS Code → **파일 → 폴더 열기** → `BDT_dev` 선택
2. 터미널에서 1회 셋업:
   ```bat
   cd tools\doc_converter
   setup.bat
   REM  내부적으로 uv venv + uv pip install
   ```
3. **F5** → `doc_converter: 문서 변환 (로컬 OSS)` 등 선택

---

## 실행 가능한 항목 (F5 / Run Task)

| 번호 | 이름 | 역할 |
|:--:|------|------|
| 0 | **셋업** (Run Task) | venv 생성 + pip install + 모델 prefetch (1회) |
| ① | **문서 변환 (로컬 OSS)** | 로컬 marker-pdf + docling + markitdown 파이프라인 |
| ② | **문서 변환 (DoXA API)** | 사내 DoXA API (DOXA_TOKEN 필요) |
| ③ | **DoXA 스모크 테스트** | API 접속·토큰 유효성 사전 확인 |
| ④ | **두 결과 비교** | 두 폴더 MD 자동 대조 (크기·테이블·한글·유사도) |
| ⑤ | **현재 파일 디버그** | 편집 중인 .py 에 F5 바로 |

---

## DoXA 사용 시 (사내 PC)

DoXA 항목을 실행하기 전에 토큰 환경변수 설정 필요:

### PowerShell (일회성)
```powershell
$env:DOXA_TOKEN = "<AI Asset Hub 발급 토큰>"
code .  # VS Code 재실행 (환경변수 상속)
```

### cmd (일회성)
```bat
set DOXA_TOKEN=<토큰>
code .
```

### 영구 설정
```bat
setx DOXA_TOKEN "<토큰>"
REM 이후 새 터미널/VS Code 에서 자동 적용
```

**또는** `.env` 파일 사용 (VS Code Python 확장이 자동 로드):
```
# tools/doc_converter/.env  (커밋 금지!)
DOXA_TOKEN=<토큰>
```

---

## 흐름 예시

### 로컬 OSS 변환
1. F5 → ①번 선택
2. 폴더 선택 창 → `C:\Users\Ryu\battery\python\BDT_dev\raw\g5p_at` 선택
3. 출력 폴더 확인 창 → `예` (기본 `g5p_at_md`)
4. 재변환 여부 → `아니요`
5. 터미널에 진행 상황 표시 → 완료 시 리포트 생성

### DoXA Web vs API 비교
1. 사내 PC 에서 DOXA_TOKEN 설정
2. F5 → ③ 스모크 테스트로 연결 확인
3. F5 → ② DoXA API 변환 (Web UI 로 이미 변환된 동일 파일 대상)
4. F5 → ④ 비교 → A=Web 결과 폴더, B=API 결과 폴더 선택 → 리포트 저장

---

## 트러블슈팅

| 증상 | 원인 | 조치 |
|------|------|------|
| `.venv 없음` | 셋업 미실행 | Run Task → `0. 셋업` |
| `uv: command not found` | uv 미설치 | PowerShell `irm https://astral.sh/uv/install.ps1 \| iex` |
| `ModuleNotFoundError: doxa` | DoXA SDK 미설치 | 터미널에서 `uv pip install -e <doxa-sdk 경로>` |
| 대화창 안 뜸 | tkinter 미설치 (드문 경우) | Python 재설치 시 tkinter 옵션 체크 |
| 한글 깨짐 | 인코딩 문제 | settings.json 의 `PYTHONIOENCODING=utf-8` 확인 |
| `ConnectionRefusedError` | DoXA = 사외 네트워크 | 사내 PC 또는 VPN 에서 실행 |
