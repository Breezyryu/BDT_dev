"""
===============================================================================
DB 인제스트 우선순위 산정 스크립트
===============================================================================
  _신뢰성_종합현황_사내.json 을 읽어서 106개 그룹에 점수를 매기고
  Tier 1 / Tier 2 / Tier 3 으로 분류한다.

  출력:
    _인제스트_우선순위.txt   — 사람이 읽을 수 있는 리포트
    _인제스트_우선순위.csv   — 정렬된 CSV (인제스트 순서)
    _mah_manual_mapping.json — 수동입력 필요 항목 매핑 템플릿

  사용법:
    python prioritize_ingest.py                    # 기본: 같은 폴더의 JSON 사용
    python prioritize_ingest.py [JSON 경로]        # 경로 직접 지정
===============================================================================
"""

import json
import csv
import sys
from pathlib import Path


# ── 설정 ──
# 온도 완성도 점수
TEMP_SCORE = {"3/3": 30, "2/3": 15, "1/3": 5, "0/3": 0}

# mAh 자동추출 가능 보너스
MAH_AUTO_BONUS = 20

# 카테고리 가중치 (Phone이 가장 비교 수요 높음)
CATEGORY_WEIGHT = {
    "Phone": 15,
    "Phone(JDM)": 10,
    "Tab": 8,
    "Watch": 8,
    "Laptop": 6,
    "Buds": 5,
    "Robot": 5,
    "Ring": 3,
}

# 파일 크기 점수 (데이터 양 = 사이클 수 반영)
def _size_score(total_size_kb: int) -> int:
    """파일 크기 기반 점수 (0~15)."""
    if total_size_kb >= 1000:
        return 15
    if total_size_kb >= 500:
        return 10
    if total_size_kb >= 200:
        return 5
    return 0

# EA(셀 수) 보너스
def _ea_score(total_ea) -> int:
    """셀 수가 있으면 보너스."""
    if total_ea is None:
        return 0
    if total_ea >= 10:
        return 5
    return 2

# 파일 수 보너스 (다수 파일 = 온도/BLK별 세분화)
def _file_count_score(file_count: int) -> int:
    if file_count >= 4:
        return 5
    if file_count >= 2:
        return 2
    return 0


# ── Tier 분류 기준 ──
TIER1_THRESHOLD = 60   # 이상 → Tier 1 (즉시 인제스트)
TIER2_THRESHOLD = 35   # 이상 → Tier 2 (다음 배치)
# 그 미만 → Tier 3 (나중)


def load_json(json_path: Path) -> dict:
    """JSON 파일 로드."""
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


def score_group(g: dict) -> dict:
    """그룹 하나에 점수를 매긴다."""
    key = g["key"]
    cat = key.get("category", "Phone")
    model = key.get("model", "?")
    vendor = key.get("vendor", "-")
    dev_stage = key.get("dev_stage", "-")
    capacity = key.get("capacity_mah")
    in_latest = g.get("in_latest", False)

    temp_comp = g.get("temp_completeness", "0/3")
    mah_ok = g.get("mah_auto_ok", False)
    size_kb = g.get("total_size_kb", 0)
    ea = g.get("total_ea")
    fc = g.get("file_count", 0)
    tags = g.get("tags", [])
    cycle_hints = g.get("cycle_hints", [])
    voltage = g.get("voltage")
    generation = g.get("generation", "")

    # 점수 계산
    s_temp = TEMP_SCORE.get(temp_comp, 0)
    s_mah = MAH_AUTO_BONUS if mah_ok else 0
    s_cat = CATEGORY_WEIGHT.get(cat, 3)
    s_size = _size_score(size_kb)
    s_ea = _ea_score(ea)
    s_file = _file_count_score(fc)

    total = s_temp + s_mah + s_cat + s_size + s_ea + s_file

    # Tier 분류
    if total >= TIER1_THRESHOLD:
        tier = 1
    elif total >= TIER2_THRESHOLD:
        tier = 2
    else:
        tier = 3

    # 배치 번호: 최신폴더 우선(1~3), 과거(4~6)
    batch = tier if in_latest else tier + 3

    return {
        "tier": tier,
        "batch": batch,
        "in_latest": in_latest,
        "score": total,
        "category": cat,
        "model": model,
        "vendor": vendor,
        "dev_stage": dev_stage,
        "capacity_mah": capacity,
        "voltage": voltage,
        "generation": generation,
        "temp_completeness": temp_comp,
        "temperatures": g.get("temperatures", []),
        "mah_auto_ok": mah_ok,
        "total_ea": ea,
        "file_count": fc,
        "total_size_kb": size_kb,
        "blks": g.get("blks", []),
        "cycle_hints": cycle_hints,
        "tags": tags,
        # 점수 상세
        "s_temp": s_temp,
        "s_mah": s_mah,
        "s_cat": s_cat,
        "s_size": s_size,
        "s_ea": s_ea,
        "s_file": s_file,
    }


def build_mah_mapping(scored: list[dict]) -> dict:
    """
    수동입력 필요(mah_auto_ok=False) 항목에 대해
    같은 모델명의 자동추출 항목에서 mAh를 참조하여 매핑 템플릿 생성.
    """
    # 모델명 → capacity 매핑 (자동추출 성공한 것들)
    model_mah_map: dict[str, list[int]] = {}
    for item in scored:
        if item["mah_auto_ok"] and item["capacity_mah"]:
            # 모델명의 핵심 부분 추출 (첫 2단어 정도)
            base_model = _base_model_name(item["model"])
            model_mah_map.setdefault(base_model, []).append(item["capacity_mah"])

    # 수동 매핑 구성
    mapping = {}
    for item in scored:
        if item["mah_auto_ok"]:
            continue
        model = item["model"]
        vendor = item["vendor"]
        map_key = f"{model}|{vendor}"

        # 같은 모델 기반으로 참조 시도
        base = _base_model_name(model)
        candidates = model_mah_map.get(base, [])

        if candidates:
            # 가장 빈번한 값
            from collections import Counter
            most_common = Counter(candidates).most_common(1)[0][0]
            mapping[map_key] = {
                "capacity_mah": most_common,
                "source": "auto_reference",
                "comment": f"같은 모델({base}) 참조 → {most_common}mAh",
            }
        else:
            mapping[map_key] = {
                "capacity_mah": None,
                "source": "manual_required",
                "comment": "Excel 열어서 확인 또는 스펙 문서 참조 필요",
            }

    return mapping


def _base_model_name(model: str) -> str:
    """모델명에서 핵심 부분 추출 (변종 식별용)."""
    # 숫자+단어 조합 패턴에서 첫 2토큰 추출
    parts = model.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"
    return parts[0] if parts else model


def generate_report(scored: list[dict], mapping: dict, json_path: Path) -> str:
    """텍스트 리포트 생성."""
    lines = []
    sep = "=" * 100

    lines.append(sep)
    lines.append(f"  DB 인제스트 우선순위 리포트  |  기준 데이터: {json_path.name}")
    lines.append(f"  생성일: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"  정렬: 최신폴더 우선 → Tier 순서 → 점수 내림차순")
    lines.append(sep)

    # 배치별 통계
    batch_counts = {}
    batch_files = {}
    for item in scored:
        b = item["batch"]
        batch_counts[b] = batch_counts.get(b, 0) + 1
        batch_files[b] = batch_files.get(b, 0) + item["file_count"]

    batch_labels = {
        1: "최신폴더 + Tier 1 (즉시 인제스트)",
        2: "최신폴더 + Tier 2",
        3: "최신폴더 + Tier 3",
        4: "과거 + Tier 1",
        5: "과거 + Tier 2",
        6: "과거 + Tier 3",
    }

    lines.append("")
    lines.append("■ 배치별 요약 (인제스트 순서)")
    for b in range(1, 7):
        cnt = batch_counts.get(b, 0)
        fc = batch_files.get(b, 0)
        lines.append(f"  배치 {b}: {batch_labels[b]:<30} → {cnt:>5}개 그룹, {fc:>5}개 파일")
    lines.append(f"  합계: {sum(batch_counts.values())}개 그룹")

    lines.append("")
    lines.append("■ 점수 기준")
    lines.append(f"  온도 완성도: 3/3={TEMP_SCORE['3/3']}점, 2/3={TEMP_SCORE['2/3']}점, 1/3={TEMP_SCORE['1/3']}점")
    lines.append(f"  mAh 자동추출 가능: +{MAH_AUTO_BONUS}점")
    lines.append(f"  카테고리: Phone={CATEGORY_WEIGHT['Phone']}점, Tab/Watch={CATEGORY_WEIGHT['Tab']}점, ...")
    lines.append(f"  파일 크기: ≥1MB=15점, ≥500K=10점, ≥200K=5점")
    lines.append(f"  EA 수: ≥10=5점, ≥1=2점")
    lines.append(f"  파일 수: ≥4=5점, ≥2=2점")

    # 배치별 상세 목록
    global_no = 0
    for batch_num in range(1, 7):
        batch_items = [i for i in scored if i["batch"] == batch_num]
        if not batch_items:
            continue

        lines.append("")
        lines.append(sep)
        latest_mark = "★ 최신폴더" if batch_num <= 3 else "  과거"
        tier_num = batch_num if batch_num <= 3 else batch_num - 3
        lines.append(f"■ 배치 {batch_num} — {latest_mark} | Tier {tier_num} ({len(batch_items)}개)")
        lines.append(sep)

        # 헤더
        header = f"{'No':>5} | {'점수':>4} | {'카테':8} | {'모델':<28} | {'제조사':<10} | {'용량':>6} | {'온도셋':<20} | {'완성':5} | {'mAh':3} | {'파일':>3} | {'크기':>8} | {'점수 상세':30}"
        lines.append(header)
        lines.append("-" * len(header))

        for item in batch_items:
            global_no += 1
            cap_str = f"{item['capacity_mah']}" if item["capacity_mah"] else "-"
            temp_str = "/".join(f"{t}°C" for t in item["temperatures"])
            mah_mark = "●" if item["mah_auto_ok"] else "○"
            detail = f"T{item['s_temp']}+M{item['s_mah']}+C{item['s_cat']}+S{item['s_size']}+E{item['s_ea']}+F{item['s_file']}"
            tags_str = ", ".join(item["tags"]) if item["tags"] else ""

            line = (
                f"{global_no:>5} | {item['score']:>4} | {item['category']:8} | "
                f"{item['model']:<28} | {item['vendor']:<10} | "
                f"{cap_str:>6} | {temp_str:<20} | {item['temp_completeness']:5} | "
                f"{mah_mark:3} | {item['file_count']:>3} | "
                f"{item['total_size_kb']:>6}K | {detail:30}"
            )
            if tags_str:
                line += f" [{tags_str}]"
            lines.append(line)

    # mAh 수동 매핑 섹션
    lines.append("")
    lines.append(sep)
    lines.append("■ mAh 수동입력 필요 항목 매핑 현황 (25개)")
    lines.append(sep)

    auto_ref = [k for k, v in mapping.items() if v["source"] == "auto_reference"]
    manual_req = [k for k, v in mapping.items() if v["source"] == "manual_required"]

    lines.append(f"  자동 참조로 해결 가능: {len(auto_ref)}개")
    lines.append(f"  수동 확인 필요:       {len(manual_req)}개")
    lines.append("")

    if auto_ref:
        lines.append("  [자동 참조 가능]")
        for k in sorted(auto_ref):
            v = mapping[k]
            lines.append(f"    {k:<40} → {v['capacity_mah']}mAh ({v['comment']})")

    if manual_req:
        lines.append("")
        lines.append("  [수동 확인 필요]")
        for k in sorted(manual_req):
            v = mapping[k]
            lines.append(f"    {k:<40} → ??? ({v['comment']})")

    lines.append("")
    lines.append(sep)
    lines.append("리포트 완료.")

    return "\n".join(lines)


def export_csv(scored: list[dict], output_path: Path) -> None:
    """우선순위 CSV 내보내기."""
    fields = [
        "batch", "tier", "in_latest", "score", "category", "model", "vendor", "dev_stage",
        "capacity_mah", "voltage", "generation", "temp_completeness",
        "temperatures", "mah_auto_ok", "total_ea", "file_count",
        "total_size_kb", "blks", "cycle_hints", "tags",
        "s_temp", "s_mah", "s_cat", "s_size", "s_ea", "s_file",
    ]
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for item in scored:
            row = dict(item)
            # 리스트 → 문자열 변환
            row["temperatures"] = "/".join(str(t) for t in row.get("temperatures", []))
            row["blks"] = ", ".join(row.get("blks", []))
            row["cycle_hints"] = "; ".join(row.get("cycle_hints", []))
            row["tags"] = ", ".join(row.get("tags", []))
            writer.writerow(row)

    print(f"  CSV 저장: {output_path}")


def main():
    # JSON 경로 결정
    if len(sys.argv) > 1:
        json_path = Path(sys.argv[1])
    else:
        json_path = Path(__file__).parent / "_신뢰성_종합현황_사내.json"

    if not json_path.exists():
        print(f"ERROR: JSON 파일을 찾을 수 없습니다: {json_path}")
        sys.exit(1)

    print(f"JSON 로드: {json_path}")
    data = load_json(json_path)
    groups = data.get("groups", [])
    print(f"  총 {len(groups)}개 그룹")

    # 1. 점수 계산
    scored = [score_group(g) for g in groups]

    # 2. 배치 순서로 정렬: batch(1~6) → 점수 내림차순 → 카테고리 → 모델명
    scored.sort(key=lambda x: (x["batch"], -x["score"], x["category"], x["model"]))

    # 3. mAh 수동 매핑 생성
    mapping = build_mah_mapping(scored)

    # 4. 출력 경로 (스크립트와 같은 폴더)
    out_dir = Path(__file__).parent
    report_path = out_dir / "_인제스트_우선순위.txt"
    csv_path = out_dir / "_인제스트_우선순위.csv"
    mapping_path = out_dir / "_mah_manual_mapping.json"

    # 5. 리포트 생성
    report = generate_report(scored, mapping, json_path)
    report_path.write_text(report, encoding="utf-8")
    print(f"  리포트 저장: {report_path}")

    # 6. CSV 내보내기
    export_csv(scored, csv_path)

    # 7. 매핑 JSON 저장
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"  매핑 JSON 저장: {mapping_path}")

    # 8. 요약 출력
    batch_counts = {}
    for item in scored:
        b = item["batch"]
        batch_counts[b] = batch_counts.get(b, 0) + 1

    batch_labels = {
        1: "최신+Tier1", 2: "최신+Tier2", 3: "최신+Tier3",
        4: "과거+Tier1", 5: "과거+Tier2", 6: "과거+Tier3",
    }
    print()
    print("=== 인제스트 배치 순서 ===")
    for b in range(1, 7):
        cnt = batch_counts.get(b, 0)
        print(f"  배치 {b} ({batch_labels[b]}): {cnt}개")

    auto_ref = sum(1 for v in mapping.values() if v["source"] == "auto_reference")
    manual_req = sum(1 for v in mapping.values() if v["source"] == "manual_required")
    print(f"  mAh 자동참조 해결: {auto_ref}개 / 수동확인 필요: {manual_req}개")


if __name__ == "__main__":
    main()
