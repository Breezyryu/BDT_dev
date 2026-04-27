---
title: "사이클 분석 결과 — '데이터' 서브탭 추가 (엑셀 시트 형태 view)"
date: 2026-04-27
tags: [feature, cycle-data, ui, qtablewidget]
related:
  - "[[260426_fix_cycle_data_seven_issues]]"
  - "[[260426_fix_cycle_channel_control_sub_and_tab2_redraw]]"
---

# 사이클 분석 결과 — '데이터' 서브탭 추가

> 사이클 분석 결과 탭 inner QTabWidget 에 **'요약 / 상세 / 데이터' 3개 서브탭** 구성.
> '데이터' 탭에서 `df.NewData` 를 엑셀 시트 형태로 read-only view.

## Context

기존: 결과 탭 = 요약(fig1) + 상세(fig2) 두 그래프 서브탭. 원본 데이터는 엑셀 export (saveok 체크) 로만 확인 가능.

신규: 그래프 외에 **원본 수치 데이터를 즉시 화면에서** 확인 가능. `_save_cycle_excel_data` 와 동일한 시트 구성 (방전용량/충전용량/효율/평균전압/방전Energy/Rest End/DCIR/...) 으로 통일.

## 구현

### A) `_cycle_sheet_specs(nd)` helper (L20492)

엑셀 시트·데이터 탭 공통 spec 리스트. `_save_cycle_excel_data` 의 시트 구성과 동일 순서·이름.

```python
def _cycle_sheet_specs(self, nd):
    """Returns: [(sheet_name, value_col, custom_header_or_None), ...]"""
    specs = []
    specs.append(("방전용량", "Dchg", None))
    specs.append(("Rest End", "RndV", None))
    if "RndV_chg_rest" in nd.columns and not nd["RndV_chg_rest"].dropna().empty:
        specs.append(("Rest End Chg", "RndV_chg_rest", None))
    specs.append(("평균 전압", "AvgV", None))
    specs.append(("충방효율", "Eff", None))
    specs.append(("충전용량", "Chg", None))
    specs.append(("방충효율", "Eff2", None))
    specs.append(("방전Energy", "DchgEng", None))
    # DCIR — mkdcir 모드 분기
    _has_mkdcir = (self.mkdcir.isChecked()
                   and "dcir2" in nd.columns
                   and not nd["dcir2"].dropna().empty)
    if _has_mkdcir:
        if "soc70_dcir" in nd.columns and not nd["soc70_dcir"].dropna().empty:
            specs.append(("SOC70_DCIR", "soc70_dcir", None))
            specs.append(("SOC70_RSS", "soc70_rss_dcir", None))
        specs.append(("RSS", "dcir", None))
        specs.append(("DCIR", "dcir2", None))
        specs.append(("RSS_OCV", "rssocv", None))
        specs.append(("RSS_CCV", "rssccv", None))
    else:
        specs.append(("DCIR", "dcir", None))
    if "ChgVolt" in nd.columns:
        specs.append(("충전전압", "ChgVolt", ["ChgVolt(V)"]))
    if "DchgVolt" in nd.columns:
        specs.append(("방전전압", "DchgVolt", ["DchgVolt(V)"]))
    return specs
```

기존 `_save_cycle_excel_data` 는 변경 없음 (회귀 0). 향후 두 함수 통합 가능.

### B) `_accumulate_cycle_sheets` helper (L19062 부근)

graph_output_cycle 호출 직후 nd → sheets_per_channel 누적:

```python
def _accumulate_cycle_sheets(self, sheets_per_channel, nd, ch_label):
    """sheets_per_channel = { sheet_name: { ch_label: pd.Series(index=OriCyc) } }"""
    if nd is None or len(nd) == 0 or 'OriCyc' not in nd.columns:
        return
    specs = self._cycle_sheet_specs(nd)
    for sheet_name, value_col, _custom in specs:
        if value_col not in nd.columns:
            continue
        sub = nd[['OriCyc', value_col]].dropna(subset=[value_col])
        if sub.empty:
            continue
        series = pd.Series(
            sub[value_col].values,
            index=sub['OriCyc'].astype(int).values,
            name=ch_label,
        )
        sheets_per_channel.setdefault(sheet_name, {})[ch_label] = series
```

### C) `_create_cycle_data_subtab` 위젯 (L19101)

```python
def _create_cycle_data_subtab(self, sheets_per_channel, channel_map):
    """엑셀 시트 형태 데이터 서브탭 위젯 (read-only).

    구조:
        QWidget (root)
        └─ QTabWidget (지표별 inner-inner 탭: 방전용량, 충전용량, ...)
             └─ QTableWidget (행=OriCyc, 열=채널)
                 - 헤더 색상: channel_map[col]['color']
                 - 셀 우측 정렬, monospace (Consolas 9pt)
                 - 시트별 소수점 자릿수 (용량=4, 전압=3, DCIR=1, Eff=4)
                 - read-only (NoEditTriggers, ItemIsSelectable|Enabled)
                 - Ctrl+C 복사 (QTableWidget 기본)
    """
```

특징:
- 빈 셀 (NaN) → 빈 문자열
- 행=OriCyc 합집합 정렬 (모든 채널의 OriCyc union)
- 채널별 Series 가 일부 OriCyc 만 있으면 다른 행은 빈 셀
- AlternatingRowColors 로 시인성

### D) `_finalize_cycle_tab` 시그니처 확장 (L19190)

```python
def _finalize_cycle_tab(self, tab, tab_layout, canvas, toolbar, tab_no,
                        channel_map, fig, axes_list, sub_channel_map=None,
                        ..., extra_figs=None, subtab_titles=None,
                        data_subtab_widget=None):    # ★ 신규
    ...
    # extra_figs 루프 끝에 한 줄 추가
    if data_subtab_widget is not None:
        _data_idx = 1 + len(extra_figs)
        _data_title = (titles[_data_idx]
                       if len(titles) > _data_idx else "데이터")
        inner.addTab(data_subtab_widget, _data_title)
```

`data_subtab_widget=None` default → 기존 호출자 영향 없음.

### E) `unified_cyc_confirm_button` 호출자 변경 (L21461·21665·21766·22086)

1. 탭 단위 loop 시작 시 `sheets_per_channel: dict = {}` 초기화
2. 연결 모드 graph_output_cycle 호출 직후 `_accumulate_cycle_sheets(sheets_per_channel, merged_df, sub_label)`
3. 비연결 모드 graph_output_cycle 호출 직후 `_accumulate_cycle_sheets(sheets_per_channel, cyctemp[1].NewData, sub_label)`
4. `_finalize_cycle_tab` 호출 직전:
   ```python
   _data_widget = self._create_cycle_data_subtab(sheets_per_channel, channel_map)
   ```
5. `_finalize_cycle_tab` 에 `subtab_titles=["요약", "상세", "데이터"]` + `data_subtab_widget=_data_widget` 전달

위젯 생성 실패 시 `try/except` 로 graph 만 표시 (안전 fallback).

## 표시 형식

```
┌─────────┬──────────┬──────────┬──────────┐
│ OriCyc  │ Q7M_030  │ Q7M_031  │ Gen4_073 │   ← 헤더 (channel_map 색상)
├─────────┼──────────┼──────────┼──────────┤
│   1     │  1.0000  │  0.9985  │  1.0010  │
│   2     │  0.9970  │  0.9952  │  0.9981  │
│  ...    │   ...    │   ...    │   ...    │
└─────────┴──────────┴──────────┴──────────┘
```

| 시트 | 컬럼 | 소수점 |
|---|---|---|
| 방전용량 / 충전용량 | Dchg / Chg | 4 |
| 충방효율 / 방충효율 | Eff / Eff2 | 4 |
| 평균 전압 / Rest End / Rest End Chg | AvgV / RndV / RndV_chg_rest | 3 |
| 충전전압 / 방전전압 | ChgVolt / DchgVolt | 3 |
| 방전Energy | DchgEng | 3 |
| DCIR / RSS / SOC70_DCIR / SOC70_RSS | dcir / dcir2 / soc70_* | 1 |
| RSS_OCV / RSS_CCV | rssocv / rssccv | 3 |

## 검증

- [x] `python -c "ast.parse(...)"` syntax OK
- [ ] 사용자 알파:
  - 결과 탭 클릭 → '요약 / 상세 / **데이터**' 3개 서브탭
  - 데이터 탭 → 지표별 inner-inner 탭 (방전용량, 충전용량, 효율, ...)
  - 각 표 행=OriCyc, 열=채널 (헤더 색상 = 그래프 색상)
  - 빈 셀 (NaN) = 빈 문자열
  - Ctrl+C 복사 → 클립보드에 탭/줄바꿈 형식
  - mkdcir on/off 분기: DCIR 시트 수 차이 (1개 vs 6개)
  - `cycle_tab_reset` 으로 정리 정상 (메모리 누수 0)
- [ ] 회귀:
  - 엑셀 export (`_save_cycle_excel_data`) 결과 동일
  - Toyo / PNE 양쪽
  - 사이클통합 / 셀별통합 / 전체통합 / 코인셀 4가지 모드

## 위험·롤백

- **위험**: 낮음 — `data_subtab_widget=None` default 로 기존 호출자 영향 0. 위젯 생성 실패 시 graph 만 표시 (try/except).
- **롤백**: 단일 commit revert 1회.

## 향후 확장 (별도 PR)

- **편집 가능한 입력 컬럼** — 스웰링 측정값 입력. `_update_ect_columns_state` 패턴 재사용. QSettings 또는 별도 파일 영속화
- **CSV/Excel 직접 export 버튼** — 데이터 탭 자체에 'Export' 버튼 추가
- **채널 토글과 데이터 탭 연동** — CH 토글 시 데이터 탭의 채널 컬럼도 숨김
- **`_save_cycle_excel_data` 와 통합** — `_cycle_sheet_specs` 기반 단일 진입점으로 리팩토링 (현재는 분리 유지)
