# 사이클데이터 탭 경로 테이블 UX 개선 — 영속화 2종

**날짜**: 2026-04-19
**대상 파일**: `DataTool_dev_code/DataTool_optRCD_proto_.py`
**배경**: 경로 입력 테이블 사용 시 반복되는 불편함(파일 다이얼로그 초기 경로 하드코딩, Undo 스택 무제한 증가) 개선. 이전 UX 리뷰의 #4 / #16 항목에 해당.

> **메모**: 초기안에 포함했던 #15(컬럼 폭 영속화)는 사용자 요청으로 제외.
> 사유 — 여러 작업 환경(PC) 간 사용하는 사용자 워크플로우에서 레지스트리에 머신별 상태를 쌓는 것을 선호하지 않음. 컬럼 폭은 기본값 고정으로 유지.

---

## 1. 파일 다이얼로그 최근 경로 기억 (#4)

**이전**
- 불러오기/저장 다이얼로그가 `initialdir="d://"` 로 하드코딩.
- D 드라이브 없는 환경이나 다른 작업 폴더를 쓰는 사용자는 매번 네비게이션 필요.

**이후**
- `QSettings("BDT", "DataTool")` 의 `cycle/last_path_dir` 키로 마지막 디렉토리 영속 저장.
- 다음 열기/저장 시 자동으로 해당 디렉토리에서 시작.
- 저장된 경로가 없거나 더 이상 존재하지 않으면 `d://` 로 폴백.
- **의도적으로 제외**: 테이블의 첫 유효 경로 기반 추정. 해당 경로는 주로 실험용 네트워크 서버(PNE1~25 등)라 다이얼로그 기본값으로는 부적절.

**신규 메서드 (모두 `WindowClass`)**
- `_cycle_settings()` — QSettings 핸들 반환.
- `_get_cycle_path_initial_dir()` — 저장된 최근 경로 또는 `d://` 폴백.
- `_set_cycle_path_last_dir(fp)` — 성공한 열기/저장 후 디렉토리 기억.

**영향 범위**
- `_load_path_file_to_table()` — 불러오기 다이얼로그
- `_save_table_to_path_file()` — 저장 다이얼로그

**QSettings 저장 위치 (Windows)**
`HKEY_CURRENT_USER\Software\BDT\DataTool\cycle\last_path_dir` 단일 키만 생성.
초기화 필요 시 regedit 에서 해당 키 삭제.

---

## 2. Undo 스택 상한 (#16)

**이전**
```python
self._table_undo_stack = []           # 무상한 리스트
...
self._table_undo_stack.append(state)
if len(self._table_undo_stack) > 20:
    self._table_undo_stack.pop(0)      # O(n) 좌측 삭제
```
- 의도한 상한 20 이었으나 매 push 마다 리스트 크기 체크 + `pop(0)` (O(n)).
- 단 20 회만 유지되어 장시간 편집 중 Ctrl+Z 되돌리기 깊이가 얕음.

**이후**
```python
self._table_undo_stack = deque(maxlen=50)
...
self._table_undo_stack.append(state)   # 넘치면 자동으로 좌측 자동 삭제
```
- `collections.deque(maxlen=50)` 사용 — 상한 50 으로 확장 + 자동 truncation.
- 좌측 추방이 O(1), 별도 크기 체크 불필요.
- 기존 `append / pop(우측) / if not self._table_undo_stack / bool` 호출은 모두 deque 호환.

**import 추가**
```python
from collections import OrderedDict, deque
```

---

## 변경 요약 (Line 기준, 변경 전 파일)

| 위치 | 변경 |
|------|------|
| L11 | `from collections import OrderedDict` → `OrderedDict, deque` |
| L10746 | `self._table_undo_stack = []` → `deque(maxlen=50)` |
| L21643 | `initialdir="d://"` → `self._get_cycle_path_initial_dir()` + 성공 시 `_set_cycle_path_last_dir()` |
| L21774 | `initialdir="d://"` → `self._get_cycle_path_initial_dir()` + 성공 시 `_set_cycle_path_last_dir()` |
| L22624 위 | QSettings 경로 영속화 헬퍼 3종 추가 (`_cycle_settings`, `_get_cycle_path_initial_dir`, `_set_cycle_path_last_dir`) |
| L22634-36 | 수동 20 상한 블록 제거 (deque 로 대체) |

---

## 제외된 항목 (#15 컬럼 폭 영속화)

**제거 사유**: 사용자는 여러 PC 에서 작업하는 워크플로우를 가지며, 컬럼 폭 같은 UI 상태를 머신별 레지스트리에 분산 저장하는 것을 선호하지 않음.

**대안 고려**
- 필요 시 컬럼 폭 기본값 자체를 더 여유있게 조정 (ex. 0→65, 5→70) — 현재는 미반영.
- 헤더 더블클릭 자동 fit 만 연결하는 안도 제외 — 저장 없이 휘발성이라 효과 제한적.

---

## 검증

- `python -c "import ast; ast.parse(...)"` 구문 검사 통과.
- 동작 검증(수동): 재시작 후 다이얼로그 초기 경로가 마지막 사용 폴더로 오는지, Ctrl+Z 가 50 회까지 되돌아가는지 확인 필요.
