---
title: "사이클 분석 채널 컨트롤 버그 수정 — 서브 채널 lookup + 상세 탭 redraw"
date: 2026-04-26
tags: [bugfix, cycle-data, channel-control, ui, multi-canvas]
related:
  - "[[260426_fix_pne_sch_typecode_swap_offset_correct]]"
---

# 사이클 분석 채널 컨트롤 버그 수정 — 서브 채널 lookup + 상세 탭 redraw

> 두 결함이 같은 함수(`_create_cycle_channel_control` L18158)에서 발생.
> 사용자 보고: ① 서브 채널 토글·하이라이트 동작 안 함 ② 채널 그룹 토글이 요약(fig1) 만 적용되고 상세(fig2) 는 그대로 보임.

## 결함 1 — 서브 채널 lookup fail (`_strip_numbering` 한계)

### 증상
서브 채널 리스트의 체크박스를 토글하거나 항목을 클릭해도 **아무 동작 없음** (artist 가시성·하이라이트 모두). 채널 그룹은 정상 동작.

### 원인
`sub_list` 항목 표시 텍스트 (L18896):
```python
_short = f"CH{label}" if label.isdigit() else label[:15]
item = QListWidgetItem(f"{idx:0{_snw}d}. {_short}")
# 결과: "01. CH032"
```

핸들러에서 라벨 추출 (`on_sub_item_changed` 등):
```python
label = _strip_numbering(item.text())  # "01. CH032" → "CH032"
if label in sub_channel_map:  # 키는 "032" → ❌ False
    ...  # 진입 안 함, no-op
```

`_strip_numbering` 은 `r'^\d+\.\s*'` 만 제거 → "CH" 접두사가 그대로 남아 sub_channel_map 키 ("032") 와 항상 불일치.

### 수정
**Qt 표준 패턴**: 표시 텍스트와 데이터 키 분리. 항목 생성 시 `setData(UserRole, label)` 로 원본 키 보관, 핸들러에서 `data(UserRole)` 로 lookup.

ch_list 는 이미 이 패턴 사용 (L18432: `orig_key = item.data(Qt.ItemDataRole.UserRole)`) — sub_list / sub2_list 만 누락.

```python
# 항목 생성 (sub_list, L18901 부근)
item.setData(Qt.ItemDataRole.UserRole, label)  # 신규
sub_list.addItem(item)

# 핸들러 (전 5곳 sub_list, 4곳 sub2_list)
label = item.data(Qt.ItemDataRole.UserRole)   # was _strip_numbering(item.text())
if not label or label not in sub_channel_map:
    return
```

영향 받는 핸들러:
- `_get_sub_items_for_group` (L18906) — 그룹→서브 동기화
- `on_sub_item_clicked` (L18952) — 클릭 하이라이트
- `on_sub_item_changed` (L18983) — 체크박스 표시/숨김
- `on_sub_item_changed_linked` (L19092) — sub→sub2 연동
- `_get_sub2_items_for_parent` (L19028) — 서브2 부모 매칭
- `_get_sub2_items_for_group` (L19039) — 서브2 그룹 매칭
- `on_sub2_item_clicked` (L19135)
- `on_sub2_item_changed` (L19155)

## 결함 2 — 상세 탭(fig2) canvas redraw 누락

### 증상
채널 그룹 체크박스 토글 시 요약 탭(fig1) 의 artist 만 사라지고 상세 탭(fig2) 은 그대로 보임. 탭 전환 후에도 그대로.

### 원인
`channel_map[ch]['artists']` 는 **fig1 + fig2 의 artist 모두** 포함 (L21607: `_all_artists = _artists + _artists_b`). 핸들러에서 `art.set_visible(visible)` 호출하면 두 figure 의 artist 모두 visibility 변경됨.

하지만 redraw 호출은 단일 canvas 만:
```python
def on_item_changed_linked(item):
    ...
    for art in channel_map[orig_key]['artists']:
        art.set_visible(visible)
    ...
    canvas.draw_idle()   # ❌ fig1 의 canvas 만 redraw
```

`_create_cycle_channel_control` 시그니처는 `(channel_map, canvas, fig, axes_list, ...)` — fig2 의 canvas 정보 없음. fig2 의 artist 는 visibility 가 변경되어도 canvas 가 redraw 되지 않아 화면에 그대로 표시.

### 수정
함수 진입부에 `_redraw_all_canvases` 헬퍼 추가 — channel_map / sub_channel_map / sub2_channel_map 의 artist 들이 속한 모든 figure 의 canvas 를 unique 하게 redraw:

```python
def _redraw_all_canvases():
    """채널 토글 후 영향 받는 모든 figure 의 canvas 재드로우."""
    seen_ids = set()
    # 메인 canvas (요약 탭)
    _primary_c = canvas
    if _primary_c is not None:
        try:
            _primary_c.draw_idle()
            seen_ids.add(id(_primary_c))
        except Exception:
            pass
    # channel_map / sub*_channel_map 의 artist 가 속한 모든 figure 의 canvas
    for _src in (channel_map, sub_channel_map, sub2_channel_map):
        if not _src:
            continue
        for _info in _src.values():
            for _art in _info.get('artists', []):
                _f = getattr(_art, 'figure', None)
                if _f is None:
                    continue
                _c = getattr(_f, 'canvas', None)
                if _c is None or id(_c) in seen_ids:
                    continue
                seen_ids.add(id(_c))
                try:
                    _c.draw_idle()
                except Exception:
                    pass
```

함수 내 모든 `canvas.draw_idle()` 호출 14곳을 `_redraw_all_canvases()` 로 일괄 교체:
- 채널 그룹 변경 (`on_item_changed_linked`, `on_item_changed_3level`, `on_item_changed_with_sub2`) — 사용자 보고 핵심
- 서브 채널 변경 (이미 결함 1 의 수정으로 lookup 성공)
- 하이라이트 / 라인 너비 / 폰트 / 범례 / 검색 등 모든 컨트롤
- 채널 카운트 표시 갱신

`_redraw_all_canvases` 자체 내부의 메인 canvas 호출은 변수 (`_primary_c`) 통해 차별화하여 자기 자신 호출 무한루프 회피.

## 효과

### Before
- 서브 채널 체크박스 클릭 → 아무 변화 없음
- 채널 그룹 체크박스 클릭 → 요약 탭만 사라짐, 상세 탭 그대로
- 서브 채널 클릭 (하이라이트) → 아무 변화 없음

### After
- 서브 채널 체크박스 → 해당 채널의 fig1+fig2 모두 표시/숨김 ✓
- 채널 그룹 체크박스 → fig1+fig2 모두 표시/숨김 ✓
- 서브 채널 클릭 → fig1+fig2 모두 하이라이트/dim ✓
- 그룹→서브 동기화·서브→서브2 동기화 정상 ✓

## 검증

- [x] `python -c "ast.parse(...)"` syntax OK
- [x] 함수 내 `canvas.draw_idle()` 호출 0회 (모두 `_redraw_all_canvases()` 로 교체)
- [x] `_redraw_all_canvases` 사용 count = 19 (정의 1 + 호출 14 + docstring 등)
- [ ] 사용자 알파:
  - 서브 채널 체크박스 토글 → fig1+fig2 동시 변화
  - 채널 그룹 체크박스 → fig1+fig2 동시 변화
  - 서브 채널 클릭 (하이라이트) → 양쪽 dim/highlight
  - 그룹→서브 자동 연동 (그룹 체크 해제 시 서브 체크도 해제)
  - 서브2 가 있는 케이스 (사이클 레벨) 도 동일

## 위험·롤백

- **위험**: 낮음 — 모든 변경이 `_create_cycle_channel_control` 함수 내부 한정. 외부 호출자 영향 없음.
- **롤백**: 단일 commit 이라 revert 1회. 이전 동작 (서브 동작 안 함, 상세 탭 redraw 안 됨) 으로 복원.

## 향후

- `_redraw_all_canvases` 패턴은 다른 multi-figure UI 에도 적용 후보 (DCIR 결과 탭 등)
- `_strip_numbering` 함수 자체는 ch_list 검색 (L18563) 에서 여전히 사용. 검색용은 텍스트 매칭이라 OK.
