# BatteryDataTool 웹 전환 계획서
> Confluence Data Center + HP Z8 워크스테이션 기반  
> 작성일: 2026-03-06

---

## 1. 개요

BatteryDataTool의 9개 탭 기능을 HP Z8 워크스테이션(Windows)을 백엔드 서버로 활용하여 웹 전환하고, 사내 Confluence Data Center 9.2.15에 iframe으로 임베딩한다.

**80명 동시 사용 고려 시 Dash(Plotly) 기반 권장** — 기존 Python 코드 최대 재사용 + 프로덕션 수준 동시접속 지원.

---

## 2. 환경 조건

| 항목 | 내용 |
|---|---|
| 서버 | HP Z8 워크스테이션 (Windows 10/11), 상시 가동 |
| 네트워크 | 사내 네트워크 연결, 방화벽 이슈 없음, HTTP 접속 가능 |
| 데이터 접근 | Toyo/PNE 원시 데이터 네트워크 드라이브 매핑 완료 |
| Confluence | Data Center 9.2.15 (온프레미스) |
| 사용자 | 현재 80명, 추후 증가 가능 |

---

## 3. 기능별 웹 전환 가능성

| 탭 | 핵심 기술 | Z8 기반 구현 | 난이도 |
|---|---|---|---|
| **현황 (Status)** | DB 조회, 실시간 테이블 | ✅ | ★★☆ |
| **사이클데이터** | Toyo/PNE 파일 I/O, pandas | ✅ | ★★★ |
| **패턴수정** | 파일 읽기/쓰기, 인터랙션 | ✅ | ★★★ |
| **세트결과** | 배치 처리, ThreadPool | ✅ | ★★★ |
| **ECT** | 데이터 파싱, 그래프 | ✅ | ★★☆ |
| **dV/dQ** | scipy 미분 분석 | ✅ | ★★★ |
| **승인 수명 예측** | curve_fit, 통계 모델 | ✅ | ★★★ |
| **EU 수명 예측** | Arrhenius, 다중 온도 | ✅ | ★★★★ |
| **실수명 예측** | root_scalar, 복합 모델 | ✅ | ★★★★ |
| **PyBaMM 시뮬레이션** | PyBaMM, casadi | ✅ (비동기 큐) | ★★★★★ |

모든 기능 구현 가능. Z8에 네트워크 드라이브가 매핑되어 있어 파일 접근 문제 해결됨.

---

## 4. 아키텍처

```
[80명 사용자 브라우저]
    ↕ (HTTP, 사내 네트워크)
[Confluence 페이지 — iframe User Macro]
    ↕
[HP Z8 워크스테이션 (Windows)] ← http://Z8-IP:8050/
    ├─ Dash (Plotly) 웹앱 — 프론트+백엔드 통합
    │   ├─ 9개 탭 UI (dash-bootstrap-components)
    │   ├─ Plotly.js 인터랙티브 차트 (20+ 그래프 타입)
    │   └─ 콜백으로 사용자 인터랙션 처리
    ├─ pandas, numpy, scipy — 데이터 처리
    ├─ PyBaMM + casadi — 시뮬레이션 (Celery 워커)
    ├─ pyodbc — SQL Server 연결
    ├─ Redis — 작업 큐 + 세션 캐시
    └─ 네트워크 드라이브 — Toyo/PNE 원시 데이터
```

### 4.1 프레임워크 선정: Dash (Plotly)

| 비교 | Streamlit | Dash | FastAPI+React |
|---|---|---|---|
| Python 코드 재사용 | 80% | **85%** | 60% |
| 동시접속 80명 | ❌ 약함 | **✅ waitress 멀티스레드** | ✅ |
| 인터랙티브 차트 | 제한적 | **Plotly 네이티브** | Plotly.js 직접 |
| 커스터마이징 | 낮음 | **중간** | 높음 |
| 프론트 개발 인력 | 불필요 | **불필요** | 필요 |
| 프로덕션 배포 | 어려움 | **waitress (Windows)** | uvicorn |

**선정 사유:**
- **Streamlit 탈락**: 80명 동시접속 시 세션 관리 취약, 멀티워커 미지원
- **FastAPI+React 탈락**: 프론트엔드 전문 인력 필요, 개발 공수 2-3배
- **Dash 선정**: Python만으로 프론트+백, Plotly 네이티브, waitress 멀티스레드로 80명+ 대응

---

## 5. 구현 Phase

### Phase 1: 인프라 + 핵심 코드 분리 (기반)

1. Z8에 Python 환경 구성: conda/venv + 패키지 설치
   - dash, plotly, pandas, scipy, pybamm, redis, celery, waitress, pyodbc
2. 기존 `BatteryDataTool.py`에서 **UI 로직(PyQt6)과 비즈니스 로직(데이터 처리) 분리**
   - 대상 함수: `toyo_read_csv()`, `toyo_cycle_data()`, `pne_cycle_data()`, `separate_series()`, `merge_rows()`, `toyo_build_cycle_map()`, `pne_search_cycle()` 등
   - 순수 Python 모듈로 추출 → `bdt_core/` 패키지
3. 네트워크 드라이브 경로 설정 파일 (`config.yaml`) — Toyo/PNE 데이터 루트 경로
4. Redis 설치 (Windows: Memurai 또는 WSL2 Redis) — 세션 캐시 + Celery 브로커
5. Windows 서비스 등록 (NSSM) — Z8 재부팅 시 자동 시작

### Phase 2: 현황 + 사이클데이터 탭 (MVP)

1. Dash 앱 구조 생성: `app.py` + `layouts/` + `callbacks/` + `bdt_core/`
2. **현황 탭** 구현
   - SQL Server 조회 → `dash_table.DataTable` (16채널 상태 테이블)
   - 색상 코딩 (가동/대기/이상) — `style_data_conditional`
   - 자동 새로고침: `dcc.Interval` (30초 폴링)
3. **사이클데이터 탭** 구현
   - 파일 경로 입력 or 드롭다운 선택 → Toyo/PNE 자동 감지 (`check_cycler()`)
   - `dcc.Graph` + Plotly 차트: `graph_cycle()`, `graph_profile()`, `graph_step()` 대응
   - matplotlib 10색 팔레트 → Plotly colorsequence 변환
   - 프로파일 4종 (Step/Rate/Charge/Discharge) 탭 내 서브탭
4. Confluence iframe 임베딩 테스트
   - User Macro: `<iframe src="http://Z8-IP:8050/" width="100%" height="950px" frameborder="0"></iframe>`
   - CSP/X-Frame-Options 설정 확인

### Phase 3: 데이터 분석 탭들 (*depends on Phase 2*)

1. **패턴수정 탭** — 프로파일 편집 UI (`dash_table.DataTable` 편집 모드)
2. **세트결과 탭** — 배치 분석 결과 테이블 + 그래프
3. **ECT 탭** — 전기화학 테스트 데이터
4. **dV/dQ 탭** — 미분 용량 분석 (scipy + Plotly)
5. 각 탭 공통: Excel 다운로드 버튼 (`dcc.Download` + xlsxwriter)

### Phase 4: 수명 예측 + 시뮬레이션 (*depends on Phase 1의 Redis/Celery*)

1. **승인 수명 예측** — curve_fit + 예측 그래프
2. **EU 수명 예측** — Arrhenius 모델, 다중 온도 데이터셋
3. **실수명 예측** — 복합 열화 모델, 시나리오 시뮬레이션
4. **PyBaMM 시뮬레이션** — Celery 비동기 작업
   - 사용자 요청 → Redis 큐 → Celery 워커 → 결과 반환
   - 진행 상태 표시: `dcc.Interval` 폴링으로 작업 완료 확인
   - 결과 4개 서브탭 (전압곡선, 종합모니터링, 전극분포, dV/dQ)
5. 시뮬레이션 파라미터 프리셋 11종 로드 UI

### Phase 5: Confluence 통합 완성 + 안정화

1. Confluence 다중 페이지 구성 (탭별 별도 iframe 또는 단일 SPA)
2. 분석 결과 → Confluence REST API로 자동 Wiki 페이지 생성 (리포트 아카이빙)
3. 사용자 인증: Confluence SSO와 연계 또는 Windows 인증 (NTLM)
4. 로깅/모니터링: 사용량 추적, 에러 알림
5. 부하 테스트: 80명 동시접속 시나리오 검증

---

## 6. 기술 스택

| 영역 | 기술 | 이유 |
|---|---|---|
| 웹 프레임워크 | **Dash 2.x** (Plotly) | Python 올인원, 80명 동시접속 가능 |
| UI 컴포넌트 | **dash-bootstrap-components** | 탭/테이블/폼 빠른 구현 |
| 차트 | **Plotly.js** (Dash 내장) | matplotlib 1:1 대응, 인터랙티브 |
| 데이터 처리 | **pandas 3.0 + numpy + scipy** | 기존 코드 그대로 |
| 시뮬레이션 | **PyBaMM + casadi** | 기존 동일 |
| 작업 큐 | **Celery + Redis (Memurai)** | PyBaMM 비동기 처리 |
| WSGI 서버 | **waitress** (Windows) | Windows 네이티브, gunicorn 대안 |
| DB | 기존 **SQL Server** (pyodbc) | 변경 없음 |
| Confluence | **User Macro (iframe)** | 가장 단순하고 안정적 |
| 자동 시작 | **NSSM** | Windows 서비스 등록 |
| 설정 관리 | **config.yaml** | 데이터 경로, DB 연결 정보 |

---

## 7. 프로젝트 파일 구조

```
bdt_web/
├── app.py                    # Dash 앱 진입점 + waitress 서버
├── config.yaml               # 데이터 경로, DB 연결, 서버 설정
├── bdt_core/                 # 기존 BatteryDataTool.py에서 추출한 비즈니스 로직
│   ├── __init__.py
│   ├── toyo.py               # toyo_read_csv, toyo_cycle_data, toyo_build_cycle_map
│   ├── pne.py                # pne_cycle_data, pne_search_cycle
│   ├── profile.py            # separate_series, merge_rows, 프로파일 4종
│   ├── analysis.py           # dV/dQ, ECT, DCIR
│   ├── prediction.py         # 수명 예측 3종 (승인, EU, 실수명)
│   ├── simulation.py         # PyBaMM 래퍼
│   └── db.py                 # SQL Server 연결 + 현황 조회
├── layouts/                  # Dash 레이아웃 (탭별)
│   ├── status.py
│   ├── cycle_data.py
│   ├── pattern_edit.py
│   ├── set_results.py
│   ├── ect.py
│   ├── dvdq.py
│   ├── prediction_approval.py
│   ├── prediction_eu.py
│   ├── prediction_real.py
│   └── simulation.py
├── callbacks/                # Dash 콜백 (탭별)
│   ├── status_cb.py
│   ├── cycle_data_cb.py
│   └── ...
├── assets/                   # CSS, 로고
│   └── style.css
├── tasks/                    # Celery 비동기 작업
│   └── simulation_tasks.py
└── requirements.txt
```

---

## 8. 기존 코드에서 추출 대상

| 원본 파일 | 추출 내용 |
|---|---|
| `BatteryDataTool.py` | 모든 데이터 처리/분석/시뮬레이션 함수 원본 |
| `BatteryDataTool_dev/BatteryDataTool_optRCD_proto_.py` | 최적화된 데이터 처리 로직 (벡터화, LRU 캐시) |
| `_toyo_templates.json` | Toyo 장비 패턴 템플릿 |

---

## 9. 80명 동시접속 대응 설계

| 과제 | 해결 방안 |
|---|---|
| 동시 요청 처리 | waitress 멀티스레드 (Windows) 또는 WSL2의 gunicorn 멀티프로세스 |
| 세션 격리 | Dash `session_id` + Redis 세션 스토어 (사용자별 분석 상태 독립) |
| 무거운 연산 | Celery 워커 (PyBaMM, 배치 처리) → 메인 프로세스 블로킹 방지 |
| 캐시 | Redis 캐시 — 동일 파일 재분석 방지 (LRU 전략) |
| 파일 I/O 병목 | 네트워크 드라이브 읽기를 비동기 처리 + 결과 캐싱 |
| Z8 리소스 모니터링 | psutil로 CPU/메모리 사용률 대시보드 추가 (관리자용) |

---

## 10. Confluence 임베딩 설정

### User Macro 생성 (Confluence 관리자)

- **매크로 이름**: `battery-data-tool`
- **Body**:
  ```html
  <iframe src="http://Z8_HOSTNAME:8050/" width="100%" height="950px" 
          frameborder="0" style="border:none;"></iframe>
  ```

### 선행 설정

1. Z8의 Windows 방화벽에서 **포트 8050 인바운드 허용**
2. Confluence `confluence.cfg.xml`에서 `X-Frame-Options` 설정 확인
   - SAMEORIGIN이면 같은 도메인 필요
3. Dash 서버에서 `app.server.config['SESSION_COOKIE_SAMESITE'] = 'None'` 설정

---

## 11. 의사결정 기록

| 항목 | 결정 | 사유 |
|---|---|---|
| 서버 | HP Z8 워크스테이션 | 전용 서버 불필요, 상시 가동 가능 |
| 프레임워크 | Dash (Plotly) | Python 단독, 80명 동시접속, 코드 85% 재사용 |
| Confluence 역할 | iframe 호스트 + 결과 아카이빙 | 단독 구현 불가 |
| Streamlit | 탈락 | 80명 동시접속 미지원 |
| FastAPI+React | 탈락 | 프론트 인력 필요, 공수 2-3배 |
| 차트 엔진 | Plotly.js | matplotlib 대응, 인터랙티브, 기존 팔레트 이식 |
| 우선순위 | 현황+사이클데이터 → 분석 → 예측+시뮬레이션 | MVP 우선 |

---

## 12. 리스크 및 추가 고려사항

### 리스크

1. **Z8 단일 장애점**: 워크스테이션 1대 의존 — UPS 설치 권장, 장애 시 데스크톱 앱 폴백
2. **HTTPS 필수**: Confluence가 HTTPS면 Z8도 HTTPS 필요 (Mixed Content 차단) — 사내 CA 인증서 적용
3. **데이터 백업**: Redis 데이터 + 분석 결과 캐시 주기적 백업 필요

### matplotlib → Plotly 전환 상세

| matplotlib 요소 | Plotly 대응 |
|---|---|
| 10색 팔레트 (#3C5488, #E64B35, ...) | `plotly.io.templates` 커스텀 컬러시퀀스 |
| Dashed grid (α=0.18, #666666) | `layout.xaxis.gridcolor`, `griddash='dash'` |
| Malgun Gothic 폰트 | `layout.font.family='Malgun Gothic'` |
| DPI 150 | Plotly는 벡터 렌더링 (SVG/WebGL), DPI 불필요 |
| NavigationToolbar (zoom, pan, save) | Plotly `modebar` 내장 (동일 기능) |
| Legend (framealpha=0.85) | `layout.legend.bgcolor='rgba(255,255,255,0.85)'` |
