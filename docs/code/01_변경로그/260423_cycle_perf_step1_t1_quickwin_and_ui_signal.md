# 사이클 탭 성능 개선 Step 1 — T1 Quick Win 5건 + UI Signal 재설계

날짜: 2026-04-23
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
관련 계획: `C:/Users/Ryu/.claude/plans/validated-forging-rabin.md`

## 배경

대형 시험(TC 2000, 채널 10, 사이클 1000+) 사이클 탭 로딩이 체감 20~60초. 3-Tier 분석(Phase 1 Explore 3개)에서 I/O 중복 / pandas boolean 스캔 중복 / Sweep dict 대량 삽입 / cross-thread UI 접근 위험이 확인됨. **엑셀 저장(to_excel) 최적화는 이번 범위 외**.

Step 1에서는 **저위험 고효과 Quick Win 5건 + UI signal 뼈대**를 묶음. T2-A(`_process_pne_cycleraw` 리팩토링) 와 T2-C(Canvas lazy) 는 회귀 위험이 커 Step 2/3 에서 분리.

## 변경 내용

### T1-A. lru_cache maxsize 확장 (autofill 경로 캐시 스래싱 제거)

`_autofill_table_empty_cells` 가 행별 × 채널별로 `_find_sch_file` / `_get_pne_sch_struct` 을 반복 호출. 채널 수가 캐시 크기를 넘으면 LRU 스래싱으로 반복 파싱.

```python
# Before
@functools.lru_cache(maxsize=128)
def _find_sch_file(channel_path: str) -> str | None: ...

@functools.lru_cache(maxsize=256)
def _get_pne_sch_struct(channel_path: str, mincapacity: float) -> dict | None: ...

# After
@functools.lru_cache(maxsize=2048)
def _find_sch_file(channel_path: str) -> str | None: ...

@functools.lru_cache(maxsize=2048)
def _get_pne_sch_struct(channel_path: str, mincapacity: float) -> dict | None: ...
```

영향:
- 캐시 메모리 소폭 증가 (엔트리당 수 KB × 1920개 추가 ≈ 수 MB 이하).
- `_reset_all_caches()` 가 lru_cache 도 같이 비워주므로 stale 우려 없음.
- 체감: autofill 단계 2~5초 단축 (채널 수가 많은 환경).

### T1-B. Toyo DCIR CSV 병렬 I/O

`toyo_cycle_data` 내부 `for cycle in cycnum:` 순차 `pd.read_csv`. NAS 기준 파일당 5~20ms, n=100이면 1~2초 순차 대기.

```python
# After — 채널 병렬과 이중 과부하 방지 위해 워커 수 4 이하로 제한
def _read_dcir_for_cycle(cycle):
    _p = raw_file_path + "\\%06d" % cycle
    if not os.path.isfile(_p):
        return int(cycle), None
    try:
        _pro = pd.read_csv(_p, sep=",", skiprows=3, engine="c",
                           encoding="cp949", on_bad_lines='skip')
        if "PassTime[Sec]" in _pro.columns:
            _pro = _pro[["PassTime[Sec]", "Voltage[V]", "Current[mA]", "Condition", "Temp1[Deg]"]]
        else:
            _pro = _pro[["Passed Time[Sec]", "Voltage[V]", "Current[mA]", "Condition", "Temp1[deg]"]]
            _pro.columns = ["PassTime[Sec]", "Voltage[V]", "Current[mA]", "Condition", "Temp1[Deg]"]
        _cal = _pro[(_pro["Condition"] == 2)]
        _i_max = round(_cal["Current[mA]"].max())
        if not _i_max:
            return int(cycle), None
        return int(cycle), (_cal["Voltage[V]"].max() - _cal["Voltage[V]"].min()) / _i_max * 1000000
    except Exception as _e:
        _perf_logger.warning(f'toyo_cycle_data DCIR read 실패 cycle={cycle}: {_e}')
        return int(cycle), None

if len(cycnum) > 0:
    _dcir_workers = min(4, calc_optimal_workers(len(cycnum)))
    with ThreadPoolExecutor(max_workers=_dcir_workers) as _ex:
        for _cyc, _val in _ex.map(_read_dcir_for_cycle, list(cycnum)):
            if _val is not None:
                dcir.loc[_cyc, "dcir"] = _val
```

차이:
- 기존 암묵적 허용 — I_max 0일 때 `ZeroDivisionError` 크래시 가능 → 명시적으로 None 반환.
- Exception 발생 시 `_perf_logger.warning` 기록 후 None.
- 체감: 500ms ~ 1s 절감.

### T1-C. mkdcir 분기 DataFrame 중복 제거

`_process_pne_cycleraw` mkdcir 경로에서 동일 인덱스(`TotlCycle_add`) 4회 `pd.DataFrame(...).set_index(...)` 반복.

```python
# Before — 4 DF 생성 + 4 set_index
dcir = pd.DataFrame({"Cyc": ..., "dcir_raw2": ...}).set_index(...)
dcir2 = pd.DataFrame({"Cyc": ..., "dcir_raw":  ...}).set_index(...)
df_rssocv = pd.DataFrame({"Cyc": ..., "rssocv":  ...}).set_index(...)
df_rssccv = pd.DataFrame({"Cyc": ..., "rssccv":  ...}).set_index(...)

# After — 단일 DataFrame, 다운스트림 호환 view 유지
dcirtemp1 = same_add(dcirtemp1, "TotlCycle")
dcirtemp2 = same_add(dcirtemp2, "TotlCycle")
dcirtemp3 = same_add(dcirtemp3, "TotlCycle")
_idx = dcirtemp1["TotlCycle_add"].values
_dc = pd.DataFrame({
    "dcir_raw2": dcirtemp1["imp"].values,
    "dcir_raw":  dcirtemp2["imp"].values,
    "rssocv":    dcirtemp3["Ocv"].values / 1_000_000,
    "rssccv":    dcirtemp1["Ocv"].values / 1_000_000,
}, index=_idx)
dcir = _dc[["dcir_raw2"]]
dcir2 = _dc[["dcir_raw"]]
```

체감: 100~300ms + 메모리 감소. 다운스트림 `dcir["dcir_raw2"]` / `dcir2["dcir_raw"]` 참조 유지.

### T1-D. Toyo Condition 필터 1-pass numpy mask

`toyo_cycle_data` 가 Condition/Finish/Cap 조합을 4번 독립 boolean 스캔 (chgdata, dcir, Dchgdata). 각 스캔이 10만 행 기준 2~5ms.

```python
# Before — 4회 pandas boolean 스캔
chgdata = Cycleraw[(Cycleraw["Condition"] == 1) & (Cycleraw["Finish"] != "                 Vol")
                   & (Cycleraw["Finish"] != "Volt") & (Cycleraw["Cap[mAh]"] > (mincapacity/60))]
dcir = Cycleraw[((Cycleraw["Finish"] == "                 Tim") | ...) & ...]
Dchgdata = Cycleraw[(Cycleraw["Condition"] == 2) & (Cycleraw["Cap[mAh]"] > (mincapacity/60))]

# After — 1회 numpy array 추출 + 3개 mask 동시 생성
_cond_arr = Cycleraw["Condition"].values
_fin_arr = Cycleraw["Finish"].values
_cap_arr = Cycleraw["Cap[mAh]"].values
_thr_cap = mincapacity / 60
_m_chg = ((_cond_arr == 1)
          & ~np.isin(_fin_arr, ("                 Vol", "Volt"))
          & (_cap_arr > _thr_cap))
_m_dchg = (_cond_arr == 2) & (_cap_arr > _thr_cap)
_m_dcir = (np.isin(_fin_arr, ("                 Tim", "Tim", "Time"))
           & (_cond_arr == 2) & (_cap_arr < _thr_cap))
chgdata = Cycleraw[_m_chg]
dcir = Cycleraw[_m_dcir]
Dchgdata = Cycleraw[_m_dchg]
```

Finish 문자열(앞 공백 17자 포함)은 기존 exact match 의미 그대로 `np.isin` 튜플로 옮김. 체감: 100~300ms.

### T1-E. PNE Sweep TC→논리사이클 bisect 매핑

`_process_pne_cycleraw` 의 물리 TC → 논리사이클 역매핑:

```python
# Before — Sweep 시 TC 범위 전체를 dict 에 삽입 (10만 회 가능)
_tc_to_ln: dict[int, int] = {}
for _ln, _tc_val in cycle_map.items():
    if isinstance(_tc_val, dict):
        _s, _e = _tc_val['all']
        for _t in range(_s, _e + 1):
            _tc_to_ln[_t] = _ln
    else:
        _tc_to_ln[int(_tc_val)] = _ln
_logical_col = df.NewData['OriCyc'].astype(int).map(_tc_to_ln)

# After — bisect 기반 O(log N) 조회, dict 대량 삽입 회피
_bounds: list[tuple[int, int, int]] = []
_is_sweep = False
for _ln, _tc_val in cycle_map.items():
    if isinstance(_tc_val, dict):
        _s, _e = _tc_val['all']
        if _s != _e:
            _is_sweep = True
        _bounds.append((int(_s), int(_e), int(_ln)))
    else:
        _tc_int = int(_tc_val)
        _bounds.append((_tc_int, _tc_int, int(_ln)))
_bounds.sort()
_starts = [b[0] for b in _bounds]

def _tc_to_ln_lookup(tc):
    _i = bisect.bisect_right(_starts, tc) - 1
    if 0 <= _i < len(_bounds):
        _s2, _e2, _ln2 = _bounds[_i]
        if _s2 <= tc <= _e2:
            return _ln2
    return None
_logical_col = df.NewData['OriCyc'].astype(int).map(_tc_to_ln_lookup)
```

- General 모드 (1 논리사이클 = 1 TC): 동일 성능 — bisect 오버헤드 미미.
- Sweep 모드 (1 논리사이클 = TC N개): dict 삽입 N회 제거 → O(log N) 조회로 체감 50~200ms 절감.
- 경계 `s <= tc <= e` 명시로 off-by-one 없음.

### T2-B. `_pump_ui` Signal 재설계 (Cross-thread 안전)

기존 `_pump_ui` 가 워커 스레드에서 호출될 경우 `progressBar.setValue` 직접 호출 + `processEvents` 가 Qt 단일스레드 가정을 깨뜨릴 위험 (Perf-2). 현재는 `as_completed` 소비가 메인 스레드에서 돌고 있어 크래시는 없지만, 워커 내부 진행률 emit 확장 시 race 위험.

**신설 — module 레벨 QObject**:

```python
class _PipelineProgress(QtCore.QObject):
    """파이프라인 진행 상황 signal — cross-thread 안전 UI 통지."""
    progressed = QtCore.pyqtSignal(int)
    errored = QtCore.pyqtSignal(str, str)
```

**WindowClass.__init__** 에 인스턴스 생성 + connect:

```python
self.setupUi(self)
self._pipe_progress = _PipelineProgress()
self._pipe_progress.progressed.connect(self.progressBar.setValue)
```

**_pump_ui 구현 재설계** — 호출자 60+ 군데는 손대지 않음:

```python
def _pump_ui(self, progress_value=None, max_ms=10):
    if progress_value is not None:
        _v = int(max(0, min(100, progress_value)))
        if hasattr(self, '_pipe_progress'):
            self._pipe_progress.progressed.emit(_v)
        else:
            self.progressBar.setValue(_v)
    _app = QtWidgets.QApplication.instance()
    if _app is not None and QtCore.QThread.currentThread() is _app.thread():
        _app.processEvents(
            QtCore.QEventLoop.ProcessEventsFlag.AllEvents, max_ms)
```

핵심:
- `pyqtSignal` AutoConnection: 호출자가 워커 스레드면 QueuedConnection, 메인이면 DirectConnection 자동.
- `processEvents` 는 메인 스레드에서만 유효 → 현재 스레드 확인 후 호출.
- 초기화 이전 폴백(`hasattr` 체크) 으로 부트스트랩 순서 보호.

**L20231 통일** — `_load_all_cycle_data_parallel` 의 `as_completed` 루프 내 직접 `setValue` 호출을 `_pump_ui` 로 교체:

```python
# Before
self.progressBar.setValue(int(completed / total_tasks * 50))
# After
self._pump_ui(int(completed / total_tasks * 50))
```

회귀:
- 메인 스레드에서 호출되던 기존 경로는 AutoConnection → DirectConnection 이라 순서·타이밍 동일.
- `processEvents` 가 워커에서 호출 안 되는 점 → 과거에도 워커 루프에서 processEvents 는 무의미했으므로 사실상 동작 불변.

## 성능 측정 (사전 예상)

| 항목 | 기존 | 개선 | 절감 |
|---|---|---|---|
| autofill (TC2000×10ch) | 3~6s | 1~1.5s | 2~5s |
| Toyo DCIR 순차 I/O (n=100) | 1~2s | 300~500ms | 500ms~1s |
| mkdcir DF 생성 | 300~500ms | 100~200ms | 100~300ms |
| Toyo Condition 필터 | 300~500ms | 100~200ms | 100~300ms |
| Sweep TC→논리 매핑 | 100~300ms | 50~100ms | 50~200ms |
| **누적** | — | — | **3~6초** |

체감 개선은 PNE 대형 시험(채널 수 多) 및 Toyo DCIR 수 많은 시험에서 가장 뚜렷.

## 회귀 테스트

실행 후 다음 모드 전부에서 `df.NewData` 컬럼 값이 기존과 동등해야 함.

| 모드 | 검증 포인트 |
|---|---|
| PNE 일반 (TC2000/10ch/1000cyc) | df.NewData 스키마 + 값 |
| PNE Sweep (GITT) | `_LogicalCyc` 매핑, bisect 경계 (s <= tc <= e) |
| PNE mkdcir (가속수명) | dcir/dcir2/rssocv/rssccv/soc70_dcir 4컬럼 일치 |
| Toyo 일반 (500cyc) | chgdata/Dchgdata/dcir 필터 동등 |
| Toyo DCIR only (100cyc) | 병렬 read 후 dcir.loc[cyc, "dcir"] 값 일치 |
| 연결 모드 | `_autofill_link_cumulative_hints` 호환 |
| 재실행 | `_channel_meta_store` 캐시 적중, lru_cache 크기 증가 무영향 |

## 롤백 절차

모든 변경은 독립 — `git revert <sha>` 로 Step 1 전체 원복 가능. 이번에는 feature flag 도입하지 않음 (각 변경이 리팩토링 수준, 호환성 유지).

## 다음 단계

- Step 2: T2-A `_process_pne_cycleraw` DataFrame 복사 감소 (중위험, 엑셀 출력 binary diff 검증 필요).
- Step 3: T2-C FigureCanvas lazy init (UI 이벤트 연쇄 검증 필요).
