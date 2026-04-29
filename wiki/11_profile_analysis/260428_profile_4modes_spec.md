---
title: "프로파일 분석 4종 모델 — Spec"
aliases:
  - Profile 4-Modes Spec
  - 4종 분석 모델
tags:
  - profile-analysis
  - spec
  - hysteresis
  - dod
  - soc
  - 4-modes
type: spec
status: draft
related:
  - "[[260428_profile_view_color_spec]]"
  - "[[260428_profile_gap_current_vs_target]]"
  - "[[hub_unified_profile]]"
  - "[[260420_profile_axis_dod_option]]"
  - "[[260418_profile_options_redesign]]"
  - "[[260420_hysteresis_preset_cv_and_rainbow_colors]]"
created: 2026-04-28
updated: 2026-04-28
---

# 프로파일 분석 4종 모델 — Spec

> [!abstract] 요약
> 프로파일 분석 탭의 분석 모델을 **4종 분석 종류**로 재정의: (1) 방전 분석 (2) 충전 분석 (3) 전체 프로파일 분석 (4) 히스테리시스. 현재 코드의 옵션 조합 모델(`data_scope × axis_mode × overlap`)은 사용자 mental model과 본질적으로 다르며, 이 spec은 향후 UI/구현 phase의 청사진 역할을 한다.

> 상위 → [[hub_unified_profile]] · 격차 → [[260428_profile_gap_current_vs_target]] · 색상/탭 → [[260428_profile_view_color_spec]]

---

## 1. 배경

기존 BDT 프로파일 분석은 옵션 조합형 UI:
- 데이터 범위 (사이클 / 충전 / 방전)
- X축 (SOC / DOD / 시간)
- 오버랩 (이어서 / 분리 / 연결)
- 부가 (Rest / CV / TC 페어링 / dQdV 전환 등)

옵션 조합 수가 많고 사용자 의도와의 매핑이 직관적이지 않아 다음 문제가 누적:
- `사이클 + DOD + 분리/연결` 조합 plot 이상 (좌우 분리 좌표계 — [[260420_profile_axis_dod_option]] 시점 의도였으나 재검토)
- TC 페어링이 별도 체크박스로 분리 — 히스테리시스의 본질이 "페어 루프"임에도 사용자가 매번 토글 필요
- 분석 종류별로 X축 / Y축 / 색상 권장값을 코드가 직접 결정하지 못함

본 spec은 사용자 mental model의 4종 분석을 **1차 분류**로 두고, X축·overlap·페어링은 분석 종류에 따라 자동/제한되는 형태를 정의한다.

---

## 2. 4종 분석 종류

### 2.1 방전 분석 (Discharge Analysis)

| 항목 | 값 |
|---|---|
| **X축** | 시간 / DOD (선택) |
| **데이터** | `Condition == 2` (방전 segment) |
| **DOD 의미** | 0~1 양수 (= 누적 방전 용량 / 방전 종료 용량) |
| **Y축 plot** | Voltage, dVdQ (X=DOD), dQdV (X=DOD), C-rate, Temp, Energy |
| **사용 시나리오** | 율별 방전 비교, 사이클별 RPT 분석, 방전 voltage profile, dV/dQ feature 추적 |
| **현재 코드 매핑** | `data_scope=discharge` + `axis_mode=time/dod` + `overlap=split` |

### 2.2 충전 분석 (Charge Analysis)

| 항목 | 값 |
|---|---|
| **X축** | 시간 / SOC (선택) |
| **데이터** | `Condition == 1` (충전 segment) |
| **SOC 의미** | 0~1 양수 |
| **Y축 plot** | Voltage, dVdQ (X=SOC), dQdV (X=SOC), C-rate, Temp, Energy |
| **dQdV 전환** | 충전 모드 전용 — X/Y축 swap (`chk_dqdv`, 이미 구현) |
| **사용 시나리오** | 스텝 충전 패턴 분석, CC/CV 비율, 충전량 비교 |
| **현재 코드 매핑** | `data_scope=charge` + `axis_mode=time/soc` + `overlap=split` |

### 2.3 전체 프로파일 분석 (Full Profile Analysis)

| 항목 | 값 |
|---|---|
| **X축** | 시간 (고정) |
| **데이터** | 충전 + 휴지 + 방전 + 휴지 (전체 사이클) |
| **시간축 처리** | 사이클별 t=0 리셋, 사이클 간 NaN 경계 |
| **Y축 plot** | Voltage, Current, C-rate, Temp, Energy |
| **Advanced 도출** | GITT (R_total/R_ohm/R_diff), OCV (긴 휴지 후 평형 voltage), CCV (펄스 직후 voltage) |
| **사용 시나리오** | 시계열 전체 흐름, 충방전 사이 휴지 패턴, 임피던스 추출 |
| **현재 코드 매핑** | `data_scope=cycle` + `axis_mode=time` + `overlap=continuous` (legacy_mode `continue`) |

### 2.4 히스테리시스 분석 (Hysteresis Analysis)

| 항목 | 값 |
|---|---|
| **X축** | SOC / DOD (선택) |
| **데이터** | TC 페어 — TC N (방전 X% depth) + TC N+1 (충전 X% recharge) |
| **핵심 동작** | 사이클별 닫힌 루프 (페어 자동 매칭) |
| **X축 좌표계** | **0~1 양수** (충전 0→peak, 방전 peak→0) — 좌우 분리 좌표계 폐기 |
| **DOD 라벨** | SOC 데이터에 X축 라벨만 "DOD" 표시 |
| **Y축 plot** | Voltage, dVdQ |
| **깊이 라벨** | 자동 — `Dchg 10%`, `Dchg 20%`, ... |
| **색상** | `chg_dchg` 모드 — Major + Minor 모두 레인보우 10색 (`_HYST_RAINBOW_STOPS`, depth 기반) |
| **현재 코드 매핑** | `data_scope=cycle` + `axis_mode=soc/dod` + `overlap=connected` + `hyst_pair=ON` (자동) |

#### 2.4.1 페어 매칭 규칙

```
TC 1 (RPT 만충, 100%)             # ← 페어링에서 제외
TC 2 (방전 100→90%) ─┐
                     ├─ depth 10% 닫힌 루프
TC 3 (충전 90→100%) ─┘
TC 4 (방전 100→80%) ─┐
                     ├─ depth 20% 닫힌 루프
TC 5 (충전 80→100%) ─┘
TC 6 (방전 100→70%) ─┐
                     ├─ depth 30% 닫힌 루프
TC 7 (충전 70→100%) ─┘
...
```

각 페어는 X축 SOC peak~(peak−depth) 영역에 위치. depth가 클수록 X축 양 끝(0, peak)을 더 넓게 사용.

#### 2.4.2 자동화 (현재 수동 → 자동)

- 현재: `profile_hyst_pair_chk` 체크박스 수동 ON
- target: `사이클 + 연결 + (SOC|DOD)` 조합 시 페어링 자동 활성. 체크박스 UI 제거.
- 사유: 히스테리시스의 정의 자체가 페어 루프 — 별도 옵션이 아닌 분석의 기본 동작.

---

## 3. 옵션 조합 매트릭스 (요약)

| 분석 | X축 옵션 | overlap | 페어링 | 좌표계 |
|---|---|---|---|---|
| **방전** | 시간 / DOD | split | 비활성 | 0~1 양수 |
| **충전** | 시간 / SOC | split | 비활성 | 0~1 양수 |
| **전체 프로파일** | 시간 | continuous | 비활성 | 시간축 |
| **히스테리시스** | SOC / DOD | connected | **자동 ON** | 0~1 양수 (DOD는 라벨만) |

### 3.1 좌표계 통일 원칙

**모든 분석에서 X축 데이터는 0~1 양수**. DOD는 단지 X축 라벨 문자열 — 데이터 변환 없음.

이전 [[260420_profile_axis_dod_option]] 시점에는 DOD를 충전 -1~0, 방전 0~1 좌우 분리 좌표계로 설계했으나, 본 spec에서 폐기. 사유:
- 사용자 mental model에서 "DOD plot"은 "방전 심도 관점" — 충전을 음수 영역으로 분리할 직관적 이유 없음
- dVdQ 충전 끝(DOD=0)에서 dQ→0 으로 ±5 스파이크 발생 (좌우 분리의 부산물)
- X축 라벨 -1.1~1.2 범위 가독성 저하 (음수 부호 시각 충돌)
- 히스테리시스 닫힌 루프 모양이 좌우 분리에서는 자연스럽지 않음

→ 격차 G1, G2 ([[260428_profile_gap_current_vs_target]]) 참조.

---

## 4. UI 매핑 (target)

향후 UI 재설계 시 권장 구조:

```
┌─ 분석 종류 라디오 (1차 분류, 4개) ─────────────┐
│  ○ 방전 분석    ○ 충전 분석                     │
│  ○ 전체 프로파일  ● 히스테리시스                │
└─────────────────────────────────────────────┘
┌─ X축 (분석 종류별 자동 활성/비활성) ────────────┐
│  ○ 시간 [활성]  ● SOC [활성]  ○ DOD [활성]      │  ← 히스테리시스
│  ● 시간 [활성]  ○ SOC [활성]  ○ DOD [비활성]   │  ← 충전 분석
└─────────────────────────────────────────────┘
┌─ 부가 옵션 (분석 종류별 의미 명확화) ────────────┐
│  ☑ Rest 포함   ☑ CV 포함                        │
│  ☑ dQdV 전환 [충전 분석 시만 활성]              │
└─────────────────────────────────────────────┘
```

기존 `overlap` (이어서/분리/연결) 라디오는 분석 종류에 의해 결정되므로 UI에서 제거 가능. 단, 호환성 유지를 위해 내부 로직은 유지하고 분석 종류 선택 시 자동 설정.

기존 `hyst_pair` 체크박스는 제거 (히스테리시스 분석에서 자동 ON).

---

## 5. 분석 종류별 데이터 흐름

### 5.1 방전 분석
```
원본 데이터 (cycle, channel, path)
  → Condition == 2 필터
  → X축 = 시간 OR DchgCap (정규화 0~1)
  → Y축 = Voltage / dVdQ / dQdV (X=DOD) / Crate / Temp / Energy
  → 사이클별 segment, NaN 경계 (split)
```

### 5.2 충전 분석
```
원본 데이터
  → Condition == 1 필터
  → X축 = 시간 OR ChgCap (정규화 0~1)
  → Y축 = Voltage / dVdQ / dQdV (X=SOC) / Crate / Temp / Energy
  → 사이클별 segment, NaN 경계
  → (옵션) dQdV 전환: X↔Y swap
```

### 5.3 전체 프로파일 분석
```
원본 데이터
  → Condition 모두 (1, 2, 3 휴지)
  → X축 = 시간 (사이클별 t=0 리셋)
  → Y축 = Voltage / Current / Crate / Temp / Energy
  → 사이클 간 NaN 경계
  → (Advanced) GITT/OCV/CCV 도출 후 추가 plot
```

### 5.4 히스테리시스 분석
```
원본 데이터
  → 사이클 페어링 (TC N + TC N+1)
  → 첫 RPT 만충 사이클 제외
  → 각 페어 별 닫힌 루프 데이터 결합:
    - 충전 phase: ChgCap (0 → peak)
    - 방전 phase: peak − DchgCap (peak → 0)
  → X축 = SOC (0~1 양수, 라벨만 SOC/DOD)
  → Y축 = Voltage / dVdQ
  → 페어별 색상 (depth 기반 레인보우)
  → 페어별 라벨 (Dchg X% / Chg X%)
```

---

## 6. Edge Cases / 주의 사항

### 6.1 페어 불완전 케이스
- TC N (방전 100→X%) 만 있고 TC N+1 (충전 X→100%) 없는 경우 → 단편 line으로 표시 (닫힘 루프 X). 라벨은 `Dchg X% (no recharge pair)`.
- 페어 매칭 실패 시 fallback: 단순 닫힌 루프 표시 (충전 0→peak, 방전 peak→0) 페어링 OFF 상태와 동일.

### 6.2 첫 RPT 사이클 (TC 1) 제외
- 일반적으로 RPT는 만충 (0→100%) 충전 후 만방 (100→0%) 방전 — 깊이 100% 페어와 동일.
- 자동 매칭 시 TC 1을 페어링에서 제외하거나, 또는 depth 100% major loop로 별도 표시.

### 6.3 RPT 중간 삽입 케이스
- 사이클 흐름 중 RPT가 삽입되면 페어링이 끊김. 사용자가 RPT 사이클을 명시 (예: 사이클 분류 메타데이터)하여 자동 매칭이 RPT를 건너뛰게 함.

### 6.4 SOC peak가 사이클별로 다른 경우
- 사이클 1: 100% peak, 사이클 100: 95% peak (열화 후) → X축에서 시각적 정렬을 위해 peak를 1.0으로 정규화하거나 raw peak로 두는 옵션 필요. spec 후속 phase에서 결정.

---

## 7. 향후 작업

| Phase | 내용 | 관련 |
|---|---|---|
| Phase 2 | DOD 좌우 분리 폐기 → 양수 닫힌 루프 (G1, G2) | [[260428_profile_gap_current_vs_target]] |
| Phase 3 | TC 페어링 자동화 (G3) — 체크박스 제거 | 위 동일 |
| Phase 4 | UI 재설계 (G4) — 분석 종류 라디오 추가 | 위 동일 |
| Phase 5 | dQdV 전환 확대 (G5) + GITT/OCV/CCV 도출 기능 | 위 동일 |

각 phase는 별도 plan 모드로 세부 정의.

---

## 8. 관련 노트

- [[260428_profile_view_color_spec]] — 그래프 구성·색상 체계 spec
- [[260428_profile_gap_current_vs_target]] — 현재 코드 vs target 격차 분석
- [[hub_unified_profile]] — 코드 아키텍처 hub (`unified_profile_core` / `_profile_render_loop`)
- [[260420_profile_axis_dod_option]] — DOD 옵션 추가 시점 (이전 좌우 분리 의도, 본 spec에서 재정의)
- [[260418_profile_options_redesign]] — 옵션 재설계 분석
- [[260420_hysteresis_preset_cv_and_rainbow_colors]] — 히스테리시스 프리셋·색상
- [[260420_hysteresis_major_threshold]] — Major loop 임계값
