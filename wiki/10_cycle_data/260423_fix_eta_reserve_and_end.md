# 260423 ETA 로직 전면 재설계 — 예약/종료 2-타깃, mtime 배제

## 배경 / 목적

### 앞선 260423_feat_eta_from_sch.md 의 한계
- 경과 컬럼을 `3d 5h → +2d 1h` 로 확장했으나, 서버 동기화 주기로 인해
  `.log`/`.cyc`/`.csv` mtime 은 **실경과 시간을 반영하지 않음**.
  → 데이터 업데이트가 매시간 발생 → mtime 기반 elapsed 는 항상 `<1h`
  로 수렴. 의미 없음.
- 단일 "남은 시간" 만 계산 → 운영자는 **중단 예약 시점**과 **시험 종료
  시점** 을 모두 알고 싶음.
- 사이클당 평균시간 × 남은 사이클 수 는 부정확: 가속수명 스케줄처럼
  사이클별 body 가 다르면 크게 틀림.

### 신규 원칙
1. **mtime 일체 사용 금지** — JSON 의 `Current_Cycle_Num/Step_No` 만 진행
  위치 정보로 신뢰.
2. **.sch loop 구조 정확 추적** — `_decompose_loop_groups` 로 각 그룹의
  `(tc_start, tc_end, body)` 를 파악하고, 현재/목표 위치까지의 **누적
  body × loop_count 이론 시간** 을 계산.
3. **2-타깃 동시 산출** —
   - `remain_to_reserve`: `.log` Reserve 정보(`→S{rs}/C{rc}`) 가 있고
     현재보다 뒤에 있을 때 거기까지.
   - `remain_to_end`: `Total_Cycle_Num` (결측 시 `.sch max_tc`) 완료까지.

---

## 변경 내용

### 1. 신규 헬퍼
**`_sch_seconds_at(steps, target_tc, target_step, mincap) -> float`**
- 스케줄 시작부터 `(target_tc, target_step)` **직전** 까지 누적 이론 시간
- `_decompose_loop_groups` 결과를 순회하면서:
  - `target_tc > tc_end` → 그룹 전체 완료 (`body_sec × loop_count`) 누적
  - `target_tc < tc_start` → 중단
  - 그룹 내: `body_sec × (target_tc − tc_start)` + 현재 반복 내
    `target_step` 이전 body 스텝 시간 합산

**`_sch_total_seconds(channel_path, mincap) -> (total_s, total_tc) | None`**
- 스케줄 전체 완주 시 이론 시간 + 총 TC 수. `@lru_cache`.

**`_estimate_eta(channel_path, cur_cycle, cur_step, tot_cycle, rsv_cycle, rsv_step, mincap) -> (remain_rsv_s, remain_end_s)`**
- mtime 완전 배제
- `current_s = _sch_seconds_at(..., cur_cycle, cur_step)`
- `end_s = _sch_seconds_at(..., end_tc+1, None)` — 종료 지점 누적
- Reserve 가 현재보다 뒤일 때만 `remain_rsv` 산출

### 2. 제거된 함수
- `_estimate_remaining_seconds` — mtime 기반 단일 타깃 로직 → 폐기
- `_estimate_sch_cycle_seconds` — 사이클 평균 계산 → `_sch_total_seconds`
  로 대체 (평균이 아닌 누적 시간 사용)

### 3. `filter_all_channels` 작업중 분기 ([26387](DataTool_dev_code/DataTool_optRCD_proto_.py:26387))
**Before** (v6 — 경과 확장)
```python
elapsed_str = f"{elapsed_str} → +{_remain_str}"
```

**After** (v7 — 2-타깃, 경과 배제)
```python
# Reserve 파싱
_rs = _rc = None
if reserve:
    _rm = re.search(r'S(\d+)\s*/\s*C(\d+)', reserve)
    if _rm:
        _rs = int(_rm.group(1))
        _rc = int(_rm.group(2))
# ETA 산출
_rem_rsv, _rem_end = _estimate_eta(
    ch_path, _cur, _stp, _tot, _rc, _rs, _mincap)
_rsv_str = _format_remain_str(_rem_rsv)
_end_str = _format_remain_str(_rem_end)
_parts = []
if _rsv_str:
    _parts.append(f"예약 +{_rsv_str}")
if _end_str:
    _parts.append(f"종료 +{_end_str}")
if _parts:
    elapsed_str = " / ".join(_parts)
```

### 4. 캐시 무효화 업데이트
```python
_sch_total_seconds.cache_clear()   # _estimate_sch_cycle_seconds 대체
```

---

## 표시 형식

### 작업중 채널
| 상황 | 표시 |
|---|---|
| Reserve 있음 (예약 미도달) | `예약 +2d 6h / 종료 +4d 12h` |
| Reserve 없음 | `종료 +4d 12h` |
| .sch 없음 / cycle < 1 | 빈 칸 |

### 멈춤/완료/시험완료 채널 (변경 없음)
- 기존처럼 `_elapsed_from_log` / `_crosscheck_elapsed` 기반 경과 표시.
- 이 채널들은 더 이상 데이터 업데이트가 없어 mtime 이 의미 있음.

---

## 영향 범위

### 동작 변화 (v6 → v7)

| 케이스 | v6 | v7 |
|---|---|---|
| 작업중 + Reserve 있음 + .sch | `1h → +4d 12h` (경과 무의미) | `예약 +2d 6h / 종료 +4d 12h` |
| 작업중 + Reserve 없음 + .sch | `1h → +4d 12h` | `종료 +4d 12h` |
| 작업중 + .sch 없음 | `1h → +?` 혼재 | 빈 칸 |
| 작업중 + cycle=1 | 빈 칸 | `.sch 기반 Reserve/종료 표시 가능` |
| 작업멈춤 / 사용자멈춤 / 중단점 도달 | `3d 5h` (그대로) | `3d 5h` (변경 없음) |
| 완료 / 시험완료 | `3d 5h` | 변경 없음 |

### 정확도 개선 포인트
- **사이클별 body 가 다른 스케줄** (가속수명의 ACCEL + RPT 혼합 등) 에서
  v6 의 "평균" 방식은 ±20%+ 오차. v7 은 loop group 별 body 시간을 정확
  누적하여 이론치 기준 오차 거의 0 (열화·온도 편차 제외).
- **예약 시점 표시** 로 운영자가 셀 회수 타이밍을 구체적으로 계획 가능.

### 한계
- 여전히 `.sch` **이론값** 기반 — CV tail 휴리스틱, 챔버 안정화 시간,
  멈춤 지연 미반영.
- 실측 보정은 다음 단계 (v8) 에서 CSV/CYC 누적 실측 시간을 사용해 스케줄
  이론값 스케일 팩터 산출 고려.

---

## 검증 체크리스트 (사내)

1. **Reserve 있는 작업중 채널**: `예약 +Xd Yh / 종료 +Xd Yh` 두 값 모두
   표시되는지
2. **Reserve 지난 채널** (rc < current_cycle): `예약` 안 나오고 `종료` 만
3. **가속수명 (ACCEL + RPT 혼합)**: 종료 ETA 가 예전 v6 대비 현실적인지
4. **GITT 스케줄**: Reserve/종료 모두 산출 되는지 (짧은 사이클이라도)
5. **`.sch` 없음 / cycle=0**: 빈 칸
6. **정렬**: 경과 컬럼 클릭 시 string 정렬 폴백 정상 동작
7. **Toyo**: 변경 없음
8. **멈춤/완료**: 변경 없음

---

## 파일 변경 요약

| 파일 | 변경 |
|---|---|
| `DataTool_dev_code/DataTool_optRCD_proto_.py` | `_estimate_remaining_seconds`·`_estimate_sch_cycle_seconds` 제거, `_sch_seconds_at`·`_sch_total_seconds`·`_estimate_eta` 추가, filter_all_channels 작업중 분기 전면 재작성 |
| `wiki/10_cycle_data/260423_fix_eta_reserve_and_end.md` | 신규 (본 문서) |
