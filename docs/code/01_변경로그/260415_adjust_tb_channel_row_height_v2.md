# 현황 탭 행 높이 재조정: (25, 20) → (20, 9)

## 배경 / 목적

`origin/main` 병합(커밋 `7d8f10a`) 시 행 높이 설정값이 origin/main 의
`(25, 20)` 으로 통합되었다. 실제 운용상 원하는 값은 이전에 적용한
`(20, 9)` (세션 초기 커밋 `61e924c`) 이므로 병합 후에도 이 값을 유지하도록
재조정한다.

## 변경 내용

### 파일
- `DataTool_dev_code/DataTool_optRCD_proto_.py`

### 위치
`filter_all_channels` 내 `tb_channel` 초기화 블록 ([L26888~26889](../../DataTool_dev_code/DataTool_optRCD_proto_.py:26888))

### Before (origin/main 병합 직후)
```python
self.tb_channel.verticalHeader().setDefaultSectionSize(25)
self.tb_channel.verticalHeader().setMinimumSectionSize(20)
```

### After
```python
self.tb_channel.verticalHeader().setDefaultSectionSize(20)
self.tb_channel.verticalHeader().setMinimumSectionSize(9)
```

### 변경 요약
| 항목 | origin/main | 재조정 |
|------|:---:|:---:|
| `defaultSectionSize` | 25 px | **20 px** |
| `minimumSectionSize` | 20 px | **9 px** |

## 영향 범위
- 현황 탭 필터링 모드의 행 높이만 변경
- 경과 시간/상태 색상 등 v3 Phase A 로직은 영향 없음
- UI 초기 정의부(L10942~, 빈 테이블 기본 43px)는 영향 없음
