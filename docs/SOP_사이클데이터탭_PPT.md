# BatteryDataTool - 사이클데이터 탭 SOP
### 충방전 Cycle / Profile 데이터 분석

---

## 📌 1. 탭 개요

| 항목 | 내용 |
|------|------|
| **탭 이름** | 사이클데이터 |
| **목적** | Toyo / PNE 충방전 원시데이터로부터 Cycle 수명 및 Profile 분석 |
| **하위 탭** | **Cycle** (tab_5) — 수명 그래프 / **Profile** (tab_6) — 충방전 프로파일 |

---

## 📌 2. 화면 구성

```
┌──────────────────────────────────────────────────────────────────┐
│ [☐ 지정Path사용] [☐ ECT path 사용] [☐ 코인셀] [경로직접입력란]     │
│ [Tab Reset]                                                       │
├────────────────────┬─────────────────────────────────────────────┤
│  ┌ 용량 선택 ─────┐│  ┌─ [ Cycle ] ──── [ Profile ] ──────────┐  │
│  │ ◉ Cyclepath 기준││  │                                       │  │
│  │ ○ 용량값 직접입력││  │  (Cycle 탭 또는 Profile 탭 내용)       │  │
│  │ Rate: [0.2]    ││  │                                       │  │
│  │ 용량: [58]     ││  │                                       │  │
│  └────────────────┘│  └───────────────────────────────────────┘  │
├────────────────────┴─────────────────────────────────────────────┤
│  [ 그래프 출력 영역 — cycle_tab (동적 탭) ]                        │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📌 3. 공통 설정 (SOP 사전 준비)

### Step 0: 경로 및 용량 설정

| 설정 항목 | 위젯 | 설명 |
|-----------|------|------|
| **지정Path사용** | `chk_cyclepath` | 체크 시, 경로 목록 txt 파일로 불러오기 |
| **ECT path 사용** | `chk_ectpath` | ECT 전용 경로 사용 |
| **코인셀** | `chk_coincell_cyc` | 코인셀 모드 활성화 |
| **경로 직접입력** | `stepnum_2` | 줄바꿈으로 구분된 경로 직접 입력 |
| **용량 선택** | `capacitygroup` | Cyclepath 이름/테스트명/Crate 기준 자동 or 직접 입력 |
| **Rate** | `ratetext` | 초기 C-rate (기본: 0.2) |
| **용량** | `capacitytext` | 기준 용량 mAh (기본: 58) |
| **Tab Reset** | `cycle_tab_reset` | 그래프 탭 전체 초기화 |

> **경로 우선순위**: ① 지정Path 파일 → ② 직접입력란 → ③ 폴더 선택 대화상자

---

## 📌 4. Cycle 하위 탭 (tab_5)

### 4-1. 설정 파라미터

| 파라미터 | 위젯 | 기본값 | 설명 |
|----------|------|--------|------|
| Y축 최대 | `tcyclerngyhl` | 1.10 | Capacity Ratio 상한 |
| Y축 최소 | `tcyclerngyll` | 0.65 | Capacity Ratio 하한 |
| X축 최대 | `tcyclerng` | 0 (자동) | Cycle 수 상한 |
| DCIR scale | `dcirscale` | 0 (자동) | DCIR 배율 조정 |

### 4-2. DCIR 옵션 (택 1)

| 라디오버튼 | 설명 |
|-----------|------|
| `dcirchk` | PNE 설비 DCIR (SOC100, 10s 방전 Pulse) |
| `pulsedcir` | PNE 10s DCIR (SOC5/50, 10s 방전 Pulse) |
| `mkdcir` | PNE DCIR (SOC 30/50/70 충방전, 1s Pulse/RSS) |
| `dcirchk_2` | DCIR 고정 해제 (체크박스) |

### 4-3. Cycle 버튼 목록

| 버튼 | 함수 | 기능 |
|------|------|------|
| **개별 Cycle** | `indiv_cyc_confirm_button` | 각 셀별로 **개별 그래프** (6패널) 생성 |
| **통합 Cycle** | `overall_cyc_confirm_button` | 모든 셀을 **하나의 그래프**에 통합 |
| **연결 Cycle** | `link_cyc_confirm_button` | 같은 셀의 여러 테스트를 **Cycle 연결** |
| **연결 Cycle 여러개 개별** | `link_cyc_indiv_confirm_button` | 여러 셀 각각 연결 후 개별 그래프 |
| **연결 Cycle 여러개 통합** | `link_cyc_overall_confirm_button` | 여러 셀 각각 연결 후 통합 그래프 |
| **신뢰성 Cycle** | `app_cyc_confirm_button` | Excel 승인 데이터 기반 Cycle 그래프 |

### 4-4. Cycle 그래프 출력 (6패널)

```
┌─────────────────────┬─────────────────────┬─────────────────────┐
│ Discharge Cap Ratio │ Dchg/Chg Efficiency │ Temperature (℃)     │
│ (ax1)               │ (ax2)               │ (ax3)               │
├─────────────────────┼─────────────────────┼─────────────────────┤
│ DC-IR (mΩ)          │ Chg/Dchg Efficiency │ Avg/Rest Voltage(V) │
│ (ax4)               │ (ax5)               │ (ax6)               │
└─────────────────────┴─────────────────────┴─────────────────────┘
```

---

## 📌 5. Profile 하위 탭 (tab_6)

### 5-1. 통합 모드 (택 1)

| 라디오버튼 | 설명 |
|-----------|------|
| **사이클 통합** (`CycProfile`) | 하나의 셀 내 여러 사이클을 통합 |
| **셀별 통합** (`CellProfile`) | 같은 사이클 폴더 내 셀별 서브폴더 통합 |
| **전체 통합** (`AllProfile`) | 모든 셀/사이클을 하나의 그래프에 통합 |

### 5-2. 설정 파라미터

| 파라미터 | 위젯 | 기본값 | 설명 |
|----------|------|--------|------|
| Cycle 번호 | `stepnum` | 2 | 분석할 Cycle 지정 (예: 2 3-5 8-9) |
| 전압 Y축 하한 | `volrngyhl` | 2.5 | 전압 그래프 하한 |
| 전압 Y축 상한 | `volrngyll` | 4.7 | 전압 그래프 상한 |
| 전압 Y축 간격 | `volrnggap` | 0.1 | Y축 눈금 간격 |
| Smooth | `smooth` | 0 (자동) | 스무딩 정도 |
| 컷오프 | `cutoff` | 0 | 전류/전압 컷오프 |
| dQdV 축늘리기 | `dqdvscale` | 1 | dQ/dV 그래프 스케일 |
| dQdV X/Y축 변환 | `chk_dqdv` | 체크박스 | dQ/dV vs dV/dQ 축 전환 |

### 5-3. Profile 버튼 목록

| 버튼 | 함수 | 기능 |
|------|------|------|
| **충전 Step 확인** | `step_confirm_button` | 충전 Step별 전압/전류 Profile 표시 |
| **충전 분석** | `chg_confirm_button` | 충전 Profile + dQ/dV 분석 |
| **율별 충전 확인** | `rate_confirm_button` | C-rate별 충전 Profile 비교 |
| **방전 분석** | `dchg_confirm_button` | 방전 Profile + dQ/dV 분석 |
| **HPPC/GITT/ECT** | `continue_confirm_button` | 연속 Pulse/GITT/ECT 분석 |
| **DCIR** | `dcir_confirm_button` | DCIR 데이터 분석 |

### 5-4. Profile 그래프 출력 (6패널)

```
┌─────────────────────┬─────────────────────┬─────────────────────┐
│ Voltage vs Cap      │ dQ/dV (또는 dV/dQ)  │ Current vs Time     │
│ (ax1)               │ (ax2)               │ (ax3)               │
├─────────────────────┼─────────────────────┼─────────────────────┤
│ Voltage vs Time     │ Temperature vs Time │ (기타)               │
│ (ax4)               │ (ax5)               │ (ax6)               │
└─────────────────────┴─────────────────────┴─────────────────────┘
```

---

## 📌 6. 조작 순서 (SOP)

### Cycle 분석 흐름

```
Step 0: 용량 설정 (자동/직접) + 경로 설정 (Path파일/직접/선택)
    │
    ▼
Step 1: Cycle 하위 탭 선택
    │
    ├─ Y축 범위, X축 범위, DCIR 옵션 설정
    │
    ▼
Step 2: 분석 버튼 클릭 (개별/통합/연결/신뢰성)
    │
    ├─ 폴더 선택 대화상자 → 데이터 로딩 (병렬 처리)
    ├─ Toyo: CycleReport.csv 읽기
    └─ PNE:  Channel별 Pattern/*.csv 읽기
    │
    ▼
Step 3: 그래프 자동 생성 → cycle_tab에 동적 탭 추가
    │
    └─ [saveok 체크 시] Excel 파일로 데이터 저장
```

### Profile 분석 흐름

```
Step 0: 용량 설정 + 경로 설정 (동일)
    │
    ▼
Step 1: Profile 하위 탭 선택
    │
    ├─ 통합 모드 선택 (사이클/셀별/전체)
    ├─ Cycle 번호, 전압 Y축, Smooth, 컷오프 설정
    │
    ▼
Step 2: 분석 버튼 클릭 (충전Step/충전/율별/방전/HPPC/DCIR)
    │
    ├─ 폴더 선택 → Profile 데이터 로딩 (병렬 처리)
    │
    ▼
Step 3: 그래프 자동 생성 → cycle_tab에 동적 탭 추가
    │
    └─ [saveok 체크 시] Excel 파일로 데이터 저장
```

---

## 📌 7. 데이터 흐름

```
경로 선택 (Path 파일 / 직접입력 / 폴더선택)
    │
    ├─ Toyo 경로?
    │   ├─ Cycle: CycleReport.csv 파싱
    │   └─ Profile: PassTime-based CSV 파싱
    │
    └─ PNE 경로? (Pattern 폴더 존재 여부로 판별)
        ├─ Cycle: Channel_info.json + CSV 파싱
        └─ Profile: Pattern/*.csv → Step별 파싱
    │
    ▼
DataFrame 가공
    ├─ 용량 정규화 (Capacity Ratio = Cap / mincapacity)
    ├─ 효율 계산 (Dchg/Chg, Chg/Dchg)
    ├─ DCIR 계산 (옵션별)
    ├─ dQ/dV 계산 (Profile)
    └─ 스무딩 (Profile)
    │
    ▼
matplotlib 그래프 생성 → FigureCanvas → cycle_tab 동적 탭
```

---

## 📌 8. 주요 특이사항

| 항목 | 설명 |
|------|------|
| **병렬 로딩** | ThreadPoolExecutor (max_workers=4)로 데이터 병렬 처리 |
| **동적 탭** | 분석 결과가 `cycle_tab`에 번호 순으로 동적 추가됨 |
| **Tab Reset** | `cycle_tab_reset` 버튼으로 동적 탭 전체 삭제 |
| **Toyo vs PNE 자동 판별** | `check_cycler()` — Pattern 폴더 유무로 충방전기 종류 판별 |
| **용량 자동 추출** | 파일명에 "mAh"가 포함된 경우 `name_capacity()`로 자동 파싱 |
| **신뢰성 Cycle** | Excel(.xlsx)의 "Plot Base Data" 시트에서 직접 읽음 (xlwings) |
| **그림 저장** | `figsaveok` 체크 시 `output_fig()`로 이미지 파일 자동 저장 |
| **데이터 저장** | `saveok` 체크 시 Excel(.xlsx)로 시트별 저장 |
