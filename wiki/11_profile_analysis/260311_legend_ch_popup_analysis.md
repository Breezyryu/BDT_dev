# 범례(Legend) 및 CH팝업 채널그룹/채널번호 구분 로직 정리

## 0. 공통 구조

모든 Cycle 버튼은 공통적으로 두 개의 딕셔너리를 사용한다:
- **`channel_map`** → CH팝업의 **"채널 그룹"** 영역 (좌측 리스트)
- **`sub_channel_map`** → CH팝업의 **"서브 채널"** 영역 (우측 리스트, 통합/연결 모드에서만 존재)

---

## 1. Toyo / PNE 구분

| 항목 | 로직 |
|------|------|
| **판별 함수** | `check_cycler()`: 폴더 내 `Pattern/` 디렉토리 존재 여부 → PNE=True, Toyo=False |
| **범례/채널 이름에 미치는 영향** | **없음**. Toyo/PNE 구분은 데이터 로딩 함수(`toyo_cycle_data` vs `pne_cycle_data`)만 분기시킬 뿐, 범례/채널 이름 생성 로직은 Toyo/PNE와 **무관** |

---

## 2. 직접입력Path / 지정Path사용

경로 입력은 `pne_path_setting()` 함수에서 3가지 분기로 처리된다:

| 입력 방식 | 조건 | `all_data_folder` | `all_data_name` | 효과 |
|-----------|------|-------------------|-----------------|------|
| **지정Path사용** | `chk_cyclepath` 체크 → TSV 파일 선택 | TSV의 `cyclepath` 컬럼 | TSV의 `cyclename` 컬럼 (**비어있지 않음**) | 범례/ch_label에 `all_data_name[i]` 사용 |
| **직접입력Path** | `stepnum_2` 텍스트 영역에 경로 직접 입력 | 입력된 경로 배열 | **빈 배열 `[]`** | 범례/ch_label에 폴더명 사용 |
| **폴더 직접 선택** | 둘 다 해당 없음 → 폴더 다이얼로그 | 선택된 폴더 배열 | **빈 배열 `[]`** | 범례/ch_label에 폴더명 사용 |

**핵심 차이**: `len(all_data_name) != 0` 여부가 범례 이름과 채널 그룹 이름을 결정한다.

---

## 3. 5가지 그래프 모드별 범례/채널 구분

### 3-1. 개별 Cycle (`indiv_cyc_confirm_button`)

| 항목 | 로직 |
|------|------|
| **그래프** | 폴더(LOT)마다 **별도 figure** 생성 → 별도 탭 |
| **범례 (lgnd)** | `extract_text_in_brackets(cycnamelist[-1])` → 서브폴더명에서 `[CH001]` 같은 대괄호 내용 추출. 없으면 서브폴더명 전체. **지정Path/직접입력 무관하게 동일** |
| **CH팝업 채널그룹 (ch_label)** | `lgnd` 값 (= 대괄호 추출값 or 서브폴더명) |
| **CH팝업 서브채널 (sub_label)** | `cycnamelist[-1]` (서브폴더 전체 이름) |
| **sub_channel_map 전달** | `_finalize_cycle_tab`에 **전달 안 함** → 서브채널 리스트 **미표시** |

### 3-2. 통합 Cycle (`overall_cyc_confirm_button`)

| 항목 | 로직 |
|------|------|
| **그래프** | **모든 폴더를 하나의 figure**에 겹쳐 그림 |
| **범례 (temp_lgnd)** | 지정Path: `all_data_name[i]` (첫 서브폴더만 표시, 나머지 `_nolegend_`) / 직접입력: `cycnamelist[-2].split('_')[-1]` (상위 폴더명의 `_` 뒤) |
| **CH팝업 채널그룹 (ch_label)** | 지정Path: `all_data_name[i]` / 직접입력: `lot_name` (상위 폴더명 기반) → 같은 LOT의 서브폴더들은 **하나의 채널그룹으로 묶임** |
| **CH팝업 서브채널 (sub_label)** | `cycnamelist[-1]` (서브폴더 전체 이름) |
| **sub_channel_map 전달** | `_finalize_cycle_tab`에 **전달됨** → 서브채널 리스트 **표시** |

### 3-3. 연결 Cycle (`link_cyc_confirm_button`)

| 항목 | 로직 |
|------|------|
| **그래프** | 모든 데이터를 **X축 연결** (index offset)하여 하나의 figure에 표시 |
| **범례 (lgnd)** | 지정Path: `all_data_name[i]` (첫 LOT만, 나머지 `""`) / 직접입력: `cycnamelist[-1]` (서브폴더명) |
| **범례 (temp_lgnd)** | 지정Path: `lgnd` 값 / 직접입력: `""` (빈 문자열 → 범례 없음) |
| **CH팝업 채널그룹 (ch_label)** | 지정Path: `all_data_name[i]` / 직접입력: `lgnd` (= 서브폴더명) |
| **CH팝업 서브채널 (sub_label)** | `cycnamelist[-1]` |
| **범례 렌더링** | 지정Path: 각 축별 `ax.legend()` / 직접입력: `plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))` (우측 통합) |
| **sub_channel_map 전달** | `_finalize_cycle_tab`에 **전달 안 함** |

### 3-4. 연결 Cycle 여러개 개별 (`link_cyc_indiv_confirm_button`)

| 항목 | 로직 |
|------|------|
| **입력** | TSV 파일 **여러 개** 선택 (`askopenfilenames`) → 각 파일마다 별도 figure/탭 |
| **범례 (lgnd)** | 지정Path(TSV내 cyclename): `all_data_name[i]` (첫 항목만) / 없으면: `cycnamelist[-1]` (서브폴더명) |
| **CH팝업 채널그룹 (ch_label)** | `temp_lgnd` or `lgnd` or `cycnamelist[-1]` |
| **CH팝업 서브채널 (sub_label)** | `cycnamelist[-1]` |
| **범례 렌더링** | 지정Path(cyclename 존재): 각 축별 legend / 없으면: 우측 통합 범례 |
| **sub_channel_map 전달** | `_finalize_cycle_tab`에 **전달 안 함** |

### 3-5. 연결 Cycle 여러개 통합 (`link_cyc_overall_confirm_button`)

| 항목 | 로직 |
|------|------|
| **입력** | TSV 파일 **여러 개** 선택 → **모든 파일을 하나의 figure**에 X축 연결하여 통합 |
| **범례 (temp_lgnd)** | 지정Path: `all_data_name[i]` (LOT당 첫 항목만) / 직접입력: `cycnamelist[-2].split('_')[-1]` (LOT당 첫 항목만) |
| **CH팝업 채널그룹 (ch_label)** | 지정Path: `all_data_name[i]` / 직접입력: `cycnamelist[-2].split('_')[-1]` → LOT 단위로 묶음 |
| **CH팝업 서브채널 (sub_label)** | `cycnamelist[-1]` |
| **범례 렌더링** | 지정Path: 각 축별 legend / 없으면: 우측 통합 범례 |
| **sub_channel_map 전달** | `_finalize_cycle_tab`에 **전달됨** → 서브채널 리스트 **표시** |

---

## 4. CH팝업 구조 요약

| 요소 | 구성 | 표시 조건 |
|------|------|-----------|
| **채널 그룹** (좌측 리스트) | `channel_map` 기반. `ch_label`이 키. 같은 색상의 artist를 하나의 그룹으로 묶음 | 항상 표시 |
| **서브 채널** (우측 리스트) | `sub_channel_map` 기반. 서브폴더명이 키. `parent` 필드로 상위 그룹 참조 | `sub_channel_map`이 전달되고 2개 이상일 때만 표시 |
| **연동** | 채널 그룹 체크 해제 → 하위 서브 채널도 함께 숨김 | sub_channel_map 있을 때 |

---

## 5. 종합 매트릭스

| 모드 | 지정Path `ch_label` | 직접입력 `ch_label` | 범례 중복 방지 | sub_channel_map 표시 |
|------|---------------------|---------------------|----------------|----------------------|
| **개별** | `[CH001]` 추출값 | `[CH001]` 추출값 | 채널별 1개씩 표시 | X |
| **통합** | `all_data_name[i]` | 상위폴더명 `_` 뒤 | LOT당 첫 항목만 | **O** |
| **연결** | `all_data_name[i]` | 서브폴더명 | LOT당 첫 항목만 | X |
| **연결 여러개 개별** | `all_data_name[i]` | 서브폴더명 | 파일당 첫 항목만 | X |
| **연결 여러개 통합** | `all_data_name[i]` | 상위폴더명 `_` 뒤 | LOT당 첫 항목만 | **O** |
