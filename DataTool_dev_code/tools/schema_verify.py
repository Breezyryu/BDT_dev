"""schema_verify.py — SaveEndData 컬럼 스키마 추정값을 실측으로 검증.

사용자가 제공한 컬럼 의미는 추정이므로, exp_data 하위의 여러 채널에서
SaveEndData.csv를 수집하여:
  1) 각 컬럼의 값 분포 집계
  2) 사용자 추정 범주값과 비교
  3) 컬럼 간 상관관계로 의미 추론
  4) 수치 단위 추정 (mV/uV, mA/uA 등)

출력: 검증 리포트 (각 컬럼별 OK/의심/반증 상태).
"""
from __future__ import annotations

import os
import sys
from collections import Counter, defaultdict
from typing import Optional

import pandas as pd

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)
from save_end_schema import SAVE_END_COLUMNS  # noqa: E402


# ---------- 사용자 추정 범주값 (검증 대상) ----------
USER_CLAIMS = {
    2: {  # StepType
        "expected_values": {1, 2, 3, 4, 5, 8},
        "mapping": {1: "CHG", 2: "DCHG", 3: "REST", 4: "OCV", 5: "IMP", 8: "LOOP"},
        "is_categorical": True,
    },
    3: {  # ChgDchg
        "expected_values": {1, 2, 255},
        "mapping": {1: "CV", 2: "CC", 255: "rest"},   # ← 의심: 사용자 추정
        "is_categorical": True,
    },
    4: {  # CurrentApp
        "expected_values": {1, 2},
        "mapping": {1: "전류 비인가 직전", 2: "전류 인가"},
        "is_categorical": True,
    },
    5: {  # CCCV
        "expected_values": {0, 1},
        "mapping": {0: "CC", 1: "CV"},
        "is_categorical": True,
    },
    6: {  # EndState
        "expected_values": {0, 64, 65, 66, 69, 78},
        "mapping": {0: "PAT_START", 64: "REST_DONE", 65: "CC_DONE",
                    66: "CV_DONE", 69: "PAT_END", 78: "CAPACITY_CUT"},
        "is_categorical": True,
    },
    25: {  # Unknown25
        "expected_values": {0, 2},
        "mapping": {0: "unknown", 2: "unknown"},
        "is_categorical": True,
    },
}


def load_save_end(path: str) -> Optional[pd.DataFrame]:
    try:
        return pd.read_csv(path, sep=",", header=None, encoding="cp949",
                           engine="c", on_bad_lines="skip")
    except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError,
            UnicodeDecodeError):
        return None


def find_all_save_ends(base: str, max_files: int = 40) -> list[str]:
    """exp_data 하위 SaveEndData.csv 수집."""
    found: list[str] = []
    for root, _dirs, files in os.walk(base):
        for f in files:
            if "SaveEndData" in f and f.lower().endswith(".csv"):
                found.append(os.path.join(root, f))
                if len(found) >= max_files:
                    return found
    return found


# ---------- 검증 루틴 ----------
def aggregate_column_stats(files: list[str]) -> dict[int, dict]:
    """파일별 컬럼 값 분포를 집계."""
    stats: dict[int, dict] = defaultdict(lambda: {
        "value_counter": Counter(),
        "min": float("inf"),
        "max": float("-inf"),
        "n_nulls": 0,
        "n_rows": 0,
        "dtype_float": 0,
        "dtype_int": 0,
    })

    for fp in files:
        df = load_save_end(fp)
        if df is None or df.empty:
            continue
        n = len(df)
        for col in df.columns:
            s = stats[int(col)]
            s["n_rows"] += n
            try:
                numeric = pd.to_numeric(df[col], errors="coerce")
                n_null = numeric.isna().sum()
                s["n_nulls"] += int(n_null)
                valid = numeric.dropna()
                if not valid.empty:
                    s["min"] = min(s["min"], float(valid.min()))
                    s["max"] = max(s["max"], float(valid.max()))
                    # 범주형 후보 (unique ≤ 20)인 경우만 카운터에
                    uniq_vals = valid.unique()
                    if len(uniq_vals) <= 20:
                        for v in valid:
                            s["value_counter"][int(v) if v == int(v) else float(v)] += 1
                    # 정수/실수 판별
                    if (valid == valid.astype(int)).all():
                        s["dtype_int"] += n
                    else:
                        s["dtype_float"] += n
            except Exception:
                pass

    return dict(stats)


def verify_categorical(col: int, stats: dict, claim: dict) -> tuple[str, str]:
    """범주형 컬럼 검증."""
    observed = set(stats["value_counter"].keys())
    expected = claim["expected_values"]

    if not observed:
        return ("SKIP", "데이터 없음")

    extra = observed - expected
    missing = expected - observed

    if not extra and not missing:
        return ("OK", f"관찰={sorted(observed)}, 추정 일치")
    elif not extra and missing:
        return ("PARTIAL", f"관찰={sorted(observed)}, 추정값 {sorted(missing)} 미관찰")
    elif extra:
        return ("SUSPECT", f"관찰={sorted(observed)}, 추정 외 값 {sorted(extra)} 발견")
    return ("UNKNOWN", "")


def verify_numeric_unit(col: int, stats: dict, claimed_unit: str) -> tuple[str, str]:
    """수치 컬럼의 단위 추정.

    Voltage 예: 3000~4500 mV 또는 3_000_000~4_500_000 uV.
    Current 예: 100~5000 mA 또는 100_000~5_000_000 uA.
    """
    if stats["min"] == float("inf"):
        return ("SKIP", "데이터 없음")

    vmin, vmax = stats["min"], stats["max"]
    info = f"min={vmin:g}, max={vmax:g}"
    return ("INFO", f"{info} (claimed unit={claimed_unit})")


def verify_correlations(files: list[str]) -> dict[str, str]:
    """컬럼 간 상관관계 검증 — StepType ↔ ChgDchg 매핑 확인."""
    st_to_chgdch: dict[int, Counter] = defaultdict(Counter)
    cccv_to_chgdch: dict[int, Counter] = defaultdict(Counter)

    for fp in files:
        df = load_save_end(fp)
        if df is None or df.empty or df.shape[1] < 6:
            continue
        for _, row in df.iterrows():
            try:
                st = int(row[2])
                cd = int(row[3])
                cc = int(row[5])
                st_to_chgdch[st][cd] += 1
                cccv_to_chgdch[cc][cd] += 1
            except (ValueError, TypeError):
                continue

    out = {
        "StepType → ChgDchg 분포": "",
        "CCCV → ChgDchg 분포": "",
    }
    lines = []
    for st in sorted(st_to_chgdch):
        items = st_to_chgdch[st].most_common()
        lines.append(f"  ST={st:>3}: {items}")
    out["StepType → ChgDchg 분포"] = "\n".join(lines)

    lines = []
    for cc in sorted(cccv_to_chgdch):
        items = cccv_to_chgdch[cc].most_common()
        lines.append(f"  CCCV={cc}: {items}")
    out["CCCV → ChgDchg 분포"] = "\n".join(lines)
    return out


def verify_tc_monotonic(files: list[str]) -> dict[str, int]:
    """col[27] TC의 단조증가성 검증 — TC가 감소하는 경우가 있는지."""
    results = {"files": 0, "non_monotonic": 0, "decrease_count_total": 0}
    for fp in files:
        df = load_save_end(fp)
        if df is None or df.empty or df.shape[1] <= 27:
            continue
        results["files"] += 1
        tcs = pd.to_numeric(df[27], errors="coerce").dropna().astype(int).tolist()
        dec = sum(1 for a, b in zip(tcs, tcs[1:]) if b < a)
        if dec > 0:
            results["non_monotonic"] += 1
            results["decrease_count_total"] += dec
    return results


def verify_curc_range(files: list[str]) -> dict:
    """col[28] CurrentCycle이 Loop 내 1~N 범위인지 검증.

    그룹 전환 시 1로 리셋되는지도 확인.
    """
    results = {
        "files": 0,
        "curc_max": 0,
        "curc_resets_to_1": 0,
        "curc_decreases": 0,
    }
    for fp in files:
        df = load_save_end(fp)
        if df is None or df.empty or df.shape[1] <= 28:
            continue
        results["files"] += 1
        curcs = pd.to_numeric(df[28], errors="coerce").dropna().astype(int).tolist()
        if not curcs:
            continue
        results["curc_max"] = max(results["curc_max"], max(curcs))
        # 감소 카운트 (= 그룹 전환)
        for a, b in zip(curcs, curcs[1:]):
            if b < a:
                results["curc_decreases"] += 1
                if b == 1:
                    results["curc_resets_to_1"] += 1
    return results


# ---------- 리포트 생성 ----------
def generate_report(files: list[str]) -> str:
    lines: list[str] = []
    lines.append("=" * 70)
    lines.append(f"SaveEndData 스키마 검증 — {len(files)}개 파일")
    lines.append("=" * 70)

    stats = aggregate_column_stats(files)

    # 1) 범주형 컬럼 검증
    lines.append("\n[1] 범주형 컬럼 추정 검증")
    lines.append("-" * 70)
    for col, claim in USER_CLAIMS.items():
        s = stats.get(col, {"value_counter": Counter()})
        status, msg = verify_categorical(col, s, claim)
        spec = SAVE_END_COLUMNS[col]
        lines.append(f"  col[{col:>2}] {spec.name:<18} [{status:<7}] {msg}")

    # 2) TC 단조증가
    lines.append("\n[2] col[27] TotalCycle 단조증가성")
    lines.append("-" * 70)
    tc_res = verify_tc_monotonic(files)
    lines.append(f"  검사 파일: {tc_res['files']}")
    lines.append(f"  비단조 파일: {tc_res['non_monotonic']}")
    lines.append(f"  총 감소 이벤트: {tc_res['decrease_count_total']}")
    if tc_res['non_monotonic'] == 0:
        lines.append("  → 확정: TC는 단조증가 (사용자 추정 OK)")
    else:
        lines.append("  → 의심: TC 감소 사례 존재 (재검토 필요)")

    # 3) CurrentCycle 범위
    lines.append("\n[3] col[28] CurrentCycle Loop 내 반복 검증")
    lines.append("-" * 70)
    curc_res = verify_curc_range(files)
    lines.append(f"  검사 파일: {curc_res['files']}")
    lines.append(f"  Max CurC: {curc_res['curc_max']}")
    lines.append(f"  감소 이벤트: {curc_res['curc_decreases']}")
    lines.append(f"    그중 1로 리셋: {curc_res['curc_resets_to_1']}")
    reset_ratio = (
        curc_res["curc_resets_to_1"] / curc_res["curc_decreases"] * 100
        if curc_res["curc_decreases"] else 0
    )
    lines.append(f"  리셋 비율: {reset_ratio:.1f}%")
    if reset_ratio > 95:
        lines.append("  → 확정: 그룹 전환 시 CurC=1 리셋 (사용자 추정 OK)")
    else:
        lines.append("  → 의심: 감소가 꼭 1로 가지는 않음")

    # 4) StepType ↔ ChgDchg 상관
    lines.append("\n[4] StepType ↔ ChgDchg 상관 (col[3] 의미 확정)")
    lines.append("-" * 70)
    corr = verify_correlations(files)
    for k, v in corr.items():
        lines.append(f"  {k}:")
        lines.append(v)

    # 5) 수치 컬럼 단위 추정
    lines.append("\n[5] 수치 컬럼 min/max (단위 추정)")
    lines.append("-" * 70)
    numeric_cols_to_check = [8, 9, 10, 11, 17, 19, 29, 30, 45, 46]
    for col in numeric_cols_to_check:
        s = stats.get(col)
        if s is None:
            continue
        spec = SAVE_END_COLUMNS[col]
        status, msg = verify_numeric_unit(col, s, spec.unit)
        lines.append(f"  col[{col:>2}] {spec.name:<16} unit={spec.unit:<8} {msg}")

    # 6) 기타 컬럼 값 분포
    lines.append("\n[6] 기타 컬럼 unique 값 (범주형 후보)")
    lines.append("-" * 70)
    for col in [1, 16, 26]:
        s = stats.get(col)
        if s is None or not s["value_counter"]:
            continue
        spec = SAVE_END_COLUMNS[col]
        top = s["value_counter"].most_common(10)
        lines.append(f"  col[{col:>2}] {spec.name:<18} top10: {top}")

    return "\n".join(lines)


if __name__ == "__main__":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

    base = r"C:\Users\Ryu\battery\python\BDT_dev\DataTool_dev_code\data\exp_data"
    files = find_all_save_ends(base, max_files=50)
    print(f"SaveEndData 파일 {len(files)}개 발견\n")

    report = generate_report(files)
    print(report)
