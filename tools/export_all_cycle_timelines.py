"""exp_data 전체 데이터셋 사이클 타임라인 일괄 추출 + HTML 렌더.

사용:
    python tools/export_all_cycle_timelines.py [--root <exp_data 경로>] [--out <html 경로>]

기본:
    root = C:/Users/Ryu/battery/python/BDT_dev/raw/raw_exp/exp_data
    out  = docs/code/02_레퍼런스/260510_exp_data_cycle_timelines.html

각 카테고리(성능/수명/...) 별로 dataset 1행씩, 대표 채널(max_tc 최대)의 classified
기반 타임라인 블록을 색상으로 출력. 코드는 BDT 본 모듈(DataTool_optRCD_proto_)의
`_build_channel_meta`를 그대로 사용하므로 사이클 탭 화면과 동일한 분류·색상.
"""
from __future__ import annotations

import argparse
import html
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any

# stdout/stderr UTF-8 강제 (cp949 환경 안전)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# BDT 본 모듈 import
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "DataTool_dev_code"))
import DataTool_optRCD_proto_ as bdt  # noqa: E402

# ---- 정적 자원 ----
PALETTE = bdt.THEME["PALETTE"]
CLASSIFIED_COLORS = bdt._CLASSIFIED_COLORS
PATTERN_CATEGORIES = bdt._PATTERN_CATEGORIES


def _is_pne_dataset(ds_path: Path) -> bool:
    for sub in ds_path.iterdir():
        if not sub.is_dir():
            continue
        try:
            if bdt.is_pne_folder(str(sub)):
                return True
        except Exception:
            pass
        # PNE 채널 한 개만 보면 충분
        return False
    return False


def _find_channels(ds_path: Path) -> list[Path]:
    """dataset 폴더에서 채널 폴더 목록 (PNE 기준 M01ChXXX, Toyo 기준 digit-only)."""
    channels = []
    for sub in sorted(ds_path.iterdir()):
        if not sub.is_dir():
            continue
        name = sub.name
        if name == "Pattern":
            continue
        if bdt._is_channel_folder(name):
            channels.append(sub)
    return channels


def _pick_best_channel(channels: list[Path]) -> tuple[Path | None, Any]:
    """max_tc 가장 큰 채널 + 그 meta 반환."""
    best_ch = None
    best_meta = None
    best_lc = -1
    for ch in channels:
        try:
            meta = bdt._build_channel_meta(str(ch))
        except Exception:
            meta = None
        if meta is None:
            continue
        lc = meta.max_tc or 0
        if lc > best_lc:
            best_lc = lc
            best_ch = ch
            best_meta = meta
    return best_ch, best_meta


def _build_blocks_for_meta(meta) -> list[dict]:
    """ChannelMeta → 타임라인 블록. classified 우선, 없으면 StepType 폴백.

    각 블록에 tc_info 기반 chg_crate/dchg_crate 추가 (median over block range).
    """
    if meta is None:
        return []
    blocks = []
    if meta.classified:
        try:
            blocks = bdt._build_timeline_blocks_tc_by_loop(
                meta.classified, cycle_map=meta.cycle_map
            )
        except Exception:
            blocks = []
    elif hasattr(meta, "save_end_data") and meta.save_end_data is not None:
        try:
            blocks = bdt._build_timeline_blocks(meta.save_end_data)
        except Exception:
            blocks = []

    # tc_info 부착 — block 범위에서 median chg/dchg crate
    tc_info = getattr(meta, "tc_info", None) or {}
    classified_by_tc = {c['cycle']: c for c in (meta.classified or [])}
    if tc_info or classified_by_tc:
        for b in blocks:
            chg_rates, dchg_rates, n_chgs, n_dchgs = [], [], [], []
            for tc in range(b['start'], b['end'] + 1):
                t = tc_info.get(tc)
                if t is not None:
                    if t.chg_crate is not None:
                        chg_rates.append(t.chg_crate)
                    if t.dchg_crate is not None:
                        dchg_rates.append(t.dchg_crate)
                cl = classified_by_tc.get(tc)
                if cl:
                    if cl.get('n_charge') is not None:
                        n_chgs.append(cl['n_charge'])
                    if cl.get('n_discharge') is not None:
                        n_dchgs.append(cl['n_discharge'])

            def _median(xs):
                if not xs:
                    return None
                xs = sorted(xs)
                n = len(xs)
                return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2

            b['chg_crate'] = _median(chg_rates)
            b['dchg_crate'] = _median(dchg_rates)
            b['n_charge_med'] = _median(n_chgs)
            b['n_discharge_med'] = _median(n_dchgs)
    return blocks


def _format_crate(c):
    if c is None:
        return ""
    if c >= 1.0:
        return f"{c:.2f}C"
    return f"{c:.3f}C".rstrip("0").rstrip(".") + "C" if c < 1 else f"{c:.2f}C"


def _block_color(pattern: str) -> tuple[str, str]:
    """블록 패턴 → (hex_color, desc).

    GITT 방향 분기 시각화 (260510): 같은 idx=3 orange 계열에서 명도 변형으로
    충전/방전 구분.
    """
    info = CLASSIFIED_COLORS.get(pattern) or PATTERN_CATEGORIES.get(pattern)
    if info is None:
        info = PATTERN_CATEGORIES["X"]
    color_idx = info.get("color_idx", 9)
    desc = info.get("desc", pattern)
    # GITT 방향별 색조 변형 (PALETTE[3] = #F39B7F 베이스)
    if pattern == "GITT(charge)":
        return "#F8B89D", desc      # 더 밝은 살구 (충전 = 채워가는 상승)
    if pattern == "GITT(discharge)":
        return "#D67555", desc      # 더 어둡고 붉은 살구 (방전 = 비워가는 하강)
    return PALETTE[color_idx % len(PALETTE)], desc


def _render_blocks_html(blocks: list[dict], total: int) -> str:
    """블록 리스트 → 가로 막대 HTML 한 줄."""
    if not blocks or total <= 0:
        return '<div class="bar empty">데이터 없음</div>'
    parts = ['<div class="bar">']
    half_set = {"initial", "반사이클"}
    # 가중치 계산 (반사이클 = 0.3 가중)
    weights = []
    for b in blocks:
        w = b["count"]
        if b.get("pattern") in half_set:
            w *= 0.3
        weights.append(w)
    total_w = sum(weights) or 1
    for b, w in zip(blocks, weights):
        color, desc = _block_color(b["pattern"])
        pct = w / total_w * 100
        crate_chg = _format_crate(b.get("chg_crate"))
        crate_dchg = _format_crate(b.get("dchg_crate"))
        crate_str = ""
        if crate_chg or crate_dchg:
            crate_str = f"\n충전 {crate_chg or '?'} / 방전 {crate_dchg or '?'}"
        tip = (f"{b['pattern']} · {b['start']}-{b['end']} ({b['count']} cy)"
               f" · {desc}{crate_str}")
        parts.append(
            f'<div class="seg" style="width:{pct:.3f}%;background:{color}" '
            f'title="{html.escape(tip)}"></div>'
        )
    parts.append("</div>")
    return "".join(parts)


def _render_summary_pills(blocks: list[dict]) -> str:
    """블록 카테고리 빈도 + C-rate → pill 리스트.

    각 패턴에 대해 등장한 (chg_crate, dchg_crate) 조합을 별도 pill로 분리.
    동일 패턴 + 다른 C-rate = 다른 pill (가속수명 1C vs RPT 0.2C 구분).
    """
    # (pattern, chg_crate_str, dchg_crate_str) → count
    bucket: dict[tuple[str, str, str], int] = {}
    for b in blocks:
        key = (b["pattern"],
               _format_crate(b.get("chg_crate")),
               _format_crate(b.get("dchg_crate")))
        bucket[key] = bucket.get(key, 0) + b["count"]
    if not bucket:
        return ""
    parts = []
    for (pat, chg, dchg), cnt in sorted(bucket.items(), key=lambda x: -x[1]):
        color, _ = _block_color(pat)
        crate_label = ""
        if chg or dchg:
            crate_label = (f' <span style="color:#666;font-size:0.92em">'
                           f'{chg or "·"}/{dchg or "·"}</span>')
        parts.append(
            f'<span class="pill" style="background:{color}22;'
            f'border-left:3px solid {color}">{html.escape(pat)}{crate_label} '
            f'<b>{cnt}</b></span>'
        )
    return " ".join(parts)


def discover_all_datasets(root: Path) -> list[tuple[str, Path]]:
    """[(category, dataset_path), ...] 정렬 리스트 반환."""
    out = []
    for cat_path in sorted(root.iterdir()):
        if not cat_path.is_dir():
            continue
        for ds_path in sorted(cat_path.iterdir()):
            if not ds_path.is_dir():
                continue
            out.append((cat_path.name, ds_path))
    return out


FINDINGS_HTML = """
<section class="findings">
<h2>📋 사용자 보고 사례 진단 (260510)</h2>
<div class="finding-grid">
  <div class="finding bad">
    <h4>① GITT 방향 미구분</h4>
    <p><b>대상</b>: 240821 GITT (성능)</p>
    <p><b>현상</b>: TC 5-214 (210 cy) 단일 <code>GITT(full)</code> 블록</p>
    <p><b>원인</b>: <code>_merge_pulse_groups</code>(proto_:6732)이 인접 charge/discharge pulse 그룹을 단일 GITT TC로 페어링하면서 direction 정보 소실</p>
    <p><b>개선</b>: pulse 그룹 merge 시 <code>action</code> 추적 →
      <code>GITT(charge)</code>/<code>GITT(discharge)</code>/<code>GITT(full)</code> 3분기.
      색상은 동일 idx=3 유지하되 명도/패턴으로 구분</p>
  </div>
  <div class="finding warn">
    <h4>② SOC별 사이클 동일 표시</h4>
    <p><b>대상</b>: 240919 SOC별DCIR (성능)</p>
    <p><b>현상</b>: TC 7-26 (20cy) + TC 72-96 (25cy) 두 SOC별 사이클 블록이 시각적으로 동일</p>
    <p><b>실체</b>: 정상 — 각각 가속수명 전(cy~6)·후(cy~96) SOC별 DCIR 측정 단계</p>
    <p><b>개선</b>: C-rate / 측정 시점 sub-tag 추가
      (예 <code>SOC별 사이클(전)</code> / <code>SOC별 사이클(후)</code>)
      또는 가속수명 idx 와의 위치 관계로 자동 라벨링</p>
  </div>
  <div class="finding bad">
    <h4>③ 보관 setup → 히스테리시스 오분류</h4>
    <p><b>대상</b>: 260109 보관 4cycle SOC30 setting (성능)</p>
    <p><b>현상</b>: TC 6 (n_chg=1, n_dchg=0, SOC 30 충전) → <code>히스테리시스(충방전)</code></p>
    <p><b>원인</b>: schedule rule 5 (proto_:9387) <code>HYSTERESIS_CHG</code> = N=1 + ref_step_chg.
      SOC setup 충전도 ref_step 사용 → 오매칭</p>
    <p><b>개선</b>: HYSTERESIS_CHG 추가 가드 — 그룹 페어 (HYSTERESIS_DCHG 인접) 또는
      multi-cycle (N≥2) 또는 후속 long-rest 부재 등 컨텍스트 검증</p>
  </div>
  <div class="finding ok">
    <h4>④ 성능_hysteresis 카테고리 ✓</h4>
    <p>현재 카테고리 분리 양호 — 사용자 컨펌</p>
  </div>
</div>
<div class="feature-req">
  <h4>💡 신규 기능 요청 — C-rate 기반 사이클 구분</h4>
  <p>각 사이클 충/방전 C-rate 정보 추가 (이번 빌드 적용 ✓):</p>
  <ul>
    <li>블록 마우스오버 툴팁: <code>충전 1.00C / 방전 0.50C</code></li>
    <li>패턴 pill: <code>가속수명 1.00C/0.50C</code> 처럼 동일 카테고리도 C-rate별로 분리 표시</li>
    <li>출처: <code>meta.tc_info[tc].chg_crate / dchg_crate</code> (median over block range)</li>
    <li>향후: 분류기 자체에서 C-rate 임계로 가속수명(≥0.5C) vs RPT(≤0.3C) 자동 구분</li>
  </ul>
</div>
</section>
"""


def render_html(records: list[dict], total_elapsed: float) -> str:
    """records → 단일 HTML."""
    by_cat: dict[str, list[dict]] = {}
    for r in records:
        by_cat.setdefault(r["category"], []).append(r)

    cat_summary = []
    for cat, rows in by_cat.items():
        ok = sum(1 for r in rows if r["blocks"])
        total = len(rows)
        cat_summary.append(f"<b>{html.escape(cat)}</b> {ok}/{total}")

    legend_items = []
    seen_idx = set()
    for pat, info in CLASSIFIED_COLORS.items():
        idx = info.get("color_idx", 9)
        if idx in seen_idx:
            continue
        seen_idx.add(idx)
        color = PALETTE[idx % len(PALETTE)]
        legend_items.append(
            f'<span class="leg-item"><span class="sw" style="background:{color}"></span>'
            f'{html.escape(info.get("desc", pat))}</span>'
        )

    body_parts = []
    for cat in sorted(by_cat.keys()):
        rows = by_cat[cat]
        body_parts.append(f'<section class="cat"><h2>{html.escape(cat)} '
                          f'<span class="cat-cnt">({len(rows)} datasets)</span></h2>')
        body_parts.append('<div class="ds-list">')
        for r in rows:
            ds = html.escape(r["dataset"])
            cycler = r["cycler"]
            ch = html.escape(r["channel"]) if r["channel"] else "—"
            mtc = r["max_tc"] or 0
            blocks = r["blocks"]
            err = r.get("error")
            cyc_class = f"cycler-{cycler.lower()}" if cycler else "cycler-x"

            bar_html = _render_blocks_html(blocks, mtc) if blocks else (
                f'<div class="bar empty">{html.escape(err) if err else "분석 불가"}</div>'
            )
            pills = _render_summary_pills(blocks)

            body_parts.append(
                f'<div class="ds">'
                f'<div class="ds-head">'
                f'<span class="cycler {cyc_class}">{html.escape(cycler or "?")}</span>'
                f'<span class="ds-name" title="{ds}">{ds}</span>'
                f'<span class="meta">ch <code>{ch}</code> · TC <b>{mtc}</b>'
                f' · blocks <b>{len(blocks)}</b></span>'
                f'</div>'
                f'{bar_html}'
                f'<div class="pills">{pills}</div>'
                f'</div>'
            )
        body_parts.append("</div></section>")

    css = """
    :root{
      --c-bg:#fafbfc; --c-fg:#1c2026; --c-mute:#5b6573; --c-line:#e3e7ee;
      --c-accent:#3C5488; --c-card:#ffffff;
    }
    *{box-sizing:border-box}
    html,body{margin:0;padding:0;background:var(--c-bg);color:var(--c-fg);
      font-family:"Pretendard","Apple SD Gothic Neo","맑은 고딕",sans-serif;
      font-size:13px; line-height:1.5}
    .wrap{max-width:1400px; margin:0 auto; padding:24px}
    header.top{border-bottom:2px solid var(--c-accent); padding-bottom:12px; margin-bottom:18px}
    header.top h1{margin:0; font-size:1.55em; color:var(--c-accent)}
    header.top .sub{color:var(--c-mute); font-size:0.92em; margin-top:5px}
    .summary{background:#fff; border:1px solid var(--c-line); border-radius:8px;
      padding:10px 16px; margin-bottom:14px; font-size:0.95em}
    .summary b{color:var(--c-accent)}
    .legend{display:flex; flex-wrap:wrap; gap:6px; padding:8px 0; margin-bottom:18px}
    .leg-item{display:inline-flex; align-items:center; gap:4px; font-size:0.78em;
      background:#fff; padding:2px 8px; border-radius:10px; border:1px solid var(--c-line)}
    .sw{width:11px; height:11px; border-radius:2px; display:inline-block}
    section.cat{margin:22px 0; background:#fff; border-radius:8px; padding:12px 16px;
      border:1px solid var(--c-line)}
    section.cat h2{margin:0 0 12px; font-size:1.15em; color:var(--c-accent);
      border-bottom:1px solid var(--c-line); padding-bottom:6px}
    .cat-cnt{font-size:0.7em; color:var(--c-mute); font-weight:400}
    .ds-list{display:flex; flex-direction:column; gap:8px}
    .ds{padding:6px 0 7px; border-bottom:1px dashed var(--c-line)}
    .ds:last-child{border-bottom:none}
    .ds-head{display:flex; align-items:center; gap:8px; margin-bottom:3px;
      font-size:0.86em; flex-wrap:wrap}
    .cycler{display:inline-block; padding:1px 7px; border-radius:9px;
      font-size:0.74em; font-weight:600}
    .cycler-pne{background:#dde7f7; color:#234478}
    .cycler-toyo{background:#fce7df; color:#9a3a23}
    .cycler-x{background:#ddd; color:#555}
    .ds-name{flex:1; font-weight:500; color:var(--c-fg);
      white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:780px}
    .meta{color:var(--c-mute); font-size:0.86em}
    .meta b{color:var(--c-fg); font-weight:600}
    .meta code{font-family:"D2Coding","Consolas",monospace; font-size:0.95em}
    .bar{display:flex; height:14px; border:1px solid #c8cfdc; border-radius:2px;
      overflow:hidden; background:#f3f4f7; margin-top:2px}
    .bar.empty{justify-content:center; align-items:center; color:#9aa3b3;
      font-size:0.78em; font-style:italic; background:#fafbfc}
    .seg{height:100%; display:inline-block; opacity:0.92}
    .seg:hover{opacity:1; outline:1px solid rgba(0,0,0,0.3)}
    .pills{margin-top:4px; display:flex; flex-wrap:wrap; gap:3px}
    .pill{display:inline-block; padding:1px 7px; border-radius:9px;
      font-size:0.7em; color:#222}
    .pill b{font-weight:600}
    section.findings{background:#fff; border:1px solid var(--c-line);
      border-radius:8px; padding:12px 18px; margin-bottom:18px}
    section.findings h2{margin:0 0 10px; font-size:1.05em; color:var(--c-accent)}
    .finding-grid{display:grid; grid-template-columns:repeat(2,1fr);
      gap:10px; margin:8px 0}
    .finding{background:#fafbfc; border-left:4px solid #ccc;
      border-radius:6px; padding:8px 12px; font-size:0.86em}
    .finding h4{margin:0 0 4px; font-size:0.95em; color:#222}
    .finding.bad{border-left-color:#E64B35; background:#fdf3f0}
    .finding.warn{border-left-color:#F39B7F; background:#fef7f1}
    .finding.ok{border-left-color:#00A087; background:#eff8f5}
    .finding p{margin:2px 0}
    .feature-req{background:#eef6f4; border-left:4px solid #00A087;
      border-radius:6px; padding:8px 14px; margin-top:10px; font-size:0.86em}
    .feature-req h4{margin:0 0 4px}
    """

    head = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8">
<title>exp_data 사이클 타임라인 — 전수 시각화 v2 (C-rate)</title>
<style>{css}</style></head><body><div class="wrap">
<header class="top">
  <h1>exp_data 사이클 타임라인 — 전수 시각화 <span style="font-size:0.6em;color:#888">v2</span></h1>
  <div class="sub">대표 채널(max_tc 최대) classified 기반 타임라인 블록 ·
    {len(records)} datasets · 처리시간 {total_elapsed:.1f}s ·
    <b>C-rate 정보 통합</b> (블록 툴팁·pill) ·
    BDT proto_ <code>_build_channel_meta</code> 사용</div>
</header>
{FINDINGS_HTML}
<div class="summary">{' · '.join(cat_summary)}</div>
<div class="legend">{''.join(legend_items)}</div>
"""
    return head + "\n".join(body_parts) + "</div></body></html>"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=r"C:/Users/Ryu/battery/python/BDT_dev/raw/raw_exp/exp_data",
        help="exp_data 루트 경로",
    )
    parser.add_argument(
        "--out",
        default=str(ROOT / "docs" / "code" / "02_레퍼런스" /
                    "260510_exp_data_cycle_timelines.html"),
        help="출력 HTML 경로",
    )
    parser.add_argument("--limit", type=int, default=0,
                        help="처리할 dataset 수 제한 (0=전수)")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        print(f"[ERR] root 없음: {root}")
        return 1

    datasets = discover_all_datasets(root)
    if args.limit > 0:
        datasets = datasets[: args.limit]
    print(f"[INFO] dataset {len(datasets)}개 발견 — 처리 시작")

    records = []
    t0 = time.time()
    for i, (cat, ds_path) in enumerate(datasets):
        ds_name = ds_path.name
        rec = {
            "category": cat, "dataset": ds_name, "cycler": "",
            "channel": "", "max_tc": 0, "blocks": [], "error": "",
        }
        try:
            channels = _find_channels(ds_path)
            if not channels:
                rec["error"] = "채널 폴더 없음"
                records.append(rec)
                continue
            best_ch, meta = _pick_best_channel(channels)
            if meta is None:
                rec["error"] = "meta 빌드 실패 (모든 채널)"
                rec["cycler"] = "PNE" if _is_pne_dataset(ds_path) else "Toyo"
                records.append(rec)
                continue
            rec["channel"] = best_ch.name if best_ch else ""
            rec["cycler"] = "PNE" if meta.is_pne else "Toyo"
            rec["max_tc"] = meta.max_tc or 0
            rec["blocks"] = _build_blocks_for_meta(meta)
        except Exception as e:
            rec["error"] = f"{type(e).__name__}: {e}"
            traceback.print_exc()
        records.append(rec)
        if (i + 1) % 10 == 0 or (i + 1) == len(datasets):
            elapsed = time.time() - t0
            print(f"  [{i+1}/{len(datasets)}] {elapsed:.1f}s  "
                  f"{cat}/{ds_name[:50]}")

    elapsed = time.time() - t0

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html_text = render_html(records, elapsed)
    out_path.write_text(html_text, encoding="utf-8")
    print(f"[OK] {out_path}  ({len(records)} datasets, {elapsed:.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
