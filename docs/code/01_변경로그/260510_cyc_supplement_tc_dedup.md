# .cyc 보충 TC 중복 dedup — DchgCap 2배 누적 차단 (260510 류성택 보고)

날짜: 2026-05-10
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수:
- `_cached_pne_restore_files` (proto_:1574-1613) — `.cyc` 보충 필터 강화

요청: 류성택 (260510, 우정협 Tab S12 dataset 방전 용량 ~2배 출력 보고)

## 사용자 보고

> `260108_260530_02_우정협_5196mAh_Tab S12+ ATL 4.5V 1-1000 상온수명`
> .cyc로 보충 사이클 방전 용량 값이 크게 출력되는 문제 어제 픽스 진행했는데 왜 다시 문제가 나타났어?
>
> ```
> 0.8747	0.8737	0.8736
> 1.7483	1.7464	1.7461   ← 2배!
> 1.7482	1.7462	1.7458
> 1.7479	1.7460	1.7455
> 1.0407	0.8731	0.9229
> ```

LC 709-711 (3 채널 모두) 약 2배 (~1.748) 출력. 정상 ~0.874 의 정확히 2배.

## 근본 원인 진단

### 데이터 구조 분석 — TC 711-714 raw

3 채널 동일 패턴:
```
TC 711 (CSV): RecIdx 374572, 374624 — DchgCap 2410+2131 mAh
TC 711 (.cyc 보충): RecIdx 373224, 373276 — DchgCap 2409+2134 mAh   ← 중복!
TC 712 (CSV): RecIdx 374909, 374961
TC 712 (.cyc 보충): RecIdx 373561, 373613   ← 중복
TC 713 (CSV): RecIdx 375247, 375299
TC 713 (.cyc 보충): RecIdx 373898, 373950   ← 중복
TC 714 (CSV): RecIdx 375566 (single)
TC 714 (.cyc 보충): RecIdx 374235, 374287   ← 중복
```

같은 TC가 CSV·.cyc 양쪽에 **다른 RecIdx 로 중복 기록**. 채널별 offset 약 1349 일정 — 장비 재시작·chunk 재기록 시나리오로 추정 (.cyc 가 먼저 작성, 이후 CSV 가 더 큰 RecIdx 로 다시 기록).

### 기존 dedup 필터 (proto_:1589-1592)

```python
csv_rec_indices = set(int(x) for x in save_end_data[0].unique())
supplement = _cyc_mapped[
    ~_cyc_mapped[0].astype(int).isin(csv_rec_indices)]
```

**RecIdx 기준 필터만 사용** → 같은 TC 라도 RecIdx 가 다르면 통과 → CSV TC 711-715 가 이미 존재함에도 .cyc 의 TC 711-714 추가됨 (27행).

### 누적 단계 — `_process_pne_cycleraw` (proto_:12327-12340)

```python
pivot_data = Cycleraw.pivot_table(
    index="TotlCycle", columns="Condition",
    values=["DchgCap", ...],
    aggfunc={"DchgCap": "sum", ...}
)
Dchg = pivot_data["DchgCap"][2] / mincapacity / 1000
```

`aggfunc=sum` 으로 같은 (TC, Condition) 쌍의 모든 DchgCap 행을 합산.
TC 711 의 4 dchg 행 (CSV 2 + .cyc 2): 2410+2131+2409+2134 ≈ 9084 mAh / 5196 ≈ **1.748** = 사용자 관찰값.

## 변경 — TC overlap 가드 추가

```python
# 260510 fix (류성택 보고): 같은 TC가 CSV·.cyc 양쪽에 다른 RecIdx로
# 중복 기록된 경우 RecIdx 필터만으로는 차단 못해 pivot_table aggfunc=sum
# 단계에서 DchgCap 이 2배로 누적되는 문제. → CSV 에 이미 존재하는 TC 는
# .cyc 보충에서 완전 제외 (CSV 가 더 신뢰 가능한 최신 기록).
csv_rec_indices = set(int(x) for x in save_end_data[0].unique())
csv_tcs = set(int(x) for x in save_end_data[27].unique())   # NEW
supplement = _cyc_mapped[
    ~_cyc_mapped[0].astype(int).isin(csv_rec_indices)
    & ~_cyc_mapped[27].astype(int).isin(csv_tcs)]            # NEW
```

### 정책

- **CSV가 더 신뢰 가능한 최신 기록**으로 간주 (chunk 재기록은 마지막에 작성된 값이 정상)
- `.cyc` 보충은 **CSV가 가지지 않은 TC**만 추가 (gap-fill 본 의도)
- 같은 TC 가 CSV·.cyc 양쪽에 있으면 .cyc 측 무시

## 검증 — 우정협 Ch013/Ch014/Ch015

| 채널 | LC 709 Before | LC 709 After | LC 710 Before | LC 710 After | LC 711 Before | LC 711 After |
|---|---|---|---|---|---|---|
| Ch013 | 1.7483 | **0.8744** | 1.7482 | **0.8743** | 1.7479 | **0.8740** |
| Ch014 | 1.7464 | **0.8735** | 1.7462 | **0.8733** | 1.7460 | **0.8731** |
| Ch015 | 1.7461 | **0.8733** | 1.7458 | **0.8731** | 1.7455 | **0.8729** |

전체 Dchg > 1.2 인 LC: 3개 → **0개** (이상값 완전 제거).

`save_end` shape: 5777 → 5750 (27행 .cyc 중복 제외, CSV 만으로 정합).

## 회귀

- `tools/test_code/regression_classify_pne_cycles.py --verify`: **PASS 760 entries** (baseline = 251028 dataset, 영향 없음)
- exp_data 전수 export (204 datasets): 27.0s 정상 완료, 회귀 0
- 다른 .cyc 보충 데이터셋 영향: TC overlap 없는 경우 (gap-fill 본 의도) 동작 불변

## "어제 픽스" 컨텍스트

사용자가 언급한 "어제 픽스" 는 `b907425` (260418, .cyc 보충 로그 확장) 추정. 해당 commit 은 로그 출력만 개선했고 dedup 로직은 그대로였음. 본 fix 가 dedup의 실질적 개선 (RecIdx-only → RecIdx + TC).

## 호환성

- **TC overlap 없는 .cyc 보충** (정상 gap-fill 시나리오): RecIdx 필터만으로 충분 → 기존 동작 유지
- **TC overlap 있는 .cyc 보충** (장비 재시작·chunk 재기록 시나리오): TC 가드 추가로 차단 → CSV 만 사용
- **`.cyc 단독`** (CSV 없는 케이스, proto_:1614+): 영향 없음 (별도 경로)

## 영향 범위

### 직접 영향
- 우정협 Tab S12 dataset 3 채널 LC 709-711 정상화
- 동일 패턴 (TC 중복) 데이터셋 자동 정상화 — 검출 시 .cyc 무시

### 간접 영향
- Phase 0 메타 캐시 일관성 (cycle_map / classified / max_tc) 회복
- 사이클 분석·프로파일 분석·연결처리 라우팅 모두 정합

### 무영향
- 정상 gap-fill (.cyc TC ⊄ CSV TC) — 보충 그대로 동작
- `.cyc 단독` 재구성 (Restore 없음)
- 비-PNE (Toyo) 데이터

## 적용 파일

- `DataTool_dev_code/DataTool_optRCD_proto_.py` (worktree zen-volhard-e787a1)
- 산출물: `docs/code/02_레퍼런스/260510_exp_data_cycle_timelines_v4.html`
- main 머지 후: `C:/Users/Ryu/battery/python/BDT_dev/DataTool_dev_code/DataTool_optRCD_proto_.py`

## 검증 절차 (사용자)

1. 앱 재시작 (또는 `_reset_all_caches()` 호출)
2. `260108_260530_02_우정협_5196mAh_Tab S12+` 폴더 입력 → 사이클 분석
3. 사이클 데이터 출력에서 LC 709-711 방전 용량 비율 ~0.87 확인 (이전 1.74)
4. 사이클 바: TC 711-714 영역에서 정상 색상 + 정상 표시 확인
5. 다른 .cyc 보충 데이터셋 (gap-fill 정상 케이스): 회귀 없음 확인

## 후속 정합 후보

- `_check_endpoint_anomaly` (260509 ec2fe55) 와 결합 — TC overlap 감지 시 자동 경고
- `.cyc 보충` 로그에 "TC overlap 차단" 사례 명시 (예: `차단된 .cyc TC: 711-714`)
- `_classify_pne_integrity` (260509) 4-tier 분류에 TC overlap 케이스 추가
