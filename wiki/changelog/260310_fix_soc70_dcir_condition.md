# SOC70 DCIR 분기 조건 수정

## 날짜
2026-03-10

## 파일
- `DataTool_dev/DataTool_optRCD_proto_.py` (L1949)

## 변경 내용
```python
# Before
if (len(soc70_dcir) // 6)  > (len(df.NewData.index) // 100):

# After
if (len(soc70_dcir) // 6)  >= (len(df.NewData.index) // 100):
```

## 원인
- `same_add()` 후 DCIR 데이터 36개 → `36 // 6 = 6`
- 601 사이클 데이터 → `601 // 100 = 6`
- `6 > 6 = False` → else 분기(`[::4]`)로 잘못 진입
- else 분기는 4개 SOC 측정 패턴용이므로 6개 SOC 데이터에서 그룹 경계를 넘나들며 선택

## 증상
- SOC70 DCIR/RSS 그래프 사이클 인덱스가 `[3, 7, 105, 203, 207, 304, 402, 406, 504]`로 잘못 표시
- 100사이클 간격이 아닌 불규칙한 패턴

## 수정 후
- `6 >= 6 = True` → if 분기(`[3:][::6]`)로 정상 진입
- SOC70 인덱스: `[6, 106, 206, 305, 405, 505]` (≈100사이클 간격)
