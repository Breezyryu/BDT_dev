# 260414 — 현황 탭 필터링 기능 개선

## 배경 / 목적

현황 탭의 필터링 기능에 PNE 충방전기 상태 세분류, 동작 타입 표시, 접기/펼치기 등
다수의 기능을 추가하여 채널 모니터링 효율을 높인다.

## 변경 내용

### 1. 작업멈춤 세분류 (PNE 전용, 필터링 버튼에서만 동작)

**기존**: 모든 "작업멈춤" 채널에 대해 .log 파일을 전수 파싱
**변경**: PNE JSON의 `Code`, `Code_Desc` 필드를 우선 활용, 검색 매칭된 건만 처리

| 조건 | 상태 출력 | 배경색 |
|------|----------|--------|
| Code=153, Code_Desc="작업멈춤종료" + .log Reserve 있음 | 중단점 도달 (C{rc}/S{rs}) | 노란색 (240,220,160) |
| Code=153 + .log 즉시 멈춤만 | 사용자멈춤 | 노란색 |
| Code≠153 | 작업멈춤 - {Code_Desc 텍스트} | 빨간색 (214,155,154) |

- `_refine_paused_status()`: Code/Code_Desc 기반 분기 로직으로 변경
- `_classify_paused_reason()`: Code:153 전용 .log 파싱 (Reserve vs 즉시 멈춤)
- `_build_channel_path()`: Result_Path에서 채널폴더를 추출하여 올바른 경로 구성
- .log 파싱 시 `re.findall` + `[-1]`로 가장 최근 Reserve 값 사용

### 2. 작업중 채널 Reserve 예약 정보 (필터링 전용)

PNE 작업중 채널의 .log에서 Reserve Cycle/Step 추출 → 상태에 표시

- 예: `작업중 (→C98/S206)`, `충전 (→C98/S206)`
- Reserve 없으면 기존대로 `작업중`만 표시
- `_parse_reserve_info()` 헬퍼 신규 추가

### 3. 동작(Type) 열 추가

필터링 테이블 열 구조 8열 → 9열:
`충방전기 | 채널 | 상태 | Step/Cycle | 전압 | **동작** | 온도 | 테스트명 | 셀 경로`

- PNE JSON `Type` 필드 값 표시 (Charge, DisCharge, Rest 등)
- 작업중/충전/방전/진행/휴지 상태일 때만 표시
- `Type == "휴지"` → `"Rest"`로 변환

### 4. PNE 업데이트 시간 변경

**기존**: 파일시스템 `os.path.getmtime()` (파일 수정 시간)
**변경**: JSON 첫 번째 채널의 `Sync_Time_Day` + `Sync_Time` 값

- `_pne_sync_time(js)` 헬퍼: JSON → `"YY-MM-DD HH:MM"` 형식
- `pne_table_make`, `pne_data_make`, `filter_all_channels` 3곳 적용

### 5. 키 바인딩 변경

| 키 | 동작 |
|-----|------|
| Enter | 강조 (현재 충방전기 내 하이라이트) |
| Shift+Enter | 필터링 (전체 스크리닝 + 작업멈춤 세분류) |

- `FindText.returnPressed` 시그널 → `eventFilter`로 교체 (Shift 감지)
- 버튼 텍스트: `"강조(Enter)"` (100px), `"필터링(Shift+Enter)"` (140px)

### 6. 접기/펼치기 기능

- 층/충방전기 헤더 클릭 → 하위 행 접기/펼치기 (`▾`↔`▸`)
- 우클릭 메뉴: 전체 펼침 / 전체 닫힘
- `_filter_sections` dict로 섹션 행 범위 관리
- 층 접기 시 하위 충방전기 접힘 상태 보존

### 7. 기타

- `tb_channel` 더블클릭 편집 비활성 (`NoEditTriggers`)
- `except Exception: continue` → 에러 로깅 추가 (`logger.warning`)
- 필터 완료 시 작업멈춤 사유별 집계 로그 추가

## 영향 범위

| 함수 | 변경 |
|------|------|
| `pne_data_make()` | Code, Code_Desc, Type 컬럼 추가; 작업멈춤 세분류 제거 (필터 전용) |
| `pne_table_make()` | 동일 컬럼 추가; 작업멈춤 세분류 제거; Sync_Time 기반 시간 표시 |
| `filter_all_channels()` | 9열 테이블; 매칭 후 세분류; Reserve 정보; 접기/펼치기 섹션 등록 |
| `_refine_paused_status()` | Code/Code_Desc 기반 분기 (pne_table_make에서만 호출 가능) |
| `_classify_paused_reason()` | Code:153 전용 간소화; findall[-1] 최신값 |
| `_parse_reserve_info()` | 신규: 작업중 .log Reserve 추출 |
| `_pne_sync_time()` | 신규: JSON Sync_Time 파싱 |
| `_build_channel_path()` | 신규: Result_Path 채널폴더 경로 구성 |
| `_filter_toggle_section()` | 신규: 헤더 클릭 접기/펼치기 |
| `_filter_context_menu()` | 신규: 우클릭 전체 펼침/닫힘 |
| `eventFilter()` | 신규: Enter/Shift+Enter 분기 |
