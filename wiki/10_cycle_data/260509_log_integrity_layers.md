# PNE 데이터 무결성 다층 cross-check — `.log` + CSV TC + endpoint

**날짜**: 2026-05-09
**요청자**: 류성택 ("예외 기록은 .log에 남기는 게 원칙이다. 손상이 의심이 되면
.log를 참고하도록 해보자.")
**대상 함수**: `_parse_pne_log`, `_check_csv_tc_continuity`,
`_check_endpoint_anomaly`, `_classify_pne_integrity` (모두 신규)

---

## 배경 — silent corruption 탐지

PNE `.cyc`/CSV 데이터가 시험 도중 손상되어도 **현재 BDT 는 인지하지 못한다**.
사용자 voc 사이클 711-714 high cap 사례처럼 데이터 비대칭이 발생해도
콘솔/UI 에 표시 없이 그대로 분석에 들어간다.

PNE 시험기는 **운영자 stop/resume + 시스템 pause + endpoint 갱신**을
서로 다른 파일에 기록한다:

| Layer | 파일 | 정보 |
|---|---|---|
| L1 | `.log` (cp949) | 운영자 stop/resume, 시스템 pause, 시작 시각 |
| L2 | `SaveEndData.csv` | TC 1~max 의 sample (cycle-level ground truth) |
| L3 | `.cyc` 마지막 RecIndex | record-level 마지막 위치 (실시간) |

3-layer cross-check 로 silent corruption 의 1차 단서를 잡을 수 있다.

---

## 신규 함수 4종

### 1. `_parse_pne_log(log_path) → dict`

`.log` 파일에서 운영 이력 추출. cp949 인코딩, 정규식 기반.

인식 패턴:
| 패턴 | kind | 추출 |
|---|---|---|
| `작업 시작 act` | start | first_start_dt |
| `작업 계속 act` | resume | n_resumes++ |
| `act 즉시 멈춤 시행 (Current Cycle:N, Step:M / ...)` | stop | n_stops++, last_stop_cycle/step |
| `Paused. [ Code:N / ... ]` | pause | n_pauses++ |
| `was created` 또는 `result file [...]` | created | (참고용) |

반환: `{n_stops, n_resumes, n_pauses, last_stop_cycle, last_stop_step,
first_start_dt, last_event_dt, last_event_kind, n_lines, is_present}`

### 2. `_check_csv_tc_continuity(raw_df) → dict`

PNE SaveEndData col[27]=TotlCycle 의 1 부터 연속 검증. StepType==8 loop
마커 제외 후 판별.

- `tc_min != 1` → partial run (앞부분 누락, replicated 불가)
- 중간 gap → 데이터 손상

반환: `{tc_min, tc_max, n_unique, starts_at_one, has_gaps, n_missing_tc,
gap_intervals, is_anomaly}`

### 3. `_check_endpoint_anomaly(cyc_max_recidx, csv_max_recidx) → dict`

`.cyc` 와 SaveData CSV RecIndex 끝점 비교.

| 케이스 | 의미 |
|---|---|
| `gap > 0` (.cyc < CSV) | silent corruption — `.cyc` 만 손실 |
| `gap < -100` (.cyc > CSV) | SaveData 미갱신 — in_progress (자정 전) |
| `\|gap\| ≤ 100` | OK |

반환: `{cyc_max, csv_max, gap, has_anomaly, ratio_cyc_to_csv, reason}`

### 4. `_classify_pne_integrity(log_summary, csv_check, ep_check) → str`

3-layer 통합 → 4-tier integrity 분류:

| 우선순위 | tier | 조건 |
|---|---|---|
| 1 | `compromised` | endpoint anomaly 또는 CSV TC anomaly (실 누락) |
| 2 | `data_loss` | `.log` stop/pause 있으나 endpoint/TC 정상 (PNE 자동 복구) |
| 3 | `in_progress` | `last_event_kind == 'pause'` 이고 stop 0 |
| 4 | `clean` | 운영 이벤트 0 + 모두 정상 |

---

## 회귀 슈트

[`tools/test_code/regression_log_integrity.py`](../../tools/test_code/regression_log_integrity.py) — 8 테스트 모두 통과:

```
[PASS] _parse_pne_log(우정협 ATL ch08): n_stops=8 n_resumes=7 n_pauses=3
       last_stop=Cycle1 Step93 last_event=stop
[PASS] _parse_pne_log(missing)
[PASS] _check_csv_tc_continuity(clean): TC 1~760, gaps=False
[PASS] _check_csv_tc_continuity(partial start)
[PASS] _check_csv_tc_continuity(gap): [(3, 4)]
[PASS] _check_endpoint_anomaly (4 시나리오)
[PASS] _classify_pne_integrity (4 tiers)
[INFO] 우정협 ATL ch08 통합 → integrity='data_loss'
[PASS] real_uchunghyup → data_loss

Result: 8/8 passed
```

검증 시나리오:
- 실측 fixture: 우정협 ATL 2335mAh ch08 (`.log` + `SaveEndData.csv`)
- synthetic: partial start (TC 5~), 중간 gap (TC 1,2,5,6 → 누락 3,4)
- endpoint 4 시나리오: 정상 / silent corruption (.cyc 90% 손실) / in_progress / 둘 다 0
- 4-tier 분류: clean / data_loss / compromised(ep) / compromised(csv)

---

## 보류 — ChannelMeta 통합 + Phase 0 콘솔

**이번 회기 범위**: 단위 함수 4 + 단위 검증 8 통과까지.

다음 단계 (별도 회기에서 사용자 결정 시):

1. **ChannelMeta** ([proto_:380~417](../../DataTool_dev_code/DataTool_optRCD_proto_.py))
   에 신규 필드:
   - `integrity: str` ('clean'|'in_progress'|'data_loss'|'compromised')
   - `log_summary: dict | None`
   - `csv_check: dict | None`
   - `endpoint_check: dict | None`
2. **`_build_channel_meta`** ([proto_:7141~](../../DataTool_dev_code/DataTool_optRCD_proto_.py))
   에 통합 — 위 4 함수 호출 + `_classify_pne_integrity` 결정
3. **Phase 0 콘솔** — `_build_all_channel_meta_parallel` 끝에 ⚠ flag +
   detail line (운영 이력, gap_intervals, endpoint reason) 출력

이전 회기 (260508 환각/미저장) 의 detail line 디자인은
`260509_console_integrity_detail.md` 참조 가능 — 단, 통합 코드 위치
(`_build_all_channel_meta_parallel`) 의 현재 구현은 별도 분석 필요.

---

## ③ standalone PoC 폐기 결정

이전 세션에서 작업했다고 추정된 `tools/test_code/cyc_sch_tc_poc_v2.py`
(`.cyc + .sch` 단독 시뮬레이터) 는 디스크에 없으며, 본진 [`proto_.py`](../../DataTool_dev_code/DataTool_optRCD_proto_.py)
가 [commit 7232bd4 (4/30)](https://github.com/Breezyryu/BDT_dev/commit/7232bd4)
로 outer-goto 의미론 (`+52 goto_target`, `+580 goto_repeat`,
`main_loop_count`/`loop_groups`) 을 이미 흡수함. **재작성 가치 없음 — 폐기.**

대신 본진 `_parse_pne_sch` / `_get_pne_sch_struct` 의 simulator 정확도
회귀 검증이 필요하면, 이미 main 에 들어간 [`test_sch_parser.py`](../../DataTool_dev_code/test_code/test_sch_parser.py)
를 활용 (해당 테스트가 별개 브랜치에 있다면 `main` 동기화 후 활용).

---

## 변경 위치

1. [`DataTool_optRCD_proto_.py`](../../DataTool_dev_code/DataTool_optRCD_proto_.py)
   — `_extract_tc_info_pne` 직후 (line ~8094) 에 4 함수 + `_PNE_LOG_DT` /
   `_PNE_LOG_STOP_POS` 정규식 모듈 상수 신규
2. [`tools/test_code/regression_log_integrity.py`](../../tools/test_code/regression_log_integrity.py)
   — 단위 회귀 슈트 8 테스트 신규

---

## 후속

- ChannelMeta integrity 필드 + Phase 0 콘솔 통합 (사용자 결정 필요)
- `_check_endpoint_anomaly` 의 호출처 — `cyc_max_recidx` 를 어디서 얻을지
  (`_cyc_to_cycle_df` 결과의 RecIndex.max(), 또는 `.cyc` 마지막 record
  fid22 — 현재 미연결)
- 박민희 4.04mAh half cell (`.cyc` 90% 손실) 같은 알려진 compromised 채널
  fixture 추가 → 회귀 슈트 보강
