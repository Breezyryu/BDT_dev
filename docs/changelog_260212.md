# 변경 이력

## 260205

- 사이클/채널 경로 병렬 처리
- Pandas 3.0 타입 대응: `int64` 컬럼에 문자열 할당 시 `TypeError` → `astype(object)` 선행 변환

## 260206

- **Toyo cycle data 벡터화**: while 루프(O(n²)) → `groupby` + `cumsum`(O(n)), **10.2배 속도 향상**
- merge_rows 함수: 연속 충/방전 그룹 일괄 병합

## 260209

- **`_append` → `pd.concat` 일괄 교체** (17개소, pandas 2.0+ 호환)
- JSON 파일 인코딩 수정 (`encoding='utf-8'`)
- **Step Profile 배치 로딩 최적화**
  - `toyo_step_Profile_batch()` / `pne_step_Profile_batch()` 신규
  - Toyo: `toyo_min_cap()` 채널당 1회 호출 (99.95% 절감)
  - PNE: 인덱스 파일 1회 읽기 + SaveData 범위 일괄 로딩
  - ThreadPool 태스크: 400,000개 → 200개로 축소

## 260210

- **pro_continue_confirm_button 최적화**: 코드 ~33% 감소
  - `global writer` 제거, `check_cycler` 캐싱, early continue 패턴
- **rate/chg/dchg confirm_button 최적화**: 동일 패턴 적용, 코드 24~35% 감소
  - chg 버그 수정: `graph_profile` 중복 호출 삭제
  - dchg 버그 수정: `self.dvscale` → `dvscale` 통일

## 260211

- **PNE search cycle 캐시 최적화**: `@lru_cache(maxsize=32)` 적용, 파일 I/O 40회→2회 (~20배 향상)
- Origin vs optRCD 결과 차이 확인: 3건 의도적 버그 수정만 결과 영향

## 260212~260213

## 1. Toyo 연속 프로파일 사이클 매핑

- **`toyo_build_cycle_map()`** 신규 함수 추가
  - 논리 사이클 번호(1-based) → 원본 파일 번호 범위 매핑 생성
  - `toyo_cycle_data()`와 동일한 재정의 로직 적용 (방전시작 보정, 연속 Condition 병합)
  - 10개 데이터셋, 1000 사이클 검증 완료

- **`toyo_continue_Profile_batch()`** 수정
  - cycle_map 자동 생성 후 논리 사이클 → 파일 범위 변환

- **`pro_continue_confirm_button()`** 수정
  - fallback 경로에서도 cycle_map 변환 적용

## 2. Toyo 연속 프로파일 SOC 수정

- **SOC 부호 보정**: 방전(Condition==2) 시 전류 부호 반전 (`signed_current *= -1`)
  - Toyo 전류는 충/방전 모두 양수 → 방전 시 음수로 변환하여 SOC 정상 산정
- **SOC 시작점**: `increments.cumsum().fillna(0.0)`으로 0에서 시작

## 3. Toyo OCV/CCV 추출 방식 변경

### 문제
- 기존: CAPACITY.LOG의 `Ocv`, `PeakVolt[V]` 컬럼 사용 → 물리적으로 부정확한 값
  - `Ocv` = 스텝 시작 전 전압, `PeakVolt` = 스텝 중 최대 전압

### 수정
- **프로파일 데이터의 Condition 전환점에서 직접 추출**
  - OCV = rest(0) → charge/discharge(1,2) 전환 시, rest 마지막 행 전압
  - CCV = charge/discharge(1,2) → rest(0) 전환 시, 부하 마지막 행 전압
- CycfileSOC AccCap: PNE 방식 적용 (`ChgCap.cumsum() - DchgCap.cumsum()`, `abs()`)

## 4. 빌드 최적화 (`build_exe.bat`)

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| 배포 방식 | `--onefile` (매 실행 수백MB 압축해제) | `--onedir` (폴더 배포, 즉시 실행) |
| UAC | `--uac-admin` (매번 팝업) | 제거 |
| 실행 시간 | 10~30초+ | 1~3초 |

## 5. 의존성 정리

- `scikit-learn` 제거 (pyproject.toml) — 코드에서 미사용 확인

## 260310

### Cycle 플롯 범례/채널팝업 통일 (지정Path vs 직접입력)

- **`indiv_cyc_confirm_button()`** (개별 Cycle)
  - 범례 텍스트를 입력 방식에 관계없이 `extract_text_in_brackets(cycnamelist[-1])`로 통일
  - 기존: 지정Path → 첫 채널만 TSV 이름, 나머지 빈 문자열 / 직접입력 → 채널별 bracket 텍스트
  - 변경: 항상 모든 채널이 개별 범례와 Ch 팝업 항목을 가짐
  - 불필요한 `j` 카운터 변수 제거

- **`overall_cyc_confirm_button()`** (통합 Cycle)
  - LOT 이름 결정 로직을 `lot_name` 변수로 통합 (입력 방식에 따라 소스만 다름)
  - 범례 분기를 `j == i` 단일 조건으로 통일 (기존 3분기 → 2분기)
  - `all_data_name[i]`가 빈 문자열/numpy 타입일 때 범례 누락 문제 수정 (`str().strip()` + fallback)
  - `ch_label` (팝업 그룹)도 `lot_name`으로 통일

### 범례 드래그 기본값 변경

- **`_finalize_cycle_tab()`**: 범례 이동 체크박스(`_drag_legend_chk`) 제거, `set_draggable(True)` 기본 적용
- **`_rebuild_legend()`**: 항상 `new_leg.set_draggable(True)`로 고정
- 설정 저장/불러오기에서 `legend_drag` 항목 제거

### CH 채널 제어 팝업 창 전환

- **`_create_cycle_channel_control()`**: 오버레이 QFrame → 독립 QDialog 팝업으로 변환
  - `QFrame(parent_tab)` → `QDialog(self)` + `WindowStaysOnTopHint` (항상 위에 표시)
  - 플롯과 채널 제어를 동시에 볼 수 있는 UX 개선
  - 오버레이 위치 계산(`_reposition_overlay`), 이벤트 필터(`_OverlayEventFilter`), QSizeGrip 제거
  - 닫기 버튼(`close_btn`) 제거 (QDialog 자체 타이틀바 X 버튼 사용)
  - 다이얼로그 X 버튼 클릭 시 토글 버튼 텍스트 동기화(`closeEvent`)

### CH 제어 Lazy Init (지연 초기화)

- **`_create_cycle_channel_control()`**: 탭 생성 시 토글 버튼만 생성, QDialog는 **첫 CH 클릭 시 초기화**
  - 기존: 탭 생성마다 QDialog + 채널 리스트 + `_orig_colors` 스냅샷 즉시 생성 → 불필요한 오버헤드
  - 변경: `_lazy = {'dialog': None}` → `_ensure_dialog()`로 첫 클릭 시에만 `_build_channel_dialog()` 호출
- **`_build_channel_dialog()`**: 신규 메서드로 분리 — QDialog 생성/채널 리스트/하이라이트/설정 등 전체 로직 포함
  - CH 안 쓰는 탭에서 비용 0, 여러 탭 빠르게 생성할 때 체감 속도 향상

### Cycle 데이터 로딩 I/O 최적화

- **`_load_all_cycle_data_parallel()`**: `subfolder_map` 캐시 반환 추가
  - `os.scandir()` 결과를 `{folder_idx: [subfolder_paths]}` 딕셔너리로 캐싱
  - 반환값: `results` → `(results, subfolder_map)` 튜플로 변경
- **5개 Cycle 함수에서 `os.scandir()` 중복 호출 제거**:
  - `indiv_cyc_confirm_button()`, `overall_cyc_confirm_button()`
  - `link_cyc_confirm_button()`, `link_cyc_indiv_confirm_button()`, `link_cyc_overall_confirm_button()`
  - 기존: 병렬 로더에서 1회 + 플롯 루프에서 1회 = 폴더당 2회 scandir
  - 변경: 병렬 로더 1회만 수행, 플롯 루프에서 `subfolder_map[i]` 참조
- **5개 Cycle 함수에서 `plt.tight_layout()` 중복 제거**:
  - `plt.close()` 직전에 호출되던 불필요한 `plt.tight_layout()` 삭제 (화면 미표시 상태에서 레이아웃 재계산 낭비)

### UI 폰트 통일 (가독성 개선)

- **전체 위젯 폰트**: `맑은 고딕 9pt` → `Pretendard 10pt`로 변경 (392개소)
- **폰트 패밀리 통일**: `맑은 고딕` → `Pretendard` (397개소)
  - 메인 윈도우(`sitool`)가 이미 `Pretendard 10pt` → 내부 위젯과 일관성 확보
- **인라인 QFont 생성자**: `QFont("맑은 고딕", 9)` → `QFont("Pretendard", 10)` (탭2 공통/버튼)
- **테이블 헤더 폰트**: `맑은 고딕 8pt` → `Pretendard 9pt` (1pt 상향)
- 20px 고정 높이 위젯과 호환 유지 (10pt 텍스트 높이 ~13px + 패딩 = ~20px)
