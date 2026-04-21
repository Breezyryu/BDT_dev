# 260613 에러 처리 체계 구현 — 사이클/프로파일 파이프라인

## 배경 / 목적

사이클 데이터 탭의 6단계 파이프라인(Phase 0~5)에서 에러 발생 시 전체 앱이 크래시되는 문제가 있었다.
개별 채널이나 사이클에서 에러가 나면 해당 항목만 건너뛰고 나머지는 정상 처리해야 한다.

핵심 목표:
1. **Phase별 에러 격리** — 한 채널/사이클 실패가 다른 데이터에 영향 없음
2. **에러 수집 → 요약 리포트** — 사용자에게 건너뛴 항목 수와 내용 안내
3. **기존 기능 무변경** — 정상 경로에서는 동작 차이 없음

## 변경 내역 (Before / After)

### 1. Phase 0: `_build_all_channel_meta_parallel()` — future.result() 에러 처리

**Before**: `future.result()` 호출 시 예외 발생하면 앱 크래시
**After**: try-except로 개별 채널 실패 포착 → `_meta_errors` 수집 → 로그 경고 + 요약 출력

### 2. `graph_output_cycle()` — 전체 try-except 래핑

**Before**: 6개 서브플롯 렌더링 중 하나라도 실패하면 전체 크래시
**After**: 함수 전체 body를 try-except로 감싸고, 실패 시 `([], '#000000')` 반환 (빈 아티스트 + 기본색)

### 3. `_profile_render_loop()` — 3개 모드 × 2지점 에러 수집

**Before**: CycProfile/AllProfile/CellProfile 모드에서 개별 사이클 플롯 실패 시 전체 루프 중단
**After**:
- `_render_errors = []` 리스트 도입
- 각 모드의 `fallback_fn` 호출과 `plot_one_fn` 호출에 개별 try-except
- 에러 발생 시 `_render_errors`에 항목 추가 + `continue`
- 루프 종료 후 `_render_errors` 요약을 `err_msg()`로 사용자에게 표시

### 4. `unified_cyc_confirm_button()` — 폴더 Phase 에러 격리

**Before**: 탭 생성 또는 전압 조건 분석 실패 시 전체 사이클 분석 중단
**After**:
- `_folder_errors = []` 리스트 도입
- **전압 조건 분석**: 그룹별 개별 try-except (분석 실패해도 탭은 정상 생성)
- **`_finalize_cycle_tab()` 호출**: try-except → 실패 시 fig 닫고 `_folder_errors`에 추가
- 전체 탭 루프 종료 후 `_folder_errors` 요약을 `err_msg()`로 표시

### 5. `metadata["error"]` 체크 — 기존 코드에서 이미 처리됨 확인

- CycProfile/CellProfile: `error_reasons.append(str(_meta.get('error', ...)))` → `_draw_no_data_text` 표시
- AllProfile: `_perf_logger.warning(...)` 로그 출력
- 추가 변경 불필요

## 영향 범위

| 함수 | 파일 라인 (approx) | 변경 유형 |
|------|-------------------|----------|
| `_build_all_channel_meta_parallel` | ~18827 | try-except + `_meta_errors` |
| `graph_output_cycle` | ~2741 | 전체 try-except 래핑 |
| `_profile_render_loop` | ~18079 | 6개 try-except + `_render_errors` + 요약 |
| `unified_cyc_confirm_button` | ~19468 | `_folder_errors` + 전압분석 try-except + finalize try-except + 요약 |

## 에러 리포트 패턴

```python
# 공통 패턴: 에러 수집 → 요약 → 사용자 알림
_errors = []
for item in items:
    try:
        process(item)
    except Exception as e:
        _errors.append(f'{item}: {e}')
        logger.warning('처리 오류: %s — %s', item, e)
        continue

if _errors:
    _n = len(_errors)
    _summary = ', '.join(_errors[:5])
    if _n > 5:
        _summary += f' 외 {_n - 5}건'
    err_msg('일부 오류', f'{_n}건 오류 발생. 정상 데이터는 표시됩니다.\n{_summary}')
```
