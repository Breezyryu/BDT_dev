# ECT Rest 포함 옵션 — CHG/DCHG 직후 Rest 만 선별

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수: `pne_Profile_continue_data()` (L9698)

## 배경 / 문제

사용자 보고:
> "rest 가 DCH, CHG 바로 뒤만 포함하면 된다. 현재는 해당 사이클의 모든 Rest 가 출력된다."

직전 커밋 (35d6ac6, `260420_ect_rest_use_checkbox.md`) 에서 체크박스로 Rest 포함 여부를 전환했지만, 필터 구현이 단순 `isin([9, 1, 3])` 였던 탓에 **같은 사이클 내 모든 Rest 스텝**이 포함됨 (방전 후 Rest 도 섞임).

### 기대 동작
- `CHG` + Rest 체크 → 충전 스텝 + **충전 직후** Rest 만
- `DCHG` + Rest 체크 → 방전 스텝 + **방전 직후** Rest 만

## 원인

PNE 패턴 한 사이클의 StepType 시퀀스 예:
```
StepType: 1 → 3 → 2 → 3 → 8 → 1 → 3 → 2 → 3 → 8 ...
         (충전)(Rest1)(방전)(Rest2)(loop) ...
```

기존 필터:
```python
_types = [9, 1] + [3]  # CHG + Rest
Profileraw[2].isin(_types)
```

`isin` 만으로는 Rest1(충전 직후) 과 Rest2(방전 직후) 를 구분할 수 없어 둘 다 포함됨.

## 도메인 근거

- **충전 직후 Rest** = OCV relaxation → SEI / Li 분포 안정화 관찰
- **방전 직후 Rest** = OCV recovery → 분극 완화 관찰

CHG 모드에서 "방전 후 Rest" 는 방전 데이터 자체가 없어 맥락이 맞지 않음. ECM / PyBaMM 피팅 입력으로도 무의미. 사용자 기대와도 어긋남.

## 수정

"직전 step 이 요청 타입(1 or 2) 인 Rest 스텝" 만 선별하도록 변경.

```python
if _cd in ("CHG", "DCH", "DCHG"):
    _want_type = 1 if _cd == "CHG" else 2
    _type_mask = Profileraw[2].isin([9, _want_type])
    if include_rest:
        # StepType 연속 그룹으로 step ID 생성
        _is_boundary = Profileraw[2] != Profileraw[2].shift(1)
        _step_id = _is_boundary.cumsum()
        # 각 step 의 대표 StepType
        _step_rep = Profileraw.groupby(_step_id)[2].first()
        # 행 단위로 직전 step 의 StepType 매핑
        _prev_type = _step_id.map(_step_rep.shift(1))
        # 직전이 CHG/DCHG 인 Rest 만
        _rest_after = (Profileraw[2] == 3) & (_prev_type == _want_type)
        _type_mask = _type_mask | _rest_after
    Profileraw = Profileraw.loc[
        (Profileraw[27] >= inicycle) & (Profileraw[27] <= endcycle) & _type_mask]
```

### 핵심 아이디어
1. `_is_boundary = Profileraw[2] != Profileraw[2].shift(1)` — StepType 이 바뀌는 지점
2. 누적합 `.cumsum()` 으로 step-wise ID 부여
3. `groupby(step_id).first()` 로 각 step 의 StepType 대표값
4. `.shift(1)` 로 직전 step 의 StepType
5. `step_id.map(...)` 으로 각 행에 직전 step 타입 매핑
6. `(StepType == 3) & (prev == _want_type)` 으로 "직전이 원하는 타입인 Rest" 선별

### 동작 검증 (시퀀스 예)

| Step | StepType | step_id | step_rep | prev | _type_mask (CHG+Rest) | 결과 |
|---|---|---|---|---|---|---|
| 1 | 1 (충전) | 1 | 1 | NaN | ✅ (1 in [9,1]) | 포함 |
| 2 | 3 (Rest) | 2 | 3 | 1 | ✅ (rest_after) | **포함** |
| 3 | 2 (방전) | 3 | 2 | 3 | ❌ | 제외 |
| 4 | 3 (Rest) | 4 | 3 | 2 | ❌ (prev≠1) | **제외** |
| 5 | 8 (loop) | 5 | 8 | 3 | ❌ | 제외 |
| 6 | 1 (충전) | 6 | 1 | 8 | ✅ | 포함 |
| 7 | 3 (Rest) | 7 | 3 | 1 | ✅ | **포함** |
| 8 | 3 (Rest) | 7 | 3 | 1 | ✅ (같은 step 이라 동일 prev) | 포함 |

→ 충전 + 충전 직후 Rest 만 정확히 남음. 방전 후 Rest (Step 4) 는 제외.

### 경계 케이스
- **범위 시작 직후 Rest**: `prev` 가 범위 이전 step 의 StepType. 범위 밖 데이터가 Profileraw 에 없다면 NaN 으로 계산되어 제외됨. 범위 밖 데이터가 있다면 정상 판정.
- **첫 스텝이 Rest**: `prev = NaN` → NaN == _want_type 은 False → Rest 제외. 안전.

## 영향 범위

- `pne_Profile_continue_data()` CHG/DCHG 분기 로직 변경 (~12줄 추가)
- `include_rest=False` 일 때 동작은 이전 세션과 완전 동일
- `CYC`/`Cycle`/`GITT` 경로 영향 없음
- Toyo ECT path 영향 없음 (PNE 전용)

## 검증 포인트

- [ ] `CHG` + Rest 체크 → 충전 스텝 + 충전 직후 Rest **만** 플롯. 방전 후 Rest 없음
- [ ] `DCHG` + Rest 체크 → 방전 스텝 + 방전 직후 Rest 만 플롯. 충전 후 Rest 없음
- [ ] `CHG` + Rest 해제 → 충전 스텝만 (기존 동작)
- [ ] 다중 사이클 범위 (예: TC 10-15) 에서도 각 사이클 별로 동일 규칙 적용
- [ ] 범위 경계 (시작 TC 의 첫 step 이 Rest 인 경우) 에서 Rest 가 우연히 포함되지 않음
- [ ] `ect_saveok` CSV 출력 데이터가 필터된 결과 그대로

## 관련 변경로그

- `260420_ect_rest_use_checkbox.md` — Rest 체크박스 방식 도입 (직전 커밋)
- `260420_fix_ect_path_profile_always_override.md` — ECT 체크 시 항상 ECT 핸들러 위임
