# Plan: 전체 통합(AllProfile) 기능 추가

## 요약

현재 사이클데이터-Profile 탭에는 **사이클 통합**(CycProfile)과 **셀별 통합**(CellProfile) 라디오 버튼만 존재한다.
**전체 통합**(AllProfile)을 추가하여, 모든 셀×사이클 데이터를 하나의 탭(그래프)에 오버레이한다.

- **사이클 통합**: 셀(채널)별 1탭 → 사이클들이 같은 axes에 오버레이
- **셀별 통합**: 사이클별 1탭 → 셀들이 같은 axes에 오버레이
- **전체 통합**: cyclefolder별 1탭 → 모든 셀×사이클이 같은 axes에 오버레이, legend에 `셀이름 사이클번호` 표시

## Steps

### 1. UI 위젯 추가

`CellProfile` QRadioButton 뒤에 `AllProfile` QRadioButton을 추가한다.
- 위치: `self.CellProfile.setObjectName("CellProfile")` / `self.horizontalLayout_15.addWidget(self.CellProfile)` 직후
- 동일한 폰트/사이즈 설정 (맑은 고딕, 9pt)

### 2. retranslateUi 텍스트 설정

`self.CellProfile.setText(...)` 뒤에 `self.AllProfile.setText(_translate("sitool", "전체 통합"))` 추가

### 3. step_confirm_button에 AllProfile 분기 추가

기존 `if self.CycProfile.isChecked():` ... `else:` 사이에 `elif self.AllProfile.isChecked():` 분기를 삽입
- 1개의 fig/tab을 생성한 뒤, 모든 subfolder × CycleNo를 이중 루프로 순회
- lgnd = `셀이름 + " %04d" % Step_CycNo`
- title = `namelist[-2] + " All"`
- 루프 종료 후 1회만 finalize

### 4. rate_confirm_button에 AllProfile 분기 추가

step_confirm_button과 동일한 패턴으로 `elif self.AllProfile.isChecked():` 분기 삽입

### 5. chg_confirm_button에 AllProfile 분기 추가

동일 패턴. chk_dqdv X/Y축 변환 옵션도 반영

### 6. dchg_confirm_button에 AllProfile 분기 추가

동일 패턴. DOD 기반 축 라벨 유지

### 7. pro_continue_confirm_button에 AllProfile 인라인 처리

이 함수는 CycProfile/CellProfile 분기가 없고 단일 루프 구조이므로, 인라인 방식으로 처리:
- 7a. `tab_no = 0` 뒤에 `all_profile = self.AllProfile.isChecked()` 플래그 추가, all_profile이면 사전에 fig/tab 생성
- 7b. 루프 내 fig 생성을 `if not all_profile:` 조건부로 변경
- 7c. lgnd에 AllProfile 분기 추가 (`셀이름 + 사이클번호`)
- 7d. 루프 내 title/finalize를 `if all_profile: last_namelist = step_namelist` / `else: 기존 로직` 조건부로 변경
- 7e. 메인 루프 종료 후 all_profile이면 한번에 title 설정, legend, finalize 실행

## 적용 스크립트

`apply_all_profile.py`를 `BatteryDataTool_260206_edit copy` 폴더에 생성하여 실행하는 방식으로 적용한다.
총 11개 문자열 치환 (1~2: UI, 3~6: 4개 confirm 함수, 7a~7e: pro_continue)

## Verification

- 단일 셀, 단일 사이클: 1탭에 1개 라인
- 복수 셀 × 복수 사이클: 모든 조합이 1탭에 오버레이
- legend에 `셀이름 사이클번호` 형식으로 표시되는지 확인
- Excel 저장 시 모든 데이터가 column 단위로 기록되는지 확인
- 기존 사이클 통합/셀별 통합이 정상 동작하는지 회귀 테스트

## Decisions

- 3개 라디오 버튼이 동일 그룹(horizontalLayout_15) 내에 있으므로 자동 배타적 선택
- AllProfile 분기는 `elif`로 CycProfile과 else(CellProfile) 사이에 삽입
- pro_continue는 구조가 다르므로 인라인 플래그 방식 적용
