"""
===============================================================================
신뢰성 DRM .xls → CSV 자동 변환 스크립트
===============================================================================
  Knox Drive의 신뢰성 .xls 파일(NASCA DRM)을 xlwings COM으로 열어
  BDT 로딩 로직(정규화 + 행 병합)까지 적용한 CSV로 변환·저장한다.

  ※ 사내 PC 전용 (Excel + NASCA DRM 플러그인 필요)

  워크플로우:
    1회차: Knox 전체 폴더 → CSV 일괄 변환
    추후:  신규/변경 폴더만 증분 변환

  사용법:
    python convert_reliability_to_csv.py <Knox원본> <CSV저장소>
    python convert_reliability_to_csv.py <Knox원본> <CSV저장소> --folder 260226
    python convert_reliability_to_csv.py <Knox원본> <CSV저장소> --dry-run

  출력 구조:
    <CSV저장소>/
      260226/
        1689mAh_ATL_Q7M_15C.csv
        1689mAh_ATL_Q7M_23C.csv
      260210/
        ...
      _변환이력.json   ← 증분 변환 추적
===============================================================================
"""

import argparse
import json
import os
import re
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import pandas as pd

try:
    import xlwings as xw
    HAS_XLWINGS = True
except ImportError:
    HAS_XLWINGS = False


# ── 설정 ──
SHEET_NAME = "Plot Base Data"
HISTORY_FILE = "_변환이력.json"
# 변환 리포트 파일
REPORT_FILE = "_변환리포트.txt"


# ── BDT 동일 로직 ──

def name_capacity(data_file_path: str) -> float:
    """파일명에서 mAh 용량값 추출 (BDT 동일 로직)."""
    if not isinstance(data_file_path, str):
        return 0.0
    raw_file_path = re.sub(r'[._@\[\]\(\)]', ' ', data_file_path)
    match = re.search(r'(\d+([\-.]\d+)?)mAh', raw_file_path)
    if match:
        min_cap = match.group(1).replace('-', '.')
        return float(min_cap)
    return 0.0


def merge_rows_199(df: pd.DataFrame) -> pd.DataFrame:
    """199사이클 단위 행 병합 (BDT 동일 로직).

    조건: 3번째 행(index=2)이 첫 행(index=0)의 50% 이하이면
    인접 행을 합산하여 충·방전을 하나의 사이클로 통합.
    """
    # 데이터가 3행 미만이면 병합 불필요
    if len(df) < 3:
        return df

    # 조건 확인: iat[2,0] 은 1-based index 기준 3번째 행의 첫 컬럼
    try:
        val_row3 = df.iat[2, 0]
        val_row1 = df.iat[0, 0]
        if pd.isna(val_row3) or pd.isna(val_row1) or val_row1 == 0:
            return df
        if val_row3 >= val_row1 * 0.5:
            return df
    except (IndexError, TypeError):
        return df

    count = len(df)
    lastcount = int((count + int(count / 199) + 1) / 2 + 1)
    index = 0
    for _ in range(lastcount - 1):
        if index == 0 or index == 197:
            index = index + 1
        else:
            if index > 197 and (index - 197) % 199 == 0:
                index = index + 1
            else:
                if index + 2 not in df.index:
                    break
                df.loc[index + 1, :] = (
                    df.loc[index + 1, :] + df.loc[index + 2, :]
                )
                df.drop(index + 2, axis=0, inplace=True)
                index = index + 2

    df.reset_index(drop=True, inplace=True)
    df.index = df.index + 1
    return df


def convert_single_file(
    app: "xw.App",
    xls_path: Path,
    csv_path: Path,
) -> dict:
    """단일 .xls 파일을 BDT 로직 적용 후 CSV로 변환.

    Returns
    -------
    dict
        변환 결과 정보 (status, channels, rows, mah 등)
    """
    result = {
        "source": str(xls_path),
        "target": str(csv_path),
        "status": "OK",
        "mah": 0.0,
        "channels": 0,
        "rows_raw": 0,
        "rows_final": 0,
        "merged": False,
        "error": "",
        "elapsed_sec": 0.0,
    }
    t0 = time.time()
    wb = None

    try:
        # 1. 파일명에서 용량 추출
        filename = xls_path.name
        mincapacity = name_capacity(filename)
        result["mah"] = mincapacity

        # 2. Excel COM으로 파일 열기
        wb = app.books.open(str(xls_path))

        # 3. "Plot Base Data" 시트 확인
        sheet_names = [s.name for s in wb.sheets]
        if SHEET_NAME not in sheet_names:
            result["status"] = "SKIP_NO_SHEET"
            result["error"] = (
                f"'{SHEET_NAME}' 시트 없음. 존재: {sheet_names}"
            )
            return result

        # 4. 데이터 읽기 (BDT 동일: offset(1,0) → 첫 행 스킵)
        ws = wb.sheets[SHEET_NAME]
        df = ws.used_range.offset(1, 0).options(
            pd.DataFrame, index=False, header=False
        ).value

        if df is None or df.empty:
            result["status"] = "SKIP_EMPTY"
            result["error"] = "데이터 없음"
            return result

        # 5. BDT 처리: drop(0) + 홀수열만 선택
        df = df.drop(0).iloc[:, 1::2]
        df.reset_index(drop=True, inplace=True)
        df.index = df.index + 1

        result["rows_raw"] = len(df)
        result["channels"] = len(df.columns)

        # 6. 정규화 (mincapacity > 0인 경우만)
        if mincapacity > 0:
            df = df / mincapacity
        else:
            # mAh 없는 파일: 원본값 유지, 상태 기록
            result["status"] = "OK_NO_MAH"

        # 7. 행 병합 (199사이클 기준)
        rows_before = len(df)
        df = merge_rows_199(df)
        result["rows_final"] = len(df)
        result["merged"] = len(df) < rows_before

        # 8. 컬럼명 설정: Ch1, Ch2, Ch3, ...
        df.columns = [f"Ch{i+1}" for i in range(len(df.columns))]

        # 9. 인덱스를 Cycle 컬럼으로 추가
        df.insert(0, "Cycle", df.index)

        # 10. CSV 저장
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = f"{type(e).__name__}: {e}"
        traceback.print_exc()

    finally:
        if wb is not None:
            try:
                wb.close()
            except Exception:
                pass
        result["elapsed_sec"] = round(time.time() - t0, 1)

    return result


# ── 변환 이력 관리 ──

def load_history(csv_root: Path) -> dict:
    """변환 이력 JSON 로드."""
    history_path = csv_root / HISTORY_FILE
    if history_path.exists():
        with open(history_path, encoding="utf-8") as f:
            return json.load(f)
    return {"converted": {}, "last_run": None}


def save_history(csv_root: Path, history: dict) -> None:
    """변환 이력 JSON 저장."""
    history["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history_path = csv_root / HISTORY_FILE
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


# ── 폴더 스캔 ──

def scan_xls_files(
    knox_root: Path,
    target_folder: str | None = None,
) -> list[tuple[str, Path]]:
    """Knox 루트에서 YYMMDD 폴더별 .xls 파일 목록 수집.

    Returns
    -------
    list[tuple[str, Path]]
        (폴더명, 파일경로) 쌍 리스트
    """
    files = []
    # YYMMDD 폴더 패턴 (6자리 숫자)
    yymmdd_re = re.compile(r'^\d{6}$')

    try:
        entries = os.listdir(str(knox_root))
    except OSError as e:
        print(f"ERROR: Knox 루트 접근 실패: {e}")
        return files

    for folder_name in sorted(entries):
        if not yymmdd_re.match(folder_name):
            continue
        if target_folder and folder_name != target_folder:
            continue

        folder_path = knox_root / folder_name
        if not os.path.isdir(str(folder_path)):
            continue

        try:
            for fname in os.listdir(str(folder_path)):
                if fname.lower().endswith('.xls') and not fname.startswith('~$'):
                    files.append((folder_name, folder_path / fname))
        except OSError as e:
            print(f"  WARN: {folder_name} 폴더 접근 실패: {e}")

    return files


# ── 메인 ──

def main() -> None:
    parser = argparse.ArgumentParser(
        description="신뢰성 DRM .xls → CSV 자동 변환"
    )
    parser.add_argument(
        "knox_root",
        help="Knox Drive 원본 경로 (예: K:\\Shared files\\rawdata)",
    )
    parser.add_argument(
        "csv_root",
        help="CSV 저장 경로 (예: E:\\reliability_csv)",
    )
    parser.add_argument(
        "--folder",
        default=None,
        help="특정 YYMMDD 폴더만 변환 (예: 260226)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="이미 변환된 파일도 강제 재변환",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 변환 없이 대상 파일 목록만 출력",
    )
    args = parser.parse_args()

    knox_root = Path(args.knox_root)
    csv_root = Path(args.csv_root)

    if not HAS_XLWINGS:
        print("ERROR: xlwings가 설치되어 있지 않습니다.")
        print("  pip install xlwings")
        sys.exit(1)

    # 1. 대상 파일 스캔
    print(f"Knox 원본: {knox_root}")
    print(f"CSV 저장소: {csv_root}")
    if args.folder:
        print(f"대상 폴더: {args.folder}")
    print()

    all_files = scan_xls_files(knox_root, args.folder)
    print(f"스캔 완료: {len(all_files)}개 .xls 파일")

    if not all_files:
        print("변환 대상 파일이 없습니다.")
        return

    # 2. 증분 필터: 이미 변환된 파일 제외
    history = load_history(csv_root)
    converted_set = set(history.get("converted", {}).keys())

    if args.force:
        targets = all_files
        print(f"강제 재변환 모드: 전체 {len(targets)}개")
    else:
        targets = [
            (folder, fpath)
            for folder, fpath in all_files
            if str(fpath) not in converted_set
        ]
        skipped = len(all_files) - len(targets)
        if skipped > 0:
            print(f"이전 변환 완료: {skipped}개 스킵")
        print(f"변환 대상: {len(targets)}개")

    if not targets:
        print("신규 변환 대상이 없습니다.")
        return

    # 3. dry-run 모드
    if args.dry_run:
        print("\n=== Dry-Run: 변환 대상 목록 ===")
        for folder, fpath in targets:
            print(f"  [{folder}] {fpath.name}")
        print(f"\n합계: {len(targets)}개 파일")
        return

    # 4. Excel COM 인스턴스 시작
    print("\nExcel 인스턴스 시작...")
    app = xw.App(visible=False)
    app.display_alerts = False
    app.screen_updating = False

    results = []
    total = len(targets)
    ok_count = 0
    err_count = 0
    skip_count = 0

    try:
        for i, (folder, xls_path) in enumerate(targets, 1):
            # CSV 저장 경로: csv_root/YYMMDD/파일명.csv
            csv_filename = xls_path.stem + ".csv"
            csv_path = csv_root / folder / csv_filename

            print(
                f"  [{i}/{total}] {folder}/{xls_path.name} ... ",
                end="", flush=True,
            )

            result = convert_single_file(app, xls_path, csv_path)
            results.append(result)

            # 상태별 카운트
            if result["status"].startswith("OK"):
                ok_count += 1
                # 이력에 기록
                history.setdefault("converted", {})[str(xls_path)] = {
                    "csv_path": str(csv_path),
                    "mah": result["mah"],
                    "channels": result["channels"],
                    "rows_final": result["rows_final"],
                    "merged": result["merged"],
                    "converted_at": datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                }
                merge_mark = " [병합]" if result["merged"] else ""
                mah_mark = f"{result['mah']:.0f}mAh" if result["mah"] > 0 else "mAh없음"
                print(
                    f"OK ({mah_mark}, {result['channels']}ch, "
                    f"{result['rows_final']}행{merge_mark}) "
                    f"{result['elapsed_sec']}s"
                )
            elif result["status"].startswith("SKIP"):
                skip_count += 1
                print(f"{result['status']} - {result['error']}")
            else:
                err_count += 1
                print(f"ERROR - {result['error']}")

            # 매 10개마다 이력 중간 저장 (장시간 작업 대비)
            if i % 10 == 0:
                save_history(csv_root, history)

    except KeyboardInterrupt:
        print("\n\n사용자 중단 (Ctrl+C)")
    finally:
        # Excel 종료
        try:
            app.quit()
        except Exception:
            pass

        # 이력 최종 저장
        save_history(csv_root, history)

    # 5. 결과 리포트
    print()
    print("=" * 60)
    print(f"  변환 완료 리포트")
    print("=" * 60)
    print(f"  성공: {ok_count}개")
    print(f"  스킵: {skip_count}개")
    print(f"  오류: {err_count}개")
    print(f"  합계: {len(results)}개 / 전체 {total}개")
    print()

    # 텍스트 리포트 저장
    report_path = csv_root / REPORT_FILE
    report_lines = [
        "=" * 80,
        f"  신뢰성 DRM → CSV 변환 리포트",
        f"  실행일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"  Knox 원본: {knox_root}",
        f"  CSV 저장소: {csv_root}",
        "=" * 80,
        "",
        f"성공: {ok_count}개 | 스킵: {skip_count}개 | 오류: {err_count}개",
        "",
    ]

    # 오류 파일 목록
    errors = [r for r in results if r["status"] == "ERROR"]
    if errors:
        report_lines.append("■ 오류 발생 파일")
        for r in errors:
            report_lines.append(f"  {r['source']}")
            report_lines.append(f"    → {r['error']}")
        report_lines.append("")

    # 스킵 파일 목록
    skips = [r for r in results if r["status"].startswith("SKIP")]
    if skips:
        report_lines.append("■ 스킵 파일")
        for r in skips:
            report_lines.append(f"  {r['source']} → {r['status']}")
        report_lines.append("")

    # mAh 없는 파일 목록
    no_mah = [r for r in results if r["status"] == "OK_NO_MAH"]
    if no_mah:
        report_lines.append(f"■ mAh 미추출 파일 ({len(no_mah)}개) — 원본값 저장됨")
        for r in no_mah:
            report_lines.append(f"  {Path(r['source']).name}")
        report_lines.append("")

    # 병합 적용 파일
    merged = [r for r in results if r.get("merged")]
    if merged:
        report_lines.append(f"■ 행 병합 적용 파일 ({len(merged)}개)")
        for r in merged:
            report_lines.append(
                f"  {Path(r['source']).name}: "
                f"{r['rows_raw']}행 → {r['rows_final']}행"
            )
        report_lines.append("")

    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"리포트 저장: {report_path}")
    print(f"변환 이력:   {csv_root / HISTORY_FILE}")


if __name__ == "__main__":
    main()
