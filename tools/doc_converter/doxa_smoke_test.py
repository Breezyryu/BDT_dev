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

    # 루트 접속 확인
    print(f"\n[test] GET {url} ...")
    try:
        r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, verify=False, timeout=10)
        print(f"[test]   status = {r.status_code}")
        if r.status_code in (200, 301, 302, 401, 403, 404):
            print("[test]   ✓ 서버 응답 정상 (네트워크 OK)")
        else:
            print(f"[test]   ✗ 예상치 못한 코드")
    except requests.exceptions.ConnectionError as e:
        print(f"[test]   ✗ 연결 실패: {e}")
        print("[test]   → 사외 네트워크일 가능성. 사내 VPN 또는 사내 PC 에서 실행 필요")
        sys.exit(3)
    except Exception as e:
        print(f"[test]   ✗ 기타 오류: {e}")
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
