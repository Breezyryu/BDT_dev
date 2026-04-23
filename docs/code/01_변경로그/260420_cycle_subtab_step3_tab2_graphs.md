# 사이클 서브탭 확장 Step 3 — 상세 탭 2×3 실제 그래프 + 탭1 ax6 AvgV 제거

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
관련 계획: `.claude/plans/4-1-1-proud-ladybug.md`

## 배경

Step 2 에서 도입한 "상세" 서브탭의 placeholder 를 **실제 2×3 그래프** 로 채움. 동시에 탭1 1-6(ax6) 에 중첩돼 있던 AvgV 는 탭2 2-3 으로 이동 — 각 축이 단일 의미로 정리.

## 변경 내용

### 1. 탭1 ax6 AvgV 제거 (`graph_output_cycle`, L3061-3066)

```diff
+ # 1-6 ax6: RndV 단독 (AvgV 는 탭2 2-3 으로 이동됨)
  artists.append(graph_cycle(_x, df.NewData.RndV, ax6, 3.00, 4.00, 0.1,
-             "Cycle", "Rest End Voltage (V)", "_nolegend_", xscale, color))
+             "Cycle", "Rest End Voltage (V)", temp_lgnd, xscale, color))
  artists.append(graph_cycle(_x, df.NewData.Eff2, ax5, 0.996, 1.008, 0.002,
                    "Cycle", "Charge/Discharge Efficiency", temp_lgnd, xscale, color))
- artists.append(graph_cycle_empty(_x, df.NewData.AvgV, ax6, 3.00, 4.00, 0.1,
-                   "Cycle", "Average/Discharge Rest Voltage (V)", temp_lgnd, xscale, color))
```

- `RndV` 의 범례 라벨을 `"_nolegend_"` → `temp_lgnd` 로 복구 (이전에 AvgV 가 범례 전담이었기 때문에 RndV 를 숨김 처리했으나, 이제 RndV 단독이라 정상 표기)
- `place_avgrest_labels(ax6)` 는 `if not avgv_ys or not rndv_ys: return` 가드가 이미 있어 AvgV 데이터 부재 시 자동으로 구분선·라벨 생성 건너뜀 — 추가 수정 불필요

### 2. 신규 함수 `graph_output_cycle_tab2()` (L3099+)

```python
def graph_output_cycle_tab2(df, xscale, temp_lgnd, colorno, graphcolor,
                            ax1, ax2, ax3, ax4, ax5, ax6):
    """탭2(상세) 2×3 그래프 — 용량/전압/에너지 중심.

    ax1: Discharge Capacity Ratio (Dchg)      ← 탭1 1-1 과 동일 참조
    ax2: Charge Capacity Ratio (Chg)
    ax3: Average Discharge Voltage (AvgV)      ← 탭1 ax6 에서 이동
    ax4: Discharge Energy (DchgEng, Wh)
    ax5: Charge Rest End Voltage (RndV_chg_rest, 만충 OCV)
    ax6: Discharge Rest End Voltage (RndV, 방전 후 OCV)
    """
```

- 같은 `colorno`/`graphcolor` 를 받아 **채널 색상 탭1/탭2 자동 일치**
- 컬럼 존재 여부(`dropna().empty`) 가드로 데이터 없는 경우 조용히 skip
- 실패 시 기존 `graph_output_cycle` 와 동일하게 `logger.warning` + 부분 결과 반환

### 3. 호출부 병렬 호출 (연결 모드 L21182+, 비연결 모드 L21272+)

```python
# 기존 (탭1)
_artists, _color = graph_output_cycle(
    _wrapper, xscale, ..., ax1, ax2, ax3, ax4, ax5, ax6)
# 신규 (탭2, 같은 colorno → 색상 일치)
_artists_b, _ = graph_output_cycle_tab2(
    _wrapper, xscale, lgnd, _plot_colorno, graphcolor,
    ax1b, ax2b, ax3b, ax4b, ax5b, ax6b)
_all_artists = _artists + _artists_b
# channel_map 과 sub_channel_map 에 병합된 artists 저장 → 기존 채널 토글 로직
# 가 탭1/탭2 양쪽 artist 를 동시에 제어
```

### 4. Step 2 placeholder 제거 (fig2 생성부 L20990+)

```diff
- # ── 상세(탭2) placeholder figure (Step 2) ──
- # Step 3 에서 실제 그래프 (2×3: ...) 로 덮어씀
- fig2, axes_b_grid = plt.subplots(...)
- axes_list_b = [axes_b_grid[_r][_c] for _r in range(2) for _c in range(3)]
- for _ax_b in axes_list_b:
-     _ax_b.text(0.5, 0.5, '상세 그래프 (Step 3)', ...)
-     _ax_b.set_xticks([]); _ax_b.set_yticks([])
+ # ── 상세(탭2) figure — Step 3: 실제 그래프 ──
+ fig2, axes_b_grid = plt.subplots(nrows=2, ncols=3, figsize=(_fig_w, 8))
+ ax1b, ax2b, ax3b = axes_b_grid[0]
+ ax4b, ax5b, ax6b = axes_b_grid[1]
+ axes_list_b = [ax1b, ax2b, ax3b, ax4b, ax5b, ax6b]
```

axes 변수를 개별 (`ax1b..ax6b`) 로 받아 Step 3 의 `graph_output_cycle_tab2` 호출에 직접 전달 가능하게 변경.

### 5. xlim 동기화 (`_auto_adjust_cycle_axes` 호출 직후 L21334+)

```python
if has_valid_data:
    _auto_adjust_cycle_axes(axes_list, ylimitlow, ylimithigh, xscale)
    # 탭2(상세) xlim 을 탭1 ax1 에 동기화
    _x1_lim = ax1.get_xlim()
    for _ax_b in axes_list_b:
        _ax_b.set_xlim(_x1_lim)
```

- 탭1 에 적용된 xscale 자동 조정 결과를 탭2 axes 에 복사 → 두 서브탭의 x축 범위 완전 일치
- ylim 은 축별 의미가 다르므로 자동 조정 생략 (matplotlib 기본 스케일 사용)

## 탭별 최종 매핑

### 탭 1 (요약)
| 위치 | 지표 | 컬럼 |
|---|---|---|
| 1-1 | Discharge Capacity Ratio | `Dchg` |
| 1-2 | Dchg/Chg Efficiency | `Eff` |
| 1-3 | Temperature | `Temp` |
| 1-4 | DC-IR @ SOC70 | `soc70_dcir` + `soc70_rss_dcir` (또는 `dcir`) |
| 1-5 | Cross Efficiency | `Eff2` |
| 1-6 | **Rest End V** (RndV 단독) | `RndV` |

### 탭 2 (상세)
| 위치 | 지표 | 컬럼 |
|---|---|---|
| 2-1 | Discharge Capacity Ratio | `Dchg` |
| 2-2 | Charge Capacity Ratio | `Chg` |
| 2-3 | Average Discharge Voltage | `AvgV` |
| 2-4 | Discharge Energy | `DchgEng` |
| 2-5 | Charge Rest End V | `RndV_chg_rest` |
| 2-6 | Discharge Rest End V | `RndV` |

## 영향 범위

- `channel_map` 채널 토글 로직 불변 — artist 리스트만 확장되어 양쪽 서브탭에 동일하게 적용
- `sub_channel_map` 도 동일 패턴 (연결 모드)
- 색상 팔레트 인덱스 (`colorno` / `_plot_colorno`) 변동 없음 — 동일 채널 = 동일 색상
- `mkdcir` / 일반 DCIR 모드 모두 탭1 ax4 에 동일하게 반영, 탭2 는 DCIR 무관
- Excel 저장 경로 (`_save_cycle_excel_data`) 는 불변 — Step 4 에서 `Rest End Chg` 시트 추가 예정

## 검증 포인트

- [ ] 사이클 분석 실행 → 외부 탭 내부 "요약" 에 기존 2×3 + ax6 이 **RndV 단독** (AvgV 없음)
- [ ] "상세" 탭에 2×3 그래프 표시 (placeholder 텍스트 사라짐)
- [ ] 2-1 Dchg 가 1-1 과 동일 색상·점 (동일 데이터)
- [ ] 2-2 Chg 가 Dchg 와 유사 형상 (CE 가 100% 근처라 두 곡선이 거의 겹침)
- [ ] 2-3 AvgV 가 3.6~3.9V 영역 scatter (탭1 에서 이동한 값)
- [ ] 2-4 DchgEng 가 Wh 절대값 scatter
- [ ] 2-5 RndV_chg_rest 가 **4.05–4.25V** 근방 (만충 OCV)
- [ ] 2-6 RndV 가 **2.80–3.30V** 근방 (방전 후 OCV, 1-6 과 동일 값)
- [ ] 채널 토글 (▶ CH) → **탭1/탭2 양쪽 artist 동시 dim/highlight**
- [ ] x축 범위 두 탭 완전 일치 (xscale 반영)
- [ ] 각 서브탭 자체 toolbar zoom/pan 독립 작동
- [ ] `saveok` 체크 실행 → 기존 엑셀 시트 구조 불변 (Step 4 에서 확장)

## 다음 단계

- **Step 4**: `_save_cycle_excel_data` 에 `Rest End Chg` 시트 추가 (RndV_chg_rest 전용)
