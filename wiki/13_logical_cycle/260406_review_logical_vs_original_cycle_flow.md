# 논리사이클 vs 원본사이클 — 전체 흐름 분석 및 개선 제안

> 📎 2026-04-21: `260404_analysis_logical_cycle_design.md` 병합 (§1 초기 설계)

> **작성일**: 2026-04-06
> **대상 파일**: `DataTool_dev/DataTool_optRCD_proto_.py`
> **핵심 함수**: `_get_table_cycle_input`, `_init_confirm_button`, `pro_continue_confirm_button`, `unified_profile_core`, `pne_build_cycle_map`, `toyo_build_cycle_map`

---

## 1. 초기 설계 (260404)

### 1.1 현황 분석 — 탭별 "사이클" 정의 차이

| | 사이클 데이터 탭 | 프로필 분석 탭 |
|--|--|--|
| **Toyo** | ✅ 논리사이클 (유효 방전 1회 = 1 사이클) | ❌ 물리 파일 번호 (000001~) |
| **PNE** | ✅ 논리사이클 (TotlCycle, Col 27, 루프 기반) | ❌ 물리 사이클 번호 (SaveData 인덱스) |

**사이클 데이터 탭**은 `toyo_cycle_data()` / `pne_cycle_data()`에서 이미 논리사이클을 구축한다:
- **Toyo**: 연속 동일 Condition 머지 → 유효 방전(Cap > mincapacity/60) 필터 → 순차 번호 부여
- **PNE**: SaveEndData의 TotlCycle 컬럼 = 사이클러 루프 기반 논리사이클

**프로필 분석 탭**은 사용자가 입력한 사이클 번호로 물리 파일에 직접 접근한다:
- `unified_profile_core()` → `_read_raw_cycler_file()` → 사이클 번호 = 파일 번호
- 물리 사이클 ≠ 논리 사이클일 때 사용자가 의도한 사이클을 찾을 수 없음

### 1.2 문제가 되는 패턴 유형

| 패턴 | 물리 사이클 구성 | 기대 논리사이클 |
|------|-----------------|---------------|
| **일반 수명** | CC Chg + CV + Rest + CC Dchg + Rest = 1 물리사이클 | 1 논리사이클 (문제 없음) |
| **다단 CC 충전** | CC1 + CC2 + CC3 + CV = 여러 스텝, 1 물리사이클 | 1 논리사이클 (문제 없음) |
| **RPT + 가속수명** | RPT(0.2C dchg) + 가속 99회 = 100 물리사이클 | RPT 1논리사이클 + 가속 99논리사이클 |
| **GITT/HPPC** | Dchg pulse 10s + Rest 40s × N회 = N 물리사이클 | 1 논리사이클 (전체 SOC sweep) |
| **율별 용량비교** | 0.2C dchg + chg + 0.5C dchg + chg + 1C dchg + chg | 3 논리사이클 (각 rate별) 또는 1세트 |
| **DCIR (Rss)** | 짧은 dchg pulse + rest = 1 물리사이클 | GITT와 유사 — 펄스 시퀀스가 1 논리사이클 |
| **충방전 히스테리시스** | Chg profile + Dchg profile = 2 물리사이클 | 1 논리사이클 (충방전 쌍) |

### 1.3 설계 목표

1. **일관된 논리사이클**: 모든 패턴에서 "1 논리사이클 = 의미 있는 전기화학 단위"
2. **양방향 매핑**: 논리사이클 ↔ 물리사이클(+스텝) 자유 변환
3. **기존 정보 보존**: 물리 사이클 번호, 스텝 번호, Condition은 그대로 유지
4. **사이클 데이터 탭과 프로필 탭 동일 번호 체계**: 같은 논리사이클 번호가 같은 데이터를 가리킴

### 1.4 논리사이클 정의

> **논리사이클 = 사이클러 패턴의 최소 반복 단위 중 유효 방전을 1회 이상 포함하는 블록**

**유효 방전 기준**:
```
유효 방전: Condition == 2 AND Cap > mincapacity / 60
```

- mincapacity/60 = 노이즈 필터 (약 0.017C 이하 용량은 유효 방전이 아님)
- GITT 펄스: 개별 펄스는 Cap ≪ mincapacity/60 → 유효 방전이 아님
- RPT 방전: Cap > mincapacity/60 → 유효 방전

**패턴별 적용 예시**:

```
GITT/HPPC (Dchg pulse 10s × 20회):
  물리사이클:  1    2    3   ...  20   21(충전)
  Condition:   2,3  2,3  2,3 ...  2,3  1,9
  유효방전?:   ✗    ✗    ✗   ...  ✗    -
  → 전체 묶어서 누적 Cap으로 유효 방전 판정 → 1 논리사이클

RPT(0.2C) + 가속수명(1C) × 99:
  물리사이클:  1(RPT)  2(가속) ... 100(가속)
  유효방전?:   ✓       ✓       ...  ✓
  → 각각 1 논리사이클 → 100 논리사이클

율별 용량비교 (0.2C + 0.5C + 1C):
  물리사이클:  1(0.2C dchg)  2(chg)  3(0.5C dchg) ... 6(chg)
  유효방전?:   ✓             -        ✓             ...  -
  → 3 논리사이클
```

### 1.5 알고리즘 초안 — 매핑 테이블 구조

```python
@dataclass
class LogicalCycleMap:
    """논리사이클 ↔ 물리사이클 매핑 테이블."""
    mapping: dict[int, list[int]]   # logical → [physical_list]
    reverse: dict[int, int]         # physical → logical
    total_logical: int
    total_physical: int
```

**매핑 생성 알고리즘**: SaveEndData (PNE) / capacity.log (Toyo)를 순회하며 유효 방전(Condition==2, Cap > mincapacity/60) 발견 시 이전 미할당 + 현재 사이클을 1 논리사이클로 묶는다. 마지막 유효 방전 이후 남은 물리사이클은 마지막 논리사이클에 편입.

### 1.6 구현 Phase 계획

| Phase | 내용 | 구현 위치 |
|------|------|----------|
| **A**: 매핑 테이블 생성 | `build_logical_cycle_map()` 공통 함수, `df.CycleMap` 첨부 | `toyo_cycle_data()`, `pne_cycle_data()` 반환값 |
| **B**: 프로필 분석 통합 | 사용자 입력(논리) → 물리 번호 리스트 변환, 다중 물리사이클 로딩 | `unified_profile_core()`, `_load_all_unified_parallel()` |
| **C**: UI 표시 | 입력란에 "논리사이클 번호" 명시, 매핑 확인 기능 | UI layer |

**의존성**: A → B → C

### 1.7 설계 고려사항

- **매핑 생성 시점**: 사이클 데이터 로드 시 1회 생성 → 프로필 탭에서 재사용
- **매핑이 불필요한 경우**: 일반 수명 시험(1 물리 = 1 논리)에서는 항등 매핑 → 성능 영향 없음
- **GITT 특수 처리**: 개별 펄스 Cap이 mincapacity/60 이하이므로 자동 묶임. 유효 방전 판정은 **개별 물리사이클 단위**로 수행
- **기존 코드 영향**: `toyo_cycle_data()` / `pne_cycle_data()` 반환값에 CycleMap 추가, `graph_output_cycle()`은 변경 없음 (이미 논리사이클 사용)

---

## 2. 배경 / 목적 (2026-04-06 리뷰 시점)

BDT의 프로필 분석 파이프라인에서 **사용자가 UI에서 입력하는 사이클 번호**와 **실제 데이터 파싱에서 사용되는 물리 파일 번호**는 서로 다른 체계를 갖는다. 이 문서는 두 번호 체계의 관계와 변환 로직을 상세히 분석하고, 개선 가능한 포인트를 제안한다.

### 왜 두 가지 번호가 존재하는가?

- **원본사이클 (Physical/Original Cycle)**: 사이클러 장비가 기록한 물리적 파일 번호.
  - Toyo: `000001`, `000002`, ... 형태의 개별 파일 번호.
  - PNE: `TotlCycle` 값 (SaveEndData 컬럼 27).
  - 하나의 "원본사이클"이 반드시 충전-방전 한 쌍을 의미하지 않음.

- **논리사이클 (Logical Cycle)**: 사용자 관점에서 "몇 번째 충방전 사이클인가"를 나타내는 번호.
  - 1 = 첫 번째 유효한 충전-방전 쌍.
  - 화성(formation) 충전 전용 그룹, GITT 펄스 스윕 등도 독립 논리사이클로 카운트.
  - 항상 1부터 시작하며 연속적.

---

## 3. 아키텍처 개요 — 3계층 구조

```
┌─────────────────────────────────────────────────────┐
│                   UI 입력 계층                        │
│                                                       │
│  cycle_path_table col4 ──→ _get_table_cycle_input()  │
│  stepnum 위젯 ──────────→ Profile_ini_set()           │
│                              ↓                        │
│              _init_confirm_button()                    │
│              pro_continue_confirm_button()             │
│                              ↓                        │
│                         CycleNo (list[int])           │
│                    [논리사이클 번호 리스트]               │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│                 매핑 계층 (Bridge)                      │
│                                                        │
│  pne_build_cycle_map() ──→ {논리: TotlCycle | (s,e)}  │
│  toyo_build_cycle_map() ─→ {논리: (시작파일, 끝파일)}   │
│  _resolve_logical_to_tc_range()                        │
│  _get_max_logical_cycle()                              │
└──────────────────────┬─────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│                데이터 파싱 계층                          │
│                                                        │
│  unified_profile_core(cycle_range, cycle_map)          │
│    ├→ _unified_pne_load_raw(cycle_start, cycle_end)    │
│    └→ _unified_toyo_load_raw(cycle_start, cycle_end)   │
│                                                        │
│  → 항상 원본사이클(물리번호)로 파일 접근                   │
│  → Cycle 컬럼은 논리사이클 번호로 재부여                   │
└──────────────────────────────────────────────────────┘
```

---

## 4. UI 입력 계층 — 상세 분석

### 3.1 입력 소스와 우선순위

사용자가 프로필 분석할 사이클을 지정하는 경로는 **3가지**이며, 우선순위 체인으로 동작한다:

| 우선순위 | 입력 소스 | 위치 | 비고 |
|---------|----------|------|------|
| 1 (최우선) | cycle_path_table col4 (검정 폰트) | 경로 테이블 "사이클" 열 | 사용자가 직접 타이핑한 값 |
| 2 | stepnum 위젯 | "프로필 옵션" 탭 내 QPlainTextEdit | 기존 입력 방식 |
| 3 (기본값) | (빈 입력) | — | 분석 실행 불가 또는 전체 사이클 |

### 3.2 `_get_table_cycle_input()` — 테이블 사이클 입력 읽기

```python
# 위치: L13941–13965
def _get_table_cycle_input(self) -> list[int] | None:
```

**핵심 로직: 폰트 색상으로 입력 출처 판별**

```
경로 테이블 col4 읽기
  │
  ├─ 유효 경로가 있는 첫 행 탐색 (col1에 경로 존재)
  │     │
  │     ├─ col4가 비어있음 → return None (stepnum 폴백)
  │     │
  │     ├─ col4 폰트색 == 회색 (160,160,160) → return None
  │     │   (자동 감지 힌트값이므로 무시)
  │     │
  │     └─ col4 폰트색 == 검정 (사용자 입력) → convert_steplist() 파싱
  │         ├─ 성공 → return list[int]
  │         └─ 파싱 실패 → return None
  │
  └─ 유효 행 없음 → return None
```

**왜 폰트 색상을 사용하는가?**

cycle_path_table의 col4에는 두 가지 값이 들어갈 수 있다:
- **회색 (자동 감지)**: 경로를 로드할 때 자동으로 채워지는 힌트값. 참고용이므로 분석에 사용하지 않음.
- **검정 (사용자 입력)**: 사용자가 직접 타이핑한 값. 분석에 우선 사용.

이 구분은 QTableWidgetItem의 `foreground().color()`를 통해 이루어진다.

### 3.3 `_init_confirm_button()` — 통합 프로필 진입점

```python
# 위치: L13906–13939
def _init_confirm_button(self, button_widget):
```

이 함수는 `unified_profile_confirm_button()`에서 호출되며, 모든 설정값을 dict로 반환한다.

**CycleNo 결정 흐름:**

```python
config = self.Profile_ini_set()
CycleNo = config[2]                    # ① stepnum 위젯에서 읽은 기본값
table_cycle = self._get_table_cycle_input()
if table_cycle is not None:
    CycleNo = table_cycle              # ② 테이블 입력이 있으면 덮어씀
```

- `Profile_ini_set()` (L17305)에서 `convert_steplist(self.stepnum.toPlainText())`로 stepnum 위젯 값을 파싱
- `_get_table_cycle_input()`이 None이 아니면 (=사용자가 테이블에 검정 폰트로 입력) 그 값으로 교체
- 최종 `CycleNo`는 `list[int]` 타입 — **논리사이클 번호 리스트**

### 3.4 `pro_continue_confirm_button()` — 이어서 보기 진입점

```python
# 위치: L19615–19734
def pro_continue_confirm_button(self):
```

이 함수는 `ContinueConfirm` 버튼의 핸들러로, `_init_confirm_button()`을 거치지 않고 **독립적으로** 사이클 입력을 처리한다.

**CycleNo 결정 흐름 (별도 구현):**

```python
config = self.Profile_ini_set()
CycleNo = config[2]                    # 기본: stepnum

# 테이블 사이클 입력 우선, 없으면 stepnum 폴백
_table_cyc = self._get_table_cycle_input()
if _table_cyc is not None:
    _cycle_input_str = ' '.join(str(c) for c in _table_cyc)
else:
    _cycle_input_str = self.stepnum.toPlainText().strip()
```

**`_init_confirm_button()`과의 차이점:**

| 항목 | `_init_confirm_button` | `pro_continue_confirm_button` |
|------|----------------------|------------------------------|
| 반환 형태 | `list[int]` (CycleNo) | `str` (_cycle_input_str) |
| 사이클 범위 지원 | `"1-5"` → `[1, 2, 3, 4, 5]` | `"1-5"` → 문자열 그대로, 이후 재파싱 |
| 논리사이클 검증 | `_get_max_logical_cycle()` 사용 | `_get_max_logical_cycle()` 사용 |
| 코드 경로 | `_init_confirm_button()` 호출 | 인라인 구현 (중복 로직) |

---

## 5. 매핑 계층 — cycle_map 생성

### 4.1 `toyo_build_cycle_map()` — Toyo용 매핑

```python
# 위치: L2792–2900
# 반환: ({논리사이클: (시작파일번호, 끝파일번호)}, mincapacity)
```

**알고리즘 2-Pass 구조:**

```
capacity.log 파싱
  │
  ├─ Condition 시퀀스 기반 그룹핑
  │   (연속 동일 Condition을 하나의 merge_group으로)
  │
  ├─ Pass 1: 방전 기반 사이클
  │   방전 그룹 탐색 → 직전 충전 + 방전 + 직후 휴지 = 1 논리사이클
  │   - 방전 유효성: Cap > mincapacity / 60
  │   - 충전 전용 그룹은 Pass 2에서 처리
  │
  ├─ Pass 2: 충전 전용 사이클
  │   Pass 1에서 사용되지 않은 충전 그룹
  │   - 화성(formation) 공정 등 방전 없이 충전만 존재하는 경우
  │
  └─ 시작 파일 기준 정렬 → 연속 번호 부여
      cycle_map = {1: (1, 3), 2: (4, 6), 3: (7, 9), ...}
```

**cycle_map 값의 의미:**

```python
cycle_map[1] = (1, 3)
# → 논리사이클 1은 물리파일 000001~000003에 걸침
#   000001: 충전, 000002: 방전, 000003: 휴지
```

### 4.2 `pne_build_cycle_map()` — PNE용 매핑

```python
# 위치: L3075–3224
# 반환: ({논리사이클: TotlCycle값 | (시작TC, 끝TC)}, mincapacity)
```

**PNE는 시험 유형에 따라 2가지 전략을 자동 선택:**

```
SaveEndData 파싱
  │
  ├─ TotlCycle × Condition 피벗 테이블 생성
  │
  ├─ 시험 유형 판별 (우선순위)
  │   1. .sch 파일의 sweep_mode 힌트
  │   2. 유의 TC 비율 (sig_ratio) + 충방전 쌍 비율 (has_both_ratio)
  │   3. TC ≤ 5이면 일반 모드 강제
  │
  ├─ 일반 시험 (가속수명, 율별, 보관 등)
  │   → TotlCycle 단위 1:1 매핑
  │   cycle_map = {1: 1, 2: 2, 3: 3, ...}  # int 값
  │
  └─ 스윕 시험 (GITT, DCIR 등)
      → 방향 기반 그룹핑으로 스윕 범위 매핑
      cycle_map = {1: (1, 15), 2: (16, 30), ...}  # tuple 값
```

**핵심 차이: cycle_map 값의 타입이 다름**

| 사이클러 | 일반 시험 값 | 스윕 시험 값 |
|---------|-----------|------------|
| Toyo | `(시작파일, 끝파일)` — 항상 tuple | — |
| PNE | `int` (단일 TotlCycle) | `(시작TC, 끝TC)` — tuple |

이 타입 불일치는 하위 함수들이 `isinstance(val, tuple)` 분기로 처리한다.

### 4.3 `_resolve_logical_to_tc_range()` — 논리→물리 범위 변환

```python
# 위치: L5258–5298
# 논리사이클 범위 → 물리사이클 연속 범위로 변환
```

이 함수는 `pro_continue_confirm_button`의 fallback 경로에서 호출된다:

```
논리사이클 범위 (start, end)
  ↓ cycle_map 조회
  ↓ 각 논리사이클의 물리값 중 min/max 추출
  ↓
물리사이클 범위 (tc_min, tc_max)
```

### 4.4 `_get_max_logical_cycle()` — 최대 논리사이클 조회

```python
# 위치: L5301–5337
# 첫 번째 유효 채널의 cycle_map에서 max(keys()) 반환
```

사용자 입력 검증에 사용: 입력된 사이클 번호가 최대 논리사이클을 초과하면 경고 메시지를 표시하고 초과분을 제거한다.

---

## 6. 데이터 파싱 계층 — unified_profile_core

### 5.1 6단계 파이프라인

```python
# 위치: L1398–1548
# unified_profile_core(raw_file_path, cycle_range, mincapacity, inirate, *, cycle_map=None, ...)
```

```
Stage 1: 사이클러 판별 + cycle_map 자동 생성 + 원시 로딩
  │  is_pne = check_cycler(raw_file_path)
  │  cycle_map이 None이면 → pne_build_cycle_map() / toyo_build_cycle_map() 호출
  │  _unified_pne_load_raw() / _unified_toyo_load_raw()
  │
Stage 2: Condition 필터링 (충전/방전/사이클 scope)
  │
Stage 3: 정규화 (μV→V, μA→mA, μAh→mAh 등)
  │
Stage 4: 스텝 병합 (연속 동일 Condition 통합)
  │
Stage 5: X축 계산 (시간/SOC) + 연속성(오버레이/이어서)
  │
Stage 6: dQ/dV 계산 (선택)
```

### 5.2 cycle_range 파라미터의 의미

`cycle_range = (start, end)`는 **논리사이클 번호**이다.

```python
# unified_profile_core 내부에서:
cycle_start, cycle_end = cycle_range  # 논리사이클 범위

# cycle_map이 None이면 자동 생성
if cycle_map is None:
    cycle_map, _ = toyo_build_cycle_map(raw_file_path, ...)

# _unified_toyo_load_raw에서 cycle_map을 사용하여 물리파일 접근
raw = _unified_toyo_load_raw(raw_file_path, cycle_start, cycle_end, cycle_map=cycle_map)
```

### 5.3 데이터 로딩에서의 논리→물리 변환

**Toyo (`_unified_toyo_load_raw`, L873–969):**

```python
if cycle_map:
    for logical_cyc in range(cycle_start, cycle_end + 1):
        first_file, last_file = cycle_map[logical_cyc]  # 논리 → 물리 범위
        for phys_cyc in range(first_file, last_file + 1):
            # 물리파일 000001 등을 직접 읽음
            tempdata = toyo_Profile_import(raw_file_path, phys_cyc)
            df_cyc["Cycle"] = logical_cyc         # Cycle 컬럼 = 논리번호
            df_cyc["PhysicalCycle"] = phys_cyc     # 원본 물리번호 보존
```

**PNE (`_unified_pne_load_raw`, L742–870):**

```python
if cycle_map:
    for logical_cyc in range(cycle_start, cycle_end + 1):
        val = cycle_map[logical_cyc]
        if isinstance(val, tuple):
            tc_start, tc_end = val  # 스윕 범위
            for tc in range(tc_start, tc_end + 1):
                totl_cycles_set.add(tc)
                logical_to_totl[tc] = logical_cyc  # 역매핑 생성
        else:
            totl_cycles_set.add(val)    # 단일 TC
            logical_to_totl[val] = logical_cyc

    # TotlCycle 범위로 CSV 파일 검색 후 로딩
    # Cycle 컬럼을 논리사이클로 재매핑
    result["PhysicalCycle"] = result["Cycle"].copy()
    result["Cycle"] = result["Cycle"].map(logical_to_totl)
```

**핵심 원칙**: 데이터 파싱 계층은 **항상 원본사이클(물리번호)로 파일에 접근**하고, 결과 DataFrame의 `Cycle` 컬럼은 **논리사이클 번호로 재부여**한다. 원본 물리번호는 `PhysicalCycle` 컬럼에 보존된다.

---

## 7. 전체 데이터 흐름 — End-to-End 예시

### 예시: Toyo 사이클러에서 논리사이클 3번 프로필 분석

```
사용자 입력: cycle_path_table col4에 "3" 입력 (검정 폰트)

① UI 입력 계층
   _get_table_cycle_input() → [3]
   _init_confirm_button() → CycleNo = [3]

② 매핑 계층
   toyo_build_cycle_map(raw_path, ...)
   → cycle_map = {1: (1,3), 2: (4,6), 3: (7,9), 4: (10,12), ...}
   → 논리사이클 3 = 물리파일 (7, 9)

③ 데이터 파싱 계층
   unified_profile_core(raw_path, cycle_range=(3,3), cycle_map=cycle_map)
   → _unified_toyo_load_raw():
     - 물리파일 000007, 000008, 000009 로딩
     - Cycle 컬럼 = 3 (논리번호)
     - PhysicalCycle = 7, 8, 9 (물리번호)
   → Stage 2~6: 필터링, 정규화, 축 계산

④ 결과
   - 그래프 범례: "사이클 3" (논리번호)
   - 내부 데이터: 물리파일 7~9의 원시 데이터
```

### 예시: PNE 스윕 시험에서 논리사이클 2번

```
① cycle_map = {1: (1, 15), 2: (16, 30), 3: (31, 45)}
   → 논리사이클 2 = TotlCycle 16~30

② _unified_pne_load_raw():
   - TotlCycle 16~30 범위의 SaveData 로딩
   - 각 row의 Cycle = 2 (논리번호)
   - PhysicalCycle = 원본 TotlCycle 값
```

---

## 8. 개선 제안

### 7.1 `pro_continue_confirm_button()`의 사이클 입력 로직 통합 (중복 제거)

**현재 문제**: `_init_confirm_button()`과 `pro_continue_confirm_button()`에서 동일한 테이블 우선→stepnum 폴백 로직이 **중복 구현**되어 있다.

```python
# _init_confirm_button() — dict 반환
CycleNo = config[2]
table_cycle = self._get_table_cycle_input()
if table_cycle is not None:
    CycleNo = table_cycle

# pro_continue_confirm_button() — 문자열 기반 별도 구현
_table_cyc = self._get_table_cycle_input()
if _table_cyc is not None:
    _cycle_input_str = ' '.join(str(c) for c in _table_cyc)
else:
    _cycle_input_str = self.stepnum.toPlainText().strip()
```

**제안**: `pro_continue_confirm_button()`도 `_init_confirm_button()`을 호출하도록 리팩토링. 현재 `pro_continue_confirm_button()`이 `_init_confirm_button()`을 사용하지 않는 이유는 반환 형태가 다르기 때문이지만, `_init_confirm_button()`이 반환하는 `CycleNo` (list[int])를 활용하면 중복을 제거할 수 있다.

```python
# 개선안 (개념)
def pro_continue_confirm_button(self):
    init_data = self._init_confirm_button(self.ContinueConfirm)
    CycleNo = init_data['CycleNo']
    # CycleNo를 range 쌍으로 변환하는 기존 로직 계속 사용
    chg_dchg_dcir_no = _convert_cycle_list_to_ranges(CycleNo)
    ...
```

### 7.2 행별(row-by-row) 사이클 입력 지원

**현재 한계**: `_get_table_cycle_input()`은 **첫 번째 유효 행의 col4만** 읽는다. 경로 테이블에 복수 행(=복수 테스트)이 있어도 첫 행의 사이클 입력만 적용된다.

```python
# 현재: 첫 행만 읽음
for r in range(tbl.rowCount()):
    path = self._get_table_cell(r, 1)
    if not path:
        continue
    cyc_text = self._get_table_cell(r, 4)
    ...
    return convert_steplist(cyc_text)  # ← 즉시 return
```

**제안**: 행별로 다른 사이클 번호를 입력하여 각 테스트에 서로 다른 사이클을 분석할 수 있도록 확장.

```python
# 개선안 (개념)
def _get_table_cycle_inputs(self) -> list[list[int] | None]:
    """각 행별 사이클 입력을 리스트로 반환."""
    result = []
    for r in range(tbl.rowCount()):
        path = self._get_table_cell(r, 1)
        if not path:
            result.append(None)
            continue
        cyc_text = self._get_table_cell(r, 4)
        if not cyc_text or _is_gray(item):
            result.append(None)  # 이 행은 기본값 사용
        else:
            result.append(convert_steplist(cyc_text))
    return result
```

**주의**: 이 변경은 하위 파이프라인에도 영향을 미치므로 (각 폴더별로 CycleNo가 달라짐) `unified_profile_confirm_button()`의 루프 구조 수정이 필요하다.

### 7.3 cycle_map 캐싱

**현재 문제**: cycle_map은 필요할 때마다 매번 재생성된다. 동일 채널에 대해 여러 사이클을 분석하면 같은 capacity.log / SaveEndData를 반복 파싱하게 된다.

**발생 지점 예시:**

```python
# _get_max_logical_cycle() — 검증용 cycle_map 생성
cm, _ = _get_pne_cycle_map(folder_path, mincapacity, inirate)

# unified_profile_core() — 데이터 로딩용 cycle_map 생성
if cycle_map is None:
    cycle_map, _ = toyo_build_cycle_map(raw_file_path, ...)

# pro_continue_confirm_button() fallback — 또 한 번 생성
cm, _ = toyo_build_cycle_map(FolderBase, mincapacity, firstCrate)
```

**제안**: `lru_cache` 또는 인스턴스 변수를 활용한 cycle_map 캐싱.

```python
# 개선안 (개념)
from functools import lru_cache

@lru_cache(maxsize=32)
def _cached_cycle_map(raw_file_path: str, mincapacity: float, inirate: float):
    is_pne = check_cycler(raw_file_path)
    if is_pne:
        return _get_pne_cycle_map(raw_file_path, mincapacity, inirate)
    else:
        return toyo_build_cycle_map(raw_file_path, mincapacity, inirate)
```

**캐시 무효화 시점**: 경로 테이블이 변경되거나, 탭이 리셋될 때 캐시를 클리어해야 한다. `mincapacity`가 다르면 다른 cycle_map이 나올 수 있으므로 인자를 캐시 키에 포함해야 한다.

### 7.4 cycle_map 값 타입 통일

**현재 문제**: PNE의 일반 시험은 `int`, 스윕 시험은 `tuple[int, int]`를 반환한다. 하위 함수마다 `isinstance(val, tuple)` 분기가 필요하다.

```python
# 현재 (여러 곳에서 반복)
if isinstance(val, tuple):
    s, e = val
else:
    s, e = val, val
```

**제안**: 모든 cycle_map 값을 `tuple[int, int]`로 통일.

```python
# 일반 시험도 (tc, tc) tuple로 저장
cycle_map[ln] = (tc, tc)  # 현재: cycle_map[ln] = tc
```

이렇게 하면 모든 하위 함수에서 `isinstance` 분기 없이 일관되게 `(s, e) = cycle_map[ln]`으로 접근할 수 있다.

**영향 범위**: `_unified_pne_load_raw`, `_resolve_logical_to_tc_range`, `_pne_build_sweep_cycle_map`, `pro_continue_confirm_button` 등.

### 7.5 사용자 입력 검증 강화

**현재 한계**:
- `convert_steplist()`는 `"abc"` 같은 비정수 입력에서 `ValueError`를 발생시키고, `_get_table_cycle_input()`이 이를 `try-except`로 잡아 `None` 반환.
- 사용자에게 **왜 입력이 무시되었는지** 피드백이 없음.

**제안**: 파싱 실패 시 `QMessageBox.warning`으로 안내.

```python
# 개선안 (개념)
try:
    return convert_steplist(cyc_text)
except (ValueError, TypeError) as e:
    # 현재: 조용히 None 반환
    # 개선: 사용자에게 알림
    logger.warning("테이블 사이클 입력 파싱 실패: %s → %s", cyc_text, e)
    return None
```

### 7.6 논리사이클 매핑 정보 UI 표시

**현재 상태**: `cycle_map_info_label` (L-cycle_path_table 하단)이 존재하지만, 매핑 정보가 표시되는 시점과 내용이 제한적일 수 있음.

**제안**: 경로 로드 시 자동으로 cycle_map을 빌드하고, 총 논리사이클 수와 주요 매핑 정보를 `cycle_map_info_label`에 표시.

```
"논리사이클: 총 85개 (물리파일 1~255 매핑) | 타입: Toyo 일반"
```

이렇게 하면 사용자가 입력해야 할 사이클 번호의 범위를 직관적으로 파악할 수 있다.

---

## 9. 핵심 Python 문법 / 패턴 설명

### 8.1 `isinstance(val, tuple)` 패턴 — 다형 딕셔너리 값 처리

```python
val = cycle_map[logical_cyc]
if isinstance(val, tuple):
    s, e = val           # 스윕: (시작TC, 끝TC)
else:
    s, e = val, val      # 일반: 단일 TC를 범위로 확장
```

Python에서 딕셔너리의 값이 여러 타입을 가질 수 있을 때 `isinstance`로 분기하는 패턴이다. 타입힌트로는 `dict[int, int | tuple[int, int]]`로 표현된다.

### 8.2 `foreground().color()` — Qt 위젯의 글꼴 색상 비교

```python
_auto_fg = QtGui.QColor(160, 160, 160)
item = tbl.item(r, 4)
if item and item.foreground().color() == _auto_fg:
    return None
```

`QTableWidgetItem.foreground()`는 `QBrush` 객체를 반환하고, `.color()`로 `QColor`를 추출한다. `QColor` 객체 간 `==` 비교는 RGB 값 기준으로 동작한다.

### 8.3 `convert_steplist()` — 범위 문자열을 정수 리스트로

```python
convert_steplist("1 3-5 8")  # → [1, 3, 4, 5, 8]
convert_steplist("1-3, 7")   # → [1, 2, 3, 7]
```

쉼표나 공백을 구분자로 분리하고, `-`가 있으면 `range(start, end+1)`로 확장한다. 사이클 번호뿐 아니라 스텝 번호 입력에도 공용으로 사용되는 유틸리티 함수이다.

### 8.4 2-Pass 알고리즘 — toyo_build_cycle_map

Pass 1에서 방전 기반 사이클을 먼저 수집하고, Pass 2에서 사용되지 않은 충전 전용 사이클을 추가하는 패턴이다. 이렇게 하는 이유는:
- 방전이 있는 사이클이 "정상적인" 충방전 사이클
- 방전 없이 충전만 있는 사이클은 화성(formation), 프리차지 등의 특수 경우
- Pass 1에서 이미 사용된 충전 그룹을 `used_indices` set으로 추적하여 중복 방지

---

## 10. 요약

| 계층 | 핵심 역할 | 사이클 타입 |
|------|----------|-----------|
| UI 입력 | 사용자로부터 사이클 번호를 받음 | **논리사이클** (사용자 관점) |
| 매핑 (Bridge) | 논리사이클 ↔ 물리사이클 변환 테이블 생성 | 논리 → 물리 변환 |
| 데이터 파싱 | 물리번호로 파일 접근, 논리번호로 결과 표시 | **물리사이클** (파일 접근) |

**핵심 원칙**: UI에서는 논리사이클을 입출력하고, 데이터 파싱에서는 원본사이클(물리번호)로 동작한다. `cycle_map`이 이 두 세계를 연결하는 유일한 다리이다.

**주요 개선 제안 요약:**

1. `pro_continue_confirm_button` 로직을 `_init_confirm_button` 호출로 통합 (코드 중복 제거)
2. 행별 사이클 입력 지원 (복수 테스트별 다른 사이클 분석)
3. cycle_map 캐싱 (동일 채널 반복 파싱 방지)
4. cycle_map 값 타입 통일 — 항상 `tuple[int, int]` (isinstance 분기 제거)
5. 파싱 실패 시 사용자 피드백 추가
6. 논리사이클 매핑 정보를 UI에 표시
