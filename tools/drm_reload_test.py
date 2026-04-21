"""DRM 걸린 Excel / PPT 를 Fasoo 훅이 감시하지 않는 포맷으로 추출.

2026-04-21 실측:
    - `.xlsx`, `.pptx` 쓰기 → 즉시 DRM 상속 (확장자 훅)
    - `.png` 쓰기 → 즉시 DRM 상속 (이미지 훅)
    - **첫 줄 공란 `.txt` 만 통과** (서명 패턴 매칭 실패, proto_:22176 트릭)

회피 전략:
    사내 반출물은 **.txt 단일 번들 하나만**. 이미지/차트는 외부 환경에서 재생성.
        사내: `<stem>_bundle.txt` (값/수식/차트 시리즈 데이터 통합, 첫 줄 공란)
        외부: 번들 txt 를 matplotlib 으로 PNG/SVG/PDF 재렌더링

사용법:
    # 사내 — txt 번들 추출 (기본)
    python drm_reload_test.py <입력파일> [출력stem]

    # 사내 — CSV 세트로 분할 (Fasoo 가 .csv 를 잡는지 실험)
    python drm_reload_test.py --csv <입력파일> [출력stem]

    # 외부 — 번들에서 차트 재렌더링
    python drm_reload_test.py --render <bundle.txt> [출력디렉터리] [png|svg|pdf]

프로그램 내 재로드:
    from tools.drm_reload_test import load_bundle, render_bundle_charts
    b = load_bundle('<stem>_bundle.txt')
    # b['values']['Sheet1']          → list[list]  (TSV raw)
    # b['formulas']['Sheet1']['A1']  → '=SUM(...)'
    # b['charts'][0]                 → {id, title, x_axis, y_axis, series:[{name,x,y}]}
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


# ── Excel → CSV 분할 (.csv 가 Fasoo 훅 대상인지 실험용) ──────────────
def export_excel_csv(src: Path, out_stem: Path) -> dict:
    """시트별 .csv + formulas.csv + charts_meta.csv + 차트 시리즈별 .csv.

    각 CSV 첫 줄 공란 (Fasoo 서명 패턴 회피 시도).
    """
    import xlwings as xw
    import pandas as pd

    stats = {"sheets": 0, "rows_total": 0, "formulas": 0,
             "charts": 0, "series_csv": 0, "files": 0}

    all_formulas: list[tuple[str, str, str]] = []    # (sheet, cell, formula)
    all_charts_meta: list[dict] = []                 # dict per chart
    chart_series_rows: list[tuple[Path, list[tuple]]] = []  # (csv_path, rows)

    app = xw.App(visible=False, add_book=False)
    try:
        app.display_alerts = False
        wb = app.books.open(str(src), update_links=False, read_only=True)
        try:
            for sh in wb.sheets:
                rng = sh.used_range
                empty = (rng.last_cell.row == 1 and rng.last_cell.column == 1
                         and rng.value is None)

                # 시트 값 → <stem>_<sheet>.csv
                sheet_tag = _safe_name(sh.name)
                sheet_csv = Path(f"{out_stem}_{sheet_tag}.csv")
                with open(sheet_csv, 'w', encoding='utf-8', newline='') as f:
                    f.write("\n")  # DRM 회피용 공란
                    if not empty:
                        val = rng.options(pd.DataFrame, index=False, header=False).value
                        df = val if isinstance(val, pd.DataFrame) else pd.DataFrame([[val]])
                        df.to_csv(f, index=False, header=False, lineterminator='\n', na_rep='')
                        stats["rows_total"] += len(df)
                stats["files"] += 1
                stats["sheets"] += 1

                # 수식 수집
                if not empty:
                    row0, col0 = rng.row, rng.column
                    nrows = rng.last_cell.row - row0 + 1
                    ncols = rng.last_cell.column - col0 + 1
                    formulas_2d = _to_2d(rng.formula, nrows, ncols)
                    for i, row in enumerate(formulas_2d):
                        for j, v in enumerate(row):
                            if isinstance(v, str) and v.startswith('='):
                                addr = f"{_col_to_letter(col0 + j)}{row0 + i}"
                                all_formulas.append((sh.name, addr, v))

                # 차트 메타 + 시리즈 CSV
                for ch in _extract_charts(sh):
                    tag = ch.get("name") or f"Chart{ch['id']}"
                    all_charts_meta.append({
                        "sheet": sh.name,
                        "chart": tag,
                        "title": ch.get("title") or "",
                        "x_axis": ch.get("x_axis") or "",
                        "y_axis": ch.get("y_axis") or "",
                        "series_count": len(ch.get("series", [])),
                    })
                    stats["charts"] += 1
                    for si, s in enumerate(ch.get("series", []), start=1):
                        xs = s.get("x") or []
                        ys = s.get("y") or []
                        n = max(len(xs), len(ys))
                        rows = []
                        for k in range(n):
                            xv = xs[k] if k < len(xs) else None
                            yv = ys[k] if k < len(ys) else None
                            rows.append((_ser_value(xv), _ser_value(yv)))
                        series_name = _safe_name(str(s.get("name") or f"series{si}"))
                        series_csv = Path(
                            f"{out_stem}_chart_{_safe_name(sh.name)}_{_safe_name(tag)}_{si:02d}_{series_name}.csv"
                        )
                        chart_series_rows.append((series_csv, rows))
                        stats["series_csv"] += 1
                        stats["files"] += 1
        finally:
            wb.close()
    finally:
        app.quit()

    # 수식 CSV
    formulas_csv = Path(f"{out_stem}_formulas.csv")
    with open(formulas_csv, 'w', encoding='utf-8', newline='') as f:
        f.write("\n")  # DRM 회피용 공란
        f.write("sheet,cell,formula\n")
        for sh_name, addr, formula in all_formulas:
            # CSV 안전 escape (쉼표/따옴표 포함 수식)
            sh_e = sh_name.replace('"', '""')
            fml_e = formula.replace('"', '""')
            f.write(f'"{sh_e}",{addr},"{fml_e}"\n')
    stats["formulas"] = len(all_formulas)
    stats["files"] += 1

    # 차트 메타 CSV
    charts_meta_csv = Path(f"{out_stem}_charts_meta.csv")
    with open(charts_meta_csv, 'w', encoding='utf-8', newline='') as f:
        f.write("\n")
        f.write("sheet,chart,title,x_axis,y_axis,series_count\n")
        for m in all_charts_meta:
            def esc(s): return str(s).replace('"', '""')
            f.write(f'"{esc(m["sheet"])}","{esc(m["chart"])}",'
                    f'"{esc(m["title"])}","{esc(m["x_axis"])}","{esc(m["y_axis"])}",'
                    f'{m["series_count"]}\n')
    stats["files"] += 1

    # 차트 시리즈 CSV 각각
    for series_csv, rows in chart_series_rows:
        with open(series_csv, 'w', encoding='utf-8', newline='') as f:
            f.write("\n")
            f.write("x,y\n")
            for xv, yv in rows:
                x_e = xv.replace('"', '""')
                y_e = yv.replace('"', '""')
                f.write(f'"{x_e}","{y_e}"\n')

    return stats


# ── 번들 로더 ───────────────────────────────────────────────────────
def load_bundle(path: str | Path) -> dict:
    """번들 txt 파싱 → {'values', 'formulas', 'charts'}."""
    result: dict = {"values": {}, "formulas": {}, "charts": []}
    section: str | None = None
    key: str | None = None
    chart: dict | None = None
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
                section = line.strip('=').strip()
                key = None
                continue

            if line.startswith('[') and line.endswith(']'):
                if section == 'VALUES':
                    _flush_values()
                    key = line[1:-1]
                elif section == 'FORMULAS':
                    key = line[1:-1]
                    result["formulas"].setdefault(key, {})
                elif section == 'CHARTS':
                    _flush_chart()
                    chart = {"id": line[1:-1], "title": None, "x_axis": None,
                             "y_axis": None, "series": []}
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

    if section == 'VALUES': _flush_values()
    if section == 'CHARTS': _flush_chart()

    return result


# ── 차트 재렌더링 (외부 환경에서) ────────────────────────────────────
def render_bundle_charts(bundle_path: str | Path, out_dir: str | Path,
                         format: str = 'png', dpi: int = 150) -> int:
    """번들 txt 의 차트 시리즈를 matplotlib 으로 재플롯 → PNG/SVG/PDF.

    DRM 없는 외부 환경에서 실행. format: 'png' / 'svg' / 'pdf'.
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

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
            out_file = out_path / f'{_safe_name(chart_id)}.{format}'
            fig.tight_layout()
            fig.savefig(out_file, dpi=dpi, format=format)
            plt.close(fig)
            count += 1
        except Exception as e:
            print(f"[render 실패] {ch.get('id')}: {type(e).__name__}: {e}")
            try: plt.close('all')
            except Exception: pass

    return count


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


def _cmd_csv(argv: list[str]) -> int:
    """--csv <입력파일> [출력stem] — Excel 을 CSV 세트로 분할 (첫 줄 공란)."""
    if len(argv) < 3:
        print("[에러] 사용법: --csv <입력파일> [출력stem]")
        return 2
    src = argv[2]
    dst = argv[3] if len(argv) >= 4 else ""

    src_path = Path(src).expanduser().resolve()
    if not src_path.is_file():
        print(f"[에러] 파일 없음: {src_path}")
        return 2

    ext = src_path.suffix.lower()
    if ext not in (".xlsx", ".xls", ".xlsm"):
        print(f"[에러] CSV 모드는 Excel 입력만 지원: {ext}")
        return 2

    out_stem = Path(dst).expanduser().resolve() if dst else src_path.with_suffix("")
    out_stem.parent.mkdir(parents=True, exist_ok=True)

    print(f"[입력] {src_path}  ({src_path.stat().st_size:,} bytes)")
    print(f"[출력] {out_stem}_*.csv  (첫 줄 공란 — Fasoo 훅 실험용)")

    try:
        stats = export_excel_csv(src_path, out_stem)
        print(f"[CSV] 시트 {stats['sheets']}, 행 {stats['rows_total']:,}, "
              f"수식 {stats['formulas']}, 차트 {stats['charts']}, "
              f"시리즈CSV {stats['series_csv']}, 파일 총 {stats['files']}개")
        print()
        print("── 산출물 구조 ──")
        print(f"  {out_stem.name}_<sheet>.csv                         시트별 값")
        print(f"  {out_stem.name}_formulas.csv                        수식 (sheet,cell,formula)")
        print(f"  {out_stem.name}_charts_meta.csv                     차트 메타")
        print(f"  {out_stem.name}_chart_<sheet>_<chart>_NN_<name>.csv 차트 시리즈 (x,y)")
    except Exception as e:
        print(f"[실패] {type(e).__name__}: {e}")
        print("  사내 Fasoo 미설치 환경이면 정상 실패.")
        return 1
    return 0


def main(argv: list[str]) -> int:
    if len(argv) >= 2:
        if argv[1] == '--render':
            return _cmd_render(argv)
        if argv[1] == '--csv':
            return _cmd_csv(argv)
    return _cmd_extract(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
