# 260508 drm_reload_test — 여러 파일 경로 기본 모드에서 처리

요청자: 사용자

## 배경

`tools/drm_reload_test.py` 의 기본(플래그 없음) 호출은 단일 파일만 받았다.

```bash
python drm_reload_test.py <입력파일> [출력stem]
```

여러 파일을 한번에 처리하려면 `--batch` 플래그를 명시해야 했다.

```bash
python drm_reload_test.py --batch <path1> <path2> ...
```

사용자는 플래그 없이 여러 경로를 그대로 넘기면 모두 처리되길 원함.

## 변경 요지

기본 모드(`_cmd_extract`)에 **다중 입력 자동 감지** 추가:

- 인자 2개 이상이고 **모두 실재 경로(파일/디렉터리)** 면 배치 모드로 자동 위임
- 그 외 (1개 / 두 번째가 미존재) 는 기존 단일 모드 그대로 유지

### Before

```bash
python drm_reload_test.py a.xlsx           # 단일 OK
python drm_reload_test.py a.xlsx b.xlsx    # b.xlsx 를 출력stem 으로 잘못 해석 → 깨진 폴더명
```

### After

```bash
python drm_reload_test.py a.xlsx                       # 단일 (기존 그대로)
python drm_reload_test.py a.xlsx myoutput              # 단일 + 출력stem (기존 그대로, myoutput 미존재)
python drm_reload_test.py a.xlsx b.xlsx                # 자동 배치 (둘 다 존재)
python drm_reload_test.py a.xlsx b.pptx folder/        # 자동 배치 (디렉터리는 재귀 탐색)
```

## 변경 내역

### `_cmd_extract` 진입부

```python
def _cmd_extract(argv: list[str]) -> int:
    # 다중 입력 자동 감지: 인자 2개 이상이고 모두 실재 파일/디렉터리면 배치 위임.
    # 단일 모드의 [출력stem] 인자는 통상 미존재 경로이므로 충돌 없음.
    if len(argv) >= 3:
        cand = argv[1:]
        if all(Path(a).expanduser().exists() for a in cand):
            files = _collect_batch_inputs(cand)
            return _run_batch(files, out_dir=None, fmt='png')
    # ... 기존 단일 모드 로직 ...
```

### `_run_batch` 신규 헬퍼 (리팩토링)

기존 `_cmd_batch` 의 본문 (수집 후 처리·실패 집계·요약 출력) 을 `_run_batch(files, out_dir, fmt)` 로 추출.

- `_cmd_batch` 는 인자 파싱 후 `_run_batch` 호출 (동작 동일)
- `_cmd_extract` 의 자동 감지 분기도 같은 헬퍼 사용 → 단일 진입점

### docstring

상단 사용법 블록에 자동 감지 모드 설명 추가:

```text
# 사내 — 여러 파일 한번에 (--batch 플래그 불필요, 자동 감지)
#   인자 2개 이상이고 모두 실재 경로(파일/디렉터리)면 배치 모드로 자동 위임
python drm_reload_test.py <입력1> <입력2> [<입력3>...]
#   → 각 원본 옆에 <stem>_bundle/ 폴더 생성 (디렉터리는 재귀 탐색)
```

## 호환성

| 호출 | 기존 동작 | 신규 동작 | 호환 |
| ---- | -------- | -------- | ---- |
| 1 arg | 단일 추출 | 동일 | ✅ |
| `<file>` `<output_stem>` (stem 미존재) | 단일 + stem 적용 | 동일 | ✅ |
| `<file1>` `<file2>` (둘 다 존재) | stem 으로 잘못 해석 | **자동 배치** | 🆕 |
| `<file>` + 디렉터리 (둘 다 존재) | stem 으로 잘못 해석 | **자동 배치 (재귀)** | 🆕 |
| `--batch` 플래그 사용 | 배치 + `--out`/`--format` 지원 | 동일 | ✅ |
| `--render`/`--to-*`/`--pack`/`--unpack` | 그대로 | 동일 | ✅ |

엣지 케이스: `<file>` `<existing_dir>` 를 사용자가 일부러 출력 stem 으로 쓰던 경우 → 자동 배치로 분기됨. 매우 드문 사용례라 수용. 명시 단일 모드를 원하면 stem 을 미존재 경로로 지정.

## 검증

- `python -m py_compile tools/drm_reload_test.py` — 통과
- 4-케이스 분기 smoke test (메모리 내 호출):
  - 1 arg, 미존재 → 단일 모드 "파일 없음" rc=2 ✅
  - 2 args, 둘 다 미존재 → 단일 모드 "파일 없음" rc=2 ✅
  - 2 args, 둘 다 존재 → 배치 모드 진입, `_collect_batch_inputs` 호출 ✅
  - 2 args, 첫 번째만 존재 → 단일 모드 + stem 처리 (기존 호환) ✅
- 사내 실측(xlwings · Fasoo) 은 별도

## 한계

- 자동 감지는 **모든 인자가 실재 경로** 일 때만 트리거. 글롭 패턴(`*.xlsx`)은 셸이 펼친 결과가 모두 실존하면 자동 배치, 일부만 매칭되면 단일 모드 폴백
- 출력 형식은 자동 모드에서 `png` 고정 (`--batch --format svg` 처럼 옵션 지정하려면 명시 플래그 사용)

## 후속 — 필요 시

- 자동 감지 시에도 `--format`/`--out` 단축 옵션 인식 (현재는 `--batch` 명시 필요)
- 글롭 패턴을 파이썬 측에서 직접 펼치는 옵션 (cmd.exe 호환)

---

## 추가 (260508) — 코드 내 다중 입력 모드

요청자: 사용자

CLI 인자 대신 **파일 상단 변수에 경로 리스트를 박고 그냥 실행** 하고 싶다는 요구.
IDE Run 버튼·디버거 사용 시 편의성 ↑.

### 신규 모듈 변수

```python
# 코드 내 다중 입력 — 비어있지 않으면 argv 없이 실행해도 배치 모드로 자동 처리.
SRCS: list[str] = [
    # r"C:\path\to\file1.xlsx",
    # r"C:\path\to\file2.pptx",
    # r"C:\folder\with\office_files",
]
# 배치 출력 디렉터리 (None/빈문자열 → 각 원본 옆, 경로 → 평탄화 출력)
OUT_DIR = r""
```

### 우선순위 (높은 → 낮은)

1. **CLI argv** — `python drm_reload_test.py <path>...` (자동 감지 다중 또는 단일)
2. **`SRCS`** — argv 없으면 SRCS 채워졌는지 확인 → 배치 위임
3. **`SRC`/`DST`** — 둘 다 비어있을 때 단일 모드 폴백

### `_cmd_extract` 진입부 (수정 후 전체)

```python
def _cmd_extract(argv: list[str]) -> int:
    # 1) argv 다중 자동 감지
    if len(argv) >= 3:
        cand = argv[1:]
        if all(Path(a).expanduser().exists() for a in cand):
            files = _collect_batch_inputs(cand)
            return _run_batch(files, out_dir=None, fmt='png')

    # 2) 코드 내 SRCS
    if len(argv) < 2 and SRCS:
        out_dir = Path(OUT_DIR).expanduser().resolve() if OUT_DIR else None
        if out_dir is not None:
            out_dir.mkdir(parents=True, exist_ok=True)
        files = _collect_batch_inputs(SRCS)
        return _run_batch(files, out_dir=out_dir, fmt='png')

    # 3) 기존 단일 모드 (argv[1]/argv[2] 또는 SRC/DST)
    ...
```

### 검증

- `python -m py_compile` — 통과
- 3-케이스 smoke test:
  - SRCS 빈 채로 argv 없음 → SRC 폴백, "입력 경로 필요" rc=2 ✅
  - SRCS=[f1,f2], argv 없음 → 배치 진입, 처리 시도 ✅
  - SRCS 채워짐 + argv 단일 경로 → argv 우선 (SRCS 무시), 단일 모드 ✅

### 사용 예 (IDE Run)

`drm_reload_test.py` 상단을 다음과 같이 편집:

```python
SRCS: list[str] = [
    r"\\office-share\team\reports\Q1_results.xlsx",
    r"\\office-share\team\reports\Q1_slides.pptx",
    r"\\office-share\team\reports\drafts",   # 폴더는 재귀
]
OUT_DIR = r"C:\tmp\drm_extract"   # 비워두면 각 원본 옆
```

VSCode/PyCharm 의 Run 버튼만 누르면 SRCS 의 모든 경로가 일괄 추출됨.

