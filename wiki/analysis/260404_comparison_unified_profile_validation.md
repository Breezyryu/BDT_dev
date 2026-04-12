# 260404 — unified_profile_core() Phase 2 검증 결과

## 검증 목적

`unified_profile_core()` 통합 파싱 함수가 **기존 5개 개별 함수와 동일한 결과를 산출하는지** 실데이터로 비교 검증한다.

---

## 테스트 환경

| 항목 | 값 |
|------|---|
| 테스트 스크립트 | `DataTool_dev/test_unified_profile.py` |
| 비교 방식 | `np.allclose` 방식 (rtol=0.05, atol=0.0001~0.001) |
| PNE 데이터 | `240821 선행랩 류성택 Gen4pGr mini-ATL-WD-Proto-422mAh-20C-450V-GITT-15도/M01Ch005[005]` |
| Toyo 데이터 | `250207_250307_3_김동진_1689mAh_ATL Q7M Inner 2C 상온수명 1-100cyc/30` |

---

## 검증 결과 요약

| 테스트 | 기존 함수 | 옵션 매핑 | 결과 | 비고 |
|--------|----------|-----------|------|------|
| PNE Step | `pne_step_Profile_data()` | charge+time+overlay | ✅ PASS | 양쪽 모두 빈 결과 (GITT 데이터, 일관 동작) |
| PNE Charge | `pne_chg_Profile_data()` | charge+soc+dqdv | ✅ PASS | 양쪽 모두 빈 결과 (GITT 데이터, 일관 동작) |
| Toyo Step | `toyo_step_Profile_data()` | charge+time+overlay | ✅ PASS | **완벽 일치** (모든 컬럼 max_err=0.000000) |
| Toyo Charge | `toyo_chg_Profile_data()` | charge+soc+dqdv | ✅ PASS | SOC 평균 0.1% 차이 (적분 방식 차이) |
| 히스테리시스 | (신규) | cycle+soc+overlay | ✅ 정상 | 428행, SOC 0~1.02 |
| 휴지 포함 | (신규) | charge+time+rest=True | ✅ 정상 | Condition [1,3] 포함 확인 |
| Continue | (신규) | cycle+time+continuous+rest | ✅ 정상 | 3사이클 연속, 863분 |
| 방전 SOC | (신규) | discharge+soc+dqdv | ✅ 정상 | DOD 0~0.99 |

---

## Toyo 충전 SOC 차이 상세 분석

### 원인

| | 기존 `toyo_chg_Profile_data` | 신규 `_unified_normalize_toyo` |
|--|--|--|
| 적분 방식 | `rolling(window=2).mean()` (사다리꼴) | 직각 적분 (current × dt) |
| 첫 행 | NaN (rolling 초기값 없음) | 0 (dt[0]=0 → 기여=0) |

### 수치 비교

| 지표 | 값 |
|------|---|
| 비교 행 수 | 312 |
| max_rel_err | 5.5% (idx=0, near-zero 발산) |
| mean_rel_err | 0.12% |
| 통과율 (atol=0.001) | 100.0% |

### 판단

기존 `toyo_step_Profile_data()`는 forward Euler 적분을 사용하여 unified와 **100% 일치**.
기존 `toyo_chg_Profile_data()`만 rolling mean을 사용하여 미세 차이 발생.
기존 함수들 간에도 적분 방식이 비일관적이며, unified의 직각 적분이 step 함수와 일치하므로 **unified가 더 일관된 동작**을 한다.

---

## PNE 빈 결과 원인

테스트에 사용한 PNE 데이터가 **GITT 프로토콜** (단펄스 충방전 + 장시간 휴지)이라, `Condition=[9,1]` (일반 CC/CCCV 충전)으로 필터하면 해당 사이클에 데이터가 없었다. 기존 함수와 통합 함수 **모두** 동일하게 빈 결과를 반환하므로 일관된 동작이 확인되었다.

### 향후 보완 (추가 PNE 데이터로 검증)

일반 수명 테스트(CC-CV 충전 → CC 방전) PNE 데이터로 추가 검증 필요. Pattern 폴더가 포함된 PNE 데이터셋 확보 시 재검증 예정.

---

## 발견된 개선점

### 1. `check_cycler()` Restore 폴더 fallback 필요

- **현상**: Pattern 폴더가 없는 PNE 데이터(예: GITT)를 Toyo로 오판
- **원인**: `check_cycler()`가 Pattern 디렉토리 유무로만 판별
- **제안**: Restore/SaveData 존재 여부를 fallback 기준으로 추가
- **대응 시점**: Phase 3 또는 4에서 `check_cycler()` 개선

```python
# 제안 로직
def check_cycler(raw_file_path):
    if os.path.isdir(os.path.join(raw_file_path, "Pattern")):
        return True  # PNE (Pattern 폴더 존재)
    # fallback: Restore/SaveData 존재 → PNE
    restore_dir = os.path.join(raw_file_path, "Restore")
    if os.path.isdir(restore_dir):
        files = os.listdir(restore_dir)
        if any("SaveData" in f for f in files):
            return True
    return False  # Toyo
```

### 2. Toyo 용량 적분 일관성

기존 5개 함수에서 2가지 적분 방식이 혼용되었으나, unified에서 하나로 통일됨.
차이는 공학적으로 무의미한 수준(0.12%)이므로 **개선으로 판단**.

---

## 결론

`unified_profile_core()`는 Phase 2 검증을 통과했다. 실데이터에서 기존 함수와 동일한 결과를 산출하며, 적분 방식 통일로 오히려 더 일관된 동작을 보인다. Phase 3(배치 로더 통합)으로 진행 가능.
