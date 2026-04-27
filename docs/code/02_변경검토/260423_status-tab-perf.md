# 260423 현황 탭 파싱/전처리 속도 개선 (방법 A)

## 배경
현황 탭(tab_1, "현황") — 충방전기 모니터링 — 은 `tb_cycler` 콤보박스 전환 시마다 네트워크
드라이브(z:, y:, x:, w:, v:, u:)에서 `Chpatrn.cfg`/`ExperimentStatusReport.dat`(Toyo) 또는
`Module_{1,2}_channel_info.json`(PNE) 을 **재파싱**했다. 캐시가 없고 `.apply(split_valueN)`
행단위 처리, 셀별 Qt 호출 반복으로 체감 지연이 크며, `filter_all_channels()` 는 최대 35개
cycler 를 순차 파싱해 수~수십 초 대기가 발생했다.

플랜: `C:\Users\Ryu\.claude\plans\bdt-proto-glowing-karp.md` (승인됨).

## 수정 파일
- `DataTool_dev_code/DataTool_optRCD_proto_.py` (단일 파일)

## 변경 요약

### 1) `WindowClass.__init__` — 캐시 필드/롤백 스위치 추가
```python
self._status_cache: dict = {}
self._status_cache_enabled = True   # False → 캐시 우회 (회귀 비교용)
self._vectorize_split = True        # False → split_value0/1/2 apply 경로 유지
```
위치: `self.df = []` 직후 (구 17417 부근).

### 2) 공통 헬퍼 4개 신규 (`split_value2` 직후)
| 함수 | 역할 |
|------|------|
| `_status_load(path, parser)` | mtime+size 기반 파일 파싱 캐시. parser ∈ {"toyo_cfg","csv","json"}. 키: `normcase(abspath(path))`. OSError/파싱 실패 시 `None` 반환 |
| `_vector_split_testname(s)` | testname Series → (day, part, name). `split_value0/1/2` 와 동일 결과를 `pandas.str.split` + `numpy.where` 로 벡터화 |
| `_apply_split_testname(df)` | 위 벡터 버전/기존 apply 경로를 `_vectorize_split` 플래그로 분기 |
| `_pne_load_channel_info(pne_num)` | `Module_{1,2}_channel_info.json` → `(df_raw, js1)`. 캐시 경유. Module_2 있으면 concat |
| `_pne_postprocess(df_raw, blkname, pne_num)` | PNE 공통 전처리 → 완성 DF 반환. **`self.df` 에 직접 쓰지 않음** (호출자가 할당) |

### 3) `toyo_base_data_make`
- `remove_end_comma(path)` / `pd.read_csv(...)` 직접 호출 → `_status_load(path, "toyo_cfg"|"csv")` 경유
- 캐시 반환물은 `.copy()` 후 수정 (캐시 무결성)
- `.apply(split_valueN)` × 3 → `self._apply_split_testname(toyo_data)` 1회
- `_status_load` 가 None 반환 시 기존과 동일하게 빈 DataFrame 폴백 유지

### 4) `pne_data_make` — 재작성 (약 50줄 → 9줄)
```python
df_raw, js1 = self._pne_load_channel_info(pne_num)
if df_raw is None:
    return None
self._pne_last_sync_time = self._pne_sync_time(js1)
self.df = self._pne_postprocess(df_raw, blkname, pne_num)
return self.df
```

### 5) `pne_table_make` — 재작성 + 렌더 배치 업데이트
- 파싱/전처리는 `_pne_load_channel_info` + `_pne_postprocess` 로 공통화
- `tb_modified_time` 갱신은 유지
- 렌더 루프를 `setUpdatesEnabled(False) + blockSignals(True)` → try/finally → `setUpdatesEnabled(True) + blockSignals(False) + viewport().update()` 로 감쌈

### 6) `toyo_table_make` — 렌더 배치 업데이트만 적용
- 2중 for 루프를 위와 동일한 패턴으로 감쌈

### 7) `filter_all_channels` — 코드 변경 없음
내부에서 `toyo_data_make`/`pne_data_make` 를 호출하므로 (1)~(3) 변경이 자동 적용됨 →
두 번째 실행부터 캐시 hit 으로 급가속.

## 회귀 검증

### (a) 롤백 스위치 (즉시 복원)
Python 콘솔(또는 디버거)에서:
```python
win._status_cache_enabled = False   # 파일 캐시 우회
win._vectorize_split = False        # apply 경로 유지
```

### (b) 결과 동등성 (ad-hoc)
```python
self._status_cache_enabled = False; self._vectorize_split = False
df_a = self.pne_data_make(0, "PNE1").copy()
self._status_cache_enabled = True;  self._vectorize_split = True
self._status_cache.clear()
df_b = self.pne_data_make(0, "PNE1").copy()
assert df_a.equals(df_b)
```

### (c) 수동 체크리스트
- [ ] Toyo1~5 각각 콤보 선택 → testname/day/part/name/cyc/vol/temp 동일
- [ ] PNE1~25 각각 콤보 선택 → 동일 컬럼 + `최종 수정 ...` 라벨
- [ ] `filter_all_channels` (Shift+Enter) 빈 검색/일반 검색 각 1회
- [ ] 네트워크 드라이브 미마운트 상태 (`net use z: /delete`) → 빈 DataFrame 폴백
- [ ] 같은 cycler 2회 선택 → 두 번째는 지연 현저히 감소 (캐시 hit)
- [ ] 파일 변경(Chpatrn.cfg 수정) 후 같은 cycler 선택 → 새 데이터 반영 (mtime/size 변경 감지)

## 예상 개선치 (네트워크 100ms/file 가정)

| 시나리오 | 현재 | 개선 후 (캐시 hit) |
|---------|------|-------------------|
| Toyo 콤보 전환 | ~300ms | ~40~80ms |
| PNE 콤보 전환 | ~300ms | ~40~80ms |
| filter_all_channels 재실행 | ~8s | ~0.5~1s |
| 앱 기동 첫 진입 | ~300ms | ~200ms (I/O 동일, 벡터/렌더만) |

## Edge Cases 처리
- **네트워크 드라이브 끊김**: `_status_load` 가 `os.stat` OSError 시 `None` 반환 → 호출자 빈 DataFrame 폴백
- **파싱 예외**: JSON 디코드/read_csv 실패 시 `None` 반환 (기존 동작보다 관대하게 실패 허용)
- **mtime 해상도**: SMB/CIFS 드라이브 mtime 해상도 문제 회피 위해 `(mtime, size)` 쌍 비교
- **캐시 키 대소문자**: `os.path.normcase(os.path.abspath(path))` 로 정규화
- **cp949 인코딩 통일**: `pne_data_make` 쪽도 `cp949, errors='ignore'` 로 통일 (구 디폴트 인코딩 → 통일)
- **DataFrame 공유 방지**: 캐시 반환 후 `.copy()` 호출로 이후 수정이 캐시에 역류하는 것 차단
- **testname NaN**: `dropna()` 이후 벡터 연산 유지 (기존 순서 보존)

## 안 건드린 부분 (의도적)
- Phase 0-5 사이클 파이프라인, `cycle_map`, `df.NewData`, 기존 `lru_cache` 래퍼들 — 사이클 분석 탭 전용
- `CycleTimelineBar`, `ChannelMeta`, `DataTool_UI.py`
- `remove_end_comma`, `change_drive`, `_pne_sync_time` 내부 — 호출만
- `filter_all_channels` 의 `.log` 기반 로직 (`_classify_paused_reason`, `_elapsed_from_log`)
