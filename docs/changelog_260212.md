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
