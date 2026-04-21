---
title: "Proto 개선안 우선순위 매트릭스 (상세 제안 병합)"
tags: [bdt-history, improvement, priority, proto]
updated: 2026-04-21
---

# Proto 개선안 우선순위 매트릭스

> 📎 2026-04-21: `260312_proto_improvement_proposals.md`(상세 제안)를 본 파일 말미 "상세 제안 본문" 섹션으로 병합.

> **작성일:** 2026-03-12  
> **기준 파일:** `DataTool_dev/DataTool_optRCD_proto_.py`  
> **소스 문서:** `260312_proto_improvement_proposals.md`(병합 완료), `260312_proto_status_cycle_tab_improvements.md`, `260312_proto_현황_사이클데이터_개선안.md`

---

## 범례

| 기호 | 의미 |
|------|------|
| 난이도 ⭐ | 쉬움 (1일 이내, 코드 변경 ~10줄) |
| 난이도 ⭐⭐ | 보통 (1주 이내, ~30~50줄) |
| 난이도 ⭐⭐⭐ | 어려움 (2~4주, 구조 변경 수반) |
| 기대효과 🔥🔥🔥 | 높음 (체감 즉시, 5배 이상 개선 또는 크래시 방지) |
| 기대효과 🔥🔥 | 보통 (2~3배 개선 또는 유지보수성 향상) |
| 기대효과 🔥 | 낮음 (부분 개선, 누적 효과) |

---

## 1. 난이도 ⭐ (즉시 적용 가능)

| # | 항목 | 카테고리 | 기대효과 | 위치(근거) | 설명 |
|---|------|----------|----------|------------|------|
| E1 | **루프 내 `pd.concat()` → list append** | 속도 | 🔥🔥🔥 | `app_cyc_confirm_button` L10806, `pne_data_make` L13415, `toyo_data_make` L13302 | O(n²)→O(n). 100파일 기준 **25배** 속도 향상. `dfs.append()` 후 마지막 1회 `pd.concat()` |
| E2 | **테이블 `setUpdatesEnabled(False/True)` 래핑** | UI | 🔥🔥🔥 | `toyo_table_make` L13305, `pne_table_make` L13421 | 128셀 렌더링 시 깜빡임 해소. +2줄 추가로 **2~3배** 렌더링 속도 향상 |
| E3 | **`clear()` → `clearContents()`** | UI | 🔥🔥 | `table_reset()` L13532 | 헤더 보존, 재생성 비용 절감. 1줄 수정 |
| E4 | **`match_highlight_text` regex 사전 컴파일** | 속도 | 🔥🔥 | L13539~13555 | 매 호출마다 `import re` + `re.sub()` 반복 → 클래스 레벨 컴파일로 **3~5배** 검색 속도 |
| E5 | **진행률 바 업데이트 누락 보완** | UX | 🔥🔥 | `app_cyc_confirm_button` L10764~10798, `dcir_confirm_button` L12993 | 루프 내 `progressBar.setValue()` + `processEvents()` 추가. +3줄/메서드 |
| E6 | **입력값 유효성 검증 (float 파싱)** | 안정성 | 🔥🔥🔥 | `capacitytext` L10870 | `float()` 실패 시 앱 크래시 → `try/except` + 에러 메시지. ~5줄 |
| E7 | **파일 저장 취소 시 무피드백 해소** | UX | 🔥 | `_setup_file_writer()` L9572 | 저장 다이얼로그 취소 감지 시 명시적 알림 또는 분석 중단 |
| E8 | **검색어 캐싱 (동일 검색어 재파싱 방지)** | 속도 | 🔥 | `match_highlight_text` L13539 | 검색어 변경 시에만 `normalized` + `keywords` 재계산. 128셀 반복 파싱 방지 |

### E등급 기대효과 요약

| 지표 | 적용 전 | 적용 후 |
|------|---------|---------|
| 100파일 app_cyc 병합 | ~25초 | **~1초** (E1) |
| 테이블 렌더링 | ~800ms + 깜빡임 | **~300ms 무깜빡임** (E2+E3) |
| 검색 처리 | ~200ms/128셀 | **~50ms** (E4+E8) |
| 용량값 잘못 입력 시 | 앱 크래시 | **에러 메시지** (E6) |

---

## 2. 난이도 ⭐⭐ (단기 개선, 1주 이내)

| # | 항목 | 카테고리 | 기대효과 | 위치(근거) | 설명 |
|---|------|----------|----------|------------|------|
| M1 | **네트워크 마운트 `subprocess` + timeout** | 보안+안정성 | 🔥🔥🔥 | `network_drive()` L13135~13142 | `os.system()` → `subprocess.run()`. 셸 인젝션 차단 + 반환값 확인 + 타임아웃 처리 |
| M2 | **네트워크 자격증명 `.env` 분리** | 보안 | 🔥🔥🔥 | `mount_*_button()` L13145~13163 | 비밀번호 평문 노출 제거. `.env` + `python-dotenv` + `.gitignore` |
| M3 | **사이클 데이터 캐싱 (설정 해시 기반)** | 속도 | 🔥🔥 | `indiv→overall` 연속 호출 | 동일 설정 반복 실행 시 로딩 시간 **0초** (캐시 히트). ~20줄 |
| M4 | **`app_cyc` 병렬 로딩 (ThreadPoolExecutor)** | 속도 | 🔥🔥 | `app_cyc_confirm_button` L10766 | xlwings COM → `openpyxl` + 병렬화. 파일당 2~3초 → 총 시간 **N배** 단축 |
| M5 | **`global writer` → 로컬화 + try/finally** | 안정성 | 🔥🔥 | 다수 confirm 메서드 | 예외 시 writer 미종료(파일 잠김) 방지. 멀티스레드 경합 제거 |
| M6 | **mount 버튼 6개 → 설정 배열 통합** | 유지보수 | 🔥 | L13145~13163 | 6개 함수 → `DRIVES` 설정 + `functools.partial`. ~30줄 |
| M7 | **`split_value0/1/2` → 단일 `parse_test_name`** | 유지보수 | 🔥 | L13218~13255 | 3개 중복 함수 통합. DRY 원칙 |
| M8 | **네트워크 마운트 상태 피드백 강화** | UX | 🔥🔥 | `mount_all_button()` L13163 | 버튼 텍스트 "TOYO ⏳" → "TOYO ✓/✗" + 상태바 메시지 |
| M9 | **Toyo DCIR 파일 반복 I/O 캐시** | 속도 | 🔥🔥 | L837~847 | 채널 단위 LRU 캐시. 중복 분석 시 **I/O 30~70% 감소** |
| M10 | **검색 디바운스 적용** | UX+속도 | 🔥🔥 | `FindText.returnPressed` L9368 | `returnPressed` → `textChanged` + 250ms 디바운스. 실시간 검색 |
| M11 | **진행률 단계 텍스트 추가** | UX | 🔥🔥 | progressBar 호출부 다수 | `로딩 중 → 병합 중 → 플롯 생성 중 → 저장 중` 상태 표시 |
| M12 | **탭 제목을 데이터셋명 기반으로 변경** | UX | 🔥 | 결과 탭 생성부 | 숫자 `0,1,2` → 파일명/조건명. 다중 결과 비교 시 편의성 |
| M13 | **PNE 개별 프로파일 함수 캐시 적용** | 속도 | 🔥 | `pne_rate/chg/dchg_Profile_data` L2153~2241 | `_pne_load_profile_raw()` 캐시 결과 활용 |

### M등급 기대효과 요약

| 지표 | 적용 전 | 적용 후 |
|------|---------|---------|
| 네트워크 전체 마운트 | 5~60초 UI멈춤 + 에러 무시 | **timeout 10초 + 에러 피드백** (M1+M8) |
| 보안 (암호) | 🔴 소스코드 평문 | ✅ **.env 분리** (M2) |
| 동일 조건 반복 분석 | 매번 전체 로딩 | **캐시 히트 0초** (M3) |
| app_cyc Excel 로딩 | 순차 2~3초/파일 | **병렬 처리** (M4) |

---

## 3. 난이도 ⭐⭐⭐ (중기 리팩토링, 2~4주)

| # | 항목 | 카테고리 | 기대효과 | 위치(근거) | 설명 |
|---|------|----------|----------|------------|------|
| H1 | **`toyo_table_make`/`pne_table_make` 통합** | 유지보수 | 🔥🔥 | L13305~13525 | ~85% 동일 코드. 설정 딕셔너리 + 공통 렌더링 함수로 **~100줄 삭감** |
| H2 | **네트워크 마운트 QThread 비동기화** | UX | 🔥🔥🔥 | `network_drive()` L13135 | 6회 연쇄 호출 UI 블로킹 → QThread로 비동기화. **UI 응답성 100%** |
| H3 | **채널 제어 팝업 디바운싱 + 아이콘 캐싱** | UI | 🔥🔥 | `_rebuild_legend` ~L9968, `_build_channel_dialog` ~L9672 | 100ch+ 연속 클릭 시 450ms→250ms. 아이콘 생성 **5배** 속도 |
| H4 | **DCIR 중첩 루프 Figure 재사용** | 메모리 | 🔥🔥 | `dcir_confirm_button` L12993~13123 | 3중 루프 내 Figure 생성 → `ax.clear()` 재사용. 메모리 조각화 방지 |
| H5 | **`QTableWidget` → `QTableView + QAbstractTableModel`** | 구조+속도 | 🔥🔥🔥 | 현황 탭 전체 | 셀 재생성 근본 해결. 대규모 채널에서 **체감 2배 이상** 응답성 |
| H6 | **`indiv/overall/link` 공통 파이프라인 정리** | 유지보수 | 🔥🔥🔥 | L10870~11360 | 유사 패턴 반복 → `PlotBuildContext` 공통화. 버그/누수 리스크 감소 |
| H7 | **데이터 처리와 UI 로직 분리 (서비스 레이어)** | 구조 | 🔥🔥🔥 | 전체 confirm 핸들러 | 버튼 핸들러에 파일탐색/변환/플롯/저장 혼합 → 서비스 분리 |
| H8 | **Excel 저장 파이프라인 배치화** | 속도 | 🔥🔥 | L10980~11300 | 분석 중 `to_excel` 끼어들기 → 메모리 버퍼 누적 후 일괄 write. **30~70% 단축** |
| H9 | **`groupby().apply()` → 벡터화** | 속도 | 🔥🔥 | Toyo 전처리 L813 | `agg` + 후처리로 치환. **CPU 20~40% 감소** |
| H10 | **PNE `pivot_table` 다중 호출 통합** | 속도 | 🔥 | L1827~1835, L2003 | 동일 집계 1회 groupby/agg로 통합. CPU 15~35% 감소 |
| H11 | **단일 대형 파일 분할** | 구조 | 🔥🔥 | 전체 18,188줄 | UI/I/O/가공/시각화 모듈 분리. 유지보수 근본 개선 |
| H12 | **절대경로/드라이브 의존 제거** | 이식성 | 🔥🔥 | 파일 전반 `d://`, `D://` 등 | `pathlib` + 상대경로 + 설정 파일. 다른 PC 배포 안정성 |
| H13 | **테스트 코드 도입** | 품질 | 🔥🔥 | 없음 (신규) | Toyo/PNE 사이클 매핑 일치, DCIR 회귀, profile batch 동일성 검증 |

### H등급 기대효과 요약

| 지표 | 적용 전 | 적용 후 |
|------|---------|---------|
| 네트워크 전체 마운트 | ~60초 UI멈춤 | **~10초 비동기** (H2) |
| 현황 탭 모델 전환 | 매번 128셀 재생성 | **변경분만 갱신** (H5) |
| 코드 중복 | indiv/overall/link 3벌 | **공통 파이프라인 1벌** (H6) |
| Excel 저장 시간 | 분석+저장 동시 | **분석 후 일괄 저장** (H8) |

---

## 4. 종합 우선순위 매트릭스 (ROI 기준)

```
              기대효과 🔥🔥🔥           🔥🔥              🔥
         ┌──────────────────┬──────────────────┬──────────────────┐
  ⭐     │ ★ E1 pd.concat   │  E3 clearContents│  E7 저장 취소    │
  쉬움   │ ★ E2 setUpdates  │  E4 regex 컴파일 │  E8 검색 캐싱    │
         │ ★ E6 입력 검증   │  E5 진행률 바    │                  │
         ├──────────────────┼──────────────────┼──────────────────┤
  ⭐⭐   │ ★ M1 subprocess  │  M3 데이터 캐싱  │  M6 mount 통합   │
  보통   │ ★ M2 .env 보안   │  M4 병렬 로딩    │  M7 split 통합   │
         │                  │  M5 writer 로컬  │  M12 탭 제목     │
         │                  │  M8 마운트 피드백 │  M13 PNE 캐시    │
         │                  │  M9-11 기타      │                  │
         ├──────────────────┼──────────────────┼──────────────────┤
  ⭐⭐⭐ │ ★ H2 QThread     │  H1 테이블 통합  │  H10 pivot 통합  │
  어려움 │ ★ H5 QTableView  │  H3 디바운싱     │                  │
         │ ★ H6 파이프라인  │  H4 Figure 재사용│                  │
         │ ★ H7 서비스 분리 │  H8 Excel 배치   │                  │
         │                  │  H9 벡터화       │                  │
         │                  │  H11-13 구조     │                  │
         └──────────────────┴──────────────────┴──────────────────┘
           ★ = 최우선 추천 (난이도 대비 효과 최대)
```

---

## 5. 추천 실행 로드맵

### Phase 1: 즉시 적용 (1일) — 체감 개선 극대화

| 순서 | 항목 | 주요 변경 | 기대 결과 |
|------|------|-----------|-----------|
| 1 | E1 | `pd.concat` 루프 제거 | 100파일 병합 25초→1초 |
| 2 | E2+E3 | `setUpdatesEnabled` + `clearContents` | 테이블 깜빡임 해소 |
| 3 | E6 | `float()` try/except | 크래시 방지 |
| 4 | E4 | regex 사전 컴파일 | 검색 3~5배 |
| 5 | E5 | progressBar 업데이트 | 진행률 표시 |

### Phase 2: 단기 개선 (1주) — 보안 + 안정성

| 순서 | 항목 | 주요 변경 | 기대 결과 |
|------|------|-----------|-----------|
| 1 | M2 | `.env` 파일 + `.gitignore` | 암호 평문 제거 |
| 2 | M1 | `subprocess.run` + timeout | 셸 인젝션 차단 + 에러 처리 |
| 3 | M5 | writer 로컬화 + try/finally | 파일 잠김 방지 |
| 4 | M3 | 설정 해시 캐시 | 반복 분석 0초 |
| 5 | M8+M10 | 마운트 피드백 + 검색 디바운스 | UX 개선 |

### Phase 3: 중기 리팩토링 (2~4주) — 구조 개선

| 순서 | 항목 | 주요 변경 | 기대 결과 |
|------|------|-----------|-----------|
| 1 | H6 | indiv/overall/link 공통화 | 중복 제거 + 버그 감소 |
| 2 | H2 | QThread 네트워크 비동기 | UI 응답성 100% |
| 3 | H5 | QTableView + Model | 현황 탭 근본 개선 |
| 4 | H8 | Excel 저장 배치화 | 저장 30~70% 단축 |
| 5 | H12 | 절대경로 제거 | 이식성 확보 |

---

## 6. 카테고리별 요약

### 🛡️ 보안 (최우선)
- **M2** 자격증명 `.env` 분리 — 소스코드 암호 평문 노출 제거
- **M1** `os.system()` → `subprocess` — 셸 인젝션 차단

### ⚡ 속도 (체감 최대)
- **E1** `pd.concat` 루프 제거 — **25배** (가장 적은 노력, 가장 큰 효과)
- **M4** `app_cyc` 병렬 로딩 — **N배**
- **M3** 사이클 데이터 캐싱 — 반복 분석 **0초**

### 🖥️ UI/UX (사용자 체감)
- **E2** `setUpdatesEnabled` — 깜빡임 즉시 해소
- **E6** 입력 검증 — 크래시 방지
- **E5** 진행률 표시 — 작업 상태 투명성
- **H2** QThread — 네트워크 마운트 중 UI 유지

### 🏗️ 구조/유지보수 (장기 투자)
- **H6** 공통 파이프라인 — 3벌 중복 코드 통합
- **H7** 서비스 레이어 분리 — 테스트 가능한 구조
- **H11** 파일 분할 — 18,188줄 단일 파일 해소

---

## 7. 총 아이템 수

| 난이도 | 항목 수 | 기대효과 🔥🔥🔥 | 🔥🔥 | 🔥 |
|--------|---------|-----------------|-------|-----|
| ⭐ 쉬움 | 8개 | 3개 (E1,E2,E6) | 3개 | 2개 |
| ⭐⭐ 보통 | 13개 | 2개 (M1,M2) | 8개 | 3개 |
| ⭐⭐⭐ 어려움 | 13개 | 4개 (H2,H5,H6,H7) | 8개 | 1개 |
| **합계** | **34개** | **9개** | **19개** | **6개** |

---

## 상세 제안 본문 (병합 흡수)

> 원본: `260312_proto_improvement_proposals.md` — 2026-03-12 작성, 현황 탭(네트워크/테이블/검색) + 사이클데이터 탭(사이클/프로필/DCIR) 분석 기반 18,188줄 proto 대상 상세 제안서.

### 8. UX / UI 개선 상세

#### 8.1 현황 탭 — 테이블 깜빡임 해소
- **현상**: FindText 검색어 입력 시 `table_reset()` (L13532)에서 `tb_channel.clear()` → `toyo_table_make()`/`pne_table_make()` 128셀 재생성 → 600~800ms 공백.
- **3가지 선택지**: `clear()`→`clearContents()`(헤더 보존, ⭐), 셀 스타일만 `setForeground/setBackground`(⭐⭐), `setUpdatesEnabled(False/True)` 래핑(⭐).
- **추천 조합**: `setUpdatesEnabled(False)` → 스타일 변경 루프 → `setUpdatesEnabled(True)`.

#### 8.2 현황 탭 — 네트워크 마운트 상태 피드백 강화
- `mount_all_button()` (L13163) 6회 연쇄 호출 시 progressBar 미사용. 버튼 텍스트 "TOYO ⏳"→"TOYO ✓/✗", 상태바 메시지 추가.

#### 8.3 사이클데이터 탭 — 진행률 표시 누락
- `app_cyc_confirm_button()` (L10757) 루프 내 `progressBar.setValue()` 누락 → 0% 고정.
- 추가: `progressBar.setValue(int((i+1)/len(files)*100))` + `QApplication.processEvents()`. `dcir_confirm_button()` (L12993)도 동일.

#### 8.4 사이클데이터 탭 — 입력값 유효성 검증
- `mincapacity = float(self.capacitytext.text())` (L10870) — 숫자 아닌 값 입력 시 **앱 크래시**.
- `try/except ValueError` + `err_msg()` + `setDisabled(False)` + `return`. `_init_confirm_button()` (L9551)에서 통합 처리.

#### 8.5 사이클데이터 탭 — 파일 저장 취소 시 무피드백
- `_setup_file_writer()` (L9572)에서 취소 감지 시 명시적 알림 또는 분석 중단.

#### 8.6 채널 제어 팝업 — 범례 재구축 디바운싱
- 100ch+ 빠르게 연속 클릭 시 `_rebuild_legend()` 매번 호출 → 450ms 블로킹.
- `QTimer.singleShot(100, _rebuild_legend)` 디바운싱으로 250ms 단축.

---

### 9. 데이터 처리 속도 개선 상세

#### 9.1 루프 내 `pd.concat()` — O(n²) → O(n)
- 위치: `app_cyc_confirm_button()` L10806, `pne_data_make()` L13415, `toyo_data_make()` L13302.
- `dfs.append(df)` 후 마지막 1회 `pd.concat(dfs, axis=1)`.
- 100파일 기준: 25초 → 1초 (**25배**).

#### 9.2 검색 함수 — regex 사전 컴파일 + 검색어 캐싱
- `match_highlight_text()` (L13539)에서 매 호출 `import re` + `re.sub()`.
- 클래스 레벨 `_COMMA_RE = re.compile(r'\s*,\s*')` 도입 (3~5배 속도).
- 추가: `self._last_search` 비교 후 달라졌을 때만 `normalized` + `keywords` 재계산 → 128셀 반복 파싱 방지.

#### 9.3 사이클 데이터 캐싱 — 중복 로딩 방지
- indiv→overall 연속 호출 시 `_load_all_cycle_data_parallel()` 2회 수행 (동일 파라미터).
- `cache_key = hash((tuple(sorted(folders)), frozenset(settings.items())))` 기반 인스턴스 캐시.
- 캐시 히트 시 **로딩 시간 0초**.

#### 9.4 테이블 렌더링 배치 최적화
- 현재: 128셀 × 5 Qt 메서드 = 640+ 개별 호출.
- 개선: 아이템 객체 미리 구성 → 일괄 `setItem`, `setUpdatesEnabled` 래핑 → **2~3배** 속도.

#### 9.5 PNE Batch 로딩 — 디스크 I/O 1회화
- 이미 `pne_step_Profile_batch()` (L1009) 최적화됨. 단 `pne_rate/chg/dchg_Profile_data()` (L2153~2241)는 개별 호출 시 여전히 반복 I/O → `_pne_load_profile_raw()` 캐시 결과 활용.

---

### 10. 성능 병목 순위표

| # | 병목 | 위치 | 매 실행 지연 | 난이도 | 기대 개선 | ROI |
|---|------|------|------------|--------|----------|-----|
| 1 | 네트워크 마운트 UI 블로킹 | `network_drive()` L13135 | 5~60초 | ⭐⭐ | UI 응답성 100% | 🔥🔥🔥 |
| 2 | 루프 내 pd.concat() | `app_cyc_confirm_button` L10806 | 1~25초 | ⭐ | 5~25배 | 🔥🔥🔥 |
| 3 | 테이블 렌더링 깜빡임 | `table_make()` L13305+ | 600~800ms | ⭐ | 2~3배 | 🔥🔥🔥 |
| 4 | app_cyc Excel UI 블로킹 | `app_cyc_confirm_button` L10766 | 2~300초 | ⭐⭐ | UI 응답성 | 🔥🔥 |
| 5 | 사이클 데이터 중복 로딩 | indiv→overall 연속 호출 | 3~10초 | ⭐⭐ | 2배 | 🔥🔥 |
| 6 | 검색 regex 반복 컴파일 | `match_highlight_text` L13539 | 200ms | ⭐ | 3~5배 | 🔥🔥 |
| 7 | 채널 제어 Icon 생성 반복 | `_build_channel_dialog` ~L9672 | 200ms (200ch) | ⭐ | 5배 | 🔥 |
| 8 | 범례 재구축 과도 호출 | `_rebuild_legend` ~L9968 | 150ms/회 | ⭐ | N→1회 | 🔥 |
| 9 | DCIR 중첩 루프 Figure 생성 | `dcir_confirm_button` L13057 | 메모리 증가 | ⭐⭐⭐ | 메모리 절감 | 🔥 |

#### 10.1 병목 #1 — 네트워크 마운트 `os.system()` → `subprocess.run()`
```python
subprocess.run(['net', 'use', driver, folder, pw, f'/user:{id}', '/persistent:no'],
               capture_output=True, text=True, timeout=15)
```
또는 QThread(MountWorker)로 비동기화 → UI 미블로킹.

#### 10.2 병목 #2 — 루프 내 `pd.concat()`
```python
dfs = []
for filepath in files:
    dfs.append(load_file(filepath))
result = pd.concat(dfs, axis=1)   # 1회만
```

#### 10.3 병목 #3 — `setUpdatesEnabled(False/True)` 래핑

#### 10.4 병목 #4 — `app_cyc` xlwings COM → openpyxl + ThreadPoolExecutor

#### 10.5 병목 #9 — DCIR 3중 루프 Figure 재사용
- 루프 외곽 Figure 1개 생성 → `ax.clear()` 재사용, 또는 서브플롯 그리드 선할당.

---

### 11. 기타 중요 개선

#### 11.1 🔴 보안 — 하드코딩된 자격증명
- `mount_*_button()` (L13145-13163) 비밀번호 `qoxjfl1!` **소스코드 평문**.
- `.env` + `python-dotenv` + `.gitignore` (난이도 ⭐), 또는 `keyring`(⭐⭐).

#### 11.2 🟡 코드 중복 — `toyo_table_make` / `pne_table_make` 통합
- 두 함수 ~85% 동일 (총 170줄 중 공통 80줄).
- `STATUS_CONFIG` 딕셔너리 + 공통 `_render_table(cycler_type, ...)`로 통합 → ~100줄 삭감.

#### 11.3 🟡 코드 중복 — mount 버튼 6개
- 6개 함수가 1줄씩 `network_drive()` 호출 → `DRIVES` 배열 + `functools.partial`.

#### 11.4 🟡 `split_value0/1/2` DRY 위반
- `parse_test_name(text, index, transform=None)` 단일 함수로 통합.

#### 11.5 🟡 글로벌 `writer` → 로컬화
- `global writer` → `writer, save_path = self._setup_file_writer()` + `try/finally writer.close()`.
- 예외 시 파일 잠김 방지, 멀티스레드 경합 제거. `_setup_file_writer()`가 이미 존재 → 일관 적용만 필요.

#### 11.6 🟡 `os.system()` → `subprocess`
- 셸 인젝션 차단, 반환값으로 성공/실패 판단, 이스케이프 문제 해결.

---

### 12. 병합본 로드맵 (Phase별)

**Phase 1 (난이도 ⭐, 1일 이내)**
1. 루프 내 `pd.concat` → list append (~10줄/메서드) — 5~25배 속도
2. 테이블 `setUpdatesEnabled(False/True)` 래핑 (+2줄) — 깜빡임 해소
3. `clear()` → `clearContents()` (1줄) — 헤더 보존
4. `match_highlight_text` regex 사전 컴파일 (~5줄) — 3~5배
5. 진행률 바 업데이트 (+3줄/메서드)
6. 입력값 유효성 검증 (~5줄) — crash 방지

**Phase 2 (난이도 ⭐⭐, 1주 이내)**
1. 네트워크 마운트 `subprocess` + timeout (~30줄)
2. 자격증명 `.env` 분리 (~20줄+.env)
3. 사이클 데이터 캐싱 (~20줄) — 2배
4. `app_cyc` 병렬 로딩 (~40줄) — N배
5. `global writer` 로컬화 + try/finally (~5줄/메서드)
6. mount 버튼 6개 → 설정 배열 통합 (~30줄)

**Phase 3 (난이도 ⭐⭐~⭐⭐⭐, 2~4주)**
1. `toyo_table_make` / `pne_table_make` 통합 (~100줄 삭감)
2. 네트워크 마운트 QThread 비동기화 (~60줄) — UI 응답성 100%
3. 채널 제어 팝업 디바운싱 + 아이콘 캐싱 (~30줄)
4. DCIR Figure 재사용 (~50줄) — 메모리 절감
5. 색상 규칙 Enum + ColorScheme (~80줄)

### 13. 기대 효과 요약 (상세)

| 지표 | 현재 | Phase 1 후 | Phase 2 후 | Phase 3 후 |
|------|------|-----------|-----------|-----------|
| 테이블 렌더링 시간 | ~800ms (깜빡임) | ~300ms (무깜빡임) | ~300ms | ~200ms |
| 100파일 app_cyc 처리 | ~25초 (UI 멈춤) | ~1초 | ~0.3초 (병렬) | ~0.3초 |
| 네트워크 전체 마운트 | ~60초 (UI 멈춤) | ~60초 | ~60초 (timeout) | ~10초 (비동기) |
| 사이클 반복 실행 | 매번 로딩 | 매번 로딩 | 캐시 히트 0초 | 캐시 히트 0초 |
| 보안 (암호 노출) | 🔴 평문 | 🔴 평문 | ✅ .env 분리 | ✅ .env 분리 |
