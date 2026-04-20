# 260420 현황 탭 상태 분류 v4 — JSON 1순위 + .log 참조 + CSV 교차검증

## 배경 / 목적

### 발단
같은 날짜 [260420_fix_classify_paused_missing_paused_log.md](260420_fix_classify_paused_missing_paused_log.md)
수정으로 PNE가 `.log` 에 Paused 이벤트를 기록하지 못한 케이스 (PNE1 ch36)는
해결됐으나, 사용자가 상태 판정 로직 전반에 다음 원칙을 적용할 것을 요청:

1. **JSON 1순위** — 채널 상태 대분류의 유일한 권위 소스는 JSON
  (`Module_N_channel_info.json` 의 State / Code / Code_Desc).
2. **.log 는 참조** — 세분 사유 판별에만 사용. JSON의 분류를 뒤집지 않음.
3. **.csv 교차검증** — `.log` 가 불완전/누락되는 PNE 펌웨어 버그를 대비해
  `Restore/*.csv` (SaveEndData) + `.cyc` mtime 으로 데이터 기록 실제 중단
  시점을 검증.

### 이전 로직의 한계
- **E9 케이스 미처리**: State=작업중 인데 Code=153 + Code_Desc=작업멈춤종료
  인 경우, 외부 분기가 State 만으로 판단 → `(C) 작업중` 분기로 흘러
  `작업중 (→S/C)` 표시. Code 가 이미 멈춤을 가리키고 있음에도 무시됨.
- **elapsed_str 공백**: `_classify_paused_reason` 이 fallback "작업멈춤" 반환
  시 두 번째 값이 `""`. 사용자는 "언제부터 멈춰있는지" 알 수 없음.
- **.csv 활용 전무**: 채널 데이터 기록 중단 시점을 확인할 1차 보조 소스인
  `Restore/SaveEndData.csv` 를 상태 분류에 전혀 사용하지 않음.

---

## 변경 내용

### 1. `_get_csv_mtime` — CSV mtime 조회 헬퍼 추가
**위치**: `DataTool_optRCD_proto_.py` (신규, `_get_cyc_mtime` 바로 아래)

```python
@staticmethod
def _get_csv_mtime(channel_path: str):
    """채널 폴더 내 Restore\\*.csv 중 최신 mtime → datetime | None."""
    try:
        if not os.path.isdir(channel_path):
            return None
        restore_path = os.path.join(channel_path, "Restore")
        if not os.path.isdir(restore_path):
            return None
        csv_files = [f.path for f in os.scandir(restore_path)
                     if f.name.lower().endswith('.csv') and f.is_file()]
        if not csv_files:
            return None
        newest = max(csv_files, key=os.path.getmtime)
        return datetime.fromtimestamp(os.path.getmtime(newest))
    except Exception:
        return None
```

### 2. `_crosscheck_elapsed` — CSV/CYC 통합 교차검증 헬퍼 추가
```python
@staticmethod
def _crosscheck_elapsed(channel_path: str) -> str:
    """.csv (Restore/) / .cyc mtime 중 최신 → 경과 문자열."""
    csv_dt = WindowClass._get_csv_mtime(channel_path)
    cyc_dt = WindowClass._get_cyc_mtime(channel_path)
    candidates = [dt for dt in (csv_dt, cyc_dt) if dt is not None]
    if not candidates:
        return ""
    best_dt = max(candidates)
    return WindowClass._elapsed_str(
        best_dt.strftime("%Y/%m/%d %H:%M:%S"))
```

### 3. `_classify_paused_reason` — 3개 fallback 경로에 CSV 교차검증 적용
- **tail=None** (`.log` 접근 실패/부재): `_crosscheck_elapsed` 호출
- **Case (ii) fallback** ("작업멈춤" 반환 시 elapsed 비어있으면): `_crosscheck_elapsed` 호출
- **tail 내 키워드 전무** (최종 fallback): `_crosscheck_elapsed` 호출

docstring 에 계층 명시:
```
입력 계층 (JSON-우선 원칙):
- 호출부가 JSON(State=작업멈춤 + Code=153)으로 '멈춤' 대분류 확정
- 본 함수는 .log를 *참조*하여 세분 사유 결정
- .log 불완전/누락 시 .csv(Restore/) 및 .cyc mtime으로 교차 검증
```

### 4. 외부 분기 재설계 — JSON Code 우선 (filter_all_channels)
**Before** (status 선분기, Code 후검사)
```python
if status in ("작업멈춤", "잠시멈춤"):
    if code == "153" and code_desc in (...):
        ...
    elif code_desc:
        ...
elif status in ("작업중", "충전", "방전", "진행", "휴지"):
    ...
```

**After** (Code 선분기 = JSON 1순위)
```python
# JSON 우선 추출 — status 분기 전에 Code/Code_Desc 확정
code = str(df.loc[ch_idx, "Code"]).strip() if "Code" in df.columns else ""
code_desc = str(df.loc[ch_idx, "Code_Desc"]).strip() if "Code_Desc" in df.columns else ""
is_paused_by_code = (
    code == "153" and code_desc in ("작업멈춤종료", "잠시멈춤"))

# (A) Code=153 + 작업멈춤종료/잠시멈춤 → State 무관 멈춤 확정
if is_paused_by_code:
    ch_path = self._build_channel_path(df, ch_idx, has_rpath, has_path)
    if ch_path:
        status, elapsed_str = self._classify_paused_reason(ch_path)
    else:
        status = "작업멈춤"
# (B) 작업멈춤/잠시멈춤 + Code != 153 → Code_Desc 그대로
elif status in ("작업멈춤", "잠시멈춤"):
    if code_desc:
        status = code_desc
    ch_path = ...
    if ch_path:
        elapsed_str = self._elapsed_from_log(ch_path)
        if not elapsed_str:
            elapsed_str = self._crosscheck_elapsed(ch_path)
# (C) 작업중/충전/방전/진행/휴지 → Reserve 정보 부가
elif status in ("작업중", "충전", "방전", "진행", "휴지"):
    ...
# (D) 완료/시험완료 → .log + CSV 교차검증 경과
if status == "완료" or _sb_tmp == "시험완료":
    ch_path = ...
    if ch_path:
        elapsed_str = self._elapsed_from_log(ch_path)
        if not elapsed_str:
            elapsed_str = self._crosscheck_elapsed(ch_path)
```

### 5. `_refine_paused_status` — 동일한 JSON 1순위 원칙 적용
마스킹 확장: State=작업멈춤/잠시멈춤 **OR** (Code=153 + Code_Desc 매칭) 중
하나라도 만족하면 처리 대상 (기존엔 State 만 체크).

---

## 상태 분류 예외 케이스 매트릭스 (v4)

| # | 예외 케이스 | 처리 방식 | v4 적용 |
|---|---|---|---|
| E1 | PNE `.log` Paused 누락 + Reserve 패턴 | Case (ii) Reserve → "중단점 도달" | ✅ |
| E2 | `.log` 접근 불가 (네트워크 끊김) | tail=None → CSV/CYC mtime fallback | ✅ (v4 신규) |
| E3 | tail 64KB 내 키워드 전무 | 최종 fallback → CSV/CYC mtime fallback | ✅ (v4 신규) |
| E4 | Test work completed | "시험완료" | ✅ 기존 |
| E5 | chamber alarm | "챔버이슈" | ✅ 기존 |
| E6 | 사용자 즉시 멈춤/완료 | "사용자멈춤" | ✅ 기존 |
| E7 | 정상 Paused + Reserve | "중단점 도달 (S/C)" | ✅ 기존 |
| E8 | Code≠153 기타 사유 | "작업멈춤 - {Code_Desc}" + CSV 보강 | ✅ (v4 보강) |
| **E9** | **State=작업중 + Code=153 모순** | **Code 우선 → 멈춤 분기** | ✅ **(v4 신규)** |
| E10 | `.log` 롤오버 / Paused 구파일 | E1/E3 경로로 흡수 | ✅ |
| E11 | `.log` 거대 파일 tail 외 Paused | E1/E3 경로로 흡수 | ✅ |
| E12 | Code_Desc 공백/변종 | `.strip()` 만 | ❌ 미처리 |
| E13 | 완료/시험완료 elapsed 누락 | `.log` → CSV 교차검증 | ✅ (v4 신규) |

---

## 영향 범위

### 수정 대상
- `WindowClass._get_csv_mtime` — **신규** static method
- `WindowClass._crosscheck_elapsed` — **신규** static method
- `WindowClass._classify_paused_reason` — 3개 fallback 경로 CSV 교차검증 추가
- `WindowClass._refine_paused_status` — JSON 1순위 마스킹 확장
- `WindowClass.filter_all_channels` — 외부 분기 재설계 (A/B/C/D)

### 동작 변화

| 시나리오 | v3 동작 | v4 동작 |
|---|---|---|
| State=작업멈춤, Code=153, `.log` Paused 없음, Reserve 있음 | "작업중 (→S/C)" | **"중단점 도달 (S/C)"** + elapsed |
| State=작업멈춤, Code=153, `.log` 접근 실패 | "작업멈춤" + elapsed 빈칸 | "작업멈춤" + **CSV/CYC mtime 기반 elapsed** |
| State=**작업중**, Code=153, Code_Desc=작업멈춤종료 | 🐛 "작업중 (→S/C)" | ✅ `_classify_paused_reason` 호출 → 세분 사유 |
| State=작업멈춤, Code=152 (통신에러) | "작업멈춤 - 통신에러" + `.log` mtime | "작업멈춤 - 통신에러" + `.log` mtime (실패 시 CSV fallback) |
| State=완료 | elapsed `.log` mtime | elapsed `.log` (실패 시 CSV fallback) |
| 기존 정상 Paused + Reserve 기록 케이스 | "중단점 도달 (S/C)" | "중단점 도달 (S/C)" (무변) |

### 주의사항
- **성능**: 채널당 최대 3회 추가 파일 시스템 접근 발생 가능
  (`Restore\` 디렉토리 존재 체크 + `scandir` + `getmtime`). 500채널 기준
  네트워크 드라이브에서 약 0.3~1초 증가 예상. 대부분 캐시 적중 시 무시 가능.
- **Restore 폴더 부재**: Toyo 또는 초기 PNE 채널은 `Restore/` 가 없을 수
  있음 → `_get_csv_mtime` 이 None 반환, `_crosscheck_elapsed` 가 `.cyc`
  단일 fallback 으로 자동 수렴.
- **E12 (Code_Desc 변종)**: 여전히 정확 일치 매칭. 실환경에서 변종 발견
  시 별도 이슈로 처리.

### 검증 방법 (사내 환경)
1. **PNE1 ch36**: `중단점 도달 (S80/C98)` + 경과시간(CSV 기반) 표시 확인.
2. **E9 검증**: State=작업중 + Code=153 인 채널이 있다면, 해당 채널이
  `중단점 도달`/`사용자멈춤`/`작업멈춤` 중 적절히 분류되는지.
3. **E2 검증**: 네트워크 드라이브 일시 끊김 시뮬레이션 시 elapsed_str
  이 `.csv`/`.cyc` mtime 에서 채워지는지.
4. **회귀**: 정상 Paused + Reserve 기록된 기존 "중단점 도달" 채널의
  표시가 그대로인지.
5. **회귀**: Toyo 채널 (Restore 폴더 없음) 이 v3 와 동일하게 표시되는지.

---

## 참고
- [260420_fix_classify_paused_missing_paused_log.md](260420_fix_classify_paused_missing_paused_log.md) — 본 변경의 전제(.log Paused 누락 버그 수정)
