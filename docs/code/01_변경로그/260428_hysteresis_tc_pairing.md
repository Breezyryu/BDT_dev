# 히스테리시스 TC 페어링 — TC N + TC N+1 보완 phase 결합

날짜: 2026-04-28
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수:
- `unified_profile_confirm_button()` — `_hyst_pair_state` closure 변수 신설
- `_profile_render_loop()` — `hyst_pair_state` 파라미터 + 사이클 루프에서 `next_temp` prefetch
- `_plot_one()` cycle_soc 의 `_is_hysteresis` 분기 — segment 필터링 + 페어링 plot

## 배경 — 사용자 보고

> "(tc3 방전 + tc4 충전) 조합을 원하는 것이다. 그래야 제대로 된 히스테리시스 비교가 가능하다."
> "위와 같은 케이스를 대비하여 tc offset 기능을 추가하자."

기존 BDT 는 TC 3 의 모든 데이터 (CHG step + DCHG step) 를 한꺼번에 plot.
실제 데이터 구조 (실측):

| TC | CHG step | DCHG step | 의미 |
|---:|---|---|---|
| 2 | 0%→100% (full) | 100%→0% (full) | RPT (참조) |
| 3 | **0%→100%** (RPT 후 만충) | **100%→90%** | Dchg 10% test 사이클 |
| 4 | **90%→100%** (재충전) | **100%→80%** | Dchg 20% test 사이클 |
| 5 | 80%→100% | 100%→70% | Dchg 30% |
| ... | ... | ... | ... |
| 11 | 20%→100% | 100%→10% | Dchg 90% |
| 12 | 10%→100% (재충전) | 100%→0% (full) | RPT/Dchg 100% |

**Dchg 10% 의 닫힌 hysteresis loop (SOC 90~100%)** = TC 3 의 DCHG (100→90% 하단 곡선) + TC 4 의 CHG (90→100% 상단 곡선). TC 3 의 초기 CHG (0→100%) 는 RPT 후 만충일 뿐 hysteresis 와 무관 — 사용자가 본 "긴 꼬리" 의 정체.

## 변경

### 1. `_hyst_pair_state` closure dict 신설

`unified_profile_confirm_button` 에서 hysteresis 라벨 산출 직후:

```python
_hyst_pair_state: dict = {
    'enabled': bool(_hyst_labels),   # classified 가 hysteresis 인식한 경우만
    'next_temp': None,                # 사이클별로 _profile_render_loop 가 갱신
}
```

`enabled` 는 `_hyst_labels` (classified 기반) 가 비어있지 않을 때만 True — 즉 자동 hysteresis 인식 + 페어링.

### 2. `_profile_render_loop` — `next_temp` prefetch

신규 파라미터 `hyst_pair_state: dict | None = None`. CycProfile 사이클 루프 안에서 plot_one_fn 호출 직전:

```python
if (hyst_pair_state is not None
        and hyst_pair_state.get('enabled')
        and isinstance(CycNo, int)):
    _next_cyc = CycNo + 1
    _next_temp = loaded_data.get((i, j, _next_cyc))
    if _next_temp is None:
        _next_temp = fallback_fn(FolderBase, _next_cyc, is_pne)
    hyst_pair_state['next_temp'] = _next_temp
```

`_plot_one` 이 closure 로 `_hyst_pair_state` 를 캡처 — 사이클 처리 중 `state['next_temp']` 가 항상 최신.

### 3. `_plot_one` cycle_soc 의 `_is_hysteresis` 분기 — segment 필터링

기존: 현재 TC 의 Cond=1 (CHG) + Cond=2 (DCHG) 양쪽 모두 plot.

신규 (페어링 활성 시):

| 사이클 방향 | plot 대상 segment |
|---|---|
| `Dchg` (방전 hysteresis) | 현재 TC 의 **Cond=2** (DCHG) + 다음 TC 의 **Cond=1** (CHG) |
| `Chg` (충전 hysteresis) | 현재 TC 의 **Cond=1** (CHG) + 다음 TC 의 **Cond=2** (DCHG) |

```python
if _pair_enabled and _direction == 'Dchg':
    _segments = [(2, p)]                          # 현재 TC DCHG
    if _pair_p is not None:
        _segments.append((1, _pair_p))            # 다음 TC CHG
elif _pair_enabled and _direction == 'Chg':
    _segments = [(1, p)]                          # 현재 TC CHG
    if _pair_p is not None:
        _segments.append((2, _pair_p))            # 다음 TC DCHG
else:
    _segments = [(1, p), (2, p)]                  # 페어링 비활성 — 기존 동작
```

이로써 Dchg 10% (TC 3) 사이클의 plot 은 **SOC 90~100% 의 닫힌 작은 loop** 만 표시 — 초기 만충 충전 (0→100%) 과 다음 사이클의 새 방전 (100→80%) 은 빠짐.

## 동작

페어링 자동 활성 조건: `meta.classified` 가 TC 들을 '히스테리시스(방전)' / '히스테리시스(충전)' 로 인식 + RPT 인접 TC 자동 100% reference 포함 — 모두 자동 동작 (사용자 별도 옵션 불필요).

페어링 비활성 (예: classified 인식 실패, hysteresis 외 모드): 기존 동작 유지 (TC N 의 양 phase 모두 plot).

### 사용자가 본 desired vs current 비교

- **이전 (페어링 없음)**: TC 3 Dchg 10% 색상 = 빨강. 그래프는 0→100% 충전 전체 + 100→90% 방전 = 긴 envelope + 작은 끝점. "분홍/빨강 끝점이 desired 와 다름".
- **신규 (페어링 활성)**: TC 3 Dchg 10% = TC 3 DCHG (100→90%) + TC 4 CHG (90→100%) = SOC 90~100% 의 닫힌 작은 loop. desired image 와 일치.

## 변경 위치

| 라인 | 함수 | 변경 |
|---|---|---|
| ~L19925+ | `_profile_render_loop` 시그니처 | `hyst_pair_state: dict \| None = None` 추가 |
| ~L20302+ | `_profile_render_loop` 사이클 루프 | next_temp prefetch + state 갱신 |
| ~L26200+ | `unified_profile_confirm_button` | `_hyst_pair_state` 신설, _profile_render_loop 호출 시 전달 |
| ~L26250+ | `_plot_one` cycle_soc 의 `_is_hysteresis` | direction 별 segment 필터링 + 다음 TC 의 보완 phase plot |

## 검증

### 데이터 구조 검증 (path 10 — 박성철 Si25%)

```
TC  2: rank=0, Dchg 100%  (RPT 직전 — Dchg 100% reference)
TC  3: rank=20, Dchg 10%  ← 페어링: TC 3 DCHG + TC 4 CHG
TC  4: rank=18, Dchg 20%  ← 페어링: TC 4 DCHG + TC 5 CHG
...
TC 11: rank=4, Dchg 90%   ← 페어링: TC 11 DCHG + TC 12 CHG
TC 12: rank=1, Dchg 100%  (RPT 직후)
```

각 사이클은 인접 TC 의 보완 phase 와 결합되어 닫힌 hysteresis loop 형성.

### GUI 검증 (사용자 측)

1. BDT 재시작 → 사이클데이터 → Profile.
2. 정상 hysteresis 경로 (예: `260326_05_현혜정_6330mAh_LWN`) 로딩.
3. 사이클 + 연결 + SOC + TC 3-12 → 프로필 분석.
4. 각 사이클이 SOC (100-X)% ~ 100% 의 **닫힌 작은 loop** 으로 표시 (긴 꼬리 없음).
5. Pink (Dchg 20%): SOC 80~100% 의 작은 loop, 끝점 SOC 80% 부근.
6. Red (Dchg 10%): SOC 90~100% 의 매우 작은 loop, 끝점 SOC 90% 부근.
7. Black (Dchg 100%, TC 12): 전체 envelope (0~100%).
8. desired image 와 일치하는지 비교 확인.

## 한계 / 후속 작업

1. **per-row TC offset 컬럼 — 미구현**: 사용자가 `tc offset 기능 추가` 요청에 따라 path table 의 col 7 에 "TC 짝" 컬럼 추가하여 행별로 페어링 offset (0/1/-1 등) 지정 가능하게 하는 것은 후속 작업. 현재는 자동 (offset=+1) 만 지원.
2. **AllProfile / CellProfile 모드 페어링 미적용**: 현재 CycProfile 만. AllProfile 에서 다채널 × 다사이클 페어링이 필요하면 추가 작업.
3. **Toyo 미지원**: classified-based 페어링이 .sch 의존이므로 Toyo (CSV) 에서는 자동 인식 안 됨. fallback 으로 기존 동작.
