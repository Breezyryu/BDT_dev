# ECT path Rest 포함 옵션 — 체크박스 방식으로 전환

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수: `pne_Profile_continue_data()` (L9698), `ect_confirm_button()` (L24917 근처)

## 배경

사용자 요청:
> "+R 텍스트 입력말고, 아래 rest 체크박스로 구분해줄 수 있어?"

앞서 커밋(f38b5ce, `260420_ect_cdstate_rest_suffix.md`)에서는 경로 테이블 모드 열에 `CHG+R` 같은 접미사를 허용해 Rest 포함 여부를 제어했다. 사용자가 텍스트 방식 대신 **프로파일 탭의 기존 Rest 체크박스(`profile_rest_chk`)** 로 제어하길 원하므로 설계 변경.

## 변경 내용

### 1. `pne_Profile_continue_data` 시그니처 확장

```python
# Before
def pne_Profile_continue_data(raw_file_path, inicycle, endcycle,
                              mincapacity, inirate, CDstate):

# After
def pne_Profile_continue_data(raw_file_path, inicycle, endcycle,
                              mincapacity, inirate, CDstate,
                              include_rest=False):
```

- 파라미터 기본값 `False` → 기존 호출자(없지만) 호환
- 실제 유일 호출자 `ect_confirm_button` 만 새 인자 전달

### 2. CDstate 파싱 단순화 (`+R` 접미사 로직 제거)

```python
# After — 대소문자/공백만 정규화, Rest 포함 여부는 파라미터로 결정
_cd = CDstate.strip().upper() if isinstance(CDstate, str) else ""
if _cd == "CHG":
    _types = [9, 1] + ([3] if include_rest else [])
    Profileraw = Profileraw.loc[... & Profileraw[2].isin(_types)]
elif _cd in ("DCH", "DCHG"):
    _types = [9, 2] + ([3] if include_rest else [])
    Profileraw = Profileraw.loc[... & Profileraw[2].isin(_types)]
elif _cd in ("CYC", "CYCLE", "7CYC", "GITT"):
    Profileraw = Profileraw.loc[...]
```

- `+R` / `+REST` 접미사 파싱 제거 → 텍스트 경로 제거, 혼란 방지
- 대소문자 무관 정규화는 **유지** (부가 UX 개선)

### 3. `ect_confirm_button` 에서 체크박스 상태 전달

```python
# After
temp = pne_Profile_continue_data(
    FolderBase, Step_CycNo, Step_CycEnd, mincapacity, firstCrate,
    ect_CD[i],
    include_rest=self.profile_rest_chk.isChecked())
```

- 프로파일 탭 데이터 범위 GroupBox 2행의 `Rest` 체크박스 상태를 그대로 사용
- ECT 체크 상태와 무관하게 Rest 체크박스는 **항상 활성** (이미 UI 상 클릭 가능)
- 변경된 흐름: `chk_ectpath ON` → `ect_confirm_button` → `profile_rest_chk.isChecked()` → filter StepType 결정

## 동작 매트릭스

| CDstate | Rest 체크박스 | 포함 StepType |
|---|---|---|
| `CHG` | ☐ 해제 | 9, 1 (기존 동작) |
| `CHG` | ☑ **체크** | 9, 1, **3** (충전 + Rest) |
| `DCHG` | ☐ 해제 | 9, 2 (기존 동작) |
| `DCHG` | ☑ **체크** | 9, 2, **3** (방전 + Rest) |
| `CYC` / `GITT` | 무관 | 전체 (기존 동작) |

Rest 체크박스 **기본 상태는 UI 초기값**(사용자 스크린샷상 체크되어 있었음). 기존 동작을 유지하려면 체크 해제.

## 도메인 해석 불변

- 충전 직후 Rest = OCV relaxation → SEI 성장, Li diffusion
- 방전 직후 Rest = OCV recovery → LAM, kinetic limitation
- GITT D_s 추출 시 각 pulse 후 Rest 의 dV/√t 기울기 필요
- ECM 피팅 R1·τ1, R2·τ2 (더블 RC) 식별에 필수

## 이전 커밋(`+R` 접미사) 롤백 여부

- `+R` 텍스트 파싱 코드는 **완전 제거**
- 이전 변경로그 `260420_ect_cdstate_rest_suffix.md` 삭제 (문서 일관성)
- Git 히스토리상 `+R` 방식 → 체크박스 방식 전환이 commit 메시지로 기록됨
- 만에 하나 사내에서 `CHG+R` 값으로 경로 파일을 이미 저장했다면 재로드 시 현재 코드는 `+R` 을 유효 모드로 인식하지 않음 → `CHG` 로 수정 필요. 이 커밋 전에 사내 테스트에서 `+R` 써봤을 가능성 낮지만, 만약 썼다면 저장된 경로 파일에서 `+R` 을 지워야 정상 동작.

## 영향 범위

- `pne_Profile_continue_data()` — 파라미터 1개 추가, 파싱 로직 단순화 (~10줄 감소)
- `ect_confirm_button()` — 호출부 1줄 → 4줄 (파라미터 전달)
- 다른 함수 영향 없음 (유일 호출자)
- Toyo ECT path 영향 없음 (PNE 전용 함수)

## 검증 포인트

- [ ] ECT path 체크 + 모드 `CHG` + Rest 체크박스 **해제** → 충전 스텝만 플롯 (기존 동작 유지)
- [ ] ECT path 체크 + 모드 `CHG` + Rest 체크박스 **체크** → 충전 + 직후 Rest 플롯
- [ ] `DCHG` 에 대해서도 동일 패턴
- [ ] `CYC`/`GITT` 는 체크박스 상태 무관하게 전체 포함
- [ ] Rest 체크 토글 후 재실행 시 반영
- [ ] `ect_saveok` 체크 시 CSV 출력 데이터가 체크박스 상태에 따라 변함 확인

## 관련 변경로그

- (삭제됨) `260420_ect_cdstate_rest_suffix.md` — `+R` 접미사 방식
- `260420_fix_ect_path_profile_always_override.md` — ECT 체크 시 항상 ECT 핸들러 위임
- `260420_fix_ect_path_tc_clear_hint_and_black_overwrite.md` — TC 삭제 시 힌트 복원
- `260420_fix_ect_path_tc_autofill_roundtrip.md` — 저장·로드 라운드트립
