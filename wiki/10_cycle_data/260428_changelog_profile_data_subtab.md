---
title: "프로파일 분석 결과 — '데이터' 서브탭 추가 (사이클 패턴 확장)"
date: 2026-04-28
tags: [feature, profile, ui, qtablewidget, cycle-data]
related:
  - "[[260427_changelog_data_subtab|사이클 데이터 서브탭 (선행 작업)]]"
  - "[[260426_fix_cycle_data_seven_issues]]"
---

# 프로파일 분석 결과 — '데이터' 서브탭 추가

> 사이클 분석 결과 탭의 **'데이터' 서브탭** (260427) 패턴을 프로파일 분석 결과 탭에 동일 적용.
> 그래프 외에 **DataFrame 원본** 을 엑셀 시트 형태로 즉시 확인 가능.

## Context

기존: 프로파일 결과 탭 = canvas 1개 직접 layout 추가. 원본 DataFrame 은 엑셀 export (saveok 체크) 로만 확인.

신규: 결과 탭 inner QTabWidget 에 **'결과 / 데이터' 2개 서브탭**. '데이터' 탭은 (channel × cycle) 조합별 inner-inner 탭으로 구성하여 각 탭이 1개 조합의 full DataFrame 을 read-only QTableWidget 으로 표시.

## 사이클 데이터 탭과의 차이

| 항목 | 사이클 (260427) | 프로파일 (이번) |
|---|---|---|
| 데이터 단위 | (ch, cyc) → 1행 값 | (ch, cyc) → DataFrame (~hundreds of samples) |
| 시트 구성 | 지표별 (방전용량/...) | (ch, cyc) 조합별 |
| 합계 탭 수 | 8~12개 | 채널수 × 사이클수 (가변) |
| inner 탭 | 요약/상세/데이터 (3개) | 결과/데이터 (2개) — 프로파일은 fig2 없음 |

## 구현

### A) `_accumulate_profile_data(...)` helper (신규, L19260 부근)

```python
def _accumulate_profile_data(self, profile_data_per_combo, df, ch_label, cyc_label):
    """profile_data_per_combo[(ch, cyc)] = df.copy() 누적.

    df 가 None / 빈 DF 면 무시. 동일 키 중복 호출은 마지막 호출 기준.
    """
    if df is None or len(df) == 0:
        return
    try:
        profile_data_per_combo[(ch_label, cyc_label)] = df.copy()
    except Exception:
        pass
```

### B) `_create_profile_data_subtab` (신규)

```python
def _create_profile_data_subtab(self, profile_data_per_combo, channel_map):
    """프로파일 데이터 서브탭 위젯 (read-only).

    구조:
        QWidget (root)
        └─ QTabWidget (조합별 inner-inner 탭)
             └─ QTableWidget (행=샘플 인덱스, 열=DataFrame columns)

    - 셀 폰트: Consolas 9pt (사이클 탭과 동일)
    - 헤더/탭 라벨: 앱 기본 (Malgun Gothic)
    - 탭 라벨 색상: channel_map[ch_label]['color']
    - read-only, AlternatingRowColors, Ctrl+C 복사 지원
    - ScrollButtons (다수 탭 대응)
    """
```

소수점 자리수:

| 컬럼 | 자릿수 |
|---|---|
| Voltage / Vol / SOC / DOD | 4 |
| Crate / dQdV / dVdQ / Energy / TimeMin | 3 |
| Temp | 1 |
| 그 외 | 3 (default) |

### C) `_finalize_plot_tab` 시그니처 확장

```python
def _finalize_plot_tab(self, ..., sub2_channel_map=None,
                       data_subtab_widget=None, subtab_titles=None):
    ...
    if data_subtab_widget is not None:
        # 신규 inner QTabWidget 분기
        inner = QTabWidget()
        titles = list(subtab_titles) if subtab_titles else ["결과", "데이터"]
        # 결과 서브탭: 기존 canvas
        ...
        inner.addTab(_s1, titles[0])
        # 데이터 서브탭
        inner.addTab(data_subtab_widget, titles[1])
        tab_layout.addWidget(inner, 1)
    else:
        tab_layout.addWidget(canvas)  # 기존 동작 (회귀 0)
```

`data_subtab_widget=None` default → 기존 호출자 (예: `ect_confirm_button` L26435) 영향 없음.

### D) `_profile_render_loop` — 3가지 view mode 모두 데이터 위젯 빌드

**CycProfile** (채널별 fig):
```python
profile_data_per_combo: dict = {}  # fig 시작 시 초기화
for CycNo in CycleNo:
    ...
    if has_data:
        self._accumulate_profile_data(profile_data_per_combo, _plot_df, ch_label, cyc_label)
# fig 마무리
try:
    _data_widget = self._create_profile_data_subtab(profile_data_per_combo, channel_map)
except Exception as _e:
    logger.warning('프로파일 데이터 서브탭 생성 실패 (CycProfile): %s', _e)
    _data_widget = None
self._finalize_plot_tab(..., data_subtab_widget=_data_widget, subtab_titles=["결과", "데이터"])
```

**AllProfile** (전체 1 fig):
- 루프 시작 전 `all_profile_data_per_combo: dict = {}` 초기화
- 각 (i, j, CycNo) 반복 시 `sub_key` (= ch_label + ' ' + sub_label) 로 누적
- 루프 종료 후 `_create_profile_data_subtab(all_profile_data_per_combo, all_sub_map)` 1회 호출
- 색상 lookup: `all_sub_map` 의 sub_key 가 곧 데이터 dict 의 키 → 탭 라벨 색상 자동 매칭

**CellProfile** (사이클별 fig):
- CycProfile 과 동일 패턴, fig 가 사이클 단위라는 점만 차이
- `profile_data_per_combo` 는 사이클당 1번 초기화

위젯 생성 실패 시 `try/except` 으로 graph 만 표시 (안전 fallback).

## 표시 형식

```
┌──── 프로필 결과 탭 ─────────────────────────────────────────┐
│ [toolbar] [▶ CH 토글]                                      │
│ ┌── inner QTabWidget ──────────────────────────────────┐ │
│ │ [결과] [데이터]                                       │ │
│ ├──────────────────────────────────────────────────────┤ │
│ │  ┌── inner-inner ────────────────────────────────┐ │ │
│ │  │ [Q7M_030 cy0001] [Q7M_030 cy0010] [Gen4_073...│ │ │  ← 탭 라벨 색 = 채널 색
│ │  ├───────────────────────────────────────────────┤ │ │
│ │  │ TimeMin │ SOC    │ Voltage │ Crate │ Temp │... │ │ │
│ │  ├─────────┼────────┼─────────┼───────┼──────┼────┤ │ │
│ │  │ 0.000   │ 0.0000 │ 3.0500  │ 0.000 │ 25.0 │... │ │ │
│ │  │ 0.100   │ 0.0010 │ 3.0512  │ 0.500 │ 25.1 │... │ │ │
│ │  └───────────────────────────────────────────────┘ │ │
│ └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

5개 plot mode 별 컬럼:

| Mode | 주요 컬럼 |
|---|---|
| step | TimeMin, Crate, Vol, Temp |
| chg | TimeMin, SOC, Energy, Voltage, Crate, dQdV, dVdQ, Temp |
| dchg | TimeMin, SOC(=DOD), Energy, Voltage, Crate, dQdV, dVdQ, Temp |
| cycle_soc | SOC, Voltage 등 (충방전 통합) |
| continue | 연속 시간축 (구간 cyc_label="S~E") |

## 검증

- [x] `python -c "ast.parse(...)"` syntax OK
- [x] PR #A helper 신규 (호출자 0)
- [x] PR #B `_finalize_plot_tab` 시그니처 확장 (default None → 기존 호출자 영향 0)
- [x] PR #C `_profile_render_loop` 3가지 view mode 데이터 위젯 빌드
- [ ] 사용자 알파:
  - 5개 plot mode (step/chg/dchg/cycle_soc/continue) × 3개 view mode (Cyc/All/Cell):
    - 결과 탭 클릭 → '결과 / 데이터' 2개 inner 탭
    - 데이터 탭 → (ch, cyc) 조합별 inner-inner 탭
    - 탭 라벨 색상 = 채널 그래프 색상
    - 빈 셀 (NaN) → 빈 문자열
    - Ctrl+C 복사 → 클립보드 탭/줄바꿈 형식
    - `profile_tab_reset` 으로 정리 정상 (메모리 누수 0)
- [ ] 회귀:
  - ECT 모드 (`ect_confirm_button` L26435) — 영향 없음 확인 (default None)
  - Toyo / PNE 양쪽
  - saveok / ect_saveok 엑셀/CSV export 결과 동일

## 위험·롤백

- **위험**: 중간 — `_profile_render_loop` 의 3가지 view mode + 5가지 plot mode 조합. 위젯 생성 try/except 으로 실패 시 graph 만 표시
- **롤백**: 단일 commit revert 1회. `data_subtab_widget=None` default 라 부분 revert 도 가능

## 향후 확장 (별도 PR)

- **2-level 탭 nesting** — 탭이 많아지면 (채널수 × 사이클수 > 30) outer = 채널, inner = 사이클 형태로 nesting
- **CSV 직접 export 버튼** — 데이터 탭 자체에 'Export' 버튼 추가
- **공통 view 모드** — 사이클 데이터 탭과 프로파일 데이터 탭의 헬퍼 통합 (`_create_data_subtab(items, render_fn)` 형태)
- **채널 토글 연동** — CH 컨트롤 토글 시 데이터 탭의 해당 (ch, cyc) 탭 enable/disable
- **ECT 모드 데이터 탭** — `ect_confirm_button` 에도 동일 패턴 적용 (현재는 default 동작 유지)
