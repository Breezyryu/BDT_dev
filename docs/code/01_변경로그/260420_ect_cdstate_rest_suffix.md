# ECT path CHG/DCHG 모드에 Rest 포함 옵션 추가

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수: `pne_Profile_continue_data()` (L9698)

## 배경 / 목적

사용자 요청:
> "CHG / DCH·DCHG 모드에서 충전 종료, 방전 종료 후 Rest 포함 옵션도 추가해줄래?"

### 기존 동작

| CDstate | 포함 StepType | Rest |
|---|---|---|
| `CHG` | 9, 1(충전) | 제외 |
| `DCH` / `DCHG` | 9, 2(방전) | 제외 |
| `CYC` / `Cycle` / `7cyc` / `GITT` | 전체 | 포함 |

`CHG`/`DCHG` 로 ECT path 를 돌리면 각 스텝 직후의 Rest (휴지) 가 자동으로 잘려 ECM/PyBaMM 파라미터 피팅에서 **pulse-relaxation 구간 (OCV recovery) 을 볼 수 없었다**.

## 도메인 근거

- **충전 후 Rest** = OCV relaxation → SEI 성장, Li diffusion 관찰
- **방전 후 Rest** = OCV recovery → LAM, kinetic limitation 평가
- GITT D_s 추출 시 각 pulse 후 Rest 의 dV/√t 기울기가 필수
- ECM 모델 피팅에서 R1·τ1, R2·τ2 (더블 RC) 식별에 필수

## 수정 — 모드 문자열 접미사 방식

경로 테이블 "모드" 열 (col 5) 에 `+R` 또는 `+REST` 접미사를 붙이면 해당 모드의 Rest 도 포함한다. 대소문자 무관, 공백 허용.

### 새로운 매핑

| 모드 입력 | 포함 StepType | 의미 |
|---|---|---|
| `CHG` | 9, 1 | 충전만 (기존) |
| **`CHG+R`** / **`CHG+REST`** | 9, 1, **3** | **충전 + Rest** |
| `DCH` / `DCHG` | 9, 2 | 방전만 (기존) |
| **`DCH+R`** / **`DCHG+R`** / **`DCHG+REST`** | 9, 2, **3** | **방전 + Rest** |
| `CYC` / `Cycle` / `7cyc` / `GITT` | 전체 | 기존 (Rest 포함) |

대소문자 정규화로 `chg+r`, `DcHg+r` 같은 혼합도 허용.

### 코드 변경 (L9717-9738)

```python
# Before
if CDstate == "CHG":
    Profileraw = Profileraw.loc[... & Profileraw[2].isin([9, 1])]
elif CDstate in ("DCH", "DCHG"):
    Profileraw = Profileraw.loc[... & Profileraw[2].isin([9, 2])]
elif CDstate in ("CYC", "Cycle", "7cyc", "GITT"):
    Profileraw = Profileraw.loc[...]

# After
_cd_raw = CDstate.strip().upper() if isinstance(CDstate, str) else ""
_cd_base = _cd_raw
_include_rest = False
if _cd_raw.endswith("+REST") or _cd_raw.endswith("+R"):
    _cd_base = _cd_raw.rsplit("+", 1)[0].strip()
    _include_rest = True
if _cd_base == "CHG":
    _types = [9, 1] + ([3] if _include_rest else [])
    Profileraw = Profileraw.loc[... & Profileraw[2].isin(_types)]
elif _cd_base in ("DCH", "DCHG"):
    _types = [9, 2] + ([3] if _include_rest else [])
    Profileraw = Profileraw.loc[... & Profileraw[2].isin(_types)]
elif _cd_base in ("CYC", "CYCLE", "7CYC", "GITT"):
    Profileraw = Profileraw.loc[...]
```

### Rest 가 어떤 Rest인지

필터 대상이 `[9, 1, 3]` 또는 `[9, 2, 3]` 이므로:
- **CHG+R**: 충전 스텝과 Rest 스텝만 남음 → 방전 Rest 는 애초에 StepType 2 가 제외되어 방전 전후 rest 중 **충전 직후 rest만 자연 포함** (방전 자체가 없으니 방전 후 rest 도 논리적으로 없음)
- **DCHG+R**: 방전 + Rest 만 남음 → 같은 논리로 **방전 직후 Rest만 포함**

따라서 사용자가 기대한 "충전/방전 종료 후 Rest" 정확히 포함.

## 영향 범위

- `pne_Profile_continue_data()` — `CDstate == "..."` 단순 비교를 파싱 로직으로 대체 (L9717-9724 → L9717-9738)
- Toyo 는 ECT path 흐름에서 해당 함수 미사용 (PNE 전용) — 영향 없음
- 기존 동작 **완전 호환**:
  - `CHG`/`DCH`/`DCHG`/`CYC`/`Cycle`/`7cyc`/`GITT` 기존 값은 그대로 동작
  - 새 접미사 모드는 **추가**만
- 부수 개선: 대소문자/공백 관대한 파싱으로 사용자 입력 오류 허용도 ↑

## 검증 포인트

- [ ] 경로 테이블 모드 열에 `CHG` → 기존과 동일하게 충전 스텝만 플롯
- [ ] 모드 열에 `CHG+R` → 충전 + 충전 직후 Rest 플롯, 방전 데이터 미포함
- [ ] `CHG+REST` / `chg+r` / `CHG +R` 모두 동일 동작 (정규화 확인)
- [ ] `DCHG+R` → 방전 + 방전 직후 Rest
- [ ] `CYC`/`GITT` 는 변화 없음 (전체 포함)
- [ ] `ect_saveok` 체크 시 CSV 출력에도 Rest 구간 포함 확인

## UI 힌트 (후속 과제)

경로 테이블 col 5 "모드" 헤더/툴팁에 지원 모드 목록을 노출하면 UX 개선:
```
CHG | CHG+R | DCH | DCHG | DCHG+R | CYC | GITT
```
(이번 변경 범위 제외 — 필요 시 별도 PR)

## 관련 변경로그

- `260420_fix_ect_path_profile_always_override.md` — ECT 체크 시 프로파일 분석 항상 ECT 위임
- `260420_fix_ect_path_tc_clear_hint_and_black_overwrite.md` — TC 삭제 시 힌트 복원
- `260420_fix_ect_path_tc_autofill_roundtrip.md` — 저장·로드 라운드트립
