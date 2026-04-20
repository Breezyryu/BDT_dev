"""DRM 걸린 .xlsx / .pptx 를 읽어 새 파일로 **재출력** (데이터 재작성 방식).

회피 경로 3가지:
    1. Excel 값   → xlsxwriter 로 새 .xlsx 처음부터 작성
    2. Excel 수식 → 첫 줄 공란 .txt 로 덤프 (Fasoo 서명 패턴 매칭 실패 트릭,
                    proto_ line 22176 `f.write("\\n")  # DRM 회피용 공란` 와 동일)
    3. PPT 슬라이드 → PNG export → python-pptx 로 새 pptx 작성

SaveAs 는 Fasoo 훅이 잡아 DRM 상속되므로 사용하지 않음.

사용법:
    python drm_reload_test.py <입력파일> [출력파일]
또는 SRC / DST 상수 직접 수정.

Excel 입력 시 두 개 생성:
    <stem>_export.xlsx   — 값만 (서식/수식/차트 손실)
    <stem>_formula.txt   — 수식 덤프 (첫 줄 공란)

사내 환경에서 이 두 파일을 만들어 외부로 옮기면 현재 환경에서 참조 데이터로 재사용 가능.
"""
from __future__ import annotations

import os
import sys
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

SRC = r""   # 예: r"D:\data\reliability\sample.xlsx"
DST = r""   # 비우면 <SRC>_export.<ext> 로 자동 생성


# ── 공용 헬퍼 ────────────────────────────────────────────────────────
def _col_to_letter(n: int) -> str:
    """1-indexed 컬럼 번호 → Excel 레터 (A, B, ..., Z, AA, AB, ...)."""
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _to_2d(val, nrows: int, ncols: int) -> list[list]:
    """xlwings .value / .formula 반환값을 항상 2D list 로 정규화."""
    if nrows == 1 and ncols == 1:
        return [[val]]
    if nrows == 1:
        return [list(val)] if isinstance(val, (list, tuple)) else [[val]]
    if ncols == 1:
        if val and isinstance(val[0], (list, tuple)):
            return [list(r) for r in val]
        return [[v] for v in val]
    return [list(r) for r in val]


# ── Excel (.xlsx / .xls / .xlsm) ─────────────────────────────────────
def export_excel(src: Path, dst_xlsx: Path, dst_formula_txt: Path) -> dict:
    """xlwings 로 값 + 수식 동시 추출 → xlsx 와 txt 로 나눠 새 파일 작성.

    proto_ 패턴:
        - 읽기: `_xw_app.books.open → sh.used_range.options(pd.DataFrame).value`
                (DataTool_optRCD_proto_.py:20410, 20433-20435)
        - 쓰기: `pd.ExcelWriter(engine="xlsxwriter")` 로 새 파일 (line 20490)
        - 첫 줄 공란: `f.write("\\n")  # DRM 회피용 공란` (line 22176)
    """
    import xlwings as xw
    import pandas as pd

    stats = {"sheets": 0, "rows_total": 0, "formulas": 0}

    sheet_values: list[tuple[str, pd.DataFrame]] = []
    sheet_formulas: list[tuple[str, list[tuple[str, str]]]] = []

    app = xw.App(visible=False, add_book=False)
    try:
        app.display_alerts = False
        wb = app.books.open(str(src), update_links=False, read_only=True)
        try:
            for sh in wb.sheets:
                rng = sh.used_range
                empty_rng = (rng.last_cell.row == 1
                             and rng.last_cell.column == 1
                             and rng.value is None)

                if empty_rng:
                    sheet_values.append((sh.name, pd.DataFrame()))
                    sheet_formulas.append((sh.name, []))
                    stats["sheets"] += 1
                    continue

                # 값
                val = rng.options(pd.DataFrame, index=False, header=False).value
                df = val if isinstance(val, pd.DataFrame) else pd.DataFrame([[val]])

                # 수식 (2D) — formula 속성은 '=' 로 시작하는 문자열을 돌려줌
                row0, col0 = rng.row, rng.column
                nrows = rng.last_cell.row - row0 + 1
                ncols = rng.last_cell.column - col0 + 1
                formulas_2d = _to_2d(rng.formula, nrows, ncols)

                f_list: list[tuple[str, str]] = []
                for i, row in enumerate(formulas_2d):
                    for j, v in enumerate(row):
                        if isinstance(v, str) and v.startswith('='):
                            addr = f"{_col_to_letter(col0 + j)}{row0 + i}"
                            f_list.append((addr, v))

                sheet_values.append((sh.name, df))
                sheet_formulas.append((sh.name, f_list))
                stats["sheets"] += 1
                stats["rows_total"] += len(df)
                stats["formulas"] += len(f_list)
        finally:
            wb.close()
    finally:
        app.quit()

    # (1) 값 → 새 xlsx (처음부터 작성, SaveAs 훅 우회)
    with pd.ExcelWriter(str(dst_xlsx), engine="xlsxwriter") as writer:
        for name, df in sheet_values:
            safe = name[:31]
            if df.empty:
                pd.DataFrame().to_excel(writer, sheet_name=safe, index=False, header=False)
            else:
                df.to_excel(writer, sheet_name=safe, index=False, header=False)

    # (2) 수식 → 첫 줄 공란 txt (Fasoo 서명 패턴 회피)
    with open(dst_formula_txt, 'w', encoding='utf-8') as f:
        f.write("\n")  # ← DRM 회피용 공란 (proto_ 22176 동일)
        f.write("# DRM-bypass formula dump\n")
        f.write(f"# Source: {src}\n")
        f.write(f"# Exported: {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"# Sheets: {stats['sheets']}, Formulas: {stats['formulas']}\n")
        f.write("# Format: [SheetName] header, then '<cell>\\t<formula>' per line.\n")
        f.write("\n")
        for name, f_list in sheet_formulas:
            f.write(f"[{name}]\n")
            for addr, formula in f_list:
                f.write(f"{addr}\t{formula}\n")
            f.write("\n")

    return stats


def load_formula_txt(path: str | Path) -> dict[str, dict[str, str]]:
    """export_excel 이 생성한 수식 txt 를 읽어 `{sheet: {cell: formula}}` 반환.

    현재 환경에서 사내 파일의 수식을 참조 데이터로 로드할 때 사용.
    """
    result: dict[str, dict[str, str]] = {}
    current: str | None = None
    with open(path, 'r', encoding='utf-8') as f:
        for raw in f:
            line = raw.rstrip('\r\n')
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            if line.startswith('[') and line.endswith(']'):
                current = line[1:-1]
                result.setdefault(current, {})
                continue
            if current is None:
                continue
            parts = line.split('\t', 1)
            if len(parts) == 2:
                cell, formula = parts
                result[current][cell] = formula
    return result


# ── PowerPoint (.pptx / .ppt) ────────────────────────────────────────
def export_pptx(src: Path, dst: Path) -> dict:
    """PowerPoint COM 으로 슬라이드를 PNG 로 export → python-pptx 로 새 파일."""
    import win32com.client as win32
    import pythoncom
    from pptx import Presentation
    from pptx.util import Emu

    stats = {"slides": 0}
    tmp_dir = Path(tempfile.mkdtemp(prefix="drm_pptx_"))
    pythoncom.CoInitialize()
    app = None
    pres = None
    try:
        app = win32.DispatchEx("PowerPoint.Application")
        pres = app.Presentations.Open(str(src), ReadOnly=True, Untitled=False, WithWindow=False)

        slide_w_pt = pres.PageSetup.SlideWidth
        slide_h_pt = pres.PageSetup.SlideHeight
        slide_w_emu = int(slide_w_pt * 12700)
        slide_h_emu = int(slide_h_pt * 12700)
        px_w = int(slide_w_pt * 2)
        px_h = int(slide_h_pt * 2)

        images: list[Path] = []
        for idx in range(1, pres.Slides.Count + 1):
            img_path = tmp_dir / f"slide_{idx:04d}.png"
            pres.Slides.Item(idx).Export(str(img_path), "PNG", px_w, px_h)
            images.append(img_path)
            stats["slides"] += 1
    finally:
        if pres is not None:
            try: pres.Close()
            except Exception: pass
        if app is not None:
            try: app.Quit()
            except Exception: pass
        pythoncom.CoUninitialize()

    try:
        prs = Presentation()
        prs.slide_width = Emu(slide_w_emu)
        prs.slide_height = Emu(slide_h_emu)
        blank_layout = prs.slide_layouts[6]

        for img in images:
            slide = prs.slides.add_slide(blank_layout)
            slide.shapes.add_picture(str(img), 0, 0, prs.slide_width, prs.slide_height)

        prs.save(str(dst))
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return stats


# ── 엔트리 포인트 ─────────────────────────────────────────────────────
def main(argv: list[str]) -> int:
    if len(argv) >= 2:
        src = argv[1]
        dst = argv[2] if len(argv) >= 3 else ""
    else:
        src, dst = SRC, DST

    if not src:
        print("[에러] 입력 파일 경로 필요. 인자 전달 또는 SRC 변수 수정.")
        return 2

    src_path = Path(src).expanduser().resolve()
    if not src_path.is_file():
        print(f"[에러] 파일 없음: {src_path}")
        return 2

    ext = src_path.suffix.lower()
    if not dst:
        dst_path = src_path.with_name(f"{src_path.stem}_export{ext}")
    else:
        dst_path = Path(dst).expanduser().resolve()
        dst_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[입력] {src_path}  ({src_path.stat().st_size:,} bytes)")
    print(f"[방식] 읽기(COM) → 새 파일 쓰기 (SaveAs 훅 우회)")

    try:
        if ext in (".xlsx", ".xls", ".xlsm"):
            formula_txt = dst_path.with_name(f"{dst_path.stem.removesuffix('_export')}_formula.txt")
            print(f"[출력 1] {dst_path}")
            print(f"[출력 2] {formula_txt}  (첫 줄 공란 = Fasoo 서명 회피)")
            stats = export_excel(src_path, dst_path, formula_txt)
            print(f"[Excel] 시트 {stats['sheets']}개, 총 행 {stats['rows_total']:,}, 수식 {stats['formulas']}개")
        elif ext in (".pptx", ".ppt", ".pptm"):
            print(f"[출력] {dst_path}")
            stats = export_pptx(src_path, dst_path)
            print(f"[PPT] 슬라이드 {stats['slides']}장 (이미지 기반 재작성)")
        else:
            print(f"[에러] 지원 않는 확장자: {ext}")
            return 2
    except Exception as e:
        print(f"[실패] {type(e).__name__}: {e}")
        print("  사내 Fasoo 미설치 환경이면 정상 실패.")
        return 1

    if not dst_path.is_file():
        print("[실패] 저장 파일 미생성.")
        return 1

    print(f"[완료] {dst_path.stat().st_size:,} bytes")
    print()
    print("── 외부 환경에서 수식 재로드 예시 ──")
    print("  from tools.drm_reload_test import load_formula_txt")
    print("  formulas = load_formula_txt('<stem>_formula.txt')")
    print("  # formulas['Sheet1']['A1']  →  '=SUM(B1:B10)'")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
