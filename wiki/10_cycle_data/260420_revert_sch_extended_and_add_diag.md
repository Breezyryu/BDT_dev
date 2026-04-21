# `.sch` 확장 탐색 롤백 + 실패 진단 로그 추가

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수: `_find_sch_file()` (L7344), `pne_build_cycle_map()` (L4674)

## 배경

직전 커밋 8080adf (`260420_fix_find_sch_extended_search.md`) 에서 `.sch` 탐색 범위를
채널 폴더 → 채널/Pattern → 상위 시험 폴더 → 상위/Pattern 4단계로 확장했다.

사용자 피드백:
> "항상 channel_path 에 .sch 파일이 있다."

→ 확장 탐색은 **불필요**. 오히려 다른 시험의 `.sch` 를 잘못 잡을 위험이 있어 오분류 유발 가능.
실제 문제는 "채널 폴더에 있는데 못 찾음" 이라는 별개의 원인 → **진단 강화**가 필요.

## 변경 내용

### 1. 확장 탐색 롤백

`_find_sch_file` 을 기존 단일 폴더 탐색으로 되돌림 — **`os.listdir(channel_path)` 한 단계**에서 `.sch` 검색.

```python
sch_files = [f for f in os.listdir(channel_path) if f.lower().endswith('.sch')]
```

운영 전제: `.sch` 는 항상 채널 폴더 내부에 존재.

### 2. 실패 케이스 진단 로그 추가

"channel_path 에 있는데 못 찾음" 원인 추적을 위해 실패 케이스마다 로그를 남김:

**OSError (listdir 실패)** — 권한/네트워크 단절/경로 오류 판단:
```python
except OSError as _e:
    _perf_logger.warning(
        f'_find_sch_file: os.listdir 실패 — path={channel_path!r} err={_e}')
    return None
```

**listdir 성공했으나 `.sch` 없음** — channel_path 값 오인 판단 (진짜 채널 폴더가 아닌지):
```python
_sample = _all[:10] if len(_all) > 10 else _all
_perf_logger.warning(
    f'_find_sch_file: .sch 파일 없음 — path={channel_path!r} '
    f'파일수={len(_all)} 샘플={_sample}')
```

`raw` 표시(`!r`) 로 백슬래시/공백/특수문자 가시화.

### 3. `pne_build_cycle_map` 폴백 경고에 경로 추가

기존 경고에는 `path` 가 없어서 어느 경로에서 실패한 건지 안 보였음:

```python
# Before
_perf_logger.warning(
    f'  [cycle_map] .sch 없음 - 데이터 휴리스틱 폴백 '
    f'(sig={sig_ratio:.2f}, both={has_both_ratio:.2f}) -> ...')

# After
_perf_logger.warning(
    f'  [cycle_map] .sch 없음 - 데이터 휴리스틱 폴백 '
    f'path={raw_file_path!r} '                                # ← 추가
    f'(sig={sig_ratio:.2f}, both={has_both_ratio:.2f}) -> ...')
```

## 후속 진단 절차

사용자가 문제 경로로 다시 실행하면 로그에서 아래 정보를 확인 가능:

1. **`_find_sch_file: .sch 파일 없음 — path='...'  파일수=N  샘플=[...]`**
   → channel_path 값이 실제로 어느 폴더인지, 폴더 안에 어떤 파일들이 있는지 직접 확인
   - `샘플` 에 `.sch` 가 보이면? → 파일명 필터(`.lower().endswith('.sch')`) 이외 원인 (숨김 속성, 유니코드 정규화 등)
   - `샘플` 에 `.sch` 가 안 보이면? → channel_path 가 실제 채널 폴더가 아니거나 파일이 정말 없음 (UI/자동채움 흐름에서 잘못된 경로 전달 가능성)

2. **`_find_sch_file: os.listdir 실패 — path='...'  err=...`**
   → 권한 문제, 네트워크 단절, 경로 미존재 등의 OS 수준 오류

3. **`[cycle_map] .sch 없음 - 데이터 휴리스틱 폴백 path='...' (sig=..., both=...)`**
   → `raw_file_path` 와 위 `_find_sch_file` 경고의 `path` 가 **일치**하는지 비교:
      - 일치: `_find_sch_file` 단계가 문제
      - 불일치: 다른 경로로 전파되는 호출 흐름 존재 (_get_pne_sch_struct 의 channel_path 인자가 상위 폴더)

## 영향 범위

- `_find_sch_file()` 탐색 로직 원복, 로그 2개 추가
- `pne_build_cycle_map()` 경고 메시지에 path 토큰 1개 추가
- 기능 동작은 확장 이전 시점과 **완전 동일** — 회귀 없음
- 로그 볼륨: 문제 경로에서만 경고, 정상 경로에선 기존과 같음

## 검증 포인트

- [ ] 문제 경로 실행 → 로그에 `_find_sch_file: .sch 파일 없음` 또는 `os.listdir 실패` 경고 + path 값 확인
- [ ] `[cycle_map] .sch 없음 ... path='...'` 로그로 어느 경로인지 즉시 파악
- [ ] 정상 경로에선 `_find_sch_file` 로그 없음 (성공 시 조용)
- [ ] `lru_cache` 때문에 이전 실패 결과가 유지될 가능성 → `_reset_all_caches()` 호출 후 재시도

## 관련 변경로그

- (삭제됨) `260420_fix_find_sch_extended_search.md` — 4단계 확장 탐색 (롤백됨)
