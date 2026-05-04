---
tags: [work-log, daily, ai-tf, bdt, sbp, ect, glossary, hysteresis, cycle-data]
date: 2026-05-04
status: completed
related:
  - "[[AI_TF_Glossary_Simulation]]"
  - "[[AI_TF_Glossary_SBP]]"
  - "[[260504_ai_tf_glossary_wiki_addition]]"
  - "[[260429_hysteresis_unified_flow]]"
  - "[[260429_legend_overlay_fix]]"
  - "[[260430_fix_hysteresis_soc_offset_clip_relax]]"
  - "[[mbo_2026]]"
  - "[[Fuel_Gauge_IC_Architectures]]"
  - "[[시뮬레이션_용어사전]]"
---

# 2026-05-04 (월) 일지

## TL;DR

- **AI TF — 배터리 용어집** 시뮬레이션(151) + SBP(137) 카테고리를 wiki 통합 후 origin/main push (`48f9342`).
- **BDT 5월 4일 commit 9건** — Layer A 단일화 PR-1, 히스테리시스 6건 통합 수정, MBO 2026 + ADR-0010 갱신, grilling 결정 기록.
- **사이클 데이터 작업** 4/28 ~ 5/1 commit 흐름을 그룹별로 정리 (프로파일 분석 색상·히스테리시스 페어링·이어서 모드·.cyc cross-validate·PNE goto loop).
- **ECT** parameter 추출 시험 최적화 문의 + TabS12+ 셀 시험 진행 (디테일 보강 필요).

---

## 1. AI TF — 배터리 용어집 (오늘 메인 작업)

### 1.1 시뮬레이션 카테고리 (본인 전담)

다른 그룹원이 작성한 초안의 시뮬레이션 카테고리 21개를 박사급 peer 관점에서 보강해 **13그룹 151개 항목**으로 정비.

| 그룹 | 항목 | 핵심 신규 |
|---|---|---|
| 기본 방정식·법칙 | 13 | Maxwell-Stefan, PNP, 농축 용액 이론, Arrhenius |
| 원자/분자 스케일 | 7 | AIMD, ReaxFF, KMC, Phase Field, Marcus |
| 전극·셀 스케일 | 13 | SPMe, ESPM, RSPM, Pseudo-3D, 응력-확산 |
| 모듈/팩 — 열·전기 | 6 | 럼프드 / 1D~3D / ETC / ETMC, 열폭주 모델 |
| **구조해석·안전성 (신규)** | **28** | **충돌·낙하·볼 드랍·관통·압착·덴트·CFL·Johnson-Cook·SPH·ALE** |
| 멀티스케일 | 4 | **MSMD, GH-MSMD** (NREL House Code 직결) |
| 데이터·하이브리드 | 14 | **PINN, phygnn, PINNSTRIPES** (NREL 계열) |
| 추정 | 12 | EKF / UKF / AUKF, PF, RLS |
| 수명 | 8 | **캘린더-사이클 분리(NREL SSC)**, SEI/Li 도금 |
| 수치 해석 | 13 | FVM, FDM, DEM, LBM, MOR/POD |
| 워크플로우 | 12 | UQ, GSA, **회귀 검증 (BDT 4-케이스)**, DOE |
| 도구 | 14 | PyBaMM, MPET, BatPaC, **LS-DYNA·Abaqus·Radioss·Pam-Crash** |
| 응용·실시간 | 7 | MIL/SIL/PIL/HIL, 디지털 트윈, ECT 통합 |

### 1.2 SBP 카테고리 (PPT 비교 자료 기반 정리)

`SBP_알고리즘비교_Ver2.1.pptx` 번들 텍스트(44 슬라이드) + 31장 슬라이드 캡처 분석.

| 그룹 | 항목 | 비고 |
|---|---|---|
| SBP / IC 일반 | 10 | NVT / SDI / ADI / TI / MPC7011C / SMBus·I2C |
| SOC 변수 | 6 | RSOC / ASOC / AvSOC / VFSOC / TrueSOC / RepSOC |
| 용량 변수 | 15 | Qmax 계열 + ADI MixCap/AvCap/RepCap/FullCap* |
| SOC 알고리즘 | 9 | CCM / OCV est / EDV sim / Mixing / Servo / EoC |
| EDV·Cut-off | 7 | EDV / TermV / Taper / CCCV |
| OCV 관련 | 11 | 2-point OCV / FastOcvQmax / Long·Short Rest |
| R-Table / 저항 | 15 | Ra·Rb · ADI 4-register · Rapid update · LPF |
| SOH | 7 | **SOH 1.0 / 2.0**, Z_re-to-Qmax LUT |
| **CSD** | 7 | **CSD 1.5 / 2.0**, Stress model, ESR↑, Si correlation |
| **ISD** | 13 | **CIS 3.0 / 4.0**, CCP, RISC, IISC, SVK, 적산 ISC |
| **SBA** | 6 | Si Loss / 3.6 V peak / dV/dQ / Hysteresis |
| Dynamic EDV | 6 | User Habits → Fading sim → ±50 mV adjust |
| SOC Smoothing | 11 | ADI Converge-to-Empty / TI 99% Hold |
| Register | 14 | BatteryStatus / IChgTerm / Cycle Count 등 |

NVT / SDI / ADI / TI 4-vendor 변수명 매핑 표 동봉 (Qmax↔MaxCap↔FullCapNom 등).

### 1.3 wiki 통합

- `wiki/30_modeling/AI_TF_Glossary_Simulation.md` 신규 (281행)
- `wiki/21_electrochem/AI_TF_Glossary_SBP.md` 신규 (282행)
- `wiki/19_bdt_history/260504_ai_tf_glossary_wiki_addition.md` 변경로그
- `MOC_Battery_Knowledge` / `MOC_Modeling_AI` cross-ref 추가
- TSV 원본 `Downloads/SBP알고/용어_시뮬레이션_v2.txt`, `용어_SBP_v1.txt` 보존
- worktree commit `e200716` → main merge `48f9342` → push 완료

> 다른 카테고리와의 분리: Tafel 식·SEI 성장 모델·Li 도금 모델·열폭주 모델·응력-확산 결합 모델은 정의에서 "현상은 X 카테고리, 본 항목은 모델"로 명시.

---

## 2. BatteryDataTool — 5월 4일 commit 흐름

오늘 9 commit. PR-1 리팩터링·히스테리시스 통합·MBO/ADR/grilling 문서 정비 + AI TF wiki.

| Commit | 분류 | 요지 |
|---|---|---|
| `48f9342` | 머지 | AI TF 배터리 용어집 wiki 추가 (시뮬 151 + SBP 137) |
| `e200716` | 문서 | (worktree) AI TF 용어집 wiki 5 files +642 |
| `4898c62` | 문서 | MBO 2026 제출본 — 수명 모델링 통합, dV/dQ SW 항목 정리, AX 5건 |
| `c7ca3e1` | 머지 | DataTool_optRCD_proto_.py 병렬 세션 충돌 해소 |
| `5d72c53` | 리팩터링 | **PR-1 Layer A 단일화** — `_unified_pne_load_raw` 의 `data_scope` 제거 |
| `4764b00` | 머지 | Merge branch 'main' of github |
| `9e4a9d5` | 문서 | MBO 2026 확정 + **ADR-0010 MBO Track Mapping** + CONTEXT.md 갱신 |
| `45a814f` | 문서 | **grilling 결정 기록** — CONTEXT.md + ADR 3건 + bundle 검증기 2건 |
| `600f2cf` | 버그수정+기능추가 | **히스테리시스 6건 통합 수정** — 페어링 / anchor / scaling / CV / 분류 / axis_mode |

### 2.1 핵심 흐름

- **PR-1 Layer A 단일화**: `unified_profile_core` 파이프라인의 첫 stage(`_unified_pne_load_raw`)에서 `data_scope` 분기를 제거하고 view 단계로 이동. 레벨 2 단일 flow 리팩터의 후속 PR.
- **히스테리시스 6건 통합 수정**: 페어링·anchor shift·scaling·CV·분류·axis_mode 의 회귀를 한 묶음으로 정리. `260429_hysteresis_unified_flow` 후속.
- **MBO 2026 + ADR-0010**: 7-track 구조에 ADR-0010 (MBO Track Mapping) 추가. 수명 모델링 통합·AX 성과 5건.
- **grilling 결정**: ADR 3건 + bundle 검증기 2건. CONTEXT.md 갱신.

---

## 3. 사이클 데이터 작업 — 4/28 ~ 5/1 commit 흐름

이번 주 BDT 사이클 영역에서 30+ commit 발생. 영역별로 묶어 정리.

### 3.1 .cyc / TC 경계 / cross-validate

| Commit | 요지 |
|---|---|
| `8685514` | .cyc TC 경계 휴리스틱 누락 보정 — SaveEndData ground truth cross-validate |
| `f980852` | .cyc cross-validate Phase 2 — Condition (col[2]) 도 SaveEndData 기준 정정 |
| `c5a087a` | cycle_range 1:N 확장 케이스 진단 — TC N 입력 시 N+1 도 로딩되는 문제 |
| `7232bd4` | **PNE outer goto loop 확장** — Cycle 반복횟수 + Goto 반복횟수 + Goto 스텝 결합 패턴 분석 (4/30) |

### 3.2 히스테리시스 (페어링 / 라벨 / dQdV)

| Commit | 요지 |
|---|---|
| `923ab5b` | 사이클 라벨/색상 — 깊이 기반 (Dchg/Chg X%) (4/28) |
| `f17fd18` | 라벨 off-by-one — classified 기반 hysteresis TC 필터링 |
| `a55e16e` | TC 페어링 — TC N + TC N+1 보완 phase 결합 |
| `9364904` | TC 페어링 체크박스 + 진단 로그 |
| `399ac53` | 후처리 색상 detection 이 페어링 모드 segment 순서를 cycle 경계로 오인 |
| `3656b17` | **히스테리시스 프리셋** — 단일 flow + Origin 호환 dQdV + Hysteresis_Analysis long-format 시트 (4/29) |
| `cd4ac67` | long-format 빌드를 saveok ON 일 때만 실행 (성능) |
| `29d77a6` | SOC offset anchor shift + unified_flow dQdV KeyError (4/29) |
| `316fa22` | RSS 측정 사이클 HYSTERESIS 오분류 수정 |
| `600f2cf` | **6건 통합 수정 — 페어링/anchor/scaling/CV/분류/axis_mode** (5/4) |

### 3.3 사이클-이어서 모드 / 프로파일 분석

| Commit | 요지 |
|---|---|
| `cfa5259` | '이어서' overlap 옵션 제거 (충/방전 데이터 범위) (4/28) |
| `0bba268` | Option B (minor DCHG dim) + Cy12 boundary offset 누락 |
| `323ba52` | 이어서 모드 C-rate y축 대칭 범위 (충/방전 모두 표시) |
| `88a48bf` | plot 4/5 Y축이 plot 1 과 다른 문제 — 일관성 정정 (4/29) |
| `316fa22` | plot 4/5 yticks/ylim 일치 |
| `c02e548` | ax4 OCV/CCV y tick / y label 명시 설정 |
| `d270ff8` | OCV/CCV 범례 1회만 출력 |
| `8fd11b0` | Y tick 이 highlimit 직전까지만 출력되는 문제 (4.7 입력 → 4.5 표시) |
| `5803272` | **사이클 분류 정규화** — schedule + 휴리스틱 분류 동일 명칭 통일 |
| `6373f94` | 프로파일 분석 모든 옵션의 plot 색상 로직 통합 — `_cycle_id_tag` 단일화 (4/28) |
| `e30900c` | 프로파일 분석 4종 모델 spec + 다중경로 색상 G6 |
| `5609f2d` | Voltage Y축 gap 기본값 0.1 → 0.2 (라벨 겹침 해소) |
| `7c72ac5` | 범례가 plot 영역 잠식 + 다중 경로 라벨에 시험명 사용 |

### 3.4 UI / 채널 리스트 / 필터링

| Commit | 요지 |
|---|---|
| `2b11b3d` | **현황/필터링 탭 분리** + 충방전기명 검색 지원 (4/29) |
| `72ef2bc` | 필터링 탭을 현황 탭 내부 sub-tab 으로 이동 |
| `3d4ba2b` | 채널 리스트 sub-tab btn_filter 제거 — 필터링 sub-tab 전용화 |
| `cb6c4a9` | 경로 테이블 — TC 항상 편집 가능 + Excel-style 드래그 채우기 (4/28) |
| `0d86593` | 데이터 탭 다중 셀 선택·복사 — ExtendedSelection + Ctrl+C |
| `27b466a` | matplot toolbar 위치 일관화 — sub-tab 외부로 이동 |
| `59c0a20` | CH 채널 제어 색상이 재도색 후 plot 라인 색과 불일치 |
| `5a39af9` | 데이터 서브탭 'Cycle' 컬럼 중복 + offset 진단 로그 |

### 3.5 기타 안정화

| Commit | 요지 |
|---|---|
| `882332a` | 패턴 리스트 Load — pyodbc NameError → `_LazyModule` 프록시 도입 (4/30) |
| `87d8efb` | DCIR 분석 NameError: scipy lazy import → eager import |
| `3e0e902` | `all_data_folder` numpy array truthiness 에러 |
| `7b2dbcb` | .gitignore — skills CLI lockfile 제외 (5/1) |
| `a61eb77` | DataTool_optRCD_proto_.py 한글 주석/docstring/log 윤문 (5/1) |
| `64cc4fd` | 폴더명 fallback 라벨 — 마지막 '_' 이후 텍스트만 추출 |
| `182d6c9` | 다중 경로 + 사이클 적은 케이스 — group 대신 distinct 색상 |
| `020131b` | 시뮬레이션 용어사전 (배터리그룹 시뮬 파트, 4/29 — 별도 출처) |

---

## 4. ECT 측정 · 셀 시험

- **ECT parameter 추출 시험 최적화 문의** — *문의 대상 / 핵심 질의 / 답변 기록 보강 필요*
- **TabS12+ 셀 시험 진행** — *시험 항목 / 조건 / 현 단계 기록 보강 필요*

> 본 항목은 BDT 트랙 7 (ECT 빅데이터)와 직결. 시뮬레이션 용어집의 **ECT 통합 시뮬레이션** 항목과 연결.

---

## 5. 산출물 / Git 통합

| 분류 | 위치 | 비고 |
|---|---|---|
| TSV 원본 | `Downloads/SBP알고/용어_시뮬레이션_v2.txt`, `용어_SBP_v1.txt` | AI TF 그룹 공유용 |
| wiki 노트 (시뮬) | `30_modeling/AI_TF_Glossary_Simulation.md` | 281 행 |
| wiki 노트 (SBP) | `21_electrochem/AI_TF_Glossary_SBP.md` | 282 행 |
| 변경로그 | `19_bdt_history/260504_ai_tf_glossary_wiki_addition.md` | 배경·산출물·다음 단계 |
| MOC 갱신 | `MOC_Battery_Knowledge`, `MOC_Modeling_AI` | cross-ref |
| Git push | [`48f9342`](https://github.com/Breezyryu/BDT_dev/commit/48f9342) | main 통합 |

---

## 6. 다음 단계

### AI TF 후속

- **v3** — 다른 그룹원 작성 카테고리(양극재·음극재·열화 메커니즘 등)와 정합성 재점검
- **SBP 보강** — 31장 PNG figure에서 블록도·수식 figure 추가 디테일 추출
- **시뮬레이션 통합** — 본 카테고리와 [[시뮬레이션_용어사전]] (16개 코어 개념) 사이의 통합 인덱스

### BDT

- **PR-2 ~ PR-N** — Layer A 단일화 후속. data_scope 의존 다른 stage들 식별·정비
- **히스테리시스** — 6건 통합 수정의 회귀 검증 (BDT 4-케이스 표준)
- **PNE goto loop** — 외부 goto 루프 확장 패턴 production 데이터 검증

### ECT 시험

- 문의 결과 + TabS12+ 진행 단계 워크로그 정리
- 위치: `wiki/22_experiments/` 또는 본 worklog 후속 노트

### 사이클 데이터

- 사이클 분류 정규화(`5803272`)와 .cyc cross-validate Phase 2 의 회귀 검증
- 이어서 모드 plot 4/5 Y축 일관성 후속 모니터링
