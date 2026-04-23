"""
DoXA API 연결성 스모크 테스트 (실제 파일 업로드 없이).

확인 항목:
- JWT 토큰 구조/만료일
- 프록시 환경변수
- DNS 해석
- TCP/TLS 연결 (3가지 URL 자동 시도: 직접 / iPaaS 사내 / iPaaS 외부)
- 각 엔드포인트의 HTTP 응답 코드

참고: parser_tutorial.ipynb / parser_ipaas_tutorial.ipynb
"""
import base64
import json
import os
import socket
import ssl
import sys
from datetime import datetime

import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


CANDIDATES = [
    ("direct", "https://doxa.sec.samsung.net"),
    ("ipaas-internal", "https://ipaas-sca.sec.samsung.net/sec/kr/doxa_parser_document_v2/1.0"),
    ("ipaas-external", "https://sca.ipaas.samsung.com/sec/kr/doxa_parser_document_v2/1.0"),
]


def decode_jwt(token: str) -> dict:
    try:
        header_b64, payload_b64, _ = token.split(".")
        pad = lambda s: s + "=" * (-len(s) % 4)
        return {
            "header": json.loads(base64.urlsafe_b64decode(pad(header_b64))),
            "payload": json.loads(base64.urlsafe_b64decode(pad(payload_b64))),
        }
    except Exception as e:
        return {"error": str(e)}


def show_env_proxies():
    print("\n[env] 프록시 환경변수")
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "NO_PROXY", "no_proxy"):
        v = os.environ.get(k, "")
        print(f"[env]   {k:12s} = {v or '(unset)'}")


def check_dns(host: str) -> str | None:
    try:
        ip = socket.gethostbyname(host)
        print(f"[dns]   {host:45s} -> {ip}")
        return ip
    except Exception as e:
        print(f"[dns]   {host:45s} -> FAIL: {e}")
        return None


def check_tcp(host: str, port: int = 443, timeout: float = 5.0) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.close()
        print(f"[tcp]   {host}:{port} TCP OK")
        return True
    except Exception as e:
        print(f"[tcp]   {host}:{port} FAIL: {e}")
        return False


def check_tls(host: str, port: int = 443, timeout: float = 5.0) -> str | None:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                tls_ver = ssock.version()
                cipher = ssock.cipher()
                print(f"[tls]   {host}:{port} handshake OK: {tls_ver}, cipher={cipher[0] if cipher else 'n/a'}")
                return tls_ver
    except Exception as e:
        print(f"[tls]   {host}:{port} FAIL: {type(e).__name__}: {e}")
        return None


def check_http(url: str, token: str, label: str) -> tuple[bool, str]:
    print(f"[http]  [{label}] GET {url}")
    try:
        r = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            verify=False,
            timeout=15,
        )
        msg = f"status={r.status_code}"
        if r.status_code in (200, 301, 302, 401, 403, 404, 405):
            print(f"[http]   ✓ {msg}  (서버 응답 도달)")
            return True, msg
        print(f"[http]   ? {msg}  (예상치 못한 코드)")
        return True, msg
    except requests.exceptions.ConnectionError as e:
        err = str(e)
        print(f"[http]   ✗ ConnectionError: {err[:200]}")
        err_l = err.lower()
        if "reset" in err_l or "10054" in err_l:
            return False, "RESET (중간 프록시/방화벽 차단 가능성)"
        if "refused" in err_l or "10061" in err_l:
            return False, "REFUSED (포트 닫힘)"
        if "timed out" in err_l or "10060" in err_l:
            return False, "TIMEOUT"
        return False, f"ConnectionError"
    except Exception as e:
        print(f"[http]   ✗ {type(e).__name__}: {e}")
        return False, f"{type(e).__name__}"


def main():
    token = os.environ.get("DOXA_TOKEN", "").strip()
    if not token:
        print("[FAIL] DOXA_TOKEN 미설정")
        sys.exit(2)

    # JWT 디코드
    info = decode_jwt(token)
    if "error" in info:
        print(f"[warn] JWT 디코드 실패: {info['error']}")
    else:
        p = info["payload"]
        print(f"[info] JWT alg    : {info['header'].get('alg')}")
        print(f"[info] JWT user   : {p.get('user')}")
        print(f"[info] JWT group  : {p.get('group')}")
        if p.get("exp"):
            print(f"[info] JWT exp    : {datetime.utcfromtimestamp(p['exp']).isoformat()}Z")

    show_env_proxies()

    # URL override (사용자 지정)
    override_url = os.environ.get("DOXA_URL", "").strip().rstrip("/")
    urls_to_try = []
    if override_url:
        urls_to_try.append(("env", override_url))
    urls_to_try.extend(CANDIDATES)

    # 각 URL 에 대해 DNS / TCP / TLS / HTTP 순차 확인
    results = []
    print()
    for label, url in urls_to_try:
        print(f"\n================ [{label}] {url} ================")
        host = url.replace("https://", "").replace("http://", "").split("/")[0]

        dns_ok = check_dns(host) is not None
        if not dns_ok:
            results.append((label, url, False, "DNS 실패"))
            continue

        tcp_ok = check_tcp(host, 443)
        if not tcp_ok:
            results.append((label, url, False, "TCP 실패"))
            continue

        tls_ver = check_tls(host, 443)
        if tls_ver is None:
            results.append((label, url, False, "TLS handshake 실패"))
            continue

        ok, detail = check_http(url, token, label)
        results.append((label, url, ok, detail))

    # 요약
    print("\n\n================ SUMMARY ================")
    any_ok = False
    for label, url, ok, detail in results:
        status = "✓" if ok else "✗"
        print(f"{status} [{label:18s}] {detail}  — {url}")
        if ok:
            any_ok = True

    if any_ok:
        usable = [(l, u) for l, u, ok, _ in results if ok]
        print("\n[OK] 사용 가능 URL 발견. 다음 환경변수로 고정 권장:")
        for l, u in usable[:1]:
            print(f'     set DOXA_URL={u}')
        print("\n     이후 doxa_convert.bat 실행 시 해당 URL 사용됨.")
        sys.exit(0)
    else:
        print("\n[FAIL] 모든 URL 접근 실패. 다음 항목 확인:")
        print("  a) VPN / 사내망 접속 여부")
        print("  b) set NO_PROXY=sec.samsung.net,samsung.com,localhost")
        print("  c) set HTTP_PROXY= / HTTPS_PROXY= 해제")
        print("  d) 방화벽/HTTPS Inspection (Zscaler/BlueCoat) 관리자 문의")
        print("  e) curl -k -v https://<URL> 로 독립 검증")
        sys.exit(3)


if __name__ == "__main__":
    main()
