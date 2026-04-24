# 1-6 Rest End V 원복 — 기존 `RndV` 사용 (충전 직전 / 방전 후 OCV)

날짜: 2026-04-25
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`

## 배경

사용자 재정정:
> 1-6 Rest End Voltage 은 **기존 의미가 맞다. 충전 직전 V.**
> 2-5 가 **충전 후 Rest 종료 = 방전 직전 V** 이다.

직전 커밋 `685b441` 에서 이전 정정을 오해해 1-6 데이터 소스를 `RndV_chg_rest` 로 변경했다. 실제 의미 관계는 다음과 같다.

### 확정 매핑

| 위치 | 의미 | 컬럼 | 값 범위 |
|---|---|---|---|
| **1-6** Rest End V | **충전 직전** V = **방전 후 Rest 종료** OCV | **`RndV`** (pivot Ocv.min) | 2.80–3.30V |
| **2-5** Charge Rest End V | **방전 직전** V = **충전 후 Rest 종료** OCV | `RndV_chg_rest` (Step 1 신규 파생) | 4.05–4.25V |
| **2-6** Discharge Rest End V | 1-6 과 동일 | `RndV` | 2.80–3.30V |

## 변경 내용

`graph_output_cycle` 탭1 ax6 블록을 **Step 3 (`504aa3a`) 이전 상태**로 원복. 폴백 로직/동적 ylim 로직 제거:

```python
# After (원복)
# 1-6 ax6: Rest End Voltage = 충전 직전 V = 방전 후 Rest 종료 OCV
# (= 기존 RndV, pivot Ocv.min 이 실제로 방전 후 OCV 를 캡처)
# 2-5 (Charge Rest End V = RndV_chg_rest) 와 의미가 다름
artists.append(graph_cycle(_x, df.NewData.RndV, ax6, 3.00, 4.00, 0.1,
            "Cycle", "Rest End Voltage (V)", temp_lgnd, xscale, color))
```

## 유지되는 것

- `_ensure_rndv_split_columns` 함수와 `RndV_chg_rest` 파생 컬럼 — **유지** (2-5 에서 사용 중)
- 진단 로그 (결과 전부 NaN 시 경고) — **유지** (2-5 데이터 누락 원인 추적용)
- `graph_output_cycle_tab2` 의 2-5 / 2-6 매핑 — **불변**

## 기존 `RndV` 로직 재확인

PNE (`_process_pne_cycleraw`):
```python
pivot_data = Cycleraw.pivot_table(
    ..., values=[..., "Ocv", ...],
    aggfunc={..., "Ocv": "min", ...})
Ocv = pivot_data["Ocv"][3] / 1000000    # Condition==3 (Rest) Ocv min (μV→V)
```
한 TC 안의 Rest 중 **가장 낮은 OCV** → 방전 후 Rest 종료 OCV (≈ 3.0V) = 다음 충전 직전 V.

Toyo (`toyo_cycle_data`):
```python
Ocv = chgdata["Ocv"]    # 충전 row 의 Ocv 컬럼 = 충전 시작 직전 OCV
```
충전 시작 직전 = 이전 방전 후 Rest 종료 ≈ 충전 직전 V.

두 cycler 모두 의도한 "충전 직전 V" 를 정확히 잡고 있어 **1-6 의미와 일치**.

## 영향 범위

- `graph_output_cycle` 탭1 ax6 (4줄 → 4줄, 로직 단순화)
- 탭2 / `_ensure_rndv_split_columns` / `_auto_adjust_*` 유지
- 사용자 의도와 `RndV` 실제 값이 일치하므로 회귀 없음

## 검증 포인트

- [ ] 사이클 분석 실행 → 탭1 1-6 ax6 에 **3.0V 근처** scatter 표시 (방전 후 OCV)
- [ ] 탭2 2-6 에 동일한 3.0V 근처 scatter (같은 `RndV` 사용)
- [ ] 탭2 2-5 는 **4.1V 근처** (`RndV_chg_rest`, 만충 OCV)
- [ ] 탭1 ax6 ylim = 3.00–4.00V (복구)
- [ ] 1-6 범례 라벨 정상 표시 (temp_lgnd)

## 세션 누적 커밋 순서 (참고)

1. `3c819e7` Step1 데이터 레이어
2. `1087041` Step1b RndV_dchg_rest 제거
3. `a61d476` Step2 서브탭 placeholder
4. `504aa3a` Step3 tab2 그래프 (1-6=RndV 유지)
5. `9ed12a0` Step4 Excel 시트
6. `f14df25` 연결처리 Cycle 오프셋
7. `685b441` 1-6 을 RndV_chg_rest 로 **변경 (이번 원복 대상)**
8. `8566f29` 연결처리 진단 로그
9. `f0728ca` 헤더·캔버스 UI
10. `5225df9` 스타일 통일
11. **이번 커밋** — 1-6 원복
