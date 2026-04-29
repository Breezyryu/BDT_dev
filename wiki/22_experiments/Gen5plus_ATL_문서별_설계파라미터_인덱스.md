---
title: "Gen5+ ATL 개발 문서별 설계 파라미터 인덱스"
date: 2026-04-22
tags: [cell-design, Gen5plus, ATL, document-index, parameters, reference]
type: reference
status: active
aliases:
  - Gen5+ 문서 인덱스
  - Gen5+ 설계 파라미터 맵
  - g5p_at 46 파일 인덱스
related:
  - "[[Cell_Design_Specification_필드]]"
  - "[[260422_report_cell_design_vs_pybamm]]"
  - "[[260422_analysis_pybamm_key_parameters]]"
  - "[[MX배터리그룹_평가항목]]"
  - "[[Silicon]]"
  - "[[양극별_특성]]"
source: "raw/g5p_at/ 46 파일 실측 스캔 (xlsx sharedStrings, pptx 슬라이드 제목)"
scope: "Gen5+ HHP向 Si 음극 배터리 플랫폼 선행개발 (ATL, 2024~2025)"
created: 2026-04-22
---

# Gen5+ ATL 개발 문서별 설계 파라미터 인덱스

> **raw/g5p_at/ 46 개 파일의 설계 파라미터 매핑**. 각 문서가 Cell Design Spec 7대 분류 (1.Cell dim ~ 7.Others) 중 어느 필드를 담는지 + 추가로 다루는 공정·위험·측정 항목.
>
> 구체 수치는 모두 기밀이므로 **필드·파라미터 카테고리만** 기록. 상세 수치는 raw/ 원본 직접 참조.
> 정본 스키마: [[Cell_Design_Specification_필드]].

---

## 0. 개발 화학 조성 (2026-04-22 확인)

- **양극**: 고전압 LCO (LiCoO₂, 4.53V cut-off) · Spec 코드 `Gen5 4.53V 2.0C PF-PTO` · `PF-MP1`
- **음극**: Graphite 또는 Graphite + SiC · Spec 코드 `APG-031+5%Si(EPF)`
- **개발 방향**: 양극 고전압화 ↑ + 음극 Si 함량 증가 ↑

---

## 1. 46 문서 단계별 분류

### 1.1 EA 단계 (Evaluation Approval, 5 개)

| 파일 | 유형 | 핵심 내용 |
|------|------|---------|
| EA01. 선행_Cell Pack Proposal_Gen5+_ATL_250218.pdf | 제안 | 셀/팩 제안서 |
| EA02. 선행_Spec meeting 회의록_Gen5+_ATL_250325.mht.pptx | 회의록 | Spec 협의 결과 |
| EA03. 선행_과제계획서_Gen5_241028.pptx | 계획 | 과제명, 개발 배경, 목표, Risk |
| EA04. 선행_EA회의록_Gen5+_250326.docx ×2 | 회의록 | EA 합의 사항 |

### 1.2 PA 단계 (Plan Approval, 10 개)

| 파일 | 유형 | 핵심 내용 |
|------|------|---------|
| PA01. 선행_Cell Design Specification 초안_Gen5+_ATL_241010.xlsx ×2 | **Spec 초안** | **63 필드 전체 초안값** (7대 분류) |
| PA02. 선행_DFMEA 초안_Gen5+_ATL_251020.xlsx.xlsx | **위험** | Failure mode × Root cause × Detection, 13 시트 (DFMEA + EIS + DCR + 수명 + 안전) |
| PA04. 선행_Risk assessment_Gen5+_ATL_240828.pdf ×2 | 위험 | 개발 Risk 평가 |
| PA05. 선행_신규 소재검토서_Gen5+_ATL_240828.pdf ×2 | **신규 소재** | 양극/음극/전해액 신규 소재 물성 spec |
| PA06. 선행_선행개발제안서_Gen5+_ATL_241028.pptx ×2 | 제안 | 과제 제안서 (EA03과 유사 템플릿) |
| PA07. 선행_제안승인회의록_Gen5+_240925.docx ×2 | 회의록 | 제안 승인 합의 |

### 1.3 Proto 단계 (Prototype 1차, 5 개)

| 파일 | 유형 | 핵심 내용 |
|------|------|---------|
| Proto02. 선행_Proto 1차 OQA data_Gen5+_ATL_250228.xlsx | **실측** | OCV, AC Impedance, SEC Capacity, Length, Cp/Cpk 산포 (Cell # 단위) |
| Proto03. 선행_Proto 1차 Test report_Gen5+_ATL_250228.xlsx.pdf | 측정 | Proto 종합 Test 결과 |
| Proto04. 선행_Proto 1차 Cycle data_Gen5+_ATL_250603.xlsx | **수명** | 23℃/45℃/15℃ × THK (두께 변화) 사이클 커브, #1-A/B/C 샘플 |
| Proto05. 선행_Proto 1차 Test report ver2_Gen5+_ATL_250316.xlsx.pdf | 측정 | Test ver2 |
| Proto08. 선행_Proto 1차 신규소재평가_Gen5+_ATL_251211.xlsx | **심화 전기화학** | Three-Electrode (양극 potential), Cyclic voltammetry, **XRD at different SOC**, **DSC of Cathode**, **ARC** (thermal runaway), **Co dissolution**, Gen5+ fresh vs 400 cycles 비교 |

### 1.4 MP1 단계 (Mass Production 1차, 9 개)

| 파일 | 유형 | 핵심 내용 |
|------|------|---------|
| MP101. 선행_MP1 1차 Run 공정결과서_Gen5+_ATL_250722.xlsx | **공정** | 공정별 NG 종류 (Coating, Pressing, Slitting, Tab, Dent, Hi-pot, Overhang 등), Yield, Defect PPM |
| MP102. 선행_MP1 1차 Cell Approve Sheet_Gen5+_ATL_250722.pdf | 승인 | MP1 Cell 승인 시트 |
| MP103. 선행_MP1 1차 Test Report_Gen5+_ATL_250722.xlsx | **측정** | Capacity Test (0.2/0.5/1.0C), Life Cycle (23/45℃), Environment Test, PL Safety (Heating/Flame/Explosion) |
| MP104. 선행_MP1 1차 Cycle data_Gen5+_ATL_250804.xlsx | **수명** | 23/45/15℃ + THK, Proto04와 포맷 동일 |
| MP106. 선행_MP1 분해분석 결과_Gen5+_ATL_250722.xlsx | **분해** | 분해분석 규격(Winding), 외관관리(Pouch), Critical/Major/Minor 영향도 분류 |
| MP107. 선행_MP1 1차 Cycle data ver2_Gen5+_ATL_251212.xlsx | 수명 | MP104 ver2 (장기 사이클 추가) |
| MP108. 선행_MP1 1차 Test Report ver2_Gen5+_ATL_250722.xlsx | 측정 | MP103 ver2 |
| MP114. 선행_MP1 1차 Cycle data ver3_Gen5+_ATL_260204.xlsx | **최종 수명** | LT/RT/HT × Thk × **DCIR** 최종 포맷, DOE + Main + Proto + MP1 교차 비교 |

### 1.5 MP2 단계 (Mass Production 2차, 13 개)

| 파일 | 유형 | 핵심 내용 |
|------|------|---------|
| MP201. 선행_MP2 1차 Run 공정결과서_Gen5+_ATL_250831.xlsx | **PMP 전체** | Revision, Cover, Summary, Design, QCP, CTQ/CTP, **Mixing / Coating / Pressing / Anode EPF / Slitting / Ablation / Winding / Packaging / Vacuum drying / E.L Injection / PIEF / Degassing / OCV 데이터** (공정 전 단계 Cpk 포함) |
| MP202. 선행_MP2 1차 Run 수율결과서_Gen5+_ATL_250831.xlsx | 수율 | 공정별 Yield·Defect PPM (MP101 형식) |
| MP203. 선행_MP2 1차 Pack Approval Sheet_Gen5+_ATL_250903.pdf | 승인 | MP2 Pack 승인 시트 |
| MP204. 선행_MP2 1차 Test report_Gen5+_ATL_250901.xlsx | 측정 | Capacity/Life/Environment/PL Safety (MP103 포맷) |
| MP205. 선행_MP2 1차 Cycle data_Gen5+_ATL_251227.xlsx | 수명 | 23/45/15℃ + THK + **23℃ Decap** (분해 확인) |
| MP207. 선행_MP2 분해분석 결과_Gen5+_ATL_250831.xlsx | 분해 | MP106 규격 적용 |
| MP208. 선행_MP2 1차 Cycle data ver2_Gen5+_ATL_251227.xlsx | 수명 | MP205 ver2 |
| MP209. 선행_MP2 1차 Test report ver2_Gen5+_ATL_250901.xlsx | 측정 | MP204 ver2 |
| MP215. 선행_MP2 1차 ER2 보고서_Gen5+_ATL_241127.pptx | **중간보고** | 30 슬라이드, 개발 목표 · Risk · 검증 |
| MP216. 선행_MP2 1차 부품승인 검토 결과_Gen5+_ATL_260105.mht.eml ×2 | 메일 | Cell/Pack 부품승인 검토 |

### 1.6 CA 단계 (Close / Completion, 4 개)

| 파일 | 유형 | 핵심 내용 |
|------|------|---------|
| CA01. 선행_CA 과제완료 보고서_Gen5+_ATL_251231.pptx | **완료 보고** | 33 슬라이드, 개발 내용·일정·목표·검증·Risk·특허·비용 |
| CA02. 선행_CA 과제완료 회의록_Gen5+_ATL_251231.docx | 회의록 | 완료 합의 |
| CA03. 선행_Cell design specification_Gen5+_ATL_250526.xlsx | **🎯 Spec 최종** | **63 필드 최종값** — [[Cell_Design_Specification_필드]] 정본 |
| CA04. 선행_DFMEA_Gen5+_ATL_260112.xlsx | **위험 최종** | DFMEA 13 시트 최종 (PA02 대비 update) |

### 1.7 기타 (1)

| 파일 | 유형 | 핵심 내용 |
|------|------|---------|
| 1. ATL_Gen5+ 2C B496478_ Approval Sheet_Ver0_20250901.pdf | 승인 | ATL 원청 Approval Sheet |
| [과제계획서] Gen5+ HHP向 Si 음극 배터리 플랫폼 선행개발_20250326.pptx | 계획 | 20 슬라이드, PA06과 유사 |

---

## 2. 문서 × Cell Design Spec 7대 분류 매트릭스

> 각 문서가 **Cell Design Spec 의 어느 대분류**를 담는지 / 변경하는지 / 검증하는지. ✅=전체 포함 / ◐=일부 / —=무관.

| 문서 | 1.Dim | 2.Cathode | 3.Anode | 4.Sep | 5.EL | 6.Pouch | 7.Others | 공정 | 위험 | 측정 |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **PA01 Spec 초안** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — |
| **CA03 Spec 최종** 🎯 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — |
| EA03 과제계획서 | — | — | — | — | — | — | ◐ (목표 C-rate, 용량) | — | ◐ | ◐ |
| PA02 DFMEA 초안 | — | ◐ | ◐ | ◐ | ◐ | — | ◐ | ◐ | ✅ | ✅ |
| **CA04 DFMEA 최종** | — | ◐ | ◐ | ◐ | ◐ | — | ◐ | ◐ | ✅ | ✅ |
| PA04 Risk assessment | — | — | — | — | — | — | — | ◐ | ✅ | — |
| **PA05 신규 소재검토서** | — | ✅ | ✅ | ✅ | ✅ | — | — | — | ◐ | ◐ |
| PA06 선행개발제안서 | — | — | — | — | — | — | ◐ | — | ◐ | — |
| CA01 과제완료 보고서 | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ✅ | ◐ | ✅ | ✅ |
| MP215 ER2 보고서 | — | — | — | — | — | — | ◐ | ◐ | ✅ | ✅ |
| **Proto02 OQA** | — | — | — | — | — | — | ◐ (OCV, IR, Cap) | — | — | ✅ |
| **Proto04 Cycle data** | ◐ (THK) | — | — | — | — | — | — | — | — | ✅ |
| **Proto08 신규소재평가** | — | ✅ (XRD, DSC, ARC, Co dissol.) | ◐ (3전극 potential) | — | ◐ (CV) | — | — | — | ✅ | ✅ |
| **MP101/202 공정결과서** | ◐ | ◐ | ◐ | ◐ | — | ◐ (Tab, Taping) | — | ✅ | ◐ | — |
| **MP103/108/204/209 Test** | — | — | — | — | — | — | ✅ (Cap, Life, PL) | — | ◐ | ✅ |
| **MP104/107/205/208 Cycle** | ◐ (THK) | — | — | — | — | — | — | — | — | ✅ |
| **MP114 Cycle ver3** (최종) | ◐ | — | — | — | — | — | ◐ (DCIR) | — | — | ✅ |
| **MP106/207 분해분석** | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | — | — | ✅ | — |
| **MP201 PMP 전체** | ◐ | ✅ | ✅ | ✅ | ✅ | ✅ | ◐ | ✅ (전공정) | ◐ | ◐ |
| MP102/203 Approve Sheet | ◐ | — | — | — | — | — | ◐ | — | — | ◐ |

### 해석

- **Spec 전체 필드를 가진 문서**: PA01 (초안) · CA03 (최종) · **PA05 신규 소재검토서** (소재 파트만)
- **공정 파라미터 정본**: MP201 (PMP 전체 15 공정 단계)
- **위험 정본**: CA04 DFMEA 최종 (+ PA02 초안)
- **측정 정본**: MP114 (수명 최종) + MP204/209 (Test 최종) + Proto08 (심화 전기화학)
- **Gen5+ 특화 측정**: Proto08 의 XRD at different SOC / DSC / ARC / Co dissolution — 고전압 LCO 의 **구조·열·금속 용출** 검증

---

## 3. 공정 단계별 파라미터 (MP201 PMP 기반)

MP201 은 전 공정 Cpk 관리를 담고 있다. 공정 → 담긴 설계 파라미터:

| 공정 | 공정 파라미터 | Cell Design Spec 대응 |
|------|-------------|-------------------|
| **Mixing** | Viscosity, Solid contents, Binder sol 조성 | 2.13 / 3.12 Formulation |
| **Coating** | Loading level (β-Ray Scanner continuous), Side A LL, Tension, Dry Temp/Airflow, Line speed | **2.7 / 3.6 Loading** |
| **Pressing** | Press thickness, Edge sliding, SAICAS, Electrode adhesion | **2.8 / 3.7 Coating thickness**, **2.9~2.10 / 3.8~3.9 Density** |
| **Anode EPF** | (Electrode Pore Formation) | 3.3 Anode characteristics, [[EPF]] |
| **Slitting** | Width, Burr | **2.15 / 3.14 Width** |
| **Ablation** | Laser 조건 | — |
| **Winding** | J/R 구조, Tension | **7.3 J/R Layer** |
| **Packaging** | Forming depth, Tab welding strength, Sealing (위치별 두께·폭) | **6.1~6.5 Pouch** |
| **Vacuum drying** | Moisture content (Max 200 ppm) | (품질 CTQ) |
| **E.L Injection** | Electrolyte weight | **5.5 Amount of electrolyte** |
| **PIEF** | (Post Injection Electrode Formation) | 화성 |
| **Degassing** | Sealing 두께·폭 재측정, Electrolyte weight 재측정 | 5.5 |
| **OCV Data** | OCV @ SOC 30/62, IR, Cell thickness | Proto02 OQA 와 연결 |

---

## 4. 위험·열화 검증 항목 (DFMEA + Proto08 + CA01)

### 4.1 CA04 DFMEA 시트 구성 (13 시트)

| 시트 | 측정 방법 | 검증 대상 |
|------|---------|---------|
| DFMEA_4.53V_Gen5+_2C_ED775 | 본 매트릭스 | Failure mode × Root cause × Detection |
| EIS (fresh + HTHH) | AC 임피던스 | 열화 메커니즘 분리 |
| DCR-By SOC | DC 저항 | SOC별 저항 맵 |
| 110℃-5hr | 고온 방치 | Thermal abuse |
| Long Term Cyclelife | 장기 사이클 | 수명 |
| Floating Results | 충전 유지 | 저장·부동 |
| Tear Down Picture | 분해 사진 | 육안 검증 |
| **Three-Electrode for Ca. potential** | 3전극 | 양극 단독 전위 측정 (4.53V 영역) |
| **Cyclic voltammetry** | CV | 전해액 산화 안정성 |
| **XRD of Cathode at different SOC** | XRD | LCO 구조 변화 (layered → spinel 전이) |
| **DSC of Cathode** | DSC | 양극 열분해 온도 (4.53V deep delithiation) |
| **ARC** | Accelerating Rate Calorimetry | 열폭주 임계 |
| **Co dissolution** | ICP | Co 용출 (고전압 LCO 특화) |

### 4.2 Failure mode 주요 카테고리

- **Li plating** (coating loading tolerance 기반 추정 실패)
- **Cathode binder reactivity at high voltage** (4.53V 특이)
- **Graphene additive reactivity at high voltage**
- **Water content in electrode**
- **Poor cathode slurry mixing** (binder floating)
- **Separator shrinkage at high temperature** → internal short
- **Gas Swelling** (전해액 부족 또는 과다 부반응)
- **Separator porosity 설계 과소·불균일**
- **Low adhesion** (separator-electrode, folding risk)
- **External pressure → separator deform → short → fire**
- **Drop test → Jelly roll separator curled → short → fire**

### 4.3 Gen5+ 고전압 LCO 특화 위험 지표

| 위험 | 측정 시트 | PyBaMM 관련 가정 |
|------|---------|--------------|
| LCO 구조 열화 | XRD of Cathode at different SOC | LAM_pe 가속 (A3 간접) |
| 양극 열분해 | DSC of Cathode | 열 서브모델 (PyBaMM 범위 밖) |
| 열폭주 | ARC | 범위 밖 (Multi-physics) |
| Co 용출 | Co dissolution (ICP) | LAM_pe + 음극 Co 침적 |
| 양극 전위 (실측) | Three-Electrode | η_pos 분리 실측 |
| 전해액 산화 | CV | A5·A6 가정 검증 (첨가제 포함) |

---

## 5. 수명·측정 데이터 구조 (MP114 / MP205 기반)

### 5.1 측정 축

- **온도**: 15℃ (LT) · 23℃ (RT) · 45℃ (HT)
- **샘플**: #1 ~ #20 (설계 조건 × DOE × 프리셋 × MP 차수 교차)
- **측정 변수**:
  - **FC** (First Capacity)
  - **Cycle** (n)
  - **Thk** (두께)
  - **DCIR** (정상상태 저항)

### 5.2 DOE 분할 (MP114 기준)

- **Main** / **DOE** 분리
- **G1 분리막 / EL4** vs **TSC 분리막 / EL6** — 분리막·전해액 조합 DOE
- **Proto2 main** / **Gen5+ MP1 장수명** / **Gen5+ MP1 0.5C 자주검증** — 단계별 교차
- **SEU4** (Spec of End Use, 엔드유저 관점 가속 수명)

### 5.3 Category C (PyBaMM 검증) 직결

MP114 의 **LT/RT/HT × Thk × DCIR** 구조는 [[260422_report_cell_design_vs_pybamm]] §5.3.1 Category C 검증의 **모든 실측 항목을 한 파일에서 제공**한다:
- OQC Cell Capacity → FC 추이
- Avg. Cell Voltage → Life Cycle 전압 프로필 (MP103/204)
- RPT 용량 추이 → Cycle #n 커브
- DCIR → DCIR_LT/RT/HT
- Thickness at 1st full charge → Thk_RT

---

## 6. 개발 단계 흐름 (시간순)

```
EA (2024-10 ~ 2025-03)
  EA03 과제계획서 (241028)
  EA01 Cell Pack Proposal (250218)
  EA02 Spec meeting (250325)
  EA04 EA회의록 (250326)
    │
    ▼
PA (2024-08 ~ 2024-10)
  PA05 신규 소재검토서 (240828)
  PA04 Risk assessment (240828)
  PA07 제안승인회의록 (240925)
  PA01 Cell Design Spec 초안 (241010)
  PA06 선행개발제안서 (241028)
  PA02 DFMEA 초안 (251020)
    │
    ▼
Proto (2025-02 ~ 2025-06)
  Proto02 OQA data (250228)
  Proto03 Test report (250228)
  Proto05 Test ver2 (250316)
  Proto04 Cycle data (250603)
  Proto08 신규소재평가 (251211) ← 장기 관찰
    │
    ▼
MP1 (2025-07 ~ 2026-02)
  MP101 공정결과서 (250722)
  MP102 Cell Approve (250722)
  MP103 Test Report (250722)
  MP106 분해분석 (250722)
  MP104 Cycle data (250804)
  MP108 Test ver2 (250722)
  MP107 Cycle ver2 (251212)
  MP114 Cycle ver3 (260204)
    │
    ▼
MP2 (2024-11 ~ 2026-01)
  MP215 ER2 보고서 (241127) ← 중간 Exit Review
  MP201 PMP 전체 (250831)
  MP202 수율 (250831)
  MP207 분해분석 (250831)
  MP204 Test (250901)
  MP209 Test ver2 (250901)
  MP203 Pack Approval (250903)
  MP205 Cycle (251227)
  MP208 Cycle ver2 (251227)
  MP216 부품승인 (260105)
    │
    ▼
CA (2025-12 ~ 2026-01)
  CA01 과제완료 보고서 (251231)
  CA02 과제완료 회의록 (251231)
  CA03 Cell Design Spec 최종 🎯 (250526)
  CA04 DFMEA 최종 (260112)
```

---

## 7. 활용 가이드 — 특정 파라미터 찾을 때

| 찾으려는 것 | 먼저 볼 문서 |
|----------|-----------|
| **전극 두께·합제밀도·입자 D50** (설계치) | CA03 Spec 최종 (2.8~2.10, 3.7~3.9) |
| **전극 두께·합제밀도** (실측 산포) | MP201 Pressing Data / Coating Data (β-Ray Scanner) |
| **전해액 조성·첨가제** (설계치) | CA03 Spec 5.1~5.4 + PA05 신규 소재검토서 |
| **전해액 주액량 실측** | MP201 E.L Injection Data + Degassing Data |
| **초기 용량·IR 실측** | Proto02 OQA (Cell # 단위) |
| **수명 (사이클별 용량·두께·DCIR)** | MP114 Cycle ver3 (최종) / MP205 (MP2) |
| **고전압 LCO 구조 변화** | Proto08 XRD at different SOC |
| **열 안전성 (DSC / ARC)** | Proto08 DSC, ARC + CA04 DFMEA 110℃-5hr |
| **Co 용출 (LCO 특화)** | Proto08 Co dissolution + CA04 |
| **양극 단독 전위 (4.53V 영역)** | Proto08 Three-Electrode for Ca. potential + CA04 |
| **전해액 산화 안정성** | CA04 Cyclic voltammetry 시트 |
| **DCIR (SOC별)** | CA04 DCR-By SOC 시트 / MP114 DCIR_*  |
| **Failure mode 전체 맵** | CA04 DFMEA (최종) / PA02 (초안) |
| **공정 CTQ·Cpk** | MP201 PMP 전체 |
| **공정 Yield·Defect PPM** | MP202 수율 / MP101 |
| **개발 목표·배경·일정** | CA01 (최종) / EA03 (초기 계획) |
| **중간 Exit Review** | MP215 ER2 보고서 |
| **분해분석 규격·결과** | MP106 (MP1) / MP207 (MP2) |

---

## 8. PyBaMM 시뮬 Category 와의 연결

[[260422_report_cell_design_vs_pybamm]] §5 매핑에 따르면 CA03 의 63 필드가 PyBaMM 에 27/32/41% (Direct/Indirect/Out-of-scope) 커버된다. 본 인덱스는 그 매핑을 **실측·공정·위험 데이터와 연결**:

- **Category A (Direct)** — CA03 직접 변환 (두께, 폭, 용량 등)
- **Category B (Indirect)** — MP201 공정 실측 (합제밀도·LL) + Proto02 OQA (c_max 교정) + PA05 신규 소재검토서 (D50·비용량)
- **Category C (Validation)** — MP114 수명 + MP204 Test + Proto02 OQA + Proto08 심화 전기화학 ↔ PyBaMM 출력 비교
- **Category D (Out of scope)** — MP201 Packaging (pouch), MP106/207 분해분석 (외관), MP202 수율, CA04 Thermal abuse (ARC)

---

## 🔗 관련 문서

- [[Cell_Design_Specification_필드]] — Spec 63 필드 상세 스키마
- [[260422_report_cell_design_vs_pybamm]] — 개발 × 모델링 종합 보고서
- [[260422_analysis_pybamm_key_parameters]] — Key 파라미터 분석 + 가정 A1~A9
- [[MX배터리그룹_평가항목]] — MX 프로젝트 평가 항목 (Gen5+ 와 비교)
- [[Silicon]] — Si / SiC 음극 도메인 지식
- [[양극별_특성]] — LCO 등 화학계별 물성
- [[합제밀도와_전류밀도]] — 전극 설계 공식
- [[260419_GITT_확산계수_추출]] — GITT → D_s 측정 (Proto08/CA04 연계)
- [[EPF]] — Anode EPF 공정 (MP201 공정 단계)
