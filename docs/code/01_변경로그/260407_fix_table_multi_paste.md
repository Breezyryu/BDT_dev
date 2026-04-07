# 260407 경로 테이블 여러 셀 붙여넣기 개선

## 배경 / 목적

경로 테이블에서 사이클(col4), 사이클Raw(col5), 모드(col6)를 엑셀 등에서 복사하여
여러 셀에 한꺼번에 붙여넣기(Ctrl+V)할 때, `cellChanged` 시그널이 셀마다 발동하여
col4→col5 자동 매핑이 중간에 간섭하는 문제가 있었다.

예: col4에 "1-5" + col5에 "10-18" + col6에 "DCHG"를 동시에 붙여넣으면
→ col4 설정 시 cellChanged 발동 → col5가 자동 매핑으로 덮어써짐
→ 이후 col5에 "10-18"이 다시 설정되지만 또 cellChanged 발동

## 변경 내용

### `_cycle_table_paste()` (L18989)

**수정 전:**
- `cellChanged` 시그널 차단 없이 `setItem()` 직접 호출
- col4 붙여넣기 시 자동 매핑 간섭으로 col5 값 오염

**수정 후:**
- `tbl.blockSignals(True)` 로 붙여넣기 중 `cellChanged` 시그널 차단
- col4/5/6에 붙여넣기 시 검정 폰트 + 편집 가능 플래그 설정
- 붙여넣기 완료 후 경로 하이라이트 갱신

```python
# 핵심 변경
tbl.blockSignals(True)
try:
    for ri, parts in enumerate(rows):
        for ci, val in enumerate(parts):
            ...
            if c in (4, 5, 6) and val.strip():
                item.setForeground(QtGui.QColor(0, 0, 0))  # 사용자 입력=검정
                item.setFlags(_editable)
            tbl.setItem(start_row + ri, c, item)
finally:
    tbl.blockSignals(False)
```

## 영향 범위

- `_cycle_table_paste()` — Ctrl+V 핸들러
- ECT 모드에서 사이클/사이클Raw/모드 일괄 붙여넣기 워크플로우
- 비-ECT 모드에서도 동일하게 적용 (다만 col4-6은 _update_ect_columns_state로 비활성)
