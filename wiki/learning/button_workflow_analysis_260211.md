# BatteryDataTool 버튼 워크플로우 분석

> 작성일: 2026-02-11  
> 대상 파일: `BatteryDataTool_260206_edit copy/BatteryDataTool_optRCD.py` (14,887 lines)

---

## 1. 버튼 기능 분류표

### 1.1 Cycle 분석 버튼 (6종)

| 버튼 함수 | 설명 | 그래프 모드 | 데이터 경로 |
|---|---|---|---|
| `indiv_cyc_confirm_button` | 개별 사이클 (셀별 분리) | 셀별 fig | `pne_path` |
| `overall_cyc_confirm_button` | 통합 사이클 (전체 오버레이) | 단일 fig | `pne_path` |
| `link_cyc_confirm_button` | 연결 사이클 (index 이어붙임) | 단일 fig | `pne_path` |
| `link_cyc_indiv_confirm_button` | CSV 링크 - 셀별 분리 | CSV별 fig | `CSV filedialog` |
| `link_cyc_overall_confirm_button` | CSV 링크 - 전체 통합 | 단일 fig | `CSV filedialog` |
| `app_cyc_confirm_button` | 승인용 사이클 (xlsx 읽기) | 단일 fig | `filedialog xlsx` |

### 1.2 Profile 분석 버튼 (4종)

| 버튼 함수 | 설명 | Graph 함수 | 데이터 파싱 |
|---|---|---|---|
| `step_confirm_button` | 스텝 프로파일 | `graph_step` | `toyo/pne_step_Profile_data` |
| `rate_confirm_button` | Rate 프로파일 | `graph_step` | `toyo/pne_rate_Profile_data` |
| `chg_confirm_button` | 충전 프로파일 | `graph_profile` | `toyo/pne_chg_Profile_data` |
| `dchg_confirm_button` | 방전 프로파일 | `graph_profile` | `toyo/pne_dchg_Profile_data` |

### 1.3 Continue/DCIR 버튼 (3종)

| 버튼 함수 | 설명 | 특이사항 |
|---|---|---|
| `pro_continue_confirm_button` | 연속 프로파일 | `toyo/pne_Profile_continue_data`, OCV/CCV 지원 |
| `ect_confirm_button` | ECT 경로 연속 프로파일 | `pne_Profile_continue_data`, ECT CSV 파싱 |
| `dcir_confirm_button` | DCIR 분석 | `pne_dcir_Profile_data`, 2×2 그래프, PNE 전용 |

---

## 2. 공통 워크플로우 5단계

모든 버튼 함수는 아래 5단계 패턴을 따른다:

```
[Stage 1] Init       → 버튼 비활성화, UI 설정 읽기, 경로 취득
[Stage 2] Load       → 데이터 파싱 (PNE/TOYO 분기), 병렬처리
[Stage 3] Plot       → matplotlib subplots 생성, graph_* 함수 호출
[Stage 4] Output     → Excel/CSV 저장, output_fig 이미지 저장
[Stage 5] Cleanup    → writer.close(), progressBar 100%, plt.close()
```

---

## 3. Stage 1: Init 패턴 (3종)

### 3.1 `cyc_ini_set()` — Cycle 버튼 전용 (L8744)

```python
def cyc_ini_set(self):
    firstCrate = float(self.ratetext.text())
    mincapacity = 0 if self.inicaprate.isChecked() else float(self.capacitytext.text())
    xscale = int(self.tcyclerng.text())
    ylimithigh = float(self.tcyclerngyhl.text())
    ylimitlow = float(self.tcyclerngyll.text())
    irscale = float(self.dcirscale.text())
    return firstCrate, mincapacity, xscale, ylimithigh, ylimitlow, irscale
```

**사용 버튼**: `indiv_cyc`, `overall_cyc`, `link_cyc`, `link_cyc_indiv`, `link_cyc_overall`, `app_cyc`

### 3.2 `Profile_ini_set()` — Profile 버튼 전용 (L8757)

```python
def Profile_ini_set(self):
    firstCrate, mincapacity = ...  # cyc_ini_set과 동일
    CycleNo = convert_steplist(self.stepnum.toPlainText())  # "1 3-5 8" → [1,3,4,5,8]
    smoothdegree = int(self.smooth.text())
    mincrate = float(self.cutoff.text())
    dqscale = float(self.dqdvscale.text())
    dvscale = dqscale
    vol_y_hlimit, vol_y_llimit, vol_y_gap = ...  # 전압 Y축 범위
    return firstCrate, mincapacity, CycleNo, smoothdegree, mincrate, dqscale, dvscale
```

**사용 버튼**: `pro_continue`, `ect`, `dcir` (직접 호출)

### 3.3 `_init_confirm_button(button_widget)` — 통합 Init (L8463)

```python
def _init_confirm_button(self, button_widget):
    button_widget.setDisabled(True)
    config = self.Profile_ini_set()
    pne_path = self.pne_path_setting()
    button_widget.setEnabled(True)
    return {'firstCrate', 'mincapacity', 'CycleNo', ...}
```

**사용 버튼**: `step`, `rate`, `chg`, `dchg` (리팩토링 완료)

---

## 4. Stage 1.5: 데이터 경로 취득 (4종)

| 방식 | 함수/로직 | 사용 버튼 |
|---|---|---|
| **pne_path** | `self.pne_path_setting()` → CSV or 직접 폴더 선택 | indiv/overall/link_cyc, step/rate/chg/dchg, continue, dcir |
| **filedialog xlsx** | `filedialog.askopenfilenames()` → xlsx 직접 선택 | `app_cyc` |
| **filedialog CSV** | `filedialog.askopenfilenames()` → CSV에서 cyclepath 읽기 | `link_cyc_indiv`, `link_cyc_overall` |
| **ECT path** | ECT CSV에서 `path`, `cycle`, `CD`, `save` 컬럼 파싱 | `ect_confirm_button` |

### `pne_path_setting()` 상세 (L8788)

```
chk_cyclepath 체크 → filedialog로 txt/csv 선택 → cyclepath/cyclename 파싱
stepnum_2 텍스트 → 직접 경로 입력 (줄바꿈 구분)
둘 다 아님 → multi_askopendirnames() 폴더 다이얼로그
```

반환: `[all_data_folder, all_data_name, datafilepath]`

---

## 5. Stage 2: 데이터 파싱 함수 매핑

### 5.1 Cycle 데이터 파싱

| 충방전기 | 함수 | 파일 위치 |
|---|---|---|
| **TOYO** | `toyo_cycle_data(FolderBase, mincapacity, firstCrate, dcirchk_2)` | L512 |
| **PNE** | `pne_cycle_data(FolderBase, mincapacity, firstCrate, dcirchk, dcirchk_2, mkdcir)` | L1285 |

- 병렬 로딩: `_load_all_cycle_data_parallel()` (L8686) → `ThreadPoolExecutor(max_workers=4)`
- 사용 버튼: `indiv_cyc`, `overall_cyc`, `link_cyc`, `link_cyc_indiv`, `link_cyc_overall`

### 5.2 Profile 데이터 파싱

| 기능 | TOYO 함수 | PNE 함수 |
|---|---|---|
| Step Profile | `toyo_step_Profile_data` | `pne_step_Profile_data` |
| Rate Profile | `toyo_rate_Profile_data` | `pne_rate_Profile_data` |
| Chg Profile | `toyo_chg_Profile_data` | `pne_chg_Profile_data` |
| Dchg Profile | `toyo_dchg_Profile_data` | `pne_dchg_Profile_data` |
| Continue | `toyo_Profile_continue_data` | `pne_Profile_continue_data` |
| DCIR | — (PNE 전용) | `pne_dcir_Profile_data` |

- 충방전기 판별: `check_cycler(cyclefolder)` → `True`면 PNE, `False`면 TOYO
- Step Profile만 병렬 배치 로딩 지원: `_load_all_step_data_parallel()` (L8595)

---

## 6. Stage 3: 그래프 모드 3-Way 분기

Profile 버튼 4종(step, rate, chg, dchg)과 continue 버튼은 3-way 분기 구조:

### 6.1 CycProfile 모드 (`self.CycProfile.isChecked()`)

```
for i, cyclefolder:
    for FolderBase in subfolder:        ← 셀 단위로 fig 생성
        fig = plt.subplots(2,3)
        for CycNo in CycleNo:           ← 사이클을 같은 fig에 오버레이
            graph_*()
        finalize_tab()                   ← 셀 하나당 1탭
```

- **X축**: 셀 (채널)
- **범례**: 사이클 번호 (`%04d`)
- **title**: `셀이름_채널번호`

### 6.2 AllProfile 모드 (`self.AllProfile.isChecked()`)

```
fig = plt.subplots(2,3)                 ← 루프 전 fig 1개 생성
for i, cyclefolder:
    for FolderBase in subfolder:
        for CycNo in CycleNo:           ← 모든 데이터를 1개 fig에 오버레이
            graph_*()
finalize_tab()                           ← 전체 1탭
```

- **X축**: 전체 (셀×사이클 조합)
- **범례**: `채널명 + 사이클번호`
- **title**: `폴더명 All`
- **특이사항**: `_setup_legend()`에서 항목 수 ≥ `LEGEND_THRESHOLD`이면 그라데이션+컬러바 자동 전환

### 6.3 Default 모드 (둘 다 미체크)

```
for i, cyclefolder:
    for CycNo in CycleNo:               ← 사이클 단위로 fig 생성
        fig = plt.subplots(2,3)
        for FolderBase in subfolder:     ← 채널을 같은 fig에 오버레이
            graph_*()
        finalize_tab()                   ← 사이클 하나당 1탭
```

- **X축**: 사이클
- **범례**: 채널명
- **title**: `폴더명=사이클번호`

### 6.4 Cycle 버튼 그래프 모드

| 버튼 | fig 생성 단위 | 오버레이 단위 |
|---|---|---|
| `indiv_cyc` | 최상위 폴더별 | 채널 (subfolder) |
| `overall_cyc` | 전체 1개 fig | 모든 폴더×채널 |
| `link_cyc` | 전체 1개 fig + index 이어붙이기 | 모든 폴더×채널 |
| `link_cyc_indiv` | CSV 파일별 | CSV 내 모든 폴더 (index 이어붙이기) |
| `link_cyc_overall` | 전체 1개 fig | 모든 CSV×폴더 (index 이어붙이기) |
| `app_cyc` | 전체 1개 fig | 선택한 xlsx 파일들 |

---

## 7. 6-Panel 그래프 구성

### 7.1 Cycle 그래프 (2×3)

```
ax1: 방전용량 (Dchg Capacity)     ax2: 방전평균전압 (Avg Voltage)    ax3: 충방효율 (Efficiency)
ax4: 충전용량 (Chg Capacity)      ax5: 저항 (DCIR)                  ax6: 방전Energy
```

- 사용 함수: `graph_output_cycle(cyctemp[1], xscale, ylimitlow, ylimithigh, irscale, lgnd, ...)`
- `graph_output_cycle`은 내부에서 6개 ax에 각각 `graph_cycle` 호출

### 7.2 Step/Continue Profile 그래프 (2×3)

```
ax1: Voltage vs Time  ax2: Crate vs Time     ax3: SOC vs Time
ax4: Voltage vs Time  ax5: Crate (음방향)    ax6: Temp vs Time
```

- 사용 함수: `graph_step()`, `graph_continue()`
- Step은 `_plot_and_save_step_data()`로 추출됨

### 7.3 Chg/Dchg Profile 그래프 (2×3)

```
ax1: Voltage vs SOC   ax2: dQdV vs Voltage  ax3: Voltage vs SOC (duplicate)
ax4: dVdQ vs SOC      ax5: C-rate vs SOC    ax6: Temp vs SOC
```

- 사용 함수: `graph_profile()`
- chg: `dchg_confirm_button`에서는 X축이 DOD로 변경

### 7.4 Rate Profile 그래프 (2×3)

```
ax1: Voltage vs Time  ax2: Crate vs Time     ax3: SOC vs Time
ax4: Voltage vs Time  ax5: Crate vs Time     ax6: Temp vs Time
```

### 7.5 DCIR 그래프 (2×2)

```
ax1: OCV/CCV vs SOC   ax3: SOC vs Voltage
ax2: DCIR vs SOC       ax4: DCIR vs OCV
```

- 사용 함수: `graph_soc_continue()`, `graph_soc_dcir()`, `graph_dcir()`

---

## 8. Stage 4: 데이터 저장

### 8.1 Excel 저장 패턴 (공통)

```python
if self.saveok.isChecked() and save_file_name:
    df.to_excel(writer, startcol=writecolno, index=False, header=[...])
    writecolno += N  # N = 컬럼 수
```

### 8.2 output_data() — Cycle 전용

```python
output_data(cyctemp[1].NewData, "방전용량", writecolno, writerowno, "Dchg", headername)
output_data(cyctemp[1].NewData, "Rest End", writecolno, writerowno, "RndV", headername)
output_data(cyctemp[1].NewData, "평균 전압", writecolno, writerowno, "AvgV", headername)
output_data(cyctemp[1].NewData, "충방효율", writecolno, writerowno, "Eff", headername)
output_data(cyctemp[1].NewData, "충전용량", writecolno, writerowno, "Chg", headername)
output_data(cyctemp[1].NewData, "방충효율", writecolno, writerowno, "Eff2", headername)
output_data(cyctemp[1].NewData, "방전Energy", writecolno, writerowno, "DchgEng", headername)
# DCIR 관련 (mkdcir 체크 시)
output_data(cyctempdcir, "DCIR/RSS", writecolno, 0, "dcir/dcir2", headername)
output_data(cyctemprssocv, "RSS_OCV", writecolno, 0, "rssocv", headername)
output_data(cyctemprssccv, "RSS_CCV", writecolno, 0, "rssccv", headername)
```

### 8.3 ECT CSV 저장 패턴

```python
if self.ect_saveok.isChecked() and save_file_name:
    continue_df = temp[1].Profile[["TimeMin", "Vol", "Crate", "Temp"]].copy()
    continue_df["TimeSec"] = (continue_df["TimeMin"] * 60).round(1)
    continue_df["Curr"] = (continue_df["Crate"] * capacity / 1000).round(4)
    continue_df.to_csv(save_file_name + "_0001.csv", header=["time(s)", "Voltage(V)", "Current(A)", "Temp."])
```

### 8.4 이미지 저장

```python
output_fig(self.figsaveok, filename)  # figsaveok 체크 시 png 저장
```

---

## 9. 추출 완료된 공통 헬퍼 함수

| 함수 | 위치 | 역할 | 사용 버튼 |
|---|---|---|---|
| `_init_confirm_button()` | L8463 | 버튼 비활성화 + Profile_ini_set + pne_path 통합 | step, rate, chg, dchg |
| `_setup_file_writer()` | L8490 | saveok/ect_saveok 체크 → writer 생성 | step, rate, chg, dchg, continue |
| `_create_plot_tab()` | L8514 | QWidget + QVBoxLayout + FigureCanvas + Toolbar | step, rate, chg, dchg, continue |
| `_finalize_plot_tab()` | L8525 | 탭 위젯 조립 + cycle_tab 등록 + tight_layout | step, rate, chg, dchg, continue |
| `_setup_legend()` | L8539 | 범례/그라데이션 자동 전환 (LEGEND_THRESHOLD) | step, rate, chg, dchg, continue |
| `_plot_and_save_step_data()` | L8654 | step 6개 그래프 + Excel/CSV 저장 통합 | step |
| `_load_all_cycle_data_parallel()` | L8686 | ThreadPoolExecutor 사이클 병렬 로딩 | indiv/overall/link_cyc 전체 |
| `_load_all_step_data_parallel()` | L8595 | ThreadPoolExecutor 스텝 배치 병렬 로딩 | step |
| `graph_output_cycle()` | 전역 | Cycle 6-panel 그래프 출력 | cycle 버튼 전체 |

---

## 10. 미추출 중복 패턴 (리팩토링 후보 6종)

### 10.1 output_data 블록 (Cycle 버튼)

`indiv_cyc`, `overall_cyc`, `link_cyc`, `link_cyc_indiv`, `link_cyc_overall`에서 **동일한 7+α개 output_data 호출**이 반복됨.

```python
# 후보: _save_cycle_output(cyctemp, writecolno, writerowno, headername, mkdcir_checked)
```

### 10.2 graph_output_cycle 전후 로직

```python
# 반복 패턴:
if hasattr(cyctemp[1], "NewData"):
    self.capacitytext.setText(str(cyctemp[0]))
    irscale = ...
    graph_output_cycle(...)
    if self.saveok.isChecked():
        output_data(...) × 7~12
```

→ `_process_cycle_data_and_plot()` 추출 가능

### 10.3 chg/dchg 그래프 패턴

`chg_confirm_button`과 `dchg_confirm_button`은 X축 라벨(SOC↔DOD), dQdV 부호, 범례 위치만 다르고 **구조 99% 동일**.

```python
# 후보: _chg_dchg_confirm_button(mode="chg"|"dchg")
```

### 10.4 rate 그래프 패턴

`rate_confirm_button`의 6×`graph_step` 호출이 3-way 분기 내에서 3번 반복됨.

```python
# 후보: _plot_rate_graphs(axes, Ratetemp, headername, lgnd, temp_lgnd)
```

### 10.5 ECT CSV 저장 패턴

`rate`, `chg`, `dchg` 버튼에서 **동일한 CSV 변환 + 저장 로직** 반복:

```python
continue_df = temp[1].Profile[["TimeMin", "Vol", "Crate", "Temp"]].copy()
continue_df["TimeSec"] = (continue_df["TimeMin"] * 60).round(1)
continue_df["Curr"] = (continue_df["Crate"] * capacity / 1000).round(4)
continue_df.to_csv(...)
```

→ `_save_ect_csv(df, capacity, save_path, filename)` 추출 가능

### 10.6 link index 누적 패턴

`link_cyc`, `link_cyc_indiv`, `link_cyc_overall`에서:

```python
CycleMax = [0, 0, 0, 0, 0]
link_writerownum = [0, 0, 0, 0, 0]
...
writerowno = link_writerownum[Chnl_num] + CycleMax[Chnl_num]
cyctemp[1].NewData.index = cyctemp[1].NewData.index + writerowno
...
CycleMax[Chnl_num] = len(cyctemp[1].NewData)
link_writerownum[Chnl_num] = writerowno
Chnl_num += 1
```

→ `LinkIndexAccumulator` 클래스 추출 가능

---

## 11. 버튼별 상세 워크플로우 요약

### 11.1 `indiv_cyc_confirm_button` (L8920)

```
1. cyc_ini_set() → firstCrate, mincapacity, xscale, ylimithigh, ylimitlow, irscale
2. pne_path_setting() → all_data_folder, all_data_name
3. _setup_file_writer()
4. _load_all_cycle_data_parallel() → loaded_data dict
5. for cyclefolder:
     fig = plt.subplots(2,3)     ← 각 최상위 폴더별 1개 fig
     for subfolder:
       loaded_data[(i, sub_idx)] → graph_output_cycle()
       output_data() × 7~12
     finalize (tab 추가)
6. writer.close(), plt.close()
```

### 11.2 `overall_cyc_confirm_button` (L9050)

```
1~4. indiv와 동일
5. fig = plt.subplots(2,3)       ← 전체 1개 fig
   for cyclefolder:
     for subfolder:
       graph_output_cycle()      ← 모든 데이터 오버레이
       output_data() × 7~12
6. legend checkbox 추가 (toggle_legend)
7. writer.close(), plt.close()
```

### 11.3 `link_cyc_confirm_button` (L9260)

```
1~4. overall과 동일
5. fig = plt.subplots(2,3)       ← 전체 1개 fig
   CycleMax, link_writerownum 초기화
   for cyclefolder:
     for subfolder:
       writerowno = link_writerownum[Chnl_num] + CycleMax[Chnl_num]
       cyctemp[1].NewData.index += writerowno   ← index 이어붙이기
       graph_output_cycle()
6. writer.close(), plt.close()
```

### 11.4 `step_confirm_button` (L9780)

```
1. _init_confirm_button(self.StepConfirm)
2. _setup_file_writer()
3. _load_all_step_data_parallel() → loaded_data dict
4. 3-way 분기:
   CycProfile:  셀별 fig, 사이클 오버레이
   AllProfile:  전체 1개 fig (루프 전 생성)
   Default:     사이클별 fig, 채널 오버레이
5. _plot_and_save_step_data() → 6개 그래프 + 저장
6. _setup_legend(), _finalize_plot_tab()
```

### 11.5 `rate_confirm_button` (L9960)

```
1. _init_confirm_button(self.RateConfirm)
2. _setup_file_writer()
3. 3-way 분기 (step과 동일 구조)
4. toyo/pne_rate_Profile_data() → Ratetemp
5. graph_step() × 6 (TimeMin vs Vol, Crate, SOC, Temp)
6. _setup_legend(), _finalize_plot_tab()
```

### 11.6 `chg_confirm_button` (L10130)

```
1. _init_confirm_button(self.ChgConfirm)
2. _setup_file_writer()
3. 3-way 분기
4. toyo/pne_chg_Profile_data() → Chgtemp
5. graph_profile() × 6 (SOC vs Vol, dQdV, Crate, dVdQ, Temp)
   ※ chk_dqdv 체크 시 dQdV X/Y 축 반전
6. ECT CSV 저장 지원
```

### 11.7 `dchg_confirm_button` (L10330)

```
chg_confirm_button과 99% 동일
차이점:
- X축 라벨: SOC → DOD
- dQdV 스케일: 양수 → 음수 (-5 * dqscale)
- dVdQ 스케일: 양수 → 음수 (-5 * dvscale)
- 범례 위치: lower right → lower left / upper left
```

### 11.8 `pro_continue_confirm_button` (L10760)

```
1. Profile_ini_set() (직접 호출)
2. pne_path_setting()
3. _setup_file_writer()
4. stepnum 파싱: "2 3-5 8" → [(2,2), (3,5), (8,8)]  (start-end 범위)
5. 3-way 분기 (CycProfile/AllProfile/Default)
6. toyo/pne_Profile_continue_data() → temp
7. graph_continue() × 6
   ※ OCV/CCV 컬럼 존재 시 추가 오버레이 (ax4, ax5)
8. Excel: Profile 시트 + OCV_CCV 시트 분리 저장
```

### 11.9 `ect_confirm_button` (L10660)

```
1. Profile_ini_set()
2. filedialog → ECT CSV 파싱 (path, cycle, CD, save 컬럼)
3. for ect_path:
     for subfolder:
       pne_Profile_continue_data(ect_CD 전달)
       graph_continue() × 6
       CSV 강제 저장: "D:\\" + ect_save[i] + ".csv"
```

### 11.10 `dcir_confirm_button` (L10910)

```
1. Profile_ini_set()
2. pne_path_setting()
3. pne_dcir_chk_cycle(FolderBase) → DCIR 사이클 자동 감지
4. PNE 전용 확인 (TOYO 시 에러 메시지)
5. pne_dcir_Profile_data() → temp
6. fig = plt.subplots(2,2)   ← 2×2 레이아웃 (유일)
7. graph_soc_continue(), graph_soc_dcir(), graph_dcir()
8. 탭 이름: "chg0", "dchg0" (SOC 기준 자동 분류)
9. Excel: DCIR 시트 + RSQ 시트
```

### 11.11 `app_cyc_confirm_button` (L8824)

```
1. cyc_ini_set()
2. filedialog.askopenfilenames() → xlsx 파일 직접 선택
3. xw.Book(datafilepath) → xlwings로 Excel 읽기
4. "Plot Base Data" 시트에서 용량 비율 계산
5. 홀짝 행 병합 로직 (비정규 데이터 보정)
6. graph_cycle() → 단일 ax1에 오버레이
7. dfoutput.to_excel() → "Approval_cycle" 시트
```

---

## 12. 데이터 흐름 다이어그램

```
[UI 입력]
    │
    ├─ cyc_ini_set() / Profile_ini_set() / _init_confirm_button()
    │       ↓
    ├─ pne_path_setting() / filedialog / ECT CSV
    │       ↓
    │   [all_data_folder, all_data_name]
    │       ↓
    ├─ check_cycler() ──→ PNE? / TOYO?
    │       ↓                ↓
    │   pne_*_data()    toyo_*_data()
    │       ↓                ↓
    │   [mincapacity, DataObject]
    │       ↓
    ├─ 3-way 분기 (CycProfile / AllProfile / Default)
    │       ↓
    │   graph_step / graph_profile / graph_continue / graph_cycle
    │       ↓
    ├─ to_excel() / output_data() / to_csv()
    │       ↓
    └─ _finalize_plot_tab() → cycle_tab 등록
```

---

## 13. 병렬 처리 아키텍처

### 13.1 Cycle 병렬 로딩

```
_load_all_cycle_data_parallel()
    │
    ├─ tasks = [(folder, mincap, firstCrate, dcir_flags, is_pne, i, j), ...]
    │
    ├─ ThreadPoolExecutor(max_workers=4)
    │       ├─ _load_cycle_data_task() → pne_cycle_data() or toyo_cycle_data()
    │       ├─ _load_cycle_data_task() → ...
    │       └─ _load_cycle_data_task() → ...
    │
    └─ results = {(i, j): (folder_path, cyctemp)}
```

### 13.2 Step 배치 병렬 로딩

```
_load_all_step_data_parallel()
    │
    ├─ tasks = [(folder, CycleNo_list, mincap, ..., is_pne, i, j), ...]
    │
    ├─ ThreadPoolExecutor(max_workers=4)
    │       ├─ _load_step_batch_task() → pne_step_Profile_batch(folder, CycleNo_list)
    │       └─ _load_step_batch_task() → toyo_step_Profile_batch(folder, CycleNo_list)
    │
    └─ results = {(i, j, cyc_no): temp}
```

**차이점**: Step은 **채널 단위 배치** (1채널의 모든 사이클을 한 번에 로딩), Cycle은 **폴더 단위**

---

## 14. 부록: 그래프 함수 카탈로그

| 함수 | X | Y | 용도 |
|---|---|---|---|
| `graph_cycle()` | index | value | Cycle 분석 (방전용량, 효율 등) |
| `graph_output_cycle()` | — | — | Cycle 6-panel 래퍼 |
| `graph_step()` | TimeMin | Vol/Crate/SOC/Temp | Step/Rate Profile |
| `graph_profile()` | SOC/dQdV | Vol/dVdQ/Crate/Temp | Chg/Dchg Profile |
| `graph_continue()` | TimeMin | Vol/Crate/SOC/Temp | Continue Profile |
| `graph_soc_continue()` | SOC | OCV/CCV | DCIR OCV-CCV |
| `graph_soc_dcir()` | SOC | DCIR(mΩ) | DCIR vs SOC |
| `graph_dcir()` | OCV | DCIR(mΩ) | DCIR vs OCV |

---

## 15. 부록: 저장 시트 카탈로그

| 버튼 | Excel 시트 | 컬럼 수/단위 |
|---|---|---|
| Cycle 전체 | Dchg, RndV, AvgV, Eff, Chg, Eff2, DchgEng, dcir, dcir2, rssocv, rssccv | output_data별 1열 |
| Step | (기본 시트) | 5열: time, SOC, Voltage, Crate, Temp |
| Rate | (기본 시트) | 5열: time, SOC, Voltage, Crate, Temp |
| Chg/Dchg | (기본 시트) | 8열: Time, SOC, Energy, Voltage, Crate, dQdV, dVdQ, Temp |
| Continue (OCV 있음) | Profile + OCV_CCV | 8열 + 3열 |
| Continue (OCV 없음) | Profile | 5열: Time, SOC, Voltage, Crate, Temp |
| DCIR | DCIR + RSQ | 9열: Capacity, SOC, OCV, 0.1s/1.0s/10.0s/20.0s DCIR, RSS, CCV |
| App Cycle | Approval_cycle | 컬럼수 = 파일별 가변 |
