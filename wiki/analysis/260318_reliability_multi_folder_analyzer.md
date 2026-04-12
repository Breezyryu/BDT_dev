# 260318 - 신뢰성 데이터 종합 현황 분석기 신규 작성

## 변경 내용

### 신규 파일
- `Rawdata/analyze_reliability.py` — 다중 폴더 신뢰성 데이터 종합 분석 스크립트

### 기능 요약
`Rawdata/` 하위의 모든 `yymmdd` 형식 날짜 폴더를 자동 스캔하여 종합 현황 리포트를 생성하는 메타데이터 기반 분석기.

#### 핵심 기능
1. **폴더 자동 탐색**: `yymmdd` 형식 폴더 자동 발견 및 정렬 (181019~260226+)
2. **파일명 메타데이터 파싱**:
   - 카테고리 (Phone / Buds / Tab / Watch / Ring / Robot / Laptop / Phone(JDM))
   - 제조사 (ATL, SDI, LGES, Cosmx, BYD, EVE, LWN, LWM, Liwinon, ICF, TSDI, Everpower)
   - 개발단계 (MP1/MP2/POC/PP), 세대 (1st~9th), 전압, 용량(mAh), 온도 (15/23/45°C)
   - EA수, BLK, 사이클 힌트, 태그 (R-tape, Graphite, Boosting, ICF 등)
3. **그룹핑 및 이력 추적**: 동일 시험 항목을 (카테고리+모델+제조사+개발단계+용량) 키로 묶어 폴더 간 이력 추적
4. **온도 완성도**: 15/23/45°C 3조건 확보율 자동 계산
5. **BDT mAh 호환성**: `name_capacity()` 자동추출 가능 여부 사전 확인

#### 출력 파일 (Rawdata/ 에 저장)
| 파일 | 용도 |
|------|------|
| `_신뢰성_종합현황.txt` | 텍스트 리포트 (콘솔 출력과 동일) |
| `_신뢰성_종합현황.csv` | 최신 기준 종합 리스트 (Excel에서 열기 용이) |
| `_신뢰성_종합현황.json` | 전체 레코드 (프로그래밍 활용용) |

### 사용법
```bash
# Rawdata 폴더에서 직접 실행
cd Rawdata
python analyze_reliability.py

# 또는 경로 지정
python analyze_reliability.py C:\path\to\Rawdata
```

### 환경 요구사항
- Python 3.12+ (표준 라이브러리만 사용, 외부 의존성 없음)
- Excel 설치 불필요 (파일명 메타데이터 기반 분석)
- 사내/개발 환경 모두 동작

### 분석 결과 (260226 기준)
- 날짜 폴더: 32개 (250207 ~ 260226)
- 총 파일: 216개
- 고유 시험 항목: 106개
- 카테고리: Buds(7), Laptop(2), Phone(72), Phone(JDM)(6), Ring(6), Robot(2), Tab(6), Watch(5)
- 온도 완성도: 3/3 확보 11개, 2/3 확보 16개
- mAh 자동추출: 78개 가능 / 28개 수동입력 필요

### 참고
- 기존 `validate_reliability_xls.py`는 사내 Excel COM 환경 전용 검증 스크립트로 별도 유지
- 기존 `_신뢰성_종합현황.txt`은 이 스크립트 실행 시 갱신됨
