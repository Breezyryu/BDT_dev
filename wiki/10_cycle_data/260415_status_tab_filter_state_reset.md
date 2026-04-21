# 현황 탭 필터링 상태 리셋 (행 높이 미적용 / 좁혀진 결과 회귀 수정)

> **작성일**: 2026-04-15
> **대상 파일**: `DataTool_dev_code/DataTool_optRCD_proto_.py`
> **변경 위치**: `filter_all_channels()` (line 26582 ~) — `setRowCount` 호출부 재배치

---

## 증상

1. **첫 검색 시 행 높이가 25px 로 안 줄어듦** — 일부 행이 초기 43px 그대로 표시
2. **두 번째 필터링부터 결과가 좁혀져 보임** — 직전 검색의 setRowHidden 상태가 살아남아 새 데이터가 일부 숨김 처리됨

## 원인 (Root Cause)

`filter_all_channels()` 가 테이블을 **재초기화하지 않고** 위에 덮어 그림.

| 문제 | 영향 |
|---|---|
| 호출 순서: `setRowCount(row_count)` → `setDefaultSectionSize(25)` | 새 default 가 이미 만들어진 행에는 적용 안 됨 → 기존 행 43px 유지 |
| `setRowHidden(r, True)` (섹션 토글, 헤더 접기 등) 가 그대로 남음 | 새 호출에서 같은 row index 의 데이터가 숨김 처리되어 결과가 적게 보임 |
| `clearContents()` / `setRowCount(0)` 호출 부재 | 이전 행 상태(데이터·숨김·메타) 누적 |

## 수정 (Root Cause Fix)

`setRowCount(row_count)` **이전**에 다음 단계를 명시적으로 수행:

```python
self.tb_channel.setColumnCount(num_cols)
# 1) 내용·구조·숨김 상태 전부 비움
self.tb_channel.clearContents()
self.tb_channel.setRowCount(0)
# 2) 행 default 높이를 먼저 설정 → 이후 추가되는 행에 새 default 적용
self.tb_channel.verticalHeader().setDefaultSectionSize(25)
self.tb_channel.verticalHeader().setMinimumSectionSize(20)
self.tb_channel.setRowCount(row_count)
```

기존 line 26821-22 의 중복된 `verticalHeader().setDefaultSectionSize(25)` / `setMinimumSectionSize(20)` 호출은 제거 (위쪽 블록에서 일괄 처리).

## 효과

- **첫 필터링부터** 모든 행이 25px 로 일관되게 생성됨
- **N 번째 필터링도** 깨끗한 빈 테이블에서 시작 → setRowHidden 누적 영향 제거
- 섹션 토글(`_filter_toggle_section`) 동작은 매 필터링 호출 직후 `_filter_sections = {}` 로 새로 등록되므로 기존 동작 그대로

## 회귀 영향

- 행 그리기 비용은 사실상 동일 (어차피 `setRowCount(row_count)` 호출 → 행 재할당)
- 일반 모드 테이블 (`tb_cycler_combobox` 등 다른 경로) 변화 없음
- 컬럼 너비, 매칭 로직 변화 없음
