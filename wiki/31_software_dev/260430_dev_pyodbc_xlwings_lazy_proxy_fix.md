---
title: pyodbc/xlwings lazy 로드 — 모듈 내부 NameError 수정 (_LazyModule 프록시 도입)
date: 2026-04-30
tags: [bdt, lazy-import, bugfix, proto_, pyodbc, xlwings, schedule-mdb, pattern-edit]
type: changelog
status: done
---

# 배경 / 목적

[패턴수정] 탭 → **[패턴 리스트 Load]** 버튼 클릭 시 다음 런타임 오류가 발생.

```
NameError: name 'pyodbc' is not defined
```

원인은 [DataTool_optRCD_proto_.py:31-43](DataTool_dev_code/DataTool_optRCD_proto_.py:31) 에 정의돼
있던 lazy 로드 메커니즘의 설계 결함이었다.

```python
# (수정 전)
_BDT_LAZY = {
    'pyodbc':      lambda: __import__('pyodbc'),
    'xw':          lambda: __import__('xlwings'),
}

def __getattr__(name):       # ← 모듈 레벨 __getattr__
    loader = _BDT_LAZY.get(name)
    ...
    obj = loader()
    globals()[name] = obj
    return obj
```

Python 3.7+ 에서 모듈 레벨 `__getattr__` 은 **외부에서 attribute 를
조회할 때만** 트리거된다 (`bdt.pyodbc` 형태). 모듈 자체 코드 안에서
`pyodbc.connect(...)` 처럼 이름을 참조하면 일반 글로벌 lookup 만 일어나며,
`pyodbc` 이 `globals()` 에 없으므로 `NameError` 가 그대로 발생한다. 코드
주석(line 47)에서도 이 한계를 명시하고 있었으나 함수 본문은 여전히
`pyodbc.connect(...)` / `xw.Book(...)` 를 직접 호출하고 있었다.

영향 받는 함수 — pyodbc 9곳, xlwings 2곳:

| 위치 | 함수 | 의존 라이브러리 |
|------|------|---------------|
| 11262 | (xlsx 프로파일 로드 분기) | xlwings |
| 22690 | (신뢰성 데이터 Excel 그룹 처리) | xlwings |
| 33262 | `ptn_change_pattern_button` | pyodbc |
| 33306 | `ptn_change_refi_button` | pyodbc |
| 33346 | `ptn_change_chgv_button` | pyodbc |
| 33379 | `ptn_change_dchgv_button` | pyodbc |
| 33412 | `ptn_change_endv_button` | pyodbc |
| 33445 | `ptn_change_endi_button` | pyodbc |
| 33485 | `ptn_change_step_button` | pyodbc |
| 33518 | `ptn_load_button` (← 사용자가 만난 지점) | pyodbc |
| 33960 | (Toyo PATRN 변환) | pyodbc |

# 변경 내용

## Before

```python
_BDT_LAZY = {
    'pyodbc':      lambda: __import__('pyodbc'),
    'xw':          lambda: __import__('xlwings'),
}

def __getattr__(name):
    loader = _BDT_LAZY.get(name)
    if loader is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    obj = loader()
    globals()[name] = obj
    return obj
```

→ 외부 접근 전용. 모듈 내부 9+2곳 `pyodbc.connect()` / `xw.Book()` /
`xw.App()` 호출이 모두 `NameError`.

## After

`_LazyModule` 프록시 클래스를 도입하고 모듈 globals 에 `pyodbc` / `xw`
이름으로 미리 바인딩한다. 첫 attribute 접근에서 실제 `__import__` 가
호출되고 그 이후는 캐시된 모듈을 그대로 반환한다.

```python
class _LazyModule:
    """첫 attribute 접근에서 실제 모듈을 import 하는 프록시."""
    __slots__ = ('_name', '_mod')

    def __init__(self, name):
        object.__setattr__(self, '_name', name)
        object.__setattr__(self, '_mod', None)

    def _load(self):
        mod = object.__getattribute__(self, '_mod')
        if mod is None:
            mod = __import__(object.__getattribute__(self, '_name'))
            object.__setattr__(self, '_mod', mod)
        return mod

    def __getattr__(self, attr):
        return getattr(self._load(), attr)

    def __repr__(self):
        name = object.__getattribute__(self, '_name')
        loaded = object.__getattribute__(self, '_mod') is not None
        return f"<_LazyModule {name!r} loaded={loaded}>"


pyodbc = _LazyModule('pyodbc')
xw = _LazyModule('xlwings')
```

### 주요 포인트

- **`__slots__`**: 일반 인스턴스 속성 채널을 닫아두고 `_name`, `_mod`
  두 슬롯만 사용 → `__getattr__` 가 `_name`/`_mod` 접근을 가로채지
  않도록 `object.__getattribute__/__setattr__` 우회 사용.
- **모듈 globals 바인딩**: `pyodbc = _LazyModule('pyodbc')` 로 모듈 로드
  시점에 이름은 즉시 묶이지만 실제 `import pyodbc` 는 첫 attribute
  접근까지 미뤄진다. → 외부 `bdt.pyodbc` 패턴과 모듈 내부
  `pyodbc.connect()` 패턴이 모두 동작.
- **scipy 는 변동 없음**: 기존대로 line 48-49 eager import 유지.

# 영향 범위

## 직접 영향

- [DataTool_dev_code/DataTool_optRCD_proto_.py:28-58](DataTool_dev_code/DataTool_optRCD_proto_.py:28) — `_BDT_LAZY` /
  `__getattr__` 제거, `_LazyModule` 클래스 + 모듈 globals 바인딩으로 교체.
- 11곳 call site는 **수정 불필요** — 호출 코드는 그대로 두고 이름
  바인딩만 정상화.

## 기능 영향

- **패턴수정 탭** 전체 (8개 버튼: Load / Pattern / Refi / ChgV / DchgV /
  EndV / EndI / Step) → 사용자가 보고한 [패턴 리스트 Load] 정상 동작.
- **Toyo PATRN 변환** 기능 (line 33960) → `MDB → Toyo` 변환 시
  pyodbc 정상 호출.
- **신뢰성 .xlsx 로드** (line 22690) → xlwings 기반 Fasoo DRM 우회 경로
  정상 동작.
- **xlsx 프로파일 로드** (line 11262) → BSOH log .xlsx import 정상.

## 외부 호환성

- 외부에서 `import DataTool_optRCD_proto_ as bdt; bdt.pyodbc.connect(...)`
  형태로 접근하던 코드도 그대로 동작 (프록시는 attribute 접근에서 실제
  모듈로 위임).
- `_BDT_LAZY` 심볼은 제거됐으나 grep 결과 외부 참조 0건이었다.

## 시작 시간

- pyodbc / xlwings import 는 여전히 lazy → 패턴수정 탭이나 Excel
  신뢰성 로드를 한 번도 사용하지 않는 사용자는 두 라이브러리 import
  비용을 전혀 지불하지 않는다 (기존 의도 유지).

## 검증

1. `python -c "import ast; ast.parse(...)"` → `AST OK`
2. `_LazyModule` 단독 동작 검증 (json stdlib 으로 시뮬레이션):
   - access 전 `loaded=False`
   - `proxy.loads('{"a":1}')` 호출 → `loaded=True` 로 전이, 결과
     `{'a': 1}` 정상 반환
3. 실 GUI 검증은 사용자 측 PNE CTSPro `Cycler_Schedule_2000.mdb` 환경
   필요 — 패턴수정 → [패턴 리스트 Load] 클릭 시 NameError 사라지고
   `TestName` / `BatteryModel` 테이블 머지 결과가 `ptn_list` QTableWidget
   에 표시되어야 한다.

## 후속 작업

없음. lazy 의도와 호출 표면이 모두 보존됐다.
