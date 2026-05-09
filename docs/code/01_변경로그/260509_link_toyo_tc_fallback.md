# 연결처리 모드 Toyo "데이터 없음" — TC 단위 정정 (raw OriCycle → 충방전 그룹 카운트)

날짜: 2026-05-09
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수:
- `classify_paths_summary` (L7470 근처) — `_max_tc` 산출 PNE/Toyo 분기
- `_resolve_path_meta` (L25903 근처) — col4 placeholder PNE/Toyo 분기
- `_get_row_max_cycle_info` (L27087 근처) — `max_raw` PNE/Toyo 분기
- `_handle_link_cycle_table` row_info raw (L27393 근처) — 동일 분기

요청: 류성택 (260509 BDT 사용 중 발견)

## 사용자 보고 — 그대로

> 연결처리 시, 사이클 입력 후 프로파일 분석이 매끄럽지 않다.
> ATL JINJU SUS 상온장수명 1-100 ~ 901-1000_32 (8개 폴더 연결), 채널 022/023/024/032,
> 공칭 245 mAh, col4 입력 `103`.
>
> "사이클바는 1-102까지 있는데 (col4 placeholder=1-399 와) 다르다. 1-102 를 원한다.
> Toyo TC 는 raw 가 아닌 한번 묶음 처리한 걸로 카운팅. PNE 와 동일 컨셉의 TC."

```
[20:20:19] [Link] offsets=[0, 399, 798, 1594, 2390, 3186, 3585, 3984]
                  total_max=4383  CycleNo=[103]
[20:20:19] [Link] pi=0 offset=0 next=399 local=103-103
[20:20:19] [Profile] Toyo 원시 데이터 없음: ...\1-100\22 (range=103~103)
[20:20:19] [Profile] Toyo 원시 데이터 없음: ...\1-100\23 (range=103~103)
[20:20:19] [Profile] Toyo 원시 데이터 없음: ...\1-100\24 (range=103~103)
[20:20:19] [Profile] Toyo 원시 데이터 없음: ...\1-100\32 (range=103~103)
```

## 근본 원인 — Toyo "TC" 의미가 raw OriCycle 로 잘못 산출

### 사이클러별 TC 정의 (사용자 정정 명시)

| 사이클러 | OriCycle | TC | 관계 |
|----------|----------|------|------|
| PNE | Cycle-loop = TotlCycle | TotlCycle | OriCycle = TC |
| Toyo | Step별 파일 (CC/CV/dchg/rest 각자 1 파일) | 충방전 그룹핑 결과 | OriCycle ≠ TC |

PNE: 1 schedule cycle = 1 TotlCycle 증가 = 1 TC. Pulse 시험에서도 각 pulse 가 별도
TotlCycle 이고 사용자 col4 입력 = TotlCycle 이 자연스럽다 (260505 PULSE_DCIR fix
정합).

Toyo: 1 schedule cycle = N OriCycle (다단 step). `toyo_build_cycle_map` 가 충방전
+휴지 그룹으로 묶어 cycle_map 생성. cycle_map.keys() = 묶음 카운트 = TC.

### 기존 산출 (proto_:7470-7475)

```python
if cycle_map:
    all_tc_ends = [v['all'][1] for v in cycle_map.values() ...]
    _max_tc = max(all_tc_ends) if all_tc_ends else max(cycle_map.keys())
```

PNE/Toyo 모두 동일하게 `max(all_tc_ends)` 사용.

- PNE: `cycle_map[ln]['all']=(TotlCycle, TotlCycle)` 또는 `(s,e)` 범위, e=TotlCycle.
  → `max(all_tc_ends) = max TotlCycle = TC` ✅
- Toyo: `cycle_map[ln]['all']=(OriCycle_start, OriCycle_end)`, e=OriCycle.
  → `max(all_tc_ends) = max OriCycle ≠ TC` ❌

본 케이스: ATL JINJU 1-100 폴더, OriCycle 1..399 (4 step/cycle), TC 1..102.
- 기존: max_tc = 399 (raw OriCycle)
- 정정: max_tc = 102 (충방전 그룹)

연결처리 offset 도 동일 단위로 누적되므로:
- 기존: `[0, 399, 798, 1594, ...]`, total_max=4383 (raw 누적, 사이클바 1-102 와 불일치)
- 정정: `[0, 102, 204, ...]`, total_max=사이클바 max 와 정합

## 변경 — `_max_tc` / `auto_cyc_str` / `max_raw` PNE/Toyo 분기

### 1. `classify_paths_summary` — `meta.max_tc` 단일 진실원천

```python
if cycle_map:
    if is_pne:
        all_tc_ends = [v['all'][1] for v in cycle_map.values()
                       if isinstance(v, dict) and 'all' in v]
        _max_tc = max(all_tc_ends) if all_tc_ends else max(cycle_map.keys())
    else:
        _max_tc = max(cycle_map.keys())
```

`_get_path_max_cycle` 가 `meta.max_tc` 를 반환하므로 **연결처리 offset 누적 / TC 검증
다이얼로그 / col4 placeholder** 가 모두 정정된 단위를 자동 사용.

### 2. `_resolve_path_meta` — col4 placeholder 표시값

```python
_is_pne_path = (meta_hit.is_pne if meta_hit is not None
                else is_pne_folder(path))
if _is_pne_path:
    all_tc = [v['all'][1] for v in cm.values() ...]
    if all_tc:
        auto_cyc_str = str(max(all_tc))
else:
    auto_cyc_str = str(max(cm.keys()))
```

### 3. `_get_row_max_cycle_info` / row_info raw — 사이클 힌트 복원 + 행 그룹핑

`max_raw` 는 col4 회색 힌트 ("1-{max_raw}") 표시 + 행 그룹 cumulative 산출에 사용.
Toyo 에서는 raw OriCycle 의미가 없으므로 `max_raw = max(cm.keys())` (= max_cycle 과 동등).

## 이전 패치(2be3cde, soft-reset 됨) revert 사유

같은 보고를 받고 처음에 `_unified_toyo_load_raw` 에 PNE 의 `_tc_to_logical` 폴백을
mirror 했음 (proto_:1794-1818 패턴). 사용자 정정 후 그 방향이 잘못이었음을 확인:

- PNE 의 폴백은 "TotlCycle = TC" 전제에서 sweep 그룹 내부 TotlCycle 직접 선택용.
- Toyo 에 mirror 하면 **raw OriCycle 직접 입력을 허용** → 사용자가 원치 않는 단위.
  사용자 정책: "Toyo TC 는 raw 가 아닌 한번 묶음 처리한 걸로 카운팅".

따라서 `_unified_toyo_load_raw` 는 **원래 silent skip 동작** 으로 복원 (cycle_map
keys 매칭만, 미매칭 시 skip). 정정 후 `meta.max_tc = max(cm.keys())` 이므로 사용자
입력은 항상 cycle_map keys 범위 내 → silent skip 미발생.

## 검증 시뮬레이션

ATL JINJU 8 폴더 연결, 채널 022/023/024/032, capacity 245, 입력 `103`:

| 단계 | 기존 | 정정 |
|------|------|------|
| 폴더1 max_tc | 399 (OriCycle) | 102 (TC) |
| 폴더2 max_tc | 399 | ~100 |
| total_max | 4383 | ~사이클바 cumulative max |
| 입력 103 라우팅 | pi=0 (폴더1), local 103 | pi=1 (폴더2), local 3 |
| cycle_map 매칭 | 폴더1 cm[103] 부재 → "데이터 없음" | 폴더2 cm[3] 적중 → 정상 plot |

General mode (기존 동작 유지 확인):
- PNE general life: cycle_map keys = TotlCycle = 1..N, 'all'=(n,n). `max(all_tc_ends)=max(keys)=N`.
- Toyo general life: cycle_map keys = 1..N (그룹 카운트). `max(keys)=N`. 기존 동작
  과 동일 (단, Toyo 가 multi-step 일 때만 차이 발생).

## 호환성

- PNE general / sweep / PULSE_DCIR: 기존 `max(all_tc_ends)` 분기 유지 → 영향 없음.
  260505 fix(_unified_pne_load_raw _tc_to_logical 폴백) 도 그대로 동작.
- Toyo single-step (드물게) general life: cycle_map.keys() == all_tc_ends max →
  값 동일.
- Toyo multi-step lifetime / RPT 포함: max_tc 가 OriCycle → TC 그룹 카운트 로 정정.
- 사이클바 (1-102) ↔ col4 placeholder (1-102) 정합 회복.
- 검증 다이얼로그 "TC 범위 초과" 메시지의 max 값도 동일 정정.

## 검증 절차 (사용자)

1. 앱 재시작 (또는 `_reset_all_caches`)
2. ATL JINJU 8 폴더 연결, 채널 022/023/024/032, capacity 245
3. 행 그룹의 col4 placeholder 가 **"1-102"** 등 사이클바와 정합되는 값으로 표시되는지 확인
4. col4 에 `103` 입력 → pi=1 (폴더2 "101-200") 로 라우팅
5. 4채널 모두 그래프 표시
6. 사이클바 클릭으로 cycle 1, 50, 100, 200, ... 등 다양한 입력 시 의도한 폴더로 라우팅되는지 cross-check

## 추가 정리 필요 (별도 PR)

- `_get_path_max_cycle` docstring: "최대 논리사이클 수" → 실제로 `meta.max_tc` 반환.
  본 PR 후 PNE/Toyo 모두 의미상 "최대 TC" 이므로 docstring 정정.
- 일부 코드 주석 (예: proto_:25911 "TC ≈ 논리사이클 in General"): 사이클러별
  의미 차이 명시 필요.

## 적용 파일

- `C:\Users\Ryu\battery\python\BDT_dev\.claude\worktrees\quizzical-hertz-e248f3\DataTool_dev_code\DataTool_optRCD_proto_.py` (worktree, 본 PR)
- main 머지 후: `C:\Users\Ryu\battery\python\BDT_dev\DataTool_dev_code\DataTool_optRCD_proto_.py`
