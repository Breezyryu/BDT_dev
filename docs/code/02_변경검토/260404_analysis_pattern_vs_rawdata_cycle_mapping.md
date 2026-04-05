# 260404 패턴파일 ↔ Raw Data ↔ BDT 논리 사이클 대응 분석

## 1. 분석 목적

BDT 사이클 분석 탭의 plot X축 "Cycle"이 실제로 무엇을 의미하는지 규명한다.  
충방전 패턴파일(Toyo PTN / PNE .sch)에서 정의된 "사이클"과, 기기가 기록한 raw data의 "TotlCycle", 그리고 BDT가 최종 표시하는 논리 사이클이 서로 어떻게 다른지 계층별로 비교한다.

---

## 2. 분석 대상 실데이터

| # | 충방전기 | 경로 | 용량 | 시험 유형 |
|---|---------|------|------|----------|
| ① | **Toyo** | `250207_250307_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 1-100cyc / 030` | 1689 mAh | 가속수명 (다단계 충전) |
| ② | **PNE**  | `251028_260428_05_나무늬_2335mAh_Q8 ATL 선상 SEU4 RT @1-1202 / M01Ch008[008]` | 2335 mAh | 가속수명 (다단계 충전) |
| ③ | **PNE**  | `250905_250915_00_류성택_4-187mAh_M2-SDI-open-ca-half-14pi-GITT-0.1C-T23 / M01Ch025[025]` | 4.187 mAh | GITT 하프셀 (Cathode) |
| ④ | **PNE**  | `250905_250915_00_류성택_4-376mAh_M2-SDI-open-an-half-14pi-GITT-0.1C-T23 / M01Ch024[024]` | 4.376 mAh | GITT 하프셀 (Anode) |
| ⑤ | **PNE**  | `250513_250526_05_나무늬_2610mAh_Gen5+B SDI MP1 DoE SBR 0.7 DCIR / M01Ch038[038]` | 2610 mAh | DCIR (MK Pulse) |
| ⑥ | **PNE**  | `260109_260112_05_이근준_5000mAh_Gen5P Si5 ATL T2 3M 보관 용량 측정 4cycle SOC 30 setting ch7 to 12 / M01Ch007[007]` | 5000 mAh | 보관 용량 측정 |
| ⑦ | **PNE**  | `260202_260226_05_문현규_5075mAh_Cosmx 25Si 율별용량+Hybrid ch54 / M01Ch054[054]` | 5075 mAh | 율별 용량 + Hybrid |
| ⑧ | **PNE**  | `260204_260226_05_문현규_4900mAh_Cosmx gen5 율별용량 ch61 / M01Ch061[061]` | 4900 mAh | 율별 용량 |
| ⑨ | **PNE**  | `260226_260228_05_문현규_3885mAh_PA1 연속저장 DCIR / M01Ch018[018]` | 3885 mAh | 연속저장 DCIR (M01Ch015는 SaveEndData 비어있음) |

---

## 3. Toyo 측 분석

### 3.1 패턴파일 구조 (Option3.PTN)

Toyo 충방전기는 `.PTN` 파일 한 개에 RPT + 가속수명 루프를 모두 정의한다.  
아래는 Q7M 1689mAh 시험의 스텝 구조:

| Mode(Step) | 충전(ChgMode / C-rate) | 방전(DchgMode / C-rate) | 방전 끝전압 | LoopTo | LoopCount | 역할 |
|-----------|------------------------|--------------------------|------------|--------|-----------|------|
| 1  | Rest | CC 0.2C → 2.75V | 2.75V | — | 1 | RPT 초기 방전 |
| 2  | CCCV 0.2C/4.5V → 0.02C | CC 0.2C → 2.75V | 2.75V | — | 1 | RPT 0.2C |
| 3  | CCCV 0.2C/4.5V → 0.02C | CC 0.5C → 2.75V | 2.75V | — | 1 | RPT 0.5C |
| 4  | CCCV 0.2C/4.5V → 0.02C | CC 1C → 2.75V | 2.75V | — | 1 | RPT 1C |
| 5  | CC 2C (충전만)           | Rest | —    | — | 1 | 가속수명 충전 Step 1 |
| 6  | CC 1.65C (충전만)        | Rest | —    | — | 1 | 가속수명 충전 Step 2 |
| 7  | CCCV 1.4C/4.3V (충전만) | Rest | —    | — | 1 | 가속수명 충전 Step 3 |
| 8  | CCCV 1C/4.5V            | CC 1C → 3.6V  | 3.6V | — | 1 | 가속수명 충·방전 동시 |
| 9  | Rest                    | CC 0.5C → 3.2V | 3.2V | **5** | **9801** | 루프 종점 (Loop Back→Mode 5) |
| 10 | CCCV 0.2C/4.5V → 0.02C | CC 0.2C → 2.75V | 2.75V | — | 1 | 후처리 RPT |
| 11 | CCCV 0.2C/4.5V → 0.02C | Rest | — | — | 1 | 만충 대기 |

**핵심**: 루프는 Mode 5→9 (5 스텝)을 9,801회 반복.  
Mode 8은 충전과 방전이 한 스텝에 묶여 **동일한 TotlCycle을 공유**.

### 3.2 Raw Data 구조 (CAPACITY.LOG)

기기가 기록하는 `CAPACITY.LOG`는 **스텝 실행이 끝날 때마다** 1행을 추가한다.

| 컬럼 | 의미 | 비고 |
|------|------|------|
| `Cycle` | 기기 자체 카운터 | 항상 1 (사실상 무의미) |
| `TotlCycle` | **누적 스텝 실행 횟수** | 스텝 1회 완료 → +1, 절대 감소 안 함 |
| `Mode` | PTN 스텝 번호 | 1~11 (패턴파일 Mode와 동일) |
| `Condition` | 충전(1)/방전(2)/휴지(3)/루프(8) | — |
| `Cap[mAh]` | 해당 스텝의 용량 | — |

**실데이터 예시 (TotlCycle 1~9):**

| TotlCycle | Condition | Mode | Cap[mAh] | 설명 |
|-----------|-----------|------|-----------|------|
| 1  | 2 | 1  | 407.99  | RPT 초기 방전 |
| 2  | 1 | 2  | 1763.62 | RPT 0.2C 충전 |
| 2  | 2 | 2  | 1720.24 | RPT 0.2C 방전 ← **TotlCycle 공유!** |
| 3  | 1 | 3  | …       | RPT 0.5C 충전 |
| …  | … | …  | …       | … |
| 5  | 1 | 5  | 543.57  | 가속수명 Loop 1: CC 2C 충전 |
| 6  | 1 | 6  | …       | Loop 1: CC 1.65C 충전 |
| 7  | 1 | 7  | …       | Loop 1: CCCV 1.4C 충전 |
| 8  | 1 | 8  | 487.22  | Loop 1: CCCV 1C 충전 |
| 8  | 2 | 8  | 1223.77 | Loop 1: CC 1C 방전 ← **TotlCycle 공유!** |
| 9  | 2 | 9  | 406.34  | Loop 1: CC 0.5C 방전 (루프 종점) |
| 10 | 1 | 5  | 534.18  | Loop 2: CC 2C 충전 (다음 루프 시작) |

**TotlCycle과 PTN Mode의 관계:**
- TotlCycle은 **스텝 실행당 +1** (충전/방전이 한 스텝에 묶여도 1 증가)
- Mode 8은 충방전이 한 스텝 → 같은 TotlCycle에 2개 행 존재
- 1 가속수명 루프 = Mode 5~9 = **5 TotlCycle 단계**
- 루프 N번째 → TotlCycle 범위 = (기준 오프셋 + 5N-4) ~ (기준 오프셋 + 5N)

### 3.3 BDT 논리 사이클 변환 (toyo_cycle_data)

```
CAPACITY.LOG 행들
    ↓
조건별 그룹핑:
  - 방전(Condition==2)을 기준으로 사이클 묶음 생성
  - Mode 5+6+7+8의 충전 합산 → 1충전 이벤트
  - Mode 8+9의 방전 합산 → 1방전 이벤트
    ↓
논리 사이클 1개 = {총 충전용량, 총 방전용량, ...}
    ↓
df.NewData: Cycle 컬럼 = range(1, N+1) [재인덱싱]
OriCyc = Mode 9 스텝의 TotlCycle (= 5N+4 for 루프 N)
```

**예:**
- 논리 사이클 1 → OriCyc = 9 (Mode 9의 TotlCycle)
- 논리 사이클 2 → OriCyc = 14
- 논리 사이클 N → OriCyc = 5N + 4

---

## 4. PNE 측 분석

### 4.1 패턴파일 구조 (.sch 추론)

PNE `.sch` 파일은 바이너리이므로 SaveEndData.csv의 `StepNum`(col[7]) 패턴으로 역추론한다.

**핵심 차이**: PTN은 RPT와 가속수명을 같은 루프 안에 정의하지만,  
PNE `.sch`는 **RPT와 가속수명을 별도 블록(StepNum 범위)으로 분리**한다.

| StepNum 범위 | 반복 횟수 | TotlCycle 범위 | 역할 |
|-------------|---------|---------------|------|
| 2–4   | 1회  | 1         | RPT 초기 방전 (CC 0.2C → 3.0V) |
| 6–10  | 1회  | 2         | RPT 충·방전 (CCCV 1C + CC 1C) |
| 12–20 | 98회 | 3 ~ 100   | 가속수명 루프 블록 1 |
| 22–26 | 1회  | 101       | 100주기 RPT |
| 28–36 | 99회 | 102 ~ 200 | 가속수명 루프 블록 2 |
| 38–42 | 1회  | 201       | 200주기 RPT |
| 44–52 | 99회 | 202 ~ 300 | 가속수명 루프 블록 3 |
| 54–58 | 1회  | 301       | 300주기 RPT |
| 60–68 | 297회| 302 ~ 598 | 가속수명 루프 블록 4 |
| …     | …    | …         | … (이후 동일 패턴) |

**가속수명 1 루프(예: StepNum 12–20)의 내부 구조:**

| StepNum | StepType | 충전/방전 모드 | 끝 전압 | 역할 |
|---------|----------|-------------|--------|------|
| 12 | Chg | CC 2C     | 4.14V | 1단계 충전 |
| 13 | Chg | CC 1.65C  | 4.16V | 2단계 충전 |
| 14 | Chg | CCCV 1.4C/4.3V | — | 3단계 충전 |
| 15 | Chg | CCCV 1C/4.55V  | — | 4단계 충전 (완충) |
| 16 | Rest| —         | —    | 휴지 |
| 17 | Dchg| CC 1C    | 3.65V | 1단계 방전 |
| 18 | Dchg| CC 0.5C  | 3.0V  | 2단계 방전 (완방) |
| 19 | Rest| —         | —    | 휴지 |
| 20 | Loop| —         | —    | 루프 마커 (종점) |

### 4.2 Raw Data 구조 (SaveEndData.csv)

PNE 충방전기는 **루프 실행이 완료될 때마다** 해당 루프의 모든 스텝 정보를 SaveEndData에 기록한다.

| 컬럼 인덱스 | 컬럼명 | 의미 |
|------------|--------|------|
| col[2]  | StepType | 1=충전, 2=방전, 3=휴지, 8=루프마커 |
| col[6]  | EndState | 65=전압종료(CC), 66=전류종료(CCCV), 64=시간종료 |
| col[7]  | StepNum  | .sch 파일 내 스텝 번호 |
| col[10] | ChgCap   | 충전 용량 (μAh) |
| col[11] | DchgCap  | 방전 용량 (μAh) |
| col[27] | TotlCycle| **루프 실행 카운터** (루프 1회 완료 → +1) |

**실데이터 예시 (TotlCycle 1~3):**

| TotlCycle | StepNum | StepType | DchgCap (mAh) | ChgCap (mAh) | 설명 |
|-----------|---------|----------|--------------|--------------|------|
| 1  | 2  | Dchg | 626.6  | —      | RPT 초기 방전 |
| 1  | 3  | Rest | —      | —      | |
| 1  | 4  | Loop | (누적) | (누적) | 루프 마커 |
| 2  | 6  | Chg  | —      | 2311.7 | RPT 충전 |
| 2  | 7  | Rest | —      | —      | |
| 2  | 8  | Dchg | 2372.9 | —      | RPT 방전 |
| 2  | 9  | Rest | —      | —      | |
| 2  | 10 | Loop | (누적) | (누적) | 루프 마커 |
| 3  | 12 | Chg  | —      | 773.6  | 가속수명 1주기: 2C 충전 |
| 3  | 13 | Chg  | —      | 215.5  | 1.65C 충전 |
| 3  | 14 | Chg  | —      | 566.9  | CCCV 1.4C 충전 |
| 3  | 15 | Chg  | —      | 781.2  | CCCV 1C 충전 (완충) |
| 3  | 16 | Rest | —      | —      | |
| 3  | 17 | Dchg | 1390.3 | —      | CC 1C 방전 (3.65V) |
| 3  | 18 | Dchg | 851.2  | —      | CC 0.5C 방전 (3.0V) |
| 3  | 19 | Rest | —      | —      | |
| 3  | 20 | Loop | (누적) | (누적) | 루프 마커 |

### 4.3 BDT 논리 사이클 변환 (pne_cycle_data)

```
SaveEndData.csv
    ↓
pivot_table(index="TotlCycle", aggfunc="sum")
  - TotlCycle별 ChgCap 합산 (모든 Chg 스텝 합)
  - TotlCycle별 DchgCap 합산 (모든 Dchg 스텝 합)
    ↓
논리 사이클 1개 = TotlCycle 1개 (이미 루프 단위로 집계됨)
    ↓
df.NewData: Cycle 컬럼 = range(1, N+1) [재인덱싱]
OriCyc = TotlCycle 그 자체 (별도 변환 불필요)
```

**예:**
- 논리 사이클 1 → OriCyc = 1 (TotlCycle=1, RPT 초기 방전)
- 논리 사이클 2 → OriCyc = 2 (TotlCycle=2, RPT 충·방전)
- 논리 사이클 3 → OriCyc = 3 (TotlCycle=3, 가속수명 1주기)

---

## 5. 핵심 비교 요약

### 5.1 TotlCycle의 의미 차이

| 항목 | Toyo (CAPACITY.LOG) | PNE (SaveEndData.csv) |
|------|--------------------|-----------------------|
| **단위** | 스텝 실행 1회 = +1 | 루프 실행 1회 = +1 |
| **1 가속수명 사이클** | TotlCycle 5개 (Mode 5~9) | TotlCycle 1개 |
| **TotlCycle 증가 속도** | 빠름 (스텝당) | 느림 (루프당) |
| **RPT 포함 방식** | 같은 루프 내 Mode 1~4, 10~11 | 별도 블록 (다른 StepNum 범위) |
| **OriCyc 계산** | Mode 9의 TotlCycle (= 5N+4) | TotlCycle 그 자체 |

### 5.2 패턴파일 레벨 비교

| 항목 | Toyo PTN | PNE .sch |
|------|---------|---------|
| **파일 형식** | 고정폭 텍스트 | 바이너리 |
| **RPT 위치** | 루프 외부 (Mode 1~4, 10~11) | 별도 스텝 블록 (StepNum이 다름) |
| **가속수명 루프** | Mode 5~9 단일 루프, 반복 9801회 | 100주기 단위 블록, 블록마다 별도 루프 |
| **충전 단계** | Mode 5~8 (4단계 충전을 4개 스텝으로 분리) | StepNum 12~15 (4단계 충전) |
| **방전 단계** | Mode 8 1C 방전 + Mode 9 0.5C 방전 (2단계) | StepNum 17 + 18 (2단계 방전) |
| **충전 총량** | Mode 5~8 ChgCap 합산 (≈ 1689mAh) | StepNum 12~15 ChgCap 합산 (≈ 2335mAh) |
| **방전 총량** | Mode 8 + Mode 9 DchgCap 합산 (≈ 1689mAh) | StepNum 17 + 18 DchgCap 합산 (≈ 2335mAh) |

### 5.3 BDT plot Cycle과 각 원시 데이터의 관계

```
BDT plot의 Cycle 번호  ≠  PTN Mode 번호
BDT plot의 Cycle 번호  ≠  CAPACITY.LOG TotlCycle
BDT plot의 Cycle 번호  ≠  SaveEndData TotlCycle  (≈ 비슷하지만 RPT 포함 여부 다름)
```

| | Toyo 예시 | PNE 예시 |
|---|---|---|
| **CAPACITY.LOG/SaveEndData TotlCycle 1** | RPT Mode 1 방전 스텝 | RPT 초기 방전 루프 |
| **CAPACITY.LOG TotlCycle 5~9** | 가속수명 Loop 1의 5 스텝 | — |
| **SaveEndData TotlCycle 3** | — | 가속수명 Loop 1 (9 스텝 포함) |
| **BDT plot Cycle 1** | 가속수명 루프 1회 (TotlCycle 5~9 합산) | TotlCycle=1 (RPT 초기 방전) |
| **BDT OriCyc 1** | TotlCycle=9 (Mode 9의 TotlCycle) | TotlCycle=1 |

> **결론**: BDT Cycle은 "충방전 1세트(충전+방전)"를 1로 카운트하는 논리 사이클이다.  
> Toyo는 복잡한 그룹핑 로직으로 5 TotlCycle → 1 논리 사이클로 변환하고,  
> PNE는 TotlCycle이 이미 루프 단위이므로 1 TotlCycle → 1 논리 사이클로 직접 대응된다.

---

## 6. RPT 구별 문제

### 6.1 RPT vs 가속수명 사이클 구별

BDT plot에서 Cycle 1은:
- Toyo: 첫 번째 가속수명 루프 (RPT 제외, TotlCycle 5~9)
- PNE: TotlCycle=1 (RPT 초기 방전 포함!)

PNE의 경우 RPT(TotlCycle 1, 2, 101, 201, ...)가 가속수명과 **동일한 방식으로 df.NewData에 포함**된다. RPT에서의 방전용량은 더 크거나 다른 C-rate이므로 Dchg 비율이 가속수명 사이클과 다르게 나타난다.

PNE의 `classify_pne_cycles()` 함수가 이를 구별하는 기준은 `n_chg >= 2 and n_dchg >= 1` 패턴이다:
- RPT (TotlCycle 2, 101, ...): `n_chg=1, n_dchg=1` → 가속수명 아님으로 분류
- 가속수명 (TotlCycle 3~100, ...): `n_chg=4, n_dchg=2` → 가속수명으로 분류

### 6.2 Toyo에서의 RPT 포함 여부

Toyo CAPACITY.LOG의 Mode 1~4 (RPT)와 Mode 10~11 (후처리 RPT)는 가속수명 루프와 별도로 존재한다. `toyo_cycle_data`의 그룹핑 로직이 이를 어떻게 처리하느냐에 따라 BDT plot에 RPT가 포함될 수도, 제외될 수도 있다.

---

## 7. 충전 방식 비교 (둘 다 다단계 충전)

| 단계 | Toyo (Q7M, 1689mAh) | PNE (Q8, 2335mAh) |
|------|--------------------|--------------------|
| 1단계 | CC 2C = 3378mA | CC 2C = 4670mA |
| 2단계 | CC 1.65C = 2787mA | CC 1.65C = 3853mA |
| 3단계 | CCCV 1.4C/4.3V | CCCV 1.4C/4.3V |
| 4단계 | CCCV 1C/4.5V | CCCV 1C/4.55V |
| 방전 1 | CC 1C → 3.6V | CC 1C → 3.65V |
| 방전 2 | CC 0.5C → 3.2V | CC 0.5C → 3.0V |

두 패턴은 본질적으로 동일한 충방전 전략(다단계 CC → CCCV, 2단계 방전)이지만,  
Toyo는 이를 **5개 스텝 / 1루프**로, PNE는 **9개 스텝 / 1루프**로 구현한다.

---

---

## 8. 추가 시험 유형별 TotlCycle 구조 분석 (PNE)

아래는 가속수명 외 다양한 시험 유형의 SaveEndData 구조 분석이다.  
모든 PNE 채널은 `col[27] = TotlCycle` (루프 카운터)를 공통으로 사용하며,  
`.sch` 파일에서 루프 블록 구성이 달라질 뿐 기본 원리는 동일하다.

---

### 8.1 GITT 하프셀 (③ Cathode 4.187mAh, ④ Anode 4.376mAh)

**시험 개요**: SDI 반쪽 셀(half-cell, Li 금속 상대전극)에서 GITT(Galvanostatic Intermittent Titration Technique) 수행.  
0.1C 펄스 방전 6분 → 휴지 1시간 패턴을 SOC 0%가 될 때까지 반복.

**Cathode half-cell SaveEndData 구조:**

| TotlCycle | StepNum 시퀀스 | StepType | 용량 | 역할 |
|-----------|-------------|---------|------|------|
| 1 | 2→3→4(L) | Chg→Rest→Loop | Chg 3807mAh | 초기 완충 (CC 0.1C → 4.6V) |
| 2~91 | 6→7→8(L) | Dchg→Rest→Loop | Dchg ≈ 42μAh/펄스 | GITT 방전 펄스 × 89회 |
| 92~100 | 10→11→12(L) | … | … | 방전 구역 전환 |
| 101~170 | 6→7→8(L) or 14→15→16(L) | … | … | GITT 계속 |
| 180 | 14→15→16(L) | Chg→Rest→Loop | Chg ≈ 42μAh | 역방향 GITT 충전 펄스 |
| 181 | 14 (미완) | Chg | Chg 42μAh | 진행 중 종료 |

**핵심 특징:**
- **1 TotlCycle = 1 GITT 펄스 + 1 휴지** (약 66분)
- Cathode: 완충 후 펄스 방전 → TotlCycle 1 = 초기 충전, TC 2~ = 방전 펄스
- Anode: 완방 후 펄스 충전 → TotlCycle 1 = 초기 방전, TC 2~ = 충전 펄스
- 총 TotlCycle ≈ 181 (Cathode), 194 (Anode)
- **BDT plot Cycle 번호 = 각 GITT 펄스 번호** (1 = 첫 번째 펄스)
- 코인셀이므로 `is_micro_unit()` 판별로 용량 단위 μAh → mAh 변환 필요

**전압 범위 (물리적 확인):**
- Cathode: 4.6V → 약 2.0V (vs Li/Li⁺)  ← NMC 하프셀 정상 범위
- Anode: 0.01V → 약 1.5V (vs Li/Li⁺) ← Graphite 하프셀 정상 범위

---

### 8.2 DCIR (⑤ Gen5+B 2610mAh, MK Pulse 방식)

**시험 개요**: MK DCIR 프로토콜 — SOC별 RSS + 1s Pulse DCIR 측정.  
각 SOC 포인트에서 짧은 펄스(CC 방전/충전)를 가하고 OCV를 측정.

**SaveEndData TotlCycle 구조:**

| TotlCycle | StepNum 시퀀스 | 역할 | 충방전 합계 |
|-----------|-------------|------|-----------|
| 1 | 2→3(L) | 초기 방전 (CC → 3.0V) | Dchg 1mAh (불완전) |
| 2~4 | 5→6→7→8→9(L) | RPT CCCV 충전 + CC 방전 반복 | Chg ≈ 5040mAh, Dchg ≈ 5040mAh |
| 5 | 11→12→13→14→15(L) | RPT 2 (다른 C-rate?) | Chg 5134mAh, Dchg 5425mAh |
| 6~13 | 17→18→19→20→21→22→23→24→25→26→27→28→29→30(L) | SOC별 DCIR 측정 루프 | Chg ≈ 76mAh, Dchg ≈ 25mAh/TC |
| 14~… | 32~105(L) | SOC별 DCIR 2차 측정 | Chg ≈ 11mAh, Dchg ≈ 18mAh/TC |

**핵심 특징:**
- **1 TotlCycle = 1 SOC 포인트의 측정 완료** (CC 방전 + CC 충전 + 휴지)
- TotlCycle 6~13 / 14~: SOC 100%→0%를 8단계로 나눠 측정
- BDT `_process_pne_cycleraw`에서 `mkdcir=True`일 때 처리
  - `EndState==78` (SOC 종료): RSS CCV 기준 스텝 선별
  - `steptime==100 (1s)`: Pulse DCIR 기준 스텝 선별
- **BDT plot Cycle = 각 SOC 포인트 번호** (의미 있는 시퀀스)
- dcir, dcir2, soc70_dcir 컬럼 계산에 사용

---

### 8.3 보관 용량 측정 (⑥ Gen5P 5000mAh, 4cycle SOC30)

**시험 개요**: 보관 후 용량 확인 시험. SOC 30% 설정 전 0.2C 충방전 4회 반복.

**SaveEndData TotlCycle 구조:**

| TotlCycle | StepNum 시퀀스 | 역할 | 충방전 합계 |
|-----------|-------------|------|-----------|
| 1 | 2→3→4(L) | 초기 방전 (CC → 3.0V) | Dchg 1223mAh |
| 2~5 | 6→7→8→9→10(L) | CCCV 충전 + CC 방전 4회 반복 | Chg ≈ 5065mAh, Dchg ≈ 5060mAh |
| 6 | 12→13→14(L) | SOC 30% 충전 후 대기 | Chg 1519mAh (SOC 종료) |

**핵심 특징:**
- **1 TotlCycle = 1 충방전 사이클** (완충 → 완방 → 휴지)
- TotlCycle 1 = 초기 방전 전처리 (공칭용량의 약 24%만 방전 → 보관 상태)
- TotlCycle 2~5 = 실제 용량 측정 사이클 4회
- TotlCycle 6 = SOC 30% 세팅 (시험 종료 조건)
- **BDT plot Cycle 1~6** = 총 6포인트 (실질적으로는 TC 2~5가 유효 데이터)
- 보관 기간 중 용량 회복 트렌드가 TC 2→5에서 관찰 가능

---

### 8.4 율별 용량 (⑦ 5075mAh Hybrid, ⑧ 4900mAh 율별)

**시험 개요**: C-rate별 충방전 용량 측정 (0.2C, 0.5C, 1C, 2C, 3C 등).  
각 C-rate마다 별도 StepNum 블록을 사용.

**5075mAh (Hybrid 포함) SaveEndData TotlCycle 구조:**

| TotlCycle | StepNum 시퀀스 | 역할 | 충방전 합계 |
|-----------|-------------|------|-----------|
| 1 | 2→3→4(L) | 초기 방전 | Dchg 4224mAh |
| 2 | 6→7→8→9→10(L) | 0.2C 충전 + 0.2C 방전 | Chg 10662mAh, Dchg 10519mAh |
| 3 | 12→13→14→15→16(L) | 0.5C 충전 + 0.5C 방전 | Chg 10550mAh, Dchg 10735mAh |
| 4 | 18→19→20→21→22(L) | 1C 충전 + 1C 방전 | Chg 10759mAh, Dchg 10876mAh |
| 5 | 24→25→26→27→28(L) | 2C 충전 + 2C 방전 | Chg 10908mAh, Dchg 10553mAh |
| 6 | 30→31→32→33→34(L) | 3C 충전 + 3C 방전 | Chg 10574mAh, Dchg 10214mAh |
| … | … | … | … |
| 22~23 | 136→137→138→139→140→141→142→143→144(L) | **Hybrid 다단계 충전** (4 Chg + 2 Dchg) | ≈ 9408mAh |

> **용량이 ≈ 2×정격**인 이유: 이 셀은 2P(병렬 2셀)로 구성되어 있어 실제 측정 용량 = 2 × 단셀 용량

**핵심 특징:**
- **1 TotlCycle = 1 C-rate 조건** (충전 1회 + 방전 1회)
- 각 TotlCycle마다 완전히 다른 StepNum 블록 사용 (C-rate마다 블록 분리)
- TotlCycle 22~23: StepNum이 달라지며 Hybrid(다단계) 패턴으로 전환
  - 4개 Chg 스텝 + 2개 Dchg 스텝 → 가속수명과 동일 구조!
- **BDT plot Cycle = 각 C-rate 조건 번호** (1=초기방전, 2=0.2C, 3=0.5C, ...)
- 용량 비교 시 각 Cycle이 다른 C-rate임을 반드시 인식해야 함

**4900mAh (단순 율별) SaveEndData:**
- 동일한 구조. TotlCycle 1~15, 각 C-rate별 블록.

---

### 8.5 연속저장 DCIR (⑨ PA1 3885mAh, M01Ch018)

**시험 개요**: 연속저장 조건에서 주기적 DCIR 측정.  
M01Ch015는 SaveEndData 비어있음(버그 케이스, 회귀 테스트 대상).

**M01Ch018 SaveEndData TotlCycle 구조:**

| TotlCycle | StepNum 시퀀스 | 역할 | 충방전 합계 |
|-----------|-------------|------|-----------|
| 1 | 2→3→4(L) | 초기 방전 (CC → ?) | Dchg 4605mAh |
| 2 | 6→7→8→9→10(L) | RPT 충방전 | Chg 7798mAh, Dchg 7769mAh |
| 3 | 12→13(L) | 짧은 방전 루프 | Dchg 117mAh |
| 4 | 15→16→17(L) | 충전 (보관 SOC 설정) | Chg 7698mAh |
| 5~13 | 19→20→21→22→23→24→25→26(L) | **DCIR 측정 루프** (R→D×4→C→D→L) | Chg ≈ 9mAh, Dchg ≈ 778mAh/TC |
| 14~17 | 28→29→30→31→32→33→34→35(L) | 2차 DCIR 측정 루프 | Chg ≈ 9mAh, Dchg ≈ 201mAh/TC |
| 18 | 28→34 (미완) | 진행 중 종료 | — |
| 19 | 37→38→39→40→41→42(L) | 3차 DCIR? | — |

**DCIR 루프 내부 구조 분석 (TC=5~13):**
```
Step 19: Rest (보관 SOC 유지 대기)
Step 20: Dchg (10% SOC 방전 펄스)
Step 21: Dchg (20% SOC 방전 펄스)
Step 22: Dchg (30% SOC 방전 펄스)
Step 23: Dchg (40% SOC 방전 펄스)
Step 24: Chg  (일부 충전 복구)
Step 25: Dchg (DCIR 측정용 추가 방전)
Step 26: Loop (종점)
```

**핵심 특징:**
- **1 TotlCycle = 1회 보관 + 1회 DCIR 측정** (수일 단위)
- TC 3, 4는 SOC 세팅용 준비 단계 (단일 충전 또는 방전)
- TC 5~13: 동일 StepNum 반복 → 동일 보관 조건에서 주기적 측정
- StepNum 블록이 다음 단계(TC 14~)로 전환되면 새로운 보관 조건으로 변경
- **M01Ch015 SaveEndData = 0 bytes**: 연속저장 중 파일 저장 미완료 상태 → BDT 예외처리 필요 (회귀 버그)
- `pne_continue_data()` 함수가 이 케이스를 처리: Restore/SaveData*.csv에서 직접 로딩

---

## 9. 시험 유형별 BDT 사이클 의미 요약표

| 시험 유형 | 대표 데이터 | TotlCycle 의미 | BDT Cycle 의미 | OriCyc |
|----------|-----------|--------------|--------------|--------|
| **가속수명 (PNE)** | Q8 2335mAh | 1 루프 (Chg×4 + Dchg×2) | 충방전 1회 | TotlCycle |
| **가속수명 (Toyo)** | Q7M 1689mAh | 1 스텝 실행 | 충방전 1회 (5 TC → 1 논리 사이클) | Mode 9의 TotlCycle |
| **GITT 하프셀** | SDI 4.187mAh | 1 펄스 + 1 휴지 | 펄스 번호 (SOC 이력) | TotlCycle |
| **DCIR (MK)** | 2610mAh | 1 SOC 포인트 측정 완료 | SOC 포인트 순서 | TotlCycle |
| **보관 용량 측정** | 5000mAh | 1 충방전 사이클 | 사이클 번호 | TotlCycle |
| **율별 용량** | 5075mAh, 4900mAh | 1 C-rate 조건 완료 | C-rate 조건 번호 | TotlCycle |
| **연속저장 DCIR** | 3885mAh | 1회 보관 + 1회 측정 | 측정 회차 | TotlCycle |

> **공통 원칙**: PNE SaveEndData의 TotlCycle은 항상 **루프 단위**이다.  
> `.sch` 파일에서 하나의 루프가 무엇을 포함하느냐에 따라 BDT Cycle의 의미가 달라진다.  
> Toyo는 스텝 단위 카운터이므로 BDT가 추가 그룹핑을 수행해야 한다.

---

## 10. 참조 코드 위치

| 함수 | 파일 | 라인 | 역할 |
|------|------|------|------|
| `toyo_cycle_data()` | proto_.py | ~1141 | Toyo CAPACITY.LOG → df.NewData |
| `pne_cycle_data()` | proto_.py | ~3839 | PNE SaveEndData → df.NewData |
| `_process_pne_cycleraw()` | proto_.py | ~3473 | PNE pivot → NewData 변환 핵심 |
| `classify_pne_cycles()` | proto_.py | ~1558 | PNE TotlCycle → RPT/가속수명 분류 |
| `classify_toyo_cycles()` | proto_.py | — | Toyo TotlCycle → 사이클 분류 |
| `analyze_accel_pattern()` | proto_.py | ~2332 | 가속수명 패턴 분석 (PNE/Toyo 공통) |
| `pne_continue_data()` | proto_.py | ~3110 | 연속저장 채널 프로파일 로딩 |
| `_cached_pne_restore_files()` | proto_.py | ~503 | SaveEndData 캐싱 (빈 파일 예외처리 포함) |
| `is_micro_unit()` | proto_.py | — | 코인셀(μAh 단위) 판별 → GITT 하프셀에 적용 |
