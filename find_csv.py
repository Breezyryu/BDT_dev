#!/usr/bin/env python3
"""
SaveEndData.csv 파일 찾기 및 분석
"""
from pathlib import Path

base_path = Path(r"C:\Users\Ryu\battery\python\BDT_dev\rawdata")

# SaveEndData.csv 찾기
csv_files = list(base_path.glob("**/*SaveData*.csv"))

print(f"찾은 CSV 파일 수: {len(csv_files)}")
for f in csv_files[:10]:
    print(f"\n파일: {f.name}")
    print(f"경로: {f.parent}")
    print(f"크기: {f.stat().st_size:,} 바이트")
    
    # 처음 몇 줄 읽기
    with open(f, encoding='cp949', errors='ignore') as file:
        lines = [file.readline() for _ in range(5)]
        print(f"처음 5줄:")
        for i, line in enumerate(lines, 1):
            print(f"  {i}: {line[:100]}")
