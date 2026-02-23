# 전기화학 시뮬레이션 기능 업무 마일스톤 계획

> 작성일: 2026-02-23  
> 목적: 셀 개발 지원 및 설계 경쟁력 강화

---

## 전체 로드맵 개요

```
Q1 2025          Q2 2025          Q3 2025          Q4 2025          Q1 2026
─────────────────────────────────────────────────────────────────────────────
[===== 1. 소재 물성 DB화 =====]
         [======== 2. dV/dQ 양음극 분리 ========]
                  [========== 3. 성능 Simulation ==========]
                           [============ 4. 수명 예측 ============]
─────────────────────────────────────────────────────────────────────────────
```

---

## 1. 소재 전기화학 물성 DB화

### 필요한 것들

| 카테고리 | 상세 내용 |
|---------|----------|
| **하드웨어/장비** | 코인셀 조립 장비(글로브박스, 크림핑기), 삼전극 셀 전용 하우징(EL-Cell 등), 충방전기(다채널), 항온조 |
| **소재/시료** | 양극 활물질(NCM, LFP 등 시리즈별), 음극 활물질(흑연, SiOx, Si-C composite), 레퍼런스 전극(Li metal, Li-In 등), 전해액(표준/프로젝트별) |
| **측정 프로토콜** | OCV-SOC 커브 측정 조건 표준화, GITT/EIS 측정 프로토콜, 온도별 측정 프로토콜 (예: -10, 0, 25, 45°C) |
| **데이터 인프라** | DB 스키마 설계 (소재 ID → 물성값 매핑), 데이터 입력/관리 UI (기존 Tool 확장), 버전 관리 및 이력 추적 체계 |
| **조직/협업** | 소재팀/분석팀과 시료 확보 채널, 셀 제작 담당자 지정, 데이터 공유 플랫폼 합의 |

### 마일스톤

```
M1.1 [Week 1-2]  요구 물성 항목 정의 및 DB 스키마 설계
     ├── 시뮬레이션에 필요한 물성 파라미터 리스트업
     │   (OCV, diffusivity, exchange current density, entropic coefficient 등)
     ├── 소재 분류 체계 확립 (양극/음극 × 조성 × 배치)
     └── DB 테이블 구조 설계 및 개발팀 리뷰

M1.2 [Week 3-6]  삼전극/Half 코인셀 제작·측정 프로세스 확립
     ├── 삼전극 셀 하우징 선정 및 조달
     ├── 전극 제작 표준 (로딩량, 프레스 밀도, 전극 크기)
     ├── 측정 프로토콜 문서화
     │   ├── Low-rate OCV 커브 (C/20 이하)
     │   ├── GITT (diffusivity 추출)
     │   ├── EIS (impedance 파라미터)
     │   └── Entropic coefficient (OCV vs T)
     ├── 재현성 검증 (동일 소재 3셀 이상)
     └── SOP 문서 발행

M1.3 [Week 7-10] Pilot 소재 물성 측정 및 DB 등록
     ├── 주력 양극 2종 (예: NCM811, NCM622) 물성 측정 완료
     ├── 주력 음극 2종 (예: 흑연, SiOx blend) 물성 측정 완료
     ├── DB 입력 및 검증 (시뮬레이션 입력 → 출력 교차 검증)
     └── 코인셀/삼전극 결과 비교 리포트

M1.4 [Week 11-14] DB 시스템 고도화 및 공유 체계 구축
     ├── DB 검색/조회 UI 개발 (기존 Tool 내 통합)
     ├── 소재팀 데이터 공유 프로세스 확립
     ├── 신규 소재 등록 워크플로우 정립
     └── 사용자 매뉴얼 배포 및 교육
```

### 핵심 산출물

- [ ] 소재 물성 DB (v1.0) — 양극 2종, 음극 2종 이상
- [ ] 삼전극/코인셀 제작·측정 SOP 문서
- [ ] DB 관리 UI 및 사용자 가이드

---

## 2. dV/dQ 양음극 분리 (열화 분리용)

### 필요한 것들

| 카테고리 | 상세 내용 |
|---------|----------|
| **입력 데이터** | 풀셀 충방전 데이터 (사이클별), 단극 OCV 커브 (DB에서 획득 → 1번 과제 연계), 초기 양/음극 용량 및 N/P ratio |
| **알고리즘** | dV/dQ (또는 dQ/dV) 피팅 알고리즘, 양/음극 슬라이딩·스케일링 최적화 (LLI, LAM_PE, LAM_NE 분리), 미분 커브 smoothing/filtering 로직 |
| **검증 데이터** | 삼전극 셀 장기 사이클 데이터 (실측 열화 모드 확인용), Post-mortem 분석 결과 (열화 모드 교차 검증) |
| **음극 특이사항** | 흑연 phase별 OCV 모델링 (stage 1~4 plateau), SiOx/Si 혼합 음극 OCV 모델 (흑연 + Si 가중합), Si 비가역 용량 및 팽창/수축 비대칭 처리 |
| **SW 개발** | 기존 Tool 내 dV/dQ 분석 모듈 통합, 시각화 (피팅 결과 overlay, 열화 mode 트렌드) |

### 마일스톤

```
M2.1 [Week 1-3]  dV/dQ 분리 알고리즘 설계 및 문헌 조사
     ├── Bloom et al., Dubarry et al. 방법론 비교 분석
     ├── 양극/음극 OCV 모델 선정
     │   ├── 양극: 다항식 or Redlich-Kister or 실측 기반
     │   └── 음극: 흑연(stage 모델) + Si(Polynomial/실측)
     ├── 피팅 파라미터 정의 (x_offset, y_scale per electrode)
     └── 알고리즘 설계 문서 작성

M2.2 [Week 4-7]  흑연/실리콘 음극 dV/dQ 분리 구현
     ├── 흑연 단독 음극 dV/dQ 모델 구현 및 검증
     ├── Si 단독(또는 SiOx) dV/dQ 모델 구현
     ├── Blended 음극(흑연+Si) composite OCV 모델 구현
     │   └── 용량 가중 합산 모델 + Si 비율 파라미터
     ├── 풀셀 = f(양극, 음극) 합성 및 실측 비교
     └── 최적화 알고리즘 구현 (scipy.optimize or custom)

M2.3 [Week 8-10] 열화 모드 분리 기능 구현
     ├── LLI (Loss of Lithium Inventory) 추출
     ├── LAM_PE / LAM_NE (Loss of Active Material) 추출
     ├── 사이클별 열화 파라미터 트렌드 자동 추출
     ├── 삼전극 실측 데이터와 교차 검증
     └── 결과 시각화 (dV/dQ overlay, 열화 mode 파이차트/트렌드)

M2.4 [Week 11-13] Tool 통합 및 검증
     ├── 기존 BatteryDataTool에 dV/dQ 분석 탭 추가
     ├── 다양한 셀 케이스 검증 (고온 수명, 상온 수명, OCV storage)
     ├── 사용성 테스트 및 피드백 반영
     └── 기술 문서 및 활용 가이드 작성
```

### 핵심 산출물

- [ ] dV/dQ 양음극 분리 알고리즘 모듈
- [ ] 흑연+Si blended 음극 OCV 모델
- [ ] 열화 모드 자동 분리 리포트 기능
- [ ] 검증 리포트 (삼전극 실측 vs 분리 결과)

---

## 3. 성능 Simulation

### 필요한 것들

| 카테고리 | 상세 내용 |
|---------|----------|
| **모델 프레임워크** | P2D (Pseudo-2D) 또는 SPM (Single Particle Model) 기반 전기화학 모델, 온도 의존성 파라미터 모델 (Arrhenius), 열 모델 (lumped thermal or 1D) |
| **입력 파라미터** | 온도별 물성 (1번 DB 연계): D_s(T), k_0(T), κ(T), OCV(SOC,T), 전극 설계 스펙: 두께, 공극률, 입자 크기, 면적, 전해액 물성: 이온전도도, 확산계수, 전이계수 |
| **충전 프로파일** | 스텝충전 프로토콜 정의 (CC-CV, 다단 CC, 펄스 등), 급속충전 시나리오 (xEV 스펙 기반) |
| **검증 데이터** | 온도별 실측 충방전 커브, 삼전극 실측 음극 전위 데이터 |
| **SW 개발** | 시뮬레이터 엔진 (Python/Julia), 충전 프로파일 스케줄러, 음극 전위 모니터링 및 리튬 석출 판정 로직 |

### 마일스톤

```
M3.1 [Week 1-4]  전기화학 모델 구축 및 기본 검증
     ├── 모델 선정 (SPMe or P2D) 및 구현
     │   ├── PyBaMM 활용 or 자체 구현 검토
     │   └── 기존 proto 코드 기반 확장
     ├── 상온(25°C) 기준 모델 파라미터 캘리브레이션
     ├── C-rate별 방전 커브 실측 대비 검증 (0.2C ~ 3C)
     └── 모델 정확도 평가 (RMSE, MAE 기준)

M3.2 [Week 5-8]  온도별 충방전 성능 예측
     ├── Arrhenius 온도 의존 모델 구현
     │   ├── D_s(T) = D_s,ref × exp(-Ea_D/R × (1/T - 1/T_ref))
     │   ├── k_0(T) = k_0,ref × exp(-Ea_k/R × (1/T - 1/T_ref))
     │   └── 전해액 전도도 σ(T), D_e(T)
     ├── 저온(-10, 0°C) / 고온(45°C) 성능 예측
     ├── 실측 데이터 대비 검증
     ├── 온도별 용량 유지율 예측 기능 구현
     └── 열 모델 연계 (발열 → 온도 상승 → 물성 변화 피드백)

M3.3 [Week 9-13] 급속 충전 Risk 검토 기능
     ├── 스텝 충전 프로토콜 입력 인터페이스
     │   ├── Step별 C-rate, SOC 구간, 컷오프 설정
     │   └── 복수 충전 조건 비교 기능
     ├── 풀셀 전압/전류/온도 예측
     ├── 음극 전위 예측 (vs Li/Li+)
     │   ├── 음극 과전위 = η_NE = φ_s - φ_e - U_NE(SOC)
     │   └── Li plating onset 판정 (η_NE < 0 V vs Li/Li+)
     ├── Risk 지표 정량화
     │   ├── 음극 전위 최저값 (mV)
     │   ├── 음극 전위 < 0V 누적 시간
     │   └── 충전 시간 vs Risk trade-off 맵
     ├── 다조건 비교 리포트 자동 생성
     └── 실측 삼전극 데이터 vs 시뮬 비교 검증

M3.4 [Week 14-16] Tool 통합 및 사용성 완성
     ├── 시뮬레이션 모듈 UI 통합 (파라미터 입력 → 결과 시각화)
     ├── 1번 DB와 자동 연동 (소재 선택 → 파라미터 자동 로딩)
     ├── 결과 엑셀/리포트 출력 기능
     └── 교육 및 배포
```

### 핵심 산출물

- [ ] 전기화학 시뮬레이션 엔진 (온도 의존)
- [ ] 급속충전 음극 전위 예측 및 Li plating Risk 평가 모듈
- [ ] 충전 프로토콜 최적화 가이드라인 도출 프로세스
- [ ] 검증 리포트 (온도별 성능, 급속충전 음극 전위)

---

## 4. 승인용/실사용 수명 예측 (Empirical 기반)

### 필요한 것들

| 카테고리 | 상세 내용 |
|---------|----------|
| **데이터** | 다조건 수명 시험 데이터 (온도 × SOC 범위 × C-rate × Calendar/Cycle), 충분한 셀 수 및 시험 기간 (최소 수백 사이클 또는 수개월 저장), 승인 시험 프로토콜 정의 (고객사별 스펙) |
| **모델** | Semi-empirical 용량 열화 모델, Calendar aging: Q_loss = A × exp(-Ea/RT) × t^n, Cycle aging: Q_loss = B × exp(-Ea/RT) × (Ah-throughput)^m, 또는 Power-law / Arrhenius 하이브리드, Calendar + Cycle 열화 중첩 모델 |
| **피팅/통계** | 비선형 회귀 (least squares), Activation energy 추출, 신뢰구간 / 예측구간 산출, Knee-point 예측 모델 (선택) |
| **시나리오 입력** | 사용 프로파일 정의 (연간 주행거리, 충전 패턴, 기후 조건), 승인 시험 조건 매핑, 실 사용 시나리오 변환 로직 |

### 마일스톤

```
M4.1 [Week 1-3]  수명 데이터 수집 및 전처리 체계 구축
     ├── 기존 수명 시험 데이터 수집 및 정리
     │   ├── 데이터 포맷 표준화 (사이클#, 용량, CE, 저항 등)
     │   ├── 시험 조건 메타데이터 정리
     │   └── 이상 데이터 필터링
     ├── 승인 시험 프로토콜별 분류
     └── 데이터 충분성 평가 (어떤 조건 영역이 부족한지)

M4.2 [Week 4-7]  Empirical 열화 모델 구축
     ├── Calendar aging 모델
     │   ├── 온도 × SOC 매트릭스 데이터 피팅
     │   ├── Ea (activation energy) 추출
     │   ├── 시간 지수 n 결정 (√t or t^0.5~0.75)
     │   └── 모델 검증 (hold-out set)
     ├── Cycle aging 모델
     │   ├── C-rate × 온도 × DOD 데이터 피팅
     │   ├── Ah-throughput 기반 모델
     │   └── 모델 검증
     ├── Calendar + Cycle 복합 모델
     │   └── 독립 합산 vs 결합 모델 비교
     └── 모델 성능 평가 (MAE, 외삽 정확도)

M4.3 [Week 8-11] 수명 예측 시뮬레이터 개발
     ├── 승인 시험 수명 예측
     │   ├── 시험 조건 입력 → 열화 커브 예측
     │   ├── EOL (End of Life) 도달 시점 예측
     │   └── 신뢰구간 표시
     ├── 실사용 수명 예측
     │   ├── 사용 시나리오 정의 인터페이스
     │   │   ├── 일일 주행 패턴 (Cycle aging 인자)
     │   │   ├── 주차/저장 시간 (Calendar aging 인자)
     │   │   └── 지역별 온도 프로파일
     │   ├── 시나리오 → 열화 인자 변환 엔진
     │   └── 연간/월간 용량 열화 예측
     ├── 다시나리오 비교 기능
     └── 결과 리포트 자동 생성

M4.4 [Week 12-14] 검증 및 Tool 통합
     ├── 실제 반출/양산 셀 수명 데이터 교차 검증
     ├── 승인 시험 결과 사후 비교 (예측 vs 실측)
     ├── 기존 Tool 통합 및 UI 완성
     ├── 피드백 반영 및 모델 업데이트 프로세스 정립
     └── 사용자 교육 및 문서화
```

### 핵심 산출물

- [ ] Empirical 수명 예측 모델 (Calendar + Cycle)
- [ ] 승인 시험 수명 예측 리포트 생성 기능
- [ ] 실사용 시나리오 기반 수명 예측 시뮬레이터
- [ ] 모델 파라미터 라이브러리 (셀 타입별)

---

## 과제 간 의존성 및 시너지

```
┌──────────────────┐
│  1. 소재 물성 DB  │
└────────┬─────────┘
         │ OCV 커브, 물성 파라미터 제공
         ├──────────────────────┐
         ▼                      ▼
┌──────────────────┐   ┌──────────────────┐
│ 2. dV/dQ 분리    │   │ 3. 성능 Simulation│
│  (열화 분석)     │   │  (설계 최적화)    │
└────────┬─────────┘   └────────┬─────────┘
         │ 열화 모드 정보         │ 열화 메커니즘 이해
         ▼                      ▼
┌────────────────────────────────────────┐
│        4. 수명 예측 (Empirical)        │
│   물리 기반 insight로 모델 개선 가능     │
└────────────────────────────────────────┘
```

---

## 종합 일정표 (주 단위)

| 주차 | 1. 소재 DB | 2. dV/dQ | 3. 성능 Sim | 4. 수명 예측 |
|------|-----------|----------|------------|-------------|
| W1-2 | 스키마 설계 | | | |
| W3-6 | 프로세스 확립 | | | |
| W7-10 | Pilot 측정/등록 | 알고리즘 설계 | | |
| W11-14 | DB 고도화 | 음극 분리 구현 | | |
| W15-17 | (유지보수) | 열화 분리 구현 | 모델 구축 | |
| W18-20 | 신규소재 추가 | Tool 통합 | 온도별 성능 | |
| W21-24 | | (유지보수) | 급속충전 Risk | 데이터 수집 |
| W25-28 | | | Tool 통합 | 모델 구축 |
| W29-32 | | | (유지보수) | 시뮬레이터 개발 |
| W33-36 | | | | 검증/통합 |

---

## 리스크 및 대응 방안

| 리스크 | 영향도 | 대응 방안 |
|--------|--------|----------|
| 삼전극 셀 재현성 부족 | 상 | SOP 강화, 셀 제작 트레이닝, 최소 3셀 반복 |
| 소재 물성 데이터 부족 | 상 | 문헌값 보완, 우선순위 소재 선정 후 집중 측정 |
| Si 음극 dV/dQ 모델링 난이도 | 중 | 단계적 접근 (흑연 먼저 → Si blend 순차 확장) |
| 수명 데이터 다양성 부족 | 중 | 기존 데이터 최대 활용, 가속 시험 설계 제안 |
| 시뮬레이션 모델 정확도 한계 | 중 | 캘리브레이션 프로세스 정립, 불확도 정량화 |
| Tool 사용성/채택률 | 하 | 사용자 참여 개발, 정기 교육, Success case 공유 |

---

> 총 기간: **약 9개월 (36주)** 기준  
> 과제 1(소재 물성 DB)이 선행되어야 나머지 과제의 입력 데이터가 확보됨  
> 병렬 진행 가능 구간을 최대한 중첩하여 전체 일정 단축

---
---

# PyBaMM 전기화학 시뮬레이션 — 초안 구현 내역

> 구현 완료일: 2026-02-23  
> 대상 파일: `BatteryDataTool_optRCD_proto_.py`  
> 의존 라이브러리: PyBaMM v25.12.2, PyQt6, matplotlib

---

## 1. 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────┐
│  BatteryDataTool (PyQt6 QMainWindow)                        │
│                                                             │
│  ┌──── 전기화학 시뮬레이션 탭 (PyBaMMTab) ─────────────────┐  │
│  │                                                         │  │
│  │  ┌─ 좌측 입력 패널 (QScrollArea 360px) ──┐  ┌─ 우측 ─┐ │  │
│  │  │ [1] 모델 선택 GroupBox               │  │ 시뮬레 │ │  │
│  │  │ [2] 전극 물성 파라미터 GroupBox       │  │ 이션   │ │  │
│  │  │     └ 프리셋 콤보 + 편집 토글        │  │ 결과   │ │  │
│  │  │     └ 파라미터 테이블 (14행)          │  │ Group  │ │  │
│  │  │ [3] 충방전 패턴 GroupBox              │  │ Box    │ │  │
│  │  │     └ 4개 라디오 (충전/방전/GITT/커스텀)│ │        │ │  │
│  │  │     └ QStackedWidget (4 페이지)       │  │ 외부탭 │ │  │
│  │  │     └ 시작 SOC / 출력 간격           │  │ Run 1  │ │  │
│  │  │ [4] 실행/초기화 버튼                  │  │ Run 2  │ │  │
│  │  └──────────────────────────────────────┘  │  ...   │ │  │
│  │                                            └────────┘ │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌── 하단 메인 프로그레스 바 (공유) ────────────────────────┐  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 의존성 및 임포트 가드

```python
try:
    import pybamm
    HAS_PYBAMM = True
except ImportError:
    HAS_PYBAMM = False
```

- `HAS_PYBAMM = False`일 경우: 실행 버튼 비활성화, 텍스트 `"PyBaMM 미설치"` 표시, 결과 영역에 경고 라벨 삽입
- 런타임 실행 시에도 재확인하여 `QMessageBox` 경고 후 조기 반환

---

## 3. UI 구성 요소

### 3.1 모델 선택 (`pybamm_model_group`)

| 항목 | 내용 |
|------|------|
| 위젯 | QComboBox (`pybamm_model_combo`) |
| 선택지 | **SPM** (Single Particle), **SPMe** (SPM with electrolyte), **DFN** (Doyle-Fuller-Newman) |
| 크기 | 340×60 고정 |

### 3.2 전극 물성 파라미터 (`pybamm_param_group`)

#### 프리셋 콤보 (11개)

`Chen2020` · `Ai2020` · `Ecker2015` · `Marquis2019` · `Mohtat2020` · `NCA_Kim2011` · `OKane2022` · `ORegan2022` · `Prada2013` · `Ramadass2004` · `사용자 정의`

- 시그널: `activated` → `_pybamm_load_preset()` (클릭 시에만 반응, 프로그래밍적 변경 무시)

#### 파라미터 테이블 (14행 × 3열)

| # | 파라미터 | 기본값 (Chen2020) | 단위 |
|---|---------|------------------|------|
| 0 | 양극 두께 | 75.6 | μm |
| 1 | 양극 입자 반경 | 5.22 | μm |
| 2 | 양극 활물질 비율 | 0.665 | - |
| 3 | 양극 Bruggeman | 1.5 | - |
| 4 | 음극 두께 | 85.2 | μm |
| 5 | 음극 입자 반경 | 5.86 | μm |
| 6 | 음극 활물질 비율 | 0.75 | - |
| 7 | 음극 Bruggeman | 1.5 | - |
| 8 | 분리막 두께 | 12.0 | μm |
| 9 | 분리막 Bruggeman | 1.5 | - |
| 10 | 전해질 농도 | 1000 | mol/m³ |
| 11 | 전극 면적 | 1.58 | m² |
| 12 | 셀 용량 | 5.0 | Ah |
| 13 | 온도 | 25 | °C |

- 파라미터명(0열)과 단위(2열)는 읽기 전용, 값(1열)만 편집 가능
- **기본 숨김**, `"파라미터 편집"` 토글 버튼으로 표시/숨김

#### 편집 토글 버튼 (`pybamm_edit_btn`)
- `QPushButton`, checkable
- 체크 시 테이블 표시 + 버튼 텍스트 `"편집 닫기"`, 해제 시 숨김 + `"파라미터 편집"`

### 3.3 충방전 패턴 (`pybamm_exp_group`)

4개 라디오 버튼 → `QStackedWidget` 4 페이지:

#### Page 0 — 충전

| 구성 요소 | 설명 |
|----------|------|
| 유형 콤보 | CC / CV / CCCV / Rest |
| 입력 필드 | C-rate (기본 1.0), 전압 (기본 4.2V), Cutoff (기본 0.05C) |
| (+) 버튼 | 현재 선택 항목 아래에 삽입 (선택 없으면 끝에 추가) |
| 스텝 리스트 | QListWidget, 기본 2항목: `CC \| Charge at 1C until 4.2V`, `CV \| Hold at 4.2V until C/50` |
| 삭제/전체삭제 | 선택 항목 삭제, 전체 비우기 |
| 사이클 수 | 기본 "1" |

#### Page 1 — 방전
- 충전과 동일 구조, 기본 전압 2.5V
- 기본 스텝: `CC \| Discharge at 1C until 2.5V`

#### Page 2 — GITT/HPPC

| 입력 항목 | 기본값 |
|----------|--------|
| 패턴 유형 | GITT / HPPC |
| 펄스 전류 | 0.5 C |
| 펄스 시간 | 600 s |
| 휴지 시간 | 3600 s |
| 반복 횟수 | 20 |
| 전압 하한 | 2.5 V |

#### Page 3 — 커스텀
- `QPlainTextEdit`에 PyBaMM 실험 문법 직접 입력

#### 공통 입력

| 항목 | 위젯 | 기본값 | 설명 |
|------|------|--------|------|
| 시작 SOC | QLineEdit | `"auto"` | 0~1 범위 또는 auto (모드별 자동 설정) |
| 출력 간격 | QLineEdit | `"10"` | 초 단위 또는 auto |

### 3.4 실행/초기화 버튼

| 버튼 | 크기 | 동작 |
|------|------|------|
| 시뮬레이션 실행 | 160×40, 볼드 | `pybamm_run_button()` 호출 |
| 탭 초기화 | 100×40 | `pybamm_tab_reset_button()` 호출 |

### 3.5 시뮬레이션 결과 영역

- `QGroupBox` (`"시뮬레이션 결과"`) 안에 `QTabWidget` (`pybamm_plot_tab`)
- **Expanding 사이즈 정책** — 남은 공간을 모두 활용
- **탭 닫기 가능** (×버튼)
- 누적 실행: Run 1, Run 2, ... 탭이 계속 추가됨

---

## 4. 시뮬레이션 엔진 (`run_pybamm_simulation`)

### 함수 시그니처

```python
def run_pybamm_simulation(model_name, params_dict, experiment_config) → pybamm.Solution
```

### 모델 생성

```python
model_map = {
    "SPM":  pybamm.lithium_ion.SPM,
    "SPMe": pybamm.lithium_ion.SPMe,
    "DFN":  pybamm.lithium_ion.DFN,
}
model = model_map[model_name]()
param = model.default_parameter_values
```

### 파라미터 매핑 (`_key_map`)

| 한국어 키 | PyBaMM 키 | 스케일 |
|----------|----------|--------|
| 양극 두께 | Positive electrode thickness [m] | ×1e-6 |
| 양극 입자 반경 | Positive particle radius [m] | ×1e-6 |
| 양극 활물질 비율 | Positive electrode active material volume fraction | ×1 |
| 양극 Bruggeman | Positive electrode Bruggeman coefficient (electrolyte) | ×1 |
| 음극 두께 | Negative electrode thickness [m] | ×1e-6 |
| 음극 입자 반경 | Negative particle radius [m] | ×1e-6 |
| 음극 활물질 비율 | Negative electrode active material volume fraction | ×1 |
| 음극 Bruggeman | Negative electrode Bruggeman coefficient (electrolyte) | ×1 |
| 분리막 두께 | Separator thickness [m] | ×1e-6 |
| 분리막 Bruggeman | Separator Bruggeman coefficient (electrolyte) | ×1 |
| 전해질 농도 | Initial concentration in electrolyte [mol.m-3] | ×1 |
| 전극 면적 | Electrode width [m] | ×1 |
| 셀 용량 | Nominal cell capacity [A.h] | ×1 |
| 온도 | Ambient temperature [K] | +273.15 (°C→K) |

- 함수형(function-type) 파라미터는 `try/except`로 건너뜀

### 초기 SOC 로직

| 모드 | auto 기본값 |
|------|------------|
| 충전 (charge) | 0.0 |
| 방전 (discharge) | 1.0 |
| GITT | 1.0 |
| CC-CV (ccv) | 0.0 |
| 커스텀 (custom) | 0.5 |

### 실험 빌드 (5개 모드)

| 모드 | 로직 |
|------|------|
| **ccv** | CC 충전 → CV 홀드 → CC 방전, cycles회 반복 |
| **charge** | UI 스텝 리스트 그대로, cycles회 반복 |
| **discharge** | UI 스텝 리스트 그대로, cycles회 반복 |
| **gitt** | GITT: [방전 펄스, 휴지] × repeats / HPPC: [방전 펄스, 휴지, 충전 펄스, 휴지] × repeats |
| **custom** | 사용자 텍스트를 콤마로 분리하여 step 리스트 생성 |

### 출력 간격 (period) 처리

```
사용자 입력값이 유효한 양수 → 각 step 문자열에 "(Xs period)" 접미어 추가
이미 "period" 포함된 step은 건너뜀
```

---

## 5. 결과 데이터 추출

`pybamm.Solution`에서 추출하는 변수:

| 변수 | PyBaMM 키 | 후처리 |
|------|----------|--------|
| 시간 | `Time [s]` | ÷60 → 분 |
| 전압 | `Terminal voltage [V]` | — |
| 전류 | `Current [A]` | — |
| 용량 | `Discharge capacity [A.h]` | fallback: `cumulative_trapezoid` 적분 |
| SOC (정규화) | `X-averaged negative particle surface concentration [mol.m-3]` | 초기값으로 나누어 정규화 |
| 양극 OCP | `X-averaged positive electrode open-circuit potential [V]` | fallback: `Positive electrode open-circuit potential [V]` |
| 음극 OCP | `X-averaged negative electrode open-circuit potential [V]` | fallback: `Negative electrode open-circuit potential [V]` |
| 양극 Li 농도 | `X-averaged positive particle surface concentration [mol.m-3]` | — |
| 음극 Li 농도 | `X-averaged negative particle surface concentration [mol.m-3]` | — |

- `EmptySolution` 체크: 비어 있으면 경고 후 조기 반환

---

## 6. 플롯 구성 (4개 서브탭)

각 Run 탭 내부에 `QTabWidget`으로 4개 서브탭 생성:

### Sub 1: 전압 커브 (1×2)

| 좌 | 우 |
|---|---|
| V vs Time [min] | V vs Capacity [Ah] |

### Sub 2: 종합 모니터링 (3×1, sharex)

| 행 | 내용 |
|---|------|
| 1 | Current [A] vs Time |
| 2 | Voltage [V] vs Time |
| 3 | Surface Conc. [norm] vs Time |

### Sub 3: 전극 분포 (2×2)

| | 좌 | 우 |
|---|---|---|
| 상 | 양극 OCP [V] | 음극 OCP [V] |
| 하 | 양극 표면 Li 농도 [mol/m³] | 음극 표면 Li 농도 [mol/m³] |

### Sub 4: dVdQ 분석 (1×2)

| 좌 | 우 |
|---|---|
| dV/dQ (충전, I>0) | dV/dQ (방전, I<0) |

- 제로 나눗셈 보호: `|dQ| > 1e-12` 필터
- 유효 데이터 2포인트 미만 시 빈 그래프

### 플롯 스타일링

모든 플롯에 `THEME` 딕셔너리 + `graph_base_parameter()` 적용:

| 속성 | 값 |
|------|---|
| figsize | (13, 7) |
| FIG_FACECOLOR | #FFFFFF |
| LINE_WIDTH | 1.4 |
| LINE_ALPHA | 0.6 |
| TITLE_SIZE / WEIGHT | 15 / bold |
| LABEL_SIZE | 12 |
| TICK_SIZE | 10 |
| GRID | dashed, α=0.18, #666666 |
| 색상 팔레트 | #3C5488, #E64B35, #00A087, #F39B7F, #4DBBD5, ... |

- 캔버스는 `QScrollArea`로 래핑하여 오버플로우 방지
- `NavigationToolbar` 포함 (줌, 팬, 저장)

---

## 7. 프리셋별 파라미터 값

| Preset | 양극두께 | 양극입자 | 양극AM | 양극Brug | 음극두께 | 음극입자 | 음극AM | 음극Brug | 분리막 | 분리막Brug | 전해질 | 면적 | 용량 | 온도 |
|--------|---------|---------|-------|---------|---------|---------|-------|---------|-------|-----------|-------|-----|-----|-----|
| Chen2020 | 75.6 | 5.22 | 0.665 | 1.5 | 85.2 | 5.86 | 0.75 | 1.5 | 12.0 | 1.5 | 1000 | 1.58 | 5.0 | 25 |
| Ai2020 | 68.0 | 3.0 | 0.62 | 1.83 | 76.5 | 5.0 | 0.61 | 2.91 | 25.0 | 1.5 | 1000 | 0.047 | 2.28 | 25 |
| Ecker2015 | 54.0 | 6.5 | 0.408 | 1.54 | 74.0 | 13.7 | 0.372 | 1.64 | 20.0 | 1.98 | 1000 | 0.085 | 0.156 | 25 |
| Marquis2019 | 100.0 | 10.0 | 0.5 | 1.5 | 100.0 | 10.0 | 0.6 | 1.5 | 25.0 | 1.5 | 1000 | 0.207 | 0.68 | 25 |
| Mohtat2020 | 67.0 | 3.5 | 0.445 | 1.5 | 62.0 | 2.5 | 0.61 | 1.5 | 12.0 | 1.5 | 1000 | 0.205 | 5.0 | 25 |
| NCA_Kim2011 | 50.0 | 1.63 | 0.41 | 2.0 | 70.0 | 0.508 | 0.51 | 2.0 | 25.0 | 2.0 | 1200 | 0.14 | 0.43 | 25 |
| OKane2022 | 75.6 | 5.22 | 0.665 | 1.5 | 85.2 | 5.86 | 0.75 | 1.5 | 12.0 | 1.5 | 1000 | 1.58 | 5.0 | 25 |
| ORegan2022 | 75.6 | 5.22 | 0.665 | 1.5 | 85.2 | 5.86 | 0.75 | 1.5 | 12.0 | 1.5 | 1000 | 1.58 | 5.0 | 25 |
| Prada2013 | 80.0 | 0.05 | 0.374 | 1.5 | 34.0 | 5.0 | 0.58 | 1.5 | 25.0 | 1.5 | 1200 | 0.3 | 2.3 | 25 |
| Ramadass2004 | 80.0 | 2.0 | 0.59 | 4.0 | 88.0 | 2.0 | 0.49 | 4.0 | 25.0 | 1.98 | 1000 | 1.061 | 1.0 | 25 |

### 프리셋별 전압 윈도우

| Preset | 충전 상한 | 방전 하한 | 비고 |
|--------|----------|----------|------|
| Chen2020 | 4.2V | 2.5V | |
| Ai2020 | 4.2V | 2.5V | |
| Ecker2015 | 4.0V | 2.5V | |
| Marquis2019 | 4.1V | 3.105V | |
| Mohtat2020 | 4.2V | 3.0V | |
| NCA_Kim2011 | 4.2V | 2.7V | 0.5C 기본 |
| OKane2022 | 4.2V | 2.5V | |
| ORegan2022 | 4.4V | 2.5V | |
| Prada2013 | 3.6V | 2.0V | LFP |
| Ramadass2004 | 4.2V | 2.8V | |

---

## 8. 시그널-슬롯 연결 요약

| 시그널 | 슬롯 |
|--------|------|
| `pybamm_mode_charge.toggled` | → stack page 0 |
| `pybamm_mode_discharge.toggled` | → stack page 1 |
| `pybamm_mode_gitt.toggled` | → stack page 2 |
| `pybamm_mode_custom.toggled` | → stack page 3 |
| `pybamm_run_btn.clicked` | → `pybamm_run_button()` |
| `pybamm_reset_btn.clicked` | → `pybamm_tab_reset_button()` |
| `pybamm_param_combo.activated` | → `_pybamm_load_preset()` |
| `pybamm_edit_btn.toggled` | → `_pybamm_toggle_param_table()` |
| `pybamm_chg_add_btn.clicked` | → `_pybamm_chg_add_step()` |
| `pybamm_chg_del_btn.clicked` | → `_pybamm_del_step(chg_list)` |
| `pybamm_chg_clear_btn.clicked` | → `pybamm_chg_list.clear()` |
| `pybamm_dchg_add_btn.clicked` | → `_pybamm_dchg_add_step()` |
| `pybamm_dchg_del_btn.clicked` | → `_pybamm_del_step(dchg_list)` |
| `pybamm_dchg_clear_btn.clicked` | → `pybamm_dchg_list.clear()` |
| `pybamm_plot_tab.tabCloseRequested` | → `_pybamm_close_run_tab()` |

---

## 9. 헬퍼 메서드 목록

| 메서드 | 역할 |
|--------|------|
| `_pybamm_close_run_tab(index)` | 지정 인덱스의 Run 탭 제거 |
| `pybamm_tab_reset_button()` | 모든 Run 탭 제거, 카운터 초기화, Chen2020 프리셋 복원 |
| `_pybamm_toggle_param_table(checked)` | 파라미터 테이블 표시/숨김 + 버튼 텍스트 변경 |
| `_pybamm_insert_step(list_widget, *items)` | 선택 항목 아래에 스텝 삽입 (선택 없으면 끝에 추가) |
| `_pybamm_chg_add_step()` | 충전 입력 바에서 스텝 문자열 생성 → 리스트에 삽입 |
| `_pybamm_dchg_add_step()` | 방전 입력 바에서 스텝 문자열 생성 → 리스트에 삽입 |
| `_pybamm_del_step(list_widget)` | 선택된 스텝 항목 삭제 |
| `_pybamm_collect_list_steps(list_widget)` | QListWidget → PyBaMM 실험 문자열 리스트 추출 |
| `_pybamm_load_preset(index)` | 프리셋 파라미터 + 전압 윈도우 + SOC/period 초기화 |
| `_create_plot_tab(fig, tab_no)` | matplotlib Figure → Qt 탭 위젯 생성 (Canvas + Toolbar) |

---

## 10. 에러 처리 및 방어 로직

| 상황 | 처리 |
|------|------|
| PyBaMM 미설치 | 실행 버튼 비활성화 + 경고 라벨 표시 |
| 시뮬레이션 실패 | `QMessageBox.critical` + traceback 표시 |
| EmptySolution | `QMessageBox.warning` + 조기 반환 |
| 스텝 리스트 비어있음 | 경고 메시지 + 반환 |
| 함수형 파라미터 | `try/except`로 건너뜀 (스칼라만 적용) |
| 변수 추출 실패 | 각 변수별 `try/except` → `None` 처리 후 플롯 건너뜀 |
| dV/dQ 제로 나눗셈 | `|dQ| > 1e-12` 필터 |
| 프로그레스 바 | indeterminate 모드(시뮬 중) → determinate 복귀(완료/에러) |
