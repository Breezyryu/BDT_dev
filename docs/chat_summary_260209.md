# 2026-02-09 채팅 내용 요약

> **작성일**: 2026-02-09  
> **주제**: Toyo 데이터 로딩 최적화 및 Pandas 3.0 업그레이드 대응 버그 수정

---

## 1. Toyo Cycle Data 최적화 (Vectorization)
기존 `while` 반복문을 사용한 행 병합 로직을 Pandas **Vectorized Operation**으로 변경하여 성능을 대폭 개선했습니다.

### **핵심 로직**
- **기존 방식**: 반복문(`while`)으로 행 하나하나 비교하며 병합 (O(n²), 느림)
- **개선 방식**: `groupby`와 `cumsum`을 활용하여 연속된 충/방전 구간을 그룹화하고 일괄 병합 (O(n), 빠름)

### **주요 코드**
```python
# 연속된 동일 Condition 그룹화
cond_series = Cycleraw["Condition"]
merge_group = ((cond_series != cond_series.shift()) | (~cond_series.isin([1, 2]))).cumsum()

# 그룹별 병합 수행 (충전/방전 로직 분리)
Cycleraw = Cycleraw.groupby(merge_group, group_keys=False).apply(merge_rows, include_groups=False)
```

---

## 2. 버그 수정 및 원인 분석

### **이슈 1: `TypeError: invalid value '완료' for dtype 'int64'`**
- **증상**: `use` 컬럼에 "완료"라는 문자열을 할당할 때 에러 발생.
- **원인**: **Pandas 3.0.0 버전 업그레이드**로 인한 Type Checking 강화. 기존 버전(2.2.1)에서는 `int64` 컬럼에 문자열 할당이 암묵적으로 허용되었으나, 3.0부터는 명시적 형변환이 필요함.
- **해결**: 값을 할당하기 전에 해당 컬럼을 `object` 타입으로 변환.
  ```python
  toyo_data["use"] = toyo_data["use"].astype(object)  # 타입 변환 추가
  toyo_data.loc[(toyo_data["chno"] == 1) & (toyo_data["use"] == 0), "use"] = "완료"
  ```

### **이슈 2: `UnicodeDecodeError` (JSON 파일 읽기)**
- **증상**: JSON 파일 로딩 시 `cp949` 코덱 디코딩 에러 발생.
- **원인**: Windows 환경에서 `open()` 함수 기본 인코딩이 `cp949`로 설정되나, JSON 파일은 `UTF-8`로 저장되어 있어 인코딩 불일치 발생.
- **해결**: `open()` 함수에 `encoding='utf-8'` 명시.
  ```python
  with open(pneworkpath, encoding='utf-8') as f1:
      js1 = json.loads(f1.read())
  ```

---

## 3. 환경 변화 (Environment Changes)
- **주요 변경 사항**: `pandas` 라이브러리가 **2.2.1**에서 **3.0.0** 이상으로 업데이트됨.
- **영향**:
  - 데이터 타입 처리가 더 엄격해짐 (Implicit casting 제거).
  - 일부 Deprecated 기능 삭제 및 API 변경.
- **결론**: 이번에 발생한 `TypeError`는 라이브러리 메이저 버전 업데이트에 따른 정상적인 동작 변경임.
