# ADR-0010 — MBO Track Mapping (5트랙 → 7트랙 재구조 + dual-credit 점수 룰 + 외부 frame 정합)

- Status: accepted
- Date: 2026-05-04
- Deciders: 본인 (BDT owner) — Grill #1~8 (`/grill-with-docs` 세션 결과)

## Context

본인 = Samsung MX 선행배터리랩 「성능·수명 해석」 파트, 직무4 메인 + 직무3 일부 (BDT 인계). 2026 MBO 가 1Q 수시피드백 후 갱신되면서 다음 갱신·정합 issue 발생:

1. **인계 시점 5트랙 메모리 (BDT 1·2·3 enabler / empirical 4 70% / EC modeling 5 30%)** 가 MBO 항목과 매핑 안 됨:
   - "성능 모델링" 4세부 항목 (코인셀/삼전극 + dV/dQ + 온도별 + 물성 DB) 이 5번 (EC modeling) 안에 강제 흡수 불가
   - "ECT/빅데이터" 가 5트랙 어디에도 없음 (메모리 = 직무3 8월 이관 검토 단계로만 존재)
2. **부서 ground rule "부서원 동료지원/협업 25% 이상"** vs 본인 MBO 비중 15% 표면적 충돌
3. **MBO 일반·도전 항목 동일 deliverable 의 cross-category 점수** 산정 룰 미명시 — 산정 합의 필요
4. **EU 수명 SW (BDT 6번 탭)** 인계 받았으나 운영자 정의 모호 (배터리 업체 시험 데이터 1순위 input 정합)
5. **외부 frame 3 layer** (부서 KPI 4 항목 + 운영방향 4 항목 + 팀 도전 Project 3개) 와 본인 MBO 정합 trace 부재
6. **Simulation 고도화 TF (3년차)** 의 본인 role 미명시 — 5번 트랙 (전기화학 모델링) substance 와 정확 정합
7. **5번 트랙 ~20% 시간 비중** 적정성 — TF main + 1.1.2 도전 4건 (Gr+SiC 성능·dV/dQ·GITT D·급속 충전 risk) 동시 진행 시 산술 부족 위험
8. **사내 PC AI 도구 금지 정책** vs MBO 2.1 AX 15점 (≥3건) 운영 — 사내 모델 Gauss (구축 예정) 도입으로 듀얼 운영 가능

박사급 peer challenge substance 기준 ([`feedback_substance_audience.md`](.claude/projects/C--Users-Ryu-battery-python-BDT-dev/memory/feedback_substance_audience.md), 4종 set: 가정·UQ·검증·한계) 정합이 모든 결정의 anchor.

## Decision

### 1. 시간 운영 = 7 트랙 (5트랙 → 7트랙 재구조)

| # | 트랙 | 시간 | MBO 매핑 |
|---|------|-----|---------|
| 1 | BDT 자체 개선·고도화 (전임자 인계) | enabler | 1.2 혁신 (개발자용 SW) |
| 2 | 충방전기 현황 업데이트 | enabler | — |
| 3 | 데이터 전처리 고도화 | enabler | 1.2 혁신 (AI/빅데이터 협업 도구) |
| 4 | **Empirical 수명 모델링** | **~50%** | 1.1 수명 모델링 + 1.1.2 도전 (방전 영향도) |
| 5 | **EC 모델링 (성능)** + ★ Simulation 고도화 TF Main | **~20%** | 1.1 성능 (온도별·dV/dQ baseline) + 1.1.2 도전 (Gr+SiC 4건) |
| 6 | **측정 Campaign 운영** ★ 신규 | **~10%** | 1.1 성능 (코인셀/삼전극·소재 DB) |
| 7 | **ECT/빅데이터** ★ 신규 | **~20%** | 1.1 ECT (S25+/S26 MR + A/M/Tablet 횡전개) |

→ 1·2·3 = 4·5·6·7번 enabler. 시간 100% = 4(50%) + 5(20%) + 6(10%) + 7(20%).

### 2. MBO 점수 비중 (100점)

| 카테고리 | 비중 | max 무제한? |
|---|---|---|
| 1.1 Project 결과 | 35 | (35 안에서) |
| 1.2 Project 혁신 | 20 | ✅ |
| 2.1 AX 성과 | 15 | ✅ |
| 2.2 특허 출원 | 5 | ✅ |
| 3.1 TF·공통업무 | 15 | ✅ |
| 4.1 역량강화 | 10 | min 10 |

### 3. 점수 산정 룰 — cross-category dual-credit

같은 deliverable 가 multiple 카테고리 측 5점/건 별도 산정 (일반·도전 겹쳐도). max 무제한 카테고리 (1.2 / 2.1 / 2.2 / 3.1) 측 score stack 가능.

### 4. EU 수명 SW 운영자 = 본인 MBO 측 X

EU 수명 보증 1순위 input = 배터리 업체 시험 데이터 → 본인 MBO "수명 모델링" 항목에서 EU 수명 SW 빠짐. BDT 6번 탭 (`self.tab_4`) 인계 받았으나 운영 deliverable 아님 — 보조 검증 측. **본인 인계 자산 운영 = 7번(승인) + 8번(실수명) 탭만**.

### 5. Ground rule "동료지원/협업 25% 이상" = 최종 score 측 의미

비중 표 15% (3.1) 는 minimum baseline. max 무제한 활동 점수 (TF 10 + 공통 5 + SME 5+ + Tech meeting 2점/회 + ...) 로 25% 이상 자연 도달.

### 6. Simulation 고도화 TF (3년차) Main Contributor = 본인

5번 트랙 (전기화학 모델링) owner 로서 TF 핵심 기여자. TF 활동은 3.1 (10점/건) + 1.1 성능 모델링 deliverable 측 dual-credit. 운영방향 "재료비 혁신·원가 절감" 의 본인 기여 = TF 의 신규 재료 특성 제안 측 (간접).

### 7. AX 운영 = 사외 외부 LLM + 사내 Gauss 듀얼

- 사외 PC = 외부 LLM (Claude 등). 사내 데이터 접근 X. 산출물 = 비-AI Python 모듈 / wiki .md / fit form / SOP.
- 사내 PC = **Gauss** (사내 모델, 구축 예정). 사내 데이터 접근 가능. 사내 한정.
- AX 3건 확정: (i) 개발자용 SW 코드 리팩토링 (ii) 수명 결과 요약 텍스트 (iii) BDT SOP LLM 작성.

### 8. 5번 도전 4건 = Q-별 sprint sequencing

5번 ~20% 비중 유지. 도전 4건 (Gr+SiC 성능 / Gr+SiC dV/dQ overlap / GITT D 추출 / 급속 충전 risk) 을 분기별 sprint 로 분산. TF main 은 baseline + sprint 결합. 분배 자체는 매주 금요일 B 노트 trace 측 evolve.

### 9. 측정 Campaign Owner — "본인은 시험 직접 X" 단정 폐기

본인 = **Campaign Owner** — (i) 코인셀/삼전극 단위 일부 직접 측정 + (ii) 리소스 부족 시 업체 발주 + (iii) 어느 셀·어느 조건 측정할지 결정·발주·QA + (iv) 받은 데이터 분석. 운영방향 "협력사들과 한단계 깊은 수준의 협업" 의 본인 측 trace.

## Consequences

### Positive

- **MBO 항목 100% 매핑** — 7트랙 frame 으로 산술 정합 (4·5·6·7번 시간 합 100%, 모든 1.1 항목이 트랙 측 home).
- **dual-credit 룰** 로 score 효율 ↑ — 같은 deliverable 가 multiple 카테고리 stack (예: BDT SOP = 1.2.1 + 2.1 = 10점, Simulation TF main = 3.1 + 1.1 = 15점+).
- **외부 frame 정합 trace** 명문화 — 부서 KPI 4 中 3 정합, 운영방향 협력사 협업 = 6번 측, 팀 도전 Simulation 고도화 = main contributor 5번 측.
- **Ground rule "25% 이상"** (d1) 해석으로 비중 재조정 회피 — 직무4 메인 deliverable 측 가중 유지.
- **AX 운영 정책** (사외 외부 + 사내 Gauss 듀얼) 명문화 — 사내 PC AI 금지 정책 정합.
- **Q-별 sequencing** 으로 박사급 peer challenge substance 4종 set 정합 시간 확보.
- **EU 수명 SW 본인 X** 결정으로 deliverable oversell 회피, 인계 자산 운영 측 trace 명료화.
- **Campaign Owner** 정정으로 운영방향 "협력사 깊은 협업" 의 본인 측 substance 명료화.

### Negative

- **5번 트랙 ~20% 비중 적정성** 은 Q-별 sequencing 의존. Sprint 실패 시 시간 측 부족 reissue 위험 (Flagged #21 → grill #7 (c) 채택, 본질 미해소).
- **EU 수명 SW 본인 X** 결정으로 BDT 6번 탭은 인계 받았으나 운영 deliverable 측 trace 빠짐 — backup/응급 운영 불가 위험.
- **6번 트랙 직접 vs 발주 비율 + DB 형식** (parquet/wiki/PostgreSQL) 미해소 (Flagged #11) — substance evolve 단계.
- **Gauss 도입 시점 미확정** — AX 사내 측 deliverable Gauss 의존, 도입 지연 시 사외 LLM 산출물 측 한계.
- **Q-별 sprint 분배** 미확정 (Flagged #23) — sequencing 자체 evolve 의존.
- **5번 도전 4건 中 일부 deferral 가능성** — Q4 마감 압박 시 1건 (예: 급속 충전 risk SW) 차년도 이월 위험.

### Neutral / Follow-up

- **Q-별 sprint 분배 detail** (Flagged #23) — 매주 금요일 B 노트 trace 측 evolve.
- **2.2 특허 1건 분야 확정** (Flagged #24) — Q2~Q3 진척 후 (Gr+SiC dV/dQ / Si-protection / Gr+SiC 성능 / ECT 알고리즘 후보).
- **4.1 역량강화 10점 substance** (Flagged #25) — 외국어 등급 + 자격증 + StarWeek 후속 grill.
- **1.2.2 도전 substance** (Flagged #26) — 스웰링 plot · 사이클 anomaly detection 진입 시.
- **6번 트랙 측정 campaign 정량 metric** — 발주 빈도 / 직접 측정 비율 / QA 측정 reject rate 등 evolve.
- **Gauss 도입 후 AX 운영 정책 갱신** — 사내 측 deliverable detail 추가.
- **운영방향 "재료비 혁신·원가 절감"** 의 본인 직접 기여 deliverable 정량화 (현재 = TF 신규 재료 제안 측 간접).
- **MBO 1.2.1 일반 "사용성 개선"** 가 ADR-0005 (dual primary user) 의 그룹원 default 측 substance 강화 — 별도 ADR 후보.

## Alternatives considered

- **(A) 5트랙 유지 + MBO 항목 강제 흡수**
  - 거부: "성능 모델링" 4세부 + "ECT/빅데이터" 가 5트랙 안에 산술 매핑 불가. ECT/측정 campaign substance 사라짐.

- **(B) "본인은 시험 직접 X" 단정 유지 (Campaign Owner 정정 X)**
  - 거부: MBO "코인셀/삼전극 제작, 측정 Process 확립" 항목 trace 부재. 운영방향 "협력사 깊은 협업" 의 본인 측 substance 부재.

- **(C) 동료지원/협업 비중 표 측 25% 까지 상향**
  - 거부: 1.1 (35) + 1.2 (20) 측 본인 main deliverable 위축, 직무4 메인 정합 X. (d1) 해석 (score 측 25%) 으로 비중 표 15% 유지.

- **(D) EU 수명 SW 본인 운영 (인계 자산 그대로 운영)**
  - 거부: 배터리 업체 시험 데이터 1순위 input 정합 X. 본인 deliverable oversell 위험. BDT 6번 탭 = 보조 검증 측 한정.

- **(E) Simulation 고도화 TF 비참여 또는 단순 협업**
  - 거부: 5번 트랙 owner 측면에서 main contributor 가 자연. TF substance = 5번 트랙 substance 동일 (전기화학 모델링).

- **(F) 사내 PC 외부 LLM 사용 (Claude/Copilot 직접 사내 운영)**
  - 거부: 보안·DRM 정책 위반. Gauss 사내 측 듀얼 운영 채택.

- **(G) 5번 도전 4건 동시 진행 (sequencing X)**
  - 거부: 시간·substance 부족. 박사급 peer challenge 4종 set 정합 시간 확보 X. Q-별 sprint sequencing 채택.

- **(H) 5번 비중 ~25~30% 상향 (4번 ~50→~40 하향)**
  - 거부: 4번 (수명) 측 인계 자산 운영 위축 위험 — 승인 수명 (PRA 게이트) + 실사용 수명 baseline 운영의 deliverable size 축소 trade-off 받지 않기로 결정 (grill #7 (c) 단독 채택).

- **(I) 5번 도전 中 그룹원/협업 측 task share**
  - 거부: ADR-0005 그룹원 default 측 정합 X — 그룹원 = BDT user 측, EC 모델링 substance 부족.

## References

- [`wiki/CONTEXT.md`](../../CONTEXT.md) — Domain 글로서리 (canonical 어휘 + Flagged ambiguities #11~26)
- [`project_bdt_work_tracks.md`](../../../../.claude/projects/C--Users-Ryu-battery-python-BDT-dev/memory/project_bdt_work_tracks.md) — 7트랙 + 비중 표
- [`feedback_substance_audience.md`](../../../../.claude/projects/C--Users-Ryu-battery-python-BDT-dev/memory/feedback_substance_audience.md) — 박사급 peer challenge substance 4종 set
- [`project_office_pc_no_ai.md`](../../../../.claude/projects/C--Users-Ryu-battery-python-BDT-dev/memory/project_office_pc_no_ai.md) — 사외 외부 LLM + 사내 Gauss 듀얼
- [ADR-0001](0001-lifetime-prediction-tool-split.md) — empirical interpolation vs EC model extrapolation 분리
- [ADR-0004](0004-cell-design-to-p2d-parameter-mapping.md) — 4-category Direct/Derived/Fit-driven/문헌 (소재 EC 물성 DB 의 stratify frame)
- [ADR-0005](0005-bdt-dual-primary-user.md) — BDT primary user 양립 (그룹원 80명 + 본인) — MBO 1.2.1 사용성 개선 + 2.1 BDT SOP 정합
- [ADR-0006](0006-reporting-format-core-and-appendix.md) — 보고 format (AX 수명 결과 요약 텍스트 정합)
- [ADR-0008](0008-bdt-test-and-study-automation.md) + [ADR-0009](0009-expert-level-code-and-study.md) — 테스트·스터디 frame (AX SW 코드 리팩토링 정합)
