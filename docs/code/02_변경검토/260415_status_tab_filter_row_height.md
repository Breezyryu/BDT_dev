# 현황 탭 필터링 모드 행 높이 조정

> **작성일**: 2026-04-15
> **대상 파일**: `DataTool_dev_code/DataTool_optRCD_proto_.py`
> **변경 위치**: `filter_all_channels()` 내부 — 행 높이 설정 (기존 line 26821-26822)

---

## 배경

현황 테이블(`self.tb_channel`) 은 일반 모드에서 행 높이 **43px** 로 표시되지만, 필터링 실행 직후(`filter_all_channels()`) 에는 행 높이가 **11px / 최소 9px** 로 크게 줄어들어 가독성이 저하되는 문제가 있었다.

- 초기(일반 모드): `setDefaultSectionSize(43)`, `setMinimumSectionSize(43)` (line 10942-10943)
- 이전 필터 모드: `setDefaultSectionSize(11)`, `setMinimumSectionSize(9)` — 텍스트가 세로로 눌림

## 변경 내용

필터 모드 행 높이를 초기(43) 와 이전 축소(11) 사이 **중간값**으로 조정.

| 항목 | Before | After |
|---|---|---|
| `setDefaultSectionSize` | 11 | **25** |
| `setMinimumSectionSize` | 9 | **20** |

## 기대 효과

- 필터링 후에도 한 줄 텍스트(충방전기/채널/상태/전압 등) 가독성 확보
- 콤팩트 모드 성격은 유지 (초기 43 의 ~58% 수준)
- 섹션 헤더/데이터 행 구분은 기존 로직(배경색·토글) 그대로

## 회귀 영향

- 일반 모드(초기 43px) 변화 없음
- 필터 섹션 접기/펼치기(`_filter_toggle_section`) 동작 변화 없음
- 컬럼 너비·컬럼 구성 변화 없음
