"""
DoXA 어댑터 — 사내 DoXA API 를 통해 문서를 Markdown + 이미지로 변환.

요건:
- 사내 네트워크 (doxa.sec.samsung.net 접근 가능)
- `doxa-sdk` 설치 (사내 GitHub 에서 pip install git+https://github.sec.samsung.net/...)
- 환경변수 `DOXA_TOKEN` 설정 (AI Asset Hub 발급 토큰)
- 선택: 환경변수 `DOXA_URL` (기본 https://doxa.sec.samsung.net)
- 선택: 환경변수 `IPAAS_TOKEN` (iPaaS 게이트웨이 경유 시)

사용법:
    python doxa_convert.py <source_dir> [output_dir]
    python doxa_convert.py <single_file> [output_dir]

출력:
    <output_dir>/<stem>/<stem>.md
    <output_dir>/<stem>/image/*     (본문 이미지)
    <output_dir>/<stem>/page_image/* (페이지 스냅샷)
    <output_dir>/<stem>/<stem>.json  (구조화 데이터)
"""
from __future__ import annotations
import argparse
import io
import os
import shutil
import sys
import traceback
import urllib3
import zipfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# DoXA SDK 는 verify=False 호출 → InsecureRequestWarning 억제
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SUPPORTED_EXTS = {".pdf", ".pptx", ".docx", ".xlsx", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}


def _safe_stem(p: Path) -> str:
    name = p.name
    for ext in (".mht.eml", ".xlsx.xlsx", ".xlsx.pdf"):
        if name.lower().endswith(ext):
            return name[: -len(ext)]
    return p.stem


def _get_parser():
    from doxa.parser import DoxaParser

    token = os.environ.get("DOXA_TOKEN", "").strip()
    if not token:
        print(
            "[ERROR] DOXA_TOKEN 환경변수가 설정되지 않았습니다.\n"
            "  사내 AI Asset Hub (https://aia.sec.samsung.net) 에서 토큰 발급 후:\n"
            "    Windows:  set DOXA_TOKEN=<발급토큰>\n"
            "    Bash   :  export DOXA_TOKEN=<발급토큰>",
            file=sys.stderr,
        )
        sys.exit(2)

    url = os.environ.get("DOXA_URL", "https://doxa.sec.samsung.net")
    ipaas_token = os.environ.get("IPAAS_TOKEN", "")
    return DoxaParser(token=token, doxa_url=url, ipaas_token=ipaas_token)


def _process_response(response, src: Path, stem_out: Path) -> str:
    """응답 타입(JSON / ZIP / text)에 따라 stem_out 아래에 전개."""
    import json

    stem_out.mkdir(parents=True, exist_ok=True)
    content_type = response.headers.get("content-type", "").lower()

    if "application/zip" in content_type:
        # ZIP → 전개
        z = zipfile.ZipFile(io.BytesIO(response.content))
        z.extractall(stem_out)
        z.close()
        md_files = list(stem_out.rglob("*.md"))
        size = sum(f.stat().st_size for f in md_files)
        return f"DoXA ZIP OK (md_files={len(md_files)}, md_total={size:,}B, names={len(z.namelist())} entries)"

    if "application/json" in content_type:
        out = stem_out / f"{_safe_stem(src)}.json"
        out.write_text(
            json.dumps(response.json(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return f"DoXA JSON OK ({out.stat().st_size:,}B)"

    # text/plain
    out = stem_out / f"{_safe_stem(src)}.txt"
    out.write_text(response.text, encoding="utf-8")
    return f"DoXA TEXT OK ({out.stat().st_size:,}B)"


def convert_one(parser, src: Path, out_root: Path, response_format: str = "standard") -> tuple[bool, str]:
    from doxa.parser.params import (
        DocumentRequestParam,
        OcrLangOption,
        OCRModuleOption,
        ResponseFormatOption,
    )

    if src.suffix.lower() not in SUPPORTED_EXTS:
        return False, f"SKIP (unsupported: {src.suffix})"

    stem = _safe_stem(src)
    stem_out = out_root / stem

    params = DocumentRequestParam(
        response_format=ResponseFormatOption(response_format),
        ocr_lang=OcrLangOption.KOREAN,
        ocr_module=OCRModuleOption.Hybrid,
        recognize_table=True,
        indent=True,
        escape=True,
    )

    try:
        response = parser.parse_document(
            input_path=str(src), params=params, timeout=3600
        )
        msg = _process_response(response, src, stem_out)
        return True, msg
    except Exception as e:
        return False, f"DoXA FAIL: {type(e).__name__}: {e}"


def iter_sources(source: Path) -> list[Path]:
    if source.is_file():
        return [source]
    if source.is_dir():
        return sorted(f for f in source.iterdir() if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS)
    return []


def main():
    ap = argparse.ArgumentParser(description="DoXA 기반 문서 → Markdown 변환")
    ap.add_argument("source", type=Path, help="변환할 파일 또는 디렉토리")
    ap.add_argument("output", type=Path, nargs="?", default=None, help="출력 디렉토리 (기본: <source>_doxa)")
    ap.add_argument(
        "--format",
        default="standard",
        choices=["standard", "json_only", "markdown_only", "page_image_only", "json_with_image", "debug_info"],
        help="DoXA 응답 포맷 (기본: standard = MD + json + page image)",
    )
    args = ap.parse_args()

    src = args.source.resolve()
    if args.output:
        out = args.output.resolve()
    else:
        base = src if src.is_dir() else src.parent
        out = base.parent / f"{base.name}_doxa"
    out.mkdir(parents=True, exist_ok=True)

    parser = _get_parser()

    files = iter_sources(src)
    print(f"Source : {src}")
    print(f"Output : {out}")
    print(f"Files  : {len(files)}")
    print(f"Format : {args.format}\n")

    results = []
    for i, f in enumerate(files, 1):
        print(f"[{i:02d}/{len(files)}] {f.name}")
        ok, msg = convert_one(parser, f, out, args.format)
        print(f"  -> {msg}")
        results.append((f.name, ok, msg))

    ok_cnt = sum(1 for _, ok, _ in results if ok)
    print(f"\nDONE: {ok_cnt}/{len(results)}")

    report = out / "_doxa_report.md"
    lines = [
        "# DoXA Conversion Report\n",
        f"- Source: `{src}`",
        f"- Output: `{out}`",
        f"- Success: {ok_cnt}/{len(results)}\n",
        "| # | File | Status | Detail |",
        "|---|------|--------|--------|",
    ]
    for i, (n, ok, m) in enumerate(results, 1):
        lines.append(f"| {i} | `{n}` | {'OK' if ok else 'FAIL'} | {m} |")
    report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {report}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[Interrupted]")
        sys.exit(130)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
