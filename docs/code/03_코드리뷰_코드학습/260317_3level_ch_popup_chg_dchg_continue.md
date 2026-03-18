# 3-level CH 팝업 확장: chg / dchg / pro_continue

**날짜**: 2026-03-17  
**파일**: `DataTool_dev/DataTool_optRCD_proto_.py`

## 변경 개요

기존 flat 1-level `channel_map`만 사용하던 프로파일 함수 3개에 3-level 채널 계층(channel_map → sub_channel_map → sub2_channel_map)을 적용했다.

- ECT(`ect_confirm_button`)는 사용자 요청에 따라 **제외**.

## 3-level 구조

| 레벨 | 맵 변수 | 키 생성 방식 | 용도 |
|------|---------|-------------|------|
| 1 (그룹) | `channel_map` / `all_profile_channel_map` | `_make_channel_labels()` → `ch_label` | 테스트 조건 그룹 |
| 2 (서브) | `sub_channel_map` / `all_profile_sub_map` | `_make_channel_labels()` → `sub_label`, parent=ch_label | 개별 채널 |
| 3 (사이클) | `sub2_channel_map` / `all_profile_sub2_map` | `"%04d" % CycNo`, parent=sub_label | 사이클 번호 |

## 모드별 맵 사용

| 모드 | 사용 맵 | 이유 |
|------|---------|------|
| CycProfile (채널별 탭) | channel_map + sub2_channel_map | 탭 당 1채널, 사이클만 분리 |
| else (사이클별 탭) | channel_map + sub_channel_map | 탭 당 1사이클, 채널만 분리 |
| AllProfile (통합 탭) | 3개 모두 | 모든 조합을 1탭에 표시 |

## 변경 함수 목록

### 1. `chg_confirm_button` (Charge Profile)
- AllProfile 초기화: `all_profile_sub_map`, `all_profile_sub2_map` 추가
- CycProfile: `sub2_channel_map` 초기화 + `_make_channel_labels()` + `_finalize_plot_tab(sub2_channel_map=...)`
- AllProfile: 3-level 맵 빌드 (sub_key, sub2_key) + `_finalize_plot_tab(sub_channel_map=..., sub2_channel_map=...)`
- else: `sub_channel_map` 초기화 + `_make_channel_labels()` + `_finalize_plot_tab(sub_channel_map=...)`

### 2. `dchg_confirm_button` (Discharge Profile)
- chg와 동일한 패턴 적용 (변수명: `Dchgnamelist`, `last_Dchgnamelist`, `Dchgtemp`)

### 3. `pro_continue_confirm_button` (Continue Profile)
- AllProfile 초기화: `all_profile_sub_map`, `all_profile_sub2_map` 추가
- 맵 빌드: `_make_channel_labels()` + AllProfile일 때만 sub/sub2 맵 추가
- AllProfile finalize: `sub_channel_map`, `sub2_channel_map` 파라미터 추가

## 이전 완료 사항 (참고)
- `_create_cycle_channel_control()`: `sub2_channel_map` 파라미터 추가
- `_build_channel_dialog()`: Section 3 패널 (sub2 리스트) + 3-level 연동 핸들러
- `_finalize_plot_tab()`: `sub_channel_map`, `sub2_channel_map` 파라미터 추가
- `step_confirm_button()`: 3-level 완료
- `rate_confirm_button()`: 3-level 완료
