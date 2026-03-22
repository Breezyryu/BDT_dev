"""Gen4p 4905mAh .sch 파일 교차검증 스크립트

새로운 스케줄 세트(10개)로 파서 정합성 검증:
- 매직 헤더 / 블록 크기 정합
- LOOP 구조 기반 구간 분류
- 용량한도 / 전류 / 전압 값 신뢰성
- 스케줄 타입별 예상 패턴 매칭
"""
import sys
sys.path.insert(0, "analysis_dev_env")
from parse_pne_schedule import parse_pne_schedule, extract_accel_pattern_from_sch
from pathlib import Path

SCH_DIR = Path("rawdata/pattern/pne_4905mAh")
NAMEPLATE_MAH = 4905.0  # 폴더명에서 파싱한 공칭 용량

# 기대되는 스케줄 타입 매핑 (파일명 키워드 → 예상 카테고리)
EXPECTED = {
    "RateCharge":   {"type": "Rate", "has_loop": True,  "desc": "충전율 테스트"},
    "RateDischarge": {"type": "Rate", "has_loop": True,  "desc": "방전율 테스트"},
    "SOC별DCIR":    {"type": "DCIR", "has_loop": True,  "desc": "SOC별 DCIR 충방전"},
    "수명1500cy":   {"type": "Life", "has_loop": True,  "desc": "가속수명 1500cy"},
    "GITT01C":      {"type": "GITT", "has_loop": True,  "desc": "GITT 0.1C"},
    "HPPC방충전":   {"type": "HPPC", "has_loop": True,  "desc": "HPPC 방충전"},
}


def classify_keyword(filename: str) -> str:
    """파일명에서 스케줄 타입 키워드 추출."""
    for kw in EXPECTED:
        if kw in filename:
            return kw
    return "Unknown"


def analyze_loop_sections(steps: list[dict]) -> list[dict]:
    """REST_SAFE / LOOP 기준 구간 분할 및 카테고리 추정."""
    sections = []
    buf = []
    for s in steps:
        buf.append(s)
        if s["type"] in ("LOOP", "REST_SAFE"):
            sections.append(list(buf))
            buf = []
    if buf:
        sections.append(list(buf))

    result = []
    for sec in sections:
        types = [x["type"] for x in sec]
        n_chg = sum(1 for t in types if t.startswith("CHG"))
        n_dchg = sum(1 for t in types if t == "DCHG_CC")
        n_rest = sum(1 for t in types if t.startswith("REST"))
        loop_items = [x for x in sec if x["type"] == "LOOP"]

        lc = loop_items[0]["loop_count"] if loop_items else 0
        target = loop_items[0]["target_step"] if loop_items else 0

        # 카테고리 추정 규칙
        cat = "기타"
        if loop_items and lc >= 50:
            cat = "가속수명"
        elif loop_items and n_chg >= 2 and n_dchg >= 2 and lc >= 5:
            cat = "Rate"
        elif loop_items and n_chg == 1 and n_dchg == 1 and lc == 1:
            cat = "RPT"
        elif loop_items and n_dchg >= 5 and lc == 1:
            cat = "Rss/DCIR_pulse"
        elif loop_items and lc >= 5 and n_dchg >= 1:
            cat = "GITT/HPPC_loop"
        elif not loop_items and any(t == "REST_SAFE" for t in types):
            cat = "구간경계"
        elif not loop_items and n_dchg >= 1 and n_chg == 0:
            cat = "초기방전"
        elif loop_items and lc == 1:
            cat = "단일구간"

        # 전류 정보 수집
        currents = []
        for x in sec:
            if x["type"] in ("CHG_CC", "CHG_CCCV", "DCHG_CC"):
                cur = x.get("current_mA", 0)
                crate = round(cur / NAMEPLATE_MAH, 2) if NAMEPLATE_MAH else 0
                currents.append(f"{x['type']}={cur:.0f}mA({crate}C)")

        result.append({
            "n_steps": len(sec),
            "n_chg": n_chg,
            "n_dchg": n_dchg,
            "n_rest": n_rest,
            "loop_count": lc,
            "target_step": target,
            "category": cat,
            "currents": currents,
            "types": types,
        })
    return result


def main():
    sch_files = sorted(SCH_DIR.glob("*.sch"))
    print(f"{'='*80}")
    print(f"Gen4p 4905mAh .sch 교차검증 — {len(sch_files)}개 파일")
    print(f"공칭 용량: {NAMEPLATE_MAH} mAh")
    print(f"{'='*80}\n")

    # ── 1단계: 기본 파싱 정합성 ──
    print("▶ 1단계: 기본 파싱 정합성 검증")
    print("-" * 60)
    results = {}
    for sf in sch_files:
        r = parse_pne_schedule(sf)
        kw = classify_keyword(sf.name)
        if r is None:
            print(f"  ✗ {sf.name}: 파싱 실패!")
            continue

        cap = r["capacity_limit_mAh"]
        est = r["estimated_nameplate_mAh"]
        n_steps = r["total_steps"]
        n_chg = len(r["charge_steps"])
        n_dchg = len(r["discharge_steps"])
        n_loop = len(r["loop_steps"])

        # 용량 검증: capacity_limit ≈ nameplate * 1.1
        cap_ratio = cap / NAMEPLATE_MAH if NAMEPLATE_MAH else 0
        cap_ok = "✓" if 0.9 <= cap_ratio <= 1.3 or cap == 0 else "✗"

        print(f"  {cap_ok} [{kw:14s}] {sf.name[:55]}")
        print(f"    {n_steps} steps | CHG={n_chg} DCHG={n_dchg} LOOP={n_loop}")
        print(f"    cap_limit={cap:.1f}mAh (ratio={cap_ratio:.3f}) est_nameplate={est:.1f}mAh")

        results[sf.name] = {"parsed": r, "keyword": kw}

    # ── 2단계: LOOP 구조 분석 ──
    print(f"\n\n▶ 2단계: LOOP 구조 기반 구간 분석")
    print("=" * 80)

    for sf in sch_files:
        name = sf.name
        if name not in results:
            continue
        r = results[name]["parsed"]
        kw = results[name]["keyword"]

        print(f"\n--- [{kw}] {name} ({r['total_steps']} steps) ---")

        sections = analyze_loop_sections(r["steps"])
        total_designed = 0
        accel_blocks = []

        for i, sec in enumerate(sections):
            lc = sec["loop_count"]
            cur_str = " | ".join(sec["currents"][:3]) if sec["currents"] else ""
            if len(sec["currents"]) > 3:
                cur_str += f" +{len(sec['currents'])-3}more"

            print(f"  [{i:2d}] {sec['category']:12s} "
                  f"CHG={sec['n_chg']} DCHG={sec['n_dchg']} "
                  f"REST={sec['n_rest']} "
                  f"LOOP={lc}{'→step'+str(sec['target_step']) if lc else ''} "
                  f"({sec['n_steps']}steps)")
            if cur_str:
                print(f"       {cur_str}")

            if sec["category"] == "가속수명":
                total_designed += lc
                accel_blocks.append({"idx": i, "loop": lc})

        if accel_blocks:
            print(f"  ▸ 가속수명 블록 {len(accel_blocks)}개, 설계 총 사이클: {total_designed}")
        
        # 패턴 문자열 생성
        pattern_parts = []
        for sec in sections:
            cat = sec["category"]
            lc = sec["loop_count"]
            if cat == "구간경계":
                continue
            if lc > 1:
                pattern_parts.append(f"{cat}×{lc}")
            elif cat != "기타":
                pattern_parts.append(cat)
        if pattern_parts:
            print(f"  ▸ 패턴: {' → '.join(pattern_parts)}")

    # ── 3단계: 가속수명 패턴 추출 (수명 스케줄만) ──
    print(f"\n\n▶ 3단계: extract_accel_pattern_from_sch() 검증 (수명 스케줄)")
    print("=" * 80)

    life_files = [sf for sf in sch_files if "수명" in sf.name]
    for sf in life_files:
        print(f"\n--- {sf.name} ---")
        pat = extract_accel_pattern_from_sch(sf, capacity=NAMEPLATE_MAH)
        if pat is None:
            print("  패턴 추출 실패!")
            continue

        print(f"  source: {pat['source']}")
        print(f"  충전 {pat['n_charge_steps']}스텝 / 방전 {pat['n_discharge_steps']}스텝")
        for cs in pat["charge_steps"]:
            mode = cs.get("mode", "?")
            crate = cs.get("crate", 0)
            cur = cs.get("current_mA", 0)
            vcut = cs.get("voltage_cutoff", 0)
            cv_v = cs.get("cv_voltage", "")
            cc_cut = cs.get("current_cutoff_crate", "")
            extra = ""
            if cv_v:
                extra += f" cv={cv_v}V"
            if cc_cut:
                extra += f" cutoff={cc_cut}C"
            print(f"    CHG: {mode} {crate}C ({cur:.0f}mA) → {vcut}V{extra}")
        for ds in pat["discharge_steps"]:
            crate = ds.get("crate", 0)
            cur = ds.get("current_mA", 0)
            vcut = ds.get("voltage_cutoff", 0)
            print(f"    DCHG: CC {crate}C ({cur:.0f}mA) → {vcut}V")

    # ── 4단계: 비수명 스케줄 특성 분석 ──
    print(f"\n\n▶ 4단계: 비수명 스케줄 특성 분석 (Rate/DCIR/GITT/HPPC)")
    print("=" * 80)

    non_life = [sf for sf in sch_files if "수명" not in sf.name]
    for sf in non_life:
        name = sf.name
        if name not in results:
            continue
        r = results[name]["parsed"]
        kw = results[name]["keyword"]

        print(f"\n--- [{kw}] {name} ---")

        # 유니크 전류값 추출
        chg_currents = set()
        dchg_currents = set()
        chg_voltages = set()
        dchg_voltages = set()
        for s in r["charge_steps"]:
            cur = s.get("current_mA", 0)
            chg_currents.add(round(cur, 1))
            v = s.get("voltage_cutoff_mV", 0) or s.get("cv_voltage_mV", 0)
            if v > 0:
                chg_voltages.add(round(v, 1))
        for s in r["discharge_steps"]:
            cur = s.get("current_mA", 0)
            dchg_currents.add(round(cur, 1))
            v = s.get("voltage_cutoff_mV", 0)
            if v > 0:
                dchg_voltages.add(round(v, 1))

        # C-rate 변환
        chg_crates = sorted([round(c / NAMEPLATE_MAH, 2) for c in chg_currents if c > 0])
        dchg_crates = sorted([round(c / NAMEPLATE_MAH, 2) for c in dchg_currents if c > 0])

        print(f"  충전 C-rates: {chg_crates}")
        print(f"  방전 C-rates: {dchg_crates}")
        print(f"  충전 전압: {sorted(chg_voltages)} mV")
        print(f"  방전 전압: {sorted(dchg_voltages)} mV")

        # LOOP 요약
        for ls in r["loop_steps"]:
            lc = ls["loop_count"]
            ts = ls["target_step"]
            print(f"  LOOP: {lc}회 → step{ts}")

    # ── 5단계: 요약 테이블 ──
    print(f"\n\n▶ 5단계: 종합 요약")
    print("=" * 80)
    print(f"  {'키워드':12s} {'파일수':>5s} {'steps범위':>12s} {'cap_limit':>10s} {'LOOP총합':>8s}")
    print(f"  {'-'*12} {'-'*5} {'-'*12} {'-'*10} {'-'*8}")

    from collections import defaultdict
    by_kw = defaultdict(list)
    for name, info in results.items():
        by_kw[info["keyword"]].append(info["parsed"])

    for kw in sorted(by_kw.keys()):
        items = by_kw[kw]
        steps_range = f"{min(r['total_steps'] for r in items)}-{max(r['total_steps'] for r in items)}"
        caps = set(r["capacity_limit_mAh"] for r in items)
        cap_str = "/".join(f"{c:.0f}" for c in sorted(caps))
        total_loops = sum(
            sum(ls["loop_count"] for ls in r["loop_steps"]) for r in items
        )
        print(f"  {kw:12s} {len(items):5d} {steps_range:>12s} {cap_str:>10s} {total_loops:>8d}")

    print(f"\n✓ 교차검증 완료: {len(results)}/{len(sch_files)}개 파싱 성공")


if __name__ == "__main__":
    main()
