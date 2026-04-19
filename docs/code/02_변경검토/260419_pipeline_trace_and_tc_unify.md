# 260419 파이프라인 스냅샷 유틸 + TC 1원화 마감

## 배경

사용자가 파싱 파이프라인(사이클 분석/프로파일 분석)의 단계별 DataFrame 변화를 시각적으로 살펴볼 수 있는 수단을 원했고, 동시에 UI 표시를 원본 TotlCycle 기준으로 통일하고자 했음. 기존 코드는 일반 시험에서는 이미 TC 1원화가 되어 있었으나 Sweep 시험(GITT/DCIR)의 집계 결과에서만 `Cycle` 컬럼이 논리사이클 번호로 남아 있었음.

## 변경 내용

### A. 디버그 스냅샷 유틸 (`_DEBUG_PROFILE_TRACE`)

`DataTool_dev_code/DataTool_optRCD_proto_.py` 상단에 추가:
```python
_DEBUG_PROFILE_TRACE: bool = False
_DEBUG_TRACE_DIR: str = r"C:\tmp\bdt_trace"
```
함수 `_debug_snapshot(obj, stage, tag)` — True 시 각 Stage의 DataFrame(shape/columns/dtypes/head/전체)을 pickle로 저장. False 시 비용 ~0.

삽입 포인트 (unified 프로파일 경로):
- `S2_load_raw` — `_unified_pne_load_raw` / `_unified_toyo_load_raw` 리턴 직전
- `S3_filter_condition` — `_unified_filter_condition` 리턴 직전
- `S4_normalize` — `_unified_normalize_pne` / `_unified_normalize_toyo` 리턴 직전
- `S5_merge_steps` — `_unified_merge_steps` cycle scope 리턴 직전
- `S6_calc_axis` — `_unified_calculate_axis` 리턴 직전
- `S7_output_df` / `S7_output_cycfile_soc` — `unified_profile_core` 최종 반환 직전

사용법:
```python
import DataTool_dev_code.DataTool_optRCD_proto_ as bdt
bdt._DEBUG_PROFILE_TRACE = True
bdt._DEBUG_TRACE_DIR = r"C:\tmp\bdt_trace"
# GUI에서 프로파일 분석 1회 실행 (사이클 1~2개)
# 이후 tools/profile_trace_viewer.ipynb 로 열람
```

### B. Jupyter 뷰어 노트북

`tools/profile_trace_viewer.ipynb` 생성:
- 가장 최근 세션의 pickle들을 번호 순 로드
- 요약 표(stage, tag, shape, n_cols)
- Stage별 컬럼/dtype 나열
- Stage 6 Cap/SOC 궤적 subplot (ffill 검증)
- Stage 7 cycfile_soc OCV/CCV vs SOC 산점도
- Stage별 행 수 변화 막대그래프

### C. Obsidian vault 노트

`docs/vault/04_Development/260419_BDT_Parsing_Pipeline.md`:
- 두 파이프라인 공통 골격 + ChannelMeta
- PNE/Toyo 입력 스키마 표
- 사이클 분석 5 Phase (원시 → 스텝 머지 → TC매핑 → 집계 → 그래프)
- 프로파일 분석 6 Stage (판별 → 로딩 → 필터 → 정규화 → 병합 → 축계산)
- 두 파이프라인 비교표
- 공유 캐시 계층표
- 디버그 유틸 사용법

### D. Sweep 집계 결과 TC 1원화

이전 코드:
```python
_grouped.rename(columns={'_ln': 'Cycle'}, inplace=True)
```
- Sweep 시험(GITT/DCIR 등)의 집계 결과에서 `Cycle` 컬럼이 **논리사이클 번호**였음
- 일반 시험은 이미 `Cycle = OriCyc (TC)`로 통일 (L4053, L9171) — Sweep만 어긋남

변경 후 ([L9155-9165](DataTool_dev_code/DataTool_optRCD_proto_.py:9155)):
```python
_grouped.rename(columns={'_ln': '_LogicalCyc'}, inplace=True)
if 'OriCyc' in _grouped.columns:
    _grouped.insert(0, 'Cycle', _grouped['OriCyc'].astype(int).values)
else:
    _grouped.insert(0, 'Cycle', _grouped['_LogicalCyc'].astype(int).values)
```
- `Cycle` = 대표 TC (`OriCyc`의 `last` 집계값, 스윕 내 마지막 TC 번호)
- `_LogicalCyc` = 논리사이클 번호 (디버깅/엑셀 참조용으로 보존)

결과:
- `df.NewData['Cycle']`가 모든 경로에서 **원본 TotlCycle** 값 보유 (Toyo · PNE 일반 · PNE Sweep)
- 엑셀 "Cycle" 컬럼 출력값이 TC로 통일
- 사이클 바 블록은 이미 `_build_timeline_blocks_tc_by_loop` 기반이라 TC 표시 유지
- 경로 테이블 col4/col5 세맨틱도 TC 그대로 (`_resolve_cyc_to_tc`는 이미 제거됨)

## UI 표시 TC 1원화 현황

| 위치 | 상태 | 비고 |
|---|---|---|
| 사이클 바 블록 색상/크기 | 논리사이클 카테고리 기반 | 사용자 의도 (시각적 그룹핑) |
| 사이클 바 블록 번호/tick | TC | `_build_timeline_blocks_tc_by_loop` |
| 사이클 바 선택 텍스트 | TC | get_selection_text가 블록 start/end 반환 |
| 경로 테이블 col4/col5 | TC | `_resolve_cyc_to_tc` 제거 완료 |
| 선택 상태 레이블 | TC | 텍스트 그대로 카운트 |
| `df.NewData['Cycle']` (Toyo) | TC | L4053 |
| `df.NewData['Cycle']` (PNE 일반) | TC | L9171 |
| `df.NewData['Cycle']` (PNE Sweep) | **TC** (이번 변경) | L9155-9165 |
| graph_output_cycle X축 | 행 index (0-based) | "첫 사이클=초충상태" 의도 — 유지 |

## 보류 항목

- **graph_output_cycle X축을 Cycle 컬럼(TC) 값으로 변경할지**: 현재는 index(0,1,2,...) 사용. Sweep 집계 후 TC가 연속하지 않을 수 있어 축 모양이 달라짐. 사용자 확인 후 별도 단계.

## 파일 변경 요약

- `DataTool_dev_code/DataTool_optRCD_proto_.py`
  - `_DEBUG_PROFILE_TRACE` 플래그 + `_debug_snapshot` 함수 추가 (~60줄)
  - 6개 Stage 함수 리턴 직전 `_debug_snapshot` 호출 삽입
  - PNE Sweep 집계 `Cycle` 컬럼을 TC로 통일
- `tools/profile_trace_viewer.ipynb` 신규
- `docs/vault/04_Development/260419_BDT_Parsing_Pipeline.md` 신규
- `docs/code/02_변경검토/260419_pipeline_trace_and_tc_unify.md` 본 문서
