# 현황 탭 상태 분류 v3 Phase A 구현

## 배경 / 목적

`docs/code/02_변경검토/260415_filter_status_classification_redesign_v3_final.md`
재설계안의 Phase A 를 `DataTool_optRCD_proto_.py` 에 적용한다.

현행 로직의 3 가지 문제를 해결:
1. JSON `Code_Desc` 에 접두사 `"작업멈춤 - "` 를 덧붙여 표시 (규칙 위반)
2. Code 별 의미 구분(조건도달/챔버이슈 등) 없이 동일한 빨강 배경
3. 완료/시험완료 채널에 경과 시간 미표시

## 변경 내용

### 1) 상태 분류 상수 신규 추가 ([L25692~](../../DataTool_dev_code/DataTool_optRCD_proto_.py:25692))

- `SAFETY_CODES` — 안전조건 Code 집합 `{128, 129, 134, 142, 208, 209}`
- `USER_OR_ERROR_LABELS` — 노랑 처리 라벨 집합 `{사용자멈춤, 작업멈춤}`
- `HW_WARNING_LABELS` — 빨강 처리 라벨 집합 `{챔버이슈}`
- `COMPLETED_LABELS` — 연녹(셀있음) 처리 집합 `{완료, 시험완료}`
- `SAFETY_CODE_DESCS` — 안전조건 Code_Desc 원본 텍스트 집합

### 2) `FILTER_STATUS_KEYWORDS` 확장

검색 키워드 신규 추가:
- `"안전조건"` → `SAFETY_CODE_DESCS` 매칭 (전압 상한/하한, OCV상한, 용량상한, 전압/전류 이상(경고))
- `"사용자멈춤계"` → `{사용자멈춤, 챔버이슈, 시험완료, 작업멈춤}` + "중단점 도달" prefix

### 3) `match_filter_text` 확장

- `frozenset` 타입 value 지원
- `"중단점 도달"` prefix 매칭 특수 처리
- 일반 키워드 검색 시 `status_base` 도 검사 대상으로 포함

### 4) 신규 헬퍼 `_elapsed_from_log()` ([L25992~](../../DataTool_dev_code/DataTool_optRCD_proto_.py:25992))

완료/시험완료 채널의 `.log` 파일 mtime 기반 경과 시간 계산.
- 1차: `os.path.getmtime()` (O(1) stat, 네트워크 드라이브 경량)
- 2차: mtime 실패 시 tail 파싱 fallback

### 5) 매칭 루프 수정 ([L26384~](../../DataTool_dev_code/DataTool_optRCD_proto_.py:26384))

**Before**
```python
if status == "작업멈춤":
    ...
    elif code_desc:
        status = f"작업멈춤 - {code_desc}"      # 접두사 중복
elif status in ("작업중", "충전", "방전", "진행", "휴지"):
    ...
```

**After**
```python
if status == "작업멈춤":
    ...
    elif code_desc:
        status = code_desc                       # 🆕 접두사 제거
elif status in ("작업중", "충전", "방전", "진행", "휴지"):
    ...
# 🆕 완료/시험완료 → .log mtime 기반 elapsed 추가
_sb_tmp = status.split(" (")[0] if " (" in status else status
if status == "완료" or _sb_tmp == "시험완료":
    ch_path = self._build_channel_path(...)
    if ch_path:
        elapsed_str = self._elapsed_from_log(ch_path)
```

### 6) `STATUS_BG` 확장 ([L26508~](../../DataTool_dev_code/DataTool_optRCD_proto_.py:26508))

- `"시험완료"` → 연녹 (`_COMPLETED_BG`)
- `"작업멈춤"` (fallback) → 노랑 (`_STOPPED_BG`)
- `"챔버이슈"` → 빨강 (`_PAUSED_BG`)
- `_COMPLETED_BG`, `_IDLE_BG` 상수 추가로 가독성 개선

### 7) 행 배경색 분기 ([L26564~](../../DataTool_dev_code/DataTool_optRCD_proto_.py:26564))

STATUS_BG 미매칭 시 fallback 을 3 색 분기로 교체:
- `startswith("중단점 도달")` → 노랑
- `COMPLETED_LABELS` → 연녹
- `HW_WARNING_LABELS` → 빨강
- `USER_OR_ERROR_LABELS` → 노랑
- 그 외 (Code_Desc 안전조건 + 미정의 코드) → 빨강

### 8) 경과 열 글자색 분리 ([L26601~](../../DataTool_dev_code/DataTool_optRCD_proto_.py:26601))

- 완료/시험완료 (`COMPLETED_LABELS`) → 회색 (100, 100, 100) — 정상 방치
- 그 외 (사용자멈춤·중단점 도달 등) → 빨강 (150, 80, 80) — 이상 경고 (기존 유지)

## 색상 매핑 최종 정리

| 상태 | 배경 | 경과 열 글자색 |
|------|:---:|:---:|
| 작업중 / 충전 / 방전 / 진행 / 휴지 | ⬜ 기본 | — |
| 대기 / 준비 / 작업정지 | 🟢 녹 (셀없음) | — |
| **완료 / 시험완료** | 🟢 **연녹 (셀있음)** | 🔘 **회색** |
| 사용자멈춤 / 중단점 도달 / 작업멈춤(fallback) | 🟡 노랑 | 🔴 빨강 |
| **챔버이슈** | 🟥 **빨강** | 🔴 빨강 |
| 전압 상한/하한, OCV상한, 용량상한, 전압/전류 이상(경고) (Code 128/129/134/142/208/209) | 🟥 빨강 | — |

## 영향 범위

- **수정 파일**: `DataTool_dev_code/DataTool_optRCD_proto_.py` 1건
- **기능 영향**:
  - 현황 탭 검색/필터링 결과의 배경색·경과 열 표시 방식 변경
  - Code_Desc 표시에서 `"작업멈춤 - "` 접두사 제거
  - 완료/시험완료 채널에 경과 시간 회색으로 표시
- **리소스 영향**:
  - Code != 153 케이스 (약 14% 채널) `.log` 파싱 생략 → 검색 속도 소폭 개선
  - 완료/시험완료 채널에 `.log` mtime 호출 추가 (O(1) stat 이므로 무시 가능)
- **기존 기능 유지**:
  - Code=153 세분화 (`_classify_paused_reason`) — 변경 없음
  - 작업중 Reserve 추출 (`_parse_reserve_info`) — 변경 없음
  - Toyo 로직 — 영향 없음

## 테스트 시나리오

1. PNE 필터링 실행
   - ✅ State="완료" 채널 → 연녹 + 경과 "Nd Nh" (회색)
   - ✅ State="작업멈춤" + Code=134 → 라벨 "OCV상한" + 빨강
   - ✅ State="작업멈춤" + Code=153 + .log "사용자멈춤" → 노랑
   - ✅ State="작업멈춤" + Code=153 + .log "챔버이슈" → 빨강
   - ✅ State="작업멈춤" + Code=153 + .log "시험완료" → 연녹 + 경과 (회색)
2. 검색창
   - ✅ "안전조건" → Code_Desc 가 안전조건 집합에 포함된 채널만 매칭
   - ✅ "사용자멈춤계" → 사용자멈춤/중단점도달/챔버이슈/시험완료/작업멈춤 매칭
   - ✅ "OCV상한" → Code:134 채널 매칭 (Code_Desc 직접 매칭)

## 후속 단계

- Phase B: Sync_Time 이 오래된 경우 "PNE 동기화 지연" 경고 표시
- Phase C: `.sch` 진행률 교차 검증 → "시험완료(조건만족)" 자동 승격
