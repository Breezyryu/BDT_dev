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

## 4. Code_Desc → 카테고리 매핑 (UI 색상용, 3색 확정)

최종 색상 정책은 **연녹(셀있음) / 노랑 / 빨강 3색**:

| 표시 라벨 | 근거 | 색상 |
|----------|------|:---:|
| `완료` | JSON State | 🟢 연녹 (셀있음) |
| `시험완료` | .log 파싱 결과 (Code:153 + Test work completed) | 🟢 **연녹 (셀있음)** |
| `사용자멈춤` | .log 파싱 결과 (Code:153) | 🟡 노랑 |
| `중단점 도달 (…)` | .log 파싱 결과 (Code:153 + Reserve) | 🟡 노랑 |
| `작업멈춤` | .log fallback (Code:153 키워드 없음) | 🟡 노랑 |
| `챔버이슈` | .log 파싱 결과 (Code:153 + chamber alarm) | 🟥 **빨강** |
| `전압 상한` (Code:128) | JSON Code_Desc | 🟥 빨강 (안전조건) |
| `전압 하한` (Code:129) | JSON Code_Desc | 🟥 빨강 (안전조건) |
| `OCV상한` (Code:134) | JSON Code_Desc | 🟥 빨강 (안전조건) |
| `용량상한` (Code:142) | JSON Code_Desc | 🟥 빨강 (안전조건) |
| `전압 이상(경고)` (Code:208) | JSON Code_Desc | 🟥 빨강 (안전조건) |
| `전류 이상(경고)` (Code:209) | JSON Code_Desc | 🟥 빨강 (안전조건) |

```python
PAUSED_CODE_CATEGORY = {
    # 사용자/오류 (.log 세분화) → 노랑 or 빨강 or 연녹 (세분화 결과에 따라)
    "153": ("작업멈춤종료",    "USER_OR_ERROR"),
    # 안전 조건 (이상 판정 필요) → 빨강
    "128": ("전압 상한",       "SAFETY_STOP"),
    "129": ("전압 하한",       "SAFETY_STOP"),
    "134": ("OCV상한",         "SAFETY_STOP"),
    "142": ("용량상한",        "SAFETY_STOP"),
    "208": ("전압 이상(경고)", "SAFETY_STOP"),
    "209": ("전류 이상(경고)", "SAFETY_STOP"),
}

# .log 세분화 결과 → 노랑 (사용자 계열)
USER_OR_ERROR_LABELS = frozenset({
    "사용자멈춤",
    "작업멈춤",       # _classify_paused_reason fallback
    # "중단점 도달 (S*/C*)" 는 startswith 로 판정
})

# .log 세분화 결과 → 빨강 (하드웨어/안전)
HW_WARNING_LABELS = frozenset({
    "챔버이슈",
})

# .log 세분화 결과 → 연녹 (완료 계열, 셀있음)
COMPLETED_LABELS = frozenset({
    "완료",           # JSON State == "완료"
    "시험완료",       # .log: Test work completed
})

CATEGORY_BG = {
    "COMPLETED":      QtGui.QColor(234, 239, 230),   # 연녹 (기존 완료 색상)
    "USER_OR_ERROR":  QtGui.QColor(240, 220, 160),   # 노랑 (기존 _STOPPED_BG)
    "SAFETY_STOP":    QtGui.QColor(214, 155, 154),   # 빨강 (기존 _PAUSED_BG)
    "UNKNOWN_CODE":   QtGui.QColor(214, 155, 154),   # 빨강 (fallback)
}
```

> `시험완료` 는 Test work completed 가 .log 끝에 있는 경우로, 시험이 정상
> 종료되어 **셀이 채널에 그대로 남아있는 상태** 이므로 JSON State "완료" 와
> 동일한 연녹 (셀있음) 으로 표시.

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

### 변경 후 (3색: 연녹/노랑/빨강)

```python
bg_color = STATUS_BG.get(status)    # "완료" 등은 여기서 바로 연녹 매칭
status_base = status.split(" (")[0] if " (" in status else status

if bg_color is None and status_base not in self._NORMAL_STATES:
    # (1) 시험완료 → 연녹 (셀있음, 완료 계열)
    if status_base in COMPLETED_LABELS:
        bg_color = CATEGORY_BG["COMPLETED"]
    # (2) 챔버이슈 → 빨강 (하드웨어/챔버 이슈)
    elif status_base in HW_WARNING_LABELS:
        bg_color = CATEGORY_BG["SAFETY_STOP"]
    # (3) 사용자멈춤 / 중단점 도달 / 작업멈춤(fallback) → 노랑
    elif (status.startswith("중단점 도달")
            or status_base in USER_OR_ERROR_LABELS):
        bg_color = CATEGORY_BG["USER_OR_ERROR"]
    # (4) Code 128/129/134/142/208/209 Code_Desc 라벨 → 빨강 (안전조건)
    else:
        bg_color = CATEGORY_BG["SAFETY_STOP"]
```

> `code_for_row` 변수를 튜플에 추가해도 되지만, status 문자열 자체가
> Code_Desc 라벨이므로 문자열 기반 판정만으로 충분.
> STATUS_BG 에 "시험완료" 를 추가 등록하면 위의 (1) 분기 없이도 첫 라인에서 매칭 가능.

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
3. State="작업멈춤" + Code=153 .log "사용자멈춤" → 🟡 노랑
4. State="작업멈춤" + Code=153 .log "시험완료" → 🟢 **연녹 + 경과시간 "N일 N시간"**
5. State="작업멈춤" + Code=153 .log "챔버이슈" → 🟥 빨강
6. State="작업멈춤" + Code=134 → `"OCV상한"` + 🟥 빨강
7. State="작업멈춤" + Code=142 → `"용량상한"` + 🟥 빨강
8. State="작업멈춤" + Code=208 → `"전압 이상(경고)"` + 🟥 빨강
9. **State="완료" → 🟢 연녹 + 경과시간 "N일 N시간"** (.log mtime 기반)
10. 검색창 "안전조건" 입력 → Code 128/129/134/142/208/209 채널 매칭
11. 검색창 "OCV상한" 입력 → Code 134 채널 매칭 (Code_Desc 직접 매칭)

---

## 10. 완료/시험완료 채널 경과 시간 표시 (.log 기반)

### 10.1 배경

`완료` / `시험완료` 상태 채널에 대해 **"시험 종료 후 얼마나 지났는지"** 를
현황 탭 `경과` 열에 표시한다. 셀이 채널에 방치된 시간이 길수록 자가방전 등
영향이 누적되므로 운용상 중요.

### 10.2 데이터 소스 — JSON Sync_Time 은 **사용 불가**

⚠️ **JSON 의 `Sync_Time_Day` / `Sync_Time` 은 완료 시각이 아님**

| 필드 | 실제 의미 |
|------|----------|
| `Sync_Time_Day` | JSON 파일이 마지막으로 **갱신**된 날짜 |
| `Sync_Time` | JSON 파일이 마지막으로 **갱신**된 시각 |

PNE 사이클러는 `Module_{N}_channel_info.json` 을 **주기적으로 덮어쓰기** 하므로
완료 채널도 Sync_Time 은 계속 최신값으로 갱신된다. → **완료 이후 경과 시간 추정 불가.**

대신 **.log 파일의 마지막 타임스탬프** 를 사용.
.log 는 시험 완료 이벤트 기록 후 사이클러가 더 이상 기록하지 않으므로
마지막 줄의 `YYYY/MM/DD HH:MM:SS` 가 실질적 완료 시각.

### 10.3 소스 옵션 비교

| 소스 | 정확도 | I/O 비용 | 권장 |
|------|:---:|:---:|:---:|
| JSON Sync_Time | ❌ (항상 현재) | O(1) | — |
| `.log` 마지막 줄 타임스탬프 | ✅ 완료 이벤트 시각 | tail 4KB 읽기 | **✅ 권장** |
| `.log` 파일 `mtime` | ✅ 쓰기 종료 시각 ≈ 완료 | O(1) (stat) | **✅ 대안** |

**권장: `.log` mtime 을 1차 소스 로 쓰고, 오차가 크거나 mtime 이 없으면 tail 파싱 fallback.**

이유:
- 완료 채널의 .log 는 완료 이벤트 이후 쓰기 없음 → mtime 이 완료 직후 고정
- `os.path.getmtime()` 은 O(1) (디렉터리 엔트리 읽기만) → tail 파싱보다 수십~수백 배 빠름
- 네트워크 드라이브(y:\) 에서도 stat 호출은 가벼움

### 10.4 구현

#### (A) 신규 헬퍼

```python
@staticmethod
def _elapsed_from_log(channel_path: str) -> str:
    """채널 폴더의 최신 .log 마지막 타임스탬프 → 현재까지 경과 문자열.

    1차: 최신 .log 파일의 mtime (빠름, 정확)
    2차: mtime 실패 시 .log tail 파싱으로 fallback

    return: "3d 5h" / "2h" / "45m" / "" (실패)
    """
    try:
        if not os.path.isdir(channel_path):
            return ""
        log_files = [f.path for f in os.scandir(channel_path)
                     if f.name.endswith('.log') and f.is_file()]
        if not log_files:
            return ""
        log_path = max(log_files, key=os.path.getmtime)

        # 1차: mtime 사용 (O(1))
        mtime_ts = os.path.getmtime(log_path)
        dt = datetime.fromtimestamp(mtime_ts)
        delta = datetime.now() - dt
        total_min = int(delta.total_seconds() / 60)
        if total_min < 0:
            # 시스템 시간 불일치 → tail 파싱 fallback
            tail = WindowClass._read_log_tail(log_path) or ""
            for ln in reversed(tail.splitlines()):
                log_time = WindowClass._extract_log_time(ln)
                if log_time:
                    return WindowClass._elapsed_str(log_time)
            return ""
        # 기존 _elapsed_str 과 동일한 포맷팅 재사용
        return WindowClass._elapsed_str(dt.strftime("%Y/%m/%d %H:%M:%S"))
    except Exception:
        return ""
```

> 기존 `_elapsed_str(log_time: str)` ([L25804](../../DataTool_dev_code/DataTool_optRCD_proto_.py:25804)) 의
> 포맷팅 로직(`N m / N h / N d N h`)을 그대로 재사용.

#### (B) 매칭 루프 적용 ([L26296~](../../DataTool_dev_code/DataTool_optRCD_proto_.py:26296))

```python
# 현행: elapsed_str 는 Code:153 .log 파싱 시에만 채워짐
elapsed_str = ""

# 🆕 추가: 완료/시험완료 상태 — .log mtime 기반
status_base = status.split(" (")[0] if " (" in status else status
if status == "완료" or status_base == "시험완료":
    ch_path = self._build_channel_path(df, ch_idx, has_rpath, has_path)
    if ch_path:
        elapsed_str = self._elapsed_from_log(ch_path)
```

### 10.5 성능 고려

- 완료/시험완료 채널이 많을 경우 `os.scandir + getmtime` 이 N 회 호출됨
- PNE 1 모듈당 평균 완료 채널 수 ≒ 10~30 → 네트워크 stat 수십 회
- 필요 시 `ThreadPoolExecutor(max_workers=8)` 배치 가능 (Phase B 최적화)

### 10.6 JSON `Sync_Time` 의 용도 재정의

Sync_Time 은 "완료 시각" 이 아니라 **"JSON 갱신 신선도 지표"** 로만 사용:
- 현재 시간과 Sync_Time 차이가 큼 (예: 1 시간 초과) → **"PNE 동기화 지연/오프라인"** 경고
- 이는 시험 상태와 무관하게 **시스템 상태** 로 별도 표시 가능 (옵션)

### 10.5 경과 열 색상 톤 (시각적 구분)

현행 렌더링 ([L26495~26499](../../DataTool_dev_code/DataTool_optRCD_proto_.py:26495)) 은
`elapsed_str` 이 있으면 빨강 계열(150,80,80) 글자색을 적용한다. 완료 채널의
경과 시간은 **이상이 아니라 정상적 방치** 이므로 **회색 계열** 로 구분:

```python
# col 3 렌더링 (현행)
item_elapsed = QtWidgets.QTableWidgetItem(elapsed_str)
item_elapsed.setFont(_font9)
if elapsed_str:
    # 🆕 완료 계열은 회색, 그 외(Code:153 멈춤)는 빨강 유지
    if status_base in COMPLETED_LABELS:
        item_elapsed.setForeground(QtGui.QColor(100, 100, 100))   # 회색
    else:
        item_elapsed.setForeground(QtGui.QColor(150, 80, 80))     # 기존 빨강
```

### 10.6 테스트 시나리오 추가

- 완료된 지 3일 된 채널 → `경과 = "3d"` (회색), 배경 연녹
- 완료된 지 5시간 된 채널 → `경과 = "5h"` (회색), 배경 연녹
- 시험완료로 분류된 지 1일된 채널 → `경과 = "1d"` (회색), 배경 연녹

## 10. 리소스 변화 (281 샘플 기준)

| 채널 유형 | 비중 | .log 파싱 (현행) | .log 파싱 (v3) | 변화 |
|-----------|:---:|:---:|:---:|:---:|
| 작업멈춤 + Code ∈ {128,129,134,142,208,209} | 14% | ✅ (_refine_paused_status?) | ❌ | 생략 |
| 작업멈춤 + Code == 153 | 49% | ✅ | ✅ | 유지 |
| 작업중 등 (Reserve 확인) | 12% | ✅ | ✅ | 유지 |
| 완료/대기/준비/작업정지 | 25% | ❌ | ❌ | — |

**즉시 절감**: 약 14% 채널의 .log I/O 제거 + Code 분류 명확화로 UI 품질 대폭 개선.
