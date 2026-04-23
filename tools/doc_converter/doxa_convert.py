"""
DoXA 어댑터 — 사내 DoXA API 를 통해 문서를 Markdown + 이미지로 변환.

튜토리얼(`parser_tutorial.ipynb`, `parser_ipaas_tutorial.ipynb`) 을 그대로 따르는 단순 래퍼.
SDK 의 `parser.parse_document()` + `parser.write_result()` 를 사용.

환경변수:
    DOXA_TOKEN  (필수)  AI Asset Hub 발급 토큰
    DOXA_URL    (선택)  기본 https://doxa.sec.samsung.net
                        iPaaS 사내 : https://ipaas-sca.sec.samsung.net/sec/kr/doxa_parser_document_v2/1.0
                        iPaaS 외부 : https://sca.ipaas.samsung.com/sec/kr/doxa_parser_document_v2/1.0
    IPAAS_TOKEN (선택)  iPaaS 게이트웨이 경유 시
"""
from __future__ import annotations
import argparse
import io
import os
import sys
import traceback
import urllib3
from pathlib import Path

if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# .env 자동 로드 (tools/doc_converter/.env)
try:
    from dotenv import load_dotenv

    _env = Path(__file__).resolve().parent / ".env"
    if _env.is_file():
        load_dotenv(_env)
    else:
        load_dotenv()
except ImportError:
    pass

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SUPPORTED_EXTS = {
    ".pdf", ".pptx", ".docx", ".xlsx",
    ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp",
    ".csv", ".txt",
}


def _get_parser():
    from doxa.parser import DoxaParser

    token = os.environ.get("DOXA_TOKEN", "").strip()
    if not token:
        print(
            "[ERROR] DOXA_TOKEN 환경변수 미설정.\n"
            "  set DOXA_TOKEN=<AI Asset Hub 토큰>",
            file=sys.stderr,
        )
        sys.exit(2)

    url = os.environ.get("DOXA_URL", "https://doxa.sec.samsung.net")
    ipaas_token = os.environ.get("IPAAS_TOKEN", "")

    print(f"[doxa] URL   : {url}")
    print(f"[doxa] iPaaS : {'O' if ipaas_token else 'X'}")

    return DoxaParser(token=token, doxa_url=url, ipaas_token=ipaas_token)


def _params(response_format: str):
    """튜토리얼 패턴: BaseModel 서브클래스로 옵션 지정."""
    from pydantic import BaseModel

    class RequestDocumentOptions(BaseModel):
        response_format: str = response_format
        image_captioning_level: int = 0
        image_with_inner_text: bool = False
        layout_model: str = "default"
        layout_manual_entity: bool = False
        ocr_module: str = "hybrid"
        ocr_lang: str = "korean"
        recognize_table: bool = True
        bbox_scale: float = 0
        include_image_base64: bool = False
        escape: bool = True
        indent: bool = True

    return RequestDocumentOptions()


def convert_one(parser, src: Path, out_dir: Path, response_format: str) -> tuple[bool, str]:
    if src.suffix.lower() not in SUPPORTED_EXTS:
        return False, f"SKIP (unsupported: {src.suffix})"

    try:
        response = parser.parse_document(
            input_path=str(src),
            params=_params(response_format),
            timeout=3600,
        )
        # SDK 의 write_result 그대로 사용 (ZIP/JSON/TXT 자동 처리)
        parser.write_result(response, str(src), str(out_dir))

        # 출력 파일 찾기 (정확한 파일명은 SDK 내부에서 결정됨)
        stem = src.stem
        candidates = sorted(out_dir.glob(f"{stem}.*"))
        if candidates:
            f = candidates[0]
            return True, f"DoXA OK: {f.name} ({f.stat().st_size:,} B)"
        return True, "DoXA OK (파일 확인 불가)"
    except Exception as e:
        return False, f"DoXA FAIL: {type(e).__name__}: {e}"


def iter_sources(source: Path) -> list[Path]:
    if source.is_file():
        return [source]
    if source.is_dir():
        return sorted(
            f for f in source.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS
        )
    return []


def _pick_interactive() -> tuple[Path | None, Path | None, str]:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, simpledialog
    except ImportError:
        print("[interactive] tkinter 미설치 → CLI 인자 사용 필요", file=sys.stderr)
        return None, None, "standard"

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    if not os.environ.get("DOXA_TOKEN", "").strip():
        messagebox.showerror(
            "DOXA_TOKEN 미설정",
            "DOXA_TOKEN 환경변수를 설정하세요.\n"
            "  set DOXA_TOKEN=<AI Asset Hub 토큰>\n"
            "그 후 VS Code 를 재시작.",
        )
        root.destroy()
        return None, None, "standard"

    choice = messagebox.askyesnocancel(
        "선택", "단일 파일 변환하시겠습니까?\n\n예 = 파일 한 개\n아니요 = 폴더 일괄"
    )
    if choice is None:
        root.destroy()
        return None, None, "standard"

    if choice:
        src = filedialog.askopenfilename(
            title="변환할 파일 선택",
            filetypes=[
                ("지원 문서", "*.pdf *.pptx *.docx *.xlsx *.jpg *.jpeg *.png *.tif *.tiff *.bmp *.csv *.txt"),
                ("전체", "*.*"),
            ],
        )
    else:
        src = filedialog.askdirectory(title="변환할 폴더 선택")

    if not src:
        root.destroy()
        return None, None, "standard"
    src_path = Path(src).resolve()
    base = src_path if src_path.is_dir() else src_path.parent
    default_out = base.parent / f"{base.name}_doxa"

    use_default = messagebox.askyesno("출력 폴더", f"기본 출력 경로를 사용하시겠습니까?\n\n{default_out}")
    if use_default:
        out = default_out
    else:
        out_sel = filedialog.askdirectory(title="출력 폴더 선택")
        out = Path(out_sel).resolve() if out_sel else default_out

    fmt = simpledialog.askstring(
        "응답 포맷",
        "standard (기본)\nmarkdown_only / json_only\njson_with_image / page_image_only / debug_info",
        initialvalue="standard",
    ) or "standard"

    root.destroy()
    return src_path, out, fmt


def main():
    ap = argparse.ArgumentParser(description="DoXA 기반 문서 → Markdown 변환")
    ap.add_argument("source", type=Path, nargs="?", default=None)
    ap.add_argument("output", type=Path, nargs="?", default=None)
    ap.add_argument(
        "--format",
        default="standard",
        choices=["standard", "json_only", "markdown_only", "page_image_only", "json_with_image", "debug_info"],
    )
    args = ap.parse_args()

    if args.source is None:
        src_path, out, fmt = _pick_interactive()
        if src_path is None:
            sys.exit(0)
        args.format = fmt
        src = src_path
    else:
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
        f"- Format: {args.format}",
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
