# 사이클 서브탭 확장 Step 1b — `RndV_dchg_rest` 제거 정정

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
관련 계획: `.claude/plans/4-1-1-proud-ladybug.md`

## 배경

Step 1 (커밋 `3c819e7`) 에서 `RndV_chg_rest` / `RndV_dchg_rest` 두 컬럼을 생성했다. 사용자 정정:

> 2-6 (Discharge Rest End V) 은 신규가 아니다. 1-6 `RndV` 와 동일.

기존 `RndV` 컬럼은 `pivot_data["Ocv"][3]/1e6` — 즉 `Condition==3` 전체 Rest 의 **min** 이므로 실제 값이 자연스럽게 **방전 후 OCV (낮은 값)** 로 수렴한다. → 탭 2-6 에서 `RndV` 를 그대로 쓰면 "방전 직후 Rest 종료 전압" 역할이 이미 충족.

따라서 `RndV_dchg_rest` 는 **중복 파생** → 제거.

## 변경 내용

### 1. `_RNDV_SPLIT_COLS` 축소 (L908)
```diff
- _RNDV_SPLIT_COLS = ['RndV_chg_rest', 'RndV_dchg_rest']
+ _RNDV_SPLIT_COLS = ['RndV_chg_rest']
```

### 2. `_ensure_rndv_split_columns()` 본문 축소 (L911-)
- 함수명·시그니처 유지 (호출부 하위 호환)
- 파라미터 `dchg_cond` 제거 (사용 안 함)
- cycle_map 매핑 / 폴백 로직에서 `dchg_rest_tcs`, `_dchg_volt`, `_is_dchg_rest` 관련 코드 일괄 제거
- docstring 도 "충전 직후 Rest 종료 전압" 단일 역할로 재작성

### 3. PNE Sweep `_agg` dict (L9755)
```diff
  _agg: dict[str, str] = {
      ...
      'RndV_chg_rest': 'first',
-     'RndV_dchg_rest': 'first',
  }
```

### 4. PNE Sweep 필수 컬럼 보장 루프
```diff
- for _req in [..., 'RndV_chg_rest', 'RndV_dchg_rest']:
+ for _req in [..., 'RndV_chg_rest']:
      if _req not in _grouped.columns:
          _grouped[_req] = np.nan
```

### 5. Toyo 호출부 (L4186)
- `_ensure_rndv_split_columns(df.NewData, Cycleraw, cycle_map=None, ocv_scale=1.0)` 그대로 유지
- 함수가 `RndV_chg_rest` 만 처리하게 됐으므로 Toyo 에도 자동 반영
- `df.NewData['RndV_chg_rest'] = df.NewData['RndV']` 복사 로직은 유지 (기존 Toyo RndV 가 `chgdata.Ocv` = 충전 직후 OCV 이므로 의미상 정확)

## 동작 변화

| 항목 | Step 1 | Step 1b |
|---|---|---|
| `df.NewData.columns` 에 `RndV_chg_rest` | ✅ 존재 | ✅ 존재 (불변) |
| `df.NewData.columns` 에 `RndV_dchg_rest` | ✅ 존재 | ❌ **제거** |
| `df.NewData['RndV']` | Condition==3 min (방전 후 OCV) | 동일 (불변) |
| 탭 2-6 데이터 소스 (Step 3 예정) | `RndV_dchg_rest` 예정이었음 | **`RndV` 로 확정** |
| Excel "Rest End" 시트 | `RndV` 기반 (Step 4 에서 별도 `Rest End Dchg` 추가 예정이었음) | `RndV` 기반 유지, 방전용 시트 신규 추가 **불필요** |

## 영향 범위

- 탭1 그래프: 변경 없음 (회귀 0)
- 탭1 ax6 의 `RndV` (scatter empty) 그대로 사용
- 신규 로드되는 데이터에 `RndV_dchg_rest` 컬럼이 **존재하지 않음** — 이 컬럼을 참조하는 코드는 Step 1 도입 이후 현재 코드베이스에 없음 (Step 3 에서 처음 소비할 예정이었으나 설계 변경)
- Sweep 모드 데이터도 `RndV_dchg_rest` 가 _agg 에서 빠져 `_grouped` 컬럼에 자동 미포함

## 검증 포인트

- [ ] 신규 실행 후 `df.NewData.columns` 에 `RndV_chg_rest` 만 존재, `RndV_dchg_rest` 없음
- [ ] `df.NewData['RndV'].describe()` 가 **2.80–3.30V** 범위 (방전 후 Rest)
- [ ] `df.NewData['RndV_chg_rest'].describe()` 가 **4.05–4.25V** 범위 (만충 OCV)
- [ ] 탭1 2×3 그래프 시각적 완전 동일 (ax6 포함 회귀 없음)
- [ ] Sweep (GITT/DCIR) 데이터에서 `RndV_chg_rest` 가 `first` 값으로 존재
- [ ] Toyo 데이터에서 `RndV_chg_rest ≈ RndV` (기존 동작 유지)

## 다음 단계

- **Step 2**: 외부 탭 내부에 `QTabWidget` 중첩 도입, "요약" / "상세" 서브탭 (placeholder)
- **Step 3**: `graph_output_cycle_tab2()` + 탭1 ax6 AvgV 제거 + 탭2 6개 그래프 (2-6 은 `RndV` 사용)
- **Step 4**: Excel 에 `Rest End Chg` 시트만 추가 (방전용 시트 불필요 — 기존 `Rest End` 가 `RndV` 기반)
