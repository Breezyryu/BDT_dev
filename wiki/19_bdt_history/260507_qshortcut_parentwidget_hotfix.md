---
date: 2026-05-07
type: changelog
tags: [bdt, bugfix, hotfix, pyqt6, qshortcut, 현황필터링]
---

# 현황 필터링 Ctrl+C — `QShortcut.parentWidget` AttributeError 핫픽스

## 증상

현황 탭 > 필터링 서브탭에서 결과 테이블(`tb_channel_filter`) 셀을
드래그 후 **Ctrl+C** 를 누르면 다음 오류 다이얼로그가 출력:

```
AttributeError: 'QShortcut' object has no attribute 'parentWidget'
```

→ 클립보드에 아무것도 복사되지 않음.

## 원인

`260507_filter_table_copy_paste.md` 변경에서 도입된 `_tb_channel_copy()`
의 sender 자동 감지 분기가 **PyQt6 API 와 어긋남**:

```python
sc = self.sender()
pw = sc.parentWidget() if isinstance(
    sc, (QtGui.QShortcut, QtGui.QAction)) else None
```

- **PyQt6 `QShortcut`** 은 `QObject` 직속 상속 → `parent()` 만 존재,
  `parentWidget()` 없음 (PyQt5 까지는 `QWidget` 상속이라 가능했으나
  PyQt6 에서 시그니처 변경)
- **`QAction`** 은 별도로 `parentWidget()` 메서드 보유

기존 코드는 두 타입을 한 분기로 묶어 `parentWidget()` 만 호출 →
`QShortcut` sender 일 때 즉시 `AttributeError`.

## 수정 — `DataTool_dev_code/DataTool_optRCD_proto_.py:30654-30664`

분기 분리:

```python
sc = self.sender()
pw = None
if isinstance(sc, QtGui.QShortcut):
    # PyQt6: QShortcut 은 QObject 상속 → parentWidget() 없음, parent() 사용
    pw = sc.parent()
elif isinstance(sc, QtGui.QAction):
    pw = sc.parentWidget()
if isinstance(pw, QtWidgets.QTableWidget):
    tb = pw
```

`QShortcut` 생성 시 두 번째 인자로 위젯을 부모로 넘기므로 `parent()`
반환값이 곧 대상 테이블 위젯과 일치 — 후속 `isinstance` 검사 통과.

## 영향 범위

- **현황 탭** > **필터링** 서브탭 Ctrl+C 정상화
- **현황 탭** > **채널 리스트** 서브탭 Ctrl+C 정상화 (동일 핸들러 공유)
- 우클릭 → "복사" 메뉴(`QAction` 경로)는 기존대로 동작 — 영향 없음

## 검증

- `python -m ast` 구문 검증 통과
- 시나리오:
  1. 필터링 결과 테이블 → 셀 드래그 → Ctrl+C → Excel 붙여넣기 ✅
  2. 채널 리스트 → 셀 드래그 → Ctrl+C ✅
  3. 우클릭 → "복사" 메뉴 → 붙여넣기 ✅ (회귀 없음)

## 관련 코드

- `_tb_channel_copy`: `DataTool_optRCD_proto_.py:30646`
- 단축키 등록 (filter): `DataTool_optRCD_proto_.py:19239-19242`
- 단축키 등록 (channel): `DataTool_optRCD_proto_.py:18893-18895`
