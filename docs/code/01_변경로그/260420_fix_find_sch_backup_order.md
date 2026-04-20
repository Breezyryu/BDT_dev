# `.sch` 백업 넘버링 이해 정정 — 큰 번호가 더 최근

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수: `_find_sch_file()` (L7344)

## 배경

직전 커밋 54423a8 (`260420_fix_find_sch_current_pattern_priority.md`) 에서
`.sch` 백업 넘버링 의미를 아래와 같이 잘못 기술·구현했음:

> ❌ `~~_000.sch` = 가장 최근 백업 / `~~_NNN.sch` = 번호 커질수록 과거

사용자 정정:
> "시간 순으로 000 > 001 > 002 로 쌓인다. 000 이 가장 과거 패턴."

### 실제 규칙

PNE 장비는 패턴을 업데이트할 때마다 **이전 패턴**을 다음 비어있는 번호로 백업하므로, 번호는 **생성된 순서 = 시간순 누적**:

| 파일 | 의미 | 시간 |
|---|---|---|
| `~~_000.sch` | 초기 패턴 (첫 번째 백업) | **가장 과거** |
| `~~_001.sch` | 두 번째 단계 | ↓ |
| `~~_002.sch` | 세 번째 단계 | ↓ |
| `~~_NNN.sch` | 번호 클수록 최근 백업 | **더 최근** |
| `~~.sch` (접미사 없음) | 현재 적용 패턴 | **가장 최신** |

## 문제

직전 커밋의 "원본 없이 백업만 존재" 분기:

```python
# Before (잘못됨)
def _suffix_num(name):
    m = _SCH_SUFFIX_RE.match(name)
    return int(m.group(2)) if m else float('inf')
sch_files.sort(key=_suffix_num)          # 오름차순
return os.path.join(channel_path, sch_files[0])   # ← _000 선택
```

→ `_000` 을 "가장 최근 백업" 이라 가정하고 선택. 실제로는 **가장 과거 백업**이므로, 원본이 삭제된 엣지 케이스에서 **가장 오래된 패턴**으로 해석하게 됨.

## 수정

```python
# After
def _suffix_num(name):
    m = _SCH_SUFFIX_RE.match(name)
    return int(m.group(2)) if m else -1
sch_files.sort(key=_suffix_num, reverse=True)   # 내림차순 → _NNN 큰 것 먼저
return os.path.join(channel_path, sch_files[0])
```

docstring 도 같이 정정:
```
PNE 운영 규칙 (백업 넘버링은 시간 누적 순):
  - 접미사 없는 원본(`~~.sch`)      = 현재 적용 중인 패턴 (가장 최신)
  - `~~_000.sch`                    = 가장 과거 백업 (초기 패턴)
  - `~~_001.sch`                    = 그다음 단계 백업
  - `~~_NNN.sch`                    = 번호가 커질수록 더 최근 백업
```

## 영향 범위

### 주 시나리오 (원본 `.sch` 가 존재하는 정상 환경)
- **영향 없음**. `originals` 분기에서 이미 원본을 1순위 반환하므로 이번 수정 경로 미진입.
- 직전 커밋(54423a8) 의 주 개선(원본 우선)이 **여전히 유효**하게 동작.

### 엣지 케이스 (원본은 없고 백업만 존재)
- **수정 전**: `_000` (가장 과거) 선택 → 초기 패턴 기준으로 해석
- **수정 후**: `_NNN` 가장 큰 번호 (가장 최근 백업) 선택 → 직전 패턴 기준으로 해석
- 실제 거의 안 생기는 케이스지만 정확성 확보

## 검증 포인트

- [ ] `~~.sch` 가 존재하는 정상 경로: 원본 선택 (회귀 없음, 직전 커밋과 동일 동작)
- [ ] 원본이 삭제된 드문 경로에서 백업만 남은 경우: `_NNN` 가장 큰 번호 파일 선택
- [ ] 파일 1개 (`~~.sch` 또는 `~~_000.sch`) 뿐인 경우: 그 파일 반환
- [ ] docstring 의 PNE 규칙 설명이 실제 순서와 일치

## 관련 변경로그

- `260420_fix_find_sch_current_pattern_priority.md` — 원본(현재 패턴) 우선 선택 규칙 (주 수정, 여전히 유효)
- `260420_revert_sch_extended_and_add_diag.md` — 확장 탐색 롤백 + 진단 로그
