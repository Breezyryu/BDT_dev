---
title: "경로 테이블 Step 4 — confirm 진입부 진행률 + UI 응답 확보"
date: 2026-04-26
tags: [changelog, cycle-data, ux, performance]
related:
  - "[[260426_changelog_path_table_step3_trigger_split|Step 3 트리거 분리]]"
  - "[[260426_changelog_path_table_step5_cache_consistency|Step 5 캐시 일관성]]"
---

# 경로 테이블 Step 4 — confirm 진입부 진행률 + UI 응답 확보

> **PR #4 / 6** — Step 3 의 light/full 분리 정책에서 발생하는 confirm 시점 IO 를
> **statusBar 진행률 + `QApplication.processEvents()`** 로 사용자에게 가시화.

## 배경

Step 3 변경으로 paste·드롭·로드 직후엔 IO 0 (light) 이지만, **confirm 시점에 한 번에 무거운 IO** 가 발생한다. 동기 코드 안에서 `_autofill_table_empty_cells(mode='full')` 가 5–30초 걸릴 수 있어 사용자가 "버튼이 안 눌리는 것처럼" 느낄 수 있다.

QThread 비동기는 B안 (향후 PR) 에서 다루고, A안에서는 **동기 코드 + UI 응답 확보** 만으로 체감 freeze 를 줄인다.

## 변경 사항

### 1) `_autofill_table_empty_cells` 에 `progress_cb` 매개변수 추가 (L22467)

```python
def _autofill_table_empty_cells(self, *, mode: str = 'full',
                                progress_cb=None):
    """...
    progress_cb : callable(done: int, total: int) | None
        매 행 처리 후 호출되는 콜백. statusBar 업데이트·processEvents 호출용.
        None 이면 진행 표시 없음 (기존 동작).
        네트워크 드라이브에서 full 모드 호출 시 UI 응답 확보 목적.
    """
    ...
    # 진행 표시용 총 행 수 (경로 비어있는 행 제외)
    if progress_cb:
        n_total = sum(1 for r in range(tbl.rowCount())
                      if self._get_table_cell(r, 1))

    n_done = 0
    for r in range(tbl.rowCount()):
        ...
        n_done += 1
        if progress_cb:
            progress_cb(n_done, n_total)
```

- `progress_cb=None` 이 default → 기존 호출자 모두 영향 없음 (회귀 0)
- light 모드 호출자도 progress_cb 전달 가능하나 IO 0 이라 의미 적음. 실제 사용은 confirm 진입부 한 곳

### 2) `unified_cyc_confirm_button` 진입부에 statusBar 콜백 (L20917)

```python
# 테이블 빈 셀 자동 채우기 (경로명, 채널, 용량, 최대사이클)
# confirm 시점에 채널·TC 등 무거운 IO 일괄 처리 (Step 3·4 정책).
# 네트워크 드라이브 환경에서 freeze 완화 위해 statusBar 진행률 + processEvents.
if self._has_table_data():
    try:
        _status = self.statusBar()
    except Exception:
        _status = None

    def _autofill_progress(done: int, total: int) -> None:
        if _status is not None and total > 0:
            _status.showMessage(f"채널·TC 채우기 중... ({done}/{total})")
        # 동기 코드 안에서 UI 응답 확보 (paint/move 이벤트 처리)
        QtWidgets.QApplication.processEvents()

    self._autofill_table_empty_cells(
        mode='full', progress_cb=_autofill_progress)
    if _status is not None:
        _status.showMessage("분석 시작...", 2000)
```

- `statusBar()` 가 없는 환경 (메인 윈도우 변경 시) 도 graceful 처리
- 행 단위 콜백 + `processEvents()` 호출 → 동기 코드여도 paint·move 이벤트 처리되어 **창 이동·최소화 가능**, freeze 체감 ↓
- 마지막에 "분석 시작..." (2초 표시) 으로 다음 단계 진입을 사용자에게 알림

## 효과

`processEvents()` 효과 (네트워크 드라이브 5경로 = 25초 IO 가정):

```
패치 전 (Step 3 까지):
[confirm] → 25초 완전 freeze → [그래프 표시]
사용자 체감: "프로그램이 멈췄나?"

패치 후 (Step 4):
[confirm] → statusBar "채널·TC 채우기 중... (1/5)" → 5초 →
            "채널·TC 채우기 중... (2/5)" → 5초 → ...
            (각 단계마다 paint 갱신, 창 이동 가능) →
            "분석 시작..." → [그래프 표시]
사용자 체감: "진행 중이구나, 잠깐 기다리면 되겠다"
```

## 검증

- [x] `python -c "ast.parse(...)"` syntax OK
- [x] 다른 호출자 5곳 모두 `progress_cb=None` default → 기존 동작 (회귀 0)
- [ ] 사용자 알파:
  - 네트워크 드라이브 5경로 paste → confirm → statusBar 진행률 표시
  - "1/5", "2/5", ... "5/5" 진행 메시지 순차 표시
  - confirm 진행 중 창 이동·최소화 가능 (완전 freeze 아님)
  - "분석 시작..." 메시지 후 그래프 정상 표시
  - 일반 모드 (소량 데이터) 에서는 진행률이 너무 빠르게 지나갈 수 있음 — 정상

## 위험·롤백

- **위험**: 매우 낮음 — progress_cb 는 default None, 다른 호출자 영향 0
- **롤백**: confirm 진입부 try/except + def + 호출 블록 제거 → 6분

## 다음 단계 (Step 5 와 함께 머지됨)

이 PR 의 코드는 Step 5 (캐시 일관성) 와 같은 commit 에 포함됨 — 두 변경이 의미적으로 "confirm 동작 정합성" 카테고리로 묶임.

- **Step 6** (PR #6): paste 헤더 자동 검출 + 연결처리 토글 즉시 hint
