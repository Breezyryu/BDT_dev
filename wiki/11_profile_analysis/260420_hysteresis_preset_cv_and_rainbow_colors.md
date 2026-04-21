# 히스테리시스 프리셋 CV 포함 + chg_dchg 레인보우 색상

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수: `_apply_profile_preset()` (L23287), `_get_profile_color()` (L3448), 신규 상수 `_HYST_RAINBOW_STOPS` (L3351~)

## 배경 / 사용자 요구

실무 경로 예시:
`260316_260320_05_현혜정_6330mAh_LWN 25P(after LT50cy) 0.5C-10min volt hysteresis`

이 실험은 SOC 10/20/…/100% 각 시작점에서 **0.5C-10min 방전 → rest → 방전** 루틴을 10회 반복한다. 실무자는 cycle 3-12, 14-23 두 구간을 각각 히스테리시스 분석한다 (각 구간 = 10개 방전 곡선, 서로 다른 SOC 영역에서 출발).

사용자 요구:
1. **프리셋 #3 히스테리시스에 CV 포함** — 5ca9d65에서 Rest/CV 둘 다 해제됐으나, CV 필터는 히스테리시스 분석에서 필요(유지 정상 구간 제거).
2. **라인 색상을 이미지처럼** — 단일 시퀀셜 스펙트럼(검정→파랑→청록→녹→노랑→주황→분홍→빨강).

## 현재 vs 변경

### 프리셋 #3 히스테리시스
| 항목 | Before | After |
|---|---|---|
| scope | cycle | cycle |
| overlap | connected | connected |
| axis | SOC | SOC |
| Rest | F | **F** (유지) |
| CV | F | **T** ✅ |
| dQdV | F | F |

Rest 는 사용자 지시가 없어 기본 F 유지.

### chg_dchg 색상 모드

**Before (이중 그라데이션):**
- Major: 검정 `#333333`
- Minor:
  - 충전(condition=1): warm `_WARM_STOPS` (살구→크림슨)
  - 방전(condition=2): cool `_COOL_STOPS` (하늘→남색)
- 문제: 방전 전용 히스테리시스(10개 곡선)에서 모두 `_COOL_STOPS` 하나의 계열만 사용 → 근접 사이클 구별이 어려움.

**After (레인보우 시퀀셜):**
- Major: 검정 `#333333` (유지)
- Minor: `_HYST_RAINBOW_STOPS` 단일 그라데이션, cycle_idx 기반 (condition 무관)

```python
_HYST_RAINBOW_STOPS = [
    (0,   0,   0),    # #000000 검정     — 최고 SOC
    (77,  77,  178),  # #4D4DB2 보라
    (51,  153, 170),  # #3399AA 청록
    (51,  102, 51),   # #336633 짙은녹
    (51,  153, 51),   # #339933 녹
    (153, 204, 102),  # #99CC66 연두
    (255, 153, 51),   # #FF9933 주황
    (255, 136, 102),  # #FF8866 연빨강
    (255, 153, 204),  # #FF99CC 분홍
    (255, 51,  51),   # #FF3333 빨강     — 최저 SOC
]
```

N=10일 때 각 stop이 cycle_idx에 정확히 1:1 매핑되어 이미지와 완전 일치. N≠10일 때는 `_interpolate_stops` 가 자연스럽게 보간.

## 검증

```
=== 3-12cy (10개 방전 히스테리시스) ===
cycle_idx=0  Dchg 100%  #000000 검정
cycle_idx=1  Dchg 90%   #4d4db2 보라
cycle_idx=2  Dchg 80%   #3399aa 청록
cycle_idx=3  Dchg 70%   #336633 짙은녹
cycle_idx=4  Dchg 60%   #339933 녹
cycle_idx=5  Dchg 50%   #99cc66 연두
cycle_idx=6  Dchg 40%   #ff9933 주황
cycle_idx=7  Dchg 30%   #ff8866 연빨강
cycle_idx=8  Dchg 20%   #ff99cc 분홍
cycle_idx=9  Dchg 10%   #ff3333 빨강
```

두 구간(3-12 / 14-23) 모두 각자 10개 cycle 내에서 cycle_idx 0~9를 가지므로 동일한 10색 스펙트럼이 두 번 재생되어 비교 분석이 용이.

## 영향 범위

- `_apply_profile_preset()` 한 줄: 히스테리시스 프리셋 CV=T.
- `_HYST_RAINBOW_STOPS` 신규 상수 10 stops.
- `_get_profile_color()` chg_dchg 분기: `_WARM_STOPS`/`_COOL_STOPS` 분리 → 단일 `_HYST_RAINBOW_STOPS`.
- 기존 warm/cool/dual/distinct/group 모드는 변경 없음.
- 이제 chg_dchg 모드에서 `condition` 인자가 색상에 영향을 주지 않음 (major 판정만 유지).

## 검증 포인트

- [ ] 히스테리시스 프리셋 선택 → CV 체크박스 자동 ON 확인
- [ ] `0.5C-10min volt hysteresis` 경로, cycle 3-12 선택 → 10개 방전 곡선이 검정→빨강 레인보우로 그려지는지 확인
- [ ] cycle 14-23 선택 시 동일 스펙트럼 재생되어 두 구간 비교 용이한지 확인
- [ ] Major loop(전체 SOC 범위 방전)이 검정으로 강조되는지 확인
- [ ] 충/방전 쌍이 모두 있는 히스테리시스(다른 실험) 에서도 cycle 순으로 색상이 진행되는지 확인
