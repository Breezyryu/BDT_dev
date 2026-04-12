# 사이클 파이프라인 로직 정비 + 사이클 바 UX 개선

> **작성일**: 2026-04-12
> **대상 파일**: `DataTool_dev/DataTool_optRCD_proto_.py`
> **변경 규모**: +2429줄, -367줄

---

## 배경/목적

사이클 데이터 파이프라인 전체 분석 후 7가지 로직 문제를 식별하고 체계적으로 정비.
사이클 바 UI/UX를 전면 개선하여 논리사이클 기준 통일 + 히스테리시스 분석 기능 추가.

---

## 변경 내용

### 1. cycle_map 이중 생성 해결
- `_get_toyo_cycle_map()` lru_cache 래퍼 신규 추가
- `_reset_all_caches()`에 lru_cache 초기화 포함
- `_build_channel_meta`에서 캐시 래퍼 경유로 변경

### 2. PNE/Toyo 분기 통합
- `is_pne_folder()` 캐시 우선 헬퍼 추가 (Phase 0 이후 I/O 제로)
- `get_cycle_map()` 통합 진입점 추가
- 12개 위치에서 if/else 분기 → 통합 함수로 대체

### 3. df.NewData DCIR 가변 컬럼 해결
- `_ensure_dcir_columns()`: 6개 DCIR 표준 컬럼 항상 생성
- `_DCIR_STANDARD_COLS` 상수 정의
- 하류 코드: hasattr/in → `dropna().empty` 패턴 통일

### 4. 갭 TC 추정 로직 개선
- `_totl_to_logical_str()`: reverse dict → bisect 기반 O(log n)
- 범위 입력("1-500"): 시작/끝만 매핑 후 논리사이클 범위 확장

### 5. sweep 모드 감지 보강
- .sch 확정 / 데이터 폴백 분기 명확화
- 폴백 실행 시 경고 로깅 + 경계값 근방 알림

### 6. 연결 모드 사이클 합산 투명화
- 툴팁에 합산 내역 표시 ("400 = 100 + 100 + 100 + 100")

### 7. 사이클 번호 체계 통일
- 사용자 레이어 = 논리사이클, 내부 = TC
- CycleNo single source of truth = 테이블 col4

### 8. CycleTimelineBar 전면 개선
- classified 기반 논리사이클 블록 (cycle_map TC→논리 역매핑)
- 블록 클릭 = 전체 선택, Shift/Ctrl 조합, 우클릭 메뉴
- TC/논리 토글, 눈금 표시, 반사이클 크기 축소 (0.3배)
- 행별 독립 선택 (_row_selections), 다중 경로 시 해당 행에 기록
- 최대 사이클 채널 기준 바 표시
- 상세 팝업 (블록 라벨 + RPT 마커 + 채널별 진행 게이지)
- stepnum 숨김 → 테이블 col4 통합
- 높이 고정 + 4행 초과 스크롤

### 9. 프로파일 실행 개선
- CycleNo 비어있으면 Phase 0 + 바 갱신만 하고 조용히 종료
- `_resolve_cyc_to_tc`: 1:1 / 다중TC 분기 처리
- `_load_step_batch_task`: 다중TC → unified_profile_core 사용

### 10. 히스테리시스 모드
- `_compute_tc_soc_offsets()`: TC별 절대 SOC 시작점 계산
- `_apply_hysteresis_soc_offsets()`: 프로파일 SOC 보정
- loop+SOC 계산: Condition별 독립 누적 → TC 내 연속 net 용량 누적
- Major(검정)/Minor(남색) 자동 분류 + 스타일링

---

## 영향 범위

- 사이클 분석 탭: cycle_map 빌드, 캐시, Phase 0
- 프로파일 분석 탭: 사이클 바, stepnum, 프로파일 로딩
- 경로 테이블: col4/col5 연동, TC 토글
- 그래프 출력: graph_output_cycle (X좌표), 히스테리시스 플롯
- CLAUDE.md, cycle-tab.md, memory 동기화
