# 사이클 바 상세정보 토글 기능 제거

## 날짜
2026-05-05

## 변경 내용
프로파일 탭의 사이클 타임라인 바 우측에 있던 펼침 토글(▶/▼) 버튼과
그 아래 인라인 상세 패널(블록 라벨 / RPT 마커 / 채널별 진행)을 전면 제거.

## 배경
- 토글 펼침 시 노출되던 정보(`[1-30]`, `[31]`, RPT (16회) 등)를 더 이상
  사용하지 않기로 판단.
- 토글 자체와 그에 딸린 패널·헬퍼들이 실사용에서 가치가 낮아
  UI 노이즈만 남김.

## 영향 범위
- 파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`

### 제거된 위젯
- `self._detail_toggle` (펼침/접기 QPushButton, 우상단 ▶/▼)
- `_btn_col` (토글을 감싸던 QVBoxLayout)
- `self._detail_panel`, `self._detail_panel_layout` (인라인 상세 QFrame)
- 레거시 별칭 `self._timeline_detail`, `self._detail_popup`

### 제거된 메서드
- `_on_detail_toggle_changed`
- `_show_detail_panel`
- `_hide_detail_panel`
- `_refresh_timeline_detail`
- `_get_best_channel_meta` (상세 패널 전용 헬퍼)
- `_get_rpt_cycles` (상세 패널 전용 헬퍼)
- `_get_channel_progress` (상세 패널 전용 헬퍼)

### 제거된 시그널 연결
- `self._detail_toggle.toggled.connect(self._on_detail_toggle_changed)`

### 변경된 호출 흐름
- `_on_timeline_selection_changed` 내 펼침 패널 갱신 코드 제거
  (`if self._detail_toggle.isChecked(): self._refresh_timeline_detail()`).

### 레이아웃 재정렬
- `_timeline_selection_label` 을 사후 `insertWidget(indexOf(_detail_panel), …)`
  방식이 아니라 타임라인 행 추가 직후 `addWidget` 으로 직접 부착.
- 변경 후 `verticalLayout_4` 순서:
  `_stepnum_container → _timeline_row → _timeline_selection_label →
   _data_scope_groupbox → _graph_opt_groupbox_pf → _profile_analysis_groupbox → stretch`.

## 검증
- `python -c "import ast; ast.parse(...)"` 구문 검사 통과.
- 외부 호출처 grep — 제거 대상 식별자 모두 0건.
