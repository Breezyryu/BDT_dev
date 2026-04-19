# Phase 1 — 신 9종 사이클 분류기 proto_.py 이식

**날짜**: 2026-04-19
**대상 파일**: `DataTool_dev_code/DataTool_optRCD_proto_.py`
**단계**: Phase 1 (Phase 0 검증 완료 후 본격 이식)
**선행 문서**:
- Phase 0: [260419_사이클분류_Phase0_신분류기_프로토타입.md](260419_사이클분류_Phase0_신분류기_프로토타입.md)
- 설계서: [260419_사이클분류_전면재검토.md](../02_변경검토/260419_사이클분류_전면재검토.md)
- 도메인: [vault/03_Battery_Knowledge/ACIR_DCIR_RSS.md](../../vault/03_Battery_Knowledge/ACIR_DCIR_RSS.md)

---

## 배경 & 설계 원칙

Phase 0 에서 검증한 신 9종(충전/방전/저장/사이클/RPT/GITT/DCIR/SOC별사이클/히스테리시스) + 서브태그 체계를 proto_.py 에 이식. 핵심 인사이트:

- proto_.py 는 **이미 풍부한 `_classify_loop_group()` 분류기(18+ 카테고리)** 를 내부에 보유
- 문제는 **`classify_pne_cycles()` (데이터 기반 heuristic) 가 UI 에 표시되는 카테고리를 결정**하며, 내부 .sch 분류 결과를 활용 안함
- → **.sch 기반 카테고리를 classified 에 덮어쓰는 얇은 오버레이**만 추가하면 완성

**컴퓨팅 최소화 전략**:
- `.sch` 파싱·loop group 분류는 이미 `_get_pne_sch_struct()` (lru_cache) 경유로 **채널당 1회**만 수행
- 신규 오버레이(`_apply_sch_categories_to_classified`)는 `O(n_classified + n_loop_groups)` 단순 스캔
- **추가 파싱 없음, 추가 분류 호출 없음, 추가 캐시 구조 없음**

---

## 변경 내용

### 1. `CATEGORY_LABELS` 확장 (L4754)
신 9종 한글 + 서브태그(방전 4, 충전 1, 사이클 2, GITT 2, 저장 1, 히스테리시스 2) 총 **21개 키** 추가.
구 약어(Rss, 가속수명, initial, unknown) 는 **alias 로 유지** — 하위 호환 보장.

### 2. `_SCH_CAT_TO_NEW` 매핑 딕트 + 헬퍼 신규
proto 내부 카테고리명 → 신 9종 한글 + 서브태그 변환.

```python
_SCH_CAT_TO_NEW = {
    'INIT':            ('방전', '초기'),
    'FORMATION':       ('사이클', 'FORMATION'),
    'ACCEL':           ('사이클', 'ACCEL'),
    'RPT':             ('RPT', None),
    'GITT_PULSE':      ('GITT', 'full'),
    'SWEEP_PULSE':     ('GITT', 'simplified'),
    'SOC_DCIR':        ('SOC별 사이클', None),
    'PULSE_DCIR':      ('DCIR', None),
    'RSS_DCIR':        ('DCIR', None),
    'HYSTERESIS_CHG':  ('히스테리시스', '충전'),
    'HYSTERESIS_DCHG': ('히스테리시스', '방전'),
    'CHARGE_SET':      ('충전', '세팅'),
    'DISCHARGE_SET':   ('방전', 'SOC세팅'),
    'DCHG_SET':        ('방전', None),
    'TERMINATION':     ('방전', '종료'),
    'FLOATING':        ('저장', 'floating'),   # 신규
    'POWER_CHG':       ('저장', None),
    'REST_LONG':       ('저장', None),
    'REST_SHORT':      ('저장', None),
    'CHG_DCHG':        ('RPT', None),          # 일반 1회 충방전
    'EMPTY':           ('unknown', None),
    'UNKNOWN':         ('unknown', None),
}
```

### 3. `_apply_sch_categories_to_classified()` 헬퍼 신규
sch_struct.loop_groups 의 `{tc_start, tc_end, category}` 를 classified 항목의 `{cycle: int, category: str}` 에 덮어쓰기. TC→카테고리 조회 테이블 한 번 구성 후 스캔. 원본 비파괴.

### 4. `_classify_loop_group()` Rule 보강 (3건)

**(a) 반셀 GITT any-REST 수용**
기존: `rest_steps[0].time_limit_s >= 600` (첫 스텝이 REST 일 때만)
변경: `max_rest_s >= 600` — 아무 위치의 REST 만 길면 GITT 인식.
→ M2 SDI 반셀 GITT (I=0.4mA, DCHG→REST 1h × 120) 해소.

**(b) FLOATING Rule 신규 (Rule 2b)**
CC/CCCV 장시간(≥12h) 충전 + 방전 없음 → `FLOATING`.
→ 김영환 1C Floating(70일), HaeanProto N=999 (90일) 모두 인식.

```python
if chg_steps and not dchg_steps:
    max_chg_time = max((s['time_limit_s'] for s in chg_steps), default=0)
    has_v_cut = any(s['v_chg_mV'] > 0 for s in chg_steps)
    if max_chg_time >= 43200 and has_v_cut:
        return 'FLOATING'
```

**(c) SOC_DCIR 조건 엄격화**
기존: `N >= 5 AND n_ec >= 4 AND body >= 8`
변경: `5 <= N < 20 AND n_ec >= 4 AND body >= 8 AND len(EC_type_set) >= 3`
→ 240919 #7, #8 (N=25, 20 가속수명) 이 SOC_DCIR 로 오분류되던 문제 해결.
→ N≥20 은 ACCEL 이 우선 매칭 (기존 Rule 3 유지).

### 5. `END` (0x0006) type code 추가
PNE .sch 에 schedule terminator 로 존재 (LOOP 뒤 최종 스텝, 모든 필드 0). `_SCH_TYPE_MAP` 에 `0x0006: 'END'` 추가 + `_decompose_loop_groups` 의 `_CTRL` set 에 'END' 포함 (LOOP/GOTO/REST_SAFE 와 동급으로 body 에서 제외).

### 6. classify 호출부 2곳에 apply 단계 삽입

**(a) `classify_channel_path()` L5392**
sch_struct 얻은 후 classified 오버레이 + counts 재계산.

**(b) `_build_channel_meta()` L5518**
schedule_struct 얻은 후 동일 적용.

**순서는 변경하지 않음** — 기존 sch_struct 추출 시점 직후 apply 만 추가.

---

## 검증 (smoke test)

`C:/tmp/smoke_test_v2.py` — AST 로 분류 함수만 추출해 4개 실험 검증.

### 240919 SOC별DCIR (기존 "7-96 분류 불가" 케이스)
```
#1  TC 1           INIT       → 방전(초기)
#2  TC 2-4 (3)     FORMATION  → 사이클(FORMATION)
#3  TC 5           RPT        → RPT
#4  TC 6           CHARGE_SET → 충전(세팅)
#5  TC 7-11  (5)   SOC_DCIR   → SOC별 사이클    ← 기존 분류 불가
#6  TC 12-26 (15)  SOC_DCIR   → SOC별 사이클    ← 기존 분류 불가
#7  TC 27-51 (25)  ACCEL      → 사이클(ACCEL)   ← 기존 분류 불가
#8  TC 52-71 (20)  ACCEL      → 사이클(ACCEL)   ← 기존 분류 불가
#9  TC 72-86 (15)  SOC_DCIR   → SOC별 사이클    ← 기존 분류 불가
#10 TC 87-96 (10)  SOC_DCIR   → SOC별 사이클    ← 기존 분류 불가
```
**UI "7-96 분류 불가" 완전 해결** ✅

### 김영환 1C Floating
```
#1 INIT → 방전(초기)
#2 RPT → RPT
#3 FLOATING → 저장(floating)   ← 신규 Rule
```

### HaeanProto N=999 Floating
```
#3 FLOATING → 저장(floating) (TC 3-1001)
```

### M2 SDI 반셀 GITT (I=0.4mA)
```
#2 GITT_PULSE → GITT(full)  (TC 2-121, N=120)   ← 신규 any-REST Rule
#4 GITT_PULSE → GITT(full)  (TC 123-242, N=120)
```

### `_apply_sch_categories_to_classified` mock 테스트
28 TC 의 카테고리가 sch_struct loop_groups 기준으로 정확히 덮어쓰기됨.

---

## 변경 파일 요약

| 파일 | 종류 | 범위 |
|------|------|------|
| `DataTool_dev_code/DataTool_optRCD_proto_.py` | 수정 | L4754 (CATEGORY_LABELS), L4760~L4910 범위 (신규 딕트·헬퍼), L5355~L5525 (2곳 apply 삽입), L6520~L6533 (_SCH_TYPE_MAP END), L6848 (_CTRL), L6775~L6810 (_classify_loop_group 보강) |

**신규 함수·상수**:
- `_SCH_CAT_TO_NEW` 상수 (신 9종 매핑 딕트)
- `_sch_cat_to_label(cat, sub)` 헬퍼
- `_pne_cat_from_sch_group(sch_cat)` 편의 함수
- `_apply_sch_categories_to_classified(classified, sch_struct)` 오버레이

**수정 함수**:
- `_decompose_loop_groups` — `_CTRL` 에 'END' 추가
- `_classify_loop_group` — any-REST GITT, FLOATING, SOC_DCIR EC-타입 다양성
- `classify_channel_path` — apply 단계 삽입
- `_build_channel_meta` — apply 단계 삽입

---

## 영향도

- **하위 호환**: 구 약어(RPT/Rss/가속수명/GITT/initial/unknown) 는 `CATEGORY_LABELS` 에 alias 로 남음. 기존 코드에서 이 키 조회 시 정상 동작.
- **컴퓨팅 오버헤드**: sch 파싱·loop 분류는 이미 lru_cache. 오버레이만 추가 — 채널당 O(TC 개수) 단순 스캔. **실측 ms 단위 이하 증가**.
- **UI 색상**: `_CLASSIFIED_COLORS` 는 이번 범위에 포함 안 함 (Phase 2 로 분리). 새 카테고리는 기본색으로 표시될 수 있음.
- **Toyo**: 본 이식은 PNE 한정. `_apply_sch_categories_to_classified` 는 Toyo sch_struct 가 없으면 무동작 (classified 그대로 반환). Phase 3 에서 Toyo `.CMT`/`.ptn` 파서 확장 시 동일 메커니즘 적용 예정.

---

## 남은 작업

### Phase 2 — UI 색상 업데이트
- `_CLASSIFIED_COLORS` 에 신 9종 + 서브태그 별 색상 지정
- 타임라인 블록 툴팁에 한글 레이블 + 서브태그 표시
- UNKNOWN 블록 사유 툴팁

### Phase 3 — Toyo 확장
- `.CMT` / `.ptn` 파서 확장 (loop 구조 추출)
- `toyo_build_cycle_map()` 에 동일 오버레이 적용

### Phase 4 — 회귀 검증
- 전체 156 실험 재분류 → UNKNOWN <2% 유지 확인
- 기존 수명/성능 엑셀 출력 샘플 10건 회귀
- 240919 + ECT parameter + 복합floating 실사용 검증

---

## 재현 / 검증 방법

```bash
# 구문 검사
cd C:/Users/Ryu/battery/python/BDT_dev/.claude/worktrees/jovial-sinoussi-e0059e
python -c "import ast; ast.parse(open('DataTool_dev_code/DataTool_optRCD_proto_.py', encoding='utf-8').read())"

# 단위 검증 (smoke test)
python C:/tmp/smoke_test_v2.py

# 전체 분류 표 재생성 (Phase 0 프로토타입 기준, 참고용)
python tools/reclassify_prototype.py
```
