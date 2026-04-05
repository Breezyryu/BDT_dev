# 260404 통합 프로필 Phase 4 버그 수정

## 배경 / 목적

Phase 4 UI 통합 후 실제 Windows 환경 테스트에서 발견된 버그들을 수정한다.

---

## 수정 1: `convert_steplist()` 쉼표+공백 입력 파싱 오류

### Before
```python
def convert_steplist(input_str):
    output_list = []
    for part in input_str.split():  # 공백만 구분자
        ...
```
- `"2,4,5, 1-10"` 입력 시 `"2,"` → `int("2,")` → `ValueError`

### After
```python
import re
parts = [p.strip() for p in re.split(r'[,\s]+', input_str.strip()) if p.strip()]
```
- 쉼표, 공백, 혼용 모두 정상 처리
- `"2,4,5, 1-10"` → `[2, 4, 5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]`

### 영향 범위
- `convert_steplist()` 함수 (전역)
- 사이클 번호 입력(`stepnum`) 사용하는 모든 분석 기능

---

## 수정 2: 충전/방전 모드에서 '이어서' 옵션 비활성화

### Before
- 충전/방전 선택 시에도 '이어서(continuous)' 옵션이 활성화됨
- 충전/방전 단독 데이터에는 이어서(연속) 모드가 의미 없음

### After
- `_profile_opt_scope_changed()` 핸들러 추가
- 충전(index=0) / 방전(index=1) → `profile_cont_combo.setEnabled(False)`, 오버레이 강제
- 사이클(index=2) → `profile_cont_combo.setEnabled(True)`
- `__init__`에서 초기 상태도 반영

### 영향 범위
- `profile_scope_combo.currentIndexChanged` 시그널 연결 추가
- `_profile_opt_scope_changed()` 메서드 추가

---

## 수정 3: 사이클+오버레이에서 충방전 시작점 정렬

### Before
```python
# 오버레이: 사이클별 시작점 0으로 리셋
for cyc in df["Cycle"].unique():
    mask = df["Cycle"] == cyc
    cyc_start = df.loc[mask, "Time_s"].min()
    df.loc[mask, "Time_s"] = df.loc[mask, "Time_s"] - cyc_start
```
- 사이클 모드에서 충전→방전이 연속이므로, 방전 시작점이 충전 시간만큼 offset
- 오버레이 시 방전 부분이 오른쪽으로 밀려서 겹치지 않음

### After
```python
if data_scope == "cycle":
    # Condition별(충전/방전 각각) 시작점 0으로 리셋
    for cyc in df["Cycle"].unique():
        mask_cyc = df["Cycle"] == cyc
        for cond in df.loc[mask_cyc, "Condition"].unique():
            if cond == 3:  # Rest 제외
                continue
            mask = mask_cyc & (df["Condition"] == cond)
            cond_start = df.loc[mask, "Time_s"].min()
            df.loc[mask, "Time_s"] = df.loc[mask, "Time_s"] - cond_start
```
- 충전과 방전이 각각 t=0에서 시작 → 오버레이 시 동일 시간축에서 비교 가능

### 영향 범위
- `_unified_calculate_axis()` 함수 (공통 함수이므로 core/batch 양쪽 적용)

---

## 수정 4: Vol 컬럼 누락 (이전 세션에서 수정)

### Before
- `output_cols`에 "Vol" 미포함 → `final_cols` 필터링에서 제거
- `_plot_and_save_step_data`의 `stepchg.Vol` 접근 시 `AttributeError`

### After
- `output_cols = base_cols + ["Vol", "Cycle", "Condition"]`
- `unified_profile_core()` 및 `_unified_process_single_cycle_from_raw()` 양쪽 수정

---

## 수정 5: 사이클+SOC 모드에서 시간 축으로 플롯되는 문제

### Before
- `_map_options_to_legacy_mode()`에서 `data_scope == "cycle"` + `axis_mode == "soc"` 조합이 없음
- Fall-through로 `"step"` 모드(시간 기반 플롯)가 선택됨
- SOC 선택해도 시간 축 그래프가 출력

### After
- `"cycle_soc"` 모드 추가: 충전(0→1) + 방전(1→0) 루프를 SOC 축에 표시
- 6개 서브플롯: SOC-V (×2, 확대용), dQdV-V, SOC-dVdQ, SOC-Crate, SOC-Temp
- dQdV 스케일은 충전(양수)+방전(음수) 양방향 범위로 설정

### 영향 범위
- `_map_options_to_legacy_mode()` — `"cycle_soc"` 반환 분기 추가
- `unified_profile_confirm_button()` — `"cycle_soc"` 플롯 콜백 + fallback 추가
- 호환 래퍼 data_attr 분기에 `"cycle_soc"` 추가
