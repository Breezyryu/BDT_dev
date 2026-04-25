# Toyo `Cycle` 컬럼이 step 단위 그대로 — 논리사이클 매핑 적용

날짜: 2026-04-25
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수: `toyo_cycle_data()` (L4300+)

## 배경

사용자 보고:
> Toyo raw 사이클은 step별로 카운팅 되기 때문에 사이클 전처리를 기존에 했었다. 지금 출력된 플랏은 전처리가 안된 것 같아

로그에서 확인:
```
[Toyo] 250219_..._101-200cyc  총 104cyc  ...  maxTC=496
[Toyo] 250304_..._201-300cyc  총 102cyc  ...  maxTC=498
[Toyo] 250317_..._301-400cyc  총 102cyc  ...  maxTC=498
논리사이클: path4 [30]  일반  104개 논리사이클
논리사이클: path5 [30]  일반  102개 논리사이클
논리사이클: path6 [30]  일반  102개 논리사이클
```

- Toyo TotlCycle 은 **step 단위 카운팅** (한 사이클 = 다단 충전 4 + 방전 2 + Rest 등 약 5 step → maxTC ≈ 5×사이클수)
- Phase 0 메타에서는 `총 104cyc / maxTC=496` 으로 둘 다 정상 산출되지만,
- 그래프 x축(`Cycle` 컬럼)은 `maxTC` 값 (step 단위) 그대로

## 원인

`toyo_cycle_data` (L4300-4305):

```python
# Before
if len(df.NewData) > 0:
    # TC 1원화: OriCyc(TC)를 Cycle로 사용
    if 'OriCyc' in df.NewData.columns and df.NewData['OriCyc'].notna().any():
        df.NewData.insert(0, "Cycle", df.NewData['OriCyc'].astype(int).values)
    else:
        df.NewData.insert(0, "Cycle", range(1, len(df.NewData) + 1))
```

- `cycle_map` 은 **L4295 에서 `toyo_build_cycle_map`** 으로 정상 생성
- **하지만 `Cycle` 컬럼에는 매핑 적용 안 함** — `OriCyc` 그대로 사용
- `OriCyc` = 원본 `TotlCycle` = **step 단위 TC** (한 사이클 안에 다단 step 마다 증가)

PNE 의 `_process_pne_cycleraw` (L9791+) 에는 동일한 cycle_map 매핑 로직이 들어있지만, **Toyo 에는 누락**된 상태.

## 수정

PNE 패턴을 Toyo 에 동일 적용 (value 형식 차이 흡수: dict / tuple / int):

```python
# After
if len(df.NewData) > 0:
    _cycle_assigned = False
    if _cycle_map and 'OriCyc' in df.NewData.columns:
        # TC → 논리사이클 역매핑
        _tc_to_ln: dict[int, int] = {}
        _is_sweep = False
        for _ln, _tc_val in _cycle_map.items():
            if isinstance(_tc_val, dict) and 'all' in _tc_val:
                _s, _e = _tc_val['all']
                if _s != _e:
                    _is_sweep = True
                for _t in range(int(_s), int(_e) + 1):
                    _tc_to_ln[_t] = _ln
            elif isinstance(_tc_val, (tuple, list)) and len(_tc_val) == 2:
                _s, _e = _tc_val
                if _s != _e:
                    _is_sweep = True
                for _t in range(int(_s), int(_e) + 1):
                    _tc_to_ln[_t] = _ln
            elif isinstance(_tc_val, (int, np.integer)):
                _tc_to_ln[int(_tc_val)] = _ln
        if _tc_to_ln:
            _logical_col = df.NewData['OriCyc'].astype(int).map(_tc_to_ln)
            if _logical_col.notna().any():
                df.NewData.insert(0, "Cycle",
                                  _logical_col.fillna(0).astype(int).values)
                _cycle_assigned = True
    if not _cycle_assigned:
        # 폴백: cycle_map 없거나 매핑 실패 → OriCyc 그대로
        if 'OriCyc' in df.NewData.columns and df.NewData['OriCyc'].notna().any():
            df.NewData.insert(0, "Cycle", df.NewData['OriCyc'].astype(int).values)
        else:
            df.NewData.insert(0, "Cycle", range(1, len(df.NewData) + 1))
```

### Toyo cycle_map value 형식 가정
`toyo_build_cycle_map` 결과는 다음 중 하나:
- `int` (단일 TC) — 일반 시험 1:1 매핑
- `tuple/list (시작TC, 끝TC)` — 다단 step 묶음
- `dict { 'all': (시작, 끝), ... }` — PNE 호환 형식 (혹시 모를 경우)

세 형식 모두 처리해 안전하게 매핑.

## 동작 변화

| 사용자 데이터 | OriCyc (step) | Before (Cycle) | **After (Cycle)** |
|---|---|---|---|
| Q7M 101-200cyc | 1..496 | **1..496** (step) | **1..104** (논리) |
| Q7M 201-300cyc | 1..498 | **1..498** (step) | **1..102** (논리) |
| Q7M 301-400cyc | 1..498 | **1..498** (step) | **1..102** (논리) |

연결처리 모드 (각 path Cycle 누적 오프셋, 커밋 `f14df25`) 와 결합 시:
- Before: 1..496 → 누적 1..1492 (step 단위, 의미 없음)
- After: 1..104 → 누적 1..308 (논리사이클, 정확)

## 영향 범위

- `toyo_cycle_data` 의 Cycle 컬럼 부여 부분 (5줄 → 약 30줄)
- PNE 경로 (`_process_pne_cycleraw`) 는 불변 (이미 동일 매핑 적용 중)
- df.NewData['OriCyc'] 자체는 step 단위 TC 그대로 보존 → 엑셀 출력의 OriCyc 열에는 원본 step 번호 표기 (디버깅용)
- `_save_cycle_excel_data` 는 OriCyc 열로 시트 작성 → 엑셀 row 인덱스에는 step 단위 표시되지만 그래프 표시는 논리사이클 (정상)

## 검증 포인트

- [ ] 사용자 케이스 (Q7M 101-200/201-300/301-400) 사이클 분석
- [ ] Toyo 단독 → 그래프 x축 1..104 (step 단위 1..496 아님)
- [ ] 연결처리 모드 → 누적 1..308
- [ ] PNE (Q8, T23) 회귀 없음 — 기존과 동일 매핑
- [ ] Toyo + PNE 혼합 통합 모드 → 두 cycler 모두 논리사이클 단위
- [ ] cycle_map 생성 실패 시 폴백 정상 (step 단위로라도 표시됨)

## 관련

- 커밋 `f14df25` 연결처리 Cycle 누적 오프셋 — 이 수정 후 Toyo 도 논리사이클 단위 누적이 됨 → 의미 일치
- 사이클 서브탭 일련 작업 (`3c819e7` ~ `2085ae5`) 이후 발견된 별개 이슈
