# CV 체크박스 해제 시 충전 프로파일에서 CV 구간이 제거되지 않는 버그 수정

## 배경 / 목적

사용자 보고: "CV 체크박스를 해제해도 충전 프로파일에서 CV 구간이 제거가 안된다."

원인 분석 결과 두 가지 문제가 중첩되어 있었음:

1. **`include_cv` 전달 누락** — `unified_profile_batch`의 continuous 분기(L2719)·`unified_profile_batch_continue`(L2836)·`_fallback` 5개 경로가 `unified_profile_core`에 `include_cv`를 전달하지 않아 기본값(`True`)으로 고정. 체크박스 해제가 해당 경로에서 무시됨.
2. **Stepmode 기반 필터의 취약성** — 기존 `_unified_filter_condition`은 SaveEndData `col[1]=Stepmode==1` (CC-CV) 스텝만 전압 플래토 검출 대상으로 삼았음. `.cyc` 보충 행이나 Stepmode 매핑이 불완전한 스케쥴에서는 Stepmode가 기본값(2=CC)으로 채워져 CV 검출이 건너뜀.

## 변경 내용

### 1) `_unified_filter_condition` CV 필터 견고화

**Before** (Stepmode에만 의존)

```python
if not include_cv and len(filtered) > 0 and "Stepmode" in filtered.columns:
    # (a) Stepmode=3 전체 제외
    # (b) Stepmode=1 레코드 단위 전압 플래토 제외
    ...
```

**After** (전압 기반 기본, Stepmode는 보조)

```python
if not include_cv and len(filtered) > 0:
    # (a) Stepmode=3 (순수 CV) 스텝 전체 제외 — Stepmode 있을 때만
    # (b) 충전(Condition=1) 레코드의 전압 플래토(step_max - 5mV 이상) 제외
    #     — Stepmode 무관 적용, 단 Stepmode=2 (순수 CC)는 사용자 의도로 제외
```

**물리 근거**: CV 단계는 설정 전압을 정전압 유지 → 스텝 내 실측 최대 전압 = CV 설정 전압. 이 값에 측정 노이즈(5mV)를 뺀 임계를 CC/CV 경계로 삼음. Stepmode 정보 없이도 동작.

### 2) `include_cv` 파이프라인 관통

다음 6개 호출 지점에 `include_cv`를 명시 전달:

| 위치 | 함수 | 비고 |
|------|------|------|
| L2721 | `unified_profile_batch` continuous 분기 | 기존 누락 (신규 추가) |
| L2789 | `unified_profile_batch_continue` 시그니처 | 파라미터 추가 (기본 `True`) |
| L2839 | `unified_profile_batch_continue` → `unified_profile_core` | 신규 전달 |
| L19190 | `_load_unified_batch_task` → `unified_profile_batch_continue` | 신규 전달 |
| L23902/23960/24014/24174/24311 | 5개 `_fallback` 경로 | 신규 전달 |

## 영향 범위

- 충전·방전 프로파일 (`data_scope=charge/discharge`): CV 체크박스가 이제 항상 정확히 반영됨. 특히 `.cyc`만 있고 SaveEndData가 불완전한 채널에서 동작 회복.
- Continue 모드 (`overlap=continuous`): CV 체크박스가 신규 반영됨 (기존에는 강제 True였음).
- 순수 CC 스텝(`Stepmode=2`): 기존대로 보존 — 사용자가 CC-only로 구성한 스텝의 마지막 레코드가 부당하게 제거되지 않음.
- 방전 프로파일: 필터는 `Condition==1`(충전)만 대상이므로 방전 레코드 영향 없음.

## 관련 커밋 기능 맥락

- 260418 `[도구추가] 프로파일 스테이지 스냅샷 유틸` — 동일 파이프라인에 Stepmode 기반 필터가 도입됨
- 본 변경은 위 필터의 **견고화 (heuristic fallback 추가)** 및 **파라미터 관통 누락 일괄 해결**
