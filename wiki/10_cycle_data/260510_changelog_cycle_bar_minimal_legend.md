---
title: "사이클 패턴 바 — ACCEL 라벨 / 정렬 동기화 / 칩 범례 정리"
date: 2026-05-10
tags: [ui, cycle-bar, simplify, legend]
related:
  - "[[260510_changelog_cycle_data_column_width_fit]]"
  - "[[260427_changelog_data_subtab]]"
requested_by: "류성택"
---

# 사이클 패턴 바 — ACCEL 라벨 / 정렬 동기화 / 칩 범례 정리

> 사이클 패턴 GroupBox (분석 탭 2번 박스) 의 시각 노이즈 최소화 — ACCEL 인라인
> 라벨 / 정렬 동기화 토글 / 다중 카테고리 칩 모두 제거하고 RPT 칩만 남김.

## Context

기존 (260510 W19 기준):
- 사이클 바 블록 위에 ACCEL/RPT/DCIR/방·초 등 약어 라벨 인라인 표시
- 우상단 "정렬 동기화 OFF" 토글 — 다중 채널 행을 글로벌 max_lc 기준 정렬
- 좌측 칩 범례 — 방전(초기) · RPT · 사이클(ACCEL) · 충전(세팅) · DCIR 등 등장
  카테고리 전부 표시

요청 (260510 류성택):

> * ACCEL 텍스트 제거
> * 정렬 동기화 OFF 기능, 버튼 제거
> * RPT 버튼만 남기고 나머지 삭제

배경:
- 사이클 바의 대부분 블록이 ACCEL → 라벨이 빽빽하게 반복되어 가독성 ↓
- 정렬 동기화 토글은 운용 중 거의 사용되지 않음 (사용자 피드백)
- 칩 범례는 RPT 위치 식별용으로만 가치 — 색상으로 충분히 구별되는 카테고리는
  칩 없어도 무방

## Why

- **ACCEL 라벨 제거** → 색상만으로 ACCEL 식별 가능, 라벨 겹침으로 인한
  시각 과부하 해소
- **정렬 동기화 제거** → 행 비교는 사용자가 자체 max 기준으로 보는 게 직관적
  (현재 OFF 가 default)
- **RPT 칩만 유지** → RPT 는 색상이 작고 바 길이도 짧아 위치 빠른 식별이
  중요. 칩 클릭 = solo 강조 (다른 카테고리 dim) 흐름 보존.

## 변경

### Path
[DataTool_optRCD_proto_.py](DataTool_dev_code/DataTool_optRCD_proto_.py)

### A. 인라인 라벨 — ACCEL 카테고리 skip (`paintEvent`, L11505~)

```python
# Before
if self._show_labels and bw >= self._LABEL_MIN_PX:
    abbr = _CYCLE_LABEL_ABBR.get(_p)
    if not abbr:
        abbr = (_p[:6] if _p else '?')
    painter.setFont(_lbl_font)
    painter.setPen(QPen(QColor(255, 255, 255, alpha_label), 1.0))
    painter.drawText(..., abbr)

# After
if self._show_labels and bw >= self._LABEL_MIN_PX:
    abbr = _CYCLE_LABEL_ABBR.get(_p)
    if not abbr:
        abbr = (_p[:6] if _p else '?')
    if _p in ('사이클(ACCEL)', '가속수명', 'ACCEL'):
        abbr = ''
    if abbr:
        painter.setFont(_lbl_font)
        painter.setPen(QPen(QColor(255, 255, 255, alpha_label), 1.0))
        painter.drawText(..., abbr)
```

`_CYCLE_LABEL_ABBR` 사전 자체는 보존 — 우클릭 메뉴/툴팁 등에서 abbr 가
필요할 수 있어 데이터 단에서는 그대로.

### B. 정렬 동기화 토글 버튼 제거

**B1. 위젯 생성 제거** (L14172~):
```python
# Before — 24줄 (chips + button + 토글 스타일)
# After  — 8줄 (chips only)
self._timeline_legend_row = QtWidgets.QHBoxLayout()
self._timeline_legend_row.setContentsMargins(0, 0, 0, 0)
self._timeline_legend_row.setSpacing(6)
self.cycle_legend_chips = CycleLegendChips(parent=self._timeline_groupbox)
self.cycle_legend_chips.setObjectName("cycle_legend_chips")
self._timeline_legend_row.addWidget(self.cycle_legend_chips, 1)
_tl_layout.addLayout(self._timeline_legend_row)
```

**B2. 시그널 연결 제거** (L20195~):
```python
# Removed:
self.cycle_sync_max_btn.toggled.connect(self._on_cycle_sync_max_toggled)
self.cycle_timeline.syncMaxToggled.connect(self._on_cycle_sync_max_state)
```

**B3. 핸들러 메서드 제거** (L29187~):
- `_on_cycle_sync_max_toggled(self, checked)` — 14줄
- `_on_cycle_sync_max_state(self, checked)` — 14줄

**B4. 우클릭 메뉴 sync 항목 제거** (`_show_context_menu`, L11719~):
```python
# Removed:
if len(self._rows) >= 2:
    act_sync = menu.addAction("정렬 동기화 (글로벌 max_lc)")
    act_sync.setCheckable(True)
    act_sync.setChecked(self._sync_max)
    act_sync.triggered.connect(lambda chk: self.set_sync_max(chk))
```

**보존 (의도)**: `CycleTimelineBar._sync_max` 필드, `set_sync_max` 메서드,
`_row_layout_data` 의 sync_max 분기, `_pad` 블록 렌더링 코드. 모두 `_sync_max`
가 영구 False 인 상태에서 dead branch 로 남음 — 기능 복원이 필요해질 경우
UI 만 다시 붙이면 즉시 복원 가능.

### C. 칩 범례 — RPT 만 표시 (L29159~)

```python
# Before
self.cycle_legend_chips.set_categories(
    self.cycle_timeline.category_set())
multi = len(rows) >= 2
self.cycle_sync_max_btn.setVisible(multi)
if not multi and self.cycle_sync_max_btn.isChecked():
    self.cycle_sync_max_btn.setChecked(False)

# After
_cats = self.cycle_timeline.category_set()
self.cycle_legend_chips.set_categories(
    [c for c in _cats if c == 'RPT'])
```

`CycleLegendChips.set_categories` 는 빈 리스트 시 자동 hide
(`setVisible(bool(self._cats))` — L11794) → RPT 가 없는 데이터에서는 칩 영역
자체가 숨김.

## 영향

- ✅ 사이클 바 시각 밀도 ↑ — ACCEL 약어 반복으로 인한 라벨 충돌 해소
- ✅ 우상단 영역 단순화 — 토글 버튼 제거로 GroupBox 헤더 너비 여유 확보
- ✅ RPT 칩 클릭 시 solo 강조 (다른 카테고리 dim) 흐름 보존
- ✅ Ctrl+L (인라인 라벨 토글) 단축키 보존 — ACCEL 외 카테고리 (RPT, DCIR,
  방·초 등) 의 라벨은 폭 충분 시 정상 표시
- 다중 채널 (행 ≥2) 의 정렬 동기화 모드 = 영구 OFF (행마다 자체 max 기준 100% 폭)
- 회귀 위험 낮음 — 제거된 모든 ID (`cycle_sync_max_btn`,
  `_on_cycle_sync_max_*`) 가 grep 으로 0건 확인됨

## Test

- [x] `python -c "import ast; ast.parse(...)"` 구문 OK
- [x] grep — `cycle_sync_max_btn`, `_on_cycle_sync_max_toggled`,
      `_on_cycle_sync_max_state` 모두 0건
- [ ] 실측 (PNE/Toyo 다중 행 로드): 사이클 바에 ACCEL 텍스트 미노출
- [ ] 실측: 우상단 토글 버튼 미노출, GroupBox 정상 렌더링
- [ ] 실측: 칩 범례에 RPT 만 표시, 다른 카테고리 칩 미노출
- [ ] 실측: RPT 칩 클릭 → 사이클 바 RPT 블록만 풀컬러, 나머지 dim

## Out of Scope

- `_sync_max` 코어 로직 (CycleTimelineBar) 은 dead branch 로 남김 — UI 복원이
  필요해지면 즉시 재활성 가능
- 카테고리 색상 자체는 변경 없음 — 사이클 바에서 ACCEL/RPT/DCIR 등은 색으로 구별
- ACCEL 외 카테고리 (FORM/STEP/GITT 등) 의 인라인 라벨은 그대로 — 빈도가 낮아
  노이즈 아님
