# 프로파일 분석 통합 아키텍처 분석

> 작성일: 2026-07-07
> 목적: 기존 5개 프로파일 모드 → 통합 파이프라인 매핑 정리 및 검증

---

## 1. 기존 → 현재 모드 매핑

### UI 옵션 조합 → legacy 모드

| scope (데이터 범위) | axis (X축) | continuity (연속성) | legacy 모드 | calc_dqdv |
|---------------------|-----------|---------------------|-------------|-----------|
| charge (충전) | soc | overlay | **chg** | ✅ |
| discharge (방전) | soc | overlay | **dchg** | ✅ |
| cycle (사이클) | soc | overlay | **cycle_soc** | ✅ |
| charge/discharge/cycle | time | overlay | **step** | ❌ |
| * | * | continuous | **continue** | ❌ |

### 기존 5개 함수 → 현재 통합 함수

| 기존 함수 | 현재 대응 | 비고 |
|-----------|----------|------|
| `toyo_step_Profile_data()` | `unified_profile_core(data_scope="charge", axis_mode="time")` | step은 기존에 Cond=1만, 현재는 scope 선택 가능 |
| `toyo_rate_Profile_data()` | 동일 (step과 동일 파이프라인) | rate는 multi-file 병합 없음 → cycle_map이 1파일 범위면 동일 |
| `toyo_chg_Profile_data()` | `unified_profile_core(data_scope="charge", axis_mode="soc", calc_dqdv=True)` | |
| `toyo_dchg_Profile_data()` | `unified_profile_core(data_scope="discharge", axis_mode="soc", calc_dqdv=True)` | |
| `toyo_Profile_continue_data()` | `unified_profile_core(continuity="continuous")` | |
| `pne_step_Profile_data()` | 동일 구조 (PNE 전용 정규화) | |
| `pne_chg_Profile_data()` | 동일 구조 | |
| `pne_dchg_Profile_data()` | 동일 구조 | |

---

## 2. 통합 파이프라인 (unified_profile_core)

```
입력: (channel_path, (논리사이클_start, 논리사이클_end), mincapacity, inirate, 옵션들)
  ↓
Stage 1: 사이클러 판별 + cycle_map 확보
  - check_cycler() → PNE / Toyo
  - cycle_map 없으면 자동 생성 (toyo_build_cycle_map / pne_build_cycle_map)
  ↓
Stage 2: 원시 데이터 로딩
  - _unified_toyo_load_raw(): cycle_map[논리사이클]['all'] 범위의 물리파일 전부 로드
  - _unified_pne_load_raw(): SaveData에서 해당 TC 범위 슬라이싱
  ↓
Stage 3: Condition 필터링 (_unified_filter_condition)
  - Condition=9(CC) → 전류 부호로 1(충전)/2(방전)/3(휴지) 재분류
  - data_scope="charge" → Cond=1만 유지
  - data_scope="discharge" → Cond=2만 유지
  - data_scope="cycle" → 전체 유지 (GITT/Pulse 등)
  - include_rest 옵션에 따라 인터펄스 휴지/경계 휴지 제어
  ↓
Stage 4: 정규화 (_unified_normalize_toyo / _unified_normalize_pne)
  - Time_s: PassTime diff → clip(0) → cumsum (파일 경계 자동 연속화)
  - Crate: Current / mincapacity
  - ChgCap/DchgCap: shift(-1) 기반 시간적분 (기존 방식 정합)
  - ChgWh/DchgWh: 에너지 적분
  ↓
Stage 5: 스텝 병합 (_unified_merge_steps)
  - data_scope="cycle" → 시간순 정렬만
  - multi_tc → 용량 리셋 감지 + 누적 보정
  - charge/discharge → Step 기반 시간/용량 연속화
  ↓
Stage 6: X축 및 SOC 계산 (_unified_calculate_axis)
  - TimeMin = Time_s / 60
  - SOC: charge → ChgCap, discharge → DchgCap, cycle → ChgCap - DchgCap
  - overlay: 사이클별/Block별 시간 0 리셋 + NaN 행 삽입 (선 끊기)
  - continuous: 전체 시간 연속
  ↓
Stage 7 (옵션): dQdV 계산 (_unified_calculate_dqdv)
  - calc_dqdv=True일 때만 실행
  ↓
최종 DataFrame 컬럼:
  - 기본: TimeMin, SOC, Voltage, Crate, Temp, Vol(=Voltage 별칭), Cycle, Condition
  - dQdV: + Energy, dQdV, dVdQ
  - continue: + TimeSec, Curr
```

---

## 3. multi-file 병합 검증

### 기존 step: lasttime 누적 방식
```python
while maxcon == 1:  # 다음 파일도 충전이면 계속
    stepcyc += 1
    tempdata = toyo_Profile_import(raw_file_path, stepcyc)
    tempdata.dataraw["PassTime[Sec]"] += lasttime
    df.stepchg = df.stepchg._append(tempdata.dataraw)
    lasttime = df.stepchg["PassTime[Sec]"].max()
```

### 현재: cycle_map + time clipping

1. `toyo_build_cycle_map`이 연속 충전 물리파일을 하나의 논리사이클로 그룹화
2. `_unified_toyo_load_raw`가 해당 범위의 물리파일 전부 로드 (각 파일의 PassTime 0부터)
3. `_unified_normalize_toyo`에서:
   ```
   PassTime: [0,10,20,30, 0,10,20,30]  (파일1, 파일2)
   diff:     [0,10,10,10, -30,10,10,10]
   clip(<0): [0,10,10,10,   0,10,10,10]
   cumsum:   [0,10,20,30, 30,40,50,60]  ← 연속!
   ```

**결론: 기존 lasttime 누적과 동일한 결과를 자동으로 생성. ✓**

### 기존 dchg: 다음 파일 방전 병합

기존: 다음 파일에 충전 없으면 → 방전만 추출 병합
현재: `toyo_build_cycle_map`의 merge_group이 연속 방전 파일을 하나의 그룹으로 인식 → 같은 논리사이클에 포함

**결론: cycle_map이 올바르게 생성되면 자동 처리. ✓**

---

## 4. 용량 계산 정합성

### 기존 Toyo (shift(-1) 방식)
```python
delta_time = PassTime.shift(-1) - PassTime      # dt[i] = t[i+1] - t[i]
next_current = Current.shift(-1)                 # I[i+1]
contribution = delta_time * next_current / 3600  # dt × I(next)
Cap = cumsum(contribution)
SOC = Cap / mincapacity
```

### 현재 (_unified_normalize_toyo) — 기존 방식에 맞춤
```python
dt_fwd[:-1] = diff(Time_s)        # dt[i] = t[i+1] - t[i]
next_curr_mA[:-1] = current[1:]   # I[i+1]
chg_inc = dt_fwd × |next_curr| / 3600 / mincapacity
ChgCap = cumsum(chg_inc)
```

**수학적으로 동일. ✓**

---

## 5. 수정 사항 이력

| 날짜 | 수정 내용 |
|------|----------|
| 2026-07-07 | SyntaxError 수정 (3492라인 한글 오타 `ㅅ` 제거) |
| 2026-07-07 | Excel 저장 컬럼 불일치 수정 — step(5→가변), chg/dchg(8→가변) 컬럼 선택 후 저장 |
| 2026-07-07 | Toyo 용량 계산을 기존 shift(-1) 방식으로 정합 (dt_fwd × next_curr) |

---

## 6. GITT/Pulse 패턴 지원 (새 기능)

기존에는 step 모드가 Condition==1(충전)만 필터링했으나, 현재 통합 시스템에서는:

- **scope=charge**: 기존 step과 동일 (충전만)
- **scope=discharge**: 방전 프로필
- **scope=cycle**: 전체 사이클 (충전+휴지+방전+보충전) → **GITT/DCIR/Pulse 패턴 지원**

data_scope="cycle"일 때 `_unified_filter_condition`은 Condition 필터 없이 전체 데이터를 유지하므로, SOC 구간별 펄스+휴지+보충전/보방전이 모두 포함됩니다.
