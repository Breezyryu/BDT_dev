"""
workers 수 변화에 따른 병렬 CSV 로딩 벤치마크
- 실제 rawdata 폴더의 CSV 파일을 pandas로 읽는 I/O 작업 기준
- workers=1,2,4,6,8,12,16,20 비교
"""
import os, sys, time, gc, re
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import psutil

# ── 채널 폴더 판별 (proto_ 코드에서 가져옴) ──
def _is_channel_folder(name):
    if re.search(r'\[.*?\]', name):
        return True
    return name.strip().isdigit()

def check_cycler(raw_file_path):
    return os.path.isdir(os.path.join(raw_file_path, "Pattern"))

# ── 단일 채널 CSV 로딩 작업 (실제 사이클 분석과 유사한 I/O + 파싱) ──
def load_channel_csv(task_info):
    """단일 채널 폴더에서 CSV 파일을 읽고 pandas DataFrame으로 파싱"""
    folder_path, is_pne, folder_idx, sub_idx = task_info
    rows_read = 0
    files_read = 0
    mem_bytes = 0
    
    try:
        if is_pne:
            # PNE: Restore 폴더의 SaveEndData.csv 로드
            restore = os.path.join(folder_path, "Restore")
            if os.path.isdir(restore):
                for f in os.listdir(restore):
                    if f.endswith('.csv'):
                        fp = os.path.join(restore, f)
                        if os.path.getsize(fp) > 0:
                            df = pd.read_csv(fp, sep=",", header=None, 
                                           encoding="cp949", engine="c",
                                           on_bad_lines='skip')
                            rows_read += len(df)
                            mem_bytes += df.memory_usage(deep=True).sum()
                            files_read += 1
                            del df
        else:
            # Toyo: 폴더 내 CSV 파일 로드
            for f in os.listdir(folder_path):
                if f.endswith('.csv') or f.endswith('.CSV'):
                    fp = os.path.join(folder_path, f)
                    if os.path.getsize(fp) > 0:
                        df = pd.read_csv(fp, sep=",", header=None,
                                       engine="c", on_bad_lines='skip')
                        rows_read += len(df)
                        mem_bytes += df.memory_usage(deep=True).sum()
                        files_read += 1
                        del df
    except Exception as e:
        pass
    
    return (folder_idx, sub_idx, files_read, rows_read, mem_bytes)

# ── 벤치마크 실행 ──
def run_benchmark(tasks, max_workers):
    """주어진 worker 수로 전체 task를 병렬 실행하고 시간/리소스 측정"""
    gc.collect()
    
    proc = psutil.Process()
    mem_before = proc.memory_info().rss
    cpu_before = psutil.cpu_percent(interval=None, percpu=True)
    
    t0 = time.perf_counter()
    
    total_rows = 0
    total_files = 0
    total_mem = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(load_channel_csv, t): t for t in tasks}
        for future in as_completed(futures):
            result = future.result()
            if result:
                _, _, files, rows, mem = result
                total_files += files
                total_rows += rows
                total_mem += mem
    
    elapsed = time.perf_counter() - t0
    
    mem_after = proc.memory_info().rss
    cpu_after = psutil.cpu_percent(interval=0.1, percpu=True)
    avg_cpu = sum(cpu_after) / len(cpu_after)
    peak_mem_mb = (mem_after - mem_before) / (1024**2)
    
    return {
        'workers': max_workers,
        'elapsed': elapsed,
        'files': total_files,
        'rows': total_rows,
        'df_mem_mb': total_mem / (1024**2),
        'proc_mem_delta_mb': peak_mem_mb,
        'avg_cpu': avg_cpu,
    }

def main():
    base = os.path.join(os.path.dirname(__file__), "rawdata")
    
    folders = [
        '250207_250307_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 1-100cyc',
        '250219_250319_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 101-200cyc',
        '250304_250404_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 201-300cyc',
        '250317_251231_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 301-400cyc',
        '251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202',
        '251029_251229_05_나무늬_2335mAh_Q8 선상 ATL SEU4 LT @1-401',
        '251029_251229_05_나무늬_2935mAh_Q8 선상 ATL SEU4 LT @1-401 - 복사본',
        '251029_260129_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 50CY HT @1-801',
        '251029_260129_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 75CY HT @1-801',
        '251029_260129_05_나무늬_2335mAh_Q8 선상 ATL SEU4 HT @1-801',
        '251029_260429_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 30CY @1-1202',
        '251029_260429_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 50CY @1-1202',
        '251029_260429_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 75CY @1-1202',
        '251113_260113_05_나무늬_2335mAh_Q8 선상 ATL SEU4 2.9V 50CY LT @1-401',
        '251113_260213_05_나무늬_2335mAh_Q8 선상 ATL 2.9V 30CY HT @1-801',
        '251209_260209_05_나무늬_2335mAh_Q8 선상 ATL SEU4 HT @301-801',
        '260115_260630_02_홍승기_2335mAh_Q8 선상 ATL SEU4 HT@1-802',
        '260119_260616_03_홍승기_2485mAh_Q8 ATL Sub 2.0C Rss RT',
        '260119_260616_03_홍승기_2485mAh_Q8 ATL Sub 2C 2.9V 100Cy',
        '260119_260616_03_홍승기_2369mAh_Q8 ATL Main 2.0C Rss RT',
        '260130_260630_03_홍승기_2369mAh_Q8 Main 2C Rss RT CH32 57Cy-RE',
        '260130_260630_03_홍승기_3456mAh_Q8 Main 2C Rss RT CH32 57Cy-RE',
        '260130_260630_03_홍승기_Q8 Main 2C Rss RT CH32 57Cy-RE',
        '260126_260630_3_홍승기_2485mAh_Q8 ATL Sub 2_9V 100cy test HT 1to100cy-2',
        '260209_260630_2_홍승기_2485mAh_Q8 ATL Sub 2_9V 100cy test HT 100to199cy re3',
        'A1_MP1_4500mAh_T23_1',
        'A1_MP1_4500mAh_T23_2',
        'A1_MP1_4500mAh_T23_3',
        'Dateset_A1_Gen4 2C ATL MP2 [45V 4470mAh] [23] blk2',
        'Gen4 2C ATL MP2 [45V 4470mAh] [23] blk7 - 240131',
        'M1 ATL [45V 4175mAh]',
        'Q7M Inner ATL_45V 1689mAh BLK1 20EA [23] - 250304',
        'Q7M Main ATL [45V_1680mAh][23] blk7 20ea - 250228',
        'Q7M Sub ATL [45v 2068mAh] [23] - 250219r',
    ]
    
    # task 목록 생성 (실제 코드와 동일한 로직)
    tasks = []
    pne_count = 0
    toyo_count = 0
    for i, foldername in enumerate(folders):
        cyclefolder = os.path.join(base, foldername)
        if not os.path.isdir(cyclefolder):
            continue
        is_pne = check_cycler(cyclefolder)
        subfolder = [f.path for f in os.scandir(cyclefolder)
                     if f.is_dir() and _is_channel_folder(f.name)]
        for j, folder_path in enumerate(subfolder):
            if "Pattern" not in folder_path:
                tasks.append((folder_path, is_pne, i, j))
                if is_pne:
                    pne_count += 1
                else:
                    toyo_count += 1
    
    print(f"=== 벤치마크 설정 ===")
    print(f"유효 폴더: {len(folders)}")
    print(f"총 채널(task): {len(tasks)} (PNE: {pne_count}, Toyo: {toyo_count})")
    print(f"CPU: {psutil.cpu_count(logical=False)}P/{os.cpu_count()}L")
    print(f"가용 RAM: {psutil.virtual_memory().available / (1024**3):.1f} GB")
    print()
    
    # 워밍업 (OS 캐시 준비)
    print("워밍업 (workers=2)...")
    run_benchmark(tasks, 2)
    gc.collect()
    time.sleep(1)
    
    # 벤치마크 실행
    worker_counts = [1, 2, 4, 6, 8, 12, 16, 20]
    results = []
    
    print(f"\n{'workers':>7} {'시간(s)':>8} {'파일수':>6} {'행수':>10} {'DF메모리':>10} {'CPU%':>6} {'속도비':>6}")
    print("-" * 65)
    
    base_time = None
    for w in worker_counts:
        gc.collect()
        time.sleep(0.5)
        
        r = run_benchmark(tasks, w)
        results.append(r)
        
        if base_time is None:
            base_time = r['elapsed']
        
        speedup = base_time / r['elapsed'] if r['elapsed'] > 0 else 0
        print(f"{r['workers']:>7} {r['elapsed']:>8.2f} {r['files']:>6} {r['rows']:>10,} "
              f"{r['df_mem_mb']:>8.1f}MB {r['avg_cpu']:>5.1f}% {speedup:>5.2f}x")
    
    # 최적 결과
    best = min(results, key=lambda x: x['elapsed'])
    print(f"\n★ 최적 workers: {best['workers']} ({best['elapsed']:.2f}s)")
    print(f"  workers=1 대비 {base_time/best['elapsed']:.2f}x 속도 향상")

if __name__ == "__main__":
    main()
