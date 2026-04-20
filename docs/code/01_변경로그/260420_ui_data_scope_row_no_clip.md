# 데이터 범위 옵션 행의 시각적 잘림 완화

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수: `_make_seg_group()` (L10494), `setupUi` 의 `_profile_opt_row2` 구성 (L11335-11393)

## 배경 / 문제

사용자 보고:
> "데이터 범위 UI버튼 시각적으로 잘리는 부분이 있다. X축 : 시간, 프리셋 등"

프로필 탭 `데이터 범위` GroupBox 2행에 다음 요소가 나열된다:

```
X축: [SOC(DOD)] [시간]  ☑Rest ☑CV  프리셋: [(선택)▼]
```

- 세그먼티드 토글 버튼의 최소 폭이 **PyQt6 기본 버튼 padding** 을 충분히 흡수하지 못해, 렌더 단계에서 텍스트가 버튼 테두리 바로 앞까지 꽉 차 시각적으로 잘린 것처럼 보임.
- 체크(bold) 상태 시 텍스트 폭이 소폭 증가하지만, `setMinimumWidth` 계산이 **non-bold 폰트 metrics + 20 px** 여서 bold 전환 시 좁아 보임.
- 행의 `addSpacing(16)` + `addSpacing(20)` 누적 36 px 이 좁은 창에서 오른쪽 요소(프리셋 콤보)까지 밀어내 잘리는 요인.

## 원인

### 1. `_make_seg_group` 버튼 폭 공식 여유 부족 (L10519)

```python
btn.setMinimumWidth(_fm.horizontalAdvance(text) + 20)
```

- `_fm` 은 bold 기준이지만 `+20` 으로는 PyQt6 기본 `QPushButton` 의 좌우 padding(약 `15px × 2`) 을 완전히 흡수 못 함.
- 결과: 짧은 라벨 (`"시간"`, `"분리"`) 은 여유가 있지만, 긴 라벨 (`"SOC(DOD)"`, `"이어서"`) 은 텍스트가 버튼 테두리 근처까지 붙어 **잘린 것처럼 보임**.

### 2. `_profile_opt_row2` 중간 스페이싱 과다

```python
self._profile_opt_row2.addSpacing(16)   # [시간] ↔ ☑Rest
self._profile_opt_row2.addSpacing(20)   # ☑CV ↔ 프리셋:
```

- 1913 px 기준 기본 창에선 여유가 있지만, 탭 분할/리사이즈/다른 panel 과 공유 시 오른쪽이 잘릴 수 있음.

## 수정

### 1. 버튼 최소 폭 공식 확장 (+20 → +28)

```python
# After
# bold(체크 시) 렌더링 편차 + PyQt6 기본 버튼 좌우 padding 흡수
btn.setMinimumWidth(_fm.horizontalAdvance(text) + 28)
```

- 8 px 증가 = PyQt6 버튼 padding 여유 흡수 + bold 전환 시 텍스트 잘림 방지
- 4개 세그 그룹 (profile_view, profile_scope, profile_overlap, profile_axis) 모두에 일괄 적용
- 영향: 각 버튼 6~8 px 증가 → 한 행 총 +18~24 px (균등 확대라 시각적 위화감 적음)

### 2. `_profile_opt_row2` 스페이싱 축소

```python
# After
self._profile_opt_row2.addSpacing(12)   # 16 → 12
...
self._profile_opt_row2.addSpacing(14)   # 20 → 14
```

- 총 10 px 절약 → 버튼 확장분(+18~24px) 일부 상쇄
- 시각적으로는 체크박스 간격이 여전히 충분히 구분됨

## 순 폭 변화

| 요소 | Before | After | 차이 |
|---|---|---|---|
| SOC(DOD) 버튼 | text+20 | text+28 | +8 |
| 시간 버튼 | text+20 | text+28 | +8 |
| [시간]↔Rest 간격 | 16 | 12 | -4 |
| CV↔프리셋 간격 | 20 | 14 | -6 |
| **행 2 총합** | — | — | **+6** |

행 2 기준 약 +6 px 순증가지만, 버튼 내부 padding 여유가 확보되어 **잘려 보이는 시각 효과 소멸**이 주된 개선.
다른 세그 그룹(사이클/충전/방전, 이어서/분리/연결, 프로필 분석 모드) 도 동일 여유 확보.

## 영향 범위

- `_make_seg_group()` — 버튼 폭 공식 한 줄
- `_profile_opt_row2` — `addSpacing` 2개 값 조정
- 기능 로직 미변경, 순수 시각적 여유 확보
- 회귀 위험: 매우 낮음
  - 기존보다 버튼이 균등하게 약간 넓어질 뿐
  - 세그 그룹이 쓰이는 모든 행 (데이터 범위, 프로필 분석 모드) 동일 효과

## 검증 포인트

- [ ] 프로필 탭 `데이터 범위` GroupBox 의 1행 (사이클|충전|방전, 이어서|분리|연결), 2행 (SOC(DOD)|시간, Rest, CV, 프리셋 드롭다운) 모두 **텍스트 잘림 없음**
- [ ] `사이클통합|셀별통합|전체통합` 모드 세그 도 동일 여유 확보 확인
- [ ] 체크(bold) 상태 전환 시 텍스트 흔들림 없음
- [ ] Windows 고DPI (125%/150%) 환경에서 잘림 재발 여부 — 재발 시 `+28` → `+32` 로 추가 조정 여지

## 후속 과제 (별건)

- `profile_preset_combo.setMinimumWidth(140)` — 콤보 최소 폭 고정. 아이템 중 "히스테리시스" 기준으로 자동 폭 계산은 `setSizeAdjustPolicy(AdjustToContents)` 로 개선 가능. 필요 시 별도 PR.
- 매우 좁은 창에서도 잘림 없도록 하려면 `_profile_opt_row2` 를 2줄로 분리 (X축/Rest/CV | 프리셋) 하는 구조 변경 검토 가능.
