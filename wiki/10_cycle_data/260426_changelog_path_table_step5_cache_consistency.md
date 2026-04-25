---
title: "경로 테이블 Step 5 — 행 삭제·경로 변경 시 캐시 일관성"
date: 2026-04-26
tags: [changelog, cycle-data, cache, consistency, ux]
related:
  - "[[260426_changelog_path_table_step2_light_meta|Step 2 light meta 분리]]"
  - "[[260426_changelog_path_table_step4_confirm_progress|Step 4 confirm 진행률]]"
---

# 경로 테이블 Step 5 — 행 삭제·경로 변경 시 캐시 일관성

> **PR #5 / 6** — 사용자 요청 1번 ("기존 기록 삭제, 변경 시 동작") 충족.
> Step 2 에서 분리한 `_path_meta_cache_light` 도 함께 무효화 + 경로 단독 사용 행 정리 시 stale 캐시 정리.

## 배경

Step 2 에서 `_path_meta_cache_light` 인스턴스 캐시를 분리했지만, **삭제·변경 시 무효화 경로** 가 `_reset_all_caches()` (새 데이터 로드 시) 와 `_clear_table()` (전체 초기화) 에 한정.

사용자가 **개별 행 삭제** 또는 **개별 셀 경로 변경** 시 stale 캐시가 다음 confirm 까지 유지되어, 외부에서 폴더 구조가 변경된 경우 재계산이 안 됨. 또한 사용자 요청 1번 의 의도는 "행 삭제·셀 변경 시 자연스럽게 stale 데이터 정리".

## 변경 사항

### 1) `_on_path_cell_changed` (L21953) — 경로 변경 시 light/full 캐시 pop

```python
# ── 이전 경로 캐시 정리 (Step 5: light/full 모두) ──
# 이 행에서만 사용되던 경로면 stale 캐시 정리. 다른 행이 같은 경로를
# 쓰고 있어도 다음 confirm 시 재계산되므로 안전.
if old_path and old_path != new_path:
    # 다른 행에서 같은 경로 사용 여부 확인 (보수적으로 유지)
    still_in_use = any(
        self._get_table_cell(r, 1) == old_path
        for r in range(self.cycle_path_table.rowCount())
        if r != row
    )
    if not still_in_use:
        self._path_meta_cache.pop(old_path, None)
        self._path_meta_cache_light.pop(old_path, None)
```

**핵심**: `still_in_use` 검사 — 다른 행에서 같은 경로를 쓰고 있으면 캐시 pop 하지 않음 (그 행의 다음 조회는 hit 유지). 드물지만 동일 경로 다중 행 시나리오 (ECT 비교 등) 에서 효율 보존.

### 2) `_cycle_table_delete` (L23086) — 행/셀 삭제 시 캐시 정리

```python
def _cycle_table_delete(self):
    """선택 셀 내용 삭제 — col1 경로 삭제 시 메타 캐시도 정리 (Step 5)."""
    self._push_table_undo()
    tbl = self.cycle_path_table
    deleted_paths: set[str] = set()
    for item in tbl.selectedItems():
        # col1 (경로) 삭제 시 캐시 무효화 대상으로 기록
        if item.column() == 1 and item.text():
            deleted_paths.add(item.text())
        item.setText('')
    # 삭제된 경로 중 다른 행에서 더 이상 사용되지 않는 것만 캐시 정리
    if deleted_paths:
        for p in deleted_paths:
            still_in_use = any(
                self._get_table_cell(r, 1) == p
                for r in range(tbl.rowCount())
            )
            if not still_in_use:
                self._path_meta_cache.pop(p, None)
                self._path_meta_cache_light.pop(p, None)
```

- Delete 키로 col1 경로 셀 비울 때 자동 캐시 정리
- col1 만 비워지고 col 0/2/3/4 가 stale 로 남는 케이스도 다음 confirm 시 재계산 → 잘못된 메타 사용 방지

## 동작 변화

**Before**:
- 행에서 경로 A → 경로 B 로 교체 시: A 의 캐시 (light/full 모두) 가 다음 `_reset_all_caches()` 까지 유지
- 행 삭제 시: 셀만 비워지고 캐시 항목은 그대로

**After**:
- 경로 A → B 교체: A 가 다른 행에서 사용 중이 아니면 즉시 pop
- 행 삭제: 동일 정책. 다른 행이 같은 경로 쓰고 있으면 보존

## 안전성

- **다른 행 사용 검사** (`still_in_use`) 로 다중 행 시나리오 보호
- `pop(p, None)` 로 키 없을 때 KeyError 안 남
- 캐시는 Phase 0 (`_reset_all_caches`) 에서 또 한 번 정리되므로 이중 보장

## 검증

- [x] `python -c "ast.parse(...)"` syntax OK
- [ ] 사용자 알파:
  - 경로 A 입력 → 같은 셀에 경로 B 로 교체 → A 의 메타 캐시 사라짐 (직접 확인 시)
  - 행 1: 경로 A, 행 2: 경로 A → 행 1 만 삭제 → A 캐시 보존 (다른 행 사용 중)
  - 행 1: 경로 A, 행 2: 경로 A → 행 1·2 모두 삭제 → A 캐시 정리됨
  - 외부 폴더 구조 변경 후 같은 경로 재입력 → 새로 계산됨 (stale 미사용)
- [ ] perf log: 캐시 hit/miss 비율 확인 — 정상 사용에서 hit rate 유지

## 위험·롤백

- **위험**: 매우 낮음 — 캐시 무효화는 항상 안전 (재계산만 발생)
- **부작용**: 동일 경로 단순 입력·삭제 반복 시 cache hit 손실 가능성 (드문 시나리오, 영향 미미)
- **롤백**: 두 위치의 if 블록 제거 → 5분

## 다음 단계

- **Step 6** (PR #6): paste 헤더 자동 검출 + 연결처리 토글 시 hint 즉시 갱신
