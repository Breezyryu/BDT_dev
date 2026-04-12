# 260405 — test_profile_analysis.py 전체 경로 프로필 분석 테스트 추가

## 배경 / 목적

`unified_profile_core()` 함수가 64개 이상의 실험 데이터 경로에서 모든 옵션 조합(X축, 데이터 범위, 사이클 입력)에 대해 올바르게 동작하는지 체계적으로 검증하기 위한 pytest 테스트 파일을 작성하였다.

기존에는 `test_unified_profile.py`에서 일부 경로/옵션만 수동 검증하였으나, 이번 테스트는 **61개 데이터 엔트리 × 11개 옵션 조합 × 사이클 범위 5종**으로 확장하여 약 1,900건의 테스트 케이스를 자동화하였다.

## 변경 내용

### 신규 파일: `tests/test_profile_analysis.py`

- **61개 실험 데이터 카탈로그** (`ALL_EXP_DATA`): PNE/Toyo 사이클러, 하프셀, GITT, DCIR, 수명, 펄스, 히스테리시스, 율별방전 등 포괄
- **11개 옵션 조합** (`OPTION_COMBOS`): SOC/Time × Charge/Discharge/Cycle × Overlay/Continuous × Rest 포함/제외
- **9개 테스트 클래스**:
  | 클래스 | 검증 내용 |
  |--------|----------|
  | `TestProfileFirstCycle` | 첫 사이클 × 전체 옵션 조합 |
  | `TestProfileMiddleCycle` | 중간 사이클 × 주요 4개 조합 |
  | `TestProfileLastCycle` | 마지막 사이클 + 플롯 생성 검증 |
  | `TestProfileAllCycles` | 전체 사이클 continuous 모드 + 시간 단조증가 |
  | `TestProfilePulseGITT` | GITT/Pulse 전용 (with/without rest) |
  | `TestOptionDependency` | SOC → overlay 강제 규칙 |
  | `TestProfileMetadata` | 메타데이터 필드 완결성 |
  | `TestCyclerDetection` | `check_cycler()` 정확성 |
  | `TestCycleMapValidity` | 사이클 맵 유효성 |

- **물리적 범위 검증** (`validate_profile_result()`):
  - 전압: -0.5V ~ 5.5V
  - 온도: -30°C ~ 100°C
  - SOC: -1.5 ~ 1.5 (단일 사이클 기준)
  - 시간: ≥ 0
  - NaN 비율 < 80%

### 특수 처리

1. **하프셀 SOC 예외**: 용량 < 50 mAh인 하프셀은 SOC 정규화가 달라 SOC 범위 검증 스킵
2. **Continuous 모드 multi-cycle SOC 예외**: 연속 모드에서 여러 사이클 누적 시 SOC가 1.0을 초과하므로 범위 검증 스킵
3. **Headless 환경 대응**: PyQt6 없이 테스트 가능하도록 mock 모듈 주입 패턴 사용
4. **Windows/Linux 경로 호환**: `os.path` 함수 패치로 Windows 경로를 Linux에서 처리

## 테스트 결과

```
1834 passed, 0 failed, 118 skipped (3분 9초)
```

- skipped: 데이터 경로가 존재하지 않거나, GITT 태그에 해당하지 않는 항목
- warnings: 일부 사이클/스코프 조합에서 필터 후 데이터가 비어있는 경우 (정상 동작)

## 영향 범위

- `tests/test_profile_analysis.py` — 신규 파일
- `tests/conftest.py` — `ALL_EXP_DATA` fixture 추가 (테스트 파일 내 자체 포함으로 직접 의존 없음)
- 기존 코드 변경 없음
