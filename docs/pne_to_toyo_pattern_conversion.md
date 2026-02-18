# PNE → Toyo 패턴 변환 기능 설명서

> **작성일**: 2026-02-15  
> **대상 파일**: `BatteryDataTool_260206_edit copy/BatteryDataTool_optRCD.py` (L15544 ~ L16040)  
> **레퍼런스**: `Rawdata/toyo_1995mAh/PATRN1.1` 외 5개 파일

---

## 1. 개요

PNE 충방전기의 스케줄 파일(`Cycler_Schedule_2000.mdb`)에 저장된 Step 데이터를  
Toyo 충방전기가 인식하는 PATRN 파일 세트로 변환하는 기능이다.

**UI 진입점**: `tab_2`(패턴 탭)의 `ptn_toyo_convert` 버튼 → `ptn_toyo_convert_button()` 호출

---

## 2. PNE와 Toyo 구조 비교

### 2.1 PNE Step 구조 (MDB `Step` 테이블)

| 컬럼 | 설명 |
|---|---|
| `StepType` | 1=충전, 2=방전, 3=휴지, 4=OCV, 5=Impedance, 6=End, 8=Loop, 9=Continuation |
| `Iref` | 기준 전류 (mA) |
| `EndI` | 종지 전류 (mA, 충전 cutoff용) |
| `Vref_Charge` | 충전 전압 (mV) |
| `Vref_DisCharge` | 방전 종지전압 (mV) |
| `EndV` | 종지 전압 대체값 (mV) |
| `Value2` | Loop 대상 스텝 번호 (문자열) |

- 각 Step은 **하나의 동작**(충전 1회, 방전 1회, 휴지 1회 등)을 나타낸다.
- Loop(StepType=8)은 별도 행으로 존재하며 `Value2`에 되돌아갈 스텝 번호, `Iref`에 반복 횟수를 저장한다.

### 2.2 Toyo PATRN 구조

```
[헤더 라인]  265 바이트 (cp949)
[데이터 라인 1]  543 chars = LEFT(261) + RIGHT(272) + LOOP(10)
[데이터 라인 2]  543 chars
...
[데이터 라인 N]  543 chars
```

- Toyo의 1라인 = **서브스텝 2개의 쌍**(LEFT + RIGHT)
- PNE의 Step 1개 = Toyo의 서브스텝 1개에 대응

| 위치 | 길이 | 역할 |
|---|---|---|
| LEFT | 261 chars | **충전** (code `10`) 또는 **휴지** (code `30`) |
| RIGHT | 272 chars | **방전** (code `00`) 또는 **휴지** (code `30`) |
| LOOP | 10 chars | 루프 정보 (대상 라인, 반복 횟수) |

**핵심 제약**: 충전은 반드시 LEFT, 방전은 반드시 RIGHT에 배치된다.

---

## 3. 변환 파이프라인

```
PNE Steps (MDB)
    ↓ ① StepType별 변환
서브스텝 리스트 (charge/discharge/rest/loop)
    ↓ ② Loop 분리·부착
실제 서브스텝 + loop 정보
    ↓ ③ Queue 기반 라인 조립
PATRN 데이터 라인 리스트 + line_types
    ↓ ④ 파일 생성
PATRN{N}.1 외 5개 파일
```

### 3.1 Phase ① — StepType별 서브스텝 변환

| StepType | 변환 결과 | 비고 |
|---|---|---|
| 1 (충전) | `("charge", Iref, V, EndI, is_cccv)` | CC-CV 판단: `EndI/Iref < 0.3` |
| 2 (방전) | `("discharge", Iref, EndV)` | `EndV = Vref_DisCharge / 1000` |
| 3, 4 (휴지/OCV) | `("rest",)` | |
| 5 (Impedance) | `("discharge", Iref, 0)` | 짧은 방전 펄스로 근사 |
| 8 (Loop) | `("loop",)` | `loop_info` 딕셔너리에 (target, count) 저장 |
| 9 (Continuation) | 이전 스텝 타입에 따라 충전/방전 | |
| 6 (End) | 건너뜀 | |

**CC-CV 판단 기준**: 
```
EndI / Iref < 0.3  →  CC-CV (CV cutoff 전류가 낮음 = 만충전)
EndI / Iref ≥ 0.3  →  CC only (단순 전류 제한)
```

### 3.2 Phase ② — Loop 분리·부착

```python
# loop 서브스텝은 제거하고, 바로 앞 실제 서브스텝에 loop 정보 부착
actual_loop_attach[이전_서브스텝_인덱스] = (target_pne_step_1based, count)
```

### 3.3 Phase ③ — Queue 기반 라인 조립 (핵심 로직)

서브스텝들을 **Queue (FIFO)**에 넣고, 하나씩 꺼내며 LEFT-RIGHT 쌍으로 조립한다.

#### 조립 규칙

| Queue에서 꺼낸 sub_a | LEFT 결정 | RIGHT 결정 |
|---|---|---|
| **충전** | `CHG_LEFT(sub_a)` | Queue에서 다음 sub_b pop → RIGHT |
| **방전** | `REST_LEFT` | sub_a 자체를 RIGHT로 이동 |
| **휴지** | `REST_LEFT` | Queue에서 다음 sub_b pop → RIGHT |

#### RIGHT 배치 규칙

| sub_b 타입 | 처리 |
|---|---|
| **방전** | `DCHG_RIGHT(sub_b)` 생성 |
| **충전** | Queue 앞에 되돌림 (push back), `REST_RIGHT` 대체 |
| **휴지** | `REST_RIGHT` 생성 |

#### Interval 규칙

```
LEFT가 REST → RIGHT 방전의 interval = 0 (데이터 기록 안 함)
LEFT가 CHG  → RIGHT 방전의 interval = 60 (60초 간격 기록)
```

#### Loop Target 매핑

라인 조립 과정에서 `pne_to_toyo_line` 딕셔너리를 구축한다:

```python
pne_to_toyo_line = {pne_step_0based: toyo_line_1based}
```

Loop 대상 스텝 번호(PNE 1-based)를 이 매핑으로 변환하여 정확한 Toyo 라인 번호를 산출한다.

---

## 4. 실제 변환 예시

### 4.1 입력 (PNE 15 Steps)

```
Step  0: 휴지
Step  1: 방전     399mA, endV=2.75V
Step  2: 충전     CC-CV 399mA→39.9mA, 4.47V    (EndI/Iref=0.10)
Step  3: 방전     399mA, endV=2.75V
Step  4: 충전     CC 2593.5mA→1995mA, 4.16V     (EndI/Iref=0.77)
Step  5: 휴지
Step  6: 충전     CC 1995mA→1596mA, 4.28V        (EndI/Iref=0.80)
Step  7: 휴지
Step  8: 충전     CC-CV 1596mA→199.5mA, 4.47V   (EndI/Iref=0.12)
Step  9: 방전     1995mA, endV=3.0V
Step 10: Loop     →Step5, 99회
Step 11: 충전     CC-CV 399mA→39.9mA, 4.47V
Step 12: 방전     399mA, endV=2.75V
Step 13: 충전     CC-CV 399mA→39.9mA, 4.47V
Step 14: 휴지
```

### 4.2 Queue 조립 과정

Phase ①②를 거치면 Queue(loop 제외):

```
Queue: [rest₀, dchg₁, chg₂, dchg₃, chg₄, rest₅, chg₆, rest₇, chg₈, dchg₉, chg₁₁, dchg₁₂, chg₁₃, rest₁₄]
       (아래첨자 = PNE step 인덱스)
```

| Toyo Line | pop sub_a | LEFT 결과 | pop sub_b | RIGHT 결과 | LOOP |
|---|---|---|---|---|---|
| **1** | rest₀ | REST (30) | dchg₁ | DCHG 399mA/2.75V **(iv=0)** | 없음 |
| **2** | chg₂ (CCCV) | CHG 399mA/4.47V/39.9mA | dchg₃ | DCHG 399mA/2.75V (iv=60) | 없음 |
| **3** | chg₄ (CC) | CHG 2593.5mA/4.16V/1995mA | rest₅ | REST | 없음 |
| **4** | chg₆ (CC) | CHG 1995mA/4.28V/1596mA | rest₇ | REST | 없음 |
| **5** | chg₈ (CCCV) | CHG 1596mA/4.47V/199.5mA | dchg₉ | DCHG 1995mA/3.0V (iv=60) | **→3, ×99** |
| **6** | chg₁₁ (CCCV) | CHG 399mA/4.47V/39.9mA | dchg₁₂ | DCHG 399mA/2.75V (iv=60) | 없음 |
| **7** | chg₁₃ (CCCV) | CHG 399mA/4.47V/39.9mA | rest₁₄ | REST | 없음 |

**Loop target 매핑**: PNE Step5 (0-based=4) → `pne_to_toyo_line[4]` = Toyo Line **3** ✓

### 4.3 검증 결과 (vs `Rawdata/toyo_1995mAh/PATRN1.1`)

```
Line 1: [PASS]  LEFT=REST  RIGHT=DCHG 399mA/2.75V (iv=0)
Line 2: [PASS]  LEFT=CHG CCCV 399mA  RIGHT=DCHG 399mA/2.75V
Line 3: [PASS]  LEFT=CHG CC 2593.5mA  RIGHT=REST
Line 4: [PASS]  LEFT=CHG CC 1995mA  RIGHT=REST
Line 5: [PASS]  LEFT=CHG CCCV 1596mA  RIGHT=DCHG 1995mA/3V  LOOP(→3, ×99)
Line 6: [PASS]  LEFT=CHG CCCV 399mA  RIGHT=DCHG 399mA/2.75V
Line 7: [PASS]  LEFT=CHG CCCV 399mA  RIGHT=REST

*** ALL 7 LINES MATCH REFERENCE EXACTLY ***
```

---

## 5. 템플릿 시스템

실제 PATRN1.1 파일에서 추출한 고정폭 문자열 템플릿을 사용한다.

### 5.1 LEFT 템플릿 (261 chars)

| 상수명 | 용도 | 치환 필드 |
|---|---|---|
| `TOYO_CHARGE_LEFT` | CC-CV 충전 | `[3:13]`=전류, `[13:21]`=전압, `[53:61]`=EndI |
| `TOYO_CHARGE_CC_LEFT` | CC 충전 | 동일 |
| `TOYO_REST_LEFT` | 휴지 | 치환 없음 (고정) |

### 5.2 RIGHT 템플릿 (272 chars)

| 상수명 | 용도 | 치환 필드 |
|---|---|---|
| `TOYO_DCHG_RIGHT` | 방전 (interval 있음) | `[3:13]`=전류, `[29:55]`=EndV, `[95:103]`=interval |
| `TOYO_DCHG_NO_INTERVAL_RIGHT` | 방전 (interval 없음) | `[3:13]`=전류, `[29:55]`=EndV |
| `TOYO_REST_RIGHT` | 휴지 | 치환 없음 (고정) |

### 5.3 치환 메서드

```python
_toyo_substitute(template, positions)
# positions = [((start, end), value_str), ...]
# 지정 위치에 value_str을 right-justify로 대입
```

---

## 6. 출력 파일 (6개 세트)

| 파일명 | 설명 | 인코딩 | 크기 참고 |
|---|---|---|---|
| `PATRN{N}.1` | 패턴 본체 (헤더 + 데이터 라인) | cp949 | 헤더 265B + 라인 543B × N |
| `Patrn{N}.option` | 셀 용량 설정 | cp949 | `[BaseCellCapacity]` 섹션 |
| `Patrn{N}.option2` | 라인별 옵션 (데이터 기록 설정) | cp949 | 헤더(266) + 라인별(295~299) |
| `Fld_Puls{N}.DIR` | 펄스 디렉토리 | cp949 | `,\n` × 데이터라인 수 |
| `Fld_Thermo{N}.DIR` | 온도 디렉토리 | cp949 | 빈 파일 |
| `THPTNNO.1` | 패턴 번호 | cp949 | 빈 파일 (없을 경우 생성) |

### 6.1 PATRN 헤더 (265 바이트)

```
[이름 필드 42바이트][고정 상수 202바이트][라인 수 21바이트]
```

- 이름 필드: cp949 인코딩, 42**바이트** 고정 (한글 2B/글자, 나머지 공백 패딩)
- `TOYO_HEADER_PREFIX`: 레퍼런스에서 추출한 202바이트 고정 상수

### 6.2 option2 패턴 (4종)

| 패턴 | 적용 라인 | 길이 | 조건 |
|---|---|---|---|
| `first_active` | 첫 번째 라인 (RIGHT=방전) | 295 chars | |
| `first_rest` | 첫 번째 라인 (RIGHT=휴지) | 295 chars | |
| `middle_active` | 중간 라인 (RIGHT=방전) | 299 chars | |
| `middle_rest` | 중간 라인 (RIGHT=휴지) | 299 chars | |
| `end_line` | 마지막 라인 | 295 chars | 항상 동일 |

---

## 7. UI 동작 흐름

```
[ptn_toyo_convert 버튼 클릭]
    ↓
1. ptn_list에서 선택된 패턴(TestID) 확인
2. MDB 경로 확인 (없으면 파일 선택 다이얼로그)
3. 출력 폴더 선택 (QFileDialog)
4. 패턴 번호 입력 (QInputDialog, 1~999)
5. 용량 읽기 (ptn_capacity 텍스트박스)
    ↓
[선택된 각 TestID에 대해]
    ↓
6. MDB에서 Step 데이터 조회
7. TestName 조회 (패턴 이름)
8. _pne_steps_to_toyo_substeps() 호출 → 변환
9. 6개 파일 생성
    ↓
10. 결과 메시지 표시
```

- 복수 패턴 선택 시 패턴 번호가 자동 증가 (`patrn_num + idx`)
- 진행률을 `progressBar`로 표시

---

## 8. 주요 엣지 케이스 처리

| 상황 | 처리 방식 |
|---|---|
| 방전이 LEFT에 위치 | REST_LEFT 생성 후 방전을 RIGHT로 이동 |
| 충전이 RIGHT에 위치 | REST_RIGHT 대체, 충전을 Queue 앞에 되돌림 (다음 라인 LEFT) |
| Queue에 서브스텝 1개만 남음 | REST로 나머지 채움 |
| Loop target 매핑 없음 | 근사 계산: `max(1, (target + 1) // 2)` |
| LEFT=REST + RIGHT=방전 | interval=0 (데이터 기록 안 함) |
| StepType 9 (Continuation) | 이전 스텝 컨텍스트(충전/방전)에 따라 결정 |
| StepType 6 (End) | 건너뜀 (Toyo에는 End 개념 없음) |
| 미지원 StepType | 휴지로 대체 |

---

## 9. 코드 위치 요약

| 메서드 | 위치(라인) | 역할 |
|---|---|---|
| `TOYO_*` 상수들 | L15549~15601 | 서브스텝 템플릿 |
| `_toyo_fmt_num()` | L15603 | 숫자 포맷팅 |
| `_toyo_substitute()` | L15610 | 템플릿 치환 |
| `_toyo_build_charge_left()` | L15617 | 충전 LEFT 생성 |
| `_toyo_build_dchg_right()` | L15627 | 방전 RIGHT 생성 |
| `_toyo_build_rest_left()` | L15636 | 휴지 LEFT |
| `_toyo_build_rest_right()` | L15640 | 휴지 RIGHT |
| `_toyo_build_loop()` | L15644 | LOOP 필드 생성 |
| `_toyo_build_line()` | L15650 | LEFT+RIGHT+LOOP 결합 |
| `_toyo_build_header()` | L15654 | 헤더 265바이트 생성 |
| `_toyo_build_option()` | L15663 | option 파일 생성 |
| `_toyo_build_option2()` | L15666 | option2 파일 생성 |
| `_toyo_build_puls_dir()` | L15722 | Fld_Puls 생성 |
| `_pne_steps_to_toyo_substeps()` | L15725 | **핵심 변환 로직** |
| `ptn_toyo_convert_button()` | L15904 | UI 버튼 핸들러 |
