# 사내환경 검증 체크리스트 — 2026-04-23 ~ 04-27 변경분

날짜: 2026-04-27
대상: `DataTool_dev_code/DataTool_optRCD_proto_.py`
범위: main 브랜치 4월 23일 이후 모든 커밋 (성능 개선 + 버그 수정 + UI 개선)

## 검증 대상 변경 요약 (날짜·커밋 기준)

| 날짜 | 커밋 | 카테고리 | 핵심 변경 | 위험도 |
|---|---|---|---|---|
| 04-23~24 | `41e27a6` (우리) | 성능 | T1 Quick Win 5건 + T2-A DF 복사 + T2-B UI signal | 중 |
| 04-26 | `7b1a90c` | 성능 | 현황 탭 mtime/size 캐시 + 벡터화 + 렌더 배치 | 중 |
| 04-26 | `8bb99fc` | **버그수정★** | PNE .sch 파싱 type_code swap + offset 의미 정정 | **높음** |
| 04-26 | `4de694e` | 버그수정 | 채우기 버튼: 연결처리 그룹 첫 행만 | 중 |
| 04-26 | `169813f` | UI | 경로 테이블 paste 헤더 검출 + 연결처리 즉시 hint | 저 |
| 04-25~26 | `96706ea` | 성능 | 경로 테이블 confirm 진행률 + 캐시 일관성 | 중 |
| 04-25~26 | `d259e56` | 성능 | 경로 테이블 자동 채우기 light/full 트리거 분리 | 중 |
| 04-25 | `139eb22` | 리팩터링 | `_resolve_path_meta_light` 분리 | 저 |
| 04-25 | `319b495` | 성능 | `check_cycler` / `_quick_max_cycle` 캐시 패치 | 중 |
| 04-25 | `196fc4d` | 버그수정 | PNE CCCV 단계 휴리스틱 (`8bb99fc`에서 revert) | — |
| 04-25 | `adc3bcb` | **버그수정** | Toyo Cycle 컬럼 step 단위 → 논리사이클 매핑 | **높음** |
| 04-25 | `2085ae5` | 버그수정 | 1-6 Rest End V `RndV` 사용으로 원복 | 중 |

---

## 0. 사전 준비 (사내 환경)

### 0.1 환경
- [ ] BDT 최신 main 동기화: `git pull --rebase --autostash origin main`
- [ ] `git log --oneline -10` 결과에 `41e27a6` 포함 확인
- [ ] PyQt6 / numpy / pandas / matplotlib 버전 변동 없음 확인 (`pip list | findstr "PyQt6 numpy pandas matplotlib"`)
- [ ] Phase 0 캐시 stale 우려 시: 앱 시작 후 첫 실행은 **`_reset_all_caches()`** 또는 BDT 메뉴 "캐시 전체 초기화" 1회 실행
- [ ] **`8bb99fc` 영향**: 모든 PNE cycle_map / classified / accel_pattern이 변경되므로 Phase 0 캐시는 첫 실행 시 자연 재계산 — **이전 사이클 결과와 차이 발생 가능, 정상**

### 0.2 NAS 마운트
- [ ] `Y:\ X:\ W:\ V:\ U:\` 모두 정상 (mount UI 점등 확인)
- [ ] 마운트 안 됐을 때 `os.path.isdir()` 폴백 정상 동작 확인 (UI freeze 없음)

### 0.3 기준 데이터셋 5종 확보 (사내)
- [ ] **A. PNE 일반 수명** — TC ≥ 1000, 채널 ≥ 5 (예: Q8 ATL Main 2.0C Rss RT)
- [ ] **B. PNE Sweep (GITT)** — Sweep 모드 시험 (TC 다수 / 논리사이클 적음)
- [ ] **C. PNE mkdcir (가속수명)** — RSS + 1s pulse + SOC70 (Gen4/Q8 가속)
- [ ] **D. Toyo 일반 수명** — Q7M 패턴 (예: 101-200/201-300/301-400cyc 3그룹)
- [ ] **E. Toyo + PNE 혼합 연결처리** — 양쪽 cycler를 link로 묶어 연결 모드

### 0.4 비교 기준 (선택)
- [ ] 가능하면 `41e27a6` **이전 빌드**로 동일 데이터 1회 로딩 → 엑셀 출력 보존
- [ ] 또는 main `7b1a90c` 시점 빌드 보존본 활용

---

## 1. PNE .sch 파싱 정정 (`8bb99fc`) — **최우선 검증**

### 1.1 충방전 패턴 표시 변화
- [ ] **Q8 ATL Main 2.0C Rss RT** 패턴 표시 확인 (capacity 2369mAh):
  - [ ] 1st: `CC 2.0C/4.14V` (이전 `CC 2.0C/4.30V` 또는 `CCCV`)
  - [ ] 2nd: `CC 1.65C/4.16V`
  - [ ] 3rd: `CCCV 1.40C/4.30V/0.99C cutoff`
  - [ ] 4th: `CCCV 1.0C/4.55V/0.10C cutoff`
- [ ] 방전 step의 voltage cutoff 표시 정상 (예: `V<3.65`/`V<3.0`)
- [ ] Toyo 시험은 **불변** (Q7M 패턴 그대로 — Toyo 별도 경로)

### 1.2 cycle_map / classified 영향 확인
- [ ] PNE 동일 시험을 다시 로딩 → cycle_map의 RPT/Rss/가속 분류가 변할 수 있음
- [ ] 만약 분류가 크게 바뀌면 **재학습 데이터셋 vs 신규 데이터셋** 충방전 패턴 비교
- [ ] 회귀 신호: 같은 시험인데 사이클바 색깔 분류가 완전히 달라짐 → `_perf_logger` 로그 확인 + `196fc4d`/`8bb99fc` 변경 의도 재학습

---

## 2. Toyo Cycle 컬럼 논리사이클 매핑 (`adc3bcb`) — **최우선 검증**

### 2.1 그래프 x축
- [ ] **Q7M 101-200cyc** 사이클 분석 → x축 `1..104` (이전 `1..496`)
- [ ] **Q7M 201-300cyc** → x축 `1..102`
- [ ] **Q7M 301-400cyc** → x축 `1..102`
- [ ] 연결처리 모드: 누적 x축 `1..308` (이전 `1..1492`, step 단위 무의미했음)

### 2.2 OriCyc 컬럼
- [ ] 엑셀 "방전용량" 시트의 OriCyc 열은 **step 단위 그대로** (디버깅용)
- [ ] 그래프 표시는 논리사이클 = `Cycle` 컬럼

### 2.3 PNE 회귀
- [ ] PNE 시험 (Q8/Gen4) 그래프 x축 변화 없음 — 기존과 동일

### 2.4 cycle_map 매핑 실패 폴백
- [ ] `cycle_map=None` 또는 비정상 데이터에서 OriCyc 그대로 표시되는지 (크래시 없음)

---

## 3. 우리 변경 (`41e27a6`) 검증

### 3.1 T1-A — lru_cache maxsize 확장
- [ ] 채널 ≥ 50 시험 5개 동시 로딩 후 **두 번째 로딩** 시간 측정 → 기존 대비 단축
- [ ] `_perf_logger` 로그에 `_find_sch_file` / `_get_pne_sch_struct` 호출 횟수 확인 (cache hit 비율 ↑)
- [ ] 메모리 사용량: Task Manager로 BDT 프로세스 RSS 모니터링 — 전체 +수 MB 이내 (8GB RAM 압박 없음)

### 3.2 T1-B — Toyo DCIR 병렬 I/O
- [ ] **D 데이터셋** (Q7M, DCIR 포함) 로딩
- [ ] DCIR 그래프 표시 정상 (값·번호 동등)
- [ ] **NAS 환경에서 시간 측정** — 기존 1~2s → 300~500ms (DCIR 사이클 多 시험)
- [ ] 의도적 차이: 비정상 사이클(0-전류)에서 기존 크래시 → **신 skip**. 만약 NaN cycle 발생 시 `_perf_logger.warning` 확인
- [ ] `dcir.loc[cyc, "dcir"]` 값을 1개 cycle 기준 기존과 수동 비교

### 3.3 T1-C — mkdcir DataFrame 통합
- [ ] **C 데이터셋** (Gen4/Q8 가속수명) 로딩
- [ ] 엑셀 시트 `RSS`, `DCIR`, `RSS_OCV`, `RSS_CCV`, `SOC70_DCIR`, `SOC70_RSS` 모두 정상 출력
- [ ] 각 시트의 OriCyc / 값 컬럼이 기존과 동일
- [ ] dcir2 (1s pulse), rssocv, rssccv 모두 NaN 아닌 정상 값

### 3.4 T1-D — Toyo Condition 1-pass numpy mask
- [ ] **D 데이터셋** 로딩
- [ ] 충전용량 / 방전용량 / DCIR 시트 값 동등
- [ ] Finish 컬럼에 공백 17자 + "Tim" 변형이 있는 데이터로 dcir 분류 확인 (PNE 6 / TOYO 5 일부에서 발생)

### 3.5 T1-E — Sweep TC→logical bisect
- [ ] **B 데이터셋** (GITT) 로딩
- [ ] `_LogicalCyc` 컬럼이 엑셀에 출력됨 (sweep 시험만)
- [ ] 사이클바의 논리사이클 라벨이 기존과 동일
- [ ] 매우 큰 sweep (TC > 5000) 시험에서 로딩 즉각성 체감

### 3.6 T2-A — `_process_pne_cycleraw` 리팩토링
- [ ] **A/B/C 데이터셋** 모두 로딩 후 `df.NewData` 컬럼 세트 동일:
  - `Cycle, Dchg, RndV, Eff, Chg, DchgEng, Eff2, dcir, dcir2, rssocv, rssccv, soc70_dcir, soc70_rss_dcir, Temp, AvgV, OriCyc, RndV_chg_rest, RndV_dchg_rest`
  - Sweep만 `_LogicalCyc` 추가
- [ ] 엑셀 출력 시트 수·이름·열 순서 변동 없음 (binary diff 또는 시트별 dataframe 비교 권장)
- [ ] chkir 모드: dcir 값 동일 (또는 첫 행 0 더미만 있음)
- [ ] mkdcir 모드: 4개 DCIR 컬럼 모두 정상

### 3.7 T2-B — `_pump_ui` signal 재설계
- [ ] 모든 사이클 분석에서 progressBar 0→100 순차 증가
- [ ] 진행률 역전·누락 없음
- [ ] 로딩 중 UI freeze 없음 (마우스 hover, 다른 탭 클릭 반응 정상)
- [ ] **워커 크래시 없음** (Python 콘솔에 `QObject::setParent` 류 경고 없음)
- [ ] `_PipelineProgress` 와 `_WorkerSignals` 두 클래스 공존 — `from PyQt6` import 에러 없음

---

## 4. 경로 테이블 Step 1~6 검증 (`319b495` ~ `169813f`)

### 4.1 자동 채우기
- [ ] **A 시험 경로** 입력 → 시험명/채널/용량/사이클 자동 채워짐
- [ ] **light/full 분리**: 경로 입력 직후는 light(빠름), confirm 시 full(완전 메타)
- [ ] confirm 진행률 표시 (statusBar에 `채우기 N/M`)
- [ ] 두 번째 같은 경로 입력 시 즉시 채워짐 (캐시 히트)

### 4.2 채우기 버튼 (`4de694e`)
- [ ] 연결처리 체크 + 채우기 버튼 클릭 → **그룹 첫 행만** 채워짐, 후속 행 빈 칸
- [ ] 비연결처리 + 채우기 → 모든 행 채워짐
- [ ] 후처리 (하이라이트, mismatch 표시) 정상

### 4.3 paste 헤더 검출 (`169813f`)
- [ ] 엑셀에서 헤더 포함 영역 복사 → 사이클 테이블에 paste → **헤더 자동 skip**
- [ ] 첫 줄에 단일 셀만 있을 때 (헤더 아닌 경우) 그대로 paste
- [ ] 연결처리 토글 시 그룹 hint 즉시 갱신 (행 색상)

---

## 5. 현황 탭 (`7b1a90c`) 검증

### 5.1 캐시 동작
- [ ] **현황 탭 클릭** → 첫 로딩 시간 측정
- [ ] 동일 탭 다시 클릭 → 캐시 hit으로 즉각 표시
- [ ] 파일 mtime 변경 후 새로고침 → 캐시 무효화, 재파싱 (변경 반영)
- [ ] 롤백 스위치: `_status_cache_enabled = False` 로 변경 시 기존 동작

### 5.2 testname 벡터화
- [ ] split 결과 23/23 등가 (이전 결과와 비교, 또는 변경로그 기재된 테스트 통과)
- [ ] 롤백 스위치: `_vectorize_split = False` 로 기존 apply 방식 작동

### 5.3 렌더 배치
- [ ] toyo_table_make / pne_table_make 그리는 동안 깜빡임 줄어듦 (`setUpdatesEnabled` 효과)
- [ ] 그리는 도중 다른 탭 클릭 시 안전하게 전환

---

## 6. 1-6 Rest End V 원복 (`2085ae5`) 검증

- [ ] 사이클 분석 실행 → **탭1 1-6 ax6** 에 **3.0V 근처** scatter 표시 (방전 후 OCV)
- [ ] 탭2 2-6 에 동일 3.0V 근처 (같은 `RndV` 사용)
- [ ] 탭2 2-5 는 **4.1V 근처** (`RndV_chg_rest`, 만충 OCV)
- [ ] 탭1 ax6 ylim = 3.00–4.00V 복구
- [ ] 1-6 범례 라벨 정상 표시

---

## 7. 사내 특화 회귀 (Fasoo / NASCA / 신뢰성)

### 7.1 Fasoo DRM (.xls)
- [ ] 신뢰성 .xls 파일 로딩 시도 → COM 정상 (사외 환경 에러는 무관)
- [ ] Fasoo 프로세스 훅 환경에서 BDT 출력 .xlsx 생성 정상 (사용자 메모리: 첫 줄 공란 .txt 통과 트릭)

### 7.2 NASCA DRM PDF
- [ ] 사내 PDF 로딩 시 `<## NASCA DRM FILE -` 헤더 감지 시 명시적 에러 메시지
- [ ] 일반 PDF는 정상 처리

### 7.3 사외 PC와 결과 동등성 (가능 시)
- [ ] 사내 NAS 데이터 → 사외 동일 데이터 사본 → 두 환경 엑셀 출력 비교
- [ ] 차이 있을 시 NAS 경로 인코딩 / Fasoo 영향 / 캐시 stale 가능성 검토

---

## 8. 성능 측정 (Quantitative)

### 8.1 표준 시험 로딩 벽시계 측정
- [ ] **A 데이터셋** 로딩: 시작 → 모든 탭 그래프 표시 완료 시간 (스톱워치)
  - [ ] 목표: 기존 20~30s → 8~15s
- [ ] **C 데이터셋** (가속수명) 동일 측정
  - [ ] 목표: 기존 30~60s → 12~20s
- [ ] **D 데이터셋** (Toyo) 동일 측정
  - [ ] 목표: 기존 15~25s → 8~12s

### 8.2 cProfile (선택, 정밀 분석용)
```python
import cProfile, pstats
prof = cProfile.Profile()
prof.enable()
# ... 사이클 분석 1회 실행
prof.disable()
pstats.Stats(prof).sort_stats('cumulative').print_stats(30)
```
- [ ] `_process_pne_cycleraw`, `_load_cycle_data_task`, `toyo_cycle_data` 누적 시간 비교
- [ ] `_pump_ui` 호출 비용이 무시 가능 (≤ 1ms)

### 8.3 메모리
- [ ] Task Manager 또는 `tracemalloc` 으로 최대 RSS 측정
- [ ] 8GB RAM 환경에서 1.5GB 초과 안 함 (T2-A 효과로 ~30% 감소 기대)

---

## 9. 회귀 (이전 결과와 동등성)

### 9.1 엑셀 시트 동등성
사전에 보존한 이전 빌드 출력본과 비교:
```python
import pandas as pd
import openpyxl

before = pd.read_excel("before.xlsx", sheet_name=None)  # 모든 시트 dict
after = pd.read_excel("after.xlsx", sheet_name=None)
for name in before:
    pd.testing.assert_frame_equal(
        before[name].fillna(-999), after[name].fillna(-999),
        check_dtype=False, check_exact=False, rtol=1e-9)
```
- [ ] **A/D 데이터셋**: 모든 시트 일치 (단, Toyo의 Cycle 열은 `adc3bcb` 영향으로 step→논리 변환 차이 발생 — 의도된 변화)
- [ ] **C 데이터셋**: dcir/dcir2/rssocv/rssccv/soc70 시트 모두 동등
- [ ] **B 데이터셋** (Sweep): `_LogicalCyc` 열 추가됨 외 동등

### 9.2 의도된 차이 (회귀 아님)
- [ ] **PNE 충방전 패턴 표시**: `8bb99fc` 영향으로 voltage / cutoff 값이 정확해짐 (이전 부정확)
- [ ] **Toyo Cycle 컬럼**: `adc3bcb` 영향으로 step → 논리사이클 (그래프 x축 자릿수 줄어듦)
- [ ] **PNE classified 분류**: cv_cutoff 의미 정정으로 RPT/Rss 분류가 변할 수 있음 — 시험자에게 확인

---

## 10. 롤백 절차 (이상 발견 시)

### 단일 커밋 롤백
- [ ] 우리 커밋만 롤백: `git revert 41e27a6 -m 1`
- [ ] PNE .sch 정정 롤백: `git revert 8bb99fc` (단, accel_pattern 표시가 다시 부정확해짐)
- [ ] Toyo Cycle 매핑 롤백: `git revert adc3bcb`

### 부분 롤백 (모듈 상단 flag)
- [ ] `_status_cache_enabled = False` (현황 탭 캐시)
- [ ] `_vectorize_split = False` (testname 벡터화)
- [ ] T1/T2 변경은 flag 없음 — git revert만 가능

### 캐시 stale 의심 시
- [ ] `_reset_all_caches()` 호출 → Phase 0부터 재계산
- [ ] BDT 메뉴 "캐시 전체 초기화" 1회 실행

---

## 11. 보고서 양식 (검증 결과)

검증 완료 후 다음 양식으로 정리하여 `docs/code/02_변경검토/260427_inhouse_validation_report.md` 생성 권장:

```markdown
# 사내 검증 결과 — 2026-04-23~04-27 변경분

## 환경
- BDT 빌드: <git commit sha>
- NAS 마운트: <Y/X/W/V/U 상태>
- 데이터셋: <A/B/C/D/E 파일 경로>

## 결과 요약
| 검증 항목 | 결과 | 비고 |
|---|---|---|
| ... | PASS / FAIL / N/A | ... |

## 회귀 발견 사항
1. ...

## 성능 비교
| 시나리오 | Before | After | 단축 |
|---|---|---|---|
| ... | 30s | 12s | 60% |

## 후속 조치
- ...
```

---

## 우선순위 권장

**Day 1 (1시간 내)**:
1. §0 환경 준비
2. §1 PNE .sch 파싱 (Q8) — accel_pattern 표시 확인
3. §2 Toyo Cycle 매핑 (Q7M) — 그래프 x축 확인
4. §8.1 A/D 데이터셋 로딩 시간 측정

**Day 2 (반나절)**:
5. §3 우리 변경 6개 항목 (T1-A~T2-B)
6. §4 경로 테이블
7. §5 현황 탭
8. §9 엑셀 동등성

**선택**:
9. §6 Rest End V (이미 main 정착 — 재검증)
10. §7 사내 특화 (Fasoo/NASCA)
11. §8.2 cProfile

---

## 비상 연락 / 책임자

문제 발생 시:
- 우리 변경 (`41e27a6`): 본 작업자에게 슬랙
- main 다른 변경: 각 커밋 메시지의 Author 참조
- 캐시 stale 의심: `_reset_all_caches()` 1회 + 재시도
