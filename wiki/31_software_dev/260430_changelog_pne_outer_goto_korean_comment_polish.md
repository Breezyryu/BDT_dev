---
title: "[문서] PNE outer goto loop 확장 한글 주석 윤문"
aliases:
  - PNE outer goto comment polish
  - 한글 주석 윤문 260430
tags:
  - software-dev
  - changelog
  - comment
  - korean
  - polish
type: changelog
status: applied
related:
  - "[[260428_changelog_path_table_step1_cache_patch]]"
created: 2026-04-30
updated: 2026-04-30
---

# [문서] PNE outer goto loop 확장 한글 주석 윤문

> [!abstract] 요약
> 직전 커밋(`7232bd4` — PNE outer goto loop 확장)에서 `DataTool_optRCD_proto_.py` 에 추가된 한글 주석을 자연스러운 한국어로 다듬었다. 코드 동작과 식별자(`goto_target_step`, `goto_repeat_count` 등)는 일절 손대지 않았고, 어색한 어순·직역 표현·축약 라벨만 정정했다.

---

## 1. 배경

`7232bd4` 커밋이 PNE outer goto 파싱·확장 로직을 새로 도입하면서 함께 추가된 한글 주석에는 다음과 같은 문체 이슈가 섞여 있었다.

- "보유" → 자연스러운 한국어에서는 "담는다 / 함께 담긴다" 가 더 자연스러움
- "외곽 반복" → "outer 반복" 또는 "바깥 반복" 이 코드 맥락에 맞음
- "1 iter" 같은 영어 축약 라벨 → "1회차" 로 통일
- "Algorithm:" 영어 헤더 → "알고리즘:" 한글로 통일
- 단편 라벨 ("비정상 — outer loop 무시") → 문장 단위로 다듬어 의미 명확화

기능·동작 변경은 0. 단순 주석 가독성 개선.

---

## 2. 변경 위치

`DataTool_dev_code/DataTool_optRCD_proto_.py` 한 파일, 6 영역.

| 영역 | 위치 | 내용 |
|------|------|------|
| 1 | `_parse_pne_sch` LOOP 분기 (≈ L7665) | offset 52 / 580 필드 설명 블록 |
| 2 | `_decompose_loop_groups` docstring (≈ L7881) | Phase 2 설명 단락 |
| 3 | `_decompose_loop_groups` 내부 dict (≈ L7898) | body_start_step / outer goto 라벨 |
| 4 | `_build_loop_group_info` (≈ L8112) | outer goto 확장 의도 설명 |
| 5 | `_expand_groups_with_outer_goto` docstring (≈ L8159) | 알고리즘 설명 |
| 6 | `_expand_groups_with_outer_goto` 본체 (≈ L8182) | 인라인 주석 5건 |

---

## 3. 윤문 원칙

1. **의미 보존** — 모든 주석은 원래 의미를 그대로 유지. 정보 추가·삭제 없음.
2. **식별자 불변** — `goto_target_step`, `body_start_step`, `loop_count` 등 변수·필드명은 절대 미변경.
3. **표 / 예시 보존** — TC 시퀀스 예시, offset 숫자, step 번호 등 사실 데이터 그대로.
4. **어순·조사 정리** — 영어식 어순, 부적절한 조사, 축약 라벨만 한국어 자연스러움 기준으로 손질.
5. **검증** — `python -m py_compile` 로 syntax 무결성 확인.

---

## 4. 검증

```
$ python -m py_compile DataTool_dev_code/DataTool_optRCD_proto_.py
$ git diff --stat DataTool_dev_code/DataTool_optRCD_proto_.py
DataTool_dev_code/DataTool_optRCD_proto_.py | 63 +++++++++++++++--------------
 1 file changed, 32 insertions(+), 31 deletions(-)
```

- syntax OK
- 한 줄 단위 1:1 치환 위주, 줄 수 거의 동일 (32 / 31)
- 코드 라인은 한 줄도 수정되지 않음 (모두 주석 / docstring 내부)

---

## 5. 후속 가능 작업

- 동일 파일 내 PNE/Toyo 분기, cycle_map 빌드, dQ/dV 처리 등 다른 영역의 한글 주석에도 같은 윤문 원칙을 적용 가능.
- 사용자 요청 시 영역 단위 (예: "PNE 파서 전체", "프로필 탭 콜백") 로 진행.
