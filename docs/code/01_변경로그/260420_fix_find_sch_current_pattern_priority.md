# `.sch` 선택 규칙 수정 — 접미사 없는 원본(현재 패턴) 우선

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수: `_find_sch_file()` (L7344)

## 배경 / 문제

사용자 보고:
> "원인은 해당 path 에 sch 파일이 2개 있어서 그런 것 같다.
> 충방전 시험 도중 패턴을 변경 업데이트 하면 sch 파일이 하나 더 생긴다.
> 파일명 뒤에 _000 이 추가된다.
> 수정 날짜 기준으로는 ~~.sch가 더 최근이고, --_000.sch 가 더 나중이다.
> 패턴을 중간에 변경 업데이트 하면, 이전 패턴 버전은 000 부터 001 로 순차적으로 넘버링 되어 쌓이게 된다."

### PNE 운영 규칙 (확정)

| 파일 | 역할 | mtime |
|---|---|---|
| `~~.sch` (접미사 없음) | **현재 적용 중** 패턴 | 가장 최근 |
| `~~_000.sch` | **가장 최근 백업** (직전 업데이트 이전 버전) | 더 이전 |
| `~~_001.sch` | 그 이전 백업 | 더 이전 |
| `~~_002.sch` ... | 번호가 커질수록 과거 | ... |

### 기존 코드의 오류

```python
# Before
def _sort_key(name):
    m = _SCH_SUFFIX_RE.match(name)
    return int(m.group(2)) if m else -1
sch_files.sort(key=_sort_key, reverse=True)   # ← 큰 번호 우선
return os.path.join(channel_path, sch_files[0])
```

- **기존 가정**: 접미사 번호 가장 큰 파일 = 최신
- **실제 규칙**: 접미사 없는 원본이 현재 패턴, 번호가 커질수록 **오래된 백업**
- 결과: 접미사 없는 원본이 있더라도 `-1` 로 취급되어 **가장 뒤로 밀림** → 가장 오래된 백업이 선택됨

선택된 `_NNN.sch` 로 `extract_schedule_structure_from_sch` 를 돌리면:
- 스케줄 구조가 이미 과거 버전이라 현재 측정 데이터와 불일치 → 파싱 실패 또는 비정상 결과
- 최상위 호출자 `_get_pne_sch_struct` 가 None 반환 → `pne_build_cycle_map` 에서 `sch_struct is None`
- → `[cycle_map] .sch 없음 - 데이터 휴리스틱 폴백` 경고
  (파일은 찾았지만 **파싱 결과가 쓸 수 없어** 실질적으로 "없음"과 동일하게 처리)

## 수정

```python
# After
# 1) 접미사 없는 원본 우선 (현재 적용 중 패턴)
originals = [f for f in sch_files if not _SCH_SUFFIX_RE.match(f)]
if originals:
    if len(originals) == 1:
        return os.path.join(channel_path, originals[0])
    # 드물게 여러 원본 → mtime 최신 (방어적)
    try:
        originals.sort(
            key=lambda f: os.path.getmtime(os.path.join(channel_path, f)),
            reverse=True)
    except OSError:
        pass
    return os.path.join(channel_path, originals[0])
# 2) 원본이 없으면 → 번호 가장 작은 백업 (가장 최근 백업)
def _suffix_num(name):
    m = _SCH_SUFFIX_RE.match(name)
    return int(m.group(2)) if m else float('inf')
sch_files.sort(key=_suffix_num)
return os.path.join(channel_path, sch_files[0])
```

### 선택 순서

| 상황 | 선택 파일 | 이유 |
|---|---|---|
| 원본 1개 + 백업 N개 | **원본** | 현재 적용 중 패턴 |
| 원본 2개 이상 (비정상) | mtime 최신 원본 | 방어적 선택 |
| 원본 없음, 백업 여러 개 | 번호 가장 작은 백업 (`_000`) | 가장 최근 백업 |
| 원본도 백업도 없음 | `.sch 없음` 경고 + None | 기존 동작 |
| 파일 1개뿐 | 그 파일 | 판별 불필요 |

## 동작 변화

### 실제 시나리오: `~~.sch` + `~~_000.sch` + `~~_001.sch`

| 항목 | Before | After |
|---|---|---|
| 선택 | `~~_001.sch` (가장 과거 백업) | **`~~.sch`** (현재 패턴) |
| `extract_schedule_structure_from_sch` 결과 | 과거 버전으로 오파싱 / None | **현재 버전 정상 파싱** |
| `pne_build_cycle_map` 판별 | 폴백 → 휴리스틱 | **`.sch sweep_mode` 기반 확정** |
| cycle_map 정확도 | ✕ 오분류 가능 | ✓ 정확 |

### 회귀 안전성

- **파일 1개(`~~.sch` 또는 `~~_000.sch`)만 있는 경우**: 기존/신규 모두 그 파일 반환 — 동일
- **원본이 있던 기존 환경**: 이제 원본 선택 (이전보다 **개선**)
- **원본 없이 백업만**: 이제 `_000` 선택 (이전에는 `_NNN` 가장 큰 번호 = 가장 과거. 전환 후엔 가장 최근)

## 영향 범위

- `_find_sch_file()` 로직만 변경
- 호출자 (`_get_pne_sch_struct`, `pne_build_cycle_map`, `extract_accel_pattern_from_sch`,
  `_process_pne_cycleraw` 경로 등) 는 투명하게 정확한 `.sch` 를 받음
- Toyo 경로 영향 없음 (.sch 는 PNE 전용)
- `lru_cache` 유지 — `_reset_all_caches()` 에서 일괄 무효화

## 검증 포인트

- [ ] `~~.sch` + `~~_000.sch` 가 공존하는 PNE 경로 → `[cycle_map] .sch 없음` 경고 **사라짐**
- [ ] 현재 패턴 기준 `sch_struct.sweep_mode` 가 정확히 판별되는지
- [ ] 사이클 바의 카테고리 색상 / 논리사이클 그룹핑이 현재 패턴과 일치
- [ ] 시험 도중 패턴 업데이트된 채널에서 `_000`, `_001` 백업이 있더라도 원본 우선 선택 확인
- [ ] 파일이 1개만 있던 기존 정상 경로 → 회귀 없음
- [ ] (드문 케이스) 원본 없이 백업만 있는 경로 → `_000` 가장 최근 백업 선택

## 관련 변경로그

- `260420_revert_sch_extended_and_add_diag.md` — 확장 탐색 롤백 + 진단 로그 추가
- `260420_fix_find_sch_extended_search.md` (삭제됨) — 4단계 확장 탐색 (롤백됨)
