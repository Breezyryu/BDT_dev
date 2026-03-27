#!/usr/bin/env python3
"""
SaveData.csv와 .cyc 파일 구조 비교 분석
- SaveEndData.csv 컬럼 인덱스 매핑 (proto 코드에서 추출)
- .cyc 필드와의 연관성 파악
"""
import pandas as pd
from pathlib import Path

# SaveData.csv 파일 찾기
base_path = Path(r"C:\Users\Ryu\battery\python\BDT_dev\rawdata")
csv_files = list(base_path.glob("**/*SaveData*.csv"))

if csv_files:
    csv_file = csv_files[0]
    print(f"분석할 CSV 파일: {csv_file.name}")
    print(f"파일 크기: {csv_file.stat().st_size:,} 바이트\n")
    
    # SaveEndData.csv 읽기
    df = pd.read_csv(csv_file, header=None, encoding='cp949', on_bad_lines='skip')
    print(f"DataFrame 형태: {df.shape}")
    print(f"컬럼 수: {df.shape[1]}")
    print(f"행 수: {df.shape[0]}\n")
    
    # proto 코드에서 발견한 컬럼 인덱스 매핑
    column_mapping = {
        2: "StepType (1=Chg, 2=Dchg, 3=Rest, 8=Loop)",
        6: "EndState (65=CC, 66=CCCV)",
        8: "EndVoltage (μV)",
        9: "EndCurrent (μA)",
        27: "TotlCycle",
        32: "CV구간 시간 (centisec)",
        38: "CC구간 시간 (centisec)",
        39: "CC구간 용량 (μAh)",
        40: "CV구간 용량 (μAh)",
    }
    
    print("=" * 100)
    print("SaveEndData.csv 분석 결과 (proto 코드 기반)")
    print("=" * 100)
    print(f"\nproto 코드가 사용하는 컬럼들:")
    print("-" * 100)
    
    for col_idx, desc in sorted(column_mapping.items()):
        print(f"  [{col_idx:2d}] {desc}")
    
    # 처음 10행의 주요 컬럼 값
    print(f"\nFirst 10 rows with key columns:")
    print("-" * 100)
    
    important_cols = [2, 6, 8, 9, 27, 32, 38, 39, 40]
    important_cols = [c for c in important_cols if c < df.shape[1]]
    
    print(f"{'Row':>3} " + " ".join([f"{c:>12}" for c in important_cols]))
    for i in range(min(10, len(df))):
        row_data = f"{i:>3} "
        for col in important_cols:
            val = df.iloc[i, col]
            row_data += f"{val:>12.0f} " if isinstance(val, (int, float)) else f"{str(val):>12} "
        print(row_data)
    
    print(f"\nAll columns range analysis:")
    print("-" * 100)
    
    first_row = df.iloc[0]
    print(f"{'Col':>3} {'Min':>12} {'Max':>12} {'Mean':>12} {'Description'}")
    print("-" * 100)
    
    for col in range(min(41, df.shape[1])):
        col_data = df.iloc[:, col]
        try:
            col_numeric = pd.to_numeric(col_data, errors='coerce')
            min_val = col_numeric.min()
            max_val = col_numeric.max()
            mean_val = col_numeric.mean()
            
            desc = column_mapping.get(col, "")
            if desc:
                desc = desc[:40]
            
            print(f"{col:>3d} {min_val:>12.0f} {max_val:>12.0f} {mean_val:>12.1f}  {desc}")
        except:
            print(f"{col:>3d} {'N/A':>12} {'N/A':>12} {'N/A':>12}  (문자열 컬럼)")
    
    # .cyc 파일의 필드와 비교
    print(f"\n' + '=" * 100)
    print(".cyc 파일의 float32 필드와 매칭 추론")
    print("=" * 100)
    
    print("""
.cyc 파일 구조 (32바이트 레코드, float32 × 8):
[0] field0
[1] field1
[2] field2
[3] field3
[4] field4
[5] field5
[6] field6
[7] field7

SaveEndData.csv의 주요 필드들이 어느 .cyc 필드에 매칭될지 추론:
- 전압 (EndVoltage [8] in CSV) → .cyc [0] or [1]? (값 범위 23000-24000 mV 추정)
- 전류 (EndCurrent [9] in CSV) → .cyc 필드? (양수/음수 가능)
- 사이클 번호 (TotlCycle [27] in CSV) → 정수여야 함
- 시간 정보 → float32로 저장될 예정
- 온도 정보 → 일반적으로 포함됨

데이터에서 관찰한 사항:
""")
    
    # float32 필드의 통계를 다시 보면서 추론
    # 처음 몇 레코드에서 특이한 값들이 보임
    
    print("SaveEndData의 전형적인 범위:")
    print(f"  - EndVoltage [8]: {df.iloc[:, 8].describe()}")
    print(f"  - EndCurrent [9]: {df.iloc[:, 9].describe()}")
    print(f"  - CV Time [32]: {df.iloc[:, 32].describe()}")
    print(f"  - CC Time [38]: {df.iloc[:, 38].describe()}")
    print(f"  - Capacity [39]: {df.iloc[:, 39].describe()}")
    
else:
    print("SaveData.csv 파일을 찾을 수 없습니다.")
