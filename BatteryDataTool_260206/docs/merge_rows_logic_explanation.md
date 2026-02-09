# 그룹별 데이터 병합 로직 (`merge_rows`) 설명

> **대상 코드**: `BatteryDataTool.py` Line 533-553  
> **작성일**: 2026-02-06

---

## 🔍 코드 역할
이 코드는 앞서 `merge_group`으로 식별된 **"연속된 충전 또는 방전 그룹"**을 실제로 어떻게 합칠지(Aggregation) 정의하고 실행하는 부분입니다.

```python
# 그룹별 집계 함수 정의
def merge_rows(group):
    if len(group) == 1:
        return group.iloc[0]
    # ... (병합 로직)
    return result

# 그룹별로 병합 수행
Cycleraw = Cycleraw.groupby(merge_group, ...).apply(merge_rows, ...)r
```

---

## 🏗️ 상세 동작 원리

### 1. `merge_rows(group)` 함수
각 그룹(예: `[충전1, 충전2, 충전3]`)을 입력받아 **하나의 행**으로 합쳐서 반환하는 함수입니다.

#### A. 단일 행 처리
```python
if len(group) == 1:
    return group.iloc[0]
```
- 그룹에 행이 하나밖에 없다면 합칠 필요가 없으므로 그대로 반환합니다. (불필요한 연산 방지)

#### B. 기준 행 설정
```python
result = group.iloc[-1].copy()  # 마지막 행 기준
```
- 병합된 결과의 기본 값들은 **그룹의 마지막 행**을 기준으로 합니다.
- 예: 종료 시간, 최종 상태 등은 마지막 데이터가 유효하기 때문입니다.

#### C. 조건별 병합 로직

**Condition 1 (충전)인 경우:**
```python
if cond == 1:
    result["Cap[mAh]"] = group["Cap[mAh]"].sum()  # 용량은 모두 더함
    result["Ocv"] = group["Ocv"].iloc[0]          # OCV는 시작 시점(첫 행) 값 유지
```
- 충전 용량은 누적되어야 하므로 합계(`sum`)를 구합니다.
- OCV(개방 회로 전압)는 충전 시작 전의 상태가 중요하므로 **첫 번째 행**의 값을 가져옵니다.

**Condition 2 (방전)인 경우:**
```python
elif cond == 2:
    result["Cap[mAh]"] = group["Cap[mAh]"].sum()  # 용량 합계
    result["Pow[mWh]"] = group["Pow[mWh]"].sum()  # 에너지 합계
    if result["Cap[mAh]"] != 0:
        # 평균 전압 = 총 에너지 / 총 용량 (가중 평균)
        result["AveVolt[V]"] = result["Pow[mWh]"] / result["Cap[mAh]"]
```
- 용량과 에너지(mWh)는 누적되므로 합계를 구합니다.
- 평균 전압(`AveVolt`)은 단순 평균이 아니라, **총 에너지 / 총 용량**으로 다시 계산하여 정확도를 유지합니다.

### 2. `groupby().apply()` 실행
```python
Cycleraw = Cycleraw.groupby(merge_group, group_keys=False).apply(merge_rows, include_groups=False)
```
- **`groupby(merge_group)`**: 앞서 계산한 그룹 ID별로 데이터를 묶습니다.
- **`apply(merge_rows)`**: 각 묶음에 대해 위에서 정의한 병합 함수를 실행합니다.
- 결과적으로 수천 개의 행이 사이클별 하나씩의 행으로 압축됩니다.

---

## 💡 요약
| 구분 | 처리 방식 | 비유 |
|------|-----------|------|
| **충전 (Cond 1)** | 용량 합산, OCV는 시작값 사용 | 물통에 물을 계속 부음 (시작 수위 기록, 총 양 합산) |
| **방전 (Cond 2)** | 용량/에너지 합산, 평균 전압 재계산 | 물통에서 물을 씀 (총 사용량 합산, 평균 수압 계산) |
| **기타 (Cond 3 등)** | 그대로 유지 (1개짜리 그룹) | 건드리지 않음 |
