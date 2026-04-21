# v2 보완 — 작업중 채널의 Reserve(중단예약) 정보 처리

## 1. 지적 사항

v2 설계는 `.log` 를 "Code=153 세분화" 에만 사용한다고 가정했으나,
현재 코드는 **State ∈ {작업중/충전/방전/진행/휴지} 인 채널에서도**
`.log` 를 열어 **Reserve Cycle/Step** (중단예약) 을 추출한다.

관련 코드:

- [_parse_reserve_info L25906](../../DataTool_dev_code/DataTool_optRCD_proto_.py:25906) — 작업중 채널의 .log tail 에서 `Reserve Cycle:X, Step:Y` 패턴 추출
- [filter 26313~26320](../../DataTool_dev_code/DataTool_optRCD_proto_.py:26313) — 운전 중 상태에도 `_parse_reserve_info` 호출, 결과를 `"작업중 (→S{s}/C{c})"` 로 표시

따라서 v2 의 Layer 구조는 **운전 중 Reserve 표시** 요구사항을 빠뜨렸다.

---

## 2. 해결 선행 조건 — JSON 스키마 전수 조사

현재 BDT 코드는 `_pne_cols` 에 정의된 13개 필드만 읽는다:

```python
["Ch_No", "State", "Test_Name", "Schedule_Name",
 "Current_Cycle_Num", "Step_No", "Total_Cycle_Num",
 "Voltage", "Result_Path", "Code", "Code_Desc", "Type"]
```

그러나 `Module_{N}_channel_info.json` 에 더 많은 필드가 있을 가능성이 높다.
특히 다음이 존재하면 `.log` 파싱을 완전히 제거 가능:

**가능성 있는 JSON 필드명** (추정):
- `Reserve_Cycle_Num`, `Reserve_Step_No` (직접 필드)
- `Next_Stop_Cycle`, `Next_Stop_Step`
- `Scheduled_End_Cycle`, `Scheduled_End_Step`
- `Pending_Command`, `Reserved_Operation`

### 확인 절차

1. Y: 드라이브 연결된 상태에서 진단 스크립트 실행:
   ```
   python C:\tmp\probe_pne_json_schema.py
   ```
2. 결과 파일(`C:\tmp\pne_json_schema_report.txt`) 에서:
   - **Reserve 관련 필드 존재 여부** 확인
   - 전체 필드 목록 → `_pne_cols` 누락 필드 파악
3. 확인 결과에 따라 아래 Path 중 택일.

---

## 3. 시나리오별 설계

### Path A — JSON 에 Reserve 필드 존재 (이상적)

→ `.log` 파싱 100% 제거 가능

```
Layer 1 (JSON 단독):
  State × Code × Reserve_Cycle/Step
    - 작업중 + Reserve 있음: "작업중 (→S{s}/C{c})"
    - 작업중 + Reserve 없음: "작업중"
    - 작업멈춤 + Code:153 + Reserve 있음: "중단점 도달 (S{s}/C{c})"
    - 작업멈춤 + Code ∈ {128,129,134,142}: "조건도달 (…)"
    - 작업멈춤 + Code ∈ {208,209}: "하드웨어이상 (…)"
```

`_parse_reserve_info`, `_classify_paused_reason` **모두 제거/축소**.
평균 필터링 시간 30~50 ms 수준까지 단축.

### Path B — JSON 에 Reserve 필드 없음 (현실적 가능성)

→ `.log` 파싱은 **Reserve 판별이 필요한 채널에 한해** 유지

최적화 전략:
1. **JSON State 를 1차 분류**:
   - `State == "완료"` / `"대기"` / `"준비"` / `"작업정지"` → .log 불필요
   - `State == "작업멈춤"` + `Code ∈ {128,129,134,142,208,209}` → .log 불필요 (Code 로 확정)
   - `State == "작업멈춤"` + `Code == "153"` → .log 파싱 (현행)
   - `State ∈ 운전중` → **조건부** .log 파싱

2. **운전중 Reserve 확인 최적화**:
   - Sync_Time 이 최근(예: < 30분) 이면 현재 State 값 신뢰
   - `State == "작업중"` 직후 .log 는 커버리지 낮음 (예약이 아직 설정 전)
   - 기존 구현 유지하되, **Reserve 사용자가 "활성" 라벨링 했는지** 옵션 제공
     (예: 검색 키워드 "예약" 입력 시에만 .log 파싱)

3. **배치 I/O**:
   - 운전 중 채널 묶음(PNE 모듈 단위) 으로 `ThreadPoolExecutor(max_workers=8)`
     동시 .log tail 읽기 → 순차 파싱 대비 5~10× 단축

### Path C — 하이브리드 (권장)

JSON 조사가 끝나기 전이라도 **안전하게 점진 도입**:

```
[즉시 적용 가능 — Path B 준용]
1. Code ∈ {128,129,134,142,208,209} → .log 생략 (조건도달/HW경고 확정)
2. Code == "153" → .log 파싱 (현행 유지)
3. State ∈ 운전중 → .log 파싱 (현행 유지, 단 배치 I/O 로 최적화)
4. State ∈ {완료, 대기, 준비, 작업정지} → .log 생략 (현행 유지)

[JSON 조사 후 Path A 로 승격]
- Reserve 필드 확인되면 3) 번도 제거
- 남은 .log 파싱 케이스: Code:153 세분화 (필요 시만)
```

---

## 4. v2 Phase A 재정의 (Path C 기반)

**변경 전 (v2 초안)**:
1. PAUSED_CODE_SEMANTICS 추가
2. Code 전수 분기 → 128/129/134/142/208/209 는 .log 생략
3. CATEGORY_BG 추가

**변경 후 (addendum 반영)**:
1. PAUSED_CODE_SEMANTICS 추가 (동일)
2. Code 분기 → **작업멈춤 + Code ∈ {128,129,134,142,208,209} 만** .log 생략
3. Code == "153" 은 현행 `.log` 파싱 유지 (세분화 품질 필요)
4. **운전중 State 는 현행 `_parse_reserve_info` 유지**
5. CATEGORY_BG 추가 (동일)
6. **신규**: JSON 스키마 조사 스크립트 실행 → 결과에 따라 Phase A' (Reserve 필드 제거) 추진 여부 결정

### 예상 리소스 절감 (Path C)

| 채널 유형 | 비중 (281 샘플 기준) | .log 파싱 | 변화 |
|-----------|:---:|:---:|:---:|
| 작업멈춤 + Code ∈ 코드 테이블 (153 제외) | 14% | **제거** | ✅ |
| 작업멈춤 + Code == 153 | 49% | 유지 | — |
| 운전중 (작업중/충전/방전/진행/휴지) | 12% | 유지 (배치 최적화) | 🔄 |
| 완료/대기/준비/작업정지 | 25% | 생략 (기존) | — |

→ **약 14% 채널의 .log I/O 즉시 제거** + 배치 I/O 로 운전중 채널도 5~10× 개선.
  JSON 에 Reserve 필드 확인되면 추가로 12% 채널 제거 가능 → 총 76% 채널에서 .log 생략.

---

## 5. 조사 결과 반영 흐름

```
[1] 진단 스크립트 실행 (probe_pne_json_schema.py)
    ↓
[2] 결과 파일 검토
    → Reserve 필드 발견 ▶ Path A 로 전환
    → 발견 안 됨          ▶ Path C (Path B+배치) 유지
    ↓
[3] Phase A 구현 (공통 부분)
    - PAUSED_CODE_SEMANTICS
    - Code ∈ {128,129,134,142,208,209} 직접 분류
    - CATEGORY_BG
    ↓
[4] Phase A' (JSON 스키마 확인 결과에 따라)
    - Path A: _parse_reserve_info 제거, State 기반 운전중 라벨링
    - Path C: ThreadPoolExecutor 배치 I/O 도입
    ↓
[5] Phase B/C (기존 v2 로드맵 계속)
```

---

## 6. 결론

- v2 의 "JSON 우선" 원칙은 유효하지만, **작업중 채널의 Reserve 정보 처리**를
  누락했다는 지적은 정확.
- 현실적 해결책은 **JSON 스키마 조사 결과에 따라 Path A/C 분기**.
- 조사 전이라도 **Path C (즉시 14% 절감)** 는 안전하게 적용 가능하며,
  이후 JSON 에 Reserve 필드 확인 시 Path A 로 승격.
- 진단 스크립트 `C:\tmp\probe_pne_json_schema.py` 를
  Y: 드라이브 연결 상태에서 1 회 실행하여 방향을 확정하는 것이 선행 필수.
