# 프로파일 분석 — plot line 색상 로직 통합 (`_cycle_id_tag` 단일화)

날짜: 2026-04-28
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수:
- `_plot_one` (chg / dchg / cycle_soc / continue / step legacy modes)
- `_plot_and_save_step_data` 호출부

## 배경

5개 legacy mode (`chg`, `dchg`, `cycle_soc`, `continue`, `step`) + cycle_soc 의 hysteresis/non-hyst 분기까지 색상 적용 로직이 mode 별로 일관성 없음:

| Mode | 이전: `_cond_tag` | 이전: `_cycle_id_tag` |
|---|:-:|:-:|
| chg | ✅ all=1 | ❌ 누락 (detection fallback) |
| dchg | ✅ all=2 | ❌ 누락 |
| cycle_soc (hysteresis 페어링) | ✅ | ✅ (이전 commit 에서 추가) |
| cycle_soc (non-hyst) | ✅ | ❌ 누락 |
| step | ✅ (cond per segment) | ❌ 누락 |
| continue | ❌ | ❌ 누락 |

**문제점**:
- 후처리 색상 루프 (`_profile_render_loop` L20684+) 가 `_cycle_id_tag` 부재 시
  Condition 전환 패턴 detection 휴리스틱 (`if _cond == _prev_cond or
  (_prev_cond == 2 and _cond == 1)`) 으로 cycle 경계 추정.
- 이 휴리스틱이 페어링 모드의 segment 순서 (DCHG → CHG) 와 맞지 않아 같은
  사이클의 두 segment 가 서로 다른 cycle_idx 받는 버그 발생 (이전 commit 에서
  hysteresis 만 fix).
- 다른 mode 들도 잠재적 동일 버그 위험.

## 변경

### 모든 plot 함수에 `_cycle_id_tag = CycleNo.index(CycNo)` 명시 부착

**chg legacy** (~L26419):
```python
_cyc_idx = CycleNo.index(CycNo) if CycNo in CycleNo else 0
_a._cond_tag = 1; _a._cycle_id_tag = _cyc_idx
```
6개 axes 모든 artist 동일.

**dchg legacy** (~L26492): 동일 패턴, `_cond_tag = 2`.

**cycle_soc non-hysteresis** (~L26720): Condition 분기 (1=chg, 2=dchg) 의 모든 segment 에 `_cycle_id_tag = _nh_cyc_idx` 부착.

**step legacy** (~L26399): `_plot_and_save_step_data` 호출 후 반환된 `_artists` 에 일괄 부착.
```python
_wc, _arts = self._plot_and_save_step_data(...)
for _a in _arts:
    _a._cycle_id_tag = _cyc_idx
```

**continue legacy** (~L26828): plot 종료 직전 일괄 부착 (이미 `_cycle_id_tag` 가진 artist 는 보존).
```python
for _a in _artists:
    if not hasattr(_a, '_cycle_id_tag'):
        _a._cycle_id_tag = _cyc_idx
```

### 후처리 루프 (변경 없음, 기 적용)

`_profile_render_loop` L20684+ 의 후처리 색상 루프는 이미 `_cycle_id_tag` 우선 사용하도록 수정됨 (이전 commit). 명시 tag 가 모든 mode 에 적용되므로 detection 휴리스틱 fallback 은 사실상 미사용 (무사용 코드 경로 유지 — Condition 컬럼 없는 fallback 케이스 대응).

## 동작 원칙 (post-cleanup)

```
Plot 함수 (mode 별 _plot_one):
  ├─ 각 artist 에 _cond_tag (1/2/3 = chg/dchg/rest) 부착
  ├─ 각 artist 에 _cycle_id_tag (CycleNo 의 index, 0-based) 부착
  ├─ _get_profile_color(mode, cycle_idx, n_total, condition) 로 색상 산출
  └─ artist.set_color(color), artist.set_alpha(alpha) — 초기 색상

후처리 (_profile_render_loop):
  ├─ axes 별로 lines 수집
  ├─ _cycle_id_tag 가 있으면 직접 사용 (휴리스틱 우회)
  ├─ 동일 _get_profile_color 재계산 — idempotent (plot 함수와 같은 결과)
  └─ artist 에 최종 색상·alpha·linewidth 적용

CH 다이얼로그 색상 캐프처:
  └─ post-process 직전 _artists[0].get_color() 캡처 — 명시 tag 기반 색상
     이 plot 함수에서 이미 정확하게 적용되었으므로 캐프처 색상이 후처리 결과와 일치.
```

## 영향 범위

- **모든 모드의 색상 일관성 확보**: 같은 cycle 의 모든 segment (chg + dchg) 가 동일 cycle_idx → 동일 색상.
- **CH 다이얼로그 색상 vs plot 색상 일치**: 후처리가 idempotent 이므로 캐프처 시점 무관.
- **Detection 휴리스틱 의존도 제거**: 명시 tag 우선 → 새로운 mode/protocol 추가 시 휴리스틱 디버깅 불필요.
- **회귀 위험 낮음**: 명시 tag 가 detection 결과와 동일한 cycle_idx 를 산출하면 시각 결과 변화 없음. 다른 경우는 plot 함수의 색상이 정답이므로 후처리 결과가 더 정확해질 뿐.

## 검증

1. 사이클 통합 + 충전 + SOC + 5사이클 이상 → 사이클별 다른 색상으로 정렬 (warm gradient).
2. 사이클 통합 + 방전 + SOC + 5사이클 이상 → cool gradient.
3. 사이클 통합 + 사이클 + SOC + 5사이클 이상 (오버레이) → dual gradient.
4. 사이클 통합 + 연결 + SOC + TC 페어링 ON → chg_dchg rainbow + minor DCHG dim.
5. CH 다이얼로그 사이클 색상 마커가 plot 색상과 일치 (모든 mode).
6. 5사이클 이하 (`distinct` mode) → 후처리 미진입, plot 함수의 PALETTE 5색 적용.

## 후속 작업

- `_get_profile_color` 의 alpha/lw 정책 한 곳에 통합 검토 (현재는 분산: plot 함수 + 후처리).
- `_apply_legend_strategy` 와 색상 로직 분리 점검.
