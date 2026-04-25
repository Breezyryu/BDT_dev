---
title: "functools.lru_cache 원리 — 메모이제이션의 표준 구현"
date: 2026-04-26
tags: [study, python, performance, cache, memoization, software-dev]
related:
  - "[[../10_cycle_data/260426_changelog_path_table_step1_cache_patch|경로 테이블 Step 1 캐시 패치]]"
  - "[[../10_cycle_data/__moc__|MOC: cycle data]]"
---

# `functools.lru_cache` 원리

> **LRU = Least Recently Used** — "가장 오래 안 쓴 항목 우선 폐기" 정책의 메모이제이션 캐시.
> Python 표준 라이브러리 `functools` 모듈에서 제공. CPython 구현체는 `_functoolsmodule.c` 의 `lru_cache_new` 에 위치.

## 핵심 아이디어 — "함수의 입력이 같으면 출력도 같다"

순수 함수(같은 입력 → 같은 출력) 라면 한 번 계산한 결과를 저장해두고 다음 호출 시 재사용해도 안전. 이것이 **메모이제이션 (memoization)** — 함수 결과를 메모리(memo)에 저장해두는 기법.

```python
@functools.lru_cache(maxsize=512)
def check_cycler(path):       # 50–200ms IO 함수
    return os.path.isdir(path + "\\Pattern")

check_cycler("/data/Q8")      # 첫 호출: IO 200ms → True (캐시 저장)
check_cycler("/data/Q8")      # 두 번째: 즉시 True ≈ 0ms (캐시 hit)
check_cycler("/data/Q9")      # 다른 키: IO 200ms → True (miss, 새로 계산)
```

## 자료구조 — Hash Map + Doubly Linked List

`lru_cache` 는 두 자료구조를 결합해 **O(1) lookup + O(1) eviction** 을 동시에 달성:

```
Hash Map (dict)              Doubly Linked List (LRU 순서)
─────────────────            ────────────────────────────────────
"/data/Q8"  ──┐              [ HEAD ←→ Q9 ←→ Q7 ←→ Q8 ←→ TAIL ]
              │                       가장 최근       가장 오래됨
              └─→ Node(value=True, prev=Q7, next=TAIL)

"/data/Q9"  ──┐
              │
              └─→ Node(value=True, prev=HEAD, next=Q7)
```

- **조회 (`__call__`)**: hash map 으로 키 → 노드 즉시 찾음 (O(1)). hit 면 노드를 리스트의 **HEAD 쪽**으로 이동 (가장 최근 사용 표시)
- **삽입 (cache miss)**: 함수 실행 → 결과 저장. 새 노드를 HEAD 에 붙이고 hash map 등록. 크기가 `maxsize` 초과 시 **TAIL 의 노드 제거** (가장 오래 안 쓴 것 폐기, O(1))

CPython 의 실제 구현은 단일 doubly linked list 의 sentinel node + hash map 으로 위 구조를 효율화. C 레벨에서 GIL 하에 atomic 으로 동작.

## `maxsize` 파라미터 의미

```python
@functools.lru_cache(maxsize=512)   # 최대 512 개 키 보관
@functools.lru_cache(maxsize=None)  # 무한 (위험, 누수 가능)
@functools.lru_cache(maxsize=0)     # 캐시 비활성 (lru_cache 효과 없음)
@functools.lru_cache               # default maxsize=128
```

- 캐시에 보관할 (입력→출력) 쌍의 최대 개수
- 초과 시 LRU 항목 자동 폐기 → 메모리 안정
- `None` 은 메모리 누수 위험 — 장기 실행 프로세스에서 키가 무한 누적 가능
- `2의 제곱수` 가 아니어도 무방. CPython 은 hash map 내부적으로 자동 리사이즈

**BDT 의 maxsize 결정 근거**:
- 일반 사용자가 동시에 다루는 path: 5–20 개
- 256/512 슬롯이면 hit rate 거의 100%
- 키+bool/int 만 저장 → 메모리 압박 없음 (≪ 1MB)
- `_get_pne_cycle_map` 같이 dict 결과를 캐시하는 경우엔 256 슬롯 = 수 MB 까지 가능 → maxsize 줄이거나 결과 크기 모니터링

## 키 생성 방식

함수 인자 전체를 **`tuple` 로 묶어** 캐시 키로 사용:

```python
@functools.lru_cache(maxsize=256)
def _quick_max_cycle(data_path: str, mincapacity: float = 0):
    ...

# 키 (인자 전체 → 튜플):
_quick_max_cycle("/data/Q8", 2335)        # 키 = ("/data/Q8", 2335)
_quick_max_cycle("/data/Q8", 2336)        # 키 = ("/data/Q8", 2336)  ← 다른 키!
_quick_max_cycle("/data/Q8")              # 키 = ("/data/Q8", 0)     ← default 값도 키에 포함

# 키워드 인자도 정렬되어 키에 포함
foo(a=1, b=2)   # 키 = (("a", 1), ("b", 2))
foo(b=2, a=1)   # 같은 키 (순서 무관)
```

**조건**: 모든 인자가 **hashable** 해야 함. Python 의 hashable 객체:

| Hashable (캐시 가능) | Unhashable (캐시 불가) |
|---|---|
| `str`, `int`, `float`, `bool`, `bytes` | `list` |
| `tuple` (모든 원소 hashable 시) | `dict` |
| `frozenset`, `frozen dataclass` | `set` |
| `None` | `pd.DataFrame`, `np.ndarray` |
| `class` (default `id()` 기반) | mutable user class instance |

**BDT 우회 패턴**: `pne_build_cycle_map(channel_path, mincapacity, ini_crate, sch_struct=dict)` 처럼 dict 인자를 받는 함수는 직접 `lru_cache` 불가. 그래서 hashable 인자만 받는 래퍼 `_get_pne_cycle_map(path, cap, crate)` 를 만들고 내부에서 `_get_pne_sch_struct()` (역시 lru_cache) 를 호출.

## 캐시 무효화

`lru_cache` 는 함수 결과가 영원히 같다고 가정하므로, 외부 상태가 변하면 **명시 무효화** 필요:

```python
# 메서드들
check_cycler.cache_clear()    # 전체 비우기
check_cycler.cache_info()     # CacheInfo(hits=42, misses=5, maxsize=512, currsize=5)
check_cycler.__wrapped__      # 원본 함수 참조 (캐시 우회 호출 가능)
```

**BDT 의 무효화 전략** (`DataTool_optRCD_proto_.py:776` `_reset_all_caches()`):

```python
def _reset_all_caches():
    """새 데이터 로드 시작 시 일괄 호출."""
    clear_channel_meta_store()
    _channel_cache.clear()
    # lru_cache 래퍼 초기화
    _get_pne_cycle_map.cache_clear()
    _get_toyo_cycle_map.cache_clear()
    _get_pne_sch_struct.cache_clear()
    _get_pne_sch_parsed.cache_clear()
    _sch_total_seconds.cache_clear()
    _find_sch_file.cache_clear()
    check_cycler.cache_clear()        # Step 1 추가
    _quick_max_cycle.cache_clear()    # Step 1 추가
    WindowClass._path_meta_cache.clear()
```

→ 새 데이터 로드 시점이 stale 캐시의 자연스러운 무효화 경계.

## 동시성 (Thread Safety)

`lru_cache` 는 **GIL 기반 thread-safe** — 내부적으로 lock 으로 자료구조 보호. 다만:

- ✅ 캐시 자료구조 (hash map + linked list) 자체는 atomic
- ⚠️ 두 스레드가 같은 미스 키를 동시에 호출하면 **함수 본문이 두 번 실행될 수 있음** (락은 캐시만 보호, 본문 실행은 보호 X)
- ✅ 결과는 둘 중 하나가 캐시에 들어가고, 다른 결과는 버려짐 (메모리 leak X)

BDT 는 단일 메인 Qt 스레드 + 동기 IO 환경 — 동시성 무관. 향후 B안 (QThread Worker) 도입 시에도 같은 키 동시 호출 가능성은 있으나, IO 가 두 번 실행되어도 결과는 일관됨.

## 인스턴스 메서드에 적용 시 주의 — 메모리 누수 위험

```python
class WindowClass:
    @functools.lru_cache(maxsize=256)  # ❌ 위험!
    def _resolve_path_meta(self, path):
        ...
```

`self` 가 캐시 키에 포함됨 → 캐시가 인스턴스 참조를 보유 → 인스턴스가 GC 되지 않음. 장기 실행 프로세스 (Qt 앱) 에서 메모리 누수.

**우회 방법**:
1. **Module-level 함수에만 적용** (BDT 의 선택) — `check_cycler`, `_quick_max_cycle`, `_get_pne_cycle_map` 등
2. 인스턴스 메서드면 `weakref` + 수동 캐시 — `WindowClass._path_meta_cache: dict` (BDT 의 인스턴스 캐시 패턴)
3. `cachetools.cached(LRUCache(maxsize=...))` — 외부 라이브러리, 더 유연

## BDT 에서 Step 1 의 효과 시각화

```
타임라인 (사용자 5경로 paste → confirm)

▼ 패치 전:
paste 직후 autofill                    confirm 시 두 번째 autofill
[check_cycler ×5 = 1s]               [check_cycler ×5 = 1s]   ← 같은 IO 반복!
[_quick_max_cycle ×5 = 5s]           [_quick_max_cycle ×5 = 5s]
                  ─────  6s 소요 ─────                  ─────  6s 소요 ─────
총 12s

▼ 패치 후 (lru_cache):
paste 직후 autofill                    confirm 시 두 번째 autofill
[check_cycler ×5 = 1s, miss]         [check_cycler ×5 = 0s, hit] ← 캐시 hit
[_quick_max_cycle ×5 = 5s, miss]     [_quick_max_cycle ×5 = 0s, hit]
                  ─────  6s 소요 ─────                  ─────  ≈0s ─────
총 6s (50% 절감)
```

## 메모이제이션의 일반 원칙

`lru_cache` 는 메모이제이션의 한 구현일 뿐. 메모이제이션 자체는:

1. **재계산 비용이 큰 함수** — IO, 무거운 계산, 외부 API 호출 등
2. **순수 함수에 가까울 것** — 같은 입력 → 같은 출력 보장
3. **호출 빈도가 높을 것** — 캐시 hit rate 가 높아야 효과
4. **결과 크기가 합리적** — 메모리 압박 없을 것

이 4 조건이 만족되지 않으면 캐시 자체가 오버헤드. BDT 의 `_get_pne_cycle_map` 은 4 조건 모두 충족.

## 한계 — `lru_cache` 가 해결하지 못하는 것

1. **인자가 hashable 해야 함** — `dict`, `list` 인자는 캐시 불가 (BDT의 dict 인자 우회 패턴 참조)
2. **외부 상태 변화 무감지** — 폴더 구조 외부 변경, 파일 추가 등 직접 폴링하지 않음. 사용자 명시 새로고침 또는 timestamp 기반 캐시 검증 필요
3. **인스턴스 메서드 메모리 누수** — module-level 함수에만 적용 권장
4. **TTL (Time-To-Live) 없음** — `lru_cache` 자체엔 만료 시간 개념 X. 시간 기반 만료가 필요하면 `cachetools.TTLCache` 사용
5. **분산 캐시 X** — 프로세스 내 메모리 캐시. 여러 워커 프로세스 간 공유 불가 (Redis 등 필요)

## 대안 라이브러리

| 라이브러리 | 특징 | 사용 시나리오 |
|---|---|---|
| `functools.lru_cache` | 표준, 가볍고 빠름 | 일반적 메모이제이션 (BDT의 선택) |
| `cachetools.LRUCache` | 인스턴스 메서드 캐싱, TTL 지원 | 클래스 내부 캐시, 시간 만료 |
| `functools.cache` (Py 3.9+) | `lru_cache(maxsize=None)` 의 alias | 무한 캐시 (작은 키 도메인) |
| `joblib.Memory` | 디스크 기반 영구 캐시 | 무거운 계산 결과 영구 보관 |
| `redis-py` + decorator | 프로세스 간 공유 | 분산 시스템, 다중 워커 |

## 참고 (CPython 소스)

- 구현: `Modules/_functoolsmodule.c` 의 `lru_cache_new`, `lru_cache_call`, `lru_cache_make_key`
- 자료구조: `lru_list_elem` (doubly linked list node) + `cache_dict` (hash map)
- 락: `lock` 필드 (PyThread_type_lock) — atomic 보장

---

## 요약

| 핵심 | 내용 |
|---|---|
| **무엇** | 함수 결과를 (입력→출력) 쌍으로 저장해 재계산 회피 |
| **어떻게** | Hash Map + Doubly Linked List → O(1) lookup/eviction |
| **왜 LRU** | 가장 오래 안 쓴 항목부터 폐기 → 활성 working set 보존 |
| **언제 사용** | 비싼 순수 함수 + 호출 빈도 ↑ + hashable 인자 |
| **언제 피함** | mutable 인자, 외부 상태 의존, 인스턴스 메서드 (직접) |
| **BDT 적용** | `check_cycler`, `_quick_max_cycle`, `_get_pne_cycle_map` 등 path 단위 IO 함수 |

> "Premature optimization is the root of all evil" (Knuth) — 그러나 **확인된 핫스팟에 lru_cache 한 줄** 은 가장 비용 대비 효과가 큰 최적화 중 하나.
