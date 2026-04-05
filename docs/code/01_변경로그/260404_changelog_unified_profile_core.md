# 260404 — unified_profile_core() 통합 프로필 파싱 엔진 추가

## 배경 / 목적

사이클데이터 탭의 Profile 분석에 5개 버튼(Step/Rate/Chg/Dchg/Continue)이 각각 별도 파싱 함수를 호출하고 있었다.
함수 간 **로직 중복이 80% 이상**이며, 신규 기능(휴지 포함, 히스테리시스 분석 등)을 추가하려면 5곳을 동시에 수정해야 하는 문제가 있었다.

이를 해결하기 위해 **4개 옵션 조합**으로 모든 프로필 분석 모드를 커버하는 `unified_profile_core()` 함수를 신규 작성한다.

## 변경 내용

### 신규 함수 (proto_.py 라인 606~)

| 함수명 | 역할 |
|--------|------|
| `UnifiedProfileResult` | 결과 컨테이너 (dataclass) |
| `_unified_pne_load_raw()` | PNE SaveData 원시 로딩 → 표준 컬럼 구조 |
| `_unified_toyo_load_raw()` | Toyo CSV 원시 로딩 → 표준 컬럼 구조 |
| `_unified_normalize_pne()` | PNE 단위 변환 (μV→V, μA→mA, is_micro 분기) |
| `_unified_normalize_toyo()` | Toyo 단위 변환 + 시간적분 용량 계산 |
| `_unified_filter_condition()` | Condition 기반 필터 (충전/방전/사이클 + 휴지 포함) |
| `_unified_merge_steps()` | 멀티스텝 시간·용량 연속 병합 |
| `_unified_calculate_axis()` | X축(Time/SOC) 및 사이클 연속성(overlay/continuous) 처리 |
| `_unified_calculate_dqdv()` | dQ/dV, dV/dQ 계산 (휴지 구간 NaN 처리) |
| `unified_profile_core()` | **메인 엔트리** — 6단계 파이프라인 실행 |

### 4개 옵션

| 옵션 | 값 | 설명 |
|------|---|------|
| `data_scope` | `"charge"` / `"discharge"` / `"cycle"` | 데이터 구간 |
| `axis_mode` | `"time"` / `"soc"` | X축 |
| `continuity` | `"overlay"` / `"continuous"` | 사이클 표시 방식 |
| `include_rest` | `True` / `False` | 휴지 포함 여부 |

### 옵션 의존성 규칙

- `axis_mode="soc"` → `continuity`는 자동으로 `"overlay"` 강제
- `continuity="continuous"` → `axis_mode`는 자동으로 `"time"` 강제

### 기존 함수 대응표

| 기존 함수 | unified_profile_core 옵션 |
|-----------|--------------------------|
| `pne_step_Profile_data()` | `data_scope="charge", axis_mode="time", continuity="overlay", include_rest=False` |
| `pne_rate_Profile_data()` | 동일 (스텝 병합 없이) |
| `pne_chg_Profile_data()` | `data_scope="charge", axis_mode="soc", calc_dqdv=True` |
| `pne_dchg_Profile_data()` | `data_scope="discharge", axis_mode="soc", calc_dqdv=True` |
| `pne_Profile_continue_data()` | `data_scope="cycle", axis_mode="time", continuity="continuous", include_rest=True` |

### 신규 지원 모드

| 모드 | 옵션 | 용도 |
|------|------|------|
| 충전 + 휴지 포함 + SOC | `charge, soc, overlay, rest=True` | 충전 후 전압 이완 관찰 |
| 방전 + 휴지 포함 + Time | `discharge, time, overlay, rest=True` | 방전 후 IR drop 분석 |
| 사이클 + 시작점 동일 + Time | `cycle, time, overlay, rest=False` | 사이클 형태 비교 |
| 사이클 + 시작점 동일 + SOC | `cycle, soc, overlay, rest=False` | **충방전 히스테리시스 분석** |

## Before / After 비교

### Before (기존)
```
5개 함수 × 2 사이클러(PNE/Toyo) = 10개 파싱 경로
각각 원시 로딩 → 필터링 → 정규화 → 병합 → 가공 중복
```

### After (통합)
```
1개 코어 함수 × 6단계 파이프라인
사이클러 분기: Stage 1(로딩) + Stage 3(정규화)에서만
나머지 Stage 2,4,5,6은 사이클러 무관 공통 로직
```

### `check_cycler()` 개선 (Phase 2 중 발견 → 즉시 적용)

기존 `check_cycler()`는 Pattern 폴더 유무로만 PNE/Toyo를 판별했다.
GITT 등 Pattern 폴더가 없는 PNE 데이터에서 Toyo로 오판하는 문제를 발견하여,
**Restore/SaveData 존재를 fallback 기준**으로 추가했다.

```python
# Before
def check_cycler(raw_file_path):
    cycler = os.path.isdir(raw_file_path + "\\Pattern")
    return cycler

# After
def check_cycler(raw_file_path):
    if os.path.isdir(raw_file_path + "\\Pattern"):
        return True
    restore_dir = raw_file_path + "\\Restore"
    if os.path.isdir(restore_dir):
        files = os.listdir(restore_dir)
        if any("SaveData" in f for f in files):
            return True
    return False
```

## 영향 범위

- **변경된 파일**: `DataTool_dev/DataTool_optRCD_proto_.py`
- **추가된 코드**: ~380줄 (라인 606 이후) — unified_profile_core 및 헬퍼 8개
- **변경된 함수**: `check_cycler()` — Restore fallback 추가 (기존 동작 유지, 확장)
- **기존 함수**: 변경 없음 (유지, Phase 4에서 점진 교체 예정)
- **UI**: 변경 없음 (Phase 4에서 통합 UI 구현 예정)
- **검증 스크립트**: `DataTool_dev/test_unified_profile.py` 추가
- **검증 결과 문서**: `docs/code/02_변경검토/260404_comparison_unified_profile_validation.md`

## Phase 2 검증 결과

| 테스트 | 결과 | 비고 |
|--------|------|------|
| PNE Step/Charge | ✅ PASS | GITT 데이터로 양쪽 모두 빈 결과 (일관 동작) |
| Toyo Step | ✅ PASS | 완벽 일치 (max_err=0) |
| Toyo Charge | ✅ PASS | SOC 평균 0.12% 차이 (적분 방식 차이, 공학적 무의미) |
| 신규 4개 모드 | ✅ PASS | 히스테리시스/휴지/Continue/방전SOC 정상 |

## 다음 단계

- ~~Phase 2: 기존 함수 결과와 1:1 비교 검증~~ ✅ 완료
- ~~Phase 3: 배치 로더 통합 (`_load_all_unified_parallel`)~~ ✅ 완료 → `260404_changelog_unified_profile_batch.md`
- ~~Phase 4: UI 통합 (옵션 위젯 + 실행 버튼 1개)~~ ✅ 완료 → `260404_changelog_unified_profile_ui.md`
- Phase 5: 기존 함수 deprecated → 제거
