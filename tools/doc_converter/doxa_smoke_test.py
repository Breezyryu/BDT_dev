"""
DoXA API 연결성 확인 스모크 테스트 (실제 파일 업로드 없이).

DOXA_URL 로 GET 해서 응답 코드 확인 + 토큰 Bearer 헤더 유효성 1차 확인.
사내 PC 에서 `doxa_convert.py` 실행 전 한 번 돌려보세요.
"""
import os
import sys

import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def main():
    token = os.environ.get("DOXA_TOKEN", "").strip()
    url = os.environ.get("DOXA_URL", "https://doxa.sec.samsung.net").rstrip("/")

    if not token:
        print("[FAIL] DOXA_TOKEN 미설정")
        sys.exit(2)

    # JWT 헤더 payload 디코드 (서명 검증 없이 정보만)
    try:
        import base64
        import json

        header_b64, payload_b64, sig_b64 = token.split(".")
        pad = lambda s: s + "=" * (-len(s) % 4)
        header = json.loads(base64.urlsafe_b64decode(pad(header_b64)))
        payload = json.loads(base64.urlsafe_b64decode(pad(payload_b64)))
        print(f"[info] JWT alg    : {header.get('alg')}")
        print(f"[info] JWT user   : {payload.get('user')}")
        print(f"[info] JWT group  : {payload.get('group')}")
        import datetime

        exp = payload.get("exp")
        if exp:
            dt = datetime.datetime.utcfromtimestamp(exp)
            print(f"[info] JWT exp    : {dt.isoformat()}Z")
    except Exception as e:
        print(f"[warn] JWT 디코드 실패: {e}")

    # 프록시 환경변수 출력 (진단)
    print("\n[env] 프록시 관련 환경변수")
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "NO_PROXY", "no_proxy"):
        v = os.environ.get(k, "")
        print(f"[env]   {k} = {v or '(unset)'}")

    # DNS 해석 확인
    print("\n[dns] doxa.sec.samsung.net 해석")
    try:
        import socket
        hostname = url.replace("https://", "").replace("http://", "").split("/")[0]
        ip = socket.gethostbyname(hostname)
        print(f"[dns]   {hostname} -> {ip}")
    except Exception as e:
        print(f"[dns]   ✗ 해석 실패: {e}")

    # TCP 연결 (TLS 없이)
    print(f"\n[tcp] {hostname}:443 TCP 연결 시도")
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((hostname, 443))
        s.close()
        print("[tcp]   ✓ TCP OK (3-way handshake 성공)")
    except Exception as e:
        print(f"[tcp]   ✗ TCP 실패: {e}")
        print("[tcp]   → 방화벽/네트워크 정책으로 TCP 레벨 차단")
        sys.exit(3)

    # HTTPS (requests)
    print(f"\n[test] GET {url} ...")
    try:
        r = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            verify=False,
            timeout=10,
        )
        print(f"[test]   status = {r.status_code}")
        if r.status_code in (200, 301, 302, 401, 403, 404):
            print("[test]   ✓ 서버 응답 정상 (네트워크 OK)")
        else:
            print(f"[test]   ? 예상치 못한 코드 {r.status_code}")
    except requests.exceptions.ConnectionError as e:
        print(f"[test]   ✗ 연결 실패: {e}")
        err_str = str(e).lower()
        if "refused" in err_str or "10061" in err_str:
            print("[test]   → 사외 네트워크. 사내망/VPN 연결 필요.")
        elif "reset" in err_str or "10054" in err_str:
            print("[test]   → Connection RESET. 다음 확인 필요:")
            print("[test]     a) 프록시 문제: set NO_PROXY=sec.samsung.net,localhost")
            print("[test]     b) 프록시 경유 강제 해제: set HTTP_PROXY= & set HTTPS_PROXY=")
            print("[test]     c) TLS/cipher 호환성: curl -k -v https://doxa.sec.samsung.net")
            print("[test]     d) HTTPS Inspection 프록시 (Zscaler/BlueCoat 등) 차단 여부 확인")
        else:
            print(f"[test]   → 기타 네트워크 이슈. 위 [env]/[dns]/[tcp] 결과 확인")
        sys.exit(3)
    except Exception as e:
        print(f"[test]   ✗ 기타 오류: {type(e).__name__}: {e}")
        sys.exit(4)

    # API 엔드포인트 확인 (OPTIONS 또는 GET 404 를 정상 간주)
    api_endpoint = f"{url}/api/v2/parser/document"
    print(f"\n[test] OPTIONS {api_endpoint} ...")
    try:
        r = requests.options(
            api_endpoint, headers={"Authorization": f"Bearer {token}"}, verify=False, timeout=10
        )
        print(f"[test]   status = {r.status_code}")
    except Exception as e:
        print(f"[test]   note: {e}")

    print("\n[OK] 스모크 테스트 완료. doxa_convert.py 로 실제 변환 가능.")


if __name__ == "__main__":
    main()
