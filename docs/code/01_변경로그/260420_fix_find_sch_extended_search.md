# `.sch` 탐색 범위 확장 (Pattern·상위 시험 폴더 포함)

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수: `_find_sch_file()` (L7344)

## 배경 / 문제

사용자 보고:
> "경로테이블에 경로 입력 시, [cycle_map] .sch 없음이라고 나온다. PNE 경로인데 .sch 검색을 어떻게 하는거야? 확인해보니 .sch 가 있는데 데이터 휴리스틱 폴백으로 빠진다."

### 원인

`_find_sch_file(channel_path)` 이 **`channel_path` 디렉토리 바로 아래 한 단계**만 검색:

```python
# Before
sch_files = [f for f in os.listdir(channel_path) if f.lower().endswith('.sch')]
```

PNE 현장 구조상 `.sch` 는 다음과 같이 **채널 폴더 밖**에 위치하는 경우가 흔함:

```
시험폴더/                        ← 사용자가 경로 테이블에 입력하는 경로
├─ {스케줄}.sch                 ← [케이스 A] 상위 시험 폴더에 공용 스케줄
├─ Pattern/
│   └─ {스케줄}.sch             ← [케이스 B] 상위 Pattern 서브
├─ M01Ch001[4905mAh]/           ← 실제 channel_path
│   ├─ Restore/
│   ├─ SaveData/
│   └─ (.sch 없음)               ← 기존 코드가 여기만 검색 → 못 찾음
```

→ `.sch` 가 있는데도 "없음" 으로 판단 → `pne_build_cycle_map` 이 데이터 휴리스틱 폴백(`sig_ratio`/`has_both_ratio`) 으로 진입 → `[cycle_map] .sch 없음 - 데이터 휴리스틱 폴백` 경고 로깅.

### 도메인 영향

- `.sch` 의 `sweep_mode` 플래그가 있어야 General/Sweep 을 **확정 판별**
- 데이터 휴리스틱은 경계값 근방에서 오판 가능 (GITT 를 수명시험으로, 또는 반대로 오분류)
- 오분류 시 논리사이클 갯수, 색상 분류, 프로파일 집계 전부 틀어짐

## 수정 — 4단계 우선순위 탐색

```python
# After — 첫 발견 반환
# 1) 채널 폴더 자체
# 2) 채널 폴더/Pattern (대소문자 변형: Pattern / pattern / PATTERN)
# 3) 상위(시험) 폴더
# 4) 상위 폴더/Pattern
```

채널 전용 `.sch` 가 있으면 1단계에서 즉시 반환 (기존 동작 동일), 없을 때만 확장 탐색.

### 구현

```python
def _collect(dir_path):
    try:
        return [(os.path.join(dir_path, f), f)
                for f in os.listdir(dir_path)
                if f.lower().endswith('.sch')]
    except OSError:
        return []

def _pick(items):
    if not items:
        return None
    if len(items) == 1:
        return items[0][0]
    def _k(it):
        m = _SCH_SUFFIX_RE.match(it[1])
        return int(m.group(2)) if m else -1
    return sorted(items, key=_k, reverse=True)[0][0]

# 4단계 탐색
found = _pick(_collect(channel_path))
if found: return found
for _sub in ('Pattern', 'pattern', 'PATTERN'):
    _p = os.path.join(channel_path, _sub)
    if os.path.isdir(_p):
        found = _pick(_collect(_p))
        if found: return found
parent = os.path.dirname(channel_path.rstrip('/\\'))
if parent and parent != channel_path:
    found = _pick(_collect(parent))
    if found: return found
    for _sub in ('Pattern', 'pattern', 'PATTERN'):
        _p = os.path.join(parent, _sub)
        if os.path.isdir(_p):
            found = _pick(_collect(_p))
            if found: return found
return None
```

접미사 `_000`/`_001` 우선순위 규칙(가장 큰 번호 = 최신 패턴) 유지.

## 동작 변화

| `.sch` 위치 | Before | After |
|---|---|---|
| 채널 폴더 | ✅ 찾음 | ✅ 찾음 (동일) |
| 채널 폴더/Pattern | ❌ 못 찾음 | ✅ **찾음** |
| 상위 시험 폴더 | ❌ 못 찾음 | ✅ **찾음** |
| 상위/Pattern | ❌ 못 찾음 | ✅ **찾음** |
| 어디에도 없음 | `.sch 없음` 폴백 | `.sch 없음` 폴백 (동일) |

## 안전성

- **채널 폴더에 있는 경우 기존 동작 완전 동일** (1단계에서 즉시 반환)
- 상위 폴더 탐색은 **다른 시험 폴더까지 안 넘어감** (한 단계 상위만)
- `os.listdir` 실패(권한/없음) 시 해당 단계만 skip, 다음 우선순위로
- `lru_cache(maxsize=128)` 유지 → 캐시 무효는 `_reset_all_caches()` 에서 일괄

## 부작용 가능성

- **채널별 다른 스케줄**이 적용된 시험에서, 채널 폴더에 `.sch` 가 없고 상위 폴더에만 있다면 → 상위의 공용 `.sch` 가 잡힘. 실무상 PNE 는 보통 시험당 단일 스케줄을 공유하므로 문제 없음
- 드물게 여러 시험을 한 상위 폴더에 묶는 구조라면, 상위 `.sch` 가 다른 시험 것일 수 있음 — 이 경우 채널 폴더 내부로 이동 권장 (기존에도 데이터 휴리스틱이 잘못 폴백되던 케이스)

## 영향 범위

- `_find_sch_file()` 단일 함수
- 호출자 (`_get_pne_sch_struct`, `pne_build_cycle_map`, `extract_accel_pattern_from_sch`, `_process_pne_cycleraw` 경로 등) 는 투명하게 혜택을 받음
- Toyo 경로 영향 없음 (.sch 는 PNE 전용)

## 검증 포인트

- [ ] `.sch` 가 **상위 시험 폴더**에 있는 PNE 경로 → `.sch 없음` 경고 **사라짐**, cycle_map 이 `.sch sweep_mode` 로 확정 판별
- [ ] `.sch` 가 **상위/Pattern** 폴더에 있는 경로 → 동일하게 찾음
- [ ] `.sch` 가 **채널 폴더**에 있는 기존 경로 → 기존과 동일 동작 (회귀 없음)
- [ ] `.sch` 가 **어디에도 없는** 경로 → 기존처럼 폴백 (문구 동일)
- [ ] 같은 경로를 여러 번 조회해도 `lru_cache` 히트 (I/O 중복 없음)
- [ ] `_reset_all_caches()` 호출 후 새 경로 탐색 로직 적용 여부

## 후속 과제 (선택)

- `_find_sch_file` 의 후보 위치를 설정 파일/환경 변수로 추가 지정 가능하도록 확장 — 특수 팀 구조 대응. 현재 범위 제외.
- 디버그 로그: 어느 단계에서 찾았는지 `DEBUG` 레벨 로그 (사용자 문의 시 위치 파악 용이) — 필요 시 별도 PR.
