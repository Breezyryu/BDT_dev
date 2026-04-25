# PNE CCCV 단계 판정 보정 — `cv_cutoff=0` 이면 CC 로 표기

날짜: 2026-04-25
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수: `extract_accel_pattern_from_sch()` (L7073+)

## 배경

사용자 보고:
> 동일한 경로 입력에서 PNE 1번 2번 연결처리 그룹의 충방전 패턴 정보가 일부 누락. CCCV 충전 컷오프 전류값 산정 기준을 살펴봐줘.

스크린샷:
```
[Q8 ATL Main 2.0C Rss RT(3ch)]
 ▷ 충전 4step:
   [1st] CCCV 2.0C/4.30V/0.0C cutoff
   [2nd] CCCV 1.65C/4.55V/0.0C cutoff
   [3rd] CC 1.40C/4.30V
   [4th] CC 1.0C/4.55V

[Gen4(6ch)]
 ▷ 충전 4step:
   [1st] CCCV 2.0C/4.30V/0.0C cutoff
   [2nd] CCCV 1.65C/4.50V/0.0C cutoff
   [3rd] CC 1.40C/4.30V
   [4th] CC 1.0C/4.50V

[ATL Q7M Inner 2C 상온수명 301-400c...(6ch)]   (Toyo)
 ▷ 충전 4step:
   [1st] CC 2.0C/4.14V
   [2nd] CC 1.65C/4.16V
   [3rd] CCCV 1.40C/4.30V/1.0C cutoff
   [4th] CCCV 1.0C/4.50V/0.10C cutoff
```

PNE 의 1st/2nd 가 `CCCV ... 0.0C cutoff` — 컷오프 0C 표시. CCCV 는 본래 CV 단계의 전류 cutoff 가 의미있는 값 (예: 0.05C, 0.1C) 이어야 함.

## 산정 로직 추적

### 1. `.sch` 바이너리 파싱 (L6905-6922)

```python
if type_name == 'CHG_CCCV':
    cv_voltage = struct.unpack_from('<f', blk, 28)[0]    # offset 28 = CV 전압 (mV)
    cv_cutoff  = struct.unpack_from('<f', blk, 32)[0]    # offset 32 = CV 컷오프 전류 (mA)
    step_info['cv_voltage_mV'] = cv_voltage
    step_info['cv_cutoff_mA']  = cv_cutoff
```

- IEEE 754 float 로 저장
- `CHG_CC` 타입에는 cv_cutoff_mA 키 없음

### 2. 패턴 dict 변환 (이전, L7078-7090)

```python
entry = {
    'mode': 'CCCV' if s['type'] == 'CHG_CCCV' else 'CC',  # ← type 만으로 결정
    ...
}
if s['type'] == 'CHG_CCCV' and 'cv_cutoff_mA' in s:
    entry['current_cutoff_crate'] = round(s['cv_cutoff_mA'] / capacity, 2)
```

### 3. 화면 포맷 (L7974-7984)

```python
if s['mode'] == 'CCCV':
    return f'[{ord_str}] CCCV {cr}C/{vcut}V/{icut}C cutoff'
return f'[{ord_str}] CC {cr}C/{vcut}V'
```

## 원인

PNE 시험자가 1st/2nd 단계를 `CHG_CCCV` 타입으로 등록하면서 **cv_cutoff = 0 mA** (또는 매우 작음) 로 입력한 경우:

- **시험 의도**: 전압 도달 즉시 다음 step 으로 전환 (CV 단계 사실상 미사용)
- **실질 거동**: CC 모드와 동일
- **다단 충전 빠른 전환 phase** 에서 흔한 패턴 (저항·OCV 측정 사이클의 빠른 충전)

기존 코드는 type_code 만으로 CCCV 표기 → `0.0C cutoff` 가 그대로 출력되어 사용자에게 정보 누락처럼 보임.

`round(0 / 2369, 2) = 0.0` → **0.0C cutoff** 표시 (수치적으로는 정확한 변환).

Toyo 의 Q7M 은 시험자가 명시적으로 cv_cutoff=1.0C / 0.10C 를 입력했기 때문에 정상 표시.

## 수정

CCCV 판정에 **임계값 1mA** 추가:

```python
_CCCV_MIN_CUTOFF_MA = 1.0
...
_cv_cut_mA = s.get('cv_cutoff_mA', 0)
_is_real_cccv = (s['type'] == 'CHG_CCCV'
                 and _cv_cut_mA >= _CCCV_MIN_CUTOFF_MA)
entry = {
    'mode': 'CCCV' if _is_real_cccv else 'CC',
    'crate': round(cur_mA / capacity, 2) if capacity else 0,
    'current_mA': cur_mA,
    'voltage_cutoff': round(v_cutoff, 3),
}
if _is_real_cccv:
    entry['current_cutoff_crate'] = (
        round(_cv_cut_mA / capacity, 2) if capacity else 0
    )
    entry['current_cutoff_mA'] = _cv_cut_mA
```

### 임계값 1mA 의 근거

- 일반적 CV cutoff 는 0.05C ~ 0.1C 수준 (cells 의 capacity 에 따라 수십 ~ 수백 mA)
- 1mA 미만이면 **시험자 미입력 또는 의도적 0** 으로 안전 가정
- capacity 무관 (절대 mA 임계) — round 단계 전이라 표시 정밀도와 독립

## 동작 변화

### Q8 ATL Main 2.0C Rss RT (capacity 2369mAh)

| step | type | cv_cutoff_mA | Before | After |
|---|---|---|---|---|
| 1st | CHG_CCCV | 0.0 | CCCV 2.0C/4.30V/0.0C cutoff | **CC 2.0C/4.30V** |
| 2nd | CHG_CCCV | 0.0 | CCCV 1.65C/4.55V/0.0C cutoff | **CC 1.65C/4.55V** |
| 3rd | CHG_CC | (없음) | CC 1.40C/4.30V | CC 1.40C/4.30V (불변) |
| 4th | CHG_CC | (없음) | CC 1.0C/4.55V | CC 1.0C/4.55V (불변) |

### Toyo Q7M (영향 없음)

Toyo 는 별도 경로 (`extract_toyo_ptn_structure`) 사용 — 이번 수정과 무관. 기존 표시 그대로:
- [3rd] CCCV 1.40C/4.30V/1.0C cutoff
- [4th] CCCV 1.0C/4.50V/0.10C cutoff

## 영향 범위

- `extract_accel_pattern_from_sch` 의 charge_steps 변환 부분만 수정 (5줄 추가)
- discharge_steps 변환은 불변 (방전은 보통 CC)
- Toyo 경로 영향 없음
- 의미있는 cv_cutoff (≥ 1mA) 는 기존과 동일하게 CCCV 표기 + cutoff 값 표시

## 검증 포인트

- [ ] PNE Q8 / Gen4 / T23 → 1st/2nd 가 **CC** 로 표기 (cutoff 텍스트 사라짐)
- [ ] PNE 다른 시험에서 진짜 CCCV (cv_cutoff > 1mA) 는 기존처럼 `CCCV ... XXC cutoff` 표시
- [ ] Toyo 시험 표기 불변 (Q7M 패턴)
- [ ] 패턴 시그니처 (`_pattern_signature`) 에서 그룹 동일성 비교 영향 — CC 로 통일되므로 같은 시험은 그대로 같음
- [ ] 채널 상태 분류·라벨에 영향 없음 (mode 변경은 표시상)

## 후속 (선택)

만약 사용자가 "CCCV 표기는 유지하되 cutoff=0 인 경우 명시적 표기" 를 원하면 다음 옵션 고려:
- CC 가 아니라 `CCCV-V` (V 도달 즉시 종료) 같은 별도 라벨
- 또는 `CCCV 2.0C/4.30V (V-only)` 처럼 부가 텍스트

이번 PR 은 가장 안전한 "CC 표기" 로 단순화. 필요 시 별도 PR.
