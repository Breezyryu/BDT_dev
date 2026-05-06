# 프로파일 부분 TC 선택 렌더링 + 진단 메시지 개선

날짜: 2026-05-05
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수:
- `_diagnose_empty_filter` (신규, L1985 근처) — scope 미스매치 진단 헬퍼
- `_unified_filter_condition` (L2236 직후) — scope 미스매치 raw 폴백
- `_unified_process_single_cycle_from_raw` (L3221) — 진단 메시지 활용
- `unified_profile_core` (L2991) — 진단 메시지 활용

## 배경 — 사용자 보고

`260226_260228_05_문현규_3876mAh_PS 연속저장 DCIR` 에서 일부 TC 만 선택해 프로파일 분석을 돌리면 다음과 같은 경고가 반복:

```
TC3   : [plot skip] 데이터 없음: M01Ch024[024] — 필터 후 데이터 없음
TC4   : 방전 DCIR (정상 출력)
TC5-19: [plot skip] 데이터 없음: M01Ch024[024] — 필터 후 데이터 없음
```

**1차 보고**: "TC를 전체 구간하면 잘 출력되는데 일부 TC 선택 후 프로파일 분석하면 데이터 없음 문제 지속 발생"
**2차 보고 (재테스트 후)**: "여전히 TC 별도 구현 안됨" — 부분 TC 선택 시 TC 들이 개별 탭으로 그려지지 않음.

## 원인 분석

### 데이터 패턴 (PS 연속저장 DCIR 예시)

| TC | 내용 | Cond 분포 |
|----|------|-----------|
| 1, 2 | 형성 (CHG+DCHG) | {1, 2, 3} |
| 3 | SOC 세팅 (CHG only) | {1, 3} |
| 4 | 방전 DCIR pulse | {2, 3} |
| 5-19 | 저장 휴지 | {3} only |

### 흐름 (1차 패치 전)

`260504 PR-1 (Layer A 단일화)` 이후 raw 단계는 cond 무관 모든 TC 를 로딩. scope 별 row 필터링은 Stage 3 (`_unified_filter_condition`) 에 위임. 사용자가 `data_scope='discharge'` 로 분석 시:

- TC3 raw = `{1, 3}` → discharge 필터에서 cond=2 부재 → 비어짐 → "필터 후 데이터 없음"
- TC4 raw = `{2, 3}` → discharge 필터 통과 → plot 정상
- TC5-19 raw = `{3}` only → discharge 필터에서 cond=2 부재 → 비어짐 → "필터 후 데이터 없음"

전체 구간으로 돌리면 TC1, 2, 4 가 동작해 "잘 출력" 으로 인식. 일부 TC 만 돌리면 빈 탭 비율이 높아 "지속 발생" 으로 체감.

### 1차 패치의 한계

진단 메시지만 추가했더니 ("`방전 스텝 없음 (휴지만 존재) — '사이클' 스코프 + '휴지 포함' 권장`") 사용자가 옵션 변경 가이드는 받았지만, 결국 **데이터가 안 그려지는 게 본질 문제**. 사용자 입장: "내가 명시적으로 선택한 TC 인데 왜 안 보여?"

## 변경 요약

### 1. raw 폴백 (`_unified_filter_condition`)

scope 필터 결과가 empty 인데 raw 에 데이터가 있으면, 모든 active+rest cond 를 보존하는 폴백을 적용.

```python
filtered = df.loc[final_mask].copy()  # 기존

# scope 미스매치 폴백 — 사용자 명시 TC 선택 보존
if filtered.empty and len(df) > 0:
    if df["Condition"].isin([1, 2, 3]).any():
        filtered = df[df["Condition"].isin([1, 2, 3])].copy()
        _perf_logger.info(
            f"  [filter] {data_scope} scope 결과 empty + raw 데이터 존재 → "
            f"all-cond 폴백 적용 ({len(filtered)} rows). "
            f"사용자 명시 TC 선택 보존."
        )
```

이로써:
- TC5-19 (휴지만 존재) → 폴백으로 휴지 데이터 표시 → V vs 시간 (또는 SOC 등) 그려짐
- TC3 (충전만 존재) in discharge scope → 폴백으로 충전 데이터 표시 → degenerate SOC 이지만 V 곡선 가시화

다운스트림 영향:
- `_unified_normalize_pne/_toyo`: cond 별 분기 없이 단순 단위 변환 → 영향 없음.
- `_unified_merge_steps` cycle 분기: ChgCap/DchgCap ffill 로직이 휴지 데이터도 적절히 처리 → 영향 없음.
- `_unified_calculate_axis`: 휴지 only 데이터에서 SOC 가 상수 (chg 가 없으면 ChgCap 변화 없음) — V vs SOC 가 수직선 형태로 degenerate 하지만 표시는 됨. axis_mode='time' 에서는 정상.
- `_unified_calculate_dqdv`: NaN 초기화 + diff 분모 보호 → degenerate 케이스에서도 안전.

### 2. 진단 메시지 헬퍼 (`_diagnose_empty_filter`)

폴백을 적용해도 정말 데이터가 한 row 도 없는 edge case 에서 사용. raw 에 cond 분포가 있을 때 어떤 토글이 부족한지 알려준다.

| raw 내용 | scope | 메시지 예시 |
|----------|-------|-------------|
| {1, 3} | discharge | `방전 스텝 없음 (충전 + 휴지만 존재) — '사이클' 스코프 권장` |
| {3} only | cycle, include_rest=False | `휴지 스텝만 존재 — '휴지 포함' 옵션 ON 필요` |
| {9} only | * | `<scope> 데이터 없음 (Current 부호 인식 실패)` |
| 분석 불가 | * | `필터 후 데이터 없음` (기존 문구 폴백) |

폴백이 동작하면 메시지는 거의 나오지 않지만, 안전망 역할로 유지.

### 3. 진단 메시지 적용 (호출 지점 2곳)

`_unified_process_single_cycle_from_raw` (PNE chunk-기반 batch 경로) 와 `unified_profile_core` (단일 사이클 경로) 의 empty 분기에서 새 헬퍼 호출:

```python
# Before
metadata={"cycle": cycle_val, "error": "필터 후 데이터 없음"}

# After
_err = _diagnose_empty_filter(raw_cycle, _data_scope_pipe, _include_rest_pipe)
metadata={"cycle": cycle_val, "error": _err}
```

## 효과 — 사용자 시나리오

### Before (1차 패치도 적용 전)
```
TC3 : [plot skip] 데이터 없음 — 필터 후 데이터 없음
TC5-19 : [plot skip] 데이터 없음 — 필터 후 데이터 없음
```
사용자: 빈 탭만 보임. 데이터 자체가 안 나옴.

### After (이번 패치 적용)
- TC3, TC4, TC5-19 모두 **개별 탭으로 렌더링됨**
- TC3: 충전 프로파일 표시 (discharge scope 라도 충전 곡선 가시화)
- TC4: 방전 DCIR (정상)
- TC5-19: 휴지 voltage 변화 표시 (저장 중 V 변화)

scope 별 SOC 축이 일부 degenerate (예: discharge scope 에서 충전만 있는 TC 의 SOC 는 상수) 하지만, V/Time 트렌드는 항상 보임.

## 변경하지 않은 것 (의도적)

1. **scope 의 의미 자체는 그대로** — 사용자가 명시한 scope 의 SOC 축 정의를 따르되, 데이터가 부족하면 자연스럽게 degenerate 해진다. scope 를 자동 변경하지 않음 (사용자 의도 존중).
2. **CV 제거 / 보충전 필터** — 기존 동작 유지.
3. **cycle_map 구조** — sweep grouping 유지 (별도 리팩터링 영역).

## 호환성

- 정상 case (필터 결과 non-empty): 폴백 분기에 들어가지 않으므로 영향 없음.
- 기존 "필터 후 데이터 없음" 으로 빈 탭이 보이던 case: 이제 데이터가 그려진다 (사용자 요청 반영).
- 빈 탭을 의도적으로 활용하던 워크플로우 (있다면): 옵션 토글로 정확히 제어 가능 (cycle scope + include_rest 등).

## 관련 별건 (이번 PR 범위 밖)

- `251209_..._율별방전Profile`: TC2-6 → 현재 `RPT (0.2C 충방전)` 으로 분류. 정확히는 `0.2C 충전 - 율별 방전`.
- `251002_..._RatedCh half ca 4.19mAh SDI`: TC3-6 → 현재 `RPT`. 정확히는 `율별 충전 - 0.2C 방전`.

→ multi-TC 패턴 분석 (chg_crate vs dchg_crate 비교) 으로 별 PR 처리 예정.

## 검증 방법 (사용자)

1. **이 패치를 main 으로 머지** — 현재는 worktree (`stoic-agnesi-bd7997`) 에만 있음:
   ```
   git checkout main
   git pull
   # 또는 worktree 의 변경을 main 으로 cherry-pick
   ```
2. `260226_260228_05_문현규_3876mAh_PS 연속저장 DCIR` 경로 입력
3. 프로파일 분석 — TC=`3, 4, 5-19` (어떤 scope 으로도 무방)
4. 출력에서 TC3, TC4, TC5-19 모두 별도 탭으로 그려지는지 확인
5. 로그에서 `[filter] ... all-cond 폴백 적용 ...` 메시지 (옵션) 확인

## 검증 방법 (회귀)

기존 정상 동작 case: 필터가 non-empty 결과를 반환하므로 폴백 분기에 들어가지 않음 → 영향 없음.

검증 명령:
```
python tools/test_code/hysteresis_render_decision_validator.py  # 49/49 PASS 유지 확인
```

## 후속 작업 — 사용자 적용 가이드

이 패치는 worktree `stoic-agnesi-bd7997` 에 있다. 사용자가 main 에서 테스트 중이라면:

```bash
# 옵션 A: worktree commit 을 main 에 cherry-pick
cd c:\Users\Ryu\battery\python\BDT_dev
git fetch
git cherry-pick <worktree-commit-sha>

# 옵션 B: 패치 파일 적용
cd c:\Users\Ryu\battery\python\BDT_dev\.claude\worktrees\stoic-agnesi-bd7997
git format-patch -1 HEAD
cd c:\Users\Ryu\battery\python\BDT_dev
git am < ../path/to/patch.patch
```

또는 main 으로 가서 `_unified_filter_condition` 의 line 2236 직후 + `_diagnose_empty_filter` 헬퍼 + 두 caller 의 error 메시지 부분만 수동 반영해도 된다.
