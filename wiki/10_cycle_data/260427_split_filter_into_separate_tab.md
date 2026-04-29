# 260427 현황 ↔ 필터링 탭 분리 + 충방전기명 검색 지원

## 배경

기존 현황 탭은 한 테이블(`tb_channel`)을 그리드 모드/필터 모드로 번갈아
쓰고 있어 사용자가 검색을 시작하면 그리드가 사라지는 혼란이 있었다.
또한 검색어로 충방전기명(예: `PNE23`, `Toyo1`)을 직접 지정해 그
충방전기 채널만 보고 싶다는 요청이 있어 함께 지원.

## 변경 내용

### 1. 신규 "필터링" 탭 (`self.tab_filter`)
- `_setup_filter_tab()` 메서드 추가 — `_bdt_setup_signals` 끝에서 호출
- 현황 탭(`self.tab`) 바로 다음(index +1)에 **"필터링"** 이름으로 동적 삽입
- 탭 내부 위젯:
  - `self.FindText_filter` — 자체 검색 입력. placeholder 에 충방전기 검색
    가능 안내 추가 ("스페이스=OR, 쉼표=AND. 충방전기명 검색 가능 (예:
    PNE23, Toyo1, 4879mAh)")
  - `self.btn_filter_run` — 필터 실행 버튼 (클릭/Enter 모두 지원)
  - `self.tb_channel_filter` — 결과 전용 QTableWidget. 우클릭 펼침/닫힘
    메뉴 + cellClicked 섹션 토글 지원

### 2. 기존 현황 탭 호환성
- 현황 탭의 `btn_filter` 클릭 핸들러를 `_btn_filter_to_tab` 으로 변경
  - 검색어 동기화 (`FindText.text()` → `FindText_filter.setText`)
  - 필터링 탭으로 자동 전환 (`tabWidget.setCurrentWidget`)
  - `filter_all_channels` 실행
- `btn_highlight` + `FindText` 의 그리드 강조 기능은 그대로 유지

### 3. 충방전기명 검색 (cycler-aware filter)
**위치**: `filter_all_channels` 검색어 파싱 직후

```python
known_cyclers = set(toyo_info.keys()) | set(pne_info.keys())
cycler_tokens = set()
remaining = []
for tok in re.split(r'[\s,]+', raw_search):
    _cy = next((cy for cy in known_cyclers
                if cy.lower() == tok.lower()), None)
    if _cy:
        cycler_tokens.add(_cy)
    else:
        remaining.append(tok)
filtered_search = " ".join(remaining)
if cycler_tokens:
    all_cyclers = [c for c in all_cyclers if c in cycler_tokens]
```

지원 패턴:
- `PNE23` → PNE23 채널만 표시 (전부)
- `Toyo1 작업멈춤` → Toyo1 의 작업멈춤 채널만
- `PNE23,4879mAh` → PNE23 의 testname 에 4879mAh 포함된 채널 (AND)
- `PNE22 PNE23` → PNE22 + PNE23 의 모든 채널 (OR)
- `PNE99` (존재하지 않는 cycler) → testname 키워드로 폴백 매칭
- 빈 검색 → 기존 유휴 모드

### 4. 위젯 분리에 따른 헬퍼 업데이트
**자동 치환** (filter_all_channels 내부 30개): `self.tb_channel.` → `tb.`
( `tb = getattr(self, 'tb_channel_filter', None) or self.tb_channel` )

**수동 수정**:
- `_sort_filter_column`: 정렬 대상 위젯 `tb_channel_filter` 우선
- `_filter_toggle_section`: tb_channel_filter 사용 (5개 치환)
- `_filter_context_menu` / `_filter_expand_all` / `_filter_collapse_all`:
  로컬 alias `tb` 도입
- 그리드 전용 `table_reset()` 호출 제거 → 필터 탭 전용 inline 초기화

### 5. 기존 cellClicked / contextMenu 바인딩 정리
`__init__` 에서 `tb_channel.cellClicked` / `customContextMenuRequested` 를
필터 헬퍼에 묶었던 코드 제거. 같은 시그널을 `_setup_filter_tab` 에서
**`tb_channel_filter` 위에 다시 바인딩**.

`tb_channel` (그리드) 의 ExtendedSelection·Ctrl+C·Ctrl+A 단축키는 유지.
`tb_channel_filter` 도 동일 단축키 추가.

## 동작 매트릭스

| 시나리오 | 동작 |
|---|---|
| 현황 탭에서 콤보박스로 충방전기 선택 | 그리드(`tb_channel`) 정상 렌더 |
| 현황 탭에서 검색어 + btn_highlight | 그리드 강조 표시 (변경 없음) |
| 현황 탭에서 검색어 + btn_filter | 검색어가 필터링 탭으로 동기화 + 자동 전환 + 실행 |
| 필터링 탭에서 검색어 + btn_filter_run | `tb_channel_filter` 에 결과 |
| 필터링 탭에서 Enter | 동일 (returnPressed 시그널) |
| 필터링 탭 검색어 = "PNE23" | PNE23 모든 채널 |
| 필터링 탭 검색어 = "Toyo1 4879mAh" | Toyo1 채널 중 testname 매칭 |
| 빈 검색어 + 필터 실행 | 유휴 모드 (기존 동작) |
| 헤더 행 클릭 / 우클릭 | `tb_channel_filter` 에서 펼침/닫힘 |

## 영향 범위

### 신규
- `_setup_filter_tab` (메서드 추가)
- `_btn_filter_to_tab` (메서드 추가)
- `self.tab_filter`, `self.FindText_filter`, `self.btn_filter_run`, `self.tb_channel_filter` (위젯 추가)

### 수정
- `_bdt_setup_signals` — `_setup_filter_tab()` 호출 추가
- `__init__` — 기존 cellClicked / contextMenu 바인딩 제거 (tb_channel_filter 로 이동)
- `filter_all_channels` — 검색어 파싱 (cycler 토큰 분리) + tb alias + cycler-only 모드
- `_sort_filter_column`, `_filter_toggle_section`, `_filter_context_menu`,
  `_filter_expand_all`, `_filter_collapse_all` — `tb_channel_filter` 사용

### 변경 없음
- 현황 탭 그리드 렌더링 (`pne_table_make`, `toyo_table_make`)
- `match_filter_text`, `match_highlight_text`
- 멈춤/완료/셀유무 색상 로직 (v4/v5)
- ETA 미사용 정책 (v8)

## 회귀 체크 포인트 (사내 환경)

1. 현황 탭 그리드 — 기존처럼 콤보 선택 시 정상 렌더
2. 현황 탭 btn_filter 클릭 → 필터링 탭으로 자동 전환 + 결과 표시
3. 필터링 탭에서 자체 입력 + Enter / 버튼 클릭 — 결과 표시
4. 검색어에 "PNE23" 만 입력 → PNE23 모든 채널만 표시
5. "Toyo1 작업멈춤" → Toyo1 의 작업멈춤 채널만
6. 헤더 행 클릭으로 섹션 접기/펼치기 — 필터링 탭에서 정상 작동
7. 우클릭 메뉴 (전체 펼침/닫힘) — 필터링 탭에서 정상 작동
8. 정렬 (헤더 클릭) — 필터링 탭 행 그룹 내에서 정렬
9. Ctrl+C / Ctrl+A — 두 탭 모두 동작

## 파일 변경 요약

| 파일 | 변경 |
|---|---|
| `DataTool_dev_code/DataTool_optRCD_proto_.py` | +95 / -52 (탭 신설, 검색 파싱, alias 도입, 헬퍼 정리) |
| `wiki/10_cycle_data/260427_split_filter_into_separate_tab.md` | 신규 (본 문서) |
