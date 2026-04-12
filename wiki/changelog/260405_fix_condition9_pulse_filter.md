# 260405 — Condition=9 전류 방향 기반 재분류로 펄스/스텝 프로필 필터 수정

## 배경 / 목적

펄스 스윕(펄스+보충전, 방전), GITT, 스텝 충전 등의 데이터에서 `data_scope="charge"` 또는 `"discharge"`로 프로필을 출력할 때, 반대 방향의 CC 스텝 데이터가 섞여 들어가 프로필이 이상하게 출력되는 문제가 있었다.

**사이클(cycle) 모드에서는 정상 출력**되었는데, 충전/방전 단독 모드에서만 문제가 발생했다.

## 원인 분석

PNE 사이클러의 Condition 값 체계:
- `1` = CCCV 충전
- `2` = 방전
- `3` = 휴지
- **`9` = CC 전용 (충전/방전 구분 없음)**

기존 `_unified_filter_condition()` 로직:
```python
# 기존: Condition=9를 충전/방전 양쪽 필터에 모두 포함
charge   → [9, 1]   # ← CC 방전 펄스도 포함됨!
discharge → [9, 2]   # ← CC 충전 펄스도 포함됨!
```

펄스/GITT 패턴에서는 CC 충전 펄스와 CC 방전 펄스가 번갈아 나오는데, Condition=9만으로는 방향을 구분할 수 없어서 양쪽 데이터가 섞였다. 이후 `_unified_merge_steps()`가 이를 전부 같은 방향으로 취급하며 시간/용량을 누적하여 프로필이 깨졌다.

## Before / After 비교

### Before (기존)
```python
def _unified_filter_condition(df, data_scope, include_rest):
    if data_scope == "charge":
        cond_values = [9, 1]       # CC(9)가 충전/방전 구분 없이 포함
    elif data_scope == "discharge":
        cond_values = [9, 2]       # 동일 문제
    elif data_scope == "cycle":
        cond_values = [9, 1, 2]
    ...
    return df.loc[df["Condition"].isin(cond_values)].copy()
```

### After (수정)
```python
def _unified_filter_condition(df, data_scope, include_rest):
    df = df.copy()

    # --- Condition=9 재분류: 전류 부호 기반 ---
    if "Current_mA" in df.columns:
        cc_mask = df["Condition"] == 9
        if cc_mask.any():
            curr = df.loc[cc_mask, "Current_mA"]
            df.loc[cc_mask & (curr > 0).values, "Condition"] = 1   # CC 충전
            df.loc[cc_mask & (curr < 0).values, "Condition"] = 2   # CC 방전
            df.loc[cc_mask & (curr == 0).values, "Condition"] = 3  # 전류 0 → 휴지

    # --- 필터 적용 (이제 Condition=9가 없으므로 깔끔) ---
    if data_scope == "charge":
        cond_values = [1]       # 충전만
    elif data_scope == "discharge":
        cond_values = [2]       # 방전만
    elif data_scope == "cycle":
        cond_values = [1, 2]
    ...
```

## 수정 핵심 로직

`Current_mA` 부호(양수=충전, 음수=방전)를 기준으로 Condition=9를 사전 재분류:

| 조건 | 재분류 |
|------|--------|
| `Current_mA > 0` | Condition=1 (충전) |
| `Current_mA < 0` | Condition=2 (방전) |
| `Current_mA == 0` | Condition=3 (휴지) |

재분류 후에는 Condition=9가 더 이상 존재하지 않으므로, charge/discharge 필터가 정확하게 동작한다.

## 영향 범위

| 영향 | 범위 |
|------|------|
| 수정 함수 | `_unified_filter_condition()` (DataTool_optRCD_proto_.py) |
| 영향받는 데이터 | PNE 사이클러의 펄스, GITT, 스텝 충전, DCIR, 히스테리시스 데이터 |
| 영향받지 않는 것 | Toyo 데이터 (Condition=9 없음), cycle 모드 (전체 포함이므로 방향 구분 불필요) |
| 테스트 | 1834 passed, 0 failed, 118 skipped (전체 통과) |

## 부수 수정

- 파일 끝부분(`_pybamm_dchg_add_step` 함수)이 이전 세션에서 잘려있던 것을 HEAD 원본에서 복원 (302줄)
