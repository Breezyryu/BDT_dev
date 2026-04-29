# 260427 필터링 탭을 현황 탭 내부 sub-tab 으로 이동

## 배경

직전 변경(260427_split_filter_into_separate_tab.md) 에서 필터링 탭을
**top-level** (사이클데이터·패턴수정 등과 같은 레벨) 로 추가했으나,
사용자 의도는 **현황 탭 내부의 sub-tab** 분리였다. 의도에 맞게 재구성.

## 구조 변경

### Before (직전 v9)
```
tabWidget
├── 현황      (self.tab)
├── 필터링    (self.tab_filter)   ← top-level
├── 사이클데이터
├── 패턴수정
└── …
```

### After (이번 v10)
```
tabWidget
├── 현황                (self.tab_status_container)
│   └── status_subtabs (QTabWidget)
│       ├── 채널 리스트  (self.tab — 기존 그리드)
│       └── 필터링       (self.tab_filter)
├── 사이클데이터
├── 패턴수정
└── …
```

## 변경 내용

### `_setup_filter_tab` 수정 (필터링 탭 삽입 부분)
**Before**
```python
idx_status = self.tabWidget.indexOf(self.tab)
self.tabWidget.insertTab(idx_status + 1, self.tab_filter, "필터링")
```

**After**
```python
idx_status = self.tabWidget.indexOf(self.tab)
text_status = self.tabWidget.tabText(idx_status) if idx_status >= 0 else "현황"
# self.tab 을 tabWidget 에서 분리 (위젯은 유지됨)
if self.tabWidget.indexOf(self.tab) >= 0:
    self.tabWidget.removeTab(self.tabWidget.indexOf(self.tab))
# sub-tab QTabWidget 생성 + self.tab / self.tab_filter 추가
self.status_subtabs = QtWidgets.QTabWidget()
self.status_subtabs.addTab(self.tab, "채널 리스트")
self.status_subtabs.addTab(self.tab_filter, "필터링")
# 컨테이너 widget 으로 감싸 원래 위치에 재삽입
self.tab_status_container = QtWidgets.QWidget()
_lo = QtWidgets.QVBoxLayout(self.tab_status_container)
_lo.setContentsMargins(0, 0, 0, 0)
_lo.addWidget(self.status_subtabs)
self.tabWidget.insertTab(
    idx_status, self.tab_status_container, text_status)
```

### `_btn_filter_to_tab` 수정 (현황 탭 btn_filter 핸들러)
**Before** — top-level tab 으로 전환
```python
self.tabWidget.setCurrentWidget(self.tab_filter)
```

**After** — 현황 컨테이너 + sub-tab 둘 다 전환
```python
self.tabWidget.setCurrentWidget(self.tab_status_container)
self.status_subtabs.setCurrentWidget(self.tab_filter)
```

## 동작

| 시나리오 | 동작 |
|---|---|
| 앱 시작 | 현황 → 채널 리스트 sub-tab 활성 (기존 그리드 표시) |
| 채널 리스트에서 콤보박스로 충방전기 선택 | 그리드(`tb_channel`) 정상 렌더 |
| 채널 리스트에서 검색어 + btn_highlight | 그리드 강조 (변경 없음) |
| 채널 리스트에서 btn_filter 클릭 | 검색어 → 필터링 sub-tab 동기화 + sub-tab 전환 + 실행 |
| 필터링 sub-tab 직접 진입 | 자체 검색바·실행 버튼 사용 |
| 필터링 sub-tab Enter | filter_all_channels 실행 |
| top-level 다른 탭 (사이클데이터 등) | 영향 없음 |

## 영향 범위

### 신규 위젯
- `self.status_subtabs` — sub-tab QTabWidget
- `self.tab_status_container` — 컨테이너 (현황 탭이 가리키는 새 root)

### 변경 없음
- `self.tab` — 여전히 채널 리스트 그리드의 컨테이너 (이름·내용 동일)
- `self.tab_filter` — 필터링 sub-tab 내용물 (FindText_filter, btn_filter_run, tb_channel_filter)
- 모든 filter 헬퍼 (`filter_all_channels`, `_sort_filter_column`,
  `_filter_toggle_section`, `_filter_context_menu`, `_filter_expand_all`,
  `_filter_collapse_all`)
- 충방전기명 검색 로직 (cycler 토큰 분리)

### `retranslateUi` 호환성
`setupUi` 내부의 `self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), "현황")`
호출은 `_setup_filter_tab` 후에는 `indexOf(self.tab) = -1` 이 되어 silent
no-op. 컨테이너의 탭 텍스트 "현황" 은 `_setup_filter_tab` 이 직접 설정하므로
영향 없음.

## 회귀 체크 포인트

1. 앱 시작 시 현황 → 채널 리스트 sub-tab 이 기본 활성
2. 채널 리스트에서 콤보 선택 → 그리드 정상 렌더
3. 필터링 sub-tab 진입 + 검색 → 결과 표시
4. 검색어 "PNE23" 등 cycler 명 검색 동작
5. 헤더 클릭 정렬 / 우클릭 펼침-닫힘
6. top-level 탭 갯수 = 이전(v9 도입 전) 과 동일
7. 다른 top-level 탭 (사이클데이터, 패턴수정 등) 영향 없음

## 파일 변경 요약

| 파일 | 변경 |
|---|---|
| `DataTool_dev_code/DataTool_optRCD_proto_.py` | _setup_filter_tab 끝부분 + _btn_filter_to_tab (~25 LoC 변경) |
| `wiki/10_cycle_data/260427_filter_subtab_inside_status.md` | 신규 (본 문서) |
