# 사이클 패턴 박스 + 프로파일 분석 박스 제목 + 좌측 패널 stretch 조정

- 작성일: 2026-05-07
- 대상: 사이클 타임라인 / 프로파일 분석 GroupBox + `verticalLayout_6` stretch
- 파일: [DataTool_optRCD_proto_.py](../../DataTool_dev_code/DataTool_optRCD_proto_.py)

## 변경 요약

| 위젯 | 변경 |
|---|---|
| `_timeline_groupbox` | 신설 + 제목 **`사이클 패턴`** ([:12988](../../DataTool_dev_code/DataTool_optRCD_proto_.py:12988)) |
| `_profile_analysis_groupbox` | 제목 추가 (없음 → **`프로파일 분석`**) ([:13334](../../DataTool_dev_code/DataTool_optRCD_proto_.py:13334)) |
| `verticalLayout_6` 의 `tabWidget_2` | stretch=0 → **stretch=1** ([:13390](../../DataTool_dev_code/DataTool_optRCD_proto_.py:13390)) |

## 사이클 패턴 박스 (신설)

기존 — 사이클 타임라인 바 + 선택 레이블이 `verticalLayout_4` 에 직접
addWidget 으로 노출. 박스 선 없이 다른 GroupBox(데이터 범위·그래프
옵션) 들과 시각 위계 어긋남.

신규 — `QGroupBox("사이클 패턴")` 으로 묶어 다른 GroupBox 들과 동일
시각 처리. 사이클 바 + 선택 상태 레이블 한 묶음.

```
┌─ 사이클 패턴 ──────────────────────────────────┐
│ ┌──────────────────────────────────────────┐ │
│ │  [TC1][TC2][TC3]...[TC N]    (스크롤 영역) │ │
│ └──────────────────────────────────────────┘ │
│ TC 5–12 선택됨 (사이클 47–112)                  │
└─────────────────────────────────────────────┘
```

윤문 — `사이클 타임라인` 의 "타임라인" 외래어 회피. `사이클 패턴` 은
`CycleTimelineBar` 클래스 docstring "사이클 패턴 타임라인 바 위젯"
([:10251](../../DataTool_dev_code/DataTool_optRCD_proto_.py:10251)) 와 일치 + 한국어 자연 어휘.

## 프로파일 분석 박스 제목 신설

기존 — `_profile_analysis_groupbox` GroupBox 가 제목 없이 생성 → 다른
박스와 시각 위계 어긋남.

신규 — 제목 **`프로파일 분석`** 추가. 4개 박스 모두 명사구 제목으로 통일:

```
┌─ 사이클 패턴 ────────┐
┌─ 데이터 범위 ────────┐
┌─ 그래프 옵션 ────────┐
┌─ 프로파일 분석 ──────┐
```

## 좌측 패널 stretch 조정

박스 추가/제목 추가로 `tabWidget_2` 안의 박스들 (사이클 패턴 / 데이터
범위 / 그래프 옵션 / 프로파일 분석) 세로 공간 +40~60px 필요.

| 위젯 | 변경 전 | 변경 후 |
|---|---|---|
| `_path_groupbox` (1. 경로 입력) | stretch=0 | stretch=0 (그대로) |
| `tabWidget_2` (Cycle/Profile 탭) | stretch=0 | **stretch=1** |

`tabWidget_2` 가 좌측 패널의 빈 세로 공간을 흡수 → Cycle/Profile 탭
안의 박스들이 더 넉넉히 표시. `_path_groupbox` 는 sizeHint 만큼만 차지.

## 영향 범위

- **위젯 객체 보존** — `cycle_timeline` / `_timeline_scroll` /
  `_timeline_selection_label` / `_profile_analysis_groupbox` 모두 동일 변수명 유지
- **외부 참조 무영향** — `_update_timeline_selection_label` 등 메서드
  내부 `setText`/`setVisible` 호출 그대로 동작
- **세로 영향** — GroupBox 제목·마진으로 +24~40px (`tabWidget_2` stretch=1
  로 흡수)
