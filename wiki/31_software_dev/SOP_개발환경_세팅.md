---
relocated: 2026-04-22
source_vault: "docs/vault/04_Development/SOP_개발환경_세팅.md"
title: "SOP: Python 개발환경 세팅 (사내 Windows)"
tags:
  - SOP
  - Development
  - Python
  - 환경설정
  - 프록시
  - Git
type: sop
status: active
related:
  - "[[Python_환경설정]]"
  - "[[MOC_Development]]"
created: 2026-04-14
updated: 2026-04-14
---

# SOP: Python 개발환경 세팅 (사내 Windows)

> **대상**: 신규 입사자 / Python 개발환경을 처음 세팅하는 인원
> **환경**: Windows 10/11, VSCode, 사내 프록시 네트워크
> **소요 시간**: 약 1~2시간
> **최종 수정**: 2026-04-14

---

## 목차

1. [[#1. 사전 준비물 확인]]
2. [[#2. Python 설치]]
3. [[#3. VSCode 설치 및 기본 설정]]
4. [[#4. 사내 프록시 및 SSL 인증서 설정]]
5. [[#5. UV 패키지 매니저 설치]]
6. [[#6. 가상환경 생성 및 패키지 설치]]
7. [[#7. VSCode 확장 프로그램 설정]]
8. [[#8. Python 디버깅 설정]]
9. [[#9. Git 설치 및 프록시 설정]]
10. [[#10. 설치 확인 체크리스트]]
11. [[#부록 A. 트러블슈팅]]
12. [[#부록 B. 참고 링크]]

---

## 1. 사전 준비물 확인

시작하기 전에 아래 항목을 준비합니다.

| 항목 | 설명 | 확인 |
|------|------|------|
| **SSL 인증서 파일** | `DigitalCity.crt` — 사내 보안팀 배포 인증서 | ☐ |
| **프록시 주소** | `http://168.219.61.252:8080` | ☐ |
| **관리자 권한** | PC 소프트웨어 설치 권한 (IT4U 신청 필요 시 사전 처리) | ☐ |
| **사내 계정** | Knox 이메일, Git 계정 (Bitbucket/GitHub Enterprise) | ☐ |

> [!important] SSL 인증서 위치
> `DigitalCity.crt` 파일을 **고정된 경로**에 저장합니다.
> 권장 경로: `C:\Users\<사번>\certs\DigitalCity.crt`
> 바탕화면에 두면 경로에 한글/공백이 포함될 수 있으므로 피합니다.

---

## 2. Python 설치

### 2.1 다운로드

공식 사이트에서 Python을 다운로드합니다.
- 다운로드 URL: https://www.python.org/downloads/
- **권장 버전**: Python 3.12.x (BDT 프로젝트 호환 버전)

### 2.2 설치 과정

1. 다운로드한 설치 파일 실행
2. **첫 화면에서 반드시 체크**:
   - ☑ `Add python.exe to PATH` ← 이것을 빠뜨리면 터미널에서 python 명령이 동작하지 않음
   - ☑ `Use admin privileges when installing py.exe`
3. `Install Now` 클릭 (기본 경로 설치)
4. 설치 완료 후 `Disable path length limit` 클릭 (Windows 경로 길이 제한 해제)

### 2.3 설치 확인

PowerShell을 열고 아래 명령어를 실행합니다.

```powershell
python --version
# 출력 예시: Python 3.12.8

pip --version
# 출력 예시: pip 24.x.x from ...
```

> [!tip] 명령어가 동작하지 않는 경우
> `Add to PATH`를 체크하지 않고 설치했다면, **제어판 → 시스템 → 고급 시스템 설정 → 환경 변수**에서 `Path`에 Python 설치 경로를 수동 추가해야 합니다.
> 일반적으로 `C:\Users\<사번>\AppData\Local\Programs\Python\Python312\` 및 하위 `Scripts\` 폴더입니다.

---

## 3. VSCode 설치 및 기본 설정

### 3.1 다운로드 및 설치

- 다운로드 URL: https://code.visualstudio.com/
- `User Installer` 버전 다운로드 → 설치
- 설치 옵션에서 아래 항목 체크 권장:
  - ☑ `Add "Open with Code" action to Windows Explorer file context menu`
  - ☑ `Add "Open with Code" action to Windows Explorer directory context menu`
  - ☑ `Add to PATH`

### 3.2 관리자 권한 실행 설정

사내 프록시 환경에서는 **VSCode를 관리자 권한으로 실행**해야 일부 패키지 설치가 정상 동작합니다.

설정 방법:
1. VSCode 바로가기 아이콘 우클릭 → `속성`
2. `호환성` 탭 → ☑ `관리자 권한으로 이 프로그램 실행` 체크
3. `확인` 클릭

> [!note] 항상 관리자 권한이 필요하지는 않습니다
> 패키지 설치나 전역 설정 변경 시에만 필요합니다. 일반 코딩 작업은 일반 권한으로 충분합니다.

---

## 4. 사내 프록시 및 SSL 인증서 설정

사내 네트워크는 외부 인터넷 접속 시 **프록시 서버**를 경유합니다. Python 패키지 설치, Git 동작 등 모든 외부 통신에 프록시와 SSL 인증서 설정이 필요합니다.

### 4.1 프록시 정보

| 항목 | 값 |
|------|-----|
| HTTP 프록시 | `http://168.219.61.252:8080` |
| HTTPS 프록시 | `http://168.219.61.252:8080` |
| 자동 설정 (PAC) | `http://168.219.61.251:8088/samsungcs.pac` |
| 프록시 예외 | `localhost, 127.0.0.1, 10.*.*.*, 165.213.*.*, 168.219.*.*, *.sec.samsung.net` |

### 4.2 Windows 시스템 환경변수 등록 (영구 설정)

매번 터미널에서 입력하지 않도록 **시스템 환경변수**에 등록합니다.

1. `Win + R` → `sysdm.cpl` 입력 → `확인`
2. `고급` 탭 → `환경 변수` 클릭
3. **사용자 변수** 영역에서 `새로 만들기`를 3번 반복:

| 변수 이름 | 변수 값 |
|-----------|---------|
| `HTTP_PROXY` | `http://168.219.61.252:8080` |
| `HTTPS_PROXY` | `http://168.219.61.252:8080` |
| `SSL_CERT_FILE` | `C:\Users\<사번>\certs\DigitalCity.crt` |

> `<사번>` 부분은 본인의 Windows 사용자 폴더명으로 교체합니다.

4. `확인` → `확인` → 모든 터미널 창을 닫고 다시 열기

### 4.3 설정 확인

새 PowerShell 창을 열고 확인합니다.

```powershell
# 환경변수가 정상 등록되었는지 확인
$env:HTTP_PROXY
# 출력: http://168.219.61.252:8080

$env:HTTPS_PROXY
# 출력: http://168.219.61.252:8080

$env:SSL_CERT_FILE
# 출력: C:\Users\<사번>\certs\DigitalCity.crt
```

세 값이 모두 정상 출력되면 성공입니다.

### 4.4 VSCode settings.json에 터미널 환경변수 추가

시스템 환경변수와 별도로, VSCode 통합 터미널에서도 프록시가 동작하도록 설정합니다.

1. VSCode 실행
2. `Ctrl + Shift + P` → `Preferences: Open User Settings (JSON)` 검색 → 선택
3. 아래 내용을 `settings.json`에 추가:

```json
{
    "terminal.integrated.env.windows": {
        "HTTP_PROXY": "http://168.219.61.252:8080",
        "HTTPS_PROXY": "http://168.219.61.252:8080",
        "SSL_CERT_FILE": "C:\\Users\\<사번>\\certs\\DigitalCity.crt"
    }
}
```

> [!warning] JSON 경로 구분자
> JSON에서는 역슬래시(`\`)를 두 번 써야 합니다: `C:\\Users\\...`
> `<사번>` 부분은 본인 폴더명으로 교체합니다.

---

## 5. UV 패키지 매니저 설치

UV는 pip보다 **10~100배 빠른** Python 패키지 매니저입니다. BDT 프로젝트에서 표준으로 사용합니다.

### 5.1 UV 설치

PowerShell에서 실행합니다.

```powershell
pip install uv
```

> [!note] UV 버전 참고
> 사내 Wiki에는 UV 0.5.8 이하 사용이라고 기재되어 있으나, 실제로는 최신 버전(0.9.x 이상)도 프록시 환경에서 정상 동작합니다 (2025년 10월 확인).

### 5.2 UV 동작 확인

```powershell
uv --version
# 출력 예시: uv 0.9.4

# 테스트: 프록시 경유 패키지 검색
uv pip search numpy
```

오류 없이 결과가 출력되면 프록시+SSL 설정이 정상입니다.

---

## 6. 가상환경 생성 및 패키지 설치

### 6.1 가상환경이란?

프로젝트마다 독립된 Python 환경을 만들어, 패키지 버전 충돌을 방지하는 기능입니다. 반드시 프로젝트별로 가상환경을 생성합니다.

### 6.2 UV로 가상환경 생성

```powershell
# 프로젝트 폴더로 이동
cd C:\Users\<사번>\battery\python\BDT_dev

# 가상환경 생성 (.venv 폴더가 생성됨)
uv venv

# 가상환경 활성화
.\.venv\Scripts\activate

# 활성화 확인 — 프롬프트 앞에 (.venv) 표시됨
# (.venv) PS C:\Users\...>
```

### 6.3 패키지 설치

```powershell
# requirements.txt가 있는 경우
uv pip install -r requirements.txt

# 개별 패키지 설치 예시
uv pip install pandas numpy matplotlib PyQt6
```

### 6.4 VSCode에서 가상환경 인터프리터 선택

1. VSCode에서 프로젝트 폴더 열기 (`File → Open Folder`)
2. `Ctrl + Shift + P` → `Python: Select Interpreter` 검색
3. 목록에서 `.venv` 경로의 Python 선택
   - 예: `Python 3.12.8 ('.venv': venv) .\.venv\Scripts\python.exe`
4. 이후 터미널을 열면 자동으로 가상환경이 활성화됩니다

---

## 7. VSCode 확장 프로그램 설정

### 7.1 필수 확장 프로그램

VSCode 좌측 사이드바의 확장 아이콘(☐) 클릭 후 검색하여 설치합니다.

| 확장 프로그램 | ID | 용도 |
|-------------|-----|------|
| **Python** | `ms-python.python` | Python 언어 지원 (필수) |
| **Pylance** | `ms-python.vscode-pylance` | 고급 코드 분석, 자동완성 |
| **Python Debugger** | `ms-python.debugpy` | 디버깅 지원 |

### 7.2 권장 확장 프로그램

| 확장 프로그램 | ID | 용도 |
|-------------|-----|------|
| GitLens | `eamodio.gitlens` | Git 이력 시각화 |
| Git Graph | `mhutchie.git-graph` | Git 브랜치 그래프 |
| Code Runner | `formulahendry.code-runner` | 빠른 코드 실행 |
| indent-rainbow | `oderwat.indent-rainbow` | 들여쓰기 시각화 |
| Error Lens | `usernamehw.errorlens` | 인라인 에러 표시 |

### 7.3 Code Runner 가상환경 연동 설정

Code Runner는 기본적으로 **전역 Python**을 사용합니다. 가상환경의 Python을 사용하려면 설정을 변경해야 합니다.

1. `Ctrl + ,` (설정 열기)
2. 검색창에 `code-runner.executorMap` 입력
3. `Edit in settings.json` 클릭
4. `python` 항목을 아래와 같이 수정:

```json
"code-runner.executorMap": {
    "python": "$pythonPath -u $fullFileName"
}
```

> **왜 이렇게 바꾸나요?**
> 기본값 `"python -u"`는 시스템 전역 Python을 호출합니다.
> `$pythonPath`는 VSCode에서 현재 선택된 인터프리터(가상환경)의 경로를 자동으로 참조합니다.

---

## 8. Python 디버깅 설정

### 8.1 launch.json 생성

1. VSCode에서 `Ctrl + Shift + D` (디버그 패널 열기)
2. `create a launch.json file` 클릭
3. `Python Debugger` 선택 → `Python File` 선택

### 8.2 라이브러리 내부 디버깅 활성화

기본 설정에서는 내가 작성한 코드만 디버깅됩니다. 외부 라이브러리(pandas, PyQt6 등) 내부까지 들어가서 확인하려면 아래 옵션을 추가합니다.

`.vscode/launch.json` 파일을 열고 `"justMyCode": false`를 추가합니다.

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python Debugger: Current File",
            "type": "debugpy",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": false
        }
    ]
}
```

> **`justMyCode`란?**
> - `true` (기본값): 내 코드에서만 멈춤. 라이브러리 호출은 건너뜀
> - `false`: 라이브러리 내부 코드까지 디버깅 가능. 오류 원인이 라이브러리 쪽에 있을 때 유용

---

## 9. Git 설치 및 프록시 설정

### 9.1 Git 설치

1. 다운로드 URL: https://git-scm.com/download/win
2. 설치 시 아래 옵션 확인:
   - **Default editor**: `Use Visual Studio Code as Git's default editor` 선택
   - **PATH environment**: `Git from the command line and also from 3rd-party software` 선택 (기본값)
   - **HTTPS transport backend**: `Use the native Windows Secure Channel library` 선택
   - **Line ending conversions**: `Checkout as-is, commit as-is` 선택 (Windows/Linux 혼합 환경 권장)
   - 나머지는 기본값 유지

### 9.2 Git 초기 설정

설치 후 PowerShell에서 사용자 정보를 등록합니다.

```powershell
# 사용자 이름 설정 (커밋 기록에 표시됨)
git config --global user.name "홍길동"

# 이메일 설정 (Knox 이메일 사용)
git config --global user.email "hong.gildong@samsung.com"

# 기본 브랜치 이름 설정
git config --global init.defaultBranch main

# 한글 파일명 표시 설정 (한글 깨짐 방지)
git config --global core.quotepath false
```

### 9.3 Git 프록시 설정

```powershell
# HTTP/HTTPS 프록시 설정
git config --global http.proxy http://168.219.61.252:8080
git config --global https.proxy http://168.219.61.252:8080
```

### 9.4 Git SSL 인증서 설정

```powershell
# SSL 인증서 경로 설정
git config --global http.sslCAInfo "C:\Users\<사번>\certs\DigitalCity.crt"
```

### 9.5 사내 도메인 프록시 예외 설정

사내 Git 서버(Bitbucket 등)에 접근할 때는 프록시를 경유하지 않아야 합니다.

```powershell
# 사내 서버는 프록시 없이 직접 접속
git config --global http.https://github.sec.samsung.net.proxy ""
```

> [!tip] 사내 Git 서버 주소가 다른 경우
> 본인 팀에서 사용하는 Git 서버 URL로 교체합니다.
> 예: `http.https://bitbucket.sec.samsung.net.proxy`

### 9.6 Git 설정 확인

```powershell
# 전체 설정 확인
git config --global --list

# 주요 항목 확인
git config --global user.name
git config --global http.proxy
git config --global http.sslCAInfo
```

### 9.7 Git 동작 확인

```powershell
# 외부 저장소 클론 테스트 (프록시 경유)
git clone https://github.com/pybamm-team/PyBaMM.git --depth 1 test_clone

# 성공하면 test_clone 폴더 삭제
Remove-Item -Recurse -Force test_clone
```

---

## 10. 설치 확인 체크리스트

모든 설치가 완료되면 아래 체크리스트로 최종 확인합니다.

```powershell
# ---- 아래 명령어를 순서대로 실행하여 모두 정상 출력되는지 확인 ----

# 1. Python 버전
python --version

# 2. pip 버전
pip --version

# 3. UV 버전
uv --version

# 4. Git 버전
git --version

# 5. 프록시 환경변수
$env:HTTP_PROXY
$env:HTTPS_PROXY
$env:SSL_CERT_FILE

# 6. Git 프록시 설정
git config --global http.proxy

# 7. 패키지 설치 테스트 (프록시 경유 확인)
uv pip install --dry-run requests

# 8. Git 연결 테스트
git ls-remote https://github.com/python/cpython.git HEAD
```

**모든 항목이 오류 없이 출력되면 환경 세팅 완료입니다.**

| # | 확인 항목 | 예상 결과 | 확인 |
|---|----------|----------|------|
| 1 | Python 버전 | `Python 3.12.x` | ☐ |
| 2 | pip 버전 | `pip 24.x.x` | ☐ |
| 3 | UV 버전 | `uv 0.x.x` | ☐ |
| 4 | Git 버전 | `git version 2.x.x` | ☐ |
| 5 | 프록시 환경변수 3개 | 모두 값 출력 | ☐ |
| 6 | Git 프록시 | `http://168.219.61.252:8080` | ☐ |
| 7 | UV 패키지 설치 | 에러 없음 | ☐ |
| 8 | Git 원격 연결 | 해시값 출력 | ☐ |

---

## 부록 A. 트러블슈팅

### A.1 `pip install` 시 SSL 인증서 오류

```
ERROR: Could not fetch URL ... SSL: CERTIFICATE_VERIFY_FAILED
```

**원인**: SSL_CERT_FILE 환경변수가 설정되지 않았거나, 인증서 파일 경로가 잘못됨

**해결**:
1. 인증서 파일이 실제로 존재하는지 확인:
   ```powershell
   Test-Path $env:SSL_CERT_FILE
   # True가 출력되어야 함
   ```
2. False인 경우 → [[#4.2 Windows 시스템 환경변수 등록 (영구 설정)]] 재설정
3. 임시 우회 (권장하지 않음):
   ```powershell
   pip install <패키지명> --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org
   ```

### A.2 `git clone` 시 프록시 오류

```
fatal: unable to access '...': Could not resolve proxy: ...
```

**해결**:
```powershell
# 프록시 설정 확인
git config --global http.proxy
# 비어있으면 재설정
git config --global http.proxy http://168.219.61.252:8080
```

### A.3 `git clone` 시 SSL 오류

```
fatal: unable to access '...': SSL certificate problem
```

**해결**:
```powershell
# SSL 인증서 경로 확인
git config --global http.sslCAInfo
# 비어있거나 잘못되었으면 재설정
git config --global http.sslCAInfo "C:\Users\<사번>\certs\DigitalCity.crt"
```

### A.4 VSCode 터미널에서 가상환경 활성화 실패

```
.\.venv\Scripts\activate : 이 시스템에서 스크립트를 실행할 수 없으므로...
```

**원인**: PowerShell 실행 정책이 `Restricted`로 설정됨

**해결** (관리자 PowerShell에서 실행):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### A.5 `python` 명령어가 Microsoft Store를 여는 경우

Windows 10/11에서 `python` 입력 시 Microsoft Store가 열리는 경우가 있습니다.

**해결**:
1. `Win + I` → `앱` → `앱 및 기능` → `앱 실행 별칭`
2. `python.exe` 및 `python3.exe` 항목을 **끔**으로 변경

### A.6 UV가 프록시를 인식하지 못하는 경우

**해결**: 환경변수가 등록되었는지 확인 후, 터미널을 **완전히 닫고 다시 열기**
(settings.json 변경 후에도 기존 터미널은 이전 환경변수를 유지합니다)

---

## 부록 B. 참고 링크

| 자료 | 링크 |
|------|------|
| 사내 Python 프록시 가이드 (M-Wiki) | https://confluence-mx.sec.samsung.net/spaces/APPTEAM/pages/1802301653 |
| Python 공식 다운로드 | https://www.python.org/downloads/ |
| VSCode 공식 다운로드 | https://code.visualstudio.com/ |
| Git 공식 다운로드 | https://git-scm.com/download/win |
| UV 공식 문서 | https://docs.astral.sh/uv/ |

---

> **문서 이력**
> - 2026-04-14: 초판 작성 (Python + VSCode + 프록시/SSL + Git)
