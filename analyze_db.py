#!/usr/bin/env python3
"""
PNE .db (SQLite) 파일 분석
"""
import sqlite3
import os

db_file = r"C:\Users\Ryu\battery\python\BDT_dev\rawdata\250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half-14pi-GITT-0.1C-T23\M01Ch025[025]\250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half-14pi-GITT-0.1C-T23.db"

print(f"파일 존재: {os.path.exists(db_file)}")
print(f"파일 크기: {os.path.getsize(db_file):,} bytes\n")

try:
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # 테이블 목록 조회
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"=== 테이블 목록 ({len(tables)}개) ===")
    for table in tables:
        print(f"  - {table[0]}")
    
    # 각 테이블의 구조와 데이터 미리보기
    for table_name in [t[0] for t in tables][:5]:  # 처음 5개만
        print(f"\n=== 테이블: {table_name} ===")
        
        # 컬럼 정보
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        print("컬럼:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # 데이터 행 수
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        row_count = cursor.fetchone()[0]
        print(f"행 수: {row_count:,}")
        
        # 샘플 데이터 (처음 3행)
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
        rows = cursor.fetchall()
        if rows:
            print("샘플 데이터:")
            for row in rows[:2]:
                print(f"  {row}")
    
    conn.close()
    
except sqlite3.DatabaseError as e:
    print(f"❌ SQLite 데이터베이스 오류: {e}")
    print("   파일이 SQLite 데이터베이스가 아니거나 손상되어 있을 수 있습니다.")
except Exception as e:
    print(f"❌ 오류: {e}")
