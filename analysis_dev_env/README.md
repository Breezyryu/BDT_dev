# analysis_dev_env — 데이터 분석 도구 모음

> Raw 데이터 분석 및 사내 환경 전용 스크립트 저장소

---

## 폴더 구조

```
analysis_dev_env/
├── reliability/        ← 신뢰성 데이터 파이프라인 (스캔 → 우선순위 → CSV변환)
├── cycle_category/     ← 사이클 카테고리 자동 분류
├── pne_schedule/       ← PNE .sch 바이너리 파서
└── utils/              ← UI 동기화, 벤치마크, 테스트
```

---

## ★ 사내 작업 체크리스트

사내 PC(Excel + NASCA DRM + Knox Drive)에서만 실행 가능한 작업 목록.

### 1. CSV 변환 실행 — `reliability/convert_reliability_to_csv.py`

Knox Drive의 DRM .xls 파일을 CSV로 변환하는 핵심 작업.

```powershell
# 대상 확인 (dry-run)
python analysis_dev_env/reliability/convert_reliability_to_csv.py "K:\Shared files\rawdata" "E:\reliability_csv" --dry-run

# 최신 폴더 먼저
python analysis_dev_env/reliability/convert_reliability_to_csv.py "K:\Shared files\rawdata" "E:\reliability_csv" --folder 260226

# 전체 변환
python analysis_dev_env/reliability/convert_reliability_to_csv.py "K:\Shared files\rawdata" "E:\reliability_csv"
```

**필요 조건**: Excel, NASCA DRM 플러그인, Knox Drive 마운트  
**상세 매뉴얼**: `docs/code/04_DataTool기술문서/260322_SOP_convert_reliability_to_csv.md`

### 2. 신뢰성 스캔 재실행 (필요시) — `reliability/analyze_reliability.py`

새 데이터 폴더 추가 시 종합현황 재생성.

```powershell
python analysis_dev_env/reliability/analyze_reliability.py "K:\Shared files\rawdata" --auto
```

### 3. mAh 수동 매핑 보완 — `reliability/_mah_manual_mapping.json`

자동 추출 불가한 모델의 용량값을 수동 입력. CSV 변환 품질에 직접 영향.

---

## 폴더별 상세

### `reliability/` — 신뢰성 데이터 파이프라인

| 파일 | 용도 | 실행환경 |
|------|------|----------|
| `analyze_reliability.py` | Knox 전체 스캔 → 종합현황 리포트 | 사내 (--auto, --excel) / 개발 (--meta) |
| `prioritize_ingest.py` | 종합현황 JSON → 인제스트 우선순위 배치 분류 | 개발환경 OK |
| `convert_reliability_to_csv.py` | **★ DRM .xls → CSV 변환** | **사내전용** |
| `_신뢰성_종합현황.*` | 스캔 결과물 (csv/json/txt) | 결과물 |
| `_인제스트_우선순위.*` | 우선순위 결과물 (csv/txt) | 결과물 |
| `_mah_manual_mapping.json` | mAh 수동 입력 매핑 | 결과물 (수동 편집 필요) |

**파이프라인 흐름**: `analyze_reliability.py` → `prioritize_ingest.py` → `convert_reliability_to_csv.py`

### `cycle_category/` — 사이클 카테고리 분류

| 파일 | 용도 | 실행환경 |
|------|------|----------|
| `analyze_cycle_category.py` | 충방전 사이클을 RPT/Rss/가속수명/GITT 등으로 자동 분류 | 개발환경 OK |
| `_사이클카테고리_분석.*` | 분류 결과물 (csv/json/txt) | 결과물 |

### `pne_schedule/` — PNE 스케줄 파서

| 파일 | 용도 | 실행환경 |
|------|------|----------|
| `parse_pne_schedule.py` | PNE .sch 바이너리 → 스텝/충방전 조건 추출 | 개발환경 OK |
| `_scan_sch.py` ~ `_scan_sch7.py` | .sch 구조 분석 과정 (Phase 1~5, 개발 히스토리) | 개발환경 OK |
| `_sch_analysis.json` | 44개 고유 스케줄 교차 분석 결과 | 결과물 |
| `_toyo_templates.json` | Toyo 충방전기 스텝 필드 템플릿 | 결과물 |

### `utils/` — 유틸리티

| 파일 | 용도 | 실행환경 |
|------|------|----------|
| `sync_ui.py` | proto_.py Ui_sitool → .ui XML 역동기화 | 개발환경 OK |
| `_bench_workers.py` | ThreadPool workers 수 벤치마크 | 개발환경 OK |
| `_test_accel_pattern.py` | 가속수명 패턴 추출 로직 단위 테스트 | 개발환경 OK |
