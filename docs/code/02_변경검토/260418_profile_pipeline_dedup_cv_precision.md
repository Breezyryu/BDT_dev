# 260418 프로파일 파이프라인 정리 및 CV 필터 정밀화

## 배경

사이클데이터 탭의 프로파일 분석 기능을 통합 파이프라인(`unified_profile_core`) 하나로 관리하려는 목표가 이전부터 진행 중이었으나, 실제 코드에는 레거시 슬롯·batch loader·파싱 함수가 UI 접근 불가 상태로 남아 있었다. 또한 `include_cv=False` 옵션의 CV 구간 제거가 "스텝 단위 통째 제외"로 구현되어 있어 CC-CV 복합 스텝의 CC 부분까지 함께 잘리는 문제가 있었다. Continue 모드 플롯은 ax5가 누락되어 5축만 채워졌다.

사용자 지시:
1. 통합 파이프라인이 이전 버전의 Step/Rate/Chg/Dchg/Continue 5개 기능을 대체하고 있으므로, hidden 상태로 남아있는 레거시 경로를 제거
2. Continue 모드 플롯의 누락 축(ax5, 방전 C-rate) 복구
3. CV 필터를 레코드 단위 경계로 정밀화하여 CC-CV 스텝의 CC 데이터 보존

## 변경 내용

### A. Continue 플롯 ax5 복구

- `_profile_render_loop`의 `legacy_mode="continue"` 분기에서 ax5에 방전 C-rate 축을 추가.
- ax2는 충전 방향(0 ~ 3.4), ax5는 방전 방향(-3.4 ~ 0.2)로 분리.
- 이전 버전 ECT 플롯(BAK L9432 근처)의 축 구성을 동일하게 복원.

```
DataTool_optRCD_proto_.py (수정 전 기준)
L25247-25258 continue _plot_one → ax1/ax4/ax2/ax3/ax6 (5축)
 ↓
(수정 후) ax1/ax4/ax2/ax5/ax3/ax6 (6축 완성, ax2=충전 Crate 0~3.4, ax5=방전 Crate -3.4~0.2)
```

### B. CV 필터 레코드 단위 경계 정밀화

`_unified_filter_condition`의 CV 구간 제거 로직 업그레이드.

기존 구현(Phase 1):
- `Stepmode ∈ {1, 3}` 인 스텝 **전체** 제외
- 부작용: CC-CV 복합 스텝(Stepmode=1)의 앞부분 CC 레코드도 함께 삭제됨

신규 구현(Phase 2):
- **Stepmode=3 (순수 CV)**: 스텝 전체 제외 (기존 동일)
- **Stepmode=1 (CC-CV 복합)**: 스텝 내 실측 최대 전압을 기준으로 레코드 단위 경계.
  - 물리 근거: CV 단계는 설정 전압을 정전압 유지하므로, 스텝 내에서 관측되는 Voltage의 최대값은 CV 설정 전압과 일치함.
  - 경계 임계: `Voltage >= max_V - epsilon` 인 레코드를 CV 구간으로 판정하여 제외.
  - `epsilon`은 측정 노이즈 허용치 5 mV. Voltage_raw 단위(PNE μV / Toyo V)에 맞춰 자동 선택(5000.0 / 0.005).
  - 그룹핑: `(Cycle, Step)` 단위로 스텝별 최대 전압 계산.
- `.sch` 파싱 없이 동작하므로 PNE/Toyo 공통 적용.

### C. 레거시 프로파일 경로 제거 (통합 완료 후 데드 코드 정리)

#### C-1. UI 엔트리 제거 (hidden 버튼 5개 + 시그널 연결)

제거:
- `Ui_sitool.setupUi` 내 5개 QPushButton 생성 블록 (StepConfirm / ChgConfirm / RateConfirm / DchgConfirm / ContinueConfirm). 모두 `setVisible(False)` 상태였음.
- `Ui_sitool.retranslateUi`의 대응 `setText()` 5줄.
- `WindowClass.__init__`의 5개 `clicked.connect` 시그널 연결.

사용자 영향: 없음. 해당 버튼은 UI에서 보이지 않으므로 클릭될 수 없었음.

#### C-2. 레거시 confirm slot 6개 제거

제거된 슬롯:
- `step_confirm_button`
- `rate_confirm_button`
- `chg_confirm_button`
- `dchg_confirm_button`
- `continue_confirm_button` (단순 분기 wrapper)
- `pro_continue_confirm_button` (continue 분기의 legacy 본체, ~265줄)

대체 경로: `unified_profile_confirm_button` (`ProfileConfirm` 메인 버튼 → `_read_profile_options` → `_map_options_to_legacy_mode` → `_profile_render_loop` → `unified_profile_core`).

#### C-3. ECT 경로 보존 + 참조 정리

- `ect_confirm_button`은 유지 (ECT 테이블/TSV 파일 입력 로직이 특수하여 통합 범위 밖, 사용자 지시로 별도 작업).
- 내부에서 사용하던 `self.ContinueConfirm.setDisabled/setEnabled` 3곳을 `self.ProfileConfirm.setDisabled/setEnabled`로 치환 (ECT가 `unified_profile_confirm_button`에서 분기 호출되므로 동일 버튼을 잠그고 풀어주는 것이 올바름).
- ECT 경로가 여전히 사용하는 `pne_Profile_continue_data`는 보존.

#### C-4. Batch loader 메서드 4개 제거

- `_load_step_batch_task`
- `_load_all_step_data_parallel`
- `_load_profile_batch_task`
- `_load_all_profile_data_parallel`

이 4개는 서로와 제거된 confirm slot에서만 호출되었으므로 데드 코드. 통합 경로는 `_load_unified_batch_task` / `_load_all_unified_parallel`을 사용.

#### C-5. 레거시 파싱 함수 20개 제거 (후속 커밋에서 완료)

제거된 batch loader가 호출하던 단일/배치 파싱 함수 전부가 이번 차수에 caller를 잃었으며, 파이썬 스크립트로 5개 블록을 원자적으로 삭제 (총 704줄):

- **Batch 10개**:
  - `toyo_step_Profile_batch`, `pne_step_Profile_batch`
  - `toyo_rate_Profile_batch`, `pne_rate_Profile_batch`
  - `toyo_chg_Profile_batch`, `pne_chg_Profile_batch`
  - `toyo_dchg_Profile_batch`, `pne_dchg_Profile_batch`
  - `toyo_continue_Profile_batch`, `pne_continue_Profile_batch`
- **Toyo single 5개**: step / rate / chg / dchg / continue (`toyo_*_Profile_data`)
- **PNE single 4개**: step / rate / chg / dchg (`pne_*_Profile_data`)
- **Batch 전용 내부 로더**: `_pne_load_profile_raw` (제거된 batch 4개가 유일한 caller)

보존:
- `pne_Profile_continue_data` — `ect_confirm_button`이 직접 호출 중 (ECT 경로 유지)
- `pne_continue_profile_scale_change` — `pne_Profile_continue_data`와 `pne_dcir_Profile_data`에서 호출
- `_resolve_logical_to_tc_range`, `_get_max_tc` — unified 경로 등에서 사용

구문 검증: Python `ast.parse` 통과, 잔존 참조는 문서 주석 1줄(`unified_profile_batch_continue` 함수 docstring)뿐으로 코드 경로 영향 없음.

## 보류 항목

사용자 지시에 따라 이번 차수에서 제외:
- **ECT path 통합**: `chk_ectpath` 체크 시 `ect_confirm_button`으로 분기하는 흐름을 그대로 두고, TSV 입력 파서만 분리하여 unified 경로에 합치는 리팩터는 보류.
- **DCIR 통합**: `DCIRConfirm` 별도 버튼 + `pne_dcir_Profile_data` 독립 경로. `UnifiedProfileResult.cycfile_soc`에 DCIR 테이블을 담는 Phase 3 작업은 보류.

## 크로스체크 결과 (Rate 통합 검증)

사용자 의견 확인: "Rate는 충전 + 분리겹침 + 시간축과 동등"이 맞음.

- 이전 Rate 데이터 추출 (BatteryDataTool_origin.py L679-729): `Condition==1` 필터 + `Current >= mincrate * mincapacity` 하한 (C-rate 기준 cutoff).
- 현재 `unified_profile_core` (L2298-2304): `data_scope="charge"`일 때 cutoff를 `Crate >= cutoff`로 필터 (C-rate 기준).
- `unified_profile_confirm_button` (L24898 근처): `legacy_mode="step"` (axis_mode=time + data_scope=charge + 비연속)일 때만 `cutoff=mincrate` 전달.

결론: "충전 + 분리겹침 + 시간축" UI 조합이 이전 버전 Rate의 기능과 동등하게 동작. 별도 UI 항목 추가 불필요.

## 파일 변경 요약

- `DataTool_dev/DataTool_optRCD_proto_.py`
  - Continue 플롯 ax5 복구 (`_profile_render_loop` 내 continue `_plot_one`)
  - CV 필터 레코드 단위 경계 (`_unified_filter_condition`)
  - Hidden 버튼 5개 + setText + 시그널 연결 제거 (`Ui_sitool.setupUi/retranslateUi`, `WindowClass.__init__`)
  - Legacy confirm slot 6개 제거
  - ECT 슬롯 내 `ContinueConfirm` → `ProfileConfirm` 참조 치환
  - Batch loader 메서드 4개 제거
  - Legacy 파싱 함수 20개(batch 10 + single 9 + `_pne_load_profile_raw`) 제거 (~704줄)
