# 사이클 탭 헤더 버튼 동일선상 + 캔버스 확장 (빈 공간 활용)

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수: `_finalize_cycle_tab()` (L18980+)

## 배경

사용자 요청:
> 버튼들을 동일선상에 나열해줘
> 그래프 크기 및 배치를 정렬하여 빈 공간을 다 활용해

현재 상황:
1. 서브탭 모드에서 **▶ CH** 버튼(채널 토글) 과 **▶ 상세** 버튼(classify_info 펼침) 이 각각 **다른 줄** 에 배치 → 세로 공간 낭비
2. `FigureCanvas` 의 기본 sizePolicy 가 `Preferred` 라 탭 가로 폭을 꽉 채우지 않음 → 우측에 빈 공간, 하단 플롯 잘림

## 변경 내용

### 1. 헤더 버튼 동일선상 (서브탭 모드)

`_finalize_cycle_tab` 의 서브탭 분기에서 `classify_info 바` + `toggle_btn` 을 **한 줄에 통합**.

```python
# 서브탭 모드: classify_info + toggle_btn 한 줄 통합
if info_label is not None or toggle_btn is not None:
    header_row = QHBoxLayout()
    header_row.setContentsMargins(0, 0, 0, 0)
    header_row.setSpacing(4)
    if info_label is not None:
        header_row.addWidget(info_label, 1)  # info 가 가로 stretch 독점
    else:
        header_row.addStretch(1)
    if toggle_btn is not None:
        header_row.addWidget(toggle_btn)
    tab_layout.addLayout(header_row)
```

- `info_label` (패턴 요약 + ▶ 상세) 가 가로 stretch 독점 (폭 자동 확장)
- `toggle_btn` (▶ CH) 은 오른쪽 끝 고정
- 결과: `[ 패턴정보 ... ▶ 상세 ] [ ▶ CH ]` 한 줄에 정렬

### 2. 캔버스 확장 (빈 공간 활용)

`FigureCanvas` 에 **Expanding sizePolicy** 명시 + layout `addWidget` 에 `stretch=1`:

```python
from PyQt6.QtWidgets import QSizePolicy as _QSP

canvas.setSizePolicy(_QSP.Policy.Expanding, _QSP.Policy.Expanding)
# 서브탭 내부 canvas 도 동일
for _ef in extra_figs:
    _ec = FigureCanvas(_ef)
    _ec.setSizePolicy(_QSP.Policy.Expanding, _QSP.Policy.Expanding)
    ...

# stretch=1 로 세로 공간 독점
_l1.addWidget(canvas, 1)
tab_layout.addWidget(inner, 1)
```

- 기본 `FigureCanvasQTAgg` sizePolicy 는 `Preferred` → figsize*dpi 기본 크기까지만 확장
- `Expanding` 으로 변경 → 부모 레이아웃의 stretch 에 반응하여 **탭 가로/세로 공간 전체 채움**
- `tight_layout` 은 이미 호출 중이므로 캔버스 resize 시 자동으로 margin 재계산

### 3. 단일 모드 (extra_figs=None) 호환

기존 단일 canvas 경로:
```python
if toggle_btn is not None:
    toolbar_row = [toolbar, toggle_btn]
    tab_layout.addLayout(toolbar_row)
else:
    tab_layout.addWidget(toolbar)
if info_label is not None:
    tab_layout.addWidget(info_label)
tab_layout.addWidget(canvas, 1)   # 캔버스 stretch 추가 (회귀 안전)
```

- 기존 레이아웃 구조 유지 (toolbar, classify_info, canvas 순서)
- canvas 에만 `stretch=1` 추가 → 빈 공간 활용 개선
- 하위 호환 완전 보장

## 레이아웃 비교

### 서브탭 모드 (Before)
```
┌────────────────────────────────────────────────┐
│ [ (빈 공간) ............... ] [ ▶ CH ]        │  ← toolbar_row
├────────────────────────────────────────────────┤
│ [Q8 ATL Main...] 충전 4step... [▶ 상세]        │  ← classify_info
├────────────────────────────────────────────────┤
│ [요약] [상세]                                    │  ← inner QTabWidget
│ ┌──────────────┐                                │
│ │   2×3 figure │ (우측 빈 공간)                   │
│ └──────────────┘                                │
└────────────────────────────────────────────────┘
```

### 서브탭 모드 (After)
```
┌────────────────────────────────────────────────┐
│ [Q8 ATL Main...] 충전 4step... [▶ 상세] [▶ CH] │  ← 한 줄 통합
├────────────────────────────────────────────────┤
│ [요약] [상세]                                    │  ← inner QTabWidget
│ ┌──────────────────────────────────────────┐   │
│ │        2×3 figure (탭 폭 전체 활용)        │   │
│ │                                           │   │
│ └──────────────────────────────────────────┘   │
└────────────────────────────────────────────────┘
```

## 영향 범위

- `_finalize_cycle_tab()` 만 수정
- 서브탭 모드 (`extra_figs` 있음): 헤더 레이아웃 개선 + 캔버스 확장
- 단일 모드 (`extra_figs=None`): 기존 구조 유지 + 캔버스 stretch=1 추가
- `_build_classify_info_label` / `_create_cycle_channel_control` 는 **불변**
- 사이클 탭 외 다른 `_finalize_cycle_tab` 호출처 없음 (ECT/프로파일 별도 함수)

## 검증 포인트

- [ ] 사이클 분석 실행 → **[패턴정보] [▶ 상세] [▶ CH]** 한 줄에 배치 확인
- [ ] 그래프가 탭 **가로 폭 전체** 사용, 우측 빈 공간 없음
- [ ] 그래프 **세로** 도 탭 높이 꽉 채움 (하단 플롯 정상 표시)
- [ ] 탭 리사이즈 (창 크기 조절) 시 그래프가 **동적으로 재렌더**
- [ ] "요약"/"상세" 서브탭 전환 시 동일 크기
- [ ] 채널 토글 (▶ CH) 정상 동작 (위치만 변경)
- [ ] classify_info 펼침 (▶ 상세) 정상 동작 (위치만 변경)
- [ ] `mkdcir` / 일반 DCIR 모드 모두 정상
- [ ] 단일 모드 (ECT 등 subtab 없는 경로) 기존 동작 불변
