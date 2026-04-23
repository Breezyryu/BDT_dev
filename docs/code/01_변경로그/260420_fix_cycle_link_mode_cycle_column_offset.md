# 연결처리 모드에서 사이클 x축이 중첩되는 문제 수정

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수: `unified_cyc_confirm_button` 연결 모드 병합 블록 (L21138+)

## 배경 / 문제

사용자 보고:
> 경로 테이블에 T23_1 / T23_2 / T23_3 (동일 채널 M02Ch073, 각각 TC 601/402/1002) 를
> 그룹으로 입력하고 "연결처리" 체크 후 사이클 분석 실행 시,
> **사이클 데이터가 연결이 안되는 문제** (그래프 x축에서 각 path 가 1부터 시작해 중첩).

로그에서도 각 path 가 **독립 매핑**됨이 확인:
```
논리사이클: path1 [M02Ch073[073]]  일반  601개
논리사이클: path2 [M02Ch073[073]]  일반  402개
논리사이클: path3 [M02Ch073[073]]  일반  1002개
```

## 원인

연결 모드 병합 블록 (L21143-21150) 은 **row `index`** 에만 누적 오프셋 적용:

```python
# Before
writerowno = st['offset'] + st['last_len']
cyctemp[1].NewData.index = cyctemp[1].NewData.index + writerowno   # 엑셀 연속 저장용 index 오프셋만
st['offset'] = writerowno
st['last_len'] = len(cyctemp[1].NewData)
```

`df.NewData['Cycle']` 컬럼 (각 path 내 원본 TC 값) 은 **수정하지 않았다**. 한편 `graph_output_cycle` (L3051-3054) 는 x축으로 `Cycle` 컬럼을 사용:

```python
if 'Cycle' in df.NewData.columns:
    _x = df.NewData['Cycle'].values
else:
    _x = df.NewData.index.values
```

- path1 Cycle: 1~601
- path2 Cycle: 1~402
- path3 Cycle: 1~1002

→ 세 곡선이 **x ∈ [1, 402]** 구간에서 완전 중첩, 연결 시 기대인 1~2005 연속 표시가 되지 않음.

추가로 `OriCyc` (엑셀 "Rest End"/"방전용량" 등 시트의 사이클 번호 열) 도 동일하게 원본값 유지라 저장본도 연결 의도와 불일치.

## 수정

연결 모드 블록에서 `Cycle`/`OriCyc` 컬럼에도 **누적 오프셋** 적용. 동시에 캐시 오염 방지를 위해 `NewData.copy()` 후 수정.

```python
# After
if sub_label not in channel_state:
    channel_state[sub_label] = {
        'offset': 0, 'last_len': 0,
        'cycle_offset': 0,   # Cycle/OriCyc 누적 오프셋 (신규)
    }
st = channel_state[sub_label]
writerowno = st['offset'] + st['last_len']
# 캐시 오염 방지: 원본 NewData 는 건드리지 않고 복사본에만 오프셋 적용
_nd_link = cyctemp[1].NewData.copy()
_nd_link.index = _nd_link.index + writerowno
# Cycle/OriCyc 에 누적 오프셋 적용 → 그래프 x축 이어붙이기
_co = st['cycle_offset']
if _co > 0:
    if 'Cycle' in _nd_link.columns:
        _nd_link['Cycle'] = _nd_link['Cycle'].astype(int) + _co
    if 'OriCyc' in _nd_link.columns:
        _nd_link['OriCyc'] = _nd_link['OriCyc'].astype(int) + _co
# 다음 path 를 위해 누적 최대 Cycle 갱신
if 'Cycle' in _nd_link.columns and len(_nd_link) > 0:
    st['cycle_offset'] = int(_nd_link['Cycle'].max())
elif len(_nd_link) > 0:
    st['cycle_offset'] = _co + len(_nd_link)
st['offset'] = writerowno
st['last_len'] = len(_nd_link)
# merged 와 엑셀 저장에 모두 _nd_link (오프셋 적용 복사본) 사용
merged[sub_label]['frames'].append(_nd_link)
if self.saveok.isChecked() and save_file_name:
    self._save_cycle_excel_data(_nd_link, writecolno, writerowno, headername)
```

### 누적 예시 (사용자 T23 그룹)

| path | 원본 Cycle | 오프셋 (_co) | 적용 후 Cycle | 다음 오프셋 |
|---|---|---|---|---|
| T23_1 | 1..601 | 0 | 1..601 (불변) | 601 |
| T23_2 | 1..402 | 601 | **602..1003** | 1003 |
| T23_3 | 1..1002 | 1003 | **1004..2005** | 2005 |

Toyo Q7M (101-200/201-300/301-400) 도 동일 패턴으로 누적.

### 캐시 오염 방지

기존 코드 `cyctemp[1].NewData.index = ... + writerowno` 는 **원본 객체를 직접 수정**해 channel 캐시가 오염될 수 있던 잠재 버그. `.copy()` 후 복사본에만 수정하도록 변경 — 부수 효과 제거.

## 동작 변화

| 항목 | Before | After |
|---|---|---|
| 단일 path 그룹 (Q8 등) | 정상 | 불변 (연결 모드 블록 미진입) |
| 연결 모드, row index 오프셋 | 적용 | 적용 (불변) |
| 연결 모드, Cycle 컬럼 오프셋 | **미적용** → 그래프 중첩 | **적용** → x축 연속 |
| 연결 모드, OriCyc 컬럼 오프셋 | 미적용 → 엑셀 OriCyc 중복 | 적용 → 엑셀 OriCyc 누적 |
| 캐시 `cyctemp[1].NewData` 원본 | index 오염 가능 | copy 로 원본 보존 |

## 영향 범위

- 연결 모드 그룹 내부 block (L21138-21170) 국한. **비연결 모드 / 단일 path 경로에는 영향 없음**
- 엑셀 저장: 연결 모드 시 한 채널의 여러 path 가 세로로 이어서 기록되는 기존 동작은 유지. OriCyc 열에는 누적값이 들어감
- `_load_all_cycle_data_parallel` / Phase 3 리매핑 등 상류 로직 변경 없음

## 검증 포인트

- [ ] T23_1/2/3 그룹 (동일 채널 M02Ch073, 각각 601/402/1002 cy) 연결처리 후 사이클 분석
- [ ] 탭1 그래프 x축이 **1 ~ 2005** 연속, 세 구간이 끊기지 않고 한 곡선
- [ ] 탭2 (Step 3 완료) 도 동일하게 연결된 x축
- [ ] Q7M 101-200/201-300/301-400 (Toyo) 도 Cycle 연결 확인
- [ ] Q8 ATL (단일 path) 는 기존과 동일 (연결 블록 미진입)
- [ ] `saveok` 체크 시 엑셀의 "방전용량"/"Rest End"/"Rest End Chg" 등 모든 시트의 OriCyc 열이 **누적 Cycle** 로 기록
- [ ] 같은 경로를 재분석 시 캐시에서 가져온 값이 오염되지 않음 (1차 실행 결과와 2차 실행 결과 동일)

## 잠재적 엣지

- 각 path 의 Cycle 이 이미 연속(예: T23_2 가 파일에 602-1003 으로 저장됐다면) 이면 오프셋 적용으로 **이중 증가** 위험. 현재 사용자 데이터는 각 파일이 1부터 시작하는 구조로 로그 확인됨 ("601/402/1002개") — 이 경우 이중 증가는 문제 아님
- 미래에 파일 자체가 이미 연속 누적된 데이터를 사용하게 되면 연결처리 체크 해제 권장 or 별도 옵션 필요

## 관련

- 사이클 서브탭 확장 Step1~4 완료 (`9ed12a0`) 이후 연결 모드 이슈 별도 발견
- 이번 수정으로 연결처리 + 서브탭 2개 모두에서 x축 연속성 확보
