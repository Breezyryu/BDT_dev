#!/usr/bin/env python3
"""
PNE .cyc 파일 파서 (실제 구현 가능한 기반 코드)
"""
import struct
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
import numpy as np
import pandas as pd

@dataclass
class CycRecord:
    """단일 .cyc 데이터 레코드 (32바이트 = float32 × 8)
    
    필드 의미:
      [0-7]: 실시간 측정값 (전압, 전류, 용량, 시간 등 - 값을 보고 판정)
      
    SaveEndData.csv와의 관계:
      - .cyc: 연속적인 측정값 기록 (1초 또는 더 짧은 주기)
      - .csv: 각 스텝 종료 시점의 요약 데이터
    """
    field0: float
    field1: float
    field2: float
    field3: float
    field4: float
    field5: float
    field6: float
    field7: float

class CycFileParser:
    """PNE .cyc 파일 파서"""
    
    HEADER_SIZE = 512
    RECORD_SIZE = 32  # float32 × 8
    RECORD_FORMAT = '<8f'  # Little-endian float32 × 8
    
    def __init__(self, cyc_file_path: str):
        self.file_path = Path(cyc_file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"파일 없음: {cyc_file_path}")
        
        self.file_size = self.file_path.stat().st_size
        self.num_records = (self.file_size - self.HEADER_SIZE) // self.RECORD_SIZE
        self.header_info = self._parse_header()
    
    def _parse_header(self) -> dict:
        """헤더(512바이트) 파싱"""
        with open(self.file_path, 'rb') as f:
            header = f.read(self.HEADER_SIZE)
        
        # 매직 번호
        magic = struct.unpack('<2H2B', header[0:6])
        
        # 날짜/시간 (ASCII)
        datetime_str = header[8:28].rstrip(b'\x00').decode('ascii', errors='ignore')
        
        # 파일 설명
        desc = header[72:103].rstrip(b'\x00').decode('ascii', errors='ignore')
        
        return {
            'magic': magic,
            'datetime': datetime_str,
            'description': desc,
            'file_size': self.file_size,
            'num_records': self.num_records,
            'record_size': self.RECORD_SIZE,
        }
    
    def read_record(self, record_index: int) -> Optional[CycRecord]:
        """인덱스로 특정 레코드 읽기"""
        if record_index < 0 or record_index >= self.num_records:
            return None
        
        offset = self.HEADER_SIZE + record_index * self.RECORD_SIZE
        
        with open(self.file_path, 'rb') as f:
            f.seek(offset)
            data = f.read(self.RECORD_SIZE)
        
        if len(data) < self.RECORD_SIZE:
            return None
        
        fields = struct.unpack(self.RECORD_FORMAT, data)
        return CycRecord(*fields)
    
    def read_range(self, start_idx: int = 0, end_idx: Optional[int] = None) -> List[CycRecord]:
        """범위 단위로 레코드 읽기 (메모리 효율적)"""
        if end_idx is None:
            end_idx = self.num_records
        
        records = []
        with open(self.file_path, 'rb') as f:
            for i in range(start_idx, min(end_idx, self.num_records)):
                offset = self.HEADER_SIZE + i * self.RECORD_SIZE
                f.seek(offset)
                data = f.read(self.RECORD_SIZE)
                
                if len(data) < self.RECORD_SIZE:
                    break
                
                fields = struct.unpack(self.RECORD_FORMAT, data)
                records.append(CycRecord(*fields))
        
        return records
    
    def read_all_as_numpy(self) -> np.ndarray:
        """전체 데이터를 NumPy 배열로 읽기 (고속)"""
        data = np.memmap(self.file_path, dtype=np.float32, mode='r', 
                        offset=self.HEADER_SIZE, shape=(self.num_records, 8))
        return np.copy(data)  # 메모리 맵을 실제 배열로 변환
    
    def get_info(self) -> str:
        """파일 정보 출력"""
        info = self.header_info
        return f"""
PNE .cyc 파일 정보
==================
경로: {self.file_path}
파일 크기: {info['file_size']:,} 바이트
레코드 수: {info['num_records']:,}개
날짜/시간: {info['datetime']}
설명: {info['description']}
"""

# ──────────────────────────────────────────────────
# 편의 함수 (proto 코드 통합용)
# ──────────────────────────────────────────────────

def load_cyc_data_to_dataframe(cyc_file_path: str) -> pd.DataFrame:
    """
    .cyc 파일을 pandas DataFrame으로 로드
    
    Args:
        cyc_file_path: .cyc 파일 경로
        
    Returns:
        DataFrame with columns [time, field0, field1, ..., field7]
        또는 None if load failed
    """
    try:
        parser = CycFileParser(cyc_file_path)
        data = parser.read_all_as_numpy()
        
        import pandas as pd
        df = pd.DataFrame(data, columns=['field0', 'field1', 'field2', 'field3', 
                                         'field4', 'field5', 'field6', 'field7'])
        
        # 시간 열 추가 (기록 수 기반, 1초 단위로 가정)
        df.insert(0, 'time_s', range(len(df)))
        
        return df
    except Exception as e:
        print(f"Error loading CYC file: {e}")
        return None

def find_and_load_cyc_file(channel_path: str) -> tuple[bool, pd.DataFrame | None]:
    """
    채널 경로에서 .cyc 파일을 찾아서 로드
    
    Args:
        channel_path: 채널 폴더 경로 (예: M01Ch025[025])
        
    Returns:
        (found, data_df)
        found: .cyc 파일 존재 여부
        data_df: 로드된 데이터프레임 또는 None
    """
    from pathlib import Path
    
    ch_path = Path(channel_path)
    cyc_files = list(ch_path.glob("*.cyc"))
    
    if not cyc_files:
        return False, None
    
    cyc_file = cyc_files[0]
    df = load_cyc_data_to_dataframe(str(cyc_file))
    
    return True, df

# 사용 예시
if __name__ == '__main__':
    cyc_file = r"C:\Users\Ryu\battery\python\BDT_dev\rawdata\250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half-14pi-GITT-0.1C-T23\M01Ch025[025]\250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half-14pi-GITT-0.1C-T23.cyc"
    
    # 파서 인스턴스 생성
    parser = CycFileParser(cyc_file)
    
    # 파일 정보 출력
    print(parser.get_info())
    
    # 처음 10개 레코드 읽기
    print("\n첫 10개 레코드:")
    print(f"{'Index':>6} {'F0':>12} {'F1':>12} {'F2':>12} {'F3':>12} {'F4':>12} {'F5':>12} {'F6':>12} {'F7':>12}")
    print("-" * 105)
    
    records = parser.read_range(0, 10)
    for i, rec in enumerate(records):
        print(f"{i:>6d} {rec.field0:>12.2f} {rec.field1:>12.2f} {rec.field2:>12.2f} {rec.field3:>12.2f} {rec.field4:>12.2f} {rec.field5:>12.2f} {rec.field6:>12.2f} {rec.field7:>12.2f}")
    
    # 전체 데이터를 NumPy로 고속 로드
    print("\n전체 데이터 로드 (NumPy 사용)...")
    import time
    start = time.time()
    data = parser.read_all_as_numpy()
    elapsed = time.time() - start
    print(f"  완료: {data.shape} 배열 ({elapsed:.3f}초)")
    print(f"  메모리 사용: {data.nbytes / 1024 / 1024:.1f} MB")
    
    # 필드별 통계
    print("\n필드별 통계 (NumPy):")
    print(f"{'Field':>6} {'Min':>12} {'Max':>12} {'Mean':>12} {'Std':>12}")
    print("-" * 54)
    for i in range(8):
        col = data[:, i]
        print(f"{'F'+str(i):>6} {col.min():>12.2f} {col.max():>12.2f} {col.mean():>12.2f} {col.std():>12.2f}")
