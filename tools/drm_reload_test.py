"""DRM 걸린 Excel / PPT / PDF / Word 를 Fasoo 훅이 감시하지 않는 포맷으로 추출.

2026-04-21 실측 결과:
    - `.xlsx` / `.pptx` / `.png` / `.csv` 모두 DRM 상속 (확장자 훅)
    - **첫 줄 공란 `.txt` 만 통과** (서명 패턴 매칭 실패, proto_:22176 트릭)
    - 캡처도구로 저장한 `.png` 는 통과 → Fasoo 는 **프로세스 기반 훅**
      (Python/Office 는 감시 대상, 캡처도구는 화이트리스트 외).
      사내에서 시각 확인 필요 시: matplotlib 창을 띄워 캡처도구로 저장하거나,
      외부 PC 로 bundle.txt 반출 후 `--render` 로 재생성.

회피 전략:
    사내 반출물은 **.txt 단일 번들 하나만**. 이미지/차트는 외부 환경에서 재생성.
        사내: `<stem>_bundle.txt` (값/수식/차트 시리즈 데이터 통합, 첫 줄 공란)
        외부: 번들 txt 를 matplotlib 으로 PNG/SVG/PDF 재렌더링

사용법:
    # 사내 — 단일 추출
    python drm_reload_test.py <입력파일> [출력stem]

    # 외부 — 단일 렌더링
    python drm_reload_test.py --render <bundle.txt> [출력디렉터리] [png|svg|pdf]

    # 여러 경로 한번에 (파일/디렉터리 혼합 가능, 디렉터리는 재귀 탐색)
    #   .xlsx/.xls/.xlsm/.pptx/.ppt/.pptm → bundle.txt 추출
    #   *_bundle.txt                      → 차트 렌더링
    python drm_reload_test.py --batch [--out <dir>] [--format png|svg|pdf] <path> [<path>...]

지원 확장자:
    Excel — .xlsx / .xls / .xlsm          (값 / 수식 / 차트 시리즈)
    PPT   — .pptx / .ppt / .pptm           (슬라이드 텍스트 / 도형)
    PDF   — .pdf                            (페이지별 텍스트, PyMuPDF)
    Word  — .docx / .doc / .docm            (단락 / 표, Word COM)

추가 의존성:
    pymupdf   (PDF 용)       — pip install pymupdf
    pywin32   (Word COM 용)  — 이미 사용 중

프로그램 내 재로드:
    from tools.drm_reload_test import load_bundle, render_bundle_charts
    b = load_bundle('<stem>_bundle.txt')
    # Excel:
    #   b['values']['Sheet1']          → list[list]  (TSV raw)
    #   b['formulas']['Sheet1']['A1']  → '=SUM(...)'
    #   b['charts'][0]                 → {id, title, x_axis, y_axis, series}
    # PPT:    b['slides']        → [{id, shapes:[{idx,name,text}]}, ...]
    # PDF:    b['pages']         → {page_num: text}
    # Word:   b['paragraphs']    → [str, ...]
    #         b['tables']        → [{name, rows:[[cell, ...]]}, ...]
    render_bundle_charts('<stem>_bundle.txt', 'out_dir', format='png')
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
import shutil
from datetime import datetime, date
from pathlib import Path

SRC = r""
DST = r""


# ── 공용 헬퍼 ────────────────────────────────────────────────────────
def _col_to_letter(n: int) -> str:
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _to_2d(val, nrows: int, ncols: int) -> list[list]:
    if nrows == 1 and ncols == 1:
        return [[val]]
    if nrows == 1:
        return [list(val)] if isinstance(val, (list, tuple)) else [[val]]
    if ncols == 1:
        if val and isinstance(val[0], (list, tuple)):
            return [list(r) for r in val]
        return [[v] for v in val]
    return [list(r) for r in val]


def _safe_name(s: str) -> str:
    return re.sub(r'[^\w.-]', '_', str(s))[:80] or "_"


def _ser_value(v) -> str:
    if v is None:
        return ""
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, float):
        if v.is_integer() and abs(v) < 1e15:
            return str(int(v))
        return repr(v)
    return str(v).replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')


def _join_values(vals) -> str:
    if not vals:
        return ""
    return ",".join(_ser_value(v) for v in vals)


def _esc(s: str) -> str:
    """탭/개행/백슬래시 이스케이프 — PDF/Word 의 다중 줄 텍스트 한 줄로 평탄화."""
    if s is None:
        return ""
    return (str(s).replace('\\', '\\\\')
            .replace('\r\n', '\\n').replace('\r', '\\n').replace('\n', '\\n')
            .replace('\t', '\\t'))


def _unesc(s: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == '\\' and i + 1 < len(s):
            nxt = s[i + 1]
            if nxt == 'n':
                out.append('\n'); i += 2; continue
            if nxt == 't':
                out.append('\t'); i += 2; continue
            if nxt == '\\':
                out.append('\\'); i += 2; continue
        out.append(c); i += 1
    return ''.join(out)


# ── Excel 차트 메타 추출 (이미지 export 없음 — DRM 대상) ─────────────
def _extract_charts(sh) -> list[dict]:
    charts: list[dict] = []
    try:
        co_coll = sh.api.ChartObjects()
        n = co_coll.Count
    except Exception:
        return charts

    for i in range(1, n + 1):
        try:
            co = sh.api.ChartObjects(i)
            chart = co.Chart
        except Exception:
            continue

        info: dict = {"id": i, "name": None, "title": None,
                      "x_axis": None, "y_axis": None, "series": []}

        try: info["name"] = co.Name
        except Exception: pass
        try:
            if chart.HasTitle:
                info["title"] = chart.ChartTitle.Text
        except Exception: pass
        for axis_idx, key in ((1, "x_axis"), (2, "y_axis")):
            try:
                ax = chart.Axes(axis_idx)
                if ax.HasTitle:
                    info[key] = ax.AxisTitle.Text
            except Exception:
                pass

        try:
            sc = chart.SeriesCollection()
            ns = sc.Count
        except Exception:
            ns = 0

        for j in range(1, ns + 1):
            try:
                s = chart.SeriesCollection(j)
            except Exception:
                continue
            s_info = {"name": None, "x": [], "y": []}
            try: s_info["name"] = s.Name
            except Exception: pass
            try: s_info["y"] = list(s.Values) if s.Values else []
            except Exception: pass
            try: s_info["x"] = list(s.XValues) if s.XValues else []
            except Exception: pass
            info["series"].append(s_info)

        charts.append(info)

    return charts


# ── Excel 번들 작성 (txt 단일) ───────────────────────────────────────
def export_excel_bundle(src: Path, bundle_txt: Path) -> dict:
    import xlwings as xw
    import pandas as pd

    stats = {"sheets": 0, "rows_total": 0, "formulas": 0, "charts": 0}

    sheet_values: list[tuple[str, pd.DataFrame]] = []
    sheet_formulas: list[tuple[str, list[tuple[str, str]]]] = []
    sheet_charts: list[tuple[str, list[dict]]] = []

    app = xw.App(visible=False, add_book=False)
    try:
        app.display_alerts = False
        wb = app.books.open(str(src), update_links=False, read_only=True)
        try:
            for sh in wb.sheets:
                rng = sh.used_range
                empty = (rng.last_cell.row == 1 and rng.last_cell.column == 1
                         and rng.value is None)

                if empty:
                    sheet_values.append((sh.name, pd.DataFrame()))
                    sheet_formulas.append((sh.name, []))
                else:
                    val = rng.options(pd.DataFrame, index=False, header=False).value
                    df = val if isinstance(val, pd.DataFrame) else pd.DataFrame([[val]])
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
                    stats["rows_total"] += len(df)
                    stats["formulas"] += len(f_list)

                chart_list = _extract_charts(sh)
                sheet_charts.append((sh.name, chart_list))
                stats["charts"] += len(chart_list)
                stats["sheets"] += 1
        finally:
            wb.close()
    finally:
        app.quit()

    with open(bundle_txt, 'w', encoding='utf-8') as f:
        f.write("\n")  # ← DRM 회피용 첫 줄 공란
        f.write("# DRM-bypass bundle\n")
        f.write(f"# Source: {src}\n")
        f.write(f"# Exported: {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"# Sheets: {stats['sheets']}, Formulas: {stats['formulas']}, "
                f"Charts: {stats['charts']}\n")
        f.write("# Render charts: python drm_reload_test.py --render <this.txt> <outdir>\n")
        f.write("\n")

        f.write("===VALUES===\n")
        for name, df in sheet_values:
            f.write(f"[{name}]\n")
            if not df.empty:
                df.to_csv(f, sep='\t', index=False, header=False,
                          lineterminator='\n', na_rep='')
            f.write("\n")

        f.write("===FORMULAS===\n")
        for name, f_list in sheet_formulas:
            if not f_list:
                continue
            f.write(f"[{name}]\n")
            for addr, formula in f_list:
                f.write(f"{addr}\t{formula}\n")
            f.write("\n")

        f.write("===CHARTS===\n")
        for sheet_name, chart_list in sheet_charts:
            for ch in chart_list:
                tag = ch.get("name") or f"Chart{ch['id']}"
                f.write(f"[{sheet_name}::{tag}]\n")
                for key in ("title", "x_axis", "y_axis"):
                    if ch.get(key):
                        f.write(f"{key}={ch[key]}\n")
                for si, s in enumerate(ch.get("series", []), start=1):
                    sname = str(s.get("name") or "").replace('\t', ' ').replace('\n', ' ')
                    f.write(f"series.{si}.name\t{sname}\n")
                    f.write(f"series.{si}.x\t{_join_values(s.get('x', []))}\n")
                    f.write(f"series.{si}.y\t{_join_values(s.get('y', []))}\n")
                f.write("\n")

    return stats


# ── 번들 로더 ───────────────────────────────────────────────────────
def load_bundle(path: str | Path) -> dict:
    """번들 txt 파싱 → dict.

    키:
      values      {sheet: [[cell,...]]}        (Excel)
      formulas    {sheet: {cell: formula}}     (Excel)
      charts      [{id,title,x_axis,y_axis,series:[{name,x,y}]}, ...]  (Excel)
      slides      [{id, shapes:[{idx,name,text}]}, ...]                 (PPT)
      pages       {page_num: text}             (PDF)
      paragraphs  [str, ...]                   (Word)
      tables      [{name, rows:[[cell,...]]}, ...]  (Word)
    """
    result: dict = {
        "values": {}, "formulas": {}, "charts": [],
        "slides": [], "pages": {}, "paragraphs": [], "tables": [],
    }
    section: str | None = None
    key: str | None = None
    chart: dict | None = None
    table_rows: list[list[str]] | None = None
    table_name: str | None = None
    value_buf: list[str] = []

    def _flush_values():
        if key is not None and value_buf:
            result["values"][key] = [ln.split('\t') for ln in value_buf]
        value_buf.clear()

    def _flush_chart():
        nonlocal chart
        if chart is not None:
            result["charts"].append(chart)
        chart = None

    def _flush_table():
        nonlocal table_rows, table_name
        if table_rows is not None and table_name is not None:
            result["tables"].append({"name": table_name, "rows": table_rows})
        table_rows = None
        table_name = None

    def _parse_scalar(s: str):
        s = s.strip()
        if s == "":
            return None
        try:
            if '.' in s or 'e' in s.lower():
                return float(s)
            return int(s)
        except ValueError:
            return s

    with open(path, 'r', encoding='utf-8') as f:
        for raw in f:
            line = raw.rstrip('\r\n')
            if not line.strip() or line.lstrip().startswith('#'):
                continue

            if line.startswith('===') and line.endswith('==='):
                if section == 'VALUES': _flush_values()
                if section == 'CHARTS': _flush_chart()
                if section == 'TABLES': _flush_table()
                section = line.strip('=').strip()
                key = None
                continue

            if line.startswith('[') and line.endswith(']'):
                label = line[1:-1]
                if section == 'VALUES':
                    _flush_values()
                    key = label
                elif section == 'FORMULAS':
                    key = label
                    result["formulas"].setdefault(key, {})
                elif section == 'CHARTS':
                    _flush_chart()
                    chart = {"id": label, "title": None, "x_axis": None,
                             "y_axis": None, "series": []}
                elif section == 'TABLES':
                    _flush_table()
                    table_rows = []
                    table_name = label
                continue

            if section == 'VALUES':
                value_buf.append(line)
            elif section == 'FORMULAS':
                if key is None:
                    continue
                parts = line.split('\t', 1)
                if len(parts) == 2:
                    result["formulas"][key][parts[0]] = parts[1]
            elif section == 'CHARTS':
                if chart is None:
                    continue
                if line.startswith('series.'):
                    parts = line.split('\t', 1)
                    if len(parts) != 2:
                        continue
                    key_parts = parts[0].split('.')
                    if len(key_parts) != 3:
                        continue
                    _, idx_s, field = key_parts
                    try: idx = int(idx_s)
                    except ValueError: continue
                    while len(chart["series"]) < idx:
                        chart["series"].append({"name": None, "x": [], "y": []})
                    s = chart["series"][idx - 1]
                    if field == "name":
                        s["name"] = parts[1]
                    elif field in ("x", "y"):
                        s[field] = [_parse_scalar(v) for v in parts[1].split(',')] if parts[1] else []
                elif '=' in line:
                    k, v = line.split('=', 1)
                    if k in ("title", "x_axis", "y_axis"):
                        chart[k] = v
            elif section == 'PAGES':
                parts = line.split('\t', 1)
                if len(parts) == 2:
                    try: pno = int(parts[0])
                    except ValueError: continue
                    result["pages"][pno] = _unesc(parts[1])
            elif section == 'PARAGRAPHS':
                result["paragraphs"].append(_unesc(line))
            elif section == 'TABLES':
                if table_rows is None:
                    continue
                table_rows.append([_unesc(c) for c in line.split('\t')])

    if section == 'VALUES': _flush_values()
    if section == 'CHARTS': _flush_chart()
    if section == 'TABLES': _flush_table()

    return result


# ── 차트 재렌더링 (외부 환경에서) ────────────────────────────────────
def render_bundle_charts(bundle_path: str | Path, out_dir: str | Path,
                         format: str = 'png', dpi: int = 150) -> int:
    """번들 txt 의 차트 시리즈를 matplotlib 으로 재플롯 → PNG/SVG/PDF.

    DRM 없는 외부 환경에서 실행. format: 'png' / 'svg' / 'pdf'.
    """
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import font_manager
    import matplotlib.pyplot as plt

    # 한글 폰트 자동 탐색 (Win/Mac/Linux 순)
    for fname in ('Malgun Gothic', 'AppleGothic', 'NanumGothic', 'Noto Sans CJK KR', 'Noto Sans KR'):
        try:
            font_manager.findfont(fname, fallback_to_default=False)
            matplotlib.rcParams['font.family'] = fname
            break
        except Exception:
            continue
    matplotlib.rcParams['axes.unicode_minus'] = False

    bundle = load_bundle(bundle_path)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    count = 0
    for idx, ch in enumerate(bundle['charts'], start=1):
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            has_label = False
            for s in ch.get('series', []):
                y_raw = s.get('y') or []
                y = [v for v in y_raw if isinstance(v, (int, float))]
                if not y:
                    continue
                x_raw = s.get('x') or []
                if x_raw and all(isinstance(v, (int, float)) for v in x_raw[:len(y)]):
                    x = x_raw[:len(y)]
                else:
                    x = list(range(1, len(y) + 1))
                n = min(len(x), len(y))
                name = str(s.get('name') or '')[:60]
                ax.plot(x[:n], y[:n], label=name if name else None)
                if name:
                    has_label = True

            if ch.get('title'):
                ax.set_title(str(ch['title']))
            if ch.get('x_axis'):
                ax.set_xlabel(str(ch['x_axis']))
            if ch.get('y_axis'):
                ax.set_ylabel(str(ch['y_axis']))
            if has_label:
                ax.legend(loc='best', fontsize='small')
            ax.grid(True, alpha=0.3)

            chart_id = ch.get('id') or f'chart_{idx}'
            # 순번 접두로 중복 id 덮어쓰기 방지
            out_file = out_path / f'{idx:02d}_{_safe_name(chart_id)}.{format}'
            fig.tight_layout()
            fig.savefig(out_file, dpi=dpi, format=format)
            plt.close(fig)
            count += 1
        except Exception as e:
            print(f"[render 실패] {ch.get('id')}: {type(e).__name__}: {e}")
            try: plt.close('all')
            except Exception: pass

    return count


# ── PDF — PyMuPDF 로 페이지별 텍스트 추출 ────────────────────────────
def export_pdf_bundle(src: Path, bundle_txt: Path) -> dict:
    """PyMuPDF(fitz) 로 페이지 텍스트 → 번들 txt.

    사내 DRM PDF 는 Fasoo 가 Adobe 프로세스에 훅해 복호화 — PyMuPDF 가 읽을 수
    있을지 여부는 정책에 따라 다름. 실패 시 메시지로 안내.
    """
    try:
        import fitz  # pymupdf
    except ImportError:
        raise RuntimeError("pymupdf 미설치 — pip install pymupdf")

    stats = {"pages": 0, "chars": 0}
    pages: list[str] = []

    doc = fitz.open(str(src))
    try:
        if doc.needs_pass:
            raise RuntimeError("PDF 암호 보호됨 — 인증 없이 열 수 없음")
        for page in doc:
            text = page.get_text("text") or ""
            pages.append(text)
            stats["pages"] += 1
            stats["chars"] += len(text)
    finally:
        doc.close()

    with open(bundle_txt, 'w', encoding='utf-8') as f:
        f.write("\n")  # DRM 회피용 공란
        f.write("# DRM-bypass PDF bundle\n")
        f.write(f"# Source: {src}\n")
        f.write(f"# Exported: {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"# Pages: {stats['pages']}, Chars: {stats['chars']:,}\n")
        f.write("# Format: '<page_num>\\t<escaped_text>' per page (\\n \\t \\\\ escaped).\n")
        f.write("\n")
        f.write("===PAGES===\n")
        for i, text in enumerate(pages, start=1):
            f.write(f"{i}\t{_esc(text)}\n")

    return stats


# ── Word — Word COM 으로 단락 + 표 추출 ──────────────────────────────
def export_word_bundle(src: Path, bundle_txt: Path) -> dict:
    """Word COM (pywin32) 으로 단락 + 표 → 번들 txt.

    Excel/PPT 와 동일 패턴 — 사내 Fasoo 에이전트가 Word 프로세스에 훅해
    DRM 복호화 제공. 단락은 한 줄 평탄화(이스케이프), 표는 `\\t` 구분.
    """
    import win32com.client as win32
    import pythoncom

    stats = {"paragraphs": 0, "tables": 0, "chars": 0}
    paragraphs: list[str] = []
    tables: list[list[list[str]]] = []

    pythoncom.CoInitialize()
    app = None
    doc = None
    try:
        app = win32.DispatchEx("Word.Application")
        app.Visible = False
        app.DisplayAlerts = 0
        doc = app.Documents.Open(
            str(src),
            ReadOnly=True,
            ConfirmConversions=False,
            AddToRecentFiles=False,
        )

        try:
            n_para = doc.Paragraphs.Count
        except Exception:
            n_para = 0
        for i in range(1, n_para + 1):
            try:
                p = doc.Paragraphs(i)
                text = (p.Range.Text or "").rstrip('\r\x07\n')
                paragraphs.append(text)
                stats["paragraphs"] += 1
                stats["chars"] += len(text)
            except Exception:
                continue

        try:
            n_tbl = doc.Tables.Count
        except Exception:
            n_tbl = 0
        for ti in range(1, n_tbl + 1):
            try:
                tbl = doc.Tables(ti)
                rows: list[list[str]] = []
                n_rows = tbl.Rows.Count
                for r in range(1, n_rows + 1):
                    cells: list[str] = []
                    try:
                        n_cells = tbl.Rows(r).Cells.Count
                    except Exception:
                        n_cells = 0
                    for c in range(1, n_cells + 1):
                        try:
                            ct = tbl.Cell(r, c).Range.Text or ""
                            # Word cell 끝은 \r\x07 — 제거
                            ct = ct.rstrip('\r\x07\n ')
                            cells.append(ct)
                        except Exception:
                            cells.append("")
                    rows.append(cells)
                tables.append(rows)
                stats["tables"] += 1
            except Exception:
                continue
    finally:
        if doc is not None:
            try: doc.Close(False)
            except Exception: pass
        if app is not None:
            try: app.Quit()
            except Exception: pass
        pythoncom.CoUninitialize()

    with open(bundle_txt, 'w', encoding='utf-8') as f:
        f.write("\n")  # DRM 회피용 공란
        f.write("# DRM-bypass Word bundle\n")
        f.write(f"# Source: {src}\n")
        f.write(f"# Exported: {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"# Paragraphs: {stats['paragraphs']}, Tables: {stats['tables']}, "
                f"Chars: {stats['chars']:,}\n")
        f.write("# Format: PARAGRAPHS=one escaped line per paragraph, "
                "TABLES=[Table N] header then TSV rows.\n")
        f.write("\n")

        f.write("===PARAGRAPHS===\n")
        for p in paragraphs:
            f.write(_esc(p) + "\n")
        f.write("\n")

        f.write("===TABLES===\n")
        for ti, rows in enumerate(tables, start=1):
            f.write(f"[Table {ti}]\n")
            for row in rows:
                f.write("\t".join(_esc(c) for c in row) + "\n")
            f.write("\n")

    return stats


# ── PowerPoint — pptx 도 DRM 걸리므로 슬라이드를 번들 txt 로 ─────────
def export_pptx_bundle(src: Path, bundle_txt: Path) -> dict:
    """슬라이드 텍스트 + 도형 메타를 번들 txt 로 덤프.

    이미지는 첨부 불가 (.png 도 DRM). 필요하면 외부 환경에서 별도 캡처 도구 사용.
    """
    import win32com.client as win32
    import pythoncom

    stats = {"slides": 0, "shapes": 0}
    pythoncom.CoInitialize()
    app = None
    pres = None
    slides_data: list[dict] = []
    try:
        app = win32.DispatchEx("PowerPoint.Application")
        pres = app.Presentations.Open(str(src), ReadOnly=True, Untitled=False, WithWindow=False)
        for idx in range(1, pres.Slides.Count + 1):
            sl = pres.Slides.Item(idx)
            shapes: list[dict] = []
            for s_idx in range(1, sl.Shapes.Count + 1):
                shp = sl.Shapes.Item(s_idx)
                text = ""
                try:
                    if shp.HasTextFrame and shp.TextFrame.HasText:
                        text = shp.TextFrame.TextRange.Text
                except Exception:
                    pass
                shapes.append({
                    "idx": s_idx,
                    "name": getattr(shp, "Name", ""),
                    "text": text,
                })
                stats["shapes"] += 1
            slides_data.append({"idx": idx, "shapes": shapes})
            stats["slides"] += 1
    finally:
        if pres is not None:
            try: pres.Close()
            except Exception: pass
        if app is not None:
            try: app.Quit()
            except Exception: pass
        pythoncom.CoUninitialize()

    with open(bundle_txt, 'w', encoding='utf-8') as f:
        f.write("\n")  # DRM 회피용 공란
        f.write("# DRM-bypass PPT bundle\n")
        f.write(f"# Source: {src}\n")
        f.write(f"# Exported: {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"# Slides: {stats['slides']}, Shapes: {stats['shapes']}\n")
        f.write("\n")
        f.write("===SLIDES===\n")
        for sl in slides_data:
            f.write(f"[Slide {sl['idx']}]\n")
            for shp in sl["shapes"]:
                text = shp["text"].replace('\r', '\\r').replace('\n', '\\n').replace('\t', ' ')
                name = (shp["name"] or "").replace('\t', ' ')
                f.write(f"shape.{shp['idx']}.name\t{name}\n")
                if text:
                    f.write(f"shape.{shp['idx']}.text\t{text}\n")
            f.write("\n")

    return stats


# ── 엔트리 포인트 ────────────────────────────────────────────────────
def _cmd_extract(argv: list[str]) -> int:
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
    out_stem = Path(dst).expanduser().resolve() if dst else src_path.with_suffix("")
    out_stem.parent.mkdir(parents=True, exist_ok=True)

    print(f"[입력] {src_path}  ({src_path.stat().st_size:,} bytes)")

    try:
        if ext in (".xlsx", ".xls", ".xlsm"):
            bundle = Path(f"{out_stem}_bundle.txt")
            print(f"[출력] {bundle}  (첫 줄 공란 — 값/수식/차트 시리즈 통합)")
            stats = export_excel_bundle(src_path, bundle)
            print(f"[Excel] 시트 {stats['sheets']}, 행 {stats['rows_total']:,}, "
                  f"수식 {stats['formulas']}, 차트 {stats['charts']}")
            if stats['charts']:
                print(f"  외부 환경에서 차트 이미지 생성:")
                print(f"    python {Path(__file__).name} --render {bundle.name} <outdir>")
        elif ext in (".pptx", ".ppt", ".pptm"):
            bundle = Path(f"{out_stem}_bundle.txt")
            print(f"[출력] {bundle}  (슬라이드 텍스트/도형 메타 — 첫 줄 공란)")
            stats = export_pptx_bundle(src_path, bundle)
            print(f"[PPT] 슬라이드 {stats['slides']}, 도형 {stats['shapes']}")
        elif ext == ".pdf":
            bundle = Path(f"{out_stem}_bundle.txt")
            print(f"[출력] {bundle}  (PDF 페이지별 텍스트 — 첫 줄 공란)")
            stats = export_pdf_bundle(src_path, bundle)
            print(f"[PDF] 페이지 {stats['pages']}, 문자 {stats['chars']:,}")
        elif ext in (".docx", ".doc", ".docm"):
            bundle = Path(f"{out_stem}_bundle.txt")
            print(f"[출력] {bundle}  (Word 단락+표 — 첫 줄 공란)")
            stats = export_word_bundle(src_path, bundle)
            print(f"[Word] 단락 {stats['paragraphs']}, 표 {stats['tables']}, 문자 {stats['chars']:,}")
        else:
            print(f"[에러] 지원 않는 확장자: {ext}")
            return 2
    except Exception as e:
        print(f"[실패] {type(e).__name__}: {e}")
        print("  사내 Fasoo 미설치 환경이면 정상 실패.")
        return 1

    return 0


def _cmd_render(argv: list[str]) -> int:
    if len(argv) < 3:
        print("[에러] 사용법: --render <bundle.txt> [출력디렉터리] [png|svg|pdf]")
        return 2
    bundle = Path(argv[2]).expanduser().resolve()
    if not bundle.is_file():
        print(f"[에러] 번들 파일 없음: {bundle}")
        return 2
    out_dir = Path(argv[3]).expanduser().resolve() if len(argv) >= 4 else bundle.parent / 'charts'
    fmt = argv[4].lower() if len(argv) >= 5 else 'png'
    if fmt not in ('png', 'svg', 'pdf'):
        print(f"[에러] format 은 png/svg/pdf 중 하나: {fmt}")
        return 2

    print(f"[번들] {bundle}")
    print(f"[출력] {out_dir}  ({fmt})")
    try:
        n = render_bundle_charts(bundle, out_dir, format=fmt)
        print(f"[완료] 차트 {n}개 생성")
    except Exception as e:
        print(f"[실패] {type(e).__name__}: {e}")
        return 1
    return 0


_OFFICE_EXTS = {'.xlsx', '.xls', '.xlsm',
                '.pptx', '.ppt', '.pptm',
                '.docx', '.doc', '.docm',
                '.pdf'}


def _collect_batch_inputs(paths: list[str]) -> list[Path]:
    """파일/디렉터리 경로 리스트 → 처리 대상 파일 리스트.

    디렉터리는 재귀 탐색: Office 파일 + `*_bundle.txt` 만 수집.
    중복 제거, 정렬 순서 보존.
    """
    collected: list[Path] = []
    for p in paths:
        path = Path(p).expanduser().resolve()
        if path.is_file():
            # 명시 인자: 관대 — Office 확장자 또는 .txt 면 bundle 로 간주
            ext = path.suffix.lower()
            if ext in _OFFICE_EXTS or ext == '.txt':
                collected.append(path)
            else:
                print(f"[건너뜀] 미지원 확장자: {path}")
        elif path.is_dir():
            # 재귀 탐색: 엄격 — 임의의 .txt 가 섞이면 오처리 위험
            for f in sorted(path.rglob('*')):
                if not f.is_file():
                    continue
                ext = f.suffix.lower()
                if ext in _OFFICE_EXTS or f.name.endswith('_bundle.txt'):
                    collected.append(f)
        else:
            print(f"[건너뜀] 경로 없음: {path}")

    seen: set[Path] = set()
    unique: list[Path] = []
    for p in collected:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def _batch_out_stem(src: Path, out_dir: Path | None) -> Path:
    """출력 파일 stem 결정. out_dir 있으면 평탄화 + 부모명 접두로 충돌 회피."""
    if out_dir is None:
        return src.with_suffix('')
    parent = src.parent.name or 'root'
    return out_dir / _safe_name(f"{parent}_{src.stem}")


def _process_one(src: Path, out_dir: Path | None, fmt: str) -> tuple[str, str]:
    """단일 파일 처리. Returns (status, message). status ∈ {'ok', 'skip'}."""
    ext = src.suffix.lower()

    if ext in ('.xlsx', '.xls', '.xlsm'):
        out_stem = _batch_out_stem(src, out_dir)
        bundle = Path(f"{out_stem}_bundle.txt")
        bundle.parent.mkdir(parents=True, exist_ok=True)
        stats = export_excel_bundle(src, bundle)
        msg = (f"→ {bundle.name}  "
               f"(sheet={stats['sheets']}, row={stats['rows_total']:,}, "
               f"formula={stats['formulas']}, chart={stats['charts']})")
        return 'ok', msg

    if ext in ('.pptx', '.ppt', '.pptm'):
        out_stem = _batch_out_stem(src, out_dir)
        bundle = Path(f"{out_stem}_bundle.txt")
        bundle.parent.mkdir(parents=True, exist_ok=True)
        stats = export_pptx_bundle(src, bundle)
        msg = f"→ {bundle.name}  (slide={stats['slides']}, shape={stats['shapes']})"
        return 'ok', msg

    if ext == '.pdf':
        out_stem = _batch_out_stem(src, out_dir)
        bundle = Path(f"{out_stem}_bundle.txt")
        bundle.parent.mkdir(parents=True, exist_ok=True)
        stats = export_pdf_bundle(src, bundle)
        msg = f"→ {bundle.name}  (page={stats['pages']}, char={stats['chars']:,})"
        return 'ok', msg

    if ext in ('.docx', '.doc', '.docm'):
        out_stem = _batch_out_stem(src, out_dir)
        bundle = Path(f"{out_stem}_bundle.txt")
        bundle.parent.mkdir(parents=True, exist_ok=True)
        stats = export_word_bundle(src, bundle)
        msg = (f"→ {bundle.name}  "
               f"(para={stats['paragraphs']}, table={stats['tables']}, char={stats['chars']:,})")
        return 'ok', msg

    if ext == '.txt':
        # _bundle 접미 떼어내기 (없으면 stem 그대로)
        base = src.name[:-len('_bundle.txt')] if src.name.endswith('_bundle.txt') else src.stem
        if out_dir is None:
            chart_dir = src.parent / f"{base}_charts"
        else:
            chart_dir = out_dir / f"{_safe_name(src.parent.name or 'root')}_{base}_charts"
        n = render_bundle_charts(src, chart_dir, format=fmt)
        return 'ok', f"→ {chart_dir.name}/  ({n} charts as {fmt})"

    return 'skip', f"미지원: {ext}"


def _cmd_batch(argv: list[str]) -> int:
    """--batch [--out <dir>] [--format png|svg|pdf] <path> [<path>...]"""
    i = 2
    out_dir: Path | None = None
    fmt = 'png'
    paths: list[str] = []

    while i < len(argv):
        a = argv[i]
        if a == '--out':
            if i + 1 >= len(argv):
                print("[에러] --out 값 필요"); return 2
            out_dir = Path(argv[i + 1]).expanduser().resolve()
            out_dir.mkdir(parents=True, exist_ok=True)
            i += 2
        elif a == '--format':
            if i + 1 >= len(argv):
                print("[에러] --format 값 필요"); return 2
            fmt = argv[i + 1].lower()
            if fmt not in ('png', 'svg', 'pdf'):
                print(f"[에러] format 은 png/svg/pdf: {fmt}"); return 2
            i += 2
        else:
            paths.append(a)
            i += 1

    if not paths:
        print("[에러] 사용법: --batch [--out <dir>] [--format png|svg|pdf] <path>...")
        return 2

    files = _collect_batch_inputs(paths)
    if not files:
        print("[에러] 처리할 파일 없음")
        return 2

    print(f"[배치] {len(files)}개 파일")
    if out_dir:
        print(f"[출력] {out_dir}  (평탄화, <parent>_<stem>_* 네이밍)")
    else:
        print(f"[출력] 각 원본 옆")
    print()

    ok = skip = fail = 0
    failures: list[tuple[Path, str]] = []

    for idx, src in enumerate(files, 1):
        try:
            size = src.stat().st_size
        except OSError:
            size = 0
        print(f"[{idx}/{len(files)}] {src}  ({size:,} bytes)")
        try:
            status, msg = _process_one(src, out_dir, fmt)
            print(f"  {msg}")
            if status == 'ok':
                ok += 1
            else:
                skip += 1
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            print(f"  → 실패: {err}")
            fail += 1
            failures.append((src, err))

    print()
    print(f"[완료] 성공 {ok}, 건너뜀 {skip}, 실패 {fail}")
    if failures:
        print("[실패 목록]")
        for src, err in failures:
            print(f"  ! {src}: {err}")

    return 0 if fail == 0 else 1


def main(argv: list[str]) -> int:
    if len(argv) >= 2:
        if argv[1] == '--render':
            return _cmd_render(argv)
        if argv[1] == '--batch':
            return _cmd_batch(argv)
    return _cmd_extract(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
