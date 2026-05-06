# PNE Endpoint Index 비교 콘솔 로그 (continuous 모드)

- 일자: 2026-05-06
- 대상: `DataTool_dev_code/DataTool_optRCD_proto_.py`
- 진입점: `unified_profile_confirm_button` (proto_:27948 부근)
- 트리거: 사용자 요청 — ".cyc / SaveData.csv 마지막 파일 / SaveEndData.csv
  의 끝점 index 를 프로파일 전체 사이클 구간 분석 시 콘솔에 비교 출력"

## 동작 요건

`legacy_mode == "continue"` (= overlap "continuous" = "전체 프로파일" preset
또는 시간축 연속 모드) 일 때만 실행. 충전·방전·SOC·DOD·hysteresis 등
다른 모드는 영향 없음.

PNE 폴더만 대상. Toyo 는 `is_pne_folder()` 체크에서 자동 skip.

## 출력 포맷

```
[HH:MM:SS]   [Endpoint Index] <폴더명> (채널 N개) — .cyc / 마지막 SaveData CSV / SaveEndData col[0] 끝점 비교
[HH:MM:SS]     M01Ch025[025]: .cyc=696,087 (rows=696,087) [<name>.cyc] | SaveData=662,011 (rows=614) [chXX_SaveData0014.csv] | SaveEndData=660,873 (rows=541) [chXX_SaveEndData.csv] ⚠ .cyc≠SaveData
[HH:MM:SS]     M01Ch017[017]: .cyc=1,959 (rows=1,959) [...] | SaveData=1,959 (rows=407) [...] | SaveEndData=1,959 (rows=26) [...]
```

- `index` = 각 소스 col[0] 의 마지막 row 값
- `rows`:
  - `.cyc` → 전체 record 수 (= 1-based Index 끝점과 동치)
  - `SaveData` → 마지막 chunk CSV 의 행 수
  - `SaveEndData` → 전체 step 종료 record 수
- `⚠` 플래그:
  - `.cyc ≠ SaveData last endpoint` → 시험 진행 중 .cyc 가 CSV 보다 앞섬
    (`_cached_pne_restore_files` 의 .cyc gap-fill 후보 신호)
  - `SaveEndData > .cyc` → 비정상 (이론상 불가, 데이터 손상 의심)

## 구현 구조

```
_read_pne_endpoint_indices(channel_path) -> dict
   ├─ 1) .cyc           : _parse_cyc_header → 마지막 record FID22 read
   ├─ 2) SaveData chunk : sorted([SaveDataNNNN.csv]) 의 [-1]·col[0] 마지막
   └─ 3) SaveEndData    : SaveEndData.csv col[0] 마지막

_log_pne_endpoint_indices(folders) -> None
   └─ folders 순회 → is_pne_folder skip → 채널 폴더별 읽기 → _perf_logger.info
```

두 함수 모두 PNE 유틸리티 영역(`_cached_pne_restore_files` 직전)에 배치.

`unified_profile_confirm_button` 의 호출 지점은 file writer 셋업 직후
(early-return 통과 후, 데이터 로딩 직전). try/except 로 감싸 로깅 실패가
분석 자체를 막지 않도록 보호.

## 성능

- 채널당 3회 file open + last record read.
- `.cyc` : header 파싱 + 마지막 1 record seek (수 KB I/O)
- `SaveData last chunk` : `usecols=[0]` 로 col[0] 만 로드 (수십~수백 KB)
- `SaveEndData` : `usecols=[0]` 로 col[0] 만 로드 (수 KB)

24 채널 × 3 read ≈ 100 ms 미만, 분석 자체 (수십 초) 에 비해 무시 가능.

## 검증

스모크 테스트 결과 (proto 코드 외부 미니 harness):
- `M01Ch025[025]` (GITT 시험 진행 중): .cyc=696,087 / SaveData=662,011 /
  SaveEndData=660,873 → ⚠ 플래그 정상 발동
- `M01Ch017[017]` (시험 종료): 3 소스 모두 1,959 일치 → 플래그 없음

`python -c "import ast; ast.parse(...)"` 통과.

## 관련 메모리

- `cycle_tab_analysis.md` — 사이클 탭 일반
- `pne_data_characteristics.md` — PNE 파일 체계
- `feedback_changelog.md` — 변경로그 의무
