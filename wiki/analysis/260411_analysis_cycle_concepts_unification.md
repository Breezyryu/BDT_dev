# TC, 논리사이클, UI 사이클, 사이클 바 — 동작 방식 정리 및 통일 제안

> **작성일**: 2026-04-11
> **대상 파일**: `DataTool_dev/DataTool_optRCD_proto_.py`
> **목적**: 4가지 사이클 개념의 현재 동작을 정리하고, 불일치를 식별하여 통일 방향을 제안

---

## 1. 4가지 사이클 개념 요약

| 개념 | 정의 | 값의 예 | 저장 위치 |
|------|------|---------|----------|
| **TC (TotlCycle)** | 충방전기 물리적 사이클 번호 | 1, 2, 3, ..., 1200 | `Cycleraw["TotlCycle"]` |
| **논리사이클** | TC를 의미 있는 단위로 그룹핑한 번호 | 1, 2, 3, ..., N (≤ TC 수) | `cycle_map`, `NewData["Cycle"]` |
| **UI 사이클** | 그래프/테이블에 표시되는 사이클 번호 | `NewData.index` 또는 `NewData["Cycle"]` | 그래프 X축 |
| **사이클 바** | 세트 탭의 그래프 스케일 컨트롤 | X축 간격, Y축 상하한 | `tcyclerng`, `tcyclerngyhl`, `tcyclerngyll` |

---

## 2. TC (TotlCycle) — 물리적 사이클 번호

### 정의

충방전기 장비가 기록하는 **원시(raw) 사이클 카운터**. 충전/방전 스텝이 완료될 때마다 1씩 증가.

### PNE에서의 TC

```
SaveEndData.csv 의 28번째 컬럼(인덱스 27)
→ Cycleraw["TotlCycle"]으로 로드 (L3854)
→ Cycleraw["OriCycle"] = Cycleraw["TotlCycle"]로 보존 (PNE cycle_map 내부)
```

- **단위**: 정수 (1, 2, 3, ...)
- **특징**: 스텝 단위 카운트. 하나의 수명 사이클(충전→방전) 안에 TC가 1개일 수도, 여러 개(GITT: 수십 개)일 수도 있음
- **예**: 100사이클 수명시험 = TC 1~100, GITT 10포인트 = TC 1~100+

### TOYO에서의 TC

```
capacity.log 파일의 각 행 → Cycleraw["TotlCycle"]
→ Cycleraw["OriCycle"] = Cycleraw["TotlCycle"]로 보존 (L3214, L3449)
```

- **단위**: 정수 (capacity.log 행 순서)
- **특징**: 6자리 파일명 (`000001`, `000002`, ...)과 동일한 값. 프로필 데이터 파일 경로 조합에 사용:
  ```python
  os.path.join(channel_path, '%06d' % totl_cycle)  # L5036
  ```

### TC의 역할

| 용도 | 설명 |
|------|------|
| 파일 I/O | TOYO 프로필 파일명 생성 (`%06d`), PNE 스텝 데이터 조회 |
| `NewData["OriCyc"]` | 물리 TC 보존 — 그래프에서 원래 사이클 참조 |
| cycle_map의 값 | `{'all': (start_tc, end_tc), 'chg': [tc_list], ...}` |
| DCIR 파일 연결 | TOYO `dcir.csv`의 인덱스 매칭 |

---

## 3. 논리사이클 (Logical Cycle) — cycle_map 기반 매핑

### 정의

물리적 TC를 **의미 있는 시험 단위(사이클)**로 그룹핑한 번호. 
- 수명시험: TC 1 = 논리사이클 1 (1:1)
- GITT: TC 1~10 = 논리사이클 1, TC 11~20 = 논리사이클 2 (N:1)

### 생성 함수

| 함수 | 라인 | 사이클러 | 전략 |
|------|------|---------|------|
| `pne_build_cycle_map()` | L3806 | PNE | .sch 힌트 우선 → 데이터 휴리스틱 |
| `toyo_build_cycle_map()` | L3428 | TOYO | capacity.log 기반 Condition 시퀀스 |
| `_pne_build_sweep_cycle_map()` | L3587 | PNE (스윕) | 방향 기반 그룹핑 |

### PNE 매핑 전략

```
판별 우선순위:
1. sch_struct.sweep_mode (True/False) — .sch 파일 기반 확정 판별
2. sig_ratio ≥ 0.5 AND has_both_ratio ≥ 0.3 → 일반 모드
3. 나머지 → 스윕 모드

임계값: threshold = mincapacity × 1000 × 0.2 (공칭 20%)
```

**일반 시험** (L3895-3971):
- 유의 TC (공칭 20% 이상) = 개별 논리사이클
- 비유의 TC 연속 블록 = 하나의 논리사이클로 묶음
- 단방향 유의 TC + 후속 비유의 블록 = 하나로 병합 (DCIR 준비단계 등)

**스윕 시험** (L3587-3803):
- `.sch` 분석으로 반복 블록 구간 식별
- 방향 기반: 충전 TC, 방전 TC, 휴지 TC를 각각 분류
- 반대 방향 쌍이 하나의 논리사이클

### TOYO 매핑 전략

```
규칙 1: 충전 → 방전 → (휴지) = 1 논리사이클  (L3483-3513)
규칙 2: 충전 전용 그룹 = 독립 논리사이클        (L3515-3533)
규칙 3: cap_threshold = mincapacity / 60
```

- Pass 1: 방전 기반 사이클 (충전 + 방전 + 방전 후 휴지)
- Pass 2: 충전 전용 사이클 (방전 없이 충전만 있는 그룹)
- 시작 파일 기준 정렬 → 논리사이클 번호 부여

### cycle_map 자료구조 (통일됨)

```python
cycle_map = {
    1: {'all': (1, 1),   'chg': [1],  'dchg': [1],  'chg_rest': [], 'dchg_rest': []},
    2: {'all': (2, 2),   'chg': [2],  'dchg': [2],  'chg_rest': [], 'dchg_rest': []},
    3: {'all': (3, 15),  'chg': [3],  'dchg': [4,6,8,10,12,14], 'chg_rest': [], 'dchg_rest': [5,7,9,11,13,15]},
    ...
}
# key = 논리사이클 번호
# 'all' = (시작TC, 끝TC) — 해당 논리사이클의 물리적 범위
# 'chg'/'dchg'/'chg_rest'/'dchg_rest' = 방향별 TC 목록
```

### 변환 함수

| 함수 | 라인 | 방향 | 설명 |
|------|------|------|------|
| `_logical_to_totl_str()` | L553 | 논리 → TC | `"1-3, 5"` → `"10-18, 25"` |
| `_totl_to_logical_str()` | L587 | TC → 논리 | `"10-18, 25"` → `"1-3, 5"` |
| `resolve_tc_range()` | L864 | 논리+scope → TC범위 | scope별(chg/dchg/all) TC 범위 |
| `_cm_tc_list()` | L823 | entry+scope → TC목록 | cycle_map entry에서 TC 목록 추출 |

### NewData에 반영되는 방식 (L7865-7921)

```python
# cycle_map이 있을 때:
if cycle_map and len(df.NewData) > 0:
    # 스윕 시험 → groupby 집계 (같은 논리사이클의 행을 하나로)
    if _is_sweep:
        _grouped = _mapped.groupby('_ln').agg({...})
        _grouped.rename(columns={'_ln': 'Cycle'})
    # 일반 시험 → 순번 부여 (1, 2, 3, ...)
    else:
        df.NewData.insert(0, 'Cycle', range(1, len(df.NewData) + 1))
else:
    # cycle_map 없음 → 순번 (1, 2, 3, ...)
    df.NewData.insert(0, "Cycle", range(1, len(df.NewData) + 1))
```

---

## 4. UI 사이클 — 그래프에 표시되는 번호

### 정의

사용자가 실제로 보는 사이클 번호. 그래프 X축, 경로 테이블 "사이클" 컬럼에 표시.

### 표시 방식

#### 사이클 탭 그래프 (`graph_output_cycle`, L2659)

```python
# X축 = NewData.index (0-based 정수 인덱스, NOT Cycle 컬럼)
graph_cycle(df.NewData.index, df.NewData.Dchg, ax1, ...)
graph_cycle(df.NewData.index, df.NewData.Eff, ax2, ...)
graph_cycle(df.NewData.index, df.NewData.Temp, ax3, ...)
```

**⚠️ 현재 문제점**: `df.NewData.index`는 `reset_index(drop=True)` 후의 0-based 인덱스이므로, **논리사이클 번호(1-based)가 아니라 행 순번(0-based)**이 표시됨. 
- 사이클 1개 삭제되면 인덱스가 뒤로 밀림
- `Cycle` 컬럼이 있지만 그래프에는 사용되지 않음

#### 경로 테이블 (cycle_path_table)

| 컬럼 | 이름 | 내용 | 입출력 |
|------|------|------|--------|
| 4 | 사이클 | **논리사이클** 번호 | 사용자 입력 |
| 5 | Raw | **TotlCycle** 번호 | 자동 변환 (L20643) |

```python
# L20643: 사이클(논리) → Raw(TC) 자동 변환
def _on_cycle_cell_changed(self, row, col):
    if col == 4:  # "사이클" 컬럼 변경 시
        logical_str = self.cycle_path_table.item(row, 4).text()
        raw_str = _logical_to_totl_str(cycle_map, logical_str)
        self.cycle_path_table.item(row, 5).setText(raw_str)
```

#### 세트 탭 그래프 (`set_cycle_button`, L24798)

```python
# X축 = Battery_Cycle (스마트폰 로그의 원시 사이클)
graph_cycle(df["Battery_Cycle"], df["ASOC1"], ax1, ...)
```

**주의**: 세트 탭은 cycle_map/논리사이클을 **사용하지 않음** — 스마트폰 로그 자체 사이클 번호를 직접 사용.

### 사이클 표시 모드 (세트 탭, L10517-10613)

| 라디오 버튼 | 이름 | 동작 |
|------------|------|------|
| `realcyc` | **실제 사이클** | 스마트폰 로그의 `Battery_Cycle` 그대로 표시 |
| `resetcycle` | **보정 사이클** ✓ (기본) | 충전↔방전 전환점을 재카운트 (보정 알고리즘, L8573-8586) |
| `allcycle` | **전체 사이클** | 전체 범위 표시 |
| `recentcycle` | **최근 사이클** ✓ (기본) | 마지막 N사이클만 표시 (기본 20) |
| `manualcycle` | **지정 사이클** | 사용자 지정 범위 |

**⚠️ 혼란 요소**: `realcyc`/`resetcycle`은 **세트 탭(Battery_Cycle 로그)**에만 해당되며, 사이클 탭의 TC/논리사이클과는 **완전히 별개** 시스템.

---

## 5. 사이클 바 — 그래프 스케일 컨트롤

### 정의

그래프의 축 범위와 간격을 조절하는 UI 입력 필드. "사이클 범위" 자체가 아닌 **표시 스케일 파라미터**.

### 사이클 탭 위젯

| 위젯 | 기본값 | 용도 |
|------|--------|------|
| `tcyclerng` | 0 | X축 눈금 간격 (0=자동) |
| `tcyclerngyhl` | 1.10 | Y축 상한 (방전용량비) |
| `tcyclerngyll` | 0.65 | Y축 하한 (방전용량비) |
| `dcirscale` | 1 | DCIR Y축 배율 |

### 세트 탭 위젯

| 위젯 | 기본값 | 용도 |
|------|--------|------|
| `setcyclexscale` | 0 | X축 눈금 간격 |

### 사용 방식 (L15475-15479)

```python
self.xscale = int(self.tcyclerng.text())        # → graph_output_cycle()의 xscale
self.setxscale = int(self.setcyclexscale.text()) # → set_cycle_button()의 setxscale
self.ylimithigh = float(self.tcyclerngyhl.text())
self.ylimitlow = float(self.tcyclerngyll.text())
```

**스케일이 적용되는 곳**: `graph_cycle()` 함수에서 X축 tick 간격, Y축 범위에 사용.

---

## 6. 전체 데이터 흐름

```
┌─────────────────────────────────────────────────────────────────┐
│ Phase 0: 채널 메타데이터 수집                                      │
│ _build_channel_meta() → ChannelMeta (min_capacity, cycle_map 등) │
└───────────────────────────┬─────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1: cycle_map 생성                                          │
│                                                                   │
│ PNE: pne_build_cycle_map()                                       │
│   SaveEndData[27] → TotlCycle → sig_ratio 판별                   │
│   → 일반: TC 1:1 매핑 (유의 TC 기준)                                │
│   → 스윕: 방향 기반 그룹핑                                          │
│                                                                   │
│ TOYO: toyo_build_cycle_map()                                     │
│   capacity.log → TotlCycle → Condition 시퀀스 분석                 │
│   → 충전→방전→(휴지) = 1 논리사이클                                 │
│   → 충전전용 = 독립 논리사이클                                      │
│                                                                   │
│ 결과: {1: {'all': (s,e), 'chg':[], 'dchg':[], ...}, 2: ...}     │
└───────────────────────────┬─────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 2: NewData 생성                                            │
│                                                                   │
│ PNE: pne_cycle_data() (L8082) → pivot → Dchg, Chg, Eff, ...     │
│ TOYO: toyo_cycle_data() (L3201) → merge_rows → Dchg, Chg, ...  │
│                                                                   │
│ → OriCycle = Dchg.index (물리 TC)                                 │
│ → NewData 생성 + reset_index(drop=True)                          │
│ → cycle_map 있으면:                                                │
│     스윕: OriCyc → 논리사이클 매핑 → groupby 집계 → Cycle 컬럼     │
│     일반: Cycle 컬럼 = range(1, len+1) (순번)                     │
│ → cycle_map 없으면:                                                │
│     Cycle 컬럼 = range(1, len+1)                                  │
│                                                                   │
│ NewData 컬럼: [Cycle, Dchg, RndV, Eff, Chg, DchgEng,            │
│               Eff2, Temp, AvgV, OriCyc, dcir, ...]               │
└───────────────────────────┬─────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 3: 그래프 표시                                               │
│                                                                   │
│ graph_output_cycle() (L2659):                                    │
│   X축 = df.NewData.index ← ⚠️ 0-based 인덱스 (Cycle 컬럼 아님)  │
│   Y축 = df.NewData.Dchg, .Eff, .Temp, ...                        │
│                                                                   │
│ 스케일: xscale(tcyclerng), ylimitlow, ylimithigh                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. PNE vs TOYO 차이점 비교

| 항목 | PNE | TOYO |
|------|-----|------|
| **TC 소스** | SaveEndData 컬럼 27 | capacity.log 행 |
| **TC 파일 경로** | `Restore/SaveData*.csv` | `%06d` 폴더 |
| **cycle_map 생성** | `pne_build_cycle_map()` | `toyo_build_cycle_map()` |
| **시험 유형 판별** | .sch 힌트 + 데이터 휴리스틱 | Condition 시퀀스만 |
| **스윕 처리** | `_pne_build_sweep_cycle_map()` | TOYO는 스윕 개념이 다름 (충전→방전 쌍으로만) |
| **고아 첫 행 처리** | 없음 (PNE는 SaveEndData 기반) | 첫 행이 방전이면 드롭 (L3218, L3453) |
| **DCIR 소스** | SaveEndData 전류/전압에서 계산 | 별도 dcir.csv 파일 |
| **Cycle 컬럼 생성** | 동일 로직 (L7865-7921) | 동일 로직 + Toyo 자체 Cycle 컬럼 생성 (L3300-3417) |
| **프로필 파일 접근** | `Restore/SaveData*.csv` | `%06d` 파일 (6자리 TC) |

---

## 8. 현재 불일치 및 문제점

### 🔴 문제 1: 그래프 X축이 0-based 인덱스를 사용

**현상**: `graph_output_cycle()`에서 `df.NewData.index`를 X축으로 사용 (L2663).
`reset_index(drop=True)` 후의 인덱스이므로 **0, 1, 2, ...**이 표시됨.

**영향**: 
- 사이클 1이 0으로 표시됨
- `NewData["Cycle"]` 컬럼은 1-based이지만 그래프에 반영 안 됨
- 경로 테이블의 "사이클" 입력값과 그래프 표시값이 1 차이남

**수정 제안**: `df.NewData.index` → `df.NewData["Cycle"]` 또는 인덱스를 Cycle 컬럼 값으로 설정

### 🔴 문제 2: 일반 시험에서 "논리사이클" = "순번"이지 "TC 매핑"이 아님

**현상**: 일반 시험(비스윕)에서 cycle_map이 있어도 NewData에는 `Cycle = range(1, len+1)`로 순번만 부여 (L7913).

**영향**:
- cycle_map이 {1: TC1, 2: TC3, 3: TC5}인데 (비유의 TC 스킵) → NewData Cycle은 1,2,3
- 유효하지만, cycle_map의 논리사이클 번호와 NewData Cycle이 **다른 숫자**가 될 수 있음
- 이후 OriCyc으로 역매핑할 때 인덱스 불일치 위험

### 🟡 문제 3: 세트 탭과 사이클 탭의 사이클 개념이 완전히 다름

**현상**: 
- 사이클 탭: `TC → 논리사이클 → NewData.index` (충방전기 기반)
- 세트 탭: `Battery_Cycle` (스마트폰 로그) + `realcyc`/`resetcycle` 보정

**영향**: 
- `realcyc`/`resetcycle` 라디오 버튼이 사이클 탭에 있지만 **사이클 탭의 TC/논리사이클과는 무관**
- UI 배치가 "세트 결과" 탭이 아닌 "Cycle 세팅" 그룹에 있어 혼란 유발

### 🟡 문제 4: `tcyclerng`(사이클 바)가 사이클 "범위"가 아닌 "간격"

**현상**: 이름이 "사이클 범위"처럼 보이지만 실제로는 X축 tick 간격 (0=자동)

**영향**: 사이클 범위를 지정하려면 경로 테이블의 "사이클" 컬럼을 써야 함 — 두 곳의 역할 혼동

### 🟢 정상: cycle_map dict 형식은 PNE/TOYO 모두 통일됨

```python
{ln: {'all': (start, end), 'chg': [...], 'dchg': [...], 'chg_rest': [...], 'dchg_rest': [...]}}
```

이 부분은 이미 잘 정리되어 있음. 변환 함수(`_logical_to_totl_str`, `_totl_to_logical_str`)도 이 형식을 정확히 처리.

---

## 9. 통일 제안

### 안 1: NewData 인덱스를 논리사이클로 통일 (최소 변경)

```python
# 현재 (L7913):
df.NewData.insert(0, 'Cycle', range(1, len(df.NewData) + 1))

# 변경:
# cycle_map의 논리사이클 번호를 직접 사용
_ln_values = list(cycle_map.keys())[:len(df.NewData)]
df.NewData.insert(0, 'Cycle', _ln_values)
df.NewData.index = df.NewData['Cycle']  # 인덱스도 논리사이클
```

**장점**: graph_output_cycle의 `df.NewData.index`가 바로 논리사이클
**단점**: cycle_map 키와 NewData 행 수가 다를 수 있음 (비유의 TC 스킵)

### 안 2: graph_output_cycle에서 Cycle 컬럼 사용 (호환성 우선)

```python
# graph_output_cycle 함수 수정:
# 기존:
graph_cycle(df.NewData.index, df.NewData.Dchg, ax1, ...)
# 변경:
_x = df.NewData['Cycle'] if 'Cycle' in df.NewData.columns else df.NewData.index
graph_cycle(_x, df.NewData.Dchg, ax1, ...)
```

**장점**: 기존 데이터 구조 변경 없이 그래프만 수정
**단점**: Cycle 컬럼이 없는 레거시 데이터에 대한 폴백 필요

### 안 3: 세트 탭 라디오 버튼 분리 (UI 정리)

```
[사이클 탭 — 충방전기 데이터용]
  ├── 논리사이클 ✓ (기본) — cycle_map 기반 그룹핑된 사이클
  └── 물리사이클 — TotlCycle(OriCyc) 그대로 표시

[세트 탭 — 스마트폰 로그용]
  ├── 보정사이클 ✓ (기본) — 충전전환점 재카운트
  ├── 실제사이클 — Battery_Cycle 그대로
  ├── 전체 / 최근N / 지정범위
```

**장점**: 사이클 개념 혼란 제거
**단점**: UI 레이아웃 변경 필요

---

## 10. 권장 우선순위

| 순위 | 작업 | 영향도 | 난이도 |
|------|------|--------|--------|
| 1 | **안 2: graph X축을 Cycle 컬럼으로** | 높음 (0-base → 1-base) | 낮음 |
| 2 | **안 1: 일반 시험에서도 cycle_map 논리번호 사용** | 중간 (정합성) | 중간 |
| 3 | **안 3: 세트 탭 라디오 버튼 분리** | 낮음 (UI 정리) | 중간 |

---

## 부록: 관련 데이터 디렉토리

### `data/exp_data/` — 실험 데이터

총 100+개 폴더/파일. 주요 유형:
- PNE 수명시험: `251028_260428_05_나무늬_2335mAh_Q8 선상 ATL SEU4 RT @1-1202`
- PNE ECT 파라미터: `260316_270318_00_이성일_5882mAh_M47 ATL ECT parameter1`
- TOYO 데이터: `A1_MP1_4500mAh_T23_1`, `Q7M Inner ATL...`
- GITT 반셀: `240821 선행랩 류성택 Gen4pGr mini-ATL-...GITT-15도`

### `data/pattern/` — 충방전 패턴

| 폴더 | 내용 |
|------|------|
| `pne_4905mAh/` | PNE .sch 스케줄 파일 |
| `toyo/`, `toyo2/` | TOYO .1 패턴 + .option2 설정 |
| `toyo_1995mAh/` | TOYO 소용량 패턴 |
| `Cycler_Schedule_2000.mdb` | PNE 스케줄 DB |
