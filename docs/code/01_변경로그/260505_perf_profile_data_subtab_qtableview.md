# 260505 — 프로파일 데이터 서브탭 QTableView 전환 (40s → 20ms)

## 요약

`unified_profile_confirm_button` 이 30 cycle 분석에서 **49.9s** 소요되는 문제 해결.
원인은 `_create_profile_data_subtab` 의 `QTableWidget` 셀당 `QTableWidgetItem`
미리 생성 패턴 (~15µs/cell) — 331,000 행 × 8 컬럼 = 2.6M 셀에서 **40.8s** 폭발.

해결: `QTableView` + 커스텀 `QAbstractTableModel` (DataFrame wrap, lazy 렌더).

## 사용자 보고

- 데이터: M47 ATL ECT parameter3 (가속수명 [sch], 30 ACCEL cycle, 331,000 행)
- 모드: legacy_mode=continue (이어서, overlap=continuous)
- 측정:
  ```
  [perf] cyc-loop (1/2): 0.103s (plot_one×1=0.089s, overhead=0.013s)
  [perf] _create_profile_data_subtab: 40.845s (combos=1, overlap=continuous)
  [perf] _finalize_plot_tab: 0.053s
  [perf] _profile_render_loop: 41.208s
  ```

## 원인 분석

### 위치

[DataTool_optRCD_proto_.py:_build_table](../../../DataTool_dev_code/DataTool_optRCD_proto_.py)
(bcee163 / 2026-04-28 — "프로파일 분석 결과에 데이터 서브탭" 추가 시 도입)

### 메커니즘

```python
for ri in range(n_rows):              # 331,000
    for ci, col in enumerate(df.columns):  # 8
        _it = QTableWidgetItem(_txt)
        _it.setFont(_cell_font)
        _it.setTextAlignment(...)
        _it.setFlags(...)
        tbl.setItem(ri, ci, _it)
```

- 셀당 비용 = item 생성 + 4 setter + setItem ≈ 15µs (PyQt6 측정)
- 2.6M × 15µs = **40s**
- continuous 모드에서 `combos=1` 이지만 단일 DataFrame 이 31만 행 (전체 TC 연속) → 최악 케이스

### 사용자 인지 vs 실제 도입

- 사용자 인지: "최근 커밋 (Phase 0-5 v3 / 분류기 / Layer A 등) 이후 느려졌다"
- 실제 원인: bcee163 (1주 전, 2026-04-28) 의 데이터 서브탭 기능
- 최근 커밋들과 무관. 사용자가 30 cycle 연속 분석을 처음 시도했거나 누적 데이터
  규모가 커지면서 임계점 통과로 체감.

## 수정

### 1. `_PandasTableModel(QAbstractTableModel)` 도입

`_create_profile_data_subtab` 내부 nested class. DataFrame 을 wrap, view 가
가시 영역에 대해서만 `data()` 호출 받음.

```python
class _PandasTableModel(QAbstractTableModel):
    def __init__(self, df, decimals_map, cell_font, parent=None):
        super().__init__(parent)
        self._cols = [str(c) for c in df.columns]
        self._values = df.to_numpy()
        self._n_rows = len(df)
        self._n_cols = len(df.columns)
        self._cell_font = cell_font
        self._col_decimals = [decimals_map.get(c, 3) for c in self._cols]

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else self._n_rows

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else self._n_cols

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            v = self._values[index.row(), index.column()]
            if v is None or (isinstance(v, float) and v != v):
                return ""
            try:
                return f"{float(v):.{self._col_decimals[index.column()]}f}"
            except (TypeError, ValueError):
                return str(v)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return _align_role
        if role == Qt.ItemDataRole.FontRole:
            return self._cell_font
        return None
```

### 2. `_build_table` 를 QTableView + model 로 교체

- `QTableWidget(n_rows, n_cols)` + 셀당 item → `QTableView` + `setModel(model)`
- 컬럼 너비: `ResizeToContents` (전체 행 비용) 대신 sample 50 행 기반 추정으로 변경
- Ctrl+C / Ctrl+A 단축키는 `selectionModel().selectedIndexes()` 기반 인라인
  helper `_install_view_copy_shortcut` 로 분리 (기존 `_install_data_table_copy_shortcut`
  은 `QTableWidget` 전용이라 그대로 유지 — `_create_cycle_data_subtab` 등에서 사용)

### 3. 진단 timing 로그 (검증용 임시)

[`_profile_render_loop`](../../../DataTool_dev_code/DataTool_optRCD_proto_.py)
와 [`unified_profile_confirm_button`](../../../DataTool_dev_code/DataTool_optRCD_proto_.py)
에 perf log 4 종 추가:

- `cyc-loop (i/N): X.XXXs (plot_one×n=Y.YYYs, overhead=Z.ZZZs)`
- `_create_profile_data_subtab: X.XXXs (combos=N, overlap=...)`
- `_finalize_plot_tab: X.XXXs`
- `_profile_render_loop: X.XXXs (legacy_mode=..., color_mode=..., ...)`

→ 검증 후 별도 commit 으로 제거 예정.

## 효과

### 측정 (Python REPL 단위 테스트, 331k×8 DataFrame)

| 방식 | setup 시간 |
|---|---|
| `QTableWidget` + 셀당 item | 40,845 ms |
| `QTableView` + `_PandasTableModel` | **11.3 ms** |

3,600x 가속.

### 메모리

- 기존: 셀당 `QTableWidgetItem` = 약 64 byte × 2.6M = 166 MB
- 신규: 모델 1개 + numpy view = 수 MB
- DataFrame 자체는 동일 (df.to_numpy() 는 view 가능한 경우 zero-copy)

### 동작 보존

- read-only ✓
- 다중 셀 선택 + Ctrl+C 복사 ✓ (_install_view_copy_shortcut)
- Ctrl+A 전체 선택 ✓
- 우측 정렬 + 모노스페이스 폰트 ✓
- 탭 라벨 색상 ✓
- 알터네이팅 행 색상 ✓
- 컬럼 자동 너비 (sample 기반) ✓

## 검증 방법

같은 데이터 (M47 ATL ECT parameter3) 로 30 cycle 연속 분석 재실행:

```
c:\Users\Ryu\battery\python\BDT_dev\.venv\Scripts\python.exe -u
  "c:\Users\Ryu\battery\python\BDT_dev\DataTool_dev_code\DataTool_optRCD_proto_.py"
```

기대 로그:
```
[perf] _create_profile_data_subtab: 0.0XXs (combos=1, overlap=continuous)
[perf] _profile_render_loop: 0.XXXs
unified_profile_confirm_button 완료  [< 2s]
```

## 후속

1. timing 로그 제거 (검증 통과 후)
2. `_create_cycle_data_subtab` 도 동일 패턴으로 전환 검토 — 현재는 데이터
   규모가 작아 (사이클 수 × 채널 수 = 수백~수천 셀) 즉시 성능 이슈 없음
3. Layer A 단일화 (5d72c53) 의 메모리 ~10-30% 증가 영향은 별도. continuous
   모드에서 raw 가 cycle scope 으로 항상 로드되는 비용 — 데이터 서브탭이
   해소됐으므로 실측 후 필요 시 별도 PR.

## 관련 commit / 파일

- 원인 도입: bcee163 (2026-04-28) `[기능추가] 프로파일 분석 결과에 데이터 서브탭`
- 수정: 본 변경
- 영향 범위: `_create_profile_data_subtab` 단일 메서드 + 그 내부 helper 만.
  외부 인터페이스 (return type=QWidget) 보존.
