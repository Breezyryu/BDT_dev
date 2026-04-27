# 260423 ETA 기능 제거 — 중단·완료(셀있음) 만 경과시간 표시

## 배경 / 목적

### 폐기 결정
앞선 두 차례 ETA 시도 (260423_feat_eta_from_sch.md, 260423_fix_eta_reserve_and_end.md)
는 다음 한계로 운영 정확도 미달:

- **mtime 기반 elapsed 무의미**: 서버가 매시간만 데이터 동기화 → `.log`/
  `.cyc`/`.csv` mtime 은 항상 1시간 이내, 실제 시험 경과 미반영.
- **.sch 이론 기반 ETA 부정확**: CV tail 휴리스틱·챔버 안정화·열화 미반영
  으로 실측과 편차 큼. 운영자 신뢰 떨어짐.
- **추가 파일 I/O 비용**: refresh 시 채널당 .sch 파싱 부담.

→ ETA 표시 자체를 **제거**. 대신 **운영상 의미 있는 시점에만 경과시간**
표시:

| 케이스 | 표시 여부 | 이유 |
|---|---|---|
| 중단 (작업멈춤/사용자멈춤/중단점도달/챔버이슈/잠시멈춤) | ✅ | 멈춘 후로 시간이 더 안 흐르므로 mtime 의미 있음 |
| 완료/시험완료 + **셀있음** (vol≠"-") | ✅ | 회수 대기 — 시험 종료 후 셀이 얼마나 방치됐는지 운영 지표 |
| 완료/시험완료 + **셀없음** (vol="-") | ❌ | 이미 회수 완료 — 시간 표시 의미 없음 |
| 작업중/충전/방전/진행/휴지 | ❌ | mtime 매시간 갱신 → 무의미 |
| 대기/준비/작업정지 | ❌ | (기존 동작 유지) |
| Toyo 채널 | ❌ | (PNE 분기 외부 — 영향 없음) |

---

## 변경 내용

### 1. 제거된 함수 (proto_.py:7433~7637 일대)
- `_get_pne_sch_parsed`
- `_estimate_step_seconds`
- `_sch_seconds_at`
- `_sch_total_seconds`
- `_estimate_eta`
- `_format_remain_str`

총 ~205 LoC 제거. `.sch` 파싱은 분류용 `_get_pne_sch_struct` 만 유지.

### 2. 캐시 무효화 단순화 (proto_.py:783)
```python
_get_pne_sch_struct.cache_clear()
_find_sch_file.cache_clear()
```
ETA 캐시 (`_get_pne_sch_parsed`, `_sch_total_seconds`) 제거.

### 3. `filter_all_channels` (C) 작업중 분기 단순화 ([26441](DataTool_dev_code/DataTool_optRCD_proto_.py:26441))
**Before** (v7 — ETA 2-타깃)
```python
elif status in ("작업중", "충전", "방전", "진행", "휴지"):
    ch_path = ...
    if ch_path:
        reserve = self._parse_reserve_info(ch_path)
        if reserve:
            status = f"{status} ({reserve})"
        # ETA 계산 (Reserve/종료) ... 약 30 LoC
        elapsed_str = " / ".join(_parts)
```

**After** (v8 — ETA 제거)
```python
elif status in ("작업중", "충전", "방전", "진행", "휴지"):
    ch_path = self._build_channel_path(df, ch_idx, has_rpath, has_path)
    if ch_path:
        reserve = self._parse_reserve_info(ch_path)
        if reserve:
            status = f"{status} ({reserve})"
    # 경과시간 미설정 — 빈 칸 유지
```

### 4. (D) 완료/시험완료 분기에 vol 체크 추가 ([26458](DataTool_dev_code/DataTool_optRCD_proto_.py:26458))
**Before**
```python
if status == "완료" or _sb_tmp == "시험완료":
    ...
    elapsed_str = self._elapsed_from_log(ch_path)
    if not elapsed_str:
        elapsed_str = self._crosscheck_elapsed(ch_path)
```

**After**
```python
# 완료/시험완료 → 셀있음(vol!="-") 일 때만 경과시간 표시
if (status == "완료" or _sb_tmp == "시험완료") and vol != "-":
    ...
    elapsed_str = self._elapsed_from_log(ch_path)
    if not elapsed_str:
        elapsed_str = self._crosscheck_elapsed(ch_path)
```

### 5. 정렬 로직 복원 (`_sort_filter_column` [26762](DataTool_dev_code/DataTool_optRCD_proto_.py:26762))
ETA 시절 추가했던 `→` 분리 로직 제거. 원래의 단순 string/float 정렬 폴백
구조로 복귀.

---

## 동작 변화 매트릭스

| 상태 | vol | v7 (ETA) | v8 (현재) |
|---|---|---|---|
| 작업중 + Reserve | 무관 | `예약 +X / 종료 +Y` | **빈 칸** |
| 작업중 | 무관 | `종료 +Y` | **빈 칸** |
| 완료 + 셀있음 | 정상 | `3d 5h` | `3d 5h` (변경 없음) |
| 완료 + 셀없음 | `-` | `3d 5h` | **빈 칸** |
| 시험완료 + 셀있음 | 정상 | `3d 5h` | `3d 5h` |
| 시험완료 + 셀없음 | `-` | `3d 5h` | **빈 칸** |
| 작업멈춤 / 사용자멈춤 / 중단점도달 / 챔버이슈 | 무관 | `3d 5h` | `3d 5h` (변경 없음) |
| 대기 / 준비 / 작업정지 | 무관 | 빈 칸 | 빈 칸 (변경 없음) |
| Toyo 채널 | 무관 | 변경 없음 | 변경 없음 |

---

## 영향 범위

### 의도한 효과
- 잘못된 mtime 기반 경과시간을 작업중 채널에서 제거 → **오해 소지 차단**
- 완료된 셀이 회수 안 된 채로 방치된 시간을 운영자가 즉시 인지 → **셀 회수 관리** 도구 역할 명확화
- 코드 단순화: ~205 LoC 제거 + 호출부 30 LoC 축소

### 변경 없는 부분
- 중단 계열 분기 (A/B): 그대로 (`_classify_paused_reason` / `_elapsed_from_log` + CSV 교차검증)
- 셀있음/셀없음 색상 (v5): 그대로
- JSON 1순위 분류 (v4): 그대로
- Toyo 동작: 그대로

### 향후 (선택)
- 실측 기반 ETA (CSV 누적 시간 → 사이클 평균 계산) 가 필요하면 별도
  분기로 신중히 설계. 단, **서버 동기화 주기 영향** 고려해 mtime 의존을
  배제하고 CSV 의 `TotTime` 컬럼을 직접 합산하는 방식 권장.

---

## 파일 변경 요약

| 파일 | 변경 |
|---|---|
| `DataTool_dev_code/DataTool_optRCD_proto_.py` | -235 / +12 (헬퍼 6개 제거, 캐시 무효화 정리, 작업중 분기 단순화, 완료 분기 vol 체크, 정렬 복원) |
| `wiki/10_cycle_data/260423_remove_eta_show_elapsed_only_paused_done.md` | 신규 (본 문서) |
