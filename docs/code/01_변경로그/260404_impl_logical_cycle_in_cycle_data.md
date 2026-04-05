# 논리사이클 매핑을 사이클 데이터 파이프라인에 통합

- **날짜**: 2026-04-04
- **파일**: `DataTool_dev/DataTool_optRCD_proto_.py`
- **카테고리**: 기능추가

---

## 배경 / 목적

기존에 `pne_build_cycle_map()`과 `toyo_build_cycle_map()`으로 논리사이클 매핑(cycle_map)이 구현되어 있었으나,
**프로필 로딩**과 **UI 표시**에서만 사용되고 있었다. 핵심 사이클 데이터 처리 함수인
`pne_cycle_data()`와 `toyo_cycle_data()`는 cycle_map을 사용하지 않아, `NewData['Cycle']` 컬럼이
단순 순번(1, 2, 3...)으로만 부여되었다.

특히 **스윕 시험**(GITT, DCIR 등)에서는 다수의 물리 TotlCycle이 하나의 논리사이클로 그룹핑되어야 하므로,
기존의 TotlCycle 단위 처리로는 의미 있는 사이클 요약 데이터를 생성할 수 없었다.

## 변경 전 / 후 비교

### Before

```
pne_cycle_data() / toyo_cycle_data()
  → pivot by TotlCycle
  → dropna(Dchg, Chg)
  → Cycle = 순번 1, 2, 3, ...    (물리 TC와 무관한 재번호)
  → OriCyc = 물리 TotlCycle
  → cycle_map 없음
```

### After

```
pne_cycle_data() / toyo_cycle_data()
  → pne_build_cycle_map() / toyo_build_cycle_map() 호출 → cycle_map 생성
  → pivot by TotlCycle (기존과 동일)
  → dropna(Dchg, Chg)
  → cycle_map 기반 Cycle 번호 부여:
    ├─ 일반 시험: OriCyc → cycle_map 역매핑 → 논리사이클 번호
    └─ 스윕 시험: 같은 논리사이클의 행을 groupby 집계
  → OriCyc = 대표 물리 TotlCycle (유지)
  → df.cycle_map = {...} 저장
```

## 변경 상세

### 1. `_process_pne_cycleraw()` — cycle_map 파라미터 추가

```python
def _process_pne_cycleraw(
    Cycleraw, df, raw_file_path, mincapacity,
    chkir, chkir2, mkdcir,
    cycle_map=None,  # ← 추가
) -> None:
```

dropna 이후 Cycle 번호 부여 로직:

- **cycle_map 있음 + 스윕**: `_tc_to_ln` 역매핑 → groupby(논리사이클).agg() → Eff/Eff2 재계산
- **cycle_map 있음 + 일반**: `_tc_to_ln` 역매핑 → Cycle = 논리사이클 번호
- **cycle_map 없음**: 기존 방식 (순번 1, 2, 3, ...)

### 2. `pne_cycle_data()` — cycle_map 생성 및 전달

```python
_cycle_map, _ = pne_build_cycle_map(raw_file_path, mincapacity, ini_crate)
_process_pne_cycleraw(..., cycle_map=_cycle_map)
df.cycle_map = _cycle_map if _cycle_map else {}
```

### 3. `toyo_cycle_data()` — cycle_map 생성 및 저장

```python
_cycle_map, _ = toyo_build_cycle_map(raw_file_path, mincapacity, inirate)
# OriCyc → 논리사이클 역매핑으로 Cycle 번호 부여
df.cycle_map = _cycle_map if _cycle_map else {}
```

### 4. `unified_cyc_confirm_button()` — 논리사이클 로그 출력

데이터 로딩 완료 후 각 경로별 cycle_map 요약을 콘솔에 출력:
```
논리사이클: path0 [M01Ch001[001]]  일반  758개 논리사이클
```

## 영향 범위

| 함수 | 변경 내용 |
|------|----------|
| `_process_pne_cycleraw()` | `cycle_map` 파라미터 추가, Cycle 번호 재정의 로직 변경 |
| `pne_cycle_data()` | cycle_map 생성/전달/저장 |
| `toyo_cycle_data()` | cycle_map 생성/저장, Cycle 번호 재정의 |
| `unified_cyc_confirm_button()` | 논리사이클 로그 출력 추가 |
| `df.NewData['Cycle']` | 순번 → 논리사이클 번호 (cycle_map 있을 때) |
| `df.cycle_map` | 새 속성: 논리사이클 매핑 딕셔너리 |

## 주의사항

- **하위 호환성**: cycle_map이 없거나 빈 경우 기존 동작(순번) 유지
- **스윕 집계**: Dchg/Chg은 합산, Eff/Eff2는 집계 후 재계산, DCIR은 평균
- **OriCyc 보존**: 전압 트래킹(ChgVolt, DchgVolt) 등 기존 코드는 OriCyc 기반이므로 영향 없음
- **성능**: `pne_build_cycle_map()`은 SaveEndData 캐시를 사용하므로 추가 I/O 최소화
