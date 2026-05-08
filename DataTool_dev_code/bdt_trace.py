"""BDT trace 모듈 — dev-only 계측 인프라.

`DataTool_optRCD_proto_.py` (monolith) 에서 분리된 trace/snapshot/timing
인프라. 환경변수 `BDT_TRACE` 가 설정된 경우에만 monolith 의 stub 들을
monkey-patch 로 교체해 다음 산출물을 생성한다:

    {trace_dir}/session_<TS>/
      ├── step.csv                  -- 행=한 sub-step (raw timing/shape data)
      ├── step_summary.md           -- 사람용 요약 (top-N hotspot, 캐시 통계)
      ├── step_hotspot.png          -- stage 별 가로 막대 차트
      └── NNN_<stage>_<tag>.pkl     -- 기존 _debug_snapshot pickle (stage 별)

활성화 메커니즘
---------------
1. monolith 가 시작 시 `try: import bdt_trace; bdt_trace.activate(...)` 호출
2. 환경변수 `BDT_TRACE` 미설정이면 즉시 return (인프라 dormant)
3. 설정되어 있으면 monolith 의 다음 stub 을 실체로 교체:
   - `log_perf` (decorator)
   - `PerfSection` (context manager)
   - `_debug_snapshot` (snapshot saver)
   - `_trace_substep` (sub-step measurement context)
4. 종료 시 `atexit` 훅이 step.csv → step_summary.md → step_hotspot.png 자동 생성

PyInstaller 빌드 격리
---------------------
이 파일은 `--exclude-module bdt_trace` 로 빌드에서 제외된다. 빌드된 exe 는
`try-import` 실패로 자동 dormant 모드 (stub 만 동작). 빌드 산출물 사이즈
영향 0.

환경변수
--------
- `BDT_TRACE=1`         -- 활성화 (값은 truthy 면 OK)
- `BDT_TRACE_DIR=<path>` -- trace 디렉토리 (기본: <BDT_dev 부모>/bdt_trace,
                            결정 실패 시 C:\\tmp\\bdt_trace 폴백.
                            사내 빌드 폴더 (..\\build\\) 와 동등 레벨.)
- `BDT_TRACE_LEVEL=stage|substep`
                        -- stage: Stage 단위만 (기본)
                        -- substep: Stage + sub-step 모두

사용 예
-------
    set BDT_TRACE=1
    set BDT_TRACE_LEVEL=substep
    python DataTool_optRCD_proto_.py

또는 노트북에서:

    import os
    os.environ['BDT_TRACE'] = '1'
    os.environ['BDT_TRACE_LEVEL'] = 'substep'
    import DataTool_optRCD_proto_  # 모듈 로드 시점에 자동 activate
"""
from __future__ import annotations

import atexit
import csv
import functools
import inspect
import logging
import os
import pickle
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

# 외부 의존성 (monolith 가 이미 import 한 것만 — 추가 설치 0)
try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import matplotlib
    matplotlib.use("Agg")  # 헤드리스 안전
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


# ── 모듈 상태 ─────────────────────────────────────────────────────
_LOGGER = logging.getLogger("BDT.trace")
_ACTIVE: bool = False
_LEVEL: str = "stage"  # "stage" | "substep"
_TRACE_DIR: str = ""   # activate() 시점에 _resolve_default_trace_dir 로 결정
_SESSION: str | None = None
_SESSION_DIR: str | None = None
_RECORDS: list[dict] = []
_SNAPSHOT_COUNTER: int = 0
_PERF_LOGGER = None  # monolith 의 _perf_logger 참조 (activate 시점에 주입)


def _resolve_default_trace_dir(monolith_module=None) -> str:
    """trace 기본 디렉토리 — build 폴더와 동등 레벨 (BDT_dev 부모/bdt_trace).

    사내환경 빌드 (`build_exe_onepath.bat` 의 `..\\build\\`) 와 같은 위치
    체계로 — `<BDT_dev 부모>/bdt_trace/` 사용. 결정 실패 시 C:\\tmp 폴백.
    """
    try:
        if monolith_module is not None and hasattr(monolith_module, '__file__'):
            monolith_path = Path(monolith_module.__file__).resolve()
            # monolith 위치: <root>/BDT_dev/DataTool_dev_code/DataTool_optRCD_proto_.py
            # parents[0]=DataTool_dev_code, [1]=BDT_dev, [2]=<root> (build 폴더와 동등)
            return str(monolith_path.parents[2] / 'bdt_trace')
    except Exception:
        pass
    return r"C:\tmp\bdt_trace"


# ── 데이터 모델 ────────────────────────────────────────────────────
@dataclass
class _StepRecord:
    seq: int
    kind: str          # 'func' | 'section' | 'substep' | 'snapshot'
    stage: str
    sub_step: str
    t_start_iso: str
    elapsed_ms: float
    rows_in: int = -1
    rows_out: int = -1
    bytes_delta: int = 0
    cache_hit: str = ""        # 'hit' | 'miss' | ''
    n_files: int = -1
    raw_path_short: str = ""
    options_hash: str = ""
    extra: dict = field(default_factory=dict)

    def to_csv_row(self) -> dict:
        row = {
            "seq": self.seq, "kind": self.kind,
            "stage": self.stage, "sub_step": self.sub_step,
            "t_start_iso": self.t_start_iso, "elapsed_ms": f"{self.elapsed_ms:.3f}",
            "rows_in": self.rows_in, "rows_out": self.rows_out,
            "bytes_delta": self.bytes_delta, "cache_hit": self.cache_hit,
            "n_files": self.n_files, "raw_path_short": self.raw_path_short,
            "options_hash": self.options_hash,
        }
        # extra 는 직렬화 안전한 값만 쉼표 → 세미콜론으로
        if self.extra:
            row["extra"] = "; ".join(
                f"{k}={v}".replace(",", ";") for k, v in self.extra.items())
        else:
            row["extra"] = ""
        return row


# ── 활성화 ─────────────────────────────────────────────────────────
def activate(monolith_module) -> None:
    """monolith 의 stub 들을 실체로 교체. 환경변수 미설정 시 즉시 return."""
    global _ACTIVE, _LEVEL, _TRACE_DIR, _SESSION, _SESSION_DIR, _PERF_LOGGER

    if not os.environ.get("BDT_TRACE"):
        return  # dormant — stub 그대로

    _ACTIVE = True
    _LEVEL = os.environ.get("BDT_TRACE_LEVEL", "stage").lower()
    if _LEVEL not in ("stage", "substep"):
        _LEVEL = "stage"
    # 우선순위: BDT_TRACE_DIR 환경변수 > monolith 위치 기준 default > C:\tmp 폴백
    _TRACE_DIR = (os.environ.get("BDT_TRACE_DIR")
                  or _resolve_default_trace_dir(monolith_module))
    _SESSION = time.strftime("session_%Y%m%d_%H%M%S")
    _SESSION_DIR = os.path.join(_TRACE_DIR, _SESSION)
    os.makedirs(_SESSION_DIR, exist_ok=True)

    # monolith 의 logger 재사용 (콘솔 라인 통일)
    _PERF_LOGGER = getattr(monolith_module, "_perf_logger", None) or _LOGGER

    # ── 콜백 등록 (log_perf / PerfSection: 이미 데코레이터/컨텍스트가
    # 22 함수 / 3 구간에 wrap 된 상태라 monkey-patch 로는 영향 못 줌.
    # monolith stub 의 _trace_func_callbacks / _trace_section_callbacks 에
    # 측정 콜백을 추가하면 매 호출마다 콜백 실행됨.)
    monolith_module._trace_func_callbacks.append(_record_func_call)
    monolith_module._trace_section_callbacks.append(_record_section_call)

    # ── monkey-patch (호출 시점 module attribute lookup 됨 → patch 통함) ──
    monolith_module._debug_snapshot = _real_debug_snapshot
    monolith_module._trace_substep = _real_trace_substep
    # 변수 동기화 (기존 _DEBUG_PROFILE_TRACE=True 로 작동했던 경로 호환)
    monolith_module._DEBUG_PROFILE_TRACE = True
    monolith_module._DEBUG_TRACE_DIR = _TRACE_DIR
    monolith_module._DEBUG_TRACE_SESSION = _SESSION

    _PERF_LOGGER.info(
        f"[bdt_trace] ACTIVE level={_LEVEL} session={_SESSION_DIR}")

    # 종료 훅 — step.csv/md/png 일괄 생성
    atexit.register(_finalize)


# ── 콜백: monolith stub log_perf/PerfSection 이 매 호출 후 부름 ───
def _record_func_call(name: str, t_iso: str, elapsed_ms: float,
                      ok: bool, exc_name: str | None) -> None:
    """log_perf 콜백 — 함수 timing + 콘솔 로그 + step.csv 기록."""
    if _PERF_LOGGER:
        if ok:
            _PERF_LOGGER.info(f"◀ {name} 완료  [{elapsed_ms/1000:.3f}s]")
        else:
            _PERF_LOGGER.error(
                f"✖ {name} 실패  [{elapsed_ms/1000:.3f}s] {exc_name}")
    extra = {"exc": exc_name} if exc_name else {}
    _record(_StepRecord(
        seq=len(_RECORDS), kind="func", stage=name, sub_step="ERROR" if not ok else "",
        t_start_iso=t_iso, elapsed_ms=elapsed_ms, extra=extra))


def _record_section_call(label: str, t_iso: str, elapsed_ms: float,
                          ctx: dict) -> None:
    """PerfSection 콜백 — 구간 timing + 콘솔 + step.csv 기록."""
    if _PERF_LOGGER:
        parts = [f"{k}={v}" for k, v in ctx.items()]
        ctx_str = f"  ({', '.join(parts)})" if parts else ""
        _PERF_LOGGER.info(f"  └ {label}{ctx_str}  [{elapsed_ms/1000:.3f}s]")
    _record(_StepRecord(
        seq=len(_RECORDS), kind="section", stage=label, sub_step="",
        t_start_iso=t_iso, elapsed_ms=elapsed_ms,
        extra={k: str(v) for k, v in ctx.items()}))


def is_active() -> bool:
    return _ACTIVE


# ── 실체 함수: log_perf 데코레이터 ────────────────────────────────
def _real_log_perf(func):
    """monolith 의 stub log_perf 를 교체. 함수 단위 timing + 콘솔 + step.csv 기록."""
    _n_params = len(inspect.signature(func).parameters)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        trimmed = args[:_n_params]
        name = func.__qualname__
        if _PERF_LOGGER:
            _PERF_LOGGER.info(f"▶ {name} 시작")
        t0 = time.perf_counter()
        t_iso = time.strftime("%H:%M:%S")
        try:
            result = func(*trimmed, **kwargs)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            if _PERF_LOGGER:
                _PERF_LOGGER.info(f"◀ {name} 완료  [{elapsed_ms/1000:.3f}s]")
            _record(_StepRecord(
                seq=len(_RECORDS), kind="func", stage=name, sub_step="",
                t_start_iso=t_iso, elapsed_ms=elapsed_ms))
            return result
        except Exception as e:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            if _PERF_LOGGER:
                _PERF_LOGGER.error(
                    f"✖ {name} 실패  [{elapsed_ms/1000:.3f}s] "
                    f"{type(e).__name__}: {e}")
            _record(_StepRecord(
                seq=len(_RECORDS), kind="func", stage=name, sub_step="ERROR",
                t_start_iso=t_iso, elapsed_ms=elapsed_ms,
                extra={"exc": type(e).__name__}))
            raise

    return wrapper


# ── 실체 클래스: PerfSection 컨텍스트 ──────────────────────────────
class _RealPerfSection:
    """monolith 의 stub PerfSection 을 교체. 구간 timing + step.csv 기록."""
    def __init__(self, label, **ctx):
        self.label = label
        self.ctx = ctx

    def __enter__(self):
        parts = [f"{k}={v}" for k, v in self.ctx.items()]
        ctx_str = f"  ({', '.join(parts)})" if parts else ""
        if _PERF_LOGGER:
            _PERF_LOGGER.info(f"  ┌ {self.label}{ctx_str}")
        self._t0 = time.perf_counter()
        self._t_iso = time.strftime("%H:%M:%S")
        return self

    def __exit__(self, *exc):
        elapsed_ms = (time.perf_counter() - self._t0) * 1000
        if _PERF_LOGGER:
            _PERF_LOGGER.info(f"  └ {self.label}  [{elapsed_ms/1000:.3f}s]")
        _record(_StepRecord(
            seq=len(_RECORDS), kind="section", stage=self.label, sub_step="",
            t_start_iso=self._t_iso, elapsed_ms=elapsed_ms,
            extra={k: str(v) for k, v in self.ctx.items()}))
        return False


# ── 실체 함수: _debug_snapshot ────────────────────────────────────
def _real_debug_snapshot(obj, stage: str, tag: str = "") -> None:
    """Stage 끝 DataFrame 을 pickle 로 저장 + shape/columns 메타 기록."""
    global _SNAPSHOT_COUNTER
    if not _ACTIVE:
        return
    try:
        seq = _SNAPSHOT_COUNTER
        _SNAPSHOT_COUNTER += 1
        fname = os.path.join(
            _SESSION_DIR,
            f"{seq:03d}_{stage}_{tag}.pkl" if tag else f"{seq:03d}_{stage}.pkl")
        payload: dict = {"stage": stage, "tag": tag, "ts": time.time()}
        rows = -1
        if pd is not None and isinstance(obj, pd.DataFrame):
            payload["shape"] = obj.shape
            payload["columns"] = list(obj.columns)
            payload["dtypes"] = {c: str(obj[c].dtype) for c in obj.columns}
            payload["head"] = obj.head(30).copy()
            payload["df"] = obj.copy()
            rows = obj.shape[0]
        else:
            payload["obj"] = obj
        with open(fname, "wb") as f:
            pickle.dump(payload, f)
        _record(_StepRecord(
            seq=len(_RECORDS), kind="snapshot",
            stage=stage, sub_step=tag,
            t_start_iso=time.strftime("%H:%M:%S"),
            elapsed_ms=0.0, rows_out=rows,
            extra={"file": os.path.basename(fname)}))
    except Exception as ex:
        if _PERF_LOGGER:
            _PERF_LOGGER.warning(f"[bdt_trace.snapshot] {stage}/{tag}: {ex}")


# ── 실체 컨텍스트: _trace_substep ────────────────────────────────
@contextmanager
def _real_trace_substep(stage: str, sub_step: str, **ctx):
    """Stage 내부 sub-step 측정. BDT_TRACE_LEVEL=stage 면 no-op.

    사용 예:
        with _trace_substep('S2_load_raw', 'cyc_attempt',
                            tc_min=tc_min, tc_max=tc_max) as t:
            df = _try_cyc_profile(...)
            t.set_rows_out(len(df) if df is not None else 0)
            t.set_cache(_cache_hit)
    """
    if _LEVEL != "substep":
        # stage 레벨 — sub-step 측정 안 함
        yield _NoOpSubstep()
        return

    rec_holder = _SubstepHolder(stage=stage, sub_step=sub_step, ctx=ctx)
    t0 = time.perf_counter()
    rec_holder._t_iso = time.strftime("%H:%M:%S")
    try:
        yield rec_holder
    finally:
        rec_holder._elapsed_ms = (time.perf_counter() - t0) * 1000
        _record(_StepRecord(
            seq=len(_RECORDS), kind="substep",
            stage=stage, sub_step=sub_step,
            t_start_iso=rec_holder._t_iso,
            elapsed_ms=rec_holder._elapsed_ms,
            rows_in=rec_holder._rows_in, rows_out=rec_holder._rows_out,
            cache_hit=rec_holder._cache_hit, n_files=rec_holder._n_files,
            raw_path_short=rec_holder._raw_path_short,
            extra={**ctx, **rec_holder._extra}))


class _NoOpSubstep:
    def set_rows_in(self, n): pass
    def set_rows_out(self, n): pass
    def set_cache(self, status): pass
    def set_n_files(self, n): pass
    def set_path(self, p): pass
    def set_extra(self, **kw): pass


class _SubstepHolder:
    def __init__(self, stage, sub_step, ctx):
        self.stage = stage
        self.sub_step = sub_step
        self.ctx = ctx
        self._rows_in = -1
        self._rows_out = -1
        self._cache_hit = ""
        self._n_files = -1
        self._raw_path_short = ""
        self._extra = {}
        self._t_iso = ""
        self._elapsed_ms = 0.0

    def set_rows_in(self, n: int): self._rows_in = int(n)
    def set_rows_out(self, n: int): self._rows_out = int(n)
    def set_cache(self, status: str): self._cache_hit = status
    def set_n_files(self, n: int): self._n_files = int(n)

    def set_path(self, p: str):
        try:
            self._raw_path_short = os.path.basename(str(p)) or str(p)[-40:]
        except Exception:
            self._raw_path_short = str(p)[-40:]

    def set_extra(self, **kw): self._extra.update(kw)


# ── 기록 ──────────────────────────────────────────────────────────
def _record(rec: _StepRecord) -> None:
    if not _ACTIVE:
        return
    _RECORDS.append(rec.to_csv_row())


# ── 종료 훅: step.csv / step_summary.md / step_hotspot.png ────────
def _finalize() -> None:
    if not _ACTIVE or not _RECORDS:
        return
    try:
        _write_step_csv()
        _write_summary_md()
        _write_hotspot_png()
        if _PERF_LOGGER:
            _PERF_LOGGER.info(f"[bdt_trace] FINALIZED → {_SESSION_DIR}")
    except Exception as ex:
        if _PERF_LOGGER:
            _PERF_LOGGER.warning(f"[bdt_trace.finalize] {ex}")


def _write_step_csv() -> None:
    path = os.path.join(_SESSION_DIR, "step.csv")
    if not _RECORDS:
        return
    cols = list(_RECORDS[0].keys())
    # 모든 행이 동일 키 갖도록 정규화
    all_keys = set()
    for r in _RECORDS:
        all_keys.update(r.keys())
    cols = ["seq", "kind", "stage", "sub_step", "t_start_iso", "elapsed_ms",
            "rows_in", "rows_out", "bytes_delta", "cache_hit", "n_files",
            "raw_path_short", "options_hash", "extra"]
    cols = [c for c in cols if c in all_keys]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(_RECORDS)


def _write_summary_md() -> None:
    if pd is None:
        _write_summary_md_text()
        return
    path = os.path.join(_SESSION_DIR, "step_summary.md")
    df = pd.DataFrame(_RECORDS)
    if df.empty:
        return
    df["elapsed_ms"] = df["elapsed_ms"].astype(float)

    # 총 시간 (kind=='func' 의 합 or section 의 합 중 큰 쪽)
    total_func = df.loc[df["kind"] == "func", "elapsed_ms"].sum()
    total_section = df.loc[df["kind"] == "section", "elapsed_ms"].sum()
    total_substep = df.loc[df["kind"] == "substep", "elapsed_ms"].sum()
    total = max(total_func, total_section, total_substep)
    if total <= 0:
        total = df["elapsed_ms"].sum() or 1.0

    # Top-10 hotspot (substep 우선, 없으면 func)
    target_kind = "substep" if (df["kind"] == "substep").any() else "func"
    hot = (df[df["kind"] == target_kind]
           .nlargest(10, "elapsed_ms")
           [["stage", "sub_step", "elapsed_ms"]]
           .copy())
    hot["pct"] = (hot["elapsed_ms"] / total * 100).round(1)

    # Stage 별 집계
    by_stage = (df[df["kind"].isin(["func", "section", "substep"])]
                .groupby("stage")["elapsed_ms"]
                .agg(["sum", "count"])
                .sort_values("sum", ascending=False))
    by_stage["pct"] = (by_stage["sum"] / total * 100).round(1)

    # 캐시 통계
    cache_stats = df.loc[df["cache_hit"].astype(str).isin(["hit", "miss"]),
                         "cache_hit"].value_counts().to_dict()

    # snapshot 추적 (stage → row 수 흐름)
    snap = df[df["kind"] == "snapshot"][
        ["stage", "sub_step", "rows_out"]].copy()

    lines = []
    lines.append(f"# BDT trace summary — {_SESSION}\n")
    lines.append(f"- 디렉토리: `{_SESSION_DIR}`")
    lines.append(f"- 레벨: `{_LEVEL}` (stage|substep)")
    lines.append(f"- 총 측정 행: {len(df)}\n")

    lines.append("## 총 시간 분해\n")
    lines.append("| 종류 | 합계 (ms) | 비고 |")
    lines.append("|---|---:|---|")
    lines.append(f"| 함수 (`@log_perf`) | {total_func:.1f} | "
                 f"{(df['kind']=='func').sum()} 호출 |")
    lines.append(f"| 구간 (`PerfSection`) | {total_section:.1f} | "
                 f"{(df['kind']=='section').sum()} 호출 |")
    lines.append(f"| sub-step | {total_substep:.1f} | "
                 f"{(df['kind']=='substep').sum()} 호출 |")
    lines.append("")

    lines.append("## Hotspot (Top 10)\n")
    if not hot.empty:
        lines.append("| rank | stage | sub_step | elapsed (ms) | % of total |")
        lines.append("|---:|---|---|---:|---:|")
        for i, row in enumerate(hot.itertuples(), 1):
            lines.append(f"| {i} | {row.stage} | {row.sub_step} | "
                         f"{row.elapsed_ms:.1f} | {row.pct} |")
    else:
        lines.append("(데이터 없음)")
    lines.append("")

    lines.append("## Stage 별 누적\n")
    lines.append("| stage | sum (ms) | n | % |")
    lines.append("|---|---:|---:|---:|")
    for stage, row in by_stage.head(20).iterrows():
        lines.append(f"| {stage} | {row['sum']:.1f} | "
                     f"{int(row['count'])} | {row['pct']} |")
    lines.append("")

    lines.append("## 캐시 통계\n")
    if cache_stats:
        for k, v in cache_stats.items():
            lines.append(f"- {k}: {v}")
    else:
        lines.append("- 측정된 캐시 hit/miss 없음")
    lines.append("")

    lines.append("## 데이터 shape 변화 (snapshot)\n")
    if not snap.empty:
        lines.append("| stage | tag | rows_out |")
        lines.append("|---|---|---:|")
        for _, row in snap.iterrows():
            lines.append(f"| {row['stage']} | {row['sub_step']} | "
                         f"{row['rows_out']} |")
    else:
        lines.append("(snapshot 없음 — `_DEBUG_PROFILE_TRACE` 호출이 없었음)")
    lines.append("")

    lines.append("## 최적화 후보\n")
    if not hot.empty:
        top1 = hot.iloc[0]
        lines.append(f"- **Top hotspot**: `{top1['stage']} / "
                     f"{top1['sub_step']}` — {top1['elapsed_ms']:.1f} ms "
                     f"({top1['pct']}%). 캐시화·병렬화·alg 변경 후보 검토.")
        if cache_stats.get("miss", 0) > cache_stats.get("hit", 0):
            lines.append("- 캐시 miss > hit — TTL/key 정책 재검토.")
    lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _write_summary_md_text() -> None:
    """pandas 미가용 시 fallback — 단순 텍스트 요약."""
    path = os.path.join(_SESSION_DIR, "step_summary.md")
    lines = [f"# BDT trace summary — {_SESSION}",
             f"- 디렉토리: `{_SESSION_DIR}`",
             f"- 총 행: {len(_RECORDS)}",
             "(pandas 미설치 — 상세 요약 생략)"]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _write_hotspot_png() -> None:
    if plt is None or pd is None:
        return
    path = os.path.join(_SESSION_DIR, "step_hotspot.png")
    df = pd.DataFrame(_RECORDS)
    if df.empty:
        return
    df["elapsed_ms"] = df["elapsed_ms"].astype(float)

    target_kind = "substep" if (df["kind"] == "substep").any() else "func"
    hot = (df[df["kind"] == target_kind]
           .nlargest(15, "elapsed_ms")
           .copy())
    if hot.empty:
        return
    labels = [f"{r.stage} / {r.sub_step}" if r.sub_step else r.stage
              for r in hot.itertuples()]
    fig, ax = plt.subplots(figsize=(10, max(4, len(hot) * 0.32)))
    ax.barh(range(len(hot)), hot["elapsed_ms"].values, color="#3C5488")
    ax.set_yticks(range(len(hot)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("elapsed (ms)")
    ax.set_title(f"BDT trace hotspot — {target_kind} (Top {len(hot)})")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


# ── monolith 가 BDT_TRACE 미설정 시 호출하는 stub 들 ─────────────
# (참고용 — monolith 안에 동일한 stub 이 직접 정의되어 있음. 여기 정의는
#  bdt_trace.py 단독 import 시 type hint/IDE 보조용.)
def _stub_log_perf(func): return func


class _StubPerfSection:
    def __init__(self, *a, **kw): pass
    def __enter__(self): return self
    def __exit__(self, *exc): return False


def _stub_debug_snapshot(*a, **kw): pass


@contextmanager
def _stub_trace_substep(*a, **kw):
    yield _NoOpSubstep()
