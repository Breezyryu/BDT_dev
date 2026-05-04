---
title: BDT Domain Context
aliases: [Context, Glossary Root, BDT 글로서리]
tags: [glossary, context, MOC, domain-language]
type: glossary
status: active
created: 2026-05-02
updated: 2026-05-02
---

# BDT Domain Context

> 배터리 데이터 분석 + 전기화학·empirical 모델링 작업의 **도메인 root 글로서리**.
> 박사급 peer 청중 (CL3·CL4) 에게 의미 명료하도록 **canonical term 합의 결과** 만 모은다.
> 일반 배터리 용어는 [[21_electrochem/!용어]], 시뮬 deep-dive 는 [[30_modeling/시뮬레이션_용어사전]] 참조.

---

## Language

### 수명 예측 (Lifetime Prediction)

**승인 수명** (Homologation / Qualification Lifetime):
양산 승인 게이트 (**PRA**) 통과를 위해 **선행PF** 데이터로 23·45°C 조건 수명을 예측한 결과. **시험 매트릭스 = 100cy 마다 0.2C RPT + 급속충전 + 1.0C·0.5C 스텝방전. 1000cy 기본 / 1600cy 여유**. **80% retention 도달 시험은 진행 안 함 — fit extrapolation 의존** (Flagged #7).
_Avoid_: 인증 수명, 양산 수명, 승인수명 (띄어쓰기 일관성)

**EU 수명** (EU Regulatory Lifetime):
EU 시장 출시 충족을 위한 수명 예측. 다층 anchor: (i) **EU 2023/1542 Battery Regulation** (Battery Passport · SOH 보고 · 수명 minimum guarantee) + (ii) **ESPR** (Eco-design Sustainable Products) + (iv) **EU 소비자 보호법 측 SOH/RUL guarantee**. **시험 매트릭스 = 100cy 마다 0.2C RPT + 급속충전 + 0.5C 방전** (사용자 메모 — 정확도 stub, 배터리 업체 EU protocol 별도 확인 필요). **Input 우선순위 = (1) 배터리 업체 EU 시험 데이터 제출, (2) 내부+업체 데이터로 예측 보완**.
**EU 수명 SW 운영자 = 본인 MBO 측 X** (2026-05-04 grill #2 확정). 1순위 input 이 업체 시험 데이터이므로 본인 MBO "수명 모델링" 항목에서 EU 수명 SW 빠짐. BDT 6번 탭 (`self.tab_4`, EU 수명 예측) 은 인계 자산이지만 본인 운영 deliverable 아님 — 업체 데이터 input + 보조 검증 측. **본인 인계 자산 운영 = 7번(승인) + 8번(실수명) 탭만**.
_Avoid_: 단일 EU 규제 (다층 anchor), 승인 수명과 동일 매트릭스 가정 (방전 부하 다름), EU 수명 SW 를 본인 MBO 측 deliverable 로 oversell

**실사용 수명** (Real-world / Service Lifetime):
다양한 V·T 조건의 현장 사용 수명. **두 도구 역할 분담**: 측정 envelope 안 = **Empirical interpolation**, 측정 envelope 외 = **EC model extrapolation**.
_Avoid_: **"실수명"** (코드 식별자 only — 보고·발표·논문에서 사용 금지), 실제 수명, real life

**Empirical interpolation** (4번 트랙, 시간 70%):
측정 grid (T=23/35/45°C, V상하한 등) 의 **envelope 안** 에서 보간으로 다른 조건 수명 추정. 23·35·45°C 데이터 있으면 28°C 예측 가능. **extrapolation 불가** — envelope 밖은 권한 없음.
_Avoid_: empirical extrapolation (한계 위반)

**EC model extrapolation** (5번 트랙, 시간 30%):
P2D / MSMD / GH-MSMD 물리 기반 모델로 측정 **envelope 외** 영역 (새 chemistry · 새 V·T 조건 · design 변경) 예측. 한계 = 파라미터 추정 **identifiability + UQ**.
_Avoid_: EC model 을 envelope 안 fit 도구로 사용 (overkill — empirical 영역)

**Functional form fit** (학계 표준 form 기반 empirical fit):
NREL Smith calendar √t Arrhenius · Wang/Ploehn cycle DOD-coupled · Spotnitz dual-mechanism 등 학계 검증 form 위에서의 fit. ADR-0003 의 form-mediated extrapolation 의 backbone.
_Avoid_: 임의 polynomial / spline (raw — ADR-0003 금지)

**Form-mediated extrapolation** (ADR-0003):
학계 표준 functional form 위에서의 limited extrapolation. ADR-0001 의 "empirical extrapolation 금지" 의 예외 카테고리. 허용 조건: (1) form 의 학계 근거 명시, (2) extrapolation 영역 (예: 1.5~2x cycle) 명시, (3) UQ 정량.
_Avoid_: raw extrapolation 과 동일시

**Raw extrapolation** (ADR-0003 금지):
검증된 form 없이 polynomial / spline 등으로 envelope 밖 외삽. **금지**. 수명 예측은 form-mediated 만.

### 셀 설계 값 ↔ P2D 파라미터 매핑 ([[31_software_dev/adr/0004-cell-design-to-p2d-parameter-mapping|ADR-0004]])

**(A) Direct 1:1 매핑**:
셀 spec 에서 직접 추출. ε_act (합제밀도×활물질비율/진밀도), R_s (D50), L (두께), c_max (이론).

**(B) Indirect / Derived**:
(A) 위에서 학계 표준 form 으로 유도. a_s = 3·ε_act/R_s, **τ = ε^-0.5 (Bruggeman, Gen6 측 검증 필요)**, ε_elyt 보존식.

**(C) Fit-driven**:
측정 데이터로 fit. D ↔ GITT, k_0 ↔ EIS, OCV ↔ half-coin GITT (일부 셀만).

**(D) 문헌 default**:
활물질/전해액 spec 으로 reference. σ, κ, Si volume expansion factor (Schweidler 2018).

**Physics-based parameter transfer** (ADR-0004 핵심):
(A) Direct 매핑 변동에 따른 (C) Fit-driven 파라미터의 셀 간 transfer 는 학계 표준 form 위에서 — D_eff ∝ ε^a/τ, k_0 ∝ a_s, OCV blend = Si-Graphite 가중 평균 (Lain-Brandon 2019). **Raw transfer 금지** (form 없이 단순 scaling 금지 — ADR-0003 의 raw extrapolation 정합).
_Avoid_: 단일 셀 fit 결과를 다른 셀에 그대로 적용 (microstructure 변동 무시), raw scaling

### 보고자료 형식 ([[31_software_dev/adr/0006-reporting-format-core-and-appendix|ADR-0006]])

**핵심 deck** (Core deck):
3 cadence × 청중 차등 — 그룹장 (8주, 3~5 슬라이드 KPI+detail) / 테크미팅 (6개월, 3~5 슬라이드 결과+그래프) / 주간그룹공유 (3개월, 3~5 highlight). pptx, bullet 스타일.
_Avoid_: 한 deck 모든 청중 동시 만족 시도, 단락 / 문장 형식

**Appendix 풀** (Full appendix):
같은 pptx 슬라이드로 구성 (별도 docx 아님). 박사급 peer 측은 풀 detail (frame · methodology · UQ · ADR cross-link · 학계 reference). 그룹장 측은 minimal + 핵심 보강.
_Avoid_: docx appendix, 핵심에 detail 흡수

**Bullet 텍스트 .md** (Pptx component source):
한 슬라이드 = 한 .md 섹션 (`## 제목`). Bullet `-` depth 2 이내. Bullet 당 한 줄 (~30~50자). 학계 reference / ADR cross-link = footnote.
_Avoid_: 단락 형식, depth 3+, bullet 당 multi-line

**pptx 수동 조립 정책**:
**pptx 자체는 본인 수동 조립**. AI / wiki / BDT 자동 .pptx 출력 ❌. AI / wiki / BDT = pptx component 측 (이미지 PNG/SVG, 표 XLSX, bullet .md).
_Avoid_: AI/BDT 자동 .pptx 생성 시도

### 업무 flow 효율화 ([[31_software_dev/adr/0007-workflow-efficiency-pipeline|ADR-0007]])

**자동 연결 pipeline (1순위)**:
(4) wiki ingest + (5) 보고 component 의 자동 연결. BDT 분석 결과 → docs/*.png + docs/*.xlsx + wiki/.md (cadence 별 템플릿) → 본인 수동 조립 → docs/*.pptx.
_Avoid_: retroactive ingest (분석 후 며칠/주 뒤), one-off scripting 누적

**Component re-use**:
같은 PNG / .md / .xlsx 가 여러 cadence (그룹장 / 테크미팅 / 주간) 에 재사용. 보고 deck 별 reference 카운트 = 효율화 input 지표.
_Avoid_: cadence 별 component 재작성 (재사용 frame 위반)

**Cognitive load ↓**:
frame 잡혀 있어 새 분석·보고 시 mental overhead 감소. ADR-0001~0006 + CONTEXT v2 의 운영 효과. 정성적 self-report.

**효율화 안티패턴 (ADR-0007 금지)**:
- One-off scripting 누적 (재사용 X)
- Retroactive wiki ingest
- PPT 자동 조립 시도 (ADR-0006 위반)
- 그룹원 측 ignored (ADR-0005 양립 위반)

### BDT 자동화 테스트 + 스터디 ([[31_software_dev/adr/0008-bdt-test-and-study-automation|ADR-0008]])

**Test frame (pytest-qt + pytest-mpl + pytest-snapshot)**:
새 frame 처음부터 구축. 기존 `tools/test_code/` 20+ 자산은 reference 만 (사용자 미인지 — 작성자 본인 X). pytest-qt = PyQt6 UI test, pytest-mpl = 그래프 image regression, pytest-snapshot = 데이터 baseline diff.
_Avoid_: 기존 test_code 의 무조건 활용 (frame 정합 X), 단순 unittest.TestCase

**4 Fixture 표준** (병목 4개 직접 매핑):
- (α) 표준 데이터 경로 — `@pytest.fixture(scope="session")` 의 PNE/Toyo/자주검증 sample 경로
- (β) 전처리 골든 레퍼런스 — parquet/pickle baseline + pytest-snapshot diff
- (γ) 그래프 골든 image — `@pytest.mark.mpl_image_compare` PNG baseline
- (δ) 저장 데이터 schema — tools/schema_verify.py 통합 자동 체크
_Avoid_: 매번 데이터 경로 입력 / 전처리 결과 수동 확인 / 그래프 시각 비교 / 저장 데이터 spot check

**Dual-environment fixture**:
사외 PC (subset, AI 가능) + 사내 PC (full, AI 금지). ENV var (`BDT_TEST_ENV=local|office`) 또는 conftest fixture chain 분기. 사외에서 작성된 test 가 사내에서 정합 동작.
_Avoid_: 단일 환경 fixture, 환경 별 별도 test code

**Test = 학습 도구 + QA 양립** (ADR-0005 의 (6) 문서 layer specialization):
test name = 한국어 시나리오 + docstring = 도메인 매핑 + ADR cross-link. `pytest --collect-only` 출력 → `wiki/31_software_dev/test_index.md` 자동 ingest. Test 모듈 별 학습 노트 → `wiki/31_software_dev/study/<module>.md`.
_Avoid_: 영어-only test name, docstring 부재, 학습 측 무시

### 전문가 수준 코드 + 스터디 frame ([[31_software_dev/adr/0009-expert-level-code-and-study|ADR-0009]])

**전문가 수준 패턴 (Production code)**:
@dataclass (PEP 557) + Protocol typing (PEP 544) + Type hints + context manager + pathlib.Path. Strategy / Factory / Adapter / Observer 의식적 사용. 학계/OSS 표준 (PyBaMM / NumPy / scikit-learn 수준).
_Avoid_: 단순 함수 only (학습 정체), class 추상화 회피 (frame 부정합)

**학습 docstring 표준**:
한국어 한 줄 요약 + [Detail 학습] (배경/입력/출력/부작용) + [전문가 frame] (패턴/학계 reference) + [참조] (ADR / wiki cross-link). 모든 public 함수 / class / dataclass / Protocol.
_Avoid_: docstring 부재, 영어-only, ADR cross-link 부재

**스터디 자료 4-layer (S)**:
- Layer P: inline docstring (위 표준)
- Layer Q: test docstring (ADR-0008 정합)
- Layer R: 자동 생성 (pdoc / sphinx / `pytest --collect-only` → wiki)
- Layer W: wiki 직접 노트 (`wiki/19_bdt_history/learning/<topic>.md` + ADR cross-link)
_Avoid_: 단일 layer (스터디 자료 빈약), 자동만 (수동 보강 부재)

**Code → Test → Study cycle**:
production code → pytest → test_index.md 자동 ingest → study/<module>.md (보강) → ADR cross-link / 학계 reference. 학습 trajectory 의 1 cycle.

### Si 음극 보호 — 만방 voltage 상향

**만방 (滿放) voltage**:
Full discharge cutoff voltage. 셀의 방전 끝점 voltage. 만방 voltage 가 낮을수록 SOC 하한 ↓ → 더 깊게 방전 = Si 음극 측 over-delithiation 가속.
_Avoid_: 만충 (滿充, full charge) 과 혼동, "방전 voltage" (모호)

**만방 voltage 상향** (Full-discharge-voltage Up-shift):
Si+Graphite 음극 보호용 운영 정책. 방전 cutoff voltage ↑ (예: 3.0V → 3.2V) → SOC 하한 ↑ → Si cyclic stress range ↓ → SEI fracture ↓ + Si full delithiation 회피 (LAM 보호) → 수명 ↑. **trade-off = 사용 capacity ↓**. 메커니즘 frame 은 **선행Lab 「배터리 소재 전공자」 파트** 가 결정 (본인 「성능·수명 해석」 파트의 모델링 input). 학계 reference: Wood et al. 2015, Schweidler et al. 2018, Berla et al. 2014.
**MBO 1.1.2 도전 "방전 영향도 추가 검토" trace** (2026-05-04 grill #2 확정): 본 항목이 정확한 자리. Deliverable = BDT 8번 탭 ('실수명 예측') 의 (i) 만방 V 상향 input + (ii) DOD 정의 운영 + (iii) Si-protection factor 추가.
_Avoid_: 만충 voltage 와 혼동, single-shot voltage (만방 보호 cycle 빈도 별도 input)

**만방 보호 cycle 빈도**:
"100cy 마다 1회 만방 V 상향" 같은 binary cycle parameter. **'실수명 예측' 탭의 fit form input 으로 흡수 — Si 보호 효과 정량 anchor**.
_Avoid_: 모든 cycle 동일 만방 V 가정 (frame 결손)

**Si-protection factor**:
'실수명 예측' fit form 의 cycle fade 항에 곱해지는 Si 보호 multiplier. **DOD 정의 흡수** (DOD = SOC100 - SOC하한, 만방 V 상향 → DOD ↓ → cyclic stress range ↓) + Si 함량 (Gen6+ 15% / Gen6++ 25%) 별 sensitivity. **DOD 정의 운영 = 전임자(랩장님) cross-check 필요** (Flagged #9).
_Avoid_: Gen6 Gr only 셀에도 동일 적용 (Si 함량 0% 셀은 보호 효과 ≈ 0)

**측정 envelope** (Measurement Envelope):
ADR-0001 의 empirical ↔ EC model division line 의 운영 정의. 차원 = **T × V상하한 × 사이클 누적·calendar 시간 (수명 축)**. 형식 = **grid points only (strict)** — 측정 점만 envelope 안, 그 외 (모서리·grid 사이 보간 영역)는 정의상 envelope 밖. **dynamic** — 시험 진행 따라 수명축 boundary 확장.
_Avoid_: hyperrectangle 형 envelope (corner 측정 부재 흡수), 정적 envelope (수명축 무시), 단일 셀 envelope (현실은 transfer 보강 — 다음 entry)

**유사 셀 데이터 transfer** (Similar-cell Data Transfer):
측정 envelope 가 단일 셀로 부족할 때 **다른 PF · 모델 · 제조사** 의 유사 거동 셀 데이터로 envelope 보강. 협력사 데이터 + 자주검증 데이터 + 사내 시험 데이터 의 제한된 자원 안에서 운영. **Transfer 신뢰도 정량화 = 박사급 peer challenge 1순위 영역** (미해소 — Flagged #5).
_Avoid_: 단일 셀 envelope 가정, transfer 데이터를 직접 측정과 동일 신뢰도 취급

### user 시나리오 데이터

**복합 저장 히트맵** (Composite Storage Heatmap):
SOC × 온도 2D 히트맵에 체류 사이클·누적 시간 discrete 정보를 누적한 stationary 분포 sample. 빅데이터 user 시나리오의 **실제 형식** — 시계열 trace 가 **아니다**.
_Avoid_: user trace (시계열 아님), telemetry log (권한 없음)

**유저 cohort** (User Cohort):
사용 패턴 별 분리 모집단. 현재 활성 = **만충고온 노출 상위 유저** + **일반 유저** 의 **2-bin cohort**. 단일 분포 가정 X.
_Avoid_: average user, single distribution

**Flagship 모집단**:
form factor 5종 (bar/foldable/wearable/tablet/notepc) 中 자료 풍부한 **flagship 모델만** 활성. wearable·tablet·notepc 등은 추후.

### BMS 알고리즘 / 데이터 source

**FG** (Fuel Gauge):
배터리 측 단순 칩. SOC 추정 + (온도 × SOC) 히트맵 빅데이터 source. 본인 frame 의 **복합 저장 히트맵** 의 main source.
_Avoid_: BMS 일반화 (FG ≠ BMS — FG 는 SOC 만, BMS 는 SOH·진단·제어 포함)

**ECT** (시스템 side BMS):
시스템 board 측 BMS 알고리즘. 양음극 potential 추정 + SOC / SOH / 내부단락. **S.LSI** 제작. 일부 출시 모델에 **hidden** 탑재 (저가 모델). Graphite 기반, Silicon 고도화 중. **2026-08 이관 → 본인 직무3 의 내재화 검토 대상**.
_Avoid_: BMS 일반화

**SBP** (배터리 PCM MCU BMS):
배터리 팩 PCM 의 MCU chip 측 BMS 알고리즘. SOC / SOH / 내부단락 + **Swelling%** 추정. **NVT** 제작. 단가 ↑ 예측 성능 ↑. Graphite·Silicon 일부 detect 가능. 선행랩 알고리즘 인력이 NVT 와 협업 검증 중.
_Avoid_: BMS 일반화

### 외부 IC 업체

**S.LSI** — ECT 제작 (Samsung System LSI 추정)
**NVT** — SBP 제작 (외부 IC 업체)

### 스웰링 / Swelling

**스웰링** (Swelling):
배터리 셀의 부피 증가 현상. **Hard swelling** (정상 cell expansion) + **Gas swelling** (이상 — 전해액 분해·SEI 부산물) 의 합. 현재 BDT/모델링 frame = **정상 hard swelling 예측·추정만 — empirical 기반, 신뢰도 높지 않음 인정**.
_Avoid_: physics 3-항 분리 (Si expansion + gas + thermal) 의 in-situ 측정 (한계), single-shot empirical 의 신뢰도 과대 평가

**스웰링 EC 모델링 한계 (학계 합의, [[30_modeling/swelling_ec_modeling_literature]])**:
- **활물질 단위** P2D + stress = 표준 (Christensen-Newman 2006). Si / Graphite expansion 정량화 가능.
- **Cell-level pouch swelling** = 활발한 최신 영역 (**Mohtat 2021 Nature Comm**, **Louli·Dahn differential thickness**). 100사이클 만충 두께 측정과 결합 가능.
- **Hard / Gas 분리 in-situ** = 여전히 한계. DEMS 로 gas component 분리 가능하나 cell-level swelling 과 결합 미정량.
- **★ House Code (MSMD/GH-MSMD) 자체에 mechanical domain 포함 가능성** — raw 분석 (D1) 시 cross-check 우선. 확인 시 5번 트랙 substance 잠재 확장점.

**만충 두께 측정** (Full-charge thickness measurement):
**100사이클마다** **만충 + 상온** 조건에서 셀 두께 직접 측정. 초기 만충 두께 대비 증가율 기록. **단위 = % + mm 둘 다**. **사내 + 업체 cross-check**. **BDT 사이클 탭의 스웰링 데이터 입력 source**. **출시 승인 (PRA) 조건의 일부**.
_Avoid_: SBP Swelling% (별개 source — 단말 online 추정), 다른 측정 빈도 (100사이클이 표준)

**SBP Swelling%** (저항 기반 online 추정):
SBP MCU 가 단말에서 **저항 증가율** 으로 추정한 두께. 모바일 제품 online 진단용. **BDT 입력 데이터가 아니다** — 만충 두께 측정과 별개. 알고리즘 인력이 고온복합열화 충방전 시험으로 검증.
_Avoid_: 만충 두께 측정과 동일시, ground truth 취급

**Hard swelling**:
정상 cell 동작 중 발생하는 cell 부피 expansion. **현재 BDT/P2D 측 예측·추정의 target**.

**Gas swelling**:
전해액 분해·SEI growth 부산물 swelling. **현재 측정 분리 불가** — hard swelling 과 합산으로만 관측.

### 셀 Platform / 양산 게이트

**선행 PF** (Advanced Platform):
양산 release 전 단계의 셀 platform 세대. MX 차세대 product 적용 검토 중. 현재 활성 = **Gen6** (Gr only) · **Gen6+** (SiC 15%) · **Gen6++** (SiC 25%).
_Avoid_: prototype, dev cell, 개발셀 (모호)

**SiC 함량 — 두 축 분리 운영**:

- **SiC sensitivity sweep** (시뮬 학습용): **5 / 10 / 15%** 등간격 sweep. P2D 시뮬에서 Si 함량 vs 성능 monotonic curve 를 박사급 peer 가독성 표준 frame 으로 학습.
- **Gen6 PF SiC 함량** (양산 실제): Gen6+ **15%**, Gen6++ **25%** (cf. Gen4+ / Gen5+VB = 5%). 비등간격 — sensitivity curve 위에 **양산 점 overlay** 로 표현.
- _Avoid_: 시뮬 함량 = 양산 함량 동일시 (혼동 발생 — 두 축 분리)

**PRA** (Production Readiness Approval, 양산승인):
시 생산품 결과로 과제 목표 달성 + 양산 가능 여부를 승인. **승인 수명 예측의 anchor 게이트**. (cf. PKA / DIA / PIA / DVR / PVR / SRA / PSA / MSA — [[21_electrochem/!용어#개발]])

### BDT 9 탭 (전임자 = 랩장님 인계 + 본인 고도화)

**최종 flow**: 1·2·3 (입력·전처리) → 5·6·7·8·9 (분석·예측·시뮬).

**Primary user = 본인 + 그룹원 80명 양립** ([[31_software_dev/adr/0005-bdt-dual-primary-user|ADR-0005]]). 양립 운영 기준 6 항목:
1. Default + Advanced 분리 (그룹원 default · 본인 advanced)
2. 자동화 layer 분리 (GUI 공통 + Script/CLI 본인 전용)
3. 검증 게이트 2종 (본인 회귀 1순위 + 그룹원 smoke test 2순위, 두 측 모두 통과)
4. 성능 baseline 양 측 (본인 PC + 그룹원 노트PC 저사양)
5. 보고 source (본인 박사급 peer 1순위 + 그룹원 같은 output form 재사용)
6. 문서 layer 분리 (본인 작업 노트 + 그룹원용 사용 가이드 후속)

| 순 | 표시명 | ObjectName | line | 역할 |
|----|--------|-----------|------|------|
| 1 | **현황** | `self.tab` | `:17701` | 그룹 충방전기 시험 현황 + 데이터 경로(online). 네트워크 1h sync, 완료 시험 네트워크 검색 |
| 2 | **사이클데이터** | `self.CycTab` | `:17765` | 경로 → 사이클(수명) / 프로파일 분석. **8 sub 기능: 율별 충방전 / 0.2C RPT dV/dQ / Si hysteresis / ECT V·I·T 추출 / GITT / DCIR**. Cycle (`tab_5`) + Profile (`tab_6`) 2 sub-탭. |
| 3 | **패턴수정** | `self.tab_2` | `:17822` | Toyo / PNE 시험 패턴 수정 (충방전기 입력 측) |
| 4 | **세트 결과** | `self.SetTab` | `:17857` | 단말 배터리 로그 + **ECT 알고리즘 세트 내 동작 분석** (직무3 도구 backbone) |
| 5 | **dVdQ 분석** | `self.dvdq` | `:17883` | RPT 0.2C 의 dV/dQ · dQ/dV. **fresh cell 양음극 half-coin peak·shift → full cell 분해 → 양음극 열화 분리 추정** (ICA/DVA + LLI/LAM frame) |
| 6 | **EU 수명 예측** | `self.tab_4` | `:17910` | EU 규제 만족 수명 시험 예측 empirical |
| 7 | **승인 수명 예측** | `self.tab_3` | `:17943` | **0.2C RPT + 가속 다중사이클 (급속+0.5C / 1.0C+0.5C 스텝) 100사이클 묶음. 0.2C RPT 방전용량 empirical 수명** (PRA 게이트) |
| 8 | **실수명 예측** | `self.FitTab` | `:18042` | 다양한 조건 (저항/수명·사이클/저장·장수명적용/미적용·단일셀/탭 PCM) empirical. **Si 음극 만방 상향 미반영 — 본인 추가 작업** |
| 9 | **전기화학Sims** | `self.PyBaMMTab` | `:18043` | PyBaMM 기반 성능 모델링. **셀 설계 값(전류밀도·합제밀도·로딩) ↔ P2D 파라미터 매핑 필요**. 최종 = 수명 시뮬. House Code 비교 → GH 계산 속도 흡수 |

> **표시명 표기 변종** (코드 정정 후속 작업): "Eu 수명 예측" → "EU 수명 예측", "전기화학Simgs" → "전기화학Sims", "세트 결과" → "세트결과" (공백 정합).

> **'실수명 예측' 탭** UI 표시명 "실수명" 은 legacy — canonical "**실사용 수명**" 으로 정합 정정 예정 (별도 작업).

### 외부 frame 정합 — 부서 KPI · 운영방향 · 팀 도전 Project ↔ MBO (2026-05-04 grill #6)

**부서 KPI 매핑 (4 항목 中 3 항목 정합)**:
- **차별화 핵심 기술 발굴 + 완성도 향상** ↔ MBO 1.1.2 도전 (Gr+SiC 성능·dV/dQ·GITT) + 4번 (Si-protection factor)
- **설계 시뮬레이션을 통한 부품 설계 완성도** ↔ MBO 5번 트랙 정확 정합 (Gen6 P2D + Gr+SiC 성능 + 온도별 예측)
- **미래 기술 + 부품 Integration 역량** ↔ MBO 7번 (ECT/빅데이터 직무3 진입) + 2.1 AX
- **New Form-Factor / Slim화 부품 개발** ↔ ❌ **본인 직접 X** (수명·성능 예측 측만, 부품 개발 X)

**운영방향 매핑 — 협력사 협업 deepening 의 본인 측 trace** (2026-05-04 grill #6 확정):
- "협력사들과 한단계 깊은 수준의 협업" ↔ **MBO 6번 트랙 (측정 Campaign) 의 측정 발주 + QA 가 대표적 deepening 측**.
- 즉, 코인셀/삼전극 측정의 (i) 어느 셀·어느 조건 측정할지 결정 + (ii) 업체 발주 + (iii) 받은 데이터 QA 로의 cycle 자체가 "한단계 깊은 협업" 의 substance.
- _Avoid_: 단순 데이터 수령 (receiver) 만으로 협업 deepening 주장

**팀 도전 Project — Simulation 고도화 (3년차) 본인 role** (2026-05-04 grill #6 확정):
- ★ **본인 = Main contributor** — 5번 트랙 (전기화학 모델링) owner 로서 TF 핵심 기여자.
- TF substance = **전기화학 모델링** — Gen6 계열 P2D + ML 기반 예측 + 신규 재료 특성 제안.
- **MBO score 측**: TF 활동은 3.1 (TF 5~10점/건) 측 별도 점수 + 5번 트랙 substance 자체는 1.1 Project 결과 측 점수 → **dual-credit**.
- 운영방향 "재료비 혁신·원가 절감" 의 본인 기여 = TF 의 신규 재료 특성 제안 측.
- 다른 2 TF (AI Semantic Risk Assessment / AI Centric Device) = 본인 직접 X 또는 wiki 측 간접 협업.
_Avoid_: 5번 트랙 시간 비중 ~20% 가 TF main contributor + 1.1 일반/도전 정합에 충분한지 별도 검증 필요 (Flagged #21)

### AX 운영 — Gauss (사내) + 외부 LLM (사외) 듀얼 트랙 (MBO 2.1, 2026-05-04 grill #5)

**Gauss** (사내 LLM, 구축 예정):
사내 PC 측 운영 가능한 사내 모델. **사내 데이터 접근 허용** (Fasoo·NASCA DRM 정합). **현재 구축 예정 — 시점 미확정**. 본인 MBO 2.1 AX 측 사내 deliverable 의 anchor.
_Avoid_: 외부 LLM (Claude/Copilot) 의 사내 PC 사용 (정책 위반), Gauss 도입 전 사내 PC 측 AX 작업 시도

**AX deliverable 운영 패턴**:
- **사외 PC** = 외부 LLM (Claude Code 등) 산출물 생성. 사내 데이터 접근 X. 산출물 = 비-AI Python 모듈 / wiki .md / fit form 정의 / SOP.
- **사내 PC (Gauss 도입 후)** = 사내 데이터 측 작업 가능. 산출물 = 사내 한정.
- **현재 (Gauss 도입 전)**: 사외 PC 산출물 → 비-AI 형태로 사내 적용.

**MBO 2.1 AX 3건 확정 (2026-05-04 grill #5)**:
1. **개발자용 SW 코드 리팩토링** — BDT proto_.py 모놀리식 (22,838줄) 측 모듈 분리 / refactor (1·3번 트랙). 사외 LLM.
2. **수명 결과 요약 텍스트 구성** — LLM 기반 수명 예측 결과 자동 요약 → 보고 component (4번 트랙, [[31_software_dev/adr/0006-reporting-format-core-and-appendix|ADR-0006]] 정합). 사외 LLM.
3. **BDT SOP LLM 기반 작성** — 배터리데이터툴 그룹원 80명 측 사용 가이드 + 운영 SOP (1·3번 트랙, [[31_software_dev/adr/0005-bdt-dual-primary-user|ADR-0005]] 그룹원용 사용 가이드 측 정합). 사외 LLM, Gauss 도입 후 사내 측 보강.

### dV/dQ 양/음극 분리 — 일반 vs 도전 분리선 (MBO 5번 트랙, 2026-05-04)

**dV/dQ 일반 분리 (MBO 1.1.1 일반)**:
**fresh cell** half-coin 측정 기반 **양극 + 흑연 2-component** separate 분리. **Graphite only 음극** (Gen5 / Gen6 측) — peak 분리 명료. BDT 5번 탭 (`self.dvdq`) baseline.
_Avoid_: Si 포함 셀에 동일 적용 (peak overlap 심함 — 도전 영역), aged cell 직접 분리 (fresh anchor 없으면 LLI/LAM 추정 불가)

**dV/dQ 도전 분리 (MBO 1.1.2 도전 — Gr+SiC 혼합 음극 dV/dQ 분리 모듈)**:
**Gr+SiC 혼합 음극** 의 overlap peak deconvolution. **대상 = SiC 5% (Gen4+ / Gen5+VB) ~ SiC 25% (Gen6++)** 함량 전 영역. **OCV blend 비선형 분리** (Lain-Brandon 2019). Si peak 와 Gr peak overlap 심함 → 단순 separate 불가, blend ratio fit 필요.
_Avoid_: 단순 weighted sum 으로 Si peak 분리 (비선형성 무시), Gen6++ (25%) 만 도전이라고 한정 (Gen4+ 5% 부터 이미 overlap 영역)

### 측정 Campaign 운영 (MBO 6번 트랙, 2026-05-04 신규)

**측정 Campaign Owner** (Measurement Campaign Owner):
본인의 측정 데이터 운영 역할. (1) 코인셀/삼전극 단위는 일부 직접 측정 + (2) 리소스 부족 시 업체 발주 + (3) 어느 셀·어느 조건 측정할지 결정 (campaign 설계) + (4) 받은 데이터 QA + (5) 분석. **MBO "성능 모델링 — 코인셀/삼전극 제작, 측정 Process 확립"** 의 substance.
_Avoid_: "본인은 시험 직접 X" 단정 (구버전 메모리 — 2026-05-04 정정), 측정 Process = 단순 매뉴얼화 (실제는 campaign 설계 + QA + 발주 운영 체계)

**소재 EC 물성 DB** (Material EC-property Database):
6번 트랙의 직접 측정 + 업체 발주 + 문헌 default + half-coin GITT 결과를 통합한 **셀별 · 재료별 (양극 / 흑연 / 실리콘) 물성 자산**. [[31_software_dev/adr/0004-cell-design-to-p2d-parameter-mapping|ADR-0004]] 의 4 카테고리 (Direct / Derived / Fit-driven / 문헌) 에 따라 stratify. **5번 트랙 (EC modeling) 의 input source** + dV/dQ 양/음극 자동 분리 SW 의 anchor library. 형식 = parquet/wiki ingest/PostgreSQL 미정 (Flagged #11).
_Avoid_: 단일 셀 물성 DB (transfer 정합 X), 측정 출처 unstratified (Direct vs Fit-driven 혼동), DB 를 단순 spreadsheet 로 운영 (재현·UQ 추적 불가)

### ECT/빅데이터 트랙 어휘 (MBO 7번 트랙, 2026-05-04 신규)

**ECT MR** (ECT Master/Mass Release? — 미정 Flagged #13):
S25+/S26 시리즈의 ECT 알고리즘 release 산출물. **본인 측 검토** = empirical 측 measurement envelope · 양음극 potential 추정 정합 · SoC/SoH 추정 정확도 anchor 제공. 직무3 BMS 인력과 협업.
**BDT 탭 cross-link** (2026-05-04 grill #3 확정): **BDT 4번 탭 '세트 결과' (`self.SetTab` line 17857)** — 단말 배터리 로그 + ECT 알고리즘 세트 내 동작 분석 — 가 ECT MR 검토의 운영 도구. 7번 트랙 (ECT/빅데이터) 의 BDT 측 entry point.
_Avoid_: ECT 알고리즘 자체 개발 측 (S.LSI 측 책임), 단순 결과 review (substance = envelope 정합 검증)

**A/M/Tablet 횡전개** (A/M/Tablet Cross-platform Deployment — A·M 의미 미정 Flagged #14):
S25+/S26 ECT 측 검증된 알고리즘을 A·M·Tablet form factor 로 horizontal 적용 + 파라미터 재추출 + 세트 검증. **MBO 일반·도전 양쪽 등장** — 일반 = 1차 파라미터 추출, 도전 = 추출 후 세트 검증/배포까지 (해석 미확정).
_Avoid_: 단일 form factor 파라미터 transfer (셀 물성 + 사용 패턴 다름), 검증 단계 누락 (추출만 하고 세트 검증 미실시)

### 프로파일 분석 architecture vocabulary (C3 deepening, 2026-05-02 진행 중)

**view_mode** (Profile View Mode):
'사이클데이터' 탭의 프로파일 분석에서 figure 분할 정책. 3종 — **전체 통합** (`AllProfile`, fig 1, 모든 데이터 누적) / **사이클 통합** (`CycProfile`, folder×channel 별 fig, default) / **셀별 통합** (`CellProfile`, folder×cycle 별 fig). UI 라디오 [`:12225-30`](DataTool_dev_code/DataTool_optRCD_proto_.py:12225).
_Avoid_: 한 view_mode 가 다른 view_mode 의 fig 단위 흡수 시도

**legacy_mode** (Profile Legacy Mode):
프로파일 분석의 데이터 추출 + plot 정책. 5종 — `step` / `rate` / `chg` (충전) / `dchg` (방전, default) / `continue`. 각 legacy_mode 별 `plot_one_fn` callback 정의.
_Avoid_: legacy_mode 추가 시 view_mode dispatch 중복 작성

**Profile dispatch — two-axis 분리** (C3 hybrid frame, 2026-05-02):
- **view_mode (3)** = module **internal `_RenderPolicy` table** — fig 분할 / 누적 / finalize 정책
- **legacy_mode (5)** = **caller 측 `plot_one_fn` callback** (PlotOneFn Protocol) — 데이터 추출 + plot
- **두 축 직교** — 새 view_mode 추가 = table 1 row, 새 legacy_mode 추가 = callback 1 추가. 책임 분리 명료.
- **15 cell single dispatch 거부** — boilerplate + 책임 응집 X. two-axis 가 박사급 peer 가독성 ★.
- 단일 entry: `render_profile(req: ProfileRenderRequest) -> RenderResult` (ADR-0009 정합).
- **위치 = 35K monolith 안 첫 step → 안정화 후 별도 파일 분리 점진** (Rule of Three).
_Avoid_: 15-cell single dispatch table, if/elif cascade, view × legacy 응집 시도

---

## Relationships

- **선행PF** 데이터 → **'승인 수명 예측' 탭** → **PRA** 게이트 통과 판정 (23·45°C anchor)
- **선행PF** 데이터 + 환경 sweep (V상하한·T) → **'실수명 예측' 탭** → **실사용 수명** RUL 예측
- **배터리 업체 EU 시험 데이터** + 내부 보완 → **'EU 수명 예측' 탭** → EU 시장 출시 충족
- **PRA 시험 (1.0C·0.5C 스텝)** ↔ **EU 시험 (0.5C 단일)** : **방전 부하 차이가 cycle fade 정량 차이의 main 원인** — 같은 셀에 두 트랙 결과 다른 이유
- **3 empirical 트랙** (EU / 승인 / 실사용) **의 시험 매트릭스 분리** — 같은 셀이라도 데이터 조합 다름 → 트랙별 envelope 별도 운영
- **만방 V 상향 (제품 정책)** ↔ **'실수명 예측' 탭 모델링 input** : 본인 1주 작업 측 추가 기능. 메커니즘 frame 은 선행Lab 소재 전공자 파트 결정, 본인은 모델링 layer.
- **만방 V 상향 → SOC 하한 ↑ → Si cyclic stress range ↓ → SEI/LAM 보호 → 수명 ↑** 동시에 **사용 capacity ↓ trade-off** : Pareto front 보고 frame 표준
- **선행Lab 4 파트 협업 frame**: 본인 (성능·수명 해석) ← 소재 전공자 파트 (Si 보호 메커니즘) · BMS 파트 (ECT/SBP 알고리즘) · 열 시뮬레이션 파트
- **인계 cross-check items (전임자=랩장님)**: DOD 정의 운영 · '실수명 예측' fit form 구조 · 9 탭 entry point 흐름 (Flagged #9)
- **보고 source ↔ 출력 매핑** (ADR-0006): wiki/.md (bullet) + docs/*.png (이미지) + docs/*.xlsx (표) → 본인 수동 조립 → docs/*.pptx
- **BDT 시각화 출력** ↔ **docs/*.png** (Pareto front · envelope · 사이클 plot 자동 저장 후보 follow-up)
- **MX form factor** (bar/foldable/wearable/tablet/notepc) 마다 **사용자 시나리오** 다름 → 같은 셀의 **실사용 수명** 도 form factor 별로 결과 갈라짐
- **승인 수명** (관리체계 ↑·물리 깊이 ↓) ↔ **실사용 수명** (관리체계 ↓·물리 깊이 ↑) — 한 셀에 대해 두 답이 동시 존재
- **SiC sensitivity sweep** (5/10/15%) → P2D 시뮬 monotonic curve → **양산 점** (Gen4+ 5%, Gen6+ 15%, Gen6++ 25%) overlay → 박사급 peer 보고용 표준 frame
- **측정 envelope 의 boundary = Empirical ↔ EC model 자연 division line**. 두 도구는 alternative 가 아니라 **complement**. 한 셀의 실사용 수명 frame = 두 도구의 union.
- **EC model 의 cross-validation anchor = empirical 측정 grid** — envelope 안에서 두 도구 결과 일치해야 envelope 외 extrapolation 신뢰 가능.
- **측정 envelope 의 dynamic 갱신** — 사이클·calendar 축 boundary 가 시험 진행 따라 확장. 보고 시점 별 envelope 명시 필수 (예: "2026-05-02 기준, Gen6+ 의 envelope 는 23°C × 4.4V × 800사이클까지").
- **유사 셀 transfer → empirical 결과 stratify**: 직접 측정 vs transfer 보강 영역의 신뢰도 다름 → 보고 시 영역 별 색상/주석 분리 권장.
- **user 시나리오 layer**: trace 부재 → (g) Path integration 불가 → **(f)' 히트맵 weight × 2-bin cohort × flagship-only** 가 본인 frame. ADR-0001 위에 얹는 layer.
- **FG → 복합 저장 히트맵 → empirical 보간 결과 weight** : 빅데이터의 적용 경로.
- **ECT 8월 이관 → 본인 직무3 내재화 검토** : 직무3 substance 의 anchor 트리거 (BMS 알고리즘 전문 인력 협업).
- **만충 두께 측정** (시험소 + 업체 cross-check) → BDT 사이클 탭 입력 → **PRA 출시 승인 조건의 일부**
- **SBP Swelling% ≠ 만충 두께 측정** : 두 source 별개 — SBP 는 단말 online (저항 기반), 만충 두께는 오프라인 ground truth. SBP 검증은 알고리즘 인력 측 책임 (BDT 측 X).
- **저항 증가율 ↔ 스웰링 상관** (가정) → 4번 empirical fade 의 secondary feature 후보. 박사급 peer challenge 시 메커니즘 정합성 별도 입증 필요.
- **P2D 의 스웰링 한계 — 영역별 정밀화** (학계 합의):
  - 활물질 단위 stress = 표준 (가능)
  - Cell-level pouch swelling = 최신 활발 (Mohtat 2021)
  - Hard/gas 분리 = 한계
  → 사용자 frame "어렵다" 는 hard/gas 분리 측 + cell-level 결합 정량 측만. **활물질 stress + cell-level 측정-모델 결합** 은 가능 영역.
- **House Code 의 mechanical domain 미발견 자산 가능성** — D1 작업 시 raw/House Code/MSMD/, GH-MSMD/ 의 mechanical 모듈 cross-check. 확인 시 ADR-0002 후보.
- **empirical 스웰링 추정 신뢰도 한계** 명시 인정 (frame epistemic 정합).

---

## Example dialogue

> **본인 (modeler):** "Gen6+ 셀의 **PRA** 통과를 위해 **승인 수명** 을 23/45°C 두 점에서 예측해야 합니다."
> **박사급 peer:** "그건 **선행PF** 시험 매트릭스에 의존하는데, full cell GITT 만 있는 상태에서 활물질 OCV/D 분리 추정은 어떻게 합니까?"
> **본인:** "현재 **승인 수명** 측은 empirical fit 으로 가고, P2D 기반 분리 추정은 **실사용 수명** 측의 V·T sweep 시뮬 단계에서 진입합니다."
> **박사급 peer:** "MX 의 어느 form factor 까지를 **실사용 수명** 의 사용자 시나리오 모집단에 두나요?"
> **본인:** "(...다음 grill 에서 해소...)"
>
> **박사급 peer:** "Gen6++ (SiC 25%) 셀의 P2D 시뮬 결과 있나요?"
> **본인:** "**SiC sensitivity sweep** 5/10/15% 의 monotonic curve 를 학습용으로 잡고, **Gen6++ (25%)** 는 그 curve 의 extrapolation 점으로 plot 합니다. extrapolation 정합성은 GITT 측정으로 별도 검증."
>
> **박사급 peer:** "Gen6+ 셀 25°C 실사용 수명 어떻게 예측?"
> **본인:** "23·35·45°C 측정 grid 있으니 25°C 는 **empirical interpolation** 입니다. envelope 안."
> **박사급 peer:** "측정 안 한 4.7V cutoff 는?"
> **본인:** "envelope 외 — empirical 권한 밖입니다. **P2D 시뮬 (EC model extrapolation)** 으로 V sweep 해서 예측. 파라미터 추정 UQ 같이 표시합니다."

---

## Flagged ambiguities

| # | 충돌 | 결정 (날짜) |
|---|------|-----------|
| ✅ 1 | **"실수명"** vs **"실사용 수명"** — 코드/UI = "실수명", 답변·메모리 = "실사용 수명" 혼용 | **canonical = "실사용 수명"** (2026-05-02). "실수명" 은 코드 식별자 only. |
| ✅ 2 | **SiC 함량 5/10/15%** (시뮬 sweep) vs **Gen6+ 15% / Gen6++ 25%** (양산 PF) | **두 축 분리 운영 (2026-05-02)**. sensitivity sweep = 5/10/15% 학습용 monotonic curve, 양산 점 = 5/15/25% overlay. |
| ✅ 3 | **'실사용 수명 예측' 의 정의** — stochastic profile vs parametric sweep vs hybrid | **(d) 두 도구 역할 분담 (2026-05-02)**. Empirical interpolation = envelope 안 (4번 70%), EC model extrapolation = envelope 외 (5번 30%). 영구 박제 = [[31_software_dev/adr/0001-lifetime-prediction-tool-split\|ADR-0001]] |
| ✅ 4 | **"실사용 수명" 의 form factor 모집단 + 빅데이터 출처** | **(2026-05-02)** flagship-only 단계적 (B) + FG 히트맵 source + 2-bin cohort (만충고온 상위 / 일반). trace 부재 → (g) 미도입, (f)' weight 채택. |
| ⏳ 5 | **유사 셀 transfer 의 정량화 frame** — 유사도 정의, transfer 신뢰도 metric, fit uncertainty propagation | 미해소 — 작업 중 발생 시 frame 정의 |
| ⏳ 6 | **House Code (MSMD/GH-MSMD) 의 mechanical 모듈 존재 여부** — D1 작업 시 cross-check | 미해소 — D1 ingest 시 즉시 확인 |
| ✅ 7 | **80% retention 시험 미진행 + fit extrapolation 의존** — ADR-0001 의 strict 정책과의 정합 | **(2026-05-02)** [[31_software_dev/adr/0003-functional-form-mediated-extrapolation\|ADR-0003]] 신규 — 학계 표준 functional form 위에서 form-mediated extrapolation 허용 (3 조건: form 학계 근거 + extrapolation 영역 + UQ). raw extrapolation 은 여전히 금지. |
| ✅ 8 | **EU 시험 매트릭스 정확도** + EU 수명 SW 운영자 정합 | **(2026-05-04 grill #2)** EU 수명 SW = 본인 MBO 측 운영 X (업체 시험 데이터 1순위) → 매트릭스 정확도 issue 는 업체 측 책임. 본인은 보조 검증만. |
| ⏳ 9 | **인계 cross-check items** — DOD 정의, '실수명 예측' fit form 구조, 9 탭 entry point 흐름 | 미해소 — 전임자(랩장님) 인계 면담 또는 코드 분석 + 질문 list |
| ⏳ 10 | **선행Lab 4번째 파트 정체** — 답에 등장한 "선행PF 배터리 소재 전공자 파트" = 4번째 파트인지 별개인지 | 미해소 — 추후 확인 |
| ⏳ 11 | **측정 Campaign — 직접 vs 발주 비율** + 소재 EC 물성 DB 형식 (parquet/wiki/PostgreSQL) | 미해소 — 6번 트랙 substance 정의 진행 중 (2026-05-04 grill) |
| ✅ 12 | **MBO ↔ 7트랙 매핑 + 시간 비중 재배분** (4: 70→50, 5: 30→20, 6 신규 10, 7 신규 20) | **(2026-05-04)** [[31_software_dev/adr/0010-mbo-track-mapping\|ADR-0010]] 채택 — 7트랙 + dual-credit + 외부 frame 정합 + AX 듀얼 운영 명문화. |
| ⏳ 13 | **ECT MR** 약어 정확 의미 (Master Release? Mass Reliability?) | 부분 해소 — BDT 4번 '세트결과' 탭 cross-link 확정 (2026-05-04 grill #3). MR 약어 자체는 미해소. |
| ⏳ 14 | **A/M/Tablet 횡전개** 의 A·M 의미 (Audio·Mobile? Anchor·Modular?) + 일반/도전 차별화 | 미해소 — 7번 트랙 정의 진행 중 |
| ✅ 15 | **MBO 2.1 AX "S레코드" 약어** | **(2026-05-04 grill #3)** "SW코드" 오타 — "개발자용 SW코드 리팩토링" 이 본의. AX = LLM 측 SW 코드 리팩토링. |
| ✅ 16 | **MBO 1.1.2 도전 dV/dQ vs 1.1.1 일반 dV/dQ 분리선** | **(2026-05-04 grill #3)** 일반 = fresh cell + Gr-only 음극 (양극·흑연 2-component separate). 도전 = Gr+SiC 혼합 음극 (SiC 5% Gen4+/Gen5+VB 부터 SiC 25% Gen6++ 까지) overlap deconvolution (Lain-Brandon 2019). |
| ✅ 17 | **MBO 1.1.1 일반 사용자 수명 vs 1.1.2 도전 방전 영향도 분리선** | **(2026-05-04 grill #3)** 일반 = baseline 인계 운영 + V·T sweep 단순 확장 (envelope 안 interpolation). 도전 = baseline 위에 Si-protection factor 추가 (만방 V 상향 + DOD + 방전 영향도). |
| ✅ 18 | **Ground rule "부서원 동료지원/협업 25% 이상" vs MBO 비중 15% 충돌** | **(2026-05-04 grill #4)** (d1) 결정 — Ground rule "25% 이상" 은 **최종 score 측** 의미. 비중 표 15% (TF/공통/SME/QTR) 는 minimum baseline, 3.1 의 "max 무제한" 활동 점수로 25% 이상 자연 도달. |
| ✅ 19 | **MBO 2.1 AX 3건 확정 + 사내·사외 듀얼 운영** | **(2026-05-04 grill #5)** 3건 = SW 코드 리팩토링 + 수명 결과 요약 + BDT SOP LLM 작성. 사외 = 외부 LLM (Claude 등), 사내 = **Gauss (사내 모델, 구축 예정)** — 사내 한정. |
| ✅ 20 | **외부 frame 정합** — 부서 KPI · 운영방향 · 팀 도전 Project ↔ MBO | **(2026-05-04 grill #6)** 부서 KPI 4 中 3 정합 (Form-Factor/Slim화 만 본인 X) · 협력사 협업 deepening = 6번 트랙 측정 발주·QA · **Simulation 고도화 TF main contributor = 본인 (5번 트랙 owner)**. |
| ✅ 21 | **5번 트랙 ~20% 비중 적정성** | **(2026-05-04 grill #7)** (c) Q-별 sequencing 채택. 비중 ~20% 유지, 도전 4건을 분기별 sprint 로 분산. TF main contributor 는 baseline 으로 진행. Q-별 분배는 grill #8 진행. |
| ✅ 22 | **MBO 점수 산정 — 건별 dual-credit (cross-category 5점/건)** | **(2026-05-04 grill #7)** 일반·도전 항목 겹쳐도 카테고리별 5점 별도 산정. max 무제한 카테고리 (1.2 / 2.1 / 2.2 / 3.1) 측 score stack 가능. 같은 deliverable 가 multiple 카테고리 score 받음. |
| ⏳ 23 | **5번 도전 4건 Q-별 sprint 분배 + 6번 measurement campaign 동기화** | **현재 fix 불필요** (사용자 결정, 2026-05-04 grill #8 종료). 후속 grill 또는 매주 금요일 노트 측 trace. |
| ⏳ 24 | **2.2 특허 5점 (1건) 분야 확정** | 미해소 — Gr+SiC 성능 / Gr+SiC dV/dQ / 만방 V Si-protection / ECT 알고리즘 후보. 후속 grill. |
| ⏳ 25 | **4.1 역량강화 10점 substance** — 외국어 등급 + 자격증 + StarWeek + 사외교육 plan | 미해소 — 후속 grill. |
| ⏳ 26 | **1.2.2 도전 신규 항목 substance** — 스웰링 plot (승인용) + 사이클 anomaly detection 운영 detail | 미해소 — 후속 grill. |

---

## 외부 참조 (도메인 deep-dive)

- [[21_electrochem/!용어]] — 사내 약어 (DV/PV/PR · PKA~MSA · FACA · DFMEA · Pack 종류)
- [[30_modeling/시뮬레이션_용어사전]] — 시뮬 16 코어 개념 (P2D · ECM · thermal · PINN · empirical fade · UQ)
- [[31_software_dev/260501 개발용어]] — 개발 측 stub (작성 중)
