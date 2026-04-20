# 히스테리시스 Major 판정 임계값 0.5 → 0.98 상향

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수: `_apply_hysteresis_soc_offsets()` (L23684)

## 배경

히스테리시스 모드에서 `_hyst_type = 'major'` 인 cycle 은 `_get_profile_color('chg_dchg', ..., is_major=True)` 에서 검정(`#333333`)으로 렌더된다 (레인보우 적용 안 됨).

기존 판정: `soc_range > 0.5` → **방전 심도 50% 이상이면 major**.

**실무 문제:** `LWN 25P 0.5C-10min volt hysteresis` 같은 방전 히스테리시스 실험은 cycle 3-12 에서 각각 Dchg 100%/90%/…/10% 심도 방전 → cycle 3-7 (심도 60% 이상) 이 모두 major 판정 → **절반 이상이 레인보우 적용 대상에서 제외되고 검정색**으로 그려짐.

사용자 의도는 "10개 cycle 모두 레인보우로 순차 구별"이므로 현재 임계값이 지나치게 관대.

## 변경

```python
# Before
result_obj._hyst_type = 'major' if soc_range > 0.5 else 'minor'

# After
result_obj._hyst_type = 'major' if soc_range >= 0.98 else 'minor'
```

- `0.98` 임계값 = 충전 0→1 + 방전 1→0 전체 루프 (soc_range ≈ 1.0) 인 "기준 풀 루프"만 major 로 강조.
- `Dchg 100%` (심도 100%) cycle만 major → 레인보우 최하(검정) 색상과도 자연스럽게 연속.
- `Dchg 90%` 이하 (심도 90~10%) 전부 minor → 레인보우 색상 9개 적용.

## 영향

- 방전 히스테리시스 실험의 시각화가 의도대로 복원.
- 충전+방전 풀 사이클만 있는 일반 사이클 분석에서는 여전히 `major` 판정 정상 (range≈1.0 이므로).
- GITT 같이 `Dchg 100%` 가 없는 실험에서는 모든 cycle이 minor 가 됨 — 이전에도 동일 동작.

## 관련 커밋

- `876c9ca` 히스테리시스 레인보우 색상 추가
- `d1aa181` DOD 축 옵션 추가

본 수정은 두 커밋의 레인보우 적용이 방전 히스테리시스 실험에서 실제로 보이도록 하는 보완.

## 사용자 환경 확인 안내

만약 이번 수정 반영 후에도 그래프가 검정으로 나온다면:

1. 사내 로컬에서 실행 파일 확인:
   ```
   - DataTool_dev_code/DataTool_optRCD_proto_.py → 개발판 (이 수정 적용됨)
   - DataTool_260306.py → 프로덕션 (이 수정 미반영 — proto 머지 필요)
   ```
2. 사내 로컬 git 최신화:
   ```bash
   git fetch origin main
   git log HEAD..origin/main --oneline   # 놓친 커밋 확인
   git status                             # unstaged 변경 확인
   git stash && git pull --rebase && git stash pop
   ```
