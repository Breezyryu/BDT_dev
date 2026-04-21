# 260404 — Phase 4: 프로필 분석 UI 통합 (5버튼 → 1버튼 + 4옵션)

## 배경 / 목적

기존 사이클 데이터 탭의 프로필 옵션에는 5개 분석 버튼이 있었다:
- 충전 Step 확인 (StepConfirm)
- 충전 분석 (ChgConfirm)
- 율별 충전 확인 (RateConfirm)
- 방전 분석 (DchgConfirm)
- HPPC/GITT/ECT (ContinueConfirm)

이를 **1개 통합 버튼 + 4개 옵션 위젯**으로 교체하여 사용자가 직관적으로 분석 모드를 조합할 수 있게 한다. DCIR 버튼은 별도로 유지.

## Before / After

### Before (6개 버튼, 3행)
```
[ 충전 Step 확인 ]  [ 충전 분석 ]
[ 율별 충전 확인 ]  [ 방전 분석 ]
[ HPPC/GITT/ECT  ]  [   DCIR   ]
```

### After (4개 옵션 + 2개 버튼)
```
데이터: [충전 ▼]   연속성: [오버레이 ▼]
X축:   [SOC  ▼]   ☐ 휴지 포함
[ ▶ 프로필 분석 ]  [   DCIR   ]
```

## 변경 내용

### 1. UI 위젯 (setupUi, 라인 ~6569)

| 위젯 | objectName | 타입 | 항목 |
|------|-----------|------|------|
| 데이터 범위 | `profile_scope_combo` | QComboBox | 충전, 방전, 사이클 |
| 연속성 | `profile_cont_combo` | QComboBox | 오버레이, 이어서 |
| X축 모드 | `profile_axis_combo` | QComboBox | SOC, 시간 |
| 휴지 포함 | `profile_rest_chk` | QCheckBox | — |
| 통합 실행 | `ProfileConfirm` | QPushButton | ▶ 프로필 분석 |

### 2. 옵션 의존성 시그널 (라인 ~12117)

- `profile_axis_combo.currentIndexChanged` → `_profile_opt_axis_changed()`
  - SOC 선택 시 → 연속성을 "오버레이"로 강제
- `profile_cont_combo.currentIndexChanged` → `_profile_opt_cont_changed()`
  - "이어서" 선택 시 → X축을 "시간"으로 강제

### 3. 통합 핸들러 (라인 ~17178)

| 함수 | 역할 |
|------|------|
| `_profile_opt_axis_changed()` | SOC↔시간 의존성 처리 |
| `_profile_opt_cont_changed()` | 오버레이↔이어서 의존성 처리 |
| `_read_profile_options()` | 위젯 → options dict 변환 |
| `_map_options_to_legacy_mode()` | options → 기존 모드명(step/chg/dchg/continue) 매핑 |
| `unified_profile_confirm_button()` | 메인 핸들러: 통합 로딩 → 호환 래퍼 → 렌더링 |

### 4. 기존 버튼 처리

- 5개 버튼(StepConfirm, ChgConfirm, RateConfirm, DchgConfirm, ContinueConfirm)은 **숨김**(`.setVisible(False)`)
- 시그널 연결은 유지 (하위 호환용, Phase 5에서 제거 예정)
- DCIRConfirm은 변경 없음

## 옵션 → 기존 모드 매핑

| data_scope | axis_mode | continuity | include_rest | 기존 모드 | 기존 버튼 |
|-----------|-----------|-----------|-------------|----------|----------|
| 충전 | SOC | 오버레이 | — | chg | 충전 분석 |
| 방전 | SOC | 오버레이 | — | dchg | 방전 분석 |
| 충전 | 시간 | 오버레이 | — | step | 충전 Step 확인 |
| 방전 | 시간 | 오버레이 | — | step | (신규 조합) |
| 사이클 | 시간 | 오버레이 | ✓ | step | (신규 조합) |
| 사이클 | 시간 | 이어서 | ✓ | continue | HPPC/GITT/ECT |
| 충전 | 시간 | 이어서 | — | continue | (신규 조합) |
| ... | ... | ... | ... | (14가지 유효 조합) | ... |

## 영향 범위

- **변경된 파일**: `DataTool_dev/DataTool_optRCD_proto_.py`
- **UI 변경**: tab_6(프로필 옵션) 하단 버튼 영역 → 옵션 + 통합 버튼
- **기존 기능**: 기존 5개 핸들러 + 렌더링 파이프라인은 변경 없음 (숨김 버튼 통해 접근 가능)
- **데이터 로딩**: Phase 3의 `_load_all_unified_parallel()` 사용

## 다음 단계

- ~~Phase 4: UI 통합~~ ✅ 완료
- Phase 5: 기존 5개 confirm 핸들러 + 10개 배치 함수 deprecated → 제거
