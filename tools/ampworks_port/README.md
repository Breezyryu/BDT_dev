# ampworks_port — 독립 개발·검증 스캐폴딩

**목적**: [ampworks](https://github.com/NatLabRockies/ampworks) 기능을 proto_.py 에 이식하기 **전** 독립 구현·검증. 검증 통과한 기능만 proto_.py 에 이식.

**라이센스**: BSD-3-Clause ([원문](../../docs/licenses/ampworks-BSD-3.txt))
**분석 문서**:
- [우선순위 개요](../../docs/code/03_코드리뷰_코드학습/260419_ampworks_분석_BDT차용제안.md)
- [기능별 정밀분석](../../docs/code/03_코드리뷰_코드학습/260419_ampworks_정밀분석_기능별.md) — 입출력·공수
- [심화분석 F1-F8](../../docs/code/03_코드리뷰_코드학습/260419_ampworks_심화분석_F1-F8.md) — 물리기반·수식유도·리스크

---

## 디렉토리 구조 (계획)

```
tools/ampworks_port/
├─ README.md              (본 파일)
├─ f1_gitt/               # F1. GITT → D_s 추출
│  ├─ gitt_extract.py     #   포팅 모듈 (BDT 단위계로 변환)
│  ├─ validate.py         #   검증 스크립트 (240821/M2 SDI 실데이터)
│  └─ results/            #   검증 결과 아티팩트 (플롯, 표, 비교)
├─ f2_ici/                # F2. ICI → D_s
├─ f3_spline/             # F3. dQ/dV spline smoothing
├─ f4_fitter/             # F4. DqdvFitter (stoichiometry)
├─ f5_lam_lli/            # F5. LAM/LLI 열화모드
├─ f6_hppc/               # F6. HPPC impedance (후순위)
├─ f7_ocv_peak/           # F7. OCV peak matching
├─ f8_uncertainty/        # F8. ±σ 전파 헬퍼
└─ _common/               # 공통 BDT 변환 layer
    ├─ units.py           #   μA→A, μV→V, 0.01s→s 변환
    └─ loaders.py         #   PNE SaveEndData → ampworks 입력 포맷
```

---

## 파일 헤더 템플릿 (포팅 파일 공통)

```python
"""{기능명} — ampworks 포팅 (BDT 단위계 적응)

Source: https://github.com/NatLabRockies/ampworks (BSD-3-Clause)
Original copyright: 2025 Alliance for Energy Innovation, LLC
                    Corey R. Randall, National Laboratory of the Rockies
See docs/licenses/ampworks-BSD-3.txt for full license text.

Modifications for BDT:
- Input units: μA/μV/0.01s → A/V/s (_common/units.py)
- Loader: PNE SaveEndData → Seconds/Amps/Volts frame (_common/loaders.py)
- {기능별 기타 변경}
"""
```

---

## 이식 판정 체크리스트 (기능별 적용)

각 기능을 proto_.py 에 이식하기 **전** 아래 모두 ✅ 되어야 함.

### A. 정확성
- [ ] 원본 ampworks 예제(있는 경우)와 출력 일치 확인 (± 수치 오차 1% 이내)
- [ ] BDT 실데이터 ≥ 3건 시험 — 결과가 물리적으로 타당 (D_s 범위 10⁻¹⁵ ~ 10⁻¹⁰ m²/s, LAM/LLI ∈ [0, 1])
- [ ] 엣지케이스: 빈 데이터 / 단일 pulse / NaN 섞임 — 크래시 없이 처리

### B. BDT 통합성
- [ ] `_common/units.py` 변환 레이어 통과 후 입력 포맷 맞음
- [ ] PNE SaveEndData / Toyo capacity.log 양쪽 로더 대응 확인
- [ ] 사이클 분류(신 9종) 카테고리와 연결 가능 — 예: `GITT(full)` 범위만 뽑아서 F1 에 공급

### C. 성능
- [ ] 대표 시험 1건 (예: 수명 TC 900) 처리 시간 ≤ 10s
- [ ] 메모리 피크 ≤ 500 MB

### D. 사용자 관점
- [ ] 결과가 엑셀·플롯으로 해석 가능 (단위 명기, 축 라벨 한글)
- [ ] 실패 시 명확한 에러 메시지 (어느 데이터·어느 파라미터가 문제인지)
- [ ] UI 입력 필드 최소화 (기본값 있음, 필수 입력만 요구)

### E. 라이센스·문서
- [ ] 파일 헤더에 BSD-3 notice 있음
- [ ] 원본 공식·변수명 차이가 주석으로 설명됨
- [ ] 변경로그 작성 (docs/code/01_변경로그/)

---

## 검증 스크립트 표준 구조

각 기능별 `validate.py` 는 다음을 수행:

```python
def run_validation():
    # 1. 대표 BDT 실데이터 리스트 (경로별 최소 3건)
    test_cases = [
        ('성능/240821 ... GITT ...', '대표 GITT'),
        ('성능/250905 ... M2-SDI-open-ca ...', '반셀 GITT (음극)'),
        ('성능/260202 ... Cosmx 25Si ...', '율별 용량'),
    ]
    
    for path, label in test_cases:
        # 2. BDT 로더로 데이터 불러오기
        df = load_bdt_data(path)
        
        # 3. ampworks 포팅 함수 실행
        result = extract_gitt_params(df, radius=5e-6)
        
        # 4. 결과 검증 (범위, shape, NaN 여부)
        assert_physical_range(result)
        
        # 5. 결과 저장 (results/ 폴더)
        save_artifacts(result, label)
    
    # 6. 요약 리포트 생성 (results/validation_summary.md)
```

---

## 진행 워크플로우

1. **분석 문서 리뷰** — 기능별 정밀분석 문서에서 다음 구현할 기능 선정
2. **f{N}_{name}/ 폴더 생성** — 모듈·validate·results 스캐폴드
3. **포팅** — BDT 단위계 적응 + 라이센스 헤더
4. **검증** — validate.py 실행 → results/ 에 아티팩트 누적
5. **판정** — 위 체크리스트 전부 ✅ 시 proto_.py 이식 승인 요청
6. **이식** — 별도 Phase 변경로그로 proto_.py 수정 (Phase 1/2 과 동일 방식)

---

## 현재 상태

| 기능 | 스캐폴드 | 포팅 | 검증 | 이식 |
|:---:|:---:|:---:|:---:|:---:|
| F1 GITT D_s | ⬜ | ⬜ | ⬜ | ⬜ |
| F2 ICI D_s | ⬜ | ⬜ | ⬜ | ⬜ |
| F3 Spline | ⬜ | ⬜ | ⬜ | ⬜ |
| F4 DqdvFitter | ⬜ | ⬜ | ⬜ | ⬜ |
| F5 LAM/LLI | ⬜ | ⬜ | ⬜ | ⬜ |
| F6 HPPC | ⬜ | ⬜ | ⬜ | ⬜ |
| F7 OCV peak | ⬜ | ⬜ | ⬜ | ⬜ |
| F8 Uncertainty | ⬜ | ⬜ | ⬜ | ⬜ |

사용자 지시로 실제 개발 시작 시 이 표 갱신.
