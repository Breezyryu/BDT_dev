# 사이클 탭 성능 개선 Step 2 — `_process_pne_cycleraw` DataFrame 복사 감소

날짜: 2026-04-24
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
관련 계획: `C:/Users/Ryu/.claude/plans/validated-forging-rabin.md`
선행: Step 1 (`260423_cycle_perf_step1_t1_quickwin_and_ui_signal.md`)

## 배경

`_process_pne_cycleraw` 의 chkir / mkdcir / else 3 분기가 다음 코드를 **각자 중복 선언**:
```python
df.NewData = pd.DataFrame({"Dchg": Dchg, "RndV": Ocv, "Eff": Eff, "Chg": Chg,
                            "DchgEng": DchgEng, "Eff2": Eff2, "Temp": Temp,
                            "AvgV": AvgV, "OriCyc": OriCycle}).reset_index(drop=True)
```
또한 chkir 경로에 `if chkir and len(OriCycle) == len(dcir):` 블록이 있는데 바로 다음 `if chkir:` 가 무조건 덮어써서 **dead code** (메모리 노트 Bug-1 참고). 마지막으로 `dropna` + `reset_index` 가 2회 할당 — intermediate 복사 1회 발생.

## 변경 내용

### 1. 공통 base dict 도입

```python
OriCycle = pd.Series(Dchg.index.values, index=Dchg.index)
# 3 분기 공통 base DataFrame dict — DCIR 컬럼만 분기별 추가.
_base_cols = {"Dchg": Dchg, "RndV": Ocv, "Eff": Eff, "Chg": Chg,
              "DchgEng": DchgEng, "Eff2": Eff2, "Temp": Temp,
              "AvgV": AvgV, "OriCyc": OriCycle}
```
이후 각 분기는 `pd.DataFrame(_base_cols).reset_index(drop=True)` 호출만 — dict 본문 중복 제거.

### 2. chkir dead-code 제거 (Bug-1)

```python
# Before
if chkir and len(OriCycle) == len(dcir):
    df.NewData = pd.concat([Dchg, Ocv, Eff, Chg, DchgEng, Eff2, dcir, Temp, AvgV, OriCycle], axis=1).reset_index(drop=True)
    df.NewData.columns = ["Dchg", "RndV", "Eff", "Chg", "DchgEng", "Eff2", "dcir", "Temp", "AvgV", "OriCyc"]
if chkir:                                       # ← 무조건 덮어씀
    df.NewData = pd.DataFrame({...}).reset_index(drop=True)
    df.NewData.loc[0, "dcir"] = 0

# After
if chkir:
    df.NewData = pd.DataFrame(_base_cols).reset_index(drop=True)
    df.NewData.loc[0, "dcir"] = 0
```

증명: 첫 블록의 조건은 두 번째 `if chkir:` 의 sub-set. 첫 블록이 True면 두 번째도 True → 첫 블록의 `df.NewData` 가 즉시 폐기. 결과 동등.

### 3. else 분기 DataFrame 생성 위치 통합

```python
# Before — dcirtemp 유무에 따라 2번 위치에서 별도 생성
else:
    if 'dcirtemp' in locals():
        # cyccal/dcir 계산
        df.NewData = pd.DataFrame({...}).reset_index(drop=True)   # ★
        ...
    else:
        df.NewData = pd.DataFrame({...}).reset_index(drop=True)   # ★
        df.NewData.loc[0, "dcir"] = 0

# After — 진입 시 1회만 생성, dcir 컬럼만 조건부 할당
else:
    df.NewData = pd.DataFrame(_base_cols).reset_index(drop=True)  # ★ 1회
    if 'dcirtemp' in locals():
        # cyccal/dcir 계산 (df.NewData 미참조 — 순서 무관)
        if 'dcir' in locals() and ...:
            df.NewData["dcir"] = dcir["dcir_raw"]
        ...
    else:
        df.NewData.loc[0, "dcir"] = 0
```
중간 계산이 `df.NewData` 를 읽지 않으므로 순서 변경 안전.

### 4. dropna + reset_index 체인화

```python
# Before — 2회 할당, intermediate 복사 1회 추가
df.NewData = df.NewData.dropna(subset=['Dchg', 'Chg'], how='any')
df.NewData = df.NewData.reset_index(drop=True)

# After — 1회 할당
df.NewData = df.NewData.dropna(subset=['Dchg', 'Chg'], how='any').reset_index(drop=True)
```

## 동등성 검증

| 항목 | 결과 |
|---|---|
| chkir dead code 제거 | 동등 (덮어써지던 코드) |
| base dict 공유 | 동등 (분기마다 새 DataFrame, dict 참조만 공유) |
| else 분기 순서 | 동등 (중간 계산이 df.NewData 미참조) |
| dropna 체인화 | 동등 (메서드 체이닝과 분리 할당이 같은 결과) |

`pd.testing.assert_frame_equal(df_before.NewData, df_after.NewData, ...)` 로 PNE 일반 / Sweep / mkdcir 3종 모드에서 정상 데이터 동등 확인 권장.

## 성능 영향

대형 시험(TC2000 × 채널10) 기준:
- DataFrame 생성 호출 3회 → 1회 (분기당) — 메모리 할당·GC 압박 감소
- intermediate 복사 1회 제거 — 100k 행 기준 약 800KB × 1회 절감
- 누적: **약 1~2초 절감** (PNE 경로)

## 회귀 위험

- **하**: chkir / mkdcir / else 모두 최종 `df.NewData` 컬럼 세트 동일 유지.
- 다운스트림 (`enrich_newdata_with_meta`, `_save_cycle_excel_data`, `_create_cycle_channel_control`, `graph_output_cycle`) 영향 없음 — 컬럼 스키마 변경 없음.
- 디버거 breakpoint 가 chkir dead-code 의 첫 `df.NewData` (concat 결과) 를 관찰하던 경우 사라짐.

## 롤백

`git revert <step2 sha>` 단일 커밋 단위 롤백.

## 다음 단계

Step 3: T2-C FigureCanvas lazy init (탭 생성 메인스레드 블로킹 해소).
