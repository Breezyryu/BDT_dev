---
title: "[버그수정] 전체통합+다중경로 plot 색상 path 차원 누락 (G6)"
aliases:
  - G6 path color fix
  - Phase 2.5 changelog
tags:
  - profile-analysis
  - changelog
  - bugfix
  - color
  - multi-path
type: changelog
status: applied
related:
  - "[[260428_profile_gap_current_vs_target]]"
  - "[[260428_profile_view_color_spec]]"
  - "[[260428_profile_4modes_spec]]"
created: 2026-04-28
updated: 2026-04-28
---

# [버그수정] 전체통합+다중경로 plot 색상 path 차원 누락 (G6)

> [!abstract] 요약
> 전체통합(`AllProfile`) + 다중 경로(N>1) 분석 시 모든 plot line이 단색(남색 #3C5488 베이스)으로 표시되던 결함 수정. `_get_profile_color('group',...)` 호출에서 `group_idx` 인자가 누락되어 default `0` (남색 베이스)만 사용되던 것을 root cause로 확정 후, 3 단계 수정으로 path 차원을 색상 결정 흐름에 회복.

> 상위 → [[hub_unified_profile]] · 격차 → [[260428_profile_gap_current_vs_target]] §G6

---

## 1. 배경

사용자 보고: `전체통합 + 이어서 + 시간` + 다중 경로 21개 분석 시 모든 plot line이 단색. 우측 "Path (21)" colorbar는 정상 다단계로 보이나 line과 매칭 안 됨.

### Root Cause

```
1. _resolve_profile_color_mode(view_mode='all', n_folders=21, ...)
   → 'group' 반환  ✓ 정상  [proto_.py:3832-3833]
   
2. legacy_mode 분기 _plot_one() (5종 공통)
   → _artists 에 _cycle_id_tag 만 부착  ✗ _path_idx_tag 부재
   
3. 후처리 색상 루프 [proto_.py:20693-20728]
   → _line_cyc_map 만 구성  ✗ _line_path_map 부재
   
4. _get_profile_color('group', ci, n_total, condition=..., is_first=..., is_last=...)
   → group_idx 인자 누락 → default 0  [proto_.py:20744-20749]
   
5. _get_profile_color() group 분기 [proto_.py:3990-4004]
   → group_bases[0 % 4] = (60, 84, 136) 남색 베이스
   → scale = 0.4 + 0.6 × (cycle_idx / max(n−1, 1))
   → 모든 line이 남색 베이스, cycle_idx 농도만 차이 → 사실상 단색
```

이는 **architecture-level 결함** — 5개 legacy_mode (`chg`/`dchg`/`cycle_soc`/`step`/`continue`) **모두** path 차원 미부착.

---

## 2. 변경 (3 단계, +24 라인)

**파일**: `DataTool_dev_code/DataTool_optRCD_proto_.py`

### Change 1 — `_profile_render_loop()` 폴더 루프에서 path_idx tag 일괄 부착

**위치**: 3 군데 (CycProfile / AllProfile / CellProfile 분기 각각)

| 분기 | 위치 | 부착 시점 |
|---|---|---|
| CycProfile | L20384 직후 (try/except 블록 다음) | `has_data = True` 직전 |
| AllProfile | L20485 직후 | `has_any_data = True` 직전 |
| CellProfile | L20578 직후 | `has_data = True` 직전 |

**삽입 코드** (3 군데 동일):
```python
# path_idx tag 일괄 부착 (group 색상 모드용 — 다중 경로 hue 구분)
for _a in _artists:
    if not hasattr(_a, '_path_idx_tag'):
        _a._path_idx_tag = i
```

`i`는 폴더 루프 변수 (`for i, cyclefolder in enumerate(all_data_folder):` L20284).

**전략**: 5 개 `_plot_one()` 콜백 본문은 건드리지 않고, `_profile_render_loop()` 외부에서 일괄 부착. 변경 범위 최소화.

### Change 2 — 후처리 색상 루프에서 `_line_path_map` 구성

**위치**: L20739-20748 (cycle 매핑 직후)

**삽입 코드**:
```python
# ─ path 매핑 (group 모드용 — 다중 경로 hue 구분) ─
_line_path_map: dict[int, int] = {}
if color_mode == 'group':
    for L in _non_rest:
        _pid = getattr(L, '_path_idx_tag', None)
        _line_path_map[id(L)] = int(_pid) if _pid is not None else 0
```

`color_mode == 'group'` 조건으로 group 모드 외에는 빈 dict 유지 (회귀 제거).

### Change 3 — `_get_profile_color()` 호출에 `group_idx` 전달

**위치**: L20758, L20770

**변경**:
```python
ci = _line_cyc_map.get(id(line), 0)
_pi = _line_path_map.get(id(line), 0)   # ← 추가
...
_c, _lw, _a = _get_profile_color(
    color_mode, ci, _n_cycles_detected,
    condition=_cond,
    group_idx=_pi,   # ← 추가
    is_first=_is_first,
    is_last=_is_last,
)
```

---

## 3. 영향 범위

### 긍정적 영향
- ✅ `전체통합 + 이어서 (다중 경로)` — 핵심 시나리오, hue 차원 회복
- ✅ `전체통합 + 충전/방전 (다중 경로)` — 'group' 모드 활성 시 경로별 hue 구분
- ✅ `전체통합 + 사이클+SOC/DOD+분리 (다중 경로)` — 비히스테리시스 분기에서도 적용

### 영향 없음 (회귀 검증)
- 단일 경로 + 모든 옵션 (n_folders=1 → 'group' 미선택)
- 사이클 통합 / 셀별 통합 (path 단일)
- 히스테리시스 모드 (`color_mode == 'chg_dchg'` 우선, group 사용 안 함)

### 회귀 위험
- **낮음**. `_line_path_map`은 `color_mode == 'group'` 일 때만 채워지고, 다른 모드는 `.get(id(line), 0)` → 0 → group_idx 무시 (해당 모드 분기에서 미사용).
- `_path_idx_tag` 부재 시 `getattr(..., None)` 폴백 → 0 → 기존 단색 동작과 동일.
- Tag 부착 시 `if not hasattr(_a, '_path_idx_tag')` 가드로 미래 명시 부착 시 우선권 유지.

---

## 4. 검증

### Syntax 검사
```
$ python -c "import ast; ast.parse(open('DataTool_dev_code/DataTool_optRCD_proto_.py', encoding='utf-8').read()); print('OK')"
OK
```

### 변경 통계
```
$ git diff --stat DataTool_dev_code/DataTool_optRCD_proto_.py
 1 file changed, 24 insertions(+)
```

### 시각 검증 매트릭스 (UI 실행 후 확인)

| 분석 | 통합 | 경로 수 | 기대 결과 |
|---|---|---|---|
| 이어서+시간 | 전체통합 | 2~4 | 4색 hue 명확 구분 |
| 이어서+시간 | 전체통합 | 5~21 | 4색 hue 순환 + cycle 농도 |
| 충전+SOC | 전체통합 | 다중 | 경로별 hue 구분 |
| 방전+DOD | 전체통합 | 다중 | 경로별 hue 구분 |
| 사이클+SOC+분리 | 전체통합 | 다중 | 경로별 hue 구분 |

회귀 검증:
| 분석 | 통합 | 경로 수 | 기대 결과 |
|---|---|---|---|
| 이어서+시간 | 사이클통합 | 다중 | 변경 없음 |
| 이어서+시간 | 전체통합 | 1 | 변경 없음 |
| 사이클+SOC+연결 | 전체통합 | 다중 | 변경 없음 (chg_dchg 사용) |

### 테스트 데이터
사용자 보고 스크린샷의 21경로 셋으로 직접 재현 → 색상 분포 확인 (UI 실행 필요).

---

## 5. 알려진 제한 사항

### 4 색 hue 순환
`_get_profile_color()` group 분기는 `group_bases[group_idx % 4]`로 4색 (남/빨/녹/보) 순환. **5번째 경로부터 1번째와 동일 hue**. cycle_idx 농도로 추가 구분 가능하나 시각 한계 존재.

→ 5+ 경로 hue 확장은 [[260428_profile_view_color_spec]] §6.1 후속 phase에서 검토.

### 히스테리시스 + 다중 경로
히스테리시스 모드는 `is_hysteresis=True` 우선 → `chg_dchg` 모드 (group 무관). 다중 경로 + 히스테리시스 조합에서는 path hue가 적용되지 않음. 별도 phase 검토 필요.

---

## 6. 후속 작업

본 phase는 path 차원 회복만 처리. 격차 매트릭스 ([[260428_profile_gap_current_vs_target]]):
- ✅ G6 (본 phase) — path 차원 색상 회복
- ⏳ G1+G2 (Phase 2) — DOD 좌표계 단순화 (독립)
- ⏳ G3 (Phase 3) — 페어링 자동화
- ⏳ G4 (Phase 4) — UI 분석 종류 라디오
- ⏳ G5 (Phase 5) — dQdV 확대 + GITT/OCV/CCV

---

## 7. 관련 노트

- [[260428_profile_gap_current_vs_target]] §G6 — 격차 정의
- [[260428_profile_view_color_spec]] — 색상 체계 spec (4 색 순환 한계 §6.1)
- [[260428_profile_4modes_spec]] — 4종 분석 spec
- [[hub_unified_profile]] — 코드 아키텍처 hub
- [[260420_hysteresis_preset_cv_and_rainbow_colors]] — 이전 색상 작업 (히스테리시스)
