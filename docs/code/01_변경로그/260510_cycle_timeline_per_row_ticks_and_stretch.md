# 사이클 타임라인 바 — 행별 눈금 분리 + 사이클 패턴 박스 잔여공간 흡수

날짜: 2026-05-10
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
요청: 류성택 (260510 BDT 사용 중 요청)

대상 식별자:
- `class CycleTimelineBar` (L11026 ~)
  - `_TICK_HEIGHT` 상수 의미 변경 (16 → 14, "행 1개당 눈금 영역")
  - `__init__` `_min_h`/`_max_h` 산식 (L11054 부근)
  - `_update_size()` (L11081 부근)
  - `_row_y()` (L11222 부근)
  - `paintEvent()` 마지막 단일 눈금 블록 → 행 루프 내부로 이동 (L11297 부근)
- UI 조립부 (`Ui_MainWindow`, "Profile" 좌패널)
  - `_timeline_scroll` max 클램프 해제 (L13787 부근)
  - `_timeline_groupbox` `setSizePolicy(Preferred, Expanding)` + `addWidget(..., 1)` (L13800 부근)
  - 14160 부근 `verticalLayout_4.addStretch(1)` 제거

## 사용자 보고 — 그대로

> 1) 여러 개의 타임라인이 있으면 각각 사이클 눈금도 구분했으면 한다.
> 2) 5. 프로파일 분석 박스 밑에 남는 공간을 2. 사이클 패턴 박스가 활용하자.

(첨부 캡처: Profile 탭 좌측 패널, 2. 사이클 패턴 박스 1행 + 그 외 4개 박스 + 5번 박스
하단의 빈 공간이 보이는 상태)

## 근본 원인

### (1) 행별 눈금 누락
이전 `paintEvent()` 는 행 루프가 끝난 뒤 **마지막 행 아래에 단 한 줄**의 눈금을
그렸고, 그 기준은 `self._total_cycles` (활성 행의 total) 였음. 결과적으로
다중 채널 다중 경로일 때 **행마다 total 사이클이 달라도** 모두 활성 행
기준으로만 0/100/200… 눈금이 표시돼, 비활성 행의 실제 사이클 수와 시각이
맞지 않았음.

```python
# (구)
if self._rows and self._total_cycles > 0:
    tick_y = self._row_y(len(self._rows) - 1) + self._ROW_HEIGHT + 2
    tc = self._total_cycles
    ...
    for t in ticks:
        tx = self._cycle_to_x(t)   # 활성 행 blocks 기준 X 변환
```

### (2) 잔여 세로 공간 낭비
좌패널 `verticalLayout_4` 가 위에서부터 다음 순서로 위젯을 쌓고 있었음.

1. (숨김) `_stepnum_container`
2. **2. 사이클 패턴** (`_timeline_groupbox`)
3. 3. 데이터 범위
4. 4. 그래프 옵션
5. 5. 프로파일 분석
6. **`addStretch(1)`** ← 5번 박스 밑 빈 공간을 흡수해 버림

또한 `_timeline_scroll.setMaximumHeight(self.cycle_timeline._max_h)` 로 1행
기준 ~38px (4행 기준 ~88px) 에서 클램프 되어 박스가 아무리 크게 잡혀도
바 영역은 그 이상 자라지 못했음.

## 변경 내용

### (1) 행별 사이클 눈금 분리 — `paintEvent()` 행 루프 내부 이동

각 행의 (라벨, blocks, total) 을 그린 직후, 그 행 바로 아래 14px 영역에
**그 행의 `total` 기준 눈금**을 그린다. `_cycle_to_x(t, blocks, total)` 처럼
명시적으로 행의 blocks/total 을 넘겨 X 변환도 행마다 독립.

```python
# (신) 행 루프 내부
if total > 0:
    tick_y = bar_y + bar_h + 1
    ...
    if total <= 20:   step = 5
    elif total <= 100: step = 10
    elif total <= 500: step = 50
    elif total <= 2000: step = 100
    else: step = 500
    ticks = list(range(step, total, step))
    if total not in ticks:
        ticks.append(total)
    for t in ticks:
        tx = self._cycle_to_x(t, blocks, total)   # 행별 blocks/total
        painter.drawLine(int(tx), tick_y, int(tx), tick_y + 3)
        painter.drawText(int(tx) - 20, tick_y + 3, 40, 11,
                         AlignHCenter | AlignTop, str(t))
```

행 루프 밖에 있던 단일 눈금 블록은 제거.

### (2) 행 1개당 (바 + 눈금) 묶음으로 사이즈 산식 갱신

| 상수 | 구 의미 | 신 의미 |
|---|---|---|
| `_TICK_HEIGHT` | 16 px (맨 밑 한 번만) | **14 px (행마다)** |

높이 산식:
- 1행: `_per_row + 4` = 36 px (구: 38 px)
- 4행: `_per_row × 4 + GAP × 3 + 4` = 138 px (구: 88 px)

| 함수 | 구 | 신 |
|---|---|---|
| `__init__._min_h` | `ROW + TICK + 4` | `(ROW + TICK) + 4` |
| `__init__._max_h` | `ROW × 4 + GAP × 3 + TICK + 4` | `(ROW + TICK) × 4 + GAP × 3 + 4` |
| `_update_size.h` | `n × ROW + (n-1) × GAP + TICK + 4` | `n × (ROW + TICK) + (n-1) × GAP + 4` |
| `_row_y(ri)` | `2 + ri × (ROW + GAP)` | `2 + ri × ((ROW + TICK) + GAP)` |

### (3) 사이클 패턴 박스가 잔여 세로 공간 흡수

```python
# 13787 부근 — ScrollArea max 클램프 해제
# (구) self._timeline_scroll.setMaximumHeight(self.cycle_timeline._max_h)
# (신) 부모 GroupBox stretch 가 ScrollArea 도 같이 키우게 풀어둠

# _update_size() 내부
scroll.setMaximumHeight(16777215)   # Qt 기본 상한 (= QWIDGETSIZE_MAX)

# 13800 부근 — GroupBox 에 Vertical Expanding + stretch=1
self._timeline_groupbox.setSizePolicy(
    QtWidgets.QSizePolicy.Policy.Preferred,
    QtWidgets.QSizePolicy.Policy.Expanding)
self.verticalLayout_4.addWidget(self._timeline_groupbox, 1)

# 14160 부근 — 하단 addStretch(1) 제거
# (구) self.verticalLayout_4.addStretch(1)
```

데이터 범위(3) / 그래프 옵션(4) / 프로파일 분석(5) 박스는 default stretch=0
이므로 자체 sizeHint 만큼만 차지. 남은 공간은 모두 사이클 패턴 박스로.

## 시각 효과

### 단일 행
- 박스 자체는 5번 박스 아래 빈 영역까지 늘어남 → 사이클 바 위/아래 여백이
  넉넉해지면서 박스 가독성 ↑
- 사이클 바 자체의 그리기 영역은 18 px (ROW_HEIGHT) 그대로 — 가는 띠 모양 유지
- 바 바로 아래 14 px 에 자기 눈금

### 4행 (다중 채널/다중 경로)
| ri | 18 px 바 | 14 px 자기 눈금 | 2 px GAP |
|----|---------|----------------|---------|
| 0  | 채널 022 (예 total=4383) | 0/500/1000/.../4383 | |
| 1  | 채널 023 (예 total=1023) | 0/100/200/.../1023  | |
| 2  | 채널 024 (예 total=4383) | 0/500/1000/.../4383 | |
| 3  | 채널 032 (예 total=2046) | 0/100/200/.../2046  | |

→ 각 행이 자기 사이클 길이를 정확히 반영 (이전엔 모두 활성 행 기준).

## 회귀 영향

- `_row_at_y(y)` 는 그대로. 행 클릭 영역은 ROW_HEIGHT (18 px) 만 — 눈금 영역 클릭은 활성 행 전환에 영향 없음.
- `mousePressEvent`/`Shift`/`Ctrl`/`Drag` 모두 좌표 → 사이클 변환만 사용해 기존 동작 보존.
- `set_blocks()` (단일 행) 경로도 호환 — 1행 모드에서는 한 줄 + 눈금 14 px.
- `_max_h` 상수는 4행 한도 산정용 참고치로만 사용 (실제 클램프는 풀림).
- 박스 stretch=1 은 다른 좌패널 박스(데이터 범위·그래프 옵션·프로파일 분석)
  의 sizeHint 를 침범하지 않음 (default stretch=0 이라 자체 크기 유지).

## 검증

- `python -m py_compile DataTool_dev_code/DataTool_optRCD_proto_.py` → OK
- 수동 시각 확인 항목:
  - [ ] Profile 탭 1행 모드 — 박스가 5번 박스 밑 빈 공간 흡수, 바 + 눈금 가독성
  - [ ] 다중 행 (2~4행, 서로 다른 total) — 각 행 아래에 자기 눈금이 그려지는지
  - [ ] 행 클릭 → 활성 전환 시 다른 행 선택 보존 / 노란·파란 오버레이 정상
  - [ ] 우클릭 메뉴 (이 블록 / 같은 패턴 / 전체 / 해제) 정상
  - [ ] Shift+Click / Ctrl+Click / Drag / Ctrl+Drag 정상
