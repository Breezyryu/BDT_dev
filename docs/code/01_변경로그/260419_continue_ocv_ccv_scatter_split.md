# Continue 프로파일 OCV/CCV 시각화 개선

## 배경 / 목적

Continue(이어서) 프로파일의 OCV/CCV 시각화 가독성 향상:

- **ax4 (OCV/CCV vs Time)**: 기존 `"o"` 타입은 마커+라인을 함께 그려 DCIR 펄스 구간에서 라인이 산점도 식별을 방해했음. 펄스 특성상 시간 순 연결선이 의미를 갖지 않아 **순수 scatter**로 전환하고, 배경 Voltage 라인과 겹침을 완화하기 위해 마커 크기를 30% 축소.
- **ax5 (OCV/CCV vs SOC)**: 충·방전 방향이 다른 점들이 동일 색으로 섞여 히스테리시스 해석이 어려웠음. **Crate 부호 기반으로 충전/방전 분리**하고, 각 방향별 scatter+line을 추가해 방향별 OCV/CCV 곡선을 식별 가능하도록 개선.

## 변경 내용

### 1) `_cycfile_soc`에 `Crate` 컬럼 추가

ax5의 충/방전 분리를 위해 OCV/CCV 요약 테이블에 `Crate` 보존.

**Before** (`DataTool_optRCD_proto_.py` L2452, L2626)

```python
_keep = [c for c in ("SOC", "OCV", "CCV") if c in _pts.columns]
```

**After**

```python
_keep = [c for c in ("SOC", "OCV", "CCV", "Crate") if c in _pts.columns]
```

### 2) Continue 모드 ax4 / ax5 플롯 재작성

`legacy_mode == "continue"` 블록 내 `_plot_one` 함수 수정.

**Before**

- ax4: `graph_continue(..., "o")` — 마커+라인 (기본 크기 5pt)
- ax5: `graph_soc_continue(..., "o")` — 충·방전 구분 없이 전체 점 하나의 시리즈로 출력

**After**

- ax4: `ax.plot(..., marker='o', linestyle='none', markersize=3.5)` — 순수 scatter, 마커 30% 축소
- ax5: `Crate` 부호로 Chg/Dch/Rst 분리 → 각 방향 `SOC` 오름차순 정렬 → `marker='o'` + `linestyle='-'`로 scatter+line 표시
  - 범례: `OCV_Chg_`, `OCV_Dch_`, `CCV_Chg_`, `CCV_Dch_` (`Crate==0` 구간은 `_Rst` 접미사)
  - `Crate` 컬럼이 없거나 모두 NaN이면 분리 없이 단일 시리즈로 fallback

## 영향 범위

- PNE DCIR/HPPC 등 OCV/CCV 컬럼이 있는 Continue 프로파일 출력
- Continue 이외 모드 (cycle, charge, discharge) 영향 없음 — `legacy_mode == "continue"` 블록 내부만 수정
- `graph_continue` / `graph_soc_continue` 헬퍼는 수정하지 않아 다른 호출자(DCIR step 뷰 등)에 영향 없음
- `_cycfile_soc`의 `Crate` 컬럼 추가는 엑셀 저장 시트에도 반영됨 (OCV_CCV 시트에 Crate 열 추가)

## 추가: 사이클-이어서-시간 조합 Rest 기본 ON

**배경**: Continue 프로파일에서 DCIR 펄스 사이 휴지 구간은 OCV 관찰/비교를 위해 필요하므로, 해당 조합 선택 시 매번 Rest 체크를 수동 ON 하는 불편이 있었음.

**변경**: `_apply_cyc_continue_rest_default()` 헬퍼 추가 — `(scope=사이클, overlap=이어서, axis=시간)` 조합에 도달하면 `profile_rest_chk`를 자동으로 체크. Scope/overlap 변경 핸들러(`_profile_opt_scope_changed`, `_profile_opt_cont_changed`) 말미에서 호출.

**영향**: 해당 조합 진입 시점에만 동작. 다른 조합은 변경 없음. 사용자가 이후 수동으로 해제하면 그 상태 유지.
