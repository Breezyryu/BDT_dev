"""
사내 오프라인 배포용 — 모델 사전 다운로드 스크립트.
setup.bat 에서 1회 호출해 HF / modelscope 캐시를 로컬에 채운 뒤,
HF_HUB_OFFLINE=1 로 재현 가능하게 한다.

HF 가 차단된 환경이면 사외 PC 에서 이 스크립트 실행 후
%USERPROFILE%\\.cache\\huggingface 폴더를 사내 PC 로 복사.
"""
from __future__ import annotations
import os
import subprocess
import sys


def main():
    print("[prefetch] 모델 다운로드 시작 (최초 1회)")

    # MinerU (layout + tableformer + PP-OCRv4 ko)
    try:
        print("[prefetch] MinerU (layout + table + OCR) ...")
        # mineru CLI 를 dummy 입력으로 한 번 호출하면 모델 자동 다운로드됨
        # 또는 python API 로 직접 모델 init
        from mineru.utils.model_utils import get_model_from_hf_or_modelscope  # type: ignore
        # 버전별 내부 API 가 다를 수 있음 → CLI 방식 폴백
        raise ImportError("fall back to CLI-based prefetch")
    except Exception:
        try:
            # CLI 로 empty-run (dummy file 없이 --help 만 호출해도 일부 모델은 초기화)
            subprocess.run(
                ["mineru", "--help"],
                check=False, capture_output=True, timeout=60,
            )
            print("[prefetch]   mineru CLI ready (모델은 첫 변환 시 다운로드)")
        except FileNotFoundError:
            print("[prefetch]   mineru CLI not found", file=sys.stderr)

    # Docling layout + TableFormer
    try:
        print("[prefetch] docling (layout + tableformer) ...")
        from docling.document_converter import DocumentConverter

        DocumentConverter()
        print("[prefetch]   docling OK")
    except Exception as e:
        print(f"[prefetch]   docling FAIL: {e}", file=sys.stderr)

    # EasyOCR ko+en (docling 내부에서 사용)
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
