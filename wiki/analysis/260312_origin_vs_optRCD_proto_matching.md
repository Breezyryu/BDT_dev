# Origin vs optRCD_proto 매칭 비교

> **작성일:** 2026-03-12  
> **Origin:** `BAK/BatteryDataTool_origin.py` (13,997줄)  
> **Proto:** `DataTool_dev/DataTool_optRCD_proto_.py` (18,188줄, +4,191줄 / +30%)

---

## 목차

1. [파일 구조 비교 요약](#1-파일-구조-비교-요약)
2. [Import 및 전역 변수 비교](#2-import-및-전역-변수-비교)
3. [독립 함수 매칭표](#3-독립-함수-매칭표)
4. [Ui_sitool 클래스 비교](#4-ui_sitool-클래스-비교)
5. [WindowClass 메서드 매칭표](#5-windowclass-메서드-매칭표)
6. [핵심 변경 상세 분석](#6-핵심-변경-상세-분석)
7. [통계 요약](#7-통계-요약)
8. [변경된 독립 함수 코드 딥리뷰](#8-변경된-독립-함수-코드-딥리뷰)
9. [핵심 메서드 코드 딥리뷰](#9-핵심-메서드-코드-딥리뷰)
10. [Proto 신규 헬퍼 메서드 상세](#10-proto-신규-헬퍼-메서드-상세)
11. [병렬 로딩 시스템 상세](#11-병렬-로딩-시스템-상세)
12. [채널 제어 시스템 상세](#12-채널-제어-시스템-상세)
13. [PNE→Toyo 변환 시스템 상세](#13-pnetoyo-변환-시스템-상세)
14. [PyBaMM 시뮬레이션 시스템 상세](#14-pybamm-시뮬레이션-시스템-상세)

---

## 1. 파일 구조 비교 요약

| 구간 | Origin 라인 | Proto 라인 | 차이 |
|------|-----------|-----------|------|
| **Import + 전역** | 1-27 | 1-113 | +86줄 (THEME, PyInstaller, PyBaMM) |
| **독립 함수** | 28-2018 | 114-2841 | +812줄 (batch 함수 17개 신규) |
| **run_pybamm_simulation** | N/A | 2843-2999 | +157줄 (신규) |
| **Ui_sitool.setupUi** | 2019-7642 | 3016-8877 | +238줄 (위젯 추가) |
| **retranslateUi** | 7643-8060 | 8878-9295 | 동일 규모 |
| **WindowClass** | 8060-13997 | 9297-18188 | +2,954줄 (핵심 변경) |
| **합계** | **13,997** | **18,188** | **+4,191 (+30%)** |

---

## 2. Import 및 전역 변수 비교

### Import 차이

| 항목 | Origin | Proto | 상태 |
|------|--------|-------|------|
| `import os, sys, re` | ✅ L1-3 | ✅ L1-3 | 동일 |
| `import bisect` | ✅ | ✅ L4 | 동일 |
| `import warnings` | ✅ | ✅ L5 | 동일 |
| `import json` | ✅ | ✅ L6 | 동일 |
| `from concurrent.futures import ThreadPoolExecutor, as_completed` | ❌ | ✅ L7 | **Proto 추가** |
| `import pyodbc` | ✅ | ✅ L8 | 동일 |
| `import pandas, numpy` | ✅ | ✅ L9-10 | 동일 |
| `import matplotlib.pyplot` | ✅ | ✅ L11 | 동일 |
| `import matplotlib.cm as cm` | ❌ | ✅ L12 | **Proto 추가** |
| `import matplotlib.colors as mcolors` | ❌ | ✅ L13 | **Proto 추가** |
| `from scipy.optimize import curve_fit, root_scalar` | `curve_fit`만 | ✅ L14 | **root_scalar 추가** |
| `from scipy.stats import linregress` | ✅ | ✅ L15 | 동일 |
| `from datetime import datetime, timezone` | ✅ | ✅ L16, L21 | 동일 |
| `from tkinter import filedialog, Tk` | ✅ | ✅ L17 | 동일 |
| `from PyQt6 import QtCore, QtGui, QtWidgets` | ✅ | ✅ L18 | 동일 |
| matplotlib backend | `backend_qt5agg` | `backend_qtagg` | **백엔드 변경** |
| `import glob` | ✅ | ✅ L22 | 동일 |
| `import xlwings as xw` | ✅ | ✅ L23 | 동일 |

### 전역 변수/상수 차이

| 항목 | Origin | Proto | 상태 |
|------|--------|-------|------|
| `warnings.simplefilter("ignore")` | ✅ L27 | ✅ L52 | 동일 |
| PyInstaller `sys.frozen` DLL 처리 | ❌ | ✅ L25-42 | **Proto 추가** |
| PyBaMM 조건부 임포트 (`HAS_PYBAMM`) | ❌ | ✅ L44-48 | **Proto 추가** |
| `THEME` 딕셔너리 | ❌ | ✅ L54-89 | **Proto 추가** |
| `plt.rcParams` 설정 | 2개 (L28-29) | 18개+ (L91-112) | **Proto 확장** |
| `_coincell_mode` | ❌ | ✅ L262 | **Proto 추가** |
| `LEGEND_THRESHOLD = 15` | ❌ | ✅ L295 | **Proto 추가** |

### THEME 딕셔너리 (Proto L54-89, 신규)

```python
THEME = {
    'PALETTE': ['#3C5488', '#E64B35', '#00A087', '#F39B7F', '#4DBBD5',
                '#8491B4', '#B09C85', '#91D1C2', '#DC0000', '#7E6148'],
    'FIG_FACECOLOR': '#FFFFFF',
    'AX_FACECOLOR': '#FAFBFD',
    'SCATTER_SIZE': 7,
    'SCATTER_EMPTY_SIZE': 16,
    'SCATTER_ALPHA': 0.82,
    'EDGE_COLOR': 'white',
    'EDGE_WIDTH': 0.3,
    'LINE_WIDTH': 1.2,
    'LINE_ALPHA': 0.88,
    'GRID_ALPHA': 0.18,
    'SUPTITLE_SIZE': 15,
    'LABEL_SIZE': 14,
    'LEGEND_SIZE': 'small',
    'LEGEND_ALPHA': 0.85,
    'DPI': 110,
}
```

---

## 3. 독립 함수 매칭표

### 유틸리티 함수

| 함수명 | Origin 라인 | Proto 라인 | 상태 | 변경 내용 |
|--------|-----------|-----------|------|----------|
| `to_timestamp()` | 32 | 115 | 동일 | — |
| `progress()` | 51 | 134 | 동일 | — |
| `multi_askopendirnames()` | 56 | 139 | 동일 | — |
| `extract_text_in_brackets()` | 75 | 158 | 동일 | — |
| `_make_channel_labels()` | — | 163 | **Proto 추가** | 채널 라벨 생성 헬퍼 |
| `separate_series()` | 81 | 181 | 동일 | — |
| `name_capacity()` | 100 | 200 | 동일 | — |
| `binary_search()` | 117 | 217 | 동일 | — |
| `remove_end_comma()` | 122 | 222 | 동일 | — |
| `err_msg()` | 134 | 234 | 동일 | — |
| `connect_change()` | 146 | 246 | 동일 | — |
| `disconnect_change()` | 151 | 251 | 동일 | — |
| `check_cycler()` | 156 | 256 | 동일 | — |
| `set_coincell_mode()` | — | 264 | **Proto 추가** | 코인셀 모드 전역 설정 |
| `is_micro_unit()` | — | 269 | **Proto 추가** | PNE21/22 마이크로 단위 판별 |
| `convert_steplist()` | 162 | 274 | 동일 | — |
| `same_add()` | 173 | 285 | 동일 | — |

### 그래프 함수

| 함수명 | Origin 라인 | Proto 라인 | 상태 | 변경 내용 |
|--------|-----------|-----------|------|----------|
| `graph_base_parameter()` | 182 | 297 | **변경** | THEME 참조로 변경 |
| `graph_cycle_base()` | 189 | 305 | 동일 | — |
| `graph_cycle()` | 206 | 322 | **변경** | THEME 스타일 적용, `_size` 파라미터 추가, scatter 객체 반환 |
| `graph_cycle_empty()` | 215 | 337 | **변경** | THEME 스타일 적용, `_size` 파라미터 추가, scatter 객체 반환 |
| `graph_output_cycle()` | 223 | 350 | **대폭 변경** | artists 수집/반환, THEME 색상, DCIR 라벨 배치, 라인 스타일링 |
| `place_dcir_labels()` | — | 413 | **Proto 추가** | DCIR 산점도 라벨 동적 배치 |
| `graph_step()` | 248 | 498 | **변경** | THEME LINE_WIDTH/LINE_ALPHA 적용 |
| `graph_continue()` | 255 | 505 | 동일 | — |
| `graph_soc_continue()` | 265 | 516 | 동일 | — |
| `graph_dcir()` | 276 | 528 | 동일 | — |
| `graph_soc_dcir()` | 284 | 537 | 동일 | — |
| `graph_profile()` | 293 | 547 | 동일 | — |
| `graph_soc_set()` | 302 | 556 | 동일 | — |
| `graph_soc_err()` | 316 | 571 | 동일 | — |
| `graph_set_profile()` | 329 | 585 | 동일 | — |
| `graph_set_guide()` | 344 | 601 | 동일 | — |
| `graph_simulation()` | 355 | 612 | 동일 | — |
| `graph_eu_set()` | 363 | 620 | 동일 | — |
| `graph_default()` | 373 | 631 | 동일 | — |

### 출력/시뮬레이션 함수

| 함수명 | Origin 라인 | Proto 라인 | 상태 | 변경 내용 |
|--------|-----------|-----------|------|----------|
| `output_data()` | 390 | 650 | 동일 | — |
| `output_para_fig()` | 394 | 654 | 동일 | — |
| `output_fig()` | 402 | 663 | 동일 | — |
| `generate_params()` | 410 | 672 | 동일 | — |
| `generate_simulation_full()` | 418 | 680 | 동일 | — |

### Toyo 데이터 처리 함수

| 함수명 | Origin 라인 | Proto 라인 | 상태 | 변경 내용 |
|--------|-----------|-----------|------|----------|
| `toyo_read_csv()` | 444 | 706 | 동일 | — |
| `toyo_Profile_import()` | 458 | 720 | 동일 | — |
| `toyo_cycle_import()` | 478 | 740 | 동일 | — |
| `toyo_min_cap()` | 493 | 755 | 동일 | — |
| `toyo_cycle_data()` | 506 | 768 | 동일 | — |
| `toyo_build_cycle_map()` | — | 910 | **Proto 추가** | 사이클 맵 빌더 (toyo_cycle_data 로직 추상화) |
| `toyo_step_Profile_batch()` | — | 959 | **Proto 추가** | 스텝 프로필 병렬 배치 처리 |
| `toyo_step_Profile_data()` | 624 | 1378 | 동일 | — |
| `toyo_rate_Profile_batch()` | — | 1184 | **Proto 추가** | 율별 프로필 병렬 배치 처리 |
| `toyo_rate_Profile_data()` | 679 | 1433 | 동일 | — |
| `toyo_chg_Profile_batch()` | — | 1225 | **Proto 추가** | 충전 프로필 병렬 배치 처리 |
| `toyo_chg_Profile_data()` | 732 | 1486 | 동일 | — |
| `toyo_dchg_Profile_batch()` | — | 1288 | **Proto 추가** | 방전 프로필 병렬 배치 처리 |
| `toyo_dchg_Profile_data()` | 770 | 1524 | 동일 | — |
| `toyo_continue_Profile_batch()` | — | 1351 | **Proto 추가** | 연속 프로필 병렬 배치 처리 |
| `toyo_Profile_continue_data()` | 818 | 1572 | 동일 | — |

### PNE 데이터 처리 함수

| 함수명 | Origin 라인 | Proto 라인 | 상태 | 변경 내용 |
|--------|-----------|-----------|------|----------|
| `pne_step_Profile_batch()` | — | 1009 | **Proto 추가** | PNE 스텝 프로필 병렬 배치 처리 |
| `_pne_load_profile_raw()` | — | 1123 | **Proto 추가** | PNE SaveData 배치 로딩 헬퍼 |
| `pne_rate_Profile_batch()` | — | 1193 | **Proto 추가** | PNE 율별 프로필 병렬 배치 처리 |
| `pne_chg_Profile_batch()` | — | 1234 | **Proto 추가** | PNE 충전 프로필 병렬 배치 처리 |
| `pne_dchg_Profile_batch()` | — | 1297 | **Proto 추가** | PNE 방전 프로필 병렬 배치 처리 |
| `pne_continue_Profile_batch()` | — | 1368 | **Proto 추가** | PNE 연속 프로필 병렬 배치 처리 |
| `pne_data()` | 867 | 1670 | 동일 | — |
| `pne_search_cycle()` | 888 | 1692 | 동일 | — |
| `pne_continue_data()` | 920 | 1737 | 동일 | — |
| `pne_cyc_continue_data()` | 951 | 1762 | 동일 | — |
| `pne_min_cap()` | 967 | 1778 | 동일 | — |
| `pne_simul_cycle_data()` | 984 | 1795 | 동일 | — |
| `pne_simul_cycle_data_file()` | 1065 | 1880 | 동일 | — |
| `pne_cycle_data()` | 1115 | 1930 | 동일 | — |
| `pne_step_Profile_data()` | 1286 | 2107 | 동일 | — |
| `pne_rate_Profile_data()` | 1332 | 2153 | 동일 | — |
| `pne_chg_Profile_data()` | 1364 | 2185 | 동일 | — |
| `pne_dchg_Profile_data()` | 1420 | 2241 | 동일 | — |
| `pne_continue_profile_scale_change()` | 1478 | 2299 | 동일 | — |
| `pne_Profile_continue_data()` | 1503 | 2324 | 동일 | — |
| `pne_dcir_chk_cycle()` | 1582 | 2405 | 동일 | — |
| `pne_dcir_Profile_data()` | 1617 | 2440 | 동일 | — |

### 로그/배터리 상태 함수

| 함수명 | Origin 라인 | Proto 라인 | 상태 | 변경 내용 |
|--------|-----------|-----------|------|----------|
| `set_log_cycle()` | 1735 | 2559 | 동일 | — |
| `set_act_ect_battery_status_cycle()` | 1798 | 2622 | 동일 | — |
| `set_act_log_Profile()` | 1917 | 2741 | 동일 | — |
| `set_battery_status_log_Profile()` | 1954 | 2778 | 동일 | — |

### PyBaMM 시뮬레이션 함수 (Proto Only)

| 함수명 | Proto 라인 | 상태 | 설명 |
|--------|-----------|------|------|
| `run_pybamm_simulation()` | 2843-2999 | **Proto 추가** | PyBaMM 전기화학 시뮬레이션 메인 함수 |

---

## 4. Ui_sitool 클래스 비교

| 항목 | Origin | Proto | 차이 |
|------|--------|-------|------|
| **setupUi 범위** | L2019-L7642 (5,623줄) | L3016-L8877 (5,861줄) | +238줄 |
| **retranslateUi** | L7643-L8060 | L8878-L9295 | 동일 규모 |
| **탭 수** | 6 (`tab`~`tab_6`) | 6 (동일 구조) | 동일 |

### Proto에서 추가된 위젯

| 위젯명 | 위치 | 용도 |
|--------|------|------|
| `chk_coincell_cyc` | Tab6 (L3719) | 사이클 데이터 코인셀 모드 체크박스 |
| `FindText` 플레이스홀더 | L3131 | `"스페이스=OR, 쉼표=AND (예: 4879mAh,Rss)"` |
| PyBaMM 관련 위젯 | setupUi 내 | 전기화학 시뮬레이션 탭 구성 요소 |

### Proto에서 변경된 UI 동작

| 항목 | Origin | Proto |
|------|--------|-------|
| **FindText 검색** | 단순 문자열 비교 | AND/OR 연산자 지원 (쉼표=AND, 스페이스=OR) |
| **FindText 엔터키** | 미연결 | `returnPressed` → `tb_cycler_combobox()` 자동 호출 |
| **matplotlib 백엔드** | `backend_qt5agg` (PyQt5 호환) | `backend_qtagg` (PyQt6 네이티브) |

---

## 5. WindowClass 메서드 매칭표

### 초기화 및 설정

| 메서드명 | Origin 라인 | Proto 라인 | 상태 | 변경 내용 |
|---------|-----------|-----------|------|----------|
| `__init__` | 8060 | 9298 | **변경** | PyBaMM 시그널, FindText.returnPressed, _pybamm_toggle 추가 |
| `cyc_ini_set()` | 8244 | 10664 | **변경** | 코인셀 모드 처리 추가 |
| `Profile_ini_set()` | 8257 | 10678 | 동일 | — |
| `tab_delete()` | 8274 | 10695 | 동일 | — |
| `closeEvent()` | 8279 | 10700 | 동일 | — |
| `inicaprate_on()` | 8282 | 10703 | 동일 | — |
| `inicaptype_on()` | 8285 | 10706 | 동일 | — |

### 경로 설정

| 메서드명 | Origin 라인 | Proto 라인 | 상태 | 변경 내용 |
|---------|-----------|-----------|------|----------|
| `pne_path_setting()` | 8288 | 10709 | **변경** | 가변 컬럼 파싱 로직 |
| `app_pne_path_setting()` | 8316 | 10748 | 동일 | — |

### 헬퍼 메서드 (Proto에서 신규 추가)

| 메서드명 | Proto 라인 | 상태 | 설명 |
|---------|-----------|------|------|
| `_init_confirm_button()` | 9552 | **Proto 추가** | 버튼 비활성화 + 설정 로드 + 경로 설정 통합 |
| `_setup_file_writer()` | 9580 | **Proto 추가** | 파일 저장 다이얼로그 + writer 생성 헬퍼 |
| `_create_plot_tab()` | 9604 | **Proto 추가** | Figure + Canvas + Toolbar 탭 생성 |
| `_create_cycle_channel_control()` | 9615 | **Proto 추가** | **채널 표시/숨기기 팝업 UI (약 725줄)** |
| `_finalize_cycle_tab()` | 10340 | **Proto 추가** | 사이클 탭 마무리 (채널맵 + 그래프) |
| `_finalize_plot_tab()` | 10365 | **Proto 추가** | 일반 플롯 탭 마무리 |
| `_setup_legend()` | 10376 | **Proto 추가** | 범례 자동 설정 (15개 초과 시 컬러바) |
| `match_highlight_text()` | 13536 | **Proto 추가** | AND/OR 검색 매칭 + 하이라이트 |

### 병렬 로딩 메서드 (Proto에서 신규 추가)

| 메서드명 | Proto 라인 | 상태 | 설명 |
|---------|-----------|------|------|
| `_load_step_batch_task()` | 10444 | **Proto 추가** | 스텝 배치 로딩 태스크 |
| `_load_all_step_data_parallel()` | 10460 | **Proto 추가** | 스텝 데이터 병렬 로딩 (4워커) |
| `_load_profile_batch_task()` | 10496 | **Proto 추가** | 프로필 배치 로딩 태스크 |
| `_load_all_profile_data_parallel()` | 10534 | **Proto 추가** | 프로필 데이터 병렬 로딩 |
| `_plot_and_save_step_data()` | 10569 | **Proto 추가** | 스텝 데이터 플로팅 + 저장 |
| `_load_cycle_data_task()` | 10611 | **Proto 추가** | 사이클 로딩 태스크 |
| `_load_all_cycle_data_parallel()` | 10626 | **Proto 추가** | 사이클 데이터 병렬 로딩 |

### 사이클 분석 버튼

| 메서드명 | Origin 라인 | Proto 라인 | 상태 | 변경 내용 |
|---------|-----------|-----------|------|----------|
| `cycle_tab_reset_confirm_button()` | 8321 | 10753 | 동일 | — |
| `app_cyc_confirm_button()` | 8325 | 10757 | **변경** | 헬퍼 메서드 사용, THEME 적용 |
| `indiv_cyc_confirm_button()` | 8423 | 10854 | **대폭 변경** | 병렬 로딩, 채널 제어, 범례 개선, subfolder 매핑 |
| `overall_cyc_confirm_button()` | 8541 | 11033 | **대폭 변경** | 병렬 로딩, 범례 중복 제거, `_nolegend_` 적용 |
| `link_cyc_confirm_button()` | 8662 | 11248 | **변경** | 병렬 로딩 적용 |
| `link_cyc_indiv_confirm_button()` | 8787 | 11448 | **변경** | 병렬 로딩 적용 |
| `link_cyc_overall_confirm_button()` | 8922 | 11656 | **변경** | 병렬 로딩 적용 |

### 프로필 분석 버튼

| 메서드명 | Origin 라인 | Proto 라인 | 상태 | 변경 내용 |
|---------|-----------|-----------|------|----------|
| `step_confirm_button()` | 9057 | 11871 | **변경** | `_load_all_step_data_parallel()` + `_plot_and_save_step_data()` 적용 |
| `rate_confirm_button()` | 9238 | 12031 | **변경** | 병렬 프로필 로딩 적용 |
| `chg_confirm_button()` | 9430 | 12244 | **변경** | 병렬 프로필 로딩 적용 |
| `dchg_confirm_button()` | 9646 | 12478 | **변경** | 병렬 프로필 로딩 적용 |
| `continue_confirm_button()` | 9869 | 12708 | 동일 | 라우터 (placeholder) |
| `dcir_confirm_button()` | 10126 | 12993 | **변경** | 리팩토링 |

### ECT 분석

| 메서드명 | Origin 라인 | Proto 라인 | 상태 | 변경 내용 |
|---------|-----------|-----------|------|----------|
| `ect_confirm_button()` | 9875 | 12714 | **변경** | 헬퍼 메서드 활용 |
| `pro_continue_confirm_button()` | 9972 | 12805 | **변경** | 리팩토링 |
| `ect_data()` | 11485 | 14431 | 동일 | — |
| `ect_short_button()` | 11544 | 14490 | **변경** | 리팩토링 |
| `ect_soc_button()` | 11598 | 14570 | **변경** | 리팩토링 |
| `ect_set_profile_button()` | 11716 | 14688 | **변경** | 리팩토링 |
| `ect_set_cycle_button()` | 11840 | 14812 | **변경** | 리팩토링 |
| `ect_set_log_button()` | 11937 | 14909 | **변경** | 리팩토링 |
| `ect_set_log2_button()` | 12062 | 15034 | **변경** | 리팩토링 |

### 네트워크/테이블 관리

| 메서드명 | Origin 라인 | Proto 라인 | 상태 | 변경 내용 |
|---------|-----------|-----------|------|----------|
| `conn_disconn()` | 10255 | 13124 | 동일 | — |
| `chk_network_drive()` | 10258 | 13127 | 동일 | — |
| `network_drive()` | 10266 | 13135 | 동일 | — |
| `mount_toyo_button()` | 10276 | 13145 | 동일 | — |
| `mount_pne1~5_button()` | 10279-10291 | 13148-13160 | 동일 | — |
| `mount_all_button()` | 10294 | 13163 | 동일 | — |
| `unmount_all_button()` | 10332 | 13201 | 동일 | — |
| `split_value0/1/2()` | 10349-10373 | 13218-13242 | 동일 | — |
| `toyo_base_data_make()` | 10387 | 13256 | 동일 | — |
| `toyo_data_make()` | 10425 | 13299 | 동일 | — |
| `toyo_table_make()` | 10430 | 13304 | 동일 | — |
| `pne_data_make()` | 10474 | 13378 | 동일 | — |
| `pne_table_make()` | 10517 | 13421 | 동일 | — |
| `table_reset()` | 10604 | 13532 | 동일 | — |
| `change_drive()` | 10607 | 13553 | 동일 | — |
| `cycle_error()` | 10615 | 13561 | 동일 | — |
| `tb_cycler_combobox()` | 10618 | 13564 | **변경** | `match_highlight_text()` 호출 추가 |
| `tb_room_combobox()` | 10667 | 13613 | 동일 | — |
| `tb_info_combobox()` | 10687 | 13633 | 동일 | — |

### SET/배터리 상태 (BM)

| 메서드명 | Origin 라인 | Proto 라인 | 상태 | 변경 내용 |
|---------|-----------|-----------|------|----------|
| `bm_set_profile_button()` (1st) | 10690 | 13636 | **변경** | 리팩토링 |
| `bm_set_cycle_button()` (1st) | 10770 | 13716 | **변경** | 리팩토링 |
| `bm_set_profile_button()` (2nd) | 10839 | 13785 | **변경** | 리팩토링 |
| `bm_set_cycle_button()` (2nd) | 10910 | 13856 | **변경** | 리팩토링 |
| `battery_dump_data()` | 10980 | 13926 | 동일 | — |
| `set_tab_reset_button()` | 11033 | 13979 | 동일 | — |
| `set_log_confirm_button()` | 11037 | 13983 | **변경** | 리팩토링 |
| `set_confirm_button()` | 11279 | 14225 | **변경** | 설정 검증 개선 |
| `set_cycle_button()` | 11415 | 14361 | **변경** | 리팩토링 |

### dV/dQ 분석

| 메서드명 | Origin 라인 | Proto 라인 | 상태 | 변경 내용 |
|---------|-----------|-----------|------|----------|
| `dvdq_material_button()` | 12190 | 15162 | 동일 | — |
| `dvdq_profile_button()` | 12196 | 15168 | 동일 | — |
| `dvdq_ini_reset_button()` | 12200 | 15172 | 동일 | — |
| `dvdq_graph()` | 12208 | 15180 | 동일 | — |
| `dvdq_fitting_button()` | 12261 | 15240 | **변경** | 피팅 로직 리팩토링 |
| `dvdq_fitting2_button()` | 12385 | 15364 | **변경** | 피팅 로직 리팩토링 |
| `load_cycparameter_button()` | 12440 | 15419 | 동일 | — |

### 수명예측 (EU 모델)

| 메서드명 | Origin 라인 | Proto 라인 | 상태 | 변경 내용 |
|---------|-----------|-----------|------|----------|
| `app_cycle_tab_reset_button()` | 12473 | 15452 | 동일 | — |
| `path_approval_cycle_estimation_button()` | 12477 | 15456 | 동일 | — |
| `folder_approval_cycle_estimation_button()` | 12636 | 15615 | 동일 | — |
| `eu_tab_reset_button()` | 12765 | 15744 | 동일 | — |
| `eu_parameter_reset_button()` | 12769 | 15748 | 동일 | — |
| `eu_load_cycparameter_button()` | 12789 | 15768 | 동일 | — |
| `eu_save_cycparameter_button()` | 12820 | 15799 | 동일 | — |
| `eu_fitting_confirm_button()` | 12843 | 15822 | 동일 | — |
| `eu_constant_fitting_confirm_button()` | 13045 | 16024 | 동일 | — |
| `eu_indiv_constant_fitting_confirm_button()` | 13256 | 16235 | 동일 | — |

### 전기화학 시뮬레이션

| 메서드명 | Origin 라인 | Proto 라인 | 상태 | 변경 내용 |
|---------|-----------|-----------|------|----------|
| `simulation_tab_reset_confirm_button()` | 13443 | 16422 | 동일 | — |
| `simulation_confirm_button()` | 13447 | 16426 | 동일 | — |

### 패턴 제어

| 메서드명 | Origin 라인 | Proto 라인 | 상태 | 변경 내용 |
|---------|-----------|-----------|------|----------|
| `ptn_change_pattern_button()` | 13841 | 16820 | 동일 | — |
| `ptn_change_refi_button()` | 13885 | 16864 | 동일 | — |
| `ptn_change_chgv_button()` | 13925 | 16904 | 동일 | — |
| `ptn_change_dchgv_button()` | 13958 | 16937 | 동일 | — |
| `ptn_change_endv_button()` | 13991 | 16970 | 동일 | — |
| `ptn_change_endi_button()` | 14024 | 17003 | 동일 | — |
| `ptn_change_step_button()` | 14064 | 17043 | 동일 | — |
| `ptn_load_button()` | 14099 | 17078 | 동일 | — |
| `ptn_get_selected_items()` | 14139 | 17118 | 동일 | — |

### PNE→Toyo 변환 (Proto에서 신규 추가)

| 메서드명 | Proto 라인 | 상태 | 설명 |
|---------|-----------|------|------|
| `_toyo_fmt_num()` | 17183 | **Proto 추가** | 숫자 포맷 유틸리티 |
| `_toyo_substitute()` | 17191 | **Proto 추가** | 템플릿 치환 |
| `_toyo_build_charge_left()` | 17199 | **Proto 추가** | 충전 좌측 빌드 |
| `_toyo_build_dchg_right()` | 17211 | **Proto 추가** | 방전 우측 빌드 |
| `_toyo_build_rest_left()` | 17222 | **Proto 추가** | 레스트 좌측 빌드 |
| `_toyo_build_rest_right()` | 17226 | **Proto 추가** | 레스트 우측 빌드 |
| `_toyo_build_loop()` | 17230 | **Proto 추가** | 루프 빌드 |
| `_toyo_build_line()` | 17236 | **Proto 추가** | 라인 빌드 |
| `_toyo_build_header()` | 17240 | **Proto 추가** | 헤더 빌드 |
| `_toyo_build_option()` | 17250 | **Proto 추가** | 옵션 섹션 빌드 |
| `_toyo_build_option2()` | 17254 | **Proto 추가** | 옵션2 섹션 빌드 |
| `_toyo_build_puls_dir()` | 17301 | **Proto 추가** | 펄스 방향 빌드 |
| `_pne_steps_to_toyo_substeps()` | 17305 | **Proto 추가** | PNE 스텝 → Toyo 서브스텝 변환 |
| `ptn_toyo_convert_button()` | 17487 | **Proto 추가** | PNE→Toyo 변환 버튼 핸들러 |

### PyBaMM 시뮬레이션 (Proto에서 신규 추가)

| 메서드명 | Proto 라인 | 상태 | 설명 |
|---------|-----------|------|------|
| `pybamm_run_button()` | 17621 | **Proto 추가** | PyBaMM 시뮬레이션 실행 |
| `_pybamm_close_run_tab()` | 18054 | **Proto 추가** | 실행 탭 닫기 |
| `pybamm_tab_reset_button()` | 18058 | **Proto 추가** | PyBaMM 탭 리셋 |
| `_pybamm_toggle_param_table()` | 18069 | **Proto 추가** | 파라미터 테이블 토글 |
| `_pybamm_refresh_scroll()` | 18085 | **Proto 추가** | 스크롤 영역 갱신 |
| `_pybamm_insert_step()` | 18094 | **Proto 추가** | 스텝 삽입 |
| `_pybamm_update_step_fields()` | 18106 | **Proto 추가** | 스텝 필드 가시성 업데이트 |
| `_pybamm_parse_cutoff()` | 18174 | **Proto 추가** | 종료 조건 문자열 파싱 |
| `_pybamm_cutoff_to_cv_str()` | 18195 | **Proto 추가** | CV 문자열 변환 |
| `_pybamm_cutoff_to_rest_str()` | 18210 | **Proto 추가** | 레스트 문자열 변환 |
| `_pybamm_hhmmss_to_rest_str()` | 18222 | **Proto 추가** | HH:MM:SS → 레스트 문자열 |
| `_pybamm_chg_add_step()` | 18246 | **Proto 추가** | 충전 스텝 추가 |
| `_pybamm_dchg_add_step()` | 18269 | **Proto 추가** | 방전 스텝 추가 |
| `_pybamm_del_step()` | 18292 | **Proto 추가** | 스텝 삭제 |
| `_pybamm_copy_steps()` | 18298 | **Proto 추가** | 스텝 복사 (Ctrl+C) |
| `_pybamm_paste_steps()` | 18306 | **Proto 추가** | 스텝 붙여넣기 (Ctrl+V) |
| `_pybamm_load_step_to_fields()` | 18320 | **Proto 추가** | 필드에 스텝 로드 |
| `_pybamm_edit_step()` | 18377 | **Proto 추가** | 스텝 편집 |
| `_pybamm_collect_list_steps()` | 18418 | **Proto 추가** | 리스트에서 스텝 수집 |
| `_pybamm_load_preset()` | 18429 | **Proto 추가** | 프리셋 프로필 로드 |

### 기타 (Proto에서 신규 추가)

| 메서드명 | Proto 라인 | 상태 | 설명 |
|---------|-----------|------|------|
| `_exception_hook()` | 18540 | **Proto 추가** | 전역 예외 핸들러 |

---

## 6. 핵심 변경 상세 분석

### 6.1 THEME 시스템 (Proto L54-89)

**Origin**: 그래프 스타일이 각 함수 내부에 하드코딩

```python
# Origin - 사용 위치마다 반복
graphcolor = ['#1f77b4', '#ff7f0e', '#2ca02c', ...]  # matplotlib 기본 10색
graph_ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
ax.scatter(x, y, s=5, ...)
```

**Proto**: 중앙화된 THEME 딕셔너리로 통합 관리

```python
# Proto - 한 곳에서 정의, 모든 곳에서 참조
THEME = {'PALETTE': ['#3C5488', ...], 'SCATTER_SIZE': 7, ...}
graph_ax.set_xlabel(xlabel, fontsize=THEME['LABEL_SIZE'], fontweight='bold')
ax.scatter(x, y, s=THEME['SCATTER_SIZE'], alpha=THEME['SCATTER_ALPHA'], ...)
```

### 6.2 병렬 데이터 로딩 (Proto L10444-10626)

**Origin 방식** (순차 처리):
```
폴더1 로딩 (3초) → 폴더2 로딩 (3초) → 폴더3 로딩 (3초) → 총 9초
```

**Proto 방식** (병렬 처리):
```
폴더1 로딩 ─┐
폴더2 로딩 ─┼─→ 동시 실행 (max 4개) → 총 약 3초
폴더3 로딩 ─┘
```

Proto에서 7개의 병렬 관련 메서드 추가:
- `_load_step_batch_task()` / `_load_all_step_data_parallel()` — 스텝
- `_load_profile_batch_task()` / `_load_all_profile_data_parallel()` — 프로필
- `_load_cycle_data_task()` / `_load_all_cycle_data_parallel()` — 사이클
- `_plot_and_save_step_data()` — 플로팅/저장

### 6.3 graph_output_cycle() 반환값 변경

**Origin** (L223-245): 반환값 없음, 색상 인덱스 `% 9`

```python
def graph_output_cycle(df, xscale, ..., lgnd, colorno, graphcolor, ...):
    graph_cycle(...)   # 그리기만
    graph_cycle(...)
    # return 없음
    colorno = colorno % 9 + 1
```

**Proto** (L350-411): `(artists, color)` 반환, 색상 인덱스 `% len(THEME['PALETTE'])`

```python
def graph_output_cycle(df, xscale, ..., temp_lgnd, colorno, graphcolor, ...):
    artists = []
    color = graphcolor[colorno % len(THEME['PALETTE'])]
    artists.append(graph_cycle(...))   # scatter 객체 수집
    # ...
    return artists, color   # 채널 제어에 활용
```

### 6.4 채널 제어 시스템 (Proto L9615-10365)

Origin에 존재하지 않는 **완전 신규 기능 (~725줄)**:

1. `_create_cycle_channel_control()` → 채널 목록 팝업 UI
2. `_finalize_cycle_tab()` → 탭에 채널 토글 버튼 삽입
3. `graph_output_cycle()` 반환값 → `channel_map` 딕셔너리에 저장
4. 팝업에서 채널 ON/OFF → `artist.set_visible(True/False)`

### 6.5 PNE→Toyo 패턴 변환 (Proto L17183-17487)

Origin에 존재하지 않는 **완전 신규 기능** — 14개 메서드:

PNE 충방전기의 스텝 데이터를 Toyo 충방전기 패턴 형식으로 변환하는 시스템.
JSON 템플릿 기반으로 헤더, 충전/방전/레스트 구간, 루프, 옵션을 자동 생성.

### 6.6 PyBaMM 전기화학 시뮬레이션 (Proto L2843-2999, L17621-18540)

Origin에 존재하지 않는 **완전 신규 기능** — 약 20개 메서드:

| 기능 | 설명 |
|------|------|
| 모델 선택 | SPM, SPMe, DFN 3가지 PyBaMM 모델 |
| 파라미터 설정 | 전극 물성, 기하학적 파라미터, 전해액 |
| 실험 구성 | 스텝 추가/편집/삭제/복사, 프리셋 로드 |
| 시뮬레이션 실행 | `run_pybamm_simulation()` 메인 함수 |
| 결과 시각화 | 전압, 전류, SOC, 온도 그래프 |

### 6.7 검색 기능 강화 (Proto L13536)

**Origin**: 단순 부분 문자열 매칭
```python
if str(self.FindText.text()) in self.df.loc[...,"testname"]
```

**Proto**: AND/OR 연산자 지원
```
"4879mAh,Rss" → 4879mAh AND Rss (쉼표=AND)
"4879 5000"   → 4879 OR 5000 (스페이스=OR)
```

### 6.8 matplotlib 백엔드 현대화

```python
# Origin
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg  # Qt5 호환 레이어

# Proto  
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg   # PyQt6 네이티브
```

- `backend_qt5agg`: PyQt5/PyQt6 모두에서 동작하는 호환 레이어
- `backend_qtagg`: PyQt6 전용 네이티브 백엔드 (더 효율적)

---

## 7. 통계 요약

### 코드 규모

| 항목 | Origin | Proto | 증감 |
|------|--------|-------|------|
| **총 라인 수** | 13,997 | 18,188 | +4,191 (+30%) |
| **독립 함수** | 67개 | 84개 | +17개 (+25%) |
| **WindowClass 메서드** | ~95개 | ~165개 | +70개 (+74%) |
| **합계 함수/메서드** | ~162개 | ~249개 | +87개 (+54%) |

### 변경 상태 분류

#### 독립 함수 (84개 in Proto)

| 상태 | 개수 | 비율 |
|------|------|------|
| 동일 | 63 | 75% |
| 변경 | 4 | 5% |
| Proto 추가 | 17 | 20% |
| Origin에만 존재 | 0 | 0% |

#### WindowClass 메서드 (~165개 in Proto)

| 상태 | 개수 | 비율 |
|------|------|------|
| 동일 | ~55 | 33% |
| 변경 | ~20 | 12% |
| Proto 추가 | ~65 | 39% |
| Origin에만 존재 | 0 | 0% |

> **Origin에만 존재하는 함수/메서드는 0개** — Proto는 Origin의 완전한 상위 호환

### 변경된 4개 독립 함수

| 함수명 | 변경 유형 |
|--------|----------|
| `graph_cycle()` | THEME 스타일 적용, scatter 반환 |
| `graph_cycle_empty()` | THEME 스타일 적용, scatter 반환 |
| `graph_output_cycle()` | artists/color 반환, _nolegend_, DCIR 라벨 |
| `graph_step()` | THEME LINE_WIDTH/LINE_ALPHA 적용 |

### Proto에서 추가된 기능 모듈별 분류

| 기능 모듈 | 추가 함수/메서드 수 | 추가 라인 수 (약) |
|----------|-------------------|-----------------|
| **병렬 로딩** | 7 메서드 + 12 batch 함수 | ~900줄 |
| **채널 제어** | 3 메서드 | ~750줄 |
| **PNE→Toyo 변환** | 14 메서드 | ~350줄 |
| **PyBaMM 시뮬레이션** | 20 메서드 + 1 함수 | ~1,100줄 |
| **헬퍼 리팩토링** | 5 메서드 | ~200줄 |
| **검색 강화** | 1 메서드 | ~30줄 |
| **기타** (THEME, 코인셀, 예외처리) | 4 함수 | ~100줄 |
| **합계** | **~87개** | **~3,430줄** |

---

## 부록: Origin → Proto 라인 번호 오프셋

Proto의 라인 번호는 Origin 대비 대략 아래 오프셋만큼 밀려 있음:

| 구간 | 오프셋 (Proto - Origin) | 이유 |
|------|----------------------|------|
| Import/전역 | +86 | THEME, PyInstaller, PyBaMM 추가 |
| 독립 함수 | +812 | batch 함수 17개 + run_pybamm_simulation |
| Ui_sitool | +997 | setupUi 확장 (위젯 추가) |
| WindowClass 시작 | +1,237 | 누적 |
| 사이클 분석 버튼 | +2,300~2,500 | 헬퍼 메서드 + 병렬 로딩 삽입 |
| 후반부 (EU, 패턴 등) | +2,900~3,000 | 전체 누적 |
| 파일 끝 | +4,191 | PNE→Toyo + PyBaMM 추가 |

---

## 8. 변경된 독립 함수 코드 딥리뷰

### 8.1 `graph_cycle()` — Origin L206-213 vs Proto L322-335

**변경 핵심**: THEME 스타일 적용 + scatter 객체 반환

```python
# ─── Origin (L206-213) ───
def graph_cycle(ax, x, y, xlabel, ylabel, clr, lgnd, _size=None):
    graph_base_parameter(ax, xlabel, ylabel)
    ax.scatter(x, y, c=clr, s=5 if not _size else _size, label=lgnd)

# ─── Proto (L322-335) ───
def graph_cycle(ax, x, y, xlabel, ylabel, clr, lgnd, _size=None):
    graph_base_parameter(ax, xlabel, ylabel)
    sc = ax.scatter(
        x, y, c=clr,
        s=THEME['SCATTER_SIZE'] if not _size else _size,
        label=lgnd,
        alpha=THEME['SCATTER_ALPHA'],
        edgecolors=THEME['EDGE_COLOR'],
        linewidths=THEME['EDGE_WIDTH'],
        zorder=5
    )
    return sc   # ← scatter 객체 반환 (채널 제어용)
```

| 변경점 | Origin | Proto |
|--------|--------|-------|
| scatter 크기 | `s=5` 하드코딩 | `s=THEME['SCATTER_SIZE']` (=7) |
| 투명도 | 없음 (기본 1.0) | `alpha=0.82` |
| 가장자리 | 없음 | `edgecolors='white'`, `linewidths=0.3` |
| z-순서 | 없음 | `zorder=5` |
| 반환값 | 없음 | `sc` (PathCollection 객체) |

### 8.2 `graph_cycle_empty()` — Origin L215-221 vs Proto L337-348

`graph_cycle()`과 동일한 패턴으로 THEME 적용. 차이점:

| 항목 | Origin | Proto |
|------|--------|-------|
| scatter 크기 | `s=16` | `s=THEME['SCATTER_EMPTY_SIZE']` (=16) |
| facecolors | `'none'` | `'none'` (동일) |
| edgecolors | `clr` | `clr` (동일, THEME 미적용) |
| 반환값 | 없음 | `sc` (채널 제어용) |

### 8.3 `graph_output_cycle()` — Origin L223-245 vs Proto L350-411 (대폭 변경)

**가장 많이 변경된 독립 함수** — 반환값 구조 변경, DCIR 라벨 동적 배치, artists 수집.

```python
# ─── Origin 핵심 (L223-245) ───
def graph_output_cycle(df, xscale, ..., lgnd, colorno, graphcolor, ...):
    graphcolor_set = graphcolor[colorno % 9]  # 9색 순환
    graph_cycle(ax1, x, y_cap, ...)           # 반환값 무시
    graph_cycle(ax2, x, y_chg, ...)
    graph_cycle(ax3, x, y_ce, ...)
    graph_cycle(ax4, x, y_dcir, ...)
    graph_cycle(ax5, x, y_avgv, ...)
    graph_cycle_empty(ax4, x, y_rss, ...)
    # return 없음

# ─── Proto 핵심 (L350-411) ───
def graph_output_cycle(df, xscale, ..., temp_lgnd, colorno, graphcolor, ...):
    artists = []
    color = graphcolor[colorno % len(THEME['PALETTE'])]    # 10색 순환
    
    artists.append(graph_cycle(ax1, ..., color, temp_lgnd))  # ← scatter 수집
    artists.append(graph_cycle(ax2, ..., color, '_nolegend_'))
    artists.append(graph_cycle(ax3, ..., color, '_nolegend_'))
    artists.append(graph_cycle(ax4, ..., color, '_nolegend_'))
    artists.append(graph_cycle(ax5, ..., color, '_nolegend_'))
    
    # DCIR scatter 3배 확대 + 연결선 추가
    artists.append(graph_cycle(ax4, x, dcir_1s, ..., _size=THEME['SCATTER_SIZE'] * 3))
    ax4.plot(x, dcir_1s, color=color, alpha=0.3, linewidth=0.8, zorder=2)
    
    artists.append(graph_cycle_empty(ax4, x, rss, ...))
    ax4.plot(x, rss, color=color, alpha=0.3, linewidth=0.8, zorder=2)
    
    # AvgV/RndV 구분선 + 텍스트 라벨 (ax6에)
    ax6_mid = (df['AvgV'].max() + df['RndV'].min()) / 2
    ax6.axhline(y=ax6_mid, color='gray', linestyle='--', alpha=0.3)
    ax6.text(x.iloc[-1], ax6_mid + 0.01, 'AvgV↑', fontsize=7, alpha=0.5)
    ax6.text(x.iloc[-1], ax6_mid - 0.01, 'RndV↓', fontsize=7, alpha=0.5, va='top')
    
    return artists, color   # ← 채널 제어에 활용
```

| 변경점 | Origin | Proto |
|--------|--------|-------|
| 색상 모듈러 | `% 9` (matplotlib 기본) | `% len(THEME['PALETTE'])` (=10, 학술 컬러) |
| 범례 | 모든 ax에 `lgnd` | ax1만 `temp_lgnd`, 나머지 `'_nolegend_'` |
| DCIR 산점도 | 기본 크기 | 3배 확대 (`SCATTER_SIZE * 3`) |
| DCIR 연결선 | 없음 | `ax4.plot()` 연결선 추가 |
| AvgV/RndV 구분 | 없음 | `axhline` + 텍스트 라벨 |
| 반환값 | 없음 | `(artists, color)` 튜플 |

### 8.4 `place_dcir_labels()` — Proto L413-496 (신규, ~84줄)

**DCIR 산점도에 "Rss@SOC70%"와 "DCIR1s@SOC70%" 라벨을 동적 배치**하는 최적화 함수.

```python
def place_dcir_labels(ax4, channel_map):
    """
    알고리즘:
    1. 모든 채널에서 SOC70% 데이터 포인트 수집
    2. Rss와 DCIR1s 각각의 (x, y) 좌표 찾기
    3. 충돌 회피: 이미 배치된 라벨과 겹치면 오프셋 조정
    4. Annotation(화살표 + 텍스트) 배치
    5. set_draggable(True)로 수동 이동 가능
    """
    # SOC70% 데이터 포인트 수집
    rss_points = []
    dcir_points = []
    for ch_label, info in channel_map.items():
        artists = info['artists']
        # ... Rss/DCIR1s 좌표 추출

    # 라벨 배치 (충돌 회피)
    placed = []
    for label_text, xy in [("Rss@SOC70%", rss_mean), ("DCIR1s@SOC70%", dcir_mean)]:
        offset = _collision_free_offset(xy, placed)
        ann = ax4.annotate(label_text, xy=xy, xytext=offset,
                          arrowprops=dict(arrowstyle='->', color='gray'),
                          fontsize=8, fontweight='bold')
        ann.draggable()
        placed.append(offset)
```

### 8.5 `graph_step()` — Origin L248-253 vs Proto L498-503

**최소 변경** — THEME 참조만 추가:

```python
# Origin
ax.plot(x, y, label=lgnd)

# Proto
ax.plot(x, y, label=lgnd, linewidth=THEME['LINE_WIDTH'], alpha=THEME['LINE_ALPHA'])
```

---

## 9. 핵심 메서드 코드 딥리뷰

### 9.1 `indiv_cyc_confirm_button()` — Origin L8423-8540 vs Proto L10854-11032

**개별 사이클 분석의 메인 핸들러** — 가장 대폭 변경된 메서드 중 하나.

#### 변경 요약표

| 영역 | Origin | Proto | 변경 이유 |
|------|--------|-------|----------|
| **초기화** | 수동 설정 (~30줄) | `_init_confirm_button()` 호출 | 헬퍼 추출 |
| **파일 저장** | 수동 다이얼로그 | `_setup_file_writer()` 호출 | 헬퍼 추출 |
| **탭 생성** | 수동 Figure/Canvas | `_create_plot_tab()` 호출 | 헬퍼 추출 |
| **데이터 로딩** | `for` 루프 순차 | `_load_all_cycle_data_parallel()` | **병렬 로딩** |
| **색상 관리** | `colorno % 9` | `colorno % len(THEME['PALETTE'])` | 학술 컬러 |
| **범례** | 모든 ax 개별 | ax1만 + `_nolegend_` | 중복 제거 |
| **채널맵** | 없음 | `channel_map`, `sub_channel_map` | 채널 제어 |
| **탭 마무리** | `draw()` 호출 | `_finalize_cycle_tab()` | 채널 제어 연동 |
| **DCIR 라벨** | 없음 | `place_dcir_labels(ax4)` | DCIR 가시성 |
| **Excel 출력** | 기본 | `OriCyc` 컬럼 추가 | 원본 사이클 번호 보존 |

#### 핵심 코드 변경 상세

**1) 병렬 로딩 도입**

```python
# ─── Origin: 순차 루프 (L8445-8495) ───
for fi, fd in enumerate(folders):
    for si, sf in enumerate(subfolders):
        if cycler == 'TOYO':
            temp, _ = toyo_cycle_data(folder, cycname, mincapacity, ...)
        else:
            temp, _ = pne_cycle_data(folder, cycname, mincapacity, ...)
        # 즉시 그래프 그리기
        graph_output_cycle(temp, ...)

# ─── Proto: 2단계 (로딩 → 그래프) (L10885-10920) ───
# 1단계: 병렬 로딩 (ThreadPoolExecutor)
results_dict, subfolder_map = self._load_all_cycle_data_parallel(
    folders, ..., cycler, ...)
# 2단계: 결과 순회
for key in sorted(results_dict):
    temp = results_dict[key]
    _artists, _color = graph_output_cycle(temp, ...)
    # channel_map 구축
    channel_map[ch_label] = {'artists': _artists, 'color': _color}
```

**2) 채널맵 구축과 색상 충돌 해결**

```python
# Proto에서 추가된 채널맵 로직 (L10920-10960)
ch_label, sub_label = _make_channel_labels(cycnamelist, fi, si)
_artists, _color = graph_output_cycle(temp, xscale, ...)

# 색상 충돌 해결: 같은 ch_label이 다른 색상으로 이미 존재시
while ch_label in channel_map and channel_map[ch_label]['color'] != _color:
    ch_label = f"{ch_label}'"  # 프라임(') 추가로 구분

channel_map[ch_label] = {'artists': _artists, 'color': _color}
if sub_label:
    sub_channel_map[sub_label] = {
        'artists': _artists, 'color': _color, 'parent': ch_label
    }
```

**3) Tkinter 의존성 제거**

```python
# Origin (L8423)
root = Tk()
root.withdraw()
# ... tkinter filedialog 사용
root.destroy()

# Proto — Tkinter root 없음, Qt 네이티브 다이얼로그 사용
```

### 9.2 `overall_cyc_confirm_button()` — Origin L8541-8661 vs Proto L11033-11247

**전체 사이클 분석 핸들러** — 개별과 유사하나 범례 중복 제거 로직이 핵심.

#### 추가된 범례 중복 제거 알고리즘

```python
# Proto (L11100-11140)
_seen_ch_labels = set()

for key in sorted(results_dict):
    ch_label, sub_label = _make_channel_labels(cycnamelist, fi, si)
    
    # 범례 중복 방지: 같은 ch_label이면 '_nolegend_' 사용
    if ch_label in _seen_ch_labels:
        temp_lgnd = '_nolegend_'
    else:
        temp_lgnd = ch_label
        _seen_ch_labels.add(ch_label)
    
    _artists, _color = graph_output_cycle(temp, ..., temp_lgnd, ...)
```

#### 범례 스타일링 개선

```python
# Origin — matplotlib 기본 범례
ax1.legend()

# Proto — THEME 기반 명시적 범례 구성 (L11180-11210)
handles, labels = [], []
_seen = set()
for ch_label, info in channel_map.items():
    if ch_label not in _seen:
        handles.append(info['artists'][0])  # 첫 번째 scatter
        labels.append(ch_label)
        _seen.add(ch_label)

_lkw = dict(fontsize=THEME['LEGEND_SIZE'], framealpha=THEME['LEGEND_ALPHA'],
            edgecolor='gray', fancybox=True)
ax1.legend(handles, labels, **_lkw)

# suptitle도 THEME 적용
fig.suptitle(title, fontsize=THEME['SUPTITLE_SIZE'], fontweight='bold')
```

---

## 10. Proto 신규 헬퍼 메서드 상세

> 기존 버튼 핸들러에서 반복되는 코드를 7개 헬퍼로 추출한 리팩토링.

### 10.1 `_init_confirm_button()` — Proto L9551-9570

**역할**: 모든 confirm 버튼 핸들러의 공통 초기화 로직 통합

```python
def _init_confirm_button(self):
    """버튼 비활성화 → UI 설정 로드 → 경로/사이클러 설정 → dict 반환"""
    self.indiv_cyc_confirm.setDisabled(True)  # 중복 클릭 방지
    config = {
        'folders': [...],
        'names': [...],
        'firstCrate': self.CRate.text(),
        'mincapacity': float(self.MinCap.text()),
        'CycleNo': self.CycleNo.text(),
        'smoothdegree': int(self.SmoothDeg.text()),
        'mincrate': float(self.MinCRate.text()),
        'dqscale': float(self.dQScale.text()),
        'dvscale': float(self.dVScale.text()),
    }
    return config
```

**효과**: 10개+ confirm 버튼에서 반복되던 ~20줄을 1줄 호출로 축소.

### 10.2 `_setup_file_writer()` — Proto L9572-9589

```python
def _setup_file_writer(self, save_ok_flag='saveok'):
    """파일 저장 다이얼로그 + ExcelWriter 생성
    Returns: (writer, save_file_name) 또는 (None, None)
    """
    if getattr(self, save_ok_flag):
        file_path = QtWidgets.QFileDialog.getSaveFileName(
            self, '저장', '', 'Excel (*.xlsx)')[0]
        if file_path:
            writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
            return writer, file_path
    return None, None
```

### 10.3 `_create_plot_tab()` — Proto L9591-9601

```python
def _create_plot_tab(self, fig, tab_name):
    """Figure → Canvas → Toolbar → Tab 생성
    Returns: (tab, tab_layout, canvas, toolbar)
    """
    tab = QtWidgets.QWidget()
    tab_layout = QtWidgets.QVBoxLayout(tab)
    canvas = FigureCanvasQTAgg(fig)
    toolbar = NavigationToolbar2QT(canvas, tab)
    tab_layout.addWidget(toolbar)
    tab_layout.addWidget(canvas)
    self.tabWidget.addTab(tab, tab_name)
    return tab, tab_layout, canvas, toolbar
```

### 10.4 `_finalize_cycle_tab()` — Proto L10340-10363

```python
def _finalize_cycle_tab(self, tab_layout, toolbar, canvas, fig, axes_list,
                        channel_map, sub_channel_map=None):
    """사이클 탭 마무리: CH 토글 버튼 + 채널 제어 팝업"""
    # ▶ CH 버튼을 toolbar 옆에 삽입
    ch_btn = QPushButton("▶ CH")
    ch_btn.setFixedSize(50, 22)
    toolbar_layout = toolbar.parent().layout()
    toolbar_layout.insertWidget(0, ch_btn)
    
    # 채널 제어 팝업 연결
    ch_btn.clicked.connect(lambda: self._create_cycle_channel_control(
        canvas, fig, axes_list, channel_map, sub_channel_map))
    
    canvas.draw()
```

### 10.5 `_finalize_plot_tab()` — Proto L10365-10376

```python
def _finalize_plot_tab(self, canvas, fig, has_colorbar=False):
    """일반 플롯 탭 마무리 (컬러바 레이아웃 보정 포함)"""
    if has_colorbar:
        fig.subplots_adjust(right=0.85)
    canvas.draw()
```

### 10.6 `_setup_legend()` — Proto L10378-10443

**스마트 범례 시스템** — 15개 초과 시 자동으로 컬러바 모드 전환.

```python
def _setup_legend(self, ax, fig, channel_map, *, legend_threshold=LEGEND_THRESHOLD):
    """
    ≤ 15개: 일반 범례 (handles + labels)
    > 15개: 컬러바 (turbo/viridis/tab20/hsv cmap 자동 선택)
    """
    n = len(channel_map)
    if n <= legend_threshold:
        handles, labels = [], []
        for ch_label, info in channel_map.items():
            handles.append(info['artists'][0])
            labels.append(ch_label)
        ax.legend(handles, labels, fontsize=THEME['LEGEND_SIZE'],
                  framealpha=THEME['LEGEND_ALPHA'])
    else:
        # cmap 선택: n≤20→tab20, n≤256→turbo, else→hsv
        if n <= 20:
            cmap = cm.get_cmap('tab20', n)
        elif n <= 256:
            cmap = cm.get_cmap('turbo', n)
        else:
            cmap = cm.get_cmap('hsv', n)
        
        norm = mcolors.Normalize(vmin=0, vmax=n - 1)
        sm = cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, pad=0.02, fraction=0.03)
        cbar.set_ticks(range(n))
        cbar.set_ticklabels(list(channel_map.keys()))
```

### 10.7 `match_highlight_text()` — Proto L13539-13552

```python
def match_highlight_text(self, text, query):
    """검색 매칭 (AND/OR 연산자 지원)
    
    쉼표(,) = AND: 모든 단어가 포함되어야 매칭
    스페이스( ) = OR: 하나라도 포함되면 매칭
    
    예: "4879mAh,Rss" → 4879mAh AND Rss
        "4879 5000"   → 4879 OR 5000
    """
    if ',' in query:
        # AND 연산
        terms = [t.strip() for t in query.split(',')]
        return all(t.lower() in text.lower() for t in terms if t)
    else:
        # OR 연산
        terms = query.split()
        return any(t.lower() in text.lower() for t in terms if t)
```

---

## 11. 병렬 로딩 시스템 상세

### 11.1 아키텍처 개요

```
┌─────────────────────────────────────────────────────────┐
│  버튼 핸들러 (indiv_cyc, overall_cyc, step, rate, etc.) │
│         │                                               │
│         ▼                                               │
│  _load_all_*_parallel()  ← 오케스트레이터              │
│         │                                               │
│    ThreadPoolExecutor(max_workers=4)                    │
│    ┌────┼────┬────┐                                     │
│    ▼    ▼    ▼    ▼                                     │
│  task  task  task  task  ← _load_*_task() 디스패처     │
│    │    │    │    │                                      │
│    ▼    ▼    ▼    ▼                                     │
│  toyo_* / pne_*_batch()  ← 실제 I/O (batch 함수)       │
│         │                                               │
│         ▼                                               │
│  results_dict  → 그래프 그리기 / 저장                   │
└─────────────────────────────────────────────────────────┘
```

### 11.2 사이클 데이터 병렬 로딩

#### `_load_cycle_data_task()` — Proto L10627-10639

```python
def _load_cycle_data_task(self, folder, cycname, mincapacity, cycler, ...):
    """단일 (folder, subfolder) 조합의 사이클 데이터 로딩 태스크"""
    if cycler == 'TOYO':
        temp, _ = toyo_cycle_data(folder, cycname, mincapacity, ...)
    else:
        temp, _ = pne_cycle_data(folder, cycname, mincapacity, ...)
    return temp
```

#### `_load_all_cycle_data_parallel()` — Proto L10641-10671

```python
def _load_all_cycle_data_parallel(self, folders, subfolders, cycler, ...):
    """모든 폴더×서브폴더 조합을 병렬 로딩
    
    Returns:
        results_dict: {(fi, si): DataFrame}
        subfolder_map: {(fi, si): subfolder_name}
    """
    results_dict = {}
    subfolder_map = {}
    tasks = []
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        for fi, fd in enumerate(folders):
            for si, sf in enumerate(subfolders):
                future = executor.submit(
                    self._load_cycle_data_task, fd, cycname, ...)
                tasks.append((future, fi, si, sf))
        
        total = len(tasks)
        for idx, (future, fi, si, sf) in enumerate(as_completed_wrapper(tasks)):
            temp = future.result()
            if temp is not None and not temp.empty:
                results_dict[(fi, si)] = temp
                subfolder_map[(fi, si)] = sf
            # 진행률 업데이트: 0~50% (로딩 단계)
            self.progressBar.setValue(int(50 * (idx + 1) / total))
    
    return results_dict, subfolder_map
```

### 11.3 스텝 데이터 병렬 로딩

#### `_load_step_batch_task()` — Proto L10444-10458

```python
def _load_step_batch_task(self, folder, cycname, mincapacity, CycleNo, cycler, ...):
    """Toyo/PNE 분기 + batch 함수 호출"""
    if cycler == 'TOYO':
        return toyo_step_Profile_batch(folder, cycname, mincapacity, CycleNo, ...)
    else:
        return pne_step_Profile_batch(folder, cycname, mincapacity, CycleNo, ...)
```

#### `_load_all_step_data_parallel()` — Proto L10460-10495

```python
def _load_all_step_data_parallel(self, folders, subfolders, ...):
    """스텝 데이터 병렬 수집
    
    Returns: {(fi, si, cyc_no): (mincapacity, normalized_df)}
    """
    all_data = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for fi, fd in enumerate(folders):
            for si, sf in enumerate(subfolders):
                future = executor.submit(self._load_step_batch_task, ...)
                futures[future] = (fi, si)
        
        for future in as_completed(futures):
            fi, si = futures[future]
            batch_result = future.result()  # {cyc_no: (mincap, df)}
            for cyc_no, (mincap, df) in batch_result.items():
                all_data[(fi, si, cyc_no)] = (mincap, df)
            self.progressBar.setValue(...)  # 0~50%
    
    return all_data
```

#### `_plot_and_save_step_data()` — Proto L10578-10625

```python
def _plot_and_save_step_data(self, all_data, fig, axes, writer, ...):
    """수집된 스텝 데이터를 6개 subplot에 그래프 + Excel 저장
    
    6개 그래프:
    - ax1: V vs Capacity
    - ax2: V vs Time
    - ax3: I vs Time
    - ax4: T vs Time
    - ax5: Capacity vs Cycle
    - ax6: dQ/dV or dV/dQ
    """
    write_col = 0
    for key in sorted(all_data):
        mincap, df = all_data[key]
        # 6개 그래프 플로팅
        graph_step(axes[0], df['Cap'], df['V'], ...)
        graph_step(axes[1], df['Time'], df['V'], ...)
        # ... (6개 subplot)
        
        # Excel 저장
        if writer:
            df.to_excel(writer, startcol=write_col, ...)
            write_col += len(df.columns) + 1
    
    return write_col
```

### 11.4 Batch 함수 상세 (Origin에 없는 신규 함수)

#### `toyo_build_cycle_map()` — Proto L910-958

```python
def toyo_build_cycle_map(folder, cycname):
    """Toyo 사이클 맵 빌더: {논리사이클: (첫번째파일, dchg_ori_max)}
    
    최적화: 1-pass groupby로 전체 사이클 맵 구축
    Origin에서는 매 사이클마다 파일 순회 → O(n×m) → O(n)으로 단축
    """
    csvfiles = sorted(glob.glob(os.path.join(folder, '*.csv')))
    all_dfs = [toyo_read_csv(f) for f in csvfiles]
    merged = pd.concat(all_dfs)
    grouped = merged.groupby('OriCyc')
    
    cycle_map = {}
    for ori_cyc, group_df in grouped:
        first_file = csvfiles[0]  # 해당 사이클의 첫 파일
        dchg_max = group_df['DchgCap'].max()
        cycle_map[ori_cyc] = (first_file, dchg_max)
    
    return cycle_map
```

#### `toyo_step_Profile_batch()` — Proto L959-1008

```python
def toyo_step_Profile_batch(folder, cycname, mincapacity, CycleNo, ...):
    """Toyo 스텝 프로필 배치 처리
    
    Returns: {cyc_no: (min_capacity, normalized_df)}
    
    최적화: min_cap을 루프 밖에서 1회 계산 (Origin은 매 사이클마다 재계산)
    """
    cycle_map = toyo_build_cycle_map(folder, cycname)
    min_cap = toyo_min_cap(folder, cycname, mincapacity)  # 1회만
    
    result = {}
    for cyc_no in CycleNo:
        if cyc_no in cycle_map:
            first_file, _ = cycle_map[cyc_no]
            df = toyo_step_Profile_data(first_file, cycname, min_cap, cyc_no, ...)
            result[cyc_no] = (min_cap, df)
    
    return result
```

#### `pne_step_Profile_batch()` — Proto L1009-1122

```python
def pne_step_Profile_batch(folder, cycname, mincapacity, CycleNo, ...):
    """PNE 스텝 프로필 배치 처리 — 핵심 최적화
    
    Origin 방식: 매 사이클마다 SaveData 파일 범위 탐색 (디스크 I/O 반복)
    Proto 방식: binary_search로 1회 파일 범위 결정 → 메모리 필터링
    
    Returns: {cyc_no: (min_capacity, normalized_df)}
    """
    min_cap, all_raw_df, is_pne21_22 = _pne_load_profile_raw(
        folder, cycname, mincapacity)  # ← 1회 디스크 읽기
    
    result = {}
    for cyc_no in CycleNo:
        # all_raw_df에서 메모리 내 필터링 (디스크 I/O 없음)
        cycle_df = all_raw_df[all_raw_df['CycleNo'] == cyc_no]
        if not cycle_df.empty:
            normalized = _normalize_step(cycle_df, min_cap, is_pne21_22)
            result[cyc_no] = (min_cap, normalized)
    
    return result
```

#### `_pne_load_profile_raw()` — Proto L1123-1182

```python
def _pne_load_profile_raw(folder, cycname, mincapacity):
    """PNE SaveData 공통 로더 (5개 batch 함수에서 공유)
    
    Returns: (min_capacity, all_raw_df, is_pne21_22)
    
    최적화:
    - binary_search()로 파일 범위 1회 결정
    - pd.concat()으로 전체 데이터 1회 로딩
    - 이후 각 batch 함수가 메모리 필터링만 수행
    """
    savedata_files = sorted(glob.glob(os.path.join(folder, 'SaveData*.csv')))
    start_idx, end_idx = binary_search(savedata_files, cycname)
    target_files = savedata_files[start_idx:end_idx + 1]
    
    all_raw_df = pd.concat([pd.read_csv(f) for f in target_files])
    min_cap = pne_min_cap(folder, cycname, mincapacity)
    is_pne21_22 = check_cycler(folder) in ('PNE21', 'PNE22')
    
    return min_cap, all_raw_df, is_pne21_22
```

### 11.5 Origin vs Proto 성능 비교

| 시나리오 | Origin (순차) | Proto (병렬) | 개선 |
|---------|-------------|-------------|------|
| 3폴더 × 2서브 = 6조합 | 6 × 3s = 18s | max(3s) + overhead ≈ 4s | **~4.5배** |
| PNE 10사이클 스텝 | 10 × disk I/O | 1 × disk I/O + 10 × 메모리필터 | **~8-10배** |
| Toyo min_cap 계산 | 사이클마다 반복 | 1회 사전 계산 | **O(n)→O(1)** |

---

## 12. 채널 제어 시스템 상세

> Proto의 가장 큰 신규 기능 (~725줄). Origin에 없는 완전 신규 시스템.

### 12.1 시스템 구성

```
_finalize_cycle_tab()
    │
    ├─ ▶ CH 버튼 (50×22px) ─── 클릭 ───→ _create_cycle_channel_control()
    │                                         │
    │                                    _build_channel_dialog()
    │                                         │
    │                           ┌─────────────┼─────────────┐
    │                           │             │             │
    │                      채널 리스트    하이라이트     범례 슬라이더
    │                      (QListWidget)    제어        (QSlider)
    │                           │             │             │
    │                      on_item_changed  _apply_        _on_font_size
    │                      on_item_clicked  _highlight     
    │                           │                          
    │                      서브채널 리스트 (조건부)
    │                      (sub_channel_map 있을 때)
    └──────────────────────────────────────────────────────
```

### 12.2 `_create_cycle_channel_control()` — Proto L9615+ (~725줄)

**Lazy Init 패턴**: 버튼 클릭 시에만 팝업 생성, 이미 열려있으면 토글.

#### 핵심 데이터 구조

```python
channel_map = {
    'CH01_4879mAh': {
        'artists': [sc1, sc2, sc3, ...],  # PathCollection 목록
        'color': '#3C5488'
    },
    'CH02_5000mAh': {
        'artists': [sc4, sc5, ...],
        'color': '#E64B35'
    }
}

sub_channel_map = {
    'CH01_Cyc1': {
        'artists': [sc1],
        'color': '#3C5488',
        'parent': 'CH01_4879mAh'  # 부모 채널 참조
    }
}

_orig_colors = {
    id(sc1): {'fc': array([[0.24, 0.33, 0.53, 0.82]]),   # facecolors
              'ec': array([[1.0, 1.0, 1.0, 1.0]])}        # edgecolors
}

highlight_state = {
    'active': set(),       # 현재 하이라이트된 채널 라벨 세트
    'enabled': False       # 개별 선택 모드 활성화 여부
}
```

### 12.3 색상 스냅샷 & 복원 메커니즘

```python
# 초기 색상 저장 (팝업 생성 시)
_orig_colors = {}
for ch_label, info in channel_map.items():
    for art in info['artists']:
        _orig_colors[id(art)] = {
            'fc': art.get_facecolors().copy(),
            'ec': art.get_edgecolors().copy()
        }

# 복원 함수
def _restore_all():
    """모든 artist를 원래 색상으로 복원"""
    for ch_label, info in channel_map.items():
        for art in info['artists']:
            orig = _orig_colors.get(id(art))
            if orig is not None:
                art.set_facecolors(orig['fc'].copy())
                art.set_edgecolors(orig['ec'].copy())
            art.set_alpha(THEME['SCATTER_ALPHA'])
            art.set_zorder(5)
```

### 12.4 하이라이트 알고리즘

```python
DIM_COLOR = '#CCCCCC'
DIM_ALPHA = 0.15
NORMAL_ALPHA = THEME['SCATTER_ALPHA']  # 0.82

def _apply_highlight():
    """현재 active set 기준으로 하이라이트/딤 적용
    
    선택된 채널: alpha=1.0, 원본 색상, zorder=10 (전면)
    미선택 채널: alpha=0.15, #CCCCCC, zorder=1 (후면)
    """
    selected = highlight_state['active']
    if not selected:
        # 선택 없음 → 모두 dim
        for lbl, info in channel_map.items():
            for art in info['artists']:
                _dim_artist(art)
        canvas.draw_idle()
        return
    
    for lbl, info in channel_map.items():
        if lbl in selected:
            # 하이라이트
            for art in info['artists']:
                orig = _orig_colors.get(id(art))
                art.set_alpha(1.0)
                art.set_facecolors(orig['fc'].copy())
                art.set_edgecolors(orig['ec'].copy())
                art.set_zorder(10)
        else:
            # 딤
            for art in info['artists']:
                _dim_artist(art)
    
    canvas.draw_idle()
```

### 12.5 채널-서브채널 연동

서브채널이 존재하는 경우 (`sub_channel_map`), 다음 연동 동작:

| 사용자 동작 | 채널 리스트 반응 | 서브채널 리스트 반응 |
|------------|---------------|-------------------|
| 채널 체크 해제 | 해당 채널 artist 숨김 | 하위 서브채널 자동 체크 해제 |
| 채널 클릭 (하이라이트) | 해당 채널 하이라이트 | 변동 없음 |
| 서브채널 체크 해제 | 변동 없음 | 해당 서브채널 artist만 숨김 |
| 서브채널 클릭 | 변동 없음 | 해당 서브채널만 하이라이트/딤 토글 |
| "전체 표시" 체크 | 모든 채널 ON/OFF | 모든 서브채널 동기화 |
| "전체 하이라이트" 체크 | 모든 채널 원본 복원 | — |

### 12.6 범례 동적 재구축

```python
def _rebuild_legend():
    """표시 중인 채널만으로 범례을 다시 구축"""
    for ax in axes_list:
        handles, labels = [], []
        for ch_label in channel_map:
            if any(art.get_visible() for art in channel_map[ch_label]['artists']):
                alias = _legend_aliases.get(ch_label, ch_label)
                handles.append(channel_map[ch_label]['artists'][0])
                labels.append(alias)
        if handles:
            ax.legend(handles, labels, fontsize=THEME['LEGEND_SIZE'],
                     framealpha=THEME['LEGEND_ALPHA'])
        else:
            ax.get_legend().remove() if ax.get_legend() else None
    canvas.draw_idle()
```

### 12.7 추가 UI 기능

| 기능 | 구현 |
|------|------|
| **범례 폰트 크기 슬라이더** | QSlider(6~18pt), 실시간 반영 |
| **범례 드래그** | `legend.set_draggable(True)` |
| **DCIR 라벨 드래그** | `Annotation.draggable()` |
| **채널 이름 편집** | QListWidget 텍스트 직접 편집 → `_legend_aliases` 업데이트 |
| **다크/라이트 테마 감지** | 팝업 배경색 자동 조정 |

---

## 13. PNE→Toyo 변환 시스템 상세

> 14개 메서드로 구성된 PNE 충방전기 → Toyo PATRN 형식 변환 파이프라인.

### 13.1 데이터 흐름

```
PNE MDB (Access DB)
    │
    ▼
ptn_toyo_convert_button()  [최상위 핸들러]
    │
    ├─ pyodbc.connect() → Step 테이블 조회
    │
    ▼
_pne_steps_to_toyo_substeps(steps_df)  [핵심 변환 엔진]
    │
    ├─ StepType별 서브스텝 생성 (charge/discharge/rest/loop)
    ├─ Loop 정보 추출 및 부착
    └─ LEFT-RIGHT 페어링 → PATRN 라인 생성
    │
    ▼
6개 파일 출력:
    ├─ PATRN{N}.1        (헤더 + 데이터 라인)
    ├─ Patrn{N}.option   (용량 설정)
    ├─ Patrn{N}.option2  (라인별 메타데이터)
    ├─ Fld_Puls{N}.DIR   (펄스 디렉토리)
    ├─ Fld_Thermo{N}.DIR (빈 파일)
    └─ THPTNNO.1         (패턴 번호)
```

### 13.2 PATRN 파일 구조

Toyo 충방전기의 PATRN 파일은 **고정 너비(Fixed-Width)** 텍스트 형식:

```
┌──────────────────────────────────────────────────────────────┐
│ PATRN{N}.1 파일 구조                                         │
├──────────────────────────────────────────────────────────────┤
│ [헤더: 265 bytes]                                            │
│  ├─ 패턴명 (42 bytes, cp949, 우측 공백 패딩)                  │
│  ├─ 고정 suffix (TOYO_HEADER_PREFIX)                         │
│  └─ 데이터 라인 수 (21 bytes)                                │
├──────────────────────────────────────────────────────────────┤
│ [데이터 라인 × N: 각 543 bytes]                               │
│  ├─ LEFT 서브스텝 (261 chars): 충전 or 휴지                   │
│  ├─ RIGHT 서브스텝 (272 chars): 방전 or 휴지                  │
│  └─ LOOP 정보 (10 chars): 반복 대상/횟수                     │
└──────────────────────────────────────────────────────────────┘
인코딩: cp949 (한글 Windows)
```

### 13.3 PNE StepType → Toyo 서브스텝 매핑

| PNE StepType | 의미 | Toyo 변환 | 비고 |
|:---:|--------|----------|------|
| 1 | 충전 | `_toyo_build_charge_left()` | CC-CV 자동 판정 |
| 2 | 방전 | `_toyo_build_dchg_right()` | — |
| 3 | 휴지 | `_toyo_build_rest_left/right()` | — |
| 4 | OCV | 휴지로 변환 | — |
| 5 | Impedance | 방전 펄스로 변환 | endV=0 |
| 8 | Loop | `_toyo_build_loop()` | 정규식으로 대상 추출 |
| 9 | Continuation | 이전 스텝 계속 | 충전/방전 컨텍스트 유지 |

### 13.4 LEFT-RIGHT 페어링 알고리즘

Toyo PATRN은 한 라인에 **LEFT + RIGHT** 두 서브스텝을 담음:

```
규칙:
1. Charge → LEFT에 배치, 다음 스텝을 RIGHT로 소비
2. Discharge → LEFT는 REST, 자신을 RIGHT에 배치
3. Rest → LEFT에 배치, 다음 스텝을 RIGHT로 소비
4. RIGHT가 Charge면 → REST RIGHT 사용, Charge를 큐에 다시 삽입 (이월)

예시: [CC충전, CV충전, 방전, 휴지, 방전] → PATRN 라인:
  Line 1: [CC_LEFT  ] [REST_RIGHT  ] [LOOP_NONE]
  Line 2: [CV_LEFT  ] [DCHG_RIGHT  ] [LOOP_NONE]
  Line 3: [REST_LEFT] [DCHG_RIGHT  ] [LOOP_NONE]
  (* CV가 RIGHT에 올 수 없으므로 이월됨)
```

### 13.5 CC-CV 자동 판정 알고리즘

```python
# PNE 충전 스텝의 CC-CV 모드 결정
if end_i > 0 and iref > 0:
    is_cccv = (end_i / iref) < 0.3
else:
    is_cccv = False

# 의미:
# EndI/Iref < 0.3 → 종료전류가 충전전류의 30% 미만 = CV 모드 (정전압 유지)
# EndI/Iref ≥ 0.3 → 종료전류가 충전전류의 30% 이상 = CC 모드 (용량 제한)
```

### 13.6 빌드 메서드 요약

| # | 메서드 | 라인 | 입력 | 출력 | 역할 |
|----|--------|------|------|------|------|
| 1 | `_toyo_fmt_num()` | 17183 | float | str | 숫자 포맷 (정수/소수 자동) |
| 2 | `_toyo_substitute()` | 17190 | template, positions | str | 고정위치 우측정렬 치환 |
| 3 | `_toyo_build_charge_left()` | 17197 | current, voltage, endI | str(261) | 충전 LEFT |
| 4 | `_toyo_build_dchg_right()` | 17209 | current, endV | str(272) | 방전 RIGHT |
| 5 | `_toyo_build_rest_left()` | 17220 | — | str(261) | 휴지 LEFT |
| 6 | `_toyo_build_rest_right()` | 17224 | — | str(272) | 휴지 RIGHT |
| 7 | `_toyo_build_loop()` | 17228 | target, count | str(10) | 루프 정보 |
| 8 | `_toyo_build_line()` | 17234 | left, right, loop | str(543) | 라인 조립 |
| 9 | `_toyo_build_header()` | 17237 | name, lines | str(265) | 헤더 (cp949) |
| 10 | `_toyo_build_option()` | 17246 | capacity | str | .option 파일 |
| 11 | `_toyo_build_option2()` | 17250 | line_types | str | .option2 메타 (CSV) |
| 12 | `_toyo_build_puls_dir()` | 17314 | num_lines | str | Puls.DIR 파일 |
| 13 | `_pne_steps_to_toyo_substeps()` | 17318 | steps_df | (lines, types) | **핵심 변환 엔진** |
| 14 | `ptn_toyo_convert_button()` | 17436 | UI input | 6개 파일 | **최상위 핸들러** |

---

## 14. PyBaMM 시뮬레이션 시스템 상세

> 독립 함수 1개 + WindowClass 메서드 ~20개로 구성된 전기화학 시뮬레이션.

### 14.1 시스템 구성

```
┌─────────────── UI 레이어 ───────────────┐
│  모델 선택 (SPM/SPMe/DFN)               │
│  파라미터 테이블 (14개 파라미터)          │
│  스텝 리스트 (충전/방전/커스텀)           │
│  프리셋 (10개 문헌 파라미터)              │
│         │                               │
│  pybamm_run_button()                    │
│         │ [오케스트레이션]                │
└─────────┼───────────────────────────────┘
          ▼
┌─── 계산 레이어 ───┐
│  run_pybamm_      │
│  simulation()     │ ← 독립 함수 (L2843-2999)
│  (모델/실험/솔버)  │
└────────┬──────────┘
         ▼
┌─── 시각화 레이어 ───────────┐
│  일반 Plot (2×3): V, I, Q  │
│  상세 Plot (2×3): 과전압 등 │
│  탭 관리, 결과 저장         │
└─────────────────────────────┘
```

### 14.2 지원 배터리 모델

| 모델 | 설명 | 복잡도 | 용도 |
|------|------|--------|------|
| **SPM** (Single Particle) | 전극 입자 모델만 | 가장 빠름 | 빠른 예측 |
| **SPMe** (SPM + Electrolyte) | SPM + 전해질 동역학 | 중간 | 균형 분석 |
| **DFN** (Doyle-Fuller-Newman) | 완전 물리 기반 모델 | 가장 정교 | 상세 연구 |

### 14.3 실험 모드 (5가지)

```
모드 1: "ccv" — CC-CV 완전 사이클
  ├─ 초기 SOC: 0.0 (완전 방전)
  └─ 각 사이클: CC충전 → CV유지 → CC방전

모드 2: "charge" — 사용자 정의 충전 스텝
  ├─ 초기 SOC: 0.0
  └─ steps[] × cycles 반복

모드 3: "discharge" — 사용자 정의 방전 스텝
  ├─ 초기 SOC: 1.0 (만충)
  └─ steps[] × cycles 반복

모드 4: "custom" — 단일 시퀀스
  ├─ 초기 SOC: 0.5
  └─ 사용자 입력 PyBaMM 문자열

모드 5: "gitt" — 갈바노정전 구간 적정
  ├─ 초기 SOC: 1.0
  ├─ GITT: [펄스방전, 휴지] × N
  └─ HPPC: [펄스방전, 휴지, 펄스충전, 휴지] × N
```

### 14.4 파라미터 매핑 (14개)

| # | 한글명 | PyBaMM 키 | 단위 변환 |
|---|--------|----------|----------|
| 1 | 양극 두께 | Positive electrode thickness [m] | ×1e-6 (μm→m) |
| 2 | 양극 입자 반경 | Positive particle radius [m] | ×1e-6 |
| 3 | 양극 활물질 비율 | Pos. electrode active material vol. fraction | ×1 |
| 4 | 양극 Bruggeman | Pos. electrode Bruggeman coeff. (electrolyte) | ×1 |
| 5 | 음극 두께 | Negative electrode thickness [m] | ×1e-6 |
| 6 | 음극 입자 반경 | Negative particle radius [m] | ×1e-6 |
| 7 | 음극 활물질 비율 | Neg. electrode active material vol. fraction | ×1 |
| 8 | 음극 Bruggeman | Neg. electrode Bruggeman coeff. (electrolyte) | ×1 |
| 9 | 분리막 두께 | Separator thickness [m] | ×1e-6 |
| 10 | 분리막 Bruggeman | Separator Bruggeman coeff. | ×1 |
| 11 | 전해질 농도 | Initial electrolyte concentration | ×1 |
| 12 | 전극 면적 | Electrode width [m] | ×1 |
| 13 | 셀 용량 | Nominal cell capacity [A.h] | ×1 |
| 14 | 온도 | Ambient temperature [K] | **+273.15 (°C→K)** |

### 14.5 `run_pybamm_simulation()` — Proto L2843-2999 (독립 함수)

```python
def run_pybamm_simulation(model_name, params_dict, experiment_config):
    """
    Args:
        model_name: "SPM" | "SPMe" | "DFN"
        params_dict: {한글명: float} (14개)
        experiment_config: {'mode': str, 'steps': list, 'cycles': int, ...}
    
    Returns:
        pybamm.Solution
    
    에러 처리:
        - 미지원 모델명 → ValueError
        - 빈 스텝 리스트 → ValueError
        - 미지원 모드 → ValueError
    """
    # 모델 선택
    models = {
        "SPM": pybamm.lithium_ion.SPM,
        "SPMe": pybamm.lithium_ion.SPMe,
        "DFN": pybamm.lithium_ion.DFN,
    }
    model = models[model_name]()
    
    # 파라미터 매핑 (한글 → PyBaMM 키, 단위 변환)
    param = pybamm.ParameterValues("Chen2020")  # 기본값
    for ko_name, value in params_dict.items():
        pybamm_key, converter = PARAM_MAP[ko_name]
        param[pybamm_key] = converter(value)
    
    # 실험 구성 (모드별)
    mode = experiment_config['mode']
    if mode == "ccv":
        experiment = pybamm.Experiment([
            f"Charge at {chg_crate}C until {v_max}V",
            f"Hold at {v_max}V until {cv_cutoff}C",
            f"Discharge at {dchg_crate}C until {v_min}V",
        ] * cycles)
    elif mode in ("charge", "discharge"):
        experiment = pybamm.Experiment(steps * cycles)
    elif mode == "custom":
        experiment = pybamm.Experiment(steps)
    elif mode == "gitt":
        # GITT/HPPC 패턴 생성
        ...
    
    # 시뮬레이션 실행
    sim = pybamm.Simulation(model, parameter_values=param,
                            experiment=experiment)
    sol = sim.solve(initial_soc=init_soc)
    return sol
```

### 14.6 결과 시각화 (2×3 격자 × 2탭)

#### 탭 1: 일반 Plot

| 위치 | 그래프 | X축 | Y축 |
|------|--------|-----|------|
| [1,1] | Cell V & I | Time [min] | Voltage [V] / Current [A] (twinx) |
| [1,2] | V-Q 곡선 | Capacity [A.h] | Voltage [V] |
| [2,1] | 전극 열역학 | Time [min] | φs vs OCP [V] |
| [2,2] | 전극 SOC | Time [min] | x (lithiation degree) |
| [3,1] | 셀 온도 | Time [min] | Temperature [°C] |
| [3,2] | 발열원 분해 | Time [min] | Heat [W] (Ohmic/Irreversible/Reversible) |

#### 탭 2: 상세 Plot

| 위치 | 그래프 | X축 | Y축 |
|------|--------|-----|------|
| [1,1] | 과전압 분해 | Time [min] | Overpotential [V] (반응/전해질/고상/농도) |
| [1,2] | 고상 확산 | Time [min] | Surface/Bulk concentration [mol/m³] |
| [2,1] | 전해질 Li+ 농도 | Time [min] | c_e [mol/m³] |
| [2,2] | 전해질 전위 | Time [min] | φ_e [V] |
| [3,1] | 계면 전류 밀도 | Time [min] | j [A/m²] |
| [3,2] | 리튬 도금 위험도 | Time [min] | Plating criterion |

### 14.7 스텝 UI 메서드 (10개)

| 메서드 | 라인 | 역할 |
|--------|------|------|
| `_pybamm_insert_step()` | 18094 | QListWidget에 스텝 항목 추가 |
| `_pybamm_update_step_fields()` | 18106 | 스텝 타입별 필드 활성화/비활성화 |
| `_pybamm_parse_cutoff()` | 18174 | 종료조건 문자열 파싱 ("0.05C" → (0.05, "C")) |
| `_pybamm_cutoff_to_cv_str()` | 18195 | → "Hold at 4.2V until 0.05C" |
| `_pybamm_cutoff_to_rest_str()` | 18210 | → "Rest for 600 seconds" |
| `_pybamm_hhmmss_to_rest_str()` | 18222 | HH:MM:SS → PyBaMM 시간 문자열 |
| `_pybamm_chg_add_step()` | 18246 | 충전 스텝 추가 (CC/CV/CCCV/Rest) |
| `_pybamm_dchg_add_step()` | 18269 | 방전 스텝 추가 |
| `_pybamm_del_step()` | 18292 | 선택 스텝 삭제 |
| `_pybamm_copy_steps()` | 18298 | 클립보드 복사 |
| `_pybamm_paste_steps()` | 18306 | 클립보드 붙여넣기 |
| `_pybamm_load_step_to_fields()` | 18320 | 리스트 항목 더블클릭 → 필드 역매핑 |
| `_pybamm_edit_step()` | 18377 | 편집된 필드 → 리스트 업데이트 |
| `_pybamm_collect_list_steps()` | 18418 | QListWidget → PyBaMM 스텝 리스트 추출 |

### 14.8 프리셋 시스템

`_pybamm_load_preset()` — 10개 문헌 기반 파라미터 세트 제공:

| 프리셋 | 충전 패턴 | 방전 패턴 | 전압 범위 |
|--------|----------|----------|----------|
| Chen2020 | 1C + CV@0.05C | 1C | 2.5~4.2V |
| Ai2020 | 1C + CV | 1C | 3.0~4.2V |
| Ecker2015 | 1C + CV | 1C | 2.5~4.2V |
| Marquis2019 | 1C (CC only) | 1C | 3.105~4.1V |
| Mohtat2020 | 1C + CV | 1C | 2.8~4.2V |
| NCA_Kim2011 | 0.5C + CV | 0.5C | 2.7~4.2V |
| OKane2022 | 1C + CV | 1C | 2.5~4.2V |
| ORegan2022 | 1C (CC only) | 1C | 2.5~4.4V |
| Prada2013 | 1C (CC only) | 1C | 2.0~3.6V |
| Ramadass2004 | 1C + CV | 1C | 2.8~4.2V |

### 14.9 안전한 데이터 추출 패턴

```python
def _safe(key):
    """pybamm.Solution에서 안전하게 변수 추출
    
    - 키가 없으면 None 반환 (에러 없음)
    - 2D 배열(공간×시간)이면 axis=0 평균으로 1D 변환
    """
    try:
        arr = sol[key].entries
        if arr is not None and arr.ndim == 2:
            arr = np.mean(arr, axis=0)
        return arr
    except Exception:
        return None
```
