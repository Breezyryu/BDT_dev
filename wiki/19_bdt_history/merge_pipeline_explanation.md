---
title: "Toyo Cycle 병합 파이프라인 설명 (그룹핑 + Aggregation)"
tags: [bdt-history, vectorization, pandas, toyo-cycle]
updated: 2026-04-21
---

# Toyo Cycle 병합 파이프라인 설명 (그룹핑 + Aggregation)

> 📎 2026-04-21: `vectorized_merge_logic_explanation.md`(그룹 ID 생성)와 `merge_rows_logic_explanation.md`(그룹별 집계)를 하나의 파이프라인 문서로 병합.

> **대상 코드**: `BatteryDataTool.py` / `DataTool_optRCD_proto_.py` `toyo_cycle_data()` 의 Cycleraw 병합 구간 (L531~L553 부근)
> **원본 작성일**: 2026-02-06

---

## 파이프라인 개요

연속된 충전(Condition=1) 또는 방전(Condition=2) 행들을 **벡터화된 방식으로** 한 행씩으로 압축하는 2단계 파이프라인:

1. **그룹 ID 생성** — `cumsum` 트릭으로 연속 구간에 같은 그룹 번호 부여
2. **그룹별 집계** — `merge_rows()` 함수로 각 그룹을 하나의 대표 행으로 병합

기존 while 루프 + `drop()` + `reset_index()` 방식(O(n²))을 대체하여 **O(n) 복잡도**, 대규모 데이터에서 **2~10배 이상 속도 향상**을 얻는다.

---

## 1단계: 그룹 ID 생성 (`cumsum` 벡터화)

```python
merge_group = ((cond_series != cond_series.shift()) | (~cond_series.isin([1, 2]))).cumsum()
```

이 한 줄은 연속된 충전(1) 또는 방전(2) 데이터를 하나의 그룹으로 묶고, 그 외의 상태(휴지 등)나 상태가 바뀌는 지점에서 그룹 ID를 증가시킨다.

### 단계별 동작

#### (1) `cond_series.shift()` — 한 칸 아래로 이동
이전 행의 값과 비교하기 위해 데이터를 한 칸 내린다.
```
원본:       [1, 1, 1, 2, 2, 3, 1, 1]
shift():    [NaN, 1, 1, 1, 2, 2, 3, 1]
```

#### (2) `cond_series != cond_series.shift()` — 변화 지점 감지
현재 값 ≠ 이전 값이면 `True`. 상태(Condition)가 변하는 순간을 포착.
```
결과:  [True, False, False, True, False, True, True, False]
        ↑ 시작     ↑ 유지   ↑ 변함  ↑ 유지  ↑ 변함
```

#### (3) `~cond_series.isin([1, 2])` — 병합 제외 마스크
충/방전(1,2)이 **아닌** 행(휴지, 대기 등)은 독립 그룹으로 강제.
```
원본:          [1, 1, 1, 2, 2, 3, 1, 1]
isin([1,2]):   [T, T, T, T, T, F, T, T]
~(NOT):        [F, F, F, F, F, T, F, F]   # 3은 병합 제외
```

#### (4) `|` (OR) — 두 조건 결합
"값이 바뀌었거나" 또는 "충/방전이 아니면" 새 그룹 시작.
```
변화:  [T, F, F, T, F, T, T, F]
예외:  [F, F, F, F, F, T, F, F]
OR:    [T, F, F, T, F, T, T, F]
```

#### (5) `.cumsum()` — 누적합으로 그룹 ID 할당
`True`(1)가 나올 때마다 누적. `False`(0) 구간은 값이 유지되어 같은 그룹.
```
불리언:  [1, 0, 0, 1, 0, 1, 1, 0]
cumsum:  [1, 1, 1, 2, 2, 3, 4, 4]
         └그룹1┘ └그룹2┘ └3┘└그룹4┘
```

### 최종 예시

```
원본 데이터: [충전, 충전, 충전, 방전, 방전, 휴지, 충전, 충전]
그룹 ID:     [  1,   1,   1,   2,   2,   3,   4,   4  ]
             └───그룹1───┘ └─그룹2─┘  ↑   └─그룹4─┘
                                     휴지는 단독
```

---

## 2단계: 그룹별 집계 (`merge_rows` 함수)

```python
def merge_rows(group):
    if len(group) == 1:
        return group.iloc[0]
    cond = group["Condition"].iloc[0]
    result = group.iloc[-1].copy()            # 마지막 행을 기준으로 복사
    if cond == 1:
        result["Cap[mAh]"] = group["Cap[mAh]"].sum()
        result["Ocv"] = group["Ocv"].iloc[0]
    elif cond == 2:
        result["Cap[mAh]"] = group["Cap[mAh]"].sum()
        result["Pow[mWh]"] = group["Pow[mWh]"].sum()
        result["Ocv"] = group["Ocv"].iloc[0]
        if result["Cap[mAh]"] != 0:
            result["AveVolt[V]"] = result["Pow[mWh]"] / result["Cap[mAh]"]
    return result

Cycleraw = Cycleraw.groupby(merge_group, group_keys=False).apply(
    merge_rows, include_groups=False
)
```

### 동작 원리

#### (A) 단일 행 그룹
```python
if len(group) == 1:
    return group.iloc[0]
```
행이 하나뿐이면 병합할 것이 없으므로 그대로 반환 (불필요한 연산 방지).

#### (B) 기준 행 설정
```python
result = group.iloc[-1].copy()
```
병합 결과의 기본 값은 **마지막 행** 기준. 종료 시간, 최종 상태 등은 마지막 행의 값이 유효.

#### (C) Condition별 병합 규칙

**Condition 1 (충전)**:
```python
result["Cap[mAh]"] = group["Cap[mAh]"].sum()    # 용량 누적
result["Ocv"] = group["Ocv"].iloc[0]            # OCV는 시작 시점(첫 행)
```
- 충전 용량은 누적 → `sum()`
- OCV는 충전 직전 상태가 중요 → 첫 번째 행의 값

**Condition 2 (방전)**:
```python
result["Cap[mAh]"] = group["Cap[mAh]"].sum()    # 용량 누적
result["Pow[mWh]"] = group["Pow[mWh]"].sum()    # 에너지 누적
if result["Cap[mAh]"] != 0:
    result["AveVolt[V]"] = result["Pow[mWh]"] / result["Cap[mAh]"]
```
- 용량·에너지 누적
- 평균 전압은 **총 에너지 / 총 용량**으로 가중평균 재계산 (단순 평균 X)

**기타 (Cond 3 등)**: 1단계에서 이미 독립 그룹이므로 (A) 경로로 그대로 유지.

#### (D) 실행
```python
Cycleraw = Cycleraw.groupby(merge_group, group_keys=False).apply(merge_rows, ...)
```
- `groupby(merge_group)` — 1단계에서 생성한 그룹 ID로 묶음
- `apply(merge_rows)` — 각 그룹에 집계 함수 적용
- 결과: 수천 개의 행이 사이클별 한 행으로 압축

### 비유 요약

| 구분 | 처리 | 비유 |
|------|------|------|
| 충전 (Cond 1) | 용량 합산, OCV는 시작값 | 물통에 물 부음 (시작 수위 기록, 총 양 합산) |
| 방전 (Cond 2) | 용량/에너지 합산, 평균 전압 재계산 | 물통에서 물 씀 (총 사용량 합산, 평균 수압 계산) |
| 기타 (Cond 3 등) | 그대로 유지 (단일 행 그룹) | 건드리지 않음 |

---

## 성능

| 구간 | Before (while 루프) | After (그룹핑+집계) | 개선도 |
|------|--------------------|--------------------|-----|
| Merge 루프 | 2.360s | 0.231s | **10.2배** |
| 전체 실행 | 2.374s | 0.245s | **9.7배** |

> Before 방식은 `drop()` + `reset_index()`가 매 반복마다 전체 DataFrame을 복사 → O(n²). After는 `groupby().apply()` 단일 패스 → O(n).

---

## 관련

- [[260406_git_full_changelog]] — Phase 1 (02-06) Toyo cycle 병합 벡터화
- [[260312_improvement_priority_matrix]] — H9 `groupby().apply()` 추가 벡터화 후보
