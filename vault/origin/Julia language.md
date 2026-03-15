# 1. Julia language
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
