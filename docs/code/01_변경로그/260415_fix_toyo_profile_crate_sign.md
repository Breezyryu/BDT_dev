# Toyo Profile plot C-rate 부호 분리

## 배경 / 목적

Toyo 사이클러 CSV의 `Current[mA]` 컬럼은 **크기(절대값)**만 기록하고 방향은 `Condition` 컬럼(1=충전, 2=방전)으로 구분한다. 이 때문에 Toyo profile plot에서 충전과 방전 Crate가 **둘 다 양수**로 표시되어 충/방전 방향이 시각적으로 구분되지 않는 문제가 있었다.

PNE는 `Current_raw`가 signed(μA 부호값)이므로 이미 충전=+, 방전=−로 표시되고 있었다. 두 사이클러의 표시 규약을 통일한다.

## Before / After

### 1. 통합 정규화 경로 (`_unified_normalize_toyo`, 약 line 1397~)

**Before**
```python
# 전류: 이미 mA 단위
result["Current_mA"] = df["Current_raw"].values
result["Crate"] = df["Current_raw"].values / mincapacity
```

**After**
```python
# 전류: 이미 mA 단위 — Toyo는 크기값만 기록하므로 Condition 기반 부호 부여 (충전=+, 방전=-)
toyo_sign = np.where(df["Condition"].values == 2, -1.0, 1.0)
signed_curr_mA = df["Current_raw"].values * toyo_sign
result["Current_mA"] = signed_curr_mA
result["Crate"] = signed_curr_mA / mincapacity
```

### 2. 레거시 fallback (`toyo_dchg_Profile_data`, 약 line 7299)

**Before**
```python
df.Profile["Current[mA]"] = df.Profile["Current[mA]"]/mincapacity
```

**After**
```python
# 방전 Crate는 음수 표시 (충전=+, 방전=-)
df.Profile["Current[mA]"] = -df.Profile["Current[mA]"]/mincapacity
```

### 수정하지 않은 함수 (이미 올바름)

| 함수 | 상태 | 사유 |
|------|------|------|
| `toyo_chg_Profile_data` | 변경 없음 | Condition==1만 필터 → 충전 양수 유지 |
| `toyo_step_Profile_data` | 변경 없음 | Condition==1만 필터 → 다단 CC 충전 양수 유지 |
| `toyo_rate_Profile_data` | 변경 없음 | Condition==1만 필터 → 율별 충전 양수 유지 |
| `toyo_Profile_continue_data` | 변경 없음 | `signed_current` 사용(line 7344)으로 이미 부호 반전 적용 |

## Impact 범위

- **영향 받는 탭**: 사이클데이터 탭 → Profile 분석 (`ProfileConfirm` 버튼) — Toyo 경로
- **영향 받는 기능**: 프로필 그래프의 Crate(전류) 표시, `TimeSec` 모드일 때의 `Curr` 컬럼 엑셀 저장값
- **영향 받는 데이터**: Toyo 방전 구간의 `Crate`, `Current_mA` 값이 양수 → 음수로 변경
- **PNE 경로**: 변경 없음 (기존에도 signed)

### 안전성 검증

1. **Cutoff 필터**: `data_scope == "charge"`일 때만 `Crate >= cutoff` 필터 적용(line 2250, 2406). 방전은 전압 cutoff 사용 → 음수 Crate 영향 없음.
2. **용량 적분**: `_unified_normalize_toyo`의 ChgCap/DchgCap 계산은 `np.abs(next_curr_mA)` 사용(line 1431~1432) → 부호 반전 영향 없음.
3. **dQdV 계산**: `_unified_calculate_dqdv`는 SOC 기반 미분이므로 Crate 부호 무관.
4. **Condition 재분류**: `_unified_filter_condition`의 CC 부호 기반 재분류는 PNE의 Condition=9 전용(Toyo는 9 없음).
5. **`abs(Crate)` 사용처**: 코드 전체 검색 결과 없음.

## 검증 체크리스트

- [ ] Toyo 데이터에서 사이클 프로파일(cycle scope) 실행 → 충전 구간 Crate > 0, 방전 구간 Crate < 0 확인
- [ ] Toyo 방전 전용 프로파일(discharge scope) 실행 → Crate가 전구간 음수 확인
- [ ] Toyo 충전 전용 프로파일(charge scope) 실행 → Crate가 전구간 양수 유지 확인
- [ ] 이어서(continuous) 모드에서 `Curr`, `Crate` 컬럼의 부호가 구간별로 전환되는지 엑셀 저장값 확인
- [ ] PNE 프로파일은 동일하게 동작 (regression 없음)
