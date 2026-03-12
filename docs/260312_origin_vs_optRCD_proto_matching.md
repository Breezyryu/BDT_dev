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
