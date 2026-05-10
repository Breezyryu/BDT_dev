# 사이클 바 인라인 라벨 + 카테고리 칩 + 정렬 동기화 (260510 류성택 요청)

## 날짜

2026-05-10 · UX 개선안 1번·6번 적용

## 한 줄 요약

큰 블록 위에 카테고리 약어를 직접 그리고, 위젯 위쪽에 카테고리 칩 범례를 두어
필터링 가능하게 하고, 다중 채널 비교 시 글로벌 `max_lc` 기준 정렬을 토글로 전환할 수 있게 했다.

## 배경

- UX 개선안 [`docs/proposals/260510_cycle_timeline_bar_ux.html`](../../docs/proposals/260510_cycle_timeline_bar_ux.html)
  6개 항목 중 **1번 (라벨+칩)** 과 **6번 (정렬 동기화)** 을 우선 채택.
- 1번: 색상만으로는 카테고리 학습 비용이 크고, 호버 툴팁에만 의존하면 분포 인지가 늦다.
- 6번: 행마다 자체 `max_lc` 100% 폭으로 그리면 채널 길이가 달라도 끝점이 같아 보여
  비교 시 착시. 글로벌 정렬 옵션을 켜면 종료 시점 차이가 즉시 보인다.

## 변경 파일

- `DataTool_dev_code/DataTool_optRCD_proto_.py` — 위젯 1개 확장 + 신규 위젯 1개 + UI 결선

## 신규 / 변경 요소

### 1. 약어 사전 (신규)

- `_CYCLE_LABEL_ABBR` (`:10812~`) — 37개 키
  - 신 9종 + 서브태그: `사이클(ACCEL)`→`ACCEL`, `방전(초기)`→`방·초`, `GITT(simplified)`→`GITT·S` 등
  - 패턴 카테고리 A~G (StepType 폴백) 포함
  - 구 alias (`Rss`, `가속수명`, `initial`, `반사이클`, `unknown`) 포함

### 2. `CycleTimelineBar` 확장

#### 멤버 추가

- `_show_labels: bool = True` — 인라인 라벨 표시
- `_filter_cats: set[str] | None = None` — 필터 카테고리 (None=전체)
- `_sync_max: bool = False` — 글로벌 max 정렬 동기화
- `_LABEL_MIN_PX = 36` — 블록 폭이 이 이상일 때만 라벨 그림

#### 시그널 추가

- `labelsToggled(bool)` · `syncMaxToggled(bool)` — 외부 컨트롤 동기화용

#### 메서드 추가

- `set_show_labels(show)` — 라벨 토글 + 시그널 emit
- `set_filter(cats)` — 카테고리 dim (cats=None은 전체 풀컬러)
- `set_sync_max(sync)` — 정렬 동기화 토글
- `category_set()` — 현재 행들에 등장한 카테고리 키 (출현 순서, `_pad` 제외)
- `_global_max()` — 모든 행 중 최대 `total_cycles`
- `_row_layout_data(ri)` — `(blocks_aug, data_total, layout_total)`. sync_max 시 끝에 `_pad` 가상 블록 추가
- `_active_aug()` — 활성 행 augmented 데이터 (mouse·hit-test 보조)

#### 시그너처 변경

- `set_multi_blocks(rows, sync_max=None)` — `sync_max` 추가 (None=현재값 유지, 기본 호환)

#### `paintEvent` 개정

- 행 루프에서 `_row_layout_data(ri)` 사용 → sync_max에서 행이 짧으면 끝에 빗금 패딩 자동 그려짐
- `_pad` 패턴 블록은 회색 + 사선 빗금 + "미실시" 라벨
- `_filter_cats not None` 이고 카테고리가 set 밖이면 alpha 200→60으로 dim
- `bw >= _LABEL_MIN_PX and _show_labels` 시 약어를 흰색 라벨로 중앙 정렬 표시
- 선택 영역 좌표는 augmented blocks/layout_total 기준 (sync 전·후 일치)
- 눈금: sync_max 시 `_global_max()` 까지 그림

#### `_cycle_to_x` / `_x_to_cycle` / `_block_at` 보정

- 인자 미지정 시 sync_max면 `_active_aug()` 사용 (눈금 그리기와 일치)
- `_pad` 영역 클릭 시 `self._total_cycles` 로 클램프 (실데이터 끝)
- `_block_at` 은 `_pad` 블록 무시

#### `keyPressEvent` 신규

- `L` (Ctrl·Alt 미동반) → 라벨 토글

#### 우클릭 메뉴 확장

- "인라인 라벨 표시 (L)" — 체크박스
- "정렬 동기화 (글로벌 max_lc)" — 다중 행 ≥ 2 일 때만, 체크박스
- "카테고리 필터 해제" — 필터 활성화 시에만

### 3. `CycleLegendChips` (신규 위젯)

- `QPushButton` 기반 칩 (둥근 테두리 · 카테고리 색상 · 약어 동시 표시)
- **클릭** = solo 강조 (그 카테고리만 풀컬러), 두 번째 클릭으로 해제
- **Alt + 클릭** = 다중 dim 토글 (해당 카테고리만 dim, 누적)
- `set_categories(cats)` — 카테고리 변경 시 필터 리셋
- `filterChanged(set | None)` 시그널 → `cycle_timeline.set_filter` 직결
- `reset()` — 필터 초기화

### 4. UI 결선

- `_timeline_groupbox` 안에 신규 행 `_timeline_legend_row` 삽입 (사이클 바 위)
  - `cycle_legend_chips` (좌, stretch)
  - `cycle_sync_max_btn` (우, ToolButton, checkable, 다중 행에서만 visible)
- `_apply_timeline_blocks` 끝에 칩 카테고리 갱신 + 동기화 버튼 가시성 갱신 추가
- 시그널 연결
  - `cycle_legend_chips.filterChanged` → `cycle_timeline.set_filter`
  - `cycle_sync_max_btn.toggled` → `_on_cycle_sync_max_toggled` (+ 라벨 갱신)
  - `cycle_timeline.syncMaxToggled` → `_on_cycle_sync_max_state` (우클릭 메뉴 등 외부 변경 시 버튼 동기화)

## 호환성 / 회귀 안전

- 기본값 `sync_max=False` · `_show_labels=True` · `_filter_cats=None`
  - 라벨이 새로 그려지지만 블록 색상·좌표·선택 텍스트·시그널 모두 그대로
- 기존 `set_blocks(blocks)` · `set_multi_blocks(rows)` 호출은 무수정으로 동작 (`sync_max=None` 기본)
- 단일 행일 때 동기화 버튼은 숨김 (의미 없음)
- 우클릭 메뉴 기존 항목 (블록 선택 / 같은 패턴 / 전체 / 선택 해제) 그대로 유지
- AST · `import` smoke OK
- 다중 채널 augmented 좌표 단위 검증 (CH-A 300cy + CH-B 120cy)
  - OFF: row0 layout_total=300, row1=120 (각자 100%)
  - ON: row0=300 (3블록), row1=300 (3블록 + `_pad` 1블록, pad_end=300)

## 단축키

- `L` — 인라인 라벨 표시 토글 (위젯 포커스 상태에서)

## 후속 (개선안 잔여)

- 2번 미니맵 + 줌 / 3번 진단 마커 / 4번 용량 오버레이 / 5번 통계 카드 — 후속 회차

## 회귀 검증

- 위젯 페인팅·UI 한정 변경, 사이클 데이터 파이프라인은 무수정 → snapshot 영향 없음 예상
- 수정 후 `pytest DataTool_dev_code/test_code/test_regression_4cases.py -v` 권장
- snapshot fail 시 본 변경 외 원인 의심 (rule 변경 없음)
