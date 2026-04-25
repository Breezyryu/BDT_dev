---
title: "경로 테이블 Step 6 — paste 헤더 자동 검출 + 연결처리 토글 즉시 hint"
date: 2026-04-26
tags: [changelog, cycle-data, paste, ux, link-mode]
related:
  - "[[260426_changelog_path_table_step3_trigger_split|Step 3 트리거 분리]]"
  - "[[260426_changelog_path_table_step4_confirm_progress|Step 4 confirm 진행률]]"
---

# 경로 테이블 Step 6 — paste 헤더 자동 검출 + 연결처리 토글 즉시 hint

> **PR #6 / 6** — 6 PR 시리즈의 마지막. 사용자 요청 5번 (paste 강화) + 2번 (연결처리 토글 동작) 충족.

## 배경

이번 PR 은 두 개의 작은 UX 개선을 묶음:

1. **paste 헤더 자동 검출**: 사용자가 엑셀에서 헤더 포함 영역을 복사·붙여넣기 시 헤더 행이 데이터로 들어가 첫 행이 깨지는 케이스 방지
2. **연결처리 토글 즉시 hint**: `chk_link_cycle` 체크박스 토글 시 그룹 구분선만 갱신되고 TC 누적 hint 는 다음 confirm 까지 갱신 안 됨 → 토글 즉시 cache hit 행만 hint 갱신

## 변경 사항

### 1) `_cycle_table_paste` 헤더 자동 검출 (L23015)

**상수**:
```python
_PASTE_HEADER_TOKENS = frozenset({
    # 한글 (테이블 헤더)
    '시험명', '경로', '채널', '용량', 'tc', '모드',
    '경로(필수입력)', '경로(필수)',
    # 영문 (path 파일 헤더 / 외부 엑셀)
    'pathname', 'path', 'ch', 'channel', 'capacity', 'cycle', 'mode',
    'name',
})
```

**검출 로직**:
```python
# 첫 줄을 탭으로 split 했을 때 비어있지 않은 토큰이 2개 이상이고
# 모두 _PASTE_HEADER_TOKENS 에 포함되면 헤더로 간주하고 skip.
# 2 토큰 이상 조건: 단일 셀 paste ("TC" 등 단일 키워드) 의 오탐 방지.
if raw_lines:
    first_tokens = [t.strip().lower() for t in raw_lines[0].split('\t')]
    non_empty = [t for t in first_tokens if t]
    if (len(non_empty) >= 2
            and all(t in self._PASTE_HEADER_TOKENS for t in non_empty)):
        raw_lines = raw_lines[1:]
```

**핵심 안전장치**:
- `len(non_empty) >= 2` — 단일 셀 paste 가 헤더 키워드여도 데이터로 처리 (사용자 의도 보존)
- `all(...)` — 일부만 매치되면 데이터 행으로 처리 (혼합 패턴 보호)
- `lower()` 비교 — TC/tc/Tc 모두 동일 처리

**검출 케이스 예시** (모두 헤더 → skip):
```
시험명	경로	채널	용량	TC	모드
pathname	path	ch	capacity	cycle	mode
경로(필수입력)	채널	용량	TC
```

**비검출 케이스 예시** (모두 데이터로 처리):
```
2335mAh_Q8	C:\path\to\data	1,2	2335	1-300	CYC
TC                                 # 단일 토큰
경로	내가직접쓴값	2	100	1-50	CYC  # "내가직접쓴값" 미매치
```

### 2) `_autofill_link_cumulative_hints` 에 `cache_only` 매개변수 추가 (L22556)

```python
def _autofill_link_cumulative_hints(self, *, cache_only: bool = False):
    """...
    cache_only : bool
        True 면 _path_meta_cache (full) 캐시 hit 인 경로만 사용 (IO 0).
        연결처리 토글 시그널에서 즉시 hint 갱신용 (Step 6).
        False (기본): 기존 동작.
    """
    ...
    for rr in range(r, tbl.rowCount()):
        ...
        # cache_only: cache hit 만 사용 (IO 0).
        if cache_only:
            m = self._path_meta_cache.get(pp) if pp else None
        else:
            m = self._resolve_path_meta(pp) if pp else None
```

- `cache_only=False` (default) → 기존 호출자 (`_autofill_table_empty_cells` 내부) 영향 없음
- `cache_only=True` → 토글 시그널에서 IO 0 보장

### 3) `chk_link_cycle.toggled` 시그널에 hint 갱신 추가 (L17660)

```python
# 연결처리 토글 시 그룹 구분선 + TC 누적 hint 즉시 갱신 (Step 6)
# cache_only=True 로 호출하여 캐시 hit 행만 즉시 갱신 (IO 0).
# cache miss 행은 다음 confirm 시 full IO 후 자연스럽게 채워짐.
self.chk_link_cycle.toggled.connect(self._update_group_separators)
self.chk_link_cycle.toggled.connect(
    lambda _checked: self._autofill_link_cumulative_hints(
        cache_only=True))
```

기존 `_update_group_separators` 연결은 유지. 추가로 `_autofill_link_cumulative_hints(cache_only=True)` 람다 연결.

## 동작 시나리오

**Before** (Step 5 까지):
1. 엑셀에서 헤더 포함 6×5 영역 복사
2. 테이블에 paste → 첫 행에 "시험명/경로/채널/..." 텍스트 들어감 (잘못)
3. 사용자가 첫 행 직접 삭제 필요
4. 연결처리 토글 → 그룹 구분선만 변함, TC 누적 hint 는 그대로

**After** (Step 6):
1. 엑셀에서 헤더 포함 6×5 영역 복사
2. 테이블에 paste → 헤더 자동 skip, 5개 데이터 행만 입력 ✓
3. 연결처리 토글 → 그룹 구분선 + TC 누적 hint 즉시 갱신 (cache hit 행만, IO 0)

## 검증

- [x] `python -c "ast.parse(...)"` syntax OK
- [ ] 엑셀에서 헤더 포함 paste → 헤더 행 skip 확인
- [ ] 단일 셀 paste ("TC" 등) → 데이터로 처리 (skip 안 됨) 확인
- [ ] 일부만 헤더 키워드인 paste → 데이터로 처리 확인
- [ ] 연결처리 토글 → 그룹 구분선 + TC 누적 hint 즉시 변경
- [ ] cache miss 행 (paste 직후 light only) 은 hint 갱신 보류 → 다음 confirm 후 자연스럽게 채워짐

## 위험·롤백

- **위험**: 매우 낮음 — 두 변경 모두 새 기능 추가, 기존 동작 보존
- **롤백**:
  - 헤더 검출: `if raw_lines:` ~ `raw_lines = raw_lines[1:]` 블록 제거 (10줄)
  - 토글 hint: `chk_link_cycle.toggled.connect(lambda...)` 추가 라인 제거 (3줄)

## 6 PR 시리즈 완료 — 사용자 요청 매핑 검토

| 요청 | 처리 PR | 결과 |
|---|---|---|
| 1. 기존 기록 삭제·변경 시 동작 | Step 5 | ✅ light/full 캐시 정리 + still_in_use 보존 |
| 2. 연결처리 온/오프 | Step 6 | ✅ 토글 즉시 hint 갱신 (IO 0) |
| 3. 경로 입력 시 경로명·용량값만 | Step 2+3 | ✅ light 자동, full 은 confirm 시점 |
| 4. 채우기 기능 사용 시 채널·TC | Step 4 | ✅ confirm 진입 자동 full + statusBar 진행률 |
| 5. 다중 행/열 paste | Step 6 | ✅ 헤더 자동 검출 (기존 paste 다중 행/열 지원과 결합) |
| (보너스) 캐시 누락 패치 | Step 1 | ✅ check_cycler·_quick_max_cycle lru_cache |

## 향후 확장 (별도 PR)

- **B안 (비동기 QThread Worker)** — A안 사용자 알파 후 효과 부족 시 도입
- **per-row spinner 아이콘** — 행 단위 진행 표시 (statusBar 만 우선)
- **paste 헤더 추가 정규화** — `_HEADER_ALIASES` (L22566+) 와 통합하여 한글·영문 모두 매핑 강화
