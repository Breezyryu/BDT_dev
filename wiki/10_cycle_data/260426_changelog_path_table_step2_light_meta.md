---
title: "경로 테이블 Step 2 — _resolve_path_meta_light 분리"
date: 2026-04-26
tags: [changelog, cycle-data, performance, refactor]
related:
  - "[[260426_changelog_path_table_step1_cache_patch|Step 1 캐시 패치]]"
  - "[[../31_software_dev/260426_study_lru_cache_principles|lru_cache 원리]]"
---

# 경로 테이블 Step 2 — `_resolve_path_meta_light` 분리

> **PR #2 / 6** — 경로 메타 해석을 IO 없는 light 단계로 분리. Step 3 의 트리거 분리 기반.
> 이 PR 자체로는 동작 변경 없음 (회귀 0) — 새 함수 추가 + 호환 캐시 분리만.

## 배경

Step 1 의 lru_cache 패치로 함수 단위 IO 비용은 줄였지만, **경로 입력 직후엔 채널·TC 정보까지 모두 산출**하는 로직 자체는 그대로. 사용자 요청 3번에 따라 paste·입력 직후엔 **경로명·용량(regex) 만** 즉시 채우고, 무거운 IO 는 confirm 시점에 일괄 처리하도록 트리거를 분리해야 한다.

이를 위해 먼저 메타 해석 함수를 IO 단위로 분해할 필요가 있다.

## 현재 구조 (Step 2 이전)

```
_resolve_path_meta(path)              [DataTool_optRCD_proto_.py:22167]
├─ _path_meta_cache 조회               (인스턴스 캐시)
├─ basename 파싱                       ◯ IO 없음
├─ name_capacity(path)                 ◯ IO 없음 (regex)
├─ XLS/XLSX 분기 → 즉시 반환            ◯ IO 없음
├─ os.path.isdir(path)                 ✗ IO ~10ms
├─ os.scandir(path) for 채널 폴더       ✗ IO 10-50ms
├─ ChannelMeta 캐시 조회 (Phase 0 후)   ◯ IO 0
├─ pne_min_cap / toyo_min_cap 폴백      ✗ IO 100ms-3s (CSV 읽기)
├─ _build_cycle_map_for_path           ✗ IO 100ms-5s
└─ _quick_max_cycle 폴백                ✗ IO (Step 1 캐시)
```

`_path_meta_cache` 단일 dict 가 light·full 결과를 구분 없이 저장 → light 만 필요한 호출자도 full 캐시 miss 시 모든 IO 발생.

## 변경 사항

### 1) `_path_meta_cache_light` 추가 (L22165 부근)

```python
# ── 경로 메타데이터 인스턴스 캐시 ──
# full: scandir + cycle_map 등 IO 결과까지 포함
_path_meta_cache: dict[str, dict] = {}
# light: basename + name_capacity (regex만, IO 0). Step 2 추가.
_path_meta_cache_light: dict[str, dict] = {}
```

두 캐시 분리 → light/full 결과가 서로 간섭하지 않음. light hit 가 full 결과를 가리지 않고, full hit 도 light 결과를 가리지 않음.

### 2) `_resolve_path_meta_light(self, path)` 신규 (L22168~)

```python
def _resolve_path_meta_light(self, path: str) -> dict | None:
    """경로명·용량(regex) 만 산출하는 light 메타 — IO 없음.

    paste·셀 입력 직후 즉시 호출되므로 디스크 IO 0 보장.
    col0(시험명)·col3(용량) 만 채워주고 col2(채널)·col4(TC) 은 비움.
    무거운 IO (scandir, cycle_map 빌드) 는 `_resolve_path_meta` (full) 에서.
    """
    if not path:
        return None
    if path in self._path_meta_cache_light:
        return self._path_meta_cache_light[path]

    # basename 파싱 (IO 0)
    basename = os.path.basename(path)
    auto_name = basename
    if "mAh_" in auto_name:
        auto_name = auto_name.split("mAh_", 1)[1]
    if len(auto_name) > 30:
        auto_name = auto_name[:30] + "..."

    # 용량: 경로명 regex (IO 0)
    _name_cap = name_capacity(path) if "mAh" in path else 0
    auto_cap_str = str(int(_name_cap)) if _name_cap and _name_cap > 0 else ""

    result = {
        'name': auto_name,
        'ch': '',                      # light 미산출
        'cap': auto_cap_str,
        'cycle': '',                   # light 미산출
        '_cap_num': _name_cap or None,
        '_meta_hit': None,
        '_io': False,                  # full 과 구분용 플래그
    }
    self._path_meta_cache_light[path] = result
    return result
```

**키 셋 호환성**: full 결과와 동일 키 (`name`, `ch`, `cap`, `cycle`, `_cap_num`, `_meta_hit`) 모두 포함. light 미산출 항목은 빈 문자열·None. 호출자가 `meta['ch']` 처럼 접근 시 KeyError 발생 X.

`_io: False` 플래그는 디버깅·로깅·향후 분기용 (full 결과는 `_io: True` 추가 가능).

### 3) 캐시 무효화 두 위치에 `_path_meta_cache_light.clear()` 추가

- `_reset_all_caches()` (L800):
  ```python
  WindowClass._path_meta_cache.clear()
  WindowClass._path_meta_cache_light.clear()   # ← 추가
  ```
- `_clear_table()` (L22561):
  ```python
  self._path_meta_cache.clear()
  self._path_meta_cache_light.clear()          # ← 추가
  ```

## 변경하지 않은 것 (의도적)

이번 PR에서는 **호출자 변경 없음**:
- `_autofill_row` (L22305) — 기존 `_resolve_path_meta(path)` 호출 그대로
- `_autofill_table_empty_cells` (L22410) — 그대로
- `_on_path_cell_changed` (L21953) — 그대로
- `_autofill_link_cumulative_hints` (L22454) — 그대로
- `_on_cycle_cell_changed` (L23380) — 그대로

→ 이 PR 단독으로는 동작 변경 0, 회귀 위험 0. light 함수가 호출되는 시점은 Step 3 에서 결정.

## 효과

- **이 PR 단독**: 효과 없음 (light 함수 정의만, 아직 호출되지 않음)
- **Step 3 와 결합**: paste/입력 직후 light 만 자동 → freeze 0
- **Step 4 와 결합**: confirm 시점에 full 자동 → progress 표시

## 검증

- [x] `python -c "ast.parse(...)"` syntax OK
- [ ] light 호출 시 `os.scandir` / `pd.read_csv` 미호출 (mock 또는 perf log)
- [ ] light 결과 dict 키 셋이 full 결과와 동일 (호환성)
- [ ] `_reset_all_caches()` 후 `_path_meta_cache_light` 비어있음
- [ ] `_clear_table()` 후 `_path_meta_cache_light` 비어있음

## 위험·롤백

- **위험**: 매우 낮음. 기존 코드 수정 없이 새 메서드·캐시·무효화 추가만
- **롤백**: 신규 함수·캐시 dict 삭제 + clear 두 줄 제거 → 4분 작업

## 다음 단계

- **Step 3** (PR #3): 호출자에서 light/full 모드 분기 — `_autofill_row(row, *, mode='light'\|'full')`, paste·cellChanged 는 light 만
- **Step 4** (PR #4): `unified_cyc_confirm_button` 진입부에서 full 자동 호출 + statusBar 진행률
