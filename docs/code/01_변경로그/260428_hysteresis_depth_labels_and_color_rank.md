# 히스테리시스 사이클 라벨/색상 — 깊이 기반 (Dchg/Chg X%) 으로 교체

날짜: 2026-04-28
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수:
- `_compute_tc_hysteresis_labels()` (신규, ~L917)
- `_build_depth_rank_map()` (신규, ~L975)
- `unified_profile_confirm_button()` (~L25997)
- `_plot_one()` cycle_soc 의 `_is_hysteresis` 분기 (~L26181)

## 배경

기존 히스테리시스 분석 (overlap=connected) 은 사이클을 **시간순 (Cy0003 → Cy0011)** 으로 라벨링·rainbow 색상. 사용자 요구는 **방전/충전 깊이 (DOD/SOC delta) 기준**:

- 방전 hysteresis (TC 3-12): `Dchg 100%` (가장 큰 envelope, 검정) ~ `Dchg 10%` (가장 작은 loop, 빨강)
- 충전 hysteresis (TC 14-23): `Chg 100%` ~ `Chg 10%` 동일 규칙

원하는 출력 형태: 사용자 제공 "방전 0.2C-10min rest" 참조 plot — 깊이 100% 가 검정, 10% 가 빨강.

## 변경 내용

### 1. 신규 헬퍼 — `_compute_tc_hysteresis_labels` (L917)

```python
def _compute_tc_hysteresis_labels(
    channel_path: str,
    capacity_mah: float,
) -> dict[int, dict]:
    """SaveEndData 에서 TC 별 히스테리시스 라벨·깊이 산출.
    
    TC 시작 SOC 위치로 phase 결정 (>0.5 → Dchg, ≤0.5 → Chg).
    깊이 = max(ChgCap, DchgCap) / 정격용량, 10% 단위 라운딩 후 [10, 100] 클램프.
    """
```

반환 형식:
```python
{tc: {'direction': 'Dchg'|'Chg', 'depth_pct': int (10~100), 'depth_raw': float}}
```

**Phase 판별 디자인**: 히스테리시스 사이클은 충·방전이 거의 균형 (예: SOC100→SOC10→SOC100) 이므로 ChgCap vs DchgCap 비교는 fragile. 대신 `_compute_tc_soc_offsets` 를 호출하여 각 TC 의 시작 SOC 를 얻고, `> 0.5` → 'Dchg' phase, `≤ 0.5` → 'Chg' phase 로 판별.

**깊이 산출**: `max(ChgCap, DchgCap)` 을 정격용량 대비 % 로 환산, `int(round(x/10))*10` 로 10% 단위 라운딩 (Python banker's rounding 회피), `[10, 100]` 클램프.

### 2. 신규 헬퍼 — `_build_depth_rank_map` (L975)

```python
def _build_depth_rank_map(labels: dict[int, dict]) -> dict[int, int]:
    """깊이 내림차순 rank — rank 0 = deepest (검정), rank N-1 = shallowest (빨강)."""
    sorted_tcs = sorted(labels.keys(), key=lambda tc: (-labels[tc]['depth_pct'], tc))
    return {tc: rank for rank, tc in enumerate(sorted_tcs)}
```

`_get_profile_color('chg_dchg', rank, n_total)` 의 norm = rank/(n-1) → `_HYST_RAINBOW_STOPS` 자동 매핑 (rank 0 = `#000000` 검정, rank N-1 = `#FF3333` 빨강). **palette 변경 불필요**.

### 3. `unified_profile_confirm_button` 사전 산출 (L25997)

`overlap == 'connected'` 일 때 첫 폴더의 max-TC 채널을 대표로 라벨·rank 사전 산출:

```python
_hyst_labels: dict[int, dict] = {}
_hyst_ranks: dict[int, int] = {}
if options.get('overlap') == 'connected' and all_data_folder:
    try:
        # ... best_ch 선택, _compute_tc_hysteresis_labels + _build_depth_rank_map
        _hyst_labels = _compute_tc_hysteresis_labels(_best_ch, _cap)
        _hyst_ranks = _build_depth_rank_map(_hyst_labels)
    except Exception as _e:
        logger.warning('히스테리시스 라벨 산출 실패, chronological fallback: %s', _e)
```

빈 dict 폴백 → 기존 chronological 동작 유지 (Toyo 또는 SaveEndData 부재 케이스).

### 4. `_plot_one` cycle_soc 의 `_is_hysteresis` 분기 (L26181)

```python
if _is_hysteresis:
    _htype = getattr(temp[1], '_hyst_type', 'minor')
    _is_major = (_htype == 'major')
    # 깊이 기반 라벨·rank 가용 시 사용, 아니면 chronological fallback
    if _hyst_labels and CycNo in _hyst_labels:
        _info = _hyst_labels[CycNo]
        _new_lgnd = f"{_info['direction']} {_info['depth_pct']}%"
        _cyc_idx = _hyst_ranks.get(CycNo, 0)
        _n_cyc = len(_hyst_ranks) or len(CycleNo)
    else:
        _new_lgnd = temp_lgnd
        _cyc_idx = CycleNo.index(CycNo) if CycNo in CycleNo else 0
        _n_cyc = len(CycleNo)
```

이후 `graph_profile(..., temp_lgnd)` → `graph_profile(..., _new_lgnd)` 로 교체. ax3 (V-x 두 번째 axis) 는 `'_nolegend_'` 그대로. cond=2 (방전 세그먼트) 도 `_nolegend_` 처리 — 한 사이클 당 범례 1개만 표시 (Dchg X% 또는 Chg X%).

## 데이터 검증

`test_code/hysteresis_label_validator.py` 신규 — 16개 hysteresis 경로 일괄 검증:

| 결과 | 개수 | 비고 |
|---|---|---|
| ✅ PASS | 14 | TC 3-12 의 ≥50% 가 'Dchg', TC 14-23 의 ≥50% 가 'Chg', depth_pct 가 [10,100] 범위 |
| ⚠️ WARN | 2 | path 11 (재측정, TC 1-13만), path 16 (after 3.0C HT800cy, 깊이 max=80%) — direction heuristic edge 케이스 |
| ❌ FAIL | 0 | |

**핵심 결과 — 모든 경로의 depth_pct 가 [100, 90, 80, ..., 10] 일관**: depth 검출 알고리즘 안정. direction heuristic 은 SOC anchor 가 정상 작동하는 케이스에서 정확.

WARN 케이스 분석:
- path 11 "충전 재측정": 파일명 자체가 "충전 재측정" — TC 3-12 가 사실상 충전 hysteresis 일 가능성. heuristic 결과 `'Chg'` 가 실제 의도와 일치할 수 있음.
- path 16 "after 3.0C HT800cy": 800 사이클 노화 후 측정 — 가용용량 감소로 깊이 max 80% 가 정상. direction 혼합은 anchor shift 후 SOC 분포 영향.

## 회귀 / 영향 범위

- 비-히스테리시스 모드 (이어서/분리) 의 라벨·색상: **변경 없음** (`_hyst_labels = {}` 폴백).
- chronological fallback: SaveEndData 부재 / Toyo / 라벨 산출 실패 시 기존 동작 유지.
- 5사이클 이하 (`color_mode == 'distinct'`): `_HYST_RAINBOW_STOPS` 미사용으로 영향 없음.
- 후처리 색상 루프 (L20463+): `_cyc_idx` 가 깊이 rank 로 변경되므로 동일 depth-based 색상이 후처리에서 재계산 (idempotent).
- CH 채널 제어 다이얼로그: `sub2_channel_map[label]['color']` 가 `_artists[0].get_color()` 자동 추출 — 깊이 기반 색상이 다이얼로그에 자동 반영.

## 변경 위치 요약

| 라인 | 함수 | 변경 |
|---|---|---|
| ~L917 | `_compute_tc_hysteresis_labels` (신규) | TC → {direction, depth_pct, depth_raw} dict 산출 |
| ~L975 | `_build_depth_rank_map` (신규) | 깊이 내림차순 rank 매핑 |
| ~L25997 | `unified_profile_confirm_button` | 히스테리시스 시 사전 라벨·rank 산출 |
| ~L26181-26257 | `_plot_one` cycle_soc 의 `_is_hysteresis` 분기 | `_cyc_idx`·`temp_lgnd` 깊이 기반으로 교체 |

후처리 루프 (L20463+), `_get_profile_color` (L3801), `_HYST_RAINBOW_STOPS` (L3713), `_make_short_legend` (L3852), `_compute_tc_soc_offsets` (L861) 는 **변경 없음**.

## 검증 (E2E, 사용자 측)

1. BDT 재시작 → 사이클데이터 → Profile.
2. 정상 경로 (예: `260326_05_현혜정_6330mAh_LWN`) 로딩 → 사이클 + 연결 + SOC + TC 3-12 → 프로필 분석.
3. 범례에 `Dchg 100%` ~ `Dchg 10%` 표시 확인 (기존 `Cy0003 dchg` 가 아님).
4. 가장 큰 envelope = 검정, 가장 작은 loop = 빨강 확인 — 사용자 제공 desired plot 과 일치.
5. CH 채널 제어 다이얼로그의 사이클 라벨도 `Dchg X%` 표시.
6. TC 14-23 으로 변경 → `Chg 100%` ~ `Chg 10%` 표시.
7. Toyo 데이터 또는 distinct 모드 (5사이클 이하) → chronological 라벨로 fallback.

## 후속 작업 (필요 시)

- direction heuristic edge 케이스: WARN 경로의 phase 판별 정확도 개선. 옵션 — `.sch` 프로토콜 파싱하여 step type sequence 로 phase 결정 (현재 휴리스틱은 SOC 분포 기반).
- Toyo SaveEndData 미존재 — Toyo 사이클 데이터에서도 깊이 산출 가능하도록 확장.
