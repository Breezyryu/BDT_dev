# 현황 탭 필터링 — 작업멈춤 fallback 색상 변경 (노랑 → 빨강)

- 작성일: 2026-05-07
- 대상: 필터링 sub-tab `STATUS_BG` 매핑 + `_classify_paused_reason` 분류 상수
- 파일: [DataTool_optRCD_proto_.py](../../DataTool_dev_code/DataTool_optRCD_proto_.py)

## 배경

v3 재설계(260415) 이후 `_classify_paused_reason()` 의 fallback 반환값
`"작업멈춤"` 은 **노랑(`_STOPPED_BG`)** 으로 표시돼 왔다. 이 케이스는

- `.log` 접근 실패/부재
- 마지막 act/Paused 줄에서 `Reserve` · `즉시 멈춤` · `chamber alarm` 등
  분류 키워드를 찾지 못함
- tail 자체가 비어있는 edge case

즉 **PNE 는 멈춤이라고 보고했는데 .log 가 사유를 알려주지 못한 채널** 이다.
사용자 도메인 판단 — 원인 불명 멈춤은 사용자 액션(노랑)보다 안전조건 이상
(빨강)으로 함께 묶는 편이 현장 식별에 유리함.

## 변경

### 색상 매핑 ([:30867-30882](../../DataTool_dev_code/DataTool_optRCD_proto_.py:30867))

| 상태 | 변경 전 | 변경 후 |
|---|---|---|
| `"작업멈춤"` (fallback) | 🟨 노랑 `_STOPPED_BG` | 🟥 빨강 `_PAUSED_BG` |
| `"사용자멈춤"` | 🟨 노랑 | 노랑 (유지) |
| `"잠시멈춤"` | 🟨 노랑 | 노랑 (유지) |
| `"챔버이슈"` | 🟥 빨강 | 빨강 (유지) |

### 분류 상수 ([:29911-29929](../../DataTool_dev_code/DataTool_optRCD_proto_.py:29911))

```python
# .log 세분화 결과 → 노랑 (사용자 조작)
USER_OR_ERROR_LABELS = frozenset({
    "사용자멈춤",
    "잠시멈춤",
    # "중단점 도달 (S*/C*)" 는 startswith 로 판정
})

# .log 세분화 결과 → 빨강 (하드웨어/챔버 이슈 + 원인 불명 fallback)
HW_WARNING_LABELS = frozenset({
    "챔버이슈",
    "작업멈춤",   # _classify_paused_reason 의 fallback 반환값 (원인 불명)
})
```

`USER_OR_ERROR_LABELS` 에서 `"작업멈춤"` 을 `HW_WARNING_LABELS` 로 이관.
fallback 분기 로직 ([:30936-30948](../../DataTool_dev_code/DataTool_optRCD_proto_.py:30936))
에서 `status_base="작업멈춤"` 이 자동으로 `_PAUSED_BG` 로 매핑된다.

## 4색 체계 (변경 후)

| 색 | RGB | 의미 |
|---|---|---|
| 🟥 빨강 `(214,155,154)` | `_PAUSED_BG` | 안전조건 Code + 챔버이슈 + **작업멈춤(fallback)** |
| 🟨 노랑 `(240,220,160)` | `_STOPPED_BG` | 사용자멈춤 + 중단점 도달 + 잠시멈춤 |
| 🟩 연녹 `(234,239,230)` | `_COMPLETED_BG` | 완료/시험완료 (셀있음, vol≠"-") |
| 🟢 녹 `(176,203,176)` | `_IDLE_BG` | 대기/준비/작업정지 (셀없음, vol="-") |

## 영향 범위

- **필터링 sub-tab `tb_channel_filter`**: 행 전체 배경색이 빨강으로
  표시됨 → 사용자 액션(노랑)과 시각적으로 분리
- **현황 탭 그리드 `tb_channel`** (`pne_table_make`,
  [:29823-29843](../../DataTool_dev_code/DataTool_optRCD_proto_.py:29823))
  는 `bg_level` 기반 분기로 별도 동작 — 본 변경에 영향 없음.
  (현황 그리드의 작업멈춤 처리는 추후 일관화 검토 대상)

## 검증 포인트

- `Code=153 + 작업멈춤종료` 채널에서 `.log` 누락 시 fallback 트리거 → 빨강 표시
- 사용자멈춤 (`즉시 멈춤 시행`) → 노랑 유지
- 중단점 도달 (`Reserve Cycle: N, Step: M`) → 노랑 유지
- 챔버이슈 (`chamber alarm`) → 빨강 유지
