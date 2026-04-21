# 프로파일 범례/색상 3모드 통합

> **작성일**: 2026-04-12
> **대상 파일**: `DataTool_dev_code/DataTool_optRCD_proto_.py`

---

## 배경/목적

프로파일 분석의 3가지 모드(사이클 통합, 셀별 통합, 전체 통합)에서 범례 텍스트, 색상 모드, 범례 표시 전략이 각각 다른 시스템으로 동작하고 있었음:
- `_setup_legend`: 기존 시스템 (LEGEND_THRESHOLD 기준 컬러바 전환)
- `_apply_legend_strategy` + `_get_profile_color`: 신규 시스템 (사이클 통합 전용)

이를 **하나의 통합 시스템**으로 일원화.

---

## 변경 내용

### 1. `_resolve_profile_color_mode` 확장

**Before**: `n_cycles`, `is_hysteresis`, `is_link` 3개 파라미터
**After**: `n_channels`, `n_folders`, `view_mode` 파라미터 추가

| view_mode | 구분 대상 | 색상 결정 기준 |
|-----------|----------|---------------|
| `cyc` | 사이클 | 사이클 >10 → gradation, ≤10 → distinct |
| `cell` | 채널 | 채널 >10 → gradation, ≤10 → distinct |
| `all` | 경로×사이클 | 다경로 → group, 단경로 → gradation/distinct |

### 2. `_make_short_legend` 확장

**Before**: 사이클 통합 전용 ("Cy2", "CH044 Cy2")
**After**: `view_mode`, `channel_idx` 파라미터 추가

| view_mode | 범례 형식 | 예시 |
|-----------|----------|------|
| `cyc` | "Cy{N}" / "CH{name} Cy{N}" | "Cy2", "CH044 Cy2" |
| `cell` | "{idx}. CH{name}" | "01. CH044", "02. CH045" |
| `all` | "CH{name} Cy{N}" | "CH044 Cy2", "LWN CH044 Cy2" |

### 3. `_apply_legend_strategy` 통합 강화

**Before**: `n_cycles` 기준 범례 on/off + coolwarm 컬러바만
**After**: `view_mode`, `n_channels`, `legend_positions` 파라미터 추가

| 라인 수 | 전략 |
|---------|------|
| ≤5 | 모든 axes 범례 (8pt), `legend_positions` 반영 |
| 6~15 | 첫 axes만 범례 (7pt) |
| >15 | 범례 숨김 + 모드별 컬러바 (Cycle / Channel / Cell×Cycle / Path) |

### 4. `_setup_legend` 호출 전면 교체

- `_profile_render_loop` 내부 3곳: `_setup_legend` 제거 → 공통 마무리의 `_apply_legend_strategy`로 통합
- `ect_confirm_button`: `_setup_legend` → `_apply_legend_strategy`
- `pro_continue_confirm_button`: 2곳 `_setup_legend` → `_apply_legend_strategy`
- `_setup_legend` 메서드 정의는 보존 (호출처 없음, 향후 정리 대상)

### 5. `_profile_render_loop` 파라미터 추가

- `view_mode: str = 'cyc'`
- `n_channels_total: int = 1`
- `n_folders_total: int = 1`

### 6. `unified_profile_confirm_button` 호출부 업데이트

- view_mode 자동 결정 (라디오버튼 상태)
- 채널 총 수 사전 계산 (Pattern 폴더 제외)
- 확장된 파라미터로 `_resolve_profile_color_mode` + `_profile_render_loop` 호출

---

## 영향 범위

- **프로파일 분석 탭**: 3모드(사이클/셀별/전체 통합) 범례·색상 동작 변경
- **ECT/Continue 경로**: 범례 시스템 교체 (`_setup_legend` → `_apply_legend_strategy`)
- **함수 시그니처**: `_resolve_profile_color_mode`, `_make_short_legend`, `_apply_legend_strategy`, `_profile_render_loop` 모두 파라미터 추가 (기본값 설정으로 하위 호환)
