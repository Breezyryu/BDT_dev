---
relocated: 2026-04-22
source_vault: "docs/vault/03_Battery_Knowledge/ACIR_DCIR_RSS.md"
title: "ACIR / DCIR / RSS — 배터리 내부저항 3종"
aliases:
  - "내부저항"
  - "Internal Resistance"
  - "ACIR"
  - "DCIR"
  - "RSS"
tags:
  - Battery_Knowledge
  - 전기화학
  - 저항
  - 분석법
type: knowledge
status: active
related:
  - "[[GITT]]"
  - "[[Electrochemical_parameter]]"
  - "[[Battery_Electrochemical_properties]]"
  - "[[MOC_Battery_Knowledge]]"
created: 2026-04-19
updated: 2026-04-19
source: "BDT 사이클 분류 재검토 트랙"
---

# ACIR / DCIR / RSS — 배터리 내부저항 3종

> [!abstract] 요약
> 배터리 내부저항은 측정 주파수(또는 시간 스케일)에 따라 **ACIR → DCIR → RSS** 의 3단 계층을 이룬다. 고주파에서 저주파로 갈수록 포함되는 물리 성분이 **전자저항 → + 이온(계면)저항 → + 확산저항** 순으로 누적된다. 측정 방법(EIS / Pulse Discharge / Simplified GITT)과 BDT 의 시험 프로파일(.sch)이 어떻게 대응되는지 정리.

## 저항 3종의 계층

| 저항 | 주파수 영역 | 포함 물리 성분 | 의미 |
|------|------------|---------------|------|
| **ACIR** (Alternating Current Internal Resistance) | ≈1 kHz (고주파) | R_ohm (전자저항만) | 전극 재료·집전체·탭·접촉 저항 |
| **DCIR** (Direct Current Internal Resistance) | 0.3 Hz ~ 수 Hz (중저주파) | ACIR + R_ct + R_film | 전하전달·피막 저항 포함 |
| **RSS** (Resistance of Steady-State) | 0 Hz (정상상태) | DCIR + R_diffusion | 확산저항까지 — 전극 분극 주원인 |

**수식 관계**:
$$\text{RSS} = \text{ACIR} + R_\text{ct} + R_\text{film} + R_\text{diffusion} = \text{DCIR} + R_\text{diffusion}$$

## 원리 — 왜 주파수에 따라 저항이 달라지는가

전기화학 시스템은 **시간 상수가 서로 다른 여러 프로세스의 직렬 연결**로 모델링된다:

```
(고주파) 전자 이동 → 이온 이동·계면 반응 → 확산 → (저주파)
   ms 미만      ms ~ 초                   수십 초 ~ 분
```

- **고주파(1kHz)**: 빠른 전자 이동만 응답 → R_ohm (ACIR)
- **중저주파(0.3~수 Hz)**: 전극 계면의 전하 전달(Rct)과 SEI/피막(Rf)까지 응답 → DCIR
- **DC(정상상태)**: Li+ 이온이 전극 내부를 확산하는 느린 과정까지 모두 포함 → RSS

이 때문에 **RSS 가 가장 크고, ACIR 가 가장 작다**. EIS Nyquist 플롯에서 확인:

```
          고주파 끝점(1585 Hz)          저주파(0.3 Hz)       f→0 외삽
    Z' = 35 mΩ ─────────────── Z' = 52 mΩ ─────────── Z' ≈ 62 mΩ
           ACIR                    DCIR                   RSS
```

## 측정 방법 — BDT 에서 어떻게 드러나는가

| 방법 | 대상 저항 | 프로파일 시그니처 | BDT 에서의 감지 키 |
|------|----------|------------------|-------------------|
| **EIS** | ACIR·DCIR (주파수 스윕) | BDT 범위 밖 (별도 임피던스 분석기) | — |
| **Pulse Discharge Test** | **DCIR** | 10 s 내외 펄스 + **짧은 REST (≤1 min)** | `.sch` 단일 DCHG + 짧은 REST, 확산 미성립 |
| **HPPC** (Hybrid Pulse Power Characterization) | 각 SOC 의 DCIR (파워 맵) | 한 SOC 에서 **다전류 레벨 펄스 세트** | `.sch` N=1, dchg≥4, EC≥다수, 짧은 REST |
| **Simplified GITT → RSS** | **RSS** | 펄스 + **긴 REST (≥30 min)** → OCV 복귀 대기 | `.sch` 펄스 반복 + REST≥1800s |
| **GITT (full)** | OCV, D_Li, R_total | 소전류 CC(ΔSOC≤5 %) + **매우 긴 REST(≥1 h)** × 다수 | `.sch` N≥10, n_steps≤3, REST≥3600s, 전류≤C/10 |

**핵심 판별 지표**: **"펄스 후 REST 시간"** 이 DCIR / RSS 를 가르는 결정적 변수.
- REST ≤ 1 min → 확산 미완성 → **DCIR**
- REST ≥ 30 min → 확산 평형 → **RSS**

## SOC·온도 의존성

DCIR·RSS 모두 **SOC / 온도에 강의존**한다 (GITT 측정 사례):

```
    DCIR·RSS vs SOC/DOD
    ┃
  RSS├─────╮                                           ╭─── 급증
    │      ╰──╮                                   ╭───╯
    │         ╰──╮            ╭──────────╮   ╭──╯      ← SOC 0.9+ 에서
    │            ╰──╮     ╭──╯          ╰──╮           고확산저항
    │               ╰──╯                    ╰──╮       (Li+ 포화)
 DCIR├─────╮                                   ╰───
    │      ╰──╮                         ╭──╯     
    │         ╰───╮                 ╭──╯         
    │             ╰─────────────╯   ╰─           ← 최소 SOC 40~60 %
    └──────────────────────────────────────── SOC
       0.1   0.2   0.3   0.4   0.5   0.6   0.7   0.8   0.9   1.0
```

- **양 극단(SOC ≤ 0.1 또는 ≥ 0.9)에서 급증** → Li+ 고갈/포화로 확산계수 급감
- 특히 RSS 가 SOC 0.95+ 에서 급증 → **실용 방전 용량 한계 결정**

## RSS 의 산업적 중요성

저자가 강조한 RSS 특성:

1. **실용 출력 용량의 스위치 역할** — 특정 전류에서 배터리가 낼 수 있는 실제 용량을 결정.
2. **사이클·보관에 따라 증가** — SEI 성장, 양극/음극 열화, 전해액 고갈 모두 RSS 를 키움.
3. **RSS 증가 → 수명 페이드 가속** — 피드백 루프 (저항↑ → 발열↑ → 열화↑)
4. **산업화 지체** — ACIR 는 양산 QC 에 표준이지만, DCIR·RSS 는 측정 비용·시간 부담으로 아직 제한적 사용.
5. **저비용 대안 연구 중** — 기존 방전 커브로부터 RSS 를 역산하는 방법 (저자 연구).

## BDT 프로파일 분류 매핑

BDT 에서 .sch 기반 사이클 분류 시 이 저항 측정을 다음 카테고리로 대응:

| BDT 카테고리 | 대응 측정 | 판별 규칙 |
|--------------|----------|----------|
| **DCIR** | 단일/소수 SOC 의 DCIR pulse | N=1, 짧은 펄스 + REST≤1m |
| **HPPC** | 한 SOC 다전류 power map | N=1, dchg≥4, EC 다수, 짧은 REST (단, BDT 데이터셋에는 현재 없음) |
| **SOC별 사이클** | 여러 SOC 순회 DCIR/RSS | N≥5, EC≥4, 각 SOC 블록 반복 |
| **GITT** | full GITT (OCV·D_Li) | N≥10, n_steps≤3, REST≥1h, 전류≤C/10 |
| **히스테리시스** | V-SOC 경로 비대칭 | N=1, SOC 또는 DOD EC 플래그 |

## 관련 문서

- [[GITT]] — full GITT 측정법 (OCV·D_Li 추출)
- [[Electrochemical_parameter]] — 전기화학 파라미터 개요
- [[Battery_Electrochemical_properties]] — 배터리 전기화학 특성
- BDT 사이클 재분류 설계: `docs/code/02_변경검토/260419_사이클분류_전면재검토.md`

## 참고

- 원문 설명(저자 미상, 친구 상담 맥락): ACIR / DCIR / RSS 정의 및 RSS 산업적 중요성.
- EIS Nyquist 플롯 기반 저항 성분 분해 예시 (35 / 52 / 62 mΩ).
- GITT 측정 결과의 DCIR vs RSS vs SOC 플롯 (양 극단 급증 확인).
