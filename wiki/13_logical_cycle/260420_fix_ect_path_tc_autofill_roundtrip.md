# ECT path 저장·로드 시 TC 자동채움 힌트 보존

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`
함수: `_save_table_to_path_file()` (L22066), `_cycle_cell_text_for_save()` (신규)

## 배경 / 문제

사용자 보고:
> "ECT path 사용으로 경로를 저장하고 다시 불러오면 TC 부분은 로딩이 안된다. 회색 폰트로 전체 TC 범위가 출력"

ECT path 테이블에서 TC 열(col 4)의 **회색 auto-fill 힌트 `"1-{max_TC}"`** 가 저장·재로드 라운드트립에서 의미를 잃었다.

### 원인

`_autofill_row` / `_restore_cycle_hint`는 col 4가 비어 있을 때 경로의 최대 TC를 계산해 `"1-{max_TC}"` 텍스트를 **회색(160,160,160)** 폰트로 써서 "사용자 입력 없음, 최대 TC 힌트"임을 시각 표시한다.

그런데 `_save_table_to_path_file`은 `_get_table_cell(r, 4)` 로 단순히 text만 읽어 저장한다. 따라서:

| 원래 상태 | 저장 텍스트 | 재로드 후 |
|---|---|---|
| 사용자 입력 `50` (검정) | `50` | col 4 = `50`, default fg (검정 렌더) ✓ |
| Auto-fill 힌트 `1-500` (회색) | `1-500` | col 4 = `1-500`, default fg (검정 렌더) ✗ |

재로드된 `1-500` 은 `_autofill_row` elif 분기 (`cyc_auto and cyc_existing`) 로 떨어져 **tooltip만 갱신**되므로 텍스트·foreground 는 그대로 유지된다. 결과적으로 회색 힌트였던 셀이 "사용자가 직접 입력한 전체 TC 범위"처럼 보이고, ECT 실행 시에도 `1-500` 이 명시 입력으로 해석된다.

## 수정

### 1. 회색 auto-fill 힌트는 저장하지 않음

`_save_table_to_path_file` 에서 col 4 값을 읽을 때 foreground 색상을 확인. 회색 `(160,160,160)` 이면 **빈 문자열로 저장**하여 재로드 시 `_autofill_row` 가 동일 힌트를 재생성하도록 위임.

```python
# Before
cyc = self._get_table_cell(r, 4)

# After
cyc = self._cycle_cell_text_for_save(r)  # 회색 힌트 → 빈칸
```

### 2. `_cycle_cell_text_for_save(row)` 헬퍼 신설

```python
def _cycle_cell_text_for_save(self, row: int) -> str:
    item = self.cycle_path_table.item(row, 4)
    if not item:
        return ''
    text = item.text().strip().strip('"').strip("'")
    if not text:
        return ''
    fg = item.foreground()
    if fg.style() != QtCore.Qt.BrushStyle.NoBrush:
        c = fg.color()
        if c.red() == 160 and c.green() == 160 and c.blue() == 160:
            return ''
    return text
```

- `NoBrush` (기본) / 검정 `(0,0,0)` / 기타 색 → 기존 텍스트 유지 (사용자 입력 또는 로드된 값)
- 회색 `(160,160,160)` → 빈 문자열 (auto-fill 힌트)

## 왕복 동작 검증

| 시나리오 | Before save | 저장 파일 col 4 | After reload |
|---|---|---|---|
| 사용자 입력 `50` (검정) | `50` BLACK | `50` | `50` default ✓ |
| Auto-fill `1-500` (회색) | `1-500` GRAY | `(empty)` | `1-500` GRAY ✓ (재생성) |
| 혼합 (특정값 + 힌트) | `50` / `1-500` | `50` / `(empty)` | `50` + `1-500` GRAY 재생성 |

PyQt 재현 테스트에서 두 시나리오 모두 라운드트립 정상 확인.

## 영향 범위

- `_save_table_to_path_file()` — col 4 저장 로직 한 줄 변경
- 신규 헬퍼 `_cycle_cell_text_for_save()` 추가
- 기타 함수 (load, autofill, ECT 실행) 미변경
- 기존 파일 역호환: 구형 저장 파일(회색 힌트 텍스트 포함)은 재로드 시 `1-500` 이 default fg 로 그려짐. 사용자가 한 번 저장하면 다음 재로드부터 회색 힌트가 복원됨.

## 검증 포인트

- [ ] ECT path 체크 + 경로만 입력 (TC 비움) → 회색 `1-{max}` 자동 생성 확인
- [ ] 저장 후 파일 열어 cycle 열이 **빈칸**인지 확인
- [ ] 재로드 후 col 4 가 다시 **회색 `1-{max}`** 으로 복원되는지 확인
- [ ] 사용자 입력 TC (검정) → 저장 → 재로드 시 텍스트 보존 확인
- [ ] ECT 실행 (`ect_confirm_button`) 에서 `_get_table_rows_ffill` 의 `cycle` 필드가 회색 힌트 대신 빈 문자열이 되면 `str(ect_cycle[i]).strip() == ''` → `chg_dchg_dcir_no` 리스트가 비어 루프가 스킵됨. 기존에도 동일 동작이므로 회귀 없음.
