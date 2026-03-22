"""LOOP 구조 기반 스케줄 패턴 분석 테스트"""
import sys
sys.path.insert(0, "analysis_dev_env")
from parse_pne_schedule import parse_pne_schedule
from pathlib import Path

# Rss 포함 스케줄만 찾기
sch_files = sorted(Path("rawdata").rglob("*.sch"))
rss_files = [f for f in sch_files if "Rss" in str(f) or "RSS" in str(f)]
print(f"=== Rss .sch 파일: {len(rss_files)}개 ===\n")

for sf in rss_files[:2]:
    r = parse_pne_schedule(sf)
    if not r:
        print(f"{sf.name}: 파싱 실패")
        continue
    steps = r["steps"]
    folder_name = sf.parent.parent.name
    short = folder_name[:50]
    print(f"--- {short} / {sf.name} ({r['total_steps']} steps) ---")

    # LOOP 구조 기반 구간 분할
    sections = []
    buf = []
    for s in steps:
        buf.append(s)
        if s["type"] in ("LOOP", "REST_SAFE"):
            sections.append(list(buf))
            buf = []
    if buf:
        sections.append(list(buf))

    for i, sec in enumerate(sections):
        types = [x["type"] for x in sec]
        chg = sum(1 for t in types if t.startswith("CHG"))
        dchg = sum(1 for t in types if t == "DCHG_CC")
        rest = sum(1 for t in types if t.startswith("REST"))
        loop = [x for x in sec if x["type"] == "LOOP"]
        loop_str = ""
        if loop:
            lc = loop[0]["loop_count"]
            target = loop[0]["target_step"]
            loop_str = f"  LOOP={lc}회→step{target}"

        # 카테고리 추정
        cat = "?"
        if loop and lc >= 50:
            cat = "가속수명"
        elif loop and chg == 1 and dchg >= 1 and lc <= 5:
            cat = "RPT"
        elif loop and 78 in [x.get("loop_count", 0) for x in sec]:
            cat = "Rss"
        elif any(t == "REST_SAFE" for t in types) and not loop:
            cat = "REST_SAFE"
        elif loop and chg >= 1:
            cat = "RPT/Rss"

        # 전류 정보 (첫 충전/방전)
        cur_info = ""
        for x in sec:
            if x["type"] in ("CHG_CC", "CHG_CCCV", "DCHG_CC"):
                cur_info = f"  {x['type']}={x['current_mA']:.0f}mA"
                break

        print(f"  [{i}] CHG={chg} DCHG={dchg} REST={rest}{loop_str}{cur_info}  → {cat}")
        print(f"       types: {types}")

    print()
