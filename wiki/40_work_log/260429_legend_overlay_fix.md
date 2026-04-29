---
tags: [bdt, profile-analysis, legend, ui, bugfix, work-log]
date: 2026-04-29
status: fixed
---

# 전체 통합 / 셀별 통합 — 범례가 plot 영역 잠식 문제 수정

## 증상

프로필 탭 → "전체 통합" 또는 "셀별 통합" 분석 시 범례 박스가 plot 영역의 절반 이상을 차지하여 그래프 크기가 줄어드는 문제.

라벨 예시: `"LWN Gen5 MP1-1 0.5C hysteresis CH022 Cy3-11"` (40+ 자) — 6개 plot 모두에 동일한 긴 라벨이 표시되어 시각화 가독성 저하.

## 원인 (이중 prefix 추가)

`_make_short_legend` 함수 ([L4173-4228](DataTool_dev_code/DataTool_optRCD_proto_.py:4173)) 는 `view_mode + n_folders` 조건으로 folder prefix 포함 여부를 자체 결정:

| view_mode | n_folders=1 | n_folders>1 |
|---|---|---|
| `cyc` | `Cy3` | `LWN Gen5 MP1-1 Cy3` (folder_name[:15]) |
| `cell` | `01. CH022` | `LWN Gen5 MP1-1 01. CH022` |
| `all` | `CH022 Cy3-11` | `LWN Gen5 MP1-1 CH022 Cy3-11` |

→ 단일 폴더 시 lgnd 자체는 짧음.

그런데 `_profile_render_loop` 의 `view_mode='all'` 와 `'cell'` 분기에서 호출자가 다시 prefix 를 추가:

```python
# 기존 (문제)
temp_lgnd = (lgnd if len(all_data_name) == 0
             else all_data_name[i] + " " + lgnd)
```

`all_data_name[i]` 는 풀 폴더명 (예: "LWN Gen5 MP1-1 0.5C hysteresis", 30+ 자) — `_make_short_legend` 의 `[:15]` 절단을 우회. 결과적으로 호출자에서 풀 폴더명이 prefix 로 붙어 plot 라벨이 40+ 자가 됨.

`view_mode='cyc'` 분기 ([L20588](DataTool_dev_code/DataTool_optRCD_proto_.py:20588))는 `temp_lgnd = lgnd` 만 사용해 정상 동작 — `'all'` / `'cell'` 분기만 중복 prefix 추가.

## 수정

`view_mode='all'` ([L20732 부근](DataTool_dev_code/DataTool_optRCD_proto_.py:20732)) 와 `view_mode='cell'` ([L20825 부근](DataTool_dev_code/DataTool_optRCD_proto_.py:20825)) 의 `temp_lgnd` 생성 로직을 `temp_lgnd = lgnd` 로 통일:

```python
# 수정 후
temp_lgnd = lgnd  # _make_short_legend 가 이미 folder 포함 여부 결정
```

## 효과

- 단일 폴더: 라벨 = `"CH022 Cy3-11"` (12자) → plot 영역 정상
- 다중 폴더: 라벨 = `"LWN Gen5 MP1-1 CH022 Cy3-11"` (`[:15]` 절단된 folder_short 포함) → plot 영역 정상
- `_apply_legend_strategy` 의 라인 수 기반 폰트/축약 전략 동작 정상화

## 후속: 다중 경로 라벨 소스 전환 (시험명 우선)

기존: `_make_short_legend(folder_name=namelist[-2])` 로 폴더 경로 끝 이름 사용 → 보통 30+ 자의 긴 폴더명, `[:15]` 절단해도 의미 없는 prefix (예: `"260202_260210_0"`).

수정: `_make_short_legend` 에 신규 인자 `test_name` 추가. 호출자는 사용자가 테이블 "시험명" 컬럼에 직접 입력한 값 (`all_data_name[i]`) 을 우선 전달. 비어있으면 기존 `folder_name` 으로 fallback.

```python
# _make_short_legend 내부
_id_name = test_name if test_name else folder_name
folder_short = _id_name[:15] if _id_name else ""

# 호출 (3곳 동일 패턴)
lgnd = _make_short_legend(
    CycNo, ...,
    folder_name=namelist[-2] if len(namelist) >= 2 else '',
    test_name=(str(all_data_name[i])
               if i < len(all_data_name) and all_data_name[i]
               else ''),
    view_mode=view_mode,
)
```

수정 위치 (3곳):
- cyc 분기 ([L20580+](DataTool_dev_code/DataTool_optRCD_proto_.py:20580))
- all 분기 ([L20712+](DataTool_dev_code/DataTool_optRCD_proto_.py:20712))
- cell 분기 ([L20806+](DataTool_dev_code/DataTool_optRCD_proto_.py:20806))

효과:
- 사용자가 "MP1-1" 또는 "LWN Gen5" 같이 짧고 의미명확한 시험명을 입력 → 그대로 라벨 prefix 사용
- 시험명 미입력 시 기존 폴더명 fallback (backward compatible)

## 관련 함수

- `_make_short_legend` ([L4173-4228](DataTool_dev_code/DataTool_optRCD_proto_.py:4173)) — 범례 텍스트 생성, view_mode별 형식 분기
- `_apply_legend_strategy` ([L4231-4296](DataTool_dev_code/DataTool_optRCD_proto_.py:4231)) — 라인 수 기준 폰트/위치/컬러바 전략
- `_profile_render_loop` ([L20304+](DataTool_dev_code/DataTool_optRCD_proto_.py:20304)) — view_mode별 호출 흐름
- `pne_path_setting` ([L23130+](DataTool_dev_code/DataTool_optRCD_proto_.py:23130)) — 사용자 입력 시험명을 `all_data_name` 으로 반환
