---
title: "AI TF 배터리 용어집 wiki 추가 — 시뮬레이션 + SBP"
date: 2026-05-04
tags: [changelog, AI_TF, glossary, wiki, simulation, SBP, BMS]
type: changelog
status: completed
related:
  - "[[AI_TF_Glossary_Simulation]]"
  - "[[AI_TF_Glossary_SBP]]"
  - "[[시뮬레이션_용어사전]]"
  - "[[Fuel_Gauge_IC_Architectures]]"
---

# 2026-05-04 — AI TF 배터리 용어집 wiki 추가

## 배경

AI TF 활동의 일환으로 배터리 그룹이 작성하는 배터리 용어집(`Downloads/SBP알고/용어.txt`, 6열 TSV, ~400행) 중 **시뮬레이션 카테고리는 본인 전담**, **SBP 카테고리는 PPT 비교 자료 기반 정리**가 할당됨.

원본 자료:
- `Downloads/SBP알고/용어.txt` — 다른 그룹원이 작성한 초안 (시뮬레이션 카테고리 21개 포함)
- `Downloads/SBP알고/SBP_알고리즘비교_Ver2.1_bundle.txt` — DRM-bypass된 PPT 텍스트 번들 (44 슬라이드, NVT/SDI/ADI/TI 4개 IC 벤더 비교)
- `Downloads/SBP알고/2026-05-04 11 *.png` — 31개 슬라이드 캡처

## 산출물

### 1. 시뮬레이션 카테고리 — 13개 그룹 151개 항목

- **TSV 원본**: `Downloads/SBP알고/용어_시뮬레이션_v2.txt` (7열, UTF-8/CRLF)
- **wiki 노트**: [[AI_TF_Glossary_Simulation]] (`30_modeling/`)

원본 21개 → 151개로 확장. 추가 영역:
- 기본 방정식·법칙 (Maxwell-Stefan, PNP, 농축 용액 이론, Arrhenius 등)
- 멀티스케일 (**MSMD, GH-MSMD** — NREL House Code 베이스)
- 데이터·하이브리드 (**PINN, phygnn, PINNSTRIPES** — NREL 계열)
- 수명/노화 (**캘린더-사이클 분리 모델** — NREL SSC 형식, SEI 성장, Li 도금)
- **구조해석·안전성 시뮬레이션 (28개 신규)** — 충돌·낙하·볼 드랍·관통·압착·덴트·CFL·Johnson-Cook 등
- 도구 — PyBaMM, MPET, BatPaC, LS-DYNA, Abaqus, Radioss, Nastran, Pam-Crash 등

### 2. SBP 카테고리 — 14개 그룹 137개 항목

- **TSV 원본**: `Downloads/SBP알고/용어_SBP_v1.txt`
- **wiki 노트**: [[AI_TF_Glossary_SBP]] (`21_electrochem/`)

NVT/SDI/ADI/TI 4개 IC 벤더의 SOC, SOH, CSD 1.5/2.0, ISD (CIS 3.0/4.0, SVK), SBA, Dynamic EDV, R-Table, SOC Smoothing 알고리즘을 포괄. 벤더별 변수명 매핑 표(Qmax↔MaxCap↔FullCapNom 등) 포함.

## 다른 카테고리와의 분리

진정한 키워드 중복은 없음. 의미 인접 항목은 정의에서 명시적으로 차별화:

| 시뮬레이션 (모델/식) | 다른 카테고리 (현상/그래프) |
|---|---|
| Tafel 식 | 분석/측정 — Tafel Plot |
| 응력-확산 결합 모델 | 열화 메커니즘 — 기계적 응력 |
| 열폭주 모델 | 안전성/열화 — 열 폭주 |
| SEI 성장 모델 | 열화 메커니즘 — SEI 성장/분해 |
| Li 도금 모델 | 안전성/열화 — 리튬 플레이팅 |
| EKF (SBP) | 시뮬레이션 EKF 일반 정의 |
| dV/dQ 분석 (SBA) | 분석/측정 — dQ/dV |
| DCIR/ACIR/ESR (SBP) | 성능/상태 지표 — 일반 |

## 위치 결정

- 시뮬레이션 → `30_modeling/` — PyBaMM·PINN과 같은 폴더
- SBP → `21_electrochem/` — `Fuel_Gauge_IC_Architectures.md`와 같은 폴더
- 두 파일은 frontmatter `related`로 cross-reference

## 다음 단계 후보

- v3 — 다른 그룹원이 작성한 다른 카테고리(양극재·음극재·열화 메커니즘 등)와 정합성 재점검
- SBP — 31개 PNG 슬라이드 캡처에서 추출 가능한 추가 디테일(블록도, 수식 figure) 보강
- 시뮬레이션 — 본 카테고리와 [[시뮬레이션_용어사전]](16개 코어 개념) 사이의 통합 인덱스 작성 검토
