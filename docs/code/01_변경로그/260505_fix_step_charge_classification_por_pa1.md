# 스텝충전 사이클 분류 분리 — `STEP_CHG` 신설 + `CHG_DCHG` → '사이클' 매핑

날짜: 2026-05-05
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수/맵:
- `_classify_loop_group` (L8378 근처) — STEP_CHG 룰 신규
- `_SCH_CAT_TO_NEW` (L5857 근처) — CHG_DCHG 매핑 변경 + STEP_CHG 추가
- `CATEGORY_LABELS` (L5821 근처) — '사이클(스텝충전)' 라벨 추가
- `_CLASSIFIED_COLORS` (L9700 근처) — 색상/desc 추가
- `_LCG_CATEGORY_MAP` (L6316 근처) — LCG 그룹 매핑 보강

## 사용자 보고

```
경로: 260211_260310_05_문현규_3885mAh_POR 40C pulse PA1 SDI
사이클 분류 시, TC 25-90 가 0.2C 충방전으로 인식된다
스텝충전 사이클도 포함되어있다.
V2보다 V3 분류가 더 이상하다
```

## 원인

`_SCH_CAT_TO_NEW` 의 `CHG_DCHG` 매핑이 잘못된 라벨로 떨어짐:

```python
# Before (V2/V3 동일)
'RPT':       ('RPT', None),         # 라벨: 'RPT (0.2C 충방전)'
'CHG_DCHG':  ('RPT', None),         # ← 일반 1회 충방전인데 '0.2C 충방전' 라벨이 붙는다 (잘못)
```

`_classify_loop_group` 의 룰 체인:

1. RPT (line 8370): `N==1 + chg+dchg + 모든 currents ≈ 0.2C (±30%)` — 진짜 0.2C 만 매칭
2. **CHG_DCHG (line 8378): `N==1 + chg+dchg`** — RPT 에 안 걸린 모든 N=1 충방전을 흡수

POR/PA1/스텝충전 시험은:
- 충전이 **multi-step CC** (예: 0.7C → 1C → 1.5C → 2C 단차) — 0.2C 가 아님
- 방전이 일반 (0.5C 등) — 0.2C 가 아님
- 한 사이클이 .sch 에서 N=1 loop 로 표현되는 케이스가 흔함

→ RPT 룰 (15) 통과 못함 → CHG_DCHG (16) 매칭 → `('RPT', None)` → "RPT (0.2C 충방전)" 라벨.

`POR 40C pulse PA1 SDI` 의 TC25-90 (66 cycle 분량 step charge cycle 들) 이 모두 `0.2C 충방전` 으로 표시되는 것은 이 매핑 버그 때문.

V2/V3 양쪽 모두 같은 매핑을 가지므로 V2 도 사실상 같은 문제가 있었지만, V3 의 다른 변경 (RSS_DCIR 우선순위, ACCEL mid-range, ref_step 일반화) 이 일부 케이스에서 라벨링 경로를 바꿔 사용자가 V3 가 더 나쁘다고 체감한 것으로 보임. 본질은 매핑 잘못.

## 변경 1 — STEP_CHG 룰 신설

`_classify_loop_group` 에 RPT 와 CHG_DCHG 사이 룰 추가:

```python
# 15b. STEP_CHG — Phase 0-5 v3+ (260505): N=1, multi-step CHG (≥2 단차) + DCHG.
# 사용자 보고 (POR 40C pulse PA1 SDI): TC25-90 step-charge cycle 들이 V3 에서
# CHG_DCHG → 'RPT (0.2C 충방전)' 으로 잘못 라벨링.
# 도메인: 단차 충전 (예: 0.7C → 1C → 1.5C → 2C 으로 V 단계 별 변경) 은
# RPT (단일 0.2C) 와는 명확히 구분되는 충전 프로토콜. 실제 currents 가
# 0.2C 가 아닌데도 CHG_DCHG fallback 으로 RPT 라벨이 붙어 사용자 혼동.
# 다단 charge 가 있고 RPT (15) 에 안 걸렸다 = currents 가 0.2C 아님 = STEP_CHG.
if N == 1 and len(chg_steps) >= 2 and dchg_steps:
    return 'STEP_CHG'
```

조건:
- `N == 1` (단일 loop iteration)
- `len(chg_steps) >= 2` (단차 충전 = 다중 CC 스텝)
- `dchg_steps` (방전 동반)

이 룰은 RPT (15) **다음** 에 위치하므로 진짜 0.2C 사이클은 여전히 RPT 라벨을 받는다 (RPT 가 먼저 매칭).

## 변경 2 — `_SCH_CAT_TO_NEW` 매핑 정정

```python
# Before
'CHG_DCHG':  ('RPT', None),          # 일반 1회 충방전 → RPT 취급

# After (260505 fix)
'CHG_DCHG':  ('사이클', None),        # 일반 1회 충방전 → '사이클' (RPT=0.2C 충방전 라벨 분리)
'STEP_CHG':  ('사이클', '스텝충전'),  # 신규: N=1 multi-step CHG + DCHG
```

→ CHG_DCHG (단일 step 의 일반 충방전) 도 더 이상 "RPT (0.2C 충방전)" 라벨이 붙지 않고 일반 '사이클' 로 분류.

## 변경 3 — 라벨 / 색상

`CATEGORY_LABELS`:
```python
'사이클(스텝충전)': '사이클 (스텝 충전)',  # 260505: N=1 multi-step CHG + DCHG (POR/PA1 등)
```

`_CLASSIFIED_COLORS`:
```python
'사이클(스텝충전)':  {'color_idx': 0, 'desc': '사이클 (스텝 충전)'},  # 260505: POR/PA1 등
```

→ 사이클 계열 색 (네이비) 으로 통일. ACCEL 가속수명과 시각적 구분되지 않지만 같은 사이클 류 그룹임을 시사.

`_LCG_CATEGORY_MAP`:
```python
'사이클': ('accel', '사이클'),
'사이클(FORMATION)': ('formation', '화성'),
'사이클(ACCEL)': ('accel', '가속수명'),
'사이클(스텝충전)': ('accel', '스텝충전'),
```

→ 신 카테고리들이 LCG 그룹으로 깔끔히 매핑되도록 보강 (이전엔 `unknown` 으로 폴백).

## 사용자 시나리오 — Before / After

### Before
```
경로: 260211_..._POR 40C pulse PA1 SDI
TC 25-90: 'RPT (0.2C 충방전)'  ← 잘못 (실제는 step-charge cycle)
```

### After
```
경로: 260211_..._POR 40C pulse PA1 SDI
TC 25-90:
  - .sch 가 N=1 loop × 다수 + multi-step chg → '사이클 (스텝 충전)' (STEP_CHG)
  - .sch 가 N≥20 loop + multi-step chg → '사이클 (가속수명)' (ACCEL strong, 기존 매칭)
  - .sch 가 N=1 loop + 단일 chg step → '사이클' (CHG_DCHG, 신 라벨)
실제 0.2C RPT (TC1-? 등): 'RPT (0.2C 충방전)' (변화 없음)
```

## 호환성

- 기존 `RPT` 카테고리 (line 8370 의 0.2C ±30% 룰) 는 그대로 → 진짜 RPT 사이클은 동일 라벨 유지.
- `CHG_DCHG` 사용처 (`_finalize_hyst_envelope_absorption` 의 envelope 흡수 등) 는 카테고리 이름 'CHG_DCHG' 자체로 비교하므로 영향 없음. 사용자에게 보이는 라벨만 변경됨.
- 기존 분석 결과 캐시: 라벨이 바뀌므로 사용자가 재실행해야 새 라벨 보임.

## 검증 (사용자)

1. 앱 재시작 (코드 재로드)
2. `260211_260310_05_문현규_3885mAh_POR 40C pulse PA1 SDI` 경로 입력
3. 사이클 분류 결과 확인:
   - TC25-90 이 더 이상 `RPT (0.2C 충방전)` 으로 표기되지 않음
   - 대신 `사이클 (스텝 충전)` 또는 `사이클 (가속수명)` 또는 `사이클` 중 하나로 표기
4. 다른 시험 (RPT 가 실제로 있는 시험) 에서 TC1-?의 RPT 라벨은 그대로 유지되는지 확인

## 별건 — V2 vs V3 차이 분석 (참고)

사용자가 "V2보다 V3 분류가 더 이상하다" 고 보고한 데에는 다음 V3 변경의 부수효과가 영향했을 수 있음:

| V3 변경 | 영향 |
|--------|------|
| `RSS_DCIR` 우선순위 변경 + `has_short_dchg` 가드 | 짧은 펄스 있는 케이스에서 RSS_DCIR 미매칭 → 다른 룰로 흘러감 |
| `HYSTERESIS_DCHG/CHG` ref_step 일반화 | 임의 ref_step 매칭 시 hysteresis 라벨 가능 (POR 와 무관할 수도 있음) |
| `ACCEL` N=11~19 mid-range (chg≥3) | N=11~19 + chg=2 케이스는 여전히 미매칭 |
| `PULSE_DCIR` (DCHG_CCCV mode=0) | 일부 케이스에서 PULSE_DCIR 라벨 |

본 fix 로 CHG_DCHG → '사이클' 매핑이 바뀌면, 위 V3 변경들이 도메인에 더 잘 맞게 되어 V2 보다 정확한 라벨링이 될 가능성이 높다. 다만 사용자가 .sch 를 공유하면 추가 검증 가능.

## 적용 파일

- `C:\Users\Ryu\battery\python\BDT_dev\DataTool_dev_code\DataTool_optRCD_proto_.py` (main, 사용자 테스트 환경)
- `C:\Users\Ryu\battery\python\BDT_dev\.claude\worktrees\stoic-agnesi-bd7997\DataTool_dev_code\DataTool_optRCD_proto_.py` (worktree)
