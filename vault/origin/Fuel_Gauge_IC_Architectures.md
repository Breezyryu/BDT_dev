# 배터리 Fuel Gauge IC 기술 분석 종합 보고서

**작성일:** 2026년 2월 3일  
**주제:** Battery Fuel Gauge IC 아키텍처 비교 및 컴포넌트 동작 원리 분석  
**대상 회로:** 1ADC (VM Only), 1ADC (VM+CC), 2ADC (VM+CC)

---

## 1. 개요 (Executive Summary)

본 보고서는 리튬 이온 배터리의 잔량(SOC: State of Charge)을 측정하는 Fuel Gauge IC의 세 가지 기술 방식을 분석한다.
배터리 관리 시스템(BMS)의 핵심인 Fuel Gauge는 전압(Voltage), 전류(Current), 온도(Temperature) 정보를 수집하여 배터리 상태를 추정한다. 본 문서는 각 방식의 **하드웨어 구조**, **공학적 동작 원리**, 그리고 각 부품의 **역할 비유**를 통해 기술적 특징을 명확히 정의한다.

---

## 2. 아키텍처별 기술 분석 (Architecture Analysis)

![Fuel Gauge Circuit Architectures](uploaded_media_1770090406692.jpg)
> **그림 1:** Fuel Gauge IC 아키텍처 비교 (좌상: Type A, 좌하: Type B, 우: Type C)

### 2.1 Type A: 1ADC (VM Only) - 전압 모드 전용

**[특징]** 전류 센싱 저항(Sense Resistor) 없이 배터리 전압만을 측정하는 가장 단순한 구조.

* **동작 원리:** 배터리의 OCV(Open Circuit Voltage) 특성 곡선을 이용하여 전압을 SOC로 변환.
* **한계:** 부하 전류에 의한 전압 강하(IR Drop)를 실시간 보정하기 어려워 동적 상태에서의 오차가 큼.

| 컴포넌트 | 공학적 기능 (Engineering Spec) | 비유적 역할 (Metaphor) |
| :--- | :--- | :--- |
| **VBATFG** | IC 구동 전원이자 측정 입력. IR Drop 보정 불가. | **[밥이자 눈]** 식량(전원)이자 유일한 관측 수단. |
| **BGR** | 온도/전압 무관 1.25V 정밀 기준 전압 생성. | **[절대 자]** 변하지 않는 측정의 기준 눈금. |
| **OSC** | 시스템 클럭 및 샘플링 주파수 생성. | **[심장 박동]** 칩을 움직이는 규칙적인 리듬. |
| **ADC** | $\Sigma\Delta$ 방식의 아날로그-디지털 변환기. | **[번역가]** 전압을 디지털 언어로 통역. |
| **Algo** | OCV 테이블 기반 SOC 추정 엔진. | **[지도 보는 항해사]** 지도(OCV)만 보고 위치 파악. |
| **ALRTB** | 저전압 등 이벤트 발생 시 인터럽트 출력(Active Low). | **[비상벨]** 문제 발생 시 울리는 경보. |

**[동작 흐름 (Operation Flow)]**
1. **Power On**: IC가 켜지면 `BGR`이 기준 전압 생성 및 `OSC` 발진 시작.
2. **Voltage Sensing**: `VBATFG` 핀으로 배터리 전압 입력.
3. **ADC Conversion**: 전압을 `Modulator` $\rightarrow$ `Digital Block` 순서로 디지털 변환.
4. **Estimation**: `Algo`가 OCV 테이블(전압-용량 지도)을 참조하여 SOC(%) 추정.
5. **Update**: 결과값을 레지스터에 업데이트하고 다음 주기까지 대기.

### 2.2 Type B: 1ADC (VM+CC) - 시분할 하이브리드

**[특징]** MUX(Multiplexer)를 사용하여 하나의 ADC로 전압과 전류를 번갈아 측정하는 표준형 구조.

* **동작 원리:** 시분할(Time-sharing) 방식을 통해 전압 측정과 전류 적산(Coulomb Counting)을 수행.
* **장점:** 전압법의 장기 안정성과 전류 적산법의 단기 정밀도를 결합. 비용 대비 성능 우수.

| 컴포넌트 | 공학적 기능 (Engineering Spec) | 비유적 역할 (Metaphor) |
| :--- | :--- | :--- |
| **Sense R** | 전류를 전압차($V=IR$)로 변환하는 션트 저항. | **[톨게이트]** 전류 통행량을 측정하는 관문. |
| **MUX** | 다채널 입력을 ADC로 순차 연결하는 스위치. | **[교통경찰]** 신호를 정리해 순서대로 보냄. |
| **Modulator** | 입력 신호를 고속 1-bit 스트림으로 변환 (Oversampling). | **[고속 연사 카메라]** 찰나를 연속 촬영하여 점으로 기록. |
| **Digital Block** | 데시메이션 필터를 통해 노이즈 제거 및 PCM 변환. | **[사진 현상소]** 점들을 모아 선명한 사진(숫자) 완성. |
| **FG Logic** | 측정 시퀀스 제어 및 MUX 스위칭 관리. | **[현장 감독]** 작업 순서를 지시하는 관리자. |
| **VDDNTC** | NTC 온도 센서용 저잡음 전용 전원. | **[청정수 공급]** 온도계용 깨끗한 전원. |

**[동작 흐름 (Operation Flow)]**
1. **Sequence Start**: `Control Logic`이 측정 스케줄 시작.
2. **MUX Switching (Voltage)**: `VBC`(전압) 채널 선택 $\rightarrow$ ADC 변환 $\rightarrow$ 전압 데이터 저장.
3. **MUX Switching (Current)**: `VCCT`(전류) 채널 선택 $\rightarrow$ ADC 변환 $\rightarrow$ 전류 데이터 저장.
4. **Hybrid Calculation**: `Algo`가 "현재 전압"과 "누적 전류량"을 융합하여 SOC 오차 보정.
5. **Loop**: 위 과정을 고속으로 반복(Time-Sharing)하며 실시간 상태 추적.

### 2.3 Type C: 2ADC (VM+CC) - 듀얼 코어 고성능

**[특징]** 전류(IADC)와 전압(VADC)을 측정하는 ADC가 물리적으로 분리된 최고급형 구조.

* **동작 원리:** 전류는 상시(Always-on) 적산하고, 전압은 주기적으로 스캔하여 시간차 없는 완전 동기화 측정 수행.
* **장점:** 급격한 부하 변동에도 전류 누락이 없으며, 하드웨어 가속기(RTL)를 통해 고속 연산 처리.

| 컴포넌트 | 공학적 기능 (Engineering Spec) | 비유적 역할 (Metaphor) |
| :--- | :--- | :--- |
| **IADC** | 전류 센싱 전용 ADC. 상시 동작하며 전류 변화 포착. | **[동체 시력 전담 눈]** 움직임(전류)만 쫓는 눈. |
| **VADC** | 전압/온도 측정용 ADC. MUX를 통해 순차 측정. | **[풍경 감상 전담 눈]** 배경(전압)을 보는 눈. |
| **RTL** | 전류 적산 및 전력 계산을 수행하는 하드웨어 가속기. | **[암산왕 (주판)]** 받아 적지 않고 머리로 바로 계산. |
| **FG Algo** | RTL 데이터와 VADC 데이터를 융합하여 최종 판단. | **[노련한 선장]** 모든 정보를 종합해 위치 결정. |
| **IRQB** | AP에 상태(완충, 에러)를 알리는 인터럽트 신호. | **[초인종]** 주인(AP)을 호출하는 벨. |
| **BATID** | 배터리 ID 저항을 읽어 용량/모델 식별. | **[신분증 리더기]** 배터리 정품/모델 확인. |

**[동작 흐름 (Operation Flow)]**
* **Path 1 (Current - 상시 가동)**: `Sense R` 감지 $\rightarrow$ `IADC` $\rightarrow$ `RTL`에서 실시간 적산(Coulomb Counting) $\rightarrow$ 누적 전하량 결과 생성.
* **Path 2 (Voltage - 주기적)**: `Battery`/`NTC` $\rightarrow$ `MUX` $\rightarrow$ `VADC` $\rightarrow$ 전압/온도 데이터 생성.
* **Final Integration**: `Algo`가 RTL의 '적산값'과 VADC의 '전압/온도'를 취합하여 최종 정밀 SOC 결정 $\rightarrow$ 필요 시 AP 인터럽트(`IRQB`) 발생.

---

## 3. 핵심 동작 메커니즘 심층 분석

### 3.1 ADC 시스템: 카메라와 현상소

Fuel Gauge의 ADC는 단순한 측정기가 아니라 **$\Sigma\Delta$ (델타-시그마)** 방식을 사용합니다.

* **Modulator (카메라):** 아날로그 신호를 엄청나게 빠른 속도로 찍어 '0'과 '1'의 밀도(Density)로 표현합니다.
* **Digital Block (현상소):** 이 거친 데이터를 필터링(Decimation)하여 우리가 아는 '3.8V', '500mA' 같은 매끄러운 숫자로 만들어냅니다.

### 3.2 전류 측정: 톨게이트 (Sense R)

전자는 눈에 보이지 않으므로, **Sense Resistor(저항)**라는 좁은 문을 통과시킵니다.

* 전류가 지나가려고 아우성칠 때 생기는 압력(전압) 차이를 측정하여 통행량(전류량)을 계산합니다.
* 이때 **CSP/CSN** 핀은 톨게이트 입구와 출구에 달린 **CCTV** 역할을 하여 압력 차이를 정밀하게 읽어냅니다.

### 3.3 두뇌의 분업: RTL vs Algorithm (2ADC 모델)

고성능 모델에서는 단순 계산과 고차원 판단을 분리합니다.

* **RTL (일개미/계산기):** "지난 1초 동안 0.1mA가 1000번 들어왔으니 총 100이다"라는 단순 더하기(적산)를 쉼 없이 수행합니다.
* **Algorithm (선장/지휘관):** RTL이 보고한 값에 온도 보정, 노화 보정 등을 적용하여 "그러므로 현재 배터리는 85% 남았다"는 최종 결정을 내립니다.

---

## 4. 회로도 기반 하드웨어 및 신호 분석 (Circuit Diagram Deep Dive)

제공된 회로도 이미지(그림 1)에 묘사된 실제 하드웨어 연결 및 블록 다이어그램의 특징에 대한 상세 분석입니다.

### 4.1 주변 회로 설계 (Application Circuit)
* **NTC 온도 센서 회로 (Type B, C)**
  * 회로도에 `100kohm` 저항이 `NTC` 핀과 직렬로 연결된 것이 확인됩니다.
  * **설계 원리**: `VDDNTC`에서 공급된 전압이 고정 저항(100kΩ)과 NTC 서미스터(온도에 가변) 사이에서 **전압 분배(Voltage Divider)** 됩니다. ADC는 이 중간 전압(`VTCP` or `NTC` node)을 측정하여 저항 비를 계산하고 온도를 역산합니다.
* **ALRTB 풀업 저항 (Type A, C)**
  * `ALRTB` 핀 외부에 전원 방향(↑)으로 연결된 저항이 보입니다.
  * **설계 원리**: 이 핀은 **Open-Drain** 구조입니다. 평소 High 상태를 유지하기 위해서는 반드시 외부 **풀업(Pull-up) 저항**을 달아야 하며, 내부 FET가 켜질 때만 Ground로 연결되어 Low 신호를 만듭니다.
* **배터리 ID 저항 (Type B, C)**
  * 배터리 팩 내부(점선 박스 안)에 추가 저항이 있고, `BATID` 핀이 이를 측정합니다.
  * BMS가 배터리 팩의 용량이나 제조사 정보를 아날로그 저항값으로 식별(ID Checking)하는 기능을 하드웨어적으로 지원함을 알 수 있습니다.

### 4.2 내부 블록 연결 특징
* **ADC IP 블록의 IP화 (Type B)**
  * `Reference`, `Delta-Sigma Modulator`, `ADC Digital Block`이 하나의 거대한 `ADC IP` 박스로 묶여 있습니다.
  * 이는 반도체 설계 관점에서 **재사용 가능한 IP(Intellectual Property)**로 설계되었음을 의미합니다. 즉, 이 ADC 블록은 다른 칩에서도 그대로 복사해서 쓸 수 있는 독립적인 모듈입니다.
* **RTL과 알고리즘의 직접 연결 (Type C)**
  * `RTL for calculation` 블록이 `IADC`, `VADC`와 직접 양방향 화살표($\leftrightarrow$)로 연결되어 있습니다.
  * 이는 CPU(Algo)의 개입 없이 하드웨어가 독자적으로 ADC 데이터를 읽어오고 적산을 수행(Direct Memory Access 유사)함을 시각적으로 보여줍니다.

### 4.3 통신 인터페이스 확장성 (I3C)
* **Type A 회로도** 좌측 하단을 보면 `SCL`, `SDA` 외에 **`I3C`** 라인이 별도로 명시되어 있습니다.
* **기술적 함의**: 이 칩은 기존 I2C뿐만 아니라, 더 빠른 속도와 In-Band Interrupt를 지원하는 차세대 **MIPI I3C** 규격을 지원하거나 호환성을 고려하여 설계되었음을 나타냅니다.

---

## 5. 용어 및 약어 사전 (Glossary)

* **FG (Fuel Gauge):** 배터리 잔량 측정 IC.
* **VM (Voltage Mode):** 전압 기반 측정 방식.
* **CC (Coulomb Counting):** 전류 적산 기반 측정 방식.
* **BGR (Bandgap Reference):** 온도 무관 기준 전압원.
* **OSC (Oscillator):** 내부 클럭 발생기.
* **NTC:** 온도에 따라 저항이 변하는 센서 (Negative Temperature Coefficient).
* **VDDNTC:** NTC 구동을 위한 전용 전원.
* **ALRTB / IRQB:** AP를 호출하는 인터럽트 신호 (Active Low).
* **CSP / CSN:** 전류 측정 핀 (Current Sense Positive / Negative).

---

## 6. 결론 (Conclusion)

분석 결과, 애플리케이션의 목적에 따라 적합한 아키텍처가 명확히 구분됩니다.

1. **1ADC (VM Only):** 저가형 IoT 기기 등 **비용 절감**이 최우선인 경우 적합.
2. **1ADC (VM+CC):** 스마트폰, 태블릿 등 **성능과 비용의 균형**이 필요한 범용 기기의 표준 솔루션.
3. **2ADC (Dual Core):** 고속 충전, 대용량 배터리, 전기차 등 **최상의 정밀도와 안전성**이 요구되는 시스템에 필수적임.
