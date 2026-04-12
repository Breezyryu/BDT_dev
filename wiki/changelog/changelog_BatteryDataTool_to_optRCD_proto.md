# BatteryDataTool 변경 내역서 (시간순)

> **비교 대상:**  
> - **기존 파일:** `BatteryDataTool.py` (14,711줄)  
> - **변경 파일:** `BatteryDataTool_optRCD_proto_.py` (17,942줄)  
> - **순증가:** +3,231줄  
> - **작성일:** 2026-03-04  
> - **정렬 기준:** Git 커밋 시간순 (oldest → newest)

---

## Phase 1. 초기 코드 및 주석 정리 (2026-02-09 ~ 02-10)

> `2f92362` 2026-02-09 — pandas _append 코드수정 및 문서  
> `b5045b9` 2026-02-10 — 주석 정리  
> `8734fc8` 2026-02-10 — profile 최적화

### 1.1 BatteryDataTool.py 초기 커밋 (14,718줄)
- `BatteryDataTool_260206_edit copy/BatteryDataTool.py` 최초 등록
- pandas `_append` deprecated 코드 수정

### 1.2 주석 정리 · profile 최적화
- 불필요한 주석 제거, 코드 정리 (4 ins / 7 del)
- PNE 파일 로딩 최적화: `dfs = []` 리스트에 append 후 1회 `pd.concat()` — 기존 순차 concat(temp → hasattr) 방식 개선

---

## Phase 2. 프로파일 기능 확장 (2026-02-10 ~ 02-11)

> `0b5da3e` ~ `fd43353` 2026-02-10 — 프로파일 사이클 최소값, 단일 사이클, 전체 통합, 범례  
> `40feff0` ~ `c4e835b` 2026-02-11 — 범례 색상, 전체통합 plot, 연속 프로파일 Toyo/PNE

### 2.1 프로파일 사이클 입력 개선
- 사이클 최소값 정의: 2 → 1로 변경
- 단일 사이클 입력 변경 처리 로직 추가
- 프로파일 전체 통합 추가 (전체통합 분기 및 UI 추가)

### 2.2 범례 · 색상 적용
- 프로파일 범례 수정 / 범례 라벨 재수정
- plot 범례 색상 적용: 채널별 고유색 매칭
- 전체통합 plot 로직 정비

### 2.3 연속 프로파일 Toyo 추가
- `toyo_Profile_continue_data()` 초기 구현: 연속 프로파일 Toyo 데이터 처리
- Toyo 연속 프로파일 기본 동작 구현

---

## Phase 3. PNE 최적화 · 코인셀 지원 (2026-02-11 ~ 02-12)

> `1356a95` 2026-02-11 — pne 사이클 서치 최적화  
> `fda7607` ~ `d690b19` 2026-02-12 — 코인셀 조건, UI 패턴수정, 디버깅

### 3.1 `pne_search_cycle()` 구조 개선
- 기존: 깊은 중첩(3레벨 이상 if문), 반복적 파일 파싱
- 변경: early return 패턴 적용, `str.replace().astype(int)` 벡터 연산, 변수명 명확화 (`save_end`, `file_index`)

### 3.2 코인셀/PNE21·22 단위 판별 통합: `is_micro_unit()`
- 기존: `('PNE21' in raw_file_path) or ('PNE22' in raw_file_path)` 형태로 16곳에서 개별 작성
- 변경: 전역 함수 `is_micro_unit(raw_file_path)` 도입 — PNE21/22 **또는** 코인셀 모드 시 True 반환
- `set_coincell_mode(enabled)` / `_coincell_mode` 전역 변수로 코인셀 체크박스 상태 관리
- 기존 16곳의 조건문을 `is_micro_unit()` 호출로 통일

### 3.3 UI 패턴수정 탭 정렬 · 코인셀 체크박스
- 패턴수정 탭 UI 정렬 개선 (a2e00f0, e5dc8a2)
- 코인셀 체크박스 UI 업데이트 완료 (f490e8d)
- UI 수정사항 원본(BatteryDataTool_UI.py/ui)에 반영 (b1e27b1)

---

## Phase 4. Toyo 연속 프로파일 대폭 개선 (2026-02-12)

> `b99b7c8` ~ `b11da68` 2026-02-12 — 시간 누적, 사이클 처리, OCV/CCV 추출

### 4.1 `toyo_Profile_continue_data()` 로직 재설계
- **시간 누적 보정** (b99b7c8): PassTime 리셋 시 음수 diff를 0으로 클리핑 후 누적합
- **사이클 처리** (bd388e9): 명시적 범위(inicycle ~ endcycle) 지원, 파일 경계 추적(`file_boundaries`)
- **방전 시 전류 부호 반전**: `signed_current` 처리로 SOC 정확도 개선

### 4.2 OCV/CCV 자동 추출 (168f58a, b11da68)
- rest→charge/discharge 전환점에서 **OCV** 추출
- load→rest 전환점에서 **CCV** 추출
- **CycfileSOC DataFrame**: capacity.log AccCap + 프로파일 OCV/CCV 결합
- 출력 컬럼 확장: `TimeSec`, `TimeMin`, `SOC`, `Vol`, `Curr`, `Crate`, `Temp`, `OCV`, `CCV`
- 반환값 변경: `[mincapacity, df]` → `[mincapacity, df, CycfileSOC]`

### 4.3 `toyo_build_cycle_map()` 신규 함수
- 논리 사이클 번호 → 원본 파일 번호 범위 매핑 자동 생성
- 연속(Continue) 프로파일 배치 로딩 시 논리 사이클↔파일 번호 자동 변환에 활용

---

## Phase 5. 그래프 테마 시스템 · 충방전 효율 수정 (2026-02-13)

> `e4ecfc4` 2026-02-13 — 배치파일 및 plot 테마 설정  
> `90e361a` ~ `fe47642` 2026-02-13 — 충방전 효율, 플랏 색/스타일 변경

### 5.1 THEME 딕셔너리 도입
- 기존 하드코딩된 그래프 스타일 값을 `THEME` 딕셔너리로 중앙 관리 체계로 전환
- 10색 컬러 팔레트 (`PALETTE`) 정의: Nature 계열 학술 색상 (`#3C5488`, `#E64B35`, `#00A087` 등)
- scatter 크기(`SCATTER_SIZE`=7), 투명도(`SCATTER_ALPHA`=0.55), 선 두께(`LINE_WIDTH`=1.4), 그리드 스타일 등 통합 관리
- 범례, DPI(150), 배경색(`FIG_FACECOLOR`=`#FFFFFF`, `AX_FACECOLOR`=`#FAFBFD`) 등 출력 품질 설정

### 5.2 matplotlib rcParams 전역 설정 강화
- 기존: `font.family`, `axes.unicode_minus` 2개만 설정
- 변경: 18개 이상의 rcParams 일괄 설정 (figure.facecolor, axes.facecolor, spines, grid, tick 등)
- 상단/우측 spine 제거 (`axes.spines.top`=False, `axes.spines.right`=False)
- 색상 순환(`axes.prop_cycle`)을 THEME PALETTE로 설정

### 5.3 개별 그래프 함수 테마 적용
- `graph_base_parameter()`: fontsize, grid 스타일을 THEME 참조로 변경
- `graph_cycle()` / `graph_cycle_empty()`: scatter 크기, alpha, edgecolor, zorder 등 THEME 적용 + `return sc` (scatter artist 반환) 추가
- `graph_step()`, `graph_continue()`, `graph_soc_continue()`, `graph_dcir()`, `graph_soc_dcir()`, `graph_profile()` 등: `linewidth`, `alpha` THEME 적용
- `graph_soc_set()`, `graph_soc_err()`, `graph_set_profile()`, `graph_default()`: 하드코딩 색상 → THEME PALETTE 색상으로 교체
- `graph_output_cycle()`: scatter artist를 `artists` 리스트로 수집하여 반환

### 5.4 Toyo 충방전 효율 계산 인덱스 보정 (90e361a)
- 기존: `Chg2 = Chg.shift(periods=-1)` 후 바로 효율 계산 → 병합 시 인덱스 불일치 가능
- 변경: Chg 인덱스와 Dchg 인덱스를 **위치(순서) 기반으로 재정렬**하여 매칭
  - 초기 부분 방전(매칭 충전 없음) 자동 제거
  - `_nmin = min(len(Chg), len(Dchg))` 기준 길이 맞춤

### 5.5 그림 저장 품질 향상
- `plt.savefig()` 호출에 `dpi=THEME['DPI']`, `facecolor`, `bbox_inches='tight'` 추가
- `output_para_fig()`, `output_fig()` 양쪽 모두 적용

---

## Phase 6. PNE → Toyo 패턴 변환기 (2026-02-19)

> `9b1d4c9` 2026-02-19 — 토요 패턴 변환 기능 (+520줄)

### 6.1 Toyo PATRN 파일 생성 (완전 신규, ~667줄)
- PNE MDB 데이터베이스에서 원시 패턴 데이터 읽기 (pyodbc)
- Toyo 충방전기 형식의 PATRN 파일 자동 생성
- 지원 스텝 타입: 충전(1), 방전(2), 휴지(3), OCV(4), 임피던스(5), 종료(6), 루프(8), 연장(9)
- LEFT+RIGHT 서브스텝을 543자 PATRN 데이터 라인으로 조합

### 6.2 생성 파일 목록
| 파일 | 내용 |
|------|------|
| `PATRN{N}.1` | 메인 패턴 파일 (cp949 인코딩) |
| `Patrn{N}.option` | 용량 옵션 파일 |
| `Patrn{N}.option2` | 라인 타입별 옵션 파일 |
| `Fld_Puls{N}.DIR` / `Fld_Thermo{N}.DIR` | 펄스/온도 방향 설정 |
| `THPTNNO.1` | 패턴 번호 인덱스 파일 |

### 6.3 헬퍼 메서드
| 메서드 | 기능 |
|--------|------|
| `_toyo_fmt_num()` | 숫자 포맷팅 (Toyo 형식) |
| `_toyo_substitute()` | 우측 정렬 필드 대입 |
| `_toyo_build_charge_left()` / `_toyo_build_dchg_right()` | 충전/방전 서브스텝 |
| `_toyo_build_rest_left/right()` | 휴지 좌/우측 생성 |
| `_toyo_build_loop()` / `_toyo_build_header/option/option2()` | 루프/헤더/옵션 |
| `_pne_steps_to_toyo_substeps()` | PNE Step DF → Toyo 서브스텝 변환 |
| `ptn_toyo_convert_button()` | 변환 실행 버튼 핸들러 |

---

## Phase 7. 사이클 Plot 가시성 개편 · 채널 컨트롤 (2026-02-20)

> `48da5f8` ~ `2a95086` 2026-02-20 — 약 20개 커밋, 총 1,000줄 이상 변경  
> cycle plot 수정 → 채널 오버레이 → 하이라이트/딤 → UI 간결화

### 7.1 Import · Backend 변경
- `matplotlib.cm`, `matplotlib.colors` import 추가 (그라데이션 컬러맵/컬러바 지원)
- matplotlib backend: `backend_qt5agg` → `backend_qtagg` (Qt6 네이티브)

### 7.2 X축 범위 로직 개선 (bc2debb)
- 기존: `xrangegap = ((xlimit >= 400) + (xlimit >= 800) * 2 + (xlimit >= 1200) * 4 + (xlimit >= 2000) * 2 + 1) * 50`
- 변경: `xrangegap = ((xlimit >= 400) + (xlimit >= 800) + (xlimit >= 1500) * 2 + (xlimit >= 3000) * 2 + (xlimit >= 6000) * 4 + 1) * 50`
- 3000/6000 사이클 이상의 장기 수명 데이터에 대한 X축 눈금 간격 최적화

### 7.3 범례/채널 컨트롤 시스템 (신규)
- **`LEGEND_THRESHOLD` 상수** (기본값 15): 초과 시 그라데이션+컬러바로 자동 전환
- **`_setup_legend()` 메서드**: 15개 이하 기존 범례 / 16개 이상 컬러맵 그라데이션 + 컬러바

### 7.4 `_create_cycle_channel_control()` — 채널 제어 오버레이 (완전 신규, ~300줄)
- 사이클 그래프용 **플로팅 오버레이 패널** 생성
- "▶ CH" 토글 버튼으로 활성화/비활성화
- 채널별 **체크박스**(표시/숨김) + **클릭**(하이라이트) 기능
- 하이라이트 시 미선택 채널을 DIM 처리 (DIM_COLOR=#CCCCCC, DIM_ALPHA=0.15)
- "전체 표시" / "전체 하이라이트" 일괄 제어 체크박스
- Legend ON/OFF 토글
- 서브 채널(sub_channel_map) 지원: 부모-자식 그룹 연동
- 다크/라이트 테마 자동 감지
- 부모 위젯 리사이즈 시 오버레이 자동 위치 조정 / 외부 클릭 시 자동 닫기

### 7.5 `_finalize_cycle_tab()` 메서드
- 기존 `_finalize_plot_tab()`을 Cycle 탭 전용으로 분리
- 채널 컨트롤 오버레이 자동 연결

### 7.6 UI 코드 간결화 — setupUi 리팩토링 (2a95086)
- **폰트 설정 통합**: 위젯마다 5~6줄 반복 → 탭 단위 `_ptn_font` 1회 선언 후 재사용
- **위젯 크기**: `setMinimumSize` + `setMaximumSize` 2줄 → `setFixedSize` 1줄로 통일
- 크기 상수 도입: `_GB_W`, `_GB_H`, `_LBL_SZ`, `_INP_SZ`, `_BTN_SZ`
- 레이아웃 spacing/margin/alignment 세밀 제어 추가

---

## Phase 8. PyBaMM 전기화학 시뮬레이션 통합 (2026-02-23)

> `d5503fa` 2026-02-23 08:42 — pybamm 추가 prototype (proto 파일 17,157줄 최초 등록)  
> `19dedcc` ~ `7282a16` 2026-02-23 — 총 11개 커밋으로 시뮬레이션 기능 완성

### 8.1 시뮬레이션 엔진: `run_pybamm_simulation()` (d5503fa, 19dedcc, d1cb9dd)
- `pybamm` optional import (`HAS_PYBAMM` 플래그)
- 지원 모델: SPM, SPMe, DFN (리튬이온 배터리)
- **한국어 UI 파라미터** → PyBaMM 내부 파라미터 자동 변환 (μm→m, °C→K)
- 실험 모드:
  - `ccv` — CC-CV 완전 충방전 사이클
  - `charge` / `discharge` — 사용자 정의 스텝 리스트
  - `custom` — 원시 PyBaMM Experiment 문법
  - `gitt` — GITT/HPPC 패턴 (pulse 전류, pulse 시간, rest 시간, 반복 횟수, 전압 하한)
- 초기 SOC: 충전=0.0, 방전=1.0, GITT=1.0, custom=0.5 자동 설정 또는 수동 지정
- 출력 주기(output period) 설정 가능

### 8.2 PyBaMM 전용 탭 UI (~517줄) (d5503fa, a65a7b3, 7282a16)
- **왼쪽 입력 패널** (스크롤, 360px):
  - 모델 선택 ComboBox (SPM/SPMe/DFN)
  - 전극 파라미터 GroupBox: 프리셋 ComboBox 10종 + 토글형 파라미터 테이블 (14행)
  - 충방전 패턴 설정 (4가지 모드): Charge / Discharge / GITT·HPPC / Custom
  - 각 모드별 스텝 리스트 (CC/CV/CCCV/Rest) + 추가/편집/삭제/초기화 버튼
  - 초기 SOC, Output Period 입력
  - 실행(Run) / 초기화(Reset) 버튼
- **오른쪽 결과 패널**: 닫기 가능한 QTabWidget (다중 실행 결과 누적)

### 8.3 실행 핸들러: `pybamm_run_button()` (8993347, d1cb9dd)
- UI 파라미터 수집 → experiment config 빌드 → `run_pybamm_simulation()` 호출
- 결과 변수 30여 개 안전 추출 (`_safe()` 헬퍼: 2D→1D 평균, 누락 변수 처리)
- **일반 Plot 탭** (2×3): Cell Voltage & Current, V-Q Curve, Electrode Thermodynamics, Electrode SOC, Cell Temperature, Heat Generation Sources
- **상세 Plot 탭** (2×3): Overpotential Breakdown, Solid-Phase Diffusion, Electrolyte Concentration, Electrolyte Potential, Interfacial Current Density, Lithium Plating Risk

### 8.4 프리셋 시스템 (67f2eb7)
- 10종 프리셋 파라미터 세트 + 매칭 충방전 패턴 자동 로드
- Chen2020, Ai2020, Ecker2015, Marquis2019, Mohtat2020, NCA_Kim2011, OKane2022, ORegan2022, Prada2013, Ramadass2004

### 8.5 충방전 패턴 UI 개선 (9a967e6, bde4021, 31b597b)
- Time step 입력 기능 추가
- 충방전 패턴 선택항목 순서 수정
- 충방전 패턴 리스트 추가/편집 로직 개선

### 8.6 시그널 연결 · 키보드 단축키
- 모드 라디오 버튼 → 스택 페이지 전환
- 프리셋 콤보 → `_pybamm_load_preset()`
- 스텝 리스트 키보드 단축키: Ctrl+C/V (복사/붙여넣기), Delete (삭제)
- `HAS_PYBAMM=False` 시 실행 비활성화 + 경고 표시

### 8.7 보조 메서드
| 메서드 | 기능 |
|--------|------|
| `_pybamm_close_run_tab()` | 개별 실행 탭 닫기 |
| `pybamm_tab_reset_button()` | 전체 초기화 |
| `_pybamm_toggle_param_table()` | 파라미터 테이블 접기/펼치기 |
| `_pybamm_insert_step()` | 스텝 삽입 (선택 후 insert) |
| `_pybamm_update_step_fields()` | 스텝 타입별 필드 라벨/기본값 동적 변경 |
| `_pybamm_parse_cutoff()` | 컷오프 파싱 (0.05C, C/50, 600s, 10m, 1h) |
| `_pybamm_chg_add_step()` / `_pybamm_dchg_add_step()` | 충전/방전 스텝 추가 |
| `_pybamm_copy_steps()` / `_pybamm_paste_steps()` | 클립보드 복사/붙여넣기 |
| `_pybamm_load_step_to_fields()` | 더블클릭 → 입력 필드 역파싱 |
| `_pybamm_edit_step()` | 선택 스텝 교체 |

---

## Phase 9. 배치 프로파일 로딩 확장 · 최종 정리 (2026-03-04)

> `b6cd08b` 2026-03-04 — 프로토 변경 및 시뮬레이션 변수 정리 (+699 / -161)  
> `380481d` 2026-03-04 — 날짜 업데이트  
> `ff6f678` 2026-03-04 — SOP, 따옴표 경로 인식

### 9.1 배치 프로파일 로딩 함수 추가

#### Toyo 배치 함수
| 함수명 | 기능 |
|--------|------|
| `toyo_rate_Profile_batch()` | Rate 프로파일 배치 로딩 (min_cap 1회 산정) |
| `toyo_chg_Profile_batch()` | 충전 프로파일 배치 로딩 |
| `toyo_dchg_Profile_batch()` | 방전 프로파일 배치 로딩 |
| `toyo_continue_Profile_batch()` | Continue 프로파일 배치 로딩 (논리 사이클 → 파일 번호 자동 변환) |

#### PNE 배치 함수
| 함수명 | 기능 |
|--------|------|
| `pne_rate_Profile_batch()` | Rate 프로파일: SaveData 1회 로딩 후 사이클별 분배 |
| `pne_chg_Profile_batch()` | 충전 프로파일: SaveData 1회 로딩 후 사이클별 분배 |
| `pne_dchg_Profile_batch()` | 방전 프로파일: SaveData 1회 로딩 후 사이클별 분배 |
| `pne_continue_Profile_batch()` | Continue 프로파일: min_cap 1회 산정 후 반복 |

### 9.2 공통 헬퍼: `_pne_load_profile_raw()`
- PNE SaveData 파일을 일괄 로딩하는 배치 공통 헬퍼 (~60줄)
- min_cycle ~ max_cycle 범위의 원시 데이터를 **1회 디스크 I/O**로 취득
- `is_micro_unit()` 기반 μA 단위 판별 포함

### 9.3 병렬 프로파일 로딩 프레임워크
- `_load_profile_batch_task()`: ThreadPoolExecutor 워커, 4가지 프로파일 타입(rate/chg/dchg/continue) 처리
- `_load_all_profile_data_parallel()`: 전체 데이터 폴더 스캔 → 작업 분배 → 스레드풀 수집 (max_workers=4)
- 기존 step 프로파일만 병렬 지원 → rate/chg/dchg/continue까지 확장

### 9.4 시뮬레이션 변수 정리 · 예외 훅
- `run_pybamm_simulation()` 결과 변수 추출 로직 정비
- `sys.excepthook = _exception_hook` 추가로 슬롯(slot) 내 예외 디버깅 강화

---

## 변경 타임라인 요약

| 날짜 | Phase | 주요 변경 | 커밋 수 |
|------|-------|----------|---------|
| 02-09 ~ 02-10 | 1 | 초기 코드, 주석 정리, profile 최적화 | 3 |
| 02-10 ~ 02-11 | 2 | 프로파일 사이클 입력, 범례, 전체통합, 연속 프로파일 | ~15 |
| 02-11 ~ 02-12 | 3 | PNE 서치 최적화, `is_micro_unit()`, 코인셀 UI | ~12 |
| 02-12 | 4 | Toyo 연속 프로파일 재설계, OCV/CCV 추출 | 7 |
| 02-13 | 5 | THEME 시스템, rcParams, 효율 인덱스 보정, 저장 품질 | 6 |
| 02-19 | 6 | PNE → Toyo 패턴 변환기 (+520줄) | 1 |
| 02-20 | 7 | 채널 컨트롤 오버레이, 범례 자동 전환, UI 간결화 | ~20 |
| 02-23 | 8 | PyBaMM 시뮬레이션 전체 통합 (~2,000줄) | 11 |
| 03-04 | 9 | 배치 프로파일 8종 추가, 병렬 로딩, 변수 정리 | 3 |

## 변경 규모 요약

| 카테고리 | 추가 줄 수 (약) | 비고 |
|----------|----------------|------|
| THEME + 그래프 스타일 | ~120 | 전역 + 함수 15개 수정 |
| is_micro_unit 통합 | ~15 | 16곳 조건문 대체 |
| Toyo Cycle 인덱스 보정 | ~50 | 효율 계산 정확도↑ |
| 배치 프로파일 함수 | ~500 | 8개 신규 함수 + 헬퍼 |
| Continue Profile 개선 | ~100 | OCV/CCV 추출, SOC 보정 |
| 채널 컨트롤 오버레이 | ~490 | 완전 신규 |
| UI setupUi 리팩토링 | -300 (감소) | 코드 간결화 |
| PyBaMM 시뮬레이션 | ~2,000 | 완전 신규 |
| PNE→Toyo 변환기 | ~667 | 완전 신규 |
| 기타 (저장, 예외 등) | ~20 | 품질 개선 |
| **합계** | **~3,231** | |
