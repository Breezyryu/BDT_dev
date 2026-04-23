# 사이클 서브탭 확장 Step 2 — 외부 탭 내부에 QTabWidget 중첩 (placeholder)

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
관련 계획: `.claude/plans/4-1-1-proud-ladybug.md`

## 배경

사이클 분석 결과 2×3 (6개) figure 를 **2개 서브탭** (요약/상세) 으로 확장하기 위한 **Step 2 (UI 구조 변경)**. "요약" 에는 기존 tab1 그래프를 그대로 이동, "상세" 는 **빈 2×3 axes + 안내 텍스트** 로 placeholder. 실제 tab2 그래프는 Step 3 에서 덮어씀.

## 변경 내용

### 1. `_finalize_cycle_tab()` 시그니처 확장 (L18882)

기존 파라미터 순서 **완전 보존**, 끝에 2개만 추가:

```python
def _finalize_cycle_tab(self, tab, tab_layout, canvas, toolbar, tab_no,
                        channel_map, fig, axes_list, sub_channel_map=None,
                        classify_info=None, classify_by_group=None,
                        save_context=None, voltage_condition_text=None,
                        group_names=None,
                        extra_figs=None, subtab_titles=None):
```

- `extra_figs`: `list[matplotlib.figure.Figure] | None`. None 이면 기존 단일 canvas 경로 (하위 호환)
- `subtab_titles`: `list[str] | None`. 첫 원소=기본 canvas 라벨, 이후 extra_figs 순

### 2. 분기 로직

- **서브탭 모드** (`extra_figs` 제공):
  - 외부 `toolbar_row` 에는 `toggle_btn` 만 (toolbar 는 서브탭 내부로 이동)
  - `QTabWidget inner` 생성 → subtab 1 에 기존 `toolbar + canvas`, subtab N+1 에 `NavigationToolbar + FigureCanvas(ef)` 쌍
  - 기본 선택: subtab 1 ("요약")
  - 각 extra fig 에 `tight_layout` 개별 적용
- **단일 모드** (`extra_figs is None`):
  - 기존 로직 완전 불변 (회귀 0)

### 3. Toolbar 전략

- 각 서브탭 내부에 **자체 toolbar** → 탭 전환 시 zoom/pan 독립
- 외부에는 토글 버튼만 남아 채널 토글(`_create_cycle_channel_control`) 이 공용으로 작동
- 채널 토글은 Step 2 단계에선 tab1 artist 만 제어 (Step 3 에서 artist 병합)

### 4. 호출부: fig2 placeholder 생성 (L20990+)

`unified_cyc_confirm_button` 폴더 분기에서 기존 `fig` 생성 직후 placeholder figure 추가:

```python
fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(
    nrows=2, ncols=3, figsize=(_fig_w, 8))
axes_list = [ax1, ax2, ax3, ax4, ax5, ax6]

# ── 상세(탭2) placeholder figure (Step 2) ──
fig2, axes_b_grid = plt.subplots(nrows=2, ncols=3, figsize=(_fig_w, 8))
axes_list_b = [axes_b_grid[_r][_c] for _r in range(2) for _c in range(3)]
for _ax_b in axes_list_b:
    _ax_b.text(0.5, 0.5, '상세 그래프 (Step 3)',
               ha='center', va='center',
               transform=_ax_b.transAxes,
               fontsize=10, color='#888')
    _ax_b.set_xticks([])
    _ax_b.set_yticks([])
```

### 5. `_finalize_cycle_tab` 호출부 수정 (L21544)

```python
self._finalize_cycle_tab(
    ...
    group_names=_group_names,
    extra_figs=[fig2],
    subtab_titles=["요약", "상세"])
```

### 6. 에러·데이터 없음 경로에서 fig2 정리

- `try/except` 에서 실패 시 `plt.close(fig)` 직후 `plt.close(fig2)` 추가
- `has_valid_data` 없음 분기의 `plt.close(fig)` 직후 `plt.close(fig2)` 추가

메모리 누수 방지.

## 영향 범위

- Excel 분기 (L20398 근처) 는 **건드리지 않음** — 단일 figure 유지
- ECT 분기 `ect_confirm_button` 의 2×3 figure 도 무관 (별도 경로)
- 기존 탭1 동작 시각적으로 완전 보존 (toolbar 위치만 탭 내부로 이동, 기능 동일)
- `cycle_tab_reset_confirm_button` 등 외부 탭 삭제 시 inner QTabWidget + fig/fig2 모두 Qt 부모 GC 로 자동 정리

## 검증 포인트

- [ ] 사이클 분석 실행 → 외부 탭 선택 시 내부에 **"요약" / "상세"** 서브탭 노출
- [ ] 기본 선택 "요약" 에 기존 2×3 그래프 정상 표시
- [ ] "상세" 에 2×3 빈 axes + 각 칸에 **"상세 그래프 (Step 3)"** 안내 텍스트
- [ ] "요약" toolbar 의 zoom/pan/home 정상 작동
- [ ] "상세" 의 자체 toolbar 도 별도 zoom/pan 가능
- [ ] 외부 toolbar_row 에 toggle_btn (▶ CH) 만 표시 (toolbar 중복 없음)
- [ ] 채널 토글 → "요약" 탭 artist 하이라이트/딤 정상 (Step 2 에선 tab2 artist 없음)
- [ ] `cycle_tab_reset` 으로 전체 탭 닫기 → 메모리 누수 없이 정리
- [ ] 여러 실행 결과 (외부 탭 2개 이상) 간 전환 시 matplotlib 렌더링 충돌 없음
- [ ] `mkdcir` / 일반 DCIR 모드 모두 "요약" 에 기존과 동일한 ax4 표시

## 다음 단계

- **Step 3**: `graph_output_cycle_tab2()` 신규 함수로 "상세" 탭 2×3 실제 그래프 (Dchg/Chg/AvgV/DchgEng/RndV_chg_rest/RndV) + 탭1 ax6 에서 AvgV 제거
- **Step 4**: Excel 에 `Rest End Chg` 시트 추가
