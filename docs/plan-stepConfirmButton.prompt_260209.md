# step_confirm_button 최적화 계획

## 코드 동작 요약

이 함수는 배터리 충방전 **스텝 프로파일 데이터**를 읽어 6개 서브플롯(Voltage×3, SOC, C-rate, Temperature)에 시각화하는 기능이다.

**실행 흐름:**

```
[UI 설정 로드] → [폴더 경로 선택] → [파일 저장 설정] → [3중 루프: 폴더 × 채널 × 사이클]
                                                            ↓
                                                  [Toyo/PNE 판별] → [원시 데이터 읽기 + 단위변환]
                                                            ↓
                                                  [6개 그래프 플롯] → [Excel/CSV 저장] → [탭 생성]
```

**예시 경로 기준 구조:**
```
C:\Users\Ryu\battery\Rawdata\A1_MP1_4500mAh_T23_1\    ← cyclefolder (all_data_folder[i])
├── Channel_01\                                         ← FolderBase (subfolder)
│   ├── 000001                                          ← 사이클 1 원시 데이터 (Toyo)
│   ├── 000002                                          ← 사이클 2
│   └── ...
├── Channel_02\
│   └── ...
└── Pattern\                                            ← PNE 판별 마커 (있으면 PNE)
    └── ...
```

**두 가지 모드** (`CycProfile` 체크박스):
| 모드 | 체크됨 | 체크 안됨 |
|------|--------|-----------|
| 탭 단위 | **채널별 1탭** (사이클들 오버레이) | **사이클별 1탭** (채널들 오버레이) |
| 루프 순서 | 채널 → 사이클 | 사이클 → 채널 |
| 범례 | 사이클 번호 `0001` | 채널명 `Channel_01` |

**핵심 데이터 구조** — `temp[1].stepchg` (DataFrame):

| 컬럼 | 의미 | 단위 |
|------|------|------|
| `TimeMin` | 경과 시간 | 분 |
| `SOC` | 누적 용량 / 기준용량 | 비율 |
| `Vol` | 전압 | V |
| `Crate` | 전류 / 기준용량 | C-rate |
| `Temp` | 온도 | ℃ |

**6개 서브플롯 배치:**
```
[ax1: V vs Time] [ax2: V vs Time] [ax3: V vs Time]         ← 상단: 전압 3중 플롯 (의도적, 축별 확대 용도)
[ax4: SOC vs Time] [ax5: C-rate vs Time] [ax6: Temp vs Time] ← 하단: SOC, C-rate, 온도
```

---

## 최적화 항목

### 1. `global writer` 제거
- **위치:** L9422
- **문제:** `writer`를 `global`로 선언하지만 함수 내부에서만 생성·사용·닫기가 완결됨
- **수정:** `global writer` 라인 삭제, 로컬 변수로만 사용

### 2. `check_cycler` 캐싱
- **위치:** L9452, L9530
- **문제:** 같은 `cyclefolder`에 대해 매 사이클마다 `check_cycler(cyclefolder)` 반복 호출 (결과 불변)
- **수정:** `cyclefolder` 루프 진입 직후 1회만 호출하여 `is_pne = check_cycler(cyclefolder)` 변수에 저장

### 3. 데이터 로딩 병렬화 (ThreadPoolExecutor)
- **문제:** 사이클마다 순차적으로 `toyo_step_Profile_data` / `pne_step_Profile_data` 호출 → I/O 바운드
- **참고:** 다른 함수들(`indiv_cyc`, `overall_cyc`, `link_cyc`)에는 이미 `_load_all_cycle_data_parallel` 적용됨
- **수정:** step 전용 병렬 로딩 함수 `_load_step_data_task` / `_load_all_step_data_parallel` 신규 생성
  - 모든 (폴더, 채널, 사이클) 조합의 데이터를 미리 병렬 로딩
  - 플로팅 루프에서는 캐시된 결과만 사용
  - 기존 `_load_cycle_data_task`와 시그니처가 다름 (`mincrate` 파라미터 추가, `toyo_step_Profile_data` 호출)

### 4. 그래프+저장 공통 함수 추출
- **문제:** 두 모드(CycProfile 체크/언체크)에서 `graph_step` 6회 호출 + Excel 저장 코드가 ~40줄 중복
- **수정:** `_plot_and_save_step_data(self, axes, data, capacity, headername, lgnd, writer, write_col, save_file_name)` 메서드 추출
  - 6개 `graph_step` 호출 통합
  - Excel 저장 로직 포함
  - 갱신된 `write_column_num` 반환

### 5. else 브랜치 들여쓰기 버그 수정
- **위치:** L9545-L9549
- **문제:** `title` 설정 및 `_setup_legend` 호출이 `for FolderBase` 루프 **안** (`if "Pattern" not in FolderBase:` 블록 내)에 위치 → 매 채널마다 반복 실행
- **수정:** `for FolderBase` 루프 **밖**으로 이동 (모든 채널 플롯 완료 후 1회만 실행)

### 6. `step_namelist` 미초기화 방어 코드
- **위치:** L9492
- **문제:** 모든 `subfolder`가 "Pattern"을 포함할 경우 내부 루프 미실행 → `step_namelist` 미정의 → `NameError`
- **수정:** 루프 전 `step_namelist = None` 초기화, `if step_namelist:` 조건 추가

### 7. CSV 저장 시 `.copy()` 사용
- **위치:** L9475-L9480
- **문제:** `temp[1].stepchg["TimeSec"] = ...` 형태로 원본 DataFrame에 직접 열 추가 → `SettingWithCopyWarning`
- **수정:** `continue_df = temp[1].stepchg[["TimeMin", "Vol", "Crate", "Temp"]].copy()` 후 변환 수행

### 8. `tight_layout` 중복 호출 제거
- **위치:** `_finalize_plot_tab` 내부 (L8330) + 함수 마지막 (L9564)
- **수정:** `_finalize_plot_tab` 측에 유지 (각 탭마다 적용), 함수 마지막의 중복 호출 제거

### 9. Voltage×3 플롯 의도 설명 주석 추가
- **위치:** L9456-L9461, L9535-L9540
- **결정:** 의도적 3중 플롯 유지
- **수정:** `# 의도적 3중 플롯: 추후 축별 확대/범위 조정 용도` 주석 추가

---

## 적용하지 않는 항목

- **else 브랜치 CSV 저장 추가:** CycProfile 모드에서만 `ect_saveok` CSV 저장 필요 → 현재 상태 유지

---

## 검증 항목

- [ ] CycProfile 체크 모드: 채널별 탭 생성 + 사이클 오버레이 정상
- [ ] CycProfile 언체크 모드: 사이클별 탭 생성 + 채널 오버레이 + title/legend 1회만 설정
- [ ] Excel `saveok` 저장: 5컬럼씩 증가하며 정상 기록
- [ ] CSV `ect_saveok` 저장: 사이클별 CSV 파일 생성 + 소수점 반올림
- [ ] 모든 subfolder가 "Pattern"인 edge case에서 `NameError` 미발생
- [ ] 병렬 로딩 적용 후 결과가 순차 처리와 동일한지 비교
