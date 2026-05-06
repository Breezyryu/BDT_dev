# 데이터 범위 박스 — 배치 정리 (5개 우선순위 일괄 적용)

- 작성일: 2026-05-07
- 대상: 프로파일 탭 데이터 범위 GroupBox
- 파일: [DataTool_optRCD_proto_.py:13007-13166](../../DataTool_dev_code/DataTool_optRCD_proto_.py:13007)

## 변경 사항

박스 시작부에 정렬 상수 6종 정의 ([:13013-13029](../../DataTool_dev_code/DataTool_optRCD_proto_.py:13013))
+ 헬퍼 함수 2종 (`_normalize_seg`, `_normalize_label`).
모든 spacing·width 매직넘버를 상수로 통일.

### 사양 (3차 — 시각적 균일 padding + 박스 폭 명시)

```python
_SEG_BTN_W       = 80     # 세그 버튼 고정 폭 (setFixedWidth — 모든 텍스트에 균일 padding)
_SEG_BTN_FIXED_H = 30     # 세그 버튼 고정 높이
_LABEL_MIN_W     = 32     # 콜론 라벨 최소 폭
_LABEL_TO_FIELD  = 4      # 라벨 ↔ 위젯 spacing
_GROUP_GAP       = 12     # 그룹 ↔ 그룹 spacing
_CHECKBOX_GAP    = 8      # 체크박스 ↔ 체크박스 spacing
```

**박스 가로 길이 — 폭 명시 없음 (5차 결정)**:
- 데이터 범위 박스 / 그래프 옵션 박스 모두 `setFixedWidth` / `setMinimumWidth` 명시 안 함
- 두 박스 같은 부모 `verticalLayout_4` 안에 있어 자연스럽게 동일 가로폭 받음
- 그래프 옵션 박스의 기존 stretch 동작을 데이터 범위 박스에도 그대로 적용

**변경 이력**
- 1차: `setMinimumWidth(60)` — `_make_seg_group` 자동 sizeHint 가 더 클 때 통일 무력화
- 2차: `setFixedWidth(64)` — 통일 강제됐으나 한글 3글자 ("사이클"·"이어서") 가
  버튼 폭에 빡빡하게 들어가 좌우 padding 거의 0 → **시각적으로 인접 버튼과 겹쳐 보임**.
  반대로 영문 짧은 텍스트(SOC/DOD)는 padding 여유 → 같은 폭이지만 "공간 있어 보임"
- 3차: `setFixedWidth(80)` — 가장 긴 "사이클별" 4글자 (~60px) + 좌우 10px씩 padding.
  모든 12개 버튼에 균일 padding 확보 → 텍스트 길이 무관 시각적 균형

**박스 가로폭 — 5차 결정 (폭 명시 제거)**:
- 사용자 요청: 그래프 옵션 박스의 기존 동작 (부모 stretch 자연 폭) 을
  데이터 범위 박스에도 동일 적용
- 두 박스 모두 같은 부모 `verticalLayout_4` → 가로폭 자동 동일
- 행 2 (572px) 가 박스 안에 안 들어가면 widget 일부 잘릴 수 있음 → 그 경우
  세그 버튼 폭 / spacing 추가 압축 또는 행 분리 검토

### 1) 🔴 세그 버튼 균일 폭/높이 (12개 통일)
- `_scope_btns` / `_ovlp_btns` / `_axis_btns` (데이터 범위 박스 9개)
  + `_pv_btns` (사이클탭 묶음 기준 3개) → **프로파일 탭 12개 모두 통일**
- `setFixedWidth(64)` + `setFixedHeight(30)` — `_make_seg_group` 의
  자동 sizeHint 무시하고 강제 통일. 가장 긴 "사이클별" 4글자 수용

### 2) 🔴 라벨 균일 폭 + 라벨 ↔ 위젯 spacing 4 (구간/X축 상하 정렬)
- `profile_scope_label` / `profile_cont_label` / `profile_axis_label` /
  `profile_preset_label` 모두 `_normalize_label()` 적용 (`setMinimumWidth(36)`)
- 모든 행에서 `addWidget(label)` → `addSpacing(4)` → `addWidget(field)` 패턴
- **결과 — 구간:/이음:/X축:/프리셋: 모두 같은 X 좌표에서 시작,
  첫 버튼·콤보 X 좌표도 통일** (행 2 의 [사이클] 과 행 3 의 [SOC] 가 상하 정렬)

### 3) 🟡 그룹 ↔ 그룹 spacing 8/14 → 14 통일
- 행 1: 프리셋 콤보 ↔ Rest포함 (`14` → `_GROUP_GAP=14`)
- 행 2: 구간 그룹 ↔ 이음 그룹 (`8` → `_GROUP_GAP=14`)

### 4) 🟡 체크박스 ↔ 체크박스 spacing 8/14 혼재 → 10 통일
- 행 1: Rest포함 ↔ CV포함 (`8` → `_CHECKBOX_GAP=10`)
- 행 1: CV포함 ↔ 방전→충전 (`14` → `_CHECKBOX_GAP=10`)

### 5) 🟢 박스 마진 + 행간 + 라벨 폰트 통일
- `_data_scope_groupbox` `setContentsMargins(6,4,6,4)` → `(8,6,8,6)`
- `_ds_layout.setSpacing(4)` → `setSpacing(6)` (행 구분 살짝 강화)
- `profile_preset_label` 단독 bold → 모든 라벨 `_pf_font` (normal) 통일

## 시각화 (Before / After)

### Before — 버튼 폭 불균일·spacing 들쭉날쭉
```
구간:[사이클][충전][방전]  이음:[이어서][분리][루프]
       ↑ 텍스트 길이 따라 다른 폭   ↑ spacing 8
프리셋:[(선택)▾]  ☐Rest포함 ☑CV포함  ☐방전→충전
                  ↑ 14    ↑ 8    ↑ 14 (혼재)
```

### After — 균일 폭·spacing 통일 + 4행 분리 (박스 폭 안전 수용)
```
프리셋: [(선택) ▾]    ☐ Rest포함   ☑ CV포함   ☐ 방전→충전
          ↑ 4 ↑ 12          ↑ 8         ↑ 8

구간 :  [ 사이클 ][  충전  ][  방전  ]
   ↑ 4     ↑ 80px 균일

이음 :  [ 이어서 ][  분리  ][  루프  ]
   ↑ 4     ↑ 80px 균일

X축  :  [  SOC  ][  DOD  ][  시간  ]
   ↑ 4     ↑ 80px 균일

→ 구간/이음/X축 라벨 같은 X 좌표 + 첫 버튼(사이클/이어서/SOC) 같은 X 좌표 (완벽 상하 정렬)
```

## 가로폭 분석 (5차 — 행 분리 + 박스 폭 자연 stretch)

행 2 의 구간 + 이음 두 그룹 한 행 (572px) → 그래프 옵션 박스 자연 폭 (~530px) 초과.
**구간 / 이음 / X축 각각 단독 행 (4행 구성)** 으로 분리해 박스 안 안전 수용.

| 행 | 구성 | 위젯 합계 |
|---|---|---|
| 행 1 | 프리셋 + Rest포함 + CV포함 + 방전→충전 | 32+4+100+12+90+8+80+8+100 ≈ **434px** |
| 행 2 | 구간: [사이클\|충전\|방전] | 32+4+244 ≈ **280px** |
| 행 3 | 이음: [이어서\|분리\|루프] | 32+4+244 ≈ **280px** |
| 행 4 | X축: [SOC\|DOD\|시간] | 32+4+244 ≈ **280px** |

가장 긴 행 = **행 1 (434px)** → 그래프 옵션 박스 자연 폭 (~530px) 안에 안전 수용.
구간/이음/X축 라벨 모두 같은 X 좌표 + 첫 버튼 (사이클/이어서/SOC) 도 같은 X 좌표
→ **상하 좌측 정렬 완벽**.

세로 영향: 3행 → 4행으로 약 36px 증가 (박스 마진 + 행 spacing 6 + 행 높이 30).

## 영향 범위

- **UI 표시만 변경** — 위젯 객체·signal·외부 참조 모두 보존
- `_profile_view_seg` (사이클탭 묶음 기준 3개) 도 동일 사양 적용 →
  프로파일 탭 12개 세그 버튼 시각 일관
- 콤보 minimum width `140` → `100` (가로폭 압축)
- 향후 디자인 토큰 변경 시 정렬 상수 6종 (`_SEG_BTN_W` 등) 한 곳만 수정
