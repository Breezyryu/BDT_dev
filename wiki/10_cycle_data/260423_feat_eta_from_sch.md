# 260423 필터링 탭 — .sch 기반 시험 남은 시간 예측 (ETA)

## 배경 / 목적

### 필요성
현황/필터링 탭은 `작업중` 채널의 **과거 경과 시간** (`3d 5h`) 만 표시.
운영자가 "언제 끝날지"를 알려면 별도 스케줄 문서를 뒤져야 함.
v4 (JSON 1순위 + CSV 교차검증), v5 (vol 셀유무 구분) 후속으로 **남은 시간
예측** 을 추가해 셀 회수·챔버 예약 등 리소스 계획에 사용할 수 있게 함.

### 기존 제약
- 500 채널 refresh 가 네트워크 드라이브 I/O 민감 → 채널당 추가 파싱 비용이
  문제.
- `.log`/`.cyc`/`.csv` mtime 외삽은 PNE 미기록 버그 (v4 맥락)와 사이클
  초기 통계 부족에 취약.
- BDT 에 이미 `.sch` 파서와 **캐시된 스케줄 구조 헬퍼** 가 존재.

### 해결 방향
**JSON (Current/Total_Cycle_Num, Step_No) + .sch 이론 시간** 으로
*"사이클당 평균 시간 × 남은 사이클 수 + 현재 사이클 내 tail 보정"*
계산. 기존 경과 컬럼 문자열을 `3d 5h → +2d 1h` 로 확장 — **컬럼 추가
없음, 화면 레이아웃 불변**. `filter_all_channels` 에만 적용.

---

## 의사결정

| 항목 | 선택 | 이유 |
|---|---|---|
| UI 위치 | 경과 컬럼 텍스트 확장 | 화면 레이아웃 변경 0, 회귀 리스크 최소 |
| 적용 범위 | 필터링 탭만 (`filter_all_channels`) | 작업중 채널이 한눈에 보이는 곳 |
| 정확도 | v1(사이클 평균) + v2(Step 보정) | 사내 검증 우선, 필요 시 CSV 하이브리드로 확장 |

---

## 변경 내용

### 1. 신규 헬퍼 (proto_.py:7395 부근 — `_get_pne_sch_struct` 뒤)

#### `_get_pne_sch_parsed(channel_path) -> dict | None`
`_parse_pne_sch` 전체 반환값(`steps` 포함) 캐싱. `@lru_cache(maxsize=256)`.

#### `_estimate_step_seconds(step, mincapacity) -> float`
스텝 1개의 이론 소요시간(초).

| 타입 | 공식 |
|---|---|
| CHG_CC / DCHG_CC / CHG_CP | `time_limit_s` → `cap_limit/current × 3600` → 0 |
| CHG_CCCV / DCHG_CCCV | `cc_time + min(cc_time × 0.25, 540s)` |
| REST / REST_SAFE | `time_limit_s` → 60s |
| LOOP / GOTO / GITT_* / UNKNOWN | 0 |

#### `_estimate_sch_cycle_seconds(channel_path, mincapacity) -> (cycle_sec, total_tc) | None`
전체 스케줄 이론 시간 / 전체 TC 수 = 사이클당 평균.
`_decompose_loop_groups` 로 body 스텝 추출해 `Σ body_sec × loop_count`.
`@lru_cache(maxsize=256)`.

#### `_estimate_remaining_seconds(channel_path, cur_cyc, tot_cyc, step_no, mincapacity) -> float | None`
- v1: `(tot_cyc − cur_cyc) × cycle_sec`
- v2: 현재 사이클 내 `step_no` 이전 스텝 이론 시간 합을 `cycle_sec` 에서 차감 → `remain_cur`
- `current_cycle < 2` / `.sch` 없음 / 총사이클 ≤ 현재 → None
- `tot_cyc` 결측/이상 시 `.sch max_tc` 폴백

#### `_format_remain_str(seconds) -> str`
`_elapsed_str` 과 동일 포맷 (`m`/`h`/`d`). 음수/None → `""`.

### 2. 캐시 무효화 (proto_.py:783 인근)
```python
_get_pne_sch_struct.cache_clear()
_get_pne_sch_parsed.cache_clear()          # 신규
_estimate_sch_cycle_seconds.cache_clear()  # 신규
_find_sch_file.cache_clear()
```

### 3. `filter_all_channels` 통합 (proto_.py:26387 (C) 작업중 분기)
Reserve 정보 부가 **이후** ETA 계산. 경과 컬럼 문자열 확장:
- 기존: `elapsed_str = ""` (작업중 분기에선 비어 있었음)
- 이제: `_elapsed_from_log(ch_path)` 1회 + `" → +{remain_str}"` 덧붙임
- ETA 산출 실패 (`.sch` 없음 등) 시 **원래대로 `""` 유지**

```python
elif status in ("작업중", "충전", "방전", "진행", "휴지"):
    ...
    if ch_path:
        reserve = self._parse_reserve_info(ch_path)
        if reserve:
            status = f"{status} ({reserve})"
        # ETA: .sch 이론 시간 + JSON Step/Cycle 진행도
        try:
            _cur = int(str(df.loc[ch_idx, "Current_Cycle_Num"]).strip())
            _tot = int(str(df.loc[ch_idx, "Total_Cycle_Num"]).strip())
            _stp = int(str(df.loc[ch_idx, "Step_No"]).strip())
        except (ValueError, KeyError, TypeError):
            _cur = _tot = _stp = 0
        _mincap = float(pne_min_cap(ch_path, 0, 1.0) or 0)
        _remain_s = _estimate_remaining_seconds(
            ch_path, _cur, _tot, _stp, _mincap)
        _remain_str = _format_remain_str(_remain_s)
        if _remain_str:
            if not elapsed_str:
                elapsed_str = self._elapsed_from_log(ch_path)
            elapsed_str = (
                f"{elapsed_str} → +{_remain_str}"
                if elapsed_str else f"+{_remain_str}")
```

### 4. 정렬 보정 (`_sort_filter_column` proto_.py:26887)
경과 컬럼 확장으로 `float("3d 5h → +2d 1h")` 가 ValueError 발생 → 기존 엔
문자열 폴백. ETA 앞 부분만 정렬 키로 사용하도록 `→` split:
```python
_txt = sort_key.text() if sort_key else ""
_key = _txt.split("→")[0].strip()
row_data.append((_key, _txt, cells))
# float 정렬 실패 시 _txt (원본) 기준 문자열 정렬
```

---

## 영향 범위

### 동작 변화

| 시나리오 | 기존 | v6 (ETA) |
|---|---|---|
| 작업중 + `.sch` 있음 + cycle ≥ 2 | 경과 빈칸 | `3d 5h → +2d 1h` |
| 작업중 + `.sch` 없음 | 경과 빈칸 | 경과 빈칸 (변경 없음) |
| 작업중 + cycle < 2 | 경과 빈칸 | 경과 빈칸 (초기 통계 부족) |
| 작업중 + `Total_Cycle_Num` 이상 | 경과 빈칸 | `.sch max_tc` 폴백 사용 |
| 멈춤/완료/시험완료 | 경과 + elapsed | **무변** (ETA 블록 미도달) |
| Toyo 채널 | 무변 | 무변 (`cycler_text in pne_info` 외부) |

### 성능
- `.sch` 파싱은 기존 v4 분류에서 이미 캐시 적중 (500채널 reload 시 첫회만 cost)
- 신규 함수 모두 `@lru_cache` 재사용
- 추가 I/O: 작업중 채널당 `_elapsed_from_log` 1회 (.log/.cyc mtime) — 100~200 채널 예상 → 1~2초 이내
- refresh 2회차부터 캐시 적중률 99%+

---

## 검증 체크리스트 (사내 환경)

1. **가속수명 채널** (ACCEL 500~1000 cycles): 경과 컬럼 `Xd Yh → +Xd Yh` 표시되는지, 실제 완료 시점 ±15% 이내
2. **GITT / SOC_DCIR** 채널: 표시 되는지 (오차 크더라도 ±25% 이내)
3. **사이클 초기** (`Current_Cycle_Num` < 2): ETA 미표시
4. **`.sch` 없는 PNE 채널** (테스트 초기 등): ETA 미표시, 경과 빈칸 유지
5. **멈춤/완료** 상태: 기존과 동일 (ETA 블록 미도달)
6. **Toyo 채널**: ETA 미적용, 기존 경과 표시 유지
7. **정렬 동작**: 경과 컬럼 클릭 시 `→` 앞 부분으로 정렬됨
8. **refresh 성능**: v5 대비 +10% 이내 시간 증가

### 오차 로깅 (선택 확장)
실측 대비 편차 > 50% 케이스를 콘솔에 `[ETA warn] ch=... theory=... real=...` 로
남겨 튜닝 기초 자료로 활용.

---

## 파일 변경 요약

| 파일 | 변경 |
|---|---|
| `DataTool_dev_code/DataTool_optRCD_proto_.py` | +154 / -7 (헬퍼 5개, 분기 확장, 정렬 보정, 캐시 클리어) |
| `docs/code/01_변경로그/260423_feat_eta_from_sch.md` | 신규 |
