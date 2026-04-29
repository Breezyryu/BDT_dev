---
title: "프로파일 그래프 구성·색상 체계 — Spec"
aliases:
  - Profile View Color Spec
  - 그래프 구성·색상 체계
tags:
  - profile-analysis
  - spec
  - color
  - tab-structure
  - view-mode
type: spec
status: draft
related:
  - "[[260428_profile_4modes_spec]]"
  - "[[260428_profile_gap_current_vs_target]]"
  - "[[hub_unified_profile]]"
  - "[[260420_hysteresis_preset_cv_and_rainbow_colors]]"
  - "[[260412_profile_legend_unification]]"
created: 2026-04-28
updated: 2026-04-28
---

# 프로파일 그래프 구성·색상 체계 — Spec

> [!abstract] 요약
> 프로파일 plot의 **그래프 구성 차원**(경로/채널/사이클) × **탭 구조**(단일탭/다중탭) × **색상 체계**(hue/gradient/depth)를 명세한다. 4종 분석([[260428_profile_4modes_spec]])과 직교하는 차원으로, 분석 종류와 무관하게 동일하게 작동.

> 상위 → [[hub_unified_profile]] · 4종 분석 → [[260428_profile_4modes_spec]] · 격차 → [[260428_profile_gap_current_vs_target]]

---

## 1. 그래프 구성 차원

프로파일 분석 plot은 다음 3차원의 데이터를 다룬다:

| 차원 | 의미 | 예시 |
|---|---|---|
| **경로 (path)** | 실험 그룹 / 시험 폴더 | `0.5C-10min volt hysteresis`, `1C cycling@45deg` |
| **채널 (channel)** | 한 경로 내의 셀 채널 | `M01Ch001`, `M01Ch016` |
| **사이클 (cycle)** | 한 채널의 사이클 번호 | TC 1, TC 2, ..., TC 100 |

각 plot line은 (경로, 채널, 사이클) 트리플로 식별된다.

---

## 2. 탭 구조 (Figure 단위)

현재 UI 라디오 그룹: `CycProfile` / `CellProfile` / `AllProfile` (사이클 통합 / 셀별 통합 / 전체 통합)

| 통합 모드 | Figure 단위 | 한 figure 내 라인 의미 | 탭 수 |
|---|---|---|---|
| **사이클 통합 (CycProfile)** | 채널당 1 figure | 같은 채널의 N개 사이클 | 채널 수 |
| **셀별 통합 (CellProfile)** | 사이클당 1 figure | 같은 사이클의 N개 채널 | 사이클 수 |
| **전체 통합 (AllProfile)** | 1 figure | (모든 경로 × 채널 × 사이클) | 1 |

### 2.1 의도

- **사이클 통합**: 한 셀의 사이클 진행에 따른 변화 추적 (열화 곡선)
- **셀별 통합**: 같은 사이클을 채널 간 비교 (셀 분산)
- **전체 통합**: 전체 그림 한눈에 보기

### 2.2 코인셀 옵션

`chk_coincell_cyc` 체크박스 — 코인셀 데이터 시 메타 처리 분기. 현재 동작 유지.

---

## 3. 색상 체계

### 3.1 색상 결정 트리

```
입력: (analysis_mode, n_paths, n_channels, n_cycles, view_mode)
  │
  ├─ analysis_mode == "히스테리시스"
  │   → chg_dchg 모드
  │       Major: _HYST_RAINBOW_STOPS (10색, depth 기반)
  │       Minor: _HYST_RAINBOW_STOPS (10색, depth 기반)
  │
  ├─ view_mode == AllProfile (전체통합)
  │   ├─ n_paths > 1 → group 모드 (경로별 베이스 hue 4색 × 사이클 농도)
  │   ├─ 충전+방전 동시 (cycle 데이터) → dual 모드 (warm/cool 이원)
  │   ├─ N_total ≤ 5 → distinct 모드 (범주형 5색)
  │   └─ N_total > 5 → warm 또는 cool 그라디언트 (분석 종류에 따라)
  │
  ├─ view_mode == CycProfile (사이클 통합)
  │   N_lines = N_cycles
  │   ├─ 분석 == 충전 → warm 그라디언트
  │   ├─ 분석 == 방전 → cool 그라디언트
  │   ├─ 분석 == 전체 프로파일 → distinct (≤5) / dual (>5, 충방전 모두)
  │   └─ N_cycles ≤ 5 → distinct
  │
  └─ view_mode == CellProfile (셀별 통합)
      N_lines = N_channels
      ├─ N_channels ≤ 5 → distinct
      └─ N_channels > 5 → cool 그라디언트 (또는 distinct extended)
```

### 3.2 색상 모드 정의

| 모드 | 용도 | 팔레트 | 그라디언트 |
|---|---|---|---|
| `distinct` | 범주형 (≤5개) | `THEME['PALETTE']` 5색 | 없음 (순환) |
| `warm` | 충전 / 시간 진행 | `_WARM_STOPS` 5색 (#F4A582 → #92182B) | cycle_idx / (n−1) |
| `cool` | 방전 / 시간 진행 | `_COOL_STOPS` 5색 (#92C5DE → #1B3A5C) | cycle_idx / (n−1) |
| `dual` | 충+방 동시 | warm(`condition=1`) + cool(`condition=2`) | 각각 cycle 진하기 |
| `chg_dchg` | 히스테리시스 | Major + Minor 모두 `_HYST_RAINBOW_STOPS` (10색, depth 기반) | depth 기반 |
| `group` | 경로 분할 | 4색 베이스 (남색/빨강/녹색/보라) × 농도 0.4~1.0 | path_idx hue, cycle_idx 농도 |

### 3.3 hue / gradient 우선순위

차원이 여러 개 겹치면 다음 우선순위로 색상 인코딩:

1. **hue** = 경로 (가장 큰 의미적 분리)
2. **hue 변형** = 채널 (같은 경로 내 셀)
3. **gradient (농도)** = 사이클 (시간 진행)
4. **warm/cool 이원** = 충/방전 (analysis_mode가 단일 방향이 아닐 때)

3차원 동시 표시 (전체통합)는 `group` 모드로 4색 베이스 사용 — 4개 초과 경로는 hue 회전 또는 별도 처리 필요.

---

## 4. 분석 종류별 권장 색상 매트릭스

| 분석 | view_mode | 권장 모드 | 비고 |
|---|---|---|---|
| **방전 분석** | CycProfile | cool 그라디언트 | 사이클 진행 진해짐 |
| 방전 분석 | CellProfile | distinct | 채널 구분 |
| 방전 분석 | AllProfile | group / cool | 경로 hue + 사이클 농도 |
| **충전 분석** | CycProfile | warm 그라디언트 | 사이클 진행 진해짐 |
| 충전 분석 | CellProfile | distinct | 채널 구분 |
| 충전 분석 | AllProfile | group / warm | 경로 hue + 사이클 농도 |
| **전체 프로파일** | CycProfile | dual | 충(warm) + 방(cool) 동시 |
| 전체 프로파일 | CellProfile | distinct | 채널 구분 |
| 전체 프로파일 | AllProfile | group / dual | 경로 hue + 충방 분리 |
| **히스테리시스** | CycProfile | **chg_dchg** | Major + Minor 모두 레인보우 (depth 기반) |
| 히스테리시스 | CellProfile | chg_dchg | 채널마다 동일한 depth 색상 (혼란 가능 — 검토 필요) |
| 히스테리시스 | AllProfile | chg_dchg + group | 경로 hue × depth 색상 (복잡 — 시각 명확성 필요) |

---

## 5. 코드 매핑

### 5.1 핵심 함수

- `_get_profile_color(mode, cycle_idx, n_total, *, condition, group_idx, is_major, is_first, is_last)` — 색상 결정 함수 (`DataTool_optRCD_proto_.py:3911`)
- `_resolve_profile_color_mode()` — 색상 모드 자동 결정
- 후처리 색상 루프 — `_profile_render_loop()` 내부 (대략 L20671)

### 5.2 Artist 태그 (후처리 색상 정렬용)

| 태그 | 의미 | 부착 위치 |
|---|---|---|
| `_cond_tag` | Condition (1=충전, 2=방전, 3=휴지) | 모든 plot 함수 |
| `_cycle_id_tag` | 사이클 인덱스 (0-based) | 모든 plot 함수 (커밋 `6373f94` 단일화) |
| `_minor_dim_alpha_tag` | 히스테리시스 minor dim 마커 | 페어링 모드 primary phase |

### 5.3 후처리 색상 루프 동작

1. plot 종료 후 `cycle_tab.count()` 순회
2. artist tag 검출 (`_cond_tag`, `_cycle_id_tag` 우선)
3. 사이클 경계 감지 (명시 tag 또는 휴리스틱 — Cond 연속성 분석)
4. `_get_profile_color()` 재호출로 색상 덮어쓰기
5. 휴지(`_cond_tag == 3`) → 회색 `#AAAAAA` alpha 0.3

### 5.4 팔레트 정의 위치

`DataTool_optRCD_proto_.py:3853-3882`:
- `_WARM_STOPS` — 5색 (충전)
- `_COOL_STOPS` — 5색 (방전)
- `_HYST_RAINBOW_STOPS` — 10색 (히스테리시스 Major + Minor 공통, depth 기반)
- `_PALETTE` (`colors.py`) — 범주형 5색

---

## 6. 향후 검토 사항

### 6.1 4개 초과 경로의 hue 처리
현재 `group` 모드는 4색 베이스. 5개 이상 경로 시 hue 순환 또는 차원 축소 필요.

### 6.2 색맹 접근성
warm/cool 그라디언트는 색맹 사용자에게 구분이 어려울 수 있음. 마커/선 스타일 보완 검토.

### 6.3 인쇄/PPT 출력
화면 색상이 인쇄 시 잘 안 보이는 경우 — 별도 인쇄용 색상 프리셋 (검정 + 그레이 그라디언트) 옵션 검토.

### 6.4 사이클 라벨 (legend) 통합
[[260412_profile_legend_unification]] 참조. 사이클 통합 모드에서 legend가 너무 길어지는 문제 — color bar 또는 축약 라벨 검토.

---

## 7. 관련 노트

- [[260428_profile_4modes_spec]] — 4종 분석 모델 spec (직교 차원)
- [[260428_profile_gap_current_vs_target]] — 현재 코드 vs target 격차
- [[hub_unified_profile]] — 코드 아키텍처 hub
- [[260420_hysteresis_preset_cv_and_rainbow_colors]] — 히스테리시스 색상 (rainbow stops)
- [[260420_hysteresis_major_threshold]] — Major loop 임계
- [[260412_profile_legend_unification]] — legend 통합
- [[260311_legend_ch_popup_analysis]] — 채널 팝업 색상 분석
