---
title: "Silicon 음극 (Si / SiC / SiC-Graphite 문헌조사 포함)"
tags: [Battery_Knowledge, 음극, 소재, SiC, literature-review]
type: knowledge
status: active
related:
  - "[[배터리_구성]]"
  - "[[합제밀도와_전류밀도]]"
  - "[[수명_해석_방향]]"
  - "[[Empirical_Degradation_Models]]"
  - "[[분리막특성평가법]]"
  - "[[양극별_특성]]"
  - "[[Knee_point]]"
  - "[[DCIR_측정_업체별]]"
aliases: [Si/Gr 음극 문헌조사, Silicon-Graphite Anode Review]
created: 2025-12-15
updated: 2026-04-21
source: "origin/Silicon.md + origin/SiC.md + SiC_Graphite_음극_문헌조사.md (2026-04-21 merged)"
---

> 📎 2026-04-21: `SiC.md` + `SiC_Graphite_음극_문헌조사.md` 를 이 문서에 병합.

# Silicon 음극

## 반응식

| **Si + 4.4Li⁺ + 4.4e⁻ ⇔ Si₄.₄Li** |
| ---------------------------- |
| 이론 용량 **Li₁₅Si₄: 3579 mAh/g** |
| (참고) LiC₆: 372 mAh/g |

## 보완 필요 (Si 순수 음극)

- Si 부피 팽창 메커니즘 (최대 ~300 % 팽창)
- SEI 파괴 및 재형성 사이클
- SiOx vs 순수 Si 비교
- 음극 설계 전략 (바인더, 도전재, 합제밀도 조건)
- 수명 특성 저하 원인 분석

---

# SiC (Silicon Carbon 복합 음극)

![[Pasted image 20260122152419.png]]

## 반응식 (Si vs SiC 비교)

| **SiC + 4Li⁺ + 4e⁻ ⇔ Li₄C + Si** |
| ---------------------------- |
| **SiC + xLi⁺ + xe⁻ ⇒ LixSiyC + (1 − y)Si (y < 1)** |

## 보완 필요 (SiC 복합)

- SiC 복합 음극 구조 설명 (Si + Carbon matrix)
- Graphite 대비 SiC 용량/수명 트레이드오프
- SiC 합성 방법 및 특성
- 전극 설계 시 SiC 함량 최적화 가이드
- [[Silicon#SiC/Graphite 문헌 조사]] 참조

---

---

# SiC/Graphite 문헌 조사

## 1. 개요

리튬이온 배터리의 에너지밀도 향상을 위해 실리콘(Si)과 흑연(Graphite)을 혼합한 복합 음극(Si/Gr blended anode)이 차세대 핵심 기술로 부상하고 있다. 실리콘은 이론 비용량 ~4,200 mAh/g으로 흑연(372 mAh/g) 대비 약 10배 이상의 용량을 제공하지만, 리튬화 시 300% 이상의 체적 팽창, SEI 불안정성, 전기적 접촉 상실 등의 문제가 상용화의 장벽이다.

본 섹션은 Si/Gr 복합 음극의 전기화학적 특성, 열화 메커니즘, 진단 기법, 개선 전략에 관한 주요 문헌 12편을 체계적으로 정리한다.

## 2. 조사 문헌 목록

### 2.1 사용자 제공 문헌 (2편)

| # | 저자 | 제목 | 저널 | 연도 | DOI |
|---|------|------|------|------|-----|
| 1 | C.M. Berg, R. Morasch, H.A. Gasteiger | Silicon Hysteresis and Voltage Relaxation Phenomena | J. Electrochem. Soc. | 2025 | 10.1149/1945-7111/adcda5 |
| 2 | Y. Jiang, G.J. Offer, J. Jiang, M. Marinescu | Voltage Hysteresis Model for Silicon Electrodes | J. Electrochem. Soc. | 2020 | 10.1149/1945-7111/abbbba |

### 2.2 추가 조사 문헌 (10편)

| # | 저자 | 제목 | 저널 | 연도 |
|---|------|------|------|------|
| 3 | Y. Jiang et al. (Imperial College) | Measuring Rapid Loss of Active Silicon in Si–Gr | ACS Appl. Energy Mater. | 2022 |
| 4 | J. Schmitt et al. | Degradation Modes Considering Aging-Induced OCP Changes | J. Power Sources | 2022 |
| 5 | H. Shin et al. (Hanyang) | Electrochemical-Mechanical Interplay in Si–Gr | Nature Commun. | 2021 |
| 6 | J. Choi et al. | Abrupt Capacity Degradation in Si-Based Anodes | Adv. Energy Mater. | 2025 |
| 7 | R. Bednorz, M. Gewald | SiC Anodes at Low Temperatures | Batteries | 2020 |
| 8 | W. Li et al. | Si/Gr Hybrid Anodes for High-Energy-Density Li-Ion | Adv. Energy Mater. | 2026 |
| 9 | M. Wetjen et al. | Degradation and Expansion: Pretension/T/C-rate/SOC | J. Energy Storage | 2025 |
| 10 | RSC review | Recent Progress in Si-Based Anode Materials | Ind. Chem. Mater. | 2024 |
| 11 | PMC review | Electrolyte Additives and Solid-State for Si | PMC | 2025 |
| 12 | F. Richter et al. | Operando Neutron Scattering on Si/C at Low-T | ChemSusChem | 2020 |

## 3. 실리콘 음극의 전압 히스테리시스 및 이완

### 3.1 전압 히스테리시스 모델 [문헌 2]

Jiang et al. (2020): 실리콘 전극 전압 히스테리시스 0차원 기계론적 모델
- 다단계 상전이 (multi-step phase transformation) 모델링
- 비정질화 + 결정화가 전압 히스테리시스의 주요 원인
- 충전: c-Si → a-LixSi → c-Li15Si4 (결정화, ~50 mV 이하)
- 방전: c-Li15Si4 → a-LixSi → 잔류 비정질 Si
- 열역학적 비대칭성이 ~150–300 mV 히스테리시스 유발

**BDT 관점:**
- Si/Gr 복합 음극 OCV 측정 시 긴 휴지 시간 필요
- dV/dQ 분석에서 실리콘 피크 위치가 방향 의존
- BMS 모델링에서 단순 OCV 테이블 불가

### 3.2 전압 이완 현상 [문헌 1]

Berg/Morasch/Gasteiger (2025): 실리콘 vs 흑연 전압 이완 비교
- Si는 전류 차단 후 수시간~수십시간 이완
- 옴 저항/반응 속도론/물질전달로 설명 범위 초과
- 화학-기계적 응력 이완이 추가 원인
- 흑연: ~30분 안정화 / Si: 계속 이완 중

**실용적 함의:**
- RPT OCV 측정 불확실성 증가
- RndV 해석 시 Si 함량별 이완 시간 확보 필요
- 과전압 분리 시 화학-기계 기여 별도 고려

## 4. 열화 메커니즘

### 4.1 Si-Gr Li⁺ Crosstalk [문헌 5]

Shin et al. (2021, Nature Comm.): operando XRD로 Li⁺ 이동 규명
1. **Li⁺ crosstalk**: Si-Gr 간 Li⁺ 재분배
2. **Li⁺ accumulation in Si**: 사이클링에 따른 잔류 리튬화 증가
3. **Graphite capacity depression**: Si 팽창 압력 → Gr staging 방해

**성능 결과:** 6 mAh/cm², 750+ cy, 800 Wh/L

**BDT 관점:**
- cycle_map 초기 activation 구간이 Gr 셀보다 뚜렷
- 용량 유지율 기준점에서 초기 activation 제외 권장

### 4.2 급격한 용량 감소 [문헌 6]

Choi et al. (2025, Adv. Energy Mater.): SiO/Gr sudden capacity decay
- RT + 1C 장기 사이클링에서 갑작스러운 용량 급감
- 원인: SiO 기계적 열화 → SiO-SEI crust 형성 → Li 소모
- 확산-유도 응력이 핵심 인자
- 고온 or 저 C-rate에서는 미발생 (Li⁺ 구배 작음)

**완화 전략:** 이완 단계 도입 → Li⁺ 농도 구배 감소

**BDT 수명예측 관점:**
- Si/Gr knee point 메커니즘 (SiO-SEI crust)이 Gr 셀과 다름
- 경험적 모델 $Q(n) = 1 - a \cdot n^b - c \cdot \exp(d \cdot (n-e))$의 exp 항이 이 현상 포착
- RPT 주기 촘촘히 (50cy 이내)

### 4.3 활성 Si의 급속 손실 [문헌 3]

Jiang et al. (2022, ACS AEM): 비파괴 dV/dQ 기반 DMA
- 0–30% SOC, 40°C, 4 kAh 충전량 → **Si 80% 손실 vs Gr 10% 손실**
- 낮은 SOC + 고온에서 Si 열화 최악
- 모든 조건에서 Si 열화 > Gr 열화
- Si 추가 용량은 수명 단축 대가 동반

### 4.4 팽창 및 열화 [문헌 9]

Wetjen et al. (2025, J. Energy Storage): 외부 압력/T/C-rate/SOC 영향
- Si stoichiometric window 에이징에 따라 확대
- SOH 알고리즘 고도화 필요
- T↑ → SEI 성장 + 전해액 분해 가속
- C-rate↑ → 기계적 응력 → 입자 파쇄
- SOC 윈도우↑ → 체적 변화폭↑

## 5. 열화 진단 기법

### 5.1 Half-Cell OCP 기반 DMA [문헌 4]

Schmitt et al. (2022, JPS): Si/Gr 블렌드 OCP 형상 변화 고려
- 기존 방법: 흑연 OCP 곡선 형상 유지 → 단순 shift+scale
- Si/Gr: Si가 더 빠르게 열화 → 형상 자체 변화
- 개선: 블렌드 OCP 모델 (Si + Gr 개별 스케일링)
- LLI, LAM_cathode, LAM_anode(Si+Gr) 개별 정량화

**오류 영향:**
- 형상 변화 무시 → LAM_anode 과소, LLI+LAM_cathode 과대

**BDT dVdQ 탭 연관:**
- 현재 BDT dVdQ는 양극/음극 반셀 OCP 기반 m, slip 피팅
- Si/Gr 음극: **블렌드 비율 추가 피팅 파라미터** 도입 필요

### 5.2 저온 충전 리튬 석출 [문헌 7, 12]

**Bednorz & Gewald (2020):**
- SiC + Ni-rich / 0–10°C / 0.2–1.5C
- Stripping method로 가역적 Li 석출 검출
- DVA로 Si 특성 용량 변화 추적
- 고 C-rate → Si 특성 용량 급속 손실

**Richter et al. (2020):**
- Operando 중성자 산란으로 Si/C 저온 리튬화 관찰
- 저온 Li⁺ 확산↓ → 금속 Li 석출 위험↑
- Si/C는 Gr 대비 Li 석출 임계 C-rate 낮음

**BDT 관점:**
- 저온(0–15°C) + 고 C-rate 충전 특히 주의
- Electrode Balance에서 음극 전위 < 0V 모니터링

## 6. 개선 전략

### 6.1 전해액 첨가제 [문헌 10, 11]

**FEC:**
- FEC → LiF-rich SEI → 기계적 내구성 + 이온 전도도
- 즉시 균일한 SEI 형성
- 진행 중 poly(FEC)로 SEI 균열 봉합
- 한계: FEC 소모 → 장기 효과 감소

**VC:** 가교 고분자 → 전해액 지속 분해 억제

**차세대:** LiFMDFB+FEC → 200cy 균일 SEI, 85% 유지(100cy), CE 99.5%, 400 Wh/kg

### 6.2 구조 설계 [문헌 8, 10]

**나노구조:**
- Core-shell: Si 코어 + C 쉘
- 다공성 복합체: 내부 공극으로 팽창 수용
- 다차원 캡슐화: 응력 분산

**계면 엔지니어링:**
- 구배 구조로 계면 응력 완화
- 전도성 프레임워크로 전자/이온 경로

### 6.3 프리리튬화 [문헌 10]

- LixSi 나노입자: 10 mV, 2000 mAh/g
- ASLS: LiF/Li₂O 쉘 30일 안정
- Roll-to-roll 전사: Gr ICE 99.99%, Si/C 99.05%
- Group14 SCC55™ (2024~): 에너지밀도 50%↑

## 7. 종합: BDT 개발 시사점

### 7.1 데이터 파이프라인 비교

| 영역 | 흑연 음극 | Si/Gr 복합 | BDT 대응 |
|------|----------|-----------|---------|
| OCV 이완 | ~30분 | 수시간~수십시간 | RndV 이완 시간 기록 |
| 전압 히스테리시스 | ~5–10 mV | 150–300 mV | 히스테리시스 모델 필요 |
| 초기 activation | 1–3 cy | 5–10 cy, crosstalk | 기준 용량 선정 시 제외 |
| Knee 메커니즘 | LLI + Li 석출 | SiO-SEI crust | exp 항 재조정 |
| dV/dQ 피팅 | 2성분 | 3성분 블렌드 | 블렌드 OCP 모델 |
| 저온 충전 | ~1C(0°C) | 더 낮음 | 안전 마진↑ |

### 7.2 PyBaMM 관점

현재 BDT PyBaMM 탭은 단일 소재 음극. Si/Gr 시뮬레이션:
1. 블렌드 전극 모델 (Si + Gr OCP 합성)
2. 전압 히스테리시스 (Jiang 2020 multi-step)
3. 차등 열화 (Si vs Gr 독립 LAM)
4. 기계적 결합 (stress-coupling)

### 7.3 수명 예측

- 비선형 열화: Si 초기 급속 → 둔화 → knee
- SOC 의존성: 0–30% / 40°C에서 Si 80% 손실
- 온도 가속: Si Ea 별도 파라미터
- 프로토콜 의존: 이완 단계 영향

## 8. 향후 방향

1. 실시간 Si/Gr 비율 추적 (비파괴 dV/dQ)
2. 기계-전기화학 결합 모델 (crosstalk + 팽창 + SEI)
3. 최적 충전 프로토콜 (Si/Gr 전용)
4. BDT dVdQ 탭 블렌드 OCP 모델 도입
5. PINN 기반 수명 예측

## 9. 참고문헌

1. Berg et al., *JES*, 172, 050516 (2025). DOI: 10.1149/1945-7111/adcda5
2. Jiang et al., *JES* (2020). DOI: 10.1149/1945-7111/abbbba
3. Jiang et al., *ACS AEM*, 5, 13367 (2022). DOI: 10.1021/acsaem.2c02047
4. Schmitt et al., *JPS*, 532, 231296 (2022)
5. Shin et al., *Nature Comm.*, 12, 2714 (2021)
6. Choi et al., *Adv. Energy Mater.*, 2502143 (2025)
7. Bednorz & Gewald, *Batteries*, 6, 34 (2020)
8. Li et al., *Adv. Energy Mater.*, 2505674 (2026)
9. Wetjen et al., *J. Energy Storage* (2025)
10. RSC review, *Ind. Chem. Mater.* (2024)
11. PMC review (2025)
12. Richter et al., *ChemSusChem*, 13, 529 (2020)

---

## 🔗 관련 문서

- [[SWCNT]] — 도전재
- [[합제밀도와_전류밀도]] — 전극 설계 파라미터
- [[분리막특성평가법]] · [[양극별_특성]] · [[CCS]]
- [[MFS_vs_MCS]] · [[MSMD]] · [[SME_분리막]]
- [[전고체_디자인]]
- [[충방전_매커니즘]] · [[Electrochemical_parameter]] · [[Knee_point]] · [[Empirical_Degradation_Models]] · [[DCIR_측정_업체별]]
