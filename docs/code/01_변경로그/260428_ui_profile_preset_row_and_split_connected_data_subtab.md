# 프로파일 옵션 UI 정리 + 분리/연결 데이터 서브탭 구조 변경

날짜: 2026-04-28
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수:
- `Ui_sitool.setupUi()` — 프로파일 옵션 행 레이아웃 (~L11716+)
- `_create_profile_data_subtab()` (L19315+)
- `_profile_render_loop()` 시그니처 + 호출부 (L19906+)
- `unified_profile_confirm_button()` 호출부 (L26345+)

## 배경 — 사용자 보고 2건

1. **UI 겹침**: "데이터 범위 박스 내부의 버튼들과 프리셋 부분이 겹치는 문제"
   - Row 2 가 X축 + axis seg(SOC/DOD/시간) + Rest + CV + 프리셋 + combobox 로 가로폭 초과 → 시각적 overflow.

2. **데이터 서브탭 구조**: "분리/연결의 경우, 데이터 탭을 사이클별로 나누지 말고 해당 채널에 데이터 셋을 아래로 쌓으면서 출력되도록 변경하자."
   - 현재: 분리/연결 모드에서 (채널×사이클) 조합당 1탭 — 사이클 N=10 + 채널 2개면 20개 탭으로 폭주.
   - 요구: 채널당 1탭 + 사이클을 세로로 누적.

## 변경 1 — 프리셋을 Row 3 으로 분리

`Ui_sitool.setupUi()` 의 데이터 범위 그룹박스 레이아웃:

**Before**:
```
Row 1: [scope: 사이클|충전|방전] [overlap: 이어서|분리|연결] | stretch
Row 2: X축 + [SOC|DOD|시간] + Rest + CV + 프리셋 + combobox | stretch
```

**After**:
```
Row 1: [scope: 사이클|충전|방전] [overlap: 이어서|분리|연결] | stretch
Row 2: X축 + [SOC|DOD|시간] + Rest + CV | stretch
Row 3 (NEW): 프리셋 + combobox | stretch
```

`_profile_opt_row3` (`QHBoxLayout`) 추가, 기존 `_profile_opt_row2` 의 프리셋 위젯들을 그대로 이동. `addItems` / 시그널 / `_apply_profile_preset` 핸들러는 변경 없음 — 위젯 위치만 변경.

세로 공간 +1 행만 소비 (높이 ~28-32px) — 좁은 창에서도 모든 옵션이 명확히 표시됨.

## 변경 2 — `_create_profile_data_subtab` overlap_mode 분기

함수에 `overlap_mode: str = 'continuous'` 파라미터 추가. 동작 분기:

| `overlap_mode` | 동작 |
|---|---|
| `'continuous'` (이어서) | (ch, cyc) 조합당 1탭 — 기존 동작 유지 |
| `'split'` (분리) | 채널당 1탭 + 사이클 세로 누적 |
| `'connected'` (연결) | 채널당 1탭 + 사이클 세로 누적 |

### 누적 알고리즘

```python
by_channel = defaultdict(list)
for (ch_label, cyc_label) in sorted(profile_data_per_combo.keys()):
    by_channel[ch_label].append((cyc_label, df))

for ch_label, parts in by_channel.items():
    _frames = []
    for cyc_label, _df in parts:
        _aug = _df.copy()
        _aug.insert(0, 'Cycle', cyc_label)   # 첫 컬럼에 Cycle 추가
        _frames.append(_aug)
    merged = pd.concat(_frames, axis=0, ignore_index=True, sort=False)
    tbl = _build_table(merged)
    combo_tabs.addTab(tbl, ch_label)
```

**핵심 디자인**:
- `Cycle` 컬럼을 첫 위치에 prepend → 어느 행이 어느 사이클에 속하는지 시각적으로 식별
- `_DECIMALS['Cycle'] = 0` 추가 — 정수형 사이클 라벨 표시
- 컬럼이 다른 사이클 (예: Si 셀의 dQdV 계산 실패) 도 `pd.concat(..., sort=False)` 로 NaN 보정하며 누적
- 탭 라벨 = 채널명만 (사이클 라벨 제거) → 가독성 향상
- 셀 폰트·정렬·스타일은 기존 동일 (Consolas 9pt, AlternatingRowColors, read-only)

### 호출 경로 wiring

`_profile_render_loop` 시그니처에 `overlap_mode: str = 'continuous'` 추가:
- 3개 호출 사이트 (`CycProfile`, `CellProfile`, `AllProfile`) 모두 `overlap_mode=overlap_mode` 전달.
- `unified_profile_confirm_button` 에서 `overlap_mode=options.get('overlap', 'continuous')` 로 wiring.

## 영향 범위 / 호환성

- "이어서" 사용자: 변경 없음 (기존 탭 구조 유지).
- "분리" / "연결" 사용자: 데이터 탭 개수 N → 1 (채널당), `Cycle` 컬럼이 첫 컬럼에 추가됨.
- 그래프 (사이클별 색상, 채널 제어 다이얼로그) 는 변경 없음.

## 변경 대상 위치

| 라인 | 변경 |
|------|------|
| ~11743+ | `_profile_opt_row2` 에서 프리셋 위젯 제거 (CV 다음 stretch 삽입) |
| ~11750+ | `_profile_opt_row3` 신설 + 프리셋 라벨 + combo 이동 |
| 19315+ | `_create_profile_data_subtab` 시그니처에 `overlap_mode` 추가 |
| 19370+ | 분리/연결 분기 — by_channel grouping + Cycle 컬럼 prepend + 세로 concat |
| 19906+ | `_profile_render_loop` 시그니처에 `overlap_mode` 파라미터 추가 |
| 20150, 20338, 20364 | `_create_profile_data_subtab` 호출에 `overlap_mode=overlap_mode` 전달 |
| 26345+ | `_profile_render_loop` 호출에 `overlap_mode=options.get('overlap', 'continuous')` 전달 |

## 검증

### UI Issue 1
1. BDT 재시작 → 사이클데이터 탭 → Profile 패널.
2. 데이터 범위 박스 내부:
   - Row 1: scope + overlap 버튼이 명확히 한 행에 표시.
   - Row 2: X축 + axis 버튼 + Rest + CV 가 한 행에 표시.
   - Row 3: 프리셋 + combobox 가 별도 행에 표시.
3. 좁은 윈도우 폭에서도 위젯 겹침 없이 표시.

### UI Issue 2
1. 정상 경로 로딩 (예: `260326_05_현혜정_6330mAh_LWN`).
2. **이어서 모드**: 데이터 서브탭에 `Q7M_044 cy0014`, `Q7M_044 cy0015`, ... 형식으로 사이클별 탭 표시 (기존 동작).
3. **분리 모드**: 데이터 서브탭에 채널 라벨만 표시 (`Q7M_044`). 탭 클릭 시 첫 컬럼 `Cycle` + 모든 사이클 데이터 세로 누적.
4. **연결 (히스테리시스) 모드**: 분리와 동일 — 채널당 1탭, Cycle 컬럼 prepend.
5. 다채널 (예: 2채널) 시 채널별 색상이 탭 라벨에 반영되는지 확인.

## 회귀 / 후속

- 색상 체계 / 그래프 / CH 다이얼로그 는 변경 없음 — 기존 동작 유지.
- 변경 전후 동일 데이터 비교 시: 사이클별 row 합 = 기존 사이클별 탭 row 합 (Cycle 컬럼 추가만).
