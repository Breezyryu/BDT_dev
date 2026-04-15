# 현황 탭 상태 분류 로직 재설계안 v3 (최종)

## 1. 확정 사항

사내 환경 확인 결과:
- **PNE `Module_{N}_channel_info.json` 에 Reserve(중단예약) 관련 필드 없음**
- 따라서 작업중 채널의 Reserve Cycle/Step 표시를 위해 `.log` 파싱은 계속 필요

## 2. 3-조건 분류 규칙 (확정)

```
(1) JSON State == "작업중" / "충전" / "방전" / "진행" / "휴지"
    → .log 파싱 (Reserve Cycle/Step 추출)
    → 표시: "{State}" or "{State} (→S{s}/C{c})"

(2) JSON State == "작업멈춤" AND Code == "153" AND Code_Desc == "작업멈춤종료"
    → .log 파싱 (_classify_paused_reason 으로 세분화)
    → 표시: "사용자멈춤" / "중단점 도달 (S{s}/C{c})" / "챔버이슈" / "시험완료"

(3) JSON State == "작업멈춤" AND Code != "153"
    → .log 파싱 없음
    → JSON 의 Code_Desc 텍스트를 그대로 사용
    → 표시: "{Code_Desc}"           # 예: "OCV상한", "용량상한", "전압 이상(경고)"
```

**그 외 State** (완료/대기/준비/작업정지) 는 현행대로 `.log` 파싱 없이 State 값 그대로 표시.

## 3. 현행 코드와의 차이

### 3.1 현행 동작 ([L26296~26320](../../DataTool_dev_code/DataTool_optRCD_proto_.py:26296))

```python
if cycler_text in pne_info:
    # 작업멈춤: Code/Code_Desc + .log 파싱
    if status == "작업멈춤":
        code = ... ; code_desc = ...
        if code == "153" and code_desc == "작업멈춤종료":
            ch_path = self._build_channel_path(...)
            if ch_path:
                status, elapsed_str = self._classify_paused_reason(ch_path)
        elif code_desc:
            status = f"작업멈춤 - {code_desc}"      # ← (3) 에 해당하나 접두사 "작업멈춤 - " 중복
    # 작업중: .log에서 Reserve 예약 정보 추출
    elif status in ("작업중", "충전", "방전", "진행", "휴지"):
        ch_path = self._build_channel_path(...)
        if ch_path:
            reserve = self._parse_reserve_info(ch_path)
            if reserve:
                status = f"{status} ({reserve})"
```

### 3.2 문제점

1. **(3) 규칙 위반**: `"작업멈춤 - {Code_Desc}"` 형식으로 접두사 `"작업멈춤 - "` 를 덧붙여
   표시 → 사용자 요청 규칙은 **Code_Desc 텍스트만** 출력
2. **UI 색상 미반영**: Code 별 의미 (조건도달 vs 하드웨어경고 vs 사용자멈춤) 가
   동일한 빨간 배경으로 처리됨 → 현장 가독성 저하
3. **FILTER_STATUS_KEYWORDS 편향**: `"유휴"` / `"작업멈춤"` 2 개만 정의,
   Code 단위 검색 불가 (예: "OCV상한" 검색 시 매칭 실패)

### 3.3 v3 변경 후

```python
if cycler_text in pne_info:
    if status == "작업멈춤":
        if code == "153" and code_desc == "작업멈춤종료":
            # (2) — .log 파싱 (기존 유지)
            ch_path = self._build_channel_path(...)
            if ch_path:
                status, elapsed_str = self._classify_paused_reason(ch_path)
        else:
            # (3) — Code_Desc 텍스트 그대로 (접두사 제거)
            if code_desc:
                status = code_desc            # ← "OCV상한", "용량상한" 등 그대로
    elif status in ("작업중", "충전", "방전", "진행", "휴지"):
        # (1) — .log Reserve 파싱 (기존 유지)
        ch_path = self._build_channel_path(...)
        if ch_path:
            reserve = self._parse_reserve_info(ch_path)
            if reserve:
                status = f"{status} ({reserve})"
```

## 4. Code_Desc → 카테고리 매핑 (UI 색상용, 2색 확정)

.log 파싱은 하지 않지만, Code 번호로 **의미 카테고리** 를 판정해 배경색 결정.
최종 색상 정책은 **노랑/빨강 2색**:

| 표시 라벨 | 근거 | 색상 |
|----------|------|:---:|
| `사용자멈춤` | .log 파싱 결과 (Code:153) | 🟡 노랑 |
| `중단점 도달 (…)` | .log 파싱 결과 (Code:153 + Reserve) | 🟡 노랑 |
| `챔버이슈` | .log 파싱 결과 (Code:153 + chamber alarm) | 🟡 노랑 |
| `시험완료` | .log 파싱 결과 (Code:153 + Test work completed) | 🟡 노랑 |
| `작업멈춤종료` (Code:153 기본) | JSON Code_Desc | 🟡 노랑 |
| `전압 상한` (Code:128) | JSON Code_Desc | 🟥 빨강 (안전조건) |
| `전압 하한` (Code:129) | JSON Code_Desc | 🟥 빨강 (안전조건) |
| `OCV상한` (Code:134) | JSON Code_Desc | 🟥 빨강 (안전조건) |
| `용량상한` (Code:142) | JSON Code_Desc | 🟥 빨강 (안전조건) |
| `전압 이상(경고)` (Code:208) | JSON Code_Desc | 🟥 빨강 (안전조건) |
| `전류 이상(경고)` (Code:209) | JSON Code_Desc | 🟥 빨강 (안전조건) |

```python
PAUSED_CODE_CATEGORY = {
    # 사용자/오류 (.log 세분화 가능) → 노랑
    "153": ("작업멈춤종료",    "USER_OR_ERROR"),
    # 안전 조건 (이상 판정 필요) → 빨강
    "128": ("전압 상한",       "SAFETY_STOP"),
    "129": ("전압 하한",       "SAFETY_STOP"),
    "134": ("OCV상한",         "SAFETY_STOP"),
    "142": ("용량상한",        "SAFETY_STOP"),
    "208": ("전압 이상(경고)", "SAFETY_STOP"),
    "209": ("전류 이상(경고)", "SAFETY_STOP"),
}

# .log 세분화 결과 라벨 → 노랑 (Code:153 계열 전부)
USER_OR_ERROR_LABELS = frozenset({
    "사용자멈춤", "챔버이슈", "시험완료", "작업멈춤종료",
    # "중단점 도달 (S*/C*)" 는 prefix 로 판정
})

CATEGORY_BG = {
    "USER_OR_ERROR":  QtGui.QColor(240, 220, 160),   # 노랑 (기존 _STOPPED_BG)
    "SAFETY_STOP":    QtGui.QColor(214, 155, 154),   # 빨강 (기존 _PAUSED_BG)
    "UNKNOWN_CODE":   QtGui.QColor(214, 155, 154),   # 빨강 (fallback)
}
```

> 연파랑 "조건도달" 분류는 사용하지 않는다. 정상 조건 종료도 결국 사용자가
> 원인을 확인해야 하는 "이상 가능성" 으로 간주하여 빨강으로 통일.

## 5. 렌더링부 수정 ([L26466~26472](../../DataTool_dev_code/DataTool_optRCD_proto_.py:26466))

### 현행

```python
bg_color = STATUS_BG.get(status)
status_base = status.split(" (")[0] if " (" in status else status
if bg_color is None and status_base not in self._NORMAL_STATES:
    if status.startswith("중단점 도달"):
        bg_color = _STOPPED_BG
    else:
        bg_color = _PAUSED_BG
```

### 변경 후 (2색 단순화)

```python
bg_color = STATUS_BG.get(status)
status_base = status.split(" (")[0] if " (" in status else status
if bg_color is None and status_base not in self._NORMAL_STATES:
    # Code:153 계열 (.log 파싱 결과 + 중단점 도달 + 기본) → 노랑
    if (status.startswith("중단점 도달")
            or status_base in USER_OR_ERROR_LABELS):
        bg_color = CATEGORY_BG["USER_OR_ERROR"]      # 노랑
    else:
        # Code 128/129/134/142/208/209 → 빨강 (안전조건)
        bg_color = CATEGORY_BG["SAFETY_STOP"]        # 빨강
```

> `code_for_row` 변수를 튜플에 추가해도 되지만, status 문자열 자체가
> Code_Desc 라벨이므로 문자열 기반 판정만으로 충분.

→ 행 렌더링 루프에서 해당 채널의 `Code` 값을 추적해야 하므로,
  `matched_by_floor` 튜플에 `code` 를 추가:

```python
# L26330~26332
matched_by_floor[floor_name][cycler_text].append(
    (ch_idx, testname, status, elapsed_str, cyc,
     vol, type_str, temp_str, cell_path, code))   # 🆕 code 추가
```

## 6. `FILTER_STATUS_KEYWORDS` 확장

```python
FILTER_STATUS_KEYWORDS = {
    "유휴":        ["완료", "준비", "작업정지"],
    "작업멈춤":     None,                         # _NORMAL_STATES 역조건 (기존)
    # 🆕 2색 분류 키워드
    "안전조건":     {"전압 상한", "전압 하한", "OCV상한", "용량상한",
                   "전압 이상(경고)", "전류 이상(경고)"},
    "사용자멈춤계": {"사용자멈춤", "중단점 도달", "챔버이슈",
                   "시험완료", "작업멈춤종료"},
}
```

`match_filter_text` 에서 set 타입도 처리하도록 약간 확장.
("중단점 도달" 은 prefix 매칭으로 처리)

## 7. 구현 범위 (한 번에 수행)

단일 커밋으로 구성 가능한 수준:

| 수정 대상 | 줄 | 변경 |
|----------|---:|------|
| `PAUSED_CODE_CATEGORY` 상수 | 신규 | 딕셔너리 정의 |
| `CATEGORY_BG` 상수 | 신규 | 딕셔너리 정의 |
| `FILTER_STATUS_KEYWORDS` | L25694 | "조건도달", "하드웨어경고" 추가 |
| `match_filter_text` | L25699 | set 타입 지원 |
| 작업멈춤 Code != 153 분기 | L26311 | `"작업멈춤 - "` 접두사 제거 |
| `matched_by_floor` 튜플 | L26330 | `code` 추가 |
| 행 렌더링부 | L26465 | 튜플 unpack 에 code 추가 |
| 배경색 로직 | L26468 | Code 카테고리 → CATEGORY_BG 조회 |

## 8. 영향 없음 (유지)

- `_classify_paused_reason`, `_parse_reserve_info`, `_build_channel_path` — 수정 불필요
- State == 작업중/충전/방전/진행/휴지 처리 — 현행 그대로
- State == 완료/대기/준비/작업정지 처리 — 현행 그대로
- `_refine_paused_status` — 사용처 없으면 제거 검토 (별도 확인 필요)

## 9. 테스트 시나리오

1. State="작업중" + Reserve 설정된 채널 → `"작업중 (→S14/C1)"` 표시
2. State="작업멈춤" + Code=153 + Reserve → `"중단점 도달 (S14/C1)"` + 🟡 노랑
3. State="작업멈춤" + Code=153 .log parsed "사용자멈춤" → 🟡 노랑
4. State="작업멈춤" + Code=153 .log parsed "챔버이슈" / "시험완료" → 🟡 노랑
5. State="작업멈춤" + Code=134 → `"OCV상한"` + 🟥 빨강
6. State="작업멈춤" + Code=142 → `"용량상한"` + 🟥 빨강
7. State="작업멈춤" + Code=208 → `"전압 이상(경고)"` + 🟥 빨강
8. 검색창 "안전조건" 입력 → Code 128/129/134/142/208/209 채널 매칭
9. 검색창 "OCV상한" 입력 → Code 134 채널 매칭 (Code_Desc 직접 매칭)

## 10. 리소스 변화 (281 샘플 기준)

| 채널 유형 | 비중 | .log 파싱 (현행) | .log 파싱 (v3) | 변화 |
|-----------|:---:|:---:|:---:|:---:|
| 작업멈춤 + Code ∈ {128,129,134,142,208,209} | 14% | ✅ (_refine_paused_status?) | ❌ | 생략 |
| 작업멈춤 + Code == 153 | 49% | ✅ | ✅ | 유지 |
| 작업중 등 (Reserve 확인) | 12% | ✅ | ✅ | 유지 |
| 완료/대기/준비/작업정지 | 25% | ❌ | ❌ | — |

**즉시 절감**: 약 14% 채널의 .log I/O 제거 + Code 분류 명확화로 UI 품질 대폭 개선.
