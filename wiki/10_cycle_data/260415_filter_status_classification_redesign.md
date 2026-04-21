# 현황 탭 상태 분류 로직 재설계안 (증거 기반)

## 1. 배경 및 목적

기존 `_classify_paused_reason()` / `_refine_paused_status()` 로직은
임계값·키워드 기반으로 작업멈춤 사유를 판별한다. 하지만 실 시험 데이터
(`DataTool_dev_code/data/exp_data`) 281 채널 로그 분석 결과,
이 접근 방식은 다음 문제가 있다:

1. **Paused Code:153 만 .log 파싱** → 나머지 6종 코드(128/129/134/142/208/209)는
   `"작업멈춤 - {Code_Desc}"` 로 일괄 접두사 치환 → UI 에서 모두 빨간색 이상 처리
2. **Code 의미 구분 없음** → 정상 조건 만족 종료(134/142)와 하드웨어 경고(208/209)가
   같은 색·같은 분류로 표시
3. **act vs Paused 순서만 판별** → "다음 조건 진행 대기"와 "사용자 멈춤"을 구분 못함

본 문서는 **증거 기반**(281 채널 전수 통계) 의 체계적 상태 분류 로직을 설계한다.

---

## 2. 실 데이터 분석 요약 (exp_data, PNE 281 채널)

### 2.1 Paused Code 분포 (실제 발견 7종)

| Code | Label | 설명 | 빈도 | 의미 구분 |
|------|-------|------|-----:|-----------|
| 153 | 작업멈춤종료 | 사용자 지령 / 외부 Error | 138 | 사용자·오류 |
| 134 | OCV상한 | OCV > 조건값 | 21 | **정상 조건 만족** |
| 142 | 용량상한 | 충방전 용량 > 조건값 | 12 | **정상 조건 만족** |
| 128 | 전압 상한 | 전압 > 조건값 | 3 | **정상 조건 만족** |
| 129 | 전압 하한 | 전압 < 조건값 | 2 | **정상 조건 만족** |
| 209 | 전류 이상(경고) | 명령 대비 +2% 초과 | 2 | **하드웨어 경고** |
| 208 | 전압 이상(경고) | 명령 대비 +1% 초과 | 1 | **하드웨어 경고** |

### 2.2 최종 이벤트 분포 (각 채널 1건)

| 최종 이벤트 | 건수 | 해석 |
|-----------|----:|------|
| ACT_AFTER_PAUSED(code=153) | 119 | 사용자 지령 후 재시작 / 다음 조건 진행 |
| TEST_WORK_COMPLETED | 50 | 명시적 시험 정상 완료 |
| ACT_START_ONLY | 26 | 작업 시작만 기록 (진행 중 or 단발 즉시 멈춤) |
| ACT_IMMEDIATE_STOP/DONE | 20 | act 즉시 멈춤/완료만 마지막 |
| PAUSED(code=153) | 19 | 사용자 멈춤 후 재시작 없음 |
| ACT_AFTER_PAUSED(code=134) | 17 | OCV상한 후 다음 조건 진행 |
| ACT_AFTER_PAUSED(code=142) | 8 | 용량상한 후 다음 조건 진행 |
| NO_ACT_NO_PAUSED | 6 | result file 만 있고 이벤트 없음 |
| PAUSED(code=134) | 4 | OCV상한에서 종료 |
| PAUSED(code=142) | 4 | 용량상한에서 종료 |
| PAUSED(code=129) | 2 | 전압 하한에서 종료 |
| ACT_AFTER_PAUSED(code=128) | 2 | 전압상한 후 진행 |
| ACT_AFTER_PAUSED(code=209) | 2 | 전류 경고 후 진행 |
| ACT_AFTER_PAUSED(code=208) | 1 | 전압 경고 후 진행 |
| PAUSED(code=128) | 1 | 전압상한에서 종료 |

### 2.3 카테고리별 스케줄 구조 (.sch 341건)

| 카테고리 | 수명_LOOP | Floating위주 | GITT | ECT | 기타 |
|---------|:---:|:---:|:---:|:---:|:---:|
| 복합floating | 38 | 24 | — | — | — |
| 성능 | 108 | 63 | 7 | 2 | 17 |
| 성능_시험직후 | — | 8 | — | — | 2 |
| 수명 | 72 | — | — | — | — |

- **수명_LOOP**: `CHG_CC → DCHG_CC → REST → LOOP → REST_SAFE → ...` 반복 (n_steps ≥ 20)
- **Floating**: `REST` 비중 ≥ 1/3, 충방전 ≤ 3회
- **GITT**: `GITT_START/PAUSE/END` 스텝 보유
- **ECT**: n_steps ≤ 20 단발 시퀀스

### 2.4 SaveEndData.csv 구조 (헤더 없는 CSV)

각 행 = 완료된 TotlCycle 1개. 주요 컬럼:

| idx | 필드 | 의미 |
|-----|------|------|
| 0 | TotlCycle | 누적 사이클 번호 |
| 2 | Condition | 1=충전, 2=방전, 3=휴지, 8=기타 |
| 3 | StepType | 서브 타입 (1=CC/CCCV, 2=CC, 255=N/A) |
| 7 | StepNo | .sch 상 Step 번호 |
| 32 | EndDate | `YYYYMMDD` |
| 33 | EndTime | `HHMMSSmmm` |

**파일 존재 + 마지막 행 = 최신 완료된 step 의 timestamp** 로 "최근 이벤트 시각"을
산출 가능 (로그 tail parsing 을 대체할 수 있는 정확한 소스).

---

## 3. 기존 로직 vs 새 로직 비교

### 3.1 기존 판별 흐름 (문제점 강조)

```
df.use == "작업멈춤" AND Code == "153" AND Code_Desc == "작업멈춤종료"
  → .log tail parsing → _classify_paused_reason()
      → act > Paused: act 줄로 분류 (Reserve 유무)
      → Paused > act: Paused 윗줄 act 로 분류
      → else: "작업멈춤"

df.use == "작업멈춤" AND Code != "153"
  → "작업멈춤 - {Code_Desc}"         ← ❌ 문제 1: 의미 구분 없음

df.use ∈ _NORMAL_STATES (운전중)
  → _parse_reserve_info()
      → "작업중 (→S{s}/C{c})" or 원본 유지
```

### 3.2 새 로직 흐름 (증거 기반 3 계층)

```
[Layer 1] 터미널 이벤트 판정 (.log tail 3-way 비교)
    TEST_WORK_COMPLETED  (가장 뒤)  → "시험완료"
    ACT_RUNNING          (act 최후, Paused 없음, "작업 시작/계속/다음 Step") → "작업중"
    ACT_STOP             (act 최후, "즉시 멈춤/완료")       → Layer 3-B 로
    ACT_AFTER_PAUSED     (act 가 Paused 뒤)                → Layer 2 + Reserve
    PAUSED               (Paused 가 최후)                   → Layer 2
    NO_EVENT             (로그 비어있음)                     → "알수없음"

[Layer 2] Paused Code 의미 분류 (CODE_SEMANTICS 테이블)
    128/129/134/142 = CONDITION_REACHED  (정상 조건 만족)
    153             = USER_OR_ERROR      (사용자 지령 or 외부 오류)
    208/209         = HW_WARNING         (측정 경고)

[Layer 3] 최종 상태 + 색상 매핑
    3-A) Paused 가 최후:
        CONDITION_REACHED → "조건도달 ({label})"        [연파랑]
        USER_OR_ERROR     → "사용자멈춤"               [노랑]
        HW_WARNING        → "하드웨어이상 ({label})"    [빨강]
        Chamber Alarm     → "챔버이슈"                  [빨강]
    3-B) act 가 최후:
        Reserve 있음 + Paused 없음 (ACT_RUNNING)       → "작업중 (→S{s}/C{c})"
        Reserve 있음 + Paused 존재 (ACT_AFTER_PAUSED) → "대기 (→S{s}/C{c}) | 직전: {code_label}"
        "즉시 완료"                                     → "사용자완료"
        "즉시 멈춤"                                     → "사용자멈춤"
    3-C) TEST_WORK_COMPLETED                          → "시험완료"
```

---

## 4. 핵심 매핑 테이블 제안

### 4.1 `CODE_SEMANTICS` (신규 추가)

```python
# Paused Code 의미 분류 — 실 데이터 기반 (2026-04-15 exp_data 분석)
PAUSED_CODE_SEMANTICS = {
    # (code, label, category, user_label)
    "128": ("전압 상한",   "CONDITION_REACHED", "전압상한 도달"),
    "129": ("전압 하한",   "CONDITION_REACHED", "전압하한 도달"),
    "134": ("OCV상한",     "CONDITION_REACHED", "OCV상한 도달"),
    "142": ("용량상한",    "CONDITION_REACHED", "용량상한 도달"),
    "153": ("작업멈춤종료", "USER_OR_ERROR",     "사용자멈춤"),
    "208": ("전압 이상",   "HW_WARNING",        "전압경고"),
    "209": ("전류 이상",   "HW_WARNING",        "전류경고"),
}

# 카테고리 → 배경색
CODE_CATEGORY_BG = {
    "CONDITION_REACHED": (185, 218, 234),  # 연파랑: 정상 조건 도달
    "USER_OR_ERROR":     (240, 220, 160),  # 노랑: 사용자 멈춤
    "HW_WARNING":        (214, 155, 154),  # 빨강: 하드웨어 이상
}
```

### 4.2 `TerminalEventType` (판별 결과 타입)

```python
from enum import Enum

class TerminalEventType(Enum):
    TEST_COMPLETED    = "test_completed"    # Test work completed 최후
    ACT_RUNNING       = "act_running"       # 작업 시작/계속/다음 Step (Paused 없음)
    ACT_USER_STOP     = "act_user_stop"     # 즉시 멈춤 act 최후
    ACT_USER_DONE     = "act_user_done"     # 즉시 완료 act 최후
    ACT_AFTER_PAUSED  = "act_after_paused"  # act > Paused, Reserve 있음 = 대기 상태
    PAUSED            = "paused"            # Paused 최후
    CHAMBER_ALARM     = "chamber_alarm"     # Paused 최후 + chamber alarm
    NO_EVENT          = "no_event"          # 유효 이벤트 없음
```

---

## 5. 구현 우선순위

### Phase A (즉시 효과) — 코드 변경 최소

1. `_classify_paused_reason` 을 `_refine_paused_status` 전체 대상(Code ∈ {128,129,134,142,208,209}) 으로 확대
2. `PAUSED_CODE_SEMANTICS` 딕셔너리 추가
3. 현황 탭 렌더링부 (`STATUS_BG`, `_PAUSED_BG`, `_STOPPED_BG`) 에 `CODE_CATEGORY_BG` 도입

### Phase B (정확도 개선) — SaveEndData 연계

4. SaveEndData.csv 의 마지막 행 timestamp 를 "최신 이벤트 시각" 의 primary source 로 채택
   (로그 tail parsing 은 fallback)
5. 마지막 row 의 Condition/StepNo 로 현재 스케줄 위치 표시

### Phase C (스케줄 교차 검증) — .sch 연계

6. `.sch` 총 step 수 × SaveEndData 최종 step 으로 **진행률 %** 산출
7. 진행률 ≥ 95% + PAUSED(CONDITION_REACHED) → "시험완료 (조건만족)" 로 승격 표시
8. 진행률 < 50% + PAUSED(USER_OR_ERROR) → "조기멈춤" 경고 표시

---

## 6. 영향 범위

- **수정 대상 함수** (`DataTool_dev_code/DataTool_optRCD_proto_.py`):
  - `FILTER_STATUS_KEYWORDS` (L25694) — 키워드 확장
  - `_NORMAL_STATES` (L25739) — 분류 기준 재정의
  - `_classify_paused_reason` (L25828) — 코드 기반 분류로 전면 재작성
  - `_refine_paused_status` (L25940) — Code 조건 분기 확장
  - 현황 탭 렌더링 (L26404 ~ 26548) — `STATUS_BG` 확장

- **신규 추가**:
  - `PAUSED_CODE_SEMANTICS` 상수 테이블
  - `CODE_CATEGORY_BG` 상수 테이블
  - `TerminalEventType` Enum
  - SaveEndData tail reader (Phase B)

- **UI 변경**:
  - 상태 셀에 "조건도달 (…)" / "하드웨어이상 (…)" / "사용자멈춤" 구분 가능
  - 배경색 3종 확장 (연파랑 추가)

---

## 7. 참고 수집 스크립트

분석에 사용한 스크립트 (추후 재현/검증 용, 임시 파일):

- `C:\tmp\analyze_exp_logs.py` — .log 태그 빈도 수집
- `C:\tmp\collect_paused_codes.py` — Paused Code × Label 전수 수집
- `C:\tmp\analyze_sch_and_csv.py` — .sch 스케줄 분류 + SaveEndData 샘플

결과 파일:
- `C:\tmp\paused_codes_report.txt` — Code 빈도 + 직전 act 컨텍스트
- `C:\tmp\sch_analysis.txt` — 스케줄 시그니처 분포
- `C:\tmp\saveenddata_samples.txt` — CSV 원본 샘플

---

## 8. 결론

- 현재 로직의 "임계값·키워드 기반" 판별은 **Code 153 편향** 되어 있으며
  나머지 정상 조건/하드웨어 경고 구분이 소실된다.
- 새 로직은 **(1) 터미널 이벤트 → (2) Code 의미 → (3) 스케줄 진행률** 의
  3 계층 교차 판정으로, 실 데이터 281 채널 기준 모든 케이스를 명시적으로 매핑한다.
- Phase A 구현만으로도 UI 에 정상 조건 종료/사용자 멈춤/하드웨어 경고가
  **다른 색·다른 라벨** 로 표시되어 즉시 현장 운용성이 향상된다.
