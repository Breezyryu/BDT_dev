# 프로파일 분석 박스 — 통합 모드 라디오 라벨 윤문

- 작성일: 2026-05-07
- 대상: `_profile_view_seg` (`CycProfile` / `CellProfile` / `AllProfile`) + 그룹 라벨 신설
- 파일: [DataTool_optRCD_proto_.py](../../DataTool_dev_code/DataTool_optRCD_proto_.py)

## 변경 내역

### 1) 라디오 텍스트 ([:18378-18380](../../DataTool_dev_code/DataTool_optRCD_proto_.py:18378))

| 위젯 | 변경 전 | 변경 후 |
|---|---|---|
| `CycProfile` | `사이클 통합` | **`사이클별`** |
| `CellProfile` | `셀별 통합` | **`셀별`** |
| `AllProfile` | `전체 통합` | **`전체`** |

### 2) 그룹 라벨 신설 ([:12909-12914](../../DataTool_dev_code/DataTool_optRCD_proto_.py:12909), [:18378](../../DataTool_dev_code/DataTool_optRCD_proto_.py:18378))

- `profile_view_label` 위젯 신규 생성 (`QLabel`, 맑은 고딕 10pt)
- 텍스트: **`묶음 기준:`**
- `_pa_mode_row` 의 라디오 좌측에 addWidget ([:13273-13280](../../DataTool_dev_code/DataTool_optRCD_proto_.py:13273))

## 윤문 근거

- 기존 `X 통합` 3회 반복 = 기계적 병렬 + "통합" 한자어 의존 (AI 티 패턴)
- 라디오 본질은 *그래프 라인을 무엇 단위로 묶을지* 선택 → 어미 `별` 로
  의미 직접 전달, "통합" 어휘 제거
- 그룹 라벨 `묶음 기준:` 으로 의미 보강 — `구간:` / `이음:` / `X축:`
  콜론 라벨 패턴과 시각적 일관

## 최종 UI

```
┌─ 프로필 분석 ────────────────────────────────────────────────┐
│ 묶음 기준: [사이클별 | 셀별 | 전체]              ☐ 코인셀(단위변환) │
│ [   프로필 분석   ] [DCIR] [초기화]                              │
└─────────────────────────────────────────────────────────┘
```

## 영향 범위

- **UI 텍스트만 변경** — 라디오 버튼 ID·objectName·외부 참조
  (`CycProfile` / `CellProfile` / `AllProfile`) 모두 보존
- 라디오 동작 매핑 (`'cyc'` / `'cell'` / `'all'`,
  [:4488-4544, 4763-4780](../../DataTool_dev_code/DataTool_optRCD_proto_.py:4488))
  로직 무변경
- 신규 라벨 위젯 추가는 가로폭 +50px 정도 차지 → 동일 행의
  코인셀 체크박스와 가로 경쟁 없음 (addStretch 사이에 두어 자동 분리)
