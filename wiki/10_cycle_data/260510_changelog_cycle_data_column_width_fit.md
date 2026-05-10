---
title: "사이클 분석 — '데이터' 서브탭 컬럼 폭 데이터 fit + 헤더 줄바꿈"
date: 2026-05-10
tags: [ui, cycle-data, qtablewidget, header-wrap]
related:
  - "[[260427_changelog_data_subtab]]"
requested_by: "류성택"
---

# 사이클 분석 — '데이터' 서브탭 컬럼 폭 데이터 fit + 헤더 줄바꿈

> 결과 → 데이터 서브탭 (방전용량 / Rest End / DCIR / RSS …) 의 각 채널 컬럼 폭을
> **숫자 데이터 크기에 맞춰 좁게** 잡고, 긴 채널 헤더 ("Q8 ATL 선상 SEU4 RT @1-1202_008")
> 는 **여러 줄로 줄바꿈** 처리.

## Context

기존: `_create_cycle_data_subtab` 에서 `QHeaderView.ResizeMode.ResizeToContents`
로 컬럼 폭을 자동 산정 → 헤더 텍스트 길이가 데이터 (`0.8099` 등) 보다 훨씬 길어
**컬럼이 과도하게 넓어짐**. 한 화면에 4–5 채널만 보이고 좌우 스크롤 빈발.

요청 (260510 류성택):
> 결과 데이터 탭에서 각 열의 넓이는 숫자 데이터 크기에 맞출 것 헤더 텍스트는 줄바꿈 처리하자

## Why

- 사이클 데이터 탭의 본질 = 채널 × OriCyc 행렬을 **빠르게 비교**.
- 헤더 길이로 컬럼이 결정되면 화면 밀도가 낮아져 비교가 어려움.
- 헤더는 한 번 식별 후 시야 밖으로 보내도 OK 한 메타정보 — 줄바꿈/세로 확장이 적합.

## 변경

### Path
[DataTool_optRCD_proto_.py](DataTool_dev_code/DataTool_optRCD_proto_.py) —
`_create_cycle_data_subtab` (L22042~)

### A. `_wrap_channel_header(text)` 헬퍼 추가

채널 헤더를 자연 break point 에서 줄바꿈.

```python
def _wrap_channel_header(text: str) -> str:
    """채널 헤더 줄바꿈 — '@' 우선, 다음 공백 가운데."""
    t = (text or '').strip()
    if '@' in t:
        prefix, suffix = t.split('@', 1)
        prefix = prefix.strip()
        suffix = '@' + suffix
        if len(prefix) > 12:
            words = prefix.split()
            if len(words) >= 2:
                mid = (len(words) + 1) // 2
                return (' '.join(words[:mid]) + '\n'
                        + ' '.join(words[mid:]) + '\n' + suffix)
        return f"{prefix}\n{suffix}" if prefix else suffix
    if len(t) > 14:
        words = t.split()
        if len(words) >= 2:
            mid = (len(words) + 1) // 2
            return ' '.join(words[:mid]) + '\n' + ' '.join(words[mid:])
    return t
```

예시:
- `Q8 ATL 선상 SEU4 RT @1-1202_008`
  → `Q8 ATL 선상\nSEU4 RT\n@1-1202_008` (3줄)
- `Q8 선상 ATL SEU4 LT @1-401_009`
  → `Q8 선상 ATL\nSEU4 LT\n@1-401_009`

### B. ResizeMode `ResizeToContents` → `Interactive`

```python
# Before
tbl.horizontalHeader().setSectionResizeMode(
    QHeaderView.ResizeMode.ResizeToContents)

# After
tbl.horizontalHeader().setSectionResizeMode(
    QHeaderView.ResizeMode.Interactive)
```

`Interactive` 로 두면 사용자가 개별 컬럼 폭을 드래그로 재조정 가능 (덤).

### C. 셀 채운 뒤 sample-based 폭 계산

각 컬럼의 첫 50행 셀 텍스트 길이를 스캔해서 폭 결정 (헤더 길이 무시).

```python
_h_header = tbl.horizontalHeader()
_sample_n = min(50, n_rows)
for _ci in range(n_cols):
    _max_chars = 4
    for _ri in range(_sample_n):
        _smp = tbl.item(_ri, _ci)
        if _smp is not None:
            _max_chars = max(_max_chars, len(_smp.text()))
    _h_header.resizeSection(_ci, max(55, _max_chars * 7 + 14))
```

- Consolas 9pt ≈ 7px/char, 셀 padding ~14px
- 최소 폭 55px 보장 (OriCyc, 짧은 정수 등)
- "0.8099" (decimals=4) → 6 chars × 7 + 14 = **56px** (기존 200px+ 대비 크게 압축)

### D. 헤더 높이 = wrap 라인 수 × 16 + 8

```python
_max_lines = max((str(h).count('\n') + 1) for h in headers)
_h_header.setFixedHeight(_max_lines * 16 + 8)
```

라인 수에 비례해 헤더 영역 자동 확장 — 1줄 24px / 2줄 40px / 3줄 56px.

## 영향

- ✅ 화면당 표시 가능 채널 수 증가 (200px→56px 컬럼 → ~4배 밀도)
- ✅ 헤더 정보 손실 없음 — 그대로 표시, 다만 줄바꿈
- ✅ 사용자가 개별 컬럼을 드래그 리사이즈 가능 (Interactive 모드)
- 헤더 색상 적용 로직 (라인 22155~) 영향 없음 — `horizontalHeaderItem(ci+1)` 그대로
- Ctrl+C 복사 동작 영향 없음 — 셀 텍스트만 복사하므로 헤더 `\n` 무관

## Test

- [x] `python -c "import ast; ast.parse(...)"` 구문 OK
- [ ] 실측: PNE/Toyo 사이클 데이터 로드 → 결과 → 데이터 서브탭 → 컬럼 폭 시각 확인
- [ ] 채널 4+ 개 시 한 화면 표시되는지 확인
- [ ] 짧은 채널명 (예: "Q8") 도 최소 폭 55px 보장 확인
- [ ] 헤더 색상 (그래프 라인 색) 그대로 적용되는지 확인

## Out of Scope

- 프로파일 데이터 서브탭 (`_create_profile_data_subtab`, L22202) — 이미 sample-based
  폭 계산 적용됨 (L22397~). 헤더 줄바꿈은 미적용 — 별도 요청 시 동일 패턴 이식 가능.
