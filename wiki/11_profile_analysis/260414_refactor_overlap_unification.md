# 260414 — 프로필 옵션 체계 통일: continuity+loop → overlap

## 배경 / 목적

프로파일 분석의 사이클 간/내 시간 배치 옵션이 `continuity`(overlay/continuous) + `loop`(bool) 2개 파라미터로
분산되어 있어, 옵션 추가 시 if-else 중첩이 깊어지고 조합 관리가 어려웠다.

- 기존 문제 1: `_unified_calculate_axis`가 5단 if-elif 중첩
- 기존 문제 2: `loop` 플래그가 SOC 축에만 묶여있어 시간축 히스테리시스 불가
- 기존 문제 3: "순차 겹침" (사이클별 t=0, 충→방 연결) 모드 추가 불가

## 변경 내용

### 1. 파라미터 통일

| Before | After |
|--------|-------|
| `continuity="overlay"` | `overlap="split"` |
| `continuity="continuous"` | `overlap="continuous"` |
| `continuity="overlay"` + `loop=True` | `overlap="connected"` |
| (없었음) | `overlap="sequential"` **(신규)** |

### 2. `_unified_calculate_axis` → handler 디스패치 패턴

기존 5단 if-elif을 4개 독립 handler 함수로 분리:

| Handler | overlap 값 | 동작 |
|---------|-----------|------|
| `_axis_continuous` | `"continuous"` | 시작점 0 보정만 (이어서) |
| `_axis_split` | `"split"` | Condition별 독립 시간 리셋 + NaN 경계 |
| `_axis_sequential` | `"sequential"` | 사이클별 리셋, 충→방 순차 연결 |
| `_axis_connected` | `"connected"` | sequential과 동일 시간축 + 히스테리시스 SOC |

보조 함수:
- `_axis_sweep_blocks`: 스윕 데이터 전용 Block별 리셋
- `_insert_nan_between_groups`: 그룹 경계 NaN 삽입 공통 유틸
- `_calc_soc`: SOC 계산 로직 분리

### 3. 시그니처 변경

| 함수 | 변경 |
|------|------|
| `unified_profile_core()` | `continuity` + `loop` → `overlap` |
| `_unified_process_single_cycle_from_raw()` | 동일 |
| `unified_profile_batch()` | 동일 |
| `unified_profile_batch_continue()` | 내부 호출만 변경 |
| `_unified_calculate_axis()` | `continuity` + `loop` → `overlap` |

### 4. UI 변경

| Before | After |
|--------|-------|
| `[오버레이 \| 이어서]` + `□루프` 체크박스 | `[이어서 \| 분리 \| 순차 \| 연결]` 4단 세그먼티드 버튼 |

- Button ID: 0=continuous, 1=split, 2=sequential, 3=connected
- 기본 선택: split (id=1)
- `□루프` 체크박스 → 숨김 (하위 호환 위젯 유지)
- `profile_cont_group` → `profile_overlap_group` (하위 호환 별칭 유지)

### 5. 상호작용 규칙

| 조건 | 동작 |
|------|------|
| charge/discharge 선택 | sequential, connected 비활성 → split 강제 |
| SOC 축 선택 | continuous, sequential 비활성 → split 강제 |
| 이어서 선택 | 시간 축 강제 |

### 6. 강제 규칙 (코어 함수 내)

```python
if axis_mode == "soc" and overlap in ("continuous", "sequential"):
    overlap = "split"
if data_scope != "cycle" and overlap in ("sequential", "connected"):
    overlap = "split"
```

## 영향 범위

- `DataTool_optRCD_proto_.py` — 약 15개 위치 변경
- 변경 함수: `_unified_calculate_axis`, `unified_profile_core`,
  `_unified_process_single_cycle_from_raw`, `unified_profile_batch`,
  `unified_profile_batch_continue`, `_load_unified_batch_task`,
  `_read_profile_options`, `_map_options_to_legacy_mode`,
  `unified_profile_confirm_button`, `_profile_opt_*_changed`,
  `setupUi`, `retranslateUi`

## 호환성

- `_map_options_to_legacy_mode` 유지 — 기존 렌더링 분기(`step`/`chg`/`dchg`/`cycle_soc`/`continue`) 그대로 동작
- `profile_cont_group`, `profile_cont_overlay`, `profile_cont_continuous` 별칭 유지
- `profile_loop_chk` 숨김 위젯 유지
