# 사이클 서브탭 확장 Step 4 — Excel `Rest End Chg` 시트 추가

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
관련 계획: `.claude/plans/4-1-1-proud-ladybug.md`

## 배경

Step 1 에서 도입한 `RndV_chg_rest` (충전 직후 Rest 종료 전압, 만충 OCV) 값을 엑셀 결과에도 포함하기 위한 **Step 4 (Excel 확장)**.

방전 후 Rest 는 기존 `Rest End` 시트 (`RndV` 기반) 가 이미 담당하므로 **충전 후 전용 시트 1개만** 추가.

## 변경 내용

`_save_cycle_excel_data()` (L20334+) 의 기존 "Rest End" 블록 직후에 **데이터 존재 시에만** 생성되는 새 시트 추가:

```python
output_data(nd, "Rest End", writecolno, start_row, "OriCyc", cyc_head)
output_data(nd, "Rest End", _dc, start_row, "RndV", headername)
# 충전 Rest End V 시트 (Step 4) — 데이터 있을 때만 생성
if "RndV_chg_rest" in nd.columns and not nd["RndV_chg_rest"].dropna().empty:
    _chg_rest = nd[["OriCyc", "RndV_chg_rest"]].dropna(subset=["RndV_chg_rest"])
    output_data(_chg_rest, "Rest End Chg", writecolno, 0, "OriCyc", cyc_head)
    output_data(_chg_rest, "Rest End Chg", _dc, 0, "RndV_chg_rest", headername)
output_data(nd, "평균 전압", writecolno, start_row, "OriCyc", cyc_head)
```

### 설계 포인트

- 시트명 `"Rest End Chg"` — 기존 `"Rest End"` 와 인접 배치
- `start_row=0` — dropna 로 필터링돼 채널 간 행 수가 다르므로 상단부터 기록 (기존 DCIR 시트와 동일 패턴)
- 가드 조건: `RndV_chg_rest` 컬럼 없거나 모두 NaN 이면 시트 자체 생성 안 됨 (빈 시트 방지)

## 동작 매트릭스

| 시나리오 | 기존 "Rest End" | 신규 "Rest End Chg" |
|---|---|---|
| 일반 PNE 수명 | `RndV` (방전 후 OCV) | `RndV_chg_rest` (만충 OCV) |
| Toyo | 기존 불변 | `RndV_chg_rest` = `RndV` 복사값 |
| GITT/DCIR Sweep | 기존 | Sweep agg `first` |
| 데이터 없음 | 기존 불변 | 시트 미생성 |

## 영향 범위

- `_save_cycle_excel_data` 1개 함수, 5줄 추가
- 기존 시트 구조 완전 보존
- `saveok` 체크 시에만 동작
- 그래프/UI 영향 없음

## 검증 포인트

- [ ] `saveok` 체크 후 사이클 분석 실행 → xlsx 에 "Rest End Chg" 시트 존재
- [ ] 시트 값이 탭2 2-5 Scatter 점과 동일 (4.05–4.25V)
- [ ] 기존 "Rest End" 시트 (= 탭1 1-6 / 탭2 2-6) 불변
- [ ] 방전용량·충전용량·Eff·AvgV·DchgEng·DCIR 등 다른 시트 완전 불변
- [ ] Toyo 데이터에서 "Rest End" ≈ "Rest End Chg" (Toyo `RndV_chg_rest = RndV`)
- [ ] `RndV_chg_rest` 데이터 없는 데이터셋 → "Rest End Chg" 시트 미생성

## 사이클 서브탭 확장 (전체 Step 완료)

| Step | 내용 | 커밋 |
|---|---|---|
| 1 | 데이터 레이어: `RndV_chg_rest` / `RndV_dchg_rest` 파생 | `3c819e7` |
| 1b | `RndV_dchg_rest` 제거 (RndV 로 충분) | `1087041` |
| 2 | 서브탭 UI + tab1 placeholder | `a61d476` |
| 3 | tab2 2×3 그래프 + 탭1 ax6 AvgV 제거 | `504aa3a` |
| 4 | Excel `Rest End Chg` 시트 | (이 커밋) |

**이번 PR 스코프 완료**. 탭 3 (0.2C RPT 프로파일) / 탭 4 (엑셀형 표 + 스웰링) 는 별도 PR 로 이월.

## 관련 계획

`.claude/plans/4-1-1-proud-ladybug.md`
