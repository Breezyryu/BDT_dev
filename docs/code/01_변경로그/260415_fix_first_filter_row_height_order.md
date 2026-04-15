# 첫 필터링 시 행 높이 미반영 버그 근본 수정 — min/default 순서 보정

## 배경 / 목적

현황 탭 진입 후 **첫 필터링 검색** 시 행 높이가 설정값(20px)으로 즉시
반영되지 않는 문제가 있었다. origin/main `66918ba` 에서 `clearContents`
→ `setRowCount(0)` → default/min 설정 → `setRowCount(row_count)` 순서를
도입했으나, **`setDefaultSectionSize` 를 `setMinimumSectionSize` 보다
먼저 호출** 하여 Qt 가 기존 minimum(43) 에 clamp 하는 edge case 가 남아있었다.

### 근본 원인

UI 초기 정의 ([L10942~10943](../../DataTool_dev_code/DataTool_optRCD_proto_.py:10942)):
```python
self.tb_channel.verticalHeader().setDefaultSectionSize(43)
self.tb_channel.verticalHeader().setMinimumSectionSize(43)
```

`minimumSectionSize` 가 43 인 상태에서 `setDefaultSectionSize(20)` 을
먼저 호출하면, Qt 내부적으로 `default >= minimum` 제약을 적용해
default 가 43 으로 유지되는 현상. 이후 `setMinimumSectionSize(9)` 를
호출해도 default 는 이미 잘못 고정된 상태.

## 변경 내용

### 파일
- `DataTool_dev_code/DataTool_optRCD_proto_.py`

### 위치
`filter_all_channels` 내 `tb_channel` 초기화 블록 ([L26886~26890](../../DataTool_dev_code/DataTool_optRCD_proto_.py:26886))

### Before
```python
self.tb_channel.clearContents()
self.tb_channel.setRowCount(0)
self.tb_channel.verticalHeader().setDefaultSectionSize(20)   # ❌ min=43 에 clamp
self.tb_channel.verticalHeader().setMinimumSectionSize(9)
self.tb_channel.setRowCount(row_count)
```

### After
```python
self.tb_channel.clearContents()
self.tb_channel.setRowCount(0)
self.tb_channel.verticalHeader().setMinimumSectionSize(9)    # ✅ 1차: min 먼저 낮춤
self.tb_channel.verticalHeader().setDefaultSectionSize(20)   # ✅ 2차: default 적용
self.tb_channel.setRowCount(row_count)
```

## 영향 범위
- 현황 탭 **첫 필터링 검색** 시 행 높이 즉시 적용
- 2 차 이후 필터링도 동일하게 20px 로 정상 작동
- 다른 탭·기능 영향 없음

## 검증 방법
1. 프로그램 실행 후 현황 탭 진입 (아직 필터링 X)
2. 검색어 입력 후 필터링 실행 → 즉시 20px 행 높이 확인
3. 검색어 변경 후 재필터링 → 여전히 20px 유지 확인
