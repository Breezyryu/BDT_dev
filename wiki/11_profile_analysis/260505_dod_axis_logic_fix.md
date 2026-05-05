# DOD 축 로직 수정 — 사이클 + 분리/연결 + DOD 물리 좌표계 회복

날짜: 2026-05-05
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`

## 배경

사이클 + 분리/연결 + **DOD** 모드에서 그래프가 비대칭으로 표시되어
SOC/DOD 개념이 어긋난다는 사용자 보고. SOC 모드는 정상.

기존 (260420 추가) DOD 로직:
- **분리 (split)**: chg = `−ChgCap` (0 → −1), dchg = `DchgCap` (0 → 1)
- **연결 (connected)**: chg = `−ChgCap` (0 → −peak), dchg = `DchgCap` (0 → peak)

원래 의도는 "충전을 음수 영역에 배치하여 방전 위주 시각 강조" 였으나:
1. **물리 의미 위반**: DOD ∈ [0, 1] 정의 (0 = 만충, 1 = 방전 완료) 와 어긋남
2. **분리 모드 plot 클리핑**: 비히스테리시스 plot 의 X 범위가 `(-0.1, 1.2)` 하드코딩 →
   chg 의 음수 DOD 곡선이 **거의 비가시**
3. **분리 모드 라벨 오류**: 비히스테리시스 plot 라벨이 `"SOC"` 하드코딩 →
   DOD 선택 시에도 X 축에 "SOC" 표시
4. **사용자 mental model 불일치**: "DOD = depth of discharge" 직관 위배

## 변경 내용

### 1. `_calc_soc` — 연결(connected) DOD 분기 (L2480~)

**Before**:
```python
if axis_mode == "dod" and overlap == "connected":
    # 방전은 DchgCap, 충전은 -ChgCap 로 음수 영역 배치
    if "Condition" in df.columns:
        dod = pd.Series(np.nan, index=df.index)
        chg_mask = df["Condition"] == 1
        dchg_mask = df["Condition"] == 2
        if chg_mask.any():
            dod[chg_mask] = -df.loc[chg_mask, "ChgCap"]
        if dchg_mask.any():
            dod[dchg_mask] = df.loc[dchg_mask, "DchgCap"]
        return dod.ffill()
```

**After** — SOC connected 의 mirror image (per-cycle peak):
```python
if axis_mode == "dod" and overlap == "connected":
    if "Condition" in df.columns:
        dod = pd.Series(np.nan, index=df.index)
        for cyc in df["Cycle"].unique():
            cyc_mask = df["Cycle"] == cyc
            if not cyc_mask.any():
                continue
            chg_mask = cyc_mask & (df["Condition"] == 1)
            dchg_mask = cyc_mask & (df["Condition"] == 2)
            peak = (df.loc[chg_mask, "ChgCap"].max()
                    if chg_mask.any() else 1.0)
            if chg_mask.any():
                dod[chg_mask] = peak - df.loc[chg_mask, "ChgCap"]
            if dchg_mask.any():
                dod[dchg_mask] = df.loc[dchg_mask, "DchgCap"]
        return dod.ffill()
```

대응 관계:
- SOC connected: chg = `ChgCap` (0 → peak), dchg = `peak − DchgCap` (peak → 0)
- DOD connected: chg = `peak − ChgCap` (peak → 0), dchg = `DchgCap` (0 → peak)
- DOD = peak − SOC (1−x 대칭, x ∈ [0, peak] 닫힌 loop).

### 2. `_calc_soc` — 분리(split) DOD 분기 (L2524~)

**Before**:
```python
if axis_mode == "dod":
    soc[chg_mask] = -df.loc[chg_mask, "ChgCap"]
```

**After**:
```python
if axis_mode == "dod":
    soc[chg_mask] = 1.0 - df.loc[chg_mask, "ChgCap"]
```

대응 관계:
- SOC split: chg = `ChgCap` (0 → 1), dchg = `DchgCap` (0 → 1) — cumulative throughput.
- DOD split: chg = `1 − ChgCap` (1 → 0), dchg = `DchgCap` (0 → 1) — 물리 DOD,
  data_scope=charge + DOD 의 식과 일치.

### 3. 히스테리시스 plot X 범위 (L28113)

**Before**:
```python
# DOD 축은 충전을 -1~0, 방전을 0~+1 범위로 표시 (방전 위주 해석)
_x_lo, _x_hi = (-1.1, 1.2) if _is_dod else (-0.1, 1.2)
```

**After** — SOC/DOD 모두 [0, 1] 좌표계:
```python
# SOC/DOD 모두 [0, 1] 범위 (2026-05-05 DOD fix).
_x_lo, _x_hi = (-0.1, 1.2)
```

### 4. 분리 plot 라벨/범위 (L28282~)

비히스테리시스 (split) 분기에서 하드코딩 `"SOC"` + `-0.1, 1.2` 를
`_axis_label` + `_x_lo/_x_hi` 변수로 교체. DOD 선택 시 X 축 라벨이
`"DOD"` 로 정확히 표시. 6 개 axes (`ax1, ax2(dQdV), ax3, ax4(dVdQ), ax5(Crate), ax6(Temp)`)
모두 일관 적용.

### 5. 히스테리시스 SOC 보정 가드 코멘트 (L27849)

기존:
```python
# DOD 축은 모든 cycle이 0에서 시작하므로 offset 불필요.
```

신규:
```python
# DOD 축은 별도 보정 로직 (mirror image) 미구현 — 현재 SOC 만 적용.
# DOD connected 는 _calc_soc 에서 [0, peak] 닫힌 loop 로 표시 (per-cycle).
```

DOD 절대좌표 보정은 후속 작업 — 현재는 per-cycle 상대 loop 로 충분히 시각화 가능.

## 검증 포인트

### 사이클 + 분리 + DOD
- [ ] 충전 곡선: x = 1 → 0 (오른쪽에서 왼쪽으로 진행, DOD 감소)
- [ ] 방전 곡선: x = 0 → 1 (왼쪽에서 오른쪽으로 진행, DOD 증가)
- [ ] X 축 라벨: "DOD" (이전: 잘못된 "SOC")
- [ ] X 범위: [0, 1] (이전: 충전이 [-1, 0] 으로 클리핑)

### 사이클 + 연결 + DOD (히스테리시스)
- [ ] 사이클별 닫힌 loop: 충전 peak → 0, 방전 0 → peak (SOC 와 1−x 대칭)
- [ ] 충전 곡선 끝과 방전 곡선 시작이 x=0 에서 만남
- [ ] 충전 곡선 시작과 방전 곡선 끝이 x=peak 에서 만남
- [ ] X 축 라벨 "DOD", X 범위 [0, 1.2]

### 사이클 + 분리 + SOC (회귀)
- [ ] 변경 없음 — 기존 동작 유지
- [ ] chg=ChgCap (0→1), dchg=DchgCap (0→1)

### 사이클 + 연결 + SOC (회귀)
- [ ] 변경 없음 — 기존 동작 유지
- [ ] chg=ChgCap (0→peak), dchg=peak−DchgCap (peak→0)

### 충전/방전 단방향 + DOD (회귀)
- [ ] 변경 없음 — `_calc_soc` 의 data_scope=charge/discharge 분기는 미수정
- [ ] charge: `1 − ChgCap` (DOD 1→0)
- [ ] discharge: `DchgCap` (DOD 0→1)

## 영향 범위

- **변경**: 사이클 + 분리/연결 + DOD 의 X 좌표 계산식 + plot 라벨/범위
- **불변**: SOC 모드, 시간 축, 충전/방전 단방향 scope, 프리셋 매핑
- **미구현 (후속)**: DOD 절대좌표 hysteresis offset (현재는 per-cycle 상대 loop)

## 관련 문서

- [[260420_profile_axis_dod_option]] — DOD 옵션 최초 추가 (이 PR 로 식 변경)
- [[260428_profile_4modes_spec]] — 4종 분석 모델 spec (DOD 좌표계 정의)
- [[260505_disable_cycle_split_time]] — 같은 날 사이클+분리+시간 비활성화
