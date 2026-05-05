# 사이클 + 분리 + 시간 조합 비활성화

날짜: 2026-05-05
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`

## 배경

프로파일 분석 탭의 데이터 범위 옵션 조합 중 **사이클 + 분리(split) + 시간** 조합이 결과값이 이상하게 출력되는 현상이 있어, 우선 UI 차원에서 해당 조합을 차단한다.

기존 overlap × axis 제약 표:

| scope | overlap | SOC | DOD | 시간 |
|---|---|---|---|---|
| 사이클 | 이어서(continuous) | ✗ | ✗ | ✓ |
| 사이클 | 분리(split) | ✓ | ✓ | **✓ → ✗** |
| 사이클 | 연결(connected) | ✓ | ✓ | ✗ |
| 충전 | 분리(split) | ✓ | ✓ | ✓ |
| 방전 | 분리(split) | ✓ | ✓ | ✓ |

> 주: 충전/방전 단방향에서의 분리 + 시간 조합은 유효하므로 유지. 사이클 모드에서만 차단.

## 변경 내용

### `_update_overlap_availability()` (L26528~)

분리(split) 분기에서 `is_cycle` 분기를 추가:

```python
else:  # 분리: SOC/DOD 허용. 사이클 모드에서는 시간 비활성 (결과값 이상)
    self.profile_axis_soc.setEnabled(True)
    self.profile_axis_dod.setEnabled(True)
    # 사이클 + 분리 + 시간 조합 비활성화 (2026-05-05)
    # 충전/방전 단방향에서는 분리 + 시간 유효 → 활성 유지
    self.profile_axis_time.setEnabled(not is_cycle)
    if is_cycle and self.profile_axis_group.checkedId() == 2:
        self.profile_axis_soc.setChecked(True)
```

핵심:
- 사이클 + 분리 모드에서 `profile_axis_time` 버튼 disable
- 현재 axis가 시간(id=2)이면 SOC(id=0)로 강제 전환
- 충전/방전 + 분리 모드에서는 시간 활성 유지

### Docstring 업데이트

유효 조합 표를 갱신:

```text
- 사이클 × {이어서(시간), 분리(SOC/DOD), 연결(SOC/DOD)}
- 충전/방전 × {분리(SOC/DOD/시간)} 만
```

## 부수 영향

- **프리셋**: `1: 전체 진단(cycle, continuous, time)` / `2: ICA(cycle, split, soc)` / `3: 히스테리시스(cycle, connected, soc)` / `4: 충전(charge, split, soc)` / `5: 방전(discharge, split, soc)` — 사이클+분리+시간 조합을 사용하는 프리셋이 없으므로 영향 없음.
- **상태 전환 시 자동 보정**:
  - 사이클 + 이어서 + 시간 → 분리로 전환: SOC 강제 선택
  - 충전 + 분리 + 시간 → 사이클로 전환: SOC 강제 선택
- **`_apply_cyc_continue_rest_default()`**: 사이클 + 이어서 + 시간 조합 (Rest 기본 ON) 은 유효 조합 그대로 유지 → 영향 없음.

## 후속 작업 (TODO)

- 사이클 + 분리 + 시간 조합의 결과값 이상 원인 분석 (시계열 좌표계 vs SOC 좌표계 mismatch 추정)
- 원인 해결 후 비활성 해제 또는 별도 처리 로직 추가 검토
