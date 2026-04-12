# toyo_cycle_data 함수 성능 최적화

> **작성일**: 2026-02-06  
> **대상 파일**: `BatteryDataTool.py`  
> **대상 함수**: `toyo_cycle_data()` (Line 507~)

---

## 📋 진행 내역

### 1단계: 문제 인식
- `toyo_cycle_data` 함수가 `pne_cycle_data`보다 느리다는 사용자 보고
- 두 함수의 구조적 차이 분석 필요

### 2단계: 데이터 구조 분석
| 항목 | PNE | TOYO |
|------|-----|------|
| **폴더 구조** | `Restore` 폴더에 통합 | 채널별 수천 개 파일 |
| **사이클 데이터** | `SaveEndData.csv` 단일 파일 | `capacity.log` + 개별 파일 |
| **데이터 접근** | 한 번 로딩 후 pivot_table | 반복적 파일 읽기 |

### 3단계: 구간별 성능 측정
테스트 스크립트 `test_cycle_timing.py` 작성하여 함수 내부 구간별 시간 측정

**측정 결과 (최적화 전)**:
```
TOYO 구간별 실행 시간
============================================================
  5_merge_loop             :   2.3599 초  ← 99.4% 차지!
  5_merge_count            : 4664        ← drop/reset_index 4664번 호출
  total                    :   2.3740 초
```

### 4단계: 병목 원인 발견
- **예상**: DCIR 파일 I/O가 병목
- **실제**: while 루프 내 DataFrame 조작이 진짜 병목!
  - 매번 `drop()` + `reset_index()` 호출 → O(n²) 복잡도

### 5단계: 최적화 적용
- while 루프 → groupby 벡터화 방식으로 변경
- Line 526-548 코드 수정

### 6단계: 성능 검증
```
TOYO 구간별 실행 시간 (최적화 후)
============================================================
  5_merge_vectorized       :   0.2310 초  ← 10배 개선!
  total                    :   0.2454 초
```

---

## 📊 성능 개선 요약

| 측정 항목 | 최적화 전 | 최적화 후 | 개선율 |
|-----------|----------|----------|--------|
| **TOYO 총 시간** | 2.374초 | 0.245초 | **9.7배 빠름** |
| **병합 구간** | 2.360초 | 0.231초 | **10.2배 빠름** |
| **PNE 대비** | 3.34배 느림 | 0.29배 (더 빠름) | - |

---

## 🔧 코드 변경 내용

### 기존 코드 (Line 526-548)
```python
# Step 충전 용량, 방전 용량, 방전 에너지 계산
i = 0
while i < len(Cycleraw) - 1:
    current_cond = Cycleraw.loc[i, "Condition"]
    next_cond = Cycleraw.loc[i + 1, "Condition"]
    if current_cond in (1, 2) and current_cond == next_cond:
        if current_cond == 1:
            Cycleraw.loc[i + 1, "Cap[mAh]"] += Cycleraw.loc[i, "Cap[mAh]"]
            Cycleraw.loc[i + 1, "Ocv"] = Cycleraw.loc[i, "Ocv"]
        else:
            Cycleraw.loc[i + 1, "Cap[mAh]"] += Cycleraw.loc[i, "Cap[mAh]"]
            Cycleraw.loc[i + 1, "Pow[mWh]"] += Cycleraw.loc[i, "Pow[mWh]"]
            Cycleraw.loc[i + 1, "AveVolt[V]"] = Cycleraw.loc[i + 1, "Pow[mWh]"] / Cycleraw.loc[i + 1, "Cap[mAh]"]
        Cycleraw = Cycleraw.drop(i, axis=0).reset_index(drop=True)  # ⚠️ 병목!
    else:
        i += 1
```

### 최적화된 코드
```python
# Step 충전 용량, 방전 용량, 방전 에너지 계산 (벡터화된 병합)
Cycleraw = Cycleraw.reset_index(drop=True)
cond_series = Cycleraw["Condition"]
merge_group = ((cond_series != cond_series.shift()) | (~cond_series.isin([1, 2]))).cumsum()

def merge_rows(group):
    if len(group) == 1:
        return group.iloc[0]
    cond = group["Condition"].iloc[0]
    result = group.iloc[-1].copy()
    if cond == 1:  # 충전
        result["Cap[mAh]"] = group["Cap[mAh]"].sum()
        result["Ocv"] = group["Ocv"].iloc[0]
    elif cond == 2:  # 방전
        result["Cap[mAh]"] = group["Cap[mAh]"].sum()
        result["Pow[mWh]"] = group["Pow[mWh]"].sum()
        if result["Cap[mAh]"] != 0:
            result["AveVolt[V]"] = result["Pow[mWh]"] / result["Cap[mAh]"]
    return result

Cycleraw = Cycleraw.groupby(merge_group, group_keys=False).apply(merge_rows, include_groups=False)
Cycleraw = Cycleraw.reset_index(drop=True)
```

---

## 🎭 비유적 설명

### 변경 전: "한 장씩 정리하는 사서" 🐜
> 도서관에 4664권의 책이 흩어져 있습니다.  
> 사서가 한 권씩 확인하고, 같은 분류면 합치고,  
> **매번 전체 서가를 다시 정렬**합니다.
> 
> 📚 결과: 4664번의 서가 재정렬 = 엄청난 시간 낭비

### 변경 후: "스마트 분류 시스템" 🚜
> 모든 책에 **연속 분류 색깔표**를 먼저 붙입니다:
> - 🔴 과학1, 🔴 과학2, 🔴 과학3 → "빨간 그룹"
> - 🔵 역사1, 🔵 역사2 → "파란 그룹"
> 
> 그 다음 **색깔별로 한 번에** 합쳐서 정리합니다.
> 
> 📚 결과: 1번의 효율적인 정리 = **10배 빠름**

---

## 💡 핵심 원리

| 관점 | 변경 전 | 변경 후 |
|------|---------|---------|
| **방식** | 반복적 (Iterative) | 일괄적 (Batch) |
| **시간복잡도** | O(n²) - 매번 재정렬 | O(n) - 한 번에 분류 |
| **비유** | 하나씩 옮기는 개미 🐜 | 한 번에 옮기는 지게차 🚜 |

---

## 📁 테스트 환경

| 항목 | 값 |
|------|-----|
| **PNE 경로** | `C:\Users\Ryu\battery\Rawdata\A1_MP1_4500mAh_T23_3\M02Ch073[073]` |
| **TOYO 경로** | `C:\Users\Ryu\battery\Rawdata\Q7M Sub ATL [45v 2068mAh] [23] - 250219r\3` |
| **테스트 스크립트** | `test_cycle_timing.py` |

### 검증 결과
- ✅ 출력 데이터 동일 (사이클 수: 1178, 용량: 2068.0 mAh)
- ✅ 기능 변경 없음, 성능만 개선
