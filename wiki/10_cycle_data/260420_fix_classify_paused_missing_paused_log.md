# 260420 현황 탭 — PNE Paused 미기록 채널의 "작업중" 오분류 수정

## 배경 / 목적

### 현상
현황 탭·필터링에서 **State=작업멈춤 + Code=153 + Code_Desc=작업멈춤종료** 로 확정된
PNE 채널이 `작업중 (→S80/C98)` 처럼 "작업중" 으로 표시되는 버그.

실 사례: **PNE1 ch36** — JSON(`Module_1_channel_info.json`) 확인 결과
`State=작업멈춤 / Code=153 / Code_Desc=작업멈춤종료` 인데 UI 에는
`작업중 (S80/C98)` 으로 출력 + 경과/동작 컬럼 `-`.

### 원인
`WindowClass._classify_paused_reason()` 는 `.log` 파일 tail 만으로 사유를
판별한다. PNE 펌웨어가 `Paused` 이벤트를 `.log` 에 기록하지 않은 케이스
(사용자 확인 사항) 에서:

- `last_paused_idx = -1` (Paused 없음)
- `last_act_idx > last_paused_idx` 분기 진입
- 마지막 `act` 줄의 `Reserve Cycle:98, Step:80` 패턴 매칭
- `return f"작업중 (→S{rs}/C{rc})", ""` ← 문제 지점

이 반환값은 호출부에서 **State/Code 와 충돌**. 호출부
(`filter_all_channels` / `_refine_paused_status`) 는 이미
`State ∈ {작업멈춤, 잠시멈춤} AND Code==153` 을 확정한 뒤 이 함수를
호출하므로, "작업중" 반환은 논리적 모순.

기존에는 호출부에 "`작업중 (→S/C)` 판정 후 Reserve S/C == JSON Step/Cycle
+ `.cyc mtime > 1일` 이면 중단점 도달로 재판정" 하는 방어 블록이 있었으나,
실제 케이스(Reserve Step=80 vs JSON Step_No=90)처럼 값이 불일치하면
재판정 실패 → 원래의 "작업중" 이 그대로 유지되는 한계.

---

## 변경 내용

### 1. `_classify_paused_reason` — `.log` 에 Paused 누락 시 로직 수정
**파일**: `DataTool_dev_code/DataTool_optRCD_proto_.py` (line 25718~25794)

**Before** (line 25755~25769)
```python
# Reserve Cycle 포함: 예약 "설정"만 되어있고 도달하지 않음 → 작업중
# (Paused가 없으므로 채널은 아직 진행 중)
reserve_m = re.search(
    r'Reserve Cycle:\s*(\d+),\s*Step:\s*(\d+)', act_line)
if reserve_m:
    rc, rs = reserve_m.group(1), reserve_m.group(2)
    return f"작업중 (→S{rs}/C{rc})", ""
if "즉시 멈춤 시행" in act_line or "즉시 완료 시행" in act_line:
    return "사용자멈춤", elapsed
if ("작업 시작 act" in act_line or "작업 계속 act" in act_line
        or "다음 Step act" in act_line):
    return "작업중", ""
return "작업멈춤", elapsed
```

**After**
```python
# 호출부는 이미 State=작업멈춤/잠시멈춤 + Code=153 을 확정한 뒤 이 함수를
# 부르므로, Paused 줄 누락(PNE 미기록) 이어도 '작업중' 반환은 모순.
# → 멈춤 사유만 세분 분류한다.
# Reserve Cycle 패턴 → 예약 지점에 도달해 멈춘 것으로 해석
# (PNE가 Paused 이벤트를 .log에 기록하지 못한 케이스 포함)
reserve_m = re.search(
    r'Reserve Cycle:\s*(\d+),\s*Step:\s*(\d+)', act_line)
if reserve_m:
    rc, rs = reserve_m.group(1), reserve_m.group(2)
    return f"중단점 도달 (S{rs}/C{rc})", elapsed
if "즉시 멈춤 시행" in act_line or "즉시 완료 시행" in act_line:
    return "사용자멈춤", elapsed
# 그 외 act (작업 시작/계속/다음 Step) → 일반 작업멈춤
return "작업멈춤", elapsed
```

변경 요약:
- `"작업중 (→S/C)"` 반환 → `"중단점 도달 (S/C)"` 로 교체. 빈 문자열이던
  두 번째 반환값도 `elapsed` 로 설정되어 경과 시간 정상 표시.
- `"작업 시작/계속/다음 Step act"` → `"작업중"` 반환 분기 제거.
  fallback인 `"작업멈춤"` 으로 흡수.

### 2. 호출부 dead code 제거
**파일**: `DataTool_dev_code/DataTool_optRCD_proto_.py` (line 26255~26256 일대)

**Before** (14줄)
```python
if ch_path:
    status, elapsed_str = self._classify_paused_reason(ch_path)
    # 작업중(→S/C) 판정이지만 실제 중단점 도달 재검증
    # 조건: Reserve S/C == JSON Step/Cycle AND .cyc mtime > 1일
    if status.startswith("작업중 (→S"):
        _m = re.match(r"작업중 \(→S(\d+)/C(\d+)\)", status)
        if _m:
            _rs, _rc = _m.group(1), _m.group(2)
            _j_step = str(df.loc[ch_idx, "Step_No"]).strip() if "Step_No" in df.columns else ""
            _j_cycle = str(df.loc[ch_idx, "Current_Cycle_Num"]).strip() if "Current_Cycle_Num" in df.columns else ""
            if _rs == _j_step and _rc == _j_cycle:
                _cyc_dt = self._get_cyc_mtime(ch_path)
                if _cyc_dt and (datetime.now() - _cyc_dt).total_seconds() > 86400:
                    status = f"중단점 도달 (S{_rs}/C{_rc})"
                    elapsed_str = self._elapsed_str(
                        _cyc_dt.strftime("%Y/%m/%d %H:%M:%S"))
```

**After** (2줄)
```python
if ch_path:
    status, elapsed_str = self._classify_paused_reason(ch_path)
```

`_classify_paused_reason` 이 더 이상 `"작업중 (→S/C)"` 을 반환하지 않으므로
`startswith("작업중 (→S")` 분기는 도달 불가능 → 제거.

---

## 영향 범위

### 수정 대상
- 현황 탭 필터링 결과 (`filter_all_channels` → `_classify_paused_reason`)
- 전체 PNE 채널 일괄 재분류 (`_refine_paused_status` → 동일 함수)

### 동작 변화
| 케이스 | 이전 | 이후 |
|---|---|---|
| State=작업멈춤, Code=153, Code_Desc=작업멈춤종료, `.log` Paused 누락, Reserve 패턴 있음 | 🐛 `작업중 (→S/C)` + 경과 빈칸 | ✅ `중단점 도달 (S/C)` + act 기반 경과 |
| 동일 조건 + Reserve 없음 + 작업 시작/계속 act | 🐛 `작업중` | ✅ `작업멈춤` |
| 동일 조건 + Reserve 없음 + 즉시 멈춤 act | `사용자멈춤` (동일) | `사용자멈춤` (동일) |
| `.log` 에 `Paused` 기록 정상 | 영향 없음 (별도 분기) | 영향 없음 |

### 미수정 (향후 검토)
- `_get_cyc_mtime()` 정적 메서드는 현재 호출처 없음 (dead). 추후
  "마지막 스텝 소요시간 기반 중단점 판정" 기능에서 재활용 여지 있어
  이번 변경에서는 삭제 보류.
- `_read_log_tail` 은 최대 64KB 까지만 읽음. 매우 큰 `.log` 에서 `Paused`
  줄이 더 앞에 있는 경우는 본 변경이 모두 "중단점 도달/작업멈춤"
  으로 흘려보내므로 실사용상 문제 없음 (UX 일관성 유지).

### 검증 방법
1. **PNE1 ch36** 실제 환경에서 현황 탭·필터링 결과가
   `중단점 도달 (S80/C98)` 으로 표시되는지 확인.
2. `.log` 에 `Paused` 정상 기록된 다른 채널의 기존 표시가 변하지
   않았는지 확인 (예: 챔버이슈, 사용자멈춤 케이스).
3. `Code≠153` 작업멈춤 채널은 기존대로 `Code_Desc` 텍스트 + 경과시간
   표시되는지 확인 (분기 (3) 경로 무변).
