# 프로파일 옵션 재설계 — 배터리 전기화학 전공자 기준

**날짜**: 2026-04-18  
**배경**: 사용자 요구 — 휴리스틱 제거, 실제 배터리 분석에 필요한 옵션으로 재편성, Graphite/LCO/SiC 케미스트리 관점.

## 1. SaveEndData 스키마 공식 정의 (원본 확정)

origin `BAK/BatteryDataTool_origin.py` L1583-1590 주석이 **정답 소스**:

```
0:Index  1:Stepmode(1:CC-CV,2:CC,3:CV,4:OCV)
2:StepType(1:충전,2:방전,3:휴지,4:OCV,5:Impedance,6:End,8:loop)
3:ChgDchg  4:State  5:Loop(Loop:1)
6:Code(66:충전,65:방전,64:휴지,64:loop)
7:StepNo  8:Voltage(uV)  9:Current(uA)
10:ChgCap(uAh)  11:DchgCap(uAh)  12:ChgPower(uW)  13:DchgPower(uW)
14:ChgWh  15:DchgWh
17:StepTime(/100s)  18:TotTime(day)  19:TotTime(/100s)  20:imp
21:Temp1  22:Temp2  23:Temp3  24:Temperature(°C)
27:TotalCycle  28:CurrCycle  29:AvgVoltage(mV)  30:AvgCurrent(A)
33:date  34:time
44:누적step(Loop,완료 제외)  45:voltage max
```

**이전 스키마 오류 (교정됨)**:
- col[1] "Default2" → **Stepmode**
- col[5] "CCCV" → **Loop flag** (사용자 추정도 오류, origin 주석이 정답)
- col[12]/[13] mW → **uW**
- col[24] "Temp4" → **Temperature(°C) 기본 온도**
- col[29] uV → **mV**
- col[30] uA → **A**

## 2. F-2 완료: 보충전/보방전 필터 삭제

**위치**: `_unified_filter_condition` L1678-1712 (삭제됨)

**이전 동작**: 공칭 용량의 2% 미만 스텝을 스윕 시험에서 자동 제외
**변경**: 모든 스텝 상시 포함. 사용자가 RSS/DCIR 계산 시 OCV 기준점으로 보충전 사용.

## 3. F-1 설계: OCV/CCV 컬럼 복원

**origin 규칙** (L1546-1554):
```python
# 스텝 단위 분류 (StepType 기반, 무휴리스틱)
CycfileOCV = df.loc[df[2]==3, [0, 8]]          # REST 스텝 전압 = OCV
CycfileCCV = df.loc[df[2].isin([1, 2]), [0, 8]] # CHG/DCHG 스텝 전압 = CCV
# RecIdx로 outer merge → 레코드마다 OCV와 CCV 컬럼
```

**구현 위치**:
- `_unified_pne_load_raw` 또는 프로파일 로드 직후
- Profileraw에 "OCV", "CCV" 컬럼 추가
- 단위 변환: uV → V (`/1_000_000`)

**사용처**:
- dVdQ 분석: OCV 기반
- DCIR 계산: `RSS = |CCV − OCV| / Current × 1000`
- 과전압 시각화: `overpotential = CCV − OCV`

## 4. C-1 설계: CV 제외 (무휴리스틱)

### 문제
현재 `_unified_filter_condition` L1714-1750의 `dv < 2mV` 임계값은 **임의 휴리스틱**.

### 해결: 장비 스펙 기반 2단계 접근

#### 4-a. 스텝 단위 (즉시 구현 가능)
```python
# SaveEndData col[1] Stepmode 활용
from save_end_schema import STEPMODE_CC_CV, STEPMODE_CV, stepmode_has_cv

if not include_cv:
    # Stepmode=1(CC-CV) 또는 3(CV) 스텝의 레코드 제외
    cv_stepmode_steps = save_end[save_end[1].isin([1, 3])][7].unique()  # col[7]=StepNo
    filtered = filtered[~filtered["Step"].isin(cv_stepmode_steps)]
```
**장점**: 무휴리스틱 100%  
**단점**: CC-CV 스텝은 **전체 제외** (CC 부분도 사라짐)

#### 4-b. 레코드 단위 (.sch cv_cutoff 기반)
```python
# .sch의 각 CHG_CCCV 스텝 → cv_cutoff (장비 제어 임계값)
from tc_plan import build_tc_plan
plan = build_tc_plan(channel_dir)

for step_num, step_info in plan.step_info.items():
    if step_info.type == "CHG_CCCV":
        cv_cutoff_mA = step_info.cv_cutoff  # 장비 스펙
        v_chg_target = step_info.v_chg_mV
        
        # 시계열에서 CV 진입 시점: |I| < cv_cutoff 첫 진입
        step_records = filtered[filtered["Step"] == step_num]
        cv_start_idx = (step_records["Current_abs"] < cv_cutoff_mA).idxmax()
        filtered.loc[filtered.index >= cv_start_idx, "in_cv"] = True

if not include_cv:
    filtered = filtered[~filtered["in_cv"]]
```
**장점**: CC 부분은 유지, CV 부분만 제거. 무휴리스틱.  
**단점**: 파이프라인에 `.sch` 정보 전달 필요 (리팩토링).

### 선택
- **Phase 1 (즉시)**: 4-a 스텝 단위 (간단, 무휴리스틱)
- **Phase 2 (후속)**: 4-b 레코드 단위 (정밀)

## 5. D-1 설계: 옵션 재구성

### 원칙
- origin 버튼별 기능을 **옵션으로 통합**
- **배터리 전기화학 전공자가 꼭 봐야 할 것**을 기본 표시
- Graphite/LCO/SiC 특화 지표 **고급 옵션**으로 접근 가능

### origin 버튼 → 새 옵션 매핑

| origin 버튼 | 기능 | 새 옵션 매핑 |
|------------|------|-------------|
| `step_confirm_button` | 기본 V-Q/V-t 프로파일 | 분석 모드 = **Standard** |
| `rate_confirm_button` | C-rate별 overlay | 분석 모드 = **Rate analysis** |
| `chg_confirm_button` | 충전만 | data_scope = charge |
| `dchg_confirm_button` | 방전만 | data_scope = discharge |
| `continue_confirm_button` | 사이클 연속 | overlap = continuous |
| `dcir_confirm_button` | DCIR 표시 | 분석 모드 = **DCIR** |
| `dvdq_profile_button` | dV/dQ | 변환 = **dV/dQ** |
| `dvdq_material_button` | 재료 분석 | 분석 모드 = **Material fitting** |

### 배터리 전기화학 전공자 필수 지표 (Graphite/LCO/SiC)

#### 공통 (모든 셀)
1. **V vs Q 프로파일** — 기본
2. **dQ/dV (incremental capacity)** — 상전이/staging
3. **dV/dQ (differential voltage)** — 전극 밸런스, LLI/LAM 분해
4. **CE (Coulombic Efficiency)** — SEI/Li plating 검출
5. **CCV − OCV = 과전압** — kinetic loss
6. **DCIR vs SOC** — 저항 증가
7. **Capacity fade vs cycle** — 열화 rate

#### Graphite 음극 특화
- **Staging peak** — dQ/dV peak at ~0.09V, 0.15V, 0.22V (Stage 1→2→3 전이)
- **ICE (Initial Coulombic Efficiency)** — SEI 형성 지표
- **Li plating 감지** — dV/dQ spike (저온/고속 충전 시)
- **OCV 완화** — rest 후 V relaxation (diffusion)

#### LCO 양극 특화
- **상전이 peak** — dQ/dV at 3.93V (H1→M), 4.17V (M→H2)
- **고전압 안정성** — 4.3V 이상 plateau 변화 (Co dissolution)
- **plateau 비대칭** — 충/방 곡선 차이

#### SiC (Silicon-Graphite 복합) 특화
- **Si 기여 peak** — dQ/dV broad peak at ~0.4-0.5V (충전), ~0.2-0.3V (방전)
- **Hysteresis loop** — SiC 특유, 크기 추적
- **사이클별 peak 이동** — SEI growth + active material loss
- **Anode-dominant LAM** — dV/dQ로 구분

### UI 재구성 초안

```
┌─ 분석 모드 (주 라디오) ─────────┐
│ ● Standard  (V-Q/V-t)           │ ← 기본 프로파일
│ ○ Rate      (C-rate overlay)    │ ← 배터리 엔지니어용
│ ○ dQ/dV     (IC curve)          │ ← 상전이/staging
│ ○ dV/dQ     (DV curve)          │ ← 전극 밸런스
│ ○ DCIR      (R-SOC)             │ ← 저항 분석
│ ○ Material  (dV/dQ 재료 피팅)    │ ← 고급 열화 분석
└─────────────────────────────────┘

┌─ 데이터 구간 ────────────────────┐
│ ● 전체 (CHG+DCHG)               │
│ ○ 충전만                        │
│ ○ 방전만                        │
│ ☐ Rest 포함 (경계 휴지)          │
│ ☐ CV 제외 (CC only)              │
│   └─ 방식: [스텝 단위 ▼]        │
│            ├ 스텝 단위 (CC-CV 스텝 전체 제외) │
│            └ 레코드 단위 (.sch cv_cutoff 기반)│
└─────────────────────────────────┘

┌─ X축 ──────────────┐ ┌─ Y축 변환 ──────────┐
│ ● 시간 (s)          │ │ ● Voltage (V)        │
│ ○ 용량 (mAh)        │ │ ○ dQ/dV              │
│ ○ SOC (%)           │ │ ○ dV/dQ              │
│ ○ DOD (%)           │ │ ○ Overpotential      │
└──────────────────┘ │   (CCV − OCV)       │
                      └────────────────────┘

┌─ 연결 모드 ────────────┐ ┌─ 도메인 마커 (옵션) ─┐
│ ● 독립 플롯            │ │ ☐ Graphite staging   │
│ ○ 시간축 연속          │ │ ☐ LCO 상전이         │
│ ○ 용량축 연속          │ │ ☐ SiC Si peak        │
└────────────────────┘ │ ☐ Li plating 경고    │
                         └────────────────────┘

┌─ 기타 ──────────────────────┐
│ ☐ 코인셀 모드               │
│ ☐ 정규화 (C-rate)            │
│ ☐ 스무딩 (N pts)             │
│ ☐ 자동 재렌더링 (G1)         │
└──────────────────────────┘
```

### 주요 변경점
- **"이어서/분리/순차/연결" → "독립/시간축/용량축"**: 용어 정리
- **X축 확장**: 용량(mAh), DOD(%) 추가 (배터리 분석 필수)
- **Y축 변환 추가**: dQ/dV, dV/dQ, 과전압 한 UI에서 전환
- **도메인 마커**: 케미스트리별 예상 peak 위치 표시 (교육/검증용)

## 6. G1 설계: 옵션 변경 즉시 반영

### 현재
옵션 변경 → 사용자가 버튼 다시 클릭해야 갱신

### 새 설계
```python
# __init__ 시그널 연결
self.profile_rest_chk.toggled.connect(self._on_profile_option_changed)
self.profile_cv_chk.toggled.connect(self._on_profile_option_changed)
self.profile_axis_soc.toggled.connect(self._on_profile_option_changed)
# ... 모든 옵션 체크박스/라디오

def _on_profile_option_changed(self):
    if not self._last_profile_args:
        return  # 아직 한 번도 분석 안 함
    if self._auto_rerender_chk.isChecked():
        # 디바운스 500ms
        self._rerender_timer.start(500)

def _debounced_rerender(self):
    self.unified_profile_confirm_button(
        from_cached_args=self._last_profile_args
    )
```

`_last_profile_args`에 마지막 성공한 분석 파라미터 저장 → 옵션 변경 시 재사용.

## 7. 구현 로드맵

| Phase | 작업 | 상태 |
|-------|------|------|
| P1 | F-2 보충전 필터 삭제 | ✅ 완료 |
| P2 | save_end_schema origin 기반 교정 | ✅ 완료 |
| P3 | F-1 OCV/CCV 컬럼 복원 | ⏳ 다음 |
| P4 | C-1 Phase 1: Stepmode 기반 스텝 단위 CV 제외 | ⏳ |
| P5 | D-1 UI 재구성 Phase 1: 분석 모드 라디오 + Y축 변환 | ⏳ |
| P6 | C-1 Phase 2: .sch cv_cutoff 전달 → 레코드 단위 CV 경계 | ⏳ |
| P7 | D-1 Phase 2: 도메인 마커, 코인셀, 스무딩 | ⏳ |
| P8 | G1 옵션 변경 즉시 반영 | ⏳ |
| P9 | 테스트 추가 (F-1/C-1/G1) + 도메인 검증 | ⏳ |
