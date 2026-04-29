---
title: "Cell Design Specification — 표준 필드 스키마"
date: 2026-04-22
tags: [cell-design, specification, schema, reference]
type: reference
status: active
aliases:
  - Cell Design Spec 필드
  - Design Sheet 표준 항목
  - Cell Design Specification schema
related:
  - "[[260422_analysis_pybamm_key_parameters]]"
  - "[[260422_report_cell_design_vs_pybamm]]"
  - "[[Gen5plus_ATL_문서별_설계파라미터_인덱스]]"
  - "[[합제밀도와_전류밀도]]"
  - "[[MX배터리그룹_평가항목]]"
  - "[[배터리_구성]]"
  - "[[전해액]]"
  - "[[분리막_기능층]]"
  - "[[Silicon]]"
  - "[[PyBaMM_Variables_PPT]]"
source: "ATL Gen5+ Cell Design Specification (CA03, 250526) 템플릿 구조"
created: 2026-04-22
---

# Cell Design Specification — 표준 필드 스키마

> **스키마 전용**: 이 노트는 실제 Cell Design Specification 문서의 **필드 체계 (schema)** 만 담는다.
> 구체 수치·업체명·코드명은 기밀이므로 담지 않는다. 실측값은 원본 xlsx 를 참조.
>
> 원본 경로 (로컬 보관): `raw/g5p_at/CA03. 선행_Cell design specification_Gen5+_ATL_250526.xlsx` (또는 개발부서 공유 드라이브).

---

## 1. 문서 구조 개요

실제 ATL Gen5+ 프로젝트의 Cell Design Specification 은 **단일 시트 `Cell Design Specification`** 에 다음 7대 분류가 번호 체계 (X.Y) 로 배열되어 있다:

```
1. Cell dimension         (1.1 ~ 1.5)
2. Cathode                (2.1 ~ 2.15)
3. Anode                  (3.1 ~ 3.14)
4. Separator              (4.1 ~ 4.13)
5. Electrolyte            (5.1 ~ 5.6)
6. Pouch or CAN           (6.1 ~ 6.5)
7. Others                 (7.1 ~ 7.5)
────────────────────────────────────
   메타: Vendor, Project Name, Model Name, Type (Winding/Stack),
         Avg. Cell Voltage, Min./Target/OQC Capacity
```

---

## 2. 필드 상세

### 2.1. 1. Cell dimension (5 항목)

| # | 필드 | 단위 | 비고 |
|---|------|------|------|
| 1.1 | X max (excluding tape) | mm | 셀 장변 |
| 1.2 | Y max (excluding terrace) | mm | 셀 단변 |
| 1.3 | Y max (including terrace) | mm | terrace 포함 단변 |
| 1.4 | t max at shipping (excluding tape) | mm | 출하 두께 |
| 1.5 | t max at 1st full charge (including tape) | mm | 1st 만충 두께 (스웰링 포함) |

### 2.2. 2. Cathode (15 항목)

| # | 필드 | 단위 | 비고 |
|---|------|------|------|
| 2.1 | Type of active material | — | 4.4V LCO / 4.5V LCO / NCM / NCA / LFP 등 |
| 2.2 | Grade name of active material | — | 소재 코드 |
| 2.3 | Characteristics of cathode active material | — | potato / flaky 형상 + surface coating/doping |
| 2.4 | 2nd reversible capacity (half cell) | mAh/g | 하프셀 2nd cycle 가역 비용량 |
| 2.5 | 2nd reversible capacity (full cell) | mAh/g | 풀셀 2nd cycle 가역 비용량 |
| 2.6 | Specific capacity (single side, reversible) | mAh/cm² | 단면 면적당 용량 |
| 2.7 | Loading (single side) | mg/cm² | LL — Loading Level |
| 2.8 | Coating thickness (single side, no substrate) | μm | 활물질층 두께 |
| 2.9 | Density (calendering) | g/cc | 압연 직후 합제밀도 |
| 2.10 | Density (winding or stack) | g/cc | 권취·적층 후 최종 합제밀도 |
| 2.11 | Substrate thickness | μm | Al foil 두께 |
| 2.12 | Substrate type and grade | — | Al alloy grade |
| 2.13 | Formulation (active : binder : carbon) | 비율 | 예: 97:1.5:1.5 |
| 2.14 | Tab thickness / width | μm / mm | 양극 tab |
| 2.15 | Width | mm | 전극 폭 |

### 2.3. 3. Anode (14 항목)

| # | 필드 | 단위 | 비고 |
|---|------|------|------|
| 3.1 | Type of active material | — | AG / NG / Graphite+Si mixture 등 |
| 3.2 | Grade name of active material | — | 소재 코드 |
| 3.3 | Characteristics of anode active material | — | 입도·표면·Si 함량·코팅 |
| 3.4 | 2nd reversible capacity (half cell) | mAh/g | |
| 3.5 | 2nd reversible capacity (full cell) | mAh/g | |
| 3.6 | Loading (single side) | mg/cm² | |
| 3.7 | Coating thickness (single side, no substrate) | μm | |
| 3.8 | Density (calendering) | g/cc | |
| 3.9 | Density (winding or stack) | g/cc | |
| 3.10 | Substrate thickness | μm | Cu foil 두께 |
| 3.11 | Substrate type and grade | — | High-strength Cu etc. |
| 3.12 | Formulation (active : binder) | 비율 | |
| 3.13 | Tab thickness / width | μm / mm | 음극 tab |
| 3.14 | Width | mm | |

### 2.4. 4. Separator (13 항목)

| # | 필드 | 단위 | 비고 |
|---|------|------|------|
| 4.1 | Material for base separator | — | PE / PP / PE-PP 등 |
| 4.2 | Base separator thickness | μm | |
| 4.3 | Coating type (symmetry / asymmetry) | — | 양면 동일 여부 |
| 4.4 | 1st side coating : 1st layer type | — | ceramic / polymer / hybrid |
| 4.5 | 1st side coating : 1st layer thickness | μm | |
| 4.6 | 1st side coating : 2nd layer type | — | |
| 4.7 | 1st side coating : 2nd layer thickness | μm | |
| 4.8 | 2nd side coating : 1st layer type | — | asymmetry 시만 |
| 4.9 | 2nd side coating : 1st layer thickness | μm | |
| 4.10 | 2nd side coating : 2nd layer type | — | |
| 4.11 | 2nd side coating : 2nd layer thickness | μm | |
| 4.12 | Separator supplier | — | |
| 4.13 | Width | mm | |

> symmetry 설계면 4.8 ~ 4.11 생략 가능.
> 분리막 코팅 체계는 [[분리막_기능층]] + [[CCS]] / [[PCS]] / [[DLC]] 등 참조.

### 2.5. 5. Electrolyte (6 항목)

| # | 필드 | 단위 | 비고 |
|---|------|------|------|
| 5.1 | Base solvents | — | EC/PC, EC/PC/EMC, EC/PC/EP 등 |
| 5.2 | Base solvent formulation | 비율 | 예: 15:15:70 |
| 5.3 | Additives | — | FEC / VEC / PS / LiDFOB / LiPO₂F₂ / HTCN / SN 등 |
| 5.4 | Additive formulation | wt% | 예: 7% FEC + 3% PS + 0.5% LiPO₂F₂ |
| 5.5 | Amount of Electrolyte (Standard: Min. Capa) | g/Ah | 주액계수 |
| 5.6 | Molarity | M | 염 농도 (보통 1.0 ~ 1.35) |

> 상세 DOE 는 [[전해액]], [[전해액_MX코인셀_평가용조성]] 참조.

### 2.6. 6. Pouch or CAN (5 항목)

| # | 필드 | 단위 | 비고 |
|---|------|------|------|
| 6.1 | Pouch(CAN) thickness | μm | |
| 6.2 | Side folding type | — | Single / Double Side Folding |
| 6.3 | Pouch(CAN) supplier | — | |
| 6.4 | Pouch Forming Type | — | Both Side / Single Side |
| 6.5 | Pouch Forming R | mm | 포밍 반경 |

### 2.7. 7. Others (5 항목)

| # | 필드 | 단위 | 비고 |
|---|------|------|------|
| 7.1 | Energy Density (Fresh / EOL / with SEU) | Wh/L | 3종 기록 |
| 7.2 | Current Density | mA/cm² | 양극 기준 1C 전류밀도 |
| 7.3 | J/R Layer | — | 적층/권취 구조 코드 |
| 7.4 | N/P ratio | — | 보통 1.08 ~ 1.15 |
| 7.5 | Cell Weight | g | |

### 2.8. 메타 정보

| 필드 | 단위 | 비고 |
|------|------|------|
| Vendor | — | ATL / SDI / LG 등 |
| Project Name | — | Gen5+ HHP 向 Si 음극 등 |
| Model Name (Vendor) | — | 업체 부여 모델명 |
| Type (Main structure characteristic) | — | Winding / Stack |
| Avg. Cell Voltage | V | 공칭 전압 |
| Min. Capacity | mAh | 최소 보증 용량 |
| Target Capacity | mAh | 목표 용량 |
| OQC Cell Capacity | mAh | OQA/OQC 기준 실측 용량 |

---

## 3. PyBaMM 파라미터 매핑 (Category A/B/C/D 재정의)

Design Spec 필드 → PyBaMM 파라미터 변환을 [[260422_analysis_pybamm_key_parameters]] 의 가정 A1~A8 에 맞춰 분류.

### 3.1. Category A (Direct Input) — 단순 단위 변환

| Spec 필드 | PyBaMM 파라미터 | 변환 |
|----------|----------------|------|
| 2.8 / 3.7 Coating thickness | `Positive/Negative electrode thickness [m]` | ×1e-6 (μm→m) |
| 4.2 Base separator thickness | `Separator thickness [m]` | ×1e-6 |
| 5.6 Molarity | `Initial concentration in electrolyte [mol.m-3]` | ×1000 |
| 5.5 Amount of electrolyte | (PyBaMM 직접 키 없음 — 고갈 모델 확장 시) | — |
| 2.15 / 3.14 Width | `Electrode width [m]` | ×1e-3 |
| 1.* Cell dimension | `Electrode height [m]` (derived) | X max 등에서 도출 |
| Min. Capacity | `Nominal cell capacity [A.h]` | ÷1000 |
| 7.2 Current Density | `Current function [A]` | × 반응 면적 |
| — | `Upper/Lower voltage cut-off [V]` | Avg. Cell Voltage 기반 + 화학계 |

### 3.2. Category B (Calculated) — 가정 통한 변환

| Spec 필드 조합 | PyBaMM 파라미터 | 가정 참조 |
|--------------|----------------|---------|
| 2.10 / 3.9 Density + 2.13 / 3.12 Formulation + 소재 진밀도 | `Positive/Negative electrode active material volume fraction` | **가정 A1** |
| 2.10 / 3.9 Density + 진밀도 | `Positive/Negative electrode porosity` | 가정 A1 |
| 2.3 / 3.3 Characteristics (D50) | `Positive/Negative particle radius [m]` | **가정 A2** |
| 2.4 / 2.5 / 3.4 / 3.5 Reversible capacity + 진밀도 | `Maximum concentration in positive/negative electrode [mol.m-3]` | **가정 A3** |
| 7.4 N/P ratio + Stoichiometry window | `Initial concentration in positive/negative electrode [mol.m-3]` | **가정 A4** |
| 5.1~5.4 Solvents + Additives + Formulation | `Electrolyte diffusivity / conductivity` 함수형 + `SEI / Li plating kinetic rate` | **가정 A5, A6** |
| 2.7 / 3.6 Loading | (교차 검증: LL = thickness × density) | — |

### 3.3. Category C (Validation) — 시뮬 결과 vs 실측 비교

| Spec 측정치 | PyBaMM 대응 | 허용 Δ |
|----------|-----------|-------|
| OQC Cell Capacity | `Discharge capacity [A.h]` | ±2% |
| Avg. Cell Voltage | `Terminal voltage [V]` (적분 평균) | ±10 mV |
| Target Capacity | 시뮬 용량 (설계 목표) | 설계 margin 내 |
| 1.5 t max at 1st full charge vs 1.4 t max at shipping | 스웰링 (PyBaMM 범위 밖) | — |

### 3.4. Category D (Out of Scope) — PyBaMM 1D 불가

- 1.1 ~ 1.5 Cell dimension 대부분 (기구 치수, 시뮬은 단면 1D)
- 2.14 / 3.13 Tab thickness/width (Tab 저항 1D에 부분 반영)
- 2.11 / 3.10 Substrate thickness (집전체 저항만 일부)
- 2.12 / 3.11 Substrate grade (재료 고유 전도도 외)
- 4.3 ~ 4.11 분리막 코팅 구조 (평균 물성만)
- 4.12 Separator supplier, 6.3 Pouch supplier
- 6.* Pouch dimension / folding / forming
- 7.3 J/R Layer, 7.5 Cell Weight
- 에너지 밀도 (Wh/L) — 계산으로만 (시뮬 자체 변수 아님)

---

## 4. Spec → PyBaMM 커버리지 요약

| Spec 대분류 | PyBaMM 직접 커버 | 간접·가정 통해 | 범위 밖 |
|-----------|:------------:|:----------:|:-------:|
| 1. Cell dimension | 0/5 | 1/5 (전극 폭·높이) | 4/5 |
| 2. Cathode | 5/15 | 7/15 | 3/15 |
| 3. Anode | 5/14 | 6/14 | 3/14 |
| 4. Separator | 2/13 | 2/13 | 9/13 |
| 5. Electrolyte | 2/6 | 3/6 (첨가제·용매 조합) | 1/6 |
| 6. Pouch or CAN | 0/5 | 0/5 | 5/5 |
| 7. Others | 3/5 (J, N/P, voltage) | 1/5 (에너지밀도) | 1/5 |
| **합계** | **17/63 (27%)** | **20/63 (32%)** | **26/63 (41%)** |

### 해석
- **직접 커버 27%**: Design Spec 필드 중 1/4 정도만 PyBaMM 단순 변환으로 들어감
- **간접 32%**: 가정 A1~A8 거치면 추가로 1/3 편입
- **범위 밖 41%**: 파우치·기구·공정·업체·코팅 구조 등 PyBaMM 1D 전기화학 모델로는 불가
- 즉 **Design Spec ≠ 시뮬 입력** — 시뮬은 전체 설계의 일부 측면만 본다. 이것이 [[260422_analysis_pybamm_key_parameters]] 섹션 6의 메시지다.

---

## 5. 활용 가이드

### 5.1. 시뮬레이션 DOE 설계 시
1. Spec 에서 **Category A 필드부터** PyBaMM 입력으로 지정
2. Category B 필드는 **변환식 + 가정 명시** 후 입력
3. Category C 필드는 **시뮬 후 비교 검증용** 으로 확보
4. Category D 필드는 시뮬 대신 **다른 tool 또는 실험**으로 처리

### 5.2. BDT UI 확장 시
`_key_map` / `_key_map_extended` 는 현재 Category A + 일부 B 커버. 확장 대상:
- Category B 필드 자동 변환 계산기 (예: 합제밀도 + 배합비 → ε_AM)
- Category C 필드 입력 후 시뮬 결과와 자동 Δ 계산
- Category D 필드는 읽기 전용 메타로 표시

### 5.3. 개발 회의 체크리스트
- Spec 초안 작성 시: 7대 분류 전부 기록
- Proto OQA 시: Category C 필드 채워 시뮬 검증
- MP 이관 시: Category B 필드의 가정 유효 범위 재검토
- CA 완료 시: Design Spec 최종본 vs 시뮬 예측 Δ 문서화

---

## 🔗 관련 문서

- [[260422_analysis_pybamm_key_parameters]] — PyBaMM key 파라미터 도출 + 단순화 가정 A1~A8
- [[PyBaMM_Variables_PPT]] — PyBaMM 전체 파라미터 리스트
- [[합제밀도와_전류밀도]] — 2.7/3.6 Loading, 2.9/3.8 Density 공식
- [[MX배터리그룹_평가항목]] — MX 프로젝트 평가/설계 항목
- [[배터리_구성]] — 양극·음극·전해액·분리막 기본 구성
- [[전해액]] — 5.1~5.4 전해액 조성 DOE
- [[분리막_기능층]] — 4.4~4.11 코팅 구조
- [[Silicon]] — 3.1~3.3 Si 음극 특성 (Gen5+ Si 기반)
