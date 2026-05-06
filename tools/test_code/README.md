# BDT 테스트 실행 가이드

## 테스트 구조

```
tests/
├── conftest.py              ← 공통 픽스처 (경로, 데이터, WindowClass)
├── test_path_parsing.py     ← Level A: 헤드리스 (경로 파싱, 콜백 계약, 사이클러 판별)
├── test_smoke_gui.py        ← Level B: GUI 스모크 (pytest-qt, Windows 전용)
└── README.md                ← 이 파일
```

## Level A — 헤드리스 유닛 테스트

**GUI 없이** 실행 가능. 데이터 파싱, 콜백 계약, 경로 파일 읽기, PNE/Toyo 판별.

### 설치 및 실행

```powershell
# 테스트 의존성 설치
pip install pytest

# 기본 실행 (Level A만 — pytest.ini에서 gui 제외 설정)
pytest

# 특정 클래스만
pytest tests/test_path_parsing.py::TestDetectPathColumns -v

# 특정 테스트만
pytest tests/test_path_parsing.py::TestCallbackContract::test_converted_buttons_call_render_loop -v
```

### 테스트 항목 (28개)

| 클래스 | 테스트 수 | 검증 내용 |
|--------|----------|----------|
| `TestDetectPathColumns` | 9 | 헤더 파싱 (4열/2열/ECT/별칭/대소문자 등) |
| `TestSplitNamePathFallback` | 6 | 드라이브 문자/UNC/따옴표 경로 분리 |
| `TestPathFileIntegration` | 5 | 실제 경로 파일 읽기 (basic/linked) |
| `TestCheckCycler` | 3 | PNE/Toyo 사이클러 구분 |
| `TestCallbackContract` | 5 | plot_one_fn/fallback_fn 시그니처, _profile_render_loop 호출 |

---

## Level B — GUI 스모크 테스트

**Windows + PyQt6 + pytest-qt** 필요. 앱을 띄우고 경로 입력 → 버튼 클릭 → 결과 탭 생성 검증.

### 설치 및 실행

```powershell
# 추가 의존성 설치
pip install pytest-qt

# Level B만 실행
pytest -m gui -v

# 전체 실행 (A + B)
pytest -m "" -v

# 특정 시나리오
pytest tests/test_smoke_gui.py::TestDirectPathInput::test_step_confirm_direct -v
```

### 테스트 시나리오

| 클래스 | 시나리오 | 케이스 수 |
|--------|---------|----------|
| `TestAppStartup` | 앱 시작, 탭 존재, 초기 상태 | 3 |
| `TestDirectPathInput` | 직접 경로 → 4버튼 × 3모드 | 12 |
| `TestLinkedPathInput` | 연결처리 on → step/chg 확인 | 2 |
| `TestPathFileLoad` | 경로 파일 로드 → 테이블 확인 | 2 |

### 테스트 매트릭스

```
             CycProfile  CellProfile  AllProfile
step_confirm    ✅           ✅           ✅
rate_confirm    ✅           ✅           ✅
chg_confirm     ✅           ✅           ✅
dchg_confirm    ✅           ✅           ✅

연결처리 off: DirectPathInput 클래스에서 검증
연결처리 on:  LinkedPathInput 클래스에서 검증
경로파일 로드: PathFileLoad 클래스에서 검증
```

---

## 테스트 데이터 의존성

테스트는 `data/` 디렉토리의 실제 데이터를 사용합니다:

| 픽스처 | 경로 | 비고 |
|--------|------|------|
| `sample_path_files` | `data/datapath/경로저장test.txt` 등 | 경로 파일 3종 |
| `toyo_folder` | `data/exp_data/250207_250307_*` | Toyo CSV 데이터 |
| `pne_folder` | `data/exp_data/251028_260428_*` | PNE 바이너리 데이터 |

데이터가 없으면 해당 테스트는 `pytest.skip()`으로 건너뜁니다.

---

## 확장 가이드

### 새 버튼 변환 후 테스트 추가

`continue_confirm_button()`이나 `dcir_confirm_button()`을 `_profile_render_loop()`으로 변환한 경우:

1. `TestCallbackContract`에 해당 버튼 이름을 `buttons` 리스트에 추가
2. `test_each_button_has_unique_data_attr`에 해당 버튼의 `data_attr` 추가
3. `TestDirectPathInput`에 `test_continue_confirm_direct` 등 추가

### 새 파싱 함수 테스트 추가

1. `conftest.py`의 `window_class` 픽스처에 해당 함수 재현 추가
2. `test_path_parsing.py`에 테스트 클래스 추가
