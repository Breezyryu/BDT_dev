# .cyc 파일 파서 - proto 코드 통합 가이드

## 현재 상황

### ✅ 완료된 것
1. **PNE .cyc 파일 포맷 분석**
   - 헤더: 512바이트 (메타데이터)
   - 데이터: 3.65백만 개 레코드 × 32바이트 (float32 × 8)
   - 암호화: 없음 (엔트로피 2.78)

2. **Python 파서 개발** (`parse_pne_cyc.py`)
   - `CycFileParser` 클래스: 파일 읽기 및 레코드 접근
   - `load_cyc_data_to_dataframe()`: DataFrame 변환
   - `find_and_load_cyc_file()`: 채널에서 .cyc 파일 자동 찾기
   - 성능: 3.65M 레코드 로드 0.05초

3. **필드 매핑 기초 작업**
   - SaveEndData.csv 컬럼 인덱스 파악
   - 필드 범위 통계 수집

### ⏳ 다음 단계 옵션

## 옵션 1: 최소 통합 (30분)
proto 코드에서 선택적으로 .cyc 데이터 사용

```python
# DataTool_optRCD_proto_.py 최상단에 추가
try:
    from parse_pne_cyc import load_cyc_data_to_dataframe, find_and_load_cyc_file
    HAS_CYC_PARSER = True
except ImportError:
    HAS_CYC_PARSER = False

# 데이터 로딩 부분에서 선택
if HAS_CYC_PARSER:
    found, cyc_data = find_and_load_cyc_file(channel_path)
    if found and cyc_data is not None:
        # .cyc 데이터 사용
        pass
```

## 옵션 2: 완전 통합 (2-3시간)
SaveEndData.csv 대신 .cyc 파일을 메인 데이터 소스로 사용

- .cyc 파일에서 직접 필드 의미 파악
- 필드별 범위 기반 자동 매핑 (전압, 전류, 온도 등)
- CSV로 내보내기 기능

## 사용 방법

### 기본 사용 (스탠드얼론)
```python
from parse_pne_cyc import CycFileParser

parser = CycFileParser("path/to/data.cyc")
print(parser.get_info())

# 범위 로드
records = parser.read_range(0, 100)
for rec in records:
    print(f"Field0={rec.field0}, Field1={rec.field1}, ...")

# 전체 NumPy 로드
data = parser.read_all_as_numpy()  # Shape: (3654454, 8)
```

### DataFrame으로 로드
```python
df = load_cyc_data_to_dataframe("path/to/data.cyc")
# Columns: time_s, field0, field1, ..., field7
```

### proto 코드에서 사용
```python
if HAS_CYC_PARSER:
    found, df_cyc = find_and_load_cyc_file(channel_path)
    if found:
        # df_cyc는 pandas DataFrame
        # SaveEndData.csv 대체 또는 보완
```

## 파일 위치

- **파서**: `parse_pne_cyc.py` (BDT_dev 루트)
- **배포**: 필요시 `DataTool_dev/` 또는 `analysis_dev_env/` 폴더로 이동

## 향후 개선사항

1. **필드 의미 자동 추론**
   - 값 범위 기반 필드 타입 판정
   - SaveEndData.csv와의 상관 분석

2. **CSV 내보내기**
   - .cyc → CSV 변환 함수
   - 프로토 메뉴에 "CYC 데이터 내보내기" 추가

3. **실시간 모니터링**
   - 측정 중인 .cyc 파일 실시간 읽기
   - 마지막 N개 레코드만 로드하는 고속 모드

## 주의사항

- 파일 인코딩: 헤더는 ASCII, 메인 데이터는 binary (float32)
- 경로에 특수문자 허용 (파일명 한글 O)
- 메모리: 전체 로드 시 약 112MB
- 성능: 3.65M 레코드 로드 0.05초 (매우 빠름)
