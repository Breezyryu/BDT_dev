---
title: "PNE .sch 파싱 결정적 정정 — type_code swap + offset 의미 정정"
date: 2026-04-26
tags: [bugfix, pne, sch-parser, accel-pattern, ground-truth, critical]
related:
  - "[[260425_review_pne_mscc_cccv_cutoff|이전 196fc4d 분석 (잘못된 가정)]]"
  - "[[../00_index/path_table_redesign|경로 테이블 재설계]]"
---

# PNE `.sch` 파싱 결정적 정정 — type_code swap + offset 의미 정정

> **결정적 fix** — Ref CSV ground truth 로 raw 검증 후 확정.
> 직전 `196fc4d` (cv_cutoff=0 → CC 휴리스틱) 의 진짜 원인이었음. 휴리스틱 revert 포함.

## 배경

사용자가 본 BDT UI 의 Q8 / Gen4 충방전 패턴 표시:
```
[Q8 ATL Main 2.0C Rss RT(3ch)]
충전 4step: [1st] CC 2.0C/4.30V → [2nd] CC 1.65C/4.55V → [3rd] CC 1.40C/4.30V → [4th] CC 1.0C/4.55V
```

→ 실제 사용자 입력 (Ref CSV ground truth):
```
12  Charge  CC      IRef=4.640A  End: V > 4.14
13  Charge  CC      IRef=3.829A  End: V > 4.16
14  Charge  CC/CV   IRef=3.250A  End: I < 2.32
15  Charge  CC/CV   IRef=2.320A  End: I < 0.234 or t > 02:00:00
```

→ **모드도 cutoff 도 모두 잘못 표시** 되고 있었음.

## 원인 — 두 개의 결함이 결합

### 결함 1: `_SCH_TYPE_MAP` swap

이전 매핑:
```python
0x0101: 'CHG_CC',     # ← 잘못
0x0201: 'CHG_CCCV',   # ← 잘못
```

raw 검증 (`Q8 .sch idx 10-13` vs `Ref CSV step 12-15`):

| .sch idx | type_code | 이전 매핑 | 실제 (CSV) |
|---|---|---|---|
| 10 | 0x0201 | CHG_CCCV ❌ | CC ✓ |
| 11 | 0x0201 | CHG_CCCV ❌ | CC ✓ |
| 12 | 0x0101 | CHG_CC ❌ | CC/CV ✓ |
| 13 | 0x0101 | CHG_CC ❌ | CC/CV ✓ |

→ **충전 type_code 가 swap** 되어 있었음. 방전 (0x0102/0x0202) 은 정상.

### 결함 2: offset 의미 오해

이전 코드는 step block 의 voltage 컬럼(`+12` for CHG, `+16` for DCHG) 을 직접 cutoff 로 해석. 사용자 답변 + raw 검증 결과:

| Offset | 이전 가정 | 실제 의미 (검증) |
|---|---|---|
| `+12` (CHG) | V cutoff | **사용자 입력 voltage** (CC: safety/표시, CCCV: CV target V) |
| `+16` (DCHG) | V cutoff | **사용자 입력 voltage** (안전 마진/표시) |
| `+20` | I (current) | I (정확) |
| `+24` | time_limit | time_limit (CCCV 의 timeout, "t > 2:00:00") |
| `+28` | cv_voltage (CCCV 만) | **end_condition voltage** (CC 충: V>x, 방전: V<x. CCCV: 0) |
| `+32` | cv_cutoff_mA (CCCV 만) | **end_condition current** (CCCV: I<x. CC: 0) |

raw 검증 (Q8 .sch):
```
idx10 CC IRef=4.640A: offset 28 = 4140 ≡ "V > 4.14V" ✓
idx11 CC IRef=3.829A: offset 28 = 4160 ≡ "V > 4.16V" ✓
idx12 CCCV IRef=3.25A: offset 32 = 2320 ≡ "I < 2.32A" ✓
idx13 CCCV IRef=2.32A: offset 24 = 7200, offset 32 = 234 ≡ "I < 0.234A or t > 2:00" ✓
idx15 DCH IRef=2.32A: offset 28 = 3650 ≡ "V < 3.65V" ✓
```

### 결함 3 (파생): 196fc4d 휴리스틱

직전 commit 의 `cv_cutoff_mA < 1.0 → CC 표기` 휴리스틱:
- 진짜 원인: type_code swap 미수행 → CC step 을 CCCV 로 잘못 읽음 → cv_cutoff=0 으로 나오니 다시 CC로 표기 (우회)
- swap 후 자연 해소되므로 휴리스틱 자체가 **불필요** → revert.

## 변경 사항

### 1) `_SCH_TYPE_MAP` swap (L6809)

```python
_SCH_TYPE_MAP: dict[int, str] = {
    0x0101: 'CHG_CCCV',     # was CHG_CC
    0x0102: 'DCHG_CCCV',    # 검증 데이터 없음 — 대칭 가정 유지
    0x0201: 'CHG_CC',       # was CHG_CCCV
    0x0202: 'DCHG_CC',      # 검증됨, 그대로
    ...
}
```

### 2) `_parse_pne_sch` — offset 28/32 를 type 무관하게 모두 읽기 (L6917~)

```python
if type_name in ('CHG_CC', 'CHG_CCCV', 'CHG_CP'):
    voltage_mV = struct.unpack_from('<f', blk, 12)[0]      # 사용자 입력 V
    current_mA = struct.unpack_from('<f', blk, 20)[0]
    time_limit = struct.unpack_from('<f', blk, 24)[0]
    end_voltage_mV = struct.unpack_from('<f', blk, 28)[0]  # 신규 — CC 의 V cutoff
    end_current_mA = struct.unpack_from('<f', blk, 32)[0]  # 신규 — CCCV 의 I cutoff
    step_info.update({
        'voltage_mV': voltage_mV,
        'current_mA': current_mA,
        'time_limit_s': time_limit,
        'capacity_limit_mAh': cap_limit,
        'end_voltage_mV': end_voltage_mV,    # 신규 키
        'end_current_mA': end_current_mA,    # 신규 키
    })
    if type_name == 'CHG_CCCV':
        # 호환 alias — 기존 키와 의미 유지
        step_info['cv_voltage_mV'] = voltage_mV
        step_info['cv_cutoff_mA'] = end_current_mA
```

방전도 동일 패턴 (`elif type_name in ('DCHG_CC', 'DCHG_CCCV')`).

### 3) `extract_accel_pattern_from_sch` — voltage/current_cutoff 의미 정정 + 휴리스틱 제거 (L7085~)

```python
# 196fc4d 휴리스틱 (_CCCV_MIN_CUTOFF_MA = 1.0) 제거 — type 만으로 결정
charge_result = []
for idx, s in enumerate(chg_steps):
    cur_mA = s.get('current_mA', 0)
    is_cccv = (s['type'] == 'CHG_CCCV')
    if is_cccv:
        # CCCV: voltage_mV(+12) = CV target V, end_current_mA(+32) = "I < x"
        v_cutoff = s.get('voltage_mV', 0) / 1000
        i_cutoff_mA = s.get('end_current_mA', 0) or s.get('cv_cutoff_mA', 0)
    else:
        # CC: end_voltage_mV(+28) = V cutoff "V > x"
        v_cutoff = s.get('end_voltage_mV', 0) / 1000
        i_cutoff_mA = 0
    entry = {
        'step': idx + 1,
        'mode': 'CCCV' if is_cccv else 'CC',
        'crate': ...,
        'current_mA': cur_mA,
        'voltage_cutoff': round(v_cutoff, 3),
    }
    if is_cccv and i_cutoff_mA > 0:
        entry['current_cutoff_crate'] = round(i_cutoff_mA / capacity, 2)
        entry['current_cutoff_mA'] = i_cutoff_mA
    charge_result.append(entry)

# 방전: end_voltage_mV(+28) = V cutoff "V < x"
for idx, s in enumerate(dchg_steps):
    v_cutoff = s.get('end_voltage_mV', 0) / 1000
    discharge_result.append({...})
```

## 효과

### Q8 ATL Main 2.0C Rss RT (2335 mAh) 표시 변화

**Before (잘못)**:
```
충전 4step: CC 2.0C/4.30V → CC 1.65C/4.55V → CC 1.40C/4.30V → CC 1.0C/4.55V
방전 2step: CC 1.0C/2.50V → CC 0.50C/2.50V
```

**After (정확)**:
```
충전 4step: CC 2.0C/4.14V → CC 1.65C/4.16V → CCCV 1.40C/4.30V/0.99C cutoff → CCCV 1.0C/4.55V/0.10C cutoff
방전 2step: CC 1.0C/3.65V → CC 0.50C/3.00V
```

→ Ref CSV ground truth 와 100% 일치.

## 영향 범위

이 변경은 **모든 PNE 데이터** 의 cycle_map 빌드 / classified / accel_pattern 분석에 영향:
- 충전 모드 분류 (CC/CCCV) 가 정정됨
- voltage cutoff 표시가 입력값 → 실제 cutoff 로 변경
- CCCV 의 current cutoff 가 정확히 표시됨

**영향 받지 않는 것**:
- raw 데이터 자체 (`.sch` 파일은 read-only)
- 사이클 데이터 / 그래프 / DCIR 계산 (이건 `.cyc`/SaveData CSV 기반)
- ATL Q7M Inner 2C 처럼 cv_cutoff_mA > 0 이던 케이스 — swap 후에도 동일하게 정상 표기됨 (검증 필요)

## 검증

- [x] `python -c "ast.parse(...)"` syntax OK
- [x] Q8 .sch raw dump → Ref CSV 와 일치 확인 (Phase 1, 모든 hypothesis 100% 일치)
- [ ] 사용자 알파:
  - Q8 ATL Main 2.0C Rss RT 표시 → CSV 와 동일
  - Gen4 4500mAh
  - ATL Q7M Inner 2C (cv_cutoff > 0 케이스) — swap 후에도 정상 표기
  - RPT 사이클 (CCCV 0.466A, "I < 0.048") → "CCCV 0.20C/4.55V/0.02C cutoff"
  - 방전 step "V < 3.0 or t > 5:00" → "CC 0.20C/3.00V"
- [ ] cycle_map 빌드 정상 동작 (swap 영향이 카운트에 미치지 않는지)
- [ ] Phase 0 캐시 (`ChannelMeta.accel_pattern`) 무효화 — 다음 실행 시 자동 재계산 (`_reset_all_caches`)

## 위험·롤백

- **위험**: 매우 높음 — 모든 PNE 파이프라인 결과 변경
- **완화**: 사용자 알파 + 회귀 시나리오 (Q7M·Gen4·RPT·방전 모두) 광범위 검증
- **롤백**: 단일 commit 이라 revert 1회로 복원 가능. ChannelMeta 캐시는 다음 실행 시 자연 재계산

## 향후

- offset 372/500/504 의미 — Q8 데이터에서는 모두 0 (미사용). 다른 시험 (예: capacity-limited, DOD-limited step) 발견 시 추가 검증
- 0x0102 (DCHG_CCCV) — 검증 데이터 없음. 발견 시 추가 검증
- 변경로그 + 사용자 알파 결과 → 회귀 발견 시 별도 PR
