#!/usr/bin/env python3
"""
SaveData.csv analysis - key columns statistics
"""
import pandas as pd
from pathlib import Path

base_path = Path(r"C:\Users\Ryu\battery\python\BDT_dev\rawdata")
csv_files = list(base_path.glob("**/*SaveData*.csv"))

if csv_files:
    csv_file = csv_files[0]
    df = pd.read_csv(csv_file, header=None, encoding='cp949', on_bad_lines='skip')
    print(f"File: {csv_file.name}")
    print(f"Shape: {df.shape}\n")
    
    # Key columns from proto code
    cols = {8: "EndVoltage(uV)", 9: "EndCurrent(uA)", 27: "TotCycle", 32: "CVTime", 38: "CCTime", 39: "CCCap"}
    
    print("SaveEndData key column statistics:")
    print(f"{'Col':>3} {'Min':>14} {'Max':>14} {'Mean':>14} {'Description'}")
    print("-" * 65)
    for col, desc in sorted(cols.items()):
        if col < df.shape[1]:
            data = pd.to_numeric(df.iloc[:, col], errors='coerce')
            print(f"{col:>3d} {data.min():>14.0f} {data.max():>14.0f} {data.mean():>14.1f}  {desc}")

    # First row analysis
    print(f"\n\nFirst 5 rows detail (all columns):")
    print("-" * 100)
    for i in range(min(5, len(df))):
        print(f"Row {i}:")
        for j in range(min(15, df.shape[1])):
            print(f"  [{j:2d}] = {df.iloc[i, j]}")
        print()
