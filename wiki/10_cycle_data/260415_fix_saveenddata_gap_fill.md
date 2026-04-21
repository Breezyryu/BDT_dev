# SaveEndData 앞쪽 누락 TC를 .cyc에서 gap-fill

**날짜**: 2026-04-15
**대상 함수**: `_cached_pne_restore_files()` (DataTool_optRCD_proto_.py:846~)

---

## 배경 / 목적

일부 PNE 채널(특히 장시간 floating 테스트)에서 **SaveEndData.csv에 앞쪽 TC가 통째로 누락**되는 현상이 발견됨.

**재현 케이스**: `260320_260923_03_안성진_251mAh_HaeanProtoDOE복합Floating/M01Ch025[025]`
- SaveData0001~0019 → TC 1~15 존재 (2026-03-20~04-10)
- SaveData0020~0023 → TC 16~22 존재 (~04-14)
- **SaveEndData.csv는 TC 16~22만 기록** (총 60행) — TC 1~15 step-end 누락
- 원인 추정: 장기 float 구간에서 PNE 소프트웨어가 step-end rotation을 건너뜀

이 상태에서 프로파일 탭 사이클바가 TC 16~22(논리 20~26)만 표시되어 사용자가 초기 사이클을 볼 수 없는 문제 발생.

---

## Before / After

### Before

```python
if save_end_data is not None:
    csv_max_tc = save_end_data[27].max()
    _cyc_mapped = _cyc_df_to_save_end_format(cyc_df, save_end_data.shape[1])
    supplement = _cyc_mapped[_cyc_mapped[27] > csv_max_tc]  # 뒤쪽만
```

→ `.cyc`는 TC 1부터 모두 가지고 있으나 `> csv_max_tc` 필터 때문에 **앞쪽 누락 TC는 복구 불가**.

### After

```python
if save_end_data is not None:
    _cyc_mapped = _cyc_df_to_save_end_format(cyc_df, save_end_data.shape[1])
    csv_tcs = set(int(x) for x in save_end_data[27].unique())
    supplement = _cyc_mapped[~_cyc_mapped[27].astype(int).isin(csv_tcs)]
    # … concat 후 TC(col27) + step(col7) 기준 stable sort
```

→ CSV에 없는 TC **전부** 보충 (앞/뒤 구분 없음) + 시간순 재정렬.

---

## 영향 범위

| 영역 | 영향 |
|------|------|
| Phase 0 (`build_channel_meta`) | `_cached_pne_restore_files` 경유 → 자동 적용 |
| Phase 2 재사용 (`_meta.save_end_data`) | Phase 0에서 이미 보충된 df 캐시 → 일관 |
| `classify_pne_cycles` | 누락 TC 복구 → 사이클 수 증가 |
| `_build_timeline_blocks_tc_by_loop` | 사이클바에 앞쪽 TC 표시 복구 |
| `pne_build_cycle_map` | 논리사이클 매핑 범위 확장 |
| 정상 채널 (SaveEndData 완전) | `csv_tcs`에 모든 TC 포함 → `supplement` 비어있음 → 변화 없음 |

**리스크**: `.cyc`와 CSV의 동일 TC가 혼재할 가능성 → 현재 `~isin` 조건으로 완벽 배제. 단, `.cyc` 단독 재구성 경로(line 934 부근)는 미변경.

---

## 로그 출력 변경

```
[이전] [.cyc 보충] ch25: CSV TC≤22, .cyc TC 23~26 추가 (N행)
[이후] [.cyc 보충] ch25: CSV TC=[16,17,18]...22, .cyc TC 1~15 (15개 TC, N행) 보충
```

앞쪽 보충이 발생하는 경우를 즉시 식별 가능.
