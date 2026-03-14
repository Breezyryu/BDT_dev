# BatteryDataTool (배터리데이터툴)

배터리 충방전 시험 데이터 분석 및 시각화 데스크톱 애플리케이션입니다.

## 주요 기능

| 탭 | 설명 |
|---|---|
| **현황** | Toyo / PNE 충방전기의 채널별 사용 현황 실시간 모니터링 |
| **사이클데이터** | 충방전 원시데이터로부터 Cycle 수명 및 Profile 분석 |
| **세트 결과** | Battery Status Log 및 ECT(ChemBatt) 결과 분석 |
| **dV/dQ 분석** | 미분 용량 분석 (Differential Voltage Analysis) |
| **패턴 수정** | 충방전 패턴 편집 및 수정 |

## 요구 사항

- Python 3.12 이상
- Windows (ODBC 데이터베이스 연결 및 PyInstaller 빌드 환경)
- 충방전기 DB 접근을 위한 ODBC 드라이버

## 환경 변수 설정 (네트워크 드라이브 인증)

네트워크 드라이브 마운트에 사용되는 인증 정보는 환경 변수로 설정합니다. 소스 코드에 자격증명을 포함하지 마세요.

| 환경 변수 | 설명 | 기본값 |
|---|---|---|
| `BDT_TOYO_USER` | TOYO 드라이브 사용자 이름 | `sec` |
| `BDT_TOYO_PASS` | TOYO 드라이브 비밀번호 | *(없음)* |
| `BDT_PNE_USER` | PNE 드라이브 사용자 이름 | `SAMSUNG` |
| `BDT_PNE_PASS` | PNE 드라이브 비밀번호 | *(없음)* |

Windows 환경 변수 설정 예시:

```bat
set BDT_TOYO_PASS=your_toyo_password
set BDT_PNE_PASS=your_pne_password
python DataTool.py
```

또는 시스템 환경 변수로 영구 설정:

```powershell
[System.Environment]::SetEnvironmentVariable("BDT_TOYO_PASS", "your_toyo_password", "User")
[System.Environment]::SetEnvironmentVariable("BDT_PNE_PASS", "your_pne_password", "User")
```

## 의존성 설치

[uv](https://github.com/astral-sh/uv) 패키지 매니저를 사용합니다.

```bash
uv sync
```

또는 pip을 사용할 경우:

```bash
pip install -e .
```

## 실행

```bash
python DataTool.py
```

## 빌드 (Windows 실행 파일 생성)

단일 실행 파일 (`DataTool.exe`):

```bat
build_exe_onefile.bat
```

폴더 배포 방식:

```bat
build_exe_onepath.bat
```

UI 파일 재생성 (`.ui` → `.py`):

```bat
build_ui.bat
```

## 프로젝트 구조

```
BDT_dev/
├── DataTool.py              # 메인 애플리케이션
├── DataTool.ico             # 애플리케이션 아이콘
├── DataTool_dev/            # 개발용 디렉토리
│   ├── DataTool_UI.py       # Qt6 UI 생성 코드
│   └── DataTool_UI.ui       # Qt Designer UI 정의 파일
├── docs/                    # 기술 문서 및 SOP
├── build_exe_onefile.bat    # 단일 실행 파일 빌드 스크립트
├── build_exe_onepath.bat    # 폴더 배포 빌드 스크립트
├── build_ui.bat             # UI 파일 컴파일 스크립트
└── pyproject.toml           # 프로젝트 설정 및 의존성
```

## 문서

상세 사용법은 [`docs/`](docs/) 디렉토리의 SOP 문서를 참고하세요.

- [현황 탭 SOP](docs/SOP_현황탭_PPT.md)
- [사이클데이터 탭 SOP](docs/SOP_사이클데이터탭_PPT.md)
- [세트 결과 탭 SOP](docs/SOP_세트결과탭_PPT.md)
- [dV/dQ 분석 탭 SOP](docs/SOP_dVdQ분석탭_PPT.md)
- [패턴 수정 탭 SOP](docs/SOP_패턴수정탭_PPT.md)
