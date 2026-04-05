# 논리사이클(Logical Cycle) 설계 문서

## 1. 현황 분석

### 1.1 현재 "사이클" 정의 — 탭별 차이

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

### 1.3 핵심 문제

> **물리사이클 번호 → 논리사이클 번호 매핑이 없으면, 사용자가 "3번째 사이클 프로필"을 요청해도 실제 3번째 논리사이클 데이터를 찾을 수 없다.**

---

## 2. 설계 목표

1. **일관된 논리사이클**: 모든 패턴에서 "1 논리사이클 = 의미 있는 전기화학 단위"
2. **양방향 매핑**: 논리사이클 ↔ 물리사이클(+스텝) 자유 변환
3. **기존 정보 보존**: 물리 사이클 번호, 스텝 번호, Condition은 그대로 유지
4. **사이클 데이터 탭과 프로필 탭 동일 번호 체계**: 같은 논리사이클 번호가 같은 데이터를 가리킴

---

## 3. 논리사이클 정의

### 3.1 원칙

> **논리사이클 = 사이클러 패턴의 최소 반복 단위 중 유효 방전을 1회 이상 포함하는 블록**

이 정의는 기존 `toyo_cycle_data()`의 로직(유효 방전 1회 = 1 사이클)과 일관된다.

### 3.2 유효 방전 기준 (기존 로직 재사용)

```
유효 방전: Condition == 2 AND Cap > mincapacity / 60
```

- mincapacity/60 = 노이즈 필터 (약 0.017C 이하 용량은 유효 방전이 아님)
- GITT 펄스: 개별 펄스는 Cap ≪ mincapacity/60 → 유효 방전이 아님
- RPT 방전: Cap > mincapacity/60 → 유효 방전

### 3.3 패턴별 적용 예시

**GITT/HPPC (Dchg pulse 10s × 20회):**
```
물리사이클:  1    2    3   ...  20   21(충전)
Condition:   2,3  2,3  2,3 ...  2,3  1,9
유효방전?:   ✗    ✗    ✗   ...  ✗    -
→ 전체 묶어서 누적 Cap으로 유효 방전 판정 → 1 논리사이클
```

**RPT(0.2C) + 가속수명(1C) × 99:**
```
물리사이클:  1(RPT)  2(가속)  3(가속) ... 100(가속)  101(RPT)
유효방전?:   ✓       ✓        ✓       ...  ✓          ✓
→ 각각 1 논리사이클 → 100 논리사이클
```

**율별 용량비교 (0.2C dchg + chg + 0.5C dchg + chg + 1C dchg + chg):**
```
물리사이클:  1(0.2C dchg)  2(chg)  3(0.5C dchg)  4(chg)  5(1C dchg)  6(chg)
유효방전?:   ✓             -        ✓              -        ✓           -
→ 3 논리사이클
```

---

## 4. 알고리즘 설계

### 4.1 매핑 테이블 구조

```python
@dataclass
class LogicalCycleMap:
    """논리사이클 ↔ 물리사이클 매핑 테이블."""

    # 핵심 매핑: logical_cycle → [physical_cycle_list]
    # key: 논리사이클 번호 (1-based)
    # value: 해당 논리사이클에 속하는 물리사이클 번호 리스트
    mapping: dict[int, list[int]]

    # 역매핑: physical_cycle → logical_cycle
    reverse: dict[int, int]

    # 메타데이터
    total_logical: int
    total_physical: int
```

### 4.2 매핑 생성 알고리즘

**입력**: SaveEndData (PNE) 또는 capacity.log (Toyo) — 기존 로딩 함수가 이미 파싱하는 데이터

```python
def build_logical_cycle_map(
    cycle_summary: pd.DataFrame,  # Condition, Cap 컬럼 포함
    mincapacity: float,
) -> LogicalCycleMap:
    """물리사이클 데이터로부터 논리사이클 매핑을 생성.

    알고리즘:
    1. 물리사이클 순서대로 순회
    2. 유효 방전(Condition==2, Cap > mincapacity/60) 발견 시:
       - 이전 미할당 물리사이클들 + 현재 사이클 = 1 논리사이클
    3. 마지막 유효 방전 이후 남은 물리사이클 → 마지막 논리사이클에 편입
    """
```

### 4.3 프로필 데이터 접근 시 활용

```python
# 기존: 사용자 입력 사이클 번호 → 물리 파일 직접 접근
physical_cycle = user_input_cycle  # 문제: 논리사이클과 불일치

# 개선: 사용자 입력 논리사이클 번호 → 매핑 → 물리 파일 접근
physical_cycles = cycle_map.mapping[user_input_cycle]
# physical_cycles = [3, 4, 5]  ← GITT의 경우 여러 물리사이클
# 각 물리사이클의 raw data를 로드 후 합치기
```

---

## 5. 구현 계획

### Phase A: 매핑 테이블 생성 (핵심)

**위치**: `toyo_cycle_data()` / `pne_cycle_data()` 반환값에 매핑 추가

| 항목 | 설명 |
|------|------|
| `build_logical_cycle_map()` | 물리→논리 매핑 함수 (공통) |
| `df.CycleMap` | cycle_data 결과에 매핑 테이블 첨부 |
| 기존 `df.NewData.Cycle` | 변경 없음 (이미 논리사이클) |

### Phase B: 프로필 분석 통합

**위치**: `unified_profile_core()` / `_load_all_unified_parallel()`

| 항목 | 설명 |
|------|------|
| 사이클 번호 변환 | 사용자 입력(논리) → 물리 번호 리스트 |
| 다중 물리사이클 로딩 | GITT 등에서 여러 파일 합산 |
| 기존 물리 사이클/스텝 컬럼 보존 | `PhysicalCycle`, `Step` 컬럼 유지 |

### Phase C: UI 표시

| 항목 | 설명 |
|------|------|
| 사이클 입력란 | "논리사이클 번호" 명시 |
| 매핑 확인 기능 | 논리→물리 매핑 테이블 조회 (선택사항) |

### 의존성

```
Phase A (매핑 테이블)
   ↓
Phase B (프로필 통합)  ← 현재 unified_profile 리팩토링과 연결
   ↓
Phase C (UI)
```

---

## 6. 고려사항

### 6.1 매핑 생성 시점

매핑은 **사이클 데이터를 처음 로드할 때 1회** 생성하면 된다.
- 사이클 데이터 탭에서 먼저 로드 → 매핑 캐시
- 프로필 탭에서 재사용
- 사이클 데이터 미로드 시 → 프로필 탭에서 자동 생성

### 6.2 매핑이 불필요한 경우

일반 수명 시험(1 물리사이클 = 1 논리사이클)에서는 매핑이 항등(identity)이므로 성능 영향 없음.

### 6.3 GITT 특수 처리

GITT에서 개별 펄스의 Cap이 mincapacity/60 이하이므로 자동으로 묶인다.
단, 전체 SOC sweep의 **누적** 방전 용량이 mincapacity/60을 넘으면 논리사이클 경계가 생길 수 있다.
→ 해결: 유효 방전 판정을 **개별 물리사이클 단위**로 수행 (누적 아님)

### 6.4 기존 코드 영향

| 기존 함수 | 변경 필요 |
|-----------|----------|
| `toyo_cycle_data()` | 반환값에 CycleMap 추가 |
| `pne_cycle_data()` | 반환값에 CycleMap 추가 |
| `graph_output_cycle()` | 변경 없음 (이미 논리사이클 사용) |
| `unified_profile_core()` | 물리사이클 번호 대신 논리사이클 번호 수용 |
| `unified_profile_batch()` | CycleMap 참조하여 물리 파일 로딩 |
| `_load_all_unified_parallel()` | CycleMap 기반 파일 접근 |
