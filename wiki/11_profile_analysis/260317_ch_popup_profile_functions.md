# CH 팝업 기능 확대 적용 (프로파일 함수)

## 변경일: 2026-03-17

## 변경 대상
`DataTool_dev/DataTool_optRCD_proto_.py`

## 변경 내용

### 1. 그래프 함수 Line2D 반환 추가
- `graph_step()` — `line, = ax.plot(...)` → `return line`
- `graph_continue()` — 두 분기(line/marker) 모두 `line, = ax.plot(...)` → `return line`

### 2. `_plot_and_save_step_data()` artists 반환
- 6개 `graph_step()` 호출 결과를 `_artists` 리스트로 수집
- 반환값: `write_column_num` → `(write_column_num, _artists)` 로 변경

### 3. `step_confirm_button()` — CH 팝업 적용
- CycProfile / AllProfile / else 3개 분기 모두:
  - `_plot_and_save_step_data()` 반환값 언패킹 수정 (`write_column_num, _artists = ...`)
  - `channel_map` 구축 → `_finalize_plot_tab()`에 전달
  - AllProfile: `all_profile_channel_map` 사용

### 4. `rate_confirm_button()` — CH 팝업 적용
- CycProfile / AllProfile / else 3개 분기 모두:
  - 6개 `graph_step()` 반환값을 `_artists` 리스트로 수집
  - `channel_map` 구축 → `_finalize_plot_tab()`에 전달
  - AllProfile: `all_profile_channel_map` 사용

### 5. `pro_continue_confirm_button()` — CH 팝업 적용
- AllProfile / non-AllProfile 2개 경로:
  - 모든 `graph_continue()` 반환값을 `_artists` 리스트로 수집 (OCV/CCV 조건부 포함)
  - `_target_map` 패턴으로 AllProfile/non-AllProfile 자동 선택
  - `_finalize_plot_tab()`에 channel_map 전달

### 6. `ect_confirm_button()` — CH 팝업 적용
- `graph_continue()` 6개 호출 반환값을 `_artists`로 수집
- 직접 `tab_layout.addWidget()` → `_finalize_plot_tab()` 사용으로 변경
- `channel_map` 구축 후 전달

## 영향 범위
- 기존 `chg_confirm_button()`, `dchg_confirm_button()`은 이전 세션에서 완료됨
- 이번 변경으로 사이클데이터 탭의 모든 프로파일 기능에 CH 팝업 지원 완료
