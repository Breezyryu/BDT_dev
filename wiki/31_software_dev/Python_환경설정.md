---
title: "Python 개발환경 (Proxy 사내)"
tags:
  - Development
  - Python
  - 환경설정
  - 프록시
type: development
status: active
related:
  - "[[Julia_language]]"
  - "[[Cuda_설정]]"
  - "[[Latex_설치]]"
  - "[[오피스_세팅]]"
created: 2025-12-15
updated: 2026-03-17
source: "origin/Python 환경 설정.md"
---

# Proxy 설정
## 사내 환경에 맞는 UV 버전
- 사내에서는 프록시 이슈로 UV 버전은 0.5.8 이하 버전으로 사용해야 함
### Package 설치 시, proxy해결
- https://confluence-mx.sec.samsung.net/spaces/APPTEAM/pages/1802301653/python+%ED%8C%A8%ED%82%A4%EC%A7%80+%EC%84%A4%EC%B9%98%EC%8B%9C+proxy%ED%95%B4%EA%B2%B0
- ![[python 패키지 설치시 proxy해결 - Application 개발팀 - M-Wiki.html]]
## UV 명령어
### Proxy 설정(사내)
*CMD와 Powershell은 명령어가 다름*
#### VScode 관리자 권한 실행
- VSCODE의 경우, 관리자 권한 실행 필요


### Console 창 입력
#### **CMD**
- CMD 창(**==관리자권한==**)에서 명령어 실행
```
set HTTP_PROXY=http://168.219.61.252:8080
set HTTPS_PROXY=https://168.219.61.252:8080
set SSL_CERT_FILE=C:\Users\st.ryu\Desktop\DigitalCity.crt
```
- 주소 확인
```
echo %HTTP_PROXY%
echo %HTTPS_PROXY%
echo %SSL_CERT_FILE%
```
#### **Powershell**
- 설정
```
	  $env:HTTP_PROXY="http://168.219.61.252:8080"
	  $env:HTTPS_PROXY="http://168.219.61.252:8080"
	  $env:SSL_CERT_FILE="C:\Users\st.ryu\Desktop\DigitalCity.crt"
```
- 설정 확인
```
$env:HTTP_PROXY
$env:HTTPS_PROXY
$env:SSL_CERT_FILE
```
#### setting.json (VSCODE)
- console 창 명령어 입력은 반복 작업으로 불편함
- default 값으로 setting.json에 아래 추가
```
 "terminal.integrated.env.windows": {
        "HTTP_PROXY": "http://168.219.61.252:8080",
        "HTTPS_PROXY": "http://168.219.61.252:8080",
        "SSL_CERT_FILE": "C:\\Users\\st.ryu\\Desktop\\DigitalCity.crt"

    },
```

```
uv pip install -r requirements.txt
```

- (25년10월20일 기준) uv 0.9.4 버전 실행 확인
	- 사내wiki는 0.5.8 이하 버전 사용이라고 기재 (but, 윗 버전도 사용가능!)
## 파이썬 사내 인증 관련 (Now talk)![[Pasted image 20251204083428.png]]

#### Code Runner (extention)

Code runner extention을 설치하여 사용할 경우
- 가상환경이 아닌 전역환경 실행으로 기본 설정되어 있음
- setting.json 변경이 필요함
	- 설정(Ctrl + ,)으로 이동
	- code-runner.executorMap 검색
	- Edit in setting.json 클릭
	- "python": "python -u" 부분을 "python": "$pythonPath -u $fullFileName",로 변경합니다.
		(이렇게 하면 VS Code에서 선택한 인터프리터 경로를 따라갑니다.)
```
"python": "$pythonPath -u $fullFileName",
```

# Python 디버깅 설정
## launch.json
디버깅 시 라이브러리 접근 가능 옵션
아래 추가
```
"justMyCode": false
```



# IDE

## Pycharm
	- IDE: Pycharm
	- window 11 환경

라이선스 설정법은 아래 2가지 있음
필요한 방법으로 설정

### 1. Community edition 이용

> [!summary] Community edition 정책
> IntelliJ IDEA Community Edition 및 PyCharm Community Edition IDE(Community IDE) 모두 상업용 및 소유권이 있는 소프트웨어 개발에 사용할 수 있습니다.
>
>
>
> 유일한 예외는 파생 제품을 제작 또는 Community IDE 상업화와 관련된 경우입니다.
>
>
>
> JetBrains Community IDE의 표준 배포에는 일부 JetBrains 소유의 플러그인(전체 목록)이 번들로 포함되므로 다른 JetBrains 제품과 별도의 설정없이 통합할 수 있습니다. 파생 제품을 만들거나 Community IDE를 상용화하는 경우, 해당 JetBrains 소유의 플러그인 라이선스 정보를 확인하세요.
>
> IntelliJ IDEA Community Edition 및 PyCharm Community Edition 코드베이스와 번들 플러그인의 대부분은 오픈 소스이며 Apache 2.0에 따라 라이선스가 부여됩니다. 라이선스 세부 정보는 여기에서 확인할 수 있습니다.
>
> 전체 IntelliJ IDEA Community Edition 및 PyCharm Community Edition IDE 사용 약관도 참조해 주세요.
>
>
> 궁금한 점이 있으면 legal@jetbrains.com으로 문의하세요.


### 2. Ultimate edition 이용

Pycharm, IntelliJ 등 Jetbrain 사의 모든 개발 툴 인증 방식 동일
사내에서 라이선스를 구매해둠

> [!note] 라이선스 설정
> 1. JetBrains 프로그램 open -> 상단의 메뉴바 중 Help 클릭 -> Register클릭
> 2. License server 클릭 후 license server address 입력 http://10.91.226.7:8080
> 3. Activation클릭 후 register 완료 여부 확인



### 3.1. Proxy 설정

#### 1.1 Manual
1. IntelliJ / Pycharm 중 하나를 실행시켜 JetAccount 로그인은 진행하면, 두 IDE를 활성화시킬 수 있음.
2. IDE 좌측 하단 proxy 설정
    1. Setting로 들어가서 Appearance & Behavior  > System Settings > HTTP Proxy 로 들어간 후 MANUAL PROXY CONFIGURATION에
    2. HOST NAME : 168.219.61.252
    3. PORT NUMBER : 8080
    4. No proxy for : *.[samsung.net](http://samsung.net/), localhost, 127.0.0.1, 10.*.*.*, 165.213.*.*, 168.219._._

#### 1.2. Automatic <span style="background:#d3f8b6">(작동확인)</span>
PyCharm > Settings (Ctrl + Alt + s) > HTTP Proxy > Auto-detect proxy settings > Automatic proxy configuration URL 에 아래 내용 넣고 Check connection 버튼으로 확인
[http://168.219.61.251:8088/samsungcs.pac](http://168.219.61.251:8088/samsungcs.pac)

### 3.2 SSL 세팅
	 UV - Proxy, SSL 설정이 필요
- 참고: [[Python 환경 설정#Console 창 입력]]

## 2. Visual studio
### **Express 설치하기**

- 아래 링크의 페이지 제일  **하단** 에 있는  **"Visual Studio Express를 계속 사용하시겠습니까?"**  에 표기되는  **Express 버전**  중에서 선택
- [https://visualstudio.microsoft.com/ko/vs/express/](https://visualstudio.microsoft.com/ko/vs/express/)

### **Professional 설치하기**

- [IT4U](http://it4u.sec.samsung.net/itvoc/jsp/new/common/menu/frame.jsp)  에서 VISUAL STUDIO WITH MSDN 신청 필요

## 3. Powershell
### 1. winget
- `winget` 명령줄 도구는 기본적으로 **앱 설치 관리자**로 Windows 11 및 최신 버전의 Windows 10에 번들로 제공됩니다.

- 윈도우 설치 된 프로그램들 업데이트가 powershell 창에서 가능해진다.
```
winget upgrade --all
```
	- 일부 프로그램은 관리자 권한 필요
	-
---

# Julia lang

1. Julia language
- vscode 활용
- Pluto : jupyterNotebook 같은 플랫폼
- 프록시 및 환경변수 설정 필요해보임
## Proxy 설정
startup.jl 파일에 다음 추가
```
# 프록시 설정

ENV["HTTP_PROXY"] = "http://168.219.61.252:8080"

ENV["HTTPS_PROXY"] = "http://168.219.61.252:8080"

ENV["NO_PROXY"] = "localhost,127.0.0.1, 168.219.61.*, 10.*.*.*, 165.213.*.*, 168.219.*.*, sec.samsung.net"



# SSL 인증서 설정

cert_file = raw"D:\\DigitalCity.crt"



if isfile(cert_file)

    ENV["SSL_CERT_FILE"] = cert_file

end



println("✓ Julia startup: 프록시 설정 적용됨 (168.219.61.252:8080)")
```

## Pluto
- 설치 가능하나 vscode webview 기능에 문제가 있음
- 방화벽 문제로 github 접근이 안되는 문제
- 직접 다운로드하여 설정해야 함
### GitHub에서 다운로드
	브라우저에서 다음 링크로 이동하여 ZIP 파일 다운로드:
	**Pluto 일반 버전:**
- URL: [https://github.com/fonsp/Pluto.jl/archive/refs/heads/main.zip](https://github.com/fonsp/Pluto.jl/archive/refs/heads/main.zip)
- 또는 [https://github.com/fonsp/Pluto.jl](https://github.com/fonsp/Pluto.jl) 접속 → Code → Download ZIP
	**Pluto vscode-webview-proxy 버전:**
- URL: [https://github.com/fonsp/Pluto.jl/archive/refs/heads/vscode-webview-proxy.zip](https://github.com/fonsp/Pluto.jl/archive/refs/heads/vscode-webview-proxy.zip)
- 또는 [https://github.com/fonsp/Pluto.jl/tree/vscode-webview-proxy](https://github.com/fonsp/Pluto.jl/tree/vscode-webview-proxy) 접속 → Code → Download ZIP
	2단계: 압축 해제
		다운로드한 ZIP 파일을 적절한 위치에 압축 해제:
```
# Julia 패키지 모드로 진입 (]키)
pkg> dev "C:/Users/Ryu/Downloads/Pluto.jl-main"
```
