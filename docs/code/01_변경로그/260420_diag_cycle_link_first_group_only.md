# 연결처리 "첫 경로그룹만 plot" 이슈 진단 로그 추가

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`

## 배경

사용자 보고:
> 아래 연결처리 시, 첫번째 경로그룹만 plot 이 출력된다.
> (경로 테이블에 3 그룹: Q8 / Gen4 T23 3경로 / ATL Q7M 3경로)

로그상 `paths=7` 로 데이터 로딩은 모두 성공, 그러나 **결과 탭에 첫 그룹만 반영**. 원인 추적을 위해 `unified_cyc_confirm_button` 내부의 **folder_groups 구성 + tab_units 할당** 요약 로그 추가.

## 변경 내용

### 1. folder_groups 요약 (L20853+)

```python
_perf_logger.info(
    f'  [탭생성] mode={_mode_s}  excel_groups={...}  folder_groups={...}')
for _gi, _g in enumerate(folder_groups):
    _perf_logger.info(
        f'    group#{_gi}  name={_g.name!r}  '
        f'paths={len(_g.paths)}  is_link={_g.is_link}  '
        f'file_idx={_g.file_idx}')
```

기대 로그 (3 그룹):
```
[탭생성] mode=통합 or 개별  excel_groups=0  folder_groups=3
  group#0  name='Q8 ATL...'  paths=1  is_link=False  file_idx=0
  group#1  name='Gen4'       paths=3  is_link=True   file_idx=1
  group#2  name='ATL Q7M...' paths=3  is_link=True   file_idx=2
```

### 2. tab_units 구성 (L21080+)

```python
for _ti, _gi_list in enumerate(tab_units):
    _names = [folder_groups[_gi].name for _gi in _gi_list]
    _perf_logger.info(
        f'    tab_unit#{_ti}  group_indices={_gi_list}  names={_names}')
```

기대 로그:
- 개별 모드: `tab_unit#0 [0] ['Q8...']`, `tab_unit#1 [1] ['Gen4']`, `tab_unit#2 [2] ['ATL Q7M...']`
- 통합 모드: `tab_unit#0 [0, 1, 2] ['Q8...', 'Gen4', 'ATL Q7M...']`

### 3. 탭 루프 시작 (L21096+)

```python
_perf_logger.info(
    f'  [탭 {tab_idx + 1}/{total_tabs}] 시작 — group_indices={group_indices}')
```

각 tab_idx 진입 여부를 확인 → 루프가 어디서 끊기는지 파악.

## 진단 시나리오

사용자 재실행 후 로그에서:

| 로그 패턴 | 원인 |
|---|---|
| `folder_groups=1` (3이어야 하는데) | `_parse_cycle_input` 에서 그룹 분리 실패 (빈 행 감지 문제?) |
| `folder_groups=3` + 통합 모드 `tab_unit#0 [0,1,2]` | 한 탭에 모두 합쳐져야 — plot 루프에서 2/3 번째 그룹 처리 중 예외? |
| `folder_groups=3` + 개별 모드 + `tab_units`=3개 | 3개 탭이 생성되어야 — `[탭 2/3] 시작` 이후 로그 끊기면 해당 탭 생성 실패 |
| `[탭 N/M] 시작` 로그는 있는데 결과 탭 미생성 | `_finalize_cycle_tab` 진입 전 has_valid_data 실패 or 예외 |

## 영향 범위

- 로그만 추가 (INFO 레벨). 기능 변경 없음
- 성능 영향 미미 (1회 실행당 O(n) n=그룹 수)

## 다음 단계

- 사용자 재실행 → 로그 확인 → 원인 특정
- 원인별 수정 방향:
  - 그룹 분리 실패: `_get_table_row_groups` 빈 행 처리 검토
  - 통합 모드 루프 중단: `try/except` 범위 확대, 예외 로그 상세화
  - 탭 생성 실패: `_finalize_cycle_tab` 호출 직전 has_valid_data 체크 + 로그
