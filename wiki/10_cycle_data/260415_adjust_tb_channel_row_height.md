# 현황 탭(tb_channel) 행 높이 조정: 11px → 20px

## 배경 / 목적

현황 탭(`tb_channel`)에서 검색 결과를 채운 뒤 행 높이가 11px로 매우 낮게 설정되어 있어
데이터 텍스트(Malgun gothic 9pt 기준)가 시각적으로 답답하게 보이는 문제가 있었다.
가독성 확보를 위해 20px로 상향 조정한다.

## 변경 내용

### 파일
- `DataTool_dev_code/DataTool_optRCD_proto_.py`

### Before

```python
# 행 높이 줄이기
self.tb_channel.verticalHeader().setDefaultSectionSize(11)
self.tb_channel.verticalHeader().setMinimumSectionSize(9)
```

### After

```python
# 행 높이 줄이기
self.tb_channel.verticalHeader().setDefaultSectionSize(20)
self.tb_channel.verticalHeader().setMinimumSectionSize(9)
```

### 변경 요약

| 항목 | Before | After |
|------|--------|-------|
| `defaultSectionSize` | 11 px | **20 px** |
| `minimumSectionSize` | 9 px | 9 px (유지) |

## 영향 범위

- **대상 위젯**: 현황 탭의 `tb_channel` (채널 현황 테이블)
- **적용 시점**: 검색 실행 → 검색 결과가 1건 이상일 때 테이블을 채우는 시점
- **영향 없음**:
  - UI 초기 정의(빈 테이블 상태)의 기본 행 높이 43px 설정은 유지
  - 열 너비, 폰트, 색상, 다른 탭 테이블은 영향 없음
