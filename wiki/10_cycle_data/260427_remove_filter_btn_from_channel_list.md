# 260427 채널 리스트 sub-tab 의 필터링 버튼 제거

## 배경

직전 v10 에서 필터링을 현황 탭 sub-tab 으로 이동했음에도, 채널 리스트
sub-tab 에는 여전히 `btn_filter`(필터링(Shift+Enter)) 버튼이 남아 검색
입력 + 필터 트리거가 두 sub-tab 에 분산되어 있었다.

→ **필터링 동작은 '필터링' sub-tab 에서만** 수행하도록 정리.

## 변경 내용

### 1. `__init__` — btn_filter 시그널 연결 제거
**Before**
```python
# Enter → 강조, Shift+Enter → 필터링
self.FindText.installEventFilter(self)
self.btn_highlight.clicked.connect(self.tb_cycler_combobox)
self.btn_filter.clicked.connect(self._btn_filter_to_tab)
```

**After**
```python
# 채널 리스트 sub-tab: Enter 만 강조 동작 (Shift+Enter 필터링 트리거 제거)
self.FindText.installEventFilter(self)
self.btn_highlight.clicked.connect(self.tb_cycler_combobox)
# btn_filter 는 _setup_filter_tab 에서 숨김 처리
```

### 2. `_setup_filter_tab` — btn_filter 숨김 추가
sub-tab 구성 직후 `self.btn_filter.hide()` 호출.

### 3. `eventFilter` — Shift+Enter 필터링 트리거 제거
**Before**
```python
if event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
    self.filter_all_channels()
else:
    self.tb_cycler_combobox()
```

**After**
```python
self.tb_cycler_combobox()  # Shift 무관 모든 Enter 가 강조 트리거
```

### 4. `_btn_filter_to_tab` — 호출처 없음 (남겨둠)
함수 정의 자체는 dead code 가 되지만 호환성·향후 단축키 재도입을 위해
유지. 실제 어디서도 호출되지 않음.

## 동작 변화

| 입력 | Before | After |
|---|---|---|
| 채널 리스트 Enter | 강조 | 강조 (변경 없음) |
| 채널 리스트 Shift+Enter | 필터 실행 + sub-tab 전환 | **무시** (강조 동작도 안 함) |
| 채널 리스트 btn_filter 클릭 | 필터 실행 + sub-tab 전환 | **버튼 안 보임** |
| 필터링 sub-tab 진입 + Enter | 필터 실행 (변경 없음) | 동일 |
| 필터링 sub-tab btn_filter_run 클릭 | 필터 실행 (변경 없음) | 동일 |

## 영향 범위

### 사라진 트리거
- 채널 리스트 `btn_filter` 버튼 (UI 에서 숨김)
- 채널 리스트 FindText Shift+Enter 필터링

### 유지
- 채널 리스트 `btn_highlight` (강조 Enter)
- 채널 리스트 FindText Enter (강조 → tb_cycler_combobox)
- 필터링 sub-tab 자체 검색·실행 흐름 (FindText_filter, btn_filter_run)
- 충방전기명 검색 (cycler 토큰 분리)
- 모든 filter 헬퍼

## 회귀 체크 포인트

1. 채널 리스트 sub-tab 진입 → 필터링 버튼 안 보임
2. 채널 리스트 FindText 에 텍스트 입력 후 Enter → 그리드 강조 정상
3. 채널 리스트 FindText 에 Shift+Enter → 아무 일 없음
4. 필터링 sub-tab 진입 → 자체 검색바·실행 버튼 정상
5. 필터링 sub-tab Enter / btn_filter_run 클릭 → filter_all_channels 실행
6. cycler 명 검색 (PNE23, Toyo1) 정상

## 파일 변경 요약

| 파일 | 변경 |
|---|---|
| `DataTool_dev_code/DataTool_optRCD_proto_.py` | -10 / +12 (시그널 제거, hide 호출, eventFilter 단순화) |
| `wiki/10_cycle_data/260427_remove_filter_btn_from_channel_list.md` | 신규 (본 문서) |
