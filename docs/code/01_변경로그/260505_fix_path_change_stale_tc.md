# 경로 교체 시 stale TC 사용 방지 — 첫 클릭은 사이클 정보만 갱신 (path 비교 방식)

날짜: 2026-05-05 (v2 — paste·load 우회 경로도 처리)
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수/필드:
- `_rows_last_analyzed_path` (신규 클래스 필드, L24405 근처)
- `unified_profile_confirm_button` (L27620) — 경로 비교 가드
- `cycle_tab_reset_confirm_button` 등 reset 핸들러 — 매핑 클리어

## 사용자 보고

```
1번 경로로 TC 프로파일 작업하다가 기존 경로 지우고 다른 경로 작업 시,
이전 TC 값으로 프로파일 분석되는 문제가 있다.
새로운 경로는 프로파일 분석하면 사이클 정보만 업데이트하도록 하자.
```

추가로 사용자 로그 (20:28:34) 에서 v1 패치 (셀 편집 시그널 기반 마킹) 적용 후에도 stale 분석이 발생하는 케이스 확인:
```
[20:28:24] (1차 분석 정상)
[20:28:34] ▶ confirm  ← 경로 변경됐는데 곧바로 full 분석 (8.758s)
```
원인: paste / load 등은 셀 편집 시그널이 차단되어 `_on_path_cell_changed` 가 호출 안 되므로 v1 의 `_rows_pending_first_analysis` 마킹이 누락.

## v2 — 경로 비교 방식

마킹 시그널에 의존하지 않고, **confirm 시점에 현재 표 의 경로 vs "마지막으로 실제 분석된 경로"** 를 직접 비교.

### 1. 신규 필드

```python
# ── 행별 "마지막으로 실제 분석된 경로" (260505 추가) ──
# _row_last_path 와 별개 — _row_last_path 는 셀 편집 추적용 (paste·load 시 동기화),
# _rows_last_analyzed_path 는 "실제 분석 실행 완료 시점" 의 스냅샷이라 paste 와 무관.
_rows_last_analyzed_path: dict[int, str] = {}
```

### 2. confirm 가드 (paste·load 무관 동작)

```python
_cur_paths = {
    r: self._get_table_cell(r, 1)
    for r in range(self.cycle_path_table.rowCount())
    if self._get_table_cell(r, 1)
}
_changed_paths = [
    (r, p) for r, p in _cur_paths.items()
    if self._rows_last_analyzed_path.get(r) != p
]
if _changed_paths:
    # 다음 클릭부터는 분석 실행되도록 현 경로 매핑을 커밋
    self._rows_last_analyzed_path = dict(_cur_paths)
    QMessageBox.information(self, "새 경로 감지", ...)
    return
```

가드는 `_build_all_channel_meta_parallel` + `_update_cycle_timeline` (= 사이클 정보 갱신) **직후**, 분석 직전에 위치 → cycle 정보는 항상 최신, 분석만 다음 클릭으로 미룸.

### 3. reset 동기화

`profile_tab_reset_confirm_button` 등에서 `_rows_last_analyzed_path.clear()`.

## v1 → v2 차이

| | v1 (시그널 기반) | v2 (path 비교) |
|---|------------------|-----------------|
| 트리거 | `_on_path_cell_changed` | confirm 시점 직접 비교 |
| 직접 셀 편집 | ✓ 감지 | ✓ 감지 |
| **paste (Ctrl+V)** | ✗ blockSignals 로 우회 | ✓ 감지 |
| **load 파일 import** | ✗ 우회 | ✓ 감지 |
| 다중 행 추가 | ✓ 감지 (각 시그널) | ✓ 감지 (한 번의 비교) |

## 사용자 시나리오 비교

### Before (v1 적용 전 / v1 우회 케이스)
```
1. Path A 입력 + TC=5-19 분석 → 그래프 출력 ✓
2. col 1 의 Path A 를 Path B 로 교체 (paste 또는 load file)
3. "프로파일 분석" 클릭
4. 시스템: Path B + TC=5-19 (stale) 로 분석 ← 버그: 잘못된 결과
```

### After (v2)
```
1. Path A 입력 + 첫 클릭: cycle 정보만 갱신 (메시지: "새 경로 감지")
2. 두 번째 클릭: TC=5-19 정상 분석 → 그래프 출력 ✓
3. col 1 의 Path A 를 Path B 로 교체 (방식 무관)
4. 첫 클릭 (Path B): cycle 정보만 갱신 (메시지)
5. 사용자: TC 재확인 (또는 그대로 유지)
6. 두 번째 클릭: 정상 분석 ✓
```

## 호환성

- 동일 경로로 분석 후 옵션 (scope/axis/overlap) 만 변경: 경로 동일 → 가드 통과 → 즉시 분석 (재분석 시 cycle 정보 갱신 1단계 들지 않음).
- 경로 추가 (빈 행 → path 입력): `_rows_last_analyzed_path[r]` 부재 → 다름 → cycle 정보 갱신.
- 경로 삭제 (path 비움): `_cur_paths` 에 해당 row 부재 → 비교 항목 자체 없음 → 가드 통과 (다른 row 가 변경 없으면).
- 표 reset: 매핑 일괄 클리어.

## 부수 효과

첫 분석 시도 시 항상 cycle 정보 갱신 1단계가 들어감. 사용자가 매번 "새 경로 감지" 다이얼로그를 보게 됨. 다소 번거롭지만 stale 분석 위험 < 다이얼로그 한 번 추가 부담.

차후 여유 시 "이미 cycle 정보가 신선하면 가드 skip" 등 최적화 가능 (현재는 단순 path 비교 — 안전 우선).

## 적용 파일

- `C:\Users\Ryu\battery\python\BDT_dev\DataTool_dev_code\DataTool_optRCD_proto_.py` (main, 사용자 테스트 환경)
- `C:\Users\Ryu\battery\python\BDT_dev\.claude\worktrees\stoic-agnesi-bd7997\DataTool_dev_code\DataTool_optRCD_proto_.py` (worktree)

## 검증 (사용자)

1. 앱 재시작
2. **시나리오 A** (직접 입력):
   - 경로 A 입력 → "프로파일 분석" 1차 → 메시지 + cycle bar 갱신
   - TC 입력 → "프로파일 분석" 2차 → 정상 그래프
3. **시나리오 B** (paste):
   - 위 분석 후 col 1 셀 선택 → Ctrl+V (다른 경로 paste) → "프로파일 분석" 1차
   - **메시지가 떠야 함** (v1 에서는 안 떴음 — 이게 핵심 검증 포인트)
   - TC 재확인 → 2차 → 정상 그래프
4. **시나리오 C** (load 파일):
   - "load file" 버튼으로 새 경로 import → "프로파일 분석" 1차
   - 메시지 → 2차 → 정상 그래프
