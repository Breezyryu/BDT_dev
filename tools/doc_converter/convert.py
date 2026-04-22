"""
문서 → Markdown + 이미지 변환 파이프라인 (로컬 OSS 전용, 외부 API 없음)

- PDF   : marker-pdf (Surya OCR ko/en) → docling → pymupdf → markitdown
- xlsx  : docling → pandas (in-memory custom_doc_props strip) → markitdown
- pptx  : docling → markitdown
- docx  : docling → markitdown
- eml   : markitdown

사용:
    python convert.py <source_dir> [output_dir] [--force] [--pdf-only] [--failed-only]

환경변수:
    HF_HUB_OFFLINE=1       : 모델 재다운로드 차단 (모델 캐시된 후 오프라인 강제)
    HF_HOME=<경로>         : HF 모델 캐시 위치 지정
"""
from __future__ import annotations
import argparse
import io
import os
import sys
import traceback
import zipfile
from pathlib import Path

# UTF-8 stdout (Windows cp949 회피)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

PDF_EXTS = {".pdf"}
OFFICE_EXTS = {".docx", ".pptx", ".xlsx"}
MARKITDOWN_EXTS = {".eml", ".mht", ".msg", ".html", ".htm"}

_MARKER = None
_DOCLING = None


def safe_stem(p: Path) -> str:
    name = p.name
    for ext in (".mht.eml", ".xlsx.xlsx", ".xlsx.pdf"):
        if name.lower().endswith(ext):
            return name[: -len(ext)]
    return p.stem


# ---------- marker-pdf ----------
def get_marker():
    global _MARKER
    if _MARKER is not None:
        return _MARKER
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict

    _MARKER = PdfConverter(
        artifact_dict=create_model_dict(),
        config={"output_format": "markdown", "languages": "ko,en"},
    )
    return _MARKER


def convert_marker(src: Path, out_dir: Path) -> tuple[bool, str]:
    try:
        from marker.output import text_from_rendered

        conv = get_marker()
        rendered = conv(str(src))
        text, _, images = text_from_rendered(rendered)
        stem = safe_stem(src)
        md_path = out_dir / f"{stem}.md"
        img_dir = out_dir / "images"
        img_dir.mkdir(parents=True, exist_ok=True)
        for img_name, img in images.items():
            try:
                img.save(img_dir / img_name)
            except Exception:
                pass
        md_path.write_text(text, encoding="utf-8")
        return True, f"marker OK ({md_path.stat().st_size:,} B, {len(images)} imgs)"
    except Exception as e:
        return False, f"marker FAIL: {type(e).__name__}: {e}"


# ---------- docling ----------
def get_docling():
    global _DOCLING
    if _DOCLING is not None:
        return _DOCLING
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import EasyOcrOptions, PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    pdf_opts = PdfPipelineOptions()
    pdf_opts.do_ocr = True
    pdf_opts.ocr_options = EasyOcrOptions(lang=["ko", "en"])
    pdf_opts.generate_picture_images = True

    _DOCLING = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_opts)}
    )
    return _DOCLING


def convert_docling(src: Path, out_dir: Path) -> tuple[bool, str]:
    try:
        from docling_core.types.doc import ImageRefMode

        conv = get_docling()
        result = conv.convert(str(src))
        doc = result.document
        stem = safe_stem(src)
        md_path = out_dir / f"{stem}.md"
        img_dir = out_dir / "images"
        img_dir.mkdir(parents=True, exist_ok=True)
        doc.save_as_markdown(
            md_path, image_mode=ImageRefMode.REFERENCED, artifacts_dir=img_dir
        )
        return True, f"docling OK ({md_path.stat().st_size:,} B)"
    except Exception as e:
        return False, f"docling FAIL: {type(e).__name__}: {e}"


# ---------- markitdown ----------
def convert_markitdown(src: Path, out_dir: Path) -> tuple[bool, str]:
    try:
        from markitdown import MarkItDown

        md = MarkItDown()
        r = md.convert(str(src))
        stem = safe_stem(src)
        md_path = out_dir / f"{stem}.md"
        md_path.write_text(r.text_content, encoding="utf-8")
        return True, f"markitdown OK ({md_path.stat().st_size:,} B)"
    except Exception as e:
        return False, f"markitdown FAIL: {type(e).__name__}: {e}"


# ---------- pymupdf ----------
def convert_pymupdf(src: Path, out_dir: Path) -> tuple[bool, str]:
    try:
        import pymupdf

        stem = safe_stem(src)
        md_path = out_dir / f"{stem}.md"
        doc = pymupdf.open(str(src))
        chunks = [f"# {src.name}\n"]
        for i, page in enumerate(doc, 1):
            chunks.append(f"\n## Page {i}\n\n{page.get_text()}")
        md_path.write_text("\n".join(chunks), encoding="utf-8")
        doc.close()
        return True, f"pymupdf OK ({md_path.stat().st_size:,} B)"
    except Exception as e:
        return False, f"pymupdf FAIL: {type(e).__name__}: {e}"


# ---------- xlsx 복구 (custom_doc_props 파괴 대응) ----------
def _strip_custom_props_bytes(src_xlsx: Path) -> io.BytesIO:
    import re

    buf_out = io.BytesIO()
    with zipfile.ZipFile(src_xlsx, "r") as z_in, zipfile.ZipFile(
        buf_out, "w", zipfile.ZIP_DEFLATED
    ) as z_out:
        for item in z_in.infolist():
            name = item.filename
            if name.startswith("customXml/") or name == "docProps/custom.xml":
                continue
            data = z_in.read(name)
            if name == "[Content_Types].xml":
                text = data.decode("utf-8", errors="replace")
                text = text.replace(
                    '<Override PartName="/docProps/custom.xml" ContentType="application/vnd.openxmlformats-officedocument.custom-properties+xml"/>',
                    "",
                )
                data = text.encode("utf-8")
            if name == "_rels/.rels":
                text = data.decode("utf-8", errors="replace")
                text = re.sub(
                    r'<Relationship[^/]*Target="docProps/custom\.xml"[^/]*/>', "", text
                )
                data = text.encode("utf-8")
            z_out.writestr(item, data)
    buf_out.seek(0)
    return buf_out


def convert_xlsx_pandas(src: Path, out_dir: Path) -> tuple[bool, str]:
    try:
        import pandas as pd

        stem = safe_stem(src)
        try:
            buf = _strip_custom_props_bytes(src)
            xl = pd.ExcelFile(buf, engine="openpyxl")
        except Exception:
            xl = pd.ExcelFile(src, engine="openpyxl")

        md_parts = [f"# {src.name}\n"]
        for sheet in xl.sheet_names:
            try:
                df = xl.parse(sheet, header=None)
            except Exception as e:
                md_parts.append(f"\n## {sheet}\n\n_(sheet read error: {e})_\n")
                continue
            md_parts.append(f"\n## Sheet: {sheet}\n")
            md_parts.append(f"- rows: {len(df)}, cols: {df.shape[1]}\n")
            preview = df.head(200).fillna("").astype(str)
            md_parts.append(preview.to_markdown(index=False))
            if len(df) > 200:
                md_parts.append(f"\n\n_(+{len(df) - 200} more rows truncated)_\n")
        xl.close()
        md_path = out_dir / f"{stem}.md"
        md_path.write_text("\n".join(md_parts), encoding="utf-8")
        return True, f"pandas-xlsx OK ({md_path.stat().st_size:,} B)"
    except Exception as e:
        return False, f"pandas-xlsx FAIL: {type(e).__name__}: {e}"


# ---------- DRM 감지 ----------
def detect_drm(src: Path) -> str | None:
    try:
        with open(src, "rb") as f:
            head = f.read(32)
        if head.startswith(b"<## NASCA DRM"):
            return "NASCA DRM"
        if head.startswith(b"<!DOCTYPE html") or b"Fasoo" in head:
            return "Fasoo DRM(추정)"
    except Exception:
        pass
    return None


# ---------- 라우팅 ----------
def process_file(f: Path, out_root: Path, force: bool) -> tuple[bool, str]:
    ext = f.suffix.lower()
    if f.name.lower().endswith(".mht.eml"):
        ext = ".eml"

    stem = safe_stem(f)
    out_dir = out_root / stem
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"{stem}.md"

    if not force and md_path.exists() and md_path.stat().st_size > 1000:
        return True, f"SKIP (existing {md_path.stat().st_size:,} B)"

    drm = detect_drm(f)
    if drm:
        return False, f"SKIP (DRM: {drm})"

    if ext in PDF_EXTS:
        for fn in (convert_marker, convert_docling, convert_pymupdf, convert_markitdown):
            ok, msg = fn(f, out_dir)
            if ok:
                return True, msg
        return False, msg

    if ext in OFFICE_EXTS:
        ok, msg = convert_docling(f, out_dir)
        if ok:
            return True, msg
        if ext == ".xlsx":
            ok, msg2 = convert_xlsx_pandas(f, out_dir)
            if ok:
                return True, msg2
            msg = f"{msg}; {msg2}"
        ok, msg3 = convert_markitdown(f, out_dir)
        return ok, (msg3 if ok else f"{msg}; {msg3}")

    if ext in MARKITDOWN_EXTS:
        return convert_markitdown(f, out_dir)

    return False, f"SKIP (unsupported: {ext})"


def main():
    ap = argparse.ArgumentParser(description="Document → Markdown batch converter")
    ap.add_argument("source", type=Path, help="변환할 소스 디렉토리")
    ap.add_argument(
        "output",
        type=Path,
        nargs="?",
        default=None,
        help="출력 디렉토리 (기본: <source>_md)",
    )
    ap.add_argument("--force", action="store_true", help="기존 MD 무시 재변환")
    args = ap.parse_args()

    src_dir = args.source.resolve()
    if not src_dir.is_dir():
        print(f"ERROR: {src_dir} 가 디렉토리가 아닙니다", file=sys.stderr)
        sys.exit(2)

    out_dir = (args.output or src_dir.parent / f"{src_dir.name}_md").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(f for f in src_dir.iterdir() if f.is_file())
    print(f"Source : {src_dir}")
    print(f"Output : {out_dir}")
    print(f"Files  : {len(files)}\n")

    results = []
    for i, f in enumerate(files, 1):
        print(f"[{i:02d}/{len(files)}] {f.name}")
        ok, msg = process_file(f, out_dir, force=args.force)
        print(f"  -> {msg}")
        results.append((f.name, ok, msg))

    ok_cnt = sum(1 for _, ok, _ in results if ok)
    print(f"\nDONE: {ok_cnt}/{len(results)}")

    report = out_dir / "_conversion_report.md"
    lines = [
        "# Conversion Report\n",
        f"- Source: `{src_dir}`",
        f"- Output: `{out_dir}`",
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
