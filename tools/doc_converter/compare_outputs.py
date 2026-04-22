"""
두 파이프라인 출력 비교 도구 (DoXA Web vs DoXA API, 또는 임의 비교)

사용:
    python compare_outputs.py <디렉토리A> <디렉토리B> [--label-a NAME] [--label-b NAME]

비교 항목:
- 파일 개수, MD 크기, 이미지 수
- MD 내용 라인·단어·문자 수
- HTML 테이블/rowspan/colspan 카운트
- 한글 글자 수, 특수문자 (↑↓←→向社比)
- 라인별 diff 통계
- 중요 단어 등장 횟수

출력: stdout 리포트 + 선택적 --save-md <경로>
"""
from __future__ import annotations
import argparse
import difflib
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp", ".svg"}


def find_md(dir_: Path) -> list[Path]:
    return sorted(dir_.rglob("*.md"))


def count_images(dir_: Path) -> int:
    return sum(1 for f in dir_.rglob("*") if f.is_file() and f.suffix.lower() in IMG_EXTS)


def analyze_md(md: Path) -> dict:
    text = md.read_text(encoding="utf-8", errors="replace")
    korean_chars = len(re.findall(r"[\uac00-\ud7a3]", text))
    table_open = len(re.findall(r"<table", text))
    rowspan = len(re.findall(r'rowspan\s*=\s*["\']?\d+', text))
    colspan = len(re.findall(r'colspan\s*=\s*["\']?\d+', text))
    img_refs = len(re.findall(r'<img\s', text)) + len(re.findall(r"!\[", text))
    page_break = len(re.findall(r"page-break", text))
    arrows = len(re.findall(r"[↑↓←→▲▼◀▶]", text))
    cjk_ext = len(re.findall(r"[向社比中等者]", text))
    return {
        "size_bytes": md.stat().st_size,
        "lines": text.count("\n") + 1,
        "chars": len(text),
        "korean_chars": korean_chars,
        "tables": table_open,
        "rowspan": rowspan,
        "colspan": colspan,
        "img_refs": img_refs,
        "page_breaks": page_break,
        "arrows": arrows,
        "cjk_ext": cjk_ext,
    }


def diff_ratio(a_text: str, b_text: str) -> float:
    sm = difflib.SequenceMatcher(None, a_text.splitlines(), b_text.splitlines())
    return sm.ratio()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a", type=Path)
    ap.add_argument("b", type=Path)
    ap.add_argument("--label-a", default="A")
    ap.add_argument("--label-b", default="B")
    ap.add_argument("--save-md", type=Path, default=None, help="리포트 MD 로 저장")
    args = ap.parse_args()

    a = args.a.resolve()
    b = args.b.resolve()
    lines = []

    def emit(s=""):
        print(s)
        lines.append(s)

    emit(f"# 비교 리포트: {args.label_a} vs {args.label_b}\n")
    emit(f"- **{args.label_a}**: `{a}`")
    emit(f"- **{args.label_b}**: `{b}`\n")

    a_mds = find_md(a)
    b_mds = find_md(b)
    a_imgs = count_images(a)
    b_imgs = count_images(b)

    emit("## 파일 개수")
    emit(f"- MD: {args.label_a}={len(a_mds)}, {args.label_b}={len(b_mds)}")
    emit(f"- 이미지: {args.label_a}={a_imgs}, {args.label_b}={b_imgs}\n")

    # 이름 기반 매칭 (stem 일치)
    a_map = {p.stem: p for p in a_mds}
    b_map = {p.stem: p for p in b_mds}
    common = sorted(set(a_map) & set(b_map))
    a_only = sorted(set(a_map) - set(b_map))
    b_only = sorted(set(b_map) - set(a_map))

    if a_only:
        emit(f"## {args.label_a} 만 존재 ({len(a_only)})")
        for s in a_only:
            emit(f"- {s}")
        emit("")
    if b_only:
        emit(f"## {args.label_b} 만 존재 ({len(b_only)})")
        for s in b_only:
            emit(f"- {s}")
        emit("")

    emit(f"## 공통 MD {len(common)} 건 — 항목별 비교\n")
    emit(
        "| 파일 | 지표 | "
        f"{args.label_a} | {args.label_b} | 차이 |"
    )
    emit("|------|------|------|------|------|")

    metrics = ["size_bytes", "lines", "korean_chars", "tables", "rowspan", "colspan", "img_refs", "page_breaks", "arrows"]
    for stem in common:
        a_info = analyze_md(a_map[stem])
        b_info = analyze_md(b_map[stem])
        for m in metrics:
            va, vb = a_info[m], b_info[m]
            diff = vb - va
            diff_s = f"+{diff}" if diff > 0 else str(diff)
            emit(f"| `{stem[:40]}...` | {m} | {va:,} | {vb:,} | {diff_s} |")
        # diff ratio
        ratio = diff_ratio(
            a_map[stem].read_text(encoding="utf-8", errors="replace"),
            b_map[stem].read_text(encoding="utf-8", errors="replace"),
        )
        emit(f"| `{stem[:40]}...` | **텍스트 유사도** | — | — | **{ratio:.1%}** |")
        emit("")

    if args.save_md:
        args.save_md.write_text("\n".join(lines), encoding="utf-8")
        print(f"\nReport saved to: {args.save_md}")


if __name__ == "__main__":
    main()
