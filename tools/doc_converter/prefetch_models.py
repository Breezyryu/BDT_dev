"""
사내 오프라인 배포용 — 모델 사전 다운로드 스크립트.
setup.bat 에서 1회 호출해 HF 캐시를 로컬에 채운 뒤, HF_HUB_OFFLINE=1 로 재현 가능하게 한다.

HF 가 차단된 환경이면 사외 PC 에서 이 스크립트 실행 후
  %USERPROFILE%\.cache\huggingface  폴더를 사내 PC 로 복사.
"""
from __future__ import annotations
import os
import sys


def main():
    print("[prefetch] 모델 다운로드 시작 (최초 1회)")

    # Surya (marker-pdf OCR/layout/detection)
    try:
        print("[prefetch] surya-ocr / layout / recognition ...")
        from marker.models import create_model_dict

        create_model_dict()
        print("[prefetch]   surya OK")
    except Exception as e:
        print(f"[prefetch]   surya FAIL: {e}", file=sys.stderr)

    # Docling layout + TableFormer
    try:
        print("[prefetch] docling (layout + tableformer) ...")
        from docling.document_converter import DocumentConverter

        DocumentConverter()
        print("[prefetch]   docling OK")
    except Exception as e:
        print(f"[prefetch]   docling FAIL: {e}", file=sys.stderr)

    # EasyOCR ko+en
    try:
        print("[prefetch] easyocr ko+en ...")
        import easyocr

        easyocr.Reader(["ko", "en"], gpu=False, verbose=False)
        print("[prefetch]   easyocr OK")
    except Exception as e:
        print(f"[prefetch]   easyocr FAIL: {e}", file=sys.stderr)

    hf_home = os.environ.get("HF_HOME") or os.path.expanduser("~/.cache/huggingface")
    print(f"\n[prefetch] 완료. HF 캐시: {hf_home}")
    print("[prefetch] 오프라인 강제하려면 HF_HUB_OFFLINE=1 환경변수 설정")


if __name__ == "__main__":
    main()
