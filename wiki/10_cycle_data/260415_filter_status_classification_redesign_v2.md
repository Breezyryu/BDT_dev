# 현황 탭 상태 분류 로직 재설계안 v2 — JSON 우선 기반

## 1. v1 대비 핵심 변경 사항

v1 에서는 `.log` 파일 tail parsing 을 Layer 1 의 주력 소스로 제안했으나,
실제 운용 환경에서는 **PNE cycler 의 `Module_{1,2}_channel_info.json`** 이
이미 다음 정보를 채널별로 제공한다:

- `State` — 현재 상태 ("작업중", "작업멈춤", "완료" 등)
- `Code`, `Code_Desc` — Paused 코드 + 설명
- `Type` — 현재 동작 타입 (Charge/DisCharge/Rest)
- `Current_Cycle_Num`, `Step_No`, `Total_Cycle_Num` — 실시간 위치
- `Voltage`, `Temperature` — 측정값
- `Schedule_Name`, `Result_Path` — 스케줄/결과 경로
- `Sync_Time_Day`, `Sync_Time` — 마지막 갱신 시각

⇒ **.log 파싱은 대부분 불필요.**
   JSON 1회 I/O (PNE 모듈당, 채널 수와 무관) 로 전체 정보 확보 가능.
   `.log` 는 JSON 이 Code 를 주지 않는 예외 케이스의 **보조 증거** 로만 사용.

### 리소스 비교

| 항목 | v1 (.log 우선) | v2 (.json 우선) |
|------|:---:|:---:|
| I/O 횟수 (PNE 25 모듈 × 채널 80개 = 2000채널) | **최대 2000회** (채널별 .log) | **25~50회** (모듈당 1~2 JSON) |
| 네트워크 경로 접근 | 채널 폴더별 탐색 | 루트 JSON 1회 |
| JSON 에 정보 있는 경우 | .log 중복 파싱 | .log 생략 |
| 평균 필터링 시간 | 수 초 (네트워크 지연) | **수십 ms** |

---

## 2. 기존 JSON 처리 코드 (현 상태)

`pne_data_make()` / `pne_table_make()` ([L25486](../../DataTool_dev_code/DataTool_optRCD_proto_.py:25486), [L25542](../../DataTool_dev_code/DataTool_optRCD_proto_.py:25542)) 는
이미 JSON 을 파싱하고 `Code`, `Code_Desc`, `Type` 컬럼을 `self.df` 에
포함시키고 있다. 즉 **데이터는 이미 확보되어 있으며 분류 로직만 개선하면 됨.**

```python
# 현재: JSON 에서 직접 읽는 필드
_pne_cols = ["Ch_No", "State", "Test_Name", "Schedule_Name",
            "Current_Cycle_Num", "Step_No", "Total_Cycle_Num",
            "Voltage", "Result_Path"]
for _extra in ("Code", "Code_Desc", "Type"):
    if _extra not in self.df.columns:
        self.df[_extra] = ""   # 없으면 빈 값
_pne_cols += ["Code", "Code_Desc", "Type"]
```

**문제점**: 이 JSON 기반 `Code`/`Code_Desc` 정보가 `_classify_paused_reason()` 에서
재활용되지 않고, 대신 각 채널의 `.log` 파일을 새로 열어 동일한 정보를 파싱한다.

---

## 3. 새 3-계층 로직 (JSON 우선)

### Layer 0: JSON 필드 정규화 (PNE 모듈당 1회)

```
Module_{1,2}_channel_info.json → df
  필수 필드:
    Ch_No, State, Code, Code_Desc, Type,
    Current_Cycle_Num, Step_No, Total_Cycle_Num,
    Voltage, Temperature, Sync_Time_Day, Sync_Time
```

이 단계는 이미 구현되어 있음. Sync_Time 이 오래된 경우(임계 예: 1일 초과) "stale" 플래그.

### Layer 1: `State × Code` 결정 (JSON 만으로 판별)

```
(State, Code) → 최종상태
```

| State | Code | 의미 카테고리 | 표시 라벨 |
|-------|------|--------------|-----------|
| 작업중 / 충전 / 방전 / 진행 / 휴지 | — | RUNNING | `{State}` (+ Type 병기) |
| 완료 | — | COMPLETED | `완료` |
| 대기 / 준비 | — | IDLE | `대기` |
| 작업정지 | — | IDLE_PAUSED | `작업정지` |
| 작업멈춤 | 128 | CONDITION_REACHED | `조건도달 (전압상한)` |
| 작업멈춤 | 129 | CONDITION_REACHED | `조건도달 (전압하한)` |
| 작업멈춤 | 134 | CONDITION_REACHED | `조건도달 (OCV상한)` |
| 작업멈춤 | 142 | CONDITION_REACHED | `조건도달 (용량상한)` |
| 작업멈춤 | 153 | USER_OR_ERROR | `작업멈춤` (.log 보조 분류로 세분화) |
| 작업멈춤 | 208 | HW_WARNING | `하드웨어이상 (전압경고)` |
| 작업멈춤 | 209 | HW_WARNING | `하드웨어이상 (전류경고)` |
| 작업멈춤 | 기타 | UNKNOWN_CODE | `작업멈춤 - {Code_Desc}` |

→ **281 채널 중 약 260 건 이상이 이 테이블만으로 확정 분류됨**
  (`Code` 가 비어있거나 153 이면서 사유 세분화가 필요한 경우에만 Layer 2 로 넘어감)

### Layer 2: .log 보조 파싱 (Layer 1 결과가 불충분할 때만)

```
Layer 1 결과가 "USER_OR_ERROR (Code:153)" 이거나
JSON 에 Code 가 비어있고 State == "작업멈춤" 인 경우에만:

→ 해당 채널의 최신 .log tail 을 열어 _classify_paused_reason() 호출
→ "사용자멈춤" / "중단점 도달 (S/C)" / "챔버이슈" / "시험완료" 로 세분화
```

주요 개선:
- 전수 채널이 아닌, Layer 1 에서 세분화가 필요한 **소수 채널**에만 적용
- 남은 케이스: 153 ≒ 138/281, 그 중 act > Paused 있는 것만 세분화 의미 있음
- 네트워크 I/O 현저히 감소

### Layer 3: `.sch` 총 step 수 × `Current_Cycle_Num/Step_No` 교차 검증 (선택)

```
진행률 = (Step_No + (Current_Cycle_Num - 1) * steps_per_cycle) / total_steps
```

- 100% + State == "작업멈춤" + Code in {128,129,134,142} → **승격 "시험완료 (조건도달)"**
- ≥95% + State == "작업중" → "마무리 단계"
- <50% + State == "작업멈춤" + Code=153 + "사용자멈춤" → **경고 "조기멈춤"**

`.sch` 는 `Schedule_Name` 으로 식별. 파일은 채널 폴더에 있으므로 1회 파싱 후 캐시.

---

## 4. 색상·UI 매핑 (JSON Code 기반)

```python
CATEGORY_BG = {
    "RUNNING":            None,                  # 기본색
    "COMPLETED":          (234, 239, 230),       # 연녹색 (유지)
    "IDLE":               (176, 203, 176),       # 녹색 (유지)
    "IDLE_PAUSED":        (176, 203, 176),       # 녹색 (유지)
    "CONDITION_REACHED":  (185, 218, 234),       # 🆕 연파랑 — 조건도달
    "USER_OR_ERROR":      (240, 220, 160),       # 노랑 _STOPPED_BG (유지)
    "HW_WARNING":         (214, 155, 154),       # 빨강 _PAUSED_BG (유지)
    "UNKNOWN_CODE":       (214, 155, 154),       # 빨강 (fallback)
}
```

---

## 5. 구현 계획 (재작성)

### Phase A — Layer 1 (JSON 만으로 분류, 즉시 효과)

1. `PAUSED_CODE_SEMANTICS` 상수 테이블 추가
   ```python
   PAUSED_CODE_SEMANTICS = {
       "128": ("전압상한 도달", "CONDITION_REACHED"),
       "129": ("전압하한 도달", "CONDITION_REACHED"),
       "134": ("OCV상한 도달", "CONDITION_REACHED"),
       "142": ("용량상한 도달", "CONDITION_REACHED"),
       "153": ("작업멈춤종료", "USER_OR_ERROR"),
       "208": ("전압경고",     "HW_WARNING"),
       "209": ("전류경고",     "HW_WARNING"),
   }
   ```
2. `_classify_from_json(state, code, code_desc) -> (label, category)` 신규 추가
3. `_refine_paused_status` 를 전 Code 대상으로 확장:
   - `Code` in `PAUSED_CODE_SEMANTICS` → 즉시 라벨 적용 (.log 파싱 생략)
   - `Code == "153"` 만 `.log` 보조 호출 (현행과 동일)
4. `STATUS_BG` 딕셔너리에 `CATEGORY_BG` 병합

### Phase B — Layer 2 최적화

5. `_read_log_tail` 호출을 "Code == 153 AND 세분화 필요" 조건으로만 제한
6. Sync_Time 이 최근(예: 6 시간 이내) 이면 .log 파싱 아예 생략
7. `_pne_last_sync_time` 을 채널별 `Sync_Time` 으로 확장 → 신선도 판별

### Phase C — Layer 3 진행률

8. `Schedule_Name` 기반 `.sch` 파싱 캐시 (`@lru_cache` on `(path, mtime)`)
9. 진행률 계산 함수 + "시험완료 승격" / "조기멈춤 경고" 로직
10. 현황 탭에 진행률 툴팁 표시 (옵션)

---

## 6. 영향 범위 (v1 대비 축소)

- **수정 대상**:
  - `FILTER_STATUS_KEYWORDS` (L25694) — "조건도달" 키워드 추가
  - `_NORMAL_STATES` (L25739) — 유지 (완료/대기/준비/작업정지)
  - `_refine_paused_status` (L25940) — Code 전수 분기로 확장
  - `_classify_paused_reason` (L25828) — Code == "153" 인 경우로 호출 축소
  - 현황 탭 `STATUS_BG` + 렌더링부 — 연파랑 추가

- **신규**:
  - `PAUSED_CODE_SEMANTICS` 상수
  - `_classify_from_json()` 메서드
  - `CATEGORY_BG` 상수

- **JSON 스키마 의존성 명시** (v2 에서 추가):
  - `Module_{1,2}_channel_info.json` 이 반드시 `Code`/`Code_Desc` 필드를 포함해야 함
  - 누락 시 기존 빈 문자열 fallback 유지 → Layer 2 (.log) 로 자동 우회

---

## 7. v1 과의 차이 요약

| 항목 | v1 | **v2 (JSON 우선)** |
|------|----|---|
| Layer 1 | .log tail 파싱 | **JSON `State × Code`** |
| Layer 2 | JSON Code 의미 분류 | **.log 보조 (153 & 불명확 케이스)** |
| Layer 3 | 진행률 | 진행률 (동일) |
| 네트워크 I/O | 채널별 .log (N) | **모듈당 JSON (N/80)** |
| 세분화 트리거 | 전수 | **Code 153 limited** |
| 구현 복잡도 | 높음 | **중간** |
| UI 즉시 개선 | Phase A 후 | **Phase A 후 동일** |

**v2 의 본질**: "이미 JSON 에 있는 정보를 굳이 .log 에서 다시 읽지 말자"
- v1 설계안의 Layer 순서를 뒤집어 JSON → .log(보조) → .sch(검증) 으로 재배열
- 코드 수정 부피는 줄이면서 실행 시간은 1~2 orders 단축

---

## 8. 결론

- `.log` 는 **폐쇄 후 1 회 기록** 되는 저빈도 데이터이며, Sync_Time 이 신선한
  JSON 이 존재하는 한 **truth source 는 JSON** 이 되어야 한다.
- 분류 로직의 골격은 **JSON 의 `State × Code`** 로 단순화되며, Code 의미 표가
  그 중심이 된다 (v1 의 `PAUSED_CODE_SEMANTICS` 를 그대로 사용).
- Phase A 만 적용해도 UI 에 Code 별 색 구분이 즉시 반영되고,
  평균 필터링 시간은 유의미하게 단축된다.
