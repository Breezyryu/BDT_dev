# 프로파일 옵션 단순화 + 프리셋 + 기본 PyQt6 스타일

**날짜**: 2026-04-19
**파일**: `DataTool_dev_code/DataTool_optRCD_proto_.py`

## 동기

전기화학 분석 관점에서 프로파일 옵션 재검토 결과:

- **`순차(sequential)`** 는 `이어서` + 특정 사이클 zoom 으로 동일 정보 획득 가능 → 정보 중복
- 시작점(default) 이 `분리` 로 되어 있었으나, full waveform 진단은 `이어서 + Rest + CV` 가 기본이어야 함
- 세그먼티드 버튼에 적용된 커스텀 QSS(파란색) 가 OS 네이티브 스타일과 이질적 → PyQt6 기본 스타일로 통일

## 변경 내용

### 1. overlap 세그먼트 4단 → 3단

| 제거 전 | 제거 후 |
|---------|---------|
| 이어서 / 분리 / **순차** / 연결 | 이어서 / 분리 / 연결 |

`profile_ovlp_sequential` 은 외부 참조 보호를 위해 `profile_ovlp_split` 로 alias 유지. 내부 파이프라인(`unified_profile_core`) 에는 `"sequential"` 처리 로직 잔존 — UI 에서 더 이상 해당 값을 emit 하지 않으므로 dead path 이지만 방어적으로 남겨둠.

### 2. 기본값 변경

- `checked_idx=1` (분리) → `checked_idx=0` (이어서)
- 이유: full waveform 진단이 시작점 철학에 부합

### 3. 축 제약 강화

overlap 선택에 따라 X축 버튼 enable/disable:

| overlap | SOC(DOD) | 시간 |
|---------|----------|------|
| 이어서 | ❌ disabled | ✅ 강제 |
| 분리 | ✅ | ✅ |
| 연결 | ✅ 강제 | ❌ disabled |

`_update_overlap_availability()` 에서 일원 처리. `_profile_opt_cont_changed()` 는 동일 함수로 위임.

### 4. 프리셋 드롭다운 신규

`data_scope` groupbox row 2 오른쪽에 `QComboBox` 추가. 5종 프리셋:

| 프리셋 | scope | overlap | axis | Rest | CV | dQdV |
|--------|-------|---------|------|------|----|----|
| 전체 진단 | cycle | continuous | time | ✓ | ✓ | |
| ICA / dV·dQ | cycle | split | soc | | ✓ | ✓ |
| 히스테리시스 | cycle | connected | soc | ✓ | ✓ | |
| 충전 분석 | charge | split | soc | | ✓ | |
| 방전 분석 | discharge | split | soc | | | |

선택 후 자동으로 `(선택)` 으로 복귀 → 재적용 허용.

### 5. PyQt6 기본 스타일 적용

`_make_seg_group()` 의 커스텀 QSS(파란 `#3C5488`, 경계 병합) 제거.
- `setStyleSheet()` 호출 삭제
- 고정 높이 26px 제거 → 기본 시스템 높이 사용
- 버튼 간격 `0` → `2px`
- 영향 범위: `profile_view_group`, `profile_scope_group`, `profile_overlap_group`, `profile_axis_group` 4개 세그먼트 모두 기본 스타일화

## 수정 위치

| 항목 | 라인 |
|------|------|
| `_make_seg_group()` QSS 제거 | ~10274 |
| overlap 세그먼트 3단 재구성 | ~11120 |
| 프리셋 콤보 추가 | ~11145 |
| 툴팁 업데이트 (3단) | ~16452 |
| 프리셋 레이블 텍스트 | ~16451 |
| 시그널 연결 | ~16904 |
| `_update_overlap_availability()` 재작성 | ~22839 |
| `_profile_opt_cont_changed()` 위임 | ~22890 |
| `_apply_profile_preset()` 신규 | ~22907 |
| `_read_profile_options()` overlap_map 3단 | ~23686 |

## 하위 호환

- `self.profile_ovlp_sequential` → `self.profile_ovlp_split` 로 alias
- `self.profile_cont_group`, `self.profile_cont_overlay`, `self.profile_cont_continuous` 기존 참조 유지
- `unified_profile_core(overlap="sequential", ...)` 호출되어도 정상 동작 (외부 스크립트 호환)

## 검증

- `python -c "import ast; ast.parse(...)"` 통과
- 조합 매트릭스:
  - 사이클·이어서·시간 (기본) ✓
  - 사이클·분리·SOC (ICA) ✓
  - 사이클·연결·SOC (히스테리시스) ✓
  - 충전·분리·SOC/시간 ✓
  - 방전·분리·SOC/시간 ✓
