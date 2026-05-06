# 프로파일 탭 — 데이터 범위 박스 행 1 라벨 노출 + 라디오 텍스트 변경

- 작성일: 2026-05-07
- 대상: 프로파일 탭 데이터 범위 GroupBox 행 1
- 파일: [DataTool_optRCD_proto_.py](../../DataTool_dev_code/DataTool_optRCD_proto_.py)

## 변경 내역

### 1) 라벨 노출 ([:13014-13042](../../DataTool_dev_code/DataTool_optRCD_proto_.py:13014))
기존에는 `profile_scope_label` / `profile_cont_label` 위젯이 생성만 되고
`setVisible(False)` 로 숨김 처리되어 있었음. 행 2 의 `X축:` 라벨과
시각적 일관성을 맞추기 위해 노출 + `_profile_opt_row1` 에 addWidget.

### 2) 라벨 텍스트 ([:18399-18400](../../DataTool_dev_code/DataTool_optRCD_proto_.py:18399))

| 위젯 | 변경 전 | 변경 후 |
|---|---|---|
| `profile_scope_label` | `데이터:` | **`구간:`** |
| `profile_cont_label` | `연속성:` | **`이음:`** |

윤문 관점 — `데이터:` 는 GroupBox 제목 `데이터 범위` 와 단어 중복.
`연속성:` 은 학술적·번역투 인상. 한국어 일상 어휘로 짧게.

### 3) Overlap 라디오 텍스트 ([:13037](../../DataTool_dev_code/DataTool_optRCD_proto_.py:13037))

| 라디오 (id=2) | 변경 전 | 변경 후 |
|---|---|---|
| `profile_ovlp_connected` | `연결` | **`루프`** |

내부 변수명·코드 참조는 보존(`profile_ovlp_connected` / `_axis_connected`).
UI 표기만 변경. 사용자 의도 — 사이클별 0 시작 + 충전→방전 순차 연결 시
사이클이 닫혀 시각적으로 루프가 그려지는 점 강조.

## 최종 UI (260507 행 재배치 반영)

```
┌─ 데이터 범위 ───────────────────────────────────────────────────┐
│ 프리셋: [(선택) ▾]    ☐ Rest포함   ☑ CV포함    ☐ 방전→충전        │
│ 구간:  [사이클 | 충전 | 방전]   이음: [이어서 | 분리 | 루프]         │
│ X축:   [SOC | DOD | 시간]                                       │
└────────────────────────────────────────────────────────────┘
```

행 재배치 의도 — 자주 건드리는 옵션(프리셋·필터·페어링)을 최상단,
주요 분석 축(구간·이음·X축)은 아래로 내림. 위젯 인스턴스는
보존, addWidget 순서만 변경 ([:13010-13134](../../DataTool_dev_code/DataTool_optRCD_proto_.py:13010)).

## 영향 범위

- **UI 텍스트만 변경** — `data_scope` / `overlap` 매핑 로직, 시간축 핸들러
  (`_axis_continuous` / `_axis_split` / `_axis_connected`) 모두 그대로
- 외부 참조 (테스트 코드 / 프리셋 / 자동화 스크립트) 가 라디오 객체를
  `profile_ovlp_connected` 변수명으로 참조하므로 영향 없음
- `setVisible(False)` 제거로 행 1 가로폭이 약간 늘어남 → 행 2 의 X축
  라벨과 좌측 정렬 패턴이 통일됨
