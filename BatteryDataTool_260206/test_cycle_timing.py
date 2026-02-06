"""
toyo_cycle_data vs pne_cycle_data 구간별 실행 시간 측정 스크립트
"""

import time
import os
import sys
import pandas as pd

# BatteryDataTool.py에서 필요한 함수들 import
sys.path.insert(0, r'c:\Users\Ryu\battery\python\BDT_dev\BatteryDataTool_260206')

# 결과 저장용
output_lines = []

def log(msg):
    print(msg)
    output_lines.append(msg)


# ========== 측정용 TOYO 함수 ==========
def toyo_cycle_data_timed(raw_file_path, mincapacity, inirate, chkir):
    """toyo_cycle_data 구간별 측정 버전"""
    timings = {}
    total_start = time.perf_counter()
    
    # 1. 초기화
    t0 = time.perf_counter()
    df = pd.DataFrame()
    timings['1_init'] = time.perf_counter() - t0
    
    # 2. 용량 산정
    t0 = time.perf_counter()
    from BatteryDataTool import toyo_min_cap, toyo_cycle_import
    tempmincap = toyo_min_cap(raw_file_path, mincapacity, inirate)
    mincapacity = tempmincap
    timings['2_min_cap'] = time.perf_counter() - t0
    
    # 3. CSV 로딩 (capacity.log)
    t0 = time.perf_counter()
    tempdata = toyo_cycle_import(raw_file_path)
    timings['3_csv_load'] = time.perf_counter() - t0
    
    if hasattr(tempdata, "dataraw") and not tempdata.dataraw.empty:
        Cycleraw = tempdata.dataraw
        
        # 4. 사이클 데이터 전처리
        t0 = time.perf_counter()
        Cycleraw.loc[:,"OriCycle"]=Cycleraw.loc[:,"TotlCycle"]
        if Cycleraw.loc[0, "Condition"] == 2 and len(Cycleraw.index) > 2:
            if Cycleraw.loc[1, "TotlCycle"] == 1:
                Cycleraw.loc[Cycleraw["Condition"] == 2, "TotlCycle"] -= 1
                Cycleraw = Cycleraw.drop(0, axis=0)
                Cycleraw = Cycleraw.reset_index()
        timings['4_preprocess'] = time.perf_counter() - t0
        
        # 5. 충방전 병합 (벡터화된 groupby 최적화)
        t0 = time.perf_counter()
        Cycleraw = Cycleraw.reset_index(drop=True)
        cond_series = Cycleraw["Condition"]
        merge_group = ((cond_series != cond_series.shift()) | (~cond_series.isin([1, 2]))).cumsum()
        
        def merge_rows(group):
            if len(group) == 1:
                return group.iloc[0]
            cond = group["Condition"].iloc[0]
            result = group.iloc[-1].copy()
            if cond == 1:
                result["Cap[mAh]"] = group["Cap[mAh]"].sum()
                result["Ocv"] = group["Ocv"].iloc[0]
            elif cond == 2:
                result["Cap[mAh]"] = group["Cap[mAh]"].sum()
                result["Pow[mWh]"] = group["Pow[mWh]"].sum()
                if result["Cap[mAh]"] != 0:
                    result["AveVolt[V]"] = result["Pow[mWh]"] / result["Cap[mAh]"]
            return result
        
        Cycleraw = Cycleraw.groupby(merge_group, group_keys=False).apply(merge_rows, include_groups=False)
        Cycleraw = Cycleraw.reset_index(drop=True)
        timings['5_merge_vectorized'] = time.perf_counter() - t0
        
        # 6. 충전/방전 데이터 필터링
        t0 = time.perf_counter()
        chgdata = Cycleraw[(Cycleraw["Condition"] == 1) & (Cycleraw["Finish"] != "                 Vol") 
                           & (Cycleraw["Finish"] != "Volt") & (Cycleraw["Cap[mAh]"] > (mincapacity/60))]
        chgdata.index = chgdata["TotlCycle"]
        Chg = chgdata["Cap[mAh]"]
        Ocv = chgdata["Ocv"]
        Cycleraw.index = Cycleraw["TotlCycle"]
        timings['6_filter_charge'] = time.perf_counter() - t0
        
        # 7. DCIR 후보 추출
        t0 = time.perf_counter()
        dcir = Cycleraw[((Cycleraw["Finish"] == "                 Tim") | (Cycleraw["Finish"] == "Tim") 
                         | (Cycleraw["Finish"] == "Time")) & (Cycleraw["Condition"] == 2) 
                        & (Cycleraw["Cap[mAh]"] < (mincapacity/60))]
        cycnum = dcir["TotlCycle"]
        timings['7_dcir_filter'] = time.perf_counter() - t0
        
        # 8. 방전 데이터 필터링
        t0 = time.perf_counter()
        Dchgdata = Cycleraw[(Cycleraw["Condition"] == 2) & (Cycleraw["Cap[mAh]"] > (mincapacity/60))]
        Dchg = Dchgdata["Cap[mAh]"]
        Temp = Dchgdata["PeakTemp[Deg]"]
        DchgEng = Dchgdata["Pow[mWh]"]
        Chg2 = Chg.shift(periods=-1)
        AvgV = Dchgdata["AveVolt[V]"]
        OriCycle = Dchgdata.loc[:,"OriCycle"]
        timings['8_filter_discharge'] = time.perf_counter() - t0
        
        # 9. DCIR 파일 읽기 (I/O 병목) - 가장 느린 부분
        t0 = time.perf_counter()
        dcir_file_count = 0
        for cycle in cycnum:
            filepath = raw_file_path + "\\%06d" % cycle
            if os.path.isfile(filepath):
                dcirpro = pd.read_csv(filepath, sep=",", skiprows=3, engine="c",
                                      encoding="cp949", on_bad_lines='skip')
                dcir_file_count += 1
                if "PassTime[Sec]" in dcirpro.columns:
                    dcirpro = dcirpro[["PassTime[Sec]", "Voltage[V]", "Current[mA]", "Condition", "Temp1[Deg]"]]
                else:
                    dcirpro = dcirpro[["Passed Time[Sec]", "Voltage[V]", "Current[mA]", "Condition", "Temp1[deg]"]]
                    dcirpro.columns = ["PassTime[Sec]", "Voltage[V]", "Current[mA]", "Condition", "Temp1[Deg]"]
                dcircal = dcirpro[(dcirpro["Condition"] == 2)]
                if len(dcircal) > 0 and dcircal["Current[mA]"].max() != 0:
                    dcir.loc[int(cycle), "dcir"] = ((dcircal["Voltage[V]"].max() - dcircal["Voltage[V]"].min()) 
                                                    / round(dcircal["Current[mA]"].max()) * 1000000)
        timings['9_dcir_file_io'] = time.perf_counter() - t0
        timings['9_dcir_file_count'] = dcir_file_count
        
        # 10. 최종 DataFrame 생성
        t0 = time.perf_counter()
        n = 1
        cyccal = []
        if len(dcir) != 0:
            dcir_len = len(dcir)
            if dcir_len > 0 and (len(Dchg)/(dcir_len/2)) >= 10:
                dcirstep = (int(len(Dchg)/(dcir_len/2)/10) + 1) * 10
            elif dcir_len > 0:
                dcirstep = int(len(Dchg)/(dcir_len/2)) + 1
            else:
                dcirstep = 1
            for i in range(len(dcir)):
                if chkir:
                    cyccal.append(n)
                    n = n + 1
                else:
                    cyccal.append(n)
                    if i % 2 == 0:
                        n = n + 1
                    else:
                        n = n + dcirstep - 1
        if len(cyccal) > 0:
            dcir["Cyc"] = cyccal
            dcir = dcir.set_index(dcir["Cyc"])
        
        Eff = Dchg/Chg
        Eff2 = Chg2/Dchg
        Dchg = Dchg/mincapacity
        Chg = Chg/mincapacity
        
        df.NewData = pd.DataFrame({"Dchg": Dchg, "RndV": Ocv, "Eff": Eff, "Chg": Chg, "DchgEng": DchgEng,
                                   "Eff2": Eff2, "Temp": Temp, "AvgV": AvgV, "OriCyc": OriCycle})
        df.NewData = df.NewData.dropna(axis=0, how='all', subset=['Dchg'])
        df.NewData = df.NewData.reset_index()
        if hasattr(dcir, "dcir"):
            df.NewData = pd.concat([df.NewData, dcir["dcir"]], axis=1, join="outer")
        else:
            df.NewData.loc[0, "dcir"] = 0
        if "TotlCycle" in df.NewData.columns:
            df.NewData = df.NewData.drop("TotlCycle", axis=1)
        timings['10_finalize'] = time.perf_counter() - t0
    
    timings['total'] = time.perf_counter() - total_start
    return timings, mincapacity, df


# ========== 측정용 PNE 함수 ==========
def pne_cycle_data_timed(raw_file_path, mincapacity, ini_crate, chkir, chkir2, mkdcir):
    """pne_cycle_data 구간별 측정 버전"""
    timings = {}
    total_start = time.perf_counter()
    
    # 1. 초기화
    t0 = time.perf_counter()
    df = pd.DataFrame()
    timings['1_init'] = time.perf_counter() - t0
    
    if (raw_file_path[-4:-1]) != "ter":
        # 2. 용량 산정
        t0 = time.perf_counter()
        from BatteryDataTool import pne_min_cap
        mincapacity = pne_min_cap(raw_file_path, mincapacity, ini_crate)
        timings['2_min_cap'] = time.perf_counter() - t0
        
        # 3. CSV 로딩 (SaveEndData.csv)
        t0 = time.perf_counter()
        Cycleraw = None
        if os.path.isdir(raw_file_path + "\\Restore\\"):
            subfile = [f for f in os.listdir(raw_file_path + "\\Restore\\") if f.endswith('.csv')]
            for files in subfile:
                if "SaveEndData.csv" in files:
                    if os.stat(raw_file_path + "\\Restore\\" + files).st_size > 0 and mincapacity is not None:
                        Cycleraw = pd.read_csv(raw_file_path + "\\Restore\\" + files, sep=",", skiprows=0, engine="c",
                                               header=None, encoding="cp949", on_bad_lines='skip')
                        break
        timings['3_csv_load'] = time.perf_counter() - t0
        
        if Cycleraw is not None:
            # 4. 컬럼 선택
            t0 = time.perf_counter()
            Cycleraw = Cycleraw[[27, 2, 10, 11, 8, 20, 45, 15, 17, 9, 24, 29, 6]]
            Cycleraw.columns = ["TotlCycle", "Condition", "chgCap", "DchgCap", "Ocv", "imp", "volmax",
                                "DchgEngD", "steptime", "Curr", "Temp", "AvgV", "EndState"]
            timings['4_preprocess'] = time.perf_counter() - t0
            
            # 5. DCIR 계산 (조건에 따라)
            t0 = time.perf_counter()
            if chkir:
                dcirtemp = Cycleraw[(Cycleraw["Condition"] == 2) & (Cycleraw["volmax"] > 4100000)]
                dcirtemp.index = dcirtemp["TotlCycle"]
                dcir = dcirtemp.imp/1000
                dcir = dcir[~dcir.index.duplicated()]
            else:
                dcirtemp = Cycleraw[(Cycleraw["Condition"] == 2) & (Cycleraw["steptime"] <= 6000)]
                dcirtemp = dcirtemp.copy()
                dcirtemp["dcir"] = dcirtemp.imp/1000
            timings['5_dcir_calc'] = time.perf_counter() - t0
            
            # 6. Pivot Table 처리 (PNE의 핵심 - 한 번에 집계)
            t0 = time.perf_counter()
            pivot_data = Cycleraw.pivot_table(
                index="TotlCycle",
                columns="Condition",
                values=["DchgCap", "DchgEngD", "chgCap", "Ocv", "Temp"],
                aggfunc={
                    "DchgCap": "sum",
                    "DchgEngD": "sum",
                    "chgCap": "sum",
                    "Ocv": "min",
                    "Temp": "max"
                }
            )
            timings['6_pivot_table'] = time.perf_counter() - t0
            
            # 7. 최종 계산
            t0 = time.perf_counter()
            Dchg = pivot_data["DchgCap"][2] / mincapacity / 1000
            DchgEng = pivot_data["DchgEngD"][2] / 1000
            Chg = pivot_data["chgCap"][1] / mincapacity / 1000
            Ocv = pivot_data["Ocv"][3] / 1000000
            Temp = pivot_data["Temp"][2] / 1000
            ChgCap2 = Chg.shift(periods=-1)
            Eff = Dchg / Chg
            Eff2 = ChgCap2 / Dchg
            AvgV = DchgEng / Dchg / mincapacity * 1000
            OriCycle = pd.Series(Dchg.index)
            timings['7_calculations'] = time.perf_counter() - t0
            
            # 8. DataFrame 생성
            t0 = time.perf_counter()
            df.NewData = pd.concat([Dchg, Ocv, Eff, Chg, DchgEng, Eff2, Temp, AvgV, OriCycle], axis=1).reset_index(drop=True)
            df.NewData.columns = ["Dchg", "RndV", "Eff", "Chg", "DchgEng", "Eff2", "Temp", "AvgV", "OriCyc"]
            df.NewData.loc[0, "dcir"] = 0
            timings['8_finalize'] = time.perf_counter() - t0
    
    timings['total'] = time.perf_counter() - total_start
    return timings, mincapacity, df


def print_timings(name, timings):
    """타이밍 결과 출력"""
    log(f"\n{'='*60}")
    log(f" {name} 구간별 실행 시간")
    log(f"{'='*60}")
    
    for key, value in sorted(timings.items()):
        if 'count' in key:
            log(f"  {key:25s}: {value}")
        else:
            log(f"  {key:25s}: {value:8.4f} 초")
    
    log(f"{'='*60}")


def main():
    # 테스트 경로
    pne_path = r"C:\Users\Ryu\battery\Rawdata\A1_MP1_4500mAh_T23_3\M02Ch073[073]"
    toyo_path = r"C:\Users\Ryu\battery\Rawdata\Q7M Sub ATL [45v 2068mAh] [23] - 250219r\3"
    
    # 테스트 파라미터
    mincapacity = 0
    ini_crate = 0.2
    chkir = False
    chkir2 = False
    mkdcir = False
    
    log("\n" + "="*60)
    log(" toyo_cycle_data vs pne_cycle_data 성능 비교")
    log("="*60)
    log(f"\nPNE 경로: {pne_path}")
    log(f"TOYO 경로: {toyo_path}")
    
    # PNE 테스트
    log("\n>>> PNE 함수 실행 중...")
    pne_timings = {}
    try:
        pne_timings, pne_cap, pne_df = pne_cycle_data_timed(
            pne_path, mincapacity, ini_crate, chkir, chkir2, mkdcir
        )
        print_timings("PNE", pne_timings)
        log(f"  감지된 용량: {pne_cap} mAh")
        if hasattr(pne_df, 'NewData'):
            log(f"  사이클 수: {len(pne_df.NewData)}")
    except Exception as e:
        log(f"PNE 오류: {e}")
        import traceback
        log(traceback.format_exc())
    
    # TOYO 테스트
    log("\n>>> TOYO 함수 실행 중...")
    toyo_timings = {}
    try:
        toyo_timings, toyo_cap, toyo_df = toyo_cycle_data_timed(
            toyo_path, mincapacity, ini_crate, chkir
        )
        print_timings("TOYO", toyo_timings)
        log(f"  감지된 용량: {toyo_cap} mAh")
        if hasattr(toyo_df, 'NewData'):
            log(f"  사이클 수: {len(toyo_df.NewData)}")
    except Exception as e:
        log(f"TOYO 오류: {e}")
        import traceback
        log(traceback.format_exc())
    
    # 비교 요약
    log("\n" + "="*60)
    log(" 성능 비교 요약")
    log("="*60)
    try:
        log(f"  PNE 총 시간:  {pne_timings['total']:8.4f} 초")
        log(f"  TOYO 총 시간: {toyo_timings['total']:8.4f} 초")
        if pne_timings['total'] > 0:
            log(f"  차이 (배율):  TOYO가 {toyo_timings['total']/pne_timings['total']:.2f}x")
    except Exception as e:
        log(f"비교 오류: {e}")
    
    log("="*60)
    
    # 결과 파일로 저장
    with open("timing_result.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    log("\n결과가 timing_result.txt에 저장되었습니다.")


if __name__ == "__main__":
    main()
