# 260407 ECT 사이클 매핑 수정 및 Del 키 동작 개선

## 배경 / 목적

BAK 260204 버전에서는 ECT path의 사이클 값을 **TotlCycle(파일 번호)로 직접** 사용했기 때문에
모든 TC가 정상 처리되었다. 현재 버전에서 논리사이클 매핑(`pne_build_cycle_map`)이 도입되면서
특정 TC가 매핑에서 누락되는 문제와, 테이블 UI에서 사이클(Raw) 열의 편집 제한 문제가 발생했다.

---

## 변경 1: `pne_build_cycle_map()` — 전체 TC 포함

### 문제

`valid_totl_cycles`를 구성할 때 **충방전 쌍이 있는 TC + 충전 전용 TC**만 포함하고,
**방전 전용 TC**와 **REST only TC**를 제외했다.

- TC=33 (DCHG only): ECT 파라미터 시험의 독립 방전 사이클 → 누락
- TC=37, 40 (REST only): 휴지 사이클 → 누락

```
수정 전 매핑: 논리 1-37 → TC "1-32, 34-36, 38-39" (TC 33, 37, 40, 41 누락)
수정 후 매핑: 논리 1-40 → TC "1-41"                 (전체 TC 포함)
```

### 변경 내용 (L3777~3784)

```python
# 수정 전: 충방전 쌍 + 충전전용만 포함
valid_dchg_tcs = set(_dchg_valid.intersection(_chg_valid))
chg_only_tcs = _all_chg - _all_dchg
valid_totl_cycles = sorted(valid_dchg_tcs | chg_only_tcs)

# 수정 후: 전체 TC 포함 (BAK 호환: TotlCycle 직접 사용과 동일)
valid_totl_cycles = sorted(all_tcs)
```

### 영향 범위

- `pne_build_cycle_map()` → 논리사이클 매핑 테이블
- 경로 테이블의 사이클/사이클(Raw) 자동 매핑 결과
- `_resolve_logical_to_tc_range()` 변환 결과
- ECT confirm, 프로필 분석, 사이클 분석 등 논리사이클 기반 전체 기능

### 검증 데이터

대상: `260326_260329_00_류성택_4860mAh_A17 ATL ECT parameter9\M01Ch025[025]`

| TC | Condition | 수정 전 | 수정 후 |
|----|-----------|--------|--------|
| 33 | DCHG only | ❌ 누락 | ✅ 논리 33 |
| 37 | REST only | ❌ 누락 | ✅ 논리 37 |
| 40 | REST only | ❌ 누락 | ✅ 논리 39에 병합 |
| 41 | DCHG only | ❌ 누락 | ✅ 논리 40 |

---

## 변경 2: `_on_cycle_cell_changed()` — col 4 Del 시 col 5 편집 가능 전환

### 문제

col 4(사이클)에 논리사이클을 입력하면 col 5(사이클Raw)에 TotlCycle이 자동 매핑되면서
**읽기전용으로 잠금**되었다. 사용자가 col 4를 Del로 지우면 **col 5의 값까지 max 힌트로
덮어써져서** 자동 매핑된 TotlCycle 값이 소실되었다.

### 변경 내용 (L19534~19590)

col 4(사이클)을 Del로 지울 때의 동작 분기:

| 상태 | col 4 (사이클) | col 5 (사이클Raw) |
|------|---------------|------------------|
| col 5에 사용자/자동매핑 값 있음 | 회색 역산 논리사이클 힌트 | **기존 값 유지 + 편집 가능으로 전환** |
| col 5도 비어있음 | 회색 max 힌트 | 회색 max 힌트 |

### 사용자 워크플로우

```
1. col 4에 "1-5" 입력 → col 5에 "1-5" 자동 매핑 (읽기전용)
2. col 4 선택 → Del 키
3. col 5: "1-5" 유지 + 편집 가능
   col 4: "1-5" (회색 역산 힌트)
4. col 5에서 직접 TotlCycle 수정 가능 (예: "1-3"으로 변경)
```

### 영향 범위

- `_on_cycle_cell_changed()` — cellChanged 핸들러
- 사이클 테이블 col 4/col 5 편집 동작
- ECT 모드에서 TotlCycle 직접 입력 워크플로우

---

## 파일 변경 목록

| 파일 | 변경 위치 | 내용 |
|------|----------|------|
| `DataTool_optRCD_proto_.py` | L3777~3784 | `valid_totl_cycles = sorted(all_tcs)` — 전체 TC 포함 |
| `DataTool_optRCD_proto_.py` | L3801 | 단방향 TC 스윕 병합 조건: `chg_only_tcs` → `not in (_all_chg & _all_dchg)` |
| `DataTool_optRCD_proto_.py` | L19534~19590 | col 4 Del 시 col 5 값 유지 + 편집 가능 전환 로직 |
