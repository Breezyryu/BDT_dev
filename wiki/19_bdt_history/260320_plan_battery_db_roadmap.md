# BDT 배터리 데이터 DB화 로드맵

> 작성일: 2026-03-20  
> 상태: Phase 1 준비 중  
> 관련 instruction: `.github/instructions/database.instructions.md`

---

## 1. 배경 및 목적

### 현재 문제점
- 수명 데이터가 **충방전기 raw 폴더(CSV/바이너리)** 에 분산 저장 → 모델 비교 시 매번 전체 파싱 필요
- Toyo CSV 1개 폴더 로딩 2~5초, 10개 모델 비교 시 **20~50초 소요**
- 신뢰성 .xls 파일은 **NASCA DRM 암호화** → xlwings COM만 읽기 가능
- Knox Drive(K:\)는 가상 클라우드 드라이브, I/O ~9.2초/폴더
- 모델 간 비교 시 동일 조건 폴더를 직접 찾아 일일이 로딩해야 함

### 목표
1. **PostgreSQL DB에 수명 데이터를 적재**하여 `SELECT` 한 번으로 다중 모델 비교
2. DB 서버를 **별도 서버에 배치** (사내 서버 또는 NAS)
3. BDT에서 **빠른 속도로 데이터 로드 → 비교 → 분석 → 시각화** 파이프라인 구현
4. 수명(cycle life)부터 시작, **추후 하나씩 항목 추가**

---

## 2. 아키텍처

### 2.1 전체 구조

```
┌──────────────┐     네트워크(TCP 5432)     ┌──────────────────┐
│  BDT 클라이언트 │ ◄──────────────────────► │  PostgreSQL 서버   │
│  (사용자 PC)    │    psycopg / SQLAlchemy   │  (별도 서버/NAS)   │
│                │                           │                  │
│  PyQt6 GUI     │                           │  battery_db      │
│  matplotlib    │                           │  ├─ product      │
│  pandas        │                           │  ├─ test_group   │
│  db_connector  │                           │  ├─ cycle_summary│
│                │                           │  └─ (확장 테이블)  │
└──────────────┘                             └──────────────────┘
```

### 2.2 DB 서버 분리 이유
- 다수 사용자 **동시 접근** (각 PC의 BDT에서 동일 DB 조회)
- 데이터 **중앙 관리** — 한 번 적재하면 모든 사용자가 즉시 사용
- 백업/복구 서버 단 일괄 처리
- BDT 클라이언트는 **읽기 전용** (SELECT만) → 안전

### 2.3 연결 방식
```python
# db_connector.py — BDT 내부 모듈
import psycopg
DB_CONFIG = {
    "host": "192.168.x.x",   # 서버 IP (config.json에서 로드)
    "port": 5432,
    "dbname": "battery_db",
    "user": "bdt_reader",     # 읽기 전용 계정
    "password": "...",        # 환경변수 또는 암호화 저장
}
```
> **보안**: 읽기 전용 계정(`bdt_reader`)만 BDT에 부여. INSERT/UPDATE는 적재 스크립트 전용 계정에서만 수행.

---

## 3. DB 스키마 (Phase 1: 수명 데이터)

### 3.1 테이블 설계

```sql
-- 제품(PF) 테이블
CREATE TABLE product (
    product_id    SERIAL PRIMARY KEY,
    product_name  VARCHAR(100) UNIQUE NOT NULL,
    capacity_mah  REAL,
    cell_maker    VARCHAR(50),
    chemistry     VARCHAR(50),
    created_at    TIMESTAMP DEFAULT NOW()
);

-- 시험 그룹 테이블
CREATE TABLE test_group (
    group_id      SERIAL PRIMARY KEY,
    product_id    INTEGER REFERENCES product(product_id),
    group_name    VARCHAR(200) NOT NULL,
    cycler_type   VARCHAR(10) CHECK (cycler_type IN ('toyo', 'pne')),
    test_type     VARCHAR(50),
    temperature   REAL,
    charge_rate   VARCHAR(20),
    discharge_rate VARCHAR(20),
    condition_desc TEXT,
    source_path   TEXT,
    ingested_at   TIMESTAMP DEFAULT NOW()
);

-- 사이클 요약 테이블 (핵심 — df.NewData와 1:1 매핑)
CREATE TABLE cycle_summary (
    id            BIGSERIAL PRIMARY KEY,
    group_id      INTEGER REFERENCES test_group(group_id),
    channel       VARCHAR(10),
    cycle_num     INTEGER NOT NULL,
    dchg_ratio    REAL,
    chg_ratio     REAL,
    eff           REAL,
    eff2          REAL,
    rest_voltage  REAL,
    avg_voltage   REAL,
    temperature   REAL,
    dchg_energy   REAL,
    dcir          REAL,
    dcir2         REAL,
    soc70_dcir    REAL,
    ori_cycle     INTEGER,
    UNIQUE (group_id, channel, cycle_num)
);
```

### 3.2 df.NewData → cycle_summary 매핑

| df.NewData 컬럼 | DB 컬럼 | 설명 |
|:---|:---|:---|
| `Dchg` | `dchg_ratio` | 방전 용량 / 기준용량 |
| `Chg` | `chg_ratio` | 충전 용량 / 기준용량 |
| `Eff` | `eff` | Dchg ÷ Chg |
| `Eff2` | `eff2` | Chg(n+1) ÷ Dchg(n) |
| `RndV` | `rest_voltage` | 충전 후 휴지 전압 (OCV) |
| `AvgV` | `avg_voltage` | 방전 평균 전압 |
| `Temp` | `temperature` | 온도 |
| `DchgEng` | `dchg_energy` | 방전 에너지 |
| `dcir` | `dcir` | DC 내부저항 (Rss) |
| `dcir2` | `dcir2` | DC 내부저항 (1s DCIR) |
| `soc70_dcir` | `soc70_dcir` | SOC 70% 기준 DCIR |
| `OriCyc` | `ori_cycle` | 원래 사이클 번호 |

### 3.3 인덱스 전략

```sql
CREATE INDEX idx_cs_group_cycle ON cycle_summary (group_id, cycle_num);
CREATE INDEX idx_tg_product ON test_group (product_id);
CREATE INDEX idx_tg_temp ON test_group (temperature);
CREATE INDEX idx_tg_type ON test_group (test_type);
```

---

## 4. 빠른 데이터 로딩 전략

### 4.1 현재 vs DB 비교

| 항목 | 현재 (CSV 파싱) | DB 조회 |
|:---|:---|:---|
| 1개 모델 로딩 | 2~5초 | **0.05~0.2초** |
| 10개 모델 비교 | 20~50초 | **0.2~1초** |
| 병렬 처리 | ThreadPoolExecutor(4) | DB 서버가 알아서 병렬 |
| 재로딩 | 매번 전체 파싱 | 캐시 가능 |
| 필터 | 파싱 후 pandas 필터 | SQL WHERE 서버사이드 |

### 4.2 속도 최적화 기법

1. **커넥션 풀링** — `psycopg_pool.ConnectionPool`으로 TCP 핸드셰이크 제거
2. **서버사이드 필터링** — SQL WHERE로 네트워크 전송량 최소화
3. **클라이언트 캐시** — `lru_cache`로 동일 쿼리 반복 방지
4. **QThread 비동기** — DB 조회 중 GUI 블로킹 방지

### 4.3 예상 속도

| 시나리오 | 예상 시간 |
|:---|:---|
| 제품 목록 로드 | < 50ms |
| 1개 그룹 (3000 사이클) | ~100ms |
| 10개 그룹 비교 (~30,000행) | ~300ms |
| 500cyc 랭킹 (전 제품) | ~200ms |
| 검색 (키워드 + 온도) | ~50ms |

---

## 5. 데이터 적재 파이프라인

```
충방전기 raw 데이터 (CSV/폴더)
         │
         ▼
    ingest_cycle_data.py        ← 적재 전용 스크립트 (INSERT 권한)
    ├── toyo_cycle_data() 호출   ← BDT 기존 함수 재사용
    ├── pne_cycle_data() 호출
    └── INSERT INTO cycle_summary
         │
         ▼
    PostgreSQL (별도 서버)
         │
         ▼
    BDT 클라이언트 (SELECT만)
```

### DRM 파일 별도 처리 (신뢰성 .xls)
```
[사내 PC] .xls (DRM) → xlwings → .parquet (DRM 해제) → DB INSERT (Phase 2)
```

---

## 6. BDT UI 통합 계획

### 6.1 기본 원칙
- 사용자는 SQL을 모름 — 메뉴/드롭다운/체크박스로 선택
- 키워드 입력 검색 (예: "A16 상온")
- 기존 `graph_output_cycle()` 함수를 그대로 재사용 (DataFrame 구조 동일)

### 6.2 UI 구성 (DB 비교 탭)

```
┌─ DB 비교 탭 ────────────────────────────────────────────┐
│  [제품 ▼] [온도 ▼] [검색: _________] [조회]             │
│  ┌─ 시험 그룹 목록 (체크박스) ───────────────────┐       │
│  │ ☑ A16_Sub_25도_0.5C_RSS   (Toyo, 1842 cyc) │       │
│  │ ☑ A16_Sub_45도_0.5C_RSS   (Toyo, 1523 cyc) │       │
│  │ ☐ B20_Pro_45도_0.7C_CV    (Toyo, 2100 cyc) │       │
│  └─────────────────────────────────────────────┘       │
│  [비교 시작] [500cyc 랭킹] [DCIR 비교]                  │
│  ┌─ 그래프 (6축 — 기존과 동일) ──────────────┐          │
│  │ ax1: Dchg  │ ax2: Eff  │ ax3: Temp       │          │
│  │ ax4: DCIR  │ ax5: Eff2 │ ax6: V          │          │
│  └───────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────┘
```

### 6.3 키워드 검색 변환

| 입력 | 변환 |
|:---|:---|
| "상온", "RT" | `temperature = 25` |
| "고온", "45도" | `temperature = 45` |
| "수명" | `test_type = 'cycle_life'` |
| 제품명 "A16" | `product_name ILIKE '%A16%'` |

---

## 7. 단계별 로드맵

### Phase 0: DRM 변환 (사내 PC 전용)
- [ ] `convert_reliability_to_parquet.py` 작성
- [ ] xlwings로 DRM .xls 읽기 → .parquet 저장

### Phase 1: 수명 데이터 DB화 ⬅ 현재 단계
- [ ] PostgreSQL 서버 설치 및 설정
- [ ] `battery_db` + 3개 테이블 생성
- [ ] `ingest_cycle_data.py` 작성 (toyo/pne_cycle_data 재사용)
- [ ] 2~3개 모델 테스트 적재
- [ ] `db_connector.py` 작성 (읽기 전용)
- [ ] `pd.read_sql()` 로딩 속도 검증

### Phase 2: 신뢰성 데이터 추가
- [ ] `reliability_data` 테이블 추가
- [ ] DRM 해제 .parquet → DB INSERT
- [ ] BDT 신뢰성 탭 DB 연동

### Phase 3: 설계 스펙 / 리스크 추가
- [ ] `design_spec`, `risk_record` 테이블 추가
- [ ] 설계 마진 비교, 리스크 이력 관리

### Phase 4: BDT DB 비교 탭 구현
- [ ] PyQt6 "DB 비교" 탭 추가
- [ ] 메뉴/검색 UI + `graph_output_cycle()` 재사용
- [ ] 키워드 검색, 프리셋 버튼

### Phase 5: Profile / 필드 데이터 확장
- [ ] `charge_profile`, `field_log` 테이블 추가
- [ ] 충방전 Profile 비교 기능

---

## 8. 확장 테이블 (Phase 2~5 예정)

| 테이블 | Phase | 용도 |
|:---|:---|:---|
| `design_spec` | 3 | 제품 설계 스펙 |
| `reliability_data` | 2 | 신뢰성 시험 결과 |
| `charge_profile` | 5 | 충방전 프로파일 시계열 |
| `field_log` | 5 | 양산/필드 실사용 로그 |
| `risk_record` | 3 | 리스크 판정 이력 |

---

## 9. 기술 스택

| 구성 요소 | 기술 | 비고 |
|:---|:---|:---|
| DB 서버 | PostgreSQL 16+ | 별도 서버/NAS |
| Python 드라이버 | psycopg 3.x | 비동기 지원 |
| 커넥션 풀 | psycopg_pool | BDT 시작 시 pool 생성 |
| ORM | 미사용 (raw SQL) | BDT 규모에서 불필요 |
| 대량 적재 | pandas to_sql + COPY | COPY 프로토콜 |
| BDT 통합 | db_connector.py | DBConnector 클래스 |
| GUI 스레딩 | QThread + pyqtSignal | GUI 블로킹 방지 |
| DRM 캐시 | parquet | 신뢰성 데이터 전용 |

---

## 10. 필요 패키지

```toml
[project.optional-dependencies]
db = ["psycopg[binary]>=3.1", "psycopg-pool>=3.1"]
```

```python
try:
    import psycopg
    HAS_DB = True
except ImportError:
    HAS_DB = False
```

---

## 부록 A: 예상 데이터 규모

| 항목 | 추정값 |
|:---|:---|
| 제품 수 | 50~100 |
| 시험 그룹 수 | 500~2,000 |
| cycle_summary 행 수 | 100만~500만 |
| DB 디스크 사용량 | 1~5 GB |
| 단일 쿼리 응답 | < 300ms |

---

## 부록 B: BDT 기존 함수 재사용

| 기존 함수 | DB 연동 시 역할 |
|:---|:---|
| `toyo_cycle_data()` | 적재 시 CSV → DataFrame |
| `pne_cycle_data()` | 적재 시 CSV → DataFrame |
| `check_cycler()` | 적재 시 Toyo/PNE 판별 |
| `name_capacity()` | 적재 시 기준용량 추출 |
| `graph_output_cycle()` | DB 결과로 그래프 (수정 없이 재사용) |
| `_load_all_cycle_data_parallel()` | DB 도입 후 불필요 (SELECT 대체) |
