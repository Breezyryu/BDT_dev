---
date: 2026-05-07
type: changelog
tags: [bdt, ui, qtablewidget, clipboard, 현황필터링]
---

# 현황 필터링 결과 테이블 — 드래그·복사·붙여넣기 지원

## 배경

현황 탭의 **필터링** 서브탭에서 결과 테이블(`tb_channel_filter`) 값을
드래그로 다중 선택해도 **Ctrl+C 가 동작하지 않음** — 우클릭 메뉴에도
복사 항목이 없어 사용자가 데이터를 외부 표(엑셀 등)로 옮길 수 없었다.

## 원인

1. **단축키 핸들러가 잘못된 테이블 참조**
   `_tb_channel_copy()` 가 항상 `self.tb_channel` 을 직접 읽음
   → 필터링 탭에서 Ctrl+C 눌러도 채널 리스트 탭의 (보이지 않는) 선택 영역만 복사 시도
2. **필터링 탭 우클릭 메뉴에 복사 항목 없음**
   `_filter_context_menu()` 는 "전체 펼침/닫힘" 만 제공
3. **드래그 중 cellClicked 트리거**
   드래그 종료 시 release 위치가 헤더 행이면 `_filter_toggle_section()`
   가 발동되어 섹션이 접히고 사용자 의도와 어긋남

## 변경 사항 — `DataTool_dev_code/DataTool_optRCD_proto_.py`

### 1. `_tb_channel_copy(tb=None)` 일반화

- `tb` 인자 명시 시 해당 테이블 사용
- 미지정 시 `sender().parentWidget()` → `focusWidget()` → fallback 순 자동 감지
  → `tb_channel`·`tb_channel_filter` 양쪽에서 동일 메서드로 동작
- **숨겨진 행(섹션 접힘) 제외** — 사용자가 보지 못한 데이터는 복사 안 함
- **TSV(plain text) + HTML** 동시 저장 (`QMimeData.setText` + `setHtml`)
  → Excel·Origin·메모장·다른 QTableWidget 모두 호환

### 2. `_filter_context_menu()` 확장

- "복사 (Ctrl+C)" 항목 추가 — 선택 영역 없으면 비활성
- "전체 선택 (Ctrl+A)" 항목 추가
- 기존 "전체 펼침/닫힘" 은 섹션 헤더가 있을 때만 표시

### 3. `tb_channel` 우클릭 메뉴 신설 — `_tb_channel_context_menu()`

- 채널 리스트 탭에도 동일한 복사·전체 선택 메뉴 부착 (UX 일관성)

### 4. `_filter_toggle_section()` 가드 추가

- 다중 선택(>1행) 상태에서는 토글 스킵
  → 드래그-선택-복사 흐름이 헤더 행에서 끊기지 않음

## 영향 범위

- **현황 탭** > **필터링** 서브탭 — 결과 테이블 드래그/복사 정상화
- **현황 탭** > **채널 리스트** 서브탭 — 우클릭 복사 메뉴 신규 제공
- 기존 Ctrl+C / Ctrl+A 단축키 동작은 유지 (메서드 시그니처 backward-compat)

## 검증

- 파이썬 구문 검증 통과 (`python -m ast`)
- 사용 시나리오:
  1. 필터링 결과 테이블 → 셀 드래그 → Ctrl+C → Excel 붙여넣기 (TSV)
  2. 필터링 결과 테이블 → 우클릭 → "복사" → 다른 표에 붙여넣기 (HTML 표 형식)
  3. 채널 리스트 그리드 → 우클릭 → "전체 선택" → "복사"
  4. 헤더 행 포함 드래그 — 섹션 접힘 발생 안 함

## 관련 코드 위치

- 단축키 등록 (filter): `DataTool_optRCD_proto_.py:19162-19169`
- 단축키 등록 (channel): `DataTool_optRCD_proto_.py:18821-18826`
- 우클릭 메뉴 등록 (channel): `DataTool_optRCD_proto_.py:18830-18833`
- `_tb_channel_context_menu`: `DataTool_optRCD_proto_.py:30562`
- `_tb_channel_copy`: `DataTool_optRCD_proto_.py:30574`
- `_filter_context_menu`: `DataTool_optRCD_proto_.py:30389`
- `_filter_toggle_section`: `DataTool_optRCD_proto_.py:30440`
