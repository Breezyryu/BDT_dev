# Profile Confirm 기능 상세 분석

> **작성일**: 2026-02-09  
> **대상 파일**: `BatteryDataTool.py`  
> **분석 목적**: 각 Confirm 버튼 기능 최적화를 위한 사전 분석

---

## 1. 기능 목록 및 역할

| 버튼 | 함수명 | 역할 | 데이터 함수 |
|------|--------|------|-------------|
| **StepConfirm** | `step_confirm_button()` | Step 충전 Profile 분석 | `toyo_step_Profile_data` / `pne_step_Profile_data` |
| **RateConfirm** | `rate_confirm_button()` | Rate 충전 Profile 분석 | `toyo_rate_Profile_data` / `pne_rate_Profile_data` |
| **ChgConfirm** | `chg_confirm_button()` | 충전 Profile (dQ/dV 포함) | `toyo_chg_Profile_data` / `pne_chg_Profile_data` |
| **DchgConfirm** | `dchg_confirm_button()` | 방전 Profile (dQ/dV 포함) | `toyo_dchg_Profile_data` / `pne_dchg_Profile_data` |
| **ContinueConfirm** | `continue_confirm_button()` | 연속 Profile 분석 | 조건에 따라 분기 |
| **DCIRConfirm** | `dcir_confirm_button()` | SOC별 DCIR 측정 | PNE 전용 (`pne_dcir_Profile_data`) |

---

## 2. Toyo vs PNE 데이터 구조 비교

### 2.1 파일/폴더 구조

| 항목 | **Toyo** | **PNE** |
|------|----------|---------|
| 사이클 파일 | 개별 파일 (`000001`, `000002`, ...) | 통합 CSV (`SaveData0001.csv`, ...) |
| 용량 요약 | `capacity.log` | `SaveEndData.csv` |
| 파일 수 | 500+ (사이클당 1개) | 100~200 (통합) |
| I/O 특성 | 다수 소형 파일 (느림) | 소수 대형 파일 (빠름) |

### 2.2 데이터 접근 방식

```
[Toyo]
  raw_file_path + "\\%06d" % cycle  → 개별 CSV 로드
  ↓
  pd.read_csv() 호출 (사이클마다)

[PNE]
  pne_data() → SaveData 파일들을 한 번에 로드하여 병합
  ↓
  DataFrame 내에서 cycle 번호로 필터링
```

---

## 3. 각 데이터 함수 분석

### 3.1 Step Profile (`toyo_step_Profile_data` / `pne_step_Profile_data`)

| 항목 | Toyo | PNE |
|------|------|-----|
| 파일 접근 | `toyo_Profile_import()` 반복 호출 | `pne_data()` 1번 호출 |
| 용량 계산 | 벡터화됨 ✅ | 이미 컬럼에 있음 (`Chgcap`) |
| 병목 | Step 병합 시 while 루프 | Step 병합 시 for 루프 |

### 3.2 Rate Profile (`toyo_rate_Profile_data` / `pne_rate_Profile_data`)

| 항목 | Toyo | PNE |
|------|------|-----|
| 파일 접근 | `toyo_Profile_import()` 1번 | `pne_data()` 1번 |
| 용량 계산 | 벡터화됨 ✅ + 레거시 코드 (중복) | 이미 컬럼에 있음 |
| 특이사항 | 용량 계산 코드 2가지 방식 공존 | 단순 |

### 3.3 Chg/Dchg Profile (`toyo_chg/dchg_Profile_data` / `pne_chg/dchg_Profile_data`)

| 항목 | Toyo | PNE |
|------|------|-----|
| 파일 접근 | 1~2개 파일 로드 | 통합 파일에서 필터링 |
| dQ/dV 계산 | `diff()` + `rolling()` | `diff()` |
| 특이사항 | 다음 사이클 확인 로직 있음 | Step 병합 필요 |

---

## 4. 주요 최적화 포인트

### 4.1 공통 최적화

| 우선순위 | 항목 | 설명 | 예상 효과 |
|----------|------|------|-----------|
| ⭐⭐⭐⭐⭐ | **Toyo 파일 I/O 최소화** | 필요한 사이클만 직접 접근 | 폴더 로딩 시간 감소 |
| ⭐⭐⭐⭐ | **병렬 처리** | `ThreadPoolExecutor`로 여러 사이클 동시 로드 | 2~4배 속도 향상 |
| ⭐⭐⭐ | **레거시 코드 제거** | `toyo_rate_Profile_data`의 중복 용량 계산 제거 | 가독성/유지보수성 향상 |

### 4.2 Toyo 전용 최적화

```python
# 현재: while 루프로 Step 병합
while maxcon == 1:
    stepcyc = stepcyc + 1
    tempdata = toyo_Profile_import(raw_file_path, stepcyc)  # 파일 I/O 반복
    ...

# 개선안: 필요한 사이클 번호를 먼저 파악 후 병렬 로드
cycle_list = get_required_cycles(raw_file_path, inicycle)
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(toyo_Profile_import, [raw_file_path]*len(cycle_list), cycle_list))
```

### 4.3 PNE 전용 최적화

- 현재도 효율적인 구조 (통합 CSV 사용)
- Step 병합 시 `for` 루프 → `pd.concat()` 한 번으로 가능

---

## 5. DCIR 기능 분석

| 항목 | 상세 |
|------|------|
| 지원 장비 | **PNE 전용** (Toyo 미지원) |
| 데이터 함수 | `pne_dcir_Profile_data()` |
| 특징 | SOC별 OCV/CCV/DCIR 계산, 0.1s/1s/10s/20s DCIR |

---

## 6. 결론 및 권고

1. **Toyo 데이터 로딩이 주요 병목** - 개별 파일 구조로 인한 I/O 오버헤드
2. **병렬 처리 적용 권장** - 특히 `step_confirm_button`의 while 루프
3. **코드 정리 필요** - `toyo_rate_Profile_data`의 중복 용량 계산 코드 제거
4. **DCIR은 PNE 전용** - Toyo 대응 불필요 (장비 특성)

---

## 7. 버튼별 중복 코드 분석

### 7.1 공통 구조 (4개 버튼 동일)

`step_confirm_button`, `rate_confirm_button`, `chg_confirm_button`, `dchg_confirm_button` 모두 동일한 패턴:

```python
def XXX_confirm_button(self):
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🔵 공통 코드 (100% 동일) - 약 15줄
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    init_data = self._init_confirm_button(self.XXXConfirm)
    firstCrate, mincapacity, CycleNo = init_data['firstCrate'], ...
    smoothdegree, mincrate, dqscale, dvscale = init_data['smoothdegree'], ...
    all_data_folder, all_data_name = init_data['folders'], init_data['names']
    
    global writer
    writecolno, foldercount, chnlcount, cyccount = 0, 0, 0, 0
    
    writer, save_file_name = self._setup_file_writer()
    tab_no = 0
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🔵 폴더 순회 구조 (90% 동일) - 약 20줄
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    for i, cyclefolder in enumerate(all_data_folder):
        if os.path.isdir(cyclefolder):
            subfolder = [f.path for f in os.scandir(cyclefolder) if f.is_dir()]
            foldercountmax = len(all_data_folder)
            foldercount = foldercount + 1
            if self.CycProfile.isChecked():
                for FolderBase in subfolder:
                    chnlcount = chnlcount + 1
                    chnlcountmax = len(subfolder)
                    if "Pattern" not in FolderBase:
                        # 🔵 Figure 생성 (동일 구조)
                        fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(...)
                        tab, tab_layout, canvas, toolbar = self._create_plot_tab(fig, tab_no)
                        
                        # 🔵 사이클 순회 (동일 구조)
                        for CycNo in CycleNo:
                            cyccount = cyccount + 1
                            progressdata = progress(...)
                            self.progressBar.setValue(int(progressdata))
                            namelist = FolderBase.split("\\")
                            headername = namelist[-2] + ", " + namelist[-1] + ", " + str(CycNo) + "cy, "
                            lgnd = "%04d" % CycNo
                            
                            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                            # 🟡 차이점: 데이터 로딩 함수
                            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                            if not check_cycler(cyclefolder):
                                temp = toyo_XXX_Profile_data(...)  # 함수명 다름
                            else:
                                temp = pne_XXX_Profile_data(...)   # 함수명 다름
                            
                            # 🔵 레전드 처리 (동일)
                            if len(all_data_name) == 0:
                                temp_lgnd = ""
                            else:
                                temp_lgnd = all_data_name[i] + " " + lgnd
                            
                            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                            # 🟡 차이점: 그래프 그리기
                            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                            if hasattr(temp[1], "XXX"):  # 속성명 다름
                                if len(temp[1].XXX) > 2:
                                    self.capacitytext.setText(str(temp[0]))
                                    graph_XXX(...)  # 그래프 함수/파라미터 다름
```

### 7.2 중복/차이 비율

| 구분 | 코드 영역 | 중복률 | 비고 |
|------|-----------|--------|------|
| **초기화** | `_init_confirm_button()` ~ `_setup_file_writer()` | **100%** | 이미 함수화됨 ✅ |
| **폴더 순회** | `for cyclefolder` ~ `for FolderBase` | **95%** | 구조 동일, 변수명만 다름 |
| **사이클 순회** | `for CycNo` ~ `progress()` | **95%** | 구조 동일, 변수명만 다름 |
| **데이터 로딩** | `toyo_XXX / pne_XXX` 호출 | **50%** | 함수명/파라미터 다름 |
| **그래프 그리기** | `graph_XXX()` 호출 | **20%** | 완전히 다름 (기능 특화) |
| **엑셀 저장** | `to_excel()` 호출 | **70%** | 헤더만 다름 |

### 7.3 통합 가능한 영역

```
┌─────────────────────────────────────────────────────────────┐
│ 🟢 통합 가능 (공통 함수로 분리)                              │
├─────────────────────────────────────────────────────────────┤
│ • 초기화 블록 (이미 완료: _init_confirm_button)              │
│ • 파일 저장 설정 (이미 완료: _setup_file_writer)             │
│ • 폴더/채널/사이클 순회 로직                                 │
│ • Progress 업데이트                                         │
│ • 레전드 생성                                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 🟡 부분 통합 가능                                            │
├─────────────────────────────────────────────────────────────┤
│ • 데이터 로딩 (함수 포인터로 추상화 가능)                     │
│ • 엑셀 저장 (헤더 리스트만 파라미터화)                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 🔴 통합 불가 (기능별 특화)                                   │
├─────────────────────────────────────────────────────────────┤
│ • 그래프 그리기 로직 (축, 데이터, 스케일 완전히 다름)         │
│ • 데이터 유효성 검사 (hasattr 대상 속성 다름)                 │
└─────────────────────────────────────────────────────────────┘
```

### 7.4 리팩토링 제안

```python
# 제안: 공통 순회 로직을 제네릭 함수로 분리
def _process_profile_confirm(self, button, load_func_toyo, load_func_pne, 
                              graph_callback, attr_name, extra_params=None):
    """
    공통 Profile Confirm 처리 로직
    
    Args:
        button: 비활성화할 버튼 (self.StepConfirm 등)
        load_func_toyo: Toyo 데이터 로딩 함수
        load_func_pne: PNE 데이터 로딩 함수
        graph_callback: 그래프 그리기 콜백 함수
        attr_name: 데이터 속성명 ("stepchg", "rateProfile", "Profile")
        extra_params: 추가 파라미터 (smoothdegree 등)
    """
    init_data = self._init_confirm_button(button)
    ...
    for i, cyclefolder in enumerate(all_data_folder):
        ...
        for CycNo in CycleNo:
            ...
            if not check_cycler(cyclefolder):
                temp = load_func_toyo(FolderBase, CycNo, ...)
            else:
                temp = load_func_pne(FolderBase, CycNo, ...)
            
            if hasattr(temp[1], attr_name):
                graph_callback(temp, axes, ...)

# 사용 예시
def step_confirm_button(self):
    self._process_profile_confirm(
        button=self.StepConfirm,
        load_func_toyo=toyo_step_Profile_data,
        load_func_pne=pne_step_Profile_data,
        graph_callback=self._draw_step_graphs,
        attr_name="stepchg"
    )
```

**예상 효과**: 각 버튼 함수 ~150줄 → ~10줄로 축소, 유지보수성 대폭 향상
